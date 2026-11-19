# Repository Review — session a67ddef8 (2026-11-19)

Scope: line-by-line structural review of `sassnarep3-star/Own6` at branch `arena/a67ddef8-own6`
(base `65ac863`), with re-execution of the standing gates and re-verification of inherited
findings. Every claim below is either (a) reproduced by a command run this session, or
(b) linked to an official source read this session. Nothing is inferred.

Baseline (from `scripts/audit_repo.py`, re-run after `git fetch --unshallow`):

| metric | value |
|---|---|
| files scanned | 1,304 |
| lines scanned | 132,095 |
| structured records | 19,422 |
| standing findings | 17 |
| audit verdict | OK |

## 1. Structure

- 29 `data/nfl_*` pack directories plus cross-cutting dirs (`data/empirical`, `data/nfl`, …).
- Per-pack script triad where present: `scripts/build_nfl_<id>.py`, `scripts/check_nfl_<id>.py`,
  `tests/test_nfl_<id>.py`, `.github/workflows/nfl-<id>-ci.yml`.
- Site: root `index.html` (decision-readiness table RQ-01..RQ-81), `docs/index.html` hub,
  one `docs/nfl-<id>/` directory per pack, plus shared `docs/leaderboard.html`,
  `docs/correlations.html`, `docs/flagged.html`, `docs/dashboard.html`.
- 18 root `NFL_*_EXECUTIVE_SUMMARY.md` files; this session adds the 19th
  (`NFL_A67DDEF8_EXECUTIVE_SUMMARY.md`).
- Working fixed-point sequence for shared-file changes:
  `build_nfl_dfc0c1bc.py` → `audit_repo.py` → `build_assurance.py` → `source_coverage.py`.
  (`scripts/build_review.py` does not exist — do not run it.)

## 2. Gates re-executed this session (all green)

| gate | command | result |
|---|---|---|
| unit tests | `python3 -m pytest -q tests/` | **502 passed** |
| site structure | `python3 scripts/check_site.py` | OK |
| release gate | `python3 scripts/release_gate.py` | exit 0 |
| NFL pack checks | `python3 scripts/check_nfl.py` | 13 pages, 0 issues |
| assurance | `python3 scripts/check_assurance.py` | OK, 21,229 rows |
| source coverage | `python3 scripts/source_coverage.py --check` | pass (manifest `234d57ba…`) |
| repo audit | `python3 scripts/audit_repo.py` | OK (after unshallow) |
| dfc0c1bc fixed point | 4-script sequence | **15 rules OK, 0 failures** |

## 3. Irregularities found / re-confirmed (with links)

New this session:

1. **Venue provenance split** — game-centre `Stadium` fields disagree with schedule-page
   hotel-affiliate params on 3 of 13 Week-11 fixtures (RELIANT/NRG, NORTHWEST/FedEx,
   ACRISURE/Heinz). One direction of staleness is on the *authoritative* page itself
   (RELIANT vs current NRG). → `data/nfl_a67ddef8/flagged.csv` A67-F01/F02.
   Sources: [IND@HOU](https://www.nfl.com/games/colts-at-texans-2026-reg-11),
   [CIN@WAS](https://www.nfl.com/games/bengals-at-commanders-2026-reg-11),
   [DEN@PIT](https://www.nfl.com/games/broncos-at-steelers-2026-reg-12).
2. **Reserve-list render window** — November table shows only 11/10–11/18 (25 rows, no
   pagination). Pre-11/10 moves are neither confirmable nor deniable.
   → A67-F03. Source: [reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11).
3. **IR players with blank game status** — Al-Shaair and Carlies are Reserve/Injured 11/17
   yet appear on reg11 with DNP + blank game status while 16 Thursday-game peers carry
   Out/Questionable. → A67-F04. Sources: reserve list + [reg11](https://www.nfl.com/injuries/league/2026/reg11).
4. **Week-12 heading/weekday contradictions** — "Sunday Night Football, November 26th"
   over a Thursday game; "Thursday Night Football, November 27th" over a Friday game.
   → A67-F08. Source: [week-12 schedule](https://www.nfl.com/schedules/2026/by-week/week-12).
5. **Official-page abbreviation drift** — bye list prints `LAR` beside a `/LA` logo slug;
   standings/cards use `LA`. → A67-F10. Source: [week-11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11).
6. **Dual Lamar recovery windows** both live on the official news rail (6-9 vs 6-10 weeks).
   → A67-F05 (inherits F-06/N6F-12).

Inherited, re-tested, still open:

7. **Texans depth chart is image-only** (zero text rows; `texans.com` host 404s).
   → A67-F06. Source: [houstontexans.com depth chart](https://www.houstontexans.com/team/depth-chart).
8. **Packers depth chart jersey prefixes + stale footer** ("Unofficial, Nov. 10, 2026").
   → A67-F07. Source: [packers.com depth chart](https://www.packers.com/team/depth-chart).
9. **Lamar Jackson absent from November reserve table** (now explained as a render-window
   problem, not a single-row omission). → 48217-F15 + A67-F03.

Inherited, re-tested, closed this session (full table: `data/nfl_a67ddef8/flag_recheck.csv`):

10. Week-11 injury report published (F-01, S-03) — 253 rows, 13/13 games.
11. LAC 23 BAL 20 FINAL settles F-13; matches `results_feed.csv` settlement.
12. Lions Joseph/Mays/Reed all Out on reg10 (VR-08/VR-12/C-03/R-48).
13. Ravens QB group = Brissett/Fagnano/Slovis, no Lamar, no Huntley (VR-17/VR-26/F-23/B-04).
14. 2026 rulebook live with 2026 rule changes (NFL-F25).
15. All 13 Week-11 venues now come from game-centre fields, not hotel params (F-02 superseded).

## 4. Process observations

- 12 open PRs exist; #110 and #84 have failing checks — **left untouched** per standing rule.
- Pages is `built` on `main:/` legacy config; live at
  <https://sassnarep3-star.github.io/Own6/> (re-confirm with `?cachebust=` after each merge).
- `COORDINATION.md` edits invalidate `data/assurance/inventory.csv`; the fixed-point
  4-script sequence must be re-run after any shared-file change (done this session:
  commit `686fca1`, 15 rules OK).
- `audit_repo.py` requires full history (`git fetch --unshallow` on fresh clones).

## 5. Verdict

No blocking defect found in the repo itself. Site, tests, assurance, coverage and audit
gates are green. The irregularities above are data-quality findings on *upstream official
pages*; all are published on the flagged page with `blocking_merge=no`, per brief.
