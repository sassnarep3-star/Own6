"""Raw capture of the official NFL-family pages read during this session.

Source of every literal in this module
--------------------------------------
All values below were read from the official pages named in ``CAPTURES`` on
2026-11-14 (UTC). The per-week transcripts were produced with a direct
``fetch_page`` of ``https://www.nfl.com/schedules/2026/by-week/week-<n>``.
Each game line appears on that page in the form

    [Away <a>, Home <h>, FINAL, <weekday>, <month> <d>]

and the score blocks follow it in the same order as the two clubs named in the
headline, which is the ordering used here. Nothing is inferred: a game whose
score block did not render a numeric score (NFL.com renders an explicit
``Hidden Score`` placeholder on some slates) is recorded with empty scores and
``score_status = "not_rendered"``.

Standings literals are from ``https://www.nfl.com/standings/`` (2026 season,
regular season, division view), read 2026-11-14. The table there is ordered
``W | L | T | PCT | PF | PA | NET | ...``.
"""

CAPTURE_DATE = "2026-11-14"

CAPTURES = {
    "standings": {
        "url": "https://www.nfl.com/standings/",
        "title": "2026 NFL Division Standings",
        "read_utc": "2026-11-14",
    },
    "schedule_week": {
        "url_template": "https://www.nfl.com/schedules/2026/by-week/week-{week}",
        "weeks_read": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "read_utc": "2026-11-14",
    },
    "injuries": {
        "url": "https://www.nfl.com/injuries/",
        "title": "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season",
        "read_utc": "2026-11-14",
    },
    "patriots_depth": {
        "url": "https://www.patriots.com/team/depth-chart",
        "title": "New England Patriots Unofficial Depth Chart",
        "read_utc": "2026-11-14",
    },
    "lions_depth": {
        "url": "https://www.detroitlions.com/team/depth-chart",
        "title": "2026 Lions Depth Chart",
        "read_utc": "2026-11-14",
    },
    "nfl_terms": {
        "url": "https://www.nfl.com/legal/terms/",
        "title": "NFL.com - Terms and Conditions (Updated: May 16, 2024)",
        "read_utc": "2026-11-14",
    },
    "betting_partners": {
        "url": "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners",
        "title": "NFL announces official partnerships with three leading sports betting operators",
        "read_utc": "2026-11-14",
    },
    "odds_probe": {
        "url": "https://www.nfl.com/odds/",
        "title": "404 - Flag on the Play.",
        "read_utc": "2026-11-14",
        "note": "NFL.com serves its 404 page here. There is no official NFL odds or line page.",
    },
}

# (abbr, W, L, T, PF, PA)  -- transcribed from https://www.nfl.com/standings/
STANDINGS = [
    ("BUF", 7, 1, 0, 256, 187),
    ("NE", 5, 4, 0, 211, 207),
    ("NYJ", 2, 7, 0, 182, 223),
    ("MIA", 1, 7, 0, 126, 200),
    ("PIT", 6, 2, 0, 180, 144),
    ("CIN", 6, 2, 0, 240, 175),
    ("CLE", 5, 4, 0, 161, 196),
    ("BAL", 4, 5, 0, 189, 236),
    ("JAX", 6, 2, 0, 229, 121),
    ("HOU", 3, 5, 0, 209, 192),
    ("IND", 2, 7, 0, 184, 249),
    ("TEN", 1, 7, 0, 144, 199),
    ("DEN", 7, 2, 0, 198, 186),
    ("KC", 6, 2, 0, 202, 143),
    ("LV", 4, 5, 0, 238, 268),
    ("LAC", 0, 8, 0, 121, 219),
    ("NYG", 5, 3, 1, 203, 196),
    ("DAL", 4, 5, 0, 246, 236),
    ("WAS", 3, 5, 1, 196, 223),
    ("PHI", 2, 7, 0, 148, 221),
    ("CHI", 7, 2, 0, 241, 184),
    ("DET", 6, 2, 0, 222, 189),
    ("MIN", 6, 2, 0, 146, 116),
    ("GB", 6, 3, 0, 216, 191),
    ("CAR", 3, 5, 0, 199, 219),
    ("NO", 3, 5, 0, 185, 216),
    ("TB", 3, 6, 0, 202, 178),
    ("ATL", 3, 6, 0, 188, 223),
    ("SF", 7, 1, 0, 235, 156),
    ("SEA", 5, 4, 0, 202, 162),
    ("LA", 5, 4, 0, 214, 181),
    ("AZ", 3, 6, 0, 178, 255),
]

