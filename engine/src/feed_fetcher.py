"""Feed fetching: OPML parsing, concurrent RSS fetch, digest formatting."""

from __future__ import annotations

import html
import logging
import re
import sys
import xml.etree.ElementTree as ET
from calendar import timegm
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import feedparser
from dateutil import parser as dateutil_parser

logger = logging.getLogger("specola.feed_fetcher")

_PREFIX_RE = re.compile(r"^\d+\s*[–\-\.]\s*")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def parse_opml(path: str | Path) -> dict[str, list[dict[str, str]]]:
    """Parse OPML file into {category_name: [{title, xmlUrl, htmlUrl}]}.

    First-level <outline> = category. Children with type="rss" = feed.
    Numeric prefixes stripped. Sorted by category name.
    """
    tree = ET.parse(path)
    body = tree.getroot().find("body")
    if body is None:
        return {}

    categories: dict[str, list[dict[str, str]]] = {}
    for outline in body:
        raw_name = outline.get("text", outline.get("title", ""))
        name = _PREFIX_RE.sub("", raw_name).strip()
        if not name:
            continue
        feeds = []
        for child in outline:
            if child.get("type", "").lower() == "rss":
                feeds.append({
                    "title": child.get("text", child.get("title", "")),
                    "xmlUrl": child.get("xmlUrl", ""),
                    "htmlUrl": child.get("htmlUrl", ""),
                })
        if feeds:
            categories[name] = feeds

    return dict(sorted(categories.items()))


def strip_html(text: str, max_length: int = 500) -> str:
    """Remove HTML tags, unescape entities, collapse whitespace, truncate."""
    if not text:
        return ""
    text = _HTML_TAG_RE.sub("", text)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:max_length]


def parse_item_date(entry) -> datetime | None:
    """Extract datetime from feedparser entry.

    Tries published_parsed -> updated_parsed -> dateutil on raw string fields.
    Returns a timezone-aware UTC datetime, or None if unparseable.
    """
    for attr in ("published_parsed", "updated_parsed"):
        ts = getattr(entry, attr, None)
        if ts:
            try:
                return datetime.fromtimestamp(timegm(ts), tz=timezone.utc)
            except (ValueError, OverflowError):
                continue

    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = dateutil_parser.parse(raw)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, OverflowError):
                continue

    return None


def _fetch_single_feed(
    feed: dict,
    category: str,
    hours: int,
    max_items: int,
) -> tuple:
    """Fetch and filter a single RSS feed.

    Returns (category, list[FeedItem]).  On any error returns (category, []).
    FeedItem keys: title, link, published, summary, source.
    """
    url = feed.get("xmlUrl", "")
    source_name = feed.get("title", url)

    try:
        fp = feedparser.parse(url, agent="Specola/1.0")
    except Exception as exc:  # noqa: BLE001
        print(f"DEBUG: Failed to fetch feed {url}: {exc}", file=sys.stderr)
        return (category, [])

    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    items: list[dict] = []

    for entry in fp.entries:
        dt = parse_item_date(entry)

        # Items with no parseable date are always included
        if dt is not None and dt < cutoff:
            continue

        # Extract summary from entry.summary -> entry.description -> entry.content[0].value
        raw_summary = (
            getattr(entry, "summary", None)
            or getattr(entry, "description", None)
        )
        if not raw_summary:
            content = getattr(entry, "content", None)
            if content and isinstance(content, list):
                raw_summary = content[0].get("value", "")

        summary = strip_html(raw_summary or "", max_length=500)

        published_str: str
        if dt is not None:
            published_str = dt.strftime("%Y-%m-%d %H:%M")
        else:
            published_str = "data n/d"

        items.append({
            "title": getattr(entry, "title", ""),
            "link": getattr(entry, "link", ""),
            "published": published_str,
            "summary": summary,
            "source": source_name,
        })

    # Sort by date descending; items with "data n/d" go to the end
    def sort_key(item: dict) -> str:
        return item["published"] if item["published"] != "data n/d" else ""

    items.sort(key=sort_key, reverse=True)
    return (category, items[:max_items])


def fetch_feeds(
    feeds_by_category: dict,
    hours: int = 24,
    max_items: int = 30,
) -> dict:
    """Fetch all feeds concurrently.

    Args:
        feeds_by_category: {category: [{title, xmlUrl, htmlUrl}]}
        hours: time window to include items from
        max_items: max items per category across all feeds in that category

    Returns:
        {category: [FeedItem, ...]}
    """
    # Build a flat list of (feed, category) tasks
    tasks: list[tuple[dict, str]] = []
    for category, feeds in feeds_by_category.items():
        for feed in feeds:
            tasks.append((feed, category))

    # Accumulate results per category
    results: dict = {cat: [] for cat in feeds_by_category}

    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_task = {
            executor.submit(_fetch_single_feed, feed, category, hours, max_items): (feed, category)
            for feed, category in tasks
        }
        for future in as_completed(future_to_task):
            try:
                cat, items = future.result()
            except Exception as exc:  # noqa: BLE001
                _, category = future_to_task[future]
                print(f"DEBUG: Unexpected error for category {category}: {exc}", file=sys.stderr)
                continue
            results[cat].extend(items)

    # Re-sort and cap per category after merging all feeds
    def sort_key(item: dict) -> str:
        return item["published"] if item["published"] != "data n/d" else ""

    for cat in results:
        results[cat].sort(key=sort_key, reverse=True)
        results[cat] = results[cat][:max_items]

    return results
