"""Cookie extraction from host browser and injection into agent-browser."""

from __future__ import annotations

from typing import Any

from trogocytosis import _agent_browser


def _extract_cookies(domain: str, bridge_host: str = "mac:7743") -> dict[str, str]:
    """Extract cookies via remote bridge, falling back to pycookiecheat."""
    import json
    import urllib.request

    # Tier 1: Remote cookie bridge (HTTP)
    try:
        url = f"http://{bridge_host}/cookies?domain={domain}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            cookies = json.loads(resp.read().decode("utf-8"))
        if cookies and "error" not in cookies:
            return cookies
    except Exception:
        pass

    # Tier 2: Local pycookiecheat
    try:
        from pycookiecheat import chrome_cookies

        return chrome_cookies(f"https://{domain}/")
    except Exception:
        pass

    return {}


def inject(domain: str, bridge_host: str = "mac:7743") -> dict[str, Any]:
    """Extract cookies from host browser and inject into agent-browser."""
    domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    cookies = _extract_cookies(domain, bridge_host)
    if not cookies:
        return {
            "success": False,
            "message": f"No cookies for {domain}",
            "count": 0,
            "failures": [],
        }
    url = f"https://{domain}"
    injected = 0
    failures = []
    for name, value in cookies.items():
        cmd = [
            "cookies", "set", name, str(value),
            "--url", url,
            "--path", "/",
            "--httpOnly",
            "--secure",
        ]
        if not name.startswith("__Host-"):
            cmd.extend(["--domain", f".{domain}"])
        ok, _ = _agent_browser.run(cmd)
        if ok:
            injected += 1
        else:
            failures.append(name)
    return {
        "success": injected > 0,
        "message": f"Injected {injected}/{len(cookies)} cookies for {domain}",
        "count": injected,
        "failures": failures,
    }
