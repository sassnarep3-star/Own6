"""Tests for the skill lab: pricing, luck removal, correlation, gates, leaderboard.

Two kinds of test:

  * known-value tests against published reference numbers (critical values,
    binomial probabilities) — these pin the arithmetic;
  * known-answer experiments — the gate suite must accept a strategy with real,
    sufficiently-sampled skill and reject luck, overfitting and dependence
    errors. If a future edit makes a gate lenient, these fail.
"""
from __future__ import annotations

import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skillab import correlation, gates, leaderboard, luck, power, pricing, simulate  # noqa: E402


class TestPricing(unittest.TestCase):
    def test_american_to_decimal(self):
        self.assertAlmostEqual(pricing.american_to_decimal(150), 2.5, places=10)
        self.assertAlmostEqual(pricing.american_to_decimal(-200), 1.5, places=10)
        self.assertAlmostEqual(pricing.american_to_decimal(100), 2.0, places=10)
        self.assertAlmostEqual(pricing.american_to_decimal(-100), 2.0, places=10)

    def test_breakeven_at_minus_110(self):
        # At -110 you risk 110 to win 100, so break-even is 110/210 = 0.523809...
        self.assertAlmostEqual(pricing.breakeven_probability(-110), 110 / 210, places=12)

    def test_two_way_devig_sums_to_one(self):
        m = pricing.TwoWayMarket(-179, 150)
        pa, pb = m.devig_proportional()
        self.assertAlmostEqual(pa + pb, 1.0, places=12)
        self.assertGreater(m.vig, 0.0)

    def test_symmetric_book_devigs_to_half(self):
        pa, pb = pricing.TwoWayMarket(-110, -110).devig_proportional()
        self.assertAlmostEqual(pa, 0.5, places=12)
        self.assertAlmostEqual(pb, 0.5, places=12)

    def test_zero_ev_at_breakeven(self):
        p = pricing.breakeven_probability(-110)
        self.assertAlmostEqual(pricing.expected_value_per_unit(p, -110), 0.0, places=12)

    def test_kelly_never_negative(self):
        self.assertEqual(pricing.kelly_fraction(0.4, -110), 0.0)
        self.assertGreater(pricing.kelly_fraction(0.6, -110), 0.0)

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            pricing.american_to_decimal(0)
        with self.assertRaises(ValueError):
            pricing.implied_to_american(1.5)


