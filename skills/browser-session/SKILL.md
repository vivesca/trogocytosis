---
name: browser-session
description: Use when understanding or managing trogocytosis's persistent browser session - cookies, state, and lifecycle across multiple CLI calls
---

# Browser session model (trogocytosis)

trogocytosis reuses the `agent-browser` session across CLI calls. This avoids cold starts and keeps page state available while an agent performs a sequence of browser actions.

## What persists across calls

- **Cookies** - including those injected via `trogocytosis inject-cookies`
- **localStorage** - authentication tokens, preferences, cached data
- **Session storage** - temporary state within a tab
- **Open tabs** - the current page stays open between calls
- **Stealth patches** - if applied via `trogocytosis stealth`, they stick

## What does NOT persist

- **After browser close/restart** - state is reset when the backing browser profile is cleared
- **Across devices** - session is local to the machine running `agent-browser`
- **After explicit clear** - some sites clear their own state on navigation

## Performance implication

Compare to launching a fresh Playwright browser per action:

| Operation | trogocytosis | Fresh Playwright |
|---|---|---|
| First navigate | ~1s | ~4s (browser launch) |
| Subsequent navigate | ~0.5s | ~4s (browser launch) |
| 10-call sequence | ~6s | ~40s |

Use trogocytosis when you have sequential browser operations. The persistent session is its defining feature.

## When to restart the session

- Session cookies expired (re-login required)
- State corruption (site behaving weirdly)
- Switching between drastically different auth contexts

To restart: close the backing `agent-browser` session, then run the next `trogocytosis` command.

## Do not

- **Don't assume cross-host state.** `TROGOCYTOSIS_HOST=mac` and local execution use different browser state.
- **Don't mix personas** in the same session - cookies from domain A can bleed into domain B if you don't clear them.
- **Don't rely on the current tab** - always pass URLs to `trogocytosis navigate` rather than assuming where you left off.
