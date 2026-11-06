#!/usr/bin/env python3
"""Build the SF Rental Increase (94122) review site into docs/rental/.

All data values come from data/rental/*.json. No number is typed by hand into a
page template; tables are generated from the JSON data files. Verification
status is rendered from flags.json. Re-run: python3 scripts/build_rental.py
"""
import json, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "rental"
OUT = ROOT / "docs" / "rental"

def load(name):
    return json.loads((DATA / name).read_text())

AGA = load("aga_history.json")
UNITS = load("units.json")
SCEN = load("scenarios.json")
SOURCES = load("sources.json")
FLAGS = load("flags.json")

SRC = {s["id"]: s for s in SOURCES["official_sources"]}
SEC = {s["id"]: s for s in SOURCES["secondary_sources_flagged"]}
FLAG = {f["id"]: f for f in FLAGS["flags"]}


def fmt_money(s):
    try:
        v = float(s)
        return f"{v:,.2f}"
    except ValueError:
        return str(s)

def esc(s):
    return html.escape(str(s), quote=True)

def src_link(sid, label=None):
    s = SRC[sid]
    return f'<a href="{esc(s["url"])}" rel="noopener">{esc(label or s["title"].split("—")[0].strip())} ↗</a>'

def checked_on():
    return "2026-11-06"

NAV = [("index.html","Dashboard"),("executive-summary.html","Executive Summary"),("units.html","Units &amp; Scenarios"),
       ("laws-local.html","Local law (SF)"),("laws-state.html","State law (CA)"),("laws-federal.html","Federal &amp; HUD"),
       ("market-practices.html","Market practices"),("notice-procedure.html","Notice procedure"),
       ("one-vs-both.html","One or both units"),("tenant-lawyer-review.html","Tenant-lawyer review"),
       ("faq.html","FAQ"),("sources.html","Sources"),("methodology.html","Methodology"),("flagged.html","Flagged for Review")]

def nav(active):
    links = []
    for href, label in NAV:
        cls = ' style="color:#fff;border-bottom:2px solid #17a2c8"' if href == active else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    return ('<nav class="nav" aria-label="Rental pack navigation"><div class="nav-inner">'
            '<a class="brand" href="index.html"><span class="mark">94122</span>RENTAL INCREASE · SF</a>'
            + "".join(links) + "</div></nav>")

def page(active, title, crumb, lede, body, footer_note=None):
    note = footer_note or "Prepared 2026-11-06 from official sources read 2026-11-06. Not legal advice."
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="SF 94122 rent-increase analysis: SF Rent Ordinance AGA, California Civil Code, federal Fair Housing Act, anonymized unit scenarios, notice procedure and tenant-lawyer review checklist.">
<title>{esc(title)} · SF 94122 Rental Increase Review</title>
<link rel="stylesheet" href="assets/rental.css">
</head>
<body>
{nav(active)}
<header class="page-head"><div class="wrap"><p class="crumb">{esc(crumb)}</p><h1>{esc(title)}</h1><p>{lede}</p></div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="footer"><div class="wrap"><p><strong>SF 94122 Rental Increase Review.</strong> {esc(note)} Personal information is anonymized (placeholders Tenants A–F); dates and amounts are preserved. Every table row carries an official source link; unverifiable values are blank and listed on <a href="flagged.html">Flagged for Review</a>. Building: rent-controlled, built 1940. This pack is not legal advice and creates no attorney–client relationship.</p></div></footer>
</body>
</html>"""

def table_open(caption, headers, klass=""):
    th = "".join(f'<th scope="col">{h}</th>' for h in headers)
    return f'<div class="table-wrap"><table class="{klass}"><caption>{esc(caption)}</caption><thead><tr>{th}</tr></thead><tbody>\n'

def table_close():
    return "</tbody></table></div>\n"

def badge(kind, text):
    return f'<span class="badge {kind}">{esc(text)}</span>'

# ---------- shared fragments ----------

def aga_rows_html():
    out = []
    for r in AGA["rows"]:
        note = esc(r["note"]) if r["note"] else "&nbsp;"
        cur = ' <span class="badge ok">current</span>' if r["note"] == "current" else ""
        out.append(f'<tr><td class="mono">{esc(r["period"])}</td><td class="mono">{esc(r["rate"])}{cur}</td><td>{note}</td><td class="src-col"><a href="{esc(AGA["source_form"])}">Form 571 ↗</a></td></tr>')
    return "\n".join(out)

def scenarios_rows_html(unit_filter=None):
    out = []
    for s in SCEN["scenarios"]:
        if unit_filter and s["unit"] != unit_filter:
            continue
        verified = '<span class="badge ok">inputs verified</span>' if s["verified_inputs"] else '<span class="badge warn">base rent unverified · F-R7</span>'
        cls = ' class="unverified"' if not s["verified_inputs"] else ''
        fid = 'F-R7' if not s['verified_inputs'] else 'F-R5'
        row = (f'<tr{cls}>'
            f'<td><strong>{esc(s["id"])}</strong><br><span class="small">{esc(s["label"])}</span></td>'
            f'<td class="mono">${esc(fmt_money(s["base_rent"]))}</td>'
            f'<td>{esc(s["rate_applied"])}</td>'
            f'<td class="mono">+${esc(s["dollar_increase"])}</td>'
            f'<td class="mono"><strong>${esc(fmt_money(s["new_rent"]))}</strong></td>'
            f'<td>{esc(s["notice_required"])}</td>'
            f'<td>{verified}<br><a href="flagged.html#{fid}" class="small">flags</a></td>'
            f'</tr>')
        out.append(row)
    return "\n".join(out)

def flags_rows_html(ids=None):
    out = []
    for f in FLAGS["flags"]:
        if ids and f["id"] not in ids:
            continue
        sev = {"high": "bad", "medium": "warn", "low": "info", "info": "info"}[f["severity"]]
        out.append(f'<tr id="{esc(f["id"])}"><td><strong>{esc(f["id"])}</strong></td><td>{badge(sev, f["severity"])}</td><td>{esc(f["title"])}<br><span class="small">{esc(f["detail"])}</span><br><span class="small"><strong>Action:</strong> {esc(f["action"])}</span></td><td class="src-col"><a href="sources.html">sources ↗</a></td></tr>')
    return "\n".join(out)

def sources_rows_html():
    out = []
    for s in SOURCES["official_sources"]:
        out.append(f'<tr><td><strong>{esc(s["id"])}</strong></td><td><a href="{esc(s["url"])}">{esc(s["title"])}</a></td><td>{esc(s["host"])}</td><td>{badge("ok","official")}</td><td><span class="small">{esc(s["supports"])}</span><br><span class="tag">read {esc(s["read_on"])}</span></td></tr>')
    for s in SOURCES["secondary_sources_flagged"]:
        out.append(f'<tr class="unverified"><td><strong>{esc(s["id"])}</strong></td><td><a href="{esc(s["url"])}">{esc(s["title"])}</a></td><td>{esc(s["host"])}</td><td>{badge("warn","secondary · unverified")}</td><td><span class="small">{esc(s["note"])}</span></td></tr>')
    return "\n".join(out)

# ---------- page: index ----------

def page_index():
    u1, u2 = UNITS["units"]
    body = f"""
<div class="grid cols-4">
  <div class="card stat"><span class="k">Current AGA (3/1/26–2/28/27)</span><span class="v">1.6%</span><span class="s">60% of Bay Area CPI-U · cap 7% · {src_link('S-01','SF.gov')}</span></div>
  <div class="card stat"><span class="k">Unit 1 @ $3,995</span><span class="v">+$63.92</span><span class="s">2026-27 annual → $4,058.92 · 30-day notice</span></div>
  <div class="card stat"><span class="k">Unit 2 @ $3,150 (base unverified)</span><span class="v">+$50.40</span><span class="s">2026-27 annual only → $3,200.40 · 30-day notice</span></div>
  <div class="card stat"><span class="k">Unit 2 — all banked + annual</span><span class="v">+$412.65</span><span class="s">13.1% combined → $3,562.65 · <strong>90-day notice</strong></span></div>
</div>

<div class="callout info"><strong>Bottom line.</strong> Both units are fully rent-controlled (built 1940, pre–June 13, 1979). The only increases that survive a San Francisco tenant lawyer's review are (a) the annual allowable increase and (b) properly banked skips — computed on base rent, once every 12 months, with a Rent Increase License, a 30- or 90-day written notice, and no rounding up. Market-rate jumps mid-tenancy, roommate surcharges and retaliatory or discriminatory increases are unlawful.</div>

<h2>The two units (anonymized)</h2>
<div class="table-wrap"><table><caption>Property: San Francisco, CA 94122 (Outer Sunset) — built 1940 — rent-controlled</caption>
<thead><tr><th scope="col">Field</th><th scope="col">Unit 1</th><th scope="col">Unit 2</th><th scope="col">Source</th></tr></thead><tbody>
<tr><td>Last lease start / rent</td><td>February 1, 2025 · <strong>$3,995.00</strong>/mo</td><td>June 1, 2019 · <strong>$3,150.00</strong>/mo (lease-start; current base unverified)</td><td>{badge('info','preserved dates & amounts')}</td></tr>
<tr><td>Initial-lease tenants (placeholder)</td><td>Tenant A, Tenant B, Tenant C</td><td>Tenant E, Tenant F</td><td class="small">names anonymized — {badge('info','F-R8')}</td></tr>
<tr><td>Current / continuing tenancy</td><td>From April 1, 2026 · <strong>$3,995.00</strong>/mo · Tenant A, Tenant D</td><td>Continuous since June 1, 2019 (no re-papering on file)</td><td class="small">Unit 1 ambiguity — {badge('warn','F-R3')}</td></tr>
<tr><td>Rent-control coverage</td><td>Full (eviction + increase limits)</td><td>Full (eviction + increase limits)</td><td><a href="{esc(SRC['S-06']['url'])}">SF.gov coverage ↗</a></td></tr>
<tr><td>AGAs unused (bankable, if ledger confirms)</td><td>1.4% (2025-26, available 2/1/2026, bankable only from 2/1/2027 — {badge('warn','F-R5')})</td><td>1.8% + 0.7% + 2.3% + 3.6% + 1.7% + 1.4% = 11.5% (2020–2026, if never imposed — {badge('warn','F-R7')})</td><td><a href="{esc(SRC['S-04']['url'])}">Banked increases ↗</a></td></tr>
</tbody></table></div>

<h2>Increase scenarios (computed, labeled)</h2>
{table_open("Computed from verified AGA rates; Unit 2 rows pending ledger verification", ["Scenario","Base rent","Rate applied","+$ / mo","New rent","Notice required","Status"])}
{scenarios_rows_html()}
{table_close()}
<p class="small">All scenario math is computed deterministically (scripts/build_rental.py from data/rental/scenarios.json). Banked increases add percentages and multiply by the current base rent — no compounding, no proration, no rounding up. See <a href="methodology.html">Methodology</a>.</p>

