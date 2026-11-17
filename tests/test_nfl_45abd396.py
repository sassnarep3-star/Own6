"""Tests for the nfl_45abd396 pack.

These are adversarial: each one attacks a claim the pack makes. They run under
stdlib unittest and are also collected by tools/run_tests.py.
"""
from __future__ import annotations

import csv
import math
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from nfl_45abd396 import availability as AV  # noqa: E402
from nfl_45abd396 import capture as C  # noqa: E402
from nfl_45abd396 import injury_capture as IC  # noqa: E402
from nfl_45abd396 import registers as RG  # noqa: E402
from nfl_45abd396 import scores as SC  # noqa: E402
from nfl_45abd396 import settle as S  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_45abd396")
DOCS = os.path.join(REPO, "docs", "nfl-45abd396")


def rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


class TestCapture(unittest.TestCase):
    def test_every_week10_card_has_a_unique_id_and_slug(self):
        ids = [c[0] for c in C.W10_CARDS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(C.W10_SLUGS))
        self.assertEqual(len(C.W10_CARDS), 14)

    def test_scores_only_exist_on_final_cards(self):
        for gid, _a, _h, _d, _s, status, asc, hsc, _m in C.W10_CARDS:
            if status == "FINAL":
                self.assertIsInstance(asc, int, gid)
                self.assertIsInstance(hsc, int, gid)
            else:
                self.assertIsNone(asc, gid)
                self.assertIsNone(hsc, gid)

    def test_standings_has_32_clubs_and_pf_equals_pa(self):
        self.assertEqual(len(C.STANDINGS_READ), 32)
        pf = sum(r[5] for r in C.STANDINGS_READ)
        pa = sum(r[6] for r in C.STANDINGS_READ)
        self.assertEqual(pf, pa, "in a closed league total PF must equal total PA")
        self.assertEqual(SC.league_scoring(C.STANDINGS_READ)["pf_equals_pa"], True)

    def test_week11_cards_plus_byes_cover_the_league_once(self):
        clubs = []
        for away, home, *_rest in C.W11_CARDS:
            clubs.extend([away, home])
        clubs.extend(C.W11_BYE_CLUBS)
        self.assertEqual(len(clubs), 30, "13 fixtures + 4 byes = 30 club-slots")
        self.assertEqual(len(set(clubs)), 30, "a club appears twice in week 11")

    def test_injury_hub_has_28_clubs_and_4_absent(self):
        self.assertEqual(len(IC.CLUBS_PRESENT), 28)
        self.assertEqual(len(IC.CLUBS_ABSENT), 4)
        self.assertFalse(set(IC.CLUBS_PRESENT) & set(IC.CLUBS_ABSENT))

    def test_every_hub_row_has_a_practice_or_game_cell(self):
        for club, table in IC.CLUB_TABLES.items():
            for player, _pos, _inj, practice, game in table:
                self.assertTrue(practice or game, f"{club} {player} has neither cell")


class TestSettlement(unittest.TestCase):
    def test_brier_is_squared_error(self):
        self.assertAlmostEqual(S.brier(0.7, 1), 0.09)
        self.assertAlmostEqual(S.brier(0.7, 0), 0.49)

    def test_log_loss_matches_hand_computation(self):
        self.assertAlmostEqual(S.log_loss(0.75, 1), -math.log(0.75))
        self.assertAlmostEqual(S.log_loss(0.75, 0), -math.log(0.25))

    def test_post_kickoff_rows_are_the_thursday_game(self):
        reg = S.settle_all(S.build_register())
        post = [r for r in reg if r["point_in_time"] == "post_kickoff"]
        self.assertTrue(post)
        for r in post:
            self.assertEqual(r["game_id"], "W10-01")
            made = S.parse_iso(r["value_committed_utc"])
            kick = S.parse_iso(r["kickoff_utc"])
            self.assertGreater(made, kick, "a post_kickoff row must be committed after kickoff")

    def test_unsettled_rows_carry_no_score(self):
        for r in S.settle_all(S.build_register()):
            if r["settled"] == "no":
                self.assertEqual(r["brier"], "")
                self.assertEqual(r["actual_winner"], "")
                self.assertTrue(r["settle_reason"])

    def test_every_settled_row_matches_the_official_final(self):
        fin = S.finals()
        for r in S.settle_all(S.build_register()):
            if r["settled"] != "yes":
                continue
            f = fin[r["game_id"]]
            self.assertTrue(f["final"])
            if f["margin_home"] > 0:
                self.assertEqual(r["actual_winner"], f["home"])
            else:
                self.assertEqual(r["actual_winner"], f["away"])


