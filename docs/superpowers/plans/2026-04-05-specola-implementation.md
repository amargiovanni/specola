# Specola Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Specola — a macOS menubar app that generates daily AI-analyzed RSS briefings as DOCX files.

**Architecture:** Two-component system: a Python CLI engine (feed fetching, Claude CLI analysis, DOCX generation) invoked by a native Swift/SwiftUI menubar app (scheduling, UI, notifications). Components communicate via CLI arguments (Swift→Python) and JSON on stdout (Python→Swift).

**Tech Stack:** Python 3.12+ (feedparser, python-docx, python-dateutil) | Swift 5.9+ / SwiftUI / macOS 14+ | Claude Code CLI via subprocess | xcodegen for Xcode project generation

---

## File Structure

### Python Engine

```
engine/
├── specola_engine.py           # Entry point, argparse, orchestration
├── requirements.txt            # Runtime: feedparser, python-docx, python-dateutil
├── requirements-dev.txt        # Dev: pytest
├── setup_engine.sh             # Creates venv, installs runtime deps
├── src/
│   ├── __init__.py
│   ├── feed_fetcher.py         # OPML parsing + concurrent RSS fetch + digest formatting
│   ├── prompt_builder.py       # Prompt assembly (system + profile + output instructions)
│   ├── analyzer.py             # Claude CLI invocation via subprocess
│   └── doc_generator.py        # DOCX generation with python-docx
└── tests/
    ├── __init__.py
    ├── conftest.py             # Shared fixtures (tmp dirs, sample data)
    ├── fixtures/
    │   └── sample.opml         # Test OPML file
    ├── test_feed_fetcher.py
    ├── test_prompt_builder.py
    ├── test_analyzer.py
    ├── test_doc_generator.py
    └── test_engine.py          # Integration test
```

### Swift App

```
Specola/
├── SpecolaApp.swift            # @main, MenuBarExtra, first launch
├── MenuBarView.swift           # Popover content (header, list, actions, footer)
├── SettingsView.swift          # TabView: Fonti, Pianificazione, Profilo, Avanzate
├── Models/
│   ├── SpecolaEntry.swift      # Codable model for a single Specola (history item)
│   ├── AppState.swift          # @Observable: history, generation state, unread count
│   └── Settings.swift          # UserDefaults wrapper for app settings
├── Services/
│   ├── EngineService.swift     # Launches Python engine via Process, parses JSON output
│   ├── SchedulerService.swift  # 60s timer + wake-from-sleep detection
│   └── NotificationService.swift # UNUserNotificationCenter wrapper
├── Helpers/
│   └── MenuBarIcon.swift       # NSImage rendering for menubar icon + badge
├── Assets.xcassets/
│   └── AppIcon.appiconset/
└── Info.plist
SpecolaTests/
├── SpecolaEntryTests.swift
├── AppStateTests.swift
├── EngineServiceTests.swift
└── SchedulerServiceTests.swift
project.yml                     # xcodegen project definition
```

---

## Phase 1: Python Engine

### Task 1: Project Scaffolding

**Files:**
- Create: `engine/requirements.txt`
- Create: `engine/requirements-dev.txt`
- Create: `engine/setup_engine.sh`
- Create: `engine/src/__init__.py`
- Create: `engine/tests/__init__.py`
- Create: `engine/tests/conftest.py`
- Create: `engine/tests/fixtures/sample.opml`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p engine/src engine/tests/fixtures
```

- [ ] **Step 2: Write requirements.txt**

```
feedparser>=6.0
python-docx>=1.1
python-dateutil>=2.9
```

- [ ] **Step 3: Write requirements-dev.txt**

```
-r requirements.txt
pytest>=8.0
```

- [ ] **Step 4: Write setup_engine.sh**

```bash
#!/bin/bash
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Make it executable: `chmod +x engine/setup_engine.sh`

- [ ] **Step 5: Create Python package files**

`engine/src/__init__.py` — empty file.

`engine/tests/__init__.py` — empty file.

`engine/tests/conftest.py`:

```python
import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_opml_path():
    return FIXTURES_DIR / "sample.opml"


@pytest.fixture
def tmp_output_dir(tmp_path):
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def sample_items_by_category():
    return {
        "Tech": [
            {
                "title": "OpenAI releases GPT-5",
                "link": "https://example.com/gpt5",
                "published": "2026-04-05 09:30",
                "summary": "OpenAI has announced GPT-5 with improved reasoning.",
                "source": "TechCrunch",
            },
            {
                "title": "EU AI Act enforcement begins",
                "link": "https://example.com/ai-act",
                "published": "2026-04-05 08:15",
                "summary": "The EU AI Act enters enforcement phase today.",
                "source": "The Verge",
            },
        ],
        "Business": [
            {
                "title": "ECB holds rates steady",
                "link": "https://example.com/ecb",
                "published": "2026-04-05 07:00",
                "summary": "The European Central Bank maintained interest rates.",
                "source": "Bloomberg",
            },
        ],
    }
```

- [ ] **Step 6: Write test OPML fixture**

`engine/tests/fixtures/sample.opml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head><title>Test Feeds</title></head>
  <body>
    <outline text="01 – Tech" title="01 – Tech">
      <outline type="rss" text="Hacker News" title="Hacker News"
               xmlUrl="https://news.ycombinator.com/rss"
               htmlUrl="https://news.ycombinator.com"/>
      <outline type="rss" text="TechCrunch" title="TechCrunch"
               xmlUrl="https://techcrunch.com/feed/"
               htmlUrl="https://techcrunch.com"/>
    </outline>
    <outline text="02 – Business" title="02 – Business">
      <outline type="rss" text="Bloomberg" title="Bloomberg"
               xmlUrl="https://feeds.bloomberg.com/markets/news.rss"
               htmlUrl="https://bloomberg.com"/>
    </outline>
    <outline text="Dev Tools" title="Dev Tools">
      <outline type="rss" text="GitHub Blog" title="GitHub Blog"
               xmlUrl="https://github.blog/feed/"
               htmlUrl="https://github.blog"/>
    </outline>
  </body>
</opml>
```

- [ ] **Step 7: Set up venv and install dev dependencies**

```bash
cd engine
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

- [ ] **Step 8: Run pytest to verify setup**

```bash
cd engine && .venv/bin/python -m pytest tests/ -v
```

Expected: `no tests ran` (0 collected), exit 5. No import errors.

- [ ] **Step 9: Commit**

```bash
git add engine/
git commit -m "chore(engine): scaffold Python engine with dependencies and test fixtures"
```

---

### Task 2: OPML Parser

**Files:**
- Create: `engine/src/feed_fetcher.py`
- Create: `engine/tests/test_feed_fetcher.py`

- [ ] **Step 1: Write failing test for parse_opml**

`engine/tests/test_feed_fetcher.py`:

```python
from src.feed_fetcher import parse_opml


class TestParseOpml:
    def test_parses_categories_and_feeds(self, sample_opml_path):
        result = parse_opml(sample_opml_path)

        assert "Tech" in result
        assert "Business" in result
        assert "Dev Tools" in result

        assert len(result["Tech"]) == 2
        assert len(result["Business"]) == 1
        assert len(result["Dev Tools"]) == 1

    def test_strips_numeric_prefixes(self, sample_opml_path):
        result = parse_opml(sample_opml_path)

        # "01 – Tech" should become "Tech"
        assert "Tech" in result
        assert "01 – Tech" not in result

        # "02 – Business" should become "Business"
        assert "Business" in result
        assert "02 – Business" not in result

    def test_preserves_feed_attributes(self, sample_opml_path):
        result = parse_opml(sample_opml_path)

        hn = result["Tech"][0]
        assert hn["title"] == "Hacker News"
        assert hn["xmlUrl"] == "https://news.ycombinator.com/rss"
        assert hn["htmlUrl"] == "https://news.ycombinator.com"

    def test_categories_sorted_by_name(self, sample_opml_path):
        result = parse_opml(sample_opml_path)
        names = list(result.keys())

        assert names == sorted(names)

    def test_empty_opml(self, tmp_path):
        opml = tmp_path / "empty.opml"
        opml.write_text(
            '<?xml version="1.0"?><opml version="2.0">'
            "<head/><body/></opml>"
        )
        result = parse_opml(opml)
        assert result == {}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py -v
```

Expected: FAIL — `ImportError: cannot import name 'parse_opml' from 'src.feed_fetcher'`

- [ ] **Step 3: Implement parse_opml**

`engine/src/feed_fetcher.py`:

```python
"""Feed fetching: OPML parsing, concurrent RSS fetch, digest formatting."""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

# Regex to strip numeric prefixes like "01 – ", "02 - ", "1. "
_PREFIX_RE = re.compile(r"^\d+\s*[–\-\.]\s*")


def parse_opml(path: str | Path) -> dict[str, list[dict[str, str]]]:
    """Parse OPML file into {category_name: [{title, xmlUrl, htmlUrl}]}.

    First-level <outline> elements are categories.
    Their children with type="rss" are feeds.
    Numeric prefixes are stripped from category names.
    Result is sorted by category name.
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
                feeds.append(
                    {
                        "title": child.get("text", child.get("title", "")),
                        "xmlUrl": child.get("xmlUrl", ""),
                        "htmlUrl": child.get("htmlUrl", ""),
                    }
                )

        if feeds:
            categories[name] = feeds

    return dict(sorted(categories.items()))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/feed_fetcher.py engine/tests/test_feed_fetcher.py
git commit -m "feat(engine): add OPML parser with category extraction and prefix stripping"
```

---

### Task 3: HTML Stripping and Date Utilities

**Files:**
- Modify: `engine/src/feed_fetcher.py`
- Modify: `engine/tests/test_feed_fetcher.py`

- [ ] **Step 1: Write failing tests for strip_html and parse_item_date**

Append to `engine/tests/test_feed_fetcher.py`:

```python
from datetime import datetime, timezone
from src.feed_fetcher import strip_html, parse_item_date


class TestStripHtml:
    def test_removes_tags(self):
        assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_unescapes_entities(self):
        assert strip_html("&amp; &lt; &gt; &quot;") == '& < > "'

    def test_collapses_whitespace(self):
        assert strip_html("  hello   world  \n\n  foo  ") == "hello world foo"

    def test_empty_input(self):
        assert strip_html("") == ""

    def test_truncates_to_max_length(self):
        long_text = "a" * 600
        result = strip_html(long_text, max_length=500)
        assert len(result) == 500


class TestParseItemDate:
    def test_published_parsed(self):
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        # feedparser time_struct: (2026, 4, 5, 9, 30, 0, 5, 95, 0)
        entry.published_parsed = (2026, 4, 5, 9, 30, 0, 5, 95, 0)
        entry.updated_parsed = None
        entry.published = ""
        entry.updated = ""

        result = parse_item_date(entry)
        assert result is not None
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 5

    def test_fallback_to_dateutil(self):
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = "Sat, 05 Apr 2026 09:30:00 +0000"
        entry.updated = ""

        result = parse_item_date(entry)
        assert result is not None
        assert result.year == 2026

    def test_returns_none_for_unparseable(self):
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = ""
        entry.updated = ""

        result = parse_item_date(entry)
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py::TestStripHtml tests/test_feed_fetcher.py::TestParseItemDate -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement strip_html and parse_item_date**

Add to `engine/src/feed_fetcher.py` (after the existing imports):

```python
import html
import logging
from calendar import timegm
from datetime import datetime, timezone

from dateutil import parser as dateutil_parser

logger = logging.getLogger("specola.feed_fetcher")

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html(text: str, max_length: int = 500) -> str:
    """Remove HTML tags, unescape entities, collapse whitespace, truncate."""
    if not text:
        return ""
    text = _HTML_TAG_RE.sub("", text)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text[:max_length]


def parse_item_date(entry) -> datetime | None:
    """Extract datetime from a feedparser entry.

    Tries: published_parsed → updated_parsed → dateutil parse of string fields.
    Returns timezone-aware UTC datetime, or None.
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
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py -v
```

Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/feed_fetcher.py engine/tests/test_feed_fetcher.py
git commit -m "feat(engine): add HTML stripping and date parsing utilities"
```

