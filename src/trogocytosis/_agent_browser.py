"""Backend router - runs agent-browser locally or over SSH."""

from __future__ import annotations

import os
import shutil
import subprocess


def _ssh_prefix() -> list[str]:
    """Return SSH prefix if TROGOCYTOSIS_HOST is set, else empty."""
    host = os.environ.get("TROGOCYTOSIS_HOST", "").strip()
    return ["ssh", host] if host else []


def _has_agent_browser() -> bool:
    return shutil.which("agent-browser") is not None


def run(args: list[str]) -> tuple[bool, str]:
    """Run agent-browser locally, or over SSH when TROGOCYTOSIS_HOST is set."""
    if _has_agent_browser() or _ssh_prefix():
        return _run_cli(args)
    return False, (
        "agent-browser not found. Install: npm i -g agent-browser\n"
        "Or set TROGOCYTOSIS_HOST for remote execution."
    )


def _run_cli(args: list[str]) -> tuple[bool, str]:
    """Run agent-browser CLI command."""
    try:
        res = subprocess.run(
            [*_ssh_prefix(), "agent-browser", *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.strip() if exc.stderr else str(exc)
    except subprocess.TimeoutExpired as exc:
        output = exc.stderr or exc.stdout or str(exc)
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return False, str(output).strip()
    except OSError as exc:
        return False, str(exc)
