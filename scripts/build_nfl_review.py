#!/usr/bin/env python3
"""Build the consolidated NFL review dashboard (docs/nfl-review/).

Session arena/44136693-own6 (2026-11-13).

The site is generated from the CSV registers in ``data/nfl_review/``. It has no
input element, so it never asks the owner for anything. Every table row carries
a link to the official page the row was read from; a value that could not be
confirmed from an official source is published as an empty cell and flagged on
the Flagged for Review page.

Usage:
    python3 scripts/build_nfl_review.py           # write docs/nfl-review/
    python3 scripts/build_nfl_review.py --check   # verify the committed pages
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl_review")
OUT = os.path.join(ROOT, "docs", "nfl-review")
ASSETS = os.path.join(OUT, "assets")

SELF = "https://sassnarep3-star.github.io/Own6/docs/nfl-review/"
BASE = "https://sassnarep3-star.github.io/Own6/docs/"

NAV = [
    ("index.html", "Overview"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions &amp; answers"),
    ("suggestions.html", "Suggestions (review)"),
    ("strategies.html", "Strategies, gates &amp; leaderboard"),
    ("injuries.html", "Injuries &amp; depth"),
    ("verification.html", "Verification ledger"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]

CSS = """:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--ink:#e6edf3;--muted:#9198a1;--accent:#4c8eda;--warn:#d29922;--bad:#f85149;--good:#3fb950}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:14px 20px;position:sticky;top:0;z-index:5}
header .brand{font-weight:700;letter-spacing:.5px;color:var(--ink);margin-right:18px}
nav a{display:inline-block;padding:6px 10px;color:var(--muted);border-radius:6px;font-size:14px}
nav a.active,nav a:hover{background:#1f6feb22;color:var(--ink);text-decoration:none}
main{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
h1{font-size:26px;margin:6px 0 8px}h2{font-size:19px;margin:30px 0 10px}h3{font-size:16px;margin:22px 0 8px}
p.lede{color:var(--muted);max-width:80ch}
.kpis{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0 8px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-width:150px}
.kpi .n{font-size:22px;font-weight:700}.kpi .l{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.6px}
table{width:100%;border-collapse:collapse;margin:12px 0 6px;font-size:13.5px;background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#1b222b;font-weight:600;color:#c9d1d9;font-size:12.5px;text-transform:uppercase;letter-spacing:.4px}
tr:last-child td{border-bottom:none}
td.num{text-align:right;white-space:nowrap}
code{background:#1b222b;padding:1px 5px;border-radius:4px;font-size:12.5px}
.badge{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11.5px;border:1px solid var(--line);white-space:nowrap}
.b-ok{color:var(--good);border-color:#2ea04366;background:#2ea0431a}
.b-warn{color:var(--warn);border-color:#d2992266;background:#d299221a}
.b-bad{color:var(--bad);border-color:#f8514966;background:#f851491a}
.b-info{color:var(--muted)}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:6px;padding:10px 13px;margin:14px 0;color:#c9d1d9}
.note.warn{border-left-color:var(--warn)}.note.bad{border-left-color:var(--bad)}.note.good{border-left-color:var(--good)}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:12.5px;padding:18px 20px;max-width:1180px;margin:0 auto}
.small{font-size:12.5px;color:var(--muted)}
ul{padding-left:20px}li{margin:4px 0}
"""


def load(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(value):
    return (str(value if value is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def link(url, label=None):
    if not url:
        return '<span class="badge b-info">no link</span>'
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label or url)}</a>'


def badge(text, kind="info"):
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


def status_badge(text, kind=None):
    t = (text or "").strip().lower()
    if kind:
        return badge(text, kind)
    if t in ("match", "verified", "pass", "done", "verified_today"):
        return badge(text, "ok")
    if t in ("differs", "fail", "needs review", "needs_review", "open"):
        return badge(text, "warn")
    if t in ("not_found_in_2026_11_13_capture", "unverified_no_player_named", "not_checked"):
        return badge(text, "bad")
    return badge(text, "info")


def page(title, active, body, lede=None):
    nav = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>'
        for href, label in NAV
    )
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} &middot; Own6 NFL review</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header><span class="brand">OWN6 / NFL REVIEW</span><nav aria-label="Primary">{nav}</nav></header>
<main>
<h1>{title}</h1>
{lede_html}
{body}
</main>
<footer>Built deterministically from <code>data/nfl_review/</code> by <code>scripts/build_nfl_review.py</code>.
Every table row links to the official page the row was read from. A blank cell means the value could not be
confirmed from an official source; those rows are listed on the
<a href="flagged.html">Flagged for Review</a> page. This is research output: it asserts no betting edge,
no profit and no legal authorisation. Session <code>arena/44136693-own6</code>, read date 2026-11-13.</footer>
</body>
</html>
"""


def table(headers, rows, empty_note="No rows."):
    if not rows:
        return f'<p class="small">{esc(empty_note)}</p>'
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    return (f'<table><thead><tr>{head}</tr></thead><tbody>'
            + "".join(body)
            + "</tbody></table>")


# --------------------------------------------------------------------------
def build_index():
    recon = load("value_reconciliation.csv")
    counts = {}
    for r in recon:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    lede = ("A single, decision-ready view of the NFL work in this repository: what the owner asked for, "
            "what is actually answered today, what is still missing, which suggestions should be chosen "
            "first, and which published numbers were re-read against an official source on 2026-11-13.")
    kpis = [
        ("Requirements tracked", "16", "info"),
        ("Published values re-read", str(len(recon)), "info"),
        ("Matched the official read", str(counts.get("match", 0)), "ok"),
        ("Differ from today's read", str(counts.get("differs", 0)), "warn"),
        ("Qualified strategies", "0", "warn"),
        ("Open flags", str(len(load("irregularities.csv"))), "warn"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="n">{esc(n)}</div><div class="l">{esc(l)}</div></div>' for n, l, _ in kpis
    )
    body = f"""
<div class="kpis">{kpi_html}</div>
<div class="note"><strong>Bottom line.</strong> The repository can describe the NFL problem in detail and can
originate model lines, but it cannot yet produce a qualified strategy, a verified price, a measured NFL
correlation or a completed depth-deficiency score, because no licensed price feed, no licensed play-by-play
feed and no complete club depth-chart capture exist. Nothing on this site claims an edge, a profit or a skill
result, and every leaderboard in the repository is empty by design.</div>
<div class="note warn"><strong>Read this first if you only read one page.</strong>
<a href="suggestions.html">Suggestions (review)</a> holds the ranked improvement register and three candidate
paths, with the decisions that are waiting on you. <a href="questions.html">Questions &amp; answers</a> holds
the sixteen decisions that must be settled before any strategy can be judged.</div>
<h2>How to use this section</h2>
<table><thead><tr><th>Page</th><th>What it answers</th><th>For</th><th>Source</th></tr></thead><tbody>
<tr><td><a href="requirements.html">Requirements</a></td><td>Every requirement in the brief, where it is addressed, and whether it is answered today</td><td>Checking coverage</td><td>{link(SELF + "requirements.html", "live page")}</td></tr>
<tr><td><a href="questions.html">Questions &amp; answers</a></td><td>The information held, the information missing, the current answer and how to obtain the rest</td><td>Making a decision</td><td>{link(SELF + "questions.html", "live page")}</td></tr>
<tr><td><a href="suggestions.html">Suggestions (review)</a></td><td>Eighteen ranked improvements, the owner decisions required, and three candidate paths</td><td>Choosing what to build next</td><td>{link(SELF + "suggestions.html", "live page")}</td></tr>
<tr><td><a href="strategies.html">Strategies, gates &amp; leaderboard</a></td><td>The 27 registered strategies, the gate sets, the correlation position and the empty leaderboard</td><td>Running the competition</td><td>{link(SELF + "strategies.html", "live page")}</td></tr>
<tr><td><a href="injuries.html">Injuries &amp; depth</a></td><td>The official Week 10 availability read and the depth-deficiency coverage per club</td><td>Backup and starter tracking</td><td>{link(SELF + "injuries.html", "live page")}</td></tr>
<tr><td><a href="verification.html">Verification ledger</a></td><td>Every published value compared with the official read, one row per claim</td><td>Trusting a number</td><td>{link(SELF + "verification.html", "live page")}</td></tr>
<tr><td><a href="flagged.html">Flagged for review</a></td><td>Every irregularity and every unconfirmed value, with the source and the requested action</td><td>Reviewing before the next change</td><td>{link(SELF + "flagged.html", "live page")}</td></tr>
<tr><td><a href="sources.html">Sources</a></td><td>The official pages read on 2026-11-13 and what each one does and does not support</td><td>Manual review</td><td>{link(SELF + "sources.html", "live page")}</td></tr>
</tbody></table>
<h2>The four NFL sections in this repository</h2>
<table><thead><tr><th>Section</th><th>What it holds</th><th>Status</th><th>Source</th></tr></thead><tbody>
<tr><td><a href="../nfl/index.html">NFL Lab</a></td><td>Requirement traceability R01-R18, decision questions Q01-Q10, suggestions S01-S12, ten frozen strategies N01-N10, ten gates G01-G10, correlation specifications C01-C08, injury and depth model</td><td>published 2026-11-12</td><td>{link(BASE + "nfl/index.html", "live section")}</td></tr>
<tr><td><a href="../nfl-origination/index.html">NFL Origination</a></td><td>Requirements matrix, decision Q&amp;A (16), site suggestions (14), ten preregistered strategies, twelve gates, twelve combo correlation specifications, 24 verified Week 10 depth chains, executive summary</td><td>published 2026-11-12</td><td>{link(BASE + "nfl-origination/index.html", "live section")}</td></tr>
<tr><td><a href="../nfl-3b81013c/index.html">NFL Week 10 pack</a></td><td>Verified Week 10 registers, 14 originated lines, 49 injury and depth rows, 34 depth groups, 12 correlation bound sets, open questions</td><td>published 2026-11-12</td><td>{link(BASE + "nfl-3b81013c/index.html", "live section")}</td></tr>
<tr><td><a href="../nfl/lab/index.html">NFL lines lab</a></td><td>Reproducible pipeline on a community 2015-2026 game log: model lines, backtests with clustered intervals, correlation estimates, availability model</td><td>published 2026-11-13 (PR #68, independently verified and merged into the review branch)</td><td>{link(BASE + "nfl/lab/index.html", "live section")}</td></tr>
</tbody></table>
<div class="note"><strong>Why four sections exist.</strong> Three parallel sessions each built an NFL pack before
the work was coordinated. Merging them is possible but is a decision, not a cleanup: suggestion S-05 proposes one
canonical entry point with the others kept as evidence archives, suggestion S-06 proposes retiring two of them.
This page deliberately does not delete any published pack.</div>
"""
    return page("NFL review and decision pack", "index.html", body, lede)


def build_requirements():
    rows = []
    for r in load("requirement_coverage.csv"):
        rows.append([
            esc(r["requirement_id"]),
            esc(r["requirement_as_stated_by_the_owner"]),
            esc(r["where_addressed_in_this_repository"]),
            status_badge(r["verification_status_on_2026_11_13"]),
            esc(r["finding"]),
            link(r["official_or_primary_source_url"], "source"),
        ])
    body = (
        "<p class=\"lede\">Every requirement in the brief, the place in this repository that addresses it, and "
        "whether the official re-read on 2026-11-13 confirms it.</p>"
        + table(["ID", "Requirement as stated", "Where it is addressed", "Status on 2026-11-13", "Finding", "Source"], rows)
    )
    return page("Requirement coverage", "requirements.html", body)


def build_questions():
    rows = []
    for r in load("decision_questions.csv"):
        rows.append([
            esc(r["question_id"]),
            esc(r["topic"]),
            esc(r["question_to_decide"]),
            esc(r["information_held_today"]),
            esc(r["information_missing"]),
            status_badge(r["answer_status"]),
            esc(r["current_answer"]),
            esc(r["how_to_discover_the_missing_information"]),
            esc(r["priority"]),
            link(r["evidence_source_url"], "source"),
        ])
    body = (
        "<p class=\"lede\">The questions that must be answered before a decision can reasonably be made, what is "
        "known today, what is missing, and the specific action that would obtain the missing information. "
        "Answering a question here does not require manual input from the owner: each row states the action and "
        "the party who must take it.</p>"
        + table(["ID", "Topic", "Question", "Information held today", "Information missing", "Answer status",
                 "Current answer", "How to discover the missing information", "Priority", "Source"], rows)
        + "<div class=\"note\"><strong>Three answers block everything else.</strong> "
          "<code>Q01</code> (a market price source), <code>Q02</code> (closing lines) and "
          "<code>Q04</code> (a licence for the historical data). Until a price exists, no edge, no closing-line "
          "value, no return figure and no leaderboard reward can be computed, and every profitability statement "
          "would be an assumption rather than a measurement.</div>"
    )
    return page("Questions, information and answers", "questions.html", body)


def build_suggestions():
    rows = []
    for r in sorted(load("suggestions.csv"), key=lambda x: int(x["priority_rank"])):
        rows.append([
            esc(r["priority_rank"]),
            esc(r["suggestion_id"]),
            esc(r["area"]),
            esc(r["title"]),
            esc(r["problem_and_evidence"]),
            esc(r["proposal"]),
            esc(r["owner_decision_required"]),
            badge(r["impact"], "ok" if r["impact"] == "high" else "info"),
            badge(r["effort"], "warn" if r["effort"] == "high" else "info"),
            badge(r["risk"], "bad" if r["risk"] == "high" else "info"),
            esc(r["candidate_path"]),
            link(r["evidence_source_url"], "source"),
        ])
    paths = [
        ["A - Verification first (recommended)", "One canonical NFL entry point, keep the three packs as evidence archives, freeze the gates, repair the source register, keep every unconfirmed value blank.",
         "Low risk, days of work, no data or licence exposure. Fixes navigation, comparability and freshness without deleting any published work.",
         "S-01, S-02, S-05, S-07, S-08, S-09, S-13, S-14, S-17, S-18"],
        ["B - Consolidate everything", "Merge the three packs into one canonical dataset and one generator, archive two packs, adopt one gate register and one status vocabulary.",
         "Cleanest end state, but it re-writes merged, published work and loses the per-session provenance unless the archive is preserved carefully.",
         "S-01, S-02, S-05, S-06, S-07, S-08, S-09, S-10, S-12, S-17"],
        ["C - Empirical first", "Make the reproducible lab the core engine, licence or replace the community dataset, and connect a licensed price feed as soon as one exists.",
         "Fastest route to real numbers, but it carries the licence question, the community-price question and the rights question until each is answered.",
         "S-01, S-02, S-04, S-08, S-09, S-12, S-15, S-16"],
    ]
    path_rows = [[esc(p[0]), esc(p[1]), esc(p[2]), esc(p[3]),
                  link(SELF + "suggestions.html", "live page")] for p in paths]
    body = (
        "<p class=\"lede\">A reviewable register of improvements to this project. Nothing here has been "
        "implemented: every row is a proposal waiting for a decision, and the rows that say so in the "
        "<em>owner decision required</em> column are the ones waiting on you.</p>"
        + table(["#", "ID", "Area", "Title", "Problem and evidence", "Proposal", "Owner decision required",
                 "Impact", "Effort", "Risk", "Path", "Source"], rows)
        + "<h2>Candidate paths</h2>"
        "<p class=\"lede\">Three coherent ways to take the project forward. Each list shows which suggestions it "
        "covers. The recommendation is path A, because it removes the blockers that are visible today without "
        "putting the licence, price or rights questions ahead of them.</p>"
        + table(["Path", "What it means", "Trade-off", "Suggestions covered", "Source"], path_rows)
        + "<div class=\"note\"><strong>Review procedure.</strong> Read the register, choose the path, then approve "
          "or reject each numbered suggestion. The board records every decision in "
          "<a href=\"https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md\">COORDINATION.md</a> before "
          "any implementation begins, so that no suggestion is implemented by default.</div>"
    )
    return page("Suggestions for review (proposals only)", "suggestions.html", body)


def build_strategies():
    srows = []
    for r in load("strategy_status.csv"):
        srows.append([
            esc(r["strategy_id"]), esc(r["source_pack"]), esc(r["bet_family"]), esc(r["description"]),
            esc(r["state"]), esc(r["gates_passed"]), status_badge(r["qualified"], "warn"),
            esc(r["correlation_value"]) if r["correlation_value"] else '<span class="badge b-bad">not measured</span>',
            esc(r["correlation_status"]), link(r["evidence_source_url"], "source"),
        ])
    grows = []
    for r in load("gate_status.csv"):
        grows.append([
            esc(r["gate_id"]), esc(r["gate_name"]), esc(r["source_pack"]), esc(r["test_method"]),
            status_badge(r["current_state"], "warn"), esc(r["why_it_is_open"]), link(r["evidence_source_url"], "source"),
        ])
    lrows = []
    for r in load("leaderboard_status.csv"):
        lrows.append([esc(r["field"]), esc(r["value_or_rule"]), status_badge(r["status"], "warn"),
                      esc(r["note"]), link(r["evidence_source_url"], "source")])
    body = (
        "<p class=\"lede\">The strategies that exist across the four NFL sections, the gates they must pass, the "
        "correlation position, and the state of the leaderboard competition.</p>"
        + "<h2>Strategy register</h2>"
        + table(["ID", "Section", "Bet family", "Description", "State", "Gates passed", "Qualified",
                 "Correlation", "Correlation note", "Source"], srows)
        + "<h2>Validation gates</h2>"
        + table(["Gate", "Name", "Section", "Test method", "State", "Why it is open", "Source"], grows)
        + "<h2>Leaderboard competition</h2>"
        + table(["Field", "Rule or value", "Status", "Note", "Source"], lrows)
        + "<div class=\"note warn\"><strong>On luck.</strong> Statistical validation can reduce the influence of "
          "luck; it cannot remove it. NIST is explicit that a 95 % confidence interval does not mean there is a "
          "95 % probability that the interval contains the true mean, and that the confidence coefficient "
          "describes the method rather than the truth of the estimate. Every interval on this project is therefore "
          "reported with its cluster count and is empty until a verified price exists.</div>"
        + "<div class=\"note bad\"><strong>No profitability is claimed.</strong> The reproducible lab in the "
          "lines-lab section reports holdout returns for three strategies whose confidence intervals all include "
          "zero, computed on a community dataset with no declared licence. Those figures are labelled "
          "computations on non-official data and are not an official league or market result.</div>"
    )
    return page("Strategies, validation gates and leaderboard", "strategies.html", body)


def build_injuries():
    inj = load("injury_status_read_2026_11_13.csv")
    by = {}
    for r in inj:
        by.setdefault(r["team"], []).append(r)
    rows = []
    for team in sorted(by):
        for r in by[team]:
            rows.append([
                esc(r["team"]), esc(r["player"]), esc(r["position"]),
                status_badge(r["designation"], "bad" if r["designation"] == "OUT" else
                             ("warn" if r["designation"] in ("DOUBTFUL", "QUESTIONABLE") else "info")),
                esc(r["practice_note"]), esc(r["source_label"]), link(r["official_source_url"], "source"),
            ])
    drows = []
    for r in load("depth_status.csv"):
        drows.append([
            esc(r["club"]), esc(r["abbr"]), esc(r["official_injury_report_week10"]),
            link(r["club_depth_chart_source_in_repository"], "depth chart") if r["club_depth_chart_source_in_repository"]
            else '<span class="badge b-bad">none captured</span>',
            status_badge(r["depth_order_known"], "warn" if r["depth_order_known"] == "partial" else "bad"),
            status_badge(r["starter_replacement_chain_published"], "ok" if r["starter_replacement_chain_published"] == "yes" else "info"),
            '<span class="badge b-bad">blank - not computable</span>',
            esc(r["why_the_value_is_blank"]), link(r["official_source_url"], "source"),
        ])
    report = load("injury_report_week10_read_2026_11_13.csv")
    report_rows = []
    for r in report:
        if r["game_status"]:
            kind = "bad" if r["game_status"].lower() == "out" else "warn"
        elif "Did Not Participate" in r["practice_status"]:
            kind = "warn"
        else:
            kind = "info"
        report_rows.append([
            esc(r["team"]), esc(r["player"]), esc(r["position"]),
            esc(r["injury"]) if r["injury"] else '<span class="badge b-info">no injury listed</span>',
            esc(r["practice_status"]), esc(r["game_status"]) if r["game_status"]
            else '<span class="badge b-info">no designation</span>',
            link(r["official_source_url"], "source"),
        ])
    body = (
        "<p class=\"lede\">The official Week 10 availability read taken on 2026-11-13, and the state of the "
        "starter-versus-backup depth tracking for all 32 clubs. The league publishes who is limited, doubtful or "
        "out; it does not publish the depth order behind a starter, which is why the deficiency column is blank "
        "for every club.</p>"
        + "<h2>Official Week 10 availability (read 2026-11-13)</h2>"
        + table(["Club", "Player", "Position", "Official designation", "Detail", "Source label", "Source"], rows)
        + "<h2>Official Week 10 league injury report, every listed player</h2>"
        + "<p>The table below is the full per-club listing from the official Week 10 league injury report read on "
          "2026-11-13: " + str(len(report_rows)) + " player rows covering all 28 clubs that play in Week 10. A blank "
          "game-status cell means the league published no designation for that player at the time of the read; it "
          "does not mean the player is healthy.</p>"
        + table(["Club", "Player", "Position", "Injury", "Practice status", "Game designation", "Source"], report_rows)
        + "<h2>Depth-deficiency coverage by club</h2>"
        + table(["Club", "Abbr", "Official injury report", "Club depth chart", "Depth order known",
                 "Replacement chain published", "Deficiency index", "Why the value is blank", "Source"], drows)
        + "<div class=\"note\"><strong>What this proves and what it does not.</strong> The league's own report "
          "establishes player availability. A depth deficiency - how much a unit loses when a second or third "
          "string player starts - needs the club's depth order and the replacement's expected snap share. The "
          "first exists for 8 clubs in this repository and the second exists nowhere as an official source, so "
          "every deficiency index stays blank. Suggestion S-10 closes the first half of that gap.</div>"
        + "<div class=\"note warn\"><strong>League policy matters here.</strong> NFL.com reported that the three "
          "official betting partners agreed to prohibit wagers the league finds objectionable, including bets "
          "tied to injuries. A product whose value comes from knowing a starter is out is exposed to that policy "
          "as well as to the general terms of use.</div>"
    )
    return page("Injuries, availability and depth deficiency", "injuries.html", body)


def build_verification():
    rows = []
    for r in load("value_reconciliation.csv"):
        rows.append([
            esc(r["check_id"]), esc(r["published_row_id"]), esc(r["published_file"]),
            esc(r["field"]), esc(r["published_value"]),
            esc(r["official_value_read_2026_11_13"]) if r["official_value_read_2026_11_13"] else
            '<span class="badge b-bad">not read</span>',
            status_badge(r["result"]), esc(r["note"]), link(r["official_source_url"], "source"),
        ])
    p68 = []
    for r in load("pr68_verification.csv"):
        p68.append([
            esc(r["check_id"]), esc(r["subject"]), esc(r["expected_value"]), esc(r["observed_value"]),
            status_badge(r["result"], "ok" if r["result"] == "pass" else "warn"), esc(r["method"]),
            link(r["official_or_primary_source_url"], "source"),
        ])
    body = (
        "<p class=\"lede\">One row per published value compared with the official reading taken on 2026-11-13. "
        "Nothing was corrected in place: a difference is recorded as a difference and flagged, because the league "
        "republishes the injury report continuously and a dated snapshot can differ from a later read without "
        "either being wrong.</p>"
        + table(["Check", "Published row", "Published file", "Field", "Published value", "Official value read 2026-11-13",
                 "Result", "Note", "Source"], rows)
        + "<h2>Independent verification of the lines-lab dataset (open pull request #68)</h2>"
        + table(["Check", "Subject", "Expected", "Observed", "Result", "Method", "Source"], p68)
        + "<div class=\"note good\"><strong>Reproduced exactly.</strong> The trimmed 2015-2026 dataset committed "
          "on the open lines-lab pull request was reconstructed byte-for-byte from the upstream repository at the "
          "recorded commit: filter to regular-season games from 2015, write the 24 recorded columns in the recorded "
          "order, CRLF line endings. The sha256 of the reconstruction equals the recorded digest "
          "<code>9fe5bd67...5ce83090</code>. The upstream repository declares no licence, which is recorded as an "
          "open flag rather than as a resolved fact.</div>"
    )
    return page("Line-by-line verification ledger", "verification.html", body)


def build_flagged():
    rows = []
    for r in load("irregularities.csv"):
        rows.append([
            esc(r["flag_id"]), esc(r["area"]),
            badge(r["severity"], "bad" if r["severity"] == "high" else ("warn" if r["severity"] == "medium" else "info")),
            esc(r["finding"]), esc(r["evidence"]), esc(r["why_it_matters"]), esc(r["requested_action"]),
            status_badge(r["status"], "warn"), link(r["official_or_primary_source_url"], "source"),
        ])
    unverified = [
        ["Historical moneyline, spread and total prices used by the lines-lab backtests", "blank", "https://github.com/sassnarep3-star/Own6/pull/68", "NFLR-F10"],
        ["Correlation coefficients between NFL bet families", "blank", "https://github.com/sassnarep3-star/Own6/blob/main/data/nfl/correlations.csv", "NFLR-F16"],
        ["Depth-deficiency index for all 32 clubs", "blank", "https://sassnarep3-star.github.io/Own6/docs/nfl-review/injuries.html", "NFLR-F18"],
        ["Measured EPA drop-off when a 2nd, 3rd or 4th string player starts", "blank", "https://www.nfl.com/injuries/", "NFLR-F18"],
        ["Verified snap share of every replacement player", "blank", "https://www.nfl.com/injuries/", "NFLR-F18"],
        ["Any live or closing market price", "blank", "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners", "NFLR-F16"],
        ["Out-of-sample return of any qualified strategy", "blank", "https://sassnarep3-star.github.io/Own6/docs/nfl-review/strategies.html", "NFLR-F16"],
        ["Player-prop market catalogue and settlement rules", "blank", "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook", "NFLR-F13"],
        ["Two standings columns whose meaning the official legend does not define", "blank", "https://www.nfl.com/standings/", "NFLR-F11"],
    ]
    urows = [[esc(u[0]), '<span class="badge b-bad">blank</span>', link(u[2], "source"), esc(u[3])] for u in unverified]
    body = (
        "<p class=\"lede\">Everything that is flagged for review: the irregularities found in the repository and "
        "the values that could not be confirmed from an official source. Flagged items do not block the site; they "
        "are published so that they can be reviewed and a change can be requested.</p>"
        + "<h2>Irregularities</h2>"
        + table(["ID", "Area", "Severity", "Finding", "Evidence", "Why it matters", "Requested action", "Status", "Source"], rows)
        + "<h2>Values left blank because no official source confirmed them</h2>"
        + table(["Value", "Published as", "Source consulted", "Related flag"], urows)
    )
    return page("Flagged for review", "flagged.html", body)


def build_sources():
    rows = []
    for r in load("official_reads.csv"):
        rows.append([
            esc(r["read_id"]), esc(r["publisher"]), esc(r["title"]),
            status_badge(r["verification_status"], "ok" if r["verification_status"] == "verified_direct" else "warn"),
            esc(r["read_date_et"]), esc(r["retrieval_method"]), esc(r["verbatim_excerpt"]),
            esc(r["supports_claim"]), esc(r["does_not_support"]), link(r["url"], "open"),
        ])
    body = (
        "<p class=\"lede\">The official pages read directly during this session, with the excerpt that was read "
        "and an explicit statement of what each source does and does not support. Every other source in the "
        "repository is listed in the source registers of the individual packs.</p>"
        + table(["ID", "Publisher", "Title", "Status", "Read", "Method", "Excerpt read", "Supports", "Does not support", "Link"], rows)
        + "<div class=\"note\"><strong>Manual review.</strong> Every link on this page is an official domain: "
          "nfl.com, operations.nfl.com, itl.nist.gov, api.github.com and codeload.github.com. The methodology "
          "references used by the packs (NIST/SEMATECH for intervals, SciPy for correlation, scikit-learn for "
          "calibration, statsmodels for multiple-testing correction) are the same authorities and are linked from "
          "the source registers of the individual packs.</div>"
    )
    return page("Official sources read on 2026-11-13", "sources.html", body)


PAGES = {
    "index.html": build_index,
    "requirements.html": build_requirements,
    "questions.html": build_questions,
    "suggestions.html": build_suggestions,
    "strategies.html": build_strategies,
    "injuries.html": build_injuries,
    "verification.html": build_verification,
    "flagged.html": build_flagged,
    "sources.html": build_sources,
}


def render():
    os.makedirs(ASSETS, exist_ok=True)
    out = {}
    for name, fn in PAGES.items():
        out[os.path.join(OUT, name)] = fn()
    out[os.path.join(ASSETS, "style.css")] = CSS
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="verify the committed pages match a fresh build")
    args = ap.parse_args(argv)
    files = render()
    if args.check:
        bad = []
        for path, content in files.items():
            if not os.path.exists(path):
                bad.append(os.path.relpath(path, ROOT) + " (missing)")
            elif open(path, encoding="utf-8").read() != content:
                bad.append(os.path.relpath(path, ROOT) + " (stale)")
        if bad:
            print("FAIL: generated pages are stale or missing:\n  " + "\n  ".join(bad))
            return 1
        print(f"OK: {len(files)} generated files reproduce exactly")
        return 0
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    print(f"wrote {len(files)} files to {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