---

### Task 4: RSS Fetcher

**Files:**
- Modify: `engine/src/feed_fetcher.py`
- Modify: `engine/tests/test_feed_fetcher.py`

- [ ] **Step 1: Write failing tests for fetch_feeds**

Append to `engine/tests/test_feed_fetcher.py`:

```python
from unittest.mock import patch, MagicMock
from src.feed_fetcher import fetch_feeds


class TestFetchFeeds:
    def _make_entry(self, title, summary, published_parsed, link="https://example.com"):
        entry = MagicMock()
        entry.title = title
        entry.link = link
        entry.get.side_effect = lambda k, d=None: getattr(entry, k, d)
        entry.summary = summary
        entry.description = summary
        entry.published_parsed = published_parsed
        entry.updated_parsed = None
        entry.published = ""
        entry.updated = ""
        # Make hasattr work for content
        if hasattr(entry, "content"):
            del entry.content
        return entry

    @patch("src.feed_fetcher.feedparser")
    def test_fetches_and_filters_by_time(self, mock_fp):
        from datetime import datetime, timezone, timedelta
        from calendar import timegm

        now = datetime.now(timezone.utc)
        recent = now - timedelta(hours=2)
        old = now - timedelta(hours=48)

        recent_ts = recent.timetuple()[:9]
        old_ts = old.timetuple()[:9]

        mock_fp.parse.return_value = MagicMock(
            entries=[
                self._make_entry("Recent Article", "Summary of recent", recent_ts),
                self._make_entry("Old Article", "Summary of old", old_ts),
            ],
            feed=MagicMock(title="Test Feed"),
        )

        feeds = {"Tech": [{"title": "Test Feed", "xmlUrl": "https://example.com/rss", "htmlUrl": ""}]}
        result = fetch_feeds(feeds, hours=24, max_items=30)

        assert "Tech" in result
        assert len(result["Tech"]) == 1
        assert result["Tech"][0]["title"] == "Recent Article"

    @patch("src.feed_fetcher.feedparser")
    def test_includes_items_with_no_date(self, mock_fp):
        entry = self._make_entry("No Date Article", "Some summary", None)
        entry.published_parsed = None

        mock_fp.parse.return_value = MagicMock(
            entries=[entry],
            feed=MagicMock(title="Test Feed"),
        )

        feeds = {"Tech": [{"title": "Test Feed", "xmlUrl": "https://example.com/rss", "htmlUrl": ""}]}
        result = fetch_feeds(feeds, hours=24, max_items=30)

        assert len(result["Tech"]) == 1

    @patch("src.feed_fetcher.feedparser")
    def test_respects_max_items(self, mock_fp):
        from datetime import datetime, timezone, timedelta

        now = datetime.now(timezone.utc)
        entries = []
        for i in range(10):
            ts = (now - timedelta(hours=i)).timetuple()[:9]
            entries.append(self._make_entry(f"Article {i}", f"Summary {i}", ts))

        mock_fp.parse.return_value = MagicMock(
            entries=entries,
            feed=MagicMock(title="Test Feed"),
        )

        feeds = {"Tech": [{"title": "Test Feed", "xmlUrl": "https://example.com/rss", "htmlUrl": ""}]}
        result = fetch_feeds(feeds, hours=48, max_items=3)

        assert len(result["Tech"]) == 3

    @patch("src.feed_fetcher.feedparser")
    def test_strips_html_from_summary(self, mock_fp):
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        ts = now.timetuple()[:9]

        entry = self._make_entry("Article", "<p>Hello <b>world</b></p>", ts)

        mock_fp.parse.return_value = MagicMock(
            entries=[entry],
            feed=MagicMock(title="Test Feed"),
        )

        feeds = {"Tech": [{"title": "Test Feed", "xmlUrl": "https://example.com/rss", "htmlUrl": ""}]}
        result = fetch_feeds(feeds, hours=24, max_items=30)

        assert result["Tech"][0]["summary"] == "Hello world"

    @patch("src.feed_fetcher.feedparser")
    def test_handles_feed_failure_gracefully(self, mock_fp):
        mock_fp.parse.side_effect = Exception("Network error")

        feeds = {"Tech": [{"title": "Broken Feed", "xmlUrl": "https://broken.com/rss", "htmlUrl": ""}]}
        result = fetch_feeds(feeds, hours=24, max_items=30)

        # Should return empty, not crash
        assert result == {} or result.get("Tech", []) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py::TestFetchFeeds -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement fetch_feeds**

Add to `engine/src/feed_fetcher.py` (after the existing functions):

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

import feedparser


def _fetch_single_feed(
    feed: dict[str, str],
    category: str,
    hours: int,
    max_items: int,
) -> tuple[str, list[dict]]:
    """Fetch one RSS feed, filter items by time window. Returns (category, items)."""
    url = feed.get("xmlUrl", "")
    feed_title = feed.get("title", url)
    if not url:
        return category, []

    try:
        feedparser.USER_AGENT = "Specola/1.0"
        parsed = feedparser.parse(url)
    except Exception as e:
        logger.debug("Failed to fetch %s: %s", url, e)
        return category, []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items = []

    for entry in parsed.entries:
        dt = parse_item_date(entry)

        # Filter by time window; include items with unknown date
        if dt is not None and dt < cutoff:
            continue

        # Extract summary
        summary_raw = getattr(entry, "summary", "") or getattr(entry, "description", "")
        if not summary_raw:
            content = getattr(entry, "content", None)
            if content and len(content) > 0:
                summary_raw = content[0].get("value", "")

        published_str = dt.strftime("%Y-%m-%d %H:%M") if dt else "data n/d"

        items.append(
            {
                "title": getattr(entry, "title", "Senza titolo"),
                "link": getattr(entry, "link", ""),
                "published": published_str,
                "summary": strip_html(summary_raw, max_length=500),
                "source": feed_title,
            }
        )

    # Sort by date descending (items with "data n/d" go last)
    items.sort(key=lambda x: x["published"], reverse=True)
    return category, items[:max_items]


def fetch_feeds(
    feeds_by_category: dict[str, list[dict[str, str]]],
    hours: int = 24,
    max_items: int = 30,
) -> dict[str, list[dict]]:
    """Fetch all feeds concurrently, return {category: [FeedItem]}."""
    all_items: dict[str, list[dict]] = {}

    tasks = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for category, feeds in feeds_by_category.items():
            for feed in feeds:
                tasks.append(
                    executor.submit(_fetch_single_feed, feed, category, hours, max_items)
                )

        for future in as_completed(tasks):
            try:
                category, items = future.result(timeout=15)
            except Exception as e:
                logger.debug("Feed fetch task failed: %s", e)
                continue

            if items:
                if category not in all_items:
                    all_items[category] = []
                all_items[category].extend(items)

    # Trim per-category to max_items, sort by date desc
    for category in all_items:
        all_items[category].sort(key=lambda x: x["published"], reverse=True)
        all_items[category] = all_items[category][:max_items]

    return {k: v for k, v in sorted(all_items.items()) if v}
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py -v
```

Expected: all 18 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/feed_fetcher.py engine/tests/test_feed_fetcher.py
git commit -m "feat(engine): add concurrent RSS fetcher with time filtering and HTML stripping"
```

---

### Task 5: Digest Formatter

**Files:**
- Modify: `engine/src/feed_fetcher.py`
- Modify: `engine/tests/test_feed_fetcher.py`

- [ ] **Step 1: Write failing test for format_digest**

Append to `engine/tests/test_feed_fetcher.py`:

```python
from src.feed_fetcher import format_digest


class TestFormatDigest:
    def test_produces_markdown_with_categories(self, sample_items_by_category):
        result = format_digest(sample_items_by_category, "2026-04-05")

        assert "# Feed Digest" in result
        assert "2026-04-05" in result
        assert "## Tech" in result
        assert "## Business" in result

    def test_includes_item_details(self, sample_items_by_category):
        result = format_digest(sample_items_by_category, "2026-04-05")

        assert "OpenAI releases GPT-5" in result
        assert "TechCrunch" in result
        assert "https://example.com/gpt5" in result
        assert "OpenAI has announced GPT-5" in result

    def test_empty_categories(self):
        result = format_digest({}, "2026-04-05")

        assert "# Feed Digest" in result
        assert "Nessun articolo" in result

    def test_returns_category_count(self, sample_items_by_category):
        result = format_digest(sample_items_by_category, "2026-04-05")

        # Should have both categories as H2 headers
        assert result.count("\n## ") == 2
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py::TestFormatDigest -v
```

Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement format_digest**

Add to `engine/src/feed_fetcher.py`:

```python
def format_digest(items_by_category: dict[str, list[dict]], date: str) -> str:
    """Format feed items into a markdown digest for Claude analysis."""
    lines = [f"# Feed Digest — {date}", ""]

    if not items_by_category:
        lines.append("Nessun articolo trovato nel periodo selezionato.")
        return "\n".join(lines)

    for category, items in sorted(items_by_category.items()):
        lines.append(f"## {category}")
        lines.append("")

        for item in items:
            lines.append(f"### {item['title']} ({item['source']})")
            lines.append(f"- Data: {item['published']}")
            if item.get("link"):
                lines.append(f"- Link: {item['link']}")
            lines.append("")
            if item.get("summary"):
                lines.append(item["summary"])
            lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_feed_fetcher.py -v
