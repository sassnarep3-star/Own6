#!/usr/bin/env python3
"""Deterministic static site builder for the SF Outer Sunset (94122) dashboard.

Reads verified/unverified CSV registers in data/sf_94122/, validates exact
Decimal math and blank-unverified invariants, and writes 6 clean, accessible
HTML pages + styles.css in docs/sf-94122/.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "sf_94122"
OUT_DIR = ROOT / "docs" / "sf-94122"

NAV_ITEMS = [
    ("index.html", "Executive Summary"),
    ("units.html", "Unit 1 & Unit 2 Math"),
    ("corporate-vs-individual.html", "Corporate vs. Individual"),
    ("notice-and-reasons.html", "Notice & Reasons"),
    ("tenant-scrutiny-and-fairness.html", "Lawyer Scrutiny & 1 vs. 2 Units"),
    ("flagged.html", "Flagged for Review"),
]

STYLES_CSS = """\
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --border: #cbd5e1;
  --border-subtle: #e2e8f0;
  --text: #0f172a;
  --muted: #475569;
  --accent: #0f4c81;
  --accent-soft: #e0f2fe;
  --verified-bg: #dcfce7;
  --verified-fg: #166534;
  --unverified-bg: #fef3c7;
  --unverified-fg: #92400e;
  --warn-bg: #fff7ed;
  --warn-border: #fdba74;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
  font-size: 15px;
}

.container {
  max-width: 1220px;
  margin: 0 auto;
  padding: 0 20px;
}

.site-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 18px 0 0;
}

.brand-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px 16px;
  padding-bottom: 12px;
}

.brand-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--accent);
  margin: 0;
}

.brand-meta {
  font-size: 0.84rem;
  color: var(--muted);
  margin: 0;
}

.nav-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  border-top: 1px solid var(--border-subtle);
  padding: 8px 0;
}

.nav-bar a {
  text-decoration: none;
  color: var(--muted);
  font-weight: 600;
  font-size: 0.88rem;
  padding: 6px 11px;
  border-radius: 6px;
}

.nav-bar a:hover {
  background: var(--surface-alt);
  color: var(--text);
}

.nav-bar a.active {
  background: var(--accent);
  color: #ffffff;
}

main {
  padding: 26px 0 44px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--accent);
  margin: 0 0 6px;
}

h1 {
  font-size: 1.72rem;
  line-height: 1.25;
  margin: 0 0 10px;
}

h2 {
  font-size: 1.22rem;
  margin: 30px 0 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

.lead {
  color: var(--muted);
  max-width: 940px;
  margin: 0 0 18px;
}

.banner {
  background: var(--warn-bg);
  border: 1px solid var(--warn-border);
  border-left: 4px solid #ea580c;
  border-radius: 8px;
  padding: 12px 16px;
  margin: 0 0 22px;
  font-size: 0.9rem;
}

.banner strong {
  color: #9a3412;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(245px, 1fr));
  gap: 14px;
  margin: 0 0 24px;
}

.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
}

.kpi-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  font-weight: 700;
  margin: 0 0 4px;
}

.kpi-value {
  font-size: 1.32rem;
  font-weight: 700;
  color: var(--accent);
  margin: 0 0 6px;
}

.kpi-note {
  font-size: 0.85rem;
  color: var(--muted);
  margin: 0;
}

.table-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow-x: auto;
  margin: 0 0 24px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

thead th {
  background: var(--surface-alt);
  color: var(--text);
  font-weight: 700;
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}

tbody td,
tbody th {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: top;
  text-align: left;
}

tbody tr:last-child td,
tbody tr:last-child th {
  border-bottom: none;
}

tbody tr:hover {
  background: #f8fafc;
}

