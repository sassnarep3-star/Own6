"""Verbatim official captures, read directly on 2026-11-14 (UTC) in session d966f630.

This module is the ONLY place in the pack where an externally sourced value is
written down. Everything else in ``src/nfl_d966f630`` is arithmetic on these
captures, and every derived number therefore traces back to a row here and
through ``SOURCES`` to an official NFL page.

Discipline applied to every row in this file
--------------------------------------------
* The value is copied from the page text, not inferred. If the page does not
  state it, the field is an empty string and ``flagged.csv`` carries the gap.
* ``src`` names an entry in ``SOURCES`` below. Each entry records the exact URL,
  the retrieval method, the date it was read and what the page does *not* say.
* nfl.com game cards display a team record **after** the game shown on the card
  (verified by cross-week consistency: GB 5-3 after Week 8 then 6-3 after Week 9,
  BUF 6-1 after Week 8 then 7-1 after Week 9). The "Teams on Bye" panel on the
  same page instead shows the record **as of the render date** (e.g. it lists
  WAS 3-5-1 and LAC 0-8 while displaying the Week 7 byes). Bye-panel records are
  therefore NOT used as point-in-time inputs anywhere in this pack; see
  ``flagged.csv`` row D966-F04 for the trap.
* Kickoff clock times are taken from https://www.nfl.com/injuries/, which labels
  them "EST". The schedule page renders the same games under a "LOCAL" caption
  without a zone, so the zone comes from the injury page only.

Season context: 2026 NFL regular season. As of the reads below, 44 games had
finished (Weeks 7-9 complete, plus the Week 10 Thursday game) and 13 Week 10
games were still to be played.
"""

from __future__ import annotations

CAPTURE_DATE_UTC = "2026-11-14"

# --------------------------------------------------------------------------
# Source register
# --------------------------------------------------------------------------
# columns: source_id, publisher, title, url, read_on_utc, method, status,
#          supports, does_not_support, verbatim_evidence
SOURCES: dict[str, dict[str, str]] = {
    "SCHED-W7": {
        "publisher": "National Football League",
        "title": "NFL Schedules: Week 7, 2026 (by week)",
        "url": "https://www.nfl.com/schedules/2026/by-week/week-7",
        "read_on": CAPTURE_DATE_UTC,
        "method": "fetch_page, chunks 0-1 read in full",
        "status": "verified_direct",
        "supports": "The 14 finished Week 7 games with both club abbreviations, both point totals, the FINAL marker, the game date and the canonical per-game URL.",
        "does_not_support": "Kickoff clock times, venues, point totals for Weeks 1-6, any score not printed on the card, and any betting market.",
    },
    "SCHED-W8": {
        "publisher": "National Football League",
        "title": "NFL Schedules: Week 8, 2026 (by week)",
        "url": "https://www.nfl.com/schedules/2026/by-week/week-8",
        "read_on": CAPTURE_DATE_UTC,
        "method": "fetch_page, chunks 0-1 read in full",
        "status": "verified_direct",
        "supports": "The 14 finished Week 8 games with both clubs, both point totals, FINAL, date, and the four Week 8 bye clubs; the post-game record badge shown on each card.",
        "does_not_support": "Point-in-time records for the bye clubs (the bye panel prints records as of the render date, not as of Week 8).",
    },
    "SCHED-W9": {
        "publisher": "National Football League",
        "title": "NFL Schedules: Week 9, 2026 (by week)",
        "url": "https://www.nfl.com/schedules/2026/by-week/week-9",
        "read_on": CAPTURE_DATE_UTC,
        "method": "fetch_page, chunks 0-1 read in full",
        "status": "verified_direct",
        "supports": "The 15 finished Week 9 games with both clubs, both point totals, FINAL, date, and the two Week 9 bye clubs; the post-game record badge shown on each card; the Madrid international game marker.",
        "does_not_support": "Kickoff times (the FINAL cards print only 'Nov 5'/'Nov 8'/'Nov 9'), and any betting market.",
    },
    "SCHED-W10": {
        "publisher": "National Football League",
        "title": "NFL Schedules: Week 10, 2026 (by week)",
        "url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "read_on": CAPTURE_DATE_UTC,
        "method": "fetch_page, chunks 0-1 read in full (chunk 2 is the bye panel and flexible-scheduling text)",
        "status": "verified_direct",
        "supports": "The 14 Week 10 matchups, which one of them is FINAL with both point totals, the remaining 13 as scheduled with date, network and the Munich/Fox international marker, and the four Week 10 bye clubs.",
        "does_not_support": "Any score for the 13 unplayed games, any kickoff time zone (the page captions times as LOCAL), and any betting market, price or line.",
    },
    "STANDINGS": {
        "publisher": "National Football League",
        "title": "2026 NFL Division Standings",
        "url": "https://www.nfl.com/standings/division/2026/reg",
        "read_on": CAPTURE_DATE_UTC,
        "method": "fetch_page, chunks 0-1 read in full",
        "status": "verified_direct",
        "supports": "For each of the 32 clubs: conference, division, W, L, T, PCT, PF, PA, NET PTS and the LEGEND that defines those column names.",
        "does_not_support": "The meaning of two further numeric columns rendered by the table (the published LEGEND does not define them), the as-of timestamp of the snapshot beyond 'the page as displayed on the read date', week-by-week splits, and any betting market.",
    },
    "INJURIES": {
        "publisher": "National Football League",
        "title": "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season",
        "url": "https://www.nfl.com/injuries/",
        "read_on": CAPTURE_DATE_UTC,
        "method": "fetch_page, chunks 0-6 read (chunk 7 is footer); all 28 Week 10 clubs captured",
        "status": "verified_direct",
        "supports": "Per club: the game slot (date, EST kickoff, networks), the pre-game record in parentheses, and every listed player with position, injury text, practice status and game status.",
        "does_not_support": "Depth charts, snap counts, which player replaces whom, who is 'first string', contract or roster-status detail, and any quantified effect of an absence on scoring. The page is a list of designations, not a ranking.",
    },
    "NEWS-ROUNDUP": {
        "publisher": "National Football League",
        "title": "Injury news headlines printed on the Week 10 injury-report page",
        "url": "https://www.nfl.com/injuries/",
        "read_on": CAPTURE_DATE_UTC,
        "method": "The NEWS block rendered under the Week 10 report (headline text captured verbatim; the linked articles were not opened)",
        "status": "verified_direct_headline_only",
        "supports": "The headline strings themselves, each with its canonical nfl.com article URL - including the Patriots/TreVeyon Henderson IR move, the Dolphins/Malik Willis IR move, Sam Darnold ruled out with Drew Lock starting, Browns starting Deshaun Watson, Cardinals starting Carson Beck, and the Ravens/Lamar Jackson absence window.",
        "does_not_support": "The body text of those articles. Only what the headline states is used, and the two headlines that disagree about Jackson's absence window are published side by side rather than reconciled (see flagged.csv D966-F13).",
    },
    "NFL-TERMS": {
        "publisher": "NFL Enterprises LLC",
        "title": "NFL.com Terms and Terms of Use (host page)",
        "url": "https://www.nfl.com/legal/terms/",
        "read_on": "not read this session - see boundary note",
        "method": "Not fetched in this session. The rights boundary used by this pack is the one recorded by session 309921cc (register row NFL3-S01, read 2026-11-13) at data/nfl_309921cc/sources.csv.",
        "status": "prior_session_read_cited",
        "supports": "Only the statement that this repository's own register must stay non-commercial and informational and is not a licensed data feed, as recorded by the prior session's verbatim excerpt.",
        "does_not_support": "Any permission to redistribute, any commercial use, and any warranty about the data. A re-read by the owner (or a licensed feed agreement) is listed in suggestions.csv row D966-S12.",
    },
    "REPO": {
        "publisher": "sassnarep3-star/Own6 (this repository)",
        "title": "Repository record of prior-session snapshots and shared gates",
        "url": "https://github.com/sassnarep3-star/Own6",
        "read_on": CAPTURE_DATE_UTC,
        "method": "git + read_file on the checked-out tree at base commit 36c6f84",
        "status": "verified_direct",
        "supports": "Facts about this repository: which packs exist, which files each owns, the prior sessions' dated captures, the shared gates and their rules. The repository is the authoritative record of its own content.",
        "does_not_support": "Any NFL fact. A prior session's capture is cited here as evidence that the capture exists and what it said on its read date - never as independent confirmation of an NFL value.",
    },
}


