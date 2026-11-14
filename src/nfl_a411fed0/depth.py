"""Injury / depth-of-replacement tracking.

The requirement is not "who is injured" but **the depth of the
replacement**: a 4th-string guard starting is a different number from a
2nd-string guard starting, and both are different from no replacement
being listed at all.

Pipeline
--------
1. Read the official Week 10 injury report (nfl.com/injuries) -> the set
   of players with a game status.
2. Read the official club depth chart (``<club>.com/team/depth-chart``)
   -> the ordered strings at each position slot.
3. Join on player name: the string index tells you how deep the club had
   to reach.  A player who is Out and appears as a first string means a
   second string is starting (depth 2).  If the depth chart is not
   readable, ``replacement_string`` stays blank and the row is flagged.

Nothing is inferred: if a player is not on a readable depth chart, the
replacement depth is recorded as unresolved.
"""
from __future__ import annotations

import csv
import re
from typing import Dict, List, Optional

from . import dataset

INJ_URL = "https://www.nfl.com/injuries/"

#: How much a starter-down event is worth at each replacement depth.  This
#: is a PROPOSED weight, not an observed quantity - it is labelled as such
#: everywhere it is published and it is not used to price anything.
PROPOSED_DEPTH_WEIGHT = {1: 1.00, 2: 0.60, 3: 0.30, 4: 0.15}


def _norm(name: str) -> str:
    n = name.lower()
    n = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b\.?", "", n)
    n = re.sub(r"[^a-z ]", " ", n)
    return " ".join(n.split())


def _suffix(name: str) -> str:
    m = re.search(r"\b(jr|sr|ii|iii|iv)\b\.?", name.lower())
    return m.group(1) if m else ""


def _same(a: str, b: str) -> bool:
    """Names match if core names are equal and suffixes are compatible."""
    na, nb = _norm(a), _norm(b)
    if na != nb:
        return False
    sa, sb = _suffix(a), _suffix(b)
    return sa == sb or not sa or not sb


def _unit_of(position: str) -> str:
    p = (position or "").upper()
    if p in ("DE", "DT", "LB", "CB", "S", "NT", "OLB", "ILB", "DB", "DL"):
        return "defense"
    if p in ("QB", "RB", "WR", "TE", "OL", "OT", "OG", "C", "G", "T", "FB"):
        return "offense"
    if p in ("K", "P", "LS"):
        return "special teams"
    return "unknown"


def _slot_index(chart: List[Dict[str, str]], unit: str, position: str,
                player: str) -> Optional[int]:
    """Return 1..4 = the string on which ``player`` appears, else None."""
    want_unit = _unit_of(position)
    cands = []
    for row in chart:
        if want_unit != "unknown" and want_unit != "defense" and \
           row["unit"].lower().startswith("defense") and want_unit == "offense":
            continue
        for s in range(2, 6):
            key = ["", "", "first_string", "second_string", "third_string",
                   "fourth_string"][s]
            if _same(row.get(key, ""), player):
                cands.append((s, row["position_slot"]))
    if not cands:
        return None
    # prefer the slot that looks like the injured player's position group
    pkey = (position or "").upper()
    for s, slot in cands:
        if pkey and pkey in slot.upper().replace(" ", ""):
            return s
    return min(cands)[0]


