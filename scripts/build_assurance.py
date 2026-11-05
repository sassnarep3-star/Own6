#!/usr/bin/env python3
"""Build the source-assurance dashboard from audited local artifacts.

No network collection or synthetic performance. Unavailable empirical values are
blank and flagged. Every table row carries an official source/reference link.
"""
from __future__ import annotations

import csv
import html
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nba_lab.registry import STRATEGIES  # noqa: E402

ASSURANCE = ROOT / "data" / "assurance"
EMPIRICAL = ROOT / "data" / "empirical"
OUT = ROOT / "docs" / "assurance"
REPO = "https://github.com/sassnarep3-star/Own6"
PAGES = [
    ("index.html", "Overview"), ("strategies.html", "Strategies"), ("lines.html", "Lines & props"),
    ("correlations.html", "Correlations"), ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Validation gates"), ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"), ("repo-audit.html", "Repo audit"),
]


def esc(value) -> str:
    return "" if value is None else html.escape(str(value))


def link(url: str, label: str) -> str:
    if not url:
        return '<span class="blank">unverified</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def badge(status: str) -> str:
    cls = {"pass": "ok", "verified_direct": "ok", "resolved_upstream": "ok", "resolved_in_session": "ok",
           "fail": "bad", "high": "bad", "blocked": "warn", "needs_review": "warn", "unverified": "warn",
           "partial": "warn", "open": "warn", "not_run": "muted"}.get(status, "muted")
    return f'<span class="badge {cls}">{esc(status.replace("_", " "))}</span>'


def blank(note: str = "blank · unverified") -> str:
    return f'<span class="blank">{esc(note)}</span>'


def table(headers: list[str], rows: list[list[str]], ident: str = "") -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<div class="table-wrap"><table id="{esc(ident)}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def page(filename: str, title: str, body: str) -> None:
    nav = "".join(f'<a href="{href}"{" aria-current=page" if href == filename else ""}>{esc(label)}</a>' for href, label in PAGES)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own6 Assurance</title><link rel="stylesheet" href="assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header><a class="brand" href="index.html">OWN6 <span>/ Assurance</span></a><nav aria-label="Assurance navigation">{nav}</nav></header>
