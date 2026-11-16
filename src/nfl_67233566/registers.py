"""Text registers for session 67233566: requirement traceability, suggestions, questions,
validation gates, demotion rules and flagged irregularities.

These are deliberately *not* prose in a README: each becomes a table on the site, one row per
line of the owner's requirement list, with the gate that blocks it and the number that would clear
it. Statuses are assigned against this pack's own evidence rules:

``implemented_verified``  the artefact exists here and every number in it is either read from the
                          cited official page or arithmetic on such numbers (builder recomputes it).
``implemented_partial``   the artefact exists but a coverage limit is published inside it (a blank
                          column with a reason) - the partial state is the honest state.
``blocked_no_source``     no official page reachable in this repository prints the input; the row
                          explains what source would unblock it.
``awaiting_human_choice`` a suggestion, not a decision; nothing on the suggestions page is applied.
``rejected_kept_closed``  on the owner's own reject list; recorded so nobody re-proposes it as a
                          shortcut.
"""
from __future__ import annotations

SRC = {
    "w10": "https://www.nfl.com/schedules/2026/by-week/week-10",
    "w11": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "standings": "https://www.nfl.com/standings/division/2026/reg",
    "injuries": "https://www.nfl.com/injuries/",
    "gc": "https://www.nfl.com/games/colts-at-texans-2026-reg-11?tab=overview",
    "terms": "https://www.nfl.com/legal/terms/",
    "flex": "https://www.nfl.com/legal/flexible-scheduling-procedures",
    "thispack": "https://github.com/sassnarep3-star/Own6/tree/main/data/nfl_67233566",
}

