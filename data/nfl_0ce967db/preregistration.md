# Pre-registration — session 0ce967db (frozen before the model was written)

**Registration rule.** This file is committed to git *before* any model code exists and before
any result is computed. The commit hash that first contains this file is the registration ID.
Nothing below may be edited after registration; corrections must be added as a new, dated,
separately hashed amendment section that names what it supersedes.

**Registered:** 2026-11-18 (UTC). **Session:** `0ce967db`. **Branch:** `arena/0ce967db-own6`.

## 1. What is being pre-registered

A family of **seven** candidate forecasters for 2026 NFL regular-season games, plus the
evaluation protocol that will judge them. The family size matters: the multiplicity adjustment
in §6 depends on it, so the count is frozen here at seven and may not grow after results are seen.

| ID | Candidate | Kind | Frozen definition |
|---|---|---|---|
| `S01` | `ML-SEASON` | strategy | Home-win probability from season-to-date scoring margin. Team strength = mean (points for − points against) over the team's prior games this season. Expected home margin = (strength_home − strength_away) + H, with H = 2.5 points fixed. |
| `S02` | `ML-FITHFA` | strategy | Identical to `S01` except H is estimated from the training window as the mean home margin of prior games (no shrinkage). |
| `S03` | `ML-RECENCY` | strategy | Identical to `S01` except team strength is an exponentially weighted mean of per-game (PF − PA) with half-life 2 team-games, and H = 2.5 fixed. |
| `S04` | `TOT-SEASON` | strategy | Expected total = league mean total (training window) + offensive deviation of both clubs, where a club's offensive deviation is its mean points scored minus the league mean, and each club's *defensive* deviation is subtracted. Formula fixed in §3. |
| `S05` | `TOT-RECENCY` | strategy | As `S04` with the half-life-2 weighting of §S03 applied to scored and allowed points. |
| `C01` | `CONTROL-CLIMATOLOGY` | control | The training-window home-win rate for every game. No team information. |
| `C02` | `CONTROL-HOME-ALWAYS` | control | Probability 1.0 for the home team, 0.0 away. Tests whether the model beats "always home". |

Both totals candidates are published side by side with the gap column until a walk-forward
comparison separates them; neither is collapsed to a single estimator by this pack.

## 2. Data the forecaster may see

Only these, all official:

* Final scores of 2026 regular-season games, weeks 1–10, as read from
  `https://www.nfl.com/schedules/2026/by-week/week-<n>` and the Week 10 finals page.
* Nothing else. No market prices (none are published by any official page), no injuries,
  no depth charts, no personnel, no weather, no rest days, no 2025 or earlier results.

**Chronology rule.** For a game in week *w*, the forecaster may use only games whose week is
strictly less than *w*. No same-week information, no result of the game being predicted, no
information that was published after kickoff. The implementation asserts this per row.

**Shrinkage rule (declared in advance).** A club with *n* prior games contributes
`n/(n+k)` × its own mean plus `k/(n+k)` × the league mean, with `k = 1` pseudo-game. This
prevents week-2 blowouts from dominating. `k` is not tuned.

## 3. Fixed formulas

Let `pf_i`, `pa_i` be club *i*'s shrunk mean points scored and allowed over its prior games,
`L` the league mean of total points per game over the training window, and `n_i` its prior game
count. With `p_i = pf_i − pa_i` (strength):

* margin expectation `M = (p_home − p_away) + H`
* `P(home win) = Φ(M / σ_M)`, where `σ_M` is the sample standard deviation of prior games'
  (actual margin − expected margin at the time) over the training window, floored at 7.0 and
  capped at 25.0 points so a thin early window cannot produce a degenerate distribution.
* total expectation `T = L + (pf_home − L/2) + (pf_away − L/2) − (pa_home − L/2) − (pa_away − L/2)`
  where each `pf − L/2` is replaced by its devigged club deviation and each club deviation is
  shrunk by the same `k = 1` rule. If any club has no prior game, `T = L`.
