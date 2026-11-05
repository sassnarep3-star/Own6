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

---

## Addendum — session `arena/269a73e2-own6` (2026-11-03)

**Scope:** line-level checks of the combined `main` tree as of `e5ceb0f` (PRs #20 and #21 merged during this session), plus recomputation of the correlation figures from repo data. Every row has the check that produced it and a link. Items marked **fixed** were changed on this branch. Official sources were read with the fetch tool, because the sandbox can reach only GitHub, npm and PyPI.

| # | Item | How it was checked | Result | Link |
|---|---|---|---|---|
| A1 | `docs/index.html` (landing) | `git grep` for conflict markers; HTML tag-balance parse | Three conflict markers on `main` (lines 1, 4, 6). **Fixed**: kept the full navigation, removed the second copy. Tags balanced. Flag F18. | [docs/index.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/index.html) |
| A2 | Landing summary wording | Read page against `docs/strategies.html` and `docs/lab/strategies.html` | Said "5 families, 8 gates". Root site: S-A to S-F with gates G1–G8. Lab: six candidates L1–X1 with ten gates. **Fixed**: wording now names both sets and points to F13. | [docs/strategies.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/strategies.html), [docs/lab/strategies.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/lab/strategies.html) |
| A3 | Lab tables | Rebuilt with `scripts/build_lab.py`; read the Strategies table cells | Cells printed `<generator object …>`. **Fixed** in `table()`; six rows now readable. `check_lab.py` passes. Flag F19. | [scripts/build_lab.py](https://github.com/sassnarep3-star/Own6/blob/main/scripts/build_lab.py) |
| A4 | Verified Sources page | Rebuilt with `scripts/build_site.py`; diffed against committed page | Rebuild dropped the F16 caution. **Fixed**: generator now writes it, quoting §9(ii) and §9(iv). Flag F20. | [scripts/build_site.py](https://github.com/sassnarep3-star/Own6/blob/main/scripts/build_site.py) |
| A5 | NBA Terms of Use §1, §9(i)–(iv) | Fetch tool, chunks 0–5, read 2026-11-03 | §9(ii) "legitimate news reporting or private, non-commercial purposes"; §9(iv) gambling-use bar; §1 linking restriction. Flags F17, F26. | [nba.com/termsofuse](https://www.nba.com/termsofuse) |
| A6 | Correlation `home_score_vs_away_score` | Recomputed Pearson from `data/games_results_2026-27.csv` | r = 0.2004, n = 92 (matches). p = 0.055; 95% CI −0.005 to 0.389. Flag F21. | [data/correlation_findings.csv](https://github.com/sassnarep3-star/Own6/blob/main/data/correlation_findings.csv) |
| A7 | Correlation `same_date_game_margins` | Tried both natural pairing definitions | One-order pairing reproduces r = 0.1052 (n = 357). Symmetric pooling gives r = 0.0927 (n = 714). No script in repo computes it. Flag F22. | same |
| A8 | Correlation `teammate_PTS_Mitchell_Allen` | Checked inputs and sample size | n = 6, CI −0.919 to 0.592, p = 0.40. Gamelog rows not in repo, so not reproducible. Labelled "ESPN official" (wrong label, F24). Flag F23. | same |
| A9 | Correlation `rest_diff_vs_home_margin` | Searched repo for rest column | No rest column in `games_results_2026-27.csv`; value not reproducible. Flag F25. | same |
| A10 | Per-row NBA links in `docs/own6/data.html` | Counted `nba.com/game/` links | 92 links. Republication of NBA game results (F26). Not re-fetched, on purpose. | [docs/own6/data.html](https://github.com/sassnarep3-star/Own6/blob/main/docs/own6/data.html) |
| A11 | Alberta helplines | Fetch tool, read 2026-11-03 | AGLC Self-Exclusion 1-844-468-8034; Alberta Health Services Addiction Helpline 1-866-332-2322. Added to landing footer; registry rows V26, V27. | [aglc.ca](https://aglc.ca/gaming/common-gaming-questions) |
| A12 | Official-source gate (`tools/check_site.py`) | Ran on branch | Failed with 2 strict errors, because the AGLC links were not in the registry. **Fixed** by appending V26 and V27 (append-only; no existing row changed). Now 0 errors. | [data/verification_log.csv](https://github.com/sassnarep3-star/Own6/blob/main/data/verification_log.csv) |
| A13 | `scripts/audit_sources.py` in a shallow clone | Ran in a sandbox with a shallow checkout | Failed with `fatal: not a tree object` (the frozen upstream commit is missing). Passes with full history: 82 rows, 43 files, 20 findings. CI was fixed upstream by `fad8c2b` (`fetch-depth: 0`). Recorded, no action. | [.github/workflows/lab-ci.yml](https://github.com/sassnarep3-star/Own6/blob/main/.github/workflows/lab-ci.yml) |
| A14 | Test suite | `pytest tests/` with the pinned `requirements-empirical.txt` | 20/20 pass (numpy 2.4.6, scipy 1.17.1, pytest 9.2.0). | [tests/](https://github.com/sassnarep3-star/Own6/tree/main/tests) |
| A15 | Other checks | `verify_data.py`, `check_lab.py`, `check_report.py`, `linkcheck.py`, `build_review.py --check`, `tools/run_tests.py` | 213/213; OK; OK; 240/240 rows sourced; 7 files match; 5/5. | [scripts/](https://github.com/sassnarep3-star/Own6/tree/main/scripts) |
| A16 | GitHub Pages | GitHub REST API `repos/…/pages` | `build_type: legacy`, source `main:/`, status `built`, https enforced. The live `github.io` URL is not reachable from the sandbox; the live check is run after deploy. | [api.github.com/repos/sassnarep3-star/Own6/pages](https://api.github.com/repos/sassnarep3-star/Own6/pages) |
| A17 | Coordination board | Read whole file | Duplicate `arena-5dfdc6d5` section, with stale "unclaimed" E3–E5 rows. Session `arena/325834c9-own6` has no entry. Flag F27. Nothing removed. | [COORDINATION.md](https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md) |
| A18 | Earlier re-verification records | Read `arena/f56f0055-own6` section | Recorded "None new" irregularities on `ba6b7b6`. It does not mention the defects in A1 and A3. Noted in F18. | [COORDINATION.md](https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md) |

**Limits.** This review did not re-verify the 92 NBA game rows against nba.com (F26), and did not verify any odds. Those values remain blank or flagged. The live site was not reachable from the sandbox. Line-level verification covers the rows and files named above, not every sentence in the 36 HTML pages under `docs/`.
