"""The flag register.

A flag row exists for every place where this pack publishes nothing, or publishes a value
with a caveat attached. The rule is: an empty cell is never silent. If we could not read a
value from an official page, the cell is empty and there is a flag row that says which
cell, why, and what would fill it.

Severity is about what a reader might wrongly conclude, not about effort.
"""

from __future__ import annotations

from . import capture as C

U = C.SOURCE_URL

# id, severity, table(s), what is blank or caveated, why, what would fill it, source url
FLAGS = [
    ("48217-F01", "high", "originated_lines_schema.csv, leaderboard.csv",
     "every market_line_* and difference_* cell",
     "No official or licensed source in this environment publishes operator prices. An "
     "estimated price would be a fabricated input, so the cells stay empty.",
     "A licensed price feed, or a written data-use agreement with an operator, recorded in "
     "the price-data policy (gate G2).", U["S2"]),

    ("48217-F02", "high", "depth_route_probe.csv, depth_of_replacement.csv",
     "every depth-order and named-replacement cell",
     "nfl.com's per-club /depth-chart route returns HTTP 404, and the roster route publishes "
     "no depth order. The report itself names no replacement.",
     "A dated, attributed depth row for each of the 32 clubs (gate G4).", U["S9"]),

    ("48217-F03", "high", "week9_inactives.csv, depth_route_probe.csv",
     "every snap-count cell",
     "No official page read this session publishes snap counts. The roster page prints "
     "roster status codes only.",
     "A snap-count source verified for all 32 clubs (gate G4).", U["S8"]),

    ("48217-F04", "high", "standings_point_in_time.csv",
     "the as-of-render standings are not published as a through-Week-9 table",
     "nfl.com/standings renders live. At capture time it already contained the nine completed "
     "Week 10 games. The through-Week-9 table is reconstructed by subtraction and is what the "
     "pack publishes.",
     "Nothing: this is handled. It is flagged because a reader who opens the official page "
     "later will see different numbers.", U["S3"]),

    ("48217-F05", "medium", "injury_report_2026_11_15.csv",
     "club record badges shown beside each fixture on the injury page",
     "Those badges render as-of-capture and already include completed Week 10 results. They "
     "are not captured and not used.",
     "Nothing: the pack uses explicit final scores from the schedule page instead.", U["S1"]),

    ("48217-F06", "medium", "results_feed.csv",
     "3 Week 10 in-progress games and 2 unstarted games have no final score",
     "At capture time those games had not finished. Their in-progress scores are published in "
     "a separate table plainly marked in-progress.",
     "Re-read the schedule page after the games finish.", U["S2"]),

    ("48217-F07", "medium", "venues.csv",
     "venue for all 14 Week 10 fixtures",
     "The by-week schedule page prints no venue. The official inactives page does print WHERE, "
     "and 13 Week 9 venues were transcribed from it.",
     "Read the inactives page or the game centre page for each Week 10 fixture (question Q08).",
     U["S5"]),

    ("48217-F08", "high", "injury_report_2026_11_15.csv",
     "every delta column",
     "Only one capture of the injury report exists, so no change between reads can be "
     "computed, and the surprise signal cannot be constructed.",
     "A second and third capture in the same week (suggestion SUG-05).", U["S1"]),

    ("48217-F09", "medium", "designation_calibration.csv",
     "the play rate for 'Out' and 'Doubtful'",
     "The only official page that publishes a designation together with its resolution is the "
     "Sunday pregame page, and it covered Questionable players only.",
     "A designation-to-inactive join across several weeks (question Q06, gate G6).", U["S4"]),

    ("48217-F10", "medium", "designation_calibration.csv",
     "the width of the interval around the Questionable play rate",
     "n = 11 definite resolutions, and the sample is not random: it is the set of players "
     "NFL.com chose to write about, which skews to starters and to genuinely doubtful cases.",
     "A population sample of every Questionable player with an outcome, not a reported "
     "subset.", U["S4"]),

    ("48217-F11", "low", "sources.csv",
     "prior-seasons injury archive",
     "The injury page has a season selector going back decades, but only 2026 Week 10 was read "
     "this session.",
     "Read and archive the weekly reports for at least two prior seasons (question Q06).",
     U["S1"]),

    ("48217-F12", "medium", "depth_route_probe.csv",
     "the Texans image-depth and Packers jersey-prefix parsing failures",
     "Neither can be reproduced: no club depth page was read, because the nfl.com route is a "
     "404 and no club page was fetched this session.",
     "Probe the 32 club-hosted depth pages and record the format of each (suggestion SUG-02).",
     U["S9"]),

    ("48217-F13", "medium", "injury_report_2026_11_15.csv",
     "the club attribution of every player on the report",
     "One attribution was checked end to end (Kenneth Walker III is on the Kansas City roster) "
     "and it held. The other 346 rows were not individually checked against a roster.",
     "A club-by-club roster sweep joined to the report.", U["S8"]),

    ("48217-F14", "medium", "injury_report_2026_11_15.csv",
     "completeness of the transcription across the 8 chunks the page was served in",
     "The page was served in eight chunks and each was transcribed by hand. Every club's rows "
     "are in surname order across the chunk joins, which is consistent with no rows being "
     "lost, but that is a consistency check, not a proof.",
     "A machine-readable capture of the page, diffed against this transcription.", U["S1"]),

    ("48217-F15", "medium", "reserve_list.csv",
     "the Lamar Jackson reserve move",
     "An official NFL.com news story dated 2026-11-05 reports that the Ravens placed Lamar "
     "Jackson on injured reserve, but no row for him appears in the November reserve-list "
     "table as captured, whose earliest row is dated 11/07.",
     "Re-read the reserve-list route for the full month and check whether the table is "
     "paginated or truncated.", U["S7"]),

    ("48217-F16", "medium", "injury_report_2026_11_15.csv",
     "terms-of-use position on republishing the raw rows",
     "The full 347 injury rows are republished on the public site. The NFL terms page was not "
     "read this session.",
     "Read the terms page and decide whether raw rows move behind the private layer "
     "(suggestion SUG-04, question Q13).", U["S1"]),

    ("48217-F17", "low", "team_ratings_naive.csv",
     "opponent adjustment",
     "The rating is margin per game with no opponent adjustment, because the game log does not "
     "exist yet. It is published so the gap is visible and is labelled unusable for "
     "origination.",
     "The game-by-game log (gate G3).", U["S3"]),
]

