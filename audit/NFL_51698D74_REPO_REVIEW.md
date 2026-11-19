# NFL Pack 51698d74 — Repo Review (2026-11-19)

**Session:** `51698d74` · **Branch:** `arena/51698d74-own6` · **Base:** `ffbbce6` (= `origin/main` at claim)
**Method:** line-by-line review of the repo at claim time; every finding below cites a file or an
official page. No value in this pack is inferred; blanks stay blank.

## 1. What the repo is

An evidence-first research repository. The NFL program (origination, validation, injury/depth,
leaderboard) lives in `docs/nfl-*` packs + `data/nfl_*` + `src/nfl_*` + `scripts/build_nfl_*` +
`scripts/check_nfl_*` + `tests/test_nfl_*` + `.github/workflows/nfl-*-ci.yml`. Preserved NBA and
housing research sits alongside. The root `index.html` is the NFL decision dashboard; `docs/index.html`
is the section hub; `README.md` is the portal. **Nothing in the repo demonstrates a profitable NFL
edge** — this pack changes nothing about that.

## 2. Prior-pack state at claim time (verified, not assumed)

- Latest merged pack: `a67ddef8` (PR #122, merge `ffbbce6`). Its capture (2026-11-19): standings
  32 clubs (149/149/2, PF=PA=6,923), reg11 injuries 253 rows + 2 markers, Week-11 venues 13/13,
  Week-12 venues 1/16, reserve window 11/10–11/18 (25 rows).
- Origination state (0ce967db): 150-game corpus reconciled 32/32; 13 Week-11 fair lines
  (side→total→moneyline, market blank by policy); leaderboard 0 qualified (all Brier-skill lower
  bounds negative); realised home margin −0.53 vs registered +2.5.
- Open PRs at claim: #113, #111, #110, #94, #84 (other sessions; stale, not taken over).

## 3. Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| 516-RF01 | info | No blocking repo defect at claim time; prior gates green | `ffbbce6` merge; a67ddef8 completion record |
| 516-RF02 | low | 15+ overlapping session packs with separate evidence boundaries | `docs/` listing; README warning |
| 516-RF03 | low | Open PRs #113/#111/#110/#94/#84 stale (>60 min, no commits) | `gh pr list` at claim |
| 516-RF04 | medium | No market price on any official NFL page | [NFL terms](https://www.nfl.com/legal/terms/) |
| 516-RF05 | medium | Depth-order source unresolved for all 32 clubs | [Texans](https://www.nfl.com/teams/houston-texans/) image-only; [Packers](https://www.nfl.com/teams/green-bay-packers/) jersey prefixes |
| 516-RF06 | low | Houston game centres carry legacy RELIANT STADIUM (Wk11 + Wk12) | [IND@HOU](https://www.nfl.com/games/colts-at-texans-2026-reg-11), [BAL@HOU](https://www.nfl.com/games/ravens-at-texans-2026-reg-12) |
| 516-RF07 | low | Week-12 SNF/TNF headings contradict game lines | [week-12 schedule](https://www.nfl.com/schedules/2026/by-week/week-12) |
| 516-RF08 | info | Shared inventories regenerate at integration (tool-only) | `scripts/build_assurance.py`, `scripts/audit_sources.py` |

## 4. What this session verified (recomputed, not restated)

- Standings arithmetic from fresh read: W=L=149, T=2, PF=PA=6,923; corpus totals match exactly.
- Week-10 Monday settlement: LAC 23, BAL 20 FINAL (margin −3, total 43).
- Realised home margin: −79/150 = −0.5267 (published −0.53).
- 13/13 Week-11 fair lines recomputed with the frozen S01 forecaster (max |Δmargin| 0.0045).
- 8/8 leaderboard Brier values recomputed from `model_outputs.csv` (control Brier 0.254094).
- 4 official-only correlations with n=150 and Fisher 95% CIs.
- 16/16 Week-12 venues from game-centre fields (11 exact / 3 mismatch / 2 variance vs hotel params).
- Reserve list: 25 rows, window 11/10–11/18, re-read.

## 5. Irregularities flagged for review (non-blocking)

See `data/nfl_51698d74/flagged.csv` (516-F01..F12) and the Flagged for Review page
(`docs/nfl-51698d74/flags.html`). Headlines: venue mismatches (3/16 Week-12), legacy RELIANT on
the authoritative source, reserve render window, IR-with-blank-status, Week-12 heading errors,
depth-source gap, missing inactives/snaps/Game Books, uncalibrated Questionable, no roof/weather
overlay, no weekly diff yet, unestimated kickoff-regime priors.

## 6. Gates run this session

- `scripts/check_nfl_51698d74.py` — 21 rules OK (559 data rows, 6 pages).
- `tests/test_nfl_51698d74.py` — 19 tests OK.
- Determinism: data + registers + recompute + site rebuilds reproduce committed bytes.
- CI: `.github/workflows/nfl-51698d74-ci.yml` (rebuild → diff → build → diff → verify → tests).
