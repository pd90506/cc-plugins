#!/usr/bin/env python3
"""Dependency-free arXiv client for the cc-arxiv `arxiv` skill.

Subcommands:
  search  --query Q | --ids ID... [--max N] [--start N] [--sort-by F] [--sort-order O]
          [--from DATE] [--to DATE]           field/known-item search, formatted results
  get     ID_OR_URL [--dir DIR] [--filename NAME]   download the PDF (default ~/Downloads/arxiv)
  cite    ID_OR_URL... [--format bibtex|text]        BibTeX (default) or APA-style text

Query syntax: field prefixes ti: au: abs: cat: all: and boolean AND / OR / ANDNOT.
API docs: https://info.arxiv.org/help/api/user-manual.html
Requires Python 3.9+. No third-party packages.
"""
import argparse
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API_BASE = "https://export.arxiv.org/api/query"
USER_AGENT = "cc-arxiv/0.1 (Claude Code plugin)"
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "arxiv")
NS = {
    "a": "http://www.w3.org/2005/Atom",
    "os": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
}


# ---- parsing ---------------------------------------------------------------

def _clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_arxiv_id(raw):
    """'arXiv:1706.03762', abs/pdf URLs, or a bare id -> bare id (version kept)."""
    ident = (raw or "").strip()
    ident = re.sub(r"^arxiv:", "", ident, flags=re.I)
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(.+?)(?:\.pdf)?$", ident, flags=re.I)
    if m:
        ident = m.group(1)
    return re.sub(r"\.pdf$", "", ident, flags=re.I).strip()


def normalize_submitted_date(raw, is_end):
    """YYYY-MM-DD, YYYYMMDD, or YYYYMMDDHHMM -> YYYYMMDDHHMM."""
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) < 8:
        raise ValueError("Invalid date '%s'. Use YYYY-MM-DD or YYYYMMDDHHMM." % raw)
    ymd = digits[:8]
    if len(digits) >= 12:
        time = digits[8:12]
    else:
        time = "2359" if is_end else "0000"
    return ymd + time


def build_submitted_date_clause(date_from, date_to):
    if not date_from and not date_to:
        return None
    lo = normalize_submitted_date(date_from, False) if date_from else "190001010000"
    hi = normalize_submitted_date(date_to, True) if date_to else "299912312359"
    return "submittedDate:[%s TO %s]" % (lo, hi)


def _parse_entry(entry):
    def text(path):
        el = entry.find(path, NS)
        return _clean(el.text) if el is not None else ""

    raw_id = text("a:id")
    bare_id = normalize_arxiv_id(re.sub(r"^https?://arxiv\.org/abs/", "", raw_id, flags=re.I))
    authors = [_clean(n.text) for n in entry.findall("a:author/a:name", NS)]
    categories = [c.get("term") for c in entry.findall("a:category", NS) if c.get("term")]
    primary = entry.find("arxiv:primary_category", NS)
    abs_url, pdf_url = "", ""
    for link in entry.findall("a:link", NS):
        href = link.get("href", "")
        if link.get("type") == "application/pdf":
            pdf_url = href
        elif link.get("rel") == "alternate" or link.get("type") == "text/html":
            abs_url = href
    return {
        "id": bare_id,
        "title": text("a:title"),
        "authors": authors,
        "summary": text("a:summary"),
        "published": text("a:published"),
        "updated": text("a:updated"),
        "categories": categories,
        "primary_category": primary.get("term") if primary is not None else None,
        "comment": text("arxiv:comment") or None,
        "journal_ref": text("arxiv:journal_ref") or None,
        "doi": text("arxiv:doi") or None,
        "abs_url": abs_url or "https://arxiv.org/abs/%s" % bare_id,
        "pdf_url": pdf_url or "https://arxiv.org/pdf/%s" % bare_id,
    }


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    papers = [_parse_entry(e) for e in root.findall("a:entry", NS)]

    def num(path, default):
        el = root.find(path, NS)
        try:
            return int(el.text)
        except (AttributeError, TypeError, ValueError):
            return default

    return {
        "total_results": num("os:totalResults", len(papers)),
        "start_index": num("os:startIndex", 0),
        "items_per_page": num("os:itemsPerPage", len(papers)),
        "papers": papers,
    }


