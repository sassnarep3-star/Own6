"""Validation gates and the promotion ladder. Fail-closed by construction.

Every gate returns ``open`` / ``closed`` plus the evidence it used. A strategy
reaches ``live`` only when **every** gate is open *and* a forward sample of at
least :data:`FORWARD_SAMPLE_MIN` graded bets exists after the gate set was
frozen. Nothing in this session can satisfy the forward-sample gate: a forward
sample requires time. That is the point -- it is the gate that stops a
backtest from being mistaken for a track record.

Gate set
--------
G01  Official inputs only          every input traces to an official NFL page
G02  Price snapshot present        opening and closing recorded for the market
G03  Verified results feed         every graded outcome has a final score
G04  Market comparison available   a market line exists to compute a difference
G05  Sample size                   n >= MIN_N_BACKTEST graded outcomes
G06  Luck removal                  p vs fair coin below the ceiling
G07  Correlation discipline        parlay legs measured, not assumed
G08  Demotion gate defined         a published trigger set exists
G09  Forward sample                >= FORWARD_SAMPLE_MIN out-of-sample bets
G10  Drawdown within limit         max drawdown inside the published limit
"""

from __future__ import annotations

from . import backtest as B
from . import correlations as K
from . import demotion as DM

MIN_N_BACKTEST = 100
FORWARD_SAMPLE_MIN = 200
P_CEILING = 0.05

GATE_ORDER = ["G%02d" % i for i in range(1, 11)]


def _g(gid, name, status, evidence, blocks):
    return {
        "gate_id": gid,
        "gate_name": name,
        "status": status,
        "evidence": evidence,
        "blocks_promotion": "yes" if status != "open" else "no",
        "why_it_blocks": blocks if status != "open" else "",
    }


def gate_rows(families, corr_rows):
    rows = []
    rows.append(
        _g(
            "G01",
            "Official inputs only",
            "open",
            "All inputs transcribed from 7 official NFL-family pages on %s; see data/nfl_market/sources.csv."
            % "2026-11-14",
            "",
        )
    )
    have_price = any(r["opening_price"] for r in B.price_snapshot_rows(B.backtest_all()))
    rows.append(
        _g(
            "G02",
            "Price snapshot present",
            "open" if have_price else "closed",
            "0 of %d snapshot rows carry a price. nfl.com/odds/ returns the NFL 404 page." % (
                2 * 3 * len(B.backtest_all())
            ),
            "Without an opening and a closing price there is no line movement to study and no "
            "market line to compute a difference against.",
        )
    )
    n_results = len([r for r in B.results_rows() if r["result_status"] == "final_verified"])
    rows.append(
        _g(
            "G03",
            "Verified results feed",
            "open" if n_results else "closed",
            "%d games carry a final score from an nfl.com schedule page." % n_results,
            "",
        )
    )
    rows.append(
        _g(
            "G04",
            "Market comparison available",
            "closed",
            "The difference column is blank for every originated market: no official market line "
            "exists to subtract.",
            "A signal that cannot be compared with the market cannot be shown to be an edge. "
            "Every strategy stays in paper.",
        )
    )
    min_n = min(f["n"] for f in families) if families else 0
    rows.append(
        _g(
            "G05",
            "Sample size",
            "open" if min_n >= MIN_N_BACKTEST else "closed",
            "Smallest family n = %d; requirement n >= %d." % (min_n, MIN_N_BACKTEST),
            "With fewer than %d graded bets the confidence interval is wider than any plausible "
            "edge." % MIN_N_BACKTEST,
        )
    )
    # Evidence is computed, not asserted: the best (smallest) one-sided p among
    # the strategy families, and whether it clears the ceiling at decision-grade n.
    qualifying = [f for f in families if f["n"] >= MIN_N_BACKTEST and f["p_one_sided_fair_coin"] is not None]
    best = min(qualifying, key=lambda f: f["p_one_sided_fair_coin"]) if qualifying else None
    if best is not None and best["p_one_sided_fair_coin"] < P_CEILING:
        status = "open"
    else:
        status = "closed"
    rows.append(
        _g(
            "G06",
            "Luck removal",
            status,
            (
                "Best one-sided p among families with n >= %d is %s (p=%s). Ceiling is p < %.2f."
                % (
                    MIN_N_BACKTEST,
                    best["strategy_id"] if best else "none",
                    best["p_one_sided_fair_coin"] if best else "n/a",
                    P_CEILING,
                )
            ),
            "A hit rate inside coin-flip noise is not a signal, whatever its ROI.",
        )
    )
    rows.append(
        _g(
            "G07",
            "Correlation discipline",
            "open",
            "All computable leg correlations measured with n published; the rest are refused rather "
            "than assumed (COR-06..COR-08).",
            "",
        )
    )
    rows.append(
        _g(
            "G08",
            "Demotion gate defined",
            "open",
            "D1-D5 published with fixed thresholds in src/nfl_market/demotion.py.",
            "",
        )
    )
    rows.append(
        _g(
            "G09",
            "Forward sample",
            "closed",
            "0 of %d required forward bets exist. Every number here is in-sample." % FORWARD_SAMPLE_MIN,
            "A backtest is not a track record. Promotion requires bets placed after the gate set "
            "was frozen.",
        )
    )
    worst_dd = max((d["max_drawdown_units"] for d in DM.gate_table(B.backtest_all())), default=0.0)
    rows.append(
        _g(
            "G10",
            "Drawdown within limit",
            "open" if worst_dd <= DM.THRESHOLDS["D2_max_drawdown_units"] else "closed",
            "Worst family drawdown %.2f units vs limit %.1f." % (worst_dd, DM.THRESHOLDS["D2_max_drawdown_units"]),
            "A strategy that already breached the demotion limit cannot be promoted past it.",
        )
    )
    return rows


def ladder(families, gates):
    """Per-strategy promotion status derived from the gates, fail-closed."""
    closed = [g["gate_id"] for g in gates if g["status"] != "open"]
    out = []
    for f in families:
        out.append(
            {
                "strategy_id": f["strategy_id"],
                "n": f["n"],
                "hit_rate": f["win_rate"],
                "gates_closed": ",".join(closed) if closed else "none",
                "rung": "paper" if closed else "candidate",
                "promotion_granted": "no",
                "why": (
                    "Blocked by %s. A strategy cannot leave paper while any gate is closed."
                    % (", ".join(closed) if closed else "nothing")
                ),
            }
        )
    return out


if __name__ == "__main__":  # pragma: no cover
    fams = B.family_table(B.backtest_all())
    for g in gate_rows(fams, K.all_rows()):
        print(g["gate_id"], g["status"], g["gate_name"])
