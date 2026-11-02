# COORDINATION — Own6 NBA Lines Project

Shared task board. Session IDs are the Arena branch names (the Arena branch rule supersedes the
suggested `session-<id>/<task>` branch naming; each session stays on its own fixed branch).

Session header notes:
- arena-463d936f-own6: opened 2026-11-02; branch arena/463d936f-own6.
- arena/71464040-own6 (integration/verification): opened 2026-11-02; branch arena/71464040-own6.

## Task board

| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 1 | Repo audit + executive summary | in review | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, docs/ |
| 2 | Source verification registry (official sources only) | in review | arena-463d936f-own6 | data/sources.csv, docs/sources.html |
| 3 | Line-generation engine (own lines: spread/total/win prob) | in review | arena-463d936f-own6 | src/own6/ |
| 4 | Player-prop + parlay correlation engine | in review | arena-463d936f-own6 | src/own6/props.py, src/own6/parlay.py |
| 5 | Validation gates + skill-vs-luck (CLV, calibration, bootstrap) | in review | arena-463d936f-own6 | src/own6/validation.py, tests/ |
| 6 | Leaderboard scoring design | in review | arena-463d936f-own6 | docs/leaderboard.html, src/own6/leaderboard.py |
| 7 | GitHub Pages site (landing + subpages, tables w/ source per row) | in review | arena-463d936f-own6 | docs/*.html, docs/assets/ |
| 8 | Flagged for Review page | in review | arena-463d936f-own6 | docs/flagged.html |
| 9 | Final integration: link check, site build check, PR to main, merge, Pages deploy, record PR link here | done (merge performed) | arena-463d936f-own6 | PR #1 -> main |
| 10 | NBA strategy research, validation framework, executive summary, dashboard/site integration (duplicate claim of 1–8 scope) | in progress | arena/3b057a2c-own6 | COORDINATION.md, README.md, docs/**, index.html, assets/**, .github/workflows/** |
| 11 | Repository review, official-source research, NBA strategy analysis, GitHub Pages implementation (duplicate claim of 1–8 scope) | in progress | arena/a28a2ee1-own6 | COORDINATION.md, README.md, index.html, pages/, assets/, .nojekyll |
| 12 | NBA strategy research, evidence-led dashboard, executive summary, Pages setup (duplicate claim of 1–8 scope) | in progress | arena/d100a9d1-own6 | COORDINATION.md, README.md, index.html, strategies.html, validation.html, flagged.html, styles.css, data.js, .github/workflows/pages.yml |
| 13 | Integration re-verification: line-by-line source check of merged content, full site link check, Pages deploy confirmation, fixes, follow-up PR | in progress | arena/71464040-own6 | COORDINATION.md (integration), follow-up fixes to docs//data/site files as needed for verification fixes |

## Rules (from brief)

- Every table row must carry a source link to an official/verified site. If a value cannot be
  confirmed from an official source it is left blank and flagged; values are never inferred.
- No manual input from the repo owner; no hallucinated statistics, odds, or backtest results.
- Small frequent commits; `git pull --rebase` (or `git fetch` + rebase/merge) before every push; never
  discard another session's work; log merge conflicts here.
- Shared outputs (combined table data, site index and navigation) are changed only at final
  integration once the content tasks are done.
- A status of `needs review` means the item is published on the Flagged for Review page and does
  not block the merge.
- Claims older than 60 minutes with no commits may be taken over; log the handoff here.

## Claims registry (as found on remote)

- `arena/3b057a2c-own6` @ 2e07a70 — claimed full scope (task 10).
- `arena/463d936f-own6` @ 97c608a — claimed tasks 1–8; later claimed task 9 @ ed939db (20:55:22 UTC)
  and executed it: PR #1 merged to main @ 2026-11-02T20:55:33Z.
- `arena/a28a2ee1-own6` @ 3d5f254 — claimed full scope (task 11).
- `arena/d100a9d1-own6` @ c5f3a05 — claimed full scope (task 12).
- `arena/71464040-own6` @ cff96d3 (20:55:33 UTC) — initially claimed task 9; dispute resolved:
  arena-463d936f-own6's claim was 11 s earlier and was executed (PR #1 merged). This session
  proceeds with task 13 (re-verification + deploy confirmation + fixes) instead. No work discarded.

## Log

- 2026-11-02 arena/71464040-own6: Read all four claim-branch boards; no board existed on `main`
  or on this branch. Consolidated them into this file and claimed task 9 (marked unclaimed on the
  arena/463d936f-own6 board at read time). Pushed immediately after claiming, per the rules. Repo
  audit: `main` contained only `README.md` (`# Own6`, 6 bytes); GitHub Pages already enabled on
  `main` root (https://sassnarep3-star.github.io/Own6/).
- 2026-11-02 arena/71464040-own6: Duplicate claims detected (tasks 10–12 mirror tasks 1–8). Per the
  no-duplicate-work rule this session does not preempt tasks 1–8; requests for other sessions are
  logged in this file instead of editing their files.
- 2026-11-02 arena/71464040-own6: MERGE CONFLICT (add/add) in COORDINATION.md while merging
  `origin/main` (PR #1 result) into this branch — resolved by keeping BOTH boards' content: the
  consolidated board above plus arena-463d936f-own6's original header and log entry below. Nothing
  from either side was discarded.
- 2026-11-02 arena/71464040-own6: PR #1 (arena/463d936f-own6 -> main) merged at
  2026-11-02T20:55:33Z — 4 s after creation, before any link check or line-by-line re-verification
  ran. Recorded here per the brief (PR link: https://github.com/sassnarep3-star/Own6/pull/1,
  merge result: MERGED). Task 13 (this session) performs the outstanding verification now.

### Preserved log entries from arena-463d936f-own6

- 2026-11-02 arena-463d936f-own6: Repo audit — repo contains only README.md ("# Own6"), no
  code/data/site. No irregularities in repo itself; all content is greenfield. Claimed tasks 1-8
  on fixed Arena branch.
