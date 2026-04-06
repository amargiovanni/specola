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
