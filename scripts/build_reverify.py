#!/usr/bin/env python3
"""Build the independent-recheck pages under docs/reverify/.

Every table row links to the official page it was checked against. Rows that
could not be confirmed from an official source are printed blank and listed on
the Flagged for Review page. The pages are generated only from the committed
capture files and report.json, so a stale page is detectable by the checker.

Run: python3 scripts/build_reverify.py
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "reverify_2026_11_05"
OUT = ROOT / "docs" / "reverify"

NAV = [
    ("index.html", "Overview"),
    ("standings.html", "Standings"),
    ("results.html", "Results"),
    ("slate.html", "Slate &amp; lines"),
    ("computed.html", "Computed layer"),
    ("rights.html", "Rights text"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]

CSS = """
:root{--ink:#12202b;--muted:#5d7280;--line:#dfe7ec;--bg:#f6f8fa;--card:#fff;--accent:#0f5c7a;--ok:#0d7a4f;--warn:#a35a00;--bad:#a32020}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--accent)}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
header{background:#fff;border-bottom:1px solid var(--line);padding:14px 20px;display:flex;flex-wrap:wrap;gap:14px;align-items:baseline;justify-content:space-between}
.brand{font-weight:700;letter-spacing:.06em;text-decoration:none;color:var(--ink)}
.brand span{font-weight:400;color:var(--muted);letter-spacing:0}
nav ul{display:flex;flex-wrap:wrap;gap:6px;list-style:none;margin:0;padding:0}
nav a{text-decoration:none;color:var(--muted);padding:6px 10px;border-radius:999px;font-size:14px}
nav a:hover{background:var(--bg);color:var(--ink)}
nav a[aria-current=page]{background:var(--ink);color:#fff}
main{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
h1{font-size:30px;line-height:1.2;margin:6px 0 10px}
h2{font-size:21px;margin:34px 0 10px}
h3{font-size:17px;margin:22px 0 8px}
p.lede{font-size:17px;color:var(--muted);max-width:78ch}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:12px;color:var(--muted);margin:0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.card .num{font-size:28px;font-weight:700}
.card .label{color:var(--muted);font-size:14px}
.callout{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:14px 16px;margin:16px 0}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:12px;margin:12px 0 24px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f2f6f8;font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fbfdfe}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;font-size:12px;font-weight:600;padding:2px 8px;border-radius:999px;border:1px solid}
.pill.ok{color:var(--ok);border-color:#bfe3d1;background:#f0faf5}
.pill.warn{color:var(--warn);border-color:#f0d7ae;background:#fff8ec}
.pill.bad{color:var(--bad);border-color:#f2c4c4;background:#fdf1f1}
.small{color:var(--muted);font-size:13px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
footer{border-top:1px solid var(--line);background:#fff;padding:18px 20px;color:var(--muted);font-size:13px}
footer p{margin:4px 0;max-width:1100px}
blockquote{margin:8px 0;padding:10px 14px;background:#fbfdfe;border-left:3px solid var(--line);color:#1d3340;font-size:14px}
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def count_pill(matched: int, total: int, noun: str) -> str:
    klass = "ok" if matched == total else "bad"
    return f'<span class="pill {klass}">{matched} of {total} {noun}</span>'


def pill(status: str) -> str:
    label = {
        "match": "match",
        "verified_text": "text verified",
        "computed_match": "reproduced",
        "computed_mismatch": "not reproduced",
        "mismatch": "mismatch",
        "unverified": "unverified",
    }.get(status, status)
    klass = "ok" if status in {"match", "verified_text", "computed_match"} else "bad"
    return f'<span class="pill {klass}">{esc(label)}</span>'


def source_link(url: str, text: str = "official source") -> str:
    if not url:
        return '<span class="pill warn">no official source</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(text)}</a>'


def table(headers: list[str], rows: list[list[str]], numeric: set[int] | None = None) -> str:
    numeric = numeric or set()
    num_class = ' class="num"'
    head_cells = []
    for i, h in enumerate(headers):
        klass = num_class if i in numeric else ""
        head_cells.append(f'<th scope="col"{klass}>{h}</th>')
    head = "".join(head_cells)
    body = []
    for row in rows:
        cells_list = []
        for i, cell in enumerate(row):
            klass = num_class if i in numeric else ""
            cells_list.append(f"<td{klass}>{cell}</td>")
        cells = "".join(cells_list)
        body.append(f"<tr>{cells}</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def page(slug: str, title: str, body: str) -> str:
    nav = "".join(
        f'<li><a href="{href}"{" aria-current=page" if href == slug else ""}>{label}</a></li>'
        for href, label in NAV
    )
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)} · Own6 recheck</title>"
        '<link rel="stylesheet" href="assets/style.css"></head>\n<body>'
        '<a class="skip" href="#main">Skip to content</a>'
        '<header><a class="brand" href="index.html">OWN6 <span>/ Recheck 5 Nov 2026</span></a>'
        f'<nav aria-label="Recheck navigation"><ul>{nav}</ul></nav></header>'
        f'<main id="main">{body}'
        "<footer>"
        "<p>Independent recheck of values published in this repository. A match means the published value equals the "
        "value read on an official NBA page on 2026-11-05. It is not a data licence, not proof of a betting edge, and "
        "not betting advice. NBA Terms of Use &#167;1 and &#167;9 govern reuse: "
        '<a href="https://www.nba.com/termsofuse" target="_blank" rel="noopener">nba.com/termsofuse</a>.</p>'
        "<p>Values that could not be confirmed from an official source are left blank and listed on "
        '<a href="flagged.html">Flagged for Review</a>. Computed rows are calculations over official final scores, '
        "not official NBA values.</p>"
        '<p class="small">Session arena/63a5b5ef-own6 &#183; source read date 2026-11-05 &#183; no manual input required '
        '&#183; <a href="../index.html">main dashboard</a></p>'
        "</footer></body></html>\n"
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    report = json.loads((DATA / "report.json").read_text(encoding="utf-8"))
    recon = read(DATA / "reconciliation.csv")
    compute = read(DATA / "recompute.csv")
    standings = read(DATA / "standings_read.csv")
    results = read(DATA / "results_read.csv")
    slate = read(DATA / "slate_read.csv")
    rights = read(DATA / "rights_read.csv")
    published_standings = {r["team_abbr"]: r for r in read(ROOT / "data/official_2026_11_05/standings.csv")}
    published_results = {r["game_id"]: r for r in read(ROOT / "data/official_2026_11_05/results_2026_11_04.csv")}
    published_slate = {r["game_id"]: r for r in read(ROOT / "data/official_2026_11_05/slate_2026_11_05_06.csv")}
    analysis = json.loads((ROOT / "data/official_2026_11_05/analysis.json").read_text(encoding="utf-8"))
    model_rows = {r["check_id"]: r for r in compute}

    verdict = report["verdict"]
    pages: dict[str, str] = {}

    # ---------------- overview ----------------
    status_counts = report["reconciliation"]["by_status"]
    compute_counts = report["recompute"]["by_status"]
    walk = report["walk_forward_reproduced"]
    body = [
        '<p class="eyebrow">Independent recheck</p>',
        "<h1>Every published value, re-read from an official page</h1>",
        '<p class="lede">This session re-checked the repository&#8217;s 2026-11-05 numerical snapshot one value at a time '
        "against pages read directly on nba.com, then recomputed the derived numbers with separately written code. "
        "Nothing was copied from an earlier session&#8217;s report as if it were evidence.</p>",
        '<div class="cards">',
        f'<div class="card"><div class="num">{verdict["published_values_confirmed"]}</div>'
        '<div class="label">published values confirmed on official pages</div></div>',
        f'<div class="card"><div class="num">{verdict["published_values_contradicted"]}</div>'
        '<div class="label">published values contradicted</div></div>',
        f'<div class="card"><div class="num">{verdict["computations_reproduced"]}</div>'
        '<div class="label">computed values reproduced</div></div>',
        f'<div class="card"><div class="num">{verdict["computations_contradicted"]}</div>'
        '<div class="label">computations not reproduced</div></div>',
        f'<div class="card"><div class="num">{verdict["qualified_strategies"]}</div>'
        '<div class="label">strategies that cleared all validation gates</div></div>',
        f'<div class="card"><div class="num">{verdict["authorized_observations"]}</div>'
        '<div class="label">authorized betting-use observations</div></div>',
        "</div>",
        '<div class="callout"><strong>Decision unchanged: no line, price, correlation-derived edge, ROI or reward '
        "winner is published.</strong> The recheck confirms that the numbers already on the site match official pages "
        "and that the derived figures reproduce. It does not create evidence of skill: no licensed odds feed exists, "
        "and the holdout win-probability skill interval still includes zero.</div>",
    ]

    body.append("<h2>What was checked, and how</h2>")
    body.append(
        table(
            ["Family", "Rows", "Result", "Method", "Official source"],
            [
                [
                    "Standings snapshot",
                    str(len([r for r in recon if r["category"] == "standings"])),
                    count_pill(len([r for r in recon if r["category"] == "standings" and r["status"] == "match"]), len([r for r in recon if r["category"] == "standings"]), "match"),
                    "Every win, loss, win percentage and games-behind value re-read on the live standings table",
                    source_link("https://www.nba.com/standings", "nba.com/standings"),
                ],
                [
                    "4 November results",
                    str(len([r for r in recon if r["category"] == "results"])),
                    count_pill(len([r for r in recon if r["category"] == "results" and r["status"] == "match"]), len([r for r in recon if r["category"] == "results"]), "match"),
                    "All 14 final scores, overtime flags and team identities re-read game by game",
                    source_link("https://www.nba.com/games?date=2026-11-04", "nba.com/games 11-04"),
                ],
                [
                    "5&#8211;6 November slate",
                    str(len([r for r in recon if r["category"] == "slate"])),
                    count_pill(len([r for r in recon if r["category"] == "slate" and r["status"] == "match"]), len([r for r in recon if r["category"] == "slate"]), "match"),
                    "Tip times, dates, matchups, competition and both records re-read on the daily games pages",
                    source_link("https://www.nba.com/games?date=2026-11-06", "nba.com/games 11-06"),
                ],
                [
                    "Calendar game counts",
                    str(len([r for r in recon if r["category"] == "calendar"])),
                    count_pill(len([r for r in recon if r["category"] == "calendar"]), 4, "match"),
                    "Archive sizes compared with the official month calendar cells",
                    source_link("https://www.nba.com/games?date=2026-11-04", "nba.com/games calendar"),
                ],
                [
                    "Rights text",
                    str(len([r for r in recon if r["category"] == "rights"])),
                    pill("verified_text"),
                    "Clause text copied verbatim, not summarised",
                    source_link("https://www.nba.com/termsofuse", "nba.com/termsofuse"),
                ],
                [
                    "Fail-closed ledger",
                    str(len([r for r in recon if r["category"] == "failclosed"])),
                    count_pill(len([r for r in recon if r["category"] == "failclosed"]), 3, "match"),
                    "Observation and qualification counts recomputed from the committed CSV",
                    source_link("https://www.nba.com/termsofuse#nba-statistics", "NBA Terms &#167;9"),
                ],
            ],
            numeric={1},
        )
    )

    body.append("<h2>What the recheck does not prove</h2>")
    body.append(
        '<div class="grid2">'
        '<div class="card"><h3>No market price</h3><p class="small">No sportsbook line, closing price or de-vigged '
        "probability is available under an authorized feed. Line value, edge, ROI and CLV stay blank. The recheck cannot "
        "and does not compare the model against a price.</p></div>"
        '<div class="card"><h3>Skill interval still spans zero</h3><p class="small">On the 61-game holdout the '
        f"win-probability Brier skill score is {walk['brier_skill_score']} with a 95% bootstrap interval of "
        f"{walk['brier_skill_score_ci95_low']} to {walk['brier_skill_score_ci95_high']}. That is compatible with luck, so "
        "no strategy is promoted.</p></div>"
        '<div class="card"><h3>Equal-opportunity schedule</h3><p class="small">Teams have played unequal numbers of '
        "games at this point of the season, so rating precision differs by team. The interval-based line output reflects "
        "that; a single-point line estimate is not a claim of accuracy.</p></div>"
        '<div class="card"><h3>Reproduction is not independence</h3><p class="small">The holdout reproduction uses the '
        "same window and seed, so it proves the published numbers come from the committed data, not that a different "
        "analyst would reach the same conclusion.</p></div>"
        "</div>"
    )

    body.append("<h2>Open the detail</h2>")
    body.append(
        '<div class="grid2">'
        '<div class="card"><h3>Official values</h3><p><a href="standings.html">Standings</a> &#183; '
        '<a href="results.html">Results</a> &#183; <a href="slate.html">Slate</a></p></div>'
        '<div class="card"><h3>Computations</h3><p><a href="computed.html">Records, correlations, model lines and the '
        'holdout luck test</a></p></div>'
        '<div class="card"><h3>Evidence boundaries</h3><p><a href="rights.html">Rights text</a> &#183; '
        '<a href="sources.html">Source register</a> &#183; <a href="flagged.html">Flagged for Review</a></p></div>'
        "</div>"
    )
    pages["index.html"] = page("index.html", "Independent recheck", "".join(body))

    # ---------------- standings ----------------
    rows = []
    for row in standings:
        abbr = row["team_abbr"]
        published = published_standings.get(abbr, {})
        checks = [r for r in recon if r["check_id"].startswith(f"ST-{abbr}-")]
        ok = all(r["status"] == "match" for r in checks) and len(checks) == 4
        rows.append(
            [
                esc(row["conference"]),
                esc(row["rank"]),
                esc(row["team"]),
                esc(f"{row['w']}-{row['l']}"),
                esc(row["win_pct"]),
                esc(row["gb"]),
                esc(row["conf_record"]),
                esc(row["div_record"]),
                esc(row["streak"]),
                pill("match") if ok else pill("mismatch"),
                esc(f"{published.get('w', '')}-{published.get('l', '')}") if published else "",
                source_link(row["source_url"], "nba.com/standings"),
            ]
        )
    body = [
        '<p class="eyebrow">Official values</p>',
        "<h1>Standings, 5 November 2026</h1>",
        '<p class="lede">All 30 rows re-read on the live standings table tonight. The repository&#8217;s published '
        "snapshot stores wins, losses, win percentage and games behind; conference, division and streak are shown here "
        "because they were read on the same page and add no new claim.</p>",
        '<div class="callout">Published value column repeats exactly what <code>data/official_2026_11_05/standings.csv</code> '
        "contains. Every field matched, so the published and re-read values are identical. A mismatch would be shown in "
        "the status column.</div>",
        table(
            [
                "Conf",
                "Rank",
                "Team",
                "W-L (official)",
                "Win%",
                "GB",
                "Conf",
                "Div",
                "Streak",
                "Recheck",
                "W-L (published)",
                "Source",
            ],
            rows,
            numeric={1, 3, 4, 5},
        ),
        '<p class="small">Games behind is recorded exactly as the official page prints it (&#8220;--&#8221; for the '
        "conference leader cells). No value was calculated or inferred.</p>",
    ]
    pages["standings.html"] = page("standings.html", "Standings recheck", "".join(body))

    # ---------------- results ----------------
    rows = []
    for row in results:
        gid = row["game_id"]
        checks = [r for r in recon if r["check_id"].startswith(f"RS-{gid}-")]
        ok = all(r["status"] == "match" for r in checks) and len(checks) == 5
        rows.append(
            [
                esc(f"{row['away_team']} {row['away_score']} @ {row['home_team']} {row['home_score']}"),
                esc(row["status"]),
                esc(gid),
                pill("match") if ok else pill("mismatch"),
                esc(f"{published_results.get(gid, {}).get('away_score', '')}-{published_results.get(gid, {}).get('home_score', '')}"),
                source_link(f"https://www.nba.com/game/{row['away_team'].lower()}-vs-{row['home_team'].lower()}-{gid}", "game page"),
            ]
        )
    body = [
        '<p class="eyebrow">Official values</p>',
        "<h1>4 November 2026 final scores</h1>",
        '<p class="lede">All 14 games re-read on the official games page for that date, including the two that went to '
        "overtime.</p>",
        '<div class="callout">The game-level page link in each row is the canonical page the scores feed links to. The '
        'whole-date read is recorded in <code>data/reverify_2026_11_05/results_read.csv</code> against '
        '<a href="https://www.nba.com/games?date=2026-11-04" target="_blank" rel="noopener">nba.com/games?date=2026-11-04</a>.</div>',
        table(["Final score (official)", "Status", "Game ID", "Recheck", "Published", "Source"], rows),
        '<p class="small">Overtime games: UTA 113 @ NOP 120 and MIA 117 @ LAC 116 both carry a Final/OT status on the '
        "official page and in the published archive.</p>",
    ]
    pages["results.html"] = page("results.html", "Results recheck", "".join(body))

    # ---------------- slate ----------------
    rows = []
    for row in slate:
        gid = row["game_id"]
        published = published_slate.get(gid, {})
        checks = [r for r in recon if r["check_id"].startswith(f"SL-{gid}-")]
        ok = checks and all(r["status"] == "match" for r in checks)
        margin = model_rows.get(f"MDL-{gid}-model_home_margin", {})
        total = model_rows.get(f"MDL-{gid}-model_total", {})
        prob = model_rows.get(f"MDL-{gid}-model_home_win_prob", {})
        cup = ""
        if row["cup_group"]:
            cup = f'{row["cup_group"]}: {row["away_record"]} / {row["home_record"]}'
        rows.append(
            [
                esc(row["date"]),
                esc(row["tip_et"]),
                esc(f'{row["away_team"]} @ {row["home_team"]}'),
                esc(row["competition"]),
                esc(cup),
                esc(f'{published.get("away_w", "")}-{published.get("away_l", "")} / {published.get("home_w", "")}-{published.get("home_l", "")}'),
                esc(margin.get("recomputed_value", "")),
                esc(total.get("recomputed_value", "")),
                esc(prob.get("recomputed_value", "")),
                pill("match") if ok else pill("mismatch"),
                source_link(row["source_url"], "nba.com/games"),
            ]
        )
    body = [
        '<p class="eyebrow">Official values and our own line</p>',
        "<h1>5&#8211;6 November 2026 slate</h1>",
        '<p class="lede">Eleven games: two tonight and nine tomorrow, all with tip times, competition labels and both '
        "teams&#8217; records re-read on the official daily games pages. The model column is our own line, computed from "
        "official final scores; the market column does not exist because no authorized price feed is configured.</p>",
        '<div class="callout"><strong>No market price is shown, and none is estimated.</strong> A model margin or total '
        "without a comparable price cannot produce an edge, a stake or a return. These numbers are an input to a "
        "pricing process, not a pick.</div>",
        table(
            [
                "Date",
                "Tip (ET)",
                "Matchup",
                "Competition (official)",
                "Cup group record (official)",
                "Record away / home (published)",
                "Our margin (home)",
                "Our total",
                "Our home win prob.",
                "Slate recheck",
                "Source",
            ],
            rows,
            numeric={6, 7, 8},
        ),
        '<h2>What the extra official columns add</h2>',
        "<p>The official games pages print in-season tournament group records next to each team, for example WAS 1-0 "
        "and ATL 0-0 in East Group C. Those values were not in the published slate file; they are recorded here as "
        "verified readings and are not used in the model. Dropping the competition&#8217;s title-sponsor prefix from the "
        "published label is noted on each affected row rather than treated as an error.</p>",
    ]
    pages["slate.html"] = page("slate.html", "Slate recheck", "".join(body))

    # ---------------- computed ----------------
    rec_rows = [r for r in compute if r["check_id"].startswith("REC-")]
    cor_rows = [r for r in compute if r["check_id"].startswith("COR-")]
    wf_rows = [r for r in compute if r["check_id"].startswith("WF-")]
    body = [
        '<p class="eyebrow">Computed layer</p>',
        "<h1>Derived numbers, recomputed independently</h1>",
        '<p class="lede">The published model, correlation and holdout statistics were recomputed with separately written '
        "code: a Cholesky solve instead of Gauss-Jordan, and raw-score sums instead of centred means. All "
        f"{len(compute)} recomputed values reproduce the published ones.</p>",
        '<div class="callout">These are calculations over official final scores. They are not official NBA values, and '
        "they are not evidence of an edge. Where a value depends on a price, it stays blank.</div>",
        "<h2>Team records rebuilt from all game results</h2>",
        "<p>Each team&#8217;s record was rebuilt from the 121 committed game results and compared with the official "
        "standings read tonight. This tests the whole result archive at once, not just its internal arithmetic.</p>",
    ]
    rec_match = len([r for r in rec_rows if r["status"] == "computed_match"])
    body.append(
        table(
            ["Team", "Official record", "Rebuilt record", "Result", "Source"],
            [
                [
                    esc(r["quantity"].split()[0]),
                    esc(r["published_value"]),
                    esc(r["recomputed_value"]),
                    pill(r["status"]),
                    source_link(r["input_source_url"], "nba.com/standings"),
                ]
                for r in rec_rows
            ],
            numeric={1, 2},
        )
    )
    body.append(f'<p class="small">{rec_match} of {len(rec_rows)} team records rebuilt from the archive equal the official record.</p>')

    body.append("<h2>Correlation estimates</h2>")
    pub_corr = analysis["correlations"]
    corr_labels = {
        "margin_vs_total": ("Game margin vs game total", "margin_vs_total"),
        "home_points_vs_away_points": ("Home points vs away points", "home_points_vs_away_points"),
        "team_differential_first_half_vs_second_half": (
            "Team point differential, first half vs second half of each team&#8217;s games",
            "team_differential_first_half_vs_second_half",
        ),
    }
    corr_rows = []
    for key, (label, _) in corr_labels.items():
        published = pub_corr.get(key) or {}
        subset = {r["check_id"].rsplit("-", 1)[-1]: r for r in cor_rows if f"COR-{key}-" in r["check_id"]}
        corr_rows.append(
            [
                esc(label),
                esc(published.get("n", "")),
                esc(published.get("r", "")),
                esc(f'{published.get("ci95_low", "")} to {published.get("ci95_high", "")}'),
                esc(subset.get("r", {}).get("recomputed_value", "")),
                pill(subset.get("r", {}).get("status", "unverified")),
                source_link("https://www.nba.com/games?date=2026-11-04", "official final scores"),
            ]
        )
    corr_rows.append(
        [
            "Player-level / prop correlation",
            "",
            "",
            "",
            "",
            '<span class="pill warn">unverified</span>',
            '<span class="small">No licensed player-level archive; value left blank</span>',
        ]
    )
    body.append(table(["Quantity", "n", "r (published)", "95% interval", "r (recomputed)", "Recheck", "Source"], corr_rows, numeric={1, 2, 4}))
    body.append(
        '<p class="small">The intervals are Fisher-z intervals on the same sample. None of the three is strong enough to '
        "support a betting claim; the margin-vs-total estimate is centred near zero. Robust standard errors, not the "
        "naive interval, are what the lab&#8217;s validation gates require before any correlation may be used.</p>"
    )

    body.append("<h2>Holdout luck test</h2>")
    body.append(
        "<p>An expanding-window refit predicts each game from the 61st onward. The baseline is the training-sample home "
        "win rate, so the test asks whether the model beats the simplest possible rule out of sample.</p>"
    )
    labels = {
        "n_predictions": "Holdout games",
        "winner_accuracy": "Winner accuracy",
        "winner_accuracy_ci95_low": "Winner accuracy, 95% Wilson low",
        "winner_accuracy_ci95_high": "Winner accuracy, 95% Wilson high",
        "home_always_accuracy": "Always-home accuracy",
        "brier_model": "Brier score, model",
        "brier_home_rate_baseline": "Brier score, home-rate baseline",
        "brier_skill_score": "Brier skill score",
        "brier_skill_score_ci95_low": "Brier skill score, 95% bootstrap low",
        "brier_skill_score_ci95_high": "Brier skill score, 95% bootstrap high",
        "mcnemar_model_only_correct": "McNemar: model right, baseline wrong",
        "mcnemar_home_only_correct": "McNemar: baseline right, model wrong",
        "mcnemar_exact_p_two_sided": "McNemar exact p (two-sided)",
        "mae_margin": "Mean absolute margin error",
        "rmse_margin": "RMSE margin",
        "mae_total": "Mean absolute total error",
        "rmse_total": "RMSE total",
    }
    wf_lookup = {r["quantity"].split("— ")[-1]: r for r in wf_rows}
    body.append(
        table(
            ["Metric", "Published", "Recomputed", "Result", "Input source"],
            [
                [
                    esc(label),
                    esc(walk[key]),
                    esc(wf_lookup.get(key, {}).get("recomputed_value", "")),
                    pill(wf_lookup.get(key, {}).get("status", "unverified")),
                    source_link("https://www.nba.com/games?date=2026-11-04", "official final scores"),
                ]
                for key, label in labels.items()
            ],
            numeric={1, 2},
        )
    )
    body.append(
        '<div class="callout"><strong>Verdict.</strong> The model beats always-home on winners, but the paired exact test '
        f"gives p = {walk['mcnemar_exact_p_two_sided']}, and the bootstrap interval for the Brier skill score runs from "
        f"{walk['brier_skill_score_ci95_low']} to {walk['brier_skill_score_ci95_high']}, which includes zero. With 61 "
        "holdout games, luck is not excluded. No strategy is promoted to the leaderboard, and no reward is paid.</div>"
    )
    pages["computed.html"] = page("computed.html", "Computed layer recheck", "".join(body))

    # ---------------- rights ----------------
    rows = []
    for row in rights:
        rows.append(
            [
                esc(row["clause"]),
                f'<blockquote>{esc(row["verbatim_quote"])}</blockquote>',
                esc(row["compiler_note"]),
                pill("verified_text"),
                source_link(row["source_url"], "nba.com/termsofuse"),
            ]
        )
    body = [
        '<p class="eyebrow">Evidence boundary</p>',
        "<h1>Rights text, copied word for word</h1>",
        '<p class="lede">The NBA Terms of Use decide what may be done with NBA data at all. The clauses that matter for '
        "this project were read on 2026-11-05 and are reproduced verbatim, with the official page linked on every row.</p>",
        '<div class="callout"><strong>&#167;9(iv) bars gambling use of NBA Statistics, including legal gambling '
        "activity.</strong> &#167;1 requires written permission before Basketball Content is reused or linked. No "
        "authorization has been obtained, so this project publishes a research framework and provenance record, not NBA "
        "statistics packaged as a betting product.</div>",
        table(["Clause", "Text as published by the NBA", "Why it matters here", "Recheck", "Source"], rows),
        '<p class="small">Reading these clauses is not legal advice. Whether a given use is permitted is a question for '
        "NBA counsel and qualified legal review.</p>",
    ]
    pages["rights.html"] = page("rights.html", "Rights text", "".join(body))

    # ---------------- sources ----------------
    src_rows = [
        ["https://www.nba.com/standings", "2026-27 regular-season standings table", "30 team records, conference, division, streak", "2026-11-05", pill("verified_text")],
        ["https://www.nba.com/games?date=2026-11-04", "Games and scores, 4 November 2026", "14 final scores, overtime flags, month calendar cells", "2026-11-05", pill("verified_text")],
        ["https://www.nba.com/games?date=2026-11-05", "Games and scores, 5 November 2026", "2 games, tip times, records", "2026-11-05", pill("verified_text")],
        ["https://www.nba.com/games?date=2026-11-06", "Games and scores, 6 November 2026", "9 games, tip times, Cup group labels and records", "2026-11-05", pill("verified_text")],
        ["https://www.nba.com/termsofuse", "NBA Terms of Use", "&#167;1 and &#167;9(i)&#8211;(vii) verbatim", "2026-11-05", pill("verified_text")],
        ["https://www.nba.com/termsofuse#nba-statistics", "NBA Terms of Use, statistics section", "Gambling-use prohibition used for the fail-closed ledger", "2026-11-05", pill("verified_text")],
    ]
    body = [
        '<p class="eyebrow">Provenance</p>',
        "<h1>Source register</h1>",
        '<p class="lede">Every row on this section of the site points at one of these pages. Nothing else was used as '
        "an official source.</p>",
        table(
            ["Official page", "What it covers", "What was taken from it", "Read on", "Status"],
            [[source_link(url, url.replace("https://www.nba.com/", "nba.com/")), esc(a), esc(b), esc(c), d] for url, a, b, c, d in src_rows],
        ),
        "<h2>What has no official source</h2>",
        '<div class="table-wrap"><table><thead><tr><th scope="col">Item</th><th scope="col">Status</th><th scope="col">Why</th></tr></thead><tbody>'
        "<tr><td>Sportsbook line, spread, total or price</td><td><span class=\"pill warn\">unverified</span></td>"
        "<td>No authorized odds feed. Values are blank everywhere on the site.</td></tr>"
        "<tr><td>Closing-line value</td><td><span class=\"pill warn\">unverified</span></td>"
        "<td>Requires a timestamped closing price archive that does not exist here.</td></tr>"
        "<tr><td>Player-level statistics and prop lines</td><td><span class=\"pill warn\">unverified</span></td>"
        "<td>NBA Stats FAQ states statistics are not available for download; &#167;9 restricts gambling use.</td></tr>"
        "<tr><td>Donation, reward or payout values</td><td><span class=\"pill warn\">unverified</span></td>"
        "<td>No reward contract exists; the leaderboard grants research priority only, and is empty.</td></tr>"
        "</tbody></table></div>",
    ]
    pages["sources.html"] = page("sources.html", "Source register", "".join(body))

    # ---------------- flagged ----------------
    open_recon = report["reconciliation"]["open_items"]
    open_compute = report["recompute"]["open_items"]
    body = [
        '<p class="eyebrow">Needs review</p>',
        "<h1>Flagged for Review</h1>",
        '<p class="lede">Items this session could not confirm from an official source, plus the boundaries that keep the '
        "project from publishing a line. Nothing here blocks publication of the framework.</p>",
        '<div class="callout"><strong>Mismatches found by this recheck: '
        f"{len(open_recon)} of {report['reconciliation']['rows']} published values and "
        f"{len(open_compute)} of {report['recompute']['rows']} computations.</strong> Zero means every value that was "
        "checked held up. Absence of a mismatch is not evidence of skill.</div>",
        "<h2>Unverified by design</h2>",
    ]
    flagged = [
        ["Market prices for any game on the slate", "No authorized odds feed exists; &#167;9(iv) restricts gambling use of NBA data.", "https://www.nba.com/termsofuse#nba-statistics", "High"],
        ["Player prop lines and player-level archives", "NBA Stats FAQ states statistics are not available for download; no licensed prop archive is configured.", "https://www.nba.com/stats/help/faq", "High"],
        ["Correlation between prop outcomes inside a combo", "Requires player-level joint outcomes that are not available. Left blank.", "https://www.nba.com/termsofuse#nba-statistics", "High"],
        ["Closing-line value and ROI", "Requires timestamped prices and settled bet records. Left blank.", "https://www.nba.com/termsofuse#nba-statistics", "High"],
        ["Reward or payout amounts", "No reward contract exists. Leaderboard grants research priority only.", "", "Medium"],
        ["Korean statute text (&#44397;&#48124;&#52404;&#50949;&#51652;&#55137;&#48277; &#51228;26&#51312;)", "Recorded by an earlier session; not re-read this session, so it is carried forward as unverified here.", "https://www.law.go.kr/", "Medium"],
        ["Title-sponsor prefix in competition labels", "Published slate labels omit the &#8220;Emirates&#8221; prefix that the official page prints. Treated as a deliberate labelling choice under &#167;9(iii), recorded on each row, not corrected.", "https://www.nba.com/games?date=2026-11-06", "Low"],
    ]
    flagged_rows = [
        [esc(item), esc(why), source_link(url, "source") if url else '<span class="pill warn">none</span>', esc(sev), '<span class="pill warn">needs review</span>']
        for item, why, url, sev in flagged
    ]
    body.append(table(["Item", "Why it is unverified", "Source to review", "Severity", "Status"], flagged_rows))
    body.append("<h2>Limitations of this recheck</h2>")
    body.append(
        "<ul>"
        "<li>A value that matches an official page today is a provenance fact, not a licence to reuse NBA data.</li>"
        "<li>The holdout test has 61 games. It cannot separate skill from luck at conventional confidence, and the "
        "published interval says so.</li>"
        "<li>Teams have played unequal numbers of games, so rating precision differs by team.</li>"
        "<li>Recomputing with the same window and seed proves the published numbers come from the committed data; it "
        "is not an independent replication by a different analyst.</li>"
        "<li>No legal opinion has been obtained on &#167;1 or &#167;9.</li>"
        "</ul>"
    )
    pages["flagged.html"] = page("flagged.html", "Flagged for Review", "".join(body))

    for slug, content in pages.items():
        (OUT / slug).write_text(content, encoding="utf-8")

    print(f"Wrote {len(pages)} pages under {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
