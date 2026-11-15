# NFL Own-Lines Requirements Closure Pack (8362b702) — Executive Summary

Session: `8362b702` · Branch: `arena/8362b702-own6` · Claim recorded in `COORDINATION.md`
Scope: `data/nfl_8362b702/**`, `src/nfl_8362b702/**`, `docs/nfl-8362b702/**`,
`scripts/{build,check}_nfl_8362b702.py`, `tests/test_nfl_8362b702.py`,
`.github/workflows/nfl-8362b702-ci.yml`, this file, `audit/NFL_8362B702_REPO_REVIEW.md`.
Shared files are touched only at final integration (P11), per protocol.

## Why this pack exists

Surveying the repository at base `32a1b69` (PR #91) showed the merged sibling
packs own prices, correlations, depth, staleness, individual accuracy and
provenance. A cluster of the project brief's requirements was built **nowhere**:

1. the "removal of luck" panel
2. control baselines (random picks; favorites-only)
3. the availability graph as a first-class dataset
4. injury signal as a *delta between timestamped reads*, never a level
5. model-output ledger of **probability plus full input vector**
6. drift alarms pinned to scraper contracts
7. proper-score leaderboard divisions with a joint-evidence gate for combos
8. two-sided "what would change our mind" per strategy

This pack closes all eight, plus the brief's data items that were still open at
the source (the three Lions game-status designations; the reserve-list capture).

## What was captured (every value read from official pages, 2026-11-15/16 UTC)

| Read | Official page | Taken |
|---|---|---|
| Standings | nfl.com/standings/league/2026/REG | 32 club rows, all columns verbatim |
| 136-game log | nfl.com/schedules/2026/by-week/week-1..9 | weeks 1-9 FINAL cards = the corpus |
| Week 10 | .../week-10 | 9 FINAL results + 3 live/2 scheduled cards logged as **not** results |
| Week 11 | .../week-11 | 13 fixtures + 6 byes; kickoffs/networks verbatim |
| Injury hub | nfl.com/injuries/ | 155 player rows / 13 clubs, read clocked 23:58Z |
| GB roster | nfl.com/teams/green-bay-packers/roster/ | 41 non-ACT rows; reserve sections |
| Game centre | nfl.com/games/buccaneers-at-lions-2026-reg-11 | venue: Ford Field, Detroit, MI |

## Numbers a reviewer can re-check in one line

- Corpus identities: **136 games · 135 decisions · 1 tie · 6246 points = 6246**
  (PF = PA) across weeks 1-9.
- Standings identities at read: sum W = 144 = sum L, T = 2, PF = 7340 = PA 7340.
- Reconciliation: corpus + week-10 finals reproduce the standings read exactly
  for every club with no unfinished week-10 card (**22 matches, 0 mismatches**;
  10 clubs legitimately not comparable mid-week-10).
- Pre-registered model S8362-SHADOW-v1: HFA = 0.055 pts (mean home margin over
  134 non-neutral corpus games), sigma = 10.589 (walk-forward residual sd).
  Week-11 forecasts carry probability + full inputs; the Mexico City game
  (SF home) correctly uses HFA = 0.
- Luck panel (exact binomial, p = 0.5 on decided games): **5 of 32** club
  records fall outside the 95% luck band — BUF +2.33σ, SF +2.12σ, MIA −2.33σ,
  TEN −2.33σ, LAC −2.83σ. Everything else is statistically indistinguishable
  from coin flips at this sample size — which is exactly the point of removing
  luck before believing anything.
- Drift alarms: 7 of 7 source contracts OK at build (row counts pinned).

## Decisions frozen before Week 11 TNF (2026-11-19 20:15 ET)

- S8362-SHADOW (singles-only), S8362-RANDOM (seeded coin, seed `4d5f7a92`-class
  hash of a fixed phrase), S8362-FAVORITE — all registered with rule text and
  evaluation windows in `src/nfl_8362b702/prereg.py` (registration = the commit
  that first contains it).
- **Joint-evidence gate**: game parlays, same-game parlays and prop combos are
  registered but *ineligible* — no validated joint probability and no operator
  void/push rules exist. Marginal multiplication is invalid under dependence.
- **Price policy**: no price-dependent number (ROI/CLV/settlement) is published
  anywhere in this pack; opening/closing columns stay blank until a licensed
  timestamped feed exists. Backtest numbers never appear on the leaderboard.
- Controls run on every window; the seeded coin is bit-reproducible.

## Deliberate blanks (blank = unknown, never inferred)

- All market/price/CLV/ROI cells (no official price exists — FLAG-06).
- All actual-start / replacement-named cells (NFL Game Books unreachable —
  FLAG-07). The availability graph publishes blanks, not "no deficiency".
- All leaderboard proper scores (the window has not kicked off).
- Malik Willis's roster state (absent from the roster page entirely; prior IR
  record not reproducible at this read — FLAG-03, "not listed ≠ available").

## Flagged for review (site: `docs/nfl-8362b702/flagged.html`)

- FLAG-01 high: MIN's published HOME+ROAD splits sum 7-3-0 against a W-L-T row
  of 7-2-0 — kept verbatim, identity failure published (only club that fails).
- FLAG-02 high: NFL.com Terms §1.3 — individual non-commercial use only, no
  systematic retrieval without written consent. Every read here is a single
  manual fetch with a clock; no automation runs in CI. Consent/licence is Q-01.
- FLAG-03 high: Willis unknown roster state (roster-turnover data event).
- FLAG-04 medium: GB roster row "Zach Bako-Bewele" links to slug `zach-tom`.
- FLAG-05 medium: week-1 SNF header "September 9th" vs card "Wednesday, September 9th".
- FLAG-07 high: no Game Books reachable; FLAG-08: the week-scoped injury URL 404s
  (hub + week selector is the working route); FLAG-11: JAX "resting player" rows
  carry game status Out — designation mixes rest and injury (calibration caution).

## Verification

- `python3 scripts/check_nfl_8362b702.py` — 14 numbered rules green (every row
  links an official source; every blank carries a reason; drift would fail the
  build; controls reproduce from the frozen seed).
- `python3 tests/test_nfl_8362b702.py` — 10/10 (verifier + identities +
  determinism: a second build is byte-identical).
- CI: `.github/workflows/nfl-8362b702-ci.yml` runs build → check → tests.

## Site

`docs/nfl-8362b702/` — 22 pages: decision-readiness ledger on the landing page
(one row per requirement: the gate that blocks it and the number that would
clear it), corpus, results feed + reconciliation, standings + what-changed
delta, pre-registration, model outputs, backtest (quarantined), controls,
removal of luck, leaderboard divisions, what-would-change-our-mind, injury
series + deltas, availability graph, reserve list, venues, drift, questions,
suggestions, flagged, sources, executive summary.
