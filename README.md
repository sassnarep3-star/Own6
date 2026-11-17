# Own6 — NFL Decision & Research Dashboard

An evidence-first research repository with an NFL line-origination and validation program, plus preserved NBA and San Francisco housing research. The NFL site organizes requirements, decision questions, source records, injury/depth context, line methods, single/parlay/player-prop strategy hypotheses, correlation methods, validation gates, suggestions, and review flags. **Nothing in this repository demonstrates a profitable NFL edge.** Model calculations are not market prices, and unverified facts remain blank or explicitly marked as computed/unverified.

## Start here

- **Live NFL landing page:** https://sassnarep3-star.github.io/Own6/ — no-input overview with clear links to the decision tools, workspaces, suggestions, and Flagged for Review.
- **Main NFL Origination dashboard:** [`docs/nfl-origination/index.html`](docs/nfl-origination/index.html) — the 12-gate research framework and 10 preregistered strategy candidates.
- **Decision-readiness and evidence pack (e5e38f9e):** [`docs/nfl-e5e38f9e/index.html`](docs/nfl-e5e38f9e/index.html) — one row per brief requirement with its blocking gate, the Week 10 official-score reconciliation across packs, the Week 10 injury spot-check, questions, suggestions, and Flagged for Review. No edge or profit is shown.
- **Suggestions (review before project changes):** [`docs/nfl-origination/suggestions.html`](docs/nfl-origination/suggestions.html)
- **Flagged for Review:** [`docs/nfl-origination/flagged.html`](docs/nfl-origination/flagged.html)
- **NFL executive summary:** [`docs/nfl-origination/executive-summary.html`](docs/nfl-origination/executive-summary.html)
- **Additional self-contained NFL Week pack:** [`docs/nfl-wk/index.html`](docs/nfl-wk/index.html) — separate input snapshots and quarantined strategy candidates; not combined with the main leaderboard.
- **Decision desk (session `67233566`):** [`docs/nfl-67233566/index.html`](docs/nfl-67233566/index.html) — 145 finished games reconciled 220-for-220 against the official standings and card badges, a hash-chained opening/closing ledger for the lines we originate, a 12-strategy signal leaderboard ranked on proper scores with a game-cluster lower bound and a multiplicity adjustment, availability floors per position group, and one table per requirement naming the gate that blocks it. Market prices stay blank by written policy because no official page in the evidence set prints one.
- **Week-10 settlement & settled leaderboard (session `45abd396`, 2026-11-17):** [`docs/nfl-45abd396/index.html`](docs/nfl-45abd396/index.html) — the first *settled* leaderboard in this repository. Week 10 has 13 of 14 cards final on the official schedule page, so the 48 pre-kickoff forecasts already in the repo (five strategies, four files) were settled against the official finals, each traced to the commit that published it. Four rows were committed **after** their game kicked off and are excluded. Every strategy shows positive point-estimate Brier skill against the same-games climatology, and **none qualifies**: every 95% game-cluster interval contains zero at n = 12, and no hit count clears the Šidák-adjusted level for m = 5 strategies. Also: 347 injury rows across 28 clubs at a new clock (2026-11-17T00:47Z) with zero designation movement between reads, 25 November reserve entries (14 of them absent from the weekly report), 12 trades checked for stale depth (one mismatch), 16 questions with discovery routes, 10 reviewable suggestions and 14 gates. No market price exists, so no ROI, CLV or staking column is published. One published Week-10 forecast row was found to have been **deleted** from its file after publication (commit `c0eb6ef`); it is republished from its own commit for review, is excluded from every score, and is flagged F-13.
- **Other research domains:** [NBA assurance](docs/assurance/index.html) · [all sections hub](docs/index.html)

The repository root now opens an NFL-focused portal. The separate `docs/` dashboard and NBA, NFL, and housing research packs remain available; they have separate evidence boundaries and should not be read as multiple independent performance records.

## NFL evidence state

