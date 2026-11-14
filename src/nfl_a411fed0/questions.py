"""The decision ledger: questions, suggestions and open inputs.

Split into three tables:

* **questions**  - what must be answered before a decision is reasonable.
  Each carries ``have_it`` = yes/partial/no and, when no, a concrete way
  to go and get it.
* **suggestions** - proposed changes or studies, each with a recommendation
  and the reason.  Nothing here is implemented; this is the human's review
  queue.
* **open_inputs** - the specific data gaps, with the exact blocker, the
  official route to close it, and what it currently costs us.
"""
from __future__ import annotations

from typing import Dict, List

from . import dataset


def build_questions() -> List[Dict[str, object]]:
    rows = [
        # ---------------- prices ----------------
        ("A10-Q01", "Prices", "What were the opening and closing numbers on "
         "every market we originate?", "no", "",
         "Licence an official or commercially-licensed odds feed, or "
         "subscribe to a price-archiving service that republishes "
         "sportsbook opening/closing prices with timestamps. Alternatively, "
         "capture prices in-house at two fixed clock times per week from a "
         "licensed operator's public pages and store the raw HTML as the "
         "evidence of the capture.",
         "Blocks ROI entirely. Without it no strategy can leave paper, and "
         "the leaderboard can only be ranked on probability scoring.",
         "https://www.nfl.com/scores/2026/week-10"),
        ("A10-Q02", "Prices", "At what time is 'opening' defined for a market "
         "that opens on Sunday but is posted the previous Wednesday?", "no", "",
         "Pick a rule and pre-register it before any bet is placed: e.g. "
         "opening = first posted price for the market; closing = price at "
         "kickoff. Write the rule into the store schema so it cannot be "
         "re-litigated after the fact.",
         "Without a pre-registered definition, closing-line value can be "
         "gamed by choosing whichever snapshot is convenient.",
         "https://www.nfl.com/schedules/2026/REG10"),
        ("A10-Q03", "Prices", "Are we consistently getting the better of the "
         "closing number (closing-line value)?", "no", "",
         "Requires Q01 first. Then compute mean and median CLV over a "
         "pre-registered number of bets; CLV is a far faster read on skill "
         "than ROI because it does not need results to converge.",
         "CLV is the single best early-warning signal that our origination "
         "is beating the market.", "https://www.nfl.com/scores/2026/week-10"),

        # ---------------- results ----------------
        ("A10-Q04", "Results", "What were the final scores of 2026 week 4?",
         "no", "16 games missing; only NE 29 @ BUF 26 (Oct 4) is known",
         "Re-fetch https://www.nfl.com/scores/2026/week-4 - the page returns "
         "the placeholder string 'Hidden Score' in place of scores on some "
         "renders, so retry until the scores render. Fall back to "
         "https://www.nfl.com/schedules/2026/by-team/<club-slug> per club, "
         "which carries each club's completed game log.",
         "The results feed is 120 of ~136 games. Training on a season with a "
         "hole in it biases the ratings for the 32 clubs involved in week 4.",
         "https://www.nfl.com/scores/2026/week-4"),
        ("A10-Q05", "Results", "Are the standings derived from our captured "
         "results consistent with the published standings?", "partial",
         "Checked club by club; see the completeness table",
         "Re-run the PF/PA reconciliation after week 4 is recovered. The "
         "check is exact: sum of captured points for and against each club "
         "must equal the PF/PA on nfl.com/standings.",
         "This is the control that proves the results feed was transcribed "
         "correctly and is complete.",
         "https://www.nfl.com/standings/league/2026/REG"),
        ("A10-Q06", "Results", "Which games in the feed were affected by "
         "weather, overtime or a mid-game quarterback injury?", "no", "",
         "Not published as a structured field on the scores pages used. Would "
         "need box scores or play-by-play, both of which are outside what "
         "this session captured.",
         "Extreme-context games inflate the residual variance and make the "
         "model look worse calibrated than it is.",
         "https://www.nfl.com/scores/2026/week-9"),

        # ---------------- origination ----------------
        ("A10-Q07", "Origination", "Is a least-squares margin model the right "
         "functional form, or should it be a logistic/gradient-boosted model "
         "on drive-level data?", "partial",
         "Compared against a constant baseline only",
         "Benchmark the current model against two challengers on the same "
         "walk-forward splits, and only adopt a challenger that wins on "
         "out-of-sample log-loss, not on in-sample fit.",
         "Choice of model determines the ceiling on every downstream signal.",
         "https://www.nfl.com/scores/2026/week-1"),
        ("A10-Q08", "Origination", "Should the home-field advantage be fitted "
         "globally or per-venue?", "partial",
         "Fitted globally; the 2026 estimate came out slightly negative, "
         "which is unusual and may be a small-sample artefact",
         "Re-fit with venue fixed effects once the sample is larger, and "
         "pre-register a sign constraint only if there is a documented "
         "reason to expect one.",
         "A negative HFA moves every originated spread by the same amount, "
         "so a wrong sign is a systematic, not random, error.",
         "https://www.nfl.com/scores/2026/week-1"),
        ("A10-Q09", "Origination", "How much of the rating is real and how "
         "much is noise at this sample size?", "partial",
         "Split-season margin stability is low",
         "Shrink the ratings toward the mean using the observed split-season "
         "correlation as the shrinkage target, and re-measure the stability "
         "correlation each week.",
         "Unshrunk ratings over-fit small samples and produce confident bets "
         "on teams that simply got lucky.",
         "https://www.nfl.com/scores/2026/week-1"),

        # ---------------- injuries / depth ----------------
        ("A10-Q10", "Depth", "For each player ruled Out, which string "
         "replaces them and how deep does the club have to reach?", "partial",
         "Resolved only for the clubs whose depth chart rendered as text "
         "(GB, SEA, MIN, DAL). The other 24 clubs are unresolved.",
         "Fetch https://www.<club>.com/team/depth-chart for all 28 clubs on "
         "the Week 10 report. Note the Houston Texans render their depth "
         "chart as an image, so an alternative official route is needed "
         "there. Automate the capture weekly - the charts change.",
         "The depth fade strategy produced only 2 signals because the depth "
         "weights are zero for 24 of 28 clubs. The signal cannot be "
         "evaluated until coverage is complete.",
         "https://www.nfl.com/injuries/"),
        ("A10-Q11", "Depth", "How much is a 2nd-string replacement worth "
         "versus a 3rd or 4th, in points?", "no", "",
         "This is an empirical question and needs a multi-season dataset "
         "joining depth charts to results. The weights published in this pack "
         "are PROPOSED (labelled proposed_weight_not_observed) and must not "
         "be used to price anything until fitted.",
         "The depth fade is the most promising original signal in this pack "
         "and it currently has no calibrated weights.",
         "https://www.nfl.com/injuries/"),
        ("A10-Q12", "Depth", "Do the Week 10 injury report rosters match "
         "reality?", "partial",
         "Several listed players do not correspond to the clubs this session "
         "would expect from prior seasons",
         "Cross-check each club's injury report against its official club-site "
         "roster page. Flag any player who appears on the report but not on "
         "the roster.",
         "If the report rosters are synthetic or stale, everything derived "
         "from them is suspect.",
         "https://www.nfl.com/injuries/"),

        # ---------------- staking / risk ----------------
        ("A10-Q13", "Staking", "What is the bankroll, and what fraction of it "
         "may a single bet risk?", "no", "",
         "A human decision, not a data question. It must be answered before "
         "any live staking plan is armed; the demotion gate references it.",
         "Determines whether the staking layer is even meaningful.",
         "https://www.nfl.com/scores/2026/week-10"),
        ("A10-Q14", "Staking", "Should staking be capped independently of "
         "Kelly?", "no", "",
         "Recommendation: yes, cap at a fixed fraction of bankroll. See "
         "suggestion A10-S05.",
         "Full Kelly assumes the probability estimates are exact; ours are "
         "not, so uncapped Kelly over-bets.",
         "https://www.nfl.com/scores/2026/week-1"),
        ("A10-Q15", "Correlation", "What is the true correlation between the "
         "side and total residuals, and is it stable?", "partial",
         "Measured in-sample on 120 games at r = -0.18 with a 95% CI that "
         "includes zero",
         "Re-measure out-of-sample, on residuals from the walk-forward fits "
         "rather than in-sample residuals, and only once there are more "
         "games.",
         "Same-game parlays are priced off this number. If it is really zero "
         "the independent product is correct; if it is not, parlays are "
         "mispriced in one direction.",
         "https://www.nfl.com/scores/2026/week-1"),
        ("A10-Q16", "Parlays", "Do sportsbooks price our correlated parlays "
         "worse or better than the independent product?", "no", "",
         "Requires book prices for parlay markets. Not on any official NFL "
         "page; needs the same licensed feed as Q01.",
         "Determines whether the parlay family is worth building at all.",
         "https://www.nfl.com/scores/2026/week-10"),
        ("A10-Q17", "Props", "Is there any official source of player-prop "
         "lines or usage data?", "no", "",
         "None found on nfl.com this session. Prop pricing needs either a "
         "licensed feed or play-by-play data, which nextgenstats.nfl.com "
         "publishes for some metrics - that is the route to try first.",
         "Blocks the entire player-prop-combo family; A9-S10 is registered "
         "but unbuilt because of this.",
         "https://nextgenstats.nfl.com/"),
        ("A10-Q18", "Governance", "Who owns the decision to promote a "
         "strategy from paper to live?", "no", "",
         "Name an owner in COORDINATION.md and make the promotion a recorded "
         "event, not an implicit one.",
         "Without a named owner, the demotion gate is unenforceable.",
         "https://www.nfl.com/scores/2026/week-10"),
    ]
    return [
        {"question_id": q[0], "category": q[1], "question": q[2],
         "have_it": q[3], "what_we_have": q[4], "how_to_get_it": q[5],
         "why_it_matters": q[6], "official_source_url": q[7]}
        for q in rows
    ]


