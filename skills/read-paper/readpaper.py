#!/usr/bin/env python3
"""Render PDF paper pages and regions to PNG so a vision model can read them.

Uses PyMuPDF when present and installs it on first run if missing. Falls back to
pypdf + macOS `sips` if that install fails, so rendering still works offline.

Commands:
  probe <pdf>                    pages, size, and detected figure/table captions
  text  <pdf> [-r A-B] [-o F]    extract the text layer (prose + references) per page
  pages <pdf> [-r A-B] [-o DIR]  render each page in a range (default all) to DIR
  page  <pdf> N [-d DPI]         render whole page N (1-based)
  find  <pdf> "Figure 3" [-o D]  locate a caption and crop its figure or table
  crop  <pdf> N -b x0,y0,x1,y1   render a region of page N
  sweep <pdf> N [-d DPI]         render page N as 4 overlapping horizontal bands

Crop boxes are FRACTIONS of the page, origin TOP-LEFT, as x0,y0,x1,y1 in [0,1].
Top-left quadrant is `-b 0,0,0.5,0.5`; left column is `-b 0,0,0.5,1`.

`pages` renders the whole paper for a page-by-page read; `-o figures` saves crops
(from `find`) or pages next to your notes. Default output is a temp dir.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

OUTDIR = os.path.join(tempfile.gettempdir(), "readpaper")
CAPTION_RE = re.compile(r"^(Figure|Fig\.?|Table|Algorithm)\s+([0-9]+|[IVXL]+)", re.I)


# ---------------------------------------------------------------- dependencies

def ensure_pymupdf(quiet=False):
    """Import PyMuPDF, installing it on first run if absent. None if unavailable."""
    try:
        import fitz
        return fitz
    except ImportError:
        pass
    # 1.28+ requires Python >=3.10; older interpreters need the last 3.9 wheel.
    spec = "pymupdf" if sys.version_info >= (3, 10) else "pymupdf<1.27"
    if not quiet:
        print("PyMuPDF not found - installing %s (first run only)..." % spec,
              file=sys.stderr)
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", spec],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if not quiet:
            print("install failed; falling back to sips renderer.\n%s"
                  % (r.stderr or r.stdout)[-400:], file=sys.stderr)
        return None
    import site
    for p in (site.getusersitepackages(),):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import fitz
        if not quiet:
            print("PyMuPDF installed.", file=sys.stderr)
        return fitz
    except ImportError:
        return None


def _pypdf():
    try:
        import pypdf
        return pypdf
    except ImportError:
        sys.exit("neither PyMuPDF nor pypdf available: pip3 install --user pymupdf")


def _outpath(pdf, page_no, tag, outdir=None):
    d = outdir or OUTDIR
    os.makedirs(d, exist_ok=True)
    stem = os.path.splitext(os.path.basename(pdf))[0][:40]
    return os.path.join(d, "%s_p%d%s.png" % (stem, page_no, tag))


# -------------------------------------------------------------------- backends

def render_mupdf(fitz, pdf, page_no, dpi, box=None, tag="", rect=None, outdir=None):
    doc = fitz.open(pdf)
    if not 1 <= page_no <= doc.page_count:
        sys.exit("page %d out of range (1-%d)" % (page_no, doc.page_count))
    page = doc[page_no - 1]
    clip = rect
    if clip is None and box:
        r = page.rect
        x0, y0, x1, y1 = box
        clip = fitz.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height,
                         r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        tag = tag or "_crop"
    out = _outpath(pdf, page_no, tag, outdir)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    pix.save(out)
    print("%s  (%dx%d px)" % (out, pix.width, pix.height))
    return out


def render_sips(pdf, page_no, dpi, box=None, tag="", outdir=None):
    """Fallback: rescale page geometry, let macOS sips rasterize."""
    pypdf = _pypdf()
    from pypdf import Transformation
    reader = pypdf.PdfReader(pdf)
    if not 1 <= page_no <= len(reader.pages):
        sys.exit("page %d out of range (1-%d)" % (page_no, len(reader.pages)))
    page = reader.pages[page_no - 1]
    mx0, my0 = float(page.mediabox.left), float(page.mediabox.bottom)
    mx1, my1 = float(page.mediabox.right), float(page.mediabox.top)
    pw, ph = mx1 - mx0, my1 - my0
    scale = dpi / 72.0
    if box:
        x0, y0, x1, y1 = box
        nx0, nx1 = mx0 + x0 * pw, mx0 + x1 * pw
        ny0, ny1 = my1 - y1 * ph, my1 - y0 * ph
        # Translate before scaling: pypdf scales about (0,0), so scaling a moved
        # mediabox renders a blank page.
        page.add_transformation(Transformation().translate(-nx0, -ny0).scale(scale))
        w, h = (nx1 - nx0) * scale, (ny1 - ny0) * scale
        page.mediabox.lower_left = page.cropbox.lower_left = (0, 0)
        page.mediabox.upper_right = page.cropbox.upper_right = (w, h)
        tag = tag or "_crop"
    else:
        page.scale(scale, scale)
    out = _outpath(pdf, page_no, tag, outdir)
    tmp = out.replace(".png", ".tmp.pdf")
    writer = pypdf.PdfWriter()
    writer.add_page(page)
    with open(tmp, "wb") as fh:
        writer.write(fh)
    r = subprocess.run(["sips", "-s", "format", "png", tmp, "--out", out],
                       capture_output=True, text=True)
    os.remove(tmp)
    if r.returncode != 0 or not os.path.exists(out):
        sys.exit("sips failed: " + (r.stderr or r.stdout).strip())
    print(out)
    return out


def render(fitz, pdf, page_no, dpi, box=None, tag="", outdir=None):
    if fitz:
        return render_mupdf(fitz, pdf, page_no, dpi, box, tag, outdir=outdir)
    return render_sips(pdf, page_no, dpi, box, tag, outdir=outdir)


# ----------------------------------------------------------- caption discovery

def captions(fitz, pdf):
    """Yield (page_no, label, caption_rect) for every figure/table caption."""
    doc = fitz.open(pdf)
    for pno in range(doc.page_count):
        for b in doc[pno].get_text("blocks"):
            text = b[4].strip()
            m = CAPTION_RE.match(text)
            if m:
                label = "%s %s" % (m.group(1).rstrip(".").title(), m.group(2))
                yield pno + 1, label, fitz.Rect(b[:4]), text[:70].replace("\n", " ")


def _column_band(page, cap_rect):
    """Horizontal band the artwork may occupy: full width, or the caption's column."""
    pr = page.rect
    if cap_rect.width > 0.6 * pr.width:
        return pr.x0, pr.x1
    mid = pr.x0 + pr.width / 2.0
    pad = pr.width * 0.03
    if (cap_rect.x0 + cap_rect.x1) / 2.0 < mid:
        return pr.x0, mid + pad
    return mid - pad, pr.x1


