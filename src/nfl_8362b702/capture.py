"""Hand-captured official values for the nfl_8362b702 pack.

Every value in this module was read during this session (2026-11-15) from the
official page named beside it, via a read-only page fetch. Nothing here is
inferred, transcribed from another pack, or filled in. Where a page rendered a
value without a label (e.g. two standings columns whose headers were not
rendered), the value is stored verbatim under a ``rec_unlabeled`` field and
flagged; it is never given an invented meaning.

Reads in this module
--------------------
* STANDINGS_READ_1   — nfl.com league standings, 2026-11-15T23:26:00Z
* WEEK11_SCHED_READ  — nfl.com week-11 schedule,      2026-11-15T23:28:00Z
* TB_DET_GAME_READ   — game centre TB @ DET,          2026-11-15T23:27:00Z
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# read clocks (UTC) and source URLs
# --------------------------------------------------------------------------
CAPTURE_DATE_UTC = "2026-11-15"

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
STANDINGS_READ_1 = "2026-11-15T23:26:00Z"

WEEK11_SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
WEEK11_SCHED_READ = "2026-11-15T23:28:00Z"

TB_DET_GAME_URL = "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"
TB_DET_GAME_READ = "2026-11-15T23:27:00Z"

# --------------------------------------------------------------------------
# Standings read 1 (32 clubs). Verbatim rows of the league standings table.
# Column notes (the fetched page rendered no header row for the table; names
# below are taken from the page's own LEGEND block where the legend names them):
#   w l t pct pf pa net            — named in legend (W, L, T, PCT, PF, PA, NET PTS)
#   home_rec road_rec              — named in legend (HOME, ROAD)
#   div_rec div_pct conf_rec conf_pct — DIV / CONF pairs (legend names DIV, CONF)
#   rec_unlabeled_1                — value read verbatim; header NOT rendered
#   strk                           — named in legend (STRK)
#   rec_unlabeled_2                — value read verbatim; header NOT rendered
# --------------------------------------------------------------------------
STANDINGS_COLS = (
    "team_abbr", "team_name", "w", "l", "t", "pct", "pf", "pa", "net",
    "home_rec", "road_rec", "div_rec", "div_pct", "conf_rec", "conf_pct",
    "rec_unlabeled_1", "strk", "rec_unlabeled_2",
)

STANDINGS_READ_1_ROWS = [
    # abbr, name (as printed), W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, DIV_PCT, CONF, CONF_PCT, unlabeled_1, STRK, unlabeled_2
    ("BUF", "Buffalo Bills", 8, 1, 0, "0.889", 287, 199, 88, "3 - 1 - 0", "5 - 0 - 0", "1 - 1 - 0", "0.500", "5 - 1 - 0", "0.833", "3 - 0 - 0", "5W", "5 - 0 - 0"),
    ("SF", "San Francisco 49ers", 7, 1, 0, "0.875", 235, 156, 79, "5 - 0 - 0", "2 - 1 - 0", "3 - 0 - 0", "1.000", "4 - 1 - 0", "0.800", "3 - 0 - 0", "1W", "4 - 1 - 0"),
    ("CHI", "Chicago Bears", 7, 2, 0, "0.778", 241, 184, 57, "4 - 1 - 0", "3 - 1 - 0", "0 - 2 - 0", "0.000", "5 - 2 - 0", "0.714", "2 - 0 - 0", "4W", "4 - 1 - 0"),
    ("DEN", "Denver Broncos", 7, 2, 0, "0.778", 198, 186, 12, "4 - 0 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 1 - 0", "0.750", "4 - 1 - 0", "5W", "5 - 0 - 0"),
    ("DET", "Detroit Lions", 7, 2, 0, "0.778", 257, 199, 58, "5 - 0 - 0", "2 - 2 - 0", "2 - 0 - 0", "1.000", "4 - 1 - 0", "0.800", "3 - 1 - 0", "5W", "5 - 0 - 0"),
    ("JAX", "Jacksonville Jaguars", 7, 2, 0, "0.778", 269, 144, 125, "4 - 1 - 0", "3 - 1 - 0", "2 - 1 - 0", "0.667", "6 - 2 - 0", "0.750", "1 - 0 - 0", "3W", "4 - 1 - 0"),
    ("KC", "Kansas City Chiefs", 7, 2, 0, "0.778", 237, 156, 81, "4 - 0 - 0", "3 - 2 - 0", "3 - 1 - 0", "0.750", "6 - 1 - 0", "0.857", "1 - 1 - 0", "2W", "3 - 2 - 0"),
    ("MIN", "Minnesota Vikings", 7, 2, 0, "0.778", 176, 126, 50, "3 - 1 - 0", "4 - 2 - 0", "3 - 1 - 0", "0.750", "5 - 1 - 0", "0.833", "2 - 1 - 0", "1W", "3 - 2 - 0"),
    ("CIN", "Cincinnati Bengals", 6, 2, 0, "0.750", 240, 175, 65, "2 - 1 - 0", "4 - 1 - 0", "1 - 1 - 0", "0.500", "4 - 2 - 0", "0.667", "2 - 0 - 0", "4W", "4 - 1 - 0"),
    ("PIT", "Pittsburgh Steelers", 6, 2, 0, "0.750", 180, 144, 36, "4 - 0 - 0", "2 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 2 - 0", "0.600", "3 - 0 - 0", "4W", "4 - 1 - 0"),
    ("NYG", "New York Giants", 5, 3, 1, "0.611", 203, 196, 7, "3 - 2 - 0", "2 - 1 - 1", "2 - 1 - 1", "0.625", "3 - 3 - 1", "0.500", "2 - 0 - 0", "1L", "2 - 2 - 1"),
    ("CLE", "Cleveland Browns", 6, 4, 0, "0.600", 188, 220, -32, "4 - 0 - 0", "2 - 4 - 0", "2 - 1 - 0", "0.667", "4 - 3 - 0", "0.571", "2 - 1 - 0", "1W", "3 - 2 - 0"),
    ("GB", "Green Bay Packers", 6, 4, 0, "0.600", 226, 221, 5, "3 - 2 - 0", "3 - 2 - 0", "1 - 3 - 0", "0.250", "4 - 4 - 0", "0.500", "2 - 0 - 0", "1L", "3 - 2 - 0"),
    ("LA", "Los Angeles Rams", 5, 4, 0, "0.556", 214, 181, 33, "2 - 3 - 0", "3 - 1 - 0", "0 - 2 - 0", "0.000", "3 - 2 - 0", "0.600", "2 - 2 - 0", "3W", "3 - 2 - 0"),
    ("SEA", "Seattle Seahawks", 5, 4, 0, "0.556", 202, 162, 40, "4 - 2 - 0", "1 - 2 - 0", "2 - 1 - 0", "0.667", "2 - 3 - 0", "0.400", "3 - 1 - 0", "1W", "2 - 3 - 0"),
    ("NE", "New England Patriots", 5, 5, 0, "0.500", 221, 242, -21, "3 - 1 - 0", "2 - 4 - 0", "3 - 0 - 0", "1.000", "5 - 1 - 0", "0.833", "0 - 4 - 0", "2L", "2 - 3 - 0"),
    ("BAL", "Baltimore Ravens", 4, 5, 0, "0.444", 189, 236, -47, "1 - 3 - 0", "3 - 2 - 0", "0 - 2 - 0", "0.000", "2 - 4 - 0", "0.333", "2 - 1 - 0", "4L", "1 - 4 - 0"),
    ("CAR", "Carolina Panthers", 4, 5, 0, "0.444", 219, 236, -17, "1 - 3 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "4 - 3 - 0", "0.571", "0 - 2 - 0", "1W", "2 - 3 - 0"),
    ("DAL", "Dallas Cowboys", 4, 5, 0, "0.444", 246, 236, 10, "1 - 3 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "2 - 4 - 0", "0.333", "2 - 1 - 0", "1W", "2 - 3 - 0"),
    ("LV", "Las Vegas Raiders", 4, 5, 0, "0.444", 238, 268, -30, "1 - 3 - 0", "3 - 2 - 0", "1 - 1 - 0", "0.500", "3 - 3 - 0", "0.500", "1 - 2 - 0", "1L", "1 - 4 - 0"),
    ("WAS", "Washington Commanders", 3, 5, 1, "0.389", 196, 223, -27, "2 - 2 - 1", "1 - 3 - 0", "2 - 2 - 1", "0.500", "3 - 4 - 1", "0.438", "0 - 1 - 0", "1W", "2 - 2 - 1"),
    ("AZ", "Arizona Cardinals", 3, 6, 0, "0.333", 178, 255, -77, "0 - 3 - 0", "3 - 3 - 0", "1 - 3 - 0", "0.250", "2 - 5 - 0", "0.286", "1 - 1 - 0", "1L", "2 - 3 - 0"),
    ("HOU", "Houston Texans", 3, 6, 0, "0.333", 233, 219, 14, "0 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 4 - 0", "0.429", "0 - 2 - 0", "1L", "3 - 2 - 0"),
    ("NO", "New Orleans Saints", 3, 6, 0, "0.333", 202, 236, -34, "1 - 5 - 0", "2 - 1 - 0", "0 - 2 - 0", "0.000", "1 - 4 - 0", "0.200", "2 - 2 - 0", "1L", "2 - 3 - 0"),
    ("TB", "Tampa Bay Buccaneers", 3, 6, 0, "0.333", 202, 178, 24, "1 - 4 - 0", "2 - 2 - 0", "2 - 0 - 0", "1.000", "3 - 3 - 0", "0.500", "0 - 3 - 0", "1L", "3 - 2 - 0"),
    ("ATL", "Atlanta Falcons", 3, 7, 0, "0.300", 201, 258, -57, "1 - 5 - 0", "2 - 2 - 0", "1 - 2 - 0", "0.333", "3 - 3 - 0", "0.500", "0 - 4 - 0", "3L", "1 - 4 - 0"),
    ("IND", "Indianapolis Colts", 3, 7, 0, "0.300", 208, 271, -63, "2 - 3 - 0", "1 - 4 - 0", "1 - 2 - 0", "0.333", "2 - 5 - 0", "0.286", "1 - 2 - 0", "1W", "1 - 4 - 0"),
    ("PHI", "Philadelphia Eagles", 2, 7, 0, "0.222", 148, 221, -73, "1 - 4 - 0", "1 - 3 - 0", "1 - 3 - 0", "0.250", "1 - 6 - 0", "0.143", "1 - 1 - 0", "7L", "0 - 5 - 0"),
    ("NYJ", "New York Jets", 2, 8, 0, "0.200", 194, 254, -60, "1 - 4 - 0", "1 - 4 - 0", "0 - 3 - 0", "0.000", "2 - 5 - 0", "0.286", "0 - 3 - 0", "5L", "0 - 5 - 0"),
    ("MIA", "Miami Dolphins", 1, 8, 0, "0.111", 148, 224, -76, "0 - 4 - 0", "1 - 4 - 0", "1 - 1 - 0", "0.500", "1 - 5 - 0", "0.167", "0 - 3 - 0", "3L", "1 - 4 - 0"),
    ("TEN", "Tennessee Titans", 1, 8, 0, "0.111", 167, 239, -72, "0 - 5 - 0", "1 - 3 - 0", "1 - 2 - 0", "0.333", "1 - 6 - 0", "0.143", "0 - 2 - 0", "3L", "1 - 4 - 0"),
    ("LAC", "Los Angeles Chargers", 0, 8, 0, "0.000", 121, 219, -98, "0 - 4 - 0", "0 - 4 - 0", "0 - 3 - 0", "0.000", "0 - 5 - 0", "0.000", "0 - 3 - 0", "8L", "0 - 5 - 0"),
]

# --------------------------------------------------------------------------
# Week 11 schedule (13 fixtures + 6 bye clubs). Verbatim from the card text:
# e.g. "Colts at Texans, Thursday, November 19th, 8:15 PM, PRIME".
# kickoff_on_card is the card's own string; the page's TBD note block writes
# times with an explicit "ET" suffix ("4:30 PM ET"), so ET is the page's own
# convention, but the individual card prints no zone and none is invented.
# Records are as printed next to each club on the card at read time.
# --------------------------------------------------------------------------
WEEK11_COLS = (
    "game_id", "slug", "date_on_card", "kickoff_on_card", "network_on_card",
    "away", "home", "away_record_on_card", "home_record_on_card",
    "event_mark_on_card", "game_page_url",
)

WEEK11_GAMES = [
    ("W11-01", "colts-at-texans-2026-reg-11", "Thursday, November 19th", "8:15 PM", "PRIME",
     "IND", "HOU", "3 - 7", "3 - 6", "", "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
    ("W11-02", "dolphins-at-bills-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "CBS",
     "MIA", "BUF", "1 - 8", "8 - 1", "", "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11"),
    ("W11-03", "ravens-at-panthers-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "FOX",
     "BAL", "CAR", "4 - 5", "4 - 5", "", "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11"),
    ("W11-04", "saints-at-bears-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "FOX",
     "NO", "CHI", "3 - 6", "7 - 2", "", "https://www.nfl.com/games/saints-at-bears-2026-reg-11"),
    ("W11-05", "titans-at-cowboys-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "FOX",
     "TEN", "DAL", "1 - 8", "4 - 5", "", "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11"),
    ("W11-06", "buccaneers-at-lions-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "FOX",
     "TB", "DET", "3 - 6", "7 - 2", "", "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
    ("W11-07", "cardinals-at-chiefs-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "CBS",
     "AZ", "KC", "3 - 6", "7 - 2", "", "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11"),
    ("W11-08", "steelers-at-eagles-2026-reg-11", "Sunday, November 22nd", "1:00 PM", "CBS",
     "PIT", "PHI", "6 - 2", "2 - 7", "", "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11"),
    ("W11-09", "jets-at-chargers-2026-reg-11", "Sunday, November 22nd", "4:05 PM", "FOX",
     "NYJ", "LAC", "2 - 8", "0 - 8", "", "https://www.nfl.com/games/jets-at-chargers-2026-reg-11"),
    ("W11-10", "jaguars-at-giants-2026-reg-11", "Sunday, November 22nd", "4:25 PM", "CBS",
     "JAX", "NYG", "7 - 2", "5 - 3 - 1", "", "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11"),
    ("W11-11", "raiders-at-broncos-2026-reg-11", "Sunday, November 22nd", "4:25 PM", "CBS",
     "LV", "DEN", "4 - 5", "7 - 2", "", "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11"),
    ("W11-12", "vikings-at-49ers-2026-reg-11", "Sunday, November 22nd", "8:20 PM", "NBC",
     "MIN", "SF", "7 - 2", "7 - 1", "Mexico City 2026 (event mark printed above the card)",
     "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"),
    ("W11-13", "bengals-at-commanders-2026-reg-11", "Monday, November 23rd", "8:15 PM", "ESPN",
     "CIN", "WAS", "6 - 2", "3 - 5 - 1", "", "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11"),
]

# "Teams on Bye" panel of the week-11 page (club abbr as printed, record as
# printed at render time — the panel is not a week-ending record).
WEEK11_BYES = [
    ("ATL", "Atlanta Falcons", "3 - 7"),
    ("CLE", "Cleveland Browns", "6 - 4"),
    ("GB", "Green Bay Packers", "6 - 4"),
    ("LA", "Los Angeles Rams", "5 - 4"),
    ("NE", "New England Patriots", "5 - 5"),
    ("SEA", "Seattle Seahawks", "5 - 4"),
]

# The week-11 page's own TBD-scheduling note prints times with an explicit ET
# suffix; captured verbatim (trimmed) as the evidence for the ET convention.
WEEK11_TIMEZONE_NOTE = (
    "The page's 2026 TBD Games note writes times as '4:30 PM ET' and '8:00 PM ET'; "
    "individual game cards print no zone. ET is the page's convention, not an "
    "invention of this pack."
)
WEEK11_TIMEZONE_NOTE_URL = WEEK11_SCHED_URL

# --------------------------------------------------------------------------
# Game-centre read: TB @ DET (week 11). The Game Info block prints:
#   Location  LOCATION  DETROIT, MI
#   Stadium   STADIUM   FORD FIELD
# This is the first of the 13 week-11 venues; the rest are captured in
# VENUE_READS below as their game-centre pages are read (see capture_notes).
# --------------------------------------------------------------------------
TB_DET_GAME_INFO = {
    "game_id": "W11-06",
    "location_on_page": "DETROIT, MI",
    "stadium_on_page": "FORD FIELD",
    "network_on_page": "FOX",
    "kickoff_on_page": "Nov 22 1:00PM",
    "injury_report_block": "Buccaneers' and Lions' Injury Reports are not available at this time",
}

# --------------------------------------------------------------------------
# Week 10 schedule (14 fixtures + 4 bye clubs), read 2026-11-15T23:35:00Z.
# Cards print "Commanders 24, Giants 21, FINAL, Thursday, November 12th" for
# finals; live cards print the in-progress quarter instead of FINAL and are
# stored with their on-card status string. Only cards whose own text says
# FINAL are results; nothing is settled from a live score.
# --------------------------------------------------------------------------
WEEK10_SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
WEEK10_SCHED_READ = "2026-11-15T23:35:00Z"

WEEK10_COLS = (
    "game_id", "slug", "date_on_card", "status_on_card", "away", "home",
    "away_score_on_card", "home_score_on_card", "event_mark_on_card",
    "game_page_url",
)

WEEK10_GAMES = [
    ("W10-01", "commanders-at-giants-2026-reg-10", "Thursday, November 12th", "FINAL",
     "WAS", "NYG", 24, 21, "", "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"),
    ("W10-02", "patriots-at-lions-2026-reg-10", "Sunday, November 15th", "FINAL",
     "NE", "DET", 10, 35, "Munich 2026 (event mark printed above the card)",
     "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"),
    ("W10-03", "chiefs-at-falcons-2026-reg-10", "Sunday, November 15th", "FINAL",
     "KC", "ATL", 35, 13, "", "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10"),
    ("W10-04", "texans-at-browns-2026-reg-10", "Sunday, November 15th", "FINAL",
     "HOU", "CLE", 24, 27, "", "https://www.nfl.com/games/texans-at-browns-2026-reg-10"),
    ("W10-05", "vikings-at-packers-2026-reg-10", "Sunday, November 15th", "FINAL",
     "MIN", "GB", 30, 10, "", "https://www.nfl.com/games/vikings-at-packers-2026-reg-10"),
    ("W10-06", "dolphins-at-colts-2026-reg-10", "Sunday, November 15th", "FINAL",
     "MIA", "IND", 22, 24, "", "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10"),
    ("W10-07", "panthers-at-saints-2026-reg-10", "Sunday, November 15th", "FINAL",
     "CAR", "NO", 20, 17, "", "https://www.nfl.com/games/panthers-at-saints-2026-reg-10"),
    ("W10-08", "bills-at-jets-2026-reg-10", "Sunday, November 15th", "FINAL",
     "BUF", "NYJ", 31, 12, "", "https://www.nfl.com/games/bills-at-jets-2026-reg-10"),
    ("W10-09", "jaguars-at-titans-2026-reg-10", "Sunday, November 15th", "FINAL",
     "JAX", "TEN", 40, 23, "", "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10"),
    # The next three cards were live at read time. The score strings are kept
    # verbatim with the on-card quarter so no live score is ever treated as a
    # result; the result columns stay empty until a card prints FINAL.
    ("W10-10", "rams-at-cardinals-2026-reg-10", "Sunday, November 15th", "Q4 (live at read)",
     "LA", "AZ", None, None, "", "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10"),
    ("W10-11", "seahawks-at-raiders-2026-reg-10", "Sunday, November 15th", "Q4 (live at read)",
     "SEA", "LV", None, None, "", "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10"),
    ("W10-12", "49ers-at-cowboys-2026-reg-10", "Sunday, November 15th", "Q3 (live at read)",
     "SF", "DAL", None, None, "", "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10"),
    ("W10-13", "steelers-at-bengals-2026-reg-10", "Sunday, November 15th", "scheduled (8:20 PM)",
     "PIT", "CIN", None, None, "", "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10"),
    ("W10-14", "chargers-at-ravens-2026-reg-10", "Monday, November 16th", "scheduled (8:15 PM)",
     "LAC", "BAL", None, None, "", "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"),
]

# Live cards at read time carried these score strings verbatim (not results).
WEEK10_LIVE_SCORE_STRINGS = {
    "W10-10": ("Rams 34, Cardinals 6, Q4", "34", "6"),
    "W10-11": ("Seahawks 21, Raiders 10, Q4", "21", "10"),
    "W10-12": ("49ers 24, Cowboys 19, Q3", "24", "19"),
}

WEEK10_BYES = [
    ("CHI", "Chicago Bears", "7 - 2"),
    ("DEN", "Denver Broncos", "7 - 2"),
    ("PHI", "Philadelphia Eagles", "2 - 7"),
    ("TB", "Tampa Bay Buccaneers", "3 - 6"),
]

# --------------------------------------------------------------------------
# The 136-game log (weeks 1-9, 2026) — pre-registered backtest corpus.
# Each week is transcribed verbatim from its official weekly schedule page
# card text ("Jaguars 33, Ravens 10, FINAL, Thursday, November 5th"). Only
# cards whose own text says FINAL are recorded as results.
# --------------------------------------------------------------------------
WEEKSCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-{}"
WEEKSCHED_READ = "2026-11-15T23:45:00Z"  # batch read clock for weeks 1-9 pages

# (week, game_no, slug, date_on_card, away, home, away_score, home_score, event_mark)
LOG136 = [
    # ---- week 9 (read 2026-11-15T23:45Z) : 15 games, byes PIT TEN ----
    (9, 1, "jaguars-at-ravens-2026-reg-9", "Thursday, November 5th", "JAX", "BAL", 33, 10, ""),
    (9, 2, "bengals-at-falcons-2026-reg-9", "Sunday, November 8th", "CIN", "ATL", 34, 17, "Madrid 2026 (event mark printed above the card)"),
    (9, 3, "broncos-at-panthers-2026-reg-9", "Sunday, November 8th", "DEN", "CAR", 26, 21, ""),
    (9, 4, "cowboys-at-colts-2026-reg-9", "Sunday, November 8th", "DAL", "IND", 27, 23, ""),
    (9, 5, "jets-at-chiefs-2026-reg-9", "Sunday, November 8th", "NYJ", "KC", 12, 35, ""),
    (9, 6, "lions-at-dolphins-2026-reg-9", "Sunday, November 8th", "DET", "MIA", 19, 9, ""),
    (9, 7, "browns-at-saints-2026-reg-9", "Sunday, November 8th", "CLE", "NO", 22, 23, ""),
    (9, 8, "giants-at-eagles-2026-reg-9", "Sunday, November 8th", "NYG", "PHI", 19, 11, ""),
    (9, 9, "rams-at-commanders-2026-reg-9", "Sunday, November 8th", "LA", "WAS", 20, 13, ""),
    (9, 10, "texans-at-chargers-2026-reg-9", "Sunday, November 8th", "HOU", "LAC", 44, 22, ""),
    (9, 11, "raiders-at-49ers-2026-reg-9", "Sunday, November 8th", "LV", "SF", 17, 38, ""),
    (9, 12, "packers-at-patriots-2026-reg-9", "Sunday, November 8th", "GB", "NE", 45, 27, ""),
    (9, 13, "cardinals-at-seahawks-2026-reg-9", "Sunday, November 8th", "AZ", "SEA", 3, 17, ""),
    (9, 14, "buccaneers-at-bears-2026-reg-9", "Sunday, November 8th", "TB", "CHI", 24, 27, "SNF card"),
    (9, 15, "bills-at-vikings-2026-reg-9", "Monday, November 9th", "BUF", "MIN", 23, 6, "MNF card"),
]

WEEK9_BYES = [("PIT", "Pittsburgh Steelers", "6 - 2"), ("TEN", "Tennessee Titans", "1 - 8")]

LOG136 += [
    # ---- week 8 (14 games, byes HOU NO NYG SF) ----
    (8, 1, "panthers-at-packers-2026-reg-8", "Thursday, October 29th", "CAR", "GB", 19, 27, ""),
    (8, 2, "ravens-at-bills-2026-reg-8", "Sunday, November 1st", "BAL", "BUF", 10, 36, ""),
    (8, 3, "titans-at-bengals-2026-reg-8", "Sunday, November 1st", "TEN", "CIN", 36, 43, ""),
    (8, 4, "cardinals-at-cowboys-2026-reg-8", "Sunday, November 1st", "AZ", "DAL", 33, 30, ""),
    (8, 5, "vikings-at-lions-2026-reg-8", "Sunday, November 1st", "MIN", "DET", 15, 19, ""),
    (8, 6, "colts-at-jaguars-2026-reg-8", "Sunday, November 1st", "IND", "JAX", 7, 42, ""),
    (8, 7, "raiders-at-jets-2026-reg-8", "Sunday, November 1st", "LV", "NYJ", 38, 33, ""),
    (8, 8, "browns-at-steelers-2026-reg-8", "Sunday, November 1st", "CLE", "PIT", 6, 27, ""),
    (8, 9, "falcons-at-buccaneers-2026-reg-8", "Sunday, November 1st", "ATL", "TB", 0, 16, ""),
    (8, 10, "chargers-at-rams-2026-reg-8", "Sunday, November 1st", "LAC", "LA", 9, 24, ""),
    (8, 11, "chiefs-at-broncos-2026-reg-8", "Sunday, November 1st", "KC", "DEN", 24, 28, ""),
    (8, 12, "patriots-at-dolphins-2026-reg-8", "Sunday, November 1st", "NE", "MIA", 24, 19, ""),
    (8, 13, "eagles-at-commanders-2026-reg-8", "Sunday, November 1st", "PHI", "WAS", 10, 27, "SNF card"),
    (8, 14, "bears-at-seahawks-2026-reg-8", "Monday, November 2nd", "CHI", "SEA", 34, 17, "MNF card"),
]
WEEK8_BYES = [("HOU", "Houston Texans"), ("NO", "New Orleans Saints"),
              ("NYG", "New York Giants"), ("SF", "San Francisco 49ers")]

LOG136 += [
    # ---- week 7 (14 games, byes BUF JAX LAC WAS) ----
    (7, 1, "patriots-at-bears-2026-reg-7", "Thursday, October 22nd", "NE", "CHI", 24, 30, ""),
    (7, 2, "steelers-at-saints-2026-reg-7", "Sunday, October 25th", "PIT", "NO", 16, 10, "Saint-Denis 2026 (event mark printed above the card)"),
    (7, 3, "49ers-at-falcons-2026-reg-7", "Sunday, October 25th", "SF", "ATL", 20, 29, ""),
    (7, 4, "bengals-at-ravens-2026-reg-7", "Sunday, October 25th", "CIN", "BAL", 35, 13, ""),
    (7, 5, "buccaneers-at-panthers-2026-reg-7", "Sunday, October 25th", "TB", "CAR", 43, 13, ""),
    (7, 6, "giants-at-texans-2026-reg-7", "Sunday, October 25th", "NYG", "HOU", 27, 21, ""),
    (7, 7, "colts-at-vikings-2026-reg-7", "Sunday, October 25th", "IND", "MIN", 10, 16, ""),
    (7, 8, "dolphins-at-jets-2026-reg-7", "Sunday, October 25th", "MIA", "NYJ", 28, 25, ""),
    (7, 9, "browns-at-titans-2026-reg-7", "Sunday, October 25th", "CLE", "TEN", 27, 24, ""),
    (7, 10, "broncos-at-cardinals-2026-reg-7", "Sunday, October 25th", "DEN", "AZ", 30, 16, ""),
    (7, 11, "packers-at-lions-2026-reg-7", "Sunday, October 25th", "GB", "DET", 17, 20, ""),
    (7, 12, "rams-at-raiders-2026-reg-7", "Sunday, October 25th", "LA", "LV", 35, 21, ""),
    (7, 13, "chiefs-at-seahawks-2026-reg-7", "Sunday, October 25th", "KC", "SEA", 3, 20, "SNF card"),
    (7, 14, "cowboys-at-eagles-2026-reg-7", "Monday, October 26th", "DAL", "PHI", 38, 21, "MNF card"),
]

LOG136 += [
    # ---- week 6 (14 games, byes CIN DET MIA MIN) ----
    (6, 1, "seahawks-at-broncos-2026-reg-6", "Thursday, October 15th", "SEA", "DEN", 14, 17, ""),
    (6, 2, "texans-at-jaguars-2026-reg-6", "Sunday, October 18th", "HOU", "JAX", 34, 31, "London 2026 (event mark printed above the card)"),
    (6, 3, "bears-at-falcons-2026-reg-6", "Sunday, October 18th", "CHI", "ATL", 31, 23, ""),
    (6, 4, "ravens-at-browns-2026-reg-6", "Sunday, October 18th", "BAL", "CLE", 10, 13, ""),
    (6, 5, "titans-at-colts-2026-reg-6", "Sunday, October 18th", "TEN", "IND", 26, 20, ""),
    (6, 6, "jets-at-patriots-2026-reg-6", "Sunday, October 18th", "NYJ", "NE", 19, 26, ""),
    (6, 7, "saints-at-giants-2026-reg-6", "Sunday, October 18th", "NO", "NYG", 34, 27, ""),
    (6, 8, "panthers-at-eagles-2026-reg-6", "Sunday, October 18th", "CAR", "PHI", 25, 14, ""),
    (6, 9, "steelers-at-buccaneers-2026-reg-6", "Sunday, October 18th", "PIT", "TB", 26, 19, ""),
    (6, 10, "cardinals-at-rams-2026-reg-6", "Sunday, October 18th", "AZ", "LA", 18, 16, ""),
    (6, 11, "chargers-at-chiefs-2026-reg-6", "Sunday, October 18th", "LAC", "KC", 6, 22, ""),
    (6, 12, "bills-at-raiders-2026-reg-6", "Sunday, October 18th", "BUF", "LV", 33, 30, ""),
    (6, 13, "cowboys-at-packers-2026-reg-6", "Sunday, October 18th", "DAL", "GB", 13, 23, "SNF card"),
    (6, 14, "commanders-at-49ers-2026-reg-6", "Monday, October 19th", "WAS", "SF", 17, 23, "MNF card"),
]

LOG136 += [
    # ---- week 5 (15 games, byes CAR KC; includes the season's only tie) ----
    (5, 1, "buccaneers-at-cowboys-2026-reg-5", "Thursday, October 8th", "TB", "DAL", 24, 16, ""),
    (5, 2, "eagles-at-jaguars-2026-reg-5", "Sunday, October 11th", "PHI", "JAX", 17, 19, "London 2026 (event mark printed above the card)"),
    (5, 3, "bengals-at-dolphins-2026-reg-5", "Sunday, October 11th", "CIN", "MIA", 31, 24, ""),
    (5, 4, "raiders-at-patriots-2026-reg-5", "Sunday, October 11th", "LV", "NE", 17, 45, ""),
    (5, 5, "vikings-at-saints-2026-reg-5", "Sunday, October 11th", "MIN", "NO", 23, 13, ""),
    (5, 6, "browns-at-jets-2026-reg-5", "Sunday, October 11th", "CLE", "NYJ", 12, 17, ""),
    (5, 7, "colts-at-steelers-2026-reg-5", "Sunday, October 11th", "IND", "PIT", 22, 34, ""),
    (5, 8, "texans-at-titans-2026-reg-5", "Sunday, October 11th", "HOU", "TEN", 26, 3, ""),
    (5, 9, "giants-at-commanders-2026-reg-5", "Sunday, October 11th", "NYG", "WAS", 27, 27, "tie game (card prints FINAL with equal scores)"),
    (5, 10, "bears-at-packers-2026-reg-5", "Sunday, October 11th", "CHI", "GB", 7, 31, ""),
    (5, 11, "broncos-at-chargers-2026-reg-5", "Sunday, October 11th", "DEN", "LAC", 23, 17, ""),
    (5, 12, "lions-at-cardinals-2026-reg-5", "Sunday, October 11th", "DET", "AZ", 45, 21, ""),
    (5, 13, "49ers-at-seahawks-2026-reg-5", "Sunday, October 11th", "SF", "SEA", 32, 29, ""),
    (5, 14, "ravens-at-falcons-2026-reg-5", "Sunday, October 11th", "BAL", "ATL", 30, 23, "SNF card"),
    (5, 15, "bills-at-rams-2026-reg-5", "Monday, October 12th", "BUF", "LA", 37, 34, "MNF card"),
]

LOG136 += [
    # ---- week 4 (16 games, no byes) ----
    (4, 1, "steelers-at-browns-2026-reg-4", "Thursday, October 1st", "PIT", "CLE", 24, 27, ""),
    (4, 2, "colts-at-commanders-2026-reg-4", "Sunday, October 4th", "IND", "WAS", 30, 13, "London 2026 (event mark printed above the card)"),
    (4, 3, "titans-at-ravens-2026-reg-4", "Sunday, October 4th", "TEN", "BAL", 18, 24, ""),
    (4, 4, "patriots-at-bills-2026-reg-4", "Sunday, October 4th", "NE", "BUF", 29, 26, ""),
    (4, 5, "jets-at-bears-2026-reg-4", "Sunday, October 4th", "NYJ", "CHI", 12, 23, ""),
    (4, 6, "jaguars-at-bengals-2026-reg-4", "Sunday, October 4th", "JAX", "CIN", 22, 17, ""),
    (4, 7, "cowboys-at-texans-2026-reg-4", "Sunday, October 4th", "DAL", "HOU", 34, 30, ""),
    (4, 8, "cardinals-at-giants-2026-reg-4", "Sunday, October 4th", "AZ", "NYG", 24, 36, ""),
    (4, 9, "rams-at-eagles-2026-reg-4", "Sunday, October 4th", "LA", "PHI", 24, 20, ""),
    (4, 10, "packers-at-buccaneers-2026-reg-4", "Sunday, October 4th", "GB", "TB", 17, 14, ""),
    (4, 11, "dolphins-at-vikings-2026-reg-4", "Sunday, October 4th", "MIA", "MIN", 10, 15, ""),
    (4, 12, "chiefs-at-raiders-2026-reg-4", "Sunday, October 4th", "KC", "LV", 30, 27, ""),
    (4, 13, "chargers-at-seahawks-2026-reg-4", "Sunday, October 4th", "LAC", "SEA", 23, 30, ""),
    (4, 14, "broncos-at-49ers-2026-reg-4", "Sunday, October 4th", "DEN", "SF", 14, 24, ""),
    (4, 15, "lions-at-panthers-2026-reg-4", "Sunday, October 4th", "DET", "CAR", 26, 32, "SNF card"),
    (4, 16, "falcons-at-saints-2026-reg-4", "Monday, October 5th", "ATL", "NO", 45, 24, "MNF card"),
]

LOG136 += [
    # ---- week 3 (16 games, no byes) ----
    (3, 1, "falcons-at-packers-2026-reg-3", "Thursday, September 24th", "ATL", "GB", 35, 14, ""),
    (3, 2, "chargers-at-bills-2026-reg-3", "Sunday, September 27th", "LAC", "BUF", 16, 24, ""),
    (3, 3, "panthers-at-browns-2026-reg-3", "Sunday, September 27th", "CAR", "CLE", 18, 21, ""),
    (3, 4, "jets-at-lions-2026-reg-3", "Sunday, September 27th", "NYJ", "DET", 24, 31, ""),
    (3, 5, "texans-at-colts-2026-reg-3", "Sunday, September 27th", "HOU", "IND", 17, 19, ""),
    (3, 6, "patriots-at-jaguars-2026-reg-3", "Sunday, September 27th", "NE", "JAX", 6, 35, ""),
    (3, 7, "chiefs-at-dolphins-2026-reg-3", "Sunday, September 27th", "KC", "MIA", 24, 10, ""),
    (3, 8, "titans-at-giants-2026-reg-3", "Sunday, September 27th", "TEN", "NYG", 7, 12, ""),
    (3, 9, "bengals-at-steelers-2026-reg-3", "Sunday, September 27th", "CIN", "PIT", 27, 30, ""),
    (3, 10, "seahawks-at-commanders-2026-reg-3", "Sunday, September 27th", "SEA", "WAS", 31, 33, ""),
    (3, 11, "cardinals-at-49ers-2026-reg-3", "Sunday, September 27th", "AZ", "SF", 30, 36, ""),
    (3, 12, "vikings-at-buccaneers-2026-reg-3", "Sunday, September 27th", "MIN", "TB", 23, 16, ""),
    (3, 13, "raiders-at-saints-2026-reg-3", "Sunday, September 27th", "LV", "NO", 35, 27, ""),
    (3, 14, "ravens-at-cowboys-2026-reg-3", "Sunday, September 27th", "BAL", "DAL", 34, 31, "Rio de Janeiro 2026 (event mark printed above the card)"),
    (3, 15, "rams-at-broncos-2026-reg-3", "Sunday, September 27th", "LA", "DEN", 26, 30, "SNF card"),
    (3, 16, "eagles-at-bears-2026-reg-3", "Monday, September 28th", "PHI", "CHI", 7, 27, "MNF card"),
]

LOG136 += [
    # ---- week 2 (16 games, no byes) ----
    (2, 1, "lions-at-bills-2026-reg-2", "Thursday, September 17th", "DET", "BUF", 31, 41, ""),
    (2, 2, "panthers-at-falcons-2026-reg-2", "Sunday, September 20th", "CAR", "ATL", 34, 3, ""),
    (2, 3, "saints-at-ravens-2026-reg-2", "Sunday, September 20th", "NO", "BAL", 24, 17, ""),
    (2, 4, "vikings-at-bears-2026-reg-2", "Sunday, September 20th", "MIN", "CHI", 9, 3, ""),
    (2, 5, "bengals-at-texans-2026-reg-2", "Sunday, September 20th", "CIN", "HOU", 20, 6, ""),
    (2, 6, "steelers-at-patriots-2026-reg-2", "Sunday, September 20th", "PIT", "NE", 3, 20, ""),
    (2, 7, "packers-at-jets-2026-reg-2", "Sunday, September 20th", "GB", "NYJ", 20, 17, ""),
    (2, 8, "browns-at-buccaneers-2026-reg-2", "Sunday, September 20th", "CLE", "TB", 23, 19, ""),
    (2, 9, "eagles-at-titans-2026-reg-2", "Sunday, September 20th", "PHI", "TEN", 24, 20, ""),
    (2, 10, "jaguars-at-broncos-2026-reg-2", "Sunday, September 20th", "JAX", "DEN", 13, 20, ""),
    (2, 11, "raiders-at-chargers-2026-reg-2", "Sunday, September 20th", "LV", "LAC", 26, 14, ""),
    (2, 12, "seahawks-at-cardinals-2026-reg-2", "Sunday, September 20th", "SEA", "AZ", 31, 7, ""),
    (2, 13, "commanders-at-cowboys-2026-reg-2", "Sunday, September 20th", "WAS", "DAL", 20, 37, ""),
    (2, 14, "dolphins-at-49ers-2026-reg-2", "Sunday, September 20th", "MIA", "SF", 13, 35, ""),
    (2, 15, "colts-at-chiefs-2026-reg-2", "Sunday, September 20th", "IND", "KC", 30, 33, "SNF card"),
    (2, 16, "giants-at-rams-2026-reg-2", "Monday, September 21st", "NYG", "LA", 6, 28, "MNF card"),
]

LOG136 += [
    # ---- week 1 (16 games, no byes). Card 1 carries an on-page oddity kept
    # verbatim: the SNF header reads "Sunday Night Football, September 9th"
    # while the game card's own date line reads "Wednesday, September 9th".
    (1, 1, "patriots-at-seahawks-2026-reg-1", "Wednesday, September 9th", "NE", "SEA", 10, 13,
     "SNF header on page reads 'Sunday Night Football, September 9th'; card date line reads 'Wednesday, September 9th' (kept verbatim; flagged)"),
    (1, 2, "49ers-at-rams-2026-reg-1", "Thursday, September 10th", "SF", "LA", 27, 7, "East Melbourne 2026 (event mark printed above the card)"),
    (1, 3, "bears-at-panthers-2026-reg-1", "Sunday, September 13th", "CHI", "CAR", 59, 37, ""),
    (1, 4, "buccaneers-at-bengals-2026-reg-1", "Sunday, September 13th", "TB", "CIN", 27, 33, ""),
    (1, 5, "saints-at-lions-2026-reg-1", "Sunday, September 13th", "NO", "DET", 30, 31, ""),
    (1, 6, "bills-at-texans-2026-reg-1", "Sunday, September 13th", "BUF", "HOU", 36, 31, ""),
    (1, 7, "ravens-at-colts-2026-reg-1", "Sunday, September 13th", "BAL", "IND", 41, 23, ""),
    (1, 8, "browns-at-jaguars-2026-reg-1", "Sunday, September 13th", "CLE", "JAX", 10, 34, ""),
    (1, 9, "falcons-at-steelers-2026-reg-1", "Sunday, September 13th", "ATL", "PIT", 13, 20, ""),
    (1, 10, "jets-at-titans-2026-reg-1", "Sunday, September 13th", "NYJ", "TEN", 23, 10, ""),
    (1, 11, "cardinals-at-chargers-2026-reg-1", "Sunday, September 13th", "AZ", "LAC", 26, 14, ""),
    (1, 12, "dolphins-at-raiders-2026-reg-1", "Sunday, September 13th", "MIA", "LV", 13, 27, ""),
    (1, 13, "packers-at-vikings-2026-reg-1", "Sunday, September 13th", "GB", "MIN", 22, 39, ""),
    (1, 14, "commanders-at-eagles-2026-reg-1", "Sunday, September 13th", "WAS", "PHI", 22, 24, ""),
    (1, 15, "cowboys-at-giants-2026-reg-1", "Sunday, September 13th", "DAL", "NYG", 20, 28, "SNF card"),
    (1, 16, "broncos-at-chiefs-2026-reg-1", "Monday, September 14th", "DEN", "KC", 10, 31, "MNF card"),
]

# --------------------------------------------------------------------------
# Injury hub read A (https://www.nfl.com/injuries/, 2026-11-15T23:58:00Z).
# The hub renders "Injuries - WEEK 10" grouped by game. Rows below are the
# complete club tables of chunks 0-2 of the page read (13 clubs). Columns are
# the page's own: Player | Position | Injuries | Practice Status | Game Status.
# Read B of the same chunks is taken later in the session for the delta panel.
# --------------------------------------------------------------------------
INJURY_URL = "https://www.nfl.com/injuries/"
INJURY_READ_A = "2026-11-15T23:58:00Z"
INJURY_READ_A_WINDOW = "chunks 0-2 (clubs WAS NYG NE DET KC ATL MIN GB JAX TEN BUF NYJ MIA)"

# (hub_game_id, club, player, position, injury_text, practice_status, game_status)
INJURY_ROWS_A = [
    ("W10-01", "WAS", "John Bates", "TE", "", "Full Participation in Practice", ""),
    ("W10-01", "WAS", "Treylon Burks", "WR", "", "Did Not Participate In Practice", ""),
    ("W10-01", "WAS", "Jayden Daniels", "QB", "", "Full Participation in Practice", ""),
    ("W10-01", "WAS", "Matt Gulbin", "C", "", "Full Participation in Practice", ""),
    ("W10-01", "WAS", "Chig Okonkwo", "TE", "", "Full Participation in Practice", ""),
    ("W10-01", "WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("W10-01", "WAS", "Amik Robertson", "CB", "", "Limited Participation in Practice", ""),
    ("W10-01", "WAS", "Shy Tuttle", "DT", "", "Full Participation in Practice", ""),
    ("W10-01", "WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    ("W10-01", "NYG", "Abdul Carter", "LB", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Jermaine Eluemunor", "T", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Malik Harrison", "LB", "Groin", "Limited Participation in Practice", "Questionable"),
    ("W10-01", "NYG", "Colton Hood", "CB", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Theo Johnson", "TE", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Charlie Jones", "WR", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "J.J. McCarthy", "QB", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Darnell Mooney", "WR", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Malik Nabers", "WR", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Cam Skattebo", "RB", "", "Full Participation in Practice", ""),
    ("W10-01", "NYG", "Andrew Thomas", "T", "", "Full Participation in Practice", ""),
    ("W10-02", "NE", "Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
    ("W10-02", "NE", "A.J. Brown", "WR", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Kevin Byard", "S", "Chest", "Full Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
    ("W10-02", "NE", "Reggie Gilliam", "FB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "NE", "TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
    ("W10-02", "NE", "Hunter Henry", "TE", "", "Limited Participation in Practice", ""),
    ("W10-02", "NE", "Cameron Latu", "TE", "Back", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Drake Maye", "QB", "", "Full Participation in Practice", ""),
    ("W10-02", "NE", "Morgan Moses", "T", "", "Full Participation in Practice", ""),
    ("W10-02", "NE", "Walter Rouse", "T", "Concussion", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Brenden Schooler", "S", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Rhamondre Stevenson", "RB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Greg Van Roten", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("W10-02", "NE", "Charles Woods", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("W10-02", "DET", "Brian Branch", "S", "", "Full Participation in Practice", ""),
    ("W10-02", "DET", "Jared Goff", "QB", "", "Full Participation in Practice", ""),
    ("W10-02", "DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
    ("W10-02", "DET", "Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("W10-02", "DET", "D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
    ("W10-02", "DET", "Jacob Saylors", "RB", "", "Full Participation in Practice", ""),
    ("W10-02", "DET", "Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "DET", "Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("W10-02", "DET", "DJ Wonnum", "DE", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Jeffrey Bassa", "LB", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Mansoor Delane", "CB", "Shoulder", "Full Participation in Practice", "Questionable"),
    ("W10-03", "KC", "Justin Fields", "QB", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Jaden Hicks", "S", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Travis Kelce", "TE", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Patrick Mahomes", "QB", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Jaylon Moore", "T", "Ankle", "Did Not Participate In Practice", "Out"),
    ("W10-03", "KC", "Omarr Norman-Lott", "DT", "Knee", "Limited Participation in Practice", "Out"),
    ("W10-03", "KC", "Jaydn Ott", "RB", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("W10-03", "KC", "Rashee Rice", "WR", "", "Full Participation in Practice", ""),
    ("W10-03", "KC", "Kenneth Walker III", "RB", "Groin", "Did Not Participate In Practice", "Questionable"),
    ("W10-03", "KC", "Peter Woods", "DT", "Neck", "Did Not Participate In Practice", "Out"),
    ("W10-03", "KC", "Xavier Worthy", "WR", "", "Full Participation in Practice", ""),
    ("W10-03", "ATL", "Zachariah Branch", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("W10-03", "ATL", "Kendal Daniels", "LB", "", "Full Participation in Practice", ""),
    ("W10-03", "ATL", "Divine Deablo", "LB", "Forearm", "Did Not Participate In Practice", "Doubtful"),
    ("W10-03", "ATL", "Gervon Dexter Sr.", "DT", "Illness", "Limited Participation in Practice", "Questionable"),
    ("W10-03", "ATL", "Jake Matthews", "T", "", "Limited Participation in Practice", ""),
    ("W10-03", "ATL", "Liam McCullough", "LS", "", "Did Not Participate In Practice", ""),
    ("W10-03", "ATL", "James Pearce Jr.", "DE", "Back", "Limited Participation in Practice", "Questionable"),
    ("W10-03", "ATL", "Za'Darius Smith", "DE", "", "Full Participation in Practice", ""),
    ("W10-03", "ATL", "Jawaan Taylor", "T", "", "Limited Participation in Practice", ""),
    ("W10-03", "ATL", "Cameron Thomas", "DE", "", "Full Participation in Practice", ""),
    ("W10-03", "ATL", "Josh Woods", "LB", "Ankle", "Full Participation in Practice", "Questionable"),
    ("W10-05", "MIN", "Jordan Addison", "WR", "Thumb", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "MIN", "Blake Cashman", "LB", "Concussion", "Limited Participation in Practice", "Out"),
    ("W10-05", "MIN", "Christian Darrisaw", "T", "", "Did Not Participate In Practice", ""),
    ("W10-05", "MIN", "T.J. Hockenson", "TE", "Wrist, Chest", "Did Not Participate In Practice", "Out"),
    ("W10-05", "MIN", "Tyrion Ingram-Dawkins", "DT", "Ankle", "Did Not Participate In Practice", "Out"),
    ("W10-05", "MIN", "Theo Jackson", "S", "", "Full Participation in Practice", ""),
    ("W10-05", "MIN", "Jauan Jennings", "WR", "Calf", "Did Not Participate In Practice", "Out"),
    ("W10-05", "MIN", "Josh Metellus", "S", "Shoulder", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "MIN", "Kyler Murray", "QB", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("W10-05", "MIN", "Harrison Smith", "S", "", "Limited Participation in Practice", ""),
    ("W10-05", "MIN", "Kyle Van Noy", "LB", "Calf", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "MIN", "Jay Ward", "S", "", "Full Participation in Practice", ""),
    ("W10-05", "MIN", "Carson Wentz", "QB", "", "Full Participation in Practice", ""),
    ("W10-05", "GB", "Aaron Banks", "G", "", "Limited Participation in Practice", ""),
    ("W10-05", "GB", "Chris Brooks", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "GB", "Javon Bullard", "S", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "GB", "Zaire Franklin", "LB", "Shin", "Did Not Participate In Practice", "Doubtful"),
    ("W10-05", "GB", "Travis Glover", "G", "Knee", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "GB", "Ty'Ron Hopper", "LB", "", "Full Participation in Practice", ""),
    ("W10-05", "GB", "Josh Jacobs", "RB", "Finger", "Did Not Participate In Practice", "Out"),
    ("W10-05", "GB", "Xavier McKinney", "S", "Foot", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "GB", "Bo Melton", "WR", "", "Full Participation in Practice", ""),
    ("W10-05", "GB", "Skyy Moore", "WR", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "GB", "Micah Parsons", "LB", "Knee, Illness", "Limited Participation in Practice", "Out"),
    ("W10-05", "GB", "Sean Rhyan", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("W10-05", "GB", "Trey Smack", "K", "", "Full Participation in Practice", ""),
    ("W10-05", "GB", "Lukas Van Ness", "LB", "Back", "Limited Participation in Practice", "Questionable"),
    ("W10-05", "GB", "Josh Whyle", "TE", "Concussion", "Did Not Participate In Practice", "Out"),
    ("W10-05", "GB", "Savion Williams", "WR", "", "Limited Participation in Practice", ""),
    ("W10-05", "GB", "Kevin Zeitler", "G", "Ankle, Triceps", "Did Not Participate In Practice", "Questionable"),
    ("W10-09", "JAX", "Jessie Bates", "S", "Not injury related - resting player", "Limited Participation in Practice", "Out"),
    ("W10-09", "JAX", "Ezra Cleveland", "G", "", "Full Participation in Practice", ""),
    ("W10-09", "JAX", "Branson Combs", "LB", "", "Full Participation in Practice", ""),
    ("W10-09", "JAX", "Jordan Davis", "DT", "Not injury related - resting player", "Limited Participation in Practice", "Out"),
    ("W10-09", "JAX", "BJ Green II", "DE", "Forearm", "Full Participation in Practice", "Out"),
    ("W10-09", "JAX", "Robert Hainsey", "C", "Concussion", "Limited Participation in Practice", "Questionable"),
    ("W10-09", "JAX", "Antonio Johnson", "S", "", "Limited Participation in Practice", ""),
    ("W10-09", "JAX", "Jakobi Meyers", "WR", "", "Limited Participation in Practice", ""),
    ("W10-09", "JAX", "Chris Rodriguez Jr.", "RB", "", "Limited Participation in Practice", ""),
    ("W10-09", "JAX", "Bhayshul Tuten", "RB", "", "Limited Participation in Practice", ""),
    ("W10-09", "JAX", "Travon Walker", "DE", "", "Limited Participation in Practice", ""),
    ("W10-09", "TEN", "Cody Barton", "LB", "Concussion", "Did Not Participate In Practice", "Out"),
    ("W10-09", "TEN", "John Franklin-Myers", "DE", "", "Full Participation in Practice", ""),
    ("W10-09", "TEN", "Marcus Harris", "CB", "", "Full Participation in Practice", ""),
    ("W10-09", "TEN", "Anthony Hill Jr.", "LB", "Neck", "Did Not Participate In Practice", "Out"),
    ("W10-09", "TEN", "Jaylon Jones", "CB", "", "Full Participation in Practice", ""),
    ("W10-09", "TEN", "JC Latham", "T", "", "Full Participation in Practice", ""),
    ("W10-09", "TEN", "Tony Pollard", "RB", "", "Full Participation in Practice", ""),
    ("W10-09", "TEN", "Peter Skoronski", "G", "Hamstring", "Did Not Participate In Practice", "Out"),
    ("W10-09", "TEN", "Tyjae Spears", "RB", "Knee", "Full Participation in Practice", "Questionable"),
    ("W10-09", "TEN", "Carnell Tate", "WR", "Shoulder", "Did Not Participate In Practice", "Out"),
    ("W10-09", "TEN", "Tommy Townsend", "P", "Knee, Achilles", "Did Not Participate In Practice", "Out"),
    ("W10-09", "TEN", "Kevin Winston Jr.", "S", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Alec Anderson", "G", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Christian Benford", "CB", "Wrist", "Full Participation in Practice", "Questionable"),
    ("W10-08", "BUF", "Terrel Bernard", "LB", "", "Did Not Participate In Practice", ""),
    ("W10-08", "BUF", "Spencer Brown", "T", "Ankle", "Did Not Participate In Practice", "Doubtful"),
    ("W10-08", "BUF", "Dion Dawkins", "T", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Sam Franklin Jr.", "S", "Shoulder", "Limited Participation in Practice", "Questionable"),
    ("W10-08", "BUF", "Greg Gaines", "DT", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Jordan Hancock", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("W10-08", "BUF", "Dalton Kincaid", "TE", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Connor McGovern", "C", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Ed Oliver", "DE", "", "Did Not Participate In Practice", ""),
    ("W10-08", "BUF", "Ar'maj Reed-Adams", "G", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "T.J. Sanders", "DE", "", "Full Participation in Practice", ""),
    ("W10-08", "BUF", "Tyrell Shavers", "WR", "Knee", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Jarvis Brownlee Jr.", "CB", "Illness", "Limited Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Omar Cooper Jr.", "WR", "Ankle", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Adonai Mitchell", "WR", "Knee", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Joseph Ossai", "DE", "Ankle", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "VJ Payne", "S", "Knee", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Harrison Phillips", "DT", "Ankle", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Trevin Wallace", "LB", "Groin", "Did Not Participate In Practice", "Out"),
    ("W10-08", "NYJ", "Garrett Wilson", "WR", "Concussion", "Full Participation in Practice", "Questionable"),
    ("W10-08", "NYJ", "Nahshon Wright", "CB", "Back", "Full Participation in Practice", "Questionable"),
    ("W10-06", "MIA", "Tucker Addington", "LS", "", "Limited Participation in Practice", ""),
    ("W10-06", "MIA", "Kaytron Allen", "RB", "", "Full Participation in Practice", ""),
    ("W10-06", "MIA", "Darrell Baker Jr.", "CB", "Knee", "Full Participation in Practice", "Questionable"),
    ("W10-06", "MIA", "Chris Bell", "WR", "Knee", "Did Not Participate In Practice", "Doubtful"),
    ("W10-06", "MIA", "Aaron Brewer", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("W10-06", "MIA", "Malik Herring", "DE", "", "Full Participation in Practice", ""),
    ("W10-06", "MIA", "Will Kacmarek", "TE", "", "Full Participation in Practice", ""),
    ("W10-06", "MIA", "Michael Taaffe", "S", "", "Full Participation in Practice", ""),
    ("W10-06", "MIA", "Dante Trader Jr.", "S", "", "Full Participation in Practice", ""),
    ("W10-06", "MIA", "Jared Wayne", "WR", "Quadricep", "Did Not Participate In Practice", "Out"),
    ("W10-06", "MIA", "Jaylen Wright", "RB", "", "Full Participation in Practice", ""),
]

# --------------------------------------------------------------------------
# GB club roster page (nfl.com/teams/green-bay-packers/roster, read
# 2026-11-16T00:02:00Z). The page prints a status code per player with no
# legend: ACT, CUT, DEV, PUP, RES, RSR, TRC, TRD, TRT. Codes are kept
# verbatim and are not expanded. Non-ACT rows are captured in full for the
# reserve-list register ("not listed" must never mean "available").
# --------------------------------------------------------------------------
GB_ROSTER_URL = "https://www.nfl.com/teams/green-bay-packers/roster/"
GB_ROSTER_READ = "2026-11-16T00:02:00Z"

# (player_display_name, player_url_slug, jersey, position, status_code)
GB_NON_ACT_ROWS = [
    ("Trey Dean III", "trey-dean-iii", "35", "SAF", "CUT"),
    ("Kahlef Hailassie", "kahlef-hailassie", "", "DB", "CUT"),
    ("Chris Hilton Jr.", "chris-hilton-jr", "37", "WR", "CUT"),
    ("Marlon Jones", "marlon-jones-2", "46", "DB", "CUT"),
    ("Coleman Owen", "coleman-owen", "", "WR", "CUT"),
    ("David Blay Jr.", "david-blay-jr", "", "DT", "DEV"),
    ("Dalton Cooper", "dalton-cooper", "78", "OT", "DEV"),
    ("Elijah Culp", "elijah-culp", "", "CB", "DEV"),
    ("Jack Dingle", "jack-dingle", "", "LB", "DEV"),
    ("Kenny Fletcher Jr.", "kenny-fletcher-jr", "", "TE", "DEV"),
    ("Domani Jackson", "domani-jackson", "20", "CB", "DEV"),
    ("DJ Johnson", "dj-johnson-2", "", "LB", "DEV"),
    ("Nyjalik Kelly", "nyjalik-kelly", "47", "DE", "DEV"),
    ("Lenny Krieg", "lenny-krieg", "", "K", "DEV"),
    ("Cam Miller", "cam-miller", "", "QB", "DEV"),
    ("Arron Mosby", "arron-mosby", "53", "LB", "DEV"),
    ("Isaiah Neyor", "isaiah-neyor", "80", "WR", "DEV"),
    ("John Saunders Jr.", "john-saunders-jr", "", "SAF", "DEV"),
    ("Quincy Skinner Jr.", "quincy-skinner-jr", "", "WR", "DEV"),
    ("Mazi Smith", "mazi-smith", "", "DT", "DEV"),
    ("Dillon Wade", "dillon-wade", "68", "G", "DEV"),
    ("Luke Musgrave", "luke-musgrave", "88", "TE", "PUP"),
    ("Micah Parsons", "micah-parsons", "1", "LB", "PUP"),
    ("Johnathan Baldwin", "johnathan-baldwin", "37", "SAF", "RES"),
    ("Warren Brinson", "warren-brinson", "91", "DT", "RES"),
    ("McCallan Castles", "mccallan-castles", "47", "TE", "RES"),
    ("Edgerrin Cooper", "edgerrin-cooper", "56", "LB", "RES"),
    ("Jonathan Ford", "jonathan-ford", "96", "DT", "RES"),
    ("Javon Hargrave", "javon-hargrave", "98", "NT", "RES"),
    ("Jacob Monk", "jacob-monk", "62", "G", "RES"),
    ("Jayden Reed", "jayden-reed", "11", "WR", "RES"),
    ("Zach Bako-Bewele", "zach-tom", "50", "G", "RES"),
    ("Josh Whyle", "josh-whyle", "81", "TE", "RES"),
    ("Thomas Yassmin", "thomas-yassmin", "84", "TE", "RES"),
    ("Collin Oliver", "collin-oliver", "45", "LB", "RSR"),
    ("Eric Johnson", "eric-johnson-7", "", "DT", "TRC"),
    ("Kedon Slovis", "kedon-slovis", "", "QB", "TRC"),
    ("Josh Gesky", "josh-gesky", "76", "OT", "TRD"),
    ("Cordell Volson", "cordell-volson", "", "OT", "TRD"),
    ("Damon Bankston", "damon-bankston", "", "RB", "TRT"),
    ("Scott Daly", "scott-daly", "", "LS", "TRT"),
]

# The page prints no legend for its status codes; this string is what a reader
# must not invent meanings for.
GB_ROSTER_STATUS_NOTE = (
    "Status codes (ACT, CUT, DEV, PUP, RES, RSR, TRC, TRD, TRT) are printed "
    "without a legend on the roster page. They are published verbatim and are "
    "not expanded to invented meanings."
)

# Malik Willis: absent from every chunk of the roster page read (QBs listed:
# Jordan Love ACT, Tyrod Taylor ACT, Cam Miller DEV, Kedon Slovis TRC). No IR
# row exists for him on this page. A sibling pack's 2026-11-13/14 capture
# recorded him on injured reserve; this read can confirm neither the IR state
# nor availability. "Not listed" is published as unknown, never as healthy.
GB_WILLIS_FINDING = {
    "player": "Malik Willis",
    "state_on_page": "absent (no row, any status code)",
    "qbs_listed": "Jordan Love (ACT), Tyrod Taylor (ACT), Cam Miller (DEV), Kedon Slovis (TRC)",
}

# Display-name / URL-slug mismatch on the same row, kept verbatim.
GB_NAME_SLUG_MISMATCH = {
    "display_name": "Zach Bako-Bewele",
    "url_slug": "zach-tom",
    "row": "50 | G | RES",
}

# --------------------------------------------------------------------------
# Capture-attempt log (negative results are data). Every attempt is a real
# fetch made this session; the outcome column is what the fetch returned.
# --------------------------------------------------------------------------
CAPTURE_ATTEMPTS = [
    ("2026-11-15T23:52:00Z", "https://www.nfl.com/injuries/2026/week-11",
     "week-scoped injury hub URL guess for week 11", "404 - Flag on the Play (page not found)",
     "the hub at https://www.nfl.com/injuries/ renders the current week (WEEK 10) with a week selector WEEK 1..WEEK 10; no week-11 report exists yet"),
    ("2026-11-15T23:55:00Z", "https://www.nfl.com/teams/green-bay-packers/roster/",
     "club roster page (reserve-list register)", "success (3 chunks, all read)",
     "reserve sections captured: PUP 2, RES 11, RSR 1, plus CUT/DEV/TRC/TRD/TRT rows"),
]

# --------------------------------------------------------------------------
# Week-11 venues transcribed from each fixture's official game-centre page
# (Game Info block: "Location LOCATION ... Stadium STADIUM ..."). A fixture
# without a read here keeps a blank venue and is gated at the venue row; no
# venue is ever taken from a ticketing or hotel link.
# --------------------------------------------------------------------------
VENUE_READS = {
    # game_id: (stadium_on_page, location_on_page, read_at_utc, game_page_url)
    "W11-06": ("FORD FIELD", "DETROIT, MI", "2026-11-15T23:27:00Z",
               "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
}
