# NFL line origination, availability and selective skill — session `67233566` executive summary

**Pack:** [`src/nfl_67233566`](src/nfl_67233566) · **Data:** [`data/nfl_67233566`](data/nfl_67233566) (58 tables,
1,723 data rows) · **Site:** [`docs/nfl-67233566/index.html`](docs/nfl-67233566/index.html) (20 pages)
**Official capture:** 2026-11-15T23:26:34Z … 23:32:40Z (UTC) · **Branch:** `arena/67233566-own6`
**Verification:** `python3 scripts/check_nfl_67233566.py` (15 checks) and
`python3 -m unittest discover -s tests -p test_nfl_67233566.py` (36 tests); every table is rebuilt
byte-identically from the frozen capture by `python3 scripts/build_nfl_67233566.py`.

---

## 1. The one-sentence version

The results side of the brief is closed and *provable*: 145 finished games, 220 identity checks, zero
mismatches. The pricing side is closed only in the sense that the door is locked from outside — no
official page in this repository's evidence set prints a price, so every market column is blank by
policy. Ten of the 79 traced requirements turn on a price at all and share a single gate (G-08, failed
closed); of the 17 requirements blocked for want of a source, exactly **one** is that missing price, and
the other sixteen are capture and coverage problems. Both counts are recomputed from
`requirements_trace.csv` on every build, so this paragraph cannot drift away from the table.

## 2. What was verified, and how

| Item | Number | How it is checked, not asserted |
|---|---|---|
| Finished games in the corpus | **145** of 150 published rows | `results_feed.csv`; the 5 excluded rows printed `in_progress` or `unplayed` at capture and are published separately in `week10_at_capture.csv` |
| Identity checks against the official standings and every card badge | **220 run · 0 mismatches** | `reconciliation_checks.csv`; the checker re-runs `corpus.reconcile` and fails the build on a single mismatch |
| Independent re-read agreement | **1 of 1** fixture | `independent_read_agreement.csv` — the pinned prior capture was read on 2026-11-14, when only the Thursday game of Week 10 had finished, so overlap is 1 by construction |
| Games gradable walk-forward | **129** (16 week-1 games cannot be) | `backtest_corpus.csv` carries a `graded_walk_forward` flag and the reason for every `no` |
| Brier sample | **128** (one tie is a push and is excluded from scoring, kept in the error means) | `leaderboard_signal.csv` `n_graded` |
| Price rows, hash-chained | **130 · 0 chain problems** | `price_snapshots.csv`; `check_nfl_67233566.py::c04` rebuilds the chain from the CSV |
| Blank cells published instead of inferred values | **2,794** across 56 tables | `blank_audit.csv`, recomputed from the files by `c10` |
| Price-capture attempts logged | **5** (4 negative, 1 not attempted by policy) | `market_price_capture_log.csv` |

## 3. What the model says

Specification `nfl_67233566_v1`, frozen in the claim commit named in `preregistration.csv`
(`data/nfl_67233566/claim_commit.txt`, verified to be an ancestor of `HEAD` by `c13`):

* Estimated home effect **−0.4950 points** (fit through the Week 10 finals; the Week 11 open vintage uses
  the fit through Week 9, where it is −0.366). A negative estimate is a finding, not noise to be
  smoothed: any feature that assumes home advantage is loading a prior this season's data does not support.
* Margin residual SD **10.663 points**; league scoring **22.963 points per team** through Week 9 — which
  independently reproduces session `d966f630`'s figure from a separate code path (`walk_forward_design.csv`).
* Mean absolute error on the 129 graded fixtures: **9.7907** points on the side, **11.3643** (T1) and
  **11.2093** (T2) on the total — about three field goals either way. Both total estimators stay published;
  the pre-registered collapse rule (n ≥ 100 **and** |gap| > 1.5 × SE of the paired gap) is satisfied on n
  and not on the gap, so nothing collapses (`totals_winner_decision.csv`).
* Correlations worth having: net points vs win percentage **r = 0.880** (n = 32), wins vs point differential
  **0.856** (n = 32), predicted margin vs actual **0.2725** (n = 129, permutation p = 0.0020). A club's
  week-to-week margin persistence is only **0.1258** (n = 243, p = 0.057) and total persistence **0.0459**
  (p = 0.475): ratings must be re-estimated every week, and a totals model built on recent scoring has
  almost no raw material. Blowout-versus-total dependence, the pair a same-game parlay actually rests on,
  is **−0.1578** (n = 145, p = 0.0625) — real but not significant at the pre-registered level.
