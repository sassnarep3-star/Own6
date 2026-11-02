#!/usr/bin/env python3
"""Build the empirical research dashboard from data/empirical/*.json and report.json.

Output is isolated under docs/lab/ so existing pages and publisher configuration are
untouched. No synthetic data is emitted; unavailable values are blank and flagged.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "empirical"
OUT = ROOT / "docs" / "lab"


def esc(value) -> str:
    if value is None or value == "":
        return ""
    return html.escape(str(value))


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def link(url, label):
    if not url:
        return ""
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'


def badge(status: str) -> str:
    cls = {"pass": "ok", "fail": "bad", "blocked": "warn", "not_run": "muted", "unverified": "warn", "needs_review": "warn", "verified": "ok"}.get(status, "muted")
    return f'<span class="badge {cls}">{esc(status)}</span>'


def cell(value):
    if value is None or value == "":
        return '<span class="blank">blank · unverified</span>'
    if isinstance(value, float):
        return f"{value:.6g}"
    return esc(value)


def page(title: str, body: str, nav: str, css_src: str = "assets/style.css") -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Own6</title><link rel="stylesheet" href="{css_src}"></head><body><header><a class="brand" href="overview.html">Own6 · Empirical NBA Lab</a><nav>{nav}</nav></header><main>{body}</main><footer>Research only. No wagers, stakes, or betting advice. No fabricated or synthetic data in the report.</footer></body></html>"""
    (OUT / f"{title.lower().replace(' ', '-').replace('—','')}.html").write_text(html_doc, encoding="utf-8")


def table(head: list[str], rows: list[list[str]], cls: str = "") -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in head)
    body = "".join(f"<tr>{''.join(td) for td in r}</tr>" for r in rows)
    return f'<table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def build_css() -> None:
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(""":root{--bg:#f7f8fa;--ink:#1f2933;--muted:#6b7280;--line:#e5e7eb;--accent:#0b5fff;--ok:#0a7d4f;--warn:#b45309;--bad:#b91c1c}*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--ink)}header{display:flex;justify-content:space-between;align-items:center;gap:2rem;padding:.9rem 1.4rem;background:#fff;border-bottom:1px solid var(--line)}.brand{font-weight:700;color:var(--ink);text-decoration:none}nav a{margin-left:1rem;font-size:.92rem;color:var(--accent);text-decoration:none}main{max-width:1080px;margin:2rem auto;padding:0 1.4rem}footer{max-width:1080px;margin:3rem auto;padding:1rem 1.4rem;color:var(--muted);font-size:.85rem}table{width:100%;border-collapse:collapse;margin:1rem 0;background:#fff;font-size:.92rem}th,td{border:1px solid var(--line);padding:.5rem .7rem;text-align:left;vertical-align:top}th{background:#f1f3f6}.badge{display:inline-block;padding:.1rem .5rem;border-radius:.4rem;font-size:.78rem;font-weight:600}.badge.ok{background:#e6f4ea;color:var(--ok)}.badge.bad{background:#fde8e8;color:var(--bad)}.badge.warn{background:#fef3c7;color:var(--warn)}.badge.muted{background:#eef0f2;color:var(--muted)}.blank{color:var(--muted)}.callout{border-left:3px solid var(--accent);background:#fff;padding:.8rem 1rem;margin:1rem 0}h1{font-size:1.6rem}h2{font-size:1.15rem;margin-top:2rem}code{background:#eef0f2;padding:.1rem .35rem;border-radius:.3rem}""", encoding="utf-8")


