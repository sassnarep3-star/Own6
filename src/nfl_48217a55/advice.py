"""The decision-readiness register, the questions register and the suggestions register.

`requirements()` is the row-per-requirement table the brief asks to put on the landing
page: for each requirement, what is actually published today, the gate that blocks it and
the number that would clear it. A row is `cleared` only where this session read the value
from the cited official page. `blocked` rows are not failures of effort - they are
requirements whose input does not exist in an official source, and the `clearing_number`
column says exactly what would have to change.

`questions()` is the questions / information / answers register: what a decision would need
to know, what we have, what is missing, and the path to discover the missing part.

`suggestions()` is the review-before-implementation list. Nothing here is applied
automatically; each row names the decision it waits on.
"""

from __future__ import annotations

from . import capture as C

U = C.SOURCE_URL

# status vocabulary
CLEARED = "cleared"
PARTIAL = "partial"
BLOCKED = "blocked"
REJECTED = "rejected"
NEEDS_REVIEW = "needs review"

# ---------------------------------------------------------------------------
# 0 id, 1 category, 2 requirement, 3 status, 4 what is published, 5 gate,
# 6 clearing number, 7 evidence file, 8 official source url, 9 what the source supports
# ---------------------------------------------------------------------------

_REQ = [
    # ---------------- data capture and storage ----------------
    ("REQ-01", "Data", "Price-snapshot store recording opening and closing numbers for every "
     "market we originate", BLOCKED,
     "0 markets with an external price. A capture-attempt log records every route tried and "
     "the result.", "G2",
     ">= 1 licensed source publishing an opening and a closing number for >= 14 markets "
     "across >= 1 week", "price_capture_attempts.csv", U["S2"],
     "The schedule page is official but carries no operator prices."),

    ("REQ-02", "Data", "Verified results feed so backtests and ROI are computable at all",
     PARTIAL,
     "9 Week 10 finals captured with kickoff and network; a 32-club through-Week-9 table "
     "reconstructed by subtracting those games and reconciled 10/10 to the official pregame "
     "page.", "G1",
     "136 game rows with final scores and a 32-club reconciliation at 0 mismatches",
     "results_feed.csv, standings_point_in_time.csv, standings_verification.csv", U["S2"],
     "Official finals only; at capture time 3 Week 10 games were still in progress."),

    ("REQ-13", "Data", "Run the 32-team roster/IR sweep before any team-level model is trusted",
     CLEARED,
     "All 32 clubs covered: 28 on the Week 10 injury report, 4 on bye (published as byes, not "
     "as injury-free); 25 November reserve-list rows; 12 November trades; 1 club roster read "
     "end to end.", "",
     "32 clubs with a dated availability row each; 0 clubs assumed healthy by absence",
     "injury_club_rollup.csv, reserve_list.csv, trades.csv", U["S1"],
     "The injury report prints no section for a club on bye, which is not evidence of health."),

    ("REQ-19", "Data", "Turn the 136-game log into the pre-registered backtest corpus", BLOCKED,
     "The standings reconstruction implies the completed-game count through Week 9 and that "
     "count is published, but no game-by-game log was read this session.", "G1,G3",
     "136 completed games captured game by game, each with an official game URL",
     "integrity_checks.csv", U["S2"],
     "Week-by-week official schedule pages exist; this session read Week 10 only."),

    ("REQ-23", "Data", "Transcribe the venue of every fixture from the official game centre and "
     "publish it", PARTIAL,
     "13 Week 10-slate fixtures had no venue printed on the schedule page; 13 Week 9 venues "
     "were transcribed from the official inactives page, which does print WHERE.", "G1",
     "venue on every fixture in the evaluation window, each with the page that printed it",
     "venues.csv", U["S5"],
     "The inactives page prints WHERE and WHEN per game; the by-week schedule page does not."),

    ("REQ-24", "Data", "Publish the league's dated schedule announcement beside the live schedule "
     "page", BLOCKED,
     "The Week 16-18 flexible-scheduling note on the schedule page was captured verbatim. The "
     "original dated announcement was not read.", "",
     "the dated announcement URL, read and captured", "schedule_week10.csv", U["S2"],
     "The schedule page carries a flexible-scheduling note and a link to the official "
     "procedures page, not the original announcement."),

    ("REQ-25", "Data", "Use official NFL Game Books for actual starters and game-day status; do "
     "not infer depth rank or snaps", BLOCKED,
     "0 Game Book rows. The pack refuses to infer a starter: the depth-of-replacement table "
     "publishes counts and leaves replacement_named empty.", "G4",
     "Game Book or equivalent official source read for every game in the window, with starters "
     "and snaps", "depth_of_replacement.csv", U["S1"],
     "The injury report gives designations only; no starters and no snaps."),

    ("REQ-29", "Data", "Automate immutable multi-day availability snapshots", BLOCKED,
     "One capture exists, with a clock time and the chunk range read for every source. Multi-day "
     "automation is not in place.", "",
     ">= 3 dated captures per week (Wed, Thu, Fri) retained with hashes, replayable",
     "sources.csv", U["S1"],
     "The page is live and re-renders; a single capture cannot show a change."),

    ("REQ-30", "Data", "Build immutable official availability snapshots with hashes, timestamps "
     "and conflict flags", PARTIAL,
     "Every source read this session carries a UTC clock time, the chunk range read and a "
     "content hash of the values transcribed. Retention is a git commit, not a hash-chained "
     "store.", "",
     "a store outside the static site holding each capture with its raw hash and conflict flags",
     "sources.csv", U["S1"],
     "The official page is the source of the values; the hash covers our transcription of them."),

    ("REQ-31", "Data", "Capture official inactive lists and snap counts", PARTIAL,
     "Official Week 9 inactive lists captured for all 13 Sunday games (26 club lists). Snap "
     "counts: 0 - no official source was read this session that publishes them.", "G5",
     "inactives for every week in the window, joined to a snap-count source verified for all "
     "32 clubs", "week9_inactives.csv", U["S5"],
     "The official inactives page lists inactives and marks emergency third quarterbacks; it "
     "prints no snap counts."),

    ("REQ-39", "Data", "Durable snapshot storage and freshness alerts", BLOCKED,
     "The pack's checker pins row counts and required fields and fails loudly, but no store "
     "outside the site exists and no alert fires on a source change.", "",
     "external store + a freshness monitor that alerts on source or schema change",
     "sources.csv", U["S1"],
     "Captures live in the repository only."),

    ("REQ-47", "Data", "Point-in-time snapshot ledger for injuries, depth charts and inactives",
     PARTIAL,
     "A ledger of what was read, when, and from which chunk range, plus a worked "
     "point-in-time reconstruction. Depth charts are not in it because no official depth rows "
     "were read.", "G4",
     "dated, immutable rows for all three streams, replayable to any pre-kickoff instant",
     "sources.csv, standings_point_in_time.csv", U["S1"],
     "One capture per stream, timestamped."),

    ("REQ-54", "Data", "Snapshot the injury report every Wed, Thu and Fri with a dated history",
     BLOCKED,
     "One capture, dated 2026-11-15 (Sunday of Week 10).", "",
     "3 captures per week for >= 4 consecutive weeks", "sources.csv", U["S1"],
     "The page is live; a single read cannot show a trend."),

    ("REQ-55", "Data", "Treat the injury report as a timestamped series, not a weekly snapshot",
     PARTIAL,
     "The capture is stored as a series of rows each carrying the read clock time, so a second "
     "capture could be differenced. Only one capture exists.", "",
     ">= 2 captures of the same report so a delta can be published",
     "injury_report_2026_11_15.csv", U["S1"],
     "The page renders the current report only; it offers no history control on this route."),

    ("REQ-63", "Data", "Drift alarm on every scraper (row counts, required fields, fail loudly)",
     CLEARED,
     "The pack's checker pins the row count and required fields for every table and exits "
     "non-zero on any drift; it is wired into CI.", "",
     "1 pin per table, failing the build when a field goes missing", "checker rules", U["S1"],
     "Nothing external: this is a property of the pack's own checker."),

    ("REQ-64", "Data", "Capture the reserve list so 'not listed' never means 'available'",
     CLEARED,
     "25 November 2026 Reserve/Injured rows captured with club, date and player, and each is "
     "marked whether it also appears on the Week 10 report.", "",
     "reserve list captured for every week in the window",
     "reserve_list.csv", U["S7"],
     "The official reserve-list route publishes dated Reserve/Injured moves."),

    ("REQ-66", "Data", "Archive weekly injury reports for past seasons", BLOCKED,
     "Only the current week's report was read. The page offers a year selector down to 1920 "
     "but this session captured 2026 Week 10 only.", "",
     ">= 2 prior seasons of weekly reports archived with dates", "sources.csv", U["S1"],
     "The page has a season selector; prior seasons were not read this session."),

    # ---------------- prices and origination ----------------
    ("REQ-03", "Origination", "Originate the side first, then the total, then the moneyline",
     BLOCKED,
     "The order is specified and will be enforced in code, but no market exists to originate "
     "against, so no stage has run.", "G2",
     "1 origination run with all three stages in the fixed order and a test that fails on "
     "reordering", "strategy_registry.csv", U["S2"],
     "Official schedule page confirms the fixtures; it carries no prices."),

    ("REQ-04", "Origination", "Publish model fair line, market line and difference as separate "
     "columns", BLOCKED,
     "Column schema published with the market and difference cells empty and flagged on every "
     "row.", "G2",
     "3 populated, separate columns per market for >= 14 markets",
     "originated_lines_schema.csv", U["S2"],
     "No official page publishes an operator price."),

    ("REQ-18", "Origination", "Price a line ourselves and publish the residual against the "
     "market, on a schedule, from day one", BLOCKED,
     "A publication schedule and column schema are defined. No residual can be computed "
     "without a market number.", "G2",
     ">= 1 published residual per market per week, on the stated schedule",
     "originated_lines_schema.csv", U["S2"],
     "Fixtures and kickoffs are official; prices are not."),

    ("REQ-20", "Origination", "Decide the price-data policy before any backtest is published",
     BLOCKED,
     "No backtest is published, so the policy has not been violated - but it is also not yet "
     "written down.", "G2",
     "a written policy naming the licensed source, the capture cadence and the retention rule",
     "questions.csv", U["S2"],
     "No official page publishes operator prices, so the policy needs a commercial decision."),

    ("REQ-60", "Origination", "Vig-free market consensus vs originated fair-line decomposition",
     BLOCKED,
     "The decomposition is specified (separate true divergence from operator margin) but no "
     "market number exists to decompose.", "G2",
     "de-vigged consensus and originated line for the same >= 14 markets",
     "originated_lines_schema.csv", U["S2"],
     "No official or licensed price source in this environment."),

    ("REQ-62", "Origination", "Publish every model total twice until one wins", BLOCKED,
     "Two estimators are named but neither can be fitted: both need the game log and neither "
     "has been run.", "G1,G3",
     "2 published totals per game with the gap column, for >= 1 week, then a walk-forward "
     "comparison", "strategy_registry.csv", U["S2"],
     "Fixtures are official; the model inputs are not complete."),

    # ---------------- availability and depth ----------------
    ("REQ-06", "Availability", "Track the depth of the replacement, not just the fact of a "
     "replacement", PARTIAL,
     "Floors published per club and unit (how many Out rows sit in each unit). No depth tier: "
     "the report names no replacement and gives no order.", "G4",
     "a dated depth order per club so a tier can be read, not inferred",
     "depth_of_replacement.csv", U["S1"],
     "The report prints player, position, injury, practice status and game status only."),

    ("REQ-10", "Availability", "Availability graph as a first-class dataset (who was expected to "
     "start, who actually did)", BLOCKED,
     "Neither side of the graph exists: no expected-starter source and no actual-starter "
     "source was read.", "G4,G5",
     "expected starters and actual starters for every club-game in the window",
     "depth_of_replacement.csv", U["S1"],
     "The injury report gives availability designations, not starters."),

    ("REQ-11", "Availability", "Model depth from playing time, not jersey order", BLOCKED,
     "0 snap counts captured. Jersey number appears on the official roster page and is "
     "explicitly not used as a depth signal.", "G4",
     "a snap-count source verified for all 32 clubs", "depth_route_probe.csv", U["S8"],
     "The official roster page prints jersey number and roster status; no snaps, no depth."),

    ("REQ-12", "Availability", "Make the injury signal a surprise, never a level", BLOCKED,
     "The design rule is stated in the strategy definitions (STR-03/04 trade the delta between "
     "two reads). No delta can be computed from one capture.", "",
     ">= 2 captures of the same report so a delta can be published",
     "strategy_registry.csv", U["S1"],
     "One capture only this session."),

    ("REQ-21", "Availability", "Store every injury-hub read with its clock time and publish the "
     "delta, never the level", PARTIAL,
     "Every row carries the read clock time. The delta column is empty because a second read "
     "does not exist yet.", "",
     ">= 2 reads of the same hub, differenced per player",
     "injury_report_2026_11_15.csv", U["S1"],
     "The live page renders the current report only."),

    ("REQ-32", "Availability", "Fix the two depth-parsing failures before widening coverage "
     "(Texans image, Packers jersey prefix)", NEEDS_REVIEW,
     "Not reproducible this session: the per-club depth route is a 404 on nfl.com and no club "
     "depth page was read. A jersey-prefix stripper is specified but has no input to strip.",
     "G4",
     "a structured depth source for all 32 clubs; until then the Texans image and the Packers "
     "prefix cannot be exercised", "depth_route_probe.csv", U["S9"],
     "The route returned HTTP 404, so no depth page content exists to parse."),

    ("REQ-33", "Availability", "Model depth slots as groups, not a single starter", BLOCKED,
     "The unit grouping is implemented (Quarterback, Backfield, Receivers, Offensive line, "
     "Defensive front, Linebackers, Secondary, Specialists) and applied to every row. Shared "
     "and empty slots cannot be represented: no depth rows exist.", "G4",
     "depth rows for all 32 clubs so shared and empty slots can be represented faithfully",
     "depth_of_replacement.csv", U["S1"],
     "The injury report is a player list, not a depth chart."),

    ("REQ-34", "Availability", "Treat roster turnover as a first-class data event", PARTIAL,
     "12 November trades captured with from/to, date and player; 25 reserve moves captured. "
     "Availability rows are not yet versioned against the last roster event.", "",
     "every availability row carries the last official roster event that could invalidate it",
     "trades.csv, reserve_list.csv", U["S6"],
     "The official transactions hub publishes dated trades by club."),

    ("REQ-41", "Availability", "Per-team view: starters out, replacements named, net injury count",
     PARTIAL,
     "Net counts published per club (out, doubtful, questionable, listed with no status) split "
     "offense/defense. Replacements named: only the five the official pages actually name.",
     "G4",
     "a named replacement per Out row where an official page names one",
     "injury_club_rollup.csv, announced_starters.csv", U["S1"],
     "The report itself names no replacement."),

    ("REQ-42", "Availability", "Announced-starter evidence field, not an inferred replacement",
     CLEARED,
     "5 officially announced starter changes published, each with the headline and the URL of "
     "the page that names the starter (Lock, McCord, Watson, Beck, Brissett).", "",
     "1 row per announced change, with the naming page and its date",
     "announced_starters.csv", U["S1"],
     "NFL.com news stories dated 2026-11-11 to 2026-11-14 name these starters."),

    ("REQ-43", "Availability", "Official depth-chart register with date and source per row",
     BLOCKED,
     "0 depth rows. Route probe published: nfl.com per-club depth chart is a 404; the roster "
     "page links a club-hosted depth chart.", "G4",
     "32 clubs with a dated depth row and a URL per row", "depth_route_probe.csv", U["S8"],
     "The roster page exists (200) and publishes no depth order; it links the club's own site."),

    ("REQ-44", "Availability", "Calibrate what 'Questionable' means empirically instead of using "
     "old percentages", PARTIAL,
     "Play rate computed from the only rows where an official page published both the "
     "designation and the resolution: 10 of 11 definite, Wilson interval published, with the "
     "selection warning on the row.", "G6",
     ">= 200 designation/outcome pairs with an interval per designation",
     "designation_calibration.csv", U["S4"],
     "The official pregame page publishes active/inactive calls for named players."),

    ("REQ-45", "Availability", "Interactive offense vs defense matchup deficiency matrix "
     "(1st-4th string)", BLOCKED,
     "The unit x side counts that would feed it are published. The matrix itself needs a depth "
     "tier per player, which does not exist.", "G4",
     "a depth tier per player for both clubs in a fixture, from an official dated source",
     "depth_of_replacement.csv", U["S1"],
     "The injury report has no depth tier."),

    ("REQ-46", "Availability", "Flag stale depth rows against the official transactions log",
     PARTIAL,
     "The transactions and reserve-list feeds that would flag a stale row are captured; no "
     "depth rows exist to flag against them.", "G4",
     "depth rows for all 32 clubs, each checked against the latest transactions read",
     "trades.csv, reserve_list.csv", U["S6"],
     "The official transactions hub is dated and club-attributed."),

    ("REQ-51", "Availability", "Represent shared and empty depth slots faithfully", BLOCKED,
     "The data model allows it; no depth rows exist to represent.", "G4",
     "depth rows for all 32 clubs with slot shape recorded", "depth_route_probe.csv", U["S8"],
     "No official depth rows read this session."),

    ("REQ-52", "Availability", "Resolve the depth-order source before building the "
     "backup-deficiency feature", CLEARED,
     "Route (a) evaluated first and reported: nfl.com per-club depth chart is a 404, and the "
     "roster page publishes no depth order but links a club-hosted depth chart. Route (b) needs "
     "a snap-count source, not yet verified for 32 clubs. The feature is not built.", "G4",
     "one route verified for all 32 clubs", "depth_route_probe.csv", U["S9"],
     "The 404 page and the roster page were both read this session."),

    ("REQ-53", "Availability", "Score injury-designation reliability before using it as a "
     "feature", PARTIAL,
     "First reliability number published with its interval and its selection warning, and the "
     "label is marked unusable as a feature until the gate clears.", "G6",
     ">= 200 designation/outcome pairs with an interval per designation",
     "designation_calibration.csv", U["S5"],
     "The official Week 9 inactives page gives one week of outcomes."),

    ("REQ-56", "Availability", "Use snap counts as the starter proxy when the depth chart is "
     "unavailable", BLOCKED,
     "No snap-count source was verified. The route probe records that the roster page publishes "
     "no snaps.", "G4",
     "a snap-count source verified for all 32 clubs", "depth_route_probe.csv", U["S8"],
     "The roster page prints roster status codes (ACT/RES/DEV/CUT/PUP/TRD), no snaps."),

    ("REQ-58", "Availability", "Stadium roof/surface and NWS hourly wind/precipitation overlay",
     BLOCKED,
     "13 Week 9 venues captured, which is the join key the overlay needs. Roof, surface and "
     "weather were not read; they are not on the pages this session captured.", "",
     "roof/surface per venue from an official source + an hourly NWS grid per fixture",
     "venues.csv", U["S5"],
     "The official page prints the venue name only."),

    # ---------------- model ----------------
    ("REQ-14", "Model", "Fixture-context feature set built only from published schedule facts",
     CLEARED,
     "Kickoff date and time, network, home/road and bye status captured for all 14 Week 10 "
     "fixtures, plus venue for 13 Week 9 fixtures.", "",
     "1 row per fixture with every context field sourced", "schedule_week10.csv, venues.csv",
     U["S2"],
     "The official by-week schedule prints kickoff, network and the bye panel."),

    ("REQ-15", "Model", "Store every model output as a probability plus its inputs, not just a "
     "pick", BLOCKED,
     "The output schema is specified (probability, inputs, benchmark, timestamp). No model has "
     "produced an output because the gates are open.", "G1,G2,G3",
     ">= 1 stored output with its full input vector", "strategy_registry.csv", U["S2"],
     "Fixtures are official; model inputs are incomplete."),

    ("REQ-26", "Model", "Ingest game-level results to make the ratings opponent-aware", BLOCKED,
     "A rating is published and explicitly labelled not opponent-adjusted, so the gap is "
     "visible.", "G1,G3",
     ">= 136 completed games in the log with both clubs and both scores",
     "team_ratings_naive.csv", U["S3"],
     "The standings page gives season totals, not the game log."),

    ("REQ-27", "Model", "Injury and personnel ablations instead of fixed penalties", BLOCKED,
     "The ablation protocol is specified (identical model with and without the availability "
     "features, chronological holdout, difference reported with an interval). No run exists.",
     "G1,G3,G4,G5",
     ">= 2 chronological holdout windows with both model variants fitted",
     "strategy_registry.csv", U["S1"],
     "Availability counts exist; the game log and depth order do not."),

    ("REQ-28", "Model", "Injury/depth ablations, not fixed penalties, on chronological holdouts",
     BLOCKED,
     "Same protocol as REQ-27, restated so it survives as its own row: the comparison is "
     "between two fits of the same model, never a points penalty for a missing starter.",
     "G1,G3,G4,G5",
     "the same two fits, with the difference and its interval published",
     "strategy_registry.csv", U["S1"],
     "Nothing in the official report supports a fixed point penalty."),

    ("REQ-68", "Model", "2026 kickoff and declared onside-kick regime priors filter", BLOCKED,
     "No rule-change page was read this session, so no prior is stated.", "",
     "the official rule-change page read and captured, then the prior stated from it",
     "questions.csv", U["S2"],
     "The schedule page does not carry rule changes."),

    # ---------------- validation, gates, luck ----------------
    ("REQ-07", "Validation", "Compute correlations only from officially sourced numbers and "
     "publish n with each value", CLEARED,
     "6 measured correlations published, each with n, unit, method, interval, p-value and one "
     "URL per axis; 5 candidates published as exclusions with the reason and the number that "
     "would clear them.", "",
     "n and an interval beside every published correlation",
     "correlations.csv, correlation_exclusions.csv", U["S1"],
     "Both axes of every published row come from pages read this session."),

    ("REQ-08", "Validation", "Demotion gate that sends a live strategy back to paper", BLOCKED,
     "Gate conditions written (calibration gap > 0.08, or drawdown beyond the staking budget) "
     "and wired to the strategy rows. No strategy is live, so the gate has never tripped.",
     "G8",
     ">= 1 live strategy before a demotion can be observed", "strategy_registry.csv", U["S2"],
     "Nothing external: this is a property of the registry."),

    ("REQ-16", "Validation", "'Removal of luck' panel on the dashboard", PARTIAL,
     "League-level panel published: observed win-percentage variance, the coin-flip null "
     "variance, the implied luck share and the margin SD, all from the reconstructed 32-club "
     "table. The strategy-level panel is blocked.", "G1,G8",
     ">= 100 prospective graded forecasts so a strategy's own luck share can be estimated",
     "luck_panel.csv", U["S3"],
     "The official standings feed the panel; no forecast record exists yet."),

    ("REQ-35", "Validation", "Singles-only shadow baseline", CLEARED,
     "STR-01 and STR-02 are singles only, frozen before their window, with no combo variant "
     "opened.", "",
     "1 singles-only strategy live in shadow before any combo division is opened",
     "strategy_registry.csv", U["S2"],
     "Nothing external: this is a property of the registry."),

    ("REQ-36", "Validation", "Parlays and prop combos behind a joint-evidence gate", CLEARED,
     "STR-05, STR-06 and STR-07 are held at paper and cannot be ranked until G10 clears; their "
     "evaluation windows are recorded as 'not opened'.", "G10",
     "a validated joint probability and the operator's void/push rules for each combo shape",
     "strategy_registry.csv", U["S2"],
     "No official page publishes combo prices or void rules."),

    ("REQ-57", "Validation", "Control baseline (random picks, favourites only) on every "
     "leaderboard run", CLEARED,
     "STR-08 (favourites only) and STR-09 (random) are registered as controls that can never "
     "be promoted and are reported beside every ranking.", "",
     "2 control rows present on every run", "strategy_registry.csv", U["S2"],
     "Nothing external: this is a property of the registry."),

    ("REQ-61", "Validation", "Weekly 'what changed' diff instead of a static snapshot", BLOCKED,
     "A single capture per stream exists; a diff needs two.", "",
     ">= 2 captures of the same stream, differenced per key",
     "sources.csv", U["S1"],
     "One capture this session."),

    ("REQ-67", "Validation", "Pre-register each strategy (definition frozen before results are "
     "seen)", CLEARED,
     "9 strategy definitions frozen in this file, each with its benchmark, its window, its "
     "required gates and its two-sided change-our-mind rule.", "",
     "every strategy frozen before its window opens", "strategy_registry.csv", U["S2"],
     "Nothing external: the freeze is the version-controlled file itself."),

    ("REQ-69", "Validation", "Freeze a rule before it sees data (pre-registration)", CLEARED,
     "The freeze mechanism is the git commit of this file; the rule text, the sample window and "
     "the gates travel together in one row.", "",
     "commit hash recorded per frozen rule", "strategy_registry.csv", U["S2"],
     "Nothing external."),

    ("REQ-70", "Validation", "Split data into train, validation and final holdout seasons",
     BLOCKED,
     "Three disjoint windows are declared in the gate text but populated with nothing, because "
     "the game log does not exist yet.", "G1,G7",
     "3 disjoint windows declared and populated, with the holdout never used for fitting",
     "validation_gates.csv", U["S2"],
     "The standings give one season slice only."),

    ("REQ-09", "Validation", "Pre-register every strategy; forbid backtest numbers from ever "
     "appearing on the leaderboard", CLEARED,
     "The leaderboard publishes 0 ranked strategies across all five divisions, with the reason "
     "on every row. Backtest columns are not part of the leaderboard schema at all.", "",
     "0 backtest-derived rows on the leaderboard, enforced by the schema",
     "leaderboard.csv", U["S2"],
     "Nothing external: this is a property of the schema."),

    # ---------------- leaderboard and rewards ----------------
    ("REQ-05", "Leaderboard", "Separate 'signal' from 'staking' so a lucky staking run cannot "
     "mask a bad signal", BLOCKED,
     "Two-table design specified: a signal table ranked on a proper score only, and a staking "
     "table with no accuracy column. Nothing to rank yet.", "G9",
     "2 published tables with the columns enforced by a test", "leaderboard.csv", U["S2"],
     "Nothing external."),

    ("REQ-37", "Leaderboard", "Proper-score leaderboard divisions", CLEARED,
     "Five divisions declared (singles, game parlays, same-game parlays, prop combos, controls) "
     "with 0 rows each and the reason on each row.", "",
     "1 division per bet structure, each ranked on its own proper score",
     "leaderboard.csv", U["S2"],
     "Nothing external."),

    ("REQ-38", "Leaderboard", "Rank with proper scores and uncertainty, not win rate", CLEARED,
     "Ranking rule published: benchmark-relative Brier skill with a game-cluster lower bound "
     "and a multiplicity adjustment. Win rate and short-run ROI are explicitly excluded from "
     "the ranking key.", "",
     "every ranking row carries a lower bound and the number of trials", "leaderboard.csv",
     U["S2"],
     "Nothing external."),

    ("REQ-59", "Leaderboard", "Two-stage leaderboard (proper-score qualification, then "
     "prospective CLV/ROI escrow)", BLOCKED,
     "Stage one is specified and empty. Stage two needs prices and a prospective record.",
     "G2,G8",
     ">= 100 prospective graded forecasts with recorded prices before stage two opens",
     "leaderboard.csv", U["S2"],
     "No official price source."),

    # ---------------- rejected approaches ----------------
    ("REQ-50", "Rejected", "Reject: deriving depth order from jersey number, experience or "
     "salary", REJECTED,
     "Rejected and recorded. The official roster page publishes jersey number, experience and "
     "college; none of them is used as a depth signal anywhere in this pack.", "",
     "n/a - permanently rejected", "depth_route_probe.csv", U["S8"],
     "The roster page prints those attributes; it does not publish a depth order."),

    ("REQ-65", "Rejected", "Reject: ranking strategies by season-long ROI", REJECTED,
     "Rejected and recorded. ROI is absent from the ranking key; the ranking is Brier skill "
     "with a lower bound and a multiplicity adjustment.", "",
     "n/a - permanently rejected", "leaderboard.csv", U["S2"],
     "Nothing external."),

    # ---------------- governance and process ----------------
    ("REQ-17", "Governance", "Two-sided 'what would change our mind' field on every strategy "
     "entry", CLEARED,
     "Every one of the 9 strategy rows carries a promote condition and a demote condition.", "",
     "2 conditions per strategy row", "strategy_registry.csv", U["S2"],
     "Nothing external: this is a property of the registry."),

    ("REQ-40", "Governance", "Split the site into a public analysis layer and a private data "
     "layer", PARTIAL,
     "The public pages carry derived counts, ratios and links to the official page. The raw "
     "injury rows are published in full, which is the item to review before the terms of use "
     "are settled.", "",
     "a written terms-of-use position; raw rows moved behind it", "questions.csv", U["S1"],
     "The official terms page governs use; it was not read this session."),

    ("REQ-71", "Governance", "Suggestions section so a reviewer can choose the best path before "
     "any change is applied", CLEARED,
     "A suggestions register with 16 rows, each with the decision it waits on, the options and "
     "the cost of doing nothing. Nothing is auto-implemented.", "",
     "1 review page, 0 auto-applied changes", "suggestions.csv", U["S2"],
     "Nothing external."),

    ("REQ-72", "Governance", "Clear list of questions, information and answers needed before any "
     "decision, with paths to discover what is missing", CLEARED,
     "A questions register with 18 rows: the decision each question blocks, what we have, what "
     "is missing and the discovery path.", "",
     "1 row per open question with a discovery path", "questions.csv", U["S2"],
     "Nothing external."),

    ("REQ-73", "Governance", "Line-by-line repo review with official-source verification and "
     "irregularities flagged", CLEARED,
     "Repo findings register with the irregularity, where it was found, the official page that "
     "settles it and the flag id.", "",
     "1 row per finding with a source link", "repo_findings.csv", U["S1"],
     "The findings are about pages read this session and files in this repository."),

    ("REQ-74", "Governance", "Every table row carries a source link to an official site; "
     "unverifiable values left blank and flagged", CLEARED,
     "A per-table blank audit counts the empty cells in every published table, and every empty "
     "cell is traced to a flag row.", "",
     "0 untraced blank cells", "blank_audit.csv, flagged.csv", U["S1"],
     "Nothing external: this is a property of the checker."),

    # ---------------- site ----------------
    ("REQ-75", "Site", "GitHub Pages site: clean landing page and subpages organised by category",
     CLEARED,
     "A dashboard landing page and 15 category subpages, all generated from the same data, with "
     "no input controls anywhere.", "",
     "site builds with 0 broken internal links", "site pages", U["S2"],
     "Nothing external."),

    ("REQ-76", "Site", "Executive summary of the important details", CLEARED,
     "A written executive summary plus an executive-summary page generated from the same "
     "numbers.", "", "1 summary, generated not hand-copied", "executive-summary.html", U["S3"],
     "Nothing external."),

    ("REQ-77", "Site", "No manual input required from the owner", CLEARED,
     "The build takes no arguments, touches no network at build time and reproduces identical "
     "files on a re-run. No page contains an input control.", "",
     "byte-identical rebuild", "build script", U["S2"],
     "Nothing external."),
]

