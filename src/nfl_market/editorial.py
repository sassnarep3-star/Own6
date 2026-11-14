"""Editorial content: sources, flags, decision ledger, suggestions, repo review.

Everything here is either
  (a) a verbatim transcription of an official page read in this capture, or
  (b) a statement about this repository that can be checked with ``git`` and
      the files named, or
  (c) an open question or an option set for the owner to choose from.

Nothing here asserts a market fact that is not in ``capture.py``.
"""

from __future__ import annotations

from . import capture as C

CAPTURE_DATE = C.CAPTURE_DATE

# ---------------------------------------------------------------- sources.csv
# (source_id, publisher, title, url, what_it_supports, boundary, verbatim_quote_or_blank)
SOURCES = [
    (
        "NM-S01",
        "National Football League",
        "2026 NFL Division Standings",
        "https://www.nfl.com/standings/",
        "W, L, T, PF, PA for all 32 clubs; the base for every team rating.",
        "Season-to-date aggregate only. No per-game data, no opponent strength, no pace.",
        "",
    ),
    (
        "NM-S02",
        "National Football League",
        "NFL schedule by week, 2026 regular season (weeks 1-10)",
        "https://www.nfl.com/schedules/2026/by-week/week-1",
        "Final scores for 137 games; the verified results feed.",
        "Final scores only. No box score, no drive data, no line, no total. Weeks 2-10 use the "
        "same URL pattern with the number replaced.",
        "",
    ),
    (
        "NM-S03",
        "National Football League",
        "Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season",
        "https://www.nfl.com/injuries/",
        "Practice status and game status (Out / Questionable) for every listed player.",
        "Only the clubs whose Week 10 game block rendered were captured (WAS, NYG, NE, DET, KC "
        "partial). Designations change up to kickoff; this is a single snapshot on 2026-11-14.",
        "",
    ),
    (
        "NM-S04",
        "New England Patriots (official club site)",
        "New England Patriots Unofficial Depth Chart",
        "https://www.patriots.com/team/depth-chart",
        "1st-4th string ordering for every offensive and defensive slot.",
        "The page calls itself unofficial and says it reflects club writers' opinions. It is not a "
        "coach's depth chart.",
        "The 2026 depth chart is unofficial and is published by the writers of Patriots.com. The "
        "depth chart reflects the opinions of the Patriots.com writers and don't necessarily "
        "reflect those of the organization.",
    ),
    (
        "NM-S05",
        "Detroit Lions (official club site)",
        "2026 Lions Depth Chart",
        "https://www.detroitlions.com/team/depth-chart",
        "1st-3rd string ordering for every offensive and defensive slot.",
        "Compiled by Lions Football Communications; labelled unofficial in the page title.",
        "2026 Unofficial Depth Chart Compiled by Lions Football Communications",
    ),
    (
        "NM-S06",
        "NFL Enterprises, LLC",
        "NFL.com Terms and Conditions (Updated: May 16, 2024)",
        "https://www.nfl.com/legal/terms/",
        "The licence boundary for this project: non-commercial, informational, no systematic "
        "retrieval to build a database.",
        "Does not grant redistribution rights. Does not describe any betting data.",
        C.QUOTES["nfl_terms_1_3"],
    ),
    (
        "NM-S07",
        "National Football League",
        "NFL announces official partnerships with three leading sports betting operators",
        "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners",
        "The league's statement that injury- and officiating-tied wagers are in its objectionable "
        "category; constrains which prop families a compliant catalog may contain.",
        "Does not enumerate the restricted markets, and does not publish any price.",
        C.QUOTES["betting_partners_integrity"],
    ),
    (
        "NM-S08",
        "National Football League",
        "nfl.com/odds/ (probed)",
        "https://www.nfl.com/odds/",
        "Establishes the negative: NFL.com serves its 404 page at this path.",
        "A 404 is the whole evidence. It means no official line page is published at this path; it "
        "does not prove no price exists anywhere on nfl.com.",
        "404 - Flag on the Play.",
    ),
    (
        "NM-S09",
        "NFL Football Operations",
        "2026 NFL Rulebook",
        "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
        "Confirms the current official rulebook location for 2026.",
        "Rule text only; no availability, depth or market information.",
        "",
    ),
]

