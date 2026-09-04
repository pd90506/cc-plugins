# cc-plugins

Custom skills, plugins, and extensions for Claude Code.

Each subdirectory is a self-contained plugin or skill collection.

Layout conventions:

- `<plugin-name>/.claude-plugin/plugin.json` for a Claude Code plugin
- `<plugin-name>/skills/<skill-name>/SKILL.md` for skills
- `<plugin-name>/agents/`, `commands/`, `hooks/` as needed

Plugins:

- `cc-skills/` — reusable skills (plan, implement, research, tdd, code-review, grill-me, handoff, codebase-design, writing-for-agents)
- `cc-arxiv/` — research-paper skills (arxiv, literature-review, source-comparison, research-review, paper-code-audit, deep-research, eli5) (uses the separately connected alphaXiv MCP server)

`.claude-plugin/marketplace.json` lists the plugins so this repo can be added as a marketplace.

Claude Code:

```bash
claude plugin marketplace add pd90506/cc-plugins
claude plugin install cc-arxiv@cc-plugins
```

Cowork (Claude desktop app): open **Customize → Plugins → Add marketplace**, enter `pd90506/cc-plugins`, then install the plugin you want. No plugin here stores or prompts for secrets; cc-arxiv expects you to connect the alphaXiv MCP server yourself (OAuth).
