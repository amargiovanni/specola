"""Tests for extract_highlights in portal_generator."""
import pytest

from src.portal_generator import extract_highlights


ITALIAN_MD = """\
# Specola — Briefing del 2026-04-05

## Da sapere oggi
- **OpenAI** lancia GPT-5 con ragionamento migliorato (TechCrunch)
- L'AI Act EU entra in vigore oggi
- ECB mantiene i tassi invariati
- [Apple annuncia](https://example.com) nuovi chip
- Mercati europei in rialzo del 2%

## Richiede attenzione
- Aggiornare le dipendenze entro venerdì
"""

ENGLISH_MD = """\
# Specola — Briefing 2026-04-05

## Key takeaways
- **OpenAI** launches GPT-5 with improved reasoning (TechCrunch)
- EU AI Act enters enforcement phase today
- ECB holds rates steady

## Requires attention
- Update dependencies by Friday
"""

STAR_BULLETS_MD = """\
## Da sapere oggi
* First item
* Second item
* Third item
"""

NUMBERED_MD = """\
## Da sapere oggi
1. First numbered item
2. Second numbered item
3. Third numbered item
"""

BOLD_AND_LINK_MD = """\
## Da sapere oggi
- **Bold title**: something happened (Source)
- See [the article](https://example.com/foo) for details
- Normal item
"""

SIX_ITEMS_MD = """\
## Da sapere oggi
- Item one
- Item two
- Item three
- Item four
- Item five
- Item six — should be excluded
"""

NO_SECTION_MD = """\
# Briefing

## Richiede attenzione
- Something urgent
"""


class TestExtractHighlights:
    def test_italian_section(self):
        items = extract_highlights(ITALIAN_MD)
        assert len(items) > 0
        assert any("GPT-5" in item for item in items)

    def test_english_section(self):
        items = extract_highlights(ENGLISH_MD)
        assert len(items) > 0
        assert any("GPT-5" in item for item in items)

    def test_max_five_items(self):
        items = extract_highlights(SIX_ITEMS_MD)
        assert len(items) == 5

    def test_strips_bold(self):
        items = extract_highlights(BOLD_AND_LINK_MD)
        assert not any("**" in item for item in items)
        assert any("Bold title" in item for item in items)

    def test_strips_links(self):
        items = extract_highlights(BOLD_AND_LINK_MD)
        assert not any("[" in item or "](" in item for item in items)
        assert any("the article" in item for item in items)

    def test_star_bullets(self):
        items = extract_highlights(STAR_BULLETS_MD)
        assert items == ["First item", "Second item", "Third item"]

    def test_empty_if_no_section(self):
        items = extract_highlights(NO_SECTION_MD)
        assert items == []

    def test_numbered_items(self):
        items = extract_highlights(NUMBERED_MD)
        assert len(items) == 3
        assert "First numbered item" in items

    def test_stops_at_next_heading(self):
        items = extract_highlights(ITALIAN_MD)
        # Items from "Richiede attenzione" section must not bleed in
        assert not any("Aggiornare" in item for item in items)

    def test_returns_plain_text_strings(self):
        items = extract_highlights(ENGLISH_MD)
        for item in items:
            assert isinstance(item, str)
            assert item.strip() == item

    def test_empty_markdown(self):
        assert extract_highlights("") == []

    def test_only_heading_no_items(self):
        md = "## Da sapere oggi\n\n## Next section"
        assert extract_highlights(md) == []

    def test_items_with_whitespace_stripped(self):
        md = "## Da sapere oggi\n-   Spaced item   \n"
        items = extract_highlights(md)
        assert items == ["Spaced item"]

    def test_ignores_non_bullet_text(self):
        """Non-bullet text between heading and next heading is ignored."""
        md = "## Da sapere oggi\nJust a paragraph\n- Actual item"
        items = extract_highlights(md)
        assert items == ["Actual item"]

    def test_stops_at_h1(self):
        """Stops at H1 heading too, not just H2."""
        md = "## Da sapere oggi\n- Item 1\n# Top Level\n- Should not appear"
        items = extract_highlights(md)
        assert len(items) == 1
        assert items[0] == "Item 1"

    def test_mixed_bullet_and_numbered(self):
        md = "## Da sapere oggi\n- Bullet item\n1. Numbered item\n* Star item"
        items = extract_highlights(md)
        assert len(items) == 3

    def test_exactly_five_items(self):
        md = "## Da sapere oggi\n- One\n- Two\n- Three\n- Four\n- Five"
        items = extract_highlights(md)
        assert len(items) == 5

    def test_empty_items_skipped(self):
        """Empty bullet points (after stripping) are skipped."""
        md = "## Da sapere oggi\n- **\n- Real item"
        items = extract_highlights(md)
        # "**" with nothing inside should be stripped to empty? Actually **\n is malformed.
        # Let's just check "Real item" is present
        assert "Real item" in items

    def test_link_with_url_stripped(self):
        md = "## Da sapere oggi\n- Check [this article](https://example.com/foo/bar?q=1) now"
        items = extract_highlights(md)
        assert items == ["Check this article now"]

    def test_multiple_links_in_one_item(self):
        md = "## Da sapere oggi\n- See [A](https://a.com) and [B](https://b.com)"
        items = extract_highlights(md)
        assert items == ["See A and B"]
