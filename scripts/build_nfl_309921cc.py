#!/usr/bin/env python3
"""Build the NFL-309921cc dashboard (CSVs + zero-input GitHub Pages site).

Usage
-----
    python3 scripts/build_nfl_309921cc.py            # write CSVs and HTML
    python3 scripts/build_nfl_309921cc.py --check    # also run the verifier
"""

from __future__ import annotations

import argparse
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_309921cc import dataset as D  # noqa: E402
from nfl_309921cc import verified as V  # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-309921cc")
DATA = D.DATA_DIR
CAPTURE = V.CAPTURE_DATE_UTC

OFFICIAL_HOSTS = (
    "www.nfl.com",
    "operations.nfl.com",
    "support.nfl.com",
    "www.patriots.com",
    "www.detroitlions.com",
    "www.itl.nist.gov",
)

CSS = """
:root{--bg:#0e1117;--panel:#161b22;--panel2:#1c2430;--line:#2a3441;--ink:#e6edf3;
--muted:#9aa7b4;--accent:#4ba3f5;--good:#3fb950;--warn:#d29922;--bad:#f85149;
--empty:#6e7681}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
nav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:10px 16px;
background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
nav .brand{font-weight:700;letter-spacing:.04em;margin-right:10px}
nav a{padding:5px 9px;border-radius:6px;font-size:14px;color:var(--ink);
background:var(--panel2);border:1px solid var(--line)}
nav a:hover{background:#243040;text-decoration:none}
main{max-width:1180px;margin:0 auto;padding:22px 16px 60px}
h1{font-size:28px;line-height:1.2;margin:6px 0 10px}
h2{font-size:21px;margin:34px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:17px;margin:22px 0 6px}
p{margin:8px 0}
.eyebrow{color:var(--accent);font-size:12px;letter-spacing:.16em;text-transform:uppercase;margin:0 0 4px}
.lede{color:var(--muted);max-width:80ch}
.hero{background:linear-gradient(180deg,#16202c,#11161d);border:1px solid var(--line);
border-radius:14px;padding:24px;margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:16px 0 4px}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:14px;color:var(--ink)}
.card:hover{border-color:var(--accent);text-decoration:none}
.card .k{font-size:26px;font-weight:700;display:block}
.card .l{color:var(--muted);font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
.tile b{display:block;font-size:22px}
.tile span{color:var(--muted);font-size:12px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:10px 0 18px}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--panel2);position:sticky;top:52px;font-size:12px;letter-spacing:.03em;
text-transform:uppercase;color:var(--muted);white-space:nowrap}
tbody tr:hover{background:#1b2430}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.empty:before{content:"blank";color:var(--empty);font-style:italic;font-size:12px}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;
border:1px solid var(--line);background:#1b2430;white-space:nowrap}
.p-ok{color:var(--good);border-color:#21402a;background:#122318}
.p-warn{color:var(--warn);border-color:#42390f;background:#241f0c}
.p-bad{color:var(--bad);border-color:#4a1d1a;background:#26120f}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:8px;padding:10px 12px;color:var(--muted);font-size:13.5px;margin:10px 0 18px}
.note strong{color:var(--ink)}
footer{border-top:1px solid var(--line);margin-top:40px;padding:16px;color:var(--muted);font-size:13px}
.kv{display:grid;grid-template-columns:180px 1fr;gap:4px 12px;font-size:14px;
background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;margin:10px 0}
.kv dt{color:var(--muted)}
.kv dd{margin:0}
details{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0}
summary{cursor:pointer;font-weight:600}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url: str, label: str | None = None) -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label or "source ↗")}</a>'


def pill(text: str) -> str:
    t = (text or "").lower()
    cls = "p-ok" if ("verified" in t or "measured" in t or "open" in t or "resolved" in t) \
        else "p-bad" if ("blocked" in t or "unresolved" in t or "high" in t) \
        else "p-warn"
    return f'<span class="pill {cls}">{esc(text)}</span>'


def table(headers, rows, source_col_last=True, num_cols=(), empty_mark=True):
    """Render a table. A cell that is blank is rendered with class 'empty'."""
    out = ['<div class="wrap"><table><thead><tr>']
    for h in headers:
        out.append(f"<th scope='col'>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i, h in enumerate(headers):
            v = r.get(h, "")
            cls = []
            if h in num_cols:
                cls.append("num")
            if v == "" or v is None:
                if empty_mark:
                    cls.append("empty")
                out.append(f"<td class='{' '.join(cls)}' aria-label='blank, unverified'></td>")
                continue
            sv = str(v)
            if sv.startswith("http://") or sv.startswith("https://"):
                cell = link(sv)
            else:
                cell = esc(sv)
            out.append(f"<td class='{' '.join(cls)}'>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def pretty(h: str) -> str:
    return h.replace("_", " ").strip()


def cols(fields):
    return [(f, pretty(f)) for f in fields]


def render_table(fields, rows, num_cols=(), note=None):
    """Table with human headers; rows keyed by machine field names."""
    mapping = cols(fields)
    out = ['<div class="wrap"><table><thead><tr>']
    for _f, label in mapping:
        out.append(f"<th scope='col'>{esc(label)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for f, _label in mapping:
            v = r.get(f, "")
            cls = ["num"] if f in num_cols else []
            if v == "" or v is None:
                cls.append("empty")
                out.append(f"<td class='{' '.join(cls)}' aria-label='blank, unverified'></td>")
                continue
            sv = str(v)
            if sv.startswith("https://") or sv.startswith("http://"):
                cell = link(sv)
            elif f in ("status", "verification_status", "review_status", "severity",
                       "value_kind", "score_kind", "qualified", "priority"):
                cell = pill(sv)
            else:
                cell = esc(sv)
            out.append(f"<td class='{' '.join(cls)}'>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    if note:
        out.insert(0, f'<p class="note">{note}</p>')
    return "".join(out)


NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("decision-ledger.html", "Decision ledger"),
    ("suggestions.html", "Suggestions"),
    ("standings.html", "Standings"),
    ("slate.html", "Week 10 slate"),
    ("injuries.html", "Injuries"),
    ("depth.html", "Depth & deficiency"),
    ("lines.html", "Originated lines"),
    ("strategies.html", "Strategies"),
    ("validation.html", "Validation gates"),
    ("correlations.html", "Correlations & luck"),
    ("leaderboard.html", "Leaderboard"),
    ("repo-review.html", "Repo review"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]


def page(title, body, active, subtitle=""):
    nav = "".join(
        f'<a href="{u}"{" aria-current=page" if u == active else ""}>{esc(t)}</a>'
        for u, t in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Own6 NFL decision, line-origination and depth-deficiency dashboard — every row source-linked, blanks flagged.">
<title>{esc(title)} · Own6 NFL 309921cc</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<nav aria-label="Primary navigation"><span class="brand">OWN6 / NFL 309921CC</span>{nav}</nav>
<main>
<header class="hero">
<p class="eyebrow">NFL · WEEK 10 2026 · CAPTURED {esc(CAPTURE)}</p>
<h1>{esc(title)}</h1>
<p class="lede">{subtitle}</p>
</header>
{body}
</main>
<footer>Research only. No wagers, no picks service, no profitability claim, and no monetary reward.
Statistical validation reduces uncertainty; it cannot remove luck. Content is published for individual
non-commercial informational review under the
<a href="https://www.nfl.com/legal/terms/">NFL.com Terms and Conditions</a>; systematic retrieval to
compile a database is prohibited without the NFL's express prior written consent.
Blank cells are blank because no official source in this pack supplies the value — see
<a href="flagged.html">Flagged for Review</a>.</footer>
</body></html>
"""


