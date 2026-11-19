# NFL final integration and release review — `fb41a18f`

**Review date:** 2026-11-19 (UTC)
**Reviewed merged-tree commit:** `68bda5a9b96c12338f7bdf415256afbb33e35de7` (`main`, PR #139)
**Review branch:** `arena/fb41a18f-own6`
**Scope:** Read-only review of the merged NFL portal, shared-hub navigation, source/evidence boundaries, the in-flight landing-page integration PR #135, and repository-wide release checks. No shared landing page, pack data, model, or pack site was edited.

## Executive summary

The deployed root NFL portal, the merged `d6a947cb` pack, and the standalone `cdf86c07` pack are reachable. A local-path scan found **no missing relative link targets** in either `index.html` (146 anchors) or `docs/index.html` (132 anchors). The release HTML gate reports 0 issues, both site checkers pass their documented scopes, and the current main-branch Actions matrix is green. A serial full pytest run at reviewed `main` reports **866 passed, 0 failed, 6 subtests passed**; `tools/run_tests.py` reports 201/201. GitHub Pages build run [44525910652](https://github.com/sassnarep3-star/Own6/actions/runs/44525910652) succeeded for `68bda5a`; the Pages API reports `built`.

The previously stale sitewide coverage snapshot has now been refreshed: `python3 scripts/source_coverage.py --check` passes on this tree (456 pages / 44,865 table rows). The standalone DFC0 check passes (15 rules, 0 failures), as do the CDF, D6, ADE, 51698, and 0fef pack checkers. GitHub Actions on the same main SHA all pass, including Assurance, Lab, DFC0, Verify site and engine, Release integrity, sitewide source coverage, and Pages deployment.

Two navigation/integration issues remain for the shared integration owner: the merged `cdf86c07` pack is still not linked from the root portal, `docs/index.html`, or README; and the root decision-board card repeats the same `a67ddef8` link. PR #135 remains open and its old branch has 34 conflicting paths against current `main`, including shared navigation and generated inventories. PR #146 was prepared against `551f292` and is now an older shared-inventory settle branch. **I did not change or merge either PR.**

**Disposition:** the deployed site, current GitHub Actions, repo tests, and checked-in source-coverage snapshot are healthy on `main`. PR #135 is not ready to merge until its conflicts are resolved and its checks rerun. Nothing in this review certifies betting performance, prices, correlations, or the full set of previously published NFL facts.

## Review method and evidence boundary

- Rechecked the current merged local tree at `68bda5a`, including its `index.html`, `docs/index.html`, `README.md`, `docs/nfl-cdf86c07/`, `docs/nfl-d6a947cb/`, `docs/nfl-0fef3044/`, generated coverage/assurance inventories, and the relevant builders/checkers. Main advanced from `188e904` after the prior re-review; the results below reflect the latest merged tree checked.
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

### F-01 · Resolved on current main — repository-wide test and CI status

After PR #142 and then PR #139 merged, a serial full test run against clean `main` at `68bda5a` reports **866 passed, 0 failed, 6 subtests passed**; `python3 tools/run_tests.py` reports **201/201**. The current main-branch Actions runs are green for [Assurance CI](https://github.com/sassnarep3-star/Own6/actions/runs/44525911096), [nfl-dfc0c1bc](https://github.com/sassnarep3-star/Own6/actions/runs/44525911300), [Lab CI](https://github.com/sassnarep3-star/Own6/actions/runs/44525911495), [Verify site and engine](https://github.com/sassnarep3-star/Own6/actions/runs/44525911110), [Legacy parlay safety](https://github.com/sassnarep3-star/Own6/actions/runs/44525911406), [Release integrity](https://github.com/sassnarep3-star/Own6/actions/runs/44525911155), [Sitewide source coverage](https://github.com/sassnarep3-star/Own6/actions/runs/44525911130), and [Pages deployment](https://github.com/sassnarep3-star/Own6/actions/runs/44525910652).

PR #142 repaired the earlier test harness and DFC0 integration failures; PR #139 then refreshed the source-coverage and related generated outputs and repaired the remaining red main gates. These are closed findings on `68bda5a`; the still-open PR #135 merge conflicts and navigation/evidence issues are separate findings below. No code or CI repair was made by this review.

### F-02 · Resolved on current main — DFC0 cross-pack coverage after CDF/D6 merges

At the earlier `551f292` review cut, the DFC0 board omitted 27 rows from `data/nfl_d6a947cb/` and `scripts/check_nfl_dfc0c1bc.py` reported 46 problems before rebuilding. PR #142's merge follow-up settled that cross-pack board. On current `68bda5a`, the checker reports **15 rules, 0 failures** (42 registers, 274 suggestions, 268 questions), the CDF and D6 standalone checkers pass, and the pytest DFC0 verifier/determinism tests pass.

This is recorded as a resolved integration issue, not a current release blocker. It also demonstrates the fixed-point hazard: generated cross-pack tables can become stale when another pack lands. The current DFC0 outputs are green.

### F-03 · Resolved on current main — committed sitewide source-coverage snapshot freshness

At the `188e904` review cut, `python3 scripts/source_coverage.py --check` still found eight stale artifacts (456 pages / 44,860 rows generated versus 445 / 43,642 committed). PR #139 refreshed those generated files. On current `68bda5a`, the same command exits 0 and reports **456 pages / 44,865 table rows**; the committed artifacts now match. The [Sitewide source coverage Action](https://github.com/sassnarep3-star/Own6/actions/runs/44525911130) also passes.

This was a snapshot-freshness issue, not a claim that any underlying value was false. The source-coverage tool continues to report 0 independently value-verified rows; its official-link counts are structural coverage only. No coverage artifacts were changed by this review.

### F-04 · High — PR #135's shared integration is still unmerged and conflicts with current `main`

[PR #135](https://github.com/sassnarep3-star/Own6/pull/135) remains open at head `5b98902c7ce546a337abc82055b3f19b5a0093ce`; its only displayed check is an older `lab` pass from 11:47Z, not a check on the current main tree. A merge-tree comparison against current `main` (`68bda5a`) reports **34 content-conflict paths**, including `COORDINATION.md`, `README.md`, `docs/index.html`, assurance/source-coverage outputs, and DFC0 board files/pages. The pack directory `docs/nfl-2dd0cbcb/` is not in the reviewed merged tree; I found no current shared-landing link to it. This is consistent with it still being an open PR, not a broken link in the currently deployed tree. PR #146, which was prepared against older `main@551f292`, also remains open; its generated outputs should not be assumed current without rebasing.

**Action for the integration owner:** rebase/reconcile PR #135 against the latest main, keep both sessions' work, regenerate generated inventories at the fixed point, then require the relevant checks to pass. I left all PR #135-owned pages untouched and did not merge it.

### F-05 · Medium — the merged CDF pack is not discoverable from the shared landing/navigation files

The eight-page `docs/nfl-cdf86c07/` pack exists on `main` and its direct Pages URL [loads](https://sassnarep3-star.github.io/Own6/docs/nfl-cdf86c07/?fb41a18f=68bda5a), but `index.html`, `docs/index.html`, and `README.md` contain no link to `docs/nfl-cdf86c07/index.html`. The current root portal therefore does not surface this merged pack (it now links the separate `d6a947cb` pack), and the secondary [`docs/index.html`](https://sassnarep3-star.github.io/Own6/docs/index.html?fb41a18f=68bda5a) still identifies itself as “NBA lines research dashboard” while listing mixed NBA/NFL workspaces. The CDF page is reachable directly; the issue is discoverability and context, not a missing file.

**Action for the integration owner:** decide whether/how to add the merged CDF pack to the shared NFL/workspace index and make the secondary hub's cross-project role explicit. Those shared landing files are under the active PR #135 integration scope and were not changed here.

### F-06 · Medium — 81 of 82 CDF requirement rows cite the same standings URL, even for unrelated claims

All 82 rows in `data/nfl_cdf86c07/requirements.csv` have a URL field, but **81** cite only the 2026 standings page and one cites the Week 11 schedule. Examples include CD-01 (opening/closing price snapshots), CD-06 (replacement depth), CD-25 (Game Books), and CD-53 (injury-report cadence); the cited standings page does not evidence those row-specific claims. A link being on an official NFL host is not the same as the linked content supporting the cell.

This finding does not assert those status/clearing-number cells are false. It records a claim-to-source mismatch against the user's source-evidence rule. See the [requirements register](https://github.com/sassnarep3-star/Own6/blob/68bda5a9b96c12338f7bdf415256afbb33e35de7/data/nfl_cdf86c07/requirements.csv), [official standings page](https://www.nfl.com/standings/division/2026/reg), and [official Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11).

**Action for the pack/integration owner:** retain only row-relevant official evidence; where the status or numeric clearing value cannot be supported by the cited source, leave it blank or keep it explicitly flagged for review. Do not substitute the official-host check for source-content verification.

### F-07 · Low — root decision-board card repeats the official-capture link

[`index.html` lines 266 and 268](https://github.com/sassnarep3-star/Own6/blob/68bda5a9b96c12338f7bdf415256afbb33e35de7/index.html#L266-L268) contain the same `docs/nfl-a67ddef8/index.html` link and same label twice in the Cross-Pack Decision Board card. It is a harmless duplicate target, not a broken route or data defect.

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
| Live GitHub Pages API / deployment | `main:/`, status `built`; deployment run [44525910652](https://github.com/sassnarep3-star/Own6/actions/runs/44525910652) succeeded for `68bda5a` |

The local target scan does not validate URL fragments or make external HTTP requests. The link checkers' green status is not fact verification.

## Repo-wide checks (reproducible on a clean worktree at `68bda5a`)

| Command / check | Result |
|---|---|
| `python3 tools/release_gate.py` | PASS — 0 issues across published HTML and tracked text |
| `python3 tools/check_site.py` | PASS — 13 strict pages, 0 errors, 0 advisories |
| `python3 scripts/check_site.py` | PASS — 9 pages, no broken internal links, all external links HTTPS |
| `python3 scripts/audit_integration.py` | PASS — no committed merge-conflict markers; independent arithmetic checks in its declared scope pass |
| `python3 scripts/check_hub.py` | PASS — 12 pages, 335 source-linked rows, 0 structural errors; its note explicitly says link/blank checks are not fact verification |
| `python3 scripts/check_assurance.py` | PASS — 9 pages and 25,897 source-linked rows |
| `python3 scripts/check_nfl_cdf86c07.py` | PASS — standalone CDF verifier |
| `python3 scripts/check_nfl_d6a947cb.py` | PASS — standalone D6 verifier |
| `python3 scripts/check_nfl_ade166a4.py` | PASS — 17 rules |
| `python3 scripts/check_nfl_51698d74.py` | PASS — 21 rules |
| `python3 scripts/check_nfl_0fef3044.py` | PASS — capture, 13 games, 253 player rows, and linked site checks |
| `python3 scripts/check_nfl_dfc0c1bc.py` | PASS — 15 rules, 0 failures; 42 registers, 274 suggestions, 268 questions |
| `python3 scripts/source_coverage.py --check` | PASS — 456 pages / 44,865 rows; committed generated artifacts match |
| `PYTHONPATH=. .venv/bin/python -m pytest -q tests/` | PASS — 866 passed, 0 failed, 6 subtests passed |
| `python3 tools/run_tests.py` | PASS — 201/201 |
| GitHub Actions on `68bda5a` | PASS — all main-branch workflows listed in the run query, including Assurance, DFC0, Lab, Verify site and engine, Legacy parlay safety, Release integrity, source coverage, and Pages deployment |

`requirements-empirical.txt` pins the pytest/scientific environment. The pinned pytest run above was run serially from a clean temporary worktree; `.venv` is local and not part of this deliverable. The snapshot freshness check and current-tree source-coverage workflow both pass on the reviewed main commit.

### Short navigation-scan reproduction

The counts above come from parsing `a[href]` in the two files and treating only scheme-less paths as local. Strip the fragment/query, resolve relative to the HTML file, and count a failure only when the resulting file does not exist. The scan deliberately does not test fragments or external reachability.

## Review-only recommendations (not applied)

1. Reconcile PR #135 against the current merged tree; it is still conflicting and its pack is not part of the deployed main tree.
2. Do not merge PR #146's generated outputs without rebasing it from its `551f292` base and rerunning `source_coverage --check` on the final tree; the current main snapshot now passes.
3. Keep the DFC0 fixed-point check in the post-merge matrix so future pack additions cannot silently leave the shared board stale.
4. Link the merged CDF pack from the agreed shared landing page and clarify that `docs/index.html` is a cross-project index, not an NFL-only page.
5. Replace generic source links in the CDF requirement table with row-relevant evidence or leave unsupported values blank and flagged.
6. Remove the duplicate A67 link from the root card.

## Close-out

This review made no changes to `index.html`, `docs/index.html`, `README.md`, any pack's data/model/site, or generated shared inventories. The only deliverables are this review report and its append-only coordination record. The current live site is served from `main`; this session did not alter or deploy it. At `68bda5a`, Actions, test suites, release gate, and committed source-coverage freshness all pass. PR #135 remains conflicting and is not ready to merge. A report-only PR will preserve the findings; its own checks must pass before it can be merged. No site merge or deployment was attempted by this review.
