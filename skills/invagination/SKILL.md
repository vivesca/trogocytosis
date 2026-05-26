---
name: invagination
description: Use when extracting structured content (headlines, article text, data tables) from a page with trogocytosis - combines navigate + snapshot efficiently (formerly browser-extraction)
---

# Invagination (trogocytosis extraction workflow)

Follow `immunological-synapse` for lifecycle rules before extracting content.

Extract content from pages using the cheapest-first pattern.

## Sequence

1. `trogocytosis navigate <url>` - load the page, get title + URL
2. `trogocytosis snapshot` - accessibility tree (cheapest overview, usually sufficient)
3. **If snapshot is incomplete** (SPA, heavy JS, dynamic content):
   use body text extraction with selector `body`. Do not call `agent-browser get text` without a selector.
4. **For specific elements** - use the `[ref=eXX]` IDs from snapshot to locate, then `trogocytosis eval` with targeted querySelectors

## Why snapshot first

The accessibility tree is what screen readers see. It's structured, already parsed, and captures the semantic meaning of the page. It's the cheapest way to understand a page's content without rendering overhead.

## When to fall back to eval

- Snapshot shows mostly `StaticText` nodes with no structure (JS hasn't rendered)
- Content is inside iframes or shadow DOMs
- You need a very specific element that's not in the accessibility tree
- You need computed styles or JavaScript-only data

## Anti-patterns

- **Don't use eval as the default.** It's slower and gives raw HTML/text without structure.
- **Don't screenshot for content extraction.** Screenshots are for visual debugging, not data extraction.
- **Don't call snapshot multiple times.** Refs become stale after actions; re-snapshot only after clicks/fills.
- **Don't re-state lifecycle policy here.** `immunological-synapse` is the source of truth for headed/profile/session behavior.
