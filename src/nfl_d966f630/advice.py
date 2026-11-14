"""Suggestions and open questions - for the human to choose from, never auto-applied.

Two registers in one file.

``suggestion_rows()`` are options with a cost and a risk each, all in state
``awaiting_human_choice``. Nothing in this module is implemented on the strength of
its own suggestion: the pack publishes the option, what it would change, and what it
would cost to verify.

``question_rows()`` is the shorter, more useful list: the specific things a person
has to supply or decide before the open questions can close - and, for each one, how
we would find the answer ourselves if the answer is discoverable at all. A question
with no discovery path is marked ``needs_owner_input``; one with a path is marked
``self_serveable`` and carries the script or page that would close it, because the
fastest way to unblock this project is usually to go look rather than to wait.
"""

from __future__ import annotations

from . import capture as C

SUGGESTION_FIELDS = [
    "suggestion_id", "title", "what_would_change", "why_now", "cost_or_effort",
    "risk_if_applied", "risk_if_not_applied", "touches_requirements", "status",
    "applied_by_default", "evidence_or_source", "official_source_url", "read_on_utc",
]

QUESTION_FIELDS = [
    "question_id", "question", "why_we_cannot_answer_it_ourselves", "what_an_answer_unlocks",
    "how_to_discover_it_without_a_human", "discovery_status", "blocking", "owner_to_decide",
    "related_suggestion_id", "official_source_url", "read_on_utc",
]

AWAITING = "awaiting_human_choice"


