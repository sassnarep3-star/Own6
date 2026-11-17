"""Hand-captured official values for the nfl_45abd396 pack (read 2026-11-17 UTC).

Every value in this module was read during this session from the official nfl.com
page named beside it, through a single read-only page fetch. Nothing is inferred,
nothing is copied from another pack, and no value is carried over from an earlier
session's capture. Where two official pages disagree the disagreement is stored as
a row in ``STALE_CONFLICTS`` and flagged — it is never resolved by preference.

Reads performed this session (all clock times UTC)
--------------------------------------------------
* R1  nfl.com week-10 schedule         2026-11-17T00:41Z  (14 cards; 13 FINAL, 1 pending)
* R2  nfl.com standings (division view)2026-11-17T00:43Z  (32 club rows)
* R3  nfl.com injury hub, Week 10      2026-11-17T00:47Z  (14 fixture blocks, 28 club tables)
* R4  nfl.com week-11 schedule         2026-11-17T00:52Z  (13 cards + 4 bye clubs)
* R5  nfl.com 2026 transactions, Nov   2026-11-17T00:56Z  (trades table)
* R6  nfl.com 2026 reserve list, Nov   2026-11-17T00:57Z  (reserve/injured table)
* R7  nfl.com news: Willis to IR       2026-11-17T00:58Z
* R8  nfl.com game centre LAC @ BAL    2026-11-17T00:54Z  (venue + club injury snippets)

Rights note: NFL.com Terms §1.3 was read by earlier sessions in this repo and
limits use to individual, non-commercial, informational purposes and prohibits
systematic retrieval. This session therefore performs single manual reads and runs
no scheduled automation in CI; the rights question stays open as Q-01.
"""

from __future__ import annotations

CAPTURE_DATE_UTC = "2026-11-17"

# ---------------------------------------------------------------------------
# source register — every URL used anywhere in this pack
# ---------------------------------------------------------------------------
URL_W10_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-10"
URL_W11_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-11"
URL_STANDINGS_DIV = "https://www.nfl.com/standings/"
URL_INJURIES = "https://www.nfl.com/injuries/"
URL_TRANSACTIONS = "https://www.nfl.com/transactions/"
URL_RESERVE = "https://www.nfl.com/transactions/league/reserve-list/2026/11"
URL_NEWS_WILLIS = (
    "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-"
    "kyle-mccord-in-line-for-first-start"
)
URL_GAME_LAC_BAL = "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"
URL_REPO = "https://github.com/sassnarep3-star/Own6"

READ_CLOCKS = {
    "R1_week10_schedule": ("2026-11-17T00:41:00Z", URL_W10_SCHED),
    "R2_standings": ("2026-11-17T00:43:00Z", URL_STANDINGS_DIV),
    "R3_injury_hub": ("2026-11-17T00:47:00Z", URL_INJURIES),
    "R4_week11_schedule": ("2026-11-17T00:52:00Z", URL_W11_SCHED),
    "R5_transactions": ("2026-11-17T00:56:00Z", URL_TRANSACTIONS),
    "R6_reserve_list": ("2026-11-17T00:57:00Z", URL_RESERVE),
    "R7_news_willis": ("2026-11-17T00:58:00Z", URL_NEWS_WILLIS),
    "R8_game_lac_bal": ("2026-11-17T00:54:00Z", URL_GAME_LAC_BAL),
}

