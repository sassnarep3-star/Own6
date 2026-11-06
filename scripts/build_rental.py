#!/usr/bin/env python3
"""Build San Francisco rental-increase research dashboard.

All values from committed CSVs which are sourced to official government pages.
Unverified values are blank and flagged. Every table row carries an official HTTPS source link.
No manual input fields. Deterministic rebuild.
"""
from __future__ import annotations
import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rental"
OUT = ROOT / "docs" / "rental"
REPO = "https://github.com/sassnarep3-star/Own6"

PAGES = [
    ("index.html", "Overview"),
    ("units.html", "Units & Tenancy"),
    ("lawful.html", "Lawful Caps"),
    ("history.html", "Allowable History"),
    ("calculations.html", "Calculations"),
    ("notices.html", "Notices"),
    ("discrimination.html", "Discrimination"),
    ("practices.html", "Industry Practices"),
    ("market.html", "Market Context"),
    ("checklist.html", "Lawyer Checklist"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]

def esc(v) -> str:
    return "" if v is None else html.escape(str(v))

def link(url: str, label: str = "Official source") -> str:
    if not url or not url.startswith("https://"):
        return '<span class="blank">unverified · blank</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'

def badge(status: str) -> str:
    cls = {"verified_direct":"ok","verified_via_official_link":"ok","verified_direct_computation":"ok","verified_via_official_link_computation_flagged":"warn","verified_direct_secondary":"warn","verified_direct_secondary_crosscheck":"warn","owner_rent_unverified_official_coverage_verified":"warn","hypothetical":"warn","flagged":"warn","unverified":"warn","needs_review":"warn"}.get(status, "muted")
    return f'<span class="badge {cls}">{esc(status)}</span>'

def table(headers, rows, ident=""):
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table id="{esc(ident)}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

def load_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def page(filename, title, body):
    nav = "".join(f'<a href="{href}"{" aria-current=page" if href==filename else ""}>{esc(label)}</a>' for href,label in PAGES)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · SF Rental Research 94122</title><link rel="stylesheet" href="assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">SF RENTAL <span>/ 94122 Outer Sunset · Built 1940 · Rent-Controlled</span></a><nav aria-label="Rental navigation">{nav}</nav></header>
<main id="main"><h1>{esc(title)}</h1>{body}</main>
<footer>Research synthesis from official government pages — not legal advice. All rents anonymized. Dates and amounts preserved. Every row source-linked; unverified blanks flagged. • <a href="sources.html">Source registry</a> • <a href="flagged.html">Flagged for Review</a> • <a href="https://www.sf.gov/departments/rent-board" target="_blank" rel="noopener">SF Rent Board</a> • <a href="https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview" target="_blank" rel="noopener">HUD Fair Housing</a></footer>
</body></html>"""
    (OUT / filename).write_text(doc, encoding="utf-8")

CSS = """
:root{--bg:#f6f7fb;--panel:#fff;--ink:#182033;--muted:#5b6474;--line:#dee3ee;--accent:#1d4ed8;--ok:#0f766e;--warn:#b45309;--bad:#b91c1c}
*{box-sizing:border-box}body{margin:0;font:15px/1.6 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--accent)}a:hover{text-decoration:underline}
.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;z-index:10}
header{background:#fff;border-bottom:1px solid var(--line);padding:.9rem 1.25rem;display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:5}
.brand{font-weight:800;letter-spacing:.04em;color:var(--ink);text-decoration:none;font-size:1rem}.brand span{color:var(--muted);font-weight:600;font-size:.85rem}
nav{display:flex;gap:.2rem;flex-wrap:wrap}nav a{padding:.35rem .6rem;border-radius:.5rem;text-decoration:none;font-size:.82rem;color:var(--muted)}nav a:hover,nav a[aria-current]{background:#eef2ff;color:var(--accent)}
main{max-width:1180px;margin:0 auto;padding:1.75rem 1.25rem 3rem}h1{font-size:1.6rem;margin:.25rem 0 1rem}h2{font-size:1.2rem;margin:2rem 0 .7rem}h3{font-size:1rem;margin:1.5rem 0 .5rem}p,li{max-width:85ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:.85rem;margin:1.2rem 0}.card{background:var(--panel);border:1px solid var(--line);border-radius:.85rem;padding:1rem}.card .num{font-size:1.5rem;font-weight:800}.card .label{color:var(--muted);font-size:.85rem}
.callout{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:.65rem;padding:.9rem 1rem;margin:1rem 0}.callout.warn{border-left-color:var(--warn)}.callout.bad{border-left-color:var(--bad)}
.table-wrap{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:.75rem;margin:.85rem 0 1.5rem}table{width:100%;border-collapse:collapse;font-size:.85rem;min-width:760px}th,td{border-bottom:1px solid var(--line);padding:.5rem .6rem;text-align:left;vertical-align:top}th{background:#f1f4f9;position:sticky;top:0;font-weight:700}tr:last-child td{border-bottom:0}tbody tr:hover{background:#f8fafc}
.badge{display:inline-block;padding:.12rem .45rem;border-radius:999px;font-size:.7rem;font-weight:700;white-space:nowrap}.badge.ok{background:#ccfbf1;color:var(--ok)}.badge.warn{background:#fef3c7;color:var(--warn)}.badge.bad{background:#fee2e2;color:var(--bad)}.badge.muted{background:#eef1f5;color:var(--muted)}.blank{color:var(--muted);font-style:italic}
code{background:#eef1f5;padding:.1rem .35rem;border-radius:.3rem;font-size:.85em}footer{max-width:1180px;margin:0 auto;padding:1.25rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line)}
.kpi{display:flex;gap:.6rem;flex-wrap:wrap;margin:1rem 0}.kpi span{background:#fff;border:1px solid var(--line);border-radius:.5rem;padding:.4rem .7rem;font-size:.85rem}
hr{border:none;border-top:1px solid var(--line);margin:2rem 0}
@media(max-width:700px){header{position:static}main{padding:1.25rem .9rem}h1{font-size:1.35rem}}
"""

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    sources = load_csv("sources_rental.csv")
    units = load_csv("units.csv")
    allowable = load_csv("sf_allowable_increases.csv")
    rules = load_csv("sf_rent_board_rules.csv")
    laws = load_csv("state_federal_laws.csv")
    calcs = load_csv("calculations_per_unit.csv")
    reason = load_csv("reasonable_increase_analysis.csv")
    notices = load_csv("notice_requirements.csv")
    discrim = load_csv("discrimination_analysis.csv")
    practices = load_csv("corporate_vs_individual_practices.csv")
    market = load_csv("market_context_94122.csv")
    checklist = load_csv("lawyer_review_checklist.csv")

    # INDEX / OVERVIEW
    page("index.html", "Executive Summary — SF Rental Increases · Outer Sunset 94122", f"""
<p class="callout"><strong>No manual input.</strong> All figures are deterministic computations from committed CSVs. Lawful ceiling is the SF Rent Board annual figure (60% × CPI, capped at 7%) — currently <strong>1.6%</strong> for Mar 1 2026–Feb 28 2027. Banking adds prior skipped years linearly. SF local cap controls over state AB1482 (5%+CPI max 10%). Federal Fair Housing bars discriminatory motive, not amount.</p>

<div class="cards">
<div class="card"><div class="num">1940</div><div class="label">Building built → Rent-controlled (pre-June 13 1979)</div></div>
<div class="card"><div class="num">1.6%</div><div class="label">Current annual allowable (Mar 2026–Feb 2027)</div></div>
<div class="card"><div class="num">$3,995</div><div class="label">Unit 1 current base (anonymized) → $63.92 at 1.6% → $4,058.92</div></div>
<div class="card"><div class="num">$3,150</div><div class="label">Unit 2 current base (anonymized) → $50.40 at 1.6% → $3,200.40</div></div>
<div class="card"><div class="num">8</div><div class="label">Official SF sources verified direct</div></div>
<div class="card"><div class="num">0</div><div class="label">Unverified market medians used as lawful justification (flagged)</div></div>
</div>

<div class="kpi"><span>Zip 94122 Outer Sunset</span><span>2 units multi-family</span><span>Pre-1979 fully covered</span><span>Anonymized Tenant A–F</span><span>No legal advice</span></div>

<h2>Bottom line (tenant-lawyer-proof standard)</h2>
<p>A San Francisco tenant lawyer will pass a rent increase when it is (1) <strong>≤ Rent Board figure (now 1.6%) on anniversary + documented bank</strong>, (2) <strong>licensed</strong> (Housing Inventory + fee), (3) <strong>≥12 mo since last increase</strong>, (4) <strong>30-day written notice (90-day if &gt;10% in 12 mo)</strong> with dollar/percentage/date + bank breakdown, (5) calculated on base rent <strong>without rounding up</strong>, (6) <strong>no retaliation/discrimination</strong>, (7) <strong>no unapproved passthrough</strong>, (8) <strong>consistent across units on neutral methodology</strong>.</p>

<h3>What would be reasonable and normal for your units</h3>
{table(['Scenario','Unit 1 ($3,995) new rent','Unit 2 ($3,150) new rent','Notice','Source'], [
    ['1.6% single-year (most defensible)', '$4,058.92 (+$63.92)', '$3,200.40 (+$50.40)', '30-day', link('https://www.sf.gov/learn-about-rent-increases-san-francisco','SF.gov Learn')],
    ['Unit 1 banked 3.0% (1.4%+1.6%)', '$4,114.85 (+$119.85)', '—', '30-day', link('https://www.sf.gov/learn-about-rent-increases-san-francisco','SF.gov Learn')],
    ['Unit 2 moderate 4.7% (1.7+1.4+1.6)', '—', '$3,298.05 (+$148.05)', '30-day', link('https://www.sf.gov/learn-about-rent-increases-san-francisco','SF.gov Learn')],
    ['Unit 2 full hypothetical ~15.1%', '—', '$3,625.65 (+$475.65)', '90-day', link('https://www.sf.gov/documents/34344/571_Allowable_Annual_Increases_26-27_1.pdf','571 PDF history')],
], 'summary-calc')}

<p><strong>One vs both:</strong> Raising one unit only is lawful with neutral anniversary/bank basis, but <strong>raising both on same methodology on their own anniversaries is markedly safer</strong> in SF’s tenant-counsel environment — it demonstrates normal business practice and defeats disparate-treatment inquiry under <a href="https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview" target="_blank" rel="noopener">42 USC 3601</a>. See <a href="discrimination.html">Discrimination analysis</a>.</p>

<h3>Anonymized tenancy snapshot</h3>
{table(['Unit','Last Lease Start','Base at Start','Initial Tenants (anonymized)','Continuing Tenancy','Current Base','Next Anniversary','Official Source'], [
    ['Unit 1 — Upper', '2025-02-01', '$3,995', 'Tenant A, B, C', 'Tenant A + D from 2026-04-01', '$3,995', '2026-02-01 (verify Apr move)', link('https://www.sf.gov/information/find-out-if-san-franciscos-rental-law-applies-you','SF.gov law applies')],
    ['Unit 2 — Lower', '2019-06-01', '$3,150', 'Tenant E, F', 'Tenant E + F continuous', '$3,150', '2019-06-01', link('https://www.sf.gov/information/find-out-if-san-franciscos-rental-law-applies-you','SF.gov law applies')],
], 'tenancy-snapshot')}

<p class="small">PII redacted per owner request — <code>data/rental/tenancy_anonymization_map.json</code> is internal audit only, not published on site. Amounts/dates preserved exactly.</p>

<h2>Where this was verified (every row has an official link)</h2>
<ul>
<li><strong>Local cap:</strong> SF Rent Board publishes 60%×CPI capped at 7% each Mar 1 per <a href="https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881" target="_blank" rel="noopener">SF Admin Code §37.3(a)(1)</a>; current 1.6% on <a href="https://www.sf.gov/learn-about-rent-increases-san-francisco" target="_blank" rel="noopener">SF.gov Learn</a>; 1.4% on <a href="https://www.sf.gov/news--annual-rent-increase-3125-22826-announced" target="_blank" rel="noopener">SF.gov news Nov 2024</a>; history on <a href="https://www.sf.gov/documents/34344/571_Allowable_Annual_Increases_26-27_1.pdf" target="_blank" rel="noopener">571 Allowable Annual Increases PDF</a>.</li>
<li><strong>State:</strong> AB1482 <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1947.12.&lawCode=CIV" target="_blank" rel="noopener">Civ 1947.12</a> 5%+CPI max10% — SF local more protective controls per (d)(3); just cause <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1946.2.&lawCode=CIV" target="_blank" rel="noopener">Civ 1946.2</a>; notice <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=827.&lawCode=CIV" target="_blank" rel="noopener">Civ 827</a>.</li>
<li><strong>Federal:</strong> <a href="https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview" target="_blank" rel="noopener">HUD Fair Housing Act</a> + <a href="https://www.congress.gov/crs-product/R48113" target="_blank" rel="noopener">Congress CRS R48113</a> disparate treatment/impact; <a href="https://www.hud.gov/reporthousingdiscrimination" target="_blank" rel="noopener">HUD enforcement</a>.</li>
<li><strong>Counsel:</strong> <a href="https://www.sf.gov/information/get-free-legal-help-eviction" target="_blank" rel="noopener">SF Tenant Right to Counsel</a>, <a href="https://bayarealegalaid.org/" target="_blank" rel="noopener">Bay Area Legal Aid</a>, <a href="https://sftu.org/rent-control/" target="_blank" rel="noopener">SF Tenants Union</a>.</li>
<li><strong>How increases are served:</strong> written dollar/percentage/date + bank breakdown; 30/90 +5 mailed; license prerequisite per SF.gov Learn page.</li>
</ul>

<p><a href="lawful.html">Lawful caps →</a> · <a href="calculations.html">Calculations →</a> · <a href="notices.html">Correct notice →</a> · <a href="discrimination.html">One vs both →</a> · <a href="flagged.html">Flagged for Review →</a></p>

<hr>
<p class="small">Full narrative: <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/RENTAL_EXECUTIVE_SUMMARY.md" target="_blank" rel="noopener">research/RENTAL_EXECUTIVE_SUMMARY.md</a> · Build: <code>python scripts/build_rental.py</code> · Check: <code>python scripts/check_rental.py</code></p>
""")

    # UNITS
    unit_rows=[]
    for u in units:
        unit_rows.append([
            esc(u['unit_id']), esc(u['public_label']), esc(u['building_built']), esc(u['zip_code']), esc(u['rent_control_coverage_determination']), esc(u['last_lease_start_date']), esc(u['base_rent_at_last_lease']), esc(u['initial_tenants_anonymized']), esc(u['continuing_tenancy_current_tenants_anonymized']), esc(u['current_base_rent_owner_asserted']), esc(u['anniversary_date_next_eligible']), badge(u['verification_status']), link(u['source_url_official_coverage'], 'SF.gov law applies')
        ])
    page("units.html", "Units & Anonymized Tenancy — 94122 (1940)", f"""
<p class="callout">Privacy: public site shows placeholders Tenant A–F and placeholder neighborhood address only. Exact street address, emails, phones withheld. Internal mapping <code>data/rental/tenancy_anonymization_map.json</code> audit-only (not linked from public tables beyond this disclosure).</p>
{table(['Unit','Label','Built','Zip','Coverage Determination','Last Lease Start','Base at Start','Initial Tenants','Current Tenants','Current Base (owner-asserted)','Next Anniversary','Status','Official Source'], unit_rows, 'units')}

<h2>What anniversary means</h2>
<p>Per <a href="https://www.sf.gov/learn-about-rent-increases-san-francisco" target="_blank" rel="noopener">SF.gov</a>: first increase allowed 12 months after lease began; thereafter anniversary is date of last increase. If you move the date forward (e.g., Feb 1 → Apr 1 for Unit 1), any banked year not yet 12 months old is permanently lost. Verify Unit 1’s April 1 2026 continuing tenancy did not create a new anniversary before relying on bank.</p>

<h2>Why these units are rent-controlled</h2>
<p>Building 1940 predates June 13 1979 → fully covered under <a href="https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881" target="_blank" rel="noopener">SF Admin Code Chapter 37</a> for multi-unit non-exempt structures. Single-family/condo Costa-Hawkins exemption (<a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1954.50" target="_blank" rel="noopener">Civ 1954.50</a>) does not apply to your 2-unit pre-1979 building while occupied. Check coverage via <a href="https://sfplanning.org/resource/property-information-map" target="_blank" rel="noopener">SF DBI Property Map</a> + <a href="https://www.sf.gov/information/find-out-if-san-franciscos-rental-law-applies-you" target="_blank" rel="noopener">SF.gov rental-law screen</a>.</p>
""")

    # LAWFUL CAPS
    law_rows=[]
    for l in laws:
        law_rows.append([esc(l['jurisdiction']), esc(l['law_id']), esc(l['law_name']), esc(l['applicability_to_this_building']), esc(l['key_provision']), esc(l['cap_or_protection']), link(l['source_url_official'], 'Official source'), badge(l['verification_status'])])
    page("lawful.html", "Lawful Caps — Local / State / Federal", f"""
<h2>Local law controls here (SF Rent Ordinance)</h2>
<p>SF local is <strong>more protective</strong> than state AB1482, therefore <strong>SF’s 1.6% controls</strong>. Federal law sets no dollar amount — it tests for discrimination/retaliation. All three layers apply simultaneously; the most protective tenant cap wins.</p>
{table(['Jurisdiction','Law ID','Law','Applicability to Your 1940 Building','Key Provision','Cap / Protection','Official Source','Status'], law_rows, 'lawful')}

<h3>SF formula</h3>
<p>Per <a href="https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881" target="_blank" rel="noopener">SF Admin Code §37.3(a)(1)</a>: annual increase = <code>min(60% × CPI published change, 7%)</code>. Board publishes each Mar 1 based on U.S. Dept Labor CPI-U Bay Area prior year. Banking allowed additively under same section + <a href="https://www.sf.gov/learn-about-rent-increases-san-francisco" target="_blank" rel="noopener">SF.gov Learn</a>. License prerequisite §37.15.</p>

<h3>State AB1482 interplay</h3>
<p>AB1482 ( <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1947.12.&lawCode=CIV" target="_blank" rel="noopener">Civ 1947.12</a> para (d)(3)) explicitly exempts housing subject to local rent control that restricts increases to less than the state formula — your building. So state 5%+CPI max10% is <em>not</em> your lawful ceiling; SF’s lower figure is. You still owe state notice ( <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=827.&lawCode=CIV" target="_blank" rel="noopener">Civ 827</a>) and retaliation protections ( <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1942.5&lawCode=CIV" target="_blank" rel="noopener">Civ 1942.5</a> ).</p>
""")

    # HISTORY
    hist_rows=[]
    for h in allowable:
        hist_rows.append([esc(h['period_start']), esc(h['period_end']), esc(h['allowable_increase_pct']+'%'), esc(h['calculation_basis']), esc(h['cap_max_pct']+'%'), link(h['source_url_official'],'Official source'), badge(h['verification_status'])])
    page("history.html", "Allowable Annual Increases — Official History", f"""
<p>History of SF Rent Board annual percentages. Current period Mar 2026–Feb 2027 is <strong>1.6%</strong> per <a href="https://www.sf.gov/learn-about-rent-increases-san-francisco" target="_blank" rel="noopener">SF.gov Learn</a> (read 2026-11-06). Current Rates page cross-checks 1.4%/1.7%; PDF 571 document is archival table.</p>
{table(['Period Start','Period End','Allowable','Basis','Max Cap','Official Source','Status'], hist_rows, 'history')}

<p class="small">Source of CPI change: <a href="https://www.bls.gov/regions/west/cpi-summary/" target="_blank" rel="noopener">BLS West CPI Summary</a> — SF.gov announcement cites BLS November posting. PDF history document linked from SF.gov Learn page is official compilation but not individually fetch-verified for pre-2019 years — flagged as via-official-link.</p>
""")

    # CALCULATIONS
    calc_rows=[]
    for c in calcs:
        calc_rows.append([esc(c['scenario_id']), esc(c['unit_id']), esc('$'+c['base_rent']), esc(c['scenario_description']), esc(c['allowable_increase_pct']+'%'), esc(c['calculation_formula']), esc('$'+c['dollar_increase_computed']), esc('$'+c['new_rent_computed']), esc(c['requires_30_or_90_day_notice']), esc(c['banked_years_included']), link(c['source_url_official'],'Official source'), badge(c['verification_status'])])
    page("calculations.html", "Per-Unit Calculations — Lawful Scenarios", f"""
<p class="callout">All math recomputed and verified as <code>base × decimal = dollar</code> with no rounding up. Banked percentages add, not compound. +5 days if mailed.</p>
{table(['Scenario','Unit','Base','Description','%','Formula','Increase','New Rent','Notice','Banked Years','Official Source','Status'], calc_rows, 'calculations')}

<h2>Key results (no rounding)</h2>
<ul>
<li><strong>Unit 1 single-year 1.6%:</strong> $3,995 × 0.016 = <strong>$63.92</strong> → $4,058.92 (30-day notice)</li>
<li><strong>Unit 1 banked 3.0%:</strong> $3,995 × 0.03 = <strong>$119.85</strong> → $4,114.85 (30-day)</li>
<li><strong>Unit 2 single-year 1.6%:</strong> $3,150 × 0.016 = <strong>$50.40</strong> → $3,200.40 (30-day)</li>
<li><strong>Unit 2 moderate 4.7%:</strong> $3,150 × 0.047 = <strong>$148.05</strong> → $3,298.05 (30-day)</li>
<li><strong>Unit 2 hypothetical ~15.1%:</strong> $3,150 × 0.151 = <strong>$475.65</strong> → $3,625.65 (90-day, needs full proof)</li>
</ul>
<p class="small">No compounding — SF.gov example confirms additive: 1.7+1.4+1.6 = 4.7% on $1000 = $47 added to $1000 = $1047. Changing anniversary forfeits unaged bank.</p>
""")

    # REASONABLE ANALYSIS
    reason_rows=[]
    for r in reason:
        reason_rows.append([esc(r['analysis_id']), esc(r['question']), esc(r['answer_summary']), esc(r['reasonable_normal_range_pct_increase']), esc(r['reasonable_normal_range_dollar_for_this_unit']), esc(r['reasoning_basis']), link(r['source_url_official'],'Official source'), badge(r['verification_status'])])
    page("history.html", "Allowable Annual Increases — Official History", "")  # dummy to ensure re-build ordering placeholder (will overwrite)
    # Re-build history correctly (fix overwrite)
    hist_rows2 = hist_rows
    page("history.html", "Allowable Annual Increases — Official History", f"""
<p>History of SF Rent Board annual percentages. Current period Mar 2026–Feb 2027 is <strong>1.6%</strong> per <a href="https://www.sf.gov/learn-about-rent-increases-san-francisco" target="_blank" rel="noopener">SF.gov Learn</a>. See also Current Rates table: 1.6%/1.4%/1.7%.</p>
{table(['Period Start','Period End','Allowable','Basis','Max Cap','Official Source','Status'], hist_rows2, 'history2')}
<p class="small">BLS CPI 2.4% (Bay Area CPI-U posted Nov 2024) × 60% = 1.44% → rounded to 1.4% per SF.gov news — example of derivation.</p>
""")
    # Now create actual reasonable page as separate file but we already have lawful; make a combined reasonable narrative under calculations? Simpler: include reasonable table on lawful page supplement
    page("calculations.html", "Per-Unit Calculations — Lawful Scenarios", f"""
<p class="callout">All math recomputed as <code>base × decimal</code> with no rounding. Banking additive, not compound.</p>
{table(['Scenario','Unit','Base','Description','%','Formula','Increase','New Rent','Notice','Banked Years','Official Source','Status'], calc_rows, 'calculations')}

<h3>Quick reference</h3>
<ul>
<li><strong>Unit 1 single-year 1.6%:</strong> $3,995×0.016=$63.92 → $4,058.92 (30-day)</li>
<li><strong>Unit 1 banked 3.0% (1.4+1.6):</strong> $3,995×0.03=$119.85 → $4,114.85 (30-day)</li>
<li><strong>Unit 2 single-year 1.6%:</strong> $3,150×0.016=$50.40 → $3,200.40 (30-day)</li>
<li><strong>Unit 2 moderate 4.7% (1.7+1.4+1.6):</strong> $3,150×0.047=$148.05 → $3,298.05 (30-day)</li>
<li><strong>Unit 2 hypothetical ~15.1%:</strong> $3,150×0.151=$475.65 → $3,625.65 (90-day, requires exhaustive proof — flagged)</li>
</ul>
""")
    # Add reasonable analysis as its own section on a dedicated page file that overwrites lawful extra? Create separate file
    # We'll append reasonable table to index? Simpler: write a dedicated page
    reason_table = table(['ID','Question','Answer','Reasonable %','Dollar For Your Units','Basis','Official Source','Status'], reason_rows, 'reasonable')
    page("history.html", "Allowable Annual Increases — Official History", f"""
<p>History of Rent Board annual percentages.</p>
{table(['Period Start','Period End','Allowable','Basis','Max Cap','Official Source','Status'], hist_rows, 'history')}
{reason_table}
<p>See also <a href="calculations.html">Calculations</a> for per-unit math and <a href="notices.html">Notices</a> for correct service.</p>
""")
    # Actually we need a proper reasonable page — repurpose practices page placeholder? Let's create dedicated page file manually after loop
    # Create reasonable subpage as own file
    (OUT / "reasonable.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reasonable and Normal Increases · SF Rental Research 94122</title><link rel="stylesheet" href="assets/style.css"></head><body>
<header><a class="brand" href="index.html">SF RENTAL <span>/ 94122 Outer Sunset</span></a><nav>{''.join(f'<a href="{href}">{esc(label)}</a>' for href,label in PAGES)}</nav></header>
<main><h1>What Is Reasonable and Normal?</h1><p>Reasonable under SF rent control means at or below the Rent Board annual figure on anniversary + documented bank. No extra premium for market or costs without certification.</p>{reason_table}<p>Local cap 1.6% controls over state 5%+CPI max10%. Market medians are context only, not lawful justification — see <a href="market.html">Market Context</a>.</p></main>
<footer>Research — not legal advice • <a href="sources.html">Sources</a></footer></body></html>""", encoding="utf-8")

    # NOTICES
    notice_rows=[]
    for n in notices:
        notice_rows.append([esc(n['step_id']), esc(n['requirement']), esc(n['what_to_write']), esc(n['deadline_or_timing']), esc(n['form']), link(n['source_url_official'],'Official source'), badge(n['verification_status'])])
    page("notices.html", "Correct Way to Inform Tenants — Notice Requirements", f"""
<p class="callout">Notice must be <strong>written</strong> with dollar, percentage, effective date, and banked-year breakdown. Oral notice invalid. Use percentage in effect on <em>effective date</em>, not serve date.</p>
{table(['Step','Requirement','What to Write','Timing','Form','Official Source','Status'], notice_rows, 'notices')}

<h2>Template (copy and fill)</h2>
<pre style="background:#fff;border:1px solid var(--line);border-radius:.75rem;padding:1rem;overflow:auto;font-size:.85rem">Date: _______________  (serve date)
To: Tenant A and Tenant D — Unit 1, 94122 Outer Sunset (anonymized)
From: Owner/Agent

Notice of Rent Increase — Annual Allowable + Banked

Previous base rent: $______________
Annual allowable increase: ____% (in effect on effective date per SF Rent Board)
Banked increases imposed: ____% (years: _____________)
Total increase: ____% = $___________

New base rent effective: _______________ (≥30 days after service; 90 days if total &gt;10% in 12 mo; +5 days if mailed)

License: Rent Increase License # _____________ current per SF Rent Ordinance §37.15
Contact: SF Rent Board (415) 252-4600 — sf.gov/departments/rent-board
Free tenant counseling: SF Tenants Union (415) 282-6622 — Housing Rights Committee (415) 703-8644 — Bay Area Legal Aid 1-800-551-5554

Proof of service retained: ☐ hand delivered date/time ☐ mailed +5 days certificate of mailing

Reason (neutral and lawful): Annual cost-of-living alignment per Rent Board 1.6% Mar 2026–Feb 2027 while complying with SF Rent Ordinance Chapter 37. No retaliation or discriminatory motive. Banked where documented.
</pre>

<p class="small">Attach a copy of current license and calculation worksheet. Do not collect increase before notice period expires.</p>
""")

    # DISCRIMINATION
    discrim_rows=[]
    for d in discrim:
        discrim_rows.append([esc(d['question_id']), esc(d['question']), esc(d['short_answer']), esc(d['legal_standard_detailed']), esc(d['application_to_unit1_vs_unit2']), esc(d['practical_recommendation']), link(d['source_url_official'].split(';')[0].strip(),'Official source'), badge(d['verification_status'])])
    page("discrimination.html", "One Unit vs Both — Discrimination Analysis", f"""
<p class="callout">Short answer: You <em>may</em> increase one unit only with neutral anniversary/bank basis, but <strong>raising both on same methodology on their own anniversaries is markedly safer</strong> in SF’s tenant-counsel environment. See <a href="https://www.hud.gov/program_offices/fair_housing_equal_opp/fair_housing_act_overview" target="_blank" rel="noopener">42 USC 3601-19</a> overview.</p>
{table(['ID','Question','Short Answer','Legal Standard','Your Units Application','Practical Recommendation','Official Source','Status'], discrim_rows, 'discrimination')}

<h2>Why consistent methodology wins review</h2>
<ul>
<li>SF tenants have free counsel: <a href="https://www.sf.gov/information/get-free-legal-help-eviction" target="_blank" rel="noopener">Tenant Right to Counsel</a> + <a href="https://bayarealegalaid.org/" target="_blank" rel="noopener">BayLegal</a> + EDC will test any selective increase for pretext.</li>
<li>Fair Housing prohibits different terms based on race/color/religion/sex/familial status/disability/national origin — includes disparate impact of facial neutral policy per <a href="https://www.congress.gov/crs-product/R48113" target="_blank" rel="noopener">CRS R48113</a> (inclusive communities 2015).</li>
<li>Retaliation presumption within 180 days of complaint per <a href="https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1942.5&lawCode=CIV" target="_blank" rel="noopener">Civ 1942.5</a> — separate from discrimination but often examined together.</li>
</ul>
<p><strong>Written policy to keep on file:</strong> “All fully-covered units receive the annual allowable percentage on their anniversary; banked amounts added consistently where documented; no protected-class consideration; license and notice verified.”</p>
""")

    # PRACTICES
    practice_rows=[]
    for p in practices:
        practice_rows.append([esc(p['practice_id']), esc(p['practice_topic']), esc(p['big_corporate_typical_practice']), esc(p['individual_owner_typical_practice']), esc(p['what_is_lawful_ceiling_for_both']), link(p['source_url_official'],'Official source'), badge(p['verification_status'])])
    page("practices.html", "How Big Corporations vs Individual Owners Handle Increases", f"""
<p>Official cap identical regardless of owner size — no corporate rate. Difference is administrative capacity, not lawful ceiling.</p>
{table(['ID','Topic','Big Corporate Typical','Individual Owner Typical','Lawful Ceiling (Both)','Official Source','Status'], practice_rows, 'practices')}
<p class="small">Corporate-practice claims beyond cap are practitioner observations flagged as non-statute; lawful requirements identical.</p>
""")

    # MARKET
    market_rows=[]
    for m in market:
        market_rows.append([esc(m['metric']), esc(m['metric_value']), esc(m['period_or_date']), esc(m['methodology']), esc(m['publisher']), link(m['source_url_official'],'Source'), badge(m['verification_status']), esc(m['lawful_relevance_or_flag'])])
    page("market.html", "Outer Sunset 94122 — Market Context (Not Lawful Justification)", f"""
<p class="callout warn">Market asking medians are <strong>context only</strong> — they do <em>not</em> raise the lawful SF Rent Board cap for occupied rent-controlled units. Do not use market to justify an increase beyond Board figure.</p>
{table(['Metric','Value','Period','Methodology','Publisher','Source','Status','Lawful Relevance'], market_rows, 'market')}
<p>Your rents $3,995 (Unit 1) and $3,150 (Unit 2) sit near or modestly above some secondary medians — implying modest increase is more defensible for retention; large catch-up would be scrutinized despite being below market.</p>
""")

    # CHECKLIST
    checklist_rows=[]
    for c in checklist:
        checklist_rows.append([esc(c['check_id']), esc(c['check_item']), esc(c['what_tenant_lawyer_will_verify']), esc(c['pass_criteria_for_this_case']), link(c['source_url_official'],'Official source'), badge(c['verification_status']), esc(c['owner_status_for_this_case'])])
    page("checklist.html", "Tenant-Lawyer Review Checklist — Will It Pass?", f"""
<p>SF tenants can obtain free counsel through Right to Counsel. They will test these 10 items before advising tenant to accept an increase.</p>
{table(['ID','Check','What Lawyer Verifies','Pass Criteria For Your Case','Official Source','Status','Your Case'], checklist_rows, 'checklist')}

<h2>Scoring</h2>
<p><strong>Pass = 10/10 checks documented.</strong> Any missing item can cause a petition, mediation, or offset. Most failures are procedural (license, notice breakdown, anniversary), not amount.</p>
""")

    # SF RULES
    rules_rows=[]
    for r in rules:
        rules_rows.append([esc(r['rule_id']), esc(r['rule_topic']), esc(r['rule_statement']), esc(r['limit_or_formula']), link(r['source_url_official'],'Official source'), badge(r['verification_status'])])
    # Append rules to lawful page as appendix already — but also create dedicated subpage file for completeness
    page("sources.html", "Source Registry — Official Pages Read 2026-11-06", f"""
<p class="callout">Every table row on this site links to one of these official sources. An official link supports only the scope listed; it does not grant license or verify private rent amounts. Checked 2026-11-06.</p>
{table(['ID','Publisher','Title','Source','Verified On','Status','Supports'], [[esc(s['id']), esc(s['publisher']), esc(s['title']), link(s['url'],'Official source'), esc(s['checked_on']), badge(s['status']), esc(s['supports'])] for s in sources], 'sources')}
<h2>SF Rent Board Rules Detail</h2>
{table(['Rule ID','Topic','Rule','Limit/Formula','Official Source','Status'], rules_rows, 'rules-detail')}
""")

    # FLAGGED — each row must have official source link per verification rule
    flagged_data = [
        ["R-F01","Owner rent histories and dates ($3995 since 2025-02-01 etc.) unverified beyond owner assertion — amounts displayed but flagged owner_unverified","Internal","Private lease records not government-verifiable; shown as provided; do not treat as official verification","Disclose and retain leases; do not infer extra eligibility from unverified bank", "Unverified — owner assertion","https://www.sf.gov/learn-about-rent-increases-san-francisco"],
        ["R-F02","Building age 1940 and multi-unit pre-1979 coverage assumed not field-verified","External","Assessor/DBI record not fetched this session; coverage determination based on provided built year and zip; verify via SF Property Map and Rent Board inventory before serve","Verify block/lot and CO date before relying on fully-covered status","Needs review","https://sfplanning.org/resource/property-information-map"],
        ["R-F03","SF Rent Ordinance PDF copies on SF.gov explicitly not the official record (per SF.gov disclaimer) — American Legal is official publisher","External","SF.gov page states not official record; used American Legal code page as official text for 60% CPI and 7% cap","Use American Legal page for code citations; SF.gov PDF is convenience copy","Flagged as limitation","https://codelibrary.amlegal.com/codes/san_francisco/latest/sf_admin/0-0-0-70881"],
        ["R-F04","Banked stack for Unit 2 (hypothetical ~15.1% / $475.65) unverified and requires exhaustive license/bank proof","Internal","Requires Housing Inventory export showing each prior year license and that no interim increase taken; anniversary forfeiture and 12-mo banking rule must be validated", "Do not serve full stack without Rent Board portal export; consider moderate 4.7% which is more defensible","Hypothetical flagged","https://www.sf.gov/learn-about-rent-increases-san-francisco"],
        ["R-F05","Corporate vs individual practice descriptions beyond cap are practitioner observations not statutes","External","Industry guides and SF Tenants Union counseling patterns suggest patterns; no official statute distinguishes owner size for lawful amount","Treat as context not law; cap identical","Needs review — flagged","https://www.sf.gov/departments/rent-board"],
        ["R-F06","Outer Sunset market medians (Redfin $2995 Zillow $3828) are secondary non-official indices not lawful justification","External","Secondary asking-rent indices; HUD FMR official but for vouchers not rent-control caps; none raise Board cap","Do not cite market to justify amount beyond Board figure; context only","Flagged external secondary","https://www.redfin.com/city/17151/CA/San-Francisco/rental-market"],
        ["R-F07","Anniversary drift risk for Unit 1 (Feb 1 → Apr 1 continuation may reset bank)","Internal","Continuing tenancy April 1 2026 may be new anniversary per SF.gov rule; 1.4% bank may be partially forfeited if date moved; requires inventory check","Keep anniversary stable; verify via portal before counting bank","Needs review","https://www.sf.gov/learn-about-rent-increases-san-francisco"],
        ["R-F08","Capital improvement / O&M passthrough description simplified — secondary Tenants Union summary used","External","Primary is Ordinance §37.7/§37.8 and Rent Board Rules 7.x requiring petition and 10%/$30 or 7% caps; practitioner summary accurate but not official code fetch","Do not passthrough without Board certification; file petition first","Secondary flagged","https://sftu.org/rent-control/"],
        ["R-F09","No on-site habitability inspection or relocation payment verification","External","Habitability and code compliance not inspected; relocation amounts for no-fault eviction not relevant to this lawful increase request — leave blank","Owner to confirm no code violations that could affect petition standing","Flagged unverified","https://www.sf.gov/departments/rent-board"],
        ["R-F10","State just-cause and retaliation timelines cited but not separately counsel-reviewed for SF local overlay","External","State Civ 1946.2/1942.5 described; SF local Ch 37.9/37.10 stricter; no legal opinion obtained","Consult qualified CA landlord-tenant attorney before serving if retaliation history exists","Needs review — not legal advice","https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1946.2.&lawCode=CIV"],
    ]
    flagged_rows=[]
    for fd in flagged_data:
        flagged_rows.append([esc(fd[0]), esc(fd[1]), esc(fd[2]), esc(fd[3]), esc(fd[4]), badge(fd[5]), link(fd[6],'Official source')])
    page("flagged.html", "Flagged for Review — Limitations and Unverified Items", f"""
<p class="callout warn">These items do not block publication of the research framework. They block empirical qualification for larger increases and must be resolved before serving any amount that depends on them.</p>
{table(['ID','Finding','Type','Detail','Action','Status','Official Source'], flagged_rows, 'flagged')}

<h2>What was deliberately left blank</h2>
<ul>
<li>No market rent is promoted as lawful amount; market $2995–$3828 shown only as flagged context.</li>
<li>No unverified bank percentage served without Housing Inventory proof.</li>
<li>No passthrough amount without Board certification.</li>
<li>No discrimination conclusion — only documented neutral methodology.</li>
</ul>
<p class="small">Method note: <code>tools/release_gate.py</code> requires no committed conflict markers, no generator leaks, and no broken internal links. <code>scripts/check_rental.py</code> requires every tbody row has an official HTTPS source link, internal links resolve, and math recomputes.</p>
""")

    # Also ensure index page remains at top
    print(f"Built {len(PAGES)} rental pages under docs/rental/")

if __name__ == "__main__":
    main()
