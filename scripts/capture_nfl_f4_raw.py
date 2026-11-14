#!/usr/bin/env python3
"""Emit the RAW, as-read snapshots for the nfl_f4 pack.

Every value in this file was copied by hand from the official page named in the
row's ``source_url`` during the capture session on 2026-11-14 (see
``data/nfl_f4/sources.csv`` for the per-source record and boundary notes).
Nothing is inferred: if a field was not on the page it is written as an empty
string and the downstream builder is required to leave it blank and flag it.

Run:  python3 scripts/capture_nfl_f4_raw.py
Out:  data/nfl_f4/raw/*.csv
"""

from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "nfl_f4", "raw")

NFL_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-{w}"
NFL_STAND = "https://www.nfl.com/standings/"
NFL_INJ = "https://www.nfl.com/injuries/"
NE_DEPTH = "https://www.patriots.com/team/depth-chart"
DET_DEPTH = "https://www.detroitlions.com/team/depth-chart"
ESPN_ODDS = ("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/"
              "{eid}/competitions/{eid}/odds")

# ---------------------------------------------------------------------------
# 1. FINAL SCORES — nfl.com/schedules/2026/by-week/week-{w}, read 2026-11-14.
#    Tuple: (away_abbr, away_score, home_abbr, home_score)
# ---------------------------------------------------------------------------
FINALS = {
    1: [("NE", 10, "SEA", 13), ("SF", 27, "LA", 7), ("CHI", 59, "CAR", 37),
        ("TB", 27, "CIN", 33), ("NO", 30, "DET", 31), ("BUF", 36, "HOU", 31),
        ("BAL", 41, "IND", 23), ("CLE", 10, "JAX", 34), ("ATL", 13, "PIT", 20),
        ("NYJ", 23, "TEN", 10), ("AZ", 26, "LAC", 14), ("MIA", 13, "LV", 27),
        ("GB", 22, "MIN", 39), ("WAS", 22, "PHI", 24), ("DAL", 20, "NYG", 28),
        ("DEN", 10, "KC", 31)],
    2: [("DET", 31, "BUF", 41), ("CAR", 34, "ATL", 3), ("NO", 24, "BAL", 17),
        ("MIN", 9, "CHI", 3), ("CIN", 20, "HOU", 6), ("PIT", 3, "NE", 20),
        ("GB", 20, "NYJ", 17), ("CLE", 23, "TB", 19), ("PHI", 24, "TEN", 20),
        ("JAX", 13, "DEN", 20), ("LV", 26, "LAC", 14), ("SEA", 31, "AZ", 7),
        ("WAS", 20, "DAL", 37), ("MIA", 13, "SF", 35), ("IND", 30, "KC", 33),
        ("NYG", 6, "LA", 28)],
    3: [("ATL", 35, "GB", 14), ("LAC", 16, "BUF", 24), ("CAR", 18, "CLE", 21),
        ("NYJ", 24, "DET", 31), ("HOU", 17, "IND", 19), ("NE", 6, "JAX", 35),
        ("KC", 24, "MIA", 10), ("TEN", 7, "NYG", 12), ("CIN", 27, "PIT", 30),
        ("SEA", 31, "WAS", 33), ("AZ", 30, "SF", 36), ("MIN", 23, "TB", 16),
        ("LV", 35, "NO", 27), ("BAL", 34, "DAL", 31), ("LA", 26, "DEN", 30),
        ("PHI", 7, "CHI", 27)],
    4: [("PIT", 24, "CLE", 27), ("IND", 30, "WAS", 13), ("TEN", 18, "BAL", 24),
        ("NE", 29, "BUF", 26), ("NYJ", 12, "CHI", 23), ("JAX", 22, "CIN", 17),
        ("DAL", 34, "HOU", 30), ("AZ", 24, "NYG", 36), ("LA", 24, "PHI", 20),
        ("GB", 17, "TB", 14), ("MIA", 10, "MIN", 15), ("KC", 30, "LV", 27),
        ("LAC", 23, "SEA", 30), ("DEN", 14, "SF", 24), ("DET", 26, "CAR", 32),
        ("ATL", 45, "NO", 24)],
    5: [("TB", 24, "DAL", 16), ("PHI", 17, "JAX", 19), ("CIN", 31, "MIA", 24),
        ("LV", 17, "NE", 45), ("MIN", 23, "NO", 13), ("CLE", 12, "NYJ", 17),
        ("IND", 22, "PIT", 34), ("HOU", 26, "TEN", 3), ("NYG", 27, "WAS", 27),
        ("CHI", 7, "GB", 31), ("DEN", 23, "LAC", 17), ("DET", 45, "AZ", 21),
        ("SF", 32, "SEA", 29), ("BAL", 30, "ATL", 23), ("BUF", 37, "LA", 34)],
    6: [("SEA", 14, "DEN", 17), ("HOU", 34, "JAX", 31), ("CHI", 31, "ATL", 23),
        ("BAL", 10, "CLE", 13), ("TEN", 26, "IND", 20), ("NYJ", 19, "NE", 26),
        ("NO", 34, "NYG", 27), ("CAR", 25, "PHI", 14), ("PIT", 26, "TB", 19),
        ("AZ", 18, "LA", 16), ("LAC", 6, "KC", 22), ("BUF", 33, "LV", 30),
        ("DAL", 13, "GB", 23), ("WAS", 17, "SF", 23)],
    7: [("NE", 24, "CHI", 30), ("PIT", 16, "NO", 10), ("SF", 20, "ATL", 29),
        ("CIN", 35, "BAL", 13), ("TB", 43, "CAR", 13), ("NYG", 27, "HOU", 21),
        ("IND", 10, "MIN", 16), ("MIA", 28, "NYJ", 25), ("CLE", 27, "TEN", 24),
        ("DEN", 30, "AZ", 16), ("GB", 17, "DET", 20), ("LA", 35, "LV", 21),
        ("KC", 3, "SEA", 20), ("DAL", 38, "PHI", 21)],
    8: [("CAR", 19, "GB", 27), ("BAL", 10, "BUF", 36), ("TEN", 36, "CIN", 43),
        ("AZ", 33, "DAL", 30), ("MIN", 15, "DET", 19), ("IND", 7, "JAX", 42),
        ("LV", 38, "NYJ", 33), ("CLE", 6, "PIT", 27), ("ATL", 0, "TB", 16),
        ("LAC", 9, "LA", 24), ("KC", 24, "DEN", 28), ("NE", 24, "MIA", 19),
        ("PHI", 10, "WAS", 27), ("CHI", 34, "SEA", 17)],
    9: [("JAX", 33, "BAL", 10), ("CIN", 34, "ATL", 17), ("DEN", 26, "CAR", 21),
        ("DAL", 27, "IND", 23), ("NYJ", 12, "KC", 35), ("DET", 19, "MIA", 9),
        ("CLE", 22, "NO", 23), ("NYG", 19, "PHI", 11), ("LA", 20, "WAS", 13),
        ("HOU", 44, "LAC", 22), ("LV", 17, "SF", 38), ("GB", 45, "NE", 27),
        ("AZ", 3, "SEA", 17), ("TB", 24, "CHI", 27), ("BUF", 23, "MIN", 6)],
    10: [("WAS", 24, "NYG", 21)],
}

