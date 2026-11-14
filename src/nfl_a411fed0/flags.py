"""Irregularities flagged for human review.

Nothing here blocks the merge. Every flag names the page it came from, the
verbatim evidence, and what a reviewer should do about it.
"""

FLAGS = [
    {
        "flag_id": "A4-F01",
        "severity": "high",
        "area": "Results feed",
        "flag": "2026 Week 4 final scores could not be read from the official page",
        "evidence_verbatim": "https://www.nfl.com/scores/2026/week-4 renders the "
                             "string 'Hidden Score' in place of both team scores "
                             "for every game on the page. The alternative form "
                             "https://www.nfl.com/scores/2026/REG4 does the same.",
        "attempts": "3 fetches across two URL forms",
        "impact": "16 games missing from a ~136-game season. Training set is "
                  "88% complete and the ratings for every club that played in "
                  "week 4 are biased by an unknown amount.",
        "recommended_action": "Re-fetch the page (renders are non-deterministic) "
                              "or read each club's game log from "
                              "https://www.nfl.com/schedules/2026/by-team/<club-slug>.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-4",
    },
    {
        "flag_id": "A4-F02",
        "severity": "high",
        "area": "Prices",
        "flag": "No official NFL page publishes point spreads, totals or moneylines",
        "evidence_verbatim": "The official scores, schedule and standings pages "
                             "carry kickoff times, networks, records and final "
                             "scores only. No price field exists on any page "
                             "fetched this session.",
        "attempts": "scores, schedules, standings, and each club's own site",
        "impact": "The price-snapshot store has 84 originated markets and 0 "
                  "prices. No ROI, no closing-line value, no settlement. Gate "
                  "A4-G05 fails closed, so no strategy can leave paper.",
        "recommended_action": "Licence an odds feed, or capture prices "
                              "in-house from a licensed operator at two fixed "
                              "clock times per week and store the raw capture "
                              "as evidence.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-10",
    },
    {
        "flag_id": "A4-F03",
        "severity": "high",
        "area": "Depth of replacement",
        "flag": "Only 4 of 32 club depth charts rendered as extractable text",
        "evidence_verbatim": "packers.com, seahawks.com, vikings.com and "
                             "dallascowboys.com /team/depth-chart all returned "
                             "a text depth table. houstontexans.com renders the "
                             "depth chart as an image with no extractable "
                             "player rows.",
        "attempts": "5 club sites fetched; 1 rendered as an image",
        "impact": "Only 18 of 77 Out-or-Doubtful players have a resolved "
                  "replacement string. Strategy A9-S06 produced 2 signals and "
                  "cannot be scored. Gate A4-G09 fails.",
        "recommended_action": "Scrape all 32 club sites weekly with a per-club "
                              "render check; route any image-rendered chart to "
                              "manual review rather than guessing.",
        "status": "open",
        "official_source_url": "https://www.packers.com/team/depth-chart",
    },
    {
        "flag_id": "A4-F04",
        "severity": "medium",
        "area": "Injury report",
        "flag": "Four clubs are absent from the Week 10 injury report",
        "evidence_verbatim": "Chicago, Denver, Philadelphia and Tampa Bay have "
                             "no players listed on https://www.nfl.com/injuries/. "
                             "Those are also the four clubs on bye in Week 10.",
        "attempts": "all 8 content chunks of the injuries page were read",
        "impact": "Bye-week absence is the expected explanation, but it means "
                  "the injury load for those clubs is unknown rather than zero. "
                  "Any depth comparison involving them is incomplete.",
        "recommended_action": "Confirm against each club's own site, and treat "
                              "missing-by-absence as unknown rather than as a "
                              "clean injury report.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/injuries/",
    },
    {
        "flag_id": "A4-F05",
        "severity": "medium",
        "area": "Injury report",
        "flag": "Las Vegas lists only 5 players, far fewer than every other club",
        "evidence_verbatim": "Per-club row counts on the Week 10 report range "
                             "from 5 (LV) to 19 (DAL, LAC). Las Vegas is the "
                             "only club below 8.",
        "attempts": "counted from the 347 captured rows",
        "impact": "Either the Raiders are unusually healthy or their report is "
                  "truncated. Their depth weight is understated either way.",
        "recommended_action": "Cross-check against raiders.com.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/injuries/",
    },
    {
        "flag_id": "A4-F06",
        "severity": "medium",
        "area": "Injury report",
        "flag": "Listed players do not match the rosters this session would "
                "expect from prior seasons",
        "evidence_verbatim": "The Week 10 report lists Aaron Donald (DT) and "
                             "Myles Garrett (LB) for the Rams; Marvin Harrison "
                             "Jr. (WR) for Houston; Quenton Nelson (G) for "
                             "Seattle; Mike Evans (WR) for San Francisco; Elgton "
                             "Jenkins (C) and Denzel Boston (WR) for Cleveland; "
                             "Dexter Lawrence (DT) and Kyle Dugger (S) for "
                             "Cincinnati; David Njoku (TE) and Khalil Mack (LB) "
                             "for the Chargers.",
        "attempts": "read verbatim from the official injuries page",
        "impact": "The rows are transcribed exactly as published, so the "
                  "transcription is not in question - but the 2026 rosters "
                  "differ sharply from prior-season knowledge, which means any "
                  "prior-based expectation is the thing that is wrong. This is "
                  "recorded so a reviewer can confirm the rosters are real "
                  "before any depth signal is trusted.",
        "recommended_action": "Cross-check each club's injury report against its "
                              "official club-site roster. Do not use "
                              "prior-season knowledge to 'correct' a row.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/injuries/",
    },
    {
        "flag_id": "A4-F07",
        "severity": "medium",
        "area": "Injury report",
        "flag": "Two Jacksonville players are listed Out as "
                "'Not injury related - resting player'",
        "evidence_verbatim": "Jessie Bates (S) and Jordan Davis (DT) are "
                             "carried as Out with the injury field reading "
                             "'Not injury related - resting player'.",
        "attempts": "read verbatim from the official injuries page",
        "impact": "Resting players are not injuries. Counting them in an "
                  "injury-load score overstates Jacksonville's deficiency.",
        "recommended_action": "Exclude 'resting player' rows from any "
                              "injury-load aggregate, and track them "
                              "separately - rest is still an absence.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/injuries/",
    },
    {
        "flag_id": "A4-F08",
        "severity": "medium",
        "area": "Model",
        "flag": "Fitted 2026 home-field advantage is slightly negative",
        "evidence_verbatim": "The least-squares fit on 120 verified games "
                             "returns a home-field advantage of -0.36 points.",
        "attempts": "fit on the full verified feed",
        "impact": "Home teams have not outscored visitors in this sample. With "
                  "only 120 games the estimate is not distinguishable from "
                  "zero, and a wrong-signed constant shifts every originated "
                  "spread by the same amount.",
        "recommended_action": "Do not impose a sign. Re-fit with more games and "
                              "publish the confidence interval alongside the "
                              "point estimate.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-1",
    },
    {
        "flag_id": "A4-F09",
        "severity": "medium",
        "area": "Model",
        "flag": "The totals model does not beat a constant baseline "
                "out-of-sample",
        "evidence_verbatim": "Pooled walk-forward MAE is 12.269 points for the "
                             "model against 11.341 for a constant league-mean "
                             "prediction, over 88 out-of-sample games.",
        "attempts": "walk-forward across all six available splits",
        "impact": "Step 2 of the origination order is not yet producing a "
                  "useful signal. Gate A4-G04 fails on the totals leg.",
        "recommended_action": "Treat the published totals as diagnostic only. "
                              "Do not bet them, and revisit after week 4 is "
                              "recovered and the sample is larger.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-1",
    },
    {
        "flag_id": "A4-F10",
        "severity": "medium",
        "area": "Validation",
        "flag": "Walk-forward results are post hoc, not pre-registered",
        "evidence_verbatim": "All six walk-forward splits were evaluated after "
                             "the 2026 results were already in hand.",
        "attempts": "n/a",
        "impact": "This is a valid backtest but it is not a forecast. The "
                  "model form, ridge constant and split rule were all chosen "
                  "with knowledge of the full sample.",
        "recommended_action": "Pre-register parameters with a timestamp and "
                              "hash before the next week's numbers are "
                              "captured (suggestion A10-S09).",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-1",
    },
    {
        "flag_id": "A4-F11",
        "severity": "medium",
        "area": "Correlations",
        "flag": "The parlay-pricing correlation includes zero in its confidence "
                "interval",
        "evidence_verbatim": "A4-C03, margin-model residual vs total-model "
                             "residual: r = -0.1759, n = 120, 95% CI "
                             "[-0.3443, 0.0035].",
        "attempts": "computed on all 120 verified games",
        "impact": "Same-game parlays priced off this number would be priced off "
                  "a value that may be zero. It is also in-sample, which is the "
                  "wrong place to measure it.",
        "recommended_action": "Re-measure on walk-forward residuals (suggestion "
                              "A10-S08) before pricing any parlay.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-1",
    },
    {
        "flag_id": "A4-F12",
        "severity": "medium",
        "area": "Correlations",
        "flag": "One published correlation has n below the pricing threshold",
        "evidence_verbatim": "A4-C10 (players ruled Out vs points allowed per "
                             "game) has n = 23, below the n >= 30 floor, and "
                             "r = -0.0469 with a CI spanning zero.",
        "attempts": "computed across the 28 clubs on the Week 10 report",
        "impact": "It is published for completeness and marked "
                  "insufficient_n. It must not be used to price anything.",
        "recommended_action": "Re-measure once depth-chart coverage is complete "
                              "and more weeks of reports are archived.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/injuries/",
    },
    {
        "flag_id": "A4-F13",
        "severity": "medium",
        "area": "Origination",
        "flag": "Team totals are derived algebraically, not modelled",
        "evidence_verbatim": "Team totals are computed as (game total +/- fair "
                             "margin) / 2.",
        "attempts": "n/a",
        "impact": "That identity holds by construction for the game total but "
                  "it is not a model of each team's scoring rate. A team that "
                  "wins by out-defending rather than out-scoring will be "
                  "mispriced.",
        "recommended_action": "Fit a third rating pair directly on team points "
                              "scored (suggestion A10-S07).",
        "status": "open",
        "official_source_url": "https://www.nfl.com/scores/2026/week-1",
    },
    {
        "flag_id": "A4-F14",
        "severity": "low",
        "area": "Standings",
        "flag": "Two standings columns could not be identified on the official page",
        "evidence_verbatim": "https://www.nfl.com/standings/league/2026/REG "
                             "renders two numeric columns whose header labels "
                             "were not readable in the fetched text.",
        "attempts": "2 chunks read; header row did not resolve to a known field",
        "impact": "Those two columns were left out of the standings table "
                  "rather than guessed at. Wins, losses, ties, points for and "
                  "points against were all read cleanly.",
        "recommended_action": "Re-read the page or consult the standings API "
                              "before using any additional standings column.",
        "status": "open",
        "official_source_url": "https://www.nfl.com/standings/league/2026/REG",
    },
    {
        "flag_id": "A4-F15",
        "severity": "low",
        "area": "Provenance",
        "flag": "NFL domains are absent from the shared publisher coverage list",
        "evidence_verbatim": "scripts/source_coverage.py PUBLISHERS contains no "
                             "nfl.com entry, so NFL-sourced rows are reported "
                             "as secondary_reference_only.",
        "attempts": "read the shared script",
        "impact": "Understates the provenance of every row in this pack during "
                  "repo-wide assurance runs. Cosmetic, not a data problem.",
        "recommended_action": "Cross-session request: add nfl.com and the 32 "
                              "club domains to PUBLISHERS. Logged in "
                              "COORDINATION.md rather than editing the shared "
                              "file (suggestion A10-S12).",
        "status": "open",
        "official_source_url": "https://www.nfl.com/standings/league/2026/REG",
    },
    {
        "flag_id": "A4-F16",
        "severity": "low",
        "area": "Schedule",
        "flag": "One Week 10 game had already kicked off at capture time",
        "evidence_verbatim": "Washington at New York Giants is shown as Final, "
                             "24-21, on https://www.nfl.com/scores/2026/week-10.",
        "attempts": "read verbatim from the official scores page",
        "impact": "That game is in the slate but is not an origination target. "
                  "It is excluded from the 14 originated markets for Week 10 by "
                  "construction, since the slate table carries it as Final.",
        "recommended_action": "None. Noted so the 14 originated markets are not "
                              "mistaken for a full 15-game Week 10 slate.",
        "status": "informational",
        "official_source_url": "https://www.nfl.com/scores/2026/week-10",
    },
    {
        "flag_id": "A4-F17",
        "severity": "low",
        "area": "Depth chart",
        "flag": "The Seahawks depth chart page carries no date or official-status label",
        "evidence_verbatim": "seahawks.com/team/depth-chart shows a depth table "
                             "with no accompanying date or 'unofficial' "
                             "disclaimer, unlike the Packers, Vikings and "
                             "Cowboys pages which all carry one.",
        "attempts": "page read in full",
        "impact": "The chart_label_verbatim field is blank for Seattle, so we "
                  "cannot tell how current that chart is.",
        "recommended_action": "Record the capture date and treat the Seattle "
                              "chart as undated until the club publishes a "
                              "label.",
        "status": "open",
        "official_source_url": "https://www.seahawks.com/team/depth-chart",
    },
]
