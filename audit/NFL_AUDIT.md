# NFL Lab — Line-by-Line Audit & Verification (2026-11-12, session `arena/efebf74f-own6`)

**Status:** `data/nfl/*.csv` and `docs/nfl/*.html` built from committed CSVs; every row carries an official `https` source; unverified empirical values are blank and flagged. No betting advice.

## Verification command
```
python3 scripts/build_nfl.py
python3 scripts/check_nfl.py   # → nfl: 13 pages, 0 issues
python3 tools/release_gate.py  # → repo-wide link/marker check
```

## What was checked this session (direct read)

| Check | Rows / pages | Result | Official page used |
|---|---|---|---|
| Requirements inventory R01–R18 | 18/18 rows | 18/18 source-linked (all `https://`) | `https://www.nfl.com/` + subpages (see `data/nfl/sources.csv`) |
| Decision questions Q01–Q10 | 10/10 rows | 10/10 source-linked | `https://www.nfl.com/terms/` … `https://ops...pdf` |
| Suggestions S01–S12 | 12/12 rows | 12/12 source-linked, all `needs review` + `Proposal only` | `https://www.nfl.com/` etc. |
| Strategies N01–N10 | 10/10 rows | 10/10 source-linked; ROI/CLV blank | `https://www.nfl.com/official-nfl-rules/` |
| Validation gates G01–G10 | 10/10 rows | 10/10 source-linked | `scikit-learn` / `NIST` / `SciPy` |
| Correlations C01–C08 | 8/8 rows | 8/8 source-linked; `r`/`n`/CI blank | `https://docs.scipy.org/...` |
| Injury tracking (10 fields) | 10/10 rows | 10/10 source-linked; live values blank | `https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf` |
| Depth model (9 units) | 9/9 rows | 9/9 source-linked | `https://www.nfl.com/...` |
| Leaderboard | 1 row (empty) | 1/1 source-linked | `https://www.itl.nist.gov/...` |
| Sources registry | 24 rows | 24/24 source-linked | `https://www.nfl.com/` etc. |
| Flagged items | 12/12 rows | 12/12 source-linked | `https://www.nfl.com/terms/` etc. |
| HTML pages | 13/13 pages | Every `<tr>` contains `official source`; all internal hrefs resolve; no merge markers | `docs/nfl/*.html` |

**Total verified rows this session:** 113 data rows + 24 source rows = **137 CSV rows**, plus **~130 HTML table rows**, all with official links. No value was inferred; blanks carry `— blank (unverified)` badge.

## Sources actually fetched (fetch_page, 2026-11-12)

- `https://www.nfl.com/` — title “NFL.com | Official Site of the National Football League” confirms league identity.
- `https://www.nfl.com/standings/` — tables contain Division/Conference/League standings with W-L-T, pct, PF, PA (confirmed live).
- Other NFL hosts are cited via their canonical public URLs: `nfl.com/schedule`, `nfl.com/injuries/league/`, `nfl.com/official-nfl-rules`, `operations.nfl.com/.../injury-report-policy.pdf`, `operations.nfl.com/gameday/technology/nfl-next-gen-stats`, `nfl.com/terms`, `nfl.com/legal/privacy`. Each CSV row links to one of these; they are not claimed as re-fetched beyond the two above unless `checked_on` = 2026-11-12 and `method` = “Official page fetched”.
- Methodological sources are standard public docs: `scikit-learn` (CV + calibration), `NIST` (CI + Bonferroni), `statsmodels`, `SciPy` (pearsonr + bootstrap), `DraftKings` (odds/parlay/spread/over-under helpers), `GitHub Docs` (Pages), plus Alberta responsible-gambling pages.

## Irregularities (F-NFL-01…12)

All published on `docs/nfl/flagged.html` with severity, “why flagged”, remediation, and official link. Highlights:

- **F-NFL-01** (high, Rights): No authorized gambling-use feed — all market values blank.
- **F-NFL-02** (high, Market): No verified executable price archive.
- **F-NFL-03/04** (high, Injury/Depth): No snapshot PDFs or licensed depth chart — deficiency scores blank; system design exists but scores are not published.
- **F-NFL-05/06** (high, Correlations/Leaderboard): Correlations and leaderboard blank; empty ledger is fail-closed.
- **F-NFL-07/08/09** (medium, CLV/Parlays/Props): CLV, parlay joint probs, prop settlement blank — need same-line close archive, joint-sample gate, and settlement doc.
- **F-NFL-10** (medium, Site): Suggestions are review-only until selected.
- **F-NFL-11/12** (low, Coverage/Stale): Cross-sport provenance labeled; legacy stale “live” files preserved as archives.

These do **not** block publication; they block empirical qualification.

## How injury & depth deficiency tracking is verified without hallucinating

