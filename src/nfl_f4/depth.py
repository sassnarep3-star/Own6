"""Replacement depth: not "someone was replaced" but "who, from which string".

The distinction that matters for a price
---------------------------------------
"Starting left guard is out" is worth roughly nothing on its own. "Starting left
guard is out and the replacement is the club's own third-string guard, who was
listed behind a player who is also out" is worth something. So every slot in
this module resolves to a *chain*:

    slot -> first string -> is he available? -> if not, who is the next listed
    player the club itself still lists as available -> what string is HE?

Two deliberate refusals:

1. **Depth charts are unofficial.** Both clubs say so in their own words, and
   that exact text is carried on every row. A depth row is therefore
   ``status=verified_unofficial_source``, never ``verified``.
2. **A missing designation is not health.** If the official injury report does
   not mention a player, the row says ``not_designated``, not ``healthy``. The
   report lists participation, not fitness, and clubs routinely list only the
   players they must.

Only clubs whose depth chart was actually read are populated. Every other club
is absent rather than inferred from a roster, because a roster sorted by jersey
number is not a depth chart.
"""

from __future__ import annotations

import csv
import os
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "nfl_f4", "raw")
OUT = os.path.join(ROOT, "data", "nfl_f4")

INJURY_URL = "https://www.nfl.com/injuries/"

CHART_FIELDS = [
    "team", "unit", "slot", "string", "player", "injury_report_status",
    "practice_status", "game_status", "club_caveat_text", "source_url",
    "injury_source_url", "status",
]

REPLACEMENT_FIELDS = [
    "replacement_id", "team", "unit", "slot", "first_string",
    "first_string_game_status", "effectively_available_first",
    "replacement_player", "replacement_string", "replacement_game_status",
    "strings_demoted", "chain_note", "deficiency_points",
    "contingency_trigger", "contingency_player", "contingency_string",
    "contingency_game_status", "contingency_points", "worst_case_points",
    "score_kind", "depth_source_url", "injury_source_url", "status",
]

# DECLARED, not observed. Each weight is a flag (F4-F10). They are monotone in
# the string number only, and the 4th-string weight is deliberately the same as
# the 3rd: below third string the club is out of its own plan and the marginal
# information is small.
DEFICIENCY_WEIGHTS = {
    1: 0.00,
    2: 0.35,
    3: 0.70,
    4: 0.70,
}
UNAVAILABLE_STATUSES = {"Out", "Doubtful"}


