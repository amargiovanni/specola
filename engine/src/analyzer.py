"""LLM analysis — supports Claude CLI, OpenAI Codex CLI, and LMStudio (local)."""
from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("specola.analyzer")


# ── Provider registry ──────────────────────────────────────────────────

def analyze(
    digest_path: Path,
    prompt: str,
    provider: str = "claude",
    model: str | None = None,
    timeout: int = 600,
    endpoint: str | None = None,
) -> str | None:
    """Route analysis to the configured LLM provider.

    Args:
        digest_path: Path to the markdown digest file.
        prompt: System/user prompt for the LLM.
        provider: One of "claude", "codex", "lmstudio".
        model: Model name (provider-specific).
        timeout: Timeout in seconds.
        endpoint: Custom endpoint URL (LMStudio only).

    Returns:
        Markdown analysis string, or None on failure.
    """
    if provider == "codex":
        return _analyze_codex(digest_path, prompt, model=model, timeout=timeout)
    elif provider == "lmstudio":
        return _analyze_lmstudio(digest_path, prompt, model=model, timeout=timeout,
                                 endpoint=endpoint)
    else:
        return _analyze_claude(digest_path, prompt, model=model, timeout=timeout)


# ── Claude CLI ─────────────────────────────────────────────────────────

def _analyze_claude(
    digest_path: Path,
    prompt: str,
    model: str | None = None,
    timeout: int = 600,
) -> str | None:
    """Invoke Claude CLI with prompt and digest as stdin."""
    cmd = ["claude", "-p", prompt]
    if model:
        cmd.extend(["--model", model])

    try:
        with open(digest_path, "r") as f:
            result = subprocess.run(
                cmd, stdin=f, capture_output=True, text=True, timeout=timeout
            )
    except FileNotFoundError:
        logger.error("Claude CLI not found in PATH")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Claude CLI timed out after %d seconds", timeout)
        return None

    if result.returncode != 0:
        logger.error("Claude CLI failed (exit %d): %s", result.returncode, result.stderr)
        return None

    return result.stdout


# ── OpenAI Codex CLI ───────────────────────────────────────────────────

def _analyze_codex(
    digest_path: Path,
    prompt: str,
    model: str | None = None,
    timeout: int = 600,
) -> str | None:
    """Invoke OpenAI Codex CLI (codex exec) with prompt and digest as stdin.

    Codex CLI uses OPENAI_API_KEY from environment (set by the user).
    Progress goes to stderr, final output to stdout.
    """
    cmd = ["codex", "exec", prompt]
    if model:
        cmd.extend(["--model", model])

    try:
        with open(digest_path, "r") as f:
            result = subprocess.run(
                cmd, stdin=f, capture_output=True, text=True, timeout=timeout
            )
    except FileNotFoundError:
        logger.error("Codex CLI not found in PATH — install with: npm install -g @openai/codex")
        return None
    except subprocess.TimeoutExpired:
        logger.error("Codex CLI timed out after %d seconds", timeout)
        return None

    if result.returncode != 0:
        logger.error("Codex CLI failed (exit %d): %s", result.returncode, result.stderr)
        return None

    return result.stdout


# ── LMStudio (local, OpenAI-compatible) ────────────────────────────────

_LMSTUDIO_DEFAULT_ENDPOINT = "http://localhost:1234/v1/chat/completions"
_LMSTUDIO_DEFAULT_MODEL = "local-model"


def _analyze_lmstudio(
    digest_path: Path,
    prompt: str,
    model: str | None = None,
    timeout: int = 600,
    endpoint: str | None = None,
) -> str | None:
    """Call LMStudio local server (OpenAI-compatible API, no auth)."""
    import urllib.request
    import urllib.error

    url = endpoint or _LMSTUDIO_DEFAULT_ENDPOINT
    chosen_model = model or _LMSTUDIO_DEFAULT_MODEL

    try:
        digest_text = digest_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("Cannot read digest file: %s", e)
        return None

    payload = json.dumps({
        "model": chosen_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": digest_text},
        ],
        "temperature": 0.3,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        logger.error("LMStudio API HTTP error %d: %s", e.code, e.reason)
        return None
    except urllib.error.URLError as e:
        logger.error("LMStudio connection error: %s — Is LMStudio running?", e.reason)
        return None
    except TimeoutError:
        logger.error("LMStudio timed out after %d seconds", timeout)
        return None
    except (json.JSONDecodeError, OSError) as e:
        logger.error("LMStudio error: %s", e)
        return None

    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        logger.error("LMStudio unexpected response format: %s", body)
        return None


# ── Backward compatibility ─────────────────────────────────────────────

def analyze_with_claude(
    digest_path: Path,
    prompt: str,
    model: str | None = None,
    timeout: int = 600,
) -> str | None:
    """Legacy wrapper — delegates to analyze() with provider='claude'."""
    return analyze(digest_path, prompt, provider="claude", model=model, timeout=timeout)
