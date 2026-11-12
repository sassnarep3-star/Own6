# NFL Signals — Originating Own Lines as a Leaderboard Competition

**Date:** 2026-11-12 · **Session:** `arena/efebf74f-own6` · **Catalog:** `data/nfl/origin_strategies.csv` (N01–N10) · **Status:** hypotheses only; zero qualified strategies; no active betting advice.

## The research question

> Does a frozen, pre-kickoff probability distribution for an NFL team total, spread, moneyline, player prop, prop combo, or parlay **beat the same-selection de-vigged market probability** after costs, under dependence-aware, out-of-sample validation?

It is not “which team will win?” but “does this model price a selection better than the market price of **that same selection on that same line**, after vig, with clustered uncertainty and family-wise error control?”

## How to originate an NFL line (method, not a result)

### 1. Team-level spreads / moneylines / totals (N01–N03)

1. **Possession basis.** Project possessions from recent pace and game-control features defined per [Next Gen Stats methodology](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats/) — possessions per game, not NBA's per-48. Fit on a licensed game log; never hard-code.
2. **Efficiency core.** Offensive and defensive efficiencies (points per drive, EPA per play) per [official rules](https://www.nfl.com/official-nfl-rules/); Net efficiency = Off − Def. Derive expected points = possessions × efficiency.
3. **Margin distribution.** Expected home margin = home-adjusted efficiency difference. Fit home advantage and margin SD from the same licensed log. Convert to win probability via logistic/normal margin CDF.
4. **Fair price without invented margin.** Convert win probability → fair American / decimal price with **no invented vig**. De-vig any market comparison on the *same line*; moved lines stay blank. Arithmetic per [DraftKings odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB).
5. **Total distribution.** Possessions × matchup efficiencies yields a scoring distribution, not a point estimate. Overtime rules (per [official rules](https://www.nfl.com/official-nfl-rules/)) must be explicit in settlement.

### 2. Player props (N04–N05)

Projected snaps/carries/targets × shrunk per-play/ per-target rate. Shrinkage toward a training-only league rate. Minutes only from timestamped official availability ([injury-report policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf)) — a player listed `Out` or inactive is not given a positive projection. Zeros for DNP rows are retained, not dropped. Settlement per provider is required ([over/under vocabulary](https://sportsbook.draftkings.com/help/how-to-bet-over-under)); unverified props stay blank.

### 3. Prop combos & parlays (N06–N09)

Joint probability is **not** the product of marginals. Estimating `P(over₁ ∧ over₂)` or two game wins requires a training-only paired residual sample, Pearson or phi correlation, and a whole-slab clustered CI. Use Gaussian copula as a documented joint model; independence is a labelled special case, never a default ([SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html): Pearson measures linear association in −1…+1; constant input is undefined). Parlay payout multiplication is a settlement formula, not a probability model ([parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator)). Cross-game legs require slate-level pairing and cluster bootstrapping ([bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)).

## Frozen candidate family (10 strategies)

| ID | Family | Market | Signal hypothesis (not proven) | Gate trigger | Status | Official reference |
|---|---|---|---|---|---|---|
| N01 | Single bet | Spread | Own fair spread deviates from licensed market spread beyond frozen edge → mispricing | \|edge\| ≥ threshold & G01–G10 | unverified | [Official rules](https://www.nfl.com/official-nfl-rules/) |
| N02 | Single bet | Total | Pace-blend extremes vs market-implied pace → total mispricing | Over-prob edge ≥ threshold | unverified | [Next Gen Stats](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats/) |
| N03 | Single bet | Win prob | Calibrated own win prob beats de-vigged market on same line | Calibrated edge ≥ threshold | unverified | [Calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| N04 | Player prop | Passing yards | Shrunk YPA × projected dropbacks beats line when QB/OL available | QB status Full & deficiency < flag | unverified | [Injury page](https://www.nfl.com/injuries/league/2024/reg17) |
| N05 | Player prop | Rushing yards | Workload × shrunk YPC captures backup-RB opportunity misprice | RB Full & starter share ≥ threshold | unverified | [Standings](https://www.nfl.com/standings/) |
| N06 | Prop combo | Same-player receiving+rushing | Same-player counting stats share touches; joint ≠ product | Joint sample n≥60 slates | unverified | [Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| N07 | Prop combo | QB+WR stack | QB and WR yards positively correlated via target share | Paired residual CI exists | unverified | [Official rules](https://www.nfl.com/official-nfl-rules/) |
| N08 | Parlay | Same-game spread+total | Pace and margin couple spread and total | Correlation CI excludes independence misuse | unverified | [Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| N09 | Parlay | Cross-game 2-leg | Cross-game independence must be tested not assumed | Slate-level cross-game test | unverified | [Bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) |
| N10 | Meta | CLV-first | Strategies beating same-line de-vigged close persist better than raw win rate | CLV gate t & CI pass | unverified | [Odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB) |

Details per row: `data/nfl/origin_strategies.csv` → `docs/nfl/strategies.html` and `docs/nfl/lines.html`.

## Leaderboard competition (rewards)

- **Eligibility:** only all-gate qualifiers (G01→G10) enter the board. The current [leaderboard](data/nfl/leaderboard.csv) is intentionally empty.
- **Ranking:** lower bound of the slate-clustered holdout ROI 95% interval, not the point estimate. A strategy can rank high only if its *worst-plausible* skill is positive.
- **Multiplicity:** Bonferroni (one-step) over the actual number of qualification statistics in the frozen family ([NIST](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm); [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html)). An independent-trial win-count is diagnostic only.
- **Rewards:** non-monetary research priority (promotion on the dashboard, first access to the next holdout). No cash payout, no guaranteed publication.
- **Freezing:** adding a candidate after inspecting holdout requires a new preregistered family and a new untouched holdout. Adaptive search outside the denominator is forbidden.

## What counts as a useful signal

A useful signal must survive the full gate set (see `research/NFL_VALIDATION.md`): rights, provenance (hashes, timestamps), chronological walk-forward, sample/precision floors (≥200 bets / ≥60 slates), market-relative Brier/log-loss, post-vig ROI lower bound, comparable same-line de-vigged CLV, multiplicity, joint dependence, and a frozen auditable ledger. A high win rate, a large historical correlation, or a profitable-looking backtest alone is insufficient.

## Current output (fail-closed)

The authorized observation ledger is empty. Therefore the site publishes **blank** current lines, blank correlations, blank performance metrics, and an empty leaderboard. That emptiness is an evidence state, not a prediction.

## Sources

- NFL schedule/standings identity: [schedule](https://www.nfl.com/schedule/) · [standings](https://www.nfl.com/standings/)
- Injury-report existence and vocabulary: [league injury page](https://www.nfl.com/injuries/league/2024/reg17) · [policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf)
- NFL rules and possessions: [official rules](https://www.nfl.com/official-nfl-rules/)
- Next Gen Stats methodology: [operations.nfl.com](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats/)
- Validation methodology: [scikit-learn CV](https://scikit-learn.org/stable/modules/cross_validation.html) · [calibration](https://scikit-learn.org/stable/modules/calibration.html) · [NIST CI](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) · [NIST Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) · [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · [DraftKings arithmetic](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB)

Research only. No betting advice.
