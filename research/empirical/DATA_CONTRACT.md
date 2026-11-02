# Licensed observation contract v1

## Default behavior

`python scripts/run_lab.py` reads the empty `data/empirical/observations.csv` and writes a deterministic `report.json` with `status: not_run`, zero observations and no qualified strategies. It requires no user input, credentials, network access, or manual typing. It does not fabricate a replacement dataset.

No authorized provider is configured. The rights registry and approved-host list are intentionally empty. This is a fail-closed research harness, not a live betting feed. Synthetic test fixtures are confined to `tests/empirical/` and never enter the report.

## One row = one pre-event paper selection

The unit stake is one. Net return is `decimal_odds - 1` for a win, `-1` for a loss and `0` for a push. A push is encoded as outcome `0.5`; pushes are excluded from binary proper scores and win-rate diagnostics but included in ROI. This convention must match the provider's settlement rules.

| Field | Contract |
|---|---|
| observation_id | Unique immutable identifier; duplicates are rejected. |
| event_id | Shared by all legs/bets exposed to the same game; uncertainty resamples this cluster, not individual rows. |
| strategy_id | Must belong to the frozen six-candidate registry, including rejected/abandoned candidates. |
| split | `train`, `validation`, or `holdout`; only chronological holdout rows can qualify. |
| event_start_utc | Timezone-aware ISO-8601 event start. |
| forecast_time_utc | Timezone-aware decision timestamp, strictly before event start. |
| features_asof_utc | Feature availability timestamp, no later than the decision and before event start. |
| market | `moneyline`, `spread`, `total`, `player_prop`, `prop_combo`, or `parlay`. |
| selection | Explicit selection and side; no ambiguous team-only string. |
| line | Numeric handicap/total/prop threshold where applicable; blank for moneyline. |
| probability | Model win probability in (0,1), frozen at decision time. |
| market_probability | Same-selection, same-line de-vigged market probability in (0,1), from both sides at decision time. |
| decimal_odds | Executable offered decimal price, strictly greater than 1. |
| closing_decimal_odds | Closing price for the identical selection and line; missing is not zero. |
| closing_line | Must equal the offered line where a line applies; changed lines are not comparable CLV evidence. |
| outcome | `1` win, `0` loss, or `0.5` push under the linked settlement rule. |
| odds_source_url / close_source_url | Official provider URLs for the offered and closing quote snapshots. |
| result_source_url | Official authorized result source. |
| feature_source_url | Official authorized feature snapshot source. |
| *_sha256 | Lowercase 64-hex checksum of the corresponding source snapshot, not a guessed hash of a mutable webpage. |
| license_id | Must resolve to an independently reviewed rights record covering this use. |
| settlement_url | Official provider settlement-rule document. |
| model_version | Immutable model/code version; changing it requires a new preregistered experiment. |
| dependence_evidence | `not_required` for single bets; `verified` for combos only with training-only joint evidence and provider permission. Missing never means independent. |

All source hosts must be in the rights-reviewed approved-host list. URLs must use HTTPS. Hashes, timestamps, prices, outcomes, probabilities and identifiers are validated before any metric is calculated. Missing evidence blocks qualification; it is never imputed.

## What the ledger cannot prove by itself

A CSV can still contain look-ahead bias or fabricated timestamps. Production qualification additionally needs an append-only, independent timestamp authority, frozen feature snapshots, reproducible model artifacts and an auditable record of every candidate tried. Those controls are not present here, so the ledger-integrity gate remains blocked even if rows are later added.

## Rights and privacy

NBA.com Terms of Use §§1 and 9 are material constraints. The NBA's official October 26, 2026 release identifies Sportradar as its official data distribution partner for authorized markets; that announcement is not a license for this repository. No credentials, personal betting records, or restricted data are collected. The project does not place bets, accept stakes, distribute rewards, or provide picks.