td.num {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

td.empty-cell {
  background: repeating-linear-gradient(
    -45deg,
    #fffbeb,
    #fffbeb 6px,
    #fef3c7 6px,
    #fef3c7 12px
  );
  min-width: 90px;
}

.badge {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  text-transform: lowercase;
  white-space: nowrap;
}

.badge-verified {
  background: var(--verified-bg);
  color: var(--verified-fg);
}

.badge-unverified {
  background: var(--unverified-bg);
  color: var(--unverified-fg);
}

a {
  color: var(--accent);
}

a.src-link {
  font-weight: 600;
  white-space: nowrap;
}

.site-footer {
  border-top: 1px solid var(--border);
  background: var(--surface);
  padding: 18px 0;
  font-size: 0.84rem;
  color: var(--muted);
}
"""


def load_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for idx, row in enumerate(rows, 1):
        status = row.get("verification_status", "")
        val = row.get("verified_value", "")
        url = row.get("official_source_url", "")
        if status not in {"verified", "unverified"}:
            raise ValueError(f"{filename} row {idx}: invalid verification_status={status!r}")
        if status == "unverified" and val != "":
            raise ValueError(f"{filename} row {idx}: unverified row must have empty verified_value, got {val!r}")
        if status == "verified" and val.strip() == "":
            raise ValueError(f"{filename} row {idx}: verified row must have non-empty verified_value")
        if not url.startswith("https://"):
            raise ValueError(f"{filename} row {idx}: missing https official_source_url")
    return rows


def verify_scenario_math(scenarios: list[dict[str, str]], rates: list[dict[str, str]]) -> None:
    # Verify Unit 2's 6 banked years (2020-21 through 2025-26) sum to 11.5% and +1.6% = 13.1%
    rate_map = {r["id"]: Decimal(r["verified_value"].rstrip("%")) for r in rates if r["id"] in {"R-02", "R-03", "R-04", "R-05", "R-06", "R-07", "R-08"}}
    banked_u2 = rate_map["R-02"] + rate_map["R-03"] + rate_map["R-04"] + rate_map["R-05"] + rate_map["R-06"] + rate_map["R-07"]
    if banked_u2 != Decimal("11.5"):
        raise ValueError(f"Expected Unit 2 2020-2025 banked sum 11.5%, got {banked_u2}%")
    if banked_u2 + rate_map["R-08"] != Decimal("13.1"):
        raise ValueError("Expected Unit 2 total banked + current = 13.1%")

    for row in scenarios:
        if row["verification_status"] == "unverified":
            for col in ("base_rent_usd", "rate_pct", "monthly_increase_usd", "new_monthly_rent_usd", "verified_value"):
                if row[col] != "":
                    raise ValueError(f"{row['id']}: unverified scenario column {col} must be blank")
            continue
        base = Decimal(row["base_rent_usd"])
        pct = Decimal(row["rate_pct"].rstrip("%"))
        inc = Decimal(row["monthly_increase_usd"])
        new_rent = Decimal(row["new_monthly_rent_usd"])
        expected_inc = (base * pct) / Decimal("100")
        if expected_inc != inc:
            raise ValueError(f"{row['id']}: expected increase {expected_inc}, got {inc}")
        if base + inc != new_rent:
            raise ValueError(f"{row['id']}: expected new rent {base + inc}, got {new_rent}")


def badge_html(status: str) -> str:
    cls = "badge-verified" if status == "verified" else "badge-unverified"
    return f'<span class="badge {cls}">{escape(status)}</span>'


def value_cell_html(value: str, status: str, numeric: bool = False) -> str:
    if status == "unverified":
        return '<td class="empty-cell"></td>'
    cls = ' class="num"' if numeric else ""
    return f"<td{cls}>{escape(value)}</td>"


def source_cell_html(label: str, url: str) -> str:
    return f'<td><a class="src-link" href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)} &#8599;</a></td>'


def render_table(headers: list[str], body_rows: list[str]) -> str:
    th_html = "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + th_html
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div>"
    )


def page_shell(active_file: str, eyebrow: str, h1_title: str, lead: str, body_html: str) -> str:
    nav_links = []
    for href, label in NAV_ITEMS:
        cls = ' class="active" aria-current="page"' if href == active_file else ""
        nav_links.append(f'<a href="{escape(href, quote=True)}"{cls}>{escape(label)}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(h1_title)} | SF 94122 Rent-Control Compliance</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="brand-row">
        <p class="brand-title">SF Outer Sunset (94122) Rent-Control Compliance Dashboard</p>
        <p class="brand-meta">Snapshot: November 6, 2026 &middot; Zero PII / Anonymized Placeholders Only</p>
      </div>
      <nav class="nav-bar" aria-label="Dashboard sections">
        {"".join(nav_links)}
      </nav>
    </div>
  </header>
  <main class="container">
    <p class="eyebrow">{escape(eyebrow)}</p>
    <h1>{escape(h1_title)}</h1>
    <p class="lead">{escape(lead)}</p>
    <div class="banner">
      <strong>Privacy &amp; Zero-Inference Notice:</strong> All tenant names and initials are excluded and replaced with anonymized placeholders (<code>Tenant 1A</code>&ndash;<code>Tenant 1D</code>, <code>Tenant 2A</code>&ndash;<code>Tenant 2B</code>). Every table row links directly to an official primary source. Unconfirmed property, license, lease-term, ledger, and post-February 28, 2027 rate fields are intentionally left blank and flagged <code>unverified</code>. Informational research only &mdash; not legal advice.
    </div>
    {body_html}
  </main>
  <footer class="site-footer">
    <div class="container">
      San Francisco Outer Sunset (ZIP 94122) Rent-Controlled Two-Unit Research &middot; Built deterministically from verified official sources (<code>sf.gov</code>, <code>leginfo.legislature.ca.gov</code>, <code>oag.ca.gov</code>, <code>calcivilrights.ca.gov</code>, <code>justice.gov</code>, <code>sec.gov</code>, <code>census.gov</code>, <code>huduser.gov</code>) &middot; Informational only, not legal advice.
    </div>
  </footer>
</body>
</html>
"""


def build_index_page(
    benchmarks: list[dict[str, str]],
    scenarios: list[dict[str, str]],
    flagged: list[dict[str, str]],
) -> str:
    unverified_count = sum(1 for r in flagged if r["verification_status"] == "unverified")
    kpis = f"""
    <section class="kpi-grid" aria-label="Key findings">
      <article class="kpi-card">
        <p class="kpi-label">SF Annual Allowable Rate (3/1/26&ndash;2/28/27)</p>
        <p class="kpi-value">1.6% Base Rent</p>
        <p class="kpi-note">60% of Bay Area CPI-U (SF Rent Board Form 571). Active Housing Inventory License required before effective date.</p>
      </article>
      <article class="kpi-card">
        <p class="kpi-label">Unit 1 ($3,995 Reported &middot; Feb 2025 / Apr 2026)</p>
        <p class="kpi-value">+$63.92 &rarr; $4,058.92</p>
        <p class="kpi-note">Conditional 1.6% illustration ONLY if month-to-month. Original occupant Tenant 1A blocks market reset; check Apr 1, 2026 lease term first.</p>
      </article>
      <article class="kpi-card">
        <p class="kpi-label">Unit 2 ($3,150 Reported &middot; Jun 2019 Start)</p>
        <p class="kpi-value">+$50.40 &rarr; $3,200.40</p>
        <p class="kpi-note">Recommended 1.6% annual policy once ledger verified; keeps up to 11.5% (2020&ndash;2025) banked without a &gt;10% 90-day shock.</p>
      </article>
      <article class="kpi-card">
        <p class="kpi-label">Fair-Housing &amp; Audit Gate Status</p>
        <p class="kpi-value">Uniform 1.6% Policy</p>
        <p class="kpi-note">Apply identical objective rule to both units as eligible; {unverified_count} record gates remain blank/unverified pending owner file check.</p>
      </article>
    </section>
    """

    exec_rows_data = [
        (
            "Q1. Reasonable & Normal Increase in 94122",
            "SF Admin Code Ch. 37 caps standard annual increases at 1.6% (effective 3/1/26–2/28/27), superseding AB 1482's 8.8%. Conditional 1.6% math is +$63.92/mo ($4,058.92) on Unit 1 and +$50.40/mo ($3,200.40) on Unit 2, strictly after confirming Housing Inventory license and periodic lease status.",
            "1.6% annual cap (3/1/26–2/28/27)",
            "verified",
            "SF.gov — Learn About Rent Increases",
            "https://www.sf.gov/learn-about-rent-increases-san-francisco",
        ),
        (
            "Q2. Corporate REITs vs. Individual SF Owners",
            "Public REITs (AvalonBay/Equity Residential: 4.1%–4.8% renewals on post-1995 exempt stock) automate March 1 portal licensing and exact 12-month 1.6% anniversaries on SF rent-controlled units, whereas small SF owners often skip years and lose $14,742+ refunds (Outer Sunset Appeal AL260003) from unlicensed or defective catch-ups.",
            "Annual licensed cadence vs. informal catch-up risk",
            "verified",
            "SF Rent Board Feb 10 2026 Minutes (AL260003)",
            "https://media.api.sf.gov/documents/m021026.pdf",
        ),
        (
            "Q3. Correct Notice Delivery & Valid Reasons",
            "Serve signed written paper notice personally or by first-class CA mail (+5 days under CCP § 1013): 30/35 days for <=10% or 90/95 days for >10% (email/text invalid per CA AG). Cite routine statutory CPI adjustment under SF Admin Code § 37.3(a)(1); never cite roommate swaps or unpetitioned tax/insurance spikes.",
            "30/35d (<=10%) or 90/95d (>10%) written notice",
            "verified",
            "CA Attorney General — Tenant Rights",
            "https://oag.ca.gov/tenants",
        ),
        (
            "Q4. Passing SF Tenant-Lawyer Strict Review",
            "ZIP 94122 (Sunset) ranks #2 in SF pre-buyout filings (48) and tied #1 in buyouts (25). Free counsel/advocates (HRCSF, BayLegal, EDC) and free Form 516C/518 petitions verify active portal license, zero rounding up, 4.2% deposit interest credits, zero 180-day repair retaliation, and Costa-Hawkins roommate rules.",
            "12-point pre-service compliance audit required",
            "verified",
            "SF.gov — Tenant & Landlord Resources",
            "https://www.sf.gov/tenant-and-landlord-resources",
        ),
        (
            "Q5. Raise One Unit vs. Raise Both Units?",
            "Adopt a written, uniform building-wide 1.6% annual AGA policy for BOTH units on each unit's objective eligible date. If Unit 1 is locked in an April 1, 2026 fixed-term lease while Unit 2 is month-to-month, raising Unit 2 now (1.6%) and scheduling Unit 1 upon fixed-term expiry is objective and non-discriminatory.",
            "Uniform building-wide 1.6% policy on eligible dates",
            "verified",
            "CA Civil Rights Dept. — Fair Housing",
            "https://calcivilrights.ca.gov/housing/",
        ),
        (
            "Actual Ready-to-Serve Notice Dollar Amount Today",
            "Intentionally left blank until owner verifies (1) active 2026 Housing Inventory Rent Increase License on portal.sfrb.org, (2) Unit 1 April 1, 2026 fixed-term vs. periodic clause, and (3) Unit 2 complete 2019–2026 rent ledger.",
            "",
            "unverified",
            "SF.gov — Housing Inventory Noncompliance",
            "https://www.sf.gov/notice-of-owner-noncompliance-with-housing-inventory",
        ),
    ]
    exec_rows_html = [
        "<tr>"
        f'<th scope="row">{escape(q)}</th>'
        f"<td>{escape(summary)}</td>"
        f"{value_cell_html(val, st)}"
        f"<td>{badge_html(st)}</td>"
        f"{source_cell_html(lbl, url)}"
        "</tr>"
        for q, summary, val, st, lbl, url in exec_rows_data
    ]

    law_rows_html = []
    bench_rows_html = []
    for r in benchmarks:
        tr = (
            "<tr>"
            f'<th scope="row">{escape(r["metric_or_law"])}</th>'
            f'<td>{escape(r["jurisdiction"])}</td>'
            f'{value_cell_html(r["verified_value"], r["verification_status"])}'
            f'<td>{badge_html(r["verification_status"])}</td>'
            f'<td>{escape(r["relevance_to_94122_units"])}</td>'
            f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
            "</tr>"
        )
        if r["group"] == "Governing Law Hierarchy":
            law_rows_html.append(tr)
        else:
            bench_rows_html.append(tr)

    body = (
        kpis
        + "<h2>Executive Decision Matrix (All 5 Core Questions)</h2>"
        + render_table(["Question / Decision Gate", "Verified Legal & Practical Finding", "Verified Value", "Status", "Official Source"], exec_rows_html)
        + "<h2>Local, State &amp; Federal Governing Law Hierarchy</h2>"
        + render_table(["Statute / Ordinance", "Jurisdiction", "Verified Rule / Cap", "Status", "Application to 94122 Two-Unit Building", "Official Source"], law_rows_html)
        + "<h2>San Francisco &amp; Outer Sunset (ZIP 94122) Official Benchmarks</h2>"
        + render_table(["Benchmark Metric", "Jurisdiction", "Verified Official Value", "Status", "Context for Unit 1 ($3,995) & Unit 2 ($3,150)", "Official Source"], bench_rows_html)
    )
    return page_shell(
        "index.html",
        "Executive Overview · Outer Sunset ZIP 94122",
        "Executive Summary & Governing Law Dashboard",
        "Line-by-line legal, mathematical, and fair-housing analysis for two reported rent-controlled residential units in a 1940 Outer Sunset (94122) building.",
        body,
    )


def build_units_page(
    baseline: list[dict[str, str]],
    rates: list[dict[str, str]],
    scenarios: list[dict[str, str]],
) -> str:
    base_rows = [
        "<tr>"
        f'<td>{escape(r["id"])}</td>'
        f'<th scope="row">{escape(r["subject"])} &mdash; {escape(r["field_label"])}</th>'
        f'<td>{escape(r["reported_context"])}</td>'
        f'{value_cell_html(r["verified_value"], r["verification_status"])}'
        f'<td>{badge_html(r["verification_status"])}</td>'
        f'<td>{escape(r["legal_relevance"])}</td>'
        f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
        "</tr>"
        for r in baseline
    ]

    rate_rows = [
        "<tr>"
        f'<th scope="row">{escape(r["rate_period"])}</th>'
        f'<td>{escape(r["rate_category"])}</td>'
        f'{value_cell_html(r["verified_value"], r["verification_status"], numeric=True)}'
        f'<td>{badge_html(r["verification_status"])}</td>'
        f'<td>{escape(r["calculation_basis"])}</td>'
        f'<td>{escape(r["unit_application_notes"])}</td>'
        f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
        "</tr>"
        for r in rates
    ]

    scen_rows = []
    for r in scenarios:
        st = r["verification_status"]
        base_disp = f'${r["base_rent_usd"]}' if r["base_rent_usd"] else ""
        inc_disp = f'+${r["monthly_increase_usd"]}' if r["monthly_increase_usd"] else ""
        new_disp = f'${r["new_monthly_rent_usd"]}' if r["new_monthly_rent_usd"] else ""
        scen_rows.append(
            "<tr>"
            f'<td>{escape(r["unit"])}</td>'
            f'<th scope="row">{escape(r["scenario_name"])}</th>'
            f'{value_cell_html(base_disp, st, numeric=True)}'
            f'{value_cell_html(r["rate_pct"], st, numeric=True)}'
            f'{value_cell_html(inc_disp, st, numeric=True)}'
            f'{value_cell_html(new_disp, st, numeric=True)}'
            f'<td>{badge_html(st)}</td>'
            f'<td>{escape(r["notice_period_required"])}</td>'
            f'<td>{escape(r["eligibility_and_lawyer_notes"])}</td>'
            f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
            "</tr>"
        )

    body = (
        "<h2>1. Conditional Rent Increase &amp; Banking Scenarios (Unit 1 &amp; Unit 2)</h2>"
        + render_table(
            ["Unit", "Scenario", "Base Rent", "Rate", "Monthly Increase", "New Base Rent", "Status", "Statutory Notice", "Legal Gate & Trade-Off Analysis", "Official Source"],
            scen_rows,
        )
        + "<h2>2. Official SF Rent Board Form 571 Rate Schedule (2019&ndash;2028) &amp; Related Rates</h2>"
        + render_table(
            ["Effective Window", "Rate Type", "Verified Rate / Fee", "Status", "Statutory Formula", "Application to Unit 1 & Unit 2", "Official Source"],
            rate_rows,
        )
        + "<h2>3. Property &amp; Anonymized Unit Baseline Facts (Verified vs. Unverified Gates)</h2>"
        + render_table(
            ["ID", "Subject & Field", "Owner-Reported Context", "Verified Value", "Status", "Legal Significance", "Official Source"],
            base_rows,
        )
    )
    return page_shell(
        "units.html",
        "Unit-Level Math · Banking · Roommate Continuity",
        "Unit 1 ($3,995) & Unit 2 ($3,150) Rent Increase Calculations",
        "Exact unrounded base-rent calculations, 2019–2027 Form 571 banking math, Costa-Hawkins / Rule 6.14 roommate rules, and blank unverified record gates.",
        body,
    )


def build_corp_page(corp_rows: list[dict[str, str]]) -> str:
    rows_html = [
        "<tr>"
        f'<td>{escape(r["owner_segment"])}</td>'
        f'<th scope="row">{escape(r["dimension"])}</th>'
        f'<td>{escape(r["verified_practice_summary"])}</td>'
        f'{value_cell_html(r["verified_value"], r["verification_status"])}'
        f'<td>{badge_html(r["verification_status"])}</td>'
        f'<td>{escape(r["compliance_takeaway_for_94122_owner"])}</td>'
        f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
        "</tr>"
        for r in corp_rows
    ]
    body = (
        "<h2>Institutional Real Estate Corporations (REITs) vs. Individual SF Property Owners</h2>"
        + render_table(
            ["Owner Segment", "Practice Dimension", "Verified Evidence from Official Filings & Hearings", "Verified Benchmark / Ruling", "Status", "Practical Takeaway for 94122 Duplex Owner", "Official Source"],
            rows_html,
        )
    )
    return page_shell(
        "corporate-vs-individual.html",
        "Comparative Practice · SEC Filings · Rent Board Appeals",
        "How Large Real Estate Corporations vs. Individual Owners Handle SF Rent Increases",
        "Comparison grounded strictly in July 2026 public REIT SEC filings, U.S. DOJ / CA AG enforcement, SF Admin Code § 37.10C, and 2025–2026 SF Rent Board Commission appeal minutes.",
        body,
    )


def build_notice_page(notice_rows: list[dict[str, str]]) -> str:
    step_rows = []
    reason_rows = []
    for r in notice_rows:
        tr = (
            "<tr>"
            f'<td>{escape(r["category"])}</td>'
            f'<th scope="row">{escape(r["step_or_reason"])}</th>'
            f'<td>{escape(r["rule_requirement"])}</td>'
            f'{value_cell_html(r["verified_value"], r["verification_status"])}'
            f'<td>{badge_html(r["verification_status"])}</td>'
            f'<td>{escape(r["lawyer_safe_guidance"])}</td>'
            f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
            "</tr>"
        )
        if "Reason" in r["category"]:
            reason_rows.append(tr)
        else:
            step_rows.append(tr)

    body = (
        "<h2>1. Mandatory Pre-Service &amp; Written Notice Delivery Protocol (Cal. Civ. Code &sect; 827)</h2>"
        + render_table(
            ["Stage", "Step", "Statutory / Rent Board Rule", "Verified Standard", "Status", "Execution Guidance", "Official Source"],
            step_rows,
        )
        + "<h2>2. Lawful &amp; Reasonable Reasons vs. Impermissible Reasons</h2>"
        + render_table(
            ["Classification", "Stated Reason / Mechanism", "Legal Standard", "Verified Rule", "Status", "Tenant-Lawyer-Safe Practice", "Official Source"],
            reason_rows,
        )
    )
    return page_shell(
        "notice-and-reasons.html",
        "Statutory Service · Lead Times · Permissible Reasons",
        "Correct Legal Method to Inform Tenants & Reasonable Reasons for Increase",
        "Exact California Civil Code § 827 + CCP § 1013 service requirements, mandatory SF Rent Board disclosures, and lawful vs. retaliatory/prohibited justifications.",
        body,
    )


def build_scrutiny_page(scrutiny_rows: list[dict[str, str]]) -> str:
    audit_rows = []
    fair_rows = []
    for r in scrutiny_rows:
        tr = (
            "<tr>"
            f'<th scope="row">{escape(r["audit_item_or_option"])}</th>'
            f'<td>{escape(r["legal_authority"])}</td>'
            f'{value_cell_html(r["verified_value"], r["verification_status"])}'
            f'<td>{badge_html(r["verification_status"])}</td>'
            f'<td>{escape(r["scrutiny_analysis_and_recommendation"])}</td>'
            f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
            "</tr>"
        )
        if r["section"] == "Tenant-Lawyer 12-Point Scrutiny":
            audit_rows.append(tr)
        else:
            fair_rows.append(tr)

    body = (
        "<h2>1. Raising One Unit vs. Raising Both Units &mdash; Fair-Housing &amp; Anti-Retaliation Matrix</h2>"
        + render_table(
            ["Policy Option / Fair-Housing Dimension", "Governing Statues", "Verified Legal Posture", "Status", "Discrimination & Inquiry Risk Analysis", "Official Source"],
            fair_rows,
        )
        + "<h2>2. SF Free Tenant-Lawyer &amp; Rent Board ALJ Strict Scrutiny Checklist</h2>"
        + render_table(
            ["Tenant-Advocate Audit Point", "Governing Authority", "Verified Standard", "Status", "How to Pass Strict Legal Review", "Official Source"],
            audit_rows,
        )
    )
    return page_shell(
        "tenant-scrutiny-and-fairness.html",
        "Advocate Review · FHA / FEHA / SF Police Code § 3304",
        "SF Tenant-Lawyer Strict Scrutiny & Raising One Unit vs. Both Units",
        "How SF free tenant legal services and Rent Board ALJs audit rent increase notices in 94122, and why a uniform, objective building-wide 1.6% policy best protects against discrimination inquiries.",
        body,
    )


def build_flagged_page(flagged_rows: list[dict[str, str]]) -> str:
    unv_rows = []
    irr_rows = []
    for r in flagged_rows:
        tr = (
            "<tr>"
            f'<td>{escape(r["id"])}</td>'
            f'<td>{escape(r["flag_type"])}</td>'
            f'<th scope="row">{escape(r["scope_or_file"])}</th>'
            f'<td>{escape(r["item_summary"])}</td>'
            f'{value_cell_html(r["verified_value"], r["verification_status"])}'
            f'<td>{badge_html(r["verification_status"])}</td>'
            f'<td>{escape(r["action_required"])}</td>'
            f'{source_cell_html(r["official_source_label"], r["official_source_url"])}'
            "</tr>"
        )
        if r["verification_status"] == "unverified":
            unv_rows.append(tr)
        else:
            irr_rows.append(tr)

    body = (
        "<h2>1. Unverified Property, Lease, Ledger &amp; Future-Rate Gates (Values Left Blank)</h2>"
        + render_table(
            ["ID", "Flag Category", "Scope", "Unconfirmed Item", "Verified Value (Blank)", "Status", "Required Verification Before Acting", "Official Source"],
            unv_rows,
        )
        + "<h2>2. Official-Source Typos &amp; Line-by-Line Repository Audit Irregularities</h2>"
        + render_table(
            ["ID", "Finding Type", "Audited Source / Repo Path", "Irregularity Details", "Verified Resolution", "Status", "Coordination / Review Action", "Official Source"],
            irr_rows,
        )
    )
    return page_shell(
        "flagged.html",
        "Audit Register · Zero Hallucinations · Manual Review Links",
        "Flagged for Review: Unverified Facts & Repo/Source Irregularities",
        "Every unconfirmed factual input is left blank and flagged unverified, alongside official SF.gov prose typos and broken HTTP-404 links identified during our line-by-line repository review.",
        body,
    )


def generate_all() -> dict[str, str]:
    baseline = load_csv("property_units_baseline.csv")
    rates = load_csv("historical_aga_rates.csv")
    scenarios = load_csv("unit_increase_scenarios.csv")
    corp = load_csv("corporate_vs_individual.csv")
    notice = load_csv("notice_and_reasons.csv")
    scrutiny = load_csv("scrutiny_and_fair_housing.csv")
    benchmarks = load_csv("benchmarks_and_laws.csv")
    flagged = load_csv("flagged_for_review.csv")

    verify_scenario_math(scenarios, rates)

    return {
        "styles.css": STYLES_CSS,
        "index.html": build_index_page(benchmarks, scenarios, flagged),
        "units.html": build_units_page(baseline, rates, scenarios),
        "corporate-vs-individual.html": build_corp_page(corp),
        "notice-and-reasons.html": build_notice_page(notice),
        "tenant-scrutiny-and-fairness.html": build_scrutiny_page(scrutiny),
        "flagged.html": build_flagged_page(flagged),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or check docs/sf-94122/ static pages.")
    parser.add_argument("--check", action="store_true", help="Verify generated files match disk without writing.")
    args = parser.parse_args()

    outputs = generate_all()
    if args.check:
        mismatches = []
        for name, expected in outputs.items():
            target = OUT_DIR / name
            if not target.exists() or target.read_text(encoding="utf-8") != expected:
                mismatches.append(name)
        if mismatches:
            print(f"FAIL: stale or missing files in docs/sf-94122/: {mismatches}")
            return 1
        print(f"OK: docs/sf-94122/ matches deterministic build ({len(outputs) - 1} HTML pages + styles.css).")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        (OUT_DIR / name).write_text(content, encoding="utf-8")
    print(f"BUILT: {len(outputs) - 1} HTML pages + styles.css in {OUT_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
