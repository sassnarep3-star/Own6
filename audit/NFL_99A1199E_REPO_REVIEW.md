# Repo Review — pack nfl_99a1199e (session 99a1199e)

Reviewed before writing code, per the pack protocol. Base: `d844122` (main, PR #107).

## What the repository review found

- **The claimed gap is real.** `data/nfl_8362b702/readiness.csv` marks **G-SWEEP /
  R-13** (32-club roster/IR sweep) as delivered, but
  `data/nfl_8362b702/availability_sweep.csv` shows the sweep was factually
  incomplete: 1 of 32 roster pages read and 13 of 32 hub tables read. A task
  marked delivered that is not — this session re-claims it (Task Board N99-1..N99-5
  in `COORDINATION.md`).
- **Conventions learned from the reference pack `nfl_8362b702`** (its builder,
  verifier, tests and site were read line by line): zero-input builders, a
  numbered-rules verifier (exit 0 = pass), byte-identical determinism, a
  read-clock on every captured row, per-row `source_url` stamped on an allowed
  host, blanks shipped with a reason rather than filled, verbatim capture with
  irregularities flagged and never silently fixed, and a hard rule against
  price/odds/ROI/profitability values anywhere in the pack.
- **Roster-page parsing contract** confirmed from the official page: one
  continuous table per club, rows shaped
  `| [Name](nfl.com/players/<slug>) | jersey | pos | STATUS | ... |`; the STATUS
  column is authoritative and is stored verbatim.
- **Repo-state weaknesses noted (not this pack's scope to fix):** 10 open PRs from
  other sessions sit unreviewed; several packs parse `docs/index.html` as a
  plain-text marker during their builds, so only the integration session may
  touch shared files; pack builds must stay offline and deterministic, which this
  pack honours (no network calls anywhere in build/check/tests).

## What this pack adds

- `src/nfl_99a1199e/roster_data.py` — the verbatim 32-club capture: per club,
  source URL, UTC read clock, row tallies, the verbatim status-code set, and every
  non-ACT row as `(name, position, status)` in page order. 2,858 rows total
  (1,715 ACT counted per club, 1,143 reserve captured per player).
- `src/nfl_99a1199e/sweep.py` — deterministic row builders (sweep, register,
  code tally, flags, capture log, sources, summary stats). Pure derivation; no
  hand-typed data beyond the capture module.
- `scripts/build_nfl_99a1199e.py` — zero-input builder: 6 CSVs + 6 dashboard
  pages. Re-run is byte-identical (asserted by the determinism test).
- `scripts/check_nfl_99a1199e.py` — 10 numbered rules, exit 0 = pass. Rules cover
  artifact completeness, source-URL presence/host on every CSV row, tally
  arithmetic, register reconciliation per club, no invented status codes,
  irregularity-class coverage in `flagged.csv`, nav-link resolution, capture-log
  completeness (including the published CAR re-read), absence of forbidden
  price/odds/ROI/profitability values, and exactly the 32 NFL clubs with
  well-formed roster URLs.
- `tests/test_nfl_99a1199e.py` — 10 tests across three layers (verifier,
  module identities, determinism). All pass.

## Capture process and honesty notes

- Every one of the 32 roster pages was fetched read-only on 2026-11-17 UTC; each
  club's read clock is stamped on its rows. The standings page was read once for
  reconnaissance and is **not** part of the sweep dataset (its clock is not
  invented for it).
- The CAR page was re-read to reconcile `total_rows` after the first transcription
  counted 96 rows. The re-read confirmed 55 ACT + 40 reserve = 95 rows and matched
  all 40 reserve rows exactly; the published total is 95 and the reconciliation is
  flagged (F99-06) rather than hidden.
- Irregularities observed on the pages were captured verbatim and flagged, never
  interpreted: the GB name/slug mismatch, the IND unusual status listing, the NE
  embedded-quote name, the two unlinked reserve rows (NO, TB), and 95 cross-club
  repeated-name occurrences (89 derived from the register plus 6 ACT-involved
  observations).
- No status code is expanded to an invented meaning; no repeated name is merged;
  no price/odds/ROI/CLV/profitability value appears anywhere in the pack.

## Verification results

- `python3 scripts/build_nfl_99a1199e.py --check` → **PASS: all 10 rules hold**.
- `python3 tests/test_nfl_99a1199e.py` → **10/10 passed**.
- Determinism: a full second build reproduces every CSV and page byte for byte.
