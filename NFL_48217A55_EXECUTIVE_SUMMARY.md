# NFL Decision-Readiness Pack — Session `arena/48217a55-own6`

**Capture date:** 2026-11-15 (Week 10 of the 2026 season, captured while games were still
finishing) · **Branch:** `arena/48217a55-own6` · **Base commit:** `32a1b692`

Live pages: <https://sassnarep3-star.github.io/Own6/docs/nfl-48217a55/>

---

## 1. What this pack is

A line-by-line reading of the official NFL pages, published as tables in which **every row
carries a source link and every blank cell carries a flag**. It was built to answer one
question the brief keeps asking in different words: *what would have to be true before a
decision here is reasonable?*

The answer is published as a row-per-requirement table — 74 requirements, each with the gate
that blocks it and the number that would clear it — on the
[decision-readiness page](docs/nfl-48217a55/decision-readiness.html).

Nine official pages were read on 2026-11-15. Nothing else was used. No price was estimated,
no replacement was inferred, and no strategy was ranked.

| Artifact | Count |
|---|---|
| Official sources read (with clock times) | 9 |
| Published CSV tables | 36 |
| Published pages | 18 |
| Verifier checks | 115, all passing |
| Unit tests | 59, all passing |
| Blank cells, every one traced to a flag or an expected-blank reason | 1,054 |

---

## 2. Executive summary — the important details

### What is true now

- **The full Week 10 injury report was captured**: 347 rows across the 28 clubs playing this
  week. 70 players are designated Out, 90 Questionable, 11 Doubtful, and 176 carry no game
  status at all. Those 176 are *not* available — they are unclassified, and the pack
  publishes them as blank rather than as clearances.
- **Four clubs are on bye** (CHI, DEN, PHI, TB) and have no section on the report. Their
  absence is published as a bye, never as health. This is the single easiest way to misread
  this page and the pack refuses to do it.
- **Week 10 was still being played at capture time.** Nine of fourteen games had gone final;
  three were in progress and two had not kicked off. Only the nine finals enter the results
  feed. The in-progress scores are published in a separate table, plainly marked, and are
  never used as results.
- **The standings page is a live table and that is handled, not ignored.** It already
  contained the nine completed Week 10 games. The through-Week-9 table was reconstructed by
  subtracting those games, then checked against an independent official page that printed
  each club's record before kickoff: **10 of 10 matched**. League points for equal points
  against (6,246 = 6,246), wins equal losses, and the implied completed-game count is
  **136** — the 136-game corpus the brief refers to, confirmed arithmetically rather than
  assumed.
- **The reserve list closes the "not listed means available" hole.** 25 November
  Reserve/Injured moves were captured; 10 of those players also appear on the Week 10 report.
  The rest are absent from the report *because they are on a reserve list*.
- **Five named starters are published, and only five** — Lock (SEA), Watson (CLE), Beck (AZ),
  McCord (MIA), and the second Lock confirmation. Each carries the official page that names
  him. No replacement is inferred anywhere.
- **Luck is quantified before any skill claim.** 51.8% of the win-percentage spread across
  the 32 clubs is what a fair coin flip would produce over the same games. Any model
  claiming to explain the standings has to beat that, not merely correlate with it.

### What is blocked, and by what

**33 of the 74 requirements are blocked**, and nearly all of them trace to three missing
inputs:

| Missing input | What the official pages actually do |
|---|---|
| **Operator prices** | No official page publishes a spread, total or moneyline. Every route tried is logged with what the page contained. |
| **A depth order** | `nfl.com/teams/<club>/depth-chart` returns **HTTP 404**. The roster route is live but publishes no depth order; it links a depth chart on the club's own domain, unverified for the other 31 clubs. |
| **Snap counts** | No official source found. The roster page publishes status codes (ACT/RES/DEV/CUT/PUP/TRD) and nothing else. |

Because of those three, the depth-of-replacement feature **is not built**. This is a
deliberate answer to the brief's instruction to resolve the depth-order source *before*
building it: route (a) was evaluated first and returned 404, route (b) found no source, so
the feature waits. What is published instead is **floors** — how many Out rows sit in each
club and unit — with the replacement column left empty.