STANDINGS_AS_OF = "2026-11-14"
STANDINGS_SCOPE = (
    "Season-to-date aggregate as displayed on nfl.com/standings after the conclusion "
    "of Week 9 and the Thursday Week 10 game (WAS 24, NYG 21). Games-played is derived "
    "as W+L+T and is therefore a computed value, not a transcribed one."
)

# Games: (week, away, home, away_score, home_score, date_label, source_index_note)
# date_label is the NFL.com game URL slug date component; scores are ints or None.
GAMES = [
    # ---- Week 1 (https://www.nfl.com/schedules/2026/by-week/week-1) ----
    (1, "NE", "SEA", 10, 13, "2026-09-09", ""),
    (1, "SF", "LA", 27, 7, "2026-09-10", ""),
    (1, "CHI", "CAR", 59, 37, "2026-09-13", ""),
    (1, "TB", "CIN", 27, 33, "2026-09-13", ""),
    (1, "NO", "DET", 30, 31, "2026-09-13", ""),
    (1, "BUF", "HOU", 36, 31, "2026-09-13", ""),
    (1, "BAL", "IND", 41, 23, "2026-09-13", ""),
    (1, "CLE", "JAX", 10, 34, "2026-09-13", ""),
    (1, "ATL", "PIT", 13, 20, "2026-09-13", ""),
    (1, "NYJ", "TEN", 23, 10, "2026-09-13", ""),
    (1, "AZ", "LAC", 26, 14, "2026-09-13", ""),
    (1, "MIA", "LV", 13, 27, "2026-09-13", ""),
    (1, "GB", "MIN", 22, 39, "2026-09-13", ""),
    (1, "WAS", "PHI", 22, 24, "2026-09-13", ""),
    (1, "DAL", "NYG", 20, 28, "2026-09-13", ""),
    (1, "DEN", "KC", 10, 31, "2026-09-14", ""),
    # ---- Week 2 (https://www.nfl.com/schedules/2026/by-week/week-2) ----
    (2, "DET", "BUF", 31, 41, "2026-09-17", ""),
    (2, "CAR", "ATL", 34, 3, "2026-09-20", ""),
    (2, "NO", "BAL", 24, 17, "2026-09-20", ""),
    (2, "MIN", "CHI", 9, 3, "2026-09-20", ""),
    (2, "CIN", "HOU", 20, 6, "2026-09-20", ""),
    (2, "PIT", "NE", 3, 20, "2026-09-20", ""),
    (2, "GB", "NYJ", 20, 17, "2026-09-20", ""),
    (2, "CLE", "TB", 23, 19, "2026-09-20", ""),
    (2, "PHI", "TEN", 24, 20, "2026-09-20", ""),
    (2, "JAX", "DEN", 13, 20, "2026-09-20", ""),
    (2, "LV", "LAC", 26, 14, "2026-09-20", ""),
    (2, "SEA", "AZ", 31, 7, "2026-09-20", ""),
    (2, "WAS", "DAL", 20, 37, "2026-09-20", ""),
    (2, "MIA", "SF", 13, 35, "2026-09-20", ""),
    (2, "IND", "KC", 30, 33, "2026-09-20", ""),
    (2, "NYG", "LA", 6, 28, "2026-09-21", ""),
    # ---- Week 3 (https://www.nfl.com/schedules/2026/by-week/week-3) ----
    (3, "ATL", "GB", 35, 14, "2026-09-24", ""),
    (3, "LAC", "BUF", 16, 24, "2026-09-27", ""),
    (3, "CAR", "CLE", 18, 21, "2026-09-27", ""),
    (3, "NYJ", "DET", 24, 31, "2026-09-27", ""),
    (3, "HOU", "IND", 17, 19, "2026-09-27", ""),
    (3, "NE", "JAX", 6, 35, "2026-09-27", ""),
    (3, "KC", "MIA", 24, 10, "2026-09-27", ""),
    (3, "TEN", "NYG", 7, 12, "2026-09-27", ""),
    (3, "CIN", "PIT", 27, 30, "2026-09-27", ""),
    (3, "SEA", "WAS", 31, 33, "2026-09-27", ""),
    (3, "AZ", "SF", 30, 36, "2026-09-27", ""),
    (3, "MIN", "TB", 23, 16, "2026-09-27", ""),
    (3, "LV", "NO", 35, 27, "2026-09-27", ""),
    (3, "BAL", "DAL", 34, 31, "2026-09-27", ""),
    (3, "LA", "DEN", 26, 30, "2026-09-27", ""),
    (3, "PHI", "CHI", 7, 27, "2026-09-28", ""),
    # ---- Week 4 (https://www.nfl.com/schedules/2026/by-week/week-4) ----
    (4, "PIT", "CLE", 24, 27, "2026-10-01", ""),
    (4, "IND", "WAS", 30, 13, "2026-10-04", ""),
    (4, "TEN", "BAL", 18, 24, "2026-10-04", ""),
    (4, "NE", "BUF", 29, 26, "2026-10-04", ""),
    (4, "NYJ", "CHI", 12, 23, "2026-10-04", ""),
    (4, "JAX", "CIN", 22, 17, "2026-10-04", ""),
    (4, "DAL", "HOU", 34, 30, "2026-10-04", ""),
    (4, "AZ", "NYG", 24, 36, "2026-10-04", ""),
    (4, "LA", "PHI", 24, 20, "2026-10-04", ""),
    (4, "GB", "TB", 17, 14, "2026-10-04", ""),
    (4, "MIA", "MIN", 10, 15, "2026-10-04", ""),
    (4, "KC", "LV", 30, 27, "2026-10-04", ""),
    (4, "LAC", "SEA", 23, 30, "2026-10-04", ""),
    (4, "DEN", "SF", 14, 24, "2026-10-04", ""),
    (4, "DET", "CAR", 26, 32, "2026-10-04", ""),
    (4, "ATL", "NO", 45, 24, "2026-10-05", ""),
    # ---- Week 5 (https://www.nfl.com/schedules/2026/by-week/week-5) ----
    (5, "TB", "DAL", 24, 16, "2026-10-08", ""),
    (5, "PHI", "JAX", 17, 19, "2026-10-11", ""),
    (5, "CIN", "MIA", 31, 24, "2026-10-11", ""),
    (5, "LV", "NE", 17, 45, "2026-10-11", ""),
    (5, "MIN", "NO", 23, 13, "2026-10-11", ""),
    (5, "CLE", "NYJ", 12, 17, "2026-10-11", ""),
    (5, "IND", "PIT", 22, 34, "2026-10-11", ""),
    (5, "HOU", "TEN", 26, 3, "2026-10-11", ""),
    (5, "NYG", "WAS", 27, 27, "2026-10-11", ""),
    (5, "CHI", "GB", 7, 31, "2026-10-11", ""),
    (5, "DEN", "LAC", 23, 17, "2026-10-11", ""),
    (5, "DET", "AZ", 45, 21, "2026-10-11", ""),
    (5, "SF", "SEA", 32, 29, "2026-10-11", ""),
    (5, "BAL", "ATL", 30, 23, "2026-10-11", ""),
    (5, "BUF", "LA", 37, 34, "2026-10-12", ""),
    # ---- Week 6 (https://www.nfl.com/schedules/2026/by-week/week-6) ----
    (6, "SEA", "DEN", 14, 17, "2026-10-15", ""),
    (6, "HOU", "JAX", 34, 31, "2026-10-18", ""),
    (6, "CHI", "ATL", 31, 23, "2026-10-18", ""),
    (6, "BAL", "CLE", 10, 13, "2026-10-18", ""),
    (6, "TEN", "IND", 26, 20, "2026-10-18", ""),
    (6, "NYJ", "NE", 19, 26, "2026-10-18", ""),
    (6, "NO", "NYG", 34, 27, "2026-10-18", ""),
    (6, "CAR", "PHI", 25, 14, "2026-10-18", ""),
    (6, "PIT", "TB", 26, 19, "2026-10-18", ""),
    (6, "AZ", "LA", 18, 16, "2026-10-18", ""),
    (6, "LAC", "KC", 6, 22, "2026-10-18", ""),
    (6, "BUF", "LV", 33, 30, "2026-10-18", ""),
    (6, "DAL", "GB", 13, 23, "2026-10-18", ""),
    (6, "WAS", "SF", 17, 23, "2026-10-19", ""),
    # ---- Week 7 (https://www.nfl.com/schedules/2026/by-week/week-7) ----
    (7, "NE", "CHI", 24, 30, "2026-10-22", ""),
    (7, "PIT", "NO", 16, 10, "2026-10-25", ""),
    (7, "SF", "ATL", 20, 29, "2026-10-25", ""),
    (7, "CIN", "BAL", 35, 13, "2026-10-25", ""),
    (7, "TB", "CAR", 43, 13, "2026-10-25", ""),
    (7, "NYG", "HOU", 27, 21, "2026-10-25", ""),
    (7, "IND", "MIN", 10, 16, "2026-10-25", ""),
    (7, "MIA", "NYJ", 28, 25, "2026-10-25", ""),
    (7, "CLE", "TEN", 27, 24, "2026-10-25", ""),
    (7, "DEN", "AZ", 30, 16, "2026-10-25", ""),
    (7, "GB", "DET", 17, 20, "2026-10-25", ""),
    (7, "LA", "LV", 35, 21, "2026-10-25", ""),
    (7, "KC", "SEA", 3, 20, "2026-10-25", ""),
    (7, "DAL", "PHI", 38, 21, "2026-10-26", ""),
    # ---- Week 8 (https://www.nfl.com/schedules/2026/by-week/week-8) ----
    (8, "CAR", "GB", 19, 27, "2026-10-29", ""),
    (8, "BAL", "BUF", 10, 36, "2026-11-01", ""),
    (8, "TEN", "CIN", 36, 43, "2026-11-01", ""),
    (8, "AZ", "DAL", 33, 30, "2026-11-01", ""),
    (8, "MIN", "DET", 15, 19, "2026-11-01", ""),
    (8, "IND", "JAX", 7, 42, "2026-11-01", ""),
    (8, "LV", "NYJ", 38, 33, "2026-11-01", ""),
    (8, "CLE", "PIT", 6, 27, "2026-11-01", ""),
    (8, "ATL", "TB", 0, 16, "2026-11-01", ""),
    (8, "LAC", "LA", 9, 24, "2026-11-01", ""),
    (8, "KC", "DEN", 24, 28, "2026-11-01", ""),
    (8, "NE", "MIA", 24, 19, "2026-11-01", ""),
    (8, "PHI", "WAS", 10, 27, "2026-11-01", ""),
    (8, "CHI", "SEA", 34, 17, "2026-11-02", ""),
    # ---- Week 9 (https://www.nfl.com/schedules/2026/by-week/week-9) ----
    (9, "JAX", "BAL", 33, 10, "2026-11-05", ""),
    (9, "CIN", "ATL", 34, 17, "2026-11-08", ""),
    (9, "DEN", "CAR", 26, 21, "2026-11-08", ""),
    (9, "DAL", "IND", 27, 23, "2026-11-08", ""),
    (9, "NYJ", "KC", 12, 35, "2026-11-08", ""),
    (9, "DET", "MIA", 19, 9, "2026-11-08", ""),
    (9, "CLE", "NO", 22, 23, "2026-11-08", ""),
    (9, "NYG", "PHI", 19, 11, "2026-11-08", ""),
    (9, "LA", "WAS", 20, 13, "2026-11-08", ""),
    (9, "HOU", "LAC", 44, 22, "2026-11-08", ""),
    (9, "LV", "SF", 17, 38, "2026-11-08", ""),
    (9, "GB", "NE", 45, 27, "2026-11-08", ""),
    (9, "AZ", "SEA", 3, 17, "2026-11-08", ""),
    (9, "TB", "CHI", 24, 27, "2026-11-08", ""),
    (9, "BUF", "MIN", 23, 6, "2026-11-09", ""),
    # ---- Week 10 (https://www.nfl.com/schedules/2026/by-week/week-10) ----
    (10, "WAS", "NYG", 24, 21, "2026-11-12", ""),
]

