#!/usr/bin/env python3
"""Deterministic builder for the 11-page zero-input NFL Origination dashboard (`docs/nfl-origination/`).

Reads verified CSV datasets from `data/nfl_origination/` and computes exact mathematical
formula verification tables via pure-stdlib `src/nfl_origination/`.
Never scrapes, never infers unconfirmed empirical values, and renders every blank CSV
field as `<td class="empty"></td>` styled strictly via CSS pseudo-element badges.
"""
from __future__ import annotations

import argparse
import csv
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from nfl_origination import (  # noqa: E402
    NFLGameInput,
    NFLRegimeParams,
    bivariate_normal_joint_prob,
    originate_nfl_game,
    prob_to_fair_american,
    push_aware_ev,
)

DATA_DIR = ROOT / "data" / "nfl_origination"
OUT_DIR = ROOT / "docs" / "nfl-origination"
ASSETS_DIR = OUT_DIR / "assets"

NAV_PAGES: tuple[tuple[str, str, str], ...] = (
    ("index.html", "Overview & Wk 10 Slate", " NFL Week 10 Dashboard & 32-Club Standings"),
    ("executive-summary.html", "Executive Summary", "Executive Summary & 28-Source Verification Register"),
    ("requirements.html", "Requirements", "Itemized Requirements Collection, Organization & Analysis"),
    ("suggestions.html", "Suggestions (Review)", "Site & Decision-Making Improvement Suggestions"),
    ("decision-qa.html", "Decision Q&A", "Pre-Decision Q&A, Missing Data & Discovery Paths"),
    ("strategies-leaderboard.html", "Origination & Leaderboard", "Line Origination, 10 Signal Strategies & Skill Leaderboard"),
    ("validation-gates.html", "Validation & Luck", "12 Validation Gates & Luck-Removal Architecture"),
    ("correlations.html", "Correlations & Combos", "Parlay / SGP / Prop-Combo Correlations & Copula Math"),
    ("injuries-depth.html", "Injuries & 1–4 Depth", "Week 10 Injuries & 1st-to-4th String Depth Deficiencies"),
    ("repo-audit.html", "Repo Audit", "Line-by-Line Repository Review & Code Audit"),
    ("flagged.html", "Flagged for Review", "Flagged Irregularities & Unverified Blank Ledger"),
)

STYLESHEET = """/* Clean, high-contrast, zero-input NFL Origination Dashboard stylesheet */
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --ink: #0f172a;
  --muted: #475569;
  --border: #cbd5e1;
  --accent: #1e3a8a;
  --accent-soft: #dbeafe;
  --ok-bg: #dcfce7;
  --ok-ink: #166534;
  --warn-bg: #fef3c7;
  --warn-ink: #92400e;
  --bad-bg: #fee2e2;
  --bad-ink: #991b1b;
  --info-bg: #e0f2fe;
  --info-ink: #075985;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.55;
  font-size: 15px;
}
a { color: #1d4ed8; text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  background: #0f172a;
  color: #f8fafc;
  padding: 1rem 1.25rem 0.75rem;
  border-bottom: 3px solid #2563eb;
}
.topbar-inner, .container {
  max-width: 1380px;
  margin: 0 auto;
}
.brand-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.brand-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #ffffff;
}
.brand-sub {
  font-size: 0.82rem;
  color: #cbd5e1;
}
.nav-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  padding-bottom: 0.2rem;
}
.nav-tabs a {
  color: #e2e8f0;
  background: #1e293b;
  padding: 0.38rem 0.68rem;
  border-radius: 6px;
  font-size: 0.81rem;
  font-weight: 600;
  border: 1px solid #334155;
}
.nav-tabs a:hover {
  background: #334155;
  text-decoration: none;
}
.nav-tabs a.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #60a5fa;
}
.container {
  padding: 1.35rem 1.25rem 2.5rem;
}
.gate-banner {
  background: #fffbeb;
  border: 1px solid #f59e0b;
  border-left: 5px solid #d97706;
  border-radius: 8px;
  padding: 0.85rem 1rem;
  margin-bottom: 1.2rem;
  font-size: 0.9rem;
  color: #78350f;
}
.gate-banner strong { color: #92400e; }
.hero {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.2rem 1.35rem;
  margin-bottom: 1.2rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.hero h1 {
  margin: 0 0 0.45rem;
  font-size: 1.55rem;
  color: var(--ink);
}
.hero p {
  margin: 0.3rem 0;
  color: var(--muted);
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(205px, 1fr));
  gap: 0.85rem;
  margin-bottom: 1.35rem;
}
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 0.9rem 1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}
.kpi-label {
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.kpi-value {
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--accent);
  margin: 0.2rem 0;
}
.kpi-note {
  font-size: 0.8rem;
  color: var(--muted);
}
.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 1.15rem 1.25rem;
  margin-bottom: 1.35rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.section-card h2 {
  margin: 0 0 0.45rem;
  font-size: 1.2rem;
  color: var(--ink);
}
.section-card p.lead {
  margin: 0 0 0.85rem;
  color: var(--muted);
  font-size: 0.92rem;
}
.callout-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
  gap: 0.9rem;
  margin-top: 0.75rem;
}
.callout {
  background: var(--surface-alt);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.85rem 1rem;
}
.callout h3 {
  margin: 0 0 0.35rem;
  font-size: 0.98rem;
  color: var(--accent);
}
.callout p, .callout ul {
  margin: 0.25rem 0;
  font-size: 0.88rem;
  color: var(--ink);
}
.callout ul { padding-left: 1.15rem; }
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--border);
  border-radius: 8px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
  background: var(--surface);
}
thead th {
  background: #f1f5f9;
  color: #0f172a;
  font-weight: 700;
  text-align: left;
  padding: 0.6rem 0.65rem;
  border-bottom: 2px solid var(--border);
  white-space: nowrap;
}
tbody td {
  padding: 0.55rem 0.65rem;
  border-bottom: 1px solid #e2e8f0;
  vertical-align: top;
}
tbody tr:nth-child(even) { background: #f8fafc; }
tbody tr:hover { background: #eff6ff; }
td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.empty {
  background: #fffbeb;
  text-align: center;
  min-width: 105px;
}
td.empty::after {
  content: "blank (unverified)";
  display: inline-block;
  font-size: 0.73rem;
  font-style: italic;
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 4px;
  padding: 0.1rem 0.42rem;
}
.badge {
  display: inline-block;
  padding: 0.14rem 0.48rem;
  border-radius: 999px;
  font-size: 0.73rem;
  font-weight: 700;
  white-space: nowrap;
}
.badge-ok { background: var(--ok-bg); color: var(--ok-ink); }
.badge-warn { background: var(--warn-bg); color: var(--warn-ink); }
.badge-bad { background: var(--bad-bg); color: var(--bad-ink); }
.badge-info { background: var(--info-bg); color: var(--info-ink); }
.src-link {
  display: inline-block;
  font-weight: 600;
  font-size: 0.79rem;
  white-space: nowrap;
}
code {
  background: #e2e8f0;
  padding: 0.08rem 0.32rem;
  border-radius: 4px;
  font-size: 0.82em;
}
footer {
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  font-size: 0.81rem;
  color: var(--muted);
}
"""


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _esc(val: object) -> str:
    return html.escape(str(val), quote=True)


