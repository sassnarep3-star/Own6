# NFL Injury & Depth-Deficiency Tracking — Design, Method, and Deficiency Model

**Date:** 2026-11-12 · **Session:** `arena/efebf74f-own6` · **Design tables:** `data/nfl/injury_tracking.csv` + `data/nfl/depth_model.csv` · **Status:** design-only; all scores blank until licensed depth-chart + timestamped injury feed exist.

## Why injuries and depth matter (official basis)

The [NFL Injury Report Policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf) states:

> “All players who have reportable injuries must be listed on the Practice Report, even if the player takes all the reps in practice, and even if the team is certain that he will play in the upcoming game.”

Reportable injuries include any injury that (a) causes a missed game, (b) prevents finishing a game, (c) causes a missed practice (DNP), (d) limits participation (Limited), or (e) prevents finishing a practice. The league also publishes a weekly league-wide report with `Player | Position | Injuries | Practice Status | Game Status` ([league injury page](https://www.nfl.com/injuries/league/2024/reg17)) and a per-week aggregation of `OUT / DOUBTFUL / QUESTIONABLE` ([Week 10 example](https://www.nfl.com/news/week-10-injury-report-for-2024-nfl-season)). Clubs also file an in-game report and a pre-kick inactive list (90 minutes before kickoff). The [NFL standings](https://www.nfl.com/standings/) and [schedule](https://www.nfl.com/schedule/) provide the official team identity and slate context for those reports.

These sources define **when** a player becomes reportable, not the data license. This document defines how to *use* those reports to estimate depth deficiency once a licensed feed exists.

## Ingestion design (no manual input)

| Capture | Frequency | Fields | Hash rule | Source |
|---|---|---|---|---|
| Practice Report | Wed / Thu / Fri per week | `Player, Position, Injury, Practice Status (DNP/LP/FP)` | SHA-256 per team per day + ET timestamp | [Policy PDF](https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf) |
| Game Status Report | Usually Friday | `Out / Doubtful / Questionable / —` | Same hash rule | [League page](https://www.nfl.com/injuries/league/2024/reg17) |
| Inactive List | 90 min pre-kick | Dressed vs inactive | ET timestamp after deadline | [nfl.com](https://www.nfl.com/) gameday |

Each file is stored with `feature_asof`, `forecast`, `event_start` timestamps satisfying `feature_asof ≤ forecast < event_start`. Any observation whose injury snapshot is newer than its forecast is rejected (look-ahead).

## Depth-chart model (1st → 2nd → 3rd → 4th string)

A **starter** is defined as the club-announced Week-1 starter at each position or the most recent officially designated starter. Backups are the depth-chart's 2nd-string (primary backup), 3rd-string, and 4th-string (often practice-squad elevation). The depth chart is not inferred from media; it must be a licensed official snapshot per game week.

`data/nfl/depth_model.csv` defines nine units and their position groups:

- **QB:** QB1 vs QB2/QB3
- **OL:** LT/LG/C/RG/RT (five slots evaluated separately)
- **WR:** WR1/WR2/WR3 depth order
- **RB:** RB1/RB2 (RB3/RB4 separate)
- **TE:** TE1/TE2
- **DL:** DE/DT (3–4 vs 4–3 front)
- **LB:** MLB/OLB by scheme
- **DB (Secondary):** CB1/2/3, S1/2
- **K:** K1 vs backup K

Each unit carries a **deficiency metric**: `deficiency = 1 − (available starter snaps / expected starter snaps)` per game.

### Interpretation

| Threshold | Meaning | Example |
|---|---|---|
| 0.0 | No deficiency (all starters available) | OL all five slots Full |
| 0.15–0.30 | Material deficiency | Secondary missing one starting CB (backup CB2 starts) |
| 0.50+ | Acute deficiency | QB1 Out → QB2 starts for full game; or OL missing two starters; or CB1+CB2 both Out vs opponent WR1 |

### Flagging 2nd/3rd/4th-string starts

A flag is raised when:
- `depth_before > 1` **and** `Game Status` for the starter is `Out` or `Doubtful` **and** the inactive list confirms the starter is inactive, **and** snap data confirms the backup actually played the majority of the unit's snaps.

Flag values stay blank until both the depth-chart snapshot and the snap-share are licensed and hashed.

## How deficiencies feed signals (but do not invent values)

Deficiency scores are **features, not bets**. They adjust the own-line model's efficiency inputs:

- QB deficiency → downgrades passing yards/efficiency projection (N04); see correlation C06 (QB YPA vs OL deficiency).
- OL deficiency → raises pressure expectation, lowers YPC; affects spread N01 and rushing props N05.
- Secondary deficiency (2nd/3rd/4th-string DBs covering WR1) → elevates opponent WR yardage; see C07.
- DL deficiency → lowers pressure/sack expectation → elevates opponent QB efficiency; see C08.
- RB carry split (Teammate RB1 vs RB2 negative correlation C05) → workload flip to backup.

**All deficiency values in the current site are blank and flagged (F-NFL-03, F-NFL-04).** Publishing a number before the two required feeds (injury PDF + depth chart) exist would be a hallucination. The pages `docs/nfl/injuries.html` and `docs/nfl/depth.html` therefore show `— blank (unverified)` with an official source link per row.

## Offense vs defense — same rule applies

The requirement explicitly asks: “the system should be tracking injuries and know any deficiencies in defenses such as 2nd/3rd or 4th string backups having to replace starters due to lineups. Also same can be said for offenses using starters or backups.” The design meets this symmetrically:

- **Offense tables:** QB, OL, WR, RB, TE — each with starter share, backup share, 2nd/3rd/4th-string flag, deficiency.
- **Defense tables:** DL, LB, DB — same columns, same flag rule.
- **Units are not mixed.** OL deficiency does not imply secondary deficiency.

## Discovery path for missing information

| Missing info | Where to discover (without hallucination) |
|---|---|
| Official injury-report PDFs with hashes | Weekly capture described above; store in `data/nfl/official_YYYYWW/` with hashes in a `manifest.csv` |
| Official depth-chart feed | Request quote from NFL licensed distributor (Sportradar/Genius) for weekly depth chart snapshots; record license ID |
| Snap-weighted deficiency (actual snaps) | Next Gen Stats player-tracking [operations page](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats/) describes tracking technology; confirm licensed feed before using snap counts |
| Market line to compare against | Licensed odds archive with capture times and hashes; de-vig same line per [DraftKings](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB) |

Until those files exist with hashes, the site correctly shows blanks and flags, and `scripts/check_nfl.py` enforces that no blank row carries a fabricated numeric value.

## No inference

This document never infers a player's status. If a report is not captured, its field is blank. If a depth chart is not licensed, its deficiency is blank. That is an evidence boundary, not a zero.
