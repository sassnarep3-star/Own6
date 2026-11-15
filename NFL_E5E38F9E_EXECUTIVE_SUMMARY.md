# NFL Executive Summary — evidence pack e5e38f9e (2026-11-15)

**Bottom line.** This pack shows no profitable NFL edge, and it publishes no ROI, CLV, market price or leaderboard winner. The repository lacks an official price source, a complete Week 10 results feed, official inactive or snap data, and any capture that repeats over days. Most brief requirements are either not built or blocked by those gaps. The next decisions are owner decisions, listed below.

Site: https://sassnarep3-star.github.io/Own6/docs/nfl-e5e38f9e/ (landing with the decision-readiness table; sources in `docs/nfl-e5e38f9e/`).

## 1. Where the brief stands (76 items, one row each)

| Status | Count | Meaning |
|---|---:|---|
| Built and checked | 10 | Artifact exists and a checker or test covers it |
| Partly built | 29 | Artifact exists; a named part is missing (includes 5 rows marked `partial`) |
| Not built | 28 | No artifact, or no source to build it from |
| Blocked by an outside source | 4 | Needs a source the sandbox cannot reach or no official source publishes |
| Needs an owner decision | 1 | Policy or licence choice |
| Rejected approach not used | 3 | Jersey order, season ROI ranking, and the like |
| Pending integration | 1 | This PR and merge |

Full table with the blocking gate and the number that clears each row: `data/nfl_e5e38f9e/brief_trace.csv` and the landing page.

## 2. What was verified this session (official pages only)

- **Week 10 schedule** (`https://www.nfl.com/schedules/2026/by-week/week-10`, read 2026-11-15, 2 chunks): 14 games. Nine printed Final: WAS 24–NYG 21, NE 10–DET 35, KC 35–ATL 13, HOU 24–CLE 27, MIN 30–GB 10, MIA 22–IND 24, CAR 20–NO 17, BUF 31–NYJ 12, JAX 40–TEN 23. Three were live (LAR–AZ, SEA–LV, SF–DAL) and two not started. Bye clubs: CHI, DEN, PHI, TB.
- **Week 10 injury report** (`https://www.nfl.com/injuries/`, read 2026-11-15, chunk 0 of 8): 44 rows for WAS, NYG, NE and DET. Kerby Joseph, Cade Mays and D.J. Reed are printed Out, so the three blank Lions designations in the brief are now confirmed.

## 3. Findings to review (16 flags; none blocks the merge)

1. **Eight final Week 10 games are missing from every results feed that holds Week 10** (E5-F01). The d966 feed has one Week 10 game, and a411fed0 has none. Any ROI on those feeds is computed on an incomplete corpus.
2. **Designation errors in two packs** (E5-F02): nfl_wk and 309921cc print Kerby Joseph as practicing in full when the official page says he did not practice; they also mismatch Sione Vaki and Amon-Ra St. Brown.
3. **Injury row counts disagree across packs** (E5-F04): 326 rows in 309921cc and nfl_wk, 347 in a411fed0 and d966f630, 50 in nfl_market. No pack has 254 or 279 injury rows (the digits occur only as row IDs such as INJ-254); the brief's counts are not reproduced. The official total is not counted here.
4. **Backtest units appear on a combined leaderboard** (E5-F05): `leaderboard_combined.csv` carries units and drawdown beside the signal rank, and the d966 leaderboard page publishes them. The brief forbids this.
5. **A strategy is marked live with no price** (E5-F06): D966-STR-01 is recorded as `live` (effective 2026-11-14) while the same pack has no market price to settle it. The demotion gate should return it to paper.
6. **Third-party prices labelled "verified"** (E5-F16): nfl_f4 holds 168 DraftKings Week 10 prices from an ESPN odds endpoint, marked verified. nfl_market states that a third-party book would breach the official-source-only rule and leaves its cells blank. The packs disagree; this pack publishes no price.
7. **Depth coverage is 28 of 32 clubs, and the 4 missing are bye clubs** (E5-F08). The Texans depth chart is an image and was not read (earlier-pack note; not re-verified this session).
8. **Joseph Ossai (NYJ) has conflicting designations** across packs (E5-F15). The NYJ block was not read.
9. **The brief's VR-/VQ- review identifiers appear nowhere in the repo** (E5-F14), so references to them cannot be traced.
10. **No automated or hashed capture exists** (E5-F03). The sandbox allowlist excludes nfl.com, so no script here can read it; the page-fetch tool can, but it is not scriptable.
11. **No inactive, snap-count, injured-reserve, transaction or game-book data** (E5-F07, E5-F12). Designation play rates and the "Questionable" calibration cannot be measured.
12. **One season only, no holdout** (E5-F13). Walk-forward and holdout claims rest on 2026 weeks 1–10.

## 4. Decisions only the owner can make

| Decision | Why it blocks | Suggestion |
|---|---|---|
| Price-data source and licence (Q-E5-01) | No official price exists; one pack uses third-party prices labelled verified | E5-S11 |
| Demote STR-01 to paper until a dated price exists (Q-E5-03) | Live state without evidence | E5-S03 |
| Remove backtest units from the public combined leaderboard (E5-F05) | Brief forbids it | E5-S02 |
| Canonical NFL pack (Q-E5-04) | Ten overlapping packs disagree | E5-S04 |
| Public vs private raw-data layer; NFL terms (Q-E5-05) | Raw rows are public now | E5-S06 |
| Whether a scheduled nfl.com capture is permitted (Q-E5-11) | Multi-day snapshots need it | E5-S05 |
| Depth route: per-club pages or snap counts (Q-E5-09) | Route (a) needs an authorised Texans source | — |
| Holdout seasons (Q-E5-10) | Only one season exists | — |

## 5. What any session can finish without an owner (self-serveable)

- Read the eight missing Week 10 finals and Weeks 1–6 from official schedule pages (Q-E5-08).
- Read all eight chunks of the Week 10 injury report to get the full row count (Q-E5-06).
- Read the NYJ block to settle Joseph Ossai (Q-E5-07).
- Read the 28 remaining club depth pages (Q-E5-09).

## 6. Limits of this pack

- Official values come from two official pages read this session (see `docs/nfl-e5e38f9e/sources.html`). Game-centre pages, the Texans depth image, and the NYJ block were not read.
- The sandbox cannot reach nfl.com from scripts. Every official value here was typed from a fetch-tool read, with its URL and read date beside it, and was not taken from memory.
- The brief's requirements were traced against the repo as committed at `32a1b69`. Items marked "built" mean an artifact and a check exist, not that the result is correct.
- Nothing here is an edge, a profit, or a recommendation to bet.

## 7. Files

- `data/nfl_e5e38f9e/` — `brief_trace.csv`, `official_w10_finals.csv`, `official_injury_spotcheck.csv`, `w10_pack_reconciliation.csv`, `injury_pack_comparison.csv`, `flagged.csv`, `questions.csv`, `suggestions.csv`, `sources.csv`.
- `scripts/build_nfl_e5e38f9e.py` (builder), `scripts/check_nfl_e5e38f9e.py` (verifier), `tests/test_nfl_e5e38f9e.py` (16 tests), `.github/workflows/nfl-e5e38f9e-ci.yml`.
- Board entry: `COORDINATION.md`, section "Session `arena/e5e38f9e-own6`".
