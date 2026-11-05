# Session 27fdbe09 — line-by-line verification record, 5 November 2026

Branch: `arena/27fdbe09-own6` · Base at claim: `33165a0` · Session claims W1–W4 in `COORDINATION.md`.

This file records exactly what was read from which official page, what was computed, and what
remains unverified. It is written so a reviewer can repeat each step. Nothing in this file is
inferred: every factual cell below appears on the linked page, and every derived number is
reproducible from committed code and committed CSV input.

---

## 1. Official pages read in this session

| ID | Page | URL | Read (UTC date) | Used for | Result |
|---|---|---|---|---|---|
| S1 | NBA.com standings, 2026-27 | https://www.nba.com/standings | 2026-11-05 | 30 team records, seeds, win%, games behind | 30 rows copied (East 15, West 15). Sum of wins 121 = sum of losses 121 |
| S2 | NBA.com games, 4 Nov 2026 | https://www.nba.com/games?date=2026-11-04 | 2026-11-05 | 14 final scores, OT flags, game IDs, club records on the cards | 14 games read across 3 page chunks |
| S3 | NBA.com game page ORL @ PHX (0022600187) | https://www.nba.com/game/orl-vs-phx-0022600187 | 2026-11-05 | 5–6 Nov slate: tip times, IDs, NBA Cup group labels, records | 2 + 9 upcoming games listed |
| S4 | NBA Terms of Use | https://www.nba.com/termsofuse | 2026-11-05 | Rights boundary; §1 and §9(i)–(vii) | Text read in chunks 0, 3, 4 |
| S5 | NBA Stats FAQ | https://www.nba.com/stats/help/faq | 2026-11-05 | Download/copy limits | "not available for download for either academic or personal use" |

Quoted passages (verbatim from the pages above):

- S4 §9, opening sentence: *"By using such NBA Statistics, you agree that: (i) any use, display, or
  publication of the NBA Statistics shall include a prominent attribution to NBA.com … (ii) the NBA
  Statistics may only be used, displayed, or published for legitimate news reporting or private,
  non-commercial purposes; (iii) the NBA Statistics may not be used in connection with any
  sponsorship or commercial identification; (iv) the NBA Statistics may not be used in connection
  with any gambling activity (including legal gambling activity); …"* — read on 2026-11-05.
- S4 §1: *"No Basketball Content from the Services may be reproduced, republished, uploaded, posted,
  modified, reused, transmitted, reproduced, distributed, copied, publicly displayed, linked to, or
  otherwise used except as provided in these Terms of Use without the written permission of the
  Operator."*
- S5: *"Our stats are not available for download for either academic or personal use. They are for
  viewing and enjoying on NBA.com/Stats"*.

---

## 2. Standings rows — 30 of 30 checked

Each row below was copied from S1 and then re-checked twice: (a) arithmetic — the 30 records sum to
121 wins and 121 losses, which equals the 121 completed games in the committed archive; (b) delta —
each record differs from the 3 November snapshot by exactly the result of that team's 4 November
game. Both checks are executed by `scripts/daily_analysis.py` and re-asserted by
`scripts/check_daily.py`.

