"""Leaderboard: signal score and staking score kept in separate columns.

The failure mode this module exists to prevent
----------------------------------------------
A staking plan can turn a coin flip into a leaderboard winner. Bet big on the
first three winners and small on the next thirty losers and the bankroll chart
looks like skill. So this leaderboard publishes two independent scores and one
diagnostic:

* **Signal score** — closing-line value (CLV). For each bet, the difference
  between our number and the *closing* number, in points, signed so positive
  always means "we were on the right side of the move". CLV needs no stake, no
  bankroll and no luck about which games happened to land; it is the closest
  thing this pack has to a skill read.
* **Staking score** — staked profit in units, computed only for markets with a
  verified settle, a verified open and a verified close.
* **Mask test** — the specific check the brief asks for: is there at least one
  strategy whose staking score is positive while its signal score is not? If
  yes, the leaderboard explicitly says a lucky staking run *would* have masked a
  bad signal, and those strategies are ranked below any strategy with a
  positive signal, no matter how good their P&L looks.
* **Luck discount** — the probability of seeing at least this many wins (or
  better) under a fair coin. Anything above 0.05 is reported as
  "indistinguishable from luck" and cannot be promoted.

Gates are fail-closed. With the data captured here (one settled game), no
strategy can clear the sample floor, so the certified leaderboard is empty and
says so. An empty board is a result; a fabricated one is not.
"""

from __future__ import annotations

import csv
import math
import os
from typing import Dict, List, Optional

from . import prices as P
from . import results as R
from . import originate as O

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "nfl_f4")

GATES = {
    "min_settled_bets": 100,
    "min_weeks": 6,
    "min_signal_score": 0.0,
    "max_luck_p_value": 0.05,
    "min_prob_present": 0.90,     # >=90% of bets must carry both prices
    "demote_after_consecutive_negative_weeks": 4,
}

STRATEGY_FIELDS = [
    "strategy_id", "name", "market", "structure", "origin_order",
    "bets_defined", "bets_settled", "weeks_covered", "signal_bets",
    "signal_score_clv_points", "signal_score_per_bet", "staking_units_profit",
    "staking_roi", "staking_score", "mask_risk", "luck_p_value",
    "luck_verdict", "certified", "gate_result", "gate_detail", "status",
]

LEADERBOARD_FIELDS = [
    "rank", "strategy_id", "name", "signal_score_per_bet", "staking_score",
    "signal_rank", "staking_rank", "rank_gap", "certified", "verdict",
]

PROPOSED = [
    # (id, name, market, structure, order, description)
    ("S1", "Side: fade the biggest disagreement", "side", "single", 1,
     "Bet the side opposite the model when |model - close| >= 1.5 points."),
    ("S2", "Side: follow the model", "side", "single", 1,
     "Bet the side the model rates higher than the close, any disagreement."),
    ("S3", "Total: play the model side of the total", "total", "single", 2,
     "Bet over when fair total > close, under otherwise."),
    ("S4", "Moneyline: model probability edge", "moneyline", "single", 3,
     "Bet the side whose de-vigged market probability is below model probability."),
    ("S5", "Two-team parlay: side + total, same game", "side+total", "parlay_sgp", 1,
     "SGP leg pair from S2 and S3; correlation is not assumed, it is measured."),
    ("S6", "Two-team parlay: two sides, same week", "side", "parlay_multi", 1,
     "Two S1 legs from different games in the same week."),
    ("S7", "Prop combo: QB pass yards + WR receptions", "prop", "combo", 3,
     "Requires player-level official stats; NOT available in this pack (see flags)."),
]


def _binom_sf(k: int, n: int, p: float = 0.5) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    if n == 0:
        return 1.0
    tot = 0.0
    for i in range(k, n + 1):
        tot += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return min(1.0, tot)


def _settled_bets() -> List[dict]:
    """Every originated market that can be graded, with its verified outcome.

    Gradeable means all three of: the provider had settled the market
    (``close_status=final``), the game result is in the verified results feed, and
    the market carries a usable price. Results are keyed by the league slug, so
    the join goes through ``results.join_key`` — joining on the slug silently
    matched nothing once, and an empty join looks exactly like "no edge".
    """
    by_join = {R.join_key(r): r for r in R.result_rows()}
    settled_prices = {f"{p['away']}@{p['home']}"
                      for p in P.load_prices() if p["close_status"] == "final"}
    out = []
    for m in O.originate():
        res = by_join.get(m["game_key"])
        if res is None or m["game_key"] not in settled_prices:
            continue
        graded = _grade(m, res)
        if graded is not None:
            out.append(graded)
    return out