class TestScores(unittest.TestCase):
    def test_sidak_alpha_brackets_the_naive_level(self):
        self.assertAlmostEqual(SC.sidak_alpha(1), 0.05)
        self.assertLess(SC.sidak_alpha(5), 0.05)
        self.assertGreater(SC.sidak_alpha(5), 0.05 / 5)

    def test_binomial_two_sided_at_the_centre_is_large(self):
        self.assertGreater(SC._binom_two_sided(6, 12), 0.9)

    def test_binomial_tail_flags_an_extreme_run(self):
        self.assertLess(SC._binom_two_sided(11, 12), 0.01)

    def test_a_perfect_forecaster_beats_climatology(self):
        rows_ = [{"p_home_win": "0.99", "outcome_home": "1", "brier": "0.0001", "game_id": "g1"},
                 {"p_home_win": "0.01", "outcome_home": "0", "brier": "0.0001", "game_id": "g2"}]
        b = SC.score_block(rows_, "perfect")
        self.assertGreater(b["brier_skill_vs_climatology"], 0.9)

    def test_a_calibration_disaster_scores_negative_skill(self):
        rows_ = [{"p_home_win": "0.99", "outcome_home": "0", "brier": "0.9801", "game_id": "g1"},
                 {"p_home_win": "0.01", "outcome_home": "1", "brier": "0.9801", "game_id": "g2"}]
        b = SC.score_block(rows_, "inverted")
        self.assertLess(b["brier_skill_vs_climatology"], -1.0)

    def test_controls_have_no_probability_information(self):
        reg = [r for r in S.settle_all(S.build_register())
               if r["point_in_time"] == "pre_kickoff" and r["settled"] == "yes"]
        ratings = SC.rating_table(C.STANDINGS_READ)
        for kind in ("coin", "favourite"):
            ctrl = SC.control_rows(reg, kind, ratings)
            self.assertTrue(ctrl)
            for r in ctrl:
                self.assertEqual(r["p_home_win"], 0.5, f"{kind} smuggled in a probability")


class TestAvailability(unittest.TestCase):
    def test_no_actual_start_is_ever_claimed(self):
        for node in AV.availability_graph_nodes():
            self.assertEqual(node["actual_start"], "")
            self.assertEqual(node["actual_snap_share"], "")
            self.assertTrue(node["blank_reason_actual"])

    def test_deltas_only_compare_clubs_read_before(self):
        deltas = AV.injury_deltas()
        covered = {r["club"] for r in AV.load_prior_series()}
        for d in deltas:
            self.assertIn(d["club"], covered, "a delta claims change in a club never read before")

    def test_reserve_list_exposes_the_not_listed_case(self):
        reserve = AV.reserve_rows()
        absent = [r for r in reserve if r["appears_on_week10_hub_at_this_read"] == "no"]
        self.assertGreaterEqual(len(absent), 10)
        self.assertTrue(any(r["player"] == "Malik Willis" for r in absent))

    def test_the_stale_trade_is_detected(self):
        trades = AV.trade_rows()
        stale = [t for t in trades if t["stale_risk"].startswith("yes")]
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0]["player"], "Daiyan Henley")

    def test_rollup_never_names_a_replacement(self):
        for r in AV.club_rollup():
            self.assertEqual(r["replacement_named_on_official_page"], "")
            self.assertEqual(r["actual_starters_evidence"], "")
            self.assertTrue(r["blank_reason_replacement"])


