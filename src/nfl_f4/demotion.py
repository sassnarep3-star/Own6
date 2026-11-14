"""Demotion gate: the conditions that send a live strategy back to paper.

A promotion gate without a demotion gate is a ratchet. A strategy that passed a
backtest once and then stopped working keeps its live status forever, because
nothing in the process is allowed to take it away. So this module defines the
return path explicitly, in advance, with numeric thresholds that a third party
can check without asking us anything.

Lifecycle
---------
    proposed --promotion gate--> paper --live-readiness gate--> live
    live --demotion gate--> paper --demotion gate repeats--> retired

Rules (all fail-closed: missing data counts against the strategy)
----------------------------------------------------------------
D1 Signal decay          trailing signal score (CLV per bet) <= 0 over the
                         lookback, with at least MIN_BETS_LOOKBACK settled bets.
D2 Drawdown              trailing staking drawdown from peak > MAX_DRAWDOWN units.
D3 Negative run          >= RUN_WEEKS consecutive weeks with negative signal,
                         even if the cumulative score is still positive.
D4 Divergence            staking ROI positive while signal <= 0 over the same
                         window (a lucky run) — demote; this is the mirror image
                         of the leaderboard mask test.
D5 Unverifiable          any live bet lacks a verified open, a verified close, or
                         a verified result. Live status requires gradeable bets.
D6 Model drift           the deployed model's declared parameters changed without
                         a new version id and a new validation run.

A demotion is sticky: it cannot be reversed by a single good week. Re-promotion
requires RE_ENTRY_MIN_BETS new settled bets *and* a positive signal score over
that fresh window. Every state change is written to a state file with a reason
code so the audit trail is the data.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional

from . import leaderboard as L

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "data", "nfl_f4")

THRESHOLDS = {
    "MIN_BETS_LOOKBACK": 40,
    "MAX_DRAWDOWN_UNITS": 8.0,
    "RUN_WEEKS": 3,
    "RE_ENTRY_MIN_BETS": 40,
    "STALE_DATA_HOURS": 36,
}

RULES = [
    ("D1", "signal_decay",
     "Trailing CLV-per-bet <= 0 with at least MIN_BETS_LOOKBACK settled bets."),
    ("D2", "staking_drawdown",
     "Trailing staking drawdown from peak exceeds MAX_DRAWDOWN_UNITS."),
    ("D3", "negative_week_run",
     "RUN_WEEKS or more consecutive weeks with a negative signal score."),
    ("D4", "luck_divergence",
     "Staking ROI positive while signal score <= 0 over the same window."),
    ("D5", "unverifiable",
     "Any live bet lacks a verified open, close, or result."),
    ("D6", "model_drift",
     "Declared model parameters changed without a new version id and validation run."),
]

GATE_FIELDS = ["rule_id", "rule_name", "threshold", "condition_text",
               "checked_against", "result", "evidence", "action_if_triggered"]

STATE_FIELDS = ["strategy_id", "name", "current_state", "target_state",
                "reason_code", "reason_text", "bets_settled", "signal_score_per_bet",
                "staking_score", "sticky", "re_entry_condition", "effective_from",
                "status"]


def _threshold_text(rule_id: str) -> str:
    if rule_id == "D1":
        return f"signal <= 0.0 over last {THRESHOLDS['MIN_BETS_LOOKBACK']} settled bets"
    if rule_id == "D2":
        return f"drawdown > {THRESHOLDS['MAX_DRAWDOWN_UNITS']} units"
    if rule_id == "D3":
        return f">= {THRESHOLDS['RUN_WEEKS']} consecutive negative weeks"
    if rule_id == "D4":
        return "staking ROI > 0 AND signal <= 0"
    if rule_id == "D5":
        return "any ungradeable live bet"
    return "parameter hash changed without version bump"


def gate_rows() -> List[dict]:
    strategies = L.evaluate_strategies()
    live_like = [s for s in strategies if s["certified"] == "yes"]
    rows = []
    for rid, name, text in RULES:
        can_evaluate = bool(live_like)
        rows.append({
            "rule_id": rid,
            "rule_name": name,
            "threshold": _threshold_text(rid),
            "condition_text": text,
            "checked_against": ("strategy state file" if can_evaluate
                                else "no strategy is live, so no state to demote"),
            "result": "not_triggered" if not can_evaluate else "evaluated",
            "evidence": (f"0 of {len(strategies)} proposed strategies certified; "
                         "all are gated out at the sample floor."
                         if not can_evaluate else ""),
            "action_if_triggered": "live -> paper; state change logged with reason code",
        })
    return rows


def state_rows() -> List[dict]:
    rows = []
    for s in L.evaluate_strategies():
        rows.append({
            "strategy_id": s["strategy_id"],
            "name": s["name"],
            "current_state": "proposed",
            "target_state": "paper",
            "reason_code": "GATES_OPEN",
            "reason_text": s["gate_detail"],
            "bets_settled": s["bets_settled"],
            "signal_score_per_bet": s["signal_score_per_bet"],
            "staking_score": s["staking_score"],
            "sticky": "n/a_not_live",
            "re_entry_condition": (f">= {THRESHOLDS['RE_ENTRY_MIN_BETS']} new settled "
                                   "bets with positive signal score"),
            "effective_from": "2026-11-14",
            "status": "not_live",
        })
    return rows


def apply(bets_settled: int, signal_per_bet: float, drawdown_units: float,
          consecutive_negative_weeks: int, staking_roi: float,
          ungradeable_bets: int, params_changed: bool) -> List[str]:
    """Pure decision function used by the tests and by any future runner.

    Returns the list of triggered rule ids; an empty list means "keep live".
    """
    hit = []
    if bets_settled >= THRESHOLDS["MIN_BETS_LOOKBACK"] and signal_per_bet <= 0:
        hit.append("D1")
    if drawdown_units > THRESHOLDS["MAX_DRAWDOWN_UNITS"]:
        hit.append("D2")
    if consecutive_negative_weeks >= THRESHOLDS["RUN_WEEKS"]:
        hit.append("D3")
    if staking_roi > 0 and signal_per_bet <= 0:
        hit.append("D4")
    if ungradeable_bets > 0:
        hit.append("D5")
    if params_changed:
        hit.append("D6")
    return hit


def _write(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_all() -> None:
    _write(os.path.join(OUT, "demotion_gate.csv"), GATE_FIELDS, gate_rows())
    _write(os.path.join(OUT, "strategy_state.csv"), STATE_FIELDS, state_rows())
