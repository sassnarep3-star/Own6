# COORDINATION — Own6 NBA Lines Project

Session ID: arena-463d936f-own6 (original integration) + arena/d100a9d1-own6 (follow-up evidence/reconciliation)

## Task Board
| Task | Status | Owner | Files / record |
|---|---|---|---|
| Repo audit, executive summary, official-source registry | done | arena-463d936f-own6 | EXECUTIVE_SUMMARY.md, data/sources.csv |
| Line/prop/parlay model utilities and validation design | done | arena-463d936f-own6 | src/own6/, tests/ |
| Pages site, table pages, leaderboard design and flagged items | done | arena-463d936f-own6 | docs/ |
| Follow-up source/evidence review and branch reconciliation | done | arena/d100a9d1-own6 | README.md, COORDINATION.md, .gitignore; preserved merged docs and source files |
| Final integration and live Pages | done | arena-463d936f-own6 | PR #1 merged, PR #4 merged; live URL below |

## Evidence boundaries
Official NBA references: https://www.nba.com/stats/help/glossary and https://www.nba.com/news/inside-the-game-stat-glossary. They support metric definitions only, not betting edges, market odds, model performance, correlations, or ROI. Numeric values and empirical claims without verified sources remain blank/unverified and are identified at docs/flagged.html. No profitability claim.

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
- Follow-up: a small correction PR to F10/F11 (see its own record below).
## Session `arena/a6ccf588-own6` — independent integration / line-by-line verification pass

**Session ID:** `arena/a6ccf588-own6` · **Branch:** `arena/a6ccf588-own6` (Arena-fixed; the brief's `session-<id>/<task>` branch rule is superseded by the workspace rule — irregularity I-1).
**Claimed:** 2026-11-02 (claim committed and pushed immediately at session start).

**Situation at claim time:** PR #1 merged 20:55:33Z; PRs #3/#4/#5 merged 20:56–20:57Z by other sessions; `main` contained the `docs/` dashboard, `src/own6/` engine, `data/sources.csv`, `EXECUTIVE_SUMMARY.md`, root redirect `index.html`, `.nojekyll`, `.gitignore`. GitHub Pages legacy source = `main:/`, build `e935977` = `built`. Five active Arena branches; three other sessions hold **overlapping** root/docs scopes (irregularity I-2).

**Handoff:** The earlier sessions marked all tasks `done` but left verification claims based on *web-search indexing only* and left known broken URLs. Per the brief, this session takes the **final integration & independent verification** role for the combined data: direct retrieval of every cited official source, automated enforcement of the "one official source link per table row" rule, repair of broken links and incorrect claims, then PR → merge → deploy confirmation.

| # | Task | Status | Owner | File scope |
|---|------|--------|-------|------------|
| 10 | Independent line-by-line re-verification, automated link/source-row gate, repair of broken links & incorrect verification claims, dashboard completion (summary / repo review / verification-log subpages), site build & deploy check, PR to main + merge record | in progress | `arena/a6ccf588-own6` | `audit/**`, `tools/**`, `data/verification_log.csv`, `data/sources.csv`, `docs/**`, `EXECUTIVE_SUMMARY.md`, `.github/workflows/verify.yml`, `COORDINATION.md` (append-only) |

**Requests logged to other sessions (their branches are NOT edited):** please do not overwrite `docs/**`, `data/sources.csv`, or `EXECUTIVE_SUMMARY.md` on `main` while task 10 is in progress; the merged copies are being re-verified row by row. If you need a change there, log it here first.

### Verification rules applied
- Every `<tr>` on every published page must contain a link to an official source that is present in `data/verification_log.csv` with `verified-direct` status; enforced by `tools/check_site.py`.
- Values that cannot be confirmed from an official source stay blank and are listed on `docs/flagged.html`; nothing is inferred.
- `git pull --rebase` before each push; small frequent commits; other sessions' work preserved on merge conflicts.

### Log
- 2026-11-02: Claimed task 10; synced to `origin/main` (ff-only), later merged newer `main` changes; COORDINATION.md conflict resolved by keeping the other sessions' board verbatim and appending this section (no work discarded).
- 2026-11-02: Direct retrieval confirmed NBA.com IS reachable (www.nba.com/stats/overview, /stats/help/faq, /stats/help/glossary, /news/...); the earlier "sandbox cannot fetch NBA.com" statement is incorrect (irregularity I-3).
- 2026-11-02: Direct retrieval found `cdn.nba.com/stats/help/faq` returns `AccessDenied`, the timestamped injury-report PDF fails to retrieve, `../COORDINATION.md` is unreachable from the Pages `docs/` root, and `Math.erf` is undefined in JavaScript so the calculator throws. All flagged and being repaired (irregularities I-4..I-7).
- 2026-11-02 (addendum): `main` moved again while this claim was open — PR #6 and PR #7 (`arena/05e359b8-own6`) added `docs/verified/**`, `data/*.json`, `scripts/build_site.py`, `scripts/check_site.py` and a rewritten README. Merge conflicts on `COORDINATION.md` were resolved twice by keeping every other session's board text verbatim and appending this session's section; nothing discarded. To avoid touching other sessions' output, this session's independent deliverables go into `docs/review/**`, `audit/**`, `tools/**`, `data/verification_log.csv` plus small surgical repairs to the merged `docs/*.html` and one nav link on `docs/index.html`.
- 2026-11-02: `PUT /repos/.../pages` (to set source `main:/docs`) returned HTTP 403 "Resource not accessible by integration"; the existing legacy `main:/` source + root `index.html` redirect is retained. GitHub Docs on publishing sources: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site (verified directly).

### Task 10 progress — verification complete, publishing next
- Sources: 24 official URLs retrieved directly (NBA.com Stats/FAQ/Glossary/News/Schedule/NBABet, NBA Official injury report + PDF, official.nba.com rulebook, scikit-learn, SciPy, statsmodels, NIST, Python docs, GitHub Docs, GitHub REST API, GitHub repo). Full line-by-line log: `data/verification_log.csv`, `audit/VERIFICATION.md`, `docs/review/verification.html`.
- Verification performed: `tools/run_tests.py` (5/5 pass), `tools/build_review.py --check` (7 generated files match), `tools/check_site.py` (**12 strict pages, 0 errors**; every data row has a directly verified official link; no broken internal links; `Math.erf()` absent; all `data/sources.csv` URLs in log). Report: `audit/link_check_report.md`.
- Repairs applied (idempotent script `tools/integration_repairs.py`): false "cannot fetch NBA.com" claim corrected; broken FAQ URL replaced; S8/leaderboard/G5–G8/F4/F7 rows given official links; `../COORDINATION.md` replaced with the official GitHub blob; calculator's undefined `Math.erf` replaced with an erf approximation (validated in Node: erf(1)=0.842701, cdf(1.96)=0.975002); consistent nav to `verified/` and `review/`.
- New deliverables (this session's scope only): `docs/review/**` (Overview, Executive summary, Verification log, Repo review, Flagged for Review), `audit/**`, `tools/**`, `.github/workflows/verify.yml`, corrected `data/sources.csv` and `EXECUTIVE_SUMMARY.md`.
- Irregularities: I-1…I-23 published on `docs/flagged.html` and `docs/review/flagged.html` with official source links. 29 advisory rows in `docs/verified/**` (owned by session 05e359b8) lack official source links; **request logged here, not edited**: please add official links or label those rows explicitly as compiler methodology; see I-18. I-21: this board currently states the Pages source is `main /docs`, but the GitHub Pages API reports `main:/`.
