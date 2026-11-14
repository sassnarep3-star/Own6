# NFL Line Desk (F4) — executive summary

**Built:** 2026-11-14 · **Branch:** `arena/f4e592a7-own6` · **Site:** `docs/nfl-f4/`
**Dashboard:** `docs/nfl-f4/index.html` · **Flags:** `docs/nfl-f4/flagged.html`

## Bottom line

Every piece of infrastructure the brief asked for is built and verified. The
verdict it returns is that **no strategy can be certified yet**, and the pack says
so in public rather than producing a leaderboard that looks like progress. With
137 verified game results (scores only) and one settled priced game, any "top
strategy" would be noise wearing a rank.

## What exists

| # | Requirement | Built | Evidence |
|---|---|---|---|
| 1 | Price-snapshot store, opening **and** closing numbers | 14 games · 42 markets · 168 snapshots, each with the vig | `data/nfl_f4/price_snapshots.csv` |
| 2 | Verified results feed usable by backtests | 137 finals, weeks 1–10 | `data/nfl_f4/results.csv` |
| 3 | Origination order side → total → moneyline | order enforced by the builder's sort | `data/nfl_f4/originated_markets.csv` |
| 4 | Fair line / market line / difference as separate columns | 42 markets, difference signed from home | `data/nfl_f4/fair_vs_market.csv` |
| 5 | Signal separated from staking | two independent scores + a luck p-value | `data/nfl_f4/leaderboard_strategies.csv` |
| 6 | Depth **of the replacement**, not the fact | 45 slots, string recorded, contingency branch | `data/nfl_f4/depth_replacement.csv` |
| 7 | Correlations from officially sourced numbers, **with n** | 3 measured, 2 uncomputable, 1 insufficient | `data/nfl_f4/correlations.csv` |
| 8 | Demotion gate live → paper | 6 rules, fixed thresholds, sticky | `data/nfl_f4/demotion_gate.csv` |

## The results feed checks itself

All 32 teams' wins, losses, ties, points for and points against are recomputed
from the 137 game rows and compared field by field against the official standings
captured the same day: **32 of 32 match on all five fields**. A single mismatch
exits non-zero instead of publishing (`results.reconcile_or_raise()`).

## Findings that matter

1. **The model disagrees with the close almost everywhere, and that is not an
   edge.** A naive points-per-game rating 1–3.5 points off a closing line is
   evidence about the rating, not about the line.
2. **Side/total correlation is not established.** r = −0.161, n = 137, p = 0.061,
   95% CI spanning zero. Same-game parlays should be priced at independence for
   now, with the caveat that a real effect this size needs ~400+ games to resolve.
3. **Offence and defence are separable.** r = 0.075 between points scored and
   allowed in the same team-game (n = 274). A useful negative: model them apart.
4. **Rest differential — the most-cited public signal — is uncomputable here** and
   is published as such rather than proxied.
5. **Depth charts are unofficial by the clubs' own words.** Both pages read say so;
   every depth row carries the club's caveat verbatim.
6. **One-week injury reports hide the case that matters.** New England's RB1 is
   Questionable in front of an RB2 who is **Out**, so the contingency is the
   **third string** (Corey Kiner). A single-injury headline would miss that.

## Grading, and why the board is empty

| Strategy | Settled bets | Signal / bet | Staking (units) | Luck p | Certified |
|---|---|---|---|---|---|
| S1 Side: fade biggest disagreement | 0 | — | — | — | no |
| S2 Side: follow the model | 1 | −1.0000 | −1.0000 | 1.0000 | no |
| S3 Total: model side | 1 | +5.0000 | +0.8929 | 0.5000 | no |
| S4 Moneyline: prob edge | 1 | +0.0391 | −1.0000 | 1.0000 | no |
| S5 SGP side+total | 2 | +2.0000 | −0.1071 | 0.7500 | no |
| S6 Parlay, two sides | 1 | −1.0000 | −1.0000 | 1.0000 | no |
| S7 Prop combo | 0 | — | — | — | no (blocked: no player-level official data) |

Gate floors: ≥100 settled bets, ≥6 weeks, ≥90% price presence, luck p ≤ 0.05.
Nothing clears any sample floor, so `leaderboard.csv` is **empty by design**.

## Mask test

The guard the brief asks for: could a lucky staking run mask a bad signal?
Synthetic case — ten winning bets at even money (staking **+10 units**) where
every bet had negative closing-line value (signal **−1.0/bet**). The board marks
`board_can_mask = true`, labels the row
`lucky_staking_run_positive_pnl_nonpositive_signal`, and refuses certification.
This is asserted by `tests/test_nfl_f4.py::test_mask_test_catches_lucky_staking_run`,
because the live board's 2-bet sample cannot demonstrate it.

## Demotion gate

D1 signal decay · D2 drawdown > 8 units · D3 three negative weeks · D4 positive
ROI on non-positive signal (the mirror of the mask test) · D5 any ungradeable live
bet · D6 model drift. Missing data counts **against** a strategy. Demotion is
sticky; re-entry needs 40 fresh settled bets with a positive signal.

## Numbers to keep in view

- 137 games verified · 32/32 teams reconcile · 0 mismatches
- 14/14 games priced · 42 markets · 168 snapshots · **only 1 settled close**
- 42 originated markets · 7 strategies proposed · **0 certified**
- 3 correlations measured (n = 137, 274, 137) · 2 uncomputable · 1 insufficient
- 45 depth slots · 2 of 32 clubs (unofficial) · 4 forced replacements
- 20 flagged items · 16 decision questions (11 answered, 5 open) · 10 suggestions
  pending your choice · 12 repo-review claims checked

## Open decisions for you

1. Keep the leaderboard empty, or publish a *provisional, not certified* board with
   the gates printed on every row? (**S01**)
2. Add a second operator's close, so CLV is robust to one book's movement? (**S02**)
3. Backfill settled closes for weeks 1–9 to reach the sample floor now? (**S03**)
4. Cover all 32 clubs' depth, or find an official feed instead? (**S04**)
5. Add opponent-adjusted ratings, or keep the naive model and say so? (**S05**)

Nothing in the suggestions is implemented. `data/nfl_f4/suggestions.csv` keeps every
row at `state=pending_human_choice`.

## Verification

```
python3 scripts/registers_nfl_f4.py
python3 scripts/build_nfl_f4.py
python3 scripts/check_nfl_f4.py --rebuild     # 318 checks, 0 failures
python3 -c "from src.nfl_f4 import results; results.reconcile_or_raise()"
python3 -m pytest tests/test_nfl_f4.py -q     # 57 passed
```

The site is zero-input: no forms, no inputs, no localhost, no client-side data
fetching; every table row carries an external reference or an explicit flag.
