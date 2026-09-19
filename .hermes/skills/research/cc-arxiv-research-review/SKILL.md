---
name: cc-arxiv-research-review
description: Critique research artifacts with severity-ranked findings.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, critique, peer review, papers]
    related_skills: [cc-arxiv-arxiv]
---

# cc-arXiv: Research Review

Run a constructive internal critique of a paper, draft, PDF, or linked research artifact. Produce a durable review even when source parsing is blocked.

## When to Use

- The user asks for a research review, paper critique, or pre-submission feedback.
- Don't use for explaining a paper to a general audience.

## Procedure

1. Derive a slug and create `outputs/.plans/<slug>-review-plan.md` stating the artifact identifier, source type, criteria, and verification checks. Completion: novelty, empirical rigor, baselines, reproducibility, claims, figures, metrics, related work, and writing are accounted for.
2. Inspect local artifacts with `read_file`; inspect arXiv and web artifacts using `cc-arxiv-arxiv`, `web_search`, and `web_extract`. Record evidence at `outputs/.drafts/<slug>-review-evidence.md`. Completion: every evidence item names a source path or URL.
3. Use `delegate_task` for separate evidence gathering only when the artifact is large enough to benefit; otherwise complete the review directly. Completion: delegation output is read and incorporated before drafting.
4. Write exactly one `outputs/<slug>-review.md` with Summary Assessment, Strengths, Critical Issues, Major Issues, Minor Issues, Reproducibility and Verification, Inline Annotations, Recommendation, and Sources. Completion: the final artifact exists and every blocked check says what failed.

## Verification

Use `read_file` to confirm the final path exists before claiming completion. Factual missing evidence is `Verification: BLOCKED`, not a paper weakness.