# ---------------------------------------------------------------- flagged.csv
FLAGGED = [
    {
        "flag_id": "NM-F01",
        "severity": "high",
        "area": "Market data",
        "finding": "No official NFL price exists, so the price-snapshot store and the difference "
                   "column are structurally empty.",
        "impact": "No edge can be measured; no strategy can be shown to beat a market; ROI against a "
                  "market is impossible.",
        "what_would_resolve_it": "An official or explicitly licensed odds source, named in the ledger "
                                 "and added to the source registry.",
        "owner_of_the_source": "NFL (no public odds product) or a licensed operator",
        "official_source_url": "https://www.nfl.com/odds/",
        "status": "open",
    },
    {
        "flag_id": "NM-F02",
        "severity": "high",
        "area": "Model",
        "finding": "The originated side went 28-44 (hit rate 0.3889) walking forward over weeks 5-9.",
        "impact": "The side model is worse than a coin flip at this sample. Any strategy built on it "
                  "is harmful until the model changes.",
        "what_would_resolve_it": "A different rating method, validated on a held-out season, or a "
                                 "decision to stop originating the side.",
        "owner_of_the_source": "this project",
        "official_source_url": "https://www.nfl.com/standings/",
        "status": "open",
    },
    {
        "flag_id": "NM-F03",
        "severity": "high",
        "area": "Sample",
        "finding": "Every published number is in-sample. No forward sample exists, so gate G09 cannot "
                   "open and no lifecycle decision can be made.",
        "impact": "Backtest results cannot support a promotion.",
        "what_would_resolve_it": "Time. Freeze the gate set and record 200 forward bets.",
        "owner_of_the_source": "this project",
        "official_source_url": "https://www.nfl.com/schedules",
        "status": "open",
    },
    {
        "flag_id": "NM-F04",
        "severity": "medium",
        "area": "Depth",
        "finding": "Depth charts were captured for 2 of 32 clubs (NE, DET).",
        "impact": "The replacement-depth register is a two-club illustration, not a league-wide signal.",
        "what_would_resolve_it": "Capture the remaining 30 club depth-chart pages.",
        "owner_of_the_source": "the 32 clubs",
        "official_source_url": "https://www.patriots.com/team/depth-chart",
        "status": "open",
    },
    {
        "flag_id": "NM-F05",
        "severity": "medium",
        "area": "Injuries",
        "finding": "The Week 10 injury report was only fully captured for WAS, NYG, NE and DET; the KC "
                   "block was cut off mid-table.",
        "impact": "Injury coverage is partial, and every designation is a single snapshot that can "
                  "change before kickoff.",
        "what_would_resolve_it": "Re-capture the full page and record a capture timestamp per club block.",
        "owner_of_the_source": "NFL",
        "official_source_url": "https://www.nfl.com/injuries/",
        "status": "open",
    },
    {
        "flag_id": "NM-F06",
        "severity": "medium",
        "area": "Method",
        "finding": "The deficiency_points penalty in the depth register is a declared weight that has "
                   "never been validated against outcomes.",
        "impact": "It is a ranking aid, not a measurement. It appears next to real data and could be "
                  "misread as one.",
        "what_would_resolve_it": "Regress depth deficiency on results once 30+ clubs are covered.",
        "owner_of_the_source": "this project",
        "official_source_url": "https://www.nfl.com/standings/",
        "status": "open",
    },
    {
        "flag_id": "NM-F07",
        "severity": "medium",
        "area": "Method",
        "finding": "The pricing model's sigma (13.5), home-field value (2.0) and shrink weight (0.75) are "
                   "declared constants, not fitted parameters.",
        "impact": "The fair lines are reproducible but not calibrated.",
        "what_would_resolve_it": "Fit on a prior season and freeze before the forward test.",
        "owner_of_the_source": "this project",
        "official_source_url": "https://www.nfl.com/standings/",
        "status": "open",
    },
    {
        "flag_id": "NM-F08",
        "severity": "low",
        "area": "Data",
        "finding": "Weeks 1, 3 and 5 on nfl.com render an explicit 'Hidden Score' placeholder in the "
                   "score block, but the game headline carries the score inline.",
        "impact": "Scores were taken from the headline. If the headline and the score block ever "
                  "disagree, the headline wins here and that choice is a human decision, not a fact.",
        "what_would_resolve_it": "Cross-check every score against a second official page (the game "
                                 "centre URL) before the next refresh.",
        "owner_of_the_source": "NFL",
        "official_source_url": "https://www.nfl.com/schedules/2026/by-week/week-1",
        "status": "needs review",
    },
    {
        "flag_id": "NM-F09",
        "severity": "low",
        "area": "Legal",
        "finding": "The NFL terms prohibit systematic retrieval of NFL content to build a database "
                   "without written consent.",
        "impact": "This pack is non-commercial and informational, which the terms permit for the "
                  "personal use clause, but the compiled CSVs are close to the line the terms draw.",
        "what_would_resolve_it": "Owner decision: keep as a private non-commercial archive, or seek "
                                 "written consent before any public/commercial use.",
        "owner_of_the_source": "NFL Enterprises, LLC",
        "official_source_url": "https://www.nfl.com/legal/terms/",
        "status": "open",
    },
    {
        "flag_id": "NM-F10",
        "severity": "low",
        "area": "Correlations",
        "finding": "COR-01 (win pct vs point diff) is near-tautological and is published only as a "
                   "transcription check.",
        "impact": "It should never be quoted as a model finding.",
        "what_would_resolve_it": "Nothing; the label is the mitigation.",
        "owner_of_the_source": "this project",
        "official_source_url": "https://www.nfl.com/standings/",
        "status": "needs review",
    },
    {
        "flag_id": "NM-F11",
        "severity": "low",
        "area": "Schedule",
        "finding": "The Week 10 slate has 14 games and 4 byes (CHI, DEN, PHI, TB). A 17-game, 32-team "
                   "week would normally have 16 games.",
        "impact": "The count is what NFL.com displays; it is transcribed as-is rather than 'corrected'.",
        "what_would_resolve_it": "Re-read the by-week page; if it still shows 14, record the season "
                                 "structure as a known oddity.",
        "owner_of_the_source": "NFL",
        "official_source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "status": "needs review",
    },
]

