# 48217A55 — Integrity log

Everything in this pack that is **wrong, uncertain, or incomplete**, in one place. The brief
requires that unconfirmable values stay blank and flagged rather than inferred; this file is
the working record behind that rule.

The published version of this list is
[`docs/nfl-48217a55/flagged.html`](../../docs/nfl-48217a55/flagged.html), driven by
`data/nfl_48217a55/flagged.csv`.

---

## A. Chunk-0 transcription verified — was open, now closed

`fetch_page` returns <https://www.nfl.com/injuries/> in eight chunks, and the transcription
in `capture.py` was made by hand. An intermediate working note in this session recorded that
**chunk 0 had never been fetched** — which would have meant the WAS, NYG, NE and DET rows
(Thursday and Munich games) were unsourced while the S1 row still claimed `chunks_read = 0-7`.

That note was wrong, and it is worth recording how the error was caught rather than quietly
fixing it: the claim in `capture.py` was checked against a fresh read of chunk 0 instead of
being taken on trust.

**Re-read 2026-11-15, chunk 0 diffed field-for-field against the transcription:**

| | |
|---|---|
| Rows compared (WAS 9, NYG 11, NE 15, DET 9) | 44 |
| Rows matching exactly | **44** |
| Field mismatches | **0** |

So chunk 0 *was* read, the `chunks_read = 0-7` claim on S1 is accurate, and those 44 rows are
verbatim. The page had also not changed between the two reads. Flag `48217-F14` is updated to
record this and now carries only the narrower open item: **chunks 1–7 were not re-read**, so
their completeness still rests on the surname-ordering check (every club's rows are in surname
order across the chunk joins — consistent with nothing being lost, but a consistency check
rather than a proof).

> Why this was verified rather than assumed: the brief's standard is that a value is either
> traceable to a page read in-session or it is blank and flagged. A row that is probably right
> is not the same as a row that is sourced — and a working note saying "never fetched" is not
> evidence either way.

## B. Irregularities in the official pages themselves

These are **facts about the sources**, not errors in the pack. They are published rather than
corrected, because "correcting" an official page's output would be fabricating a value.

| # | Irregularity | Handling |
|---|---|---|
| F02 | The Rams' injury table lists Aaron Donald and Myles Garrett | Published as printed; not deduplicated |
| F03 | The Seahawks' table lists Quenton Nelson, a guard, in a context implying a skill position | Published as printed |
| F04 | JAX BJ Green II is marked Full Participation and also Out | Both values published; the contradiction is the flag |
| F05 | JAX Jessie Bates and Jordan Davis are "Not injury related – resting player" | Excluded from injury counts, kept in the table with the reason shown |
| F07 | The by-week schedule page prints **no venue** | Week 10 venue cells are blank. 13 Week 9 venues *were* transcribed from the inactives page, which does print `WHERE` |
| F08 | The Chiefs' roster page links a depth chart on the club's own domain | Recorded as club-sourced and unverified for the other 31 clubs |

## C. Route probes that failed

| Route | Result |
|---|---|
| `nfl.com/teams/kansas-city-chiefs/depth-chart` | **HTTP 404**. NFL.com does not host per-club depth charts. This is why the depth feature is not built. |
| `nfl.com/teams/kansas-city-chiefs/roster` | Live, but publishes **no depth order** — only status codes (ACT / RES / DEV / CUT / PUP / TRD). |
| Any official price route | None exists. Four attempts are logged in `price_capture_attempts.csv` with what each page actually contained. |

## D. The reserve-list route is probably truncated

The reserve-list page's earliest November row is dated **11/07**, but an official NFL.com
story dated **2026-11-05** reports the Ravens placing Lamar Jackson on injured reserve, with
no corresponding row on the list. (`48217-F15`)

Two readings: the route paginates and the first page was missed, or the transaction was
posted under a different category. Either way **"absent from the reserve list" is not
established as "not on the reserve list"**, which weakens — but does not invalidate — the
pack's use of the list to close the "not listed means available" gap.

## E. Club attribution was spot-checked, not audited

Kenneth Walker III appears on the injury page under **Kansas City**. Reading the Kansas City
roster confirms he is on it, so the attribution held. (`48217-F13`)

**One row was checked. The other 346 were not.** A club-section misparse would corrupt the
per-club Out counts without any obvious symptom, so those counts should be treated as
provisional until the report is re-read.

## F. The capture is a snapshot of a page that was still moving

Nine of fourteen Week 10 games had gone final at capture time. Three were in progress and
two had not kicked off. The in-progress scores are published in a separate table, plainly
marked, and are never used as results.

Re-reading the official pages later will give different numbers. That is expected, and it is
why every table carries the capture date in its header.

## G. Repository-level findings

`REPO_FINDINGS` in `capture.py` records RF-01 … RF-13. The ones with the widest blast radius:

- **RF-10** — eight overlapping NFL packs now exist in this repository and nothing tells a
  reader which is authoritative. The decision-readiness table is this pack's answer to that,
  but the ambiguity is a repository problem, not a pack problem.
- **RF-11** — `scripts/audit_repo.py` pins a baseline commit (`86eca0f`). In a **shallow
  clone** it fails with `fatal: invalid object name`, which makes `data/assurance/inventory.csv`
  impossible to regenerate and turns `tests/assurance::test_inventory_hashes_and_line_counts`
  red. This is an environment artifact, not a repository defect — `git fetch --unshallow`
  fixes it, and CI checks out with `fetch-depth: 0`. Worth knowing before concluding the
  audit scripts are broken.

---

## Summary counts

| | |
|---|---|
| Flags published | 17 (`48217-F01` … `48217-F17`) |
| Blank cells across all 36 tables | 1,054 |
| …traced to a flag | all of them |
| …traced to a declared expected-blank reason | 12 tables |
| Blank cells with **no** trace | **0** — enforced by verifier rules 8 and 11 |
