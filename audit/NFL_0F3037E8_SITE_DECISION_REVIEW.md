# NFL portal decision-review route — site audit

**Session:** `arena/0f3037e8-own6` · **Review date:** 2026-11-19 (UTC)
**Scope:** the root landing-page Suggestions section, its cross-pack summary, the legacy `docs/` hub summary, the README entrypoint, and the DFC0 decision-board register counts. This is a portal/freshness review, not a new NFL data capture or a full independent fact audit of every historical pack.

## Executive finding

The repository already has a dedicated cross-pack review board at [`docs/nfl-dfc0c1bc/`](../docs/nfl-dfc0c1bc/index.html), with pages for suggestions, questions/answers, information gaps, decision paths, sources and flags. The root NFL portal also has a Suggestions section, but it links only the Origination and NFL Week queues rather than the consolidated board. Its separate workspace blurb, and the legacy `docs/` hub card, still show superseded totals (159 suggestions / 176 questions). The current committed registers contain 197 suggestions and 188 question rows; the board's generated index exposes those totals. The README's Start-here list also lacks a direct cross-pack board entry.

Session `0050c939` integrated shared root/README changes in PR #123. At the time of this review's final handoff, open PR #125 (`arena/51698d74-own6`) owned the overlapping shared `index.html`, `docs/index.html`, `README.md` and source-coverage integration scope. Per the task-ownership rule, this session did **not** edit those shared files. The requested updates were posted to PR #125 and recorded in `COORDINATION.md`. The root landing's existing Suggestions section remains usable, but its consolidated-review route and summary counts still need the owner-scoped integration update.

The totals are **repository record counts**, not official NFL facts, prices, results, model outputs, correlations, skill or proof of an edge. No NFL data or strategy was newly verified or changed. Owner-choice fields remain blank; no suggestion was implemented.

## Checks performed and evidence boundary

- Read `COORDINATION.md` before work; reviewed the current root landing, `docs/index.html`, README entrypoint, DFC0 generated index, register dictionary, source index and the CSVs used for counts.
- Counted records with Python's CSV reader from the committed DFC0 files: 29 rows in `suggestions_inventory.csv`, 197 in `suggestions_master.csv`, 188 in `questions_master.csv`, 13 in `information_gaps.csv`, 16 in `decision_paths.csv`, and 40 in `sources.csv`.
- Ran `scripts/check_nfl_dfc0c1bc.py` before this session's portal/coordination edits: 15 rules, 0 failures. After this session added its coordination/workflow entries, the DFC0 builder reported repo-stat-dependent changes in four DFC0-generated files. Those out-of-scope generated changes were restored locally and are not included here. The cross-pack freshness handoff is recorded in `COORDINATION.md`; PR #123 later merged its own generated DFC0 corrections, which are retained during rebase.
- This session did **not** fetch an official page anew. Archived source-read links and timestamps remain in DFC0's source ledger; a link indicates where a reviewer can check a fact, not that this session reverified it.

## Findings and disposition

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| U-F01 | The root Suggestions section does not directly link to the consolidated cross-pack suggestions, question/answer, gap and decision-path pages. | The portal's `#suggestions` links to the Origination and NFL Week queues; the DFC0 review board is linked separately farther down the workspace map. | **Needs review / handed off:** open PR #125 (`arena/51698d74-own6`) owns the shared landing/docs-index integration. The request to add the consolidated board as a direct Suggestions CTA while retaining pack-specific queues was posted at [PR #125 comment](https://github.com/sassnarep3-star/Own6/pull/125#issuecomment-7007574833). No root edit made here. |
| U-F02 | Static cross-pack totals on the root workspace summary and legacy `docs/` hub are stale. | Those summaries say 159 suggestions / 176 questions. The current committed CSV row counts are 197 / 188; the register inventory has 29 rows. | **Needs review / handed off:** open PR #125 owns the root portal, `docs/index.html`, README and shared integration. The request to refresh the figures from the registers was posted in the [PR #125 handoff](https://github.com/sassnarep3-star/Own6/pull/125#issuecomment-7007574833). These shared files were not edited here. |
| U-F03 | DFC0's own README and executive summary still contain superseded totals. | `data/nfl_dfc0c1bc/README.md` reports 26 inventory rows, 159 suggestions, 176 questions and 35 source rows; `NFL_DFC0C1BC_EXECUTIVE_SUMMARY.md` repeats 159 / 176. Current CSVs count 29, 197, 188 and 40 respectively. | **Needs review / not edited:** these are DFC0 pack-owned files. The owning integration should refresh the documentation from the current registers. |
| U-F04 | The DFC0 builder rewrites repo-stat-derived output when the repository tree changes. | In the working tree, `scripts/check_nfl_dfc0c1bc.py` reported changes to `data/nfl_dfc0c1bc/flagged.csv`, `data/nfl_dfc0c1bc/repo_findings.csv`, `docs/nfl-dfc0c1bc/flagged.html`, and `docs/nfl-dfc0c1bc/repo-review.html` after coordination/workflow additions. | **Needs review / not edited:** the four generated files were restored; none is included in this pack. The owner/final integrator should re-run that pack's builder and checker on the merged tree. |
| U-F05 | The consolidated row count is not evidence that each inherited suggestion/question is an official NFL fact or has been freshly re-read. | DFC0 distinguishes inherited `repo_claim` rows from `read_this_session` official reads; the totals themselves are arithmetic over repository CSV rows. | **Boundary published here:** this report and the checker label totals as repository counts. The existing DFC0 source and flagged pages remain the place to inspect source-read scope and unresolved claims. |

## Manual source-review links

These URLs are archived in `data/nfl_dfc0c1bc/official_reads.csv` as 2026-11-17 reads. They are provided for manual review; **they were not re-read by this session** and do not support the repository-count figures above.

- [NFL injury report](https://www.nfl.com/injuries/) — archived read R1; weekly injury-report content and designation cells.
- [NFL Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) — archived read R5; fixture/date/time text.
- [NFL Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) — archived reads R10–R11; schedule/final/bye text, not market prices.
- [Packers official club depth chart](https://www.packers.com/team/depth-chart) — archived read R4; the board flags grouped/empty slots and its dated unofficial label.
- [Texans official club depth-chart route](https://www.texans.com/team/depth-chart) — archived read R9 recorded a 404 at the time; that is not evidence of a current route or data availability.
- [DFC0 archived source/read register](../data/nfl_dfc0c1bc/official_reads.csv) · [DFC0 source index page](../docs/nfl-dfc0c1bc/sources.html) · [Flagged for Review](../docs/nfl-dfc0c1bc/flagged.html).

## Regression gate

`python3 scripts/check_nfl_0f3037e8.py` reads the five committed registers, pins their expected counts, and verifies that the DFC0 generated index states the counts and directly links to its suggestions, questions, gaps and decision paths pages. It also reports—but does not fail on—landing-page discoverability/stale-counter findings owned by another session. The checker performs no network requests and verifies no NFL facts. Its tests are in `tests/test_nfl_0f3037e8.py`.
