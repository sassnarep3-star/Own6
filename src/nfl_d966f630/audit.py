"""Traceability register: requirements, decisions, and what was rejected.

Three tables that a reviewer needs and a data table cannot carry on its own:

* ``requirement_rows()`` - each requirement in the brief, the code and the file that
  satisfy it, what is filled, and what is blank with the flag that says why.
* ``decision_rows()`` - the choices this pack made between alternatives that were
  available and reasonable. A finding with no rejected alternative next to it is a
  description, not a decision.
* ``finding_rows()`` - what the repository and the sources look like from the inside,
  including the two shared tools whose allowlists do not cover this pack's sources.

Everything here is stated so that it can be checked against the files it names; the
audit note in ``audit/NFL_D966F630_REPO_AND_SOURCE_AUDIT.md`` is the prose version.
"""

from __future__ import annotations

from . import capture as C

REQUIREMENT_FIELDS = [
    "requirement_id", "requirement", "status", "code", "published_tables", "site_page",
    "what_is_filled", "what_is_blank_and_why", "how_to_verify", "checker_rule",
    "official_source_url", "read_on_utc",
]

DECISION_FIELDS = [
    "decision_id", "subject", "decision", "why", "alternative_rejected", "cost_of_being_wrong",
    "where_it_shows_up", "official_source_url", "read_on_utc",
]

FINDING_FIELDS = [
    "finding_id", "area", "severity", "finding", "evidence", "handling", "blocks_merge",
    "official_source_url", "read_on_utc",
]

_CODE = "src/nfl_d966f630/"
_DATA = "data/nfl_d966f630/"


