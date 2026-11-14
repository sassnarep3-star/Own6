"""Replacement-depth register.

The request is not "was there a replacement" but "how deep was the
replacement". For every starter slot on both clubs whose Week 10 game was
captured, this module resolves:

    string 1  -> the listed starter
    string 2  -> first backup
    string 3  -> second backup
    string 4  -> third backup

and then answers, for each slot, the questions that actually move a line:

* Is the starter on the injury report at all, and with what game status?
* If the starter cannot play, which string is the *first available* body?
* How many strings deep is that? (``depth_of_replacement`` = the string number
  of the first available player, so 1 means no replacement is needed.)
* How many listed players above that player are unavailable?
* Does the drop cross a unit boundary (offence vs defence)?

Only two clubs have a verified depth chart in this capture (New England and
Detroit -- the Week 10 Munich game). Every other club's row is deliberately
absent rather than guessed, and the coverage gap is published on the site.

Designations come from ``https://www.nfl.com/injuries/`` only. A player who is
not listed on the injury report is treated as available with designation
``not_listed`` -- that is an absence of evidence and is labelled as such, not
as a verified "healthy".
"""

from __future__ import annotations

from . import capture as C

AVAILABLE_DESIGNATIONS = {"", "Questionable", "not_listed", "Doubtful"}


def injury_lookup():
    """(team, normalised player name) -> (designation, record)."""
    out = {}
    for team, player, pos, injury, practice, game in C.INJURIES_W10:
        out[(team, _norm(player))] = {
            "player": player,
            "position": pos,
            "injury": injury,
            "practice_status": practice,
            "game_status": game,
        }
    return out


def _norm(name):
    n = name.lower().replace(".", "").replace("'", "").replace("-", " ")
    n = n.replace(" iii", "").replace(" jr", "").replace(" sr", "")
    return " ".join(n.split())


def _depth_slots(team):
    return C.DEPTH_BY_TEAM.get(team, [])


def register_rows(team):
    """One row per depth-chart slot for ``team``."""
    inj = injury_lookup()
    rows = []
    for unit, slot, names in _depth_slots(team):
        statuses = []
        for i, name in enumerate(names, start=1):
            rec = inj.get((team, _norm(name)))
            if rec is None:
                statuses.append({"string": i, "player": name, "designation": "not_listed", "record": None})
            else:
                statuses.append(
                    {
                        "string": i,
                        "player": name,
                        "designation": rec["game_status"] or "practice_only",
                        "record": rec,
                    }
                )
        first_available = None
        for st in statuses:
            if st["designation"] not in ("Out", "Doubtful"):
                first_available = st
                break
        starter = statuses[0]
        depth_of_replacement = first_available["string"] if first_available else None
        unavailable_above = sum(
            1 for st in statuses if st["designation"] in ("Out", "Doubtful") and (first_available is None or st["string"] < first_available["string"])
        )
        # Second-order check: if a starter who is merely Questionable is scratched,
        # how deep does the club actually go? This is the number that matters for
        # a line, so it is published next to -- never instead of -- the primary.
        scratch = [st for st in statuses[1:] if st["designation"] not in ("Out", "Doubtful")]
        depth_if_scratched = scratch[0]["string"] if scratch else None
        replacement_designation = first_available["designation"] if first_available else ""
        rows.append(
            {
                "team": team,
                "unit": unit,
                "position_slot": slot,
                "starter": starter["player"],
                "starter_designation": starter["designation"],
                "listed_strings": len(names),
                "first_available_player": "" if first_available is None else first_available["player"],
                "replacement_designation": replacement_designation,
                "depth_of_replacement": "" if depth_of_replacement is None else depth_of_replacement,
                "depth_if_starter_scratched": "" if depth_if_scratched is None else depth_if_scratched,
                "unavailable_above_replacement": unavailable_above,
                "is_backup_start": "yes" if depth_of_replacement not in (None, 1) else "no",
                "replacement_is_4th_string_or_worse": "yes" if (depth_of_replacement or 0) >= 4 else "no",
                "deficiency_points": _deficiency(depth_of_replacement, unavailable_above),
                "score_kind": "proposed_weight_not_observed",
                "injury_report_url": C.CAPTURES["injuries"]["url"],
                "depth_chart_url": C.DEPTH_URL_BY_TEAM[team],
            }
        )
    return rows


def _deficiency(depth, unavailable_above):
    """A declared, un-validated penalty. Published as ``proposed_weight``."""
    if depth is None:
        return 0.0
    base = {1: 0.0, 2: 1.0, 3: 2.0, 4: 3.0}.get(depth, 3.0)
    return round(base + 0.5 * max(0, unavailable_above - 1), 2)


def register_notes(team):
    """Cross-checks between the depth chart and the injury report.

    These are the cases a reader must look at, because they are where the two
    official pages disagree about who is available.
    """
    inj = injury_lookup()
    notes = []
    for unit, slot, names in _depth_slots(team):
        for i, name in enumerate(names, start=1):
            rec = inj.get((team, _norm(name)))
            if rec and rec["game_status"] == "Out":
                notes.append(
                    {
                        "team": team,
                        "unit": unit,
                        "position_slot": slot,
                        "string": i,
                        "player": name,
                        "designation": rec["game_status"],
                        "injury": rec["injury"],
                        "practice_status": rec["practice_status"],
                        "note": "Listed on the depth chart but ruled Out on the official injury report.",
                    }
                )
    return notes


if __name__ == "__main__":  # pragma: no cover
    rows = register_rows("NE") + register_rows("DET")
    print("depth rows:", len(rows))
    for r in rows:
        if r["is_backup_start"] == "yes":
            print(r["team"], r["position_slot"], r["starter"], "->", r["first_available_player"], "string", r["depth_of_replacement"])
