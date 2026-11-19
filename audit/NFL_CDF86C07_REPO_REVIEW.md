# NFL Pack cdf86c07 — Repo Review (2026-11-19)

**Session:** `cdf86c07` · **Branch:** `arena/cdf86c07-own6` · **Base:** `e9185b3` (= `main` at claim)
**Method:** review of the repo at claim time, plus a fresh read of two official nfl.com pages. Every
value below either cites an official URL or is arithmetic on such values. Blanks stay blank.

## 1. What the repo is

An evidence-first research repository. NFL work lives in `docs/nfl-*`, `data/nfl_*`, `src/nfl_*`,
`scripts/build_nfl_*` / `scripts/check_nfl_*`, `tests/test_nfl_*` and `.github/workflows/nfl-*-ci.yml`.
Preserved NBA and housing research sits alongside. Nothing in the repo demonstrates a profitable NFL edge.

## 2. State at claim time (checked in the workspace)

- HEAD `e9185b3` = Merge PR #130 (`arena/ade166a4-own6`); working tree clean.
- Latest packs: `ade166a4` (PR #130), `51698d74` (PRs #125, #129). Their standings CSVs were used as
  an independent cross-check (see §4).
- Root `index.html` is the NFL decision dashboard for prior packs; this pack publishes its own landing
  page at `docs/nfl-cdf86c07/` and does **not** edit the shared root index or README (not in claimed scope).

## 3. Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| CDR-01 | info | No blocking repo defect at claim time | `git status` clean at `e9185b3` |
| CDR-02 | medium | No official NFL page publishes a betting line; market columns cannot be filled | [NFL odds path returns 404 per prior packs](https://www.nfl.com/odds/); [NFL legal terms](https://www.nfl.com/legal/terms/) |
| CDR-03 | medium | Corpus size differs across packs (136 in the brief/log; 150 recomputed from standings) | [standings](https://www.nfl.com/standings/division/2026/reg); `data/nfl_51698d74/standings_2026_11_19.csv` |
| CDR-04 | low | Standings H1 renders template tokens | [standings](https://www.nfl.com/standings/division/2026/reg) — flag CDF-01 |
| CDR-05 | low | Week-11 'International Game' header sits over a game with no printed venue | [Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) — flag CDF-02 |

## 4. What this session verified

- **Standings (32 clubs):** fetched from the official page; every row carries a source link.
  Arithmetic checks: PCT = (W + T/2)/G to 3 dp (all 32 rows), Net = PF − PA (all 32 rows),
  league W = L = 149, T = 2, PF = PA = 6,923.
- **Independent cross-check:** all 32 rows of W, L, T, PF, PA and net match the prior pack's
  standings CSV (`data/nfl_51698d74/standings_2026_11_19.csv`) exactly. This is a comparison against a
  different transcription, not a substitute for the official page.
- **Week-11 slate (13 games, 6 byes):** every printed record matches the standings for that club;
  the 26 playing clubs and 6 byes partition all 32 clubs.
- **Dated schedule announcement:** the TBD note on the Week-11 page (Weeks 16–18 dating) is transcribed.
- Verifier `scripts/check_nfl_cdf86c07.py` (all rules pass); tests `tests/test_nfl_cdf86c07.py` (7 pass,
  including two seeded-defect tests that must fail when a value is corrupted).

## 5. Not verified in this session (stated, not claimed)

Game-centre venues, injury reports, depth charts, inactives, snap counts, Game Books, roof/weather,
transactions and any betting market were **not** fetched this session. Their requirement rows are
marked `blocked` or `partial` with the prior pack named, and no value from them appears here.

## 6. Gates run this session

- `python3 scripts/build_nfl_cdf86c07.py` then `git diff` determinism (CI step).
- `python3 scripts/check_nfl_cdf86c07.py` → OK.
- `python3 -m pytest -q tests/test_nfl_cdf86c07.py` → 7 passed.
