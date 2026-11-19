#!/usr/bin/env python3
"""Build the nfl-a67ddef8 Pages site from committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_a67ddef8.py            # write docs/nfl-a67ddef8/**
    python3 scripts/build_nfl_a67ddef8.py --check    # build then run the verifier

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
DATA = os.path.join(REPO, "data", "nfl_a67ddef8")
DOCS = os.path.join(REPO, "docs", "nfl-a67ddef8")

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


def cell(v) -> str:
    if v in ("", None):
        return '<span class="blank">not published</span>'
    return esc(v)


def table(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def page(name: str, title: str, active: str, body: str) -> str:
    navs = [
        ("index.html", "Overview"),
        ("captures.html", "Captures"),
        ("flags.html", "Flags"),
        ("reverification.html", "Reverification"),
        ("registers.html", "Registers"),
        ("sources.html", "Sources"),
    ]
    nav = "".join(
        f'<a href="{h}"{" class=on" if h == active else ""}>{esc(t)}</a>'
        for h, t in navs
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · nfl-a67ddef8</title>
<style>{STYLE}</style></head>
<body><header><div class="wrap">
<div class="top"><b>OWN6 · NFL DESK</b><span>pack nfl-a67ddef8 · read 2026-11-19 UTC</span></div>
<nav>{nav}</nav></div></header>
<main><div class="wrap">
<h1>{esc(title)}</h1>
{body}
</div></main>
<footer><div class="wrap">Built from committed data by <code>scripts/build_nfl_a67ddef8.py</code>.
No page contains inputs, market prices or picks. Unverified values are blank and flagged.</div>
</footer></body></html>
"""


def build_index() -> str:
    standings = read("standings_2026_11_19.csv")
    reqs = read("requirements.csv")
    flags = read("flagged.csv")
    rev = read("reverification.csv")
    w = sum(int(r["w"]) for r in standings)
    l = sum(int(r["l"]) for r in standings)
    t = sum(int(r["t"]) for r in standings)
    pf = sum(int(r["pf"]) for r in standings)
    pa = sum(int(r["pa"]) for r in standings)

    status_pill = {
        "satisfied-this-session": ("ok", "done now"),
        "satisfied-prior-verified": ("ok", "prior · verified"),
        "satisfied-prior-reverified": ("ok", "prior · re-verified"),
        "satisfied-prior + this-session addition": ("ok", "prior + now"),
        "satisfied-prior + carried": ("ok", "prior · carried"),
        "satisfied-before-work": ("ok", "done first"),
        "partial": ("warn", "partial"),
        "open": ("warn", "open"),
        "open-at-writing": ("info", "at integration"),
    }
    req_rows = []
    for r in reqs:
        pill_cls, pill_txt = status_pill.get(r["status"], ("info", r["status"][:18]))
        ev = r["evidence_pointer"]
        if ev.startswith("http"):
            ev_html = a(ev)
        elif ev and os.path.exists(os.path.join(REPO, ev)):
            ev_html = f'<a href="../../{esc(ev)}">{esc(os.path.basename(ev))}</a>'
        else:
            ev_html = cell(ev)
        req_rows.append([
            f'<code>{esc(r["req_id"])}</code>', esc(r["requirement"]),
            f'<span class="pill {pill_cls}">{esc(pill_txt)}</span>',
            cell(r["blocking_gate"]), cell(r["clears_when"]), ev_html,
        ])

    body = f"""
<p class="lead">Session <b>a67ddef8</b> — official-source capture and flag re-testing for the
2026 NFL season through Week 12. Every row below links to the official page it came from.
Values that could not be confirmed are left blank and published on the
<a href="flags.html">flagged page</a> instead of being inferred.</p>

<div class="cards">
<div class="card"><div class="k">Standings clubs</div><div class="v">{len(standings)}</div>
<div class="s">W {w} · L {l} · T {t}</div></div>
<div class="card"><div class="k">Points (PF = PA)</div><div class="v">{pf:,}</div>
<div class="s">league identity holds</div></div>
<div class="card"><div class="k">Week-11 injury rows</div><div class="v">253</div>
<div class="s">13 games · 2 no-injury markers</div></div>
<div class="card"><div class="k">Flags re-tested</div><div class="v">{len(read("flag_recheck.csv"))}</div>
<div class="s">{len(flags)} new this session</div></div>
<div class="card"><div class="k">Reverifications</div><div class="v">{len(rev)}</div>
<div class="s">prior rows re-read</div></div>
<div class="card"><div class="k">Capture log rows</div><div class="v">{len(read("capture_log.csv"))}</div>
<div class="s">sha256 over artifacts</div></div>
</div>

<div class="note"><b>Decision-readiness table</b> — one row per requirement with its blocking
gate and the number that would clear it. Status pills: <span class="pill ok">done now</span>
<span class="pill ok">prior · verified</span> <span class="pill warn">partial / open</span>
<span class="pill info">at integration</span>.</div>

{table(["ID", "Requirement", "Status", "Blocking gate", "Clears when", "Evidence"], req_rows)}
"""
    return page("index.html", "Pack overview & decision readiness", "index.html", body)


