"""MCP server entry point — exposes browser tools via stdio transport."""

from __future__ import annotations

import json

from mcp.server import Server
from mcp.server.stdio import stdio_server

from trogocytosis import browser, cookies, stealth

app = Server("trogocytosis")


@app.tool()
async def browser_navigate(url: str) -> str:
    """Navigate to URL. Returns page title and URL."""
    return json.dumps(browser.navigate(url))


@app.tool()
async def browser_snapshot() -> str:
    """Capture accessibility tree of current page."""
    return json.dumps(browser.snapshot())


@app.tool()
async def browser_screenshot(path: str = "/tmp/screenshot.png", device: str = "") -> str:
    """Capture PNG screenshot of current page."""
    return json.dumps(browser.screenshot(path, device))


@app.tool()
async def browser_click(selector: str) -> str:
    """Click element by CSS selector."""
    return json.dumps(browser.click(selector))


@app.tool()
async def browser_fill(selector: str, value: str) -> str:
    """Fill form field (clears first, then types value)."""
    return json.dumps(browser.fill(selector, value))


@app.tool()
async def browser_eval(js: str) -> str:
    """Evaluate JavaScript in page context."""
    return json.dumps(browser.evaluate(js))


@app.tool()
async def browser_inject_cookies(domain: str, browser_name: str = "chrome") -> str:
    """Import cookies from host browser for a domain (trogocytosis)."""
    return json.dumps(cookies.inject(domain, browser_name))


@app.tool()
async def browser_check_auth() -> str:
    """Check if current page requires authentication."""
    return json.dumps(browser.check_auth())


@app.tool()
async def browser_stealth() -> str:
    """Apply stealth patches to browser session."""
    for js in stealth.patches():
        browser.evaluate(js)
    return json.dumps({"applied": len(stealth.patches()), "ua": stealth.random_ua()})


async def _run() -> None:
    async with stdio_server() as (read, write):
        await app.run(read, write)


def main() -> None:
    """CLI entry point for `uvx trogocytosis`."""
    import asyncio

    asyncio.run(_run())


if __name__ == "__main__":
    main()
