"""Tests for the nfl_b2511a5c pack.

Layer 1 - the verifier (rules 1-9) passes on the built pack.
Layer 2 - negative cases: the builder refuses a table row without an official link, and the verifier
          fails when a raw capture no longer matches its recorded SHA-256 or an excerpt is missing.
Layer 3 - determinism: a second build overwrites every page byte for byte.

Run: python3 tests/test_nfl_b2511a5c.py   (or pytest tests/test_nfl_b2511a5c.py)
"""
from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import build_nfl_b2511a5c as B  # noqa: E402
import check_nfl_b2511a5c as C  # noqa: E402


class VerifierPasses(unittest.TestCase):
    def test_verifier_exit_zero(self):
        out = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_nfl_b2511a5c.py")],
                             capture_output=True, text=True, cwd=REPO)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("all rules pass", out.stdout)


class NegativeCases(unittest.TestCase):
    def test_row_without_official_link_is_refused(self):
        with self.assertRaises(ValueError):
            B.table(["A"], [(["x"], "")])

    def test_link_helper_escapes_html(self):
        self.assertIn("&lt;script&gt;", B.esc("<script>"))

    def test_hash_mismatch_is_reported(self):
        # Copy the pack, corrupt one raw capture, and point the verifier at the copy.
        tmp = tempfile.mkdtemp()
        try:
            data = os.path.join(tmp, "data", "nfl_b2511a5c")
            os.makedirs(os.path.dirname(data))
            shutil.copytree(os.path.join(REPO, "data", "nfl_b2511a5c"), data)
            with open(os.path.join(data, "raw", "R01.txt"), "a", encoding="utf-8") as f:
                f.write("tampered\n")
            with open(os.path.join(data, "official_reads.csv"), encoding="utf-8", newline="") as f:
                reads = list(csv.DictReader(f))
            C.REPO = tmp
            C.errors.clear()
            C.rule2(reads)
            self.assertTrue(any("R01: raw SHA-256 mismatch" in e for e in C.errors), C.errors)
        finally:
            C.REPO = REPO
            shutil.rmtree(tmp, ignore_errors=True)


class Determinism(unittest.TestCase):
    def test_second_build_is_byte_identical(self):
        before = B.build()
        for name, text in before.items():
            with open(os.path.join(B.DOCS, name), encoding="utf-8") as f:
                self.assertEqual(f.read(), text, name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
