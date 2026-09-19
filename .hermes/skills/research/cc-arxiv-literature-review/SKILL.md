---
name: cc-arxiv-literature-review
description: Synthesize research literature from primary sources.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, literature review, papers, synthesis]
    related_skills: [cc-arxiv-arxiv, grounded-citations]
---

# cc-arXiv: Literature Review

Survey a topic, lab, PI, author, or research field using inspectable primary sources. Deliver a cited synthesis and provenance record rather than chat-only notes.

## When to Use

- The user asks for a literature review, state-of-the-art survey, or academic landscape.
- Don't use for a single-paper summary.

## Procedure

1. Derive a slug and write scope, source types, period, sections, task ledger, and verification log to `outputs/.plans/<slug>.md`. For a lab or author, resolve identity and publication corpus first. Completion: corpus gaps are explicit.
2. Use `cc-arxiv-arxiv` for known-paper/author/category lookups, `web_search` for discovery, and `web_extract` for primary pages or PDFs. Record reachable publications in `outputs/.drafts/<slug>-publications.md` when reviewing a corpus. Completion: each source has a direct URL.
3. Use `delegate_task` for broad independent triage; keep synthesis lead-owned. Completion: research notes identify done, blocked, or superseded questions.
4. Write a cited final review at `outputs/<slug>.md`, separating consensus, disagreements, open questions, and research trajectories where applicable. Write `outputs/<slug>.provenance.md` with date, sources consulted/accepted/rejected, verification status, and intermediate files. Completion: both final paths exist and are readable with `read_file`.

## Verification

Verify source URLs before treating a source as evidence. Do not generate Mermaid diagrams unless the cited structure changes a research decision.
