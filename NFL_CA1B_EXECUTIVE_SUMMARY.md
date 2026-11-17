# NFL own-lines project — executive summary (session `ca1b3769`, 2026-11-17)

**What you asked for:** originate your own NFL lines, track injuries and depth
deficiencies, rank strategies on skill rather than luck, verify everything against
official sources, publish it as a clean site, and make no manual input necessary.

**What this session actually did:** it stopped adding features and made the sixteen
already-merged packs answerable. It re-read the official pages, said value by value
which stored numbers survive that re-read, produced the single requirement list the
project never had, originated a fair line for all 13 live fixtures, and measured what
the injury designations actually predict. Where the brief asks for something no
official source supports, the answer is **blank plus the number that would clear it**,
not a guess.

Live site: `https://sassnarep3-star.github.io/Own6/docs/nfl-ca1b/`
Data: `data/nfl_ca1b/` (31 CSVs) · Code: `src/nfl_ca1b/` (13 modules) · Pages: 19

---

## 1. The five numbers that matter

| Question | Answer today | Source |
|---|---|---|
| Does the rating model beat a coin? | Picks the winner in **66 of 101** walk-forward games (65.3%); exact-binomial **p = 0.0027**. Brier skill **0.1142**, game-bootstrap 95% CI **[−0.0069, 0.2230]** — the lower bound includes zero | `luck_panel.csv`, `backtest.html` |
| Are the results better than the probabilities imply? | No. Under the model's own probabilities the expected hits were **63.6**, not 50.5; Poisson-binomial **p = 0.674**. The results are exactly what the published probabilities imply | `luck_panel.csv` |
| Is anything rankable or bettable? | No. **0** strategies are reward-eligible; every leaderboard rank, ROI, CLV and market cell is blank because no official NFL page publishes a price | `leaderboard.csv` |
| What did "Questionable" mean in week 10? | **80.4%** played (n = 56, 95% CI 68.2–88.7). Doubtful 50.0% (n = 6). Out 27.1% "played" — see the caveat in §4. Blank 96.7% (n = 91) | `designation_calibration.csv` |
| Can the repo's stored numbers be trusted? | **971** stored values re-tested against today's official pages; **0 contradictions**. 288/288 comparable standings club-rows and 625 joined result rows reconcile | `verification_standings.csv`, `verification_results.csv` |

## 2. The highest-value finding: the model was overconfident, and it is fixed visibly

In-sample and walk-forward, the raw model's top band (80–100%) forecast **0.895** and
observed **0.636** over 22 games. That is the classic failure mode: a normal
approximation that understates variance in the tails.

The fix is not hidden. A multiplier `k` on the margin standard deviation is chosen
**inside** the walk-forward loop, on games strictly older than the one being predicted
(median `k` = 1.8). It is printed on every published row, and the resulting band is
0.839 predicted vs 1.000 observed on 8 games — better, but the honest note is that 8
games prove nothing.

**Consequence for the site:** the *spread* comes from the margin equation, the
*probability* comes from the calibrated variance. They are deliberately not a matched
pair, and the page says so, because forcing them to agree would reintroduce the
overconfidence that was just measured.

## 3. Convergence: 342 requirement rows were hiding 210 requirements

Six merged packs each publish a requirement table — 73, 74, 79, 15, 20 and 81 rows.
They use **25 different status words** for the same idea, and the same brief sentence
appears up to **four times** under different IDs.

This session collapses them into one register of **210 distinct requirements**
(99 delivered, 59 open, 46 blocked, 5 unstated, 1 rejected by policy). Where packs
disagree on status, the register reports the **worst** status, so nothing looks
delivered because one pack said so.

## 4. Availability and depth, stated honestly

**What was confirmed.** The official week-10 inactives article was read and 147
inactive lines for 24 clubs transcribed. Every designation row on the injury hub was
joined to that list **by exact name** (generational suffixes only), and the play rate
per designation is published with a Wilson interval.

