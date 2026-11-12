"""Regression tests for the NFL origination, depth and skill-gate pack.

Loadable by the repository's stdlib runner (tools/run_tests.py) and by pytest.
"""
from __future__ import annotations

import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import build_nfl_3b81013c as builder  # noqa: E402
import check_nfl_3b81013c as checker  # noqa: E402

from nfl_3b81013c import (  # noqa: E402
    StrategyCandidate,
    american_to_implied_prob,
    check_gameday_active_limit,
    devig_multiplicative,
    devig_shin_power,
    evaluate_strategy_gates,
    evaluate_unit_deficiency,
    fair_prob_to_american,
    frechet_hoeffding_bounds,
    gaussian_copula_joint_prob,
    holm_bonferroni_adjust,
    originate_nfl_game_lines,
    paired_residual_correlation,
    rank_skill_leaderboard,
    same_line_devig_clv,
    DepthSlotStatus,
)

DATA = ROOT / "data" / "nfl_3b81013c"
DOCS = ROOT / "docs" / "nfl-3b81013c"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class PricingTests(unittest.TestCase):
    def test_american_conversion_matches_the_official_formula(self) -> None:
        self.assertAlmostEqual(american_to_implied_prob(-110), 110 / 210, places=12)
        self.assertAlmostEqual(american_to_implied_prob(150), 100 / 250, places=12)
        self.assertAlmostEqual(american_to_implied_prob(-200), 2 / 3, places=12)
        self.assertAlmostEqual(american_to_implied_prob(100), 0.5, places=12)

    def test_rejects_odds_inside_minus_100_to_100(self) -> None:
        for bad in (0, 50, -50, -99, 99):
            with self.assertRaises(ValueError):
                american_to_implied_prob(bad)
        for bad in (float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                american_to_implied_prob(bad)

    def test_even_money_is_plus_100_not_minus_110(self) -> None:
        self.assertEqual(fair_prob_to_american(0.5), 100)
        self.assertEqual(fair_prob_to_american(0.62), -163)
        self.assertNotEqual(fair_prob_to_american(0.5), -110)

    def test_fair_probability_rejects_out_of_range(self) -> None:
        for bad in (0.0, 1.0, -0.1, 1.1):
            with self.assertRaises(ValueError):
                fair_prob_to_american(bad)

    def test_multiplicative_devig_removes_the_booksum(self) -> None:
        fair = devig_multiplicative([-110, -110])
        self.assertAlmostEqual(sum(fair), 1.0, places=12)
        self.assertAlmostEqual(fair[0], 0.5, places=12)

    def test_power_devig_agrees_on_a_balanced_book_and_differs_on_a_lopsided_one(self) -> None:
        self.assertAlmostEqual(devig_shin_power([-110, -110])[0], 0.5, places=6)
        multi = devig_multiplicative([-150, 130])
        power = devig_shin_power([-150, 130])
        self.assertAlmostEqual(sum(power), 1.0, places=9)
        self.assertGreater(abs(power[0] - multi[0]), 1e-4)

    def test_clv_is_blank_when_the_line_moves(self) -> None:
        self.assertIsNone(same_line_devig_clv(0, -2.5, -3.5, [-110, -110], [-125, 105]))
        value = same_line_devig_clv(0, -3.0, -3.0, [-110, -110], [-125, 105])
        self.assertIsNotNone(value)
        self.assertGreater(value, 0.0)


class LineOriginationTests(unittest.TestCase):
    def test_neutral_site_removes_home_field_advantage(self) -> None:
        kwargs = dict(
            home_team="DET", away_team="NE",
            home_off_epa_per_play=0.02, home_def_epa_per_play=-0.01,
            away_off_epa_per_play=0.01, away_def_epa_per_play=0.0,
        )
        home = originate_nfl_game_lines(neutral_site=False, **kwargs)
        neutral = originate_nfl_game_lines(neutral_site=True, **kwargs)
        self.assertNotEqual(home.fair_home_spread, neutral.fair_home_spread)
        self.assertAlmostEqual(home.fair_total, neutral.fair_total, places=6)
        # a neutral site must favour the home side less: the spread becomes less negative
        self.assertGreater(neutral.fair_home_spread, home.fair_home_spread)

    def test_win_probabilities_are_complementary_and_prices_fair(self) -> None:
        line = originate_nfl_game_lines(
            "SF", "DAL", 0.05, -0.02, 0.01, 0.0, home_field_advantage_pts=1.75
        )
        self.assertAlmostEqual(line.home_win_prob + line.away_win_prob, 1.0, places=6)
        self.assertEqual(
            round(american_to_implied_prob(line.fair_home_ml), 2),
            round(line.home_win_prob, 2),
        )

    def test_register_lines_match_an_independent_recomputation(self) -> None:
        errors = checker.check_line_arithmetic(ROOT)
        self.assertEqual(errors, [])


class DepthTests(unittest.TestCase):
    def test_gameday_limit_drops_to_47_without_eight_linemen(self) -> None:
        ok, limit, _ = check_gameday_active_limit(48, 8)
        self.assertTrue(ok)
        self.assertEqual(limit, 48)
        ok, limit, _ = check_gameday_active_limit(48, 7)
        self.assertFalse(ok)
        self.assertEqual(limit, 47)

    def test_practice_squad_elevation_cap(self) -> None:
        self.assertTrue(check_gameday_active_limit(48, 8, 2)[0])
        self.assertFalse(check_gameday_active_limit(48, 8, 3)[0])

    def test_fourth_string_costs_more_than_second_string(self) -> None:
        def index(tier: int) -> float:
            return evaluate_unit_deficiency([
                DepthSlotStatus("SEA", "OFFENSE", "OL", "LT", "Starter", "Backup", tier, "DNP", "OUT")
            ]).structural_deficiency_index

        # A healthy first-string left tackle carries no replacement penalty, but a DNP starter
        # still carries the partial-degradation term shared by every DNP slot.
        self.assertLess(index(1), index(2))
        self.assertLess(index(2), index(3))
        self.assertLess(index(3), index(4))

    def test_cluster_multiplier_rises_with_simultaneous_absences(self) -> None:
        slots = [
            DepthSlotStatus("SF", "DEFENSE", "SECONDARY", slot, "Starter", "Backup", 2, "DNP", "OUT")
            for slot in ("CB1", "CB2", "SS")
        ]
        self.assertGreater(evaluate_unit_deficiency(slots).cluster_penalty_multiplier, 1.3)

    def test_register_severity_is_never_assigned_without_a_verified_string(self) -> None:
        for row in rows("injuries_and_depth.csv"):
            if row["verification_status"] == "unverified":
                # No numeric exposure may be asserted without a verified incoming string.
                self.assertEqual(row["structural_severity_index"], "", row["id"])
                self.assertEqual(row["replacement_string"], "", row["id"])

    def test_depth_arithmetic_recomputes(self) -> None:
        self.assertEqual(checker.check_depth_arithmetic(ROOT), [])


class CorrelationTests(unittest.TestCase):
    def test_frechet_bounds(self) -> None:
        self.assertEqual(frechet_hoeffding_bounds([0.5, 0.5]), (0.0, 0.5))
        self.assertEqual(frechet_hoeffding_bounds([0.9, 0.9]), (0.8, 0.9))
        with self.assertRaises(ValueError):
            frechet_hoeffding_bounds([1.5])

    def test_copula_is_monotone_in_rho_and_stays_inside_the_bounds(self) -> None:
        values = [gaussian_copula_joint_prob(0.5, 0.5, rho) for rho in (-0.9, -0.5, 0.0, 0.5, 0.9)]
        self.assertEqual(values, sorted(values))
        for value in values:
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 0.5)
        self.assertAlmostEqual(gaussian_copula_joint_prob(0.5, 0.5, 0.0), 0.25, places=12)

    def test_correlation_rejects_non_training_rows_and_survives_zeros(self) -> None:
        with self.assertRaises(ValueError):
            paired_residual_correlation("p", [0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.3, 0.4],
                                        ["a", "a", "b", "b"], ["train", "train", "test", "train"])
        estimate = paired_residual_correlation(
            "p", [0.0, 1.0, 2.0, 3.0, 0.0, 1.0], [0.0, 2.0, 4.0, 6.0, 0.0, 2.0],
            ["w1", "w1", "w2", "w2", "w3", "w3"], ["train"] * 6,
        )
        self.assertAlmostEqual(estimate.pearson_r, 1.0, places=6)

    def test_every_registered_correlation_stays_blank(self) -> None:
        for row in rows("correlations.csv"):
            self.assertEqual(row["pearson_r"], "", row["id"])
            self.assertEqual(row["verification_status"], "unverified", row["id"])
        self.assertEqual(checker.check_correlation_arithmetic(ROOT), [])


