#!/usr/bin/env python3
"""Specola Engine — RSS briefing generator powered by Claude Code CLI.

Two-phase analysis:
  Phase 1: Per-category analysis (one small Claude call per category)
  Phase 2: Synthesis (one Claude call to produce cross-cutting sections)
"""
from __future__ import annotations

import os

# Workaround: on macOS, after ThreadPoolExecutor loads the Network framework,
# subprocess.run() → fork() crashes in the atfork handler of libnetworkextension
# ("multi-threaded process forked / crashed on child side of fork pre-exec").
# This disables the ObjC fork safety check that triggers the crash.
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.feed_fetcher import parse_opml, fetch_feeds, format_digest
from src.prefilter import prefilter_items, condense_profile
from src.prompt_builder import build_category_prompt, build_synthesis_prompt
from src.analyzer import analyze_with_claude, analyze
from src.doc_generator import generate_docx, generate_fallback_docx
from src.html_generator import generate_html
from src.portal_generator import regenerate_portal_index, extract_highlights

# Lazy imports: weasyprint and epub load C libraries (libgobject, libgio,
# libpango) whose atfork handlers crash when subprocess.run() calls fork()
# after ThreadPoolExecutor has been used for feed fetching.
# Import them only when the output format actually requires them.
def _lazy_generate_pdf(html_path, date, output_dir):
    from src.pdf_generator import generate_pdf
    return generate_pdf(html_path, date, output_dir)

def _lazy_generate_epub(markdown, date, output_dir, language, theme="corporate"):
    from src.epub_generator import generate_epub
    return generate_epub(markdown, date, output_dir, language, theme=theme)

logger = logging.getLogger("specola")

# Timeout per call: 120s per category, 180s for synthesis
CATEGORY_TIMEOUT = 120
SYNTHESIS_TIMEOUT = 180

# Categories with fewer items than this get batched into a single LLM call
_BATCH_THRESHOLD = 5

_SAFE_FILENAME_RE = __import__("re").compile(r"[^\w\-]+")


def _output_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False))


def _analyze_categories(
    items_by_category: dict[str, list[dict]],
    profile_text: str,
    language: str,
    work_dir: Path,
    today: str,
    model: str | None,
    provider: str = "claude",
    endpoint: str | None = None,
    category_model: str | None = None,
    compact_profile: str | None = None,
) -> tuple[dict[str, str], int]:
    """Phase 1: Analyze each category independently.

    Small categories (< _BATCH_THRESHOLD items) are batched into a single
    LLM call to avoid paying the prompt overhead (profile + instructions)
    for each tiny category. Uses compact digest format to minimize tokens.

    If category_model is set, it overrides model for phase 1 calls (e.g. a
    faster/cheaper model like Haiku). If compact_profile is set, the condensed
    keyword-only profile is used instead of the full text.

    Returns (category_analyses, success_count).
    """
    # Split into big (individual call) and small (batched call) categories
    big_cats: dict[str, list[dict]] = {}
    small_cats: dict[str, list[dict]] = {}
    for cat, items in items_by_category.items():
        if len(items) >= _BATCH_THRESHOLD:
            big_cats[cat] = items
        else:
            small_cats[cat] = items

    results = {}
    success_count = 0
    total_calls = len(big_cats) + (1 if small_cats else 0)
    call_idx = 0

    # Resolve the model for phase 1: prefer category_model, fall back to model
    phase1_model = category_model or model

    # ── Individual calls for large categories ──
    for category, items in big_cats.items():
        call_idx += 1
        logger.info("  [%d/%d] Analyzing: %s (%d items)", call_idx, total_calls, category, len(items))

        mini_digest = format_digest({category: items}, date.today().isoformat(), compact=True)
        safe_name = _SAFE_FILENAME_RE.sub("_", category).strip("_")
        digest_path = work_dir / f"cat_{safe_name}_{today}.md"
        digest_path.write_text(mini_digest, encoding="utf-8")

        prompt = build_category_prompt(profile_text, language, category,
                                       compact_profile=compact_profile)
        analysis = analyze(
            digest_path, prompt, provider=provider, model=phase1_model,
            timeout=CATEGORY_TIMEOUT, endpoint=endpoint,
        )

        if analysis:
            results[category] = analysis.strip()
            success_count += 1
            logger.info("  [%d/%d] %s: OK", call_idx, total_calls, category)
        else:
            raw = "\n".join(
                f"- {item['title']} ({item['source']}) — {item['summary']}"
                for item in items
            )
            results[category] = raw
            logger.warning("  [%d/%d] %s: LLM failed, using raw items", call_idx, total_calls, category)

    # ── Single batched call for small categories ──
    if small_cats:
        call_idx += 1
        small_total = sum(len(v) for v in small_cats.values())
        cat_names = ", ".join(small_cats.keys())
        logger.info(
            "  [%d/%d] Batched analysis: %d small categories (%d items): %s",
            call_idx, total_calls, len(small_cats), small_total, cat_names,
        )

        # Build a combined digest with all small categories
        batched_digest = format_digest(small_cats, date.today().isoformat(), compact=True)
        digest_path = work_dir / f"cat_batched_{today}.md"
        digest_path.write_text(batched_digest, encoding="utf-8")

        # Build a combined prompt listing all batched category names
        batch_label = " + ".join(small_cats.keys())
        prompt = build_category_prompt(profile_text, language, batch_label,
                                       compact_profile=compact_profile)
        analysis = analyze(
            digest_path, prompt, provider=provider, model=phase1_model,
            timeout=CATEGORY_TIMEOUT, endpoint=endpoint,
        )

        if analysis:
            # Store the combined analysis under each category key so synthesis
            # can reference them. We split later if possible, else store as one block.
            _split_batched_analysis(analysis, small_cats.keys(), results)
            success_count += 1
            logger.info("  [%d/%d] Batched: OK", call_idx, total_calls)
        else:
            for cat, items in small_cats.items():
                raw = "\n".join(
                    f"- {item['title']} ({item['source']}) — {item['summary']}"
                    for item in items
                )
                results[cat] = raw
            logger.warning("  [%d/%d] Batched: LLM failed, using raw items", call_idx, total_calls)

    return results, success_count


