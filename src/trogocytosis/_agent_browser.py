"""Low-level subprocess wrapper for agent-browser CLI."""

from __future__ import annotations

import shutil
import subprocess


def _binary() -> str:
    return shutil.which("agent-browser") or "agent-browser"


def run(args: list[str]) -> tuple[bool, str]:
    """Run agent-browser CLI command. Returns (success, stdout)."""
    try:
        res = subprocess.run(
            [_binary(), *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.strip() if exc.stderr else str(exc)
    except FileNotFoundError:
        return False, "agent-browser not found. Install with: npm i -g agent-browser"
