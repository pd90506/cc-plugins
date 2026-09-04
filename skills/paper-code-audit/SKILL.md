---
name: paper-code-audit
description: Compare a paper's claims against its public codebase. Use when the user asks to audit a paper, check code-claim consistency, verify reproducibility of a specific paper, or find mismatches between a paper and its implementation.
---

# Paper-Code Audit

Apply this workflow to the paper and codebase the user asked to audit. Auto-surfaces when a request matches; the user can also invoke it explicitly with `/cc-arxiv:paper-code-audit`.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. If a call returns `Tool not found` or `Invalid URL`, do not retry it — map to a visible tool with valid arguments, or record the capability as blocked.

- **Papers (cc-arxiv).** Discover papers by topic with the alphaXiv MCP tool `discover_papers` (pass `keywords[]`, a `question`, and `difficulty` 1–10; optional `prioritize` and `published_after` / `published_before`); look up papers by author, category, title, id, or date with the `arxiv` skill's `search` command. Read a paper with `get_paper_content` (`url`; add `fullText: true` for the raw text); ask questions about a PDF with `answer_pdf_queries` (`paper`, `queries[]`); read a paper's linked GitHub repo with `read_files_from_github_repository` (`githubUrl`, `path`). Cite with the `arxiv` skill's `cite` command; fetch PDFs with its `get` command. The alphaXiv tools are registered as `mcp__plugin_cc-arxiv_alphaxiv__<tool>`. For any `arxiv` skill command, load the skill first (`Skill` tool, `cc-arxiv:arxiv`) so its script runs pre-approved.
- **Web.** Search with `WebSearch`; fetch a URL with `WebFetch` (one `url` plus a `prompt` per call; it returns an extracted summary, so quote only what it shows). Do not invent variants such as `search_web`, `fetch_url`, or `google_search`.
- **Delegation.** When the audit is non-trivial, delegate via the `Agent` tool (`subagent_type: general-purpose`), giving it a role (researcher / verifier) in its prompt and pointing it at the artifact file to write. Do not assume named bundled agents exist — describe the role in the task itself. Otherwise do the audit directly.
- **User questions.** To ask the user something, write plain chat text and wait for the next user message.

Derive a short slug from the audit target (lowercase, hyphens, no filler words, ≤5 words). Use this slug for all files in this run.

Requirements:
- Before starting, outline the audit plan: which paper, which repo, which claims to check. Write the plan to `outputs/.plans/<slug>.md`. Briefly summarize the plan to the user and continue immediately. Do not wait for confirmation unless the user explicitly asked to review the plan first.
- Extract the paper's claimed methods, defaults, metrics, and data handling with `get_paper_content` and `answer_pdf_queries`; read the actual implementation with `read_files_from_github_repository`.
- Delegate via the `Agent` tool (`subagent_type: general-purpose`) with a researcher role for evidence gathering and to another `Agent` call with a verifier role to verify sources and add inline citations when the audit is non-trivial.
- Compare claimed methods, defaults, metrics, and data handling against the actual code.
- Call out missing code, mismatches, ambiguous defaults, and reproduction risks.
- Save exactly one audit artifact to `outputs/<slug>-audit.md`.
- End with a `Sources` section containing paper and repository URLs; add BibTeX from the `arxiv` skill's `cite` command for the audited paper.