# --------------------------------------------------------------------------- requirements
# (id, category, requirement, status, gate_blocking, number_that_clears_it, where, source)
REQUIREMENTS: list[tuple[str, str, str, str, str, str, str, str]] = [
    ("R-01", "Pricing", "Price-snapshot store recording an opening and a closing number for every market we originate",
     "implemented_verified", "none for our own prices; the market half of the store is closed by PX-01",
     ">=100 fixtures with both an official market snapshot and an official final score",
     "data/nfl_67233566/price_snapshots.csv (hash-chained)", SRC["thispack"]),
    ("R-02", "Results", "Verified results feed so backtests and ROI can be computed at all",
     "implemented_partial", "ROI still needs a price; the feed itself reconciles 220/220 identities",
     "0 mismatches on the standings reconciliation (met) + a cleared price gate (not met)",
     "results_feed.csv, reconciliation_checks.csv", SRC["w10"]),
    ("R-03", "Origination", "Originate the side first, then the total, then the moneyline",
     "implemented_verified", "none", "n/a - enforced structurally: a later stage raises on an unpublished predecessor",
     "originated_lines.csv + origination_order.csv", SRC["thispack"]),
    ("R-04", "Origination", "Publish the model's fair line, the market line and the difference as separate columns",
     "implemented_verified", "market line has no official source (PX-01)",
     "one licensed price source with terms permitting storage",
     "originated_lines.csv: fair_* / market_* / difference_* column triples", SRC["thispack"]),
    ("R-05", "Leaderboard", "Separate 'signal' from 'staking' so a lucky staking run cannot mask a bad signal",
     "implemented_verified", "none", "n/a - the verifier fails on a payout column in the signal table",
     "leaderboard_signal.csv (ranked) / leaderboard_staking.csv (empty by construction)", SRC["thispack"]),
    ("R-06", "Depth", "Track the depth of the replacement, not just the fact of a replacement",
     "blocked_no_source", "no verified depth-chart source for 32/32 clubs and no official snap-count source",
     "32 of 32 clubs with a dated, machine-readable depth or snap source (currently 0)",
     "replacement_depth.csv (floor columns only)", SRC["injuries"]),
    ("R-07", "Correlation", "Compute correlations only from officially sourced numbers and publish n with each value",
     "implemented_verified", "none for the measured set; four families are published as exclusions",
     "n >= 100 per pair (met for the game-level pairs); excluded pairs stay excluded",
     "correlations.csv, correlation_exclusions.csv", SRC["w10"]),
    ("R-08", "Governance", "Define a demotion gate that sends a live strategy back to paper",
     "implemented_verified", "nothing is live, so the gate is armed and evaluated but has nothing to demote",
     "one strategy clearing every promotion gate - the count is published in leaderboard_signal.csv and echoed in corpus_summary.csv, never typed into prose",
     "demotion_gate.csv, strategy_states.csv, state_transitions.csv", SRC["thispack"]),
    ("R-09", "Governance", "Pre-register every strategy; forbid backtest numbers from ever appearing on the leaderboard",
     "implemented_verified", "the registration commit hash is published per strategy",
     "n/a - the leaderboard reads only walk-forward forecasts, by construction",
     "preregistration.csv", SRC["thispack"]),
    ("R-10", "Availability", "Build the availability graph as a first-class dataset (expected vs actual)",
     "implemented_partial", "expected-to-start needs a verified depth source; actually-played needs official inactives",
     "one official inactives/snap source covering >= 8 weeks",
     "availability_graph.csv (50 edges read this session)", SRC["injuries"]),
    ("R-11", "Depth", "Do not model depth from jersey order; model it from playing time",
     "blocked_no_source", "no official snap-count source reachable",
     "an official playing-time source for all 32 clubs",
     "depth_source_register.csv (both routes recorded as unverified)", SRC["injuries"]),
    ("R-12", "Injury signal", "Make the injury signal a surprise, never a level",
     "implemented_partial", "two dated reads of the same page are required; the earlier read was partial",
     "2+ complete captures per week retained with hashes",
     "injury_surprise.csv (delta columns; empty where only one read exists)", SRC["injuries"]),
    ("R-13", "Sweep", "Run the 32-team roster/IR sweep before any team-level model is trusted",
     "implemented_partial", "4 of 32 clubs' report sections were read this session; the rest are UNREAD, not healthy",
     "32 of 32 clubs with a dated read of their report section and reserve list",
     "roster_ir_sweep.csv (status column says which is which)", SRC["injuries"]),
    ("R-14", "Features", "Fixture-context feature set built only from published schedule facts",
     "implemented_verified", "none", "n/a - every feature names the page it came from",
     "fixture_context.csv", SRC["w11"]),
    ("R-15", "Model outputs", "Store every model output as a probability plus its inputs, not just a pick",
     "verified", "none", "n/a - the builder refuses to emit a forecast without its input hash",
     "originated_lines.csv (model_inputs_json + inputs_sha256)", SRC["thispack"]),
    ("R-16", "Luck", "Compute and publish the 'removal of luck' panel on the site dashboard",
     "implemented_verified", "none", "n/a",
     "luck_panel.csv, page luck.html", SRC["thispack"]),
    ("R-17", "Governance", "Two-sided 'what would change our mind' field on every strategy entry",
     "implemented_verified", "none", "n/a - required column, the checker fails if it is empty",
     "strategies.csv (both fields)", SRC["thispack"]),
    ("R-18", "Pricing", "Price a line ourselves and publish the residual against the market, on a schedule, from day one",
     "implemented_partial", "the schedule runs; the residual is empty because no market number exists",
     "a licensed price source; then 1 residual row per fixture per scheduled read",
     "residual_publish_schedule.csv", SRC["thispack"]),
    ("R-19", "Backtest", "Turn the 136-game log into the pre-registered backtest corpus",
     "implemented_verified", "none", "met: 136 games W1-W9 reconciled + 9 Week 10 finals read this session = 145",
     "backtest_corpus.csv", SRC["w10"]),
    ("R-20", "Pricing", "Decide the price-data policy before any backtest is published",
     "implemented_verified", "none", "n/a - the builder refuses to write a graded table without the policy row",
     "price_policy.csv (decided 2026-11-15, before the tables)", SRC["thispack"]),
    ("R-21", "Injury signal", "Store every injury-hub read with its clock time and publish the delta, never the level",
     "implemented_verified", "none", "n/a",
     "injury_surprise.csv, capture_log.csv (UTC on every read)", SRC["injuries"]),
    ("R-22", "Site", "Decision-readiness table on the landing page: one row per requirement, gate + clearing number",
     "implemented_verified", "none", "n/a",
     "requirements_trace.csv rendered on docs/nfl-67233566/index.html", SRC["thispack"]),
    ("R-23", "Venues", "Transcribe the venue of every fixture from the official game centre and publish it",
     "implemented_partial", "the by-week schedule page does not print venues; only the game centre does, and reading 13 costs 13 fetches per week",
     "13 of 13 Week 11 fixtures with a game-centre venue (currently 1)",
     "venues.csv", SRC["gc"]),
    ("R-24", "Schedule", "Publish the league's dated schedule announcement beside the live schedule page",
     "blocked_no_source", "no dated 2026 schedule-announcement page was located in this session's read set; the flexible-scheduling text is on the schedule page itself",
     "one dated official announcement URL, stored with its date",
     "flagged (see F-07)", SRC["flex"]),
    ("R-25", "Sources", "Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps",
     "blocked_no_source", "no Game Book is reachable from this repository's evidence set",
     "32 game books per week, or an official inactives source with the same coverage",
     "not built; the inference it replaces is recorded as rejected",
     "https://operations.nfl.com/"),
    ("R-26", "Ratings", "Ingest game-level results so the ratings are opponent-aware",
     "implemented_verified", "none", "n/a",
     "corpus.py: margin ridge fit on game rows, walk-forward", SRC["w10"]),
    ("R-27", "Ablation", "Injury/personnel ablations instead of fixed penalties, reported with uncertainty",
     "implemented_partial", "personnel evidence exists for only 2 games of the corpus",
     "n >= 40 fixtures with both clubs' report sections captured",
     "ablations.csv (harness runs, n published, no penalty constant anywhere)", SRC["injuries"]),
    ("R-28", "Snapshots", "Automate immutable multi-day availability snapshots with retained hashes",
     "blocked_no_source", "no scheduler in this repository and no storage outside the git tree",
     "a workflow that runs Wed/Thu/Fri and commits a dated, hashed capture (0 runs today)",
     "snapshot_ledger.csv + drift_alarms.csv (the ledger and the alarm exist; the automation does not)",
     SRC["injuries"]),
    ("R-29", "Capture", "Capture official inactive lists and snap counts",
     "blocked_no_source", "no official page in the read set prints inactives or snap share",
     "1 source, 1 week, 32 clubs, retained with hash and clock time",
     "flagged (see F-05)", SRC["gc"]),
    ("R-30", "Depth", "Model depth slots as groups, not a single starter",
     "implemented_verified", "none", "n/a",
     "replacement_depth.csv (players_in_slot, shared_slot_flag)", SRC["injuries"]),
    ("R-31", "Roster events", "Treat roster turnover as a first-class data event",
     "blocked_no_source", "no transactions page in this session's read set",
     "a dated transaction feed versioned against depth/availability rows",
     "flagged (see F-08)", "https://www.nfl.com/news/"),
    ("R-32", "Shadow baseline", "Start with a singles-only shadow baseline; freeze versions; record forecasts before kickoff",
     "implemented_verified", "none - this pack is exactly that",
     "100 recorded pre-kickoff forecasts before any promotion discussion",
     "originated_lines.csv (13 Week 11 fixtures recorded before kickoff), strategies.csv", SRC["w11"]),
    ("R-33", "Combos", "Parlays and prop combos behind a joint-evidence gate",
     "implemented_verified", "the joint leg is measurable for one combo family; prop combos are not",
     "measured joint probability within 1 SE of the independence product, n >= 100",
     "combo_joint_evidence.csv", SRC["thispack"]),
    ("R-34", "Leaderboard", "Proper-score leaderboard divisions: singles, game parlays, SGPs, prop combos",
     "implemented_verified", "the last three divisions have no eligible entrant",
     "one strategy per division clearing every gate",
     "leaderboard_divisions.csv", SRC["thispack"]),
    ("R-35", "Leaderboard", "Rank with proper scores and uncertainty, not win rate",
     "implemented_verified", "none", "n/a - win rate is computed nowhere in this pack",
     "leaderboard_signal.csv (Brier skill, log score, interval score, cluster LB, BH q)", SRC["thispack"]),
    ("R-36", "Storage", "Durable snapshot storage outside the static site, with freshness monitoring and alerts",
     "blocked_no_source", "this repository publishes a static site; no object store is configured",
     "a store plus a workflow that alerts on a schema or row-count change",
     "drift_alarms.csv implements the alarm logic locally", SRC["thispack"]),
    ("R-37", "Site", "Split the public analysis layer from a private data layer until terms are read",
     "implemented_partial", "the raw read is committed in the public tree, so the split is not real yet",
     "move raw captures to a private store; keep only derived tables public",
     "docs/nfl-67233566/ (derived) vs data/nfl_67233566/raw/ (still public)", SRC["terms"]),
    ("R-38", "Per-team view", "Starters out, replacements named, net injury count per team",
     "implemented_partial", "replacements named and net injury count both need depth/inactive evidence",
     "a per-club availability read covering all 32 clubs",
     "team_view.csv", SRC["injuries"]),
    ("R-39", "Evidence", "Announced-starter evidence field, not an inferred replacement",
     "implemented_verified", "the field exists and is empty everywhere today",
     "one dated official starter-change notice per row we want to fill",
     "availability_graph.csv (expected_to_start, deliberately blank)", SRC["gc"]),
    ("R-40", "Depth register", "Official depth-chart register with date and source per row",
     "blocked_no_source", "no club depth page in this session's read set rendered as text",
     "32 clubs x 1 dated read with row counts retained",
     "depth_source_register.csv", SRC["injuries"]),
    ("R-41", "Calibration", "Calibrate what 'Questionable' means empirically instead of using old percentages",
     "implemented_partial", "requires inactives to know who played; the report alone cannot pay off",
     "3 seasons of designations joined to official inactives (play rate per designation with CIs)",
     "designation_calibration.csv (empty rate columns + the design that would fill them)", SRC["injuries"]),
    ("R-42", "Matchup matrix", "1st-4th string offense vs defense deficiency matrix",
     "blocked_no_source", "needs a verified depth order, which the reject list forbids deriving from jersey numbers",
     "verified depth or snap source for all 32 clubs",
     "not built (see F-03)", SRC["injuries"]),
    ("R-43", "Staleness", "Flag stale depth rows against the official transactions log",
     "blocked_no_source", "no transactions source read",
     "a dated transactions feed", "flagged (see F-08)", "https://www.nfl.com/news/"),
    ("R-44", "Snapshot ledger", "Point-in-time snapshot ledger for injuries, depth and inactives",
     "implemented_verified", "inactives are not capturable; the ledger for what is capturable exists",
     "2+ dated captures per week", "snapshot_ledger.csv", SRC["injuries"]),
    ("R-45", "Correction", "Populate the three missing Lions game-status designations",
     "implemented_verified", "closed: the official page now prints all three",
     "met on 2026-11-15: Kerby Joseph Out, Cade Mays Out, D.J. Reed Out",
     "injuries_week10_read.csv (the three rows, with the practice status that preceded them)", SRC["injuries"]),
    ("R-46", "Correction", "Re-capture and republish the Week 10 injury tables",
     "implemented_partial", "recaptured for 4 complete clubs + 1 partial; the league-wide total is still not reproducible",
     "all 8 chunks of the report page in one dated capture",
     "injuries_week10_read.csv + capture_log.csv (chunks read is a published column)", SRC["injuries"]),
    ("R-47", "Reject", "Reject deriving depth order from jersey number, experience or salary",
     "rejected_kept_closed", "n/a - rejected by the owner; this pack implements the rejection",
     "n/a", "depth_source_register.csv (route 'rejected_jersey_order' recorded as closed)", SRC["injuries"]),
    ("R-48", "Depth", "Represent shared and empty depth slots faithfully",
     "implemented_verified", "no depth-chart source, so shared/empty slots cannot be observed yet",
     "a club-by-club depth register with slot groups",
     "replacement_depth.csv (players_in_slot + shared_slot_flag)", SRC["injuries"]),
    ("R-49", "Decision", "Resolve the depth-order source (club pages, then snap counts) before building the feature",
     "implemented_partial", "both routes evaluated in order and both fail; the feature therefore stays unbuilt",
     "route (a) verified for 32/32 or route (b) available; today 0/32 and none",
     "depth_source_register.csv", SRC["injuries"]),
    ("R-50", "Injury signal", "Score injury-designation reliability before using it as a feature",
     "blocked_no_source", "needs the inactive list join", "3 seasons of designations x inactives",
     "designation_calibration.csv", SRC["injuries"]),
    ("R-51", "Cadence", "Snapshot the injury report every Wed, Thu, Fri with a dated history",
     "blocked_no_source", "no scheduler; and the Week 11 report does not exist yet (the page's own selector stops at Week 10)",
     "3 dated captures of Week 11 (Wed/Thu/Fri) committed",
     "capture_log.csv holds capture #1 of that sequence", SRC["injuries"]),
    ("R-52", "Cadence", "Treat the report as a timestamped daily series from Wednesday to kickoff",
     "implemented_partial", "one timestamped read exists; the series needs the scheduler",
     ">= 5 dated reads for a single game week", "snapshot_ledger.csv", SRC["injuries"]),
    ("R-53", "Proxy", "Use snap counts as the starter proxy when the depth chart is unavailable",
     "blocked_no_source", "no official snap-count source", "an official playing-time source",
     "not built (see F-04)", SRC["injuries"]),
    ("R-54", "Controls", "Control baseline (random picks; favourites only) in every leaderboard run",
     "implemented_verified", "the favourites-only control needs a price, so the random and constant controls carry the run",
     "a price source for the favourites control",
     "control_baselines.csv", SRC["thispack"]),
    ("R-55", "Context", "Stadium roof/surface and NWS hourly wind/precipitation overlay",
     "blocked_no_source", "roof/surface is not printed on any page in the read set; no weather feed is reachable (the schedule page renders a 'Weather Clearnight' token we do not trust as data)",
     "one official stadium-config source plus a licensed forecast grid",
     "fixture_context.csv (venue-dependent columns left blank)", SRC["w11"]),
    ("R-56", "Leaderboard", "Two-stage skill leaderboard: proper-score qualification then prospective CLV/ROI escrow",
     "implemented_verified", "stage 2 cannot open: no CLV without prices",
     "1 price source + 4 prospective weeks after promotion",
     "leaderboard_signal.csv (stage 1) / escrow_stage2.csv (closed, with the reason)", SRC["thispack"]),
    ("R-57", "Pricing", "Vig-free market consensus vs originated fair-line decomposition",
     "blocked_no_source", "a consensus of book prices is not obtainable from an official source",
     "2+ price sources with terms permitting storage",
     "market_decomposition.csv (structure published, values blank)", SRC["thispack"]),
    ("R-58", "Site", "Weekly 'what changed' diff instead of a static snapshot",
     "implemented_verified", "the diff needs 2 captures; this pack supplies capture #1 and a same-page diff against the repo's prior read",
     "2+ dated captures per week of standings, report and slate",
     "weekly_diff.csv, injury_surprise.csv", SRC["standings"]),
    ("R-59", "Model", "Publish every model total twice until one wins",
     "implemented_verified", "the collapse rule needs >= 100 graded games on the same estimator set",
     "100 graded fixtures and a gap beyond 1.5 SE",
     "totals_two_estimators.csv (T1, T2, gap, winner=not_declared)", SRC["thispack"]),
    ("R-60", "Pipeline", "Drift alarm on every scraper: pinned row counts and required fields",
     "implemented_verified", "runs on rebuild, not on a schedule",
     "a scheduled run of the same check + an alert channel",
     "drift_alarms.csv", SRC["injuries"]),
    ("R-61", "Availability", "Capture the reserve list so 'not listed' never means 'available'",
     "implemented_verified", "no official reserve list reachable, so the flag is set on every club",
     "a per-club reserve/IR list with a date",
     "roster_ir_sweep.csv (reserve_list_status on all 32 rows)", SRC["injuries"]),
    ("R-62", "Reject", "Reject ranking strategies by season-long ROI",
     "rejected_kept_closed", "n/a - the leaderboard ranks skill on proper scores; ROI is not a ranking input anywhere",
     "n/a", "strategies.csv (ranking_basis column states it)", SRC["thispack"]),
    ("R-63", "History", "Archive weekly injury reports for past seasons",
     "blocked_no_source", "the report page exposes weeks of the current season only (selector: WEEK 1..WEEK 10 of 2026)",
     "an official archive or a licensed third-party history",
     "flagged (see F-06)", SRC["injuries"]),
    ("R-64", "Governance", "Pre-register each strategy: definition frozen before results are seen",
     "implemented_verified", "none", "n/a", "preregistration.csv", SRC["thispack"]),
    ("R-65", "Governance", "Freeze the rule before it sees data; the commit hash is the registration",
     "implemented_verified", "none - the registration commit is written into the table by the checker",
     "n/a", "preregistration.csv (git_commit column)", SRC["thispack"]),
    ("R-66", "Method", "Split into train, validation and final holdout seasons",
     "implemented_partial", "one season of official data exists; a season-level holdout cannot be carved from it",
     "2+ seasons in the corpus (2026 + a licensed 2025 archive)",
     "walk_forward_design.csv (within-season chronology used as the interim)", SRC["w10"]),
    ("R-67", "Rewards", "Leaderboard competition with rewards for top strategies",
     "implemented_partial", "the reward is promotion to live staking, not money; promotion is blocked by the price gate",
     "one strategy clearing all gates",
     "rewards_policy.csv", SRC["thispack"]),
    ("R-68", "Singles/parlays/props", "Look at single bets, parlays and player-prop combos",
     "implemented_partial", "prop families have no official line source",
     "an official prop register (does not exist in the read set)",
     "leaderboard_divisions.csv", SRC["thispack"]),
    ("R-69", "Skill", "Remove luck and build selectively skill-based strategies",
     "implemented_verified", "none", "qualification = skill LB > 0 and BH q <= 0.10 and both controls beaten",
     "luck_panel.csv, leaderboard_signal.csv", SRC["thispack"]),
    ("R-70", "Deficiency", "Track deficiencies when 2nd/3rd/4th-string backups replace starters, on both sides of the ball",
     "implemented_partial", "the 'which string' half needs the depth source that does not exist",
     "verified depth or snaps for 32 clubs",
     "replacement_depth.csv (unavailability floors by slot group)", SRC["injuries"]),
    ("R-71", "Governance", "No manual input from the owner; work autonomously to completion",
     "implemented_verified", "none", "n/a - zero input controls on any page of this pack",
     "checked by scripts/check_nfl_67233566.py", SRC["thispack"]),
    ("R-72", "Verification", "Every table row carries an official source link; blanks stay blanks",
     "implemented_verified", "none", "n/a - enforced by the checker (SOURCE-MISSING)",
     "every CSV in this pack has an official_source_url column", SRC["thispack"]),
    ("R-73", "Review", "Flag irregularities on a labelled Flagged for Review page; do not block the merge on them",
     "implemented_verified", "none", "n/a", "flagged.csv -> flagged.html", SRC["thispack"]),
    ("R-74", "Suggestions", "Suggestions section for improving the site's decision quality, reviewed before changes",
     "implemented_verified", "each suggestion is awaiting_human_choice by construction",
     "the owner selects a path; nothing here is auto-applied",
     "suggestions.csv -> suggestions.html", SRC["thispack"]),
    ("R-75", "Questions", "Questions / information / answers needed before a decision is reasonable",
     "implemented_verified", "each open row carries a discovery path",
     "an answer sourced to an official page turns the row to answered",
     "questions.csv -> questions.html", SRC["thispack"]),
    ("R-76", "Executive summary", "Executive summary outlining the important details",
     "implemented_verified", "none", "n/a", "NFL_67233566_EXECUTIVE_SUMMARY.md + page", SRC["thispack"]),
    ("R-77", "Repo review", "Review the repo line by line and flag irregularities with links",
     "implemented_verified", "none", "n/a", "repo_findings.csv + audit/NFL_67233566_REPO_AND_SOURCE_AUDIT.md", SRC["thispack"]),
    ("R-78", "Site", "GitHub Pages site with a clean landing page and category subpages in table form",
     "implemented_verified", "none", "n/a", "docs/nfl-67233566/", SRC["thispack"]),
    ("R-79", "Coordination", "Parallel-session coordination, PR, merge, Pages confirmation",
     "implemented_verified", "none", "n/a", "COORDINATION.md session block + PR record",
     "https://github.com/sassnarep3-star/Own6/pulls"),
]