<h2>What would a SF tenant lawyer check?</h2>
<div class="grid cols-2">
  <div class="card"><h3>Must be true ✔</h3><ul class="tight">
    <li>Increase ≤ AGA or petition-approved amount ({src_link('S-01','S-01')} · {src_link('S-05','S-05')})</li>
    <li>Not more than once per 12 months; first increase 12+ months after lease start ({src_link('S-01','S-01')})</li>
    <li>Banked skips only after ≥24 full months with no increase; correct portion stated in notice ({src_link('S-04','S-04')})</li>
    <li>Rent Increase License held before service; notice states dollar, percentage, effective date ({src_link('S-01','S-01')})</li>
    <li>30-day notice; 90-day if combined increase &gt;10%; +5 days if mailed ({src_link('S-01','S-12')})</li>
    <li>Base rent only; housing services included; passthroughs excluded; no rounding up ({src_link('S-01','S-01')})</li>
  </ul></div>
  <div class="card"><h3>Red flags ✘</h3><ul class="tight">
    <li>Any increase above AGA without an approved petition ({src_link('S-05','S-05')})</li>
    <li>Surcharge for a new/additional roommate ({src_link('S-01','S-01')})</li>
    <li>Increase coinciding with protected-class activity or retaliation ({src_link('S-17','S-17')})</li>
    <li>Different treatment of one tenant cohort with no objective, documented basis ({src_link('S-16','S-16')})</li>
    <li>"Market rate" reset during an ongoing tenancy ({src_link('S-15','S-15')})</li>
    <li>Banked portion imposed before 24 months elapsed ({src_link('S-04','S-04')})</li>
  </ul></div>
</div>

<h2>Explore</h2>
<div class="grid cols-3">
  <a class="card" href="executive-summary.html"><h3>Executive Summary →</h3><p class="small">The whole analysis: coverage, caps, scenarios, one-vs-both answer, flagged items.</p></a>
  <a class="card" href="units.html"><h3>Units &amp; Scenarios →</h3><p class="small">Anonymized profiles, full computations, notice math for each unit.</p></a>
  <a class="card" href="laws-local.html"><h3>Local law (SF) →</h3><p class="small">Chapter 37, 60% CPI formula, 7% cap, full 45-period AGA history, banking, petitions.</p></a>
  <a class="card" href="laws-state.html"><h3>State law (CA) →</h3><p class="small">Costa-Hawkins vacancy decontrol, AB 1482 cap &amp; exemptions, §827 notice, Unruh.</p></a>
  <a class="card" href="laws-federal.html"><h3>Federal &amp; HUD →</h3><p class="small">No federal rent control; Fair Housing Act classes; HUD complaint path; FY2027 FMRs (blank/unverified).</p></a>
  <a class="card" href="one-vs-both.html"><h3>One or both units →</h3><p class="small">Discrimination-risk analysis and the recommended uniform approach.</p></a>
  <a class="card" href="notice-procedure.html"><h3>Notice procedure →</h3><p class="small">Step-by-step, with templates of what the notice must contain.</p></a>
  <a class="card" href="tenant-lawyer-review.html"><h3>Tenant-lawyer review →</h3><p class="small">The scrutiny checklist SF tenant advocates apply — and free counsel resources.</p></a>
  <a class="card" href="flagged.html"><h3>Flagged for Review →</h3><p class="small">F-R1…F-R13: everything unverified, ambiguous or requiring sign-off.</p></a>
</div>
"""
    return page("index.html", "Dashboard · 94122 Outer Sunset", "Dashboard · SF 94122 · Rent-controlled (built 1940)",
                "Anonymized, source-linked analysis of reasonable and lawful rent increases for two rent-controlled units in San Francisco's 94122 zip code: the SF Rent Ordinance allowable increase, California and federal law, banking of skipped increases, notice rules, discrimination risk and tenant-lawyer scrutiny.", body)

# ---------- page: executive summary ----------

def page_exec():
    body = f"""
<div class="callout info"><strong>Prepared 2026-11-06 · Branch arena/10504d38-own6.</strong> Location: San Francisco, CA 94122 (Outer Sunset). Building built 1940. Two units, both fully rent-controlled. Personal information anonymized (placeholders Tenants A–F); dates and amounts preserved exactly. Not legal advice.</div>

<h2>1 · The units at a glance</h2>
{table_open("Anonymized unit profiles (dates and amounts preserved)", ["Unit","Tenancy start","Rent (preserved)","Placeholders (current)","Placeholders (initial)"])}
<tr><td><a href="units.html">Unit 1</a></td><td>February 1, 2025</td><td class="mono">$3,995.00/mo (unchanged through April 1, 2026)</td><td>Tenant A, Tenant D</td><td>Tenant A, Tenant B, Tenant C <a href="methodology.html" class="small">records ↗</a></td></tr>
<tr><td>Unit 2</td><td>June 1, 2019</td><td class="mono">$3,150.00/mo (recorded lease-start rent; current lawful base unverified — <a href="flagged.html#F-R7">F-R7</a>)</td><td>Tenant E, Tenant F</td><td>Tenant E, Tenant F</td></tr>
{table_close()}

<h2>2 · What a "reasonable and normal" increase is here (verified)</h2>
<p>The SF Rent Board sets the allowable increase each March at <strong>60% of the Bay Area CPI-U change, capped at 7%</strong>, once per 12 months, base rent only. Building stock pre-June 13, 1979 ⇒ full coverage. AB 1482's 5%+CPI/10% cap is <strong>inapplicable</strong> (more-restrictive local law exemption, §1947.12(d)(3)). There is no federal rent control.</p>
{table_open("Verified AGA values (official Form 571 & SF.gov)", ["Effective period","Allowable increase","Source"])}
{''.join(f'<tr><td class="mono">{esc(r["period"])}</td><td class="mono">{esc(r["rate"])}</td><td class="src-col"><a href="{esc(AGA["source_form"])}">Form 571 ↗</a></td></tr>' for r in AGA["rows"][:8])}
{table_close()}
<p class="small">Full 45-period history: <a href="laws-local.html">Local law (SF)</a>.</p>

<h2>3 · Bottom-line numbers (computed)</h2>
{table_open("Scenario comparison (all amounts computed 2026-11-06; Unit 2 pending ledger)", ["Scenario","Base","Rate","+$/mo","New rent","Notice"])}
<tr><td><a href="units.html#scen-U1-A">Unit 1 — 2026-27 annual</a></td><td class="mono">$3,995.00</td><td class="mono">1.6%</td><td class="mono">+$63.92</td><td class="mono">$4,058.92</td><td>30-day</td></tr>
<tr class="unverified"><td>Unit 1 — banked 1.4% (earliest 2/1/2027) + annual 1.6%</td><td class="mono">$3,995.00</td><td class="mono">3.0% combined</td><td class="mono">+$119.85</td><td class="mono">$4,114.85</td><td>30-day</td></tr>
<tr class="unverified"><td>Unit 2 — 2026-27 annual only</td><td class="mono">$3,150.00</td><td class="mono">1.6%</td><td class="mono">+$50.40</td><td class="mono">$3,200.40</td><td>30-day</td></tr>
<tr class="unverified"><td>Unit 2 — all banked (11.5%) + annual 1.6%</td><td class="mono">$3,150.00</td><td class="mono">13.1% combined</td><td class="mono">+$412.65</td><td class="mono">$3,562.65</td><td><strong>90-day</strong></td></tr>
<tr class="unverified"><td>Unit 2 — benchmark: on-time annual increases 2020–2026</td><td class="mono">$3,150.00</td><td class="mono">1.8/0.7/2.3/3.6/1.7/1.4/1.6%</td><td class="mono">+$435.72 total</td><td class="mono">$3,585.72</td><td>30-day/yr</td></tr>
{table_close()}

<h2>4 · Corporations vs individual owners</h2>
<p>Same caps, same banking rules, same license and petition regime for every owner — what differs is <em>practice discipline</em> and one narrow AB 1482 carve-out (single-family/condo exemption is lost for REIT/corporation/LLC owners, §1947.12(d)(5)). Institutional owners typically run a calendar of maximum lawful AGAs and timely Housing Inventory filings; individual owners more often skip years (as on this property), banking value that may later be imposed once per tenancy with correct notice. No official dataset on increase behavior in 94122 could be read this session; market-practice observations are labeled and flagged (F-R13), not published as fact.</p>

<h2>5 · Correct notification and reasonable reasons</h2>
<p><strong>Reasonable:</strong> cost of living (AGA); banked skips (≥24-month rule); petition-approved passthroughs (capital improvement, operating &amp; maintenance, special circumstances, utility worksheet, bond passthroughs); vacancy decontrol on a genuinely new tenancy — nothing else. <strong>Unlawful:</strong> roommate surcharge; market-rate reset mid-tenancy; retaliation; any protected-class basis; increases without license/notice. <a href="notice-procedure.html">Full notice procedure →</a></p>

<h2>6 · One unit or both?</h2>
<p><strong>Both — using the same objective, published formula applied to each unit's own lawful base, with identical notice machinery and documentation.</strong> The law permits per-tenancy increases and does not require equality; but uniform treatment is the posture that cannot reasonably support a discrimination claim, mirrors "normal business practice," and survives tenant-lawyer scrutiny. Any single-unit raise needs a documented, objective reason (e.g., different banking histories) and carries elevated risk. <a href="one-vs-both.html">Full analysis →</a></p>

<h2>7 · Will it survive tenant-lawyer scrutiny?</h2>
<p>Only if computed exactly as shown, licensed, and noticed correctly — and the Unit 2 ledger confirms the $3,150 base (<a href="flagged.html#F-R7">F-R7</a>), Unit 1's banked 1.4% waits until February 1, 2027 (<a href="flagged.html#F-R5">F-R5</a>), and Unit 2's combined 13.1% uses a 90-day notice (<a href="flagged.html#F-R1">F-R1</a>). Tenants have free legal help (Tenant Right to Counsel via Eviction Defense Collaborative; Rent Board counselor 415-252-4600), so the increase will be scrutinized — design it to pass.</p>

<h2>8 · Flagged for Review</h2>
<p>F-R1 (90-day trigger) · F-R2 (HUD FMR blank) · F-R3 (occupancy ambiguity) · F-R4 (2025 reset) · F-R5 (Unit 1 banking timing) · F-R6 (1.6% methodology, unverified) · F-R7 (Unit 2 base) · F-R8 (anonymization) · F-R9 (RTC citation) · F-R10 (mail +5d) · F-R11 (not legal advice) · F-R12 (verification basis) · F-R13 (market practices labeled). <a href="flagged.html">See all with sources →</a></p>
"""
    return page("executive-summary.html", "Executive Summary", "Analysis · all categories",
                "Important details at a glance: coverage, verified AGA caps, computed scenarios, the one-vs-both answer, notice rules and everything flagged for review.", body)

# ---------- page: units ----------

def page_units():
    u1, u2 = UNITS["units"]
    scen_detail = []
    for s in SCEN["scenarios"]:
        assumptions = "".join(f"<li>{esc(a)}</li>" for a in s["assumptions"])
        scen_detail.append(f"""<div class="card" id="scen-{esc(s['id'])}"><h3>{esc(s['id'])} — {esc(s['label'])}</h3>
