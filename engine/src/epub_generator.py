"""EPUB generation from markdown via ebooklib."""
from __future__ import annotations

from pathlib import Path

from ebooklib import epub

from src.html_generator import markdown_to_html

_EPUB_CSS_THEMES: dict[str, str] = {
    "corporate": """\
body { font-family: Georgia, serif; color: #333; line-height: 1.7; }
h1 { font-size: 1.6em; color: #1a1a2e; margin: 1em 0 0.3em; }
h2 { font-size: 1.3em; color: #16213e; margin: 1em 0 0.3em; padding-left: 12px; border-left: 3px solid #e94560; }
h3 { font-size: 1.1em; color: #0f3460; margin: 0.8em 0 0.3em; }
p { margin-bottom: 0.8em; }
ul, ol { margin: 0.5em 0 1em 1.5em; }
li { margin-bottom: 0.4em; }
a { color: #1a73e8; text-decoration: none; }
strong { color: #1a1a2e; }
hr { border: none; border-top: 1px solid #ddd; margin: 1.5em 0; }
""",
    "minimal": """\
body { font-family: Georgia, serif; color: #1a1a1a; background: #fafaf9; line-height: 1.7; }
h1 { font-size: 1.6em; color: #1a1a1a; margin: 1em 0 0.3em; }
h2 { font-size: 1.3em; color: #1a1a1a; margin: 1em 0 0.3em; padding-left: 12px; border-left: 3px solid #d4d4d4; }
h3 { font-size: 1.1em; color: #1a1a1a; margin: 0.8em 0 0.3em; }
p { margin-bottom: 0.8em; }
ul, ol { margin: 0.5em 0 1em 1.5em; }
li { margin-bottom: 0.4em; }
a { color: #1e3a5f; text-decoration: none; }
strong { color: #1a1a1a; }
hr { border: none; border-top: 1px solid #d4d4d4; margin: 1.5em 0; }
""",
    "dark": """\
body { font-family: Georgia, serif; color: #e0e0e0; background: #1a1a2e; line-height: 1.7; }
h1 { font-size: 1.6em; color: #e0e0e0; margin: 1em 0 0.3em; }
h2 { font-size: 1.3em; color: #c0c0d0; margin: 1em 0 0.3em; padding-left: 12px; border-left: 3px solid #e94560; }
h3 { font-size: 1.1em; color: #a0a0b8; margin: 0.8em 0 0.3em; }
p { margin-bottom: 0.8em; }
ul, ol { margin: 0.5em 0 1em 1.5em; }
li { margin-bottom: 0.4em; }
a { color: #82b1ff; text-decoration: none; }
strong { color: #ffffff; }
hr { border: none; border-top: 1px solid #3a3a5e; margin: 1.5em 0; }
""",
}

# Keep backward-compatible alias
_EPUB_CSS = _EPUB_CSS_THEMES["corporate"]


def generate_epub(
    markdown: str, date: str, output_dir: str | Path, language: str,
    theme: str = "corporate",
) -> str:
    """Generate EPUB from markdown. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    epub_path = output_dir / f"Specola_{date}.epub"

    book = epub.EpubBook()
    book.set_identifier(f"specola-{date}")
    book.set_title(f"Specola — Briefing del {date}")
    book.set_language(language)
    book.add_author("Specola")

    # CSS
    css_text = _EPUB_CSS_THEMES.get(theme, _EPUB_CSS_THEMES["corporate"])
    style = epub.EpubItem(
        uid="style", file_name="style/default.css",
        media_type="text/css", content=css_text.encode("utf-8"),
    )
    book.add_item(style)

    # Chapter
    chapter = epub.EpubHtml(
        title=f"Briefing del {date}", file_name="briefing.xhtml", lang=language,
    )
    chapter.content = (
        f"<html><body>{markdown_to_html(markdown)}</body></html>"
    )
    chapter.add_item(style)
    book.add_item(chapter)

    # Navigation
    book.toc = [chapter]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]

    epub.write_epub(str(epub_path), book)
    return str(epub_path)