* Ties: the outcome is a home win only if home score > away score. A tie is scored as a loss
  for both probability directions, i.e. `y = 0` for "home win" and also `y = 0` for "away win".
  Ties are kept in the sample, never dropped.

## 4. Scored quantity, and what is *not* scored

* **Primary score: Brier score** of the home-win probability, `BS = mean((p − y)²)`.
* Secondary: log loss, and for totals MAE and RMSE in points.
* **Not scored, and not published as a performance number:** ROI, units won, CLV, win rate of
  picks. No official page publishes a price, so no staking result can exist. A profit number
  here would be invented, and this registration forbids inventing one.

## 5. Sample and evaluation window

* Backtest corpus: every completed 2026 regular-season game in weeks 1–10 for which a final
  score is published on the official schedule page — 150 games (13 in week 10 plus the Monday
  game settled on 2026-11-18).
* Scored only from week 3 onward (two prior weeks needed for a defensible `σ_M`); weeks 1–2 are
  consumed as training data only.
* The corpus is the pre-registered backtest corpus. **These numbers are backtest numbers and may
  never appear on the strategy leaderboard**, which is prospective-only by rule (§7).

## 6. Uncertainty, clustering and multiplicity

* Uncertainty: percentile bootstrap over **week clusters** (resample weeks with replacement,
  take all games in a sampled week), 2,000 resamples, seed 20261118, 95% interval. The
  published lower bound is the 2.5th percentile of the bootstrapped Brier skill score.
* Skill: `BSS = 1 − BS_candidate / BS_control`, control = `C01` climatology.
* Multiplicity: the family is seven candidates; the qualification test is two-sided at
  `α/m` with `m = 7`, i.e. `α = 0.05/7 = 0.007143`. A candidate may be called a finding only if
  its bootstrapped interval excludes zero **and** the Bonferroni-adjusted test passes. Both are
  reported for every candidate, pass or fail.
* No candidate that fails is presented as a signal. A failure is published as a failure.

## 7. Leaderboard admission (backtest numbers are barred)

The strategy leaderboard begins **empty and prospective** at the week-11 kickoff
(2026-11-19T01:15Z). A strategy may enter it only with forecasts that were committed to git
before the kickoff of each game, on games not yet played. Backtest skill — including any
positive Brier skill computed above — is a **qualification input** in the frozen state machine,
never a leaderboard entry. Week-11 forecasts are registered in this same session and are the
first prospective entries; they score after the games finish.

## 8. Demotion gate (live → paper)

A strategy in state `paper` may move to `live-candidate` only when all hold:
prospective sample ≥ 100 scored forecasts; prospective Brier skill lower bound > 0;
Bonferroni-adjusted test passes. A strategy in `live-candidate` **returns to `paper`** when,
over its trailing 50 prospective forecasts, the week-cluster bootstrap lower bound of its Brier
skill falls below 0. Demotion is automatic and published with the number that triggered it.
Since no market price exists, no strategy can ever reach `live`, and the pack says so.

## 9. Ablations instead of penalties

Personnel and availability are **not** given fixed point penalties anywhere. The registered
test is a paired ablation: the same forecaster, same games, with and without a personnel feature
block, compared by the difference in Brier score with a week-cluster bootstrap interval. If the
personnel block cannot be built from official data, the ablation is published as **not run**
with the exact blocking gate — never as an assumed effect size.

## 10. Correlations

Correlations are computed only from official numbers, always with `n` and a confidence interval
published beside the value. No correlation enters a parlay or combo calculation unless a
directly validated *joint* probability exists; multiplying marginal probabilities is barred.

## 11. What this registration refuses

No edits to thresholds after seeing results. No dropping games that behaved badly. No
re-specification of `k`, the half-life, `σ_M` bounds or the family size. No claim of
profitability. No market line, market probability, CLV or ROI value anywhere in this pack.
