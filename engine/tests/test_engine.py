import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from specola_engine import run_engine, _output_json, _analyze_categories, _synthesize, _assemble_briefing


class TestRunEngine:
    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_dry_run(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {
            "Tech": [{"title": "Art", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "S", "source": "Feed"}]
        }

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=True, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert result["feed_count"] == 1
        assert result["item_count"] == 1
        mock_analyze.assert_not_called()

    @patch("specola_engine.generate_docx")
    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_two_phase_analysis(self, mock_parse, mock_fetch, mock_analyze, mock_docx, tmp_path, capsys):
        """Phase 1 analyzes each category, Phase 2 synthesizes."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {
            "Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}],
            "Biz": [{"title": "Feed2", "xmlUrl": "https://y.com/rss", "htmlUrl": ""}],
        }
        mock_fetch.return_value = {
            "Tech": [{"title": "Art1", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "S1", "source": "Feed"}],
            "Biz": [{"title": "Art2", "link": "https://y.com", "published": "2026-04-05 08:00", "summary": "S2", "source": "Feed2"}],
        }

        # Claude returns analysis for each category call + synthesis call
        mock_analyze.side_effect = [
            "**Art1** — analysis of tech article. [Feed](https://x.com)",   # Phase 1: Tech
            "**Art2** — analysis of biz article. [Feed2](https://y.com)",   # Phase 1: Biz
            "## Da sapere oggi\n- Point 1\n- Point 2",                      # Phase 2: Synthesis
        ]
        mock_docx.return_value = str(output_dir / "Specola_2026-04-05_0900.docx")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert "output_path" in result

        # Claude called 3 times: 2 categories + 1 synthesis
        assert mock_analyze.call_count == 3
        mock_docx.assert_called_once()

    @patch("specola_engine.generate_docx")
    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_partial_category_failure(self, mock_parse, mock_fetch, mock_analyze, mock_docx, tmp_path, capsys):
        """If one category fails, others still work."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {
            "Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}],
        }
        mock_fetch.return_value = {
            "Tech": [{"title": "Art1", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "Summary", "source": "Feed"}],
        }

        # Phase 1 fails, Phase 2 (synthesis) also fails
        mock_analyze.side_effect = [None, None]
        mock_docx.return_value = str(output_dir / "Specola_2026-04-05_0900.docx")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"

    @patch("specola_engine.generate_fallback_docx")
    @patch("specola_engine.analyze", return_value=None)
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_total_failure_generates_fallback(self, mock_parse, mock_fetch, mock_analyze, mock_fallback, tmp_path, capsys):
        """If ALL Claude calls fail, generate fallback DOCX."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("Test profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "Feed", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {
            "Tech": [{"title": "Art", "link": "https://x.com", "published": "2026-04-05 09:00", "summary": "S", "source": "Feed"}]
        }
        mock_fallback.return_value = str(output_dir / "Specola_2026-04-05_0900.docx")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        mock_fallback.assert_called_once()


class TestOutputJson:
    def test_prints_json(self, capsys):
        _output_json({"status": "ok", "count": 5})
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["count"] == 5

    def test_unicode_preserved(self, capsys):
        _output_json({"message": "Ciao àèìòù"})
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["message"] == "Ciao àèìòù"


class TestAnalyzeCategories:
    @patch("specola_engine.analyze")
    def test_all_succeed(self, mock_claude, tmp_path):
        mock_claude.return_value = "  Analysis result  "
        items = {
            "Tech": [{"title": "Art", "source": "F", "summary": "S", "link": "", "published": ""}],
        }
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        results, count = _analyze_categories(items, "profile", "it", work_dir, "2026-04-05", None)
        assert count == 1
        assert "Tech" in results
        assert results["Tech"] == "Analysis result"

    @patch("specola_engine.analyze", return_value=None)
    def test_failure_uses_raw_items(self, mock_claude, tmp_path):
        items = {
            "Tech": [{"title": "Art", "source": "Feed", "summary": "Sum", "link": "", "published": ""}],
        }
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        results, count = _analyze_categories(items, "profile", "it", work_dir, "2026-04-05", None)
        assert count == 0
        assert "Art" in results["Tech"]
        assert "Feed" in results["Tech"]

    @patch("specola_engine.analyze")
    def test_mixed_success_failure(self, mock_claude, tmp_path):
        mock_claude.side_effect = ["  Analysis  ", None]
        items = {
            "Tech": [{"title": "A", "source": "F", "summary": "S", "link": "", "published": ""}],
            "Biz": [{"title": "B", "source": "G", "summary": "S", "link": "", "published": ""}],
        }
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        results, count = _analyze_categories(items, "profile", "it", work_dir, "2026-04-05", None)
        assert count == 1  # Only Tech succeeded
        assert len(results) == 2

    @patch("specola_engine.analyze")
    def test_writes_digest_files(self, mock_claude, tmp_path):
        mock_claude.return_value = "result"
        items = {
            "Tech": [{"title": "A", "source": "F", "summary": "S", "link": "", "published": ""}],
        }
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        _analyze_categories(items, "profile", "it", work_dir, "2026-04-05", None)
        digest_files = list(work_dir.glob("cat_*.md"))
        assert len(digest_files) == 1

    @patch("specola_engine.analyze")
    def test_passes_model(self, mock_claude, tmp_path):
        mock_claude.return_value = "result"
        items = {"Tech": [{"title": "A", "source": "F", "summary": "S", "link": "", "published": ""}]}
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        _analyze_categories(items, "profile", "it", work_dir, "2026-04-05", "opus")
        _, kwargs = mock_claude.call_args
        assert kwargs["model"] == "opus"


class TestSynthesize:
    @patch("specola_engine.analyze")
    def test_success(self, mock_claude, tmp_path):
        mock_claude.return_value = "## Da sapere oggi\n- Point 1"
        analyses = {"Tech": "tech analysis", "Biz": "biz analysis"}
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        result = _synthesize(analyses, "profile", "it", "2026-04-05", work_dir, "2026-04-05", None)
        assert "Da sapere oggi" in result

    @patch("specola_engine.analyze", return_value=None)
    def test_failure_returns_none(self, mock_claude, tmp_path):
        analyses = {"Tech": "analysis"}
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        result = _synthesize(analyses, "profile", "it", "2026-04-05", work_dir, "2026-04-05", None)
        assert result is None

    @patch("specola_engine.analyze")
    def test_writes_analyses_file(self, mock_claude, tmp_path):
        mock_claude.return_value = "result"
        analyses = {"Tech": "tech stuff", "Biz": "biz stuff"}
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        _synthesize(analyses, "profile", "it", "2026-04-05", work_dir, "2026-04-05", None)
        files = list(work_dir.glob("all_analyses_*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "## Tech" in content
        assert "## Biz" in content


class TestAssembleBriefing:
    def test_with_synthesis(self):
        synthesis = "## Da sapere oggi\n- Point 1"
        analyses = {"Tech": "tech analysis"}
        result = _assemble_briefing(synthesis, analyses, "2026-04-05")
        assert "Specola — Briefing del 2026-04-05" in result
        assert "Da sapere oggi" in result
        assert "---" in result
        assert "## Tech" in result
        assert "tech analysis" in result

    def test_without_synthesis(self):
        analyses = {"Tech": "tech analysis", "Biz": "biz analysis"}
        result = _assemble_briefing(None, analyses, "2026-04-05")
        assert "Specola — Briefing del 2026-04-05" in result
        assert "---" not in result
        assert "## Tech" in result
        assert "## Biz" in result

    def test_empty_analyses(self):
        result = _assemble_briefing(None, {}, "2026-04-05")
        assert "Specola" in result

    def test_synthesis_stripped(self):
        synthesis = "  \n## Da sapere oggi\n- Point\n  "
        result = _assemble_briefing(synthesis, {}, "2026-04-05")
        assert "## Da sapere oggi" in result


class TestRunEngineFormats:
    """Test different output formats."""

    @patch("specola_engine.generate_epub")
    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_epub_format(self, mock_parse, mock_fetch, mock_analyze, mock_epub, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"
        mock_epub.return_value = str(output_dir / "Specola_2026-04-05.epub")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False,
                   output_format="epub")

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        mock_epub.assert_called_once()

    @patch("specola_engine.generate_pdf")
    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_pdf_format(self, mock_parse, mock_fetch, mock_analyze, mock_pdf, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"
        mock_pdf.return_value = str(output_dir / "Specola_2026-04-05.pdf")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False,
                   output_format="pdf")

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        mock_pdf.assert_called_once()

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_html_format(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        """html format uses html_path as main_path."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False,
                   output_format="html")

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert result["output_path"].endswith(".html")


