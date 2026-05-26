---
name: immunological-synapse
description: Canonical lifecycle substrate for trogocytosis browser automation - private session, headless defaults, cookies, state, cleanup, and env isolation across CLI calls (formerly browser-session)
---

# Immunological synapse (trogocytosis session model)

Load this skill first for any trogocytosis browser workflow. Invagination, surface-marker-transfer, and glycocalyx all inherit these rules.

## Canonical rules

- Use the private `agent-browser` session named `trogocytosis`.
- Normal commands are headless: `agent-browser --session trogocytosis --headed false ...`.
- Non-headed commands strip `AGENT_BROWSER_HEADED`, `AGENT_BROWSER_PROFILE`, and `AGENT_BROWSER_EXTENSIONS`.
- Preserve headed/profile/extension environment only for explicit headed login flows.
- Close only this session: `agent-browser --session trogocytosis close`. Never use `close --all`.
- Use `TROGOCYTOSIS_SESSION=<name>` only for intentional separate personas or parallel workflows.
- Use `TROGOCYTOSIS_TIMEOUT=<seconds>` only for known-slow pages.

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

To restart only this browser: `agent-browser --session trogocytosis close`, then run the next `trogocytosis` command.

## Do not

- **Don't assume cross-host state.** `TROGOCYTOSIS_HOST=mac` and local execution use different browser state.
- **Don't mix personas** in the same session - cookies from domain A can bleed into domain B if you don't clear them.
- **Don't rely on the current tab** - always pass URLs to `trogocytosis navigate` rather than assuming where you left off.
- **Don't set headed/profile/extension env vars** for normal extraction. Use headed mode only for intentional login flows.
