# NFL Week Pack — Executive Summary

**Session:** `arena/0a988733-own6` · **Built:** 2026-11-13 · **Site:** `docs/nfl-wk/` · **Data:** `data/nfl_wk/`

---

## 1. What this pack is

A zero-manual-input NFL research dashboard built only from official sources, with every table row linked to the page it came from. It covers the **current official week** — nfl.com labels 12–16 November 2026 as **Week 10** (schedule URL `/schedules/2026/by-week/week-10`, injury page title *"Week 10 of the 2026 Season"*) — and lists Week 11 (19–23 November) separately.

It exists to answer four questions honestly: what do we actually know, what can we compute from it, what does the competition require before a strategy may be ranked, and what is missing before any real decision can be made.

## 2. The single most important finding

**There is no licensed market price anywhere in this repository.** Without a timestamped price there is no edge, no closing-line value, no return on investment and no defensible ranking. Every one of those cells is blank, and the build **fails** if a number appears in one. This is not a shortcoming of the analysis; it is the analysis.

A close second: **NFL.com Terms §1.3** (read 2026-11-13) limits use to *"individual non-commercial and informational purposes"* and prohibits *"systematic retrieval of data … to create or compile … a collection, compilation, database"* without express prior written consent. No consent or licence is on file. Every strategy in this pack is therefore downstream of a legal question that only you can settle.

## 3. What is verified

