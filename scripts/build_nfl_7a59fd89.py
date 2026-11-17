#!/usr/bin/env python3
"""Build the nfl_7a59fd89 pack site: GitHub Pages pages from committed capture CSVs.

The builder takes no arguments and touches no network: a re-run must produce
byte-identical files (determinism is asserted by tests). Data CSVs are capture
artifacts written by the session reads + src modules; this script only renders.

Usage
-----
    python3 scripts/build_nfl_7a59fd89.py            # write HTML pages
    python3 scripts/build_nfl_7a59fd89.py --check    # build, then run the verifier
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_7a59fd89")
DOCS = os.path.join(REPO, "docs", "nfl-7a59fd89")
OFFICIAL_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com", "github.com")

URLCOLS = ("source_url", "source_urls", "url", "game_page_url", "week_page_url",
           "roster_status_source")

PAGE_SOURCES = {
    "delta.html": "https://www.nfl.com/injuries/",
    "sweep.html": "https://www.nfl.com/teams/",
}


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url: str, label: str = "source") -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)} &#8599;</a>'


def official_link(url: str) -> str:
    return link(url)


NAV = [
    ("index.html", "Decision readiness"),
    ("finals.html", "Week-10 finals"),
    ("sweep.html", "32-club sweep"),
    ("conflicts.html", "Availability conflicts"),
    ("delta.html", "Injury cross-read delta"),
    ("announcement.html", "Schedule announcement"),
    ("findings.html", "Repo review findings"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]


def page(title: str, body: str, active: str) -> str:
    nav = ""
    for href, label in NAV:
        cls = ' class="on"' if href == active else ""
        nav += f'<a href="{href}"{cls}>{esc(label)}</a>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — nfl 7a59fd89</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#101418;color:#e8eaed}}
header{{padding:18px 22px;border-bottom:1px solid #2a2f36}}
h1{{font-size:20px;margin:0 0 4px}} h2{{font-size:16px;margin:18px 0 8px}}
nav{{padding:10px 22px;border-bottom:1px solid #2a2f36;display:flex;flex-wrap:wrap;gap:10px}}
nav a{{color:#8ab4f8;text-decoration:none;font-size:13px}} nav a.on{{color:#fff;font-weight:600}}
main{{padding:18px 22px;max-width:1200px}}
p{{font-size:14px;line-height:1.5;max-width:900px}}
table{{border-collapse:collapse;width:100%;font-size:12px;margin:10px 0 18px}}
th,td{{border:1px solid #2a2f36;padding:5px 7px;text-align:left;vertical-align:top}}
th{{background:#1a2027;position:sticky;top:0}}
tr:nth-child(even) td{{background:#141a20}}
td a{{color:#8ab4f8;text-decoration:none}}
.flag{{color:#f6c344}} .ok{{color:#81c995}} .blank{{color:#5f6368}}
.note{{font-size:12px;color:#9aa0a6}}
</style></head><body>
<header><h1>nfl 7a59fd89 — 32-club roster/IR sweep + Week-10 finals settlement</h1>
<p class="note">Every published value was read from a cited official page or is arithmetic on such
values with the derivation shown. Unverifiable values stay blank and are flagged.
"Not listed" never means "available". Nothing is inferred.</p></header>
<nav>{nav}</nav>
<main>
{body}
</main></body></html>
"""


