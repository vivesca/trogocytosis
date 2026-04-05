"""MCP server — exposes browser tools via FastMCP. Works standalone (uvx) or mounted into another server."""

from __future__ import annotations

from fastmcp import FastMCP

from trogocytosis import browser, cookies, stealth

app = FastMCP("trogocytosis")


@app.tool()
def browser_navigate(url: str) -> dict:
    """Navigate to URL. Returns page title and URL."""
    return browser.navigate(url)


@app.tool()
def browser_snapshot() -> dict:
    """Capture accessibility tree of current page."""
    return browser.snapshot()


@app.tool()
def browser_screenshot(path: str = "/tmp/screenshot.png", device: str = "") -> dict:
    """Capture PNG screenshot of current page."""
    return browser.screenshot(path, device)


@app.tool()
def browser_click(selector: str) -> dict:
    """Click element by CSS selector."""
    return browser.click(selector)


@app.tool()
def browser_fill(selector: str, value: str) -> dict:
    """Fill form field (clears first, then types value)."""
    return browser.fill(selector, value)


@app.tool()
def browser_eval(js: str) -> dict:
    """Evaluate JavaScript in page context."""
    return browser.evaluate(js)


@app.tool()
def browser_inject_cookies(domain: str, browser_name: str = "chrome") -> dict:
    """Import cookies from host browser for a domain (trogocytosis)."""
    return cookies.inject(domain, browser_name)


@app.tool()
def browser_check_auth() -> dict:
    """Check if current page requires authentication."""
    return browser.check_auth()


@app.tool()
def browser_stealth() -> dict:
    """Apply stealth patches to browser session."""
    for js in stealth.patches():
        browser.evaluate(js)
    return {"applied": len(stealth.patches()), "ua": stealth.random_ua()}


def main() -> None:
    """CLI entry point for `uvx trogocytosis`."""
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
