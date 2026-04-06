# trogocytosis — Design Spec

## Overview

Persistent browser MCP server with credential transfer and stealth fallback.
Wraps `agent-browser` CLI (Apache-2.0, by Vercel) with three capabilities no existing MCP server provides:

1. **Persistent sessions** — browser stays alive across MCP tool calls
2. **Credential transfer (trogocytosis)** — import cookies from Chrome/Arc/Firefox
3. **Multi-tier stealth fallback** — headless -> cookie injection -> stealth patches

## Architecture

```
Standalone users:  uvx trogocytosis  (stdio MCP server)
Vivesca:           from trogocytosis import browser  (direct Python import)
Both:              -> agent-browser CLI (subprocess)
```

### Package Structure

```
src/trogocytosis/
    __init__.py          # version, public API re-exports
    server.py            # MCP server (mcp SDK, stdio transport)
    browser.py           # Core API: navigate, snapshot, click, fill, eval, screenshot
    cookies.py           # Cookie extraction + injection (pycookiecheat, kleis)
    stealth.py           # Navigator patches, UA rotation, human delay
    _agent_browser.py    # Low-level subprocess wrapper for agent-browser CLI
```

### Dependencies

Required:
- `fastmcp>=2.0` — MCP server SDK

Optional:
- `playwright>=1.40` — direct Playwright fallback
- `pycookiecheat>=0.7` — Chrome cookie extraction (macOS/Linux)

agent-browser CLI must be installed separately (`npm i -g agent-browser`).

## MCP Tools

### browser_navigate
Navigate to URL. Returns page title + URL.
```
params: { url: string }
returns: { title: string, url: string }
```

### browser_snapshot  
Capture accessibility tree of current page.
```
params: {}
returns: { snapshot: string }  # ARIA tree text
```

### browser_screenshot
Capture PNG screenshot.
```
params: { path?: string, device?: string }
returns: { path: string, size_bytes: int }
```

### browser_click
Click element by CSS selector.
```
params: { selector: string }
returns: { success: bool }
```

### browser_fill
Fill form field.
```
params: { selector: string, value: string }
returns: { success: bool }
```

### browser_eval
Evaluate JavaScript in page context.
```
params: { js: string }
returns: { result: string }
```

### browser_inject_cookies
Import cookies from host browser for a domain (the trogocytosis action).
```
params: { domain: string, browser?: "chrome" | "arc" | "firefox" }
returns: { count: int, domain: string }
```

### browser_check_auth
Check if current page requires authentication.
```
params: {}
returns: { authenticated: bool, url: string }
```

## Cookie Transfer (trogocytosis)

Extraction tiers:
1. **pycookiecheat** — Python library, reads Chrome Cookies SQLite + Keychain decryption

Injection: `agent-browser cookies set <name> <value> --url <url> --domain <domain> --httpOnly --secure`

## Stealth Patches (applied to agent-browser context)

Via `browser_eval` at session start:
- `navigator.webdriver` -> undefined
- `window.chrome.runtime` -> stub
- `navigator.plugins` -> mock array
- Permissions query -> resolved promise
- Random User-Agent from 20 real Chrome UAs

## Testing

- Unit tests: mock subprocess calls, test cookie parsing, test stealth patches
- Integration test: navigate to httpbin.org, extract content, verify
- Auth test: inject test cookies, verify they persist across navigations