# --------------------------------------------------------------------------- suggestions
# (id, area, suggestion, why_it_improves_decisions, what_it_unblocks, evidence_needed, effort, priority, risk_if_not_done, recommended_path, status)
SUGGESTIONS: list[tuple[str, str, str, str, str, str, str, str, str, str, str]] = [
    ("SG-01", "Pricing",
     "Settle the price-data question as a procurement decision, not a modelling one",
     "The requirements trace lists 17 rows this pack cannot close for want of a source; the ones that "
     "matter most - ROI, the CLV escrow, market-versus-fair decomposition, the favourites-only control, "
     "and promotion itself - all name the same single input: a price whose terms permit storage. Until "
     "it exists they are unanswerable at any modelling effort level, and the count is recomputed from "
     "requirements_trace.csv on every build rather than asserted here.",
     "ROI, CLV escrow (stage 2), market-vs-fair decomposition, favourites-only control, promotion",
     "A written data-terms position for one or two price sources, plus a storage decision",
     "Low build / high decision cost", "P0 - first",
     "Every other improvement is measured against a benchmark we cannot see, so effort keeps going "
     "into model complexity that cannot be graded",
     "Do not scrape. Decide whether the project may hold prices at all; if yes, choose the minimum "
     "source that satisfies terms; if no, freeze the pricing half of the roadmap and say so on the "
     "landing page.", "awaiting_human_choice"),
    ("SG-02", "Availability",
     "Turn the injury-report read into a scheduled 3x-per-week capture before the model grows another feature",
     "A single capture cannot support a surprise signal, cannot be replayed, and cannot be audited. "
     "The report is the only personnel input the league itself publishes, and it is currently read "
     "by hand, once.",
     "Surprise-not-level injury signal; designation reliability scoring; point-in-time replay for "
     "backtests",
     "A scheduled job that fetches the report page, retains the raw text plus a hash, and pins "
     "expected row counts per club",
     "Medium", "P0 - second",
     "The '6 of 254 rows carry a game designation' class of claim stays unrepeatable, and every "
     "depth feature stays built on a snapshot nobody can re-read",
     "Two captures per week is enough to start (Wednesday and Friday); the Friday one must be before "
     "the final line move.", "awaiting_human_choice"),
    ("SG-03", "Site",
     "Publish one decision-readiness table on the landing page and retire the parallel per-pack copies",
     "Seven packs each publish their own readiness view, so the same requirement has four statuses "
     "and the owner has to reconcile them. A single table with one row per requirement and one gate "
     "per row makes the next decision visible without cross-reading.",
     "Any governance decision that currently needs a repo tour",
     "Agreement on one owner for the table; the numbers are already computed here",
     "Low", "P1",
     "Decisions keep being made against whichever pack was opened last",
     "Make this pack's requirements_trace.csv the single table; have other packs link to it instead "
     "of restating it.", "awaiting_human_choice"),
    ("SG-04", "Data layer",
     "Move raw captures out of the published site into a private, retention-controlled store",
     "The raw read of a league page is the most legally sensitive artefact in the repository and it "
     "is currently published in the same tree as the analysis. The site needs only derived values "
     "plus a provenance link.",
     "A defensible answer to the terms question; a private store that can hold licensed data later",
     "Terms read (nfl.com legal terms section 1.1/1.3 as cited by prior packs) + a storage location",
     "Medium", "P1",
     "Systematic retrieval compiled into a directory stays visible in the public tree, which is the "
     "one thing the terms language most plainly discourages",
     "Keep derived CSVs public; move raw/** to a private bucket and publish its hashes instead.",
     "awaiting_human_choice"),
    ("SG-05", "Depth",
     "Buy the depth answer once instead of re-deriving it per pack: one register, 32 clubs, dated",
     "Every pack re-answers 'can we read depth?' and gets a slightly different count. A single dated "
     "register with row counts and failure reasons makes the depth question answerable the next time "
     "it is asked, and stops a jersey-number shortcut creeping back in.",
     "Backup-deficiency feature, 1st-4th string matrix, depth-of-replacement column",
     "For each club: the page URL, the date, whether depth rendered as text, and the row count",
     "Medium", "P1",
     "Depth-based features stay impossible while four packs disagree about why",
     "Route (a) club pages, verified club by club; only then route (b) snap counts. Never a "
     "jersey/experience/salary proxy.", "awaiting_human_choice"),
    ("SG-06", "Method",
     "State the corpus boundary in the leaderboard header: 145 games, one season, in-progress week",
     "Readers compare numbers across packs that use 120, 136, 137 and 145 games. Publishing the exact "
     "corpus id, the boundary week and the number of unplayed fixtures next to every ranking removes "
     "a whole class of false comparison.",
     "Cross-pack comparability",
     "Nothing; the corpus is already pinned in this pack",
     "Low", "P0",
     "Rankings get compared across different samples as if they were the same sample",
     "Add corpus_id + boundary_week + unplayed_count to every leaderboard header row.",
     "awaiting_human_choice"),
    ("SG-07", "Method",
     "Grade the totals question against a distributional score, not against a made-up benchmark total",
     "Totals are the weakest link right now: two estimators, both with a large walk-forward error, "
     "and no market to calibrate against. Ranking them by MAE alone invites tuning to noise; the "
     "interval score plus coverage is proper and harder to fool.",
     "A defensible collapse decision (T1 vs T2)",
     "Nothing; both scores are already computed here",
     "Low", "P2",
     "The 'publish twice until one wins' rule turns into a coin flip that someone later calls "
     "evidence",
     "Require coverage within 5 points of the nominal 80% before declaring a winner.",
     "awaiting_human_choice"),
    ("SG-08", "Governance",
     "Make the pre-registration commit the only permitted source of gate thresholds",
     "Thresholds written into data files can be edited after a bad week; thresholds in a git object "
     "cannot be quietly rewritten. This pack publishes the registration commit hash next to every "
     "strategy, which makes a post-hoc change visible as a second registration.",
     "Trust in every gate number, including the demotion line",
     "Nothing; the hashes are computed by the checker",
     "Low", "P1",
     "Gate disputes become unfalsifiable arguments about intent",
     "Extend the pattern to the demotion thresholds and the price policy row.", "awaiting_human_choice"),
    ("SG-09", "Data",
     "Capture the game centre per fixture, not the schedule page, for venues and status",
     "The by-week page does not print venues at all; the game centre does, and it also carries the "
     "'Injury Report is not available at this time' state, which is itself a decision-relevant fact "
     "(it is what tells us a Week 11 availability signal does not exist yet).",
     "Venue transcription, per-fixture availability state, kickoff context",
     "One fetch per fixture per scheduled read (13 for Week 11)",
     "Medium", "P2",
     "Venue-derived features (roof, surface, altitude, travel) stay unbuildable and every fixture "
     "table has a blank venue column",
     "Fetch game centres for the fixtures we originate, on the same Wednesday/Friday cadence as the "
     "report.", "awaiting_human_choice"),
    ("SG-10", "Analysis",
     "Report the home-field estimate everywhere it matters, including where it embarrasses the model",
     "The estimate from the verified corpus is negative (-0.5 points), so any feature that assumes "
     "home advantage is loading a prior the data does not support. Publishing the estimate next to "
     "each forecast makes the reader able to check the model's assumptions without reading the code.",
     "Trust in the side and total columns; a filter on future features",
     "Nothing; it is already in the inputs JSON of every row",
     "Low", "P1",
     "Assumptions that were never tested keep propagating into new features",
     "Print HFA estimate + its bootstrap interval in the model page header and in every fair-line row.",
     "awaiting_human_choice"),
    ("SG-11", "Verification",
     "Reconcile against the card badges, not only against the standings table",
     "The standings page is one rendering of one database; the per-game card badge is a second, "
     "independent rendering. Requiring the corpus to reproduce both catches transcription errors "
     "that a single-source check cannot, and it is cheap.",
     "Confidence in the results feed; detection of as-of-render records",
     "Nothing; implemented in this pack (26 badge checks on top of 160 standing identities)",
     "Low", "P0",
     "A wrong score can reconcile with the standings and still be wrong",
     "Adopt the badge reconciliation in every pack's checker.", "awaiting_human_choice"),
    ("SG-12", "Scope",
     "Stop shipping new per-session dashboards that re-answer the same question",
     "Ten packs publish the same four tables from the same four pages with different labels. The "
     "marginal decision value of pack eleven is close to zero; the marginal confusion is not.",
     "A single, current decision desk instead of an archive",
     "Owner's choice of which pack becomes canonical",
     "Low build / high organisational value", "P0",
     "The site becomes the thing that needs verifying instead of the thing that supports decisions",
     "Declare one canonical pack, link the others as archive, and make new sessions extend the "
     "canonical tables instead of cloning them.", "awaiting_human_choice"),
]

