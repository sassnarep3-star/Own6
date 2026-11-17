"""This session's official reads, kept as evidence — verbatim, clocked, and nothing inferred.

The rule the pack lives by: a value is *read* only if the text is here with the URL it came from.
Anything else on the site is either arithmetic over these rows, or another session's file quoted
with its path. The fetch tool used in this session returns page text but no response header, so
the clock is the session clock (sandbox clock is UTC) recorded as a window, not a fake per-request
second. The window is stated once and every read cites it.
"""
from __future__ import annotations

from typing import Dict, List

PACK = "nfl_dfc0c1bc"
SESSION = "dfc0c1bc"
BRANCH = "arena/dfc0c1bc-own6"

#: the full session-clock span in which the reads below were performed (sandbox clock, UTC). Two passes:
#: nine reads at 00:38-00:44Z, then two follow-ups at 01:05-01:10Z against the exact URL a price ledger cites.
#: each read carries its own `window` when it differs from the first pass, so no read borrows another's clock.
READ_WINDOW_UTC = "2026-11-17T00:38Z to 2026-11-17T01:10Z"
FIRST_PASS = "2026-11-17T00:38Z to 2026-11-17T00:44Z"
SECOND_PASS = "2026-11-17T01:05Z to 2026-11-17T01:10Z"
CLOCK_NOTE = (
    "window recorded from the session clock (sandbox timezone UTC) around the fetches; the "
    "retrieval tool returns page text and its own status, not a response Date header, so a "
    "per-request second is not claimed"
)

OFFICIAL_HOSTS = (
    "www.nfl.com", "nfl.com", "operations.nfl.com", "www.packers.com", "www.texans.com",
    "www.miamidolphins.com",
)

