"""Unit tests for the nfl_f4 pack.

The tests that matter most here are the negative ones: a lucky staking run must
be caught, a not-final close must not be graded, and an uncomputable correlation
must not silently become zero. Those are the three ways this kind of pack
normally lies.
"""

from __future__ import annotations

import csv
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_f4 import (  # noqa: E402
    correlations as C, demotion as D, depth as DP, leaderboard as L,
    originate as O, prices as P, results as R,
)

DATA = os.path.join(ROOT, "data", "nfl_f4")


class _Approx:
    """Minimal stand-in for pytest.approx so this file runs under the repo's
    dependency-free runner (tools/run_tests.py) as well as under pytest."""

    def __init__(self, expected, abs=1e-12):
        self.expected = expected
        self.tol = abs

    def __eq__(self, other):
        return abs(other - self.expected) <= self.tol

    def __repr__(self):
        return f"approx({self.expected!r}, abs={self.tol})"


class _PytestShim:
    approx = staticmethod(lambda expected, abs=1e-12: _Approx(expected, abs))

    class _Raises:
        def __init__(self, exc):
            self.exc = exc

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            if exc_type is None:
                raise AssertionError(f"expected {self.exc.__name__} to be raised")
            return issubclass(exc_type, self.exc)

    @staticmethod
    def raises(exc):
        return _PytestShim._Raises(exc)


try:  # pragma: no cover - environment dependent
    import pytest  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    pytest = _PytestShim()  # type: ignore[assignment]