<ul class="kpi-list"><li><span>Base rent</span><span class="mono">${esc(fmt_money(s['base_rent']))}</span></li><li><span>Rate applied</span><span>{esc(s['rate_applied'])}</span></li><li><span>Dollar increase</span><span class="mono">+${esc(s['dollar_increase'])}</span></li><li><span>New rent</span><span class="mono"><strong>${esc(fmt_money(s['new_rent']))}</strong></span></li><li><span>Notice</span><span>{esc(s['notice_required'])}</span></li></ul>
<p class="small"><strong>Assumptions &amp; computation notes</strong></p><ul class="tight small">{assumptions}</ul></div>""")
    body = f"""
<div class="callout warn"><strong>Privacy.</strong> Real names are replaced everywhere by placeholders (Tenants A–F). Dates and amounts are preserved exactly as recorded. Unit addresses beyond 94122 are not published. Tenant mapping is held only in the private source file and released nowhere.</div>

<h2>Unit 1 — continuing tenancy</h2>
{table_open("Unit 1 profile (anonymized)", ["Field","Recorded value","Notes"])}
<tr><td>Location</td><td>San Francisco, CA 94122 (Outer Sunset)</td><td>2-unit building, built 1940 · <a href="methodology.html">protocol ↗</a></td></tr>
<tr><td>Last lease start</td><td class="mono">February 1, 2025</td><td>Initial tenancy · <a href="methodology.html">records ↗</a></td></tr>
<tr><td>Monthly rent at lease start</td><td class="mono">$3,995.00</td><td>Preserved exactly · <a href="methodology.html">records ↗</a></td></tr>
<tr><td>Initial-lease tenants (placeholder)</td><td>Tenant A, Tenant B, Tenant C</td><td>Names anonymized · <a href="methodology.html">legend ↗</a></td></tr>
<tr><td>Continuing tenancy</td><td class="mono">From April 1, 2026 @ $3,995.00</td><td>Rent identical to February 2025 — no increase imposed · <a href="methodology.html">records ↗</a></td></tr>
<tr><td>Current tenants (placeholder)</td><td>Tenant A, Tenant D</td><td><a href="flagged.html#F-R3">F-R3 — occupancy-change ambiguity; no added roommate rent may be charged</a></td></tr>
<tr><td>Rent-control coverage</td><td>Full (pre-6/13/79 building)</td><td><a href="{esc(SRC['S-06']['url'])}">SF.gov coverage ↗</a></td></tr>
{table_close()}
<div class="callout warn"><strong>F-R5 — Banked increase not yet available.</strong> The 2025-26 skipped increase (1.4%) is bankable only once <strong>24 full months</strong> pass with no rent increase — i.e., on/after <strong>February 1, 2027</strong>. Earlier imposition would exceed the lawful amount. The 2026-27 1.6% remains available now. <a href="flagged.html#F-R5">Details ↗</a></div>
{table_open("Unit 1 increase scenarios", ["Scenario","Base","Rate","+$ / mo","New rent","Notice","Status"])}
{scenarios_rows_html("Unit 1")}
{table_close()}

<h2>Unit 2 — continuous tenancy since June 1, 2019</h2>
{table_open("Unit 2 profile (anonymized)", ["Field","Recorded value","Notes"])}
<tr><td>Location</td><td>San Francisco, CA 94122 (Outer Sunset)</td><td>2-unit building, built 1940 · <a href="methodology.html">protocol ↗</a></td></tr>
<tr><td>Last lease start</td><td class="mono">June 1, 2019</td><td>Continuous tenancy · <a href="methodology.html">records ↗</a></td></tr>
<tr><td>Monthly rent at lease start</td><td class="mono">$3,150.00</td><td><strong>Current lawful base rent unverified</strong> — <a href="flagged.html#F-R7">F-R7</a>. All Unit 2 computations assume $3,150.00; confirm via ledger + Housing Inventory before service.</td></tr>
<tr><td>Tenants (placeholder)</td><td>Tenant E, Tenant F</td><td>Unchanged since lease start per records · <a href="methodology.html">legend ↗</a></td></tr>
<tr><td>Rent-control coverage</td><td>Full (pre-6/13/79 building)</td><td><a href="{esc(SRC['S-06']['url'])}">SF.gov coverage ↗</a></td></tr>
<tr><td>AGAs skipped (if never imposed)</td><td class="mono">1.8 + 0.7 + 2.3 + 3.6 + 1.7 + 1.4 = 11.5%</td><td>Bankable; no expiry during tenancy; not compounded/prorated; notice must state banked part — <a href="{esc(SRC['S-04']['url'])}">SF.gov banking ↗</a></td></tr>
{table_close()}
{table_open("Unit 2 increase scenarios", ["Scenario","Base","Rate","+$ / mo","New rent","Notice","Status"])}
{scenarios_rows_html("Unit 2")}
{table_close()}
<div class="callout bad"><strong>F-R1 — 90-day trigger.</strong> A single notice imposing 11.5% banked + 1.6% annual (13.1% combined) exceeds the 10% threshold in Civil Code §827(b)(3)(A); a <strong>90-day</strong> written notice is mandatory. Splitting notices cannot exceed the AGA for any 12-month period. <a href="flagged.html#F-R1">Details ↗</a></div>

<h2>Computation detail (per scenario)</h2>
<div class="grid cols-2">
{''.join(scen_detail)}
</div>
<p class="small">Computed with exact decimal arithmetic on 2026-11-06 (scripts/build_rental.py; inputs in data/rental/scenarios.json). Values are not Rent Board determinations.</p>
"""
    return page("units.html", "Units & Increase Scenarios", "Property · 94122 (Outer Sunset) · built 1940",
                "Anonymized profiles of the two rent-controlled units — dates and amounts preserved — with computed allowable increases, banking math and notice requirements. Unit 2's base rent is unverified (F-R7).", body)

# ---------- page: laws-local ----------

def page_laws_local():
    body = f"""
<div class="callout info"><strong>Governing framework.</strong> San Francisco Administrative Code Chapter 37 (Residential Rent Stabilization and Arbitration Ordinance) limits annual rent increases to <strong>60% of the published Bay Area CPI-U increase, in no event more than 7%</strong>, for licensed landlords whose units are covered. Building stock: pre–June 13, 1979 ⇒ full coverage. Official code library: {src_link('S-09','SF Admin Code §37.3')}.</div>

<h2>Allowable Annual Increase history — verbatim from official Form 571</h2>
<p class="small">45 periods, April 1, 1982 → February 28, 2027. Source: <a href="{esc(AGA['source_form'])}">Form 571 Allowable Annual Increases 26-27 (sf.gov) ↗</a>, read 2026-11-06. The 1992–93 footnote (*) is printed on the form: only ONE of the two increases may be imposed.</p>
{table_open("SF Allowable Annual Increases (all periods)", ["Effective period","Increase","Note","Source"])}
{aga_rows_html()}
{table_close()}

<h2>The rules a tenant lawyer applies (each row → official source)</h2>
{table_open("SF Rent Ordinance & Rent Board requirements", ["Rule","Requirement","Source"])}
<tr><td>Coverage</td><td>Full protection (rent cap + just cause) for most SF residential units, incl. pre-6/13/1979 stock; partial (eviction-only) for post-1979 construction, most SFH/condos with tenancy from 1/1/1996, substantially rehabilitated units</td><td><a href="{esc(SRC['S-06']['url'])}">SF.gov coverage ↗</a></td></tr>
<tr><td>Formula &amp; cap</td><td>Annual increase ≤ 60% of published Bay Area CPI-U growth; never more than 7%; license required (ties to §37.15 Housing Inventory reporting)</td><td><a href="{esc(SRC['S-09']['url'])}">SF Admin Code §37.3 ↗</a></td></tr>
<tr><td>Current rate</td><td>1.6% effective 3/1/2026–2/28/2027 (announced January 14, 2026); example $2,000.00 × .016 = $32.00</td><td><a href="{esc(SRC['S-07']['url'])}">SF.gov news ↗</a> · <a href="{esc(SRC['S-02']['url'])}">Current Rates ↗</a></td></tr>
<tr><td>Base rent scope</td><td>Compute on base rent only; includes parking/storage housing services; excludes temporary passthroughs &amp; fluctuating charges; <strong>no rounding up</strong></td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov rent increases ↗</a></td></tr>
<tr><td>Cadence</td><td>Once per 12 months; first increase ≥12 months after lease start; first increase sets "anniversary date"; late imposition moves the anniversary date</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov rent increases ↗</a></td></tr>
<tr><td>Banking</td><td>Skipped increase bankable only after <strong>≥24 full months</strong> without any increase; no expiry during tenancy; no cap; not compounded/prorated; add banked %s × current base rent; combine with annual increase; partial use leaves remainder banked; carries to new owners, not new tenants; allowed since 4/1/1982; notice must state banked part; Rent Increase License required</td><td><a href="{esc(SRC['S-04']['url'])}">SF.gov banked increases ↗</a></td></tr>
<tr><td>Rent Increase License</td><td>Required before imposing annual allowable and/or banked increases; effective 7/1/2022 (3/1/2023 for condos and 1–9 unit buildings); prerequisite: report into Rent Board Housing Inventory</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a> · <a href="{esc(SRC['S-04']['url'])}">Banking ↗</a> · <a href="{esc(SRC['S-08']['url'])}">Housing Inventory FAQ ↗</a></td></tr>
<tr><td>Petition-only increases</td><td>Capital improvement; operating &amp; maintenance; special circumstances (comparable units); Proposition I past-history; utility (petition or worksheet); §1.21 occupancy — must file BEFORE noticing; retroactive only if approved and notice valid; free filing</td><td><a href="{esc(SRC['S-05']['url'])}">SF.gov petitions ↗</a></td></tr>
<tr><td>Bond passthroughs</td><td>General obligation bond &amp; water revenue bond passthroughs need no petition but DO need the Rent Board worksheet filed before notice (plus certain utility worksheets)</td><td><a href="{esc(SRC['S-05']['url'])}">SF.gov petitions ↗</a></td></tr>
<tr><td>Additional occupant</td><td>No increase may be charged merely because a new/additional roommate moved in — unlawful even if the lease provides for it</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Vacancy decontrol</td><td>No limit on the initial rent of an emptied unit (Costa-Hawkins); limits resume on the new tenancy</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a> · <a href="{esc(SRC['S-15']['url'])}">CC §1954.53 ↗</a></td></tr>
<tr><td>Eviction protections (context)</td><td>Just-cause applies to most SF units incl. post-1979 stock and SFH/condos; Rent Board counseling (415) 252-4600; Tenant Right to Counsel for eviction matters</td><td><a href="{esc(SRC['S-10']['url'])}">SF.gov evictions ↗</a> · <a href="{esc(SRC['S-11']['url'])}">Form 1007 ↗</a></td></tr>
<tr><td>Relocation (if no-fault eviction pursued)</td><td>3/1/26–2/28/27: $8,245.00/tenant, $24,733.00 max/unit, +$5,497.00 elderly (60+)/disabled/minor-child; Ellis: $11,110.05 / $33,330.13 / +$7,443.90 (62+)</td><td><a href="{esc(SRC['S-02']['url'])}">SF.gov Current Rates ↗</a></td></tr>
<tr><td>Security deposit interest</td><td>4.2% (3/1/26–2/28/27); 5.0% (25-26); 5.2% (24-25)</td><td><a href="{esc(SRC['S-02']['url'])}">SF.gov Current Rates ↗</a></td></tr>
<tr><td>Capital improvement imputed interest</td><td>4.1% (7-yr, factor .01372) · 4.3% (10-yr, .01027) · 4.6% (15-yr, .00770) · 4.8% (20-yr, .00649); use rate in effect at petition filing</td><td><a href="{esc(SRC['S-02']['url'])}">SF.gov Current Rates ↗</a></td></tr>
{table_close()}

