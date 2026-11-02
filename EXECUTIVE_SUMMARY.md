# Executive summary — NBA line-origination research (Own6)

**Date:** 2026-11-02 · **Session:** `325834c9` · **Branch:** `arena/325834c9-own6`
**Scope:** verified data collection → model → strategy validation gates → correlation structure →
leaderboard → published site. Research/paper only; no real wagers.

## What was built

1. **Line-by-line verified datasets** (every row carries an official-source link):
   - 2026-27 standings (30 teams) — [data/standings_2026-27.csv](data/standings_2026-27.csv)
   - Team advanced ratings (NBA.com) — [data/team_ratings_2026-27.csv](data/team_ratings_2026-27.csv)
   - All **92 game results** Oct 20–Nov 1 — [data/games_results_2026-27.csv](data/games_results_2026-27.csv)
   - DraftKings market lines for tonight's **15 games** (spread/total/ML, open + current) —
     [data/market_lines_2026-11-02.csv](data/market_lines_2026-11-02.csv)
   - Verified player-prop lines (7 athletes, identity-checked against ESPN athlete endpoints) —
     [data/player_props_2026-11-02.csv](data/player_props_2026-11-02.csv)
   - Automated cross-check: **213/213 verification checks pass** (recomputed W-L from official
     game cards matches official standings exactly) — [verification/verification_report.csv](verification/verification_report.csv)
2. **Line origination model v0.1** (`scripts/model.py`): walk-forward, shrinkage (k=8),
   expanding HCA/σ — generates Own6 spread/total/win-probability for all 15 games and compares
   them to DraftKings ([data/our_lines_2026-11-02.csv](data/our_lines_2026-11-02.csv)).
3. **Validation gates with honest outcomes** ([research/validation.md](research/validation.md)):
   - Walk-forward backtest, 82 graded games: log-loss **0.6747** vs 0.6932 (coin) vs 0.7059
     (home baseline); straight-up accuracy **59.8%**; margin correlation r=0.210.
   - **Gate G1 (calibration) NOT met**: 95% bootstrap CI on log-loss improvement
     [−0.013, +0.073] crosses zero → no validated edge is claimed; S-1 stays `TRACKING`.
   - Luck-removal protocol: pre-registration, walk-forward, shrinkage, baseline comparisons,
     multiple-testing log (Bailey & López de Prado 2014 DSR framing).
4. **Correlation values determined** ([research/correlation.md](research/correlation.md)):
   same-game team scores r=**+0.200** (n=92); cross-game parlay legs r=**+0.105** (n=357);
   rest signal r=**−0.016** (n=76, null); teammate prop pair r=**−0.422** (n=6, flagged).
5. **Strategy leaderboard with paper rewards** ([research/strategies.md](research/strategies.md)):
   7 pre-registered strategies; rank by gates passed; rewards 20/10/5 paper units monthly;
   current best: S-1 (score 4, TRACKING); S-2/S-3/S-5 NOT DEPLOYED with reasons stated.
6. **Flagged-for-review register** ([data/flagged_items.csv](data/flagged_items.csv), site page):
   7 items including an NBA.com recap-slug/score mismatch (IND-BKN 10/25), unresolved prop
   athlete IDs (withheld from publication), unavailable historical closing lines (G5 blocked),
   prop side-label ambiguity, and the failed G1 gate itself. All non-blocking.

## Headline findings (2026-11-02)

- **Slate:** 15 games; DraftKings anchors: SA −16.5 vs UTA (biggest), NY −14.5 vs BKN,
  MIN −10.5 vs MIL, PHI −10.5 vs CHI (highest total 239.5), BOS@HOU lowest total 216.5.
- **Model vs market:** favourites agree 13/15; model disagrees on WSH@ORL and POR@DEN
  (takes the dog +2.3 in both); model totals deviate ≥6 pts on 5 games — recorded as leans only.
- **Market movement (open→current):** ATL −7.5→−10.5, DET −4.5→−6.5, LAL −1.5→−2.5,
  under-money on PHI/CHI total; S-7 tracks these against tonight's results.
- **Props (verified):** SGA 30.5 (open 29.5), Mitchell 22.5 (open 23.5; Oct avg 22.7),
  Harden 17.5 (open 18.5), Allen 12.5, Hartenstein 10.5, Merrill 9.5, Kenrich 7.5.
- **Season context:** only ~4–7 games/team → every rating is shrinkage-dominated; home win rate
  52.2% and HCA 1.64 pts run below long-run norms (small-sample, flagged).

## Honest limits (do not skip)

- No strategy is `VALIDATED`; G1 failed and G5 (CLV) is blocked by source availability.
- Historical closing odds for the 92 finished games are not obtainable from the official
  sources used → ATS/CLV backtest deferred; tracking starts with this slate (flagged).
- Prop identity gaps (6 athlete IDs) are published as flags, never as filled rows.
- Early-season σ=16.48 inflates uncertainty; all probabilities are conservative.

## Artifacts

- Site: [docs/index.html](docs/index.html) (dashboard + data/lines/strategies/validation/correlation/flagged pages)
- Verification: [verification/verification_report.csv](verification/verification_report.csv) ·
  [verification/backtest_metrics.csv](verification/backtest_metrics.csv)
- Coordination: [COORDINATION.md](COORDINATION.md)
