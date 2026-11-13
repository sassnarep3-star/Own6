# NFL lines lab - executive summary

Date: 2026-11-12. Season: 2026, Week 10. All values below are generated from
`data/nfl/model/*.json` and every one of them links to the page that shows its source.
Read the flagged items at the end before quoting any number.

## 1. The one-line answer

A transparent, opponent-adjusted model produces own lines for the Week 10 slate, but **none of the eight
frozen strategy candidates qualifies** under the ten validation gates, and the one signal that could be
tested loses money after vig on a season it never saw. The honest output of this project is a measured
"no", a working method, and a precise list of the data that would be required to try again.

## 2. What was built

| Piece | State | Where |
|---|---|---|
| Official-source reads | 89 checks, 0 discrepancies | `data/nfl/raw/`, `data/nfl/source_manifest.json` |
| Own lines, Week 10 | 14 games, market cells blank | `/nfl/lab/lines.html` |
| Model library | ratings, pricing, correlation, availability, validation, combos | `src/nfllab/` |
| Validation gates | 10 gates x 8 candidates | `/nfl/lab/validation.html` |
| Correlation study | 3 measured dependence studies + combo pricing | `/nfl/lab/correlations.html` |
| Injury board | 275 rows, 26 clubs | `/nfl/lab/injuries.html` |
| Depth deficiency | 13 starter-level rows, 3 clubs | `/nfl/lab/depth.html` |
| Questions | 18 questions, 7 blocking | `/nfl/lab/questions.html` |
| Suggestions | 15 ranked, none auto-applied | `/nfl/lab/suggestions.html` |
| Flagged for review | 12 unresolved items | `/nfl/lab/flagged.html` |

## 3. The result that matters

2025 holdout, fit window 2015-2024, one season never seen by the model:

| Strategy | Bets | Win rate | ROI per bet | 95% clustered interval |
|---|---|---|---|---|
| S1 spread | 172 | 51.7% | -1.2% | -12.3% to +10.4% |
| S2 totals | 111 | 50.5% | -3.7% | -24.3% to +17.3% |
| S3 moneyline dogs | 219 | 30.1% | -7.5% | -28.0% to +15.3% |

Not one interval excludes zero on the upside, and the only statistically distinguishable effect is negative.
Calibration against a coin-flip market baseline is also negative (Brier skill score
-0.113, n=205). That baseline is deliberately weak, so the result
says less about the market than it does about the model: **this model is worse than a coin flip**.

## 4. Why the leaderboard is empty

All eight candidates were frozen before the run. This is the gate board, generated from `data/nfl/model/backtest.json` - no status below was hand-assigned:

- **G01 (Data rights & market-permission audit)** - fail: S1, S2, S3, S4, S5, S6, S7, S8.
- **G02 (Field-level provenance)** - blocked: S1, S2, S3, S4, S5, S6, S7, S8.
- **G03 (Chronological walk-forward)** - blocked: S4, S5, S6, S7, S8; pass: S1, S2, S3.
- **G04 (Sample floor)** - fail: S1, S2, S3; blocked: S4, S5, S6, S7, S8.
- **G05 (Calibration vs market)** - blocked: S1, S2, S3, S4, S5, S6, S7, S8.
- **G06 (Post-vig ROI)** - fail: S1, S2, S3; blocked: S4, S5, S6, S7, S8.
- **G07 (Closing-line value)** - blocked: S1, S2, S3, S4, S5, S6, S7, S8.
- **G08 (Multiplicity control)** - fail: S1, S2, S3, S4, S5, S6, S7, S8.
- **G09 (Dependence & joint sample)** - blocked: S1, S2, S3, S4, S5, S6, S7, S8.
- **G10 (Deflated Sharpe ratio)** - fail: S1, S2, S3; blocked: S4, S5, S6, S7, S8.

The three *testable* candidates fail the same five gates: data rights (G01), the sample floor (G04 - 34 to 50 slate dates against a floor of 60), post-vig ROI (G06), multiplicity (G08) and the deflated Sharpe (G10). Closing-line value (G07) and calibration against a real market price (G05) are **blocked**, not passed: no price sidecar exists, so they can neither save a candidate nor condemn one.

Five candidates (S4-S8) cannot be evaluated at all. Between them they need opening lines, prop outcomes, prop prices and a dated injury archive. **The binding constraint is data capture, not modelling.**

## 5. Correlation: what may be multiplied

| Study | Measure | Result | Reading |
|---|---|---|---|
| C1 same-game cover + over | phi | +0.0224 (CI -0.0100 to +0.0560) | independence not rejected; joint is 1.023x the independent product |
| C2 cross-game pairs | phi | +0.0988 (CI -0.030 to +0.228) | indistinguishable from noise at n=234 |
| C3 abs margin vs total | Pearson r | +0.0341 (CI -0.0016 to +0.0683) | no usable relationship |

Practical consequence: for the one pair the data can test, an independence price is defensible **with the
measured ratio published beside it**. For player props, no dependence value exists at all - the page says so
instead of inventing one.

## 6. Injuries and depth deficiency

- 275 injury rows across 26 clubs were transcribed verbatim from
  NFL.com. Only six rows carried an explicit game status on the day of reading; the rest are published with a
  blank status rather than inferred from practice participation.
- Depth deficiency is computed for the three clubs whose official depth charts were captured
  (WAS 0.0087, NYG 0.0205, DET 0.0870 on a 0-1 scale).
  Detroit's number is driven by its quarterback (Jared Goff limited participation in practice, Joshua Dobbs at string 2, index 0.0525).
- The index is a published formula, not a measured points value. No snap-share or EPA-by-replacement data was
  obtained, so the site does not claim a points impact.

## 7. What would change the answer

1. **A licensed price feed with timestamps** (SG-03). Without it, closing-line value, de-vigged fair prices and
   every ROI statement stay unverifiable.
2. **Player-prop outcomes and prices.** Three of the eight candidates are prop-based and cannot start until this
   exists.
3. **A dated injury archive** (SG-05). This is the difference between listing injuries and pricing them.
4. **A better signal.** The correct target is information the closing line does not already contain -
   not a better team-strength estimate.

## 8. Flagged before you quote anything

- **F-N01** no verified market price exists for any Week 10 game; every market cell on the site is blank.
- **F-N02** the historical game log has no licence file; the backtest is a diagnostic, not a publishable record.
- **F-N03** NFL.com Terms section 1.3 limits use to individual, non-commercial, informational purposes and
  prohibits systematic retrieval to build a database. This site publishes derived analysis and small cited facts.
- **F-N04** historical bets are priced at an assumed -110, not an observed price.
- **F-N08** only 6 of 275 injury rows carry a game status as of the read.

The full list, with the source that would close each item, is on `/nfl/lab/flagged.html`.