<main id="main"><h1>{esc(title)}</h1>{body}</main>
<footer>Evidence-first research only. No wagers, stakes, picks or payouts. Official source links are not data licenses. Unverified values stay blank.</footer>
</body></html>"""
    (OUT / filename).write_text(doc, encoding="utf-8")


CSS = """
:root{--bg:#f5f7fb;--panel:#fff;--ink:#172033;--muted:#5b6474;--line:#dfe4ee;--accent:#1d4ed8;--ok:#0f766e;--warn:#b45309;--bad:#b91c1c}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--accent)}a:hover{text-decoration:underline}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;z-index:10}
header{background:#fff;border-bottom:1px solid var(--line);padding:.85rem 1.25rem;display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;position:sticky;top:0;z-index:5}
.brand{font-weight:800;letter-spacing:.04em;color:var(--ink);text-decoration:none}.brand span{color:var(--muted);font-weight:600}
nav{display:flex;gap:.25rem;flex-wrap:wrap}nav a{padding:.35rem .6rem;border-radius:.5rem;text-decoration:none;font-size:.9rem;color:var(--muted)}nav a:hover,nav a[aria-current]{background:#eef2ff;color:var(--accent)}
main{max-width:1180px;margin:0 auto;padding:1.75rem 1.25rem 3rem}h1{font-size:1.75rem;margin:.25rem 0 1rem}h2{font-size:1.2rem;margin:2rem 0 .75rem}p{max-width:80ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.85rem;margin:1.25rem 0}.card{background:var(--panel);border:1px solid var(--line);border-radius:.85rem;padding:1rem}.card .num{font-size:1.7rem;font-weight:800}.card .label{color:var(--muted);font-size:.85rem}
.callout{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:.65rem;padding:.9rem 1rem;margin:1rem 0}.callout.warn{border-left-color:var(--warn)}
.table-wrap{overflow:auto;background:#fff;border:1px solid var(--line);border-radius:.75rem;margin:.85rem 0 1.5rem}table{width:100%;border-collapse:collapse;font-size:.88rem;min-width:720px}th,td{border-bottom:1px solid var(--line);padding:.55rem .7rem;text-align:left;vertical-align:top}th{background:#f1f4f9;position:sticky;top:0;font-weight:700}tr:last-child td{border-bottom:0}tbody tr:hover{background:#f8fafc}
.badge{display:inline-block;padding:.12rem .5rem;border-radius:999px;font-size:.75rem;font-weight:700;white-space:nowrap}.badge.ok{background:#ccfbf1;color:var(--ok)}.badge.warn{background:#fef3c7;color:var(--warn)}.badge.bad{background:#fee2e2;color:var(--bad)}.badge.muted{background:#eef1f5;color:var(--muted)}.blank{color:var(--muted)}
code{background:#eef1f5;padding:.1rem .35rem;border-radius:.3rem;font-size:.85em}footer{max-width:1180px;margin:0 auto;padding:1.25rem;color:var(--muted);font-size:.85rem;border-top:1px solid var(--line)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem}.small{font-size:.85rem;color:var(--muted)}
@media(max-width:700px){header{position:static}main{padding:1.25rem .9rem}h1{font-size:1.45rem}}
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    report = json.loads((EMPIRICAL / "report.json").read_text(encoding="utf-8"))
    summary = json.loads((ASSURANCE / "summary.json").read_text(encoding="utf-8"))
    sources = load_csv(ASSURANCE / "sources.csv")
    findings = load_csv(ASSURANCE / "findings.csv")
    row_audit = load_csv(ASSURANCE / "row_audit.csv")
    inventory = load_csv(ASSURANCE / "inventory.csv")
    legacy = [r for r in row_audit if r["category"] == "legacy_data"]
    open_findings = [r for r in findings if r["status"] == "open"]

    overview = f"""
<p class="callout"><strong>No authorized betting-use data feed is configured.</strong> Current lines, correlations, edge, ROI and CLV are blank. The leaderboard is empty because no strategy has passed the validation gates. This dashboard separates official source reads, reproducible calculations and unverified historical claims.</p>
<p class="callout"><strong>Final integration evidence, 2026-11-05.</strong> All 15 November 2 final scores were freshly re-read on their official NBA game pages and matched. The 30-team W-L table remains a <strong>2026-11-03 snapshot</strong>: the live standings have advanced and are not presented as current. See the <a href="../verify/index.html">dated verification ledger</a>, <a href="../review/verification.html">direct-read log V28–V54</a>, <a href="../verified/flagged.html">public flags F28–F29</a> and {link(REPO + '/blob/main/audit/FINAL_INTEGRATION_REVIEW_2026-11-05.md', 'integration audit')}. Verifying historical scores does not verify odds, statistics rights or betting skill.</p>
<div class="cards">
<div class="card"><div class="num">{report['n_observations']}</div><div class="label">Authorized observations</div></div>
<div class="card"><div class="num">{report['n_qualified']}</div><div class="label">Qualified strategies</div></div>
<div class="card"><div class="num">{len(STRATEGIES)}</div><div class="label">Frozen candidates</div></div>
<div class="card"><div class="num">{len(report['strategies'][0]['gates'])}</div><div class="label">Validation gates</div></div>
<div class="card"><div class="num">{len(legacy)}</div><div class="label">Legacy records unverified</div></div>
<div class="card"><div class="num">{len(open_findings)}</div><div class="label">Open review findings</div></div>
</div>
<h2>Executive decision</h2>
<p>Publish the research framework and audit trail; do not publish a current betting line or reward winner. Skill cannot be proven without authorized, timestamped, out-of-sample evidence. Luck cannot be eliminated, only accounted for through dependence-aware uncertainty, multiplicity control and frozen preregistration.</p>
{table(['Evidence state','Value','Source'], [
    ['Authorized observations', str(report['n_observations']), link(REPO + '/blob/main/data/empirical/report.csv', 'Project report')],
    ['Qualified strategies', str(report['n_qualified']), link(REPO + '/blob/main/data/empirical/report.csv', 'Project report')],
    ['Legacy records unverified', str(len(legacy)), link(REPO + '/blob/main/data/assurance/row_audit.csv', 'Row audit')],
    ['Direct official source reads', str(sum(s['status'] == 'verified_direct' for s in sources)), link(REPO + '/blob/main/data/assurance/sources.csv', 'Source register')],
], 'evidence-state')}
<div class="grid2">
<div class="card"><h3>Research</h3><p><a href="strategies.html">Candidate signals</a> · <a href="lines.html">Line origination contract</a> · <a href="correlations.html">Joint dependence</a> · <a href="validation.html">Gates</a></p></div>
<div class="card"><h3>Evidence</h3><p><a href="sources.html">Official sources</a> · <a href="flagged.html">Flagged for Review</a> · <a href="repo-audit.html">Full row audit</a> · <a href="leaderboard.html">Leaderboard</a></p></div>
<div class="card"><h3>Preserved archives</h3><p><a href="../hub/index.html">Data hub</a> · <a href="../lab/overview.html">Empirical lab</a> · <a href="../index.html">Earlier landing</a> · <a href="../verified/index.html">Verified section</a></p></div>
</div>
<h2>What changed in this session</h2>
<ul>
<li>Current-tree structural scan and record-level provenance audit; file checksums are not fact certification.</li>
<li>Empirical engine hardened: artifact-bound audit evidence, slate clustering, strict training residuals, de-vigged CLV sidecar, joint-sample combo gates and family-wise qualification tests.</li>
<li>Concurrent upstream repairs to the legacy odds formula, root landing and lab tables are preserved and credited.</li>
</ul>
<p class="small">Primary policy source: {link('https://www.nba.com/termsofuse#nba-statistics', 'NBA Terms of Use §9')}. Full executive summary: {link(REPO + '/blob/main/EXECUTIVE_SUMMARY.md', 'repository summary')}.</p>
"""
    page("index.html", "NBA research assurance", overview)

    strategy_rows = []
    for s, r in zip(STRATEGIES, report["strategies"]):
        strategy_rows.append([
            esc(s["id"]), esc(s["name"]), esc(s["category"]), esc(s["signal"]), esc(s["risk"]),
            blank("not qualified"), link(s["source_url"], "NBA glossary"),
            link("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"),
        ])
    page("strategies.html", "Strategy candidates", f"""
<p class="callout">Six frozen hypotheses cover singles, player props, same-game prop combos and a two-game parlay. They are specifications, not verified edges. Adding a candidate after seeing holdout results requires a new preregistered family and holdout.</p>
{table(['ID','Candidate','Category','Signal hypothesis','Main risk','Empirical result','Definition source','Feature context'], strategy_rows, 'strategies')}
<p>Detailed rationale and official references: {link(REPO + '/blob/main/research/SIGNALS.md', 'research/SIGNALS.md')}.</p>
""")

    line_rows = [
        ["Moneyline", "Margin distribution → win probability → fair decimal/American price", "Licensed prior-game features; same-side market price", blank(), link("https://www.nba.com/stats/help/glossary", "NBA glossary"), link("https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB", "Odds formulas")],
        ["Spread", "Fair home spread = −expected home margin; cover probability from training residuals", "Handicap, both-side prices, push settlement", blank(), link("https://sportsbook.draftkings.com/help/how-to-bet-spread", "Spread rules"), link("https://www.nba.com/stats/help/glossary", "NBA glossary")],
        ["Total", "Projected possessions × matchup efficiencies; residual total distribution", "Pace, efficiency, availability, total and prices", blank(), link("https://www.nba.com/stats/help/glossary", "NBA glossary"), link("https://sportsbook.draftkings.com/help/how-to-bet-over-under", "Over/under")],
        ["Player prop", "Projected minutes × shrunk scoring rate; empirical residual over probability", "Participation history, line, price, DNP settlement", blank(), link("https://www.nba.com/stats/help/glossary", "NBA glossary"), link("https://official.nba.com/nba-injury-report-2026-27-season/", "Injury policy")],
        ["Prop combo", "Direct paired joint hit frequency; no default independence", "Paired residuals, combo quote, provider permission", blank(), link("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "Pearson/phi"), link("https://www.nba.com/termsofuse#nba-statistics", "Rights gate")],
        ["Parlay", "Joint win probability plus executable combo price", "Binary joint sample, slate cluster, parlay rules", blank(), link("https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator", "Parlay calculator"), link("https://www.nba.com/termsofuse#nba-statistics", "Rights gate")],
    ]
    page("lines.html", "Line origination and props", f"""
<p class="callout warn">No current line is originated because no authorized feature/odds ledger exists. The methods below are contracts for future authorized research, not picks. No manual statistics entry is requested.</p>
{table(['Market','Fair-line method','Required authorized inputs','Current line','Method source','Policy/settlement source'], line_rows, 'lines')}
<p>Protocol: {link(REPO + '/blob/main/research/VALIDATION_v2.md', 'validation protocol v2')}.</p>
""")

    corr_rows = []
    for c in report["correlations"]:
        corr_rows.append([esc(c["id"]), esc(c["leg_a"]), esc(c["leg_b"]), esc(c["scope"]), blank(), blank(), blank(), badge(c["status"]), link(c["source_url"], "Rights / method reference")])
    page("correlations.html", "Correlation and joint dependence", f"""
<p class="callout">Estimates require strict training-only paired residuals with official provenance, explicit clusters and a clustered interval. Zero residuals are retained. Missing evidence is not independence. Historical legacy correlations are flagged, not promoted.</p>
{table(['Pair','Leg A','Leg B','Scope','Estimate','n','Clustered interval','Status','Source'], corr_rows, 'correlations')}
<p>Method: {link(REPO + '/blob/main/research/VALIDATION_v2.md', 'validation protocol v2')} · {link('https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html', 'SciPy Pearson reference')}.</p>
""")

    if report["leaderboard"]:
        leader_rows = [[str(r["rank"]), esc(r["strategy_id"]), esc(r["name"]), esc(r["score_roi_lower"]), link(r["source_url"], "Source")] for r in report["leaderboard"]]
    else:
        leader_rows = [[blank("—"), blank("no strategy qualified"), blank(), blank(), link(REPO + "/blob/main/data/empirical/report.csv", "Project report"), link("https://www.nba.com/stats/help/glossary", "NBA glossary")]]
    page("leaderboard.html", "Skill leaderboard", f"""
<p class="callout">Only all-gate qualifiers are ranked, by the lower bound of slate-clustered holdout ROI. Rewards are non-monetary research priority only. A high win rate or small-sample heater cannot win. No payouts or stakes are distributed.</p>
{table(['Rank','Strategy','Name','ROI lower bound','Result source','Definition source'], leader_rows, 'leaderboard')}
<p>Status: {badge(report['status'])}. Qualification requires {link(REPO + '/blob/main/research/VALIDATION_v2.md', 'all ten gates')}.</p>
""")

    gate_rows = [[esc(g["id"]), esc(g["name"]), badge(g["status"]), esc(g["reason"]), link(g["source_url"], "Official reference")] for g in report["strategies"][0]["gates"]]
    page("validation.html", "Validation gates", f"""
<p class="callout">Luck cannot be removed. These gates reduce false discoveries by requiring rights, provenance, chronology, sample/precision, market-relative scoring, post-vig ROI, comparable CLV, multiplicity control, joint dependence and an audited frozen ledger.</p>
{table(['Gate','Name','Status','Reason','Source'], gate_rows, 'gates')}
<p>Sample floors are policy minima, not a power guarantee. Bootstrap p-values are approximate. Full protocol: {link(REPO + '/blob/main/research/VALIDATION_v2.md', 'research/VALIDATION_v2.md')}.</p>
""")

    source_rows = [[esc(s["id"]), esc(s["publisher"]), esc(s["title"]), link(s["url"], "Official source"), badge(s["status"]), esc(s["supports"]), esc(s["does_not_support"])] for s in sources]
    page("sources.html", "Official source register", f"""
<p class="callout">Direct reads are separated from partial reads. A source supports only the scope listed; it does not verify an unrelated numeric claim or grant a data license. Checked {esc(sources[0]['checked_on'])}.</p>
{table(['ID','Publisher','Title','Source','Read status','Supports','Does not support'], source_rows, 'sources')}
""")

    finding_rows = [[esc(f["id"]), badge(f["severity"]), esc(f["file"]), esc(f["lines"]), esc(f["finding"]), esc(f["detail"]), esc(f["action"]), badge(f["status"]), link(f["source_url"], "Reference"), link(f["code_url"], "Code record")] for f in findings]
    by_file = Counter(r["file"] for r in legacy)
    legacy_summary = [[esc(file), str(count), blank("unverified"), link("https://www.nba.com/termsofuse#nba-statistics", "NBA data policy"), link(f"{REPO}/blob/main/{file}", "Repository record")] for file, count in sorted(by_file.items())]
    page("flagged.html", "Flagged for Review", f"""
<p class="callout warn">These items do not block publication of the research framework. They block empirical qualification and prevent unverified values from being presented as facts. No value is inferred to fill a gap.</p>
<h2>Review findings</h2>
{table(['ID','Severity','File','Lines','Finding','Detail','Action / disposition','Status','Official reference','Code record'], finding_rows, 'findings')}
<h2>Legacy data records still unverified</h2>
<p>{len(legacy)} legacy records remain unverified in this review. The full row-level ledger is on the <a href="repo-audit.html">Repo audit</a> page.</p>
{table(['File','Records','Value status','Official scope reference','Repository record'], legacy_summary, 'legacy-summary')}
""")

    inventory_rows = [[esc(r["path"]), esc(r["lines"]), esc(r["sha256"][:16] + "…"), esc(r["kind"]), link(r["source_url"], "Repository source")] for r in inventory]
    audit_rows = [[esc(r["file"]), esc(r["row"]), esc(r["category"]), esc(r["record_id"]), badge(r["value_verification"]), esc(r["review_note"]), link(r["official_scope_reference"], "Official scope reference"), link(r["record_url"], "Repository record")] for r in row_audit]
    page("repo-audit.html", "Repository audit ledger", f"""
<p class="callout">Every non-generated tracked text file was structurally scanned line by line and inventoried with a SHA-256 digest. Every legacy data record was reviewed for provenance. A checksum or URL is not external fact certification. Baseline: <code>{esc(summary['baseline_commit'])}</code>.</p>
<h2>File inventory</h2>
{table(['File','Lines','SHA-256 prefix','Kind','Source'], inventory_rows, 'inventory')}
<h2>Record-level provenance review</h2>
{table(['File','Row','Category','Record','Value status','Review note','Official scope reference','Repository record'], audit_rows, 'row-audit')}
""")
    print(f"Built {len(PAGES)} assurance pages under docs/assurance/")


if __name__ == "__main__":
    main()
