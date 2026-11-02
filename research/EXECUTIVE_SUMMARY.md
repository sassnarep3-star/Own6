# Executive Summary — Own6 Empirical NBA Lab

**Date:** 2026-11-02 · **Session:** `arena-5dfdc6d5` · **Branch:** `arena/5dfdc6d5-own6`

## Objective

Originate NBA lines, player-prop and parlay strategies, and rank them on a leaderboard that rewards skill rather than luck. Every strategy must pass explicit validation gates before it can qualify. This extension preserves the existing upstream dashboards and adds an isolated empirical lab that runs without manual input and stays fail-closed until authorized data and evidence are provided.

## What was built

1. **Official-source evidence audit** — `scripts/audit_sources.py` reads the upstream data row by row, produces a checksum/line-count inventory at upstream `77a28cc`, and writes 63 upstream data-row reviews, 43 upstream files, and 20 reproducible findings. Official pages were read directly: NBA Terms §§1 and 9, NBA Stats FAQ, glossary, schedule, game `0022600169`, integrity release, partner pages, scikit-learn calibration, NIST uncertainty and Bonferroni, SciPy binomial reference, and GitHub Pages docs. The Korean statute header was readable but the dynamic article body was not; the injury PDF fetch failed. Those limitations are flagged, not filled in.

2. **Licensed-data contract** — `research/empirical/DATA_CONTRACT.md` defines one observation per pre-event paper selection. It requires official provider URLs, SHA-256 checksums, settlement rules, license IDs, model versions, and timestamps. Missing evidence blocks qualification; it is never imputed.

3. **Fail-closed validation framework** — `nba_lab/` contains strict pricing, event-clustered statistics, models, contracts, and gates. The lab runs deterministically on the empty ledger and reports `not_run`, zero observations, zero qualified strategies, and no leaderboard rows. No synthetic or fabricated returns are published.

4. **Six frozen candidate strategies** — `L1` efficiency moneyline, `L2` margin-residual spread, `L3` pace-efficiency total, `P1` shrunk player-points prop, `C1` two-player same-game overs combo, and `X1` two-game moneyline parlay. The family is frozen in advance so the multiple-testing correction reflects every hypothesis tried, including abandoned ones.

5. **Ten validation gates** — `G01` rights and market permission, `G02` field-level provenance, `G03` chronological walk-forward, `G04` effective sample size, `G05` market-relative predictive quality, `G06` post-vig profitability, `G07` closing-line value, `G08` luck and multiple testing, `G09` joint dependence, and `G10` frozen auditable ledger. Missing evidence never counts as a pass.

6. **Empirical dashboard** — `scripts/build_lab.py` builds eight isolated pages under `docs/lab/`. `scripts/check_lab.py` verifies the report is fail-closed, the ledger schema is correct, all 10 gates are present, and all internal links resolve.

## Key findings

- **No authorized NBA gambling-use data feed is configured.** NBA.com Terms §9 restricts NBA Statistics from being used in connection with any gambling activity, and §1 restricts public reuse. The NBA Stats FAQ says stats are not available for download. The lab therefore does not scrape, republish, or invent NBA statistics, odds, correlations, or returns.

- **The upstream repository had two published dashboards before this session.** Their work is preserved unchanged. This session adds a non-overlapping empirical extension.

- **The original executive summary omitted the NBA Terms §9 gambling restriction and §1 reuse restriction.** Finding R01 flags this. The new lab makes rights and market permission a blocking gate.

- **The original validation gates were designed, not enforced.** Findings R02–R12 flag missing log-loss, correlation, ledger, and clustering checks, plus unvalidated odds/probability inputs. The new `nba_lab` enforces all ten gates and fails closed on missing evidence.

- **The original leaderboard used only sample size.** Finding R03 flags that a negative lower-bound strategy could still be marked eligible. The new leaderboard ranks only all-gate qualifiers by the lower bound of event-clustered holdout ROI.

- **No strategy has demonstrated market-relative skill.** No licensed historical odds or results archive is present, so all empirical rows are blank and every strategy is unqualified. No profitability claim is made.

## What is not verified

- **Korean law.** The National Sports Promotion Act header was read from law.go.kr, but the dynamic article body was not returned. The upstream legal rows are flagged `needs_review`, not independently re-verified.

- **NBA prop restrictions.** The official release confirms restrictions exist, but the specific reported prop bans appear only in press reports. They remain unverified.

- **Odds, results, correlations, and strategy performance.** No licensed odds archive or official historical results dataset was available. All such values are blank and flagged.

## Deliverables

- `nba_lab/` — fail-closed validation framework.
- `tests/empirical/` — 20 tests, including adversarial cases for invalid odds, unaligned arrays, constant series, empty samples, and unequal lengths.
- `data/empirical/` — sources, ledger schema, rights registry, evidence file, report, and audit outputs.
- `docs/lab/` — isolated eight-page dashboard.
- `scripts/run_lab.py`, `scripts/build_lab.py`, `scripts/check_lab.py`, `scripts/audit_sources.py` — automated pipeline.
- `.github/workflows/lab-ci.yml` — non-publishing CI that installs pinned dependencies and runs the full pipeline.

## Sources

All official source links and scope limits are in `data/empirical/sources.json`. The upstream row-by-row audit is in `data/empirical/source_audit.csv`. The reproducible findings are in `data/empirical/repo_findings.csv`.

## No betting advice

This repository is analytics research only. It does not place bets, accept stakes, distribute rewards, or provide picks. Any future authorized data must clear the rights and legal gates before empirical results are published.
