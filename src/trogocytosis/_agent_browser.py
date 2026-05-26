"""Backend router - runs agent-browser locally or over SSH."""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess

_DEFAULT_SESSION = "trogocytosis"
_DEFAULT_TIMEOUT = 45

_HEADLESS_ENV_KEYS = (
    "AGENT_BROWSER_HEADED",
    "AGENT_BROWSER_PROFILE",
    "AGENT_BROWSER_EXTENSIONS",
)


def _is_explicit_headed(args: list[str]) -> bool:
    """True when args explicitly request a headed browser."""
    return any(a == "--headed" or a.startswith("--headed=") for a in args)


def _ssh_prefix() -> list[str]:
    """Return SSH prefix if TROGOCYTOSIS_HOST is set, else empty."""
    host = os.environ.get("TROGOCYTOSIS_HOST", "").strip()
    return ["ssh", host] if host else []


def _has_agent_browser() -> bool:
    return shutil.which("agent-browser") is not None


def _parse_timeout() -> int:
    """Parse TROGOCYTOSIS_TIMEOUT; invalid or non-positive falls back to default."""
    raw = os.environ.get("TROGOCYTOSIS_TIMEOUT", "").strip()
    if not raw:
        return _DEFAULT_TIMEOUT
    try:
        val = int(raw)
        return val if val > 0 else _DEFAULT_TIMEOUT
    except (ValueError, TypeError):
        return _DEFAULT_TIMEOUT


def _session_name() -> str:
    """Return session name from TROGOCYTOSIS_SESSION or default."""
    return os.environ.get("TROGOCYTOSIS_SESSION", "").strip() or _DEFAULT_SESSION



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
    session = _session_name()
    timeout = _parse_timeout()
    prefix = _ssh_prefix()
    explicit_headed = _is_explicit_headed(args)
    cmd = [*prefix, "agent-browser", "--session", session]
    if not explicit_headed:
        cmd.extend(["--headed", "false"])
    cmd.extend(args)

    env = dict(os.environ)
    if not explicit_headed:
        for key in _HEADLESS_ENV_KEYS:
            env.pop(key, None)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            start_new_session=True,
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        if proc.returncode == 0:
            return True, stdout.strip()
        return False, (stderr.strip() if stderr else f"exit code {proc.returncode}")
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            proc.wait(timeout=5)
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                [*prefix, "agent-browser", "--session", session, "close"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        return False, f"agent-browser timed out after {timeout}s"
    except OSError as exc:
        return False, str(exc)