def _td(val: str, *, num: bool = False) -> str:
    if val == "":
        return '<td class="empty"></td>'
    cls = ' class="num"' if num else ""
    return f"<td{cls}>{_esc(val)}</td>"


def _badge(text: str) -> str:
    up = text.upper()
    if any(k in up for k in ("BLOCKED", "CRITICAL", "SEVERE", "UNQUALIFIED", "OUT", "HIGH", "FALSE")):
        cls = "badge-bad"
    elif any(k in up for k in ("WARN", "WATCH", "MODERATE", "PENDING", "BLANK", "MEDIUM", "PARTIAL", "LIMITED")):
        cls = "badge-warn"
    elif any(k in up for k in ("VERIFIED", "NOMINAL", "COMPLETE", "SOUND", "READY", "PASS", "TRUE")):
        cls = "badge-ok"
    else:
        cls = "badge-info"
    return f'<span class="badge {cls}">{_esc(text)}</span>'


def _src_cell(url: str, label: str = "Official Source") -> str:
    safe_url = _esc(url)
    return f'<td><a class="src-link" href="{safe_url}" rel="noopener noreferrer">{_esc(label)}</a></td>'


def _layout(filename: str, page_title: str, subtitle: str, body_html: str) -> str:
    nav_links = []
    for href, label, _ in NAV_PAGES:
        cls = ' class="active"' if href == filename else ""
        nav_links.append(f'<a href="{href}"{cls}>{_esc(label)}</a>')
    nav_bar = "\n        ".join(nav_links)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(page_title)} — Own6 NFL Origination &amp; Verification Pack</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand-row">
        <div>
          <div class="brand-title">Own6 · NFL Fair-Line Origination, Depth-Deficiency &amp; Skill-Gated Leaderboard</div>
          <div class="brand-sub">Verified 2026 Regular Season (Entering Week 10 · Nov 12, 2026) · Zero Manual Input · Pure-Stdlib Engine</div>
        </div>
        <div class="brand-sub">
          <a href="../index.html" style="color:#93c5fd;">Repo Docs Hub</a> ·
          <a href="../assurance/index.html" style="color:#93c5fd;">NBA Assurance</a> ·
          <a href="../sf-94122/index.html" style="color:#93c5fd;">SF 94122</a>
        </div>
      </div>
      <nav class="nav-tabs" aria-label="NFL Origination sections">
        {nav_bar}
      </nav>
    </div>
  </header>
  <main class="container">
    <div class="gate-banner">
      <strong>DECISION-READINESS GATE STATUS:</strong> Engine Math &amp; 2026 NFL Rules/Standings/Depth Chains <strong>VERIFIED</strong> ·
      Live Line Publication &amp; Strategy Qualification <strong>FAIL-CLOSED (0 / 10 Qualified)</strong> pending licensed NFL play-by-play &amp; timestamped sportsbook closing feeds (<code>Gate NFL-G01</code>, <code>NFL-G07</code>, <code>NFL-G11</code>). Unconfirmed empirical cells are intentionally left blank.
    </div>
    <section class="hero">
      <h1>{_esc(page_title)}</h1>
      <p>{_esc(subtitle)}</p>
    </section>
{body_html}
    <footer>
      <p>
        <strong>Verification &amp; Compliance Notice:</strong> All rows link directly to primary official sources retrieved on <code>2026-11-12</code>
        (<code>nfl.com</code>, <code>operations.nfl.com</code>, <code>support.nfl.com</code>, official NFL club sites, <code>scipy.org</code>, <code>scikit-learn.org</code>, <code>statsmodels.org</code>, <code>nist.gov</code>, <code>aglc.ca</code>, and <code>github.com/sassnarep3-star/Own6</code>).
        Analytical research &amp; software verification only — no wagering solicitation or unlicensed data scraping.
        Responsible gambling support (Alberta, CA): AGLC GameSense / Self-Exclusion <code>1-844-468-8034</code> (<a href="https://aglc.ca/gaming/common-gaming-questions">aglc.ca</a>).
      </p>
    </footer>
  </main>
</body>
</html>
"""


def _live_standings_summary() -> dict:
    """Post-Thursday (13 Nov 2026) official standings, read from data/nfl_origination/standings_live_2026_11_13.csv."""
    st = _read_csv("standings_live_2026_11_13.csv")
    return {
        "n": len(st),
        "w": sum(int(r["w"]) for r in st),
        "l": sum(int(r["l"]) for r in st),
        "t": sum(int(r["t"]) for r in st),
        "pf": sum(int(r["pf"]) for r in st),
        "pa": sum(int(r["pa"]) for r in st),
        "changed": [r["abbr"] for r in st if r["changed_since_w9_snapshot"] == "true"],
    }


def _live_check_counts() -> dict:
    counts: dict = {}
    for r in _read_csv("live_check_2026_11_13.csv"):
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    return counts


def _build_live_check_html() -> str:
    checks = _read_csv("live_check_2026_11_13.csv")
    counts = _live_check_counts()
    summary = " · ".join(f"{k} {v}" for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
    rows = []
    for r in checks:
        rows.append(
            "<tr>"
            f"<td><code>{_esc(r['check_id'])}</code></td>"
            f"<td><code>{_esc(r['case_id'])}</code></td>"
            f"<td><strong>{_esc(r['player'])}</strong><br><small>{_esc(r['team'])}</small></td>"
            f"{_td(r['repo_claim'])}"
            f"{_td(r['nfl_com_listed'])}"
            f"{_td(r['nfl_com_injury'])}"
            f"{_td(r['nfl_com_practice_status'])}"
            f"{_td(r['nfl_com_game_status'])}"
            f"<td>{_badge(r['result'])}</td>"
            f"{_td(r['corrected_status'])}"
            f"{_td(r['note'])}"
            f"{_src_cell(r['official_source_url'], 'NFL.com')}"
            "</tr>"
        )
    return f"""
    <section class="section-card">
      <h2>Live Re-Verification, 13 Nov 2026: Line-by-Line Check of {len(checks)} Named Players</h2>
      <p class="lead">Each named player in the depth table was compared with the nfl.com Week 10 injury report (read 13 Nov 2026) and, where stated, the nfl.com news item for the same day. Results: {_esc(summary)}. <strong>NOT_ON_OFFICIAL_REPORT</strong> means the report lists no injury for that player, so no active status is claimed for them. Full reasoning is in <code>data/nfl_origination/live_check_2026_11_13.csv</code>.</p>
      <details>
        <summary>Show all {len(checks)} line-by-line checks</summary>
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th>Check</th><th>Case</th><th>Player &amp; Club</th><th>Repo Claim (before)</th><th>Listed on Wk 10 Report</th><th>Injury</th><th>Practice</th><th>Game Status</th><th>Result</th><th>Corrected Status</th><th>Note</th><th>Official Source</th></tr>
            </thead>
            <tbody>
              {"".join(rows)}
            </tbody>
          </table>
        </div>
      </details>
    </section>
