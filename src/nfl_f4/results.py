"""Verified results feed.

Every backtest in this repository needs exactly three things before it can say
anything: a verified final score, a verified market price, and a verified
market. This module produces the first, and it refuses to trust itself: each
team's wins, losses, ties, points-for and points-against are recomputed from the
game rows and compared against the official nfl.com standings read on the same
day. A single mismatch fails the build rather than shipping a quiet error.

Coverage note (deliberate): scores are captured for weeks 1-9 plus the one
Week 10 game that had been played when the data was read. Week 10's other
thirteen games kick off on 2026-11-15, after the capture date, so they are
absent — not zero, not projected.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "nfl_f4", "raw")
OUT = os.path.join(ROOT, "data", "nfl_f4")

RESULT_FIELDS = [
    "game_key", "join_key", "season", "week", "status", "away", "away_score", "home",
    "home_score", "winner", "margin", "total_points", "went_to_ot",
    "result_source_url", "read_date", "status_kind",
]

CHECK_FIELDS = [
    "abbr", "wins_recomputed", "losses_recomputed", "ties_recomputed",
    "pf_recomputed", "pa_recomputed", "wins_official", "losses_official",
    "ties_official", "pf_official", "pa_official", "games_recomputed",
    "wins_match", "losses_match", "ties_match", "pf_match", "pa_match",
    "result", "standings_source_url",
]


def load_finals() -> List[dict]:
    with open(os.path.join(RAW, "results_finals.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_standings() -> List[dict]:
    with open(os.path.join(RAW, "standings.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def join_key(row: dict) -> str:
    """Canonical ``AWAY@HOME`` key for joining results to prices.

    The published ``game_key`` is the provider/league slug
    (``2026-REG-10-was-at-nyg``), which is good for a stable identifier and bad
    for joining: the price store keys on ``AWAY@HOME``. Rather than rewrite the
    published slug, every consumer joins on this function. A silent failed join
    once cost this pack its entire set of gradeable bets, so the join now has one
    definition in one place.
    """
    return f"{row['away']}@{row['home']}"


def result_rows() -> List[dict]:
    rows = []
    for r in load_finals():
        a, h = int(r["away_score"]), int(r["home_score"])
        margin = h - a
        winner = r["home"] if margin > 0 else (r["away"] if margin < 0 else "TIE")
        # OT is not stated on the week pages that were read, so it is left blank
        # rather than guessed from a margin.
        rows.append({
            "game_key": r["game_key"],
            "join_key": f"{r['away']}@{r['home']}",
            "season": r["season"],
            "week": r["week"],
            "status": r["status"],
            "away": r["away"],
            "away_score": r["away_score"],
            "home": r["home"],
            "home_score": r["home_score"],
            "winner": winner,
            "margin": margin,
            "total_points": a + h,
            "went_to_ot": "",
            "result_source_url": r["source_url"],
            "read_date": r["read_date"],
            "status_kind": "verified",
        })
    return rows


def recompute_team_records(rows: List[dict]) -> Dict[str, dict]:
    agg: Dict[str, dict] = {}
    for r in rows:
        a, h = int(r["away_score"]), int(r["home_score"])
        for team, pf, pa in ((r["away"], a, h), (r["home"], h, a)):
            d = agg.setdefault(team, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "g": 0})
            d["g"] += 1
            d["pf"] += pf
            d["pa"] += pa
            if pf > pa:
                d["w"] += 1
            elif pf < pa:
                d["l"] += 1
            else:
                d["t"] += 1
    return agg


def reconciliation_rows() -> List[dict]:
    rows = result_rows()
    agg = recompute_team_records(rows)
    official = {s["abbr"]: s for s in load_standings()}
    teams = sorted(set(agg) | set(official))
    out = []
    for t in teams:
        g = agg.get(t, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "g": 0})
        o = official.get(t)
        if o is None:
            out.append({"abbr": t, "result": "NO_OFFICIAL_ROW"})
            continue
        checks = {
            "wins": g["w"] == int(o["w"]),
            "losses": g["l"] == int(o["l"]),
            "ties": g["t"] == int(o["t"]),
            "pf": g["pf"] == int(o["pf"]),
            "pa": g["pa"] == int(o["pa"]),
        }
        ok = all(checks.values())
        out.append({
            "abbr": t,
            "wins_recomputed": g["w"], "losses_recomputed": g["l"],
            "ties_recomputed": g["t"], "pf_recomputed": g["pf"],
            "pa_recomputed": g["pa"],
            "wins_official": o["w"], "losses_official": o["l"],
            "ties_official": o["t"], "pf_official": o["pf"], "pa_official": o["pa"],
            "games_recomputed": g["g"],
            "wins_match": "yes" if checks["wins"] else "NO",
            "losses_match": "yes" if checks["losses"] else "NO",
            "ties_match": "yes" if checks["ties"] else "NO",
            "pf_match": "yes" if checks["pf"] else "NO",
            "pa_match": "yes" if checks["pa"] else "NO",
            "result": "MATCH" if ok else "MISMATCH",
            "standings_source_url": o["source_url"],
        })
    return out


def reconcile_or_raise() -> List[dict]:
    rows = reconciliation_rows()
    bad = [r for r in rows if r.get("result") != "MATCH"]
    if bad:
        raise SystemExit(
            "results feed failed official reconciliation: "
            + ", ".join(f"{r['abbr']}={r['result']}" for r in bad)
        )
    return rows


def coverage() -> dict:
    rows = result_rows()
    weeks = sorted({int(r["week"]) for r in rows})
    return {
        "games": len(rows),
        "weeks": weeks,
        "teams": len({r["away"] for r in rows} | {r["home"] for r in rows}),
        "last_played_week": max(weeks),
        "note": ("Week 10 contains only the game played before the capture date; the "
                 "remaining Week 10 games had not kicked off."),
    }


def _write(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_all() -> None:
    rows = result_rows()
    _write(os.path.join(OUT, "results.csv"), RESULT_FIELDS, rows)
    _write(os.path.join(OUT, "results_reconciliation.csv"), CHECK_FIELDS,
           reconcile_or_raise())
