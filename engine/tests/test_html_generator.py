"""Tests for html_generator — markdown_to_html, _inline_format, _display_date, generate_html."""
from pathlib import Path

import pytest

from src.html_generator import generate_html, markdown_to_html, _inline_format, _display_date


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
        assert '<a href="https://example.com" target="_blank">the article</a>' in html

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


    def test_direct_transition_ul_to_ol_without_blank_line(self):
        """Switching from bullet to numbered without blank line closes UL first."""
        md = "- Bullet\n1. Number"
        html = markdown_to_html(md)
        assert "</ul>" in html
        assert "<ol>" in html

    def test_direct_transition_ol_to_ul_without_blank_line(self):
        """Switching from numbered to bullet without blank line closes OL first."""
        md = "1. Number\n- Bullet"
        html = markdown_to_html(md)
        assert "</ol>" in html
        assert "<ul>" in html

    def test_heading_closes_open_list(self):
        """A heading after a list closes the list."""
        md = "- Item\n## Heading"
        html = markdown_to_html(md)
        assert "</ul>" in html
        ul_close = html.index("</ul>")
        h2_open = html.index("<h2>")
        assert ul_close < h2_open

    def test_hr_closes_open_list(self):
        """A horizontal rule after a list closes the list."""
        md = "- Item\n---"
        html = markdown_to_html(md)
        assert "</ul>" in html
        ul_close = html.index("</ul>")
        hr_pos = html.index("<hr>")
        assert ul_close < hr_pos

    def test_paragraph_after_ol(self):
        """Paragraph after numbered list closes the OL."""
        md = "1. Item\n\nParagraph text."
        html = markdown_to_html(md)
        assert "</ol>" in html
        ol_close = html.index("</ol>")
        p_open = html.index("<p>")
        assert ol_close < p_open

    def test_end_of_input_closes_lists(self):
        """Lists at end of input are properly closed."""
        md = "- Item one\n- Item two"
        html = markdown_to_html(md)
        assert html.endswith("</ul>")

    def test_end_of_input_closes_ol(self):
        md = "1. First\n2. Second"
        html = markdown_to_html(md)
        assert html.endswith("</ol>")

    def test_empty_string(self):
        html = markdown_to_html("")
        assert html == ""

    def test_only_whitespace(self):
        html = markdown_to_html("   \n   \n   ")
        assert "<p>" not in html

    def test_html_entities_escaped(self):
        """Special chars in text are escaped."""
        html = markdown_to_html("Use < and > symbols & \"quotes\"")
        assert "&lt;" in html
        assert "&gt;" in html
        assert "&amp;" in html

    def test_bold_inside_list_item(self):
        html = markdown_to_html("- **Bold** text in list")
        assert "<strong>Bold</strong>" in html
        assert "<li>" in html

    def test_link_inside_heading(self):
        html = markdown_to_html("## See [this](https://example.com)")
        assert '<a href="https://example.com"' in html
        assert "<h2>" in html

    def test_multiple_links_in_paragraph(self):
        md = "See [link1](https://a.com) and [link2](https://b.com)"
        html = markdown_to_html(md)
        assert html.count('<a href=') == 2

    def test_bold_and_link_together(self):
        md = "**Bold** and [link](https://x.com) here"
        html = markdown_to_html(md)
        assert "<strong>Bold</strong>" in html
        assert '<a href="https://x.com"' in html

    def test_three_dash_hr(self):
        assert "<hr>" in markdown_to_html("---")

    def test_five_dash_hr(self):
        assert "<hr>" in markdown_to_html("-----")

    def test_not_hr_two_dashes(self):
        """Two dashes is not a horizontal rule."""
        html = markdown_to_html("--")
        assert "<hr>" not in html
        assert "<p>--</p>" in html


class TestInlineFormat:
    def test_plain_text(self):
        assert _inline_format("hello") == "hello"

    def test_bold(self):
        assert _inline_format("**bold**") == "<strong>bold</strong>"

    def test_link(self):
        result = _inline_format("[text](https://url.com)")
        assert '<a href="https://url.com" target="_blank">text</a>' in result

    def test_bold_and_link(self):
        result = _inline_format("**bold** and [link](https://x.com)")
        assert "<strong>bold</strong>" in result
        assert '<a href="https://x.com"' in result

    def test_escapes_html_entities(self):
        result = _inline_format("a < b & c > d")
        assert "&lt;" in result
        assert "&amp;" in result
        assert "&gt;" in result

    def test_empty_string(self):
        assert _inline_format("") == ""

    def test_multiple_bolds(self):
        result = _inline_format("**A** normal **B**")
        assert result.count("<strong>") == 2

    def test_link_with_special_chars_in_text(self):
        result = _inline_format("[a & b](https://x.com)")
        assert "a &amp; b" in result


class TestHtmlDisplayDate:
    def test_with_underscore(self):
        assert _display_date("2026-04-05_1930") == "2026-04-05"

    def test_without_underscore(self):
        assert _display_date("2026-04-05") == "2026-04-05"

    def test_empty_string(self):
        assert _display_date("") == ""


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

    def test_date_with_timestamp(self, tmp_output_dir):
        path = generate_html("# T", "2026-04-05_1930", tmp_output_dir)
        assert "Specola_2026-04-05_1930.html" in path
        content = Path(path).read_text()
        # Display date should strip timestamp
        assert "2026-04-05" in content

    def test_title_contains_date(self, tmp_output_dir):
        path = generate_html("# T", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "<title>" in content
        assert "2026-04-05" in content

    def test_page_header_present(self, tmp_output_dir):
        path = generate_html("# T", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "page-header" in content

    def test_utf8_encoding(self, tmp_output_dir):
        md = "# Café résumé über"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        content = Path(path).read_text(encoding="utf-8")
        assert "Café" in content
        assert 'charset="UTF-8"' in content

    def test_a4_page_size_in_css(self, tmp_output_dir):
        path = generate_html("# T", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "size: A4" in content
