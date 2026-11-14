# NFL Decision Pack — Executive Summary (session arena/6cefc476-own6, 2026-11-14)

**Live page:** https://sassnarep3-star.github.io/Own6/docs/nfl-6cefc476/
**Evidence policy:** every value traces to an official page read on 2026-11-14; unverifiable values are
published **blank and flagged**, never inferred. Model outputs are computations, not market prices.
**Nothing in this pack demonstrates a profitable edge.**

## What was built (requirements → deliverables)

| Requirement | Deliverable | State |
|---|---|---|
| Price-snapshot store recording opening and closing numbers for every market we originate | `data/nfl_6cefc476/price_snapshots.csv` — 156 rows: one **open** + one **close** row for each of the 78 originated markets | Opens captured 2026-11-14; closes provisioned, blank, `pending_close` (flag N6F-02). Market numbers blank (no licensed source, N6F-04) |
| Verified results feed so backtests and ROI can be computed | `results_feed.csv` — 16 finals verified from official nfl.com game pages (Week 9 × 15 + WAS 24 @ NYG 21) + `backtest_grades.csv` settlement demonstration | Settlement machinery demonstrated (15 retrospective grades). Honest ROI/CLV blank until prices exist |
| Originate the side first, then the total, then the moneyline | `originated_lines.csv` — wave 1 side (26), wave 2 total (26), wave 3 moneyline (26); checker enforces order | Done; enforced in CI |
| Publish the model's fair line, the market line, and the difference as separate columns | `model_fair_line`, `market_line`, `line_difference` columns on every row | Fair lines computed; market/difference **blank + flagged** (VG-02) — never filled |
| Separate 'signal' from 'staking' in the leaderboard | `leaderboard.csv` — separate signal and staking columns/ranks; `staking_can_escalate_signal = no` pinned | Done; all 6 strategies unqualified (n below the 200 floor) |
| Track the depth of the replacement, not just the fact | `replacement_depth.csv` — 72 events; `depth_of_replacement` (string level) + `replacement_step` | 16 events carry verified strings (NE/DET/SEA/MIN/BAL charts); the rest blank + flagged N6F-08 |
| Compute correlations only from officially sourced numbers and publish n with each value | `correlations.csv` — 6 measured values (n=32 ×3, n=15 ×2, phi n=15) each with n, p, Fisher-z CI; 3 blocked rows n=0 | Done; blocked rows stay blank (N6F-11) |
| Define a demotion gate that sends a live strategy back to paper | `demotion_gate.csv` DG-01…DG-06 with LIVE → PAPER actions; state machine documented | Done; DG-04/DG-05 evaluable today, the rest arm with the price archive |
| Suggestions section for review before changes | `suggestions.html` + `suggestions.csv` — 12 suggestions, options + recommended path, all `pending_human_choice` | Done |
| Clear list of questions / information / answers, and discovery of missing information | `questions.html` + `decision_questions.csv` — 18 questions: answered / partial / missing, each with a discovery protocol | Done |
| Injury tracking with backup-depth deficiencies (offense + defense) | `replacement_depth.csv` covers Out/Doubtful for all 14 Week 10 games, offense and defense, strings 2/3/4 | Done within the read scope |
| Executive summary | This document + `executive-summary.html` | Done |

## Verified facts (with sources)

- **2026 standings through Week 10 TNF** (32 clubs, read 2026-11-14): league totals W=136, L=136, T=2,
  PF=PA (reconciled in build). https://www.nfl.com/standings/
- **Week 9 results** (15 finals) and **W10-01** (WAS 24 @ NYG 21). https://www.nfl.com/scores/2026/week-9
- **Week 10 slate** (14 games; byes CHI/DEN/PHI/TB) and **Week 11 slate** (13 games; byes ATL/CLE/GB/LAR/NE/SEA).
  https://www.nfl.com/schedules/2026/by-week/week-11
- **Week 10 injury report** (all 14 games' Out/Doubtful designations). https://www.nfl.com/injuries/
- **Replacement-depth headline cases:** SEA QB1 Darnold Out → QB2 Drew Lock (news-confirmed starter);
  MIN QB1 Murray Out → QB2 Carson Wentz (chart QB3 Brosmer, QB4 Cousins); NE RB2 Henderson Out/IR →
  RB3 Corey Kiner (RB1 Stevenson Questionable → conditional two-string drop); DET C1 Mays → C2 Scruggs,
  CB1 Reed → CB2 Ya-Sin; NE CB1 Davis III → CB2 Canada; BAL SS1 Hawkins → SS2 Keondre Jackson.

## Decision state (read before any decision)

1. **0 qualified strategies; no rewards.** The competition framework is live; qualification requires
   200 graded selections (VG-06) and chronological out-of-sample testing (VG-07).
2. **No market prices exist here.** market_line / line_difference / ROI / CLV are blank by policy.
3. **Model parameters are uncalibrated:** HFA = 0.000 (flag N6F-03); σ = 14.705 points from n=15
   Week 9 margins. Fair lines are model numbers, not quotes.
4. **Blocking unknowns:** licensed odds archive (Q01), close captures (N6F-02), official player-prop
   results feed (Q10), pre-event depth strings where charts moved on (N6F-05).
5. **Rights:** NFL.com terms restrict systematic retrieval and permit individual non-commercial
   informational use (flag N6F-01). Keep this project non-commercial.

## Irregularities flagged (14 items, full list on the Flagged page)

High severity: N6F-01 (rights boundary), N6F-02 (closes pending), N6F-04 (no market prices),
N6F-11 (parlay/prop correlations blocked). Medium: N6F-03 (uncalibrated parameters), N6F-05/06/07
(depth unverifiable in three specific cases), N6F-08 (56 events without chart strings), N6F-09
(retrospective grades are in-sample), N6F-12 (**two official nfl.com headlines disagree on Lamar
Jackson's absence window: 6-10 vs 6-9 weeks** — for human review).

## Repo review findings (8 items)

Cross-session requests **R1** (broken rules URL in `data/nfl/sources.csv`) and **R4**
(`scripts/source_coverage.py` PUBLISHERS allowlist lacks NFL domains) were re-checked in the tree and
remain open. Full register: `audit/NFL_6CEFC476_REPO_REVIEW.md` and the repo-review page.

## Recommended next actions (owner decisions — see Suggestions page)

1. Choose the price-archive path (N6CF-S02) — ROI/CLV/market columns unblock behind it.
2. Approve automated close capture (N6CF-S03) so the snapshot store fills with no manual work.
3. Approve the depth-chart backfill session (N6CF-S04) to clear N6F-08.

*Sources for every row: `data/nfl_6cefc476/sources.csv` (17 reads with evidence boundaries).*
