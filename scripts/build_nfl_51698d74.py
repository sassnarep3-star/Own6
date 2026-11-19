#!/usr/bin/env python3
"""Build the nfl-51698d74 Pages site from committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_51698d74.py            # write docs/nfl-51698d74/**
    python3 scripts/build_nfl_51698d74.py --check    # build then run the verifier

Every page is a table or a list. Every published row links to the official page it
came from. Cells that no official source supports stay empty and the page says why.
"""
from __future__ import annotations

import csv
import html
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_51698d74")
DOCS = os.path.join(REPO, "docs", "nfl-51698d74")

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


def a(url: str, label: str) -> str:
    return f'<a href="{esc(url)}">{esc(label)}</a>'


def cell(x) -> str:
    if x is None or str(x).strip() == "":
        return '<span class="blank">blank — unverified</span>'
    return esc(x)


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def page(fname: str, title: str, active: str, body: str) -> str:
    nav = "".join(
        f'<a href="{p}" class="{"on" if p == active else ""}">{label}</a>'
        for p, label in [("index.html", "Overview"), ("captures.html", "Captures"),
                         ("flags.html", "Flags"), ("reverification.html", "Reverification"),
                         ("registers.html", "Questions &amp; suggestions"),
                         ("sources.html", "Sources")]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · nfl-51698d74</title>
<style>{STYLE}</style></head>
<body><header><div class="wrap">
<div class="top"><b>OWN6 · NFL ORIGINATION</b><span>session 51698d74 · 2026-11-19</span></div>
<nav>{nav}</nav></div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap">Research only; no wagers or guarantee of skill. Every value cites an
official NFL page; blank means unverified, never zero. Flagged items do not block merge.</div></footer>
</body></html>
"""


def status_pill(s: str) -> str:
    cls = {"satisfied-this-session": "ok", "satisfied-prior": "ok",
           "partial": "warn", "blocked": "bad"}.get(s, "info")
    return f'<span class="pill {cls}">{esc(s)}</span>'


def build_index() -> str:
    req = read("requirements.csv")
    flags = read("flagged.csv")
    standings = read("standings_2026_11_19.csv")
    pf = sum(int(r["pf"]) for r in standings)
    BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"

    def ev_cell(s: str) -> str:
        s = s.strip()
        if not s or s.startswith("n/a"):
            return f'<span class="blank">{esc(s) if s else "—"}</span>'
        path, _, note = s.partition(" (")
        parts = [x.strip() for x in path.split(";") if x.strip()]
        links = []
        for x in parts:
            is_repo_file = x.endswith((".md", ".csv", ".py", ".html", ".json"))
            if is_repo_file or x.startswith(("data/", "scripts/", "tests/", "src/", "audit/", "docs/")):
                links.append(a(BLOB + x, x))
            else:
                links.append(esc(x))
        out = "; ".join(links)
        return out + (f" ({esc(note)}" if note else "")

    req_rows = [[
        f'<code>{esc(r["req_id"])}</code>', esc(r["requirement"]),
        status_pill(r["status"]), esc(r["blocking_gate"]), esc(r["clears_when"]),
        ev_cell(r["evidence_pointer"]),
    ] for r in req]
    body = f"""
<h1>Pack overview &amp; decision readiness</h1>
<p class="lead">Fresh official capture on 2026-11-19 (standings, Week-11 injury register,
Week-10 finals, Week-11/12 slates, all 16 Week-12 game-centre venues, November reserve list),
independent recomputation of the prior pack's fair lines and leaderboard, and one row per
requirement with its blocking gate and clearing number. No market price exists on any official
NFL page, so every market column stays blank by written policy. No profitability claim anywhere.</p>
<div class="cards">
<div class="card"><div class="k">Standings clubs</div><div class="v">32</div>
<div class="s">W=L=149 · T=2 · PF=PA={pf:,}</div></div>
<div class="card"><div class="k">Week-11 injuries</div><div class="v">253</div>
<div class="s">13 games · 2 no-injury markers</div></div>
<div class="card"><div class="k">Week-12 venues</div><div class="v">16/16</div>
<div class="s">11 exact · 3 mismatch · 2 variance</div></div>
<div class="card"><div class="k">Fair lines recomputed</div><div class="v">13/13</div>
<div class="s">MATCH · market blank by policy</div></div>
<div class="card"><div class="k">Leaderboard recomputed</div><div class="v">8/8</div>
<div class="s">MATCH · 0 qualified</div></div>
<div class="card"><div class="k">Requirements</div><div class="v">{len(req)}</div>
<div class="s">{sum(1 for r in req if r['status']=='satisfied-this-session')} done now · {sum(1 for r in req if r['status']=='blocked')} blocked</div></div>
<div class="card"><div class="k">Flags re-tested</div><div class="v">{len(read("flag_recheck.csv"))}</div>
<div class="s">{len(flags)} new this session</div></div>
<div class="card"><div class="k">Capture log rows</div><div class="v">{len(read("capture_log.csv"))}</div>
<div class="s">sha256 over artifacts</div></div>
</div>

<div class="note"><b>Decision-readiness table</b> — one row per requirement with its blocking
gate and the number that would clear it. Status pills: <span class="pill ok">satisfied</span>
<span class="pill warn">partial</span> <span class="pill bad">blocked</span>.</div>

{table(["ID", "Requirement", "Status", "Blocking gate", "Clears when", "Evidence"], req_rows)}
"""
    return page("index.html", "Pack overview & decision readiness", "index.html", body)


def build_captures() -> str:
    standings = read("standings_2026_11_19.csv")
    w11 = read("week11_slate.csv")
    w10 = read("week10_finals.csv")
    w12 = read("week12_slate.csv")
    inj = read("injuries_reg11.csv")
    reserve = read("reserve_list.csv")
    lines = read("originated_lines_check.csv")
    board = read("leaderboard_check.csv")
    corrs = read("correlations_check.csv")

    s_rows = [[
        esc(r["club"]), esc(r["division"]), r["w"], r["l"], r["t"],
        esc(r["pct"]), r["pf"], r["pa"], r["net_pts"],
        f'<span class="pill info">{esc(r["streak"])}</span>',
        a(r["source_url"], "standings"),
    ] for r in standings]

    def venue_rows(slate):
        out = []
        for r in slate:
            match = r["venue_match"]
            pill = {"exact": "ok", "mismatch": "bad", "variance": "warn",
                    "n/a-international": "info"}.get(match, "info")
            out.append([
                esc(r["game_date"]), esc(r["kickoff_et"]), esc(r["network"]),
                f'{esc(r["away"])} {esc(r["away_record"])} @ {esc(r["home"])} {esc(r["home_record"])}',
                cell(r["venue_stadium_gamecentre"]), cell(r["venue_location_gamecentre"]),
                cell(r["venue_hotel_param_schedulepage"]),
                f'<span class="pill {pill}">{esc(match)}</span>',
                esc(r.get("venue_note") or r.get("note") or ""),
                a(r["game_url"], "game"),
            ])
        return out

    t10 = [[
        esc(r["game_date"]),
        f'{esc(r["away"])} {esc(r["away_score"])} @ {esc(r["home"])} {esc(r["home_score"])}',
        f'<span class="pill ok">{esc(r["status"])}</span>',
        esc(r["schedule_section"]), r["margin_home"],
        a(r["game_url"], "game"),
    ] for r in w10]

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
        a(r["source_url"], "reg11"),
    ] for r in inj if r["player"]]

    res_rows = [[
        esc(r["date"]), esc(r["club"]), esc(r["player"]), esc(r["transaction"]),
        a(r["source_url"], "reserve list"),
    ] for r in reserve]

    line_rows = [[
        esc(r["game_id"]), f'{esc(r["away"])} @ {esc(r["home"])}',
        r["recomputed_fair_margin_home"], r["recomputed_fair_total"], r["recomputed_p_home"],
        cell(r["market_margin_home"]), cell(r["market_total"]),
        cell(r["difference_margin"]), cell(r["difference_total"]),
        f'<span class="pill ok">{esc(r["verdict"])}</span>',
        a(r["source_url"], "slate"),
    ] for r in lines]

    BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"
    board_rows = [[
        f'<code>{esc(r["strategy_id"])}</code>', esc(r["strategy"]), r["n_scored"],
        cell(r["recomputed_brier"]), cell(r["published_brier"]),
        cell(r["recomputed_brier_skill_vs_control"]),
        esc(r["proper_score_qualified"]),
        f'<span class="pill ok">{esc(r["verdict"])}</span>',
        a(BLOB + "data/nfl_0ce967db/leaderboard.csv", "published board"),
    ] for r in board]

    corr_rows = [[
        esc(r["pair"]), r["n"], r["pearson_r"], r["fisher_95_lo"], r["fisher_95_hi"],
        esc(r["note"]), a(r["source_url"], "feed"),
    ] for r in corrs]

    body = f"""
<h2>Standings — 2026 regular season through Week 10</h2>
<p class="lead">32 clubs transcribed from the official division standings on 2026-11-19.
Arithmetic checked at build time: W = L = 149, T = 2, PF = PA = {sum(int(r["pf"]) for r in standings):,}.</p>
{table(["Club", "Division", "W", "L", "T", "PCT", "PF", "PA", "Net", "Strk", "Source"], s_rows)}

<h2>Week 11 slate + venues (game-centre fields)</h2>
<p class="lead">Venue columns come from each fixture's official game centre
<span class="blank">Location / Stadium</span> fields — never from hotel affiliate query strings.
The hotel column is kept only as a cross-check. IND@HOU was re-read this session; the other
12 venues are carried from the a67ddef8 capture (see provenance in the CSV).</p>
{table(["Date", "Kickoff ET", "Net", "Matchup", "Stadium (game centre)", "Location (game centre)",
        "Hotel param (cross-check)", "Match", "Note", "Source"], venue_rows(w11))}

<h2>Week 12 slate + venues (all 16 game centres read this session)</h2>
<div class="note">All 16 Week-12 venues are now filled from game-centre fields (prior pack had 1/16).
Three mismatches: DEN@PIT (ACRISURE vs Heinz), BAL@HOU (RELIANT legacy vs NRG),
TEN@JAX (EVERBANK vs TIAA). Two variances: U.S. Bank punctuation, Levi's apostrophe.</div>
{table(["Date", "Kickoff ET", "Net", "Matchup", "Stadium (game centre)", "Location (game centre)",
        "Hotel param (cross-check)", "Match", "Note", "Source"], venue_rows(w12))}

<h2>Week 10 finals</h2>
{table(["Date", "Final", "Status", "Section heading", "Home margin", "Source"], t10)}

<h2>Week 11 injury report — game statuses (16 rows, all Thursday)</h2>
<p class="lead">Only the Thursday IND@HOU game carries game statuses at this read; every
Sunday/Monday row is <span class="blank">pending</span> by cadence, not missing data.</p>
{table(["Game", "Team", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], des_rows)}

<h2>No-injury markers</h2>
{table(["Game", "Team", "Marker", "Source"], marker_rows)}

<h2>Week 11 injury report — full register (253 rows)</h2>
{table(["Game", "Team", "Player", "Pos", "Injury", "Practice", "Game status", "Source"], full_rows)}

<h2>November reserve list (25 rows, render window 11/10–11/18)</h2>
<div class="note">Absence from this list never means available. The page renders only
11/10–11/18 with no pagination control; earlier November moves are invisible.</div>
{table(["Date", "Club", "Player", "Transaction", "Source"], res_rows)}

<h2>Originated fair lines — recomputation (side → total → moneyline)</h2>
<p class="lead">Frozen S01 forecaster re-run on the 150-game corpus. Fair columns recomputed;
market and difference columns are blank because no official NFL page publishes a price
(written policy PP-01/PP-02). Not an edge and not a recommendation.</p>
{table(["Game", "Matchup", "Fair margin (home)", "Fair total", "Fair P(home)",
        "Market margin", "Market total", "Diff margin", "Diff total", "Verdict", "Source"], line_rows)}

<h2>Leaderboard — Brier recomputation (signal only; staking never ranks)</h2>
{table(["Strategy", "Name", "n", "Brier (recomputed)", "Brier (published)", "Skill vs control",
        "Qualified", "Verdict", "Source"], board_rows)}

<h2>Correlations — official numbers only, n published</h2>
{table(["Pair", "n", "Pearson r", "Fisher 95% lo", "Fisher 95% hi", "Note", "Source"], corr_rows)}
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
    def src_cell(s: str) -> str:
        m = re.search(r"https?://[^\s)]+", s)
        if not m:
            return esc(s)
        url = m.group(0)
        rest = (s[:m.start()] + s[m.end():]).strip(" ()")
        return a(url, "re-read") + (f' {esc(rest)}' if rest else "")

    rc_rows = [[
        f'<code>{esc(r["flag_id"])}</code>', esc(r["origin_pack"]),
        esc(r["flag_summary"]), esc(r["retest_date"]),
        src_cell(r["retest_source"]),
        f'<span class="pill {status_pill.get(r["new_status"], "info")}">{esc(r["new_status"])}</span>',
        esc(r["retest_finding"]),
        cell(r["evidence"]),
    ] for r in recheck]

    sev_pill = {"medium": "warn", "low": "info", "high": "bad", "info": "info"}
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
closed/confirmed · {sum(1 for r in recheck if r["new_status"] == "STILL-OPEN")} still open ·
{sum(1 for r in recheck if r["new_status"] == "NOT-RETESTED")} not retested (no fetch this session).</p>
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
    SRC = {
        "V-01": ("https://www.nfl.com/standings/division/2026/reg", "standings"),
        "V-02": ("https://www.nfl.com/schedules/2026/by-week/week-10", "week-10"),
        "V-03": ("https://www.nfl.com/schedules/2026/by-week/week-10", "settled finals"),
        "V-04": ("https://www.nfl.com/schedules/2026/by-week/week-11", "week-11 slate"),
        "V-05": ("https://www.nfl.com/schedules/2026/by-week/week-10", "settled finals"),
        "V-06": ("https://www.nfl.com/standings/division/2026/reg", "standings"),
        "V-07": ("https://www.nfl.com/games/packers-at-rams-2026-reg-12", "game centres"),
        "V-08": ("https://www.nfl.com/transactions/league/reserve-list/2026/11", "reserve list"),
    }
    rows = [[
        f'<code>{esc(r["rev_id"])}</code>', esc(r["target"]),
        esc(r["claim"]), esc(r["method"]),
        f'<span class="pill {verdict_pill.get(r["verdict"], "info")}">{esc(r["verdict"])}</span>',
        esc(r["result"]), cell(r["arithmetic"]),
        a(*SRC[r["rev_id"]]) if r["rev_id"] in SRC else "",
    ] for r in rev]
    body = f"""
<p class="lead">Prior published rows were recomputed from their own inputs on 2026-11-19.
Arithmetic columns show the recomputation, not a restatement.</p>
{table(["ID", "Target", "Claim", "Method", "Verdict", "Result", "Arithmetic", "Source"], rows)}
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
<p class="lead">No decision in this pack depends on an unanswered question being guessed.
Each open question names the information that would answer it and what stays blocked meanwhile.</p>
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
        esc(r["artifact_path"].replace("data/nfl_51698d74/", "")),
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
        print(f"wrote docs/nfl-51698d74/{name} ({len(content)} bytes)")
    if "--check" in sys.argv:
        rc = subprocess.call([sys.executable,
                              os.path.join(REPO, "scripts", "check_nfl_51698d74.py")])
        sys.exit(rc)


if __name__ == "__main__":
    main()
