# NFL decision desk — executive summary (session 0ce967db, 2026-11-18)

**Branch** `arena/0ce967db-own6` · **Site** `docs/nfl-0ce967db/` · **Data** `data/nfl_0ce967db/`
**Every official read in this pack is dated 2026-11-18 UTC** and logged with a clock and a hash in
`data/nfl_0ce967db/capture_log.csv`.

---

## 1. The one-paragraph version

The corpus is now **150 settled games**, reconciled **32/32 clubs** against the official standings after
this session settled the Monday game (*Chargers 23, Ravens 20*) and repaired one real data defect (the
inherited corpus used two club codes for the Rams). Six forecasters and two controls are scored by proper
score on those games. **All five registered candidates show positive point-estimate Brier skill and all
five have a negative week-cluster lower bound**, so none qualifies and the leaderboard is empty by
construction. The removal-of-luck panel then identifies *why* the models are weaker than they look: they
are miscalibrated, because the registration adds a fixed **+2.5 points** of home field in a season whose
realised home margin is **−0.53 points**. That defect is measured, published and registered for a
prospective fix — not tuned away. **Nothing is qualified, nothing is staked, no price exists, and no
profitability claim is made.**

---

## 2. What is genuinely new in this session

| # | Deliverable | The number that matters |
|---|---|---|
| 1 | **Live capture of the current slate** (Week 11, 13 games) with kickoff, network, bye clubs and event marks read from the official schedule page | 13/13 fixtures; 6 clubs on bye; one international game (Mexico City) |
| 2 | **Corpus settled and reconciled** | 150 games, 6,923 PF = 6,923 PA, 32/32 clubs match on record **and** points for **and** against |
| 3 | **First measured proper-score board in the repo** (every earlier pack publishes an empty board because no price exists) | 5 candidates × 118 scored games; best point skill **+0.098**, best lower bound **−0.066** |
| 4 | **Removal-of-luck panel** with an exact Murphy decomposition | reliability ÷ Brier ≈ **0.98** for the probability models |
| 5 | **Home-field diagnostic** that isolates the dominant error | margin MAE **10.21** at H = +2.5 versus **9.90** at H = 0 and **9.96** with a rolling H |
| 6 | **Ablations instead of penalties**, as the owner required | three run (recency, fitted home field, totals recency) — **none** has an interval excluding zero; two blocked and published as *not run* |
| 7 | **Six correlations**, each with n and a Fisher interval | only one of six excludes zero (passing yards vs points, n = 32, r = 0.708) |
| 8 | **One ledger row per owner bullet** (96 rows) with the blocking gate and the clearing number | 43 met · 24 partial · 19 blocked · 4 not run · 5 rejected-by-rule · 1 out of scope |
| 9 | **Q/I/A register** (22 questions) and a **suggestions queue** (18 proposals, none implemented) | 2 questions can only be answered by the owner |
| 10 | **Honest failure reporting** | 15 flagged items, including **two bugs in my own code** found and fixed before publication |

---

## 3. The results, with the caveats attached

| Candidate | Division | n | Brier skill | Week-cluster 95% | Sign-test p | Bonferroni (0.05/7) | Qualified |
|---|---|---|---|---|---|---|---|
| ML-SEASON (S01) | moneyline | 118 | +0.073 | [−0.081, +0.184] | 0.0012 | pass | **no** |
| ML-FITHFA (S02) | moneyline | 118 | +0.098 | [−0.066, +0.211] | 0.0006 | pass | **no** |
| ML-RECENCY (S03) | moneyline | 118 | +0.065 | [−0.118, +0.190] | 0.0041 | pass | **no** |
| TOT-SEASON (S04) | totals | 118 | — | MAE **11.58** pts | — | — | **no** |
| TOT-RECENCY (S05) | totals | 118 | — | MAE **12.02** pts | — | — | **no** |
| CONTROL-CLIMATOLOGY (C01) | control | 118 | 0.000 | by definition | 1.0 | — | — |
| CONTROL-HOME-ALWAYS (C02) | control | 118 | −1.135 | [−1.522, −0.727] | — | — | — |

**How to read it.** The point estimates look like an edge; the clustered lower bounds say the sample
cannot demonstrate one. The sign test is *not* a rescue: it treats games as independent, and the
week-cluster bootstrap exists precisely because they are not. Both are published so the disagreement is
visible instead of hidden.

**Why the models are miscalibrated, measured.** The registered constant is +2.5 points of home advantage.
The 150-game corpus shows a realised home margin of **−0.53 points** and a home-win rate of **47.3%**.
Consequence: the models forecast a mean home probability of **0.549** against a realised **0.458**.

| Home-field variant (post-hoc diagnostic) | Mean forecast P(home) | Observed | Margin MAE | Bias |
|---|---|---|---|---|
| H = +2.5 (as registered) | 0.549 | 0.458 | **10.213** | +2.697 |
| H = 0 | 0.492 | 0.458 | 9.904 | +0.197 |
| H = −0.53 (realised mean) | 0.462 | 0.458 | 9.913 | −0.333 |
| H = rolling prior-week mean (S06) | — | — | 9.961 | +0.496 |

