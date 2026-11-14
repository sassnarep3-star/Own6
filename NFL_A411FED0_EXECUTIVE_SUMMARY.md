# NFL Originated Lines — Executive Summary

**Session:** `a411fed0` · **Branch:** `arena/a411fed0-own6` · **Captured:** 2026-11-14
**Dashboard:** [`docs/nfl-a411fed0/`](docs/nfl-a411fed0/index.html)
**Data:** `data/nfl_a411fed0/` · **Code:** `src/nfl_a411fed0/`

---

## The one thing to know first

**This pack originates lines but has no prices, so nothing in it can be
promoted to live betting — and that is the correct outcome, not a shortfall
to be papered over.**

The NFL does not publish point spreads, totals or moneylines anywhere. Every
page we could read — scores, schedules, standings, injuries, and all 32 club
sites — carries results and rosters, never prices. We enumerated all 84
originated Week 10 markets in the price-snapshot store and left every price
cell **blank** rather than filling it from a non-official source. A number we
cannot verify is worse than no number.

That single fact propagates through everything:

- ROI cannot be computed.
- Closing-line value cannot be computed.
- No bet can be settled.
- Gate `A4-G05` fails closed, so **no strategy is eligible to leave paper**.

So the leaderboard is ranked on **Brier score** — whether the probabilities a
strategy produced were calibrated out-of-sample — not on profit.

---

## What was built

| Requirement | Status | Where |
|---|---|---|
| Price-snapshot store (opening + closing) | **Built, empty** — 84 markets enumerated, 0 prices | [`prices.html`](docs/nfl-a411fed0/prices.html) |
| Verified results feed | **Built** — 120 games verified against official standings | [`results.html`](docs/nfl-a411fed0/results.html) |
| Originate side → total → moneyline, in that order | **Built** — 14 games × 3 markets | [`origination.html`](docs/nfl-a411fed0/origination.html) |
| Fair line / market line / difference as separate columns | **Built** — market and difference blank, never guessed | [`origination.html`](docs/nfl-a411fed0/origination.html) |
| Signal separated from staking | **Built** — separate columns, separate pages | [`staking.html`](docs/nfl-a411fed0/staking.html) |
| Depth of replacement, not just "injured" | **Built** — 43 resolved, 304 unresolved and flagged | [`injuries.html`](docs/nfl-a411fed0/injuries.html) |
| Correlations from official numbers, with n | **Built** — 10 correlations, each with n and a 95% CI | [`correlations.html`](docs/nfl-a411fed0/correlations.html) |
| Demotion gate | **Built** — 6 armed rules with numeric thresholds | [`gates.html`](docs/nfl-a411fed0/gates.html) |
| Suggestions section for human review | **Built** — 12 suggestions, none implemented | [`suggestions.html`](docs/nfl-a411fed0/suggestions.html) |
| Questions, split by what we have / don't have | **Built** — 18 questions, each with a route to the answer | [`questions.html`](docs/nfl-a411fed0/questions.html) |
| Leaderboard competition with rewards | **Built** — 10 strategies, 4 reward tiers | [`strategies.html`](docs/nfl-a411fed0/strategies.html) |
| Single bets, parlays, player-prop combos | **Partial** — prop family blocked on data | [`strategies.html`](docs/nfl-a411fed0/strategies.html) |
| Executive summary | **This document** | — |
| Flagged irregularities published | **Built** — 17 flags with verbatim evidence | [`flagged.html`](docs/nfl-a411fed0/flagged.html) |

---

## The headline numbers

- **120 verified games** — weeks 1–3 and 5–9 of 2026. Week 4 is missing; the
  official page renders the string `"Hidden Score"` in place of every score
  (flag `A4-F01`).
- **84 originated markets** for Week 10 — 14 games × 6 market families.
- **347 injury-report rows** covering all 28 clubs on the official Week 10
  report.
- **43 of 77** Out-or-Doubtful players have a resolved replacement string.
  Only 4 of 32 club depth charts rendered as extractable text.
- **6 of 10** validation gates fail. Ten out of ten must pass before anything
  goes live.
- **10 of 10** strategies are in paper. Zero are eligible for promotion.

---

## The three findings that matter

### 1. Losing signals can look like winners if you let staking into the headline

