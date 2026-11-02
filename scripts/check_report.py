#!/usr/bin/env python3
"""Verify the fail-closed default is preserved in the report."""
import json
import sys

r = json.load(open("data/empirical/report.json", encoding="utf-8"))
assert r["status"] == "not_run", "empty ledger must report not_run"
assert r["n_observations"] == 0, "empty ledger must have zero observations"
assert r["n_qualified"] == 0, "empty ledger must have zero qualified strategies"
assert r["leaderboard"] == [], "empty ledger must have empty leaderboard"
print("OK: fail-closed default preserved")
