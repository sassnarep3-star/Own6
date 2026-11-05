# Executive Summary — Own6 Skill Lab

**Session:** `arena/53ada516-own6` · **Date:** 2026-11-05 · **Site:** https://sassnarep3-star.github.io/Own6/docs/skill/
**Scope:** signal generation, correlation measurement, luck removal, validation gates, and a leaderboard that rewards skill rather than luck.

---

## 1. The headline

**No strategy in this project qualifies. That is the finding, not a failure to finish.**

The repository now contains a complete, tested, reproducible machinery for deciding whether a
betting record is skill or luck. When that machinery is pointed at everything the repository can
lawfully measure, nothing survives — and the reasons are specific, quantified, and published
rather than hidden behind an empty table.

Three numbers explain the whole situation:

| | Value | What it means |
|---|---|---|
| Bets needed to detect a 3% edge at 80% power, −110 | **7,897** | The repository has 15 graded bets. |
| Median best ROI of 50 zero-edge strategies, 100 bets each | **20.3%** | A leaderboard sorting by ROI ranks this. |
| Verified real sportsbook prices in this build | **0** | NBA Terms §9 blocks the only lawful route. |

---

## 2. What was built

### 2.1 A luck-removal engine (`skillab/`)

Dependency-free where it matters, so the gates run in CI without scientific wheels.

| Module | What it does | Verified against |
|---|---|---|
| `pricing.py` | American↔decimal↔probability; proportional and additive de-vig; EV, Kelly, settlement | Closed-form identities (zero EV at break-even: 1e-12) |
| `luck.py` | Exact binomial, Student-t intervals, bootstrap and moving-block bootstrap, Brier decomposition, log loss, ECE | Published critical values: t(0.975,10)=2.228139, t(0.975,30)=2.042272; sklearn's documented Brier example (0.0375) |
| `correlation.py` | Pearson with t p-value, Fisher z interval, Spearman, **date-cluster bootstrap**, Gaussian copula for parlay joint probability | SciPy `pearsonr` and `multivariate_normal.cdf` — agreement to 1e-15 |
| `power.py` | Exact per-bet SD, z-power, minimum sample size, FWER growth | Round-trip: n from `n_for_power` achieves the requested power |
| `leaderboard.py` | Bonferroni, Holm, BH-FDR, stationary-bootstrap reality check, Hansen SPA, deflated Sharpe, PBO (CSCV), closed-form max-of-N | Holm never stricter than Bonferroni; deflated Sharpe monotone in trial count |
| `gates.py` | Twelve fail-closed gates SG01–SG12 | Known-answer experiments (see §2.3) |
| `simulate.py` | Six seeded archetypes with known ground truth | Fixed seed; byte-identical on rebuild |
| `audit.py` | Recomputation over the repository's own CSVs | Matches published summary to 5×10⁻⁴ |

### 2.2 A published site (`docs/skill/`, 11 pages)

Summary · Signal research · Singles · Parlays & combos · Correlation · Luck removal ·
Validation gates · Leaderboard · Proof of discrimination · Sources · Flagged for Review.

Every one of the **136 table rows carries a source link** — either an official document or the
module in this repository that produced the value. Every value carries one of four provenance
tags: **SYNTHETIC**, **REPO**, **FORMULA**, or **SOURCE**. A value that cannot be produced is a
blank cell with a visible flag; blank never means zero.

### 2.3 Proof that the gates work

A validation framework that rejects everything is not a test. Six archetypes with known ground
truth, all seeded and reproducible:

| Archetype | True edge | n | Realised ROI | Verdict | Why |
|---|---|---|---|---|---|
| Full evidence skill | 5% | 30,000 | 5.95% | **QUALIFIED (12/12)** | Passes every gate including the power requirement |
| Skill, 3,000 bets | 3% | 3,000 | 4.17% | Rejected (SG05, SG06) | Correct: 3,000 is under the 7,897 needed |
| Lucky heater | **0%** | 150 | **+12.00%** | Rejected (SG05,07,10) | A naive leaderboard ranks this first |
| Long-run luck | 0% | 3,000 | 0.42% | Rejected (SG05,07,10) | Converges to zero, as it must |
| Low power, real edge | 2% | 40 | 0.23% | Rejected (SG05,07) | Real edge, unusable sample |
| Overfit (best of 60) | 0% | 400 | 11.68% in-sample | Collapses to **−0.73%** OOS | Selection, not skill |