def _split_batched_analysis(
    analysis: str,
    category_names: "list[str] | dict_keys",
    results: dict[str, str],
) -> None:
    """Try to split a batched LLM analysis back into per-category sections.

    Looks for ## Category headers in the output. If splitting fails,
    stores the entire analysis under a single combined key (not duplicated
    across every unmatched category).
    """
    import re
    cat_list = list(category_names)
    sections: dict[str, list[str]] = {}
    current_cat = None
    preamble: list[str] = []  # lines before any matched header

    for line in analysis.strip().splitlines():
        # Match ## headers — try exact match with known category names
        if line.startswith("## "):
            header = line[3:].strip()
            matched = None
            for cat in cat_list:
                if cat.lower() in header.lower() or header.lower() in cat.lower():
                    matched = cat
                    break
            if matched:
                current_cat = matched
                sections[current_cat] = []
                continue
            else:
                # Unrecognized header — keep it as content under current category
                if current_cat is not None:
                    sections.setdefault(current_cat, []).append(line)
                else:
                    preamble.append(line)
                continue
        if current_cat is not None:
            sections.setdefault(current_cat, []).append(line)
        else:
            preamble.append(line)

    if sections:
        for cat, lines in sections.items():
            results[cat] = "\n".join(lines).strip()
        # Categories not found in the split are simply skipped — their
        # content is already covered by the matched sections.  Assigning
        # the full output to each unmatched category caused massive
        # repetition in the final briefing.
        unmatched = [c for c in cat_list if c not in results]
        if unmatched:
            logger.info(
                "  Batched split: %d matched, %d unmatched (skipped): %s",
                len(sections), len(unmatched), ", ".join(unmatched),
            )
    else:
        # Could not split at all — store under combined key
        combined_key = " / ".join(cat_list)
        results[combined_key] = analysis.strip()


