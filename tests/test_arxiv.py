"""Tests for skills/arxiv/scripts/arxiv.py. Run: python3 -m unittest discover -s tests"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "skills", "arxiv", "scripts", "arxiv.py")
FIXTURE = os.path.join(HERE, "fixtures", "attention.atom")

spec = importlib.util.spec_from_file_location("arxiv", SCRIPT)
arxiv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arxiv)


def load_fixture():
    with open(FIXTURE, encoding="utf-8") as f:
        return arxiv.parse_feed(f.read())


class ParseFeed(unittest.TestCase):
    def test_parses_attention_paper_entry(self):
        result = load_fixture()
        self.assertEqual(result["total_results"], 1)
        self.assertEqual(result["start_index"], 0)
        p = result["papers"][0]
        self.assertEqual(p["id"], "1706.03762v7")
        self.assertEqual(p["title"], "Attention Is All You Need")
        self.assertEqual(p["authors"][0], "Ashish Vaswani")
        self.assertEqual(len(p["authors"]), 8)
        self.assertEqual(p["published"][:10], "2017-06-12")
        self.assertEqual(p["primary_category"], "cs.CL")
        self.assertIn("cs.LG", p["categories"])
        self.assertEqual(p["abs_url"], "https://arxiv.org/abs/1706.03762v7")
        self.assertEqual(p["pdf_url"], "https://arxiv.org/pdf/1706.03762v7")
        self.assertTrue(p["summary"].startswith("The dominant sequence transduction models"))
        self.assertNotIn("\n", p["summary"])


class NormalizeId(unittest.TestCase):
    def test_accepts_bare_prefixed_and_url_forms(self):
        cases = {
            "1706.03762": "1706.03762",
            "arXiv:1706.03762v2": "1706.03762v2",
            "https://arxiv.org/abs/1706.03762v7": "1706.03762v7",
            "https://arxiv.org/pdf/1706.03762.pdf": "1706.03762",
            "cond-mat/0011267v1": "cond-mat/0011267v1",
        }
        for raw, expected in cases.items():
            self.assertEqual(arxiv.normalize_arxiv_id(raw), expected, raw)


class DateClause(unittest.TestCase):
    def test_open_and_closed_ranges(self):
        self.assertIsNone(arxiv.build_submitted_date_clause(None, None))
        self.assertEqual(
            arxiv.build_submitted_date_clause("2024-01-15", None),
            "submittedDate:[202401150000 TO 299912312359]",
        )
        self.assertEqual(
            arxiv.build_submitted_date_clause("20240101", "2024-06-30"),
            "submittedDate:[202401010000 TO 202406302359]",
        )

    def test_rejects_short_dates(self):
        with self.assertRaises(ValueError):
            arxiv.build_submitted_date_clause("2024", None)


class Citations(unittest.TestCase):
    def test_bibtex_entry(self):
        p = load_fixture()["papers"][0]
        bib = arxiv.to_bibtex(p)
        self.assertTrue(bib.startswith("@misc{vaswani2017attention,\n"))
        self.assertIn("  title = {{Attention Is All You Need}}", bib)
        self.assertIn("  author = {Ashish Vaswani and Noam Shazeer", bib)
        self.assertIn("  eprint = {1706.03762}", bib)
        self.assertIn("  primaryClass = {cs.CL}", bib)
        self.assertTrue(bib.endswith("\n}"))

    def test_text_citation(self):
        p = load_fixture()["papers"][0]
        text = arxiv.to_citation(p)
        self.assertTrue(text.startswith("Ashish Vaswani, Noam Shazeer, "))
        self.assertIn(" & Illia Polosukhin (2017). Attention Is All You Need. arXiv:1706.03762 [cs.CL].", text)
        self.assertTrue(text.endswith("https://arxiv.org/abs/1706.03762v7"))


class Filenames(unittest.TestCase):
    def test_paper_filename_is_fs_safe(self):
        p = load_fixture()["papers"][0]
        self.assertEqual(arxiv.paper_filename(p), "1706.03762v7 - Attention Is All You Need.pdf")
        p2 = dict(p, id="cond-mat/0011267v1", title='A "quoted": title? <with> * pipes | ' + "x" * 100)
        name = arxiv.paper_filename(p2)
        self.assertTrue(name.startswith("cond-mat_0011267v1 - A quoted title with pipes "))
        self.assertLessEqual(len(name), len("cond-mat_0011267v1 - ") + 80 + len(".pdf"))


class Formatting(unittest.TestCase):
    def test_format_paper_lines(self):
        p = load_fixture()["papers"][0]
        out = arxiv.format_paper(p, 0)
        lines = out.split("\n")
        self.assertEqual(lines[0], "1. Attention Is All You Need")
        self.assertEqual(lines[1], "   id: 1706.03762v7  [cs.CL]  (2017-06-12)")
        self.assertEqual(lines[2], "   authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, et al.")
        self.assertEqual(lines[3], "   abs: https://arxiv.org/abs/1706.03762v7")
        self.assertTrue(lines[5].startswith("   summary: "))


class QueryParams(unittest.TestCase):
    def test_builds_search_params(self):
        params = arxiv.build_params(query="au:Vaswani", ids=None, start=0, max_results=5,
                                    sort_by="submittedDate", sort_order="ascending",
                                    submitted_from="2017-01-01", submitted_to=None)
        self.assertEqual(params["search_query"], "(au:Vaswani) AND submittedDate:[201701010000 TO 299912312359]")
        self.assertEqual(params["max_results"], "5")
        self.assertEqual(params["sortBy"], "submittedDate")
        self.assertNotIn("id_list", params)

    def test_requires_query_or_ids(self):
        with self.assertRaises(ValueError):
            arxiv.build_params(query=None, ids=[], start=0, max_results=10,
                               sort_by=None, sort_order=None, submitted_from=None, submitted_to=None)


if __name__ == "__main__":
    unittest.main()