| Item | Count | Source | Verification performed |
|---|---|---|---|
| Club standings rows | 32 | [nfl.com/standings](https://www.nfl.com/standings/) | Five league identities checked: ΣW = ΣL = 136, ties = 2, ΣPF = ΣPA = 6,291, home wins = road losses, per-club W+L+T = home+road |
| Slate fixtures | 27 | [Week 10](https://www.nfl.com/schedules/2026/by-week/week-10) · [Week 11](https://www.nfl.com/schedules/2026/by-week/week-11) | 14 + 13 games, kickoff times, broadcasters, venue notes, records cross-checked against standings |
| Injury-report rows | 326 | [nfl.com/injuries](https://www.nfl.com/injuries/) | All eight page chunks read; 14 games; 28 clubs; every row carries the source URL |
| Club depth charts | 14 charts / 12 clubs on the report | Official club sites (AZ, BAL, CHI, DET, GB, IND, KC, LV, MIA, MIN, NE, PIT, SEA, TB) | Full chart transcribed; ordering and slot verified per player; 2 charts carry an explicit date |
| Registered sources | 32 | Registry in `data/nfl_wk/sources.csv` | Each with read date, verbatim excerpt, and an explicit "does not support" column |

## 4. What is computed (and is therefore *not* an NFL statistic)

| Output | Method | Why it is labelled "computed" |
|---|---|---|
| Own total per game | Mean of both clubs' points-for and points-against per game | Our arithmetic on official inputs |
| Own home spread | `((hPF + aPA) − (aPF + hPA)) / 2` | No home-field term, no opponent adjustment |
| Home win probability | `Φ(spread / 5.9044)` | The 5.9044 is a **model assumption**, derived as √2 × the club scoring SD (FLAG-12) |
| Fair American price | Fair odds for that probability, zero margin | No market to compare against |
| Depth deficiency | **Counts only** — first-string players ruled Out/Questionable, split by offence and defence | No official metric converts a lost starter into points, so the score column is blank (FLAG-11) |

## 5. What the injury and depth work shows

The join between the league's injury report and the clubs' own depth charts is the most useful new artefact here. Twelve clubs' charts were read (Arizona, Baltimore, Chicago, Detroit, Green Bay, Indianapolis, Kansas City, Las Vegas, Miami, Minnesota, New England, Pittsburgh, Seattle and Tampa Bay; fourteen charts, twelve of which have a player on the Week 10 report). Across them:

- **7 first-string players are ruled Out** (3 offence, 4 defence) and **3 are Questionable** (2 offence, 1 defence).
- The clearest replacement chain is at **centre**: Detroit's Cade Mays (1st-string C on the Lions' own chart) is ruled Out, and the chart lists Juice Scruggs directly behind him. New England's Ben Brown (1st-string LG, 2nd-string C) is also ruled Out.
- **Two clubs list a quarterback other than the presumed Week-1 starter** on their own chart, and the charts give **no reason**: Baltimore lists Jacoby Brissett 1st with Lamar Jackson absent from the chart entirely, and Philadelphia lists Tanner McKee 1st. Whether that reflects injury, a coaching decision or a chart that is out of date is unknown, so this pack asserts none of it. Separately, Seattle's own chart still lists Sam Darnold 1st and Drew Lock 2nd, while an NFL.com headline from this week says Darnold was *ruled out* for the Week 10 game — the chart and the news disagree, which is itself recorded as a data-quality problem.
- **16 of 28 clubs remain blank.** No chart was read for them in this session, so their cells say nothing rather than zero. Houston's page serves its chart as an image and could not be transcribed.

### 5a. The 3rd-string case, isolated

The brief singles out situations where a 2nd/3rd/4th-string backup replaces a starter. That only happens when the men *in front* are unavailable too, so the pack tests for it mechanically: **both** of the two shallowest slots a club's own chart lists at a position must carry a Week 10 status of Out or Questionable. Three position groups pass that test, all at New England:

| Club | Group | 1st on chart | Status | 2nd on chart | Status | Next listed |
|---|---|---|---|---|---|---|
| NE | LG | Ben Brown | Out | Walter Rouse | Questionable | none — not identifiable |
| NE | RB | Rhamondre Stevenson | Questionable | TreVeyon Henderson | Out | none — not identifiable |
| NE | S | Kevin Byard | Questionable | Brenden Schooler (3rd on chart; 2nd slot empty) | Questionable | none — not identifiable |

In all three cases the club's own chart does not list a third name at the position, so the replacement cannot be identified from the official pages read here. The pack records **"not identifiable"** rather than assuming a promotion from elsewhere on the roster. This is the honest answer to the brief's question and it is a gap in the official sources, not in the method.

Three genuine irregularities surfaced and are published rather than smoothed over:

1. **The official injury-policy URLs are dead.** `operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf` and `operations.nfl.com/the-rules/nfl-injury-report-policy/` both return a 404 page titled *"FLAG ON THE PLAY"* (FLAG-04). Earlier sessions cited the first URL as verified. The widely repeated "90-minute inactive list" deadline is therefore **not** asserted from an official source here.
2. **The two official sources disagree on player names.** Matthew/Matt Hibner, Olaivavega/Vega Ioane, A.J./AJ Haulcy and Drew/Andrew Ogletree (FLAG-08). Matches are made through a documented alias list, never fuzzy matching.
3. **Six injured players are absent from their club's chart** — including Kerby Joseph, who is ruled **Out** (FLAG-09). Their depth string is unknown, so they are excluded from the deficiency counts rather than assumed to be backups.

## 6. The competition design

Eleven preregistered hypotheses — 5 singles, 3 parlays, 3 player-prop combinations — each with an exact signal rule and a named data requirement. Twelve fail-closed gates sit in front of them. Today **11 of 12 gates are blocked**; the only one that passes is pre-registration, because the register was committed to git before any observation existed.

Rewards are **research units, not money**: Tier 0 (0), Tier 1 (1), Tier 2 (3), Tier 3 (6), Tier 4 (10). Nothing has been awarded, because nothing has passed.

The leaderboard is empty and says so at the top of the page.

## 7. Luck removal

The pack specifies the test rather than pretending to have run it:

- **Closing-line value** replaces ROI as the primary skill signal, because it isolates whether the model beat the market from whether the ball bounced.
- **Brier skill score** against a baseline separates calibration from luck.
- **Pre-registered multiplicity correction** stops "best of eleven" from looking like skill.
- **Walk-forward splits** stop the model from seeing its own test weeks.
- **Roster-identity down-weighting** (`effective_half_life` in `src/nfl_wk/model.py`) stops season-long rates being applied to a roster that no longer exists.

Every one of these has a gate and none has a number, because a number would require the licensed history we do not have (FLAG-05).

## 8. The 22 questions that gate every decision

Fourteen are **BLOCKED** on information we lack, seven are **OPEN** owner decisions, one is **RESOLVED** (week numbering). The five that unblock the most:

1. **Q-01** — obtain written consent or a licence for analytics and database construction.
2. **Q-03** — obtain a timestamped closing-line archive.
3. **Q-07** — obtain dated depth charts (every club chart calls itself "unofficial").
4. **Q-11** — obtain paired outcome history for the eight registered dependence pairs.
5. **Q-12** — replace the asserted 200-bet floor with a derived one.

## 9. The suggestions section you asked for

Nineteen proposals on `docs/nfl-wk/suggestions.html`, each with the problem it solves, effort, impact, **risk if adopted**, what a decision owner still needs, and an **empty decision column**. Six are already implemented because they cost nothing and improved the evidence; thirteen await your choice. Grouped by what the decision actually requires: money or a licence, agreement with another session, or your call alone.

My recommendation, stated as a recommendation: settle Q-01 and Q-03 before any of the nineteen. The rest improve how clearly the absence of data is presented; they cannot substitute for the data.

## 10. Flagged for review (16 items, none blocking)

Five high: no licence (F-01), no market price (F-02), no correlation coefficients (F-03), dead official injury-policy URLs (F-04), luck test uncomputable (F-05). Full register with sources on `docs/nfl-wk/flagged.html`.

## 11. How to reproduce and verify

```bash
python3 scripts/build_nfl_wk.py     # regenerate all CSVs and all 13 pages
python3 scripts/check_nfl_wk.py     # 0 broken links, 0 input elements, 0 invented values, deterministic
python3 -m unittest tests.test_nfl_wk -v   # 46 tests
```

The checker fails the build if a market price, an ROI figure or a correlation coefficient appears anywhere, if any gate other than pre-registration passes, if a league identity breaks, or if two consecutive builds differ by a byte.

## 12. Bottom line

The verified layer is solid and internally consistent. The analytical layer is a transparent baseline, not a forecast. The competitive layer is designed, gated and empty. **No strategy can be recommended, ranked or rewarded until a licence and a price archive exist** — and the site is built so that this limitation is impossible to miss rather than buried in a footnote.
