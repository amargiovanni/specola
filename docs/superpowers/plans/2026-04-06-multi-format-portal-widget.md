# Multi-format Output, HTML Portal, Notification Center Widget — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add output format choice (DOCX/PDF/EPUB) with always-on HTML, a static HTML portal index, and a macOS Notification Center widget showing daily highlights.

**Architecture:** The Python engine gains three new generators (HTML, PDF, EPUB) plus a portal index generator. HTML is always produced alongside the chosen format. The Swift app adds a format picker in settings, extends SpecolaEntry/EngineResult with new fields, and gets a WidgetKit extension target communicating via App Group shared container.

**Tech Stack:** Python (weasyprint, ebooklib), Swift/SwiftUI, WidgetKit, App Groups

**Spec:** `docs/superpowers/specs/2026-04-06-multi-format-portal-widget-design.md`

---

## File Structure

### Python engine — new files
- `engine/src/html_generator.py` — Markdown → HTML standalone (shared `markdown_to_html()` function)
- `engine/src/pdf_generator.py` — HTML → PDF via weasyprint
- `engine/src/epub_generator.py` — Markdown → EPUB via ebooklib
- `engine/src/portal_generator.py` — Regenerates `index.html` from existing HTML briefings
- `engine/tests/test_html_generator.py` — Tests for HTML generation
- `engine/tests/test_pdf_generator.py` — Tests for PDF generation
- `engine/tests/test_epub_generator.py` — Tests for EPUB generation
- `engine/tests/test_portal_generator.py` — Tests for portal index generation
- `engine/tests/test_highlights.py` — Tests for highlight extraction

### Python engine — modified files
- `engine/requirements.txt` — Add weasyprint, ebooklib
- `engine/specola_engine.py` — Add `--format` arg, orchestrate new generators, extract highlights, extend JSON output

### Swift app — modified files
- `Specola/Models/Settings.swift` — Add `outputFormat` key
- `Specola/Models/SpecolaEntry.swift` — Add `htmlPath`, `highlights` fields with backwards-compatible decoding
- `Specola/Services/EngineService.swift` — Pass `--format`, parse new JSON fields
- `Specola/SettingsView.swift` — Add format picker in AdvancedTab
- `Specola/SpecolaApp.swift` — Add `onOpenURL` handler for widget deep link, call `updateWidgetData()`
- `Specola/MenuBarView.swift` — Update SpecolaEntry construction with new fields
- `Specola/Models/AppState.swift` — Add `updateWidgetData()` method

### Swift app — new files
- `Specola/Models/WidgetData.swift` — Shared Codable model for widget data
- `Specola/Specola.entitlements` — App Group entitlement for main app
- `SpecolaWidget/SpecolaWidget.swift` — Widget bundle + TimelineProvider
- `SpecolaWidget/SpecolaWidgetEntry.swift` — Timeline entry model
- `SpecolaWidget/SpecolaWidgetView.swift` — SwiftUI views for systemMedium/Large
- `SpecolaWidget/Info.plist` — Widget extension info
- `SpecolaWidget/SpecolaWidget.entitlements` — App Group entitlement for widget

### Swift app — test files modified
- `SpecolaTests/SpecolaEntryTests.swift` — Tests for backwards-compatible decoding
- `SpecolaTests/EngineServiceTests.swift` — Tests for extended JSON parsing

---

## Task 1: HTML Generator — Shared Markdown→HTML Conversion

**Files:**
- Create: `engine/src/html_generator.py`
- Create: `engine/tests/test_html_generator.py`

This is the core building block: a `markdown_to_html()` function that converts briefing markdown to an HTML string, and a `generate_html()` function that wraps it into a standalone HTML page with inline CSS.

- [ ] **Step 1: Write failing tests for `markdown_to_html()`**

Create `engine/tests/test_html_generator.py`:

```python
from src.html_generator import markdown_to_html, generate_html


class TestMarkdownToHtml:
    def test_h1(self):
        result = markdown_to_html("# Main Title")
        assert "<h1>Main Title</h1>" in result

    def test_h2(self):
        result = markdown_to_html("## Section Title")
        assert "<h2>Section Title</h2>" in result

    def test_h3(self):
        result = markdown_to_html("### Subsection")
        assert "<h3>Subsection</h3>" in result

    def test_bullet_list(self):
        result = markdown_to_html("- Item one\n- Item two")
        assert "<ul>" in result
        assert "<li>Item one</li>" in result
        assert "<li>Item two</li>" in result
        assert "</ul>" in result

    def test_star_bullet_list(self):
        result = markdown_to_html("* Item one\n* Item two")
        assert "<ul>" in result
        assert "<li>" in result

    def test_numbered_list(self):
        result = markdown_to_html("1. First\n2. Second")
        assert "<ol>" in result
        assert "<li>First</li>" in result
        assert "</ol>" in result

    def test_bold(self):
        result = markdown_to_html("This is **bold text** here")
        assert "<strong>bold text</strong>" in result

    def test_link(self):
        result = markdown_to_html("Check [example](https://example.com) link")
        assert '<a href="https://example.com"' in result
        assert "example</a>" in result

    def test_horizontal_rule(self):
        result = markdown_to_html("---")
        assert "<hr" in result

    def test_paragraph(self):
        result = markdown_to_html("Just a plain paragraph.")
        assert "<p>Just a plain paragraph.</p>" in result

    def test_empty_lines_ignored(self):
        result = markdown_to_html("# Title\n\n\nParagraph")
        assert result.count("<p>") == 1

    def test_mixed_content(self):
        md = "# Title\n\n## Section\n\n- **Bold item** with [link](https://x.com)\n- Plain item\n\nParagraph."
        result = markdown_to_html(md)
        assert "<h1>" in result
        assert "<h2>" in result
        assert "<ul>" in result
        assert "<strong>" in result
        assert "<a href" in result
        assert "<p>" in result

    def test_list_closes_before_non_list(self):
        md = "- Item 1\n- Item 2\n\nParagraph after list"
        result = markdown_to_html(md)
        assert result.index("</ul>") < result.index("<p>")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_html_generator.py -v`
Expected: ImportError — `html_generator` module does not exist yet.

- [ ] **Step 3: Implement `markdown_to_html()` in `html_generator.py`**

Create `engine/src/html_generator.py`:

