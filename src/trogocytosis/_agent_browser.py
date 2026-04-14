"""Backend router — uses agent-browser CLI, supports SSH transport."""

from __future__ import annotations

import os
import shutil


def _ssh_prefix() -> list[str]:
    """Return SSH prefix if TROGOCYTOSIS_HOST is set, else empty."""
    host = os.environ.get("TROGOCYTOSIS_HOST")
    if host:
        return ["ssh", host]
    return []


def _has_agent_browser() -> bool:
    return shutil.which("agent-browser") is not None


def run(args: list[str]) -> tuple[bool, str]:
    """Run browser command via agent-browser CLI (locally or SSH)."""
    if not _has_agent_browser() and not os.environ.get("TROGOCYTOSIS_HOST"):
        return False, (
            "agent-browser not found. Install: npm i -g agent-browser\n"
            "Or set TROGOCYTOSIS_HOST for remote execution."
        )
    return _run_cli(args)


def _run_cli(args: list[str]) -> tuple[bool, str]:
    """Run agent-browser CLI command, locally or via SSH."""
    import subprocess
    prefix = _ssh_prefix()
    try:
        res = subprocess.run(
            [*prefix, "agent-browser", *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.strip() if exc.stderr else str(exc)
