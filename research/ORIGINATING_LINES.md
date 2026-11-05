# Originating Your Own NBA Lines — Strategy & Validation Pack (2026-11-05)

Research only. No betting advice, no picks, no profitability claim. **No strategy below is validated.** Every empirical value (correlation, n, ROI, CLV, edge) is blank/unverified until an authorized, timestamped, out-of-sample ledger exists.

## How to originate a line (method, not a result)
1. **Efficiency core:** expected points from pace × offensive/defensive efficiency per the official definitions in the [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) (PACE, OffRtg, DefRtg, NetRtg = OFFRTG − DEFRTG). Fit home advantage and margin SD from a licensed game log — never hard-code.
2. **Fair price:** convert expected margin/total to win probabilities; convert to fair American odds with **no invented margin** (repo hardened pricing). De-vig any market comparison on the *same line*; moved lines stay blank.
3. **Player props:** projected minutes × shrunk per-minute rate; minutes only from timestamped official status ([NBA injury report](https://official.nba.com/nba-injury-report-2026-27-season/)).
4. **Combos/parlays:** joint probability from training-only paired residuals via Gaussian copula; independence is a labelled special case, never a default ([SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html): Pearson measures linear relationship, −1…+1).

Catalogue: `data/origin_strategies.csv` (O1–O10: 3 single-bet, 3 prop/prop-combo, 2 parlay, 1 CLV meta, 1 minutes) — each row source-linked, all values blank.

## Validation gates (all must pass; frozen before testing)
Rights & provenance (authorized feed; [NBA Terms §9](https://www.nba.com/termsofuse) bars gambling use of NBA Statistics; [Stats FAQ](https://www.nba.com/stats/help/faq): stats "not available for download") → chronology (walk-forward, train/validation/holdout; [scikit-learn CV](https://scikit-learn.org/stable/modules/cross_validation.html) warns testing on training data is overfitting) → sample (n≥200, ≥60 slates, frozen in `data/empirical/report.json` config) → calibration ([Brier/log-loss](https://scikit-learn.org/stable/modules/calibration.html)) → CLV (de-vigged same-line close) → multiplicity (Bonferroni over the *whole* frozen family; [statsmodels multipletests](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html)) → clustered uncertainty (slate-clustered bootstrap ROI lower bound > 0; [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)) → correlation/joint-sample gate → immutable pre-game ledger with hashes.

## Removing luck (reducing, never eliminating)
Pre-register thresholds; rank only all-gate qualifiers by the **lower bound** of clustered holdout ROI; exact binomial win-count is diagnostic only; report CIs beside every estimate; a passing strategy can still lose. Leaderboard is therefore **empty**.

## Correlations
Determine ρ only from authorized training residuals, retain zeros, slate-cluster CIs, require actual joint samples for combos. Current values: **blank** for O1–O10 pairs (see `docs/origin/correlations.html`).
