# trogocytosis - Design Spec

## Overview

Browser automation CLI with credential transfer and stealth fallback. It wraps
`agent-browser` and adds Vivesca-specific session borrowing and escalation.

1. **Persistent sessions** - `agent-browser` keeps browser state between CLI calls
2. **Credential transfer** - import cookies from the host browser into the agent browser
3. **SSH transport** - run the browser on another machine with `TROGOCYTOSIS_HOST`
4. **Stealth fallback** - apply navigator patches when bot detection blocks access

## Architecture

```
CLI:               trogocytosis <command>
Library:           from trogocytosis import browser, cookies, stealth
Local backend:     agent-browser ...
Remote backend:    ssh "$TROGOCYTOSIS_HOST" agent-browser ...
```

### Package Structure

```
src/trogocytosis/
    __init__.py          # version, public API re-exports
    browser.py           # Core API: navigate, snapshot, click, fill, eval, screenshot
    cookies.py           # Cookie extraction + injection
    stealth.py           # Navigator patches, UA rotation, human delay
    _agent_browser.py    # Low-level subprocess wrapper for agent-browser CLI
```

### Dependencies

Required:
- `cyclopts>=4.0` - CLI framework
- `agent-browser` CLI installed separately (`npm i -g agent-browser`)

Optional:
- `pycookiecheat>=0.7` - Chrome cookie extraction (macOS/Linux)

## CLI Commands

### navigate

Navigate to URL. Returns page title + URL.
```
trogocytosis navigate https://example.com
```

### snapshot

Capture accessibility tree of current page.
```
trogocytosis snapshot
```

### screenshot

Capture PNG screenshot.
```
trogocytosis screenshot /tmp/page.png
```

### click

Click element by CSS selector.
```
trogocytosis click '[ref=e12]'
```

### fill

Fill form field.
```
trogocytosis fill '#email' terry@example.com
```

### eval

Evaluate JavaScript in page context.
```
trogocytosis eval 'document.body.innerText'
```

### inject-cookies

Import cookies from host browser for a domain (the trogocytosis action).
```
trogocytosis inject-cookies github.com --json-output
```

### check-auth

Check if current page requires authentication.
```
trogocytosis check-auth --json-output
```

## Cookie Transfer (trogocytosis)

Extraction tiers:
1. Cookie bridge, defaulting to `mac:7743`
2. `porta`, when installed
3. `pycookiecheat`, when installed

Injection: `agent-browser cookies set <name> <value> --url <url> --domain <domain> --httpOnly --secure`

## Stealth Patches (applied to agent-browser context)

Via `trogocytosis stealth`:
- `navigator.webdriver` -> undefined
- `window.chrome.runtime` -> stub
- `navigator.plugins` -> mock array
- Permissions query -> resolved promise
- Random User-Agent from 20 real Chrome UAs

## Remote Browser Host

Set `TROGOCYTOSIS_HOST` to run `agent-browser` over SSH:

```
TROGOCYTOSIS_HOST=mac trogocytosis login linkedin.com
TROGOCYTOSIS_HOST=mac trogocytosis snapshot
```

## Testing

- Unit tests: mock subprocess calls, test cookie parsing, test stealth patches
- Integration test: navigate to httpbin.org, extract content, verify
- Auth test: inject test cookies, verify they persist across navigations
