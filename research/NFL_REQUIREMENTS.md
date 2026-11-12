# NFL Requirements — Collect, Organize, Analyze

**Date:** 2026-11-12 · **Session:** `arena/efebf74f-own6` · **Inventory:** `data/nfl/requirements.csv` (R01–R18) · **Status:** research framework published; empirical values blank.

This document collects every requirement from the user directive, organizes them into categories, and analyzes what is satisfied by structure versus what still lacks authorized evidence.

## Collection method (line-by-line)

The requirement list was transcribed verbatim from the user message, then deduplicated and cross-referenced with the repo's existing verification rules (every row needs an official source link; unverified values stay blank; no hallucinations). Each row in `data/nfl/requirements.csv` contains `id / category / requirement / description / status / evidence_state / source_url`.

Official hosts used for manual-review links: `nfl.com`, `operations.nfl.com`, `docs.github.com`, `scikit-learn.org`, `docs.scipy.org`, `itl.nist.gov`, `statsmodels.org`, `sportsbook.draftkings.com`.

## Organized categories

| Category | IDs | Count | Evidence file | Published page |
|---|---|---|---|---|
| Governance | R01, R15, R16 | 3 | `audit/NFL_AUDIT.md`, `COORDINATION.md` | `docs/nfl/flagged.html`, `docs/nfl/sources.html` |
| Site & UX | R02, R03, R18 | 3 | `data/nfl/suggestions.csv` | `docs/nfl/suggestions.html`, `docs/nfl/index.html` |
| Decision Framework | R04, R05 | 2 | `data/nfl/decision_questions.csv` | `docs/nfl/questions.html` |
| NFL Analytics | R06–R13 | 8 | `data/nfl/origin_strategies.csv`, `data/nfl/validation_gates.csv`, `data/nfl/correlations.csv`, `data/nfl/injury_tracking.csv`, `data/nfl/depth_model.csv` | `docs/nfl/strategies.html`, `docs/nfl/lines.html`, `docs/nfl/leaderboard.html`, `docs/nfl/validation.html`, `docs/nfl/correlations.html`, `docs/nfl/injuries.html`, `docs/nfl/depth.html` |
| Executive | R14 | 1 | `research/NFL_EXECUTIVE_SUMMARY.md` | `docs/nfl/index.html` |
| Verification | R16, R17 | 2 | `audit/NFL_AUDIT.md` | every `docs/nfl/*.html` table |

## Analysis

### What the inventory satisfies (structural)

- **R01** — full list is captured and categorized; analysis below shows gaps between design and evidence.
- **R03 & R18** — a dedicated suggestions review page and a clean dashboard with category subpages, readable tables, and analysis sections exist in `docs/nfl/` (10+ pages) and pass `scripts/check_nfl.py`.
- **R10–R12** — ten validation gates, correlation method, and luck-control logic are specified with official methodological sources; leaderboard ranking uses the lower bound of a clustered holdout ROI, not a point estimate.
- **R13** — injury and depth-deficiency tracking is specified to the column level (practice participation, game status, inactive list, per-unit starter share, 2nd/3rd/4th-string flag).

### What remains open (evidence, not structure)

- **R06–R09, R11–R13** — every empirical value (own line, market line, correlation `r`, `n`, ROI, CLV) is blank because no authorized feed or licensed stat snapshot is on file (F-NFL-01…F-NFL-07). The design is verified; the numbers are not.
- **R16–R17** — verification is line-by-line at the row level: each CSV row carries `source_url`; each HTML row carries `official source`; unverified rows show `— blank / unverified`. See `audit/NFL_AUDIT.md` for counts.
- **R02** — suggestions for decision-making are proposals (F-NFL-10) and explicitly not implemented until selected.

### Traceability

Each requirement ID maps 1→1 to rows in the decision ledger (Q01–Q10), the suggestions table (S01–S12), and the flagged list (F-NFL-01–F-NFL-12). Example: R04 (questions/informations/answers) ↔ Q01–Q10 ↔ S02 (decision-readiness chips).

## How to use this inventory for decisions

1. Before any decision, open `docs/nfl/questions.html` and check that every `information_we_have` needed for the decision is not blank.
2. If any required cell is blank, follow that row's `discovery_suggestion`.
3. If a site improvement is desired, open `docs/nfl/suggestions.html`, compare `effort` vs `decision_impact`, select one, and record the pick in `COORDINATION.md` before editing code.

## Sources (verify each claim)

- NFL site identity and navigation: [nfl.com](https://www.nfl.com/)
- NFL standings (official reference for table identity): [nfl.com/standings](https://www.nfl.com/standings/)
- NFL schedule (official slate identity): [nfl.com/schedule](https://www.nfl.com/schedule/)
- NFL injury report league page: [nfl.com/injuries/league/2024/reg17](https://www.nfl.com/injuries/league/2024/reg17)
- NFL injury-report policy PDF (reportable-injury definition): [operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf)
- NFL official rules (possessions/scoring/overtime): [nfl.com/official-nfl-rules](https://www.nfl.com/official-nfl-rules/)
- Next Gen Stats methodology (pace/efficiency): [operations.nfl.com/gameday/technology/nfl-next-gen-stats](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats/)
- Cross-validation (chronology gate): [scikit-learn CV](https://scikit-learn.org/stable/modules/cross_validation.html)
- Calibration (proper scores): [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html)
- Confidence intervals: [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm)
- Multiplicity: [NIST Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) · [statsmodels multipletests](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html)
- Correlation: [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)
- Odds conversion: [DraftKings odds calculator](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB)
- Parlay payout ≠ joint probability: [DraftKings parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator)

Research only. No betting advice. Blank = unverified.