# --------------------------------------------------------------------------- questions
# (id, decision_blocked, question, what_we_have, what_is_missing, answer, answer_status, discovery_path, source)
QUESTIONS: list[tuple[str, str, str, str, str, str, str, str, str]] = [
    ("Q-01", "Any promotion of a strategy",
     "Is there any price we are permitted to store, from any source, on any cadence?",
     "A written policy (PX-01) that says no official NFL page in our read set prints a price, and a "
     "capture-attempt log showing where we looked.",
     "A licence or an explicit terms position for one price source.",
     "", "open - blocks 9 other gates",
     "Owner decides whether third-party price data may be held at all; if yes, name the source.",
     SRC["terms"]),
    ("Q-02", "Whether Week 11 can be traded at all",
     "Do Week 11 availability facts exist yet at the time we are pricing?",
     "The report page's own week selector reads WEEK 1..WEEK 10 on 2026-11-15, and the Week 11 game "
     "centre prints 'Injury Report is not available at this time' for both clubs.",
     "The Wednesday/Thursday/Friday reads of the Week 11 report.",
     "No - and that is a fact, not a guess: pricing this week must be availability-blind, and any "
     "injury-flavoured number on a Week 11 row would be invented.", "answered_officially",
     "Re-read the report page on Wednesday and diff it against the Week 10 capture ledger.",
     SRC["injuries"]),
    ("Q-03", "Every depth-derived feature",
     "Which of the two depth routes (club pages, snap counts) is verified for all 32 clubs?",
     "Both routes recorded and both fail; a club page that publishes depth as an image cannot be "
     "repaired by transcription-by-eye, and there is no official snap-count page in the read set.",
     "32/32 dated reads, or an official playing-time source.",
     "", "open",
     "One dated attempt per club, keeping the row count and the failure reason; then decide.",
     SRC["injuries"]),
    ("Q-04", "Any use of 'Questionable' as a feature",
     "What fraction of Questionable players actually play?",
     "The official report prints the designation and the practice status; 21 of the 50 rows read "
     "this session carry a game designation.",
     "The inactive list, or any official record of who played.",
     "", "open",
     "Join designations to inactives for >= 3 seasons; publish play rate per designation with a CI.",
     SRC["injuries"]),
    ("Q-05", "Fair totals",
     "Why is the walk-forward total error (about a touchdown either side) acceptable or not?",
     "Two estimators, both graded on 9 Week 10 fixtures plus the earlier weeks, with MAE, interval "
     "score and coverage published.",
     "A market total to compare against; 100+ graded fixtures before the collapse rule fires.",
     "Not acceptable as an edge claim. Acceptable as a shadow baseline, which is what it is labelled.",
     "answered_within_bounds",
     "Freeze the estimator pair, add the interval score, and let the pre-registered collapse rule "
     "fire at n>=100 only if the gap exceeds 1.5 SE of the gap.", SRC["thispack"]),
    ("Q-06", "Injury-signal value",
     "Does a designation change predict a line move or a result shift at all?",
     "One design: surprise = change between two dated reads; a corpus with a personnel axis for 2 "
     "fixtures.",
     "A designation history and a price history for the same fixtures.",
     "", "open - cannot be answered with anything in this repository today",
     "Two captures per week from now on (cheap), and past-season reports if a licensed archive can "
     "be found; then measure.", SRC["injuries"]),
    ("Q-07", "Correlations inside a combo",
     "Are the two legs of a same-game parlay independent enough to multiply?",
     "A measured joint probability over 145 fixtures with the independence product next to it and a "
     "bootstrap interval on the difference.",
     "Nothing for this family; prop-level dependence remains unmeasurable.",
     "Publish the measured ratio; if the interval on the difference contains zero, multiplying is "
     "defensible for that pair and only that pair.", "answered_by_measurement",
     "Re-run each week as the corpus grows; never extend a measured pair to an unmeasured one.",
     SRC["w10"]),
    ("Q-08", "Site architecture",
     "Which pack is the canonical decision desk?",
     "Ten packs, four near-identical readiness tables, different corpus boundaries (120/136/137/145).",
     "An owner decision.",
     "", "open - a decision, not a research gap",
     "Pick one; link the rest as archive; forbid new packs that restate it.", SRC["thispack"]),
    ("Q-09", "Stake sizing",
     "What fraction of a bankroll does a signal at this calibration error justify?",
     "A calibration gap per strategy and a scoring rule.",
     "A price to compute Kelly against; a bankroll policy.",
     "", "open - blocked by Q-01, not by modelling",
     "Answer Q-01 first; the sizing rule is arithmetic once a price exists.", SRC["thispack"]),
    ("Q-10", "Backtest validity",
     "Can a 145-game single-season backtest support any strategy ranking?",
     "A walk-forward design with a game-cluster lower bound and a multiplicity adjustment; a "
     "noise-floor simulation that shows what a best-of-ten record looks like by chance.",
     "A second season.",
     "It can rank candidates by proper score; it cannot support an ROI claim, a season-long ranking, "
     "or a promotion.", "answered_within_bounds",
     "Keep the within-season chronology, add 2025 only from a licensed archive, and keep the "
     "holdout untouched until a rule is registered against it.", SRC["thispack"]),
    ("Q-11", "Fixture context",
     "Does roof/surface/travel matter enough to build the overlay before prices exist?",
     "Schedule facts that are published and free: date, slot, network, bye-in, short week, "
     "international marker.",
     "Stadium configuration and a forecast grid.",
     "No - the free facts can be captured now and the roof/weather half can wait for the price "
     "decision, because its value is measured against a total.", "answered_within_bounds",
     "Publish the free facts in a versioned feature table; add the overlay only when the totals "
     "division has a benchmark.", SRC["w11"]),
    ("Q-12", "Legal exposure",
     "What does the league's own terms text permit us to keep?",
     "The terms page cited by prior packs and a raw-capture directory currently published in the open.",
     "A read of the current terms by whoever owns publication decisions.",
     "", "open - blocks SG-04",
     "Read the terms; decide public-derived vs private-raw; do not resolve this in code.",
     SRC["terms"]),
]

