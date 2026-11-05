# Luck-exclusion power analysis and publication acceptance — 2026-11-05

Session `arena/95c04c74-own6`. Branch `arena/95c04c74-own6`. Base commit `33165a0` (`origin/main`).

This note records what was built, what was verified, against which source, and what could
not be read at all. Nothing here asserts an NBA fact, a market price, a correlation value
or a return.

---

## 1. What the session set out to do

The project brief asks for a strategy competition in which luck is removed and only
selective skill is rewarded. The repository already contains the strategy framework,
validation gates and a fail-closed leaderboard, but it had no quantitative answer to the
question that decides whether any of that matters: **how much evidence is needed before a
record stops being explainable by luck, and how much more is needed when many candidates
compete?**

Nothing in the repository could answer that from official basketball sources, because no
authorised odds or results ledger is available. The answer does not depend on basketball
data at all: it is closed-form statistics. That is what this session added — the one class
of number that can be published honestly while the empirical inputs remain unavailable.

## 2. Deliverables

| Path | Purpose |
| --- | --- |
| `src/own6/power.py` | Standard-library engine: price conversions, per-bet moments, required sample size, minimum detectable ROI, Bonferroni, Benjamini–Hochberg, exact binomial p-values, Wilson intervals, Fisher-z sample size, two-condition luck verdict |
| `scripts/luck_analysis.py` | Generates `data/luck/*.csv` deterministically (`--check` enforces it) |
| `scripts/verify_luck_numerics.py` | Recomputes the same quantities with SciPy/statsmodels and records the differences in `data/luck/numerics_crosscheck.json` |
| `scripts/acceptance_audit.py` | Publication acceptance audit; caches the GitHub API snapshot in `data/acceptance/github_state.json` |
| `scripts/build_luck.py` | Builds the seven pages under `docs/luck/` |
| `scripts/check_luck.py` | Gate: reproducibility, one source link per table row, no non-https links, no merge markers, blocked ≠ verified |
| `tests/test_power.py` | 33 tests, including SciPy/statsmodels cross-checks |
| `tests/test_luck_site.py` | 15 publication-rule tests (standard library only) |
| `.github/workflows/luck.yml` | CI job `luck-skill` |
| `docs/luck/**` | Overview, sample size, parlays/props, multiple testing, method and checks, acceptance, flagged for review |
| `data/luck/flags.csv` | L-01 … L-10, published on the Flagged for Review page |

## 3. Headline computed results (arithmetic, not observations)

Verified by `scripts/luck_analysis.py --check` and by the committed cross-check record.

| Question | Result |
| --- | --- |
| Bets to detect a 3% ROI at −110, one-sided α = 0.05, 80% power | 6,221 |
| Same, after Bonferroni over 200 candidates | 18,800 |
| Bets to detect a 5% ROI at −110 | 3,735 |
| Smallest ROI separable from luck with 500 bets at −110 | 10.60% |
| Smallest ROI separable with 1,000 bets | 7.50% |
| Paired observations to detect r = 0.10 (Fisher z, two-sided, 80% power) | 783 |
| Paired observations to detect r = 0.30 | 85 |
| Expected pure-noise winners among 200 candidates at α = 0.05 | 10 |
| Graded 6-leg parlays at an assumed 2% edge per leg, independent baseline | 20,685 |
| 55 wins in 100 bets at −110 | p = 0.336 → **explainable by luck** |
| 540 wins in 1,000 bets at −110 | p = 0.160 → **explainable by luck** |
| 560 wins in 1,000 bets at −110 | p = 0.0118, Wilson low 0.5291 > 0.5238 → exceeds luck |

Interpretation: a leaderboard that rewards the top record over a few hundred bets is
ranking noise. The threshold is thousands of graded bets per candidate, and the
multiple-testing correction multiplies it again.

## 4. Verification performed in this session

| Check | Tool | Result |
| --- | --- | --- |
| Normal quantiles vs `scipy.stats.norm.ppf` | `scripts/verify_luck_numerics.py` | max abs difference 0.0 |
| One-sided exact binomial p-value vs `scipy.stats.binomtest`, 140 grid points | same | max abs difference 4.53e-13 |
| Wilson interval vs `statsmodels proportion_confint(method="wilson")` | same | max abs difference < 1e-9 |
| Benjamini–Hochberg q-values vs `statsmodels multipletests(method="fdr_bh")` | same | max abs difference < 1e-9 |
| Sample size vs closed form using SciPy quantiles | same | 0 bets difference |
| Fisher-z required pairs vs closed form using SciPy quantiles | same | 0 pairs difference |
| Committed tables regenerate exactly | `luck_analysis.py --check` | pass |
| Every table row carries an https source link | `check_luck.py` | pass |
| Blocked verifications are not labelled verified | `check_luck.py`, tests | pass |
| GitHub Pages source and latest build | GitHub API | `main:/`, latest build `33165a0`, status `built`, no error |
| Every PR referenced in `COORDINATION.md` resolves | GitHub API | 25/25 resolve; 22 merged |
| Repository scripts referenced by CI workflows exist | static parse | 7 workflows, 0 missing scripts |
| Internal links, https-only externals, merge markers across all 64 pages | `acceptance_audit.py` | 0 broken local links, 0 http links, 0 markers |
| Every page reachable from another page | inbound-link graph | 0 unreachable (2 fixed this session) |

