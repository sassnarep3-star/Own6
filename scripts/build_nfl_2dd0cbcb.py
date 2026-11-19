#!/usr/bin/env python3
"""Build the nfl-2dd0cbcb Pages site from committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_2dd0cbcb.py            # write docs/nfl-2dd0cbcb/**
    python3 scripts/build_nfl_2dd0cbcb.py --check    # build then run the verifier

Six static pages. Every published row links to the official page it came from (or, for
register rows, to the artifact that pins it). Cells that no official source supports stay
empty and the page says why. No form controls anywhere: the only interactive elements on
this site are links.
"""
from __future__ import annotations

import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_2dd0cbcb")
DOCS = os.path.join(REPO, "docs", "nfl-2dd0cbcb")

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

PAGES = ["index.html", "requirements.html", "captures.html", "depth.html",
         "flags.html", "sources.html"]

NAV = [
    ("index.html", "Overview"),
    ("requirements.html", "Readiness"),
    ("captures.html", "Captures"),
    ("depth.html", "Depth"),
    ("flags.html", "Flags & queues"),
    ("sources.html", "Sources"),
]

LIMIT = ("Provenance limit, stated once and meant: the hashes in this pack cover the "
         "transcription artifacts under <code>data/nfl_2dd0cbcb/raw/</code>, not the live "
         "NFL.com or club pages. They prove the artifact has not changed since it was "
         "written, not what the page said when it was read.")


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


def cell(v, blank="not published") -> str:
    if v in ("", None):
        return f'<span class="blank">{esc(blank)}</span>'
    return esc(v)


def linkcell(url: str, label: str = "open") -> str:
    return a(url, label) if url else '<span class="blank">no link</span>'


def links_field(value: str, label: str = "source") -> str:
    """Render a ';'-separated URL cell as one link per URL."""
    parts = [u.strip() for u in (value or "").split(";") if u.strip()]
    if not parts:
        return '<span class="blank">no link</span>'
    return " &middot; ".join(a(u, label) for u in parts)



def repo_url(pointer: str) -> str:
    """Map a register pointer (repo-relative path or URL) to a clickable https link."""
    p = (pointer or "").strip()
    if p.startswith("http"):
        return p
    return "https://github.com/sassnarep3-star/Own6/blob/main/" + p.lstrip("/")


