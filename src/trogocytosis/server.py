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


# ---------------------------------------------------------------------------
# Prompts — universal usage guidance that ships with the package
# ---------------------------------------------------------------------------


@app.prompt()
def auth_wall_recovery(domain: str) -> str:
    """Guidance for handling authentication walls on a domain."""
    return f"""You hit an authentication wall on {domain}. Recovery sequence:

1. `browser_check_auth()` — confirm the page is actually requiring auth
2. `browser_inject_cookies(domain="{domain}")` — import cookies from the host
   browser (Chrome, Arc, Firefox) where you're already logged in
3. `browser_navigate(url)` — retry the original URL
4. If still blocked, the host browser session may have expired. Open the site
   in your real browser, log in fresh, then retry step 2.

Do NOT attempt to automate login forms — trogocytosis borrows existing sessions
rather than creating them. That's the whole point of the credential transfer
pattern."""


@app.prompt()
def extraction_workflow(url: str) -> str:
    """How to extract structured data from a page efficiently."""
    return f"""To extract content from {url}:

1. `browser_navigate("{url}")` — load the page
2. `browser_snapshot()` — get the accessibility tree (cheapest overview)
3. If the page is a SPA or JS-heavy and snapshot is incomplete:
   `browser_eval("document.body.innerText")` — fallback to innerText
4. For specific elements: use the [ref=eXX] IDs from the snapshot to locate
   them, then `browser_eval` with targeted querySelector calls.

The snapshot is usually all you need. Only fall back to eval when the
accessibility tree doesn't capture dynamic content."""


@app.prompt()
def stealth_browsing() -> str:
    """When to apply stealth patches (and when not to)."""
    return """Apply `browser_stealth()` ONLY when a site is actively blocking
automated access (Cloudflare challenge, Akamai bot detection, navigator.webdriver
checks). It patches navigator, spoofs Chrome runtime, rotates UA.

Don't apply stealth preemptively — it adds overhead and can break legitimate
interactions (some sites check that the patches exist as a bot signal).

Signs you need stealth:
- Page loads but content is empty
- Cloudflare "Checking your browser" page persists
- 403 or 429 on otherwise-public pages

Signs you don't need it:
- Authenticated pages (use inject_cookies instead)
- Normal public pages that load fine"""


@app.prompt()
def session_persistence() -> str:
    """Understanding trogocytosis's persistent session model."""
    return """trogocytosis reuses one browser instance across all tool calls in
a session. Cookies, localStorage, and open tabs persist until the MCP server
stops. This means:

- Login once via inject_cookies, then navigate freely
- Don't call browser_stealth() multiple times — patches stick
- Session state survives individual tool errors
- If you need a fresh session, restart the MCP server

Compare to vanilla Playwright MCP which creates a new browser per call —
trogocytosis keeps the expensive browser process alive, which is 2-3x faster
on sequential calls."""


def main() -> None:
    """CLI entry point — dispatches between MCP server and install-skills."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "install-skills":
        from trogocytosis.install import main as install_main
        raise SystemExit(install_main(sys.argv[2:]))

    # Default: run MCP server
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
