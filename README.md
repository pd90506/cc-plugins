# cc-skills

A small library of reusable [Claude Code](https://docs.claude.com/en/docs/claude-code)
skills, packaged as a plugin. Each skill lives in `skills/<name>/SKILL.md` and is
loaded on-demand when a task matches its description, or invoked explicitly as
`/<name>` (namespaced `/cc-skills:<name>` when loaded via the plugin).

Migrated from the Pi package `mypi-skills`; the skill bodies are agent-neutral
and unchanged apart from install-location notes.

## Skills

| Skill                | Description                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------- |
| `plan`               | Research first (via `research`), then write an implementation plan under `docs/plans/` before executing.      |
| `implement`          | Implement an approved plan test-first (`tdd`), review with `code-review` subagents, fix findings, report.      |
| `research`           | Investigate a question against primary sources and capture findings as Markdown in the repo.                  |
| `tdd`                | Red-green-refactor test-driven development, with guidance on tests and mocking.                               |
| `code-review`        | Review changes since a fixed point along two axes (Standards, Spec) in parallel subagents.                     |
| `grill-me`           | A relentless interview to sharpen a plan or design. Manual invocation only.                                   |
| `handoff`            | Compact the current conversation into a handoff document for another agent. Manual invocation only.          |
| `codebase-design`    | Shared vocabulary for designing deep modules; includes deepening and design-it-twice references.              |
| `writing-for-agents` | How to write skills, `CLAUDE.md` / `AGENTS.md`, and other documents an agent consumes.                        |
| `read-pdf`           | Read any PDF into Markdown by rendering pages with the bundled `readpdf.py` and reading the pixels.           |

Skill dependencies: `plan` → `research`; `implement` → `tdd`, `code-review`.
All are bundled here, and each dependent skill specifies an inline fallback if
its dependency is unavailable.

## Install

**Quick test (no install)** — load the plugin for one session:

```bash
claude --plugin-dir /Users/panda/repo/Agents/cc-plugins/cc-skills
```

**Persistent install** — register the parent directory as a local marketplace,
then install the plugin from it:

```bash
claude plugin marketplace add /Users/panda/repo/Agents/cc-plugins
```

```bash
claude plugin install cc-skills@cc-plugins
```

Skills then appear as `/cc-skills:<name>`. After editing skill files, restart
Claude Code (or `/reload-plugins`) to pick up changes.

## Adding a skill

Create `skills/<name>/SKILL.md` with the required frontmatter:

```markdown
---
name: my-skill
description: What this skill does and when to use it. Be specific — this is what
  the agent matches against to decide when to load the skill.
---

# My Skill

Instructions for the agent. Reference bundled scripts or docs with paths
relative to this skill's directory.
```

Optional frontmatter: `disable-model-invocation: true` (only the user can
invoke it) and `argument-hint` (shown when the user types the slash command).
Follow the `writing-for-agents` skill when authoring.
