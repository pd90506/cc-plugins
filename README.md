# cc-plugins

Custom skills, plugins, and extensions for Claude Code.

Each subdirectory is a self-contained plugin or skill collection.

Layout conventions:

- `<plugin-name>/.claude-plugin/plugin.json` for a Claude Code plugin
- `<plugin-name>/skills/<skill-name>/SKILL.md` for skills
- `<plugin-name>/agents/`, `commands/`, `hooks/` as needed

Plugins:

- `cc-skills/` — reusable skills (plan, implement, research, tdd, code-review, grill-me, handoff, codebase-design, writing-for-agents)
- `cc-arxiv/` — research-paper skills (arxiv, literature-review, source-comparison, research-review, paper-code-audit, deep-research, eli5) plus the alphaXiv MCP server

`.claude-plugin/marketplace.json` lists the plugins so this directory can be added as a local marketplace:

```bash
claude plugin marketplace add /Users/panda/repo/Agents/cc-plugins
```
