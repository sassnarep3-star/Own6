"""Timestamped injury-hub series: reads with clock times, deltas, never levels.

The store keeps each read as its own block. A designator's *level* (e.g.
"Questionable") is never used as a feature here; what this module publishes is
the *change between reads* — the surprise. Read A is captured in
``capture.INJURY_ROWS_A``; read B is appended the same way and diffed here.
"""
from __future__ import annotations

from .capture import (INJURY_ROWS_A, INJURY_READ_A, INJURY_URL,
                      INJURY_READ_A_WINDOW)

# Read B block is appended to capture.py during the session; import defensively.
try:
    from .capture import INJURY_ROWS_B, INJURY_READ_B, INJURY_READ_B_WINDOW
except ImportError:  # read B not taken yet at build time
    INJURY_ROWS_B, INJURY_READ_B, INJURY_READ_B_WINDOW = [], "", ""


def read_rows(rows, read_at):
    out = []
    for gid, club, player, pos, inj, practice, game in rows:
        out.append({"hub_game_id": gid, "club": club, "player": player,
                    "position": pos, "injury_text": inj,
                    "practice_status": practice, "game_status": game,
                    "read_at_utc": read_at, "source_url": INJURY_URL})
    return out


def series_rows():
    rows = read_rows(INJURY_ROWS_A, INJURY_READ_A)
    if INJURY_ROWS_B:
        rows += read_rows(INJURY_ROWS_B, INJURY_READ_B)
    return rows


def delta_rows():
    """One row per player present in BOTH reads, plus appeared/disappeared.

    The delta is the published quantity: ``status_from -> status_to``. A row
    whose statuses are equal is still published with delta 'no-change', so the
    series proves its own cadence.
    """
    if not INJURY_ROWS_B:
        return []
    a = {(r[1], r[2]): r for r in INJURY_ROWS_A}
    b = {(r[1], r[2]): r for r in INJURY_ROWS_B}
    out = []
    for key in sorted(set(a) | set(b)):
        club, player = key
        ra, rb = a.get(key), b.get(key)
        if ra and rb:
            from_s = f"practice={ra[5]};game={ra[6] or 'blank'}"
            to_s = f"practice={rb[5]};game={rb[6] or 'blank'}"
            kind = "no-change" if (ra[5], ra[6]) == (rb[5], rb[6]) else "changed"
        elif ra:
            from_s = f"practice={ra[5]};game={ra[6] or 'blank'}"; to_s = "absent at read B"
            kind = "row-disappeared"
        else:
            from_s = "absent at read A"; to_s = f"practice={rb[5]};game={rb[6] or 'blank'}"
            kind = "row-appeared"
        out.append({"club": club, "player": player,
                    "read_a_at_utc": INJURY_READ_A, "state_at_read_a": from_s,
                    "read_b_at_utc": INJURY_READ_B, "state_at_read_b": to_s,
                    "delta_kind": kind,
                    "surprise_column": to_s if kind != "no-change" else "",
                    "source_url": INJURY_URL})
    return out


def designation_counts(rows):
    counts = {}
    for r in rows:
        key = r["game_status"] if r["game_status"] else "(blank)"
        counts[key] = counts.get(key, 0) + 1
    return counts


def cross_read_notes():
    """Deltas against earlier reads recorded by other packs (not re-verified
    here; cited so the delta is on the record with its provenance)."""
    return [
        {"item": "DET Kerby Joseph, Cade Mays, D.J. Reed game-status cells",
         "earlier_state": "blank (sibling packs' 2026-11-13/14 reads of the hub; see "
                          "COORDINATION.md VR-08/VR-12 lineage)",
         "state_at_read_a_2026-11-15T23:58Z": "Out (Knee / Ankle / Hip, all DNP) — "
                                              "published on the hub now",
         "delta_kind": "blank -> Out (designation filled at later read)",
         "source_url": INJURY_URL,
         "note": "The brief's 'Populate the three missing Lions game-status designations' "
                 "resolves at the source itself: the hub now prints Out for all three."},
        {"item": "GB Malik Willis",
         "earlier_state": "recorded on injured reserve by a sibling pack (2026-11-13/14)",
         "state_at_read_a_2026-11-15T23:58Z": "absent from the hub AND from the GB roster "
                                              "page (no row, any status)",
         "delta_kind": "roster-state changed at source between reads; current state unknown",
         "source_url": "https://www.nfl.com/teams/green-bay-packers/roster/",
         "note": "'Not listed' is published as unknown, never as available."},
    ]