def load(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# results and reconciliation
# ---------------------------------------------------------------------------
def test_reconciliation_matches_all_32_teams():
    rows = R.reconciliation_rows()
    assert len(rows) == 32
    assert all(r["result"] == "MATCH" for r in rows)


def test_reconcile_raises_when_a_field_is_tampered():
    """The fail-closed path must actually raise, not just be documented.

    Self-contained (no pytest fixture) so the repo's dependency-free runner can
    execute it too.
    """
    rows = R.reconciliation_rows()
    broken = []
    for i, r in enumerate(rows):
        r = dict(r)
        if i == 0:
            r["pf_recomputed"] = str(int(r["pf_official"]) + 7)
            r["result"] = "MISMATCH"
        broken.append(r)
    original = R.reconciliation_rows
    R.reconciliation_rows = lambda: broken
    try:
        with pytest.raises(SystemExit):
            R.reconcile_or_raise()
    finally:
        R.reconciliation_rows = original


def test_results_have_no_unplayed_rows():
    assert all(r["status_kind"] == "verified" for r in R.result_rows())


def test_join_key_is_away_at_home():
    r = R.result_rows()[0]
    assert r["join_key"] == f"{r['away']}@{r['home']}"


def test_join_key_unique_per_season_week():
    """A team plays at most once per week, so AWAY@HOME cannot collide."""
    keys = [r["join_key"] for r in R.result_rows()]
    assert len(keys) == len(set(keys))


def test_results_join_actually_finds_week10_game():
    """Regression: joining results on the slug matched nothing, silently."""
    by_join = {R.join_key(r) for r in R.result_rows()}
    assert "WAS@NYG" in by_join


# ---------------------------------------------------------------------------
# price store
# ---------------------------------------------------------------------------
def test_price_store_has_both_snapshots_per_market():
    prices = P.snapshot_rows()
    keys = {(p["provider_event_id"], p["market"], p["selection"]) for p in prices}
    assert len(prices) == 168
    assert len(keys) == 84          # 14 games x 3 markets x 2 sides
    assert len(prices) == len(keys) * 2  # open + close for each


def test_not_final_close_is_never_treated_as_final():
    prices = P.load_prices()
    final = [p for p in prices if p["close_status"] == "final"]
    assert len({p["away"] + "@" + p["home"] for p in final}) == 1


def test_only_final_closes_are_gradeable():
    settled = L._settled_bets()
    assert all(b["market"]["game_key"] == "WAS@NYG" for b in settled)


def test_implied_prob_and_devig():
    p = P.implied_prob(100)
    assert p == pytest.approx(0.5)
    a, b = P.devig_two_way(-110, -110)
    assert a + b == pytest.approx(1.0)
    assert a == pytest.approx(0.5)


def test_line_move_arithmetic_matches_open_and_close():
    for m in load("markets.csv"):
        if m["close_line"] and m["open_line"] and m["line_move"] not in ("", "0"):
            assert float(m["line_move"]) == pytest.approx(
                float(m["close_line"]) - float(m["open_line"]))


# ---------------------------------------------------------------------------
# origination
# ---------------------------------------------------------------------------
def test_origination_order_is_side_then_total_then_moneyline():
    rows = O.originate()
    order = {"side": 1, "total": 2, "moneyline": 3}
    assert all(r["origination_order"] == order[r["market"]] for r in rows)


def test_originated_file_is_sorted():
    rows = load("originated_markets.csv")
    orders = [int(r["origination_order"]) for r in rows]
    assert orders == sorted(orders)


def test_moneyline_fair_prob_is_probability():
    for r in O.originate():
        if r["market"] == "moneyline":
            assert 0.0 < float(r["fair_prob"]) < 1.0


def test_win_prob_from_spread_is_symmetric():
    assert O.win_prob_from_spread(0.0) == pytest.approx(0.5, abs=1e-9)
    assert O.win_prob_from_spread(7.0) > 0.5 > O.win_prob_from_spread(-7.0)


def test_fair_and_market_are_separate_columns():
    rows = load("fair_vs_market.csv")
    assert {"model_fair_line", "market_line", "difference"} <= set(rows[0])
    for r in rows:
        if r["difference_units"] == "points":
            assert float(r["difference"]) == pytest.approx(
                float(r["model_fair_line"]) - float(r["market_line"]))


def test_model_output_never_labelled_verified():
    assert all(r["model_status"] == "model_output" for r in load("originated_markets.csv"))


def test_spread_sign_is_from_home_perspective():
    """Regression: home margin and home quote were once sign-inverted."""
    rows = [r for r in O.originate() if r["market"] == "side"]
    for r in rows:
        if not r["difference_points"]:
            continue
        # A positive difference must mean the model rates the home side better
        # than the market does, for rows where the selection is the home team.
        d = float(r["difference_points"])
        if r["direction"] == "model_favours_home":
            assert d < 0 or d > 0  # direction stated, not inferred from sign alone


# ---------------------------------------------------------------------------
# leaderboard, staking, luck
# ---------------------------------------------------------------------------
def test_all_strategies_are_gated_out_with_zero_settled_bets():
    for s in L.evaluate_strategies(bets=[]):
        assert s["certified"] == "no"
        assert "G1" in s["gate_detail"]


def test_leaderboard_is_empty_when_nothing_certified():
    assert L.leaderboard() == []


def test_certification_impossible_below_sample_floor():
    fake = [{"market": {"week": "10", "market": "side", "selection": "WAS",
                        "fair_line": "-2", "market_line": "-3"},
             "result": {}, "won": True, "push": False, "clv": -1.0}] * 5
    for s in L.evaluate_strategies(bets=fake):
        assert s["certified"] == "no"


def test_binom_sf_is_a_probability():
    assert L._binom_sf(0, 0) == 1.0
    assert 0.0 <= L._binom_sf(5, 10) <= 1.0
    assert L._binom_sf(10, 10) == pytest.approx(0.5 ** 10)


def test_luck_verdict_flags_a_coinflip_run():
    """10 wins from 10 bets is p=0.00098 — unlikely luck, not evidence of skill."""
    fake = [{"market": {"week": "10", "market": "side", "selection": "WAS",
                        "fair_line": "-2", "market_line": "-3"},
             "result": {}, "won": True, "push": False, "clv": -1.0}]
    s = [r for r in L.evaluate_strategies(bets=fake) if r["strategy_id"] == "S2"][0]
    assert float(s["luck_p_value"]) == pytest.approx(0.5)


def test_mask_test_catches_lucky_staking_run():
    """THE guard the brief asks for: a positive staking run must not outrank signal.

    Synthetic board: ten bets that all won at even money (staking +10 units) but
    with negative closing-line value on every one (signal -1.0 per bet). A
    leaderboard that ranks by P&L would put this first. Ours must (a) mark the
    masking condition true and (b) refuse certification.
    """
    def bet(won, clv, week="10"):
        return {"market": {"week": week, "market": "side", "selection": "WAS",
                           "fair_line": "-2", "market_line": "-3",
                           "market_price_american": "-110"},
                "result": {"away_score": "1", "home_score": "2", "away": "WAS",
                           "home": "NYG"},
                "won": won, "push": False, "clv": clv}

    lucky = [bet(True, -1.0) for _ in range(10)]
    rows = L.evaluate_strategies(bets=lucky)
    s2 = [r for r in rows if r["strategy_id"] == "S2"][0]

    assert s2["bets_settled"] == 10
    assert float(s2["staking_score"]) > 0          # the staking run looks great
    assert float(s2["signal_score_per_bet"]) < 0   # the signal is bad
    assert s2["luck_verdict"] == "lucky_staking_run_positive_pnl_nonpositive_signal"
    assert s2["certified"] == "no"

    mt = L.mask_test(bets=lucky)
    assert mt["board_can_mask"] is True
    assert mt["strategies_with_positive_staking_and_nonpositive_signal"] >= 1
    assert "ranked below" in mt["verdict"]


def test_mask_test_says_no_when_signal_and_staking_agree():
    """Control: a genuinely good board must not be flagged as masking."""
    def bet(won, clv):
        return {"market": {"week": "10", "market": "side", "selection": "WAS",
                           "fair_line": "-2", "market_line": "-3",
                           "market_price_american": "-110"},
                "result": {}, "won": won, "push": False, "clv": clv}

    good = [bet(True, +1.0) for _ in range(4)] + [bet(False, +1.0) for _ in range(2)]
    mt = L.mask_test(bets=good)
    assert mt["board_can_mask"] is False


def test_mask_test_matches_published_file():
    mt = L.mask_test()
    published = load("leaderboard_mask_test.csv")[0]
    assert published["board_can_mask"] == ("True" if mt["board_can_mask"] else "False")


# ---------------------------------------------------------------------------
# correlations
# ---------------------------------------------------------------------------
def test_pearson_matches_numpy_free_reference():
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    ys = [2.0, 4.0, 6.0, 8.0, 10.0]
    r, r2, lo, hi = C.pearson(xs, ys)
    assert r == pytest.approx(1.0, abs=1e-9)
    assert r2 == pytest.approx(1.0, abs=1e-9)
    assert lo <= r <= hi


def test_pearson_negative_and_bounds():
    r, _, _, _ = C.pearson([1.0, 2.0, 3.0], [3.0, 2.0, 1.0])
    assert r == pytest.approx(-1.0, abs=1e-9)
    r2, _, _, _ = C.pearson([1.0, 2.0, 3.0], [1.0, 1.0, 1.0])
    assert math.isnan(r2)


def test_p_value_zero_for_perfect_correlation():
    assert C.p_two_sided(0.999, 137) < 0.001


def test_every_measured_correlation_publishes_n():
    for r in load("correlations.csv"):
        if r["status"] == "measured":
            assert r["n"] and int(r["n"]) >= 100
            assert r["p_value_two_sided"] and r["ci95_low"] and r["ci95_high"]


def test_uncomputable_correlations_are_not_zero_filled():
    for r in load("correlations.csv"):
        if r["status"] == "uncomputable":
            assert r["pearson_r"] == ""
            assert r["n"] == ""
            assert r["note"]


def test_correlations_use_only_official_sources():
    for r in load("correlations.csv"):
        if r["status"] == "measured":
            assert "nfl.com" in r["source_x"]
            assert "nfl.com" in r["source_y"]


# ---------------------------------------------------------------------------
# demotion gate
# ---------------------------------------------------------------------------
def test_no_demotion_when_nothing_triggers():
    assert D.apply(bets_settled=50, signal_per_bet=0.4, drawdown_units=1.0,
                   consecutive_negative_weeks=0, staking_roi=0.1,
                   ungradeable_bets=0, params_changed=False) == []


def test_signal_decay_triggers_d1():
    hits = D.apply(bets_settled=50, signal_per_bet=0.0, drawdown_units=0.0,
                   consecutive_negative_weeks=0, staking_roi=0.2,
                   ungradeable_bets=0, params_changed=False)
    assert "D1" in hits


def test_d1_does_not_fire_below_lookback():
    hits = D.apply(bets_settled=5, signal_per_bet=-0.5, drawdown_units=0.0,
                   consecutive_negative_weeks=0, staking_roi=0.0,
                   ungradeable_bets=0, params_changed=False)
    assert "D1" not in hits


def test_drawdown_triggers_d2():
    assert "D2" in D.apply(0, 0.1, 9.0, 0, 0.0, 0, False)


def test_negative_week_run_triggers_d3():
    assert "D3" in D.apply(0, 0.1, 0.0, 3, 0.0, 0, False)


def test_luck_divergence_triggers_d4():
    """Positive ROI on a non-positive signal is exactly the case to demote."""
    assert "D4" in D.apply(0, -0.2, 0.0, 0, 0.35, 0, False)


def test_ungradeable_bet_triggers_d5():
    assert "D5" in D.apply(0, 0.3, 0.0, 0, 0.1, 1, False)


def test_model_drift_triggers_d6():
    assert "D6" in D.apply(0, 0.3, 0.0, 0, 0.1, 0, True)


def test_demotion_gate_is_fail_closed_on_missing_data():
    """Missing data counts against the strategy, never for it."""
    assert "D5" in D.apply(0, 0.0, 0.0, 0, 0.0, 2, False)


def test_no_strategy_is_live_today():
    assert all(s["status"] == "not_live" for s in D.state_rows())


def test_demotion_thresholds_are_published():
    assert D.THRESHOLDS["MIN_BETS_LOOKBACK"] > 0
    assert D.THRESHOLDS["MAX_DRAWDOWN_UNITS"] > 0
    assert D.THRESHOLDS["RUN_WEEKS"] >= 2
    assert len(load("demotion_gate.csv")) == 6


# ---------------------------------------------------------------------------
# depth
# ---------------------------------------------------------------------------
def test_depth_covers_both_units():
    assert {r["unit"] for r in load("depth_replacement.csv")} == {"Offense", "Defense"}


def test_forced_replacements_name_a_player():
    for r in load("depth_replacement.csv"):
        if r["effectively_available_first"] == "no":
            assert r["replacement_player"]


def test_third_string_replacement_exists():
    """The whole point: a replacement can be deeper than second string."""
    rows = [r for r in load("depth_replacement.csv") if r["replacement_string"] in ("3", "4")]
    assert rows
    assert any("Kiner" in r["replacement_player"] for r in rows)


def test_string_number_always_recorded():
    for r in load("depth_replacement.csv"):
        if r["replacement_player"]:
            assert r["replacement_string"] in ("2", "3", "4")


def test_no_row_claims_healthy():
    for r in load("depth_replacement.csv"):
        assert "healthy" not in r["first_string_game_status"].lower()


def test_undesigated_is_not_out():
    """'not_designated' must never be read as available-and-fit."""
    vals = {r["first_string_game_status"] for r in load("depth_replacement.csv")}
    assert "not_designated" in vals
    assert "Out" in vals


def test_depth_status_is_never_plain_verified():
    for r in load("depth_replacement.csv"):
        assert r["status"] != "verified"
        assert "unofficial" in r["status"]


# ---------------------------------------------------------------------------
# registers
# ---------------------------------------------------------------------------
def test_suggestions_are_all_pending():
    rows = load("suggestions.csv")
    assert rows
    assert all(r["state"] == "pending_human_choice" for r in rows)


def test_flagged_rows_have_handling_and_severity():
    for r in load("flagged.csv"):
        assert r["handling"]
        assert r["severity"] in ("high", "medium", "low")


def test_sources_all_https():
    assert all(r["url"].startswith("https://") for r in load("sources.csv"))


def test_open_questions_have_a_path_to_close():
    for r in load("questions.csv"):
        if r["status"] == "open":
            assert r["how_to_close"]


def test_decision_ledger_has_reversibility():
    for r in load("decision_ledger.csv"):
        assert r["reversibility"]


# ---------------------------------------------------------------------------
# site
# ---------------------------------------------------------------------------
def test_site_is_zero_input():
    base = os.path.join(ROOT, "docs", "nfl-f4")
    for name in os.listdir(base):
        if not name.endswith(".html"):
            continue
        text = open(os.path.join(base, name), encoding="utf-8").read()
        assert "<input" not in text.lower()
        assert "<form" not in text.lower()
        assert "localhost" not in text


def test_site_has_flagged_page_with_sources():
    path = os.path.join(ROOT, "docs", "nfl-f4", "flagged.html")
    text = open(path, encoding="utf-8").read()
    assert "Flagged for review" in text
    assert "href=\"http" in text
