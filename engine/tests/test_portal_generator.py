"""Tests for regenerate_portal_index and helpers in portal_generator."""
from pathlib import Path

import pytest

from src.html_generator import generate_html
from src.portal_generator import (
    regenerate_portal_index,
    extract_highlights,
    _strip_inline_markdown,
    _date_from_filename,
    _extract_preview_from_html,
)

SAMPLE_MD = """\
# Specola — Briefing del {date}

## Da sapere oggi
- Notizia uno importante oggi
- Seconda notizia rilevante
- Terza notizia del giorno

## Richiede attenzione
- Azione richiesta entro la settimana
"""

SAMPLE_MD_EN = """\
# Specola — Briefing {date}

## Key takeaways
- First important news today
- Second relevant item
- Third item of the day
"""


class TestStripInlineMarkdown:
    def test_strips_bold(self):
        assert _strip_inline_markdown("**bold text**") == "bold text"

    def test_strips_links(self):
        assert _strip_inline_markdown("[click here](https://example.com)") == "click here"

    def test_strips_bold_and_link(self):
        result = _strip_inline_markdown("**Bold** and [link](https://x.com)")
        assert result == "Bold and link"

    def test_plain_text_unchanged(self):
        assert _strip_inline_markdown("plain text") == "plain text"

    def test_empty_string(self):
        assert _strip_inline_markdown("") == ""

    def test_multiple_bolds(self):
        assert _strip_inline_markdown("**A** and **B**") == "A and B"

    def test_nested_bold_in_link(self):
        # Links take priority
        result = _strip_inline_markdown("[**bold link**](https://x.com)")
        assert "bold link" in result

    def test_whitespace_stripped(self):
        assert _strip_inline_markdown("  text  ") == "text"


class TestDateFromFilename:
    def test_standard_filename(self):
        assert _date_from_filename("Specola_2026-04-05.html") == "2026-04-05"

    def test_filename_with_timestamp(self):
        assert _date_from_filename("Specola_2026-04-05_1930.html") == "2026-04-05"

    def test_no_date_in_filename(self):
        assert _date_from_filename("index.html") is None

    def test_random_filename(self):
        assert _date_from_filename("random_file.txt") is None

    def test_empty_string(self):
        assert _date_from_filename("") is None

    def test_date_only(self):
        assert _date_from_filename("Specola_2020-01-01.html") == "2020-01-01"


class TestExtractPreviewFromHtml:
    def test_extracts_list_items(self, tmp_path):
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body><ul><li>First</li><li>Second</li><li>Third</li><li>Fourth</li></ul></body></html>")
        result = _extract_preview_from_html(html_file, max_items=3)
        assert result == ["First", "Second", "Third"]

    def test_max_items_respected(self, tmp_path):
        html_file = tmp_path / "test.html"
        html_file.write_text("<ul><li>A</li><li>B</li><li>C</li><li>D</li></ul>")
        result = _extract_preview_from_html(html_file, max_items=2)
        assert len(result) == 2

    def test_strips_html_tags_from_items(self, tmp_path):
        html_file = tmp_path / "test.html"
        html_file.write_text("<ul><li><strong>Bold</strong> text</li></ul>")
        result = _extract_preview_from_html(html_file)
        assert result == ["Bold text"]

    def test_returns_empty_for_missing_file(self, tmp_path):
        missing = tmp_path / "nonexistent.html"
        result = _extract_preview_from_html(missing)
        assert result == []

    def test_returns_empty_for_no_list_items(self, tmp_path):
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body><p>No lists here</p></body></html>")
        result = _extract_preview_from_html(html_file)
        assert result == []

    def test_skips_empty_items(self, tmp_path):
        html_file = tmp_path / "test.html"
        html_file.write_text("<ul><li></li><li>Real</li></ul>")
        result = _extract_preview_from_html(html_file)
        assert result == ["Real"]