### Numbers a reviewer can check in one step each

| Check | Result |
|---|---|
| Injury rows / clubs on the report | 347 / 28 (+4 byes = 32) |
| Out / Questionable / Doubtful / no status | 70 / 90 / 11 / 176 |
| Standings checks that matched the official pregame page | 10 of 10 |
| League points for vs points against | 6,246 = 6,246 |
| Completed games through Week 9 | 136 |
| Luck share of the win-percentage spread | 0.518 |
| League points per game | 23.01 |
| Qualified strategies | 0 |
| Gates passing | 1 of 12 (the drift alarm) |
| Correlations measured / excluded with reasons | 6 / 5 |

---

## 3. Irregularities flagged for review

Full list with source links on the
[Flagged for review page](docs/nfl-48217a55/flagged.html). The ones worth reading first:

1. **The reserve-list route may be truncated.** Its earliest November row is dated 11/07, but
   an official NFL.com story dated 2026-11-05 reports the Ravens placing Lamar Jackson on
   injured reserve with no corresponding row. (`48217-F15`)
2. **Club attribution on the injury report looks wrong until you check it.** Kenneth Walker
   III appears under Kansas City. Reading the Kansas City roster confirms he is on it. One
   row checked end to end and it held; the other 346 are unchecked. (`48217-F13`)
3. **The by-week schedule page prints no venue**, so Week 10 venues are blank. The
   *inactives* page does print `WHERE`, and 13 Week 9 venues were transcribed from it.
   (`48217-F07`)
4. **The injury page was served in eight chunks** and transcribed by hand. Chunk 0 was
   re-read and diffed field-for-field: all 44 WAS/NYG/NE/DET rows match exactly, confirming
   both the transcription and the `chunks 0-7` claim. Chunks 1–7 were not re-read, so their
   completeness rests on the surname-ordering check — consistent with nothing being lost, but
   a consistency check rather than a proof. (`48217-F14`, partially closed)
5. **Eight overlapping NFL packs now exist in this repository**, and nothing tells a reader
   which is authoritative. The decision-readiness table is this pack's answer to that.
   (`RF-10`)

---

## 4. Answers to the brief's structural questions

### "One row per requirement, with the gate that blocks it and the number that would clear it"

Published: [decision-readiness.html](docs/nfl-48217a55/decision-readiness.html) — 74 rows,
grouped by category, each with *what is published today*, *blocking gate*, *number that
would clear it*, *evidence file* and *source*. 23 cleared, 15 partial, 33 blocked, 2
rejected, 1 needs review.

### "A clear list of questions, information and answers needed before any decision"

Published: [questions.html](docs/nfl-48217a55/questions.html) — 18 questions. Each names the
**decision it blocks**, **what we have**, **what is missing**, and a **discovery path** that
can actually be walked. The three that unblock the most:

- **Q01/Q02** — where prices come from, and whether their use is permitted. Everything about
  origination, residuals, CLV and ROI sits behind this, and it is an owner decision, not a
  scraping task.
- **Q03** — can the game-by-game log for Weeks 1–9 be obtained? Without it, ratings cannot
  be opponent-aware and there is no backtest corpus.
- **Q04** — which official source publishes a depth order, verified for all 32 clubs?

### "A suggestions section so someone can review and choose the best path"

Published: [suggestions.html](docs/nfl-48217a55/suggestions.html) — 16 suggestions, each with
**options A / B / C** and the **cost of doing nothing**. Nothing is applied automatically;
the page exists so a choice is made first. A is the full version, B buys most of the value at
a fraction of the work, C declines deliberately and leaves the gate open on the record.

### "Remove luck from the equation"

Published: [luck.html](docs/nfl-48217a55/luck.html). The league-level number is measured
(**0.518**). The strategy-level number is blank and flagged: it needs 100 prospective graded
forecasts, and there are zero. It is not estimated.

### "Determine correlation values"

