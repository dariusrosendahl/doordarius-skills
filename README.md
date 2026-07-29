# doordarius-skills

[![skills.sh](https://skills.sh/b/dariusrosendahl/doordarius-skills)](https://skills.sh/dariusrosendahl/doordarius-skills)

Personal collection of agent skills for web development, browser automation, and AI-assisted workflows. Works in Claude Code, Codex, Cursor, GitHub Copilot Chat, and [50+ other agents](https://github.com/vercel-labs/skills#supported-agents).

Skills are short markdown files with frontmatter that teach an AI assistant how to handle a specific task.

## Skills

| Skill | What it does |
| --- | --- |
| [`efficient-browser-automation`](./plugins/doordarius-skills/skills/efficient-browser-automation/SKILL.md) | Use Playwright CLI + accessibility snapshots instead of screenshots/MCP browser tools |
| [`seo-technical-expert`](./plugins/doordarius-skills/skills/seo-technical-expert/SKILL.md) | Multi-mode SEO/SEA agent — full audits, GSC analysis, Core Web Vitals, BigQuery, content/copy audits, ads review |
| [`dutch-copy`](./plugins/doordarius-skills/skills/dutch-copy/SKILL.md) | Write, proofread and rewrite Dutch copy through Loes (EU-hosted Dutch-native LLM), with a diff gate so no facts change |

## 30-second install

```sh
npx skills add dariusrosendahl/doordarius-skills
```

Run from inside your agent (Claude Code, Codex CLI, etc.) — the [vercel-labs/skills](https://github.com/vercel-labs/skills) CLI auto-detects which one you're in and symlinks the skills into the right location. Add `-g` for a global install across projects, `--copy` if symlinks aren't supported, or `--skill <name>` to install only a specific one. Same CLI handles `update`, `remove`, and `list`.

### Backup: Claude Code marketplace

If you'd rather not run `npx` (or want the namespaced `doordarius-skills:` prefix in the skill picker):

```sh
/plugin marketplace add dariusrosendahl/doordarius-skills
/plugin install doordarius-skills@doordarius
```

Pick up new versions with `/plugin marketplace update doordarius`.

## Repo layout

```
.claude-plugin/marketplace.json          # marketplace catalog
plugins/doordarius-skills/
├── .claude-plugin/plugin.json           # plugin manifest
└── skills/
    ├── efficient-browser-automation/SKILL.md
    ├── seo-technical-expert/SKILL.md
    └── dutch-copy/
        ├── SKILL.md
        └── scripts/loes.py              # bundled CLI, python3 + curl only
```

## Adding a new skill

Create a new folder under `plugins/doordarius-skills/skills/<skill-name>/SKILL.md`:

```markdown
---
name: your-skill-name
description: Use when <trigger condition> — concise, specific
---

# Your Skill Name

...content...
```

Then add a row to the Skills table above and commit.

## License

MIT