"""


def _build_index() -> str:
    n_flags = len(_read_csv("flagged_for_review.csv"))
    standings = _read_csv("verified_standings_2026_w10.csv")
    slate = _read_csv("week10_slate_and_lines.csv")
    rules = _read_csv("nfl_official_rules_and_roster.csv")

    slate_rows = []
    for r in slate:
        neutral = "Munich Neutral (HFA=0)" if r["neutral_site"] == "true" else "Domestic / Bye"
        slate_rows.append(
            "<tr>"
            f"<td><code>{_esc(r['slot_id'])}</code></td>"
            f"{_td(r['date_et'])}"
            f"{_td(r['kickoff_et'])}"
            f"<td><strong>{_esc(r['away_team'])}</strong> ({_esc(r['away_record'])})</td>"
            f"<td><strong>{_esc(r['home_team'])}</strong> ({_esc(r['home_record'])})</td>"
            f"{_td(r['venue'])}"
            f"<td>{_badge(neutral)}</td>"
            f"{_td(r['market_spread_home'], num=True)}"
            f"{_td(r['market_total'], num=True)}"
            f"{_td(r['originated_fair_spread_home'], num=True)}"
            f"{_td(r['originated_fair_total'], num=True)}"
            f"<td><a href=\"flagged.html\">{_esc(r['flag_id'])}</a></td>"
            f"{_src_cell(r['official_source_url'], 'NFL.com / Ops')}"
            "</tr>"
        )

    st_rows = []
    for r in standings:
        st_rows.append(
            "<tr>"
            f"{_td(r['division'])}"
            f"<td><strong>{_esc(r['team'])}</strong> (<code>{_esc(r['abbr'])}</code>)</td>"
            f"{_td(r['w'], num=True)}"
            f"{_td(r['l'], num=True)}"
            f"{_td(r['t'], num=True)}"
            f"{_td(r['pct'], num=True)}"
            f"{_td(r['pf'], num=True)}"
            f"{_td(r['pa'], num=True)}"
            f"{_td(r['net_pts'], num=True)}"
            f"{_td(r['home_rec'])}"
            f"{_td(r['road_rec'])}"
            f"{_td(r['div_rec'])}"
            f"{_td(r['conf_rec'])}"
            f"{_td(r['streak'])}"
            f"{_src_cell(r['official_source_url'], 'NFL Standings')}"
            "</tr>"
        )

    rule_rows = []
    for r in rules:
        rule_rows.append(
            "<tr>"
            f"<td><code>{_esc(r['rule_id'])}</code></td>"
            f"{_td(r['domain'])}"
            f"<td><strong>{_esc(r['official_rule_name'])}</strong></td>"
            f"{_td(r['verified_rule_parameter'])}"
            f"{_td(r['origination_modeling_impact'])}"
            f"{_td(r['empirical_effect_estimate'], num=True)}"
            f"<td>{_badge(r['verification_status'])}</td>"
            f"{_src_cell(r['official_source_url'], 'Official Rule')}"
            "</tr>"
        )

    body = f"""
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Verified 2026 League Identity</div>
        <div class="kpi-value">135W–135L–2T</div>
        <div class="kpi-note">All 32 clubs reconciled · <code>6,246 PF = 6,246 PA</code> across 136 games</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Live Re-Check, 13 Nov 2026 (after WAS 24–NYG 21, FINAL)</div>
        <div class="kpi-value">{_live_standings_summary()["w"]}W–{_live_standings_summary()["l"]}L–{_live_standings_summary()["t"]}T</div>
        <div class="kpi-note">{_live_standings_summary()["pf"]:,} PF = {_live_standings_summary()["pa"]:,} PA · {len(_live_standings_summary()["changed"])} clubs changed (NYG, WAS) · <a href="injuries-depth.html">see line-by-line check</a></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Week 10 Slate &amp; Byes</div>
        <div class="kpi-value">14 Games + 4 Byes</div>
        <div class="kpi-note">Includes Munich neutral site (<code>NE vs DET</code>) · Lines left blank</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Strategy Leaderboard</div>
        <div class="kpi-value">0 / 10 Qualified</div>
        <div class="kpi-note">12 fail-closed validation &amp; anti-luck gates enforced</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Starter-to-Backup Depth</div>
        <div class="kpi-value">24 Wk 10 Chains</div>
        <div class="kpi-note">1st–4th string Offense &amp; Defense + 48-OL &amp; QB3 rules</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Decision Governance</div>
        <div class="kpi-value">14 Suggestions · 16 Q&amp;As</div>
        <div class="kpi-note">Reviewable multi-path options &amp; lawful data discovery</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Primary Verification</div>
        <div class="kpi-value">28 Official Sources</div>
        <div class="kpi-note">100% row-linked · {n_flags} items on <a href="flagged.html">Flagged for Review</a></div>
      </div>
    </div>

    <section class="section-card">
      <h2>Quick Navigation Across All Project Deliverables</h2>
      <p class="lead">Every requirement is organized into a dedicated, zero-input dashboard view with per-row official source links.</p>
      <div class="callout-grid">
        <div class="callout">
          <h3>1. Governance, Suggestions &amp; Pre-Decision Q&amp;A</h3>
          <ul>
            <li><a href="executive-summary.html">Executive Summary &amp; 28-Source Register</a></li>
            <li><a href="requirements.html">Full Itemized Requirements Matrix (REQ-01..REQ-16)</a></li>
            <li><a href="suggestions.html">Dedicated Site &amp; Decision Suggestions for Review (SUG-01..SUG-14)</a></li>
            <li><a href="decision-qa.html">Pre-Decision Questions, Missing Data &amp; Discovery Paths (Q-01..Q-16)</a></li>
          </ul>
        </div>
        <div class="callout">
          <h3>2. Line Origination, Leaderboard, Correlations &amp; Luck</h3>
          <ul>
            <li><a href="strategies-leaderboard.html">Fair-Line Origination &amp; 10-Strategy Skill Leaderboard</a></li>
            <li><a href="validation-gates.html">12 Validation Gates &amp; Luck-Removal Controls (NFL-G01..G12)</a></li>
            <li><a href="correlations.html">SGP / Parlay / Prop-Combo Correlations &amp; Copula Math</a></li>
          </ul>
        </div>
        <div class="callout">
          <h3>3. Starter/Backup Depth, Repo Audit &amp; Flagged Items</h3>
          <ul>
            <li><a href="injuries-depth.html">Week 10 Injuries &amp; 1st–4th String Offensive/Defensive Depth</a></li>
            <li><a href="repo-audit.html">Line-by-Line Existing Repository Audit (RA-01..RA-16)</a></li>
            <li><a href="flagged.html">Flagged for Review Page (NFL-F01..NFL-F{n_flags:02d} — Non-Blocking)</a></li>
          </ul>
        </div>
      </div>
    </section>

    <section class="section-card">
      <h2>2026 NFL Week 10 Official Slate &amp; Fail-Closed Line Origination Ledger (Nov 12–16, 2026)</h2>
      <p class="lead">Matchups, records, kickoff windows, broadcast networks, and Munich neutral-site designation verified directly from NFL.com and NFL Football Operations. Unlicensed sportsbook spreads/totals and uncalibrated empirical originated lines remain strictly blank (<code>NFL-F01</code>).</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Slot</th><th>Date</th><th>Kickoff</th><th>Away Club (Rec)</th><th>Home Club (Rec)</th><th>Venue</th><th>Site Type</th><th>Mkt Spread</th><th>Mkt Total</th><th>Orig Spread</th><th>Orig Total</th><th>Flag</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(slate_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>Official 2026 NFL Rules, Roster Thresholds &amp; Data-Rights Constraints</h2>
      <p class="lead">Structural rules verified verbatim from NFL Football Operations and NFL.com Terms; empirical point/EPA effect sizes stay blank until post-2025 licensed play-by-play regression is run.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Rule ID</th><th>Domain</th><th>Official Rule</th><th>Verified Parameter</th><th>Origination Modeling Impact</th><th>Empirical Delta</th><th>Status</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rule_rows)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>Verified 2026 NFL Standings Entering Week 10 (All 32 Clubs)</h2>
      <p class="lead">Verified line-by-line from <code>nfl.com/standings/division/2026/reg</code> on Nov 12, 2026. League-wide identity check: <code>sum(W) = 135 = sum(L)</code>, <code>sum(T) = 2</code>, and <code>sum(PF) = 6,246 = sum(PA)</code>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Division</th><th>Club</th><th>W</th><th>L</th><th>T</th><th>PCT</th><th>PF</th><th>PA</th><th>Net</th><th>Home</th><th>Road</th><th>Div</th><th>Conf</th><th>Strk</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(st_rows)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("index.html", NAV_PAGES[0][2], "Complete Week 10 NFL schedule, reconciled 32-club 2026 standings, 2025–2026 rule regime parameters, and fail-closed origination ledger.", body)


