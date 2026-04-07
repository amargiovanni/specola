import json
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from src.analyzer import (
    analyze,
    analyze_with_claude,
    _analyze_claude,
    _analyze_codex,
    _analyze_lmstudio,
    _LMSTUDIO_DEFAULT_ENDPOINT,
    _LMSTUDIO_DEFAULT_MODEL,
)


# ═══════════════════════════════════════════════════════════════════════
# analyze() — Router
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyzeRouter:
    def test_routes_to_claude_by_default(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_claude", return_value="result") as m:
            result = analyze(digest, "prompt")
            m.assert_called_once()
            assert result == "result"

    def test_routes_to_codex(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_codex", return_value="codex result") as m:
            result = analyze(digest, "prompt", provider="codex")
            m.assert_called_once()
            assert result == "codex result"

    def test_routes_to_lmstudio(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_lmstudio", return_value="lm result") as m:
            result = analyze(digest, "prompt", provider="lmstudio")
            m.assert_called_once()
            assert result == "lm result"

    def test_unknown_provider_falls_to_claude(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_claude", return_value="claude") as m:
            analyze(digest, "prompt", provider="unknown")
            m.assert_called_once()

    def test_passes_model_to_claude(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_claude", return_value="r") as m:
            analyze(digest, "p", provider="claude", model="opus")
            _, kwargs = m.call_args
            assert kwargs["model"] == "opus"

    def test_passes_model_to_codex(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_codex", return_value="r") as m:
            analyze(digest, "p", provider="codex", model="o3-pro")
            _, kwargs = m.call_args
            assert kwargs["model"] == "o3-pro"

    def test_passes_endpoint_to_lmstudio(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_lmstudio", return_value="r") as m:
            analyze(digest, "p", provider="lmstudio", endpoint="http://custom:5000/v1")
            _, kwargs = m.call_args
            assert kwargs["endpoint"] == "http://custom:5000/v1"

    def test_passes_timeout(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer._analyze_claude", return_value="r") as m:
            analyze(digest, "p", timeout=42)
            _, kwargs = m.call_args
            assert kwargs["timeout"] == 42

    def test_no_api_key_param(self):
        """analyze() should not accept api_key parameter anymore."""
        import inspect
        sig = inspect.signature(analyze)
        assert "api_key" not in sig.parameters


# ═══════════════════════════════════════════════════════════════════════
# _analyze_claude() — Claude CLI
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyzeClaude:
    """Tests for _analyze_claude which delegates to _posix_spawn_claude."""

    def test_success(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("# Test digest\n\nSome content")
        expected = "# Briefing\n\n## Da sapere oggi\n- Point 1"
        with patch("src.analyzer._posix_spawn_claude", return_value=expected) as mock_spawn:
            result = _analyze_claude(digest, "prompt text")
            assert result == expected
            mock_spawn.assert_called_once()
            cmd = mock_spawn.call_args[0][0]
            assert cmd == ["claude", "-p", "prompt text"]

    def test_with_model(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer._posix_spawn_claude", return_value="output") as mock_spawn:
            _analyze_claude(digest, "prompt", model="opus")
            cmd = mock_spawn.call_args[0][0]
            assert "--model" in cmd
            assert "opus" in cmd

    def test_failure_returns_none(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer._posix_spawn_claude", return_value=None):
            result = _analyze_claude(digest, "prompt")
            assert result is None

    def test_timeout_returns_none(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer._posix_spawn_claude", side_effect=TimeoutError()):
            result = _analyze_claude(digest, "prompt", timeout=300)
            assert result is None

    def test_file_not_found_returns_none(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        with patch("src.analyzer._posix_spawn_claude", side_effect=FileNotFoundError("claude not found")):
            result = _analyze_claude(missing, "prompt")
            assert result is None

    def test_no_model_flag_when_none(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer._posix_spawn_claude", return_value="output") as mock_spawn:
            _analyze_claude(digest, "prompt", model=None)
            cmd = mock_spawn.call_args[0][0]
            assert "--model" not in cmd

    def test_returns_raw_output(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer._posix_spawn_claude", return_value="  output with spaces  \n"):
            result = _analyze_claude(digest, "prompt")
            assert result == "  output with spaces  \n"

    def test_prompt_passed_as_p_flag(self, tmp_path):
        digest = tmp_path / "digest.md"
        digest.write_text("content")
        with patch("src.analyzer._posix_spawn_claude", return_value="out") as mock_spawn:
            _analyze_claude(digest, "my specific prompt")
            cmd = mock_spawn.call_args[0][0]
            assert cmd[1] == "-p"
            assert cmd[2] == "my specific prompt"


# ═══════════════════════════════════════════════════════════════════════
# _analyze_codex() — OpenAI Codex CLI
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyzeCodex:
    def test_success(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("digest content")
        mock_result = MagicMock(returncode=0, stdout="Codex analysis result")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            result = _analyze_codex(digest, "prompt text")
            assert result == "Codex analysis result"
            mock_run.assert_called_once()

    def test_uses_codex_exec_command(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "my prompt")
            cmd = mock_run.call_args[0][0]
            assert cmd[0] == "codex"
            assert cmd[1] == "exec"
            assert cmd[2] == "my prompt"

    def test_with_model(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "prompt", model="o3-pro")
            cmd = mock_run.call_args[0][0]
            assert "--model" in cmd
            assert "o3-pro" in cmd

    def test_no_model_flag_when_none(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "prompt", model=None)
            cmd = mock_run.call_args[0][0]
            assert "--model" not in cmd

    def test_stdin_is_digest_file(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "prompt")
            assert mock_run.call_args[1]["stdin"] is not None

    def test_capture_output(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "prompt")
            assert mock_run.call_args[1]["capture_output"] is True
            assert mock_run.call_args[1]["text"] is True

    def test_file_not_found_returns_none(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer.subprocess.run", side_effect=FileNotFoundError("codex not found")):
            result = _analyze_codex(digest, "prompt")
            assert result is None

    def test_timeout_returns_none(self, tmp_path):
        import subprocess
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer.subprocess.run", side_effect=subprocess.TimeoutExpired("codex", 300)):
            result = _analyze_codex(digest, "prompt", timeout=300)
            assert result is None

    def test_nonzero_exit_code_returns_none(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        for code in [1, 2, 127]:
            mock_result = MagicMock(returncode=code, stdout="", stderr="err")
            with patch("src.analyzer.subprocess.run", return_value=mock_result):
                assert _analyze_codex(digest, "prompt") is None

    def test_default_timeout(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "prompt")
            assert mock_run.call_args[1]["timeout"] == 600

    def test_custom_timeout(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="ok")
        with patch("src.analyzer.subprocess.run", return_value=mock_result) as mock_run:
            _analyze_codex(digest, "prompt", timeout=120)
            assert mock_run.call_args[1]["timeout"] == 120

    def test_returns_raw_stdout(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        mock_result = MagicMock(returncode=0, stdout="  output\n")
        with patch("src.analyzer.subprocess.run", return_value=mock_result):
            assert _analyze_codex(digest, "p") == "  output\n"


# ═══════════════════════════════════════════════════════════════════════
# _analyze_lmstudio() — LMStudio local
# ═══════════════════════════════════════════════════════════════════════

def _mock_urlopen(response_body):
    """Create a mock for urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_body).encode("utf-8")
    mock_resp.__enter__ = Mock(return_value=mock_resp)
    mock_resp.__exit__ = Mock(return_value=False)
    return mock_resp


class TestAnalyzeLmstudio:
    def test_success(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("digest content")
        resp = {"choices": [{"message": {"content": "Local analysis"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)):
            result = _analyze_lmstudio(digest, "prompt")
            assert result == "Local analysis"

    def test_no_auth_header(self, tmp_path):
        """LMStudio should NOT send Authorization header."""
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "prompt")
            req = m.call_args[0][0]
            assert "Authorization" not in req.headers

    def test_uses_default_endpoint(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "prompt")
            req = m.call_args[0][0]
            assert req.full_url == _LMSTUDIO_DEFAULT_ENDPOINT

    def test_custom_endpoint(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "prompt", endpoint="http://gpu-server:8080/v1/chat/completions")
            req = m.call_args[0][0]
            assert req.full_url == "http://gpu-server:8080/v1/chat/completions"

    def test_uses_default_model(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "prompt")
            body = json.loads(m.call_args[0][0].data)
            assert body["model"] == _LMSTUDIO_DEFAULT_MODEL

    def test_custom_model(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "prompt", model="llama-3.3-70b")
            body = json.loads(m.call_args[0][0].data)
            assert body["model"] == "llama-3.3-70b"

    def test_connection_refused_returns_none(self, tmp_path):
        import urllib.error
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("urllib.request.urlopen",
                    side_effect=urllib.error.URLError("Connection refused")):
            result = _analyze_lmstudio(digest, "p")
            assert result is None

    def test_http_error_returns_none(self, tmp_path):
        import urllib.error
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("urllib.request.urlopen",
                    side_effect=urllib.error.HTTPError("url", 500, "server error", {}, None)):
            result = _analyze_lmstudio(digest, "p")
            assert result is None

    def test_timeout_returns_none(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("urllib.request.urlopen", side_effect=TimeoutError):
            result = _analyze_lmstudio(digest, "p", timeout=5)
            assert result is None

    def test_malformed_response_returns_none(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"error": "something"}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)):
            result = _analyze_lmstudio(digest, "p")
            assert result is None

    def test_empty_choices_returns_none(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": []}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)):
            result = _analyze_lmstudio(digest, "p")
            assert result is None

    def test_missing_digest_file_returns_none(self, tmp_path):
        missing = tmp_path / "nonexistent.md"
        result = _analyze_lmstudio(missing, "p")
        assert result is None

    def test_sends_prompt_as_system_message(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("the digest")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "system prompt", model="llama")
            body = json.loads(m.call_args[0][0].data)
            assert body["messages"][0]["role"] == "system"
            assert body["messages"][0]["content"] == "system prompt"
            assert body["messages"][1]["role"] == "user"
            assert body["messages"][1]["content"] == "the digest"

    def test_temperature_is_low(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        resp = {"choices": [{"message": {"content": "ok"}}]}
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(resp)) as m:
            _analyze_lmstudio(digest, "p")
            body = json.loads(m.call_args[0][0].data)
            assert body["temperature"] == 0.3


# ═══════════════════════════════════════════════════════════════════════
# analyze_with_claude() — Backward compatibility
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyzeWithClaudeLegacy:
    def test_delegates_to_analyze(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer.analyze", return_value="result") as m:
            result = analyze_with_claude(digest, "prompt", model="opus", timeout=120)
            m.assert_called_once_with(digest, "prompt", provider="claude", model="opus", timeout=120)
            assert result == "result"

    def test_default_params(self, tmp_path):
        digest = tmp_path / "d.md"
        digest.write_text("content")
        with patch("src.analyzer.analyze", return_value="r") as m:
            analyze_with_claude(digest, "prompt")
            m.assert_called_once_with(digest, "prompt", provider="claude", model=None, timeout=600)
