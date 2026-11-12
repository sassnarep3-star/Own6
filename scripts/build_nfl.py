#!/usr/bin/env python3
"""Build the source-linked, fail-closed NFL research pages from data/nfl/*.csv."""
from __future__ import annotations

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl"
OUT = ROOT / "docs" / "nfl"

PAGES = {
    "strategies.html": ("Strategy hypotheses", "strategies.csv", "Hypotheses are test designs, not proven edges. Each performance cell stays blank until rights-cleared, timestamped, out-of-sample results exist."),
    "injuries.html": ("Injuries and depth chart", "injury_fields.csv", "The official NFL report fields can inform an availability log. A report does not by itself establish a starter, expected snaps, or second/third/fourth replacement. Live values remain blank."),
    "correlations.html": ("Correlation methods", "correlations.csv", "No empirical NFL correlation has been estimated. Coefficients and intervals are blank rather than guessed; methods below are proposed for authorized paired data."),
    "validation.html": ("Validation gates", "gates.csv", "All gates must pass before qualification. Rights, lineups, price data and legal review are hard stops; methodological thresholds must be preregistered, not tuned after results."),
    "leaderboard.html": ("Leaderboard", "leaderboard.csv", "The leaderboard is intentionally empty: no rank, score, performance result or material reward is published. Entries below are ineligible research candidates, not picks."),
    "questions.html": ("Decision questions", "questions.csv", "Questions that must be answered before deployment. Current official evidence is separated from unresolved inputs and decisions."),
    "suggestions.html": ("Suggestions for review", "suggestions.csv", "A decision queue for choosing a responsible path before implementation. Recommendations are proposals; no source grants permission or demonstrates a betting edge."),
    "sources.html": ("Official sources and evidence ledger", "sources.csv", "Verified direct means the official page was opened and the described content checked on 12 November 2026. Link-only and partial reads are labeled. An official link is not proof of any unverified value."),
    "flagged.html": ("Flagged for Review", "flags.csv", "Open issues do not block publication of this research framework. They do block data ingestion, current lines, empirical claims and rewards as specified below."),
}

NAV = [
    ("index.html", "Overview"), ("strategies.html", "Strategies"),
    ("injuries.html", "Injuries & depth"), ("correlations.html", "Correlations"),
    ("validation.html", "Validation"), ("leaderboard.html", "Leaderboard"),
    ("questions.html", "Decision questions"), ("suggestions.html", "Suggestions"),
    ("sources.html", "Sources"), ("flagged.html", "Flagged for Review"),
]


