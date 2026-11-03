# Signal research and candidate specifications

**Status:** hypotheses only. No candidate has demonstrated a market-relative edge. No current NBA line, player projection, correlation estimate or ROI is published from an authorized ledger.

The research question is not “which team will win?” but “does a frozen, pre-event probability distribution beat the same-selection market price after costs, under dependence-aware out-of-sample validation?” The [NBA Stats FAQ](https://www.nba.com/stats/help/faq) supports per-possession normalization and Four Factors vocabulary; it does not verify a betting edge. The [NBA glossary](https://www.nba.com/stats/help/glossary) defines the features. The [injury-report policy](https://official.nba.com/nba-injury-report-2026-27-season/) shows why availability must be timestamped rather than treated as static.

## Frozen candidate family

| ID | Market | Signal hypothesis | Required pre-event inputs | Main failure mode | Official reference |
|---|---|---|---|---|---|
| L1 | Single moneyline | Prior-game offensive/defensive efficiency, pace, venue, rest and availability improve a margin distribution relative to the market. | Licensed prior-game efficiency/pace snapshots; venue; rest; timestamped availability; same-side market price. | Market already prices the information; lineup news and rating drift. | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| L2 | Single spread | Own expected home margin plus a training residual distribution identifies a handicap mispricing only when cover probability clears edge/EV gates. | Prior margins/efficiency; offered handicap and both-side prices; explicit push settlement. | Garbage time, key absences, push rules and line movement. | [DraftKings spread rules](https://sportsbook.draftkings.com/help/how-to-bet-spread) |
| L3 | Single total | Projected possessions multiplied by matchup efficiencies produces a total distribution, not merely a point estimate. | Prior pace and offensive/defensive efficiency; rest; availability; offered total and both-side prices. | Overtime, fouling, rotation changes and pace endogeneity. | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| P1 | Player points prop | Minutes projected from participation history times a scoring rate shrunk toward a training-only league rate. | Prior minutes/points including authorized zero-minute DNP rows; availability; provider settlement; offered line and price. | Minutes volatility, usage changes, blowouts and restricted prop types. | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| C1 | Same-game prop combo | Direct training-only joint hit frequency for two player-point overs captures shared pace/minutes exposure better than multiplying marginals. | Paired residual hits; shared pace/total exposure; availability; executable same-game combo price. | Sparse joint tails, roster changes and sportsbook correlation adjustments. | [SciPy Pearson reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| X1 | Two-game parlay | Two single-game win probabilities plus explicit cross-game joint evidence and a real executable parlay price. | Timestamped single-game probabilities; binary joint win sample; shared news exposure; provider parlay rules and quote. | Common news shocks, shared players and compounding calibration error. | [DraftKings parlay calculator](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator) |

## Feature discipline

1. **Normalize for opportunity.** Pace and per-100-possession ratings separate scoring volume from efficiency. The FAQ's historical examples are not current measurements. [NBA Stats FAQ](https://www.nba.com/stats/help/faq)
2. **Use the official Four Factors vocabulary.** eFG%, turnover ratio, offensive rebounding percentage and free-throw attempt rate are candidate features, not automatically profitable signals. [NBA Stats FAQ](https://www.nba.com/stats/help/faq)
3. **Timestamp availability.** Injury reports update throughout the day; a feature snapshot must precede the decision. [NBA injury policy](https://official.nba.com/nba-injury-report-2026-27-season/)
4. **Price the same selection.** Compare model probability with the same-side, same-line de-vigged market probability, then test the executable price after vig. [DraftKings odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB)
5. **Model dependence explicitly.** Correlation is association, not causation; a parlay payout formula is not a joint-probability model. [SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) · [DraftKings](https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator)

## What would count as a useful signal

A useful signal must survive the full protocol in [VALIDATION_v2.md](VALIDATION_v2.md): rights, provenance, chronology, sample/precision, market-relative proper scores, post-vig ROI, comparable CLV, multiplicity, joint dependence and an audited frozen ledger. A high win rate, a large historical correlation, or a profitable-looking backtest alone is insufficient.

The family is frozen at six candidates for multiplicity. Adding a signal after inspecting holdout results requires a new preregistered version and a new untouched holdout. No adaptive search is hidden from the family denominator.

## Current output

The authorized ledger is empty. Therefore the dashboard shows blank current lines, blank correlations, blank performance metrics and an empty leaderboard. That is an evidence state, not a prediction.