def url_for(source_id: str) -> str:
    return SOURCES[source_id]["url"]


def link_for(source_id: str) -> str:
    """Official source link for a published table row."""
    return SOURCES[source_id]["url"]


# --------------------------------------------------------------------------
# 1. Verified results feed: finished games, copied from the game cards
# --------------------------------------------------------------------------
# game_id, week, date_utc_label, slot_label, away, home, away_pts, home_pts, src
FINAL_GAMES: list[tuple[str, int, str, str, str, str, int, int, str]] = [
    # Week 7 - Thu Oct 22, Sun Oct 25, Mon Oct 26
    ("2026-W07-01", 7, "2026-10-22", "Thursday Night Football", "NE", "CHI", 24, 30, "SCHED-W7"),
    ("2026-W07-02", 7, "2026-10-25", "International Game (Saint-Denis)", "PIT", "NO", 16, 10, "SCHED-W7"),
    ("2026-W07-03", 7, "2026-10-25", "Sunday", "SF", "ATL", 20, 29, "SCHED-W7"),
    ("2026-W07-04", 7, "2026-10-25", "Sunday", "CIN", "BAL", 35, 13, "SCHED-W7"),
    ("2026-W07-05", 7, "2026-10-25", "Sunday", "TB", "CAR", 43, 13, "SCHED-W7"),
    ("2026-W07-06", 7, "2026-10-25", "Sunday", "NYG", "HOU", 27, 21, "SCHED-W7"),
    ("2026-W07-07", 7, "2026-10-25", "Sunday", "IND", "MIN", 10, 16, "SCHED-W7"),
    ("2026-W07-08", 7, "2026-10-25", "Sunday", "MIA", "NYJ", 28, 25, "SCHED-W7"),
    ("2026-W07-09", 7, "2026-10-25", "Sunday", "CLE", "TEN", 27, 24, "SCHED-W7"),
    ("2026-W07-10", 7, "2026-10-25", "Sunday", "DEN", "ARI", 30, 16, "SCHED-W7"),
    ("2026-W07-11", 7, "2026-10-25", "Sunday", "GB", "DET", 17, 20, "SCHED-W7"),
    ("2026-W07-12", 7, "2026-10-25", "Sunday", "LA", "LV", 35, 21, "SCHED-W7"),
    ("2026-W07-13", 7, "2026-10-25", "Sunday Night Football", "KC", "SEA", 3, 20, "SCHED-W7"),
    ("2026-W07-14", 7, "2026-10-26", "Monday Night Football", "DAL", "PHI", 38, 21, "SCHED-W7"),
    # Week 8 - Thu Oct 29, Sun Nov 1, Mon Nov 2
    ("2026-W08-01", 8, "2026-10-29", "Thursday Night Football", "CAR", "GB", 19, 27, "SCHED-W8"),
    ("2026-W08-02", 8, "2026-11-01", "Sunday", "BAL", "BUF", 10, 36, "SCHED-W8"),
    ("2026-W08-03", 8, "2026-11-01", "Sunday", "TEN", "CIN", 36, 43, "SCHED-W8"),
    ("2026-W08-04", 8, "2026-11-01", "Sunday", "ARI", "DAL", 33, 30, "SCHED-W8"),
    ("2026-W08-05", 8, "2026-11-01", "Sunday", "MIN", "DET", 15, 19, "SCHED-W8"),
    ("2026-W08-06", 8, "2026-11-01", "Sunday", "IND", "JAX", 7, 42, "SCHED-W8"),
    ("2026-W08-07", 8, "2026-11-01", "Sunday", "LV", "NYJ", 38, 33, "SCHED-W8"),
    ("2026-W08-08", 8, "2026-11-01", "Sunday", "CLE", "PIT", 6, 27, "SCHED-W8"),
    ("2026-W08-09", 8, "2026-11-01", "Sunday", "ATL", "TB", 0, 16, "SCHED-W8"),
    ("2026-W08-10", 8, "2026-11-01", "Sunday", "LAC", "LA", 9, 24, "SCHED-W8"),
    ("2026-W08-11", 8, "2026-11-01", "Sunday", "KC", "DEN", 24, 28, "SCHED-W8"),
    ("2026-W08-12", 8, "2026-11-01", "Sunday", "NE", "MIA", 24, 19, "SCHED-W8"),
    ("2026-W08-13", 8, "2026-11-01", "Sunday Night Football", "PHI", "WAS", 10, 27, "SCHED-W8"),
    ("2026-W08-14", 8, "2026-11-02", "Monday Night Football", "CHI", "SEA", 34, 17, "SCHED-W8"),
    # Week 9 - Thu Nov 5, Sun Nov 8, Mon Nov 9
    ("2026-W09-01", 9, "2026-11-05", "Thursday Night Football", "JAX", "BAL", 33, 10, "SCHED-W9"),
    ("2026-W09-02", 9, "2026-11-08", "International Game (Madrid)", "CIN", "ATL", 34, 17, "SCHED-W9"),
    ("2026-W09-03", 9, "2026-11-08", "Sunday", "DEN", "CAR", 26, 21, "SCHED-W9"),
    ("2026-W09-04", 9, "2026-11-08", "Sunday", "DAL", "IND", 27, 23, "SCHED-W9"),
    ("2026-W09-05", 9, "2026-11-08", "Sunday", "NYJ", "KC", 12, 35, "SCHED-W9"),
    ("2026-W09-06", 9, "2026-11-08", "Sunday", "DET", "MIA", 19, 9, "SCHED-W9"),
    ("2026-W09-07", 9, "2026-11-08", "Sunday", "CLE", "NO", 22, 23, "SCHED-W9"),
    ("2026-W09-08", 9, "2026-11-08", "Sunday", "NYG", "PHI", 19, 11, "SCHED-W9"),
    ("2026-W09-09", 9, "2026-11-08", "Sunday", "LA", "WAS", 20, 13, "SCHED-W9"),
    ("2026-W09-10", 9, "2026-11-08", "Sunday", "HOU", "LAC", 44, 22, "SCHED-W9"),
    ("2026-W09-11", 9, "2026-11-08", "Sunday", "LV", "SF", 17, 38, "SCHED-W9"),
    ("2026-W09-12", 9, "2026-11-08", "Sunday", "GB", "NE", 45, 27, "SCHED-W9"),
    ("2026-W09-13", 9, "2026-11-08", "Sunday", "ARI", "SEA", 3, 17, "SCHED-W9"),
    ("2026-W09-14", 9, "2026-11-08", "Sunday Night Football", "TB", "CHI", 24, 27, "SCHED-W9"),
    ("2026-W09-15", 9, "2026-11-09", "Monday Night Football", "BUF", "MIN", 23, 6, "SCHED-W9"),
    # Week 10 - only the Thursday game has finished as of the read
    ("2026-W10-01", 10, "2026-11-12", "Thursday Night Football", "WAS", "NYG", 24, 21, "SCHED-W10"),
]

