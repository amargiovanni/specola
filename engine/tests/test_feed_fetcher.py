from datetime import datetime, timezone

import pytest

from src.feed_fetcher import parse_opml, strip_html, parse_item_date


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
