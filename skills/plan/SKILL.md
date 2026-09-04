---
name: plan
description: Research first, then write an implementation plan before executing. Use when the user wants a task investigated against primary sources and captured as an ordered implementation plan (written to files) before any code is changed.
---

# Plan

Before writing any code or making changes, produce a **plan** for the task the
user asked to plan.

Rules:

1. **Research first, using the `research` skill.** Load and follow the
   `research` skill to investigate the task against primary sources, and have it
   **write the findings to a Markdown file** (save it under `docs/research/`,
   e.g. `docs/research/<slug>-<YYYY-MM-DD>.md`). This keeps the research durable
   so it does not have to be redone next time. If a suitable research file for
   this task already exists, reuse it instead of researching again.
2. **Do not execute.** Make no edits, file writes (except the research and plan
   files), installs, or other changes. This is planning only.
3. **Write the plan to a file** at `docs/plans/NN-<slug>-<YYYY-MM-DD>.md`:
   - `NN` = next zero-padded sequence number in `docs/plans/` (start at `01`).
   - `<slug>` = short kebab-case summary of the task.
   - `<YYYY-MM-DD>` = today's date.
   - Create `docs/plans/` if it doesn't exist.
4. **Draft the spec first.** Begin the document with a `## Spec` section that
   defines *what* to build and *why*, before any implementation steps. The spec
   is the contract the rest of the plan must satisfy, so the steps can be
   verified against it. The spec should cover:
   - **Goal / problem statement** — the problem being solved and for whom.
   - **Scope** — what is included, and explicitly what is out of scope
     (non-goals).
   - **Requirements / behavior** — concrete, observable statements of how it
     should behave ("When X, the system does Y").
   - **Acceptance criteria** — the checklist that defines done and correct;
     these double as the test list during implementation.
   - **Constraints & assumptions** — dependencies, compatibility, performance,
     and anything taken as given.
   - **Open questions** — things still undecided.
5. **Plan contents (after the spec):**
   - A link to the research file, plus a short summary of its key findings.
   - Research findings, with file paths or source references.
   - A detailed, ordered list of concrete implementation steps, each traceable
     to the spec's requirements or acceptance criteria.
   - Files to create or modify.
   - Risks and assumptions.

When done, give the user the file path and a brief summary, then wait for their
approval before executing anything.

> **Dependency:** this skill loads the `research` skill, bundled alongside it in
> this plugin. If it is unavailable, research inline instead.
