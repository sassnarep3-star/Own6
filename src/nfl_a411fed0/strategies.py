"""Strategy definitions, signal-vs-staking separation and the leaderboard.

Each strategy emits *signals* first (which side/total/moneyline, and the
edge it claims).  Staking is a **separate** layer: the same signal can be
run under flat staking, Kelly staking or Martingale staking and the
leaderboard reports them in different columns so that a lucky staking run
can never be mistaken for a good signal.

Backtests are run as **walk-forward probability scoring**, not as betting
records: we have no prices, so no bet was ever placed and no ROI exists.
What we can measure out-of-sample is whether the probabilities the
strategy produced were calibrated - a signal that is not calibrated
cannot be profitable at any stake size.
"""
from __future__ import annotations

import json
import math
import os
from typing import Callable, Dict, List, Sequence

from . import dataset, model

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "nfl_a411fed0")

BREAK_EVEN = 0.5238  # -110


# --------------------------------------------------------------------- signals
def _fit(train):
    return model.fit_side(train), model.fit_total(train)


def sig_power_side(g, side, total):
    """Baseline: bet the side whenever the model's margin differs from zero."""
    pm = side["rate"][g["home"]] - side["rate"][g["away"]] + side["hfa"]
    return [{"market": "side", "side": "home" if pm > 0 else "away",
             "model_margin": pm,
             "p_win": model.norm_cdf(abs(pm) / _sd(side["residuals"]))
             if _sd(side["residuals"]) else ""}]


def sig_power_total(g, side, total):
    pt = total["rate"][g["home"]] + total["rate"][g["away"]] + total["intercept"]
    # no market total exists, so the "line" is the model's own league mean
    base = total["intercept"]
    return [{"market": "total", "side": "over" if pt > base else "under",
             "model_total": pt, "model_baseline": base,
             "p_win": model.norm_cdf(abs(pt - base) / _sd(total["residuals"]))
             if _sd(total["residuals"]) else ""}]


def _sd(xs):
    return model._sd(xs)


def sig_fade_public_dog(g, side, total):
    """Big road favourite: bet the away side when the model likes it a lot."""
    pm = side["rate"][g["home"]] - side["rate"][g["away"]] + side["hfa"]
    if -pm < 6.0:          # model must like the road team by 6+
        return []
    return [{"market": "side", "side": "away", "model_margin": -pm,
             "p_win": model.norm_cdf(-pm / _sd(side["residuals"]))
             if _sd(side["residuals"]) else ""}]


def sig_low_total(g, side, total):
    """Unders only: bet the under when the model total is far below league mean."""
    pt = total["rate"][g["home"]] + total["rate"][g["away"]] + total["intercept"]
    if pt >= total["intercept"] - 4.0:
        return []
    return [{"market": "total", "side": "under", "model_total": pt,
             "model_baseline": total["intercept"],
             "p_win": model.norm_cdf((total["intercept"] - pt) / _sd(total["residuals"]))
             if _sd(total["residuals"]) else ""}]


def sig_home_dog(g, side, total):
    pm = side["rate"][g["home"]] - side["rate"][g["away"]] + side["hfa"]
    if pm > -1.0:
        return []
    return [{"market": "side", "side": "home", "model_margin": pm,
             "p_win": model.norm_cdf(-pm / _sd(side["residuals"]))
             if _sd(side["residuals"]) else ""}]


def sig_injury_fade(g, side, total, depth_weight: Dict[str, float]):
    """Fade the team carrying the heavier depth-weighted injury load."""
    hw = depth_weight.get(g["home"], 0.0)
    aw = depth_weight.get(g["away"], 0.0)
    if abs(hw - aw) < 1.0:
        return []
    pm = side["rate"][g["home"]] - side["rate"][g["away"]] + side["hfa"]
    pmadj = pm - (hw - aw) * 1.5
    if (pmadj > 0) == (pm > 0) or pm == 0:
        return []
    return [{"market": "side", "side": "home" if pmadj > 0 else "away",
             "model_margin": pm, "adj_margin": pmadj,
             "home_depth_weight": hw, "away_depth_weight": aw,
             "p_win": model.norm_cdf(abs(pmadj) / _sd(side["residuals"]))
             if _sd(side["residuals"]) else ""}]


