# NFL 3B81013C — Repository and Source Audit

**Session:** `arena/3b81013c-own6` · **Branch:** `arena/3b81013c-own6`, branched from `main` at `b41bc814c6830431cd00cf2b45b74d1434240557`
**Audit date:** 12 November 2026 · **Scope:** every tracked file in the repository at the branch point, plus every official page cited by this pack
**Claimed paths (disjoint from all other sessions):** `data/nfl_3b81013c/**`, `src/nfl_3b81013c/**`, `docs/nfl-3b81013c/**`, `scripts/build_nfl_3b81013c.py`, `scripts/check_nfl_3b81013c.py`, `tests/test_nfl_3b81013c.py`, `research/NFL_3B81013C_EXECUTIVE_SUMMARY.md`, `audit/NFL_3B81013C_REPO_AND_SOURCE_AUDIT.md`

---

## 1. Method

1. Read `COORDINATION.md` and claimed `NFL-3B1`…`NFL-3B8` under disjoint paths before writing a single file; the claim was committed and pushed immediately (`3f130b4`).
2. Enumerated every tracked file, every CI workflow and every gate script to learn the invariants a new page set must satisfy.
3. Ran the repository's own audit (`python3 scripts/audit_repo.py`) against the branch point. This required deepening the shallow clone — the script pins `BASE = "86eca0f"` and does a `git show` on that revision, which a depth-limited clone cannot resolve.
4. Re-read every official page cited by this pack directly, recording the URL on every register row.
5. Re-entered the official Week 10 standings independently inside `scripts/check_nfl_3b81013c.py` so the register cannot act as its own evidence.
6. Flagged every irregularity rather than repairing another session's file.

---

## 2. Repository state at the branch point

| Measure | Value |
|---|---|
| Files inventoried by `scripts/audit_repo.py` | 333 |
| Lines scanned | 26,341 |
| Data records reviewed | 2,061 |
| Recorded findings | 17 (4 open at baseline) |
| Published HTML pages | 133 |
| CSV registers under `data/` | 66 at audit time; 78 after this pack |
| CI workflows | 10 |

---

## 3. Findings carried forward from the existing audit

`scripts/audit_repo.py` records 17 findings against baseline commit `86eca0f`. They are **not** re-litigated here; the table below records whether each is still observable in the current tree, so a reviewer can see the current state without trusting a stale label.

| ID | Severity | File | Recorded status | Observable in this tree |
|---|---|---|---|---|
| A-F01 | high | `docs/index.html` | resolved_upstream | No merge markers present |
| A-F02 | high | `scripts/model.py` | open | **Not reproducible.** The current code uses `100.0/(ml+100.0)` and `-ml/(-ml+100.0)`, which is the correct conversion, and the file carries a comment saying a prior session fixed it. The recorded status is stale. |
| A-F03 | high | `nba_lab/experiments.py` | resolved_in_session | Evidence string no longer present |
| A-F04 | high | `nba_lab/experiments.py` | resolved_in_session | Evidence string no longer present |
| A-F05 | high | `nba_lab/gates.py` | resolved_in_session | Evidence string still present — see §5 |
| A-F06 | high | `nba_lab/gates.py` | resolved_in_session | Evidence string still present — see §5 |
| A-F07 | medium | `nba_lab/contracts.py` | resolved_in_session | Evidence string no longer present |
| A-F08 | high | `nba_lab/registry.py` | resolved_in_session | `"min_events": 200` still present — the documented policy floor |
| A-F09 | high | `nba_lab/contracts.py` | resolved_in_session | `if market not in MARKETS:` present |
| A-F10 | medium | `nba_lab/models.py` | resolved_in_session | Evidence string no longer present |
| A-F11 | high | `scripts/verify_data.py` | open | Confirmed: the module docstring reads "Line-by-line verification of collected NBA data" while the checks are internal recomputation between local tables |
| A-F12 | high | `data/correlation_findings.csv` | open | Confirmed: four rows carry `pearson_r` values from 6 to 357 observations with no paired-residual ledger and no interval |
| A-F13 | medium | `README.md` | resolved_upstream | The quoted conflicting sentence is gone |
| A-F14 | medium | `data/legal_kr.json` | open | Confirmed: article-level rows present |
| A-F15 | low | `LICENSE` | open | Confirmed: no root `LICENSE`, no `LICENSE.*` file exists |
| A-F16 | medium | `scripts/check_lab.py` | resolved_upstream | Table inspection present |
| A-F17 | medium | `nba_lab/pricing.py` | resolved_in_session | Evidence string no longer present |

### Irregularities found by this audit

