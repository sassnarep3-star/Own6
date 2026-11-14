# NFL Repository Review — session arena/6cefc476-own6 (2026-11-14)

Scope: line-by-line review of the repository as found at branch `arena/6cefc476-own6`
(base `36c6f84`, merge of PR #83) before this pack was added. Method: read every NFL-facing
data register and shared gate script; spot-check claims against pages read this session; re-check
the two outstanding cross-session requests (R1, R4). Findings are published at
`docs/nfl-6cefc476/repo-review.html` with evidence links and mirrored in
`data/nfl_6cefc476/repo_findings.csv` (N6CF-RF01…RF08). Nothing here is inferred; carried
prior-session reports are labelled as carried, not re-verified.

## Findings

| ID | Finding | Verification performed | Status |
|---|---|---|---|
| N6CF-RF01 | `data/nfl/sources.csv` still cites `https://www.nfl.com/official-nfl-rules/` (S-NFL-07), which prior sessions reported as an official NFL 404 (cross-session request R1) | Read the file on 2026-11-14; URL still present. Not re-fetched (the 404 is a carried verified report from sessions 309921cc/9e78abc5) | needs review |
| N6CF-RF02 | `scripts/source_coverage.py` `PUBLISHERS` allowlist (lines 25–36) contains no NFL or NFL-club domain, so NFL-sourced rows classify `secondary_reference_only` (cross-session request R4) | Read the script on 2026-11-14; allowlist lists nba.com, law.go.kr, nist.gov, scipy/sklearn/statsmodels docs, GitHub docs, and gaming regulators only | needs review |
| N6CF-RF03 | Two official nfl.com headlines disagree on Lamar Jackson's absence window (6-10 weeks vs 6-9 weeks) | Both headlines read on the nfl.com/injuries/ news section 2026-11-14 (sources S6CF-08/S6CF-09) | needs review |
| N6CF-RF04 | DET club depth chart does not list S Kerby Joseph although the official injury report lists him Out | `detroitlions.com/team/depth-chart` (S6CF-12) vs `nfl.com/injuries/` (S6CF-05), both read 2026-11-14 | needs review |
| N6CF-RF05 | League standings totals reconcile: W=136, L=136, T=2, PF=PA (league PF total = PA total) | Computed in `scripts/build_nfl_6cefc476.py` from the 32-row standings read (S6CF-01); matches the 136/136/2 figure recorded by the 2026-11-13 review | verified consistent |
| N6CF-RF06 | Repository mixes NBA, NFL and San Francisco housing research in one tree (five NFL packs, three housing analysis packs, several NBA packs) | Root listing read 2026-11-14 | needs review |
| N6CF-RF07 | Prior sessions reported the 2017 NFL injury-policy PDF as 404 and an NFL rule-change page showing 2025 content (NFL-F25) | Carried from COORDINATION.md session records; **not re-verified this session** | carried, not re-verified |
| N6CF-RF08 | `data/nfl_origination/site_suggestions.csv` SUG-01 describes a former root-redirect state that no longer matches the live root landing (README notes the same) | Root `index.html` read 2026-11-14 | needs review |

## Cross-checks that passed

- Every `data/nfl_6cefc476/*.csv` row carries an https source link on an official host
  (`scripts/check_nfl_6cefc476.py`, 0 issues).
- Origination order side → total → moneyline holds for all 26 games; every market has an open and a
  close snapshot row (regression tests in `tests/test_nfl_6cefc476.py`, 28 tests).
- Site pages contain zero input elements and every table row carries an https source link.
- The model math reproduces previously published statistical values (p-value and Fisher-z interval
  cross-checked against `data/nfl_309921cc/correlations.csv` NFL3-COR-01 inside unit tests).

## Boundaries

No market price, ROI, CLV, or profitability claim is made anywhere in this pack. No external NFL page
was fetched outside the sources listed in `data/nfl_6cefc476/sources.csv`. Prior packs' data was not
edited; this review only reports what it found with links for manual review.