def _vertical_stop(fitz, page, cap_rect, upward, band):
    """Nearest other caption in the travel direction, which bounds the region."""
    lo, hi = band
    limit = page.rect.y0 if upward else page.rect.y1
    for b in page.get_text("blocks"):
        r = fitz.Rect(b[:4])
        if not CAPTION_RE.match(b[4].strip()) or r == cap_rect:
            continue
        if r.x1 < lo or r.x0 > hi:
            continue  # different column
        if upward and cap_rect.y0 > r.y1 > limit:
            limit = r.y1
        elif not upward and cap_rect.y1 < r.y0 < limit:
            limit = r.y0
    return limit


def content_rect(fitz, page, cap_rect, upward):
    """Union of drawings/images on the side of the caption the artwork sits on."""
    pr = page.rect
    lo, hi = _column_band(page, cap_rect)
    stop = _vertical_stop(fitz, page, cap_rect, upward, (lo, hi))
    boxes = []
    for d in page.get_drawings():
        boxes.append(fitz.Rect(d["rect"]))
    for img in page.get_images(full=True):
        try:
            boxes.extend(page.get_image_rects(img[0]))
        except Exception:
            pass
    keep = []
    for r in boxes:
        # Table rules are zero-height lines, so require size in EITHER axis;
        # demanding both would discard every rule that defines a table.
        if max(r.width, r.height) < 4:
            continue
        # centre must sit in the caption's column, not merely overlap it
        if not (lo <= (r.x0 + r.x1) / 2.0 <= hi):
            continue
        if upward and not (stop - 2 <= r.y0 and r.y1 <= cap_rect.y0 + 2):
            continue
        if not upward and not (cap_rect.y1 - 2 <= r.y1 and r.y0 <= stop + 2):
            continue
        keep.append(r)
    if not keep:
        return None
    keep.append(cap_rect)
    # explicit min/max: Rect |= ignores empty (zero-height) rects
    u = fitz.Rect(min(r.x0 for r in keep), min(r.y0 for r in keep),
                  max(r.x1 for r in keep), max(r.y1 for r in keep))
    return u & pr


