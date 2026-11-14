"""nfl_f4 — price snapshots, verified results, own-line origination and the
signal/staking-split leaderboard for the 2026 NFL season.

Design rules enforced across this package:

* Every published cell either comes from an official page read in-session
  (``status=verified``), is arithmetic over verified inputs
  (``status=derived``), or is a declared model output (``status=model_output``).
  Nothing else is allowed, and anything unsupported is emitted blank.
* No staking, ROI or "units won" figure is published unless a verified open and
  a verified close exist for the same market and the result is verified.
"""
