# Validation gates, luck-removal protocol, and results

Session `325834c9` · data cut 2026-11-02 · everything pre-registered before results were read.

## Why gates exist (methodology sources)

1. **Multiple-testing / overfitting** — the same backtest that finds a strategy also inflates it.
   Correcting the acceptance threshold for the number of trials tried:
   Bailey & López de Prado, *The Deflated Sharpe Ratio: Correcting for Selection Bias,
   Backtest Overfitting, and Non-Normality*, Journal of Portfolio Management 40(5):94–107, 2014
   ([ResearchGate](https://www.researchgate.net/publication/286121118_The_Deflated_Sharpe_RatioCorrecting_for_Selection_Bias_BacktestOverfitting_and_Non-Normality),
   [author publication list](https://quantresearch.org/Publications.htm)).
   Our protocol: every configuration tried is logged (N=1 so far: model v0.1); the gate
   threshold rises with N — we report trial counts alongside every result.
2. **Market benchmarks** — closing lines are the most efficient public forecast; beating them
   (CLV) is the standard skill test:
   Harvard DASH thesis on MLB closing-line accuracy, 1977–2018
   ([PDF](https://dash.harvard.edu/bitstreams/24950429-b1b7-4372-a029-1b68de1872e3/download));
   Szalkowski & Nelson, *The Performance of Betting Lines for Predicting the Outcome of NFL Games*
   ([record](https://www.researchgate.net/publication/233427163_The_Performance_of_Betting_Lines_for_Predicting_the_Outcome_of_NFL_Games));
   systematic review of ML sports betting, 2024 ([arXiv:2410.21484](https://arxiv.org/html/2410.21484v1)).
3. **Margin-based win models** — point differential is the standings (Pythagorean expectation,
   Morey exponent 13.91): [NBAAnalytic explanation](https://nbaanalytic.com/articles/pythagorean-expectation-nba-standings.html).
   Our model uses venue-adjusted shrunk margins + normal CDF instead of raw Pythagorean wins.
4. **Rest effects** — small but real in literature, so we tested rather than assumed:
   Entine, *The Role of Rest in the NBA Home Court Advantage* (B2B ≈ −1.77 pts vs 3+ days;
   rest explains ~10% of HCA) [Wharton PDF](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Nba.pdf);
   Small, NESSIS 2007 (B2B vs 3+ rest ≈ −2.26 pts; win-odds multiplier 0.62)
   [PDF](https://www.nessis.org/nessis07/Dylan_Small.pdf);
   NBAAnalytic 2025-26 season split (B2B 48.3% vs rested 50.4%, margin −1.17 vs +0.27)
   [link](https://nbaanalytic.com/articles/rest-back-to-backs-load-management.html).

## Luck-removal protocol (applied to every strategy)

- **Walk-forward only**: each game graded with statistics from strictly prior games
  (`scripts/model.py`), warmup 10 league games; no look-ahead.
- **Shrinkage**: strength prior weight k=8 games, scoring prior k=4, toward league average —
  early-season noise is pulled to neutral instead of being over-read.
- **Pre-registration**: gates, thresholds and strategy rules are written before results
  (this file + `research/strategies.md`); N trials logged for DSR-style deflation.
- **Baseline comparison**: every metric is reported against a naive baseline (coin 0.5,
  expanding home-win rate, expanding mean total) — raw accuracy alone proves nothing.
- **Uncertainty reported**: 95% percentile bootstrap (10,000 resamples, seed 42) on the
  paired log-loss difference; CIs that cross zero fail the gate even if the point estimate looks good.
- **Unconfirmable values stay blank**: e.g. SGA's season PPG was not collected → prop projection
  is blank + flagged, never inferred.

## Gates (pre-registered)

| Gate | Requirement | Status (2026-11-02) |
|---|---|---|
| G1 Calibration | walk-forward log-loss improvement vs expanding home-win baseline, 95% bootstrap CI strictly > 0 | **FAIL** — CI [−0.013, 0.073] |
| G2 Discrimination | model-favourite straight-up accuracy ≥ 55% over ≥100 graded games | **PASS point estimate** — 59.8%, but n=82 < 100 → partially met |
| G3 Correlation structure | pairwise correlation of every parlay/combo leg measured and used in joint pricing | PASS — measured (see [correlation.md](correlation.md)) |
| G4 Multiple testing | all tried configurations logged; thresholds deflate with N | PASS — N=1 logged |
| G5 Market benchmark (CLV) | mean closing-line value ≥ 0 over ≥100 bets | NOT TESTABLE yet — historical closing lines unavailable from official sources (flagged); tracking starts 2026-11-02 |
| G6 Sample size | ≥100 graded events for `VALIDATED` | 82 graded backtest games (of 92) |

## Backtest results (Own6 model v0.1, 82 graded games)

Source: [verification/backtest_metrics.csv](../verification/backtest_metrics.csv) ·
game-level rows: [data/backtest_walkforward.csv](../data/backtest_walkforward.csv)

| Metric | Model | Baseline (coin) | Baseline (expanding home-win) |
|---|---|---|---|
| Log-loss (↓ better) | **0.6747** | 0.6932 | 0.7059 |
| Brier (↓ better) | **0.2408** | 0.2500 | — |
| Straight-up sign accuracy | **59.8%** | 50.0% | 52.2% (season home WR) |
| Pearson r(pred, actual margin) | **0.210** | — | — |
| Totals MAE | 16.45 | — | 16.80 (expanding mean) |

- Paired log-loss difference (home baseline − model): mean **+0.0312**, 95% CI
  **[−0.0130, +0.0733]**, model better on 47/82 games → G1 **not met**.
- Estimated in-sample HCA: **1.64 pts** (season home-win rate 52.2% — early-season anomaly vs
  the ~3.4 pt / 59% long-run norm in the cited literature; small sample, flagged).
- Margin σ estimated: **16.48 pts** (2026-27 early returns show unusually large margins,
  e.g. ATL 128–81, CHA 81; this widens all model probabilities toward 50%).
- Decision: S-1 stays `TRACKING`. No strategy is `VALIDATED`; no edge is claimed.

## Model-vs-market snapshot (2026-11-02 slate)

[data/our_lines_2026-11-02.csv](../data/our_lines_2026-11-02.csv) · market rows carry the
per-event DraftKings/ESPN source URL; model rows cite `scripts/model.py`.

- Favourite agreement: **13/15** games (disagreements: WSH@ORL, POR@DEN — model takes the dog).
- Model totals vs market: biggest gaps **PHI−CHI** (model 227.9 vs market 239.5, −11.6) and
  **BOS@HOU** (model 228.3 vs 216.5, +11.8). These are model disagreements, not bets — S-2 is
  not deployable (totals MAE ≈ baseline).
- Open→current movement recorded for all 15 games (S-7 tracking data).
