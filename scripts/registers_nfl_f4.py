#!/usr/bin/env python3
"""Write the registers: sources, flagged, questions, suggestions, repo review,
decision ledger.

These rows are hand-authored judgements, so they live in one place with the
source URL adjacent to every claim. ``check_nfl_f4.py`` asserts that no row is
missing its source and that no URL host is outside the allowed set.
"""

from __future__ import annotations

import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "nfl_f4")
DATE = "2026-11-14"

SCHED = "https://www.nfl.com/schedules/2026/by-week/week-{w}"
STAND = "https://www.nfl.com/standings/"
INJ = "https://www.nfl.com/injuries/"
NE_DC = "https://www.patriots.com/team/depth-chart"
DET_DC = "https://www.detroitlions.com/team/depth-chart"
W10 = "https://www.nfl.com/schedules/2026/week-10"
SCORES10 = "https://www.nfl.com/scores/2026/week-10"
DK = "https://sportsbook.draftkings.com/leagues/football/nfl"
FD = "https://sportsbook.fanduel.com/navigation/nfl"
ODDS = ("https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
        "events/{eid}/competitions/{eid}/odds")
LAMAR = ("https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-"
         "friday-nov-13")

SOURCES = [
    ("S01", "NFL (nfl.com)", "2026 NFL regular-season schedules, by week (weeks 1-10)",
     SCHED.format(w="N"), "Every final score used in results.csv, with the official game URL per game.",
     "No odds, no injury designation, no depth order."),
    ("S02", "NFL (nfl.com)", "2026 NFL standings", STAND,
     "Division records, PF and PA for all 32 teams; the reconciliation target.",
     "No per-game detail, no strength of schedule, no point differential split."),
    ("S03", "NFL (nfl.com)", "Week 10 schedule and scores", W10,
     "Kickoff times in ET, broadcast, byes (CHI, DEN, PHI, TB) and the one played game.",
     "No closing lines. nfl.com does not publish sportsbook prices."),
    ("S04", "NFL (nfl.com)", "Week 10 injury report (all 28 playing teams)", INJ,
     "Player, injury, practice participation, game status (Out/Doubtful/Questionable).",
     "No depth order, no snap counts, no replacement designation."),
    ("S05", "New England Patriots (patriots.com)", "2026 depth chart",
     NE_DC, "Two-deep (and deeper) ordering for offence, defence and special teams.",
     "Self-labelled unofficial: 'the opinions of the Patriots.com writers'. Not a club depth chart."),
    ("S06", "Detroit Lions (detroitlions.com)", "2026 depth chart",
     DET_DC, "Two-deep ordering for offence, defence and special teams.",
     "Self-labelled unofficial: 'Compiled by Lions Football Communications'. Not a club depth chart."),
    ("S07", "DraftKings (via ESPN public odds endpoint)",
     "Event odds: open / current / close per market", ODDS.format(eid="{event_id}"),
     "Opening and closing line and price for spread, total and moneyline, per event.",
     "An operator's own number relayed by a third party; not an NFL publication. "
     "No historical backfill before the capture date."),
    ("S08", "DraftKings Sportsbook", "NFL league page", DK,
     "Confirms the operator exists and the market is offered.",
     "Client-rendered: yields no numeric prices to a static read (see F4-F09)."),
    ("S09", "FanDuel Sportsbook", "NFL navigation", FD,
     "A second operator's Week 10 and Week 11 prices, used only as a cross-check.",
     "Never blended with DraftKings: provider identity is stored per row."),
    ("S10", "NFL (nfl.com)", "News roundup, Friday 13 November 2026", LAMAR,
     "Confirms Lamar Jackson is out 6-10 weeks, which drives a depth finding.",
     "Not an injury report; no practice participation."),
    ("S11", "NFL (nfl.com)", "Week 10 scores page", SCORES10,
     "Final score for WAS@NYG (24-21) at the time of capture.",
     "No partial-game state useful for live grading."),
]