def load_depth() -> List[dict]:
    with open(os.path.join(RAW, "depth_charts.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_injuries() -> List[dict]:
    with open(os.path.join(RAW, "injuries.csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _norm(name: str) -> str:
    """Normalise a player name for joining. Handles the 'III'/'Jr.' suffixes that
    differ between the club chart and the NFL injury report."""
    n = name.lower().replace(".", "").replace("'", "").strip()
    for suffix in (" iii", " ii", " jr", " sr", " iv"):
        if n.endswith(suffix):
            n = n[: -len(suffix)]
    return n


def injury_index() -> Dict[str, dict]:
    idx = {}
    for r in load_injuries():
        idx.setdefault(_norm(r["player"]), r)
    return idx


def chart_rows() -> List[dict]:
    inj = injury_index()
    rows = []
    for r in load_depth():
        i = inj.get(_norm(r["player"]))
        rows.append({
            "team": r["team"],
            "unit": r["unit"],
            "slot": r["slot"],
            "string": r["string"],
            "player": r["player"],
            "injury_report_status": "listed" if i else "not_designated",
            "practice_status": i["practice_status"] if i else "",
            "game_status": i["game_status"] if i else "",
            "club_caveat_text": r["club_caveat_text"],
            "source_url": r["source_url"],
            "injury_source_url": INJURY_URL,
            "status": "verified_unofficial_source",
        })
    return rows


def _status(player_norm: str, inj: Dict[str, dict]) -> str:
    i = inj.get(player_norm)
    if not i:
        return "not_designated"
    return i["game_status"] or "no_game_status"


def _available(player_norm: str, inj: Dict[str, dict]) -> bool:
    i = inj.get(player_norm)
    if not i:
        return True  # not designated -> available by default, and said so
    return (i["game_status"] or "") not in UNAVAILABLE_STATUSES


def replacement_rows() -> List[dict]:
    inj = injury_index()
    by_slot: Dict[tuple, List[dict]] = {}
    for r in load_depth():
        by_slot.setdefault((r["team"], r["unit"], r["slot"]), []).append(r)
    rows = []
    for (team, unit, slot), players in sorted(by_slot.items()):
        players.sort(key=lambda x: int(x["string"]))
        norm = {p["player"]: _norm(p["player"]) for p in players}
        first = players[0]
        # Walk down the club's own list until a player is not ruled out.
        replacement = None
        for p in players[1:]:
            if _available(norm[p["player"]], inj):
                replacement = p
                break
        first_available = _available(norm[first["player"]], inj)
        if replacement is None:
            rep_name = ""
            rep_string = ""
            rep_status = ""
            demoted = len(players) - 1
            note = ("No listed backup is available; the slot resolves to nobody on "
                    "the club's own chart.") if len(players) > 1 else (
                    "Club lists no backup at this slot.")
        else:
            rep_name = replacement["player"]
            rep_string = replacement["string"]
            rep_status = _status(norm[replacement["player"]], inj)
            demoted = int(replacement["string"]) - 1
            skipped = [x["player"] for x in players[1:int(replacement["string"])]]
            note = ("Direct backup starts." if demoted == 1 else
                    "Skipped " + ", ".join(
                        f"{nm} ({_status(norm[nm], inj)})" for nm in skipped) + ".")
        weight = DEFICIENCY_WEIGHTS.get(int(rep_string), 0.0) if rep_string else 0.0
        if first_available:
            weight = 0.0
            note = ("First string is not ruled out; the replacement exists but is "
                    "not forced.")

        # Contingency: if the first string is merely QUESTIONABLE (not ruled out),
        # the plan that actually matters is who plays when he cannot. This is the
        # difference between "a backup exists" and "the third string is one
        # scratch away", and it is the case a one-week injury report hides.
        first_status = _status(norm[first["player"]], inj)
        contingency_player = contingency_string = contingency_status = ""
        contingency_trigger = ""
        contingency_points = 0.0
        if first_status == "Questionable":
            contingency_trigger = "first_string_questionable"
            for p in players[1:]:
                if _available(norm[p["player"]], inj):
                    contingency_player = p["player"]
                    contingency_string = p["string"]
                    contingency_status = _status(norm[p["player"]], inj)
                    contingency_points = DEFICIENCY_WEIGHTS.get(int(p["string"]), 0.0)
                    break
        worst = max(weight, contingency_points)
        rows.append({
            "replacement_id": f"R-{team}-{unit[:3].upper()}-{slot}",
            "team": team,
            "unit": unit,
            "slot": slot,
            "first_string": first["player"],
            "first_string_game_status": _status(norm[first["player"]], inj),
            "effectively_available_first": "yes" if first_available else "no",
            "replacement_player": rep_name,
            "replacement_string": rep_string,
            "replacement_game_status": rep_status,
            "strings_demoted": demoted,
            "chain_note": note,
            "deficiency_points": f"{weight:.2f}",
            "contingency_trigger": contingency_trigger,
            "contingency_player": contingency_player,
            "contingency_string": contingency_string,
            "contingency_game_status": contingency_status,
            "contingency_points": f"{contingency_points:.2f}" if contingency_player else "",
            "worst_case_points": f"{worst:.2f}",
            "score_kind": "proposed_weight_not_observed",
            "depth_source_url": players[0]["source_url"],
            "injury_source_url": INJURY_URL,
            "status": "derived_from_unofficial_depth_plus_official_injury_report",
        })
    return rows


def unit_summary() -> List[dict]:
    """Per team/unit replacement burden, split offence vs defence as required."""
    rows = replacement_rows()
    out = []
    for team in sorted({r["team"] for r in rows}):
        for unit in ("Offense", "Defense"):
            sel = [r for r in rows if r["team"] == team and r["unit"] == unit]
            forced = [r for r in sel if r["effectively_available_first"] == "no"]
            deep = [r for r in forced if r["replacement_string"] and int(r["replacement_string"]) >= 3]
            out.append({
                "team": team,
                "unit": unit,
                "slots_listed": len(sel),
                "starters_ruled_out": len(forced),
                "replacement_from_3rd_string_or_worse": len(deep),
                "deficiency_points_total": f"{sum(float(r['deficiency_points']) for r in sel):.2f}",
                "contingency_slots_3rd_string_or_worse": sum(
                    1 for r in sel if r["contingency_string"]
                    and int(r["contingency_string"]) >= 3),
                "worst_case_points_total": f"{sum(float(r['worst_case_points']) for r in sel):.2f}",
                "score_kind": "proposed_weight_not_observed",
            })
    return out


def _write(path, fields, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def write_all() -> None:
    _write(os.path.join(OUT, "depth_chart_verified.csv"), CHART_FIELDS, chart_rows())
    _write(os.path.join(OUT, "depth_replacement.csv"), REPLACEMENT_FIELDS, replacement_rows())
    _write(os.path.join(OUT, "depth_unit_summary.csv"),
           ["team", "unit", "slots_listed", "starters_ruled_out",
            "replacement_from_3rd_string_or_worse", "deficiency_points_total",
            "contingency_slots_3rd_string_or_worse", "worst_case_points_total",
            "score_kind"], unit_summary())