GAME_URL = {
    "2026-W07-01": "patriots-at-bears-2026-reg-7",
    "2026-W07-02": "steelers-at-saints-2026-reg-7",
    "2026-W07-03": "49ers-at-falcons-2026-reg-7",
    "2026-W07-04": "bengals-at-ravens-2026-reg-7",
    "2026-W07-05": "buccaneers-at-panthers-2026-reg-7",
    "2026-W07-06": "giants-at-texans-2026-reg-7",
    "2026-W07-07": "colts-at-vikings-2026-reg-7",
    "2026-W07-08": "dolphins-at-jets-2026-reg-7",
    "2026-W07-09": "browns-at-titans-2026-reg-7",
    "2026-W07-10": "broncos-at-cardinals-2026-reg-7",
    "2026-W07-11": "packers-at-lions-2026-reg-7",
    "2026-W07-12": "rams-at-raiders-2026-reg-7",
    "2026-W07-13": "chiefs-at-seahawks-2026-reg-7",
    "2026-W07-14": "cowboys-at-eagles-2026-reg-7",
    "2026-W08-01": "panthers-at-packers-2026-reg-8",
    "2026-W08-02": "ravens-at-bills-2026-reg-8",
    "2026-W08-03": "titans-at-bengals-2026-reg-8",
    "2026-W08-04": "cardinals-at-cowboys-2026-reg-8",
    "2026-W08-05": "vikings-at-lions-2026-reg-8",
    "2026-W08-06": "colts-at-jaguars-2026-reg-8",
    "2026-W08-07": "raiders-at-jets-2026-reg-8",
    "2026-W08-08": "browns-at-steelers-2026-reg-8",
    "2026-W08-09": "falcons-at-buccaneers-2026-reg-8",
    "2026-W08-10": "chargers-at-rams-2026-reg-8",
    "2026-W08-11": "chiefs-at-broncos-2026-reg-8",
    "2026-W08-12": "patriots-at-dolphins-2026-reg-8",
    "2026-W08-13": "eagles-at-commanders-2026-reg-8",
    "2026-W08-14": "bears-at-seahawks-2026-reg-8",
    "2026-W09-01": "jaguars-at-ravens-2026-reg-9",
    "2026-W09-02": "bengals-at-falcons-2026-reg-9",
    "2026-W09-03": "broncos-at-panthers-2026-reg-9",
    "2026-W09-04": "cowboys-at-colts-2026-reg-9",
    "2026-W09-05": "jets-at-chiefs-2026-reg-9",
    "2026-W09-06": "lions-at-dolphins-2026-reg-9",
    "2026-W09-07": "browns-at-saints-2026-reg-9",
    "2026-W09-08": "giants-at-eagles-2026-reg-9",
    "2026-W09-09": "rams-at-commanders-2026-reg-9",
    "2026-W09-10": "texans-at-chargers-2026-reg-9",
    "2026-W09-11": "raiders-at-49ers-2026-reg-9",
    "2026-W09-12": "packers-at-patriots-2026-reg-9",
    "2026-W09-13": "cardinals-at-seahawks-2026-reg-9",
    "2026-W09-14": "buccaneers-at-bears-2026-reg-9",
    "2026-W09-15": "bills-at-vikings-2026-reg-9",
    "2026-W10-01": "commanders-at-giants-2026-reg-10",
    "2026-W10-02": "patriots-at-lions-2026-reg-10",
    "2026-W10-03": "chiefs-at-falcons-2026-reg-10",
    "2026-W10-04": "texans-at-browns-2026-reg-10",
    "2026-W10-05": "vikings-at-packers-2026-reg-10",
    "2026-W10-06": "dolphins-at-colts-2026-reg-10",
    "2026-W10-07": "panthers-at-saints-2026-reg-10",
    "2026-W10-08": "bills-at-jets-2026-reg-10",
    "2026-W10-09": "jaguars-at-titans-2026-reg-10",
    "2026-W10-10": "rams-at-cardinals-2026-reg-10",
    "2026-W10-11": "seahawks-at-raiders-2026-reg-10",
    "2026-W10-12": "49ers-at-cowboys-2026-reg-10",
    "2026-W10-13": "steelers-at-bengals-2026-reg-10",
    "2026-W10-14": "chargers-at-ravens-2026-reg-10",
}


def game_url(game_id: str) -> str:
    return f"https://www.nfl.com/games/{GAME_URL[game_id]}"


# --------------------------------------------------------------------------
# 2. Week 10 slate as scheduled (13 unplayed + 1 finished), times from the
#    injury-report page which prints the zone
# --------------------------------------------------------------------------
# game_id, date_et, kickoff_et, network, away, home, status, src
WEEK10_SLATE: list[tuple[str, str, str, str, str, str, str, str]] = [
    ("2026-W10-01", "2026-11-12", "8:15 PM EST", "Prime Video", "WAS", "NYG", "final", "SCHED-W10"),
    ("2026-W10-02", "2026-11-15", "9:30 AM EST", "FOX, FOX DEPORTES", "NE", "DET", "scheduled", "INJURIES"),
    ("2026-W10-03", "2026-11-15", "1:00 PM EST", "CBS", "KC", "ATL", "scheduled", "INJURIES"),
    ("2026-W10-04", "2026-11-15", "1:00 PM EST", "FOX", "HOU", "CLE", "scheduled", "INJURIES"),
    ("2026-W10-05", "2026-11-15", "1:00 PM EST", "FOX", "MIN", "GB", "scheduled", "INJURIES"),
    ("2026-W10-06", "2026-11-15", "1:00 PM EST", "CBS", "MIA", "IND", "scheduled", "INJURIES"),
    ("2026-W10-07", "2026-11-15", "1:00 PM EST", "FOX", "CAR", "NO", "scheduled", "INJURIES"),
    ("2026-W10-08", "2026-11-15", "1:00 PM EST", "CBS", "BUF", "NYJ", "scheduled", "INJURIES"),
    ("2026-W10-09", "2026-11-15", "1:00 PM EST", "FOX", "JAX", "TEN", "scheduled", "INJURIES"),
    ("2026-W10-10", "2026-11-15", "4:05 PM EST", "CBS", "LA", "ARI", "scheduled", "INJURIES"),
    ("2026-W10-11", "2026-11-15", "4:05 PM EST", "CBS", "SEA", "LV", "scheduled", "INJURIES"),
    ("2026-W10-12", "2026-11-15", "4:25 PM EST", "FOX, FOX DEPORTES", "SF", "DAL", "scheduled", "INJURIES"),
    ("2026-W10-13", "2026-11-15", "8:20 PM EST", "NBC, UNIVERSO", "PIT", "CIN", "scheduled", "INJURIES"),
    ("2026-W10-14", "2026-11-16", "8:15 PM EST", "ESPN, ABC, ESPN2, ESPN DEPORTES", "LAC", "BAL", "scheduled", "INJURIES"),
]

WEEK10_BYE_CLUBS = ["CHI", "DEN", "PHI", "TB"]
WEEK9_BYE_CLUBS = ["PIT", "TEN"]
WEEK8_BYE_CLUBS = ["HOU", "NO", "NYG", "SF"]
WEEK7_BYE_CLUBS = ["BUF", "JAX", "LAC", "WAS"]


