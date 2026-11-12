# NFL Line Origination, Depth Deficiency & Skill-Gate Pack — Executive Summary

**Session:** `arena/3b81013c-own6` · **Snapshot:** 2026 Week 10, read on 12 November 2026
**Live dashboard:** https://sassnarep3-star.github.io/Own6/docs/nfl-3b81013c/
**Registers:** `data/nfl_3b81013c/*.csv` (12 files, 288 rows) · **Pages:** `docs/nfl-3b81013c/` (11)

---

## 1. What this pack is

A single, self-checking research pack for the 2026 Week 10 NFL slate. It does four things and refuses to do a fifth.

It **states verified NFL facts** with the exact official page each value came from. It **originates its own lines** for all 14 games by arithmetic over those facts, disclosing every assumption. It **tracks injuries and depth deficiency** down to the string a replacement came from, and blanks the value when that string is not officially stated. It **defines a leaderboard competition** with ten fail-closed gates, a fixed reward ladder and an intentionally empty ranking.

It **refuses to publish a market price, an edge, a return, a correlation or a ranked strategy**, because none of those can be established from the official information available to this repository.

### Headline numbers

| Measure | Value | Meaning |
|---|---|---|
| Register rows | 288 | Every row links to an official NFL page and a methodology reference |
| Verified facts | 122 | Stated on an official NFL page read this session |
| Computed values | 44 | Arithmetic or model output, recomputed independently by the checker |
| Unverified / blank | 122 | Rendered as hatched empty cells and listed on Flagged for Review |
| Sourced table rows on the site | 473 | Every row of every table carries an official NFL link |
| Originated Week 10 lines | 14 | Spread, total and moneyline; no market comparison |
| Starter-level injury entries | 49 | Across 12 clubs, transcribed from the official report |
| Certified correlations | 0 of 12 | Mathematical bounds published instead |
| Ranked strategies | 0 of 10 | All quarantined by at least one gate |

---

## 2. Line origination

Each Week 10 game is priced from official season scoring:

```
offence_rating[club]  = points_for / games_played − league_average
defence_rating[club]  = points_against / games_played − league_average
home_points = league_average + offence_rating[home] + defence_rating[away] + HFA/2
away_points = league_average + offence_rating[away] + defence_rating[home] − HFA/2
spread      = −(home_points − away_points)      # negative means the home side is favoured
total       = home_points + away_points
P(home win)= Φ(margin / 13.45)
```

The league average is 22.963235 points per team-game, the exact quotient of all 32 clubs' official
points scored over all team-games played.

Two inputs are **not** official and are labelled as priors everywhere they appear: home-field
advantage (1.75 points) and margin spread (13.45 points). No official NFL page publishes either. The
New England at Detroit game (15 November, 09:30 ET, Munich) is priced as a neutral site with zero
home-field advantage, per the official calendar entry.

Fourteen originated lines, two examples:

| Game | Originated line |
|---|---|
| Washington at New York Giants | spread −6.75 / total 45.07 / home ML −225 |
| New England at Detroit (neutral site) | spread −3.68 / total 51.89 / home ML −155 |

**What this is not.** It is not a market line and there is nothing to compare it to. The repository has
no licensed odds feed, and NFL.com Terms of Use section 12 prohibits using the site for wagering on NFL
games. A reader should treat the originated number as a reproducible estimate from public season
scoring, not as an edge.

---

## 3. Injuries and depth deficiency

The official Week 10 injury report supplies practice status (FP / LP / DNP) and game status for every
listed player. What it usually does **not** supply is which string the replacement came from, and that
is exactly the quantity a depth-deficiency model needs.

So the pack splits the problem in two. It records all 49 starter-level entries. It assigns a numeric
severity only where an official source states the incoming player's depth:

| Verified cascades | Club | Starter → replacement | Incoming string | Severity |
|---|---|---|---|---|
| Quarterback | MIA | Malik Willis (IR) → Kyle McCord → Brady Cook (practice squad) | 2nd | 0.4500 |
| Quarterback | AZ | Gardner Minshew (DNP) → Carson Beck (first career start) | 2nd | 0.4500 |
| Quarterback | SEA | Sam Darnold (Out) → Drew Lock (limited, ankle) | 2nd | 0.4500 |