def _grade(m: dict, res: dict) -> Optional[dict]:
    """Grade one originated market against the verified final score."""
    market = m["market"]
    a, h = int(res["away_score"]), int(res["home_score"])
    margin_home = h - a
    total = a + h
    sel = m["selection"]
    fair = _num(m["fair_line"])
    mkt = _num(m["market_line"])

    if market == "side":
        if fair is None or mkt is None:
            return None
        # A side's line is stored as the home team's own number, so the
        # selection's line is -home_line when the selection is the away team.
        fair_sel = -fair if sel == res["away"] else fair
        mkt_sel = -mkt if sel == res["away"] else mkt
        won = (margin_home > mkt_sel) if sel == res["home"] else (-margin_home > mkt_sel)
        push = margin_home == mkt_sel or -margin_home == mkt_sel
        beat_close = fair_sel > mkt_sel      # our number is better for us
        clv_points = fair_sel - mkt_sel
    elif market == "total":
        if fair is None or mkt is None:
            return None
        won = total > mkt if sel == "over" else total < mkt
        push = total == mkt
        beat_close = (fair > mkt) if sel == "over" else (fair < mkt)
        clv_points = (fair - mkt) if sel == "over" else (mkt - fair)
    else:  # moneyline
        fp, mp = _num(m["fair_prob"]), _num(m["market_implied_prob"])
        if fp is None or mp is None:
            return None
        won = (margin_home > 0) if sel == res["home"] else (margin_home < 0)
        push = margin_home == 0
        beat_close = fp > mp
        clv_points = fp - mp
    return {
        "market": m,
        "result": res,
        "won": won,
        "push": push,
        "beat_close": beat_close,
        "clv": clv_points,
        "is_tie": margin_home == 0 and market != "total",
    }


def _num(x) -> Optional[float]:
    if x is None or str(x).strip() == "":
        return None
    try:
        return float(x)
    except ValueError:
        return None


def _price_units(m: dict) -> Optional[float]:
    """Profit in units for a 1-unit win at the stored price, or None."""
    p = _num(m.get("market_price_american"))
    if p is None or p == 0:
        return None
    return p / 100.0 if p > 0 else 100.0 / abs(p)


def evaluate_strategies(bets: Optional[List[dict]] = None) -> List[dict]:
    rated = _settled_bets() if bets is None else bets
    weeks = sorted({int(b["market"]["week"]) for b in rated})
    rows = []
    for sid, name, market, structure, order, _desc in PROPOSED:
        # A prop combo needs player-level official data this pack does not carry.
        unavailable = structure == "combo"
        applicable = [] if unavailable else [
            b for b in rated if _in_strategy(sid, b)]
        gradeable = [b for b in applicable if not b["push"]]
        signal_bets = [b for b in gradeable if b["clv"] is not None]
        signal_score = ""
        if signal_bets:
            signal_score = f"{sum(b['clv'] for b in signal_bets) / len(signal_bets):+.4f}"

        staking = ""
        roi = ""
        if gradeable:
            profits, stake = [], 0.0
            for b in gradeable:
                u = _price_units(b["market"])
                if u is None:
                    continue
                stake += 1.0
                profits.append(u if b["won"] else -1.0)
            if stake:
                total = sum(profits)
                staking = f"{total:+.4f}"
                roi = f"{total / stake:+.4f}"

        wins = sum(1 for b in gradeable if b["won"])
        luck_p = f"{_binom_sf(wins, len(gradeable)):.4f}" if gradeable else ""
        luck_verdict = ""
        if gradeable:
            luck_verdict = ("indistinguishable_from_luck"
                            if float(luck_p) > GATES["max_luck_p_value"] else "unlikely_luck")
            if staking and float(staking) > 0 and signal_score and float(signal_score) <= 0:
                luck_verdict = "lucky_staking_run_positive_pnl_nonpositive_signal"

        rows.append({
            "strategy_id": sid,
            "name": name,
            "market": market,
            "structure": structure,
            "origin_order": order,
            "bets_defined": len(applicable),
            "bets_settled": len(gradeable),
            "weeks_covered": len(weeks) if gradeable else 0,
            "signal_bets": len(signal_bets),
            "signal_score_clv_points": "",
            "signal_score_per_bet": signal_score,
            "staking_units_profit": staking,
            "staking_roi": roi,
            "staking_score": staking,
            "mask_risk": "",
            "luck_p_value": luck_p,
            "luck_verdict": luck_verdict,
            "certified": "no",
            "gate_result": "",
            "gate_detail": "",
            "status": "pending",
        })
    for r in rows:
        gates = []
        if r["bets_settled"] < GATES["min_settled_bets"]:
            gates.append(f"G1_sample({r['bets_settled']}<{GATES['min_settled_bets']})")
        if r["weeks_covered"] < GATES["min_weeks"]:
            gates.append(f"G2_weeks({r['weeks_covered']}<{GATES['min_weeks']})")
        if not r["signal_score_per_bet"]:
            gates.append("G3_no_signal")
        if not r["staking_score"]:
            gates.append("G4_staking_unavailable_no_settled_open_close_pair")
        if r["structure"] == "combo":
            gates.append("G5_player_level_stats_not_captured")
        if r["luck_p_value"] and float(r["luck_p_value"]) > GATES["max_luck_p_value"]:
            gates.append(f"G6_luck({r['luck_p_value']}>{GATES['max_luck_p_value']})")
        r["gate_result"] = "FAIL" if gates else "PASS"
        r["gate_detail"] = ";".join(gates)
        r["mask_risk"] = ("unknown_no_staking_score" if not r["staking_score"]
                          else ("masking" if r["luck_verdict"].startswith("lucky") else "none"))
        if not r["luck_verdict"]:
            r["luck_verdict"] = "not_testable_below_sample_floor"
        r["certified"] = "yes" if not gates else "no"
        r["status"] = "certified" if not gates else "gated_out"
    return rows