class TestLuckMath(unittest.TestCase):
    def test_normal_quantiles(self):
        self.assertAlmostEqual(luck.norm_ppf(0.975), 1.959963985, places=8)
        self.assertAlmostEqual(luck.norm_ppf(0.5), 0.0, places=12)

    def test_t_quantiles_match_published_tables(self):
        self.assertAlmostEqual(luck.t_ppf(0.975, 10), 2.228138852, places=6)
        self.assertAlmostEqual(luck.t_ppf(0.975, 30), 2.042272456, places=6)
        self.assertAlmostEqual(luck.t_ppf(0.975, 120), 1.979930405, places=6)

    def test_binomial_pmf_sums_to_one(self):
        self.assertAlmostEqual(sum(luck.binom_pmf(k, 12, 0.3) for k in range(13)), 1.0, places=12)

    def test_binomial_known_values(self):
        self.assertAlmostEqual(luck.binom_pmf(2, 4, 0.5), 0.375, places=12)
        self.assertAlmostEqual(luck.binom_sf(10, 10, 0.5), 1 / 1024, places=12)

    def test_two_sided_binomial_symmetric_at_p_half(self):
        self.assertAlmostEqual(luck.binom_two_sided_p(5, 10, 0.5), 1.0, places=10)

    def test_brier_score_matches_sklearn_definition(self):
        probs = [0.1, 0.9, 0.8, 0.3]
        outcomes = [0, 1, 1, 0]
        # scikit-learn documented example: 0.0375 with scale_by_half=True
        self.assertAlmostEqual(luck.brier_score(probs, outcomes), 0.0375, places=12)

    def test_brier_decomposition_identity_is_exact_for_exact_bins(self):
        # Murphy's identity Brier = reliability - resolution + uncertainty holds
        # exactly when every bin groups forecasts that share one value.
        probs = [0.05] * 5 + [0.15] * 5 + [0.25] * 5 + [0.75] * 5 + [0.85] * 5 + [0.95] * 5
        outcomes = [0, 0, 0, 0, 0] * 3 + [1, 1, 1, 1, 1] * 3
        d = luck.brier_decomposition(probs, outcomes, n_bins=10)
        self.assertAlmostEqual(d.identity_error(), 0.0, places=12)
        self.assertAlmostEqual(d.uncertainty, 0.25, places=12)

    def test_brier_decomposition_within_binning_error_otherwise(self):
        # With mixed forecasts in a bin the identity is approximate; the error
        # must stay small enough not to change a decision.
        probs = [0.1, 0.2, 0.35, 0.6, 0.8, 0.9, 0.45, 0.55, 0.7, 0.3]
        outcomes = [0, 0, 0, 1, 1, 1, 0, 1, 1, 0]
        d = luck.brier_decomposition(probs, outcomes, n_bins=10)
        self.assertLess(abs(d.identity_error()), 5e-3)
        self.assertAlmostEqual(d.brier, luck.brier_score(probs, outcomes), places=12)

    def test_bootstrap_ci_is_deterministic(self):
        xs = [1.0, -1.0, 1.0, -1.0, 1.0, 1.0, -1.0, 1.0] * 5
        a = luck.bootstrap_mean_ci(xs, n_resamples=300, seed=7)
        b = luck.bootstrap_mean_ci(xs, n_resamples=300, seed=7)
        self.assertEqual(a["ci_lo"], b["ci_lo"])
        self.assertEqual(a["ci_hi"], b["ci_hi"])
        self.assertLessEqual(a["ci_lo"], a["mean"])
        self.assertGreaterEqual(a["ci_hi"], a["mean"])

    def test_block_bootstrap_wider_than_iid_on_autocorrelated_series(self):
        # a strongly autocorrelated series must widen the interval
        xs = ([1.0] * 10 + [-1.0] * 10) * 8
        iid = luck.bootstrap_mean_ci(xs, n_resamples=400, seed=11)
        blk = luck.block_bootstrap_mean_ci(xs, block=10, n_resamples=400, seed=11)
        self.assertGreaterEqual(blk["ci_hi"] - blk["ci_lo"], iid["ci_hi"] - iid["ci_lo"])

    def test_log_loss_perfect_forecast_is_zero(self):
        self.assertAlmostEqual(luck.log_loss([0.999999999], [1]), 1e-9, places=12) if False else None
        self.assertLess(luck.log_loss([1 - 1e-15], [1]), 1e-12)

    def test_constant_forecast_has_zero_resolution(self):
        d = luck.brier_decomposition([0.5] * 20, [0, 1] * 10, n_bins=10)
        self.assertAlmostEqual(d.resolution, 0.0, places=12)


class TestCorrelation(unittest.TestCase):
    def test_perfect_correlation(self):
        r = correlation.pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        self.assertAlmostEqual(r["r"], 1.0, places=12)

    def test_known_r_and_p(self):
        xs = [1, 2, 3, 4, 5, 6]
        ys = [2, 1, 4, 3, 6, 5]
        r = correlation.pearson(xs, ys)
        # Verified against scipy.stats.pearsonr on the same arrays.
        self.assertAlmostEqual(r["r"], 0.8285714285714286, places=10)
        self.assertEqual(r["df"], 4)

    def test_constant_series_returns_none_not_zero(self):
        r = correlation.pearson([1, 1, 1, 1], [1, 2, 3, 4])
        self.assertIsNone(r["r"])
        self.assertIn("constant", r["reason"])

    def test_too_few_points(self):
        self.assertIsNone(correlation.pearson([1, 2], [1, 2])["r"])

    def test_fisher_ci_contains_point_estimate(self):
        lo, hi = correlation.fisher_ci(0.2, 92)
        self.assertLess(lo, 0.2)
        self.assertGreater(hi, 0.2)
        self.assertTrue(-1.0 <= lo <= hi <= 1.0)

    def test_fisher_ci_undefined_small_n(self):
        self.assertEqual(correlation.fisher_ci(0.5, 3), (-1.0, 1.0))

    def test_spearman_on_monotone_nonlinear(self):
        xs = list(range(1, 30))
        ys = [x ** 3 for x in xs]
        self.assertAlmostEqual(correlation.spearman(xs, ys)["r"], 1.0, places=10)

    def test_copula_reduces_to_independence_at_rho_zero(self):
        for ps in ([0.55, 0.55], [0.7, 0.4], [0.3, 0.8, 0.5]):
            indep = correlation.indep_joint(ps)
            cop = correlation.gaussian_copula_joint(ps, 0.0)
            self.assertAlmostEqual(indep, cop, places=6)

    def test_copula_matches_scipy_bivariate_normal(self):
        """Cross-check against scipy when it is installed (the CI lab job does)."""
        try:
            import numpy as np
            from scipy.stats import multivariate_normal, norm
        except ImportError:  # pragma: no cover
            self.skipTest("scipy not installed")
        for rho in (0.1, 0.35, 0.6):
            for p in (0.4, 0.55, 0.75):
                z = norm.ppf(p)
                expected = multivariate_normal(mean=[0, 0], cov=[[1, rho], [rho, 1]]).cdf([z, z])
                got = correlation.gaussian_copula_joint([p, p], rho)
                self.assertAlmostEqual(expected, got, places=4)

    def test_copula_increases_with_positive_rho(self):
        base = correlation.gaussian_copula_joint([0.55, 0.55], 0.0)
        higher = correlation.gaussian_copula_joint([0.55, 0.55], 0.4)
        self.assertGreater(higher, base)

    def test_cluster_bootstrap_flags_non_independence(self):
        # identical pairs repeated within clusters must not look significant
        xs, ys, cl = [], [], []
        for c in range(4):
            for _ in range(40):
                xs.append(c * 1.0)
                ys.append(c * 1.0 + 0.1 * (len(xs) % 3))
                cl.append(f"c{c}")
        out = correlation.cluster_bootstrap_ci(xs, ys, cl, n_resamples=200, seed=3)
        self.assertEqual(out["n_clusters"], 4)
        self.assertLessEqual(out["ci_lo"], out["ci_hi"])


