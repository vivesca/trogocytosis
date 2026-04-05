"""Core browser API — navigate, snapshot, click, fill, eval, screenshot."""

from __future__ import annotations

import os
from typing import Any

from trogocytosis import _agent_browser


def navigate(url: str) -> dict[str, Any]:
    """Navigate to URL. Returns {title, url}."""
    _agent_browser.run(["open", url])
    _, title = _agent_browser.run(["get", "title"])
    _, page_url = _agent_browser.run(["get", "url"])
    return {"title": title, "url": page_url}


def snapshot() -> dict[str, str]:
    """Capture accessibility tree of current page."""
    _, tree = _agent_browser.run(["snapshot"])
    return {"snapshot": tree}


def screenshot(path: str = "/tmp/screenshot.png", device: str = "") -> dict[str, Any]:
    """Capture PNG screenshot."""
    if device:
        _agent_browser.run(["set", "device", device])
    _agent_browser.run(["screenshot", path])
    size = os.path.getsize(path) if os.path.exists(path) else 0
    return {"path": path, "size_bytes": size}


def click(selector: str) -> dict[str, bool]:
    """Click element by CSS selector."""
    ok, _ = _agent_browser.run(["click", selector])
    return {"success": ok}


def fill(selector: str, value: str) -> dict[str, bool]:
    """Fill form field — clears first, then types value."""
    _agent_browser.run(["fill", selector, ""])
    ok, _ = _agent_browser.run(["fill", selector, value])
    return {"success": ok}


def evaluate(js: str) -> dict[str, str]:
    """Evaluate JavaScript in page context."""
    _, result = _agent_browser.run(["eval", js])
    return {"result": result}


def check_auth() -> dict[str, Any]:
    """Check if current page requires authentication."""
    _, url = _agent_browser.run(["get", "url"])
    auth_keywords = ["login", "signin", "sign-in", "auth", "sso"]
    authenticated = not any(kw in url.lower() for kw in auth_keywords)
    return {"authenticated": authenticated, "url": url}
