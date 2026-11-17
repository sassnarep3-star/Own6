# NFL Week-10 Settlement & Settled Leaderboard — Executive Summary

**Session:** `arena/45abd396-own6` (Arena session `45abd396`)
**Captured:** 2026-11-17 UTC (eight single manual reads of official nfl.com pages)
**Site:** https://sassnarep3-star.github.io/Own6/docs/nfl-45abd396/
**Data:** `data/nfl_45abd396/` (22 CSVs) · **Code:** `src/nfl_45abd396/` (5 modules) · **Pages:** 15

---

## 1. The one thing that changed

Week 10 is **settled** on the official schedule page. Thirteen of fourteen cards print `FINAL`
(the fourteenth, LAC @ BAL, was still pre-kickoff at this read). Before today the repository
held **pre-kickoff forecasts with no official result to score them against**, which is why every
earlier leaderboard in this repo was empty or backtest-only.

This pack scores them. It is the first *settled* proper-score leaderboard in the repository.

## 2. What was settled, and what was thrown out

| | Count |
|---|---|
| Forecast rows found in the repo that name a Week-10 fixture | 68 |
| Pre-kickoff rows (committed before kickoff) | 61 |
| — of which settled against an official final | 56 |
| — of which still unplayed (LAC @ BAL, 5 strategies) | 5 |
| **Post-kickoff rows, excluded from every score** | **7** |
| Distinct strategies scored | 5 |

The seven exclusions matter more than any number on the site. They are forecasts for the Thursday
night game whose files were first committed on 2026-11-13 and 2026-11-14 — after the game kicked
off at 2026-11-13T01:15Z. A leaderboard that had scored them would have been scoring a "forecast"
that could have seen the result. The commit time for every row is on the
[settlement page](docs/nfl-45abd396/settlement.html), so the claim is checkable.

## 3. The result: positive point estimates, zero qualifications

| Rank | Strategy | n | Brier | Brier (climatology) | Skill vs climatology | 95% game-cluster CI | Qualified |
|---|---|---|---|---|---|---|---|
| 1 | WK-ML | 12 | 0.1307 | 0.2222 | **+0.412** | [−0.260, +0.638] | no |
| 2 | A411-ML-NORMAL | 12 | 0.1586 | 0.2222 | +0.286 | [−0.435, +0.540] | no |
| 3 | D966-ML | 12 | 0.1620 | 0.2222 | +0.271 | [−0.726, +0.418] | no |
| 4 | A411-ML-EMPIRICAL | 12 | 0.1625 | 0.2222 | +0.269 | [−0.415, +0.526] | no |
| 5 | N6F-ML | 18 | 0.1786 | 0.2222 | +0.196 | [−1.087, +0.334] | no |

Three of the five went 11-for-12. Under coin-flipping that is a two-sided p ≈ 0.006 — which *looks*
like skill and is not. Three reasons it is not:

1. **Twelve games is one draw.** The interval is a bootstrap that resamples **fixtures**, not rows,
   and every one contains zero.
2. **The strategies are not five opinions.** All five derive from the same input (points for and
   against per game). On the 13 fixtures where several strategies published, the mean gap between
   the most and least confident home-win probability is **0.147** and the maximum is **0.202**.
   Their agreement is not independent confirmation.
3. **Multiplicity.** Five strategies were tried against the same twelve games; the Šidák-adjusted
   per-test level is **0.01021**, and no hit count clears it. The true trial count is higher, because
   earlier packs ran further variants elsewhere in the season — so 5 is a lower bound, and the
   adjustment on the site is therefore *not conservative enough*, which is stated on the page.

## 4. Removal of luck, stated in hits rather than percentages

| Strategy | Hits | Coin expects | Coin 95% band | p (two-sided) | Significant after adjustment |
|---|---|---|---|---|---|
| WK-ML | 11 / 12 | 6.0 | 3–9 | 0.0063 | no |
| D966-ML | 11 / 12 | 6.0 | 3–9 | 0.0063 | no |
| N6F-ML | 11 / 12 | 6.0 | 3–9 | 0.0063 | no |
| A411-ML-EMPIRICAL | 9 / 12 | 6.0 | 3–9 | 0.1460 | no |
| A411-ML-NORMAL | 9 / 12 | 6.0 | 3–9 | 0.1460 | no |

