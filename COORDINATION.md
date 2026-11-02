# COORDINATION — Own6 NBA Lines Project

Session ID: arena-463d936f-own6 | Branch: arena/463d936f-own6 (fixed by Arena; note: user template suggested session-<id>/<task> branches, superseded by Arena branch rule — do not switch branches)
Date opened: 2026-11-02

## Task Board
| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 1 | Repo audit + executive summary | in progress | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, docs/ |
| 2 | Source verification registry (official sources only) | in progress | arena-463d936f-own6 | data/sources.csv, docs/sources.html |
| 3 | Line-generation engine (own lines: spread/total/win prob) | in progress | arena-463d936f-own6 | src/own6/ |
| 4 | Player-prop + parlay correlation engine | in progress | arena-463d936f-own6 | src/own6/props.py, src/own6/parlay.py |
| 5 | Validation gates + skill-vs-luck (CLV, calibration, bootstrap) | in progress | arena-463d936f-own6 | src/own6/validation.py, tests/ |
| 6 | Leaderboard scoring design | in progress | arena-463d936f-own6 | docs/leaderboard.html, src/own6/leaderboard.py |
| 7 | GitHub Pages site (landing + subpages, tables w/ source per row) | in progress | arena-463d936f-own6 | docs/*.html, docs/assets/ |
| 8 | Flagged for Review page | in progress | arena-463d936f-own6 | docs/flagged.html |
| 9 | Final integration, link check, PR to main, merge, Pages deploy | in progress | arena-463d936f-own6 | docs/, .github/ |

## Rules (from brief)
- Every table row: official-source link. Unconfirmable value => blank + flagged, never inferred.
- No manual input from owner; no hallucinated statistics, odds, or backtest results.
- Small frequent commits; pull --rebase before push; never discard others' work.
- Shared outputs (site index/nav, combined tables) changed only at final integration.

## Log
- 2026-11-02 arena-463d936f-own6: Repo audit — repo contains only README.md ("# Own6"), no code/data/site. No irregularities in repo itself; all content is greenfield. Claimed tasks 1-8 on fixed Arena branch.
