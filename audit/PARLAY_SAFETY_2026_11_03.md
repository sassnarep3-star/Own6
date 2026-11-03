# Executive summary — independent parlay safety review

Review date: 2026-11-03 · Session: `arena/b700d3ca-own6` · Baseline: `f2877f3`.

## Decision

**Keep the project in research/paper mode. No validated NBA betting edge, empirical copula coefficient, current executable line or reward winner is established by this review.** Statistical validation can quantify uncertainty, not eliminate luck. No money was wagered, no rewards were paid, and no live NBA statistical feed was scraped or activated.

The existing site already organizes singles, game lines, props, combos, parlays, candidate strategies, validation gates, correlations and a leaderboard. This session preserves that work and fixes an independently reproducible safety defect in the older dependency-free parlay simulator, outside the active scopes of open PRs #28 and #31. A new single-page review at [`docs/parlay-safety/index.html`](../docs/parlay-safety/index.html) publishes the repair, explicit evidence boundaries, official methodological sources and **Flagged for Review** findings. It needs no user input.

The authorized empirical ledger remains empty in this session. Existing historical numeric files were not re-authenticated; their inherited verification labels do not become verified by compilation, arithmetic, source-domain checks, or this repair. Those records must not be used to claim an independently verified betting edge. We cannot honestly certify every historical fact in the repository from this narrow review.

## Repaired original utility: complete line-range review

Primary record: [src/own6/parlay.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py). Line ranges refer to the repaired file in this change. Blank/comment/import lines are included within the ranges, not treated as factual NBA claims.

