#!/usr/bin/env python3
"""Specola Engine — RSS briefing generator powered by Claude Code CLI."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.feed_fetcher import parse_opml, fetch_feeds, format_digest
from src.prompt_builder import build_prompt
from src.analyzer import analyze_with_claude
from src.doc_generator import generate_docx, generate_fallback_docx

logger = logging.getLogger("specola")


def _output_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False))


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
        logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    today = date.today().isoformat()

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

    # 3. Generate digest markdown
    work_dir = Path(__file__).parent / ".work"
    work_dir.mkdir(exist_ok=True)
    digest = format_digest(items_by_category, today)
    digest_path = work_dir / f"digest_{today}.md"
    digest_path.write_text(digest, encoding="utf-8")

    # 4. Build prompt
    profile_text = Path(profile).read_text(encoding="utf-8")
    categories = list(items_by_category.keys())
    prompt = build_prompt(profile_text, language, categories, today)

    # 5. Analyze with Claude
    logger.info("Invoking Claude CLI...")
    analysis = analyze_with_claude(digest_path, prompt, model=model)

    # 6. Generate DOCX
    if analysis:
        output_path = generate_docx(analysis, today, output_dir)
    else:
        logger.warning("Claude analysis failed, generating fallback DOCX")
        output_path = generate_fallback_docx(digest, today, output_dir)

    _output_json({"status": "ok", "output_path": output_path, "feed_count": feed_count, "item_count": item_count})


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