def rows_for(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def escape(value: str) -> str:
    return html.escape(value or "", quote=True)


def nav_html(current: str) -> str:
    links = []
    for path, label in NAV:
        cls = ' aria-current="page"' if path == current else ""
        links.append(f'<a href="{path}"{cls}>{escape(label)}</a>')
    return "\n".join(links)


def table_for(csv_name: str) -> str:
    rows = rows_for(csv_name)
    if not rows:
        raise ValueError(f"No rows in {csv_name}")
    headers = [key for key in rows[0] if key not in {"source_id", "url"}]
    head = "".join(f'<th scope="col">{escape(key.replace("_", " ").title())}</th>' for key in headers)
    head += '<th scope="col">Official source / review</th>'
    out = [f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>']
    source_rows = {r["source_id"]: r for r in rows_for("sources.csv")}
    for row in rows:
        source_id = row.get("source_id", "")
        source = source_rows.get(source_id)
        if not source or not source.get("url", "").startswith("https://"):
            raise ValueError(f"Missing HTTPS official source for {csv_name}: {source_id}")
        cells: list[str] = []
        for key in headers:
            value = row.get(key, "")
            if value == "":
                label = "Unverified; blank" if key in {"performance_result", "reported_value", "live_value", "rank", "score", "reward_status"} else "Blank"
                cells.append(f'<td class="blank" aria-label="{label}"></td>')
            else:
                cells.append(f"<td>{escape(value)}</td>")
        cells.append(f'<td><a rel="noopener" href="{escape(source["url"])}">{escape(source_id)} — review source ↗</a></td>')
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def document(title: str, body: str, current: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="NFL evidence-first line research, injury-data requirements, validation and review dashboard.">
  <title>{escape(title)} | Own6 NFL Research</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar"><a class="brand" href="index.html">OWN6 <span>/ NFL RESEARCH</span></a><nav aria-label="NFL research sections">{nav_html(current)}</nav></header>
<main>{body}</main>
<footer><strong>Research only.</strong> No current lines, picks, wagers, measured edge, correlation coefficients, ROI, or strategy rewards are published. Luck cannot be removed; validation can only reduce false discovery and quantify uncertainty. See <a href="flagged.html">Flagged for Review</a>, the <a href="https://www.nfl.com/legal/terms/">NFL terms</a>, the <a href="https://aglc.ca/playalberta">AGLC</a> and <a href="https://gamesenseab.ca/">GameSense</a>.</footer>
</body></html>'''


def main() -> None:
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    cards = "".join(
        f'<a class="card" href="{path}"><span class="num">{i:02d}</span><h2>{escape(label)}</h2><p>{escape(desc)}</p><span class="go">Open section →</span></a>'
        for i, (path, label, desc) in enumerate([
            ("strategies.html", "Strategy hypotheses", "Singles, player props, same-game and cross-game parlays; none claim an edge."),
            ("injuries.html", "Injuries & depth", "Official injury-report fields plus a strict role/depth schema; no guessed replacements."),
            ("correlations.html", "Correlation methods", "Method plan only; all empirical coefficients and uncertainty intervals are blank."),
            ("validation.html", "Validation gates", "Rights, point-in-time data, holdouts, multiplicity, dependence, price and legal gates."),
            ("leaderboard.html", "Leaderboard", "An empty, fail-closed competition board; no rank or prize winner."),
            ("questions.html", "Decision questions", "Known facts, missing information and what each blocks."),
            ("suggestions.html", "Suggestions for review", "Prioritized choices to resolve before implementing a data pipeline or prizes."),
            ("sources.html", "Official sources", "Directly checked official NFL, Alberta, Canada and statistical references."),
            ("flagged.html", "Flagged for Review", "Rights, injury-depth, odds, legal and validation blockers."),
        ], 1)
    )
    index_body = f'''<section class="hero"><p class="eyebrow">EVIDENCE-FIRST NFL LINES RESEARCH · 12 NOV 2026</p><h1>Better decisions start<br><em>with verified inputs.</em></h1><p class="intro">This NFL section organizes source-reviewed requirements and a test plan for originating lines across game markets, player props and parlays. It does not publish picks or assert any strategy works.</p><div class="status"><div><span>Published NFL odds / lines</span><strong>—</strong></div><div><span>Measured NFL correlations</span><strong>—</strong></div><div><span>Qualified strategies / rewards</span><strong>0</strong></div><div><span>Automated NFL data feeds</span><strong>0</strong></div></div><p class="callout"><b>Current decision: do not ingest or price yet.</b> NFL.com’s terms page says its services are for individual, non-commercial, informational use and prohibits systematic retrieval to compile databases absent express prior written consent. No written NFL data permission or licensed odds source is configured in this repo. See <a href="sources.html">source notes</a> and <a href="flagged.html">open flags</a>.</p><p class="fine">The zeroes and dashes above describe this repository’s reviewed NFL work, not NFL-wide facts. A dash means no verified value, not zero performance.</p></section><section class="section"><p class="eyebrow">EXPLORE</p><h2>One path from question to evidence</h2><div class="cards">{cards}</div></section><section class="section"><p class="eyebrow">RECOMMENDED ORDER</p><h2>Resolve blockers before a model exists</h2><ol class="steps"><li>Get written data-use permission and jurisdiction-specific legal advice.</li><li>Choose licensed player/outcome, lineup, injury and timestamped odds feeds.</li><li>Define market/settlement rules and freeze a candidate list and holdout protocol.</li><li>Run chronological, multiplicity-aware validation; publish failed candidates too.</li><li>Only after independent audit, consider a non-monetary leaderboard; material rewards stay disabled until legal signoff.</li></ol><p>Every data table row links to an official source for review. An official page is not treated as proof of a value the page does not provide. Missing values remain blank and are flagged.</p></section>'''
    (OUT / "index.html").write_text(document("NFL research dashboard", index_body, "index.html"), encoding="utf-8")
    for filename, (title, csv_name, intro) in PAGES.items():
        body = f'<section class="page-head"><p class="eyebrow">NFL RESEARCH / EVIDENCE REGISTER</p><h1>{escape(title)}</h1><p>{escape(intro)}</p><p class="back"><a href="index.html">← NFL dashboard</a></p></section><section class="section">{table_for(csv_name)}</section>'
        (OUT / filename).write_text(document(title, body, filename), encoding="utf-8")
    print(f"Built {len(PAGES) + 1} NFL pages from {len(list(DATA.glob('*.csv')))} CSV files.")


CSS = '''
:root{--ink:#172b31;--muted:#52656a;--paper:#f4f7f5;--white:#fff;--green:#174e47;--lime:#cbf06b;--line:#d8e0dc;--amber:#fff1cf;--shadow:0 16px 44px #142c2610}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.62 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.topbar{background:#102d2c;color:#fff;display:flex;align-items:center;justify-content:space-between;gap:1.25rem;padding:14px clamp(18px,4vw,64px);position:sticky;top:0;z-index:5}.brand{font-weight:900;color:white;text-decoration:none;letter-spacing:.08em;white-space:nowrap}.brand span{font-weight:500;color:#b6cdc2}.topbar nav{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.topbar nav a{color:#e3eee9;text-decoration:none;border-radius:8px;padding:6px 9px;font-size:.85rem}.topbar nav a:hover,.topbar nav a[aria-current=page]{background:#315951;color:#fff}main{max-width:1440px;margin:0 auto;padding:36px clamp(16px,4vw,58px) 72px}.hero{background:linear-gradient(125deg,#123a36,#1d5d50);color:white;border-radius:26px;padding:clamp(26px,5vw,62px);box-shadow:var(--shadow)}.eyebrow{font-size:.72rem;letter-spacing:.17em;text-transform:uppercase;font-weight:850;color:#8ab5a5}.hero .eyebrow{color:var(--lime)}h1{font-size:clamp(2.4rem,5vw,4.8rem);line-height:1.04;letter-spacing:-.045em;margin:.25em 0}.hero h1 em{color:var(--lime);font-style:normal}.intro{max-width:840px;font-size:1.16rem;color:#e3efea}.status{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:30px 0}.status div{border:1px solid #ffffff45;background:#ffffff0c;padding:14px 16px;border-radius:13px}.status span,.status strong{display:block}.status span{font-size:.82rem;color:#c7d9d3}.status strong{font-size:1.5rem;margin-top:3px;color:#fff}.callout{max-width:1000px;border-radius:14px;background:#fff;color:var(--ink);padding:16px 18px}.callout a{color:#146451;font-weight:700}.fine{font-size:.8rem;color:#d3e2dc}.section{margin-top:42px}.section h2{font-size:1.8rem;letter-spacing:-.03em;margin:.1em 0 .6em}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.card{background:white;border:1px solid var(--line);border-radius:16px;padding:20px;color:var(--ink);text-decoration:none;box-shadow:var(--shadow);transition:transform .15s,border-color .15s}.card:hover{transform:translateY(-2px);border-color:#93bda8}.card .num{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:10px;background:#e9f5ed;color:#1c6350;font-weight:800}.card h2{font-size:1.15rem;margin:12px 0 5px}.card p{font-size:.92rem;color:var(--muted);margin:0 0 13px}.go{color:#17644f;font-size:.87rem;font-weight:800}.page-head{padding:16px 0 24px}.page-head h1{font-size:clamp(2.3rem,4vw,3.8rem)}.page-head>p:not(.eyebrow):not(.back){max-width:980px;color:var(--muted);font-size:1.08rem}.back a{color:#1b6751;font-weight:700;text-decoration:none}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:16px;background:white;box-shadow:var(--shadow)}table{border-collapse:collapse;width:100%;min-width:1020px;font-size:.9rem}th,td{text-align:left;vertical-align:top;padding:12px 14px;border-bottom:1px solid #e4e9e6}th{position:sticky;top:0;background:#eaf1ed;color:#173f39;font-size:.77rem;letter-spacing:.04em;text-transform:uppercase;z-index:1}tbody tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#fbfcfb}td a{color:#1b6751;font-weight:700;text-underline-offset:3px}.blank{min-width:80px;background:linear-gradient(135deg,transparent 48%,#ebefec 49%,#ebefec 51%,transparent 52%)}.steps{padding-left:1.3rem}.steps li{margin:.75rem 0}footer{background:#102d2c;color:#d7e5df;padding:26px clamp(18px,4vw,64px);font-size:.88rem}footer a{color:var(--lime)}@media(max-width:950px){.topbar{position:static;align-items:flex-start;flex-direction:column}.topbar nav{justify-content:flex-start}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.status{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:620px){.cards{grid-template-columns:1fr}.status{grid-template-columns:1fr 1fr}main{padding-top:20px}.hero{border-radius:18px}.topbar nav a{padding:6px 7px}}
'''

if __name__ == "__main__":
    main()
