"""Flag register: everything irregular we saw, published as evidence.

A flag here is not an apology and not a blocker. It is the record that a value is
absent and why, or that an official page said something odd and we reproduced it
rather than quietly fixing it. The merge does not wait on flags; the site's
"Flagged for Review" page is the index.

Two kinds, kept in one table because a reader needs both in one place:

* **gaps** - a column is blank because no source we are allowed to use supplies it
  (D966-F01, F03, F06, F10, F16);
* **irregularities in the sources themselves** - an official page that looks wrong
  (D966-F12..F15). We do not repair these. A third-party correction of a league page
  would be exactly the invention the brief rules out, so the anomaly is printed and
  the affected row stays blank where it cannot be resolved.
"""

from __future__ import annotations

from . import capture as C

FLAG_FIELDS = [
    "flag_id", "kind", "title", "what_we_observed", "where_it_shows_up",
    "why_it_is_flagged", "what_we_did_instead", "does_it_block_merge", "severity",
    "human_decision_needed", "official_source_url", "read_on_utc",
]

BLOCKS = "no - a blank with a reason is a finished row, not an unfinished one"


def flag_rows() -> list[dict[str, str]]:
    raw = [
        {
            "flag_id": "D966-F01",
            "kind": "gap",
            "title": "No market price exists in this environment",
            "what_we_observed": "Four source classes were read or attempted for a price: the Week 10 schedule "
                                "page (prints matchups, times, networks, records and FINAL scores; no line), "
                                "the official injury report (designations only), a commercial odds feed (not "
                                "reachable: the session network allowlist is github.com, registry.npmjs.org, "
                                "pypi.org and their file hosts), and the prior session's published CSV, whose "
                                "market and closing columns are themselves blank.",
            "where_it_shows_up": "market_line_side, market_line_total, market_line_moneyline_home, "
                                 "difference_side, difference_total, difference_moneyline_home on every row of "
                                 "originated_lines.csv; the whole market_* block of price_snapshots.csv",
            "why_it_is_flagged": "Requirements 4 and 7 are about the *difference* between our line and the "
                                 "market's. Without a market number the difference cannot be computed, and "
                                 "inventing one would make every downstream edge statistic fictional.",
            "what_we_did_instead": "The model columns are published in full; the market and difference columns "
                                   "are left blank with a status string and this flag id on the row. Four "
                                   "capture attempts are recorded in price_capture_attempts.csv so the absence "
                                   "is evidenced.",
            "severity": "high_for_edge_statistics_none_for_accuracy_statistics",
            "human_decision_needed": "Approve a licensed odds source, or accept that edge/CLV stay blank (see "
                                     "suggestion D966-S01).",
            "official_source_url": C.link_for("SCHED-W10"),
        },
        {
            "flag_id": "D966-F02",
            "kind": "measurement_caveat",
            "title": "Open and close come from two different model versions",
            "what_we_observed": "The only earlier publication of these fourteen markets is the prior session's "
                                "file at commit 46391f1 (model nfl_309921cc_v1). Our snapshots are "
                                "nfl_d966f630_v1. The 26 two-snapshot markets therefore mix a model change "
                                "with the passage of time.",
            "where_it_shows_up": "price_snapshots_open_close.csv movement_closing_minus_opening, movement_note",
            "why_it_is_flagged": "Calling that movement a market move would be false: it is a rewrite, not a "
                                 "reprice. It is also the only movement the store can measure today.",
            "what_we_did_instead": "Published the movement with the model versions named on both rows and this "
                                   "flag id, and marked the strategy that trades on it (D966-STR-05) blocked "
                                   "until two snapshots share a model version.",
            "severity": "medium",
            "human_decision_needed": "Confirm whether cross-version movement should be excluded from the "
                                      "movement column entirely (suggestion D966-S06).",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "flag_id": "D966-F03",
            "kind": "gap",
            "title": "The prior publication left moneyline probability blank",
            "what_we_observed": "originated_moneyline_home_prob is empty for all fourteen of its rows; its own "
                                 "note reads: \"Blank: requires a margin-distribution (spread of "
                                 "victory-margin) parameter that no official NFL page in this pack supplies.\"",
            "where_it_shows_up": "price_snapshots.csv prior_session_publication moneyline rows; "
                                 "open_close_table movement_status for the 13 live moneyline markets",
            "why_it_is_flagged": "It is the reason our moneyline has no opening number: the ledger cannot show "
                                 "movement into a blank.",
            "what_we_did_instead": "Emitted the blank prior row anyway - the absence is a row, not a hole - and "
                                   "derived the missing parameter from the verified results feed "
                                   "(dispersion.csv: sigma_pts 10.2808, rho -0.0659 at the Week 9 vintage).",
            "severity": "low_resolved_forward",
            "human_decision_needed": "nothing - the handling above is the decision",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "flag_id": "D966-F05",
            "kind": "own_construction",
            "title": "Position grouping into offence/defence/special-teams is ours, not the league's",
            "what_we_observed": "The injury report prints a position label per player (QB, LB, P, ...) and no "
                                 "unit. Grouping QB/RB/WR/TE/offensive line into 'offence' and LB/DE/DT/CB/S "
                                 "into 'defence' is our mapping.",
            "where_it_shows_up": "depth_of_replacement.csv unit; club_depth_rollup.csv offence_/defence_ "
                                 "columns; correlations D966-COR-06/07/08",
            "why_it_is_flagged": "A fullback or a long-snapper could reasonably sit either side of a unit split, "
                                 "and the club-level rollup inherits that choice.",
            "what_we_did_instead": "Published POSITION_UNIT in capture.py verbatim so the mapping is auditable, "
                                   "and every depth row keeps its raw position label next to the unit.",
            "severity": "low",
            "human_decision_needed": "Approve the mapping or supply the unit definition to use (suggestion "
                                     "D966-S07).",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "flag_id": "D966-F06",
            "kind": "gap",
            "title": "No player statistics were collected, so prop legs cannot settle",
            "what_we_observed": "Team final scores are on the schedule pages we read; per-player statistics are "
                                "on different pages that this session did not read.",
            "where_it_shows_up": "strategies.csv row D966-STR-10 (blocked, zero selections); "
                                 "correlation_exclusions.csv D966-CX-02",
            "why_it_is_flagged": "The brief asks for player-prop combinations. A prop parlay whose legs are "
                                 "graded by guessing is worse than no parlay.",
            "what_we_did_instead": "Specified the rule, gate-blocked it, and published zero selections rather "
                                   "than a fabricated settlement.",
            "severity": "medium",
            "human_decision_needed": "Approve the per-player statistics ingest (suggestion D966-S04).",
            "official_source_url": C.link_for("SCHED-W9"),
        },
        {
            "flag_id": "D966-F08",
            "kind": "sample_size",
            "title": "Small n on every correlation and leaderboard row",
            "what_we_observed": "The verified results feed holds Weeks 7-10 only: 44 games, 88 team-games, and "
                                "at the Week 9 vintage 43 games / 86 team-games. Correlation n ranges from 28 to "
                                "287 (the 287 is same-week game pairs, which are not independent draws).",
            "where_it_shows_up": "correlations.csv n and ci95_low/ci95_high; leaderboard_signal.csv "
                                 "n_legs_graded_excluding_pushes; leaderboard_staking.csv n_tickets_graded",
            "why_it_is_flagged": "Requirement 7 exists because a coefficient at n=28 is a hint, and the 95% "
                                 "intervals here are wide enough to contain both signs on several rows.",
            "what_we_did_instead": "Published n, the interval, the sample unit and an explicit floor "
                                   "(N_FLOOR = 20 graded legs). Rows below the floor are shown and labelled, not "
                                   "ranked.",
            "severity": "high_for_any_decision_that_needs_power",
            "human_decision_needed": "Decide whether to backfill Weeks 1-6 before promotion thresholds are "
                                      "relied on (suggestion D966-S02).",
            "official_source_url": C.link_for("SCHED-W7"),
        },
        {
            "flag_id": "D966-F09",
            "kind": "catalogue",
            "title": "Two strategies are in the catalogue with no input at all",
            "what_we_observed": "D966-STR-09 (market-edge side) needs a book price; D966-STR-10 (prop combo) "
                                "needs player statistics. Both are published with status blocked and zero "
                                "graded legs.",
            "where_it_shows_up": "strategies.csv, leaderboard rows with status blocked_no_input, "
                                    "validation_gates.csv rows that read not_evaluated",
            "why_it_is_flagged": "A leaderboard that silently omits the strategies it cannot run hides the gap; "
                                 "listing them with a reason is the honest version.",
            "what_we_did_instead": "Kept them in every table with their blocking reason, so the gate has "
                                   "something to refuse and the reader can see what is missing.",
            "severity": "low",
            "human_decision_needed": "remove them only if the owner wants a catalogue of live rules only",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "flag_id": "D966-F10",
            "kind": "gap",
            "title": "Week 7 moneylines cannot be originated, and the ledger says so per row",
            "what_we_observed": "The moneyline needs a point-noise scale measured from finished games *before* "
                                "the game. At the Week 6 vintage the feed has no games at all, so the model "
                                "returns no moneyline for the 14 Week 7 games.",
            "where_it_shows_up": "originated_lines_graded.csv, price_snapshots.csv rows with market_flag_id "
                                 "D966-F10 (14 rows), leaderboard row D966-STR-03 n=30 rather than 44",
            "why_it_is_flagged": "Silently filling the gap with the Week 7 scale would be a look-ahead: the "
                                 "moneyline would be priced with information that did not exist at kickoff.",
            "what_we_did_instead": "Left them blank with the reason on the row. For the calibration statistics "
                                   "only (Brier, log loss), where no measurable scale exists at the vintage, the "
                                   "earliest measurable vintage is substituted and every such leg is labelled "
                                   "substituted_forward_from_vintage_7.",
            "severity": "medium",
            "human_decision_needed": "Approve the Weeks 1-6 backfill, which would remove the gap entirely.",
            "official_source_url": C.link_for("SCHED-W7"),
        },
        {
            "flag_id": "D966-F11",
            "kind": "as_of_mismatch",
            "title": "The standings page read on 2026-11-14 already includes the Week 10 Thursday game",
            "what_we_observed": "The read shows Washington 3-5-1 and the Giants 5-3-1, which is the 24-21 "
                                "Thursday result, while the Week 10 slate page shows that game as played and "
                                "the other thirteen as upcoming.",
            "where_it_shows_up": "results_reconciliation.csv, originated_lines.csv vintage columns",
            "why_it_is_flagged": "Any aggregate 'through week N' number must subtract feed games that the page "
                                 "already counted, or it double-counts them.",
            "what_we_did_instead": "Derived every vintage table by subtracting feed games after the vintage from "
                                   "the single read, and reconciled 86 of 96 club-week checks against the "
                                   "independent game-card badges (the other 10 are clubs on bye, which carry no "
                                   "badge that week).",
            "severity": "low_handled",
            "human_decision_needed": "nothing - the handling above is the decision",
            "official_source_url": C.link_for("STANDINGS"),
        },
        {
            "flag_id": "D966-F12",
            "kind": "source_irregularity",
            "title": "Five players appear under a club that is not the one their position line names",
            "what_we_observed": "On the official Week 10 report: Myles Garrett, listed LB Green Bay, appears in "
                                "the Rams table; Von Miller appears in the Cowboys table; Quenton Nelson, G "
                                "Indianapolis, appears in the Seahawks table; David Njoku, TE Cleveland, appears "
                                "in the Chargers table; Patrick O'Connell appears as LB for Seattle. Peter Woods "
                                "is DT in the Jets block and DE in the Packers block.",
            "where_it_shows_up": "injury_report_rows.csv rows for those players; the club rollups for "
                                 "LAR, DAL, SEA, LAC, NYJ, GB inherit the count",
            "why_it_is_flagged": "Either the report's club grouping or the position line is wrong. Both "
                                 "possibilities change a depth count, and we cannot tell which from the page.",
            "what_we_did_instead": "Recorded the row exactly as the table prints it - club as grouped, position "
                                   "as printed - and flagged it. No row was re-attributed, moved or deleted.",
            "severity": "medium_for_depth_counts",
            "human_decision_needed": "Confirm which field is authoritative, then re-run the ingest (suggestion "
                                     "D966-S08).",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "flag_id": "D966-F13",
            "kind": "source_disagreement",
            "title": "Two official headlines disagree on Lamar Jackson's absence window",
            "what_we_observed": "One headline reads 'Report: Ravens QB Lamar Jackson to miss 6-10 weeks with "
                                "groin injury'; another in the same capture reads 'Ravens QB Lamar Jackson out "
                                "6-9 weeks'.",
            "where_it_shows_up": "replacement_evidence.csv, injury_report_rows.csv Baltimore QB rows",
            "why_it_is_flagged": "The return window decides which week the replacement chain stops being used. "
                                 "The two numbers are not compatible.",
            "what_we_did_instead": "Published both headlines side by side with both URLs and no merged value. "
                                   "Nothing in the model uses a return date.",
            "severity": "medium_if_return_dates_are_ever_used",
            "human_decision_needed": "Pick which headline governs, or prefer the injury-report designation over "
                                      "both.",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "flag_id": "D966-F14",
            "kind": "thin_capture",
            "title": "Las Vegas has only five listed rows on the Week 10 report",
            "what_we_observed": "Every other club on the slate lists between 7 and 21 players; the Raiders block "
                                "prints 5.",
            "where_it_shows_up": "injury_report_rows.csv (club LV), club_depth_rollup.csv LV row, "
                                 "depth_of_replacement.csv LV groups",
            "why_it_is_flagged": "A club with a thin report looks healthier than it may be. A count of 'no one "
                                "listed Out' is not the same as 'no one is out'.",
            "what_we_did_instead": "Published the row count next to every LV depth figure, and did not compare "
                                   "clubs on raw counts without it. The comparison rows (correlations "
                                   "D966-COR-06/07/08) treat a listed-row count as a floor, never as a census.",
            "severity": "medium_for_cross_club_comparisons",
            "human_decision_needed": "re-read the page on the next practice day; no choice is needed now",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "flag_id": "D966-F15",
            "kind": "interpretation_risk",
            "title": "A blank game status is not 'available'",
            "what_we_observed": "Several Raiders, Saints and Jaguars players carry a practice status (for example "
                                "'Limited Participation') and an empty game-status cell. Two Jets receivers, "
                                "Rashee Rice and Xavier Worthy, appear in the table with neither field filled.",
            "where_it_shows_up": "injury_report_rows.csv availability = listed_no_designation; "
                                 "depth_of_replacement.csv practice_report_only_no_designation",
            "why_it_is_flagged": "Reading a blank as 'cleared to play' would silently manufacture a count, and "
                                 "reading it as 'out' would manufacture the opposite.",
            "what_we_did_instead": "Counted blanks into a separate column that contributes nothing to the "
                                   "tiers-dropped bound, and kept the practice participation text on the row.",
            "severity": "low_handled",
            "human_decision_needed": "nothing - the handling above is the decision",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "flag_id": "D966-F16",
            "kind": "measurement_caveat",
            "title": "Most markets have one snapshot, so their opening number is their closing number",
            "what_we_observed": "118 of 171 markets in the store hold a single row: the reconstructed "
                                "pre-kickoff number written in this run. Movement for those rows is 0.00 by "
                                "construction.",
            "where_it_shows_up": "price_snapshots_open_close.csv movement_closing_minus_opening, n_snapshots",
            "why_it_is_flagged": "A zero-movement column full of zeros reads like a calm market. It reads that "
                                 "way only because the ledger started today.",
            "what_we_did_instead": "movement_status distinguishes single_snapshot_open_and_close_are_the_same_row "
                                   "from measured_within_store, and the store's role field says "
                                   "open_and_close_final rather than pretending there were two quotes.",
            "severity": "high_for_any_movement_based_claim",
            "human_decision_needed": "nothing to choose: the daily runner adds a row per publication and the "
                                      "zeros retire themselves",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "flag_id": "D966-F17",
            "kind": "environment",
            "title": "Signed proxy URLs from earlier turns were unusable",
            "what_we_observed": "Five fetch attempts against signed routify-file-proxy URLs all returned "
                                "SignatureDoesNotMatch. The canonical www.nfl.com pages were read instead, with "
                                "the chunk index needed to reach the full tables.",
            "where_it_shows_up": "every capture in this pack (all data comes from the canonical pages)",
            "why_it_is_flagged": "Recorded so that a later session does not retry the same dead end, and so the "
                                 "provenance of the numbers says 'the league page', not 'a cached copy'.",
            "what_we_did_instead": "Re-read every value from the canonical URL, and stored the values in "
                                   "capture.py with their source id.",
            "severity": "informational",
            "human_decision_needed": "nothing - the handling above is the decision",
            "official_source_url": C.link_for("SCHED-W10"),
        },
    ]
    for r in raw:
        r["does_it_block_merge"] = BLOCKS
        r["read_on_utc"] = C.CAPTURE_DATE_UTC
    return raw
