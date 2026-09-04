---
name: source-comparison
description: Compare multiple sources on a topic and produce a grounded comparison matrix. Use when the user asks to compare papers, tools, approaches, frameworks, or claims across multiple sources.
---

# Source Comparison

Apply this workflow to the sources or topic the user asked to compare. Auto-surfaces when a request matches; the user can also invoke it explicitly with `/cc-arxiv:source-comparison`.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. If a call returns `Tool not found` or `Invalid URL`, do not retry it — map to a visible tool with valid arguments, or record the capability as blocked.

- **Papers (cc-arxiv).** Discover papers by topic with the alphaXiv MCP tool `discover_papers` (pass `keywords[]`, a `question`, and `difficulty` 1–10; optional `prioritize` and `published_after` / `published_before`); look up papers by author, category, title, id, or date with the `arxiv` skill's `search` command. Read a paper with `get_paper_content` (`url`; add `fullText: true` for the raw text); ask questions about a PDF with `answer_pdf_queries` (`paper`, `queries[]`); read a paper's linked GitHub repo with `read_files_from_github_repository` (`githubUrl`, `path`). Cite with the `arxiv` skill's `cite` command; fetch PDFs with its `get` command. The alphaXiv tools are registered as `mcp__plugin_cc-arxiv_alphaxiv__<tool>`. For any `arxiv` skill command, load the skill first (`Skill` tool, `cc-arxiv:arxiv`) so its script runs pre-approved.
- **Web.** Search with `WebSearch`; fetch a URL with `WebFetch` (one `url` plus a `prompt` per call; it returns an extracted summary, so quote only what it shows). Do not invent variants such as `search_web`, `fetch_url`, or `google_search`.
- **Delegation.** When the source set is broad, delegate via the `Agent` tool (`subagent_type: general-purpose`), giving it a role (researcher / verifier) in its prompt and pointing it at the artifact file to write. Do not assume named bundled agents exist — describe the role in the task itself. For a small set, do the work directly.
- **User questions.** To ask the user something, write plain chat text and wait for the next user message.

Derive a short slug from the comparison topic (lowercase, hyphens, no filler words, ≤5 words). Use this slug for all files in this run.

Requirements:
- Before starting, outline the comparison plan: which sources to compare, which dimensions to evaluate, expected output structure. Write the plan to `outputs/.plans/<slug>.md`. Briefly summarize the plan to the user and continue immediately. Do not wait for confirmation unless the user explicitly asked to review the plan first.
- Delegate via the `Agent` tool (`subagent_type: general-purpose`) with a researcher role to gather source material when the comparison set is broad, and to another `Agent` call with a verifier role to verify sources and add inline citations to the final matrix. Use `discover_papers` / the `arxiv` skill's `search` command to find the sources and `get_paper_content` / `answer_pdf_queries` to read them.
- Build a comparison matrix covering: source, key claim, evidence type, caveats, confidence.
- Use Mermaid for method or architecture comparisons when the structure is source-supported; otherwise use a source-backed table.
- Distinguish agreement, disagreement, and uncertainty clearly.
- Save exactly one comparison to `outputs/<slug>-comparison.md`.
- End with a `Sources` section containing direct URLs for every source used; add BibTeX from the `arxiv` skill's `cite` command for arXiv papers where formal references help.