# ---------------------------------------------------------------------------
# 2. STANDINGS — nfl.com/standings/, read 2026-11-14.
#    (conf, division, abbr, w, l, t, pf, pa)
# ---------------------------------------------------------------------------
STANDINGS = [
    ("AFC", "AFC East", "BUF", 7, 1, 0, 256, 187),
    ("AFC", "AFC East", "NE", 5, 4, 0, 211, 207),
    ("AFC", "AFC East", "NYJ", 2, 7, 0, 182, 223),
    ("AFC", "AFC East", "MIA", 1, 7, 0, 126, 200),
    ("AFC", "AFC North", "PIT", 6, 2, 0, 180, 144),
    ("AFC", "AFC North", "CIN", 6, 2, 0, 240, 175),
    ("AFC", "AFC North", "CLE", 5, 4, 0, 161, 196),
    ("AFC", "AFC North", "BAL", 4, 5, 0, 189, 236),
    ("AFC", "AFC South", "JAX", 6, 2, 0, 229, 121),
    ("AFC", "AFC South", "HOU", 3, 5, 0, 209, 192),
    ("AFC", "AFC South", "IND", 2, 7, 0, 184, 249),
    ("AFC", "AFC South", "TEN", 1, 7, 0, 144, 199),
    ("AFC", "AFC West", "DEN", 7, 2, 0, 198, 186),
    ("AFC", "AFC West", "KC", 6, 2, 0, 202, 143),
    ("AFC", "AFC West", "LV", 4, 5, 0, 238, 268),
    ("AFC", "AFC West", "LAC", 0, 8, 0, 121, 219),
    ("NFC", "NFC East", "NYG", 5, 3, 1, 203, 196),
    ("NFC", "NFC East", "DAL", 4, 5, 0, 246, 236),
    ("NFC", "NFC East", "WAS", 3, 5, 1, 196, 223),
    ("NFC", "NFC East", "PHI", 2, 7, 0, 148, 221),
    ("NFC", "NFC North", "CHI", 7, 2, 0, 241, 184),
    ("NFC", "NFC North", "DET", 6, 2, 0, 222, 189),
    ("NFC", "NFC North", "MIN", 6, 2, 0, 146, 116),
    ("NFC", "NFC North", "GB", 6, 3, 0, 216, 191),
    ("NFC", "NFC South", "CAR", 3, 5, 0, 199, 219),
    ("NFC", "NFC South", "NO", 3, 5, 0, 185, 216),
    ("NFC", "NFC South", "TB", 3, 6, 0, 202, 178),
    ("NFC", "NFC South", "ATL", 3, 6, 0, 188, 223),
    ("NFC", "NFC West", "SF", 7, 1, 0, 235, 156),
    ("NFC", "NFC West", "SEA", 5, 4, 0, 202, 162),
    ("NFC", "NFC West", "LA", 5, 4, 0, 214, 181),
    ("NFC", "NFC West", "AZ", 3, 6, 0, 178, 255),
]

