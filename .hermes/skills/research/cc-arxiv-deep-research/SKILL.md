---
name: cc-arxiv-deep-research
description: Produce cited investigations with durable provenance.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, deep research, provenance, citations]
    related_skills: [cc-arxiv-arxiv, grounded-citations]
---

# cc-arXiv: Deep Research

Conduct a source-heavy investigation with an explicit plan, durable artifacts, citations, and provenance. It pauses after planning for the user's approval.

## When to Use

- The user asks for deep research, a comprehensive investigation, or a source-heavy report.
- Don't use for a question answerable with a few sources.

## Procedure

1. Derive a slug and immediately create `outputs/.plans/<slug>.md` with questions, evidence needed, scale decision, task ledger, verification log, and decision log. Completion: research scope is reviewable.
2. Ask for explicit approval before gathering evidence. Completion: the user has replied affirmatively or revised the plan.
3. For direct research, use at least three focused `web_search` queries and retrieve accepted URLs with `web_extract`; record notes in `outputs/.drafts/<slug>-research-direct.md`. For broad work, delegate bounded independent streams with `delegate_task` and record outputs in separate draft files. Completion: every material source is logged.
4. Write `outputs/.drafts/<slug>-draft.md`, then a cited `outputs/.drafts/<slug>-cited.md`. Inspect every critical claim against a source URL or research note; label inference. Completion: unsupported claims are removed, downgraded, or marked.
5. Review the cited draft directly or with a bounded `delegate_task`, fix fatal issues, and deliver `outputs/<slug>.md` (or `papers/<slug>.md`) plus its `.provenance.md` sidecar. Completion: final and provenance files exist and include verification status.

## Verification

If retrieval or verification is blocked after approval, still deliver a partial artifact with `Verification: BLOCKED` and the exact failure.