The framework therefore accepts a real, sufficiently-sampled edge and rejects a lucky one. It is
a test, not a wall.

---

## 3. Measured correlation values

Everything below is recomputed from `data/games_results_2026-27.csv` (92 games, 2026-10-20 to
2026-11-01), each row of which carries an official `nba.com` game link.

| Pair | Pearson r | n | 95% interval | Verdict |
|---|---|---|---|---|
| Home score vs away score (same game) | 0.2004 | 92 | −0.0046 to 0.3892 | Weak; interval nearly touches zero |
| Margin vs total (same game) | −0.0026 | 92 | −0.2073 to 0.2024 | No relationship |
| Rest differential vs home margin | −0.0801 | 76 | −0.3001 to 0.1480 | No relationship |
| Same-date game margins (pooled pairs) | 0.1052 | 357 pairs | **−0.0749 to 0.2205** (date-cluster) | **Not significant** |

### Three findings on the repository's own published values

1. **Two of three published correlations reproduce exactly.** Home/away (Δ = −1.1×10⁻⁵) and
   same-date (Δ = +1.7×10⁻⁵) match to rounding. Both are confirmed as arithmetically correct.

2. **The rest-differential value does not reproduce.** Published −0.0162 versus recomputed
   −0.0801 from the same file, same n = 76. A Δ of 0.064 is far outside rounding. This is
   **flagged, not silently corrected** — the rest definition belongs to the file's owner.

3. **The same-date "significance" is an artefact.** The nominal p-value of 0.047 looks
   significant. But every game appears in many of the 357 pairs, so the pairs are not
   independent. Resampling whole dates instead of pairs gives an interval of −0.0749 to 0.2205,
   which **contains zero**. This is pseudo-replication — the same error that inflates most
   amateur parlay-dependence claims.

---

## 4. Parlays and player-prop combinations

A parlay is one bet on a joint event, not k independent bets. Getting the dependence wrong is
the largest single source of fictitious edge in this space.

Two legs at 55% each:

| ρ | Joint probability | vs independence | Fair American price |
|---|---|---|---|
| 0.00 | 0.3025 | 1.000 | +231 |
| 0.20 | 0.3341 | 1.104 | +199 |
| 0.35 | 0.3586 | 1.186 | +179 |
| 0.50 | 0.3848 | 1.272 | +160 |

**The direction matters more than the magnitude.** For positively correlated same-game legs (two
overs in a fast-paced game), the true joint exceeds the product, so a book pricing at the product
pays short and the bettor who assumes independence leaves value on the table. For negatively
correlated legs — two teammates competing for one possession pool — the true joint is *below* the
product, and multiplying marginals **invents an edge on a bet that is actually overpriced**. Both
directions are handled by the same copula; only the sign of ρ changes.

The repository's single measured teammate pair has **n = 6**. Its interval spans almost the whole
range, so the sign is not established and it is published as a flagged observation, not a usable ρ.

---

## 5. Removing luck

Six independent mechanisms, all implemented and all exercised on simulated data:

1. **Sample size.** 7,897 bets for a 3% edge; 17,795 for 2%; 2,833 for 5%. A 200-bet record is
   uninformative regardless of process quality.
2. **Multiple testing.** P(≥1 false positive) = 1 − (1−α)^k. Exceeds 50% at 14 tries, ~90% at 45.
   Holm and BH-FDR both implemented; the leaderboard uses Holm over the *declared* family, and
   rejects a family size that does not match the number of p-values supplied.
3. **Selection bias.** The median max of 50 zero-edge strategies is 20.3% (simulation) versus
   21.0% (closed form Φ⁻¹(0.5^(1/N))·σ/√n). A leaderboard sorting by ROI measures this.
4. **Family-wide reality check.** White's bootstrap reality check (p = 0.31) and Hansen's SPA
   (p = 0.17) both correctly fail to reject on 60 zero-edge strategies.
5. **Deflated Sharpe.** Requires DSR ≥ 0.95 given the number of trials; penalises trial count
   monotonically (verified by test).
6. **Probability of backtest overfitting.** Reported as 0.49 on the simulated family (high risk,
   correctly detected) and **refused** on the repository's real data, where 15 observations cannot
   support CSCV. A blank is better than a meaningless number.

---

## 6. Leaderboard and rewards

A strategy appears on the board only after passing all twelve gates. Eligible strategies rank by
the **lower bound** of a block-bootstrap 95% interval on return per bet — the worst plausible
estimate, not the best observed one — with a deflated-Sharpe tie-break.

