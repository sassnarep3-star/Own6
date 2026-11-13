# Injury and depth-deficiency tracking (offense and defense, 1st through 4th string)

Session `arena/309921cc-own6` · captured 2026-11-13 ·
tables: `week10_injuries.csv`, `week10_injury_load.csv`, `depth_charts.csv`,
`depth_deficiency.csv`, `depth_unlisted_designations.csv` → `docs/nfl-309921cc/injuries.html`, `depth.html`

## 1. What the official report gives us

`https://www.nfl.com/injuries/` publishes, for Week 10 of 2026, a table per club with exactly five
columns: **Player, Position, Injuries, Practice Status, Game Status**. The page itself defines those
columns; nothing is added.

- **326 rows** across the 28 clubs playing this week.
- **Practice Status** vocabulary as printed: *Did Not Participate In Practice*,
  *Limited Participation in Practice*, *Full Participation in Practice*.
- **Game Status** is blank for most rows. Only 25 rows carry a designation at capture, spread across
  three clubs (WAS, NYG, NE, DET and IND). The report is populated progressively through the week —
  Friday designations for Sunday games were not yet published (flag NFL3-F11).
- The **Injuries** column is blank for most rows. That is the page's own blank; no injury is inferred.

## 2. Per-club load

Counts derived by reading every row, published in `week10_injury_load.csv`. The heaviest lists at
capture were Dallas (18 listed), the Chargers (18) and Green Bay (16); the lightest was Las Vegas (4).
The verifier checks that the three practice-status counts sum to the listed total for all 28 clubs,
and that the 28 club counts sum to 326.

## 3. Depth charts — and the caveat that governs them

Two club charts were captured: New England (`patriots.com/team/depth-chart`) and Detroit
(`detroitlions.com/team/depth-chart`). Both give 1st-to-4th string ordering for offense and defense.

**Both clubs label their own chart unofficial.** Patriots.com states the chart "is unofficial and is
published by the writers of Patriots.com. The depth chart reflects the opinions of the Patriots.com
writers and don't necessarily reflect those of the organization." The Lions chart is an "Unofficial
Depth Chart Compiled by Lions Football Communications".

That caveat is carried onto **every row** the pack derives from a chart, and the chart's
`source_status` is `verified_direct_unofficial_source` rather than `verified_direct` (flag NFL3-F04).
This matters because the most natural reading of "2nd string will start" is that it is an official
statement. It is not.

## 4. The deficiency model

For each position slot, ordered 1st → 4th string:

- The **active string** is the shallowest listed string **not ruled Out**.
- The **next available backup** is the first string behind the active one that is listed **and** not
  ruled Out. Players ruled Out are skipped, which is how a 3rd or 4th string replacement is surfaced.
- The **deficiency score** uses proposed weights:

| Situation | Score |
|---|---|
| Healthy 1st string active | 0.00 |
| 1st string active but Questionable | 0.35 |
| Healthy 2nd string must start | 0.65 |
| 2nd string must start and is himself Questionable | 0.85 |
| Replacement is 3rd string or deeper, or none is listed | 1.00 |

**These weights are a design hypothesis, not an observed quantity** (flag NFL3-F07). No official
source defines how much a backup weakens a unit. Every row is labelled
`proposed_weight_not_observed`, as requested by a prior session's review.

## 5. What it found for Week 10

| Club | Unit | Slot | 1st string | Active | Next available | Score |
|---|---|---|---|---|---|---|
| NE | Offense | WR | A.J. Brown (Questionable) | 1st | 2nd — Efton Chism III | 0.35 |
| NE | Offense | **LG** | Ben Brown (**Out**) | 2nd — Walter Rouse (**Questionable**) | **none listed** | **0.85** |
| NE | Offense | RB | Rhamondre Stevenson (Questionable) | 1st | **3rd** — Corey Kiner | 0.35 |
| NE | Defense | CB | Carlton Davis III (**Out**) | 2nd — Channing Canada | none listed | 0.65 |
| DET | Offense | C | Cade Mays (**Out**) | 2nd — Juice Scruggs | none listed | 0.65 |
| DET | Defense | CB | D.J. Reed (**Out**) | 2nd — Rock Ya-Sin | 3rd — Khalil Dorsey | 0.65 |

Two are worth calling out:

- **New England left guard is the worst slot in the pack.** The 1st string (Ben Brown) is Out, the
  2nd string (Walter Rouse) is himself Questionable, and the chart lists no 3rd string.
- **New England running back is the 3rd-string case.** The starter (Rhamondre Stevenson) is
  Questionable and the 2nd string (TreVeyon Henderson) is Out, so the next *available* back is
  Corey Kiner, the 3rd string — with Lan Larison 4th. A naive "next man up" reading would have
  named Henderson, who cannot play.

Defense is tracked identically: Carlton Davis III (CB) and D.J. Reed (CB) are both 1st-string
defensive backs ruled Out, so both clubs start a 2nd string corner.

## 6. Designated players missing from their own club chart

Four designated players do not appear anywhere on their club's published chart, so no replacement
string can be resolved for them:

| Club | Player | Status | Chart entry sharing a name prefix |
|---|---|---|---|
| NE | Reggie Gilliam (FB) | Questionable | — |
| NE | Greg Van Roten (G) | Questionable | — |
| NE | Kevin Byard (S) | Questionable | Kevin Byard III |
| DET | Kerby Joseph (S) | **Out** | — |

The Kevin Byard / Kevin Byard III pair is reported as a **candidate string match only**. The pack
does not assert the two names are the same person, because no official page here says so. This is
deliberate: a name-resolution step that silently merged the two would be an inference, and the
whole point of this pack is that inferences are not published as facts. Every row in
`depth_unlisted_designations.csv` carries `name_match_is_verified_identity = no`.

## 7. Limits

The report is a Friday snapshot. Designations for most Sunday games were blank at capture and will
change. The deficiency scores are proposed weights on an unofficial ordering. Nothing here is a
prediction of performance, and nothing here should be used to justify an injury-tied wager: the
NFL's own release lists bets tied to injuries among the wagers partners work together to prohibit.