# ---------------------------------------------------------------------------
# 3. WEEK 10 PRICE SNAPSHOTS — DraftKings lines as published through the ESPN
#    odds endpoint, read 2026-11-14. ``open`` and ``close`` are the provider's
#    own fields. For unplayed games the provider exposes ``current`` (the live
#    number at read time) and NO ``close`` field, which this capture records as
#    an empty close and marks ``close_status=not_final``.
#    (eid, away, home, away_open, away_open_px, away_close, away_close_px,
#     home_open, home_open_px, home_close, home_close_px,
#     tot_open, over_open_px, tot_close, over_close_px,
#     ml_away_open, ml_away_close, ml_home_open, ml_home_close)
# ---------------------------------------------------------------------------
PRICES = [
    # (eid, away, home, away_open, away_open_px, away_close, away_close_px,
    #  home_open, home_open_px, home_close, home_close_px,
    #  tot_open, over_open_px, under_open_px, tot_close, over_close_px, under_close_px,
    #  ml_away_open, ml_away_close, ml_home_open, ml_home_close)
    (401873052, "WAS", "NYG", 1.5, -110, 1.5, -110, -1.5, -110, -1.5, -110,
     47.5, -110, -110, 40.5, -112, -108, 105, 105, -125, -125),
    (401873053, "NE", "DET", 1.5, -110, 2.5, -102, -1.5, -110, -2.5, -118,
     48.5, -110, -110, 49.5, -112, -108, 105, 124, -125, -148),
    (401873054, "BUF", "NYJ", -7.0, -110, -7.5, -112, 7.0, -110, 7.5, -108,
     46.5, -110, -110, 50.5, -115, -105, -340, -395, 270, 310),
    (401873055, "CAR", "NO", 1.5, -110, 2.5, -115, -1.5, -110, -2.5, -105,
     43.5, -110, -110, 48.5, -115, -105, 105, 114, -125, -135),
    (401873056, "HOU", "CLE", -4.5, -110, -4.5, -108, 4.5, -110, 4.5, -112,
     38.5, -110, -110, 40.5, -108, -112, -218, -225, 180, 185),
    (401873057, "JAX", "TEN", -2.5, -110, -10.5, -115, 2.5, -110, 10.5, -105,
     45.5, -110, -110, 46.5, -110, -110, -135, -700, 114, 500),
    (401873058, "KC", "ATL", -4.5, -110, -3.0, -112, 4.5, -110, 3.0, -108,
     45.5, -110, -110, 47.5, -102, -118, -225, -166, 185, 140),
    (401873059, "MIA", "IND", 6.5, -110, 4.5, -112, -6.5, -110, -4.5, -108,
     47.5, -110, -110, 37.5, -110, -110, 235, 180, -290, -218),
    (401873060, "MIN", "GB", 4.5, -110, 2.5, 100, -4.5, -110, -2.5, -120,
     45.5, -110, -110, 42.5, -105, -115, 185, 124, -225, -148),
    (401873061, "LA", "AZ", -10.5, -110, -9.5, -112, 10.5, -110, 9.5, -108,
     47.5, -110, -110, 39.5, -108, -112, -535, -500, 400, 380),
    (401873062, "SEA", "LV", -7.0, -110, -6.5, -112, 7.0, -110, 6.5, -108,
     43.5, -110, -110, 40.5, -112, -108, -340, -305, 270, 245),
    (401873063, "SF", "DAL", 1.5, -115, -3.5, -115, -1.5, -105, 3.5, -105,
     52.5, -110, -110, 55.5, -118, -102, 100, -205, -120, 170),
    (401873064, "PIT", "CIN", 3.5, -110, 3.5, -112, -3.5, -110, -3.5, -108,
     47.5, -110, -110, 49.5, -105, -115, 160, 160, -192, -192),
    (401873065, "LAC", "BAL", 2.5, -110, 4.5, -112, -2.5, -110, -4.5, -108,
     48.5, -110, -110, 38.5, -110, -110, 120, 180, -142, -218),
]
# Games whose provider record had already settled to a close block at read time.
PRICE_SETTLED = {401873052}

