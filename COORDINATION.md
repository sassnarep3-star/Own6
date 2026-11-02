# COORDINATION — Own6 NBA Lines Project

Shared task board. Consolidated by the integration session from all claim branches on 2026-11-02.
Session IDs are the Arena branch names (the Arena branch rule supersedes the suggested
`session-<id>/<task>` branch naming; each session stays on its own fixed branch).

## Task board

| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 1 | Repo audit + executive summary | in progress | arena/463d936f-own6 | EXECUTIVE_SUMMARY.md, docs/ |
| 2 | Source verification registry (official sources only) | in progress | arena/463d936f-own6 | data/sources.csv, docs/sources.html |
| 3 | Line-generation engine (own lines: spread/total/win prob) | in progress | arena/463d936f-own6 | src/own6/ |
| 4 | Player-prop + parlay correlation engine | in progress | arena/463d936f-own6 | src/own6/props.py, src/own6/parlay.py |
| 5 | Validation gates + skill-vs-luck (CLV, calibration, bootstrap) | in progress | arena/463d936f-own6 | src/own6/validation.py, tests/ |
| 6 | Leaderboard scoring design | in progress | arena/463d936f-own6 | docs/leaderboard.html, src/own6/leaderboard.py |
| 7 | GitHub Pages site (landing + subpages, tables w/ source per row) | in progress | arena/463d936f-own6 | docs/*.html, docs/assets/ |
| 8 | Flagged for Review page | in progress | arena/463d936f-own6 | docs/flagged.html |
| 9 | Final integration: merge session branches, re-verify combined data line by line, link check, site build check, PR to main, merge, GitHub Pages deploy, record PR link here | claimed | arena/71464040-own6 | COORDINATION.md (integration), PR/merge to main, Pages settings |
| 10 | NBA strategy research, validation framework, executive summary, dashboard/site integration (duplicate claim of 1–8 scope) | in progress | arena/3b057a2c-own6 | COORDINATION.md, README.md, docs/**, index.html, assets/**, .github/workflows/** |
| 11 | Repository review, official-source research, NBA strategy analysis, GitHub Pages implementation (duplicate claim of 1–8 scope) | in progress | arena/a28a2ee1-own6 | COORDINATION.md, README.md, index.html, pages/, assets/, .nojekyll |
| 12 | NBA strategy research, evidence-led dashboard, executive summary, Pages setup (duplicate claim of 1–8 scope) | in progress | arena/d100a9d1-own6 | COORDINATION.md, README.md, index.html, strategies.html, validation.html, flagged.html, styles.css, data.js, .github/workflows/pages.yml |

## Rules (from brief)

- Every table row must carry a source link to an official/verified site. If a value cannot be
  confirmed from an official source it is left blank and flagged; values are never inferred.
- No manual input from the repo owner; no hallucinated statistics, odds, or backtest results.
- Small frequent commits; `git pull --rebase` (or `git fetch` + rebase) before every push; never
  discard another session's work; log merge conflicts here.
- Shared outputs (combined table data, site index and navigation) are changed only by the final
  integration session (task 9) once the content tasks are done.
- A status of `needs review` means the item is published on the Flagged for Review page and does
  not block the merge.
- Claims older than 60 minutes with no commits may be taken over; log the handoff here.

## Claims registry (as found on remote at session start, 2026-11-02)

- `arena/3b057a2c-own6` @ 2e07a70 — claimed full scope (task 10).
- `arena/463d936f-own6` @ 97c608a — claimed tasks 1–8; left task 9 unclaimed (task 9 owner now: arena/71464040-own6).
- `arena/a28a2ee1-own6` @ 3d5f254 — claimed full scope incl. integration (tasks 11; integration of record belongs to task 9 owner).
- `arena/d100a9d1-own6` @ c5f3a05 — claimed full scope (task 12).
- `arena/71464040-own6` (this session) — claimed task 9 (integration), maintains this consolidated board.

## Log

- 2026-11-02 arena/71464040-own6: Read all four claim-branch boards; no board existed on `main`
  or on this branch. Consolidated them above and claimed task 9 (explicitly unclaimed on the
  arena/463d936f-own6 board). Pushed immediately after claiming, per the rules. Repo audit:
  `main` contains only `README.md` (`# Own6`, 6 bytes); GitHub Pages already enabled on
  `main` root (status: built, https://sassnarep3-star.github.io/Own6/). No PRs open.
- 2026-11-02 arena/71464040-own6: Duplicate claims detected (tasks 10–12 mirror tasks 1–8).
  Per the no-duplicate-work rule this session will not edit files in tasks 1–8 scope; it will
  only integrate, re-verify, check links/build, open and merge the PR, deploy Pages, and update
  this board. Requests for other sessions are logged in this file instead of editing their files.