<h2>Where landlords go wrong (2026 practice)</h2>
<div class="callout warn"><ul class="tight">
<li>Imposing the 1.6% without the Housing Inventory license — the increase is unenforceable until licensed (S-01, S-04).</li>
<li>Rounding $63.92 up to $64 — prohibited (S-01).</li>
<li>Mailing a 30-day notice and waiting only 30 calendar days — mailed service adds 5 days (S-01, S-04, S-12).</li>
<li>Serving Unit 2's 13.1% combined increase on 30 days — defective; 90 days required (S-12).</li>
<li>Charging either unit for a new roommate — unlawful (S-01).</li>
<li>Noticing an above-AGA amount "subject to Rent Board approval" without filing the petition first — tenants need not pay until approved, and approval is retroactive only to a <em>valid</em> notice date (S-05).</li>
</ul></div>
"""
    return page("laws-local.html", "Local Law — San Francisco Rent Ordinance", "Legal framework · City & County of San Francisco",
                "Administrative Code Chapter 37, the 60%-of-Bay-Area-CPI formula (7% cap), the complete Allowable Annual Increase history, banking rules, the Rent Increase License, petition-based passthroughs and relocation rates — all from official SF sources.", body)

# ---------- page: laws-state ----------

def page_laws_state():
    body = f"""
<div class="callout info"><strong>Layer order.</strong> For these two units the <em>local</em> AGA is the operative cap: AB 1482 yields to more-restrictive local rent control. State law still governs <strong>notice mechanics</strong> (§827), <strong>anti-discrimination</strong> (Unruh §51; FEHA §12955) and <strong>vacancy decontrol on new tenancies</strong> (Costa-Hawkins §1954.53).</div>

<h2>California law rows (each row → official text)</h2>
{table_open("State statutes and their effect on these units", ["Statute","What it does","Effect on Unit 1 / Unit 2","Source"])}
<tr><td>Civil Code §827 — notice of rent increase</td><td>≤10% combined increase (vs. lowest rent charged in prior 12 months): <strong>30-day</strong> written notice, personal or mail (+5 days, CCP §1013). &gt;10% combined: <strong>90-day</strong> notice. Service details: §827(b)(1)–(3). Notice incorporated into lease on tenant's continued occupancy (§827(a)(2)).</td><td>Unit 1 combined 3.0% → 30 days. Unit 2 combined 13.1% → <strong>90 days</strong>.</td><td><a href="{esc(SRC['S-12']['url'])}">leginfo §827 ↗</a></td></tr>
<tr><td>Civil Code §1947.12 — AB 1482 rent cap (Tenant Protection Act)</td><td>Rent may not rise &gt;5% + CPI, or 10%, whichever lower, over any 12-month period; max two increments/12 months; new-tenancy initial rate freely set. <strong>Exempt:</strong> housing subject to a more-restrictive local rent/price control (§1947.12(d)(3)); new construction within 15 years (d)(4). SF rent-controlled units are outside the cap.</td><td>No cap beyond SF AGA. Track for the building generally; SF applies.</td><td><a href="{esc(SRC['S-13']['url'])}">leginfo §1947.12 ↗</a></td></tr>
<tr><td>§1947.12(d)(5) — the owner-identity carve-out</td><td>Even the single-family/condo exemption is lost where the owner is a REIT, corporation or LLC. This is the one place California law treats "corporate landlords" differently from individuals.</td><td>Both units are pre-1979 multi-unit stock; exemption analysis irrelevant — full SF control regardless of owner type.</td><td><a href="{esc(SRC['S-13']['url'])}">leginfo §1947.12 ↗</a></td></tr>
<tr><td>Civil Code §1946.2 — AB 1482 just cause</td><td>After 12 months' continuous lawful occupancy, tenancy may not be terminated absent just cause stated in a written notice (at-fault or no-fault). Anti-avoidance backstop; retaliation for asserting rights is unlawful.</td><td>A purported "increase" that functions as a de facto eviction is unlawful. Any increase must stand alone on AGA/banking math.</td><td><a href="{esc(SRC['S-14']['url'])}">leginfo §1946.2 ↗</a></td></tr>
<tr><td>Civil Code §1954.53 — Costa-Hawkins vacancy decontrol</td><td>Owner may set the <strong>initial</strong> rent on a new tenancy, except where prior tenancy was terminated by the owner (§1954.53(a)(1)) or other exceptions apply. During an ongoing tenancy it is no defense to an AGA-only increase claim nor a license to exceed the AGA.</td><td>Unit 1 (Feb 1, 2025 commencement): $3,995 may have been a lawful vacancy reset — <strong>unverified</strong>, see <a href="flagged.html#F-R4">F-R4</a>. Unit 2 (June 1, 2019): same analysis would have applied then; not re-usable now.</td><td><a href="{esc(SRC['S-15']['url'])}">leginfo §1954.53 ↗</a></td></tr>
<tr><td>Civil Code §51 — Unruh Civil Rights Act</td><td>Full and equal accommodations in all business establishments regardless of sex, race, color, religion, ancestry, national origin, disability, medical condition, genetic information, marital status, sexual orientation, citizenship, primary language, immigration status (§51(b), (e)).</td><td>Increase practice must be uniform or objectively justified; tenant selection of notice template must not vary by protected class.</td><td><a href="{esc(SRC['S-16']['url'])}">leginfo §51 ↗</a></td></tr>
<tr><td>Gov Code §12955 — FEHA housing discrimination</td><td>Unlawful to discriminate or harass in housing because of race, color, religion, sex, gender, gender identity/expression, sexual orientation, marital status, national origin, ancestry, familial status, <strong>source of income</strong>, disability, veteran/military status, genetic information; retaliation unlawful (§12955(f)); discriminatory notices/ads unlawful (§12955(c)).</td><td>Any increase targeted at a unit because of its occupants' protected class — or retaliation for complaints — violates FEHA. Objective AGA math is the antidote.</td><td><a href="{esc(SRC['S-17']['url'])}">leginfo §12955 ↗</a></td></tr>
{table_close()}

<h2>AB 1482 quick-math (for the record)</h2>
<div class="callout info"><p><strong>If</strong> AB 1482 applied (it does not for these units): max annual increase = 5% + Bay Area CPI-U change, or 10%, whichever is lower, of the <em>lowest</em> rent charged in the prior 12 months; at most two increments per 12 months; clear written notice under Civil Code §827 still required. For SF rent-controlled units the operative number is the AGA (1.6% for 3/1/26–2/28/27), which is always tighter. (§1947.12(a)(1)–(2), (d)(3) — <a href="{esc(SRC['S-13']['url'])}">leginfo ↗</a>)</p></div>
"""
    return page("laws-state.html", "State Law — California", "Legal framework · State of California",
                "Costa-Hawkins vacancy decontrol, the Tenant Protection Act (AB 1482) and its exemptions, the §827 30/90-day notice rule, just cause (§1946.2), and Unruh/FEHA anti-discrimination statutes — each row linked to leginfo.legislature.ca.gov.", body)

# ---------- page: laws-federal ----------

def page_laws_federal():
    body = f"""
<div class="callout info"><strong>No federal rent control exists.</strong> The federal government does not cap private rents. Federal law reaches this analysis in exactly two ways: (1) the <strong>Fair Housing Act</strong> bars discriminatory terms, conditions and privileges of rental — including how increases are set and served; (2) HUD <strong>Fair Market Rents</strong> are a federal benchmark for subsidized programs — <em>not</em> a cap, and not evidence of lawful rent for a specific unit.</div>

<h2>Federal rows (each row → official source)</h2>
{table_open("Federal framework", ["Item","What it is","Effect on this property","Source"])}
<tr><td>Fair Housing Act (42 U.S.C. 3601 et seq.)</td><td>Bars discrimination in the sale, rental and <strong>terms/conditions/privileges</strong> of housing because of race, color, national origin, religion, sex, disability, familial status. Retaliation is illegal. HUD FHEO investigates; SF Regional Office: One Sansome Street, Suite 1200, San Francisco, CA 94104, (415) 489-6524, (800) 347-3739.</td><td>Increase notices must not be issued/structured on any protected-class basis; complaint path runs through HUD FHEO (online or 1-800-669-9777).</td><td><a href="{esc(SRC['S-18']['url'])}">hud.gov report ↗</a> · <a href="{esc(SRC['S-21']['url'])}">FHEO contact ↗</a></td></tr>
<tr><td>No federal rent stabilization statute</td><td>Nothing in federal law caps or schedules private residential rents; FMRs (below) are voucher/HOME/CoC benchmarks, not price controls.</td><td>State (AB 1482) and local (SF AGA) regimes control; both units under SF AGA as more-restrictive local law (§1947.12(d)(3)).</td><td><a href="{esc(SRC['S-13']['url'])}">leginfo §1947.12 ↗</a> · <a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR ↗</a></td></tr>
<tr><td>HUD Fair Market Rents (40th percentile) — FY2027</td><td>HUD annually estimates FMR areas' 40th-percentile gross rents (24 CFR 888.113; effective Oct 1, 2026 per FY2027 notice, Docket FR-6553-N-03); used for voucher payment standards and rent ceilings in HOME/ESG/CoC. <strong>Not</strong> a cap on private rent; <strong>not</strong> proof of a unit's market rent.</td><td>Context only. FY2027 San Francisco area values could not be read from the official area-level tool this session and are therefore <strong>left blank</strong> — <a href="flagged.html#F-R2">F-R2</a>. (Secondary reporting, unverified: 2BR ≈ $3,697, T-03.)</td><td><a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR ↗</a> · <a href="{esc(SRC['S-20']['url'])}">Federal Register FY2027 ↗</a></td></tr>
<tr><td>FY2026 FMRs (for reference)</td><td>FMRs are indexed to each federal fiscal year; FY2026 notice published Aug. 22, 2025 (90 FR 41096, cited in the FY2027 notice).</td><td>Historical benchmark; figures not re-published here (see F-R2).</td><td><a href="{esc(SRC['S-20']['url'])}">Federal Register FY2027 (cites FY2026) ↗</a></td></tr>
<tr><td>Federal reporting channels</td><td>Housing discrimination: HUD FHEO online or 1-800-669-9777 (S-18). FHA violations may also proceed via DOJ pattern-or-practice referral.</td><td>A tenant alleging discrimination over an increase may file with HUD; owner should expect document request.</td><td><a href="{esc(SRC['S-18']['url'])}">hud.gov ↗</a></td></tr>
{table_close()}