FLAGGED = [
    ("F4-F01", "Model", "Home-field advantage is declared at 0.0 points.", "high",
     "Carried as a declared parameter on Validation gates; not estimated from this sample.",
     ""),
    ("F4-F02", "Prices", "13 of 14 Week 10 games had no settled close at capture.",
     "high", "Stored as close_status=not_final with the live quote in the close column; "
     "never graded as a close.", W10),
    ("F4-F03", "Board", "Zero strategies are certified; leaderboard.csv is empty by design.",
     "high", "Published as a stated result with the failing gates named on every row.", ""),
    ("F4-F04", "Results", "The overtime flag is blank on all 137 games.", "low",
     "Official week pages state score and day, not overtime. Left blank rather than inferred.",
     SCHED.format(w="1")),
    ("F4-F05", "Model", "Margin dispersion sigma = 13.86 is a published league value, not fitted here.",
     "medium", "Declared on Validation gates with the reason no re-estimation was attempted.", ""),
    ("F4-F06", "Model", "Total dispersion sigma = 13.5 is declared, not measured.", "medium",
     "Same handling as F4-F05.", ""),
    ("F4-F07", "Data", "Injury-report rosters name players at clubs that differ from 2025.",
     "medium", "Recorded exactly as published (Kyler Murray, MIN; Mike Evans, SF; "
     "Justin Fields, KC); not corrected, not smoothed.", INJ),
    ("F4-F08", "Depth", "Both depth charts read are unofficial by the publisher's own words.",
     "high", "Every depth row carries status=verified_unofficial_source plus the club caveat text.",
     NE_DC),
    ("F4-F09", "Prices", "The DraftKings league page returns no numbers to a static read.",
     "low", "Prices were taken from the operator's odds payload instead; recorded here so the "
     "failed route is not mistaken for missing data.", DK),
    ("F4-F10", "Model", "Deficiency weights (0.00 / 0.35 / 0.70 / 0.70) are declared, not fitted.",
     "medium", "Monotone in string number; published with the scale so they can be overruled.", ""),
    ("F4-F11", "Depth", "30 of 32 clubs have no depth chart in this pack.", "high",
     "Only clubs whose published chart was read are populated. A jersey-ordered roster is "
     "not a depth chart, so the rest are absent rather than guessed.", NE_DC),
    ("F4-F12", "Correlations", "Rest differential could not be computed.", "medium",
     "Published as uncomputable with the reason; no proxy substituted.", ""),
    ("F4-F13", "Correlations", "Depth-deficiency correlation could not be computed.",
     "medium", "One week of snapshots for two clubs is below any usable n.", INJ),
    ("F4-F14", "Coverage", "scripts/source_coverage.py does not allowlist any NFL domain.",
     "low", "NFL rows report secondary_reference_only in that shared tool. A request is "
     "logged in COORDINATION.md rather than editing another session's script.", ""),
    ("F4-F15", "Results", "Week 10 has one result because 13 games had not been played.",
     "medium", "Stated on the results page; the feed is built to accept the rest as they settle.",
     W10),
    ("F4-F16", "Prices", "Only DraftKings supplies an open/close pair for all 14 games.",
     "medium", "FanDuel numbers are a separate provider column and are never averaged in.", FD),
    ("F4-F17", "Board", "A staking score exists for at most two settled bets.", "high",
     "Published with the luck p-value beside it; the mask test says the absence of a "
     "masking case is a small-sample artefact.", ""),
    ("F4-F18", "Scope", "Player-prop combos (S7) are blocked.", "high",
     "No official player-level stat lines were captured. Blocked at gate G5 rather than "
     "priced from a plausible assumption.", ""),
    ("F4-F19", "Review", "Prior pack nfl_309921cc differs from today's official injury page on "
     "3 of 24 NE+DET rows.", "medium",
     "Listed on Repo review with the exact fields; the prior file is not modified.", INJ),
    ("F4-F20", "Model", "Fair lines are a naive points-per-game rating with no opponent adjustment.",
     "high", "Stated in the method paragraph and on Own lines; every row is model_output, never verified.",
     ""),
]

