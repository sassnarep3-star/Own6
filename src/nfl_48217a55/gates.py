"""Validation gates and the pre-registered strategy registry.

A gate is a binary that must be `pass` before a strategy may move from `paper` to
`live`. Every gate names the number that clears it, so "not yet" is always a measurable
statement rather than an opinion.

Pre-registration rule (REQ-67/69): a strategy's definition is frozen here, in a file
under version control, *before* any result is observed. The evaluation window opens after
the freeze. Nothing here has been tuned on a result.
"""

from __future__ import annotations

from . import capture as C

# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------
# id, name, requirement, threshold (the number that clears it), observed now, status

GATES = [
    ("G1", "Verified results feed",
     "Game-level final scores for every game in the evaluation window, read from an "
     "official page and reconciled to the official standings.",
     "136 game rows with final scores; 32-club reconciliation with 0 mismatches",
     "9 Week 10 finals; 32-club through-Week-9 table reconciled 10/10 to the pregame page",
     "fail"),
    ("G2", "Price-data policy and licensed price source",
     "A written policy on where operator prices come from, plus at least one source that "
     "actually publishes an opening and a closing number per market.",
     "1 licensed feed; opening and closing timestamps on >= 14 markets for >= 1 week",
     "0 sources; 0 markets with an external price",
     "fail"),
    ("G3", "Opponent-aware ratings",
     "Ratings fitted on the game-by-game log so strength of schedule is identified.",
     ">= 136 completed games in the log; holdout season held out",
     "reconstructed table only (no game log); rating published explicitly unadjusted",
     "fail"),
    ("G4", "Dated, attributed availability register",
     "Depth order from an official source with a date and a URL per row, for all 32 clubs.",
     "32 clubs with a dated depth row; 0 inferred tiers",
     "1 club route probed (404 on nfl.com, club-hosted link found); 0 depth rows published",
     "fail"),
    ("G5", "Designation-to-outcome join",
     "Practice/game designations joined to the official inactives for the same game.",
     ">= 2 seasons of weekly reports joined to inactives",
     "Week 9 inactives captured (13 games); Week 10 designations captured; not yet joined "
     "across seasons",
     "fail"),
    ("G6", "Designation reliability scored",
     "Play rate per designation with a confidence interval, before the label is used.",
     ">= 200 designation/outcome pairs with a Wilson interval per designation",
     "14 published resolutions, 11 definite; interval too wide to use as a feature",
     "fail"),
    ("G7", "Chronological train / validation / holdout split",
     "Seasons split by time, never at random, with a final holdout never peeked at.",
     "3 disjoint windows declared before the first fit",
     "windows declared, not yet populated (needs G1 at full length)",
     "fail"),
    ("G8", "Prospective sample",
     "Results recorded after the forecast, never before.",
     ">= 100 prospective graded forecasts per strategy",
     "0",
     "fail"),
    ("G9", "Proper-score ranking",
     "Leaderboard ordered by a proper score against a stated benchmark, with uncertainty.",
     "Brier/log score vs benchmark, game-clustered lower bound, multiplicity adjustment",
     "method specified; 0 rows to rank",
     "fail"),
    ("G10", "Joint-evidence gate for combos",
     "A parlay or prop combo may be ranked only with a validated joint probability and the "
     "operator's void/push rules.",
     "joint sample for each combo shape + documented void/push rules",
     "0 combos; no joint sample and no operator rules",
     "fail"),
    ("G11", "Control baseline",
     "Every leaderboard run carries random-pick and favourite-only controls.",
     "2 control rows per run",
     "controls specified, no run exists",
     "fail"),
    ("G12", "Drift alarm on every scraper",
     "Each parser pinned to expected row counts and required fields; missing field fails "
     "the build.",
     "1 alarm per parser, wired into CI",
     "implemented for this pack's checker (row-count and field pins)",
     "pass"),
]

GATE_STATUS = {g[0]: g[5] for g in GATES}

