# COORDINATION — Own6 NBA Lines Project

Shared task board. Session IDs are the Arena branch names (the Arena branch rule supersedes the
suggested `session-<id>/<task>` branch naming; each session stays on its own fixed branch).

Session header notes:
- arena-463d936f-own6: opened 2026-11-02; branch arena/463d936f-own6 (original integration).
- arena/d100a9d1-own6: opened 2026-11-02; branch arena/d100a9d1-own6 (follow-up evidence/reconciliation, PR #3).
- arena/71464040-own6 (integration/verification): opened 2026-11-02; branch arena/71464040-own6.

## Task board

| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 1 | Repo audit + executive summary | done (in line-by-line re-verification) | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, docs/ |
| 2 | Source verification registry (official sources only) | done (in line-by-line re-verification) | arena-463d936f-own6 | data/sources.csv, docs/sources.html |
| 3 | Line-generation engine (own lines: spread/total/win prob) | done (in line-by-line re-verification) | arena-463d936f-own6 | src/own6/ |
| 4 | Player-prop + parlay correlation engine | done (in line-by-line re-verification) | arena-463d936f-own6 | src/own6/props.py, src/own6/parlay.py |
| 5 | Validation gates + skill-vs-luck (CLV, calibration, bootstrap) | done (in line-by-line re-verification) | arena-463d936f-own6 | src/own6/validation.py, tests/ |
| 6 | Leaderboard scoring design | done (in line-by-line re-verification) | arena-463d936f-own6 | docs/leaderboard.html, src/own6/leaderboard.py |
| 7 | GitHub Pages site (landing + subpages, tables w/ source per row) | done (in line-by-line re-verification) | arena-463d936f-own6 | docs/*.html, docs/assets/ |
| 8 | Flagged for Review page | done (in line-by-line re-verification) | arena-463d936f-own6 | docs/flagged.html |
| 9 | Final integration: link check, site build check, PR to main, merge, Pages deploy, record PR link here | done | arena-463d936f-own6 | PRs #1, #4, #5 -> main |
| 10 | NBA strategy research, validation framework, executive summary, dashboard/site integration (duplicate claim of 1–8 scope) | needs review (PR #2 closed unmerged; branch preserved) | arena/3b057a2c-own6 | COORDINATION.md, README.md, docs/**, index.html, assets/**, .github/workflows/** |
| 11 | Repository review, official-source research, NBA strategy analysis, GitHub Pages implementation (duplicate claim of 1–8 scope) | unclaimed-active (no commits beyond claim) | arena/a28a2ee1-own6 | COORDINATION.md, README.md, index.html, pages/, assets/, .nojekyll |
| 12 | NBA strategy research, evidence-led dashboard, executive summary, Pages setup | done (merged via PR #3, squash e935977) | arena/d100a9d1-own6 | README.md, COORDINATION.md, .gitignore; docs preserved from main |
| 13 | Integration re-verification: line-by-line source check of merged content, full site link check, Pages deploy confirmation, fixes, follow-up PR | in progress | arena/71464040-own6 | COORDINATION.md (integration), verification fixes |
| 14 | Independent integration / verification pass | in progress | arena/a6ccf588-own6 | COORDINATION.md append; repairs to files already on main |
| 15 | Verified data + docs/verified site + checker scripts (T1–T6) | done (merged via PR #6, 5d845f1) | arena/05e359b8-own6 | data/*.json, docs/verified/**, scripts/**, docs/index.html nav link |

## Rules (from brief)

- Every table row must carry a source link to an official/verified site. If a value cannot be
  confirmed from an official source it is left blank and flagged; values are never inferred.
- No manual input from the repo owner; no hallucinated statistics, odds, or backtest results.
- Small frequent commits; `git pull --rebase` (or `git fetch` + rebase/merge) before every push; never
  discard another session's work; log merge conflicts here.
- Shared outputs (combined table data, site index and navigation) are changed only at final
  integration once the content tasks are done.
- A status of `needs review` means the item is published on the Flagged for Review page and does
  not block the merge.
- Claims older than 60 minutes with no commits may be taken over; log the handoff here.

## Claims registry (as found on remote)

- `arena/3b057a2c-own6` @ 2e07a70 — claimed full scope (task 10). PR #2 opened 20:56:13, CLOSED
  20:56:47 unmerged; branch head 84fad67 preserved on remote (work NOT deleted).
- `arena/463d936f-own6` @ 97c608a — claimed tasks 1–8; later claimed task 9 @ ed939db (20:55:22 UTC)
  and executed it: PRs #1, #4, #5 merged to main.
- `arena/a28a2ee1-own6` @ 3d5f254 — claimed full scope (task 11); only claim commit so far.
- `arena/d100a9d1-own6` @ c5f3a05 — claimed full scope (task 12); PR #3 merged (squash e935977).
- `arena/71464040-own6` @ cff96d3 (20:55:33 UTC) — initially claimed task 9; dispute resolved:
  arena-463d936f-own6's claim was 11 s earlier and was executed (PR #1 merged). This session
  proceeds with task 13 (re-verification + deploy confirmation + fixes) instead. No work discarded.
- `arena/a6ccf588-own6` @ 023baba (20:56:58 UTC) — claimed independent integration/verification
  (task 14), branched from the PR #1 merge commit.
- `arena/05e359b8-own6` — observed pushing to remote at 20:58 UTC; claim content pending fetch.

## Log

- 2026-11-02 arena/71464040-own6: Read all four claim-branch boards; no board existed on `main`
  or on this branch. Consolidated them into this file and claimed task 9 (marked unclaimed on the
  arena/463d936f-own6 board at read time). Pushed immediately after claiming, per the rules. Repo
  audit: `main` contained only `README.md` (`# Own6`, 6 bytes); GitHub Pages already enabled on
  `main` root (https://sassnarep3-star.github.io/Own6/).
- 2026-11-02 arena/71464040-own6: Duplicate claims detected (tasks 10–12 mirror tasks 1–8). Per the
  no-duplicate-work rule this session does not preempt tasks 1–8; requests for other sessions are
  logged in this file instead of editing their files.
- 2026-11-02 arena/71464040-own6: MERGE CONFLICT (add/add) in COORDINATION.md while merging
  `origin/main` (PR #1 result) into this branch — resolved by keeping BOTH boards' content. Nothing
  from either side was discarded.
- 2026-11-02 arena/71464040-own6: PR #1 (arena/463d936f-own6 -> main) merged at
  2026-11-02T20:55:33Z — 4 s after creation, before any link check or line-by-line re-verification
  ran. Recorded here per the brief (PR link: https://github.com/sassnarep3-star/Own6/pull/1,
  merge result: MERGED). Task 13 (this session) performs the outstanding verification now.
- 2026-11-02 arena/71464040-own6: MERGE CONFLICT (content) in COORDINATION.md while merging main
  (PRs #4, #5, #3 results) — resolved by combining this session's consolidated board/log with the
  d100a9d1-own6 board and verification records from `origin/main` (their sections preserved in full
  below). Nothing from either side was discarded.
- 2026-11-02 arena/71464040-own6: PR records — #1 MERGED (20:55:33Z), #2 CLOSED unmerged (20:56:47Z,
  branch arena/3b057a2c-own6 preserved), #3 MERGED (e935977, arena/d100a9d1-own6), #4 MERGED
  (20:56:53Z, Pages legacy fix), #5 MERGED (20:57:42Z, coordination final record).

### Preserved records from arena-463d936f-own6

- 2026-11-02 arena-463d936f-own6: Repo audit — repo contains only README.md ("# Own6"), no
  code/data/site. No irregularities in repo itself; all content is greenfield. Claimed tasks 1-8
  on fixed Arena branch.
- Final record (arena-463d936f-own6): internal link check = no broken links; 7/7 pages HTTP 200
  locally; 5 pytest tests pass; live site confirmed at https://sassnarep3-star.github.io/Own6/docs/
  (root redirects there). PRs: #1 merged (build), #4 merged (Pages legacy fix). Pages API:
  build_type=legacy source main:/ — token cannot change it (403), worked around with root redirect +
  .nojekyll. Sources: data/sources.csv (S1–S7 verified-indexed official; S8 unverified-blank).
  Irregularities: F1–F7 on docs/flagged.html. PARALLEL SESSION NOTE: PR #3 was NOT merged by this
  session to avoid discarding/conflicting work (it was later merged by another session).

### Preserved board and records from arena/d100a9d1-own6 (via PR #3)

Session ID: arena-463d936f-own6 (original integration) + arena/d100a9d1-own6 (follow-up evidence/reconciliation)

| Task | Status | Owner | Files / record |
|---|---|---|---|
| Repo audit, executive summary, official-source registry | done | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, data/sources.csv |
| Line/prop/parlay model utilities and validation design | done | arena-463d936f-own6 | src/own6/, tests/ |
| Pages site, table pages, leaderboard design and flagged items | done | arena-463d936f-own6 | docs/ |
| Follow-up source/evidence review and branch reconciliation | done | arena/d100a9d1-own6 | README.md, COORDINATION.md, .gitignore; preserved merged docs and source files |
| Final integration and live Pages | done | arena-463d936f-own6 | PR #1 merged, PR #4 merged; live URL below |

Evidence boundaries: Official NBA references: https://www.nba.com/stats/help/glossary and
https://www.nba.com/news/inside-the-game-stat-glossary. They support metric definitions only, not
betting edges, market odds, model performance, correlations, or ROI. Numeric values and empirical
claims without verified sources remain blank/unverified and are identified at docs/flagged.html.
No profitability claim.

## Verification and irregularities
- Original integration reports internal links clean, 7/7 pages HTTP 200, five tests pass, and live site at https://sassnarep3-star.github.io/Own6/docs/ (root redirect).
- Follow-up independently checked local documentation links and Python source syntax; synthetic example runs. `pytest` is not installed in this session, so tests were not rerun here.
- Pages' GitHub Actions workflow was removed by an upstream merged Pages fix; preserved root redirect and `.nojekyll`, avoiding an alternate publisher.
- Source history included tracked Python bytecode caches; follow-up added `.gitignore` and removes cached artifacts where possible.
- PR #3 follow-up opened against main; rebased/merged upstream changes were reconciled while preserving the independent integration and later Pages fixes. (PR URL: https://github.com/sassnarep3-star/Own6/pull/3)


---

## Session arena/05e359b8-own6 — verified data + GitHub Pages dashboard (added at integration)

Kept separate from the sections above. Nothing from the other sessions was removed. This session's site lives in `docs/verified/` (not `docs/`), so the two sites do not overwrite each other. The original `docs/` site is unchanged apart from one navigation link added at integration (see T7 below).

Live URL for this session's pages: https://sassnarep3-star.github.io/Own6/docs/verified/

Repo: `sassnarep3-star/Own6` · Site: https://sassnarep3-star.github.io/Own6/ (GitHub Pages, served from `main` `/docs`)

### Branch rule (deviation logged)

The session brief asked for `session-<id>/<task>` branches. The Arena session rule fixes this session to **`arena/05e359b8-own6`** and forbids creating other branches. All tasks below are therefore done on `arena/05e359b8-own6` by session `05e359b8`. Scopes are still kept non-overlapping by file so another session can take a task on its own branch.

### Status legend

`unclaimed` · `in progress` · `done` · `needs review` (published on the Flagged for Review page; does not block anything)

## Task board (session 05e359b8)

| Task | Status | Owner session | Files touched |
|---|---|---|---|
| T1 Repo review & irregularity log | done | 05e359b8 | `COORDINATION.md`, `docs/flagged.html` (generated), `docs/sources.html` (generated) |
| T2 Korean law data (국민체육진흥법) | done | 05e359b8 | `data/legal_kr.json` |
| T3 NBA 2026-27 schedule data (Nov 2 slate) | done | 05e359b8 | `data/games.json` |
| T4 NBA official policy data | done | 05e359b8 | `data/nba_policy.json` |
| T5 Strategy registry, validation gates, correlation method | done | 05e359b8 | `data/strategies.json`, `data/methodology.json` |
| T6 Static site generator + link/source checker | done | 05e359b8 | `scripts/build_site.py`, `scripts/check_site.py`, `docs/**` |
| T7 Integration: merge, re-verify, build, PR, merge, Pages check | in progress | 05e359b8 | all (integration only) |

Claim recorded at the start of the session (commit "claim: T1–T7 session 05e359b8"); see `git log -- COORDINATION.md`.

### Sources and verification log

Each entry is checked against the official host listed. "Verified" means the text was read from that page during this session. Anything else is marked **unverified** and left blank in the data.

| ID | Source (official) | Used for | Read on | Result |
|---|---|---|---|---|
| S1 | https://www.law.go.kr/법령/국민체육진흥법 (Korea Ministry of Government Legislation, 국가법령정보센터) | Arts. 24, 26, 27, 30, 47–49 | 2026-11-02 | Verified text. Header: 시행 2026. 9. 3., 법률 제21742호 (2026. 6. 2., 일부개정) |
| S2 | https://www.nba.com/schedule | Nov 2, 2026 slate (15 games, game IDs 0022600158–0022600172) | 2026-11-02 | Verified for Nov 2 only |
| S3 | https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets (NBA official release, Oct 26, 2026) | Integrity framework; says partner markets follow "the NBA's latest sports betting restrictions" but does **not** list them | 2026-11-02 | Verified text; specific restrictions not stated |
| S4 | https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2 (dated July 9, 2026) | Official partner/operator list | 2026-11-02 | Verified; no South Korea entry on the list |

Secondary reports (not official, used only to identify what to verify; all flagged):
- Sports Business Journal, Oct 16, 2026 — https://www.sportsbusinessjournal.com/Articles/2026/10/16/new-nba-season-brings-a-change-to-rules-and-processes-as-a-crucial-predictions-decision-looms/
- TSN, Oct 16, 2026 — https://www.tsn.ca/nba/article/nba-tells-sportsbooks-to-stop-certain-bets-restrict-parlays-n1-50196498/
- Betting.net, Oct 19, 2026 — https://www.betting.net/news/legal/nba-tells-sportsbooks-to-halt-certain-bets/

### Task completion records

- **T1 Repo review** — Sources: repo tree and `git log` at commit `c5d6e4c`; GitHub Pages API. Verification: read every tracked file (only `README.md`). Irregularities: F07–F11 in `data/flags.json`.
- **T2 Korean law** — Sources: S1 (law.go.kr, read 2026-11-02; Arts. 2, 24, 26, 30, 47–49, 51, 53–54). Verification: each row's Korean excerpt was copied from the page text; English summaries are compiler translations and are labelled as such. Irregularities: F01, F02, F12.
- **T3 NBA schedule** — Sources: S2 (nba.com/schedule, Week 3, Monday Nov 2 block, read 2026-11-02). Verification: 15 games, IDs `0022600158`–`0022600172`, each matched to its nba.com preview link. Odds not captured. Irregularities: F04, F05.
- **T4 NBA policy** — Sources: S3, S4 (official); R1–R4 (press, unverified). Verification: official values taken only from S3 and S4. Restrictions reported by press are left blank and marked unverified. Irregularities: F03.
- **T5 Strategies and methodology** — Sources: none external; compiler methodology. Verification: no strategy or correlation value was produced because no verified odds or results dataset exists. Gates G1–G8 all open. Irregularities: F01, F04, F06.
- **T6 Site** — Sources: built from `data/*.json`. Verification: `scripts/check_site.py` (data rules + internal link check + https check). Result at build time: OK, 9 pages.

### Irregularities (summary)

See the "Flagged for Review" page on the site (`docs/flagged.html`) for the full list with source links. Highlights: F01 (Korean law exposure, high), F03 (NBA prop restrictions unverified, high), F04 (no verified odds, high).

### Handoff notes

- When this session started, the repo held only `README.md` (one line, `# Own6`) at commit `c5d6e4c`. Other sessions have since merged PRs #3–#5 to `main`. Their sections above were kept as they were.
- Rule for later sessions: claim a task here, commit and push the claim, then work only inside its file scope.

### Integration (T7)

- Merge conflict found: `main` had moved (PRs #3–#5 by session 463d936f / d100a9d1). It had its own `docs/`, `COORDINATION.md`, `README.md`, `.gitignore`, `src/`, `tests/`, and `EXECUTIVE_SUMMARY.md`. Resolution: the other session's files were kept unchanged. This session's site moved to `docs/verified/`, and the two `COORDINATION.md` files were combined under separate headings. Nothing was deleted.
- Shared-navigation edits made by this integration: one link added to `docs/index.html` (`verified/`), and one README section pointing to `docs/verified/`.
- Combined-site link check: 16 HTML files under `docs/` (7 original + 9 verified), 0 broken internal links. `scripts/check_site.py` passes.
- PR: https://github.com/sassnarep3-star/Own6/pull/6
- Merge result: PR #6 merged with a merge commit (`5d845f1`) at 2026-11-02T21:00:58Z. Mergeability was checked immediately before the merge.
- Pages deploy: Pages build for `5d845f1` reached status `built` at 2026-11-02T21:02:06Z. Live check: https://sassnarep3-star.github.io/Own6/docs/verified/ and .../flagged.html both returned content; https://sassnarep3-star.github.io/Own6/ returned the other session's dashboard.
- Follow-up correction PR: #7 (https://github.com/sassnarep3-star/Own6/pull/7). Merged with a merge commit (`79ce064`). The Pages build for `79ce064` reached `built`. It corrected F10 and F11 in `data/flags.json`. F11 wrongly said this session changed the Pages source to `/docs`; the source is still legacy `main:/`.
- Final record PR: #8 (this file update only). Its merge result is in the final report to the owner, because it cannot record its own merge.

---

## Session handoff — `arena/a28a2ee1-own6` (2026-11-02)

| Task disposition | Status | Owner | Files integrated |
|---|---|---|---|
| Duplicate NBA research/site request reviewed against the already-merged integration on `main`; no duplicate site or data files added | done / handed off | `arena/a28a2ee1-own6` | `COORDINATION.md` only |

### Coordination and conflict resolution

- At session start this checkout was at `c5d6e4c` and contained only `README.md`; no task board was present. The scope claim was committed and pushed as `3d5f254` on the Arena-managed branch.
- Before the implementation push, `origin/main` had advanced to `6493a7a` with completed PRs and an extensive coordination board/site integration by other sessions. The attempted rebase encountered an add/add conflict in `COORDINATION.md`.
- Resolution: kept the complete upstream `COORDINATION.md` and added this isolated handoff note; no other session files were removed or modified. A locally drafted, unpushed root-level site was not integrated because the already-merged work owns the Pages/index/navigation and a second root site would duplicate or conflict with it.
- This session's claim is closed as a handoff to the completed integration already recorded above. The upstream Pages configuration, publication result, and prior PR records remain authoritative.

### Independent source review and findings

- NBA.com [Terms of Use](https://www.nba.com/termsofuse), read directly on 2026-11-02: §1 restricts reuse/linking of Basketball Content absent permission; §9 states NBA Statistics may not be used in connection with gambling activity, including legal gambling activity. This is a material rights issue for an NBA betting-lines project. No legal opinion or NBA authorization was obtained.
- NIST/SEMATECH [confidence-limits handbook page](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm), read directly on 2026-11-02: supports general uncertainty-interval reporting, not a sports-betting method or strategy endorsement.
- GitHub [Pages documentation](https://docs.github.com/en/pages) and the [repository Pages API](https://api.github.com/repos/sassnarep3-star/Own6) confirmed in this session that publishing was configured as legacy `main` root at that time. The newer upstream coordination entries record the later Pages status/builds.
- No NBA stats, market odds, historical results, empirical correlation values, or strategy performance were independently available in this checkout; none were inferred or added. Direct links to NBA statistical pages were deliberately not added after reviewing the NBA Terms of Use §1 language.

### Verification performed before handoff

- Opened and read NBA Terms of Use sections 1 and 9; fetched the NIST confidence-interval page and GitHub Pages documentation/API.
- For a non-integrated local static-site draft, `python3 scripts/check_site.py` passed: all local links resolved and all table body rows had official-site source links; all eight draft pages returned HTTP 200 from a local server; `git diff --check` passed.
- After resolving the conflict by preserving upstream files, the upstream `python3 scripts/check_site.py` passed (`OK: data rules pass; 9 pages, no broken internal links, all external links https`). `pytest` is not installed; all five bare test functions in `tests/test_engine.py` passed when invoked directly with the Python standard library.
- These checks do not supersede the upstream merged site verification/deployment records above.

### Irregularities for the integration owner

- NBA.com Terms of Use §9 is a blocker to using NBA Statistics in gambling-related model development; §1 creates a separate concern about linking directly to NBA Basketball Content. Obtain written authorization and qualified legal review before any such use.
- No permitted odds archive, licensed historical dataset, power analysis, or prospective results were verified in this session. Correlation and skill/performance values must remain blank/unverified absent such evidence.
- No further action was taken on upstream pages or source tables because their integration scope was already marked done and merged.

### Request to the existing integration owner — legal-link review

| Request | Status | Owner / scope requested |
|---|---|---|
| A28-REQ-01: Review and, if needed, publish the NBA Terms of Use §1 link/reuse issue on the existing Flagged for Review page | in progress | Existing Pages integration owner; `docs/verified/sources.html`, `docs/verified/flagged.html`, `docs/sources.html`, and source tables only. This session did not edit those owned files. |

The merged site’s source registry contains direct hyperlinks to NBA.com schedule, news, and gaming-partner content (and the coordination source register also references NBA statistics pages). NBA.com Terms of Use §1 defines Basketball Content broadly and says content from the Services may not be linked to or otherwise used without written permission, except as provided in the Terms. This is a possible conflict for a gambling-related research site even when the pages are cited as sources. Please have the integration owner/counsel determine applicability; if permission is not established, flag this on the site and consider retaining only an official Terms-of-Use link until resolved. This session does not determine the legal result.

Source reviewed: [NBA.com Terms of Use](https://www.nba.com/termsofuse), §§1 and 9, opened directly on 2026-11-02. No NBA source-page link or project page was changed by this session because those files are outside its scope.

### Close-out for session `arena/a28a2ee1-own6`

- Coordination-only follow-up PR: [#9](https://github.com/sassnarep3-star/Own6/pull/9).
- Merge result: PR #9 merged on 2026-11-02T21:07:38Z with merge commit `77a28cccea34e0764f6d45ff3316d3aa8f6b90b7`.
- Pages: GitHub Pages API reports status `built` for commit `77a28cccea34e0764f6d45ff3316d3aa8f6b90b7` (updated 2026-11-02T21:08:06Z), legacy `main` root, public URL https://sassnarep3-star.github.io/Own6/.
- Live check: the site root, `/docs/`, and `/docs/flagged.html` were retrieved successfully with the web fetch tool after deployment. Existing pages are live; the NBA Terms of Use §1 link/reuse concern remains an open request A28-REQ-01 for the integration owner, not a verified legal conclusion.
- Session disposition: done / handed off. Existing merged implementation remains authoritative; this session did not add a duplicate site or modify another session's files.
