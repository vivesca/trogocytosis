# trogocytosis

Browser automation CLI with credential transfer and stealth.

> In cell biology, trogocytosis is the process by which lymphocytes extract membrane fragments from other cells, acquiring their surface identity markers. This tool does the same — it borrows authenticated browser sessions and navigates hostile environments on behalf of AI agents.

## Features

- **Credential transfer** — import cookies from Chrome, Arc, or Firefox via escalation chain (cookie-bridge → porta → pycookiecheat)
- **1Password auto-login** — headed browser login with auto-fill from 1Password vault
- **Stealth mode** — navigator patches, UA rotation, human-like timing
- **SSH transport** — run agent-browser on a remote host (e.g., Mac with display) via `TROGOCYTOSIS_HOST`

## Install

```bash
pip install trogocytosis
```

## Requirements

- [agent-browser](https://www.npmjs.com/package/agent-browser) CLI installed (`npm i -g agent-browser`)
- Python 3.11+

## Usage

```bash
trogocytosis navigate https://example.com
trogocytosis snapshot
trogocytosis inject-cookies linkedin.com
trogocytosis login linkedin.com
trogocytosis stealth

# Remote execution (agent-browser on another host)
TROGOCYTOSIS_HOST=mac trogocytosis login linkedin.com
```

## License

MIT