The remaining 46 entries stay blank. That is the honest answer: stating that a starting centre was
replaced by "the backup" without an official source for the depth order would be an inferred value, and
this pack does not infer values.

Unit-level exposure is grouped by club, side and unit. The three verified quarterback cascades carry the
highest verified exposure (0.4500 each). Defensive units show many report entries but zero verified
severity, which is stated on every affected row rather than hidden by a multiplier.

Roster rules that bound who can actually dress are verified and stated: a 48-man gameday active list
requires at least eight active offensive linemen, otherwise the limit falls to 47; practice-squad
elevation is capped at two per week and three games per player per season; the inactive list is
delivered in the Game Day Administration Report 90 minutes before kickoff.

---

## 4. The leaderboard competition

Ten strategies are registered across single bets, parlays and player-prop combos. None can rank, because
ten gates stand between a hypothesis and a reward:

| Gate | Blocks | Week 10 result |
|---|---|---|
| VG-01 | Data rights and terms compliance | BLOCKED for all 10 |
| VG-02 | Pre-kickoff timestamp and T-90 minute cutoff | BLOCKED for all 10 |
| VG-03 | Strict chronological walk-forward | FAIL for all 10 |
| VG-04 | 200 events across 18 slate clusters | FAIL for all 10 |
| VG-05 | Brier or log-loss beats the de-vigged market | BLOCKED for all 10 |
| VG-06 | Positive de-vigged same-line closing value | BLOCKED for all 10 |
| VG-07 | Training-only paired-residual correlation | PASS for the 4 singles, BLOCKED for 6 combos |
| VG-08 | Holm-adjusted p and clustered ROI lower bound | BLOCKED for all 10 |
| VG-09 | Officially verified depth strings | BLOCKED for all 10 |
| VG-10 | Deterministic reproducibility | PASS for all 10 |

The reward ladder — gold research allocation, silver shadow promotion, bronze sandbox grant, quarantine
— is published **before** any result exists, so it cannot be fitted to a lucky winner. Quarantine is the
default, which puts the burden of proof on the strategy rather than on the reviewer.

**Luck control.** Four mechanisms operate together: a Holm–Bonferroni adjustment across the strategy
family, a slate-clustered bootstrap interval instead of an independent-sample interval, an out-of-sample
proper scoring rule compared against the de-vigged market, and disclosure of how many strategies were
tried. None of these eliminates randomness, and the pack says so.

---

## 5. Correlations

Twelve parlay and prop-combo pairs are registered with a stated structural direction. Every empirical
coefficient is blank, because no authorized paired-residual ledger exists.

What can be published is mathematics. At two legs each priced at a true 0.50 probability, the joint
probability can lie anywhere from 0.00 (perfectly opposed) to 0.50 (identical), with independence
sitting at 0.25 in the middle of that range. Under an illustrative Gaussian copula the joint moves from
0.1704 at correlation −0.5 to 0.3296 at +0.5. Any price built by simple multiplication is therefore
wrong in an unknown direction, and the width of that interval is the honest uncertainty.

Some pairings are definitionally redundant rather than merely correlated — a cornerback interception
prop against the team interception total — and must be excluded by rule, not corrected by a coefficient.

---

## 6. Questions that must be answered before any decision

Eighteen questions are registered: ten answered from official sources, eight open. The eight open
questions are, in priority order:

1. **What home-field advantage and margin spread should the model use?** No official page publishes
   either; both current values are declared priors. *Discover by:* fitting on authorized historical
   closing lines or play-by-play.
2. **Does the model price key numbers 3 and 7?** Not yet; it uses a continuous normal. *Discover by:*
   fitting a discrete margin distribution on authorized historical margins.
3. **Should the model use opponent-adjusted efficiency?** It currently uses raw points scored and
   allowed. *Discover by:* licensing a play-by-play feed; the package already accepts efficiency inputs.
4. **Which string did each replacement come from?** Unstated for 46 of 49 entries. *Discover by:*
   reading official club depth charts with the official transaction wire.
5. **What is the points value of losing each depth string?** Uncalibrated. *Discover by:* regressing
   realized margin on verified depth changes once play-by-play exists.
6. **What are the true pairwise correlations?** Zero paired samples. *Discover by:* building a
   training-only paired-residual ledger from authorized data.
7. **Is the 200-event floor actually powered?** It is a policy choice, not a demonstrated guarantee.
   *Discover by:* running an a-priori power calculation and publishing it.
