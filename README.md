# Own6 NBA Lines Lab

A transparent, research-first framework for originating NBA prices and evaluating single wagers, parlays, and player-prop combinations. This repository currently contains **research design, not a live pricing feed or a proven profitable model**. No odds, historical results, correlation estimates, or player-specific projections are fabricated.

## Executive summary

The goal is to estimate outcome distributions independently, convert them into fair probabilities/prices, and test whether they outperform a contemporaneous market benchmark after vig, slippage, and realistic execution. Skill is not demonstrated by a winning streak. It must survive out-of-sample, time-ordered testing, calibration checks, multiple-testing controls, and uncertainty bounds. Parlays require joint probabilities; multiplying leg probabilities is only defensible under independence, which is usually not established. Estimate joint behavior from historical paired outcomes or a documented joint model, and shrink unstable estimates.

**Do not treat any strategy here as a betting recommendation.** The repository has no validated historical dataset, market snapshots, verified odds feed, or backtest results. Accordingly, empirical edge, correlations, ROI, and leaderboard ranks remain blank/unverified. Public NBA sources define statistics; they do not verify sportsbook prices or predictive performance.

Proposed workflow: (1) acquire licensed, timestamped data and preserve source/version; (2) model player/team outcome distributions using availability, role, minutes and matchup features; (3) publish fair odds and uncertainty before the event; (4) calculate market-relative expected value net of vig; (5) enforce validation gates; (6) score only settled, auditable out-of-sample picks. The “Leaderboard” concept should reward robust out-of-sample log-score/calibration and market-adjusted return with minimum sample and uncertainty constraints—not raw win rate.

## Pages
- [Dashboard](index.html)
- [Strategy catalog](strategies.html)
- [Validation & correlation](validation.html)
- [Flagged for Review](flagged.html)

## Verification standard
Every factual metric definition in the tables links to an official NBA source. Unmeasured values are intentionally blank and flagged. Proposed analytical methods are clearly labeled as proposals and are not represented as official NBA facts. See [COORDINATION.md](COORDINATION.md) for provenance and verification notes.

## GitHub Pages
Static HTML/CSS/JS, no external runtime dependencies. Pages deploy from the repository via GitHub Actions after the workflow is enabled and GitHub Pages is configured to use GitHub Actions.
