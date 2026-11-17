# Repo review — pack nfl_dfc0c1bc (cross-pack decision board), 2026-11-17

Reviewed before writing code, because this pack's whole subject *is* the state of the other packs.
Base: `d8441221c6704bd57e1047f2d6692b3a3236097e` on `main`; branch `arena/dfc0c1bc-own6`.
Numbers below are measured, not remembered: `data/nfl_dfc0c1bc/repo_findings.csv` (RF-01…RF-10) holds the
same findings with the command-shaped evidence, and `docs/nfl-dfc0c1bc/repo-review.html` renders them.

## What was read

* `git ls-files` at review time → 1,142 tracked files (before this branch's additions); `data/` holds 24 pack
  directories; `docs/` holds 33 pack pagesets. `docs/index.html` carries 24 hub cards and the root portal
  `index.html` 19, of which 9 name the same packs — both counts include the card this branch added, so the
  pages are self-consistent with the registers that measured them (`repo_findings.csv` RF-01).
* Every register that carries a suggestion or an open question: 14 suggestion registers (159 rows) and 10
  question registers (176 rows) across 13 packs, inventoried with row counts and `sha256` in
  `data/nfl_dfc0c1bc/suggestions_inventory.csv`. No prior cross-pack consolidation of these existed.
* The evidence files the board and the summaries quote: result corpora (145 / 136 / 137 / 120 / 44 rows
  depending on the file), the injury capture (347 rows, 28 clubs, 171 with a status), depth source register
  (4 rows, `clubs_verified_this_session=0`), reserve register (41), readiness ledgers (81 and 73 requirements),
  `data/nfl_48217a55/blank_audit.csv` (36 rows; 1,054 blank cells over 12,177), six price stores.
* Shared tooling: `tools/release_gate.py` (`OFFICIAL_HOSTS` at line 21), `tools/check_site.py`
  (13 strict pages, 0 errors), `python3 tools/release_gate.py` → **0 issues** on this branch as well.
* Eleven official pages, read in two passes (`2026-11-17T00:38Z → 00:44Z`, then `01:05Z → 01:10Z` for the
  exact URL the price ledger cites), transcribed into `src/nfl_dfc0c1bc/reads.py` so the quote outlives the
  fetch. Each read row carries its own window.
* `COORDINATION.md` (3,151 lines / 382 KB, T1–T13 and P1–P11 all still *in progress*), open PRs (#111, #110,
  #94, #84, #79, #72, #68, #56 …), and 25 workflow files under `.github/workflows/`.

## Weaknesses found (none of them this pack's scope to fix)

1. **The hub and the root portal disagree about what exists.** hub-only: `nfl-309921cc`, `nfl-a411fed0`,
   `nfl-f4`, `nfl-market`; root-only: `nfl-e5e38f9e`, `nfl-wk` (RF-02, measured after this branch linked
   itself into both). Both card lists are hand-maintained, so the drift is invisible to a link checker: every
   link on both pages resolves, which is exactly what a link checker can say about it.
2. **The coordination board is no longer reviewable as a board.** 3,151 lines, 84 rows still *in progress*
   whose deliverables are on `main`, and it names two files that are not in the tree
   (`data/nfl_48217a55/depth_chart_register.csv`, `depth_slot_shapes.csv`). Published as `CF-04` and `C15`
   rather than silently corrected; rule 15 of the verifier re-hashes every register the board consolidated,
   so a stale citation fails CI.
3. **Sixteen executive summaries at the repository root, one per session** (15 of them NFL-domain, including
   this branch's). There is no single answer to
   "where are we", which is exactly the gap this pack's summary file is trying to fill without deleting
   anyone's.
4. **Verification is asserted by each pack and cross-checked by none.** The citation defect below was only
   findable by reading the cited page; no pack had done it, and a link checker cannot see the difference. 16 per-pack build/check pairs and 6
   shared checkers; the same value reads `verified` in one register and `unverified — blank` in another. The
   mis-citation this session found (`CF-10`: 39 `closing_number` cells in `nfl_d966f630` citing an
   `nfl.com/schedules` page that carries no prices) is the concrete cost: a link is not an evidence chain.
5. **`tools/release_gate.py` still whitelists NBA hosts** (line 21) for its row-source rule, and that rule
   only fires on `docs/index.html`. An NFL row on the hub is therefore not covered by it — the gate passes
   whether or not the hub's NFL rows cite anything.
6. **Blanks are the most informative cells and they are published nowhere in aggregate.** 196 flagged rows
   across 13 pack flag registers, plus 1,054 blank cells in the one pack that audited them. This board now
   surfaces the aggregate per pack; it cannot reduce it.
7. **`nfl_8362b702/reserve_absence.csv` attributes a player to the wrong club** — published as
   `CF-01`/`DFC-F01` with the two official pages quoted, and *not* edited here, because rule 13 of the
   verifier fails this branch if it touches another pack's file.
8. **Eight PRs sit open and unreviewed**, including #94 (a stale bookkeeping branch from 2026-11-14). Merge
   queue, not data, and it blocks nothing except the reader's confidence that `main` is current.

## Choices made while reading

* **Themes are decisions, not topics.** A row grouped under "injuries" cannot be chosen; a row asking "which
  source defines depth order, and what do we do about the disclaimer on the club page" can. Sixteen of them,
  each with option paths and a published score formula.
* **Deduplicate by keeping, not by dropping.** Each of the 335 consolidated rows keeps its own
  `source_file` + `source_row_id`, and variants other packs proposed are joined verbatim into `options_raised`
  rather than averaged away. Rule 2 proves no register row vanished.
* **Two statement classes, never mixed.** A value inherited from another pack's CSV is `repo_claim`; only
  text quoted from `reads.py` may be `read_this_session`. Marking an inherited row "verified" because the other
  pack said so is the failure mode this pack exists to remove.
* **No per-request timestamp is claimed.** The fetch tool returns page text and a status but no response
  `Date` header, so the clock is published as a session window plus a `clock_note` on every read row.
* **Price reported as settled-negative, not as another open task.** Five packs, eleven official pages, zero
  price figures — and `price_semantics.csv` shows the six stores are not even measuring the same thing
  (448 cells citing a third-party carrier, 78 own-labelled, 262 citing this repository, 39 official-cited).
  `G-01` is therefore a procurement decision, and the board says so instead of scheduling a tenth attempt.
* **Nothing implemented.** The brief asked for review before changes, so every owner column ships blank and
  `decision_paths.status` is `awaiting_owner_choice` for all 16 rows.

## What a reviewer should check first

1. `data/nfl_dfc0c1bc/cross_pack_conflicts.csv` — `CF-10` and `CF-01` are the two that change other packs'
   output if acted on.
2. `data/nfl_dfc0c1bc/decision_paths.csv` — the ranking formula is printed in the register; if the owner
   dislikes the order, the fixable object is the formula, not the table.
3. `python3 scripts/check_nfl_dfc0c1bc.py` → `OK — 15 rules, 0 failures`; `python3 tests/test_nfl_dfc0c1bc.py`
   → `ALL PASS (11 tests)`; `python3 tools/release_gate.py` → `0 issue(s)`.
4. This pack adds no capture pipeline and no model, so the only clock-sensitive claims it makes are the eleven
   reads and the file hashes in `sources.csv`. The two-page follow-up pass (`R10`, `R11`) is the pattern worth
   copying: it read the *specific* URL a number cites, which is the only way to tell a mis-citation from a price
   the repo simply does not have.