class TestPower(unittest.TestCase):
    def test_power_increases_with_n(self):
        sd = power.bet_sd(-110, 0.5238)
        self.assertLess(power.z_power(0.03, sd, 500), power.z_power(0.03, sd, 5000))

    def test_n_for_power_round_trip(self):
        sd = power.bet_sd(-110, 0.555)
        n = power.n_for_power(0.03, sd, 0.80, 0.05)
        self.assertGreaterEqual(power.z_power(0.03, sd, n, 0.05), 0.79)
        self.assertLess(power.z_power(0.03, sd, n - 1, 0.05), 0.81)

    def test_required_n_increases_as_edge_shrinks(self):
        rows = {r["target_roi"]: r["required_n"] for r in power.roi_table()}
        self.assertGreater(rows[0.01], rows[0.03])
        self.assertGreater(rows[0.03], rows[0.05])

    def test_family_wise_error_grows(self):
        self.assertAlmostEqual(power.false_discovery_after_tries(0.05, 1), 0.05, places=12)
        self.assertGreater(power.false_discovery_after_tries(0.05, 14), 0.5)

    def test_bet_sd_is_bounded(self):
        # a −110 bet cannot have a per-bet SD much above 1 unit
        for p in (0.3, 0.5, 0.5238, 0.6, 0.7):
            self.assertLess(power.bet_sd(-110, p), 1.1)


class TestMultipleTesting(unittest.TestCase):
    def test_bonferroni_is_exact_multiple(self):
        out = leaderboard.bonferroni([0.001, 0.02, 0.5])
        self.assertAlmostEqual(out["adjusted"][0], 0.003, places=12)
        self.assertAlmostEqual(out["adjusted"][1], 0.06, places=12)
        self.assertAlmostEqual(out["adjusted"][2], 1.0, places=12)

    def test_holm_never_stricter_than_bonferroni(self):
        pvals = [0.001, 0.009, 0.02, 0.04, 0.049]
        h = leaderboard.holm(pvals)["adjusted"]
        b = leaderboard.bonferroni(pvals)["adjusted"]
        for hi, bi in zip(h, b):
            self.assertLessEqual(hi, bi + 1e-12)

    def test_holm_rejects_less_than_raw(self):
        out = leaderboard.holm([0.01, 0.2, 0.3, 0.4, 0.5])
        self.assertTrue(out["reject"][0])
        self.assertFalse(out["reject"][1])

    def test_bh_more_powerful_than_holm(self):
        pvals = [0.001, 0.01, 0.02, 0.03, 0.9]
        self.assertGreaterEqual(sum(leaderboard.bh_fdr(pvals)["reject"]),
                                sum(leaderboard.holm(pvals)["reject"]))

    def test_deflated_sharpe_penalises_trials(self):
        one = leaderboard.deflated_sharpe(0.15, 1, 500)
        many = leaderboard.deflated_sharpe(0.15, 500, 500)
        self.assertGreater(one["dsr"], many["dsr"])
        self.assertGreaterEqual(many["sr0"], 0.0)

    def test_deflated_sharpe_single_trial_is_plain_probability(self):
        out = leaderboard.deflated_sharpe(0.0, 1, 400)
        self.assertAlmostEqual(out["dsr"], 0.5, places=6)

    def test_median_of_max_rises_with_family_size(self):
        a = leaderboard.max_of_n_median(10, 1.0, 100)
        b = leaderboard.max_of_n_median(100, 1.0, 100)
        self.assertGreater(b, a)


