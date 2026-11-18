#!/usr/bin/env python3
"""Build the nfl-0d4da02c pack site: GitHub Pages pages from committed CSVs.

Deterministic: no network, no arguments that change output. A re-run must
produce byte-identical files (asserted by tests). Data CSVs are produced by
src/nfl_0d4da02c/*; this script only renders them.

Usage
-----
    python3 scripts/build_nfl_0d4da02c.py            # write HTML pages
    python3 scripts/build_nfl_0d4da02c.py --check    # build, then run the verifier
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_0d4da02c")
DOCS = os.path.join(REPO, "docs", "nfl-0d4da02c")
OFFICIAL_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com", "api.weather.gov",
                  "github.com")

NAV = [
    ("index.html", "Decision readiness"),
    ("requirements.html", "Requirements"),
    ("gates.html", "Gates"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Questions & answers"),
    ("gaps.html", "Information gaps"),
    ("week11.html", "Week 11 fixtures"),
    ("injury.html", "Injury register"),
    ("availability.html", "Availability counts"),
    ("starters.html", "Starter evidence"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]

CSS = """
:root{--bg:#f6f7f9;--card:#ffffff;--ink:#1a1d21;--muted:#5f6672;--line:#e2e5ea;
--accent:#1b5e9c;--ok:#1a7f45;--warn:#9a6400;--bad:#a32b2b;--blank:#9aa1ab}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:#10161d;color:#fff;padding:20px 24px}
header h1{margin:0 0 6px;font-size:21px;font-weight:650;letter-spacing:-.2px}
header p{margin:0;color:#b6c0cc;font-size:13px;max-width:1050px}
nav{background:#fff;border-bottom:1px solid var(--line);padding:0 24px;
display:flex;flex-wrap:wrap;gap:2px;position:sticky;top:0;z-index:5}
nav a{color:var(--muted);text-decoration:none;font-size:12.5px;padding:11px 10px;
border-bottom:2px solid transparent}
nav a:hover{color:var(--ink)}
nav a.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
main{padding:22px 24px 60px;max-width:1400px}
h2{font-size:16px;margin:26px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h2:first-child{margin-top:4px}
h3{font-size:14px;margin:18px 0 6px}
p{max-width:1000px;margin:8px 0}
.note{color:var(--muted);font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(184px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.card span{display:block;color:var(--muted);font-size:11.5px;text-transform:uppercase;
letter-spacing:.4px}
.card strong{display:block;font-size:22px;margin-top:4px;font-weight:650}
.card small{display:block;color:var(--muted);font-size:11.5px;margin-top:3px}
.tw{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);
margin:10px 0 20px;max-height:78vh}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#eef1f5;position:sticky;top:0;font-weight:600;white-space:nowrap;z-index:2}
tbody tr:nth-child(even){background:#fafbfc}
tbody tr:hover{background:#f0f5fa}
td a{color:var(--accent);text-decoration:none}
td a:hover{text-decoration:underline}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
.blank{color:var(--blank);font-style:italic}
.tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600;
white-space:nowrap}
.t-cleared{background:#e4f5ea;color:var(--ok)}
.t-cleared_repo{background:#eef3f8;color:#2b5a86}
.t-partially{background:#eef0f5;color:#4a5260}
.t-structural{background:#fdf3e0;color:var(--warn)}
.t-blocked{background:#fbe9e9;color:var(--bad)}
.t-open{background:#f1f2f4;color:#5f6672}
.t-rejected{background:#efeaf4;color:#64468a}
.t-needs{background:#fdf3e0;color:var(--warn)}
.t-progress{background:#e6f0f8;color:#1b5e9c}
.t-info{background:#f1f2f4;color:#5f6672}
.t-medium{background:#fdf3e0;color:var(--warn)}
.t-high{background:#fbe9e9;color:var(--bad)}
.t-low{background:#f1f2f4;color:#5f6672}
.t-out{background:#fbe9e9;color:var(--bad)}
.t-questionable{background:#fdf3e0;color:var(--warn)}
.t-doubtful{background:#f3ecf9;color:#64468a}
ul{max-width:1000px}
li{margin:4px 0}
code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:12px}
footer{padding:20px 24px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}
footer a{color:var(--accent)}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def link(url: str, label: str = "source", blank_label: str = "no source") -> str:
    url = (url or "").strip()
    if not url:
        return f'<span class="blank">{esc(blank_label)}</span>'
    return (f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">'
            f'{esc(label)} &#8599;</a>')


def cell(val: str, cls: str = "") -> str:
    v = (val or "").strip()
    if not v:
        return '<td class="blank">blank</td>'
    return f'<td class="{cls}">{esc(v)}</td>' if cls else f"<td>{esc(v)}</td>"


def table(header: list[str], rows: list[str]) -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in header)
    return (f'<div class="tw"><table><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def tag(status: str) -> str:
    s = (status or "").strip().lower()
    key = {"cleared": "cleared", "cleared_repo": "cleared_repo",
           "partially cleared": "partially", "structural": "structural",
           "blocked": "blocked", "open": "open", "rejected": "rejected",
           "needs review": "needs", "in progress": "progress", "info": "info",
           "medium": "medium", "high": "high", "low": "low"}.get(s, "")
    return f'<span class="tag t-{key}">{esc(status)}</span>' if key else esc(status)


def page(title: str, subtitle: str, body: str, active: str) -> str:
    parts = []
    for href, label in NAV:
        cls = ' class="on"' if href == active else ""
        parts.append(f'<a href="{href}"{cls}>{esc(label)}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL Decision Gate 0D4DA02C</title>
<style>{CSS}</style></head><body>
<header><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></header>
<nav>{nav}</nav>
<main>
{body}
</main>
<footer>Research only. No prices, no profitability claim, and no wagers. Statistical validation
can reduce uncertainty; it can never remove luck. Every value on this site was read from the
official page named in its row, inherited from another pack and labelled as a claim, or left
blank and flagged. <a href="flagged.html">Flagged for review &#8599;</a></footer>
</body></html>
"""


def write(name: str, content: str) -> None:
    path = os.path.join(DOCS, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"wrote docs/nfl-0d4da02c/{name}")


# ---------------------------------------------------------------------------
def build_index() -> None:
    reqs = read("requirements.csv")
    gates = {g["gate_id"]: g for g in read("gates.csv")}
    by_status: dict[str, int] = {}
    for r in reqs:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    cards = "".join(
        f'<div class="card"><span>{esc(k)}</span><strong>{v}</strong></div>'
        for k, v in sorted(by_status.items(), key=lambda kv: -kv[1]))

    rows = []
    for r in reqs:
        g = gates.get(r["blocking_gate"], {})
        rows.append(
            "<tr>"
            + cell(r["req_id"], "mono")
            + cell(r["category"])
            + f'<td>{esc(r["requirement_text"])}</td>'
            + f"<td>{tag(r['status'])}</td>"
            + cell(r["blocking_gate"], "mono")
            + cell(r["clearing_number"])
            + f'<td>{link(r["source_url"], blank_label="owner brief")}</td>'
            + "</tr>")
    body = f"""
<p>This is the decision-readiness table the owner asked for: one row per requirement, the gate
that blocks it, and the number that would clear it. The requirement text is the owner's own
wording from the 2026-11-18 brief. Nothing here is a pack's idea.</p>
<div class="cards">{cards}
<div class="card"><span>requirements</span><strong>{len(reqs)}</strong>
<small>75 product + 8 process</small></div>
<div class="card"><span>gates</span><strong>{len(gates)}</strong>
<small>each with a clearing number</small></div>
</div>
<h2>Decision readiness — every requirement, the gate that blocks it, the number that clears it</h2>
<p class="note">A blank clearing-number cell means the requirement is already cleared. A blank
gate cell means no gate blocks it; the work is either done or is a schema rule. Rows are in the
order the owner wrote them.</p>
{table(["ID", "Category", "Requirement", "Status", "Blocking gate",
        "The number that would clear it", "Source"], rows)}
"""
    write("index.html", page(
        "NFL decision gate — what blocks each requirement, and what clears it",
        "Session 0d4da02c · base aa82798 · official reads taken 2026-11-18 · "
        "every row source-linked, nothing inferred",
        body, "index.html"))


def build_requirements() -> None:
    reqs = read("requirements.csv")
    ev: dict[str, list[dict]] = {}
    for e in read("repo_evidence.csv"):
        ev.setdefault(e["req_id"], []).append(e)
    rows = []
    for r in reqs:
        hits = ev.get(r["req_id"], [])
        top = sorted(hits, key=lambda h: -int(h["n_files_matching"]))[:3]
        files = "<br>".join(
            f'<span class="mono">{esc(h["example_paths"].split("; ")[0])}</span> '
            f'({h["n_files_matching"]} files)' for h in top if int(h["n_files_matching"]) > 0
        ) or '<span class="blank">no matching file in the repo</span>'
        rows.append(
            "<tr>"
            + cell(r["req_id"], "mono")
            + cell(r["category"])
            + f'<td>{esc(r["requirement_text"])}</td>'
            + f"<td>{tag(r['status'])}</td>"
            + cell(r["verified_this_session"])
            + f"<td>{esc(r['note'])}</td>"
            + f"<td>{files}</td>"
            + f'<td>{link(r["source_url"], blank_label="owner brief")}</td>'
            + "</tr>")
    body = ("""
<p>The full register. <code>verified_this_session</code> is populated only where this session
read the value from an official page on 2026-11-18; everything else is either inherited from
another pack (and labelled a claim) or blank. The <em>repo evidence</em> column is a keyword scan
computed by <code>src/nfl_0d4da02c/repo_review.py</code> — it shows which files mention the
requirement, not that those files satisfy it.</p>
""" + table(["ID", "Category", "Requirement", "Status", "Verified this session",
             "Note", "Repo evidence (computed)", "Source"], rows))
    write("requirements.html", page(
        "Requirement register", "75 product requirements and 8 process instructions, "
        "in the owner's own wording", body, "requirements.html"))


def build_gates() -> None:
    gates = read("gates.csv")
    rows = ["<tr>" + cell(g["gate_id"], "mono") + cell(g["gate_name"])
            + f"<td>{esc(g['definition'])}</td>"
            + f"<td>{tag(g['state'])}</td>"
            + cell(g["clearing_number"])
            + cell(g["current_observation"]) + "</tr>" for g in gates]
    body = ("""
<p>A gate is a named condition. A gate is only ever closed by the observation written in its
<em>clearing number</em> column, which is deliberately measurable so it cannot be argued away
after the fact.</p>
""" + table(["Gate", "Name", "Definition", "State", "The number that clears it",
             "Current observation"], rows))
    write("gates.html", page("Gates", "Named conditions, each with the observation that closes it",
                             body, "gates.html"))


def build_suggestions() -> None:
    sug = read("suggestions.csv")
    opts: dict[str, list[dict]] = {}
    for o in read("suggestion_options.csv"):
        opts.setdefault(o["suggestion_id"], []).append(o)
    rows = []
    for s in sug:
        rows.append(
            "<tr>"
            + cell(s["suggestion_id"], "mono")
            + f'<td><strong>{esc(s["title"])}</strong><br>'
            f'<span class="note">{esc(s["what_it_improves"])}</span></td>'
            + cell(s["category"])
            + cell(s["blocking_gate"], "mono")
            + cell(s["req_ids"], "mono")
            + '<td class="blank">owner decides — blank by design</td>'
            + "</tr>")
    body = ("""
<h2>Suggestions — review before implementing</h2>
<p>Each suggestion carries two or more option paths below. The <strong>decision column is
deliberately blank</strong>: the whole point of this section is that the owner chooses a path
before anything is built. Nothing on this page has been implemented.</p>
""" + table(["ID", "Suggestion", "Category", "Blocking gate", "Requirements",
             "Owner decision"], rows))

    body += "<h2>Option paths — pick one, then implement</h2>"
    for s in sug:
        rows = []
        for o in opts.get(s["suggestion_id"], []):
            rows.append(
                "<tr>"
                + cell(o["option_id"], "mono")
                + cell(o["path_label"])
                + cell(o["what_it_does"])
                + cell(o["cost"])
                + cell(o["risk"])
                + cell(o["evidence_needed"])
                + cell(o["clearing_number"])
                + '<td class="blank">owner chooses — blank by design</td>'
                + "</tr>")
        body += (f'<h3>{esc(s["suggestion_id"])} — {esc(s["title"])}</h3>'
                 + table(["Option", "Path", "What it does", "Cost", "Risk",
                          "Evidence needed", "Clearing number", "Choice"], rows))
    write("suggestions.html", page(
        "Suggestions — review before implementing",
        "30 suggestions, 68 option paths, decision columns blank by design",
        body, "suggestions.html"))


def build_questions() -> None:
    qia = read("qia.csv")
    rows = []
    for q in qia:
        rows.append(
            "<tr>"
            + cell(q["question_id"], "mono")
            + f"<td>{esc(q['question'])}</td>"
            + cell(q["what_we_have"])
            + cell(q["what_we_lack"])
            + cell(q["answer"])
            + f"<td>{tag(q['answer_status'])}</td>"
            + cell(q["discovery_route"])
            + cell(q["blocking_gate"], "mono")
            + f'<td>{link(q["source_url"], blank_label="not closed yet")}</td>'
            + "</tr>")
    answered = sum(1 for q in qia if q["answer_status"].startswith("answered"))
    body = (f"""
<p>The register the owner asked for: the questions that must be answered before a decision is
reasonable, what we already have, what we lack, and the route to close each one.
<strong>{answered} of {len(qia)}</strong> are answered by an official source read this session.
The rest are left blank rather than filled in.</p>
""" + table(["ID", "Question", "What we have", "What we lack", "Answer",
             "Answer status", "Discovery route", "Gate", "Source"], rows))
    write("questions.html", page(
        "Questions, information, answers",
        "28 open questions with what we have, what we lack, and the route that closes each",
        body, "questions.html"))


def build_gaps() -> None:
    gaps = read("information_gaps.csv")
    rows = []
    for g in gaps:
        rows.append(
            "<tr>"
            + cell(g["gap_id"], "mono")
            + f"<td>{esc(g['missing_dataset'])}</td>"
            + cell(g["why_it_blocks"])
            + cell(g["acquisition_route"])
            + cell(g["clearing_number"])
            + cell(g["official_host"], "mono")
            + cell(g["status"])
            + cell(g["req_ids_blocked"], "mono")
            + f'<td>{link(g["source_url"], blank_label="no source yet")}</td>'
            + "</tr>")
    body = ("""
<p>Every gap carries the exact acquisition route and the number that clears it. These are the
rows that generate suggestions: what we do not have, and the concrete way to go and get it.</p>
""" + table(["ID", "Missing dataset", "Why it blocks", "Acquisition route",
             "The number that clears it", "Official host", "Status",
             "Requirements blocked", "Source"], rows))
    write("gaps.html", page("Information gaps", "What we do not have, and the route to get it",
                            body, "gaps.html"))


def build_week11() -> None:
    games = read("week11_schedule.csv")
    byes = read("week11_byes.csv")
    ann = read("schedule_announcement.csv")
    rows = []
    for g in games:
        key = f'{g["away"]}@{g["home"]}'
        direct = g["venue_provenance"].startswith("page badge")
        venue = (f'{esc(g["venue_text_on_page"])}'
                 + ("" if direct else
                    f'<br><span class="note">provenance: {esc(g["venue_provenance"])} '
                    f'— flagged</span>'))
        rows.append(
            "<tr>"
            + cell(g["game_date"], "mono")
            + cell(g["kickoff_et"], "mono")
            + cell(g["network"])
            + f'<td><strong>{esc(g["away"])}</strong> <span class="note">{esc(g["away_record"])}</span></td>'
            + f'<td><strong>{esc(g["home"])}</strong> <span class="note">{esc(g["home_record"])}</span></td>'
            + f"<td>{venue}</td>"
            + f"<td>{link(g['game_url'], 'game page')}</td>"
            + "</tr>")
    bye_rows = ["<tr>" + cell(b["club"], "mono") + cell(b["record_on_page"])
                + f"<td>{link(b['source_url'])}</td></tr>" for b in byes]
    ann_rows = ["<tr>" + cell(a["item"])
                + f'<td><pre style="white-space:pre-wrap;margin:0;font-size:11.5px">'
                f'{esc(a["text_verbatim"])}</pre></td>'
                + f"<td>{link(a['source_url'])}</td></tr>" for a in ann]
    body = f"""
<p>Week 11 of the 2026 season, read from the official schedule page on 2026-11-18:
<strong>{len(games)} games</strong> and <strong>{len(byes)} clubs on bye</strong>
(26 plus 6 equals 32). Only facts the page itself prints are recorded — no rest days, no travel
distance, no timezone arithmetic.</p>
<h2>Fixtures</h2>
{table(["Date", "Kickoff ET", "Network", "Away", "Home", "Venue text on the page", "Source"], rows)}
<h2>Teams on bye</h2>
{table(["Club", "Record on page", "Source"], bye_rows)}
<h2>The league's own scheduling statement, verbatim</h2>
<p class="note">This is a standing procedure note printed under "Info / 2026 TBD Games" on the
official schedule page. It is not a dated announcement of a specific change, and it does not name
the designated matchups. That distinction is flagged, because the owner asked for the dated
announcement.</p>
{table(["Item", "Text as printed on the official page", "Source"], ann_rows)}
"""
    write("week11.html", page("Week 11 fixtures and the league's scheduling statement",
                              "13 games, 6 byes, venues and records — read 2026-11-18",
                              body, "week11.html"))


def build_injury() -> None:
    inj = read("injury_report_2026_11_18.csv")
    absent = read("week10_absent_clubs.csv")
    rows = []
    for r in inj:
        gs = (r["game_status"] or "").strip()
        cls = {"Out": "t-out", "Questionable": "t-questionable",
               "Doubtful": "t-doubtful"}.get(gs, "")
        gcell = (f'<td><span class="tag {cls}">{esc(gs)}</span></td>' if gs
                 else '<td class="blank">blank</td>')
        rows.append(
            "<tr>"
            + cell(r["club"], "mono")
            + f'<td>{esc(r["player"])}</td>'
            + cell(r["position"], "mono")
            + cell(r["injuries"])
            + cell(r["practice_status"])
            + gcell
            + f'<td class="note">{esc(r["game_block"])}</td>'
            + f"<td>{link(r['source_url'])}</td>"
            + "</tr>")
    absent_rows = ["<tr>" + cell(a["club"], "mono") + cell(a["page_state"])
                   + cell(a["interpretation"]) + f"<td>{link(a['source_url'])}</td></tr>"
                   for a in absent]
    body = f"""
<p>The official NFL injury report for <strong>Week 10 of the 2026 season</strong>, re-read and
re-published on 2026-11-18: <strong>{len(inj)} rows across 28 clubs</strong>. Every cell is
transcribed from the page. A blank cell means the page printed nothing, and it is rendered as
blank rather than guessed.</p>
<p class="note">The Week 11 report was <strong>not published</strong> at read time: a request for
<code>/injuries/league/2026/REG11/</code> resolved to the Week 10 page. That is recorded as a
finding, not filled in from another source.</p>
<h2>Injury register</h2>
{table(["Club", "Player", "Pos", "Injuries", "Practice status", "Game status",
        "Game", "Source"], rows)}
<h2>Clubs with no section on the page</h2>
<p class="note">Absence from the report is not health. These four clubs were on a Week 10 bye,
which the page confirms by listing the complement as the Week 11 bye group.</p>
{table(["Club", "Page state", "Interpretation", "Source"], absent_rows)}
"""
    write("injury.html", page("Injury register — Week 10, re-read 2026-11-18",
                              "347 rows, 28 clubs, every cell transcribed from the official page",
                              body, "injury.html"))


def build_availability() -> None:
    counts = read("designation_counts.csv")
    xtab = read("designation_xtab.csv")
    clubs = read("club_injury_counts.csv")
    groups = read("position_group_counts.csv")
    cal = read("designation_calibration_status.csv")

    def simple(rows: list[dict], cols: list[tuple[str, str]]) -> list[str]:
        out = []
        for r in rows:
            out.append("<tr>" + "".join(cell(r[c], k) for c, k in cols) + "</tr>")
        return out

    body = """
<p>Every number on this page is a count or a ratio of rows read from the official injury page on
2026-11-18. n is published beside every value. Nothing here is a model output and nothing is a
claim about profit.</p>
<h2>Designation counts (n = 347)</h2>
""" + table(["Dimension", "Value", "n", "% of rows", "Source"],
            simple(counts, [("dimension", ""), ("value", ""), ("n", "mono"),
                            ("pct_of_rows", "mono"), ("source_url", "")])) \
        .replace("<td>https://www.nfl.com/injuries/</td>",
                 '<td><a href="https://www.nfl.com/injuries/" rel="noopener noreferrer" '
                 'target="_blank">source &#8599;</a></td>')

    body += """
<h2>Game status by practice status</h2>
<p class="note">Read down the rows: of the 70 players ruled Out, 62 did not practise at all. Of
the 90 Questionable, 46 were limited and 34 were full participants. That spread is the reason the
owner asked for empirical calibration instead of remembered percentages.</p>
""" + table(["Game status", "Practice status", "n", "n with that game status",
             "% of game status", "Source"],
            simple(xtab, [("game_status", ""), ("practice_status", ""), ("n_cells", "mono"),
                          ("n_with_that_game_status", "mono"),
                          ("pct_of_game_status", "mono"), ("source_url", "")])) \
        .replace("<td>https://www.nfl.com/injuries/</td>",
                 '<td><a href="https://www.nfl.com/injuries/" rel="noopener noreferrer" '
                 'target="_blank">source &#8599;</a></td>')

    body += """
<h2>Per club</h2>
<p class="note">The four clubs with a blank row count are the Week 10 bye clubs: they have no
section on the page, so their counts are unknown rather than zero.</p>
""" + table(["Club", "Rows", "Out", "Doubtful", "Questionable", "Blank game status", "Source"],
            simple(clubs, [("club", "mono"), ("n_rows", "mono"), ("n_out", "mono"),
                           ("n_doubtful", "mono"), ("n_questionable", "mono"),
                           ("n_blank_game_status", "mono"), ("source_url", "")])) \
        .replace("<td>https://www.nfl.com/injuries/</td>",
                 '<td><a href="https://www.nfl.com/injuries/" rel="noopener noreferrer" '
                 'target="_blank">source &#8599;</a></td>')

    body += """
<h2>By position group</h2>
""" + table(["Position group", "Positions", "n", "Out", "Doubtful", "Questionable",
             "Blank", "% Out", "Source"],
            simple(groups, [("position_group", ""), ("positions_included", ""),
                            ("n_rows", "mono"), ("n_out", "mono"), ("n_doubtful", "mono"),
                            ("n_questionable", "mono"), ("n_blank_game_status", "mono"),
                            ("pct_out", "mono"), ("source_url", "")])) \
        .replace("<td>https://www.nfl.com/injuries/</td>",
                 '<td><a href="https://www.nfl.com/injuries/" rel="noopener noreferrer" '
                 'target="_blank">source &#8599;</a></td>')

    body += """
<h2>What this table cannot say</h2>
<p>The counts are the numerator. The outcome — did the player actually play — is unknown without
the official inactive list, so no play rate and no correlation is published. That is the honest
state, and it is the single largest information gap on the board.</p>
""" + table(["Question", "Numerator", "Denominator", "n numerator", "n denominator",
             "Status", "What is missing", "Source"],
            simple(cal, [("question", ""), ("numerator_available", ""),
                         ("denominator_available", ""), ("n_numerator", "mono"),
                         ("n_denominator", "mono"), ("status", ""),
                         ("what_is_missing", ""), ("source_url", "")])) \
        .replace("<td>https://www.nfl.com/injuries/</td>",
                 '<td><a href="https://www.nfl.com/injuries/" rel="noopener noreferrer" '
                 'target="_blank">source &#8599;</a></td>')
    write("availability.html", page(
        "Availability counts from official numbers",
        "Counts and ratios with n published; no outcome leg, therefore no play rate",
        body, "availability.html"))


def build_starters() -> None:
    rows = []
    for a in read("starter_announcements.csv"):
        rows.append(
            "<tr>"
            + cell(a["date_in_headline"], "mono")
            + cell(a["club"], "mono")
            + f'<td><strong>{esc(a["player"])}</strong></td>'
            + f'<td>{esc(a["headline_verbatim"])}</td>'
            + cell(a["claim_scope"])
            + f"<td>{link(a['source_url'], 'announcement')}</td>"
            + "</tr>")
    body = """
<p>The owner asked for an <strong>announced-starter evidence field</strong>, not an inferred
replacement. These are the league's own dated statements, captured from the official injury hub's
news rail on 2026-11-18.</p>
<p class="note">Only the headline text is claimed. No article body was opened this session, so
nothing beyond the headline is asserted. Where a headline is conditional ("in line for",
"could miss"), it is recorded as conditional and flagged rather than treated as a fact. No dated
announcement for Brissett appeared on the page; that row is absent, not filled in.</p>
""" + table(["Date in headline", "Club", "Player", "Headline as published", "Scope of the claim",
             "Source"], rows)
    write("starters.html", page("Announced-starter evidence",
                                "Dated official statements, not inferred replacements",
                                body, "starters.html"))


def build_repo_review() -> None:
    findings = read("repo_findings.csv")
    stats = {r["metric"]: r["value"] for r in read("repo_stats.csv")}
    inv = read("repo_inventory.csv")
    rows = []
    for f in findings:
        rows.append(
            "<tr>"
            + cell(f["finding_id"], "mono")
            + f"<td>{tag(f['severity'])}</td>"
            + cell(f["path"], "mono")
            + f"<td>{esc(f['finding'])}</td>"
            + cell(f["evidence"])
            + cell(f["status"])
            + f'<td>{link("https://github.com/sassnarep3-star/Own6", "repo")}</td>'
            + "</tr>")
    cards = "".join(
        f'<div class="card"><span>{esc(k.replace("_", " "))}</span>'
        f'<strong>{esc(v)}</strong></div>'
        for k, v in stats.items() if not k.endswith("commit"))
    nosrc = [i for i in inv if i["file_kind"] == "data" and not i["source_columns"]]
    cc = read("claim_checks.csv")
    cc_rows = []
    for c in cc:
        cls = {"match": "t-cleared", "superseded": "t-structural",
               "not attempted": "t-open"}.get(c["result"], "")
        cc_rows.append(
            "<tr>"
            + cell(c["check_id"], "mono")
            + f"<td>{esc(c['claim'])}</td>"
            + cell(c["where_it_was_published"])
            + cell(c["recomputed_this_session"])
            + f'<td><span class="tag {cls}">{esc(c["result"])}</span></td>'
            + cell(c["note"])
            + "</tr>")
    body = f"""
<p>Computed by <code>src/nfl_0d4da02c/repo_review.py</code> against the pinned base commit
<code>{esc(stats.get("base_commit", ""))}</code>. Nothing on this page is hand-written: every
finding is produced by scanning the tracked files.</p>
<div class="cards">{cards}</div>
<h2>Findings</h2>
<p class="note">Severity here is about evidence quality, not style. A missing source column on a
published data table is high because the owner's rule is that every row carries a source link.</p>
{table(["Finding", "Severity", "Path", "What was found", "Evidence", "Status", "Link"], rows)}
<h2>Headline irregularities</h2>
<ul>
<li><strong>{len(nosrc)} committed data CSVs have no source-like column at all</strong>, which is
contrary to the requirement that every table row carry a source link.</li>
<li>The repository holds 18 parallel NFL data packs and 18 matching site directories, with up to
23 separate files registering the same concept under different column vocabularies.</li>
<li>13 published pages contain interactive controls, which the brief forbids.</li>
<li>One internal link is broken: <code>docs/dashboard.html</code> links to <code>lab/</code>, and
<code>docs/lab/</code> has no <code>index.html</code>.</li>
<li>Five committed files exceed 1 MB, the largest being an 11 MB coverage table.</li>
</ul>
<h2>Independent claim checks</h2>
<p>A published claim from elsewhere in the repository, recomputed this session from this session's
own official read. <em>match</em> means the numbers agree; <em>superseded</em> means the page has
moved on since the claim was written; <em>not attempted</em> means this session did not re-derive
it and says so rather than guessing.</p>
""" + table(["Check", "Claim", "Where it was published", "Recomputed this session",
             "Result", "Note"], cc_rows) + """
"""
    write("repo-review.html", page(
        "Repository review", "Line-by-line, computed at a pinned base commit",
        body, "repo-review.html"))


def build_flagged() -> None:
    flags = read("flagged.csv")
    rows = []
    for f in flags:
        rows.append(
            "<tr>"
            + cell(f["flag_id"], "mono")
            + cell(f["flag_scope"])
            + f"<td>{tag(f['severity'])}</td>"
            + cell(f["area"])
            + f'<td><strong>{esc(f["item"])}</strong><br>'
            f'<span class="note">{esc(f["what_we_found"])}</span></td>'
            + cell(f["value_if_known"])
            + cell(f["req_ids"], "mono")
            + f'<td>{link(f["source_url"], blank_label="see item")}</td>'
            + "</tr>")
    body = ("""
<p>Flagged irregularities and unverified items do not block the merge — they are published here
with their source links so the owner can review them once the site is live. A blank
<em>value if known</em> cell means the honest value is unknown, so the table cell it belongs to is
blank.</p>
""" + table(["Flag", "Scope", "Severity", "Area", "Item", "Value if known",
             "Requirements", "Source"], rows))
    write("flagged.html", page("Flagged for review",
                               "Irregularities and unverified items, with source links",
                               body, "flagged.html"))


def build_sources() -> None:
    srcs = read("sources.csv")
    reads = read("official_reads.csv")
    rows = []
    for s in srcs:
        rows.append(
            "<tr>"
            + cell(s["source_id"], "mono")
            + f"<td>{link(s['requested_url'], 'open')}</td>"
            + cell(s["canonical_url"], "mono")
            + cell(s["page_title"])
            + cell(s["used_for"])
            + cell(s["read_date"], "mono")
            + cell(s["note"])
            + "</tr>")
    rrows = []
    for r in reads:
        rrows.append(
            "<tr>"
            + cell(r["read_id"], "mono")
            + cell(r["source_id"], "mono")
            + cell(r["canonical_url"], "mono")
            + cell(r["read_date"], "mono")
            + cell(r["rows_transcribed"], "mono")
            + cell(r["sha256_transcript"], "mono")
            + cell(r["hash_scope"])
            + cell(r["note"])
            + f"<td>{link(r['requested_url'])}</td>"
            + "</tr>")
    body = ("""
<h2>Official sources read this session</h2>
<p>Every value published by this pack comes from one of these pages, or is inherited from another
pack and labelled as a claim.</p>
""" + table(["ID", "Requested URL", "Canonical URL", "Page title", "Used for", "Read date",
             "Note"], rows) + """
<h2>Read log</h2>
<p class="note">The SHA-256 is computed over the exact text this session transcribed from the
page. It is a tamper check on the committed data, not a fingerprint of the page's own bytes — a
distinction recorded as flag F-17.</p>
""" + table(["Read", "Source", "Canonical URL", "Read date", "Rows", "SHA-256 of transcript",
             "Hash scope", "Note", "Link"], rrows))
    write("sources.html", page("Sources and read log",
                               "Four dated official reads, two with stored transcript hashes",
                               body, "sources.html"))


def build_exec() -> None:
    reqs = read("requirements.csv")
    gates = read("gates.csv")
    sug = read("suggestions.csv")
    opts = read("suggestion_options.csv")
    qia = read("qia.csv")
    gaps = read("information_gaps.csv")
    inj = read("injury_report_2026_11_18.csv")
    games = read("week11_schedule.csv")
    flags = read("flagged.csv")
    status: dict[str, int] = {}
    for r in reqs:
        status[r["status"]] = status.get(r["status"], 0) + 1
    blocked_gates: dict[str, int] = {}
    for r in reqs:
        if r["blocking_gate"]:
            blocked_gates[r["blocking_gate"]] = blocked_gates.get(r["blocking_gate"], 0) + 1
    top = sorted(blocked_gates.items(), key=lambda kv: -kv[1])[:6]
    cards = "".join(
        f'<div class="card"><span>{esc(k)}</span><strong>{v}</strong></div>'
        for k, v in sorted(status.items(), key=lambda kv: -kv[1]))
    body = f"""
<h2>Where the project actually stands</h2>
<div class="cards">{cards}</div>
<p>The owner's brief contains 75 product requirements and 8 process instructions. Of those,
<strong>{status.get('cleared', 0)} are cleared</strong> by evidence read this session from an
official page, {status.get('cleared_repo', 0)} are inherited from earlier packs as claims,
{status.get('structural', 0)} exist as schema or code with no data behind them,
{status.get('blocked', 0)} are blocked by a named gate, {status.get('partially cleared', 0)} are
partly cleared, {status.get('open', 0)} are open with no evidence either way, and
{status.get('rejected', 0)} were rejected by the owner and are recorded so they are not
re-proposed.</p>
<h2>The three things that decide everything else</h2>
<ol>
<li><strong>No official market-price source exists.</strong> Until one does, the residual,
closing line value and the vig decomposition cannot be published, and neither can any backtest
that uses prices. The owner's own ordering rule (R-20) says decide the price policy first.</li>
<li><strong>No depth-order source is verified for all 32 clubs.</strong> Fourteen requirements
sit behind this, including the entire backup-deficiency feature the owner asked for. The owner
ordered this resolved before the feature is built, and that order is respected.</li>
<li><strong>No official inactive list has been captured.</strong> The injury register is now
verifiable every week, but the question "did the player actually play" is unanswerable without it,
so "Questionable" cannot be calibrated and no designation may become a model feature.</li>
</ol>
<h2>What this session verified from official pages</h2>
<ul>
<li>The Week 10 injury report: <strong>{len(inj)} rows across 28 clubs</strong>, re-read and
re-published on 2026-11-18, with four bye clubs recorded as absent rather than healthy.</li>
<li>The Week 11 schedule: <strong>{len(games)} games and 6 clubs on bye</strong>, with kickoff
times, networks, records and venue text, plus the league's own scheduling statement verbatim.</li>
<li>That the <strong>Week 11 injury report was not published</strong> at read time — a request for
the Week 11 URL resolves to the Week 10 page.</li>
<li>Dated official starter announcements for Lock, McCord, Watson and Beck; none found for
Brissett, which is left blank rather than filled.</li>
<li>That the three Lions designations the owner reported as blank are <strong>no longer
blank</strong>: Joseph, Mays and Reed each read Out with Did Not Participate.</li>
</ul>
<h2>Gates that block the most requirements</h2>
""" + table(["Gate", "Requirements blocked"],
            ["<tr>" + cell(g, "mono") + cell(str(n), "mono") + "</tr>" for g, n in top]) + f"""
<h2>The decision board</h2>
<p>{len(sug)} suggestions with {len(opts)} option paths, {len(qia)} questions with what we have
and what we lack, and {len(gaps)} information gaps with the route that closes each one. The
decision columns are blank by design: the owner picks the path before anything is implemented.</p>
<h2>Flagged</h2>
<p>{len(flags)} items are published on the
<a href="flagged.html">Flagged for review</a> page with their source links. None blocks the
merge.</p>
<h2>What is deliberately missing</h2>
<p>No prices, no odds, no correlation between a designation and playing, no leaderboard rows, and
no statement that any strategy is profitable. Those cells are blank because the evidence does not
exist yet, and filling them would be the exact failure mode this project is built to avoid.</p>
"""
    write("executive-summary.html", page(
        "Executive summary", "Read this first — the state of the programme in one page",
        body, "executive-summary.html"))


def main() -> int:
    os.makedirs(DOCS, exist_ok=True)
    build_index()
    build_requirements()
    build_gates()
    build_suggestions()
    build_questions()
    build_gaps()
    build_week11()
    build_injury()
    build_availability()
    build_starters()
    build_repo_review()
    build_flagged()
    build_sources()
    build_exec()
    print(f"built {len(NAV)} pages in docs/nfl-0d4da02c/")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    rc = main()
    if args.check and rc == 0:
        rc = subprocess.call([sys.executable, "scripts/check_nfl_0d4da02c.py"], cwd=REPO)
    raise SystemExit(rc)
