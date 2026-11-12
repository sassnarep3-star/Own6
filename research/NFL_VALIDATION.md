# NFL Validation — Ten Gates, Clustered Uncertainty, and the Leaderboard Ranking Rule

**Version:** 1.0.0 · **Date:** 2026-11-12 · **Session:** `arena/efebf74f-own6` · **Ledger:** empty (fail-closed) · **Gates ledger:** `data/nfl/validation_gates.csv` (G01–G10)

No statistical method removes randomness from betting. This protocol reduces avoidable false discoveries. A qualified strategy can still lose.

## 1. Rights and data boundary (G01)

[NFL Terms](https://www.nfl.com/terms/) and the landing at [nfl.com](https://www.nfl.com/) make clear that NFL Content is subject to reuse limits; no gambling-use analytics license is implied. The [injury-report policy](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf) describes reporting obligations; it is not a data license. Therefore no authorized feed is configured and the observation ledger is empty. The engine does not scrape or invent a substitute.

## 2. Observation contract and chronology (G02–G03)

Each pre-kickoff observation (if it existed) would carry `feature_asof ≤ forecast < event_start` with ET timestamps, strategy ID bound to its declared market, model probability, same-selection de-vigged market probability, executable decimal price, outcome, provider URLs, SHA-256 snapshot digests, settlement rules, license ID, frozen model version, and frozen minimum edge / conservative post-vig EV threshold. The conservative EV bound treats push mass as a loss; true EV is ≥ the bound — no missing push probability is guessed. Combo partial-void settlement without a leg-level contract is not supported.

Chronology is walk-forward: training → validation → holdout by Eastern calendar date (the date of kickoff). Only `holdout` rows can qualify. Fitting and evaluation must be separate — [scikit-learn CV guide](https://scikit-learn.org/stable/modules/cross_validation.html): “Learning the parameters of a prediction function and testing it on the same data is a methodological mistake.”

The operational dependence cluster is the **Eastern calendar date of event start**. This keeps same-slate cross-game parlays together and prevents counting multiple bets on one slate as independent. Serial dependence across dates is not eliminated; the limitation is disclosed.

## 3. Sample floors and precision (G04)

Policy minima, not power calculations: 200 holdout bets, 200 distinct events, 60 slate clusters, 200 non-push observations per candidate. A separate artifact-bound training-only power/precision audit is required. [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm): “The level of confidence is associated with the method of calculating the interval” — not with a guaranteed future outcome.

## 4. Market-relative proper scores (G05)

Brier loss and log-loss on holdout vs the market's de-vigged probability on the *same selection and same line*. A lower Brier alone does not prove calibration — [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html): inspect reliability separately. Improvement is required with uncertainty: calibration gate blocks unless model proper score is strictly better than market.

## 5. Post-vig ROI (G06)

`ROI = (sum profit / sum stake) − 1` after vig, using executable price. Lower-bound gate: the 95% slate-clustered bootstrap interval's lower bound must exceed zero ([SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)). Raw win rate is not a gate; American ↔ implied conversion follows [DraftKings formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB).

## 6. Comparable de-vigged CLV (G07)

Raw price ratios confound probability movement with changing margin. The optional `closing_probabilities.csv` sidecar supplies the same-selection, same-line **de-vigged closing probability**. `CLV = log(close_fair / entry_fair)`. Positive means entry was better than fair close. If the line moved, comparable CLV is blank and blocks the gate. Missing close is never zero. Spread pushes void per [DraftKings spread](https://sportsbook.draftkings.com/help/how-to-bet-spread).

## 7. Multiplicity (G08)

Bonferroni (one-step) over the actual qualification statistics in the frozen family — [NIST Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) and [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html). An independent-trial win-count test is diagnostic only. Adding a candidate after seeing holdout requires a new family and a new holdout.

## 8. Correlation and joint probability (G09)

Training-only paired residual file: one row per pair/event, cluster ID, finite residuals, source URLs, hashes, license IDs. Zeros are retained. Duplicates, holdout rows, missing values, and unreviewed rights are rejected.

- Continuous pairs: Pearson `r` with whole-cluster percentile interval ([SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)).
- Binary legs: phi correlation from same paired sample.
- Same-player combos: `P(A∧B)` estimated directly from paired residual hits.
- Cross-game parlays: binary win indicators + explicit joint sample; independence never default.

Multiplying marginals is not a valid default. Payout multiplication is distinct from joint probability ([parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator)).

## 9. Frozen auditable ledger (G10)

Selections must be written **before kickoff** to an immutable ledger with config hash + ledger hash + artifact URL / hash + reviewer + scope. A boolean “audit passed” alone is rejected. The ledger must be reproducible: re-running `python3 scripts/run_lab.py` (or NFL equivalent) on the committed ledger deterministically yields the same report.

## 10. Leaderboard ranking — removing luck, not eliminating it

Only all-gate qualifiers enter the board. Ranking uses the **lower bound** of the slate-clustered holdout ROI interval, not the point estimate. A strategy can rank highly only if its *worst-plausible* skill exceeds zero. Bonferroni, proper scores, clustered CIs, and frozen preregistration together make it harder for a lucky streak to impersonate skill — they cannot guarantee that a qualified strategy will win next week.

Current output: `data/nfl/leaderboard.csv` contains `— no qualifier` (verified empty).

## Verification of this document

Each gate row in `data/nfl/validation_gates.csv` carries an official `source_url`. The pages `docs/nfl/validation.html` and `docs/nfl/correlations.html` render each gate row with an `official source` link. Blanks carry the `— unverified` badge and are flagged F-NFL-01…F-NFL-09.

## No betting advice

Research framework only. No profitability claim. See `audit/NFL_AUDIT.md`.