STRATEGIES: List[Dict[str, object]] = [
    {"strategy_id": "A9-S01", "name": "Baseline power rating - side",
     "family": "single bet", "signal": sig_power_side,
     "description": "Originate the side, take it whenever the fair margin is "
                    "non-zero. This is the control: if it has no edge, nothing "
                    "built on top of the ratings does either.",
     "registered_signal_rule": "side = sign(model margin)"},
    {"strategy_id": "A9-S02", "name": "Baseline power rating - total",
     "family": "single bet", "signal": sig_power_total,
     "description": "Originate the total, take over when the model total "
                    "exceeds the fitted league mean. Control for the totals "
                    "model.",
     "registered_signal_rule": "over if model total > league mean"},
    {"strategy_id": "A9-S03", "name": "Road favourite",
     "family": "single bet", "signal": sig_fade_public_dog,
     "description": "Only bet the away side, and only when the model favours "
                    "them by 6 or more.",
     "registered_signal_rule": "away side, model margin <= -6.0"},
    {"strategy_id": "A9-S04", "name": "Systematic under",
     "family": "single bet", "signal": sig_low_total,
     "description": "Only bet unders, and only when the model total is at "
                    "least 4 points below the fitted league mean.",
     "registered_signal_rule": "under, model total <= league mean - 4.0"},
    {"strategy_id": "A9-S05", "name": "Home underdog",
     "family": "single bet", "signal": sig_home_dog,
     "description": "Bet the home side only when the model makes them an "
                    "underdog of more than a point.",
     "registered_signal_rule": "home side, model margin < -1.0"},
    {"strategy_id": "A9-S06", "name": "Depth-of-replacement fade",
     "family": "single bet", "signal": sig_injury_fade,
     "description": "Adjust the model margin by the difference in "
                    "depth-weighted injury load and bet only when the "
                    "adjustment flips the side. Uses the PROPOSED depth "
                    "weights - not an observed quantity.",
     "registered_signal_rule": "sign flip after depth adjustment, |diff| >= 1.0"},
    {"strategy_id": "A9-S07", "name": "Same-game parlay: favourite + over",
     "family": "parlay", "signal": None,
     "description": "Two-leg parlay built from the side and the total when "
                    "both models agree on direction. Priced with the observed "
                    "margin/total residual correlation A4-C03, not with an "
                    "independent product.",
     "registered_signal_rule": "model margin > 3 and model total > league mean"},
    {"strategy_id": "A9-S08", "name": "Same-game parlay: dog + under",
     "family": "parlay", "signal": None,
     "description": "Mirror of A9-S07 on the other side of both markets.",
     "registered_signal_rule": "model margin < -3 and model total < league mean"},
    {"strategy_id": "A9-S09", "name": "Moneyline favourite",
     "family": "single bet", "signal": None,
     "description": "Step 3 of the origination order: bet the moneyline when "
                    "the derived win probability exceeds the -110 break-even "
                    "rate with margin.",
     "registered_signal_rule": "p_win >= 0.60"},
    {"strategy_id": "A9-S10", "name": "Player-prop combo placeholder",
     "family": "player prop combo", "signal": None,
     "description": "Registered but NOT built: no official NFL page publishes "
                    "player-prop lines or the usage data needed to price them. "
                    "Listed so the family is visible in the leaderboard and "
                    "its blocker is on the record.",
     "registered_signal_rule": "none - blocked"},
]

STAKING_PLANS = [
    {"staking_id": "flat-1u", "name": "Flat 1 unit",
     "description": "Every signal gets exactly one unit. This is the column "
                    "that measures the SIGNAL."},
    {"staking_id": "kelly-quarter", "name": "Quarter Kelly",
     "description": "Stake = 0.25 * (p*b - q) / b on the model's own "
                    "probability. Measures the signal AND the sizing."},
    {"staking_id": "martingale", "name": "Martingale 2x after a loss",
     "description": "Deliberately included as the cautionary case: it shows "
                    "how a staking plan can manufacture a good-looking P&L "
                    "from a losing signal, right up until it doesn't."},
]


