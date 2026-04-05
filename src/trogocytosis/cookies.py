"""Cookie extraction from host browser and injection into agent-browser."""

from __future__ import annotations

from typing import Any

from trogocytosis import _agent_browser


def _extract_cookies(domain: str, browser: str = "chrome") -> dict[str, str]:
    """Extract cookies from host browser using pycookiecheat."""
    from pycookiecheat import chrome_cookies

    url = f"https://{domain}/"
    return chrome_cookies(url)


def inject(domain: str, browser: str = "chrome") -> dict[str, Any]:
    """Extract cookies from host browser and inject into agent-browser."""
    cookies = _extract_cookies(domain, browser)
    url = f"https://{domain}/"
    _agent_browser.run(["open", url])
    for name, value in cookies.items():
        _agent_browser.run([
            "cookies", "set", name, value,
            "--url", url,
            "--domain", f".{domain}",
            "--path", "/",
            "--httpOnly",
            "--secure",
        ])
    return {"count": len(cookies), "domain": domain}