#: The official page whose state each gate's "observed" figure is measured against, so
#: every gate row carries a source link a reviewer can open.
GATE_SOURCES = {
    "G1": C.SOURCE_URL["S2"],   # the results feed is measured against the official schedule
    "G2": C.SOURCE_URL["S2"],   # the prices the gate needs would be for these fixtures
    "G3": C.SOURCE_URL["S3"],   # opponent-aware ratings need the log behind the standings
    "G4": C.SOURCE_URL["S9"],   # the depth route that returned 404
    "G5": C.SOURCE_URL["S5"],   # the official inactives page
    "G6": C.SOURCE_URL["S4"],   # the pregame page that publishes resolutions
    "G7": C.SOURCE_URL["S2"],
    "G8": C.SOURCE_URL["S2"],
    "G9": C.SOURCE_URL["S2"],
    "G10": C.SOURCE_URL["S2"],
    "G11": C.SOURCE_URL["S2"],
    "G12": C.SOURCE_URL["S1"],  # the drift alarm guards this capture
}


# ---------------------------------------------------------------------------
# pre-registered strategies
# ---------------------------------------------------------------------------
# id, name, family, frozen definition, benchmark, evaluation window, what would change
# our mind (two-sided), gates required, status

STRATEGIES = [
    ("48217-STR-01", "Singles: market-relative side difference", "singles",
     "Back a side when our originated fair line differs from the market line by more than a "
     "fixed threshold, after de-vigging. Threshold frozen before any result is seen.",
     "market-implied probability after de-vig",
     "Week 11 2026 onward, recorded before kickoff",
     "Promote if the game-clustered lower bound on benchmark Brier skill is > 0 over 100 "
     "prospective graded forecasts. Demote if the calibration gap exceeds 0.08 or the "
     "drawdown exceeds the staking budget.",
     "G1,G2,G3,G8,G9",
     "paper"),
    ("48217-STR-02", "Singles: totals from reconstructed strength", "singles",
     "Originate a game total from the opponent-aware rating in G3 and take the residual "
     "against the market total.",
     "market total, de-vigged",
     "Week 11 2026 onward",
     "Promote on a positive Brier skill lower bound over 100 forecasts. Demote if the mean "
     "absolute total error is not better than the naive league-average baseline by a "
     "margin whose interval excludes zero.",
     "G1,G2,G3,G8,G9",
     "paper"),
    ("48217-STR-03", "Singles: availability surprise (offense)", "singles",
     "Trade the side when the count of offensive players newly designated Out between two "
     "consecutive official reads exceeds a frozen threshold. Uses the delta between reads, "
     "never the level.",
     "market side, de-vigged",
     "Week 11 2026 onward",
     "Promote if the delta signal adds Brier skill over the no-availability model on a "
     "chronological holdout. Demote if an ablation with and without the feature shows an "
     "interval covering zero.",
     "G1,G2,G3,G4,G5,G8,G9",
     "paper"),
    ("48217-STR-04", "Singles: availability surprise (defense)", "singles",
     "As STR-03 but on defensive units, keyed to the opponent's offensive unit.",
     "market side, de-vigged",
     "Week 11 2026 onward",
     "Promote if the delta signal adds Brier skill over the no-availability model on a "
     "chronological holdout. Demote if an ablation with and without the feature shows an "
     "interval covering zero.",
     "G1,G2,G3,G4,G5,G8,G9",
     "paper"),
    ("48217-STR-05", "Game parlay: correlated side and total", "parlay",
     "Combine a side and a total from the same game only with a directly validated joint "
     "probability. Marginals are never multiplied.",
     "market parlay price, de-vigged, after the operator's void rules",
     "Not opened until G10 clears",
     "Promote only with a joint sample and documented void/push rules. Demote if the joint "
     "model's calibration gap on combo tickets exceeds 0.08.",
     "G1,G2,G3,G8,G9,G10",
     "paper"),
    ("48217-STR-06", "Same-game parlay: player and team", "same-game parlay",
     "Combine a player prop with a team side in the same game, joint-validated only.",
     "market SGP price after void rules",
     "Not opened until G10 clears",
     "Promote only with a joint sample. Demote if the dependence assumption fails an "
     "out-of-sample check on joint outcomes.",
     "G1,G2,G3,G8,G9,G10",
     "paper"),
    ("48217-STR-07", "Prop combo: two players, same game", "prop combo",
     "Combine two player props from the same game, joint-validated only.",
     "market combo price after void rules",
     "Not opened until G10 clears",
     "Promote only with a joint sample. Demote if the residual dependence is not stable "
     "across two chronological windows.",
     "G1,G2,G3,G8,G9,G10",
     "paper"),
    ("48217-STR-08", "Control: favourites only", "control",
     "Back the market favourite in every game. Not a candidate for reward; it exists so a "
     "strategy that merely rides favourites is visible as such.",
     "market side, de-vigged",
     "Every run",
     "Never promoted. Reported beside every ranking.",
     "G1,G2,G8,G9",
     "control"),
    ("48217-STR-09", "Control: uniform random pick", "control",
     "Pick a side at random with probability one half. Not a candidate for reward.",
     "market side, de-vigged",
     "Every run",
     "Never promoted. Reported beside every ranking.",
     "G1,G2,G8,G9",
     "control"),
]