Four anti-gaming properties:

- **Can't win on volume:** SG05 requires power for the *claimed* edge.
- **Can't hide failed variants:** SG09 rejects a mismatch between declared and supplied trials.
- **Can't win on a heater:** the ranking uses the lower bound.
- **Can't win on a lucky parlay:** SG11 requires measured dependence with n and an interval.

**No reward is configured or paid.** Any reward scheme depends on SG01, which is open.

---

## 7. Repo review — irregularities found

| ID | Sev | Finding | Status |
|---|---|---|---|
| S-F01 | High | No lawful basis for gambling-related use of NBA data (Terms §9) | Open; needs written permission |
| S-F02 | High | Rest-differential correlation does not reproduce (−0.0162 vs −0.0801) | Flagged, not corrected |
| S-F03 | High | Same-date correlation's p-value is pseudo-replication | Flagged; cluster CI published |
| S-F04 | High | 15 graded bets vs 7,897 needed | No fix without a lawful archive |
| S-F05 | Med | Teammate correlation n = 6 | Published as flagged observation |
| S-F06 | Med | Three incompatible gate numberings (G1–G8, G01–G10, SG01–SG12) | Crosswalk published |
| S-F07 | Med | Five earlier PRs (#23, #28, #31, #32, #37) open and conflicting >24h | Not merged; assessed and logged |
| S-F08 | Med | `data/source_coverage` snapshot is stale | Owned elsewhere; logged |
| S-F09 | Low | Repository has no licence | Owner decision |
| S-F10 | Low | Every published strategy return is synthetic | Labelled on every table |

Two defects were found **in this session's own code** by the SciPy cross-check and fixed before
publication, both now covered by tests:

- The parlay copula used ρ as the factor loading instead of √ρ, understating joint probabilities
  by up to 4 points.
- The SG06 loss comparison was inverted, which would have credited a model that lost *more* than
  the market.

Both are recorded on the Flagged page. A framework that does not report its own near-misses is
not credible about anyone else's.

---

## 8. Verification performed

| Check | Result |
|---|---|
| `pytest tests/` (whole repository) | 177 passed |
| `tests/test_skilllab.py` (new) | 75 passed |
| `tools/run_tests.py` | 32/32 |
| `tools/release_gate.py` | 0 issues |
| `tools/check_site.py` | 0 errors, 31 advisory (pre-existing, other scope) |
| `scripts/check_skilllab.py --check` | OK, 11 pages, 136/136 rows sourced, reproducible |
| `scripts/check_site.py`, `linkcheck.py`, `verify_data.py` | OK, 240/240, 213/213 |
| `scripts/check_hub.py`, `check_lab.py`, `check_report.py` | 335 rows / 0 errors, OK, OK |
| `scripts/audit_integration.py` | all checks passed |
| SciPy copula cross-check | max deviation 7.8×10⁻¹⁶ |

**Official sources read directly this session** (2026-11-05): NBA Terms of Use §1/§9, NBA Stats
FAQ, NBA Stats glossary, NIST/SEMATECH e-Handbook 1.3.6.6.18 (binomial) and 1.3.5.17 (outlier
detection), SciPy `pearsonr` and `bootstrap`, scikit-learn `brier_score_loss`, statsmodels
`multipletests`. Each is linked on the Sources page with the date it was read.

---

## 9. What is not claimed

- **No profitable strategy.** Zero qualified.
- **No real edge, ROI, CLV, or correlation presented as established.** Every correlation is
  published with its interval; two are indistinguishable from zero.
- **No NBA data was scraped or republished.** No new NBA value entered this repository.
- **No legal opinion.** SG01 is a gate on a factual question (do you hold permission), not a
  legal conclusion.
- **No betting advice.** This is research infrastructure. It does not place, accept, or
  recommend a wager.

---

## 10. What would change the answer

In dependency order:

1. **Written permission or a licensed provider contract** covering gambling-related use. Without
   this, SG01 fails and nothing downstream can be published.
2. **A timestamped two-sided price archive** across a full season. This unlocks CLV, makes SG07
   meaningful, and gives the first honest shot at 7,900 observations.
3. **Paired player game logs** with minutes and usage. This unlocks the prop and combo families
   and makes a real correlation estimate possible.
4. **Pre-registration of the family** before the first bet, with the plan hash committed.

Only then does the leaderboard have a real entrant. Until then, the correct output of a
skill-versus-luck system is zero qualified strategies, and this build produces exactly that.
