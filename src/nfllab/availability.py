"""Injury / availability modelling.

Two separate questions are kept separate on purpose:

  1. *Availability confirmation* — what the official Week 10 injury report states
     today (Out / Doubtful / Questionable, and practice participation). Only values
     that literally appear on https://www.nfl.com/injuries/ are published.

  2. *Depth deficiency* — if the listed starter at a position is out or limited,
     who is next on the club's published depth chart, and how many strings deep is
     the replacement? No snap share, PFF grade, or "expected points lost" value is
     invented: those numbers are blank/unverified until a licensed feed exists.

The module therefore emits (a) a fully sourced starter/backup board for clubs whose
official depth chart and official injury report were both read this session, and
(b) a parameterised deficiency score whose parameters are published with their
uncertainty so a reviewer can change them and see the decision change.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass

# Position groups that carry the largest published evidence of scoring impact.
# The ordering is a modelling choice, stated here, not a measured fact.
POSITION_WEIGHT = {
    "QB": 1.00, "LT": 0.45, "RT": 0.35, "C": 0.30, "LG": 0.25, "RG": 0.25,
    "WR": 0.35, "TE": 0.25, "RB": 0.30, "FB": 0.05,
    "EDGE": 0.40, "DE": 0.40, "DL": 0.30, "DT": 0.30, "NT": 0.30,
    "LB": 0.30, "MLB": 0.30, "WLB": 0.28, "SAM": 0.25, "OLB": 0.32,
    "CB": 0.40, "NB": 0.30, "S": 0.32, "SS": 0.30, "FS": 0.30, "RUSH": 0.35,
    "K": 0.20, "P": 0.10, "H": 0.05, "LS": 0.05, "PR": 0.05, "KR": 0.05,
}
STRING_PENALTY = {1: 0.0, 2: 0.35, 3: 0.62, 4: 0.80}   # replacement cost by string
PRACTICE_RISK = {"Did Not Participate In Practice": 0.65,
                 "Limited Participation in Practice": 0.30,
                 "Full Participation in Practice": 0.05,
                 "": 0.10}
STATUS_CERTAINTY = {"Out": 1.0, "Doubtful": 0.75, "Questionable": 0.45, "": 0.0}


@dataclass
class Available:
    team: str
    player: str
    position: str
    game: str
    game_status: str
    practice_status: str
    report_injury: str
    source_url: str


def load_injuries(path) -> list[Available]:
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append(Available(team=r["team"], player=r["player"], position=r["position"], game=r["game"],
                                 game_status=r["game_status"], practice_status=r["practice_status"],
                                 report_injury=r["report_injury"], source_url=r["source_url"]))
    return out


def load_depth(path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def depth_deficiency(injuries: list[Available], depth: list[dict], team: str) -> list[dict]:
    """For one club: which listed starters are compromised, and who replaces them."""
    rows = []
    by_slot: dict[tuple[str, str], list[dict]] = {}
    for d in depth:
        if d["team"] != team:
            continue
        by_slot.setdefault((d["unit"], d["position_slot"]), []).append(d)
    injured = {i.player: i for i in injuries if i.team == team}
    for (unit, slot), players in sorted(by_slot.items()):
        players = sorted(players, key=lambda x: int(x["string"]))
        starter = players[0]["player"]
        inj = injured.get(starter)
        if not inj:
            continue
        nxt = next((p for p in players[1:] if p["player"]), None)
        worse_than_one = int(nxt["string"]) if nxt else None
        penalty = STRING_PENALTY.get(worse_than_one, 1.0) if worse_than_one else 1.0
        weight = POSITION_WEIGHT.get(slot, 0.15)
        risk = max(STATUS_CERTAINTY.get(inj.game_status, 0.0),
                   PRACTICE_RISK.get(inj.practice_status, 0.1) * 0.5)
        rows.append({
            "team": team, "unit": unit, "position_slot": slot, "starter": starter,
            "starter_status": inj.game_status, "practice_status": inj.practice_status,
            "injury": inj.report_injury,
            "replacement": nxt["player"] if nxt else "",
            "replacement_string": worse_than_one if worse_than_one else "",
            "depth_gap": "" if worse_than_one is None else worse_than_one - 1,
            "position_weight": weight,
            "deficiency_index": round(weight * penalty * risk, 4),
            "source_injury": inj.source_url,
            "source_depth": players[0]["source_url"],
        })
    return rows


def team_deficiency(rows: list[dict]) -> float:
    """Sum of position deficiencies, capped at 1.0 so one club cannot dominate."""
    return min(1.0, sum(float(r["deficiency_index"]) for r in rows))


def spread_adjustment(index: float, points_per_unit: float = 3.0, cap: float = 3.0) -> float:
    """Points of spread moved toward that club's opponent for a given index.

    `points_per_unit` is an assumption to be estimated later, not a measured value.
    """
    return -min(cap, points_per_unit * index)
