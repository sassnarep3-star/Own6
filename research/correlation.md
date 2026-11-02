# Correlation findings (2026-27 official data)

Session `325834c9` · every number below is computed from official-source rows in
[data/](../data/) — reproduction: [data/correlation_findings.csv](../data/correlation_findings.csv)
plus [scripts/model.py](../scripts/model.py) backtest output. Pearson r unless noted.

| Pair | n | r | Interpretation | Source rows |
|---|---|---|---|---|
| Home score vs away score (same game) | 92 | **+0.200** | Pace couples team totals: both sides' scoring rises together. Same-game "both over" legs are positively dependent — joint P(both over) > product of marginals. | [games_results_2026-27.csv](../data/games_results_2026-27.csv) |
| Cross-game margins, pooled same-date pairs | 357 | **+0.105** | Parlay legs from different games are *mostly* independent but not exactly: weak positive same-date dependence (schedule/rest clustering). Cross-game parlays must not assume strict independence. | [games_results_2026-27.csv](../data/games_results_2026-27.csv) |
| Rest differential (away−home) vs home margin | 76 | **−0.016** | Essentially zero in this sample — rest edge not detectable yet (literature expects a small effect; see [validation.md](validation.md)). | [games_results_2026-27.csv](../data/games_results_2026-27.csv) |
| Teammate points, Mitchell (CLE) vs Allen (CLE), 2026-27 | 6 | **−0.422** | Usage-sharing direction (one's big night tends to come with the other's quiet one), but n=6 → **insufficient sample**, flagged; joint prop combos stay NOT DEPLOYED. | ESPN gamelogs ([Mitchell](https://www.espn.com/nba/player/gamelog/_/id/3908809), [Allen](https://www.espn.com/nba/player/gamelog/_/id/4066328)) |
| Model predicted margin vs actual margin (walk-forward) | 82 | **+0.210** | Positive but modest predictive correlation; early season + heavy shrinkage. | [backtest_walkforward.csv](../data/backtest_walkforward.csv) |

## Derived facts (not correlations, but used by strategies)

- 2026-27 scoring margin σ = **16.48 pts** (n=92); season mean total = **227.4**;
  home-win rate = **52.2%** (48-44); empirical HCA after expanding update = **1.64 pts**.
- B2B/1-day-rest team-games: 66-65 (50.4%) vs 2+ days: 12-11 (52.2%) — no significant gap.
- Rest-differential signal: none detected (r=−0.016) → S-3 not deployed.

## What this means for parlays / combos (strategy linkage)

1. **Same-game combos**: legs share pace (+0.20) and may share usage (teammate −0.42 in n=6).
   Any combo price must be built from a joint distribution; independence is wrong in both directions.
2. **Cross-game parlays**: measured dependence is small (+0.105) but non-zero; treating legs as
   independent slightly overstates joint win probability for favorite-side legs → conservative
   pricing requires the measured r, not the textbook 0.
3. **Sample honesty**: the teammate number that drives combo pricing is n=6 — the combo strategy
   (S-5) stays NOT DEPLOYED until n≥60 (gate G6), even though the point estimate is large.

## Sources
- Official NBA game results (all rows carry per-game nba.com URLs): [data/games_results_2026-27.csv](../data/games_results_2026-27.csv)
- ESPN official player game logs: https://www.espn.com/nba/player/gamelog/_/id/3908809 · https://www.espn.com/nba/player/gamelog/_/id/4066328
- Walk-forward model output: [verification/backtest_metrics.csv](../verification/backtest_metrics.csv)