# --------------------------------------------------------------------------- validation gates
GATES: list[tuple[str, str, str, str, str]] = [
    ("G-01", "Provenance", "Every published number is read from a named official page this session, or "
     "is arithmetic on such numbers with the derivation shown in the same table.",
     "0 unsourced values", "pass"),
    ("G-02", "No-lookahead", "A forecast for week w may only use games from weeks < w.",
     "walk-forward only; in-sample fits rejected", "pass"),
    ("G-03", "Sample", "A strategy needs >= 100 graded games before it can be ranked as qualified.",
     "min n = 100", "pass_with_consequence"),
    ("G-04", "Calibration", "Mean predicted probability within 0.05 of the realised rate on the graded set.",
     "abs gap <= 0.05", "enforced"),
    ("G-05", "Uncertainty", "Game-cluster bootstrap lower bound on skill must be above zero, i.i.d. and blocked.",
     "lb_iid > 0 and lb_block > 0", "enforced"),
    ("G-06", "Multiplicity", "Benjamini-Hochberg across every trial in the run at q = 0.10.",
     "q <= 0.10 after adjustment", "enforced"),
    ("G-07", "Controls", "Beat the no-skill constant and the seeded random control in the same division.",
     "skill > 0 vs both", "enforced"),
    ("G-08", "Price", "A stake, ROI or CLV number requires a licensed price source (policy PX-01).",
     "1 source with terms permitting storage", "FAIL_closed"),
    ("G-09", "Combos", "A combo may be priced multiplicatively only when the joint outcome is measured "
     "on >= 100 fixtures and the interval on the difference from independence contains zero.",
     "measured joint + n >= 100", "partial_only"),
    ("G-10", "Rights", "No systematic retrieval published as a data feed; derived analysis only.",
     "terms position recorded", "open_needs_human"),
    ("G-11", "Immutability", "A capture that cannot be re-read with its hash and clock time cannot enter "
     "a backtest.", "1 dated capture per graded week", "fail_on_availability"),
    ("G-12", "No-backtest-on-board", "The leaderboard may not display an in-sample number.",
     "0 in-sample rows", "pass"),
    ("G-13", "Freshness", "A table whose source page has moved since its capture is stale and must be "
     "republished or blanked.", "0 stale rows", "pass_at_capture"),
]