8. **When does the inactive list become public, as distinct from its delivery to the referee?**
   Unstated officially. *Discover by:* recording the public timestamp each week.

The blocking decision in every case is the same: **data rights**. No amount of modelling closes that
gap, and NFL.com Terms of Use sections 1.3, 11(f) and 12 make the constraint explicit.

---

## 7. Site improvement suggestions

Twelve suggestions are published with effort, impact, risk and the decision their owner must make.
Eight are implemented in this pack (freshness stamps, three-state evidence labels, live gate checklists,
pre-registered reward tiers, semantic accessible tables, a Flagged for Review page, a decision-readiness
summary, and rebuild-and-diff CI). Four need an owner decision:

| # | Suggestion | Why it is proposed | Effort / impact |
|---|---|---|---|
| S-01 | One shared site-wide navigation generated from a single list | Every existing dashboard hand-maintains its own nav, so sections drift | medium / high |
| S-04 | Publish a market line beside the originated line | Without a comparison the originated line cannot support a decision | high / high, **blocked on a licence** |
| S-05 | Show the incoming replacement's depth string as a fourth value | Closes the largest gap in the depth screen | medium / high |
| S-10 | Add a root LICENSE and a separate data-rights statement | Public visibility is not a licence; repository finding A-F15 remains open | low / medium |

Three paths are laid out for a reviewer to choose between: publish only what is proven, buy the two
missing datasets, or capture depth charts manually each week. The recommended order is rights first,
then odds, then depth calibration — because a weight without a price has no decision value.

---

## 8. What is verified, and what is not

**Verified, with links on every row:** the Week 10 schedule and kickoff times; the neutral-site Munich
game; 2026 Week 10 standings for all 32 clubs; the 53-man list and 48/47 gameday rule; the 16-player
practice squad and elevation caps; the T-90 minute inactive-list delivery; the NFL important dates for
November 2026 through March 2027; the NFL.com terms on reuse, harvesting and wagering; and 49
starter-level injury entries.

**Not verified, and deliberately blank:** market prices of any kind; the incoming depth string for 46 of
49 entries; all twelve empirical correlations; the points value of any depth change; home-field advantage
and margin spread; club-level gameday active counts; and every strategy result.

No value in this pack was inferred, interpolated or copied from a secondary source. Where an official
answer did not exist, the cell is empty and the item is on the Flagged for Review page with the exact URL
a reviewer should open.

**No wagering recommendation is made anywhere in this pack**, and no claim of profitability is made or
implied.

---

## 9. Reproducing and re-verifying

```bash
python3 scripts/build_nfl_3b81013c.py     # regenerate all 11 pages
python3 scripts/check_nfl_3b81013c.py     # rebuild, diff, and recompute every number
python3 -m unittest tests.test_nfl_3b81013c -v
```

The checker re-derives the league average, all 96 per-club season-record values, all 14 originated
lines, all five pricing examples, all 34 depth-deficiency groups and every correlation bound from
independently re-entered official inputs. It fails if any page byte differs from what the builder
produces, if any unverified row carries a value, or if any table row lacks an official NFL source link.

### Official sources used (all read 12 November 2026)

- 2026 Week 10 schedule — https://www.nfl.com/schedules/2026/reg10/
- NFL standings (2026 Week 10) — https://www.nfl.com/standings/
- NFL official injury report — https://www.nfl.com/injuries/
- NFL news roundup, Wednesday 11 November 2026 — https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11
- Dolphins place QB Malik Willis on IR — https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start
- NFL.com Terms of Use (updated 16 May 2024) — https://www.nfl.com/legal/terms/
- NFL Operations, 2020 NFL–NFLPA CBA need to know — https://operations.nfl.com/inside-football-ops/players-legends/2020-nfl-nflpa-cba-need-to-know/
- NFL Operations, game and stadium preparation — https://operations.nfl.com/game-operations-logistics/preparation-safety/game-and-stadium-prep
- NFL Operations, important dates — https://operations.nfl.com/calendar-events/nfl-important-dates
- NIST/SEMATECH handbook, confidence intervals — https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm
- SciPy `scipy.stats.pearsonr` — https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html
- scikit-learn probability calibration — https://scikit-learn.org/stable/modules/calibration.html
- statsmodels `multipletests` — https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html