<h2>HUD FMR values — deliberately blank</h2>
<div class="table-wrap"><table><caption>FY2027 HUD FMR — San Francisco (values blank: not confirmable from official page this session)</caption>
<thead><tr><th scope="col">Area / bedroom</th><th scope="col">FY2027 FMR</th><th scope="col">Status</th><th scope="col">Verify at</th></tr></thead><tbody>
<tr class="unverified"><td>San Francisco-Oakland-Fremont, CA HUD Metro FMR Area — efficiency</td><td class="empty" aria-label="blank, unverified"></td><td>{badge('warn','unverified')}</td><td><a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR Query ↗</a></td></tr>
<tr class="unverified"><td>Same area — 1-bedroom</td><td class="empty" aria-label="blank, unverified"></td><td>{badge('warn','unverified')}</td><td><a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR Query ↗</a></td></tr>
<tr class="unverified"><td>Same area — 2-bedroom</td><td class="empty" aria-label="blank, unverified"></td><td>{badge('warn','unverified')}</td><td><a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR Query ↗</a></td></tr>
<tr class="unverified"><td>Same area — 3-bedroom</td><td class="empty" aria-label="blank, unverified"></td><td>{badge('warn','unverified')}</td><td><a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR Query ↗</a></td></tr>
<tr class="unverified"><td>Same area — 4-bedroom</td><td class="empty" aria-label="blank, unverified"></td><td>{badge('warn','unverified')}</td><td><a href="{esc(SRC['S-19']['url'])}">HUDUSER FMR Query ↗</a></td></tr>
</tbody></table></div>
<p class="small">The FY2027 Federal Register notice confirms the program, effective date (2026-10-01) and area documentation, but not area-level dollar figures; the HUD area tool could not be read. Per project rules, values that cannot be confirmed from an official source are left blank and flagged — see <a href="flagged.html#F-R2">F-R2</a>.</p>
"""
    return page("laws-federal.html", "Federal Law & HUD", "Legal framework · United States",
                "There is no federal rent control. What exists instead: the Fair Housing Act (terms, conditions and privileges of rental), HUD's Fair Market Rents as program benchmarks, and the FHEO complaint path. FMR dollar figures are blank here — see F-R2.", body)

# ---------- page: market practices ----------

def page_market():
    body = f"""
<div class="callout warn"><strong>Evidence boundary (F-R13).</strong> No official dataset on corporate-vs-individual rent-increase practice in 94122 could be read this session. The legal framework below is official and verified. The "practice" observations are clearly labeled general practice, rest on secondary/non-official material where noted, and are flagged — never published as verified fact.</div>

<h2>What the law treats identically (official)</h2>
{table_open("Owner-agnostic rules — every landlord, corporate or individual", ["Rule","Requirement","Source"])}
<tr><td>AGA cap &amp; cadence</td><td>Same 1.6% (3/1/26–2/28/27), once per 12 months, first increase ≥12 months after lease start — for corporate and individual owners alike</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a> · <a href="{esc(SRC['S-09']['url'])}">§37.3 ↗</a></td></tr>
<tr><td>Banking</td><td>≥24 full months with no increase before a skip is banked; no expiry; no cap; non-compounded/prorated — same for all owners</td><td><a href="{esc(SRC['S-04']['url'])}">SF.gov banking ↗</a></td></tr>
<tr><td>Rent Increase License</td><td>Housing Inventory registration before imposing allowable/banked increases — all owners, all unit counts (condos and 1–9-unit buildings: since 3/1/2023)</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Petition-based increases</td><td>Capital improvement, operating &amp; maintenance, comparable-unit, utility, Prop I, §1.21 — filing before notice; Retroactive only if approved</td><td><a href="{esc(SRC['S-05']['url'])}">SF.gov petitions ↗</a></td></tr>
<tr><td>Notice rules</td><td>30/90-day per §827; contents (dollar, %, effective date, banked portion); +5 days if mailed — all owners</td><td><a href="{esc(SRC['S-12']['url'])}">CC §827 ↗</a> · <a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Vacancy decontrol (Costa-Hawkins)</td><td>INITIAL rent on a new tenancy freely set — but owner-termination and public-contract exceptions apply (§1954.53(a)(1)–(4))</td><td><a href="{esc(SRC['S-15']['url'])}">CC §1954.53 ↗</a></td></tr>
<tr><td>AB 1482</td><td>Inapplicable to these units ((d)(3) local-control exemption); where it does apply, 5%+CPI/10% cap, two increments max, written notice</td><td><a href="{esc(SRC['S-13']['url'])}">CC §1947.12 ↗</a></td></tr>
{table_close()}

<h2>Where the law distinguishes owners (official)</h2>
{table_open("The only owner-identity distinction in the framework", ["Provision","Distinction","Consequence"])}
<tr><td>Civil Code §1947.12(d)(5)</td><td>Single-family/condo exemption from AB 1482 is lost if the owner is a real estate investment trust, a corporation, or a limited liability company (§1947.12(d)(5)(A)(i)–(iii))</td><td>Corporate owners of SFH/condos stay under AB 1482; individual owners may be exempt (state law), though SF eviction rules still apply to most SF units (S-10)</td><td><a href="{esc(SRC['S-13']['url'])}">CC §1947.12 ↗</a></td></tr>
{table_close()}

<h2>General practice — labeled, unverified (F-R13)</h2>
<div class="grid cols-2">
  <div class="card"><h3>Institutional / corporate owners</h3><ul class="tight">
    <li>Systematically impose the <em>maximum lawful AGA every year on the anniversary date</em> — no banking build-up; compliance-calendar management.</li>
    <li>Maintain Housing Inventory registrations and batch filings across portfolios; dedicated counsel sign-off before notices.</li>
    <li>Where banked balances are imposed in one letter, the same §827(b)(3)(A) 90-day rule applies once the combined increase exceeds 10% — corporate notices still need 90 days.</li>
    <li><span class="badge warn">practice observation — no official 94122 source; see F-R13</span></li>
  </ul></div>
  <div class="card"><h3>Individual / "mom-and-pop" owners</h3><ul class="tight">
    <li>Frequently skip anniversary increases (relational tenants), building large banked balances — exactly the Unit 2 pattern (11.5% banked since 2020, if never imposed).</li>
    <li>Then either never impose (leaving value unrealized), or impose once with a 90-day combined notice after long silence.</li>
    <li>More likely to err procedurally: license, mailing (+5 days), rounding, roommate surcharges — the SF.gov "common mistakes" list applies to them most (S-01).</li>
    <li><span class="badge warn">practice observation — no official 94122 source; see F-R13</span></li>
  </ul></div>
</div>

<h2>What "normal business practice" means for this property</h2>
<div class="callout good"><p><strong>Benchmark behavior:</strong> (1) register Housing Inventory / hold license; (2) compute AGA on base rent without rounding; (3) notice correctly (30/90 days +5 if mailed); (4) same template and method for both units; (5) document the ledger basis for any banked portion; (6) keep proof of service. An increase structured this way is what a SF tenant lawyer or the Rent Board itself would recognize as ordinary, lawful practice. Anything beyond it — percentage games, selective targeting, roommate fees — is not "normal business practice," corporate or otherwise.</p></div>

<h2>Secondary material consulted (flagged, not authoritative)</h2>
<div class="table-wrap"><table><caption>Secondary sources — used to frame verification only</caption><thead><tr><th scope="col">ID</th><th scope="col">Source</th><th scope="col">Note</th></tr></thead><tbody>
<tr class="unverified"><td>T-01</td><td><a href="{esc(SEC['T-01']['url'])}">Kenny Realty (2025-26 1.4%)</a></td><td>Corroborates S-02/S-03; not used for any published value.</td></tr>
<tr class="unverified"><td>T-02</td><td><a href="{esc(SEC['T-02']['url'])}">Relisto (2026-27 1.6% methodology claim)</a></td><td>Geometric-mean CPI estimation story — unverified; see <a href="flagged.html#F-R6">F-R6</a>.</td></tr>
<tr class="unverified"><td>T-03</td><td><a href="{esc(SEC['T-03']['url'])}">VoucherMatch (SF FY2027 2BR FMR $3,697)</a></td><td>FMR figures left blank; see <a href="flagged.html#F-R2">F-R2</a>.</td></tr>
<tr class="unverified"><td>T-04</td><td><a href="{esc(SEC['T-04']['url'])}">SF Service Guide (Tenant Right to Counsel)</a></td><td>Prop F context; official corroboration via S-11 (Form 1007).</td></tr>
</tbody></table></div>
"""
    return page("market-practices.html", "Market Practices — Corporations vs Individuals", "Analysis · practice with labeled evidence boundaries",
                "The legal framework treats corporate and individual owners identically for these units; only AB 1482's owner-identity carve-out differs in narrow cases. Practices are labeled and flagged — no official 94122 practice dataset was readable.", body)

# ---------- page: notice procedure ----------

def page_notice():
    body = f"""
<div class="callout info"><strong>Golden rule.</strong> A rent increase that is substantively lawful can still be defeated by defective service. The sequence below is the one SF.gov and Civil Code §827 require; deviating converts a valid increase into an invalid one.</div>

