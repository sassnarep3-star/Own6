# Decision readiness — what we have, what we lack, and how to find it

Session `arena/309921cc-own6` · captured 2026-11-13 · published table: `data/nfl_309921cc/decision_ledger.csv`
→ `docs/nfl-309921cc/decision-ledger.html`

## Purpose

A decision is only as good as the information behind it. This file separates three things that are
routinely mixed together in this repository:

1. **What an official page actually says** (information we have);
2. **What is missing** (information we lack);
3. **A concrete action that would produce the missing information** (how to discover it).

Nothing in the third column is a guess. Every discovery suggestion is an action — buy, request,
capture, fit, or ask — not a value.

## The ledger at a glance

| Priority | Count | Question IDs |
|---|---|---|
| High | 9 | Q01, Q02, Q03, Q04, Q05, Q07, Q08, Q09, Q13, Q14 (Q13/Q14 are repository-level) |
| Medium | 5 | Q10, Q11, Q12, Q15 |
| Low | 1 | Q16 (rewards — resolved) |

## The five that block everything else

**Q01 — Data rights.** NFL.com Terms §1.3 (read 2026-11-13, updated May 16, 2024): the Services may
be used "solely for your own individual non-commercial and informational purposes only", and
"Systematic retrieval of data or other content from the Services, whether to create or compile,
directly or indirectly, a collection, compilation, database, or directory, is prohibited absent our
express prior written consent." This repository is a compiled database of official tables. The
question is not about one pack; it is about the repository. Until it is answered, every further
capture increases exposure.

**Q02 — The market benchmark.** The NFL's own release names DraftKings, FanDuel and Fanatics as 2026
official sportsbook partners and Genius Sports as the exclusive official betting-data distributor.
That tells us who distributes data; it does not give us a price. Without a licensed archive of
timestamped opening and closing prices, gates G02 (no invented prices), G08 (closing-line value) and
G10 (luck-separated skill) cannot be evaluated at all, and therefore no leaderboard tier above
Tier 3 can be reached. Three paths exist: buy an archive, restrict the project to no-price research,
or hand-capture under a documented rationale. One must be chosen.

**Q03 — Line-origination inputs.** The originated line uses verified points-for and points-against
per game only. Two parameters are declared rather than fitted — home-field advantage at 0.00 points
and shrinkage at 1.00 — because no official page in this pack supplies them. A third, the
victory-margin distribution, is why the moneyline column is blank. All three can be fitted from a
licensed multi-season results file. Until then they stay neutral, and the moneyline stays blank.

**Q04 — Injury-data timing.** The Week 10 report read on 2026-11-13 publishes Player, Position,
Injuries, Practice Status and Game Status. Designations were populated for 3 of 14 games; the other
11 clubs had Game Status blank, because the report is filled in progressively through the week. A
deficiency claim is only defensible if it is tied to a specific, timestamped, hash-stamped capture.
Suggested cadence: Wednesday, Friday and Saturday, with the last pre-kickoff capture being the only
one allowed to justify a flag.

**Q05 — Standings freshness.** nfl.com/scores publishes Thursday 12 November's Commanders 24–21 win
over the Giants as Final. nfl.com/standings still lists WAS 3-5-1 and NYG 5-3-1 — both pre-game,
9-game records. Any model that mixes a standings-derived rate with a result the standings do not yet
contain is internally inconsistent. Either lag every input to the snapshot date or wait for the
refresh; never mix.

## Repository-level questions

**Q13 — Which NFL pack is canonical?** Four independent NFL dashboards are now published from this
repository: `docs/nfl/`, `docs/nfl-3b81013c/`, `docs/nfl-origination/` and `docs/nfl-309921cc/`.
Each has its own source register and its own evidence standard. A reviewer can easily act on the
older one. Nothing should be deleted — each register is provenance — but one pack per question
should be named canonical and the rest bannered as archived.

**Q14 — Which source links no longer resolve?** `https://www.nfl.com/official-nfl-rules/` returned
the official NFL 404 page on 2026-11-13. A repository-wide count finds 71 occurrences across 20+
files, including live published pages. A row whose supporting link is a 404 cannot be treated as
verified. Repoint to `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook`, or to the
specific rule section each row relies on.

**Q15 — Does the printed URL load?** The README publishes
`https://sassnarep3-star.github.io/Own6/nfl/`, which returned GitHub's 404 page on 2026-11-13. Pages
for this repository is served from `main:/`, so the same content is live at `/docs/nfl/`.

## Lower priority

**Q10 — Sample size.** A floor of 200 graded selections per family is declared, with the reason: with
ten strategies tested, an uncorrected 5% threshold produces false positives far more often than 5%
of the time. The floor is about statistical power, not money, so it can be met with paper-graded
(unbet) selections.

**Q11 — Roster rules.** The NFL Operations CBA summary states the gameday active list rises to 48
from 46 and that teams must carry at least eight offensive linemen. It does not state 2026
practice-squad elevation counts or injured-reserve return counts; those remain unknown.

**Q12 — Rule changes.** The 2026 rulebook page lists the 2026 changes, including 6-1-6, which permits
the kicking team to declare an onside kick at any time during the game. Whether that moves any
special-teams or total market is unread and unmeasured here.

## What "resolved" looks like

A question is closed only when the answer is written into `COORDINATION.md` with the source that
supports it, and the corresponding gate status changes in `data/nfl_309921cc/validation_gates.csv`.
Nothing in this pack has been closed on the owner's behalf.