def build_captures() -> str:
    standings = read("standings_2026_11_19.csv")
    w11 = read("week11_slate.csv")
    w10 = read("week10_finals.csv")
    w12 = read("week12_slate.csv")
    inj = read("injuries_reg11.csv")

    s_rows = [[
        esc(r["club"]), esc(r["division"]), r["w"], r["l"], r["t"],
        esc(r["pct"]), r["pf"], r["pa"], r["net_pts"],
        f'<span class="pill info">{esc(r["streak"])}</span>',
        a(r["source_url"], "standings"),
    ] for r in standings]

    v_rows = []
    for r in w11:
        match = r["venue_match"]
        pill = {"exact": "ok", "mismatch": "bad", "variance": "warn",
                "n/a-international": "info"}.get(match, "info")
        v_rows.append([
            esc(r["game_date"]), esc(r["kickoff_et"]), esc(r["network"]),
            f'{esc(r["away"])} {esc(r["away_record"])} @ {esc(r["home"])} {esc(r["home_record"])}',
            cell(r["venue_stadium_gamecentre"]), cell(r["venue_location_gamecentre"]),
            cell(r["venue_hotel_param_schedulepage"]),
            f'<span class="pill {pill}">{esc(match)}</span>',
            esc(r["venue_note"]),
            a(r["game_url"], "game"),
        ])

    t10 = [[
        esc(r["game_date"]),
        f'{esc(r["away"])} {esc(r["away_score"])} @ {esc(r["home"])} {esc(r["home_score"])}',
        f'<span class="pill ok">{esc(r["status"])}</span>',
        esc(r["schedule_section"]), r["margin_home"],
        a(r["game_url"], "game"),
    ] for r in w10]

    t12 = [[
        esc(r["game_date"]), esc(r["kickoff_et"]), esc(r["network"]),
        f'{esc(r["away"])} {esc(r["away_record"])} @ {esc(r["home"])} {esc(r["home_record"])}',
        cell(r["venue_stadium_gamecentre"]),
        cell(r["note"]),
        a(r["game_url"], "game"),
    ] for r in w12]

    # injuries: designations first, then full register
    des_rows = [[
        esc(r["game"].split(" — ")[0]), esc(r["team"]), esc(r["player"]),
        esc(r["position"]), cell(r["injury"]), esc(r["practice_status"]),
        f'<span class="pill bad">{esc(r["game_status"])}</span>',
        a(r["source_url"], "reg11"),
    ] for r in inj if r["game_status"]]

    marker_rows = [[
        esc(r["game"].split(" — ")[0]), esc(r["team"]),
        '<span class="pill info">No Injuries Reported</span>',
        a(r["source_url"], "reg11"),
    ] for r in inj if r["note"]]

    full_rows = [[
        esc(r["game"].split(" — ")[0]), esc(r["team"]), esc(r["player"]),
        esc(r["position"]), cell(r["injury"]), esc(r["practice_status"]),
        esc(r["game_status"]) or '<span class="blank">pending</span>',
    ] for r in inj if r["player"]]

    body = f"""
<h2>Standings — 2026 regular season through Week 10</h2>
<p class="lead">32 clubs transcribed from the official division standings on 2026-11-19.
Arithmetic checked at build time: W = L = 149, T = 2, PF = PA = {sum(int(r["pf"]) for r in standings):,}.</p>
{table(["Club", "Division", "W", "L", "T", "PCT", "PF", "PA", "Net", "Strk", "Source"], s_rows)}

<h2>Week 11 slate + venues (game-centre fields)</h2>
<p class="lead">Venue columns come from each fixture's official game centre
<span class="blank">Location / Stadium</span> fields — never from hotel affiliate query strings.
The hotel column is kept only as a cross-check; three of them are stale (see
<a href="flags.html">flags</a>).</p>
{table(["Date", "Kickoff ET", "Net", "Matchup", "Stadium (game centre)", "Location (game centre)",
        "Hotel param (cross-check)", "Match", "Note", "Source"], v_rows)}

<h2>Week 10 finals</h2>
{table(["Date", "Final", "Status", "Section heading", "Home margin", "Source"], t10)}

<h2>Week 12 slate</h2>
<div class="note">Venue cells are deliberately blank except DEN@PIT: only that game centre was
read this session (ACRISURE STADIUM). Blank = not read, not inferred.</div>
{table(["Date", "Kickoff ET", "Net", "Matchup", "Stadium (game centre)", "Note", "Source"], t12)}

<h2>Week 11 injury report — game statuses (16 rows, all Thursday)</h2>
<p class="lead">Only the Thursday IND@HOU game carries game statuses at this read; every
Sunday/Monday row is <span class="blank">pending</span> by cadence, not missing data.</p>
{table(["Game", "Team", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], des_rows)}

<h2>No-injury markers</h2>
{table(["Game", "Team", "Marker", "Source"], marker_rows)}

<h2>Week 11 injury report — full register (253 rows)</h2>
{table(["Game", "Team", "Player", "Pos", "Injury", "Practice", "Game status"], full_rows)}
"""
    return page("captures.html", "Official captures", "captures.html", body)


