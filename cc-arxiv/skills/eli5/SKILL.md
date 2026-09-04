---
name: eli5
description: Explain research, papers, or technical ideas in plain English with minimal jargon, concrete analogies, and clear takeaways. Use when the user says "ELI5 this", asks for a simple explanation of a paper or research result, or wants jargon removed.
---

# ELI5

Explain, in plain English, the paper or topic the user asked about. Auto-surfaces when a request matches; the user can also invoke it explicitly with `/cc-arxiv:eli5`.

## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. If a call returns `Tool not found`, map to a visible tool or say so plainly — do not retry the same invalid call.

- **Papers (cc-arxiv).** When the user names a specific paper, arXiv id, DOI, or paper URL, find it with the `arxiv` skill's `search` command (known-item) or the alphaXiv MCP tool `discover_papers` (topic; pass `keywords[]`, `question`, `difficulty`; optional `prioritize`, `published_after` / `published_before`) and read it with `get_paper_content`; use `answer_pdf_queries` to pin down a specific claim, method, or number. The alphaXiv tools come from the separately connected alphaXiv MCP server (`mcp__alphaxiv__<tool>` in Claude Code; a connector-prefixed name in Cowork). If they are absent, tell the user to connect alphaXiv and fall back to the `arxiv` skill plus `WebFetch`.
- **Web.** For non-paper topics, use `WebSearch` and `WebFetch` if you need to ground a detail. Do not invent tool-name variants.

If the input names a paper, arXiv id, DOI, or URL, anchor the explanation on that paper. If it gives only a topic, identify 1–3 representative papers and anchor on the clearest or most important one.

Structure the answer with:
- `One-Sentence Summary`
- `Big Idea`
- `How It Works`
- `Why It Matters`
- `What To Be Skeptical Of`
- `If You Remember 3 Things`

Guidelines:
- Use short sentences and concrete words. Define jargon immediately or remove it.
- Prefer one good analogy over several weak ones.
- Separate what the paper actually shows from speculation or interpretation.
- Keep the explanation inline in chat unless the user explicitly asks to save it as an artifact.
