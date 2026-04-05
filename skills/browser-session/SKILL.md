---
name: browser-session
description: Use when understanding or managing trogocytosis's persistent browser session — cookies, state, and lifecycle across multiple tool calls
---

# Browser session model (trogocytosis)

trogocytosis reuses one browser instance across all tool calls in a single MCP session. This makes it 2-3x faster than tools that launch a fresh browser per call.

## What persists across calls

- **Cookies** — including those injected via `browser_inject_cookies`
- **localStorage** — authentication tokens, preferences, cached data
- **Session storage** — temporary state within a tab
- **Open tabs** — the current page stays open between calls
- **Stealth patches** — if applied via `browser_stealth`, they stick

## What does NOT persist

- **Between MCP sessions** — when the server restarts, state is lost
- **Across devices** — session is local to the machine running the MCP server
- **After explicit clear** — some sites clear their own state on navigation

## Performance implication

Compare to vanilla Playwright MCP which launches a new browser per call:

| Operation | trogocytosis | Playwright MCP |
|---|---|---|
| First navigate | ~1s | ~4s (browser launch) |
| Subsequent navigate | ~0.5s | ~4s (browser launch) |
| 10-call sequence | ~6s | ~40s |

Use trogocytosis when you have sequential browser operations. The persistent session is its defining feature.

## When to restart the session

- Session cookies expired (re-login required)
- State corruption (site behaving weirdly)
- Switching between drastically different auth contexts

To restart: stop the MCP server and restart it. `uvx trogocytosis` kills the previous instance and launches fresh.

## Do not

- **Don't assume cross-session state.** Every new MCP session starts fresh.
- **Don't mix personas** in the same session — cookies from domain A bleed into domain B if you don't clear them.
- **Don't rely on the current tab** — always pass URLs to `navigate` rather than assuming where you left off.
