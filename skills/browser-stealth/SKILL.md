---
name: browser-stealth
description: Use when a page is actively blocking automated access (Cloudflare challenge, 403, empty content, bot detection) — apply trogocytosis stealth patches
---

# Browser stealth mode (trogocytosis)

Apply stealth only when bot detection is blocking you. It's not a default — it adds overhead and can break legitimate interactions.

## When to apply

Signs you NEED stealth:
- Page loads but `document.body.innerText` is empty
- Cloudflare "Checking your browser" page persists across reloads
- 403 or 429 on otherwise-public pages
- Snapshot shows only bot-check UI

Signs you DON'T need stealth:
- Authenticated pages (use `auth-wall-recovery` instead)
- Normal public pages that load fine
- Auth redirects (different problem)

## How

```
browser_stealth()
```

Applies in one call:
- `navigator.webdriver` → undefined
- `window.chrome.runtime` → stub
- `navigator.plugins` → mock array
- Random Chrome User-Agent rotation

## Do not

- **Don't apply preemptively.** Some sites check that stealth patches EXIST as a bot signal (if `navigator.webdriver` is actively undefined rather than missing, it's suspicious).
- **Don't apply multiple times.** Patches stick — calling again is wasted work.
- **Don't mix with cookie transfer.** If auth is the issue, fix auth first. Stealth is for anonymous bot detection, not auth walls.

## Verify it worked

After applying, re-navigate and snapshot. If content renders now, stealth worked. If still empty, the site's detection is beyond what stealth patches handle — consider residential proxies or accept the limitation.
