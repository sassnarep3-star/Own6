# NFL Suggestions — How to Improve the Site to Improve Decision Making

**Date:** 2026-11-12 · **Session:** `arena/efebf74f-own6` · **Inventory:** `data/nfl/suggestions.csv` (S01–S12) · **Site page:** `docs/nfl/suggestions.html` (dedicated review section)

> These are proposals, not enacted changes. Someone should review the table, score `effort` vs `decision_impact`, and choose a path before any code is changed. That review happens on `docs/nfl/suggestions.html`; no suggestion is applied until recorded in `COORDINATION.md` (F-NFL-10).

## How this section improves decision making

1. **Traceability before commitment (S01–S02).** A requirements traceability table + a decision-readiness dashboard (have / missing / blank chips) make it impossible to approve a bet, line, or parlay when a required input is blank.
2. **Injury-aware pricing awareness (S03, S10–S11).** Per-unit deficiency badges translate the 2nd/3rd/4th-string backup risk into a visible flag before any model is trusted; ingestion is designed with no manual input and no scrape.
3. **Dependence literacy (S05, S12).** A correlation explorer with training-only, slate-clustered CIs plus a parlay-safety explainer teach that two overs in the same game are not independent.
4. **Gate discipline (S06–S07).** A validation-gate progress board and a leaderboard rewards charter prevent “nearly qualified” from becoming published as qualified.
5. **Transparency by default (S08–S09).** A sticky Flagged link and a source-coverage counter keep unverified items discoverable on every page.

## The twelve suggestions (summary)

| ID | Title | Effort | Impact | Risk if ignored |
|---|---|---|---|---|
| S01 | Requirements traceability table | low | high | Decisions without evidence |
| S02 | Decision-readiness dashboard | low | high | Premature commitment |
| S03 | Injury & depth deficiency indicator | medium | high | Underestimating backup risk |
| S04 | Own-line calculator (formulas, not prices) | medium | high | Opacity reduces trust |
| S05 | Correlation explorer with clustered CIs | medium | high | Overpricing combos |
| S06 | Validation-gate progress board | low | high | Gates skipped |
| S07 | Leaderboard rules & rewards charter | low | medium | Misunderstood incentives |
| S08 | Flagged-for-review prominence | low | high | Hidden uncertainty |
| S09 | Source-coverage counter | low | medium | Unverified tables slip through |
| S10 | Weekly injury-report ingestion (no scraping) | medium | medium | Provenance loss |
| S11 | Depth-chart deficiency model (quant.) | medium | high | Mispriced depth |
| S12 | Parlay safety explainer | low | medium | Overbetting correlated legs |

Full rows with problem/solution/remediation: `data/nfl/suggestions.csv` → `docs/nfl/suggestions.html`. Every row carries an official source, `needs review` status, and `Proposal only — not implemented` label.

## How to choose the best path

1. **Open** https://sassnarep3-star.github.io/Own6/nfl/suggestions.html.
2. **Filter** by `high decision_impact` → `low effort` first (quick wins): S01, S02, S06, S08.
3. **Rank** by dependency: gates board (S06) and flagged prominence (S08) should precede deficiency badges (S03) which depend on the ingestion design (S10–S11).
4. **Record** the chosen 1–2 items in `COORDINATION.md` (N9 section) before merging any `docs/nfl/` change.
5. **Implement** via `scripts/build_nfl.py` and re-run `scripts/check_nfl.py` — every new table row must carry an `official source` link or fail the build.

## What a chosen path looks like (example)

If S06 (gate board) + S02 (readiness chips) are selected, the next commit would:

- Add a one-page gate matrix to `docs/nfl/validation.html` with 10 gates × {open/blocked, config hash, ledger hash, source}.
- Add three-state chips (`have` / `missing` / `blank`) to the header of every `docs/nfl/*.html` page.
- Log the decision in the COORDINATION.md claim log and flag the old pages as superseded, not deleted.

Until that selection is recorded, the current dedicated review page fully satisfies the directive: suggestions are visible, scored, and blocked from silent auto-implementation.

## Sources per row

S01 [nfl.com](https://www.nfl.com/) · S02 [injury policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf) · S03 [league injury page](https://www.nfl.com/injuries/) · S04 [Next Gen Stats](https://operations.nfl.com/game-operations-logistics/technology/performance-tracking-data-next-gen-stats) · S05 [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · S06 [scikit-learn CV](https://scikit-learn.org/stable/modules/cross_validation.html) · S07 [nfl.com legal](https://www.nfl.com/legal/privacy/) · S08 [nfl.com terms](https://www.nfl.com/legal/terms/) · S09 [GitHub Pages docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · S10 [policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf) · S11 [official rules](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) · S12 [parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator)

---

## 2026-11-13 source correction (session 5a49ead3, NFL-R1)

Re-checked against live official pages on 2026-11-13. Corrections are in `data/nfl/sources.csv` and `data/nfl/flagged.csv` (flag F-NFL-13):

- The rules link is now the 2026 rulebook, `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook`. The previous `nfl.com/official-nfl-rules/` link returns 404.
- The injury link is now the live 2026 Week 10 report, `https://www.nfl.com/injuries/`. The previous `/injuries/league/2024/reg17` link is a 2024 page, retained only as S-NFL-25.
- The terms link is now `https://www.nfl.com/legal/terms/` (general terms). The previous `nfl.com/terms/` link redirects to subscription terms.
- The 2017 injury-policy PDF (`operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf`) returns 404. Any timing or definition claim that relies only on it is **unverified** until a live copy is located (F-NFL-03).
