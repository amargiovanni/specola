"""Tests for html_generator — markdown_to_html and generate_html."""
from pathlib import Path

import pytest

from src.html_generator import generate_html, markdown_to_html


class TestMarkdownToHtml:
    def test_h1(self):
        html = markdown_to_html("# Hello World")
        assert "<h1>Hello World</h1>" in html

    def test_h2(self):
        html = markdown_to_html("## Section Title")
        assert "<h2>Section Title</h2>" in html

    def test_h3(self):
        html = markdown_to_html("### Subsection")
        assert "<h3>Subsection</h3>" in html

    def test_bullet_list_dash(self):
        html = markdown_to_html("- Item one\n- Item two")
        assert "<ul>" in html
        assert "</ul>" in html
        assert "<li>Item one</li>" in html
        assert "<li>Item two</li>" in html

    def test_bullet_list_star(self):
        html = markdown_to_html("* Item A\n* Item B")
        assert "<ul>" in html
        assert "</ul>" in html
        assert "<li>Item A</li>" in html
        assert "<li>Item B</li>" in html

    def test_numbered_list(self):
        html = markdown_to_html("1. First\n2. Second\n3. Third")
        assert "<ol>" in html
        assert "</ol>" in html
        assert "<li>First</li>" in html
        assert "<li>Second</li>" in html
        assert "<li>Third</li>" in html

    def test_bold(self):
        html = markdown_to_html("This has **bold text** here.")
        assert "<strong>bold text</strong>" in html

    def test_link(self):
        html = markdown_to_html("See [the article](https://example.com) now.")
        assert '<a href="https://example.com">the article</a>' in html

    def test_horizontal_rule(self):
        html = markdown_to_html("---")
        assert "<hr" in html

    def test_paragraph(self):
        html = markdown_to_html("Just a regular paragraph.")
        assert "<p>Just a regular paragraph.</p>" in html

    def test_empty_lines_ignored(self):
        html = markdown_to_html("\n\n\n")
        assert "<p>" not in html
        assert "<li>" not in html

    def test_mixed_content(self):
        md = "# Title\n\n## Section\n\n- Item\n\nA paragraph."
        html = markdown_to_html(md)
        assert "<h1>Title</h1>" in html
        assert "<h2>Section</h2>" in html
        assert "<li>Item</li>" in html
        assert "<p>A paragraph.</p>" in html

    def test_list_closes_before_non_list(self):
        md = "- Item one\n- Item two\n\nA paragraph after."
        html = markdown_to_html(md)
        # </ul> must appear before <p>
        ul_close = html.index("</ul>")
        p_open = html.index("<p>")
        assert ul_close < p_open

    def test_ul_closes_before_ol(self):
        md = "- Bullet\n\n1. Numbered"
        html = markdown_to_html(md)
        assert "</ul>" in html
        assert "<ol>" in html
        ul_close = html.index("</ul>")
        ol_open = html.index("<ol>")
        assert ul_close < ol_open

    def test_ol_closes_before_ul(self):
        md = "1. Numbered\n\n- Bullet"
        html = markdown_to_html(md)
        assert "</ol>" in html
        assert "<ul>" in html
        ol_close = html.index("</ol>")
        ul_open = html.index("<ul>")
        assert ol_close < ul_open


class TestGenerateHtml:
    def test_creates_file(self, tmp_output_dir):
        md = "# Specola — Briefing del 2026-04-05\n\n## Da sapere oggi\n- Punto 1"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        assert Path(path).exists()

    def test_filename_format(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        assert Path(path).name == "Specola_2026-04-05.html"

    def test_contains_doctype(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "<!DOCTYPE html>" in content

    def test_contains_inline_css(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "<style>" in content

    def test_contains_heading(self, tmp_output_dir):
        md = "# My Briefing Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "My Briefing Title" in content

    def test_contains_footer(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "Specola" in content

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "subdir" / "output"
        md = "# Title"
        path = generate_html(md, "2026-04-05", new_dir)
        assert Path(path).exists()

    def test_language_it_sets_lang_attribute(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir, language="it")
        content = Path(path).read_text()
        assert 'lang="it"' in content

    def test_language_en_sets_lang_attribute(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir, language="en")
        content = Path(path).read_text()
        assert 'lang="en"' in content

    def test_contains_media_print(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "@media print" in content

    def test_returns_string_path(self, tmp_output_dir):
        md = "# Title"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        assert isinstance(path, str)