# --------------------------------------------------------------------------
# 3. Official division standings, exactly as the 2026-11-14 read displayed them
# --------------------------------------------------------------------------
# abbr, conference, division, w, l, t, pct, pf, pa, net_pts
STANDINGS: list[tuple[str, str, str, int, int, int, str, int, int, int]] = [
    ("BUF", "AFC", "AFC East", 7, 1, 0, "0.875", 256, 187, 69),
    ("NE", "AFC", "AFC East", 5, 4, 0, "0.556", 211, 207, 4),
    ("NYJ", "AFC", "AFC East", 2, 7, 0, "0.222", 182, 223, -41),
    ("MIA", "AFC", "AFC East", 1, 7, 0, "0.125", 126, 200, -74),
    ("PIT", "AFC", "AFC North", 6, 2, 0, "0.750", 180, 144, 36),
    ("CIN", "AFC", "AFC North", 6, 2, 0, "0.750", 240, 175, 65),
    ("CLE", "AFC", "AFC North", 5, 4, 0, "0.556", 161, 196, -35),
    ("BAL", "AFC", "AFC North", 4, 5, 0, "0.444", 189, 236, -47),
    ("JAX", "AFC", "AFC South", 6, 2, 0, "0.750", 229, 121, 108),
    ("HOU", "AFC", "AFC South", 3, 5, 0, "0.375", 209, 192, 17),
    ("IND", "AFC", "AFC South", 2, 7, 0, "0.222", 184, 249, -65),
    ("TEN", "AFC", "AFC South", 1, 7, 0, "0.125", 144, 199, -55),
    ("DEN", "AFC", "AFC West", 7, 2, 0, "0.778", 198, 186, 12),
    ("KC", "AFC", "AFC West", 6, 2, 0, "0.750", 202, 143, 59),
    ("LV", "AFC", "AFC West", 4, 5, 0, "0.444", 238, 268, -30),
    ("LAC", "AFC", "AFC West", 0, 8, 0, "0.000", 121, 219, -98),
    ("NYG", "NFC", "NFC East", 5, 3, 1, "0.611", 203, 196, 7),
    ("DAL", "NFC", "NFC East", 4, 5, 0, "0.444", 246, 236, 10),
    ("WAS", "NFC", "NFC East", 3, 5, 1, "0.389", 196, 223, -27),
    ("PHI", "NFC", "NFC East", 2, 7, 0, "0.222", 148, 221, -73),
    ("CHI", "NFC", "NFC North", 7, 2, 0, "0.778", 241, 184, 57),
    ("DET", "NFC", "NFC North", 6, 2, 0, "0.750", 222, 189, 33),
    ("MIN", "NFC", "NFC North", 6, 2, 0, "0.750", 146, 116, 30),
    ("GB", "NFC", "NFC North", 6, 3, 0, "0.667", 216, 191, 25),
    ("CAR", "NFC", "NFC South", 3, 5, 0, "0.375", 199, 219, -20),
    ("NO", "NFC", "NFC South", 3, 5, 0, "0.375", 185, 216, -31),
    ("TB", "NFC", "NFC South", 3, 6, 0, "0.333", 202, 178, 24),
    ("ATL", "NFC", "NFC South", 3, 6, 0, "0.333", 188, 223, -35),
    ("SF", "NFC", "NFC West", 7, 1, 0, "0.875", 235, 156, 79),
    ("SEA", "NFC", "NFC West", 5, 4, 0, "0.556", 202, 162, 40),
    ("LA", "NFC", "NFC West", 5, 4, 0, "0.556", 214, 181, 33),
    ("ARI", "NFC", "NFC West", 3, 6, 0, "0.333", 178, 255, -77),
]

# The LEGEND block printed under the table defines exactly these columns. Two
# further numeric columns are rendered but undefined by the legend; they are not
# captured (same boundary session 309921cc recorded as NFL3-F02).
STANDINGS_LEGEND = (
    "LEGEND - W: Wins; L: Losses; T: Ties; PCT: Winning Percentage; HOME: Home Record; "
    "ROAD: Road Record; DIV: Division Record; CONF: Conference Record; PF: Total Points For; "
    "PA: Total Points Against; NET PTS: Net Points; STRK: Streak"
)

TEAM_NAMES = {
    "BUF": "Buffalo Bills", "NE": "New England Patriots", "NYJ": "New York Jets",
    "MIA": "Miami Dolphins", "PIT": "Pittsburgh Steelers", "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns", "BAL": "Baltimore Ravens", "JAX": "Jacksonville Jaguars",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "TEN": "Tennessee Titans",
    "DEN": "Denver Broncos", "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers", "NYG": "New York Giants", "DAL": "Dallas Cowboys",
    "WAS": "Washington Commanders", "PHI": "Philadelphia Eagles", "CHI": "Chicago Bears",
    "DET": "Detroit Lions", "MIN": "Minnesota Vikings", "GB": "Green Bay Packers",
    "CAR": "Carolina Panthers", "NO": "New Orleans Saints", "TB": "Tampa Bay Buccaneers",
    "ATL": "Atlanta Falcons", "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks",
    "LA": "Los Angeles Rams", "ARI": "Arizona Cardinals",
}


# Abbreviation aliases on the official pages (recorded because the pages do not agree
# with each other, and a pack that silently picks one side of a mismatch is a pack
# nobody can reconcile). This pack uses the left-hand key everywhere.
CLUB_ABBR_ALIASES = {
    "ARI": ("nfl.com/schedules and nfl.com/games logo paths print ARI; "
            "nfl.com/injuries and nfl.com/standings print AZ", "ARI"),
    "LA": ("nfl.com/schedules logo paths print LA; nfl.com/injuries prints LAR", "LA"),
    "WAS": ("both spellings seen historically; the pages read this session print WAS", "WAS"),
}


# --------------------------------------------------------------------------
# 4. Record badges printed on each finished game card.
#    A card's badge is the club's record *after* the game on that card, which was
#    established by cross-week consistency (see the module docstring). These are
#    used as an independent official check on the point-in-time aggregates that
#    results.py derives from the standings page by subtraction.
# --------------------------------------------------------------------------
# week -> {abbr: (w, l, t)}
CARD_BADGES: dict[int, dict[str, tuple[int, int, int]]] = {
    7: {
        "NE": (4, 3, 0), "CHI": (5, 2, 0), "PIT": (5, 2, 0), "NO": (2, 5, 0),
        "SF": (6, 1, 0), "ATL": (3, 4, 0), "CIN": (4, 2, 0), "BAL": (4, 3, 0),
        "TB": (2, 5, 0), "CAR": (3, 3, 0), "NYG": (4, 2, 1), "HOU": (2, 5, 0),
        "IND": (2, 5, 0), "MIN": (6, 0, 0), "MIA": (1, 5, 0), "NYJ": (2, 5, 0),
        "CLE": (5, 2, 0), "TEN": (1, 6, 0), "DEN": (5, 2, 0), "ARI": (2, 5, 0),
        "GB": (4, 3, 0), "DET": (4, 2, 0), "LA": (3, 4, 0), "LV": (3, 4, 0),
        "KC": (5, 1, 0), "SEA": (4, 3, 0), "DAL": (3, 4, 0), "PHI": (2, 5, 0),
    },
    8: {
        "CAR": (3, 4, 0), "GB": (5, 3, 0), "BAL": (4, 4, 0), "BUF": (6, 1, 0),
        "TEN": (1, 7, 0), "CIN": (5, 2, 0), "ARI": (3, 5, 0), "DAL": (3, 5, 0),
        "MIN": (6, 1, 0), "DET": (5, 2, 0), "IND": (2, 6, 0), "JAX": (5, 2, 0),
        "LV": (4, 4, 0), "NYJ": (2, 6, 0), "CLE": (5, 3, 0), "PIT": (6, 2, 0),
        "ATL": (3, 5, 0), "TB": (3, 5, 0), "LAC": (0, 7, 0), "LA": (4, 4, 0),
        "KC": (5, 2, 0), "DEN": (6, 2, 0), "NE": (5, 3, 0), "MIA": (1, 6, 0),
        "PHI": (2, 6, 0), "WAS": (2, 4, 1), "CHI": (6, 2, 0), "SEA": (4, 4, 0),
    },
    9: {
        "JAX": (6, 2, 0), "BAL": (4, 5, 0), "CIN": (6, 2, 0), "ATL": (3, 6, 0),
        "DEN": (7, 2, 0), "CAR": (3, 5, 0), "DAL": (4, 5, 0), "IND": (2, 7, 0),
        "NYJ": (2, 7, 0), "KC": (6, 2, 0), "DET": (6, 2, 0), "MIA": (1, 7, 0),
        "CLE": (5, 4, 0), "NO": (3, 5, 0), "NYG": (5, 2, 1), "PHI": (2, 7, 0),
        "LA": (5, 4, 0), "WAS": (2, 5, 1), "HOU": (3, 5, 0), "LAC": (0, 8, 0),
        "LV": (4, 5, 0), "SF": (7, 1, 0), "GB": (6, 3, 0), "NE": (5, 4, 0),
        "ARI": (3, 6, 0), "SEA": (5, 4, 0), "TB": (3, 6, 0), "CHI": (7, 2, 0),
        "BUF": (7, 1, 0), "MIN": (6, 2, 0),
    },
    10: {
        "WAS": (3, 5, 1), "NYG": (5, 3, 1),
    },
}


