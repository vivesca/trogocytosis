# trogocytosis

Persistent browser MCP server with credential transfer and stealth fallback.

> In cell biology, trogocytosis is the process by which lymphocytes extract membrane fragments from other cells, acquiring their surface identity markers. This tool does the same — it borrows authenticated browser sessions and navigates hostile environments on behalf of AI agents.

## Features

- **Persistent sessions** — browser stays alive across MCP calls, no cold starts
- **Credential transfer** — import cookies from Chrome, Arc, or Firefox into the agent browser
- **Stealth fallback** — headless -> cookie injection -> stealth mode, escalating as needed
- **Anti-bot measures** — navigator patches, UA rotation, human-like timing

## Install

```bash
uvx trogocytosis          # run as MCP server
pip install trogocytosis  # use as library
```

## Requirements

- [agent-browser](https://www.npmjs.com/package/agent-browser) CLI installed (`npm i -g agent-browser`)
- Python 3.11+

## License

MIT
