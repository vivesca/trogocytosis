"""Backend router — uses agent-browser CLI if available, falls back to Playwright."""

from __future__ import annotations

import importlib.util
import shutil


def _has_agent_browser() -> bool:
    return shutil.which("agent-browser") is not None


def _has_playwright() -> bool:
    return importlib.util.find_spec("playwright") is not None


def run(args: list[str]) -> tuple[bool, str]:
    """Run browser command. Prefers agent-browser CLI, falls back to Playwright."""
    if _has_agent_browser():
        return _run_cli(args)
    if _has_playwright():
        from trogocytosis._playwright import run as pw_run
        return pw_run(args)
    return False, (
        "No browser backend found. Install one of:\n"
        "  npm i -g agent-browser    (recommended)\n"
        "  pip install playwright     (fallback)"
    )


def _run_cli(args: list[str]) -> tuple[bool, str]:
    """Run agent-browser CLI command."""
    import subprocess

    try:
        res = subprocess.run(
            ["agent-browser", *args],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.strip() if exc.stderr else str(exc)
