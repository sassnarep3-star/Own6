# NFL line-origination session b72e2687 — Executive summary

**Session:** `b72e2687` · **Branch:** `arena/b72e2687-own6` · **Base:** `ffbbce6` (origin/main)
**Read date:** 2026-11-19 · **Claim:** W1–W8 via `COORDINATION.md` (exclusive file scopes)
**Site:** `docs/nfl-b72e2687/` · **Verification:** checker 21/21 · regression tests 22/22

## 1. What this session did

Session `b72e2687` continued the evidence-first NFL line-origination program. It
**re-read and re-verified the official captures** from `nfl.com` and the club
sites on 2026-11-19, **re-tested every inherited irregularity flag**, **re-verified
the prior pack's published numbers** by independent arithmetic, and published a
**six-page decision dashboard** with a 79-row requirement inventory, a 16-row
flag register, a 12-row questions ledger, a 10-row suggestions review, and a
source register — each row linked to the official page it was read from.

It did **not** originate a single line with a market price, because **no official
NFL page publishes a market price**. The standing rule is: a value is published
only if it was read this session from the official page in its `source_url`,
logged with a UTC clock and sha256, or is arithmetic on such values with the
derivation shown. Everything else is a blank cell and a "Flagged for Review" row.
No profitability claim exists anywhere in this pack.

## 2. Verified captures (all read 2026-11-19 from official pages)

| Register | Rows | Re-verified finding | Official source |
|---|---|---|---|
| Standings | 32 clubs | W 149 / L 149 / T 2 (NYG, WAS); PF = PA = 6,923 (AFC 3,430 + NFC 3,493) | nfl.com/standings/division/2026/reg |
| Week-12 slate | 16 games | all matchups, kickoff times, networks and records match the prior pack; 2 heading/weekday contradictions reproduced | nfl.com/schedules/2026/by-week/week-12 |
| Week-11 injury register | 253 players + 2 markers | 13/13 games; practice tallies recomputed to DNP 83 / LP 87 / FP 83; exactly 16 published game-status cells, all Thursday IND@HOU | nfl.com/injuries/league/2026/reg11 |
| Reserve list (November) | 25 rows | window 11/10–11/18; fresh in-window rows present (Hutchinson 11/18) | nfl.com/transactions/league/reserve-list/2026/11 |

Capture discipline: `capture_log.csv` records each read with a **UTC clock** and a
**sha256 of the transcription artifact**; the hash covers the artifact only and
cannot prove what the page said at read time, which is an acknowledged evidence
boundary.

## 3. Re-verification outcome (15 rows, `reverification.csv`)

- **RV-01..RV-13: MATCH** — every prior-pack published number reproduced by
  independent re-read and/or re-arithmetic: standings totals, PF/PA, Week-12 slate,
  injury row counts and practice tallies, the 16 game-status cells, the reserve
  list, both game-centre stadium fields, the Packers depth-chart irregularity, the
  Texans image-only depth chart, the DEN@PIT "panels not available" reading, and
  game-centre records against standings.
- **RV-14: NOT_RECOMPUTABLE** — the realised 2026 home margin (−0.53) cannot be
  recomputed from the division standings page alone; it needs the official
  home/road results split. Recorded as an open data need, **not** a contradiction.
- **RV-15: CORROBORATED** — the 145-game settlement total is internally consistent
  with this session's standings read (298 decisions over 151 games incl. 2 ties);
  the game-by-game settlement was not re-derived from a single standings read.

## 4. Flags (16 rows, all non-blocking — `flagged.csv`)

**12 inherited flags (A67-F01..F12)** were re-tested on 2026-11-19
(`flag_recheck.csv`): **11 remain OPEN** (venue-name disagreement, legacy stadium
name, reserve-list window, IR players with blank game status, Lamar Jackson
window conflict, Texans image-only depth chart, Packers jersey prefixes + stale
footer, Week-12 heading/weekday contradictions, DEN@PIT unavailable panels, Rams
abbreviations, absence-inference policy, Wednesday blank game statuses), **1 not
re-tested** (cosmetic, A67-F10). New this session:

- **B72-F01 (fixed)** — the first hand tally of the injury register miscounted
  practice codes (LP 90/FP 80, 15 game-status cells); recomputation gave
  **LP 87 / FP 83 and 16 cells**; the corrected values are the published ones.
- **B72-F02 (open)** — the Week-12 schedule page carries **no venue fields at all**
  (venue names only appear in Marriott affiliate links); official venue
  transcription must come from game-centre Location/Stadium fields.
- **B72-F03 (open)** — the home/road results split is **not derivable** from the
  division standings page; the removal-of-luck recomputation needs the official
  split or the game-level results feed.