| # | Finding | Evidence | Suggested action | Owner |
|---|---|---|---|---|
| N-01 | **A-F02 is stale in the wrong direction.** It is labelled `open` but the described defect is absent from the current file. | `scripts/model.py` lines 198–201 now implement the correct conversion. | Re-run the audit with a current `BASE`, or mark the finding resolved, so the published dashboard does not understate the current state. | session owning `scripts/audit_repo.py` |
| N-02 | **Four findings labelled `resolved_in_session` still match their offending evidence string in the current tree** (A-F05, A-F06, A-F08, A-F09). | `[raw_p] + [1.0] * (family_size - 1)` at `nba_lab/gates.py:114`; `o.dependence_evidence == "verified"`; `"min_events": 200`; `if market not in MARKETS:` | A resolved label should mean the offending construct is gone or provably corrected. Either re-verify each with a test that the corrected behaviour holds, or downgrade the label. | session owning `nba_lab/**` |
| N-03 | **`scripts/audit_repo.py` cannot run on a shallow clone.** | `git show 86eca0f:scripts/model.py` fails with exit 128 on a depth-limited clone | Document the `fetch-depth: 0` requirement for local runs, as `lab-ci.yml` already does, or fall back gracefully. | session owning `scripts/audit_repo.py` |
| N-04 | **A hard-coded branch name ships a stale URL.** | `BRANCH = "arena/74d27b5d-own6"` at `scripts/audit_repo.py:26` is baked into every inventory `source_url` for files that changed since the baseline | Derive the branch from `git rev-parse --abbrev-ref HEAD`, or record the commit SHA instead. | session owning `scripts/audit_repo.py` |
| N-05 | **Eight published dashboard directories are not linked from `README.md`.** | `docs/assurance/`, `docs/coverage/`, `docs/hub-evidence/`, `docs/origin/`, `docs/parlay-safety/`, `docs/reverification/`, `docs/reverify/`, `docs/sf-rent/` exist but have no README entry | Add them to the shared README at final integration. Requested here, not edited. | final integration session |
| N-06 | **Two CSV conventions coexist.** | 16 files use CRLF line endings (`data/correlation_findings.csv`, `data/hub_flags.csv`, …) while newer registers use LF | Normalise at integration, or document the mixed convention so byte-level diffs are not mistaken for edits. | final integration session |
| N-07 | **Legacy correlation rows keep a 6-observation estimate.** | `data/correlation_findings.csv`: `teammate_PTS_Mitchell_Allen`, n=6, r=−0.4222, sourced to ESPN player logs | Already published as flagged/unverified by the assurance audit; keep it flagged and do not reuse the number. | already flagged |
| N-08 | **`data/empirical/observations.csv` is a header-only contract with no rows.** | One line: the field list | Correct fail-closed default: the lab reports `not_run` and the leaderboard stays empty. No action. | none |

All eight are published on this pack's Flagged for Review page with source links, as required. None blocks publication and none was silently repaired.

---

## 4. Source verification performed for this pack

Every value below was read directly from the official page during this session. No secondary source was used for any football fact.

| Official page | What was read | Values this pack depends on |
|---|---|---|
| https://www.nfl.com/schedules/2026/reg10/ | All 14 Week 10 games, kickoff times, venues, broadcasters, 4 bye clubs | Slate composition; neutral-site flag for NE at DET |
| https://www.nfl.com/standings/ | All 32 clubs' W-L-T, points for, points against | Every per-club offence and defence rating; the league average |
| https://www.nfl.com/injuries/ | Practice status and game status for every listed player | All 49 starter-level entries; the LP partial-degradation rows |
| https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11 | Club-by-club Week 10 updates | AZ quarterback change; MIN trade for Cousins; CLE concussion clearance |
| https://www.nfl.com/news/dolphins-place-qb-malik-willis-groin-on-injured-reserve-kyle-mccord-in-line-for-first-start | Club announcement | MIA quarterback cascade to a practice-squad elevation |
| https://www.nfl.com/legal/terms/ | Sections 1.3, 11(f), 12, 16, 18 | Reuse, harvesting and wagering restrictions; liability cap; governing law |
| https://operations.nfl.com/inside-football-ops/players-legends/2020-nfl-nflpa-cba-need-to-know/ | Roster rules | 53-man list; 48/47 gameday rule; 16-player practice squad; elevation caps |
| https://operations.nfl.com/game-operations-logistics/preparation-safety/game-and-stadium-prep | Pregame countdown | T-90 minute Game Day Administration Report; roof lock |
| https://operations.nfl.com/calendar-events/nfl-important-dates | 2026–27 calendar | Munich and Mexico City games; waiver date; playoff freeze; Super Bowl LXI |
| https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm | Confidence-interval procedure | Fisher-z and clustered-interval methodology |
| https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html | Pearson correlation reference | Correlation definitions and the two-sided test |
| https://scikit-learn.org/stable/modules/calibration.html | Probability calibration | Brier and log-loss comparison versus the market |
| https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html | Holm, BH and BY corrections | The multiplicity gate |

