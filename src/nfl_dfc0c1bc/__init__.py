"""nfl_dfc0c1bc — the cross-pack decision board.

Nothing in this package computes a line, a price or a probability. It reads the registers that
other packs already published, puts them on one canonical schema, finds where they contradict each
other, and records the official reads that close (or widen) the open questions. Every module is
pure standard library and free of network access so the build is reproducible in CI.
"""