def suggestion_rows() -> list[dict[str, str]]:
    rows = [
        {
            "suggestion_id": "D966-S01",
            "title": "License one market-price source, even a small one",
            "what_would_change": "Fills market_line_* and difference_* on every originated row, unblocks "
                                 "D966-STR-09, and makes closing-line value and edge decay real measurements "
                                 "instead of blanks. Roughly half the requirement list is written against a "
                                 "number this pack cannot see.",
            "why_now": "The store, the columns and the gate are already built around the absence, so adding a "
                       "price later is an ingest, not a rewrite.",
            "cost_or_effort": "one source decision plus one ingest module; the ledger and the difference columns "
                              "already exist",
            "risk_if_applied": "operator pages carry redistribution terms of their own; a licensed feed removes "
                               "that question, a scraped one creates it",
            "risk_if_not_applied": "edge, CLV and the ROI claim stay unavailable forever, and the leaderboard "
                                   "keeps ranking against our own prices",
            "touches_requirements": "2, 4, 7",
            "evidence_or_source": "four capture attempts recorded in price_capture_attempts.csv",
            "official_source_url": C.link_for("SCHED-W10"),
        },
        {
            "suggestion_id": "D966-S02",
            "title": "Backfill Weeks 1-6 into the results feed",
            "what_would_change": "Takes the graded window from 44 games to about 136, which lifts the moneyline "
                                 "gap (flag D966-F10) away, narrows every correlation interval, and lets "
                                 "dispersion and the damping factor be fitted before Week 7 instead of on the "
                                 "window they are used in.",
            "why_now": "the ingest is one page per week at the URL pattern already in capture.py; the identity "
                       "checks and the reconciliation were written to scale to it unchanged",
            "cost_or_effort": "six page reads and six table appends; no new code",
            "risk_if_applied": "more rows to keep honest; a mid-season rule change or roster turnover can make "
                               "early-week rates a worse prior than late-week ones",
            "risk_if_not_applied": "every coefficient published today sits under flag D966-F08 for small n",
            "touches_requirements": "2, 7",
            "evidence_or_source": "correlations.csv n column; results_feed.csv week coverage",
            "official_source_url": C.link_for("SCHED-W7"),
        },
        {
            "suggestion_id": "D966-S03",
            "title": "Write the settlement conventions down as a file the site displays",
            "what_would_change": "Push, tie, no-contest and void handling are declared in backtest.py's "
                                 "docstring today. A published rules file means a graded result can be "
                                 "re-derived by someone else without reading Python.",
            "why_now": "the tie probability is now non-zero (0.0273 on the Washington-Giants line), so push "
                       "handling changes numbers rather than being a footnote",
            "cost_or_effort": "one short document, generated from the same constants the code uses",
            "risk_if_applied": "the file must then be kept in sync with the code, which is a real cost over a "
                               "year",
            "risk_if_not_applied": "a settlement disagreement later becomes an argument about what we meant",
            "touches_requirements": "2, 5",
            "evidence_or_source": "backtest.py module docstring; originated_lines.csv tie probability column",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "suggestion_id": "D966-S04",
            "title": "Ingest official per-player game statistics so prop combos can settle",
            "what_would_change": "Unblocks D966-STR-10 and correlation candidate D966-CX-02: a prop leg could be "
                                 "settled from a box score, and a prop-team parlay could be priced with a "
                                 "measured dependence instead of an assumption.",
            "why_now": "the parlay machinery (legs, push handling, joint probability from a measured rho) is "
                       "already written; only the axis is missing",
            "cost_or_effort": "a box-score ingest per game plus a player-id join against the injury report",
            "risk_if_applied": "player-name joins are where misattribution happens; a wrong join settles a leg "
                               "wrong, so the id join needs its own identity check",
            "risk_if_not_applied": "prop combinations stay specified-but-ungraded, which is the weakest place in "
                                   "the brief's list",
            "touches_requirements": "1, 7",
            "evidence_or_source": "correlation_exclusions.csv D966-CX-02; flag D966-F06",
            "official_source_url": C.link_for("SCHED-W9"),
        },
        {
            "suggestion_id": "D966-S05",
            "title": "Add an official playing-time source so depth can be weighted, not counted",
            "what_would_change": "Tiers-dropped is a lower bound built from designations. Snap counts or a "
                                 "published depth chart would let the deficit be weighted by how much a club "
                                 "actually plays the position.",
            "why_now": "the column already carries a score_kind that says the weighting is a proposal; a real "
                       "weight would replace the proposal rather than add to it",
            "cost_or_effort": "a source with redistribution rights; none of the pages read for this pack qualify",
            "risk_if_applied": "third-party depth charts are estimates with their own model error - swapping one "
                               "guess for a better-documented one is still a guess unless it is labelled",
            "risk_if_not_applied": "depth keeps reporting a floor, and the club rollup keeps understating",
            "touches_requirements": "6",
            "evidence_or_source": "correlation_exclusions.csv D966-CX-04; depth_of_replacement.csv "
                                   "depth_bound_kind",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "suggestion_id": "D966-S06",
            "title": "Decide whether cross-version movement belongs in the open/close column",
            "what_would_change": "26 markets currently show movement between the prior session's model and ours. "
                                 "Either keep the number with flag D966-F02 attached (today's choice) or blank "
                                 "it and move the figure to a separate model_revision_delta column.",
            "why_now": "the column exists and is being read; a decision now prevents it being quoted as market "
                       "movement later",
            "cost_or_effort": "one column and one sentence in the builder",
            "risk_if_applied": "blanking it hides the only measured movement available, which readers may want",
            "risk_if_not_applied": "a model rewrite gets quoted as if the market moved",
            "touches_requirements": "1, 4",
            "evidence_or_source": "price_snapshots_open_close.csv movement_note",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "suggestion_id": "D966-S07",
            "title": "Confirm the offence/defence position mapping",
            "what_would_change": "Fixes the unit split that club depth rollups and three correlations depend on. "
                                 "Special teams currently means K, P and LS; FB is mapped to offence.",
            "why_now": "flag D966-F05 is open and a mapping decision is one line in capture.py",
            "cost_or_effort": "a minute, and a re-run of the builder",
            "risk_if_applied": "none beyond re-publishing the three affected correlation rows",
            "risk_if_not_applied": "the rollup keeps carrying our assumption without a decision on record",
            "touches_requirements": "6, 7",
            "evidence_or_source": "capture.POSITION_UNIT verbatim",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "suggestion_id": "D966-S08",
            "title": "Re-read the injury report on a practice day to resolve the club-grouping anomalies",
            "what_would_change": "Flag D966-F12 lists five players printed under a club that their own position "
                                 "line contradicts. A second read on a different day shows whether it is a "
                                 "rendering artefact of the day we read it or something in the page.",
            "why_now": "cheap, and it either resolves five rows or turns them into a durable finding about the "
                       "source",
            "cost_or_effort": "one page read and a diff against the stored rows",
            "risk_if_applied": "if the two reads disagree, we then hold two versions of the same report and must "
                               "say which one every table used",
            "risk_if_not_applied": "depth counts for six clubs keep an unexplained attribution",
            "touches_requirements": "6",
            "evidence_or_source": "injury_report_rows.csv rows for Garrett, Miller, Nelson, Njoku, O'Connell",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "suggestion_id": "D966-S09",
            "title": "Let the demotion gate run before publication, not after",
            "what_would_change": "The gate is computed in the same run today, after the tables are written. "
                                 "Running it first would let the site refuse to publish a strategy that fails, "
                                 "instead of publishing it and labelling it paper.",
            "why_now": "one strategy was promoted and nine held back on real numbers; the ordering question "
                       "starts to matter the moment the pack runs daily",
            "cost_or_effort": "reorder the builder; keep the failing rows published either way",
            "risk_if_applied": "refusing to publish is worse for review than publishing with a reason - the "
                               "failing row would become invisible, which is what flags exist to prevent",
            "risk_if_not_applied": "a strategy can appear on the board for one run before it is sent back",
            "touches_requirements": "8",
            "evidence_or_source": "state_transitions.csv; validation_gates.csv",
            "official_source_url": C.link_for("REPO"),
            "note": "this one is not applied by default and the analysis argues against it",
        },
        {
            "suggestion_id": "D966-S10",
            "title": "Decide whether rewards stay non-monetary",
            "what_would_change": "The tier table pays in standing, compute priority and a badge. Cash would "
                                 "change the incentive from 'be accurate' to 'be profitable', and it runs into "
                                 "the rights position the prior session recorded for league data.",
            "why_now": "the reward table is written; changing its currency later changes what strategies optimise "
                       "for",
            "cost_or_effort": "a policy decision, no code",
            "risk_if_applied": "monetary reward on betting outcomes in a project built on league data invites "
                               "both the rights question and a regulatory one",
            "risk_if_not_applied": "none material - standing is what an autonomous leaderboard can grant itself",
            "touches_requirements": "5, 8",
            "evidence_or_source": "reward_tiers.csv why_not_cash column",
            "official_source_url": "https://www.nfl.com/legal/terms/",
        },
    ]
    for r in rows:
        r["status"] = AWAITING
        r["applied_by_default"] = "no - the human picks the path before anything changes"
        r["read_on_utc"] = C.CAPTURE_DATE_UTC
    return rows