Both control baselines (a seeded coin and a rating favourite) face exactly the same twelve
fixtures, so "skill" and "no skill" are compared on identical games.

## 5. Availability: the sweep, the reserve list, and the stale row

- **The 32-club sweep is 28 of 32.** The Week-10 injury hub renders 28 club tables across 14
  fixture blocks. CHI, DEN, PHI and TB have no table at all, and none of the four is on a bye.
- **347 player rows** at a new clock (2026-11-17T00:47Z), joined to the two earlier reads.
  **Zero of 155 paired designations moved** — and the honest reading is that both earlier reads
  came *after* those clubs' games, so this measures agreement, not in-week movement.
- **25 reserve/injured entries** were published in November. **14 of them never appear on the
  weekly report.** A model reading only the weekly report would treat those fourteen players as
  available. This is the brief's "not listed never means available" rule, demonstrated on data.
- **One stale row is proven.** Daiyan Henley was traded LAC→DEN on 11/10 per the league's own
  transactions table, and is *still* in the Chargers' injury table at this read. This is exactly
  the failure mode the brief warns about with the Ravens' depth chart.
- **No replacement is ever named.** The report publishes a designation, not a depth chart, and no
  Game Book was obtained. Every `actual_start` cell is blank with a printed reason.

## 6. What is deliberately absent

- **No market line.** No nfl.com page prints a price. There is no ROI, no closing-line value, no
  residual-vs-market and no vig-free consensus anywhere on this site — the cells are blank with the
  reason attached, not filled with a plausible guess.
- **No staking column**, so the brief's "a lucky staking run must not mask a bad signal" rule is met
  by there being nothing to get lucky with.
- **No "Questionable means 62%" figure.** That number needs designations joined to official
  inactives across seasons; that join does not exist yet.
- **No depth rank from jersey number, salary or experience.** Rejected explicitly on the
  depth page, per the brief.

## 7. Read this next, in this order

1. [Settlement](docs/nfl-45abd396/settlement.html) — 68 rows with commit times and kickoffs.
2. [Settled leaderboard](docs/nfl-45abd396/leaderboard.html) — the scoring table and the disagreement table.
3. [Removal of luck](docs/nfl-45abd396/luck.html) — the binomial view.
4. [Questions → answers](docs/nfl-45abd396/questions.html) — 16 questions, each with the route that would fill the gap.
5. [Suggestions](docs/nfl-45abd396/suggestions.html) — 10 proposals with a review state you can act on.
6. [Flagged for review](docs/nfl-45abd396/flagged.html) — 12 items, each with both source links.

## 8. The three actions that would change the most

1. **Re-read one page after the Monday game ends.** That closes the fourteenth fixture and makes
   the sample complete. Cost: one page. No new method needed.
2. **Answer Q-01 (NFL.com Terms §1.3).** Every cadence-dependent requirement — the Wed/Thu/Fri
   injury series, the price archive, the daily depth sweep — is blocked by the rights boundary,
   not by effort.
3. **Read 13 game-centre Game Info blocks** to finish the Week-11 venue register. This is the
   cheapest gate blocked only by effort.

## 9. Verification performed

- Builder is offline and **byte-identical across two consecutive runs**.
- Verifier: **3,442 checks, rules 1–20, zero failures** — including recomputing every Brier score
  and every skill score from the settled rows, recomputing every margin and total from the finals,
  and asserting that the availability graph has **zero** non-blank actual-start cells.
- **30 pack tests** pass, including adversarial ones (an inverted forecaster must score negative
  skill; a control must carry no probability information; a delta must not be claimed for a club
  never read before).
- CI workflow `.github/workflows/nfl-45abd396-ci.yml` re-builds, re-diffs and re-runs all of the
  above.

## 10. Honest limitations of this pack

- Five strategies, twelve games each, one sport, one week. Nothing here is a track record.
- The game-cluster bootstrap shares a base rate across replicates drawn from only 12–13 fixtures,
  so its intervals are wide and its tails are coarse. It is a floor on uncertainty, not a
  confidence statement about the future.
- The Week-11 fixtures are published with **no** availability features, because the Week-11 report
  does not exist yet. That is a stated omission, not a modelling choice.
- The favourite control's Brier is 0.25 by construction and carries no information; only its hit
  rate is reported.
