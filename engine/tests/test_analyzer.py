from pathlib import Path
from unittest.mock import patch, MagicMock
from src.analyzer import analyze_with_claude


class TestAnalyzeWithClaude:
    def test_success(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("# Test digest\n\nSome content")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "# Briefing\n\n## Da sapere oggi\n- Point 1"
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            result = analyze_with_claude(digest, "prompt text")
            assert result == mock_result.stdout
            mock_run.assert_called_once()
            args = mock_run.call_args
            assert args[0][0] == ["claude", "-p", "prompt text"]
            assert args[1]["text"] is True
            assert args[1]["capture_output"] is True

    def test_with_model(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="output")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            analyze_with_claude(digest, "prompt", model="opus")
            cmd = mock_run.call_args[0][0]
            assert "--model" in cmd
            assert "opus" in cmd

    def test_failure_returns_none(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=1, stdout="", stderr="error")
        with patch("src.analyzer.subprocess.run", return_value=mock_result):
            result = analyze_with_claude(digest, "prompt")
            assert result is None

    def test_timeout_returns_none(self, tmp_path):
        import subprocess
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer.subprocess.run", side_effect=subprocess.TimeoutExpired("claude", 300)):
            result = analyze_with_claude(digest, "prompt", timeout=300)
            assert result is None

    def test_file_not_found_returns_none(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        with patch("src.analyzer.subprocess.run", side_effect=FileNotFoundError("claude not found")):
            result = analyze_with_claude(missing, "prompt")
            assert result is None
