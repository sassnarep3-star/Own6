# Validation protocol v2 — skill-seeking, not luck elimination

**Version:** 1.1.0 · **Date:** 2026-11-03 · **Status:** fail-closed; no authorized observations.

No statistical method can remove randomness from betting. This protocol reduces avoidable false discoveries by requiring pre-event evidence, market-relative scoring, dependence-aware uncertainty, multiplicity control and an untouched holdout. A qualified strategy can still lose. Nothing here is a betting recommendation or a promise of profit.

## 1. Rights and data boundary

The [NBA Terms of Use](https://www.nba.com/termsofuse#nba-statistics) restrict gambling use of NBA Statistics, and the [Stats FAQ](https://www.nba.com/stats/help/faq) does not offer a download. No authorized feed is configured. The engine therefore ships with an empty observation ledger, empty residual ledger, empty closing-probability sidecar and no approved rights records. It does not scrape or invent replacements.

## 2. Observation contract

The v1 observation header is preserved. Each row is one pre-event paper selection with:

- timezone-aware feature, forecast and event-start timestamps, with `features_asof <= forecast < event_start`;
- a strategy ID bound to its declared market;
- model probability, same-selection de-vigged market probability, executable decimal price and settlement outcome;
- official provider URLs, SHA-256 snapshot digests, settlement rules, license ID and frozen model version;
- a frozen minimum probability edge and conservative post-vig EV threshold.

The conservative EV bound treats any push mass as a loss. Because a push actually returns stake, true EV is at least this bound; no missing push probability is guessed. Combo partial-void settlement is not supported without a leg-level contract.

### Closing-line value

Raw price ratios confound probability movement with changing sportsbook margin. The optional `closing_probabilities.csv` sidecar supplies the same-selection, same-line **de-vigged closing probability**. CLV is:

`log(closing_fair_probability / entry_fair_probability)`

Positive values mean the entry price was better than the closing fair price. If the line moved, comparable CLV is blank and the CLV gate blocks. Missing closing evidence is never zero. See the [official operator odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB) and [spread push rules](https://sportsbook.draftkings.com/help/how-to-bet-spread).

## 3. Chronology and dependence

Only `holdout` rows can qualify. Training and validation are used for fitting and specification selection; the holdout is not a tuning set. The [scikit-learn cross-validation guide](https://scikit-learn.org/stable/modules/cross_validation.html) explains why fitting and evaluation must be separated.

The operational dependence cluster is the **Eastern calendar date of event start**. This is a project convention, not an official NBA slate identifier. It keeps same-night cross-game parlays together and avoids treating multiple bets on one slate as independent. Serial dependence across dates is not eliminated; the limitation is disclosed.

The sample floors are policy minima, not a power calculation: 200 holdout bets, 200 distinct events, 60 slate clusters and 200 non-push observations per candidate. A separate artifact-bound training-only power/precision audit is required. [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) explains that confidence belongs to the interval-producing method, not to a guaranteed future outcome.

## 4. Correlation and joint probability

Correlations use a strict training-only file with one row per pair/event, explicit cluster IDs, finite residuals, official source URLs, hashes and license IDs. Zero residuals are valid and retained. Duplicate pair/events, holdout rows, missing values and unreviewed rights are rejected.

- Continuous pairs use Pearson correlation with a paired whole-cluster percentile interval.
- Binary legs use phi correlation, computed from the same paired sample.
- Same-game player-point combos estimate `P(A > 0 and B > 0)` directly from paired residual hits.
- Cross-game parlays require binary win indicators and an explicit joint sample.

A correlation interval and joint-hit sample are required before a combo can pass. Multiplying marginal probabilities is not a default. Payout multiplication, described by the [official parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator), is not evidence that legs are independent. The [SciPy Pearson reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) defines association, not causation.

## 5. Validation gates

| Gate | Requirement | Official reference |
|---|---|---|
| G01 | Artifact-bound rights and market-permission audit | [NBA Terms](https://www.nba.com/termsofuse#nba-statistics) |
| G02 | Field-level provenance audit with official URLs and hashes | [NBA Terms](https://www.nba.com/termsofuse#nba-statistics) |
| G03 | Chronological walk-forward audit; no holdout tuning | [scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html) |
| G04 | Policy sample floors plus training-only power/precision audit | [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) |
| G05 | Positive Brier and log-loss improvement vs market, with clustered lower bounds | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| G06 | Positive post-vig ROI with clustered lower bound above zero | [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) |
| G07 | Positive comparable de-vigged CLV with clustered lower bound above zero | [DraftKings odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB) |
| G08 | Bonferroni across the actual qualification statistics for the full frozen family | [NIST Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) |
| G09 | Training-only paired joint evidence and clustered interval for combos | [SciPy Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| G10 | Artifact-bound preregistration, ledger audit and one frozen model version | [Repository contract](https://github.com/sassnarep3-star/Own6/blob/main/research/empirical/DATA_CONTRACT.md) |

## 6. Multiplicity and leaderboard

The frozen family has six candidates. Four qualification statistics are tested per candidate: ROI, Brier improvement, log-loss improvement and CLV. Missing candidates/tests are padded as `p = 1`; abandoning a strategy cannot shrink the family. Bonferroni is applied across all 24 tests. The independent-trial Poisson-binomial win-count test remains a labeled diagnostic only.

Bootstrap p-values are approximate, not exact randomization tests. Bonferroni controls family-wise error when the input p-values are valid; it does not repair leakage, bad provenance or an invalid dependence model. Only strategies passing **all ten gates** enter the leaderboard, ranked by the lower bound of slate-clustered holdout ROI. Rewards are non-monetary research priority only. No payouts, stakes or picks are produced.

## 7. Audit evidence

`evidence.json` uses schema version 2. Each audit record must name a reviewer, date, HTTPS artifact URL, artifact SHA-256, explicit scope, current config hash and current ledger hash. A boolean alone is rejected. This validates the binding of supplied evidence; it does not independently certify the external artifact offline. The bundled file contains no records, so every external-evidence gate remains blocked.

## 8. Current result

`python scripts/run_lab.py` reports `not_run`, zero authorized observations, zero qualified strategies and an empty leaderboard. All empirical correlation, edge, ROI and CLV fields remain blank. This is the correct result for the available evidence, not a failed attempt to manufacture a winner.
