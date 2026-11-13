# Validation gates, correlations, and removing luck from the equation

Session `arena/309921cc-own6` · captured 2026-11-13 ·
tables: `validation_gates.csv`, `correlations.csv`, `luck_index.csv` → `docs/nfl-309921cc/validation.html`, `correlations.html`

## 1. The twelve gates

Four are open because they depend only on how the pack is built. Eight are blocked because a
licensed input does not exist in this repository. A blocked gate is not a failure — it is the
reason no performance number is published.

| Gate | Name | Status | What blocks it |
|---|---|---|---|
| G01 | Rights and provenance | open | — |
| G02 | No invented market prices | blocked | Licensed historical price archive |
| G03 | Minimum sample (200 per family) | blocked | Graded selection history |
| G04 | Chronological out-of-sample | blocked | Multi-season results and prices |
| G05 | Pre-registration | open | — |
| G06 | Multiple-testing control (Holm, α = 0.05) | blocked | Test statistics from G03/G04 |
| G07 | Calibration and proper scoring | blocked | Graded probability-outcome pairs |
| G08 | Closing-line value | blocked | Licensed closing prices |
| G09 | Dependence handled, never assumed | blocked | Paired licensed residual history |
| G10 | Luck-separated skill statistic | blocked | Graded selections with slate identifiers |
| G11 | Market-integrity eligibility | open | — |
| G12 | Reproducibility | open | — |

### How each gate actually removes luck

Luck is not removed by being strict. It is removed by refusing to let variance, in-sample optimism,
post-hoc rule-shopping, multiplicity, mispriced dependence and unfalsifiable benchmarks masquerade
as skill. In order:

- **G03** stops a short lucky run from qualifying.
- **G04** removes in-sample optimism — the most common way luck is mistaken for skill.
- **G05** removes post-hoc rule-shopping, which turns noise into apparent signal.
- **G06** recognises that ten strategies tested at 5% produce a false positive far more often than 5% of the time.
- **G07** catches the case where a strategy wins bets and is still badly calibrated.
- **G08** asks the question variance cannot fake: did you beat the close?
- **G09** stops a correlated combo being mispriced in one direction by an independence assumption.
- **G10** requires the interval, not the point estimate, to exclude zero.

## 2. Measured correlations

Every other NFL pack in this repository leaves correlation values blank. These are **measured**: each
is computed here from the 32 verified official standings rows, with n, a two-sided p-value, a Fisher
z interval, and an independent 5,000-draw percentile bootstrap interval. They describe the league,
not a betting market, and they are not betting edges.

| ID | Relationship | Method | n | r | p | 95% CI | Bootstrap CI |
|---|---|---|---|---|---|---|---|
| COR-01 | Points for per game ~ win % | Pearson | 32 | 0.6984 | 8.8e-06 | 0.4622 to 0.8420 | 0.4204 to 0.8716 |
| COR-02 | Points against per game ~ win % | Pearson | 32 | −0.6636 | 3.5e-05 | −0.8221 to −0.4097 | −0.7925 to −0.5187 |
| COR-03 | Net points per game ~ win % | Pearson | 32 | 0.8781 | 4.1e-11 | 0.7630 to 0.9392 | 0.7808 to 0.9425 |
| COR-04 | Points for ~ points against per game | Pearson | 32 | −0.2041 | 0.2626 | −0.5160 to 0.1557 | −0.5298 to 0.1348 |
| COR-05 | Net points per game ~ win % | Spearman | 32 | 0.8658 | 1.6e-10 | 0.7407 to 0.9329 | 0.7087 to 0.9403 |
| COR-06 | Home win % ~ overall win % | Pearson | 32 | 0.8863 | 1.5e-11 | 0.7781 to 0.9434 | 0.8221 to 0.9373 |
| COR-07 | Division win % ~ overall win % | Pearson | 32 | 0.3084 | 0.0859 | −0.0451 to 0.5933 | −0.0605 to 0.6484 |
| COR-08 | Points for per game ~ net points per game | Pearson | 32 | 0.8019 | 3.4e-08 | 0.6291 to 0.8992 | 0.6137 to 0.9070 |

Two results are **not** distinguishable from zero at the 5% level: points-for vs points-against
(COR-04, p = 0.26) and division record vs overall record (COR-07, p = 0.086). Both are published as
they came out. Suppressing a null result is its own form of selection bias, and gate G05 exists
precisely to prevent it.

The p-values come from a two-sided Student-t test on r with n − 2 degrees of freedom; the tail
probability is computed from the regularized incomplete beta function in `src/nfl_309921cc/stats.py`.
The bootstrap reseeds with a fixed seed, so a rebuild reproduces the interval exactly.

## 3. The luck index

Regressing win percentage on net points per game across the 32 official rows:

```
win% = 0.4990 + 0.033574 × (net points per game)
n = 32, SE(slope) = 0.003341, t = 10.0498, df = 30, p = 4.075e-11
R² = 0.7710, residual SD = 0.1165 win percentage
```

The residual is the part of a club's record its scoring does not explain — close-game fortune,
turnover luck, special-teams variance, scheduling. In a 9-game sample, a residual of ±0.20 win
percentage is roughly ±1.8 wins.

| Most positive (won more than scoring implies) | Residual | Most negative | Residual |
|---|---|---|---|
| Denver Broncos | +0.234 | Tampa Bay Buccaneers | −0.255 |
| Cleveland Browns | +0.187 | Jacksonville Jaguars | −0.202 |
| Minnesota Vikings | +0.125 | Houston Texans | −0.195 |
| Arizona Cardinals | +0.122 | Tennessee Titans | −0.143 |

The full 32-row table is on the Correlations page. Residuals sum to zero by construction, which the
verifier checks.

## 4. What is still blank, and why

**No dependence between two betting legs is published.** Measuring one requires graded paired
outcomes under licence; the ledger is empty (flag NFL3-F09). The method is specified and is what
gate G09 will apply:

1. Build paired residuals on a training window only — never on the evaluation window.
2. Measure dependence with Pearson (continuous) or phi (binary joint outcomes) on an explicit joint sample.
3. Report the interval, not the point estimate, clustered by slate.
4. Never assume independence to make a price look better.

The eight correlations above are a **worked demonstration** of the estimator — same code path, same
interval method — applied to data we are allowed to have. They are not substitutes for the measured
leg dependence, and they are not presented as such.