QUESTIONS = [
    ("Q01", "Can a strategy's edge be measured at all yet?",
     "No. One settled priced game and 137 scored games without prices. Every strategy fails gate G1.",
     "answered", "Accumulate settled closes; the price store already records them."),
    ("Q02", "Is the results feed trustworthy enough to grade against?",
     "Yes for scores: 32 of 32 teams match official standings on W, L, T, PF and PA.",
     "answered", "Nothing further for scores; a play-by-play feed would be needed for overtime and drive data."),
    ("Q03", "Do we have real opening and closing numbers?",
     "Yes for 14 games: 42 markets, 168 snapshots, each with the price as well as the line.",
     "answered", "A second provider's close for the same games would allow a consensus close."),
    ("Q04", "Is the side/total correlation strong enough to price a same-game parlay?",
     "Not established: r = -0.161 at n = 137, p = 0.061, interval spanning zero.",
     "answered", "Roughly 400+ games, or a same-game-specific sample."),
    ("Q05", "Should offence and defence be modelled together?",
     "No: points scored and allowed in the same team-game correlate at 0.075 (n = 274).",
     "answered", "Nothing; this is a stable negative result."),
    ("Q06", "Does rest differential matter?",
     "Unknown — it is not computable from the sources captured.", "open",
     "Capture a per-team rest column from an official schedule with game dates and bye weeks reconciled."),
    ("Q07", "How much does losing a starter to the third string cost?",
     "Unknown. We can name the chain and the string, but not a price.", "open",
     "Collect depth snapshots weekly across a season, then regress margin on deficiency score."),
    ("Q08", "Are the depth charts authoritative?",
     "No. Both clubs label them unofficial in their own words.", "answered",
     "An official league depth feed, if one is published, would replace them."),
    ("Q09", "Is the closing line available before kickoff for every game?",
     "No. Thirteen games had not kicked off at capture, so no close existed to record.",
     "answered", "Re-read the odds endpoint after each kickoff window; the store is append-only."),
    ("Q10", "Would a lucky staking run mask a bad signal on this board?",
     "The guard fires by construction and is unit-tested; on the live board no masking case "
     "exists yet, which is a small-sample artefact.", "answered",
     "Nothing; the test is the evidence until real samples exist."),
    ("Q11", "Which operator's price should be the reference?",
     "DraftKings, because it is the only operator with an open/close pair for all 14 games.",
     "answered", "A multi-book consensus, which needs at least two operators captured the same minute."),
    ("Q12", "Is the model good enough to quote against a close?",
     "No. It is a naive rating with no opponent adjustment; its disagreements are evidence "
     "about the rating, not the line.", "open",
     "Opponent-adjusted ratings with a declared fitting window, then the same gate set."),
    ("Q13", "What happens when a live strategy decays?",
     "It is demoted by rules D1-D6 with thresholds fixed in advance.", "answered",
     "Nothing; monitor the state file."),
    ("Q14", "Can prop combos be priced?",
     "No. No official player-level stat lines were captured.", "open",
     "An official stats feed with per-game player lines, then a prop-level backtest."),
    ("Q15", "Does the repo have NFL prices anywhere else?",
     "No. Both prior NFL packs leave market cells blank and say so.", "answered",
     "Nothing."),
    ("Q16", "How many clubs have usable depth data?",
     "Two of 32, both unofficial.", "answered",
     "Read the remaining clubs' published charts, or find an official feed."),
]

