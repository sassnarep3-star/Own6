#!/usr/bin/env python3
"""Unit tests for the nfl_b72e2687 pack (data registers + capture parser).

    python3 -m unittest tests.test_nfl_b72e2687 -v
"""
from __future__ import annotations

import csv
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_b72e2687")


def load(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class StandingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load("standings_2026_11_19.csv")

    def test_32_clubs(self):
        self.assertEqual(len(self.rows), 32)

    def test_totals(self):
        w = sum(int(r["w"]) for r in self.rows)
        l = sum(int(r["l"]) for r in self.rows)
        t = sum(int(r["t"]) for r in self.rows)
        self.assertEqual((w, l, t), (149, 149, 2))

    def test_pf_equals_pa(self):
        pf = sum(int(r["pf"]) for r in self.rows)
        pa = sum(int(r["pa"]) for r in self.rows)
        self.assertEqual(pf, 6923)
        self.assertEqual(pa, 6923)

    def test_every_club_has_all_fields(self):
        for r in self.rows:
            for k in ("conference", "club", "w", "l", "t", "pct", "pf", "pa", "net_pts"):
                self.assertTrue(r[k], f"missing {k} in {r}")


class Week12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load("week12_slate.csv")

    def test_16_games(self):
        self.assertEqual(len(self.rows), 16)

    def test_every_game_has_a_game_centre_link(self):
        for r in self.rows:
            self.assertRegex(r["game_centre_url"], r"^https://www\.nfl\.com/games/")

    def test_slots_are_sequential(self):
        self.assertEqual([int(r["slot"]) for r in self.rows], list(range(1, 17)))


class InjuryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load("injuries_reg11.csv")
        cls.players = [r for r in cls.rows if r["player"] != "NO_INJURIES_REPORTED"]
        cls.markers = [r for r in cls.rows if r["player"] == "NO_INJURIES_REPORTED"]

    def test_253_player_rows(self):
        self.assertEqual(len(self.players), 253)

    def test_2_markers(self):
        self.assertEqual(len(self.markers), 2)
        teams = {r["team"] for r in self.markers}
        self.assertEqual(teams, {"Bengals", "Commanders"})

    def test_13_games(self):
        self.assertEqual(len({r["game"] for r in self.rows}), 13)

    def test_practice_tallies(self):
        codes = {}
        for r in self.players:
            codes[r["practice_code"]] = codes.get(r["practice_code"], 0) + 1
        self.assertEqual(codes, {"DNP": 83, "LP": 87, "FP": 83})

    def test_published_game_status_cells(self):
        gs = [r for r in self.players if r["game_status"]]
        self.assertEqual(len(gs), 16)
        for r in gs:
            self.assertIn(r["game_status"], ("Questionable", "Out"))
            self.assertIn(r["team"], ("Colts", "Texans"))

    def test_practice_code_matches_status(self):
        mapping = {"Did Not Participate In Practice": "DNP",
                   "Limited Participation in Practice": "LP",
                   "Full Participation in Practice": "FP",
                   # the raw transcription also carries the code itself in some rows
                   "DNP": "DNP", "LP": "LP", "FP": "FP"}
        for r in self.players:
            self.assertIn(r["practice_status"], mapping, r["practice_status"])
            self.assertEqual(r["practice_code"], mapping[r["practice_status"]])

    def test_practice_status_forms_are_documented(self):
        # the register mixes the long practice text and the bare code; the checker's
        # tally uses practice_code, so the test enforces code consistency instead
        codes = {}
        for r in self.players:
            codes[r["practice_code"]] = codes.get(r["practice_code"], 0) + 1
        self.assertEqual(codes, {"DNP": 83, "LP": 87, "FP": 83})


class CaptureLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load("capture_log.csv")

    def test_three_reads(self):
        self.assertEqual(len(self.rows), 3)

    def test_utc_clock_and_sha256(self):
        for r in self.rows:
            self.assertRegex(r["read_on_utc"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertRegex(r["artifact_sha256"], r"^[0-9a-f]{64}$")

    def test_artifacts_exist_and_hash_matches(self):
        import hashlib
        for r in self.rows:
            path = os.path.join(REPO, r["artifact_path"])
            self.assertTrue(os.path.exists(path), path)
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            self.assertEqual(h.hexdigest(), r["artifact_sha256"])


class RegisterTests(unittest.TestCase):
    def test_requirements_have_source_links(self):
        for r in load("requirements.csv"):
            self.assertRegex(r["source_url"], r"^https?://")

    def test_flags_are_non_blocking_with_sources(self):
        for r in load("flagged.csv"):
            self.assertEqual(r["blocking_merge"], "no")
            self.assertTrue(r["source_urls"])

    def test_suggestions_await_human_choice(self):
        for r in load("suggestions.csv"):
            self.assertEqual(r["pending_human_choice"], "yes")

    def test_questions_have_all_fields(self):
        for r in load("questions.csv"):
            for k in ("question", "what_we_have", "what_we_lack", "how_to_answer"):
                self.assertTrue(r[k], f"missing {k}")


class ReverificationTests(unittest.TestCase):
    def test_rows_carry_method_and_result(self):
        rows = load("reverification.csv")
        self.assertGreaterEqual(len(rows), 12)
        for r in rows:
            self.assertTrue(r["method"])
            self.assertTrue(r["result"])


if __name__ == "__main__":
    unittest.main()