# -------------------------------------------------------- decision_ledger.csv
# Columns: id, question, category, what_we_know, what_we_do_not_know, why_it_blocks_a_decision,
#          discovery_action, source_or_protocol, status
LEDGER = [
    ("DQ-01", "Does an official, citable NFL line exist for any market?",
     "Market", "NFL.com serves a 404 at /odds/. The terms and the betting-partner release contain no price.",
     "Whether any price exists behind a login, in NFL+ or in an operator feed.",
     "If no citable line exists, the difference column can never be filled, and no strategy can ever be "
     "shown to beat the market.",
     "Probe nfl.com sitemap and search for an odds product page; if none, ask the owner whether a licensed "
     "operator feed is acceptable and record the answer as a scope change.",
     "NM-S08, https://www.nfl.com/odds/", "open"),
    ("DQ-02", "Is the 2026 week structure (14 games, 4 byes in Week 10) correct, or a capture artefact?",
     "Data", "The by-week page lists 14 games plus a 'Teams on Bye' block naming CHI, DEN, PHI, TB.",
     "Whether NFL.com was mid-update when read, or the season genuinely has this shape.",
     "Sample size per week feeds every gate. A wrong week count changes n.",
     "Re-read the same page on a later date and diff; also read nfl.com/schedules/2026 (by team).",
     "https://www.nfl.com/schedules/2026/by-week/week-10", "open"),
    ("DQ-03", "Which depth chart is authoritative when a club page and the injury report disagree?",
     "Injuries", "Club pages list a player who the official injury report rules Out (6 such cases).",
     "Which page the club treats as operative on game day.",
     "The replacement register's 'first available' answer depends on which page wins.",
     "Treat the injury report as authoritative for availability and the depth chart as authoritative for "
     "ordering; record that rule here and apply it mechanically. Done in src/nfl_market/depth.py.",
     "NM-S03 vs NM-S04/NM-S05", "resolved_by_rule"),
    ("DQ-04", "What stake schedule should the ROI column assume?",
     "Staking", "A flat 1-unit stake at -110 is used and labelled.",
     "Whether the owner bets flat, by edge, or by Kelly.",
     "ROI is meaningless without a stake rule; different rules rank strategies differently.",
     "Owner decision. Options in suggestions S-02.",
     "this project", "awaiting_owner_choice"),
    ("DQ-05", "Should the side model be scrapped, refitted, or kept as a control?",
     "Model", "It went 28-44 walking forward.",
     "Whether the failure is the rating method, the sample, or both.",
     "Every downstream strategy inherits this. Keeping it silently would poison the catalog.",
     "Options in suggestions S-01. Until decided, the side is published with its record attached.",
     "this project", "awaiting_owner_choice"),
    ("DQ-06", "What counts as a 'forward' bet for gate G09?",
     "Validation", "The gate requires 200 out-of-sample bets after the gate set is frozen.",
     "Whether a paper bet placed after the freeze but never staked counts.",
     "Without a definition, G09 can be gamed by reclassifying backtest rows.",
     "Define: a forward bet is one whose game was unplayed at the moment the model line was written, "
     "recorded with a timestamp. Options in S-03.",
     "this project", "awaiting_owner_choice"),
    ("DQ-07", "Are same-game parlay legs correlated strongly enough to forbid independent pricing?",
     "Correlation", "Measured r = -0.181 (n=72) between side and total grades; correlation is negative.",
     "Whether the effect holds for player-prop legs, which were not captured.",
     "Parlay pricing maths depends on it; the D5 demotion trigger depends on it.",
     "Recompute after the forward sample; capture prop legs once a prop source exists.",
     "COR-03", "open"),
    ("DQ-08", "Does depth deficiency actually move a line?",
     "Depth", "Deficiency is captured for two clubs; n=0 games of outcome data.",
     "Effect size, and whether 2nd-string is materially worse than 4th-string.",
     "If it does not move a line, the whole depth register is decoration.",
     "Capture 30 more clubs and regress deficiency on result vs the model line over 100+ games.",
     "S-04", "open"),
    ("DQ-09", "What is the legal ceiling on publishing these compiled CSVs?",
     "Legal", "The NFL terms prohibit systematic retrieval to build a database absent consent; personal "
     "non-commercial use is permitted.",
     "Whether a public GitHub Pages site counts as non-commercial informational use in the NFL's view.",
     "If not, the public site must not publish the compiled tables.",
     "Owner decision; options in S-06.",
     "NM-S06", "awaiting_owner_choice"),
    ("DQ-10", "Which of the 32 clubs publish a usable depth chart at all?",
     "Depth", "2 of 2 probed clubs publish one, both labelled unofficial.",
     "Whether the other 30 publish, and in what format.",
     "A league-wide deficiency signal needs uniform coverage.",
     "Probe all 32 club domains once; record which return a chart and which 404.",
     "S-04", "open"),
    ("DQ-11", "How should a push be treated in ROI?",
     "Staking", "Pushes are excluded from the win-rate denominator and the ROI denominator.",
     "Whether the owner prefers push-as-half-loss, push-as-refund, or exclusion.",
     "Different conventions change ROI by a few percent, which is the size of the effect being chased.",
     "Owner decision; the convention is stated on every ROI table. Options in S-05.",
     "this project", "awaiting_owner_choice"),
    ("DQ-12", "Is a 13.5-point sigma for NFL margins still right for 2026?",
     "Model", "It is a declared constant, not fitted.",
     "The realised 2026 margin distribution.",
     "The moneyline probabilities inherit it directly.",
     "Fit sigma on weeks 1-9 and compare; publish both.",
     "https://www.nfl.com/schedules", "open"),
]