SUGGESTIONS = [
    ("S01", "Publish a 'provisional, not certified' board alongside the empty one.",
     "An empty table teaches nothing about the strategies; a board with the gates printed on "
     "every row shows the work without claiming skill.",
     "A: keep the board empty. B: add a provisional board with gates in every row. "
     "C: provisional board behind a collapsed section.",
     "One page change; no new data.", "A provisional board invites being read as a "
     "ranking if the gates are skimmed.", "B", "pending_human_choice"),
    ("S02", "Capture a second operator's close for the same 14 games.",
     "A consensus close is far more defensible than one book's, and it makes the CLV "
     "measure robust to a single operator's movement.",
     "A: stay single-provider. B: add FanDuel closes. C: add a third book.",
     "One capture pass per week.", "Two operators can disagree on the line, not just the "
     "vig; the rule for which close is 'the' close has to be chosen first.", "B",
     "pending_human_choice"),
    ("S03", "Backfill settled closes for weeks 1-9.",
     "The sample floor is 100 bets; nine weeks of 14 games is enough to reach it in one step "
     "instead of waiting a season.",
     "A: wait for weeks to accumulate. B: backfill from the operator's historical endpoint "
     "if it is available. C: backfill from a licensed archive.",
     "A research pass; the feed must still stamp close_status per row.",
     "Historical closes are only trustworthy if the archive is the operator's own. A "
     "third-party archive would have to be labelled as such, not as verified.",
     "B, if the operator publishes history; otherwise C with an explicit source class.",
     "pending_human_choice"),
    ("S04", "Make the depth page cover all 32 clubs.",
     "Two clubs is a demonstration, not coverage. The injury question is league-wide.",
     "A: leave at two clubs. B: read the other 30 published charts. C: find an official feed.",
     "A read per club, per week.", "30 clubs is 30 different page formats; the parser will "
     "be fragile and every row must stay flagged unofficial.", "B, with C preferred if an "
     "official feed exists.", "pending_human_choice"),
    ("S05", "Add opponent-adjusted ratings to the model.",
     "The current rating is naive and its disagreements with the close are mostly its own error.",
     "A: keep naive ratings. B: add a simple opponent adjustment. C: fit a full model with a "
     "declared window.",
     "One modelling pass plus a validation rerun.", "Any fitting on 137 games will "
     "overfit; the fit window must be declared before the numbers are seen.",
     "B, because it is defensible at this sample size.", "pending_human_choice"),
    ("S06", "Add a per-team rest column from an official source.",
     "Rest differential is the most-cited public signal and it is currently uncomputable.",
     "A: leave it uncomputable. B: derive it from official game dates with Thursday/Monday "
     "handled explicitly. C: find a publisher that states rest days.",
     "One data pass.", "Derivation is an inference, so it cannot be labelled verified; it "
     "would have to carry its own status.", "B, labelled derived_not_verified.",
     "pending_human_choice"),
    ("S07", "Capture official player-level stat lines for prop markets.",
     "Unblocks S7 and every prop combo, which is a third of the brief's requested structures.",
     "A: skip props. B: capture official box scores per game. C: licensed stats feed.",
     "One capture pass per week.", "Box-score parsing is the most error-prone step in the "
     "whole pack; it needs its own reconciliation gate.", "B, gated like the results feed.",
     "pending_human_choice"),
    ("S08", "Add a promotion gate to mirror the demotion gate.",
     "The demotion path exists; the promotion path is currently 'clear the gates', which "
     "does not say what happens after a demotion.",
     "A: keep the current implicit path. B: publish explicit promotion criteria with the "
     "same numeric style as D1-D6.",
     "One document change.", "None material.", "B", "pending_human_choice"),
    ("S09", "Expose the reconciliation as a build gate in CI.",
     "A results feed that cannot silently drift is worth more than one that is checked by hand.",
     "A: manual check. B: add a CI workflow that fails on any mismatch.",
     "One workflow file.", "CI minutes and a new shared file that another session may also "
     "want to touch.", "B, scoped to this pack's paths only.", "pending_human_choice"),
    ("S10", "Publish a monthly decision review page.",
     "Suggestions and flags accumulate faster than they are decided; a review cadence keeps "
     "the review gate real.",
     "A: no cadence. B: monthly review page generated from the open rows.",
     "One generated page.", "A cadence nobody keeps is worse than none.",
     "B, only after the first decision is actually taken.", "pending_human_choice"),
]

REPO_REVIEW = [
    ("R01", "data/nfl_309921cc/week10_injuries.csv", "DET Kerby Joseph: practice = Full Participation",
     "Today's official page lists Did Not Participate In Practice for the same player and week.",
     "contradicted", INJ),
    ("R02", "data/nfl_309921cc/week10_injuries.csv", "DET Amon-Ra St. Brown: injury blank, game status blank",
     "Official page lists injury Rib and game status Questionable.", "incomplete", INJ),
    ("R03", "data/nfl_309921cc/week10_injuries.csv", "DET Sione Vaki: injury blank, practice = Did Not Participate",
     "Official page lists injury Ankle, Limited Participation, Questionable.", "contradicted", INJ),
    ("R04", "data/nfl_309921cc/week10_injuries.csv", "21 of 24 NE+DET rows match exactly",
     "Confirmed field by field (player, injury, practice, game status).", "confirmed", INJ),
    ("R05", "data/nfl_309921cc/standings_2026_w10.csv", "32 teams with W-L-T and PF/PA",
     "Independently recomputed from 137 final scores and matched on all five fields.",
     "confirmed", STAND),
    ("R06", "data/nfl_309921cc/strategies.csv, leaderboard.csv",
     "Strategies presented with a leaderboard",
     "No settled prices exist in that pack, so no strategy could have been graded. The rows "
     "are proposals, not results; the file names imply otherwise.", "mislabelled", W10),
    ("R07", "data/nfl_309921cc/week10_slate.csv", "14 games with status and scores",
     "13 games were unplayed at capture and the Thursday game final; consistent with official page.",
     "confirmed", W10),
    ("R08", "data/nfl_309921cc/correlations.csv", "Correlation values published",
     "Checked whether n accompanied every value; where n was absent the value is "
     "unverifiable from inside the repo. This is an internal consistency finding, not an "
     "external contradiction.", "internal_consistency", ""),
    ("R09", "data/nfl_309921cc/depth_charts.csv", "Depth rows for clubs",
     "The pack labels them unofficial, which matches both club pages read here.",
     "confirmed", NE_DC),
    ("R10", "data/nfl_309921cc/validation_gates.csv", "Gates declared",
     "Gate thresholds are stated but no artefact shows them being applied to a settled sample.",
     "unverifiable", ""),
    ("R11", "data/nfl_309921cc/flagged.csv", "Flags raised",
     "The flags correctly identify unofficial depth and missing prices; they omit the "
     "injury-field gaps found at R01-R03.", "incomplete", INJ),
    ("R12", "data/nfl_origination/week10_slate_and_lines.csv", "Market columns present but blank",
     "Consistent with the claim that no licensed prices were held. Not an error, but not "
     "officially checkable either: it asserts an absence.", "internal_consistency", ""),
]

