# Originating our own NFL lines, and the strategy catalog

Session `arena/309921cc-own6` · captured 2026-11-13 ·
tables: `data/nfl_309921cc/originated_lines.csv`, `strategies.csv`, `leaderboard_*.csv`

## 1. What "originate our own line" means here

It means producing a fair price **from verified inputs only**, using a formula that is written down,
and refusing to publish any value that would require a number no official page supplies. It does
**not** mean guessing a market price, and it does not mean publishing a pick.

### Inputs (all verified)

- Points for and points against per game for all 32 clubs — `https://www.nfl.com/standings/`
- The 14-game Week 10 slate — `https://www.nfl.com/schedules`

### Formula

For a game with home club *H* and away club *A*:

```
home_expected = (H.points_for_per_game + A.points_against_per_game) / 2 + HFA / 2
away_expected = (A.points_for_per_game + H.points_against_per_game) / 2 - HFA / 2
originated_home_spread = away_expected - home_expected      # American form: negative = home favoured
originated_total       = home_expected + away_expected
```

### Declared parameters (flag NFL3-F06)

| Parameter | Value used | Status |
|---|---|---|
| Home-field advantage | 0.00 points | Declared, not fitted. No official page in this pack supplies it. |
| Shrinkage | 1.00 (none applied) | Declared, not fitted. Needs a licensed multi-season history. |
| Victory-margin distribution | — | Absent. This is why the moneyline column is blank (flag NFL3-F08). |

All three are neutral values. Choosing a real home-field advantage would improve the line and
simultaneously make it unverifiable, so it is left at zero and flagged.

### Self-consistency check (measured, not assumed)

| Quantity | Value |
|---|---|
| League points per team-game (from verified standings) | 22.9599 |
| League points per game, both teams | 45.9197 |
| Model mean total over the 13 scheduled games | 46.3785 |
| Model minus league | +0.4588 |
| Model mean absolute home spread | 3.7808 |
| Games modelled | 13 (1 excluded: already final) |

The one game already final at capture — Commanders 24, Giants 21 on Thursday 12 November — is
deliberately **not** modelled. Modelling a game whose result is already published is the easiest way
to fool yourself that a model works.

## 2. Strategy catalog

Ten preregistered strategies: three single bets, two player props, two same-game prop combos, two
parlays, and one meta diagnostic. Each row states its hypothesis, its signal rule, how its own line
is built, which of its inputs are verified, the dependence pair it needs, and the gates it must clear.

| Family | IDs | Note |
|---|---|---|
| Single bet | ST-01 spread, ST-02 total, ST-03 moneyline | ST-03 is **blocked** — no margin distribution exists. |
| Player prop | ST-04 performance, ST-05 depth-driven usage | G11 eligibility is applied before modelling. |
| Prop combo (SGP) | ST-06 QB+WR stack, ST-07 RB+team total | Dependence must be measured; independence is never assumed. |
| Parlay | ST-08 cross-game, ST-09 same-game spread+total | Cross-game independence is a claim to test, not an input. |
| Meta | ST-10 closing-line value | Blocked on licensed closes. |

**0 graded selections. 0 qualified strategies.**

### Market-integrity eligibility (gate G11)

Applied before any modelling. The NFL's own release states partners will work together "to prohibit
wagers the league finds objectionable, including bets tied to officiating and injuries, along with
those that can be knowable in advance or easily manipulated by a single person." A prop family tied
to injuries or officiating is therefore rejected by construction — not because it is unprofitable,
but because it is outside the catalog's remit.

## 3. Leaderboard and rewards

Four tiers, all **non-monetary**: research standing and publication priority only.

| Tier | Requirement | Entries |
|---|---|---|
| Tier 3 — Preregistered | G01, G05, G11, G12 open | 0 |
| Tier 2 — Measurable | + G03, G04 (200 chronological out-of-sample selections) | 0 |
| Tier 1 — Skill-evidenced | + G06, G07, G10 (Holm-corrected, calibrated, interval excludes zero) | 0 |
| Tier 0 — Price-evidenced | + G08 (positive closing-line value) | 0 |

No reward has been awarded. Rewards stay non-monetary because the NFL terms restrict use to
individual non-commercial informational purposes; a prize would contradict that.
