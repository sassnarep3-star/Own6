# Methodology — Own6 Empirical NBA Lab

## Data contract

One row is one pre-event paper selection. The unit stake is one. Net return is `decimal_odds - 1` for a win, `-1` for a loss, and `0` for a push. A push is encoded as outcome `0.5`; pushes are excluded from binary proper scores and win-rate diagnostics but included in ROI. This convention must match the provider's settlement rules.

Every row requires:
- `observation_id`, `event_id`, `strategy_id`, `split`, and timezone-aware ISO-8601 timestamps for event start, forecast time, and feature availability.
- `event_start_utc` > `forecast_time_utc` ≥ `features_asof_utc`.
- `market` in `moneyline`, `spread`, `total`, `player_prop`, `prop_combo`, or `parlay`.
- `probability` and `market_probability` in `(0,1)`.
- `decimal_odds` and `closing_decimal_odds` > 1.
- `outcome` in `0`, `0.5`, or `1`.
- `line` must equal `closing_line` for CLV comparability.
- Official provider URLs, SHA-256 checksums, settlement URL, license ID, model version, and dependence evidence.

All source hosts must be in the rights-reviewed approved-host list. Missing evidence blocks qualification; it is never imputed.

## Splits and chronology

Only the `holdout` split can qualify. Features and model parameters are fit on earlier splits only. Qualification uses the untouched chronological holdout. Training outcomes must end before the evaluation window starts.

## Uncertainty

ROI, CLV, and predictive-quality improvements use a percentile bootstrap that resamples whole event clusters. Same-game and same-slate bets are clustered to preserve within-event dependence. Serial dependence across dates is not eliminated.

The binomial tail is a diagnostic only. Parlays and same-game props are clustered and heterogeneous; the heterogeneous-price Poisson-binomial diagnostic does not replace cluster-robust gates.

## Proper scoring

Brier and log loss are computed against the same non-push rows. Both must improve versus the same-selection de-vigged market with positive event-clustered lower bounds. Reliability bins are reported separately; a lower Brier score alone does not prove better calibration.

## Multiple testing

The Bonferroni adjustment is applied across all six frozen candidates, including abandoned ones. No adaptive search may add a new candidate after seeing holdout results.

## Joint dependence

Single bets use event clustering. Combos additionally require training-only joint evidence, adequate paired samples, and provider permission. Missing evidence is not independence.

## Gates

| Gate | Name | Requirement |
|---|---|---|
| G01 | Rights and market permission | Independently reviewed gambling-use/data rights and authorized market. |
| G02 | Field-level provenance | Official provider URLs, source hashes, settlement rules, and independent audit. |
| G03 | Chronological walk-forward | Features and fits precede decisions; decisions precede events; untouched holdout only. |
| G04 | Effective sample size | ≥ 200 holdout bets, ≥ 200 distinct event clusters, ≥ 200 non-push scoring observations. |
| G05 | Market-relative predictive quality | Positive Brier and log-loss improvement versus de-vigged market with positive clustered lower bounds. |
| G06 | Post-vig profitability | Positive unit-stake holdout ROI with event-clustered 95% bootstrap lower bound > 0. |
| G07 | Closing-line value | Positive mean `log(offered / closing)` with clustered lower bound > 0. |
| G08 | Luck and multiple testing | Heterogeneous-price diagnostic survives Bonferroni across all six candidates. |
| G09 | Joint dependence | Combos require verified joint evidence; singles use event clustering. |
| G10 | Frozen auditable ledger | Independent append-only timestamp audit, preregistration, one model version. |

## Leaderboard

Only strategies passing all gates qualify. Ranking uses the lower bound of event-clustered holdout ROI so small-sample heaters cannot win. Rewards are non-monetary research priority only. No payouts, stakes, or picks.

## Limitations

No method removes variance. The gates reduce the chance of mistaking luck for skill. A strategy that passes can still lose money. The empty ledger is the deterministic fail-closed default; it is not evidence of profitability.

## Sources

Official methodology links are in `data/empirical/sources.json`. The empty ledger and report are in `data/empirical/`. The built dashboard is in `docs/lab/`.
