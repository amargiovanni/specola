#!/usr/bin/env python3
"""Specola Engine — RSS briefing generator powered by Claude Code CLI.

Two-phase analysis:
  Phase 1: Per-category analysis (one small Claude call per category)
  Phase 2: Synthesis (one Claude call to produce cross-cutting sections)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.feed_fetcher import parse_opml, fetch_feeds, format_digest
from src.prompt_builder import build_category_prompt, build_synthesis_prompt
from src.analyzer import analyze_with_claude
from src.doc_generator import generate_docx, generate_fallback_docx

logger = logging.getLogger("specola")

# Timeout per call: 120s per category, 180s for synthesis
CATEGORY_TIMEOUT = 120
SYNTHESIS_TIMEOUT = 180


def _output_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False))


def _analyze_categories(
    items_by_category: dict[str, list[dict]],
    profile_text: str,
    language: str,
    work_dir: Path,
    today: str,
    model: str | None,
) -> tuple[dict[str, str], int]:
    """Phase 1: Analyze each category independently.

    Returns (category_analyses, success_count).
    """
    results = {}
    total = len(items_by_category)
    success_count = 0

    for i, (category, items) in enumerate(items_by_category.items(), 1):
        logger.info("  [%d/%d] Analyzing: %s (%d items)", i, total, category, len(items))

        # Build mini-digest for this category
        mini_digest = format_digest({category: items}, date.today().isoformat())
        digest_path = work_dir / f"cat_{category.replace(' ', '_')}_{today}.md"
        digest_path.write_text(mini_digest, encoding="utf-8")

        # Build prompt and call Claude
        prompt = build_category_prompt(profile_text, language, category)
        analysis = analyze_with_claude(
            digest_path, prompt, model=model, timeout=CATEGORY_TIMEOUT
        )

        if analysis:
            results[category] = analysis.strip()
            success_count += 1
            logger.info("  [%d/%d] %s: OK", i, total, category)
        else:
            # Fallback: include raw items as plain text
            raw = "\n".join(
                f"- {item['title']} ({item['source']}) — {item['summary']}"
                for item in items
            )
            results[category] = raw
            logger.warning("  [%d/%d] %s: Claude failed, using raw items", i, total, category)

    return results, success_count


def _synthesize(
    category_analyses: dict[str, str],
    profile_text: str,
    language: str,
    date_display: str,
    work_dir: Path,
    today: str,
    model: str | None,
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
    return analyze_with_claude(
        analyses_path, prompt, model=model, timeout=SYNTHESIS_TIMEOUT
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

    # Save full digest for fallback
    work_dir = Path(__file__).parent / ".work"
    work_dir.mkdir(exist_ok=True)
    full_digest = format_digest(items_by_category, today_date)
    digest_path = work_dir / f"digest_{today}.md"
    digest_path.write_text(full_digest, encoding="utf-8")

    profile_text = Path(profile).read_text(encoding="utf-8")

    # 3. Phase 1 — Per-category analysis
    logger.info("Phase 1: Analyzing %d categories...", len(items_by_category))
    category_analyses, category_successes = _analyze_categories(
        items_by_category, profile_text, language, work_dir, today, model
    )
    logger.info("Phase 1 done: %d/%d categories analyzed by Claude", category_successes, len(items_by_category))

    # 4. Phase 2 — Synthesis (only if we have at least some Claude analyses)
    synthesis = None
    if category_successes > 0:
        logger.info("Phase 2: Synthesis...")
        synthesis = _synthesize(
            category_analyses, profile_text, language, today_date, work_dir, today, model
        )
        if synthesis:
            logger.info("Synthesis: OK")
        else:
            logger.warning("Synthesis: Claude failed, briefing will lack overview sections")
    else:
        logger.warning("Phase 2 skipped: no successful category analyses")

    # 5. Assemble final markdown and generate DOCX
    if category_successes > 0:
        final_markdown = _assemble_briefing(synthesis, category_analyses, today_date)
        output_path = generate_docx(final_markdown, today, output_dir)
    else:
        logger.warning("All analyses failed, generating fallback DOCX")
        output_path = generate_fallback_docx(full_digest, today, output_dir)

    _output_json({
        "status": "ok",
        "output_path": output_path,
        "feed_count": feed_count,
        "item_count": item_count,
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
    run_parser.add_argument("--max-items", type=int, default=30)
    run_parser.add_argument("--model", default=None)
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
        )


if __name__ == "__main__":
    main()
