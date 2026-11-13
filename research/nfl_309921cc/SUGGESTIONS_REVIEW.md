# Suggestions for review — pick a path before implementing anything

Session `arena/309921cc-own6` · captured 2026-11-13 ·
published table: `data/nfl_309921cc/suggestions.csv` → `docs/nfl-309921cc/suggestions.html`

## The rule this section follows

**Nothing here has been implemented.** Every row is `pending_human_choice`. Each suggestion states:

- the **current repository state** it responds to;
- the **decision problem** it would solve;
- **two or three option paths**, so the choice is explicit;
- a **recommended path**, clearly labelled as a recommendation;
- **prerequisites** — what must be true before it is started;
- **effort and reversibility**.

The point of this section is that a reviewer can compare paths and choose one *before* any code
changes. Implementing first and reviewing afterwards is how a repository ends up with four
competing dashboards.

## The 14 suggestions

| ID | Area | Recommendation | Effort |
|---|---|---|---|
| SUG-01 | Site architecture | Neutral multi-domain root portal | Low, reversible |
| SUG-02 | Duplicate packs | Canonical pack + "archived provenance" banner | Low, non-destructive |
| SUG-03 | Broken sources | Repoint 71 dead citations | Medium, touches another session's files |
| SUG-04 | Documentation | Correct the README's 404 URL | Low, reversible |
| SUG-05 | Data freshness | UTC timestamp + SHA-256 per capture | Medium, new captures only |
| SUG-06 | Standings lag | Refuse to model already-played games | Low, reversible |
| SUG-07 | Depth-chart status | Carry the club's own caveat onto every row | Low, already in place |
| SUG-08 | Evidence labelling | A required `value_kind` column on every table | Low, already in place |
| SUG-09 | Coordination file | Split task board from append-only history | Low, but shared |
| SUG-10 | Merge safety | Regenerate derived inventories only at integration | Medium |
| SUG-11 | Evidence ledger | One consolidated "what we cannot show" page | Low |
| SUG-12 | Rights gate | Pause numeric capture pending counsel | High impact |
| SUG-13 | Verification automation | Nightly HTTP probe of every source URL | Medium |
| SUG-14 | Leaderboard rewards | Keep rewards non-monetary and say so | None, already in place |

## Three that deserve a decision first

**SUG-12 — Rights first.** The NFL terms permit individual non-commercial informational use and
prohibit systematic retrieval to compile a database. This repository is a compiled database of
official tables. The interim operating rule suggested here is: keep capturing only what a human
reader could verify in a single page view, and stop adding bulk tables until counsel answers. This
is the one suggestion that is only partly reversible — adopting it later means deleting captured data.

**SUG-03 — The dead URL.** 71 citations, 20+ files, including live pages. This is a concrete
demonstration of why SUG-13 matters: no existing checker fetches the URL, so a dead link passes
every current gate. Fixing 71 citations is mechanical; fixing the class of defect is the real work.

**SUG-02 — Canonical pack.** Four NFL dashboards now answer overlapping questions. The recommended
path is deliberately non-destructive: keep all four, banner the superseded ones as archived
provenance, and point to one canonical pack per question. Deleting a pack would also delete its
source register, which is the one thing that cannot be reconstructed.

## Why suggestions are separated from decisions

A *decision* (see `DECISION_READINESS.md`) is a question that must be answered before something can
be done safely. A *suggestion* is a proposed change with options. Keeping them apart means a
reviewer is never asked to approve an implementation before the information needed to judge it
exists.
