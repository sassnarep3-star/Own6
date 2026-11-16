# Repo Review — pack nfl_8362b702 (session 8362b702)

Reviewed before writing code, per requirement "review the repository line by
line … explain what you see and its weaknesses":

- `git log`/tree at `32a1b69` (main after PR #91): 843 files; six merged sibling
  packs (nfl-3b81013c accuracy, nfl-309921cc depth, nfl-d966f630 prices/
  correlations/staking/demotion, nfl-a411fed0 availability/injury deltas,
  nfl-f4 freshness provenance, nfl-wk verification + merge gate).
- `tools/run_tests.py` at base: 139/139 green; `tools/check_site.py` 13 pages
  error-free; release_gate OFFICIAL_HOSTS at `tools/release_gate.py:21`;
  source_coverage PUBLISHERS at `scripts/source_coverage.py:25`.
- Requirement coverage grep across the repo (`removal of luck`, `availability
  graph`, `control baseline`, `favorites only`, `reserve list`, `ablation`,
  `backtest corpus`, `proper-score`, `drift alarm`, …): the eight-item cluster
  listed in the executive summary is unowned — this pack claims it.
- Weaknesses found in the repo state (not in others' scope to fix here):
  1. shared inventories (`data/assurance/inventory.csv` family) hash every
     tracked text file, so *any* edit requires regenerating 2-3 tool passes;
     stale hashes are silent until a checker runs.
  2. nine PRs sit open/unreviewed; PR #94 is a stale bookkeeping branch.
  3. `tools/release_gate.py` OFFICIAL_HOSTS is an NBA host list — an NFL pack's
     official links would be *falsely rejected* by it (flagged, left to the
     gate's owner).
  4. multiple packs parse `docs/index.html` and `docs/verified/index.html` as a
     plain-text marker file during build — concurrent edits corrupt builds;
     only the integration session may touch those files.

This pack adds zero network calls to any build: capture is data in
`src/nfl_8362b702/capture.py`; build/check/tests are offline and deterministic.