# ------------------------------------------------------------------ backtests
def _walk_forward_signals(fn, games, depth_weight=None):
    weeks = sorted({g["week"] for g in games})
    out = []
    for k in weeks[:-1]:
        nxt = weeks[weeks.index(k) + 1]
        train = [g for g in games if g["week"] <= k]
        test = [g for g in games if g["week"] == nxt]
        if len(train) < 24:
            continue
        side, total = _fit(train)
        for g in test:
            sigs = fn(g, side, total) if depth_weight is None \
                else fn(g, side, total, depth_weight)
            for s in sigs:
                row = dict(s)
                row["game"] = g["game_slug"]
                row["week"] = g["week"]
                row["home"] = g["home"]
                row["away"] = g["away"]
                row["actual_margin"] = g["margin"]
                row["actual_total"] = g["total"]
                row["train_n"] = len(train)
                row["train_through_week"] = k
                won = _won(row)
                row["result"] = won
                out.append(row)
    return out


def _won(row):
    if row["market"] == "side":
        pick_home = row["side"] == "home"
        return 1 if ((row["actual_margin"] > 0) == pick_home) else (
            0 if row["actual_margin"] != 0 else 0)
    if row["market"] == "total":
        over = row["side"] == "over"
        return 1 if ((row["actual_total"] > row["model_baseline"]) == over) else 0
    return ""


def _brier(rows):
    scored = [r for r in rows if r.get("p_win") not in ("", None)]
    if not scored:
        return ""
    return round(sum((float(r["p_win"]) - r["result"]) ** 2 for r in scored)
                 / len(scored), 4)


def _logloss(rows):
    scored = [r for r in rows if r.get("p_win") not in ("", None)]
    if not scored:
        return ""
    tot = 0.0
    for r in scored:
        p = min(0.999, max(0.001, float(r["p_win"])))
        tot += -(r["result"] * math.log(p) + (1 - r["result"]) * math.log(1 - p))
    return round(tot / len(scored), 4)


def _calibration(rows):
    """Split into probability buckets and compare stated vs realised."""
    scored = [r for r in rows if r.get("p_win") not in ("", None)]
    if not scored:
        return []
    buckets = [(0.50, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 1.01)]
    out = []
    for lo, hi in buckets:
        b = [r for r in scored if lo <= float(r["p_win"]) < hi]
        if not b:
            continue
        out.append({"p_bucket": f"[{lo:.2f}, {hi:.2f})", "n": len(b),
                    "stated_p": round(sum(float(r["p_win"]) for r in b) / len(b), 4),
                    "realised": round(sum(r["result"] for r in b) / len(b), 4)})
    return out


def _staking(rows, plan):
    """Apply a staking plan to a signal stream.

    IMPORTANT: the resulting P&L is a **hypothetical**, because no price
    was ever captured.  It is reported at -110 for every bet purely so the
    signal and the staking can be compared on the same axis.  It is
    labelled ``hypothetical_no_price_captured`` everywhere.
    """
    if not rows:
        return {"units": "", "peak": "", "max_drawdown": "", "bets": 0}
    bank, peak, mdd = 0.0, 0.0, 0.0
    stake = 1.0
    for r in rows:
        if plan == "flat-1u":
            s = 1.0
        elif plan == "kelly-quarter":
            p = float(r["p_win"]) if r.get("p_win") not in ("", None) else 0.5
            b = 0.909  # -110 decimal minus 1
            s = max(0.0, 0.25 * (p * (b + 1) - 1) / b)
            s = min(s, 2.0)
        else:  # martingale
            s = stake
        if r["result"] == 1:
            bank += s * 0.909
            stake = 1.0
        else:
            bank -= s
            stake = stake * 2 if plan == "martingale" else 1.0
        peak = max(peak, bank)
        mdd = max(mdd, peak - bank)
    return {"units": round(bank, 2), "peak": round(peak, 2),
            "max_drawdown_units": round(mdd, 2), "bets": len(rows)}