# --------------------------------------------------------------------------
# 5. Official Week 10 injury report, transcribed from https://www.nfl.com/injuries/
#    one row per listed player: club|player|pos|injury|practice_status|game_status
#    Blank game_status means the page left the cell blank (player listed for
#    practice-status reporting only) - it is NOT a designation of "available".
# --------------------------------------------------------------------------
INJURY_REPORT_W10_RAW = """\
WAS|John Bates|TE||Full Participation in Practice|
WAS|Treylon Burks|WR||Did Not Participate In Practice|
WAS|Jayden Daniels|QB||Full Participation in Practice|
WAS|Matt Gulbin|C||Full Participation in Practice|
WAS|Chig Okonkwo|TE||Full Participation in Practice|
WAS|Lucas Patrick|C|Concussion|Did Not Participate In Practice|Out
WAS|Amik Robertson|CB||Limited Participation in Practice|
WAS|Shy Tuttle|DT||Full Participation in Practice|
WAS|Colson Yankoff|TE|Knee|Did Not Participate In Practice|Out
NYG|Abdul Carter|LB||Full Participation in Practice|
NYG|Jermaine Eluemunor|T||Full Participation in Practice|
NYG|Malik Harrison|LB|Groin|Limited Participation in Practice|Questionable
NYG|Colton Hood|CB||Full Participation in Practice|
NYG|Theo Johnson|TE||Full Participation in Practice|
NYG|Charlie Jones|WR||Full Participation in Practice|
NYG|J.J. McCarthy|QB||Full Participation in Practice|
NYG|Darnell Mooney|WR||Full Participation in Practice|
NYG|Malik Nabers|WR||Full Participation in Practice|
NYG|Cam Skattebo|RB||Full Participation in Practice|
NYG|Andrew Thomas|T||Full Participation in Practice|
NE|Ben Brown|C|Knee|Did Not Participate In Practice|Out
NE|A.J. Brown|WR|Ankle, Knee|Limited Participation in Practice|Questionable
NE|Kevin Byard|S|Chest|Full Participation in Practice|Questionable
NE|Carlton Davis III|CB|Knee|Did Not Participate In Practice|Out
NE|Reggie Gilliam|FB|Knee|Limited Participation in Practice|Questionable
NE|TreVeyon Henderson|RB|Illness|Did Not Participate In Practice|Out
NE|Hunter Henry|TE||Limited Participation in Practice|
NE|Cameron Latu|TE|Back|Limited Participation in Practice|Questionable
NE|Drake Maye|QB||Full Participation in Practice|
NE|Morgan Moses|T||Full Participation in Practice|
NE|Walter Rouse|T|Concussion|Limited Participation in Practice|Questionable
NE|Brenden Schooler|S|Hamstring|Limited Participation in Practice|Questionable
NE|Rhamondre Stevenson|RB|Knee|Limited Participation in Practice|Questionable
NE|Greg Van Roten|G|Hamstring|Full Participation in Practice|Questionable
NE|Charles Woods|CB|Hamstring|Full Participation in Practice|Questionable
DET|Brian Branch|S||Full Participation in Practice|
DET|Jared Goff|QB||Full Participation in Practice|
DET|Kerby Joseph|S|Knee|Did Not Participate In Practice|Out
DET|Cade Mays|C|Ankle|Did Not Participate In Practice|Out
DET|D.J. Reed|CB|Hip|Did Not Participate In Practice|Out
DET|Jacob Saylors|RB||Full Participation in Practice|
DET|Amon-Ra St. Brown|WR|Rib|Limited Participation in Practice|Questionable
DET|Sione Vaki|RB|Ankle|Limited Participation in Practice|Questionable
DET|DJ Wonnum|DE||Full Participation in Practice|
KC|Jeffrey Bassa|LB||Full Participation in Practice|
KC|Mansoor Delane|CB|Shoulder|Full Participation in Practice|Questionable
KC|Justin Fields|QB||Full Participation in Practice|
KC|Jaden Hicks|S||Full Participation in Practice|
KC|Travis Kelce|TE||Full Participation in Practice|
KC|Patrick Mahomes|QB||Full Participation in Practice|
KC|Jaylon Moore|T|Ankle|Did Not Participate In Practice|Out
KC|Omarr Norman-Lott|DT|Knee|Limited Participation in Practice|Out
KC|Jaydn Ott|RB|Hamstring|Limited Participation in Practice|Questionable
KC|Rashee Rice|WR||Full Participation in Practice|
KC|Kenneth Walker III|RB|Groin|Did Not Participate In Practice|Questionable
KC|Peter Woods|DT|Neck|Did Not Participate In Practice|Out
KC|Xavier Worthy|WR||Full Participation in Practice|
ATL|Zachariah Branch|WR|Hamstring|Did Not Participate In Practice|Out
ATL|Kendal Daniels|LB||Full Participation in Practice|
ATL|Divine Deablo|LB|Forearm|Did Not Participate In Practice|Doubtful
ATL|Gervon Dexter Sr.|DT|Illness|Limited Participation in Practice|Questionable
ATL|Jake Matthews|T||Limited Participation in Practice|
ATL|Liam McCullough|LS||Did Not Participate In Practice|
ATL|James Pearce Jr.|DE|Back|Limited Participation in Practice|Questionable
ATL|Za'Darius Smith|DE||Full Participation in Practice|
ATL|Jawaan Taylor|T||Limited Participation in Practice|
ATL|Cameron Thomas|DE||Full Participation in Practice|
ATL|Josh Woods|LB|Ankle|Full Participation in Practice|Questionable
MIN|Jordan Addison|WR|Thumb|Limited Participation in Practice|Questionable
MIN|Blake Cashman|LB|Concussion|Limited Participation in Practice|Out
MIN|Christian Darrisaw|T||Did Not Participate In Practice|
MIN|T.J. Hockenson|TE|Wrist, Chest|Did Not Participate In Practice|Out
MIN|Tyrion Ingram-Dawkins|DT|Ankle|Did Not Participate In Practice|Out
MIN|Theo Jackson|S||Full Participation in Practice|
MIN|Jauan Jennings|WR|Calf|Did Not Participate In Practice|Out
MIN|Josh Metellus|S|Shoulder|Limited Participation in Practice|Questionable
MIN|Kyler Murray|QB|Hamstring|Did Not Participate In Practice|Out
MIN|Harrison Smith|S||Limited Participation in Practice|
MIN|Kyle Van Noy|LB|Calf|Limited Participation in Practice|Questionable
MIN|Jay Ward|S||Full Participation in Practice|
MIN|Carson Wentz|QB||Full Participation in Practice|
GB|Aaron Banks|G||Limited Participation in Practice|
GB|Chris Brooks|RB|Ankle|Limited Participation in Practice|Questionable
GB|Javon Bullard|S|Ankle, Knee|Limited Participation in Practice|Questionable
GB|Zaire Franklin|LB|Shin|Did Not Participate In Practice|Doubtful
GB|Travis Glover|G|Knee|Limited Participation in Practice|Questionable
GB|Ty'Ron Hopper|LB||Full Participation in Practice|
GB|Josh Jacobs|RB|Finger|Did Not Participate In Practice|Out
GB|Xavier McKinney|S|Foot|Limited Participation in Practice|Questionable
GB|Bo Melton|WR||Full Participation in Practice|
GB|Skyy Moore|WR|Ankle|Limited Participation in Practice|Questionable
GB|Micah Parsons|LB|Knee, Illness|Limited Participation in Practice|Out
GB|Sean Rhyan|C|Ankle|Did Not Participate In Practice|Out
GB|Trey Smack|K||Full Participation in Practice|
GB|Lukas Van Ness|LB|Back|Limited Participation in Practice|Questionable
GB|Josh Whyle|TE|Concussion|Did Not Participate In Practice|Out
GB|Savion Williams|WR||Limited Participation in Practice|
GB|Kevin Zeitler|G|Ankle, Triceps|Did Not Participate In Practice|Questionable
JAX|Jessie Bates|S|Not injury related - resting player|Limited Participation in Practice|Out
JAX|Ezra Cleveland|G||Full Participation in Practice|
JAX|Branson Combs|LB||Full Participation in Practice|
JAX|Jordan Davis|DT|Not injury related - resting player|Limited Participation in Practice|Out
JAX|BJ Green II|DE|Forearm|Full Participation in Practice|Out
JAX|Robert Hainsey|C|Concussion|Limited Participation in Practice|Questionable
JAX|Antonio Johnson|S||Limited Participation in Practice|
JAX|Jakobi Meyers|WR||Limited Participation in Practice|
JAX|Chris Rodriguez Jr.|RB||Limited Participation in Practice|
JAX|Bhayshul Tuten|RB||Limited Participation in Practice|
JAX|Travon Walker|DE||Limited Participation in Practice|
TEN|Cody Barton|LB|Concussion|Did Not Participate In Practice|Out
TEN|John Franklin-Myers|DE||Full Participation in Practice|
TEN|Marcus Harris|CB||Full Participation in Practice|
TEN|Anthony Hill Jr.|LB|Neck|Did Not Participate In Practice|Out
TEN|Jaylon Jones|CB||Full Participation in Practice|
TEN|JC Latham|T||Full Participation in Practice|
TEN|Tony Pollard|RB||Full Participation in Practice|
TEN|Peter Skoronski|G|Hamstring|Did Not Participate In Practice|Out
TEN|Tyjae Spears|RB|Knee|Full Participation in Practice|Questionable
TEN|Carnell Tate|WR|Shoulder|Did Not Participate In Practice|Out
TEN|Tommy Townsend|P|Knee, Achilles|Did Not Participate In Practice|Out
TEN|Kevin Winston Jr.|S||Full Participation in Practice|
BUF|Alec Anderson|G||Full Participation in Practice|
BUF|Christian Benford|CB|Wrist|Full Participation in Practice|Questionable
BUF|Terrel Bernard|LB||Did Not Participate In Practice|
BUF|Spencer Brown|T|Ankle|Did Not Participate In Practice|Doubtful
BUF|Dion Dawkins|T||Full Participation in Practice|
BUF|Sam Franklin Jr.|S|Shoulder|Limited Participation in Practice|Questionable
BUF|Greg Gaines|DT||Full Participation in Practice|
BUF|Jordan Hancock|CB|Hamstring|Full Participation in Practice|Questionable
BUF|Dalton Kincaid|TE||Full Participation in Practice|
BUF|Connor McGovern|C||Full Participation in Practice|
BUF|Ed Oliver|DE||Did Not Participate In Practice|
BUF|Ar'maj Reed-Adams|G||Full Participation in Practice|
BUF|T.J. Sanders|DE||Full Participation in Practice|
BUF|Tyrell Shavers|WR|Knee|Full Participation in Practice|Questionable
NYJ|Jarvis Brownlee Jr.|CB|Illness|Limited Participation in Practice|Questionable
NYJ|Omar Cooper Jr.|WR|Ankle|Full Participation in Practice|Questionable
NYJ|Adonai Mitchell|WR|Knee|Full Participation in Practice|Questionable
NYJ|Joseph Ossai|DE|Ankle|Full Participation in Practice|Questionable
NYJ|VJ Payne|S|Knee|Full Participation in Practice|Questionable
NYJ|Harrison Phillips|DT|Ankle|Full Participation in Practice|Questionable
NYJ|Trevin Wallace|LB|Groin|Did Not Participate In Practice|Out
NYJ|Garrett Wilson|WR|Concussion|Full Participation in Practice|Questionable
NYJ|Nahshon Wright|CB|Back|Full Participation in Practice|Questionable
MIA|Tucker Addington|LS||Limited Participation in Practice|
MIA|Kaytron Allen|RB||Full Participation in Practice|
MIA|Darrell Baker Jr.|CB|Knee|Full Participation in Practice|Questionable
MIA|Chris Bell|WR|Knee|Did Not Participate In Practice|Doubtful
MIA|Aaron Brewer|C|Concussion|Did Not Participate In Practice|Out
MIA|Malik Herring|DE||Full Participation in Practice|
MIA|Will Kacmarek|TE||Full Participation in Practice|
MIA|Michael Taaffe|S||Full Participation in Practice|
MIA|Dante Trader Jr.|S||Full Participation in Practice|
MIA|Jared Wayne|WR|Quadricep|Did Not Participate In Practice|Out
MIA|Jaylen Wright|RB||Full Participation in Practice|
IND|Mo Alie-Cox|TE|Groin|Did Not Participate In Practice|Out
IND|CJ Allen|LB||Full Participation in Practice|
IND|Jaylon Carlies|LB|Neck|Did Not Participate In Practice|Out
IND|Akeem Davis-Gaither|LB|Knee|Did Not Participate In Practice|Out
IND|A.J. Haulcy|S||Full Participation in Practice|
IND|Arden Key|DE|Hamstring|Full Participation in Practice|Questionable
IND|Will Mallory|TE|Hamstring|Limited Participation in Practice|Questionable
IND|Luke Rhodes|LS|Hamstring|Did Not Participate In Practice|Out
IND|Grover Stewart|DT||Full Participation in Practice|
IND|Jonathan Taylor|RB||Full Participation in Practice|
IND|Jerry Tillery|DT|Calf|Did Not Participate In Practice|Out
IND|Jalen Travis|T|Knee|Did Not Participate In Practice|Out
IND|Justin Walley|CB||Full Participation in Practice|
IND|Charvarius Ward|CB||Full Participation in Practice|
CAR|Jonathon Brooks|RB|Groin|Limited Participation in Practice|Doubtful
CAR|Brady Christensen|G|Hamstring|Full Participation in Practice|Questionable
CAR|Trevor Etienne|RB||Full Participation in Practice|
CAR|Chuba Hubbard|RB||Full Participation in Practice|
CAR|Lee Hunter|DT||Full Participation in Practice|
CAR|Mike Jackson|CB|Groin|Limited Participation in Practice|Doubtful
CAR|Will Lee III|CB|Hamstring|Limited Participation in Practice|Questionable
CAR|Xavier Legette|WR|Knee|Full Participation in Practice|Questionable
CAR|Damien Lewis|G||Full Participation in Practice|
CAR|Bobby Okereke|LB|Foot|Did Not Participate In Practice|Out
CAR|Jaelan Phillips|LB|Hamstring|Full Participation in Practice|Questionable
CAR|Torricelli Simpkins III|G||Full Participation in Practice|
NO|Kelvin Banks Jr.|T||Full Participation in Practice|
NO|CJ Donaldson|RB|Shoulder|Did Not Participate In Practice|Out
NO|David Edwards|G||Full Participation in Practice|
NO|Martin Emerson|CB|Shin|Limited Participation in Practice|Questionable
NO|Travis Etienne|RB|Hamstring|Full Participation in Practice|Questionable
NO|Noah Fant|TE||Full Participation in Practice|
NO|Taliese Fuaga|T|Knee|Did Not Participate In Practice|Out
NO|Alvin Kamara|RB||Full Participation in Practice|
NO|Erik McCoy|C|Biceps|Did Not Participate In Practice|Out
NO|Christen Miller|DT|Knee|Did Not Participate In Practice|Out
NO|Asim Richards|T||Full Participation in Practice|
NO|Quincy Riley|CB||Full Participation in Practice|
HOU|Azeez Al-Shaair|LB|Groin, Not injury related - personal matter|Did Not Participate In Practice|Out
HOU|Will Anderson Jr.|DE|Ankle|Did Not Participate In Practice|Questionable
HOU|Reed Blankenship|S||Full Participation in Practice|
HOU|Trent Brown|T|Wrist, Illness|Did Not Participate In Practice|Questionable
HOU|Tank Dell|WR||Full Participation in Practice|
HOU|Blake Fisher|T||Full Participation in Practice|
HOU|Marvin Harrison Jr.|WR|Hamstring|Did Not Participate In Practice|Out
HOU|Jacob Hummel|LB|Groin|Full Participation in Practice|Questionable
HOU|Danielle Hunter|DE|Hamstring|Did Not Participate In Practice|Out
HOU|Brevin Jordan|TE|Finger, Foot|Did Not Participate In Practice|Out
HOU|Woody Marks|RB||Full Participation in Practice|
HOU|David Montgomery|RB|Groin|Full Participation in Practice|Questionable
HOU|Keylan Rutledge|G|Neck, Shoulder|Did Not Participate In Practice|Out
HOU|Jaylin Smith|CB|Hamstring|Full Participation in Practice|Questionable
HOU|Wyatt Teller|G|Illness, Back|Limited Participation in Practice|Questionable
HOU|Tommy Togiai|DT||Full Participation in Practice|
CLE|Austin Barber|T||Full Participation in Practice|
CLE|Denzel Boston|WR|Toe|Limited Participation in Practice|Questionable
CLE|Michael Burton|FB|Calf|Did Not Participate In Practice|Out
CLE|Maliek Collins|DT||Full Participation in Practice|
CLE|Harold Fannin Jr.|TE||Full Participation in Practice|
CLE|Ronnie Hickman Jr.|S|Concussion|Did Not Participate In Practice|Out
CLE|Tytus Howard|T||Full Participation in Practice|
CLE|Elgton Jenkins|C||Full Participation in Practice|
CLE|Donovan McMillon|S||Limited Participation in Practice|
CLE|Carson Schwesinger|LB||Full Participation in Practice|
CLE|Denzel Ward|CB||Limited Participation in Practice|
CLE|Quincy Williams|LB||Full Participation in Practice|
LA|Davis Allen|TE|Oblique|Limited Participation in Practice|Questionable
LA|Steve Avila|G|Hamstring|Did Not Participate In Practice|Out
LA|Joe Cardona|LS|Ankle|Limited Participation in Practice|Questionable
LA|Kam Curl|S|Toe|Limited Participation in Practice|Questionable
LA|Aaron Donald|DT||Did Not Participate In Practice|
LA|Terrance Ferguson|TE|Ankle, Hamstring|Did Not Participate In Practice|Out
LA|Braden Fiske|DT||Did Not Participate In Practice|
LA|Myles Garrett|LB|Knee, Not injury related - resting player|Did Not Participate In Practice|Questionable
LA|Tyler Higbee|TE||Limited Participation in Practice|
LA|Trent McDuffie|CB|Back|Limited Participation in Practice|Questionable
LA|Puka Nacua|WR||Did Not Participate In Practice|
LA|Colby Parkinson|TE||Full Participation in Practice|
LA|Matthew Stafford|QB||Full Participation in Practice|
LA|Byron Young|LB||Did Not Participate In Practice|
ARI|Budda Baker|S||Full Participation in Practice|
ARI|Zachary Carter|DT|Knee|Limited Participation in Practice|Out
ARI|Hjalte Froholdt|C|Concussion|Did Not Participate In Practice|Out
ARI|Jon Gaines II|G|Ankle|Did Not Participate In Practice|Out
ARI|Bam Knight|RB||Full Participation in Practice|
ARI|Hunter Long|TE|Knee|Limited Participation in Practice|Questionable
ARI|Roy Lopez|DT|Toe, Ankle|Limited Participation in Practice|Questionable
ARI|Max Melton|CB|Knee, Hand|Limited Participation in Practice|Questionable
ARI|Darius Robinson|DT|Wrist|Limited Participation in Practice|Questionable
ARI|Isaac Seumalo|G||Full Participation in Practice|
ARI|Dante Stills|DT||Full Participation in Practice|
ARI|Josh Sweat|LB||Full Participation in Practice|
ARI|Jayden Williams|T|Knee|Limited Participation in Practice|Questionable
ARI|Mack Wilson|LB||Full Participation in Practice|
ARI|Andrew Wingard|S|Groin|Did Not Participate In Practice|Questionable
SEA|AJ Barner|TE||Full Participation in Practice|
SEA|Anthony Bradford|G||Full Participation in Practice|
SEA|Charles Cross|T|Ankle|Did Not Participate In Practice|Out
SEA|Sam Darnold|QB|Ribs, Quadricep|Did Not Participate In Practice|Out
SEA|Derick Hall|LB||Did Not Participate In Practice|
SEA|Drew Lock|QB||Limited Participation in Practice|
SEA|Quenton Nelson|G|Knee|Did Not Participate In Practice|Out
SEA|Uchenna Nwosu|LB||Full Participation in Practice|
SEA|Patrick O'Connell|LB||Full Participation in Practice|
SEA|Connor O'Toole|LB||Full Participation in Practice|
SEA|Brandon Pili|DT||Full Participation in Practice|
SEA|Jarran Reed|DT||Full Participation in Practice|
SEA|Rashid Shaheed|WR||Full Participation in Practice|
SEA|Jaxon Smith-Njigba|WR||Full Participation in Practice|
SEA|Leonard Williams|DT|Stinger|Did Not Participate In Practice|Out
LV|Thomas Booker|DT|Ankle|Full Participation in Practice|Questionable
LV|Foley Fatukasi|DT||Full Participation in Practice|
LV|Ian Thomas|TE||Full Participation in Practice|
LV|Dont'e Thornton Jr.|WR|Back|Did Not Participate In Practice|Questionable
LV|Trey Zuhn III|C||Full Participation in Practice|
SF|Mike Evans|WR|Achilles|Did Not Participate In Practice|Out
SF|Renardo Green|CB|Back|Limited Participation in Practice|Questionable
SF|Dre Greenlaw|LB|Knee|Limited Participation in Practice|Questionable
SF|Nate Hobbs|CB|Groin|Full Participation in Practice|Questionable
SF|Deommodore Lenoir|CB|Foot|Limited Participation in Practice|Questionable
SF|Christian McCaffrey|RB||Full Participation in Practice|
SF|Siran Neal|S||Full Participation in Practice|
SF|Demarcus Robinson|WR||Full Participation in Practice|
SF|Deebo Samuel Sr.|WR||Full Participation in Practice|
SF|Upton Stout|CB|Shoulder, Neck|Limited Participation in Practice|Questionable
SF|C.J. West|DT|Knee|Full Participation in Practice|Questionable
SF|Trent Williams|T|Shoulder|Did Not Participate In Practice|Questionable
DAL|DaRon Bland|CB|Ankle|Limited Participation in Practice|Questionable
DAL|Jonathan Bullard|DT|Calf|Full Participation in Practice|Questionable
DAL|Alijah Clark|S|Illness|Did Not Participate In Practice|Questionable
DAL|Donovan Ezeiruaku|LB|Ankle|Did Not Participate In Practice|Out
DAL|Jake Ferguson|TE|Knee, Ankle|Did Not Participate In Practice|Out
DAL|Tyler Goodson|RB|Ankle, Knee|Did Not Participate In Practice|Out
DAL|Malik Hooker|S||Did Not Participate In Practice|
DAL|Marist Liufau|LB||Full Participation in Practice|
DAL|P.J. Locke|S|Concussion|Did Not Participate In Practice|Out
DAL|Von Miller|LB||Did Not Participate In Practice|
DAL|Jonathan Mingo|WR|Ankle|Did Not Participate In Practice|Out
DAL|Devin Moore|CB|Hip|Full Participation in Practice|Questionable
DAL|DeMarvion Overshown|LB||Full Participation in Practice|
DAL|George Pickens|WR||Full Participation in Practice|
DAL|Joey Porter Jr.|CB|Ankle, Foot|Limited Participation in Practice|Questionable
DAL|Luke Schoonmaker|TE||Full Participation in Practice|
DAL|Brevyn Spann-Ford|TE||Full Participation in Practice|
DAL|Juanyeh Thomas|S|Hamstring|Did Not Participate In Practice|Doubtful
DAL|KaVontae Turpin|WR||Full Participation in Practice|
PIT|Brandin Echols|CB||Full Participation in Practice|
PIT|DeShon Elliott|S||Full Participation in Practice|
PIT|Derrick Harmon|DT|Foot|Full Participation in Practice|Questionable
PIT|Cameron Heyward|DT||Full Participation in Practice|
PIT|Ben Skowronek|WR||Full Participation in Practice|
PIT|Doneiko Slaughter|CB||Full Participation in Practice|
PIT|Darnell Washington|TE||Full Participation in Practice|
PIT|T.J. Watt|LB||Full Participation in Practice|
CIN|Jonathan Allen|DT||Limited Participation in Practice|
CIN|Jalen Davis|CB|Hamstring|Full Participation in Practice|Doubtful
CIN|Kyle Dugger|S|Quadricep|Did Not Participate In Practice|Out
CIN|Dylan Fairchild|G||Full Participation in Practice|
CIN|B.J. Hill|DT||Did Not Participate In Practice|
CIN|Andrei Iosivas|WR|Thumb|Full Participation in Practice|Doubtful
CIN|Dexter Lawrence|DT||Did Not Participate In Practice|
CIN|Brian Parker II|G|Knee|Full Participation in Practice|Doubtful
CIN|DJ Turner II|CB||Full Participation in Practice|
LAC|Kayode Awosika|G||Limited Participation in Practice|
LAC|Bud Dupree|DE||Did Not Participate In Practice|
LAC|Justin Eboigbe|DE||Limited Participation in Practice|
LAC|Alex Harkey|G||Full Participation in Practice|
LAC|Tre Harris|WR||Full Participation in Practice|
LAC|Cam Hart|CB||Full Participation in Practice|
LAC|Daiyan Henley|LB||Full Participation in Practice|
LAC|Deane Leonard|CB||Full Participation in Practice|
LAC|Khalil Mack|LB||Full Participation in Practice|
LAC|Ladd McConkey|WR||Did Not Participate In Practice|
LAC|Keaton Mitchell|RB||Limited Participation in Practice|
LAC|David Njoku|TE||Limited Participation in Practice|
LAC|Denzel Perryman|LB||Full Participation in Practice|
LAC|Trey Pipkins|T||Did Not Participate In Practice|
LAC|Rodney Shelley|CB||Limited Participation in Practice|
LAC|Branson Taylor|G||Did Not Participate In Practice|
LAC|Brenen Thompson|WR||Did Not Participate In Practice|
LAC|Isas Waxter|CB||Did Not Participate In Practice|
LAC|Kendall Williamson|S||Did Not Participate In Practice|
BAL|Rasheen Ali|RB||Full Participation in Practice|
BAL|Rashod Bateman|WR||Full Participation in Practice|
BAL|Calais Campbell|DT||Did Not Participate In Practice|
BAL|Kyle Hamilton|S||Full Participation in Practice|
BAL|Jaylinn Hawkins|S|Knee|Limited Participation in Practice|Out
BAL|Matthew Hibner|TE||Full Participation in Practice|
BAL|Olaivavega Ioane|G||Full Participation in Practice|
BAL|Adam Randall|RB|Neck, Hamstring|Full Participation in Practice|Questionable
BAL|Ronnie Stanley|T||Did Not Participate In Practice|
BAL|Nate Wiggins|CB||Full Participation in Practice|
"""