def build() -> List[Dict[str, object]]:
    charts: Dict[str, List[Dict[str, str]]] = {}
    labels: Dict[str, str] = {}
    urls: Dict[str, str] = {}
    for row in dataset.depth_charts():
        t = row["team_abbr"]
        charts.setdefault(t, []).append(row)
        labels.setdefault(t, row.get("chart_label_verbatim", ""))
        urls.setdefault(t, row.get("official_source_url", ""))

    out: List[Dict[str, object]] = []
    for r in dataset.injuries():
        team = r["team_abbr"]
        player = r["player"]
        pos = r["position"]
        if team not in charts:
            out.append({
                "team_abbr": team, "player": player, "position": pos,
                "unit": _unit_of(pos), "injury": r["injury"],
                "practice_status": r["practice_status"],
                "game_status": r["game_status"],
                "roster_string": "", "replacement_string": "",
                "replacement_player": "", "replacement_depth": "",
                "status": "unresolved_depth_chart_not_read",
                "official_injury_url": INJ_URL,
                "official_depth_chart_url": "",
            })
            continue
        chart = charts[team]
        s = _slot_index(chart, _unit_of(pos), pos, player)
        if s is None:
            # not listed on the chart at all - cannot name a replacement
            out.append({
                "team_abbr": team, "player": player, "position": pos,
                "unit": _unit_of(pos), "injury": r["injury"],
                "practice_status": r["practice_status"],
                "game_status": r["game_status"],
                "roster_string": "", "replacement_string": "",
                "replacement_player": "", "replacement_depth": "",
                "status": "unresolved_player_not_on_depth_chart",
                "official_injury_url": INJ_URL,
                "official_depth_chart_url": urls.get(team, ""),
            })
            continue
        nxt = s + 1
        slot = ""
        for row in chart:
            for ss in range(2, 6):
                k2 = ["", "", "first_string", "second_string", "third_string",
                      "fourth_string"][ss]
                if _same(row.get(k2, ""), player):
                    slot = row["position_slot"]
                    break
            if slot:
                break
        if nxt > 4:
            # The injured player is already the deepest string the club lists,
            # so the club must go beyond its published chart. We know that
            # much and nothing more: name and depth both stay blank.
            rep = ""
            status = "unresolved_beyond_listed_strings"
            rep_string = ""
            rep_depth = ""
        else:
            key = ["", "", "first_string", "second_string", "third_string",
                   "fourth_string"][nxt]
            rep_row = next((row for row in chart
                            if row["position_slot"] == slot), None)
            rep = rep_row.get(key, "") if rep_row else ""
            if rep and _same(rep, player):
                rep = ""
            status = ("resolved" if rep
                      else "partial_string_known_player_not_listed")
            rep_string = nxt
            rep_depth = nxt
        out.append({
            "team_abbr": team, "player": player, "position": pos,
            "unit": _unit_of(pos), "position_slot": slot,
            "injury": r["injury"], "practice_status": r["practice_status"],
            "game_status": r["game_status"],
            "roster_string": s, "replacement_string": rep_string,
            "replacement_player": rep,
            "replacement_depth": rep_depth,
            "strings_listed_in_slot": _strings_in_slot(chart, slot),
            "status": status,
            "depth_chart_label_verbatim": labels.get(team, ""),
            "official_injury_url": INJ_URL,
            "official_depth_chart_url": urls.get(team, ""),
        })
    return out


def _strings_in_slot(chart: List[Dict[str, str]], slot: str) -> int:
    for row in chart:
        if row["position_slot"] == slot:
            try:
                return int(row.get("strings_listed", "") or 0)
            except ValueError:
                return 0
    return 0


def summarise(rows: List[Dict[str, object]]) -> List[Dict[str, object]]:
    agg: Dict[str, Dict[str, object]] = {}
    for r in rows:
        t = r["team_abbr"]
        a = agg.setdefault(t, {"team_abbr": t, "listed_players": 0, "out": 0,
                               "doubtful": 0, "questionable": 0,
                               "resolved_replacements": 0,
                               "unresolved_replacements": 0,
                               "deepest_replacement": 0,
                               "depth_weighted_out": 0.0})
        a["listed_players"] += 1
        gs = r["game_status"]
        if gs == "Out":
            a["out"] += 1
        elif gs == "Doubtful":
            a["doubtful"] += 1
        elif gs == "Questionable":
            a["questionable"] += 1
        if r["status"] == "resolved":
            a["resolved_replacements"] += 1
        else:
            a["unresolved_replacements"] += 1
        if isinstance(r["replacement_depth"], int):
            a["deepest_replacement"] = max(a["deepest_replacement"],
                                           int(r["replacement_depth"]))
            if gs in ("Out", "Doubtful"):
                a["depth_weighted_out"] += PROPOSED_DEPTH_WEIGHT.get(
                    int(r["replacement_depth"]), 0.0)
    for a in agg.values():
        a["proposed_depth_weight_out_doubtful"] = round(a.pop("depth_weighted_out"), 2)
        a["score_kind"] = "proposed_weight_not_observed"
        a["official_injury_url"] = INJ_URL
    return sorted(agg.values(), key=lambda r: -r["proposed_depth_weight_out_doubtful"])
