# Own6 — NFL Decision & Research Dashboard

An evidence-first research repository with an NFL line-origination and validation program, plus preserved NBA and San Francisco housing research. The NFL site organizes requirements, decision questions, source records, injury/depth context, line methods, single/parlay/player-prop strategy hypotheses, correlation methods, validation gates, suggestions, and review flags. **Nothing in this repository demonstrates a profitable NFL edge.** Model calculations are not market prices, and unverified facts remain blank or explicitly marked as computed/unverified.

## Start here

- **Live NFL landing page:** https://sassnarep3-star.github.io/Own6/ — no-input overview with clear links to the decision tools, workspaces, suggestions, and Flagged for Review.
- **Main NFL Origination dashboard:** [`docs/nfl-origination/index.html`](docs/nfl-origination/index.html) — the 12-gate research framework and 10 preregistered strategy candidates.
- **Suggestions (review before project changes):** [`docs/nfl-origination/suggestions.html`](docs/nfl-origination/suggestions.html)
- **Flagged for Review:** [`docs/nfl-origination/flagged.html`](docs/nfl-origination/flagged.html)
- **NFL executive summary:** [`docs/nfl-origination/executive-summary.html`](docs/nfl-origination/executive-summary.html)
- **Other research domains:** [NBA assurance](docs/assurance/index.html) · [all sections hub](docs/index.html)

The repository root now opens an NFL-focused portal. The separate `docs/` dashboard and NBA, NFL, and housing research packs remain available; they have separate evidence boundaries and should not be read as multiple independent performance records.

## Evidence state

## Live site contents

**Verification ledger (2026-11-03):** [`docs/verify/`](docs/verify/index.html) records every value that was re-read against an official page this session — 15/15 final scores and 30/30 standings rows match (54/54 ledger checks), with the NBA Terms of Use and 국민체육진흥법 제26조 quoted verbatim. Items that could not be confirmed are blank and listed with a reason. Build/check: `python3 scripts/build_verify.py` · `python3 scripts/check_verify.py`.
GitHub Pages serves the NFL-focused portal from the repository root; the organized multi-section site under [`docs/`](docs/index.html) preserves the dashboard/calculator, strategy catalog, validation gates, correlation methodology, leaderboard design, sources registry, and Flagged for Review. See [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) for the NBA assurance summary.

