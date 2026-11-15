"""Availability graph: who was expected to start, who actually did.

Nodes are player-club-game states with an explicit evidence level. The graph
is a first-class dataset: it has its own tables and its own rules.

Evidence levels (published per node, never mixed):
  designation   — the official hub printed a game status for the player
  roster_state  — the official club roster page printed a status code
  announced     — an official dated starter announcement (none captured here)
  actual_start  — an official Game Book names the starter (NONE available:
                  game books were not reachable this session; every
                  actual_start cell is blank and gated)

Depth order is NOT derived from jersey number, experience or salary (the
brief's explicit rejection). Replacement identity stays blank unless an
official page names the replacement.
"""
from __future__ import annotations

from .capture import (GB_NON_ACT_ROWS, GB_ROSTER_READ, GB_ROSTER_URL,
                      WEEK10_GAMES)
from .injury import INJURY_ROWS_A, INJURY_READ_A, INJURY_URL


def _w10_by_club():
    m = {}
    for gid, slug, date, status, away, home, as_, hs, mark, url in WEEK10_GAMES:
        m[away] = (gid, status, url); m[home] = (gid, status, url)
    return m


def designation_nodes():
    """One node per hub row (read A), tied to the club's week-10 game slot."""
    w10 = _w10_by_club()
    out = []
    for gid, club, player, pos, inj, practice, game in INJURY_ROWS_A:
        slot, status, url = w10.get(club, (gid, "unknown", INJURY_URL))
        out.append({
            "node_id": f"DES-{gid}-{club}-{player}", "player": player, "club": club,
            "position": pos, "game_slot": slot, "game_status_at_read_a": game or "",
            "practice_status_at_read_a": practice,
            "expected_to_start": "",   # never inferred from a designation
            "actual_start": "",        # Game Book gate: no official starter data
            "replacement_named": "",   # blank unless an official page names one
            "evidence_level": "designation",
            "read_at_utc": INJURY_READ_A,
            "source_url": INJURY_URL,
        })
    return out


def roster_nodes():
    out = []
    for name, slug, jersey, pos, code in GB_NON_ACT_ROWS:
        out.append({
            "node_id": f"ROS-GB-{slug}", "player": name, "club": "GB",
            "position": pos, "game_slot": "W10-05", "game_status_at_read_a": "",
            "practice_status_at_read_a": "",
            "expected_to_start": "", "actual_start": "", "replacement_named": "",
            "evidence_level": "roster_state",
            "read_at_utc": GB_ROSTER_READ,
            "source_url": GB_ROSTER_URL,
        })
    return out


def edges():
    """Event edges between node states and game slots. Each edge names its
    evidence; an edge with unknown replacement carries a blank, not a guess."""
    out = []
    for gid, club, player, pos, inj, practice, game in INJURY_ROWS_A:
        if game == "Out":
            out.append({"edge_id": f"E-OUT-{gid}-{club}-{player}",
                        "from_node": f"DES-{gid}-{club}-{player}",
                        "to_slot": gid, "edge_type": "declared_out",
                        "replacement_named": "",
                        "actual_start_evidence": "",
                        "note": "starter-or-backup role unknown: depth order must not be "
                                "inferred; Game Book / snap evidence not available",
                        "source_url": INJURY_URL})
        elif game in ("Doubtful", "Questionable"):
            out.append({"edge_id": f"E-RISK-{gid}-{club}-{player}",
                        "from_node": f"DES-{gid}-{club}-{player}",
                        "to_slot": gid, "edge_type": f"designation_{game.lower()}",
                        "replacement_named": "", "actual_start_evidence": "",
                        "note": "surprise signal only (delta across reads); the level is "
                                "not a feature",
                        "source_url": INJURY_URL})
    return out


def sweep_rows():
    """32-club availability sweep status. A club is 'swept' only when its hub
    table AND its roster page were both read this session."""
    from .results import TEAMS
    hub_clubs = {r[1] for r in INJURY_ROWS_A}
    roster_clubs = {"GB"}
    out = []
    for t in TEAMS:
        ok = t in hub_clubs and t in roster_clubs
        out.append({"club": t,
                    "hub_table_read": "yes" if t in hub_clubs else "no",
                    "roster_page_read": "yes" if t in roster_clubs else "no",
                    "sweep_complete": "yes" if ok else "no",
                    "blocking_gate": "" if ok else
                        "G-SWEEP: 32 club roster/IR pages must be read before any "
                        "team-level model is trusted",
                    "number_that_would_clear": "32 of 32 clubs with hub table + roster page "
                                               "captured (this session: "
                                               f"{len(hub_clubs)} hub, {len(roster_clubs)} roster)",
                    "source_url": GB_ROSTER_URL if (t in roster_clubs and t not in hub_clubs)
                                  else INJURY_URL,
                    "roster_source_url": GB_ROSTER_URL if t in roster_clubs else ""})
    return out