* Combo evidence: joint P(home win ∧ over T1) **0.2109** vs the product of marginals **0.2271**, difference
  **−0.0161** with 95 % CI **[−0.0582, 0.0267]** (n = 128). Dependence is measurable and *not* distinguishable
  from zero here, so a two-leg same-game parlay may be ranked by proper score and may not be priced.
* Ablations instead of fixed penalties: the home-field axis is worth **0.1047** points of MAE with a CI of
  **[−1.8488, 2.1357]** (n = 129), and the personnel axis could only be tested on **2** fixtures — which is
  the answer to "why is there no injury adjustment in the lines": the measurement, not a coefficient.

## 4. The competition, honestly reported

12 strategies registered (STR-01 … STR-12); 9 could be graded at all; **4 of those 9 clear every signal
gate simultaneously** — positive benchmark-relative skill, a game-cluster lower bound above zero, a
calibration gap inside ±0.05, and survival of Benjamini-Hochberg at q = 0.10 across the trials run. The
totals division produces **0** qualifiers. The staking division produces **0** of 12, and no number of
additional strategies changes that: `leaderboard_staking.csv` is a header-only file with an empty-table
explanation, and `escrow_stage2.csv` records both opening conditions as failing.

The luck panel is deliberately unflattering: **78.82 %** of the spread in 32-club win totals is *not*
explained by the model's own expectation, and a room of 12 coin-flipping strategies over 128 games
produces a best win rate of **0.6172** in simulation. Any single strategy's headline record at this
sample size is expected noise, which is why promotion needs the lower bound rather than the point estimate.

Every strategy is in state `paper` against all seven demotion rules (DG-01 … DG-07 evaluated per strategy
in `demotion_gate.csv`), and one promotion was refused on record in `state_transitions.csv`: a
"best-of-ten" win rate is not a reason to stake.

## 5. What is missing, and who can supply it

17 requirements are `blocked_no_source` and 17 are `implemented_partial`; 43 are recorded as
`implemented_verified` or `verified`, and 2 are owner rejects kept closed. The blocking-question
register (`questions.csv`) has 12 rows: 5 answered — within bounds, officially, or by measurement — and
7 open, two of which the register labels as decisions rather than research gaps. The short version:

1. **A price source whose terms permit storage** (SG-01). Closes `G-08` and, with it, nine dependent
   requirements. Nobody at Arena can decide this; it is an owner/procurement call.
2. **Two dated captures a week of the injury report** (SG-02), plus inactive lists and snap counts
   (the only route to depth and to "Questionable" calibration). One read is a level; a surprise is a delta.
3. **A ruling on depth** (SG-07): 4 of 32 club depth charts render as extractable text and one club
   publishes it as an image, so `depth_source_register.csv` records both routes as unverified and the
   starter/quality columns stay blank. The owner's rejected shortcut (jersey order, experience, salary)
   is recorded as closed.
4. **One canonical desk** (SG-12): the repository holds several parallel NFL packs whose corpus
   boundaries differ (145 here, 44 there, 347 injury rows versus 50 versus the requirement's 254/279);
   `repo_findings.csv` RV-01…RV-07 lists each collision with a disposition and no edits to other
   sessions' files.
5. **Scheduled capture and durable storage** (SG-03/G-11): this pack has exactly one capture and no
   alerting; `snapshot_ledger.csv` says so per block and `drift_alarms.csv` fires on the shape pins.

Nothing above was implemented on the strength of a suggestion: every row of `suggestions.csv` is
`status=awaiting_owner_choice`, and the checker fails any page that contains an input control
(`c11`), because the site takes no manual input in either direction.

## 6. Irregularities found while doing this

15 flags, none of which blocks the merge (`flagged.csv`, published at
[`docs/nfl-67233566/flagged.html`](docs/nfl-67233566/flagged.html)) — 3 high, 6 medium, 6 low. The high
ones, in one line each: the Week 11 injury report does not exist yet and the page's own selector stops
at Week 10; the injury page mis-groups some players against their club line and prints `AZ` where other
pages print `ARI`; and four different row counts exist for one injury page with no retained hash to
adjudicate between them.

## 7. Reproduce it

```bash
python3 scripts/build_nfl_67233566.py      # 58 tables + 20 pages from the frozen capture
python3 scripts/check_nfl_67233566.py      # 15 checks, exits non-zero on any unsourced or fabricated cell
python3 -m unittest discover -s tests -p test_nfl_67233566.py
git diff --exit-code -- data/nfl_67233566 docs/nfl-67233566   # must be empty: nothing was hand-edited
```

Research only. No prices, no picks, no profitability claim; a blank cell means no official value exists.