READS: List[Dict[str, str]] = [
    {
        "read_id": "R1",
        "url": "https://www.nfl.com/injuries/",
        "host": "www.nfl.com",
        "purpose": "state of the league injury report between weeks; Lions designation gap; which weeks the page offers",
        "verbatim": [
            "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season",
            "2026 NFL Injury Report / Injuries - WEEK 10",
            "THURSDAY, NOVEMBER 12TH 8:15 PM EST Prime Video WAS Commanders (3-5-1) NYG Giants (5-3-1)",
            "SUNDAY, NOVEMBER 15TH 9:30 AM EST FOX, FOX DEPORTES NE Patriots (5-5) DET Lions (7-2)",
            "Kerby Joseph | S | Knee | Did Not Participate In Practice | Out",
            "Cade Mays | C | Ankle | Did Not Participate In Practice | Out",
            "D.J. Reed | CB | Hip | Did Not Participate In Practice | Out",
            "A.J. Brown | WR | Ankle, Knee | Limited Participation in Practice | Questionable",
            "Carlton Davis III | CB | Knee | Did Not Participate In Practice | Out",
        ],
        "selector_observed": "season selector lists 1965-2026; week selector lists WEEK 1 to WEEK 10 only",
    },
    {
        "read_id": "R2",
        "url": "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11/boxscore",
        "host": "www.nfl.com",
        "purpose": "does an official per-game page publish player participation (snaps) for a fixture we would originate",
        "verbatim": ["404 - FLAG ON THE PLAY", "[BACK TO NFL.COM](https://www.nfl.com/)"],
        "selector_observed": "page returned the site's 404 body; the fixture is scheduled for Nov 22 and had not been played when read",
    },
    {
        "read_id": "R3",
        "url": "https://www.nfl.com/teams/green-bay-packers/depth-chart/",
        "host": "www.nfl.com",
        "purpose": "does nfl.com host a club depth chart at the conventional route",
        "verbatim": ["404 - Flag on the Play.", "[BACK TO NFL.COM](https://www.nfl.com/ \"BACK TO NFL.COM\")"],
        "selector_observed": "404 body only; no redirect to a depth page was offered by the page",
    },
    {
        "read_id": "R4",
        "url": "https://www.packers.com/team/depth-chart",
        "host": "www.packers.com",
        "purpose": "route (a) test: is a club-hosted depth chart machine-readable, dated, and how is it labelled",
        "verbatim": [
            "Green Bay Packers Depth Chart",
            "Unofficial, Nov. 10, 2026",
            "WR | 9 Christian Watson | 16 Bo Melton | (empty)",
            "WR | 0 Matthew Golden | 87 J. Michael Sturdivant | (empty)",
            "WR | 83 Savion Williams | (empty) | (empty)",
            "QB | 10 Jordan Love | 6 Tyrod Taylor | (empty)",
            "S | 29 Xavier McKinney | 27 Kitan Oladapo | (empty)",
            "S | 33 Evan Williams | 27 Kitan Oladapo | (empty)",
            "PR | (empty) | 0 Matthew Golden | (empty)",
        ],
        "selector_observed": ("table with three player columns and no rank labels; names prefixed with jersey numbers; "
                              "WR appears in three separate rows; one safety appears in two rows; empty cells present"),
    },
    {
        "read_id": "R5",
        "url": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "host": "www.nfl.com",
        "purpose": "the next slate to originate: fixtures, dates, kickoff, network, records as printed",
        "verbatim": [
            "Thursday Night Football, November 19th — Colts at Texans, Thursday, November 19th, 8:15 PM, PRIME (COLTS 3-7, TEXANS 3-6)",
            "Dolphins at Bills, Sunday, November 22nd, 1:00 PM, CBS (DOLPHINS 1-8, BILLS 8-1)",
            "Ravens at Panthers, Sunday, November 22nd, 1:00 PM, FOX (RAVENS 4-5, PANTHERS 4-5)",
            "Saints at Bears, Sunday, November 22nd, 1:00 PM, FOX (SAINTS 3-6, BEARS 7-2)",
            "Titans at Cowboys, Sunday, November 22nd, 1:00 PM, FOX (TITANS 1-8, COWBOYS 4-6)",
            "Buccaneers at Lions, Sunday, November 22nd, 1:00 PM, FOX (BUCCANEERS 3-6, LIONS 7-2)",
        ],
        "selector_observed": "the by-week page prints fixtures, dates, times and networks; no venue column is printed on it",
    },
    {
        "read_id": "R6",
        "url": "https://www.nfl.com/games/colts-at-texans-2026-reg-11",
        "host": "www.nfl.com",
        "purpose": "venue transcription for an unplayed fixture, and whether the game centre carries a club injury report before the report is filed",
        "verbatim": [
            "Game Info — Location LOCATION HOUSTON, TX; Stadium STADIUM RELIANT STADIUM",
            "Nov 19 8:15 PM (Prime Video network icon)",
            "Colts' Injury Report is not available at this time.",
            "Texans' Injury Report is not available at this time.",
            "AFC SOUTH: JAGUARS 7-2 0.778; TEXANS 3-6 0.333; COLTS 3-7 0.300; TITANS 1-8 0.111",
            "Indianapolis Colts, POINTS PER GAME, 20.8, ranked 23rd.",
            "Houston Texans, POINTS PER GAME, 25.9, ranked 9th.",
            "Houston Texans, TOTAL DEF SACKS, 33, ranked 2nd.",
            "Indianapolis Colts, TOTAL TURNOVER DIFFERENTIAL, -12, ranked 32nd.",
        ],
        "selector_observed": ("the 'at a glance' block publishes per-team points per game, yards per game, time of possession, "
                             "sacks, interceptions and turnover differential with rank — official inputs a model may use"),
    },
    {
        "read_id": "R7",
        "url": "https://www.nfl.com/players/malik-willis/",
        "host": "www.nfl.com",
        "purpose": "close the open question 'what is Malik Willis's roster state', which a prior pack asked against the wrong club",
        "verbatim": [
            "Malik Willis — QB • #2",
            "Related Content: 'Dolphins place QB Malik Willis (groin) on injured reserve; Kyle McCord in line for first start'",
            "article text: 'Miami Dolphins quarterback Malik Willis was placed on injured reserve Tuesday due to a groin injury. With Willis shelved, second-year QB Kyle McCord will fill in, beginning Sunday on the road against the Indianapolis Colts.'",
        ],
        "selector_observed": "the profile page itself prints no team or status field; the status lives on the club roster page (R8)",
    },
    {
        "read_id": "R8",
        "url": "https://www.nfl.com/teams/miami-dolphins/roster",
        "host": "www.nfl.com",
        "purpose": "official status code for the player above, and the league page's own link to a club depth chart",
        "verbatim": [
            "Miami Dolphins 2026 Player Roster | NFL.com — Miami Dolphins, 4th AFC East, 1 - 8 - 0",
            "Malik Willis | 2 | QB | RES | 73 | 225 | 5 | Liberty",
            "Zach Sieler | 92 | DE | RES | ...; Cole Turner | 87 | TE | RES; Rene Konga | 95 | DE | RES",
            "Trey Moore | 17 | LB | RSR",
            "DEPTH CHART (link) -> https://www.miamidolphins.com/team/depth-chart",
            "Kyle McCord | 14 | QB | ACT | 75 | 218 | 1 | Syracuse; Brady Cook | 15 | QB | ACT",
        ],
        "selector_observed": ("roster rows carry a status code column (ACT/RES/RSR/TRC/TRD/TRT observed on this page); "
                             "the page links out to the club's own depth chart"),
    },
    {
        "read_id": "R9",
        "url": "https://www.texans.com/team/depth-chart",
        "host": "www.texans.com",
        "purpose": "test the claim that one club's depth chart is not machine-readable at the conventional club path",
        "verbatim": ["404", "This page could not be found."],
        "selector_observed": "the conventional /team/depth-chart route is not the club's published route; no alternate route was located this session",
    },
    {
        # the exact URL that 39 number cells in data/nfl_d966f630/price_snapshots_open_close.csv cite beside
        # their closing numbers — read in full this session so the citation can be judged, not assumed
        "read_id": "R10",
        "window": SECOND_PASS,
        "url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "host": "www.nfl.com",
        "purpose": "does the page cited beside a closing_number cell in the d966 price ledger contain a price",
        "verbatim": [
            "NFL Week 10 Schedule 2026: Games, Times, Matchups & Tickets",
            "Thursday Night Football, November 12th",
            "Commanders 24, Giants 21, FINAL, Thursday, November 12th",
            "International Game, November 15th Munich",
            "Patriots 10, Lions 35, FINAL, Sunday, November 15th",
            "Vikings 30, Packers 10, FINAL, Sunday, November 15th",
            "Dolphins 22, Colts 24, FINAL, Sunday, November 15th",
            "49ers 46, Cowboys 40, FINAL, Sunday, November 15th",
            "WAYS TO WATCH Get a personalized view of the NFL schedule based on your location and services",
            "Tickets (link to a ticketmaster.com event page)",
        ],
        "selector_observed": "the week navigation links the previous and the next week; nothing on the page is "
                            "labelled as a line, a total, a spread or a price",
    },
    {
        "read_id": "R11",
        "window": SECOND_PASS,
        "url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "host": "www.nfl.com",
        "purpose": "what the same page carries for an unplayed fixture, for byes, and for weather",
        "verbatim": [
            "Monday Night Football, November 16th",
            "Chargers at Ravens, Monday, November 16th, 8:15 PM, ESPN",
            "CHARGERS 0-8",
            "RAVENS 4-5",
            "Weather Clearnight",
            "Teams on Bye",
            "Chicago Bears 7-2",
            "Denver Broncos 7-2",
            "Philadelphia Eagles 2-7",
            "Tampa Bay Buccaneers 3-6",
            "2026 TBD Games",
            "Specific dates and start times for the designated Week 16 matchups will be determined and "
            "announced at a later date during the season",
            "View Flexible Schedule Procedures",
        ],
        "selector_observed": "read on 2026-11-17: the Monday fixture, played the previous evening, showed a time, "
                            "a network and both records but no FINAL line, while every earlier fixture on the same "
                            "page showed one; the weather field is a one-word token with no number beside it",
    },
]

