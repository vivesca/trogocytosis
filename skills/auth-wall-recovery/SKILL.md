---
name: auth-wall-recovery
description: Use when trogocytosis hits an authentication wall or login redirect — recover by transferring cookies from the host browser instead of automating login forms
---

# Auth wall recovery (trogocytosis)

When you navigate to a page and hit a login wall, authentication redirect, or 403 on a page that should be accessible, use the credential transfer pattern.

## Recovery sequence

1. `browser_check_auth()` — confirm the page is requiring auth (returns `authenticated: false` if URL contains login/signin/auth/sso)
2. `browser_inject_cookies(domain="example.com")` — import cookies from the host browser (Chrome, Arc, Firefox) where you're already logged in
3. `browser_navigate(url)` — retry the original URL with the transferred session

## Why this works

trogocytosis borrows existing browser sessions via cookie extraction from the host OS keychain. You log into sites once in your real browser, and trogocytosis can reuse those sessions.

## Do not

- **Do not automate login forms.** trogocytosis is designed to borrow sessions, not create them. Automating logins triggers bot detection on most sites.
- **Do not retry with fresh navigation.** If cookies are expired, re-login in your real browser and repeat step 2.
- **Do not use stealth mode for this.** Stealth is for anti-bot pages, not auth walls.

## Signs you need this skill

- `check_auth()` returns `authenticated: false`
- Page title is "Sign in" or "Log in"
- URL contains `/login`, `/auth`, `/sso`
- Content mentions "please sign in to continue"
