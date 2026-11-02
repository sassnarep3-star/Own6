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

---

## Session `arena/a6ccf588-own6` — independent integration / verification pass (claimed 2026-11-02)

**Session ID:** `arena/a6ccf588-own6` · **Branch:** `arena/a6ccf588-own6` (Arena-fixed; the brief's `session-<id>/<task>` branch rule is superseded by the workspace rule — see irregularity I-1).

**Situation at start:** PR #1 (`arena/463d936f-own6` → `main`) was already MERGED at 2026-11-02T20:55:33Z; GitHub Pages build `28ef7066` was still `building`. Remote `main` contains a complete site in `docs/`, engine in `src/own6/`, `data/sources.csv`, `EXECUTIVE_SUMMARY.md`, and `.github/workflows/pages.yml`. Three other sessions (`arena/a28a2ee1-own6`, `arena/d100a9d1-own6`, `arena/3b057a2c-own6`) hold **overlapping, unclaimed-against-main** scopes on their own branches (COORDINATION.md/README.md/docs/**, index.html), which is an irregularity (I-2). Their branches currently contain only `COORDINATION.md` + `README.md`.

**Handoff note:** Task 9 (final integration / link check / re-verify / deploy) was left `in progress` by `arena-463d936f-own6` even though its PR merged. Per the brief's integration rule, this session acts as the **final integration & independent verification session** for the already-published combined data. No other session's in-progress *content* branch is modified; all repairs below are to files already merged into `main`, done only to fix verification failures and broken links.

### Claimed task (integration scope; disjoint from other sessions' *new* work)
| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 10 | Independent line-by-line re-verification of merged data/site, automated link + source-row gate, repair of broken links & incorrect verification claims, site completion (summary/audit/repo-review subpages), final build/deploy check, PR #2 + merge record | in progress | `arena/a6ccf588-own6` | `audit/**`, `tools/**`, `data/verification_log.csv`, `.gitignore`, `docs/**`, `data/sources.csv`, `EXECUTIVE_SUMMARY.md`, `COORDINATION.md` (append-only), `.github/workflows/pages.yml` |

**Request logged to other sessions (not editing their branches):** please do not overwrite `docs/**`, `data/sources.csv`, or `EXECUTIVE_SUMMARY.md` on `main` while integration pass 10 is in progress; the merged copies are being re-verified row by row.

### Rules honoured
- Every table row on the site must carry a link to an official source; unconfirmable values stay blank + flagged.
- No numeric NBA value, odd, correlation, or backtest result is inferred or filled in.
- `git pull --rebase` before every push; small frequent commits; other sessions' work is never discarded.

### Log
- 2026-11-02: Claimed task 10. Synced `arena/a6ccf588-own6` to `origin/main` with `git merge --ff-only` (no branch switch). Beginning direct source retrieval.