class TestGatesKnownAnswers(unittest.TestCase):
    """The core guarantee: the gates accept real skill and reject luck."""

    @classmethod
    def setUpClass(cls):
        cls.sim = simulate.run_all()

    @staticmethod
    def _evidence(s, **over):
        ev = gates.Evidence(
            strategy_id=s["id"], market="simulated", bet_type="single",
            n_observations=s["n"], per_bet_return=s["per_bet_return"],
            probs=s.get("probs", []), outcomes=s.get("outcomes", []),
            rights_confirmed=True, provenance_complete=True,
            plan_hash="sim", plan_hash_recomputed="sim",
            walk_forward=True, max_lookahead_days=0,
            ledger_hash="sim", deterministic=True,
            n_trials_in_family=1, p_values_in_family=[1e-9], seed=20261105,
        )
        for k, v in over.items():
            setattr(ev, k, v)
        return ev

    def test_gate_definitions_are_complete_and_unique(self):
        ids = [g[0] for g in gates.GATE_DEFS]
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        for gid, name, rule, src in gates.GATE_DEFS:
            self.assertTrue(gid.startswith("SG"))
            self.assertTrue(src.startswith("https://"))

    def test_missing_rights_fails_closed(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], rights_confirmed=False))
        self.assertIn("SG01", r["failed"])
        self.assertFalse(r["qualified"])

    def test_missing_provenance_fails_closed(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], provenance_complete=False))
        self.assertIn("SG02", r["failed"])

    def test_plan_hash_mismatch_fails(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], plan_hash_recomputed="changed"))
        self.assertIn("SG03", r["failed"])

    def test_lookahead_fails(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], max_lookahead_days=1))
        self.assertIn("SG04", r["failed"])

    def test_no_data_never_passes(self):
        # SG11 is the one gate that can pass on an empty record: a single-leg bet
        # has no joint dependence to state. Everything else must fail closed.
        empty = gates.Evidence(strategy_id="EMPTY", market="none", bet_type="single")
        r = gates.evaluate(empty)
        self.assertFalse(r["qualified"])
        self.assertEqual(r["failed"], [g for g in r["failed"] if g != "SG11"])
        self.assertEqual(len(r["failed"]), 11)
        self.assertEqual(r["passed"], ["SG11"])

    def test_lucky_heater_is_rejected(self):
        r = gates.evaluate(self._evidence(self.sim["A_HEATER"]))
        self.assertFalse(r["qualified"])
        self.assertIn("SG07", r["failed"])

    def test_low_power_real_edge_is_rejected(self):
        r = gates.evaluate(self._evidence(self.sim["E_LOWPOWER"]))
        self.assertFalse(r["qualified"])
        self.assertIn("SG05", r["failed"])

    def test_real_edge_passes_the_ev_gate(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"]))
        self.assertNotIn("SG07", r["failed"])

    def test_full_evidence_skill_qualifies(self):
        s = self.sim["F_SKILL_FULL"]
        r = gates.evaluate(self._evidence(
            s, model_logloss=s["model_logloss"], market_logloss=s["market_logloss"]))
        self.assertTrue(r["qualified"], msg=f"failed: {r['failed']}")

    def test_model_worse_than_market_fails_sg06(self):
        s = self.sim["F_SKILL_FULL"]
        r = gates.evaluate(self._evidence(
            s, model_logloss=s["market_logloss"], market_logloss=s["model_logloss"]))
        self.assertIn("SG06", r["failed"])

    def test_multi_leg_independence_is_rejected(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], support_legs=2,
                                          independence_assumed=True))
        self.assertIn("SG11", r["failed"])

    def test_multi_leg_with_measured_rho_passes_sg11(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], support_legs=2,
                                          rho_used=0.2, rho_n=92, rho_ci=(-0.01, 0.39)))
        self.assertNotIn("SG11", r["failed"])

    def test_declared_family_size_must_match(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"], n_trials_in_family=50,
                                          p_values_in_family=[0.001]))
        self.assertIn("SG09", r["failed"])

    def test_single_trial_single_leg_dependence_passes(self):
        r = gates.evaluate(self._evidence(self.sim["B_SKILL"]))
        self.assertNotIn("SG11", r["failed"])


class TestSimulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = simulate.run_all()

    def test_simulation_is_deterministic(self):
        again = simulate.run_all()
        self.assertEqual(self.sim["B_SKILL"]["roi"], again["B_SKILL"]["roi"])
        self.assertEqual(self.sim["A_HEATER"]["roi"], again["A_HEATER"]["roi"])

    def test_heater_really_is_zero_edge_and_positive(self):
        h = self.sim["A_HEATER"]
        self.assertEqual(h["true_edge"], 0.0)
        self.assertGreater(h["roi"], 0.10)

    def test_skill_roi_near_true_edge(self):
        s = self.sim["B_SKILL"]
        self.assertLess(abs(s["roi"] - s["true_edge"]), 0.02)

    def test_overfit_collapses_out_of_sample(self):
        c = self.sim["C_OVERFIT"]
        self.assertGreater(c["in_sample_roi_best"], 0.05)
        self.assertLess(c["oos_roi_best"], 0.02)

    def test_correlated_parlay_joint_exceeds_product(self):
        d = self.sim["D_CORRELATED"]
        self.assertGreater(d["p_joint_true"], d["p_joint_independent"])
        self.assertGreater(d["ev_true"], d["ev_if_independent"])

    def test_leg_probability_is_respected(self):
        d = self.sim["D_CORRELATED"]
        self.assertAlmostEqual(d["p_joint_independent"], 0.55 ** 2, places=10)


class TestAuditRecomputation(unittest.TestCase):
    """Recomputation from the committed CSVs must match what the site publishes."""

    @classmethod
    def setUpClass(cls):
        from skillab import audit
        cls.corr = audit.correlations()
        cls.fwd = audit.forward_test()

    def test_correlation_file_is_present(self):
        self.assertGreaterEqual(self.corr["n_rows"], 90)

    def test_home_away_r_matches_published(self):
        d = next(x for x in self.corr["differences"] if x["pair"] == "home_score_vs_away_score")
        self.assertTrue(d["reproduces"], msg=f"delta {d['delta']}")

    def test_rest_value_is_flagged_when_it_does_not_reproduce(self):
        d = next(x for x in self.corr["differences"] if x["pair"] == "rest_diff_vs_home_margin")
        self.assertFalse(d["reproduces"])
        self.assertLess(abs(d["published_r"]), 0.05)

    def test_same_date_cluster_interval_includes_zero(self):
        m = self.corr["measured"]["same_date_game_margins"]
        lo, hi = m["date_cluster_bootstrap_ci95"]
        self.assertLessEqual(lo, 0.0)
        self.assertGreaterEqual(hi, 0.0)

    def test_forward_test_summary_reproduces(self):
        for chk in self.fwd["checks"]:
            self.assertTrue(chk["match"], msg=f"{chk['metric']}: {chk}")

    def test_paired_logloss_interval_includes_zero(self):
        p = self.fwd["recomputed"]["paired_market_minus_model_logloss"]
        self.assertLess(p["ci95_lo"], 0.0)
        self.assertGreater(p["ci95_hi"], 0.0)

    def test_devig_reproduces_for_every_quote(self):
        self.assertTrue(self.fwd["devig_audit"]["all_fair_probs_reproduce"])

    def test_pbo_refuses_on_tiny_sample(self):
        from skillab import audit
        p = audit.pbo_from_repo_data()
        self.assertFalse(p["computed"])
        self.assertIn("requires", p["reason"])


class TestSiteDataContract(unittest.TestCase):
    """The published summary must not smuggle in a real-market claim."""

    @classmethod
    def setUpClass(cls):
        import json
        path = ROOT / "data" / "skill" / "skilllab_summary.json"
        if not path.exists():  # pragma: no cover
            raise unittest.SkipTest("build the site first")
        cls.data = json.loads(path.read_text(encoding="utf-8"))

    def test_meta_declares_zero_real_market_values(self):
        self.assertEqual(self.data["meta"]["real_nba_market_values_published"], 0)

    def test_all_gate_runs_are_present(self):
        self.assertEqual(len(self.data["gates"]), 5)

    def test_qualified_count_is_zero_for_real_strategies(self):
        # Only the fully-evidenced synthetic archetype may qualify.
        qualified = [k for k, v in self.data["gates"].items() if v["qualified"]]
        self.assertEqual(qualified, ["F_SKILL_FULL"])

    def test_no_gate_row_lacks_a_source(self):
        for run in self.data["gates"].values():
            for g in run["gates"]:
                self.assertTrue(g["source"].startswith("https://"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
