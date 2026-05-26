---
name: auth-wall-recovery
description: Use when trogocytosis hits an authentication wall or login redirect - recover by transferring cookies from the host browser instead of automating login forms
---

# Auth wall recovery (trogocytosis)

When you navigate to a page and hit a login wall, authentication redirect, or 403 on a page that should be accessible, use the credential transfer pattern.

## Recovery sequence

1. `trogocytosis check-auth --json-output` - confirm the page is requiring auth (returns `authenticated: false` if URL contains login/signin/auth/sso)
2. `trogocytosis inject-cookies example.com` - import cookies from the host browser where you're already logged in
3. `trogocytosis navigate <url>` - retry the original URL with the transferred session

## Why this works

trogocytosis borrows existing browser sessions via cookie extraction from the host OS keychain. You log into sites once in your real browser, and trogocytosis can reuse those sessions.

## Do not

- **Do not automate login forms.** trogocytosis is designed to borrow sessions, not create them. Automating logins triggers bot detection on most sites.
- **Do not retry with fresh navigation.** If cookies are expired, re-login in your real browser and repeat step 2.
- **Do not use stealth mode for this.** Stealth is for anti-bot pages, not auth walls.
- **Do not use headed mode for extraction.** Headed/profile/extension environment is preserved only for intentional login flows; normal recovery should return to the private headless session.

## Signs you need this skill

- `trogocytosis check-auth --json-output` returns `authenticated: false`
- Page title is "Sign in" or "Log in"
- URL contains `/login`, `/auth`, `/sso`
- Content mentions "please sign in to continue"
