---
name: read-paper
description: Read a whole research-paper PDF end to end and transcribe it into notes — every equation as LaTeX, every table as Markdown, figures saved as PNG, each page-cited. Use when asked to read, summarize, or extract a paper PDF's math, tables, or figures, or when copied PDF text has garbled equations, misaligned table columns, or figures that carry meaning in pixels.
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/readpaper.py *)
---

# Read Paper

The text layer of a paper extracts cleanly for prose, headings, and reference lists — but it returns an equation as scattered glyph fragments, a table as columns collapsed into one stream, and a figure as its caption alone (the diagram, the plot's trend, the axis values live in pixels). So work in **two tiers**: pull the text layer first for everything it handles well, and **render pixels only for what it garbles** — equations, tables, figures, and any page whose text is empty or not self-contained. Do not render every page by reflex; match the effort to the request.

`readpaper.py` (at `${CLAUDE_SKILL_DIR}/readpaper.py`) uses PyMuPDF, installing it on first run if missing and falling back to `pypdf` + macOS `sips` if that install fails. It extracts the text layer per page (`text`), renders whole pages for a page-by-page read (`pages`), and crops individual figures and tables (`find`, `crop`).

**Prefer arXiv LaTeX source over any PDF.** If the paper is on arXiv, its LaTeX gives cleaner equations than pixel transcription ever will: find it with the `arxiv` skill's `search` command, and read the report with `get_paper_content` / pin a claim with `answer_pdf_queries`. Drop to this PDF flow when there is no source, the file is local, or you must verify the typeset original.

**`Read` can open a PDF directly** (a whole file up to 10 pages, longer ones via `pages` ranges of up to 20). That is the quickest first look at a short paper. Use `readpaper.py` when you need per-page text with page citations, figure and table crops, or control over DPI.

## What the text layer settles, and what needs pixels

The text layer is trustworthy for **prose, section text, and reference lists** — quote and summarize those from `text` output with page numbers, no rendering needed. It is **not** trustworthy for **equations** (glyph scatter), **tables** (columns collapse into one stream), or **figures** (meaning is in pixels). Those, and any numeric value read from inside a table or plot, are **eyes-on**: a figure, table, or equation may be stated as fact only once rendered to PNG and viewed with the `Read` tool. A number lifted from a collapsed table stream, or a figure described from its caption alone, is paraphrase — label it and verify it in pixels before asserting it. This is the honesty rule the skill turns on.

## Steps

1. **Probe.** `python3 ${CLAUDE_SKILL_DIR}/readpaper.py probe <pdf>` — page count and every figure/table/algorithm caption with its page number. This is the index; work from it rather than scrolling by eye. No captions on a scanned PDF means there is no text layer — the `text` pass will return empty, so render every page and treat every number as image-read.
2. **Text pass first.** `python3 ${CLAUDE_SKILL_DIR}/readpaper.py text <pdf>` prints the whole text layer, `## Page N`-cited, to stdout; `-r 3-8` limits the range. Read it. For a summary, a prose question, or the reference list, this is usually all you need — stop here and answer, citing page numbers. For a long paper that would overflow the console, add `-o <file>` pointed at a scratch path (e.g. `"$TMPDIR/text.md"`), not your repo, then `Read` it. Pages that print `(no extractable text ...)` are scanned or vector and must be rendered.
3. **Escalate to pixels only where the text failed or the answer needs it.** Render a page when its equations, a table, or a figure matter to the request — not by default. `python3 ${CLAUDE_SKILL_DIR}/readpaper.py pages <pdf> -r 7-8` renders a range to the scratch temp dir and prints each path; `page <pdf> N -d 300` or `crop` re-renders tighter when subscripts or a dense table are unreadable. Open each printed PNG with `Read`, transcribe equations to LaTeX (`$...$` inline, `$$...$$` display, KaTeX-compatible) and tables to Markdown, each with its page number.
4. **Crop the figures and tables you cite.** `python3 ${CLAUDE_SKILL_DIR}/readpaper.py find <pdf> "Figure 3"` locates the caption, unions the artwork around it, saves the crop to the scratch temp dir, and prints its path. Open it with `Read` and record what only the image carries — axis ranges and tick values, trend direction, arrow direction, icon meaning (frozen vs. trainable), color legends, which cells are bold. Keep the PNG; it is the figure output.
5. **Cross-check the numbers.** For any figure or table value, the rendered page is authoritative over the collapsed text stream; report any mismatch as an extraction discrepancy.

Done when the request is answered with page-cited evidence: prose and references from the text pass, and every equation, table, and figure you assert as fact rendered eyes-on with its page number. Name any page or figure that could not be rendered as unread.

## Commands

Invoke as `python3 ${CLAUDE_SKILL_DIR}/readpaper.py <command>`; `--help` carries the full interface. Pages are 1-based; output paths print to stdout — pass them to `Read`.

| Command | Purpose |
|---|---|
| `probe <pdf>` | pages, size, and all captions with page numbers |
| `text <pdf> [-r A-B] [-o FILE]` | extract the text layer per page, `## Page N`-cited (stdout, or `-o` to a file) |
| `pages <pdf> [-r A-B] [-o DIR] [-d DPI]` | render each page in a range (default all, 170) to DIR |
| `find <pdf> "Figure 3" [-o DIR] [-d DPI]` | locate a caption and crop its figure or table (350) |
| `page <pdf> N [-d DPI]` | whole page (200) |
| `crop <pdf> N -b x0,y0,x1,y1 [-d DPI]` | one region (400) |
| `sweep <pdf> N [-d DPI]` | page as 4 overlapping horizontal bands (120) |

`-o DIR` sets the output directory. **It defaults to a temp scratch dir, so nothing lands in the working repo** — every command prints the path it wrote. Pass `-o <dir>` only when the user explicitly wants the figures and text kept somewhere specific (and prefer a path outside the repo unless they ask for one inside it).

### Crop boxes and DPI

`-b x0,y0,x1,y1` are fractions of the page, origin **top-left**: full page `0,0,1,1`, left column `0,0,0.5,1`, top third `0,0,1,0.33`, bottom-right quadrant `0.5,0.5,1,1`. The `Read` tool downsamples wide images to ~2000 px, so DPI and crop size trade off — crop tighter to read smaller type rather than raising DPI on a whole page. Use 120–150 to locate content, 200–350 for a table or full-column figure, 400–600 for axis tick labels or small annotations.

## Gotchas

- **The `text` pass follows PyMuPDF reading order**, which is right for single- and most two-column papers but can interleave lines in heavy multi-column or boxed layouts. If the prose reads out of order, render that page instead of trusting the stream.
- **`find` warns `no artwork bounds detected`** (to stderr) when it cannot locate the artwork and falls back to a fixed span past the caption. That crop is a guess — check it and re-crop by hand with `page` then `crop`.
- **`find` takes the first caption matching the label**, so a "Figure 3" repeated in an appendix needs a manual crop.
- **Vector figures hold no extractable bitmap** — plots and diagrams are drawn as vectors, so image extraction returns nothing. Rendering the page is what works, which is why this skill rasterizes rather than extracts.
- **Table rules are zero-height lines**; the engine unions them per-axis so tables do not silently vanish. A blank crop means the box was off-page, not that the region was empty.
- **Equations rarely transcribe perfectly from pixels.** Verify structure — subscripts, limits, fractions — against the rendered page.

## Reporting

Report what the paper shows, not whether the work is good — keep evidence separate from judgement; the **eyes-on** rule governs what may be stated as fact.
