# Own6 — NBA Lines Research Lab

A research-first project for originating NBA spreads, totals, win probabilities, player props and parlays. **Nothing in this repository demonstrates a profitable edge.** No player projections, prices, empirical correlations or backtest returns are asserted without evidence.

## Executive summary
Estimate outcome distributions independently, convert them to fair probabilities, and compare against timestamped executable market prices after vig and execution costs. Skill must survive time-ordered out-of-sample testing, calibration checks, uncertainty bounds, multiple-testing controls and market benchmarks. Parlays and player-prop combinations require joint probabilities; multiplying marginal probabilities assumes independence and is not a default.

Leaderboard rewards should be based on audited, preregistered, out-of-sample forecasts with uncertainty-aware eligibility—not raw win rate. Require adequate samples, proper scoring/calibration, market-relative results, drawdown reporting, and robust performance across periods. No historical data or sportsbook quotes are included here; measured advantage and correlation fields remain blank/unverified.

## Live site contents
GitHub Pages publishes the organized site from [`docs/`](docs/index.html): dashboard/calculator, strategy catalog, validation gates, correlation methodology, leaderboard design, sources registry and Flagged for Review. See [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

The Python package in `src/own6/` contains transparent modeling utilities, with tests in `tests/`. Inputs and model assumptions are not official NBA facts; do not interpret illustrative estimates as verified lines or betting advice.

## Sources and evidence boundaries
Official NBA sources used for metric definitions: [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) and [NBA Inside the Game Stat Glossary](https://www.nba.com/news/inside-the-game-stat-glossary). These sources do **not** verify predictive value, odds, correlation estimates or profitability. Unconfirmed values must remain blank and be flagged.

## Source-linked verified dashboard

A separate, source-checked section lives in [`docs/verified/`](docs/verified/index.html): the verified NBA schedule rows (Nov 2, 2026), Korean statute rows (국민체육진흥법), NBA official policy vs. unverified press reports, validation gates, and a Flagged for Review page. Data is in `data/*.json`; build with `python3 scripts/build_site.py` and check with `python3 scripts/check_site.py`.