The `Out` play rate of 27.1% needs its caveat in the same breath: 13 of the 48 `Out`
rows did not join the inactive list at all (no fuzzy matching was allowed), so the
denominator is the joinable subset, not every `Out` designation. The names are
listed on the site so the miss can be inspected rather than assumed away.

**What cannot be confirmed, and why.** The brief asks for depth — 1st string, 2nd
string, who replaced whom. On 2026-11-17:

* `https://www.nfl.com/teams/houston-texans/depth-chart` returns **404 "Flag on the
  Play"** (probe P-01). The route the project has been planning against does not exist.
* No official snap-count table was reachable (G-SNAP).
* The game-centre injury module for the week-11 opener reads "Injury Report is not
  available at this time" for both clubs (probe P-02).

So this pack publishes **no depth rank at all**: not from jersey number, not from
salary, not from experience, not from a hand-read image. The per-team view counts
designations and confirmed inactives and leaves "starters out", "replacements named"
and "net injury count" blank, each with the sentence that explains why.

## 5. Venues: a conflict that turned out to be two official surfaces

All 13 week-11 fixtures now carry a venue. Two official surfaces disagree on three
stadium names — the schedule card's hotel deep-link says **NRG Stadium**,
**FedEx Field** and **GEHA Field at Arrowhead Stadium**, while the game-centre Game
Info block says **RELIANT STADIUM** (re-read this session), **Northwest Stadium** and
**Arrowhead Stadium** (both as reported by a sibling pack).

Neither string is wrong. Both are published, each labelled by the surface that carries
it. For MIN @ SF the schedule card has no hotel link at all, so only the game centre
supplies a venue (**ESTADIO BANORTE**, Mexico City).

## 6. The decision the project cannot make for you

Two gates block almost everything:

* **A price.** No official NFL page publishes one. Until a licensed archive exists,
  every market column, residual, ROI, CLV and staking test is blank, and origination
  can only be compared with a blank.
* **The retrieval terms.** NFL.com's Terms of Use restrict systematic retrieval. Every
  capture in this repo is a single manual read with a clock time. No scheduled capture
  was built, because building one would be a decision about the terms, not about code.

Every other open item is on the site with the number that would clear it.

## 7. What is published, and where

| Page | What it answers |
|---|---|
| `decision.html` | One row per requirement: gate that blocks it, number that clears it |
| `lines.html` | Fair spread, total and moneyline for 13 fixtures, with the full input vector |
| `signal.html` | Proper scores, three controls, exact binomial + Poisson-binomial tests, calibration, 5 correlations with n |
| `backtest.html` | The 101-game walk-forward, **kept off the leaderboard on purpose** |
| `leaderboard.html` | 5 pre-registered strategies with rule hashes, signal vs staking, 5 demotion gates |
| `availability.html` | What each designation actually meant, joined to official inactives |
| `injuries.html` | Two dated reads of the same page, differenced player by player |
| `depth.html` | Why no depth rank can be published, and the 32-club sweep status |
| `venues.html` | Both official surfaces per fixture, disagreements left visible |
| `verify.html` | 971 stored values re-tested, line by line |
| `conflicts.html` | 9 cases where two packs publish different values for the same fact |
| `snapshots.html` | Hash-chained point-in-time ledger |
| `freshness.html` | Which dataset has been overtaken by its source |
| `requirements.html` | The single register of 210 requirements |
| `qia.html` | 10 decisions that are unreachable, with what would settle each |
| `suggestions.html` | 11 suggestions ranked for your choice — **none implemented** |
| `flagged.html` | Everything unverified or irregular, each with its official link |
| `sources.html` | All 8 pages read, with clock times, plus the 3 probes that returned nothing |

## 8. What this session did **not** do

* It did not invent a price, a rank, a depth chart, a starter, or a replacement.
* It did not automate any capture (that is the owner's terms decision, Q-01).
* It did not claim profitability anywhere, and it did not delete or relabel any earlier
  pack's work — every one of those packs is still live, and this pack sits beside them.
