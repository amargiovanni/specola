import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from specola_engine import main, run_engine


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
    def test_full_run_success(self, mock_parse, mock_fetch, mock_analyze, mock_docx, tmp_path, capsys):
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
        mock_analyze.return_value = "# Briefing\n\n## Da sapere oggi\n- Point 1"
        mock_docx.return_value = str(output_dir / "Specola_2026-04-05.docx")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        assert "output_path" in result
        mock_analyze.assert_called_once()
        mock_docx.assert_called_once()

    @patch("specola_engine.generate_fallback_docx")
    @patch("specola_engine.analyze_with_claude", return_value=None)
    @patch("specola_engine.fetch_feeds")
    @patch("specola_engine.parse_opml")
    def test_claude_failure_generates_fallback(self, mock_parse, mock_fetch, mock_analyze, mock_fallback, tmp_path, capsys):
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
        mock_fallback.return_value = str(output_dir / "Specola_2026-04-05.docx")

        run_engine(opml=str(opml), profile=str(profile), output_dir=str(output_dir),
                   hours=24, language="it", max_items=30, model=None, dry_run=False, verbose=False)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result["status"] == "ok"
        mock_fallback.assert_called_once()
