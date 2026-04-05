from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.feed_fetcher import (
    _fetch_single_feed,
    fetch_feeds,
    format_digest,
    parse_item_date,
    parse_opml,
    strip_html,
)


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
        assert "Tech" in result
        assert "01 – Tech" not in result
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
        opml.write_text('<?xml version="1.0"?><opml version="2.0"><head/><body/></opml>')
        result = parse_opml(opml)
        assert result == {}


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entry(title="Test title", link="https://example.com", summary="Summary text",
                published_parsed=None, published=None):
    """Build a minimal feedparser-like entry object."""
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.description = None
    entry.content = []
    entry.published_parsed = published_parsed
    entry.updated_parsed = None
    entry.published = published or ""
    entry.updated = ""
    return entry


def _make_parsed_feed(entries):
    """Return a mock feedparser result with the given entries."""
    fp = MagicMock()
    fp.entries = entries
    return fp


# ---------------------------------------------------------------------------
# TestFetchFeeds
# ---------------------------------------------------------------------------

class TestFetchFeeds:
    """Tests for _fetch_single_feed and fetch_feeds."""

    def test_fetches_and_filters_by_time(self):
        """Recent items are included; items older than the window are excluded."""
        now = datetime.now(tz=timezone.utc)
        recent_parsed = now - timedelta(hours=1)
        old_parsed = now - timedelta(hours=48)

        # feedparser uses time.struct_time-like tuples via published_parsed
        def dt_to_struct(dt):
            return dt.timetuple()[:9]

        recent_entry = _make_entry(title="Recent", published_parsed=dt_to_struct(recent_parsed))
        old_entry = _make_entry(title="Old", published_parsed=dt_to_struct(old_parsed))

        mock_feed = _make_parsed_feed([recent_entry, old_entry])
        feed_info = {"title": "Test Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            category, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert category == "Tech"
        titles = [i["title"] for i in items]
        assert "Recent" in titles
        assert "Old" not in titles

    def test_includes_items_with_no_date(self):
        """Items where date cannot be parsed are always included."""
        no_date_entry = _make_entry(title="No Date", published_parsed=None, published="")
        mock_feed = _make_parsed_feed([no_date_entry])
        feed_info = {"title": "Test Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            category, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert len(items) == 1
        assert items[0]["title"] == "No Date"
        assert items[0]["published"] == "data n/d"

    def test_respects_max_items(self):
        """fetch_feeds enforces max_items per category."""
        now = datetime.now(tz=timezone.utc)

        def dt_to_struct(dt):
            return dt.timetuple()[:9]

        entries = [
            _make_entry(title=f"Item {i}", published_parsed=dt_to_struct(now - timedelta(minutes=i)))
            for i in range(10)
        ]
        mock_feed = _make_parsed_feed(entries)
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            category, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=3)

        assert len(items) == 3

    def test_strips_html_from_summary(self):
        """HTML tags are removed from the summary field."""
        entry = _make_entry(summary="<p>Hello <b>world</b></p>")
        entry.published_parsed = datetime.now(tz=timezone.utc).timetuple()[:9]
        mock_feed = _make_parsed_feed([entry])
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["summary"] == "Hello world"

    def test_handles_feed_failure_gracefully(self):
        """An exception during fetch does not crash; returns empty list."""
        feed_info = {"title": "Broken Feed", "xmlUrl": "https://broken.example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", side_effect=Exception("network error")):
            category, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert category == "Tech"
        assert items == []


# ---------------------------------------------------------------------------
# TestFormatDigest
# ---------------------------------------------------------------------------

class TestFormatDigest:
    """Tests for format_digest."""

    def test_produces_markdown_with_categories(self, sample_items_by_category):
        result = format_digest(sample_items_by_category, "2026-04-05")
        assert result.startswith("# Feed Digest — 2026-04-05")
        assert "\n## Tech\n" in result
        assert "\n## Business\n" in result

    def test_includes_item_details(self, sample_items_by_category):
        result = format_digest(sample_items_by_category, "2026-04-05")
        assert "OpenAI releases GPT-5" in result
        assert "TechCrunch" in result
        assert "https://example.com/gpt5" in result
        assert "OpenAI has announced GPT-5" in result

    def test_empty_categories(self):
        result = format_digest({}, "2026-04-05")
        assert result == "Nessun articolo trovato nel periodo selezionato."

    def test_returns_category_count(self, sample_items_by_category):
        result = format_digest(sample_items_by_category, "2026-04-05")
        count = result.count("\n## ")
        # sample_items_by_category has Tech and Business (2 categories with items)
        assert count == 2