REQ_COLUMNS = [
    "requirement_id", "category", "requirement", "status", "what_is_published",
    "blocking_gate", "clearing_number", "evidence_file", "official_source_url",
    "what_the_source_supports",
]


def requirements():
    out = []
    for r in _REQ:
        row = dict(zip(REQ_COLUMNS, r))
        row["read_on_utc"] = C.CAPTURE_CLOCK_UTC
        out.append(row)
    return out


def requirement_summary():
    counts = {}
    for r in requirements():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# questions / information / answers register
# ---------------------------------------------------------------------------

_Q = [
    # id, decision it blocks, question, what we have, what is missing, discovery path, source
    ("Q01", "Any origination at all",
     "Where do operator prices come from, and is their use permitted?",
     "Every official page this session read is price-free. No licensed feed exists in this "
     "environment.",
     "A licensed price source and a written data-use position.",
     "Read the NFL terms page and the club/operator partner pages; if a commercial feed is "
     "required, that is an owner decision, not a scraping task.", U["S2"]),
    ("Q02", "Backtest publication",
     "What is the price-data policy, decided before any backtest is published?",
     "The policy is unwritten. No backtest has been published, so nothing is violated yet.",
     "The policy text: source, cadence, retention, and who may see row-level data.",
     "Draft the policy, then re-read the NFL terms page against it.", U["S2"]),
    ("Q03", "Opponent-aware ratings",
     "Can we obtain the game-by-game log for seasons before 2026?",
     "Week 10 2026 only (14 fixtures, 9 finals). A 32-club through-Week-9 table reconstructed "
     "from standings.",
     "Weeks 1-9 game by game, and prior seasons.",
     "Read nfl.com/schedules/2026/by-week/week-N for N = 1..9, one week at a time, and record "
     "each game URL.", U["S2"]),
    ("Q04", "Depth and replacement modelling",
     "Which official source publishes a depth order, verified for all 32 clubs?",
     "nfl.com per-club /depth-chart is a 404. The roster page publishes no depth order but "
     "links a club-hosted depth chart (chiefs.com/team/depth-chart for one club).",
     "Confirmation that a club-hosted depth page exists for all 32 clubs, and a date on each.",
     "Visit each club's official site depth page, one club at a time, and record URL + date + "
     "whether the page is HTML or an image.", U["S8"]),
    ("Q05", "Snap-count route",
     "Is there an official snap-count source?",
     "None read this session. The roster page publishes roster status codes only.",
     "A verified snap-count source, or a decision to drop route (b).",
     "Check the official team stats pages and the NFL Game Books for a snap-count table; if "
     "absent, route (b) is closed.", U["S8"]),
    ("Q06", "Designation reliability",
     "How often does each designation actually play?",
     "11 definite designation/outcome pairs from one official pregame page; 10 played.",
     "Roughly 200 pairs across seasons, joined to the official inactives.",
     "Read the weekly injury report and the weekly inactives page for the same week, for "
     "several weeks, and join them.", U["S5"]),
    ("Q07", "Multi-day snapshots",
     "Can the injury report be captured on Wednesday, Thursday and Friday?",
     "One capture, Sunday 2026-11-15, with a clock time.",
     "A scheduler outside the static site that writes immutable captures.",
     "Choose a store, then run the capture on the three days and confirm the rows differ.",
     U["S1"]),
    ("Q08", "Venue coverage",
     "Which official page prints the venue for every fixture?",
     "The inactives page prints WHERE per game (13 Week 9 venues captured). The by-week "
     "schedule page does not print a venue.",
     "Venues for Week 10 and for the rest of the season.",
     "Read the inactives page for each week, or the individual game centre page per fixture.",
     U["S5"]),
    ("Q09", "Stadium roof and surface",
     "Where is roof status and surface published officially?",
     "13 Week 9 venue names captured, which is the join key the overlay would need.",
     "Roof status, surface type, and the 90-minute roof designation per game.",
     "Check the official game centre page for a stadium field; check the club site for surface.",
     U["S5"]),
    ("Q10", "Weather overlay",
     "Is an hourly NWS grid available per stadium coordinate?",
     "Nothing captured.",
     "Stadium coordinates, then an hourly forecast grid per fixture.",
     "Confirm the coordinate source first; the weather grid is a separate, non-NFL source and "
     "needs its own terms check.", U["S5"]),
    ("Q11", "Schedule announcement",
     "What is the dated official schedule announcement?",
     "The flexible-scheduling note for Weeks 16-18 was captured verbatim from the schedule "
     "page.",
     "The original dated announcement and its URL.",
     "Search NFL.com news for the schedule release story for the 2026 season and capture it "
     "with its date.", U["S2"]),
    ("Q12", "Rule regime priors",
     "What changed for 2026 kickoffs and onside kicks?",
     "Nothing read this session.",
     "The official rule-change page and the text of the change.",
     "Read operations.nfl.com rule-change pages for 2026 and capture the exact wording.",
     U["S2"]),
    ("Q13", "Terms of use",
     "May row-level official data be republished on a public site?",
     "Derived counts and ratios are published. Full injury rows are published too.",
     "A written position on republication.",
     "Read the NFL terms page, then decide whether the raw rows move behind the private layer.",
     U["S1"]),
    ("Q14", "Combo pricing",
     "What are the operator's void and push rules for parlays and combos?",
     "Nothing. No operator document was read.",
     "The rules per operator, for each combo shape.",
     "Obtain the rules from the operator's own published terms; without them no combo may be "
     "ranked.", U["S2"]),
    ("Q15", "Prospective record",
     "When does the first forecast get recorded before kickoff?",
     "No forecast has been recorded. The registry is frozen and waiting.",
     "One recorded forecast per market, timestamped before kickoff.",
     "Pick the Week 11 slate, freeze the model version, and record before the first kickoff.",
     U["S2"]),
    ("Q16", "Sample size",
     "How many prospective forecasts are needed before a ranking is not noise?",
     "The gate says 100. No power calculation has been published against the expected effect "
     "size.",
     "A published power calculation for the smallest effect worth detecting.",
     "State the smallest skill worth having, then compute the required n at 80% power and "
     "publish it beside the gate.", U["S2"]),
    ("Q17", "Data durability",
     "Where do immutable captures live?",
     "Captures live in the git repository, which is a static-site host.",
     "A store outside the site, with freshness monitoring and alerting.",
     "Choose a store, then migrate the capture pipeline and add a freshness job.", U["S1"]),
    ("Q18", "Bye-club handling",
     "Is a club with no injury section healthy or simply not playing?",
     "4 Week 10 bye clubs published as byes. A club on bye has no injury section at all.",
     "A rule that joins the bye list to the availability table for every week.",
     "Capture the bye panel from the schedule page each week and join it before any "
     "'injury-free' claim is made.", U["S2"]),
]

