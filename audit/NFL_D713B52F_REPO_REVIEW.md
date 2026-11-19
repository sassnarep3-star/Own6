# Repo review — session `d713b52f` (2026-11-19)

Scope: a line-by-line review of what this session touched, plus the NFL packs and shared tooling it must
coexist with. Findings that are not mine to fix are **logged, not edited**. Severity is about decision
risk, not tidiness.

## Method

1. `git log --oneline -20`, `git branch -a`, `git status`, then the full tree listing.
2. Read `COORDINATION.md` head-to-tail for the last four session records and every open claim; confirmed
   no live claim covered the scopes this pack owns.
3. Read the nearest packs' builders and verifiers (`nfl_a67ddef8`, `nfl_dfc0c1bc`, `nfl_0ce967db`) so
   this pack follows the repository's conventions rather than inventing a parallel style.
4. Read the registers this pack depends on: `data/nfl_0ce967db/model_outputs.csv` (944 rows),
   `data/nfl_0ce967db/{results_feed,luck_panel,demotion_gate}.csv`, `data/nfl_8362b702/capture_attempts.csv`.
5. Ran the whole repository's test suite before and after (`tools/run_tests.py`), the link checker
   (`tools/check_site.py`) and the release gate (`tools/release_gate.py`).
6. Fetched the official pages myself rather than trusting any inherited transcript, and recorded every
   read with its URL, clock time and sha256.

## Findings

| ID | Kind | Finding | Severity | Handling |
|---|---|---|---|---|
| RF-01 | **inherited defect, cleared** | `data/nfl_8362b702/capture_attempts.csv` records the Game Book PDF route as unreachable. From this session the same route returns the PDF on the first attempt, four times | **high** | re-tested live 2026-11-19; 4 books transcribed; FLAG-07 closed with evidence |
| RF-02 | **data defect, mine, fixed** | the model scored 16 first-game fixtures using a club number derived from games played earlier in the *same* week | **high** | refused those games; 150 = 134 scored + 16 refused, both published; verifier rule 15 now fails the build if it recurs |
| RF-03 | **data defect, mine, fixed** | four phantom "designated Out but not on the inactive list" rows, caused by generational suffixes (`Carlton Davis III` vs `C. Davis`) | medium | suffix-aware matcher; the remaining 4 unresolved rows are genuine and published as unresolved |
| RF-04 | **integration defect, mine, fixed** | suggestion rows used only a `title` column; the shared reader (`src/nfl_dfc0c1bc/registers.py`) maps `title` into `statement`, so the cross-pack theme classifier saw headlines and left two rows unclassifiable (`T00`) | medium | added `suggestion`/`statement`/`official_source_url`; the other session's test now passes **without editing their code** |
| RF-05 | structural | 18 prior NFL packs, 17 distinct requirement-id schemes, no merged view; this pack adds a 19th (86 rows) | medium | each pack stays namespaced; the site's landing page is a per-bullet readiness table for this pack only |
| RF-06 | data hygiene | `playtime` transcription must be hand-read: the PDF interleaves club columns and repeats rows (two CLE rows for one player at 39% and 36%) | medium | hand-read only; the sole automated bound is snaps × 11, which all 8 clubs pass; duplicates published as F-05 |
| RF-07 | verified good | inherited standings reconcile exactly: 32 clubs, W = L = 149, 2 ties, PF = PA = 6,923 | info | independently re-computed; 3 standings checks, all match |
| RF-08 | verified good | inherited build scripts are deterministic and offline | info | rebuilt twice, byte-identical; adopted the same pattern here |
| RF-09 | risk | a prior pack's implementation of the same frozen rule scores **better** than this one (0.2355 vs 0.2448 on the 118 shared games). The gap is 71% of the measured skill | **high** | published, not hidden; the pack refuses to claim its own number is the better model |
| RF-10 | process | the repository's release gate and link checker pass, but neither checks cross-pack register schemas — which is exactly how RF-04 survived | medium | logged as a suggestion for the shared tooling owner; not edited here |
| RF-11 | verified good | no page in this pack contains a form control, a placeholder string, or a link to a non-official host; enforced by rules 5, 6, 7 | info | 20-rule verifier green |
| RF-13 | **verified defect in an inherited table** | `data/nfl_0ce967db/luck_panel.csv` row S03 has `brier` exactly equal to `reliability` and `resolution` exactly equal to `uncertainty` — the signature of bins keyed on exact forecast values, which makes the decomposition measure nothing | **high** | not mine to edit; logged in the flagged register and in the executive summary so that pack's owner can repair it. This pack's own panel had the same defect and was rebuilt with the identity asserted at 1e-9 |
| RF-12 | **claim accuracy** | an earlier draft of `preregistration.md` said the registration was "committed before the scoring run". The git history shows the registration text and the first scoring artifacts entered the repository in the **same commit** | medium | reworded to the true chronology; constants were fixed in code before the first run, and that is all the file now claims |

## Files reviewed but deliberately not edited (other sessions' scopes)

* `src/nfl_dfc0c1bc/**`, `scripts/build_nfl_dfc0c1bc.py`, `tests/test_nfl_dfc0c1bc.py` — RF-04 was fixed
  on my side of the boundary; their code is untouched and their suite passes.
* `data/nfl_8362b702/capture_attempts.csv` — a historical record; the correction lives in this pack's
  flagged register so the original stays auditable.
* `data/nfl_0ce967db/**` — read-only inputs to the implementation comparison.
* `index.html`, `docs/index.html`, `README.md` — shared hubs. Only additive blocks were inserted, in the
  convention the earlier packs used, and the link checker confirms every new link resolves.

## Verification evidence

| Gate | Command | Result |
|---|---|---|
| Pack tests | `python3 tests/test_nfl_d713b52f.py` | all pass (67 assertions) |
| Repo tests | `python3 tools/run_tests.py` | **194/194** |
| Pack verifier | `python3 scripts/check_nfl_d713b52f.py` | **20 rules, 1,066 pinned rows, 7 pages** |
| Links | `python3 tools/check_site.py` | 13 strict pages, 0 errors, 0 advisory |
| Release gate | `python3 tools/release_gate.py` | 0 issues |
| Determinism | verifier rule 16 | data and site rebuild byte-identically |