Published: [correlations.html](docs/nfl-48217a55/correlations.html). Six measured, each with
n, unit, method, a 95% interval, a p-value and one official URL per axis. **Every interval
straddles zero or rests on a sample far too small to decide anything — that is the finding.**
Five further candidates are published as *exclusions* with the reason and the number that
would clear them, rather than being estimated from the wrong data.

A first calibration of "Questionable" is published too: 10 of 11 definite resolutions were
active, Wilson interval [0.59, 0.99], with the warning that the sample is **not random** — it
is the set of players NFL.com chose to write about, which skews to starters and to genuinely
doubtful cases. The label is marked unusable as a feature until 200 pairs exist.

---

## 5. Governance decisions this pack enforces

| Decision | How it is enforced |
|---|---|
| No backtest number ever reaches the leaderboard | The leaderboard schema has no backtest column; all five divisions report 0 ranked |
| Combos wait for joint evidence | Parlay, same-game parlay and prop-combo strategies all have `G10` as a required gate and an evaluation window recorded as *not opened* |
| Controls always run | Two control strategies (favourites only, uniform random) are registered and can never be promoted |
| Rewards are never monetary | All four tiers record `monetary: none` |
| Pre-registration is real | Nine strategy definitions are frozen in `src/nfl_48217a55/gates.py` before their windows open; the commit is the registration |
| A blank is never silent | 1,054 blank cells, each traceable to one of 17 flags or to a declared expected-blank reason |
| Drift fails loudly | The verifier pins row counts and required fields for every table and exits non-zero on any change (gate G12, the one gate that passes) |

---

## 6. Sources

All nine were read on 2026-11-15; the full register with clock times and chunk ranges is on
[sources.html](docs/nfl-48217a55/sources.html).

| ID | Page | What it supports |
|---|---|---|
| S1 | <https://www.nfl.com/injuries/> | Week 10 injury report, all 347 rows |
| S2 | <https://www.nfl.com/schedules/2026/by-week/week-10> | 14 fixtures, kickoffs, networks, finals, bye panel |
| S3 | <https://www.nfl.com/standings/division/2026/reg> | 32 clubs: W/L/T, PF/PA, splits |
| S4 | <https://www.nfl.com/news/week-10-injuries-sunday-pregame-2026-nfl-season> | Active/inactive resolutions and pre-kickoff records |
| S5 | <https://www.nfl.com/news/nfl-week-9-inactives-players-ruled-out-sunday-2026-season> | 13 official inactive lists and venues |
| S6 | <https://www.nfl.com/transactions/> | 12 November trades |
| S7 | <https://www.nfl.com/transactions/league/reserve-list/2026/11> | 25 Reserve/Injured moves |
| S8 | <https://www.nfl.com/teams/kansas-city-chiefs/roster> | Roster route, status codes, club-hosted depth link |
| S9 | <https://www.nfl.com/teams/kansas-city-chiefs/depth-chart> | Route probe: HTTP 404 |

---

## 7. Reproduce

```sh
python3 scripts/build_nfl_48217a55.py             # write 36 CSVs and 18 pages
python3 scripts/check_nfl_48217a55.py             # 115 checks
python3 -m unittest discover -s tests -p "test_nfl_48217a55.py" -v   # 59 tests
```

The builder takes no arguments and touches no network, so a re-run reproduces
**byte-identical** files. That property is what makes the published tables auditable: they
are exactly what the code computes from the captured values, and a test asserts it.

---

## 8. Boundaries

- **Nothing here demonstrates a profitable NFL edge.** No strategy is qualified; none has a
  single prospective forecast.
- **No market price appears anywhere in this pack.** Where a price would go, the cell is
  blank and flagged `48217-F01`.
- **A blank cell is never zero and never a clearance.** It is an empty cell with a reason on
  the [Flagged for review](docs/nfl-48217a55/flagged.html) page.
- **The capture is a snapshot, not a feed.** It was taken while Week 10 was being played.
  Re-reading the official pages later will give different numbers, and that is expected.