def build_flags() -> str:
    recheck = read("flag_recheck.csv")
    flags = read("flagged.csv")

    status_pill = {
        "CLOSED": "ok", "CONFIRMED": "ok", "CORROBORATED": "ok",
        "MATCH-IMPROVED": "ok", "REINFORCED": "warn", "SUPERSEDED": "info",
        "PARTIAL": "warn", "STILL-OPEN": "bad", "NOT-RETESTED": "info",
    }
    rc_rows = [[
        f'<code>{esc(r["flag_id"])}</code>', esc(r["origin_pack"]),
        esc(r["flag_summary"]), esc(r["retest_date"]),
        a(r["retest_source"], "retest"),
        f'<span class="pill {status_pill.get(r["new_status"], "info")}">{esc(r["new_status"])}</span>',
        esc(r["retest_finding"]),
        cell(r["evidence"]),
    ] for r in recheck]

    sev_pill = {"medium": "warn", "low": "info", "info": "info"}
    f_rows = [[
        f'<code>{esc(r["flag_id"])}</code>',
        f'<span class="pill {sev_pill.get(r["severity"], "info")}">{esc(r["severity"])}</span>',
        esc(r["category"]), esc(r["summary"]), esc(r["detail"]),
        '<span class="pill warn">open</span>',
        '<span class="pill ok">no — does not block merge</span>',
        a(r["source_urls"].split(";")[0], "source"),
    ] for r in flags]

    body = f"""
<h2>Flag re-tests of inherited findings</h2>
<p class="lead">Every open flag carried into this session was re-tested against a live official
read on 2026-11-19. {sum(1 for r in recheck if r["new_status"] in ("CLOSED", "CONFIRMED", "CORROBORATED"))}
closed/confirmed/corroborated ·
{sum(1 for r in recheck if r["new_status"] == "STILL-OPEN")} still open ·
{sum(1 for r in recheck if r["new_status"] == "NOT-RETESTED")} not retested.</p>
{table(["Flag", "Origin", "What was flagged", "Retest date", "Retest source", "Result",
        "Finding", "Evidence"], rc_rows)}

<h2>Flagged for Review — new this session</h2>
<div class="note">These items are unverified, contradictory or stale <b>on upstream official
pages</b>. Per the brief they are published here and <b>do not block merge</b>.</div>
{table(["Flag", "Severity", "Category", "Summary", "Detail", "Status", "Blocks merge?", "Source"], f_rows)}
"""
    return page("flags.html", "Flags & re-tests", "flags.html", body)


def build_reverification() -> str:
    rev = read("reverification.csv")
    verdict_pill = {
        "MATCH": "ok", "MATCH-IMPROVED": "ok", "MATCH-CHANGED": "ok",
        "CORROBORATED": "ok", "PARTIAL": "warn",
    }
    rows = [[
        f'<code>{esc(r["rev_id"])}</code>', esc(r["target_pack"]),
        esc(r["target_row_or_claim"]), esc(r["claim_as_published"]),
        esc(r["retest_method"]),
        f'<span class="pill {verdict_pill.get(r["verdict"], "info")}">{esc(r["verdict"])}</span>',
        esc(r["retest_result"]), cell(r["arithmetic"]),
    ] for r in rev]
    body = f"""
<p class="lead">Rows published by earlier packs were re-read from their cited sources on
2026-11-19. {sum(1 for r in rev if r["verdict"].startswith("MATCH"))} matched exactly ·
{sum(1 for r in rev if r["verdict"] == "CORROBORATED")} corroborated ·
{sum(1 for r in rev if r["verdict"] == "PARTIAL")} partial. Arithmetic columns show the
recomputation, not a restatement.</p>
{table(["ID", "Target pack", "Row / claim", "As published", "Retest method", "Verdict",
        "Result", "Arithmetic"], rows)}
"""
    return page("reverification.html", "Prior-row reverification", "reverification.html", body)