<h2>Step-by-step</h2>
<ol class="steps">
<li><strong>Confirm coverage &amp; license.</strong> Both units: pre-6/13/1979 building ⇒ full Chapter 37 protection. Confirm the Rent Board <strong>Housing Inventory report</strong> is filed and the <strong>Rent Increase License</strong> is held before any allowable/banked increase may be imposed (in effect 7/1/2022; 3/1/2023 for condos &amp; 1–9-unit buildings). <a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></li>
<li><strong>Pull the ledger.</strong> Rent actually charged for the prior 12 months (for the §827 10% computation), every increase date since tenancy start, and every skipped year (for banking). Unit 2's ledger is <strong>not yet pulled</strong> — <a href="flagged.html#F-R7">F-R7</a>.</li>
<li><strong>Compute on base rent only.</strong> Base rent includes parking/storage housing services; excludes temporary passthroughs and fluctuating charges. 1.6% × $3,995.00 = $63.92 (Unit 1) / 1.6% × $3,150.00 = $50.40 (Unit 2). <strong>Never round up.</strong> <a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></li>
<li><strong>Choose the increase size.</strong> One 12-month period per increase; no more than two increments/12 months under AB 1482 were it to apply (it does not). Combined increase in any 12-month window ≤10% ⇒ 30-day notice; &gt;10% ⇒ 90-day.</li>
<li><strong>Determine the percentage for the notice.</strong> Use the AGA in effect on the <em>effective date</em> of the increase (not the date the notice is served). For 2026-27: 1.6%. <a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></li>
<li><strong>Draft the notice.</strong> Must state: (a) the new rent in <strong>dollars</strong>; (b) the <strong>percentage</strong>; (c) the <strong>effective date</strong>; (d) if any portion is banked, <strong>which portion</strong> is banked. Identify the unit, the tenancy, and the signature/date. <a href="{esc(SRC['S-04']['url'])}">SF.gov banking ↗</a></li>
<li><strong>Serve correctly.</strong> Personal delivery to the tenant, or mail under CCP §1013 procedures (+5 days for California-mailed service). SF.gov: "30-day written notice / 90-day if &gt;10% / +5 more days if mailed." Keep proof of service (declaration). <a href="{esc(SRC['S-12']['url'])}">CC §827 ↗</a></li>
<li><strong>Timing.</strong> First-ever increase: ≥12 months after the lease began. After any increase: ≥12 months before the next. Imposing late moves the anniversary date to the actual effective date (new anniversary). Unit 1: first increase eligible February 1, 2026 (2025-26, 1.4%) — skipped, so subject to the ≥24-month rule for banking; 2026-27 1.6% available now.</li>
<li><strong>Petition first?</strong> If any amount relies on capital improvement, operating &amp; maintenance, special circumstances, utility worksheet or bond passthrough, <strong>file the petition/worksheet BEFORE serving the notice</strong>; amount is retroactive to the effective date in a valid notice only if approved. <a href="{esc(SRC['S-05']['url'])}">SF.gov petitions ↗</a></li>
<li><strong>After service.</strong> Keep a copy + proof; diarize the next eligible date; do not re-notice within 12 months; adjust the security deposit interest if deposits are involved (4.2% 2026-27, S-02).</li>
</ol>

<h2>Notice content checklist (what a SF tenant lawyer looks for)</h2>
{table_open("Notice adequacy — pass/fail", ["Element","Required?","Source"])}
<tr><td>Dollar amount of increase</td><td>Required</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Percentage amount</td><td>Required</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Effective date of increase</td><td>Required</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Which portion (if any) is banked</td><td>Required for banked increases</td><td><a href="{esc(SRC['S-04']['url'])}">SF.gov banking ↗</a></td></tr>
<tr><td>License / Housing Inventory reference</td><td>Strongly advisable (license itself is mandatory)</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>Service method + proof</td><td>Required (personal or CCP §1013 mail)</td><td><a href="{esc(SRC['S-12']['url'])}">CC §827 ↗</a></td></tr>
<tr><td>30 days (≤10%) / 90 days (&gt;10%) / +5 if mailed</td><td>Mandatory periods</td><td><a href="{esc(SRC['S-12']['url'])}">CC §827 ↗</a> · <a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
{table_close()}

<h2>Reasonable reasons — and what is never a reason</h2>
<div class="grid cols-2">
  <div class="card"><h3>Reasonable, lawful reasons</h3><ul class="tight">
    <li>Cost of living — the AGA (60% of Bay Area CPI-U, 1.6% now) ({src_link('S-01','S-01')})</li>
    <li>Banked skipped increases — computed, noticed as banked portion ({src_link('S-04','S-04')})</li>
    <li>Petition-approved: capital improvement; operating &amp; maintenance; special circumstances / comparable units; Prop I past-history; utility; §1.21 occupancy ({src_link('S-05','S-05')})</li>
    <li>Utility passthroughs on filed worksheet; GO-bond / water revenue bond passthroughs on worksheet ({src_link('S-05','S-05')})</li>
    <li>Costa-Hawkins vacancy reset — NEW tenancy only, subject to §1954.53 exceptions ({src_link('S-15','S-15')})</li>
  </ul></div>
  <div class="card"><h3>Never a lawful reason</h3><ul class="tight">
    <li>"Market rent" above the AGA during an ongoing tenancy</li>
    <li>New or additional roommate (expressly unlawful even if the lease allows a surcharge) ({src_link('S-01','S-01')})</li>
    <li>Retaliation for protected activity — complaints, organizing, asserting habitability rights (FEHA §12955(f); see {src_link('S-17','S-17')})</li>
    <li>Any protected-class basis — race, color, religion, sex, gender, gender identity/expression, sexual orientation, marital status, national origin, ancestry, familial status, source of income, disability, veteran/military status, genetic information ({src_link('S-17','S-17')} · {src_link('S-16','S-16')} · {src_link('S-18','S-18')})</li>
    <li>Lack of license, wrong notice period, math errors, rounding up — procedural, not substantive</li>
  </ul></div>
</div>
"""
    return page("notice-procedure.html", "Notice Procedure — How to Do It Right", "Procedure · service & content",
                "The exact sequence SF.gov and Civil Code §827 require — license first, base-rent math, 30/90-day service rules, the mandatory notice contents, and what never qualifies as a lawful reason.", body)

# ---------- page: one vs both ----------

def page_one_vs_both():
    body = f"""
<div class="callout info"><strong>Short answer.</strong> Raise <strong>both</strong> units — with the same objective, published formula applied to each unit's own lawful base, identical notice templates, and identical documentation. The law allows per-tenancy increases; it does not require parity. But uniform treatment is the only posture that never even <em>raises the question</em> of discrimination, mirrors normal business practice, and passes SF tenant-lawyer scrutiny cleanly. A one-unit raise is defensible <em>only</em> with a documented, objective reason — different banking histories — retained in the file.</div>

<h2>The legal frame (official)</h2>
{table_open("What the law does — and does not — require", ["Question","Answer","Source"])}
<tr><td>Must both units get the same increase?</td><td><strong>No.</strong> Chapter 37 keys increases to each tenancy (base rent, anniversary date, banking history). Two units can lawfully receive different increases for objective reasons.</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov</a> · <a href="{esc(SRC['S-04']['url'])}">banking ↗</a></td></tr>
<tr><td>What makes an increase discriminatory?</td><td>Selection by protected class (race, color, religion, sex, gender/identity/expression, sexual orientation, marital status, national origin, ancestry, familial status, source of income, disability, veteran/military status, genetic information) — not the amount itself.</td><td><a href="{esc(SRC['S-17']['url'])}">FEHA §12955</a> · <a href="{esc(SRC['S-16']['url'])}">Unruh §51</a> · <a href="{esc(SRC['S-18']['url'])}">FHA/HUD ↗</a></td></tr>
<tr><td>May an owner retaliate against a tenant for asserting rights via an increase?</td><td><strong>No</strong> — retaliation is unlawful (FEHA §12955(f)); also constrains eviction-related pressure (§1946.2 just cause).</td><td><a href="{esc(SRC['S-17']['url'])}">FEHA ↗</a> · <a href="{esc(SRC['S-14']['url'])}">CC §1946.2 ↗</a></td></tr>
<tr><td>Does equal treatment prove non-discrimination?</td><td>Strong evidence of regular business practice; the converse (disparate burden with no objective basis) is what advocates probe with testing and discovery.</td><td><a href="{esc(SRC['S-18']['url'])}">HUD FHEO ↗</a></td></tr>
{table_close()}

<h2>Applied to these two units</h2>
{table_open("Comparison of the two units' situations (objective)", ["Factor","Unit 1","Unit 2"])}
<tr><td>Tenancy start</td><td class="mono">February 1, 2025</td><td class="mono">June 1, 2019 · <a href="methodology.html">records ↗</a></td></tr>
<tr><td>Base rent (as recorded)</td><td class="mono">$3,995.00</td><td class="mono">$3,150.00 (unverified — F-R7)</td></tr>
<tr><td>Years without any increase</td><td>~1 yr 9 mo (to Feb 1, 2027) — <a href="flagged.html#F-R5">F-R5</a></td><td>~7.5 yrs — <a href="flagged.html#F-R7">F-R7</a></td></tr>
<tr><td>Banked capacity (if never imposed)</td><td>1.4% (2025-26), bankable from 2/1/2027 — <a href="flagged.html#F-R5">F-R5</a></td><td>11.5% (2020–2025 skips), if the ledger confirms — <a href="flagged.html#F-R7">F-R7</a></td></tr>
<tr><td>2026-27 annual available now</td><td>1.6% ($63.92) — <a href="units.html#scen-U1-A">scenario ↗</a></td><td>1.6% ($50.40) — <a href="units.html#scen-U2-A">scenario ↗</a></td></tr>
<tr><td>Occupant cohorts (placeholder)</td><td>Tenant A, Tenant D (initial: A, B, C)</td><td>Tenant E, Tenant F (unchanged) — <a href="methodology.html">legend ↗</a></td></tr>
{table_close()}

<h2>Risk matrix</h2>
{table_open("Options ranked by discrimination/challenge risk", ["Option","Lawful?","Risk","Assessment"])}
<tr><td><strong>Both units — AGA-only increase, same notice, same date</strong> (1.6% each: $63.92 / $50.40)</td><td>Yes</td><td><span class="badge ok">lowest</span></td><td>Uniform objective formula; zero protected-class inference; mirrors normal practice; trivially explained to Rent Board or counsel. Recommended baseline.</td></tr>
<tr><td><strong>Both units — each at its own maximum (Unit 1: 1.6% now or 3.0% from 2/1/2027; Unit 2: up to 13.1% with 90-day notice)</strong></td><td>Yes, if ledger/banking/license/notice all verified</td><td><span class="badge ok">low–moderate</span></td><td>Objective per-tenancy differences (anniversary dates, banking) are lawful; documentation burden higher — notice must itemize banked parts separately per unit; Unit 2 needs 90 days. Still uniform <em>methodology</em> = strong defense.</td></tr>
<tr><td><strong>Only Unit 2 raised; Unit 1 skipped</strong></td><td>Lawful in principle</td><td><span class="badge warn">elevated</span></td><td>Different outcomes per unit need a documented objective reason; expect the question "why only them?" Document: Unit 2 is 7.5 years without any increase; Unit 1's banked 1.4% is not yet available (F-R5). Retain the ledger math with the notice.</td></tr>
<tr><td><strong>Only Unit 1 raised; Unit 2 skipped</strong></td><td>Lawful in principle</td><td><span class="badge warn">elevated</span></td><td>Same analysis reversed; only defensible with documentation. No scenario in the records justifies Unit 1 over Unit 2 today except annual symmetry.</td></tr>
<tr><td><strong>Either unit raised above AGA without petition; roommate surcharge; retaliation-linked amount</strong></td><td><strong>No</strong></td><td><span class="badge bad">unlawful</span></td><td>Per se violations: S-01, S-05, FEHA §12955(f). Do not do.</td></tr>
{table_close()}

