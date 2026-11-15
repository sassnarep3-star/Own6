"""Regression tests for the consolidated decision-readiness pack (6ab24751).

Pure standard library: runs under both ``pytest`` and the bare stdlib runner.
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from nfl_6ab24751.readiness import (  # noqa: E402
    ALLOWED_STATUS,
    PackPaths,
    load_pack,
    validate,
)

DATA_DIR = os.path.join(ROOT, "data", "nfl_6ab24751")
DOCS_DIR = os.path.join(ROOT, "docs", "nfl-6ab24751")


def _pack():
    return load_pack(PackPaths.for_repo(ROOT))


class ReadinessDataTests(unittest.TestCase):
    def setUp(self):
        self.pack = _pack()

    def test_pack_validates(self):
        self.assertEqual(validate(self.pack), [])

    def test_every_row_has_https_source(self):
        for r in self.pack.rows:
            self.assertTrue(r["official_source_url"].startswith("https://"), r["req_id"])

    def test_statuses_are_known(self):
        for r in self.pack.rows:
            self.assertIn(r["status"], ALLOWED_STATUS, r["req_id"])

    def test_blocking_gates_resolve(self):
        gate_ids = self.pack.gate_ids
        for r in self.pack.rows:
            gate = r["blocking_gate"]
            if gate and not gate.startswith("none"):
                self.assertTrue(any(g in gate for g in gate_ids), (r["req_id"], gate))

    def test_open_rows_have_clearing_number(self):
        for r in self.pack.rows:
            if r["status"] in ("not_started", "needs_review", "implemented_limited", "blocked"):
                self.assertTrue(r["clearing_number"].strip(), r["req_id"])

    def test_status_counts_match_rows(self):
        counts = self.pack.status_counts()
        self.assertEqual(sum(counts.values()), len(self.pack.rows))

    def test_req_ids_unique(self):
        ids = [r["req_id"] for r in self.pack.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_readiness_requires_decision_table_row(self):
        # RQ-23 is the explicit landing-page requirement; it must be implemented.
        row = next(r for r in self.pack.rows if r["req_id"] == "RQ-23")
        self.assertEqual(row["status"], "implemented")
        self.assertIn("landing", row["requirement"].lower())

    def test_rejected_policy_rows_exist(self):
        rejected = [r for r in self.pack.rows if r["status"] == "rejected_policy"]
        self.assertGreaterEqual(len(rejected), 2)


class GeneratedSiteTests(unittest.TestCase):
    def test_pages_exist_without_input(self):
        for name in ("index.html", "gates.html", "sources.html",
                     "flagged.html", "executive-summary.html"):
            path = os.path.join(DOCS_DIR, name)
            self.assertTrue(os.path.exists(path), name)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertNotIn("<input", content.lower(), name)

    def test_landing_table_present_in_root_index(self):
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as fh:
            idx = fh.read()
        self.assertIn("<!-- BEGIN DECISION-READINESS TABLE", idx)
        self.assertIn("<!-- END DECISION-READINESS TABLE", idx)
        self.assertGreaterEqual(idx.count("<tr"), 80)

    def test_checker_passes(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "check_nfl_6ab24751.py")],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("0 failures", proc.stdout)

    def test_builder_is_idempotent(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "build_nfl_6ab24751.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
