# NFL Pack a67ddef8 — Executive Summary

**Session:** `a67ddef8` · **Branch:** `arena/a67ddef8-own6` · **Read date:** 2026-11-19 (UTC)
**Scope:** official-source capture for the 2026 NFL season through the Week 12 slate,
flag re-testing of inherited findings, and reverification of prior packs' published rows.

Site: [`docs/nfl-a67ddef8/`](docs/nfl-a67ddef8/index.html) ·
Decision readiness: 60 rows in [`data/nfl_a67ddef8/requirements.csv`](data/nfl_a67ddef8/requirements.csv) ·
Flagged (non-blocking): 12 rows in [`data/nfl_a67ddef8/flagged.csv`](data/nfl_a67ddef8/flagged.csv)

---

## 1. What was captured (all from official pages, 2026-11-19)

| capture | rows | source |
|---|---:|---|
| Standings, all 32 clubs (W-L-T/PCT/PF/PA/Net/Strk) | 32 | [nfl.com standings](https://www.nfl.com/standings/division/2026/reg) |
| Week 10 finals (incl. Monday LAC 23–20 BAL) | 14 | [week-10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) |
| Week 11 slate + game-centre venues | 13 | [week-11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) + 13 game centres |
| Week 12 slate (venues blank except DEN@PIT) | 16 | [week-12 schedule](https://www.nfl.com/schedules/2026/by-week/week-12) |
| Week 11 injury report (full register) | 253 + 2 markers | [reg11](https://www.nfl.com/injuries/league/2026/reg11) |
| November reserve list (render window 11/10–11/18) | 25 | [reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11) |
| Depth-chart re-tests (Ravens / Texans / Packers) | 3 pages | club sites |
| 2026 rulebook re-test | 1 page | [operations.nfl.com](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) |

Capture honesty: 13 `capture_log.csv` rows, each `sha256` over the transcription artifact
bytes only — the log states on every row that the hash **cannot prove what the page said**.
`read_on_utc` is the artifact-write clock (upper bound on the fetch).

## 2. Headline numbers (reconciled, not restated)

- **149 W / 149 L / 2 T** across **150 games**; **PF = PA = 6,923** (league identity holds).
- README snapshot (2026-11-13): 136/136/2 and **6,291** PF → +13 Week-10 games (+632 pts)
  = today's totals. Verified arithmetic, not a copy.
- corpus_150: 150 rows, one tie (`2026-W05-09`), 149 margins sum −76 (mean −0.5101);
  with settled `W10-14` (−3): −79/150 = **−0.5267 → the published −0.53 home-field figure**.
- Week 11: 13 games, 6 byes (ATL CLE GB LAR NE SEA), MNF CIN@WAS;
  all 13 venues now come from **game-centre Location/Stadium fields** (brief-compliant).
- Week 11 injuries: **253 player rows**, 13/13 games, CIN/WAS "No Injuries Reported";
  16 game statuses (all Thursday IND@HOU) — Sunday/Monday blanks are cadence, not gaps.

## 3. Flag re-tests (24 inherited findings, live re-read)

| outcome | count | examples |
|---|---:|---|
| **closed / confirmed / corroborated** | 14 | F-01 Week-11 report published · F-13 LAC 23–20 FINAL · VR-08/12 Lions all Out · VR-17/26 Ravens QB = Brissett (no Lamar/Huntley) · NFL-F25 2026 rulebook live · VR-24/25 Lock & Beck start headlines |
| **still open** | 7 | 48217-F15 Lamar reserve row · F-06/N6F-12 Lamar 6-9 vs 6-10 · F-21 Texans image-only depth · 48217-F12 Packers jersey prefixes |
| **reinforced / partial / superseded / not-retested** | 3+ | VQ-06 Willis absence (second concrete case) · F-02 venue source superseded by game centres · B-05 Cardinals depth not retested |

## 4. New flags this session (12, all `blocking_merge=no`)

1. **A67-F01/F02 (venue)** — hotel params stale on 3 fixtures (NRG/FedEx/Heinz) **and** the
   game centre itself shows legacy `RELIANT STADIUM` for IND@HOU. Both values published side by side.
2. **A67-F03 (transactions)** — reserve list renders only 11/10–11/18; pre-window moves
   unverifiable (sharpens 48217-F15 into a render-window problem).
3. **A67-F04 (designations)** — Al-Shaair & Carlies are IR (11/17) yet show **blank** game
   status on reg11 while 16 peers carry Out/Questionable.
4. **A67-F05** — both Lamar recovery windows still live on the official rail.
5. **A67-F06/F07** — Texans image-only depth; Packers jersey prefixes + 9-day-stale footer.
6. **A67-F08** — Week-12 headings ("Sunday Night Football, November 26th" over a Thursday
   game; "Thursday Night Football, November 27th" over a Friday game).
7. **A67-F09** — DEN@PIT week-12 injury panels "not available at this time" (expected cadence).
8. **A67-F10** — official page mixes `LAR`/`LA` for the Rams.
9. **A67-F11** — reserve-list absence still cannot support availability claims (VQ-06 case 2).
10. **A67-F12** — blank Sunday/Monday game statuses recorded as cadence, not missing data.

## 5. Reverification of prior published rows (15 tests)

11 exact matches, 1 improved, 2 changed-by-time (report published; depth chart updated),
1 corroborated (AZ trade notes), 1 partial (venue cross-check). Full table:
[`data/nfl_a67ddef8/reverification.csv`](data/nfl_a67ddef8/reverification.csv).
Key identity re-derived independently: **6,246 (W1–9) + 45 (Thu) + 632 (13 games) = 6,923**.

## 6. Repo review

[`audit/NFL_A67DDEF8_REPO_REVIEW.md`](audit/NFL_A67DDEF8_REPO_REVIEW.md) — 1,304 files /
132,095 lines scanned; gates re-run this session: **521 unit tests OK** (502 prior + 19 new),
`check_site` OK, `tools/release_gate.py` 0 issues, `check_assurance` 21,229 rows OK,
`check_nfl` 13 pages 0 issues, pack checker 15 rules OK, dfc0c1bc fixed point 15 rules OK.
No blocking repo defect; all findings are upstream data-quality issues.

## 7. Decision-readiness snapshot

- **60 requirements** tracked with blocking gate + clearing number
  ([`requirements.csv`](data/nfl_a67ddef8/requirements.csv), rendered on the pack landing page).
- **Done this session:** 31 · **prior packs verified/reverified:** 24 ·
  **partial/open:** 3 · **integration-time gates:** 5 (PR, merge, Pages, COORDINATION, site link check).
- **8 suggestions**, all `pending_human_choice=yes` — nothing implemented without a human decision.
- **12 questions** (10 open, 2 answered).

## 8. Honesty rules enforced by the checker

`scripts/check_nfl_a67ddef8.py` (15 rules): pinned row counts · official-host URLs on every
data row · standings/injuries/slate arithmetic · no market prices or return claims ·
no inputs/selects/buttons · no placeholders · internal links resolve · gates+clearing numbers
non-empty · suggestions undecided · capture-log sha256 verification · deterministic rebuild ·
exactly six pages · non-empty retest findings. Determinism also enforced in CI
(`.github/workflows/nfl-a67ddef8-ci.yml`).

## 9. What a human should decide next (suggestions register)

1. Normalize venue strings in a derived column (keeps both raw values).
2. Capture the remaining 15 Week-12 game-centre venues next session.
3. Add reserve-list render-window fields (start/end date) to the capture log.
4. Publish both Lamar windows side by side until one retracts.
5. Treat blank game-status as an explicit `Pending` state downstream.
6. Ask the Texans club for a text depth chart (closes three inherited flags).
7. Add a weekly game-centre-vs-hotel venue diff to the checklist.
8. Re-test B-05 (Cardinals depth) to finish the flag-recheck matrix.

## 10. Sources

All 28 sources with last-read dates: [`data/nfl_a67ddef8/sources.csv`](data/nfl_a67ddef8/sources.csv)
(published at [`docs/nfl-a67ddef8/sources.html`](docs/nfl-a67ddef8/sources.html)).
Primary hosts: `nfl.com`, `operations.nfl.com`, club sites. Hotel affiliate params are
labeled `third-party-linked` and used **only** as cross-checks, never as venue sources.
