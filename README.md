# trogocytosis

> **Deprecated (2026-08-27).** This package is no longer an active Vivesca route, and no new releases are planned. Use **agent-browser** for normal browser control and dedicated profiles, **transcytosis** for explicitly authorized exact-domain cookie diagnostics and transfer, and **tegument** for hostile public-page stealth. Repository history remains available as reference.

Browser automation CLI with credential transfer and stealth fallback.

> In cell biology, trogocytosis is the process by which lymphocytes extract membrane fragments from other cells, acquiring their surface identity markers. This tool does the same: it borrows authenticated browser sessions and navigates hostile environments on behalf of AI agents.

## Features

- Credential transfer from Chrome, Arc, or Firefox via cookie bridge, porta, or pycookiecheat
- 1Password auto-login in headed browser sessions
- Stealth patches for bot-detection pages
- SSH transport for running `agent-browser` on another machine
- Persistent sessions through `agent-browser`

## Install

```bash
pip install trogocytosis
uvx trogocytosis --help
```

## Requirements

- [agent-browser](https://www.npmjs.com/package/agent-browser) CLI installed (`npm i -g agent-browser`)
- Python 3.11+

## Examples

```bash
trogocytosis navigate https://example.com
trogocytosis snapshot
trogocytosis inject-cookies github.com --json-output
trogocytosis login linkedin.com
trogocytosis stealth
```

Cookie transfer alone does not prove a usable session. Use `verify-auth` to inject cookies, load the page, and confirm it is authenticated before trusting the session — this avoids mistaking copied cookies for a verified browser login:

```bash
trogocytosis verify-auth linkedin.com \
    --url https://www.linkedin.com/in/terryli \
    --browser-name comet \
    --json-output
```

On success the human form prints `verified: <url>`; on failure it prints a stderr message and exits nonzero, because cookies may have been copied while the page still requires auth or redirected.

Run the browser on a remote host that already has `agent-browser` installed:

```bash
TROGOCYTOSIS_HOST=mac trogocytosis login linkedin.com
TROGOCYTOSIS_HOST=mac trogocytosis snapshot
```

The remote browser command is `ssh "$TROGOCYTOSIS_HOST" agent-browser ...`. Commands that use 1Password also run `op` on the same host.

## License

MIT
