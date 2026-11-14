# NFL line origination, prices and proof — session `d966f630` executive summary

**Pack:** `src/nfl_d966f630` · **Data:** `data/nfl_d966f630` · **Site:** [`docs/nfl-d966f630/index.html`](docs/nfl-d966f630/index.html)
**Sources read:** 2026-11-14 (UTC) · **Branch:** `arena/d966f630-own6` · **Verification:** `python3 scripts/check_nfl_d966f630.py` (51 checks) and `python3 -m unittest discover -s tests -p test_nfl_d966f630.py` (61 tests)

---

## 1. What this pack adds

Eight requirements were added to the standing brief. All eight are implemented, and
each is checked by a rule in the verifier rather than asserted here:

| # | Requirement | Where it lives | State |
|---|---|---|---|
| 1 | Price-snapshot store with opening **and** closing numbers | [`prices.py`](src/nfl_d966f630/prices.py), `data/nfl_d966f630/price_snapshots.csv` | 210 rows, 171 markets, hash-chained, 0 chain breaks |
| 2 | Verified results feed so backtests and ROI are computable | [`results.py`](src/nfl_d966f630/results.py), `results_feed.csv` | 44 official games (Weeks 7–10), 37 identity checks, 96 reconciliations, 0 mismatches |
| 3 | Origination order: side → total → moneyline | [`originate.py`](src/nfl_d966f630/originate.py) | enforced; `StageOrderError` if the order is violated, tested |
| 4 | Fair line, market line and difference as separate columns | `O.published_columns`, `originated_lines.csv` | 21 columns; model filled, market + difference blank with a flag on every row |
| 5 | Leaderboard separates signal from staking | [`leaderboard.py`](src/nfl_d966f630/leaderboard.py) | two tables, two ranks; the checker rejects a payout column in one and an accuracy column in the other |
| 6 | Depth of the replacement, not the fact of one | [`depth.py`](src/nfl_d966f630/depth.py) | 347 report rows → 213 club-position groups with tiers-dropped floors + 11 evidenced replacement rows |
| 7 | Correlations from official numbers only, each with *n* | [`correlate.py`](src/nfl_d966f630/correlate.py) | 8 measured rows (n = 28…287), 5 published exclusions |
| 8 | A demotion gate back to paper | [`demotion.py`](src/nfl_d966f630/demotion.py) | 10 gates × 10 strategies = 100 evaluated rows; 1 promotion, 9 held, mechanism tested both ways |

Also delivered: single / parlay / same-game / prop-combo bet types (four families, two
gate-blocked), validation gates, correlation values, an explicit luck measure per
staking row, injury and backup-deficiency tracking, a suggestions register that
nothing auto-applies, and this summary.

## 2. The numbers that matter

| Measure | Value | How to recompute |
|---|---|---|
| Official games in the feed | 44 (W7 14, W8 14, W9 15, W10 1) | `R.feed_rows()` |
| League points per team-game at the W9 vintage | 22.963 | `R.league_baseline(9)` |
| σ of a team's points around its own expectation | 10.2808 pts (n = 86 team-games) | `O.dispersion(9)` |
| ρ(home points, away points) | −0.0659 (n = 43 games) | `O.dispersion(9)` |
| Mean abs error, published side | 10.50 pts vs 12.16 for a zero-margin line | `line_accuracy_graded.csv` |
| Mean abs error, published total | 11.24 pts vs 10.63 for the league baseline | same |
| Best fitted margin damping λ | 1.00 at the W9 vintage (MAE 10.598) | `O.fit_lambda(9)` |
| Best fitted total shrinkage | 0.00 (baseline beats the deviation term) | `O.fit_total_shrinkage(10)` |
| Markets with a measurable open→close movement | 26 of 171 (all cross-model-version) | `price_snapshots_open_close.csv` |
| Strategies live after the gate | 1 of 10 (`D966-STR-01`) | `DM.live_strategies()` |
| Flags published | 15 (4 gaps, 5 source anomalies, others caveats) | `flagged.csv` |

## 3. Four findings worth a reader's time

1. **The spread is signal; the total is not yet.** Over 44 graded games the published
   side beats a zero-margin line by 1.66 points of mean absolute error, and the
   damping scan prefers no shrinkage at all (λ = 1.00). On the total the scan runs the
   other way: the best shrink factor is 0.00, i.e. doubling the league's
   points-per-team beats the model's own total. The total-anchor strategy is the one
   the gate refuses to promote, and the reason published on its row is exactly this
   number, not a status word.
