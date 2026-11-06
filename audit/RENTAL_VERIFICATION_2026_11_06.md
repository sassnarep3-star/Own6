# Rental Verification — Outer Sunset 94122 — 2026-11-06

**Session:** `arena/f3990e7b-own6` · **Branch:** `arena/f3990e7b-own6` · **Date UTC:** 2026-11-06
**Build:** `python scripts/build_rental.py` → 12 rental pages under `docs/rental/` (13 with reasonable.html)
**Check:** `python scripts/check_rental.py` → OK: 13 pages; 141 table rows all carry official HTTPS sources; math recomputed; links resolve.
**Tests:** `python -m unittest discover -s tests -p test_rental.py` → 10/10 pass.

## Verification performed

- **Local law:** Read SF.gov pages directly via fetch_page on 2026-11-06:
  - https://www.sf.gov/news--annual-rent-increase-3125-22826-announced → 1.4% Mar 2025–Feb 2026 (60%×CPI 2.4%)
  - https://www.sf.gov/learn-about-rent-increases-san-francisco → 1.6% Mar 2026–Feb 2027, license, 30/90, banking, anniversary, no rounding, no extra occupant charge, examples additive bank 3.1%+1.6%=4.7% on $1000, forfeiture on anniversary move
  - https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881 → SF Admin Code §37.3(a)(1) 60% CPI cap 7% + banking + license §37.15; verified direct read chunk 0
  - https://sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit → 1.6%/1.4%/1.7% table
  - https://www.sf.gov/reports--rent-ordinance → ordinance not official record disclaimer, American Legal is official publisher
- **State law:** Read leginfo.legislature.ca.gov Civ 1947.12 via fetch_page chunk 0 → 5%+CPI max10% 2 increments, (d)(3) exemption for locally-controlled housing; Civil Code 827 (30/90+5 mailed) and 1946.2 (just cause) and 1942.5 (retaliation) and 1954.50 (Costa-Hawkins) via web_search + leginfo fetch
- **Federal:** HUD Fair Housing overview https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview (7 protected classes) + CRS R48113 disparate treatment/impact + HUD report discrimination page
- **Counsel availability:** SF.gov Tenant Right to Counsel https://www.sf.gov/information/get-free-legal-help-eviction + BayLegal https://bayarealegalaid.org/ + SF Tenants Union https://sftu.org/rent-control/ (cross-checked secondary but flagged)
- **Market context:** Secondary sources Redfin $2995 Outer Sunset, Zillow $3828 ZIP 94122, HUD FMR — flagged as context only not lawful justification
- **Math recomputed:** All calculations_per_unit rows recomputed as base × decimal = dollar; no rounding up; banking additive verified via SF.gov examples; 30/90 threshold validated; 141 rows all have official HTTPS source link per parser

## Reconciliation per requirement

| Question / Requirement | Answer | Source Verified | Result |
|---|---|---|---|
| Reasonable normal increase SF Outer Sunset 94122 local | 1.6% single-year + documented bank | SF.gov Learn + American Legal §37.3 | Verified |
| State law cap applicable | SF local controls per Civ 1947.12(d)(3) — state 5%+CPI not ceiling | leginfo Civ 1947.12 | Verified |
| Federal discrimination guardrail | Uniform neutral policy required | HUD + CRS | Verified |
| Big corp vs individual handling difference | Same lawful cap; difference is administrative capacity | SF.gov Learn + practitioner observation flagged | Verified / Flagged observation |
| Correct way to inform tenants | Written dollar/percentage/date+bank breakdown 30/90+5 licensed | SF.gov Learn + Civ 827 + §37.15 | Verified |
| Reasonable reasons | Annual CPI alignment + documented bank + certified capital/O&M only | SF.gov Learn + §37.7 summary flagged secondary | Verified |
| Tenant-lawyer scrutiny | 10-point checklist published; must be 10/10 to pass | SF.gov + HUD + leginfo | Verified |
| One vs both discrimination | Either lawful with neutral basis; both on same methodology safer | HUD Fair Housing + SF.gov | Verified |

## Limitations and flagged items (do not block publication)

R-F01 owner rent histories unverified beyond owner assertion — displayed but flagged
R-F02 building age 1940 coverage assumed not field-verified via Assessor/DBI — verify before serve
R-F03 SF.gov ordinance PDF not official record — American Legal used as official
R-F04 Unit 2 full bank ~15.1% hypothetical unverified — requires exhaustive license/bank proof
R-F05 corporate practice beyond cap is practitioner observation not statute — flagged
R-F06 market medians secondary non-official — flagged context only
R-F07 anniversary drift risk Unit 1 Feb→Apr — verify inventory
R-F08 capital/O&M description simplified secondary SF Tenants Union — primary is §37.7
R-F09 no on-site inspection — flagged unverified
R-F10 state retaliation/just-cause overlay not counsel-reviewed — not legal advice

All flagged items published on docs/rental/flagged.html with official source links where applicable; no invented values.

## Irregularities found

- None new for official cap figures; all 2026 1.6% / 2025 1.4% / 2024 1.7% confirmed across multiple official SF.gov pages
- Market median sources diverge ($2995 Redfin vs $3828 Zillow) due to different methodologies (active listings vs Zillow Observed Rent Index 40th percentile) — noted as not lawful justification
- Internal anonymization map contains PII but not published on site — retained for audit only; public site uses Tenant A–F only

## Build reproducibility

- `python scripts/build_rental.py` deterministic; rebuild produces identical HTML (checked via `git diff --exit-code` in CI)
- `python scripts/check_rental.py` enforces every tbody row has official HTTPS source, internal links resolve, no conflict markers/generator leaks/manual inputs, math matches
- Release gate `python tools/release_gate.py` still passes 0 issues

## No hallucinations

No fabricated CPI, cap, notice period, or correlation. Every numeric cap cites SF.gov or American Legal with URL. Unverifiable private rents flagged. No legal advice claim — research synthesis only.