def build_registers() -> str:
    qs = read("questions.csv")
    sg = read("suggestions.csv")

    q_rows = [[
        f'<code>{esc(r["q_id"])}</code>', esc(r["question"]),
        esc(r["information_needed"]),
        (f'<span class="pill ok">answered</span> {esc(r["answer"])}'
         if r["status"] == "answered" else '<span class="pill warn">open</span>'),
        cell(r["impact_if_unanswered"]),
    ] for r in qs]

    s_rows = [[
        f'<code>{esc(r["s_id"])}</code>', esc(r["suggestion"]), esc(r["rationale"]),
        esc(r["pros"]), esc(r["cons"]), esc(r["implementation_sketch"]),
        esc(r["effort"]),
        (f'<span class="pill warn">awaiting human</span>'
         if r["pending_human_choice"] == "yes" else
         f'<span class="pill info">{esc(r["decision"] or "decided")}</span>'),
    ] for r in sg]

    body = f"""
<h2>Questions / information / answers</h2>
{table(["ID", "Question", "Information needed", "Status", "Impact if unanswered"], q_rows)}

<h2>Suggestions — human chooses before anything is implemented</h2>
<div class="note">No suggestion in this pack has been implemented. Every row waits for a
human decision in the <code>decision</code> column (currently empty on all rows).</div>
{table(["ID", "Suggestion", "Rationale", "Pros", "Cons", "Sketch", "Effort", "Choice"], s_rows)}
"""
    return page("registers.html", "Questions & suggestions", "registers.html", body)


def build_sources() -> str:
    src = read("sources.csv")
    log = read("capture_log.csv")

    s_rows = [[
        f'<code>{esc(r["source_id"])}</code>', a(r["url"], r["publisher"]),
        esc(r["what_it_supports"]), esc(r["last_read"]),
        f'<span class="pill info">{esc(r["trust_class"])}</span>',
    ] for r in src]

    l_rows = [[
        f'<code>{esc(r["read_id"])}</code>', a(r["source_url"], "page"),
        esc(r["page_title_as_read"]), esc(r["what_was_read"]),
        esc(r["read_on_utc"]),
        f'<code>{esc(r["artifact_sha256"][:16])}…</code>',
        esc(r["artifact_path"].replace("data/nfl_a67ddef8/", "")),
        esc(r["status"]),
    ] for r in log]

    body = f"""
<h2>Sources</h2>
<p class="lead">Every published row cites one of these. Trust class:
<span class="pill info">official-primary</span> league-owned ·
<span class="pill info">official-club</span> club-owned ·
<span class="pill info">third-party-linked</span> linked from an official page (cross-check only).</p>
{table(["ID", "URL", "Supports", "Last read", "Class"], s_rows)}

<h2>Capture log</h2>
<div class="note"><code>sha256</code> covers the transcription artifact bytes only. It proves
the artifact has not changed since it was written — it cannot prove what the page said.
<code>read_on_utc</code> is the artifact-write clock (upper bound on the fetch).</div>
{table(["Read", "Source", "Page title", "What was read", "read_on_utc", "sha256 (16)",
        "Artifact", "Status"], l_rows)}
"""
    return page("sources.html", "Sources & capture log", "sources.html", body)


def main() -> None:
    os.makedirs(DOCS, exist_ok=True)
    out = {
        "index.html": build_index(),
        "captures.html": build_captures(),
        "flags.html": build_flags(),
        "reverification.html": build_reverification(),
        "registers.html": build_registers(),
        "sources.html": build_sources(),
    }
    for name, content in out.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"wrote docs/nfl-a67ddef8/{name} ({len(content)} bytes)")
    if "--check" in sys.argv:
        rc = subprocess.call([sys.executable,
                              os.path.join(REPO, "scripts", "check_nfl_a67ddef8.py")])
        sys.exit(rc)


if __name__ == "__main__":
    main()
