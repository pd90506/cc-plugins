---
name: implement
description: Execute an approved plan from docs/plans/ test-first, review with subagents, fix findings, then report. Use when the user wants an existing written plan implemented end-to-end with TDD, a parallel code review, and a final implementation report.
---

# Implement

Implement the requested plan end-to-end.

If no plan file is given, locate the relevant plan under `docs/plans/` (prefer
the most recent matching one) and confirm it before starting.

Run the following pipeline in order:

1. **Build it test-first, using the `tdd` skill.** Load and follow the `tdd`
   skill to implement the plan red-green-refactor: write failing tests first,
   make them pass, then refactor. Work through the plan's steps in order and
   keep the test suite green as you go.
2. **Review with subagents, using the `code-review` skill.** Load and follow
   the `code-review` skill to review the changes since the pre-implementation
   baseline. Run its parallel review subagents (Standards + Spec) so both the
   repo's coding standards and the plan/spec are checked.
3. **Fix everything the subagents flagged.** Triage each finding from the
   review, fix real issues, and re-run the relevant tests to confirm the fixes.
   For anything you intentionally do not fix, note why. Re-run the review if the
   changes were substantial.
4. **Mark the plan completed.** Update the plan file under `docs/plans/` to
   record that it was implemented: check off each completed step and add a short
   status note near the top (e.g. `Status: Completed <YYYY-MM-DD>`). If any step
   was skipped or deferred, mark it accordingly with a one-line reason.
5. **Show a final implementation report** covering:
   - What was implemented, mapped back to the plan's steps.
   - Files created or modified.
   - Tests added/changed and their current pass/fail status.
   - Review findings and how each was resolved (or why deferred).
   - Any remaining open questions, risks, or follow-ups.

> **Dependencies:** this skill loads the `tdd` and `code-review` skills, bundled
> alongside it in this plugin. If either is unavailable, fall back to
> implementing and reviewing inline.
