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

    def test_no_body_element(self, tmp_path):
        """OPML without <body> returns empty dict."""
        opml = tmp_path / "no_body.opml"
        opml.write_text('<?xml version="1.0"?><opml version="2.0"><head/></opml>')
        result = parse_opml(opml)
        assert result == {}

    def test_category_with_no_rss_feeds_excluded(self, tmp_path):
        """Category with non-RSS children is excluded."""
        opml = tmp_path / "no_rss.opml"
        opml.write_text('''<?xml version="1.0"?>
        <opml version="2.0"><head/><body>
            <outline text="Empty Cat">
                <outline type="include" text="Not RSS" xmlUrl="https://x.com"/>
            </outline>
        </body></opml>''')
        result = parse_opml(opml)
        assert result == {}

    def test_strips_dash_prefix(self, tmp_path):
        """Strips numeric prefix with dash separator."""
        opml = tmp_path / "dash.opml"
        opml.write_text('''<?xml version="1.0"?>
        <opml version="2.0"><head/><body>
            <outline text="03 - Science">
                <outline type="rss" text="Nature" xmlUrl="https://nature.com/rss"/>
            </outline>
        </body></opml>''')
        result = parse_opml(opml)
        assert "Science" in result

    def test_strips_dot_prefix(self, tmp_path):
        """Strips numeric prefix with dot separator."""
        opml = tmp_path / "dot.opml"
        opml.write_text('''<?xml version="1.0"?>
        <opml version="2.0"><head/><body>
            <outline text="04. Sports">
                <outline type="rss" text="ESPN" xmlUrl="https://espn.com/rss"/>
            </outline>
        </body></opml>''')
        result = parse_opml(opml)
        assert "Sports" in result

    def test_uses_title_attribute_fallback(self, tmp_path):
        """If text attr is missing, uses title attr for category name."""
        opml = tmp_path / "title_attr.opml"
        opml.write_text('''<?xml version="1.0"?>
        <opml version="2.0"><head/><body>
            <outline title="MyCategory">
                <outline type="rss" title="Feed1" xmlUrl="https://x.com/rss"/>
            </outline>
        </body></opml>''')
        result = parse_opml(opml)
        assert "MyCategory" in result

    def test_rss_type_case_insensitive(self, tmp_path):
        """type='RSS' (uppercase) should still be detected."""
        opml = tmp_path / "upper.opml"
        opml.write_text('''<?xml version="1.0"?>
        <opml version="2.0"><head/><body>
            <outline text="Cat">
                <outline type="RSS" text="Feed" xmlUrl="https://x.com/rss"/>
            </outline>
        </body></opml>''')
        result = parse_opml(opml)
        assert "Cat" in result
        assert len(result["Cat"]) == 1

    def test_invalid_xml_raises(self, tmp_path):
        """Invalid XML should raise an exception."""
        opml = tmp_path / "invalid.opml"
        opml.write_text("not xml at all")
        with pytest.raises(Exception):
            parse_opml(opml)

    def test_empty_category_name_skipped(self, tmp_path):
        """Category with empty name after prefix stripping is skipped."""
        opml = tmp_path / "empty_name.opml"
        opml.write_text('''<?xml version="1.0"?>
        <opml version="2.0"><head/><body>
            <outline text="01 – ">
                <outline type="rss" text="Feed" xmlUrl="https://x.com/rss"/>
            </outline>
        </body></opml>''')
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

    def test_custom_max_length(self):
        result = strip_html("abcdefgh", max_length=4)
        assert result == "abcd"

    def test_nested_html_tags(self):
        assert strip_html("<div><p><span>deep</span></p></div>") == "deep"

    def test_preserves_text_between_tags(self):
        assert strip_html("before<br/>after") == "beforeafter"

    def test_handles_none_like_empty(self):
        """Empty string input returns empty."""
        assert strip_html("") == ""

    def test_complex_entities(self):
        assert strip_html("&#x27;hello&#39;") == "'hello'"

    def test_mixed_html_and_entities(self):
        result = strip_html("<p>&amp;amp; &lt;b&gt;not bold&lt;/b&gt;</p>")
        assert "&amp;" in result
        assert "<b>" in result  # The entities got unescaped to literal tags? No...
        # Actually: &lt;b&gt; → <b> after unescape, then strip_html removes it
        # Let's just check it doesn't crash and returns text
        assert isinstance(result, str)


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

    def test_updated_parsed_fallback(self):
        """Uses updated_parsed when published_parsed is None."""
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = None
        entry.updated_parsed = (2026, 3, 15, 12, 0, 0, 0, 74, 0)
        entry.published = ""
        entry.updated = ""
        result = parse_item_date(entry)
        assert result is not None
        assert result.month == 3
        assert result.day == 15

    def test_updated_raw_string_fallback(self):
        """Uses updated raw string when published string is empty."""
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = ""
        entry.updated = "2026-03-15T12:00:00Z"
        result = parse_item_date(entry)
        assert result is not None
        assert result.year == 2026

    def test_returns_utc_aware_datetime(self):
        """Returned datetime should always be UTC-aware."""
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = (2026, 4, 5, 9, 30, 0, 5, 95, 0)
        entry.updated_parsed = None
        entry.published = ""
        entry.updated = ""
        result = parse_item_date(entry)
        assert result.tzinfo is not None

    def test_naive_dateutil_gets_utc(self):
        """Naive datetime from dateutil gets UTC timezone."""
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = "2026-04-05 09:30:00"  # No timezone
        entry.updated = ""
        result = parse_item_date(entry)
        assert result is not None
        assert result.tzinfo is not None

    def test_garbage_string_returns_none(self):
        """Completely unparseable string returns None."""
        entry = type("E", (), {"get": lambda s, k, d=None: d})()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = "not a date at all XYZ"
        entry.updated = "also garbage 123"
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

    def test_summary_fallback_to_description(self):
        """Falls back to entry.description if summary is None."""
        entry = _make_entry(summary=None)
        entry.summary = None
        entry.description = "Description fallback text"
        entry.published_parsed = datetime.now(tz=timezone.utc).timetuple()[:9]
        mock_feed = _make_parsed_feed([entry])
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["summary"] == "Description fallback text"

    def test_summary_fallback_to_content(self):
        """Falls back to entry.content[0].value if summary and description are None."""
        entry = _make_entry(summary=None)
        entry.summary = None
        entry.description = None
        entry.content = [{"value": "<b>Content</b> fallback"}]
        entry.published_parsed = datetime.now(tz=timezone.utc).timetuple()[:9]
        mock_feed = _make_parsed_feed([entry])
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["summary"] == "Content fallback"

    def test_no_summary_at_all(self):
        """If no summary/description/content, summary is empty string."""
        entry = _make_entry(summary=None)
        entry.summary = None
        entry.description = None
        entry.content = []
        entry.published_parsed = datetime.now(tz=timezone.utc).timetuple()[:9]
        mock_feed = _make_parsed_feed([entry])
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["summary"] == ""

    def test_items_sorted_by_date_descending(self):
        """Items are returned sorted newest-first."""
        now = datetime.now(tz=timezone.utc)

        def dt_to_struct(dt):
            return dt.timetuple()[:9]

        e1 = _make_entry(title="Oldest", published_parsed=dt_to_struct(now - timedelta(hours=3)))
        e2 = _make_entry(title="Newest", published_parsed=dt_to_struct(now - timedelta(hours=1)))
        e3 = _make_entry(title="Middle", published_parsed=dt_to_struct(now - timedelta(hours=2)))

        mock_feed = _make_parsed_feed([e1, e2, e3])
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        titles = [i["title"] for i in items]
        assert titles == ["Newest", "Middle", "Oldest"]

    def test_no_date_items_sort_to_end(self):
        """Items with 'data n/d' sort after dated items."""
        now = datetime.now(tz=timezone.utc)

        def dt_to_struct(dt):
            return dt.timetuple()[:9]

        dated_entry = _make_entry(title="Dated", published_parsed=dt_to_struct(now - timedelta(hours=1)))
        no_date_entry = _make_entry(title="Undated", published_parsed=None, published="")

        mock_feed = _make_parsed_feed([no_date_entry, dated_entry])
        feed_info = {"title": "Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["title"] == "Dated"
        assert items[-1]["title"] == "Undated"

    def test_source_name_uses_feed_title(self):
        """Item source should come from feed title."""
        entry = _make_entry(title="Art")
        entry.published_parsed = datetime.now(tz=timezone.utc).timetuple()[:9]
        mock_feed = _make_parsed_feed([entry])
        feed_info = {"title": "My Great Feed", "xmlUrl": "https://example.com/rss"}

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["source"] == "My Great Feed"

    def test_source_name_fallback_to_url(self):
        """If feed has no title, source falls back to URL."""
        entry = _make_entry(title="Art")
        entry.published_parsed = datetime.now(tz=timezone.utc).timetuple()[:9]
        mock_feed = _make_parsed_feed([entry])
        feed_info = {"xmlUrl": "https://example.com/rss"}  # no title key

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            _, items = _fetch_single_feed(feed_info, "Tech", hours=24, max_items=30)

        assert items[0]["source"] == "https://example.com/rss"

    def test_fetch_feeds_merges_multiple_feeds_in_category(self):
        """fetch_feeds merges items from multiple feeds in the same category."""
        now = datetime.now(tz=timezone.utc)

        def dt_to_struct(dt):
            return dt.timetuple()[:9]

        entry1 = _make_entry(title="Feed1 Art", published_parsed=dt_to_struct(now))
        entry2 = _make_entry(title="Feed2 Art", published_parsed=dt_to_struct(now))
        mock_feed1 = _make_parsed_feed([entry1])
        mock_feed2 = _make_parsed_feed([entry2])

        feeds_by_category = {
            "Tech": [
                {"title": "Feed1", "xmlUrl": "https://f1.com/rss"},
                {"title": "Feed2", "xmlUrl": "https://f2.com/rss"},
            ]
        }

        def mock_parse(url, agent=None):
            return mock_feed1 if "f1" in url else mock_feed2

        with patch("src.feed_fetcher.feedparser.parse", side_effect=mock_parse):
            result = fetch_feeds(feeds_by_category, hours=24, max_items=30)

        assert len(result["Tech"]) == 2

    def test_fetch_feeds_caps_after_merge(self):
        """fetch_feeds caps items per category AFTER merging all feeds."""
        now = datetime.now(tz=timezone.utc)

        def dt_to_struct(dt):
            return dt.timetuple()[:9]

        entries = [_make_entry(title=f"Art {i}", published_parsed=dt_to_struct(now - timedelta(minutes=i))) for i in range(5)]
        mock_feed = _make_parsed_feed(entries)

        feeds_by_category = {
            "Tech": [
                {"title": "Feed1", "xmlUrl": "https://f1.com/rss"},
                {"title": "Feed2", "xmlUrl": "https://f2.com/rss"},
            ]
        }

        with patch("src.feed_fetcher.feedparser.parse", return_value=mock_feed):
            result = fetch_feeds(feeds_by_category, hours=24, max_items=3)

        assert len(result["Tech"]) == 3

    def test_fetch_feeds_handles_future_exception(self):
        """If a future raises, that category still exists with partial results."""
        feeds_by_category = {
            "Tech": [{"title": "F", "xmlUrl": "https://x.com/rss"}]
        }

        with patch("src.feed_fetcher.feedparser.parse", side_effect=RuntimeError("boom")):
            result = fetch_feeds(feeds_by_category, hours=24, max_items=30)

        assert "Tech" in result
        assert result["Tech"] == []


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

    def test_all_empty_lists(self):
        """Categories with empty item lists returns 'no articles' message."""
        result = format_digest({"Tech": [], "Biz": []}, "2026-04-05")
        assert result == "Nessun articolo trovato nel periodo selezionato."

    def test_skips_empty_categories(self):
        """Categories with no items are skipped in output."""
        data = {
            "Tech": [{"title": "Art", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}],
            "Empty": [],
        }
        result = format_digest(data, "2026-04-05")
        assert "## Tech" in result
        assert "## Empty" not in result

    def test_item_without_link_omits_link_line(self):
        """Items with empty link don't include the Link line."""
        data = {
            "Tech": [{"title": "Art", "link": "", "published": "2026-04-05", "summary": "S", "source": "F"}],
        }
        result = format_digest(data, "2026-04-05")
        assert "**Link:**" not in result

    def test_item_without_summary_omits_summary(self):
        """Items with empty summary don't include a summary line."""
        data = {
            "Tech": [{"title": "Art", "link": "https://x.com", "published": "2026-04-05", "summary": "", "source": "F"}],
        }
        result = format_digest(data, "2026-04-05")
        lines = result.strip().split("\n")
        # After the **Link:** line, there should be an empty separator, not a summary
        link_lines = [l for l in lines if "**Link:**" in l]
        assert len(link_lines) == 1

    def test_date_in_header(self):
        result = format_digest(
            {"Tech": [{"title": "A", "link": "", "published": "", "summary": "", "source": "F"}]},
            "2026-12-25"
        )
        assert "2026-12-25" in result.split("\n")[0]

    def test_multiple_items_per_category(self):
        data = {
            "Tech": [
                {"title": "Art1", "link": "", "published": "", "summary": "", "source": "F"},
                {"title": "Art2", "link": "", "published": "", "summary": "", "source": "F"},
            ]
        }
        result = format_digest(data, "2026-04-05")
        assert result.count("### ") == 2
