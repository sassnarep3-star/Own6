# NFL decision gate — executive summary

**Session `0d4da02c` · branch `arena/0d4da02c-own6` · base `aa82798` · official reads 2026-11-18**

Live site: <https://sassnarep3-star.github.io/Own6/docs/nfl-0d4da02c/>

---

## 1. What this pack is

The owner's 2026-11-18 brief contains **75 product requirements and 8 process instructions**. Prior
sessions each registered suggestions and questions *as those sessions wrote them*. This pack does
the one thing none of them did: it takes **the owner's own bullet list as the authoritative row
set**, ties each bullet to what the repository actually contains at a named commit, and returns a
**decision-readiness table** — one row per requirement, the gate that blocks it, and the number that
would clear it — plus a **suggestions section with review-before-implement decision columns** and a
**questions / information / answers register** with a discovery route for every gap.

Everything published here is either (a) read this session from an official page, (b) inherited from
another pack and labelled `repo claim`, or (c) blank and flagged. Nothing is inferred.

## 2. Where the programme stands

| Status | Count | What it means |
|---|---:|---|
| blocked | 32 | a named gate blocks it; the clearing number says what removes the block |
| structural | 18 | schema or code exists; the data it needs does not |
| cleared | 17 | verified this session against an official page |
| cleared_repo | 5 | prior pack verified it; inherited as a claim, not upgraded |
| partially cleared | 4 | one leg available, the other not |
| open | 3 | no evidence either way |
| rejected | 2 | the owner rejected the approach; recorded so it is not re-proposed |
| needs review | 1 | published with a provenance caveat |
| in progress | 1 | the PR/merge step |

**Three gates decide almost everything else:**

1. **G-PRICE — no official market-price source exists.** Until one does, the residual, closing line
   value and the vig decomposition cannot be published, and neither can any backtest that uses
   prices. The owner's own ordering rule (R-20) says decide the price policy *first*.
2. **G-DEPTH-SRC — no depth-order source is verified for all 32 clubs.** Fourteen requirements sit
   behind this, including the whole backup-deficiency feature. The owner ordered this resolved
   *before* the feature is built, and that order is respected: the feature is not built.
3. **G-INACT — no official inactive list has been captured.** The injury register is now verifiable
   weekly, but "did the player actually play" is unanswerable, so *Questionable* cannot be
   calibrated and no designation may become a model feature.

## 3. What this session verified from official pages

All four reads were taken on **2026-11-18** and are logged with the requested URL, the canonical URL
the page resolved to, and a SHA-256 of the exact text transcribed (a tamper check on the committed
data — not a fingerprint of the page's own bytes; that caveat is published as flag F-17).

| Source | What it gave us |
|---|---|
| <https://www.nfl.com/injuries/> | **347 injury rows across 28 clubs** for Week 10, re-read and re-published |
| <https://www.nfl.com/schedules/2026/REG11/> | **13 Week 11 fixtures + 6 clubs on bye** (26 + 6 = 32), with kickoff times, networks, records, venue text and the league's own scheduling statement verbatim |
| <https://www.nfl.com/injuries/league/2026/REG11/> | **the Week 11 injury report is not published** — the request resolves to the Week 10 page |
| the injury hub's news rail | **19 dated official announcements**, including starter changes |

### Findings that close or move owner-reported defects

- **R-48 is cleared.** The three Lions designations the owner reported as blank
  (Kerby Joseph, Cade Mays, D.J. Reed) now read **Out**, each with *Did Not Participate*. The defect
  is no longer present on the live page.
- **R-42 is partly cleared.** Dated official starter announcements exist for **Drew Lock** (SEA),
  **Kyle McCord** (MIA), **Deshaun Watson** (CLE) and **Carson Beck** (AZ). **No dated Brissett
  announcement appeared**, so that row is left blank rather than filled.
- **R-49 is cleared.** The Week 10 tables are re-captured: 347 rows, 28 clubs. CHI, DEN, PHI and TB
  have no section — a **bye-week presentation, not a clean bill of health**, published as absence.
- **R-24 is cleared for what the page actually carries.** The schedule page prints a standing
  "2026 TBD Games" block for Weeks 16–18. It is a **procedure note, not a dated announcement**, and
  it does not name the designated matchups. That distinction is flagged rather than smoothed over.
- **R-14 is cleared.** Thirteen fixtures of fixture-context features, restricted to facts the
  official page prints: date, kickoff, network, venue, records. No derived rest days or travel.

### Numbers published with n (from official counts only)

347 rows: **176 blank game status · 90 Questionable · 70 Out · 11 Doubtful**. Of the 70 Out, 62 did
not practise at all; of the 90 Questionable, 46 were limited and 34 were full participants. That
spread is exactly why the owner asked for empirical calibration instead of remembered percentages —
and why the table stops there: **no play rate and no correlation is published**, because the outcome
leg does not exist. That is recorded, not hidden (`designation_calibration_status.csv`).

## 4. The decision board

- **30 suggestions**, each with **2–3 option paths** (68 paths total), each path with its cost, its
  risk, the evidence it needs and the number that clears it.
- **28 questions** with what we have, what we lack, the answer where an official source closes it,
  and the discovery route where it does not. **8 of 28 are answered** by an official source read
  this session (6 fully, 1 with a conflict flagged, 1 for counts only); 6 are partly answered,
  5 are unanswered, 4 rest on inherited claims this session did not re-verify, 2 were not
  attempted, and 2 need the owner's decision. The rest are blank by design
- **22 information gaps** with the acquisition route and the clearing number for each.
- **26 flagged items** on the Flagged for Review page, with source links. None blocks the merge.

The **decision columns are blank**. That is the contract: the owner picks the path before anything
is implemented. Nothing in this pack has been implemented on the owner's behalf.

## 5. Repo review (computed, not asserted)

Scanned **1,166 tracked files** at the pinned base. Headline irregularities:

- Data CSVs whose header carries **no source-like column at all** — contrary to the requirement
  that every table row carry a source link.
- **18 parallel NFL data packs and 18 matching site directories**, with up to 23 separate files
  registering the same concept under different column vocabularies (23 `depth*`, 18 `flagged*`,
  15 `suggestions*`, 15 `injury*`).
- **13 published pages contain interactive controls**, which the brief forbids.
- **One broken internal link**: `docs/dashboard.html` → `lab/`, and `docs/lab/` has no
  `index.html`.
- **Five committed files over 1 MB**, the largest an 11 MB coverage table and a 9.8 MB audit page.

## 6. What is deliberately missing

No prices. No odds. No correlation between a designation and playing. No leaderboard rows. No
statement that any strategy is profitable. Those cells are blank because the evidence does not exist
yet, and filling them is the exact failure mode this project exists to avoid.

## 7. Artifacts

| Path | Contents |
|---|---|
| `data/nfl_0d4da02c/` | 25 CSVs: capture, register, gates, suggestions, options, Q/I/A, gaps, flags, repo review |
| `src/nfl_0d4da02c/` | `capture.py` (as-read transcription), `register.py`, `analysis.py`, `decisions.py`, `flags.py`, `repo_review.py` |
| `docs/nfl-0d4da02c/` | 14 pages, the landing page being the decision-readiness table |
| `scripts/build_nfl_0d4da02c.py` · `scripts/check_nfl_0d4da02c.py` | deterministic renderer and 10-rule verifier |
| `tests/test_nfl_0d4da02c.py` | 24 tests (verifier, identities, determinism) |
| `audit/NFL_0D4DA02C_REPO_REVIEW.md` | the line-by-line repo review |

Verification at the time of writing: verifier **26/26**, tests **24/24**, rebuild byte-identical.
