# NFL Decision-Readiness Pack — Executive Summary (session 6ab24751)

**Branch:** `arena/6ab24751-own6` · **Date:** 2026-11-15 · **Scope:** `data/nfl_6ab24751/`,
`src/nfl_6ab24751/`, `docs/nfl-6ab24751/`, and the decision-readiness table on the root landing page.

## Objective

The brief's explicit deliverable that was **not yet delivered anywhere** is the
**decision-readiness table on the landing page: one row per requirement, with the gate that blocks it
and the number that would clear it**. The root landing page (`index.html`) carried category cards but
**zero table rows**. This session builds a consolidated, source-linked roll-up of the entire requirement
list, renders it as a table on the landing page, and publishes a self-contained dashboard behind it.

Statuses, blocking gates and clearing numbers are grounded in the validation-gate and flag registers that
already exist in the merged NFL packs. Nothing is inferred; unconfirmed values are blank and flagged.

## What is delivered

| Deliverable | Path | Count |
|---|---|---|
| Requirements decision-readiness dataset | `data/nfl_6ab24751/readiness.csv` | 81 requirements |
| Gate reference register | `data/nfl_6ab24751/gates.csv` | 33 gates (VG / NFL-G / D966-G) |
| Official source register | `data/nfl_6ab24751/sources.csv` | 18 official/methodological sources |
| Flagged-for-review register | `data/nfl_6ab24751/flagged.csv` | 10 flags |
| Self-contained dashboard | `docs/nfl-6ab24751/` | 5 pages + landing-table fragment |
| **Landing-page decision-readiness table** | `index.html` | 81 rows + header |
| Verifier, tests, CI | `scripts/check_nfl_6ab24751.py`, `tests/test_nfl_6ab24751.py`, `.github/workflows/nfl-6ab24751-ci.yml` | 344 checks, 13 tests |

## Status of the 81 requirements

| Status | Count | Meaning |
|---|---|---|
| Implemented | 18 | The artifact exists and is checked. |
| Implemented (limited) | 20 | Structure exists and is checked, but the key numeric output is blank because a required input is absent. |
| Open (blocked / needs review / not started) | 40 | Not delivered; the row names the gate that blocks it and the condition that would clear it. |
| Rejected (policy) | 3 | Shortcuts the brief explicitly rejects. |

## The binding blockers

1. **VG-03 — no licensed market price archive.** No official NFL page publishes a price, so every
   market line, difference, residual, open/close snapshot, ROI and CLV cell stays blank. This is the single
   largest blocker and it blocks ROI, CLV, settlement-grade backtests and the residual-vs-market view.
2. **NFL-G10 — partial depth coverage.** Only a minority of the 32 clubs have a verified depth chart, so
   deficiency scores are **floors, not charts**. Club charts are also labelled unofficial by the clubs.
3. **VG-07 — the sample floor.** Zero strategies are certified because no graded selections exist yet;
   the leaderboard is empty **by design**.

## Deliberate non-findings (state them, do not fill them)

- No market price, ROI, CLV or reward payout is published anywhere in this pack.
- No depth is inferred from jersey number, experience or salary (rejected by policy: RQ-12, RQ-51).
- No strategy is ranked by raw win rate or season-long ROI (rejected by policy: RQ-66).
- The readiness table is a **consolidated roll-up**, not a fresh line-by-line re-verification of every
  underlying pack value (flag F6A-01).

## Verification performed

- `python3 scripts/build_nfl_6ab24751.py --check` → readiness pack validates; dashboard regenerates
  byte-identically.
- `python3 scripts/check_nfl_6ab24751.py` → **344 checks, 0 failures**: every readiness row carries an
  official https source present in the register; every blocking gate resolves to a gate in `gates.csv`;
  every generated `<tbody>` row carries an https source link; the landing-page table matches the emitted
  fragment; no `<input>` elements; internal links resolve.
- `python3 -m unittest discover -s tests -p "test_nfl_6ab24751.py"` → **13 tests pass**.
- `python3 tools/release_gate.py` → 0 issues (run at integration).

## Sources

Official NFL and methodological sources are recorded in `data/nfl_6ab24751/sources.csv` and rendered on
`docs/nfl-6ab24751/sources.html`. Key official references: `nfl.com/schedules`, `nfl.com/standings`,
`nfl.com/injuries`, `nfl.com/scores`, `nfl.com/legal/terms/`, `operations.nfl.com/rules-officiating/2026-nfl-rulebook`,
`patriots.com/team/depth-chart`, and the NFL's official sportsbook-partner release. Methodological
references: NIST/SEMATECH, scikit-learn, SciPy, statsmodels.

## Irregularities (published, not concealed)

See `docs/nfl-6ab24751/flagged.html` (F6A-01 … F6A-10). None blocks the merge. The most material are the
absent market price archive (F6A-02), partial and unofficial depth coverage (F6A-03, F6A-04), and the
absent gambling-use licence under NFL.com Terms §1.3 (F6A-08).

## No-manual-input

The site is fully generated from committed CSVs. No page contains an input control; the checker and tests
assert zero `<input>` elements.