| Conf | Seed | Team | Abbr | W–L | Since 3 Nov | Result |
|---|---|---|---|---|---|---|
| East | 1 | Philadelphia 76ers | PHI | 8–1 | 7–1 → 8–1 | matches win over DET (112–106) |
| East | 2 | Detroit Pistons | DET | 6–2 | 6–1 → 6–2 | matches loss to PHI |
| East | 3 | Boston Celtics | BOS | 6–2 | 5–2 → 6–2 | matches win over MIL (109–102) |
| East | 4 | Atlanta Hawks | ATL | 5–4 | 4–4 → 5–4 | matches win over WAS (120–105) |
| East | 5 | Toronto Raptors | TOR | 4–4 | 4–3 → 4–4 | matches loss to DEN |
| East | 6 | Cleveland Cavaliers | CLE | 4–4 | 4–3 → 4–4 | matches loss to OKC |
| East | 7 | Washington Wizards | WAS | 4–4 | 4–3 → 4–4 | matches loss to ATL |
| East | 8 | New York Knicks | NYK | 4–4 | 3–4 → 4–4 | matches win over CHI (135–105) |
| East | 9 | Miami Heat | MIA | 3–5 | 2–5 → 3–5 | matches win at LAC (117–116 OT) |
| East | 10 | Charlotte Hornets | CHA | 3–6 | 3–5 → 3–6 | matches loss to BKN |
| East | 11 | Indiana Pacers | IND | 3–6 | 2–6 → 3–6 | matches win at MEM (107–103) |
| East | 12 | Orlando Magic | ORL | 2–5 | 2–5 → 2–5 | idle on 4 Nov |
| East | 13 | Brooklyn Nets | BKN | 2–6 | 1–6 → 2–6 | matches win over CHA (114–104) |
| East | 14 | Chicago Bulls | CHI | 1–7 | 1–6 → 1–7 | matches loss to NYK |
| East | 15 | Milwaukee Bucks | MIL | 1–7 | 1–6 → 1–7 | matches loss to BOS |
| West | 1 | Portland Trail Blazers | POR | 6–1 | 5–1 → 6–1 | matches win at PHX (132–119) |
| West | 2 | Los Angeles Lakers | LAL | 7–2 | 6–2 → 7–2 | matches win at SAC (116–103) |
| West | 3 | Houston Rockets | HOU | 7–2 | 7–1 → 7–2 | matches loss to MIN |
| West | 4 | Oklahoma City Thunder | OKC | 6–2 | 5–2 → 6–2 | matches win over CLE (124–116) |
| West | 5 | San Antonio Spurs | SAS | 6–2 | 5–2 → 6–2 | matches win over DAL (112–111) |
| West | 6 | Memphis Grizzlies | MEM | 6–2 | 6–1 → 6–2 | matches loss to IND |
| West | 7 | Minnesota Timberwolves | MIN | 6–3 | 5–3 → 6–3 | matches win at HOU (117–107) |
| West | 8 | Golden State Warriors | GSW | 5–3 | 5–3 → 5–3 | idle on 4 Nov |
| West | 9 | Denver Nuggets | DEN | 4–3 | 3–3 → 4–3 | matches win over TOR (128–109) |
| West | 10 | New Orleans Pelicans | NOP | 4–4 | 3–4 → 4–4 | matches win over UTA (120–113 OT) |
| West | 11 | Dallas Mavericks | DAL | 4–4 | 4–3 → 4–4 | matches loss to SAS |
| West | 12 | Phoenix Suns | PHX | 1–5 | 1–4 → 1–5 | matches loss to POR |
| West | 13 | LA Clippers | LAC | 1–7 | 1–6 → 1–7 | matches loss to MIA |
| West | 14 | Sacramento Kings | SAC | 1–7 | 1–6 → 1–7 | matches loss to LAL |
| West | 15 | Utah Jazz | UTA | 1–7 | 1–6 → 1–7 | matches loss to NOP |

**Closed irregularity.** Earlier sessions flagged that the Utah row of the 3 November snapshot was
sourced to a schedule page because the standings text had been truncated. On 2026-11-05 the Utah row
(1–7) appears directly in the standings table, so the new snapshot cites S1 for it. The old note in
`data/standings_live_2026-11-03.csv` is left untouched as a historical record.

**Open irregularity (new).** The file named `standings_live_2026-11-03.csv` and the pages built from
it imply live data; re-reading S1 shows 14 of 30 records have since changed. It is a dated snapshot
and internally consistent, but "live" is a misleading label. Published as F04 on the Flagged page;
the file is not overwritten.

---

## 3. Results rows — 14 of 14 checked

Read from S2, one card per game. For each game the game ID in the URL was matched to the CSV row and
the winner's record on the card was compared with the standings delta in section 2.

