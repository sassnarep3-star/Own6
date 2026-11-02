# Executive Summary — Own6: Originate Your Own NBA Lines

**Date:** 2026-11-02 · **Repo state audited:** greenfield (only `README.md` = "# Own6"). Everything below was built this session. **No NBA statistic, odd, or backtest result is asserted anywhere in this project unless linked to an official source — see `data/sources.csv`. Values that could not be confirmed are blank and listed on the Flagged for Review page, by design.**

## Objective
Build *your own* NBA lines (spread, total, win probability), player-prop projections, and correlated parlay prices; treat strategy development as a leaderboard competition that rewards **skill, not luck**; require every strategy to pass explicit validation gates before it can be ranked or staked.

## The system (code in `src/own6/`, 5 tests passing)
1. **Own lines (`lines.py`)** — Expected points from official NBA definitions only: PACE (possessions/48), OffRtg & DefRtg (pts/100 poss) per the NBA Stats Glossary [S2]. Multiplicative matchup model → fair spread, fair total, win probability. Home-court advantage and margin SD are **fitted from your own game log** (`fit_from_games`), never hard-coded from memory.
2. **Props (`props.py`)** — Projection = projected minutes × shrunk per-minute rate (shrinkage toward season mean). Minutes/rates must come from NBA Stats [S1] and availability from the Official Injury Report [S5].
3. **Parlays & correlation (`parlay.py`)** — Gaussian-copula joint probability with Pearson correlations **estimated from paired residuals (n always reported)**. Independence is shown only as a labelled special case; positively correlated legs (e.g., pace-up game → multiple overs) are systematically mispriced by independence multiplication.
4. **Validation gates (`validation.py`)** — G1 walk-forward only · G2 n≥200 · G3 calibration beats market baseline (Brier/log-loss, methodology [S7]) · G4 positive CLV with t≥2 · G5 binomial luck test, Bonferroni-corrected across *all* strategies tried · G6 bootstrap 95% ROI CI lower bound >0 · G7 correlation honesty · G8 pre-game timestamped ledger, no deletions.
5. **Leaderboard (`leaderboard.py`)** — Score is built on the **lower confidence bound of ROI** + CLV + calibration edge. A 20-bet heater is ineligible, not champion. This is how luck is removed: ranking rewards the worst plausible skill estimate, not the best observed outcome.

## Strategy families researched (hypotheses, NOT proven edges — each must pass G1–G8)
| Family | Signal hypothesis | Main risk |
|---|---|---|
| S-A Spread/total vs own line | Own pace/efficiency line deviates from market by > fitted margin SD threshold | Market already prices efficiency; injuries late |
| S-B Pace-mismatch totals | Pace blend extremes regress less in market total | Minutes/rotation changes |
| S-C Prop shrinkage | Recent-form props overreact; shrunk rate beats market line | Minutes volatility, blowouts |
| S-D Correlated SGP | Positive-correlation combos underpriced vs copula joint prob | Book correlation adjustments, limits |
| S-E CLV-first meta | Only take prices that systematically beat close | Needs large honest ledger |

## Correlation — what must be measured (not assumed)
Game-total↔team-total, player PTS↔team total (usage share), PTS↔AST for primary creators, starter minutes↔blowout margin (negative late), pace↔all counting overs. Every correlation used in pricing must be computed from residual pairs with `n` disclosed (`parlay.pearson`). **No correlation value is published in this repo yet — flagged unverified until computed from an official-data export.**

## Data & legality notes
- NBA Stats states stats are **not available for CSV download** [S3] — plan for manual/exported inputs via the site's own tools; do not scrape in violation of terms.
- Only bet where legal, with licensed books; NBA's co-official partners are DraftKings/FanDuel [S6]. This project is analytics/research, not betting advice. No bet is recommended anywhere in it.

## Status after integration re-verification (2026-11-02)
- **Verified data now on the site:** 15 NBA games for the Mon Nov 2, 2026 slate (every row matched live against https://www.nba.com/schedule, game IDs 0022600158–0022600172); 13 rows of 국민체육진흥법 text (Arts. 2, 24, 26, 30, 47–49, 51, 53–54 quoted verbatim from law.go.kr, penalties exact); 2 official NBA policy rows (Oct 26, 2026 prediction-market release; Jul 9, 2026 partner list — DraftKings/FanDuel domestic, no Korea entry) with 5 press-only rows left unverified; source registry S1–S7 re-fetched live from official hosts (S3 URL corrected — old `cdn.` link was AccessDenied).
- **Still blank by rule:** all odds, closing lines, fitted parameters, correlation values, backtests, win rates, ROI. Leaderboard is empty; strategy registry is empty. Flags F01–F15 on the Flagged for Review pages.
- **Rewards/leaderboard gate:** `data/methodology.json` G1 (Korean legal review) is **open/FAIL** — under 국민체육진흥법 Art. 26, reward leaderboards and public line publication need written Korean counsel review before being exposed to Korean users. The leaderboard ships as scoring design only; no rewards are configured.
- **Checks:** `pytest` = 5 passed; `scripts/check_site.py` = 9 pages, no broken internal links; live root redirects to `docs/` and `docs/verified/` serves (both confirmed by live fetch after the latest Pages build).

## Irregularities flagged
Repo itself: none at start (empty). Content: **odds, fitted parameters, correlations, and backtests remain intentionally blank/unverified**; full list with sources: `docs/flagged.html` (F1–F7) and `docs/verified/flagged.html` (F01–F15, incl. F13 gate-label collision between the two G1–G8 sets, F14 S3 URL fix, F15 transient stale root deploy). They do not block launch per brief.

## Deliverables
GitHub Pages dashboard (`docs/`): Landing · Strategies · Validation Gates · Correlations · Leaderboard · Sources · Flagged for Review — plus the source-checked sub-site (`docs/verified/`): Dashboard · Games · Strategies · Korea law · NBA policy · Methodology · Executive summary · Sources · Flagged. Python engine + tests + synthetic-only demo (`examples/demo_synthetic.py`, clearly labelled, not NBA data). Live: https://sassnarep3-star.github.io/Own6/
