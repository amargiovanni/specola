"""EPUB generation from markdown via ebooklib."""
from __future__ import annotations

from pathlib import Path

from ebooklib import epub

from src.html_generator import markdown_to_html

_EPUB_CSS = """\
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
"""


def generate_epub(
    markdown: str, date: str, output_dir: str | Path, language: str
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
    style = epub.EpubItem(
        uid="style", file_name="style/default.css",
        media_type="text/css", content=_EPUB_CSS.encode("utf-8"),
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