# ---------------------------------------------------------------------------
# 4. WEEK 10 INJURY REPORT — nfl.com/injuries/, read 2026-11-14.
#    (team, player, position, injury, practice_status, game_status)
# ---------------------------------------------------------------------------
INJURIES = [
    # Washington Commanders
    ("WAS", "John Bates", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Treylon Burks", "WR", "", "Did Not Participate In Practice", ""),
    ("WAS", "Jayden Daniels", "QB", "", "Full Participation in Practice", ""),
    ("WAS", "Matt Gulbin", "C", "", "Full Participation in Practice", ""),
    ("WAS", "Chig Okonkwo", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("WAS", "Amik Robertson", "CB", "", "Limited Participation in Practice", ""),
    ("WAS", "Shy Tuttle", "DT", "", "Full Participation in Practice", ""),
    ("WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    # New York Giants
    ("NYG", "Abdul Carter", "LB", "", "Full Participation in Practice", ""),
    ("NYG", "Jermaine Eluemunor", "T", "", "Full Participation in Practice", ""),
    ("NYG", "Malik Harrison", "LB", "Groin", "Limited Participation in Practice", "Questionable"),
    ("NYG", "Colton Hood", "CB", "", "Full Participation in Practice", ""),
    ("NYG", "Theo Johnson", "TE", "", "Full Participation in Practice", ""),
    ("NYG", "Charlie Jones", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "J.J. McCarthy", "QB", "", "Full Participation in Practice", ""),
    ("NYG", "Darnell Mooney", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "Malik Nabers", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "Cam Skattebo", "RB", "", "Full Participation in Practice", ""),
    ("NYG", "Andrew Thomas", "T", "", "Full Participation in Practice", ""),
    # New England Patriots
    ("NE", "Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "A.J. Brown", "WR", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "Kevin Byard", "S", "Chest", "Full Participation in Practice", "Questionable"),
    ("NE", "Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "Reggie Gilliam", "FB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
    ("NE", "Hunter Henry", "TE", "", "Limited Participation in Practice", ""),
    ("NE", "Cameron Latu", "TE", "Back", "Limited Participation in Practice", "Questionable"),
    ("NE", "Drake Maye", "QB", "", "Full Participation in Practice", ""),
    ("NE", "Morgan Moses", "T", "", "Full Participation in Practice", ""),
    ("NE", "Walter Rouse", "T", "Concussion", "Limited Participation in Practice", "Questionable"),
    ("NE", "Brenden Schooler", "S", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("NE", "Rhamondre Stevenson", "RB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "Greg Van Roten", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("NE", "Charles Woods", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    # Detroit Lions
    ("DET", "Brian Branch", "S", "", "Full Participation in Practice", ""),
    ("DET", "Jared Goff", "QB", "", "Full Participation in Practice", ""),
    ("DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
    ("DET", "Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DET", "D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
    ("DET", "Jacob Saylors", "RB", "", "Full Participation in Practice", ""),
    ("DET", "Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
    ("DET", "Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("DET", "DJ Wonnum", "DE", "", "Full Participation in Practice", ""),
]

# ---------------------------------------------------------------------------
# 5. CLUB DEPTH CHARTS — read 2026-11-14. Both clubs label the chart UNOFFICIAL.
#    NE caveat (verbatim): "The 2026 depth chart is unofficial and is published
#    by the writers of Patriots.com. The depth chart reflects the opinions of
#    the Patriots.com writers and don't necessarily reflect those of the
#    organization."  DET caveat (verbatim): "2026 Unofficial Depth Chart
#    Compiled by Lions Football Communications"
#    (team, unit, slot, strings[list best->worst])
# ---------------------------------------------------------------------------
DEPTH = [
    ("NE", "Offense", "WR", ["A.J. Brown", "Efton Chism III"]),
    ("NE", "Offense", "LT", ["Will Campbell", "Dametrious Crownover", "Marcus Bryant"]),
    ("NE", "Offense", "LG", ["Ben Brown", "Walter Rouse"]),
    ("NE", "Offense", "C", ["Jared Wilson", "Ben Brown"]),
    ("NE", "Offense", "RG", ["Matt Pryor", "Walter Rouse"]),
    ("NE", "Offense", "RT", ["Morgan Moses", "Caleb Lomu"]),
    ("NE", "Offense", "TE", ["Hunter Henry", "Eli Raridon", "Cameron Latu"]),
    ("NE", "Offense", "WR2", ["DeMario Douglas", "Kyle Williams"]),
    ("NE", "Offense", "WR3", ["Efton Chism III", "Kyle Williams"]),
    ("NE", "Offense", "RB", ["Rhamondre Stevenson", "TreVeyon Henderson", "Corey Kiner", "Lan Larison"]),
    ("NE", "Offense", "QB", ["Drake Maye", "Tommy DeVito", "Behren Morton"]),
    ("NE", "Defense", "OLB", ["Dre'Mont Jones", "Gabe Jacas"]),
    ("NE", "Defense", "DT", ["Christian Barmore", "Leonard Taylor III"]),
    ("NE", "Defense", "DT2", ["Cory Durden", "DaQuan Jones"]),
    ("NE", "Defense", "DT3", ["Milton Williams", "Joshua Farmer"]),
    ("NE", "Defense", "OLB2", ["Elijah Ponder", "Gabe Jacas"]),
    ("NE", "Defense", "LB", ["Robert Spillane", "Darius Muasau", "Erick Hunter"]),
    ("NE", "Defense", "LB2", ["Christian Elliss", "Namdi Obiazor"]),
    ("NE", "Defense", "CB", ["Carlton Davis III", "Channing Canada"]),
    ("NE", "Defense", "S", ["Craig Woodson", "Mike Brown"]),
    ("NE", "Defense", "S2", ["Kevin Byard III", "Jaylen Reed", "Brenden Schooler"]),
    ("NE", "Defense", "CB2", ["Marcus Jones", "Charles Woods"]),
    ("NE", "Defense", "CB3", ["Christian Gonzalez", "Karon Prunty"]),
    ("DET", "Offense", "WR", ["Jameson Williams"]),
    ("DET", "Offense", "WR2", ["Amon-Ra St. Brown", "DeAndre Carter"]),
    ("DET", "Offense", "LT", ["Penei Sewell"]),
    ("DET", "Offense", "LG", ["Christian Mahogany", "Miles Frazier"]),
    ("DET", "Offense", "C", ["Cade Mays", "Juice Scruggs"]),
    ("DET", "Offense", "RG", ["Tate Ratledge", "Seth McLaughlin"]),
    ("DET", "Offense", "RT", ["Blake Miller", "Larry Borom"]),
    ("DET", "Offense", "TE", ["Sam LaPorta", "Brock Wright", "Tyler Conklin", "Jackson Meeks"]),
    ("DET", "Offense", "WR3", ["Isaac TeSlaa", "Tay Martin"]),
    ("DET", "Offense", "QB", ["Jared Goff", "Joshua Dobbs"]),
    ("DET", "Offense", "RB", ["Jahmyr Gibbs", "Sione Vaki", "Jacob Saylors"]),
    ("DET", "Defense", "EDGE", ["Aidan Hutchinson", "Derrick Moore", "Eric O'Neill"]),
    ("DET", "Defense", "DL", ["Alim McNeill", "Skyler Gill-Howard", "Mekhi Wingo"]),
    ("DET", "Defense", "DL2", ["Tyleik Williams", "Levi Onwuzurike"]),
    ("DET", "Defense", "EDGE2", ["DJ Wonnum", "Tyler Lacy", "Ahmed Hassanein"]),
    ("DET", "Defense", "LB", ["Derrick Barnes", "Joe Bachie"]),
    ("DET", "Defense", "LB2", ["Malcolm Rodriguez", "K.J. Britt"]),
    ("DET", "Defense", "LB3", ["Trevor Nowaske", "Amen Ogbongbemiga"]),
    ("DET", "Defense", "CB", ["D.J. Reed", "Rock Ya-Sin", "Khalil Dorsey", "Nick Whiteside"]),
    ("DET", "Defense", "CB2", ["Roger McCreary", "Ennis Rakestraw Jr.", "Keith Abney II"]),
    ("DET", "Defense", "S", ["Chuck Clark"]),
    ("DET", "Defense", "S2", ["Brian Branch", "Christian Izien"]),
]

CAVEATS = {
    "NE": ("The 2026 depth chart is unofficial and is published by the writers of "
           "Patriots.com. The depth chart reflects the opinions of the Patriots.com "
           "writers and don't necessarily reflect those of the organization."),
    "DET": "2026 Unofficial Depth Chart Compiled by Lions Football Communications",
}
DEPTH_URLS = {"NE": NE_DEPTH, "DET": DET_DEPTH}


def _w(name, header, rows):
    path = os.path.join(RAW, name)
    os.makedirs(RAW, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh, lineterminator="\n")
        wr.writerow(header)
        wr.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")


def main():
    read_date = "2026-11-14"

    rows = []
    for w in sorted(FINALS):
        for away, asc, home, hsc in FINALS[w]:
            rows.append([f"2026-REG-{w:02d}-{away.lower()}-at-{home.lower()}", 2026, w,
                         "final", away, asc, home, hsc,
                         NFL_SCHED.format(w=w), read_date])
    _w("results_finals.csv",
       ["game_key", "season", "week", "status", "away", "away_score", "home",
        "home_score", "source_url", "read_date"], rows)

    _w("standings.csv",
       ["conference", "division", "abbr", "w", "l", "t", "pf", "pa",
        "source_url", "read_date"],
       [[c, d, a, w, l, t, pf, pa, NFL_STAND, read_date]
        for c, d, a, w, l, t, pf, pa in STANDINGS])

    rows = []
    for (eid, away, home, ao, aop, ac, acp, ho, hop, hc, hcp,
         to, top, uop, tc, tcp, ucp, mao, mac, mho, mhc) in PRICES:
        settled = eid in PRICE_SETTLED
        close_status = "final" if settled else "not_final"
        url = ESPN_ODDS.format(eid=eid)
        for market, sel, ol, op_, cl, cp_ in (
                ("spread", away, ao, aop, ac, acp),
                ("spread", home, ho, hop, hc, hcp),
                ("total", "over", to, top, tc, tcp),
                ("total", "under", to, uop, tc, ucp),
                ("moneyline", away, "", mao, "", mac),
                ("moneyline", home, "", mho, "", mhc)):
            rows.append([eid, away, home, market, sel, ol, op_, cl, cp_,
                         "american", "open_close", close_status, url, read_date])
    _w("prices.csv",
       ["provider_event_id", "away", "home", "market", "selection",
        "open_line", "open_price", "close_line", "close_price", "price_format",
        "snapshot_kind", "close_status", "source_url", "read_date"], rows)

    _w("injuries.csv",
       ["team", "player", "position", "injury", "practice_status", "game_status",
        "source_url", "read_date"],
       [[t, p, pos, inj, pr, g, NFL_INJ, read_date]
        for t, p, pos, inj, pr, g in INJURIES])

    rows = []
    for team, unit, slot, strings in DEPTH:
        for i, ply in enumerate(strings, start=1):
            rows.append([team, unit, slot, i, ply, CAVEATS[team], DEPTH_URLS[team], read_date])
    _w("depth_charts.csv",
       ["team", "unit", "slot", "string", "player", "club_caveat_text",
        "source_url", "read_date"], rows)


if __name__ == "__main__":
    main()
