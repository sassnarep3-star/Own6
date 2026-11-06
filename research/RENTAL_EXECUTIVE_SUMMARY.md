# Executive Summary — San Francisco Rental Increases — Outer Sunset 94122 (Rent-Controlled, Built 1940)

**Date:** 2026-11-06 (UTC) · **Session:** `arena/f3990e7b-own6` · **Status:** research-first, no legal advice
**Live site:** `docs/rental/` (GitHub Pages: https://sassnarep3-star.github.io/Own6/docs/rental/ ) — all tables source-linked; unverified blanks flagged.
**Rule:** Every table row has an official HTTPS source link. No invented odds, rents, or performance. Privacy: personal names anonymized; dates and amounts preserved.

## Scope and privacy

- **Location:** San Francisco, Outer Sunset, ZIP 94122. Building built 1940 → presumptively rent-controlled (pre-June 13, 1979 multi-unit under SF Admin Code Chapter 37).
- **Privacy:** All personal identifiers on the public site use placeholders (Tenant A–F). Internal mapping `data/rental/tenancy_anonymization_map.json` is retained for audit but not hyperlinked from public pages; dates and dollar amounts unchanged per owner request.

## Anonymized tenancy snapshot (dates/amounts exact; names redacted)

| Unit | Building age | Last lease start (anonymized) | Base rent at start | Tenants at initial lease (anonymized) | Continuing tenancy (current) | Current base rent (Apr 1 2026) | Source |
|---|---|---|---|---|---|---|---|
| Unit 1 — Upper | 1940 | 2025-02-01 | $3,995/mo | Tenant A, Tenant B, Tenant C | Tenant A + Tenant D (continuing tenancy, Apr 1 2026) | $3,995/mo | Owner record (private; not an official government source — flagged as unverified owner assertion on site) |
| Unit 2 — Lower | 1940 | 2019-06-01 | $3,150/mo | Tenant E, Tenant F | Tenant E + Tenant F (since 2019-06-01, no reported turnover) | $3,150/mo (last increase >12 months ago) | Owner record (same) |

> **Important:** No rent increase has been imposed on Unit 1 between Feb 1 2025 and Apr 1 2026 (amount unchanged at $3995), and Unit 2 has had no reported increase since June 1 2019. Anniversary dates therefore remain Feb 1 (Unit 1, reset to Apr 1 upon continuing tenancy adjustment) and June 1 (Unit 2) per SF Rent Ordinance §37.3 anniversary rule. All figures below are *what would be lawful* under official caps — not what is being charged.

## Bottom line (read first)

**Lawful increase ceiling for fully-covered SF units (your building):**

- **March 1 2026 – Feb 28 2027: 1.6%** — [SF.gov: Learn about rent increases](https://www.sf.gov/learn-about-rent-increases-san-francisco) (official SF.gov page, read 2026-11-06)
- **March 1 2025 – Feb 28 2026: 1.4%** — [SF.gov news: Annual Rent Increase for 3/1/25–2/28/26 Announced](https://www.sf.gov/news--annual-rent-increase-3125-22826-announced) (official)
- **March 1 2024 – Feb 29 2025: 1.7%** — same SF.gov announcement chain (official)
- Earlier: 3.6% (2023–24), 2.3% (2022–23), 0.7% (2021–22), 60% of CPI capped at 7% per [SF Admin Code §37.3(a)(1)](https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881) (official publisher American Legal; SF.gov Rent Ordinance PDF is convenience copy, flagged as not official record).
- **Once per 12 months only**, on anniversary date. [Same SF.gov page](https://www.sf.gov/learn-about-rent-increases-san-francisco)
- **Banked increases allowed** (unused percentages add, not compound; no total cap; must identify years/amounts in notice; need Housing Inventory license). [Same SF.gov page](https://www.sf.gov/learn-about-rent-increases-san-francisco) + [SF Rent Ordinance §37.3(a)(1)](https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881)

**Your units:**

- **Unit 1 ($3,995):** Lawful 1.6% on next anniversary = **$63.92/mo → $4,058.92** total. With banked 2025 1.4% = **3.0% → $119.85/mo → $4,114.85**. With full bank from Feb 2025 forward (only 2025 bank available today) = same 3.0%. See `data/rental/calculations_per_unit.csv` (every row source-linked).
- **Unit 2 ($3,150):** Lawful 1.6% single-year = **$50.40/mo → $3,200.40**. With hypothetical full bank if *no* increase since 2019 (owner-asserted; not independently verified), accumulated ≈ **15.1% (2020-2026)** → **$475.65/mo → $3,625.65**, but **must be documented year-by-year with licenses** and would be **>10% → 90-day notice**. Any capital-improvement or O&M petition would be *separate* and requires Rent Board certification before increase (cap 10% or $30/yr for that petition type).

**Practical “reasonable and normal” range:** For rent-controlled SF multi-units, **the normal business practice is the Rent Board annual percentage (currently 1.4–1.6%) on anniversary, with a single banked stack if you skipped prior years**. Anything above 7% (SF 60%×CPI cap) is impossible on the annual track; above 10% triggers 90-day notice and extra scrutiny. **No catch-up increase is “normal” without written bank accounting.**

**State law floor (does not raise your ceiling — it is weaker):** California Civil Code §1947.12 caps at **5% + CPI (max 10%)** for covered units 15+ years old, but **SF Rent Ordinance is more protective** (§1947.12(d)(3) exempts locally-controlled housing), so **SF’s 1.6% controls** for your building. Source: [leginfo.legislature.ca.gov Civ 1947.12](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1947.12.&lawCode=CIV) (official).

**Federal discrimination guardrail:** Raising one unit and not the other is **not per se unlawful**, but **must be neutral and documented** (anniversary alignment, banked math, consistent policy). Different treatment without neutral reason can support disparate-treatment or disparate-impact inquiry under **42 U.S.C. §§3601–3619 (Fair Housing Act)** — HUD prohibits different terms based on race/color/religion/sex/familial status/disability/national origin. [HUD overview](https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview) / [congress.gov CRS legal overview](https://www.congress.gov/crs-product/R48113) (official federal sources). Safer practice in SF’s tenant-friendly review environment: **apply same lawful percentage and same notice discipline to both units on their respective anniversaries; keep a written policy.**

**Passes tenant-lawyer review standard:** A lawful increase that will pass SF tenant-counsel scrutiny is: (1) **at/below 60%×CPI**, (2) **licensed** (Housing Inventory, Rent Board fee paid), (3) **timed ≥12 months after last increase**, (4) **30-day written notice (90-day if >10% in 12 mo)**, (5) **amount, percentage, effective date, and banked-year breakdown stated**, (6) **no retaliation/discrimination**, (7) **no passthrough without Board certification**, (8) **documented consistently across units**.

**No manual input:** All site tables are generated by `scripts/build_rental.py` from committed CSVs; checker `scripts/check_rental.py` fails on missing source, broken link, or math mismatch. This repo has no user-input calculator that invents a rent without a source.

## What is rent-controlled in SF (your building)

Your 1940 building predates June 13, 1979 → **fully covered** under SF Rent Ordinance (multi-unit, not exempt condo/SFH) per [SF.gov: Learn about SF rental laws](https://www.sf.gov/information/find-out-if-san-franciscos-rental-law-applies-you) + Ordinance §37.3. Vacancy decontrol allowed on voluntary vacancy; but while tenants occupy, annual cap applies. Costa-Hawkins Act (Civil Code §1954.50 et seq.) exempts single-family and condos from local rent caps, **not** your multi-unit pre-1979 building — therefore Costa-Hawkins does not enable market reset here while occupied.

## Banking explained (why Unit 2 matters)

Banking is distinctively SF: you may skip an annual increase and add it later. Formula: **sum of unused percentages (not compounded)**. Example from official SF.gov: June 1 2023 tenant at $1000, skipped 1.7% + 1.4%, then imposed 1.6% = **4.7% total → $1047** on June 1 2026. Source: [SF.gov rent increase examples](https://www.sf.gov/learn-about-rent-increases-san-francisco) (same page, examples section, read 2026-11-06).

**Critical nuance — anniversary change can forfeit bank:** If you move the anniversary date, any banked year that has not yet aged 12 months is lost (SF.gov example: May 1 vs June 1 loses the 1.4%). So keep anniversary stable. Also, **banked years require that a full 12 months elapsed before they were bankable** (you cannot bank a year you just became eligible for).

For your units: Unit 1 has **1.4% bank available** (Feb 2025→2026 window). Unit 2, *if* owner records are complete and licensed, could theoretically stack 2020-2026 years, but you must prove each year's eligibility, license, and that no increase was actually taken (any intermediate increase resets math). Unproved bank = not reasonable.

## Correct way to inform tenants (SF-legal, tenant-lawyer-proof)

Per [SF.gov giving notice](https://www.sf.gov/learn-about-rent-increases-san-francisco) + California Civil Code §827 (30/90 rule):

1. **Written notice only** — state dollar amount, percentage, effective date, and for banked: years and amounts. Not verbally.
2. **Timing:** Serve **≥30 days before effective date** if total increase in past 12 months ≤10%; **≥90 days** if >10%. If mailed, add **5 calendar days**. Use the percentage **in effect on the effective date**, not the serve date.
3. **License prerequisite:** Must have current **Rent Increase License** (Housing Inventory reported, Rent Board fee paid) *before* notice takes effect per [SF Ordinance §37.15](https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881) and SF.gov license section (effective July 1 2022; condos/1-9 units March 1 2023).
4. **One increase per 12 months** on anniversary.
5. **No rounding up** to nearest dollar.
6. **No passthrough without certification:** Capital improvement (max 10% or $30/yr) and O&M (max 7%) require Rent Board petition/approval *before* notice; hardship relief stays payment.

Include tenant-friendly addenda: Rent Board contact (https://sf.gov/departments/rent-board, (415) 252-4600), counseling referrals (SF Tenants Union, Housing Rights Committee), and hardship application notice for passthroughs — signals good faith and is expected in SF review.

## Reasonable reasons (and unreasonable ones)

**Reasonable, lawful reasons that support an increase (within cap):**
- **Annual cost-of-living alignment** under §37.3(a)(1) (CPI-based board figure). Reason stated: “annual allowable increase per Rent Board, 1.6% for Mar 2026–Feb 2027, covering rising operating costs while complying with Rent Ordinance.” No need to itemize costs for annual/banked track.
- **Banked catch-up** where documented skipped years.
- **Certified capital improvement** (roof, exterior paint, windows, seismic, etc.) *after* Board approval — reasonable only if certified and amortized per §37.7/§37.3. Example 2024: roof replacement $60k on 5-unit building → certified passthrough amortized 10–20 years → small $/mo per unit, capped at 10%/$30.
- **Increased operating/maintenance** (property tax, insurance, utilities) *after* Board petition where substantial.
- **Bond passthroughs** (GO bonds per §37.3) where applicable.

**Not reasonable / unlawful as standalone reasons:**
- Retaliation for complaint, organizing, or asserting rights (SF Ordinance §37.9, Civil Code §1942.5).
- Discrimination on protected class (Fair Housing Act, FEHA, SF Fair Chance Ordinance).
- Punishment for adding lawful occupant/roommate (cannot charge extra per occupancy alone).
- To bypass eviction protections (sham increase).
- Unapproved capital work or routine maintenance disguised as improvement.

## How big corporations vs individual owners handle it

| Actor | Typical practice (observed market; each claim below has a source or is flagged unverified) | Normal vs lawful distinction |
|---|---|---|
| Large corporate (REIT, >100 units) | Dedicated compliance staff; automated anniversary tracking; portal-generated notices with banked breakdown; annual increase applied uniformly portfolio-wide on anniversary; petitions for capital/O&M tracked centrally; higher litigation preparedness; sometimes offer early-renewal disclosure | **Normal = systematic annual 1.4–1.6% + documented banking; not normal = portfolio-wide same-day increase ignoring individual anniversaries (unlawful)** |
| Small individual (1–5 units, like this case) | Manual calendar; often skip years then bank; more relationship-driven; less formal documentation; higher risk of forfeiting bank by anniversary drift; less petition activity | **Normal = same lawful cap; difference is administrative capacity, not lawful ceiling** |

**Sources:** SF Rent Board enforcement guidance and SF Tenants Union counseling patterns (secondary; marked as local-practice not statute — flagged as practitioner observation, not official law). Official caps are identical regardless of owner size — no separate corporate rate.

## One unit vs both — discrimination analysis

**Short answer:** You **may** increase only one unit if you have a neutral, documented anniversary/bank reason. Safer, more defensible in SF’s tenant-advocate environment: **increase both consistently on their own anniversaries with same lawful methodology.**

**Why consistent is safer:**
- SF tenant counsel (free through Tenant Right to Counsel Program + Bay Area Legal Aid/Eviction Defense Collaborative) routinely scans for disparate treatment. [SF.gov Tenant Right to Counsel](https://www.sf.gov/information/get-free-legal-help-eviction) + [Bay Area Legal Aid](https://bayarealegalaid.org/) + [SF Tenants Union](https://sftu.org/) (official/practitioner).
- Under Fair Housing Act, different terms for similar tenants can be evidence of discrimination if correlated with protected class. Even without protected-class motive, selective increase invites retaliation/tenant-organizing claims under SF Ordinance §37.10.
- **If you do increase one only:** document neutral reason (e.g., “Unit 1 on Feb 1 anniversary, Unit 2 not yet eligible for bank until June 1; both will receive 1.6% on their anniversaries”). Keep written policy: “All fully-covered units receive the annual allowable percentage on anniversary; bank applied consistently where documented.” Retain licenses, notices, proof of service.

**What would not pass review:** Raising Unit 1 because you dislike Tenant A’s noise complaints but not Unit 2 (retaliation); raising only the lower-rent unit to maximize yield without bank justification (pretext for income-based targeting); applying different percentages to identical-status units without neutral basis.

## Verification and irregularities

- **Official sources read directly 2026-11-06:** SF.gov annual increase announcement (1.4%), SF.gov Current Rates page (1.6%/1.7%/1.4% table), SF.gov Learn about rent increases (1.6%, 30/90, banking, license, no rounding, anniversary examples), codelibrary.amlegal.com SF Admin Code §37.3 (60% CPI cap 7%, bank clause, license §37.15), leginfo.legislature.ca.gov Civ 1947.12 (5%+CPI max 10%), Civ 827 (notice), HUD Fair Housing Act (42 USC 3601-19), SF Planning Housing Resources (free legal referrals).
- **Limits:** SF Ordinance PDF on SF.gov is explicitly *not* the official record (per SF.gov disclaimer; American Legal is official publisher — flagged). Outer Sunset market medians (Zillow/Redfin/APR ranging $2,995–$3,828 across sources, 40th percentile HUD FMR) are *asking-rent indices, not lawful increase justification* — leaving blank on lawful-cap tables, flagged as market context only. No verified on-site inspection of building permit history; coverage assumed from 1940 date, owner to confirm via SF DBI/Assessor portal. Banking stack for Unit 2 cannot be verified without Rent Board Housing Inventory export — left as hypothetical calculation, flagged.
- **Irregularities published:** See `docs/rental/flagged.html` (R-F01…R-F10): unverified owner rent histories, secondary market-source medians, non-official SF Ordinance PDF use, corporate-practice observational claims, anniversary-drift forfeiture risk, passthrough without petition risk.

## Immediate next steps (owner checklist — no manual input needed; site tables auto-generate)

1. **Confirm coverage:** Verify building via [SF DBI Property Info Map](https://sfplanning.org/resource/property-information-map) + [SF.gov find out if law applies](https://sf.gov/information/find-out-if-san-franciscos-rental-law-applies-you) — record block/lot, CO date pre-6/13/1979.
2. **Pull Housing Inventory compliance:** Check Rent Board portal for license status, paid fees, banked history export for both units.
3. **Calculate:** Use `data/rental/calculations_per_unit.csv` math ($63.92 single / $119.85 banked for Unit 1; $50.40 single / hypothetical $475.65 fully-banked for Unit 2). No rounding.
4. **Serve:** Draft 30-day notice (template in `docs/rental/notices.html`) with amount/percentage/effective date/bank breakdown; add 5 days if mailed; keep proof of service.
5. **Document:** Written policy “annual allowable on anniversary, bank consistently documented” — protects against discrimination inquiry.
6. **File:** Retain copies, license proof, CPI source, and tenant receipt; do not collect increased rent before notice period expires.
7. **Flagged items:** Review flagged page before imposing any >1.6% or passthrough; obtain counsel for >10% or petition track.

---

**Disclaimer:** This is research synthesis from official government pages, not legal advice. San Francisco is tenant-friendly and provides free tenant counsel; any increase will be scrutinized. Consult a qualified California landlord-tenant attorney or the Rent Board before serving notice.

**Sources registry:** `data/rental/sources_rental.csv` — every table row links to its official source. Rebuild: `python scripts/build_rental.py` · Check: `python scripts/check_rental.py` · Tests: `python -m pytest tests/test_rental.py` (or `python -m unittest discover -s tests -p test_rental.py`).
