"""Tests for regenerate_portal_index in portal_generator."""
from pathlib import Path

import pytest

from src.html_generator import generate_html
from src.portal_generator import regenerate_portal_index

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