Libraries installed from PyPI in an ignored virtualenv: SciPy 1.17.1, NumPy 2.4.6,
statsmodels (dev-only). None is required at runtime or in CI.

## 5. What could not be verified — and why

This sandbox has egress only to `github.com`, `codeload.github.com`, `api.github.com`,
`registry.npmjs.org`, `pypi.org` and `files.pythonhosted.org`. Direct probes:

```
https://www.nba.com/termsofuse            -> HTTP 000
https://www.nba.com/stats/help/glossary   -> HTTP 000
https://www.law.go.kr/                    -> HTTP 000
https://www.espn.com/nba/                 -> HTTP 000
https://sassnarep3-star.github.io/Own6/docs/ -> HTTP 000
```

Consequences, all published as flags:

* **No official NBA, statute or press page was re-read.** Every inherited official-source
  row keeps its earlier status; none is re-certified here. Claims A13/A14 in the acceptance
  audit are recorded as `verification blocked`, and the checker fails if that changes while
  the environment is offline.
* **The live site could not be opened.** Deployment is evidenced only through the GitHub
  Pages API (source `main:/`, latest build `built`, matching `main`).
* **Merge commit SHAs quoted in the coordination board are not assessable.** The clone is
  shallow (two commits), so absence of a SHA locally proves nothing.
* **Method documentation was not read.** SciPy/statsmodels/NIST links are citations; the
  in-session verification is the numerical cross-check, not a reading of those pages.

## 6. Irregularities found and their disposition

| ID | Finding | Disposition |
| --- | --- | --- |
| L-01 | No official source re-readable from this sandbox | needs review — recorded on the Flagged page |
| L-02 | NBA Terms §§1/9 rights limits not re-read, no permission or legal opinion | needs review — inherited, unresolved |
| L-03 | Four PRs from other sessions remain open (#23, #28, #31, #37); their work is not on the published site | needs review — this session merged none of them |
| L-04 | `docs/hub-evidence/index.html` and `docs/reverification/index.html` were published but unreachable | fixed — additive landing-page links |
| L-05 | `docs/dashboard.html` linked to `lab/`, a directory with no index, so the link 404'd | fixed — now `lab/overview.html` |
| L-06 | `docs/hub-evidence/index.html` and `docs/parlay-safety/index.html` have no generator script | needs review — disclosed in the inventory |
| L-07 | Requirements assume independence and fixed prices; same-game legs are dependent | info — independence baseline labelled on every parlay row |
| L-08 | Zero strategies are skill-eligible; the ledger is empty (`not_run`) | info — intended fail-closed state |
| L-09 | Cited merge SHAs not assessable in a shallow clone | needs review |
| L-10 | SciPy/statsmodels/NIST documentation not read this session | needs review — cross-check published instead |

Two defects found by this session's own audit were repaired (L-04, L-05). The remainder are
disclosed, not resolved, and are published at `docs/luck/flagged.html`.

## 7. Cross-scope changes, logged rather than hidden

| File group | Owner of record | Change | Why |
| --- | --- | --- | --- |
| `docs/index.html` | shared navigation | three additive links (`luck/index.html`, `hub-evidence/index.html`, `reverification/index.html`) | the new section and the two fixed orphans need an entry point; no existing link or text was changed |
| `docs/dashboard.html` | shared, legacy | one href corrected | it was the only broken internal link on the site (A08/L-05) |
| `data/source_coverage/**`, `docs/coverage/**`, `audit/SOURCE_COVERAGE.md` | session fd5276fa | regenerated by their own script so its `--check` gate passes with the new pages | derived snapshot; no analysis or claim changed. Same precedent as PR #37 |

## 8. Reproduction

```bash
python3 scripts/luck_analysis.py --check
python3 scripts/acceptance_audit.py --check      # uses the committed API snapshot
python3 scripts/build_luck.py --check
python3 scripts/check_luck.py
python3 -m unittest tests.test_power tests.test_luck_site
# optional, needs scipy/statsmodels:
python3 scripts/verify_luck_numerics.py
```

## 9. Non-claims

No profitability claim. No prediction. No NBA value is published on these pages: the tables
are requirements, the flagged values are blank, the leaderboard is empty, and no wager is
recommended or simulated with real money. The NBA Terms of Use were not read this session;
their §§1 and 9 restrictions remain unresolved and are flagged.