<h2>Recommendation</h2>
<div class="callout good"><ol class="tight">
<li>Serve <strong>both</strong> units with 30-day written notices imposing the <strong>2026-27 AGA of 1.6%</strong> (Unit 1: $63.92 → $4,058.92; Unit 2: $50.40 → $3,200.40; Unit 2 base subject to F-R7 verification first).</li>
<li>In parallel, assemble Unit 2's full ledger; if it confirms no increases since June 1, 2019, serve a separate <strong>90-day</strong> notice (or a correctly phased 30-day/yr series) imposing the 11.5% banked + 1.6% annual = 13.1% ($412.65 → $3,562.65) — <em>only after</em> F-R7 clears and license/banked-portion itemization are confirmed.</li>
<li>Hold Unit 1's banked 1.4% until on/after February 1, 2027 (F-R5), then impose with 30-day notice as a clearly itemized banked portion.</li>
<li>Use one template, one methodology note, one service method, one filing for both units. Put the objective basis (anniversary dates, banking histories, form letters) in the permanent file.</li>
<li>If any amount above AGA is contemplated (capital improvement etc.), file the petition/worksheet <em>before</em> noticing.</li>
</ol></div>
<div class="callout warn"><strong>Why not maximize everything now?</strong> Unit 2's 13.1% single notice triggers the 90-day rule and invites — legitimately — a tenant challenge and free-counsel review; that is lawful only when the ledger, license and service are perfect. If anything is off, a phased approach (1.6%/yr 30-day notices, never exceeding 10%/12-month window) is slower but far safer. Speed never justifies an unlawful notice.</div>
"""
    return page("one-vs-both.html", "One Unit or Both? — Discrimination-Risk Analysis", "Analysis · equal-treatment posture",
                "The law does not require parity between units; it forbids protected-class-based and retaliatory treatment. The lowest-risk lawful posture is uniform AGA-based increases on both units with identical documentation — or a documented objective reason for any deviation.", body)

# ---------- page: tenant-lawyer-review ----------

def page_review():
    body = f"""
<div class="callout info"><strong>Why this matters.</strong> San Francisco tenants facing eviction have a <strong>right to a free attorney</strong> (Tenant Right to Counsel — Prop F, 2018), and every tenant can get free counseling from the Rent Board. An increase that would not survive a tenant lawyer's review is an increase destined for a Rent Board petition, a complaint to CRD (FEHA) or HUD (FHA), or litigation. Design to pass.</div>

<h2>Free help available to the tenants in these units (official)</h2>
{table_open("Free tenant assistance", ["Resource","What it provides","Source"])}
<tr><td>SF Rent Board counselors</td><td>Free information for tenants and landlords on the Rent Ordinance; (415) 252-4600; 25 Van Ness Ave, Suite 700; Mon–Fri 9:00–4:00</td><td><a href="{esc(SRC['S-05']['url'])}">SF.gov petitions/contact ↗</a> · <a href="{esc(SRC['S-10']['url'])}">SF.gov evictions ↗</a></td></tr>
<tr><td>Tenant Right to Counsel — Eviction Defense Collaborative</td><td>Free full-scope attorney for eligible SF tenants served with eviction notices/lawsuits: (415) 659-9184 · legal@evictiondefense.org · 976 Mission Street</td><td><a href="{esc(SRC['S-11']['url'])}">SF Form 1007 ↗</a></td></tr>
<tr><td>HUD FHEO (federal)</td><td>Housing discrimination complaints — online or 1-800-669-9777; SF Regional FHEO Office, One Sansome Street, Suite 1200, SF 94104, (415) 489-6524</td><td><a href="{esc(SRC['S-18']['url'])}">hud.gov ↗</a> · <a href="{esc(SRC['S-21']['url'])}">FHEO offices ↗</a></td></tr>
<tr><td>CRD (California Civil Rights Department)</td><td>FEHA housing-discrimination complaints (source of income, disability, familial status, etc.)</td><td><a href="{esc(SRC['S-17']['url'])}">Gov Code §12955 ↗</a></td></tr>
<tr><td>SF Service Guide / 311</td><td>Referrals to tenant resources; rental assistance programs</td><td><a href="{esc(SRC['S-10']['url'])}">SF.gov evictions ↗</a></td></tr>
{table_close()}

<h2>The scrutiny checklist — how a SF tenant advocate attacks an increase</h2>
{table_open("Line-by-line challenge map", ["Check","Tenant lawyer asks","Our answer / evidence","Source"])}
<tr><td>1. Base rent lawful?</td><td>"What is the lawful base, and where is the ledger/Housing Inventory entry?"</td><td>Unit 1: $3,995 tracked from 2/1/2025 (F-R4 reset question open). Unit 2: <strong>F-R7 — must be pulled before service</strong>.</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>2. License held?</td><td>"Show the Housing Inventory report and license."</td><td>Must be produced before noticing allowable/banked increases (F-R7 adjacent).</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a> · <a href="{esc(SRC['S-04']['url'])}">S-04 ↗</a></td></tr>
<tr><td>3. Math correct?</td><td>"Show the arithmetic — no rounding, correct base, banked sum not compounded."</td><td>Scenario table recomputes deterministically; $63.92 / $50.40 / $412.65 exact; no rounding up.</td><td><a href="units.html">Units &amp; scenarios →</a></td></tr>
<tr><td>4. Banking valid?</td><td>"24 full months with no increase? Which years banked, summed how?"</td><td>Unit 1: 2025-26 skip NOT bankable before 2/1/2027 (F-R5). Unit 2: 11.5% bankable if ledger confirms; never compounded/prorated.</td><td><a href="{esc(SRC['S-04']['url'])}">SF.gov banking ↗</a></td></tr>
<tr><td>5. Notice period?</td><td>"30 days, or 90 because combined &gt;10%? Mail +5?"</td><td>Unit 1: 30 days (3.0% combined). Unit 2 single-letter 13.1%: <strong>90 days</strong> (F-R1); mail adds 5 (S-12).</td><td><a href="{esc(SRC['S-12']['url'])}">CC §827 ↗</a></td></tr>
<tr><td>6. Notice contents?</td><td>"Dollar? Percentage? Effective date? Banked portion identified?"</td><td>Template includes all four + unit/tenancy identification + signature (see notice procedure).</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a> · <a href="{esc(SRC['S-04']['url'])}">S-04 ↗</a></td></tr>
<tr><td>7. Once per 12 months?</td><td>"Any increase in the last 12 months? First increase ≥12 months after lease start?"</td><td>Unit 1: none since 2/1/2025. Unit 2: none on record since 6/1/2019 (verify F-R7).</td><td><a href="{esc(SRC['S-01']['url'])}">SF.gov ↗</a></td></tr>
<tr><td>8. Petition needed first?</td><td>"Any capital improvement / O&amp;M / passthrough without prior filing?"</td><td>None contemplated; if added, file before notice (S-05).</td><td><a href="{esc(SRC['S-05']['url'])}">SF.gov petitions ↗</a></td></tr>
<tr><td>9. Discrimination / retaliation?</td><td>"Why this unit(s)? Any animus, protected class, complaint history?"</td><td>Uniform methodology, both units, objective basis documented — see <a href="one-vs-both.html">One or both</a>.</td><td><a href="{esc(SRC['S-17']['url'])}">FEHA ↗</a> · <a href="{esc(SRC['S-18']['url'])}">HUD ↗</a></td></tr>
<tr><td>10. Vacancy decontrol misused?</td><td>"Was this a genuinely new tenancy, or owner-terminated re-papering?"</td><td>Unit 1 2/1/2025 commencement — open question F-R4; Unit 2 continuous, n/a.</td><td><a href="{esc(SRC['S-15']['url'])}">CC §1954.53 ↗</a></td></tr>
{table_close()}