def question_rows() -> list[dict[str, str]]:
    rows = [
        {
            "question_id": "D966-Q01",
            "question": "Is there a market-price source the project is allowed to use, and who holds the "
                        "licence?",
            "why_we_cannot_answer_it_ourselves": "Nothing reachable from this session publishes one, and whether "
                                                  "the project may consume a licensed feed is an owner decision, "
                                                  "not a lookup.",
            "what_an_answer_unlocks": "difference columns, edge statistics, CLV, D966-STR-09, and a real ROI "
                                      "denominator.",
            "how_to_discover_it_without_a_human": "Nothing further to try inside the allowlist: four source "
                                                  "classes were already attempted and logged. The next step is a "
                                                  "procurement decision.",
            "discovery_status": "needs_owner_input",
            "blocking": "requirements 4 and 7 in their edge-measurement form",
            "owner_to_decide": "project owner",
            "related_suggestion_id": "D966-S01",
            "official_source_url": C.link_for("SCHED-W10"),
        },
        {
            "question_id": "D966-Q02",
            "question": "How far back should the verified results feed go?",
            "why_we_cannot_answer_it_ourselves": "This is a scope decision, not a missing fact: more weeks means "
                                                  "more pages read and more rows to reconcile, and the pack works "
                                                  "either way.",
            "what_an_answer_unlocks": "n from 44 games to about 136, dissolving flags D966-F08 and D966-F10.",
            "how_to_discover_it_without_a_human": "Self-serveable: the URL pattern is in capture.py "
                                                  "(schedules/2026/by-week/week-N) and the same identity checks "
                                                  "apply to each added week. An agent can extend the feed without "
                                                  "a decision; it stopped at Week 7 because that was this "
                                                  "session's window.",
            "discovery_status": "self_serveable_and_deferred",
            "blocking": "statistical power, not correctness",
            "owner_to_decide": "any session that runs the ingest",
            "related_suggestion_id": "D966-S02",
            "official_source_url": C.link_for("SCHED-W7"),
        },
        {
            "question_id": "D966-Q03",
            "question": "Which settlement rule governs a push on the spread and on a total - refund, or loss?",
            "why_we_cannot_answer_it_ourselves": "There is no operator here to have a rule. Refund is the common "
                                                 "convention and what this pack implements, but the choice changes "
                                                 "graded rows: one push on a 44-game window moves a hit rate by "
                                                 "about two points.",
            "what_an_answer_unlocks": "settled legs whose denominators match whatever market eventually prices "
                                      "these lines.",
            "how_to_discover_it_without_a_human": "An operator's published rules would answer it; no such page "
                                                  "is reachable in this environment, and the league rulebook is "
                                                  "not a betting-rules source.",
            "discovery_status": "needs_owner_input_or_a_licensed_market",
            "blocking": "settlement denominators only",
            "owner_to_decide": "project owner",
            "related_suggestion_id": "D966-S03",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "question_id": "D966-Q04",
            "question": "Is the tie probability worth keeping on the published line, or should the moneyline "
                        "absorb it?",
            "why_we_cannot_answer_it_ourselves": "It depends on what the site is for. A published tie probability "
                                                  "of 0.0273 on the Washington-Giants line is unusual for a "
                                                  "dashboard and is honest; most boards fold it into the "
                                                  "moneyline.",
            "what_an_answer_unlocks": "the moneyline columns' exact meaning - no-push versus three-way.",
            "how_to_discover_it_without_a_human": "Both variants are already computed by the model; publishing "
                                                  "both is a layout decision, not a missing fact. Nothing to look "
                                                  "up.",
            "discovery_status": "self_serveable_presentation_choice",
            "blocking": "nothing",
            "owner_to_decide": "site owner",
            "related_suggestion_id": "D966-S03",
            "official_source_url": C.link_for("SCHED-W10"),
        },
        {
            "question_id": "D966-Q05",
            "question": "Which promotion thresholds should the demotion gate use at the Week 10 vintage - the "
                        "declared ones, or ones fitted to the sample?",
            "why_we_cannot_answer_it_ourselves": "n_legs >= 20, calibration gap <= 0.08 and a 8-unit drawdown "
                                                  "budget are declared numbers in demotion.py. Fitting them to 44 "
                                                  "games would let the sample choose its own pass mark, which is "
                                                  "the failure mode the requirement exists to prevent.",
            "what_an_answer_unlocks": "a gate the strategies cannot argue was set around them.",
            "how_to_discover_it_without_a_human": "Partly self-serveable: as the window grows, each threshold's "
                                                  "false-positive rate can be measured on real graded weeks and "
                                                  "published next to it, which is what the daily runner accumulates.",
            "discovery_status": "partly_self_serveable",
            "blocking": "nothing today - one promotion and nine holds, all on real numbers",
            "owner_to_decide": "project owner",
            "related_suggestion_id": "D966-S09",
            "official_source_url": C.link_for("REPO"),
        },
        {
            "question_id": "D966-Q06",
            "question": "Should the five club-grouping anomalies on the injury report be re-read or reported "
                        "upstream?",
            "why_we_cannot_answer_it_ourselves": "We can see the page says one thing and prints another; only "
                                                 "the league can say which field is right, and re-attributing a "
                                                 "player ourselves would be invention.",
            "what_an_answer_unlocks": "depth counts for six clubs, and confidence in the rest of the report.",
            "how_to_discover_it_without_a_human": "Re-read the page on the next practice day and diff; if it "
                                                  "persists, the row stands as printed and stays flagged. That "
                                                  "diff is cheap and can be run by any session.",
            "discovery_status": "self_serveable_check_then_report",
            "blocking": "nothing - counts are published as floors",
            "owner_to_decide": "next session, then the owner if it persists",
            "related_suggestion_id": "D966-S08",
            "official_source_url": C.link_for("INJURIES"),
        },
        {
            "question_id": "D966-Q07",
            "question": "Who owns the shared hub page and the root landing when this pack is merged?",
            "why_we_cannot_answer_it_ourselves": "docs/index.html and the root index.html are shared outputs that "
                                                 "only the integration session edits, per the coordination board. "
                                                 "This pack therefore ships its own subdirectory and links out.",
            "what_an_answer_unlocks": "the pack appearing in the site's main navigation instead of only by URL.",
            "how_to_discover_it_without_a_human": "Read COORDINATION.md and the current docs/index.html diff; "
                                                  "no external information is needed.",
            "discovery_status": "coordination_already_records_it",
            "blocking": "navigation only",
            "owner_to_decide": "integration session",
            "related_suggestion_id": "",
            "official_source_url": C.link_for("REPO"),
        },
    ]
    for r in rows:
        r["read_on_utc"] = C.CAPTURE_DATE_UTC
    return rows
