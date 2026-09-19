---
name: cc-arxiv-eli5
description: Explain papers and research ideas in plain English.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, papers, explanation, ELI5]
    related_skills: [cc-arxiv-arxiv]
---

# cc-arXiv: ELI5

Explain the requested paper or research idea with minimal jargon, one useful analogy, and clear caveats. Keep the result in chat unless the user asks for a saved artifact.

## When to Use

- The user asks for an ELI5 explanation, plain-English paper summary, or jargon removal.
- Don't use for a formal review or literature survey.

## Procedure

1. For a specified paper, retrieve its metadata with `cc-arxiv-arxiv` and read the abs/PDF URL with `web_extract`. For a topic, use `web_search` and select 1–3 representative sources. Completion: the explanation is tied to an identified source or the source limitation is explicit.
2. When a claim needs verification, retrieve the relevant primary source with `web_extract`; use visible MCP paper tools only if they are available. Completion: factual claims are distinguishable from interpretation.
3. Structure the answer as **One-Sentence Summary**, **Big Idea**, **How It Works**, **Why It Matters**, **What To Be Skeptical Of**, and **If You Remember 3 Things**. Completion: every section is present or intentionally omitted for brevity.

## Pitfalls

Do not imply that a paper proves more than its cited results. Define jargon immediately or replace it with concrete words.

## Verification

The response names the paper or representative sources and clearly separates reported findings from inference.