#: Observations joined to reads. ``claim`` is what a prior register asserts, ``verdict`` is what
#: this evidence supports. Empty ``claim`` = a bare fact, useful for gaps and features.
OBSERVATIONS: List[Dict[str, str]] = [
    {"obs_id": "O1", "read_id": "R1",
     "observation": "The league report page was still showing Week 10 on 2026-11-17, and its week selector stops at WEEK 10.",
     "supports": "A cadence job run today would capture nothing new; the Week 11 report had not been published yet.",
     "theme": "T03"},
    {"obs_id": "O2", "read_id": "R1",
     "observation": "Kerby Joseph, Cade Mays and D.J. Reed are each printed with practice status 'Did Not Participate In Practice' and game status 'Out'.",
     "supports": "The three Lions rows the owner flagged as blank are populated on the official page as read this session.",
     "theme": "T09"},
    {"obs_id": "O3", "read_id": "R2|R6",
     "observation": "No official per-game page for a Week 11 fixture exposed a participation/snap table, and the /boxscore route returned 404 before kickoff.",
     "supports": "Route (b) of the depth question (snap counts) has still not been located on an official host; it stays open, not disproved.",
     "theme": "T05"},
    {"obs_id": "O4", "read_id": "R3|R8",
     "observation": "nfl.com has no club depth page (404), yet nfl.com's own roster page links to the club's depth chart on the club domain.",
     "supports": "The league points at club-hosted charts without hosting them; route (a) is sanctioned but decentralised and disclaimed.",
     "theme": "T05"},
    {"obs_id": "O5", "read_id": "R4",
     "observation": "The Packers chart is dated 'Unofficial, Nov. 10, 2026', uses three player columns with no rank labels, prefixes jersey numbers, lists WR across three rows, and repeats one safety in two rows.",
     "supports": "Depth must be stored as groups of names with the raw string, not as 'the starter'; the 'Unofficial' label and the page date belong on every derived row.",
     "theme": "T05"},
    {"obs_id": "O6", "read_id": "R4|R8",
     "observation": "The chart lists two quarterbacks (Love, Taylor) while the roster page for the same club lists a third QB as active for another club; charts omit rostered players.",
     "supports": "A depth chart is not a roster: joining the two is a real data task, not a formatting detail.",
     "theme": "T06"},
    {"obs_id": "O7", "read_id": "R7|R8",
     "observation": "Malik Willis is a Miami Dolphin listed with status code RES on nfl.com's Dolphins roster, after the league's own article reported the Dolphins placed him on injured reserve.",
     "supports": "His absence from the weekly report is explained by the reserve list; the repo register that asks 'what happened to Willis' reads the Green Bay roster page instead.",
     "theme": "T06"},
    {"obs_id": "O8", "read_id": "R5|R6",
     "observation": "The by-week schedule page prints fixtures, dates, times and networks but no venue; the game centre prints Location and Stadium.",
     "supports": "Venue must come from the game centre per fixture — the schedule page cannot supply it.",
     "theme": "T15"},
    {"obs_id": "O9", "read_id": "R6",
     "observation": "The game centre for an unplayed fixture printed 'Colts' Injury Report is not available at this time' and the same for the Texans.",
     "supports": "There is a real gap between the last published report and kickoff; a per-fixture read must be time-aware, not assumed continuous.",
     "theme": "T03"},
    {"obs_id": "O10", "read_id": "R6",
     "observation": "The game centre publishes points per game, yards per game, time of possession, sacks, interceptions and turnover differential with ranks, and the AFC South standings with win percentage.",
     "supports": "Official, quotable inputs exist for fixture context and for an opponent-aware rating, without any licensed feed.",
     "theme": "T08"},
    {"obs_id": "O11", "read_id": "R9",
     "observation": "The Texans' club depth chart was not at the conventional club path; the page returned the site's 404 body.",
     "supports": "Per-club verification is required before route (a) can be claimed for 32 clubs; a 404 for one club is exactly what a blanket assumption would hide.",
     "theme": "T05"},
    {"obs_id": "O12", "read_id": "R5",
     "observation": "Records printed on the Week 11 schedule page on 2026-11-17 (e.g. Bills 8-1, Lions 7-2, Dolphins 1-8) match the standings block printed on the game centre read the same minute.",
     "supports": "Two independent official pages agree today; a same-minute cross-page check is cheap and it is the pattern the freshness alarm should use.",
     "theme": "T13"},
    {"obs_id": "O13", "read_id": "R10",
     "observation": "The by-week schedule page that 39 closing_number cells cite as their source prints fixtures, "
                    "dates, networks, final scores and club records, and no line, total or price anywhere on it; "
                    "the only commercial link on the page sells seats.",
     "supports": "CF-10 is now tested against the page itself instead of inferred from the route's name: the URL "
                 "beside those numbers cannot have published them, so it names an input, not a source.",
     "theme": "T02"},
    {"obs_id": "O14", "read_id": "R11",
     "observation": "The same page prints a one-word weather token per fixture and nothing numeric: no "
                    "temperature, wind speed or precipitation figure.",
     "supports": "G-08 stays open with its route unchanged — an official page is a display token, so an hourly "
                 "forecast grid has to come from the public-domain weather service, not from nfl.com.",
     "theme": "T04"},
    {"obs_id": "O15", "read_id": "R10|R11",
     "observation": "Every Thursday and Sunday fixture showed FINAL while the Monday fixture, played the previous "
                    "evening, showed only a time, a network and two records. The week's byes are printed as a "
                    "labelled block with records.",
     "supports": "A by-week page is not a results feed and should not be polled as one; and the bye list the task "
                 "board asked for as a file is published on this page, so that gap is a store to build, not a "
                 "source to find.",
     "theme": "T07"},
]

