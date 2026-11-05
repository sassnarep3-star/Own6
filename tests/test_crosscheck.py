"""Regression tests for the independent cross-check section (stdlib unittest).

These tests attack the publication rules rather than the NBA facts: an unverified
value must never be smuggled into a page, a "match" verdict must be earned, and the
comparison tables must keep the counts the checker pins.
"""
from __future__ import annotations

import csv
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_crosscheck  # noqa: E402
import check_crosscheck  # noqa: E402


class CrosscheckDataTests(unittest.TestCase):
    def test_data_files_pass_the_checker(self):
        self.assertEqual(check_crosscheck.check_data_errors(), [])

    def test_pages_pass_the_checker(self):
        self.assertEqual(check_crosscheck.check_page_errors(), [])

    def test_archive_deduplicates_to_121_finals(self):
        games = build_crosscheck.load_archive()
        self.assertEqual(len(games), 121)
        self.assertEqual(min(g["date"] for g in games.values()), "2026-10-20")
        self.assertEqual(max(g["date"] for g in games.values()), "2026-11-04")

    def test_standings_reconcile_three_ways(self):
        games = build_crosscheck.load_archive()
        _, summary = build_crosscheck.standings_compare(games)
        self.assertEqual(summary["rows"], 30)
        self.assertEqual(summary["two_reader_matches"], 30)
        self.assertEqual(summary["archive_matches"], 30)
        self.assertEqual(summary["delta_matches"], 30)
        self.assertEqual(summary["teams_idle_nov4"], ["ORL", "GSW"])

    def test_wins_balance(self):
        games = build_crosscheck.load_archive()
        records = build_crosscheck.records(games)
        self.assertEqual(sum(w for w, _ in records.values()), 121)
        self.assertEqual(sum(l for _, l in records.values()), 121)

    def test_pearson_matches_published_coefficients(self):
        games = build_crosscheck.load_archive()
        home = [g["home_score"] for g in games.values()]
        away = [g["away_score"] for g in games.values()]
        self.assertAlmostEqual(build_crosscheck.pearson(home, away), 0.1994, places=4)

    def test_pearson_of_a_line_is_one(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        self.assertAlmostEqual(build_crosscheck.pearson(xs, xs), 1.0, places=9)

    def test_exact_binomial_reproduces_the_published_mcnemar_p(self):
        # 7 model-only vs 17 baseline-only wins is the published discordant split
        self.assertAlmostEqual(build_crosscheck.exact_binom_two_sided(7, 24), 0.06391, places=5)

    def test_exact_binomial_is_symmetric_and_bounded(self):
        self.assertAlmostEqual(
            build_crosscheck.exact_binom_two_sided(3, 10),
            build_crosscheck.exact_binom_two_sided(7, 10),
            places=12,
        )
        self.assertEqual(build_crosscheck.exact_binom_two_sided(5, 10), 1.0)

    def test_blank_official_counts_stay_blank(self):
        games = build_crosscheck.load_archive()
        rows = build_crosscheck.games_completeness(games)
        october = [r for r in rows if r["date"] < "2026-11-01"]
        self.assertTrue(october)
        for row in october:
            self.assertEqual(row["official_game_count"], "")
            self.assertEqual(row["status"], "unverified")

    def test_future_dates_are_not_scored_as_mismatches(self):
        games = build_crosscheck.load_archive()
        rows = build_crosscheck.games_completeness(games)
        future = [r for r in rows if r["date"] > build_crosscheck.LAST_RESULT_DATE]
        self.assertTrue(future)
        for row in future:
            self.assertNotEqual(row["match"], "NO")
            self.assertEqual(row["status"], "not_applicable")

    def test_played_dates_match_official_counts(self):
        games = build_crosscheck.load_archive()
        rows = [r for r in build_crosscheck.games_completeness(games) if r["match"]]
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r["match"] == "yes" for r in rows))


class CrosscheckPublicationTests(unittest.TestCase):
    def test_claim_verdicts_are_from_the_allowed_set(self):
        with (build_crosscheck.CD / "claims.csv").open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                self.assertIn(row["verdict"], {"match", "DRIFT", "not_recomputable"}, row["claim_id"])

    def test_gate_count_drift_is_recorded(self):
        with (build_crosscheck.CD / "claims.csv").open(newline="", encoding="utf-8") as handle:
            drift = [r for r in csv.DictReader(handle) if r["verdict"] == "DRIFT"]
        self.assertEqual([r["claim_id"] for r in drift], ["C13"])

    def test_every_flag_has_a_source_and_a_severity(self):
        path = build_crosscheck.CD / "flags.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                self.assertIn(row["severity"], {"high", "medium", "low"})
                self.assertTrue(row["source_url"].startswith("https://"), row["id"])

    def test_market_columns_are_blank_not_zero(self):
        html = (build_crosscheck.OUT / "slate.html").read_text(encoding="utf-8")
        self.assertIn('class="empty"', html)
        self.assertNotIn("edge = 0", html)

    def test_unverified_cell_marker_detected(self):
        # a silent blank cell must be rejected by the checker's own rule
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text(
                "<table><tbody><tr><td>row</td><td></td>"
                '<td><a href="https://www.nba.com/standings">src</a></td></tr></tbody></table>',
                encoding="utf-8",
            )
            errors = check_crosscheck.inspect_page(page)
        self.assertTrue(any("silent blank" in e for e in errors))

    def test_row_without_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text(
                "<table><tbody><tr><td>row</td><td>1</td><td>no link</td></tr></tbody></table>",
                encoding="utf-8",
            )
            errors = check_crosscheck.inspect_page(page)
        self.assertTrue(any("without an official source link" in e for e in errors))

    def test_broken_internal_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            (Path(tmp) / "blank.html").write_text("", encoding="utf-8")
            page.write_text('<a href="missing.html">x</a>', encoding="utf-8")
            errors = check_crosscheck.inspect_page(page)
        self.assertTrue(any("broken internal link" in e for e in errors))

    def test_conflict_marker_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "page.html"
            page.write_text("<<<<<<< HEAD\n", encoding="utf-8")
            errors = check_crosscheck.inspect_page(page)
        self.assertTrue(any("conflict" in e or "marker" in e.lower() for e in errors))


if __name__ == "__main__":
    unittest.main()
