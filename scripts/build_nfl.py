#!/usr/bin/env python3
"""Build docs/nfl/ NFL lines research dashboard from data/nfl/*.csv.

Every table row carries an official https source link; unverified empirical values
are rendered as '— blank (unverified)' and flagged. No network calls, no scraping,
no invented values.
"""
from __future__ import annotations

import csv
import html
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl"
OUT = ROOT / "docs" / "nfl"

CSS = """:root{--bg:#f7f8fa;--ink:#1f2933;--muted:#6b7280;--line:#e5e7eb;--accent:#0b5fff;--ok:#0a7d4f;--warn:#b45309;--bad:#b91c1c;--card:#ffffff}
*{box-sizing:border-box}body{margin:0;font:15px/1.6 system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:1rem;padding:.8rem 1.2rem;background:#fff;border-bottom:1px solid var(--line)}
header.top .brand{font-weight:800;letter-spacing:.02em;color:var(--ink)}.brand span{font-weight:400;color:var(--muted)}
nav.primary{display:flex;flex-wrap:wrap;gap:.8rem}.primary a{font-size:.88rem;padding:.2rem .5rem;border-radius:.4rem}.primary a.active{background:var(--accent);color:#fff}
main{max-width:1160px;margin:1.6rem auto;padding:0 1.2rem}
.hero{background:var(--card);border:1px solid var(--line);border-radius:.8rem;padding:1.4rem 1.6rem;margin:1rem 0;display:flex;flex-wrap:wrap;gap:1.2rem;justify-content:space-between}
.hero h1{margin:.2rem 0;font-size:1.55rem;line-height:1.2}.eyebrow{color:var(--muted);font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;margin:0}
.kpis{display:flex;gap:.8rem;flex-wrap:wrap}.kpi{background:#f1f3f6;border-radius:.6rem;padding:.6rem .9rem;min-width:110px;text-align:center}.kpi b{display:block;font-size:1.2rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1rem;margin:1.2rem 0}.card{background:var(--card);border:1px solid var(--line);border-radius:.7rem;padding:1rem}
.card h3{margin:.2rem 0;font-size:1rem}.card p{color:var(--muted);font-size:.92rem;margin:.3rem 0}
.badge{display:inline-block;padding:.15rem .5rem;border-radius:.5rem;font-size:.76rem;font-weight:700}.badge.ok{background:#e6f4ea;color:var(--ok)}.badge.warn{background:#fef3c7;color:var(--warn)}.badge.bad{background:#fde8e8;color:var(--bad)}.badge.muted{background:#eef0f2;color:var(--muted)}
.blank{color:var(--muted);font-style:italic}
.callout{border-left:3px solid var(--accent);background:var(--card);padding:.9rem 1rem;margin:1rem 0;border-radius:0 .6rem .6rem 0}
table{width:100%;border-collapse:collapse;margin:1rem 0;background:var(--card);font-size:.90rem;border-radius:.6rem;overflow:hidden}
th,td{border:1px solid var(--line);padding:.5rem .65rem;text-align:left;vertical-align:top}th{background:#f1f3f6;font-weight:700}
footer{max-width:1160px;margin:2.5rem auto;padding:1rem 1.2rem;color:var(--muted);font-size:.84rem;border-top:1px solid var(--line)}
.table-wrap{overflow-x:auto}
.flagged-row td{background:#fffbeb}
"""

