# Own6 — NBA Lines Research Lab

A research-first project for originating NBA spreads, totals, win probabilities, player props and parlays. **Nothing in this repository demonstrates a profitable edge.** No player projections, prices, empirical correlations or backtest returns are asserted without evidence.

## Executive summary
Estimate outcome distributions independently, convert them to fair probabilities, and compare against timestamped executable market prices after vig and execution costs. Skill must survive time-ordered out-of-sample testing, calibration checks, uncertainty bounds, multiple-testing controls and market benchmarks. Parlays and player-prop combinations require joint probabilities; multiplying marginal probabilities assumes independence and is not a default.

Leaderboard rewards should be based on audited, preregistered, out-of-sample forecasts with uncertainty-aware eligibility—not raw win rate. Require adequate samples, proper scoring/calibration, market-relative results, drawdown reporting, and robust performance across periods. No historical data or sportsbook quotes are included here; measured advantage and correlation fields remain blank/unverified.

## Start here: unified hub

The data hub ([`docs/hub/index.html`](docs/hub/index.html), linked from the site landing page) is a category dashboard: executive summary, results, standings, lines, props, forward test, strategies, correlations, validation, sources and Flagged for Review, all generated from the committed data by `python3 scripts/build_hub.py` and checked by `python3 scripts/check_hub.py` and `python3 scripts/audit_integration.py`. Live: https://sassnarep3-star.github.io/Own6/docs/

## Live site contents
GitHub Pages publishes the organized site from [`docs/`](docs/index.html): dashboard/calculator, strategy catalog, validation gates, correlation methodology, leaderboard design, sources registry and Flagged for Review. See [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).

The Python package in `src/own6/` contains transparent modeling utilities, with tests in `tests/`. Inputs and model assumptions are not official NBA facts; do not interpret illustrative estimates as verified lines or betting advice.

## Sources and evidence boundaries
Official NBA sources used for metric definitions: [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) and [NBA Inside the Game Stat Glossary](https://www.nba.com/news/inside-the-game-stat-glossary). These sources do **not** verify predictive value, odds, correlation estimates or profitability. Unconfirmed values must remain blank and be flagged.

## Source-linked verified dashboard

A separate, source-checked section lives in [`docs/verified/`](docs/verified/index.html): the verified NBA schedule rows (Nov 2, 2026), Korean statute rows (국민체육진흥법), NBA official policy vs. unverified press reports, validation gates, and a Flagged for Review page. Data is in `data/*.json`; build with `python3 scripts/build_site.py` and check with `python3 scripts/check_site.py`.

## Research sub-site (session `arena/325834c9-own6`)

A second, independently verified research line lives in [`docs/own6/`](docs/own6/index.html):
92 official game results with per-row nba.com links (213/213 recomputation checks pass), a
walk-forward line-origination model with honest gate outcomes (**G1 not met — no edge claimed**),
measured parlay/prop correlations, a pre-registered strategy leaderboard with paper rewards, and a
Flagged-for-Review page. Research docs: [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) (session
section), [`research/`](research/strategies.md), [`verification/`](verification/verification_report.csv).
Build/check: `python3 scripts/build_site_own6.py` · `python3 scripts/linkcheck.py` ·
`python3 scripts/verify_data.py` · `python3 scripts/model.py`. DraftKings lines arrive via the
ESPN feed (secondary source, labeled as such); research/paper only — no real wagers.

## Luck vs skill: how much evidence a strategy needs

[`docs/luck/`](docs/luck/index.html) is a quantified answer to the question the brief puts
first: remove luck, reward only selective skill. It computes, in closed form, the bets
required to distinguish a real per-bet ROI from noise (a 3% edge at -110 needs ~6,200 bets,
and ~18,800 after correcting for 200 candidates), the smallest ROI a record of a given size
can resolve, the multiple-testing and correlation sample requirements, and a two-condition
rule (p-value plus Wilson lower bound above break-even) that fails 55/100 and even 540/1,000
at -110. The engine is [`src/own6/power.py`](src/own6/power.py), cross-checked against SciPy
and statsmodels (differences published in `data/luck/numerics_crosscheck.json`). The same
section carries a publication acceptance audit that resolves the repository's deployment
claims against the GitHub API. Build/check: `python3 scripts/build_luck.py`,
`python3 scripts/check_luck.py`, `python3 scripts/acceptance_audit.py --check`.
Everything on those pages is arithmetic: no NBA value, price or return is asserted, and the
leaderboard still holds zero qualified strategies.

## Empirical fail-closed lab

An isolated empirical extension lives in [`docs/lab/`](docs/lab/overview.html). It adds a strict data contract, six frozen strategy candidates, ten validation gates, event-clustered uncertainty, and a leaderboard that ranks only all-gate qualifiers by the lower bound of holdout ROI. With the bundled empty ledger it runs automatically and reports `not_run` — no synthetic or fabricated returns are published. Sources and scope limits are in [`research/EXECUTIVE_SUMMARY.md`](research/EXECUTIVE_SUMMARY.md), [`research/METHODOLOGY.md`](research/METHODOLOGY.md), and [`research/REPO_AUDIT.md`](research/REPO_AUDIT.md). Build and check with `python3 scripts/run_lab.py`, `python3 scripts/build_lab.py`, and `python3 scripts/check_lab.py`.

**No authorized NBA gambling-use data feed is configured.** NBA.com Terms §9 restricts NBA Statistics from being used in connection with any gambling activity, and §1 restricts public reuse. The NBA Stats FAQ says statistics are not available for download. The lab therefore does not scrape, republish, or invent NBA statistics, odds, correlations, or returns. No betting advice is provided.
