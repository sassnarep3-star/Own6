"""Regression tests for the luck/skill section and the acceptance audit.

These are standard-library tests so they run in the dependency-free CI job.
They assert the publication rules that make the section honest:

* every table row carries an https source link;
* no page is unreachable;
* a check that could not be performed is never labelled verified;
* the committed data regenerates exactly.

They do not, and cannot, verify any NBA fact.
"""

from __future__ import annotations

import csv
import html.parser
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LUCK_PAGES = sorted((ROOT / "docs" / "luck").glob("*.html"))


class Rows(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.in_tbody = False
        self.in_row = False
        self.current: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
                if self.in_row:
                    self.current.append(attrs[key])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.current = []

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            self.rows.append(self.current)
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False


def parse(path: Path) -> Rows:
    parser = Rows()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


class TestSectionPublished(unittest.TestCase):
    def test_pages_exist(self):
        self.assertEqual(len(LUCK_PAGES), 7)
        names = {path.name for path in LUCK_PAGES}
        for expected in ("index.html", "requirements.html", "parlays.html", "testing.html",
                         "method.html", "acceptance.html", "flagged.html"):
            self.assertIn(expected, names)

    def test_every_table_row_has_https_source(self):
        for path in LUCK_PAGES:
            parser = parse(path)
            self.assertTrue(parser.rows, f"{path.name} has no table rows")
            for index, links in enumerate(parser.rows, start=1):
                self.assertTrue(
                    any(link.startswith("https://") for link in links),
                    f"{path.name} row {index} has no https source link",
                )

    def test_all_local_links_resolve(self):
        for path in LUCK_PAGES:
            for link in parse(path).links:
                if link.startswith(("https://", "#", "mailto:", "http://")):
                    continue
                self.assertTrue((path.parent / link.split("#")[0]).exists(), f"{path.name}: {link}")

    def test_no_merge_markers_or_placeholders(self):
        import re

        for path in LUCK_PAGES:
            text = path.read_text(encoding="utf-8")
            for marker in ("<<<<<<<", ">>>>>>>", "None</td>"):
                self.assertNotIn(marker, text, f"{path.name} contains {marker!r}")
            self.assertIsNone(re.search(r"\bnan\b", text), f"{path.name} contains a bare NaN")

    def test_states_the_evidence_boundary(self):
        index = (ROOT / "docs" / "luck" / "index.html").read_text(encoding="utf-8")
        self.assertIn("unverified", index.lower())
        self.assertIn("no wagers", index.lower())


class TestDataAndChecker(unittest.TestCase):
    def test_checker_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_luck.py")],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_analysis_is_deterministic(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "luck_analysis.py"), "--check"],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_flags_have_sources_and_actions(self):
        with (ROOT / "data" / "luck" / "flags.csv").open(newline="", encoding="utf-8") as handle:
            flags = list(csv.DictReader(handle))
        self.assertGreaterEqual(len(flags), 8)
        for flag in flags:
            self.assertTrue(flag["source_url"].startswith("https://"), flag["id"])
            self.assertTrue(flag["action_requested"].strip(), flag["id"])

    def test_crosscheck_all_pass(self):
        record = json.loads((ROOT / "data" / "luck" / "numerics_crosscheck.json").read_text())
        self.assertTrue(record["all_pass"])
        self.assertGreaterEqual(len(record["checks"]), 6)

    def test_parlay_table_declares_independence(self):
        with (ROOT / "data" / "luck" / "parlay_requirements.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                self.assertIn("independent", row["assumption"])
                self.assertIn("NOT assumed", row["assumption"])


class TestAcceptanceBoundaries(unittest.TestCase):
    def setUp(self):
        with (ROOT / "data" / "acceptance" / "claims.csv").open(newline="", encoding="utf-8") as handle:
            self.claims = list(csv.DictReader(handle))
        with (ROOT / "data" / "acceptance" / "pages.csv").open(newline="", encoding="utf-8") as handle:
            self.pages = list(csv.DictReader(handle))

    def test_blocked_checks_are_not_verified(self):
        blocked = {claim["id"] for claim in self.claims if claim["verdict"] == "verification blocked"}
        self.assertIn("A13", blocked, "official-source re-read must stay blocked without egress")
        self.assertIn("A14", blocked, "live-URL check must stay blocked without egress")

    def test_every_claim_has_source(self):
        for claim in self.claims:
            self.assertTrue(claim["source_url"].startswith("https://"), claim["id"])

    def test_no_unreachable_pages(self):
        unexpected = [
            page["page"]
            for page in self.pages
            if page["orphan"] == "yes" and page["intentional_orphan"] != "yes"
        ]
        self.assertEqual(unexpected, [])

    def test_missing_generators_are_disclosed(self):
        """A page without a generator must be disclosed, not silently accepted."""
        missing = sorted(page["page"] for page in self.pages if page["generator_exists"] == "NO")
        with (ROOT / "data" / "luck" / "flags.csv").open(newline="", encoding="utf-8") as handle:
            flags = {row["id"]: row for row in csv.DictReader(handle)}
        self.assertIn("L-06", flags, "provenance gap flag L-06 is required")
        for page in missing:
            self.assertIn(Path(page).parent.name, flags["L-06"]["detail"], page)
        a12 = next(claim for claim in self.claims if claim["id"] == "A12")
        self.assertEqual(a12["verdict"], "needs review" if missing else "verified")

    def test_shallow_clone_caveat_present(self):
        shallow = next(claim for claim in self.claims if claim["id"] == "A06")
        self.assertEqual(shallow["verdict"], "not assessable")
        self.assertIn("shallow", shallow["observed"])


if __name__ == "__main__":
    unittest.main()
