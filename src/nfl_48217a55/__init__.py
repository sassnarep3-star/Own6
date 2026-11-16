"""Session 48217a55 — NFL decision-readiness pack.

Every published number in ``data/nfl_48217a55`` and ``docs/nfl-48217a55`` comes from
:mod:`nfl_48217a55.capture`, which holds only values read during this session from the
official pages listed in ``capture.SOURCES``. Nothing here touches the network at build
time, so a re-run must reproduce identical files.

Evidence rules (enforced by ``scripts/check_nfl_48217a55.py``):

1. A value is published only if it was read this session from the cited official page,
   or is arithmetic on such values with the derivation shown in the row.
2. Anything else is an empty cell plus a row in ``flagged.csv``. Never inferred.
3. Market/operator prices are not obtainable from an official source; ``market_*``
   columns stay blank with a capture-attempt log, never an estimate.
4. No profitability claim is made anywhere.
"""

__all__ = [
    "capture",
    "stats",
    "injuries",
    "model",
    "correlate",
    "gates",
    "advice",
    "flags",
]

SESSION_ID = "48217a55"
PACK = "nfl_48217a55"
PUBLIC_DIR = "docs/nfl-48217a55"
DATA_DIR = "data/nfl_48217a55"

#: Hosts accepted as "official" for the pack's own verifier. nfl.com hosts are not in
#: the repo-wide allowlists (see COORDINATION.md request R7), so the pack enforces them
#: locally rather than editing shared tooling.
OFFICIAL_HOSTS = (
    "www.nfl.com",
    "operations.nfl.com",
    "static.www.nfl.com",
    "www.chiefs.com",
    "github.com",
)
