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
| T2 | Official NBA data collection (standings, team games, ratings) | done | `325834c9` | data/*.csv, scripts/verify_data.py | 92 results, 30-team standings + advanced ratings, all rows sourced |
| T3 | Strategy research (single bets, parlays, player props) | done | `325834c9` | research/strategies.md | 7 pre-registered strategies + paper leaderboard/rewards |
| T4 | Validation gates & de-luck methodology | done | `325834c9` | research/validation.md | G1–G6 defined; G1 FAIL reported honestly; DSR/CLV/rest citations |
| T5 | Correlation analysis (parlay/prop legs) | done | `325834c9` | research/correlation.md, data/correlation_findings.csv | r=0.200 / 0.105 / −0.422 / −0.016 measured from official data |
| T6 | Own-line model + market comparison | done | `325834c9` | scripts/model.py, data/our_lines_*.csv, data/market_lines_*.csv | 15 DK lines (open+current) vs model; walk-forward backtest |
| T7 | Executive summary | done | `325834c9` | EXECUTIVE_SUMMARY.md | |
| T8 | GitHub Pages site (landing + subpages + tables) | done | `325834c9` | docs/**, scripts/build_site.py | 7 pages, 238 data rows (all sourced) |
| T9 | Link/verification checker | done | `325834c9` | scripts/linkcheck.py, verification/ | 320 links PASS; 213/213 data checks PASS |
| T10 | Final integration, PR, merge, Pages deploy | in progress | `325834c9` | integration log below | Final session task |

Status values: `unclaimed` | `in progress` | `done` | `needs review` (needs review = published on Flagged for Review page; does not block).

## Integration verification (pre-merge, 2026-11-02)

| Check | Command | Result |
| --- | --- | --- |
| Data line-by-line verification | `python3 scripts/verify_data.py` | **PASS — 213/213** (recomputed W-L from official game cards == official standings; all rows sourced) |
| Model idempotent rerun | `python3 scripts/model.py` | PASS — backtest n=82, log-loss 0.6747 vs 0.6932/0.7059 baselines, G1 FAIL (CI crosses 0) reported |
| Site build | `python3 scripts/build_site.py` | PASS — 7 pages generated |
| Link + row-sourcing check | `python3 scripts/linkcheck.py` | **PASS — 320 links** (internal resolve, external allowlisted), **238/238 data rows have source links** |
| Flagged items | `data/flagged_items.csv` → docs/flagged.html | 7 items, all `needs review`, non-blocking |

## Change requests (cross-scope)

None yet.

## Log

- **2026-11-02 (session `325834c9`)** — Repo reviewed: initial commit `c5d6e4c`, README only. Created coordination board. Environment provides single session; claiming all tasks under `325834c9` with per-task file scopes above.
- **2026-11-02 (session `325834c9`)** — T2–T9 completed and pushed on `arena/325834c9-own6` (data → model → research → site → linkcheck). Sources: NBA.com (standings, advanced stats, game cards), ESPN schedule/odds core feed (DraftKings — NBA co-official sports betting partner per pr.nba.com), ESPN player gamelogs/rosters/athletes. Irregularities: 7 flagged (see T9) — non-blocking per rules.
- **2026-11-02 (session `325834c9`)** — PR → main: see "Merge record" below (appended after PR creation).

## Merge record (appended by T10)

- PR: pending
- Merge: pending
- GitHub Pages: pending

## Verification rules (binding for every task)

1. Every table row must carry a source link to an official/trusted site (nba.com, stats.nba.com, official league/rulebook pages; recognized primary sources for market data).
2. If a value cannot be confirmed from an official source → leave blank, mark `UNVERIFIED`, and list it on the site's **Flagged for Review** page. Never infer or fill in values.
3. Mark task `done` only after recording sources + verification performed here.