# ---- network ---------------------------------------------------------------

def normalize_ids(raw_ids):
    return [i for i in (normalize_arxiv_id(x) for x in (raw_ids or [])) if i]


def primary_category(paper):
    return paper.get("primary_category") or (paper["categories"][0] if paper["categories"] else "")


def year_of(paper):
    return paper["published"][:4]


def build_params(query=None, ids=None, start=0, max_results=10, sort_by=None, sort_order=None,
                 submitted_from=None, submitted_to=None):
    clause = build_submitted_date_clause(submitted_from, submitted_to)
    if clause:
        query = "(%s) AND %s" % (query, clause) if query else clause
    ids = normalize_ids(ids)
    if not query and not ids:
        raise ValueError("Provide a search query, a date range, or at least one arXiv id.")
    params = {}
    if query:
        params["search_query"] = query
    if ids:
        params["id_list"] = ",".join(ids)
    params["start"] = str(start or 0)
    params["max_results"] = str(max_results or 10)
    params["sortBy"] = sort_by or "relevance"
    params["sortOrder"] = sort_order or "descending"
    return params


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def search_arxiv(**kwargs):
    params = build_params(**kwargs)
    return parse_feed(_fetch(API_BASE + "?" + urllib.parse.urlencode(params)).decode("utf-8"))


def lookup(ids):
    return search_arxiv(ids=ids, max_results=len(ids))["papers"]


# ---- formatting ------------------------------------------------------------

def _truncate(s, n):
    return s[:n] + "…" if len(s) > n else s


def format_paper(paper, index=None):
    num = "%d. " % (index + 1) if index is not None else ""
    authors = paper["authors"]
    authors = ", ".join(authors[:4]) + ", et al." if len(authors) > 4 else ", ".join(authors)
    date = paper["published"][:10]
    cat = primary_category(paper)
    lines = [
        "%s%s" % (num, paper["title"]),
        "   id: %s%s%s" % (paper["id"], "  [%s]" % cat if cat else "", "  (%s)" % date if date else ""),
        "   authors: %s" % (authors or "unknown"),
        "   abs: %s" % paper["abs_url"],
        "   pdf: %s" % paper["pdf_url"],
    ]
    if paper["summary"]:
        lines.append("   summary: %s" % _truncate(paper["summary"], 500))
    return "\n".join(lines)


def id_without_version(ident):
    return re.sub(r"v\d+$", "", ident, flags=re.I)


def _last_name(author):
    parts = author.strip().split()
    return parts[-1] if parts else author


def bibtex_key(paper):
    first = paper["authors"][0] if paper["authors"] else "arxiv"
    last = re.sub(r"[^a-z0-9]", "", _last_name(first).lower()) or "arxiv"
    year = year_of(paper)
    word = ""
    for w in paper["title"].split():
        w = re.sub(r"[^a-z0-9]", "", w.lower())
        if len(w) > 3:
            word = w
            break
    return last + year + word


def to_bibtex(paper):
    primary = primary_category(paper)
    entry_type = "article" if paper.get("journal_ref") else "misc"
    fields = [
        ("title", "{%s}" % paper["title"]),
        ("author", " and ".join(paper["authors"])),
        ("year", year_of(paper)),
        ("eprint", id_without_version(paper["id"])),
        ("archivePrefix", "arXiv"),
        ("primaryClass", primary),
        ("journal", paper.get("journal_ref")),
        ("doi", paper.get("doi")),
        ("url", paper["abs_url"]),
    ]
    lines = ["  %s = {%s}" % (k, v) for k, v in fields if v]
    return "@%s{%s,\n%s\n}" % (entry_type, bibtex_key(paper), ",\n".join(lines))


def to_citation(paper):
    year = year_of(paper)
    authors = paper["authors"]
    if len(authors) > 1:
        authors = "%s & %s" % (", ".join(authors[:-1]), authors[-1])
    else:
        authors = authors[0] if authors else "Unknown"
    primary = " [%s]" % paper["primary_category"] if paper.get("primary_category") else ""
    journal = " %s." % paper["journal_ref"] if paper.get("journal_ref") else ""
    text = "%s (%s). %s. arXiv:%s%s.%s %s" % (
        authors, year, paper["title"], id_without_version(paper["id"]), primary, journal, paper["abs_url"])
    return re.sub(r"\s+", " ", text)


