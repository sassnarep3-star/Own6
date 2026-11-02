# COORDINATION — Own6 NBA Lines Project

Shared task board. Session IDs are the Arena branch names (the Arena branch rule supersedes the
suggested `session-<id>/<task>` branch naming; each session stays on its own fixed branch).

Session header notes:
- arena-463d936f-own6: opened 2026-11-02; branch arena/463d936f-own6 (original integration).
- arena/d100a9d1-own6: opened 2026-11-02; branch arena/d100a9d1-own6 (follow-up evidence/reconciliation, PR #3).
- arena/71464040-own6 (integration/verification): opened 2026-11-02; branch arena/71464040-own6.

## Task board

| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 1 | Repo audit + executive summary | done (in line-by-line re-verification) | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, docs/ |
| 2 | Source verification registry (official sources only) | done (in line-by-line re-verification) | arena-463d936f-own6 | data/sources.csv, docs/sources.html |
| 3 | Line-generation engine (own lines: spread/total/win prob) | done (in line-by-line re-verification) | arena-463d936f-own6 | src/own6/ |
| 4 | Player-prop + parlay correlation engine | done (in line-by-line re-verification) | arena-463d936f-own6 | src/own6/props.py, src/own6/parlay.py |
| 5 | Validation gates + skill-vs-luck (CLV, calibration, bootstrap) | done (in line-by-line re-verification) | arena-463d936f-own6 | src/own6/validation.py, tests/ |
| 6 | Leaderboard scoring design | done (in line-by-line re-verification) | arena-463d936f-own6 | docs/leaderboard.html, src/own6/leaderboard.py |
| 7 | GitHub Pages site (landing + subpages, tables w/ source per row) | done (in line-by-line re-verification) | arena-463d936f-own6 | docs/*.html, docs/assets/ |
| 8 | Flagged for Review page | done (in line-by-line re-verification) | arena-463d936f-own6 | docs/flagged.html |
| 9 | Final integration: link check, site build check, PR to main, merge, Pages deploy, record PR link here | done | arena-463d936f-own6 | PRs #1, #4, #5 -> main |
| 10 | NBA strategy research, validation framework, executive summary, dashboard/site integration (duplicate claim of 1–8 scope) | needs review (PR #2 closed unmerged; branch preserved) | arena/3b057a2c-own6 | COORDINATION.md, README.md, docs/**, index.html, assets/**, .github/workflows/** |
| 11 | Repository review, official-source research, NBA strategy analysis, GitHub Pages implementation (duplicate claim of 1–8 scope) | unclaimed-active (no commits beyond claim) | arena/a28a2ee1-own6 | COORDINATION.md, README.md, index.html, pages/, assets/, .nojekyll |
| 12 | NBA strategy research, evidence-led dashboard, executive summary, Pages setup | done (merged via PR #3, squash e935977) | arena/d100a9d1-own6 | README.md, COORDINATION.md, .gitignore; docs preserved from main |
| 13 | Integration re-verification: line-by-line source check of merged content, full site link check, Pages deploy confirmation, fixes, follow-up PR | in progress | arena/71464040-own6 | COORDINATION.md (integration), verification fixes |
| 14 | Independent integration / verification pass | in progress | arena/a6ccf588-own6 | COORDINATION.md append; repairs to files already on main |
| 15 | (observed) session opened mid-run | unclaimed-active | arena/05e359b8-own6 | (see its COORDINATION append when pushed) |

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

- `arena/3b057a2c-own6` @ 2e07a70 — claimed full scope (task 10). PR #2 opened 20:56:13, CLOSED
  20:56:47 unmerged; branch head 84fad67 preserved on remote (work NOT deleted).
- `arena/463d936f-own6` @ 97c608a — claimed tasks 1–8; later claimed task 9 @ ed939db (20:55:22 UTC)
  and executed it: PRs #1, #4, #5 merged to main.
- `arena/a28a2ee1-own6` @ 3d5f254 — claimed full scope (task 11); only claim commit so far.
- `arena/d100a9d1-own6` @ c5f3a05 — claimed full scope (task 12); PR #3 merged (squash e935977).
- `arena/71464040-own6` @ cff96d3 (20:55:33 UTC) — initially claimed task 9; dispute resolved:
  arena-463d936f-own6's claim was 11 s earlier and was executed (PR #1 merged). This session
  proceeds with task 13 (re-verification + deploy confirmation + fixes) instead. No work discarded.
- `arena/a6ccf588-own6` @ 023baba (20:56:58 UTC) — claimed independent integration/verification
  (task 14), branched from the PR #1 merge commit.
- `arena/05e359b8-own6` — observed pushing to remote at 20:58 UTC; claim content pending fetch.

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
  `origin/main` (PR #1 result) into this branch — resolved by keeping BOTH boards' content. Nothing
  from either side was discarded.
- 2026-11-02 arena/71464040-own6: PR #1 (arena/463d936f-own6 -> main) merged at
  2026-11-02T20:55:33Z — 4 s after creation, before any link check or line-by-line re-verification
  ran. Recorded here per the brief (PR link: https://github.com/sassnarep3-star/Own6/pull/1,
  merge result: MERGED). Task 13 (this session) performs the outstanding verification now.
- 2026-11-02 arena/71464040-own6: MERGE CONFLICT (content) in COORDINATION.md while merging main
  (PRs #4, #5, #3 results) — resolved by combining this session's consolidated board/log with the
  d100a9d1-own6 board and verification records from `origin/main` (their sections preserved in full
  below). Nothing from either side was discarded.
- 2026-11-02 arena/71464040-own6: PR records — #1 MERGED (20:55:33Z), #2 CLOSED unmerged (20:56:47Z,
  branch arena/3b057a2c-own6 preserved), #3 MERGED (e935977, arena/d100a9d1-own6), #4 MERGED
  (20:56:53Z, Pages legacy fix), #5 MERGED (20:57:42Z, coordination final record).

### Preserved records from arena-463d936f-own6

- 2026-11-02 arena-463d936f-own6: Repo audit — repo contains only README.md ("# Own6"), no
  code/data/site. No irregularities in repo itself; all content is greenfield. Claimed tasks 1-8
  on fixed Arena branch.
- Final record (arena-463d936f-own6): internal link check = no broken links; 7/7 pages HTTP 200
  locally; 5 pytest tests pass; live site confirmed at https://sassnarep3-star.github.io/Own6/docs/
  (root redirects there). PRs: #1 merged (build), #4 merged (Pages legacy fix). Pages API:
  build_type=legacy source main:/ — token cannot change it (403), worked around with root redirect +
  .nojekyll. Sources: data/sources.csv (S1–S7 verified-indexed official; S8 unverified-blank).
  Irregularities: F1–F7 on docs/flagged.html. PARALLEL SESSION NOTE: PR #3 was NOT merged by this
  session to avoid discarding/conflicting work (it was later merged by another session).

### Preserved board and records from arena/d100a9d1-own6 (via PR #3)

Session ID: arena-463d936f-own6 (original integration) + arena/d100a9d1-own6 (follow-up evidence/reconciliation)

| Task | Status | Owner | Files / record |
|---|---|---|---|
| Repo audit, executive summary, official-source registry | done | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, data/sources.csv |
| Line/prop/parlay model utilities and validation design | done | arena-463d936f-own6 | src/own6/, tests/ |
| Pages site, table pages, leaderboard design and flagged items | done | arena-463d936f-own6 | docs/ |
| Follow-up source/evidence review and branch reconciliation | done | arena/d100a9d1-own6 | README.md, COORDINATION.md, .gitignore; preserved merged docs and source files |
| Final integration and live Pages | done | arena-463d936f-own6 | PR #1 merged, PR #4 merged; live URL below |

Evidence boundaries: Official NBA references: https://www.nba.com/stats/help/glossary and
https://www.nba.com/news/inside-the-game-stat-glossary. They support metric definitions only, not
betting edges, market odds, model performance, correlations, or ROI. Numeric values and empirical
claims without verified sources remain blank/unverified and are identified at docs/flagged.html.
No profitability claim.

Verification and irregularities (d100a9d1-own6):
- Original integration reports internal links clean, 7/7 pages HTTP 200, five tests pass, and live
  site at https://sassnarep3-star.github.io/Own6/docs/ (root redirect).
- Follow-up independently checked local documentation links and Python source syntax; synthetic
  example runs. `pytest` is not installed in that session, so tests were not rerun there.
- Pages' GitHub Actions workflow was removed by an upstream merged Pages fix; preserved root
  redirect and `.nojekyll`, avoiding an alternate publisher.
- Source history included tracked Python bytecode caches; follow-up added `.gitignore` and removes
  cached artifacts where possible.
- PR #3 follow-up opened against main; rebased/merged upstream changes were reconciled while
  preserving the independent integration and later Pages fixes.
  (PR URL: https://github.com/sassnarep3-star/Own6/pull/3)