- **Qualification:** the Origination leaderboard has 10 preregistered candidates and 0 qualified strategies; it remains empty until authorized timestamped market/outcome data and every validation artifact exist. This is not evidence of an edge or profitability. See the [leaderboard specification](data/nfl_origination/strategies_leaderboard.csv), [validation gates](data/nfl_origination/validation_gates.csv), and [official NFL data-partner information](https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners).
- **Current values:** market prices, NFL fair-line calibration, ROI, CLV, player-prop results, and measured parlay/prop correlations are blank where unverified. A separate worked-line page contains computations from explicitly uncalibrated assumptions, not market quotes or a verified edge. Review the [worked lines](docs/nfl-3b81013c/lines.html) and the [NFL terms page](https://www.nfl.com/legal/terms/) before any data-use conclusion; public availability alone does not establish usage rights.
- **Dated source review:** PR #77 records direct reads of NFL standings, Week 10 schedule and injury report on 2026-11-13; the resulting [standings snapshot](data/nfl_origination/standings_live_2026_11_13.csv) contains 32 clubs and the [injury/depth reconciliation](data/nfl_origination/live_check_2026_11_13.csv) contains 102 named checks. The review recorded the Thursday final as WAS 24–NYG 21 and standings totals as 136 W / 136 L / 2 T, 6,291 PF = PA. These are dated snapshot facts from that prior review, not a live feed or a new verification by this README edit. See the [official NFL standings](https://www.nfl.com/standings/division/2026/reg), [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10), [injury report](https://www.nfl.com/injuries/), [13 Nov reconciliation record](audit/NFL_LIVE_REVERIFICATION_2026_11_13.md), and [PR #77](https://github.com/sassnarep3-star/Own6/pull/77).
- **Review items:** 25 rows are present in the Origination Flagged for Review register. The four bye clubs were confirmed by the later official schedule review, but remain packed into one irregular row; NFL-F25 records that a cited rule-change page showed 2025 content. The older 2017 injury-policy PDF is reported as 404, so unsupported policy timing/cadence claims stay unverified. See [Flagged for Review](docs/nfl-origination/flagged.html), the [NFL Lab flags](docs/nfl/flagged.html), and [COORDINATION.md](COORDINATION.md).
- **Suggestions:** the main Origination register has 14 proposals and the separate NFL Week pack has 19; both are review-only, not auto-implemented. `SUG-01` still describes the former root redirect and needs its owner to reconcile the current site state. Review [Origination suggestions](docs/nfl-origination/suggestions.html) and [NFL Week suggestions](docs/nfl-wk/suggestions.html) before proposing further project changes.
- **Repository-wide audit:** the [source-coverage ledger](audit/SOURCE_COVERAGE.md) measures reference-link coverage, not factual correctness. A URL, passing test, checksum, model calculation, or source register status is not by itself proof that a linked source supports every claim.

## Preserved NBA assurance archives

Earlier NBA research and its assurance artifacts remain available as a separate project area. Their zero-observation, data-rights, verification-ledger and historical-snapshot claims apply to the NBA artifacts only; they are not NFL evidence. Start with the [NBA assurance dashboard](docs/assurance/index.html), [NBA verification ledger](docs/verify/index.html), [NBA research summary](EXECUTIVE_SUMMARY.md), and [legacy row audit](data/assurance/row_audit.csv). GitHub Pages serves the NFL-focused portal from the repository root; [`docs/`](docs/index.html) retains the older multi-section site.


## Historical NBA snapshot — 5 November 2026 (`docs/daily/`)

A dated, official-source snapshot with its own checker: 121 committed final scores reconciled
30/30 to today's `nba.com/standings` **and** 30/30 to the previous 3 November snapshot; the 14
4 November games re-read one card at a time; an 11-game forward slate (5–6 November) with model
line estimates and deliberately **blank** market cells; a luck-controlled walk-forward signal test
(61 games, McNemar plus bootstrap); and a Flagged-for-Review page. Live:
https://sassnarep3-star.github.io/Own6/docs/daily/

Build and check: `python3 scripts/daily_analysis.py` · `python3 scripts/build_daily.py` ·
`python3 scripts/check_daily.py` · `python3 -m unittest discover -s tests -p test_daily.py`.
Per-row verification record: [`audit/SESSION_27fdbe09.md`](audit/SESSION_27fdbe09.md).

## NBA archive sources and evidence boundaries
Official NBA sources used for metric definitions: [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) and [NBA Inside the Game Stat Glossary](https://www.nba.com/news/inside-the-game-stat-glossary). These sources do **not** verify predictive value, odds, correlation estimates or profitability. Unconfirmed values must remain blank and be flagged.

The repository does contain historical legacy CSV/JSON archives and earlier dashboards. Those are **not** the authorized empirical ledger. The current assurance review leaves their numeric values unverified unless separately matched to an authorized official snapshot. Internal consistency checks are not official-source verification.

## NBA assurance methods preserved

- Fair American odds conversion no longer invents a margin.
- Strategy/market identity, frozen edge and conservative EV thresholds are enforced.
- Audit evidence requires reviewer, artifact URL/hash, scope, config hash and ledger hash; a boolean alone is rejected.
- CLV uses de-vigged same-line closing probabilities; moved lines stay blank and block the CLV gate.
- Correlations use strict training-only paired residuals, retain zeros, and require slate-clustered intervals and joint samples for combos.
- Bonferroni covers the actual qualification statistics across the frozen candidate family; the independent-trial win-count test is diagnostic only.
- The leaderboard ranks only all-gate qualifiers by the lower bound of slate-clustered holdout ROI. Rewards are non-monetary research priority only.

## Reproduce the NBA assurance artifacts

```sh
python -m pip install -r requirements-empirical.txt
python scripts/audit_repo.py
python scripts/run_lab.py
python scripts/build_assurance.py
python scripts/check_assurance.py
python -m pytest -q tests
```

The empty ledger deterministically reports `not_run`, zero observations and an empty leaderboard. Synthetic fixtures are confined to tests and never enter the report.

## Preserved archives

- Data hub: [`docs/hub/index.html`](docs/hub/index.html)
- Earlier repaired landing: [`docs/index.html`](docs/index.html)
- Fail-closed empirical lab: [`docs/lab/overview.html`](docs/lab/overview.html)
- Source-linked verified section: [`docs/verified/index.html`](docs/verified/index.html)
- Research sub-site: [`docs/own6/index.html`](docs/own6/index.html)
- Independent review: [`docs/review/index.html`](docs/review/index.html)

These archives are preserved for provenance. Their historical claims are not promoted to verified facts by the assurance dashboard.

## Coordination

Concurrent sessions are coordinated in [`COORDINATION.md`](COORDINATION.md). Each session's fixed Arena branch, file scope, source trail, verification performed, and irregularities are recorded there. Shared tables and navigation are changed only by the integration owner; flagged items remain visible on a **Flagged for Review** page and do not block publication of the research framework.

## No betting advice

Analytics research only. No wagers, stakes, picks, payouts or profitability claims. Luck cannot be eliminated; the protocol reduces false discoveries through rights, provenance, chronology, dependence-aware uncertainty, multiplicity control and frozen preregistration.

## NFL Lab — originate your own NFL lines (added 2026-11-12)

A fully additive NFL research lab covering requirement traceability (R01–R18), decision-readiness questions (Q01–Q10) with discovery paths, a suggestions review section (S01–S12) that must be reviewed before changes, ten frozen signal strategies for singles/parlays/player-prop combos (N01–N10), own-line methods, ten validation gates (G01–G10), correlation pairs, and offensive/defensive injury-depth review through fourth-string replacements. Its source-linked rows are not all fresh or value-verified; the source register records read dates and limits, unconfirmed values stay blank, and nothing establishes profitability.

- **Live section:** https://sassnarep3-star.github.io/Own6/docs/nfl/ (`docs/nfl/index.html`)
- **Start here:** [`docs/nfl/index.html`](docs/nfl/index.html) → [`research/NFL_EXECUTIVE_SUMMARY.md`](research/NFL_EXECUTIVE_SUMMARY.md)
- **Requirements:** [`data/nfl/requirements.csv`](data/nfl/requirements.csv) · [`research/NFL_REQUIREMENTS.md`](research/NFL_REQUIREMENTS.md)
- **Decision framework:** [`data/nfl/decision_questions.csv`](data/nfl/decision_questions.csv) → [`docs/nfl/questions.html`](docs/nfl/questions.html)
- **Suggestions (review only):** [`data/nfl/suggestions.csv`](data/nfl/suggestions.csv) → [`docs/nfl/suggestions.html`](docs/nfl/suggestions.html)
- **Strategies & own lines:** [`data/nfl/origin_strategies.csv`](data/nfl/origin_strategies.csv) · [`research/NFL_SIGNALS.md`](research/NFL_SIGNALS.md)
- **Validation & correlations:** [`data/nfl/validation_gates.csv`](data/nfl/validation_gates.csv) · [`research/NFL_VALIDATION.md`](research/NFL_VALIDATION.md)
- **Injury & depth:** [`data/nfl/injury_tracking.csv`](data/nfl/injury_tracking.csv) · [`data/nfl/depth_model.csv`](data/nfl/depth_model.csv) · [`research/NFL_INJURY_DEPTH.md`](research/NFL_INJURY_DEPTH.md)
- **Build / check:** `python3 scripts/build_nfl.py` · `python3 scripts/check_nfl.py` (13 pages, 0 issues, every row source-linked) · `python3 tools/release_gate.py` (0 issues)
- **Flagged for Review (F-NFL-01…13):** https://sassnarep3-star.github.io/Own6/docs/nfl/flagged.html — includes the legacy rule/terms/2024-source corrections and the unresolved injury-policy PDF, market-data, depth, correlation, CLV, parlay-dependence and prop-settlement limits

## SF rental increase review — 94122 (added 2026-11-06)

A fully additive pack analyzing lawful, "reasonable and normal" rent increases for two rent-controlled units (building built 1940) in San Francisco's 94122 (Outer Sunset) zip code — San Francisco Rent Ordinance allowable increase (1.6% for 3/1/2026–2/28/2027; 60% of Bay Area CPI-U, 7% cap), banking of skipped increases, California Civil Code §§827 / 1946.2 / 1947.12 / 1954.53 / 51 and Gov. Code §12955, the Fair Housing Act/HUD, computed per-unit scenarios with correct 30/90-day notice math, a one-vs-both-units discrimination analysis, a tenant-lawyer scrutiny checklist, and a clearly labeled Flagged for Review page. All personal information is anonymized (placeholders Tenants A–F); dates and amounts are preserved. Not legal advice.

- **Live section:** https://sassnarep3-star.github.io/Own6/docs/rental/
- **Start here:** [`docs/rental/index.html`](docs/rental/index.html) → [`docs/rental/executive-summary.html`](docs/rental/executive-summary.html)
- **Executive summary (markdown):** [`RENTAL_INCREASE_SF_EXECUTIVE_SUMMARY.md`](RENTAL_INCREASE_SF_EXECUTIVE_SUMMARY.md)
- **Data:** [`data/rental/`](data/rental/) · **Build:** `python3 scripts/build_rental.py` · **Check:** `python3 scripts/check_rental.py` (14 pages, 0 broken internal links, every table row source-linked)

Flagged for Review (F-R1…F-R13, e.g., Unit 2's 13.1% combined notice would require 90 days; HUD area FMRs blank/unverified; Unit 2's current base rent unverified): https://sassnarep3-star.github.io/Own6/docs/rental/flagged.html

## SF Outer Sunset (`94122`) Compliance, SEC REIT vs. Small-Owner & Tenant-Lawyer Audit (`docs/sf-94122/`)

An anonymized, zero-inference compliance dashboard and dataset suite covering San Francisco Rent Ordinance (`1.6%` Form 571 rate for `3/1/2026–2/28/2027`), Housing Inventory Rent Increase Licensing (`SF Admin Code § 37.15`), Costa-Hawkins & Rule `6.14`/`6.15` roommate continuity (`Tenant 1A`–`Tenant 1D`, `Tenant 2A`–`Tenant 2B`), July 22, 2026 AvalonBay/Equity Residential SEC Form 425 renewal filings vs. SF Rent Board appeal rulings (`AL260003` `$14,742.04` Outer Sunset refund; `AL250027` non-waivable Costa-Hawkins protection), SF Admin Code `§ 37.10C` algorithmic pricing ban, ZIP `94122` buyout statistics (`48` declarations / `25` buyouts), HUD FY 2026 San Francisco HMFA Fair Market Rents, 12-point SF tenant-lawyer strict scrutiny checklist, and single-unit vs. both-unit Fair Housing analysis. Informational only; not legal advice.

- **Dashboard:** [`docs/sf-94122/index.html`](docs/sf-94122/index.html) (`https://sassnarep3-star.github.io/Own6/docs/sf-94122/`)
- **Flagged for Review:** [`docs/sf-94122/flagged.html`](docs/sf-94122/flagged.html)
- **Executive Summary:** [`research/SF_94122_EXECUTIVE_SUMMARY.md`](research/SF_94122_EXECUTIVE_SUMMARY.md)
- **Line-by-Line Repo & Source Audit:** [`audit/SF_94122_REPO_AND_SOURCE_AUDIT.md`](audit/SF_94122_REPO_AND_SOURCE_AUDIT.md)
- **CSV Datasets & Verifier:** [`data/sf_94122/`](data/sf_94122/) · `python3 scripts/build_sf_94122.py --check` · `python3 scripts/check_sf_94122.py`

## NFL Decision, Origination & Depth-Deficiency Command Center (`docs/nfl-309921cc/`) — added 2026-11-13

Session `arena/309921cc-own6`. Built only from pages read directly on official NFL and club sites on
2026-11-13. A value with no official source is left blank and flagged, never filled in.

- **Live dashboard (16 pages):** [`docs/nfl-309921cc/index.html`](docs/nfl-309921cc/index.html)
  (`https://sassnarep3-star.github.io/Own6/docs/nfl-309921cc/`)
- **Decision ledger:** [`data/nfl_309921cc/decision_ledger.csv`](data/nfl_309921cc/decision_ledger.csv) →
  [`docs/nfl-309921cc/decision-ledger.html`](docs/nfl-309921cc/decision-ledger.html) — 16 questions:
  what we have, what we lack, how to discover it
- **Suggestions (review only, nothing auto-applied):** [`data/nfl_309921cc/suggestions.csv`](data/nfl_309921cc/suggestions.csv) →
  [`docs/nfl-309921cc/suggestions.html`](docs/nfl-309921cc/suggestions.html) — 14 items, all `pending_human_choice`
- **Measured correlations & luck index:** `data/nfl_309921cc/correlations.csv` ·
  `data/nfl_309921cc/luck_index.csv` → [`docs/nfl-309921cc/correlations.html`](docs/nfl-309921cc/correlations.html)
- **Originated lines:** [`data/nfl_309921cc/originated_lines.csv`](data/nfl_309921cc/originated_lines.csv) →
  [`docs/nfl-309921cc/lines.html`](docs/nfl-309921cc/lines.html)
- **Injury & depth (1st–4th string, offense and defense):** `data/nfl_309921cc/week10_injuries.csv` (326 rows) ·
  `data/nfl_309921cc/depth_deficiency.csv` → [`docs/nfl-309921cc/depth.html`](docs/nfl-309921cc/depth.html)
- **Strategies, gates, leaderboard:** `data/nfl_309921cc/strategies.csv` · `validation_gates.csv` ·
  `leaderboard_tiers.csv` — 10 preregistered strategies, 12 gates, **0 qualified**
- **Repository review & flagged items:** `data/nfl_309921cc/repo_findings.csv` (15) ·
  `data/nfl_309921cc/flagged.csv` (17) → [`docs/nfl-309921cc/flagged.html`](docs/nfl-309921cc/flagged.html)
- **Engine, datasets, verifier:** [`src/nfl_309921cc/`](src/nfl_309921cc/) ·
  `python3 scripts/build_nfl_309921cc.py` · `python3 scripts/check_nfl_309921cc.py`
- **Executive summary:** [`NFL_309921CC_EXECUTIVE_SUMMARY.md`](NFL_309921CC_EXECUTIVE_SUMMARY.md) ·
  **Repo review:** [`audit/NFL_309921CC_REPO_REVIEW.md`](audit/NFL_309921CC_REPO_REVIEW.md)

**Verified counts:** 32 clubs (sum W = sum L = 136, sum T = 2, sum PF = sum PA = 6,291) · 14 Week 10 games
+ 4 byes · 326 official injury-report rows · 8 correlations measured from the verified standings ·
16 pages, 695 sourced table rows, 0 `<input>` elements.

## NFL Fair-Line Origination, Depth-Deficiency & Skill-Gated Leaderboard (`docs/nfl-origination/`)

A pure-stdlib Python 3.11 NFL fair-line origination, starter-vs-backup (`1st`–`4th` string) offensive/defensive depth-deficiency, combo-correlation, and 12-gate anti-luck leaderboard suite. Its official-source register has 28 entries with read dates and scope. A prior 13 Nov 2026 live re-verification recorded all 32 clubs' standings (`136W–136L–2T`, `6,291 PF = 6,291 PA` after WAS 24–NYG 21), a 102-row injury/depth reconciliation and the Week 10 schedule; these are dated source snapshots, not a live feed. All unverified sportsbook prices, calibrated NFL fair lines, empirical outcomes, and paired correlations remain blank. The four bye clubs were confirmed in that review, but their combined slate row remains a formatting/schema issue.

- **Live Dashboard (11 pages):** [`docs/nfl-origination/index.html`](docs/nfl-origination/index.html) (`https://sassnarep3-star.github.io/Own6/docs/nfl-origination/`)
- **Suggestions for Review & Decision Q&A:** [`docs/nfl-origination/suggestions.html`](docs/nfl-origination/suggestions.html) · [`docs/nfl-origination/decision-qa.html`](docs/nfl-origination/decision-qa.html)
- **Flagged for Review (`NFL-F01`..`NFL-F25`):** [`docs/nfl-origination/flagged.html`](docs/nfl-origination/flagged.html)
- **Live 13 Nov snapshot & reconciliation:** [`standings_live_2026_11_13.csv`](data/nfl_origination/standings_live_2026_11_13.csv) · [`live_check_2026_11_13.csv`](data/nfl_origination/live_check_2026_11_13.csv) · [`audit/NFL_LIVE_REVERIFICATION_2026_11_13.md`](audit/NFL_LIVE_REVERIFICATION_2026_11_13.md)
- **Executive Summary & Repo Audit:** [`NFL_ORIGINATION_EXECUTIVE_SUMMARY.md`](NFL_ORIGINATION_EXECUTIVE_SUMMARY.md) · [`audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md`](audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md)
- **Independent Final Review (2026-11-13):** [`audit/NFL_FINAL_REVIEW_709D3C80.md`](audit/NFL_FINAL_REVIEW_709D3C80.md) — local checks, source-access boundary, and flagged integration issues.
- **Engine, Datasets & Verifier:** [`src/nfl_origination/`](src/nfl_origination/) · [`data/nfl_origination/`](data/nfl_origination/) · `python3 scripts/build_nfl_origination.py --check` · `python3 scripts/check_nfl_origination.py`
- **Peer NFL Week 10 Verification Pack (`3b81013c`):** [`docs/nfl-3b81013c/index.html`](docs/nfl-3b81013c/index.html) (`https://sassnarep3-star.github.io/Own6/docs/nfl-3b81013c/`)
- **Additional self-contained NFL Week pack (PR #80):** [`docs/nfl-wk/index.html`](docs/nfl-wk/index.html) · [`data/nfl_wk/sources.csv`](data/nfl_wk/sources.csv) · [`data/nfl_wk/flagged.csv`](data/nfl_wk/flagged.csv). PR #80 describes 11 candidates as quarantined, 19 suggestions awaiting choice, and its originated lines as calculations from official standings with all market/edge/ROI/correlation cells blank. These are pack-reported statuses, not new source reads by this integration or results to combine with the main 10-candidate leaderboard. Manual source review: [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) · [Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11).


---

## NFL Own-Line Market Desk (`data/nfl_market/`, `docs/nfl-market/`)

Session `arena/33ee4854-own6`, capture 2026-11-14. Live:
https://sassnarep3-star.github.io/Own6/docs/nfl-market/

This pack originates NFL side, total and moneyline numbers, keeps an opening/closing price-snapshot
store for every originated market, grades itself against a verified results feed, and separates
**signal score** from **staking score** on its leaderboard.

Read `NFL_MARKET_EXECUTIVE_SUMMARY.md` first. Rebuild with
`python3 scripts/build_nfl_market.py`, verify with `python3 scripts/check_nfl_market.py` (971 checks),
test with `python3 -m unittest discover -s tests -p "test_nfl_market.py"`.

**Headline finding:** the NFL publishes no odds or line page (`https://www.nfl.com/odds/` is the NFL
404 page). Every market-line and difference cell is therefore blank with an explicit status rather
than filled from a non-official source. No edge has been measured, no strategy is live, and the
originated side model went 28-44 walking forward. All of that is published on the site rather than
omitted from it.
## NFL Price & Results Pack (session 6cefc476, 2026-11-14)

A self-contained pack implementing the price-snapshot store, a verified results feed, ordered
origination (side → total → moneyline) with separate **fair line / market line / difference** columns,
a leaderboard that separates **signal from staking**, **replacement-depth** tracking (the string level
of the replacement), correlations computed only from officially sourced numbers **with n published**,
a defined **demotion gate** (live → paper), a decision-questions register, and a review-first
suggestions section. Live: https://sassnarep3-star.github.io/Own6/docs/nfl-6cefc476/

Every table row carries an official source link; values that cannot be confirmed are published blank
and flagged ([Flagged for review](docs/nfl-6cefc476/flagged.html)). Build/check:
`python3 scripts/build_nfl_6cefc476.py` · `python3 scripts/check_nfl_6cefc476.py` ·
`python3 -m unittest tests.test_nfl_6cefc476`. Nothing demonstrates a profitable edge; model outputs
are computations, not market prices. Executive summary:
[`NFL_6CEFC476_EXECUTIVE_SUMMARY.md`](NFL_6CEFC476_EXECUTIVE_SUMMARY.md) · repo review:
[`audit/NFL_6CEFC476_REPO_REVIEW.md`](audit/NFL_6CEFC476_REPO_REVIEW.md).

## NFL Prices & Proof (session d966f630, 2026-11-14)

The same eight-requirement brief as the sibling packs above, implemented on its own spine:
`src/nfl_d966f630/` (capture, results, prices, originate, depth, correlate, backtest, leaderboard,
demotion, flags, advice, audit) → 41 tables in `data/nfl_d966f630/` → 17 pages at
https://sassnarep3-star.github.io/Own6/docs/nfl-d966f630/

- **Verified results feed:** 44 official games (Weeks 7–10, 2026), 37 identity checks
  (`sum W = sum L`, `PF − PA = NET`, `games = 0.5·Σ` others' games`), and 96 club-week
  reconciliations of the derived "through week N" tables against the standings read: 86 matched,
  10 clubs on bye with no badge, **0 mismatches**.
- **Price ledger:** 210 hash-chained snapshot rows over 171 markets; open, close and movement are
  derived from a market's position in its own series, never asserted. 26 markets show real
  movement, and all 26 cross model versions, so the movement strategy is held at the gate.
- **Origination:** side → total → moneyline enforced by a stage-order contract; fair / market /
  difference published as three separate columns, with the model side filled and the market side
  blank on all 14 rows plus a logged capture-attempt register.
- **Leaderboard:** signal ranked on Brier **skill against each event's own base rate**, staking
  reported beside it and never used for rank; the verifier fails the build if a payout column
  appears in the signal table or an accuracy column in the staking table.
- **Demotion gate:** 10 gates × 10 strategies = 100 evaluated rows; 1 strategy promoted, 9 held —
  including the top-ranked signal row, which fails on calibration drift, and the second, which
  fails on its drawdown budget.

**Known limits, stated where they are read:** there is no book price in this environment, so no
edge, no closing-line value and no ROI against a price exists anywhere in the pack; the
probabilities are fitted on 28–86 team-games and published undamped with the fits shown as
analysis; prop-combination legs cannot settle without per-player statistics.
Build / check / test: `python3 scripts/build_nfl_d966f630.py` ·
`python3 scripts/check_nfl_d966f630.py` (51 checks) ·
`python3 -m unittest discover -s tests -p "test_nfl_d966f630.py"` (61 tests).
Executive summary: [`NFL_D966F630_EXECUTIVE_SUMMARY.md`](NFL_D966F630_EXECUTIVE_SUMMARY.md) ·
audit: [`audit/NFL_D966F630_REPO_AND_SOURCE_AUDIT.md`](audit/NFL_D966F630_REPO_AND_SOURCE_AUDIT.md).

*Note for whoever merges next:* five sessions implemented this same eight-requirement brief independently on the same branch policy - `docs/nfl-market/` (session `f4e592a7`), `docs/nfl-6cefc476/`, `docs/nfl-f4/`, `docs/nfl-a411fed0/` and this pack. They agree on the central fact (no official or licensed source in this environment publishes a price, so the market and difference columns are blank everywhere); they differ in sample window, in how signal is ranked, and in how the demotion gate is defined. Choosing one as canonical is a human decision, recorded on the coordination board rather than resolved by this pack.

## NFL Decision-Readiness Table on the Landing Page (session 6ab24751, 2026-11-15)

The brief asks for a **decision-readiness table on the landing page: one row per requirement, with the
gate that blocks it and the number that would clear it**. The root landing page (`index.html`) now carries
that table directly, and the same table is published in a self-contained dashboard at
[`docs/nfl-6ab24751/`](docs/nfl-6ab24751/) →
https://sassnarep3-star.github.io/Own6/docs/nfl-6ab24751/

- **81 requirements**, each mapped to a status, the gate that blocks it, the number or condition that
  would clear it, the evidence artifact, and an official source link.
- **33 validation gates** (VG / NFL-G / D966-G families) in `data/nfl_6ab24751/gates.csv`, each naming what
  it blocks and its threshold.
- **Statuses:** 18 implemented · 20 implemented (limited) · 40 open/blocked/needs-review · 3 rejected by
  policy (depth from jersey/experience/salary; ranking by season-long ROI).
- **The binding blockers:** VG-03 (no licensed market price archive), NFL-G10 (partial, unofficial depth
  coverage), VG-07 (the sample floor — zero certified strategies by design).

The table is a consolidated roll-up grounded in the merged packs' gate and flag registers; it is not a fresh
re-verification of every underlying value, and no market price, ROI or CLV is published. Build / check /
test: `python3 scripts/build_nfl_6ab24751.py` · `python3 scripts/check_nfl_6ab24751.py` (344 checks) ·
`python3 -m unittest discover -s tests -p "test_nfl_6ab24751.py"` (13 tests). Executive summary:
[`NFL_6AB24751_EXECUTIVE_SUMMARY.md`](NFL_6AB24751_EXECUTIVE_SUMMARY.md).

## NFL Pack 48217A55 (session 48217a55, 2026-11-15) — Week 10 game-day capture

A pack built from a **single game-day reading of nine official NFL pages**, captured 2026-11-15 while Week 10
was still being played. Published at [`docs/nfl-48217a55/`](docs/nfl-48217a55/) →
https://sassnarep3-star.github.io/Own6/docs/nfl-48217a55/

- **347 injury rows** across the 28 clubs playing in Week 10 (70 Out · 90 Questionable · 11 Doubtful · 176
  with no game status, published as blank rather than as clearances). Four clubs were on bye and have no
  section on the report; their absence is published as a bye, never as health.
- **Through-Week-9 standings reconstructed by subtraction** from the live standings page and verified
  **10 of 10** against an official pre-game page that printed each club's record before kickoff. League
  points for equals points against (6,246 = 6,246); the implied completed-game count is **136**.
- **Reserve list, trades and Week 9 inactives** captured so that *not listed* never reads as *available*.
- **Luck share measured at 0.518** across 136 games — the bar any skill claim has to clear.
- **74 requirements**, each with the gate that blocks it and the number that would clear it · 12 gates ·
  9 pre-registered strategies · an empty five-division leaderboard · 18 questions with discovery paths ·
  16 suggestions with options and a cost of doing nothing.
- **1,054 blank cells, every one traced** to one of 17 flags or to a declared expected-blank reason. Where a
  market price would go, the cell is blank and flagged — nothing is inferred.

Build / check / test: `python3 scripts/build_nfl_48217a55.py` · `python3 scripts/check_nfl_48217a55.py`
(115 checks) · `python3 -m unittest discover -s tests -p "test_nfl_48217a55.py"` (59 tests). The builder
takes no arguments and touches no network, so a re-run reproduces byte-identical files. Executive summary:
[`NFL_48217A55_EXECUTIVE_SUMMARY.md`](NFL_48217A55_EXECUTIVE_SUMMARY.md).