# Week 10 slate: 14 played/scheduled games listed on the by-week page.
# (week, day, date, kickoff_et, network, away, home)
SLATE_W10 = [
    (10, "Thursday", "2026-11-12", "8:15 PM", "Prime Video", "WAS", "NYG"),
    (10, "Sunday", "2026-11-15", "9:30 AM", "FOX", "NE", "DET"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "CBS", "KC", "ATL"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "FOX", "HOU", "CLE"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "FOX", "MIN", "GB"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "CBS", "MIA", "IND"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "FOX", "CAR", "NO"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "CBS", "BUF", "NYJ"),
    (10, "Sunday", "2026-11-15", "1:00 PM", "FOX", "JAX", "TEN"),
    (10, "Sunday", "2026-11-15", "4:05 PM", "CBS", "LA", "AZ"),
    (10, "Sunday", "2026-11-15", "4:05 PM", "CBS", "SEA", "LV"),
    (10, "Sunday", "2026-11-15", "4:25 PM", "FOX", "SF", "DAL"),
    (10, "Sunday", "2026-11-15", "8:20 PM", "NBC", "PIT", "CIN"),
    (10, "Monday", "2026-11-16", "8:15 PM", "ESPN", "LAC", "BAL"),
]

BYES_W10 = ["CHI", "DEN", "PHI", "TB"]

