# Repository review — line by line, session `arena/309921cc-own6`

Reviewed 2026-11-13 at commit `d18f495` (merge of PR #73), on branch `arena/309921cc-own6`.
Machine-readable table: `data/nfl_309921cc/repo_findings.csv` → `docs/nfl-309921cc/repo-review.html`

## Method

1. Read the branch note and `COORDINATION.md` in full; listed open PRs and remote branches.
2. Enumerated all 448 tracked files and inspected the NFL-related ones line by line.
3. Fetched every official URL the repository cites as a source for the NFL packs, and recorded what
   the page actually returned on 2026-11-13.
4. Fetched the live GitHub Pages URLs printed in `README.md` and recorded the HTTP result.
5. Recomputed, with independently written code, every derived NFL number this session publishes.

Findings that belong to another session's files are logged as requests in `COORDINATION.md` and are
**not** edited by this session.

## Findings

| ID | Area | Severity | Finding |
|---|---|---|---|
| RF-01 | Site navigation | Medium | Root `index.html` is a `meta refresh` to `docs/assurance/`, an NBA-only dashboard. No other domain is reachable from the live root. |
| RF-02 | Duplication | High | Four independent NFL dashboards published from one repository: `docs/nfl/`, `docs/nfl-3b81013c/`, `docs/nfl-origination/`, `docs/nfl-309921cc/`. |
| RF-03 | Broken source link | High | `https://www.nfl.com/official-nfl-rules/` returns the official NFL 404 page. Cited 71 times across 20+ files, including live pages under `docs/nfl/`. |
| RF-04 | Incorrect live URL | Medium | `README.md` line 97 prints `https://sassnarep3-star.github.io/Own6/nfl/`, which returned GitHub's 404 page. Pages source is `main:/`, so the content is live at `/docs/nfl/`. |
| RF-05 | Source-scope mismatch | Medium | `https://www.nfl.com/terms/` redirects to `https://www.nfl.com/legal/subscriptions_terms`, which scopes itself to subscription, authentication and mobile products. The general page is `https://www.nfl.com/legal/terms/` (updated May 16, 2024). |
| RF-06 | Unreadable source | Medium | `https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf` is cited as verified on `docs/nfl/index.html`; a prior session recorded that it returned empty parsed content. |
| RF-07 | Evidence labelling | Medium | Expected signs in `data/nfl/correlations.csv`, floors such as 200 observations / 60 slates, and depth thresholds such as >0.5 / >0.6 are design choices published in value columns. |
| RF-08 | Data freshness | High | `nfl.com/scores` publishes Thursday 12 November Commanders 24–21 as Final; `nfl.com/standings` still shows WAS 3-5-1 and NYG 5-3-1. |
| RF-09 | Column provenance | Low | The NFL standings table renders two record/percentage columns its own LEGEND does not define. This pack omits them rather than guessing. |
| RF-10 | Unreadable table headers | Medium | `https://www.nfl.com/stats/team-stats/` returned 32 data rows per table with no readable header row, so no team statistic is reproduced here. |
| RF-11 | Concurrency | Medium | Open PR #68 and PR #72 both edit `data/assurance/*`, `data/source_coverage/*` and `audit/SOURCE_COVERAGE.md`. |
| RF-12 | Coordination file size | Low | `COORDINATION.md` is 194,096 bytes; the live task board is buried above many past session sections. |
| RF-13 | Verification coverage | High | `scripts/check_nfl.py`, `scripts/check_nfl_origination.py` and `scripts/check_site.py` validate link shape and internal resolution; none fetches the external URL. |
| RF-14 | Data rights | High | NFL.com Terms §1.3 prohibits systematic retrieval to compile a database without express prior written consent. This repository is a compiled database of official tables. |
| RF-15 | Coverage tooling | Medium | `scripts/source_coverage.py` declares a publisher allowlist with no NFL or NFL-club domain, so 655 of this pack's 693 NFL-sourced rows are reported as coverage gaps. |

## Regeneration note

`scripts/source_coverage.py` scans every `docs/**/*.html` page except its own `docs/coverage/`
output, and `scripts/audit_repo.py` writes `data/assurance/*` which `scripts/build_assurance.py`
then renders into `docs/assurance/*`. The three generators therefore depend on each other's output.
The committed artefacts were produced by iterating the sequence
`build_nfl_309921cc → build_lab → run_lab → build_assurance → source_coverage → audit_repo`
until two consecutive passes produced byte-identical files, then verifying with
`source_coverage.py --check`, `check_assurance.py`, `release_gate.py`, `check_nfl_309921cc.py` and
the full `pytest` suite.

The coverage tool classifies 655 of this pack's 693 rows as `secondary_reference_only` and 17 as
`repository_reference_only`, because its PUBLISHERS allowlist contains no NFL domain. Only 21 rows
register as official, and those are the rows citing NIST. This is logged as NFL3-RF-15 and is a
request to the tool's owner; this session does not edit that shared script.

## Verification performed on the official sources

| URL fetched on 2026-11-13 | Result |
|---|---|
| `https://www.nfl.com/standings/` | 200; 32 club rows; LEGEND defines 12 columns; two further columns undefined |
| `https://www.nfl.com/schedules` | 200; Week 10; 14 games with times, networks and pre-game records; 4 bye teams |
| `https://www.nfl.com/scores/` | 200; Thursday 12 November Commanders 24, Giants 21, Final |
| `https://www.nfl.com/injuries/` | 200; Week 10; 326 rows; five defined columns |
| `https://www.nfl.com/legal/terms/` | 200; updated May 16, 2024; §1.1 and §1.3 quoted verbatim |
| `https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners` | 200; integrity-policy and objectionable-wager text quoted verbatim |
| `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook` | 200; 2026 rule-change list present, including 6-1-6 |
| `https://operations.nfl.com/inside-football-ops/players-legends/2020-nfl-nflpa-cba-need-to-know/` | 200; gameday active list 48, eight offensive linemen, 14-team playoff |
| `https://www.patriots.com/team/depth-chart` | 200; offense and defense 1st-to-4th string; self-labelled unofficial |
| `https://www.detroitlions.com/team/depth-chart` | 200; offense and defense 1st-to-4th string; self-labelled unofficial |
| `https://www.nfl.com/stats/team-stats/` | 200; data rows present, no readable headers — no value taken |
| `https://www.nfl.com/official-nfl-rules/` | **404** (official NFL 404 page) |
| `https://sassnarep3-star.github.io/Own6/nfl/` | **404** (GitHub Pages 404 page) |
| `https://sassnarep3-star.github.io/Own6/docs/nfl/` | 200; NFL Lab dashboard |

## Independent recomputation

Every number this session publishes was recomputed with separately written code before publication:

- **Standings identities.** sum(W) = sum(L) = 136; sum(T) = 2; sum(PF) = sum(PA) = 6,291. Checked
  with a one-off script that does not import the pack.
- **Headline correlation.** `NFL3-COR-03` (net points per game ~ win percentage) recomputed
  independently: r = 0.878060 against the published 0.8781. The verifier asserts agreement.
- **Luck residuals.** Recomputed and confirmed to sum to zero, as OLS residuals must.
- **Injury counts.** Per-club practice-status counts were enumerated by hand from the fetched pages
  and compared against the counts the builder derives from the raw capture: 326 rows, 28 clubs, no
  duplicates, and every club's three counts summing to its listed total.
- **Model total.** Compared against the league's own points per game computed from the verified
  standings — a difference of +0.4588 points, published rather than hidden.

## What this session did not touch

No file owned by another session was edited. In particular: `data/nfl/**`, `docs/nfl/**`,
`data/nfl_3b81013c/**`, `docs/nfl-3b81013c/**`, `data/nfl_origination/**`, `docs/nfl-origination/**`,
`src/nfl_3b81013c/**`, `src/nfl_origination/**`, `data/assurance/**`, `docs/assurance/**`,
`data/source_coverage/**` and `docs/coverage/**` are untouched by this session's feature work. Only
the final integration step adds one navigation link and regenerates derived inventories.

## Requests logged to other sessions

- **R1** (to `efebf74f`, owner of `data/nfl/sources.csv`): repoint `S-NFL-07`-dependent rows from the
  404 URL to `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook`.
- **R2** (to `efebf74f`): cite `https://www.nfl.com/legal/terms/` rather than the
  subscription-scoped redirect, and retain the scope limitation.
- **R3** (to `efebf74f`): correct the README's `/nfl/` live URL to `/docs/nfl/`.
- **R4** (to any future session): label proposed thresholds and measured values differently in every
  value column.
