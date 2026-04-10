"""Cookie extraction from host browser and injection into agent-browser."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from trogocytosis import _agent_browser

COOKIE_BRIDGE_URL = os.environ.get("COOKIE_BRIDGE_URL", "http://127.0.0.1:7743")


def _extract_via_bridge(domain: str) -> dict[str, str]:
    """Extract cookies via cookie-bridge HTTP service (no keychain needed)."""
    url = f"{COOKIE_BRIDGE_URL}/cookies?domain={domain}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def _extract_via_pycookiecheat(domain: str) -> dict[str, str]:
    """Extract cookies from host browser using pycookiecheat (needs keychain)."""
    from pycookiecheat import chrome_cookies

    url = f"https://{domain}/"
    return chrome_cookies(url)


def _extract_cookies(domain: str, browser: str = "chrome") -> dict[str, str]:
    """Extract cookies — tries cookie bridge first, falls back to pycookiecheat."""
    try:
        return _extract_via_bridge(domain)
    except Exception:
        pass
    return _extract_via_pycookiecheat(domain)


def inject(domain: str, browser: str = "chrome") -> dict[str, Any]:
    """Extract cookies from host browser and inject into agent-browser."""
    extracted = _extract_cookies(domain, browser)
    url = f"https://{domain}/"
    _agent_browser.run(["open", url])
    for name, value in extracted.items():
        _agent_browser.run([
            "cookies", "set", name, value,
            "--url", url,
            "--domain", f".{domain}",
            "--path", "/",
            "--httpOnly",
            "--secure",
        ])
    return {"count": len(extracted), "domain": domain}
