"""Regression tests for the 6cefc476 NFL pack (stdlib unittest; also runs under pytest)."""
from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_6cefc476 import model as M  # noqa: E402

DATA = ROOT / "data" / "nfl_6cefc476"
SITE = ROOT / "docs" / "nfl-6cefc476"


def load(name):
    with (DATA / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestModelMath(unittest.TestCase):
    def test_fair_american(self):
        self.assertEqual(M.fair_american(0.5), -100)
        self.assertEqual(M.fair_american(0.6), -150)
        self.assertEqual(M.fair_american(0.4), 150)
        self.assertEqual(M.fair_american(0.75), -300)
        self.assertEqual(M.fair_american(0.25), 300)

    def test_expected_points(self):
        home, away = M.expected_points(24.0, 18.0, 22.0, 20.0, hfa=0.0)
        self.assertAlmostEqual(home, (24.0 + 20.0) / 2)
        self.assertAlmostEqual(away, (22.0 + 18.0) / 2)

    def test_norm_cdf_symmetry(self):
        self.assertAlmostEqual(M.norm_cdf(0.0), 0.5)

    def test_pearson_known(self):
        r = M.pearson_r([1, 2, 3, 4], [2, 4, 6, 8])
        self.assertAlmostEqual(r, 1.0)
        r2 = M.pearson_r([1, 2, 3, 4], [4, 3, 2, 1])
        self.assertAlmostEqual(r2, -1.0)

    def test_p_value_reproduces_published_prior_value(self):
        # Published in the earlier NFL3-COR-01 row (data/nfl_309921cc/correlations.csv):
        # pearson r=0.6984, n=32 -> p=8.80942e-06.  That value was computed from the
        # unrounded r; recomputing from the rounded 0.6984 lands within 0.2%.
        p = M.corr_p_value(0.6984, 32)
        self.assertAlmostEqual(p, 8.80942e-06, delta=1e-7)

    def test_p_value_known_t_critical(self):
        # t(0.975, df=30) = 2.04523 -> two-sided p = 0.05.
        # r = t / sqrt(t^2 + df) = 2.04523 / sqrt(30 + 4.1830) = 0.34982.
        # (tolerance reflects r given to 5 decimal places only)
        p = M.corr_p_value(0.34982, 32)
        self.assertAlmostEqual(p, 0.05, delta=1e-3)

    def test_fisher_ci_reproduces_published_prior_value(self):
        lo, hi = M.fisher_ci95(0.6984, 32)
        self.assertAlmostEqual(lo, 0.4622, places=3)
        self.assertAlmostEqual(hi, 0.8420, places=3)

    def test_sample_std(self):
        self.assertAlmostEqual(M.sample_std([2, 4, 4, 4, 5, 5, 7, 9]), 2.13809, places=4)


class TestSettlement(unittest.TestCase):
    def test_side_covers(self):
        # Home favored by 3 (fair_spread_home=-3); home wins by 7 -> home covers.
        self.assertEqual(M.settle_side(10, 17, -3.0), "win")
        self.assertEqual(M.settle_side(17, 10, -3.0), "loss")
        self.assertEqual(M.settle_side(14, 17, -3.0), "push")

    def test_side_away_favored(self):
        self.assertEqual(M.settle_side(21, 10, 3.0), "win")   # pick away; away covers
        self.assertEqual(M.settle_side(10, 21, 3.0), "loss")

    def test_total(self):
        self.assertEqual(M.settle_total(21, 21, 41.5), "win")   # 42 > 41.5
        self.assertEqual(M.settle_total(20, 21, 41.5), "loss")  # 41 < 41.5
        self.assertEqual(M.settle_total(21, 20, 41.0), "push")

    def test_ml(self):
        self.assertEqual(M.settle_ml(10, 20, 0.7), "win")   # pick home; home wins
        self.assertEqual(M.settle_ml(20, 10, 0.7), "loss")
        self.assertEqual(M.settle_ml(20, 10, 0.3), "win")   # pick away


class TestDepthAndDemotion(unittest.TestCase):
    def test_depth(self):
        d = M.depth_of_replacement(1, 3)
        self.assertEqual(d, {"depth_of_replacement": 3, "replacement_step": 2})

    def test_demotion_triggers(self):
        stats = {"clv_mean": -0.02, "clv_n": 120, "roi_lb95": -0.1, "graded_n": 250,
                 "drawdown_sigma": 3.4, "input_stale_days": 9,
                 "feed_integrity_ok": False, "regime_break_review_ok": False}
        fired = M.evaluate_demotion(stats)
        for rid in ("DG-01", "DG-02", "DG-03", "DG-04", "DG-05", "DG-06"):
            self.assertIn(rid, fired)

    def test_demotion_quiet(self):
        stats = {"clv_mean": 0.01, "clv_n": 120, "roi_lb95": 0.02, "graded_n": 250,
                 "drawdown_sigma": 1.0, "input_stale_days": 2,
                 "feed_integrity_ok": True, "regime_break_review_ok": True}
        self.assertEqual(M.evaluate_demotion(stats), [])

    def test_demotion_small_n_no_trigger(self):
        stats = {"clv_mean": -0.5, "clv_n": 5, "roi_lb95": -0.9, "graded_n": 10,
                 "drawdown_sigma": 0.1, "input_stale_days": 0,
                 "feed_integrity_ok": True, "regime_break_review_ok": True}
        self.assertEqual(M.evaluate_demotion(stats), [])


class TestDataIntegrity(unittest.TestCase):
    def test_wave_ordering_and_completeness(self):
        orig = load("originated_lines.csv")
        self.assertEqual(len(orig), 78)
        orders = [(int(r["origination_wave"]), int(r["origination_order"])) for r in orig]
        self.assertEqual([w for w, _ in orders], sorted(w for w, _ in orders))
        by_game = {}
        for r in orig:
            by_game.setdefault(r["game_id"], {})[r["market_type"]] = int(r["origination_order"])
        for gid, m in by_game.items():
            self.assertEqual(set(m), {"side_spread", "total", "moneyline"})
            self.assertLess(m["side_spread"], m["total"])
            self.assertLess(m["total"], m["moneyline"])

    def test_market_and_difference_blank(self):
        for r in load("originated_lines.csv"):
            self.assertEqual(r["market_line"], "")
            self.assertEqual(r["line_difference"], "")
            self.assertIn("N6F-04", r["flag_id"])

    def test_price_store_open_close_per_market(self):
        snaps = load("price_snapshots.csv")
        kinds: dict[str, set] = {}
        for r in snaps:
            kinds.setdefault(r["market_id"], set()).add(r["snapshot_type"])
        self.assertEqual(len(kinds), 78)
        for mid, kinds_set in kinds.items():
            self.assertEqual(kinds_set, {"open", "close"})

    def test_results_verified(self):
        rows = load("results_feed.csv")
        self.assertEqual(len(rows), 16)
        for r in rows:
            self.assertEqual(r["verification_status"], "verified_direct")
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/games/"))

    def test_sigma_matches_published(self):
        results = load("results_feed.csv")
        margins = [int(r["margin_home"]) for r in results if r["week"] == "9"]
        sigma = M.sample_std([float(x) for x in margins])
        for r in load("originated_lines.csv"):
            self.assertEqual(r["sigma_margin_used"], f"{sigma:.4f}")
            self.assertEqual(r["sigma_n"], str(len(margins)))

    def test_correlations_publish_n(self):
        rows = load("correlations.csv")
        self.assertGreaterEqual(len(rows), 9)
        for r in rows:
            self.assertTrue(r["n"].strip())
        measured = [r for r in rows if r["status"].startswith("measured")]
        self.assertGreaterEqual(len(measured), 5)
        for r in measured:
            self.assertTrue(r["coefficient"].strip())

    def test_depth_blank_without_source(self):
        rows = load("replacement_depth.csv")
        verified = [r for r in rows if r["depth_of_replacement"]]
        self.assertGreaterEqual(len(verified), 12)
        for r in rows:
            if r["depth_of_replacement"]:
                self.assertTrue(r["depth_source_url"].startswith("https://"))
                self.assertTrue(r["injured_string"])
            else:
                self.assertEqual(r["replacement_string"], "")
                self.assertTrue(r["flag_id"])

    def test_leaderboard_separation(self):
        rows = load("leaderboard.csv")
        self.assertGreaterEqual(len(rows), 6)
        for r in rows:
            self.assertEqual(r["staking_can_escalate_signal"], "no")
            self.assertEqual(r["staking_roi"], "")
            self.assertEqual(r["reward"], "not_awarded")

    def test_demotion_gate_rows(self):
        rows = load("demotion_gate.csv")
        self.assertGreaterEqual(len(rows), 6)
        self.assertTrue(any("LIVE -> PAPER" in r["action"] for r in rows))

    def test_league_totals_reconcile(self):
        rows = load("standings_2026_11_14.csv")
        self.assertEqual(len(rows), 32)
        self.assertEqual(sum(int(r["w"]) for r in rows), sum(int(r["l"]) for r in rows))
        self.assertEqual(sum(int(r["pf"]) for r in rows), sum(int(r["pa"]) for r in rows))

    def test_suggestions_pending(self):
        rows = load("suggestions.csv")
        self.assertGreaterEqual(len(rows), 12)
        for r in rows:
            self.assertEqual(r["status"], "pending_human_choice")

    def test_site_zero_input_and_row_links(self):
        pages = sorted(SITE.glob("*.html"))
        self.assertGreaterEqual(len(pages), 14)
        for p in pages:
            text = p.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"<(input|form|button|textarea|select)\b", text),
                              f"{p.name} contains an input element")
            body = text.split("<tbody>", 1)
            if len(body) == 2:
                for row in body[1].split("</tbody>")[0].split("<tr>")[1:]:
                    self.assertIn('href="https://', row,
                                  f"{p.name} has a table row without a source link")


if __name__ == "__main__":
    unittest.main()