class TestRegisters(unittest.TestCase):
    def test_every_question_has_a_discovery_route_and_valid_status(self):
        for q in RG.QUESTIONS:
            self.assertIn(q["status"], {"ANSWERED", "PARTIAL", "OPEN", "BLOCKED"})
            self.assertTrue(q["discovery_route"])

    def test_answered_questions_carry_an_official_source(self):
        for q in RG.QUESTIONS:
            if q["status"] == "ANSWERED":
                self.assertTrue(q["source_url"].startswith("https://"))

    def test_every_suggestion_can_be_decided(self):
        for s in RG.SUGGESTIONS:
            self.assertTrue(s["review_state"])
            self.assertIn("decided_by", s)
            self.assertIn("decision_date", s)
            self.assertTrue(s["what_it_would_take_to_validate"])

    def test_every_gate_states_a_numeric_clearing_condition(self):
        for g in RG.GATES:
            self.assertTrue(g[4].strip(), g[0])
            self.assertIn(g[1], {"open", "blocked", "closed"})


class TestProvenance(unittest.TestCase):
    def test_frozen_provenance_records_the_mutation(self):
        entry = S.FIRST_ADD_COMMIT["data/nfl_wk/own_lines.csv"]
        self.assertEqual(entry[3], 2, "the mutated file must record two commits")
        self.assertEqual(entry[2], "c0eb6efc8a0be37907f78d2da69cf24949a2174e")
        for path, e in S.FIRST_ADD_COMMIT.items():
            self.assertEqual(len(e[2]), 40, path)
            self.assertEqual(e[1], e[2][:8], path)

    def test_deleted_forecast_row_is_published_but_not_scored(self):
        d = rows("deleted_forecast_rows.csv")
        self.assertEqual(len(d), 1)
        self.assertEqual(d[0]["game_id"], "W10-01")
        self.assertEqual(d[0]["settled_here"], "no")
        self.assertTrue(d[0]["reason_not_settled"])
        scored = [r for r in rows("settled_forecasts.csv")
                  if r["strategy_id"] == "WK-ML" and r["game_id"] == "W10-01"]
        self.assertEqual(scored, [], "a deleted row must not be re-scored")

    def test_every_register_row_records_how_many_commits_touched_its_file(self):
        for r in rows("forecast_register.csv"):
            self.assertIn(r["commits_touching_file"], {"1", "2"})


class TestPublishedArtifacts(unittest.TestCase):
    def test_leaderboard_matches_the_settled_rows(self):
        pre = [r for r in rows("settled_forecasts.csv") if r["point_in_time"] == "pre_kickoff"]
        for r in rows("leaderboard_settled.csv"):
            sample = [x for x in pre if x["strategy_id"] == r["strategy_id"] and x["settled"] == "yes"]
            b = sum(float(x["brier"]) for x in sample) / len(sample)
            self.assertAlmostEqual(b, float(r["brier_model"]), places=6)
            self.assertEqual(int(r["n_games_settled"]), len(sample))

    def test_no_page_makes_a_profit_claim(self):
        for name in os.listdir(DOCS):
            if not name.endswith(".html"):
                continue
            with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
                body = fh.read().lower()
            for phrase in ("guaranteed", "units won", "sure thing", "risk-free"):
                self.assertNotIn(phrase, body, f"{name} contains {phrase}")

    def test_no_page_has_an_input_control(self):
        for name in os.listdir(DOCS):
            if not name.endswith(".html"):
                continue
            with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
                body = fh.read().lower()
            self.assertNotIn("<input", body, name)
            self.assertNotIn("<form", body, name)

    def test_no_strategy_is_published_as_qualified(self):
        for r in rows("leaderboard_settled.csv"):
            self.assertEqual(r["qualified_on_skill"], "no")
            self.assertLessEqual(float(r["cluster_lower_95"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