def extract_text(fitz, pdf, pages):
    """Yield (page_no, text) for each page, PyMuPDF reading order or pypdf fallback."""
    if fitz:
        doc = fitz.open(pdf)
        for pno in pages:
            yield pno, doc[pno - 1].get_text("text").strip()
    else:
        reader = _pypdf().PdfReader(pdf)
        for pno in pages:
            yield pno, (reader.pages[pno - 1].extract_text() or "").strip()


_NO_TEXT = "(no extractable text \u2014 likely scanned or vector; render this page)"


def _parse_range(spec, npages):
    """'3', '2-5', '2-', '-4' -> inclusive 1-based page list, clamped to [1,npages]."""
    if not spec:
        return list(range(1, npages + 1))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a) if a.strip() else 1
            b = int(b) if b.strip() else npages
        else:
            a = b = int(part)
        out.extend(range(max(1, a), min(npages, b) + 1))
    return sorted(set(out))


# ------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("probe").add_argument("pdf")
    p = sub.add_parser("text")
    p.add_argument("pdf")
    p.add_argument("-r", "--range", default=None, help='e.g. 1-8 or 2,5,9-12')
    p.add_argument("-o", "--out", default=None,
                   help="write to this .md file (default: print to stdout)")
    for name, dflt in (("page", 200), ("sweep", 120)):
        p = sub.add_parser(name)
        p.add_argument("pdf"); p.add_argument("page", type=int)
        p.add_argument("-d", "--dpi", type=int, default=dflt)
        p.add_argument("-o", "--outdir", default=None)
    p = sub.add_parser("pages")
    p.add_argument("pdf")
    p.add_argument("-r", "--range", default=None, help='e.g. 1-8 or 2,5,9-12')
    p.add_argument("-d", "--dpi", type=int, default=170)
    p.add_argument("-o", "--outdir", default=None)
    p = sub.add_parser("crop")
    p.add_argument("pdf"); p.add_argument("page", type=int)
    p.add_argument("-b", "--box", required=True)
    p.add_argument("-d", "--dpi", type=int, default=400)
    p.add_argument("-o", "--outdir", default=None)
    p = sub.add_parser("find")
    p.add_argument("pdf"); p.add_argument("label", help='e.g. "Figure 3" or "Table 1"')
    p.add_argument("-d", "--dpi", type=int, default=350)
    p.add_argument("-m", "--margin", type=float, default=6.0, help="pad in points")
    p.add_argument("-o", "--outdir", default=None)

    a = ap.parse_args()
    if not os.path.exists(a.pdf):
        sys.exit("no such file: %s" % a.pdf)
    fitz = ensure_pymupdf()

    if a.cmd == "probe":
        if fitz:
            doc = fitz.open(a.pdf)
            print("pages: %d" % doc.page_count)
            print("size:  %.0f x %.0f pt" % (doc[0].rect.width, doc[0].rect.height))
            found = list(captions(fitz, a.pdf))
            print("captions: %d" % len(found))
            for pno, label, _, snippet in found:
                print("  p%-3d %-10s %s" % (pno, label, snippet))
        else:
            r = _pypdf().PdfReader(a.pdf)
            print("pages: %d" % len(r.pages))
            print("size:  %.0f x %.0f pt" % (float(r.pages[0].mediabox.width),
                                             float(r.pages[0].mediabox.height)))
            print("captions: (needs PyMuPDF)")
        return

    if a.cmd == "text":
        if fitz:
            npages = fitz.open(a.pdf).page_count
        else:
            npages = len(_pypdf().PdfReader(a.pdf).pages)
        pages = _parse_range(a.range, npages)
        parts, empty = [], 0
        for pno, txt in extract_text(fitz, a.pdf, pages):
            if not txt:
                empty += 1
            parts.append("## Page %d\n\n%s\n" % (pno, txt or _NO_TEXT))
        body = "\n".join(parts)
        if a.out:
            os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
            with open(a.out, "w") as fh:
                fh.write(body)
            note = ", %d empty" % empty if empty else ""
            print("%s  (%d pages, %d chars%s)" % (a.out, len(pages), len(body), note))
        else:
            sys.stdout.write(body)
        return

    if a.cmd == "pages":
        if fitz:
            npages = fitz.open(a.pdf).page_count
        else:
            npages = len(_pypdf().PdfReader(a.pdf).pages)
        for pno in _parse_range(a.range, npages):
            render(fitz, a.pdf, pno, a.dpi, outdir=a.outdir)
        return

    if a.cmd == "find":
        if not fitz:
            sys.exit("find needs PyMuPDF; use `crop` with the sips fallback instead")
        want = a.label.strip().lower().replace(".", "")
        hits = [c for c in captions(fitz, a.pdf)
                if c[1].lower().replace(".", "") == want]
        if not hits:
            sys.exit("caption %r not found; run `probe` to list captions" % a.label)
        pno, label, cap, _ = hits[0]
        doc = fitz.open(a.pdf)
        page = doc[pno - 1]
        upward = label.lower().startswith(("figure", "fig"))
        rect = content_rect(fitz, page, cap, upward)
        if rect is None:
            # No vector/raster artwork found: fall back to a fixed span past the caption.
            span = page.rect.height * 0.34
            rect = fitz.Rect(cap.x0, cap.y0 - span if upward else cap.y0,
                             cap.x1, cap.y1 if upward else cap.y1 + span) & page.rect
            print("no artwork bounds detected; using a fixed span", file=sys.stderr)
        rect = (rect + (-a.margin, -a.margin, a.margin, a.margin)) & page.rect
        tag = "_" + label.lower().replace(" ", "")
        render_mupdf(fitz, a.pdf, pno, a.dpi, tag=tag, rect=rect, outdir=a.outdir)
        return

    if a.cmd == "page":
        render(fitz, a.pdf, a.page, a.dpi, outdir=a.outdir); return

    if a.cmd == "sweep":
        for i in range(4):
            top = max(0.0, i * 0.25 - 0.025)
            bot = min(1.0, (i + 1) * 0.25 + 0.025)
            render(fitz, a.pdf, a.page, a.dpi, (0.0, top, 1.0, bot),
                   "_band%d" % (i + 1), outdir=a.outdir)
        return

    if a.cmd == "crop":
        try:
            box = tuple(float(v) for v in a.box.split(","))
            assert len(box) == 4
        except Exception:
            sys.exit("--box must be x0,y0,x1,y1 as fractions, e.g. 0,0,0.5,0.5")
        if not all(0.0 <= v <= 1.0 for v in box):
            sys.exit("box values must be within [0,1]")
        if box[0] >= box[2] or box[1] >= box[3]:
            sys.exit("box must satisfy x0<x1 and y0<y1")
        render(fitz, a.pdf, a.page, a.dpi, box, outdir=a.outdir)


if __name__ == "__main__":
    main()