FLAG_COLUMNS = [
    "flag_id", "severity", "affected_tables", "what_is_blank_or_caveated", "why",
    "what_would_fill_it", "official_source_url",
]


def flags():
    return [dict(zip(FLAG_COLUMNS, f)) for f in FLAGS]


def flag_index():
    """map table file -> flag ids, so every blank cell can be traced."""
    out = {}
    for f in flags():
        for table in f["affected_tables"].split(","):
            out.setdefault(table.strip(), []).append(f["flag_id"])
    return out


#: Tables that legitimately contain empty cells. Two distinct reasons appear here and the
#: distinction matters: (a) the official page itself printed nothing, and (b) a value we
#: refuse to invent. Neither is a gap in capture, and neither is zero.
EXPECTED_BLANKS = {
    "injury_report_2026_11_15.csv":
        "injury and game_status: the official table printed nothing in these cells",
    "depth_of_replacement.csv":
        "replacement_named and replacement_source_url: the official report names no "
        "replacement, so the pack refuses to name one",
    "originated_lines_schema.csv":
        "model_fair_line, market_line, difference, inputs_json, probability and "
        "published_at_utc: no licensed price source, so no market was originated",
    "designation_calibration.csv":
        "Out and Doubtful rows: no official page read this session publishes a "
        "designation-to-outcome join for those designations",
    "week10_live_scores.csv":
        "away_points and home_points for the two games that had not kicked off: nothing to "
        "report yet",
    "week10_slate.csv":
        "venue (the official by-week schedule page prints no venue) and the score columns "
        "for games that were not final at capture time",
    "roster_events.csv":
        "starter_announced: the official transactions page does not say who starts",
    "trades.csv":
        "starter_announced: the official transactions page does not say who starts",
    "luck_panel.csv":
        "strategy-level luck removal: blocked until a strategy has 100 prospective graded "
        "forecasts (gate G8)",
    "price_capture_attempts.csv":
        "what_the_page_actually_contains for the operator route: the route was deliberately "
        "not consulted, so there is nothing to report",
    "blank_audit.csv":
        "flag_ids is empty on tables that have no blanks, which is the point of the "
        "column; the column is not itself sourced to an external page",
    "requirements_decision_readiness.csv":
        "blocking_gate is empty on every cleared requirement by construction, and the "
        "source cell is empty where the requirement is a property of this repository "
        "rather than of an external page",
}
