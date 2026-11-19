# NFL 0fef3044 — Executive Summary (Week-11 official injury-hub capture)

**Date of evidence:** 2026-11-19 (reads after 12:09:34Z, UTC). **Scope:** one dated, reconciled capture of the official Week-11 injury report, plus flags. **Not betting advice.** Nothing here is a probability, price, pick, or edge.

## What changed today

- The official Week-11 injury report is live. The 2026-11-18 read in this repo still showed Week 10 (`data/nfl_0ce967db/raw/injury_hub_read_2026_11_18.txt`); today's reads show Week 11.
- Captured: 13 games, 26 clubs, 253 player rows, 2 clubs with "No Injuries Reported" (CIN, WAS).
- Designations on this read: **9 Out and 7 Questionable, all on the Thursday game (IND@HOU)**. Every other Game Status cell is blank. Blank means blank: nothing was filled in.
- Six clubs (ATL, CLE, GB, LA, NE, SEA) have no table. The official schedule read lists them as bye clubs.

## Verification

| Check | Result |
|---|---|
| Row-level cross-read against the independent 11:07Z same-day read (session ade166a4) | 253 of 253 player rows match exactly |
| Pairings and kickoffs against the official Week-11 schedule read | 13 of 13 match |
| Six absent clubs against the schedule bye list | identical |
| Parser drift alarm (fields, team blocks, game count, club count, status vocabulary) | passes |
| Unit tests / checker | 10 unit tests; checker passes (regenerated outputs byte-identical) |

**Limits.** The sandbox has no shell route to nfl.com, so the text was read through a page-fetch tool. There is no hash of official bytes, and the read time is "after 12:09:34Z". The capture log says this and does not invent a hash.

## Sources (official, read 2026-11-19 unless noted)

- Injury report, Week 11: https://www.nfl.com/injuries/league/2026/reg11 (also https://www.nfl.com/injuries/)
- Week-11 schedule (read 2026-11-18 by session 0ce967db): https://www.nfl.com/schedules/2026/by-week/week-11
- Independent same-day read: `data/nfl_ade166a4/injuries_reg11_b.csv`, which cites the same official URL.

## Flagged for review (open, non-blocking)

Full list with source links: [`docs/nfl-0fef3044/flagged.html`](docs/nfl-0fef3044/flagged.html).

1. **Jaylen Waddle under DEN, not MIA** (carry-forward ADE-F01). This read matches earlier reads. No official trade row was found, so the club is not resolved here.
2. **Six clubs absent from the report.** Matches the schedule's bye list, but the injury page itself does not state "bye".
3. **Kerby Joseph, Cade Mays and D.J. Reed have blank Game Status** on the Week-11 report. Their Week-10 Out status belongs to a different week and is not carried forward.
4. **Capture precision:** no official bytes and no exact fetch time (see Limits).
5. **Name display vs. profile-link slug** differ for Jacob Hummel and Dee Alford. Displayed names are used.

## What this does not do

This pack covers one capture. It does not establish daily or Wednesday–Friday history, practice-status trends, snap counts, depth charts, inactive lists, or model results. Those items remain open in the existing packs and in the requirements ledger (`data/nfl_0ce967db/requirements.csv`). As of that ledger's last update, 43 of its 96 rows were met, 24 partially met, 19 blocked, 4 not run, 5 rejected, and 1 out of scope. Market prices remain blank by policy because no official source prints them.

## Where to look

- Week-11 capture: [`docs/nfl-0fef3044/index.html`](docs/nfl-0fef3044/index.html)
- Flagged for Review: [`docs/nfl-0fef3044/flagged.html`](docs/nfl-0fef3044/flagged.html)
- Raw transcription and hash: `data/nfl_0fef3044/raw/injury_hub_week11_read_2026_11_19.txt`, `data/nfl_0fef3044/capture_log.csv`
- Coordination record: [`COORDINATION.md`](COORDINATION.md) (session arena/0fef3044-own6)
