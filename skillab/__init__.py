"""skillab — luck-removal and selective-skill validation for NBA line strategies.

This package contains no NBA data. It implements the statistics used to decide
whether a betting strategy's observed record is distinguishable from luck, and
it computes every published number from either:

  * arithmetic / simulation with a fixed seed (reproducible, labelled SYNTHETIC), or
  * the repository's own committed CSVs (labelled IN-REPO RECOMPUTATION, with the
    file and row count named).

No value is copied from an unread source. No market price, correlation or return
is invented. See ``docs/skill/`` for the published report and its flags.
"""

from . import pricing, correlation, luck, gates, leaderboard, simulate, audit, power  # noqa: F401

__all__ = ["pricing", "correlation", "luck", "gates", "leaderboard", "simulate", "audit", "power"]
__version__ = "1.0.0"
