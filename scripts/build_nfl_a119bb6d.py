#!/usr/bin/env python3
"""Build the a119bb6d registers and the published pages for this pack.

The build is a pure function of the committed official reads. If a value is not
in the official read it is not in the page: the cell is blank and, where the
page can explain why, the reason is printed next to it.

Run: python3 scripts/build_nfl_a119bb6d.py
"""

from __future__ import annotations

import csv
import html
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_a119bb6d.registers import (  # noqa: E402
    build_availability_graph,
    build_designation_calibration,
    club_of,
    load,
    week_of_game,
)

DATA = os.path.join(ROOT, "data", "nfl_a119bb6d")
PARSED = os.path.join(DATA, "parsed")
DOCS = os.path.join(ROOT, "docs", "nfl-a119bb6d")

STYLE = """
:root{--ink:#16232e;--muted:#5d7183;--navy:#0f2433;--teal:#0a7d74;--line:#dbe3e8;--paper:#f5f8f9;
--white:#fff;--warn:#fff4dc;--warnink:#7a4b00;--ok:#0a6b4f;--bad:#9c2b2b;--soft:#eef4f5}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.55;
font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:15px}
a{color:var(--teal);text-underline-offset:.16em}
header{background:var(--navy);color:#fff}
.wrap{width:min(1280px,calc(100% - 2rem));margin:0 auto}
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
p{max-width:82ch}
.lead{color:var(--muted);max-width:86ch}
.cards{display:grid;gap:.7rem;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));margin:1rem 0 .4rem}
.card{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:.8rem .9rem}
.card .k{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.card .v{font-size:1.55rem;font-weight:700;line-height:1.15;margin-top:.15rem}
.card .s{font-size:.78rem;color:var(--muted)}
.tw{overflow-x:auto;background:var(--white);border:1px solid var(--line);border-radius:10px;margin:.6rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.83rem}
th,td{padding:.42rem .6rem;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--soft);font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;color:#39505f;
position:sticky;top:0;white-space:nowrap}
tbody tr:hover{background:#fbfdfd}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:.05rem .42rem;border-radius:999px;font-size:.72rem;font-weight:600;
white-space:nowrap;border:1px solid}
.p-met{background:#e7f6ef;color:var(--ok);border-color:#b9e3d0}
.p-blocked{background:#fdeaea;color:var(--bad);border-color:#f2c6c6}
.p-partially_met{background:var(--warn);color:var(--warnink);border-color:#f0d9a8}
.p-not_run,.p-out_of_scope{background:#eceff1;color:#4a5c69;border-color:#d3dae0}
.p-rejected_adopted{background:#eef0fb;color:#3d3f8a;border-color:#cfd4ef}
.note{background:var(--warn);border:1px solid #f0d9a8;border-left:4px solid #d99b1a;color:#4a3300;
padding:.7rem .9rem;border-radius:8px;margin:.9rem 0;max-width:94ch;font-size:.88rem}
.good{background:#eef8f3;border:1px solid #bfe3d2;border-left:4px solid var(--ok);color:#134a37;
padding:.7rem .9rem;border-radius:8px;margin:.9rem 0;max-width:94ch;font-size:.88rem}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;word-break:break-all}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.8rem;padding:1rem 0 2rem}
ul.tight{margin:.3rem 0 .8rem;padding-left:1.1rem}
ul.tight li{margin:.18rem 0;max-width:90ch}
"""

