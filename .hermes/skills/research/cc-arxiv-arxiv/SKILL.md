---
name: cc-arxiv-arxiv
description: Search, download, and cite arXiv papers.
version: 0.4.0
author: panda (pd90506), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, arXiv, papers, citations]
    related_skills: [arxiv]
---

# cc-arXiv: arXiv

Use the bundled dependency-free client for precise arXiv author, title, ID, category, and date searches. It supplements Hermes's built-in `arxiv` skill with formatted results, PDF downloads, and BibTeX or APA-style citations.

## When to Use

- Search a known paper, author, category, or date range.
- Download an arXiv PDF or generate a citation.
- Don't use for broad topic discovery; use `web_search` with several focused queries.

## Commands

Run through `terminal` from this repository:

```bash
python3 .hermes/skills/research/cc-arxiv-arxiv/scripts/arxiv.py search --query 'au:Vaswani AND ti:attention' --max 5
python3 .hermes/skills/research/cc-arxiv-arxiv/scripts/arxiv.py search --ids 1706.03762
python3 .hermes/skills/research/cc-arxiv-arxiv/scripts/arxiv.py get 1706.03762 --dir ./papers
python3 .hermes/skills/research/cc-arxiv-arxiv/scripts/arxiv.py cite 1706.03762 --format bibtex
```

## Procedure

1. Select `search`, `get`, or `cite`; preserve an arXiv ID including its version suffix when supplied. Completion: command arguments match the requested operation.
2. Use `terminal` for the command. For a title-only lookup, start with `ti:"<title>"`; if no result is returned, retry once with `all:"<title>"`. Completion: captured output identifies the returned paper(s), or records no result.
3. Use `web_extract` on an abs or PDF URL when full content is needed. Completion: claims are grounded in retrieved paper content, not metadata alone.

## Query Syntax

Use `ti:`, `au:`, `abs:`, `cat:`, or `all:` and combine with `AND`, `OR`, or `ANDNOT`. Use `--from` and `--to` as `YYYY-MM-DD`; use `--sort-by relevance|lastUpdatedDate|submittedDate` and `--sort-order ascending|descending`.

## Verification

The command exits successfully and returns the requested metadata, saved PDF path, or citation. The bundled script has no third-party dependencies; run `python3 -m unittest discover -s cc-arxiv/tests` from the repository after changing it.
