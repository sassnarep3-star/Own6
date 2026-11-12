# NFL Line Research — Executive Summary

**Review date:** 12 November 2026  
**Scope:** NFL game lines, single bets, player props, same-game and cross-game parlays, injury/lineup adjustments, strategy validation, a gated leaderboard and reward governance.  
**Status:** Research framework only. No NFL betting recommendations or empirical model results are published.

## Executive decision

**Do not start automated NFL data ingestion, publish originated prices, claim an edge, calculate NFL correlations, rank a winning strategy, or distribute material rewards yet.** The first blocker is data permission: the directly reviewed [NFL.com Terms and Conditions §1.3](https://www.nfl.com/legal/terms/) state that the Services may be used solely for individual non-commercial informational purposes and prohibit systematic retrieval to compile a collection or database absent express prior written consent. The terms do not resolve every possible contract or legal issue; written data-use permissions and counsel review are required before any production pipeline.

The repository contains no configured, authorized NFL stats feed, historical injury/depth snapshots, market-odds archive, NFL game ledger or NFL backtest. Accordingly, all NFL line, injury-impact, replacement-depth, correlation, edge, ROI, closing-line value and leaderboard performance values remain **blank/unverified**. The NFL dashboard is a requirements and decision-support section, not a live feed or recommendation service.

## What was directly verified from official sources

- The official [NFL injury report](https://www.nfl.com/injuries/) visibly lists players, positions, injuries, practice status and game status. It is useful as a source to evaluate for an availability log, but these fields do **not** establish a starting role, expected playing time, or replacement impact. Blank report fields must remain blank; they do not mean healthy or active.
- The official [NFL player statistics page](https://www.nfl.com/stats/player-stats/) has player stat categories and a 2026 passing table. It does not establish a predictive edge and its terms still apply.
- The official [NFL schedule](https://www.nfl.com/schedules/) provides schedule/game-center links but no sportsbook odds.
- The official [2026 NFL Rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) is a rules reference, not an odds or performance dataset.
- NFL Football Operations’ [Next Gen Stats description](https://operations.nfl.com/game-operations-logistics/technology/performance-tracking-data-next-gen-stats) describes tracking-based measures, but is not a license to collect or use those data for wagering research. The official [Next Gen Stats glossary](https://nextgenstats.nfl.com/glossary) returned only an image in this review; individual glossary entries were not treated as verified.
- A directly opened [NFL game center](https://www.nfl.com/games/packers-at-patriots-2026-reg-9) visibly links a downloadable gamebook. This one checked game does not prove consistent historical availability or data reuse rights.
- The directly opened official [AGLC Play Alberta page](https://aglc.ca/playalberta) says Play Alberta is Alberta’s only regulated online gambling site and describes a sports betting product. The [current Justice Canada Criminal Code §207](https://laws-lois.justice.gc.ca/eng/acts/C-46/section-207.html) contains provisions on provincial lottery schemes and offences. These are starting points only—not a conclusion on the legality of this research, a leaderboard, or prizes.

All sources and exact review scope are listed in [`data/nfl/sources.csv`](../data/nfl/sources.csv) and the [NFL Sources page](../docs/nfl/sources.html). Verified means that the linked official page was opened and the described content was checked. Link-only and partial reads are labeled separately.

## Research plan: candidate signals, not claimed edges

Candidates cover team moneyline, spread and total singles; quarterback passing props; running-back rushing/carry props; receiver reception/yardage props; same-game prop combinations; cross-game parlays; injury/lineup adjustments; and line movement. Hypotheses are deliberately stated as tests, not assertions that a market is beatable. No candidate has a measured result.

Proposed signal families include opponent-adjusted historical outcomes, quarterback availability, offensive-line continuity, defensive-front/secondary availability, prior participation/role, and lawful tracking-derived features. Every feature needs an immutable information timestamp earlier than the prediction. News, depth order, role, snaps and outcomes must not leak from after the forecast cutoff.

### Injury and backup replacement requirements

Retain raw report values and source timestamps. For both offense and defense, link each unavailable player to a **dated, authorized** starter/role and (where supported) the actual replacement at depth positions 2, 3 or 4. Add prior participation/usage evidence only from a rights-cleared source. Do not treat the published injury report as a depth chart; do not infer a missing starter, a backup’s order, expected snaps, “defensive deficiency,” or an impact magnitude. If a role mapping is missing, the derived feature stays blank and the strategy is blocked. See the complete [injury field schema](../data/nfl/injury_fields.csv) and [Flagged for Review](../docs/nfl/flagged.html).

## Correlation and luck control

No NFL coefficient is published. With authorized matched data, estimate paired out-of-sample residual relationships and direct joint outcome probabilities; report sample sizes and dependence-aware uncertainty. For parlays, model settlement of the joint event instead of multiplying marginal probabilities unless independence has been supported. Resample/cluster at the game or slate level as appropriate. Use a complete preregistered candidate family and correct for selection/multiple testing.

Use chronological walk-forward evaluation, a frozen final holdout, calibrated probability forecasts, price-aware net returns including settlement/costs, and independent replication. Keep all attempted and failed candidates. A favorable short-run record cannot eliminate chance; statistical validation can reduce overfitting and quantify uncertainty, not remove luck. The methodological references—[scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html), [SciPy Pearson correlation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html), [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), and [statsmodels multiple-testing correction](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html)—are general methods, not NFL evidence.

## Leaderboard and rewards

The [leaderboard](../docs/nfl/leaderboard.html) is deliberately empty and all candidates are ineligible. A future board should rank only versioned strategies that clear every rights, provenance, timestamp, preregistration, holdout, multiplicity, calibration, dependence, price/settlement and replication gate. Do not rank on raw hit rate or a selected best run. Publish full qualification status, number of eligible observations, uncertainty, score definition and failed trials.

Recommendation: begin with non-monetary research priority only, if/when a valid leaderboard exists. Keep cash, valuable prizes, credits and wagering rewards disabled pending a jurisdiction-specific written legal review of the contest structure, eligibility, age, entry conditions, skill/chance design, sponsor, official rules, tax, privacy and appeals. Do not assume describing a contest as skill-based determines its legal status.

## Decisions and next actions

1. Obtain written NFL/data-provider permission for each intended data field, systematic access, archive, model training, gambling/research use and publication.
2. Select a licensed historical and real-time odds source with immutable quote timestamps, operator, market, price, limits, settlement rules and retention rights.
3. Identify an authorized all-club source for dated depth charts, lineups, transactions and participation for both offensive and defensive unit roles; if unavailable, leave replacement-tier values unverified.
4. Define covered markets, competition, jurisdictions, point-in-time cutoff and price/settlement convention.
5. Pre-register model candidates, baseline, exclusions, testing periods, minimum evidence methodology and multiple-testing family before outcome inspection.
6. Obtain Alberta and other applicable legal advice before public line display, wagering activity, or material prizes.

The prioritized alternatives are in the [Suggestions for Review page](../docs/nfl/suggestions.html); the unanswered information requirements are in the [Decision Questions page](../docs/nfl/questions.html). No further user-provided data were needed to produce this conservative, source-limited framework. Future live operation is intentionally blocked until external permissions and licensed feeds exist.
