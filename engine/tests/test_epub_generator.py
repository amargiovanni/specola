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

    def test_returns_string_path(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05", tmp_output_dir, "it")
        assert isinstance(path, str)

    def test_epub_has_briefing_chapter(self, tmp_output_dir):
        md = "# Title\n\n## Section\n\n- Item"
        path = generate_epub(md, "2026-04-05", tmp_output_dir, "it")
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            assert any("briefing" in n for n in names)

    def test_epub_has_css(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05", tmp_output_dir, "it")
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            assert any("style" in n and ".css" in n for n in names)

    def test_epub_title_includes_date(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05", tmp_output_dir, "it")
        with zipfile.ZipFile(path) as zf:
            for name in zf.namelist():
                if name.endswith(".opf"):
                    content = zf.read(name).decode()
                    assert "2026-04-05" in content
                    break

    def test_epub_has_nav(self, tmp_output_dir):
        path = generate_epub("# T", "2026-04-05", tmp_output_dir, "it")
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            assert any("nav" in n.lower() for n in names)

    def test_complex_markdown_in_epub(self, tmp_output_dir):
        md = "# Title\n\n## Da sapere\n\n- **Bold** item\n- [Link](https://x.com)\n\n---\n\n## Section 2\n\n1. First\n2. Second"
        path = generate_epub(md, "2026-04-05", tmp_output_dir, "it")
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0
