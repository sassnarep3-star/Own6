# Integration audit — session arena/f58e0178-own6 (2026-11-03)

Repeatable checks: `python3 scripts/audit_integration.py` (exit 1 on failure). Full flag list with source links: `data/hub_flags.csv` (published at docs/hub/flagged.html).

| Check | Result | Source |
|---|---|---|
| Committed merge-conflict markers in tracked text files | FAIL at `ba6b7b6` (docs/index.html); fixed | https://sassnarep3-star.github.io/Own6/docs/ (pre-fix) |
| Backtest log-loss, Brier, accuracy recomputed from `data/backtest_walkforward.csv` | match `verification/backtest_metrics.csv`; `research/validation.md` and the own6 page had the wrong Brier; fixed | data/backtest_walkforward.csv |
| Market probability = proportional de-vig of current moneylines | FAIL at `ba6b7b6` (formula bug in `scripts/model.py`); fixed | scripts/model.py |
| Nov 2 results: 15 rows, ids = nba.com schedule, links present | pass | https://www.nba.com/games?date=2026-11-02 |
| 13 historical score rows re-read on nba.com | 13/13 match | https://www.nba.com/games?date=2026-10-20 (also 10-22, 10-25 game page, 10-29, 11-01) |
| W-L of 30 teams recomputed from 107 rows vs official standings | 30/30 match | https://www.nba.com/standings |
| Forward test reproducible (seeded) | pass | scripts/forward_test.py |
| Existing checkers (`tools/*`, `scripts/check_site.py`, `linkcheck.py`, `verify_data.py`, `check_lab.py`, tests) | all pass after changes | — |

Not verified (flagged): 79 score rows at score level; team-ratings snapshot; ESPN/DraftKings odds and props; NBA Terms §§1/9 and Korean-law questions (counsel needed).
