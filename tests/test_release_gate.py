"""Mutation tests: release safety gate must reject regressions."""
from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

# The repository's dependency-free runner loads tests by file path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.release_gate import check_release
from scripts.build_lab import table
from scripts.check_lab import TableRows


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.docs = self.root / "docs"
        self.docs.mkdir()
        (self.root / "index.html").write_text('<a href="docs/index.html">Open</a>', encoding="utf-8")
        self.landing = self.docs / "index.html"
        self.landing.write_text(
            '<h1>Research</h1><table><tbody><tr><td>Unverified</td>'
            '<td><a href="https://www.nba.com/termsofuse">NBA terms</a></td>'
            '</tr></tbody></table>', encoding="utf-8"
        )

    def issues(self):
        return check_release(self.root, tracked=[Path("docs/index.html")])

    def test_valid_fixture(self):
        self.assertEqual(self.issues(), [])

    def test_conflict_marker(self):
        self.landing.write_text("<<<<<<< HEAD\n" + self.landing.read_text(), encoding="utf-8")
        self.assertTrue(any("merge marker" in issue for issue in self.issues()))

    def test_broken_and_escaping_links(self):
        self.landing.write_text(self.landing.read_text() +
                                '<a href="missing.html">X</a><a href="../../secret">Y</a>',
                                encoding="utf-8")
        self.assertEqual(sum("internal link" in issue for issue in self.issues()), 2)

    def test_generator_repr(self):
        self.landing.write_text(self.landing.read_text() +
                                '<tr><generator object table at 0x123></tr>', encoding="utf-8")
        self.assertTrue(any("generator repr" in issue for issue in self.issues()))

    def test_secondary_host_not_official_and_no_cells(self):
        self.landing.write_text(
            '<table><tbody><tr><a href="https://www.espn.com/">Odds</a></tr>'
            '</tbody></table>', encoding="utf-8"
        )
        errors = self.issues()
        self.assertTrue(any("no cells" in issue for issue in errors))
        self.assertTrue(any("no official HTTPS" in issue for issue in errors))

    def test_project_absolute_link(self):
        self.landing.write_text(self.landing.read_text() + '<a href="/docs/index.html">X</a>',
                                encoding="utf-8")
        self.assertTrue(any("root-absolute" in issue for issue in self.issues()))


class LabTableTests(unittest.TestCase):
    def test_generated_row_has_real_cells_and_official_source(self):
        markup = table(["Value", "Source"], [["blank", '<a href="https://www.nba.com/termsofuse">NBA</a>']])
        self.assertEqual(markup.count("<td>"), 2)
        self.assertNotIn("generator object", markup)
        audit = TableRows()
        audit.feed(markup)
        self.assertEqual(audit.rows, [{"cells": 2, "source": True}])

    def test_row_without_https_source_is_detected(self):
        audit = TableRows()
        audit.feed(table(["Source"], [["none"]]))
        self.assertFalse(audit.rows[0]["source"])


if __name__ == "__main__":
    unittest.main()