| Game ID | Date | Matchup (away @ home) | Final | OT | Card record check |
|---|---|---|---|---|---|
| 0022600174 | 2026-11-04 | ATL @ WAS | 120–105 | — | Hawks 5-4 / Wizards 4-4 ✓ |
| 0022600173 | 2026-11-04 | PHI @ DET | 112–106 | — | 76ers 8-1 / Pistons 6-2 ✓ |
| 0022600175 | 2026-11-04 | MIL @ BOS | 102–109 | — | Bucks 1-7 / Celtics 6-2 ✓ |
| 0022600176 | 2026-11-04 | CHA @ BKN | 104–114 | — | Hornets 3-6 / Nets 2-6 ✓ |
| 0022600177 | 2026-11-04 | CHI @ NYK | 105–135 | — | Bulls 1-7 / Knicks 4-4 ✓ |
| 0022600180 | 2026-11-04 | CLE @ OKC | 116–124 | — | Cavaliers 4-4 / Thunder 6-2 ✓ |
| 0022600179 | 2026-11-04 | UTA @ NOP | 113–120 | OT | Jazz 1-7 / Pelicans 4-4 ✓ |
| 0022600178 | 2026-11-04 | IND @ MEM | 107–103 | — | Pacers 3-6 / Grizzlies 6-2 ✓ |
| 0022600181 | 2026-11-04 | MIN @ HOU | 117–107 | — | Timberwolves 6-3 / Rockets 7-2 ✓ |
| 0022600182 | 2026-11-04 | TOR @ DEN | 109–128 | — | Raptors 4-4 / Nuggets 4-3 ✓ |
| 0022600183 | 2026-11-04 | POR @ PHX | 132–119 | — | Trail Blazers 6-1 / Suns 1-5 ✓ |
| 0022600184 | 2026-11-04 | DAL @ SAS | 111–112 | — | Mavericks 4-4 / Spurs 6-2 ✓ |
| 0022600185 | 2026-11-04 | LAL @ SAC | 116–103 | — | Lakers 7-2 / Kings 1-7 ✓ |
| 0022600186 | 2026-11-04 | MIA @ LAC | 117–116 | OT | Heat 3-5 / Clippers 1-7 ✓ |

All 14 games are also consistent with the league-wide check: 121 completed games = 30 teams ×
average 8.07 games played, and wins equal losses.

---

## 4. Forward slate rows — 11 of 11 checked