class ValidationGateTests(unittest.TestCase):
    def _candidate(self, **overrides) -> StrategyCandidate:
        base = dict(
            strategy_id="T-1", strategy_name="test", category="SINGLE",
            n_authorized_events=0, n_slate_clusters=0, rights_verified=False,
            pre_kickoff_timestamps_verified=False, walk_forward_clean=False,
            depth_chart_verified=False, holdout_brier_delta_vs_market=None,
            holdout_same_line_clv=None, holdout_roi_ci_lower=None,
            raw_p_value=None, adjusted_p_value=None, combo_correlation_verified=False,
        )
        base.update(overrides)
        return StrategyCandidate(**base)

    def test_ten_gates_are_evaluated(self) -> None:
        gates = evaluate_strategy_gates(self._candidate())
        self.assertEqual(len(gates), 10)
        self.assertEqual([g.gate_id for g in gates], [f"VG-{i:02d}" for i in range(1, 11)])

    def test_a_strategy_with_no_data_never_qualifies(self) -> None:
        ranked = rank_skill_leaderboard([self._candidate()])
        self.assertFalse(ranked[0]["qualified"])
        self.assertIsNone(ranked[0]["rank"])
        self.assertEqual(ranked[0]["reward_tier"], "QUARANTINED_UNVERIFIED_DATA")

    def test_a_parlay_needs_a_verified_correlation(self) -> None:
        gates = {
            g.gate_id: g for g in evaluate_strategy_gates(self._candidate(category="PARLAY"))
        }
        self.assertEqual(gates["VG-07"].status, "BLOCKED_NO_DATA")
        gates = {
            g.gate_id: g
            for g in evaluate_strategy_gates(self._candidate(category="SINGLE"))
        }
        self.assertEqual(gates["VG-07"].status, "PASS")

    def test_a_fully_evidenced_strategy_can_qualify(self) -> None:
        good = self._candidate(
            n_authorized_events=400, n_slate_clusters=30, rights_verified=True,
            pre_kickoff_timestamps_verified=True, walk_forward_clean=True,
            depth_chart_verified=True, holdout_brier_delta_vs_market=-0.01,
            holdout_same_line_clv=0.02, holdout_roi_ci_lower=0.03,
            raw_p_value=0.01, adjusted_p_value=0.02, combo_correlation_verified=True,
        )
        ranked = rank_skill_leaderboard([good])
        self.assertTrue(ranked[0]["qualified"])
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[0]["reward_tier"], "TIER_1_GOLD_RESEARCH_ALLOCATION")

    def test_holm_adjustment_is_monotone_and_bounded(self) -> None:
        adjusted = holm_bonferroni_adjust([0.01, 0.04, 0.03, 0.002])
        self.assertEqual(len(adjusted), 4)
        self.assertTrue(all(0.0 <= p <= 1.0 for p in adjusted))
        self.assertLess(adjusted[3], adjusted[0])
        with self.assertRaises(ValueError):
            holm_bonferroni_adjust([1.2])

    def test_register_expects_quarantine_for_every_strategy(self) -> None:
        self.assertEqual(checker.check_gates_and_leaderboard(ROOT), [])