NAV = [
    ("index.html", "Overview"),
    ("game-books.html", "Official Game Books"),
    ("availability.html", "Availability graph"),
    ("calibration.html", "Designation calibration"),
    ("snapshots.html", "Snapshot ledger"),
    ("requirements.html", "Requirements"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def esc(value: object) -> str:
    return html.escape(str(value if value not in (None, "") else ""))


def link(url: str, label: str = "official source") -> str:
    if not url:
        return '<span class="mut">not published</span>'
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def table(headers: list[str], rows: list[list[str]], *, numeric: set[int] | None = None) -> str:
    numeric = numeric or set()
    head = "".join(
        f'<th class="{"n" if i in numeric else ""}">{esc(h)}</th>' for i, h in enumerate(headers)
    )
    body = []
    for row in rows:
        cells = "".join(
            f'<td class="{"n" if i in numeric else ""}">{c}</td>' for i, c in enumerate(row)
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        '<div class="tw"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def page(title: str, active: str, body: str, reads: str) -> str:
    nav = "".join(
        f'<a href="{esc(href)}" class="{"on" if href == active else ""}">{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own6 NFL official game books</title>
<style>{STYLE}</style></head>
<body>
<header><div class="wrap">
  <div class="top"><b>OWN6</b><span>NFL official availability · session a119bb6d</span>
  <span style="margin-left:auto;color:#8fb7b2">{esc(reads)}</span></div>
  <nav>{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap">Every row on these pages is read from an official NFL page or an official
NFL Game Book. Cells that the league does not publish are left blank and flagged on the
<a href="flagged.html">Flagged for review</a> page.</footer>
</body></html>
"""


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def write_csv(path: str, rows: list[dict], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    games = load("game_books.csv")
    lineups = load("gamebook_lineups.csv")
    participation = load("gamebook_participation.csv")
    injuries = load("injury_report.csv")
    inactives = load("inactives.csv")
    capture_log = load("capture_log.csv", os.path.join(DATA, "_capture"))
    problems = load("capture_problems.csv")

    availability, availability_problems = build_availability_graph(
        games, lineups, participation
    )
    calibration, calibration_problems = build_designation_calibration(
        injuries, games, lineups, participation
    )
    all_problems = (
        [p["problem"] for p in problems]
        + availability_problems
        + calibration_problems
    )

    # ---- derived registers ------------------------------------------------
    write_csv(
        os.path.join(DATA, "availability_graph.csv"),
        availability,
        [
            "week", "game_slug", "game_url", "club", "opponent", "side", "unit",
            "position", "expected_player", "actual_player", "change_type",
            "previous_game_slug", "replacement_string_lower_bound",
            "unavailable_ahead", "expected_source", "actual_source", "source_url",
            "read_at_utc", "note",
        ],
    )
    write_csv(
        os.path.join(DATA, "designation_calibration.csv"),
        calibration,
        [
            "designation", "n", "n_started", "n_played_off_bench",
            "n_did_not_play", "n_inactive", "n_not_in_game_book", "play_rate",
            "play_rate_ci95_low", "play_rate_ci95_high", "interpretation",
            "source_url", "read_at_utc",
        ],
    )
    write_csv(
        os.path.join(DATA, "capture_problems.csv"),
        [{"problem": p} for p in all_problems],
        ["problem"],
    )

    reads = ""
    if capture_log:
        stamps = sorted({row["fetched_at_utc"] for row in capture_log if row["fetched_at_utc"]})
        if stamps:
            reads = f"reads of {stamps[0][:10]} UTC"

    games_by_week: dict[int, list[dict]] = {}
    for game in games:
        games_by_week.setdefault(week_of_game(game["game_slug"]), []).append(game)

    # ---- pages ------------------------------------------------------------
    build_index(games, availability, calibration, capture_log, all_problems, reads)
    build_game_books(games, games_by_week, reads)
    build_availability(availability, games, reads)
    build_calibration(calibration, injuries, reads)
    build_snapshots(capture_log, reads)
    build_requirements(games, availability, calibration, all_problems, reads)
    build_flagged(all_problems, games, reads)
    build_sources(games, capture_log, reads)
    print(f"built {len(games)} games, {len(availability)} availability rows, "
          f"{len(calibration)} calibration rows, {len(all_problems)} problems")
    return 0


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def build_index(games, availability, calibration, capture_log, problems, reads) -> None:
    replaced = [r for r in availability if r["change_type"] == "replaced"]
    deeper = [r for r in replaced if r["replacement_string_lower_bound"] not in ("", "1")]
    designated = sum(int(c["n"]) for c in calibration)
    cards = [
        ("Official Game Books read", len(games), "each one hashed"),
        ("Availability rows", len(availability), "expected vs actual starters"),
        ("Starter replacements", len(replaced), "official Game Book evidence"),
        ("Replacements at depth 2+", len(deeper), "lower bound, official only"),
        ("Designated players joined", designated, "injury report to Game Book"),
        ("Official reads logged", len(capture_log), "with SHA-256 and clock time"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div>'
        f'<div class="s">{esc(s)}</div></div>'
        for k, v, s in cards
    )
    body = f"""
<h1>Official NFL Game Books, availability graph and snapshot ledger</h1>
<p class="lead">The league publishes an official <strong>Game Book</strong> for every game it
plays, linked from the league's own game centre. That one document carries the official starting
eleven on both sides of the ball, the game-day <em>Not Active</em> list, the stadium, the
90-minute roof and surface designation, the game-day weather, the final score and the paid
attendance. This pack reads it, hashes it, and turns it into the availability graph the model
needs: who was expected to start, who actually did, and how deep the replacement was.</p>

<div class="cards">{card_html}</div>

<div class="note"><strong>What this pack does not claim.</strong> The Game Book publishes no snap
counts and no player-participation table — a keyword scan of the whole document finds
<strong>0</strong> occurrences of &ldquo;snap&rdquo; and <strong>0</strong> of
&ldquo;participation&rdquo;. The league publishes no club depth chart either
(<code>https://www.nfl.com/teams/&lt;club&gt;/roster/depth-chart/</code> returns the league's
404 page). So the depth of a replacement is published here as a <strong>lower bound</strong>
counted from official Game Books alone, and the model must not pretend to know more.</div>

<h2>What changed because of this pack</h2>
<ul class="tight">
<li>The requirement to use <em>official NFL Game Books for actual starters and game-day status</em>
was recorded as blocked by earlier packs because no official source could be found. There is one.</li>
<li>The availability graph is no longer a plan: it is a dataset, with the expected starter taken
from the same club's official Game Book of its previous game.</li>
<li>The designation &ldquo;Questionable&rdquo; is no longer a number somebody remembered. It is
measured against the Game Book of the same week, with <em>n</em> and a 95% interval.</li>
<li>The injury-report hub is now captured with a clock time and a SHA-256 on every read, so a
week-to-week change is a difference between two dated captures rather than a recollection.</li>
</ul>

<h2>Pages</h2>
<ul class="tight">
<li><a href="game-books.html">Official Game Books</a> — one row per game: venue, roof and surface,
game-day weather, score, attendance, and the official link and hash of the document.</li>
<li><a href="availability.html">Availability graph</a> — expected starter, actual starter, the
replacement and the depth of the replacement.</li>
<li><a href="calibration.html">Designation calibration</a> — what each league designation meant
in practice, with <em>n</em> and an interval.</li>
<li><a href="snapshots.html">Snapshot ledger</a> — every official read with its URL, clock time
and SHA-256.</li>
<li><a href="requirements.html">Requirements</a> — the requirements this pack moves, the gate
that blocks each one and the number that would clear it.</li>
<li><a href="flagged.html">Flagged for review</a> — every irregularity and every cell the league
does not publish.</li>
</ul>
"""
    write(os.path.join(DOCS, "index.html"), page("Overview", "index.html", body, reads))


def build_game_books(games, games_by_week, reads) -> None:
    rows = []
    for game in sorted(games, key=lambda g: (week_of_game(g["game_slug"]), g["game_slug"])):
        away = club_of(game["away_team"]) or game["away_team"]
        home = club_of(game["home_team"]) or game["home_team"]
        roof = game["roof_status"]
        surface = game["surface"]
        roof_surface = " / ".join(x for x in (roof, surface) if x)
        weather = "; ".join(
            x for x in (
                game["weather_sky"],
                f"{game['temp_f']}&deg;F" if game["temp_f"] else "",
                f"{game['humidity_pct']}% humidity" if game["humidity_pct"] else "",
                game["wind"],
            ) if x
        )
        rows.append([
            f"W{week_of_game(game['game_slug'])}",
            f"{away} @ {home}",
            esc(game["date_et"]),
            esc(game["start_time"]),
            esc(game["stadium"]),
            esc(game["city"]),
            esc(roof_surface),
            weather,
            f"{esc(game['away_score'])}&ndash;{esc(game['home_score'])}",
            esc(game["attendance"]),
            link(game["gamebook_url"], "Game Book PDF"),
            f'<span class="mono">{esc(game["gamebook_sha256"][:16])}</span>',
            link(game["game_url"], "game centre"),
        ])
    body = f"""
<h1>Official NFL Game Books</h1>
<p class="lead">One row per game. Every value is read from that game's official Game Book, and
the last two columns are the document's own link and the SHA-256 of the bytes that were read, so
any reviewer can re-download the file and confirm the hash.</p>
{table(
    ["Week", "Match-up", "Date", "Kick-off", "Stadium", "City", "Roof / surface",
     "Game-day weather", "Score", "Attendance", "Document", "SHA-256 (first 16)", "Game centre"],
    rows,
)}
<div class="note">The Game Book's own copyright statement reads: &ldquo;This summary and
play-by-play is for the express purpose of assisting media in its coverage of the game; any other
use of this material is prohibited without the written permission of the National Football
League.&rdquo; This pack therefore records the URL and the hash of each document and publishes
the facts read from it; it does not redistribute the documents themselves. The licence question
is recorded on the <a href="flagged.html">Flagged for review</a> page.</div>
"""
    write(os.path.join(DOCS, "game-books.html"),
          page("Official Game Books", "game-books.html", body, reads))


def build_availability(availability, games, reads) -> None:
    rows = []
    for row in availability:
        if row["change_type"] == "held_over":
            continue
        rows.append([
            esc(row["week"]),
            esc(row["club"]),
            esc(row["opponent"]),
            esc(f"{row['unit']} {row['position']}"),
            esc(row["expected_player"]) or '<span class="mut">no prior Game Book</span>',
            esc(row["actual_player"]),
            esc(row["change_type"].replace("_", " ")),
            esc(row["replacement_string_lower_bound"]) or "",
            esc(row["unavailable_ahead"]),
            link(row["source_url"], "game centre"),
        ])
    changed = [r for r in availability if r["change_type"] != "held_over"]
    deeper = [r for r in changed if r["replacement_string_lower_bound"] not in ("", "1")]
    body = f"""
<h1>Availability graph &mdash; expected starter vs actual starter</h1>
<p class="lead">For every club, unit and position slot, the <em>expected</em> starter is the
same club's official starter at that slot in its previous game, read from the previous week's
official Game Book. The <em>actual</em> starter is the official Game Book of the game in hand.
Rows where the two agree are omitted here and kept in
<code>data/nfl_a119bb6d/availability_graph.csv</code>.</p>

<div class="cards">
<div class="card"><div class="k">Slots compared</div><div class="v">{len(availability)}</div><div class="s">across every Game Book read</div></div>
<div class="card"><div class="k">Starter changes</div><div class="v">{len(changed)}</div><div class="s">a different player started</div></div>
<div class="card"><div class="k">Depth 2 or deeper</div><div class="v">{len(deeper)}</div><div class="s">a lower bound from official data</div></div>
</div>

{table(
    ["Week", "Club", "Opponent", "Slot", "Expected starter", "Actual starter", "Change",
     "Replacement string (lower bound)", "Unavailable ahead", "Source"],
    rows,
)}

<div class="note"><strong>How the depth column is built, and why it is a lower bound.</strong> The
league publishes no depth chart and no snap counts. The only official evidence of who was ahead
of a replacement is the Game Book itself: if a club's previous starting player at a position is
listed as <em>Not Active</em> or <em>Did Not Play</em> in the game in hand, that player was
unavailable, so the replacement who started is at least one string deeper. The column
<em>unavailable ahead</em> counts exactly those players and the column
<em>replacement string (lower bound)</em> is that count plus one. A player who merely lost the
job is not counted, so the true string is never overstated.</div>
"""
    write(os.path.join(DOCS, "availability.html"),
          page("Availability graph", "availability.html", body, reads))


def build_calibration(calibration, injuries, reads) -> None:
    rows = []
    for row in calibration:
        rows.append([
            esc(row["designation"]),
            esc(row["n"]),
            esc(row["n_started"]),
            esc(row["n_played_off_bench"]),
            esc(row["n_did_not_play"]),
            esc(row["n_inactive"]),
            esc(row["n_not_in_game_book"]),
            esc(row["play_rate"]),
            f'{esc(row["play_rate_ci95_low"])} &ndash; {esc(row["play_rate_ci95_high"])}',
            link(row["source_url"], "injury report"),
        ])
    designations = sorted({r["game_status"] or "(none printed)" for r in injuries})
    body = f"""
<h1>What the league's designations actually mean</h1>
<p class="lead">The league's injury report prints three game-status designations —
<strong>Out</strong>, <strong>Doubtful</strong> and <strong>Questionable</strong> — and never
prints a percentage. This page measures each one against the official Game Book of the same
week: of the players the league designated, how many actually started, how many came off the
bench, how many were inactive and how many did not play.</p>

{table(
    ["Designation", "n", "Started", "Off the bench", "Did not play", "Inactive",
     "Not in Game Book", "Play rate", "95% interval", "Source"],
    rows,
    numeric={1, 2, 3, 4, 5, 6, 7},
)}

<div class="note">The play rate is the share of designated players the official Game Book shows
actually played, and the interval is a Wilson 95% interval on that share. <strong>n</strong> is
the number of designated players who could be joined to an official Game Book of the same week;
it is printed on every row so a rate is never read without its sample size.</div>

<h2>Designations the league printed in the captured report</h2>
<ul class="tight">
{''.join(f'<li>{esc(d)}</li>' for d in designations) or '<li>none captured</li>'}
</ul>
<div class="note">The sample is small because it is bounded by how many Game Books have been
read. Widening it needs the Game Books of the archived 2025 seasons, which are captured as a
hash and a URL but are not yet parsed. The gate and the number that would clear it are on the
<a href="requirements.html">Requirements</a> page.</div>
"""
    write(os.path.join(DOCS, "calibration.html"),
          page("Designation calibration", "calibration.html", body, reads))


def build_snapshots(capture_log, reads) -> None:
    rows = []
    for row in capture_log:
        rows.append([
            esc(row["kind"]),
            f'<a href="{esc(row["url"])}" rel="noopener">{esc(row["url"][:88])}</a>',
            esc(row["http_status"] or row["error"]),
            esc(row["bytes"]),
            f'<span class="mono">{esc(row["sha256"][:20])}</span>',
            esc(row["fetched_at_utc"]),
            esc(row["note"]),
        ])
    body = f"""
<h1>Point-in-time snapshot ledger</h1>
<p class="lead">Every official document this pack has read, with the URL it came from, the
clock time it was read and the SHA-256 of the bytes that came back. A capture that is replayed
produces the same hash; a capture that cannot be replayed is visible here.</p>
{table(
    ["Kind", "URL", "Status", "Bytes", "SHA-256 (first 20)", "Read (UTC)", "Note"], rows,
    numeric={3},
)}
<div class="good">The capture itself is a scheduled job: the workflow
<code>.github/workflows/nfl-a119bb6d-capture.yml</code> runs every Wednesday, Thursday and Friday
at 21:00 UTC to capture the injury-report hub and the weekly inactive-list article, and every
Monday at 05:00 UTC to capture the Game Books of the week just finished, the archived weekly
injury reports and the 32 club roster pages.</div>
"""
    write(os.path.join(DOCS, "snapshots.html"),
          page("Snapshot ledger", "snapshots.html", body, reads))


def build_requirements(games, availability, calibration, problems, reads) -> None:
    from src.nfl_a119bb6d.requirements import REQUIREMENTS  # noqa: E402

    rows = []
    for req in REQUIREMENTS:
        rows.append([
            esc(req["req_id"]),
            esc(req["requirement"]),
            f'<span class="pill p-{esc(req["state"])}">{esc(req["state"].replace("_", " "))}</span>',
            esc(req["what_is_now_true"]),
            esc(req["blocking_gate"]),
            esc(req["number_that_would_clear_it"]),
            link(req["source_url"], "official source"),
        ])
    body = f"""
<h1>Requirements this pack moves</h1>
<p class="lead">One row per requirement: what the requirement asked for, what is true now
because of the official Game Books, the gate that still blocks it and the number that would
clear that gate. Requirement identifiers are the ones used by the
<code>data/nfl_0ce967db/requirements.csv</code> register so the two can be read together.</p>
{table(
    ["ID", "Requirement", "State", "What is true now", "Blocking gate",
     "Number that would clear it", "Source"],
    rows,
)}
"""
    write(os.path.join(DOCS, "requirements.html"),
          page("Requirements", "requirements.html", body, reads))


def build_flagged(problems, games, reads) -> None:
    rows = [[esc(p)] for p in problems]
    body = f"""
<h1>Flagged for review</h1>
<p class="lead">Everything that could not be confirmed from an official source, and everything
that is structurally unavailable. None of it is filled in with a guess; each item names the gate
that would clear it.</p>
<h2>Capture and parse problems ({len(problems)})</h2>
{table(["Problem"], rows)}
<h2>Structural limits that are not bugs</h2>
<ul class="tight">
<li>The official Game Book contains <strong>no snap counts</strong> and no player-participation
table: a scan of a complete document finds 0 lines containing &ldquo;snap&rdquo; and 0 lines
containing &ldquo;participation&rdquo;. Any depth feature built on playing time therefore needs
a source the league does not currently publish in this document.</li>
<li>The league publishes <strong>no club depth chart</strong>:
<code>https://www.nfl.com/teams/houston-texans/roster/depth-chart/</code> returns the league's
own 404 page. The club's own chart is a club document and is labelled unofficial by the club.</li>
<li>The Game Book carries the league's copyright statement, quoted on the
<a href="game-books.html">Game Books</a> page. This pack records the URL and the hash and
publishes the facts; it does not redistribute the documents. A written position from NFL
Enterprises would close the licence question.</li>
<li>Depth of a replacement is published as a <strong>lower bound</strong>, counted only from
players the Game Book shows were unavailable. It is not a depth-chart rank and must not be used
as one.</li>
</ul>
"""
    write(os.path.join(DOCS, "flagged.html"),
          page("Flagged for review", "flagged.html", body, reads))


def build_sources(games, capture_log, reads) -> None:
    seen: dict[str, dict] = {}
    for row in capture_log:
        seen.setdefault(row["url"], row)
    rows = []
    for url, row in sorted(seen.items()):
        rows.append([
            esc(row["kind"]),
            f'<a href="{esc(url)}" rel="noopener">{esc(url[:92])}</a>',
            esc(row["http_status"]),
            f'<span class="mono">{esc(row["sha256"][:24])}</span>',
            esc(row["fetched_at_utc"]),
        ])
    body = f"""
<h1>Sources</h1>
<p class="lead">Every official page this pack read, by URL. All of them are on
<code>nfl.com</code>; no other host is used and no third-party source is mixed in.</p>
{table(["Kind", "URL", "Status", "SHA-256 (first 24)", "Read (UTC)"], rows, numeric={2})}
"""
    write(os.path.join(DOCS, "sources.html"),
          page("Sources", "sources.html", body, reads))


if __name__ == "__main__":
    raise SystemExit(main())