# Week 10 injury report entries read from https://www.nfl.com/injuries/
# (team, player, position, injury, practice_status, game_status)
# Only clubs whose Week 10 games were fully rendered in the capture are included.
INJURIES_W10 = [
    # Commanders (read from the Thursday Nov 12 block)
    ("WAS", "John Bates", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Treylon Burks", "WR", "", "Did Not Participate In Practice", ""),
    ("WAS", "Jayden Daniels", "QB", "", "Full Participation in Practice", ""),
    ("WAS", "Matt Gulbin", "C", "", "Full Participation in Practice", ""),
    ("WAS", "Chig Okonkwo", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("WAS", "Amik Robertson", "CB", "", "Limited Participation in Practice", ""),
    ("WAS", "Shy Tuttle", "DT", "", "Full Participation in Practice", ""),
    ("WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    # Giants
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
    # Patriots
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
    # Lions
    ("DET", "Brian Branch", "S", "", "Full Participation in Practice", ""),
    ("DET", "Jared Goff", "QB", "", "Full Participation in Practice", ""),
    ("DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
    ("DET", "Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DET", "D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
    ("DET", "Jacob Saylors", "RB", "", "Full Participation in Practice", ""),
    ("DET", "Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
    ("DET", "Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("DET", "DJ Wonnum", "DE", "", "Full Participation in Practice", ""),
    # Chiefs (partial block captured; see data/nfl_market/flagged.csv F05)
    ("KC", "Jeffrey Bassa", "LB", "", "Full Participation in Practice", ""),
    ("KC", "Mansoor Delane", "CB", "Shoulder", "Full Participation in Practice", "Questionable"),
    ("KC", "Justin Fields", "QB", "", "Full Participation in Practice", ""),
    ("KC", "Jaden Hicks", "S", "", "Full Participation in Practice", ""),
    ("KC", "Travis Kelce", "TE", "", "Full Participation in Practice", ""),
    ("KC", "Patrick Mahomes", "QB", "", "Full Participation in Practice", ""),
]

# Depth charts.  (unit, position_slot, [string1, string2, string3, string4])
# Transcribed verbatim from the two club pages; blanks in the source are dropped.
DEPTH_PATRIOTS = [
    ("Offense", "WR", ["A.J. Brown", "Efton Chism III"]),
    ("Offense", "LT", ["Will Campbell", "Dametrious Crownover", "Marcus Bryant"]),
    ("Offense", "LG", ["Ben Brown", "Walter Rouse"]),
    ("Offense", "C", ["Jared Wilson", "Ben Brown"]),
    ("Offense", "RG", ["Matt Pryor", "Walter Rouse"]),
    ("Offense", "RT", ["Morgan Moses", "Caleb Lomu"]),
    ("Offense", "TE", ["Hunter Henry", "Eli Raridon", "Cameron Latu"]),
    ("Offense", "WR", ["DeMario Douglas", "Kyle Williams"]),
    ("Offense", "WR", ["Efton Chism III", "Kyle Williams"]),
    ("Offense", "RB", ["Rhamondre Stevenson", "TreVeyon Henderson", "Corey Kiner", "Lan Larison"]),
    ("Offense", "QB", ["Drake Maye", "Tommy DeVito", "Behren Morton"]),
    ("Defense", "OLB", ["Dre'Mont Jones", "Gabe Jacas"]),
    ("Defense", "DT", ["Christian Barmore", "Leonard Taylor III"]),
    ("Defense", "DT", ["Cory Durden", "DaQuan Jones"]),
    ("Defense", "DT", ["Milton Williams", "Joshua Farmer"]),
    ("Defense", "OLB", ["Elijah Ponder", "Gabe Jacas"]),
    ("Defense", "LB", ["Robert Spillane", "Darius Muasau", "Erick Hunter"]),
    ("Defense", "LB", ["Christian Elliss", "Namdi Obiazor"]),
    ("Defense", "CB", ["Carlton Davis III", "Channing Canada"]),
    ("Defense", "S", ["Craig Woodson", "Mike Brown"]),
    ("Defense", "S", ["Kevin Byard III", "Jaylen Reed", "Brenden Schooler"]),
    ("Defense", "CB", ["Marcus Jones", "Charles Woods"]),
    ("Defense", "CB", ["Christian Gonzalez", "Karon Prunty"]),
]

DEPTH_LIONS = [
    ("Offense", "WR", ["Jameson Williams"]),
    ("Offense", "WR", ["Amon-Ra St. Brown", "DeAndre Carter"]),
    ("Offense", "LT", ["Penei Sewell"]),
    ("Offense", "LG", ["Christian Mahogany", "Miles Frazier"]),
    ("Offense", "C", ["Cade Mays", "Juice Scruggs"]),
    ("Offense", "RG", ["Tate Ratledge", "Seth McLaughlin"]),
    ("Offense", "RT", ["Blake Miller", "Larry Borom"]),
    ("Offense", "TE", ["Sam LaPorta", "Brock Wright", "Tyler Conklin", "Jackson Meeks"]),
    ("Offense", "WR", ["Isaac TeSlaa", "Tay Martin"]),
    ("Offense", "QB", ["Jared Goff", "Joshua Dobbs"]),
    ("Offense", "RB", ["Jahmyr Gibbs", "Sione Vaki", "Jacob Saylors"]),
    ("Defense", "EDGE", ["Aidan Hutchinson", "Derrick Moore", "Eric O'Neill"]),
    ("Defense", "DL", ["Alim McNeill", "Skyler Gill-Howard", "Mekhi Wingo"]),
    ("Defense", "DL", ["Tyleik Williams", "Levi Onwuzurike"]),
    ("Defense", "EDGE", ["DJ Wonnum", "Tyler Lacy", "Ahmed Hassanein"]),
    ("Defense", "LB", ["Derrick Barnes", "Joe Bachie"]),
    ("Defense", "LB", ["Malcolm Rodriguez", "K.J. Britt"]),
    ("Defense", "LB", ["Trevor Nowaske", "Amen Ogbongbemiga"]),
    ("Defense", "CB", ["D.J. Reed", "Rock Ya-Sin", "Khalil Dorsey", "Nick Whiteside"]),
    ("Defense", "CB", ["Roger McCreary", "Ennis Rakestraw Jr.", "Keith Abney II"]),
    ("Defense", "S", ["Chuck Clark"]),
    ("Defense", "S", ["Brian Branch", "Christian Izien"]),
]

DEPTH_BY_TEAM = {"NE": DEPTH_PATRIOTS, "DET": DEPTH_LIONS}
DEPTH_URL_BY_TEAM = {
    "NE": CAPTURES["patriots_depth"]["url"],
    "DET": CAPTURES["lions_depth"]["url"],
}

# Verbatim quotes used to constrain what the model is allowed to claim.
QUOTES = {
    "nfl_terms_1_1": (
        "As between you and us, we own all right, title and interest, including all intellectual "
        "property and proprietary rights (including goodwill), in and to, and related to, the "
        "Services, Modular Content, and all Trademarks, software, technology, platforms, "
        "applications, user interface, tools, links, text, images, photographs, video, audio, "
        "graphics, user interface, and other content (and the selection, coordination, and "
        "arrangement of any content), data, analytics, algorithms, or materials included or "
        "displayed in or through, provided with or through the use of, or generated from the "
        "Services, and any and all improvements to or derivatives of the forgoing."
    ),
    "nfl_terms_1_3": (
        "You may use the Services solely for your own individual non-commercial and informational "
        "purposes only. Any other use, including for any commercial purposes, is strictly "
        "prohibited without our express prior written consent. Systematic retrieval of data or "
        "other content from the Services, whether to create or compile, directly or indirectly, a "
        "collection, compilation, database, or directory, is prohibited absent our express prior "
        "written consent."
    ),
    "betting_partners_integrity": (
        "All three NFL partners agreed to adhere to the league's core game integrity policies and "
        "will collaborate on intelligence sharing, advocacy efforts and responsible gambling "
        "initiatives. This includes working together to prohibit wagers the league finds "
        "objectionable, including bets tied to officiating and injuries, along with those that can "
        "be knowable in advance or easily manipulated by a single person."
    ),
}
