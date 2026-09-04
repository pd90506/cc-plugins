---
name: read-pdf
description: Read any PDF — invoice, form, slide deck, manual, contract, report, scanned page — into Markdown: text and tables as Markdown, images and charts saved as PNG. Use when asked to read a PDF's text, fields, tables, or figures, or when copied PDF text comes out garbled, mis-columned, or empty. For academic-paper PDFs (equations, captioned figures, page citations) use read-paper instead.
---

# Read PDF

A PDF's text layer collapses a table into one stream, reads a two-column page top-to-bottom across both columns, and returns a chart or scanned page as nothing at all — the layout, the numbers in the cells, the trend in the plot live in pixels. The fix is to **render the pages and read the pixels**, transcribing what you see into Markdown.

`readpdf.py` (this skill's directory) renders with PyMuPDF, installing it on first run if missing and falling back to `pypdf` + macOS `sips` if that install fails. It dumps the text layer (`text`), renders whole pages (`pages`, `page`), and crops regions (`crop`) — one engine for every document type.

## Eyes-on

A table, figure, chart, or form field is **eyes-on** once rendered to PNG and viewed with the `read` tool. Only eyes-on content may be stated as fact. Anything taken from the text-layer dump is paraphrase — fine for prose, but label any figure or number drawn from it as "from the text layer" until you have seen the page. This is the honesty rule the whole skill turns on.

## Steps

1. **Probe.** `python3 readpdf.py probe <pdf>` — page count, size, and whether a text layer is present. This picks the path:
   - **Text layer present (born-digital)** — take the fast path. `python3 readpdf.py text <pdf> -o notes/text.md` dumps the layer, page-delimited, as the base of your read. Then render only the pages that carry a table, figure, chart, form, or text that came out garbled or mis-columned.
   - **No text layer (scanned/image-only)** — there is nothing to dump; render every page and read the pixels. Treat every field and number as image-read and say so. (Heavier opt-in: `brew install ocrmypdf tesseract`, then `ocrmypdf in.pdf out.pdf` adds a text layer for a re-`probe` — vision-read stays the default and needs nothing installed.)
2. **Render the pages you need.** `python3 readpdf.py pages <pdf> -o notes/pages` renders the whole document (default 170 DPI); `-r 3-8` limits the range. For a long document render and read in ranges rather than dumping every page into context at once.
3. **Read and transcribe.** Open each page PNG with `read` and write Markdown: prose to a running summary, **key-value documents (invoices, receipts, forms) as labeled fields** (`Total: $42.00`), tables to Markdown tables, and any math to LaTeX (`$...$` inline, `$$...$$` display, KaTeX-compatible). On a multi-column or mixed layout, read the column order off the rendered page — left column fully, then right. Re-render a page tighter (`page <pdf> N -d 300`, or `crop`) when small type or a dense table is unreadable.
4. **Crop the images and tables you rely on.** `python3 readpdf.py crop <pdf> N -b x0,y0,x1,y1 -o notes/figures` saves the region as PNG. Open it with `read` and record what only the pixels carry — axis ranges and tick values, trend direction, which cells are bold, a logo or stamp, a signature. Keep the PNG; it is the image output.
5. **Cross-check.** On a born-digital PDF, compare each transcribed number against the text-layer dump; the rendered page is authoritative, so report any mismatch as an extraction discrepancy.

Done when every table, figure, and form field you rely on is eyes-on, the transcription is saved (Markdown text and tables, images as PNG), and any page that could not be rendered is named as unread.

## Commands

Run from this skill's directory; `--help` carries the full interface. Pages are 1-based; output paths print to stdout — pass them to `read`.

| Command | Purpose |
|---|---|
| `probe <pdf>` | pages, size, text-layer presence, and any captions |
| `text <pdf> [-r A-B] [-o FILE]` | dump the text layer, page-delimited (born-digital fast path) |
| `pages <pdf> [-r A-B] [-o DIR] [-d DPI]` | render each page in a range (default all, 170) to DIR |
| `page <pdf> N [-d DPI]` | whole page (200) |
| `crop <pdf> N -b x0,y0,x1,y1 [-d DPI]` | one region (400) |
| `find <pdf> "Figure 3" [-o DIR] [-d DPI]` | locate a caption and crop its figure or table (350) |
| `sweep <pdf> N [-d DPI]` | page as 4 overlapping horizontal bands (120) |

`-o DIR` sets the output directory (default a temp dir) — point `pages` and `crop` at your notes folder so the images land beside the write-up.

### Crop boxes and DPI

`-b x0,y0,x1,y1` are fractions of the page, origin **top-left**: full page `0,0,1,1`, left column `0,0,0.5,1`, top third `0,0,1,0.33`, bottom-right quadrant `0.5,0.5,1,1`. The `read` tool downsamples wide images to ~2000 px, so DPI and crop size trade off — crop tighter to read smaller type rather than raising DPI on a whole page. Use 120–150 to locate content, 200–350 for a table or full-column figure, 400–600 for axis tick labels or fine print.

## Gotchas

- **Vector charts and diagrams hold no extractable bitmap** — image extraction returns nothing for vector art, so rasterize the page. This is why the skill renders rather than extracts.
- **Table rules are zero-height lines**; the engine unions them per-axis so tables do not silently vanish. A blank crop means the box was off-page, not that the region was empty.
- **Text-layer column bleed** — a born-digital `text` dump of a two-column page can interleave the columns; the rendered page shows the true reading order.
- **`find` is caption-oriented** (figure/table labels) and less useful on general documents; reach for `crop` with a fraction box to grab any region by position.