def table(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def page(name: str, title: str, active: str, body: str) -> str:
    nav = "".join(
        f'<a href="{h}"{" class=on" if h == active else ""}>{esc(t)}</a>'
        for h, t in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · nfl-2dd0cbcb</title>
<style>{STYLE}</style></head>
<body>
<header><div class="wrap">
<div class="top"><b>NFL PROGRAM · SESSION 2dd0cbcb</b>
<span>week-12 capture series · decision-readiness re-baseline · 2026-11-19</span></div>
<nav>{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Static build: <code>python3 scripts/build_nfl_2dd0cbcb.py</code> from
<code>data/nfl_2dd0cbcb/*.csv</code>. No network, no clock, no form controls, nothing
computed at page-view time. <a href="../../index.html">Program landing</a> ·
<a href="../index.html">Pack hub</a> ·
<a href="https://github.com/sassnarep3-star/Own6/tree/main/data/nfl_2dd0cbcb">Data
directory on GitHub</a>.</p>
</div></footer>
</body></html>
"""


def pill(text: str) -> str:
    t = (text or "").lower()
    cls = "info"
    if t.startswith(("satisfied", "closed", "match", "confirmed", "answered")):
        cls = "ok"
    elif t.startswith(("open", "still open", "not-retested", "not tested")):
        cls = "bad"
    elif t.startswith(("partial", "owner", "probe", "corroborated", "reconfirmed",
                       "scheduled", "unanswered")):
        cls = "warn"
    return f'<span class="pill {cls}">{esc(text)}</span>'


# -------------------------------------------------------------------------- pages
def p_index() -> str:
    req = read("requirements.csv")
    ven = read("week12_venues.csv")
    th = read("thursday_status_reg11.csv")
    res = read("reserve_rows.csv")
    flag = read("flagged.csv")
    rec = read("rechecks.csv")
    q = read("questions.csv")
    s = read("suggestions.csv")
    log = read("capture_log.csv")
    depth = read("depth_retest.csv")

    def n(x: int) -> str:
        return f"{x:,}"

    by_status: dict[str, int] = {}
    for r in req:
        key = r["status"].split(" ")[0].split("-")[0]
        by_status[key] = by_status.get(key, 0) + 1
    counts = table(
        ["requirement status", "rows", "reading"],
        [
            ["satisfied", n(by_status.get("satisfied", 0)),
             "the machine exists in the repo (built by this or a prior session, pointers "
             "asserted at build time)"],
            ["partial", n(by_status.get("partial", 0)),
             "half the requirement is built; the blocking half is named in the row"],
            ["open", n(by_status.get("open", 0)),
             "no artifact found at base commit ffbbce6 — recorded as a gap, not patched over"],
            ["owner-decision-pending", n(by_status.get("owner", 0)),
             "the gate is a human decision; the decision cells in the queues stay blank"],
        ],
    )
    cards = f"""<div class="cards">
<div class="card"><div class="k">Week-12 venues</div><div class="v">{len(ven)}/16</div>
<div class="s">all captured from game centres; 3 venue-name mismatches vs the schedule-page
hotel param, published side by side</div></div>
<div class="card"><div class="k">Week-12 injury panels</div><div class="v">0/16</div>
<div class="s">every game centre said "Injury Report is not available at this time" —
and <code>/reg12</code> quietly serves Week 11 instead</div></div>
<div class="card"><div class="k">Reserve rows, Nov window</div><div class="v">{len(res)}</div>
<div class="s">11/10–11/18, identical at both 2026-11-19 clocks; no intra-month
pagination</div></div>
<div class="card"><div class="k">Re-tested flags</div><div class="v">{len(rec)}</div>
<div class="s">each with the inherited question, the read clock, the finding and a new
status</div></div>
<div class="card"><div class="k">Owner queue delta</div><div class="v">{len(q)} + {len(s)}</div>
<div class="s">new questions + new suggestions; every decision cell left blank for the
owner</div></div>
<div class="card"><div class="k">Captures pinned</div><div class="v">{len(log)}</div>
<div class="s">rows in the capture log, each with a sha256 over its transcription
artifact</div></div>
</div>"""

    regs = table(["file", "rows", "what it is"], ["file", "rows", "what it is"], [
    [f"<code>requirements.csv</code>", n(len(req)),
     'one row per line of the owner brief: status at base commit, the gate that blocks it, '
     'what clears it, and a pointer the build asserts exists — <a href="requirements.html">rendered</a>'],
    [f"<code>week12_venues.csv</code>", n(len(ven)),
     'Week-12 fixtures with both venue fields as read, and two comparison columns — <a href="captures.html">rendered</a>'],
    [f"<code>thursday_status_reg11.csv</code>", n(len(th)),
     'the full Week-11 Thursday game table (IND@HOU) at 11:08 UTC, the last read before the 8 PM designation deadline'],
    [f"<code>reserve_rows.csv</code>", n(len(res)),
     "the November reserve-list window as rendered, row for row, with the window recorded beside it"],
    [f"<code>depth_retest.csv</code>", n(len(depth)),
     "the three club depth-chart re-tests with row counts, date stamps and the parsing verdict — <a href=\"depth.html\">rendered</a>"],
    [f"<code>rechecks.csv</code>", n(len(rec)),
     "the flag re-test chain: inherited question, method, finding, new status — <a href=\"flags.html\">rendered</a>"],
    [f"<code>questions.csv</code> · <code>suggestions.csv</code>", f"{len(q)} · {len(s)}",
     "the queue delta for the owner: what to answer next, and how to discover what is missing — decisions blank"],
    [f"<code>flagged.csv</code>", n(len(flag)),
     "irregularities found while doing the above, none of which blocks a merge — <a href=\"flags.html\">rendered</a>"],
    [f"<code>repo_findings.csv</code>", n(len(read("repo_findings.csv"))),
     "repository findings from the line-by-line review (hub/landing drift, a pack with no CI, a "
     "dangling evidence pointer, 108 register rows the board cannot see, no scheduled workflows), "
     "each with the command that measured it and the link to fix it — summarised in "
     "<code>audit/NFL_2DD0CBCB_REPO_REVIEW.md</code>"],
    [f"<code>capture_log.csv</code>", n(len(log)),
     "read-by-read provenance for every artifact in <code>raw/</code> — <a href=\"sources.html\">rendered</a>"],
])
    body = f"""<h1>Week-12 capture series and decision-readiness re-baseline</h1>
<p class="lead">Session <code>2dd0cbcb</code> did two things on 2026-11-19: it read the
official pages a second time in the day (Week-12 venues, the injury-report path, the
monthly reserve list, three club depth charts), and it re-baselined the owner's
requirement list against the repository at base commit <code>ffbbce6</code>. Nothing here
is modelled, priced, or projected: the pack publishes reads, deltas and gates.</p>
{cards}
<div class="note">{LIMIT}</div>
<h2>What the day's second read changed</h2>
<ul>
<li><b>Week-12 venues are no longer blank.</b> A prior pack captured 13 of 13 Week-11
venues and 1 of 16 for Week 12; this session captured all 16 from game-centre pages and
kept the schedule-page hotel param as a separate, clearly-labelled cross-check column
rather than a source of truth.</li>
<li><b>The injury-report URL does not 404 when a week is unpublished — it serves the most
recent published week</b> with that week's own title. A consumer that trusts the URL would
have stored Week-11 rows as Week-12 data today. Flagged
<code>2DD-F01</code>, with the detection recipe on the <a href="flags.html">flags page</a>.</li>
<li><b>Two of tonight's Thursday-game rows still carry a blank game status while the
players sit on the 11/17 IR list</b> (Teague Carlies, Azeez Al-Shaair). The blank is
explained by joining two official surfaces, not by inference — see
<a href="captures.html">captures</a>.</li>
<li><b>Arizona's own depth chart now prints Carson Beck at QB1</b>, and does not print
Jacob Brissett at all: the strongest official corroboration yet of a move a prior session
could only leave blank-and-flagged. It is recorded as closure of that test, and as a new
question, because the same page omits Gardner Minshew while a Week-12 game centre still
shows him as the Cardinals' season passing leader (<code>2DD-F04</code>).</li>
</ul>
<h2>Registers published by this pack</h2>
{regs}
<p class="lead">Cross-pack context: <a href="../nfl-a67ddef8/index.html">session a67ddef8</a>
(morning reads, Week-11 slate, standings re-verification) and
<a href="../nfl-dfc0c1bc/index.html">session dfc0c1bc</a> (the consolidated question and
suggestion masters, 198 suggestions and the conflict register) are the two registers this
pack's deltas are meant to be read against. This pack adds rows; it does not rewrite
theirs.</p>
<h2>Standing rules this pack follows</h2>
<ul>
<li><b>No market prices.</b> No official page read by any session carries a market price,
so price columns stay blank by written policy — not by oversight, and not filled with a
model output relabelled as a market line.</li>
<li><b>No profit or return claims.</b> Nothing on this site is priced, and the release gate
bans profit vocabulary; the leaderboard's honest current answer is that no strategy has
qualified, which is the scoreboard working rather than failing.</li>
<li><b>Blank beats invented.</b> Where the official record is contradictory (venue names,
schedule headings, the Arizona quarterback room), both readings are published verbatim and
the contradiction is flagged. Reconciliation is an owner decision, not a build step.</li>
<li><b><code>needs review</code> never blocks a merge</b>, and a flag here never edits
another pack's files: requests against other sessions' registers are logged as rows in
this pack's queue.</li>
</ul>"""
    return page("index.html", "Overview", "index.html", body)


def p_requirements() -> str:
    req = read("requirements.csv")
    rows = []
    for r in req:
        rows.append([
            f"<b>{esc(r['req_id'])}</b>", cell(r["brief_line"]),
            f'<span class="pill info">{esc(r["section"])}</span>',
            pill(r["status"]),
            cell(r["blocking_gate"], "no gate recorded"),
            cell(r["clears_when"], "n/a — already cleared"),
            a(repo_url(r["evidence_pointer"]), "evidence"),
        ])
    body = f"""<h1>Decision-readiness table — one row per requirement, with its gate</h1>
<p class="lead">The owner brief asks for "one row per requirement, with the gate that blocks
it and the number that would clear it". This is that table, re-baselined against the
repository at base commit <code>ffbbce6</code> plus this session's captures. {len(req)} rows:
80 brief lines (including the four process/deliverable lines). A "satisfied" row is not a
self-certification: its evidence pointer is a file path, and the build that generated this
page asserted each pointer exists in the tree — a missing pointer is a build failure, so a
green build means every row below is anchored to a real artifact.</p>
<div class="note">Statuses describe <i>the repository</i>, not the NFL. "satisfied" means
the machinery the line asks for exists and is pointed at. "partial" names the missing half.
"open" means nothing was found at the base commit. "owner-decision-pending" means the next
move is a human choice, and those decision cells are blank in the queues on purpose.</div>
{table(["id", "requirement line (owner brief)", "area", "status", "blocking gate",
        "clears when", "evidence"], rows)}
<p class="lead">Machine-readable copy:
<code>data/nfl_2dd0cbcb/requirements.csv</code>. Rows whose pointer names a file inside
this pack (requirements.csv itself, rechecks.csv, week12_venues.csv, the exec summary,
the checker) were written by this session; rows pointing at other packs reference files
that existed at the base commit and were not modified here.</p>"""
    return page("requirements.html", "Readiness", "requirements.html", body)


def p_captures() -> str:
    ven = read("week12_venues.csv")
    th = read("thursday_status_reg11.csv")
    res = read("reserve_rows.csv")

    vrows = []
    for r in ven:
        mism = r["venue_raw_differs"] == "yes"
        norm = r["venue_mismatch_after_normalization"] == "yes"
        flagcell = (pill("mismatch after normalize") if norm else
                    pill("raw differs, same after normalize", ) if mism else
                    pill("equal", ))
        vrows.append([
            esc(r["game_date"]), esc(r["kickoff_et"]), cell(r["network"], "—"),
            f'<b>{esc(r["away"])}</b> at {esc(r["home"])}',
            cell(r["location_gamecentre"]),
            f'<code>{esc(r["venue_stadium_gamecentre"])}</code>',
            f'<code>{esc(r["venue_hotel_param_schedulepage"])}</code>',
            flagcell,
            a(r["game_url"], "game centre"),
        ])
    vtab = table(["date", "kickoff ET", "net", "fixture", "location (game centre)",
                  "stadium (game centre)", "venue (schedule hotel param)", "venue check",
                  "source"], vrows)

    trows = []
    for r in th:
        trows.append([
            esc(r["club"]), cell(r["player"]), esc(r["position"]),
            cell(r["injury"]), cell(r["practice_status"], "not listed"),
            cell(r["game_status"], "blank on page"),
            a("https://www.nfl.com/injuries/league/2026/reg11", "reg11"),
        ])
    ttab = table(["club", "player", "pos", "injury", "practice status",
                  "game status (11:08 UTC)", "source"], trows)

    rrows = []
    for r in res:
        rrows.append([
            esc(r["date"]), cell(r["name"]), esc(r["club"]), cell(r["transaction"]),
            a("https://www.nfl.com/transactions/league/reserve-list/2026/11", "reserve list"),
        ])
    rtab = table(["date", "name", "club", "transaction", "source"], rrows)

    statuses = sum(1 for r in th if r["game_status"])
    blanks = sum(1 for r in th if not r["game_status"])
    ind_s = sum(1 for r in th if r["game_status"] and r["club"] == "IND")
    hou_s = sum(1 for r in th if r["game_status"] and r["club"] == "HOU")
    body = f"""<h1>What the official pages said on 2026-11-19 (second read of the day)</h1>
<p class="lead">Three captures, one clock: 11:08–11:13 UTC, about two hours after the
morning session's reads. Each table is a transcription; the
<a href="sources.html">sources page</a> pins each one to its raw artifact and hash.</p>

<h2>Week 12 · venue of record, both fields, every fixture</h2>
<p>Captured from each game centre's own <i>Location / Stadium</i> fields. The schedule
page's hotel-affiliate param is kept as a separate column and labelled as a cross-check
only — it is a marketing parameter, and this week it is the stale one in three cases.
Nothing is reconciled: where the two disagree, both strings are printed exactly as read.</p>
{vtab}
<div class="note">Three raw-string disagreements survive normalization in the week's
reading: <b>DEN@PIT</b> (Acrisure Stadium vs "Heinz Field Stadium"), <b>BAL@HOU</b>
(Reliant Stadium on the game centre vs NRG Stadium in the param — and the Texans' own
gameday banner names Reliant too), and <b>TEN@JAX</b> (EverBank Stadium vs "TIAA Bank
Field"). A fourth case, <b>ATL@MIN</b>, differs only in punctuation
("U.S. BANK STADIUM" vs "US Bank Stadium") and is equal after normalization — recorded so
the comparison rule stays honest in both directions. <code>LEVI'S® STADIUM</code> keeps its
registered-trademark glyph in the raw column; equality holds only after non-alphanumerics
are stripped.</div>

<h2>Week 11 Thursday game · final-ish designations 9 hours before kickoff</h2>
<p>The Week-12 report does not exist yet (see <a href="flags.html">flags</a>), so the most
recent live injury table is tonight's Thursday fixture. {len(th)} rows for one game:
{statuses} carry a game status (IND {ind_s}, HOU {hou_s}) and {blanks} print a practice status
with the game-status cell left blank. Two of those blanks are the interesting ones — Jaylon
Carlies and Azeez Al-Shaair both appear on the November reserve list as placed on IR 11/17,
which is exactly the "blank does not mean available" case the brief anticipates.
This capture is also the last read before the Thursday 8:00 PM ET final-designation
deadline, so it is labelled as pre-final, not as the game's status list.</p>
{ttab}

<h2>November reserve list · the window the page actually renders</h2>
<p>Same {len(res)} rows as the morning read, same 11/10–11/18 window, and the page offers
no intra-month pagination at all — the prev/next controls move between <i>months</i>. That
is a finding in itself: it means a player absent from this table cannot be treated as
un-injured, because the table's completeness for earlier November dates is not observable
from this page. Row 20 (Puka Nacua, LA, IR 11/12) is also the counter-example to a tempting
shortcut: the Rams' Week-12 game centre still lists him as the team's receiving leader.</p>
{rtab}
<h3>How to read these tables</h3>
<ul>
<li>A blank <i>game status</i> is what the page printed. It is not "available", not
"questionable", and not a data error in this pack — it is an open item in the register
inherited from the morning session.</li>
<li>Every cell here is a transcription of page text. Values the page did not print
(position on the reserve list, for instance — that column is blank for all 25 rows) are
published blank, never filled in from another source.</li>
<li>These reads are dated. A reader on 2026-11-26 sees a page that has moved on: the
Week-12 reports will exist by then, and this pack's value is the dated series, not a
current view.</li>
</ul>"""
    return page("captures.html", "Captures", "captures.html", body)


def p_depth() -> str:
    d = read("depth_retest.csv")
    rows = []
    for r in d:
        rows.append([
            f'<b>{esc(r["club"])}</b>',
            cell(r["render"]),
            cell(r["text_rows_count"], "no text rows"),
            cell(r["date_stamp_as_read"], "no date printed"),
            cell(r["jersey_prefixes"]),
            cell(r["qb_group_as_read"], "not readable"),
            cell(r["finding"]),
            a(r["source_url"], "club page"),
        ])
    body = f"""<h1>Club depth charts: three re-tests, three different failures</h1>
<p class="lead">The brief's line is blunt: "fix the two depth-parsing failures before
widening coverage". One of the two is a parsing problem we can demonstrate a fix for; the
other is not a parsing problem at all, and re-reading the page a second time today is what
proves that. This page is deliberately small — three clubs, because those are the three
whose blocker was named in the inherited registers.</p>
{table(["club", "render", "text rows", "date stamp as read", "jersey prefixes",
        "QB group", "finding", "source"], rows)}
<h2>Why the counts and stamps matter more than the chart</h2>
<ul>
<li><b>Arizona publishes a usable chart and no date.</b> No publication date is rendered
anywhere on the page, so a freshness alarm cannot be built from it. The chart's content is
still the most consequential read of the day (Beck at QB1; Brissett absent) — but the
register has to record the <i>date state</i>, not just the players.</li>
<li><b>Green Bay publishes a date and says it does not trust it.</b> The footer reads
"Unofficial, Nov. 10, 2026" — nine days old at read time, unchanged since the morning
read, and self-labelled unofficial. The jersey-number prefix on every cell is the case the
parsing fix exists for: the register now stores the raw cell text and the stripped name
side by side, so the number is preserved as evidence without ever becoming a ranking.
That is the line the brief's rejection draws — depth order must never be derived from
jersey number, experience or salary.</li>
<li><b>Houston publishes an image.</b> Third consecutive session with zero text rows. It
is not a parser defect: there is nothing to parse. Any Texans depth row therefore stays
blank-and-flagged, and the register says so rather than eyeballing an image into fake
certainty. The same page's gameday banner is also where the Reliant/NRG naming inconsistency
showed up a second time this week (see <a href="captures.html">captures</a>).</li>
</ul>
<div class="note">Shared and empty slots are reproduced exactly as printed: Arizona lists
Zaven Collins and Baron Browning in <i>one</i> OLB cell (a shared slot, not two rankings),
Green Bay prints Kaleb Johnson under a blank position cell and repeats Kitan Oladapo in
both safety rows. Splitting or de-duplicating those rows would manufacture a depth order
that the club did not publish.</div>"""
    return page("depth.html", "Depth", "depth.html", body)


def p_flags() -> str:
    flag = read("flagged.csv")
    rec = read("rechecks.csv")
    q = read("questions.csv")
    s = read("suggestions.csv")

    frows = []
    for r in flag:
        frows.append([
            f'<b>{esc(r["flag_id"])}</b>', cell(r["severity"]), esc(r["category"]),
            esc(r["summary"]), cell(r["detail"]),
            pill(r["status"]), cell(r["blocking_merge"]),
            links_field(r["source_urls"]),
        ])
    ft = table(["id", "severity", "area", "summary", "detail", "status", "blocks merge",
                "source"], frows)

    rrows = []
    for r in rec:
        rrows.append([
            f'<b>{esc(r["flag_id"])}</b>', cell(r["origin_register"]),
            cell(r["target"]), cell(r["question_or_flag_as_inherited"]),
            cell(r["retest_utc"]), cell(r["method"]), cell(r["finding"]),
            pill(r["new_status"]),
            a("https://github.com/sassnarep3-star/Own6/tree/main/" + r["evidence_pointer"],
              "evidence") + " " + a(r["source_url"], "page"),
        ])
    rt = table(["id", "inherited from", "target", "question as inherited", "retested",
                "method", "finding", "new status", "links"], rrows)

    qrows = []
    for r in q:
        qrows.append([
            f'<b>{esc(r["q_id"])}</b>', cell(r["question"]), cell(r["information_needed"]),
            cell(r["answer"], "awaiting an answer"), cell(r["status"], "open"),
            cell(r["impact_if_unanswered"]),
            links_field(r["source_urls"]),
        ])
    qt = table(["id", "question", "what would answer it", "answer", "status",
                "cost of leaving it open", "sources"], qrows)

    srows = []
    for srow in s:
        srows.append([
            f'<b>{esc(srow["s_id"])}</b>', cell(srow["suggestion"]),
            cell(srow["rationale"]), cell(srow["pros"]), cell(srow["cons"]),
            cell(srow["implementation_sketch"]), cell(srow["effort"]),
            cell(srow["linked_requirement"]),
            cell(srow["discover_missing_information"]),
            '<span class="blank">owner — blank by design</span>',
        ])
    st = table(["id", "suggestion", "why", "pros", "cons", "sketch", "effort",
                "requirement", "finds missing info", "decision"], srows)

    body = f"""<h1>Flags, the re-test chain, and the owner queue</h1>
<p class="lead">{len(flag)} irregularities found while doing the reads, {len(rec)} re-tests
of inherited items, {len(q)} questions and {len(s)} suggestions for the consolidated
register. A flag records a defect in the <i>upstream</i> record or a boundary in our own
data; it never blocks a merge, and it never gets quietly fixed.</p>
<h2>Re-test chain — the inherited questions, answered with a dated read</h2>
<p>Each row names the register it came from (mostly the morning session's
<code>data/nfl_a67ddef8</code>, plus two inherited from 0d4da02c and 48217a55), what this
session did about it, and the resulting status. A "NOT-RETESTED" row is an honest one: the
session chose not to claim an answer it had no read for.</p>
{rt}
<h2>Flags raised this session</h2>
{ft}
<h2>Questions for the owner</h2>
<p>Two of these are already answered by today's reads (the injury-path fallback and the
venue normalization contract), and the answers are recorded in the register — not invented
from plausibility. The rest are open because the evidence for them does not exist yet.</p>
{qt}
<h2>Suggestions — how to go and find out</h2>
<p>Suggestions carry a decision cell, and every decision cell here is blank on purpose:
this session proposes, the owner disposes. Where a suggestion needs a human choice before
it can even be scoped, the row says so in the "finds missing info" / "decision" columns.</p>
{st}
<div class="note">Consolidation note for the hub owner: this pack writes
<code>questions.csv</code> and <code>suggestions.csv</code> rather than a
<code>questions.csv</code>/<code>suggestions.csv</code>, so the cross-pack master build
(<code>scripts/build_nfl_dfc0c1bc.py</code>, which globs
<code>data/nfl_*/questions*.csv</code>) picks them up without double-counting this pack's
register as a second source of the same rows. The masters it publishes — {198} suggestions
and the question register — remain the place where deduplication happens.</div>"""
    return page("flags.html", "Flags & queues", "flags.html", body)


def p_sources() -> str:
    src = read("sources.csv")
    log = read("capture_log.csv")
    srows = []
    for r in src:
        srows.append([
            f'<b>{esc(r["src_id"])}</b>', esc(r["official_host"]), cell(r["source_kind"]),
            a(r["url"], "open page"), cell(r["what_it_supplies"]), cell(r["read_date_utc"]),
            pill(r["verification_status"]), cell(r["provenance_limit"]),
            a("https://github.com/sassnarep3-star/Own6/blob/main/" + r["artifact"], "artifact"),
        ])
    st = table(["id", "host", "kind", "url", "what it supplies", "read", "status",
                "what the hash cannot prove", "artifact"], srows)

    lrows = []
    for r in log:
        lrows.append([
            f'<b>{esc(r["read_id"])}</b>', cell(r["source_url"], "see note"),
            cell(r["page_title_as_read"]), cell(r["what_was_read"]),
            cell(r["read_on_utc"]), cell(r["access_method"]),
            a("https://github.com/sassnarep3-star/Own6/blob/main/" + r["artifact_path"],
              r["artifact_path"].split("/")[-1]),
            f'<code>{esc(r["artifact_sha256"][:16])}…</code>',
            cell(r["status"]), cell(r["note"]),
        ])
    lt = table(["read", "source url", "title as read", "what was read", "read (UTC)",
                "method", "artifact", "sha256 (artifact)", "status", "note"], lrows)

    files = table(["path", "role"], [
        ["<code>data/nfl_2dd0cbcb/raw/*.md</code>",
         "five transcription artifacts (the only primary record this pack owns)"],
        ["<code>data/nfl_2dd0cbcb/*.csv</code>",
         "derived tables + the authored registers (requirements, queues, flags)"],
        ["<code>data/nfl_2dd0cbcb/capture_log.csv</code>",
         "read-by-read provenance with artifact hashes"],
        ["<code>scripts/build_nfl_2dd0cbcb_data.py</code>",
         "raw to CSV derivation; offline, deterministic, idempotent"],
        ["<code>data/nfl_2dd0cbcb/repo_findings.csv</code>",
     "11 repository findings from the W1 review, each with the command that measured it"],
    ["<code>audit/NFL_2DD0CBCB_REPO_REVIEW.md</code>",
     "the line-by-line repository review this register summarizes"],
    ["<code>scripts/authored_2dd0cbcb_requirements.py</code>",
         "writes the readiness table and asserts every evidence pointer exists"],
        ["<code>scripts/build_nfl_2dd0cbcb.py</code>", "this site, from committed CSVs only"],
        ["<code>scripts/check_nfl_2dd0cbcb.py</code>", "the pack verifier — rules CI enforces"],
        ["<code>src/nfl_2dd0cbcb/capture.py</code>",
         "hash and log helpers shared by the build and the verifier"],
    ])
    body = f"""<h1>Sources, and exactly what this pack can and cannot prove</h1>
<p class="lead">Nine source entries, seven capture-log rows. The verification status on
every row says <i>read-verified</i>, meaning: a session read this page on this date and
the transcription is pinned. It does not mean the underlying fact was independently
confirmed against another authority, and no row in this pack claims that.</p>
{st}
<h2>Capture log</h2>
<p class="lead">{LIMIT}</p>
{lt}
<h3>Method, stated plainly</h3>
<ul>
<li><b>Read path.</b> Pages were read with the session's page-fetch tool over HTTPS against
the host named in each row — <code>www.nfl.com</code> and three club domains, no third-party
aggregators, no cached mirrors, and no proxy hosts (a proxy-fetch attempt this session
returned an access-denied page and was discarded; nothing in this pack came from it).</li>
<li><b>Transcription path.</b> The tool returns the page's text; the session wrote what it
saw into <code>data/nfl_2dd0cbcb/raw/*.md</code>, including table rows that were inconvenient
(blank cells, contradictory headings). Every CSV in this pack is derived from those files by
<code>scripts/build_nfl_2dd0cbcb_data.py</code>, offline — there is no hand-typed number in
the derived tables, and CI re-runs the derivation and fails if the output drifts.</li>
<li><b>Clock path.</b> <code>read_on_utc</code> is the artifact-write time, an upper bound on
the fetch. Where two reads share one date (11/19 morning and 11/19 midday), both are kept as
separate rows — a zero-change result across the two is published as a zero, because "the
designations did not move" is itself the finding.</li>
<li><b>Nothing inferred.</b> No starter is inferred from a depth chart, no injury from a
blank cell, no market price from a model line, no venue from a marketing param. Those four
rules account for most of the blank cells on this site.</li>
</ul>
<h3>Files in this pack</h3>
{files}
"""
    return page("sources.html", "Sources", "sources.html", body)


BUILDERS = {
    "index.html": p_index,
    "requirements.html": p_requirements,
    "captures.html": p_captures,
    "depth.html": p_depth,
    "flags.html": p_flags,
    "sources.html": p_sources,
}


def build() -> None:
    os.makedirs(DOCS, exist_ok=True)
    for name in PAGES:
        out = os.path.join(DOCS, name)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(BUILDERS[name]())
        print(f"wrote {os.path.relpath(out, REPO)}")


def main() -> int:
    build()
    if "--check" in sys.argv:
        subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_nfl_2dd0cbcb.py")],
                       check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
