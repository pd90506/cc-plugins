---
name: deep-research
description: Run a thorough, source-heavy investigation on any topic. Use when the user asks for deep research, a comprehensive analysis, an in-depth report, or a multi-source investigation. Produces a cited research brief with provenance tracking.
---

# Deep Research

Apply this workflow to the topic the user asked to research. Auto-surfaces when a request matches; the user can also invoke it explicitly with `/cc-arxiv:deep-research`.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. If a call returns `Tool not found` or `Invalid URL`, do not retry it — map to a visible tool with valid arguments, or record the capability as blocked.

- **Papers (cc-arxiv).** Discover papers by topic with the alphaXiv MCP tool `discover_papers` (pass `keywords[]`, a `question`, and `difficulty` 1–10; optional `prioritize` and `published_after` / `published_before`); look up papers by author, category, title, id, or date with the `arxiv` skill's `search` command. Read a paper with `get_paper_content` (`url`; add `fullText: true` for the raw text); ask questions about a PDF with `answer_pdf_queries` (`paper`, `queries[]`); read a paper's linked GitHub repo with `read_files_from_github_repository` (`githubUrl`, `path`). Cite with the `arxiv` skill's `cite` command; fetch PDFs with its `get` command. The alphaXiv tools are registered as `mcp__plugin_cc-arxiv_alphaxiv__<tool>`. For any `arxiv` skill command, load the skill first (`Skill` tool, `cc-arxiv:arxiv`) so its script runs pre-approved.
- **Web.** Search with `WebSearch`; fetch a URL with `WebFetch` (one `url` plus a `prompt` per call; it returns an extracted summary, so quote only what it shows). Do not invent variants such as `search_web`, `fetch_url`, or `google_search`.
- **Delegation.** When decomposition clearly helps, delegate to one or more `Agent` calls (`subagent_type: general-purpose`), giving each a role (researcher / verifier / reviewer) in its prompt and pointing it at the artifact file to write. Do not assume named bundled agents exist — describe the role in the task itself. Spawn one `Agent` role at a time; do not run a verifier and a reviewer in the same call.
- **User questions.** To ask the user something, write plain chat text and wait for the next user message.

This is an execution request, not a request to explain the workflow. Execute it. Your first actions should be tool calls that create directories and write the plan artifact.

## Required Artifacts

Derive a short slug from the topic: lowercase, hyphenated, no filler words, at most 5 words.

Every run must leave these files on disk:
- `outputs/.plans/<slug>.md`
- `outputs/.drafts/<slug>-draft.md`
- `outputs/.drafts/<slug>-cited.md`
- `outputs/<slug>.md` or `papers/<slug>.md`
- `outputs/<slug>.provenance.md` or `papers/<slug>.provenance.md`

After the user approves the plan, if a tool call fails at runtime, continue and still write a blocked or partial final output and provenance sidecar rather than stopping. Never end with chat-only output after plan approval. Use `Verification: BLOCKED` when verification could not be completed.

## Step 1: Plan

Create `outputs/.plans/<slug>.md` immediately. The plan must include: key questions, evidence needed, scale decision, task ledger, verification log, decision log.

Make the scale decision before assigning owners. If the topic is a narrow "what is X" explainer, use lead-owned direct search tasks only; do not allocate researcher `Agent` calls in the task ledger. If a memory tool is visible, optionally record the plan there; otherwise continue without it.

After writing the plan, stop and ask for explicit confirmation before gathering evidence. Summarize the plan briefly and ask:

`Proceed with this deep research plan? Reply "yes" to continue, or tell me what to change.`

Do not run searches, fetch sources, delegate, draft, cite, review, or deliver until the user confirms. If the user requests changes, update `outputs/.plans/<slug>.md` first, then ask again.

## Step 2: Scale

Use direct search for a single fact or narrow question (including "what is X" explainers), or work you can answer with 3–10 tool calls. For "what is X" topics you MUST NOT delegate researcher `Agent` calls unless the user explicitly asks for comprehensive coverage, current landscape, benchmarks, or production deployment.

Delegate only when decomposition clearly helps: a direct comparison of 2–3 items (2 researcher `Agent` calls), a broad survey (3–4), or complex multi-domain research (4–6). Spawn them as separate `Agent` calls.

## Step 3: Gather Evidence