def table(rows: list[dict], cols: list[str], default_source: str = "") -> str:
    out = ["<table><thead><tr>"]
    for c in cols:
        out.append(f"<th>{esc(c)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        has_link = False
        for c in cols:
            v = "" if r.get(c) is None else str(r.get(c))
            cell = esc(v)
            if c in URLCOLS and v:
                parts = [u.strip() for u in v.split(";") if u.strip()]
                if not parts:
                    parts = [v]
                has_link = has_link or any(h in v for h in OFFICIAL_HOSTS)
                cell = " ".join(link(u, "source &#8599;") for u in parts)
            elif c == "source_url" and not v and default_source:
                cell = official_link(default_source)
                has_link = True
            out.append(f"<td>{cell}</td>")
        if not has_link and default_source:
            out.append(f"<td>{official_link(default_source)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def read_csv(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_page(name: str, title: str, body: str) -> str:
    os.makedirs(DOCS, exist_ok=True)
    path = os.path.join(DOCS, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(page(title, body, name))
    return path


def build() -> list[str]:
    written = []

    # ---- finals.html ----
    finals = read_csv("week10_finals.csv")
    settled = [r for r in finals if r["status"] == "FINAL"]
    live = [r for r in finals if r["status"] != "FINAL"]
    body = ["<h2>Week-10 finals settlement</h2>",
            f"<p>13 finals settled from <a href=\"https://www.nfl.com/scores/\" rel=\"noopener noreferrer\" target=\"_blank\">nfl.com/scores</a> (read 2026-11-17T01:15:22Z) and corroborated verbatim by the schedules page (01:26Z). All 13 reconcile exactly with the club records read on the 32 roster pages this session.</p>",
            "<p class=\"flag\">LAC@BAL was in progress (Q1, LAC 7-0) at capture time: score cells stay blank until a final read. An earlier session note claiming a 24-14 final is unverifiable and contradicted by three reads — never published as a result.</p>",
            table(settled, ["game_id", "game_date", "kickoff_et", "away_team", "home_team",
                            "away_score", "home_score", "status", "score_source", "read_at_utc", "source_url"]),
            "<h2>Not settled at capture time</h2>",
            table(live, ["game_id", "game_date", "kickoff_et", "away_team", "home_team",
                         "away_score", "home_score", "status", "read_at_utc", "source_url", "notes"]),
            "<h2>Corpus extension</h2>",
            "<p>The verified results feed extends weeks 1-9 (136 rows, 8362b702) with the 14 week-10 rows: <code>data/nfl_7a59fd89/corpus_150.csv</code> (136 + 14 = 150; margin_home = home − away and total = away + home shown only when both scores are settled).</p>"]
    written.append(write_page("finals.html", "Week-10 finals", "".join(body)))

    # ---- sweep.html ----
    sweep = read_csv("roster_sweep.csv")
    register = read_csv("roster_reserve.csv")
    from collections import Counter
    codes = Counter(r["status_code"] for r in register)
    code_line = ", ".join(f"{k} {v}" for k, v in sorted(codes.items()))
    body = ["<h2>32-club roster/IR sweep</h2>",
            f"<p>2,845 roster rows read across all 32 club pages (window 2026-11-17 00:47-01:11Z). Non-ACT register: <b>{len(register)} rows</b>. League-wide status codes: <b>{esc(code_line)}</b>. New codes this sweep, recorded verbatim: RLS (SF, Brandon Aiyuk), EXE (SEA, Terrion Arnold).</p>",
            "<p>Every sweep aggregate below is re-derived from <code>roster_reserve.csv</code> (per-row truth); the <code>trd_rows</code> column lumps TRC/TRD/TRT/RSR/RSN/RLS/EXE.</p>",
            table(sweep, ["club", "url", "act_rows", "res_rows", "pup_rows", "cut_rows",
                          "dev_rows", "trd_rows", "total_rows_read", "read_at_utc"]),
            "<p class=\"flag\">KC act_rows is provisional (chunk-boundary tail never transcribed); all non-ACT counts are row-level verified.</p>"]
    written.append(write_page("sweep.html", "32-club sweep", "".join(body)))

    # ---- conflicts.html ----
    conflicts = read_csv("availability_conflicts.csv")
    kinds = Counter(r["conflict_kind"] for r in conflicts)
    kind_line = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
    body = ["<h2>Availability cross-checks</h2>",
            f"<p>{len(conflicts)} flagged conflicts in 6 kinds: <b>{esc(kind_line)}</b>. Conflicts are flagged, never resolved by inference.</p>",
            table(conflicts, ["conflict_id", "conflict_kind", "club", "player", "position",
                              "roster_page_status", "roster_status_source",
                              "hub_status_or_other_side", "source_urls", "disposition"])]
    written.append(write_page("conflicts.html", "Availability conflicts", "".join(body)))

    # ---- delta.html ----
    delta = read_csv("injury_delta.csv")
    body = ["<h2>Injury hub cross-read delta (2026-11-15 vs 2026-11-17)</h2>",
            "<p>Both dated reads cover 28 clubs x 347 rows. The only delta is one display-name variant; practice statuses, game statuses and injury text are identical across every dated sibling read pair (11-15T18:40Z, 11-15T23:58Z, 11-16T00:50Z, 11-17T00:45:48Z).</p>",
            "<p class=\"flag\">An earlier session note of \"170 injury-field diffs\" is superseded: the figure corresponds to the 171 non-empty injury cells (a count, not a diff).</p>",
            table(delta, ["club", "player_prior", "player_current", "position", "delta_kind"],
                  default_source="https://www.nfl.com/injuries/")]
    written.append(write_page("delta.html", "Injury cross-read delta", "".join(body)))

    # ---- announcement.html ----
    ann = read_csv("schedule_announcement.csv")
    body = ["<h2>Dated schedule-announcement capture (G-ANNOUNCE)</h2>",
            "<p>The league's dated schedule announcements were captured verbatim from the official procedures page and the TBD-games block published beside the live schedule page. No standalone season-schedule press release was located; the interpretation is flagged for review.</p>",
            table(ann, ["attempt_id", "target", "outcome", "detail", "read_at_utc"],
                  default_source="https://www.nfl.com/legal/flexible-scheduling-procedures")]
    written.append(write_page("announcement.html", "Schedule announcement", "".join(body)))

    # ---- findings.html ----
    findings = read_csv("repo_findings.csv")
    body = ["<h2>Repository review findings (R-01..R-73)</h2>",
            "<p>Line-by-line re-verification of the 8362b702 readiness ledger against the working tree. Narrative: <code>audit/NFL_7A59FD89_REPO_REVIEW.md</code>. Result: 0 missing claimed artifacts, 0 fabrications; 2 wording mismatches recorded (drift module location; reserve.csv name).</p>",
            table(findings, ["requirement_id", "claimed_status", "verification",
                             "evidence_this_session", "gate_that_blocks_it", "checked_at_utc"],
                  default_source="https://github.com/sassnarep3-star/Own6")]
    written.append(write_page("findings.html", "Repo review findings", "".join(body)))

    # ---- flagged.html ----
    flagged = read_csv("flagged.csv")
    body = ["<h2>Flagged for review</h2>",
            "<p>Irregularities, corrected errors and interpretation decisions this pack publishes. Flagged items never block; they are published so a human can review.</p>",
            table(flagged, ["flag_id", "flag_class", "detail", "source_urls", "disposition"])]
    written.append(write_page("flagged.html", "Flagged for review", "".join(body)))

    # ---- sources.html ----
    sources = read_csv("sources.csv")
    body = ["<h2>Sources read this session</h2>",
            "<p>Every official page read by session 7a59fd89, with the read clock and what it fed.</p>",
            table(sources, ["source_id", "url", "read_at_utc", "what_was_read", "pack_use"])]
    written.append(write_page("sources.html", "Sources", "".join(body)))

    # ---- executive-summary.html ----
    exec_md = os.path.join(REPO, "NFL_7A59FD89_EXECUTIVE_SUMMARY.md")
    with open(exec_md, encoding="utf-8") as f:
        md = f.read()
    paras = []
    in_code = False
    for chunk in md.split("\n\n"):
        c = chunk.strip()
        if c.startswith("```"):
            in_code = not in_code
            paras.append("<pre>" + esc("\n".join(chunk.splitlines()[1:-1])) + "</pre>")
            continue
        if in_code:
            paras.append("<pre>" + esc(chunk) + "</pre>")
        elif c.startswith("## "):
            paras.append(f"<h2>{esc(c[3:])}</h2>")
        elif c.startswith("# "):
            paras.append(f"<h2>{esc(c[2:])}</h2>")
        elif c.startswith("- "):
            paras.append("<p>" + "<br>".join("&#8226; " + esc(ln[2:]) for ln in c.splitlines()) + "</p>")
        elif c:
            paras.append(f"<p>{esc(c)}</p>")
    written.append(write_page("executive-summary.html", "Executive summary", "".join(paras)))

    # ---- index.html ----
    gates = [
        ("G-SWEEP", "roster leg satisfied (32/32 clubs; 1,142 non-ACT rows)", "hub leg 28/32: CHI DEN PHI TB not listed on hub page (week-10 bye presentation) — flagged, not inferred"),
        ("G-ANNOUNCE", "evidence captured", "dated official announcement page + on-schedule-page TBD block; interpretation flagged for review"),
        ("G-GAMEBOOK", "blocked", "Game Book host unreachable (carried from prior sessions)"),
        ("G-SNAP", "open", "no official snap-count source read (carried)"),
        ("G-DEPTH-SRC", "open", "Texans image / Packers numbering carried"),
        ("G-PRICE", "open", "no official market-price source (carried)"),
        ("G-TERMS", "open", "Terms section 1.3 restricts automated capture; manual single fetches only"),
        ("G-SCHED", "open", "no scheduled automation built (rights question carried)"),
        ("G-SETTLE", "open", "no settled leaderboard window yet (carried)"),
        ("G-JOINT", "open", "no validated joint evidence (carried)"),
    ]
    rows = [{"gate": g, "state": s, "note": n} for g, s, n in gates]
    body = ["<h2>Decision readiness — session 7a59fd89</h2>",
            "<p>Workstreams: W1 repo readiness re-verification (R-01..R-73, 0 missing artifacts) · W2 injury hub capture + cross-read delta (byte-stable; 1 name variant) · W3 32-club roster sweep (2,845 rows read; 1,142 registered; aggregates re-derived from the register) · W4 week-10 finals settlement (13 finals; 1 live game flagged) · W5 dated schedule-announcement capture · W6 availability cross-checks (96 flagged conflicts) · W7 pack site/verifier/tests/CI · W8 integration · W9 PR/merge/Pages.</p>",
            "<h2>Gate states after this session</h2>",
            table(rows, ["gate", "state", "note"],
                  default_source="https://github.com/sassnarep3-star/Own6"),
            "<h2>Key artifacts</h2>",
            "<ul>"
            "<li>Hub capture: <code>data/nfl_7a59fd89/injury_hub_2026_11_17.csv</code> (347 rows, 28 clubs)</li>"
            "<li>Roster register: <code>data/nfl_7a59fd89/roster_reserve.csv</code> (1,142 rows)</li>"
            "<li>Sweep blocks: <code>data/nfl_7a59fd89/roster_sweep.csv</code> (32 blocks)</li>"
            "<li>Finals: <code>data/nfl_7a59fd89/week10_finals.csv</code> (14 rows; 13 settled)</li>"
            "<li>Corpus extension: <code>data/nfl_7a59fd89/corpus_150.csv</code> (136 + 14)</li>"
            "<li>Cross-read delta: <code>data/nfl_7a59fd89/injury_delta.csv</code> (1 row)</li>"
            "<li>Cross-checks: <code>data/nfl_7a59fd89/availability_conflicts.csv</code> (96 rows)</li>"
            "<li>G-ANNOUNCE: <code>data/nfl_7a59fd89/schedule_announcement.csv</code></li>"
            "<li>Repo review: <code>audit/NFL_7A59FD89_REPO_REVIEW.md</code> + <code>data/nfl_7a59fd89/repo_findings.csv</code></li>"
            "</ul>",
            "<h2>Club records corroborated from roster-page headers (2026-11-17)</h2>",
            "<p>BUF 8-1 · SF 8-1 · KC CHI CIN DEN DET JAX MIN 7-2 · PIT 6-3 · GB CLE LAR SEA 6-4 · NE 5-5 · NYG 5-3-1 · BAL CAR 4-5 · DAL LV 4-6 · HOU NO TB 3-6 · AZ ATL IND 3-7 · WAS 3-5-1 · PHI 2-7 · NYJ 2-8 · LAC 0-8 · MIA TEN 1-8</p>",
            official_link("https://github.com/sassnarep3-star/Own6")]
    written.append(write_page("index.html", "Decision readiness", "".join(body)))

    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    written = build()
    print(f"built {len(written)} pages in docs/nfl-7a59fd89/")
    if args.check:
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_nfl_7a59fd89.py")])
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
