# doordarius-skills

A personal collection of [Claude Code](https://claude.com/claude-code) skills for web development, browser automation, and AI-assisted workflows.

Skills are short markdown files with frontmatter that teach an AI assistant how to handle a specific task. The skill content is platform-agnostic — Claude Code users can install this as a plugin, but the markdown files also work in Codex CLI, GitHub Copilot, Cursor, and other AI tools.

## Skills

| Skill | What it does |
| --- | --- |
| [`efficient-browser-automation`](./skills/efficient-browser-automation/SKILL.md) | Use Playwright CLI + accessibility snapshots instead of screenshots/MCP browser tools |

## Install (Claude Code)

```bash
# Add this repo as a plugin marketplace
/plugin marketplace add dariusrosendahl/doordarius-skills

# Install the plugin
/plugin install doordarius-skills
```

Skills will then be auto-discovered and invokable as `/efficient-browser-automation`, etc.

## Install (Codex CLI)

Copy any skill's `SKILL.md` into your Codex prompts folder:

```bash
cp skills/efficient-browser-automation/SKILL.md ~/.codex/prompts/efficient-browser-automation.md
```

Invoke with `/efficient-browser-automation` in Codex.

## Install (GitHub Copilot, VS Code)

Copy any skill's `SKILL.md` into your repo's prompts folder:

```bash
mkdir -p .github/prompts
cp skills/efficient-browser-automation/SKILL.md \
   .github/prompts/efficient-browser-automation.prompt.md
```

Invoke with `/efficient-browser-automation` in Copilot Chat.

## Cross-tool (AGENTS.md)

For tools that auto-load `AGENTS.md` (Codex, Cursor, Aider), append a skill's content to your repo's `AGENTS.md` to make it always-on.

## Adding a new skill

```
skills/
└── your-skill-name/
    └── SKILL.md
```

Each `SKILL.md` needs YAML frontmatter:

```markdown
---
name: your-skill-name
description: Use when <trigger condition> — concise, specific
---

# Your Skill Name

...content...
```

Then add a row to the table above.

## License

MIT
