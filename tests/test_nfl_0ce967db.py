#!/usr/bin/env python3
"""Tests for the nfl-0ce967db pack: identities, chronology, determinism, and the honesty rules.

Run: python3 tests/test_nfl_0ce967db.py
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
DATA = os.path.join(REPO, "data", "nfl_0ce967db")
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_0ce967db import model as M  # noqa: E402
from nfl_0ce967db import score as S  # noqa: E402


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestModelIdentities(unittest.TestCase):
    def test_phi_is_a_cdf(self):
        self.assertAlmostEqual(M._phi(0.0), 0.5, places=12)
        self.assertGreater(M._phi(1.0), 0.84)
        self.assertLess(M._phi(1.0), 0.842)
        self.assertAlmostEqual(M._phi(-1.0) + M._phi(1.0), 1.0, places=12)

    def test_shrinkage_pulls_to_the_league_mean(self):
        self.assertEqual(M._shrunk([], 21.5), 21.5)
        # one game of 40 with k=1 shrinks halfway to the league mean
        self.assertAlmostEqual(M._shrunk([40.0], 20.0), 30.0)
        # many games barely shrink
        self.assertAlmostEqual(M._shrunk([40.0] * 40, 20.0), 40.0 * 40 / 41 + 20.0 / 41)

    def test_recency_weighting_favours_the_newest_game(self):
        self.assertGreater(M._weighted_mean([0.0, 10.0], half_life=2.0),
                           M._weighted_mean([0.0, 10.0], half_life=None))
        self.assertAlmostEqual(M._weighted_mean([5.0, 5.0, 5.0], half_life=2.0), 5.0)

    def test_sigma_is_bounded_by_the_registration(self):
        self.assertEqual(M.sigma_margin([0.0, 0.001, -0.001]), M.SIGMA_FLOOR)
        self.assertEqual(M.sigma_margin([100.0, -100.0, 100.0]), M.SIGMA_CAP)
        self.assertIsNone(M.sigma_margin([1.0, 2.0]))

    def test_tie_is_not_a_home_win(self):
        g = M.Game("x", 5, "AAA", "BBB", 17, 17)
        self.assertEqual(g.home_win, 0)
        self.assertEqual(g.margin, 0)

    def test_total_formula_uses_the_league_TOTAL_not_the_team_mean(self):
        """Regression guard for the fixed bug: MAE must be plausible, not ~24 points."""
        h = M.TeamHistory([24, 27, 20], [20, 17, 30])
        a = M.TeamHistory([17, 20, 13], [24, 30, 27])
        f = M.margin_forecast(h, a, 21.7, 2.5, None, 13.0)
        self.assertGreater(f["expected_total"], 20.0)
        self.assertLess(f["expected_total"], 70.0)

    def test_chronology_assertion_fails_on_lookahead(self):
        g = M.Game("2026-W05-01", 5, "AAA", "BBB", 20, 17)
        h = {"AAA": M.TeamHistory([20], [17]), "BBB": M.TeamHistory([17], [20])}
        M.assert_chronology(g, h, prior_max_week=4)  # fine
        with self.assertRaises(AssertionError):
            M.assert_chronology(g, h, prior_max_week=5)


class TestScoreMath(unittest.TestCase):
    def test_brier_of_perfect_and_worst(self):
        self.assertEqual(S.brier([1.0, 0.0], [1, 0]), 0.0)
        self.assertEqual(S.brier([0.0, 1.0], [1, 0]), 1.0)
        self.assertAlmostEqual(S.brier([0.5, 0.5], [1, 0]), 0.25)

    def test_skill_of_the_control_against_itself_is_zero(self):
        ctrl = [0.6, 0.4, 0.55, 0.5]
        ys = [1, 0, 1, 1]
        self.assertAlmostEqual(S.brier_skill(ctrl, ys, ctrl), 0.0)

    def test_bonferroni_threshold(self):
        b = S.bonferroni(0.001)
        self.assertAlmostEqual(b["threshold"], 0.05 / 7)
        self.assertTrue(b["passes"])
        self.assertFalse(S.bonferroni(0.01)["passes"])

    def test_sign_test_is_two_sided_and_symmetric(self):
        self.assertAlmostEqual(S._exact_sign_two_sided(10, 10), 2 / 1024)
        self.assertAlmostEqual(S._exact_sign_two_sided(0, 10), 2 / 1024)
        self.assertEqual(S._exact_sign_two_sided(5, 10), 1.0)

    def test_bootstrap_is_deterministic(self):
        clusters = {1: [0, 1, 2], 2: [3, 4], 3: [5, 6, 7]}
        vals = [0.1, 0.9, 0.5, 0.2, 0.8, 0.3, 0.7, 0.6]
        a = S.week_cluster_bootstrap(clusters, vals, lambda idx: sum(vals[i] for i in idx) / len(idx))
        b = S.week_cluster_bootstrap(clusters, vals, lambda idx: sum(vals[i] for i in idx) / len(idx))
        self.assertEqual(a, b)
        self.assertLessEqual(a["lo"], a["hi"])

    def test_decomposition_reconstructs_the_brier_score(self):
        probs = [0.7, 0.3, 0.6, 0.4, 0.5, 0.8]
        ys = [1, 0, 1, 0, 1, 1]
        d = S.variance_decomposition(probs, ys)
        self.assertAlmostEqual(d["brier"], d["brier_from_decomposition"], places=12)


class TestPublishedArtifacts(unittest.TestCase):
    def test_no_market_value_is_published(self):
        for r in rows("originated_lines.csv"):
            for f in ("market_margin_home", "market_total", "market_home_price",
                      "difference_margin", "difference_total"):
                self.assertEqual(r[f].strip(), "", f"{r['game_id']} {f}")
        for r in rows("leaderboard.csv"):
            for f in ("roi", "clv", "units"):
                self.assertEqual(r[f].strip(), "", f"{r['strategy_id']} {f}")

    def test_no_candidate_claims_qualification(self):
        for r in rows("leaderboard.csv"):
            if r["proper_score_qualified"] == "yes":
                self.assertGreater(float(r["bss_lower_95_week_cluster"]), 0)
        self.assertFalse(any(r["proper_score_qualified"] == "yes" for r in rows("leaderboard.csv")))

    def test_every_correlation_publishes_n_and_an_interval(self):
        for r in rows("correlations.csv"):
            self.assertTrue(r["n"].strip())
            self.assertTrue(r["fisher_lo95"].strip() and r["fisher_hi95"].strip())
            self.assertGreaterEqual(int(r["n"]), 3)

    def test_every_requirement_has_gate_and_clearing_number(self):
        for r in rows("requirements.csv"):
            self.assertTrue(r["blocking_gate"].strip(), r["req_id"])
            self.assertTrue(r["number_that_would_clear_it"].strip(), r["req_id"])
            self.assertIn("nfl.com", r["source_url"])

    def test_week11_batch_is_registered_before_kickoff(self):
        for r in rows("week11_forecasts.csv"):
            self.assertIn("2026-11-19T01:15Z", r["registered_before_kickoff_utc"])
            self.assertEqual(r["market_line_home"], "")
            self.assertEqual(r["state"], "paper")

    def test_capture_hashes_match_the_artifacts(self):
        for r in rows("capture_log.csv"):
            p = os.path.join(REPO, r["artifact_path"])
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            self.assertEqual(h, r["artifact_sha256"], r["read_id"])


class TestBuildsAreDeterministic(unittest.TestCase):
    def test_run_py_is_byte_stable(self):
        files = ["results_feed.csv", "leaderboard.csv", "model_outputs.csv", "week11_forecasts.csv"]
        before = {n: hashlib.sha256(open(os.path.join(DATA, n), "rb").read()).hexdigest() for n in files}
        subprocess.run([sys.executable, os.path.join(REPO, "src", "nfl_0ce967db", "run.py")],
                       check=True, capture_output=True)
        for n in files:
            now = hashlib.sha256(open(os.path.join(DATA, n), "rb").read()).hexdigest()
            self.assertEqual(before[n], now, n)

    def test_site_builder_is_byte_stable(self):
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_0ce967db.py")],
                       check=True, capture_output=True)
        docs = os.path.join(REPO, "docs", "nfl-0ce967db")
        first = {n: hashlib.sha256(open(os.path.join(docs, n), "rb").read()).hexdigest()
                 for n in sorted(os.listdir(docs)) if n.endswith(".html")}
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_0ce967db.py")],
                       check=True, capture_output=True)
        for n in first:
            now = hashlib.sha256(open(os.path.join(docs, n), "rb").read()).hexdigest()
            self.assertEqual(first[n], now, n)


if __name__ == "__main__":
    unittest.main(verbosity=2)
