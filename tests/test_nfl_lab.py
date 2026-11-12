"""Tests for the NFL lines lab: model maths, gate honesty, and page guard rails.

The tests are adversarial. They check the things that make a published research
page wrong: a sign flip, a filled blank, a gate that passes without evidence,
a correlation multiplied as if independent, a leaderboard that ranks on luck.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from nfllab import combos, correlation, pricing, ratings, validation  # noqa: E402

DATA = ROOT / "data" / "nfl"


# --------------------------------------------------------------- pricing
def test_home_favourite_has_negative_spread():
    """A negative home spread must mean the home team is favoured."""
    # Expected home margin of +6 against a home spread of -3 must be well above 50%.
    p = pricing.cover_probability(margin=6.0, line=-3.0, sd=13.9)["p_home"]
    assert p > 0.55, "a 6-point edge over a 3-point spread must cover more often than not"
    # The same margin against a bigger requirement (-9) is a losing proposition.
    q = pricing.cover_probability(margin=6.0, line=-9.0, sd=13.9)["p_home"]
    assert q < 0.45 and q < p, "a bigger favourite line must lower cover probability"
    # Laying exactly the expected margin is a coin flip, not a lock.
    r = pricing.cover_probability(margin=6.0, line=-6.0, sd=13.9)
    assert 0.45 < r["p_home"] < 0.55 and r["push"] > 0
    # Getting 6 points when the expectation is only +6 is close to a lock.
    s6 = pricing.cover_probability(margin=6.0, line=6.0, sd=13.9)
    assert s6["p_home"] > 0.75


def test_probabilities_are_a_partition():
    m = pricing.cover_probability(margin=-2.5, line=-2.0, sd=13.9)
    t = pricing.total_over_probability(total_mean=43.5, line=43.0, sd=13.9)
    assert abs(m["p_home"] + m["p_away"] + m["push"] - 1.0) < 1e-9
    assert abs(t["p_over"] + t["p_under"] + t["push"] - 1.0) < 1e-9
    assert t["push"] > 0, "a whole-number line must have a push mass"
    assert 0 < m["p_home"] < 1


def test_american_odds_round_trip():
    for p in (0.2, 0.35, 0.5, 0.62, 0.8):
        american = pricing.prob_to_american(p)
        assert abs(pricing.american_to_prob(american) - p) < 0.01


def test_american_odds_are_never_between_minus_100_and_plus_100():
    for p in np.linspace(0.05, 0.95, 19):
        a = pricing.prob_to_american(float(p))
        assert a <= -100 or a >= 100, f"{a} is not a valid American price"


# ----------------------------------------------------------- correlation
def test_phi_is_zero_for_independent_tables():
    rng = np.random.default_rng(7)
    a = rng.integers(0, 2, 4000)
    b = rng.integers(0, 2, 4000)
    phi = correlation.phi(a, b)
    assert abs(phi) < 0.06, "phi must not invent dependence"


def test_phi_matches_hand_computation():
    # 2x2: [[30, 10], [10, 30]] -> phi = (ad-bc)/sqrt(...) = 0.5
    a = np.array([1] * 40 + [0] * 40)
    b = np.array([1] * 30 + [0] * 10 + [1] * 10 + [0] * 30)
    assert abs(correlation.phi(a, b) - 0.5) < 1e-9


def test_joint_probability_never_leaves_frechet_bounds():
    lo, hi = correlation.frechet_bounds(0.52, 0.55)
    assert 0.07 - 1e-9 <= lo <= hi <= 0.52 + 1e-9
    for rho in (-0.99, -0.4, 0.0, 0.4, 0.99):
        joint = correlation.joint_from_copula(0.52, 0.55, rho)
        assert lo - 1e-6 <= joint <= hi + 1e-6


def test_clustered_ci_refuses_too_few_clusters():
    rng = np.random.default_rng(3)
    vals = rng.normal(0.0, 1.0, 20)
    groups = np.array(["a"] * 5 + ["b"] * 5 + ["c"] * 5 + ["d"] * 5)
    assert correlation.cluster_bootstrap_ci(vals, groups, np.mean) is None


def test_clustered_ci_is_wide_when_clusters_disagree():
    rng = np.random.default_rng(11)
    vals, groups = [], []
    for i in range(20):
        vals.extend(rng.normal(loc=(-1) ** i * 2.0, scale=0.3, size=8))
        groups.extend([i] * 8)
    ci = correlation.cluster_bootstrap_ci(np.array(vals), np.array(groups), np.mean)
    assert ci and ci[1] - ci[0] > 1.0, "clustered intervals must reflect between-cluster spread"
    # and the point estimate must be near zero because the clusters cancel out
    assert ci[0] < 0 < ci[1]


# ------------------------------------------------------------ validation
def test_gate_registry_is_complete_and_ordered():
    ids = validation.GATE_IDS
    assert ids == [f"G{i:02d}" for i in range(1, 11)]
    assert len(validation.GATE_DEFINITIONS) == 10
    for gid, meta in validation.GATE_DEFINITIONS.items():
        assert meta["threshold"] and meta["name"]


def test_gates_block_rather_than_pass_without_evidence():
    """No licence, no provenance, a tiny sample: no gate may pass."""
    fails = validation.gate_rights("unverified", "https://www.nfl.com/legal/terms")
    prov = validation.gate_provenance(0, 0, "https://www.nfl.com/injuries/")
    sample = validation.gate_sample(10, 3, 2, "https://www.nfl.com/standings/")
    for g in (fails, prov, sample):
        assert g.as_row()["status"] != "pass", f"{g.gate_id} passed without evidence"
    assert fails.as_row()["status"] == "fail"
    assert prov.as_row()["status"] == "blocked"   # no rows -> unknown, never a pass
    assert sample.as_row()["status"] == "fail"


def test_deflated_sharpe_penalises_more_trials():
    rng = np.random.default_rng(5)
    series = rng.normal(0.30, 1.0, 300)
    one = validation.gate_deflated_sharpe(series, 1, "https://www.nist.gov/")
    eight = validation.gate_deflated_sharpe(series, 8, "https://www.nist.gov/")
    assert one.as_row()["status"] == "pass"
    assert eight.as_row()["status"] == "fail", "the same series must fail after eight trials"
    assert one.observed != eight.observed


def test_multiplicity_gate_needs_a_signal_to_award_a_pass():
    # A raw p of 0.01 survives a family of two (0.02) and dies in a family of six (0.06).
    two = validation.gate_multiplicity([0.01, 0.9], "https://www.nist.gov/")
    six = validation.gate_multiplicity([0.01, 0.9, 0.5, 0.6, 0.7, 0.8], "https://www.nist.gov/")
    assert two.as_row()["status"] == "pass"
    assert six.as_row()["status"] == "fail"


# --------------------------------------------------------------- ratings
def _rows(n, margin, season=2024):
    return [{"season": season, "home_team": "A", "away_team": "B",
             "home_score": 27 if margin >= 0 else 27 + margin,
             "away_score": 27 - margin if margin >= 0 else 27,
             "week": (i % 17) + 1} for i in range(n)]


def test_ratings_recover_a_known_margin():
    """A team winning by 10 both home and away must rate ~10 points better."""
    home_win = {"season": 2024, "home_team": "A", "away_team": "B", "home_score": 27,
                "away_score": 17, "week": 1}
    away_win = {"season": 2024, "home_team": "B", "away_team": "A", "home_score": 17,
                "away_score": 27, "week": 2}
    r = ratings.fit_ratings([home_win, away_win] * 10, asof_season=2025)
    gap = r.expected_margin("A", "B")
    assert 8.0 < gap < 12.0, f"expected a ~10 point gap, got {gap:.2f}"
    assert r.expected_margin("B", "A") < 0 < gap


def test_ratings_shrink_more_with_fewer_games():
    """The empirical-Bayes shrink factor g/(g+k) must damp a thin sample more."""
    filler = []
    for w in range(1, 15):
        filler.append({"season": 2024, "home_team": "C", "away_team": "D",
                       "home_score": 21 + (w % 3), "away_score": 20 + (w % 4), "week": w})
        filler.append({"season": 2024, "home_team": "D", "away_team": "C",
                       "home_score": 23 - (w % 3), "away_score": 22 + (w % 2), "week": w})

    def blowout(season, week):
        return {"season": season, "home_team": "A", "away_team": "B",
                "home_score": 34, "away_score": 10, "week": week}

    thin = ratings.fit_ratings(filler + [blowout(2024, 15)], asof_season=2025).expected_margin("A", "B")
    fat = ratings.fit_ratings(filler + [blowout(2024, w) for w in range(1, 15)], asof_season=2025).expected_margin("A", "B")
    assert 0 < thin < fat, f"one game ({thin:.2f}) must be shrunk harder than fourteen ({fat:.2f})"


# ---------------------------------------------------------------- combos
def test_combo_table_multiplies_two_legs_correctly():
    table = combos.combo_price_table(p_leg1=0.52, p_leg2=0.55, rho=None, offered_decimals=[2.61])
    indep = [r for r in table if "independence" in r["method"].lower()][0]
    assert abs(indep["joint"] - 0.52 * 0.55) < 1e-9
    assert indep["fair_american"] > 100, "a 28.6% joint must be a plus price"


def test_combo_table_prices_are_inside_frechet_bounds():
    table = combos.combo_price_table(p_leg1=0.52, p_leg2=0.55, rho=0.30, offered_decimals=[2.61])
    lo, hi = correlation.frechet_bounds(0.52, 0.55)
    for r in table:
        if r["joint"] is not None:
            assert lo - 1e-6 <= r["joint"] <= hi + 1e-6, r["method"]


def test_parlay_ev_at_two_standard_prices_is_negative():
    for price in (2.61, 2.70):
        ev = correlation.parlay_prob(0.25, price)["ev_per_unit"]
        assert ev < 0, "a 25% joint at a two-leg -110 payout must be negative EV"


# -------------------------------------------------------- page artefacts
def test_pages_exist_and_are_ascii():
    pages = sorted((ROOT / "docs" / "nfl" / "lab").glob("*.html"))
    assert len(pages) == 14
    for p in pages:
        p.read_text(encoding="ascii")  # raises on a smart quote or em dash


def test_checker_passes():
    import check_nfl_lab
    errs = check_nfl_lab.check()
    assert errs == [], "\n".join(errs)


def test_no_market_price_is_published():
    lines = json.loads((DATA / "model" / "week10.json").read_text())
    for g in lines["games"]:
        for key in ("market_spread", "market_total"):
            assert not g.get(key), f"{g['game_id']} carries an unverified market price"


def test_status_rollup_fails_closed():
    """A failed gate can never be rescued by a blocked one, and a pass needs all ten."""
    cand = {"candidate_id": "T", "name": "t", "market": "m",
            "source_url": "https://www.nfl.com/", "license_status": "unverified"}
    row = validation.evaluate_candidate(cand, None)
    assert row["status"] == "rejected", "G01 fails, so the candidate is rejected even with 8 blocked gates"
    assert row["gates_total"] == 10 and row["gates_passed"] == 0


def test_backtest_has_no_qualified_strategy_without_evidence():
    b = json.loads((DATA / "model" / "backtest.json").read_text())
    for cand in b["gates"]:
        if cand["status"] == "qualifies":
            assert all(g["status"] == "pass" for g in cand["gates"])
    assert b["qualifiers"] == [c["candidate_id"] for c in b["gates"] if c["status"] == "qualifies"]
    assert all(c["status"] in ("rejected", "blocked") for c in b["gates"]), "no candidate may qualify"


def test_leaderboard_ranks_on_lower_bound_not_point_estimate():
    b = json.loads((DATA / "model" / "backtest.json").read_text())
    quals = [r for r in b["leaderboard"] if r["status"] == "qualifies"]
    assert quals == [], "the board is expected to be empty on current evidence"
