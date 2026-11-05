"""Tests for the luck-exclusion engine (src/own6/power.py).

Two layers:

1. Analytic identities and input validation, using only the standard library.
2. Independent cross-checks against SciPy (and statsmodels when available),
   installed from PyPI in the development virtualenv.  Those tests skip when the
   library is absent so the standard library CI runner still passes.

The SciPy comparison is the verification evidence for this module: the same
quantity computed twice by independent implementations.
"""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from own6 import power  # noqa: E402

try:  # optional numeric cross-check
    import numpy as _np
    from scipy import stats as _stats  # type: ignore
except Exception:  # pragma: no cover - exercised only without SciPy
    _stats = None

try:
    from statsmodels.stats.multitest import multipletests as _multipletests  # type: ignore
    from statsmodels.stats.proportion import proportion_confint as _proportion_confint  # type: ignore
except Exception:  # pragma: no cover
    _multipletests = None
    _proportion_confint = None


class TestPrices(unittest.TestCase):
    def test_american_to_decimal_known_values(self):
        self.assertAlmostEqual(power.decimal_from_american(-110), 1.909090909, places=8)
        self.assertAlmostEqual(power.decimal_from_american(150), 2.5, places=12)
        self.assertAlmostEqual(power.decimal_from_american(-300), 1.333333333, places=8)
        self.assertAlmostEqual(power.decimal_from_american(100), 2.0, places=12)
        self.assertAlmostEqual(power.decimal_from_american(-100), 2.0, places=12)

    def test_roundtrip(self):
        for moneyline in (-1000, -250, -110, 100, 145, 900):
            decimal_odds = power.decimal_from_american(moneyline)
            self.assertAlmostEqual(power.american_from_decimal(decimal_odds), moneyline, places=6)

    def test_break_even_is_reciprocal(self):
        for moneyline in (-200, -110, 130):
            self.assertAlmostEqual(
                power.break_even_probability(power.decimal_from_american(moneyline)),
                power.implied_probability(moneyline),
                places=12,
            )

    def test_invalid_prices(self):
        for bad in (0, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                power.decimal_from_american(bad)
        with self.assertRaises(ValueError):
            power.break_even_probability(1.0)
        with self.assertRaises(TypeError):
            power.decimal_from_american("+150")  # type: ignore[arg-type]


class TestMoments(unittest.TestCase):
    def test_break_even_has_zero_mean(self):
        for moneyline in (-300, -110, 250):
            d = power.decimal_from_american(moneyline)
            mean, variance = power.bet_moments(power.break_even_probability(d), d)
            self.assertAlmostEqual(mean, 0.0, places=12)
            self.assertGreater(variance, 0.0)

    def test_moments_match_definition(self):
        p, d = 0.55, 1.909090909
        mean, variance = power.bet_moments(p, d)
        outcomes = [d - 1.0, -1.0]
        weights = [p, 1.0 - p]
        expected_mean = sum(w * x for w, x in zip(weights, outcomes))
        expected_var = sum(w * x * x for w, x in zip(weights, outcomes)) - expected_mean**2
        self.assertAlmostEqual(mean, expected_mean, places=12)
        self.assertAlmostEqual(variance, expected_var, places=12)

    def test_probability_bounds(self):
        for bad in (0.0, 1.0, -0.1, 1.2):
            with self.assertRaises(ValueError):
                power.bet_moments(bad, 1.9)


class TestSampleSize(unittest.TestCase):
    def test_required_bets_inverts_minimum_detectable_roi(self):
        variance = 0.909090909
        for n in (100, 500, 2000):
            mdr = power.minimum_detectable_roi(n, variance, alpha=0.05, power=0.8)
            required = power.required_bets(mdr, variance, alpha=0.05, power=0.8)
            self.assertAlmostEqual(required, n, delta=1)

    def test_doubling_edge_quarters_sample(self):
        variance = 0.909090909
        n_small = power.required_bets(0.02, variance)
        n_large = power.required_bets(0.04, variance)
        self.assertAlmostEqual(n_small / n_large, 4.0, delta=0.05)

    def test_required_bets_for_roi_price_sensitivity(self):
        # A longer price carries more variance, so the same ROI needs more bets.
        self.assertGreater(
            power.required_bets_for_roi(0.03, power.decimal_from_american(400)),
            power.required_bets_for_roi(0.03, power.decimal_from_american(-300)),
        )

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            power.required_bets(0.0, 1.0)
        with self.assertRaises(ValueError):
            power.required_bets(0.03, 0.0)
        with self.assertRaises(ValueError):
            power.required_bets(0.03, 1.0, sides=3)
        with self.assertRaises(ValueError):
            power.required_bets_for_roi(-1.0, 1.909)

    @unittest.skipIf(_stats is None, "SciPy not installed")
    def test_matches_scipy_normal_quantiles(self):
        for alpha in (0.001, 0.01, 0.05, 0.10):
            self.assertAlmostEqual(
                power._z(alpha, 1), float(_stats.norm.ppf(1 - alpha)), places=10
            )
            self.assertAlmostEqual(
                power._z(alpha, 2), float(_stats.norm.ppf(1 - alpha / 2)), places=10
            )

    @unittest.skipIf(_stats is None, "SciPy not installed")
    def test_matches_scipy_sample_size_formula(self):
        from scipy.stats import norm

        for roi, moneyline in ((0.03, -110), (0.05, 130), (0.02, -300)):
            d = power.decimal_from_american(moneyline)
            p = (1 + roi) / d
            mean, variance = power.bet_moments(p, d)
            expected = ((norm.ppf(0.95) + norm.ppf(0.80)) ** 2) * variance / roi**2
            self.assertAlmostEqual(
                power.required_bets_for_roi(roi, d), math.ceil(expected), delta=1
            )


class TestMultipleTesting(unittest.TestCase):
    def test_bonferroni(self):
        self.assertAlmostEqual(power.bonferroni_alpha(0.05, 200), 0.00025, places=12)
        with self.assertRaises(ValueError):
            power.bonferroni_alpha(0.05, 0)

    def test_bonferroni_increases_requirement(self):
        base = 6000
        self.assertGreater(power.bonferroni_required_bets(base, 50), base)
        self.assertLess(
            power.bonferroni_required_bets(base, 50),
            power.bonferroni_required_bets(base, 500),
        )

    def test_expected_false_positives(self):
        self.assertAlmostEqual(power.expected_false_positives(200, 0.05), 10.0, places=12)

    def test_bh_known_example(self):
        p_values = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
        q_values = power.bh_qvalues(p_values)
        self.assertEqual(len(q_values), len(p_values))
        self.assertTrue(power.require_monotone([q for _, q in sorted(zip(p_values, q_values))]))
        self.assertTrue(all(q >= p for p, q in zip(p_values, q_values)))
        self.assertTrue(all(q <= 1.0 for q in q_values))
        # For this vector the largest rank satisfying p_(j) <= (j/m) alpha is
        # j = 2 (0.008 <= 0.010), so exactly the first two hypotheses are
        # rejected by the step-up rule.
        self.assertEqual([q <= 0.05 for q in q_values], [True, True] + [False] * 8)
        self.assertAlmostEqual(q_values[0], 0.01, places=10)
        self.assertAlmostEqual(q_values[1], 0.04, places=10)

    def test_bh_empty_and_validation(self):
        self.assertEqual(power.bh_qvalues([]), [])
        with self.assertRaises(ValueError):
            power.bh_qvalues([0.0])
        with self.assertRaises(ValueError):
            power.bh_qvalues([1.0])

    @unittest.skipIf(_multipletests is None, "statsmodels not installed")
    def test_bh_matches_statsmodels(self):
        p_values = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
        _, expected, _, _ = _multipletests(p_values, alpha=0.05, method="fdr_bh")
        for got, want in zip(power.bh_qvalues(p_values), expected):
            self.assertAlmostEqual(got, float(want), places=10)


class TestBinomialAndWilson(unittest.TestCase):
    def test_binomial_sf_small_case_by_hand(self):
        # P(X>=8) for X~Bin(10,0.5) = (45+10+1)/1024
        self.assertAlmostEqual(power.binomial_sf(8, 10, 0.5), 56 / 1024, places=12)
        self.assertAlmostEqual(power.binomial_sf(0, 10, 0.5), 1.0, places=12)
        self.assertEqual(power.binomial_sf(11, 10, 0.5), 0.0)

    def test_large_n_does_not_overflow(self):
        value = power.binomial_sf(1120, 2000, 1 / 1.909090909)
        self.assertTrue(0.0 < value < 1.0)
        self.assertLess(value, 0.01)

    def test_wilson_known_value(self):
        low, high = power.wilson_interval(55, 100)
        self.assertAlmostEqual(low, 0.452446, places=5)
        self.assertAlmostEqual(high, 0.643855, places=5)

    def test_verdict_requires_interval_separation(self):
        separated = power.luck_verdict(560, 1000, 1.909090909)
        self.assertTrue(separated["exceeds_luck"])
        self.assertEqual(separated["verdict"], "exceeds_luck")
        not_separated = power.luck_verdict(540, 1000, 1.909090909)
        self.assertFalse(not_separated["exceeds_luck"])
        self.assertEqual(not_separated["verdict"], "explainable_by_luck")

    @unittest.skipIf(_stats is None, "SciPy not installed")
    def test_binomial_p_value_matches_scipy(self):
        for wins, bets, price in ((55, 100, -110), (110, 200, -110), (560, 1000, -110), (30, 50, -300)):
            p0 = power.break_even_probability(power.decimal_from_american(price))
            expected = _stats.binomtest(wins, bets, p0, alternative="greater").pvalue
            self.assertAlmostEqual(
                power.binomial_p_value(wins, bets, p0, sides=1), float(expected), places=10
            )
            expected_two = _stats.binomtest(wins, bets, p0, alternative="two-sided").pvalue
            self.assertAlmostEqual(
                power.binomial_p_value(wins, bets, p0, sides=2), float(expected_two), places=10
            )

    @unittest.skipIf(_proportion_confint is None, "statsmodels not installed")
    def test_wilson_matches_statsmodels(self):
        for wins, n in ((55, 100), (560, 1000), (3, 20)):
            low, high = power.wilson_interval(wins, n)
            want_low, want_high = _proportion_confint(wins, n, alpha=0.05, method="wilson")
            self.assertAlmostEqual(low, float(want_low), places=10)
            self.assertAlmostEqual(high, float(want_high), places=10)


class TestCorrelationPower(unittest.TestCase):
    def test_monotone_in_correlation(self):
        values = [power.fisher_required_pairs(r) for r in (0.1, 0.2, 0.3, 0.5)]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_matches_closed_form(self):
        from statistics import NormalDist

        z = NormalDist().inv_cdf(0.975) + NormalDist().inv_cdf(0.80)
        self.assertEqual(
            power.fisher_required_pairs(0.3, sides=2), math.ceil((z / math.atanh(0.3)) ** 2 + 3)
        )

    def test_invalid(self):
        with self.assertRaises(ValueError):
            power.fisher_required_pairs(0.0)
        with self.assertRaises(ValueError):
            power.fisher_required_pairs(1.0)

    @unittest.skipIf(_stats is None, "SciPy not installed")
    def test_matches_scipy_fisher_z(self):
        # Expected n from SciPy's own quantiles, computed independently here.
        r = 0.25
        z_alpha = float(_stats.norm.ppf(0.975))
        z_beta = float(_stats.norm.ppf(0.80))
        expected = math.ceil(((z_alpha + z_beta) / math.atanh(r)) ** 2 + 3)
        self.assertEqual(power.fisher_required_pairs(r), expected)


class TestCommittedData(unittest.TestCase):
    """The published tables must be regenerable and internally consistent."""

    def test_data_is_up_to_date(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "luck_analysis.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_required_bets_table_shape(self):
        path = ROOT / "data" / "luck" / "required_bets.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        self.assertEqual(len(rows), 25)  # 5 price levels x 5 ROI levels
        for row in rows:
            self.assertGreater(int(row["required_bets_alpha_0.05_power_0.80"]), 0)
            self.assertGreater(
                int(row["required_bets_bonferroni_200_candidates"]),
                int(row["required_bets_alpha_0.05_power_0.80"]),
            )

    def test_meta_states_the_boundary(self):
        meta = json.loads((ROOT / "data" / "luck" / "meta.json").read_text(encoding="utf-8"))
        self.assertIn("not NBA observations", meta["statement"])
        self.assertFalse(any(source["read_this_session"] for source in meta["method_sources"]))

    def test_verdicts_have_no_fabricated_record(self):
        rows = list(csv.DictReader((ROOT / "data" / "luck" / "luck_verdicts.csv").open(encoding="utf-8")))
        for row in rows:
            self.assertIn("illustrative arithmetic only", row["interpretation"])


if __name__ == "__main__":
    unittest.main()
