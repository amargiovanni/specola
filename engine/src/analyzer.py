"""Claude Code CLI invocation."""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger("specola.analyzer")


def analyze_with_claude(
    digest_path: Path,
    prompt: str,
    model: str | None = None,
    timeout: int = 600,
) -> str | None:
    """Invoke Claude CLI with prompt and digest as stdin. Returns markdown or None."""
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