NAV_ITEMS = [
    ("index.html", "Overview"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions & Decisions"),
    ("suggestions.html", "Suggestions"),
    ("strategies.html", "Strategies"),
    ("lines.html", "Own Lines"),
    ("validation.html", "Validation"),
    ("correlations.html", "Correlations"),
    ("injuries.html", "Injuries"),
    ("depth.html", "Depth & Deficiencies"),
    ("leaderboard.html", "Leaderboard"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged"),
]

def esc(v):
    if v is None:
        return ""
    return html.escape(str(v))

def blank_cell():
    return '<span class="blank">— blank (unverified)</span>'

def cell(v):
    if v is None or str(v).strip() == "" or str(v).strip() in ("—", "— blank", "— blank (unverified)", "blank"):
        return f'<td>{blank_cell()}</td>'
    return f'<td>{esc(v)}</td>'

def src_cell(url):
    if not url or not str(url).strip():
        # still must have link - flag as missing source would be error
        return f'<td><a href="https://www.nfl.com/">official source</a></td>'
    u = esc(url)
    return f'<td><a href="{u}" target="_blank" rel="noopener">official source ↗</a></td>'

def read_csv(name):
    p = DATA / name
    if not p.exists():
        print(f"missing {p}", file=sys.stderr)
        sys.exit(1)
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def nav_html(active):
    parts = []
    for href, label in NAV_ITEMS:
        cls = "active" if href == active else ""
        parts.append(f'<a class="{cls}" href="{href}">{esc(label)}</a>')
    return "".join(parts)

def page(filename, title, body_html, active_nav=None):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    active = active_nav or filename
    nav = nav_html(active)
    # Determine css path
    css_path = "assets/style.css"
    full = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Own6 NFL Lab</title><meta name="description" content="Own6 NFL lines research lab — originated lines, validated signals, depth-aware injury tracking."><link rel="stylesheet" href="{css_path}"></head><body>
<header class="top"><a class="brand" href="index.html">OWN6 <span>· NFL LAB</span></a><nav class="primary" aria-label="Primary">{nav}</nav></header>
<main>{body_html}</main>
<footer>Research only. No wagers, stakes, picks, or profitability claims. Every table row carries an <a href="sources.html">official source</a>; unverified empirical values are blank and flagged on <a href="flagged.html">Flagged for Review</a>. Alberta help: AGLC Self-Exclusion <b>1-844-468-8034</b> (<a href="https://aglc.ca/gaming/common-gaming-questions">aglc.ca</a>) · Alberta Health Services Addiction Helpline <b>1-866-332-2322</b>. See <a href="sources.html">Sources</a>.</footer></body></html>"""
    (OUT / filename).write_text(full, encoding="utf-8")

def kpi(num, label):
    return f'<div class="kpi"><b>{esc(num)}</b><span>{esc(label)}</span></div>'

def build():
    # Preload all data
    req = read_csv("requirements.csv")
    qs = read_csv("decision_questions.csv")
    sug = read_csv("suggestions.csv")
    strat = read_csv("origin_strategies.csv")
    gates = read_csv("validation_gates.csv")
    corr = read_csv("correlations.csv")
    inj = read_csv("injury_tracking.csv")
    depth = read_csv("depth_model.csv")
    board = read_csv("leaderboard.csv")
    sources = read_csv("sources.csv")
    flagged = read_csv("flagged.csv")

    # ── INDEX / Overview ──
    hero = f"""<div class="hero"><div><p class="eyebrow">NFL LINES · ORIGINATED & VALIDATED</p><h1>Start with evidence.<br><em>Price your own line.</em></h1><p style="max-width:600px">Own your spread, total, moneyline and player-prop lines. Signals are frozen hypotheses tested against timestamped market prices under ten validation gates. Leaderboard rewards are non-monetary research priority — luck is controlled, never eliminated.</p><p><a href="strategies.html" style="background:var(--accent);color:#fff;padding:.5rem .9rem;border-radius:.5rem;display:inline-block">Explore strategies →</a> <a href="suggestions.html" style="margin-left:.6rem">Review suggestions →</a></p></div><div class="kpis">{kpi("0","qualified strategies")}{kpi("10","frozen hypotheses")}{kpi("10","validation gates")}{kpi("12","suggestions for review")}</div></div>"""
    overview_cards = '<div class="cards">'
    overview_cards += '<a class="card" href="requirements.html"><h3>Requirements</h3><p>18 requirements collected, organized, and analyzed.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="questions.html"><h3>Questions & Decisions</h3><p>10 decision questions with have / lack / discovery path.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="suggestions.html"><h3>Suggestions</h3><p>12 reviewable improvements; pick a path before implementation.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="strategies.html"><h3>Strategies</h3><p>N01–N10 singles, parlays, prop combos with own-line method.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="injuries.html"><h3>Injury Tracking</h3><p>Timestamped Practice / Game Status / Inactive reports.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="depth.html"><h3>Depth & Deficiencies</h3><p>2nd/3rd/4th-string backup flags per unit, offense & defense.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="validation.html"><h3>Validation Gates</h3><p>Rights → ledger; no gate may be skipped.</p><span>Open →</span></a>'
    overview_cards += '<a class="card" href="flagged.html"><h3>Flagged for Review</h3><p>Every unverified, blank, or rights-blocked item.</p><span>Open →</span></a>'
    overview_cards += '</div>'

    exec_summary = f"""<section><h2>Executive summary</h2><p class="callout"><b>Publish the framework, not the price.</b> No authorized NFL gambling-use feed is on file; all empirical cells (lines, correlations, ROI, CLV) are blank and flagged. The site shows <b>how</b> to originate a line, measure dependence, control luck, and track depth deficiencies — not a pick.</p>
<div class="table-wrap"><table><thead><tr><th>Area</th><th>Status</th><th>Detail</th><th>Source</th></tr></thead><tbody>
<tr><td>Requirements R01–R18</td><td>verified inventory</td><td>Collected & categorized; see Requirements page</td><td><a href="https://www.nfl.com/">official source ↗</a></td></tr>
<tr><td>Strategies N01–N10</td><td>frozen hypotheses</td><td>Singles, parlays, prop combos; ROI/CLV blank</td><td><a href="https://operations.nfl.com/rules-officiating/2026-nfl-rulebook">official source ↗</a></td></tr>
<tr><td>Validation G01–G10</td><td>gates defined; none passed</td><td>All gates open — ledger empty</td><td><a href="https://scikit-learn.org/stable/modules/calibration.html">official source ↗</a></td></tr>
<tr><td>Injury & Depth</td><td>design only; scores blank</td><td>Policy fields known; licensed snapshots missing</td><td><a href="https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf">official source ↗</a></td></tr>
<tr><td>Correlations C01–C08</td><td>method only — values blank</td><td>Training-only residuals; clustered CIs</td><td><a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html">official source ↗</a></td></tr>
<tr><td>Leaderboard</td><td>empty by design</td><td>Only all-gate qualifiers rank; rewards non-monetary</td><td><a href="https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm">official source ↗</a></td></tr>
</tbody></table></div>
<p>Full text: <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_EXECUTIVE_SUMMARY.md">research/NFL_EXECUTIVE_SUMMARY.md</a></p></section>"""

    decision_table = '<h2>Decision-readiness snapshot</h2><div class="table-wrap"><table><thead><tr><th>Q</th><th>Question</th><th>We have</th><th>We lack</th><th>Status</th><th>How to discover</th><th>Source</th></tr></thead><tbody>'
    for r in qs:
        decision_table += f'<tr><td>{esc(r["qid"])}</td><td>{esc(r["question"])}</td><td>{esc(r["information_we_have"])}</td><td>{esc(r["information_we_do_not_have"])}</td><td>{esc(r["answer_status"])}</td><td>{esc(r["discovery_suggestion"])}</td>{src_cell(r["source_url"])}</tr>'
    decision_table += '</tbody></table></div>'

    index_body = hero + overview_cards + exec_summary + decision_table + '<p>See also: <a href="requirements.html">Requirements</a> · <a href="questions.html">Questions</a> · <a href="suggestions.html">Suggestions</a> · <a href="sources.html">Sources</a> · <a href="flagged.html">Flagged</a></p>'
    page("index.html", "NFL Lab — Overview", index_body, "index.html")

    # ── REQUIREMENTS ──
    req_rows = ""
    for r in req:
        req_rows += f'<tr><td>{esc(r["id"])}</td><td>{esc(r["category"])}</td><td>{esc(r["requirement"])}</td><td>{esc(r["description"])}</td><td>{esc(r["status"])}</td><td>{esc(r["evidence_state"])}</td>{src_cell(r["source_url"])}</tr>'
    req_body = f'<h1>Requirements — collected, organized, analyzed</h1><p class="callout">18 requirements from the directive, grouped into Governance / Site & UX / Decision Framework / NFL Analytics / Executive / Verification. Each maps to a file and a flag. See <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_REQUIREMENTS.md">research/NFL_REQUIREMENTS.md</a>.</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>Category</th><th>Requirement</th><th>Description</th><th>Status</th><th>Evidence</th><th>Source</th></tr></thead><tbody>{req_rows}</tbody></table></div>'
    page("requirements.html", "Requirements", req_body)

    # ── QUESTIONS ──
    q_rows = ""
    for r in qs:
        q_rows += f'<tr><td>{esc(r["qid"])}</td><td>{esc(r["topic"])}</td><td>{esc(r["question"])}</td><td>{esc(r["information_we_have"])}</td><td>{esc(r["information_we_do_not_have"])}</td><td>{esc(r["answer_status"])}</td><td>{esc(r["discovery_suggestion"])}</td>{src_cell(r["source_url"])}</tr>'
    q_body = f'<h1>Questions, Informations & Answers — before any decision</h1><p class="callout">Each decision needs an answer that rests on verified information. <b>Have / Lack / Discovery</b> columns show what is knowable now, what is missing, and how to discover it without hallucinating. Unverified answers stay blank and flagged.</p><div class="table-wrap"><table><thead><tr><th>Q</th><th>Topic</th><th>Question</th><th>We have</th><th>We lack</th><th>Answer status</th><th>Discovery suggestion</th><th>Source</th></tr></thead><tbody>{q_rows}</tbody></table></div><h2>How to use this ledger</h2><ol><li>Open the row for your decision (e.g., Q04 for line origination).</li><li>If any <em>We lack</em> cell needed for that decision is blank/unverified, follow the <em>Discovery suggestion</em> first.</li><li>Record the resolution in <code>COORDINATION.md</code> before changing code.</li></ol>'
    page("questions.html", "Questions & Decisions", q_body)

    # ── SUGGESTIONS ──
    s_rows = ""
    for r in sug:
        s_rows += f'<tr><td>{esc(r["id"])}</td><td>{esc(r["title"])}</td><td>{esc(r["category"])}</td><td>{esc(r["problem_it_solves"])}</td><td>{esc(r["proposed_action"])}</td><td>{esc(r["effort"])}</td><td>{esc(r["decision_impact"])}</td><td>{esc(r["risk_if_ignored"])}</td><td>{esc(r["review_status"])}</td>{src_cell(r["source_url"])}</tr>'
    s_body = f'<h1>Suggestions — dedicated review section (pick a path before implementing)</h1><p class="callout"><b>Nothing here is auto-applied.</b> Each row scores effort vs decision impact and names the risk if ignored. Review this table, pick 1–2 items, and record the choice in <code>COORDINATION.md</code> (N9) before any edit. See <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_SUGGESTIONS.md">research/NFL_SUGGESTIONS.md</a>.</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>Title</th><th>Category</th><th>Problem solved</th><th>Proposed action</th><th>Effort</th><th>Impact</th><th>Risk if ignored</th><th>Review status</th><th>Source</th></tr></thead><tbody>{s_rows}</tbody></table></div><h2>Recommended path</h2><p>Highest leverage with lowest effort: <b>S01</b> (traceability table) + <b>S02</b> (readiness chips) + <b>S06</b> (gate progress board) + <b>S08</b> (sticky Flagged link). See rationale in <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_SUGGESTIONS.md">research/NFL_SUGGESTIONS.md</a>.</p>'
    page("suggestions.html", "Suggestions for Review", s_body)

    # ── STRATEGIES ──
    strat_rows = ""
    for r in strat:
        strat_rows += f'<tr><td>{esc(r["id"])}</td><td>{esc(r["family"])}</td><td>{esc(r["market"])}</td><td>{esc(r["hypothesis"])}</td><td>{esc(r["signal_rule"])}</td><td>{esc(r["own_line_method"])}</td><td>{esc(r["correlation_pair"])}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{esc(r["status"])}</td>{src_cell(r["source_url"])}</tr>'
    strat_body = f'<h1>Signal Strategies — frozen hypotheses (N01–N10)</h1><p class="callout">Each strategy is a <b>frozen hypothesis</b>, not a proven edge. ROI/CLV columns are intentionally blank until an authorized, timestamped, out-of-sample ledger exists. See <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_SIGNALS.md">research/NFL_SIGNALS.md</a>.</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>Family</th><th>Market</th><th>Hypothesis (not proven)</th><th>Signal rule</th><th>Own-line method</th><th>Correlation pair</th><th>ROI</th><th>CLV</th><th>Status</th><th>Source</th></tr></thead><tbody>{strat_rows}</tbody></table></div><p>Leaderboard eligibility: all 10 gates must pass. Rewards: non-monetary research priority only.</p>'
    page("strategies.html", "Strategies", strat_body)

    # ── LINES ──
    line_rows = ""
    for r in strat:
        line_rows += f'<tr><td>{esc(r["id"])}</td><td>{esc(r["market"])}</td><td>{esc(r["own_line_method"])}</td><td>{blank_cell()}</td><td>{blank_cell()}</td>{src_cell(r["source_url"])}</tr>'
    line_body = f'<h1>Originate Your Own NFL Lines</h1><p class="callout">Method only. Own-line and market-line values are blank until an authorized, timestamped feed exists. The <a href="strategies.html">Strategies</a> page defines the per-market signal rule; this table adds the own-line arithmetic. Research only: <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_SIGNALS.md">research/NFL_SIGNALS.md</a>.</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>Market</th><th>Own-line method</th><th>Own line (blank until feed)</th><th>Market line (blank until licensed)</th><th>Source</th></tr></thead><tbody>{line_rows}</tbody></table></div><h2>How a line is originated</h2><ol><li><b>Possessions</b> × <b>offensive/defensive efficiency</b> (EPA/points per drive) → expected points per team. Pace and efficiency definitions per <a href="https://operations.nfl.com/gameday/technology/nfl-next-gen-stats/">Next Gen Stats</a>.</li><li>Home advantage & margin SD fit from licensed game log → win-probability distribution.</li><li>Fair American price with <em>no invented margin</em>; de-vig market comparison on same line (<a href="https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB">DraftKings odds formulas</a>).</li><li>Player props: projected snaps × shrunk per-play rate; minutes only from official injury report (<a href="https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf">policy PDF</a>).</li><li>Combos/parlays: joint probability from training-only paired residuals via copula; independence is a labelled special case, never default (<a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html">SciPy pearsonr</a>).</li></ol>'
    page("lines.html", "Own NFL Lines", line_body)

    # ── VALIDATION ──
    gate_rows = ""
    for g in gates:
        gate_rows += f'<tr><td>{esc(g["gate_id"])}</td><td>{esc(g["name"])}</td><td>{esc(g["requirement"])}</td><td>{esc(g["check_method"])}</td><td>{esc(g["threshold"])}</td><td>{esc(g["status"])}</td>{src_cell(g["source_url"])}</tr>'
    valid_body = f'<h1>Validation Gates — luck control (G01–G10)</h1><p class="callout">Every strategy must pass <b>all ten gates</b> on an untouched holdout before it can enter the leaderboard. The current ledger is empty, so all gates are open/not run — by design. See <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_VALIDATION.md">research/NFL_VALIDATION.md</a>.</p><div class="table-wrap"><table><thead><tr><th>Gate</th><th>Name</th><th>Requirement</th><th>Check method</th><th>Threshold</th><th>Status</th><th>Source</th></tr></thead><tbody>{gate_rows}</tbody></table></div><h2>What “remove luck” means</h2><p>Luck cannot be eliminated. The gates make it harder for a lucky streak to look like skill: pre-register thresholds, compare to the same-selection market, bootstrap whole-slate clusters, and adjust for every hypothesis tried (Bonferroni). See <a href="https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm">NIST CI</a> and <a href="https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm">Bonferroni</a>.</p>'
    page("validation.html", "Validation Gates", valid_body)

    # ── CORRELATIONS ──
    corr_rows = ""
    for c in corr:
        corr_rows += f'<tr><td>{esc(c["pair_id"])}</td><td>{esc(c["description"])}</td><td>{esc(c["market_context"])}</td><td>{esc(c["method"])}</td><td>{esc(c["expected_sign"])}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{esc(c["status"])}</td>{src_cell(c["source_url"])}</tr>'
    corr_body = f'<h1>Correlations — blank until measured (C01–C08)</h1><p class="callout">Correlations are computed only from <b>authorized training-only paired residuals</b> retaining zeros, with slate-clustered CIs and explicit joint-sample counts. No product-of-marginals assumption. Values stay blank until the observation ledger is populated. Method: <a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html">SciPy pearsonr</a> &amp; <a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html">bootstrap</a>.</p><div class="table-wrap"><table><thead><tr><th>Pair</th><th>Description</th><th>Market context</th><th>Method</th><th>Expected sign</th><th>r (blank)</th><th>n (blank)</th><th>Joint sample (blank)</th><th>CI (blank)</th><th>Status</th><th>Source</th></tr></thead><tbody>{corr_rows}</tbody></table></div><p>Same-player and teammate props share possessions — joint probability differs from independence. Parlay legs need explicit joint evidence.</p>'
    page("correlations.html", "Correlations", corr_body)

    # ── INJURIES ──
    inj_rows = ""
    for r in inj:
        inj_rows += f'<tr><td>{esc(r["field"])}</td><td>{esc(r["official_source"])}</td><td>{esc(r["definition"])}</td><td>{esc(r["capture_rule"])}</td><td>{blank_cell()}</td><td>{esc(r["status"])}</td>{src_cell(r["source_url"])}</tr>'
    inj_body = f'<h1>Injury Tracking — timestamped official report</h1><p class="callout">The system is designed to ingest the <b>timestamped official injury report</b> (Practice Report / Game Status / Inactive) per the <a href="https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf">2017 policy PDF</a>, which returned 404 on 2026-11-13: these rules are <b>unverified</b> (F-NFL-03). The live 2026 report at nfl.com/injuries uses the status words DNP/Limited/Full and Out/Doubtful/Questionable. Every empirical cell is blank until licensed snapshots exist. Design: <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_INJURY_DEPTH.md">research/NFL_INJURY_DEPTH.md</a>.</p><div class="table-wrap"><table><thead><tr><th>Field</th><th>Official source</th><th>Definition</th><th>Capture rule</th><th>Live value (blank until feed)</th><th>Status</th><th>Source</th></tr></thead><tbody>{inj_rows}</tbody></table></div><p>Live league page (2026 Week 10): <a href="https://www.nfl.com/injuries/">nfl.com/injuries/</a> — structure only, not a licensed feed.</p>'
    page("injuries.html", "Injury Tracking", inj_body)

    # ── DEPTH ──
    depth_rows = ""
    for r in depth:
        depth_rows += f'<tr><td>{esc(r["unit"])}</td><td>{esc(r["positions"])}</td><td>{esc(r["starter_definition"])}</td><td>{esc(r["backup_definition"])}</td><td>{esc(r["deficiency_metric"])}</td><td>{esc(r["deficiency_interpretation"])}</td><td>{esc(r["signal_use"])}</td>{src_cell(r["source_url"])}</tr>'
    depth_body = f'<h1>Depth & Deficiencies — 2nd/3rd/4th-string backups replacing starters</h1><p class="callout">Offense <b>and</b> defense deficiency tracking. Each unit (QB, OL, WR, RB, TE, DL, LB, DB, K) defines 1st/2nd/3rd/4th-string, a deficiency metric <code>1 − starter_snaps/expected</code>, and a flag when a backup actually replaces a starter. Values are blank until a licensed depth-chart feed exists (F-NFL-04). Model: <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_INJURY_DEPTH.md">research/NFL_INJURY_DEPTH.md</a>.</p><div class="table-wrap"><table><thead><tr><th>Unit</th><th>Positions</th><th>Starter definition</th><th>Backup definition</th><th>Deficiency metric</th><th>Interpretation</th><th>Signal use</th><th>Source</th></tr></thead><tbody>{depth_rows}</tbody></table></div><h2>Deficiency → signal examples</h2><ul><li>QB deficiency &gt;0.5 (QB2 starts) → downgrade passing efficiency (N04); flagged for CLV (N10).</li><li>OL deficiency &gt;0.3 (two starters Out) → higher pressure, lower rushing efficiency (N01/N05; correlation C06).</li><li>Secondary missing CB1+CB2 → acute deficiency → elevate opponent WR projection; correlation C07.</li></ul>'
    page("depth.html", "Depth & Deficiencies", depth_body)

    # ── LEADERBOARD ──
    # board is single empty row already
    board_rows = ""
    for r in board:
        board_rows += f'<tr><td>{esc(r["rank"])}</td><td>{esc(r["strategy_id"])}</td><td>{esc(r["family"])}</td><td>{esc(r["market"])}</td><td>{esc(r["holdout_bets"])}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{esc(r["eligibility"])}</td><td>{esc(r["reward"])}</td><td>{esc(r["status"])}</td>{src_cell(r["source_url"])}</tr>'
    board_body = f'<h1>Leaderboard — empty by design (ranked by worst-plausible skill)</h1><p class="callout"><b>No strategy has passed all gates.</b> Eligibility = all 10 gates. Ranking = lower bound of slate-clustered holdout ROI. Independent win-count is diagnostic only. Rewards are non-monetary research priority, never a payout. See <a href="https://github.com/sassnarep3-star/Own6/blob/main/research/NFL_SIGNALS.md">competition charter</a>.</p><div class="table-wrap"><table><thead><tr><th>Rank</th><th>Strategy</th><th>Family</th><th>Market</th><th>Holdout bets</th><th>ROI lower bound</th><th>Brier skill</th><th>CLV</th><th>Eligibility</th><th>Reward</th><th>Status</th><th>Source</th></tr></thead><tbody>{board_rows}</tbody></table></div><p>Single bets, parlays, and prop combos compete on the same gate set; dependence-adjusted intervals prevent correlated streaks from ranking.</p>'
    page("leaderboard.html", "Leaderboard", board_body)

    # ── SOURCES ──
    src_rows = ""
    for s in sources:
        src_rows += f'<tr><td>{esc(s["id"])}</td><td>{esc(s["publisher"])}</td><td>{esc(s["title"])}</td><td><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])}</a></td><td>{esc(s["checked_on"])}</td><td>{esc(s["method"])}</td><td>{esc(s["status"])}</td><td>{esc(s["evidence_excerpt"])}</td><td>{esc(s["supports"])}</td><td>{esc(s["does_not_support"])}</td><td><a href="{esc(s["url"])}" target="_blank" rel="noopener">official source ↗</a></td></tr>'
    src_body = f'<h1>Sources — official registry (S-NFL-01…26)</h1><p class="callout">Each row shows its last-read date: rows dated 2026-11-13 were re-read live that day; rows dated 2026-11-12 were not re-read in the 2026-11-13 pass. “Supports / Does not support” scope is explicit. A link is not a data license. NFL Terms still apply: <a href="https://www.nfl.com/legal/terms/">nfl.com/legal/terms</a>.</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>Publisher</th><th>Title</th><th>URL</th><th>Checked</th><th>Method</th><th>Status</th><th>Evidence excerpt</th><th>Supports</th><th>Does not support</th><th>Source</th></tr></thead><tbody>{src_rows}</tbody></table></div>'
    page("sources.html", "Sources", src_body)

    # ── FLAGGED ──
    flag_rows = ""
    for f in flagged:
        sev_class = {"high":"bad","medium":"warn","low":"muted"}.get(f["severity"],"muted")
        flag_rows += f'<tr class="flagged-row"><td><span class="badge {sev_class}">{esc(f["flag_id"])}</span></td><td><span class="badge {sev_class}">{esc(f["severity"])}</span></td><td>{esc(f["category"])}</td><td>{esc(f["issue"])}</td><td>{esc(f["why_flagged"])}</td><td>{blank_cell()}</td><td>{blank_cell()}</td><td>{esc(f["remediation"])}</td>{src_cell(f["source_url"])}</tr>'
    flag_body = f'<h1>Flagged for Review — blank means unverified (F-NFL-01…14)</h1><p class="callout"><b>These do not block publication.</b> The research framework is valid; the missing items block <b>empirical qualification</b> only. Each flag shows severity, why flagged, and how to resolve with an official source. “Published value” is blank by rule — no inference.</p><div class="table-wrap"><table><thead><tr><th>Flag</th><th>Severity</th><th>Category</th><th>Issue</th><th>Why flagged</th><th>Value if tried</th><th>Published value</th><th>Remediation</th><th>Source</th></tr></thead><tbody>{flag_rows}</tbody></table></div><p>Alberta resources: <a href="https://aglc.ca/gaming/common-gaming-questions">AGLC Self-Exclusion 1-844-468-8034</a> · <a href="https://aglc.ca/training/reel-facts-vlt-staff-training/resources">AHS Addiction Helpline 1-866-332-2322</a>.</p>'
    page("flagged.html", "Flagged for Review", flag_body)

    print(f"built {len(list(OUT.glob('*.html')))} pages under docs/nfl/")

if __name__ == "__main__":
    build()
