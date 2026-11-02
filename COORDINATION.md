# COORDINATION.md — Shared Task Board

**Repository:** `sassnarep3-star/Own6`
**Purpose:** NBA line-origination research project — collect, organize, analyze; build strategies with validation gates; publish a GitHub Pages dashboard.

## Session registry

| Session ID | Branch | Status | Scope (file paths) |
| --- | --- | --- | --- |
| `325834c9` | `arena/325834c9-own6` | active | All tasks (see below) — sole session in this run |

> **Branch note:** The Arena environment pins this session to branch `arena/325834c9-own6`; all work for this session happens there (environment requirement). Scope separation by file path below still applies so any parallel session can claim non-overlapping files.

## Task board

| Task ID | Task | Status | Owner | Files | Notes |
| --- | --- | --- | --- | --- | --- |
| T1 | Coordination board setup | done | `325834c9` | COORDINATION.md | This file |
| T2 | Official NBA data collection (standings, team games, ratings) | in progress | `325834c9` | data/*.csv, scripts/fetch_*.py | Source: nba.com / stats.nba.com |
| T3 | Strategy research (single bets, parlays, player props) | unclaimed | — | research/strategies.md | |
| T4 | Validation gates & de-luck methodology | unclaimed | — | research/validation.md | |
| T5 | Correlation analysis (parlay/prop legs) | unclaimed | — | research/correlation.md, data/correlation_*.csv | |
| T6 | Own-line model + market comparison | unclaimed | — | scripts/model.py, data/our_lines_*.csv | |
| T7 | Executive summary | unclaimed | — | EXECUTIVE_SUMMARY.md | |
| T8 | GitHub Pages site (landing + subpages + tables) | unclaimed | — | docs/** | |
| T9 | Link/verification checker | unclaimed | — | scripts/linkcheck.py, verification/ | |
| T10 | Final integration, PR, merge, Pages deploy | unclaimed | — | integration log below | Final session task |

Status values: `unclaimed` | `in progress` | `done` | `needs review` (needs review = published on Flagged for Review page; does not block).

## Change requests (cross-scope)

None yet.

## Log

- **2026-11-02 (session `325834c9`)** — Repo reviewed: initial commit `c5d6e4c`, README only. Created coordination board. Environment provides single session; claiming all tasks under `325834c9` with per-task file scopes above.

## Verification rules (binding for every task)

1. Every table row must carry a source link to an official/trusted site (nba.com, stats.nba.com, official league/rulebook pages; recognized primary sources for market data).
2. If a value cannot be confirmed from an official source → leave blank, mark `UNVERIFIED`, and list it on the site's **Flagged for Review** page. Never infer or fill in values.
3. Mark task `done` only after recording sources + verification performed here.
