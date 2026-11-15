#!/usr/bin/env python3
"""Build the e5e38f9e NFL brief-to-evidence pack.

Inputs (all committed):
  data/nfl_e5e38f9e/*.csv          official reads (finals, injury spot-check) and registers
  data/nfl_<pack>/...              earlier packs, read only for reconciliation

Outputs (deterministic):
  data/nfl_e5e38f9e/w10_pack_reconciliation.csv
  data/nfl_e5e38f9e/injury_pack_comparison.csv
  docs/nfl-e5e38f9e/*.html

Run:  python3 scripts/build_nfl_e5e38f9e.py          (writes)
      python3 scripts/build_nfl_e5e38f9e.py --check  (exit 1 on drift; used by check_nfl_e5e38f9e.py)
"""
from __future__ import annotations

import csv
import html
import io
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(ROOT, "data", "nfl_e5e38f9e")
DOCS = os.path.join(ROOT, "docs", "nfl-e5e38f9e")

STATUS_LABEL = {
    "built_checked": "Built and checked",
    "built_partial": "Partly built",
    "partial": "Partly built",
    "not_built": "Not built",
    "blocked_external": "Blocked by an outside source",
    "owner_decision_needed": "Needs an owner decision",
    "honored_by_design": "Rejected approach not used",
    "pending": "Pending integration",
}
STATUS_CLASS = {
    "built_checked": "ok",
    "built_partial": "warn",
    "partial": "warn",
    "not_built": "bad",
    "blocked_external": "bad",
    "owner_decision_needed": "warn",
    "honored_by_design": "ok",
    "pending": "muted",
}

# Club code normalisation: official logo codes vs schedule/alias codes used by packs.
CLUB_ALIAS = {"ARI": "AZ", "LAR": "LA"}


def club(code: str) -> str:
    c = (code or "").strip().upper()
    return CLUB_ALIAS.get(c, c)


def norm_name(name: str) -> str:
    return re.sub(r"[^a-z]", "", (name or "").lower())


def read_csv(rel: str, delim: str = ",") -> list[dict]:
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter=delim))


def read_local(name: str) -> list[dict]:
    return read_csv(os.path.join("data", "nfl_e5e38f9e", name))


# ---------------------------------------------------------------- pack loaders
def pack_results_w10() -> dict[str, list[dict]]:
    """Return {pack: [ {away, home, away_score, home_score, status} ]} for Week 10 rows only."""
    out: dict[str, list[dict]] = {}

    def add(pack, rows):
        out.setdefault(pack, []).extend(rows)

    r = read_csv("data/nfl_d966f630/results_feed.csv")
    add("d966f630", [{"away": x["away"], "home": x["home"], "away_score": x["away_points"],
                      "home_score": x["home_points"], "status": x["feed_status"]}
                     for x in r if x["week"] == "10"])
    r = read_csv("data/nfl_6cefc476/results_feed.csv")
    add("6cefc476", [{"away": x["away"], "home": x["home"], "away_score": x["away_score"],
                      "home_score": x["home_score"], "status": x["status"]}
                     for x in r if x["week"] == "10"])
    r = read_csv("data/nfl_f4/results.csv")
    add("f4", [{"away": x["away"], "home": x["home"], "away_score": x["away_score"],
                "home_score": x["home_score"], "status": x["status"]}
               for x in r if x["week"] == "10"])
    r = read_csv("data/nfl_market/results.csv")
    add("market", [{"away": x["away_team"], "home": x["home_team"], "away_score": x["away_score"],
                    "home_score": x["home_score"], "status": x["result_status"]}
                   for x in r if x["week"] == "10"])
    r = read_csv("data/nfl_309921cc/results_feed.csv")
    add("309921cc", [{"away": x["away"], "home": x["home"], "away_score": x["away_score"],
                      "home_score": x["home_score"], "status": x["result_status"]}
                     for x in r if x["game_id"].startswith("W10")])
    r = read_csv("data/nfl_a411fed0/results_2026_verified.psv", delim="|")
    add("a411fed0", [{"away": x["away_abbr"], "home": x["home_abbr"], "away_score": x["away_score"],
                      "home_score": x["home_score"], "status": x["result_status"]}
                     for x in r if x["week"] == "10"])
    return out