def main() -> None:
    build_css()
    report = load("report.json")
    sources = load("sources.json")
    findings = list(csv.DictReader((DATA / "repo_findings.csv").open(newline="", encoding="utf-8")))
    audit = list(csv.DictReader((DATA / "source_audit.csv").open(newline="", encoding="utf-8")))
    inventory = list(csv.DictReader((DATA / "repo_inventory.csv").open(newline="", encoding="utf-8")))
    strategies = report["strategies"]

    nav = "".join(f'<a href="{name.lower().replace(" ", "-")}.html">{esc(name)}</a>' for name in ["Overview", "Strategies", "Methodology", "Correlations", "Leaderboard", "Sources", "Findings", "Flagged"])

    # Overview
    overview = f"""<h1>Empirical NBA Lab</h1>
<p class="callout">This is a research-first project for originating NBA lines and testing whether any strategy beats the market after legal rights, provenance, chronology, proper scoring, clustered ROI, CLV, dependence and preregistration gates. <strong>No licensed NBA observation feed is configured.</strong> With the bundled empty ledger, all empirical rows are blank and every strategy is unqualified. No bets, stakes, or betting advice are produced.</p>
<p>Status: {badge(report["status"])} · Observations: {report["n_observations"]} · Qualified: {report["n_qualified"]} · Strategies: {len(strategies)} · Correlation pairs: {len(report["correlations"])}</p>
<h2>What is here</h2>
<ul><li><strong>Strategies</strong> — six frozen candidate specifications: singles, player props, prop combos and a two-game parlay.</li>
<li><strong>Methodology</strong> — ten gates, event-clustered uncertainty, Bonferroni over the full frozen family, and proper scoring rules.</li>
<li><strong>Correlations</strong> — paired training residuals; unavailable pairs stay blank and unverified. Independence is never assumed by default.</li>
<li><strong>Leaderboard</strong> — only all-gate qualifiers; ranking uses the lower bound of event-clustered holdout ROI.</li>
<li><strong>Sources</strong> — official source links and scope limits. Findings and flagged items are separate.</li></ul>
<p>No historical odds or sportsbook quotes are imported. The empty run is the deterministic fail-closed default.</p>"""
    page("Overview", overview, nav)

    # Strategies
    rows = []
    for s in strategies:
        rows.append([
            esc(s["id"]), esc(s["name"]), esc(s["category"]), esc(s["market"]),
            link(s["source_url"], "NBA Glossary"),
            '<span class="blank">—</span>', '<span class="blank">—</span>',
            badge("unverified"), '<span class="blank">authorized holdout required</span>',
        ])
    strategies_body = f"""<h1>Strategies</h1>
<p class="callout">Each candidate must pass all ten gates on an untouched chronological holdout before it can appear on the leaderboard. The six-member family is frozen in advance so the multiple-testing correction reflects every hypothesis tried, including any later abandoned.</p>
{table(["ID", "Name", "Category", "Market", "Source", "Sample size", "Gates passed", "Status", "Holdout result"], rows, "strategy-table")}"""
    page("Strategies", strategies_body, nav)

    # Methodology
    gate_rows = []
    for g in strategies[0]["gates"]:
        gate_rows.append([esc(g["id"]), esc(g["name"]), badge(g["status"]), esc(g["reason"]), link(g["source_url"], "Source")])
    methodology = f"""<h1>Methodology</h1>
<p class="callout">Luck cannot be removed from the equation. The gates reduce the chance of mistaking luck for skill. They are proposals for authorized, preregistered, audited research — not official NBA rules or a guarantee of profit.</p>
{table(["Gate", "Name", "Status", "Reason", "Source"], gate_rows, "gate-table")}
<h2>Uncertainty</h2>
<p>ROI, CLV and predictive-quality improvements use a percentile bootstrap that resamples whole event clusters. Serial dependence across dates is not eliminated. The binomial tail is a diagnostic only; parlays and same-game props are clustered and heterogeneous.</p>
<h2>Multiplicity</h2>
<p>The Bonferroni adjustment is applied across all six frozen candidates, including abandoned ones. No adaptive search may add a new candidate after seeing holdout results.</p>
<h2>What is not here</h2>
<ul><li>No synthetic or fabricated returns.</li><li>No sportsbook odds or closing prices.</li><li>No NBA statistics beyond the official glossary and schedule metadata that are directly linked above.</li></ul>"""
    page("Methodology", methodology, nav)

    # Correlations
    corr_rows = []
    for c in report["correlations"]:
        corr_rows.append([
            esc(c["id"]), esc(c["leg_a"]), esc(c["leg_b"]), esc(c["scope"]),
            '<span class="blank">unverified</span>', '<span class="blank">—</span>',
            esc(c["status"]), link(c["source_url"], "Source"),
        ])
    correlations = f"""<h1>Correlations</h1>
<p class="callout">Pairwise correlations are estimated only from training-period paired residuals. Missing evidence stays blank and unverified. Independence is a special case requiring evidence — never a silent default.</p>
{table(["Pair", "Leg A", "Leg B", "Scope", "Estimate", "Sample size", "Status", "Source"], corr_rows, "corr-table")}"""
    page("Correlations", correlations, nav)

    # Leaderboard
    leader_rows = []
    if report["leaderboard"]:
        for r in report["leaderboard"]:
            leader_rows.append([str(r["rank"]), esc(r["strategy_id"]), esc(r["name"]), cell(r["score_roi_lower"]), link(r["source_url"], "Source")])
    else:
        leader_rows.append(['<span class="blank">—</span>', '<span class="blank">no strategy qualified</span>', '<span class="blank">—</span>', '<span class="blank">—</span>', '<span class="blank">—</span>'])
    leaderboard = f"""<h1>Leaderboard</h1>
<p class="callout">Ranking uses the lower bound of event-clustered holdout ROI so small-sample heaters cannot win. Only strategies passing all gates appear here. Rewards are non-monetary research priority only — no payouts, stakes, or picks.</p>
{table(["Rank", "Strategy", "Name", "ROI lower bound", "Source"], leader_rows, "leaderboard-table")}
<p>Status: {badge(report["status"])} · Qualified: {report["n_qualified"]}</p>"""
    page("Leaderboard", leaderboard, nav)

    # Sources
    src_rows = []
    for s in sources["rows"]:
        src_rows.append([esc(s["id"]), esc(s["publisher"]), esc(s["title"]), link(s["url"], "URL"), esc(s["status"]), esc(s["supports"])])
    sources_body = f"""<h1>Sources</h1>
<p class="callout">Official sources are cited for definitions, policy and methodology only. A link is not a license to reuse NBA statistics in a gambling-related context. The NBA Terms of Use §§1 and 9 must be resolved through appropriate rights and legal review.</p>
{table(["ID", "Publisher", "Title", "URL", "Status", "Supports"], src_rows, "sources-table")}"""
    page("Sources", sources_body, nav)

    # Findings
    find_rows = []
    for f in findings:
        find_rows.append([esc(f["id"]), esc(f["severity"]), esc(f["file"]), esc(f["lines"]), esc(f["finding"]), esc(f["detail"]), esc(f["action"]), link(f["source_url"], "Source"), badge(f["status"])])
    findings_body = f"""<h1>Repo Findings</h1>
<p class="callout">These are reproducible code, data and documentation findings in the upstream tree at <code>77a28cccea34e0764f6d45ff3316d3aa8f6b90b7</code>. They do not imply the upstream data is false; they describe review limitations and failure modes that the new lab addresses.</p>
{table(["ID", "Severity", "File", "Lines", "Finding", "Detail", "Action", "Source", "Status"], find_rows, "findings-table")}"""
    page("Findings", findings_body, nav)

    # Flagged
    flag_rows = []
    for r in audit:
        flag_rows.append([esc(r["file"]), esc(r["row"]), esc(r["verification"]), esc(r["review_note"]), link(r["source_url"], "Source")])
    flagged = f"""<h1>Flagged for Review</h1>
<p class="callout">Every upstream data row is reviewed against an official source or explicitly marked unverified. Blank values are not inferred. These items do not block the build; they are published for owner review after launch.</p>
{table(["File", "Row", "Verification", "Review note", "Source"], flag_rows, "flagged-table")}"""
    page("Flagged", flagged, nav)

    print(f"Built {len(list(OUT.glob('*.html')))} pages under docs/lab/")


if __name__ == "__main__":
    main()