# Position groups, as the report abbreviates them. Offence / defence / special
# teams assignment is a plain-language grouping of the position label the page
# prints; it is stated here so the grouping is reproducible, and it is not an
# NFL-published taxonomy (flagged as D966-F05).
POSITION_UNIT = {
    "QB": "offence", "RB": "offence", "FB": "offence", "WR": "offence",
    "TE": "offence", "T": "offence", "G": "offence", "C": "offence",
    "LB": "defence", "DE": "defence", "DT": "defence", "CB": "defence", "S": "defence",
    "K": "special", "P": "special", "LS": "special",
}

# --------------------------------------------------------------------------
# 6. Official headlines printed on the same injury-report page, quoted verbatim.
#    Used only to record a replacement fact the report table itself does not carry
#    (a player moved to injured reserve, or which backup is named to start).
# --------------------------------------------------------------------------
OFFICIAL_HEADLINES: list[tuple[str, str, str]] = [
    (
        "NE", "Patriots place RB TreVeyon Henderson (illness) on injured reserve",
        "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14",
    ),
    (
        "MIA", "Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start",
        "https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start",
    ),
    (
        "SEA", "Sam Darnold ruled out for Seahawks' Week 10 game vs. Raiders; Drew Lock expected to start again",
        "https://www.nfl.com/news/sam-darnold-ruled-out-for-seahawks-week-10-game-vs-raiders-drew-lock-expected-to-start-again",
    ),
    (
        "SEA", "Drew Lock (elbow/oblique) has no injury designation, will start for Seahawks vs. Raiders",
        "https://www.nfl.com/news/drew-lock-no-injury-designation-seahawks-raiders",
    ),
    (
        "CLE", "NFL news roundup: Browns to start QB Deshaun Watson vs. Texans; Cardinals' Carson Beck to start vs. Rams",
        "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11",
    ),
    (
        "BAL", "NFL news roundup: Ravens confirm Lamar Jackson expected to miss 6-10 weeks; Kenneth Walker questionable",
        "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-friday-nov-13",
    ),
    (
        "BAL", "NFL Network: Ravens' Lamar Jackson (right thumb) out 6-9 weeks, expects to return this season",
        "https://www.nfl.com/news/ravens-lamar-jackson-right-thumb-out-6-9-weeks-expects-to-return-this-season",
    ),
    (
        "LA", "Rams WR Puka Nacua likely to be placed on injured reserve with turf toe, sprained MCL and PCL",
        "https://www.nfl.com/news/rams-wr-puka-nacua-likely-to-be-placed-on-injured-reserve-with-turf-toe-sprained-mcl-and-pcl",
    ),
    (
        "GB", "Packers RB Josh Jacobs to undergo surgery on finger this week; timeline to return TBD",
        "https://www.nfl.com/news/packers-rb-josh-jacobs-to-undergo-surgery-on-finger-this-week",
    ),
    (
        "BUF", "NFL news roundup: Bills acquire S Amani Hooker; Broncos trade for Chargers' Daiyan Henley",
        "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-tuesday-nov-10",
    ),
    (
        "NYG", "NFL news roundup: J.J. McCarthy expected to play Week 10; Justin Herbert avoids finger fracture",
        "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-monday-nov-9",
    ),
]
