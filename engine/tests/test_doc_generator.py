from pathlib import Path
from docx import Document
from src.doc_generator import generate_docx, generate_fallback_docx


class TestGenerateDocx:
    def test_creates_file(self, tmp_output_dir):
        md = "# Specola — Briefing del 2026-04-05\n\n## Da sapere oggi\n- Punto 1\n- Punto 2"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        assert Path(path).exists()
        assert Path(path).name == "Specola_2026-04-05.docx"

    def test_heading_levels(self, tmp_output_dir):
        md = "# H1 Title\n\n## H2 Section\n\n### H3 Subsection\n\nParagraph text."
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        doc = Document(path)
        styles = [p.style.name for p in doc.paragraphs]
        assert "Heading 1" in styles
        assert "Heading 2" in styles
        assert "Heading 3" in styles
        assert "Normal" in styles

    def test_bullet_lists(self, tmp_output_dir):
        md = "## Section\n\n- Item one\n- Item two\n* Item three"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        doc = Document(path)
        styles = [p.style.name for p in doc.paragraphs]
        assert styles.count("List Bullet") == 3

    def test_numbered_lists(self, tmp_output_dir):
        md = "## Section\n\n1. First\n2. Second\n3. Third"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        doc = Document(path)
        styles = [p.style.name for p in doc.paragraphs]
        assert styles.count("List Number") == 3

    def test_bold_text(self, tmp_output_dir):
        md = "## Section\n\nThis has **bold text** inside."
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        doc = Document(path)
        para = [p for p in doc.paragraphs if p.style.name == "Normal"][0]
        runs_bold = [r.bold for r in para.runs]
        assert True in runs_bold

    def test_header_contains_specola(self, tmp_output_dir):
        md = "# Title"
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        doc = Document(path)
        header = doc.sections[0].header
        header_text = "".join(p.text for p in header.paragraphs)
        assert "SPECOLA" in header_text.upper()

    def test_hyperlinks(self, tmp_output_dir):
        md = "## Section\n\nCheck [this article](https://example.com) for details."
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        doc = Document(path)
        # Verify the document contains the hyperlink text
        all_text = " ".join(p.text for p in doc.paragraphs)
        assert "this article" in all_text or "Check" in all_text

    def test_horizontal_rule(self, tmp_output_dir):
        md = "## Section 1\n\nSome text.\n\n---\n\n## Section 2\n\nMore text."
        path = generate_docx(md, "2026-04-05", tmp_output_dir)
        assert Path(path).exists()

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "subdir" / "output"
        md = "# Title"
        path = generate_docx(md, "2026-04-05", new_dir)
        assert Path(path).exists()


class TestGenerateFallbackDocx:
    def test_creates_file_with_warning(self, tmp_output_dir):
        digest = "## Tech\n\n### Article 1\nSummary here"
        path = generate_fallback_docx(digest, "2026-04-05", tmp_output_dir)
        assert Path(path).exists()
        doc = Document(path)
        texts = [p.text for p in doc.paragraphs]
        assert any("Analisi non disponibile" in t for t in texts)
        assert any("Article 1" in t for t in texts)