These are **diagnostics, not candidates**. They appear in no leaderboard column and count toward no
promotion sample. The fix is registered separately as **amendment A1 (candidate S06)** and will only ever
be judged on games not yet played.

---

## 4. What the owner's brief asked for that the data cannot support — and the exact reason

| Blocked requirement | Why | The number that clears it |
|---|---|---|
| Replacement depth, 2nd/3rd/4th string | the injury hub names designations, never replacements; no depth chart read | one official depth chart per club (32/32) |
| Who actually started | no game book or starter list read | one official game book per scored game |
| Snap counts as the starter proxy | no official snap-count table read | one table per game |
| What "Questionable" means empirically | no designation was captured *before* kickoff with an inactive list to join it to | 1 season of pre-kickoff designations joined to inactive lists |
| Injury/personnel ablations | the feature block cannot be built from what was read | ≥1 played game with both a pre-kickoff designation and an inactive list |
| Price snapshots, ROI, CLV, residuals vs market | **no official page prints a price**, and a book price cannot be relabelled verified | one licensed feed whose terms permit archiving |
| Scheduled capture, past-season archives | NFL terms restrict systematic retrieval without written consent | written consent |
| Multi-season train/validation/holdout split | only 10 weeks of one season exist in the repo | 2 more seasons of official results |
| Stadium roof, surface, NWS weather | not reachable from this sandbox and not read | a reachable weather source plus an official roof/surface table |

**One gate blocks the most work:** the price/terms gate. It is the reason 6 requirements are blocked
outright and the reason no ROI can exist anywhere in the project.

---

## 5. Irregularities found (all published on the Flagged for Review page)

1. **Data defect, inherited:** `data/nfl_7a59fd89/corpus_150.csv` writes the Rams as both `LA` and
   `LAR`. Reconciliation failed for exactly one club until repaired read-only. *The source file was not
   edited;* the repair is declared in this pack.
2. **Bug in my own code, caught before publication:** totals candidates were first scored on moneyline
   Brier and duplicated the margin model's numbers. Fixed; totals are now scored on point error.
3. **Bug in my own code, caught by a plausibility check:** a league-mean unit error inflated every
   forecast total by about 23 points (MAE 24.07). Fixed; MAE is now 11.58.
4. **Bug in my own code, caught by a unit test:** the Murphy decomposition was computed over coarse bins
   and the identity failed by 0.0008. Fixed to an exact per-value decomposition.
5. **Source not published yet:** the official injury hub still serves *Week 10*; a week-11 URL redirects
   to week 10. No week-11 designation exists, and none is invented.
6. **Venue provenance is weaker than the requirement asks:** 12 of 13 stadium names come from partner
   links inside the card, not a stadium field; only one game centre was read.
7. **No raw page bytes retained:** this sandbox cannot reach nfl.com from a shell, so pages were read
   through a text-returning fetch tool. The hashes prove the transcriptions were not edited afterwards;
   they cannot prove the page said it. Stated on the site.
8. **Legal boundary:** systematic retrieval needs written consent; no consent exists.

---

## 6. The three actions that would change the most, in order

1. **Capture inactive lists on game day (SUG-06).** It converts the injury report from designations into a
   measurable play rate and is the prerequisite for the ablation the owner asked for by name.
2. **Read one official game book and publish actual starters (SUG-07).** One read settles whether starter
   data is obtainable at all before committing to 272 of them.
3. **Raise the qualification sample from the registered 100 to a full season (SUG-15).** At the measured
   effect size, 100 games is very unlikely to separate skill from luck — the published interval is the
   evidence for that recommendation.

Two of those are free. The third is a registration amendment the owner has to choose, which is why it sits
in the suggestions queue and not in the code.

---

## 7. What is *not* claimed

No edge. No profitability. No market line. No ROI. No CLV. No qualified strategy. No reward paid. No
starter, no replacement, no snap count, no depth rank, no weather value, no prop price, and no week-11
injury designation. Where those are missing, the cell is empty and the reason is written next to it.

---

## 8. Verification performed

| Check | Result |
|---|---|
| Pack verifier (`scripts/check_nfl_0ce967db.py`), 15 rules | **50 checks passed, 0 failed** |
| Pack tests (`tests/test_nfl_0ce967db.py`) | **21 tests passed** |
| Corpus reconciliation against official standings | 32/32 clubs on record, PF and PA |
| Derived artifacts reproduce byte for byte | 10/10 files |
| Site rebuild is byte-stable | 10/10 pages |
| Internal links across the whole `docs/` tree | **6,901 checked, 0 broken** |
| Input controls on any page | **0** |
| Market / ROI / CLV values published | **0** |
| CI workflow added | `.github/workflows/nfl-0ce967db-ci.yml` (rebuild → diff must be empty → verify → test) |

**Official sources used (all read 2026-11-18 UTC):**
`nfl.com/schedules/2026/by-week/week-10` · `.../week-11` · `nfl.com/standings/division/2026/reg` ·
`nfl.com/injuries/` · `nfl.com/stats/team-stats/offense/{passing,rushing,scoring}/2026/reg/all` ·
`nfl.com/games/vikings-at-49ers-2026-reg-11` · `nfl.com/legal/terms/`

See `COORDINATION.md` for the task board, the claim, the file scope and the merge record.