def _build_exec_summary() -> str:
    sources = _read_csv("sources.csv")
    rows_html = []
    for r in sources:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['source_id'])}</code></td>"
            f"{_td(r['publisher'])}"
            f"<td><strong>{_esc(r['title'])}</strong></td>"
            f"{_td(r['verified_date'])}"
            f"{_td(r['retrieval_method'])}"
            f"<td>{_badge(r['verification_status'])}</td>"
            f"{_td(r['supports_claim'])}"
            f"{_td(r['does_not_support_boundary'])}"
            f"{_src_cell(r['official_source_url'], 'Primary Source')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>Executive Summary — Key Architecture &amp; Findings</h2>
      <p class="lead">Companion Markdown deliverable: <a href="../../NFL_ORIGINATION_EXECUTIVE_SUMMARY.md"><code>NFL_ORIGINATION_EXECUTIVE_SUMMARY.md</code></a>.</p>
      <div class="callout">
        <h3>Live re-verification, 13 Nov 2026</h3>
        <p>The Thursday game is <strong>final: Commanders 24, Giants 21</strong>. League totals are now <strong>136W–136L–2T</strong> and <strong>6,291 PF = PA</strong> (through-Week-9 snapshot kept below for provenance). The line-by-line check of named players found <strong>17 depth/injury statuses contradicted by the official report</strong>; they are corrected on the <a href="injuries-depth.html">injuries &amp; depth page</a>. Audit: <a href="https://github.com/sassnarep3-star/Own6/blob/arena/4fc2fd57-own6/audit/NFL_LIVE_REVERIFICATION_2026_11_13.md"><code>audit/NFL_LIVE_REVERIFICATION_2026_11_13.md</code></a>.</p>
      </div>
      <div class="callout-grid">
        <div class="callout">
          <h3>Verified 2026 NFL Baseline</h3>
          <p>Through Week 9 (136 completed 2026 regular-season games), league scoring averages <strong>45.93 combined points/game</strong> (<code>6,246 PF = 6,246 PA</code>) with 1 regular-season tie (<code>WAS–NYG</code>) under the permanent 10-minute both-teams-possess overtime rule and 35-yard Dynamic Kickoff touchback.</p>
        </div>
        <div class="callout">
          <h3>Pure-Stdlib NFL Engine (<code>src/nfl_origination/</code>)</h3>
          <p>Implements multiplicative &amp; power de-vigging, push-exact EV, same-line CLV, discrete integer-margin PMFs (key numbers <code>3, 7, 6, 10, 14</code> + OT ties), 1st–4th string depth &amp; 48-OL/QB3 roster checks, Sheppard/Simpson 2-leg &amp; Cholesky k-leg Gaussian copulas, and 12 anti-luck validation gates.</p>
        </div>
        <div class="callout">
          <h3>Critical Depth &amp; Data Integrity Discovery</h3>
          <p>Official club websites explicitly label their depth charts <em>"Unofficial"</em> and lag mid-season trades (Vikings QB Kirk Cousins) and injury designations (Commanders C Lucas Patrick). Standalone reliance on static club depth charts is blocked by <code>Gate NFL-G10</code>.</p>
        </div>
        <div class="callout">
          <h3>Zero Hallucinations &amp; Review-First Governance</h3>
          <p>All unlicensed odds, empirical EPA drop-offs, and paired NFL residual correlations are strictly blank (<code>""</code>). 14 site/workflow improvements wait in <a href="suggestions.html">Suggestions for Review</a> so human decision-makers control every shared-repo change.</p>
        </div>
      </div>
    </section>

    <section class="section-card">
      <h2>Complete 28-Source Official Verification Register (<code>NFL-S01</code>..<code>NFL-S28</code>)</h2>
      <p class="lead">Every external source below was directly retrieved via <code>fetch_page</code> or GitHub API on <code>2026-11-12</code>, recording both what it supports and what it does NOT support.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Publisher</th><th>Document Title</th><th>Verified</th><th>Method</th><th>Status</th><th>Supports Claim</th><th>Boundary (Does Not Support)</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("executive-summary.html", NAV_PAGES[1][2], "High-level synthesis of verified 2026 NFL Week 10 state, pure-stdlib mathematical architecture, blocking unknowns, and all 28 primary sources.", body)


