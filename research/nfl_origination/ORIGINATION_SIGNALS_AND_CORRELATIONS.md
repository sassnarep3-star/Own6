# NFL Line Origination, Signal Competition, Correlation Copulas & Luck-Removal Specification

**Implementation Modules:** `src/nfl_origination/{pricing,lines,correlations,gates,leaderboard}.py`  
**Verified Datasets:** `data/nfl_origination/{strategies_leaderboard,validation_gates,correlations_and_combos}.csv`

---

## 1. Discrete NFL Fair-Line Origination (`lines.py` & `pricing.py`)

Unlike basketball (where 200+ combined possessions allow a continuous normal margin approximation), NFL scoring occurs in discrete chunks (`TD+XP = 7`, `TD+2pt = 8`, `TD+missed = 6`, `FG = 3`, `Safety = 2`) across ~11 drives per team, producing sharp probability spikes at **key numbers `3` (~8–9%), `7` (~6–7%), `6`, `10`, and `14`**, plus non-zero regular-season **overtime ties** (already observed in 2026: `WAS 2-5-1`, `NYG 5-2-1`).

1. **Regime-Consistent Expected Points (`NFLRegimeParams`):**
   - Models team expected points from post-2025-regime offensive/defensive points-per-drive, domestic home-field advantage (`HFA = 0` automatically when `neutral_site=True`, as in Week 10 Munich `NE vs DET`), and calibrated starter-to-backup depth adjustments.
   - Fails closed (`status="unverified_missing_inputs"`, returning `None` for all lines) whenever `NFLRegimeParams` or team efficiency inputs are unverified.
2. **Discrete Integer-Margin PMF (`_discrete_margin_pmf`):**
   - Evaluates integer margins $m \in [-75, +75]$ combining Gaussian bin mass, post-2025 regular-season 10-minute both-possess overtime tie mass $P(M = 0) > 0$, and key-number multipliers $w_{|m|}$, normalized so $\sum_{m} P(M = m) = 1$.
3. **Push-Exact Expected Value & De-Vigging (`pricing.py`):**
   - Supports both **multiplicative** and **power-method** ($\sum_i p_i^k = 1$) vig removal.
   - Computes exact push-aware expected value per unit risked:
     $$\text{EV} = P(\text{win}) \cdot (d - 1) - P(\text{loss}) \cdot 1 + P(\text{push}) \cdot 0, \quad P(\text{win}) + P(\text{loss}) + P(\text{push}) = 1.$$
   - Enforces **same-line de-vigged CLV** (`same_line_clv`), returning `None` if a spread moved across an NFL half-point (e.g., `-2.5` to `-3.5`) so key-number line movement is never conflated with same-number price improvement.

---

## 2. Ten Preregistered NFL Signal Strategies (`NFL-STR-01`..`NFL-STR-10`)

- **Single Bets (`NFL-STR-01`..`NFL-STR-04`):**
  1. `NFL-STR-01` (*Spread*): Trench OL-Cluster (`>=2` OL or `1st+2nd` string at same slot impaired + `<8` active OL 47-man penalty) vs. Top-Decile Pass-Rush Mismatch.
  2. `NFL-STR-02` (*Spread / 3-Way ML*): Quarterback Replacement Tier (`QB1->QB2->QB3` + Emergency 3rd QB constraint) & Mid-Season Trade-Lag Re-Origination.
  3. `NFL-STR-03` (*Total*): Post-2025 Dynamic Kickoff (`35-yd` touchback) & Outdoor Cross-Wind (`>= 15 mph`) Total Origination.
  4. `NFL-STR-04` (*Player Prop*): Weak-Link `2nd/3rd/4th`-String Defensive Back Target-Funnel WR Receiving Prop.
- **Multi-Game Parlays (`NFL-STR-05`..`NFL-STR-06`):**
  5. `NFL-STR-05` (*2–3 Leg Cross-Game Spread Parlay*): Uncorrelated Key-Number Crossing Parlay across disjoint venues/windows verified to have zero shared slate residual shock.
  6. `NFL-STR-06` (*2-Leg Outdoor Under Parlay*): Regional Synoptic Severe-Weather Under Parlay priced explicitly with positive cross-game weather copula dependence.