class TestRunEngineErrors:
    def test_opml_parse_error(self, tmp_path, capsys):
        """Invalid OPML produces error JSON."""
        opml = tmp_path / "bad.opml"
        opml.write_text("not xml")
        profile = tmp_path / "profile.md"
        profile.write_text("profile")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(tmp_path),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "error"
        assert "OPML" in result["message"]

    @patch("specola_engine.parse_opml", return_value={})
    def test_empty_opml(self, mock_parse, tmp_path, capsys):
        """Empty OPML (no feeds) produces error JSON."""
        run_engine(opml="x", profile="x", output_dir=str(tmp_path),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "error"
        assert "Nessun feed" in result["message"]

    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_zero_items(self, mock_parse, mock_fetch, tmp_path, capsys):
        """No items in time window produces error JSON."""
        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": []}

        profile = tmp_path / "profile.md"
        profile.write_text("profile")

        run_engine(opml="x", profile=str(profile), output_dir=str(tmp_path),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "error"
        assert "Nessun articolo" in result["message"]

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_verbose_mode(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        """Verbose mode doesn't crash (logging set to DEBUG)."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=True)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_output_includes_highlights(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        """Output JSON includes highlights array."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.side_effect = [
            "analysis text",
            "## Da sapere oggi\n- Highlight one\n- Highlight two",
        ]

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "highlights" in result
        assert isinstance(result["highlights"], list)

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_output_includes_html_path(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        """Output JSON includes html_path."""
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "html_path" in result
        assert result["html_path"].endswith(".html")

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_output_includes_portal_path(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "portal_path" in result


class TestRunEngineProviders:
    """Test that provider args are passed through the pipeline."""

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_openai_provider_passes_api_key(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model="gpt-4o", dry_run=False, verbose=False,
                   provider="openai", api_key="sk-test-key", endpoint=None)

        # analyze() should have been called with openai provider and api_key
        for call in mock_analyze.call_args_list:
            _, kwargs = call
            assert kwargs["provider"] == "openai"
            assert kwargs["api_key"] == "sk-test-key"

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_lmstudio_provider_passes_endpoint(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model="llama", dry_run=False, verbose=False,
                   provider="lmstudio", endpoint="http://gpu:8080/v1/chat/completions")

        for call in mock_analyze.call_args_list:
            _, kwargs = call
            assert kwargs["provider"] == "lmstudio"
            assert kwargs["endpoint"] == "http://gpu:8080/v1/chat/completions"

    @patch("specola_engine.analyze")
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_claude_provider_default(self, mock_parse, mock_fetch, mock_analyze, tmp_path, capsys):
        opml = tmp_path / "test.opml"
        opml.write_text('<opml version="2.0"><head/><body/></opml>')
        profile = tmp_path / "profile.md"
        profile.write_text("profile")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        mock_parse.return_value = {"Tech": [{"title": "F", "xmlUrl": "https://x.com/rss", "htmlUrl": ""}]}
        mock_fetch.return_value = {"Tech": [{"title": "A", "link": "", "published": "2026-04-05 09:00", "summary": "S", "source": "F"}]}
        mock_analyze.return_value = "analysis"

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        for call in mock_analyze.call_args_list:
            _, kwargs = call
            assert kwargs["provider"] == "claude"


class TestAnalyzeCategoriesProvider:
    """Test _analyze_categories passes provider args through."""

    @patch("specola_engine.analyze")
    def test_passes_provider_and_key(self, mock_analyze, tmp_path):
        mock_analyze.return_value = "result"
        items = {"Tech": [{"title": "A", "source": "F", "summary": "S", "link": "", "published": ""}]}
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        _analyze_categories(items, "profile", "it", work_dir, "2026-04-05", None,
                            provider="openai", api_key="sk-key", endpoint="https://custom.api")
        _, kwargs = mock_analyze.call_args
        assert kwargs["provider"] == "openai"
        assert kwargs["api_key"] == "sk-key"
        assert kwargs["endpoint"] == "https://custom.api"


class TestSynthesizeProvider:
    """Test _synthesize passes provider args through."""

    @patch("specola_engine.analyze")
    def test_passes_provider_and_endpoint(self, mock_analyze, tmp_path):
        mock_analyze.return_value = "## Da sapere"
        analyses = {"Tech": "analysis"}
        work_dir = tmp_path / ".work"
        work_dir.mkdir()
        _synthesize(analyses, "profile", "it", "2026-04-05", work_dir, "2026-04-05", None,
                    provider="lmstudio", endpoint="http://local:1234/v1/chat/completions")
        _, kwargs = mock_analyze.call_args
        assert kwargs["provider"] == "lmstudio"
        assert kwargs["endpoint"] == "http://local:1234/v1/chat/completions"