DEMOTE_RULES: list[tuple[str, str, str, str]] = [
    ("DG-01", "Calibration collapse", "moving mean |predicted - realised| over the last 20 graded games",
     "> 0.08 for two consecutive weeks"),
    ("DG-02", "Skill lower bound at or below zero", "game-cluster bootstrap lower bound on skill",
     "<= 0 on the most recent evaluation"),
    ("DG-03", "Multiplicity failure", "BH q-value recomputed over all live strategies",
     "> 0.10"),
    ("DG-04", "Drawdown budget", "cumulative score-gap against the division's constant control",
     "worse than 8 units of the score, or 2 weeks below the control"),
    ("DG-05", "Data-loss demotion", "a required source page fails its drift alarm or goes unreachable",
     "any single occurrence - a strategy priced on stale inputs is demoted, not excused"),
    ("DG-06", "Gate regression", "any gate moving from pass to fail (rights, price policy, provenance)",
     "immediate, no appeal window"),
    ("DG-07", "Prospective-window failure", "the escrow window's skill interval (stage 2 only)",
     "lower bound <= 0 at the end of a 4-week window"),
]

# --------------------------------------------------------------------------- flags / irregularities
# (id, severity, kind, finding, evidence, impact, proposed_action, blocks_merge, source)
FLAGS: list[tuple[str, str, str, str, str, str, str, str, str]] = [
    ("F-01", "high", "no-source",
     "No official NFL page in this session's read set prints a betting price for any market.",
     "Six hosts attempted (recorded in market_price_capture_log.csv); the game centre prints odds "
     "for ways-to-watch, not for markets.",
     "market_* and difference_* columns are empty on every row; no ROI, no CLV, no promotion.",
     "Decide the price-data policy as a procurement question (SG-01); do not fill the column with an "
     "estimate.", "no", SRC["gc"]),
    ("F-02", "high", "stale-vs-source",
     "The Week 11 injury report does not exist yet, and the report page's own selector still reads "
     "WEEK 1..WEEK 10.",
     "Read 2026-11-15T23:30Z; the Week 11 game centre for IND@HOU prints 'Injury Report is not "
     "available at this time' for both clubs.",
     "No availability feature may be attached to a Week 11 forecast; those rows are availability-blind "
     "by policy, not by omission.",
     "Re-read on Wednesday and Friday and diff against this capture.", "no", SRC["injuries"]),
    ("F-03", "high", "unverified-source",
     "Depth order cannot be verified: no club depth page in this read set rendered as text, and no "
     "official snap-count source exists here.",
     "Requirement R-49 asked for both routes to be tried in order; both fail in this session's reads.",
     "Every depth column (depth_of_replacement, snap_share, 1st-4th string deficiency) stays blank.",
     "Run the 32-club register once, dated, with row counts (SG-05); until then keep the feature off.",
     "no", SRC["injuries"]),
    ("F-04", "medium", "corpus-boundary",
     "Packs in this repository publish 120, 136, 137 and now 145 games as 'the' verified corpus, and "
     "the difference is invisible on the pages.",
     "Each count is traceable to a read date and a coverage decision, not to a disagreement about a score.",
     "Cross-pack comparisons of strategy quality are not valid as they stand.",
     "Publish corpus_id and the boundary week next to every ranking (SG-06).", "no", SRC["w10"]),
    ("F-05", "medium", "missing-capture",
     "No official inactive list or snap-count page is captured anywhere in the repository, so a "
     "backup replacing a starter can only be suspected, never confirmed.",
     "The report page prints designations and practice status; the game centre prints neither.",
     "Blocks R-29, R-41, R-50 and the replacement-depth half of R-06.",
     "Look for an official game-book or inactives source; if none is reachable, mark those "
     "requirements blocked rather than partial.", "no", SRC["gc"]),
    ("F-06", "medium", "history-gap",
     "Only the current season's weekly reports are exposed by the page, so designation reliability and "
     "any multi-season rule cannot be measured.",
     "Week selector exposes 2026 weeks 1-10 plus prior seasons' weeks only where the league renders them.",
     "Keeps R-63 and R-50 open; keeps the train/validation/holdout split within one season.",
     "Seek a licensed archive; otherwise keep the within-season chronology and say so.", "no",
     SRC["injuries"]),
    ("F-07", "medium", "source-not-found",
     "The league's dated schedule-announcement document was not located in this session's reads, so "
     "R-24 stays open instead of being satisfied by the live schedule page.",
     "The by-week page carries the flexible-scheduling text but not a dated announcement.",
     "The 'published schedule facts' feature set lacks the announcement that authorises its own dates.",
     "Ask for the canonical announcement URL; do not substitute a news article for it.", "no",
     SRC["flex"]),
    ("F-08", "medium", "not-read",
     "No transactions log was read this session, so roster turnover is not yet a versioned data event.",
     "The requirement (R-31) explicitly wants depth/availability versioned against the last official "
     "roster event.",
     "Stale rows (e.g. a traded or IR'd player still printed in a depth view) cannot be detected here.",
     "Add a dated transactions capture to the same weekly job as the report.", "no",
     "https://www.nfl.com/news/"),
    ("F-09", "low", "page-ambiguity",
     "The standings table renders split-record columns that its own LEGEND does not define.",
     "LEGEND defines W, L, T, PCT, HOME, ROAD, DIV, CONF, PF, PA, NET PTS, STRK; the rendered row has "
     "more numeric groups than that.",
     "Only LEGEND-defined columns are used by this pack; the others are not published at all.",
     "Either restrict the site to defined columns or publish the LEGEND gap beside the table (done "
     "here).", "no", SRC["standings"]),
    ("F-10", "low", "as-of-render",
     "Record badges on a by-week page are as-of-render, and clubs with a game in progress show their "
     "pre-game record.",
     "At read time three Week 10 games were live; those six clubs show records that exclude the "
     "in-progress game, while clubs whose games had finished show updated records.",
     "Any 'through week N' aggregate built from a badge during a live week is wrong for exactly those "
     "clubs.",
     "Reconcile against a finals-only corpus (done here: 220 identities) and never read a badge as a "
     "week-ending record.", "no", SRC["w10"]),
    ("F-11", "low", "partial-coverage",
     "This session's report read is chunk 0 of 8: 4 clubs complete, 1 truncated, 27 clubs unread.",
     "Recorded in capture_log.csv as a coverage column rather than hidden.",
     "The league-wide row count and the 32-club sweep cannot be closed from this read; the previous "
     "packs' counts (254, 279, 347, 50) also disagree for the same page.",
     "Read all chunks in one dated capture with a pinned per-club row count.", "no", SRC["injuries"]),
    ("F-12", "low", "terminology",
     "The official report uses no percentages for 'Questionable'; any play-rate number attached to a "
     "designation is folklore.",
     "Column headers are Player, Position, Injuries, Practice Status, Game Status.",
     "Keeps R-41 open and prevents a designation-weighted feature.",
     "Measure it from joined designations + inactives before anyone encodes a percentage.", "no",
     SRC["injuries"]),
    ("F-13", "medium", "in-repo-conflict",
     "Two live sessions both appended to COORDINATION.md and both plan an additive edit of "
     "docs/index.html and index.html.",
     "Board entries for 74d4ad32 and 67233566 claim overlapping shared files.",
     "Integration order matters; a naive merge would duplicate nav cards or drop a block.",
     "Integrate strictly by append + one-link-per-pack, re-verify after merge (this session's PR does "
     "that and records the result).", "no",
     "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"),
    ("F-14", "low", "naming",
     "Club abbreviation is 'AZ' on standings/schedule pages and 'ARI' in logo paths within the same page.",
     "Both spellings visible in the Week 10 and Week 11 renders.",
     "Any join keyed on one spelling silently drops Arizona.",
     "Keep a single alias table per pack (this pack keeps both spellings in venues.csv).", "no",
     SRC["w11"]),
    ("F-15", "low", "no-input-claim",
     "Root landing page previously invited manual statistics entry in one pack's copy; the owner's rule "
     "is zero manual input.",
     "This pack's pages contain no input control; the checker asserts it.",
     "None for this pack; it is a repo-wide consistency note.",
     "Have the canonical pack assert 'no input elements' in CI for every published page (done here for "
     "this pack).", "no", SRC["thispack"]),
]