```

Expected: all 22 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/feed_fetcher.py engine/tests/test_feed_fetcher.py
git commit -m "feat(engine): add digest markdown formatter"
```

---

### Task 6: Prompt Builder

**Files:**
- Create: `engine/src/prompt_builder.py`
- Create: `engine/tests/test_prompt_builder.py`

- [ ] **Step 1: Write failing tests**

`engine/tests/test_prompt_builder.py`:

```python
from src.prompt_builder import build_prompt, SYSTEM_INSTRUCTION, OUTPUT_INSTRUCTIONS_IT, OUTPUT_INSTRUCTIONS_EN


class TestBuildPrompt:
    def test_italian_prompt_contains_all_parts(self):
        profile = "Sono un CTO di una startup fintech."
        categories = ["Tech", "Business"]
        result = build_prompt(profile, "it", categories, "2026-04-05")

        assert SYSTEM_INSTRUCTION in result
        assert profile in result
        assert "Da sapere oggi" in result
        assert "Richiede attenzione" in result
        assert "Per area tematica" in result
        assert "Da leggere con calma" in result
        assert "Spunti" in result
        assert "Tech" in result
        assert "Business" in result

    def test_english_prompt_contains_all_parts(self):
        profile = "I'm a CTO at a fintech startup."
        categories = ["Tech"]
        result = build_prompt(profile, "en", categories, "2026-04-05")

        assert SYSTEM_INSTRUCTION in result
        assert profile in result
        assert "Must know today" in result
        assert "Needs attention" in result
        assert "By topic" in result
        assert "Deep reads" in result
        assert "Ideas" in result

    def test_profile_injected_verbatim(self):
        profile = "Custom profile with special chars: éàü"
        result = build_prompt(profile, "it", ["Tech"], "2026-04-05")

        assert "Custom profile with special chars: éàü" in result

    def test_date_included(self):
        result = build_prompt("profile", "it", ["Tech"], "2026-04-05")
        assert "2026-04-05" in result

    def test_categories_listed(self):
        categories = ["Tech", "Business", "Dev Tools"]
        result = build_prompt("profile", "it", categories, "2026-04-05")

        assert "Tech" in result
        assert "Business" in result
        assert "Dev Tools" in result

    def test_defaults_to_italian(self):
        result = build_prompt("profile", "xx", ["Tech"], "2026-04-05")
        # Unknown language falls back to Italian
        assert "Da sapere oggi" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_prompt_builder.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement prompt_builder**

`engine/src/prompt_builder.py`:

```python
"""Prompt construction for Claude analysis."""

SYSTEM_INSTRUCTION = (
    "Sei Specola, un assistente che produce briefing giornalieri da fonti RSS.\n"
    "Analizza il digest in input, prioritizza le notizie in base al profilo\n"
    "dell'utente, e produci un briefing strutturato e approfondito."
)

OUTPUT_INSTRUCTIONS_IT = """\
Produci il briefing in markdown:

# Specola — Briefing del {date}

## Da sapere oggi
3-5 punti. Le cose più importanti per il profilo dell'utente. Una riga ciascuno.

## Richiede attenzione
Sviluppi che richiedono azione o valutazione entro la settimana. Per ciascuno: \
cosa è successo, perché conta per l'utente, cosa fare. Se non c'è nulla, ometti.

## Per area tematica
Per ogni categoria del digest che contiene notizie rilevanti, crea una sezione \
H2 con il nome della categoria. Dentro: item ordinati per rilevanza, sintesi di \
una o due frasi ciascuno, fonte tra parentesi. Ometti categorie senza notizie rilevanti.

## Da leggere con calma
Articoli di approfondimento non urgenti ma di valore.

## Spunti
2-3 idee per riflessioni, post, o azioni ispirate dalle notizie del giorno.

Regole:
- Scrivi in italiano
- Zero fuffa, zero premesse
- Ogni item ha la fonte tra parentesi
- Sezioni vuote: omettile
- Ordine per rilevanza decrescente
- Non inventare notizie assenti dal digest
- Max 3000 parole"""

OUTPUT_INSTRUCTIONS_EN = """\
Produce the briefing in markdown:

# Specola — Briefing for {date}

## Must know today
3-5 points. The most important things for the user's profile. One line each.

## Needs attention
Developments that require action or evaluation within the week. For each: \
what happened, why it matters for the user, what to do. If nothing qualifies, omit.

## By topic
For each digest category that contains relevant news, create an H2 section \
with the category name. Inside: items ordered by relevance, one or two sentence \
summary each, source in parentheses. Omit categories with no relevant news.

## Deep reads
In-depth articles that are not urgent but valuable.

## Ideas
2-3 ideas for reflections, posts, or actions inspired by today's news.

Rules:
- Write in English
- Zero fluff, zero preamble
- Every item has its source in parentheses
- Empty sections: omit them
- Order by decreasing relevance
- Do not invent news absent from the digest
- Max 3000 words"""


def build_prompt(
    profile: str, language: str, categories: list[str], date: str
) -> str:
    """Assemble the complete prompt from system instruction, profile, and output instructions."""
    output_instructions = (
        OUTPUT_INSTRUCTIONS_EN if language == "en" else OUTPUT_INSTRUCTIONS_IT
    )

    parts = [
        SYSTEM_INSTRUCTION,
        "",
        "Profilo dell'utente:",
        "---",
        profile,
        "---",
        "",
        output_instructions.format(date=date),
        "",
        "Categorie presenti nel digest:",
        *[f"- {cat}" for cat in categories],
    ]

    return "\n".join(parts)
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_prompt_builder.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/prompt_builder.py engine/tests/test_prompt_builder.py
git commit -m "feat(engine): add prompt builder with Italian and English templates"
```

---

### Task 7: Analyzer

**Files:**
- Create: `engine/src/analyzer.py`
- Create: `engine/tests/test_analyzer.py`

- [ ] **Step 1: Write failing tests**

`engine/tests/test_analyzer.py`:

```python
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.analyzer import analyze_with_claude


