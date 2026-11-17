# Repo review — session `ca1b3769` (2026-11-17)

Line-by-line review of the repository as it stood at `d844122` (merge of PR #107),
with what was checked, how, and what was found. Nothing here is a preference: each
item names the file, the value, and the official page it was checked against.

## Method

1. Enumerated every tracked file and every `data/nfl_*` dataset (16 NFL packs,
   ~13k CSV rows).
2. Read the official pages those packs cite, on 2026-11-17 UTC, through the
   page-fetch tool (see the transport note below), recording the clock time.
3. Re-tested every stored official value mechanically (`src/nfl_ca1b/verify.py`):
   971 rows, 0 contradictions.
4. Collapsed seven requirement registers (342 rows) into one (210 rows) and looked
   for status disagreements between packs.
5. Probed three routes the project depends on and previously assumed: club depth
   charts, the game-centre injury module, and a week-scoped injury-hub URL.

## Transport note (a finding in itself)

`curl` from this sandbox has **no route to nfl.com** (`HTTP 000`). The page-fetch
tool does reach `www.nfl.com`. This matters for two reasons: (a) every "verified"
claim in this pack rests on a tool-mediated read, with a clock time, and cannot be
reproduced by a CI job; (b) the repo's own `scripts/source_coverage.py` and
`tools/release_gate.py` allow-lists were flagged by three earlier sessions as missing
`nfl.com`, which is consistent with tooling that has never successfully fetched the
host.

## Findings

| # | Finding | Evidence | Severity |
|---|---|---|---|
| 1 | Week 10 moved under every pack: 9 finals at 2026-11-15T23:35Z → **13 finals** at 2026-11-17T00:41Z; only LAC@BAL is still scheduled | `data/nfl_8362b702/week10_nonfinal.csv` vs this session's read | expected drift |
| 2 | Four packs' standings snapshots predate the Sunday week-10 block but are internally correct; after adding back only the unseen games, **32/32 clubs reconcile** in each | `verification_standings.csv` | none — no error |
| 3 | Two packs' results feeds store a **live score** as if it were a result (SF 24-19 DAL; SEA 21-10 LV). Both label the row `in_progress` and exclude it from their corpus, so the pack is honest; the row is now stale | `data/nfl_67233566/results_feed.csv` | low — labelling is correct |
| 4 | `data/nfl_d966f630` stores IND **Arden Key** with `injury_text = 'Hamstring'`; the live page shows no injury and full participation. Sibling pack `s11` flagged exactly this row on 2026-11-15 and it was never corrected | `D966-INJ-161` vs SN-04 | medium — value is not replayable |
| 5 | Club codes differ between packs and the page (`ARI`/`AZ`, `LAR`/`LA`). Without an alias map this produces 5 **false** mismatches | `CLUB_ALIAS` in `verify.py` | none — nomenclature |
| 6 | The club depth-chart route **does not exist**: `nfl.com/teams/<club>/depth-chart` → 404 | probe P-01 | high — invalidates a workstream |
| 7 | The game-centre injury module is empty for week 11 ("not available at this time") | probe P-02 | medium |
| 8 | The injury hub still renders **WEEK 10** two days before week-11 kickoff; there is no week-11 report yet, and no week-scoped URL | SN-04, probe P-03 | expected |
| 9 | Six packs published **342 requirement rows** for what is **210 requirements**, using 25 status words; the worst disagreement kept 4 copies of one requirement | `requirements.csv` | medium — this is what the owner could not see |
| 10 | Venue names differ between two official surfaces for 3 of 13 fixtures; both strings are legitimate | `venues_week11.csv`, `conflicts.csv` CF-01..03 | none |
| 11 | Pack `nfl_s11`'s 347-row injury count and pack `48217a55`'s 279-row count cannot both describe one page; no session has transcribed all 8 chunks at one clock time | `conflicts.csv` CF-09 | medium — open |
| 12 | `data/nfl_market/standings.csv` uses `wins/losses/ties/points_for/points_against` column names, unlike every other pack (`w/l/t/pf/pa`), which silently breaks naive joins | file header | low |
| 13 | Every NFL pack's market/price columns are empty, correctly: no official source publishes a price. Confirmed again this session | all packs | none — policy |
| 14 | The repo carries 4 stale merged NFL packs with overlapping scope (`309921cc`, `3b81013c`, `6cefc476`, `nfl_market`, `nfl_f4`, `nfl_origination`) and 9 open PRs from 2026-11-05..11-14; none was touched by this session | `gh pr list` | low — housekeeping |

## What was NOT found

* No stored official value contradicts today's official page (0 of 971).
* No page publishes a price, so no pack's "market" claim is testable anywhere.
* No pack derives a depth rank from jersey number, salary or experience — every one
  that comes close says so and gates it.
* No leaderboard in the repo publishes a rank it has not earned; the ranks are blank
  in every pack that follows its own rules.

## Consequence for this session's scope

The review removed two pieces of planned work (depth charts, and any availability
claim naming a starter) and added one (the alias map, published as SG-02). Everything
else proceeded as claimed.