# ------------------------------------------------------------ suggestions.csv
# (id, area, title, option_a, option_b, option_c, recommended, rationale, effort, reversible, status)
SUGGESTIONS = [
    ("S-01", "Model", "What to do with the side model that went 28-44",
     "A: Scrap the side entirely and originate only total and moneyline.",
     "B: Replace the points-based rating with an opponent-adjusted rating (e.g. per-play efficiency) "
     "and backtest the replacement on weeks 5-9.",
     "C: Keep the side, publish its record prominently, and treat it as a documented control.",
     "B, with C's transparency as a permanent feature of the page.",
     "The current method averages points for and against with no opponent adjustment, so it double-counts "
     "schedule strength. B is the only option that could fix the mechanism rather than hide it. C alone "
     "leaves a harmful number in the catalog.",
     "medium", "yes", "pending_human_choice"),
    ("S-02", "Staking", "What stake schedule should ROI assume",
     "A: Flat 1 unit at -110 (current).",
     "B: Flat 1 unit at the model's own fair price, i.e. break-even evaluation only.",
     "C: A fractional-Kelly schedule driven by the model's edge.",
     "A stays as the headline, B is added as a second column.",
     "C depends on a calibrated edge, and no edge is measurable without a market line (NM-F01). Shipping "
     "Kelly now would produce confident-looking numbers from an unmeasured quantity.",
     "low", "yes", "pending_human_choice"),
    ("S-03", "Validation", "Define what counts as a forward bet for gate G09",
     "A: Any game unplayed when the model line was written, recorded with a UTC timestamp.",
     "B: Only bets the owner actually placed.",
     "C: Any game from a season week after the gate-set freeze date.",
     "A.",
     "A is the only definition that is both mechanical and independent of the owner's behaviour, so the "
     "gate cannot be opened by reclassifying backtest rows.",
     "low", "yes", "pending_human_choice"),
    ("S-04", "Depth", "Close the 30-club depth-chart gap",
     "A: Probe all 32 club domains for a depth chart and capture every one that exists.",
     "B: Capture only the clubs in the current week's slate.",
     "C: Leave it at two clubs and label it an illustration.",
     "A, once per week.",
     "The deficiency signal is worthless as a two-club anecdote. B is cheaper but creates a rotating "
     "coverage gap that makes week-over-week comparison impossible.",
     "medium", "yes", "pending_human_choice"),
    ("S-05", "Staking", "Choose the push convention",
     "A: Exclude pushes from the denominator (current).",
     "B: Count a push as half a loss.",
     "C: Count a push as a refunded stake, i.e. 0 units but n+1.",
     "A for the hit rate, C for the units column.",
     "A and C together are what a reader intuitively expects: the push is not a win and not a loss. B "
     "quietly biases every ROI downward.",
     "low", "yes", "pending_human_choice"),
    ("S-06", "Legal", "Decide the publication ceiling under the NFL terms",
     "A: Publish aggregate findings and keep the compiled CSVs private.",
     "B: Publish everything as a non-commercial informational archive.",
     "C: Seek written consent from the NFL before publishing the tables.",
     "A.",
     "The terms permit personal non-commercial informational use but prohibit systematic retrieval to "
     "build a database absent consent. A keeps the useful conclusions public while keeping the compiled "
     "database private, which is the lowest-risk reading.",
     "low", "yes", "pending_human_choice"),
    ("S-07", "Site", "Add a weekly diff report",
     "A: A page that diffs this week's numbers against last week's and highlights every change.",
     "B: Rely on git history.",
     "C: No diffing.",
     "A.",
     "The most decision-relevant fact each week is what changed. Git history exists but nobody reads it "
     "while deciding.",
     "low", "yes", "pending_human_choice"),
    ("S-08", "Market", "Resolve the missing-price dead end",
     "A: Accept blank prices permanently and never claim a market edge.",
     "B: Add one licensed operator feed, named and dated, as an explicit exception to the "
     "official-only rule.",
     "C: Use a public closing-line archive, clearly marked non-official.",
     "A now; B only if the owner is willing to change the project's own rule in writing.",
     "Every other choice here is blocked by the missing price. The owner should decide this first, "
     "because it determines whether the whole exercise can ever produce an edge.",
     "high", "no", "pending_human_choice"),
]

