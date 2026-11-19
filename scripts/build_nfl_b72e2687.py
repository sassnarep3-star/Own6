#!/usr/bin/env python3
"""Build the nfl-b72e2687 Pages site from committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_b72e2687.py            # write docs/nfl-b72e2687/**
    python3 scripts/build_nfl_b72e2687.py --check    # build then run the verifier

Every page is a table or a list. Every published row links to the official page it
came from. Cells that no official source supports stay empty and the page says why.
"""
from __future__ import annotations

import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_b72e2687")
DOCS = os.path.join(REPO, "docs", "nfl-b72e2687")

STYLE = """
:root{--ink:#16232e;--muted:#5d7183;--navy:#0f2433;--teal:#0a7d74;--line:#dbe3e8;--paper:#f5f8f9;
--white:#fff;--warn:#fff4dc;--warnink:#7a4b00;--ok:#0a6b4f;--bad:#9c2b2b;--soft:#eef4f5}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.55;
font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:15px}
a{color:var(--teal);text-underline-offset:.16em}
header{background:var(--navy);color:#fff}
.wrap{width:min(1220px,calc(100% - 2rem));margin:0 auto}
.top{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;align-items:baseline;padding:.95rem 0}
.top b{letter-spacing:.06em}
.top span{color:#9fc7c2;font-size:.8rem;letter-spacing:.1em;text-transform:uppercase}
nav{display:flex;flex-wrap:wrap;gap:.25rem .9rem;padding:0 0 .7rem}
nav a{color:#cfe3e0;text-decoration:none;font-size:.86rem;padding:.15rem 0;border-bottom:2px solid transparent}
nav a:hover{border-bottom-color:#7fd3c6}
nav a.on{color:#fff;border-bottom-color:#7fd3c6;font-weight:600}
main{padding:1.4rem 0 3rem}
h1{font-size:1.5rem;margin:.2rem 0 .4rem}
h2{font-size:1.12rem;margin:1.9rem 0 .55rem;padding-bottom:.3rem;border-bottom:1px solid var(--line)}
h3{font-size:.98rem;margin:1.2rem 0 .35rem}
p{max-width:78ch}
.lead{color:var(--muted);max-width:82ch}
.cards{display:grid;gap:.7rem;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin:1rem 0 .4rem}
.card{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:.8rem .9rem}
.card .k{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.card .v{font-size:1.65rem;font-weight:700;line-height:1.15;margin-top:.15rem}
.card .s{font-size:.78rem;color:var(--muted)}
.tw{overflow-x:auto;background:var(--white);border:1px solid var(--line);border-radius:10px;margin:.6rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.84rem}
th,td{padding:.42rem .6rem;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--soft);font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;color:#39505f;
position:sticky;top:0;white-space:nowrap}
tbody tr:hover{background:#fbfdfd}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:.05rem .42rem;border-radius:999px;font-size:.72rem;font-weight:600}
.pill.ok{background:#dff3ec;color:var(--ok)}
.pill.warn{background:var(--warn);color:var(--warnink)}
.pill.bad{background:#fbe6e6;color:var(--bad)}
.pill.info{background:#e7eef4;color:#31556e}
.note{background:var(--warn);border:1px solid #f0dcb2;color:var(--warnink);
border-radius:8px;padding:.55rem .8rem;font-size:.86rem;margin:.7rem 0}
.blank{color:#93a6b3;font-style:italic}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.8rem;padding:1rem 0 2rem}
code{background:var(--soft);padding:.05rem .3rem;border-radius:4px;font-size:.85em}
"""

PAGES = ["index.html", "captures.html", "flags.html", "reverification.html",
         "registers.html", "sources.html"]

STATUS_PILL = {
    "satisfied": "ok", "satisfied-this-session": "ok", "policy-enforced": "info",
    "partial": "warn", "partially-satisfied": "warn", "open": "bad",
    "needs-review": "warn", "rejected": "bad",
}


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def a(url: str, label: str = "source") -> str:
    if not url:
        return ""
    return (f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">'
            f'{esc(label)}&nbsp;&#8599;</a>')


