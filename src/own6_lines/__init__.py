"""Own6 NBA lines research engine.

This package originates NBA lines from official game results and scores
candidate strategies against each other on a time-ordered holdout.

Design rules (all enforced by :mod:`own6_lines.gates`):

* Inputs are official NBA results only. A row that cannot be traced to an
  nba.com source is never used.
* Every fit uses only games strictly earlier than the game it predicts.
  There is no look-ahead and no retuning on held-out outcomes.
* Legs are never combined by multiplying marginal probabilities. Joint
  dependence is estimated on training data and reported.
* No gate ever passes because evidence is missing. Missing evidence is a
  failure, never a pass.

Nothing in this package places bets, accepts stakes or advises on wagers.
It produces research measurements for evaluation.
"""
from __future__ import annotations

__all__ = ["data", "features", "model", "stats", "gates", "leaderboard", "report"]

__version__ = "1.0.0"
