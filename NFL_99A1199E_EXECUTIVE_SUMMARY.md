# NFL 32-Club Roster Sweep (99a1199e) — Executive Summary

Session: `99a1199e` · Branch: `arena/99a1199e-own6` · Claim: **G-SWEEP / R-13**, recorded
in `COORDINATION.md` (Task Board N99-1..N99-5).
Scope: `data/nfl_99a1199e/**`, `src/nfl_99a1199e/**`, `docs/nfl-99a1199e/**`,
`scripts/{build,check}_nfl_99a1199e.py`, `tests/test_nfl_99a1199e.py`, this file,
`audit/NFL_99A1199E_REPO_REVIEW.md`. Shared files are touched only at final integration.

## Why this pack exists

`data/nfl_8362b702/readiness.csv` marked **G-SWEEP / R-13** (32-club roster/IR sweep)
as delivered, but its own `availability_sweep.csv` was factually incomplete: 1 of 32
roster pages read, 13 of 32 hub tables read. The sweep gap was real. This pack closes
it: **all 32 official NFL club roster pages were read on 2026-11-17 UTC and transcribed
verbatim**, with every row linked to its source page and every status code stored
exactly as the publisher printed it.

## What was captured (every value read from official pages, 2026-11-17 UTC)

| Read | Official page | Taken |
|---|---|---|
| 32 roster pages | `nfl.com/teams/<slug>/roster/` (all 32 clubs) | full roster table: every row's name, position and STATUS code; reserve rows per player, ACT rows by count |
| Standings | `nfl.com/standings/league/2026/reg/` | reconnaissance read confirming the official fetch route (not part of the sweep dataset) |
| CAR re-read | `nfl.com/teams/carolina-panthers/roster/` | reconcile `total_rows` (see F99-06); all 40 reserve rows matched the first read |

The roster page renders one continuous table per club:

```
| [player](player-url) | jersey | position | STATUS | years | weight | age | college |
```

The **STATUS column is authoritative** and is stored verbatim — never expanded to an
invented meaning. Rows whose status is not `ACT` form the reserve register (captured
per player); `ACT` rows are summarised by count only, exactly as read.

## Numbers a reviewer can re-check in one line

- **Clubs swept: 32 of 32** — every club's official roster page was read.
- **Roster rows read: 2,858** = 1,715 ACT + 1,143 reserve.
- **Status codes observed (12, verbatim):** ACT, CUT, DEV, EXE, PUP, RES, RLS, RSN,
  RSR, TRC, TRD, TRT.
- **Code distribution:** ACT 1,715 · DEV 511 · RES 257 · CUT 160 · TRC 82 · TRD 58 ·
  RSR 31 · PUP 19 · TRT 17 · RSN 6 · EXE 1 (SEA) · RLS 1 (SF).
- **Flagged irregularities: 95** — 6 hand-observed + 89 cross-club repeated names
  (see `data/nfl_99a1199e/flagged.csv`).
- **Capture log: 34 rows** — 32 club reads + 2 CAR re-reads, all successful.

Per-club tallies (total / ACT / reserve) are in `data/nfl_99a1199e/roster_sweep.csv`
and on the dashboard page `docs/nfl-99a1199e/index.html`.

## What is deliberately not in this pack

- **No interpretation of status codes.** Each code is stored verbatim; none is
  expanded to an invented meaning, and the register never guesses what a code "means".
- **No merging of repeated names.** When the same name is printed on two club pages,
  each occurrence is kept on its own page and flagged for review — never reconciled.
- **No price, line, odds, ROI, CLV or profitability values anywhere** (no official
  price data exists; the verifier's rule 9 fails the build on any such value).
- **No blanks filled.** Unreadable content would ship blank with its reason; here every
  page was read successfully, so no row carries a blank.

## Irregularities (captured verbatim, not interpreted)

Published in `data/nfl_99a1199e/flagged.csv` and `docs/nfl-99a1199e/flagged.html`:

| ID | Club | Category | Issue |
|---|---|---|---|
| F99-01 | GB | name_slug_mismatch | Row prints "Zach Bako-Bewele" but links to player slug `zach-tom` |
| F99-02 | IND | unusual_status | "Darius Slayton" listed with status CUT |
| F99-03 | NE | embedded_quotes | DEV row name `Al'zillion "AZ" Hamilton` (embedded quotes, kept verbatim) |
| F99-04 | NO | unlinked_row | CUT row "Kyrese Rowan" prints without a player link |
| F99-05 | TB | unlinked_row | DEV row "Brandon Johnson" prints without a player link |
| F99-06 | CAR | reconciliation | Re-read reconciled `total_rows` 96 → 95 (55 ACT + 40 reserve); reserve rows unchanged |
| F99-R01.. | multi | cross_club_repeat | 89 reserve-row names printed on more than one club page, each kept per page |
| F99-07 | multi | cross_club_repeat | 6 additional repeats involving an ACT row on one page (observations: Robert Henry Jr. WAS/SEA, Sean Murphy-Bunting PIT/TB, Robert Longerbeam ATL/PHI, Andy Dalton ATL/PHI, Charles Snowden ATL/WAS, Malcolm DeWalt IV CAR/ATL) |

## Pack layout

- `src/nfl_99a1199e/roster_data.py` — the verbatim per-club capture (32 entries).
- `src/nfl_99a1199e/sweep.py` — deterministic row builders derived from the capture.
- `scripts/build_nfl_99a1199e.py` — zero-input builder: 6 CSVs + 6 dashboard pages;
  re-run is byte-identical.
- `scripts/check_nfl_99a1199e.py` — verifier, 10 numbered rules, exit 0 = pass.
- `tests/test_nfl_99a1199e.py` — 10 tests (verifier, identities, determinism).
- `data/nfl_99a1199e/` — `roster_sweep.csv`, `reserve_register.csv`,
  `status_code_tally.csv`, `capture_log.csv`, `flagged.csv`, `sources.csv`.
- `docs/nfl-99a1199e/` — dashboard (`index.html`), reserve register, flagged,
  sources, capture log, executive summary.

## Verification status

- `python3 scripts/build_nfl_99a1199e.py --check` → **PASS: all 10 rules hold**.
- `python3 tests/test_nfl_99a1199e.py` → **10/10 passed** (including the
  byte-identical determinism re-build).
