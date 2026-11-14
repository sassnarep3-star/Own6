"""Regression tests for the nfl_market pack.

These lock the invariants that make the pack honest. If someone later "fills in"
a market line, hard-codes a correlation, or lets a strategy reach live without a
forward sample, one of these tests fails.
"""

from __future__ import annotations

import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_market import backtest as B  # noqa: E402
from nfl_market import capture as C  # noqa: E402
from nfl_market import correlations as K  # noqa: E402
from nfl_market import demotion as DM  # noqa: E402
from nfl_market import depth as DEP  # noqa: E402
from nfl_market import gates as G  # noqa: E402
from nfl_market import leaderboard as L  # noqa: E402
from nfl_market import model as M  # noqa: E402
from nfl_market import stats as S  # noqa: E402


class TestCaptureIntegrity(unittest.TestCase):
    def test_standings_cover_all_32_clubs(self):
        self.assertEqual(len(C.STANDINGS), 32)
        self.assertEqual(len({r[0] for r in C.STANDINGS}), 32)

    def test_every_team_in_games_appears_in_standings(self):
        teams = {r[0] for r in C.STANDINGS}
        for _w, away, home, *_rest in C.GAMES:
            self.assertIn(away, teams)
            self.assertIn(home, teams)

    def test_game_counts_match_a_real_nfl_week_structure(self):
        # Weeks 1-8 have 16 games each in a 32-team league with no byes;
        # weeks 5-10 introduce byes. The count is asserted only where the
        # capture shows a full slate, so a genuinely odd week is not "fixed".
        by_week = {}
        for w, *_ in C.GAMES:
            by_week[w] = by_week.get(w, 0) + 1
        self.assertEqual(by_week[1], 16)
        self.assertEqual(by_week[2], 16)
        self.assertEqual(by_week[3], 16)
        self.assertEqual(by_week[4], 16)
        self.assertEqual(by_week[6], 14)
        self.assertEqual(by_week[7], 14)
        self.assertEqual(by_week[8], 14)
        self.assertEqual(by_week[9], 15)

    def test_slate_has_no_team_twice(self):
        teams = [t for *_x, a, h in C.SLATE_W10 for t in (a, h)]
        self.assertEqual(len(teams), len(set(teams)))

    def test_byes_and_slate_are_disjoint(self):
        playing = {t for *_x, a, h in C.SLATE_W10 for t in (a, h)}
        self.assertFalse(playing & set(C.BYES_W10), "a bye club is scheduled to play")

    def test_standings_points_reconcile_with_captured_games(self):
        """PF/PA from standings must equal the sum over captured games.

        Standings include the Thursday Week 10 game, so the check runs on
        weeks 1-10 inclusive.
        """
        agg, _ = M.season_totals(C.GAMES, before_week=11)
        for abbr, _w, _l, _t, pf, pa in C.STANDINGS:
            self.assertEqual(agg[abbr]["pf"], pf, "%s points-for mismatch" % abbr)
            self.assertEqual(agg[abbr]["pa"], pa, "%s points-against mismatch" % abbr)


class TestModelInvariants(unittest.TestCase):
    def setUp(self):
        self.agg, _ = M.season_totals(C.GAMES, before_week=10)

    def test_origination_order_is_side_then_total_then_moneyline(self):
        self.assertEqual(M.MARKET_ORDER, ("side", "total", "moneyline"))

    def test_market_line_is_never_invented(self):
        for away, home in (("NE", "DET"), ("KC", "ATL"), ("BUF", "NYJ")):
            m = M.originate_game(self.agg, away, home)
            for market in M.MARKET_ORDER:
                self.assertIsNone(m[market]["market_line"],
                                  "market line was populated with no official source")
                self.assertIsNone(m[market]["difference"],
                                  "difference was computed against a non-existent market line")

    def test_no_line_below_min_games(self):
        early, _ = M.season_totals(C.GAMES, before_week=2)
        m = M.originate_game(early, "NE", "DET")
        self.assertIsNone(m["side"]["model_fair_line"])
        self.assertIn("insufficient_history", m["side"]["status"])

    def test_moneyline_probability_is_a_probability(self):
        m = M.originate_game(self.agg, "KC", "ATL")
        p = m["moneyline"]["model_home_win_prob"]
        self.assertTrue(0.0 < p < 1.0)

    def test_american_odds_round_trip(self):
        self.assertEqual(M._prob_to_american(0.5), -100.0)
        self.assertAlmostEqual(M._prob_to_american(2 / 3), 200.0, places=6)


class TestStats(unittest.TestCase):
    def test_wilson_reference_value(self):
        lo, hi = S.wilson_interval(14, 20)
        self.assertAlmostEqual(lo, 0.48103, places=4)
        self.assertAlmostEqual(hi, 0.85452, places=4)

    def test_student_t_reference_value(self):
        self.assertAlmostEqual(S._student_t_cdf(2.0, 10), 0.963306, places=5)

    def test_perfect_correlation(self):
        r, p, n = S.pearson([1, 2, 3, 4], [2, 4, 6, 8])
        self.assertAlmostEqual(r, 1.0, places=9)
        self.assertEqual(n, 4)

    def test_constant_series_is_not_computable_not_zero(self):
        r, p, n = S.pearson([1, 1, 1, 1], [1, 2, 3, 4])
        self.assertIsNone(r)
        self.assertIsNone(p)

    def test_binomial_extremes(self):
        self.assertAlmostEqual(S.binomial_one_sided_p(0, 10), 1.0, places=10)
        # P(X >= 10 | n=10, p=0.5) = 0.5**10 = 1/1024
        self.assertAlmostEqual(S.binomial_one_sided_p(10, 10), 1 / 1024.0, places=12)


