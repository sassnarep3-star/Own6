#!/usr/bin/env python3
"""Tests for the nfl_ade166a4 pack: delta honesty, identities, arithmetic, site rules.

Run: python3 tests/test_nfl_ade166a4.py
No network, no pytest dependency (this repo's CI runs plain python3 for pack tests).
"""
from __future__ import annotations

import csv
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_ade166a4")
DATA_A = os.path.join(REPO, "data", "nfl_a67ddef8")
DOCS = os.path.join(REPO, "docs", "nfl-ade166a4")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from src.nfl_ade166a4.build_data import (  # noqa: E402
    compute_delta, parse_injuries, parse_standings, parse_schedule, parse_transactions,
)


def rows(name: str, base: str = DATA) -> list[dict]:
    with open(os.path.join(base, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestSameDayDelta(unittest.TestCase):
    def test_both_reads_parse_to_253_players_plus_2_markers(self):
        first = parse_injuries(os.path.join(DATA_A, "raw", "injuries_reg11_2026-11-19.md"))
        second = parse_injuries(os.path.join(DATA, "raw", "injuries_reg11_2026-11-19_b.md"))
        for label, parsed in (("first", first), ("second", second)):
            players = [r for r in parsed if r["row_class"] == "player"]
            markers = [r for r in parsed if r["row_class"] == "marker"]
            self.assertEqual(len(players), 253, label)
            self.assertEqual(len(markers), 2, label)

    def test_delta_is_zero_across_253_keys(self):
        first = parse_injuries(os.path.join(DATA_A, "raw", "injuries_reg11_2026-11-19.md"))
        second = parse_injuries(os.path.join(DATA, "raw", "injuries_reg11_2026-11-19_b.md"))
        delta, summary = compute_delta(first, second)
        self.assertEqual(delta, [])
        self.assertEqual(summary["rows_first_read"], 253)
        self.assertEqual(summary["rows_second_read"], 253)
        self.assertEqual(summary["added"], 0)
        self.assertEqual(summary["removed"], 0)
        self.assertEqual(summary["changed_fields"], 0)
        self.assertEqual(summary["player_keys_unchanged"], 253)
        self.assertTrue(summary["games_identical"])

    def test_compute_delta_detects_a_synthetically_added_row(self):
        """Guard: the delta machinery must not be a constant zero."""
        first = parse_injuries(os.path.join(DATA_A, "raw", "injuries_reg11_2026-11-19.md"))
        second = parse_injuries(os.path.join(DATA, "raw", "injuries_reg11_2026-11-19_b.md"))
        synthetic = dict(second[0])
        synthetic["player"] = "Synthetic Player"
        synthetic["row_class"] = "player"
        delta, summary = compute_delta(first, second + [synthetic])
        added = [d for d in delta if d["change_class"] == "added"]
        self.assertEqual(len(added), 1)
        self.assertEqual(summary["added"], 1)

    def test_compute_delta_detects_a_status_change(self):
        first = parse_injuries(os.path.join(DATA_A, "raw", "injuries_reg11_2026-11-19.md"))
        second = parse_injuries(os.path.join(DATA, "raw", "injuries_reg11_2026-11-19_b.md"))
        changed = [dict(r) for r in second]
        for r in changed:
            if r["row_class"] == "player" and r["team"] == "Colts":
                r["game_status"] = "Doubtful"
                break
        delta, summary = compute_delta(first, changed)
        self.assertEqual(summary["changed_fields"], 1)
        self.assertEqual(delta[0]["field"], "game_status")
        self.assertEqual(delta[0]["value_second_read"], "Doubtful")

    def test_summary_csv_matches_the_pinned_result(self):
        s = rows("delta_summary.csv")[0]
        self.assertEqual(int(s["rows_first_read"]), 253)
        self.assertEqual(int(s["rows_second_read"]), 253)
        self.assertEqual(int(s["added"]) + int(s["removed"]) + int(s["changed_fields"]), 0)
        self.assertEqual(s["games_identical"], "True")

    def test_delta_register_is_empty(self):
        self.assertEqual(rows("delta_reg11_sameday.csv"), [])


class TestStandingsSecondRead(unittest.TestCase):
    def test_32_clubs_and_totals(self):
        r = rows("standings_2026_11_19b.csv")
        self.assertEqual(len(r), 32)
        self.assertEqual(sum(int(x["w"]) for x in r), 149)
        self.assertEqual(sum(int(x["l"]) for x in r), 149)
        self.assertEqual(sum(int(x["t"]) for x in r), 2)
        pf = sum(int(x["pf"]) for x in r)
        pa = sum(int(x["pa"]) for x in r)
        self.assertEqual(pf, 6923)
        self.assertEqual(pf, pa)

    def test_standings_equal_first_read_row_for_row(self):
        first = {x["club"]: x for x in rows("standings_2026_11_19.csv", DATA_A)}
        second = rows("standings_2026_11_19b.csv")
        self.assertEqual(len(second), 32)
        for x in second:
            f = first[x["club"]]
            self.assertEqual((x["w"], x["l"], x["t"], x["pf"], x["pa"]),
                             (f["w"], f["l"], f["t"], f["pf"], f["pa"]),
                             f"{x['club']} differs between same-day reads")

    def test_every_row_sourced(self):
        for x in rows("standings_2026_11_19b.csv"):
            self.assertEqual(x["source_url"], "https://www.nfl.com/standings/division/2026/reg")


class TestInjuriesSecondRead(unittest.TestCase):
    def test_counts_and_status_vocabulary(self):
        r = rows("injuries_reg11_b.csv")
        players = [x for x in r if x["player"] != "(no injuries reported)"]
        markers = [x for x in r if x["player"] == "(no injuries reported)"]
        self.assertEqual(len(players), 253)
        self.assertEqual(len(markers), 2)
        self.assertEqual(len({x["game"] for x in r}), 13)
        statuses = [x for x in players if x["game_status"]]
        self.assertEqual(len(statuses), 16)
        self.assertTrue(all(x["game_status"] in ("Out", "Questionable") for x in statuses))
        self.assertTrue(all(x["practice_status"] in (
            "Full Participation in Practice", "Limited Participation in Practice",
            "Did Not Participate In Practice") for x in players))

    def test_injuries_equal_first_read_row_for_row(self):
        key = lambda x: (x["team"], x["player"])
        first = {key(x): x for x in rows("injuries_reg11.csv", DATA_A)
                 if x["player"] != "(no injuries reported)"}
        second = [x for x in rows("injuries_reg11_b.csv")
                  if x["player"] != "(no injuries reported)"]
        self.assertEqual(len(second), 253)
        for x in second:
            f = first[key(x)]
            self.assertEqual((x["position"], x["injury"], x["practice_status"], x["game_status"]),
                             (f["position"], f["injury"], f["practice_status"], f["game_status"]),
                             f"{x['team']}/{x['player']} differs between same-day reads")

    def test_ir_players_corroborated_against_reserve_list(self):
        reserve = {x["who"] for x in rows("reserve_nov2026_b.csv")}
        injuries = {x["player"] for x in rows("injuries_reg11_b.csv")}
        for name in ("Azeez Al-Shaair (HOU)", "Jaylon Carlies (IND)"):
            self.assertIn(name, reserve)
            self.assertIn(name.replace(" (HOU)", "").replace(" (IND)", ""), injuries)


class TestScheduleSecondRead(unittest.TestCase):
    def test_13_games_and_no_overlap(self):
        slate = rows("week11_slate_b.csv")
        self.assertEqual(len(slate), 13)
        teams = [t for r in slate for t in (r["away"], r["home"])]
        self.assertEqual(len(teams), 26)
        self.assertEqual(len(set(teams)), 26)


class TestTransactions(unittest.TestCase):
    def test_reserve_and_trade_counts(self):
        self.assertEqual(len(rows("reserve_nov2026_b.csv")), 25)
        self.assertEqual(len(rows("trades_nov2026_b.csv")), 12)

    def test_reserve_matches_first_read(self):
        """The 09:01Z first read lives in the a67ddef8 raw artifact (section A rows
        'date | club | name | kind'); compare the player-name sets."""
        import re
        raw = open(os.path.join(DATA_A, "raw", "misc_reads_2026-11-19.md"), encoding="utf-8").read()
        section_a = raw.split("## B.")[0]
        first_names = set(re.findall(r"^\d{2}/\d{2} \| [A-Z]{2,3} \| (.+?) \| Reserve/Injured$",
                                     section_a, re.M))
        self.assertEqual(len(first_names), 25)
        for x in rows("reserve_nov2026_b.csv"):
            name = x["who"].split(" (")[0]
            self.assertIn(name, first_names, f"{name} absent from the 09:01Z reserve read")

    def test_no_waddle_trade_row(self):
        trades = rows("trades_nov2026_b.csv")
        self.assertFalse(any("Waddle" in x["who"] for x in trades))


class TestSite(unittest.TestCase):
    PAGES = ["index.html", "delta.html", "captures.html", "flags.html",
             "registers.html", "reverification.html", "sources.html"]

    def test_all_pages_exist(self):
        for p in self.PAGES:
            self.assertTrue(os.path.exists(os.path.join(DOCS, p)), p)

    def test_no_inputs_or_placeholders(self):
        for p in self.PAGES:
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            for tag in ("<input", "<select", "<textarea", "<button"):
                self.assertNotIn(tag, text, p)
            for bad in ("TODO", "lorem", "XXX", "{{"):
                self.assertNotIn(bad, text, p)

    def test_no_forbidden_value_tokens(self):
        import re
        pat = re.compile(r"\b(ROI|CLV|closing line|profit|units|stake)\b", re.I)
        for p in self.PAGES:
            text = open(os.path.join(DOCS, p), encoding="utf-8").read()
            self.assertIsNone(pat.search(text), p)


class TestCaptureLog(unittest.TestCase):
    def test_hashes_match_artifacts(self):
        import hashlib
        for r in rows("capture_log.csv"):
            path = os.path.join(REPO, r["artifact_path"])
            h = hashlib.sha256(open(path, "rb").read()).hexdigest()
            self.assertEqual(h, r["artifact_sha256"], r["read_id"])
            self.assertTrue(r["read_on_utc"].endswith("Z"), r["read_id"])
            self.assertIn("cannot prove", r["note"], r["read_id"])

    def test_all_reads_are_official(self):
        for r in rows("capture_log.csv"):
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/"), r["read_id"])


class TestParsers(unittest.TestCase):
    def test_parse_standings_on_synthetic_line(self):
        text = ["## AFC East", "Fake Club | 1 | 2 | 3 | 0.333 | 10 | 20 | -10 | 1L"]
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("\n".join(text))
            path = fh.name
        try:
            out = parse_standings(path)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["club"], "Fake Club")
            self.assertEqual(out[0]["net_pts"], -10)
        finally:
            os.unlink(path)

    def test_parse_transactions_sections(self):
        text = ["## Reserve List — November 2026", "11/18 | A (PIT) | Reserve/Injured",
                "## Trades — November 2026", "11/10 | B (A → JAX) | Traded"]
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("\n".join(text))
            path = fh.name
        try:
            self.assertEqual(len(parse_transactions(path, "Reserve List")), 1)
            self.assertEqual(len(parse_transactions(path, "Trades")), 1)
        finally:
            os.unlink(path)

    def test_parse_schedule_handles_network_extras(self):
        text = ["2026-11-23 | 8:15 PM | ESPN (+2) | Bengals (CIN) 7-2 | at | Commanders (WAS) 3-5-1"]
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write("\n".join(text))
            path = fh.name
        try:
            out = parse_schedule(path)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0]["network"], "ESPN (+2)")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
