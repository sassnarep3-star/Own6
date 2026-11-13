"""Regression tests for the NFL-309921cc pack.

Runs under both ``python3 tools/run_tests.py`` (bare stdlib) and ``pytest``.
"""

from __future__ import annotations

import csv
import math
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_309921cc import dataset as D  # noqa: E402
from nfl_309921cc import stats  # noqa: E402
from nfl_309921cc import verified as V  # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-309921cc")


# ---------------------------------------------------------------- statistics
class TestStats(unittest.TestCase):
    def test_pearson_perfect_and_negative(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(stats.pearson(xs, xs), 1.0)
        self.assertAlmostEqual(stats.pearson(xs, list(reversed(xs))), -1.0)

    def test_pearson_undefined_on_zero_variance(self):
        self.assertIsNone(stats.pearson([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(stats.pearson([1, 2], [1, 2]))  # n < 3

    def test_spearman_matches_known_value(self):
        xs = [1, 2, 3, 4, 5]
        ys = [5, 6, 7, 8, 7]
        self.assertIsNotNone(stats.spearman(xs, ys))
        self.assertAlmostEqual(stats.spearman(xs, xs), 1.0)

    def test_rank_handles_ties(self):
        self.assertEqual(stats.rank([1, 1, 2]), [1.5, 1.5, 3.0])

    def test_ols_recovers_known_line(self):
        xs = [float(i) for i in range(20)]
        ys = [2.0 + 3.0 * x for x in xs]
        fit = stats.ols_simple(xs, ys)
        self.assertAlmostEqual(fit["intercept"], 2.0, places=6)
        self.assertAlmostEqual(fit["slope"], 3.0, places=6)
        self.assertAlmostEqual(fit["r2"], 1.0, places=9)
        self.assertAlmostEqual(sum(fit["residuals"]), 0.0, places=6)

    def test_ols_slope_p_value_is_significant_for_strong_signal(self):
        xs = [float(i) for i in range(30)]
        ys = [3.0 * x + (i % 3) * 0.1 for i, x in enumerate(xs)]
        fit = stats.ols_simple(xs, ys)
        self.assertLess(fit["p_slope"], 1e-6)

    def test_t_distribution_two_sided(self):
        # t = 0 gives p = 1; large |t| gives p close to 0
        self.assertAlmostEqual(stats.t_sf_two_sided(0.0, 10), 1.0, places=9)
        self.assertLess(stats.t_sf_two_sided(10.0, 10), 1e-5)
        # symmetry
        self.assertAlmostEqual(stats.t_sf_two_sided(2.0, 15),
                               stats.t_sf_two_sided(-2.0, 15), places=12)

    def test_fisher_ci_contains_point_estimate(self):
        ci = stats.fisher_z_ci(0.5, 32)
        self.assertIsNotNone(ci)
        self.assertLess(ci[0], 0.5)
        self.assertGreater(ci[1], 0.5)

    def test_bootstrap_ci_is_deterministic(self):
        xs = [float(i) for i in range(30)]
        ys = [float((i * 7) % 13) for i in range(30)]
        a = stats.percentile_bootstrap_ci(xs, ys, draws=500, seed=1)
        b = stats.percentile_bootstrap_ci(xs, ys, draws=500, seed=1)
        self.assertEqual(a, b)

    def test_binomial_two_sided(self):
        # 5/5 heads against p=0.5 -> p = 2 * 0.5^5 = 0.0625
        self.assertAlmostEqual(stats.binomial_two_sided_p(5, 5, 0.5), 0.0625, places=9)
        self.assertAlmostEqual(stats.binomial_two_sided_p(0, 5, 0.5), 0.0625, places=9)
        self.assertGreater(stats.binomial_two_sided_p(3, 5, 0.5), 0.9)

    def test_brier_and_log_loss(self):
        self.assertAlmostEqual(stats.brier([(1.0, 1), (0.0, 0)]), 0.0)
        self.assertAlmostEqual(stats.brier([(0.5, 1), (0.5, 0)]), 0.25)
        ll = stats.log_loss([(0.5, 1), (0.5, 0)])
        self.assertAlmostEqual(ll, math.log(2.0), places=6)


# ------------------------------------------------------------ verified capture
class TestVerifiedCapture(unittest.TestCase):
    def test_standings_are_complete_and_balanced(self):
        self.assertEqual(len(V.STANDINGS), 32)
        self.assertEqual(sum(r[4] for r in V.STANDINGS), sum(r[5] for r in V.STANDINGS))
        self.assertEqual(sum(r[12] for r in V.STANDINGS), sum(r[13] for r in V.STANDINGS))
        self.assertEqual(len({r[3] for r in V.STANDINGS}), 32)

    def test_standings_records_are_internally_consistent(self):
        for row in V.STANDINGS:
            conf, div, team, abbr, w, l, t, pct, *_rest = row
            games = w + l + t
            self.assertGreater(games, 0)
            expected = (w + 0.5 * t) / games
            self.assertAlmostEqual(float(pct), expected, places=3,
                                   msg=f"{abbr}: pct {pct} vs computed {expected}")

    def test_slate_covers_28_distinct_clubs(self):
        clubs = set()
        for g in V.SLATE:
            clubs.add(g[5])
            clubs.add(g[7])
        self.assertEqual(len(clubs), 28)

    def test_byes_do_not_overlap_the_slate(self):
        playing = set()
        for g in V.SLATE:
            playing.add(g[5])
            playing.add(g[7])
        for abbr, _rec, _url in V.BYES:
            self.assertNotIn(abbr, playing)
        self.assertEqual(len(V.BYES), 4)

    def test_injury_rows_use_the_official_vocabulary(self):
        practice = {"Did Not Participate In Practice",
                    "Limited Participation in Practice",
                    "Full Participation in Practice"}
        game = {"", "Out", "Questionable", "Doubtful"}
        self.assertEqual(len(V.INJURIES), 326)
        for team, player, pos, _inj, pr, gs in V.INJURIES:
            self.assertIn(pr, practice, f"{team} {player}")
            self.assertIn(gs, game, f"{team} {player}")
            self.assertTrue(pos, f"{team} {player} has no position")
        self.assertEqual(len({r[0] for r in V.INJURIES}), 28)
        self.assertEqual(len({(r[0], r[1]) for r in V.INJURIES}), len(V.INJURIES))

    def test_every_slated_club_has_an_injury_table(self):
        covered = {r[0] for r in V.INJURIES}
        for g in V.SLATE:
            self.assertIn(g[5], covered)
            self.assertIn(g[7], covered)

    def test_depth_charts_always_have_a_first_string(self):
        for team, unit, slot, strings in V.DEPTH_CHARTS:
            self.assertTrue(strings and strings[0], f"{team} {slot} has no first string")
            self.assertIn(unit, ("Offense", "Defense"))


# ------------------------------------------------------------------ derivation
class TestDerived(unittest.TestCase):
    def test_injury_load_sums_to_the_capture(self):
        load = D.injury_load_rows()
        self.assertEqual(sum(r["players_listed"] for r in load), len(V.INJURIES))
        for r in load:
            self.assertEqual(
                int(r["did_not_participate"]) + int(r["limited"]) + int(r["full"]),
                int(r["players_listed"]))

    def test_designated_counts_match_the_raw_capture(self):
        load = D.injury_load_rows()
        total_out = sum(r["designated_out"] for r in load)
        self.assertEqual(total_out, sum(1 for r in V.INJURIES if r[5] == "Out"))

    def test_deficiency_scores_are_within_range_and_labelled(self):
        for r in D.depth_deficiency_rows():
            score = float(r["deficiency_score"])
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            self.assertEqual(r["score_kind"], "proposed_weight_not_observed")

    def test_starter_out_raises_the_deficiency_score(self):
        rows = {(r["team_abbr"], r["unit"], r["position_slot"]): r
                for r in D.depth_deficiency_rows()}
        # Lions: Cade Mays (1st string C) is Out -> Juice Scruggs (2nd string) is active
        det_c = rows[("DET", "Offense", "C")]
        self.assertEqual(det_c["active_string"], "2")
        self.assertEqual(det_c["active_player"], "Juice Scruggs")
        self.assertEqual(float(det_c["deficiency_score"]), 0.65)

    def test_second_string_out_behind_questionable_starter(self):
        rows = {(r["team_abbr"], r["unit"], r["position_slot"]): r
                for r in D.depth_deficiency_rows()}
        # Patriots RB: Stevenson (1st) Questionable, Henderson (2nd) Out -> Kiner is 3rd
        ne_rb = rows[("NE", "Offense", "RB")]
        self.assertIn("TreVeyon Henderson", ne_rb["ruled_out_in_slot"])
        self.assertEqual(float(ne_rb["deficiency_score"]), 0.35)
        self.assertEqual(ne_rb["next_available_backup"], "Corey Kiner")
        self.assertEqual(ne_rb["next_backup_string"], "3")

    def test_unlisted_designations_are_reported_without_identity_claims(self):
        rows = D.unlisted_designated_rows()
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["name_match_is_verified_identity"],
                             "no - string prefix only, not an identity claim")

    def test_correlations_are_measured_and_finite(self):
        for r in D.correlation_rows():
            self.assertEqual(r["status"], "measured_from_verified_official_data")
            c = float(r["coefficient"])
            p = float(r["p_value"])
            self.assertTrue(-1.0 <= c <= 1.0)
            self.assertTrue(0.0 <= p <= 1.0)
            self.assertEqual(r["n"], 32)

    def test_headline_correlation_reproduces_independently(self):
        idx = D.team_index()
        abbrs = [r[3] for r in V.STANDINGS]
        xs = [idx[a]["net_ppg"] for a in abbrs]
        ys = [idx[a]["win_pct"] for a in abbrs]
        independent = stats.pearson(xs, ys)
        published = [r for r in D.correlation_rows()
                     if r["correlation_id"] == "NFL3-COR-03"][0]
        self.assertAlmostEqual(float(published["coefficient"]), independent, places=4)

    def test_luck_residuals_sum_to_zero(self):
        rows, summary = D.luck_rows()
        self.assertEqual(len(rows), 32)
        self.assertAlmostEqual(sum(float(r["luck_residual_win_pct"]) for r in rows),
                               0.0, places=2)
        self.assertGreater(float(summary["r2"]), 0.0)
        self.assertLessEqual(float(summary["r2"]), 1.0)

    def test_final_game_is_not_modelled(self):
        lines, check = D.originated_line_rows()
        final = [r for r in lines if r["model_applicability"].startswith("already_final")]
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]["originated_home_spread"], "")
        self.assertEqual(final[0]["originated_total"], "")
        for r in lines:
            self.assertEqual(r["originated_moneyline_home_prob"], "")
            self.assertEqual(r["market_spread"], "")
            self.assertEqual(r["market_total"], "")
            self.assertEqual(r["closing_line_value"], "")
            self.assertEqual(r["status"], "model_output")
        self.assertEqual(check["games_modelled"], 13)
        self.assertEqual(check["games_excluded_already_final"], 1)

    def test_model_total_is_close_to_the_league_rate(self):
        _lines, check = D.originated_line_rows()
        league = float(check["league_points_per_game_both_teams"])
        model = float(check["model_mean_total"])
        # The model is deliberately parameter-free; if it drifted more than 3
        # points per game from the league's own rate the inputs are wrong.
        self.assertLess(abs(model - league), 3.0)

    def test_strategies_are_all_unqualified(self):
        gate_ids = {g[0] for g in D.GATES}
        for s in D.strategy_rows():
            self.assertEqual(s["qualified"], "no")
            self.assertEqual(int(s["selections_graded"]), 0)
            for g in s["required_gates"].split(","):
                self.assertIn(g, gate_ids)

    def test_gate_counts(self):
        gates = D.gate_rows()
        self.assertEqual(len(gates), 12)
        self.assertEqual(sum(1 for g in gates if g["status"] == "open"), 4)

    def test_no_monetary_reward_anywhere(self):
        tiers, entries = D.leaderboard_rows()
        for t in tiers:
            self.assertIn("non-monetary", t["monetary_value"])
        for e in entries:
            self.assertEqual(e["reward_awarded"], "not_awarded")


# ------------------------------------------------------------------- artefacts
class TestArtefacts(unittest.TestCase):
    def _read(self, name):
        path = os.path.join(D.DATA_DIR, name)
        with open(path, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    def test_csvs_exist_and_are_sourced(self):
        names = ["sources.csv", "repo_findings.csv", "standings_2026_w10.csv",
                 "week10_slate.csv", "week10_byes.csv", "week10_injuries.csv",
                 "week10_injury_load.csv", "depth_charts.csv",
                 "depth_deficiency.csv", "depth_unlisted_designations.csv",
                 "decision_ledger.csv", "suggestions.csv", "strategies.csv",
                 "validation_gates.csv", "correlations.csv", "luck_index.csv",
                 "originated_lines.csv", "leaderboard_tiers.csv",
                 "leaderboard_entries.csv", "flagged.csv"]
        for n in names:
            rows = self._read(n)
            self.assertTrue(rows, f"{n} is empty")
            cols = [c for c in rows[0] if "url" in c or "reference" in c]
            self.assertTrue(cols, f"{n} has no source column")
            for r in rows:
                self.assertTrue(any((r.get(c) or "").startswith("https://") for c in cols),
                                f"{n}: unsourced row")

    def test_pages_have_no_input_elements(self):
        pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
        self.assertGreaterEqual(len(pages), 16)
        for p in pages:
            with open(os.path.join(DOCS, p), encoding="utf-8") as fh:
                html = fh.read()
            self.assertNotRegex(html, r"<input\b", f"{p} has an input element")
            self.assertIn("<table", html, f"{p} has no table")


if __name__ == "__main__":
    unittest.main(verbosity=2)