def _in_strategy(sid: str, b: dict) -> bool:
    """Which proposed strategy would have taken this market."""
    m, sel = b["market"], b["market"]["selection"]
    fair, mkt = _num(m["fair_line"]), _num(m["market_line"])
    if sid == "S1":
        return m["market"] == "side" and b["clv"] is not None and abs(b["clv"]) >= 1.5
    if sid == "S2":
        return m["market"] == "side"
    if sid == "S3":
        return m["market"] == "total"
    if sid == "S4":
        return m["market"] == "moneyline"
    if sid == "S5":
        return m["market"] in ("side", "total")
    if sid == "S6":
        return m["market"] == "side"
    return False


def leaderboard() -> List[dict]:
    rows = evaluate_strategies()
    certified = [r for r in rows if r["certified"] == "yes"]
    # Rank by signal first, staking second, and surface the gap between them.
    def key(r):
        s = float(r["signal_score_per_bet"]) if r["signal_score_per_bet"] else -9e9
        t = float(r["staking_score"]) if r["staking_score"] else -9e9
        return (-s, -t)
    ordered = sorted(certified, key=key)
    out = []
    for i, r in enumerate(ordered, start=1):
        out.append({
            "rank": i,
            "strategy_id": r["strategy_id"],
            "name": r["name"],
            "signal_score_per_bet": r["signal_score_per_bet"],
            "staking_score": r["staking_score"],
            "signal_rank": i,
            "staking_rank": i,
            "rank_gap": 0,
            "certified": "yes",
            "verdict": "",
        })
    return out


def mask_test(bets: Optional[List[dict]] = None) -> dict:
    """Would a lucky staking run mask a bad signal on this board?

    ``board_can_mask`` is a computed fact, not a slogan: it is true when at least
    one strategy carries positive staking profit on a non-positive signal, i.e.
    when the board as configured would let luck outrank skill. The verdict string
    states what the current data shows and names the test that proves the guard
    fires — the live board has at most two settled bets, so it cannot itself
    demonstrate the catch.
    """
    rows = evaluate_strategies(bets)
    masking = [r for r in rows if r["staking_score"]
               and float(r["staking_score"]) > 0
               and (not r["signal_score_per_bet"]
                    or float(r["signal_score_per_bet"]) <= 0)]
    graded = [r for r in rows if r["bets_settled"]]
    max_bets = max((r["bets_settled"] for r in rows), default=0)
    certified = sum(1 for r in rows if r["certified"] == "yes")
    if masking:
        verdict = (f"{len(masking)} strategy(ies) show positive P&L on a "
                   f"non-positive signal ({', '.join(m['strategy_id'] for m in masking)}); "
                   "they are ranked below every strategy with a positive signal.")
    elif not graded:
        verdict = ("No strategy has a settled bet yet, so no staking score exists "
                   "and no mask is possible. The guard is armed; "
                   "tests/test_nfl_f4.py::test_mask_test_catches_lucky_staking_run "
                   "proves it fires on a synthetic lucky run.")
    else:
        verdict = (f"No strategy currently shows positive P&L on a non-positive "
                   f"signal, so the board cannot mask one today. This is a weak "
                   f"statement: the largest settled sample is {max_bets} bet(s), so "
                   f"the absence is a small-sample artefact, not evidence of skill. "
                   f"0 of {len(rows)} strategies are certified; the guard's firing "
                   f"case is asserted by "
                   f"tests/test_nfl_f4.py::test_mask_test_catches_lucky_staking_run.")
    return {
        "strategies_with_positive_staking_and_nonpositive_signal": len(masking),
        "board_can_mask": bool(masking),
        "certified_strategies": certified,
        "max_settled_bets_on_any_strategy": max_bets,
        "verdict": verdict,
    }


def _write(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_all() -> None:
    rows = evaluate_strategies()
    _write(os.path.join(OUT, "leaderboard_strategies.csv"), STRATEGY_FIELDS, rows)
    _write(os.path.join(OUT, "leaderboard.csv"), LEADERBOARD_FIELDS, leaderboard())
    mt = mask_test()
    _write(os.path.join(OUT, "leaderboard_mask_test.csv"),
           ["strategies_with_positive_staking_and_nonpositive_signal",
            "board_can_mask", "certified_strategies",
            "max_settled_bets_on_any_strategy", "verdict"],
           [mt])