def src_or_text(url: str) -> str:
    """Render an https source as a link; a repo-relative evidence pointer as plain text."""
    if not url:
        return ""
    if url.startswith("http"):
        return a(url)
    return esc(url)


def cell(v) -> str:
    if v in ("", None):
        return '<span class="blank">not published</span>'
    return esc(v)


def pill(status: str) -> str:
    cls = STATUS_PILL.get(status.lower().split("-")[0] + ("-session" if "session" in status.lower() else ""), "info")
    if "policy" in status.lower():
        cls = "info"
    return f'<span class="pill {cls}">{esc(status)}</span>'


def table(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def page(name: str, title: str, active: str, body: str) -> str:
    nav = "".join(
        f'<a href="{p}" class="{"on" if p == active else ""}">{p[:-5].replace("_", " ").title()}</a>'
        for p in PAGES)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Own6 NFL session b72e2687: official-source capture, flag re-tests, reverification, decision-readiness and suggestions. No market prices; unverified values blank and flagged.">
<title>{esc(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<header><div class="wrap">
<div class="top"><b>OWN6 · NFL</b><span>session b72e2687 · read 2026-11-19</span></div>
<nav>{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
Evidence rule: a published value is text read this session from the official page named in its
source link (logged with UTC clock and sha256 in <code>data/nfl_b72e2687/capture_log.csv</code>), or
arithmetic on such values with the derivation shown. Everything else is blank and flagged. No market
price exists on any official NFL page, so price columns stay blank by policy. No profitability claim.
</div></footer>
</body>
</html>
"""


def build_index() -> str:
    standings = read("standings_2026_11_19.csv")
    week12 = read("week12_slate.csv")
    injuries = read("injuries_reg11.csv")
    players = [r for r in injuries if r.get("player") and r["player"] != "NO_INJURIES_REPORTED"]
    markers = [r for r in injuries if r.get("player") == "NO_INJURIES_REPORTED"]
    reqs = read("requirements.csv")
    flags = read("flagged.csv")
    qs = read("questions.csv")
    sugs = read("suggestions.csv")

    n_dnp = sum(1 for r in players if r["practice_code"] == "DNP")
    n_lp = sum(1 for r in players if r["practice_code"] == "LP")
    n_fp = sum(1 for r in players if r["practice_code"] == "FP")

    total_w = sum(int(r["w"]) for r in standings)
    total_l = sum(int(r["l"]) for r in standings)
    total_t = sum(int(r["t"]) for r in standings)
    total_pf = sum(int(r["pf"]) for r in standings)
    total_pa = sum(int(r["pa"]) for r in standings)

    cards = f"""
<div class="cards">
<div class="card"><span class="k">Standings (official)</span><span class="v">{total_w}-{total_l}-{total_t}</span>
<span class="s">32 clubs · PF {total_pf} = PA {total_pa} · read 2026-11-19</span></div>
<div class="card"><span class="k">Week-11 injury register</span><span class="v">{len(players)}</span>
<span class="s">player rows + {len(markers)} no-injury markers · 13/13 games · DNP {n_dnp} / LP {n_lp} / FP {n_fp}</span></div>
<div class="card"><span class="k">Week-12 slate</span><span class="v">{len(week12)}</span>
<span class="s">games with kickoff times and networks · read 2026-11-19</span></div>
<div class="card"><span class="k">Flags</span><span class="v">{len(flags)}</span>
<span class="s">open or fixed · none block the merge · see Flagged for Review</span></div>
<div class="card"><span class="k">Requirements tracked</span><span class="v">{len(reqs)}</span>
<span class="s">one row each with blocking gate and clearing number</span></div>
<div class="card"><span class="k">Open questions / suggestions</span><span class="v">{len(qs)} / {len(sugs)}</span>
<span class="s">Q/I/A ledger and review-only suggestions</span></div>
</div>"""

    req_rows = []
    for r in reqs:
        req_rows.append([
            f'<b>{esc(r["req_id"])}</b>', cell(r["requirement"]),
            pill(r["status"]), cell(r["blocking_gate"]), cell(r["clears_when"]),
            a(r["source_url"])])
    req_table = table(
        ["ID", "Requirement", "Status", "Blocking gate", "Clears when", "Official source"],
        req_rows)

    body = f"""
<h1>NFL decision desk — session b72e2687</h1>
<p class="lead">Fresh official captures from <b>2026-11-19</b>: standings, the Week-11 injury
register, the Week-12 slate, venue fields from official game centres, and the November reserve
list. Every value below is linked to the official page it was read from. Prices stay blank because
no official NFL page publishes a market price. <b>Nothing here is a profitability claim.</b></p>
{cards}
<h2>Decision readiness: one row per requirement</h2>
<p class="lead">For every requirement: the gate that blocks it and the number that would clear it.
Nothing is auto-implemented from this table; suggestions and questions are review-only.</p>
{req_table}
<h2>What this session verified (headline rows)</h2>
<p class="lead">Full detail and per-row evidence: <a href="captures.html">Captures</a> ·
<a href="reverification.html">Reverification</a> · <a href="flags.html">Flagged for Review</a>.</p>
{table(["Check", "Result", "Official source"], [
    ["Standings totals recomputed independently", "149 W / 149 L / 2 T; PF = PA = 6,923 — MATCH vs prior pack", a("https://www.nfl.com/standings/division/2026/reg")],
    ["Week-12 slate re-read line by line", "16/16 games match; 2 official heading/weekday contradictions reproduced", a("https://www.nfl.com/schedules/2026/by-week/week-12")],
    ["Week-11 injury register re-read", f"{len(players)} player rows + {len(markers)} markers; 16 game-status cells — MATCH vs prior pack", a("https://www.nfl.com/injuries/league/2026/reg11")],
    ["Reserve list re-read", "25 rows, window 11/10–11/18 — MATCH vs prior pack", a("https://www.nfl.com/transactions/league/reserve-list/2026/11")],
    ["Inherited flags re-tested", f"{len(flags)} rows on the Flagged for Review page, none blocking", a("https://www.nfl.com/injuries/league/2026/reg11")],
])}
<div class="note">Evidence boundary: the NIST/SEMATECH handbook supports uncertainty-interval
reporting only. It supports no sports-betting method and no edge claim. Suggestions are proposals;
the owner chooses the path before anything is implemented.</div>
"""
    return page("index.html", "Own6 NFL · b72e2687 decision desk", "index.html", body)


def build_captures() -> str:
    standings = read("standings_2026_11_19.csv")
    week12 = read("week12_slate.csv")
    injuries = read("injuries_reg11.csv")
    log = read("capture_log.csv")

    body = """
<h1>Official captures — 2026-11-19</h1>
<p class="lead">Every value below was read this session from the official page named in the source
link. The capture log records the UTC read clock and the sha256 of the transcription artifact; the
hash covers the artifact bytes and cannot prove what the page said at read time.</p>
"""
    body += f"""
<h2>Standings — all 32 clubs</h2>
{table(["Conference", "Club", "W", "L", "T", "PCT", "PF", "PA", "NET", "Source"],
    [[esc(r["conference"]), cell(r["club"]), esc(r["w"]), esc(r["l"]), esc(r["t"]),
      esc(r["pct"]), esc(r["pf"]), esc(r["pa"]), esc(r["net_pts"]),
      a("https://www.nfl.com/standings/division/2026/reg")] for r in standings])}
<p class="lead">Session arithmetic: W {sum(int(r['w']) for r in standings)} / L
{sum(int(r['l']) for r in standings)} / T {sum(int(r['t']) for r in standings)}; PF
{sum(int(r['pf']) for r in standings)} = PA {sum(int(r['pa']) for r in standings)}.</p>

<h2>Week-12 slate — 16 games</h2>
{table(["#", "Day / date", "Kickoff ET", "Network", "Matchup", "Game centre", "Away rec", "Home rec", "Source"],
    [[esc(r["slot"]), cell(r["day_date"]), cell(r["time_et"]), cell(r["network"]),
      cell(r["matchup"]), a(r["game_centre_url"], "game centre"), cell(r["away_record"]),
      cell(r["home_record"]), a("https://www.nfl.com/schedules/2026/by-week/week-12")]
     for r in week12])}
<div class="note">The schedule page itself carries no venue fields; venue names appear only in
affiliate links. Official venue transcription comes from game-centre Location/Stadium fields (see
Flagged for Review, B72-F02).</div>

<h2>Week-11 injury register — 13/13 games</h2>
<p class="lead">Practice status is published as full text; the code column (DNP/LP/FP) is the parsed
canonical form. Blank game-status cells are the live page's cadence, not an omission.</p>
{table(["Game", "Team", "Player", "Pos", "Injuries", "Practice", "Code", "Game status", "Source"],
    [[cell(r["game"]), cell(r["team"]), cell(r["player"]), cell(r["position"]),
      cell(r["injuries"]), cell(r["practice_status"]), cell(r["practice_code"]),
      cell(r["game_status"]), a("https://www.nfl.com/injuries/league/2026/reg11")]
     for r in injuries])}

<h2>Capture log</h2>
{table(["Read", "Source", "What was read", "Read on (UTC)", "Artifact", "sha256", "Status"],
    [[cell(r["read_id"]), a(r["source_url"]), cell(r["what_was_read"]), cell(r["read_on_utc"]),
      cell(r["artifact_path"]), cell(r["artifact_sha256"]), cell(r["status"])] for r in log])}
"""
    return page("captures.html", "Own6 NFL · b72e2687 captures", "captures.html", body)


def build_flags() -> str:
    flags = read("flagged.csv")
    recheck = read("flag_recheck.csv")
    body = """
<h1>Flagged for Review</h1>
<p class="lead">Irregularities and open data needs, each with its official source link. A status of
<b>open</b> does not block anything; <b>fixed</b> means the item was found and corrected in this
session before publication. Nothing here is a verified value — it is a documented gap.</p>
"""
    body += f"""
<h2>Flag register</h2>
{table(["ID", "Raised", "Severity", "Category", "Summary", "Detail", "Status", "Source"],
    [[f'<b>{esc(r["flag_id"])}</b>', esc(r["raised_date"]), cell(r["severity"]), cell(r["category"]),
      cell(r["summary"]), cell(r["detail"]),
      ('<span class="pill bad">open</span>' if r["status"] == "open" else
       '<span class="pill info">fixed</span>'),
      src_or_text(r["source_urls"])] for r in flags])}

<h2>Flag re-tests — 2026-11-19</h2>
<p class="lead">Each inherited flag was re-tested against its official source today; the finding is
the value read from that page.</p>
{table(["Flag", "Origin", "Summary", "Re-test source", "Finding today", "New status", "Evidence"],
    [[f'<b>{esc(r["flag_id"])}</b>', cell(r["origin_pack"]), cell(r["flag_summary"]),
      src_or_text(r["retest_source"]), cell(r["retest_finding"]),
      ('<span class="pill bad">still open</span>' if r["new_status"] == "still_open" else
       '<span class="pill info">not retested</span>'),
      cell(r["evidence"])] for r in recheck])}
"""
    return page("flags.html", "Own6 NFL · b72e2687 flagged for review", "flags.html", body)


def build_reverification() -> str:
    rev = read("reverification.csv")
    body = """
<h1>Line-by-line reverification</h1>
<p class="lead">Published values from the merged packs were re-read this session from the same
official pages they cite. Results are recomputed, not asserted: MATCH means the fresh read agrees,
CORROBORATED_CONSISTENT means the figures are internally consistent but the full recomputation needs
a source not read this session, and NOT_RECOMPUTABLE_FROM_THIS_READ names the missing official input.</p>
"""
    body += f"""
{table(["ID", "Prior pack", "Value reverified", "Re-verify source", "Method", "Result", "Evidence"],
    [[f'<b>{esc(r["row_id"])}</b>', cell(r["prior_pack"]), cell(r["published_value_reverified"]),
      src_or_text(r["reverify_source"]), cell(r["method"]), cell(r["result"]), cell(r["evidence"])]
     for r in rev])}
"""
    return page("reverification.html", "Own6 NFL · b72e2687 reverification", "reverification.html", body)


def build_registers() -> str:
    reqs = read("requirements.csv")
    qs = read("questions.csv")
    sugs = read("suggestions.csv")
    body = """
<h1>Registers: requirements, questions, suggestions</h1>
<p class="lead">One row per requirement with the gate that blocks it and the number that would clear
it. Questions are the information gaps that must be answered before decisions; suggestions are
proposals for the owner to choose from — nothing here is auto-implemented.</p>
"""
    body += f"""
<h2>Requirements — {len(reqs)} rows</h2>
{table(["ID", "Requirement", "Section", "Status", "Blocking gate", "Clears when", "Evidence", "Source"],
    [[f'<b>{esc(r["req_id"])}</b>', cell(r["requirement"]), cell(r["brief_section"]),
      pill(r["status"]), cell(r["blocking_gate"]), cell(r["clears_when"]),
      cell(r["evidence_pointer"]), src_or_text(r["source_url"])] for r in reqs])}

<h2>Questions / information / answers — {len(qs)} rows</h2>
{table(["ID", "Question", "What we have", "What we lack", "Why it matters", "How to answer", "Source needed", "Status"],
    [[f'<b>{esc(r["question_id"])}</b>', cell(r["question"]), cell(r["what_we_have"]),
      cell(r["what_we_lack"]), cell(r["why_it_matters"]), cell(r["how_to_answer"]),
      cell(r["source_needed"]), cell(r["status"])] for r in qs])}

<h2>Suggestions — {len(sugs)} rows (review before implementing)</h2>
{table(["ID", "Suggestion", "Motivation", "Suggested action", "Prerequisite", "Priority", "Human choice pending", "Status"],
    [[f'<b>{esc(r["sug_id"])}</b>', cell(r["suggestion"]), cell(r["motivation"]),
      cell(r["suggested_action"]), cell(r["prerequisite"]), cell(r["priority"]),
      cell(r["pending_human_choice"]), cell(r["status"])] for r in sugs])}
"""
    return page("registers.html", "Own6 NFL · b72e2687 registers", "registers.html", body)


def build_sources() -> str:
    srcs = read("sources.csv")
    body = """
<h1>Official sources</h1>
<p class="lead">Every source this session read or referenced. <b>verified-2026-11-19</b> means the
page was read in-session; <b>reference-only</b> means it is cited for policy or method and was not
read for data this session.</p>
"""
    body += f"""
{table(["ID", "URL", "Host", "Title as read", "Used for", "Read on", "Status"],
    [[f'<b>{esc(r["source_id"])}</b>', a(r["source_url"]), cell(r["host"]), cell(r["title_as_read"]),
      cell(r["used_for"]), cell(r["read_on_utc"]), cell(r["status"])] for r in srcs])}
"""
    return page("sources.html", "Own6 NFL · b72e2687 sources", "sources.html", body)


def main() -> None:
    os.makedirs(DOCS, exist_ok=True)
    builders = {
        "index.html": build_index,
        "captures.html": build_captures,
        "flags.html": build_flags,
        "reverification.html": build_reverification,
        "registers.html": build_registers,
        "sources.html": build_sources,
    }
    for name, fn in builders.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(fn())
        print(f"wrote docs/nfl-b72e2687/{name}")
    if "--check" in sys.argv:
        subprocess.check_call([sys.executable, os.path.join(REPO, "scripts", "check_nfl_b72e2687.py")])


if __name__ == "__main__":
    main()
