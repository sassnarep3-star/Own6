#!/usr/bin/env python3
"""Tests for the nfl_a67ddef8 pack: identities, arithmetic, capture honesty, site rules.

Run: python3 tests/test_nfl_a67ddef8.py
No network, no pytest dependency (this repo's CI runs plain python3 for pack tests).
"""
from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_a67ddef8")
DOCS = os.path.join(REPO, "docs", "nfl-a67ddef8")
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def rows(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestStandings(unittest.TestCase):
    def test_32_clubs_and_arithmetic(self):
        r = rows("standings_2026_11_19.csv")
        self.assertEqual(len(r), 32)
        self.assertEqual(sum(int(x["w"]) for x in r), 149)
        self.assertEqual(sum(int(x["l"]) for x in r), 149)
        self.assertEqual(sum(int(x["t"]) for x in r), 2)
        pf = sum(int(x["pf"]) for x in r)
        pa = sum(int(x["pa"]) for x in r)
        self.assertEqual(pf, 6923)
        self.assertEqual(pf, pa)

    def test_every_row_sourced(self):
        for x in rows("standings_2026_11_19.csv"):
            self.assertTrue(x["source_url"].startswith("https://www.nfl.com/"))


class TestInjuries(unittest.TestCase):
    def test_counts(self):
        r = rows("injuries_reg11.csv")
        players = [x for x in r if x["player"]]
        self.assertEqual(len(players), 253)
        self.assertEqual(sum(1 for x in r if x["note"]), 2)
        statuses = [x for x in players if x["game_status"]]
        self.assertEqual(len(statuses), 16)
        self.assertTrue(all("THURSDAY" in x["game"] for x in statuses))
        self.assertEqual(len({x["game"] for x in r}), 13)

    def test_sunday_rows_pending_not_invented(self):
        for x in rows("injuries_reg11.csv"):
            if x["player"] and "SUNDAY" in x["game"]:
                self.assertEqual(x["game_status"], "")


class TestSlates(unittest.TestCase):
    def test_week11_venues_from_game_centre(self):
        r = rows("week11_slate.csv")
        self.assertEqual(len(r), 13)
        for x in r:
            self.assertTrue(x["venue_stadium_gamecentre"].strip())
            self.assertTrue(x["game_url"].startswith("https://www.nfl.com/games/"))

    def test_week12_venue_blank_except_den_pit(self):
        r = rows("week12_slate.csv")
        self.assertEqual(len(r), 16)
        filled = [x for x in r if x["venue_stadium_gamecentre"]]
        self.assertEqual(len(filled), 1)
        self.assertEqual(filled[0]["home"], "PIT")
        self.assertEqual(filled[0]["venue_stadium_gamecentre"], "ACRISURE STADIUM")

    def test_week10_monday_settlement(self):
        r = rows("week10_finals.csv")
        self.assertEqual(len(r), 14)
        mnf = [x for x in r if x["game_date"] == "2026-11-16"]
        self.assertEqual(len(mnf), 1)
        x = mnf[0]
        self.assertEqual((x["away"], x["away_score"], x["home"], x["home_score"]),
                         ("LAC", "23", "BAL", "20"))
        self.assertEqual(x["status"], "FINAL")

    def test_readme_snapshot_reconciles(self):
        """6,246 (weeks 1-9 PF) + 45 (Thursday) + 632 (13 games) == 6,923 standings PF."""
        w10 = rows("week10_finals.csv")
        thu = [x for x in w10 if x["game_date"] == "2026-11-12"]
        self.assertEqual(len(thu), 1)
        thu_pf = int(thu[0]["away_score"]) + int(thu[0]["home_score"])
        self.assertEqual(thu_pf, 45)
        rest = [x for x in w10 if x["game_date"] != "2026-11-12"]
        rest_pf = sum(int(x["away_score"]) + int(x["home_score"]) for x in rest)
        self.assertEqual(rest_pf, 632)
        self.assertEqual(6246 + thu_pf + rest_pf, 6923)


class TestRegisters(unittest.TestCase):
    def test_requirements_have_gate_and_clearing(self):
        r = rows("requirements.csv")
        self.assertEqual(len(r), 60)
        for x in r:
            self.assertTrue(x["blocking_gate"].strip(), x["req_id"])
            self.assertTrue(x["clears_when"].strip(), x["req_id"])

    def test_suggestions_not_auto_implemented(self):
        for x in rows("suggestions.csv"):
            self.assertEqual(x["pending_human_choice"], "yes")
            self.assertEqual(x["decision"].strip(), "")

    def test_flagged_do_not_block_merge(self):
        for x in rows("flagged.csv"):
            self.assertEqual(x["blocking_merge"], "no")
            self.assertEqual(x["published_on_flagged_page"], "yes")

    def test_reverification_verdicts_present(self):
        r = rows("reverification.csv")
        self.assertEqual(len(r), 15)
        for x in r:
            self.assertTrue(x["verdict"].strip())
            self.assertTrue(x["retest_result"].strip())

    def test_flag_recheck_findings_present(self):
        r = rows("flag_recheck.csv")
        self.assertEqual(len(r), 24)
        for x in r:
            self.assertTrue(x["retest_finding"].strip(), x["flag_id"])
            self.assertTrue(x["retest_source"].startswith("http"), x["flag_id"])


class TestCaptureHonesty(unittest.TestCase):
    def test_capture_log_hashes_verify(self):
        from nfl_a67ddef8 import capture
        self.assertEqual(capture.verify_capture_log(), [])

    def test_capture_log_claims_are_modest(self):
        r = rows("capture_log.csv")
        self.assertEqual(len(r), 13)
        for x in r:
            self.assertIn("cannot prove what the page said", x["artifact_sha_covers"])
            self.assertTrue(x["read_on_utc"].endswith("Z"))

    def test_capture_helpers_roundtrip(self):
        from nfl_a67ddef8 import capture
        path, digest = capture.write_raw("_test_roundtrip.md", "hello capture\n")
        try:
            self.assertEqual(len(digest), 64)
            self.assertTrue(os.path.exists(path))
            self.assertEqual(capture.sha256_file(path), digest)
            self.assertTrue(capture.utc_now().endswith("Z"))
        finally:
            os.remove(path)


class TestSite(unittest.TestCase):
    def test_pages_exist_without_inputs(self):
        self.assertTrue(os.path.isdir(DOCS))
        pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
        self.assertEqual(pages, ["captures.html", "flags.html", "index.html",
                                 "registers.html", "reverification.html", "sources.html"])
        for fn in pages:
            text = open(os.path.join(DOCS, fn), encoding="utf-8").read()
            for tag in ("<input", "<select", "<textarea", "<button"):
                self.assertNotIn(tag, text, f"{fn} contains {tag}")

    def test_build_is_deterministic(self):
        def snap():
            return {fn: hashlib.sha256(
                open(os.path.join(DOCS, fn), "rb").read()).hexdigest()
                for fn in os.listdir(DOCS) if fn.endswith(".html")}
        r1 = subprocess.run([sys.executable,
                             os.path.join(REPO, "scripts", "build_nfl_a67ddef8.py")],
                            capture_output=True, text=True)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        h1 = snap()
        r2 = subprocess.run([sys.executable,
                             os.path.join(REPO, "scripts", "build_nfl_a67ddef8.py")],
                            capture_output=True, text=True)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(h1, snap())

    def test_checker_passes(self):
        r = subprocess.run([sys.executable,
                            os.path.join(REPO, "scripts", "check_nfl_a67ddef8.py")],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
