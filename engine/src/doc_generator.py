"""DOCX generation from markdown."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_NUMBERED_RE = re.compile(r"^\d+\.\s+")


def _set_default_font(doc: Document) -> None:
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15


def _configure_heading_style(doc: Document, level: int, size: int, color_hex: str) -> None:
    style_name = f"Heading {level}"
    style = doc.styles[style_name]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(size)
    font.bold = True
    font.color.rgb = RGBColor.from_string(color_hex)
    pf = style.paragraph_format
    if level == 1:
        pf.space_before = Pt(18)
        pf.space_after = Pt(6)
    elif level == 2:
        pf.space_before = Pt(14)
        pf.space_after = Pt(4)
    elif level == 3:
        pf.space_before = Pt(10)
        pf.space_after = Pt(4)


def _setup_styles(doc: Document) -> None:
    _set_default_font(doc)
    _configure_heading_style(doc, 1, 18, "1a1a2e")
    _configure_heading_style(doc, 2, 14, "16213e")
    _configure_heading_style(doc, 3, 12, "0f3460")


def _setup_page(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)


def _setup_header_footer(doc: Document, date: str) -> None:
    section = doc.sections[0]

    # Header
    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    hp.clear()
    run_left = hp.add_run("Specola")
    run_left.font.size = Pt(9)
    run_left.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    hp.add_run("\t\t")
    run_right = hp.add_run(date)
    run_right.font.size = Pt(9)
    run_right.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # Footer with page number
    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    fp.clear()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    fld_char_begin = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "begin"})
    run._r.append(fld_char_begin)
    instr = run._r.makeelement(qn("w:instrText"), {})
    instr.text = " PAGE "
    run._r.append(instr)
    fld_char_end = run._r.makeelement(qn("w:fldChar"), {qn("w:fldCharType"): "end"})
    run._r.append(fld_char_end)


def _add_paragraph_with_bold(doc: Document, text: str, style: str = "Normal") -> None:
    para = doc.add_paragraph(style=style)
    parts = _BOLD_RE.split(text)
    for i, part in enumerate(parts):
        if not part:
            continue
        run = para.add_run(part)
        if i % 2 == 1:
            run.bold = True


def generate_docx(markdown: str, date: str, output_dir: str | Path) -> str:
    """Generate DOCX from markdown. Returns output file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.docx"

    doc = Document()
    _setup_styles(doc)
    _setup_page(doc)
    _setup_header_footer(doc, date)

    for line in markdown.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            _add_paragraph_with_bold(doc, stripped[4:], "Heading 3")
        elif stripped.startswith("## "):
            _add_paragraph_with_bold(doc, stripped[3:], "Heading 2")
        elif stripped.startswith("# "):
            _add_paragraph_with_bold(doc, stripped[2:], "Heading 1")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            _add_paragraph_with_bold(doc, stripped[2:], "List Bullet")
        elif _NUMBERED_RE.match(stripped):
            text = _NUMBERED_RE.sub("", stripped)
            _add_paragraph_with_bold(doc, text, "List Number")
        else:
            _add_paragraph_with_bold(doc, stripped)

    doc.save(str(output_path))
    return str(output_path)


def generate_fallback_docx(digest: str, date: str, output_dir: str | Path) -> str:
    """Generate fallback DOCX from raw digest with warning."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"Specola_{date}.docx"

    doc = Document()
    _setup_styles(doc)
    _setup_page(doc)
    _setup_header_footer(doc, date)

    warn = doc.add_paragraph()
    run = warn.add_run("\u26a0 Analisi non disponibile. Di seguito il digest grezzo.")
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    run.bold = True

    doc.add_paragraph()

    for line in digest.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            doc.add_paragraph(stripped[4:], "Heading 3")
        elif stripped.startswith("## "):
            doc.add_paragraph(stripped[3:], "Heading 2")
        elif stripped.startswith("# "):
            doc.add_paragraph(stripped[2:], "Heading 1")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            doc.add_paragraph(stripped[2:], "List Bullet")
        else:
            doc.add_paragraph(stripped)

    doc.save(str(output_path))
    return str(output_path)