def strategy_rows():
    out = []
    for sid, name, family, definition, benchmark, window, change_mind, gates, status in STRATEGIES:
        required = [g.strip() for g in gates.split(",") if g.strip()]
        missing = [g for g in required if GATE_STATUS.get(g) != "pass"]
        out.append(
            {
                "strategy_id": sid,
                "name": name,
                "family": family,
                "frozen_definition": definition,
                "benchmark": benchmark,
                "evaluation_window": window,
                "what_would_change_our_mind": change_mind,
                "required_gates": gates,
                "gates_uncleared": ",".join(missing),
                "status": status,
                "qualified": "no",
                "qualified_reason": "gates uncleared: " + ",".join(missing) if missing else "",
                "pre_registration": "definition frozen in this file before the window opened",
                "backtest_on_leaderboard": "forbidden",
                "source_url": C.SOURCE_URL["S2"],
            }
        )
    return out


def gate_rows():
    return [
        {
            "gate_id": gid,
            "name": name,
            "requirement": req,
            "threshold": threshold,
            "observed": observed,
            "status": status,
            "source_url": GATE_SOURCES.get(gid, ""),
        }
        for gid, name, req, threshold, observed, status in GATES
    ]


def leaderboard_rows():
    """The leaderboard is empty and must be empty.

    Every gate is open, so no strategy has a single prospective graded forecast. Publishing
    a ranking here would be publishing a backtest as if it were a record, which the brief
    forbids outright.
    """
    return [
        {
            "division": d,
            "ranked_strategies": 0,
            "qualified_strategies": 0,
            "note": "no strategy has a prospective graded forecast; every gate is open",
            "source_url": C.SOURCE_URL["S2"],
        }
        for d in ("singles", "game parlays", "same-game parlays", "prop combos", "controls")
    ]


#: Non-monetary reward tiers, stated so a ranking can never be read as a payout.
REWARD_TIERS = [
    {"tier": "research priority 1",
     "evidence": "internal governance artifact: no external source; the conditions it names "
                 "are the gates on validation-gates.html",
     "condition": "Brier skill lower bound > 0 over >= 100 prospective forecasts, all gates pass",
     "reward": "highest research priority; first call on new data sources",
     "monetary": "none"},
    {"tier": "research priority 2",
     "evidence": "internal governance artifact: no external source; see validation-gates.html",
     "condition": "Brier skill point estimate > 0 but lower bound <= 0",
     "reward": "maintained in paper with a published next-sample size",
     "monetary": "none"},
    {"tier": "held",
     "evidence": "internal governance artifact: no external source; see validation-gates.html",
     "condition": "any required gate open",
     "reward": "none; the blocking gate and its clearing number are published",
     "monetary": "none"},
    {"tier": "demoted",
     "evidence": "internal governance artifact: no external source; see validation-gates.html",
     "condition": "demotion gate trips on a live strategy",
     "reward": "returned to paper; the trip reason is published",
     "monetary": "none"},
]
