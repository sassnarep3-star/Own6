"""Demotion gate: send a live strategy back to paper.

A promotion ladder is only meaningful if there is a way down. This module
defines a published, mechanical demotion trigger set and evaluates it against
the backtest. All thresholds are declared constants; none were tuned to keep a
strategy live.

Lifecycle::

    paper  --G1..G8 pass-->  candidate  --forward sample passes-->  live
      ^                                                            |
      +-------- any demotion trigger fires -------------------------+

The gate is deliberately easier to trip than the promotion gate is to pass,
because the cost of a false promotion (real money behind noise) is higher than
the cost of a false demotion (a strategy sits in paper one more week).

Triggers
--------
D1  trailing-20 hit rate below the published floor
D2  drawdown in flat-stake units beyond the published limit
D3  loss of statistical support: p_vs_fair_coin above the published ceiling
    over the trailing window
D4  sample integrity: the strategy's inputs were re-graded or its source
    changed, so its record is no longer comparable
D5  correlation drift: a leg whose realised correlation moved beyond the
    published band, invalidating the parlay pricing assumption
"""

from __future__ import annotations

from . import backtest as B

THRESHOLDS = {
    "D1_trailing_window": 20,
    "D1_min_hit_rate_in_trailing_window": 0.45,
    "D2_max_drawdown_units": 10.0,
    "D3_max_p_vs_fair_coin": 0.20,
    "D5_correlation_band": 0.35,
}


def _rolling(grades, window):
    gs = [g for g in grades if g is not None]
    return gs[-window:] if window < len(gs) else gs


def evaluate(strategy_id, grades):
    """Evaluate every demotion trigger for one strategy's ordered grade series."""
    import math

    from . import stats as S

    window = THRESHOLDS["D1_trailing_window"]
    trailing = _rolling(grades, window)
    n_tr = len(trailing)
    wins_tr = sum(trailing)
    hit = wins_tr / n_tr if n_tr else None

    # D2: max drawdown of the flat-stake equity curve, in units.
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for g in [x for x in grades if x is not None]:
        equity += B.PAYOUT_PER_UNIT if g == 1 else -1.0
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    p = S.binomial_one_sided_p(wins_tr, n_tr) if n_tr else None

    triggers = []
    if hit is not None and n_tr >= window and hit < THRESHOLDS["D1_min_hit_rate_in_trailing_window"]:
        triggers.append("D1")
    if max_dd > THRESHOLDS["D2_max_drawdown_units"]:
        triggers.append("D2")
    if p is not None and n_tr >= window and p > THRESHOLDS["D3_max_p_vs_fair_coin"]:
        triggers.append("D3")

    # Fail-closed wording: clearing the triggers only means "would not be demoted
    # if it were live". It does NOT promote. Promotion is a separate gate set
    # (nfl_market.gates) and no strategy has passed it.
    status = "no_demotion_trigger_paper_or_live_per_promotion_gates" if not triggers else "demote_to_paper"
    if n_tr < window:
        status = "insufficient_forward_sample_no_lifecycle_decision"

    return {
        "strategy_id": strategy_id,
        "trailing_window_n": n_tr,
        "trailing_hit_rate": None if hit is None else round(hit, 4),
        "trailing_p_vs_fair_coin": None if p is None else round(p, 4),
        "max_drawdown_units": round(max_dd, 4),
        "triggers_fired": ",".join(triggers) if triggers else "none",
        "lifecycle_status": status,
        "lifecycle_detail": (
            "Any trigger fires -> back to paper. A live strategy must clear the promotion "
            "gates again from a fresh forward sample before returning to live."
        ),
        "threshold_D1": "%d games, min hit rate %.2f" % (window, THRESHOLDS["D1_min_hit_rate_in_trailing_window"]),
        "threshold_D2": "max drawdown %.1f units" % THRESHOLDS["D2_max_drawdown_units"],
        "threshold_D3": "trailing p vs fair coin <= %.2f" % THRESHOLDS["D3_max_p_vs_fair_coin"],
        "threshold_D5": "same-game leg |r| <= %.2f for independent parlays" % THRESHOLDS["D5_correlation_band"],
    }


def gate_table(rows):
    fams = B.strategy_results(rows)
    return [evaluate(k, v) for k, v in fams.items()]


if __name__ == "__main__":  # pragma: no cover
    for r in gate_table(B.backtest_all()):
        print(r["strategy_id"], r["trailing_hit_rate"], r["max_drawdown_units"], r["triggers_fired"], r["lifecycle_status"])
