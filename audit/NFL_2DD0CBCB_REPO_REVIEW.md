# Repository Review — session 2dd0cbcb (2026-11-19)

Scope: line-by-line structural review of `sassnarep3-star/Own6` at branch
`arena/2dd0cbcb-own6` (base `ffbbce6`), plus a second dated read of the official pages this
session owns (Week-12 venues, the injury-path behaviour, the November reserve window, three
club depth charts). Every claim below is either reproduced by a command run this session, or
linked to an official page read this session, or a pointer that the build asserts exists.
Nothing is inferred, and nothing in another pack's data was edited.

Baseline (from `scripts/audit_repo.py`, re-run at this branch's fixed point, after every file in
this PR existed; the same figures are recorded in `data/assurance/summary.json`):

| metric | value |
|---|---|
| files scanned | 1,371 |
| lines scanned | 139,193 |
| structured records | 20,201 |
| standing findings | 17 (4 open) |
| audit verdict | OK |

Note on these figures: `audit_repo.py` counts the tree as it finds it, so this PR's own pages and
registers are inside the count; the run above is the settled fixed-point state, not a partial one.
An earlier mid-session run at commit `4b4a592` reported 1,358 files / 136,775 lines / 20,164
records — kept here because it documents what the tree looked like before this pack's site existed.

## 1. Structure

- 21 `data/nfl_*` pack directories, 21 matching `docs/nfl-*` site directories (this session adds
  one to each). Cross-cutting dirs: `data/assurance`, `data/hub`, `data/empirical`, `data/nfl`.
- Per-pack triad: `scripts/build_nfl_<id>.py`, `scripts/check_nfl_<id>.py`,
  `tests/test_nfl_<id>.py`, `.github/workflows/nfl-<id>-ci.yml`. 29 workflows exist for 21 packs;
  `3b81013c` has the triad but **no workflow** (RF2-02).