Q_COLUMNS = [
    "question_id", "decision_blocked", "question", "what_we_have", "what_is_missing",
    "discovery_path", "official_source_url",
]


def questions():
    return [dict(zip(Q_COLUMNS, q)) for q in _Q]


# ---------------------------------------------------------------------------
# suggestions register (review before implementing)
# ---------------------------------------------------------------------------

_S = [
    # id, title, category, what it changes, options, cost of doing nothing, priority
    ("SUG-01", "Read Weeks 1-9 of the official schedule, one week at a time", "Data",
     "Turns the reconstructed standings into a real 136-game log, which unblocks opponent-aware "
     "ratings and the backtest corpus.",
     "A: read all nine weeks now. B: read them week by week as the season closes. C: skip prior "
     "weeks and start the log from Week 11.",
     "G1 and G3 stay open; every model stays naive.", "high"),
    ("SUG-02", "Probe all 32 club-hosted depth pages", "Data",
     "Settles whether route (a) for depth order is viable, which unblocks the replacement-depth "
     "feature and the deficiency matrix.",
     "A: probe all 32 and record URL/date/format. B: probe a sample of 8 first. C: abandon "
     "route (a) and close the feature.",
     "REQ-45 and REQ-06 stay blocked indefinitely.", "high"),
    ("SUG-03", "Decide the price-data policy in writing", "Governance",
     "Unblocks the price-snapshot store, origination and every residual column.",
     "A: licensed commercial feed. B: manual capture under a documented agreement. C: no "
     "prices, publish originated lines only with no market column.",
     "No residual, no CLV, no ROI, and the leaderboard can never open.", "high"),
    ("SUG-04", "Move raw injury rows behind the private data layer", "Governance",
     "Keeps the public site to derived analysis until the terms position is settled.",
     "A: move raw rows out now. B: keep them and publish the terms position first. C: leave as "
     "is.",
     "The public site may republish more than the terms permit.", "medium"),
    ("SUG-05", "Add a Wednesday/Thursday/Friday capture job", "Data",
     "Turns the injury report from a snapshot into a series, which is what the surprise signal "
     "needs.",
     "A: three captures per week. B: two (Wednesday and Friday). C: leave one per week.",
     "The delta signal cannot exist; only levels can be published.", "high"),
    ("SUG-06", "Join designations to inactives across several seasons", "Model",
     "Scores designation reliability properly and decides whether the label becomes a feature.",
     "A: two full seasons. B: the remainder of 2026 only. C: drop the feature.",
     "The label stays unusable, or worse, gets used unmeasured.", "medium"),
    ("SUG-07", "Publish a power calculation beside every gate", "Validation",
     "Replaces round gate numbers with the n actually needed to detect the smallest useful "
     "effect.",
     "A: publish the calculation for all twelve gates. B: for the ranking gates only. C: keep "
     "the stated thresholds.",
     "A strategy could pass a gate that has no power to detect anything.", "medium"),
    ("SUG-08", "Transcribe venue, roof and surface for every fixture", "Model",
     "Builds the fixture-context feature set and the stadium overlay join.",
     "A: venue for all weeks, roof/surface where published. B: venue only. C: skip.",
     "Totals and passing props stay exposed to stadium effects.", "medium"),
    ("SUG-09", "Automate the weekly 'what changed' diff", "Site",
     "Replaces the static capture with a diff column, which is what a reviewer actually reads.",
     "A: diff on injuries, depth and standings. B: injuries only. C: leave static.",
     "Week-to-week movement stays invisible.", "medium"),
    ("SUG-10", "Add freshness monitoring and alerting to the capture store", "Data",
     "Fails loudly when a source changes shape or goes stale.",
     "A: monitor all nine sources. B: monitor the injury and schedule pages. C: rely on CI.",
     "A parser can silently drift and publish blanks.", "medium"),
    ("SUG-11", "Publish the ablation protocol before the first fit", "Model",
     "Pre-registers the with/without comparison so the injury effect is measured, not asserted.",
     "A: publish the protocol now. B: publish it with the first fit. C: compare only the final "
     "models.",
     "The injury effect risks being fitted to the result.", "high"),
    ("SUG-12", "Keep the leaderboard empty until a strategy earns a row", "Leaderboard",
     "Prevents a backtest or a short lucky run from appearing as a record.",
     "A: keep the current hard rule. B: allow a shadow division with no ranking. C: rank on "
     "whatever exists.",
     "The ranking stops being evidence of skill.", "high"),
    ("SUG-13", "Capture the bye panel every week and join it to availability", "Data",
     "Stops a bye club from being read as injury-free.",
     "A: join weekly. B: note the byes in text. C: leave it.",
     "Four clubs per week are silently misread as healthy.", "high"),
    ("SUG-14", "Record the first prospective forecast before Week 11 kickoff", "Validation",
     "Starts the only record that can ever clear G8.",
     "A: freeze a model version and record Week 11. B: wait for the depth source. C: wait for "
     "prices.",
     "The prospective record stays at zero and nothing can ever qualify.", "high"),
    ("SUG-15", "Split the injury report table into club sub-tables on the site", "Site",
     "Makes a 347-row table readable without losing a row.",
     "A: sub-tables per club with a rollup. B: keep one long table with a filter. C: leave it.",
     "The single largest table is hard to review line by line.", "low"),
    ("SUG-16", "Reconcile the abbreviation trap once, centrally", "Data",
     "nfl.com prints AZ on the injury and standings pages and ARI elsewhere; joins silently "
     "drop rows.",
     "A: one alias map in the pack, asserted by a test. B: normalise per table. C: leave it.",
     "Joins between injury data and schedule data drop Arizona.", "medium"),
]

S_COLUMNS = [
    "suggestion_id", "title", "category", "what_it_changes", "options",
    "cost_of_doing_nothing", "priority",
]


def suggestions():
    return [dict(zip(S_COLUMNS, s)) for s in _S]
