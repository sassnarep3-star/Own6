# COORDINATION — Own6 NBA Lines Project

| Task | Status | Owner | Files in scope | Verification / notes |
|---|---|---|---|---|
| NBA strategy research, executive summary and dashboard evidence pass | done | arena/d100a9d1-own6 | README.md; root static research prototype; workflow; coordination | Official metric sources: https://www.nba.com/stats/help/glossary and https://www.nba.com/news/inside-the-game-stat-glossary. Definitions only; no betting edge, odds, correlations, or performance verified. |
| Integrated NBA engine, docs site, validation and source registry | done (merged PR #1) | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, data/, docs/, src/, tests/ | Main already contained the other session's merged integration when this branch was rebased/merged. Preserved its files. |
| Final Pages link validation and PR | in progress | arena/d100a9d1-own6 | .github/workflows/pages.yml, COORDINATION.md | Adding local-link check to existing docs deployment without replacing the published docs site. |

## Log
- 2026-11-02: This branch began with only README.md; task claim was committed and pushed. Before PR merge, origin/main advanced with PR #1 from another session. Detected merge conflict, stopped, and merged origin/main while preserving its docs, code and source registry. PR #3 initially reported conflicting; integrating main is in progress.
- Official NBA references establish definitions only. Models and thresholds are proposals; odds, correlations, returns and leaderboard values remain unverified/blank. No profitability claim.