- 40 directories under `docs/` (this pack's `nfl-2dd0cbcb/` included; 39 before it); the hub (`docs/index.html`) links 16 pack ids while the root
  landing (`index.html`) links 14 — the navigation drift recorded as RF-02 by session dfc0c1bc
  is still live at this base commit (RF2-01).
- The `tools/` harness (`tools/run_tests.py`, `tools/release_gate.py`, `tools/hub_reference_gate.py`,
  `tools/build_review.py`) is the stdlib-only entry point; `pytest` is not installed in this image
  (RF2-06).

## 2. Gates executed this session

| gate | command | result |
|---|---|---|
| repo audit | `python3 scripts/audit_repo.py` | OK — 1,371 files, 139,193 lines, 20,201 records, 17 findings |
| unit harness | `python3 tools/run_tests.py` | **194/194** (four separate runs) |
| site structure | `python3 scripts/check_site.py` | OK: data rules pass; 9 pages, no broken internal links, all external links https |
| nfl pack | `python3 scripts/check_nfl.py` | nfl: 13 pages, 0 issues |
| release gate | `python3 tools/release_gate.py` | 0 issues across published HTML and tracked text |
| link/reference gate | `python3 scripts/linkcheck.py` | pages=7 links=322 data_rows=240 rows_with_source=240 — PASS |
| source coverage | `python3 scripts/source_coverage.py --check` | pass (manifest `ccd7acb2…`) |
| cross-pack board | `python3 scripts/check_nfl_dfc0c1bc.py` | **OK — 15 rules, 0 failures** · registers 31; suggestions 209; questions 196; paths 16; gaps 13; reads 11; flags 26 |
| this pack | `python3 scripts/check_nfl_2dd0cbcb.py` | OK — 19 rules, 217 data rows, 6 pages |
| this pack tests | `python3 tests/test_nfl_2dd0cbcb.py` | 27 tests pass |

Two gates were **red** at intermediate points, and both were symptoms of ordering rather than of
content — recorded here because the next session will hit the same thing:

1. `python3 scripts/check_assurance.py` → `FAIL - legacy unverified count missing from overview`
   while `audit_repo.py` had already regenerated `data/assurance/*` and `build_assurance.py` had
   not yet rebuilt the pages.
2. `tests/assurance/test_audit.py::test_inventory_hashes_and_line_counts` failed in an isolated
   pytest run (720 passed, 1 failed) after files were added following an audit run: the committed
   inventory no longer hashed the tree. Running the audit again (i.e. completing the fixed point)
   makes it pass. The gate works; skipping it does not stay quiet.

## 3. Irregularities in the repository (each with a link, none auto-fixed)

Machine-readable copy: `data/nfl_2dd0cbcb/repo_findings.csv` (11 rows, all `blocks_merge=no`).

1. **Hub vs landing inventory drift** (RF2-01) — hub links 16 pack ids, landing links 14; hub-only
   `309921cc, a411fed0, f4, market`; landing-only `e5e38f9e, wk`. Two decision surfaces, two
   inventories. → [`docs/index.html`](https://github.com/sassnarep3-star/Own6/blob/main/docs/index.html)
2. **A pack with no CI** (RF2-02) — `3b81013c` has build/check/tests but no workflow, so its gates
   never run on push. → [`.github/workflows/`](https://github.com/sassnarep3-star/Own6/tree/main/.github/workflows)
3. **Dangling evidence pointer in a readiness register** (RF2-03) —
   `data/nfl_6cefc476/announced_starters.csv` does not exist; the file is at
   `data/nfl_48217a55/announced_starters.csv`. 32 of 33 pointers in that register resolve.
   → [`data/nfl_a67ddef8/requirements.csv`](https://github.com/sassnarep3-star/Own6/blob/main/data/nfl_a67ddef8/requirements.csv)
4. **Dead page reference** (RF2-04) — `docs/nfl-a67ddef8/flagged.html` is cited by a register; the
   page that exists is `flags.html`.
5. **Fixed-point ordering is load-bearing** (RF2-05) — see §2 items 1–2.
6. **Test counts are environment-dependent** (RF2-06) — no `pytest`, no `numpy` in this image;
   `tests/empirical` cannot even be collected under a bare venv pytest. Quote the harness
   (194/194) with its environment, not a bare number.
7. **Consolidation is filename-driven** (RF2-07) — `src/nfl_dfc0c1bc/registers.py` matches stems
   (`questions.`, `open_questions.`, `decision_questions.`, `suggestions.`, `site_suggestions.`), so
   108 rows of real owner-facing registers in other packs (`0ce967db/desk_questions.csv` 22,
   `0ce967db/desk_suggestions.csv` 18, `0d4da02c/suggestion_options.csv` 68) never reach the board.
   This pack therefore publishes `questions.csv`/`suggestions.csv` and the growth was measured
   (188→196, 197→209). → [`src/nfl_dfc0c1bc/registers.py`](https://github.com/sassnarep3-star/Own6/blob/main/src/nfl_dfc0c1bc/registers.py)
8. **No scheduled runner anywhere** (RF2-08) — 29 workflows, none with `on: schedule:`;
   `daily-verify.yml` has no cron block. Any "we snapshot every Wed/Thu/Fri" claim would be false
   today, so this pack leaves those requirement rows open instead of closing them.
   → [`.github/workflows/daily-verify.yml`](https://github.com/sassnarep3-star/Own6/blob/main/.github/workflows/daily-verify.yml)
9. **A root file whose name invites misuse** (RF2-09) — `data/team_ratings_2026-27.csv` contains NBA
   teams. Requirement R27 states explicitly that it is not counted as NFL evidence.
10. **Four standing findings remain open** (RF2-10) — `A-F11` (verify_data checks internal
    consistency while labelled source verification), `A-F12` (legacy correlations lack
    qualification evidence), `A-F14` (statute body not reproduced), `A-F15` (**no LICENSE file in the
    repository** — a rights question only the owner can settle).
    → [`data/assurance/findings.csv`](https://github.com/sassnarep3-star/Own6/blob/main/data/assurance/findings.csv)
11. **Shallow clone breaks the audit** (RF2-11) — `audit_repo.py` reads base-commit blobs; on this
    branch `git rev-parse --is-shallow-repository` was `true` until an unshallow fetch this session.

## 4. What the second dated read changed in the registers

These are the *upstream* findings this pack is responsible for (details and hashes in
`data/nfl_2dd0cbcb/`, rendered at `docs/nfl-2dd0cbcb/`):

- **Week-12 venues: 16 of 16 captured** from game-centre `Location`/`Stadium` fields, with the
  schedule page's hotel param published as a labelled cross-check. Three differ after
  normalization (Acrisure vs Heinz, Reliant vs NRG, EverBank vs TIAA Bank Field); one differs only
  in punctuation (U.S. Bank vs US Bank). A prior session captured 1 of 16.
- **`/injuries/league/2026/reg12` does not 404 — it serves the Week-11 page**, with Week 11's own
  title and a selector that ends at WEEK 11. Any fetcher trusting the URL would have written
  Week-11 rows under a Week-12 date. All 16 Week-12 game centres separately said the injury report
  "is not available at this time", so the two facts corroborate each other.
- **Reserve-list November window is 25 rows over 11/10–11/18 at both of today's clocks**, with no
  intra-month pagination (month tabs only). The render-window question therefore stays open, and
  the probe the prior session asked for is now instrumented per read.
- **Arizona's depth chart prints Carson Beck at QB1 and does not print Jacob Brissett at all**, which
  corroborates a move a prior session could only leave blank-and-flagged. The same page omits
  Gardner Minshew while a Week-12 game centre still shows him as the Cardinals' season passing
  leader — published as a contradiction (`2DD-F04`), not resolved.
- **Houston is still an image-only depth chart** (third consecutive session) and **Green Bay's footer
  still reads "Unofficial, Nov. 10, 2026"** (unchanged since the 09:01Z read). The brief's "fix the two
  parsing failures before widening coverage" gate is recorded as 1-of-2, with the strip-then-keep-raw
  fix demonstrated in this pack's own depth evidence.
- **The Thursday game table agrees with the morning read row for row** (26 rows, 16 game statuses,
  IND 9 / HOU 7). A zero-change delta published as a zero.

## 5. Verdict

No blocking defect found in the repository, and nothing in this review needed a fix outside this
pack's scope: 194/194 unit tests, 15/15 board rules, 19/19 pack rules, release gate and link gates
clean, audit OK. The eleven repository findings and ten upstream flags are published with links and
`needs review` semantics — they inform the owner rather than stopping the merge. The five
owner-decision gates (price policy, private/public split, alerting channel, depth-source route,
historical archive rights) remain the only items whose next move is not a session's to make.
