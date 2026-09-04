---
name: research-review
description: Run a tough but constructive internal research critique of an AI research artifact. Use when the user asks for a review, critique, or feedback on a paper or draft, or wants to identify weaknesses before submission.
---

# Research Review

Apply this workflow to the artifact the user asked to review. Auto-surfaces when a request matches; the user can also invoke it explicitly with `/cc-arxiv:research-review`.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. If a call returns `Tool not found` or `Invalid URL`, do not retry it — map to a visible tool with valid arguments, or record the capability as blocked.

- **Papers (cc-arxiv).** Discover papers by topic with the alphaXiv MCP tool `discover_papers` (pass `keywords[]`, a `question`, and `difficulty` 1–10; optional `prioritize` and `published_after` / `published_before`); look up papers by author, category, title, id, or date with the `arxiv` skill's `search` command. Read a paper with `get_paper_content` (`url`; add `fullText: true` for the raw text); ask questions about a PDF with `answer_pdf_queries` (`paper`, `queries[]`); read a paper's linked GitHub repo with `read_files_from_github_repository` (`githubUrl`, `path`). Cite with the `arxiv` skill's `cite` command; fetch PDFs with its `get` command. The alphaXiv tools come from the separately connected alphaXiv MCP server (`mcp__alphaxiv__<tool>` in Claude Code; a connector-prefixed name in Cowork). If they are absent, tell the user to connect alphaXiv and fall back to the `arxiv` skill plus `WebFetch`. For any `arxiv` skill command, load the skill first (`Skill` tool, `cc-arxiv:arxiv`) so its script runs pre-approved.
- **Web.** Search with `WebSearch`; fetch a URL with `WebFetch` (one `url` plus a `prompt` per call; it returns an extracted summary, so quote only what it shows). Do not invent variants such as `search_web`, `fetch_url`, or `google_search`.
- **Delegation.** When the artifact is large, delegate via the `Agent` tool (`subagent_type: general-purpose`), giving it a role (researcher / reviewer) in its prompt and pointing it at the artifact file to write. Do not assume named bundled agents exist — describe the role in the task itself. Otherwise do the review directly.
- **User questions.** To ask the user something, write plain chat text and wait for the next user message.

This is an execution request, not a request to explain the workflow. Carry it out with tools and durable files. Do not answer by describing the protocol, saying what you would do, or stopping after a plan. Do not ask for confirmation. Briefly summarize the plan to the user and continue immediately unless the user explicitly asked to review the plan first.

Derive a short slug from the artifact name (lowercase, hyphens, no filler words, ≤5 words). Use this slug for all files in this run.

Required artifacts:
- Plan: `outputs/.plans/<slug>-review-plan.md`
- Evidence notes: `outputs/.drafts/<slug>-review-evidence.md`
- Final review: `outputs/<slug>-review.md`

Workflow:
1. Create `outputs/.plans`, `outputs/.drafts`, and `outputs`.
2. Write `outputs/.plans/<slug>-review-plan.md` with:
   - artifact identifier and source type (arXiv id, URL, local file, PDF, Markdown, etc.)
   - review criteria: novelty, empirical rigor, baselines, reproducibility, claims validity, figures/tables, metrics, related work, writing quality
   - verification checks needed for claims, figures, reported metrics, data/code availability, and linked artifacts
3. Continue immediately. Do not end after planning.
4. Inspect the artifact:
   - For local files, read or parse the file directly.
   - For arXiv ids or paper URLs, read the paper with `get_paper_content` and interrogate specific claims, metrics, or figures with `answer_pdf_queries`; record the source URL.
   - For a linked codebase, inspect it with `read_files_from_github_repository` when it materially affects the review. If a source cannot be parsed, record the failure and still produce a blocked or partial review artifact.
5. Write evidence notes to `outputs/.drafts/<slug>-review-evidence.md` before the final review. Include quoted/paraphrased claims, observed methods, reported metrics, baseline comparisons, reproducibility facts, and every inspected source path or URL.
6. Delegate via the `Agent` tool (`subagent_type: general-purpose`) with a researcher role and/or a reviewer role only when the artifact is large enough to benefit from delegation. Otherwise do the lead-owned review directly. Never merely say an `Agent` call was made; either delegate for real or continue yourself.
7. Write exactly one final review artifact to `outputs/<slug>-review.md` with:
   - Summary Assessment
   - Strengths
   - Critical Issues
   - Major Issues
   - Minor Issues
   - Reproducibility and Verification
   - Inline Annotations tied to sections, claims, figures, or tables where possible
   - Recommendation
   - Sources
8. If the artifact cannot be parsed or critical evidence is unavailable, still write `outputs/<slug>-review.md`. Mark affected sections with `Verification: BLOCKED`, explain exactly what failed, and distinguish blocked checks from actual paper weaknesses.
9. Before responding, verify on disk that `outputs/<slug>-review.md` exists. If it does not, create it immediately as a blocked review artifact with the failure reason.

Never end with planning-only chat. Never ask what to do next. Never claim the review is complete unless `outputs/<slug>-review.md` exists.