def paper_filename(paper):
    safe_id = re.sub(r"[/\\]", "_", paper["id"])
    safe_title = re.sub(r"[/\\:*?\"<>|]", "", paper["title"])
    safe_title = re.sub(r"\s+", " ", safe_title).strip()[:80]
    return "%s%s.pdf" % (safe_id, " - %s" % safe_title if safe_title else "")


def resolve_dir(directory):
    if not directory or not directory.strip():
        return DEFAULT_DOWNLOAD_DIR
    return os.path.abspath(os.path.expanduser(directory.strip()))


# ---- CLI -------------------------------------------------------------------

def cmd_search(a):
    result = search_arxiv(query=a.query, ids=a.ids, start=a.start, max_results=a.max,
                          sort_by=a.sort_by, sort_order=a.sort_order,
                          submitted_from=a.date_from, submitted_to=a.date_to)
    papers = result["papers"]
    if not papers:
        print("No papers found for that query.")
        return
    print("Found %d result(s); showing %d (offset %d).\n" % (
        result["total_results"], len(papers), result["start_index"]))
    print("\n\n".join(format_paper(p, result["start_index"] + i) for i, p in enumerate(papers)))


def cmd_get(a):
    ident = normalize_arxiv_id(a.id)
    if not ident:
        sys.exit("Could not parse an arXiv id from '%s'." % a.id)
    papers = lookup([ident])
    if not papers:
        sys.exit("No arXiv paper found for id '%s'." % ident)
    paper = papers[0]
    directory = resolve_dir(a.dir)
    os.makedirs(directory, exist_ok=True)
    name = os.path.basename(a.filename.strip()) if a.filename and a.filename.strip() else paper_filename(paper)
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    dest = os.path.join(directory, name)
    data = _fetch(paper["pdf_url"])
    with open(dest, "wb") as f:
        f.write(data)
    print('Saved "%s" (%.1f KB) to:\n%s' % (paper["title"], len(data) / 1024, dest))


def cmd_cite(a):
    ids = normalize_ids(a.ids)
    if not ids:
        sys.exit("Provide one or more arXiv ids.")
    papers = lookup(ids)
    if not papers:
        sys.exit("No papers found for those ids.")
    render = to_citation if a.format == "text" else to_bibtex
    print("\n\n".join(render(p) for p in papers))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="arxiv.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search arXiv (field/known-item lookups)")
    s.add_argument("--query", "-q", help="arXiv query, e.g. 'au:Hinton AND cat:cs.LG'")
    s.add_argument("--ids", nargs="+", help="specific arXiv ids or URLs")
    s.add_argument("--max", type=int, default=10, help="max results 1-100 (default 10)")
    s.add_argument("--start", type=int, default=0, help="pagination offset")
    s.add_argument("--sort-by", choices=["relevance", "lastUpdatedDate", "submittedDate"])
    s.add_argument("--sort-order", choices=["ascending", "descending"])
    s.add_argument("--from", dest="date_from", help="submitted on/after (YYYY-MM-DD)")
    s.add_argument("--to", dest="date_to", help="submitted on/before (YYYY-MM-DD)")
    s.set_defaults(func=cmd_search)

    g = sub.add_parser("get", help="download a paper's PDF")
    g.add_argument("id", help="arXiv id or URL")
    g.add_argument("--dir", help="destination directory (default %s)" % DEFAULT_DOWNLOAD_DIR)
    g.add_argument("--filename", help="override '<id> - <title>.pdf'")
    g.set_defaults(func=cmd_get)

    c = sub.add_parser("cite", help="BibTeX or text citations")
    c.add_argument("ids", nargs="+", help="arXiv ids or URLs")
    c.add_argument("--format", choices=["bibtex", "text"], default="bibtex")
    c.set_defaults(func=cmd_cite)

    a = ap.parse_args(argv)
    if a.cmd == "search" and not (1 <= a.max <= 100):
        ap.error("--max must be between 1 and 100")
    try:
        a.func(a)
    except ValueError as e:
        sys.exit(str(e))
    except urllib.error.URLError as e:
        sys.exit("arXiv request failed: %s" % e)


if __name__ == "__main__":
    main()
