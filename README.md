# trogocytosis

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

Run the browser on a remote host that already has `agent-browser` installed:

```bash
TROGOCYTOSIS_HOST=mac trogocytosis login linkedin.com
TROGOCYTOSIS_HOST=mac trogocytosis snapshot
```

The remote browser command is `ssh "$TROGOCYTOSIS_HOST" agent-browser ...`. Commands that use 1Password also run `op` on the same host.

## License

MIT
