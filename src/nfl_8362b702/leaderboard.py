"""Proper-score leaderboard with divisions, and the joint-evidence gate.

Divisions: singles / game_parlays / same_game_parlays / prop_combos.
Ranking statistic: Brier skill versus each event's own base rate, with a
game-cluster lower bound and a multiplicity note. At registration time no
forecast in the evaluation window is settled, so every proper-score cell is
blank with the gate that will fill it. Backtest numbers never appear here —
they are published on their own page by the builder.
"""
from __future__ import annotations

from .prereg import GATES, STRATEGY_SPECS

DIVISIONS = ["singles", "game_parlays", "same_game_parlays", "prop_combos"]


def division_rows():
    out = []
    for d in DIVISIONS:
        eligible = d == "singles"
        out.append({
            "division": d,
            "eligible_for_ranking": "yes" if eligible else "no",
            "joint_evidence_gate": "G-JOINT" if d != "singles" else "not applicable (single leg)",
            "n_registered_strategies": sum(1 for s in STRATEGY_SPECS if s["division"] == d),
            "n_settled": 0,
            "brier_skill": "", "brier_skill_lower_bound": "",
            "blank_reason": "" if not eligible else
                "no settled forecast yet (G-SETTLE: week-11 finals not published at "
                "registration; n_settled = 0)",
            "blocked_reason": "" if eligible else
                ("no validated joint probability and no operator void/push rules on file "
                 "(G-JOINT); multiplying marginals is invalid under dependence"),
        })
    return out


def strategy_rows():
    out = []
    for s in STRATEGY_SPECS:
        eligible = s["division"] == "singles"
        out.append({
            "strategy_id": s["strategy_id"], "division": s["division"],
            "registered": "yes", "registered_before_kickoff": s["frozen_before_kickoff"],
            "leaderboard_eligible": "yes" if eligible else "no",
            "n_forecasts_registered": 13 if s["division"] == "singles" else 0,
            "n_settled": 0,
            "brier": "", "brier_skill_vs_base": "", "cluster_lower_bound": "",
            "rank": "" ,
            "blank_or_blocked_reason": (
                "proper scores publish only after official finals settle the window (G-SETTLE)"
                if eligible else
                "division blocked at G-JOINT (combo) or G-PRICE (prop prices); "
                "no ranking exists for a division that cannot be scored"),
            "backtest_numbers_on_this_row": "none (G-BACKTEST forbids them)",
        })
    return out


def gate_rows():
    return [{"gate_id": g["gate_id"], "rule": g["rule"], "threshold": g["threshold"],
             "closes_if": g["closes_if"]} for g in GATES]
