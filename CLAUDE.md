# CLAUDE.md — cc-skills

## Purpose

A Claude Code plugin that ships reusable **skills**. Each `skills/<name>/SKILL.md`
is loaded on-demand when a task matches its `description`, or invoked explicitly
as `/<name>`. There is no runtime code — only skill content plus the
`.claude-plugin/plugin.json` manifest Claude Code reads to discover it.

Some skills deliberately depend on other skills in this plugin (`plan` →
`research`; `implement` → `tdd`, `code-review`). Each names its dependency and
specifies an inline fallback when it is absent — preserve that fallback when
editing.

## Conventions

- Skill content only — do not add build tooling or runtime code unless asked.
- Each skill is a directory `skills/<name>/` containing `SKILL.md` with `name`
  and `description` frontmatter; the `name` must be lowercase a-z, 0-9, hyphens.
- `README.md` is the source of truth for the skill list, install, and
  skill-authoring steps. Keep it and the skill table in sync with `skills/` and
  `.claude-plugin/plugin.json`; do not restate its instructions here.
- Keep skill bodies as declarative agent instructions; no machine-specific paths
  inside a body.
- Skill bodies are agent-neutral: avoid Claude-Code-only tool names so the same
  content can be reused by other agents.
