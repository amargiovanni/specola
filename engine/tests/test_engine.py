import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, str(Path(__file__).parent.parent))

from specola_engine import run_engine


class TestRunEngine:
    @patch("specola_engine.analyze_with_claude")
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
    @patch("specola_engine.analyze_with_claude")
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
    @patch("specola_engine.analyze_with_claude")
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
    @patch("specola_engine.analyze_with_claude", return_value=None)
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