def _build_requirements() -> str:
    reqs = _read_csv("requirements_matrix.csv")
    rows_html = []
    for r in reqs:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['req_id'])}</code></td>"
            f"{_td(r['category'])}"
            f"<td><strong>{_esc(r['requirement_statement'])}</strong></td>"
            f"{_td(r['collection_artifact'])}"
            f"<td><code>{_esc(r['organization_layer'])}</code></td>"
            f"{_td(r['analytical_method'])}"
            f"<td>{_badge(r['verification_status'])}</td>"
            f"<td><a href=\"{_esc(r['deliverable_page'])}\">{_esc(r['deliverable_page'])}</a></td>"
            f"{_src_cell(r['official_source_url'], 'Authority')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>Itemized Project Requirements — Collection, Organization &amp; Analytical Traceability (<code>REQ-01</code>..<code>REQ-16</code>)</h2>
      <p class="lead">Every requirement is decomposed into (1) Verified Collection Artifact, (2) Structured CSV/Code Organization Layer, (3) Analytical/Statistical Verification Method, and (4) Published Dashboard View.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Req ID</th><th>Category</th><th>Requirement</th><th>Collection Artifact</th><th>Organization Layer</th><th>Analytical Method</th><th>Status</th><th>View</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("requirements.html", NAV_PAGES[2][2], "End-to-end traceability from every user requirement to verified primary sources, structured CSV schemas, pure-stdlib modules, and dashboard pages.", body)


def _build_suggestions() -> str:
    sugs = _read_csv("site_suggestions.csv")
    rows_html = []
    for r in sugs:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['suggestion_id'])}</code></td>"
            f"{_td(r['area'])}"
            f"<td><strong>{_esc(r['title'])}</strong></td>"
            f"{_td(r['current_repo_state'])}"
            f"{_td(r['decision_problem_solved'])}"
            f"{_td(r['option_paths_for_review'])}"
            f"<td><strong>{_esc(r['recommended_path'])}</strong></td>"
            f"{_td(r['prerequisites_before_implementing'])}"
            f"{_td(r['effort_and_reversibility'])}"
            f"<td>{_badge(r['review_status'])}</td>"
            f"{_src_cell(r['official_source_url'], 'Ref Link')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>How to Use This Suggestions Review Section Before Implementing Shared Changes</h2>
      <p class="lead">Detailed companion note: <a href="../../research/nfl_origination/DECISION_QA_AND_SUGGESTIONS.md"><code>research/nfl_origination/DECISION_QA_AND_SUGGESTIONS.md</code></a>. None of the shared-repo structural changes below were forced unilaterally — each presents concrete Option Paths (A / B / C), prerequisites, and reversibility so a reviewer can choose the best path first.</p>
      <div class="callout-grid">
        <div class="callout">
          <h3>Immediate Zero-Risk Wins (Path A Recommended)</h3>
          <p><code>SUG-03</code> (Go/No-Go Gate Banner), <code>SUG-05</code> (Unit-Depth Cascade Badges), <code>SUG-08</code> (SkillScore Primary Ranking), and <code>SUG-09</code> (Stdlib Test Guard) are previewed non-destructively inside <code>docs/nfl-origination/</code> without altering any peer files.</p>
        </div>
        <div class="callout">
          <h3>Owner Sign-Off Required (Shared Root / Legacy Paths)</h3>
          <p><code>SUG-01</code> (Neutral Multi-Domain Root <code>index.html</code>), <code>SUG-02</code> (Parallel Battle-Pack Archival Banners), and <code>SUG-10</code> (Legacy Prototype CSV Quarantine) touch shared entrypoints and wait for explicit owner approval.</p>
        </div>
        <div class="callout">
          <h3>Highest Origination Alpha Upgrades</h3>
          <p><code>SUG-11</code> (Free public-domain <code>api.weather.gov</code> stadium wind feed), <code>SUG-04</code> (Wednesday vs. T-85m Post-Inactive dual snapshots), and <code>SUG-12</code> (Bottom-up roster-assembled ratings for mid-season trades).</p>
        </div>
      </div>
    </section>

    <section class="section-card">
      <h2>Site &amp; Decision-Making Improvement Proposals (<code>SUG-01</code>..<code>SUG-14</code>)</h2>
      <p class="lead">Compare Option Paths, Prerequisites, Effort, and Reversibility side by side before authorizing implementation.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Area</th><th>Proposal</th><th>Current Repo State</th><th>Decision Problem Solved</th><th>Option Paths (A / B / C)</th><th>Recommended Path</th><th>Prerequisites</th><th>Effort &amp; Reversibility</th><th>State</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("suggestions.html", NAV_PAGES[3][2], "Dedicated pre-implementation review board comparing concrete architectural and decision-workflow upgrades across effort, risk, and reversibility.", body)


def _build_decision_qa() -> str:
    qas = _read_csv("decision_qa_and_missing_info.csv")
    rows_html = []
    for r in qas:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['qa_id'])}</code></td>"
            f"{_td(r['decision_domain'])}"
            f"<td><strong>{_esc(r['critical_question'])}</strong></td>"
            f"{_td(r['information_we_have_verified'])}"
            f"{_td(r['information_we_do_not_have'])}"
            f"{_td(r['current_answer_and_gate_impact'])}"
            f"{_td(r['discovery_suggestion_path'])}"
            f"<td>{_badge(r['blocking_severity'])}</td>"
            f"<td><a href=\"flagged.html\">{_esc(r['flag_id'])}</a></td>"
            f"{_src_cell(r['official_source_url'], 'Official Ref')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>Pre-Decision Readiness Audit — Known Facts vs. Missing Information &amp; Lawful Discovery (<code>Q-01</code>..<code>Q-16</code>)</h2>
      <p class="lead">Before making any line-origination, strategy-promotion, or site-governance decision, review the 16 critical questions below separating verified primary-source facts from blank unverified gaps and the exact lawful path to acquire each missing input.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Q ID</th><th>Domain</th><th>Critical Pre-Decision Question</th><th>What We Already Have (Verified)</th><th>What We Do NOT Have (Blank)</th><th>Answer &amp; Gate Impact</th><th>Concrete Discovery Suggestion</th><th>Severity</th><th>Flag</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("decision-qa.html", NAV_PAGES[4][2], "Explicit inventory of pre-decision questions, verified facts in hand, missing unverified inputs, answers, and lawful data-discovery protocols.", body)


