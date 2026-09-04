---
name: literature-review
description: Run a literature review using paper search and primary-source synthesis. Use when the user asks for a lit review, paper survey, state of the art, or academic landscape summary on a research topic, lab, PI, or author.
---

# Literature Review

Apply this workflow to the topic, lab, PI, or author the user asked to review. Auto-surfaces when a request matches; the user can also invoke it explicitly with `/cc-arxiv:literature-review`.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. If a call returns `Tool not found` or `Invalid URL`, do not retry it — map to a visible tool with valid arguments, or record the capability as blocked.

- **Papers (cc-arxiv).** Discover papers by topic with the alphaXiv MCP tool `discover_papers` (pass `keywords[]`, a `question`, and `difficulty` 1–10; optional `prioritize` and `published_after` / `published_before`); look up papers by author, category, title, id, or date with the `arxiv` skill's `search` command. Read a paper with `get_paper_content` (`url`; add `fullText: true` for the raw text); ask questions about a PDF with `answer_pdf_queries` (`paper`, `queries[]`); read a paper's linked GitHub repo with `read_files_from_github_repository` (`githubUrl`, `path`). Cite with the `arxiv` skill's `cite` command; fetch PDFs with its `get` command. The alphaXiv tools come from the separately connected alphaXiv MCP server (`mcp__alphaxiv__<tool>` in Claude Code; a connector-prefixed name in Cowork). If they are absent, tell the user to connect alphaXiv and fall back to the `arxiv` skill plus `WebFetch`. For any `arxiv` skill command, load the skill first (`Skill` tool, `cc-arxiv:arxiv`) so its script runs pre-approved.
- **Web.** Search with `WebSearch`; fetch a URL with `WebFetch` (one `url` plus a `prompt` per call; it returns an extracted summary, so quote only what it shows). Do not invent variants such as `search_web`, `fetch_url`, or `google_search`.
- **Delegation.** When the sweep is wide, delegate via the `Agent` tool (`subagent_type: general-purpose`), giving it a role (researcher / verifier / reviewer) in its prompt and pointing it at the artifact file to write. Do not assume named bundled agents exist — describe the role in the task itself. For narrow topics, do the work directly.
- **User questions.** To ask the user something, write plain chat text and wait for the next user message.

This is an execution request, not a request to explain the workflow. Carry it out with tools and durable files. Do not answer by describing the protocol or stopping after a plan.

Derive a short slug from the topic (lowercase, hyphens, no filler words, ≤5 words). Use this slug for all files in this run.

## Workflow

1. **Plan** — Outline the scope: key questions, source types (papers, web, repos), time period, expected sections, and a small task ledger plus verification log. When the input names a lab, PI, author, institution lab page, or author profile, run it as a publication-corpus review: resolve the lab/author identity first, collect the reachable publication list, then map the research trajectory across that corpus. Write the plan to `outputs/.plans/<slug>.md`. Briefly summarize the plan to the user and continue immediately. Do not wait for confirmation unless the user explicitly asked to review the plan first.
2. **Gather** — Delegate via the `Agent` tool (`subagent_type: general-purpose`) with a researcher role when the sweep is wide enough to benefit from delegated paper triage before synthesis; its notes go to `outputs/.drafts/<slug>-research-*.md`. For narrow topics, search directly. Lean on `discover_papers` for topic discovery, the `arxiv` skill's `search` command for known-item/author lookups, and `get_paper_content` / `answer_pdf_queries` to read and interrogate specific papers. For publication-corpus reviews, the lead agent owns identity resolution and writes `outputs/.drafts/<slug>-publications.md` with reachable titles, years, venues, URLs/DOIs, and gaps before delegating trajectory synthesis. Prefer lab publication pages, author profiles, arXiv/OpenReview pages, and paper-search results that expose stable source URLs. Do not silently skip assigned questions; mark them `done`, `blocked`, or `superseded`.
3. **Synthesize** — Separate consensus, disagreements, and open questions. For publication-corpus reviews, also identify 3–5 research trajectories and the 3–5 papers that most changed the corpus direction; rank by contrastive originality, methodology strength, and relationship to prior art rather than author prestige. Use Mermaid diagrams for taxonomies, method pipelines, or trajectory maps when the structure is source-supported and changes the reader's research decision. Keep the output to research evidence, source coverage, and next research decisions.
4. **Cite** — Delegate via the `Agent` tool (`subagent_type: general-purpose`) with a verifier role to add inline citations and verify every source URL in the draft. Generate BibTeX for arXiv papers with the `arxiv` skill's `cite` command where formal references help.
5. **Verify** — Delegate via the `Agent` tool (`subagent_type: general-purpose`) with a reviewer role to check the cited draft for unsupported claims, logical gaps, zombie sections, and single-source critical findings. Fix FATAL issues before delivering. Note MAJOR issues in Open Questions. If FATAL issues were found, run one more verification pass after the fixes.
6. **Deliver** — Save the final literature review to `outputs/<slug>.md`. Write a provenance record alongside it as `outputs/<slug>.provenance.md` listing: date, sources consulted vs. accepted vs. rejected, verification status, and intermediate research files used; for publication-corpus reviews, include the publication-log path and unresolved corpus gaps. Before you stop, verify on disk that both files exist; do not stop at an intermediate cited draft alone.
