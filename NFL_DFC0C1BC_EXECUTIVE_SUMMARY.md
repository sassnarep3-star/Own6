# NFL cross-pack decision board — executive summary

Session branch `arena/dfc0c1bc-own6`, built 2026-11-17. Pages: `docs/nfl-dfc0c1bc/`.
Registers: `data/nfl_dfc0c1bc/` (19 files, verified by `scripts/check_nfl_dfc0c1bc.py`, 15 rules).
**Nothing on this board is implemented.** Every decision column is blank by design, and rule 4 of the
verifier fails the build if a session writes into one.

## Why this pack exists

Two instructions were open on the coordination board and neither was satisfied by the 17 packs already in
the tree:

* *"suggestions on how to improve the site to improve decision making … a section dedicated for suggestions
  so someone can review suggestions and choose the best path before implementing any changes"*;
* *"a clear list of questions, informations and answers that need to be addressed before any decision can be
  reasonably made based upon the information we already have and do not have"*.

Both were answerable **without touching anyone's model**: the material already existed, scattered across
per-pack registers that no single page showed together. So this pack consolidates it, and spends its own
effort on the part only a fresh read can settle — which official routes actually publish what the board
claims they do.

## What is on the board

| register | rows | note |
|---|---|---|
| suggestions consolidated | 159 | from 14 registers across 13 packs, each row keeping `source_file` + `source_row_id` |
| questions consolidated | 176 | from 10 registers, with the answer/observation ids that close them where one exists |
| decision paths | 16 | themes are **decisions the owner can take**, not topics; each has option paths A/B/C and a score |
| information gaps | 13 | what we do not have, measured coverage, route, clearing number, cost |
| cross-pack conflicts | 10 | where two packs, or the board and the tree, say different things |
| claim checks | 18 | each published claim tested against the file that should support it |
| official reads | 11 | pages read this session, with verbatim quotes and a per-read window |
| observations / answers | 12 / 7 | what each read showed, and which questions it closes or reopens |
| register dictionary | — | `data/nfl_dfc0c1bc/README.md` names every column and both statement classes |
| flagged for review | 25 | everything a reviewer must look at before choosing |

Ranking is a published formula, not taste: `value = 2·packs + suggestion_rows + question_rows +
2·evidence_rows`, `ratio = value / effort_score` (effort 1 = low, 2 = medium, 3 = high).

## The six paths the arithmetic puts first

| # | decision to take | packs | rows | ratio |
|---|---|---|---|---|
| 1 | **T12** one canonical site with an owner decision log, or many per-session dashboards | 13 | 32 + 11 | 69.0 |
| 2 | **T10** what the board ranks, when a strategy may go live, and the priority order between them | 13 | 18 + 13 | 57.0 |
| 3 | **T08** which estimators are published, and whether the model says what it left out | 10 | 11 + 16 | 51.0 |
| 4 | **T01** what this project may store and republish at all | 13 | 10 + 12 | 48.0 |
| 5 | **T07** which game log is canonical, how far back, and what happens on disagreement | 10 | 10 + 13 | 43.0 |
| 6 | **T05** which source defines depth order — club pages, official snap counts, or our own derivation | 14 | 15 + 26 | 39.5 |

T05 scores the highest raw value (79: 14 packs raised it, 26 open questions, 5 new evidence rows this
session) and ranks sixth only because its effort is high. **If the owner wants the biggest single unblocking
act rather than the best value-per-day, T05 is it**; if the owner wants the cheapest wide one, T12 is: it is
a naming and layout decision, and 13 packs already asked for it.

## What the official reads settled (this session)

Reads happened in two passes — `2026-11-17T00:38Z → 00:44Z` (nine pages) and `01:05Z → 01:10Z` (two
follow-ups against the exact URL a price ledger cites). The tool returns page text and status but **no response
`Date` header**, so the board publishes a window per read and never claims a per-request second.

1. **A register attributes a quarterback to the wrong club.** `data/nfl_8362b702/reserve_absence.csv` holds
   "Malik Willis, GB, state unknown"; the league's own pages place him on **Miami's** reserve list (`#2 QB
   RES`, groin). The row is not unknown, it is mis-attributed. Published as `CF-01` / `DFC-F01` with a request
   to the owning pack — not edited here.
