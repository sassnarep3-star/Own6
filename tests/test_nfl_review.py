"""Regression tests for the consolidated NFL review pack (session arena/44136693-own6).

Standard-library only, so the suite runs with `python3 tools/run_tests.py` as
well as with pytest.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs", "nfl-review")
DATA = os.path.join(ROOT, "data", "nfl_review")

OFFICIAL_HOSTS = (
    "nfl.com", "operations.nfl.com", "support.nfl.com", "itl.nist.gov",
    "docs.scipy.org", "scikit-learn.org", "www.statsmodels.org", "aglc.ca",
    "github.com", "api.github.com", "codeload.github.com", "docs.github.com",
    "sassnarep3-star.github.io",
)


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def pages():
    return sorted(f for f in os.listdir(SITE) if f.endswith(".html"))


class TestBuild(unittest.TestCase):
    def test_pages_exist(self):
        self.assertEqual(len(pages()), 9)

    def test_build_reproduces_committed_pages(self):
        res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_nfl_review.py"), "--check"],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_checker_passes(self):
        res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "check_nfl_review.py")],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_reconciliation_reproduces(self):
        res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_nfl_review.py"), "--check"],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


class TestPublicationRules(unittest.TestCase):
    def test_no_manual_input(self):
        for page in pages():
            html = open(os.path.join(SITE, page), encoding="utf-8").read().lower()
            for token in ("<input", "<form", "<textarea", "<select"):
                self.assertNotIn(token, html, f"{page} contains {token}")

    def test_every_data_row_has_a_source_link(self):
        for page in pages():
            html = open(os.path.join(SITE, page), encoding="utf-8").read()
            for row in re.findall(r"<tr>(.*?)</tr>", html, re.S):
                if "<th>" in row:
                    continue
                self.assertRegex(row, r'<a href="https://', f"{page} has a row without an https source link")

    def test_relative_links_resolve(self):
        for page in pages():
            html = open(os.path.join(SITE, page), encoding="utf-8").read()
            for href in re.findall(r'href="([^"]+)"', html):
                if href.startswith(("http", "#", "mailto:")):
                    continue
                target = href.split("#")[0]
                if not target:
                    continue
                self.assertTrue(os.path.exists(os.path.normpath(os.path.join(SITE, target))),
                                f"{page}: broken relative link {href}")

    def test_no_placeholder_text_in_cells(self):
        for page in pages():
            html = open(os.path.join(SITE, page), encoding="utf-8").read()
            for cell in re.findall(r"<td>(.*?)</td>", html, re.S):
                text = re.sub(r"<[^>]+>", "", cell).strip().lower()
                self.assertNotIn(text, ("tbd", "n/a", "???", "unknown", "placeholder"),
                                 f"{page} publishes a placeholder value")

    def test_source_urls_use_official_hosts(self):
        for name in os.listdir(DATA):
            if not name.endswith(".csv"):
                continue
            for r in rows(name):
                for key, value in r.items():
                    if not key.endswith("url") and "source" not in key:
                        continue
                    if not value or not value.startswith("http"):
                        continue
                    host = re.sub(r"^https?://([^/]+).*$", r"\1", value)
                    self.assertTrue(any(host == h or host.endswith("." + h) for h in OFFICIAL_HOSTS),
                                    f"{name}: {key} points at a non-official host {host}")


class TestLedgerCoverage(unittest.TestCase):
    def test_ledger_covers_every_published_injury_row(self):
        covered = {r["published_row_id"] for r in rows("value_reconciliation.csv")}
        for name, field in (("injury_and_depth_deficiency.csv", "case_id"), ("injuries_and_depth.csv", "id")):
            for base in ("nfl_origination", "nfl_3b81013c"):
                path = os.path.join(ROOT, "data", base, name)
                if not os.path.exists(path):
                    continue
                with open(path, newline="", encoding="utf-8") as fh:
                    for row in csv.DictReader(fh):
                        self.assertIn(row[field], covered, f"{row[field]} missing from the ledger")

    def test_every_ledger_row_has_a_result_and_source(self):
        for r in rows("value_reconciliation.csv"):
            self.assertTrue(r["result"])
            self.assertTrue(r["official_source_url"].startswith("https://"))

    def test_ledger_counts_are_stable(self):
        counts = {}
        for r in rows("value_reconciliation.csv"):
            counts[r["result"]] = counts.get(r["result"], 0) + 1
        self.assertGreater(counts.get("match", 0), 150)
        self.assertGreater(counts.get("differs", 0), 0)

    def test_every_flag_is_published(self):
        html = open(os.path.join(SITE, "flagged.html"), encoding="utf-8").read()
        for r in rows("irregularities.csv"):
            self.assertIn(r["flag_id"], html)

    def test_every_source_read_is_published(self):
        html = open(os.path.join(SITE, "sources.html"), encoding="utf-8").read()
        for r in rows("official_reads.csv"):
            self.assertIn(r["read_id"], html)
            self.assertIn(r["url"], html)


class TestOfficialRead(unittest.TestCase):
    def test_standings_cover_all_32_clubs(self):
        st = rows("standings_read_2026_11_13.csv")
        self.assertEqual(len(st), 32)
        self.assertEqual(len({r["abbr"] for r in st}), 32)
        self.assertEqual(sum(int(r["w"]) for r in st), sum(int(r["l"]) for r in st))
        self.assertEqual(sum(int(r["pf"]) for r in st), sum(int(r["pa"]) for r in st))

    def test_standings_rows_are_internally_consistent(self):
        for r in rows("standings_read_2026_11_13.csv"):
            games = int(r["w"]) + int(r["l"]) + int(r["t"])
            self.assertGreater(games, 0)
            self.assertEqual(int(r["net_pts"]), int(r["pf"]) - int(r["pa"]))

    def test_slate_has_fourteen_games_and_four_byes(self):
        sl = rows("slate_week10_read_2026_11_13.csv")
        games = [r for r in sl if not r["slot_id"].startswith("W10-BYE")]
        byes = [r for r in sl if r["slot_id"].startswith("W10-BYE")]
        self.assertEqual(len(games), 14)
        self.assertEqual(len(byes), 4)
        self.assertEqual(len({r["away_abbr"] for r in games} | {r["home_abbr"] for r in games}), 28)

    def test_injury_designations_use_the_official_vocabulary(self):
        allowed = {"OUT", "DOUBTFUL", "QUESTIONABLE", "NO DESIGNATION"}
        for r in rows("injury_status_read_2026_11_13.csv"):
            self.assertIn(r["designation"], allowed)

    def test_injury_capture_covers_both_teams_of_each_week_10_game(self):
        sl = [r for r in rows("slate_week10_read_2026_11_13.csv") if not r["slot_id"].startswith("W10-BYE")]
        inj = rows("injury_status_read_2026_11_13.csv")
        clubs = {r["team"] for r in inj}
        for game in sl:
            self.assertIn(game["away_team"], clubs)
            self.assertIn(game["home_team"], clubs)


class TestDecisionRegisters(unittest.TestCase):
    def test_suggestions_are_ranked_without_gaps(self):
        ranks = sorted(int(r["priority_rank"]) for r in rows("suggestions.csv"))
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_every_suggestion_has_evidence_and_status(self):
        for r in rows("suggestions.csv"):
            self.assertTrue(r["evidence_source_url"].startswith("https://"))
            self.assertEqual(r["status"], "proposed_not_implemented")

    def test_decision_questions_are_complete(self):
        for r in rows("decision_questions.csv"):
            for field in ("question_to_decide", "information_held_today", "information_missing",
                          "current_answer", "how_to_discover_the_missing_information"):
                self.assertTrue(r[field].strip(), f"{r['question_id']} is missing {field}")

    def test_leaderboard_records_zero_qualified_strategies(self):
        rows_ = {r["field"]: r for r in rows("leaderboard_status.csv")}
        self.assertEqual(rows_["Current qualified strategies"]["value_or_rule"], "0")
        self.assertEqual(rows_["Current leaderboard rows"]["value_or_rule"], "0")

    def test_no_strategy_is_qualified(self):
        for r in rows("strategy_status.csv"):
            self.assertEqual(r["qualified"], "no")
            self.assertEqual(r["correlation_value"], "")

    def test_depth_deficiency_is_blank_for_every_club(self):
        for r in rows("depth_status.csv"):
            self.assertEqual(r["deficiency_index"], "")

    def test_requirement_coverage_is_complete(self):
        cov = rows("requirement_coverage.csv")
        self.assertGreaterEqual(len(cov), 16)
        for r in cov:
            self.assertTrue(r["requirement_as_stated_by_the_owner"])
            self.assertTrue(r["official_or_primary_source_url"].startswith("https://"))


class TestPr68Provenance(unittest.TestCase):
    def test_pr68_checks_are_recorded(self):
        checks = {r["check_id"]: r for r in rows("pr68_verification.csv")}
        self.assertIn("PR68-01", checks)
        self.assertIn("PR68-06", checks)
        self.assertEqual(checks["PR68-06"]["result"], "fail")  # no licence upstream - an open flag
        self.assertEqual(checks["PR68-07"]["result"], "pass")  # reconstruction reproduced

    def test_pr68_expected_digest_is_the_recorded_one(self):
        checks = {r["check_id"]: r for r in rows("pr68_verification.csv")}
        self.assertTrue(checks["PR68-01"]["expected_value"].startswith("9fe5bd67"))

    def test_pr68_expected_digest_is_consistent_when_the_dataset_is_present(self):
        path = os.path.join(ROOT, "data", "nfl", "model", "games_2015_2026.csv")
        if not os.path.exists(path):
            self.skipTest("the lines-lab dataset is not present in this checkout")
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        self.assertEqual(digest, "9fe5bd67210691255cf90af21e39cc242b606f253dbc65198b7915565ce83090")

    def test_upstream_licence_status_is_recorded_as_unlicensed(self):
        meta_path = os.path.join(ROOT, "data", "nfl", "model", "games_2015_2026.meta.json")
        if not os.path.exists(meta_path):
            self.skipTest("the lines-lab metadata is not present in this checkout")
        meta = json.load(open(meta_path, encoding="utf-8"))
        self.assertEqual(meta.get("license_status"), "unverified")
        self.assertEqual(meta.get("sha256"), "9fe5bd67210691255cf90af21e39cc242b606f253dbc65198b7915565ce83090")


if __name__ == "__main__":
    unittest.main()
