# CLAUDE.md — cc-arxiv

## Purpose

A Claude Code plugin for research-paper work. It ships skills plus one MCP server entry (`.mcp.json`, pointing at alphaXiv's hosted server) and two bundled Python scripts. There is no other runtime code and no Node dependency.

## Conventions

- Skill content first. Add runtime code only when prose cannot do the job, and keep it dependency-free Python 3.9 (no `match`, no `X | Y` types).
- Skill bodies in this plugin **intentionally name Claude Code tools literally** (`WebSearch`, `WebFetch`, `Agent`, `Read`, `mcp__plugin_cc-arxiv_alphaxiv__*`). This differs from `cc-skills`, whose bodies stay agent-neutral. Keep the "Tool Discipline" block at the top of each workflow skill accurate when tool names change.
- Bundled scripts are referenced as `${CLAUDE_SKILL_DIR}/...` and pre-approved with `allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/... *)` in the skill frontmatter.
- Never put secrets, `.env` files, reference checkouts, or `node_modules` in this directory. Installs copy the whole directory into `~/.claude/plugins/cache/`.
- `README.md` is the source of truth for the skill and tool tables, setup, and release steps. Keep it in sync with `skills/` and `.mcp.json`.
- Run `python3 -m unittest discover -s tests` after touching `skills/arxiv/scripts/arxiv.py`.
