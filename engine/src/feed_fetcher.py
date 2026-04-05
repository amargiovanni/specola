"""Feed fetching: OPML parsing, concurrent RSS fetch, digest formatting."""

from __future__ import annotations

import html
import logging
import re
import xml.etree.ElementTree as ET
from calendar import timegm
from datetime import datetime, timezone
from pathlib import Path

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
