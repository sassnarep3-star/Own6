"""A tiny memo helper.

Several tables in this pack are recomputed from the same small set of captured
facts by the backtest, the leaderboard and the gate in one run. Without memoisation
a single report re-originates the same slate a few hundred times, which makes the
builder slow enough that people would be tempted to skip it. Nothing here changes a
number: the functions are pure over the captured tables in :mod:`capture`.
"""

from __future__ import annotations

import functools

def memo(fn):
    """Cache results for hashable arguments. Pure functions of captured data only."""
    return functools.lru_cache(maxsize=None)(fn)