# ---------------------------------------------------------------- repo review
REPO_FINDINGS = [
    ("NM-RF-01", "Scope overlap risk", "medium",
     "Five NFL packs already share the repo namespace (data/nfl, nfl_3b81013c, nfl_origination, nfl_wk, "
     "nfl_309921cc) with overlapping subject matter and different numbers for the same Week 10 games.",
     "A reader cannot tell which pack is current. This pack is namespaced nfl_market and linked from the "
     "root index, but the duplication itself is unresolved."),
    ("NM-RF-02", "Duplicate work", "medium",
     "data/nfl_309921cc/week10_slate.csv, data/nfl_origination/week10_slate_and_lines.csv and this "
     "pack's slate_week10.csv all describe the same Week 10 slate.",
     "Three sources of truth for one slate. Only this pack's rows were re-verified on 2026-11-14."),
    ("NM-RF-03", "Stale derived artefacts", "low",
     "scripts/audit_repo.py and the assurance generators depend on each other's output, and prior "
     "sessions note they must be iterated until stable.",
     "This session did not run them; the inventories under data/assurance may not include this pack."),
    ("NM-RF-04", "Generated HTML in git", "low",
     "docs/ contains ~166 generated HTML pages across all packs.",
     "Large, review-noisy diffs, and every generator change rewrites many files. Acceptable for GitHub "
     "Pages but worth naming."),
    ("NM-RF-05", "Open PR backlog", "medium",
     "Five PRs were open at claim time (#84, #79, #72, #68, #56 and older).",
     "Unmerged branches carry alternative NFL numbers. Merging them later would create contradictory "
     "tables under one site."),
    ("NM-RF-06", "CI breadth", "low",
     "There are 13 workflow files, several of which run repo-wide audits.",
     "A change to shared generated data can fail unrelated workflows. This pack adds one self-contained "
     "workflow to avoid that coupling."),
]


