---
name: efficient-browser-automation
description: Use when testing pages in a browser, checking UI, verifying visual output, debugging frontend issues, or running any browser automation task
---

# Efficient Browser Automation

## Overview

Use the Playwright CLI (`npx playwright`) for all browser automation.
Use accessibility tree snapshots instead of screenshots to save tokens and get structured output.

## Quick Reference

| Task                                 | Command                          |
| ------------------------------------ | -------------------------------- |
| Open a URL in a browser              | `npx playwright open <url>`      |
| Generate test code interactively     | `npx playwright codegen <url>`   |
| Run test files                       | `npx playwright test`            |
| Run a specific test                  | `npx playwright test <file>`     |
| Show test report                     | `npx playwright show-report`     |
| Install browsers                     | `npx playwright install`         |

## Core Rules

1. **Playwright CLI only** — use `npx playwright` commands for all browser automation. Never use `claude-in-chrome` or `chrome-devtools` MCP unless the user explicitly asks for them
2. **Accessibility tree, not screenshots** — when inspecting page content, use `page.accessibility.snapshot()` in Playwright test scripts. This returns structured, parseable data and costs far fewer tokens than base64 images. Only take screenshots when a visual check is explicitly needed
3. **Parallel sub-agents for multi-page testing** — when checking multiple pages or flows, dispatch each as a separate sub-agent running its own Playwright CLI commands

## Inspecting Pages with Accessibility Snapshots

In Playwright test scripts, use the accessibility tree to inspect page content:

```js
const snapshot = await page.accessibility.snapshot();
console.log(JSON.stringify(snapshot, null, 2));
```

Or use `npx playwright codegen <url>` to interactively explore the page and generate selectors.

## Multi-Page Testing Pattern

When verifying multiple pages (e.g., checking 5 URLs for correct rendering), dispatch sub-agents in parallel:

- Agent 1: `npx playwright test` for url-1 + accessibility snapshot
- Agent 2: `npx playwright test` for url-2 + accessibility snapshot
- Agent 3: `npx playwright test` for url-3 + accessibility snapshot

Each agent reports back its findings. This is faster than sequential testing and keeps context windows small.

## Common Mistakes

| Mistake                                                  | Fix                                                      |
| -------------------------------------------------------- | -------------------------------------------------------- |
| Using `claude-in-chrome` or `chrome-devtools` MCP        | Use `npx playwright` CLI instead                         |
| Taking screenshots for page inspection                   | Use `page.accessibility.snapshot()` for structured output |
| Testing pages sequentially                               | Dispatch parallel sub-agents                             |
| Using MCP tools like `browser_navigate`                  | Use Playwright CLI commands and test scripts             |