```python
"""HTML generation from markdown — standalone briefing pages."""
from __future__ import annotations

import re
from pathlib import Path

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")
_HR_RE = re.compile(r"^-{3,}$")


def _inline_format(text: str) -> str:
    """Convert inline markdown (bold, links) to HTML."""
    text = _LINK_RE.sub(r'<a href="\2" target="_blank">\1</a>', text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    return text


def markdown_to_html(markdown: str) -> str:
    """Convert briefing markdown to HTML body string."""
    lines = markdown.split("\n")
    parts: list[str] = []
    in_ul = False
    in_ol = False

    def _close_list():
        nonlocal in_ul, in_ol
        if in_ul:
            parts.append("</ul>")
            in_ul = False
        if in_ol:
            parts.append("</ol>")
            in_ol = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            _close_list()
            continue

        if _HR_RE.match(stripped):
            _close_list()
            parts.append("<hr>")
        elif stripped.startswith("### "):
            _close_list()
            parts.append(f"<h3>{_inline_format(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            _close_list()
            parts.append(f"<h2>{_inline_format(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            _close_list()
            parts.append(f"<h1>{_inline_format(stripped[2:])}</h1>")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_ul:
                _close_list()
                parts.append("<ul>")
                in_ul = True
            parts.append(f"<li>{_inline_format(stripped[2:])}</li>")
        elif _NUMBERED_RE.match(stripped):
            if not in_ol:
                _close_list()
                parts.append("<ol>")
                in_ol = True
            text = _NUMBERED_RE.sub("", stripped)
            parts.append(f"<li>{_inline_format(text)}</li>")
        else:
            _close_list()
            parts.append(f"<p>{_inline_format(stripped)}</p>")

    _close_list()
    return "\n".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_html_generator.py -v`
Expected: All tests PASS.

- [ ] **Step 5: Write failing tests for `generate_html()`**

Add to `engine/tests/test_html_generator.py`:

```python
class TestGenerateHtml:
    def test_creates_file(self, tmp_output_dir):
        md = "# Specola — Briefing del 2026-04-05\n\n## Da sapere oggi\n- Punto 1"
        path = generate_html(md, "2026-04-05", tmp_output_dir)
        assert Path(path).exists()
        assert Path(path).suffix == ".html"

    def test_filename_format(self, tmp_output_dir):
        path = generate_html("# Title", "2026-04-05_0700", tmp_output_dir)
        assert "Specola_2026-04-05_0700.html" in path

    def test_contains_doctype(self, tmp_output_dir):
        path = generate_html("# Title", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "<!DOCTYPE html>" in content

    def test_contains_inline_css(self, tmp_output_dir):
        path = generate_html("# Title", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "<style>" in content
        assert "max-width" in content

    def test_contains_heading(self, tmp_output_dir):
        path = generate_html("# My Title\n\n## Section", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "<h1>My Title</h1>" in content
        assert "<h2>Section</h2>" in content

    def test_contains_footer(self, tmp_output_dir):
        path = generate_html("# Title", "2026-04-05", tmp_output_dir)
        content = Path(path).read_text()
        assert "Specola" in content.lower()

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "sub" / "out"
        path = generate_html("# Title", "2026-04-05", new_dir)
        assert Path(path).exists()
```

