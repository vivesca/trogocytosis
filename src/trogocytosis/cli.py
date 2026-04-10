"""CLI interface — cyclopts commands wrapping the same browser/cookies/stealth modules."""

from __future__ import annotations

import json
import sys

import cyclopts

from trogocytosis import browser, cookies, stealth

app = cyclopts.App(name="trogocytosis", help="Browser automation with credential transfer and stealth.")


@app.command
def navigate(url: str, *, json_output: bool = False) -> None:
    """Navigate to URL. Prints title and URL."""
    result = browser.navigate(url)
    if json_output:
        print(json.dumps(result))
    else:
        print(f"{result['title']}\n{result['url']}")


@app.command
def snapshot(*, json_output: bool = False) -> None:
    """Capture accessibility tree of current page."""
    result = browser.snapshot()
    if json_output:
        print(json.dumps(result))
    else:
        print(result["snapshot"])


@app.command
def screenshot(path: str = "/tmp/screenshot.png", *, device: str = "", json_output: bool = False) -> None:
    """Capture PNG screenshot."""
    result = browser.screenshot(path, device)
    if json_output:
        print(json.dumps(result))
    else:
        print(f"Saved {result['size_bytes']} bytes to {result['path']}")


@app.command
def click(selector: str, *, json_output: bool = False) -> None:
    """Click element by CSS selector or @ref."""
    result = browser.click(selector)
    if json_output:
        print(json.dumps(result))
    elif not result["success"]:
        print("Click failed", file=sys.stderr)
        raise SystemExit(1)


@app.command
def fill(selector: str, value: str, *, json_output: bool = False) -> None:
    """Fill form field (clears first)."""
    result = browser.fill(selector, value)
    if json_output:
        print(json.dumps(result))
    elif not result["success"]:
        print("Fill failed", file=sys.stderr)
        raise SystemExit(1)


@app.command(name="eval")
def eval_js(js: str, *, json_output: bool = False) -> None:
    """Evaluate JavaScript in page context."""
    result = browser.evaluate(js)
    if json_output:
        print(json.dumps(result))
    else:
        print(result["result"])


@app.command(name="inject-cookies")
def inject_cookies(domain: str, *, browser_name: str = "chrome", json_output: bool = False) -> None:
    """Import cookies from host browser for a domain."""
    result = cookies.inject(domain, browser_name)
    if json_output:
        print(json.dumps(result))
    else:
        print(f"Injected {result['count']} cookies for {result['domain']}")


@app.command(name="check-auth")
def check_auth(*, json_output: bool = False) -> None:
    """Check if current page requires authentication."""
    result = browser.check_auth()
    if json_output:
        print(json.dumps(result))
    else:
        status = "authenticated" if result["authenticated"] else "auth required"
        print(f"{status}: {result['url']}")


@app.command(name="login")
def login(domain: str, *, login_url: str = "", json_output: bool = False) -> None:
    """Headed browser login with 1Password auto-fill. Persists session."""
    result = cookies.login_headed(domain, login_url or None)
    if json_output:
        print(json.dumps(result))
    else:
        if result.get("success"):
            fill_msg = " (auto-filled from 1Password)" if result.get("auto_filled") else ""
            print(f"Logged in to {domain}{fill_msg}")
            print(f"Session URL: {result.get('url', '')}")
        else:
            print(f"Login may have failed: {result.get('url', result.get('error', ''))}", file=sys.stderr)
            raise SystemExit(1)


@app.command(name="stealth")
def apply_stealth(*, json_output: bool = False) -> None:
    """Apply stealth patches to browser session."""
    for js in stealth.patches():
        browser.evaluate(js)
    result = {"applied": len(stealth.patches()), "ua": stealth.random_ua()}
    if json_output:
        print(json.dumps(result))
    else:
        print(f"Applied {result['applied']} patches, UA: {result['ua']}")


@app.command(name="serve")
def serve() -> None:
    """Run as MCP server (stdio transport)."""
    from trogocytosis.server import app as mcp_app

    mcp_app.run(transport="stdio")


def main() -> None:
    app()