class TestBacktest(unittest.TestCase):
    def test_no_lookahead(self):
        """Week-w origination must not see week-w results."""
        for week in B.BACKTEST_WEEKS:
            agg, _ = M.season_totals(C.GAMES, before_week=week)
            games_used = sum(v["games"] for v in agg.values()) // 2
            expected = len([g for g in C.GAMES if g[0] < week])
            self.assertEqual(games_used, expected, "week %d leaked future games" % week)

    def test_every_graded_row_has_a_verified_score(self):
        verified = {"R%d-%s-%s" % (r["week"], r["away_team"], r["home_team"])
                    for r in B.results_rows() if r["result_status"] == "final_verified"}
        for r in B.backtest_all():
            key = "R%d-%s-%s" % (r["week"], r["away"], r["home"])
            self.assertIn(key, verified)

    def test_moneyline_has_no_roi(self):
        for f in B.family_table(B.backtest_all()):
            if "moneyline" in f["strategy_id"]:
                self.assertIsNone(f["roi"], "moneyline ROI was invented without a price")
                self.assertEqual(f["price_basis"], "no_price_basis_moneyline")

    def test_snapshot_store_is_double_rowed(self):
        rows = B.price_snapshot_rows(B.backtest_all())
        self.assertEqual(len(rows), 3 * len(B.backtest_all()))
        self.assertTrue(all(r["opening_price"] == "" for r in rows))


class TestLeaderboardAndGates(unittest.TestCase):
    def setUp(self):
        self.bt = B.backtest_all()
        self.fams = B.family_table(self.bt)

    def test_signal_and_staking_are_separate_columns(self):
        for r in L.rows(self.fams):
            self.assertIn("signal_score", r)
            self.assertIn("staking_score", r)
            self.assertNotIn("combined_score", r)

    def test_divergence_is_flagged_not_resolved(self):
        rows = L.rows(self.fams)
        flagged = [r for r in rows if r["divergence_flag"]]
        self.assertTrue(flagged, "expected at least one signal/staking divergence in this sample")

    def test_no_strategy_is_live(self):
        for r in G.ladder(self.fams, G.gate_rows(self.fams, K.all_rows())):
            self.assertEqual(r["promotion_granted"], "no")
            self.assertEqual(r["rung"], "paper")

    def test_forward_sample_gate_cannot_be_open(self):
        gates = {g["gate_id"]: g for g in G.gate_rows(self.fams, K.all_rows())}
        self.assertEqual(gates["G09"]["status"], "closed")

    def test_market_comparison_gate_is_closed(self):
        gates = {g["gate_id"]: g for g in G.gate_rows(self.fams, K.all_rows())}
        self.assertEqual(gates["G04"]["status"], "closed")


class TestCorrelations(unittest.TestCase):
    def test_refusals_carry_no_value(self):
        for r in K.refused_rows():
            self.assertEqual(r["correlation_value"], "")
            self.assertTrue(r["status"].startswith("refused"))

    def test_published_rows_carry_n(self):
        for r in K.all_rows():
            if r["status"] in ("published", "insufficient_n"):
                self.assertIsInstance(r["n"], int)
                self.assertGreater(r["n"], 0)

    def test_tautological_row_is_labelled(self):
        row = [r for r in K.all_rows() if r["correlation_id"] == "COR-01"][0]
        self.assertIn("tautological", row["interpretation_note"])


class TestDepth(unittest.TestCase):
    def test_backup_starts_name_a_replacement(self):
        for r in DEP.register_rows("NE") + DEP.register_rows("DET"):
            if r["is_backup_start"] == "yes":
                self.assertNotEqual(r["first_available_player"], "")
                self.assertNotEqual(r["depth_of_replacement"], "")

    def test_rule_injury_report_beats_depth_chart(self):
        """A player ruled Out must never be returned as the available body."""
        for team in ("NE", "DET"):
            rows = DEP.register_rows(team)
            for r in rows:
                if r["first_available_player"]:
                    self.assertNotIn(r["first_available_player"], ("",))
                    self.assertNotEqual(r["replacement_designation"], "Out")

    def test_ne_rb_skips_out_second_string(self):
        row = [r for r in DEP.register_rows("NE") if r["position_slot"] == "RB"][0]
        # Stevenson (Q) 1st, Henderson (Out) 2nd, Kiner 3rd, Larison 4th.
        self.assertEqual(row["starter_designation"], "Questionable")
        self.assertEqual(int(row["depth_if_starter_scratched"]), 3)


class TestDemotion(unittest.TestCase):
    def test_thresholds_are_published(self):
        for key in ("D1_trailing_window", "D2_max_drawdown_units", "D3_max_p_vs_fair_coin"):
            self.assertIn(key, DM.THRESHOLDS)

    def test_a_losing_strategy_is_demoted(self):
        table = DM.gate_table(B.backtest_all())
        self.assertTrue(any(r["triggers_fired"] != "none" for r in table))
        self.assertTrue(all(r["lifecycle_status"] != "live" for r in table))

    def test_clearing_triggers_does_not_promote(self):
        table = DM.gate_table(B.backtest_all())
        for r in table:
            self.assertNotIn("live_eligible", r["lifecycle_status"])


if __name__ == "__main__":
    unittest.main()
