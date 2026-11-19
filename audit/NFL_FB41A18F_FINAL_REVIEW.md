# NFL final integration and release review — `fb41a18f`

**Review date:** 2026-11-19 (UTC)
**Reviewed merged-tree commit:** `551f292682793bc9231e2b98abf3c0883cb0f929` (`main`, PR #145)
**Review branch:** `arena/fb41a18f-own6`
**Scope:** Read-only review of the merged NFL portal, shared-hub navigation, source/evidence boundaries, the in-flight landing-page integration PR #135, and repository-wide release checks. No shared landing page, pack data, model, or pack site was edited.

## Executive summary

The deployed root NFL portal, the merged `d6a947cb` pack, and the standalone `cdf86c07` pack are reachable. A local-path scan found **no missing relative link targets** in either `index.html` (146 anchors) or `docs/index.html` (132 anchors). The release HTML gate reports 0 issues, and both site checkers pass their documented scopes. GitHub Pages build run [44524378266](https://github.com/sassnarep3-star/Own6/actions/runs/44524378266) succeeded for reviewed commit `551f292`; the Pages API reports `built`.

This is **not a green repository-wide release**. A serial full pytest run against a clean worktree at the reviewed `main` reports **838 passed, 2 failed, 6 subtests passed**. The two failures are the stale assurance inventory hash for `COORDINATION.md` and the DFC0 verifier: the merged DFC0 board has 515 rows while the discovered registers now have 542, leaving the 14 `d6a947cb` suggestions and 13 questions off the board. The DFC0 checker reports 46 problems before its rebuild; the rebuild changes 18 published outputs. The committed sitewide source-coverage snapshot also fails its explicit `--check` freshness test (454 generated pages / 43,961 table rows versus 445 / 43,642 committed). GitHub Actions for this same main SHA show failures in Assurance CI, DFC0, Lab CI, Verify site and engine, and Legacy parlay safety; Release integrity, the sitewide coverage workflow, and Pages deploy succeeded.

The latest merges have moved the specific DFC0 omission from the `cdf86c07` rows to the newly merged `d6a947cb` rows. PR #145 added the CDF S-01 theme override and regenerated shared outputs, but the final merged `551f292` tree also contains PR #144's D6 pack while its DFC0/source-coverage snapshots remain pre-D6. This is a fixed-point/integration ordering issue, not a reason to discard either pack's rows.

Two navigation/integration issues also need the shared integration owner: the merged `cdf86c07` pack is still not linked from the root portal, `docs/index.html`, or README; and the root decision-board card repeats the same `a67ddef8` link. PR #135 remains open and conflicting with current `main`; a current-tree merge simulation reports 34 content-conflict paths, including shared navigation and generated inventories. **I did not change or merge PR #135.**

**Disposition:** retain the current live site as a research portal, but do not treat the integrated repository as release-green or merge an integration change until the shared artifacts and cross-pack checks are reconciled and rerun. Nothing in this review certifies betting performance, prices, correlations, or the full set of previously published NFL facts.

## Review method and evidence boundary

- Rechecked the current merged local tree at `551f292`, including its `index.html`, `docs/index.html`, `README.md`, `docs/nfl-cdf86c07/`, `docs/nfl-d6a947cb/`, generated coverage/assurance inventories, and the relevant builders/checkers. PR #145 merged after the first review cut; the current results below supersede the earlier `bb18cec` snapshot.
- Scanned local anchor targets in the two shared landing pages. The scan establishes local path existence only; it does **not** establish external URL reachability or fragment-ID existence.
- Directly read the official NFL Week 11 schedule and standings pages listed below. I compared only the one cited schedule row. I did not independently re-transcribe all 13 games, all 32 standings rows, all injury reports, or the older packs' claim tables.
- A green structural checker, source host, capture hash, or internal arithmetic is not being treated as proof that an adjacent value is true. The repo-wide source-coverage tool itself labels its independent value-verification count as zero; that structural metric is not a claim that prior values are false.

### Official-source spot checks performed for this review

| Item | Direct official read | Result and limit |
|---|---|---|
| Week 11 IND–HOU row in `data/nfl_cdf86c07/week11_slate.csv` | [NFL Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) | The official page displayed Colts at Texans on Thu Nov 19 at 8:15 PM, PRIME, with IND 3–7 and HOU 3–6. This matches that one CSV row. It does not independently verify the other 12 schedule rows or any derived model output. |
| 2026 standings page cited by the pack | [NFL 2026 division standings](https://www.nfl.com/standings/division/2026/reg) | The live page included a standings table, but its heading rendered literal template tokens (`$year$ NFL $displayname$ Standings`). The pack already records this as CDF-01. I did not certify all standings values from this review. |

No official-source read in this review supplies a sportsbook quote, licensed price archive, player-depth ordering, or a measured prop/parlay correlation. Those values remain outside this review and must not be inferred from the two pages above.

## Findings

### F-01 · High — repository-wide tests and CI are not green

A serial run against a clean worktree at reviewed `main` using the pinned test dependencies produced **838 passed, 2 failed, 6 subtests passed**:

1. `tests/assurance/test_audit.py::test_inventory_hashes_and_line_counts` — the `data/assurance/inventory.csv` hash for `COORDINATION.md` does not match the current file (`7ca55650…` recorded versus `88702fd0…` actual).
2. `tests/test_nfl_dfc0c1bc.py::test_verifier_passes` — DFC0 rule 2 and rule 9 fail before the generated board is refreshed; 14 D6 suggestions and 13 D6 questions are missing, and 18 published DFC0 outputs change on rebuild.

On the same `551f292` commit, Actions also reported failures for [Assurance CI](https://github.com/sassnarep3-star/Own6/actions/runs/44524379187), [nfl-dfc0c1bc](https://github.com/sassnarep3-star/Own6/actions/runs/44524379148), [Lab CI](https://github.com/sassnarep3-star/Own6/actions/runs/44524379041), [Verify site and engine](https://github.com/sassnarep3-star/Own6/actions/runs/44524379055), and [Legacy parlay safety](https://github.com/sassnarep3-star/Own6/actions/runs/44524379270). The failed steps include the generated-assurance-committed check, the DFC0 build/committer check, the engine-test step, and test steps. The [Release integrity](https://github.com/sassnarep3-star/Own6/actions/runs/44524379274), [Sitewide source coverage](https://github.com/sassnarep3-star/Own6/actions/runs/44524378971), and [Pages build/deployment](https://github.com/sassnarep3-star/Own6/actions/runs/44524378266) checks succeeded. These are distinct gates: a working static deployment does not make the failed repo-wide checks green.

[PR #145](https://github.com/sassnarep3-star/Own6/pull/145) merged after the initial `bb18cec` review cut and added the CDF S-01 theme override. The present failures are after that merge and after [PR #144](https://github.com/sassnarep3-star/Own6/pull/144) added the `d6a947cb` pack; the report below reflects this newer tree. **Action for the integration owner:** refresh shared inventories and DFC0 output from the same current tree, then rerun the complete matrix before calling the repository release-green. This review did not change CI or other owners' files.

### F-02 · High — the cross-pack DFC0 board omits the newly merged D6 questions/suggestions and rebuilds differently

On a clean worktree at `551f292`, `python3 scripts/check_nfl_dfc0c1bc.py` reports **46 problems** before its own rebuild. Rule 2 finds the master board has 515 rows while the discovered registers have 542; the 27 missing rows are 14 suggestions (`S-01`–`S-14`) and 13 questions (`Q01`–`Q13`) from `data/nfl_d6a947cb/`. Rebuild checks also report 18 published DFC0 data/HTML outputs changed. This is the next cross-pack fixed-point miss after PR #145 added CDF's S-01 theme override; the CDF standalone verifier now passes, and the D6 standalone verifier also passes.

Relevant files are [`data/nfl_d6a947cb/questions.csv`](https://github.com/sassnarep3-star/Own6/blob/551f292682793bc9231e2b98abf3c0883cb0f929/data/nfl_d6a947cb/questions.csv), [`data/nfl_d6a947cb/suggestions.csv`](https://github.com/sassnarep3-star/Own6/blob/551f292682793bc9231e2b98abf3c0883cb0f929/data/nfl_d6a947cb/suggestions.csv), and [`data/nfl_dfc0c1bc/questions_master.csv`](https://github.com/sassnarep3-star/Own6/blob/551f292682793bc9231e2b98abf3c0883cb0f929/data/nfl_dfc0c1bc/questions_master.csv). The checker/build is self-mutating: after its rebuild has updated the worktree, it can pass, but that does not make the committed pre-build artifacts current.

**Action for the integration owner:** reconcile the board's declared inputs with the merged D6 registers, rebuild to a fixed point, and rerun DFC0's rule and determinism tests. Do not silently drop the D6 rows or mark them classified without a reproducible rule.

### F-03 · High — committed sitewide source-coverage artifacts are stale

`python3 scripts/source_coverage.py --check` exits 1 on a clean worktree at the reviewed merged tree. It calculates **454 pages and 43,961 table rows**, while the committed [`data/source_coverage/summary.json`](https://github.com/sassnarep3-star/Own6/blob/551f292682793bc9231e2b98abf3c0883cb0f929/data/source_coverage/summary.json) still records 445 pages and 43,642 rows. Eight generated artifacts are reported stale: `data/source_coverage/{rows.csv,pages.csv,summary.json}`, `docs/coverage/{index.html,pages.html,rows.html,flagged.html}`, and `audit/SOURCE_COVERAGE.md`. The nine-page/319-row delta is a freshness measurement, not a claim that any row value is false.

The current-tree [Sitewide source coverage Action](https://github.com/sassnarep3-star/Own6/actions/runs/44524378971) passed. The repo's coverage documentation states that CI's current-tree repeatability check does not enforce committed-snapshot freshness, so this pass does not contradict the local `--check` failure. The tool reports 0 independently value-verified rows; its official-link counts are structural coverage only.

**Action for the integration owner:** regenerate and commit these artifacts from the same merged tree after all pack/shared-page changes, then rerun `--check`. Preserve the published coverage gaps and the explicit non-verification caveat.

### F-04 · High — PR #135's shared integration is still unmerged and conflicts with current `main`

[PR #135](https://github.com/sassnarep3-star/Own6/pull/135) remains open at head `5b98902c7ce546a337abc82055b3f19b5a0093ce`; its displayed merge state is `DIRTY` / `CONFLICTING`, with only its `lab` check shown as passing. A merge-tree comparison against current `main` (`551f292`) reports **34 content-conflict paths**, including `COORDINATION.md`, `README.md`, `docs/index.html`, assurance/source-coverage outputs, and DFC0 board files/pages. The pack directory `docs/nfl-2dd0cbcb/` is not in the reviewed merged tree; I found no current shared-landing link to it. This is consistent with it still being an open PR, not a broken link in the currently deployed tree.

**Action for the integration owner:** rebase/reconcile the PR against the latest main, keep both sessions' work, regenerate generated inventories at the fixed point, then require the relevant checks to pass. I left all PR #135-owned pages untouched and did not merge it.

### F-05 · Medium — the merged CDF pack is not discoverable from the shared landing/navigation files

The eight-page `docs/nfl-cdf86c07/` pack exists on `main` and its direct Pages URL [loads](https://sassnarep3-star.github.io/Own6/docs/nfl-cdf86c07/?fb41a18f=551f292), but `index.html`, `docs/index.html`, and `README.md` contain no link to `docs/nfl-cdf86c07/index.html`. The current root portal therefore does not surface this merged pack (it now links the separate `d6a947cb` pack), and the secondary [`docs/index.html`](https://sassnarep3-star.github.io/Own6/docs/index.html?fb41a18f=551f292) still identifies itself as “NBA lines research dashboard” while listing mixed NBA/NFL workspaces. The CDF page is reachable directly; the issue is discoverability and context, not a missing file.

**Action for the integration owner:** decide whether/how to add the merged CDF pack to the shared NFL/workspace index and make the secondary hub's cross-project role explicit. Those shared landing files are under the active PR #135 integration scope and were not changed here.

### F-06 · Medium — 81 of 82 CDF requirement rows cite the same standings URL, even for unrelated claims

All 82 rows in `data/nfl_cdf86c07/requirements.csv` have a URL field, but **81** cite only the 2026 standings page and one cites the Week 11 schedule. Examples include CD-01 (opening/closing price snapshots), CD-06 (replacement depth), CD-25 (Game Books), and CD-53 (injury-report cadence); the cited standings page does not evidence those row-specific claims. A link being on an official NFL host is not the same as the linked content supporting the cell.

This finding does not assert those status/clearing-number cells are false. It records a claim-to-source mismatch against the user's source-evidence rule. See the [requirements register](https://github.com/sassnarep3-star/Own6/blob/551f292682793bc9231e2b98abf3c0883cb0f929/data/nfl_cdf86c07/requirements.csv), [official standings page](https://www.nfl.com/standings/division/2026/reg), and [official Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11).

**Action for the pack/integration owner:** retain only row-relevant official evidence; where the status or numeric clearing value cannot be supported by the cited source, leave it blank or keep it explicitly flagged for review. Do not substitute the official-host check for source-content verification.

### F-07 · Low — root decision-board card repeats the official-capture link

[`index.html` lines 266 and 268](https://github.com/sassnarep3-star/Own6/blob/551f292682793bc9231e2b98abf3c0883cb0f929/index.html#L266-L268) contain the same `docs/nfl-a67ddef8/index.html` link and same label twice in the Cross-Pack Decision Board card. It is a harmless duplicate target, not a broken route or data defect.

**Action for the integration owner:** remove one repeated anchor when reconciling the shared portal; not changed by this review.

## Navigation and live deployment checks

| Check | Result |
|---|---|
| Root `index.html` relative anchors | 146 anchors, 68 unique hrefs, 0 missing local targets |
| `docs/index.html` relative anchors | 132 anchors, 51 unique hrefs, 0 missing local targets |
| Root exact duplicate | `docs/nfl-a67ddef8/index.html` appears twice in the same cross-pack card |
| `docs/nfl-cdf86c07/index.html` | Exists and is deployed, but has no shared landing-page/README link |
| `docs/nfl-d6a947cb/index.html` | Exists and is linked by the root portal |
| `docs/nfl-2dd0cbcb/index.html` | Absent from merged tree while PR #135 remains open; no current merged-page link points to it |
| `python3 tools/check_site.py` | `STRICT PAGES: 13`, `ERRORS: 0`, `ADVISORY: 0` |
| `python3 scripts/check_site.py` | Pass: 9 pages, no broken internal links, external links use HTTPS |
| Live GitHub Pages API / deployment | `main:/`, status `built`; deployment run [44524378266](https://github.com/sassnarep3-star/Own6/actions/runs/44524378266) succeeded for `551f292` |

The local target scan does not validate URL fragments or make external HTTP requests. The link checkers' green status is not fact verification.

## Repo-wide checks (reproducible on a clean worktree at `551f292`)

| Command / check | Result |
|---|---|
| `python3 tools/release_gate.py` | PASS — 0 issues across published HTML and tracked text |
| `python3 tools/check_site.py` | PASS — 13 strict pages, 0 errors, 0 advisories |
| `python3 scripts/check_site.py` | PASS — 9 pages, no broken internal links, all external links HTTPS |
| `python3 scripts/audit_integration.py` | PASS — no committed merge-conflict markers; independent arithmetic checks in its declared scope pass |
| `python3 scripts/check_hub.py` | PASS — 12 pages, 335 source-linked rows, 0 structural errors; its note explicitly says link/blank checks are not fact verification |
| `python3 scripts/check_assurance.py` | PASS — 9 pages and 25,321 source-linked rows; the pytest hash/line-count test still fails for `COORDINATION.md` |
| `python3 scripts/check_nfl_cdf86c07.py` | PASS — standalone CDF verifier |
| `python3 scripts/check_nfl_d6a947cb.py` | PASS — standalone D6 verifier |
| `python3 scripts/check_nfl_ade166a4.py` | PASS — 17 rules |
| `python3 scripts/check_nfl_51698d74.py` | PASS — 21 rules |
| `python3 scripts/source_coverage.py --check` | **FAIL** — 8 stale committed artifacts; 454 pages / 43,961 rows generated versus 445 / 43,642 committed; see F-03 |
| `python3 scripts/check_nfl_dfc0c1bc.py` | **FAIL before rebuild** — 46 problems: 27 D6 rows absent and 18 generated outputs change; see F-02. The checker rebuilds output, so rerunning it against that mutated worktree can pass. |
| `PYTHONPATH=. .venv/bin/python -m pytest -q tests/` | **FAIL** — 838 passed, 2 failed, 6 subtests passed; see F-01 |
| `python3 tools/run_tests.py` | **FAIL** on the available system interpreter: 193/195; it cannot import `test_nfl_cdf86c07.py` because system Python lacks `pytest`, and its DFC0 rebuild-determinism test fails. GitHub's Verify site and engine run also failed on this step. |

`requirements-empirical.txt` pins the pytest/scientific environment. The pinned pytest run above was run serially from a clean temporary worktree; `.venv` is local and not part of this deliverable. The legacy `tools/run_tests.py` runner directly invokes test functions and is not a replacement for pytest fixtures; do not interpret its partial tally as a passing suite.

### Short navigation-scan reproduction

The counts above come from parsing `a[href]` in the two files and treating only scheme-less paths as local. Strip the fragment/query, resolve relative to the HTML file, and count a failure only when the resulting file does not exist. The scan deliberately does not test fragments or external reachability.

## Review-only recommendations (not applied)

1. Reconcile PR #135 against the current merged tree and regenerate shared outputs only after the final integration set is known.
2. Settle the DFC0 fixed point with the merged D6 registers included (or explicitly revise the board's documented input scope); require zero omitted rows and a deterministic second build.
3. Refresh the assurance inventory and source-coverage artifacts from the same tree; require the hash test and `source_coverage --check` to pass.
4. Link the merged CDF pack from the agreed shared landing page and clarify that `docs/index.html` is a cross-project index, not an NFL-only page.
5. Replace generic source links in the CDF requirement table with row-relevant evidence or leave unsupported values blank and flagged.
6. Remove the duplicate A67 link from the root card.

## Close-out

This review made no changes to `index.html`, `docs/index.html`, `README.md`, any pack's data/model/site, or generated shared inventories. The only deliverables are this review report and its append-only coordination record. The current live site is served from `main`; this session did not alter or deploy it. A report-only PR will be used to preserve the findings. **No merge is authorized by this report while the listed repository-wide checks remain failing.**