def write_pages(page, table, write_csv, data_dir):
    """Write the editorial CSVs and the five editorial pages."""
    # sources.csv
    src_rows = []
    for sid, pub, title, url, supports, boundary, quote in SOURCES:
        src_rows.append(
            {
                "source_id": sid,
                "publisher": pub,
                "title": title,
                "official_source_url": url,
                "verification_status": "verified_direct_fetch",
                "retrieved_utc": CAPTURE_DATE,
                "supports_claim": supports,
                "does_not_support_boundary": boundary,
                "verbatim_evidence_excerpt": quote,
            }
        )
    write_csv("sources.csv", src_rows)

    write_csv("flagged.csv", FLAGGED)

    led_rows = []
    for r in LEDGER:
        led_rows.append(
            {
                "id": r[0], "question": r[1], "category": r[2], "what_we_know": r[3],
                "what_we_do_not_know": r[4], "why_it_blocks_a_decision": r[5],
                "discovery_action": r[6], "source_or_protocol": r[7], "status": r[8],
            }
        )
    write_csv("decision_ledger.csv", led_rows)

    sug_rows = []
    for r in SUGGESTIONS:
        sug_rows.append(
            {
                "id": r[0], "area": r[1], "title": r[2], "option_a": r[3], "option_b": r[4],
                "option_c": r[5], "recommended": r[6], "rationale": r[7], "effort": r[8],
                "reversible": r[9], "status": r[10],
                "decision_owner": "repository owner",
            }
        )
    write_csv("suggestions.csv", sug_rows)

    rep_rows = []
    for r in REPO_FINDINGS:
        rep_rows.append(
            {"finding_id": r[0], "area": r[1], "severity": r[2], "finding": r[3], "why_it_matters": r[4]}
        )
    write_csv("repo_findings.csv", rep_rows)

    # ---------------- pages
    # sources
    body = ("<p class=\"lede\">Every source read in this capture, with what it does and does not "
            "support. All were fetched directly on %s.</p>" % CAPTURE_DATE)
    body += table(["source_id", "publisher", "title", "official_source_url", "verification_status",
                   "supports_claim", "does_not_support_boundary", "verbatim_evidence_excerpt"],
                  src_rows, status_cols=("verification_status",), link_cols=("official_source_url",),
                  maxlen=300)
    page("sources.html", "Sources read in this capture", body)

    # flagged
    body = ("<p class=\"lede\">Everything that could not be confirmed, or that is a declared guess, is "
            "here with the source link needed to review it. None of these blocked publication.</p>")
    body += table(["flag_id", "severity", "area", "finding", "impact", "what_would_resolve_it",
                   "official_source_url", "status"],
                  FLAGGED, status_cols=("status",), link_cols=("official_source_url",), maxlen=260)
    page("flagged.html", "Flagged for review", body)

    # decision ledger
    body = ("<p class=\"lede\">The questions that must be answered before any decision is reasonable, "
            "split into what we know, what we do not, and how to find out. Five of these need an owner "
            "choice; the rest need data collection or time.</p>")
    body += table(["id", "category", "question", "what_we_know", "what_we_do_not_know",
                   "why_it_blocks_a_decision", "discovery_action", "status"],
                  led_rows, status_cols=("status",), maxlen=300)
    body += ("<h2>Read in this order</h2><ol>"
             "<li><strong>DQ-01 / S-08</strong> &mdash; is there ever going to be a price? Everything "
             "about measuring an edge depends on it.</li>"
             "<li><strong>DQ-05 / S-01</strong> &mdash; is the side model fixable or dead?</li>"
             "<li><strong>DQ-06 / S-03</strong> &mdash; lock the forward-bet definition before any "
             "forward bet is recorded, or the sample will be unusable.</li>"
             "<li><strong>DQ-09 / S-06</strong> &mdash; the publication ceiling.</li>"
             "</ol>")
    page("decision-ledger.html", "Decision questions", body)

    # suggestions
    body = ("<p class=\"lede\">Nothing on this page has been implemented. Each row is an option set with "
            "a recommendation and the reason for it, so a reviewer can accept, reject or replace the "
            "recommendation. Every row is <code>pending_human_choice</code>.</p>")
    body += table(["id", "area", "title", "option_a", "option_b", "option_c", "recommended",
                   "rationale", "effort", "reversible", "status"],
                  sug_rows, status_cols=("status",), maxlen=320)
    body += ("<h2>The three that unblock the most</h2><ol>"
             "<li><strong>S-08</strong> &mdash; the missing-price decision. It gates every market claim.</li>"
             "<li><strong>S-01</strong> &mdash; what happens to the 28-44 side model.</li>"
             "<li><strong>S-03</strong> &mdash; the forward-bet definition, which must exist before the "
             "forward sample starts accumulating.</li>"
             "</ol>")
    page("suggestions.html", "Suggestions for review", body)

    # repo review
    body = ("<p class=\"lede\">A line-by-line read of the repository as it stood at base commit "
            "<code>36c6f84</code>, limited to irregularities that affect this pack or the site.</p>")
    body += table(["finding_id", "area", "severity", "finding", "why_it_matters"], rep_rows, maxlen=400)
    body += ("<h2>What was checked by hand</h2><ul>"
             "<li>All 24 <code>data/nfl*</code> CSV headers, to confirm the new <code>nfl_market</code> "
             "namespace does not collide.</li>"
             "<li>All 5 existing <code>docs/nfl*</code> directories, to confirm no path is reused.</li>"
             "<li><code>git log</code>, <code>git ls-remote --heads origin</code> and "
             "<code>gh pr list --state open</code> at claim time.</li>"
             "<li>Every claim on every page of this pack, checked against "
             "<code>data/nfl_market/sources.csv</code>.</li></ul>")
    body += "<h2>What was not checked</h2><ul><li>The contents of the other NFL packs' numeric tables, " \
            "beyond their headers and row counts.</li><li>Anything requiring credentials or a " \
            "third-party data feed.</li></ul>"
    page("repo-review.html", "Repository review", body)