# ---------------------------------------------------------------------------
# R1 — week-10 schedule cards. ``status`` and ``score`` are the page's own words.
# The card that prints no FINAL carries no score here; it is not guessed.
# ---------------------------------------------------------------------------
W10_CARDS = [
    # game_id, away, home, day_on_card, slot_on_card, status_on_card, away_score, home_score, event_mark
    ("W10-01", "WAS", "NYG", "Thursday, November 12th", "8:15 PM", "FINAL", 24, 21, ""),
    ("W10-02", "NE", "DET", "Sunday, November 15th", "9:30 AM", "FINAL", 10, 35, "Munich 2026"),
    ("W10-03", "KC", "ATL", "Sunday, November 15th", "1:00 PM", "FINAL", 35, 13, ""),
    ("W10-04", "HOU", "CLE", "Sunday, November 15th", "1:00 PM", "FINAL", 24, 27, ""),
    ("W10-05", "MIN", "GB", "Sunday, November 15th", "1:00 PM", "FINAL", 30, 10, ""),
    ("W10-06", "MIA", "IND", "Sunday, November 15th", "1:00 PM", "FINAL", 22, 24, ""),
    ("W10-07", "CAR", "NO", "Sunday, November 15th", "1:00 PM", "FINAL", 20, 17, ""),
    ("W10-08", "BUF", "NYJ", "Sunday, November 15th", "1:00 PM", "FINAL", 31, 12, ""),
    ("W10-09", "JAX", "TEN", "Sunday, November 15th", "1:00 PM", "FINAL", 40, 23, ""),
    ("W10-10", "LA", "AZ", "Sunday, November 15th", "4:05 PM", "FINAL", 34, 6, ""),
    ("W10-11", "SEA", "LV", "Sunday, November 15th", "4:05 PM", "FINAL", 21, 13, ""),
    ("W10-12", "SF", "DAL", "Sunday, November 15th", "4:25 PM", "FINAL", 46, 40, ""),
    ("W10-13", "PIT", "CIN", "Sunday, November 15th", "8:20 PM", "FINAL", 18, 38, ""),
    ("W10-14", "LAC", "BAL", "Monday, November 16th", "8:15 PM", "scheduled (8:15 PM)", None, None, ""),
]

W10_GAME_URL = "https://www.nfl.com/games/{slug}-2026-reg-10"
W10_SLUGS = {
    "W10-01": "commanders-at-giants",
    "W10-02": "patriots-at-lions",
    "W10-03": "chiefs-at-falcons",
    "W10-04": "texans-at-browns",
    "W10-05": "vikings-at-packers",
    "W10-06": "dolphins-at-colts",
    "W10-07": "panthers-at-saints",
    "W10-08": "bills-at-jets",
    "W10-09": "jaguars-at-titans",
    "W10-10": "rams-at-cardinals",
    "W10-11": "seahawks-at-raiders",
    "W10-12": "49ers-at-cowboys",
    "W10-13": "steelers-at-bengals",
    "W10-14": "chargers-at-ravens",
}