class TestAnalyzeWithClaude:
    def test_success(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("# Test digest\n\nSome content")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "# Briefing\n\n## Da sapere oggi\n- Point 1"

        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            result = analyze_with_claude(digest, "prompt text")

            assert result == mock_result.stdout
            mock_run.assert_called_once()
            args = mock_run.call_args
            assert args[0][0] == ["claude", "-p", "prompt text"]
            assert args[1]["text"] is True
            assert args[1]["capture_output"] is True

    def test_with_model(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")

        mock_result = MagicMock(returncode=0, stdout="output")

        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            analyze_with_claude(digest, "prompt", model="opus")

            cmd = mock_run.call_args[0][0]
            assert "--model" in cmd
            assert "opus" in cmd

    def test_failure_returns_none(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")

        mock_result = MagicMock(returncode=1, stdout="", stderr="error")

        with patch("src.analyzer.subprocess.run", return_value=mock_result):
            result = analyze_with_claude(digest, "prompt")
            assert result is None

    def test_timeout_returns_none(self, tmp_path):
        import subprocess

        digest = tmp_path / "digest.md"
        digest.write_text("content")

        with patch("src.analyzer.subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 300)):
            result = analyze_with_claude(digest, "prompt", timeout=300)
            assert result is None

    def test_file_not_found_returns_none(self, tmp_path):
        missing = tmp_path / "nonexistent.md"

        with patch("src.analyzer.subprocess.run", side_effect=FileNotFoundError("claude not found")):
            result = analyze_with_claude(missing, "prompt")
            assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_analyzer.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement analyzer**

`engine/src/analyzer.py`:

```python
"""Claude Code CLI invocation."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("specola.analyzer")


def analyze_with_claude(
    digest_path: Path,
    prompt: str,
    model: str | None = None,
    timeout: int = 300,
) -> str | None:
    """Invoke Claude CLI with prompt and digest as stdin. Returns markdown or None."""
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])

    try:
        with open(digest_path, "r") as f:
            result = subprocess.run(
                cmd, stdin=f, capture_output=True, text=True, timeout=timeout
            )
    except FileNotFoundError:
        logger.error("Claude CLI not found in PATH")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timed out after %d seconds", timeout)
        return None

    if result.returncode != 0:
        logger.error("Claude CLI failed (exit %d): %s", result.returncode, result.stderr)
        return None

    return result.stdout
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_analyzer.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/analyzer.py engine/tests/test_analyzer.py
git commit -m "feat(engine): add Claude CLI analyzer via subprocess"
```

---

### Task 8: DOCX Generator

**Files:**
- Create: `engine/src/doc_generator.py`
- Create: `engine/tests/test_doc_generator.py`

- [ ] **Step 1: Write failing tests**

`engine/tests/test_doc_generator.py`:

```python
from pathlib import Path
from docx import Document
from src.doc_generator import generate_docx, generate_fallback_docx


class TestGenerateDocx:
    def test_creates_file(self, tmp_output_dir):
        md = "# Specola — Briefing del 2026-04-05\n\n## Da sapere oggi\n- Punto 1\n- Punto 2"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)

        assert Path(path).exists()
        assert Path(path).name == "Specola_2026-04-05.docx"

    def test_heading_levels(self, tmp_output_dir):
        md = "# H1 Title\n\n## H2 Section\n\n### H3 Subsection\n\nParagraph text."
        path = generate_docx(md, "2026-04-05", tmp_output_dir)

        doc = Document(path)
        styles = [p.style.name for p in doc.paragraphs]
        assert "Heading 1" in styles
        assert "Heading 2" in styles
        assert "Heading 3" in styles
        assert "Normal" in styles

    def test_bullet_lists(self, tmp_output_dir):
        md = "## Section\n\n- Item one\n- Item two\n* Item three"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)

        doc = Document(path)
        styles = [p.style.name for p in doc.paragraphs]
        assert styles.count("List Bullet") == 3

    def test_numbered_lists(self, tmp_output_dir):
        md = "## Section\n\n1. First\n2. Second\n3. Third"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)

        doc = Document(path)
        styles = [p.style.name for p in doc.paragraphs]
        assert styles.count("List Number") == 3

    def test_bold_text(self, tmp_output_dir):
        md = "## Section\n\nThis has **bold text** inside."
        path = generate_docx(md, "2026-04-05", tmp_output_dir)

        doc = Document(path)
        para = [p for p in doc.paragraphs if p.style.name == "Normal"][0]
        runs_bold = [r.bold for r in para.runs]
        assert True in runs_bold  # At least one bold run

    def test_header_contains_specola(self, tmp_output_dir):
        md = "# Title"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)

        doc = Document(path)
        header = doc.sections[0].header
        header_text = "".join(p.text for p in header.paragraphs)
        assert "Specola" in header_text

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "subdir" / "output"
        md = "# Title"
        path = generate_docx(md, "2026-04-05", new_dir)
        assert Path(path).exists()


class TestGenerateFallbackDocx:
    def test_creates_file_with_warning(self, tmp_output_dir):
        digest = "## Tech\n\n### Article 1\nSummary here"
        path = generate_fallback_docx(digest, "2026-04-05", tmp_output_dir)

        assert Path(path).exists()
        doc = Document(path)
        texts = [p.text for p in doc.paragraphs]
        # Should contain the warning
        assert any("Analisi non disponibile" in t for t in texts)
        # Should contain the digest content
        assert any("Article 1" in t for t in texts)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_doc_generator.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement doc_generator**

`engine/src/doc_generator.py`:

```python
"""DOCX generation from markdown."""

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")


def _set_default_font(doc: Document) -> None:
    """Set document default font to Calibri 11pt, line spacing 1.15."""
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15


def _configure_heading_style(doc: Document, level: int, size: int, color_hex: str) -> None:
    """Configure heading style with specific size and color."""
    style_name = f"Heading {level}"
    style = doc.styles[style_name]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(size)
    font.bold = True
    font.color.rgb = RGBColor.from_string(color_hex)

    pf = style.paragraph_format
    if level == 1:
        pf.space_before = Pt(18)
        pf.space_after = Pt(6)
    elif level == 2:
        pf.space_before = Pt(14)
        pf.space_after = Pt(4)
    elif level == 3:
        pf.space_before = Pt(10)
        pf.space_after = Pt(4)


def _setup_styles(doc: Document) -> None:
    """Configure all document styles."""
    _set_default_font(doc)
    _configure_heading_style(doc, 1, 18, "1a1a2e")
    _configure_heading_style(doc, 2, 14, "16213e")
    _configure_heading_style(doc, 3, 12, "0f3460")


def _setup_page(doc: Document) -> None:
    """Configure A4 page with 2.5cm margins."""
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)


def _setup_header_footer(doc: Document, date: str) -> None:
    """Add header (Specola | date) and footer (page number)."""
    section = doc.sections[0]

    # Header
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.clear()

    run_left = hp.add_run("Specola")
    run_left.font.size = Pt(9)
    run_left.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    hp.add_run("\t\t")

    run_right = hp.add_run(date)
    run_right.font.size = Pt(9)
    run_right.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # Set tab stops for right alignment
    hp.alignment = None  # custom via tab stops

    # Footer with page number
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.clear()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER

    run = fp.add_run()
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # Add PAGE field
    fld_char_begin = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
    run._r.append(fld_char_begin)

    instr = run._r.makeelement(qn("w:instrText"), {})
    instr.text = " PAGE "
    run._r.append(instr)

    fld_char_end = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
    run._r.append(fld_char_end)


def _add_paragraph_with_bold(doc: Document, text: str, style: str = "Normal") -> None:
    """Add a paragraph, converting **bold** markers to bold runs."""
    para = doc.add_paragraph(style=style)
    parts = _BOLD_RE.split(text)

    for i, part in enumerate(parts):
        if not part:
            continue
        run = para.add_run(part)
        if i % 2 == 1:  # odd indices are the captured bold groups
            run.bold = True


def generate_docx(markdown: str, date: str, output_dir: str | Path) -> str:
    """Generate DOCX from markdown. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.docx"

    doc = Document()
    _setup_styles(doc)
    _setup_page(doc)
    _setup_header_footer(doc, date)

    for line in markdown.split("\n"):
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("### "):
            _add_paragraph_with_bold(doc, stripped[4:], "Heading 3")
        elif stripped.startswith("## "):
            _add_paragraph_with_bold(doc, stripped[3:], "Heading 2")
        elif stripped.startswith("# "):
            _add_paragraph_with_bold(doc, stripped[2:], "Heading 1")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            _add_paragraph_with_bold(doc, stripped[2:], "List Bullet")
        elif _NUMBERED_RE.match(stripped):
            text = _NUMBERED_RE.sub("", stripped)
            _add_paragraph_with_bold(doc, text, "List Number")
        else:
            _add_paragraph_with_bold(doc, stripped)

    doc.save(str(output_path))
    return str(output_path)


def generate_fallback_docx(digest: str, date: str, output_dir: str | Path) -> str:
    """Generate fallback DOCX from raw digest with warning."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.docx"

    doc = Document()
    _setup_styles(doc)
    _setup_page(doc)
    _setup_header_footer(doc, date)

    # Warning paragraph in red
    warn = doc.add_paragraph()
    run = warn.add_run("\u26a0 Analisi non disponibile. Di seguito il digest grezzo.")
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    run.bold = True

    doc.add_paragraph()  # spacer

    # Add raw digest line by line
    for line in digest.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("### "):
            doc.add_paragraph(stripped[4:], "Heading 3")
        elif stripped.startswith("## "):
            doc.add_paragraph(stripped[3:], "Heading 2")
        elif stripped.startswith("# "):
            doc.add_paragraph(stripped[2:], "Heading 1")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            doc.add_paragraph(stripped[2:], "List Bullet")
        else:
            doc.add_paragraph(stripped)

    doc.save(str(output_path))
    return str(output_path)
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/test_doc_generator.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/src/doc_generator.py engine/tests/test_doc_generator.py
git commit -m "feat(engine): add DOCX generator with markdown parsing and fallback mode"
```

---

### Task 9: Engine CLI Orchestrator

**Files:**
- Create: `engine/specola_engine.py`
- Create: `engine/tests/test_engine.py`

- [ ] **Step 1: Write failing tests**

`engine/tests/test_engine.py`:

```python
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add engine root to path for importing specola_engine
sys.path.insert(0, str(Path(__file__).parent.parent))

from specola_engine import main, run_engine


class TestCLIParsing:
    def test_requires_subcommand(self):
        with patch("sys.argv", ["specola_engine.py"]):
            with patch("sys.exit") as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass

    def test_run_requires_opml(self):
        with patch("sys.argv", ["specola_engine.py", "run", "--profile", "p.md"]):
            with patch("sys.exit"):
                try:
                    main()
                except SystemExit:
                    pass


class TestRunEngine:
    @patch("specola_engine.analyze_with_claude")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_dry_run(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {
            "Tech": [
                {"title": "Art", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "S", "source": "Feed"}
            ]
        }

        run_engine(
            opml=str(opml),
            profile=str(profile),
            output_dir=str(output_dir),
            hours=24,
            language="it",
            max_items=30,
            model=None,
            dry_run=True,
            verbose=False,
        )

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert result["feed_count"] == 1
        assert result["item_count"] == 1
        mock_analyze.assert_not_called()

    @patch("specola_engine.generate_docx")
    @patch("specola_engine.analyze_with_claude")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_full_run_success(
        self, mock_parse, mock_fetch, mock_analyze, mock_docx, tmp_path, capsys
    ):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {
            "Tech": [
                {"title": "Art", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "S", "source": "Feed"}
            ]
        }
        mock_analyze.return_value = "# Briefing\n\n## Da sapere oggi\n- Point 1"
        mock_docx.return_value = str(output_dir / "Specola_2026-04-05.docx")

        run_engine(
            opml=str(opml),
            profile=str(profile),
            output_dir=str(output_dir),
            hours=24,
            language="it",
            max_items=30,
            model=None,
            dry_run=False,
            verbose=False,
        )

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert "output_path" in result
        mock_analyze.assert_called_once()
        mock_docx.assert_called_once()

    @patch("specola_engine.generate_fallback_docx")
    @patch("specola_engine.analyze_with_claude", return_value=None)
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_claude_failure_generates_fallback(
        self, mock_parse, mock_fetch, mock_analyze, mock_fallback, tmp_path, capsys
    ):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {
            "Tech": [
                {"title": "Art", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "S", "source": "Feed"}
            ]
        }
        mock_fallback.return_value = str(output_dir / "Specola_2026-04-05.docx")

        run_engine(
            opml=str(opml),
            profile=str(profile),
            output_dir=str(output_dir),
            hours=24,
            language="it",
            max_items=30,
            model=None,
            dry_run=False,
            verbose=False,
        )

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        mock_fallback.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd engine && .venv/bin/python -m pytest tests/test_engine.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement specola_engine.py**

`engine/specola_engine.py`:

```python
#!/usr/bin/env python3
"""Specola Engine — RSS briefing generator powered by Claude Code CLI."""

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
    """Print JSON result to stdout."""
    print(json.dumps(data, ensure_ascii=False))


def run_engine(
    opml: str,
    profile: str,
    output_dir: str,
    hours: int,
    language: str,
    max_items: int,
    model: str | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Main orchestration: fetch → analyze → generate DOCX."""
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
        _output_json({
            "status": "ok",
            "feed_count": feed_count,
            "item_count": item_count,
        })
        return

    if item_count == 0:
        _output_json({"status": "error", "message": "Nessun articolo trovato nel periodo selezionato"})
        return

    # 3. Generate digest markdown and save to .work/
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

    _output_json({
        "status": "ok",
        "output_path": output_path,
        "feed_count": feed_count,
        "item_count": item_count,
    })


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Specola Engine — RSS briefing generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Generate a briefing")
    run_parser.add_argument("--opml", required=True, help="Path to OPML file")
    run_parser.add_argument("--profile", required=True, help="Path to user profile file")
    run_parser.add_argument("--output-dir", required=True, help="Output directory for DOCX")
    run_parser.add_argument("--hours", type=int, default=24, help="Time window in hours (default: 24)")
    run_parser.add_argument("--language", default="it", choices=["it", "en"], help="Briefing language (default: it)")
    run_parser.add_argument("--max-items", type=int, default=30, help="Max items per category (default: 30)")
    run_parser.add_argument("--model", default=None, help="Claude model override")
    run_parser.add_argument("--dry-run", action="store_true", help="Fetch only, no Claude, no DOCX")
    run_parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging")

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
```

- [ ] **Step 4: Run all engine tests to verify they pass**

```bash
cd engine && .venv/bin/python -m pytest tests/ -v
```

Expected: all tests PASS (approximately 38 tests).

- [ ] **Step 5: Commit**

```bash
git add engine/specola_engine.py engine/tests/test_engine.py
git commit -m "feat(engine): add CLI orchestrator with argparse, dry-run mode, and fallback"
```

---

## Phase 2: Swift App

### Task 10: Xcode Project Setup

**Files:**
- Create: `project.yml`
- Create: `Specola/SpecolaApp.swift` (minimal)
- Create: `Specola/Info.plist`
- Create: `SpecolaTests/SpecolaTests.swift` (minimal)

**Prerequisites:** xcodegen must be installed. If not: `brew install xcodegen`

- [ ] **Step 1: Create project.yml for xcodegen**

`project.yml`:

```yaml
name: Specola
options:
  bundleIdPrefix: com.oltrematica
  deploymentTarget:
    macOS: "14.0"
  xcodeVersion: "16.0"
  createIntermediateGroups: true

settings:
  base:
    SWIFT_VERSION: "5.9"
    MACOSX_DEPLOYMENT_TARGET: "14.0"

targets:
  Specola:
    type: application
    platform: macOS
    sources:
      - path: Specola
    settings:
      base:
        INFOPLIST_FILE: Specola/Info.plist
        PRODUCT_BUNDLE_IDENTIFIER: com.oltrematica.specola
        PRODUCT_NAME: Specola
        CODE_SIGN_ENTITLEMENTS: ""
        ENABLE_APP_SANDBOX: false
    info:
      path: Specola/Info.plist
      properties:
        LSUIElement: true
        CFBundleName: Specola
        CFBundleDisplayName: Specola
        CFBundleIdentifier: com.oltrematica.specola
        CFBundleVersion: "1"
        CFBundleShortVersionString: "1.0"
        LSMinimumSystemVersion: "14.0"
        NSHumanReadableCopyright: "Copyright © 2026 Oltrematica. All rights reserved."

  SpecolaTests:
    type: bundle.unit-test
    platform: macOS
    sources:
      - path: SpecolaTests
    dependencies:
      - target: Specola
    settings:
      base:
        PRODUCT_BUNDLE_IDENTIFIER: com.oltrematica.specola.tests
        TEST_HOST: "$(BUILT_PRODUCTS_DIR)/Specola.app/Contents/MacOS/Specola"
        BUNDLE_LOADER: "$(TEST_HOST)"
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p Specola/Models Specola/Services Specola/Helpers Specola/Assets.xcassets SpecolaTests
```

- [ ] **Step 3: Create minimal SpecolaApp.swift**

`Specola/SpecolaApp.swift`:

```swift
import SwiftUI

@main
struct SpecolaApp: App {
    var body: some Scene {
        MenuBarExtra("Specola", systemImage: "binoculars") {
            Text("Specola is running")
                .padding()
        }
        .menuBarExtraStyle(.window)
    }
}
```

- [ ] **Step 4: Create Info.plist**

`Specola/Info.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>LSUIElement</key>
    <true/>
    <key>CFBundleName</key>
    <string>Specola</string>
    <key>CFBundleDisplayName</key>
    <string>Specola</string>
    <key>CFBundleIdentifier</key>
    <string>com.oltrematica.specola</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
</dict>
</plist>
```

- [ ] **Step 5: Create minimal test file**

`SpecolaTests/SpecolaTests.swift`:

```swift
import XCTest
@testable import Specola

final class SpecolaTests: XCTestCase {
    func testPlaceholder() {
        XCTAssertTrue(true)
    }
}
```

- [ ] **Step 6: Generate Xcode project and build**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -5
```

Expected: `BUILD SUCCEEDED`

- [ ] **Step 7: Commit**

```bash
git add project.yml Specola/ SpecolaTests/ Specola.xcodeproj/
echo "*.xcuserdata" >> .gitignore
git add .gitignore
git commit -m "chore(swift): scaffold Xcode project with menubar app skeleton"
```

---

### Task 11: Models — SpecolaEntry and Settings

**Files:**
- Create: `Specola/Models/SpecolaEntry.swift`
- Create: `Specola/Models/Settings.swift`
- Create: `SpecolaTests/SpecolaEntryTests.swift`

- [ ] **Step 1: Write SpecolaEntry model**

`Specola/Models/SpecolaEntry.swift`:

```swift
import Foundation

struct SpecolaEntry: Codable, Identifiable, Equatable {
    let id: String            // "2026-04-05"
    let date: Date
    let path: String
    let feedCount: Int
    let itemCount: Int
    var read: Bool
}
```

- [ ] **Step 2: Write Settings wrapper**

`Specola/Models/Settings.swift`:

```swift
import Foundation

enum SpecolaSettings {
    private static let defaults = UserDefaults.standard

    private enum Key {
        static let scheduleHour = "scheduleHour"
        static let scheduleMinute = "scheduleMinute"
        static let autoGenerate = "autoGenerate"
        static let language = "language"
        static let hours = "hours"
        static let outputDir = "outputDir"
        static let claudePath = "claudePath"
        static let launchAtLogin = "launchAtLogin"
        static let hasCompletedSetup = "hasCompletedSetup"
    }

    static var scheduleHour: Int {
        get { defaults.object(forKey: Key.scheduleHour) as? Int ?? 7 }
        set { defaults.set(newValue, forKey: Key.scheduleHour) }
    }

    static var scheduleMinute: Int {
        get { defaults.object(forKey: Key.scheduleMinute) as? Int ?? 0 }
        set { defaults.set(newValue, forKey: Key.scheduleMinute) }
    }

    static var autoGenerate: Bool {
        get { defaults.object(forKey: Key.autoGenerate) as? Bool ?? true }
        set { defaults.set(newValue, forKey: Key.autoGenerate) }
    }

    static var language: String {
        get { defaults.string(forKey: Key.language) ?? "it" }
        set { defaults.set(newValue, forKey: Key.language) }
    }

    static var hours: Int {
        get {
            let val = defaults.integer(forKey: Key.hours)
            return val > 0 ? val : 24
        }
        set { defaults.set(newValue, forKey: Key.hours) }
    }

    static var outputDir: String {
        get {
            defaults.string(forKey: Key.outputDir)
                ?? NSString("~/Documents/Specola").expandingTildeInPath
        }
        set { defaults.set(newValue, forKey: Key.outputDir) }
    }

    static var claudePath: String {
        get { defaults.string(forKey: Key.claudePath) ?? "" }
        set { defaults.set(newValue, forKey: Key.claudePath) }
    }

    static var launchAtLogin: Bool {
        get { defaults.bool(forKey: Key.launchAtLogin) }
        set { defaults.set(newValue, forKey: Key.launchAtLogin) }
    }

    static var hasCompletedSetup: Bool {
        get { defaults.bool(forKey: Key.hasCompletedSetup) }
        set { defaults.set(newValue, forKey: Key.hasCompletedSetup) }
    }

    // MARK: - Directories

    static var supportDir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        let dir = base.appendingPathComponent("Specola")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    static var opmlPath: URL { supportDir.appendingPathComponent("Feeds.opml") }
    static var profilePath: URL { supportDir.appendingPathComponent("profile.md") }
    static var historyPath: URL { supportDir.appendingPathComponent("history.json") }
    static var engineDir: URL { supportDir.appendingPathComponent("engine") }
    static var pythonPath: URL { engineDir.appendingPathComponent(".venv/bin/python") }

    static var hasOPML: Bool {
        FileManager.default.fileExists(atPath: opmlPath.path)
    }
}
```

- [ ] **Step 3: Write tests for SpecolaEntry**

`SpecolaTests/SpecolaEntryTests.swift`:

```swift
import XCTest
@testable import Specola

final class SpecolaEntryTests: XCTestCase {
    func testEncodeDecode() throws {
        let entry = SpecolaEntry(
            id: "2026-04-05",
            date: ISO8601DateFormatter().date(from: "2026-04-05T07:00:00Z")!,
            path: "/Users/test/Documents/Specola/Specola_2026-04-05.docx",
            feedCount: 187,
            itemCount: 42,
            read: false
        )

        let data = try JSONEncoder().encode(entry)
        let decoded = try JSONDecoder().decode(SpecolaEntry.self, from: data)

        XCTAssertEqual(entry.id, decoded.id)
        XCTAssertEqual(entry.feedCount, decoded.feedCount)
        XCTAssertEqual(entry.itemCount, decoded.itemCount)
        XCTAssertEqual(entry.read, decoded.read)
        XCTAssertEqual(entry.path, decoded.path)
    }

    func testDecodesFromHistoryJSON() throws {
        let json = """
        {
            "id": "2026-04-05",
            "date": "2026-04-05T07:00:00Z",
            "path": "/Users/test/Specola_2026-04-05.docx",
            "feedCount": 187,
            "itemCount": 42,
            "read": false
        }
        """.data(using: .utf8)!

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let entry = try decoder.decode(SpecolaEntry.self, from: json)

        XCTAssertEqual(entry.id, "2026-04-05")
        XCTAssertEqual(entry.feedCount, 187)
        XCTAssertFalse(entry.read)
    }
}
```

- [ ] **Step 4: Build and run tests**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests -destination 'platform=macOS' test 2>&1 | tail -10
```

Expected: `Test Suite 'All tests' passed` (3 tests).

- [ ] **Step 5: Commit**

```bash
git add Specola/Models/ SpecolaTests/SpecolaEntryTests.swift
git commit -m "feat(swift): add SpecolaEntry model and Settings wrapper"
```

---

### Task 12: AppState

**Files:**
- Create: `Specola/Models/AppState.swift`
- Create: `SpecolaTests/AppStateTests.swift`

- [ ] **Step 1: Write AppState**

`Specola/Models/AppState.swift`:

```swift
import Foundation
import Observation

@Observable
final class AppState {
    var history: [SpecolaEntry] = []
    var isGenerating: Bool = false
    var lastError: String?

    private static let maxHistoryEntries = 30

    var unreadCount: Int {
        history.filter { !$0.read }.count
    }

    var lastGeneration: Date? {
        history.first?.date
    }

    var hasGeneratedToday: Bool {
        guard let last = history.first else { return false }
        return Calendar.current.isDateInToday(last.date)
    }

    var canGenerate: Bool {
        !isGenerating && SpecolaSettings.hasOPML
    }

    // MARK: - History Persistence

    func loadHistory() {
        let path = SpecolaSettings.historyPath
        guard FileManager.default.fileExists(atPath: path.path) else { return }

        do {
            let data = try Data(contentsOf: path)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            history = try decoder.decode([SpecolaEntry].self, from: data)
        } catch {
            history = []
        }
    }

    func saveHistory() {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

        do {
            let data = try encoder.encode(history)
            try data.write(to: SpecolaSettings.historyPath)
        } catch {
            // Silently fail — non-critical
        }
    }

    func addEntry(_ entry: SpecolaEntry) {
        history.insert(entry, at: 0)
        if history.count > Self.maxHistoryEntries {
            history = Array(history.prefix(Self.maxHistoryEntries))
        }
        saveHistory()
    }

    func markAsRead(_ entry: SpecolaEntry) {
        guard let index = history.firstIndex(where: { $0.id == entry.id }) else { return }
        history[index].read = true
        saveHistory()
    }

    // MARK: - Profile

    func loadProfile() -> String {
        let path = SpecolaSettings.profilePath
        return (try? String(contentsOf: path, encoding: .utf8)) ?? ""
    }

    func saveProfile(_ text: String) {
        try? text.write(to: SpecolaSettings.profilePath, atomically: true, encoding: .utf8)
    }
}
```

- [ ] **Step 2: Write tests for AppState**

`SpecolaTests/AppStateTests.swift`:

```swift
import XCTest
@testable import Specola

final class AppStateTests: XCTestCase {
    func testUnreadCount() {
        let state = AppState()
        state.history = [
            SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
            SpecolaEntry(id: "2", date: Date(), path: "", feedCount: 0, itemCount: 0, read: true),
            SpecolaEntry(id: "3", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
        ]
        XCTAssertEqual(state.unreadCount, 2)
    }

    func testMarkAsRead() {
        let state = AppState()
        let entry = SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]

        state.markAsRead(entry)

        XCTAssertTrue(state.history[0].read)
        XCTAssertEqual(state.unreadCount, 0)
    }

    func testAddEntryEnforcesMax() {
        let state = AppState()

        for i in 0..<35 {
            let entry = SpecolaEntry(
                id: "\(i)", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false
            )
            state.addEntry(entry)
        }

        XCTAssertEqual(state.history.count, 30)
    }

    func testHasGeneratedToday() {
        let state = AppState()

        XCTAssertFalse(state.hasGeneratedToday)

        let entry = SpecolaEntry(id: "today", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]

        XCTAssertTrue(state.hasGeneratedToday)
    }
}
```

- [ ] **Step 3: Build and run tests**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests -destination 'platform=macOS' test 2>&1 | tail -10
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add Specola/Models/AppState.swift SpecolaTests/AppStateTests.swift
git commit -m "feat(swift): add AppState with history management and unread tracking"
```

---

### Task 13: EngineService

**Files:**
- Create: `Specola/Services/EngineService.swift`
- Create: `SpecolaTests/EngineServiceTests.swift`

- [ ] **Step 1: Write EngineService**

`Specola/Services/EngineService.swift`:

```swift
import Foundation

struct EngineResult {
    let outputPath: String?
    let feedCount: Int
    let itemCount: Int
}

enum EngineError: LocalizedError {
    case engineNotFound
    case pythonNotFound
    case executionFailed(String)

    var errorDescription: String? {
        switch self {
        case .engineNotFound: return "Motore Python non trovato"
        case .pythonNotFound: return "Python venv non trovato"
        case .executionFailed(let msg): return msg
        }
    }
}

enum EngineService {
    static func run() async throws -> EngineResult {
        let pythonPath = SpecolaSettings.pythonPath
        let engineDir = SpecolaSettings.engineDir
        let enginePath = engineDir.appendingPathComponent("specola_engine.py")

        guard FileManager.default.fileExists(atPath: enginePath.path) else {
            throw EngineError.engineNotFound
        }
        guard FileManager.default.fileExists(atPath: pythonPath.path) else {
            throw EngineError.pythonNotFound
        }

        let process = Process()
        process.executableURL = pythonPath
        process.arguments = [
            enginePath.path, "run",
            "--opml", SpecolaSettings.opmlPath.path,
            "--profile", SpecolaSettings.profilePath.path,
            "--output-dir", SpecolaSettings.outputDir,
            "--hours", String(SpecolaSettings.hours),
            "--language", SpecolaSettings.language,
        ]
        process.currentDirectoryURL = engineDir

        let outputPipe = Pipe()
        let errorPipe = Pipe()
        process.standardOutput = outputPipe
        process.standardError = errorPipe

        try process.run()
        process.waitUntilExit()

        let outputData = outputPipe.fileHandleForReading.readDataToEndOfFile()
        let errorData = errorPipe.fileHandleForReading.readDataToEndOfFile()

        guard let outputString = String(data: outputData, encoding: .utf8),
              !outputString.isEmpty else {
            let errorString = String(data: errorData, encoding: .utf8) ?? "Unknown error"
            throw EngineError.executionFailed(errorString)
        }

        return try parseOutput(outputString)
    }

    static func parseOutput(_ json: String) throws -> EngineResult {
        guard let data = json.data(using: .utf8) else {
            throw EngineError.executionFailed("Invalid output encoding")
        }

        let parsed = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let parsed else {
            throw EngineError.executionFailed("Invalid JSON output")
        }

        guard let status = parsed["status"] as? String else {
            throw EngineError.executionFailed("Missing status in output")
        }

        if status == "error" {
            let message = parsed["message"] as? String ?? "Errore sconosciuto"
            throw EngineError.executionFailed(message)
        }

        return EngineResult(
            outputPath: parsed["output_path"] as? String,
            feedCount: parsed["feed_count"] as? Int ?? 0,
            itemCount: parsed["item_count"] as? Int ?? 0
        )
    }
}
```

- [ ] **Step 2: Write tests for JSON parsing**

`SpecolaTests/EngineServiceTests.swift`:

```swift
import XCTest
@testable import Specola

final class EngineServiceTests: XCTestCase {
    func testParseSuccessOutput() throws {
        let json = """
        {"status": "ok", "output_path": "/path/to/file.docx", "feed_count": 187, "item_count": 42}
        """
        let result = try EngineService.parseOutput(json)

        XCTAssertEqual(result.outputPath, "/path/to/file.docx")
        XCTAssertEqual(result.feedCount, 187)
        XCTAssertEqual(result.itemCount, 42)
    }

    func testParseErrorOutput() {
        let json = """
        {"status": "error", "message": "Claude CLI non trovata"}
        """
        XCTAssertThrowsError(try EngineService.parseOutput(json)) { error in
            XCTAssertTrue(error.localizedDescription.contains("Claude CLI"))
        }
    }

    func testParseInvalidJSON() {
        XCTAssertThrowsError(try EngineService.parseOutput("not json"))
    }

    func testParseEmptyJSON() {
        XCTAssertThrowsError(try EngineService.parseOutput("{}"))
    }
}
```

- [ ] **Step 3: Build and run tests**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests -destination 'platform=macOS' test 2>&1 | tail -10
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add Specola/Services/EngineService.swift SpecolaTests/EngineServiceTests.swift
git commit -m "feat(swift): add EngineService with Process launching and JSON parsing"
```

---

### Task 14: SchedulerService

**Files:**
- Create: `Specola/Services/SchedulerService.swift`
- Create: `SpecolaTests/SchedulerServiceTests.swift`

- [ ] **Step 1: Write SchedulerService**

`Specola/Services/SchedulerService.swift`:

```swift
import Foundation
import AppKit

final class SchedulerService {
    private var timer: Timer?
    private var onTrigger: (() -> Void)?

    func start(onTrigger: @escaping () -> Void) {
        self.onTrigger = onTrigger

        // Check every 60 seconds
        timer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            self?.checkAndTrigger()
        }

        // Wake-from-sleep detection
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(handleWake),
            name: NSWorkspace.didWakeNotification,
            object: nil
        )
    }

    func stop() {
        timer?.invalidate()
        timer = nil
        NSWorkspace.shared.notificationCenter.removeObserver(self)
    }

    @objc private func handleWake() {
        // Short delay to let the system settle after wake
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in
            self?.checkAndTrigger()
        }
    }

    private func checkAndTrigger() {
        if Self.shouldGenerate() {
            onTrigger?()
        }
    }

    /// Determines whether a generation should be triggered right now.
    /// Public and static for testability.
    static func shouldGenerate(
        autoGenerate: Bool? = nil,
        scheduleHour: Int? = nil,
        scheduleMinute: Int? = nil,
        hasGeneratedToday: Bool? = nil,
        now: Date = Date()
    ) -> Bool {
        let auto = autoGenerate ?? SpecolaSettings.autoGenerate
        guard auto else { return false }

        let hour = scheduleHour ?? SpecolaSettings.scheduleHour
        let minute = scheduleMinute ?? SpecolaSettings.scheduleMinute

        let calendar = Calendar.current
        let components = calendar.dateComponents([.hour, .minute], from: now)
        let currentHour = components.hour ?? 0
        let currentMinute = components.minute ?? 0

        // Current time must be at or past the scheduled time
        let isPastSchedule = currentHour > hour || (currentHour == hour && currentMinute >= minute)
        guard isPastSchedule else { return false }

        // Must not have already generated today
        let generated = hasGeneratedToday ?? false
        return !generated
    }
}
```

- [ ] **Step 2: Write tests**

`SpecolaTests/SchedulerServiceTests.swift`:

```swift
import XCTest
@testable import Specola

final class SchedulerServiceTests: XCTestCase {
    func testShouldNotGenerateBeforeScheduledTime() {
        // Schedule at 07:00, current time is 06:30
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true,
            scheduleHour: 7,
            scheduleMinute: 0,
            hasGeneratedToday: false,
            now: dateAt(hour: 6, minute: 30)
        )
        XCTAssertFalse(result)
    }

    func testShouldGenerateAtScheduledTime() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true,
            scheduleHour: 7,
            scheduleMinute: 0,
            hasGeneratedToday: false,
            now: dateAt(hour: 7, minute: 0)
        )
        XCTAssertTrue(result)
    }

    func testShouldGenerateAfterScheduledTime() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true,
            scheduleHour: 7,
            scheduleMinute: 0,
            hasGeneratedToday: false,
            now: dateAt(hour: 10, minute: 30)
        )
        XCTAssertTrue(result)
    }

    func testShouldNotGenerateIfAlreadyDone() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true,
            scheduleHour: 7,
            scheduleMinute: 0,
            hasGeneratedToday: true,
            now: dateAt(hour: 10, minute: 0)
        )
        XCTAssertFalse(result)
    }

    func testShouldNotGenerateIfAutoOff() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: false,
            scheduleHour: 7,
            scheduleMinute: 0,
            hasGeneratedToday: false,
            now: dateAt(hour: 10, minute: 0)
        )
        XCTAssertFalse(result)
    }

    // MARK: - Helper

    private func dateAt(hour: Int, minute: Int) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        components.hour = hour
        components.minute = minute
        components.second = 0
        return Calendar.current.date(from: components)!
    }
}
```

- [ ] **Step 3: Build and run tests**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests -destination 'platform=macOS' test 2>&1 | tail -10
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add Specola/Services/SchedulerService.swift SpecolaTests/SchedulerServiceTests.swift
git commit -m "feat(swift): add SchedulerService with timer, wake detection, and scheduling logic"
```

---

### Task 15: NotificationService

**Files:**
- Create: `Specola/Services/NotificationService.swift`

- [ ] **Step 1: Implement NotificationService**

`Specola/Services/NotificationService.swift`:

```swift
import Foundation
import UserNotifications

enum NotificationService {
    static func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
    }

    static func notifySuccess(date: String, itemCount: Int, docxPath: String) {
        let content = UNMutableNotificationContent()
        content.title = "Specola del \(date) pronta"
        content.body = "\(itemCount) articoli analizzati"
        content.sound = .default
        content.userInfo = ["docxPath": docxPath]

        let request = UNNotificationRequest(
            identifier: "specola-\(date)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    static func notifyError(message: String) {
        let content = UNMutableNotificationContent()
        content.title = "Specola: generazione fallita"
        content.body = message
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "specola-error-\(Date().timeIntervalSince1970)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
```

- [ ] **Step 2: Build to verify**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -5
```

Expected: `BUILD SUCCEEDED`

- [ ] **Step 3: Commit**

```bash
git add Specola/Services/NotificationService.swift
git commit -m "feat(swift): add NotificationService for completion and error notifications"
```

---

### Task 16: MenuBarIcon Helper

**Files:**
- Create: `Specola/Helpers/MenuBarIcon.swift`

- [ ] **Step 1: Implement menubar icon with badge rendering**

`Specola/Helpers/MenuBarIcon.swift`:

```swift
import AppKit

enum MenuBarIcon {
    /// Renders the binoculars SF Symbol with an optional numeric badge overlay.
    static func image(badgeCount: Int) -> NSImage {
        let config = NSImage.SymbolConfiguration(pointSize: 16, weight: .regular)
        guard let baseImage = NSImage(systemSymbolName: "binoculars", accessibilityDescription: "Specola")?
            .withSymbolConfiguration(config) else {
            return NSImage()
        }

        if badgeCount <= 0 {
            baseImage.isTemplate = true
            return baseImage
        }

        let canvasSize = NSSize(width: 24, height: 18)
        let image = NSImage(size: canvasSize, flipped: false) { rect in
            // Draw base icon
            baseImage.draw(
                in: NSRect(x: 0, y: 0, width: 18, height: 18),
                from: .zero,
                operation: .sourceOver,
                fraction: 1.0
            )

            // Draw badge circle
            let badgeSize: CGFloat = 10
            let badgeRect = NSRect(
                x: rect.width - badgeSize,
                y: rect.height - badgeSize,
                width: badgeSize,
                height: badgeSize
            )
            NSColor.systemRed.setFill()
            NSBezierPath(ovalIn: badgeRect).fill()

            // Draw number
            let text = badgeCount > 9 ? "+" : "\(badgeCount)"
            let attrs: [NSAttributedString.Key: Any] = [
                .font: NSFont.systemFont(ofSize: 7, weight: .bold),
                .foregroundColor: NSColor.white,
            ]
            let textSize = (text as NSString).size(withAttributes: attrs)
            let textPoint = NSPoint(
                x: badgeRect.midX - textSize.width / 2,
                y: badgeRect.midY - textSize.height / 2
            )
            (text as NSString).draw(at: textPoint, withAttributes: attrs)

            return true
        }

        // Badge has color, so not a template image
        image.isTemplate = false
        return image
    }
}
```

- [ ] **Step 2: Build to verify**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -5
```

Expected: `BUILD SUCCEEDED`

- [ ] **Step 3: Commit**

```bash
git add Specola/Helpers/MenuBarIcon.swift
git commit -m "feat(swift): add MenuBarIcon helper with badge rendering"
```

---

### Task 17: MenuBarView (Popover)

**Files:**
- Create: `Specola/MenuBarView.swift`

- [ ] **Step 1: Implement the popover content**

`Specola/MenuBarView.swift`:

```swift
import SwiftUI

struct MenuBarView: View {
    @Environment(AppState.self) private var appState
    @State private var showSettings = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // MARK: Header
            VStack(alignment: .leading, spacing: 2) {
                Text("Specola")
                    .font(.headline)
                    .fontWeight(.bold)

                if let lastDate = appState.lastGeneration {
                    Text("Ultima generazione: \(lastDate.formatted(date: .long, time: .shortened))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    Text("Nessuna Specola generata")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            .padding(.bottom, 8)

            Divider()

            // MARK: List
            if appState.history.isEmpty {
                Text("Nessuna Specola disponibile")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 24)
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 0) {
                        ForEach(appState.history.prefix(10)) { entry in
                            SpecolaRow(entry: entry)
                                .onTapGesture { openSpecola(entry) }
                        }
                    }
                }
                .frame(maxHeight: 300)
            }

            Divider()

            // MARK: Actions
            VStack(spacing: 8) {
                if appState.isGenerating {
                    HStack {
                        ProgressView()
                            .controlSize(.small)
                        Text("Generazione in corso...")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 4)
                } else {
                    Button("Genera ora") {
                        generateNow()
                    }
                    .disabled(!appState.canGenerate)
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)

            Divider()

            // MARK: Footer
            HStack {
                Button("Impostazioni...") {
                    openSettings()
                }
                .buttonStyle(.plain)
                .foregroundStyle(.primary)

                Spacer()

                Button("Esci") {
                    NSApplication.shared.terminate(nil)
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
            }
            .font(.subheadline)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
        .frame(width: 320)
    }

    private func openSpecola(_ entry: SpecolaEntry) {
        let url = URL(fileURLWithPath: entry.path)
        NSWorkspace.shared.open(url)
        appState.markAsRead(entry)
    }

    private func generateNow() {
        appState.isGenerating = true
        appState.lastError = nil

        Task {
            do {
                let result = try await EngineService.run()
                let entry = SpecolaEntry(
                    id: dateId(),
                    date: Date(),
                    path: result.outputPath ?? "",
                    feedCount: result.feedCount,
                    itemCount: result.itemCount,
                    read: false
                )
                await MainActor.run {
                    appState.addEntry(entry)
                    appState.isGenerating = false
                }
                if let path = result.outputPath {
                    NotificationService.notifySuccess(
                        date: dateId(),
                        itemCount: result.itemCount,
                        docxPath: path
                    )
                }
            } catch {
                await MainActor.run {
                    appState.isGenerating = false
                    appState.lastError = error.localizedDescription
                }
                NotificationService.notifyError(message: error.localizedDescription)
            }
        }
    }

    private func openSettings() {
        NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
    }

    private func dateId() -> String {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        return fmt.string(from: Date())
    }
}

// MARK: - Row

private struct SpecolaRow: View {
    let entry: SpecolaEntry

    var body: some View {
        HStack(spacing: 10) {
            // Unread indicator
            Circle()
                .fill(entry.read ? Color.clear : Color.accentColor)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(entry.date.formatted(date: .long, time: .omitted))
                    .font(.subheadline)
                    .fontWeight(entry.read ? .regular : .semibold)

                Text("\(entry.feedCount) fonti · \(entry.itemCount) articoli")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .contentShape(Rectangle())
        .background(Color.primary.opacity(0.001)) // hit target
    }
}
```

- [ ] **Step 2: Build to verify**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -5
```

Expected: `BUILD SUCCEEDED`

- [ ] **Step 3: Commit**

```bash
git add Specola/MenuBarView.swift
git commit -m "feat(swift): add MenuBarView popover with history list and generation controls"
```

---

### Task 18: SettingsView

**Files:**
- Create: `Specola/SettingsView.swift`

- [ ] **Step 1: Implement SettingsView with TabView**

`Specola/SettingsView.swift`:

```swift
import SwiftUI
import ServiceManagement
import UniformTypeIdentifiers

struct SettingsView: View {
    var body: some View {
        TabView {
            SourcesTab()
                .tabItem { Label("Fonti", systemImage: "doc.text") }

            ScheduleTab()
                .tabItem { Label("Pianificazione", systemImage: "clock") }

            ProfileTab()
                .tabItem { Label("Profilo", systemImage: "person") }

            AdvancedTab()
                .tabItem { Label("Avanzate", systemImage: "gearshape.2") }
        }
        .frame(width: 520, height: 420)
    }
}

// MARK: - Sources Tab

private struct SourcesTab: View {
    @State private var opmlInfo: String = ""
    @State private var opmlConfigured: Bool = SpecolaSettings.hasOPML

    var body: some View {
        Form {
            Section {
                if opmlConfigured {
                    LabeledContent("File OPML") {
                        Text(SpecolaSettings.opmlPath.lastPathComponent)
                            .foregroundStyle(.secondary)
                    }
                    if !opmlInfo.isEmpty {
                        Text(opmlInfo)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } else {
                    Text("Nessun file OPML configurato")
                        .foregroundStyle(.secondary)
                }

                HStack {
                    Button("Scegli file OPML...") { chooseOPML() }
                    if opmlConfigured {
                        Button("Rimuovi", role: .destructive) { removeOPML() }
                    }
                }
            }
        }
        .formStyle(.grouped)
        .onAppear { refreshOPMLInfo() }
    }

    private func chooseOPML() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [
            UTType(filenameExtension: "opml") ?? .xml,
            .xml,
        ]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false

        guard panel.runModal() == .OK, let url = panel.url else { return }

        // Copy to support directory
        let dest = SpecolaSettings.opmlPath
        try? FileManager.default.removeItem(at: dest)
        try? FileManager.default.copyItem(at: url, to: dest)

        opmlConfigured = true
        refreshOPMLInfo()
    }

    private func removeOPML() {
        try? FileManager.default.removeItem(at: SpecolaSettings.opmlPath)
        opmlConfigured = false
        opmlInfo = ""
    }

    private func refreshOPMLInfo() {
        guard SpecolaSettings.hasOPML else {
            opmlInfo = ""
            return
        }
        do {
            let data = try Data(contentsOf: SpecolaSettings.opmlPath)
            let xml = try XMLDocument(data: data)
            let categories = try xml.nodes(forXPath: "/opml/body/outline")
            let feeds = try xml.nodes(forXPath: "//outline[@type='rss']")
            opmlInfo = "\(categories.count) categorie, \(feeds.count) feed"
        } catch {
            opmlInfo = "Errore nella lettura del file OPML"
        }
    }
}

// MARK: - Schedule Tab

private struct ScheduleTab: View {
    @State private var scheduleDate = scheduleDateFromSettings()
    @State private var autoGenerate = SpecolaSettings.autoGenerate
    @State private var launchAtLogin = SpecolaSettings.launchAtLogin

    var body: some View {
        Form {
            Section {
                DatePicker("Orario generazione", selection: $scheduleDate, displayedComponents: .hourAndMinute)
                    .onChange(of: scheduleDate) { _, newValue in
                        let comps = Calendar.current.dateComponents([.hour, .minute], from: newValue)
                        SpecolaSettings.scheduleHour = comps.hour ?? 7
                        SpecolaSettings.scheduleMinute = comps.minute ?? 0
                    }

                Toggle("Genera automaticamente", isOn: $autoGenerate)
                    .onChange(of: autoGenerate) { _, val in SpecolaSettings.autoGenerate = val }

                Text("Se il Mac è in stop all'orario previsto, la Specola verrà generata al risveglio.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Section {
                Toggle("Avvia Specola al login", isOn: $launchAtLogin)
                    .onChange(of: launchAtLogin) { _, val in
                        SpecolaSettings.launchAtLogin = val
                        if val {
                            try? SMAppService.mainApp.register()
                        } else {
                            try? SMAppService.mainApp.unregister()
                        }
                    }
            }
        }
        .formStyle(.grouped)
    }

    private static func scheduleDateFromSettings() -> Date {
        var comps = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        comps.hour = SpecolaSettings.scheduleHour
        comps.minute = SpecolaSettings.scheduleMinute
        return Calendar.current.date(from: comps) ?? Date()
    }
}

// MARK: - Profile Tab

private struct ProfileTab: View {
    @State private var profileText: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Descrivi il tuo ruolo professionale, il tuo stack, i tuoi interessi e progetti. Specola usa questo profilo per personalizzare l'analisi delle notizie.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 16)
                .padding(.top, 12)

            TextEditor(text: $profileText)
                .font(.body)
                .frame(minHeight: 200)
                .padding(4)
                .overlay(
                    Group {
                        if profileText.isEmpty {
                            Text("Es: Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS. Mi interessa: regolamentazione EU, sicurezza API, trend VC europeo...")
                                .foregroundStyle(.tertiary)
                                .padding(8)
                                .allowsHitTesting(false)
                        }
                    },
                    alignment: .topLeading
                )
                .padding(.horizontal, 16)

            Spacer()
        }
        .onAppear {
            profileText = (try? String(contentsOf: SpecolaSettings.profilePath, encoding: .utf8)) ?? ""
        }
        .onDisappear {
            saveProfile()
        }
        .onChange(of: profileText) { _, _ in
            // Debounced save would be ideal; for now, save on disappear
        }
    }

    private func saveProfile() {
        guard !profileText.isEmpty else { return }
        try? profileText.write(to: SpecolaSettings.profilePath, atomically: true, encoding: .utf8)
    }
}

// MARK: - Advanced Tab

private struct AdvancedTab: View {
    @State private var outputDir = SpecolaSettings.outputDir
    @State private var language = SpecolaSettings.language
    @State private var hours = SpecolaSettings.hours
    @State private var claudePath = SpecolaSettings.claudePath

    var body: some View {
        Form {
            Section("Output") {
                LabeledContent("Directory DOCX") {
                    HStack {
                        Text(outputDir)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .foregroundStyle(.secondary)
                        Button("Apri cartella") {
                            let url = URL(fileURLWithPath: outputDir)
                            try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
                            NSWorkspace.shared.open(url)
                        }
                    }
                }
            }

            Section("Briefing") {
                Picker("Lingua", selection: $language) {
                    Text("Italiano").tag("it")
                    Text("English").tag("en")
                }
                .pickerStyle(.segmented)
                .onChange(of: language) { _, val in SpecolaSettings.language = val }

                Stepper("Ultime \(hours) ore", value: $hours, in: 6...72)
                    .onChange(of: hours) { _, val in SpecolaSettings.hours = val }
            }

            Section("Claude Code CLI") {
                TextField("Path (auto-detected se vuoto)", text: $claudePath)
                    .onChange(of: claudePath) { _, val in SpecolaSettings.claudePath = val }

                Text("Posizioni controllate: /usr/local/bin/claude, ~/.local/bin/claude, ~/.claude/local/claude")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .formStyle(.grouped)
    }
}
```

- [ ] **Step 2: Build to verify**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -5
```

Expected: `BUILD SUCCEEDED`

- [ ] **Step 3: Commit**

```bash
git add Specola/SettingsView.swift
git commit -m "feat(swift): add SettingsView with TabView (Fonti, Pianificazione, Profilo, Avanzate)"
```

---

### Task 19: SpecolaApp — Main Entry, Wiring, First Launch

**Files:**
- Modify: `Specola/SpecolaApp.swift`

- [ ] **Step 1: Rewrite SpecolaApp with full wiring**

Replace the contents of `Specola/SpecolaApp.swift`:

```swift
import SwiftUI

@main
struct SpecolaApp: App {
    @State private var appState = AppState()
    private let scheduler = SchedulerService()

    var body: some Scene {
        MenuBarExtra {
            MenuBarView()
                .environment(appState)
        } label: {
            Image(nsImage: MenuBarIcon.image(badgeCount: appState.unreadCount))
        }
        .menuBarExtraStyle(.window)

        Settings {
            SettingsView()
                .environment(appState)
        }
    }

    init() {
        // Request notification permission
        NotificationService.requestPermission()

        // Load history
        appState.loadHistory()

        // Setup engine on first launch
        Task {
            await setupEngineIfNeeded()
        }

        // Start scheduler
        scheduler.start { [appState] in
            guard !appState.isGenerating, !appState.hasGeneratedToday else { return }
            triggerGeneration(appState: appState)
        }

        // Show settings on first launch
        if !SpecolaSettings.hasCompletedSetup {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
                SpecolaSettings.hasCompletedSetup = true
            }
        }
    }
}

// MARK: - Engine Setup

private func setupEngineIfNeeded() async {
    let engineDir = SpecolaSettings.engineDir
    let venvPath = engineDir.appendingPathComponent(".venv/bin/python")

    // If venv already exists, we're good
    guard !FileManager.default.fileExists(atPath: venvPath.path) else { return }

    // Find bundled engine in app bundle
    guard let bundledEngine = Bundle.main.resourceURL?.appendingPathComponent("engine") else { return }
    guard FileManager.default.fileExists(atPath: bundledEngine.path) else { return }

    // Copy to support directory
    try? FileManager.default.removeItem(at: engineDir)
    try? FileManager.default.copyItem(at: bundledEngine, to: engineDir)

    // Run setup_engine.sh
    let setupScript = engineDir.appendingPathComponent("setup_engine.sh")
    guard FileManager.default.fileExists(atPath: setupScript.path) else { return }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/bin/bash")
    process.arguments = [setupScript.path]
    process.currentDirectoryURL = engineDir

    try? process.run()
    process.waitUntilExit()
}

// MARK: - Generation

private func triggerGeneration(appState: AppState) {
    guard appState.canGenerate else { return }

    appState.isGenerating = true
    appState.lastError = nil

    Task {
        do {
            let result = try await EngineService.run()
            let dateId = {
                let fmt = DateFormatter()
                fmt.dateFormat = "yyyy-MM-dd"
                return fmt.string(from: Date())
            }()

            let entry = SpecolaEntry(
                id: dateId,
                date: Date(),
                path: result.outputPath ?? "",
                feedCount: result.feedCount,
                itemCount: result.itemCount,
                read: false
            )

            await MainActor.run {
                appState.addEntry(entry)
                appState.isGenerating = false
            }

            if let path = result.outputPath {
                NotificationService.notifySuccess(
                    date: dateId,
                    itemCount: result.itemCount,
                    docxPath: path
                )
            }
        } catch {
            await MainActor.run {
                appState.isGenerating = false
                appState.lastError = error.localizedDescription
            }
            NotificationService.notifyError(message: error.localizedDescription)
        }
    }
}
```

- [ ] **Step 2: Remove duplicate SpecolaTests placeholder**

Delete the placeholder test in `SpecolaTests/SpecolaTests.swift` — the real tests are in the individual test files.

```bash
rm SpecolaTests/SpecolaTests.swift
```

- [ ] **Step 3: Build the complete app**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -10
```

Expected: `BUILD SUCCEEDED`

- [ ] **Step 4: Run all tests**

```bash
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests -destination 'platform=macOS' test 2>&1 | tail -15
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add Specola/SpecolaApp.swift
git rm SpecolaTests/SpecolaTests.swift 2>/dev/null; true
git add SpecolaTests/
git commit -m "feat(swift): wire SpecolaApp with MenuBarExtra, scheduling, first launch, and engine setup"
```

---

### Task 20: Final Integration Verification

- [ ] **Step 1: Run all Python tests**

```bash
cd engine && .venv/bin/python -m pytest tests/ -v
```

Expected: all ~38 tests PASS.

- [ ] **Step 2: Run all Swift tests**

```bash
xcodegen generate
xcodebuild -project Specola.xcodeproj -scheme SpecolaTests -destination 'platform=macOS' test 2>&1 | tail -15
```

Expected: all tests PASS.

- [ ] **Step 3: Test Python engine dry-run with a real OPML file**

Create a test profile and run the engine in dry-run mode:

```bash
echo "Sono un developer che lavora con Python e Swift." > /tmp/test_profile.md
cd engine && .venv/bin/python specola_engine.py run \
    --opml tests/fixtures/sample.opml \
    --profile /tmp/test_profile.md \
    --output-dir /tmp/specola_test \
    --dry-run \
    --verbose
```

Expected: JSON output with `"status": "ok"` and feed/item counts.

- [ ] **Step 4: Build and launch the app**

```bash
xcodebuild -project Specola.xcodeproj -scheme Specola -destination 'platform=macOS' build 2>&1 | tail -5
```

Launch manually from Xcode or:
```bash
open build/Build/Products/Debug/Specola.app
```

Verify:
- Binoculars icon appears in menubar
- Click opens popover with "Nessuna Specola disponibile"
- Settings window opens on first launch
- All 4 tabs are present and functional

- [ ] **Step 5: Final commit**

```bash
git add -A
git status
git commit -m "chore: final integration verification — all tests passing"
```