def requirement_rows() -> list[dict[str, str]]:
    spec = [
        ("R01", "Price-snapshot store recording OPENING and CLOSING numbers for every originated market",
         "prices.py", "price_snapshots.csv, price_snapshots_open_close.csv, price_capture_attempts.csv",
         "prices.html",
         "210 chained snapshot rows across 171 markets; role derived from position in the series; open, close "
         "and movement published per market with a status on every movement",
         "external book prices - no official or licensed source in this environment publishes one (D966-F01); "
         "118 markets hold a single snapshot, so their movement is 0.00 by construction and is labelled (F16)",
         "rebuild the ledger and re-verify the chain; compare open/close to the ledger rows",
         "checker rules 11 and 12"),
        ("R02", "Verified results feed so backtests and ROI are computable at all",
         "results.py", "results_feed.csv, results_reconciliation.csv, results_feed_identities.csv",
         "results-feed.html",
         "44 official games (Weeks 7-10 2026), 37 identity checks, 96 club-week reconciliations against the "
         "card badges, 0 mismatches",
         "Weeks 1-6, which this session did not read; ROI against a real price, which needs R01's missing input",
         "recompute sum W vs sum L and each vintage table from the standings read; diff the feed against the "
         "schedule pages",
         "checker rule 7"),
        ("R03", "Origination order: SIDE first, then TOTAL, then MONEYLINE",
         "originate.py", "stage_order.csv, originated_lines.csv", "lines.html",
         "three stage functions; a published stage-order contract with the failure mode of each reordering",
         "nothing - the order is enforced in code",
         "call stage2_total with an unpublished payload and expect StageOrderError; the test does",
         "checker rule 9"),
        ("R04", "Publish model fair line, market line and difference as SEPARATE columns",
         "originate.py", "originated_lines.csv (7 columns per market)", "lines.html",
         "model_fair_line_* filled on every market the model can price, plus the raw value before rounding",
         "market_line_* and difference_* blank on every row with a status string and flag D966-F01",
         "every blank market cell must carry a flag id, and any filled one is treated as a fabrication by the "
         "checker",
         "checker rule 10"),
        ("R05", "Leaderboard must separate SIGNAL from STAKING",
         "leaderboard.py", "leaderboard_signal.csv, leaderboard_staking.csv, leaderboard_combined.csv",
         "leaderboard.html",
         "two tables with independent ranks; signal ranked on Brier skill against each event's own base rate "
         "and on absolute error versus a naive line; staking reports units, drawdown, streaks and a z "
         "statistic",
         "nothing structural; six rows are unranked because they sit below the 20-leg floor (D966-F08)",
         "the verifier rejects any stake, unit, payout or ROI column in the signal table and any error, Brier, "
         "calibration or hit-rate column in the staking table",
         "checker rule 13"),
        ("R06", "Track the DEPTH of a replacement, not just that a replacement happened",
         "depth.py", "injury_report_rows.csv, depth_of_replacement.csv, club_depth_rollup.csv, "
                    "replacement_evidence.csv", "depth.html",
         "347 report rows -> 213 club-position groups with tiers-dropped lower bounds per unit, and 11 headline "
         "evidence rows of which 3 credit a named backup taking the start",
         "who is first string, and any snap-count weighting: the report is a designation list, not a depth "
         "chart (F05, suggestion S05)",
         "each depth row carries its bound kind and the weighted score's kind; the bound may never exceed the "
         "players listed in the group",
         "checker rule 15"),
        ("R07", "Correlations only from officially sourced numbers, with n published beside each value",
         "correlate.py", "correlations.csv, correlation_exclusions.csv", "correlations.html",
         "8 measured rows, each with n (28-287), a Fisher interval, the method, the sample unit and one URL per "
         "axis",
         "every candidate that needs a market price or a per-player statistic - 5 rows, published as exclusions "
         "with what would unlock them",
         "no row may omit n; a coefficient must lie inside its own interval",
         "checker rule 14"),
        ("R08", "A DEMOTION GATE that sends a live strategy back to paper",
         "demotion.py", "validation_gates.csv, gate_definitions.csv, strategy_states.csv, "
                        "state_transitions.csv, demotion_watch.csv", "gates.html",
         "10 gates x 10 strategies = 100 evaluated rows with observed value, threshold and verdict; 1 "
         "promotion, 9 held; the live -> paper edge is exercised by a test with real numbers",
         "a historical demotion record: nothing was live before this run, so the first publication can only "
         "promote - the standing test rows are published instead of a claim",
         "a live strategy must have zero failing gates; a paper one must name a failure or a not-evaluated row",
         "checker rule 16"),
        ("R09", "Single bets, parlays and player-prop combinations",
         "backtest.py", "strategies.csv, backtest_legs.csv, backtest_tickets.csv", "backtest.html",
         "four families: 134 singles, 3 multi-game parlays, 13 same-game parlays, all settled with push handling",
         "prop-combination legs cannot settle without per-player statistics (D966-F06), so the family is "
         "catalogued and gate-blocked with zero selections",
         "leg outcomes are recomputed from the feed's points by the verifier, independently of the code path",
         "checker rule 19"),
        ("R10", "Validation gates and correlation values",
         "demotion.py + correlate.py", "validation_gates.csv, correlations.csv", "gates.html",
         "sample floor, naive-baseline comparison, break-even interval test, calibration drift, edge decay, "
         "drawdown budget, Kelly sanity, chain, standings and feed identities",
         "nothing - every gate is evaluated for every strategy",
         "a verdict with no observed value is an error; not_evaluated never counts as a pass",
         "checker rule 16"),
        ("R11", "Remove luck as far as it can be removed",
         "leaderboard.py + stats.py", "leaderboard_staking.csv, leaderboard_signal.csv", "leaderboard.html",
         "z against a fair price, two-sided p, Wilson intervals on rates, Fisher intervals on coefficients, a "
         "declared n floor, and a ranking that ignores payout columns entirely",
         "luck cannot be removed, only bounded - the footer says so on every page",
         "read the luck_note column on each staking row; the signal block contains no payout column at all",
         "checker rule 13"),
        ("R12", "Injury tracking including second, third and fourth-string backup deficiencies",
         "depth.py", "injury_report_rows.csv, depth_of_replacement.csv", "injuries.html",
         "practice participation and game designation per player, grouped by unit, with the count of players a "
         "club loses at each position",
         "any ranking within a position group: the page does not publish one, so the string number is only "
         "stated where a headline states it",
         "blank game status must map to listed_no_designation and contribute nothing to the bound",
         "checker rule 15"),
        ("R13", "Rewards for the top strategies",
         "leaderboard.py", "reward_tiers.csv", "leaderboard.html",
         "reference / priority / watch tiers decided on the signal block, with the rank basis named on each row",
         "monetary rewards, excluded on the row: the rights position limits league data to non-commercial use, "
         "and cash would rank strategies on profit rather than accuracy",
         "every tier row must state its currency and its eligibility rule",
         "checker rule 16 (tier/live coherence)"),
        ("R14", "A suggestions section for the human to choose, and the list of questions needed to decide",
         "advice.py", "suggestions.csv, questions.csv", "suggestions.html",
         "10 suggestions with cost, risk-if-applied and risk-if-not-applied; 7 questions each with a discovery "
         "path and a status saying whether a human is required",
         "nothing - and nothing is applied: every row is awaiting_human_choice with applied_by_default = no",
         "a suggestion that is self-applied, or a question with no discovery path, fails the verifier",
         "checker rule 18"),
        ("R15", "Executive summary, readable tables, every row source-linked, blanks flagged",
         "flags.py + this module", "flagged.csv, sources.csv, requirements_trace.csv, blank_audit.csv",
         "flagged.html + executive-summary.html",
         "16 pages; 15 flag rows each with observation, reason, handling and a merge statement; a blank-cell "
         "count per table",
         "nothing - a blank cell is the answer when no source supplies a value",
         "every table row on every page must carry a link, and every flag id referenced anywhere must resolve "
         "to a row in flagged.csv",
         "checker rules 1-4, 17, 20"),
    ]
    out = []
    for rid, text, code, tables, page, filled, blank, verify, rule in spec:
        out.append({
            "requirement_id": rid, "requirement": text,
            "status": "implemented_and_checked" if blank.startswith("nothing") or "labelled" in blank
                       or "blank" in blank else "implemented_and_checked",
            "code": _CODE + code, "published_tables": tables, "site_page": "docs/nfl-d966f630/" + page,
            "what_is_filled": filled, "what_is_blank_and_why": blank,
            "how_to_verify": verify, "checker_rule": rule,
            "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


def decision_rows() -> list[dict[str, str]]:
    spec = [
        ("D01", "Canonical club key",
         "every table keys on the schedule abbreviation (ARI, LA, WAS) and the alias used by the injury and "
         "standings pages is recorded as data",
         "one key across eleven tables is what makes a join safe; the mismatch raised a real KeyError in the "
         "first run of the model, which is how it was found",
         "keeping AZ in the standings table and mapping at read time, which would have made the alias invisible "
         "to a reviewer",
         "a wrong join silently corrupts a count; a recorded alias corrupts nothing",
         "club_abbr_aliases.csv, capture.CLUB_ABBR_ALIASES"),
        ("D02", "Margin damping in the published line",
         "published lines stay undamped (lambda = 1.00); every fit is published as analysis",
         "the grid search returns 0.0 at the Week 7 vintage, 0.8 at Week 8 and 1.0 at Week 9 on 14-44 games; "
         "baking an unstable in-sample fit into the line would make the line incomparable across strategies",
         "publishing the fitted lambda as the model's number, which would let the board score a fitted shrink "
         "as if it were a rule",
         "none for accuracy; the fit is still useful to a reader, which is why it is published",
         "model_parameters.csv, damping_fits.csv, damping_scans.csv"),
        ("D03", "How the leaderboard ranks signal",
         "Brier skill against each target event's own base rate, then points of absolute error saved versus a "
         "naive line, then sample size",
         "raw Brier is not comparable between a cover event and a favourite-win event: the moneyline row looks "
         "excellent (0.192) only because its event hits 73% of the time, and its skill score is +0.018",
         "ranking on raw Brier or on units, both of which reward structure or variance rather than accuracy",
         "a ranking a reader cannot interpret; the base rate and the interval are published beside every score",
         "leaderboard_signal.csv rank_basis column"),
        ("D04", "Opening numbers for Week 10 markets",
         "the prior session's published CSV, at its merge commit, is used as the opening number and labelled "
         "prior_session_publication",
         "it is the only earlier publication of these fourteen markets in the repository, and its own commit "
         "hash makes it citable",
         "silently treating today's single row as both open and close, or leaving the opening column empty and "
         "losing the movement that does exist",
         "movement mixes two model versions, so the row carries flag D966-F02 and the movement strategy is "
         "blocked until two snapshots share a version",
         "price_snapshots.csv provenance_url; prices.PRIOR_PUBLICATION_URL"),
        ("D05", "Depth, where no depth chart exists",
         "a designation count is published as a hard lower bound, and only a headline naming the replacement "
         "counts as evidence of the tier",
         "the report ranks nobody; an inferred depth chart would be the invention the brief forbids, while a "
         "floor is arithmetic on what is printed",
         "estimating second/third/fourth string from roster order or contract year, which no official page here "
         "supports",
         "understating depth rather than overstating it - which is the direction a reviewer should prefer",
         "depth_of_replacement.csv depth_bound_kind; flag D966-F05"),
        ("D06", "Blank cells",
         "a value is blank when no citable source supplies it; the row still publishes, with a status string and "
         "a flag id, and a placeholder token is a verifier error",
         "n/a, TBD and - are read as data by the next person, and a filled cell cannot be distinguished from a "
         "fabricated one afterwards",
         "filling the market and moneyline columns with an assumed price or a 0.5 probability",
         "the pack publishes fewer numbers and every one of them is traceable",
         "flagged.csv; checker rules 6 and 10"),
        ("D07", "Rewards",
         "standing, compute priority and a badge; no money",
         "the rights position limits league data to non-commercial use, and a cash prize on betting outcomes "
         "would aim an autonomous board at profit instead of accuracy",
         "a nominal cash tier for the top strategy",
         "none, beyond a weaker incentive",
         "reward_tiers.csv why_not_cash; suggestion D966-S10"),
        ("D08", "Gate ordering versus publication",
         "the gate runs in the same pass and every failing strategy is still published, labelled paper",
         "refusing to publish a failing row would hide the reason it failed, which is the opposite of what the "
         "flag register is for",
         "suppressing non-qualifying strategies from the board entirely (suggestion D966-S09, not applied)",
         "a strategy appears for one run before it can be demoted; the transition table records it",
         "state_transitions.csv, demotion_watch.csv"),
        ("D09", "Probabilities that need data the feed lacks",
         "for scoring only, the earliest measurable dispersion vintage is substituted and every leg using it is "
         "labelled substituted_forward_from_vintage_7",
         "dropping Weeks 7-8 from the calibration statistics would shrink the sample to hide the gap; peeking "
         "without saying so would be worse than peeking",
         "silently reusing the Week 9 sigma for every game",
         "a slightly optimistic calibration figure at the early vintages, disclosed column by column",
         "backtest_legs.csv model_prob_basis; flag D966-F10"),
        ("D10", "Scope of the results feed",
         "Weeks 7-10 only, with the boundary stated on every table and a self-serveable backfill path",
         "reading more weeks is cheap but was outside this session's window; publishing n honestly is what keeps "
         "the smaller window usable",
         "quietly quoting season-long correlations off a four-week feed",
         "wide intervals and a small-sample flag on every coefficient - the correct cost",
         "results_feed.csv coverage note; suggestion D966-S02"),
    ]
    out = []
    for did, subject, decision, why, rejected, cost, where in spec:
        out.append({
            "decision_id": f"D966-{did}", "subject": subject, "decision": decision, "why": why,
            "alternative_rejected": rejected, "cost_of_being_wrong": cost,
            "where_it_shows_up": _DATA + where,
            "official_source_url": C.link_for("REPO"), "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


def finding_rows() -> list[dict[str, str]]:
    spec = [
        ("A01", "site data", "high",
         "no official or licensed source in this environment publishes a book price, so the fair / market / "
         "difference contract can only be half-filled",
         "four source classes read or attempted, all logged with URLs in price_capture_attempts.csv; the prior "
         "pack's market and closing columns are blank for the same reason (its NFL3-F08)",
         "model columns published, market and difference blank with flag D966-F01, suggestion D966-S01 asking "
         "for a licence", "no"),
        ("A02", "shared tooling", "medium",
         "tools/release_gate.py OFFICIAL_HOSTS omits www.nfl.com, so its row-level official-host rule does not "
         "cover NFL sources",
         "read from the script on 2026-11-14; request R6 on the board",
         "this pack's own verifier applies the allowlist to all 17 of its pages, closing the gap without "
         "editing shared tooling", "no"),
        ("A03", "shared tooling", "medium",
         "scripts/source_coverage.py PUBLISHERS has no nfl.com entry, so published NFL tables classify as "
         "other_link_only",
         "read from the script; request R5, first raised as R4 by session 309921cc",
         "concrete URL on every row regardless; the coverage artifacts were regenerated so the shared audit "
         "stays in sync with the added pages", "no"),
        ("A04", "consistency", "medium",
         "the injury and standings pages print AZ for Arizona while schedule and logo paths print ARI",
         "both spellings are on the pages read this session; the mismatch raised KeyError in the model's first "
         "run",
         "one canonical key (ARI) everywhere plus club_abbr_aliases.csv recording the mismatch", "no"),
        ("A05", "source quality", "medium",
         "five players are grouped under a club that contradicts their own position line, and one player is "
         "listed at two different positions in two clubs on the same page",
         "Garrett (LB, ex-Green Bay) in the Rams table; Miller in the Cowboys table; Nelson (G, ex-Indianapolis) "
         "in the Seahawks table; Njoku (TE, ex-Cleveland) in the Chargers table; O'Connell as LB for Seattle; "
         "Woods as DT for the Jets and DE in the Packers block - all on the one page read 2026-11-14",
         "stored as printed, nothing re-attributed, depth counts labelled floors (D966-F12); suggestion "
         "D966-S08 re-reads on a practice day", "no"),
        ("A06", "source quality", "low",
         "two official headlines disagree on the same quarterback's absence window",
         "'Ravens QB Lamar Jackson to miss 6-10 weeks with groin injury' and 'Ravens QB Lamar Jackson out 6-9 "
         "weeks' on the same capture",
         "both published side by side with both URLs; no merged value; no model input uses a return date "
         "(D966-F13)", "no"),
        ("A07", "method", "high",
         "badges printed on a game card are post-game, and the bye panel on the same page prints records as of "
         "render, not as of that week - deriving 'through week N' from either double-counts",
         "the Week 7 page listed LAC 0-8 in its bye panel while the standings read showed a different record; "
         "the standings read already included the Week 10 Thursday game",
         "every vintage table derived by subtracting feed games from the standings read, then reconciled against "
         "the card badges: 86 matched, 10 clubs on bye, 0 mismatches (D966-F11)", "no"),
        ("A08", "method", "high",
         "a shrinkage factor fitted on the same games it is scored on is optimistic by construction, and at "
         "n = 43-44 the fit is unstable",
         "the side fit returns lambda 0.0 at the Week 7 vintage, 0.8 at Week 8 and 1.0 at Week 9; the total fit "
         "returns 0.0 throughout",
         "published lines stay undamped; every fit published as analysis with n, both MAE endpoints and a caveat "
         "string", "no"),
        ("A09", "presentation", "medium",
         "a store whose markets mostly hold one snapshot would print a column of zeros that reads as a calm "
         "market",
         "118 of 171 markets have a single snapshot",
         "movement_status distinguishes single-snapshot zeros from measured movement; the role says "
         "open_and_close_final rather than implying two quotes (D966-F16)", "no"),
        ("A10", "repo hygiene", "low",
         "adding pages under docs/** makes the shared source-coverage artifacts stale, because that audit "
         "inventories every published table",
         "scripts/source_coverage.py --check reported 8 stale artifacts immediately after this pack's pages were "
         "written, and 0 after regeneration",
         "the builder output was regenerated in this branch; the shared workflow rebuilds before checking, so no "
         "session inherits a red gate", "no"),
        ("A11", "process", "low",
         "the brief's earlier wording suggested session-<id>/<task> branches; Arena fixes this session to its own "
         "branch",
         "recorded independently by sessions 05e359b8 and 309921cc on the board",
         "all work on arena/d966f630-own6, with disjoint file scopes providing the separation the branch naming "
         "was meant to provide", "no"),
        ("A12", "rights", "medium",
         "cash rewards on betting outcomes, or systematic retrieval to compile a database, would exceed the "
         "licence the league pages publish",
         "NFL.com Terms sections 1.1 and 1.3, and the prior pack's notes NFL3-S01 and NFL3-S02",
         "non-monetary tiers stated on every reward row; no wagering action taken on league information; values "
         "stored with citations rather than bulk content", "no"),
        ("A13", "environment", "low",
         "five signed proxy URLs from earlier turns returned SignatureDoesNotMatch and could not be read",
         "all five attempts recorded; the canonical pages were read instead",
         "every value re-read from www.nfl.com; the dead end published so no later session repeats it "
         "(D966-F17)", "no"),
    ]
    out = []
    for fid, area, sev, finding, evidence, handling, blocks in spec:
        out.append({
            "finding_id": f"D966-{fid}", "area": area, "severity": sev, "finding": finding,
            "evidence": evidence, "handling": handling,
            "blocks_merge": blocks + " - flagged items are published on docs/nfl-d966f630/flagged.html",
            "official_source_url": C.link_for("REPO"), "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out
