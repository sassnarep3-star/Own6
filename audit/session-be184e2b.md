# Session audit — independent verification close-out (`arena/be184e2b-own6`)

**Date:** 2026-11-03 (UTC) · **Branch:** `arena/be184e2b-own6` · **Base:** `main` @ `f2877f3` (PR #30 merged)
**Scope claimed in `COORDINATION.md`:** V1 verification ledger, V2 remediation of 31 advisory rows in `docs/verified/**` (60-minute handoff from session `05e359b8`), V3 integration.

## 1. What I set out to test

The prior integration recorded two open issues: 31 table rows on `docs/verified/**` without an official source link, and no independent line-by-line audit of published values in this checkout. This session re-read the published values against official pages rather than trusting earlier records, then made the gap explicit in machine-checkable data.

## 2. Method

1. For each value: open the official page for *that row*, read it, record the value seen, the URL and the date in a CSV ledger.
2. Compare ledger value to the committed value by script; any difference is a `MISMATCH` and fails the build.
3. Anything not read from an official page is **not** marked verified: its published value stays blank and it is listed with a reason and the official page a reviewer should consult.
4. Every generated table row must carry at least one official https link; internal links must resolve; a Python-repr or merge-marker leak fails the build.

## 3. Official pages opened in this session

| # | Page | Used for |
|---|---|---|
| 1–15 | `https://www.nba.com/game/<slug>-<id>` for game ids 0022600158–0022600172 | final scores of the 2026-11-02 slate |
| 16 | `https://www.nba.com/standings` (both chunks) | 30-team W-L |
| 17 | `https://www.nba.com/games?date=2026-11-02` | slate size (15 games) |
| 18 | `https://www.nba.com/schedule?date=2026-11-02` | schedule page structure / preview links |
| 19 | `https://www.nba.com/termsofuse` (§1, §6, §9) | rights restrictions |
| 20 | `https://www.nba.com/stats/help/faq` | no bulk download |
| 21 | `https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets` | official release, 26 Oct 2026 |
| 22 | `https://www.nba.com/stats/help/glossary` | metric definitions (context) |
| 23 | law.go.kr whole-law page | statute identity / effective dates |
| 24 | law.go.kr Article 26 page | 제26조 text |

## 4. Result

- **54 ledger checks, 54 match, 0 mismatch.** 15 scores, 30 standings, 9 rights/law rows.
- No committed value required correction in this session. The audit therefore confirms the scores/standings that earlier sessions published, and does not upgrade any unverified market or prop value.
- 8 items are recorded as unverified with blank values (see `data/verification_unverified_2026_11_03.csv`).
- 7 irregularities are published on the verification Flagged page (V-F1…V-F7).

## 5. V2 remediation (31 advisory rows)

The 31 rows were **not** values that could be sourced; they were editorial rows (gate rules, flags) and press-only claims. Fix applied in `scripts/build_site.py`:

- Gate rows (G1–G8, on `strategies.html` and `methodology.html`) gain a column **“Official reference for the rule”** pointing at the document that defines the rule: 국민체육진흥법 제26조, NBA Stats FAQ, the NBA release, scikit-learn cross-validation, NIST binomial, NBA Terms §9, statsmodels `multipletests`, SciPy `pearsonr`.
- `nba-policy.html` press rows gain an **“Official status of this row”** column linking the official release and stating **not enumerated**, so the row shows both what is claimed and what the official record actually says.
- `flagged.html` rows gain an **“Official reference”** column (statute, NBA Terms, official release, Stats FAQ, or the GitHub repository for repo/site flags).
- `sources.html` gains an **“Official status”** column: verified rows say so; press rows link the release and say *not confirmed*.

`tools/check_site.py` now reports **0 errors, 0 advisories** (previously 31 advisories). No data JSON values were changed.

## 6. Irregularities recorded (never silently resolved)

| ID | Severity | Item |
|---|---|---|
| V-F1 | high | NBA Terms §6 restricts links to internal pages; this site links internal NBA game/schedule pages as its audit trail |
| V-F2 | medium | The Korean statute shows two different effective dates (2026-09-03 whole-law view vs 2026-06-02 Article 26 view) |
| V-F3 | high | NBA Terms §9 bars gambling-connected use of NBA Statistics; no authorisation or legal opinion exists |
| V-F4 | high | Market/prop prices are ESPN relay only; no official or licensed odds source; no capture times, so no CLV |
| V-F5 | medium | Press-reported prop/parlay restrictions are not enumerated in the official NBA release |
| V-F6 | low | 79 of 92 earlier score rows were not re-read in this session (aggregate W-L cross-check passes) |
| V-F7 | medium | One teammate correlation uses ESPN game logs and n = 6; unusable for pricing |

## 7. Limits of this audit

- It tests **correspondence with official pages**, not predictive value. Nothing here supports a betting edge.
- Live NBA pages are dynamic; a value verified today may be presented differently tomorrow (e.g. standings change nightly). The ledger stores the read date for that reason.
- Fetching was done by page retrieval; no bulk NBA feed is used (NBA Stats FAQ forbids download). This limits how many rows can be re-read per session.

## 8. Reproduce

```bash
python3 scripts/build_verify.py     # rebuild docs/verify from the committed ledger
python3 scripts/check_verify.py     # completeness, official-source and link checks (73 table rows)
python3 tools/check_site.py         # repo-wide row/source gate (0 errors, 0 advisories)
python3 tools/release_gate.py       # published HTML integrity
python3 -m pytest tests -q          # 34 tests
```