def _build_strategies_leaderboard() -> str:
    strats = _read_csv("strategies_leaderboard.csv")
    rows_html = []
    for r in strats:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['strategy_id'])}</code></td>"
            f"{_td(r['bet_structure'])}"
            f"<td><strong>{_esc(r['strategy_name'])}</strong></td>"
            f"{_td(r['signal_hypothesis_and_mechanism'])}"
            f"{_td(r['key_features_required'])}"
            f"{_td(r['primary_luck_controls'])}"
            f"{_td(r['gates_passed_ratio'], num=True)}"
            f"{_td(r['n_observations'], num=True)}"
            f"{_td(r['holdout_roi'], num=True)}"
            f"{_td(r['same_line_clv'], num=True)}"
            f"{_td(r['brier_score'], num=True)}"
            f"{_td(r['skill_score'], num=True)}"
            f"{_td(r['leaderboard_rank'], num=True)}"
            f"<td>{_badge(r['reward_tier'])}</td>"
            f"{_src_cell(r['official_source_url'], 'Spec Source')}"
            "</tr>"
        )

    # Deterministic engine formula verification table (clearly labeled synthetic/structural illustration!)
    illustrative_regime = NFLRegimeParams(
        league_mean_pts_per_drive=2.08,
        mean_drives_per_team=11.0,
        hfa_points=2.0,
        margin_sd=13.5,
        total_sd=10.2,
        reg_ot_tie_prob_when_close=0.008,
        dynamic_kickoff_35yd_active=True,
        both_teams_possess_ot_active=True,
        key_number_pmf_weights={3: 1.90, 7: 1.55, 6: 1.25, 10: 1.30, 14: 1.25},
    )
    synth_game = NFLGameInput(
        game_id="FORMULA-DEMO",
        away_team="AWAY_SYNTH",
        home_team="HOME_SYNTH",
        neutral_site=False,
        away_off_pts_per_drive=2.02,
        away_def_pts_per_drive=2.10,
        home_off_pts_per_drive=2.14,
        home_def_pts_per_drive=2.00,
    )
    key_rows = []
    for target_line in (-2.5, -3.0, -3.5, -6.5, -7.0, -7.5):
        out = originate_nfl_game(synth_game, illustrative_regime, target_spread_home=target_line)
        cp = out["spread_cover_probs"]
        assert isinstance(cp, dict)
        ev110 = push_aware_ev(cp["p_cover"], cp["p_loss"], cp["p_push"], -110)
        fair_no_push = cp["p_cover"] / (cp["p_cover"] + cp["p_loss"])
        key_rows.append(
            "<tr>"
            f"<td><code>Home {target_line:+.1f}</code></td>"
            f"<td class=\"num\">{cp['p_cover']*100:.2f}%</td>"
            f"<td class=\"num\">{cp['p_loss']*100:.2f}%</td>"
            f"<td class=\"num\">{cp['p_push']*100:.2f}%</td>"
            f"<td class=\"num\">{prob_to_fair_american(fair_no_push):+d}</td>"
            f"<td class=\"num\">{ev110*100:+.2f}%</td>"
            "<td>Synthetic formula verification of <code>originate_nfl_game()</code> &amp; <code>push_aware_ev()</code> (NOT a real team rating)</td>"
            f"{_src_cell('https://operations.nfl.com/rules-officiating/2026-nfl-rulebook', 'NFL Rule 11')}"
            "</tr>"
        )

    body = f"""
    <section class="section-card">
      <h2>NFL Strategy Competition Leaderboard — Singles, Multi-Game Parlays &amp; Player-Prop Combos (<code>NFL-STR-01</code>..<code>NFL-STR-10</code>)</h2>
      <p class="lead">Strategies compete for non-monetary research priority &amp; compute allocation tiers (<code>GOLD</code> / <code>SILVER</code> / <code>BRONZE</code>) ranked strictly by <code>SkillScore = 100*ROI_LCB95_Week + 50*Mean_SameLine_CLV + 25*Brier_Edge</code>. Because licensed NFL play-by-play and closing-odds ledgers are absent, <strong>0 of 10 strategies qualify today</strong> and empirical metrics remain strictly blank.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Structure</th><th>Strategy Name</th><th>Signal Hypothesis &amp; Football Mechanism</th><th>Required Inputs</th><th>Anti-Luck Controls</th><th>Gates</th><th>N</th><th>Holdout ROI</th><th>Same-Line CLV</th><th>Brier</th><th>Skill Score</th><th>Rank</th><th>Reward Tier</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>Discrete NFL Key-Number &amp; Push-Exact Origination Engine Verification (Formula Check Only)</h2>
      <p class="lead">Demonstrates why legacy continuous NBA normal CDFs fail on NFL spreads: moving a single half-point across key number <code>-3.0</code> or <code>-7.0</code> creates a massive discontinuous jump in push probability and expected value at <code>-110</code>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Evaluated Spread</th><th>P(Cover)</th><th>P(Loss)</th><th>P(Push)</th><th>Fair No-Vig Odds</th><th>EV at -110</th><th>Scope &amp; Provenance Note</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(key_rows)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("strategies-leaderboard.html", NAV_PAGES[5][2], "Independent NFL fair-line origination math, 10 preregistered single/parlay/prop-combo strategies, and fail-closed skill leaderboard.", body)


def _build_validation_gates() -> str:
    gates = _read_csv("validation_gates.csv")
    rows_html = []
    for r in gates:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['gate_id'])}</code></td>"
            f"<td><strong>{_esc(r['gate_name'])}</strong></td>"
            f"{_td(r['quantitative_threshold_rule'])}"
            f"{_td(r['luck_or_leakage_failure_mode_blocked'])}"
            f"<td><code>{_esc(r['code_enforcement_module'])}</code></td>"
            f"<td>{_badge(r['current_ledger_state'])}</td>"
            f"{_src_cell(r['official_source_url'], 'Primary Spec')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>How Luck Is Removed From NFL Leaderboard Qualification</h2>
      <p class="lead">In a 272-game NFL regular season, single-game turnover luck (fumble bounces, tipped interceptions, upright kicks) creates a <code>~6.03%</code> ROI standard error at <code>N = 250</code> binary bets. Our engine eliminates luck from strategy promotion via four orthogonal statistical barriers:</p>
      <div class="callout-grid">
        <div class="callout">
          <h3>1. Same-Line De-Vigged CLV (<code>t &gt;= 2.50</code>)</h3>
          <p><code>Gate NFL-G07</code> measures whether originated prices consistently beat the vig-free closing line on the <em>exact same spread/total number</em> — a pre-kickoff skill signal with 3x–4x tighter variance than binary game outcomes.</p>
        </div>
        <div class="callout">
          <h3>2. Strictly Proper Scoring Dominance</h3>
          <p><code>Gate NFL-G06</code> requires out-of-sample <code>Brier</code> AND <code>LogLoss</code> to beat the de-vigged closing market on identical games, disqualifying lucky longshot parlay hits that lack calibration.</p>
        </div>
        <div class="callout">
          <h3>3. NFL Week-Clustered Block Bootstrap</h3>
          <p><code>Gate NFL-G08</code> resamples entire NFL slate weeks together (<code>n_resamples = 4,000</code>) so correlated Sunday wind troughs or slate-wide injury shocks cannot understate confidence-interval width.</p>
        </div>
        <div class="callout">
          <h3>4. Holm-Bonferroni Family-Wise Error Control</h3>
          <p><code>Gate NFL-G09</code> adjusts raw p-values across all <code>M &gt;= 10</code> registered strategies and feature variants so testing multiple NFL hypotheses cannot sneak a false positive onto the leaderboard.</p>
        </div>
      </div>
    </section>

    <section class="section-card">
      <h2>All 12 Mandatory NFL Validation Gates (<code>NFL-G01</code>..<code>NFL-G12</code>)</h2>
      <p class="lead">Every strategy must pass <code>12 / 12</code> gates simultaneously; missing evidence always evaluates to <code>BLOCKED</code>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Gate ID</th><th>Gate Name</th><th>Quantitative Threshold Rule</th><th>Failure Mode / Luck Mechanism Blocked</th><th>Code Module</th><th>Current State</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("validation-gates.html", NAV_PAGES[6][2], "Mandatory 12-gate validation pipeline and anti-luck statistical controls separating repeatable origination skill from NFL variance.", body)


def _build_correlations() -> str:
    corrs = _read_csv("correlations_and_combos.csv")
    rows_html = []
    for r in corrs:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['corr_id'])}</code></td>"
            f"{_td(r['combo_category'])}"
            f"<td><strong>{_esc(r['leg_1_market'])}</strong></td>"
            f"<td><strong>{_esc(r['leg_2_market'])}</strong></td>"
            f"{_td(r['football_dependence_mechanism'])}"
            f"<td>{_badge(r['theoretical_direction'])}</td>"
            f"{_td(r['empirical_pearson_r'], num=True)}"
            f"{_td(r['empirical_spearman_rho'], num=True)}"
            f"{_td(r['week_cluster_ci_95'])}"
            f"{_td(r['empirical_n_pairs'], num=True)}"
            f"{_td(r['copula_illustrative_sensitivity_note'])}"
            f"{_src_cell(r['official_source_url'], 'Math / NFL Spec')}"
            "</tr>"
        )

    # Exact deterministic Sheppard / Simpson quadrature Gaussian copula table at p1 = p2 = 0.50
    copula_rows = []
    for rho in (-0.50, -0.30, -0.15, 0.00, 0.15, 0.30, 0.45, 0.60):
        jp = bivariate_normal_joint_prob(0.50, 0.50, rho)
        mult = jp / 0.25
        fair_am = prob_to_fair_american(jp)
        copula_rows.append(
            "<tr>"
            f"<td class=\"num\"><code>{rho:+.2f}</code></td>"
            "<td class=\"num\">50.00% / 50.00%</td>"
            "<td class=\"num\">25.00% (+300)</td>"
            f"<td class=\"num\"><strong>{jp*100:.2f}%</strong></td>"
            f"<td class=\"num\">{mult:.3f}x</td>"
            f"<td class=\"num\"><code>{fair_am:+d}</code></td>"
            "<td>Exact bivariate normal copula quadrature (<code>bivariate_normal_joint_prob</code>); empirical NFL <code>rho</code> requires licensed residuals</td>"
            f"{_src_cell('https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.multivariate_normal.html', 'SciPy MVN')}"
            "</tr>"
        )

    body = f"""
    <section class="section-card">
      <h2>NFL Parlay, SGP &amp; Player-Prop Combo Correlation Matrix (<code>CORR-01</code>..<code>CORR-12</code>)</h2>
      <p class="lead">Companion specification: <a href="../../research/nfl_origination/ORIGINATION_SIGNALS_AND_CORRELATIONS.md"><code>ORIGINATION_SIGNALS_AND_CORRELATIONS.md</code></a>. Qualitative football mechanisms are documented below while empirical Pearson, Spearman, and week-block CI cells remain strictly blank (<code>NFL-F08</code>) until paired pregame-centered residuals are licensed.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Category</th><th>Leg 1</th><th>Leg 2</th><th>Causal Football Dependence Mechanism</th><th>Expected Sign</th><th>Emp Pearson r</th><th>Emp Spearman rho</th><th>Week-Block 95% CI</th><th>N Pairs</th><th>Copula Pricing &amp; SGP Tax Note</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-card">
      <h2>Exact 2-Leg Gaussian Copula Joint-Probability &amp; Fair-Odds Sensitivity Table (Mathematical Verification)</h2>
      <p class="lead">Computed deterministically by <code>src/nfl_origination/correlations.py</code> for two 50% marginal legs across latent correlation <code>rho</code>. Shows both why negative correlation destroys naive parlay EV and how to audit sportsbook SGP correlation taxes on positive stacks.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Latent Residual rho</th><th>Leg Marginals</th><th>Independent Joint (Odds)</th><th>Copula Joint Hit %</th><th>Multiplier</th><th>Fair Correlated Odds</th><th>Analytical Governance Note</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(copula_rows)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("correlations.html", NAV_PAGES[7][2], "Causal dependence structures across Same-Game Parlays, multi-game weather parlays, and player-prop combinations with exact Gaussian copula math.", body)


