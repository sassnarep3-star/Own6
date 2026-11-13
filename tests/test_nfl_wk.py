"""Tests for the NFL Week pack. Pure stdlib so they run without pytest.

    python3 -m unittest tests.test_nfl_wk -v
"""

from __future__ import annotations

import csv
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl_wk import depth, gates, model  # noqa: E402

DATA = ROOT / "data" / "nfl_wk"


def rows(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestDistributionMath(unittest.TestCase):
    def test_norm_cdf_known_values(self):
        self.assertAlmostEqual(model.norm_cdf(0.0), 0.5, places=12)
        self.assertAlmostEqual(model.norm_cdf(1.96), 0.975002, places=5)
        self.assertAlmostEqual(model.norm_cdf(-1.96), 0.024998, places=5)

    def test_norm_ppf_inverts_cdf(self):
        for p in (0.01, 0.25, 0.5, 0.75, 0.99):
            self.assertAlmostEqual(model.norm_cdf(model.norm_ppf(p)), p, places=6)

    def test_win_prob_half(self):
        self.assertAlmostEqual(model.win_prob_from_margin(0.0, 6.0), 0.5, places=12)

    def test_win_prob_monotone(self):
        ps = [model.win_prob_from_margin(m, 6.0) for m in (-14, -7, 0, 7, 14)]
        self.assertEqual(ps, sorted(ps))

    def test_american_round_trip(self):
        for p in (0.25, 0.4, 0.5, 0.62, 0.8):
            a = model.american_from_prob(p)
            self.assertAlmostEqual(model.prob_from_american(a), p, places=2)

    def test_devig_balances(self):
        h, a, s = model.devig_multiplicative(-110, -110)
        self.assertAlmostEqual(h, 0.5, places=9)
        self.assertAlmostEqual(a, 0.5, places=9)
        self.assertAlmostEqual(s, 1.047619, places=5)

    def test_devig_asymmetric_still_sums_to_one(self):
        h, a, s = model.devig_multiplicative(-150, 130)
        self.assertAlmostEqual(h + a, 1.0, places=12)
        self.assertGreater(s, 1.0)

    def test_pearson_perfect(self):
        self.assertAlmostEqual(model.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0, places=12)
        self.assertAlmostEqual(model.pearson([1, 2, 3, 4], [8, 6, 4, 2]), -1.0, places=12)

    def test_pearson_undefined_cases(self):
        self.assertIsNone(model.pearson([1, 2], [3, 4]))       # n < 3
        self.assertIsNone(model.pearson([1, 1, 1], [1, 2, 3]))  # zero variance

    def test_fisher_ci_contains_point_estimate(self):
        lo, hi = model.fisher_ci(0.4, 50)
        self.assertLess(lo, 0.4)
        self.assertGreater(hi, 0.4)
        self.assertLess(hi - lo, 1.0)

    def test_fisher_ci_undefined_small_n(self):
        self.assertIsNone(model.fisher_ci(0.4, 3))

    def test_brier_bounds(self):
        self.assertEqual(model.brier(1.0, 1), 0.0)
        self.assertEqual(model.brier(0.0, 1), 1.0)

    def test_skill_score_zero_for_identical(self):
        self.assertAlmostEqual(model.brier_skill_score(0.2, 0.2), 0.0, places=12)

    def test_luck_test_refuses_to_invent(self):
        self.assertIsNone(model.prob_of_positive_over_n(0.55, 200))


class TestDepth(unittest.TestCase):
    def test_default_weights(self):
        d, groups = depth.depth_index("SEA", "Sam Darnold")
        self.assertEqual(d, 1)
        self.assertIn("QB", groups)

    def test_backup_string(self):
        d, _ = depth.depth_index("SEA", "Drew Lock")
        self.assertEqual(d, 2)
        d3, _ = depth.depth_index("SEA", "Jalen Milroe")
        self.assertEqual(d3, 3)

    def test_best_slot_wins_across_groups(self):
        # Ben Brown is 1st-string LG and 2nd-string C on the Patriots chart.
        d, groups = depth.depth_index("NE", "Ben Brown")
        self.assertEqual(d, 1)
        self.assertIn("LG", groups)
        self.assertIn("C", groups)

    def test_unknown_player_has_no_string(self):
        d, groups = depth.depth_index("SEA", "Nobody Atall")
        self.assertIsNone(d)
        self.assertEqual(groups, [])

    def test_unread_club_returns_none(self):
        # Houston's chart is image-only, so it is deliberately not in the registry.
        self.assertNotIn("HOU", depth.CHART_SOURCES)
        d, groups = depth.depth_index("HOU", "C.J. Stroud")
        self.assertIsNone(d)
        self.assertEqual(groups, [])

    def test_charted_club_does_resolve(self):
        d, groups = depth.depth_index("KC", "Patrick Mahomes")
        self.assertEqual(d, 1)
        self.assertEqual(groups, ["QB"])

    def test_alias_resolution(self):
        self.assertEqual(depth.depth_index("BAL", "Matthew Hibner")[0],
                         depth.depth_index("BAL", "Matt Hibner")[0])
        self.assertEqual(depth.depth_index("BAL", "Olaivavega Ioane")[0], 1)

    def test_unit_classification(self):
        self.assertEqual(depth.unit_of("QB"), "offense")
        self.assertEqual(depth.unit_of("CB"), "defense")
        self.assertEqual(depth.unit_of("LS"), "special_teams")

    def test_availability_labels(self):
        self.assertEqual(depth.availability("Did Not Participate In Practice", "Out"), 0.0)
        self.assertEqual(depth.availability("Limited Participation in Practice", "Questionable"), 0.5)
        self.assertIsNone(depth.availability("", ""))

    def test_every_chart_has_a_source_url(self):
        for team, chart in depth.CHART_SOURCES.items():
            self.assertTrue(chart["url"].startswith("https://"), team)
            self.assertTrue(chart["source_id"].startswith("W11-S"), team)

    def test_chart_strings_are_contiguous(self):
        # Within a position group the list must be ordered 1st, 2nd, 3rd …, never skipping.
        for team, chart in depth.CHART_SOURCES.items():
            for group, names in chart["groups"].items():
                self.assertGreaterEqual(len(names), 1, f"{team}/{group}")


class TestGatesFailClosed(unittest.TestCase):
    def test_only_preregistration_passes(self):
        passed = [g["gate_id"] for g in gates.evaluate_all() if g["status"] == "PASS"]
        self.assertEqual(passed, ["VG-12"])

    def test_unknown_artefact_blocks(self):
        status, _ = gates.gate_result("no_such_artefact")
        self.assertEqual(status, "BLOCKED")

    def test_absent_artefact_blocks(self):
        status, _ = gates.gate_result("gate_price_archive")
        self.assertEqual(status, "BLOCKED")

    def test_no_strategy_is_eligible(self):
        for s in gates.STRATEGIES:
            elig, tier, units = gates.strategy_eligibility([])
            self.assertEqual(elig, "QUARANTINED")
            self.assertEqual(tier, "Tier 0")
            self.assertEqual(units, 0)

    def test_full_gate_set_is_eligible(self):
        all_gates = [g[0] for g in gates.GATES]
        elig, tier, units = gates.strategy_eligibility(all_gates)
        self.assertEqual((elig, tier, units), ("ELIGIBLE", "Tier 4", 10))

    def test_tier_one_requires_preregistration(self):
        elig, tier, _ = gates.strategy_eligibility(["VG-01", "VG-02"])
        self.assertEqual(elig, "QUARANTINED")
        elig, tier, _ = gates.strategy_eligibility(["VG-01", "VG-02", "VG-12"])
        self.assertEqual((elig, tier), ("QUARANTINED", "Tier 1"))

    def test_every_strategy_covers_a_family(self):
        fams = {s["family"] for s in gates.STRATEGIES}
        self.assertIn("Single bet", fams)
        self.assertIn("Parlay", fams)
        self.assertIn("Player prop combination", fams)

    def test_rewards_are_not_monetary(self):
        self.assertFalse(gates.REWARD_POLICY["monetary"])


class TestVerifiedInputs(unittest.TestCase):
    def test_standings_identity(self):
        r = rows("standings_2026_w11.csv")
        self.assertEqual(len(r), 32)
        s = lambda k: sum(int(x[k]) for x in r)
        self.assertEqual(s("w"), s("l"))
        self.assertEqual(s("pf"), s("pa"))
        self.assertEqual(s("t"), 2)
        self.assertEqual(s("home_w"), s("road_l"))

    def test_injury_rows_all_source_linked(self):
        r = rows("injuries_week10.csv")
        self.assertGreater(len(r), 300)
        for x in r:
            self.assertEqual(x["source_url"], "https://www.nfl.com/injuries/", x["player"])

    def test_every_slate_game_has_both_teams_and_time(self):
        for g in rows("slate.csv"):
            self.assertTrue(g["away_team"])
            self.assertTrue(g["home_team"])
            self.assertRegex(g["kickoff_et"], r"^\d{2}:\d{2}$")

    def test_week10_has_14_games_week11_has_13(self):
        r = rows("slate.csv")
        self.assertEqual(sum(1 for x in r if x["week"] == "10"), 14)
        self.assertEqual(sum(1 for x in r if x["week"] == "11"), 13)

    def test_sources_all_https_and_dated(self):
        for s in rows("sources.csv"):
            self.assertTrue(s["url"].startswith("https://"))
            self.assertRegex(s["read_on"], r"^\d{4}-\d{2}-\d{2}$")

    def test_no_market_value_anywhere(self):
        for r in rows("own_lines.csv"):
            for c in ("market_spread", "market_total", "market_ml_home", "market_ml_away", "edge_vs_market"):
                self.assertEqual(r[c], "", f"{r['game_id']} {c}")

    def test_no_correlation_coefficient(self):
        for r in rows("correlations.csv"):
            self.assertEqual(r["corr_value"], "")
            self.assertTrue(r["pre_registered_sign"])

    def test_flags_have_severity_and_source(self):
        for f in rows("flagged.csv"):
            self.assertIn(f["severity"], ("high", "medium", "low"))
            self.assertTrue(f["source_url"].startswith("https://"))

    def test_decision_questions_have_discovery_steps(self):
        for q in rows("decision_qa.csv"):
            self.assertTrue(q["discovery_step"])
            self.assertTrue(q["what_we_have"])
            self.assertTrue(q["what_we_lack"])

    def test_suggestions_have_risk(self):
        for s in rows("suggestions.csv"):
            self.assertTrue(s["risk_if_adopted"])
            self.assertIn(s["review_status"], ("implemented", "awaiting_decision", "rejected"))


class TestOwnLineComputation(unittest.TestCase):
    def test_fair_moneylines_are_vig_free(self):
        for r in rows("own_lines.csv"):
            ph = model.prob_from_american(int(r["fair_ml_home"]))
            pa = model.prob_from_american(int(r["fair_ml_away"]))
            self.assertAlmostEqual(ph + pa, 1.0, places=2)

    def test_probabilities_in_range(self):
        for r in rows("own_lines.csv"):
            p = float(r["own_win_prob_home"])
            self.assertGreater(p, 0.0)
            self.assertLess(p, 1.0)

    def test_total_is_plausible(self):
        for r in rows("own_lines.csv"):
            t = float(r["own_total"])
            self.assertGreater(t, 20.0)
            self.assertLess(t, 80.0)

    def test_spread_sign_matches_probability(self):
        for r in rows("own_lines.csv"):
            sp = float(r["own_spread_home"])
            p = float(r["own_win_prob_home"])
            if sp > 0:
                self.assertGreater(p, 0.5)
            elif sp < 0:
                self.assertLess(p, 0.5)


class TestDepthTiers(unittest.TestCase):
    """Co-starters must not be forced into a false 1st/2nd ordering."""

    def test_plain_list_is_one_name_per_tier(self):
        self.assertEqual(depth._tiers(["A", "B", "C"]), [["A"], ["B"], ["C"]])

    def test_nested_tier_puts_both_players_first(self):
        self.assertEqual(depth._tiers([["A", "B"], "C"]), [["A", "B"], ["C"]])

    def test_co_starter_gets_string_one(self):
        # Pittsburgh lists Freiermuth and Washington as co-starting tight ends.
        d1, g1 = depth.depth_index("PIT", "Pat Freiermuth")
        d2, g2 = depth.depth_index("PIT", "Darnell Washington")
        self.assertEqual((d1, g1), (1, ["TE"]))
        self.assertEqual((d2, g2), (1, ["TE"]))

    def test_third_man_behind_co_starters_is_string_two(self):
        d, g = depth.depth_index("PIT", "Robert Tonyan")
        self.assertEqual(d, 2)

    def test_arizona_co_listed_outside_linebackers(self):
        self.assertEqual(depth.depth_index("AZ", "Zaven Collins")[0], 1)
        self.assertEqual(depth.depth_index("AZ", "Baron Browning")[0], 1)

    def test_empty_group_is_empty(self):
        self.assertEqual(depth._tiers([]), [])
        self.assertEqual(depth._tiers(None), [])

    def test_unknown_player_has_no_string(self):
        d, g = depth.depth_index("KC", "Nobody At All")
        self.assertIsNone(d)
        self.assertEqual(g, [])


class TestCascadeSlots(unittest.TestCase):
    """The 3rd-string case only exists when the two men in front are both unavailable."""

    def _row(self, team, group, string, player, status):
        return {"team": team, "club_chart_groups": group, "club_chart_depth_string": str(string),
                "player": player, "game_status": status, "position": "X", "chart_status": "listed"}

    def test_single_injury_is_not_a_cascade(self):
        rows = [self._row("AAA", "RB", 1, "Starter", "Out"),
                self._row("AAA", "RB", 2, "Backup", ""),
                self._row("AAA", "RB", 3, "Third", "")]
        self.assertEqual(depth.cascade_slots(rows), [])

    def test_two_men_down_is_a_cascade_with_next_man(self):
        rows = [self._row("AAA", "RB", 1, "Starter", "Out"),
                self._row("AAA", "RB", 2, "Backup", "Questionable"),
                self._row("AAA", "RB", 3, "Third", "")]
        out = depth.cascade_slots(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["slot_1_player"], "Starter")
        self.assertEqual(out[0]["slot_2_player"], "Backup")
        self.assertEqual(out[0]["next_listed_player"], "Third")
        self.assertEqual(out[0]["next_listed_slot"], "3")

    def test_two_available_players_plus_one_out_is_not_a_cascade(self):
        rows = [self._row("AAA", "RB", 1, "Starter", ""),
                self._row("AAA", "RB", 2, "Backup", ""),
                self._row("AAA", "RB", 3, "Third", "Out")]
        self.assertEqual(depth.cascade_slots(rows), [])

    def test_thin_chart_reports_no_identifiable_replacement(self):
        rows = [self._row("AAA", "LG", 1, "Starter", "Out"),
                self._row("AAA", "LG", 2, "Backup", "Questionable")]
        out = depth.cascade_slots(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["next_listed_player"], "")
        self.assertIn("not identifiable", out[0]["note"])

    def test_unlisted_rows_are_ignored(self):
        rows = [{"team": "AAA", "club_chart_groups": "RB", "club_chart_depth_string": "",
                 "player": "P", "game_status": "Out", "position": "RB",
                 "chart_status": "not_listed_on_club_chart"}]
        self.assertEqual(depth.cascade_slots(rows), [])

    def test_published_cascades_all_belong_to_a_charted_club(self):
        for c in rows("depth_cascade.csv"):
            self.assertIn(c["team"], depth.CHART_SOURCES)

    def test_published_cascades_have_both_top_slots_unavailable(self):
        for c in rows("depth_cascade.csv"):
            self.assertIn(c["slot_1_status"], ("Out", "Questionable"))
            self.assertIn(c["slot_2_status"], ("Out", "Questionable"))


class TestCountsAreDerived(unittest.TestCase):
    """Prose counts must equal the data they describe, not a hand-typed number."""

    def test_originated_lines_exclude_the_finished_game(self):
        final = [r for r in rows("slate.csv") if r.get("played_status") == "final"]
        self.assertEqual(len(final), 1, "expected exactly one finished Week 10 game")
        for r in rows("own_lines.csv"):
            self.assertNotEqual(r["game_id"], final[0]["game_id"])

    def test_own_lines_cover_every_unplayed_week10_game(self):
        slate = [r for r in rows("slate.csv")
                 if r["week"] == "10" and r.get("played_status") != "final"]
        self.assertEqual({r["game_id"] for r in rows("own_lines.csv")},
                         {r["game_id"] for r in slate})

    def test_finished_game_has_a_score_and_unplayed_games_do_not(self):
        for r in rows("slate.csv"):
            if r.get("played_status") == "final":
                self.assertRegex(r["final_score"], r"\d+")
            else:
                self.assertEqual(r["final_score"], "")

    def test_every_slate_row_states_whether_it_was_played(self):
        for r in rows("slate.csv"):
            self.assertIn(r["played_status"], ("final", "not_played"))

    def test_depth_cascade_csv_matches_the_function(self):
        self.assertEqual(len(rows("depth_cascade.csv")),
                         len(depth.cascade_slots(rows("depth_deficiency.csv"))))


if __name__ == "__main__":
    unittest.main(verbosity=2)
