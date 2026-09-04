---
name: arxiv
description: Search arXiv by author, title, id, category, or date range; download a paper's PDF; or produce BibTeX / APA citations. Use for known-item and field lookups ("papers by Hinton", "cat:cs.LG since 2024", "cite 1706.03762", "download 2101.00001"). For open-ended topic discovery ("papers about X") prefer the alphaXiv discover_papers MCP tool instead.
argument-hint: "<query or arXiv id>"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/arxiv.py *)
---

# arXiv

A dependency-free script at `${CLAUDE_SKILL_DIR}/scripts/arxiv.py` talks to the arXiv API. Run it with Bash; it needs only `python3`.

If this skill was invoked with arguments (`$ARGUMENTS`), treat them as a search: an arXiv id or URL means `search --ids`, anything else is a `--query`. Show the results and stop.

## Commands

| Command | Purpose |
|---|---|
| `search --query "<q>" [--max N] [--start N] [--sort-by relevance\|lastUpdatedDate\|submittedDate] [--sort-order ascending\|descending] [--from YYYY-MM-DD] [--to YYYY-MM-DD]` | field search; up to 100 results (default 10) |
| `search --ids <id> [<id> ...]` | fetch specific papers by id or URL |
| `get <id|url> [--dir DIR] [--filename NAME]` | download the PDF as `<id> - <title>.pdf` (default dir `~/Downloads/arxiv`) |
| `cite <id|url> [<id> ...] [--format bibtex\|text]` | BibTeX (default) or APA-style text |

Example:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/arxiv.py search --query "au:Vaswani AND ti:attention" --max 5
```

## Query syntax

Field prefixes: `ti:` title, `au:` author, `abs:` abstract, `cat:` category (e.g. `cs.LG`), `all:` any field. Combine with `AND`, `OR`, `ANDNOT`; quote phrases with `"`. Date filters (`--from`, `--to`) are added as a `submittedDate` clause. Ids accept `1706.03762`, `1706.03762v7`, `arXiv:1706.03762`, `cond-mat/0011267`, or any `arxiv.org/abs|pdf` URL.

## When to use what

- **This skill:** the user names an author, title, id, category, or date range, wants a PDF on disk, or wants a citation.
- **alphaXiv `discover_papers`** (MCP tool `mcp__plugin_cc-arxiv_alphaxiv__discover_papers`): natural-language topic discovery. Pass `keywords[]`, a `question`, and `difficulty` 1–10.
- After `get`, read the PDF with `Read`, or with the `read-paper` skill when equations, tables, or figures matter.

Each result lists the id, primary category, date, authors, abs and pdf URLs, and a trimmed abstract. Quote ids exactly, including any version suffix.