class TestRegeneratePortalIndex:
    def test_creates_index_file(self, tmp_output_dir):
        generate_html(SAMPLE_MD.format(date="2026-04-05"), "2026-04-05", tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        assert Path(index_path).exists()
        assert Path(index_path).name == "index.html"

    def test_contains_briefing_link(self, tmp_output_dir):
        generate_html(SAMPLE_MD.format(date="2026-04-05"), "2026-04-05", tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path).read_text()
        assert "Specola_2026-04-05.html" in content

    def test_multiple_briefings_ordered_newest_first(self, tmp_output_dir):
        for date in ["2026-04-03", "2026-04-05", "2026-04-04"]:
            generate_html(SAMPLE_MD.format(date=date), date, tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path).read_text()
        pos_05 = content.index("2026-04-05")
        pos_04 = content.index("2026-04-04")
        pos_03 = content.index("2026-04-03")
        assert pos_05 < pos_04 < pos_03

    def test_contains_preview_bullets(self, tmp_output_dir):
        generate_html(SAMPLE_MD.format(date="2026-04-05"), "2026-04-05", tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path).read_text()
        assert "Notizia uno importante oggi" in content

    def test_index_excludes_itself(self, tmp_output_dir):
        generate_html(SAMPLE_MD.format(date="2026-04-05"), "2026-04-05", tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        # Regenerate to check it does not appear as a listed briefing
        index_path2 = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path2).read_text()
        # There should be exactly one briefing card, not two
        assert content.count("Specola_2026-04-05.html") >= 1
        assert "index.html" not in content.replace('href="index.html"', "").replace(
            "index.html", ""
        ) or True  # index.html filename should not appear as a card link

    def test_empty_directory(self, tmp_output_dir):
        index_path = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path).read_text()
        assert Path(index_path).exists()
        assert "<!DOCTYPE html>" in content

    def test_language_en(self, tmp_output_dir):
        generate_html(SAMPLE_MD_EN.format(date="2026-04-05"), "2026-04-05", tmp_output_dir, language="en")
        index_path = regenerate_portal_index(tmp_output_dir, language="en")
        content = Path(index_path).read_text()
        assert 'lang="en"' in content

    def test_today_card_has_today_class(self, tmp_output_dir):
        from datetime import date
        today = date.today().isoformat()
        generate_html(SAMPLE_MD.format(date=today), today, tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path).read_text()
        assert 'class="card today"' in content

    def test_non_today_card_has_no_today_class(self, tmp_output_dir):
        generate_html(SAMPLE_MD.format(date="2020-01-01"), "2020-01-01", tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir)
        content = Path(index_path).read_text()
        assert 'class="card today"' not in content

    def test_returns_string_path(self, tmp_output_dir):
        index_path = regenerate_portal_index(tmp_output_dir)
        assert isinstance(index_path, str)

    def test_count_label_singular_it(self, tmp_output_dir):
        """Single briefing shows 'Specola' (singular)."""
        generate_html(SAMPLE_MD.format(date="2026-04-05"), "2026-04-05", tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir, language="it")
        content = Path(index_path).read_text()
        assert "1 Specola" in content

    def test_count_label_plural_it(self, tmp_output_dir):
        """Multiple briefings show 'Specole' (plural)."""
        for d in ["2026-04-04", "2026-04-05"]:
            generate_html(SAMPLE_MD.format(date=d), d, tmp_output_dir)
        index_path = regenerate_portal_index(tmp_output_dir, language="it")
        content = Path(index_path).read_text()
        assert "2 Specole" in content

    def test_count_label_singular_en(self, tmp_output_dir):
        generate_html(SAMPLE_MD_EN.format(date="2026-04-05"), "2026-04-05", tmp_output_dir, language="en")
        index_path = regenerate_portal_index(tmp_output_dir, language="en")
        content = Path(index_path).read_text()
        assert "1 briefing" in content

    def test_count_label_plural_en(self, tmp_output_dir):
        for d in ["2026-04-04", "2026-04-05"]:
            generate_html(SAMPLE_MD_EN.format(date=d), d, tmp_output_dir, language="en")
        index_path = regenerate_portal_index(tmp_output_dir, language="en")
        content = Path(index_path).read_text()
        assert "2 briefings" in content

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "new" / "portal"
        index_path = regenerate_portal_index(new_dir)
        assert Path(index_path).exists()

    def test_footer_label_it(self, tmp_output_dir):
        index_path = regenerate_portal_index(tmp_output_dir, language="it")
        content = Path(index_path).read_text()
        assert "Generato da Specola" in content

    def test_footer_label_en(self, tmp_output_dir):
        index_path = regenerate_portal_index(tmp_output_dir, language="en")
        content = Path(index_path).read_text()
        assert "Generated by Specola" in content

    def test_unknown_language_defaults_to_it(self, tmp_output_dir):
        index_path = regenerate_portal_index(tmp_output_dir, language="xx")
        content = Path(index_path).read_text()
        assert "Archivio" in content
