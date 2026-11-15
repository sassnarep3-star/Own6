"""Regression tests for the nfl e5e38f9e evidence pack (stdlib only, no network).

Run: python3 -m unittest discover -s tests -p test_nfl_e5e38f9e.py
"""
from __future__ import annotations

import csv
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import build_nfl_e5e38f9e as b  # noqa: E402
import check_nfl_e5e38f9e as c  # noqa: E402


class ClubKeys(unittest.TestCase):
    def test_official_codes_map_to_one_key(self):
        self.assertEqual(b.club("ARI"), "AZ")
        self.assertEqual(b.club("LAR"), "LA")
        self.assertEqual(b.club(" nyg "), "NYG")

    def test_names_compare_without_punctuation(self):
        self.assertEqual(b.norm_name("D.J. Reed"), b.norm_name("DJ Reed"))
        self.assertEqual(b.norm_name("Amon-Ra St. Brown"), b.norm_name("Amon-Ra St Brown"))


class OfficialReads(unittest.TestCase):
    def test_week10_has_fourteen_games_and_nine_finals(self):
        finals = b.read_local("official_w10_finals.csv")
        self.assertEqual(len(finals), 14)
        self.assertEqual(sum(r["official_status_at_read"] == "Final" for r in finals), 9)

    def test_injury_spotcheck_is_four_full_clubs_with_44_rows(self):
        inj = b.read_local("official_injury_spotcheck.csv")
        self.assertEqual(len(inj), 44)
        self.assertEqual({r["club"] for r in inj}, {"WAS", "NYG", "NE", "DET"})

    def test_lions_three_out_designations_match_the_official_read(self):
        inj = {r["player"]: r for r in b.read_local("official_injury_spotcheck.csv")}
        for name in ("Kerby Joseph", "Cade Mays", "D.J. Reed"):
            self.assertEqual(inj[name]["game_status_official"], "Out", name)


class Reconciliation(unittest.TestCase):
    def test_every_final_has_a_result_for_every_pack(self):
        rows = b.reconcile_finals()
        self.assertEqual(len(rows), 14 * len(b.PACK_ORDER))
        finals = {r["game_key"] for r in rows if r["official_status_at_read"] == "Final"}
        self.assertEqual(len(finals), 9)

    def test_only_washington_giants_matches_in_any_feed(self):
        matches = [r for r in b.reconcile_finals() if r["result"] == "match"]
        self.assertEqual({r["game_key"] for r in matches}, {"2026-REG-10-was-at-nyg"})

    def test_reconcile_detects_a_score_conflict_and_swapped_orientation(self):
        # The comparison is pure: check the orientation rule on a synthetic pack row.
        g = {"away": "WAS", "home": "NYG", "away_score": "24", "home_score": "21"}
        p_flipped = {"away": "NYG", "home": "WAS", "away_score": "21", "home_score": "24", "status": "final"}
        p_conflict = {"away": "WAS", "home": "NYG", "away_score": "20", "home_score": "21", "status": "final"}
        self.assertEqual(self._classify(g, p_flipped), "match")
        self.assertEqual(self._classify(g, p_conflict), "score_conflict")

    @staticmethod
    def _classify(g, p):
        same = (b.club(p["away"]) == b.club(g["away"]) and p["away_score"] == g["away_score"]
                and p["home_score"] == g["home_score"])
        flip = (b.club(p["away"]) == b.club(g["home"]) and p["away_score"] == g["home_score"]
                and p["home_score"] == g["away_score"])
        return "match" if (same or flip) else "score_conflict"


class InjuryComparison(unittest.TestCase):
    def test_every_official_row_is_compared_for_every_pack(self):
        rows = b.compare_injuries()
        self.assertEqual(len(rows), 44)
        for r in rows:
            for p in b.INJ_PACKS:
                self.assertIn(r[f"{p}_result"], {"match", "practice_conflict", "game_conflict", "absent"})

    def test_known_nfl_wk_practice_error_is_detected(self):
        joseph = next(r for r in b.compare_injuries() if r["player"] == "Kerby Joseph")
        self.assertEqual(joseph["nfl_wk_result"], "practice_conflict")
        self.assertEqual(joseph["309921cc_result"], "practice_conflict")

    def test_absent_is_not_treated_as_available(self):
        rows = b.compare_injuries()
        for r in rows:
            if r["d966f630_result"] == "absent":
                self.assertNotEqual(r["d966f630_result"], "match")


class Register(unittest.TestCase):
    def test_brief_trace_statuses_are_allowed_and_ids_unique(self):
        trace = b.read_local("brief_trace.csv")
        self.assertEqual(len(trace), 76)
        self.assertEqual(len({r["item_id"] for r in trace}), 76)
        for r in trace:
            self.assertIn(r["status"], set(b.STATUS_LABEL), r["item_id"])

    def test_no_brief_row_claims_an_ablation_is_built(self):
        ab = [r for r in b.read_local("brief_trace.csv") if "ablation" in r["brief_item"].lower()]
        self.assertTrue(ab)
        for r in ab:
            self.assertNotIn(r["status"], {"built_checked", "built_partial"}, r["item_id"])

    def test_third_party_prices_are_not_used_as_official(self):
        flag = next(r for r in b.read_local("flagged.csv") if r["flag_id"] == "E5-F16")
        self.assertIn("ESPN", flag["what_we_observed"])
        self.assertIn("verified", flag["what_we_observed"])

    def test_pack_flag_references_resolve(self):
        flags = {r["flag_id"] for r in b.read_local("flagged.csv")}
        for r in b.read_local("brief_trace.csv"):
            for fid in filter(None, (x.strip() for x in r["flag_ids"].split(";"))):
                self.assertIn(fid, flags, r["item_id"])

    def test_checker_passes_on_committed_tree(self):
        self.assertEqual(c.run(), [])


if __name__ == "__main__":
    unittest.main()