#: The questions this session's reads can actually answer, and the ones they leave open.
ANSWERS: List[Dict[str, str]] = [
    {"answer_id": "A1", "theme": "T06",
     "question": "What is Malik Willis's roster state, and does his absence from the weekly report mean he is available?",
     "answer": "No. nfl.com's Miami roster prints 'Malik Willis | 2 | QB | RES' and the league's own article says the Dolphins placed him on injured reserve on the Tuesday before the Week 10 win over Indianapolis. His absence from the report is a reserve-list absence.",
     "status": "CLOSED for this player",
     "reads": "R7;R8",
     "still_open": "the same join for the other 31 clubs — the roster/IR sweep is still not run for all 32",
     "note_on_repo": "the register row in data/nfl_8362b702/reserve_absence.csv attributes Willis to GB and calls the state unknown; the club attribution is wrong and the state is now documented"},
    {"answer_id": "A2", "theme": "T05",
     "question": "Which official source publishes a depth order, verified for all 32 clubs?",
     "answer": "None found on nfl.com — the league hosts no club depth page (404 read this session) but links to the club's own chart. A club chart does exist, is machine-readable and is dated, but the club itself labels it 'Unofficial'.",
     "status": "PARTIAL: 1 of 32 clubs verified as readable and dated this session; 1 club verified as not at the conventional path",
     "reads": "R3;R4;R8;R9",
     "still_open": "route (b): no official snap-count/participation table was located; and 30 clubs still unverified",
     "note_on_repo": "confirms the owner's instruction to model depth as groups (three WR rows, a repeated safety) and to keep the raw string"},
    {"answer_id": "A3", "theme": "T03",
     "question": "Can the injury report be captured on Wednesday, Thursday and Friday — is there something to capture today?",
     "answer": "Not yet this week: on 2026-11-17 the report page still displayed Week 10 and its week selector stopped at WEEK 10, while two Week 11 game centres said the clubs' reports were 'not available at this time'. A cadence job must therefore be triggered by availability, not by the calendar day alone.",
     "status": "ANSWERED with an operational consequence",
     "reads": "R1;R6",
     "still_open": "the scheduler and the store outside the static site",
     "note_on_repo": "no prior pack records whether anything was available to capture; this session's read is the first dated evidence of the between-week gap"},
    {"answer_id": "A4", "theme": "T09",
     "question": "Are the three Lions game-status blanks (Joseph, Mays, Reed) on the official page?",
     "answer": "Yes. Each of the three is printed with 'Did Not Participate In Practice' and game status 'Out' on the report read this session — the blank cells are a capture/publish failure in the site, not missing source data.",
     "status": "CLOSED for these three rows",
     "reads": "R1",
     "still_open": "the historical capture that produced the blanks cannot be repaired retroactively; the fix is the cadence job in T03",
     "note_on_repo": "the owner's brief item is confirmed against the official page"},
    {"answer_id": "A5", "theme": "T15",
     "question": "Which official page prints the venue for every fixture?",
     "answer": "The game centre prints Location and Stadium for an unplayed fixture (read for Colts at Texans, Week 11); the by-week schedule page does not print venues at all.",
     "status": "CLOSED as a source question; 1 of 13 Week 11 fixtures read this session",
     "reads": "R5;R6",
     "still_open": "the remaining Week 11 fixtures, and roof/surface, which no page read this session publishes",
     "note_on_repo": "prior packs recorded venues as 'not published' for most Week 11 fixtures at their read time; the game centre route works"},
    {"answer_id": "A6", "theme": "T08",
     "question": "Are there official inputs available for a team-strength model without a licensed feed?",
     "answer": "Yes, at fixture level: the game centre publishes points per game, yards per game, time of possession, sacks, interceptions and turnover differential with ranks, plus the division standings with win percentage. These are quotable, dated, and per-club.",
     "status": "OPENED — a new route the registers did not list",
     "reads": "R6",
     "still_open": "no game-level play-by-play, so an opponent-aware rating still needs the per-game log from T07",
     "note_on_repo": "the registers treated 'no licensed feed' as 'no official inputs'; the two are different questions"},
    {"answer_id": "A7", "theme": "T02",
     "question": "Did this session find a market price on any official page?",
     "answer": "No. Nine reads across five hosts, none printed an opening, closing or vig figure; the 404s were routes, not prices.",
     "status": "STILL OPEN — the price question cannot be answered from official pages",
     "reads": "R1;R2;R3;R4;R5;R6;R7;R8;R9",
     "still_open": "a licensed archive, or the owner's decision to freeze the pricing half",
     "note_on_repo": "this is the fifth pack to record the same negative; the board should treat it as settled evidence, not as another open task"},
    {"answer_id": "A8", "theme": "T02",
     "question": "Does the official page that the d966 price ledger cites beside its closing numbers publish a price?",
     "answer": "No. The exact URL those cells cite was read this session in full: it prints fixtures, times, "
               "final scores, club records and a links-to-tickets module, and no line, total or price anywhere. "
               "The pairing is an input citation, not a sourced market number, and the file's own columns say the "
               "numbers are ours.",
     "status": "CLOSED as a source question — and it closes it against the pack's citation, not its data",
     "reads": "R10;R11",
     "still_open": "what the owning pack does about it: relabel the column, move the URL, or both — that is their "
                   "edit, not this session's",
     "note_on_repo": "CF-10 on the conflicts page; the correction rule proposed there (a number column may not "
                      "cite a host that cannot publish that class) is the general fix"},
]


def reads() -> List[Dict[str, str]]:
    out = []
    for r in READS:
        row = dict(r)
        row["verbatim_excerpt"] = " || ".join(r["verbatim"])
        row["read_window_utc"] = r.get("window") or FIRST_PASS
        row["clock_note"] = CLOCK_NOTE
        row["evidence_class"] = "read_this_session"
        out.append(row)
    return out


def observations() -> List[Dict[str, str]]:
    return [dict(o) for o in OBSERVATIONS]


def answers() -> List[Dict[str, str]]:
    return [dict(a) for a in ANSWERS]


def read_hosts_ok() -> bool:
    return all(r["host"] in OFFICIAL_HOSTS for r in READS)


def by_theme(theme_id: str) -> Dict[str, List[Dict[str, str]]]:
    return {
        "observations": [o for o in OBSERVATIONS if o["theme"] == theme_id],
        "answers": [a for a in ANSWERS if a["theme"] == theme_id],
    }