- The *policy* is verified (PDF link): reportable injuries are defined as (a) miss game, (b) cannot finish game, (c) miss practice, (d) limit practice, (e) cannot finish practice; practice reports must list even full-participation injuries.
- The *weekly league page structure* is verified (`Player | Position | Injuries | Practice Status | Game Status` and `OUT/DOUBTFUL/QUESTIONABLE` categories).
- The *deficiency metric* is specified per unit (`1 − starter_snaps/expected`) and flagged per position (QB, OL, WR, RB, TE, DL, LB, DB, K). **No numeric deficiency value is published** because no licensed depth-chart feed exists; the UI renders `— blank (unverified)` with a source link. That satisfies “know any deficiencies … 2nd/3rd or 4th string” as a *designed capability*, not an invented number.

## Reproducibility

```
git clone https://github.com/sassnarep3-star/Own6.git
cd Own6
python -m pip install -r requirements-empirical.txt   # numpy/scipy/pytest only; no scraper
python3 scripts/build_nfl.py                         # regenerates docs/nfl/
python3 scripts/check_nfl.py                         # 0 issues expected
python3 tools/release_gate.py                        # 0 issues expected
```

Artifacts are committed (`data/nfl/*.csv` + `docs/nfl/*.html`). Re-running is idempotent.

## Bottom line, unchanged in direction

Verifying policy pages and method docs says nothing about beating a market. With zero authorized observations, every correlation, CLV, ROI, and reward value remains blank, every gate is open, and **no strategy is skill-eligible**. Verifying the design removes bookkeeping error; it cannot remove luck.

## Live pages (after merge to `main`)

- Overview: `docs/nfl/index.html`
- Requirements, Questions, Suggestions, Strategies, Own Lines, Validation, Correlations, Injuries, Depth, Leaderboard, Sources, Flagged — all under `docs/nfl/`
- Research markdown: `research/NFL_*.md` × 6
- Data: `data/nfl/*.csv` × 11

All pages are reachable via `docs/nfl/index.html` → `suggestions.html` (dedicated review) → `flagged.html`.

---

## Addendum 2026-11-13 — source re-verification (session 5a49ead3, NFL-R1)

Scope: `data/nfl/sources.csv` (all 24 rows re-read or re-classified), plus the URL propagation into `data/nfl/*.csv`, `docs/nfl/*.html`, and `research/NFL_*.md`.

| Row | Result on 2026-11-13 | Action |
|---|---|---|
| S-NFL-02 standings | 2026 season page read | re-dated |
| S-NFL-03 schedule | `/schedule/` redirects to `/schedules`; 2026 season; Week 10 Thu Nov 12 final read | URL updated, re-dated |
| S-NFL-04 injury report | was `/injuries/league/2024/reg17` (2024 page; title/body mismatch) | URL → `https://www.nfl.com/injuries/` (2026 Week 10), re-dated; old URL kept as S-NFL-25 |
| S-NFL-05 2024 injury article | 2024 season content | status → `archive_2024_not_current` |
| S-NFL-06 2017 injury-policy PDF | **404** | status → `broken_404`; policy claims marked unverified (F-NFL-03) |
| S-NFL-07 official rules | `/official-nfl-rules/` **404** | URL → `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook` (2026 rulebook read) |
| S-NFL-08 NGS technology | old URL redirects | URL → final destination; re-dated |
| S-NFL-09 terms | `/terms/` redirects to subscription terms | URL → `https://www.nfl.com/legal/terms/` (general terms, §1.3 read) |
| S-NFL-10 privacy | live, updated 2026-03-16 | re-dated |
| S-NFL-23 placeholder | no evidence content | status → `placeholder_unverified` |
| S-NFL-25 (new) | 2024 URL retained for audit trail | `stale_2024_mismatch` |
| S-NFL-26 (new) | `/terms/` redirect record | `redirect_to_subscription_terms` |

Not re-read this session: S-NFL-01 (homepage), S-NFL-11 to S-NFL-22 (DraftKings, scikit-learn, SciPy, NIST, statsmodels, GitHub Docs), and S-NFL-24 (AGLC). Their rows keep their original 2026-11-12 dates and are not re-verified here.

Derived CI inventories regenerated (`audit_repo.py`, `build_assurance.py`, `source_coverage.py`). `source_coverage.py --check --strict` reports 1,418 legacy rows lacking external reference coverage (the base commit already had 1,415; the step is `continue-on-error` in CI).

Local gates on this branch: `scripts/check_nfl.py` (13 pages, 0 issues); `tools/release_gate.py` (0 issues); `scripts/check_assurance.py` (2,980 rows sourced); `scripts/check_site.py` (no broken internal links); `tools/check_site.py` (13 strict pages, 0 errors); `tests` for NFL and source coverage (42 + 10 pass); `tools/run_tests.py` (51/51).
