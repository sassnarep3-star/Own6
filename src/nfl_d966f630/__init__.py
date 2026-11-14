"""Own6 NFL origination spine, session d966f630 (2026-11-14).

Eight pieces, one pipeline:

``results``     verified results feed and point-in-time aggregates
``prices``      append-only price-snapshot store (open / close per market)
``originate``   side -> total -> moneyline, fair / market / difference columns
``depth``       depth of the replacement, not the fact of it
``correlate``   correlations from official numbers only, with n on every row
``backtest``    settlement of published lines against verified results
``leaderboard`` signal separated from staking, ranked on signal alone
``demotion``    the gate that sends a live strategy back to paper
``flags``       the register of every blank, anomaly and disagreement
``advice``      suggestions and open questions, for a human to choose from
``audit``       requirements, decisions and findings, traced to files

Every external value lives in :mod:`nfl_d966f630.capture` and nothing else; the
rest is arithmetic on those captures.
"""

__all__ = ["advice", "audit", "backtest", "cache", "capture", "correlate", "demotion", "depth",
           "flags", "leaderboard", "originate", "prices", "results", "stats"]
