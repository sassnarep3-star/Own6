# NFL research and decision-support system — consolidated executive summary

**Session:** `arena/44136693-own6` · **Read date of every official source below:** 2026-11-13
**Live section:** <https://sassnarep3-star.github.io/Own6/docs/nfl-review/>
**Audit record:** `audit/NFL_REVIEW_2026_11_13.md` · **Verification ledger:** `data/nfl_review/value_reconciliation.csv`

---

## 1. What was asked, and what this is

The brief asked for an NFL research and decision-support system that reviews the repository line by line
against official sources, publishes a readable dashboard with an executive summary, keeps a ranked
Suggestions list for review before anything is implemented, answers the decision-readiness questions
(including what is still missing and how to obtain it), originates NFL lines, investigates signals
across single bets, parlays, player props and prop combinations, runs strategies as a leaderboard
competition with rewards, forces every strategy through validation gates, calculates correlations where
evidence supports it, reduces luck with defensible statistics, tracks injuries and offensive and
defensive depth deficiencies including second-, third- and fourth-string replacements, and runs
automatically with no manual input.

This summary is the consolidated answer. It covers all four NFL packs in this repository
(`docs/nfl/`, `docs/nfl-3b81013c/`, `docs/nfl-origination/`, `docs/nfl/lab/`) and adds one canonical
review surface, `docs/nfl-review/`, that reconciles every published number against a fresh official read.

**The honest headline:** the system is complete as a *research and decision* system and empty as a
*profitable-strategy* system. Twenty-seven strategies are registered across the packs, zero have passed
their gates, zero are on a leaderboard, and no profitability is claimed anywhere. That is the correct
result of the validation rules the brief itself requires, not a defect.

---

## 2. What was verified, and how

| Evidence | Count | What it means |
|---|---|---|
| Official pages read in this session | 18 | Standings, Week 10 schedule, the official league injury report, four NFL news items, the CBA summary, the 2026 rulebook, the terms of use, the betting-partner policy, the NIST confidence-interval page, and the upstream community repository plus its archive |
| Published values compared line by line | 496 | One ledger row per published claim, each with the published value, the official value read, and a result |
| Results: match | 455 | The published value equals the official read |
| Results: differs | 34 | The published value and the official read disagree — flagged, not silently corrected |
| Results: not checked | 0 | Every compared cell had an official counterpart to read |
| Results: not found in the capture | 6 | The named player does not appear in the official report |
| Results: no player named | 1 | The published row names no player, so nothing can be confirmed for it |
| Irregularities logged | 20 | Each published on the Flagged for Review page with its source and the requested action |
| Depth-deficiency indices | 0 of 32 filled | No official source publishes depth order plus snap share, so every value stays blank |

The ledger covers both published standings registers — the through-Week-9 snapshot
(`data/nfl_origination/verified_standings_2026_w10.csv`) and the live snapshot
(`data/nfl_origination/standings_live_2026_11_13.csv`) that the concurrently merged live-verification
session added — plus the published Week 10 slate, the two published injury registers and the depth
chains. Every one of the 496 rows is a cell that exists in a published file; nothing was sampled.

The distinction that matters: **a source link is not verification.** The ledger records the value that was
read from the official page on 2026-11-13, not the presence of a hyperlink, not an internal consistency
check and not a recomputation. Where a published claim was wrong, it is reported as `differs` and left
in place for the owning session to fix.

### The three findings that change decisions