| Lines | Verified implementation behavior | Verification / official primary reference |
|---|---|---|
| 1–22 | Scope disclaimer; latent-normal dependence, singular-model limitation; explicit project numerical policy | [Primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L1-L22), [statsmodels GaussianCopula](https://www.statsmodels.org/stable/generated/statsmodels.distributions.copula.api.GaussianCopula.html) |
| 24–47 | Reject bool/non-real, nonfinite, empty or out-of-range probability inputs; convert supported real inputs to floats | [Primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L24-L47), [regression tests](https://github.com/sassnarep3-star/Own6/blob/main/tests/test_legacy_parlay.py) |
| 50–77 | Aligned paired Pearson formula; reject constant/near-constant inputs; scale before squaring to avoid overflow; bound only final floating-point roundoff | [SciPy Pearson formula / warnings](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html), [primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L50-L77) |
| 80–105 | Finite square symmetric correlation matrix with unit diagonal; reject invalid pivots instead of clipping | [NumPy positive-definite Cholesky reference](https://numpy.org/doc/stable/reference/generated/numpy.linalg.cholesky.html), [primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L80-L105) |
| 108–116 | Standard-library normal CDF/inverse; inverse accepts interior probabilities only | [Primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L108-L116), [CPython statistics implementation](https://github.com/python/cpython/blob/3.11/Lib/statistics.py) |
| 119–141 | Validated count/seed, endpoint thresholds and explicit latent-normal all-leg simulation | [statsmodels copula equation](https://www.statsmodels.org/stable/generated/statsmodels.distributions.copula.api.GaussianCopula.html), [primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L119-L141) |
| 142–156 | Probability, hit count, seed and two-sided 95% Wilson interval for conditional Monte Carlo error only | [NIST interval equations](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm), [primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L142-L156) |
| 159–173 | Existing float-return API retained; independence product remains explicit and now validates nonempty marginals | [Primary code](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py#L159-L173) |

### Important numerical distinctions

- `pearson` returns a point estimate, not a significance test or confidence interval. At least two nonconstant pairs permit arithmetic; two pairs do **not** establish adequate statistical evidence.
- This strict implementation supports only positive-definite correlation matrices. Singular positive-semidefinite matrices can be mathematically valid; rejecting them is an implementation limitation, not proof that those models are invalid.
- Pivot floor `1e-12`, exact matrix symmetry and exact unit diagonal are disclosed fail-closed project policies. No nearest-correlation repair, regularization or independence substitution is performed.
- Observed score residuals, binary leg outcomes and latent normal copula correlations are distinct. Numerical tests do not calibrate an NBA copula or establish a profitable combo.
- Wilson limits describe finite Monte Carlo sampling uncertainty **conditional on the supplied fixed model**. They omit parameter estimation, sample selection, NBA forecast error, market movement, costs and future drift. A very narrow Monte Carlo interval is not high confidence in an NBA edge.
- The random seed controls reproducibility within the Python random implementation; no cross-version bit-identical guarantee is asserted.

## Official source reads

The following source sections were returned by direct `fetch_page` retrieval on 2026-11-03. No external source is represented as verifying our empirical performance.

| Source | Sections directly read | Supports / limits | Official link |
|---|---|---|---|
| SciPy | `pearsonr`, chunks 0–1 | Pearson formula, minimum sample length, constant-input undefined result, near-constant warning; does not verify any NBA correlation | [SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| NumPy | Cholesky page, chunk 0 | Square symmetric/Hermitian positive-definite matrix and decomposition failure behavior | [NumPy](https://numpy.org/doc/stable/reference/generated/numpy.linalg.cholesky.html) |
| statsmodels | GaussianCopula, chunk 0 | Construction from multivariate latent normals, copula equation, separate singular handling | [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.distributions.copula.api.GaussianCopula.html) |
| NIST | Handbook §7.2.4.1, chunk 0 (complete page) | Wilson interval equations and interval limitations | [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) |
| NBA | Terms, chunks 0 and 4 | Ownership/public reuse restrictions; §9 prohibits gambling use including legal gambling. This review is not a legal opinion | [NBA Terms](https://www.nba.com/termsofuse) |
| NBA | Stats glossary, chunk 0 | Metric-definition context only; not NBA values, licenses, correlations or edges | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| Python | Statistics docs, chunk 0 | Official module index/context only; NormalDist details were not returned in that chunk. No whole-page verification claim | [Python docs](https://docs.python.org/3/library/statistics.html) |

## Published unresolved flags

Full detail appears in the source-linked **Flagged for Review** section of the new page.

| ID | Status / finding | Primary record or official review source |
|---|---|---|
| PS-01 | needs review: no independently calibrated empirical NBA copula or authorized paired sample | [statsmodels model definition](https://www.statsmodels.org/stable/generated/statsmodels.distributions.copula.api.GaussianCopula.html), [NBA Terms](https://www.nba.com/termsofuse#nba-statistics) |
| PS-02 | needs review: legacy `validation.evaluate` tests only G1–G6 although catalog lists G1–G8; log-loss/ledger/correlation checks are not all enforced | [validation.py lines 18–30](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/validation.py#L18-L30) |
| PS-03 | needs review: legacy line/prop invalid standard deviations return 0.5 rather than fail closed | [lines.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/lines.py), [props.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/props.py) |
| PS-04 | needs review: original leaderboard is sample-count-only eligibility with an i.i.d.-style normal ROI bound, not complete competition qualification | [leaderboard.py lines 3–9](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/leaderboard.py#L3-L9) |
| PS-05 | needs review: public availability is not data-use authorization | [NBA Terms §9](https://www.nba.com/termsofuse#nba-statistics) |
| PS-06 | needs review: historical facts/odds/correlations not independently re-authenticated in this session | [Primary repository data](https://github.com/sassnarep3-star/Own6/tree/main/data) |

## Tests and publication evidence

Initial local result: **45 pytest tests passed**, including 11 new dependency-free regressions; the stdlib runner passed **21/21** top-level function tests. The release gate found **0 issues**. Tests include unequal/missing pairs, nonfinite and bool inputs, overflow-scale Pearson arithmetic, malformed/asymmetric/indefinite/singular matrices, deterministic marginals, controls, reproducibility, analytic bivariate-normal orthant comparison, and per-row official links on the new report page. All test quantities are synthetic mathematical fixtures, not NBA observations.

An additional independent scientific-library comparison and final combined-tree checks, PR, merge and GitHub Pages status are recorded under session `arena/b700d3ca-own6` in [COORDINATION.md](../COORDINATION.md). Deployment is not claimed until the GitHub API reports a successful build for the merged commit. Passing a link checker is not line-by-line factual verification of inherited data.
