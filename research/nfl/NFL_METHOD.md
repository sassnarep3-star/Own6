# NFL lines lab - method

## 1. Data

| Input | Rows | Source | Licence |
|---|---|---|---|
| Official standings | 32 | https://www.nfl.com/standings/ | NFL.com terms, section 1.3 (research use) |
| Week 9 finals | 15 | https://www.nfl.com/schedules/2026/by-week/week-9 | same |
| Week 10 slate | 14 | https://www.nfl.com/schedules/2026/by-week/week-10 | same |
| Week 10 injury report | 275 | https://www.nfl.com/injuries/ | same |
| Depth charts (WAS/NYG/DET) | 178 | club sites | same |
| Historical game log 2015-2026 | 3,167 | https://github.com/leesharpe/nfldata | **none - flagged F-N02** |

The historical log is used only to fit and test the model. Every published claim about the 2026 season is
checked against a verbatim official read first (`scripts/nfl_reconcile.py`, 89 checks,
0 discrepancies).

## 2. Ratings

Alternating least squares on (points for, points against) with an opponent adjustment, a season decay of 0.55
per year, and empirical-Bayes shrinkage of `g / (g + 6)` games. Home field is estimated from the data
(1.97 points in the window), not assumed. The fit for a holdout season uses **only** earlier seasons.

## 3. Pricing

Own line = the model's expected margin, snapped to the nearest half point. Probabilities come from a normal
approximation with a measured out-of-sample margin SD of 13.89 points and a
total SD set 6% wider as a stated assumption. Whole-number lines carry an explicit push band; pushes are never
split 50/50. `pricing.cover_probability` uses the home-spread sign convention (negative = home favoured); the
test suite pins that convention.

## 4. Validation

Ten gates, frozen before the run. A gate that cannot be evaluated is **blocked**, never passed. A candidate is
rejected if any gate fails, even when other gates are blocked. Ranking, if any candidate ever qualifies, uses the
lower bound of a slate-clustered bootstrap, not the point estimate, and the deflated Sharpe requires 95%
confidence after accounting for the number of trials.

## 5. Correlation

* C1: same-game cover and over, phi on 2,792 games, slate-clustered bootstrap over 570 dates,
  Fisher exact test, and the observed/independent ratio.
* C2: cross-game pairs on the same slate, 234 pairs.
* C3: absolute margin against total points, 2,895 games.
* Combo pricing shows independence, copula, and both Frechet bounds, so a reader sees the honest range.

## 6. Availability

Position weights, string penalties and practice-risk multipliers are **published assumptions**, not measured
values; they live in one dict in `src/nfllab/availability.py`. The index is capped at 1.0 per club. No snap-share
or points-lost value is claimed.

## 7. What the method cannot do

- It cannot price a market without a licensed price feed (F-N01).
- It cannot test props without prop outcomes and prices (F-N07).
- It cannot claim a profit from a backtest priced at an assumed -110 (F-N04).
- It cannot show skill from one holdout season; a single season can reject a strategy but never prove one.