2. **Depth charts are not on nfl.com.** `nfl.com/teams/green-bay-packers/depth-chart/` is a 404; the club's own
   site publishes one, dated, labelled **Unofficial**, in three-column groups with repeated positions. So the
   realistic shape of a depth register is "groups of names + raw string + page date + disclaimer", and any
   suggestion that assumes a tidy 1st/2nd/3rd string needs re-scoping. `CF-06`, guardrails `RJ-01`/`RJ-09`.
3. **Venue is published per fixture, not per week.** It is on the game centre page, not the by-week page — so
   the "venue missing" gap is a route problem, not a data gap (`A5`).
4. **The three Lions blanks are a publish failure, not a source gap.** `nfl.com/injuries/` printed
   Joseph / Mays / Reed as `Did Not Participate In Practice` → **Out**, and the repo capture file *also* already
   carries "Out" for all three. The blank cells are a display/extract defect. `C18`, `lions_status_check.csv`.
5. **The price half stays unfound, and is reported as settled-negative.** Nine official pages, five packs,
   zero price figures — again. Per cell across the six price stores: 448 cells cite a third-party carrier
   (real operator quotes), 78 sit in a column the pack itself labels as ours, 262 cite a file inside this
   repository, 39 sit in a market-sounding column with an official page URL beside them, and none hold a number
   taken from a page that publishes lines. `G-01` is therefore a **procurement decision**, not a scraping task.

6. **A by-week page is not a results feed.** Read on Nov 17, every Thursday and Sunday fixture on the Week 10
   page showed `FINAL`, while the Monday game played the previous evening showed only a time, a network and two
   records. Whether that is page lag or an extraction artefact cannot be settled from one read — which is
   precisely why a results ledger must be reconciled from game centres, not scraped off a schedule page (`O15`).
   The same page does print the week's byes as a labelled block, so the board's missing `bye_clubs_week10.csv`
   is a store to build, not a source to find; and its weather field is a one-word token (`Weather Clearnight`)
   with no number beside it, so `G-08` keeps its weather-service route (`O14`).

## Two things the owner should resolve *before* choosing a path

* **`CF-10` — a citation defect worth fixing globally.** In `data/nfl_d966f630/price_snapshots_open_close.csv`,
  39 `closing_number` cells pair `www.nfl.com/schedules/2026/by-week/week-10` as their source URL, while the
  same file's own columns say `opening_class = retrospective_reconstruction ×132` and `closing_role =
  open_and_close_final ×132 / close_provisional ×39`, and its `movement_note` says the two numbers come from
  two different model versions. That URL names where an *input* came from, not where the *number* was read. A
  later reader (or a verifier) will quote it as "official price". Fix: move input-provenance URLs into an
  `inputs_url` column, and add a host-class rule to the verifier — a number in a market column may not cite a
  host that cannot publish that class.
* **`CF-09` / `CF-02` — the same label means different things in different packs.** "verified" on a price row
  can mean *verified against an official page for inputs*, and the corpus is 145 / 136 / 137 / 120 / 44 games
  depending on which file is opened. Both are settled by a written class rule (what a column means), not by
  another capture.

## Board vs tree

`CF-04` stands: the coordination board's T7 deliverables `data/nfl_48217a55/depth_chart_register.csv` and
`depth_slot_shapes.csv` are **not in the tree**, while `blank_audit.csv` is and sums to 1,054 blank cells over
12,177. `C15` prints the contradiction. The board also still shows all of T1–T13 and P1–P11 as *in progress*
although their deliverables are on `main` — a governance row, not a data one.

## Recommended path (a recommendation, not an action)

1. **Decide T12** (canonical site + decision log) — cheapest wide win; it is the page on which every other
   choice gets recorded, and 13 packs asked for it.
2. **Decide T02/T10 together** (price policy and what the board ranks). With no licensed price source, the
   only honest rank is on proper scores against verified results; publishing that constraint is a decision,
   not a failure.
3. **Take `CF-10` as a one-line verifier rule** across packs (host class must match column class) — it prevents
   the mis-citation class rather than fixing one row.
4. **Fund T05 only after a written source rule** for depth (club page + date + disclaimer, or nothing).
5. Then work the gaps with a clearing number each: `G-08` (hourly kickoff forecast from a public-domain source)
   is the cheapest real closure on the board; `G-13` is this summary's own point — no path is closed until a
   choice is recorded.

Every row above is a *choice to make*, with the option paths, the evidence needed, and the file names to check.
Nothing here is implemented, and that is the point of the section.