def _build_injuries_depth() -> str:
    cases = _read_csv("injury_and_depth_deficiency.csv")
    live_html = _build_live_check_html()
    rows_html = []
    for r in cases:
        casc = "CASCADE ALERT" if r["cascading_cluster_alert"] == "true" else "Single / Contained"
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['case_id'])}</code></td>"
            f"<td><strong>{_esc(r['team'])}</strong><br><small>{_esc(r['week10_matchup'])}</small></td>"
            f"<td>{_badge(r['side'])}</td>"
            f"<td>{_esc(r['unit_group'])} (<code>{_esc(r['position'])}</code>)</td>"
            f"<td><strong>{_esc(r['string_1_starter'])}</strong><br><small>{_esc(r['starter_week10_status'])}</small></td>"
            f"<td>{_esc(r['string_2_backup'])}<br><small>{_esc(r['backup_2_status'])}</small></td>"
            f"{_td(r['string_3_backup'])}"
            f"{_td(r['string_4_backup'])}"
            f"<td>{_badge(r['active_replacement_tier'])}</td>"
            f"<td>{_badge(casc)}</td>"
            f"{_td(r['empirical_epa_dropoff'], num=True)}"
            f"{_td(r['verified_week10_snap_share'], num=True)}"
            f"{_src_cell(r['official_source_url'], 'Club / NFL.com')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>Offensive &amp; Defensive Starter-vs-Backup (1st, 2nd, 3rd &amp; 4th String) Depth Methodology</h2>
      <p class="lead">Companion specification: <a href="../../research/nfl_origination/INJURY_AND_BACKUP_DEPTH_METHODOLOGY.md"><code>INJURY_AND_BACKUP_DEPTH_METHODOLOGY.md</code></a>. Reconciles official Week 10 <code>nfl.com/injuries/</code> reports (retrieved Nov 12, 2026) with directly fetched 2026 club depth charts and NFL roster bylaws.</p>
      <div class="callout-grid">
        <div class="callout">
          <h3>48-vs-47 Active Roster &amp; 8-OL Rule</h3>
          <p>Under NFL Football Operations contract language, dressing fewer than <strong>8 offensive linemen</strong> drops a club's gameday active limit from <strong>48 to 47 players</strong> — compounding multi-OL injury clusters (Patriots &amp; Cardinals in Week 10).</p>
        </div>
        <div class="callout">
          <h3>Emergency 3rd QB &amp; PS Elevation Caps</h3>
          <p>Emergency 3rd QBs must sit on the <strong>53-man roster</strong> (Practice Squad QBs are ineligible per NFLPA veto) and enter only if QB1 &amp; QB2 exit via injury/disqualification. Standard PS elevations cap at <strong>2/week</strong> and <strong>3 games/season/player</strong>.</p>
        </div>
        <div class="callout">
          <h3>Club Web Depth-Chart Lag Proof (<code>NFL-F07</code>)</h3>
          <p>Patriots.com, Lions.com, Vikings.com, and Packers.com carry explicit <em>"Unofficial"</em> disclaimers; Vikings.com lags the Kirk Cousins trade, and Commanders.com omits C Lucas Patrick (<code>OUT</code> on NFL.com).</p>
        </div>
      </div>
    </section>

    <section class="section-card">
      <h2>Verified Week 10 Starter-to-Backup Replacement &amp; Deficiency Table (<code>DEPTH-01</code>..<code>DEPTH-24</code>)</h2>
      <p class="lead">Tracks 1st-string starter vs. 2nd-, 3rd-, and 4th-string replacements across Offense and Defense. Empirical EPA/play drop-offs and unplayed Week 10 snap shares remain strictly blank (<code>NFL-F04</code>).</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Club &amp; Wk 10 Game</th><th>Side</th><th>Unit (Pos)</th><th>1st String (Starter &amp; Status)</th><th>2nd String (Primary Backup)</th><th>3rd String</th><th>4th String / Notes</th><th>Replacement Tier</th><th>Cluster</th><th>Emp EPA Delta</th><th>Wk 10 Snaps</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
{live_html}"""
    return _layout("injuries-depth.html", NAV_PAGES[8][2], "Week 10 NFL offensive and defensive 1st-to-4th string replacement tracking, cascading unit-cluster alerts, and 48-OL / Emergency-QB3 compliance.", body)


def _build_repo_audit() -> str:
    findings = _read_csv("repo_audit_findings.csv")
    rows_html = []
    for r in findings:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['finding_id'])}</code></td>"
            f"<td>{_badge(r['severity'])}</td>"
            f"<td><code>{_esc(r['repo_path'])}</code></td>"
            f"{_td(r['lines_checked'])}"
            f"{_td(r['component_domain'])}"
            f"{_td(r['verification_finding'])}"
            f"<td>{_badge(r['status_disposition'])}</td>"
            f"{_src_cell(r['official_source_url'], 'Repo / API')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>Line-by-Line Existing Repository Review (<code>RA-01</code>..<code>RA-16</code>)</h2>
      <p class="lead">Companion full audit report: <a href="../../audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md"><code>audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md</code></a>. Every legacy module, CI workflow, sibling pack, and root entrypoint was inspected against official sources without modifying files outside our claimed scope.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Audit ID</th><th>Severity</th><th>Repository Path</th><th>Lines</th><th>Domain</th><th>Line-by-Line Verification Finding</th><th>Disposition</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("repo-audit.html", NAV_PAGES[9][2], "Line-by-line code, math, CI-workflow, and link audit of existing Own6 repository modules with primary GitHub inspection links.", body)


def _build_flagged() -> str:
    flags = _read_csv("flagged_for_review.csv")
    n_flags = len(flags)
    rows_html = []
    for r in flags:
        rows_html.append(
            "<tr>"
            f"<td><code>{_esc(r['flag_id'])}</code></td>"
            f"<td>{_badge(r['severity'])}</td>"
            f"{_td(r['category'])}"
            f"<td><code>{_esc(r['affected_table_or_path'])}</code></td>"
            f"<td><strong>{_esc(r['item_summary'])}</strong></td>"
            f"{_td(r['why_blank_or_flagged'])}"
            f"{_td(r['resolution_path'])}"
            f"<td>{_badge('NON-BLOCKING (' + r['blocking_merge'] + ')')}</td>"
            f"{_src_cell(r['official_source_url'], 'Manual Review')}"
            "</tr>"
        )
    body = f"""
    <section class="section-card">
      <h2>Flagged for Review — Unverified Blank Cells &amp; Repository Irregularities (<code>NFL-F01</code>..<code>NFL-F{n_flags:02d}</code>)</h2>
      <p class="lead">Per strict anti-hallucination governance, unconfirmed empirical values are never guessed or interpolated. All {n_flags} items below are published transparently with direct links for manual human review and do not block PR merge.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Flag ID</th><th>Severity</th><th>Category</th><th>Affected Table / Path</th><th>Flagged Item Summary</th><th>Why Left Blank or Flagged</th><th>Lawful Resolution Path</th><th>Merge Policy</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows_html)}
          </tbody>
        </table>
      </div>
    </section>