Strategy **A9-S05** (home underdog) hit **34.1%** of its picks — a badly
losing signal — and under flat staking it lost **15.4 units**. Under a
doubling-up plan it ran to a **positive peak of +8.0 units** before a
**drawdown of 511 units**.

The signal is byte-for-byte identical in both columns. Only the staking
changed. This is precisely the failure mode the signal/staking separation
exists to prevent, and it is why the two are never merged into a single
column anywhere in this pack.

### 2. The totals model does not currently work

Walk-forward, pooled over 88 out-of-sample games:

| | Model MAE | Constant-baseline MAE | Verdict |
|---|---|---|---|
| Margin | 9.93 | 10.68 | **beats baseline** |
| Total | 12.27 | 11.34 | **loses to baseline** |

Step 1 of the origination order (the side) clears its baseline. Step 2 (the
total) does not — it is beaten by simply predicting the league average every
time. The totals in this pack are therefore **diagnostic only and must not be
bet** (flag `A4-F09`). Gate `A4-G04` fails on this leg.

### 3. Skill takes far more data than intuition suggests

At −110 the break-even win rate is **52.38%**. To demonstrate a genuine
5-point edge at 99% confidence and 80% power takes about **1,160 settled
bets** — roughly six seasons at 200 bets a year. A 2-point edge takes
**7,273**.

Any claim of skill from a single season is a claim about luck. This is why
the leaderboard is ranked on probability scoring, and why closing-line value
is the recommended primary metric once prices exist — it converges without
waiting for results to accumulate.

---

## What is still missing, in priority order

| # | Gap | Cost | Route |
|---|---|---|---|
| 1 | **Prices** — no official feed exists | No ROI, no CLV, no settlement. Blocks promotion entirely. | License a feed, or capture in-house at two fixed clock times per week and store the raw capture as evidence |
| 2 | **2026 Week 4 results** — 16 games | 12% hole in the training data, biasing every club that played that week | Re-fetch the page (renders are non-deterministic) or read each club's game log |
| 3 | **Club depth charts** — only 4 of 32 readable | The most original signal in the pack is unevaluable (n = 2) | Scrape all 32 club sites weekly with a per-club render check; the Texans page is an image and needs another route |

Those three gaps account for **every failing gate** in this pack.

---

## Governance

**Demotion gate** — six armed rules, each with a numeric threshold, that
send a live strategy back to paper: trailing-ROI confidence, closing-line
value decay, drawdown breach, missing price snapshot, parameter drift outside
pre-registered bounds, and minimum live sample. The strictest is `A4-D04`: a
single bet placed without *both* an opening and a closing price recorded
sends the strategy back to paper and quarantines the affected bets.

All six currently report `armed_not_evaluable`, because there are no live
strategies — the gate blocks promotion before it has to block demotion.

**Reward tiers** — Tier 1 (promoted, live staking) requires all ten gates
passing and ≥ 1,000 settled bets; **no strategy qualifies**. Tier 2 is the
paper leader on Brier score, currently **A9-S01** at 0.2315. Tier 3 is
research, published but not staked. Tier 4 is blocked, with the blocker
tracked publicly.

---

## Verification

- **126 automated checks** pass — `python scripts/check_nfl_a411fed0.py`
- **29 tests** pass — `python -m pytest tests/test_nfl_a411fed0.py`
- **Every data row** in all 19 tables carries a link to the official page it
  was read from, and every URL resolves to an official NFL or NFL club domain.
- **Every unverifiable value** is left blank and rendered as a striped
  "unverified" cell, never inferred.
- CI rebuilds the artifacts from the raw captures and **fails if the committed
  output has drifted** from what the code produces.

---

## Recommendation

Do not promote anything. The correct next action is to close gap #1 —
prices — because it is the binding constraint on everything else. Ten more
strategies evaluated on probability scoring still would not tell us whether
we can beat a number.

Full detail, including the verbatim evidence behind every flag, is on the
[Flagged for Review](docs/nfl-a411fed0/flagged.html) page. The 18 questions
that must be answered before a decision is reasonable — split by what we have
and do not have, each with a concrete route to the answer — are on the
[Questions](docs/nfl-a411fed0/questions.html) page.