def run_backtests() -> Dict[str, object]:
    from . import depth
    games = model._games()
    dw = {r["team_abbr"]: r["proposed_depth_weight_out_doubtful"]
          for r in depth.summarise(depth.build())}
    results = {}
    for st in STRATEGIES:
        fn = st["signal"]
        if fn is None:
            results[st["strategy_id"]] = []
            continue
        rows = _walk_forward_signals(fn, games,
                                     dw if st["strategy_id"] == "A9-S06" else None)
        results[st["strategy_id"]] = rows
    return results


def build_leaderboard() -> List[Dict[str, object]]:
    bt = run_backtests()
    out = []
    for st in STRATEGIES:
        rows = bt.get(st["strategy_id"], [])
        # A strategy with no signal function never produced a row, so its n
        # is "not evaluable" (blank), not zero.
        n = len(rows) if st["signal"] is not None else ""
        wins = sum(1 for r in rows if r["result"] == 1)
        row = {
            "strategy_id": st["strategy_id"],
            "strategy_name": st["name"],
            "family": st["family"],
            "signal_rule": st["registered_signal_rule"],
            "signal_n": n,
            "signal_direction_hit_rate": round(wins / n, 4) if n != "" else "",
            "signal_direction_definition": "share of out-of-sample games where "
                                           "the model's fair margin had the same "
                                           "sign as the verified final margin "
                                           "(i.e. picking the straight-up "
                                           "winner). This is NOT an "
                                           "against-the-spread record: no "
                                           "official spread was captured.",
            "nominal_break_even_rate_at_minus_110": BREAK_EVEN,
            "signal_brier": _brier(rows),
            "signal_log_loss": _logloss(rows),
            "signal_beats_nominal_break_even": ("yes" if wins / n > BREAK_EVEN
                                                else "no") if n != "" else "",
            "signal_verdict": ("unproven - direction hit only, no prices"
                               if n != "" else "not evaluable"),
            "signal_n_status": ("sufficient_n" if n >= 30 else "insufficient_n")
                               if n != "" else "not_evaluable",
            "staking_flat_1u_units": "",
            "staking_kelly_quarter_units": "",
            "staking_martingale_units": "",
            "staking_martingale_max_drawdown": "",
            "staking_note": "hypothetical_no_price_captured - computed at "
                            "-110 on every bet because no official price was "
                            "captured; NOT a track record",
            "status": "blocked_no_prices" if n == "" else "paper_only",
            "official_source_url": "https://www.nfl.com/scores/2026/week-1",
        }
        if n != "":
            for plan, key in (("flat-1u", "staking_flat_1u_units"),
                              ("kelly-quarter", "staking_kelly_quarter_units"),
                              ("martingale", "staking_martingale_units")):
                r = _staking(rows, plan)
                row[key] = r["units"]
                if plan == "martingale":
                    row["staking_martingale_max_drawdown"] = r["max_drawdown_units"]
                    row["staking_martingale_peak_units"] = r["peak"]
        out.append(row)
    # rank: signal column only
    ranked = sorted(out, key=lambda r: (r["signal_brier"] is None or r["signal_brier"] == "",
                                        r["signal_brier"] if r["signal_brier"] != "" else 9))
    for i, r in enumerate(ranked, 1):
        r["signal_rank"] = i
    return out


def build_calibration() -> List[Dict[str, object]]:
    bt = run_backtests()
    out = []
    for st in STRATEGIES:
        rows = bt.get(st["strategy_id"], [])
        for b in _calibration(rows):
            b = dict(b)
            b["strategy_id"] = st["strategy_id"]
            b["strategy_name"] = st["name"]
            b["official_source_url"] = "https://www.nfl.com/scores/2026/week-1"
            out.append(b)
    return out
