# NFL lines lab - audit notes

Date: 2026-11-12. Scope: everything added by this session, plus the repository checks that affect it.
Written for a reviewer who wants to know **what could be wrong** before trusting a number.

## 1. Defects found and fixed in this session

These were found by the test suite and by comparing rendered pages against the artefacts. Each one changed a
published number, so each is listed with the evidence.

| ID | Defect | Impact | Fix |
|---|---|---|---|
| D-01 | `pricing.cover_probability` applied the spread with the wrong sign | Every alternate-line probability on the own-lines page was inverted (a home team getting +2.5 points was priced as a 36% cover) | Rewrote with the home-spread convention; added a test that pins the convention |
| D-02 | `correlation.joint_from_copula` called `scipy.stats.mvn.mvnun`, removed in SciPy 1.9, and swallowed the `AttributeError` | Every copula joint silently returned `None`, which the page rendered as a blank without explanation | Replaced with an exact 1-D quadrature; tested against rho=0 and both Frechet bounds |
| D-03 | `gate_deflated_sharpe` awarded a **pass** with `n_trials=1` because the expected-maximum term is -inf | A single trial would have passed the hardest gate in the suite | A single trial now benchmarks against zero skill; DSR is a 95% probability gate |
| D-04 | Candidate roll-up labelled a candidate with real failures as `blocked` | A failing candidate could look merely un-evaluated, and `blocked` sounds softer than `rejected` | Fail-closed: any failed gate means rejected |
| D-05 | Bonferroni-adjusted p-values were not clamped at 1 | The site printed `min adjusted p=1.7898`, which is not a probability | Clamped at 1; test asserts the value stays in [0, 1] |
| D-06 | Depth-page prose named players who were not in the deficiency rows | A hand-written narrative contradicted the generated table - the exact failure mode this project forbids | The narrative is now generated from the rows; nothing about a club is typed by hand |

## 2. Repository defects found but **not** caused by this session

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| R-01 | `tests/assurance/test_audit.py` fails on a clean checkout of `main` | Reproduced in a fresh worktree at `b41bc81` before any file was added: the stored SHA-256 for `.gitignore` does not match after checkout | Listed in `COORDINATION.md`; not fixed here (out of scope, another session owns assurance) |
| R-02 | `scripts/audit_repo.py` cannot run in this clone | Missing git object `86eca0f` | Not a regression; noted only |
| R-03 | A second NFL section was merged while this lab was built (PR #66) | `docs/nfl/*.html` from that PR; disjoint from `docs/nfl/lab/**` | Request R-1/R-2 logged in `COORDINATION.md` |

## 3. Claims made by the pages, and their backing

| Claim | Backing | Verified? |
|---|---|---|
| "0 of 8 candidates qualify" | `backtest.json.gates`, recomputed by `check_nfl_lab.py` | yes |
| "45/34/50 slate clusters" | `results[*].n_clusters` | yes |
| "phi +0.022, CI includes zero" | `correlations.json.C1` | yes |
| "6 of 275 injury rows carry a game status" | count of non-empty `game_status` in `injuries_week10_read.csv` | yes |
| "89 official-value checks, 0 discrepancies" | `reconciliation.json` | yes |
| "the historical file has no licence" | GitHub API `license: null`, recorded in `sources.json` | yes |
| "NFL terms forbid systematic retrieval" | quoted verbatim from nfl.com/legal/terms section 1.3 | yes |

## 4. Claims deliberately **not** made

- No profitability claim of any kind.
- No market price for any 2026 game (F-N01).
- No points-lost value for an injured player (no snap-share or EPA-by-replacement data).
- No player-prop dependence value (no prop outcomes).
- No claim that any strategy "nearly" qualified.

## 5. Reproduce

```
python3 scripts/nfl_reconcile.py      # 89 official-value checks
python3 scripts/nfl_analysis.py       # every model artefact
python3 scripts/build_nfl_lab.py      # 14 pages
python3 scripts/check_nfl_lab.py      # row-source, blank, link and drift rules
python3 -m pytest -q tests/test_nfl_lab.py
```

CI (`.github/workflows/nfl-lab-ci.yml`) runs all five and additionally fails if rebuilding produces a
byte-level diff, so a hand-edited page or stale artefact cannot be merged.
