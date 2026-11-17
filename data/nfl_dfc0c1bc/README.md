# `data/nfl_dfc0c1bc` — the cross-pack decision board, register by register

Built by `python3 scripts/build_nfl_dfc0c1bc.py`. Every file here is generated output — edit the
registers in `src/nfl_dfc0c1bc/*.py` (or the source CSVs the board reads) and rebuild. Verified by
`python3 scripts/check_nfl_dfc0c1bc.py` (15 rules) and `python3 tests/test_nfl_dfc0c1bc.py` (11 tests).
Pages: `docs/nfl-dfc0c1bc/`.

## What this pack is for

Two owner instructions, taken literally:

1. *"make suggestions on how to improve the site to improve decision making and create a section dedicated
   for suggestions so someone can review suggestions and choose the best path before implementing any
   changes"* — so every suggestion ever registered is on one page (`suggestions_master.csv`), grouped into
   themes that are **decisions, not topics**, with the best-path ranking beside them
   (`decision_paths.csv`), and **no suggestion implemented**.
2. *"a clear list of questions, informations and answers that need to be addressed before any decision can
   be reasonably made based upon the information we already have and do not have"* — so the open questions
   are consolidated (`questions_master.csv`), the things we do not have are measured as gaps
   (`information_gaps.csv`), and the questions that could be closed from official pages today were closed
   (`official_reads.csv`, `observations.csv`, `answers.csv`).

Because the brief asks for review *before* implementation, `owner_decision`, `owner_choice`, `owner_notes`,
`owner_answer`, `decision_logged_on` ship **blank on purpose** and rule 4 of the verifier fails the build if
anything writes into them.

## Two classes of statement, never mixed

| class | where it may appear | what it means |
|---|---|---|
| `repo_claim` | any consolidated row | text inherited from another pack's CSV, with `source_file` + `source_row_id` naming the row. Nothing here was re-read at its source. |
| `read_this_session` | `official_reads.csv` and rows that cite a `read_id` | text quoted from a page fetched during this session. |

The retrieval tool returns page text and a status but **no response `Date` header**, so the clock is published
as a session window and no per-request second is claimed (`clock_note` on every read row). The session ran two
passes — `2026-11-17T00:38Z–00:44Z` for the first nine reads, `01:05Z–01:10Z` for two follow-ups against the
exact URL a price ledger cites — and each read row carries its own `read_window_utc`, so no read borrows
another's clock. A blank cell always
means "no confirmed value", never zero and never "does not exist". A 404 is recorded as a finding — the route
is absent, or the fixture is unplayed — not as an empty source.

## Files

| file | rows | what it holds |
|---|---|---|
| `suggestions_inventory.csv` | 26 | every source register the board consolidated: pack, path, kind, row count, column names, `sha256` at read time. |
| `suggestions_master.csv` | 159 | all suggestions from 14 registers, deduplicated-by-source not deduplicated-by-silence: each row keeps `theme_id`, `source_pack`, `source_file`, `source_row_id`, `options_raised` (the variants other packs proposed, verbatim, joined with ` \|\| `), plus empty owner columns. |
| `questions_master.csv` | 176 | all open questions from 10 registers, with the answer/observation ids that close them when one exists (`answer_ids`, `observation_ids`). |
| `decision_paths.csv` | 16 | one row per theme: the decision phrased as a choice, the option paths, evidence needed, `value = 2·packs + suggestions + questions + 2·evidence`, `ratio = value / effort_score`, `status = awaiting_owner_choice`. |
| `information_board.csv` | 16 | per theme: what is known now, what is missing, what this session changed, what it costs to close. |
| `information_gaps.csv` | 13 | each gap: measured coverage now, acquisition route, clearing number, cost, risk if left open, themes blocked, and whether the owner can close it by decision alone. |
| `official_reads.csv` | 11 | one row per official page read: url, host, session window, how the clock was obtained, verbatim excerpt, state (including the 404s). |
| `observations.csv` | 15 | one finding per read or read-pair: `read_id` (pipe-joined), observation, what it supports, theme. |
| `answers.csv` | 8 | questions closed, partially closed, or explicitly not closed — with the read ids that decide it. |
| `metrics.csv` | 55 | row/field counts measured from other packs' registers (results, injuries, depth, reserve, readiness, blanks) — each row names its file; a missing file yields no number. |
| `corpus_sizes.csv` | 11 | game corpora side by side, so "the corpus is 136 games" can be checked against the file it came from. |
| `price_semantics.csv` | 6 | what each pack's price store says a *number* is: populated cells per column, and the class of the URL cited beside each cell (own-labelled / official-cited / third-party / repo reconstruction). |
| `claim_checks.csv` | 18 | each published claim tested against the file that should support it, with the arithmetic; verdicts are `consistent`, `check needed`, `CONTRADICTION`. |
| `cross_pack_conflicts.csv` | 10 | where two packs, or a board and the tree, disagree — side A, side B, what it changes, the action available. |
| `reject_guardrails.csv` | 12 | what may **not** be inferred from a page, and what not to conclude from a blank — the read-side equivalent of a test that fails on purpose. |
| `repo_findings.csv` | 10 | repository-wide structural findings with their measured numbers; `owner_decision` blank. |
| `flagged.csv` | 25 | everything a reviewer must look at before choosing: another pack's wrong value, clock precision, synthesis labelling, and every high/medium cross-pack conflict by id. |
| `sources.csv` | 35 | the two classes above, with url/host/read-on/hash for each register the board read. |
| `lions_status_check.csv` | 3 | the three rows the owner reported as blank: what the capture file holds, what the official page printed today. |
| `build_note.txt` | — | the build's own counts, so a stale page can be spotted against its registers. |

## How to check any row

```
python3 scripts/build_nfl_dfc0c1bc.py      # regenerate (deterministic: a rebuild changes no byte)
python3 scripts/check_nfl_dfc0c1bc.py      # rules 1-15: coverage, provenance, empty owner columns,
                                           # https-only, no price published, links, hashes, scope
python3 tests/test_nfl_dfc0c1bc.py         # identities: theme assignment, the ranking formula,
                                           # read-host checks, byte-for-byte determinism
```

Rule 15 re-hashes every register in `sources.csv`: if another pack edits its suggestions file, the hash
mismatch fails CI until this board is rebuilt, so the board cannot quietly quote a stale register.
Rule 13 fails the build if this branch touches a file outside its own scope — which is why corrections found
here (e.g. the wrong-club attribution in `nfl_8362b702`) are published as requests, not applied as edits.

## What this pack does **not** do

* It builds no model, no capture pipeline, and no price store — those are other packs' rows on the board.
* It does not own the requirements axis: `nfl_6ab24751` (81 readiness rows) and `nfl_48217a55` (74) do. This
  board reads their registers as evidence and never renumbers them.
* It publishes no price and no pick. That the six price stores hold no market number is reported as a
  measurement (`price_semantics.csv`), not as a price.
* It does not mark a row `verified` because another pack's CSV said so; inheritance is labelled `repo_claim`.