def _synthesize(
    category_analyses: dict[str, str],
    profile_text: str,
    language: str,
    date_display: str,
    work_dir: Path,
    today: str,
    model: str | None,
    provider: str = "claude",
    endpoint: str | None = None,
) -> str | None:
    """Phase 2: Produce cross-cutting sections from all category analyses."""
    logger.info("  Synthesis pass over %d categories...", len(category_analyses))

    # Build the input: all category analyses concatenated
    sections = []
    for category, analysis in category_analyses.items():
        sections.append(f"## {category}\n\n{analysis}")

    all_analyses = "\n\n---\n\n".join(sections)
    analyses_path = work_dir / f"all_analyses_{today}.md"
    analyses_path.write_text(all_analyses, encoding="utf-8")

    prompt = build_synthesis_prompt(profile_text, language, date_display)
    return analyze(
        analyses_path, prompt, provider=provider, model=model,
        timeout=SYNTHESIS_TIMEOUT, endpoint=endpoint,
    )


def _assemble_briefing(
    synthesis: str | None,
    category_analyses: dict[str, str],
    date_display: str,
) -> str:
    """Assemble the final markdown from synthesis + category analyses."""
    parts = [f"# Specola — Briefing del {date_display}", ""]

    # Synthesis sections (Da sapere oggi, Richiede attenzione, etc.)
    if synthesis:
        parts.append(synthesis.strip())
        parts.append("")
        parts.append("---")
        parts.append("")

    # Per-category analyses
    for category, analysis in category_analyses.items():
        parts.append(f"## {category}")
        parts.append("")
        parts.append(analysis)
        parts.append("")

    return "\n".join(parts)


