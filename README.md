# Own6 — NBA Lines Research Lab

A research-first project for originating NBA spreads, totals, win probabilities, player props, prop combos and parlays. **Nothing in this repository demonstrates a profitable edge.** No current line, correlation, ROI or reward winner is published without authorized, timestamped, out-of-sample evidence.

## Start here

- **Live assurance dashboard:** https://sassnarep3-star.github.io/Own6/ — clean no-input overview, strategies, lines/props, correlations, leaderboard, validation gates, official sources, Flagged for Review and full repo audit.
- **Executive summary:** [`research/EXECUTIVE_SUMMARY.md`](research/EXECUTIVE_SUMMARY.md)
- **Signal research:** [`research/SIGNALS.md`](research/SIGNALS.md)
- **Validation protocol v2:** [`research/VALIDATION_v2.md`](research/VALIDATION_v2.md)
- **Source assurance:** [`research/ASSURANCE.md`](research/ASSURANCE.md)

The root page redirects to the assurance dashboard. The earlier data hub and section sites are preserved as archives and linked from the dashboard.

## Evidence state

## Live site contents

**Verification ledger (2026-11-03):** [`docs/verify/`](docs/verify/index.html) records every value that was re-read against an official page this session — 15/15 final scores and 30/30 standings rows match (54/54 ledger checks), with the NBA Terms of Use and 국민체육진흥법 제26조 quoted verbatim. Items that could not be confirmed are blank and listed with a reason. Build/check: `python3 scripts/build_verify.py` · `python3 scripts/check_verify.py`.
GitHub Pages publishes the organized site from [`docs/`](docs/index.html): dashboard/calculator, strategy catalog, validation gates, correlation methodology, leaderboard design, sources registry and Flagged for Review. See [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

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

Concurrent sessions are coordinated in [`COORDINATION.md`](COORDINATION.md). This session works on the fixed Arena branch `arena/74d27b5d-own6`, preserves other sessions' work, and records sources, verification and irregularities there. Flagged items are published on the site's **Flagged for Review** page and do not block publication of the research framework.

## No betting advice

Analytics research only. No wagers, stakes, picks, payouts or profitability claims. Luck cannot be eliminated; the protocol reduces false discoveries through rights, provenance, chronology, dependence-aware uncertainty, multiplicity control and frozen preregistration.

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