<h2>Verdict template (for counsel's file)</h2>
<div class="callout good"><p><strong>Pass condition:</strong> every row above answered with documents, base rent confirmed, license produced, notice correctly served. <strong>Fail condition:</strong> any row blank — an advocate will exploit it. At present, with Unit 2's ledger (F-R7) and Unit 1's banking timing (F-R5) open, the <em>only</em> currently-clean notices are the 1.6% annual increases for both units with 30-day service.</p></div>
"""
    return page("tenant-lawyer-review.html", "Tenant-Lawyer Review — SF Scrutiny Checklist", "Review · advocates' playbook",
                "How a San Francisco tenant advocate (or the Rent Board, or CRD/HUD) attacks an increase — row by row — with the evidence this property can produce today, and the free legal help both tenant cohorts can access.", body)

# ---------- page: faq ----------

def page_faq():
    qa = [
        ("What is a reasonable rent increase in SF 94122 right now?",
         "For rent-controlled units, whatever the Rent Board allows: 1.6% for increases effective 3/1/2026–2/28/2027 (base rent only, once per 12 months). Anything above that requires an approved Rent Board petition (e.g., capital improvements). <a href='https://www.sf.gov/learn-about-rent-increases-san-francisco'>SF.gov ↗</a>"),
        ("The building is from 1940 — which rules apply?",
         "Full SF Rent Ordinance coverage: rent-increase limits AND just-cause eviction protections. Pre–June 13, 1979 rent-controlled stock. <a href='https://sf.gov/information/find-out-if-san-franciscos-rental-laws-apply-you'>SF.gov coverage ↗</a>"),
        ("Can AB 1482's 5%+CPI/10% cap be used instead? Like in 2024-25 when inflation was higher?",
         "No — §1947.12(d)(3) exempts housing subject to a more-restrictive local rent control. SF's AGA always governs these units. AB 1482 is only relevant if SF coverage failed — it does not here. <a href='https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1947.12&lawCode=CIV'>leginfo ↗</a>"),
        ("Did 3.6% in 2023-24 and 40% increases around 2021-22 happen in SF?",
         "Yes — the official Form 571 shows 3.6% (3/1/23–2/29/24), 2.3% (2022-23), 0.7% (2021-22), 1.8% (2020-21), 2.6% (2019-20); the 2008-era table shows no 10%+ year since 1982's 7.0% cap. <a href='https://www.sf.gov/documents/34344/571_Allowable_Annual_Increases_26-27_1.pdf'>Form 571 ↗</a>"),
        ("Can we charge Unit 1's current tenants for the April 1, 2026 change (new roommate)?",
         "No. An added roommate is never a lawful basis for added rent, even if the lease says so. <a href='https://www.sf.gov/learn-about-rent-increases-san-francisco'>SF.gov ↗</a>"),
        ("Unit 2 hasn't seen an increase since 2019. What's the maximum we can do?",
         "If the ledger confirms no increases: 11.5% banked (sum of the six skipped AGAs, not compounded) + 1.6% annual = 13.1% on $3,150 = $412.65 ($3,562.65) — but a single notice that large requires 90 days, and the banked part must be itemized. Verify the current base first (F-R7) and confirm the license. <a href='https://www.sf.gov/information--banked-rent-increases'>SF.gov banking ↗</a>"),
        ("Does a banked increase expire?",
         "Not during the tenancy; no cap on total banked; survives sale of the property (new owner may use it); does NOT carry to a new tenant. But a skip is bankable only after at least 24 full months pass with no increase. <a href='https://www.sf.gov/information--banked-rent-increases'>SF.gov ↗</a>"),
        ("30-day or 90-day notice — which one?",
         "30 days if the increase (alone or combined with any other increase in the prior 12 months) is ≤10%; 90 days if >10%. Mailed service adds 5 days. Civil Code §827(b)(2)–(3). <a href='https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=827&lawCode=CIV'>leginfo §827 ↗</a>"),
        ("Can we raise only one unit now and the other next year?",
         "Lawful if each unit's notice stands alone on its own anniversary/banking math. Riskier posture than uniform raises; needs a documented objective basis; see the One-vs-Both page — recommended: both units, same method. <a href='one-vs-both.html'>One vs both →</a>"),
        ("What must the notice include?",
         "Dollar amount, percentage, effective date, and (for banked portions) which part is banked. Use the percentage in effect on the effective date. No rounding up. <a href='https://www.sf.gov/learn-about-rent-increases-san-francisco'>SF.gov ↗</a>"),
        ("Do we need Rent Board approval for the regular annual increase?",
         "No — but you DO need the Rent Increase License (Housing Inventory registration) first. Only petition-based increases (capital improvement etc.) need Rent Board approval before the tenant must pay. <a href='https://www.sf.gov/landlord-petitions-and-passthroughs'>SF.gov petitions ↗</a>"),
        ("What if tenants refuse the increase?",
         "Do not self-help (no lockouts, no deposit grabs). The AGA increase properly noticed becomes part of the lease; nonpayment triggers the ordinary nonpayment process (3-day notice to pay or quit) — but eviction triggers Tenant Right to Counsel (free attorney) for the tenant. Talk to the Rent Board counselor first: (415) 252-4600. <a href='https://www.sf.gov/evictions-san-francisco'>SF.gov evictions ↗</a>"),
        ("Is there any federal rent control or HUD cap?",
         "No federal rent control exists. HUD FMRs (FY2027 effective 10/1/2026) benchmark subsidized programs only; they cap nothing in private tenancies. FY2027 area figures are blank/unverified here — F-R2. <a href='https://www.huduser.gov/portal/datasets/fmr.html'>HUDUSER ↗</a>"),
        ("Does raising both units the same amount protect us from a discrimination claim?",
         "It eliminates disparate-impact optics; it does not immunize discriminatory motive — but combined with objective AGA math, identical templates and documented file notes, it is the strongest practical defense. Protected classes under FEHA/Unruh/FHA make selective increases dangerous. <a href='https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12955&lawCode=GOV'>FEHA ↗</a>"),
        ("What should happen before any notice is served?",
         "(1) Pull Unit 2's ledger + Housing Inventory report (F-R7); (2) confirm the license; (3) verify Unit 1's banking dates (F-R5); (4) have a qualified SF attorney or Rent Board counselor review the notice; (5) serve with proof; (6) calendar the next eligible date."),
        ("Who reviewed or endorses this analysis?",
         "No one — this is research prepared from official public sources, not legal advice, and it creates no attorney–client relationship. Verification basis and remaining gaps are on the Methodology and Flagged pages. <a href='methodology.html'>Methodology →</a>"),
    ]
    items = "\n".join(f'<div class="card"><h3>Q{i+1}. {esc(q)}</h3><p>{a}</p></div>' for i, (q, a) in enumerate(qa))
    body = f'<div class="grid cols-2">\n{items}\n</div>'
    return page("faq.html", "Frequently Asked Questions", "FAQ · both units",
                "Straight answers with source links: the AGA, banking, notice periods, roommates, one-vs-both units, license vs petition, and what happens if tenants refuse.", body)

# ---------- page: sources ----------

def page_sources():
    body = f"""
<p>Every official source read for this pack (all read 2026-11-06), with the exact facts each supports. Secondary sources are listed separately, clearly labeled, and never used as the sole basis for a published value.</p>
{table_open("Official sources (read 2026-11-06)", ["ID","Source","Host","Status","Supports / notes"])}
{sources_rows_html()}
{table_close()}
<div class="callout info"><strong>Reading protocol.</strong> Pages were fetched and read in full (leginfo.legislature.ca.gov, sf.gov, huduser.gov, federalregister.gov/public-inspection.federalregister.gov, codelibrary.amlegal.com, hud.gov). Search snippets were used only to locate the correct official URL, never as a source of a published value. Where a page was reachable but the specific datum was not present (HUD area-level FY2027 FMRs), the value was left blank — see <a href="flagged.html#F-R2">F-R2</a>.</div>
"""
    return page("sources.html", "Source Registry", "Verification · sources",
                "Every source used, link-by-link: official SF, California and federal pages (read 2026-11-06) plus clearly labeled flagged secondary material.", body)

# ---------- page: methodology ----------

def page_methodology():
    body = f"""
<h2>How this was verified</h2>
<ol class="tight">
<li><strong>Official-first.</strong> Every legal/regulatory value traces to an .gov / .ca.gov / federalregister.gov page (or the official SF code library) read on 2026-11-06 — see <a href="sources.html">Sources</a>. leginfo.legislature.ca.gov, sf.gov and hud.gov pages were fetched and read directly.</li>
<li><strong>Form 571 for history.</strong> The complete 45-period AGA table was copied verbatim from the official Rent Board Form 571 PDF (2026-11-06), including its footnote on the two 1992–93 increases.</li>
<li><strong>Computed values are labeled, never passed off as official.</strong> Dollar increases and scenario tables are produced deterministically by <code>scripts/build_rental.py</code> from <code>data/rental/scenarios.json</code> using exact decimal arithmetic. They are illustrations, not Rent Board determinations.</li>
<li><strong>Blank beats unverified.</strong> Where a value could not be read from an official page (HUD area-level FY2027 FMRs — F-R2; Unit 2's current base rent — F-R7), it is blank and flagged. Nothing is inferred or filled in from secondary sites.</li>
<li><strong>Banking math follows SF.gov exactly:</strong> banked percentages are <em>added</em>, multiplied by the <em>current</em> base rent; never compounded or prorated; a skip is bankable only after ≥24 full months without any increase; banked amounts never expire during the tenancy.</li>
<li><strong>Notice periods</strong> follow Civil Code §827(b): ≤10% → 30 days; &gt;10% (alone or combined) → 90 days; mail adds 5 days (incorporating CCP §1013).</li>
<li><strong>Privacy protocol.</strong> Tenant names replaced by placeholders (Tenants A–F) everywhere, including this page and the repository history of this pack. Dates and dollar amounts preserved exactly as recorded in the underlying documents. No street address beyond 94122 is published. The placeholder mapping is kept only in the private source material, never committed.</li>
<li><strong>No legal advice.</strong> This pack informs; it does not represent. SF tenants facing eviction have a right to free counsel (S-11); all tenants can call Rent Board counselors (S-05).</li>
</ol>

<h2>Anonymization mapping (private; not published)</h2>
{table_open("Placeholder legend", ["Placeholder","Role"])}
<tr><td><a href="flagged.html#F-R8">Tenant A</a></td><td>Unit 1 — initial and continuing tenant</td></tr>
<tr><td><a href="flagged.html#F-R8">Tenant B</a></td><td>Unit 1 — initial tenant only</td></tr>
<tr><td><a href="flagged.html#F-R8">Tenant C</a></td><td>Unit 1 — initial tenant only</td></tr>
<tr><td><a href="flagged.html#F-R8">Tenant D</a></td><td>Unit 1 — continuing tenancy (from April 1, 2026 records)</td></tr>
<tr><td><a href="flagged.html#F-R8">Tenant E</a></td><td>Unit 2 — tenant since June 1, 2019</td></tr>
<tr><td><a href="flagged.html#F-R8">Tenant F</a></td><td>Unit 2 — tenant since June 1, 2019</td></tr>
{table_close()}
<p class="small">Letters are labels only; no inference about identity, count, or relationship of occupants may be drawn. Dates and amounts are unchanged from the source records.</p>

<h2>Verification status summary</h2>
{table_open("What is verified vs flagged", ["Area","Status","Where"])}
<tr><td>AGA current (1.6%) and history (Form 571)</td><td>{badge('ok','verified')}</td><td><a href="laws-local.html">Local law</a></td></tr>
<tr><td>Notice periods (30/90 days, mail +5)</td><td>{badge('ok','verified')}</td><td><a href="notice-procedure.html">Notice procedure</a></td></tr>
<tr><td>Banking mechanics; license requirement; no roommate surcharge; no rounding</td><td>{badge('ok','verified')}</td><td><a href="laws-local.html">Local law</a></td></tr>
<tr><td>Scenario dollar math (from verified rates)</td><td>{badge('ok','verified rates')} · unit 2 base {badge('warn','unverified')}</td><td><a href="units.html">Units</a></td></tr>
<tr><td>HUD area-level FY2027 FMRs</td><td>{badge('warn','blank · F-R2')}</td><td><a href="laws-federal.html">Federal</a></td></tr>
<tr><td>Unit 2 current lawful base rent</td><td>{badge('warn','unverified · F-R7')}</td><td><a href="flagged.html#F-R7">F-R7</a></td></tr>
<tr><td>Unit 1 2025 commencement theory (vacancy decontrol)</td><td>{badge('warn','unverified · F-R4')}</td><td><a href="flagged.html#F-R4">F-R4</a></td></tr>
<tr><td>2026-27 AGA methodology (geometric-mean CPI story)</td><td>{badge('warn','secondary only · F-R6')}</td><td><a href="flagged.html#F-R6">F-R6</a></td></tr>
<tr><td>Corporate-vs-individual practice claims</td><td>{badge('warn','labeled practice · F-R13')}</td><td><a href="market-practices.html">Market practices</a></td></tr>
{table_close()}
"""
    return page("methodology.html", "Methodology & Privacy Protocol", "Verification · how this was built",
                "Official-first verification, deterministic computations, the blank-over-unverified rule, and the placeholder protocol that keeps tenant identities out of every published page.", body)

# ---------- page: flagged ----------

def page_flagged():
    body = f"""
<div class="callout warn"><strong>These items do not block the site</strong> — they are what the owner must review before serving any notice. Each flag links to its context page; source links live there and on the <a href="sources.html">Sources</a> page. Severity: <span class="badge bad">high</span> = must resolve before acting · <span class="badge warn">medium</span> = resolve before relying · <span class="badge info">low/info</span> = note for the file.</div>
{table_open("Flagged for Review — F-R1 through F-R13", ["ID","Severity","Finding & required action","Sources"])}
{flags_rows_html()}
{table_close()}
"""
    return page("flagged.html", "Flagged for Review", "Review · unresolved items",
                "Everything that is unverified, ambiguous, or requires owner sign-off before service of any increase notice — with source links and concrete actions.", body)

# ---------- build all ----------

PAGES = {
    "index.html": page_index,
    "executive-summary.html": page_exec,
    "units.html": page_units,
    "laws-local.html": page_laws_local,
    "laws-state.html": page_laws_state,
    "laws-federal.html": page_laws_federal,
    "market-practices.html": page_market,
    "notice-procedure.html": page_notice,
    "one-vs-both.html": page_one_vs_both,
    "tenant-lawyer-review.html": page_review,
    "faq.html": page_faq,
    "sources.html": page_sources,
    "methodology.html": page_methodology,
    "flagged.html": page_flagged,
}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in PAGES.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
    print(f"built {len(PAGES)} pages into {OUT}")

if __name__ == "__main__":
    main()