2. **Brier must be compared against its own event's base rate.** The moneyline-anchor
   strategy hits 73.3% of the time and looks excellent on raw Brier (0.192) — only
   because "the favourite wins" is a 73% event. Against that base rate its skill score
   is +0.018, and its calibration gap (0.1222 against a 0.08 tolerance) sends it back to
   paper while it still holds the top signal rank. That separation is requirement 5
   doing work, not decoration.
3. **Correlation is small, measured, and it moves parlays slightly.** With
   ρ(margin, total) = −0.283 and ρ(home points, away points) = −0.066 at n = 44, a
   same-game side-and-over ticket's joint probability sits about a point below the
   product of its legs on the illustrative pair (0.2756 vs 0.2860). No page in this
   pack quotes an invented "correlation discount".
4. **One official page contradicts itself, and the pack says so.** The Week 10 injury
   report prints five players under a club that their own position line contradicts
   (Garrett in the Rams table while listed LB Green Bay; Miller in the Cowboys table;
   Nelson in Seahawks; Njoku in Chargers; O'Connell listed LB for SEA), and Peter Woods
   as DT for one club and DE for another. Nothing was re-attributed: the rows are
   stored as printed and the affected depth counts are labelled floors
   (`flagged.csv` D966-F12).

## 4. What is blank, and why that is the answer

There is **no market price anywhere in this pack**. Four source classes were read or
attempted — the Week 10 schedule page, the official injury report, a licensed odds
feed (outside the session's network allowlist), and the prior session's published CSV,
whose own market cells are blank — and all four attempts are recorded in
`price_capture_attempts.csv`. So `market_line_*` and `difference_*` are empty on every
originated row, carrying `blank_no_licensed_market_price` and flag `D966-F01`.

The consequences are stated rather than smoothed over: no edge statistic, no
closing-line value, no ROI against a book, and no profitability claim. Prices used in
the backtest are the model's own (even money on sides and totals, our no-vig number on
moneylines), which makes every settled figure a calibration measurement. A perfectly
fair model breaks even against these prices **by construction** — see
`backtest.py`'s docstring, the leaderboard's `price_basis` column and the site footer.

## 5. Sample size, honestly

The feed holds Weeks 7–10 because that is what this session read. Every coefficient
publishes its n; six of ten strategies sit below the declared 20-graded-leg floor and
are shown as unranked rather than ranked on a thin sample; three rows carry
`substituted_forward_from_vintage_7` on their probability basis because no dispersion
was measurable at their own vintage. Backfilling Weeks 1–6 (suggestion `D966-S02`,
self-serveable: six page reads) lifts n from 44 games to about 136 and dissolves two
of the fifteen flags without needing any new kind of source.

## 6. What a human has to decide

Ten suggestions are in `data/nfl_d966f630/suggestions.csv`, every one in state
`awaiting_human_choice` with `applied_by_default = no`, each with a cost, a
risk-if-applied and a risk-if-not-applied — two of them argue against themselves.
Seven open questions in `questions.csv` name who must answer, what an answer unlocks,
and how we would find out without a human where that is possible (two of the seven are
fully self-serveable; the price-source question is not).

The single decision that gates the most work: **license one market-price source**. It
is the only thing that converts the difference column, edge and CLV from blanks into
measurements.

## 7. Rights and scope

Every value is copied from an official NFL page or is arithmetic on such values, cited
row by row, for individual non-commercial review under the
[NFL.com Terms and Conditions](https://www.nfl.com/legal/terms/); the prior session's
rights notes ([`data/nfl_309921cc/sources.csv`](data/nfl_309921cc/sources.csv), rows
NFL3-S01 and S02) are followed rather than re-litigated: no systematic scraping for
database compilation, no wagering action taken on league injury or officiating
information, no monetary reward on any leaderboard row (rewards are standing, compute
priority and a badge; `reward_tiers.csv` states why).

Reproduce this summary's numbers:

```bash
python3 scripts/build_nfl_d966f630.py          # rebuilds all 41 CSVs and 16 pages, byte-identical
python3 scripts/check_nfl_d966f630.py          # 51 line-by-line checks
python3 -m unittest discover -s tests -p "test_nfl_d966f630.py"   # 61 tests
```
