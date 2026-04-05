"""Playwright backend — fallback when agent-browser CLI is not installed."""

from __future__ import annotations

import os
from typing import Any

_browser = None
_context = None
_page = None


def _ensure_browser() -> Any:
    """Lazy-launch a persistent Playwright Chromium context."""
    global _browser, _context, _page
    if _page is not None:
        return _page

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    profile_dir = os.environ.get(
        "TROGOCYTOSIS_PROFILE",
        os.path.expanduser("~/.trogocytosis-profile"),
    )
    _browser = pw.chromium.launch_persistent_context(
        profile_dir,
        headless=True,
        args=["--disable-blink-features=AutomationControlled"],
    )
    _page = _browser.pages[0] if _browser.pages else _browser.new_page()
    return _page


def run(args: list[str]) -> tuple[bool, str]:
    """Execute browser commands using Playwright, matching agent-browser CLI interface."""
    try:
        page = _ensure_browser()
        return _dispatch(page, args)
    except Exception as exc:
        return False, str(exc)


def _dispatch(page: Any, args: list[str]) -> tuple[bool, str]:
    """Route CLI-style args to Playwright API calls."""
    if not args:
        return False, "No command specified"

    cmd = args[0]

    if cmd == "open" and len(args) > 1:
        page.goto(args[1], wait_until="domcontentloaded", timeout=30000)
        return True, ""

    if cmd == "get" and len(args) > 1:
        prop = args[1]
        if prop == "title":
            return True, page.title()
        if prop == "url":
            return True, page.url
        return False, f"Unknown property: {prop}"

    if cmd == "snapshot":
        tree = page.accessibility.snapshot()
        return True, _format_tree(tree) if tree else ""

    if cmd == "screenshot" and len(args) > 1:
        page.screenshot(path=args[1])
        return True, ""

    if cmd == "click" and len(args) > 1:
        page.click(args[1])
        return True, "clicked"

    if cmd == "fill" and len(args) > 2:
        page.fill(args[1], args[2])
        return True, ""

    if cmd == "eval" and len(args) > 1:
        result = page.evaluate(args[1])
        return True, str(result) if result is not None else ""

    if cmd == "cookies" and len(args) > 2 and args[1] == "set":
        name = args[2]
        value = args[3] if len(args) > 3 else ""
        cookie: dict[str, Any] = {"name": name, "value": value}
        # Parse flags
        i = 4
        while i < len(args):
            flag = args[i]
            if flag == "--url" and i + 1 < len(args):
                cookie["url"] = args[i + 1]
                i += 2
            elif flag == "--domain" and i + 1 < len(args):
                cookie["domain"] = args[i + 1]
                i += 2
            elif flag == "--path" and i + 1 < len(args):
                cookie["path"] = args[i + 1]
                i += 2
            elif flag == "--httpOnly":
                cookie["httpOnly"] = True
                i += 1
            elif flag == "--secure":
                cookie["secure"] = True
                i += 1
            else:
                i += 1
        page.context.add_cookies([cookie])
        return True, ""

    if cmd == "set" and len(args) > 1:
        if args[1] == "device" and len(args) > 2:
            from playwright.sync_api import sync_playwright

            devices = sync_playwright().start().devices
            if args[2] in devices:
                vp = devices[args[2]].get("viewport", {})
                page.set_viewport_size(vp)
            return True, ""
        if args[1] == "viewport" and len(args) > 3:
            page.set_viewport_size({"width": int(args[2]), "height": int(args[3])})
            return True, ""
        return False, f"Unknown set command: {args[1]}"

    return False, f"Unknown command: {cmd}"


def _format_tree(node: dict[str, Any] | None, indent: int = 0) -> str:
    """Format accessibility tree into text similar to agent-browser output."""
    if not node:
        return ""
    prefix = "  " * indent
    role = node.get("role", "")
    name = node.get("name", "")
    line = f"{prefix}- {role}"
    if name:
        line += f' "{name}"'
    lines = [line]
    for child in node.get("children", []):
        lines.append(_format_tree(child, indent + 1))
    return "\n".join(lines)