- **B72-F04 (open, low)** — the raw injury transcription mixes full practice text
  and bare codes in `practice_status`; the published `practice_code` column is
  consistent and its tallies recompute, so the register stays trustworthy.

**No flag blocks the merge.** All flags are published on the "Flagged for Review"
page.

## 5. Requirements, questions, suggestions (`requirements.csv` / `questions.csv` / `suggestions.csv`)

**79 requirements** — one row per brief requirement, each with a status, the
blocking gate, and the number that would clear it. Statuses: 33 satisfied, 2
policy-enforced (jersey-order depth inference and season-long-ROI ranking both
rejected by policy), 28 partial, 8 open, 1 needs-review.

The **biggest open blockers** (all evidence-bound, never filled by inference):

1. **Price-snapshot store / verified results feed (R02/R03)** — no official NFL
   page publishes market prices; a licensed archive is the only route to ROI.
2. **Correlations (R08)** — correlation values require paired graded outcomes
   under licence; all remain blank with `n` undefined.
3. **Depth verification (R07/R31/R51)** — Texans depth is image-only; a structured
   source or official snap-count feed is required before any backup-deficiency
   value is published.
4. **Game Books / inactives / snap counts (R26/R30/R55)** — no official
   game-day status document has been read this session; no inference performed.
5. **Questionable calibration (R43/R52)** — play rates per designation need
   seasons of designations joined to official inactive lists.
6. **2026 kickoff/onside-kick priors (R67)** — the rulebook read has not happened.

**12 questions** (Q/I/A ledger) name exactly what is needed to clear each
blocker, with the source required and a discovery path. **10 suggestions** are
review-only, each with a prerequisite; nothing is auto-implemented.

## 6. Rejected by policy (stays rejected)

- Deriving depth order from **jersey number, experience, or salary**.
- Ranking strategies by **season-long ROI**; the leaderboard ranks by
  benchmark-relative proper-score skill with game-cluster lower bounds and
  multiplicity adjustment.

## 7. Site and verification

`docs/nfl-b72e2687/` — **6 pages**: index (decision-readiness table + stat cards),
captures (standings, Week-12 slate, injury register, capture log), flags
("Flagged for Review"), reverification (15 rows with method and result),
registers (requirements / questions / suggestions), sources. Every table row
links to the official source it came from; unverified values are blank and
flagged.

`scripts/check_nfl_b72e2687.py` enforces **9 rules** (row counts, standings
arithmetic, practice tallies, source links, flag disposition, capture-log
clock/hash, broken internal links, no published prices, reverification
documentation): **21/21 PASS**. `tests/test_nfl_b72e2687.py` (22 tests) covers
every register's invariants, including that the capture-log hashes match the
raw artifacts on disk: **22/22 PASS**. CI runs the build + checker + tests on
every push (`.github/workflows/nfl-b72e2687-ci.yml`).

## 8. Evidence boundaries (honest limits)

- **No market prices** exist on official NFL pages, so no ROI/CLV claim is
  possible from official sources alone; the price-data policy (R21/Q01) is an
  owner decision that must precede any published backtest.
- The standings page carries **net points only** — home/road splits are not
  derivable (B72-F03).
- The Texans club depth page is **image-only**; Houston depth is unverifiable
  from official text.
- The 2026 rulebook, official Game Books, and official inactive lists were
  **not read this session**; no game-day status was inferred.
- Snap counts as a starter proxy have no official source yet.

## 9. Deliverables

| File | Purpose |
|---|---|
| `audit/NFL_B72E2687_REPO_REVIEW.md` + `data/nfl_b72e2687/repo_findings.csv` | W1 line-by-line repo review with source links and irregularities |
| `src/nfl_b72e2687/capture.py` + `data/nfl_b72e2687/raw/**` + `capture_log.csv` | W2 capture pipeline (hashed, timestamped) |
| `data/nfl_b72e2687/{standings_2026_11_19,week12_slate,injuries_reg11}.csv` | W2 registers (32 / 16 / 253+2 rows) |
| `data/nfl_b72e2687/flag_recheck.csv`, `reverification.csv`, `flagged.csv` | W3/W4/W5 flag and re-verification registers |
| `data/nfl_b72e2687/{requirements,questions,suggestions,sources}.csv` | W5 governance registers (79/12/10/14 rows) |
| `docs/nfl-b72e2687/` (6 pages) | W6 decision dashboard |
| `scripts/build_nfl_b72e2687.py`, `scripts/check_nfl_b72e2687.py`, `scripts/fix_nfl_b72e2687_csv.py` | W6 build + verification |
| `tests/test_nfl_b72e2687.py`, `.github/workflows/nfl-b72e2687-ci.yml` | W6 regression tests + CI |
| `NFL_B72E2687_EXECUTIVE_SUMMARY.md` | W7 this summary |
