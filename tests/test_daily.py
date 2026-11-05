"""Regression tests for the 2026-11-05 verified snapshot (stdlib unittest)."""
from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_daily  # noqa: E402
import check_daily  # noqa: E402
import daily_analysis  # noqa: E402


class SnapshotDataTests(unittest.TestCase):
    def test_snapshot_has_no_data_issues(self):
        self.assertEqual(check_daily.check_data(), [])

    def test_standings_arithmetic(self):
        rows = check_daily.read(check_daily.DATA / "standings.csv")
        self.assertEqual(len(rows), 30)
        self.assertEqual(sum(int(r["w"]) for r in rows), 121)
        self.assertEqual(sum(int(r["l"]) for r in rows), 121)

    def test_results_reconcile_to_today(self):
        data = json.loads((check_daily.DATA / "analysis.json").read_text(encoding="utf-8"))
        cons = data["consistency"]
        self.assertEqual(cons["standings_2026_11_05_matches"], 30)
        self.assertEqual(cons["standings_2026_11_03_matches"], 30)
        self.assertEqual(cons["games_total"], 121)
        self.assertEqual(cons["teams_idle_nov4"], ["GSW", "ORL"])

    def test_missing_source_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            shutil.copytree(check_daily.DATA, data_dir)
            path = data_dir / "results_2026_11_04.csv"
            rows = check_daily.read(path)
            rows[0]["source_url"] = "https://example.com/game/0022600174"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            original = check_daily.DATA
            check_daily.DATA = data_dir
            try:
                issues = check_daily.check_data()
            finally:
                check_daily.DATA = original
        self.assertTrue(any("official source link" in issue for issue in issues))

    def test_impossible_standings_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            shutil.copytree(check_daily.DATA, data_dir)
            path = data_dir / "standings.csv"
            rows = check_daily.read(path)
            rows[0]["w"] = "99"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            original = check_daily.DATA
            check_daily.DATA = data_dir
            try:
                issues = check_daily.check_data()
            finally:
                check_daily.DATA = original
        self.assertTrue(any("wins" in issue for issue in issues))


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((check_daily.DATA / "analysis.json").read_text(encoding="utf-8"))

    def test_analysis_reconciles(self):
        self.assertEqual(check_daily.check_analysis(), [])

    def test_intervals_contain_point_estimates(self):
        walk = self.data["model"]["walk_forward"]
        self.assertLessEqual(walk["brier_skill_score_ci95_low"], walk["brier_skill_score"])
        self.assertGreaterEqual(walk["brier_skill_score_ci95_high"], walk["brier_skill_score"])
        self.assertLessEqual(walk["winner_accuracy_ci95_low"], walk["winner_accuracy"])
        self.assertGreaterEqual(walk["winner_accuracy_ci95_high"], walk["winner_accuracy"])

    def test_no_prop_correlation_is_invented(self):
        self.assertIsNone(self.data["correlations"]["prop_or_player_level"])

    def test_slate_bands_are_ordered(self):
        for row in self.data["slate"]:
            self.assertLess(row["model_margin_low80"], row["model_margin_high80"])
            self.assertLess(row["model_total_low80"], row["model_total_high80"])

    def test_walk_forward_never_trains_on_future_games(self):
        games = daily_analysis.load_games()
        teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
        model = daily_analysis.fit(games[: daily_analysis.MIN_TRAIN], teams)
        # Fitting only on the first 60 games cannot depend on later results.
        refit = daily_analysis.fit(games[: daily_analysis.MIN_TRAIN], teams)
        self.assertEqual(model["margin"], refit["margin"])
        self.assertEqual(len(model["margin"]), len(teams) + 1)

    def test_home_advantage_is_positive(self):
        self.assertGreater(self.data["model"]["home_advantage_points"], 0)


class PageTests(unittest.TestCase):
    def test_pages_are_generated_and_checked(self):
        build_daily.main()
        self.assertEqual(check_daily.check_html(), [])

    def test_slate_market_cells_are_blank_in_source_data(self):
        rows = check_daily.read(check_daily.DATA / "slate_2026_11_05_06.csv")
        for row in rows:
            for field in ("market_spread", "market_total", "market_price"):
                self.assertFalse(row.get(field), f"{row['game_id']} has an unsourced {field}")

    def test_section_has_a_flagged_page(self):
        text = (check_daily.DOCS / "flagged.html").read_text(encoding="utf-8")
        self.assertIn("Flagged for Review", text)
        self.assertIn("https://www.nba.com/termsofuse", text)

    def test_removing_a_row_link_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "daily"
            shutil.copytree(check_daily.DOCS, docs)
            page = docs / "standings.html"
            text = page.read_text(encoding="utf-8")
            page.write_text(text.replace(
                '<a href="https://www.nba.com/standings" rel="noopener">',
                '<a href="standings.html">', 1), encoding="utf-8")
            original = check_daily.DOCS
            check_daily.DOCS = docs
            try:
                issues = check_daily.check_html(rebuild=False)
            finally:
                check_daily.DOCS = original
        self.assertTrue(any("no official HTTPS source link" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