Read from S3 (which carries both tonight's games and the 6 November NBA Cup block).

| Date | Tip (ET) | Matchup | Competition | Game ID | Records on page |
|---|---|---|---|---|---|
| 2026-11-05 | 9:00 PM ET | ORL @ PHX | Regular season | 0022600187 | Magic 2-5, Suns 1-5 ✓ |
| 2026-11-05 | 10:00 PM ET | MIA @ GSW | Regular season | 0022600188 | Heat 3-5, Warriors 5-3 ✓ |
| 2026-11-06 | 7:00 PM ET | WAS @ ATL | NBA Cup, East Group C | 0022600025 | Wizards 4-4 (1-0), Hawks 5-4 (0-0) ✓ |
| 2026-11-06 | 7:00 PM ET | BOS @ CHA | NBA Cup, East Group C | 0022600026 | Celtics 6-2 (1-0), Hornets 3-6 (0-1) ✓ |
| 2026-11-06 | 7:30 PM ET | PHI @ CLE | NBA Cup, East Group B | 0022600027 | 76ers 8-1 (1-0), Cavaliers 4-4 (0-0) ✓ |
| 2026-11-06 | 8:00 PM ET | UTA @ DAL | NBA Cup, West Group A | 0022600028 | Jazz 1-7 (0-0), Mavericks 4-4 (1-0) ✓ |
| 2026-11-06 | 8:00 PM ET | OKC @ MEM | NBA Cup, West Group B | 0022600029 | Thunder 6-2 (0-0), Grizzlies 6-2 (0-0) ✓ |
| 2026-11-06 | 8:00 PM ET | TOR @ MIL | NBA Cup, East Group A | 0022600030 | Raptors 4-4 (0-1), Bucks 1-7 (0-0) ✓ |
| 2026-11-06 | 8:00 PM ET | MIN @ NOP | NBA Cup, West Group B | 0022600031 | Timberwolves 6-3 (1-0), Pelicans 4-4 (0-0) ✓ |
| 2026-11-06 | 10:00 PM ET | POR @ LAL | NBA Cup, West Group C | 0022600032 | Trail Blazers 6-1 (0-0), Lakers 7-2 (0-1) ✓ |
| 2026-11-06 | 10:00 PM ET | SAS @ SAC | NBA Cup, West Group C | 0022600033 | Spurs 6-2 (0-0), Kings 1-7 (0-0) ✓ |

Cup games carry IDs in the `002260002x` series rather than `00226001xx`; both forms are verbatim
from the official page (F07).

No market price, spread or total is published for any of these games: no official price source is
configured (F02). Those cells are blank on the site, not zero.

---

## 5. Computed values (project, not official)

Produced by `scripts/daily_analysis.py` into `data/official_2026_11_05/analysis.json`; the formulas
are in that file, the inputs are the CSVs above.

| Quantity | Value | Method | Verification status |
|---|---|---|---|
| Games in archive | 121 | 92 (20 Oct–1 Nov) + 15 (2 Nov) + 14 (4 Nov), unique game IDs | input rows source-linked; aggregate reconciled |
| Standings reconciliation, 5 Nov | 30/30 | recomputed W–L from all 121 games vs S1 | verified |
| Standings reconciliation, 3 Nov | 30/30 | recomputed W–L from the 107 games up to 2 Nov vs the 3 Nov snapshot | verified |
| Home advantage | +1.33 pts | ridge model, all 121 games | computed, not official |
| Walk-forward games | 61 | expanding window, refit before each game | computed |
| Winner accuracy | 67.2% (95% Wilson 54.7–77.7%) | model vs actual | computed |
| Always-home accuracy | 50.8% | naive benchmark on the same 61 games | computed |
| McNemar exact p | 0.0639 | discordant pairs 17 vs 7 | computed, **not significant** |
| Brier skill score | +0.1299 (bootstrap 95% −0.0385 to +0.2961) | 1 − model Brier / home-rate Brier, 2000 resamples, seed 20261105 | computed, **interval includes zero** |
| MAE margin / total | 11.51 / 15.31 pts | walk-forward residuals | computed |
| corr(margin, total) | +0.018 [−0.161, +0.196], n=121 | Pearson, Fisher-z interval | computed from official finals |
| corr(home pts, away pts) | +0.199 [+0.022, +0.365], n=121 | Pearson | computed from official finals |
| Split-half team differential | +0.464 [+0.124, +0.706], n=30 | Pearson | computed, underpowered |
| Player-prop correlations | blank | no licensed player-level archive | **unverified** |

Conclusion recorded on the site: the point estimates look encouraging, but the luck-controlled
tests do not exclude chance at 95%, there is no market benchmark, and the sample is about four
games per team. No strategy is promoted; the leaderboard has zero qualified entries.

---

## 6. Irregularities and open questions

1. **F01 Rights.** NBA Terms §9(iv) bars using NBA statistics in connection with gambling; §9(ii)
   limits use to news reporting or private non-commercial purposes; §1 bars republication without
   permission. This site is a private research record with attribution and no prices, but a
   qualified reviewer must confirm the position before any public or commercial reuse.
2. **F02 No official price source.** All market cells blank; no CLV, hold or ROI can be computed.
3. **F03 No player-level data.** Prop and combination strategies cannot be scored; correlations blank.
4. **F04 "live" label stale.** 14 of 30 records changed since 2026-11-03 (see section 2).
5. **F05 Sample size.** 121 games, ~4 per team; forward bands are wide.
6. **F06 Older rows not re-read individually.** The 107-game archive is validated by aggregate
   reconciliation only; per-row links exist in `data/games_results_2026-27.csv`.
7. **F07 Cup game-ID series differs.** Expected; recorded so a later session does not "fix" it.
8. **F08 Inherited sections use different standards.** Not rewritten by this session.
9. **F09 NBA press-reported bet restrictions** are not enumerated in the official release, so none
   are reproduced.

---

## 7. Reproducing this record

```
python3 scripts/daily_analysis.py   # recompute analysis.json from the CSVs
python3 scripts/build_daily.py      # regenerate docs/daily/*.html
python3 scripts/check_daily.py      # rows, sources, blanks, determinism
python3 -m unittest discover -s tests -p test_daily.py -v
```

`check_daily.py` proves internal consistency and source-link coverage. It cannot prove that a cited
page says what this document claims — that is what sections 1–4 are for, page by page.
