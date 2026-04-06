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

    def test_returns_string_path(self, tmp_output_dir):
        html_path = generate_html("# T", "2026-04-05", tmp_output_dir)
        pdf_path = generate_pdf(html_path, "2026-04-05", tmp_output_dir)
        assert isinstance(pdf_path, str)

    def test_complex_html_generates_pdf(self, tmp_output_dir):
        md = "# Title\n\n## Section\n\n- **Bold** item\n- [Link](https://x.com)\n\n---\n\n1. First\n2. Second"
        html_path = generate_html(md, "2026-04-05", tmp_output_dir)
        pdf_path = generate_pdf(html_path, "2026-04-05", tmp_output_dir)
        assert Path(pdf_path).exists()
        assert Path(pdf_path).stat().st_size > 100

    def test_date_with_timestamp(self, tmp_output_dir):
        html_path = generate_html("# T", "2026-04-05_1930", tmp_output_dir)
        pdf_path = generate_pdf(html_path, "2026-04-05_1930", tmp_output_dir)
        assert "Specola_2026-04-05_1930.pdf" in pdf_path