PACK_ORDER = ["d966f630", "6cefc476", "f4", "market", "309921cc", "a411fed0"]


def reconcile_finals() -> list[dict]:
    official = read_local("official_w10_finals.csv")
    packs = pack_results_w10()
    rows = []
    for g in official:
        final = g["official_status_at_read"] == "Final"
        pair = {club(g["away"]), club(g["home"])}
        for pack in PACK_ORDER:
            hits = [p for p in packs.get(pack, []) if {club(p["away"]), club(p["home"])} == pair]
            if not final:
                result, pscore = "not_final_at_read", ""
            elif not hits:
                result, pscore = "missing_in_pack", ""
            else:
                p = hits[0]
                pscore = f'{club(p["away"])} {p["away_score"]} - {club(p["home"])} {p["home_score"]}'
                if not (p["status"] or "").lower().startswith("final"):
                    result = "pack_not_final"
                else:
                    same = (club(p["away"]) == club(g["away"])
                            and p["away_score"] == g["away_score"]
                            and p["home_score"] == g["home_score"])
                    flip = (club(p["away"]) == club(g["home"])
                            and p["away_score"] == g["home_score"]
                            and p["home_score"] == g["away_score"])
                    result = "match" if (same or flip) else "score_conflict"
            rows.append({
                "game_key": g["game_key"],
                "official_matchup": f'{club(g["away"])} {g["away_score"]} - {club(g["home"])} {g["home_score"]}',
                "official_status_at_read": g["official_status_at_read"],
                "pack": pack,
                "pack_value": pscore,
                "result": result,
                "official_source_url": g["official_game_page"] or g["official_schedule_page"],
                "read_on_utc": g["read_on_utc"],
            })
    return rows


def pack_injuries_w10() -> dict[str, dict[tuple[str, str], dict]]:
    out: dict[str, dict[tuple[str, str], dict]] = {}

    def put(pack, rows, club_key, player_key, prac_key, game_key):
        d = out.setdefault(pack, {})
        for x in rows:
            k = (club(x[club_key]), norm_name(x[player_key]))
            d[k] = {"practice": x[prac_key], "game": x[game_key]}

    put("d966f630", [x for x in read_csv("data/nfl_d966f630/injury_report_rows.csv") if x["week"] == "10"],
        "club", "player", "practice_status", "game_status")
    put("309921cc", read_csv("data/nfl_309921cc/week10_injuries.csv"),
        "team_abbr", "player", "practice_status", "game_status")
    put("a411fed0", read_csv("data/nfl_a411fed0/injuries_2026_w10.psv", delim="|"),
        "team_abbr", "player", "practice_status", "game_status")
    put("nfl_wk", read_csv("data/nfl_wk/injuries_week10.csv"),
        "team", "player", "practice_status", "game_status")
    put("market", read_csv("data/nfl_market/injuries_week10.csv"),
        "team_abbr", "player", "practice_status", "game_status")
    return out


INJ_PACKS = ["d966f630", "309921cc", "a411fed0", "nfl_wk", "market"]


def compare_injuries() -> list[dict]:
    official = read_local("official_injury_spotcheck.csv")
    packs = pack_injuries_w10()
    rows = []
    for o in official:
        key = (club(o["club"]), norm_name(o["player"]))
        row = {
            "row_id": o["row_id"],
            "club": o["club"],
            "player": o["player"],
            "official_practice": o["practice_status_official"],
            "official_game": o["game_status_official"],
        }
        for pack in INJ_PACKS:
            p = packs.get(pack, {}).get(key)
            if p is None:
                row[f"{pack}_result"] = "absent"
                row[f"{pack}_practice"] = ""
                row[f"{pack}_game"] = ""
            else:
                row[f"{pack}_practice"] = p["practice"]
                row[f"{pack}_game"] = p["game"]
                if p["practice"] != o["practice_status_official"]:
                    res = "practice_conflict"
                elif p["game"] != o["game_status_official"]:
                    res = "game_conflict"
                else:
                    res = "match"
                row[f"{pack}_result"] = res
        row["official_source_url"] = o["official_source_url"]
        row["read_on_utc"] = o["read_on_utc"]
        rows.append(row)
    return rows