- [ ] **Step 6: Run tests — new tests should fail**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_html_generator.py::TestGenerateHtml -v`
Expected: FAIL — `generate_html` not yet implemented.

- [ ] **Step 7: Implement `generate_html()`**

Add to `engine/src/html_generator.py`:

```python
_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Specola — Briefing del {date}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; color: #333; background: #fafafa; line-height: 1.7; }}
  .container {{ max-width: 680px; margin: 0 auto; padding: 40px 24px; }}
  header {{ border-bottom: 2px solid #1a1a2e; padding-bottom: 16px; margin-bottom: 32px; }}
  header .title {{ font-size: 28px; font-weight: bold; color: #1a1a2e; letter-spacing: -0.5px; }}
  header .meta {{ font-size: 13px; color: #888; margin-top: 4px; font-family: system-ui, sans-serif; }}
  h1 {{ font-size: 24px; color: #1a1a2e; margin: 24px 0 8px; letter-spacing: -0.3px; }}
  h2 {{ font-size: 18px; color: #16213e; margin: 28px 0 8px; padding-left: 16px; border-left: 3px solid #e94560; }}
  h3 {{ font-size: 15px; color: #0f3460; margin: 20px 0 6px; }}
  p {{ margin-bottom: 12px; font-size: 15px; }}
  ul, ol {{ margin: 8px 0 16px 24px; }}
  li {{ margin-bottom: 6px; font-size: 15px; }}
  a {{ color: #1a73e8; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  strong {{ color: #1a1a2e; }}
  hr {{ border: none; border-top: 1px solid #e5e5e5; margin: 24px 0; }}
  footer {{ text-align: center; padding-top: 24px; margin-top: 32px; border-top: 1px solid #e5e5e5; font-size: 12px; color: #bbb; font-family: system-ui, sans-serif; }}
  @media print {{
    body {{ background: white; }}
    .container {{ max-width: 100%; padding: 0; }}
    @page {{ size: A4; margin: 2.5cm; }}
  }}
</style>
</head>
<body>
<div class="container">
<header>
  <div class="title">Specola</div>
  <div class="meta">Briefing del {date_display}</div>
</header>
{body}
<footer>Generato da Specola &middot; {date_display}</footer>
</div>
</body>
</html>"""


def generate_html(
    markdown: str, date: str, output_dir: str | Path, language: str = "it"
) -> str:
    """Generate standalone HTML briefing from markdown. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.html"

    body = markdown_to_html(markdown)
    date_display = date.replace("_", " ore ").replace("-", "/") if "_" in date else date

    html = _HTML_TEMPLATE.format(
        lang=language,
        date=date,
        date_display=date_display,
        body=body,
    )
    output_path.write_text(html, encoding="utf-8")
    return str(output_path)
```

- [ ] **Step 8: Run all html_generator tests**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_html_generator.py -v`
Expected: All PASS.

- [ ] **Step 9: Commit**

```bash
git add engine/src/html_generator.py engine/tests/test_html_generator.py
git commit -m "feat(engine): add HTML generator with shared markdown_to_html conversion"
```

---

## Task 2: PDF Generator

**Files:**
- Modify: `engine/requirements.txt`
- Create: `engine/src/pdf_generator.py`
- Create: `engine/tests/test_pdf_generator.py`

- [ ] **Step 1: Add weasyprint to requirements.txt**

Modify `engine/requirements.txt` — add after existing lines:

```
weasyprint>=62.0
```

- [ ] **Step 2: Install new dependency**

Run: `cd engine && ../.venv/bin/pip install -r requirements.txt`

- [ ] **Step 3: Write failing tests**

Create `engine/tests/test_pdf_generator.py`:

```python
from pathlib import Path
from src.html_generator import generate_html
from src.pdf_generator import generate_pdf


class TestGeneratePdf:
    def test_creates_file(self, tmp_output_dir):
        md = "# Title\n\n## Section\n\n- Item 1\n- Item 2"
        html_path = generate_html(md, "2026-04-05", tmp_output_dir)
        pdf_path = generate_pdf(html_path, "2026-04-05", tmp_output_dir)
        assert Path(pdf_path).exists()
        assert Path(pdf_path).suffix == ".pdf"

    def test_filename_format(self, tmp_output_dir):
        html_path = generate_html("# T", "2026-04-05_0700", tmp_output_dir)
        pdf_path = generate_pdf(html_path, "2026-04-05_0700", tmp_output_dir)
        assert "Specola_2026-04-05_0700.pdf" in pdf_path

    def test_pdf_is_not_empty(self, tmp_output_dir):
        html_path = generate_html("# Title\n\nContent here.", "2026-04-05", tmp_output_dir)
        pdf_path = generate_pdf(html_path, "2026-04-05", tmp_output_dir)
        assert Path(pdf_path).stat().st_size > 100

    def test_creates_output_dir_if_missing(self, tmp_path):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        html_path = generate_html("# T", "2026-04-05", src_dir)
        out_dir = tmp_path / "new" / "out"
        pdf_path = generate_pdf(html_path, "2026-04-05", out_dir)
        assert Path(pdf_path).exists()
```

- [ ] **Step 4: Run tests — should fail**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_pdf_generator.py -v`
Expected: ImportError — module does not exist.

- [ ] **Step 5: Implement `generate_pdf()`**

Create `engine/src/pdf_generator.py`:

```python
"""PDF generation from HTML via weasyprint."""
from __future__ import annotations

from pathlib import Path

from weasyprint import HTML


def generate_pdf(html_path: str | Path, date: str, output_dir: str | Path) -> str:
    """Convert HTML briefing to PDF. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"Specola_{date}.pdf"

    HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    return str(pdf_path)
```

- [ ] **Step 6: Run tests**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_pdf_generator.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add engine/src/pdf_generator.py engine/tests/test_pdf_generator.py engine/requirements.txt
git commit -m "feat(engine): add PDF generator via weasyprint"
```

---

## Task 3: EPUB Generator

**Files:**
- Modify: `engine/requirements.txt`
- Create: `engine/src/epub_generator.py`
- Create: `engine/tests/test_epub_generator.py`

- [ ] **Step 1: Add ebooklib to requirements.txt**

Modify `engine/requirements.txt` — add after existing lines:

```
ebooklib>=0.18
```

- [ ] **Step 2: Install new dependency**

Run: `cd engine && ../.venv/bin/pip install -r requirements.txt`

- [ ] **Step 3: Write failing tests**

Create `engine/tests/test_epub_generator.py`:

```python
from pathlib import Path
import zipfile
from src.epub_generator import generate_epub


class TestGenerateEpub:
    def test_creates_file(self, tmp_output_dir):
        md = "# Title\n\n## Section\n\n- Item 1\n- Item 2"
        path = generate_epub(md, "2026-04-05", tmp_output_dir, "it")
        assert Path(path).exists()
        assert Path(path).suffix == ".epub"

    def test_filename_format(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05_0700", tmp_output_dir, "it")
        assert "Specola_2026-04-05_0700.epub" in path

    def test_epub_is_valid_zip(self, tmp_output_dir):
        path = generate_epub("# Title\n\nContent.", "2026-04-05", tmp_output_dir, "it")
        assert zipfile.is_zipfile(path)

    def test_epub_contains_content(self, tmp_output_dir):
        md = "# Title\n\n## Da sapere\n\n- Important point"
        path = generate_epub(md, "2026-04-05", tmp_output_dir, "it")
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            # EPUB must contain at least content.opf and a chapter file
            assert any("content.opf" in n for n in names)

    def test_language_it(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05", tmp_output_dir, "it")
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith(".opf"):
                    content = zf.read(name).decode()
                    assert "it" in content
                    break

    def test_language_en(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05", tmp_output_dir, "en")
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith(".opf"):
                    content = zf.read(name).decode()
                    assert "en" in content
                    break

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "sub" / "out"
        path = generate_epub("# T", "2026-04-05", new_dir, "it")
        assert Path(path).exists()
```

- [ ] **Step 4: Run tests — should fail**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_epub_generator.py -v`
Expected: ImportError — module does not exist.

- [ ] **Step 5: Implement `generate_epub()`**

Create `engine/src/epub_generator.py`:

```python
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
```

- [ ] **Step 6: Run tests**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_epub_generator.py -v`
Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add engine/src/epub_generator.py engine/tests/test_epub_generator.py engine/requirements.txt
git commit -m "feat(engine): add EPUB generator via ebooklib"
```

---

## Task 4: Highlight Extraction + Portal Index Generator

**Files:**
- Create: `engine/src/portal_generator.py`
- Create: `engine/tests/test_highlights.py`
- Create: `engine/tests/test_portal_generator.py`

- [ ] **Step 1: Write failing tests for `extract_highlights()`**

Create `engine/tests/test_highlights.py`:

```python
from src.portal_generator import extract_highlights


class TestExtractHighlights:
    def test_extracts_italian_section(self):
        md = (
            "## Da sapere oggi\n"
            "- Point one\n"
            "- Point two\n"
            "- Point three\n"
            "\n"
            "## Richiede attenzione\n"
            "- Something else\n"
        )
        result = extract_highlights(md)
        assert result == ["Point one", "Point two", "Point three"]

    def test_extracts_english_section(self):
        md = (
            "## Key takeaways\n"
            "- Alpha\n"
            "- Beta\n"
        )
        result = extract_highlights(md)
        assert result == ["Alpha", "Beta"]

    def test_max_five_items(self):
        lines = "\n".join(f"- Item {i}" for i in range(10))
        md = f"## Da sapere oggi\n{lines}\n\n## Next section\n"
        result = extract_highlights(md)
        assert len(result) == 5

    def test_strips_bold_and_links(self):
        md = "## Da sapere oggi\n- **Bold item** with [link](https://x.com)\n"
        result = extract_highlights(md)
        assert result == ["Bold item with link"]

    def test_handles_star_bullets(self):
        md = "## Da sapere oggi\n* Star item one\n* Star item two\n"
        result = extract_highlights(md)
        assert result == ["Star item one", "Star item two"]

    def test_returns_empty_if_no_section(self):
        md = "## Some other section\n- Item\n"
        result = extract_highlights(md)
        assert result == []

    def test_numbered_items(self):
        md = "## Da sapere oggi\n1. First\n2. Second\n\n## Next\n"
        result = extract_highlights(md)
        assert result == ["First", "Second"]
```

- [ ] **Step 2: Run tests — should fail**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_highlights.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `extract_highlights()` and `regenerate_portal_index()`**

Create `engine/src/portal_generator.py`:

```python
"""Portal index generation and highlight extraction."""
from __future__ import annotations

import re
from datetime import date
from glob import glob
from pathlib import Path

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")
_BULLET_RE = re.compile(r"^[-*]\s+")
_HIGHLIGHT_SECTIONS = ("## Da sapere oggi", "## Key takeaways")
_MAX_HIGHLIGHTS = 5


def _strip_inline_markdown(text: str) -> str:
    """Remove bold/link markdown, keep plain text."""
    text = _LINK_RE.sub(r"\1", text)
    text = _BOLD_RE.sub(r"\1", text)
    return text.strip()


def extract_highlights(markdown: str) -> list[str]:
    """Extract bullet points from the highlights section. Max 5 items."""
    lines = markdown.split("\n")
    collecting = False
    items: list[str] = []

    for line in lines:
        stripped = line.strip()

        if any(stripped.startswith(s) for s in _HIGHLIGHT_SECTIONS):
            collecting = True
            continue

        if collecting:
            if stripped.startswith("## "):
                break
            if _BULLET_RE.match(stripped):
                text = _BULLET_RE.sub("", stripped)
                items.append(_strip_inline_markdown(text))
            elif _NUMBERED_RE.match(stripped):
                text = _NUMBERED_RE.sub("", stripped)
                items.append(_strip_inline_markdown(text))

        if len(items) >= _MAX_HIGHLIGHTS:
            break

    return items[:_MAX_HIGHLIGHTS]


def _extract_preview_from_html(html_path: Path, max_items: int = 3) -> list[str]:
    """Extract first N bullet texts from an HTML briefing file."""
    content = html_path.read_text(encoding="utf-8")
    items = re.findall(r"<li>(.*?)</li>", content)
    result = []
    for item in items[:max_items]:
        clean = re.sub(r"<[^>]+>", "", item).strip()
        if clean:
            result.append(clean)
    return result


def _date_from_filename(name: str) -> str:
    """Extract date portion from Specola_YYYY-MM-DD*.html filename."""
    m = re.search(r"Specola_(\d{4}-\d{2}-\d{2})", name)
    return m.group(1) if m else ""


_INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Specola — Archivio</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; color: #333; background: #fafafa; line-height: 1.7; }}
  .container {{ max-width: 680px; margin: 0 auto; padding: 40px 24px; }}
  header {{ border-bottom: 2px solid #1a1a2e; padding-bottom: 16px; margin-bottom: 40px; }}
  header .title {{ font-size: 32px; font-weight: bold; color: #1a1a2e; letter-spacing: -0.5px; }}
  header .meta {{ font-size: 14px; color: #888; margin-top: 4px; font-family: system-ui, sans-serif; }}
  .card {{ padding-left: 20px; padding-bottom: 24px; margin-bottom: 28px; border-bottom: 1px solid #eee; }}
  .card.today {{ border-left: 3px solid #e94560; }}
  .card .date {{ font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 1.5px; font-family: system-ui, sans-serif; }}
  .card.today .date {{ color: #e94560; font-weight: bold; }}
  .card a.card-title {{ font-size: 18px; font-weight: bold; color: #1a1a2e; text-decoration: none; display: block; margin: 8px 0 6px; }}
  .card a.card-title:hover {{ color: #e94560; }}
  .card.today a.card-title {{ font-size: 20px; }}
  .card .preview {{ font-size: 14px; color: #555; line-height: 1.7; margin-bottom: 8px; }}
  .card .card-meta {{ font-size: 12px; color: #aaa; font-family: system-ui, sans-serif; }}
  footer {{ text-align: center; padding-top: 24px; margin-top: 16px; border-top: 1px solid #e5e5e5; font-size: 12px; color: #bbb; font-family: system-ui, sans-serif; }}
</style>
</head>
<body>
<div class="container">
<header>
  <div class="title">Specola</div>
  <div class="meta">{archive_label} &middot; {count} {number_label}</div>
</header>
{cards}
<footer>{footer_label} &middot; {today_display}</footer>
</div>
</body>
</html>"""

_LABELS = {
    "it": {
        "archive": "Archivio briefing",
        "numeri": "numeri",
        "numero": "numero",
        "oggi": "Oggi",
        "briefing_del": "Briefing del",
        "footer": "Generato da Specola &middot; Aggiornato il",
    },
    "en": {
        "archive": "Briefing archive",
        "numeri": "issues",
        "numero": "issue",
        "oggi": "Today",
        "briefing_del": "Briefing —",
        "footer": "Generated by Specola &middot; Updated",
    },
}


def regenerate_portal_index(output_dir: str | Path, language: str = "it") -> str:
    """Scan for HTML briefings and regenerate index.html. Returns index path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(
        [p for p in output_dir.glob("Specola_*.html") if p.name != "index.html"],
        key=lambda p: p.name,
        reverse=True,
    )

    today_str = date.today().isoformat()
    labels = _LABELS.get(language, _LABELS["it"])

    cards_html = []
    for f in html_files:
        file_date = _date_from_filename(f.name)
        is_today = file_date == today_str
        css_class = "card today" if is_today else "card"
        date_label = labels["oggi"] if is_today else file_date

        preview_items = _extract_preview_from_html(f)
        preview_html = "<br>".join(f"&bull; {item}" for item in preview_items)

        cards_html.append(
            f'<div class="{css_class}">\n'
            f'  <div class="date">{date_label}</div>\n'
            f'  <a class="card-title" href="{f.name}">{labels["briefing_del"]} {file_date}</a>\n'
            f'  <div class="preview">{preview_html}</div>\n'
            f"</div>"
        )

    count = len(html_files)
    number_label = labels["numero"] if count == 1 else labels["numeri"]

    index_html = _INDEX_TEMPLATE.format(
        lang=language,
        archive_label=labels["archive"],
        count=count,
        number_label=number_label,
        cards="\n".join(cards_html),
        footer_label=labels["footer"],
        today_display=today_str,
    )

    index_path = output_dir / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    return str(index_path)
```

- [ ] **Step 4: Run highlight tests**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_highlights.py -v`
Expected: All PASS.

- [ ] **Step 5: Write failing tests for `regenerate_portal_index()`**

Create `engine/tests/test_portal_generator.py`:

```python
from pathlib import Path
from src.html_generator import generate_html
from src.portal_generator import regenerate_portal_index


class TestRegeneratePortalIndex:
    def test_creates_index_file(self, tmp_output_dir):
        generate_html("# Title\n\n- Bullet one", "2026-04-05", tmp_output_dir)
        path = regenerate_portal_index(tmp_output_dir)
        assert Path(path).exists()
        assert Path(path).name == "index.html"

    def test_index_contains_briefing_link(self, tmp_output_dir):
        generate_html("# Title\n\n- Bullet", "2026-04-05", tmp_output_dir)
        path = regenerate_portal_index(tmp_output_dir)
        content = Path(path).read_text()
        assert "Specola_2026-04-05.html" in content

    def test_multiple_briefings_ordered_newest_first(self, tmp_output_dir):
        generate_html("# T1\n\n- B1", "2026-04-03", tmp_output_dir)
        generate_html("# T2\n\n- B2", "2026-04-05", tmp_output_dir)
        generate_html("# T3\n\n- B3", "2026-04-04", tmp_output_dir)
        path = regenerate_portal_index(tmp_output_dir)
        content = Path(path).read_text()
        pos_05 = content.index("2026-04-05")
        pos_04 = content.index("2026-04-04")
        pos_03 = content.index("2026-04-03")
        assert pos_05 < pos_04 < pos_03

    def test_index_contains_preview_bullets(self, tmp_output_dir):
        generate_html("# Title\n\n## Section\n\n- Important bullet", "2026-04-05", tmp_output_dir)
        path = regenerate_portal_index(tmp_output_dir)
        content = Path(path).read_text()
        assert "Important bullet" in content

    def test_index_excludes_itself(self, tmp_output_dir):
        generate_html("# T", "2026-04-05", tmp_output_dir)
        regenerate_portal_index(tmp_output_dir)
        # Run again — should not list index.html as a briefing
        path = regenerate_portal_index(tmp_output_dir)
        content = Path(path).read_text()
        assert content.count("Specola_") == content.count("Specola_2026")

    def test_empty_directory(self, tmp_output_dir):
        path = regenerate_portal_index(tmp_output_dir)
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "0" in content

    def test_language_en(self, tmp_output_dir):
        generate_html("# T", "2026-04-05", tmp_output_dir)
        path = regenerate_portal_index(tmp_output_dir, language="en")
        content = Path(path).read_text()
        assert "Briefing archive" in content
```

- [ ] **Step 6: Run portal tests**

Run: `cd engine && ../.venv/bin/python -m pytest tests/test_portal_generator.py -v`
Expected: All PASS (implementation already written in step 3).

- [ ] **Step 7: Commit**

```bash
git add engine/src/portal_generator.py engine/tests/test_highlights.py engine/tests/test_portal_generator.py
git commit -m "feat(engine): add portal index generator and highlight extraction"
```

---

## Task 5: Engine Orchestration — Wire New Generators

**Files:**
- Modify: `engine/specola_engine.py:137-228` (run_engine function)
- Modify: `engine/specola_engine.py:236-245` (argparse)

- [ ] **Step 1: Add `--format` CLI argument**

In `engine/specola_engine.py`, after line 241 (`--language`), add:

```python
    run_parser.add_argument("--format", default="docx", choices=["docx", "pdf", "epub"])
```

And update `run_engine()` signature (line 137) to accept the new parameter:

```python
def run_engine(
    opml: str,
    profile: str,
    output_dir: str,
    hours: int,
    language: str,
    max_items: int,
    model: "str | None",
    dry_run: bool,
    verbose: bool,
    output_format: str = "docx",
) -> None:
```

And update the call at line 250:

```python
        run_engine(
            opml=args.opml,
            profile=args.profile,
            output_dir=args.output_dir,
            hours=args.hours,
            language=args.language,
            max_items=args.max_items,
            model=args.model,
            dry_run=args.dry_run,
            verbose=args.verbose,
            output_format=args.format,
        )
```

- [ ] **Step 2: Add imports at top of specola_engine.py**

After the existing imports from `src`, add:

```python
from src.html_generator import generate_html
from src.pdf_generator import generate_pdf
from src.epub_generator import generate_epub
from src.portal_generator import regenerate_portal_index, extract_highlights
```

- [ ] **Step 3: Replace DOCX-only generation with multi-format pipeline**

Replace lines 215–228 (the section starting with `# 5. Assemble final markdown and generate DOCX`) with:

```python
    # 5. Assemble final markdown and generate outputs
    if category_successes > 0:
        final_markdown = _assemble_briefing(synthesis, category_analyses, today_date)
    else:
        logger.warning("All analyses failed, using raw digest")
        final_markdown = full_digest

    # 5a. Always generate HTML standalone
    html_path = generate_html(final_markdown, today, output_dir, language)

    # 5b. Generate the chosen format
    if category_successes > 0:
        if output_format == "docx":
            main_path = generate_docx(final_markdown, today, output_dir)
        elif output_format == "pdf":
            main_path = generate_pdf(html_path, today, output_dir)
        elif output_format == "epub":
            main_path = generate_epub(final_markdown, today, output_dir, language)
        else:
            main_path = html_path
    else:
        main_path = generate_fallback_docx(full_digest, today, output_dir)

    # 5c. Regenerate portal index
    portal_path = regenerate_portal_index(output_dir, language)

    # 5d. Extract highlights for widget
    highlights = extract_highlights(final_markdown)

    _output_json({
        "status": "ok",
        "output_path": main_path,
        "html_path": html_path,
        "portal_path": portal_path,
        "feed_count": feed_count,
        "item_count": item_count,
        "highlights": highlights,
    })
```

- [ ] **Step 4: Run existing engine tests to verify no regressions**

Run: `cd engine && ../.venv/bin/python -m pytest tests/ -v`
Expected: All existing tests PASS. Some engine tests may need a minor update if they check exact JSON output — adjust accordingly.

- [ ] **Step 5: Commit**

```bash
git add engine/specola_engine.py
git commit -m "feat(engine): wire multi-format pipeline with HTML, portal, and highlights"
```

---

## Task 6: Swift — SpecolaSettings + SpecolaEntry Extensions

**Files:**
- Modify: `Specola/Models/Settings.swift:6-16` (Key enum), and add new property after line 67
- Modify: `Specola/Models/SpecolaEntry.swift` (add fields + custom decoder)

- [ ] **Step 1: Add `outputFormat` to SpecolaSettings**

In `Specola/Models/Settings.swift`, add to the `Key` enum (after line 15):

```swift
        static let outputFormat = "outputFormat"
```

Then add the property (after line 67, before `static var supportDir`):

```swift
    static var outputFormat: String {
        get { defaults.string(forKey: Key.outputFormat) ?? "docx" }
        set { defaults.set(newValue, forKey: Key.outputFormat) }
    }
```

- [ ] **Step 2: Extend SpecolaEntry with new fields**

Replace `Specola/Models/SpecolaEntry.swift` entirely:

```swift
import Foundation

struct SpecolaEntry: Codable, Identifiable, Equatable {
    let id: String
    let date: Date
    let path: String
    let htmlPath: String
    let feedCount: Int
    let itemCount: Int
    let highlights: [String]
    var read: Bool

    enum CodingKeys: String, CodingKey {
        case id, date, path, htmlPath, feedCount, itemCount, highlights, read
    }

    init(
        id: String, date: Date, path: String, htmlPath: String = "",
        feedCount: Int, itemCount: Int, highlights: [String] = [], read: Bool
    ) {
        self.id = id
        self.date = date
        self.path = path
        self.htmlPath = htmlPath
        self.feedCount = feedCount
        self.itemCount = itemCount
        self.highlights = highlights
        self.read = read
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        date = try c.decode(Date.self, forKey: .date)
        path = try c.decode(String.self, forKey: .path)
        htmlPath = try c.decodeIfPresent(String.self, forKey: .htmlPath) ?? ""
        feedCount = try c.decode(Int.self, forKey: .feedCount)
        itemCount = try c.decode(Int.self, forKey: .itemCount)
        highlights = try c.decodeIfPresent([String].self, forKey: .highlights) ?? []
        read = try c.decode(Bool.self, forKey: .read)
    }
}
```

- [ ] **Step 3: Verify Swift builds**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: Build succeeds with no errors. There will be build errors from callers that don't pass the new fields — these get fixed in the next tasks.

- [ ] **Step 4: Commit**

```bash
git add Specola/Models/Settings.swift Specola/Models/SpecolaEntry.swift
git commit -m "feat(swift): extend SpecolaSettings and SpecolaEntry for multi-format support"
```

---

## Task 7: Swift — EngineService + SettingsView Updates

**Files:**
- Modify: `Specola/Services/EngineService.swift:1-101`
- Modify: `Specola/SettingsView.swift:177-221`

- [ ] **Step 1: Update EngineResult and EngineService**

In `Specola/Services/EngineService.swift`:

Replace `EngineResult` (lines 3–7):

```swift
struct EngineResult {
    let outputPath: String?
    let htmlPath: String?
    let feedCount: Int
    let itemCount: Int
    let highlights: [String]
}
```

Add `--format` to process arguments (after line 44, before the closing `]`):

```swift
            "--format", SpecolaSettings.outputFormat,
```

Update `parseOutput` (lines 95–99) to parse new fields:

```swift
        return EngineResult(
            outputPath: parsed["output_path"] as? String,
            htmlPath: parsed["html_path"] as? String,
            feedCount: parsed["feed_count"] as? Int ?? 0,
            itemCount: parsed["item_count"] as? Int ?? 0,
            highlights: parsed["highlights"] as? [String] ?? []
        )
```

- [ ] **Step 2: Add format picker to AdvancedTab**

In `Specola/SettingsView.swift`, add `@State` variable to `AdvancedTab` (after line 181):

```swift
    @State private var outputFormat = SpecolaSettings.outputFormat
```

In the `Section("Briefing")` block (after line 199, before the language picker), add:

```swift
                Picker("Formato di output", selection: $outputFormat) {
                    Text("DOCX").tag("docx")
                    Text("PDF").tag("pdf")
                    Text("EPUB").tag("epub")
                }
                .pickerStyle(.segmented)
                .onChange(of: outputFormat) { _, val in SpecolaSettings.outputFormat = val }
```

Also update the "Directory DOCX" label (line 186) to "Directory output" since it's no longer DOCX-only:

```swift
                LabeledContent("Directory output") {
```

- [ ] **Step 3: Verify Swift builds**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: Build errors remain from SpecolaEntry construction sites — fixed next.

- [ ] **Step 4: Commit**

```bash
git add Specola/Services/EngineService.swift Specola/SettingsView.swift
git commit -m "feat(swift): add format picker in settings, extend EngineService for multi-format"
```

---

## Task 8: Swift — Fix SpecolaEntry Construction Sites

**Files:**
- Modify: `Specola/MenuBarView.swift:112-119`
- Modify: `Specola/SpecolaApp.swift:128-135`

Both `MenuBarView.generateNow()` and `SpecolaApp.triggerGeneration()` construct `SpecolaEntry` — they need the new fields.

- [ ] **Step 1: Update MenuBarView.generateNow()**

In `Specola/MenuBarView.swift`, replace the SpecolaEntry construction (lines 112–119):

```swift
                let entry = SpecolaEntry(
                    id: dateId(),
                    date: Date(),
                    path: result.outputPath ?? "",
                    htmlPath: result.htmlPath ?? "",
                    feedCount: result.feedCount,
                    itemCount: result.itemCount,
                    highlights: result.highlights,
                    read: false
                )
```

- [ ] **Step 2: Update SpecolaApp.triggerGeneration()**

In `Specola/SpecolaApp.swift`, replace the SpecolaEntry construction (lines 128–135):

```swift
            let entry = SpecolaEntry(
                id: dateId,
                date: Date(),
                path: result.outputPath ?? "",
                htmlPath: result.htmlPath ?? "",
                feedCount: result.feedCount,
                itemCount: result.itemCount,
                highlights: result.highlights,
                read: false
            )
```

- [ ] **Step 3: Build and verify**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED.

- [ ] **Step 4: Commit**

```bash
git add Specola/MenuBarView.swift Specola/SpecolaApp.swift
git commit -m "fix(swift): update SpecolaEntry construction with htmlPath and highlights"
```

---

## Task 9: Swift — WidgetData Model + AppState Widget Support

**Files:**
- Create: `Specola/Models/WidgetData.swift`
- Modify: `Specola/Models/AppState.swift`

- [ ] **Step 1: Create WidgetData shared model**

Create `Specola/Models/WidgetData.swift`:

```swift
import Foundation

struct WidgetData: Codable {
    let date: Date
    let dateLabel: String
    let unreadCount: Int
    let highlights: [String]
    let latestPath: String

    static let placeholder = WidgetData(
        date: .now,
        dateLabel: "—",
        unreadCount: 0,
        highlights: [],
        latestPath: ""
    )

    static let appGroupID = "group.com.oltrematica.specola"

    static var sharedContainerURL: URL? {
        FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupID)
    }

    static var fileURL: URL? {
        sharedContainerURL?.appendingPathComponent("widget_data.json")
    }
}
```

- [ ] **Step 2: Add `updateWidgetData()` to AppState**

In `Specola/Models/AppState.swift`, add after the `markAsRead` method (after line 64):

```swift
    func updateWidgetData() {
        guard let latest = history.first,
              let url = WidgetData.fileURL else { return }

        let formatter = DateFormatter()
        formatter.dateStyle = .long
        formatter.locale = Locale(identifier: SpecolaSettings.language == "it" ? "it_IT" : "en_US")
        let dateLabel = formatter.string(from: latest.date)

        let data = WidgetData(
            date: latest.date,
            dateLabel: dateLabel,
            unreadCount: unreadCount,
            highlights: latest.highlights,
            latestPath: latest.path
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        try? encoder.encode(data).write(to: url)
    }
```

Also add `import WidgetKit` at the top of AppState.swift (line 1), and add a `WidgetCenter.shared.reloadAllTimelines()` call at the end of `updateWidgetData()`:

```swift
        WidgetCenter.shared.reloadAllTimelines()
```

Then update `addEntry()` and `markAsRead()` to call `updateWidgetData()`:

In `addEntry()` (after `saveHistory()` on line 57), add:

```swift
        updateWidgetData()
```

In `markAsRead()` (after `saveHistory()` on line 63), add:

```swift
        updateWidgetData()
```

- [ ] **Step 3: Build and verify**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED (WidgetKit import works on macOS 14+).

- [ ] **Step 4: Commit**

```bash
git add Specola/Models/WidgetData.swift Specola/Models/AppState.swift
git commit -m "feat(swift): add WidgetData model and updateWidgetData() in AppState"
```

---

## Task 10: Swift — URL Scheme Handler for Widget Deep Link

**Files:**
- Modify: `Specola/SpecolaApp.swift`

- [ ] **Step 1: Add `onOpenURL` handler**

In `Specola/SpecolaApp.swift`, add an `onOpenURL` modifier to the `MenuBarView()` inside `MenuBarExtra` (after line 14, the `.modifier(FirstLaunchModifier())` line):

```swift
                .onOpenURL { url in
                    guard url.scheme == "specola", url.host == "open-latest" else { return }
                    if let latest = appState.history.first {
                        NSWorkspace.shared.open(URL(fileURLWithPath: latest.path))
                        appState.markAsRead(latest)
                    }
                }
```

- [ ] **Step 2: Register URL scheme in Info.plist**

In `Specola/Info.plist`, add the URL scheme registration. This needs to be added as a `CFBundleURLTypes` entry. Read the current Info.plist first, then add before the closing `</dict></plist>`:

```xml
	<key>CFBundleURLTypes</key>
	<array>
		<dict>
			<key>CFBundleURLName</key>
			<string>com.oltrematica.specola</string>
			<key>CFBundleURLSchemes</key>
			<array>
				<string>specola</string>
			</array>
		</dict>
	</array>
```

- [ ] **Step 3: Build and verify**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED.

- [ ] **Step 4: Commit**

```bash
git add Specola/SpecolaApp.swift Specola/Info.plist
git commit -m "feat(swift): add specola:// URL scheme for widget deep link"
```

---

## Task 11: Swift — App Group Entitlement for Main App

**Files:**
- Create: `Specola/Specola.entitlements`
- Note: The Xcode project file needs to reference this entitlement. This step may require manual Xcode configuration.

- [ ] **Step 1: Create entitlements file**

Create `Specola/Specola.entitlements`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>com.apple.security.application-groups</key>
	<array>
		<string>group.com.oltrematica.specola</string>
	</array>
</dict>
</plist>
```

- [ ] **Step 2: Add entitlements reference to Xcode project**

This needs to be configured in the Xcode project's build settings: `Signing & Capabilities > + Capability > App Groups` and add `group.com.oltrematica.specola`. Alternatively, add `CODE_SIGN_ENTITLEMENTS = Specola/Specola.entitlements` to the build settings in `project.pbxproj`.

Run: Open Xcode and add the entitlement via the GUI, or modify `project.pbxproj` to add `CODE_SIGN_ENTITLEMENTS = Specola/Specola.entitlements;` to the main app target's build settings.

- [ ] **Step 3: Build and verify**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED.

- [ ] **Step 4: Commit**

```bash
git add Specola/Specola.entitlements
git commit -m "feat(swift): add App Group entitlement for widget communication"
```

---

## Task 12: WidgetKit Extension — Target + Provider + Views

**Files:**
- Create: `SpecolaWidget/SpecolaWidget.swift`
- Create: `SpecolaWidget/SpecolaWidgetEntry.swift`
- Create: `SpecolaWidget/SpecolaWidgetView.swift`
- Create: `SpecolaWidget/Info.plist`
- Create: `SpecolaWidget/SpecolaWidget.entitlements`

This task creates the widget extension. **Note:** Adding a new target to the Xcode project requires either using Xcode's GUI (File > New > Target > Widget Extension) or manually editing `project.pbxproj`. The recommended approach is to use Xcode's GUI to create the target, then replace the generated files with the ones below.

- [ ] **Step 1: Create widget extension target in Xcode**

In Xcode: File > New > Target > Widget Extension. Name it `SpecolaWidget`. Deployment target: macOS 14. Uncheck "Include Configuration App Intent". This creates the target, build settings, and linking automatically.

- [ ] **Step 2: Add App Group entitlement for widget**

Create `SpecolaWidget/SpecolaWidget.entitlements`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>com.apple.security.application-groups</key>
	<array>
		<string>group.com.oltrematica.specola</string>
	</array>
</dict>
</plist>
```

- [ ] **Step 3: Create SpecolaWidgetEntry**

Create `SpecolaWidget/SpecolaWidgetEntry.swift`:

```swift
import WidgetKit

struct SpecolaWidgetEntry: TimelineEntry {
    let date: Date
    let data: WidgetSnapshot
}

struct WidgetSnapshot {
    let briefingDate: Date
    let dateLabel: String
    let unreadCount: Int
    let highlights: [String]
    let latestPath: String
    let isEmpty: Bool

    static let placeholder = WidgetSnapshot(
        briefingDate: .now,
        dateLabel: "6 aprile 2026",
        unreadCount: 2,
        highlights: [
            "EU approva regolamento AI Act",
            "GitHub Copilot Workspace in GA",
            "Vulnerabilita critica OpenSSL 3.x",
        ],
        latestPath: "",
        isEmpty: false
    )

    static let empty = WidgetSnapshot(
        briefingDate: .now,
        dateLabel: "—",
        unreadCount: 0,
        highlights: [],
        latestPath: "",
        isEmpty: true
    )
}

func loadWidgetSnapshot() -> WidgetSnapshot {
    let appGroupID = "group.com.oltrematica.specola"
    guard let container = FileManager.default.containerURL(
        forSecurityApplicationGroupIdentifier: appGroupID
    ) else { return .empty }

    let fileURL = container.appendingPathComponent("widget_data.json")
    guard let data = try? Data(contentsOf: fileURL) else { return .empty }

    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601

    struct RawData: Decodable {
        let date: Date
        let dateLabel: String
        let unreadCount: Int
        let highlights: [String]
        let latestPath: String
    }

    guard let raw = try? decoder.decode(RawData.self, from: data) else { return .empty }

    return WidgetSnapshot(
        briefingDate: raw.date,
        dateLabel: raw.dateLabel,
        unreadCount: raw.unreadCount,
        highlights: raw.highlights,
        latestPath: raw.latestPath,
        isEmpty: false
    )
}
```

- [ ] **Step 4: Create SpecolaWidgetView**

Create `SpecolaWidget/SpecolaWidgetView.swift`:

```swift
import SwiftUI
import WidgetKit

struct SpecolaWidgetView: View {
    let entry: SpecolaWidgetEntry
    @Environment(\.widgetFamily) var family

    var body: some View {
        if entry.data.isEmpty {
            emptyState
        } else {
            content
        }
    }

    private var content: some View {
        VStack(alignment: .leading, spacing: 8) {
            header
            Divider()
            sectionTitle
            highlights
            Spacer(minLength: 0)
        }
        .padding()
        .widgetURL(URL(string: "specola://open-latest"))
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Specola")
                    .font(.headline)
                    .fontWeight(.bold)
                Text(entry.data.dateLabel)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if entry.data.unreadCount > 0 {
                Text("\(entry.data.unreadCount)")
                    .font(.caption2)
                    .fontWeight(.bold)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.red, in: Capsule())
            }
        }
    }

    private var sectionTitle: some View {
        Text("Da sapere oggi")
            .font(.subheadline)
            .fontWeight(.semibold)
            .foregroundStyle(Color(red: 0.91, green: 0.27, blue: 0.38)) // #e94560
    }

    private var highlights: some View {
        let maxItems = family == .systemMedium ? 3 : 5
        return VStack(alignment: .leading, spacing: 6) {
            ForEach(
                Array(entry.data.highlights.prefix(maxItems).enumerated()),
                id: \.offset
            ) { _, item in
                HStack(alignment: .top, spacing: 6) {
                    Text("\u{2022}")
                        .foregroundStyle(.secondary)
                    Text(item)
                        .font(.caption)
                        .lineLimit(2)
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 8) {
            Text("Specola")
                .font(.headline)
                .fontWeight(.bold)
            Text("Nessun briefing disponibile")
                .font(.caption)
                .foregroundStyle(.secondary)
            Text("Configura l'app per iniziare")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}
```

- [ ] **Step 5: Create main SpecolaWidget file**

Create `SpecolaWidget/SpecolaWidget.swift`:

```swift
import WidgetKit
import SwiftUI

struct SpecolaProvider: TimelineProvider {
    func placeholder(in context: Context) -> SpecolaWidgetEntry {
        SpecolaWidgetEntry(date: .now, data: .placeholder)
    }

    func getSnapshot(in context: Context, completion: @escaping (SpecolaWidgetEntry) -> Void) {
        let snapshot = loadWidgetSnapshot()
        completion(SpecolaWidgetEntry(date: .now, data: snapshot))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<SpecolaWidgetEntry>) -> Void) {
        let snapshot = loadWidgetSnapshot()
        let entry = SpecolaWidgetEntry(date: .now, data: snapshot)
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
    }
}

struct SpecolaWidgetBundle: Widget {
    let kind = "com.oltrematica.specola.widget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: SpecolaProvider()) { entry in
            SpecolaWidgetView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Specola")
        .description("I punti chiave del briefing di oggi")
        .supportedFamilies([.systemMedium, .systemLarge])
    }
}

@main
struct SpecolaWidgets: WidgetBundle {
    var body: some Widget {
        SpecolaWidgetBundle()
    }
}
```

- [ ] **Step 6: Build widget target**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme SpecolaWidgetExtension -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED.

- [ ] **Step 7: Build full app**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED.

- [ ] **Step 8: Commit**

```bash
git add SpecolaWidget/
git commit -m "feat(widget): add Notification Center widget with highlights preview"
```

---

## Task 13: Run All Tests + Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run all Python tests**

Run: `cd engine && ../.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 2: Run Swift build**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet build 2>&1 | tail -5`
Expected: BUILD SUCCEEDED.

- [ ] **Step 3: Run Swift tests**

Run: `cd /Users/andreamargiovanni/dev/specola && xcodebuild -scheme Specola -quiet test 2>&1 | tail -20`
Expected: All tests PASS (some may need updating for new SpecolaEntry fields).

- [ ] **Step 4: Dry-run the engine with --format flag**

Run: `cd engine && ../.venv/bin/python specola_engine.py run --opml /path/to/test.opml --profile /path/to/profile.md --output-dir /tmp/specola-test --format pdf --dry-run`
Expected: JSON output with `status: ok` (dry-run doesn't generate files but validates args).

- [ ] **Step 5: Review full diff**

Run: `git diff main --stat`
Review all changes for forgotten debug code, leftover TODOs, or unintended modifications.