Use only visible tool names. Prefer paper metadata, abstracts, and HTML pages via `discover_papers`, `WebSearch`, and `WebFetch`; use `get_paper_content` / `answer_pdf_queries` when you need a paper's contents, and `read_files_from_github_repository` for a linked repo. If a fetch or PDF read fails, cite the source URL from search metadata and mark full-text extraction as blocked instead of retrying.

If direct search was chosen: skip delegation, search and fetch yourself, use at least 3 distinct queries (definition/history, mechanism/formula, current usage/comparison), record the exact search terms and notes in `outputs/.drafts/<slug>-research-direct.md`, then continue to synthesis.

If `Agent` delegation was chosen: write a per-researcher brief first (e.g. `outputs/.plans/<slug>-T1.md`), keep each `Agent` task small and role-scoped in its prompt, point each at a distinct output file (e.g. `outputs/.drafts/<slug>-research-web.md`), and do not name exact tool commands unless those tools are visible. After gathering, update the plan ledger and verification log; if research failed, record what failed and proceed with a blocked or partial draft.

## Step 4: Draft

Write the report yourself; do not delegate synthesis. Save to `outputs/.drafts/<slug>-draft.md`. Include an executive summary, findings organized by question/theme, evidence-backed caveats and disagreements, and open questions. Invent no sources, results, figures, benchmarks, or tables. Before citation, sweep the draft: every critical claim, number, figure, table, or benchmark must map to a source URL, research note, or command output; remove or downgrade unsupported claims; mark inferences as inferences.

## Step 5: Cite

If direct search was chosen: cite yourself. Verify reachable HTML/doc URLs with `WebFetch`, add BibTeX from the `arxiv` skill's `cite` command for arXiv papers, and write `outputs/.drafts/<slug>-cited.md` with inline citations and a Sources section. Do not delegate for simple direct-search runs.

If `Agent` delegation was used: after the draft exists, delegate via the `Agent` tool (`subagent_type: general-purpose`) with a verifier role to add inline citations using the research files as source material, verify every URL, and write the complete cited brief to `outputs/.drafts/<slug>-cited.md`. After it returns, verify on disk that the cited file exists; if the agent wrote elsewhere, move or copy it into place.

## Step 6: Review

If direct search was chosen: review the cited draft yourself, write `outputs/.drafts/<slug>-verification.md` with FATAL / MAJOR / MINOR findings, and fix FATAL issues before delivery. Do not delegate for simple direct-search runs.

If `Agent` delegation was used: only after `outputs/.drafts/<slug>-cited.md` exists, delegate via the `Agent` tool (`subagent_type: general-purpose`) with a reviewer role to flag unsupported claims, logical gaps, single-source critical claims, and overstated confidence — a verification pass, not a peer review. If it flags FATAL issues, fix them and run one more review pass; note MAJOR issues in Open Questions; accept MINOR issues.

When applying fixes, use small localized edits for 1–3 simple corrections; for larger rewrites, read the cited draft and write a corrected full file to `outputs/.drafts/<slug>-revised.md`. After applying fixes, prove on disk (with `rg`/`grep`/a targeted read) that the old wording is gone and the replacement exists before claiming the fix landed. The final candidate is `outputs/.drafts/<slug>-revised.md` if it exists, else `outputs/.drafts/<slug>-cited.md`.

## Step 7: Deliver

Copy the final candidate to `papers/<slug>.md` (paper-style drafts) or `outputs/<slug>.md` (everything else). Write provenance next to it as `<slug>.provenance.md`:

```markdown
# Provenance: [topic]

- **Date:** [date]
- **Rounds:** [number of research rounds]
- **Sources consulted:** [count and/or list]
- **Sources accepted:** [count and/or list]
- **Sources rejected:** [dead, unverifiable, or removed]
- **Verification:** [PASS / PASS WITH NOTES / BLOCKED]
- **Plan:** outputs/.plans/<slug>.md
- **Research files:** [files used]
```

Before responding, verify on disk that all required artifacts exist and that any fix claimed in the provenance is reflected in the final candidate (run a targeted `rg`/`grep` for removed and corrected content). Set `Verification: BLOCKED` or `PASS WITH NOTES` if checks could not complete. Keep the final response brief: link the final file, the provenance file, and any blocked checks.