def build_suggestions() -> List[Dict[str, object]]:
    rows = [
        ("A10-S01", "Prices", "Close the price gap before building anything else",
         "Every other improvement is unmeasurable without opening and closing "
         "prices. Ten more strategies evaluated on probability scoring will "
         "still not tell us whether we can beat a number.",
         "Highest. This is the binding constraint on the whole programme.",
         "Licence a price feed; until then keep everything in paper and rank "
         "on Brier score only.", "not_started",
         "https://www.nfl.com/scores/2026/week-10"),
        ("A10-S02", "Results", "Recover 2026 week 4 and re-run the reconciliation",
         "16 games are missing from a 136-game season. That is a hole in the "
         "training data for every club.",
         "High - it is a small, well-defined task with an exact success test "
         "(captured PF/PA must equal published PF/PA).",
         "Retry the week-4 scores page, then fall back to per-club schedule "
         "pages.", "not_started", "https://www.nfl.com/scores/2026/week-4"),
        ("A10-S03", "Depth", "Automate weekly capture of all 32 club depth charts",
         "Only 4 of 32 charts were readable as text this session, which is why "
         "the depth-fade strategy produced 2 signals and cannot be scored.",
         "High among the original signals - this is the one thing in this pack "
         "that no generic odds feed would give us.",
         "A weekly scraper over <club>.com/team/depth-chart with a per-club "
         "render check; flag any club whose chart renders as an image.",
         "not_started", "https://www.packers.com/team/depth-chart"),
        ("A10-S04", "Origination", "Shrink the ratings toward the mean",
         "Split-season margin stability is low, which means a large part of "
         "each rating is noise. Unshrunk ratings produce confident bets on "
         "lucky teams.",
         "Medium-high. Cheap to do and it should improve out-of-sample "
         "log-loss immediately.",
         "Use the observed split-season correlation to set the shrinkage "
         "factor; re-estimate weekly and publish the factor.",
         "not_started", "https://www.nfl.com/scores/2026/week-1"),
        ("A10-S05", "Staking", "Cap the Kelly fraction and separate the staking "
         "columns permanently",
         "The martingale row in the leaderboard turned a losing signal into a "
         "paper profit right up until a drawdown that would have ended it. "
         "That is exactly the failure mode the separation is meant to expose.",
         "High as a governance matter - it costs nothing and prevents the most "
         "likely way this programme loses money.",
         "Cap any Kelly-derived stake at a fixed fraction of bankroll, and "
         "never let a staking result influence the signal ranking.",
         "not_started", "https://www.nfl.com/scores/2026/week-1"),
        ("A10-S06", "Validation", "Switch the primary skill metric from win rate "
         "to closing-line value",
         "At -110 the break-even is 52.38%, and detecting a 5-point edge takes "
         "roughly a thousand settled bets. CLV converges far faster because it "
         "does not need results.",
         "High, once prices exist. Until then use log-loss and Brier.",
         "Compute mean CLV over the trailing window and wire it into the "
         "demotion gate as rule A4-D02.",
         "blocked_on_prices", "https://www.nfl.com/scores/2026/week-10"),
        ("A10-S07", "Origination", "Model team totals jointly instead of "
         "splitting the game total by the margin",
         "The pack currently derives team totals algebraically as (total ± "
         "margin)/2. That is a convenient identity, not a model, and it will "
         "misprice a team whose scoring rate differs from its margin.",
         "Medium. It matters for the parlay family and for any prop work.",
         "Fit a third rating pair directly on each team's points scored, then "
         "check whether it beats the algebraic split out-of-sample.",
         "not_started", "https://www.nfl.com/scores/2026/week-1"),
        ("A10-S08", "Correlation", "Re-measure the side/total residual "
         "correlation out-of-sample",
         "The published value is in-sample and its confidence interval "
         "includes zero, so it cannot yet justify a parlay price adjustment.",
         "Medium. It gates the parlay family.",
         "Use walk-forward residuals rather than in-sample residuals and "
         "re-publish with n and CI.",
         "not_started", "https://www.nfl.com/scores/2026/week-1"),
        ("A10-S09", "Validation", "Pre-register every strategy parameter before "
         "the season resumes",
         "The walk-forward results in this pack were produced after the fact, "
         "on data already in hand. That is a valid backtest but it is not the "
         "same as a pre-registered one.",
         "Medium-high as a discipline. It is the difference between a "
         "backtest and a forecast.",
         "Write the parameter set to a file with a timestamp and hash it "
         "before the next week's numbers are captured.",
         "not_started", "https://www.nfl.com/scores/2026/week-1"),
        ("A10-S10", "Props", "Treat the player-prop family as blocked, not "
         "deferred",
         "No official NFL page publishes prop lines. Registering the family "
         "without a data route invites someone to fill it in later with "
         "non-official numbers.",
         "Medium as a safeguard.",
         "Keep A9-S10 in the leaderboard with a blocked status until a data "
         "route exists, and re-open only when nextgenstats or a licensed feed "
         "is available.", "not_started", "https://nextgenstats.nfl.com/"),
        ("A10-S11", "Governance", "Name an owner for promotion and demotion",
         "The demotion gate has six armed rules and no one to fire them.",
         "Low effort, high consequence.",
         "Record the owner in COORDINATION.md and make promotion a logged, "
         "timestamped event.", "not_started",
         "https://www.nfl.com/injuries/"),
        ("A10-S12", "Data", "Ask the shared session that owns "
         "scripts/source_coverage.py to add the NFL domains",
         "NFL.com rows are currently reported as secondary_reference_only "
         "because the publisher list has no NFL entry, which understates the "
         "provenance of every row in this pack.",
         "Low effort, affects how this pack is audited.",
         "Log a cross-session request in COORDINATION.md rather than editing "
         "the shared file.", "requested_via_coordination",
         "https://www.nfl.com/standings/league/2026/REG"),
    ]
    return [
        {"suggestion_id": r[0], "category": r[1], "suggestion": r[2],
         "reasoning": r[3], "priority": r[4], "recommended_path": r[5],
         "status": r[6], "official_source_url": r[7]}
        for r in rows
    ]


