---
name: cc-arxiv-source-comparison
description: Compare research sources with evidence and caveats.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, comparison, papers, evidence]
    related_skills: [cc-arxiv-arxiv, grounded-citations]
---

# cc-arXiv: Source Comparison

Produce a grounded comparison of papers, tools, approaches, frameworks, or claims. Use primary sources and state uncertainty rather than filling gaps.

## When to Use

- The user requests a comparison matrix across multiple research sources.
- Don't use for a single-paper critique.

## Procedure

1. Derive a lowercase slug of at most five meaningful words. Write the scope, sources, evaluation dimensions, and expected output to `outputs/.plans/<slug>.md`. Completion: the plan records every source or selection criterion.
2. Retrieve known papers using `cc-arxiv-arxiv`; use `web_search` for discovery and `web_extract` for paper or primary URLs. Completion: every matrix row has an inspected source URL.
3. For broad independent workstreams, use `delegate_task`; otherwise research directly. Completion: research notes and source URLs are available before synthesis.
4. Write exactly one `outputs/<slug>-comparison.md` with a matrix covering source, key claim, evidence type, caveats, and confidence; distinguish agreement, disagreement, and uncertainty. End with direct URLs and BibTeX where useful. Completion: every material claim has a source.

## Verification

Read the final artifact with `read_file` and verify it exists, includes its Sources section, and does not contain unsupported claims.
