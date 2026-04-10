"""Cookie extraction from host browser and injection into agent-browser.

Escalation chain: cookie bridge → porta → pycookiecheat → error with login hint.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
from typing import Any

from trogocytosis import _agent_browser

COOKIE_BRIDGE_URL = os.environ.get("COOKIE_BRIDGE_URL", "http://127.0.0.1:7743")


def _extract_via_bridge(domain: str) -> dict[str, str]:
    """Extract cookies via cookie-bridge HTTP service (no keychain needed)."""
    url = f"{COOKIE_BRIDGE_URL}/cookies?domain={domain}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        cookies = json.loads(resp.read())
        if not cookies:
            raise ValueError(f"Cookie bridge returned empty for {domain}")
        return cookies


def _extract_via_porta(domain: str) -> dict[str, str]:
    """Extract cookies via porta CLI (Rust binary, bridges Chrome cookies)."""
    if not shutil.which("porta"):
        raise FileNotFoundError("porta not installed")
    result = subprocess.run(
        ["porta", "inject", "--domain", domain, "--json"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"porta failed: {result.stderr.strip()}")
    cookies = json.loads(result.stdout)
    if not cookies:
        raise ValueError(f"porta returned empty for {domain}")
    return cookies


def _extract_via_pycookiecheat(domain: str) -> dict[str, str]:
    """Extract cookies from host browser using pycookiecheat (needs keychain)."""
    from pycookiecheat import chrome_cookies

    url = f"https://{domain}/"
    cookies = chrome_cookies(url)
    if not cookies:
        raise ValueError(f"pycookiecheat returned empty for {domain}")
    return cookies


def _extract_cookies(domain: str) -> dict[str, str]:
    """Extract cookies — escalates: bridge → porta → pycookiecheat."""
    errors: list[str] = []
    for name, extractor in [
        ("cookie-bridge", lambda: _extract_via_bridge(domain)),
        ("porta", lambda: _extract_via_porta(domain)),
        ("pycookiecheat", lambda: _extract_via_pycookiecheat(domain)),
    ]:
        try:
            return extractor()
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    raise RuntimeError(
        f"All cookie extraction methods failed for {domain}:\n"
        + "\n".join(f"  - {err}" for err in errors)
        + f"\nRun: trogocytosis login {domain}"
    )


def _inject_into_browser(domain: str, extracted: dict[str, str]) -> int:
    """Inject extracted cookies into agent-browser."""
    url = f"https://{domain}/"
    _agent_browser.run(["open", url])
    for cookie_name, value in extracted.items():
        _agent_browser.run([
            "cookies", "set", cookie_name, value,
            "--url", url,
            "--domain", f".{domain}",
            "--path", "/",
            "--httpOnly",
            "--secure",
        ])
    return len(extracted)


def inject(domain: str, browser: str = "chrome") -> dict[str, Any]:
    """Extract cookies and inject into agent-browser. Full escalation chain."""
    extracted = _extract_cookies(domain)
    count = _inject_into_browser(domain, extracted)
    return {"count": count, "domain": domain}


def login_headed(domain: str, login_url: str | None = None) -> dict[str, Any]:
    """Open headed browser for manual login, then persist session."""
    if login_url is None:
        login_url = f"https://{domain}/login"

    # Close existing session, open headed
    _agent_browser.run(["close"])
    import time
    time.sleep(1)

    # Try 1Password for creds
    creds = _op_lookup(domain)

    ok, _ = _agent_browser.run(["--headed", "open", login_url])
    if not ok:
        return {"success": False, "error": "Failed to open headed browser"}

    if creds:
        time.sleep(2)
        _agent_browser.run(["fill", "#username, [name=username], [name=email], [type=email]", creds["username"]])
        _agent_browser.run(["fill", "#password, [name=password], [type=password]", creds["password"]])
        _agent_browser.run(["click", "[type=submit], button[data-litms]"])
        time.sleep(3)

    _, url = _agent_browser.run(["get", "url"])
    authenticated = "login" not in url.lower() and "auth" not in url.lower()
    return {"success": authenticated, "url": url, "auto_filled": creds is not None}


def _op_lookup(domain: str) -> dict[str, str] | None:
    """Look up credentials from 1Password Agents vault by domain.

    Matches items whose URL contains the domain. When multiple items match,
    picks the one whose URL is the closest match (shortest href containing
    the domain — avoids picking a generic 'google.com' item for 'linkedin.com').
    """
    if not shutil.which("op"):
        return None
    try:
        result = subprocess.run(
            ["op", "item", "list", "--vault", "Agents", "--format=json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None
        items = json.loads(result.stdout)
        best_match: tuple[int, str] | None = None  # (url_length, item_id)
        for item in items:
            for url_entry in item.get("urls", []):
                href = url_entry.get("href", "")
                if domain in href:
                    url_len = len(href)
                    if best_match is None or url_len < best_match[0]:
                        best_match = (url_len, item["id"])
        if best_match is None:
            return None
        item_id = best_match[1]
        username = subprocess.run(
            ["op", "item", "get", item_id, "--vault", "Agents", "--fields", "username", "--reveal"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        password = subprocess.run(
            ["op", "item", "get", item_id, "--vault", "Agents", "--fields", "password", "--reveal"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        if username and password:
            return {"username": username, "password": password}
    except Exception:
        pass
    return None