1. **The open lines-lab PR (#68) is reproducible, and its data still has no licence.** The dataset's
   SHA-256 `9fe5bd67210691255cf90af21e39cc242b606f253dbc65198b7915565ce83090` was reproduced
   **exactly** from the upstream commit `6ea0be6dd9bfc95c818c05568753bc70f1986ea2` by filtering
   `game_type == REG` and `season >= 2015`, selecting the recorded 24 columns and writing CRLF CSV.
   Six of the seven provenance checks pass. The seventh does not: the upstream repository declares **no
   licence** (GitHub API `license: null`, no licence file in the archive root). Byte identity proves the
   transformation; it does not prove row accuracy, price quality, predictive value, or the right to
   redistribute. The dataset may be used as a private prototype. It may not be published as a first-party
   source, and every figure derived from it must carry the community-data label.
2. **The community backtest does not show an edge.** The lines lab reports 2025 holdout ROI of
   approximately −1.22 %, −3.69 % and −7.50 % for its three testable candidates, and every interval
   includes zero. Nothing is described as profitable, and the leaderboard stays empty by design.
3. **The published Week 10 slate matches the official schedule on every checked cell.** All fourteen
   games now resolve to an official matchup row by club name: date, kickoff, both records and the
   broadcast network match, and the Washington–New York Thursday game carries the final 24–21 score
   from the official page. The two published snapshot generations disagree with each other on the two
   clubs affected by that game, and the live snapshot is the one that agrees with the official read.
4. **A published pack contradicts the official report on several high-profile players.** The official
   Week 10 league injury report read on 2026-11-13 shows Jaxon Smith-Njigba, Christian McCaffrey and
   Dre Greenlaw at full or limited participation with no game designation, and Joey Porter Jr. did not
   participate. A secondary pack carries different statuses for the same players. The legacy rows are
   **not** republished as current anywhere in this section; they are reconciled and flagged.

---

## 3. The dashboard

Nine pages, generated from the committed registers by `scripts/build_nfl_review.py` and gated by
`scripts/check_nfl_review.py`. No page contains a single input element: collection and generation run
automatically.

| Page | What it answers |
|---|---|
| `index.html` | Where everything is, and how the four packs fit together |
| `requirements.html` | All 16 requirements from the brief, where each is addressed, and whether it is answered today |
| `questions.html` | 16 decision questions: what is known, what is missing, the current answer, and the discovery step that closes the gap |
| `suggestions.html` | 18 ranked proposals with the decision each requires, plus three candidate paths — **proposals only, none implemented** |
| `strategies.html` | 27 strategies, three gate sets, the correlation position and the empty leaderboard |
| `injuries.html` | The full official Week 10 report (326 player rows, all 28 clubs) and the depth status of all 32 clubs |
| `verification.html` | The 496-row ledger and the seven PR #68 provenance checks |
| `flagged.html` | The 20 irregularities with source, severity and requested action |
| `sources.html` | The 18 official pages read, what each supports and what it does not |

Every published table row carries at least one `https` link to the source it came from. The gate fails
the build if a row has no link, a cell contains a placeholder, a table row has the wrong number of
cells, a relative link does not resolve, or an input element appears.

---

## 4. Where the brief is answered, and where it is not

| Requirement | State today |
|---|---|
| Line-by-line review with official sources and review links | **Answered.** 496-row ledger, 18 source reads, 9 linked pages, 20 logged irregularities |
| Dashboard with landing page, subpages, tables, analysis, findings, executive summary | **Answered.** Nine generated pages plus this summary |
| Dedicated Suggestions section, review before implementation | **Answered.** 18 ranked proposals, every one marked `proposed_not_implemented`; the repository contains no auto-implemented suggestion |
| Requirements register and decision-readiness Q&A with discovery steps | **Answered.** 16 requirements and 16 questions, each with a concrete discovery step |
| Originate NFL lines | **Partially answered.** 14 model lines are computed from official standings in the Week 10 pack, and the lines lab originates model expectations from a community game log. No market price was ever confirmed, so every market cell is blank |
| Signals across singles, parlays, player props, prop combinations | **Answered as a specification.** All four families are registered with a frozen method. Only the community-data lab computes joint dependence, and its cross-game interval includes zero |
| Leaderboard competition with rewards for top performers | **Answered as a design; empty in fact.** Ranking metric, qualification rule, tie-break and reward are written down in advance. Zero strategies qualify, so no reward can be allocated. Rewards are non-monetary |
| Every strategy passes validation gates | **Answered.** Three gate sets (10 + 12 + 8 gates). Every gate is open; none has passed |
| Correlation where evidence supports it | **Answered with a limit.** Only the community-data lab contains measured coefficients; they are labelled as computed on non-official data. Every correlation value in the three official-source packs is blank |
| Reduce luck: out-of-sample, intervals, clustering, multiple-testing correction, calibration, proper scoring | **Answered as a method; not yet evaluated.** The methods are specified and the tests are runnable, but there is no verified price series, so every interval is empty. Luck is reduced, never eliminated — the site says so in the same words as NIST |
| Track injuries and offensive/defensive depth deficiencies including 2nd, 3rd and 4th string | **Partially answered.** Availability is tracked from the official report for all 28 playing clubs. The deficiency index stays blank for all 32 clubs because no official source publishes depth order together with snap share |
| No manual user input | **Answered.** Zero input elements across the section; the capture and build are automated |
| Blank and flagged where unconfirmed | **Answered.** Blank means *not confirmed from an official source*, and every blank is explained on the page |
| Every published row has an official source link | **Answered and enforced in CI** |

---

## 5. What is missing, and how to close it

| Missing input | How to obtain it | Who must act |
|---|---|---|
| A licensed historical game and price series | Ask the upstream author for a licence, or replace the rows with a licensed feed | Repository owner + rights holder |
| Official depth order per club | Capture each club's official depth-chart page (8 of 32 are captured) and record the published order | Repository owner, per club |
| Official snap share or efficiency data | No official source exists; the league's next-gen-stats programme is the only plausible route | Repository owner, with a licensed partner |
| A market price source | Obtain a licensed feed and record every price with its timestamp | Repository owner, with a licensed partner |
| Written consent for systematic retrieval | NFL.com's terms restrict systematic retrieval without prior written consent | Repository owner, with counsel |

Until the first three exist, the correct statement about this project is *what is known, from where, and
what is still missing* — which is exactly what the questions page publishes.

---

## 6. Decisions requested

1. **Choose a path from the Suggestions page.** Path A (verification first) is the recommended one:
   close the licence and price gaps before adding any strategy. Path B consolidates the four packs into
   one surface. Path C runs empirical work first on non-official data.
2. **Approve or reject the leaderboard thresholds.** The qualification rule, tie-break and reward are
   written down but need the owner's written approval before any result is computed against them.
3. **Decide the licence position on the community dataset.** It is currently used and labelled, never
   published as first-party evidence.
4. **Direct the four logged corrections** to the owning sessions (`NFLR-REQ-01` to `NFLR-REQ-04` in
   `COORDINATION.md`). Two of them — the 404 rules URL and the redirecting terms URL — were independently
   confirmed as live defects before this session began and remain open.

---

## 7. Standing limits

- Statistical validation reduces the influence of luck; it cannot remove it. NIST is explicit that a
  95 % confidence interval does not mean there is a 95 % probability that the interval contains the true
  mean. Every interval in this project is reported with its cluster count and stays empty until a
  verified price exists.
- No number on any page was inferred from a link, a checksum or a passing test. Every published figure
  is either read from the official page linked on that row, or labelled as a computation from data
  committed in this repository.
- NFL.com's terms of use, the league's betting-partner integrity policy and the CBA are read directly.
  Their applicability to any commercial or wagering use is flagged for qualified counsel; it is not
  asserted here. NFL.com has stated that the league finds injury- and officiating-linked wagers
  objectionable, which is disclosed on the injuries page.
- The lines-lab dataset is community-compiled and unlicensed. It is reproduced exactly, labelled
  everywhere, and excluded from any first-party claim.