# --------------------------------------------------------------------------
# page bodies
# --------------------------------------------------------------------------
def build_all():
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fh:
        fh.write("")

    # ---- CSVs ----
    standings = D.standings_rows()
    slate = D.slate_rows()
    byes = D.bye_rows()
    injuries = D.injury_rows()
    load = D.injury_load_rows()
    charts = D.depth_chart_rows()
    deficiency = D.depth_deficiency_rows()
    unlisted = D.unlisted_designated_rows()
    decisions = D.decision_rows()
    suggestions = D.suggestion_rows()
    strategies = D.strategy_rows()
    gates = D.gate_rows()
    corrs, luck, luck_summary, = D.correlation_rows(), *D.luck_rows()
    lines, linecheck = D.originated_line_rows()
    tiers, entries = D.leaderboard_rows()
    findings = D.repo_finding_rows()
    sources = D.source_rows()
    flags = D.flag_rows()

    written = []
    written.append(D.write_csv("sources.csv", D.SOURCE_FIELDS, sources))
    written.append(D.write_csv("repo_findings.csv", D.REPO_FINDING_FIELDS, findings))
    written.append(D.write_csv("standings_2026_w10.csv", D.STANDINGS_FIELDS, standings))
    written.append(D.write_csv("week10_slate.csv", D.SLATE_FIELDS, slate))
    written.append(D.write_csv("week10_byes.csv", D.BYE_FIELDS, byes))
    written.append(D.write_csv("week10_injuries.csv", D.INJURY_FIELDS, injuries))
    written.append(D.write_csv("week10_injury_load.csv", D.INJURY_LOAD_FIELDS, load))
    written.append(D.write_csv("depth_charts.csv", D.DEPTH_CHART_FIELDS, charts))
    written.append(D.write_csv("depth_deficiency.csv", D.DEPTH_DEFICIENCY_FIELDS, deficiency))
    written.append(D.write_csv("depth_unlisted_designations.csv", D.UNLISTED_FIELDS, unlisted))
    written.append(D.write_csv("decision_ledger.csv", D.DECISION_FIELDS, decisions))
    written.append(D.write_csv("suggestions.csv", D.SUGGESTION_FIELDS, suggestions))
    written.append(D.write_csv("strategies.csv", D.STRATEGY_FIELDS, strategies))
    written.append(D.write_csv("validation_gates.csv", D.GATE_FIELDS, gates))
    written.append(D.write_csv("correlations.csv", D.CORRELATION_FIELDS, corrs))
    written.append(D.write_csv("luck_index.csv", D.LUCK_FIELDS, luck))
    written.append(D.write_csv("originated_lines.csv", D.ORIGINATED_FIELDS, lines))
    written.append(D.write_csv("leaderboard_tiers.csv", D.LEADERBOARD_TIER_FIELDS, tiers))
    written.append(D.write_csv("leaderboard_entries.csv", D.LEADERBOARD_ENTRY_FIELDS, entries))
    written.append(D.write_csv("flagged.csv", D.FLAG_FIELDS, flags))

    # ---- pages ----
    pages = {}

    # Overview -------------------------------------------------------------
    tiles = [
        ("32", "clubs verified"),
        ("14", "Week 10 games"),
        (str(len(injuries)), "injury-report rows"),
        ("8", "measured correlations"),
        ("10", "preregistered strategies"),
        ("0", "qualified strategies"),
        ("12", "validation gates"),
        ("16", "items flagged"),
    ]
    tl = "".join(f'<div class="tile"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in tiles)
    cards = [
        ("decision-ledger.html", "Decision ledger", "16 questions: what we have, what we lack, and how to discover it."),
        ("suggestions.html", "Suggestions", "14 reviewable improvements with option paths — nothing is auto-applied."),
        ("lines.html", "Originated lines", "Our own fair spread and total for 13 scheduled games, from verified inputs."),
        ("strategies.html", "Strategies", "Singles, parlays and same-game prop combos, each preregistered."),
        ("validation.html", "Validation gates", "12 gates; 4 open, 8 blocked on missing licensed data."),
        ("correlations.html", "Correlations & luck", "8 correlations measured from official standings, plus a 32-row luck index."),
        ("depth.html", "Depth & deficiency", "1st-to-4th string charts mapped onto official injury designations."),
        ("injuries.html", "Injuries", f"All {len(injuries)} official Week 10 rows, plus a per-club load table."),
        ("leaderboard.html", "Leaderboard", "Four non-monetary tiers; no entry has qualified."),
        ("repo-review.html", "Repo review", "14 irregularities found reviewing this repository line by line."),
        ("sources.html", "Sources", "11 official pages read directly on 2026-11-13, with verbatim excerpts."),
        ("flagged.html", "Flagged for review", "16 blank or unresolved items, each with its source."),
    ]
    cl = "".join(
        f'<a class="card" href="{u}"><span class="k">{esc(t.split()[0])}</span>'
        f'<strong>{esc(t)}</strong><br><span class="l">{esc(d)}</span></a>'
        for u, t, d in cards)
    pages["index.html"] = page(
        "NFL decision, origination and depth command center",
        f'<div class="tiles">{tl}</div>'
        '<p class="note"><strong>What this pack is.</strong> A decision-support dashboard built only from '
        'pages read directly on official NFL and club sites on 2026-11-13. Where a value has no official '
        'source it is left blank and flagged, never filled in. The eight correlations and the 32-row luck '
        'index on the Correlations page are <strong>measured</strong> from the verified standings table; '
        'everything else that looks like a number is either a verified count or a labelled model output.</p>'
        f'<div class="cards">{cl}</div>'
        '<h2>Where the gates stand</h2>'
        '<p>Gates are the rules a strategy must clear before it can be called skill-based. Four are open '
        '(they depend only on how the pack is built); eight are blocked because a licensed data input does '
        'not exist in this repository.</p>'
        + render_table(
            ["gate_id", "gate", "status", "blocking_missing_input", "official_or_method_reference"],
            gates, num_cols=("gate_id",))
        + '<h2>The five decisions that matter most</h2>'
        + render_table(
            ["question_id", "decision_area", "question", "information_we_lack", "priority", "status",
             "official_source_url"],
            [r for r in decisions if r["priority"] == "High"][:5],
            num_cols=("question_id",)),
        "A clean, source-linked dashboard for originating NFL lines, gating strategies against luck, and "
        "tracking starter-versus-backup deficiencies on both offense and defense.")

    summary_rows = [
        {"dataset": "standings_2026_w10.csv", "rows": len(standings),
         "row_kind": "Official table row, read directly",
         "status": "verified", "official_source_url": "https://www.nfl.com/standings/"},
        {"dataset": "week10_slate.csv", "rows": len(slate),
         "row_kind": "Official schedule row, read directly",
         "status": "verified", "official_source_url": "https://www.nfl.com/schedules"},
        {"dataset": "week10_byes.csv", "rows": len(byes),
         "row_kind": "Official schedule row, read directly",
         "status": "verified", "official_source_url": "https://www.nfl.com/schedules"},
        {"dataset": "week10_injuries.csv", "rows": len(injuries),
         "row_kind": "Official injury-report row, read directly",
         "status": "verified", "official_source_url": "https://www.nfl.com/injuries/"},
        {"dataset": "week10_injury_load.csv", "rows": len(load),
         "row_kind": "Count derived by reading every injury row",
         "status": "verified_count", "official_source_url": "https://www.nfl.com/injuries/"},
        {"dataset": "depth_charts.csv", "rows": len(charts),
         "row_kind": "Club depth chart, labelled unofficial by the club",
         "status": "verified_direct_unofficial_source",
         "official_source_url": "https://www.patriots.com/team/depth-chart"},
        {"dataset": "depth_deficiency.csv", "rows": len(deficiency),
         "row_kind": "Derived mapping of depth chart onto injury designations",
         "status": "model_output", "official_source_url": "https://www.nfl.com/injuries/"},
        {"dataset": "correlations.csv", "rows": len(corrs),
         "row_kind": "Statistic computed here from the verified standings table",
         "status": "measured_from_verified_official_data",
         "official_source_url": "https://www.nfl.com/standings/"},
        {"dataset": "luck_index.csv", "rows": len(luck),
         "row_kind": "Regression residual computed here from the verified standings table",
         "status": "measured_from_verified_official_data",
         "official_source_url": "https://www.nfl.com/standings/"},
        {"dataset": "originated_lines.csv", "rows": len(lines),
         "row_kind": "Our own fair price, from verified inputs",
         "status": "model_output", "official_source_url": "https://www.nfl.com/standings/"},
        {"dataset": "strategies.csv", "rows": len(strategies),
         "row_kind": "Preregistered hypothesis, 0 graded selections",
         "status": "preregistered_not_qualified",
         "official_source_url": "https://www.nfl.com/schedules"},
        {"dataset": "validation_gates.csv", "rows": len(gates),
         "row_kind": "Gate definition",
         "status": "open", "official_source_url": "https://www.nfl.com/legal/terms/"},
        {"dataset": "decision_ledger.csv", "rows": len(decisions),
         "row_kind": "Unresolved decision, with a discovery suggestion",
         "status": "unresolved", "official_source_url": "https://www.nfl.com/legal/terms/"},
        {"dataset": "suggestions.csv", "rows": len(suggestions),
         "row_kind": "Reviewable improvement, nothing implemented",
         "status": "pending_human_choice",
         "official_source_url": "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"},
        {"dataset": "repo_findings.csv", "rows": len(findings),
         "row_kind": "Irregularity found reviewing this repository",
         "status": "needs review",
         "official_source_url": "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"},
        {"dataset": "flagged.csv", "rows": len(flags),
         "row_kind": "Blank or unresolved item",
         "status": "needs review", "official_source_url": "https://www.nfl.com/legal/terms/"},
        {"dataset": "sources.csv", "rows": len(sources),
         "row_kind": "Official page read directly, with a verbatim excerpt",
         "status": "verified_direct", "official_source_url": "https://www.nfl.com/legal/terms/"},
    ]

    # Executive summary ----------------------------------------------------
    pages["executive-summary.html"] = page(
        "Executive summary",
        '<h2>The short version</h2>'
        '<p class="note">This pack can be summarised in one sentence: <strong>the framework, the measured '
        'league-level statistics and the verified Week 10 picture are real; every betting-performance '
        'number is blank and stays blank until licensed data exists.</strong></p>'
        '<h3>What is verified</h3>'
        '<ul><li>All 32 club standings rows, read from '
        f'{link("https://www.nfl.com/standings/", "nfl.com/standings")} on {CAPTURE}, with the twelve '
        'columns that the page\'s own legend defines.</li>'
        '<li>The 14-game Week 10 slate with kickoff times, networks, pre-game records and canonical game '
        f'URLs, from {link("https://www.nfl.com/schedules", "nfl.com/schedules")}, plus 4 bye teams.</li>'
        f'<li>All {len(injuries)} rows of the official Week 10 injury report from '
        f'{link("https://www.nfl.com/injuries/", "nfl.com/injuries")}, with the five columns the page defines.</li>'
        '<li>Two club depth charts (Patriots, Lions) giving 1st-to-4th string ordering for offense and '
        'defense — with both clubs\' own "unofficial" disclaimer carried onto every row.</li>'
        '<li>Eight correlations and a 32-row luck index, computed here from the verified standings table.</li></ul>'
        '<h3>What is deliberately blank</h3>'
        '<ul><li>Every market price, closing line and closing-line value (no licensed odds archive).</li>'
        '<li>Every moneyline probability (needs a victory-margin distribution that no official page supplies).</li>'
        '<li>Every measured dependence between two betting legs (needs graded paired outcomes).</li>'
        '<li>Every strategy performance statistic: the ledger holds 0 graded selections.</li></ul>'
        '<h3>The four findings that change what you should do next</h3>'
        '<ol><li><strong>Rights is the first question, not the last.</strong> The NFL terms prohibit '
        'systematic retrieval to compile a database; this repository is, by construction, a compiled '
        'database of official tables. Nothing else should grow until that is answered.</li>'
        '<li><strong>71 citations point at a dead URL.</strong> '
        f'{link("https://www.nfl.com/official-nfl-rules/", "nfl.com/official-nfl-rules")} returned the '
        'official NFL 404 page on 2026-11-13, and 20+ files in this repository — including live published '
        'pages — cite it as a source.</li>'
        '<li><strong>The standings lag a completed game.</strong> Thursday\'s Commanders 24–21 win over '
        'the Giants is published as final, but the standings table still shows both clubs with pre-game '
        'records. Any model mixing the two is internally inconsistent.</li>'
        '<li><strong>Four NFL packs now compete.</strong> A reviewer can easily act on the older one. '
        'Nothing is deleted here; the fix is a canonical pointer.</li></ol>'
        + '<h2>What is published, row by row</h2>'
        + render_table(
            ["dataset", "rows", "row_kind", "status", "official_source_url"],
            summary_rows, num_cols=("rows",))
        + '<h3>Originated lines</h3>'
        '<p>Thirteen scheduled Week 10 games carry our own fair spread and total, computed only from '
        'verified points-for and points-against per game. The model\'s mean total is '
        f'<strong>{esc(linecheck["model_mean_total"])}</strong> against the league\'s own '
        f'<strong>{esc(linecheck["league_points_per_game_both_teams"])}</strong> points per game computed '
        f'from the standings — a difference of {esc(linecheck["model_minus_league_total"])} points, which '
        'is the model\'s self-consistency check. The one game already final is not modelled.</p>'
        '<h3>Luck removal, demonstrated</h3>'
        f'<p>Regressing win percentage on net points per game across the 32 official rows gives R² = '
        f'<strong>{esc(luck_summary["r2"])}</strong> (slope {esc(luck_summary["slope"])} per net point per '
        f'game, p = {esc(luck_summary["p_slope"])}). The residual is the part of a team\'s record that its '
        'scoring does not explain — the same estimator is what gate G10 applies to a strategy, but on '
        'slate-clustered data, and it requires the interval to exclude zero before any reward.</p>',
        "Important details, what is verified, what is blank, and what to do next.")

    # Decision ledger ------------------------------------------------------
    pages["decision-ledger.html"] = page(
        "Decision ledger",
        '<p class="note">Each row is one decision that cannot reasonably be made yet. '
        '<strong>Information we have</strong> is what an official page says. '
        '<strong>Information we lack</strong> is what is missing. '
        '<strong>Suggested way to discover</strong> is a concrete action, not a guess.</p>',
        ) if False else page(
        "Decision ledger",
        '<p class="note">Each row is one decision that cannot reasonably be made yet. '
        '<strong>Information we have</strong> is what an official page says. '
        '<strong>Information we lack</strong> is what is missing. '
        '<strong>Suggested way to discover</strong> is a concrete action, not a guess. '
        'Every question below is published for review; none has been answered on your behalf.</p>'
        + render_table(
            ["question_id", "decision_area", "question", "information_we_have",
             "information_we_lack", "decision_it_blocks", "suggested_way_to_discover",
             "priority", "status", "official_source_url"],
            decisions, num_cols=("question_id",)),
        "16 questions, what is known, what is missing, and how to find it.")

    # Suggestions ----------------------------------------------------------
    pages["suggestions.html"] = page(
        "Suggestions for review",
        '<p class="note"><strong>Nothing here has been implemented.</strong> Every row is '
        '<em>pending_human_choice</em>. Each one states the current repository state, the decision problem '
        'it solves, two or three option paths, a recommended path, and what must be true before it is '
        'started. Choose a path, then implement — not the other way round.</p>'
        + render_table(
            ["suggestion_id", "area", "title", "current_repo_state",
             "decision_problem_solved", "option_paths_for_review", "recommended_path",
             "prerequisites_before_implementing", "effort_and_reversibility",
             "review_status", "official_source_url"],
            suggestions, num_cols=("suggestion_id",)),
        "14 reviewable improvements to the site and the decision process, none auto-applied.")

    # Standings ------------------------------------------------------------
    pages["standings.html"] = page(
        "2026 standings (verified)",
        '<p class="note">All 32 rows read from '
        f'{link("https://www.nfl.com/standings/", "nfl.com/standings")} on {CAPTURE}. Only the twelve '
        'columns the page\'s own LEGEND defines are captured; the table renders two further columns it '
        'does not define, and those are omitted rather than guessed (flag NFL3-F02). '
        '<strong>This snapshot does not yet include the completed Thursday 12 November game</strong> '
        '(flag NFL3-F05). Per-game rates are computed here from the verified totals.</p>'
        '<dl class="kv">'
        f'<dt>Identity check</dt><dd>sum(W) = 136, sum(L) = 136, sum(T) = 2 — every non-tie game yields '
        'exactly one win and one loss.</dd>'
        f'<dt>Points identity</dt><dd>sum(PF) = sum(PA) = 6,291 — every point scored is a point allowed.</dd>'
        f'<dt>League rate</dt><dd>{esc(linecheck["league_points_per_team_game"])} points per team-game, '
        f'i.e. {esc(linecheck["league_points_per_game_both_teams"])} points per game.</dd>'
        '</dl>'
        + render_table(
            ["conference", "division", "team", "abbr", "w", "l", "t", "pct", "pf", "pa",
             "net_pts", "home", "road", "div", "conf", "streak", "games_played",
             "pf_per_game", "pa_per_game", "net_pts_per_game", "status",
             "official_source_url"],
            standings,
            num_cols=("w", "l", "t", "pct", "pf", "pa", "net_pts", "games_played",
                      "pf_per_game", "pa_per_game", "net_pts_per_game")),
        "The verified official standings table, with identity checks.")

    # Slate ----------------------------------------------------------------
    pages["slate.html"] = page(
        "Week 10 slate and byes",
        '<p class="note">Fourteen games with kickoff date, Eastern time, network, pre-game records and the '
        f'canonical NFL game URL, read from {link("https://www.nfl.com/schedules", "nfl.com/schedules")}. '
        'One game was already final at capture: the Thursday 12 November Commanders 24–21 win over the '
        f'Giants, verified on {link("https://www.nfl.com/scores/", "nfl.com/scores")}. Score cells are '
        'blank for every game that had not kicked off.</p>'
        + render_table(
            ["game_id", "week", "day", "date", "kickoff_et", "network", "away",
             "away_record_pregame", "home", "home_record_pregame", "game_status",
             "away_score", "home_score", "official_source_url"],
            slate, num_cols=("week", "away_score", "home_score"))
        + '<h2>Teams on bye (Week 10)</h2>'
        + render_table(
            ["week", "team_abbr", "record_pregame", "official_source_url"],
            byes, num_cols=("week",)),
        "The verified Week 10 schedule, final result, and bye teams.")

    # Injuries -------------------------------------------------------------
    tot = len(injuries)
    designated = sum(1 for r in injuries if r["game_status"])
    pages["injuries.html"] = page(
        "Official Week 10 injury report",
        f'<p class="note">All {tot} rows published on '
        f'{link("https://www.nfl.com/injuries/", "nfl.com/injuries")} at capture, with the five columns the '
        'page itself defines: Player, Position, Injuries, Practice Status, Game Status. '
        f'{designated} rows carry an Out / Questionable / Doubtful designation; the rest were still blank, '
        'because the report is populated progressively through the week (flag NFL3-F11). Blank injury '
        'descriptions are the page\'s own blanks — none is inferred.</p>'
        '<h2>Per-club load</h2>'
        '<p>Counts derived by reading every row above. "No game status published" counts listed players '
        'whose Game Status cell was still empty.</p>'
        + render_table(
            ["team_abbr", "players_listed", "did_not_participate", "limited", "full",
             "designated_out", "designated_questionable", "designated_doubtful",
             "no_game_status_published", "dnp_share", "status", "official_source_url"],
            load,
            num_cols=("players_listed", "did_not_participate", "limited", "full",
                      "designated_out", "designated_questionable", "designated_doubtful",
                      "no_game_status_published", "dnp_share"))
        + f'<h2>Full report ({tot} rows)</h2>'
        + render_table(
            ["row_id", "team_abbr", "player", "position", "injury", "practice_status",
             "game_status", "official_source_url"],
            injuries, num_cols=("row_id",)),
        "Every official Week 10 injury-report row, plus a per-club load count.")

    # Depth ----------------------------------------------------------------
    pages["depth.html"] = page(
        "Depth charts and starter-versus-backup deficiency",
        '<p class="note"><strong>Both clubs label their own chart unofficial.</strong> Patriots.com says '
        'the chart "is unofficial and is published by the writers of Patriots.com"; the Lions chart is an '
        '"Unofficial Depth Chart Compiled by Lions Football Communications". That caveat is carried onto '
        'every row below, and the deficiency score is a <strong>proposed weighting, not an observed '
        'quantity</strong> (flag NFL3-F07). Offense and defense are tracked the same way.</p>'
        '<h2>Deficiency map</h2>'
        '<p>For each position slot the shallowest listed string not ruled Out is the active string; the '
        'next listed player behind them is the replacement. A slot scores 0.00 when a healthy 1st string '
        'is active, 0.35 when the 1st string is Questionable, 0.65 when a healthy 2nd string must start, '
        '0.85 when the 2nd string is himself Questionable, and 1.00 when the replacement is 3rd string or '
        'deeper, or when no replacement is listed at all. Those weights are design choices.</p>'
        + render_table(
            ["team_abbr", "unit", "position_slot", "first_string", "active_string",
             "active_player", "active_game_status", "next_available_backup",
             "next_backup_string", "ruled_out_in_slot", "questionable_in_slot",
             "deficiency_score", "score_kind", "official_source_url", "injury_report_url"],
            deficiency, num_cols=("active_string", "next_backup_string", "deficiency_score"))
        + '<h2>Charts as published (1st → 4th string)</h2>'
        + render_table(
            ["team_abbr", "unit", "position_slot", "first_string", "second_string",
             "third_string", "fourth_string", "strings_listed", "source_status",
             "source_caveat", "official_source_url"],
            charts, num_cols=("strings_listed",))
        + '<h2>Designated players missing from their own club chart</h2>'
        '<p>These players carry an official Out/Questionable designation but do not appear anywhere on '
        'their club\'s published chart, so no replacement string can be resolved for them. Where a chart '
        'entry shares a name prefix, it is shown as a <em>candidate string match only</em> — this pack '
        'does not assert the two names are the same person.</p>'
        + render_table(
            ["team_abbr", "player", "position", "game_status", "practice_status", "injury",
             "finding", "same_prefix_name_on_chart", "name_match_is_verified_identity",
             "official_source_url", "depth_chart_url"],
            unlisted),
        "1st-to-4th string ordering mapped onto official injury designations, offense and defense.")

    # Lines ----------------------------------------------------------------
    pages["lines.html"] = page(
        "Originated lines",
        '<p class="note"><strong>These are our own numbers, not market prices.</strong> They are computed '
        'only from verified points-for and points-against per game. Two parameters are declared rather '
        'than fitted — home-field advantage at 0.00 points and shrinkage at 1.00 — because no official '
        'page in this pack supplies them (flag NFL3-F06). The moneyline column is blank because turning '
        'a point margin into a win probability needs a victory-margin distribution that is also un-sourced '
        '(flag NFL3-F08). Market spread, market total and closing-line value are blank because no licensed '
        'price archive is configured (flag NFL3-F10).</p>'
        '<h2>Self-consistency check</h2>'
        '<dl class="kv">'
        '<dt>League points per team-game</dt>'
        f'<dd>{esc(linecheck["league_points_per_team_game"])} (computed from verified standings: 6,291 '
        'points over 274 team-games)</dd>'
        '<dt>League points per game (both teams)</dt>'
        f'<dd>{esc(linecheck["league_points_per_game_both_teams"])}</dd>'
        '<dt>Model mean total</dt>'
        f'<dd>{esc(linecheck["model_mean_total"])}</dd>'
        '<dt>Model minus league</dt>'
        f'<dd>{esc(linecheck["model_minus_league_total"])} points</dd>'
        '<dt>Model mean absolute home spread</dt>'
        f'<dd>{esc(linecheck["model_mean_abs_home_spread"])} points</dd>'
        '<dt>Games modelled</dt>'
        f'<dd>{esc(linecheck["games_modelled"])} scheduled '
        f'({esc(linecheck["games_excluded_already_final"])} excluded: already final)</dd>'
        '</dl>'
        '<p>Convention: the home spread is in American form, so a negative number means the home team is '
        'favoured by that many points.</p>'
        + render_table(
            ["game_id", "away", "home", "home_ppg_input", "home_papg_input", "away_ppg_input",
             "away_papg_input", "inputs_status", "inputs_source_url", "hfa_points_parameter",
             "shrinkage_parameter", "model_applicability", "expected_home_points",
             "expected_away_points", "originated_home_spread", "originated_total",
             "originated_moneyline_home_prob", "market_spread", "market_total",
             "closing_line_value", "status", "official_source_url"],
            lines,
            num_cols=("home_ppg_input", "home_papg_input", "away_ppg_input", "away_papg_input",
                      "hfa_points_parameter", "shrinkage_parameter", "expected_home_points",
                      "expected_away_points", "originated_home_spread", "originated_total",
                      "market_spread", "market_total", "closing_line_value"))
        + '<details><summary>Why the moneyline column is blank</summary><p>'
        + esc(lines[0]["originated_moneyline_home_prob_note"])
        + '</p></details>',
        "Our own fair spread and total for Week 10, from verified inputs only.")

    # Strategies -----------------------------------------------------------
    pages["strategies.html"] = page(
        "Strategy catalog",
        '<p class="note">Ten preregistered strategies across single bets, player props, same-game prop '
        'combos and parlays. Every row states its hypothesis, its signal rule, how its own line is built, '
        'and which gates must open. <strong>Zero selections have been graded, so zero strategies '
        'qualify.</strong> Two are additionally blocked on a missing parameter or missing data.</p>'
        '<p>Market-integrity eligibility (gate G11) is applied before any modelling: a prop family tied to '
        'officiating or injuries is rejected by construction, because the NFL\'s own release says partners '
        f'work together to prohibit wagers "tied to officiating and injuries".</p>'
        + render_table(
            ["strategy_id", "family", "market", "hypothesis", "signal_rule",
             "own_line_method", "inputs_verified", "correlation_pair", "required_gates",
             "selections_graded", "qualified", "status", "official_source_url"],
            strategies, num_cols=("selections_graded",)),
        "Singles, parlays and prop combos — preregistered, none qualified.")

    # Validation -----------------------------------------------------------
    pages["validation.html"] = page(
        "Validation gates",
        '<p class="note">Twelve gates. Four are open because they depend only on how the pack is built. '
        'Eight are blocked because a licensed input does not exist in this repository. A blocked gate is '
        'not a failure — it is the reason no performance number is published.</p>'
        + render_table(
            ["gate_id", "gate", "rule", "how_it_removes_luck", "blocking_missing_input",
             "status", "official_or_method_reference"],
            gates, num_cols=("gate_id",)),
        "Twelve gates that separate skill from variance; 4 open, 8 blocked.")

    # Correlations ---------------------------------------------------------
    pages["correlations.html"] = page(
        "Measured correlations and the luck index",
        '<p class="note">Unlike every other NFL pack in this repository, these correlation values are '
        '<strong>measured</strong>: each is computed here from the 32 verified official standings rows, '
        'with n, a two-sided p-value, a Fisher z interval and a 5,000-draw percentile bootstrap interval '
        'computed independently. They describe the league, not any betting market, and they are not '
        'betting edges.</p>'
        '<p>Two of the eight are not statistically distinguishable from zero at the 5% level '
        '(points-for vs points-against, and division record vs overall record). That result is published '
        'as it came out; it is not suppressed.</p>'
        + render_table(
            ["correlation_id", "x_variable", "y_variable", "method", "n", "coefficient",
             "p_value", "ci95_low", "ci95_high", "bootstrap_ci95_low",
             "bootstrap_ci95_high", "status", "official_source_url"],
            corrs, num_cols=("n", "coefficient", "p_value", "ci95_low", "ci95_high",
                             "bootstrap_ci95_low", "bootstrap_ci95_high"))
        + '<h2>Luck index: win percentage regressed on net points per game</h2>'
        '<dl class="kv">'
        f'<dt>Model</dt><dd>win% = a + b &times; (net points per game), n = {esc(luck_summary["n"])}</dd>'
        f'<dt>Intercept</dt><dd>{esc(luck_summary["intercept"])}</dd>'
        f'<dt>Slope</dt><dd>{esc(luck_summary["slope"])} per net point per game '
        f'(SE {esc(luck_summary["se_slope"])}, t = {esc(luck_summary["t_slope"])}, '
        f'df = {esc(luck_summary["df"])}, p = {esc(luck_summary["p_slope"])})</dd>'
        f'<dt>R²</dt><dd>{esc(luck_summary["r2"])}</dd>'
        f'<dt>Residual SD</dt><dd>{esc(luck_summary["residual_sd_win_pct"])} win percentage</dd>'
        '</dl>'
        '<p>The residual is the part of a club\'s record its scoring does not explain — the same estimator '
        'gate G10 applies to a strategy, except that a strategy gets slate-clustered intervals and must '
        'clear zero before it is called skilled. A positive residual means the club won more than its '
        'scoring implies.</p>'
        + render_table(
            ["team_abbr", "team", "games_played", "win_pct", "net_pts_per_game",
             "expected_win_pct_from_net_pts", "luck_residual_win_pct",
             "luck_residual_wins", "status", "official_source_url"],
            luck,
            num_cols=("games_played", "win_pct", "net_pts_per_game",
                      "expected_win_pct_from_net_pts", "luck_residual_win_pct",
                      "luck_residual_wins"))
        + '<h2>What is still blank</h2>'
        '<p>No dependence between two betting legs is published: measuring one needs graded paired '
        'outcomes under licence, and the ledger is empty (flag NFL3-F09). The method — paired residuals, '
        'Pearson on a joint sample, slate-clustered interval, no independence assumption — is specified '
        'and is what gate G09 will apply.</p>',
        "Eight correlations measured from official data, plus a 32-row luck decomposition.")

    # Leaderboard ----------------------------------------------------------
    pages["leaderboard.html"] = page(
        "Leaderboard and rewards",
        '<p class="note"><strong>Rewards are non-monetary by design:</strong> research standing and '
        'publication priority only. No monetary prize is offered, and none may be offered while the NFL '
        'terms restrict use to individual non-commercial informational purposes. The board is empty '
        'because no entry has cleared the gates.</p>'
        '<h2>Tiers</h2>'
        + render_table(
            ["tier_id", "tier", "requirement", "reward", "entries_at_this_tier",
             "monetary_value", "official_or_method_reference"],
            tiers, num_cols=("entries_at_this_tier",))
        + '<h2>Entries</h2>'
        '<p>Every entry sits below Tier 3: each has gates G01, G05, G11 and G12 open, and each is blocked '
        'on the licensed data that gates G02, G03, G04, G06, G07, G08, G09 and G10 require.</p>'
        + render_table(
            ["strategy_id", "family", "market", "selections_graded", "gates_open",
             "gates_blocked", "tier", "reward_awarded", "status", "official_source_url"],
            entries, num_cols=("selections_graded",)),
        "A four-tier, non-monetary competition; no entry has qualified.")

    # Repo review ----------------------------------------------------------
    pages["repo-review.html"] = page(
        "Repository review — irregularities",
        '<p class="note">Findings from reviewing this repository line by line on 2026-11-13. Every finding '
        'states the evidence and links to the file or page it came from. Findings that belong to another '
        'session\'s files are logged as requests in COORDINATION.md and are <strong>not</strong> edited by '
        'this session.</p>'
        + render_table(
            ["finding_id", "area", "finding", "evidence", "impact", "files_affected",
             "severity", "review_status", "official_or_repo_source_url"],
            findings, num_cols=("finding_id",)),
        "14 verified irregularities across the repository, with evidence and links.")

    # Sources --------------------------------------------------------------
    pages["sources.html"] = page(
        "Source register",
        '<p class="note">Eleven pages, each read directly on 2026-11-13. The verbatim column quotes what '
        'the page actually said. The last column states what the source does <em>not</em> support — the '
        'boundary is part of the record, not a footnote.</p>'
        + render_table(
            ["source_id", "publisher", "title", "official_source_url", "verified_date",
             "retrieval_method", "verification_status", "verbatim_evidence_excerpt",
             "supports_claim", "does_not_support_boundary"],
            sources, num_cols=("source_id",)),
        "Every page read for this pack, with verbatim excerpts and boundaries.")

    # Flagged --------------------------------------------------------------
    pages["flagged.html"] = page(
        "Flagged for review",
        '<p class="note">Everything blank or unresolved, in one place. A blank cell in this pack means no '
        'official source in this pack supplies the value; it never means zero.</p>'
        + render_table(
            ["flag_id", "area", "item", "what_is_blank", "why", "official_source_url",
             "severity", "review_status"],
            flags, num_cols=("flag_id",)),
        "16 blank or unresolved items, each with its source.")

    for name, body in pages.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
            fh.write(body)

    return {
        "csv": written,
        "pages": sorted(pages),
        "counts": {
            "standings": len(standings), "slate": len(slate), "byes": len(byes),
            "injuries": len(injuries), "injury_load": len(load),
            "depth_charts": len(charts), "deficiency": len(deficiency),
            "unlisted": len(unlisted), "decisions": len(decisions),
            "suggestions": len(suggestions), "strategies": len(strategies),
            "gates": len(gates), "correlations": len(corrs), "luck": len(luck),
            "lines": len(lines), "tiers": len(tiers), "entries": len(entries),
            "findings": len(findings), "sources": len(sources), "flags": len(flags),
        },
        "line_check": linecheck,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="run the verifier after building")
    args = ap.parse_args()
    res = build_all()
    print("CSVs written:", len(res["csv"]))
    for k, v in res["counts"].items():
        print(f"  {k:14s} {v:5d} rows")
    print("Pages written:", len(res["pages"]))
    for p in res["pages"]:
        print("  docs/nfl-309921cc/" + p)
    print("Line self-check:", res["line_check"])
    if args.check:
        cp = subprocess.run([sys.executable,
                             os.path.join(REPO, "scripts", "check_nfl_309921cc.py")])
        return cp.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
