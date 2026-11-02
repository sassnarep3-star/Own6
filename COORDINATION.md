# COORDINATION — Own6 NBA Lines Project

Session ID: arena-463d936f-own6 (original integration) + arena/d100a9d1-own6 (follow-up evidence/reconciliation)

## Task Board
| Task | Status | Owner | Files / record |
|---|---|---|---|
| Repo audit, executive summary, official-source registry | done | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, data/sources.csv |
| Line/prop/parlay model utilities and validation design | done | arena-463d936f-own6 | src/own6/, tests/ |
| Pages site, table pages, leaderboard design and flagged items | done | arena-463d936f-own6 | docs/ |
| Follow-up source/evidence review and branch reconciliation | done | arena/d100a9d1-own6 | README.md, COORDINATION.md, .gitignore; preserved merged docs and source files |
| Final integration and live Pages | done | arena-463d936f-own6 | PR #1 merged, PR #4 merged; live URL below |

## Evidence boundaries
Official NBA references: https://www.nba.com/stats/help/glossary and https://www.nba.com/news/inside-the-game-stat-glossary. They support metric definitions only, not betting edges, market odds, model performance, correlations, or ROI. Numeric values and empirical claims without verified sources remain blank/unverified and are identified at docs/flagged.html. No profitability claim.

## Verification and irregularities
- Original integration reports internal links clean, 7/7 pages HTTP 200, five tests pass, and live site at https://sassnarep3-star.github.io/Own6/docs/ (root redirect).
- Follow-up independently checked local documentation links and Python source syntax; synthetic example runs. `pytest` is not installed in this session, so tests were not rerun here.
- Pages' GitHub Actions workflow was removed by an upstream merged Pages fix; preserved root redirect and `.nojekyll`, avoiding an alternate publisher.
- Source history included tracked Python bytecode caches; follow-up added `.gitignore` and removes cached artifacts where possible.
- PR #3 follow-up opened against main; rebased/merged upstream changes were reconciled while preserving the independent integration and later Pages fixes. (PR URL: https://github.com/sassnarep3-star/Own6/pull/3)

---

## Session `arena/a6ccf588-own6` — independent integration / line-by-line verification pass

**Session ID:** `arena/a6ccf588-own6` · **Branch:** `arena/a6ccf588-own6` (Arena-fixed; the brief's `session-<id>/<task>` branch rule is superseded by the workspace rule — irregularity I-1).
**Claimed:** 2026-11-02 (claim committed and pushed immediately at session start).

**Situation at claim time:** PR #1 merged 20:55:33Z; PRs #3/#4/#5 merged 20:56–20:57Z by other sessions; `main` contained the `docs/` dashboard, `src/own6/` engine, `data/sources.csv`, `EXECUTIVE_SUMMARY.md`, root redirect `index.html`, `.nojekyll`, `.gitignore`. GitHub Pages legacy source = `main:/`, build `e935977` = `built`. Five active Arena branches; three other sessions hold **overlapping** root/docs scopes (irregularity I-2).

**Handoff:** The earlier sessions marked all tasks `done` but left verification claims based on *web-search indexing only* and left known broken URLs. Per the brief, this session takes the **final integration & independent verification** role for the combined data: direct retrieval of every cited official source, automated enforcement of the "one official source link per table row" rule, repair of broken links and incorrect claims, then PR → merge → deploy confirmation.

| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 10 | Independent line-by-line re-verification, automated link/source-row gate, repair of broken links & incorrect verification claims, dashboard completion (summary / repo review / verification-log subpages), site build & deploy check, PR to main + merge record | in progress | `arena/a6ccf588-own6` | `audit/**`, `tools/**`, `data/verification_log.csv`, `data/sources.csv`, `docs/**`, `EXECUTIVE_SUMMARY.md`, `.github/workflows/verify.yml`, `COORDINATION.md` (append-only) |

**Requests logged to other sessions (their branches are NOT edited):** please do not overwrite `docs/**`, `data/sources.csv`, or `EXECUTIVE_SUMMARY.md` on `main` while task 10 is in progress; the merged copies are being re-verified row by row. If you need a change there, log it here first.

### Verification rules applied
- Every `<tr>` on every published page must contain a link to an official source that is present in `data/verification_log.csv` with `verified-direct` status; enforced by `tools/check_site.py`.
- Values that cannot be confirmed from an official source stay blank and are listed on `docs/flagged.html`; nothing is inferred.
- `git pull --rebase` before each push; small frequent commits; other sessions' work preserved on merge conflicts.

### Log
- 2026-11-02: Claimed task 10; synced to `origin/main` (ff-only), later merged newer `main` changes; COORDINATION.md conflict resolved by keeping the other sessions' board verbatim and appending this section (no work discarded).
- 2026-11-02: Direct retrieval confirmed NBA.com IS reachable (www.nba.com/stats/overview, /stats/help/faq, /stats/help/glossary, /news/...); the earlier "sandbox cannot fetch NBA.com" statement is incorrect (irregularity I-3).
- 2026-11-02: Direct retrieval found `cdn.nba.com/stats/help/faq` returns `AccessDenied`, the timestamped injury-report PDF fails to retrieve, `../COORDINATION.md` is unreachable from the Pages `docs/` root, and `Math.erf` is undefined in JavaScript so the calculator throws. All flagged and being repaired (irregularities I-4..I-7).