### Source-integrity limits, stated for the reviewer

1. **Read once, on one day.** Injury status is a moving target; the T-90 minute inactive list supersedes the practice report. Every injury row carries the report URL so a reviewer can re-check.
2. **Transcription, not independent entry.** Values were transcribed by an automated agent. The checker re-enters the standings independently, which catches arithmetic and mapping errors but not a shared misreading of the same page.
3. **No source-body archiving.** Pages are not stored; only the URL and the value are recorded. A page that changes will make a cited value unverifiable from the repository alone.
4. **No market data of any kind was read from a sportsbook.** The pack therefore cannot and does not compute an edge, a return or closing-line value.
5. **Structural weights are a prior.** The positional weights and string tiers are ordinal judgements with no historical fit. They are labelled throughout as uncalibrated.
6. **The copula figures are approximate.** A second-order Mehler expansion is used; it is accurate at moderate correlation and diverges near the Fréchet bounds, which the page states.

---

## 5. Gate invariants verified before publishing

The new page set was checked against every repository gate that scans published HTML, not only against its own checker.

| Gate | Requirement | Result for `docs/nfl-3b81013c/**` |
|---|---|---|
| `tools/release_gate.py` | No merge markers in tracked text; no generator repr; every `href`/`src` relative link resolves; no root-absolute links; HTTPS only | Pass — all links relative or HTTPS; no markers |
| `tools/check_site.py` | No `Math.erf(` in any HTML or JS; internal links resolve | Pass — the normal CDF is computed in Python at build time, never in the browser |
| `scripts/linkcheck.py` | Every `<tr>` with a `<td>` contains an `<a href>` | Pass — 473 sourced table rows |
| `scripts/source_coverage.py` | Each row should carry a recognised official-domain reference | Pass — every row carries `nfl.com` or `operations.nfl.com` plus a recognised methodology host (`nist.gov`, `scipy.org`, `scikit-learn.org`, `statsmodels.org`, `docs.github.com`) |
| `scripts/audit_repo.py` | Every `data/**/*.csv` must parse with unique headers | Pass — 12 new registers, unique headers, parsed by the audit |
| `assurance-ci.yml` | `git diff --exit-code -- data/assurance docs/assurance` after regeneration | Regenerated and committed at integration |
| `tools/run_tests.py` | Every `tests/test_*.py` must be loadable by the stdlib runner | `tests/test_nfl_3b81013c.py` uses the `unittest.TestCase` class form the runner discovers |

---

## 6. Data-rights position

This pack is a research document. It **does not**:

- scrape NFL.com or operations.nfl.com at request time — every page was read manually, once, and only the cited value and URL are stored;
- republish article text, images, video, logos or box scores;
- quote, derive or imply a sportsbook price;
- make any wagering recommendation or profitability claim.

NFL.com Terms of Use sections 1.3 (non-commercial informational use), 11(f) (no automated harvesting) and 12 (no use for wagering on NFL games) are recorded as verified facts on the Sources page and are treated as the binding constraint on every commercial or market-facing extension described in the suggestions register. A reviewer extending this pack commercially must obtain written consent or a licence first; that is registered as open question Q-01 and is gate VG-01.

---

## 7. Coordination record

- Claimed `NFL-3B1`…`NFL-3B8` in `COORDINATION.md` before writing files; claim commit `3f130b4` was pushed immediately.
- Three other NFL sessions were active on 12 November 2026 (`arena/efebf74f-own6`, `arena/34dacba5-own6`, `arena/8132a3b1-own6`). They had claimed `docs/nfl/**` and `docs/nfl-origination/**`. **No file under those paths was read for modification, written, or renamed by this session.**
- This pack writes only under `docs/nfl-3b81013c/`, `data/nfl_3b81013c/`, `src/nfl_3b81013c/`, plus five named files listed at the top of this document, and the shared `COORDINATION.md`.
- Requests to other sessions' owners are logged in `COORDINATION.md`: N-01 through N-06 above, and the README navigation additions for final integration.
- `README.md` and `docs/index.html` are shared outputs and were **not** edited; the navigation request is logged rather than applied.

---

## 8. Reproduction

```bash
git fetch --unshallow origin        # required: scripts/audit_repo.py pins BASE=86eca0f
python3 scripts/audit_repo.py       # regenerates data/assurance/*
python3 scripts/build_nfl_3b81013c.py
python3 scripts/check_nfl_3b81013c.py
python3 -m unittest tests.test_nfl_3b81013c -v
python3 tools/release_gate.py
```