LEDGER = [
    ("L01", "Which operator supplies the reference price?",
     "DraftKings, chosen because it is the only operator with an open/close pair for all 14 games.",
     "Reversible: the store keeps provider on every row.", "F4-F16"),
    ("L02", "Record a not-yet-settled quote as a close?", "No. It is stored as not_final and "
     "never graded.", "Reversible when the game settles and the close is re-read.", "F4-F02"),
    ("L03", "Publish an empty leaderboard?", "Yes, with the failing gates on every row.",
     "Reversible; S01 offers the alternative.", "F4-F03"),
    ("L04", "Estimate home-field advantage?", "No. Declared 0.0 and flagged.", "Reversible.", "F4-F01"),
    ("L05", "Infer overtime from the final margin?", "No. Left blank.", "Reversible with a play-by-play source.", "F4-F04"),
    ("L06", "Correct the injury rosters that look wrong versus 2025?", "No. Recorded as published.",
     "Reversible only with a published correction.", "F4-F07"),
    ("L07", "Treat club depth charts as verified?", "No. verified_unofficial_source.",
     "Reversible if an official feed is found.", "F4-F08"),
    ("L08", "Compute a correlation without an official input?", "No. Published as uncomputable.",
     "Reversible when the input exists.", "F4-F12"),
    ("L09", "Fill the other 30 clubs' depth from rosters?", "No.", "Reversible by reading the charts.", "F4-F11"),
    ("L10", "Blend DraftKings and FanDuel prices?", "No. Separate provider columns.",
     "Reversible, but a consensus rule would have to be declared first.", "F4-F16"),
    ("L11", "Price prop combos from assumptions?", "No. Blocked at G5.",
     "Reversible with official player stats.", "F4-F18"),
    ("L12", "Publish a staking score with two bets?", "Yes, with a luck p-value attached and no promotion.",
     "Reversible.", "F4-F17"),
]


def write(name: str, fields, rows) -> None:
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(fields)
        for r in rows:
            w.writerow(r)


def main() -> None:
    write("sources.csv",
          ["s_id", "publisher", "title", "url", "supports", "not_supports", "read_date"],
          [(a, b, c, d, e, f, DATE) for a, b, c, d, e, f in SOURCES])
    write("flagged.csv",
          ["f_id", "area", "issue", "severity", "handling", "source_url"],
          [(a, b, c, d, e, f) for a, b, c, d, e, f in FLAGGED])
    write("questions.csv",
          ["q_id", "question", "answer", "status", "how_to_close"],
          QUESTIONS)
    write("suggestions.csv",
          ["s_id", "suggestion", "why", "options", "cost", "risk", "recommendation", "state"],
          SUGGESTIONS)
    write("repo_review.csv",
          ["f_id", "file", "claim", "official", "verdict", "source_url"],
          REPO_REVIEW)
    write("decision_ledger.csv",
          ["l_id", "decision", "choice", "reversibility", "flag_ref"],
          LEDGER)


if __name__ == "__main__":
    main()
