# Repository review — line by line, with official links for manual review

**Session:** `arena/a6ccf588-own6` · **Date:** 2026-11-02 · **Reviewed:** initial commit `c5d6e4c` and the combined `main` tree after PRs #1–#7.
**Official sources for repo facts:** the [GitHub repository](https://github.com/sassnarep3-star/Own6), the [GitHub REST API repo endpoint](https://api.github.com/repos/sassnarep3-star/Own6), the [tree endpoint](https://api.github.com/repos/sassnarep3-star/Own6/git/trees/main?recursive=1), the [Pages endpoint](https://api.github.com/repos/sassnarep3-star/Own6/pages), and [GitHub Docs on publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). All were read directly during this session.

## 1. Repository-level facts (verified via official GitHub API)

| Item | Observed value | Official link |
|---|---|---|
| Repository | `sassnarep3-star/Own6`, public, not archived | [api.github.com/repos/sassnarep3-star/Own6](https://api.github.com/repos/sassnarep3-star/Own6) |
| Default branch | `main` | [api.github.com/repos/sassnarep3-star/Own6](https://api.github.com/repos/sassnarep3-star/Own6) |
| Created | 2026-10-31T22:49:36Z | [api.github.com/repos/sassnarep3-star/Own6](https://api.github.com/repos/sassnarep3-star/Own6) |
| License | `null` (no LICENSE file) — **flag I-19** | [api.github.com/repos/sassnarep3-star/Own6](https://api.github.com/repos/sassnarep3-star/Own6) |
| Initial commit | `c5d6e4c` — "Initial commit", one file: `README.md` containing `# Own6` | [github.com/…/commit/c5d6e4c](https://github.com/sassnarep3-star/Own6/commit/c5d6e4c4b3b7ed486d48b0bf4d9d0cbce89ef49d) |
| Pages | enabled, `build_type: legacy`, source `main:/`, https enforced, URL `https://sassnarep3-star.github.io/Own6/` | [api.github.com/repos/…/pages](https://api.github.com/repos/sassnarep3-star/Own6/pages) |
| Pages builds | multiple `built` builds; latest checked during this session | [api.github.com/repos/…/pages/builds](https://api.github.com/repos/sassnarep3-star/Own6/pages/builds) |
| Branches at review time | 10 (`main` + 9 `arena/*` session branches) — parallel sessions | [github.com/…/branches](https://github.com/sassnarep3-star/Own6/branches) |
| Pull requests at review time | #1–#7 (six merged, #2 closed) | [github.com/…/pulls](https://github.com/sassnarep3-star/Own6/pulls) |

## 2. File-by-file review of the combined `main` tree

Each row links to the official GitHub blob for manual review. "Verified" means the file's content/purpose was read from the repository during this session.

| Path | What it is / content checked | Official link | Verification / flag |
|---|---|---|---|
| `README.md` | Project overview, executive-summary pointer, sources boundary, live-site contents | [blob/main/README.md](https://github.com/sassnarep3-star/Own6/blob/main/README.md) | Originally 6 bytes (`# Own6`); expanded by parallel sessions. States no profitable edge is demonstrated — consistent with this review. |
| `COORDINATION.md` | Shared task board; multiple session sections, claims, logs, PR/merge records | [blob/main/COORDINATION.md](https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md) | Overlapping scopes between sessions (I-2); this session's section appended only, other sections preserved verbatim. |
| `EXECUTIVE_SUMMARY.md` | Objective, system, strategy families, correlations, data/legality notes, irregularities | [blob/main/EXECUTIVE_SUMMARY.md](https://github.com/sassnarep3-star/Own6/blob/main/EXECUTIVE_SUMMARY.md) | Contained "sandbox cannot fetch NBA.com directly" — **incorrect**, corrected in this pass (I-3). |
| `index.html` | Root meta-refresh redirect to `docs/` | [blob/main/index.html](https://github.com/sassnarep3-star/Own6/blob/main/index.html) | Needed because Pages source is `main:/`; live root URL confirmed to reach the dashboard (V17, V19). |
| `.nojekyll` | Disables Jekyll processing | [blob/main/.nojekyll](https://github.com/sassnarep3-star/Own6/blob/main/.nojekyll) | Present at root and in `docs/`. |
| `.gitignore` | Ignores `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.venv/` | [blob/main/.gitignore](https://github.com/sassnarep3-star/Own6/blob/main/.gitignore) | Added by another session after `.pyc` files were committed (I-11). |
| `data/sources.csv` | Official-source registry S1–S8 | [blob/main/data/sources.csv](https://github.com/sassnarep3-star/Own6/blob/main/data/sources.csv) | Re-verified and corrected in this pass; S3 URL was broken, statuses were "indexed" not direct (I-4, I-14). |
| `data/*.json` | Schedule, Korean statute, NBA policy, strategies, methodology, flags (another session) | [tree/main/data](https://github.com/sassnarep3-star/Own6/tree/main/data) | Other session's scope; not edited. Their official-source claims were independently re-checked for the URLs used here (V21–V23). |
| `docs/index.html` | Dashboard + own-line calculator | [blob/main/docs/index.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/index.html) | Calculator used `Math.erf`, undefined in JS → **broken** (I-7); repaired. Added link to the independent review section. |
| `docs/strategies.html` | Strategy families S-A…S-F (single bets, totals, props, parlays, combos) | [blob/main/docs/strategies.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/strategies.html) | All data rows carry official links; no results published. |
| `docs/validation.html` | Gates G1–G8 | [blob/main/docs/validation.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/validation.html) | Rows G5–G8 had no official source link → repaired with V11–V14, V12, V24 (I-20). |
| `docs/correlations.html` | Correlation measurement plan, all ρ blank | [blob/main/docs/correlations.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/correlations.html) | Blank values are correct policy; added Pearson methodology reference V12. |
| `docs/leaderboard.html` | Empty leaderboard + lower-bound scoring rule | [blob/main/docs/leaderboard.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/leaderboard.html) | Its single data row linked only to an internal page → official link added (I-20). |
| `docs/sources.html` | Published source table | [blob/main/docs/sources.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/sources.html) | False "sandbox cannot fetch NBA.com" note, broken FAQ URL, S8 row without source link → all corrected (I-3, I-4, I-20). |
| `docs/flagged.html` | Flagged for Review page | [blob/main/docs/flagged.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/flagged.html) | F1/F3 gave a wrong reason; F7 linked `../COORDINATION.md` which 404s from the Pages root → corrected; new irregularities added (I-6). |
| `docs/assets/style.css` | Shared dashboard styling | [blob/main/docs/assets/style.css](https://github.com/sassnarep3-star/Own6/blob/main/docs/assets/style.css) | Left unchanged (other session's scope); the review section uses its own stylesheet. |
| `docs/verified/**` | Separate source-linked site built by session `05e359b8` | [tree/main/docs/verified](https://github.com/sassnarep3-star/Own6/tree/main/docs/verified) | Not edited (other session's scope). Some methodology/strategy rows lack official links → request logged in `COORDINATION.md` (I-18). |
| `src/own6/lines.py` | Own spread/total/win-prob from PACE/OffRtg/DefRtg; de-vig; fitted home-adv/margin SD | [blob/main/src/own6/lines.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/lines.py) | Definitions match V02; no hard-coded NBA numeric values — correct. |
| `src/own6/props.py` | Shrunk per-minute rate × projected minutes; normal P(over) | [blob/main/src/own6/props.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/props.py) | Shrinkage constant `k=10` is a project default, not an official value — labelled as policy. |
| `src/own6/parlay.py` | Pearson ρ + Gaussian-copula joint probability; independence only as labelled case | [blob/main/src/own6/parlay.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/parlay.py) | ρ is computed from supplied residual pairs; no ρ value is stored in the repo — correct. |
| `src/own6/validation.py` | Breakeven, Brier, log-loss, exact binomial, bootstrap CI, CLV t-stat, Bonferroni, G1–G8 | [blob/main/src/own6/validation.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/validation.py) | Methods independently confirmed against V09–V16. Thresholds are disclosed project policy, not official NBA facts. |
| `src/own6/leaderboard.py` | Score = 100·ROI lower confidence bound + 10·CLV + 10·Brier edge; n≥200 | [blob/main/src/own6/leaderboard.py](https://github.com/sassnarep3-star/Own6/blob/main/src/own6/leaderboard.py) | Weights are project policy, explicitly disclosed in code. |
| `tests/test_engine.py` | 5 unit tests | [blob/main/tests/test_engine.py](https://github.com/sassnarep3-star/Own6/blob/main/tests/test_engine.py) | 5/5 pass via `tools/run_tests.py` (I-10); `pytest` unavailable in sandbox. |
| `examples/demo_synthetic.py` | Synthetic-only pipeline demo | [blob/main/examples/demo_synthetic.py](https://github.com/sassnarep3-star/Own6/blob/main/examples/demo_synthetic.py) | Clearly labelled "NOT NBA data"; no fabricated stats published. |
| `scripts/build_site.py`, `scripts/check_site.py` | Another session's site generator + checker | [tree/main/scripts](https://github.com/sassnarep3-star/Own6/tree/main/scripts) | Not edited. This session's independent tools live in `tools/`. |

## 3. Irregularities flagged for the owner

- **Greenfield start:** the initial commit contained only `README.md` (6 bytes) — no data, code, tests, license, CI or site. All current content was produced by parallel sessions on 2026-11-02. [Initial commit](https://github.com/sassnarep3-star/Own6/commit/c5d6e4c4b3b7ed486d48b0bf4d9d0cbce89ef49d).
- **No license** (`license: null`). [API](https://api.github.com/repos/sassnarep3-star/Own6) → I-19.
- **Coordination collisions:** several sessions claimed overlapping root/docs scopes and merged to `main` within minutes of each other; `COORDINATION.md` was rewritten twice while this pass was open. All conflicts were resolved by concatenation, never by discarding another session's text. → I-2.
- **Broken / unverifiable links and claims** in the first published site (I-3…I-7, I-14, I-20), repaired by this pass and listed on the [Flagged for Review page](../docs/flagged.html).
- **Pages configuration:** legacy `main:/` source with a root redirect; setting `main:/docs` via the REST API returned HTTP 403 "Resource not accessible by integration". The deployed root URL was confirmed to reach the dashboard. [GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) → I-12.
- **Historical failed Actions deploy runs** from the removed `pages.yml` workflow; the workflow was removed in PR #4 and no deploy job remains. → I-13.
- **Tracked Python bytecode** in early commits; `.gitignore` now excludes it and the files are gone from `main`. → I-11.
- **Empty/unverified numeric fields** (odds, correlations, ROI, backtests) remain blank by design; no official source exists for them. → I-15, I-16.