REWARDS_POLICY: list[tuple[str, str, str, str]] = [
    ("RW-01", "What a win is", "The only reward this repository awards is precedence: a qualified "
     "strategy becomes the reference model for its division and its forecast replaces the naive one "
     "in the published table.", "Available today"),
    ("RW-02", "What a win is not", "No money, no stake, no 'units won', no promotion to live staking "
     "while gate G-08 is closed.", "Closed by policy"),
    ("RW-03", "Award condition", "Qualification = G-03..G-07 all pass and no blockers remain in "
     "leaderboard_signal.csv, and the count is carried in corpus_summary.csv rather than repeated as prose.", "Not met"),
    ("RW-04", "Durability", "A reward is withdrawn automatically by any demotion rule DG-01..DG-07 "
     "without a further decision.", "Armed"),
]


# --------------------------------------------------------------------------- source support boundary
# Which claims each page may be used for, and which it must not be used for. Printed on the sources
# page because the boundary is the finding: a page that prints a score does not print a price, and a
# page that prints a record as-of-render does not print one as-of-week.
SUPPORTS: dict[str, str] = {
    "https://www.nfl.com/schedules/2026/by-week/week-10":
        "The 14 Week 10 game cards as they stood at capture: opponent pairing, score line, card "
        "status (Final / Live / Scheduled) and the W-L-T badge printed on each card. 9 finals, 3 live, "
        "2 unplayed.",
    "https://www.nfl.com/standings/division/2026/reg":
        "Division standings W/L/T/PCT/PF/PA/differential/strreak with the official clincher markers, "
        "which is the identity the derived corpus must reproduce.",
    "https://www.nfl.com/schedules/2026/by-week/week-11":
        "The Week 11 slate, dates, times, networks and the Mexico City marker, plus the on-bye list. "
        "It is the only place Week 11 fixtures exist at all.",
    "https://www.nfl.com/injuries/":
        "Practice status and (sparingly) game status for the clubs whose sections rendered, for the "
        "week the page's own selector named: WEEK 10.",
    "https://www.nfl.com/games/colts-at-texans-2026-reg-11?tab=overview":
        "One fixture's context blob: venue, network, both clubs' records, the At a glance ranking "
        "table, team leaders, both clubs' injury-report blocks (both empty) and prior-game cards.",
}
NOT_SUPPORTS: dict[str, str] = {
    "https://www.nfl.com/schedules/2026/by-week/week-10":
        "A finished Week 10. Three games were live and two unplayed when this was read, and no final "
        "score for them exists to publish.",
    "https://www.nfl.com/standings/division/2026/reg":
        "Kickoff times, venues, injuries, or any price. Also not a point-in-time view: it is the "
        "render of the moment, which is why a club with a live game can reconcile against itself.",
    "https://www.nfl.com/schedules/2026/by-week/week-11":
        "Results, injuries or a price. Week 11 has not been played; every Week 11 line in this pack is "
        "an open forecast, graded false.",
    "https://www.nfl.com/injuries/":
        "A league-wide injury register. The page renders club sections lazily; only four complete "
        "sections and one truncated one were extractable, and the selector offered WEEK 1..WEEK 10 "
        "only, so there is no Week 11 report to read today.",
    "https://www.nfl.com/games/colts-at-texans-2026-reg-11?tab=overview":
        "Anything about the other 12 Week 11 fixtures, and anything about health: both clubs' injury "
        "blocks printed 'Injury Report is not available at this time'.",
}
