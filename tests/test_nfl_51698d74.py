#!/usr/bin/env python3
"""Tests for the nfl_51698d74 pack: identities, arithmetic, capture honesty, site rules.

Run: python3 tests/test_nfl_51698d74.py
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
DATA = os.path.join(REPO, "data", "nfl_51698d74")
DOCS = os.path.join(REPO, "docs", "nfl-51698d74")
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

    def test_week12_all_venues_filled(self):
        r = rows("week12_slate.csv")
        self.assertEqual(len(r), 16)
        for x in r:
            self.assertTrue(x["venue_stadium_gamecentre"].strip())
            self.assertTrue(x["venue_location_gamecentre"].strip())
            self.assertTrue(x["game_url"].startswith("https://www.nfl.com/games/"))

    def test_week12_venue_match_counts(self):
        from collections import Counter
        c = Counter(x["venue_match"] for x in rows("week12_slate.csv"))
        self.assertEqual(c["exact"], 11)
        self.assertEqual(c["mismatch"], 3)
        self.assertEqual(c["variance"], 2)

    def test_week10_monday_settlement(self):
        r = rows("week10_finals.csv")
        self.assertEqual(len(r), 14)
        monday = [x for x in r if x["away"] == "LAC"][0]
        self.assertEqual((monday["away_score"], monday["home_score"]), ("23", "20"))
        self.assertEqual(monday["margin_home"], "-3")


class TestReserve(unittest.TestCase):
    def test_25_rows_window(self):
        r = rows("reserve_list.csv")
        self.assertEqual(len(r), 25)
        dates = sorted(x["date"] for x in r)
        self.assertEqual(dates[0], "2026-11-10")
        self.assertEqual(dates[-1], "2026-11-18")
        self.assertTrue(all(x["transaction"] == "Reserve/Injured" for x in r))


class TestOrigination(unittest.TestCase):
    def test_fair_lines_match_market_blank(self):
        r = rows("originated_lines_check.csv")
        self.assertEqual(len(r), 13)
        for x in r:
            self.assertEqual(x["verdict"], "MATCH")
            for col in ("market_margin_home", "market_total", "market_home_price",
                        "difference_margin", "difference_total"):
                self.assertEqual(x[col], "")

    def test_leaderboard_zero_qualified(self):
        r = rows("leaderboard_check.csv")
        self.assertEqual(len(r), 8)
        for x in r:
            self.assertTrue(x["verdict"].startswith("MATCH"))
            self.assertEqual(x["proper_score_qualified"], "no")

    def test_correlations_n150(self):
        r = rows("correlations_check.csv")
        self.assertEqual(len(r), 4)
        for x in r:
            self.assertEqual(x["n"], "150")
            self.assertTrue(x["fisher_95_lo"])
            self.assertTrue(x["fisher_95_hi"])


class TestRegisters(unittest.TestCase):
    def test_requirements_gates(self):
        r = rows("requirements.csv")
        self.assertEqual(len(r), 80)
        for x in r:
            self.assertTrue(x["blocking_gate"].strip())
            self.assertTrue(x["clears_when"].strip())

    def test_suggestions_undecided(self):
        for x in rows("suggestions.csv"):
            self.assertEqual(x["pending_human_choice"], "yes")
            self.assertEqual(x["decision"], "")

    def test_flagged_nonblocking(self):
        for x in rows("flagged.csv"):
            self.assertEqual(x["blocking_merge"], "no")
            self.assertEqual(x["published_on_flagged_page"], "yes")


class TestCaptureHonesty(unittest.TestCase):
    def test_capture_log_hashes_match(self):
        from nfl_51698d74 import capture
        self.assertEqual(capture.verify_capture_log(), [])

    def test_capture_log_states_limit(self):
        for x in rows("capture_log.csv"):
            self.assertIn("cannot prove what the page said", x["artifact_sha_covers"])


class TestSiteRules(unittest.TestCase):
    def test_six_pages_no_inputs(self):
        pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
        self.assertEqual(pages, ["captures.html", "flags.html", "index.html",
                                 "registers.html", "reverification.html", "sources.html"])
        for fn in pages:
            text = open(os.path.join(DOCS, fn), encoding="utf-8").read()
            for tag in ("<input", "<select", "<textarea", "<button"):
                self.assertNotIn(tag, text)

    def test_determinism(self):
        before = {fn: hashlib.sha256(open(os.path.join(DOCS, fn), "rb").read()).hexdigest()
                  for fn in os.listdir(DOCS) if fn.endswith(".html")}
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_51698d74.py")],
                       check=True, capture_output=True)
        for fn, h in before.items():
            now = hashlib.sha256(open(os.path.join(DOCS, fn), "rb").read()).hexdigest()
            self.assertEqual(now, h)


if __name__ == "__main__":
    unittest.main(verbosity=2)
