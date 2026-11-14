"""NFL own-line origination, price snapshots, verified results and skill-gated competition.

Every number that reaches a published table in this package is either
(a) transcribed verbatim from an official NFL-family page during the capture
session recorded in :mod:`nfl_market.capture`, or
(b) computed by this package from those captured numbers, in which case the
    computation is reproducible from the committed CSVs.

No market price, no closing line and no opening line is present in the capture
because no official NFL page publishes one (``https://www.nfl.com/odds/``
returns the NFL 404 page; see findings in ``data/nfl_market/flagged.csv``).
Those columns therefore ship blank with an explicit
``unverified_no_official_price_source`` status instead of being filled in.
"""

__all__ = ["capture", "model", "snapshots", "backtest", "depth", "correlations", "demotion"]