# ---------------------------------------------------------------------------
# R2 — standings, division view. Columns printed on the page, in page order:
#   W L T PCT PF PA NET HOME ROAD DIV DIV% CONF CONF% (unlabelled) STRK (unlabelled)
# The two unlabelled columns are stored verbatim and never named (see FLAG-W05).
# ---------------------------------------------------------------------------
STANDINGS_READ = [
    # abbr, W, L, T, PCT, PF, PA, NET, HOME, ROAD, DIV, DIV_PCT, CONF, CONF_PCT, unl1, STRK, unl2
    ("BUF", 8, 1, 0, "0.889", 287, 199, 88, "3 - 1 - 0", "5 - 0 - 0", "1 - 1 - 0", "0.500", "5 - 1 - 0", "0.833", "3 - 0 - 0", "5W", "5 - 0 - 0"),
    ("NE", 5, 5, 0, "0.500", 221, 242, -21, "3 - 1 - 0", "2 - 4 - 0", "3 - 0 - 0", "1.000", "5 - 1 - 0", "0.833", "0 - 4 - 0", "2L", "2 - 3 - 0"),
    ("NYJ", 2, 8, 0, "0.200", 194, 254, -60, "1 - 4 - 0", "1 - 4 - 0", "0 - 3 - 0", "0.000", "2 - 5 - 0", "0.286", "0 - 3 - 0", "5L", "0 - 5 - 0"),
    ("MIA", 1, 8, 0, "0.111", 148, 224, -76, "0 - 4 - 0", "1 - 4 - 0", "1 - 1 - 0", "0.500", "1 - 5 - 0", "0.167", "0 - 3 - 0", "3L", "1 - 4 - 0"),
    ("CIN", 7, 2, 0, "0.778", 278, 193, 85, "3 - 1 - 0", "4 - 1 - 0", "2 - 1 - 0", "0.667", "5 - 2 - 0", "0.714", "2 - 0 - 0", "5W", "5 - 0 - 0"),
    ("PIT", 6, 3, 0, "0.667", 198, 182, 16, "4 - 0 - 0", "2 - 3 - 0", "2 - 2 - 0", "0.500", "3 - 3 - 0", "0.500", "3 - 0 - 0", "1L", "4 - 1 - 0"),
    ("CLE", 6, 4, 0, "0.600", 188, 220, -32, "4 - 0 - 0", "2 - 4 - 0", "2 - 1 - 0", "0.667", "4 - 3 - 0", "0.571", "2 - 1 - 0", "1W", "3 - 2 - 0"),
    ("BAL", 4, 5, 0, "0.444", 189, 236, -47, "1 - 3 - 0", "3 - 2 - 0", "0 - 2 - 0", "0.000", "2 - 4 - 0", "0.333", "2 - 1 - 0", "4L", "1 - 4 - 0"),
    ("JAX", 7, 2, 0, "0.778", 269, 144, 125, "4 - 1 - 0", "3 - 1 - 0", "2 - 1 - 0", "0.667", "6 - 2 - 0", "0.750", "1 - 0 - 0", "3W", "4 - 1 - 0"),
    ("HOU", 3, 6, 0, "0.333", 233, 219, 14, "0 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 4 - 0", "0.429", "0 - 2 - 0", "1L", "3 - 2 - 0"),
    ("IND", 3, 7, 0, "0.300", 208, 271, -63, "2 - 3 - 0", "1 - 4 - 0", "1 - 2 - 0", "0.333", "2 - 5 - 0", "0.286", "1 - 2 - 0", "1W", "1 - 4 - 0"),
    ("TEN", 1, 8, 0, "0.111", 167, 239, -72, "0 - 5 - 0", "1 - 3 - 0", "1 - 2 - 0", "0.333", "1 - 6 - 0", "0.143", "0 - 2 - 0", "3L", "1 - 4 - 0"),
    ("KC", 7, 2, 0, "0.778", 237, 156, 81, "4 - 0 - 0", "3 - 2 - 0", "3 - 1 - 0", "0.750", "6 - 1 - 0", "0.857", "1 - 1 - 0", "2W", "3 - 2 - 0"),
    ("DEN", 7, 2, 0, "0.778", 198, 186, 12, "4 - 0 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 1 - 0", "0.750", "4 - 1 - 0", "5W", "5 - 0 - 0"),
    ("LV", 4, 6, 0, "0.400", 251, 289, -38, "1 - 4 - 0", "3 - 2 - 0", "1 - 1 - 0", "0.500", "3 - 3 - 0", "0.500", "1 - 3 - 0", "2L", "1 - 4 - 0"),
    ("LAC", 0, 8, 0, "0.000", 121, 219, -98, "0 - 4 - 0", "0 - 4 - 0", "0 - 3 - 0", "0.000", "0 - 5 - 0", "0.000", "0 - 3 - 0", "8L", "0 - 5 - 0"),
    ("NYG", 5, 3, 1, "0.611", 203, 196, 7, "3 - 2 - 0", "2 - 1 - 1", "2 - 1 - 1", "0.625", "3 - 3 - 1", "0.500", "2 - 0 - 0", "1L", "2 - 2 - 1"),
    ("DAL", 4, 6, 0, "0.400", 286, 282, 4, "1 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "2 - 5 - 0", "0.286", "2 - 1 - 0", "1L", "2 - 3 - 0"),
    ("WAS", 3, 5, 1, "0.389", 196, 223, -27, "2 - 2 - 1", "1 - 3 - 0", "2 - 2 - 1", "0.500", "3 - 4 - 1", "0.438", "0 - 1 - 0", "1W", "2 - 2 - 1"),
    ("PHI", 2, 7, 0, "0.222", 148, 221, -73, "1 - 4 - 0", "1 - 3 - 0", "1 - 3 - 0", "0.250", "1 - 6 - 0", "0.143", "1 - 1 - 0", "7L", "0 - 5 - 0"),
    ("DET", 7, 2, 0, "0.778", 257, 199, 58, "5 - 0 - 0", "2 - 2 - 0", "2 - 0 - 0", "1.000", "4 - 1 - 0", "0.800", "3 - 1 - 0", "5W", "5 - 0 - 0"),
    ("MIN", 7, 2, 0, "0.778", 176, 126, 50, "3 - 1 - 0", "4 - 1 - 0", "3 - 1 - 0", "0.750", "5 - 1 - 0", "0.833", "2 - 1 - 0", "1W", "3 - 2 - 0"),
    ("CHI", 7, 2, 0, "0.778", 241, 184, 57, "4 - 1 - 0", "3 - 1 - 0", "0 - 2 - 0", "0.000", "5 - 2 - 0", "0.714", "2 - 0 - 0", "4W", "4 - 1 - 0"),
    ("GB", 6, 4, 0, "0.600", 226, 221, 5, "3 - 2 - 0", "3 - 2 - 0", "1 - 3 - 0", "0.250", "4 - 4 - 0", "0.500", "2 - 0 - 0", "1L", "3 - 2 - 0"),
    ("CAR", 4, 5, 0, "0.444", 219, 236, -17, "1 - 3 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "4 - 3 - 0", "0.571", "0 - 2 - 0", "1W", "2 - 3 - 0"),
    ("TB", 3, 6, 0, "0.333", 202, 178, 24, "1 - 4 - 0", "2 - 2 - 0", "2 - 0 - 0", "1.000", "3 - 3 - 0", "0.500", "0 - 3 - 0", "1L", "3 - 2 - 0"),
    ("NO", 3, 6, 0, "0.333", 202, 236, -34, "1 - 5 - 0", "2 - 1 - 0", "0 - 2 - 0", "0.000", "1 - 4 - 0", "0.200", "2 - 2 - 0", "1L", "2 - 3 - 0"),
    ("ATL", 3, 7, 0, "0.300", 201, 258, -57, "1 - 5 - 0", "2 - 2 - 0", "1 - 2 - 0", "0.333", "3 - 3 - 0", "0.500", "0 - 4 - 0", "3L", "1 - 4 - 0"),
    ("SF", 8, 1, 0, "0.889", 281, 196, 85, "5 - 0 - 0", "3 - 1 - 0", "3 - 0 - 0", "1.000", "5 - 1 - 0", "0.833", "3 - 0 - 0", "2W", "4 - 1 - 0"),
    ("SEA", 6, 4, 0, "0.600", 223, 175, 48, "4 - 2 - 0", "2 - 2 - 0", "2 - 1 - 0", "0.667", "2 - 3 - 0", "0.400", "4 - 1 - 0", "2W", "3 - 2 - 0"),
    ("LA", 6, 4, 0, "0.600", 248, 187, 61, "2 - 3 - 0", "4 - 1 - 0", "1 - 2 - 0", "0.333", "4 - 2 - 0", "0.667", "2 - 2 - 0", "4W", "4 - 1 - 0"),
    ("AZ", 3, 7, 0, "0.300", 184, 289, -105, "0 - 4 - 0", "3 - 3 - 0", "1 - 4 - 0", "0.200", "2 - 6 - 0", "0.250", "1 - 1 - 0", "2L", "2 - 3 - 0"),
]

# ---------------------------------------------------------------------------
# R4 — week-11 schedule: 13 cards, and the four clubs on bye printed on the page.
# ---------------------------------------------------------------------------
W11_CARDS = [
    # away, home, day_on_card, slot_on_card, network, event_mark
    ("IND", "HOU", "Thursday, November 19th", "8:15 PM", "PRIME", ""),
    ("MIA", "BUF", "Sunday, November 22nd", "1:00 PM", "CBS", ""),
    ("BAL", "CAR", "Sunday, November 22nd", "1:00 PM", "FOX", ""),
    ("NO", "CHI", "Sunday, November 22nd", "1:00 PM", "FOX", ""),
    ("TEN", "DAL", "Sunday, November 22nd", "1:00 PM", "FOX", ""),
    ("TB", "DET", "Sunday, November 22nd", "1:00 PM", "FOX", ""),
    ("AZ", "KC", "Sunday, November 22nd", "1:00 PM", "CBS", ""),
    ("PIT", "PHI", "Sunday, November 22nd", "1:00 PM", "CBS", ""),
    ("NYJ", "LAC", "Sunday, November 22nd", "4:05 PM", "FOX", ""),
    ("JAX", "NYG", "Sunday, November 22nd", "4:25 PM", "CBS", ""),
    ("LV", "DEN", "Sunday, November 22nd", "4:25 PM", "CBS", ""),
    ("MIN", "SF", "Sunday, November 22nd", "8:20 PM", "NBC", "Mexico City 2026"),
    ("CIN", "WAS", "Monday, November 23rd", "8:15 PM", "ESPN", ""),
]

W11_BYE_CLUBS = ["ATL", "CLE", "GB", "LA"]

# Venue fields read from a game-centre "Game Info" block this session.
# Only fixtures whose block was actually read carry a venue; the rest stay blank.
W11_VENUES_FROM_GAME_CENTRE = {
    # away, home -> (stadium_on_page, location_on_page, read_clock, url)
    ("IND", "HOU"): ("NRG STADIUM", "HOUSTON, TX", "2026-11-16T00:35:00Z",
                     "https://www.nfl.com/games/colts-at-texans-2026-reg-11"),
    ("TB", "DET"): ("FORD FIELD", "DETROIT, MI", "2026-11-15T23:27:00Z",
                    "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11"),
    ("LAC", "BAL"): ("M&T BANK STADIUM", "BALTIMORE, MD", "2026-11-17T00:54:00Z",
                     "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"),
}
# Venue names appear in schedule-page hotel links (destinationAddress.location=…).
# That is a link parameter, not a rendered venue field, so it is NOT used here.

# ---------------------------------------------------------------------------
# R5 — November 2026 trades table, verbatim from the transactions page.
# ---------------------------------------------------------------------------
TRADES_NOV_2026 = [
    # from, to, date_on_page, player
    ("ATL", "JAX", "11/10", "Jessie Bates"),
    ("PHI", "JAX", "11/10", "Jordan Davis"),
    ("TEN", "BUF", "11/10", "Amani Hooker"),
    ("IND", "SF", "11/10", "Keenan Allen"),
    ("LV", "MIN", "11/10", "Kirk Cousins"),
    ("LAC", "DEN", "11/10", "Daiyan Henley"),
    ("IND", "KC", "11/10", "Josh Downs"),
    ("ATL", "BAL", "11/10", "Ryan Neuzil"),
    ("BAL", "ATL", "11/10", "Andrew Vorhees"),
    ("NYJ", "DET", "11/09", "Andre Cisco"),
    ("NO", "JAX", "11/09", "Davon Godchaux"),
    ("AZ", "BAL", "11/06", "Jacoby Brissett"),
]

# ---------------------------------------------------------------------------
# R6 — November 2026 reserve list ("Reserve/Injured"), verbatim.
# ---------------------------------------------------------------------------
RESERVE_NOV_2026 = [
    # club, date_on_page, player
    ("LA", "11/16", "Dylan McMahon"),
    ("LAC", "11/16", "Branson Taylor"),
    ("NO", "11/14", "Christen Miller"),
    ("NE", "11/14", "TreVeyon Henderson"),
    ("CLE", "11/14", "Michael Burton"),
    ("IND", "11/14", "Mo Alie-Cox"),
    ("IND", "11/14", "Akeem Davis-Gaither"),
    ("TEN", "11/14", "Peter Skoronski"),
    ("TEN", "11/14", "Tommy Townsend"),
    ("DAL", "11/14", "Tyler Goodson"),
    ("GB", "11/14", "Josh Whyle"),
    ("LA", "11/12", "Puka Nacua"),
    ("LA", "11/10", "Jordan Whittington"),
    ("MIA", "11/10", "Zach Sieler"),
    ("MIA", "11/10", "Malik Willis"),
    ("SF", "11/10", "Gracen Halton"),
    ("AZ", "11/10", "Gardner Minshew"),
    ("AZ", "11/10", "Michael Wilson"),
    ("TEN", "11/09", "James Williams"),
    ("MIN", "11/09", "Demond Claiborne"),
    ("BUF", "11/09", "Josh Palmer"),
    ("ATL", "11/07", "Brian Robinson"),
    ("LA", "11/07", "Jaylen Watson"),
    ("DEN", "11/07", "Eyioma Uwazurike"),
    ("DET", "11/07", "Jack Campbell"),
]

# ---------------------------------------------------------------------------
# R7 — one dated official news page read this session. Only the sentences below
# are used, and only for the claim they make directly.
# ---------------------------------------------------------------------------
WILLIS_ARTICLE = {
    "player": "Malik Willis",
    "club": "MIA",
    "claim_ir_date": "placed on injured reserve Tuesday",
    "claim_reason": "groin injury",
    "claim_replacement": "Kyle McCord",
    "claim_return": "eligible to return for the team's Dec. 13 home game against the Chicago Bears",
    "url": URL_NEWS_WILLIS,
    "read_at_utc": "2026-11-17T00:58:00Z",
}

# ---------------------------------------------------------------------------
# Stale / conflicting official evidence found this session.
# Each row names both official pages so a reviewer can adjudicate.
# ---------------------------------------------------------------------------
STALE_CONFLICTS = [
    {
        "conflict_id": "C-01",
        "kind": "club assignment on the injury hub contradicts the transactions table",
        "player": "Daiyan Henley",
        "page_a_claim": "injury hub, Week 10, Chargers table: LB, Full Participation in Practice",
        "page_b_claim": "transactions, November: Traded 11/10 from LAC to DEN",
        "page_a_url": URL_INJURIES,
        "page_b_url": URL_TRANSACTIONS,
        "severity": "medium",
        "consequence": "any depth or availability model keyed on the hub's club column would place a traded player on his old club",
    },
    {
        "conflict_id": "C-02",
        "kind": "reserve-list entry with no weekly injury-report row at the same read",
        "player": "Malik Willis",
        "page_a_claim": "reserve list, November: MIA Reserve/Injured 11/10",
        "page_b_claim": "injury hub, Week 10: no Malik Willis row in any club table at this read",
        "page_a_url": URL_RESERVE,
        "page_b_url": URL_INJURIES,
        "severity": "low",
        "consequence": "confirms the brief's rule that 'not listed' never means 'available'; resolves the earlier pack's open question Q-05",
    },
    {
        "conflict_id": "C-03",
        "kind": "bye clubs publish no injury-report table at all",
        "player": "",
        "page_a_claim": "injury hub, Week 10: 28 club tables across 14 fixture blocks; CHI, DEN, PHI and TB have none",
        "page_b_claim": "week-11 schedule page lists ATL, CLE, GB and LA as the clubs on bye",
        "page_a_url": URL_INJURIES,
        "page_b_url": URL_W11_SCHED,
        "severity": "low",
        "consequence": "the 32-club sweep cannot be completed from the weekly report alone in any week; the four clubs absent here (CHI, DEN, PHI, TB) played in week 10 but are not on a bye — they simply have no table on this page, which is itself unexplained",
    },
]

# ---------------------------------------------------------------------------
# R8 — the only two club injury snippets rendered on the LAC @ BAL game centre.
# Stored because they disagree in wording with the hub ('Did participate').
# ---------------------------------------------------------------------------
GAME_CENTRE_SNIPPETS = {
    "url": URL_GAME_LAC_BAL,
    "read_at_utc": "2026-11-17T00:54:00Z",
    "rows": [
        # club, player, position_on_page, code_on_page, body_part, practice_word
        ("LAC", "B. Taylor", "OL #71", "O", "Ankle", "Did not participate"),
        ("LAC", "I. Waxter", "DB", "O", "Ankle", "Did not participate"),
        ("LAC", "K. Williamson", "DB #32", "O", "Calf", "Did not participate"),
        ("LAC", "B. Thompson", "WR #89", "D", "Hamstring", "Did not participate"),
        ("BAL", "J. Hawkins", "DB #21", "O", "Knee", "Did participate"),
        ("BAL", "A. Randall", "RB #23", "Q", "Hamstring", "Full participation"),
        ("BAL", "R. Ali", "RB #26", "A", "", "Full participation"),
        ("BAL", "R. Bateman", "WR #7", "A", "", "Full participation"),
    ],
}