| Area | Status | Source |
|---|---|---|
| Authorized empirical observations | 0 | [Project report](https://github.com/sassnarep3-star/Own6/blob/main/data/empirical/report.csv) |
| Qualified strategies | 0 | [Project report](https://github.com/sassnarep3-star/Own6/blob/main/data/empirical/report.csv) |
| Current correlations / edge / ROI / CLV | Blank · unverified | [NBA Terms §9](https://www.nba.com/termsofuse#nba-statistics) |
| Legacy data archives | Preserved but unverified in the current assurance review | [Row audit](https://github.com/sassnarep3-star/Own6/blob/main/data/assurance/row_audit.csv) |
| Official source register | 20 direct reads, 2 partial reads | [Source register](https://github.com/sassnarep3-star/Own6/blob/main/data/assurance/sources.csv) |

**No authorized NBA gambling-use data feed is configured.** [NBA Terms §9](https://www.nba.com/termsofuse#nba-statistics) restricts gambling use of NBA Statistics, and §1 restricts public reuse. The [NBA Stats FAQ](https://www.nba.com/stats/help/faq) says statistics are not available for download. The project does not scrape, republish or invent NBA statistics, odds, correlations or returns.


## Verified snapshot — 5 November 2026 (`docs/daily/`)

A dated, official-source snapshot with its own checker: 121 committed final scores reconciled
30/30 to today's `nba.com/standings` **and** 30/30 to the previous 3 November snapshot; the 14
4 November games re-read one card at a time; an 11-game forward slate (5–6 November) with model
line estimates and deliberately **blank** market cells; a luck-controlled walk-forward signal test
(61 games, McNemar plus bootstrap); and a Flagged-for-Review page. Live:
https://sassnarep3-star.github.io/Own6/docs/daily/

Build and check: `python3 scripts/daily_analysis.py` · `python3 scripts/build_daily.py` ·
`python3 scripts/check_daily.py` · `python3 -m unittest discover -s tests -p test_daily.py`.
Per-row verification record: [`audit/SESSION_27fdbe09.md`](audit/SESSION_27fdbe09.md).

## Sources and evidence boundaries
Official NBA sources used for metric definitions: [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) and [NBA Inside the Game Stat Glossary](https://www.nba.com/news/inside-the-game-stat-glossary). These sources do **not** verify predictive value, odds, correlation estimates or profitability. Unconfirmed values must remain blank and be flagged.

The repository does contain historical legacy CSV/JSON archives and earlier dashboards. Those are **not** the authorized empirical ledger. The current assurance review leaves their numeric values unverified unless separately matched to an authorized official snapshot. Internal consistency checks are not official-source verification.

## What was hardened

- Fair American odds conversion no longer invents a margin.
- Strategy/market identity, frozen edge and conservative EV thresholds are enforced.
- Audit evidence requires reviewer, artifact URL/hash, scope, config hash and ledger hash; a boolean alone is rejected.
- CLV uses de-vigged same-line closing probabilities; moved lines stay blank and block the CLV gate.
- Correlations use strict training-only paired residuals, retain zeros, and require slate-clustered intervals and joint samples for combos.
- Bonferroni covers the actual qualification statistics across the frozen candidate family; the independent-trial win-count test is diagnostic only.
- The leaderboard ranks only all-gate qualifiers by the lower bound of slate-clustered holdout ROI. Rewards are non-monetary research priority only.

## Reproduce

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

A fully additive NFL research lab covering requirement traceability (R01–R18), decision-readiness questions/informations/answers (Q01–Q10) with discovery paths for missing info, a dedicated suggestions review section (S01–S12) that must be reviewed before any change, ten frozen signal strategies for singles/parlays/player-prop combos (N01–N10) with own-line method and correlation pairs, ten validation gates (G01–G10) with clustered-uncertainty and Bonferroni luck control, per-unit injury & depth-deficiency modeling that flags 2nd/3rd/4th-string backups replacing starters on offense and defense, and a clean dashboard-style GitHub Pages site — all rows source-linked, blank means unverified, no hallucinations, no profitability claim.

- **Live section:** https://sassnarep3-star.github.io/Own6/docs/nfl/ (`docs/nfl/index.html`)
- **Start here:** [`docs/nfl/index.html`](docs/nfl/index.html) → [`research/NFL_EXECUTIVE_SUMMARY.md`](research/NFL_EXECUTIVE_SUMMARY.md)
- **Requirements:** [`data/nfl/requirements.csv`](data/nfl/requirements.csv) · [`research/NFL_REQUIREMENTS.md`](research/NFL_REQUIREMENTS.md)
- **Decision framework:** [`data/nfl/decision_questions.csv`](data/nfl/decision_questions.csv) → [`docs/nfl/questions.html`](docs/nfl/questions.html)
- **Suggestions (review only):** [`data/nfl/suggestions.csv`](data/nfl/suggestions.csv) → [`docs/nfl/suggestions.html`](docs/nfl/suggestions.html)
- **Strategies & own lines:** [`data/nfl/origin_strategies.csv`](data/nfl/origin_strategies.csv) · [`research/NFL_SIGNALS.md`](research/NFL_SIGNALS.md)
- **Validation & correlations:** [`data/nfl/validation_gates.csv`](data/nfl/validation_gates.csv) · [`research/NFL_VALIDATION.md`](research/NFL_VALIDATION.md)
- **Injury & depth:** [`data/nfl/injury_tracking.csv`](data/nfl/injury_tracking.csv) · [`data/nfl/depth_model.csv`](data/nfl/depth_model.csv) · [`research/NFL_INJURY_DEPTH.md`](research/NFL_INJURY_DEPTH.md)
- **Build / check:** `python3 scripts/build_nfl.py` · `python3 scripts/check_nfl.py` (13 pages, 0 issues, every row source-linked) · `python3 tools/release_gate.py` (0 issues)
- **Flagged for Review (F-NFL-01…12):** https://sassnarep3-star.github.io/Own6/docs/nfl/flagged.html — rights, market prices, live injury snapshots, depth scores, correlations, leaderboard, CLV, parlay dependence, prop settlement

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

## NFL Fair-Line Origination, Depth-Deficiency & Skill-Gated Leaderboard (`docs/nfl-origination/`)

A pure-stdlib Python 3.11 NFL fair-line origination, starter-vs-backup (`1st`–`4th` string) offensive/defensive depth-deficiency, Gaussian copula combo-correlation, and 12-gate anti-luck leaderboard suite verified against 28 primary sources on `2026-11-12` (reconciling all 32 NFL clubs' 2026 standings `135W–135L–2T`, `6,246 PF = 6,246 PA`, all 14 Week 10 matchups + 4 byes including Munich neutral site, and 24 Week 10 injury/depth chains while leaving unconfirmed sportsbook lines, empirical EPA drop-offs, and paired correlations strictly blank).

- **Live Dashboard (11 pages):** [`docs/nfl-origination/index.html`](docs/nfl-origination/index.html) (`https://sassnarep3-star.github.io/Own6/docs/nfl-origination/`)
- **Suggestions for Review & Decision Q&A:** [`docs/nfl-origination/suggestions.html`](docs/nfl-origination/suggestions.html) · [`docs/nfl-origination/decision-qa.html`](docs/nfl-origination/decision-qa.html)
- **Flagged for Review (`NFL-F01`..`NFL-F15`):** [`docs/nfl-origination/flagged.html`](docs/nfl-origination/flagged.html)
- **Executive Summary & Repo Audit:** [`NFL_ORIGINATION_EXECUTIVE_SUMMARY.md`](NFL_ORIGINATION_EXECUTIVE_SUMMARY.md) · [`audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md`](audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md)
- **Independent Final Review (2026-11-13):** [`audit/NFL_FINAL_REVIEW_709D3C80.md`](audit/NFL_FINAL_REVIEW_709D3C80.md) — local checks, source-access boundary, and flagged integration issues.
- **Engine, Datasets & Verifier:** [`src/nfl_origination/`](src/nfl_origination/) · [`data/nfl_origination/`](data/nfl_origination/) · `python3 scripts/build_nfl_origination.py --check` · `python3 scripts/check_nfl_origination.py`
- **Peer NFL Week 10 Verification Pack (`3b81013c`):** [`docs/nfl-3b81013c/index.html`](docs/nfl-3b81013c/index.html) (`https://sassnarep3-star.github.io/Own6/docs/nfl-3b81013c/`)