- **Same-Game Parlays & Player-Prop Combos (`NFL-STR-07`..`NFL-STR-10`):**
  7. `NFL-STR-07` (*SGP Stack*): QB Passing Yards Over + Primary WR1 Receiving Yards Over (audited against sportsbook SGP correlation tax).
  8. `NFL-STR-08` (*SGP Script Stack*): Favorite Spread Cover + RB1 (or elevated RB3) Rushing Attempts Over.
  9. `NFL-STR-09` (*Inverse Trench Combo*): Depleted-OL QB Passing Yards Under + Opposing Defense Sacks Over.
  10. `NFL-STR-10` (*Target Redistribution Combo*): WR1-Out / Backup-QB Short-Area RB/TE Reception Funnel.

---

## 3. Correlation & Copula Pricing Architecture (`correlations.py`)

Naive leg independence $P(A \cap B) = P(A)P(B)$ fails in both directions on NFL parlays and prop combos:
- **Positive residual correlation** (`CORR-01`, `CORR-03`, `CORR-07`, `CORR-10`): e.g., at $p_1 = p_2 = 0.50$ and latent residual $\rho = +0.50$, Sheppard's identity gives $P(Z_1 \le 0, Z_2 \le 0) = \frac{1}{4} + \frac{\arcsin(0.5)}{2\pi} = \frac{1}{3} \approx 33.33\%$ (`+200` fair) vs. $25.00\%$ (`+300` independent). However, retail sportsbooks frequently quote popular QB+WR SGPs at `+165` to `+180`—imposing a steep **SGP correlation tax** that turns a positively correlated stack into a negative-EV bet!
- **Negative residual correlation** (`CORR-04`, `CORR-06`): e.g., Favorite `-6.5` blowout cover + own-QB pass attempts Over ($\rho < 0$); at $\rho = -0.50$, joint hit drops from $25.00\%$ to $16.67\%$ (`+500` fair), so assuming independence overstates fair EV by `33%`.

Our engine enforces:
1. **Zero-Preserving Paired Pregame Residuals:** Computes `paired_pearson` and tie-aware `paired_spearman` on residuals $e_{i,g} = y_{i,g} - \hat{\mu}_{i,g}$ (retaining exact `0.0` residuals).
2. **Week-Clustered Block Bootstrap (`week_block_bootstrap_corr_ci`):** Resamples whole NFL weeks (`G >= 4`) to preserve synoptic weather and slate-wide shocks.
3. **Exact 2-Leg Quadrature & $k$-Leg Cholesky Gaussian Copula:** Uses deterministic 120-panel Simpson quadrature for $k=2$ (`~1e-9` accuracy, zero Monte Carlo noise) and strict Cholesky PD validation (`pivot > 1e-12`) + 95% Wilson bounds for $k \ge 3$.
4. **Strict Blank Policy (`NFL-F08`):** Because no licensed paired NFL residual dataset is present in this repo, all 12 empirical correlation cells in `correlations_and_combos.csv` are left blank (`""`) and `correlation_pricing_report(..., None)` returns `status="blocked_unverified_correlation"`.

---

## 4. Controlling Outcome Luck & Leaderboard Qualification (`gates.py`, `leaderboard.py`)

Single-game football luck (fumble bounces, tipped passes, upright-doinked kicks) cannot be erased from a single score, so we **eliminate luck from strategy qualification** via four orthogonal filters inside `NFL-G01`..`NFL-G12`:

1. **Sample & Slate Breadth (`NFL-G04`):** Requires $N \ge 250$ settled single bets or $N \ge 400$ combos across $\ge 18$ distinct NFL weeks.
2. **De-Vigged Same-Line CLV (`NFL-G07`):** Requires week-clustered $t \ge 2.50$ on closing line value—proving the strategy consistently beats the sharpest market price at kickoff (3x–4x lower variance than binary win/loss noise).
3. **Strictly Proper Scoring Dominance (`NFL-G06`):** Requires both out-of-sample `Brier(model) < Brier(market)` and `LogLoss(model) < LogLoss(market)`, blocking uncalibrated longshot parlay gamblers.
4. **Week-Block Bootstrap LCB & Holm-Bonferroni FWER (`NFL-G08`, `NFL-G09`):** Requires 95% week-clustered ROI lower confidence bound $> 0$ AND family-wise adjusted $p < 0.05$ across all $M = 10$ registered strategies.

Only `12/12` gate-passing strategies receive a rank and non-monetary research compute tier via:
$$\text{SkillScore} = 100 \cdot \text{ROI}_{\text{LCB95,week}} + 50 \cdot \overline{\text{CLV}}_{\text{same-line}} + 25 \cdot (\text{Brier}_{\text{market}} - \text{Brier}_{\text{model}}).$$