class RegisterContractTests(unittest.TestCase):
    def test_every_register_row_cites_an_official_source_and_a_methodology(self) -> None:
        for name in sorted(p.name for p in DATA.glob("*.csv")):
            for row in rows(name):
                self.assertTrue(
                    any(checker._host(u) in checker.OFFICIAL_HOSTS
                        for u in row["official_source_url"].split() if u.strip()),
                    f"{name}:{row.get('id')} lacks an official NFL source",
                )
                self.assertTrue(row["methodology_reference_url"].strip(), f"{name}:{row.get('id')} lacks a methodology reference")
                self.assertIn(row["verification_status"], {"verified", "computed", "unverified"})

    def test_unverified_rows_never_carry_a_value(self) -> None:
        for name in sorted(p.name for p in DATA.glob("*.csv")):
            header = rows(name)[0].keys() if rows(name) else []
            if "value" not in header:
                continue
            for row in rows(name):
                if row["verification_status"] == "unverified":
                    self.assertEqual(row["value"], "", f"{name}:{row['id']}")

    def test_every_unverified_cell_is_blank_on_the_published_pages(self) -> None:
        errors, stats = checker.check_pages(ROOT)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(stats["rows"], 400)
        self.assertEqual(stats["pages"], 11)


class BuildIntegrityTests(unittest.TestCase):
    def test_published_pages_match_the_builder(self) -> None:
        expected = builder.generate_all()
        for name, content in expected.items():
            target = DOCS / name
            self.assertTrue(target.is_file(), name)
            self.assertEqual(target.read_text(encoding="utf-8"), content, name)

    def test_page_set_is_exactly_the_navigation(self) -> None:
        pages = {p.name for p in DOCS.glob("*.html")}
        self.assertEqual(pages, {name for name, _ in builder.NAV_ITEMS})
        self.assertTrue((DOCS / "styles.css").is_file())

    BASE_ROW = {
        "id": "X", "group": "g", "item": "i", "value": "v", "unit_or_scope": "u",
        "verification_status": "verified", "derivation_or_detail": "d",
        "official_source_label": "NFL.com Terms of Use (updated May 16, 2024)",
        "official_source_url": "https://www.nfl.com/legal/terms/",
        "methodology_reference_label": "NIST",
        "methodology_reference_url": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm",
    }

    def _validate(self, **overrides):
        row = dict(self.BASE_ROW)
        row.update(overrides)
        builder.validate_register("fixture.csv", [row], list(row.keys()))

    def test_builder_rejects_an_unverified_row_with_a_value(self) -> None:
        with self.assertRaises(builder.DataError):
            self._validate(verification_status="unverified", value="leaked")

    def test_builder_accepts_an_unverified_row_with_a_blank_value(self) -> None:
        self._validate(verification_status="unverified", value="")

    def test_builder_rejects_a_verified_row_with_a_blank_value(self) -> None:
        with self.assertRaises(builder.DataError):
            self._validate(value="")

    def test_builder_rejects_a_row_without_an_official_source(self) -> None:
        with self.assertRaises(builder.DataError):
            self._validate(official_source_url="https://example.com/page")

    def test_builder_rejects_an_off_allowlist_methodology_reference(self) -> None:
        with self.assertRaises(builder.DataError):
            self._validate(methodology_reference_url="https://example.com/method")

    def test_builder_rejects_an_unknown_status(self) -> None:
        with self.assertRaises(builder.DataError):
            self._validate(verification_status="probably_fine")

    def test_every_table_row_matches_its_header_width(self) -> None:
        """A row with the wrong number of cells silently shifts every later column."""
        for path in sorted(DOCS.glob("*.html")):
            parser = checker.RowParser()
            parser.feed(path.read_text(encoding="utf-8"))
            for index, row in enumerate(parser.completed_rows, 1):
                expected = parser.header_width.get(row["table"])
                self.assertIsNotNone(expected, f"{path.name} row {index}: table has no header")
                self.assertEqual(
                    row["cells"], expected,
                    f"{path.name} row {index}: {row['cells']} cells vs {expected} header cells",
                )

    def test_kpi_counts_match_the_registers(self) -> None:
        import re

        text = (DOCS / "index.html").read_text(encoding="utf-8")
        questions = rows("open_questions.csv")
        expected_open = sum(1 for q in questions if q["status"] == "open")
        match = re.search(r"Open questions</p><p class=\"kpi-value\">(\d+)<", text)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), expected_open)
        match = re.search(r"Unverified / blank</p><p class=\"kpi-value\">([\d,]+)<", text)
        self.assertIsNotNone(match)
        registered_unverified = sum(
            1
            for name in sorted(p.name for p in DATA.glob("*.csv"))
            for r in rows(name)
            if r["verification_status"] == "unverified"
        )
        self.assertEqual(int(match.group(1).replace(",", "")), registered_unverified)

    def test_no_wagering_recommendation_language(self) -> None:
        for path in DOCS.glob("*.html"):
            text = path.read_text(encoding="utf-8").lower()
            for phrase in checker.BANNED_PHRASES:
                self.assertNotIn(phrase, text, f"{path.name}: {phrase}")


class DeliverableTests(unittest.TestCase):
    def test_reports_exist_and_link_official_sources(self) -> None:
        for rel in (
            "research/NFL_3B81013C_EXECUTIVE_SUMMARY.md",
            "audit/NFL_3B81013C_REPO_AND_SOURCE_AUDIT.md",
        ):
            path = ROOT / rel
            self.assertTrue(path.is_file(), rel)
            text = path.read_text(encoding="utf-8")
            self.assertIn("https://www.nfl.com/", text)
            self.assertIn("https://operations.nfl.com/", text)
            self.assertGreater(len(text), 4000)

    def test_full_checks_pass_on_the_current_tree(self) -> None:
        errors, stats = checker.run_checks(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(stats["pages"], 11)
        self.assertGreater(stats["verified"], 100)
        self.assertGreater(stats["unverified"], 50)


if __name__ == "__main__":
    unittest.main()