def run_engine(
    opml: str,
    profile: str,
    output_dir: str,
    hours: int,
    language: str,
    max_items: int,
    model: "str | None",
    dry_run: bool,
    verbose: bool,
    output_format: str = "docx",
    provider: str = "claude",
    endpoint: str | None = None,
    theme: str = "corporate",
    category_model: "str | None" = None,
) -> None:
    if verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                            format="%(message)s")

    now = datetime.now()
    today = now.strftime("%Y-%m-%d_%H%M")
    today_date = date.today().isoformat()

    # 1. Parse OPML
    try:
        feeds_by_category = parse_opml(opml)
    except Exception as e:
        _output_json({"status": "error", "message": f"Errore parsing OPML: {e}"})
        return

    if not feeds_by_category:
        _output_json({"status": "error", "message": "Nessun feed trovato nel file OPML"})
        return

    feed_count = sum(len(feeds) for feeds in feeds_by_category.values())
    logger.info("Parsed %d feeds in %d categories", feed_count, len(feeds_by_category))

    # 2. Fetch feeds
    items_by_category = fetch_feeds(feeds_by_category, hours=hours, max_items=max_items)
    item_count = sum(len(items) for items in items_by_category.values())
    logger.info("Fetched %d items from %d categories", item_count, len(items_by_category))

    if dry_run:
        _output_json({"status": "ok", "feed_count": feed_count, "item_count": item_count})
        return

    if item_count == 0:
        _output_json({"status": "error", "message": "Nessun articolo trovato nel periodo selezionato"})
        return

    # Save full digest for fallback (verbose format)
    work_dir = Path(__file__).parent / ".work"
    work_dir.mkdir(exist_ok=True)
    full_digest = format_digest(items_by_category, today_date)
    digest_path = work_dir / f"digest_{today}.md"
    digest_path.write_text(full_digest, encoding="utf-8")

    profile_text = Path(profile).read_text(encoding="utf-8")

    # Build compact profile for category calls (saves ~70% of profile tokens per call)
    compact_profile = condense_profile(profile_text)
    if compact_profile and compact_profile != profile_text.strip():
        logger.info(
            "Profile condensed: %d chars → %d chars (keywords only for phase 1)",
            len(profile_text), len(compact_profile),
        )

    # 2b. Pre-filter: local relevance scoring, dedup, summary truncation
    filtered = prefilter_items(items_by_category, profile_text)
    filtered_count = sum(len(items) for items in filtered.values())
    logger.info(
        "Pre-filter: %d → %d items (%.0f%% saved before LLM)",
        item_count, filtered_count,
        (1 - filtered_count / max(item_count, 1)) * 100,
    )

    if filtered_count == 0:
        logger.warning("Pre-filter removed all items, falling back to unfiltered")
        filtered = items_by_category

    # 3. Phase 1 — Per-category analysis
    effective_cat_model = category_model or model
    logger.info(
        "Phase 1: Analyzing %d categories%s...",
        len(filtered),
        f" (model: {effective_cat_model})" if effective_cat_model else "",
    )
    category_analyses, category_successes = _analyze_categories(
        filtered, profile_text, language, work_dir, today, model,
        provider=provider, endpoint=endpoint,
        category_model=category_model, compact_profile=compact_profile,
    )
    logger.info("Phase 1 done: %d/%d categories analyzed by %s", category_successes, len(filtered), provider)

    # 4. Phase 2 — Synthesis (only if we have at least some Claude analyses)
    #    Synthesis always uses the main --model (full quality) + full profile text
    synthesis = None
    if category_successes > 0:
        logger.info(
            "Phase 2: Synthesis%s...",
            f" (model: {model})" if model else "",
        )
        synthesis = _synthesize(
            category_analyses, profile_text, language, today_date, work_dir, today, model,
            provider=provider, endpoint=endpoint,
        )
        if synthesis:
            logger.info("Synthesis: OK")
        else:
            logger.warning("Synthesis: Claude failed, briefing will lack overview sections")
    else:
        logger.warning("Phase 2 skipped: no successful category analyses")

    # 5. Assemble final markdown and generate outputs
    # Use compact format for the synthesis input as well
    if category_successes > 0:
        final_markdown = _assemble_briefing(synthesis, category_analyses, today_date)
    else:
        logger.warning("All analyses failed, using raw digest")
        final_markdown = full_digest

    # 5a. Always generate HTML standalone
    html_path = generate_html(final_markdown, today, output_dir, language, theme=theme)

    # 5b. Generate the chosen format
    if category_successes > 0:
        if output_format == "docx":
            main_path = generate_docx(final_markdown, today, output_dir, theme=theme)
        elif output_format == "pdf":
            main_path = _lazy_generate_pdf(html_path, today, output_dir)
        elif output_format == "epub":
            main_path = _lazy_generate_epub(final_markdown, today, output_dir, language, theme=theme)
        else:
            main_path = html_path
    else:
        main_path = generate_fallback_docx(full_digest, today, output_dir, theme=theme)

    # 5c. Regenerate portal index
    portal_path = regenerate_portal_index(output_dir, language)

    # 5d. Extract highlights for widget
    highlights = extract_highlights(final_markdown)

    _output_json({
        "status": "ok",
        "output_path": main_path,
        "html_path": html_path,
        "portal_path": portal_path,
        "feed_count": feed_count,
        "item_count": item_count,
        "highlights": highlights,
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="Specola Engine — RSS briefing generator")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    run_parser = subparsers.add_parser("run", help="Generate a briefing")
    run_parser.add_argument("--opml", required=True, help="Path to OPML file")
    run_parser.add_argument("--profile", required=True, help="Path to user profile file")
    run_parser.add_argument("--output-dir", required=True, help="Output directory for DOCX")
    run_parser.add_argument("--hours", type=int, default=24)
    run_parser.add_argument("--language", default="it", choices=["it", "en"])
    run_parser.add_argument("--format", default="docx", choices=["docx", "pdf", "epub"])
    run_parser.add_argument("--max-items", type=int, default=30)
    run_parser.add_argument("--model", default=None,
                            help="Model for synthesis (phase 2). Also used for categories if --category-model not set.")
    run_parser.add_argument("--category-model", default=None,
                            help="Faster/cheaper model for per-category analysis (phase 1). Falls back to --model.")
    run_parser.add_argument("--theme", default="corporate",
                            choices=["corporate", "minimal", "dark"],
                            help="Visual theme for output documents")
    run_parser.add_argument("--provider", default="claude",
                            choices=["claude", "codex", "lmstudio"])
    run_parser.add_argument("--endpoint", default=None,
                            help="Custom API endpoint (LMStudio)")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--verbose", action="store_true")

    args = parser.parse_args()

    if args.command == "run":
        run_engine(
            opml=args.opml,
            profile=args.profile,
            output_dir=args.output_dir,
            hours=args.hours,
            language=args.language,
            max_items=args.max_items,
            model=args.model,
            dry_run=args.dry_run,
            verbose=args.verbose,
            output_format=args.format,
            provider=args.provider,
            endpoint=args.endpoint,
            theme=args.theme,
            category_model=args.category_model,
        )


if __name__ == "__main__":
    main()