INJ_COLS = (["row_id", "club", "player", "official_practice", "official_game"]
            + [f"{p}_{s}" for p in INJ_PACKS for s in ("result", "practice", "game")]
            + ["official_source_url", "read_on_utc"])
REC_COLS = ["game_key", "official_matchup", "official_status_at_read", "pack", "pack_value",
            "result", "official_source_url", "read_on_utc"]


def to_csv(rows: list[dict], cols: list[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return buf.getvalue()


# ---------------------------------------------------------------- HTML helpers
CSS = """
:root{--ink:#13283b;--muted:#526477;--navy:#10263c;--teal:#087e79;--line:#d8e1e5;--paper:#f4f7f8;
--ok:#0d6b3a;--okbg:#e2f5ea;--warn:#704500;--warnbg:#fff3d8;--bad:#8a1c1c;--badbg:#fbe4e4;--mutedbg:#eef1f3}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper);line-height:1.5}
a{color:var(--teal)}header{background:var(--navy);color:#fff;padding:20px 24px}header a{color:#a8f0d3}
header h1{margin:0 0 4px;font-size:1.5rem}header p{margin:0;color:#c8d6df;font-size:.95rem}
nav{background:#fff;border-bottom:1px solid var(--line);padding:10px 24px;font-size:.95rem}nav a{margin-right:16px;text-decoration:none;font-weight:600}
main{max-width:1200px;margin:0 auto;padding:20px 24px 40px}section{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:18px}
h2{margin:0 0 10px;font-size:1.2rem}h3{margin:14px 0 6px;font-size:1rem}
.note{background:var(--warnbg);color:var(--warn);border-radius:8px;padding:10px 14px;margin:0 0 14px}
.boundary{color:var(--muted);font-size:.9rem}
table{width:100%;border-collapse:collapse;font-size:.88rem;margin-top:8px}th,td{text-align:left;vertical-align:top;padding:7px 8px;border-bottom:1px solid var(--line)}
th{background:var(--soft,#e9f2f2);font-size:.82rem;text-transform:uppercase;letter-spacing:.02em;color:var(--muted)}
tr:nth-child(even) td{background:#fbfdfd}.wrap{overflow-x:auto}
.badge{display:inline-block;border-radius:999px;padding:2px 9px;font-size:.78rem;font-weight:600;white-space:nowrap}
.ok{background:var(--okbg);color:var(--ok)}.warn{background:var(--warnbg);color:var(--warn)}.bad{background:var(--badbg);color:var(--bad)}.muted{background:var(--mutedbg);color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}.card{border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#fff}
.card b{display:block;font-size:1.5rem}.card span{color:var(--muted);font-size:.85rem}
footer{color:var(--muted);font-size:.85rem;text-align:center;padding:20px}
"""

PAGES = [
    ("index.html", "Landing"),
    ("reconciliation.html", "Week 10 official reconciliation"),
    ("injuries.html", "Week 10 injury spot-check"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions (review only)"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]


def esc(v) -> str:
    return html.escape(str(v or ""))


def link(url: str, text: str | None = None) -> str:
    if not url:
        return '<span class="muted badge">blank: no official source</span>'
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'


def badge(status: str) -> str:
    cls = STATUS_CLASS.get(status, "muted")
    return f'<span class="badge {cls}">{esc(STATUS_LABEL.get(status, status))}</span>'


def page(name: str, title: str, body: str) -> str:
    nav = "".join(f'<a href="{esc(p)}">{esc(lbl)}</a>' for p, lbl in PAGES)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | Own6 NFL evidence pack</title>
<style>{CSS}</style></head>
<body>
<header><h1>{esc(title)}</h1>
<p>Own6 · NFL evidence pack e5e38f9e · Official values link to nfl.com; blank means unverified. Nothing here shows an edge or a profit.</p></header>
<nav>{nav} <a href="../../README.md">Repository README</a></nav>
<main>{body}</main>
<footer>Built by scripts/build_nfl_e5e38f9e.py from data/nfl_e5e38f9e/. Generated file: edit the CSV, not this page.</footer>
</body></html>
"""


def table(headers: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="wrap"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


# ---------------------------------------------------------------- pages
def page_index() -> str:
    trace = read_local("brief_trace.csv")
    counts: dict[str, int] = {}
    for r in trace:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    cards = "".join(
        f'<div class="card"><b>{counts.get(k, 0)}</b><span>{esc(STATUS_LABEL[k])}</span></div>'
        for k in ["built_checked", "built_partial", "partial", "not_built", "blocked_external",
                  "owner_decision_needed", "honored_by_design", "pending"] if counts.get(k))
    rows = []
    for r in trace:
        rows.append([
            esc(r["item_id"]),
            esc(r["brief_item"]),
            badge(r["status"]),
            esc(r["blocking_gate"]) or "<span class='muted'>none</span>",
            esc(r["number_that_clears_it"]) or "<span class='muted'>none</span>",
            esc(r["flag_ids"]),
        ])
    body = f"""
<section>
  <h2>Summary</h2>
  <p class="note">Nothing in this pack shows a profitable NFL edge. No market price is published here: no official NFL price source exists, and one earlier pack holds third-party prices labelled verified that this pack does not accept (flag E5-F16). No ROI, CLV or edge is published. Each row below is one requirement from the brief, its status, the gate that blocks it, and the number that would clear it.</p>
  <div class="cards">{cards}</div>
  <p class="boundary">Status counts: {len(trace)} brief items. Repo-status rows cite repository files; official facts appear only as links on the reconciliation and injury pages.</p>
</section>
<section>
  <h2>Decision-readiness table (one row per requirement)</h2>
  {table(["ID", "Requirement (from the brief)", "Status", "Blocking gate", "Number that clears it", "Flags"], rows)}
  <p class="boundary">Full evidence for each row: data/nfl_e5e38f9e/brief_trace.csv. Week 10 official values: <a href="reconciliation.html">reconciliation</a> and <a href="injuries.html">injury spot-check</a>.</p>
</section>
<section>
  <h2>Start here</h2>
  <ul>
    <li><a href="flagged.html">Flagged for Review</a> — {len(read_local('flagged.csv'))} items with evidence, blocking status and official links where read.</li>
    <li><a href="questions.html">Questions</a> — what must be answered before any decision, and how to answer each.</li>
    <li><a href="suggestions.html">Suggestions</a> — options for review; none is applied.</li>
    <li><a href="sources.html">Sources</a> — every official page read this session, with what was and was not read.</li>
  </ul>
</section>"""
    return page("index.html", "Own6 | NFL decision readiness", body)


def page_reconciliation() -> str:
    finals = read_local("official_w10_finals.csv")
    recon = reconcile_finals()
    by_game: dict[str, dict[str, dict]] = {}
    for r in recon:
        by_game.setdefault(r["game_key"], {})[r["pack"]] = r
    rows = []
    for g in finals:
        cells = [esc(g["game_key"]), esc(f'{club(g["away"])} {g["away_score"]} – {club(g["home"])} {g["home_score"]}'),
                 esc(g["official_status_at_read"]), link(g["official_game_page"], "game page")]
        for pack in PACK_ORDER:
            r = by_game.get(g["game_key"], {}).get(pack)
            cells.append(esc(r["result"]) if r else "")
        rows.append(cells)
    body = f"""
<section>
  <h2>Official Week 10 games as read on 2026-11-15</h2>
  <p class="note">Source: <a href="https://www.nfl.com/schedules/2026/by-week/week-10">nfl.com Week 10 schedule</a>, read with the page-fetch tool on 2026-11-15. Three games were still in progress at the read, and two had not started; those are not compared with any pack.</p>
  {table(["Game key", "Official score (away – home)", "Status at read", "Official game page", *[f"Pack: {p}" for p in PACK_ORDER]], rows)}
</section>
<section>
  <h2>How to read the pack columns</h2>
  <ul>
    <li><b>match</b>: the pack holds this final with the same score.</li>
    <li><b>missing_in_pack</b>: the official game is final but the pack has no row for it.</li>
    <li><b>score_conflict</b>: the pack holds a different score (none found).</li>
    <li><b>pack_not_final</b>: the pack holds the game but not as final.</li>
    <li><b>not_final_at_read</b>: the game was live or scheduled at the official read; nothing is compared.</li>
  </ul>
  <p class="boundary">Machine-readable: data/nfl_e5e38f9e/w10_pack_reconciliation.csv (one row per game and pack).</p>
</section>"""
    return page("reconciliation.html", "Week 10 official reconciliation", body)


def page_injuries() -> str:
    rows = compare_injuries()
    head = ["Row", "Club", "Player", "Official practice", "Official game status"] + [f"{p}" for p in INJ_PACKS]
    trs = []
    for r in rows:
        cells = [esc(r["row_id"]), esc(r["club"]), esc(r["player"]), esc(r["official_practice"]) or "<span class='muted'>blank</span>",
                 esc(r["official_game"]) or "<span class='muted'>blank</span>"]
        for p in INJ_PACKS:
            res = r[f"{p}_result"]
            cls = "ok" if res == "match" else ("bad" if res in ("practice_conflict", "game_conflict") else "muted")
            detail = f'{r[p + "_practice"] or "blank"} / {r[p + "_game"] or "blank"}'
            cells.append(f'<span class="badge {cls}">{esc(res)}</span><br><span class="boundary">{esc(detail)}</span>')
        trs.append(cells)
    summary = []
    for p in INJ_PACKS:
        m = sum(1 for r in rows if r[f"{p}_result"] == "match")
        c = sum(1 for r in rows if r[f"{p}_result"] in ("practice_conflict", "game_conflict"))
        a = sum(1 for r in rows if r[f"{p}_result"] == "absent")
        summary.append([esc(p), str(len(rows)), str(m), str(c), str(a)])
    body = f"""
<section>
  <h2>Official Week 10 injury rows read in full (four clubs)</h2>
  <p class="note">Source: <a href="https://www.nfl.com/injuries/">nfl.com injury report, Week 10</a>, read with the page-fetch tool on 2026-11-15 (chunk 0 of 8). Washington, Giants, Patriots and Lions blocks, {len(rows)} rows. Other clubs were not read in this session. A pack that lacks a row is shown as absent, not as available.</p>
  <h3>Pack agreement with the official rows</h3>
  {table(["Pack", "Official rows", "Match", "Conflict", "Absent"], summary)}
</section>
<section>
  <h2>Row-by-row comparison</h2>
  {table(INJ_HEADERS_FOR_PAGE(), trs)}
  <p class="boundary">Machine-readable: data/nfl_e5e38f9e/injury_pack_comparison.csv. Pack keys: d966f630 injury_report_rows.csv; 309921cc week10_injuries.csv; a411fed0 injuries_2026_w10.psv; nfl_wk injuries_week10.csv; market injuries_week10.csv.</p>
</section>"""
    return page("injuries.html", "Week 10 injury spot-check", body)


def INJ_HEADERS_FOR_PAGE() -> list[str]:
    return ["Row", "Club", "Player", "Official practice", "Official game"] + [f"Pack: {p}" for p in INJ_PACKS]


def page_list(name: str, title: str, file: str, cols: list[str], labels: list[str], note: str) -> str:
    rows = read_local(file)
    trs = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            if c.endswith("url") or c == "official_source_url":
                cells.append(link(v))
            elif c == "status" or c == "severity":
                cells.append(badge(v) if c == "status" else esc(v))
            else:
                cells.append(esc(v) or "<span class='muted'>blank</span>")
        trs.append(cells)
    body = f'<section><p class="note">{esc(note)}</p>{table(labels, trs)}</section>'
    return page(name, title, body)


def page_flagged() -> str:
    rows = read_local("flagged.csv")
    trs = []
    for r in rows:
        trs.append([
            esc(r["flag_id"]),
            f'<span class="badge {"bad" if r["severity"] == "high" else "warn"}">{esc(r["severity"])}</span>',
            esc(r["title"]),
            esc(r["what_we_observed"]),
            esc(r["evidence_and_where"]),
            esc(r["why_it_matters"]),
            esc(r["does_it_block_merge"]),
            link(r["official_source_url"]) if r["official_source_url"] else "<span class='muted'>blank: no official page read for this flag</span>",
        ])
    body = f"""<section><p class="note">Flagged for Review. These items do not block the merge. Each one has its evidence and the reason it matters. A blank source means no official page was read for that flag.</p>
{table(["Flag", "Severity", "Title", "What we observed", "Evidence / where", "Why it matters", "Blocks merge?", "Official source"], trs)}</section>"""
    return page("flagged.html", "Flagged for Review", body)


def page_suggestions() -> str:
    rows = read_local("suggestions.csv")
    trs = []
    for r in rows:
        trs.append([
            esc(r["suggestion_id"]), esc(r["title"]), esc(r["problem_it_solves"]), esc(r["options_for_review"]),
            f'<b>{esc(r["recommended_path"])}</b>', esc(r["why_recommended"]), esc(r["effort"]),
            esc(r["status"]), link(r["official_source_url"]) if r["official_source_url"] else "<span class='muted'>none</span>",
        ])
    body = f"""<section><p class="note">Review only. No suggestion has been applied. Choose an option per row before any change is made.</p>
{table(["ID", "Suggestion", "Problem it solves", "Options", "Recommended", "Why", "Effort", "Status", "Official source"], trs)}</section>"""
    return page("suggestions.html", "Suggestions (review only)", body)


def page_questions() -> str:
    rows = read_local("questions.csv")
    trs = []
    for r in rows:
        trs.append([esc(r["question_id"]), esc(r["question"]), esc(r["what_we_have"]), esc(r["what_we_lack"]),
                    esc(r["how_to_answer"]), esc(r["answer_type"]), esc(r["blocks_which_brief_items"]),
                    esc(r["owner_decides"]), link(r["official_source_url"]) if r["official_source_url"] else "<span class='muted'>none</span>"])
    body = f"""<section><p class="note">Questions that must be answered before a decision can be made on the evidence we have. "self_serveable" questions can be answered by an agent reading official pages; "owner_decision" questions need a human choice.</p>
{table(["ID", "Question", "What we have", "What we lack", "How to answer it", "Answer type", "Blocks brief items", "Owner decides", "Official source"], trs)}</section>"""
    return page("questions.html", "Questions", body)


def page_sources() -> str:
    rows = read_local("sources.csv")
    trs = [[esc(r["source_id"]), esc(r["publisher"]), link(r["url"]), esc(r["read_on_utc"]), esc(r["read_method"]),
            esc(r["what_was_read"]), esc(r["what_it_supports"]), esc(r["what_it_does_not_support"])] for r in rows]
    body = f"""<section><p class="note">Only official pages read in this session count as sources. A link without a read is shown as not read.</p>
{table(["ID", "Publisher", "URL", "Read on (UTC)", "Method", "What was read", "Supports", "Does not support"], trs)}</section>"""
    return page("sources.html", "Sources", body)


def build_outputs() -> dict[str, str]:
    """Return {absolute path: content} for every generated file."""
    out: dict[str, str] = {}
    out[os.path.join(DATA, "w10_pack_reconciliation.csv")] = to_csv(reconcile_finals(), REC_COLS)
    out[os.path.join(DATA, "injury_pack_comparison.csv")] = to_csv(compare_injuries(), INJ_COLS)
    out[os.path.join(DOCS, "index.html")] = page_index()
    out[os.path.join(DOCS, "reconciliation.html")] = page_reconciliation()
    out[os.path.join(DOCS, "injuries.html")] = page_injuries()
    out[os.path.join(DOCS, "questions.html")] = page_questions()
    out[os.path.join(DOCS, "suggestions.html")] = page_suggestions()
    out[os.path.join(DOCS, "flagged.html")] = page_flagged()
    out[os.path.join(DOCS, "sources.html")] = page_sources()
    return out


def main(argv: list[str]) -> int:
    outputs = build_outputs()
    if "--check" in argv:
        drift = []
        for path, text in outputs.items():
            cur = None
            if os.path.exists(path):
                with open(path, encoding="utf-8") as fh:
                    cur = fh.read()
            if cur != text:
                drift.append(os.path.relpath(path, ROOT))
        if drift:
            print("DRIFT:", *drift, sep="\n  ")
            return 1
        print(f"OK: {len(outputs)} generated files match their sources")
        return 0
    os.makedirs(DOCS, exist_ok=True)
    for path, text in outputs.items():
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    print(f"wrote {len(outputs)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
