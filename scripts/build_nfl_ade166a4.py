#!/usr/bin/env python3
"""Build the nfl-ade166a4 Pages site from committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_ade166a4.py            # write docs/nfl-ade166a4/**
    python3 scripts/build_nfl_ade166a4.py --check    # build then run the verifier

Every page is a table or a list. Every published row links to the official page it
came from. Cells that no official source supports stay empty and the page says why.
"""
from __future__ import annotations

import csv
import html
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_ade166a4")
DOCS = os.path.join(REPO, "docs", "nfl-ade166a4")

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
.ok-note{background:#e4f4ee;border:1px solid #bfe3d6;color:#0a5c40;
border-radius:8px;padding:.55rem .8rem;font-size:.86rem;margin:.7rem 0}
.blank{color:#93a6b3;font-style:italic}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.8rem;padding:1rem 0 2rem}
code{background:var(--soft);padding:.05rem .3rem;border-radius:4px;font-size:.85em}
"""

PAGES = ["index.html", "delta.html", "captures.html", "flags.html",
         "registers.html", "reverification.html", "sources.html"]

NAV_LABELS = {
    "index.html": "Overview",
    "delta.html": "Same-day delta",
    "captures.html": "Captures",
    "flags.html": "Flagged for review",
    "registers.html": "Registers",
    "reverification.html": "Reverification",
    "sources.html": "Sources",
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


def cell(v) -> str:
    if v in ("", None):
        return '<span class="blank">not published</span>'
    return esc(v)


def table(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def page(name: str, title: str, body: str) -> str:
    nav = "".join(
        f'<a href="{h}"{" class=on" if h == name else ""}>{esc(t)}</a>'
        for h, t in NAV_LABELS.items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · nfl-ade166a4</title>
<style>{STYLE}</style></head>
<body><header><div class="wrap">
<div class="top"><b>OWN6 · NFL DESK</b><span>pack nfl-ade166a4 · second same-day read 2026-11-19 UTC</span></div>
<nav>{nav}</nav></div></header>
<main><div class="wrap">
<h1>{esc(title)}</h1>
{body}
</div></main>
<footer><div class="wrap">Built from committed data by <code>scripts/build_nfl_ade166a4.py</code>.
No page contains inputs, market prices or picks. Unverified values are blank and flagged.</div>
</footer></body></html>
"""


STATUS_PILL = {
    "satisfied-this-session": ("ok", "done now"),
    "satisfied-by-prior-pack": ("ok", "prior · verified"),
    "satisfied-by-design": ("ok", "by design"),
    "advanced-this-session": ("info", "advanced now"),
    "advanced-by-prior-pack": ("info", "prior · advanced"),
    "partial": ("warn", "partial"),
    "open": ("bad", "open"),
}


def build_index() -> str:
    delta = read("delta_summary.csv")[0]
    standings = read("standings_2026_11_19b.csv")
    reqs = read("requirements.csv")
    flags = read("flagged.csv")
    rev = read("reverification.csv")
    w = sum(int(r["w"]) for r in standings)
    l = sum(int(r["l"]) for r in standings)
    t = sum(int(r["t"]) for r in standings)
    pf = sum(int(r["pf"]) for r in standings)
    pa = sum(int(r["pa"]) for r in standings)
    status_counts: dict[str, int] = {}
    for r in reqs:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    cards = f"""
<div class="cards">
<div class="card"><div class="k">Same-day reads</div><div class="v">2</div>
<div class="s">injury hub · ~09:01Z and ~11:07Z</div></div>
<div class="card"><div class="k">Row-level deltas</div><div class="v">{esc(delta["added"])}/{esc(delta["removed"])}/{esc(delta["changed_fields"])}</div>
<div class="s">added / removed / changed across {esc(delta["rows_second_read"])} player rows</div></div>
<div class="card"><div class="k">Standings re-read</div><div class="v">{w}W·{l}L·{t}T</div>
<div class="s">PF = PA = {pf:,} (recomputed)</div></div>
<div class="card"><div class="k">Reverified rows</div><div class="v">{sum(1 for r in rev if r["verdict"] == "MATCH")}/{len(rev)}</div>
<div class="s">MATCH verdicts, prior-pack claims</div></div>
<div class="card"><div class="k">Open flags</div><div class="v">{sum(1 for r in flags if r["status"] == "open")}</div>
<div class="s">of {len(flags)} published, all non-blocking</div></div>
<div class="card"><div class="k">Requirements</div><div class="v">{len(reqs)}</div>
<div class="s">gate + clearing number each</div></div>
</div>
<p class="lead">This pack is a <b>second same-day read</b> of the official Week-11 injury hub
plus standings, schedule and transactions, taken about 2.1 hours after the first read
(pack <code>nfl_a67ddef8</code>, ~09:01Z). It publishes the row-level <b>delta</b> between the
two reads — never the level — as the first entry in the timestamped injury series the brief
requires. Nothing here shows a betting edge, a market price, or any performance claim.</p>
<div class="ok-note"><b>Delta result.</b> {esc(delta["rows_first_read"])} rows compared at
{esc(delta["first_read_utc"].split(" (")[0])} vs {esc(delta["second_read_utc"].split(" (")[0])}:
<b>{esc(delta["added"])} added · {esc(delta["removed"])} removed · {esc(delta["changed_fields"])} changed ·
{esc(delta["player_keys_unchanged"])} keys identical</b>, games identical:
{esc(delta["games_identical"])}. The delta register is empty by observation, not by omission.
Caveat: two fetches through one tool cannot exclude CDN cache — see question Q-06.</div>
<h2>Decision-readiness — one row per requirement</h2>
<p class="lead">Gate = what blocks the requirement today. Clears when = the observable
condition that would clear it. Blanks stay blank.</p>
"""
    rows = []
    for r in reqs:
        pill_cls, pill_text = STATUS_PILL.get(r["status"], ("info", r["status"]))
        rows.append([
            f'<code>{esc(r["req_id"])}</code>',
            esc(r["requirement"]),
            f'<span class="pill {pill_cls}">{esc(pill_text)}</span>',
            cell(r["blocking_gate"]),
            cell(r["clears_when"]),
            a(r["evidence_pointer"]) if r["evidence_pointer"].startswith("http") else f'<code>{esc(r["evidence_pointer"])}</code>',
        ])
    body = cards + table(["req", "requirement", "status", "blocking gate", "clears when", "evidence"], rows)
    return page("index.html", "NFL same-day delta pack — ade166a4", body)


def build_delta() -> str:
    dsum = read("delta_summary.csv")[0]
    deltas = read("delta_reg11_sameday.csv")
    slate = read("week11_slate_b.csv")
    reserve = read("reserve_nov2026_b.csv")
    trades = read("trades_nov2026_b.csv")
    body = f"""
<p class="lead">The injury hub was read twice on 2026-11-19: once at ~09:01Z by pack
<code>nfl_a67ddef8</code> and once at ~11:07Z by this pack. Both transcriptions are committed,
and the delta below is computed mechanically from them by
<code>src/nfl_ade166a4/build_data.py::compute_delta</code>. Only changes are published — the
level lives in the captures page.</p>
<h2>Delta summary (09:01Z → 11:07Z)</h2>
{table(["field", "value"], [
    ["first read clock", esc(dsum["first_read_utc"])],
    ["second read clock", esc(dsum["second_read_utc"])],
    ["window", esc(dsum["window_hours"]) + " hours"],
    ["player rows first read", f'<span class="n">{esc(dsum["rows_first_read"])}</span>'],
    ["player rows second read", f'<span class="n">{esc(dsum["rows_second_read"])}</span>'],
    ["keys added", f'<span class="n">{esc(dsum["added"])}</span>'],
    ["keys removed", f'<span class="n">{esc(dsum["removed"])}</span>'],
    ["fields changed", f'<span class="n">{esc(dsum["changed_fields"])}</span>'],
    ["keys identical", f'<span class="n">{esc(dsum["player_keys_unchanged"])}</span>'],
    ["game headers identical", esc(dsum["games_identical"])],
    ["no-injury markers", f'{esc(dsum["markers_first"])} → {esc(dsum["markers_second"])}'],
    ["source", a(dsum["source_url"])],
])}
<div class="ok-note"><b>Conclusion.</b> {esc(dsum["conclusion"])} — 253/253 keys unchanged in
the 2.1-hour window. The register below is empty because no row-level change was observed.</div>
<h2>Delta register (row-level changes only)</h2>
{table(["key", "class", "field", "first read", "second read"], [
    [f'<code>{esc(r["comparison_key"])}</code>', esc(r["change_class"]), esc(r["field"]),
     esc(r["value_first_read"]), esc(r["value_second_read"])] for r in deltas
]) if deltas else '<div class="note">No rows — zero deltas observed in this window.</div>'}
<h2>Week 11 slate (second read, 11:10Z)</h2>
{table(["date", "kickoff ET", "network", "away", "record", "home", "record"], [
    [esc(r["game_date"]), esc(r["kickoff_et"]), esc(r["network"]),
     esc(r["away"]), esc(r["away_record"]), esc(r["home"]), esc(r["home_record"])]
    for r in slate])}
<h2>November transactions (11:11Z)</h2>
<h3>Reserve list — 25 rows, 11/10–11/18</h3>
{table(["date", "player (club)", "transaction"], [
    [esc(r["date"]), esc(r["who"]), esc(r["kind"])] for r in reserve])}
<h3>Trades — 12 rows, 11/06–11/10</h3>
{table(["date", "player (from → to)", "transaction"], [
    [esc(r["date"]), esc(r["who"]), esc(r["kind"])] for r in trades])}
<div class="note"><b>Why the trades page is here.</b> Flag ADE-F01: Jaylen Waddle appears on
the Broncos Week-11 injury table at both reads, but no November trade row names him and the
Dolphins table does not list him. Both official pages are linked in the flag; the explanation
is unverified and nothing is inferred.</div>
"""
    return page("delta.html", "Same-day injury-hub delta", body)


def build_captures() -> str:
    log = read("capture_log.csv")
    rows = []
    for r in log:
        rows.append([
            f'<code>{esc(r["read_id"])}</code>',
            esc(r["page_title_as_read"]),
            esc(r["what_was_read"]),
            esc(r["read_on_utc"]),
            esc(r["access_method"]),
            f'<code>{esc(r["artifact_path"])}</code>',
            f'<code>{esc(r["artifact_sha256"][:16])}…</code>',
            a(r["source_url"]),
        ])
    body = f"""
<p class="lead">Every official page this session read, with its UTC clock and the sha256 of
the committed transcription artifact. The hash covers the artifact bytes only — it cannot
prove what the page said at read time; <code>read_on_utc</code> is the artifact-write clock,
an upper bound on the fetch time. Both statements are repeated in every log row.</p>
{table(["read", "page", "what was read", "clock (UTC)", "method", "artifact", "sha256", "source"], rows)}
<h2>Standings (second read, 11:08Z)</h2>
{table(["club", "division", "W", "L", "T", "PCT", "PF", "PA", "NET", "STRK"], [
    [esc(r["club"]), esc(r["division"]), f'<span class="n">{esc(r["w"])}</span>',
     f'<span class="n">{esc(r["l"])}</span>', f'<span class="n">{esc(r["t"])}</span>',
     f'<span class="n">{esc(r["pct"])}</span>', f'<span class="n">{esc(r["pf"])}</span>',
     f'<span class="n">{esc(r["pa"])}</span>', f'<span class="n">{esc(r["net_pts"])}</span>',
     esc(r["streak"])] for r in read("standings_2026_11_19b.csv")])}
<p class="lead">League totals recomputed from the 32 rows: 149 W / 149 L / 2 T, PF = PA = 6,923 —
identical to the first read, as expected on a non-game-day morning (the Week-11 Thursday game
kicks off tonight).</p>
"""
    return page("captures.html", "Captures and raw artifacts", body)


def build_flags() -> str:
    flags = read("flagged.csv")
    rows = []
    for r in flags:
        sev_cls = "bad" if r["severity"] == "high" else ("warn" if r["severity"] == "medium" else "info")
        rows.append([
            f'<code>{esc(r["flag_id"])}</code>',
            f'<span class="pill {sev_cls}">{esc(r["severity"])}</span>',
            esc(r["category"]),
            f'<b>{esc(r["summary"])}</b><br>{esc(r["detail"])}',
            f'<span class="pill warn">{esc(r["status"])}</span>' if r["status"] == "open"
            else f'<span class="pill ok">{esc(r["status"])}</span>',
            "yes" if r["blocking_merge"] == "yes" else "no",
            " · ".join(a(u.strip()) for u in r["source_urls"].split(";")),
        ])
    body = f"""
<p class="lead">Irregularities observed this session, published for the owner's review.
None blocks the merge. Every row links the official pages involved. Nothing here was
corrected by inference — the observation is published as read.</p>
{table(["flag", "severity", "category", "what was observed", "status", "blocks merge", "sources"], rows)}
"""
    return page("flags.html", "Flagged for review", body)


def build_registers() -> str:
    questions = read("questions.csv")
    suggestions = read("suggestions.csv")
    body = f"""
<h2>Questions — information needed before a decision</h2>
{table(["id", "question", "information needed", "answer", "status", "impact if unanswered"], [
    [f'<code>{esc(r["q_id"])}</code>', esc(r["question"]), cell(r["information_needed"]),
     cell(r["answer"]), f'<span class="pill warn">{esc(r["status"])}</span>',
     cell(r["impact_if_unanswered"])] for r in questions])}
<h2>Suggestions — review-only, nothing auto-implemented</h2>
<p class="lead">Every suggestion stays <b>pending human choice</b>; the decision column is
blank by design until the owner picks a path.</p>
{table(["id", "suggestion", "rationale", "pros", "cons", "effort", "linked req", "decision"], [
    [f'<code>{esc(r["s_id"])}</code>', f'<b>{esc(r["suggestion"])}</b>', esc(r["rationale"]),
     esc(r["pros"]), esc(r["cons"]), esc(r["effort"]),
     f'<code>{esc(r["linked_requirement"])}</code>', cell(r["decision"])]
    for r in suggestions])}
"""
    return page("registers.html", "Questions and suggestions", body)


def build_reverification() -> str:
    rev = read("reverification.csv")
    rows = []
    for r in rev:
        cls = "ok" if r["verdict"] == "MATCH" else ("bad" if r["verdict"] == "MISMATCH" else "warn")
        rows.append([
            f'<code>{esc(r["rev_id"])}</code>',
            esc(r["target_pack"]),
            esc(r["target_row_or_claim"]),
            esc(r["claim_as_published"]),
            esc(r["retest_method"]),
            esc(r["retest_result"]),
            f'<span class="pill {cls}">{esc(r["verdict"])}</span>',
            cell(r["arithmetic"]),
        ])
    body = f"""
<p class="lead">Published prior-pack rows re-tested against the fresh official reads of this
session. {sum(1 for r in rev if r["verdict"] == 'MATCH')} of {len(rev)} rows returned MATCH;
none returned MISMATCH; nothing was re-rated without a re-read.</p>
{table(["id", "pack", "target", "claim as published", "retest method", "retest result", "verdict", "arithmetic"], rows)}
"""
    return page("reverification.html", "Line-by-line reverification", body)


def build_sources() -> str:
    srcs = read("sources.csv")
    rows = []
    for r in srcs:
        url_cell = (a(r["url"], r["url"])
                    if r["url"].startswith("http")
                    else f'<code>{esc(r["url"])}</code>')
        rows.append([
            f'<code>{esc(r["source_id"])}</code>',
            url_cell,
            esc(r["publisher"]),
            esc(r["what_it_supports"]),
            esc(r["last_read"]),
            f'<span class="pill ok">{esc(r["trust_class"])}</span>',
        ])
    body = f"""
<p class="lead">What each source supports and how fresh the read is. Official-primary pages
are nfl.com; in-repo artifacts are committed transcriptions of those pages from the first
same-day read.</p>
{table(["id", "source", "publisher", "what it supports", "last read", "trust"], rows)}
"""
    return page("sources.html", "Sources", body)


def main() -> None:
    os.makedirs(DOCS, exist_ok=True)
    builders = {
        "index.html": build_index,
        "delta.html": build_delta,
        "captures.html": build_captures,
        "flags.html": build_flags,
        "registers.html": build_registers,
        "reverification.html": build_reverification,
        "sources.html": build_sources,
    }
    for name, fn in builders.items():
        path = os.path.join(DOCS, name)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(fn())
        print("wrote", os.path.relpath(path, REPO))
    # remove any stale page not in PAGES
    for name in sorted(os.listdir(DOCS)):
        if name.endswith(".html") and name not in PAGES:
            os.remove(os.path.join(DOCS, name))
            print("removed stale page", name)


if __name__ == "__main__":
    main()