def build_open_inputs() -> List[Dict[str, object]]:
    rows = [
        ("A10-I01", "Opening and closing prices", "None",
         "nfl.com does not publish spreads, totals or moneylines on any page "
         "readable this session",
         "Licensed odds feed or an in-house capture from a licensed operator",
         "No ROI, no CLV, no settlement, nothing leaves paper",
         "https://www.nfl.com/scores/2026/week-10"),
        ("A10-I02", "2026 week 4 results", "1 of 16 games",
         "The week-4 scores page renders 'Hidden Score' instead of scores",
         "Retry the page; fall back to per-club schedule pages",
         "16-game hole in a 136-game training set",
         "https://www.nfl.com/scores/2026/week-4"),
        ("A10-I03", "Club depth charts", "4 of 32 clubs",
         "Only some club sites render the chart as extractable text; the "
         "Texans page is an image",
         "Scrape all 32 club sites weekly with a render check",
         "Depth-fade signal unevaluable (n=2)",
         "https://www.packers.com/team/depth-chart"),
        ("A10-I04", "Calibrated depth weights", "None - proposed only",
         "Requires a multi-season depth-chart-to-results join",
         "Build the historical join once depth capture is automated",
         "Depth weights published as proposed_weight_not_observed and unused",
         "https://www.nfl.com/injuries/"),
        ("A10-I05", "Player-prop lines and usage", "None",
         "No official NFL page publishes prop lines",
         "nextgenstats.nfl.com or a licensed feed",
         "A9-S10 registered but unbuilt",
         "https://nextgenstats.nfl.com/"),
        ("A10-I06", "Weather / venue conditions", "None",
         "Not a structured field on the scores pages used",
         "A weather archive keyed on venue and kickoff time",
         "Residual variance inflated; totals model looks worse than it is",
         "https://www.nfl.com/scores/2026/week-10"),
        ("A10-I07", "Official injury practice-participation history", "None",
         "Only the current week's report is published",
         "Archive the nfl.com/injuries page every day of the week",
         "Cannot distinguish a new injury from a recurring one",
         "https://www.nfl.com/injuries/"),
        ("A10-I08", "Settled bet ledger", "None",
         "There are no priced bets to settle",
         "Follows automatically once prices exist",
         "Nothing can be promoted out of paper",
         "https://www.nfl.com/scores/2026/week-10"),
    ]
    return [
        {"input_id": r[0], "missing_input": r[1], "current_coverage": r[2],
         "blocker": r[3], "route_to_close": r[4], "cost_of_the_gap": r[5],
         "official_source_url": r[6]}
        for r in rows
    ]
