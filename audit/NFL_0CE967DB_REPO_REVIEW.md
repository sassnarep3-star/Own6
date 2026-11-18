# Repo review — session 0ce967db (2026-11-18)

Scope: line-by-line review of what this session touched plus the NFL packs it must coexist with.
Findings that are not mine to fix are logged, not edited. Severity is about decision risk, not about
whether a file is tidy.

## Method

1. Full tree listing (1,220 tracked files), `git log`, open-PR list, Pages API status.
2. Read the coordination board's last three session records and every open claim.
3. Read the data registers this pack consumes: `data/nfl_7a59fd89/corpus_150.csv`,
   `data/nfl_7a59fd89/week10_finals.csv`, `data/nfl_67233566/results_feed.csv`,
   `data/nfl_67233566/standings.csv`.
4. Read the build/verifier pattern of the two nearest packs (`nfl_7a59fd89`, `nfl_dfc0c1bc`) so this
   pack's tooling is consistent with the repo's conventions instead of inventing a new style.
5. Ran the whole repository's test suite from a **complete** clone before and after this session.

## Findings

| ID | Kind | Finding | Severity | Handling |
|---|---|---|---|---|
| RF-01 | structural | 18 NFL packs, each with its own requirement ledger and id scheme (`RQ-`, `R-`, `T-`, `P-`, `D-`); >500 requirement rows and no single view | medium | this pack adds a per-bullet ledger but does not merge others |
| RF-02 | duplication | 16 suggestion registers and 10 question registers before this session | medium | this pack adds one of each, namespaced `desk_*`; merging others was out of scope |
| RF-03 | **data defect** | `data/nfl_7a59fd89/corpus_150.csv` writes the Rams as both `LA` (9 rows) and `LAR` (1 row). Per-club reconciliation failed 1/32 until repaired | **high** | repaired read-only in this pack with a declared map; source untouched |
| RF-04 | data hygiene | the same file stores a long prose note inside `event_mark_on_card` on the unsettled row | low | noted only |
| RF-05 | verified good | the inherited corpus reconciles exactly (6,923 PF = 6,923 PA) once the Monday game is settled | info | published on the evidence page |
| RF-06 | pattern | every prior pack publishes an empty leaderboard because no price exists — honest, but leaves the owner with no measured number at all | info | this pack publishes proper scores on official outcomes |
| RF-07 | risk | some earlier ledgers mark a requirement "met" when the artefact merely exists (a schema with no rows) | medium | this pack separates `blocked`/`not_run` from `met` and prints populated-row counts |
| RF-08 | verified good | pack builders are deterministic and offline | info | confirmed by rebuilding this pack twice and diffing |
| RF-09 | cross-session breakage | `src/nfl_dfc0c1bc/registers.py` globs `data/*/questions*.csv` and `data/*/suggestions*.csv` repo-wide and fails on foreign rows — it was already failing on two other sessions' files | medium | my registers renamed to `desk_*`; that pack's code untouched |
| RF-10 | environment | this sandbox's clone was **shallow**, so `scripts/audit_sources.py` could not read historical tree `77a28cc` and one dfc0c1bc determinism test truncated a long field on rebuild; both looked like `main` failures | medium | `git fetch --unshallow` → clean `main` is 170/170; CI uses `fetch-depth: 0` |
| RF-11 | process | `scripts/source_coverage.py --check` is stale after any merge that adds pages; the correct sequence is regenerate **after** the merge | low | done as the final integration step |
| RF-12 | honesty | prior packs' claim that "0 qualified strategies" is a property of the market (no price) understates the case: even with outcomes only, no candidate survives clustering | info | published with both the point estimate and the lower bound |

## What this pack refuses to do, on purpose

- No market price, from any source, labelled verified.
- No ROI, CLV or units, because none can exist without a price.
- No starter, replacement, snap count, depth rank or week-11 designation invented to fill a table.
- No retuning of the registration after seeing results; the one post-hoc idea is declared in
  amendment A1 and tested prospectively only.