"""
    return _layout("flagged.html", NAV_PAGES[10][2], "Transparent non-blocking ledger of every intentionally blank empirical field, club depth-chart disclaimer, and legacy repository irregularity.", body)


def generate_all() -> dict[Path, str]:
    builders = {
        OUT_DIR / "assets" / "style.css": STYLESHEET,
        OUT_DIR / "index.html": _build_index(),
        OUT_DIR / "executive-summary.html": _build_exec_summary(),
        OUT_DIR / "requirements.html": _build_requirements(),
        OUT_DIR / "suggestions.html": _build_suggestions(),
        OUT_DIR / "decision-qa.html": _build_decision_qa(),
        OUT_DIR / "strategies-leaderboard.html": _build_strategies_leaderboard(),
        OUT_DIR / "validation-gates.html": _build_validation_gates(),
        OUT_DIR / "correlations.html": _build_correlations(),
        OUT_DIR / "injuries-depth.html": _build_injuries_depth(),
        OUT_DIR / "repo-audit.html": _build_repo_audit(),
        OUT_DIR / "flagged.html": _build_flagged(),
    }
    return builders


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or check docs/nfl-origination static site.")
    parser.add_argument("--check", action="store_true", help="Verify committed files match generator output.")
    args = parser.parse_args()

    outputs = generate_all()
    if args.check:
        stale: list[str] = []
        for path, expected in outputs.items():
            if not path.is_file():
                stale.append(f"Missing {path.relative_to(ROOT)}")
            elif path.read_text(encoding="utf-8") != expected:
                stale.append(f"Out-of-date {path.relative_to(ROOT)}")
        if stale:
            for msg in stale:
                print("FAIL:", msg)
            return 1
        print(f"build_nfl_origination --check OK: {len(outputs)} generated artifacts up to date.")
        return 0

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"Generated {len(outputs)} artifacts in {OUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
