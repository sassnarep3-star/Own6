"""The requirement trace for session a119bb6d.

The identifiers are the ones used by the ``data/nfl_0ce967db/requirements.csv``
register, so the two can be read together. Each row states what is true now
*because of the official Game Books*, what still blocks the requirement, and
the number that would clear that gate.

Nothing here claims more than the official documents support. A requirement
that the league does not publish the evidence for stays blocked, with the
reason written down.
"""

from __future__ import annotations

REQUIREMENTS = [
    {
        "req_id": "R25",
        "requirement": (
            "Use official NFL Game Books for actual starters and game-day status; "
            "do not infer depth rank or snaps"
        ),
        "state": "met",
        "what_is_now_true": (
            "The league publishes an official Game Book for every game, linked from its own "
            "game centre. It carries the official starting eleven on both sides, the "
            "game-day Not Active list, the Did Not Play list, the substitutes who played, "
            "the stadium, the roof and surface designation, the game-day weather, the score "
            "by quarter and the paid attendance. Every game book read is recorded with its "
            "URL and SHA-256 so it can be re-downloaded and confirmed."
        ),
        "blocking_gate": "",
        "number_that_would_clear_it": "",
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R10",
        "requirement": (
            "Build the availability graph as a first-class dataset "
            "(who was expected to start, who actually did)"
        ),
        "state": "met",
        "what_is_now_true": (
            "data/nfl_a119bb6d/availability_graph.csv holds one row per club, unit and "
            "position slot per game: the expected starter (the same club's official starter "
            "at that slot in its previous game, read from the previous Game Book), the actual "
            "starter, the change type and the replacement depth. Both sides of the ball are "
            "covered, so the graph can be read as an offence-versus-defence match-up."
        ),
        "blocking_gate": "",
        "number_that_would_clear_it": "",
        "source_url": "https://www.nfl.com/games/patriots-at-lions-2026-reg-10",
    },
    {
        "req_id": "R94",
        "requirement": "Availability graph first-class (repeat of R10)",
        "state": "met",
        "what_is_now_true": (
            "Same dataset as R10; it is published as its own page rather than as a note "
            "inside another pack's table."
        ),
        "blocking_gate": "",
        "number_that_would_clear_it": "",
        "source_url": "https://www.nfl.com/games/patriots-at-lions-2026-reg-10",
    },
    {
        "req_id": "R39",
        "requirement": (
            "Add an announced-starter evidence field (not an inferred replacement)"
        ),
        "state": "met",
        "what_is_now_true": (
            "The starting eleven in the Game Book is the league's own record of the "
            "announced lineup, so the announced starter is now an official field rather "
            "than an inference from a depth chart."
        ),
        "blocking_gate": "",
        "number_that_would_clear_it": "",
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R28",
        "requirement": "Capture official inactive lists and snap counts",
        "state": "partially_met",
        "what_is_now_true": (
            "The official game-day inactive list is captured for every game read: the Game "
            "Book's own Not Active block, cross-checked against the league's weekly "
            "inactive-list article, which is also captured and hashed."
        ),
        "blocking_gate": (
            "Snap counts: the official Game Book contains no snap count and no player "
            "participation table. A scan of a complete document finds 0 lines containing "
            "'snap' and 0 containing 'participation'. The league does not publish an "
            "official snap count in this document."
        ),
        "number_that_would_clear_it": (
            "One official, league-published per-player snap count source covering every "
            "game, with a documented URL and terms"
        ),
        "source_url": "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season",
    },
    {
        "req_id": "R53",
        "requirement": (
            "Use snap counts as the starter proxy when the depth chart is unavailable"
        ),
        "state": "blocked",
        "what_is_now_true": (
            "The requirement is now testable: the Game Book's Not Active list and the "
            "Substitutions list are the league's own record of who was unavailable and who "
            "was a replacement, which is the same information a snap count would give at "
            "the margin."
        ),
        "blocking_gate": (
            "No official snap-count source exists in the Game Book. The league publishes "
            "no club depth chart either: "
            "https://www.nfl.com/teams/houston-texans/roster/depth-chart/ returns the "
            "league's 404 page."
        ),
        "number_that_would_clear_it": (
            "One club-by-club official depth chart page for all 32 clubs, or one official "
            "league snap-count feed, with a recorded source and date per row"
        ),
        "source_url": "https://www.nfl.com/teams/houston-texans/roster/depth-chart/",
    },
    {
        "req_id": "R11",
        "requirement": (
            "Do not model depth from jersey order; model it from playing time"
        ),
        "state": "blocked",
        "what_is_now_true": (
            "The rejection of the jersey-order shortcut is enforced in code: the depth "
            "feature this pack builds counts only players the Game Book shows were "
            "unavailable, and never the order of a list. The league's own roster and "
            "depth pages are captured with hashes so the shortcut can be shown to be "
            "wrong rather than merely avoided."
        ),
        "blocking_gate": (
            "Playing time is not published in the official Game Book, so depth from "
            "playing time cannot yet be modelled from an official source."
        ),
        "number_that_would_clear_it": (
            "An official league snap-count feed, or a verified club depth chart for all 32 "
            "clubs, before any depth rank is published"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R06",
        "requirement": "Track the depth of the replacement, not just the fact of a replacement",
        "state": "partially_met",
        "what_is_now_true": (
            "Every replacement in the availability graph carries a depth lower bound: the "
            "number of the club's previous starters at that position who the Game Book "
            "shows were inactive or did not play, plus one. A replacement that took over "
            "from one unavailable starter is at least second string by league evidence; a "
            "replacement that took over from two is at least third string."
        ),
        "blocking_gate": (
            "The league publishes no depth chart and no snap counts, so the true string "
            "cannot be established from an official source; only the lower bound can."
        ),
        "number_that_would_clear_it": (
            "One official depth order for all 32 clubs, verified club by club, which would "
            "replace the lower bound with the real string"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R41",
        "requirement": (
            "Calibrate what 'Questionable' means empirically instead of using old percentages"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The designation is now measured: every player the league designated is joined "
            "to the official Game Book of the same week, and the page publishes the count, "
            "the play rate and a Wilson 95% interval for each designation."
        ),
        "blocking_gate": (
            "The sample is bounded by the number of Game Books read so far. A league-wide "
            "calibration needs the Game Books of the archived seasons."
        ),
        "number_that_would_clear_it": (
            "Every regular-season game of at least three completed seasons parsed from its "
            "official Game Book, giving a multi-season designation table with n per row"
        ),
        "source_url": "https://www.nfl.com/injuries/",
    },
    {
        "req_id": "R50",
        "requirement": (
            "Score injury-designation reliability before using it as a feature"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The reliability table is published with n and an interval per designation, so a "
            "designation can only be used as a feature once its measured play rate is known."
        ),
        "blocking_gate": "Multi-season sample; see R41.",
        "number_that_would_clear_it": "See R41.",
        "source_url": "https://www.nfl.com/injuries/",
    },
    {
        "req_id": "R51",
        "requirement": (
            "Snapshot the nfl.com injury report every Wed, Thu and Fri and keep a dated history"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The capture is automated: the workflow "
            ".github/workflows/nfl-a119bb6d-capture.yml runs at 21:00 UTC on Wednesday, "
            "Thursday and Friday and writes the injury-report hub, the week-specific "
            "injury report and the weekly inactive-list article into a dated ledger with a "
            "SHA-256 for each read."
        ),
        "blocking_gate": (
            "The dated history only grows from the day the job first runs; a back-dated "
            "series cannot be created from an official source after the fact."
        ),
        "number_that_would_clear_it": (
            "One full in-season Wed/Thu/Fri series for 2026 with one capture per day and "
            "no missing weekday"
        ),
        "source_url": "https://www.nfl.com/injuries/",
    },
    {
        "req_id": "R95",
        "requirement": "Snapshot nfl.com injury report Wed/Thu/Fri (repeat of R51)",
        "state": "partially_met",
        "what_is_now_true": "See R51.",
        "blocking_gate": "See R51.",
        "number_that_would_clear_it": "See R51.",
        "source_url": "https://www.nfl.com/injuries/",
    },
    {
        "req_id": "R52",
        "requirement": (
            "Treat the injury report as a timestamped series, not a weekly snapshot"
        ),
        "state": "met",
        "what_is_now_true": (
            "Every read of the injury report is stored with its own clock time and hash, so "
            "two reads of the same URL on different days are two records and their "
            "difference is a computable delta."
        ),
        "blocking_gate": "",
        "number_that_would_clear_it": "",
        "source_url": "https://www.nfl.com/injuries/",
    },
    {
        "req_id": "R44",
        "requirement": (
            "Point-in-Time Snapshot Ledger for injuries, depth charts and inactives"
        ),
        "state": "met",
        "what_is_now_true": (
            "The ledger is published: every official read this pack makes is recorded with "
            "its URL, its clock time and the SHA-256 of the bytes read. A backtest can "
            "therefore be replayed against the document as it was known at the time."
        ),
        "blocking_gate": "",
        "number_that_would_clear_it": "",
        "source_url": "https://www.nfl.com/injuries/league/2026/reg10",
    },
    {
        "req_id": "R36",
        "requirement": "Add durable snapshot storage and alerts",
        "state": "partially_met",
        "what_is_now_true": (
            "Storage is durable: the captures live in the repository with their hashes, so "
            "they survive a rebuild and can be re-verified. The scheduled job fails loudly "
            "and its manifest is published, so a failed or missing capture is visible "
            "rather than silent."
        ),
        "blocking_gate": (
            "No freshness alert yet: nothing watches the age of the newest capture and "
            "raises an alarm when the league has moved on."
        ),
        "number_that_would_clear_it": (
            "One scheduled freshness check that fails when the newest capture of the "
            "injury hub is older than the expected capture window"
        ),
        "source_url": "https://www.nfl.com/injuries/",
    },
    {
        "req_id": "R23",
        "requirement": (
            "Transcribe the venue of every fixture from the official game centre and publish it"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The venue, city, roof and surface designation and the game-day weather of "
            "every game read are published from the official Game Book, which names the "
            "stadium and city directly. The league's weekly inactive-list article adds the "
            "same venue from the league's own fixture listing, which is a second official "
            "source for the same fact."
        ),
        "blocking_gate": (
            "Only the weeks whose Game Books have been read are transcribed."
        ),
        "number_that_would_clear_it": (
            "One Game Book read per regular-season game of 2026, giving every fixture a "
            "venue row with a hash"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R55",
        "requirement": (
            "Stadium roof/surface and NWS hourly wind/precipitation overlay"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The roof and surface designation and the game-day weather are official and "
            "published for every game read, taken from the Game Book's own header: for "
            "example 'Retractable Roof - Closed on Field Turf' with the temperature, the "
            "humidity and the wind."
        ),
        "blocking_gate": (
            "The NWS hourly forecast grid for an upcoming game is not yet joined to the "
            "venue rows, so the overlay is retrospective rather than forward-looking."
        ),
        "number_that_would_clear_it": (
            "One NWS gridpoint forecast per upcoming fixture, joined to the venue row and "
            "published with its issue time"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R26",
        "requirement": "Ingest game-level results to make the ratings opponent-aware",
        "state": "partially_met",
        "what_is_now_true": (
            "Every game read contributes its final score, its score by quarter and its paid "
            "attendance, with the official document and hash behind each row, so a rating "
            "can be conditioned on the opponent actually faced."
        ),
        "blocking_gate": "Only the weeks whose Game Books have been read carry a result row.",
        "number_that_would_clear_it": (
            "One Game Book read per regular-season game of 2026 and 2025, giving a complete "
            "result corpus with opponent and score for every row"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R61",
        "requirement": "Capture the reserve list so 'not listed' never means 'available'",
        "state": "partially_met",
        "what_is_now_true": (
            "All 32 official club roster pages are captured with their hash and clock time "
            "on every scheduled run, so the reserve list is captured rather than assumed. "
            "The league's own game-day Not Active list is captured per game, which is the "
            "status that actually decides availability on game day."
        ),
        "blocking_gate": (
            "The per-player roster status on those pages is not yet parsed into a table, so "
            "the reserve list is captured as a document rather than as rows."
        ),
        "number_that_would_clear_it": (
            "One parsed row per player per club with the club's own status (Active, "
            "Reserve, Injured Reserve, Practice Squad) and the date it was read"
        ),
        "source_url": "https://www.nfl.com/teams/miami-dolphins/roster/",
    },
    {
        "req_id": "R63",
        "requirement": (
            "Archive weekly injury reports for past seasons (for calibration)"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The archive route exists and is captured: "
            "https://www.nfl.com/injuries/league/<season>/reg<week> serves each week of a "
            "past season, and the 2025 regular season is captured week by week with a hash "
            "and a clock time."
        ),
        "blocking_gate": (
            "The archived pages are captured as documents but are not yet parsed into the "
            "designation table, and the matching 2025 Game Books are not yet read, so no "
            "multi-season calibration can be computed yet."
        ),
        "number_that_would_clear_it": (
            "Every archived 2025 weekly injury report parsed into designation rows and "
            "joined to the 2025 Game Book of the same week"
        ),
        "source_url": "https://www.nfl.com/injuries/league/2025/reg1",
    },
    {
        "req_id": "R77",
        "requirement": (
            "Track injuries and know deficiencies in defences such as 2nd/3rd/4th string "
            "backups having to replace starters, and the same on offence"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The availability graph gives both sides of the ball: for every club, unit and "
            "position slot it names the expected starter, the actual starter and the depth "
            "of the replacement, from official Game Books. A match-up view can therefore be "
            "built from the same rows."
        ),
        "blocking_gate": (
            "The match-up matrix is not yet published as its own view, and the depth figure "
            "remains a lower bound until an official depth order exists."
        ),
        "number_that_would_clear_it": (
            "The full 2026 season of Game Books plus a published offence-versus-defence "
            "matrix that joins both clubs' per-slot personnel for every fixture"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R42",
        "requirement": (
            "Interactive Offense vs Defense Matchup Deficiency Matrix (1st-4th string)"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "Both clubs' per-slot personnel for every game read is in the availability "
            "graph, so the two halves of the matrix are available from official data."
        ),
        "blocking_gate": (
            "The matrix view is not published yet, and the string column is a lower bound "
            "because the league publishes no depth order and no snap counts."
        ),
        "number_that_would_clear_it": (
            "An official depth order for all 32 clubs, plus the published matrix joining "
            "both sides for every fixture"
        ),
        "source_url": "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10",
    },
    {
        "req_id": "R40",
        "requirement": (
            "Add an official depth-chart register with date and source per row"
        ),
        "state": "blocked",
        "what_is_now_true": (
            "The route is now known and recorded as unavailable rather than unknown: the "
            "league hosts no club depth page and "
            "https://www.nfl.com/teams/houston-texans/roster/depth-chart/ returns the "
            "league's 404 page. The club's own chart is a club document."
        ),
        "blocking_gate": (
            "No league-published depth chart exists. A register built from club sites would "
            "be a register of club documents, and the club itself labels the chart "
            "unofficial."
        ),
        "number_that_would_clear_it": (
            "A dated, sourced depth row for all 32 clubs from a club or league document "
            "whose own status is recorded on every row"
        ),
        "source_url": "https://www.nfl.com/teams/houston-texans/roster/depth-chart/",
    },
    {
        "req_id": "R43",
        "requirement": "Flag stale depth rows against the official transactions log",
        "state": "blocked",
        "what_is_now_true": (
            "The transactions log is capturable from the club's own official page, and the "
            "32 club roster pages are already captured on every scheduled run, which is "
            "where a stale entry would show up."
        ),
        "blocking_gate": (
            "There are no depth rows to check, because the league publishes no depth chart "
            "(R40)."
        ),
        "number_that_would_clear_it": (
            "A depth register (R40) plus a captured transactions log per club, so each row "
            "can be compared with the club's own last transaction"
        ),
        "source_url": "https://www.nfl.com/teams/baltimore-ravens/roster/",
    },
    {
        "req_id": "R31",
        "requirement": "Treat roster turnover as a first-class data event",
        "state": "partially_met",
        "what_is_now_true": (
            "Roster state is captured as a dated document rather than assumed: every "
            "scheduled run records all 32 club roster pages with their hash and clock time, "
            "so a change in roster status between two captures is visible."
        ),
        "blocking_gate": (
            "The transactions log itself is not yet captured, and the per-player status is "
            "not yet parsed, so turnover is a diff of two documents rather than an event row."
        ),
        "number_that_would_clear_it": (
            "One captured transactions log per club per week and one parsed status row per "
            "player, so each transaction becomes a dated event"
        ),
        "source_url": "https://www.nfl.com/teams/miami-dolphins/roster/",
    },
    {
        "req_id": "R24",
        "requirement": (
            "Publish the league's dated schedule announcement beside the live schedule page"
        ),
        "state": "partially_met",
        "what_is_now_true": (
            "The league's dated schedule announcements are captured as part of every "
            "scheduled run, for example the 'Week 11 schedule change' notice dated "
            "Nov. 9, 2026, which prints the final week and the broadcast networks."
        ),
        "blocking_gate": (
            "The announcements are captured and hashed but not yet parsed into a dated table "
            "beside the live schedule page."
        ),
        "number_that_would_clear_it": (
            "One parsed row per dated announcement with its date and the games it changes, "
            "shown next to the live schedule"
        ),
        "source_url": "https://www.nfl.com/news/week-11-schedule-change",
    },
]
