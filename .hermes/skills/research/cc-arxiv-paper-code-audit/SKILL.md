---
name: cc-arxiv-paper-code-audit
description: Audit paper claims against a public codebase.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, reproducibility, code audit, papers]
    related_skills: [cc-arxiv-arxiv]
---

# cc-arXiv: Paper-Code Audit

Compare a paper's claims with its public implementation and report mismatches, ambiguous defaults, missing code, and reproduction risks.

## When to Use

- The user requests a paper audit, code-claim consistency check, or reproducibility assessment.
- Don't use for a general code review without a paper target.

## Procedure

1. Derive a concise slug and write `outputs/.plans/<slug>.md` listing the paper, repository, and claims to check. Completion: each target claim is identifiable.
2. Retrieve the paper with `cc-arxiv-arxiv` and `web_extract`; retrieve repository files with `web_extract` for GitHub URLs or inspect a local checkout with `read_file` and `search_files`. Completion: evidence notes record every inspected URL or path.
3. Compare methods, defaults, metrics, and data handling. Use `delegate_task` only when the evidence set has independent substantial components. Completion: each finding cites the paper and code evidence or is marked blocked.
4. Write exactly one `outputs/<slug>-audit.md`, including missing code, mismatches, ambiguous defaults, reproduction risks, and a Sources section with paper and repository URLs. Completion: the artifact exists and is readable with `read_file`.

## Verification

Mark unavailable paper text or code as `Verification: BLOCKED`; never represent missing evidence as a defect.
