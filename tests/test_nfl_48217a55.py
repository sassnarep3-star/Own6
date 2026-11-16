"""Regression tests for the nfl-48217a55 pack.

Runs under ``python3 -m unittest discover -s tests -p test_nfl_48217a55.py`` (used by the
CI workflow) and under plain ``pytest``.

These are the checks a table cannot make for itself: that the reconstruction arithmetic is
right, that the verification against an independent official page actually matches, that
blank cells are never silently filled, that no replacement is ever named from a report that
names none, that the build is deterministic, and that the pack's own verifier passes.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, REPO)

from nfl_48217a55 import advice as A        # noqa: E402
from nfl_48217a55 import capture as C       # noqa: E402
from nfl_48217a55 import correlate as X     # noqa: E402
from nfl_48217a55 import flags as FL        # noqa: E402
from nfl_48217a55 import gates as G         # noqa: E402
from nfl_48217a55 import injuries as IN     # noqa: E402
from nfl_48217a55 import model as M         # noqa: E402
from nfl_48217a55 import stats as S         # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-48217a55")
DATA = os.path.join(REPO, "data", "nfl_48217a55")


class TestStats(unittest.TestCase):
    def test_pearson_on_a_known_series(self):
        xs = [1, 2, 3, 4, 5]
        self.assertAlmostEqual(S.pearson(xs, xs), 1.0, places=9)
        self.assertAlmostEqual(S.pearson(xs, list(reversed(xs))), -1.0, places=9)

    def test_pearson_is_zero_when_a_series_is_flat(self):
        self.assertEqual(S.pearson([1, 2, 3], [5, 5, 5]), 0.0)

    def test_population_variance_uses_n_not_n_minus_one(self):
        self.assertAlmostEqual(S.pvariance([1, 3]), 1.0, places=9)
        self.assertAlmostEqual(S.pvariance([2, 4, 4, 4, 5, 5, 7, 9]), 4.0, places=9)

    def test_fisher_interval_brackets_the_estimate(self):
        r = S.pearson([1, 2, 3, 4, 5, 6], [2, 1, 4, 3, 6, 5])
        lo, hi = S.fisher_ci(r, 6)
        self.assertLessEqual(lo, r)
        self.assertLessEqual(r, hi)

    def test_wilson_interval_stays_inside_zero_one(self):
        lo, hi = S.wilson_interval(10, 11)
        self.assertGreaterEqual(lo, 0.0)
        self.assertLessEqual(hi, 1.0)
        self.assertLess(lo, 10 / 11)
        self.assertGreater(hi, 10 / 11)

    def test_wilson_interval_survives_a_zero_denominator(self):
        self.assertEqual(S.wilson_interval(0, 0), (0.0, 0.0))

    def test_student_t_sf_is_monotone_and_bounded(self):
        self.assertGreater(S._student_t_sf(0.0, 10), 0.49)
        self.assertLess(S._student_t_sf(0.0, 10), 0.51)
        self.assertGreater(S._student_t_sf(1.0, 10), S._student_t_sf(2.0, 10))
        self.assertGreaterEqual(S._student_t_sf(5.0, 10), 0.0)

    def test_brier(self):
        self.assertAlmostEqual(S.brier(1.0, 1), 0.0)
        self.assertAlmostEqual(S.brier(0.0, 1), 1.0)
        self.assertAlmostEqual(S.brier(0.7, 0), 0.49)


class TestCaptureIntegrity(unittest.TestCase):
    def test_every_source_has_a_url_and_a_read_time(self):
        for sid, url, read_at, chunks, read, what in C.SOURCES:
            self.assertTrue(url.startswith("https://"), sid)
            self.assertTrue(read_at.startswith("2026-11-15"), sid)
            self.assertTrue(read, sid)
            self.assertTrue(what, sid)

    def test_club_alias_map_only_maps_to_known_codes(self):
        known = {c for c, *_ in C.STANDINGS_RENDER}
        for src, dst in C.CLUB_ABBR_ALIASES.items():
            self.assertIn(dst, known, src)

    def test_injury_report_has_the_expected_shape(self):
        for row in C.INJURY_REPORT:
            self.assertEqual(len(row), 6, row)
            club, player, pos, injury, practice, game = row
            self.assertTrue(club)
            self.assertTrue(player)
            self.assertTrue(pos)
            self.assertIn(practice, IN.PRACTICE_STATUSES, row)
            self.assertIn(game, IN.DESIGNATIONS + ("",), row)

    def test_bye_clubs_do_not_appear_on_the_injury_report(self):
        on_report = {r[0] for r in C.INJURY_REPORT}
        for club in C.BYE_CLUBS_WEEK10:
            self.assertNotIn(club, on_report)

    def test_every_club_on_the_report_plays_this_week(self):
        playing = set()
        for _slug, _d, _k, away, home, *_ in C.WEEK10_SLATE:
            playing.add(C.CLUB_ABBR_ALIASES.get(away, away))
            playing.add(C.CLUB_ABBR_ALIASES.get(home, home))
        for club in {r[0] for r in C.INJURY_REPORT}:
            self.assertIn(club, playing, club)


class TestInjuries(unittest.TestCase):
    def setUp(self):
        self.rows = IN.rows()
        self.roll = IN.club_rollup()

    def test_rollup_reconciles_to_the_report(self):
        self.assertEqual(sum(r["rows_on_report"] for r in self.roll), len(self.rows))
        self.assertEqual(
            sum(r["out"] for r in self.roll),
            sum(1 for r in self.rows if r["game_status"] == "Out"),
        )

    def test_one_rollup_row_per_club(self):
        self.assertEqual(len(self.roll), len(IN.clubs_on_report()))

    def test_no_replacement_is_ever_named_from_the_report(self):
        for row in IN.depth_of_replacement():
            self.assertEqual(row["replacement_named"], "")
            self.assertEqual(row["replacement_source_url"], "")

    def test_every_unit_is_mapped(self):
        unmapped = [r for r in self.rows if r["unit"] == "Unmapped"]
        self.assertEqual(unmapped, [], [r["position"] for r in unmapped])

    def test_announced_starters_all_cite_a_page(self):
        rows = IN.announced_starters()
        self.assertTrue(rows)
        for r in rows:
            self.assertTrue(r["source_url"].startswith("https://www.nfl.com/news/"), r)
            self.assertEqual(r["evidence_kind"], "announced_starter")

    def test_roster_events_never_claim_a_start(self):
        for r in IN.roster_events():
            self.assertEqual(r["starter_announced"], "")

    def test_reserve_coverage_marks_absence_explicitly(self):
        rows = IN.reserve_coverage()
        self.assertEqual(len(rows), len(C.RESERVE_LIST_NOV_2026))
        for r in rows:
            self.assertIn(r["on_week10_injury_report"], ("yes", "no"))
            self.assertTrue(r["interpretation"])

    def test_inactive_rows_are_club_and_venue_tagged(self):
        rows = IN.week9_inactive_rows()
        self.assertEqual(len(rows), 160)
        for r in rows:
            self.assertTrue(r["club"])
            self.assertTrue(r["venue"])
            self.assertIn(r["emergency_third_qb"], ("yes", "no"))

    def test_venues_are_unique_per_game(self):
        venues = IN.venues()
        self.assertEqual(len({v["game_slug"] for v in venues}), 13)
        self.assertTrue(all(v["venue"] for v in venues))


class TestPointInTimeModel(unittest.TestCase):
    def setUp(self):
        self.pit, self.recon = M.point_in_time_standings()

    def test_thirty_two_clubs(self):
        self.assertEqual(len(self.pit), 32)

    def test_league_points_balance(self):
        self.assertEqual(sum(r["pf"] for r in self.pit),
                         sum(r["pa"] for r in self.pit))

    def test_wins_equal_losses(self):
        self.assertEqual(sum(r["w"] for r in self.pit),
                         sum(r["l"] for r in self.pit))

    def test_completed_games_through_week_nine_is_136(self):
        self.assertEqual(sum(r["games"] for r in self.pit) // 2, 136)

    def test_reconstruction_arithmetic(self):
        for r in self.recon:
            rw, rl, rt = (int(x) for x in r["rendered_record"].split("-"))
            sw, sl, st = (int(x) for x in r["reconstructed_record"].split("-"))
            self.assertEqual((rw - sw) + (rl - sl) + (rt - st),
                             int(r["week10_games_subtracted"]), r["club"])
            self.assertEqual(int(r["rendered_pf"]) - int(r["subtracted_pf"]),
                             int(r["reconstructed_pf"]), r["club"])

    def test_reconstruction_matches_the_official_pregame_page(self):
        ver = M.verification_against_pregame_page(self.pit)
        self.assertEqual(len(ver), 10)
        for v in ver:
            self.assertEqual(v["match"], "yes", v)

    def test_integrity_identities(self):
        results = {c["check"]: c["result"] for c in M.integrity_checks(self.pit)}
        self.assertEqual(results["league points for equals league points against"], "pass")
        self.assertEqual(results["wins equal losses"], "pass")
        self.assertEqual(results["team-games is even"], "pass")
        self.assertEqual(results["clubs in reconstructed table"], "pass")

    def test_finals_and_live_games_partition_the_slate(self):
        self.assertEqual(len(M.final_games()) + len(M.live_games()), len(C.WEEK10_SLATE))

    def test_no_live_game_enters_the_results_feed(self):
        live = {g["game_slug"] for g in M.live_games()}
        for g in M.final_games():
            self.assertNotIn(g["game_slug"], live)

    def test_luck_panel_is_ordered_and_bounded(self):
        lp = M.luck_panel(self.pit)
        self.assertGreater(lp["obs_win_pct_variance"], lp["null_win_pct_variance"])
        self.assertGreater(lp["luck_share"], 0.0)
        self.assertLess(lp["luck_share"], 1.0)
        self.assertAlmostEqual(lp["skill_variance"],
                               lp["obs_win_pct_variance"] - lp["null_win_pct_variance"],
                               places=9)

    def test_naive_rating_is_marked_unadjusted(self):
        for r in M.naive_ratings(self.pit):
            self.assertEqual(r["opponent_adjusted"], "no")
            self.assertEqual(r["blocking_gate"], "G3")


class TestCorrelations(unittest.TestCase):
    def setUp(self):
        self.pit, _ = M.point_in_time_standings()
        self.cors = X.correlations(self.pit)

    def test_every_correlation_publishes_n_and_an_interval(self):
        for c in self.cors:
            self.assertGreaterEqual(int(c["n"]), 3, c["id"])
            self.assertLessEqual(float(c["ci_low"]), float(c["estimate"]), c["id"])
            self.assertLessEqual(float(c["estimate"]), float(c["ci_high"]), c["id"])

    def test_both_axes_are_sourced(self):
        for c in self.cors:
            for key in ("x_source_url", "y_source_url"):
                self.assertTrue(c[key].startswith("https://www.nfl.com/"), c["id"])

    def test_exclusions_explain_themselves(self):
        excl = X.exclusions()
        self.assertEqual(len(excl), 5)
        for e in excl:
            self.assertTrue(e["why_not"])
            self.assertTrue(e["what_would_clear_it"])

    def test_no_price_based_correlation_was_estimated(self):
        joined = " ".join(c["x_axis"] + " " + c["y_axis"] for c in self.cors).lower()
        for banned in ("market", "closing line", "price", "odds"):
            self.assertNotIn(banned, joined)

    def test_designation_calibration_is_honest_about_its_sample(self):
        cal = X.designation_calibration()
        q = [r for r in cal if r["designation"] == "Questionable"][0]
        self.assertEqual(int(q["n_definite"]), 11)
        self.assertEqual(int(q["n_active"]), 10)
        self.assertTrue(q["selection_warning"])
        self.assertEqual(q["usable_as_feature"], "no")
        for r in cal:
            if r["designation"] in ("Out", "Doubtful"):
                self.assertEqual(r["play_rate"], "")


class TestGatesAndStrategies(unittest.TestCase):
    def test_every_gate_names_a_number(self):
        for g in G.gate_rows():
            self.assertTrue(g["threshold"], g["gate_id"])
            self.assertTrue(g["observed"], g["gate_id"])
            self.assertTrue(g["source_url"].startswith("https://"), g["gate_id"])
            self.assertIn(g["status"], ("pass", "fail"))

    def test_only_the_drift_alarm_passes(self):
        passing = [g["gate_id"] for g in G.gate_rows() if g["status"] == "pass"]
        self.assertEqual(passing, ["G12"])

    def test_no_strategy_is_qualified(self):
        for s in G.strategy_rows():
            self.assertEqual(s["qualified"], "no", s["strategy_id"])
            self.assertTrue(s["gates_uncleared"], s["strategy_id"])
            self.assertEqual(s["backtest_on_leaderboard"], "forbidden")

    def test_candidates_have_two_sided_rules(self):
        for s in G.strategy_rows():
            if s["family"] == "control":
                self.assertIn("never promoted", s["what_would_change_our_mind"].lower())
            else:
                self.assertIn("Promote", s["what_would_change_our_mind"], s["strategy_id"])
                self.assertIn("Demote", s["what_would_change_our_mind"], s["strategy_id"])

    def test_combo_families_have_no_open_window(self):
        for s in G.strategy_rows():
            if s["family"] in ("parlay", "same-game parlay", "prop combo"):
                self.assertTrue(s["evaluation_window"].lower().startswith("not opened"),
                                s["strategy_id"])
                self.assertIn("G10", s["required_gates"], s["strategy_id"])

    def test_controls_exist_and_are_never_promotable(self):
        controls = [s for s in G.strategy_rows() if s["family"] == "control"]
        self.assertEqual(len(controls), 2)

    def test_leaderboard_is_empty_in_every_division(self):
        rows = G.leaderboard_rows()
        self.assertEqual(len(rows), 5)
        for r in rows:
            self.assertEqual(r["ranked_strategies"], 0)
            self.assertEqual(r["qualified_strategies"], 0)

    def test_no_reward_is_monetary(self):
        for t in G.REWARD_TIERS:
            self.assertEqual(t["monetary"], "none")
            self.assertTrue(t["evidence"])


class TestRegisters(unittest.TestCase):
    def test_requirements_are_unique_and_complete(self):
        rows = A.requirements()
        ids = [r["requirement_id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        for r in rows:
            self.assertTrue(r["requirement"])
            self.assertTrue(r["what_is_published"])
            self.assertTrue(r["evidence_file"])
            self.assertIn(r["status"], {A.CLEARED, A.PARTIAL, A.BLOCKED, A.REJECTED,
                                        A.NEEDS_REVIEW})

    def test_blocked_rows_name_the_number_that_clears_them(self):
        for r in A.requirements():
            if r["status"] in (A.BLOCKED, A.PARTIAL):
                self.assertTrue(r["clearing_number"], r["requirement_id"])

    def test_rejected_approaches_are_recorded(self):
        rejected = [r for r in A.requirements() if r["status"] == A.REJECTED]
        self.assertEqual(len(rejected), 2)
        joined = " ".join(r["requirement"] for r in rejected).lower()
        self.assertIn("jersey number", joined)
        self.assertIn("roi", joined)

    def test_questions_have_a_discovery_path(self):
        for q in A.questions():
            self.assertTrue(q["decision_blocked"])
            self.assertTrue(q["what_we_have"])
            self.assertTrue(q["what_is_missing"])
            self.assertTrue(q["discovery_path"])

    def test_suggestions_are_not_self_executing(self):
        for s in A.suggestions():
            self.assertTrue(s["options"])
            self.assertTrue(s["cost_of_doing_nothing"])
            self.assertIn(s["priority"], ("high", "medium", "low"))

    def test_flags_are_unique_and_actionable(self):
        rows = FL.flags()
        ids = [f["flag_id"] for f in rows]
        self.assertEqual(len(ids), len(set(ids)))
        for f in rows:
            self.assertIn(f["severity"], ("high", "medium", "low"))
            self.assertTrue(f["what_would_fill_it"])

    def test_price_flag_covers_the_blank_market_cells(self):
        idx = FL.flag_index()
        self.assertIn("48217-F01", idx.get("originated_lines_schema.csv", []))


class TestBuiltArtifacts(unittest.TestCase):
    """The committed tables and pages, checked where they sit on disk."""

    def test_tables_and_pages_exist(self):
        self.assertTrue(os.path.isdir(DATA))
        self.assertTrue(os.path.isdir(DOCS))
        self.assertGreaterEqual(len(os.listdir(DATA)), 36)
        self.assertGreaterEqual(len([f for f in os.listdir(DOCS)
                                     if f.endswith(".html")]), 18)

    def test_build_is_deterministic(self):
        """A rebuild must reproduce byte-identical files, or the tables are not what the
        code computes."""
        before = self._digest()
        r = subprocess.run([sys.executable, "scripts/build_nfl_48217a55.py"],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertEqual(before, self._digest(), "rebuild changed the artefacts")

    def test_pages_have_no_input_controls(self):
        import re
        bad = re.compile(r"<(input|select|textarea|form)\b", re.I)
        for name in os.listdir(DOCS):
            if not name.endswith(".html"):
                continue
            with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
                self.assertIsNone(bad.search(fh.read()), name)

    def test_internal_links_resolve(self):
        import re
        for name in os.listdir(DOCS):
            if not name.endswith(".html"):
                continue
            with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
                text = fh.read()
            for href in re.findall(r'href="([^"#][^"]*)"', text):
                if href.startswith("http"):
                    continue
                target = os.path.join(DOCS, href.split("#")[0])
                self.assertTrue(os.path.exists(target), f"{name} -> {href}")

    def test_no_signed_or_non_official_external_host_is_linked(self):
        import re
        allowed = {"www.nfl.com", "operations.nfl.com", "static.www.nfl.com",
                   "www.chiefs.com", "github.com"}
        for name in os.listdir(DOCS):
            if not name.endswith(".html"):
                continue
            with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
                text = fh.read()
            for href in re.findall(r'href="(https?://[^"]+)"', text):
                from urllib.parse import urlparse
                self.assertTrue(href.startswith("https://"), href)
                self.assertIn(urlparse(href).hostname, allowed, href)
                self.assertNotIn("sk=", href)

    def _digest(self):
        import hashlib
        h = hashlib.sha256()
        for folder in (DATA, DOCS):
            for root, _dirs, files in os.walk(folder):
                for f in sorted(files):
                    path = os.path.join(root, f)
                    with open(path, "rb") as fh:
                        h.update(os.path.relpath(path, REPO).encode())
                        h.update(fh.read())
        return h.hexdigest()


class TestVerifier(unittest.TestCase):
    def test_pack_verifier_passes(self):
        r = subprocess.run([sys.executable, "scripts/check_nfl_48217a55.py"],
                           cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-2000:])
        self.assertIn("0 failure(s)", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
