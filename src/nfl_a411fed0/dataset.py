"""Loaders for the raw, officially-sourced captures in ``data/nfl_a411fed0/raw``.

Every loader returns plain dicts.  Nothing here computes, imputes or
interpolates: it only reads what was transcribed from an official page.
"""
from __future__ import annotations

import csv
import os
from typing import Dict, List

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "nfl_a411fed0", "raw")

RESULTS_FILE = "results_2026_w1_9.psv"
SLATE_FILE = "slate_2026_w10.psv"
BYES_FILE = "week10_byes.psv"
INJURY_FILE = "injuries_2026_w10.psv"
DEPTH_FILE = "depth_charts.psv"
BULLETIN_FILE = "official_bulletins.psv"

#: Teams whose regular-season 2026 record/points were read from
#: https://www.nfl.com/standings/league/2026/REG on 2026-11-14.
#: (abbr, conference, division, team, W, L, T, PF, PA)
STANDINGS_THRU_W9 = [
    ("BUF", "AFC", "AFC East", "Buffalo Bills", 7, 1, 0, 256, 187),
    ("SF", "NFC", "NFC West", "San Francisco 49ers", 7, 1, 0, 235, 156),
    ("CHI", "NFC", "NFC North", "Chicago Bears", 7, 2, 0, 241, 184),
    ("DEN", "AFC", "AFC West", "Denver Broncos", 7, 2, 0, 198, 186),
    ("CIN", "AFC", "AFC North", "Cincinnati Bengals", 6, 2, 0, 240, 175),
    ("DET", "NFC", "NFC North", "Detroit Lions", 6, 2, 0, 222, 189),
    ("JAX", "AFC", "AFC South", "Jacksonville Jaguars", 6, 2, 0, 229, 121),
    ("KC", "AFC", "AFC West", "Kansas City Chiefs", 6, 2, 0, 202, 143),
    ("MIN", "NFC", "NFC North", "Minnesota Vikings", 6, 2, 0, 146, 116),
    ("PIT", "AFC", "AFC North", "Pittsburgh Steelers", 6, 2, 0, 180, 144),
    ("GB", "NFC", "NFC North", "Green Bay Packers", 6, 3, 0, 216, 191),
    ("NYG", "NFC", "NFC East", "New York Giants", 5, 3, 1, 203, 196),
    ("CLE", "AFC", "AFC North", "Cleveland Browns", 5, 4, 0, 161, 196),
    ("LA", "NFC", "NFC West", "Los Angeles Rams", 5, 4, 0, 214, 181),
    ("NE", "AFC", "AFC East", "New England Patriots", 5, 4, 0, 211, 207),
    ("SEA", "NFC", "NFC West", "Seattle Seahawks", 5, 4, 0, 202, 162),
    ("BAL", "AFC", "AFC North", "Baltimore Ravens", 4, 5, 0, 189, 236),
    ("DAL", "NFC", "NFC East", "Dallas Cowboys", 4, 5, 0, 246, 236),
    ("LV", "AFC", "AFC West", "Las Vegas Raiders", 4, 5, 0, 238, 268),
    ("WAS", "NFC", "NFC East", "Washington Commanders", 3, 5, 1, 196, 223),
    ("CAR", "NFC", "NFC South", "Carolina Panthers", 3, 5, 0, 199, 219),
    ("HOU", "AFC", "AFC South", "Houston Texans", 3, 5, 0, 209, 192),
    ("NO", "NFC", "NFC South", "New Orleans Saints", 3, 5, 0, 185, 216),
    ("AZ", "NFC", "NFC West", "Arizona Cardinals", 3, 6, 0, 178, 255),
    ("ATL", "NFC", "NFC South", "Atlanta Falcons", 3, 6, 0, 188, 223),
    ("TB", "NFC", "NFC South", "Tampa Bay Buccaneers", 3, 6, 0, 202, 178),
    ("IND", "AFC", "AFC South", "Indianapolis Colts", 2, 7, 0, 184, 249),
    ("NYJ", "AFC", "AFC East", "New York Jets", 2, 7, 0, 182, 223),
    ("PHI", "NFC", "NFC East", "Philadelphia Eagles", 2, 7, 0, 148, 221),
    ("MIA", "AFC", "AFC East", "Miami Dolphins", 1, 7, 0, 126, 200),
    ("TEN", "AFC", "AFC South", "Tennessee Titans", 1, 7, 0, 144, 199),
    ("LAC", "AFC", "AFC West", "Los Angeles Chargers", 0, 8, 0, 121, 219),
]

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"

#: Weeks of the 2026 regular season whose official scores page returned
#: readable final scores during this session's capture.
INGESTED_WEEKS = (1, 2, 3, 5, 6, 7, 8, 9)
#: Week whose official scores page would not render scores ("Hidden Score")
#: on every attempt made in this session.
MISSING_WEEKS = (4,)


def _read_psv(name: str) -> List[Dict[str, str]]:
    path = os.path.join(RAW_DIR, name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="|"))


def results() -> List[Dict[str, str]]:
    """Verified 2026 regular-season results (weeks 1-3, 5-9)."""
    return _read_psv(RESULTS_FILE)


def slate() -> List[Dict[str, str]]:
    """Week 10 slate as published on the official NFL scores page."""
    return _read_psv(SLATE_FILE)


def byes() -> List[Dict[str, str]]:
    return _read_psv(BYES_FILE)


def injuries() -> List[Dict[str, str]]:
    return _read_psv(INJURY_FILE)


def depth_charts() -> List[Dict[str, str]]:
    return _read_psv(DEPTH_FILE)


def bulletins() -> List[Dict[str, str]]:
    return _read_psv(BULLETIN_FILE)


def standings() -> List[Dict[str, object]]:
    rows = []
    for abbr, conf, div, team, w, l, t, pf, pa in STANDINGS_THRU_W9:
        gp = w + l + t
        rows.append({
            "team_abbr": abbr, "conference": conf, "division": div, "team": team,
            "w": w, "l": l, "t": t, "pf": pf, "pa": pa, "net_pts": pf - pa,
            "games_played": gp,
            "pf_per_game": round(pf / gp, 3) if gp else "",
            "pa_per_game": round(pa / gp, 3) if gp else "",
            "net_pts_per_game": round((pf - pa) / gp, 3) if gp else "",
            "official_source_url": STANDINGS_URL,
        })
    return rows


TEAMS = sorted(r[0] for r in STANDINGS_THRU_W9)
TEAM_NAMES = {r[0]: r[3] for r in STANDINGS_THRU_W9}
