#!/usr/bin/env python3
"""Build the nfl-48217a55 pack: CSV tables + a zero-input GitHub Pages dashboard.

Everything published is computed from :mod:`src.nfl_48217a55`, whose only hand-written
content is the official values in ``capture.py``. The builder takes no arguments and
touches no network, so a re-run must produce byte-identical files - that is how a
reviewer checks that the published tables really are what the code computes.

Usage
-----
    python3 scripts/build_nfl_48217a55.py            # write CSVs and HTML
    python3 scripts/build_nfl_48217a55.py --check    # build, then run the verifier
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_48217a55 import advice as A          # noqa: E402
from nfl_48217a55 import capture as C         # noqa: E402
from nfl_48217a55 import correlate as X       # noqa: E402
from nfl_48217a55 import flags as FL          # noqa: E402
from nfl_48217a55 import gates as G           # noqa: E402
from nfl_48217a55 import injuries as IN       # noqa: E402
from nfl_48217a55 import model as M           # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-48217a55")
DATA = os.path.join(REPO, "data", "nfl_48217a55")
ASSETS = os.path.join(DOCS, "assets")

CAPTURE = C.CAPTURE_CLOCK_UTC

STYLE = """:root{--bg:#0e1117;--panel:#161b22;--panel2:#1c2430;--line:#2a3441;--ink:#e6edf3;
--muted:#9aa7b4;--accent:#4ba3f5;--good:#3fb950;--warn:#d29922;--bad:#f85149;--empty:#6e7681}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
nav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:10px 16px;background:var(--panel);
border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
nav .brand{font-weight:700;letter-spacing:.04em;margin-right:10px}
nav a{padding:5px 9px;border-radius:6px;font-size:13.5px;color:var(--ink);background:var(--panel2);
border:1px solid var(--line)}nav a:hover{background:#243040;text-decoration:none}
nav a[aria-current=page]{border-color:var(--accent);color:var(--accent)}
main{max-width:1320px;margin:0 auto;padding:22px 16px 60px}
h1{font-size:27px;line-height:1.2;margin:6px 0 10px}h2{font-size:20px;margin:34px 0 8px;
padding-top:8px;border-top:1px solid var(--line)}h3{font-size:16px;margin:20px 0 6px}
p{margin:8px 0}.eyebrow{color:var(--accent);font-size:12px;letter-spacing:.16em;text-transform:uppercase}
.lede{color:var(--muted);max-width:92ch}
.hero{background:linear-gradient(180deg,#16202c,#11161d);border:1px solid var(--line);border-radius:14px;
padding:22px;margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:14px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px;
color:var(--ink)}.card:hover{border-color:var(--accent);text-decoration:none}
.card .k{font-size:24px;font-weight:700;display:block}.card .l{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:12px 0 18px}
.cat{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;color:var(--ink)}
.cat:hover{border-color:var(--accent);text-decoration:none}
.cat h3{margin:0 0 4px;font-size:15px}.cat p{margin:0;color:var(--muted);font-size:13px}
.cat .arrow{display:block;margin-top:8px;font-size:12.5px;color:var(--accent)}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:10px 0 16px;max-height:none}
table{border-collapse:collapse;width:100%;font-size:13px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--panel2);font-size:11.5px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);
white-space:nowrap;position:sticky;top:44px}tbody tr:hover{background:#1b2430}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.blank:before{content:"blank";color:var(--empty);font-style:italic;font-size:11.5px}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid var(--line);
background:#1b2430;white-space:nowrap}.p-ok{color:var(--good);border-color:#204a2b}
.p-warn{color:var(--warn);border-color:#5a4413}.p-bad{color:var(--bad);border-color:#5c2422}
.p-info{color:var(--accent);border-color:#1d4b73}
.note{color:var(--muted);font-size:13.5px;max-width:92ch}
ul{margin:8px 0 8px 22px;padding:0}li{margin:5px 0}
code{background:#1b2430;border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:13px}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:13px;padding:18px 16px 40px;
max-width:1320px;margin:0 auto}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:8px;margin:10px 0 4px}
.kv div{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:9px 11px}
.kv span{display:block;color:var(--muted);font-size:12px}
.kv strong{font-size:16px}
"""

PAGES = [
    ("index.html", "Dashboard"),
    ("decision-readiness.html", "Decision readiness"),
    ("injuries.html", "Injuries"),
    ("depth.html", "Depth &amp; starters"),
    ("inactives.html", "Inactives &amp; venues"),
    ("schedule-results.html", "Schedule &amp; results"),
    ("standings.html", "Standings"),
    ("transactions.html", "Transactions &amp; IR"),
    ("correlations.html", "Correlations"),
    ("luck.html", "Removal of luck"),
    ("strategies.html", "Strategies"),
    ("validation-gates.html", "Gates"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("repo-review.html", "Repo review"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
    ("executive-summary.html", "Executive summary"),
]


# ---------------------------------------------------------------------------
# rendering helpers
# ---------------------------------------------------------------------------
def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url, label="source"):
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)} &#8599;</a>'


def pill(text):
    t = (text or "").lower()
    cls = "pill"
    if t in ("cleared", "pass", "yes", "verified-this-session", "match", "active"):
        cls += " p-ok"
    elif t in ("partial", "info", "medium", "verified-in-repo", "control", "trending toward playing",
               "expected to play", "observed-needs-owner"):
        cls += " p-warn"
    elif t in ("blocked", "fail", "no", "high", "rejected", "inactive", "needs review"):
        cls += " p-bad"
    else:
        cls += " p-info"
    return f'<span class="{cls}">{esc(text)}</span>'


def table(headers, rows, num_cols=(), max_rows=None, internal=None):
    """Render a table.

    A cell whose value is an https URL becomes a clickable source link, so every data row
    carries its source. Empty cells get the .blank class so 'blank' is visibly blank rather
    than a dash or a zero.

    `internal` marks a table of governance artifacts that have no external source; the
    reason is rendered as a data attribute the checker reads, so "no source here" is a
    declared decision rather than an oversight.
    """
    body = []
    for i, r in enumerate(rows):
        if max_rows and i >= max_rows:
            break
        if len(r) != len(headers):
            raise ValueError(
                f"row {i} has {len(r)} cells but {len(headers)} headers: {headers}"
            )
        cells = []
        for j, v in enumerate(r):
            s = "" if v is None else str(v)
            cls = []
            if headers[j] in num_cols:
                cls.append("num")
            if s == "":
                cls.append("blank")
            attr = ' class="' + " ".join(cls) + '"' if cls else ""
            if s.startswith("https://"):
                shown = link(s, "official")
            else:
                shown = esc(s)
            cells.append("<td" + attr + ">" + shown + "</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th scope='col'>{esc(h)}</th>" for h in headers)
    attr = ' data-internal="' + esc(internal) + '"' if internal else ""
    return (
        '<div class="wrap"><table' + attr + '><thead><tr>' + head + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def page(title, active, body):
    nav = "".join(
        f'<a href="{p}"{" aria-current=page" if p == active else ""}>{n}</a>'
        for p, n in PAGES
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="NFL decision-readiness pack: every row sourced to an official page, every blank cell flagged.">
<title>{esc(title)} | NFL Decision Readiness (48217a55)</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<nav aria-label="Pack navigation"><a class="brand" href="index.html">48217A55 <span>/ NFL</span></a>{nav}<a href="../index.html">All sections</a></nav>
<main>
{body}
</main>
<footer>
<p>Session <code>arena/48217a55-own6</code> &#183; capture {esc(CAPTURE)} &#183;
sources read live on {esc(C.CAPTURE_DATE_UTC)} &#183; rebuild with
<code>python3 scripts/build_nfl_48217a55.py</code>.</p>
<p>A value is published only if it was read from the official page cited on its row. A blank
cell is never zero: it is an empty cell with a flag. Nothing here demonstrates a profitable
NFL edge, and no market price appears anywhere in this pack.</p>
</footer>
</body>
</html>
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_csv(name, fieldnames, rows):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore",
                           lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def main() -> int:
    os.makedirs(ASSETS, exist_ok=True)
    write(os.path.join(ASSETS, "style.css"), STYLE)

    pit, recon = M.point_in_time_standings()
    verif = M.verification_against_pregame_page(pit)
    checks = M.integrity_checks(pit)
    luck = M.luck_panel(pit)
    cors = X.correlations(pit)
    reqs = A.requirements()
    req_counts = A.requirement_summary()
    roll = IN.club_rollup()
    depth = IN.depth_of_replacement()

    tables = {}

    # ---- sources ------------------------------------------------------
    tables["sources.csv"] = write_csv(
        "sources.csv",
        ["source_id", "url", "read_at_utc", "chunks_total", "chunks_read", "what_it_supports"],
        [{"source_id": s, "url": u, "read_at_utc": t, "chunks_total": c,
          "chunks_read": cr, "what_it_supports": w}
         for s, u, t, c, cr, w in C.SOURCES],
    )

    # ---- injuries -----------------------------------------------------
    tables["injury_report_2026_11_15.csv"] = write_csv(
        "injury_report_2026_11_15.csv",
        ["club", "player", "position", "unit", "side", "injury", "practice_status",
         "game_status", "source_url", "read_at_utc"],
        IN.rows(),
    )
    tables["injury_club_rollup.csv"] = write_csv(
        "injury_club_rollup.csv",
        ["club", "rows_on_report", "out", "doubtful", "questionable", "listed_no_game_status",
         "dnp", "limited", "full", "offense_out", "defense_out", "source_url", "read_at_utc"],
        roll,
    )
    tables["depth_of_replacement.csv"] = write_csv(
        "depth_of_replacement.csv",
        ["club", "unit", "side", "on_report", "out_floor", "questionable", "doubtful",
         "replacement_named", "replacement_source_url", "note", "source_url"],
        depth,
    )
    tables["announced_starters.csv"] = write_csv(
        "announced_starters.csv",
        ["club", "player", "position", "evidence_kind", "announced_for",
         "date_in_official_story", "headline", "source_url", "read_at_utc"],
        IN.announced_starters(),
    )
    tables["roster_events.csv"] = write_csv(
        "roster_events.csv",
        ["date", "club_from", "club_to", "player", "event", "starter_announced", "note",
         "source_url", "read_at_utc"],
        IN.roster_events(),
    )

    # ---- availability cross-checks ------------------------------------
    tables["reserve_list.csv"] = write_csv(
        "reserve_list.csv",
        ["date", "club", "player", "transaction", "on_week10_injury_report",
         "interpretation", "source_url", "read_at_utc"],
        IN.reserve_coverage(),
    )
    tables["trades.csv"] = write_csv(
        "trades.csv",
        ["date", "club_from", "club_to", "player", "event", "starter_announced", "note",
         "source_url", "read_at_utc"],
        IN.roster_events(),
    )

    # ---- schedule, results, standings ---------------------------------
    slate_rows = []
    for slug, date, kickoff, away, home, ap, hp, status, net in C.WEEK10_SLATE:
        slate_rows.append({
            "game_slug": slug, "week": 10, "season": C.SEASON, "date": date,
            "kickoff_et": kickoff, "away": away, "home": home, "away_points": ap,
            "home_points": hp, "status": status, "network": net,
            "venue": "", "venue_source_url": "",
            "source_url": f"https://www.nfl.com/games/{slug}",
            "read_at_utc": CAPTURE,
        })
    tables["week10_slate.csv"] = write_csv(
        "week10_slate.csv",
        ["game_slug", "week", "season", "date", "kickoff_et", "away", "home", "away_points",
         "home_points", "status", "network", "venue", "venue_source_url", "source_url",
         "read_at_utc"],
        slate_rows,
    )

    live_rows = [{
        "game_slug": g["game_slug"], "away": g["away"], "home": g["home"],
        "away_points": g["away_points"], "home_points": g["home_points"],
        "quarter": g.get("quarter", ""), "status": g["status"],
        "in_results_feed": "no",
        "note": "in progress or not started at capture time; never used as a result",
        "source_url": g["source_url"], "read_at_utc": CAPTURE,
    } for g in M.live_games()]
    tables["week10_live_scores.csv"] = write_csv(
        "week10_live_scores.csv",
        ["game_slug", "away", "home", "away_points", "home_points", "quarter", "status",
         "in_results_feed", "note", "source_url", "read_at_utc"],
        live_rows,
    )

    feed = []
    for g in M.final_games():
        feed.append({
            "game_slug": g["game_slug"], "week": 10, "season": C.SEASON,
            "date": g["date"], "kickoff_et": g["kickoff_et"],
            "away": g["away"], "home": g["home"],
            "away_points": g["away_points"], "home_points": g["home_points"],
            "winner": g["winner"], "margin": g["margin"], "total_points": g["total_points"],
            "status": g["status"], "source_url": g["source_url"], "read_at_utc": CAPTURE,
        })
    tables["results_feed.csv"] = write_csv(
        "results_feed.csv",
        ["game_slug", "week", "season", "date", "kickoff_et", "away", "home", "away_points",
         "home_points", "winner", "margin", "total_points", "status", "source_url",
         "read_at_utc"],
        feed,
    )

    tables["standings_as_rendered.csv"] = write_csv(
        "standings_as_rendered.csv",
        ["club", "w", "l", "t", "pct", "pf", "pa", "net_points", "home", "road", "div",
         "conf", "streak", "caveat", "source_url", "read_at_utc"],
        [{"club": c, "w": w, "l": l, "t": t, "pct": pct, "pf": pf, "pa": pa, "net_points": net,
          "home": hm, "road": rd, "div": dv, "conf": cf, "streak": st,
          "caveat": "as rendered at capture time; already includes the 9 completed Week 10 games",
          "source_url": C.SOURCE_URL["S3"], "read_at_utc": CAPTURE}
         for c, w, l, t, pct, pf, pa, net, hm, rd, dv, cf, st in C.STANDINGS_RENDER],
    )
    tables["standings_point_in_time.csv"] = write_csv(
        "standings_point_in_time.csv",
        ["club", "club_name", "through_week", "w", "l", "t", "games", "win_pct", "pf", "pa",
         "net_points", "pf_per_game", "pa_per_game", "margin_per_game",
         "week10_games_removed"],
        [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in pit],
    )
    tables["standings_reconstruction.csv"] = write_csv(
        "standings_reconstruction.csv",
        ["club", "rendered_record", "rendered_pf", "rendered_pa", "week10_games_subtracted",
         "subtracted_pf", "subtracted_pa", "reconstructed_record", "reconstructed_pf",
         "reconstructed_pa"],
        recon,
    )
    tables["standings_verification.csv"] = write_csv(
        "standings_verification.csv",
        ["club", "record_on_pregame_page", "expected_from_arithmetic", "match", "basis",
         "source_url"],
        verif,
    )
    tables["integrity_checks.csv"] = write_csv(
        "integrity_checks.csv",
        ["check", "value_a", "value_b", "result", "note"], checks,
    )
    tables["team_ratings_naive.csv"] = write_csv(
        "team_ratings_naive.csv",
        ["club", "club_name", "rating_ppg", "win_pct", "pf_per_game", "pa_per_game",
         "opponent_adjusted", "blocking_gate", "note"],
        [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
         for r in M.naive_ratings(pit)],
    )
    tables["luck_panel.csv"] = write_csv(
        "luck_panel.csv", ["metric", "value", "derivation"],
        [
            {"metric": "clubs", "value": luck["clubs"], "derivation": "rows in the reconstructed table"},
            {"metric": "team-games", "value": luck["team_games"], "derivation": "sum of club games"},
            {"metric": "completed games through Week 9", "value": luck["games"],
             "derivation": "half the summed team-games"},
            {"metric": "observed win-pct variance", "value": round(luck["obs_win_pct_variance"], 6),
             "derivation": "population variance of win percentage across the 32 clubs"},
            {"metric": "observed win-pct SD", "value": round(luck["obs_win_pct_sd"], 6),
             "derivation": "square root of the above"},
            {"metric": "coin-flip null variance", "value": round(luck["null_win_pct_variance"], 6),
             "derivation": "mean over clubs of 0.25 / games: the spread if every game were a fair flip"},
            {"metric": "implied skill variance", "value": round(luck["skill_variance"], 6),
             "derivation": "observed variance minus null variance"},
            {"metric": "luck share", "value": round(luck["luck_share"], 6),
             "derivation": "null variance / observed variance"},
            {"metric": "margin SD (points per game)", "value": round(luck["margin_sd"], 6),
             "derivation": "population SD of points-for minus points-against per game"},
            {"metric": "league points per game", "value": round(luck["league_ppg"], 6),
             "derivation": "mean of club points-for per game"},
            {"metric": "league points allowed per game", "value": round(luck["league_papg"], 6),
             "derivation": "mean of club points-against per game"},
            {"metric": "strategy-level luck removal", "value": "",
             "derivation": "blocked: needs 100 prospective graded forecasts (gate G8)"},
        ],
    )

    # ---- inactives and venues -----------------------------------------
    tables["week9_inactives.csv"] = write_csv(
        "week9_inactives.csv",
        ["game_slug", "club", "player", "position", "emergency_third_qb", "venue",
         "kickoff_et", "source_url", "read_at_utc"],
        IN.week9_inactive_rows(),
    )
    tables["venues.csv"] = write_csv(
        "venues.csv",
        ["week", "season", "game_slug", "away", "home", "kickoff_et", "venue", "source_url",
         "read_at_utc"],
        IN.venues(),
    )

    # ---- depth route probe --------------------------------------------
    tables["depth_route_probe.csv"] = write_csv(
        "depth_route_probe.csv",
        ["route", "url", "http_result", "depth_order_published", "club_hosted_depth_link_found",
         "notes", "read_at_utc"],
        [{**{"route": r, "url": u, "http_result": h, "depth_order_published": d,
             "club_hosted_depth_link_found": cl, "notes": n}, "read_at_utc": CAPTURE}
         for r, u, h, d, cl, n in C.DEPTH_ROUTE_PROBES],
    )

    # ---- correlations --------------------------------------------------
    tables["correlations.csv"] = write_csv(
        "correlations.csv",
        ["id", "x_axis", "y_axis", "n", "unit", "method", "estimate", "ci_low", "ci_high",
         "p_value", "caveat", "x_source_url", "y_source_url"],
        cors,
    )
    tables["correlation_exclusions.csv"] = write_csv(
        "correlation_exclusions.csv",
        ["id", "candidate", "why_not", "what_would_clear_it", "source_url"],
        X.exclusions(),
    )
    tables["designation_calibration.csv"] = write_csv(
        "designation_calibration.csv",
        ["designation", "sample", "n_published_resolutions", "n_definite", "n_active",
         "n_inactive", "play_rate", "ci_low", "ci_high", "method", "selection_warning",
         "usable_as_feature", "blocking_gate", "source_url"],
        X.designation_calibration(),
    )

    # ---- prices and origination ---------------------------------------
    tables["price_capture_attempts.csv"] = write_csv(
        "price_capture_attempts.csv",
        ["route", "kind", "result", "what_the_page_actually_contains", "conclusion"],
        [{"route": r, "kind": k, "result": res, "what_the_page_actually_contains": w,
          "conclusion": con} for r, k, res, w, con in C.PRICE_CAPTURE_ATTEMPTS],
    )
    schema_rows = []
    for slug, date, kickoff, away, home, _ap, _hp, _st, _net in C.WEEK10_SLATE:
        for market in ("side", "total", "moneyline"):
            schema_rows.append({
                "game_slug": slug, "market": market, "origination_stage":
                {"side": 1, "total": 2, "moneyline": 3}[market],
                "model_fair_line": "", "market_line": "", "difference": "",
                "inputs_json": "", "probability": "", "published_at_utc": "",
                "status": "blocked: no licensed price source (gate G2)",
                "flag_id": "48217-F01",
                "source_url": f"https://www.nfl.com/games/{slug}",
            })
    tables["originated_lines_schema.csv"] = write_csv(
        "originated_lines_schema.csv",
        ["game_slug", "market", "origination_stage", "model_fair_line", "market_line",
         "difference", "inputs_json", "probability", "published_at_utc", "status",
         "flag_id", "source_url"],
        schema_rows,
    )

    # ---- strategies, gates, leaderboard --------------------------------
    tables["strategy_registry.csv"] = write_csv(
        "strategy_registry.csv",
        ["strategy_id", "name", "family", "frozen_definition", "benchmark",
         "evaluation_window", "what_would_change_our_mind", "required_gates",
         "gates_uncleared", "status", "qualified", "qualified_reason", "pre_registration",
         "backtest_on_leaderboard", "source_url"],
        G.strategy_rows(),
    )
    tables["validation_gates.csv"] = write_csv(
        "validation_gates.csv",
        ["gate_id", "name", "requirement", "threshold", "observed", "status", "source_url"],
        G.gate_rows(),
    )
    tables["leaderboard.csv"] = write_csv(
        "leaderboard.csv",
        ["division", "ranked_strategies", "qualified_strategies", "note", "source_url"],
        G.leaderboard_rows(),
    )
    tables["reward_tiers.csv"] = write_csv(
        "reward_tiers.csv", ["tier", "condition", "reward", "monetary", "evidence"],
        G.REWARD_TIERS,
    )

    # ---- governance ----------------------------------------------------
    tables["requirements_decision_readiness.csv"] = write_csv(
        "requirements_decision_readiness.csv",
        A.REQ_COLUMNS + ["read_on_utc"], reqs,
    )
    tables["questions.csv"] = write_csv(
        "questions.csv", A.Q_COLUMNS, A.questions(),
    )
    tables["suggestions.csv"] = write_csv(
        "suggestions.csv", A.S_COLUMNS, A.suggestions(),
    )
    tables["repo_findings.csv"] = write_csv(
        "repo_findings.csv",
        ["finding_id", "area", "finding", "how_it_was_checked", "status", "effect",
         "source_url"],
        [{"finding_id": i, "area": a, "finding": f, "how_it_was_checked": h, "status": s,
          "effect": e, "source_url": u} for i, a, f, h, s, e, u in C.REPO_FINDINGS],
    )
    tables["flagged.csv"] = write_csv("flagged.csv", FL.FLAG_COLUMNS, FL.flags())

    # ---- blank audit (must be last: it counts the tables above) -------
    audit = []
    for name in sorted(tables):
        path = tables[name]
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        cols = list(rows[0].keys()) if rows else []
        blanks = sum(1 for r in rows for c in cols if (r.get(c) or "") == "")
        cells = len(rows) * len(cols) if cols else 0
        audit.append({
            "table": name,
            "rows": len(rows),
            "columns": len(cols),
            "cells": cells,
            "blank_cells": blanks,
            "blank_pct": round(100.0 * blanks / cells, 2) if cells else 0.0,
            "why_blank": FL.EXPECTED_BLANKS.get(
                name, "not expected: every blank here must be traced to a flag row"),
            "flag_ids": ",".join(FL.flag_index().get(name, [])),
        })
    tables["blank_audit.csv"] = write_csv(
        "blank_audit.csv",
        ["table", "rows", "columns", "cells", "blank_cells", "blank_pct", "why_blank",
         "flag_ids"],
        audit,
    )
    # The audit must cover itself: compute its own row from the file just written, so a
    # reader can see how many cells of the audit are blank and why.
    with open(tables["blank_audit.csv"], encoding="utf-8", newline="") as fh:
        own = list(csv.DictReader(fh))
    own_cols = list(own[0].keys())
    own_blanks = sum(1 for r in own for c in own_cols if (r.get(c) or "") == "")
    audit.append({
        "table": "blank_audit.csv",
        "rows": len(own),
        "columns": len(own_cols),
        "cells": len(own) * len(own_cols),
        "blank_cells": own_blanks,
        "blank_pct": round(100.0 * own_blanks / (len(own) * len(own_cols)), 2),
        "why_blank": "flag_ids is empty for tables with no blanks; that is the point of "
                     "the column",
        "flag_ids": "",
    })
    write_csv(
        "blank_audit.csv",
        ["table", "rows", "columns", "cells", "blank_cells", "blank_pct", "why_blank",
         "flag_ids"],
        audit,
    )

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------
    total_out = sum(1 for r in IN.rows() if r["game_status"] == "Out")
    total_q = sum(1 for r in IN.rows() if r["game_status"] == "Questionable")
    n_final = len(M.final_games())
    n_match = sum(1 for v in verif if v["match"] == "yes")

    # ---------- index ----------
    cats = [
        ("decision-readiness.html", "Decision readiness",
         f"{len(reqs)} requirements, one row each, with the gate that blocks it and the "
         f"number that would clear it."),
        ("injuries.html", "Injuries",
         f"{len(IN.rows())} Week 10 rows across {len(IN.clubs_on_report())} clubs, with "
         f"{total_out} Out and {total_q} Questionable."),
        ("depth.html", "Depth &amp; starters",
         f"{len(depth)} club/unit replacement floors, the depth-route probe, and the "
         f"{len(IN.announced_starters())} starters an official page actually names."),
        ("inactives.html", "Inactives &amp; venues",
         f"{len(IN.week9_inactive_rows())} official Week 9 inactive rows and "
         f"{len(IN.venues())} transcribed venues."),
        ("schedule-results.html", "Schedule &amp; results",
         f"{len(C.WEEK10_SLATE)} Week 10 fixtures, {n_final} finals in the results feed, "
         f"and the in-progress games kept out of it."),
        ("standings.html", "Standings",
         f"The 32-club through-Week-9 table, reconstructed and checked {n_match}/"
         f"{len(verif)} against an independent official page."),
        ("transactions.html", "Transactions &amp; IR",
         f"{len(C.TRADES_NOV_2026)} November trades and "
         f"{len(C.RESERVE_LIST_NOV_2026)} reserve-list moves."),
        ("correlations.html", "Correlations",
         f"{len(cors)} measured with n and an interval, "
         f"{len(X.exclusions())} published as exclusions with the reason."),
        ("luck.html", "Removal of luck",
         f"Luck share {luck['luck_share']:.3f} of the win-percentage spread, from "
         f"{luck['games']} completed games."),
        ("strategies.html", "Strategies",
         f"{len(G.STRATEGIES)} pre-registered definitions, "
         f"{sum(1 for s in G.strategy_rows() if s['qualified'] == 'yes')} qualified."),
        ("validation-gates.html", "Gates",
         f"{len(G.GATES)} gates; {sum(1 for g in G.GATES if g[5] == 'pass')} pass."),
        ("questions.html", "Questions",
         f"{len(A.questions())} questions, what we have, what is missing and the path to "
         f"discover it."),
        ("suggestions.html", "Suggestions",
         f"{len(A.suggestions())} reviewable suggestions; nothing is applied without a "
         f"choice."),
        ("repo-review.html", "Repo review",
         f"{len(C.REPO_FINDINGS)} findings, each checked against an official page or the "
         f"repository itself."),
        ("sources.html", "Sources",
         f"{len(C.SOURCES)} official pages read this session, with clock times."),
        ("flagged.html", "Flagged for review",
         f"{len(FL.flags())} flags covering every blank and every caveat."),
    ]
    cat_cards = "".join(
        f'<a class="cat" href="{u}"><h3>{n}</h3><p>{d}</p><span class="arrow">Open &#8599;</span></a>'
        for u, n, d in cats
    )
    status_counts = "".join(
        f'<div class="card"><span class="k">{v}</span><span class="l">{esc(k)}</span></div>'
        for k, v in sorted(req_counts.items())
    )
    write(os.path.join(DOCS, "index.html"), page(
        "NFL decision-readiness dashboard", "index.html", f"""
<p class="eyebrow">NFL &#183; SESSION 48217A55 &#183; WEEK 10 CAPTURE {esc(C.CAPTURE_DATE_UTC)}</p>
<div class="hero">
<h1>One row per requirement.<br><em>The gate that blocks it. The number that clears it.</em></h1>
<p class="lede">This pack reads the official NFL pages and publishes only what those pages
say. Everything it cannot read stays blank and carries a flag. There is no market price
anywhere in here, and nothing here demonstrates a profitable edge. The point is to make the
state of every requirement measurable, so a decision is a choice about a number rather than
an argument about a feeling.</p>
<div class="cards">
<a class="card" href="decision-readiness.html"><span class="k">{len(reqs)}</span><span class="l">requirements tracked</span></a>
<a class="card" href="decision-readiness.html"><span class="k">{req_counts.get("cleared", 0)}</span><span class="l">cleared</span></a>
<a class="card" href="decision-readiness.html"><span class="k">{req_counts.get('partial', 0)}</span><span class="l">partial</span></a>
<a class="card" href="decision-readiness.html"><span class="k">{req_counts.get('blocked', 0)}</span><span class="l">blocked</span></a>
<a class="card" href="strategies.html"><span class="k">0</span><span class="l">qualified strategies</span></a>
</div>
</div>

<h2 id="status">Where the requirements stand</h2>
<div class="cards">{status_counts}</div>
<p class="note">{esc(req_counts.get('blocked', 0))} requirements are blocked. In almost every
case the block is the same input: an official source that does not exist yet for prices,
depth order or snap counts. The <a href="decision-readiness.html">decision-readiness
table</a> names the number that would clear each one.</p>

<h2 id="capture">What was captured, and when it stops being true</h2>
<div class="kv">
<div><span>Injury-report rows</span><strong>{len(IN.rows())}</strong></div>
<div><span>Clubs on the report</span><strong>{len(IN.clubs_on_report())} of 32</strong></div>
<div><span>Clubs on bye</span><strong>{len(C.BYE_CLUBS_WEEK10)}</strong></div>
<div><span>Players designated Out</span><strong>{total_out}</strong></div>
<div><span>Players designated Questionable</span><strong>{total_q}</strong></div>
<div><span>Week 10 finals in the feed</span><strong>{n_final} of {len(C.WEEK10_SLATE)}</strong></div>
<div><span>Standings checks that matched</span><strong>{n_match} of {len(verif)}</strong></div>
<div><span>Completed games through Week 9</span><strong>{luck['games']}</strong></div>
<div><span>Luck share of the standings spread</span><strong>{luck['luck_share']:.3f}</strong></div>
</div>
<p class="note">Four clubs are on bye this week ({esc(", ".join(C.BYE_CLUBS_WEEK10))}) and
have no section on the injury report at all. Their absence is published as a bye, never as
health. The capture happened while Week 10 games were still finishing
({n_final} finals, {len(M.live_games())} not final), so the live scores sit in their own
table and never enter the results feed.</p>

<h2 id="categories">Browse by category</h2>
<div class="grid">{cat_cards}</div>

<h2 id="rules">The four rules this pack follows</h2>
<ul>
<li>A value is published only if it was read this session from the official page cited on its
row, or is arithmetic on such values with the derivation shown.</li>
<li>Everything else is an empty cell plus a row on the
<a href="flagged.html">Flagged for review</a> page. Nothing is inferred, imputed or
estimated.</li>
<li>No market price. Every route tried is recorded on the
<a href="correlations.html">exclusions</a> and
<a href="sources.html">sources</a> pages with what the page actually contained.</li>
<li>No profitability claim, and no ranking: the leaderboard is empty because no strategy has
a single prospective forecast.</li>
</ul>

<h2 id="start">If you read one page</h2>
<p class="note">Read the <a href="decision-readiness.html">decision-readiness table</a> first:
it is the whole brief in one table, with the blocking gate and the clearing number on every
row. Then the <a href="questions.html">questions register</a> for what is still unknown, and
the <a href="suggestions.html">suggestions register</a> to choose a path before anything is
implemented.</p>
"""))

    # ---------- decision readiness ----------
    by_cat = {}
    for r in reqs:
        by_cat.setdefault(r["category"], []).append(r)
    sections = []
    for cat in sorted(by_cat):
        rows = by_cat[cat]
        body = ""
        for r in rows:
            cells = []
            for h, v in (
                ("id", r["requirement_id"]), ("requirement", r["requirement"]),
                ("status", r["status"]), ("published", r["what_is_published"]),
                ("gate", r["blocking_gate"]), ("clears at", r["clearing_number"]),
                ("evidence", r["evidence_file"]), ("source", r["official_source_url"]),
            ):
                if h == "status":
                    cell = pill(v)
                elif v:
                    cell = esc(v)
                else:
                    cell = '<span class="blank"></span>'
                cells.append("<td>" + cell + "</td>")
            body += "<tr>" + "".join(cells) + "</tr>"
        head = "".join(
            "<th scope='col'>" + esc(h) + "</th>" for h in
            ("ID", "Requirement", "Status", "What is published today", "Blocking gate",
             "Number that would clear it", "Evidence", "Source")
        )
        sections.append(
            f'<h3>{esc(cat)} <span class="pill">{len(rows)}</span></h3>'
            f'<div class="wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
        )
    # linkify source cells (they are raw URLs in the last column)
    dr_html = "".join(sections)
    for url in sorted({r["official_source_url"] for r in reqs if r["official_source_url"]},
                      key=len, reverse=True):
        dr_html = dr_html.replace(f">{esc(url)}</td>", f">{link(url, 'official')}</td>")

    write(os.path.join(DOCS, "decision-readiness.html"), page(
        "Decision readiness", "decision-readiness.html", f"""
<p class="eyebrow">LANDING TABLE</p>
<h1>One row per requirement</h1>
<p class="lede">Each row states what is published today, the gate that blocks the
requirement, and the number that would clear it. A <strong>blocked</strong> row is not a
failure of effort: it is a requirement whose input does not exist in an official source, and
the clearing number says exactly what would have to change. {len(reqs)} requirements,
{req_counts.get('cleared', 0)} cleared, {req_counts.get('partial', 0)} partial,
{req_counts.get('blocked', 0)} blocked, {req_counts.get('rejected', 0)} rejected,
{req_counts.get('needs review', 0)} needs review.</p>
{dr_html}
<p class="note">Every row links the official page closest to that requirement. Where a
requirement is a property of this repository rather than of an external page, the source cell
points at the official page its evidence depends on, and the evidence column names the file
that implements it.</p>
"""))

    # ---------- injuries ----------
    write(os.path.join(DOCS, "injuries.html"), page(
        "Week 10 injury report", "injuries.html", f"""
<p class="eyebrow">CAPTURED {esc(CAPTURE)}</p>
<h1>Official Week 10 injury report</h1>
<p class="lede">{len(IN.rows())} rows across {len(IN.clubs_on_report())} clubs, transcribed
from the official injury report. {total_out} players are designated Out, {total_q}
Questionable. An empty injury or game-status cell is exactly what the official table
printed: it is not a missing value and it is not a clearance. The four bye clubs
({esc(", ".join(C.BYE_CLUBS_WEEK10))}) have no section at all.
{link(C.SOURCE_URL['S1'], 'official injury report')}</p>

<h2>Per-club rollup</h2>
{table(["Club", "Rows", "Out", "Doubtful", "Questionable", "No game status", "DNP",
        "Limited", "Full", "Offense Out", "Defense Out", "Source"],
       [[r["club"], r["rows_on_report"], r["out"], r["doubtful"], r["questionable"],
         r["listed_no_game_status"], r["dnp"], r["limited"], r["full"], r["offense_out"],
         r["defense_out"], r["source_url"]] for r in roll])}
<p class="note"><strong>No game status</strong> counts rows the official table left blank.
Those players are on the report and unclassified; they are not available.</p>

<h2>Every row</h2>
{table(["Club", "Player", "Pos", "Unit", "Side", "Injury", "Practice status", "Game status",
        "Source"],
       [[r["club"], r["player"], r["position"], r["unit"], r["side"], r["injury"],
         r["practice_status"], r["game_status"], r["source_url"]] for r in IN.rows()])}
"""))

    # ---------- depth ----------
    ann = IN.announced_starters()
    write(os.path.join(DOCS, "depth.html"), page(
        "Depth, starters and the route problem", "depth.html", f"""
<p class="eyebrow">REPLACEMENT DEPTH</p>
<h1>What the official pages will and will not say</h1>
<p class="lede">The brief asks for the depth of the replacement, not just the fact of one.
The official injury report publishes the fact and not the depth: it names no replacement and
gives no order. So this pack publishes <strong>floors</strong> - how many Out rows sit in
each club and unit - and leaves the replacement column empty rather than filling it in.</p>

<h2>The route probe</h2>
{table(["Route", "URL", "Result", "Depth order published", "Club-hosted depth link", "Notes"],
       [[r, u, h, d, cl, n] for r, u, h, d, cl, n in C.DEPTH_ROUTE_PROBES])}
<p class="note">This is the answer to <em>resolve the depth-order source before building the
feature</em>. Route (a), the per-club depth page on nfl.com, does not exist: it returns 404.
The roster route is live but publishes no depth order; it does link a depth chart on the
club's own domain, which is a candidate route that is unverified for the other 31 clubs.
Route (b), snap counts, found no official source. The feature is therefore not built.</p>

<h2>Announced starters (the only named replacements published here)</h2>
{table(["Club", "Player", "Pos", "For", "Date in story", "Headline", "Source"],
       [[r["club"], r["player"], r["position"], r["announced_for"],
         r["date_in_official_story"], r["headline"], r["source_url"]] for r in ann])}
<p class="note">These are the only rows where a named replacement appears, and each one
carries the official page that publishes the name. Nothing here is derived from a depth
chart, a jersey number, experience or salary.</p>

<h2>Dated roster events (trades are not starter announcements)</h2>
{table(["Date", "From", "To", "Player", "Event", "Starter announced", "Note", "Source"],
       [[r["date"], r["club_from"], r["club_to"], r["player"], r["event"],
         r["starter_announced"], r["note"], r["source_url"]] for r in IN.roster_events()])}

<h2>Replacement floors by club and unit</h2>
{table(["Club", "Unit", "Side", "On report", "Out (floor)", "Questionable", "Doubtful",
        "Replacement named", "Note", "Source"],
       [[r["club"], r["unit"], r["side"], r["on_report"], r["out_floor"], r["questionable"],
         r["doubtful"], r["replacement_named"], r["note"], r["source_url"]] for r in depth])}
<p class="note">{len(depth)} club/unit rows. Every <em>Replacement named</em> cell is
intentionally empty: the report names none.</p>
"""))

    # ---------- inactives ----------
    w9 = IN.week9_inactive_rows()
    write(os.path.join(DOCS, "inactives.html"), page(
        "Official inactives and venues", "inactives.html", f"""
<p class="eyebrow">WEEK 9 &#183; OFFICIAL INACTIVE LISTS</p>
<h1>Inactives and the venue question</h1>
<p class="lede">NFL.com publishes an official inactive list for every Sunday game, and unlike
the by-week schedule page it prints WHERE each game is played. This pack transcribed all 13
Week 9 games: {len(w9)} inactive rows and {len(IN.venues())} venues.
{link(C.SOURCE_URL['S5'], 'official Week 9 inactives')}</p>

<h2>Venues</h2>
{table(["Week", "Game", "Away", "Home", "Kickoff (ET)", "Venue", "Source"],
       [[v["week"], v["game_slug"], v["away"], v["home"], v["kickoff_et"], v["venue"],
         v["source_url"]] for v in IN.venues()])}
<p class="note">Venues for Week 10 are blank: the by-week schedule page prints no venue, and
the Week 10 inactives page had not been published at capture time. This is flag
48217-F07.</p>

<h2>Every inactive row</h2>
{table(["Game", "Club", "Player", "Pos", "Emergency 3rd QB", "Venue", "Kickoff", "Source"],
       [[r["game_slug"], r["club"], r["player"], r["position"], r["emergency_third_qb"],
         r["venue"], r["kickoff_et"], r["source_url"]] for r in w9])}
<p class="note">Emergency third quarterbacks are marked, because they are listed as inactive
but are not unavailable in the same sense as the others.</p>
"""))

    # ---------- schedule and results ----------
    write(os.path.join(DOCS, "schedule-results.html"), page(
        "Week 10 schedule and results", "schedule-results.html", f"""
<p class="eyebrow">CAPTURED {esc(CAPTURE)} &#183; GAMES STILL FINISHING</p>
<h1>Schedule and the results feed</h1>
<p class="lede">The capture happened while Week 10 was being played. {n_final} of
{len(C.WEEK10_SLATE)} games had gone final; the rest are published separately and are never
allowed into the results feed. {link(C.SOURCE_URL['S2'], 'official Week 10 schedule')}</p>

<h2>Results feed (finals only)</h2>
{table(["Date", "Kickoff", "Away", "Score", "Home", "Score", "Winner", "Margin", "Total",
        "Source"],
       [[g["date"], g["kickoff_et"], g["away"], g["away_points"], g["home"],
         g["home_points"], g["winner"], g["margin"], g["total_points"], g["source_url"]]
        for g in M.final_games()])}

<h2>In progress or not started (excluded from the feed)</h2>
{table(["Date", "Kickoff", "Away", "Home", "Status", "Quarter", "Score shown", "Note",
        "Source"],
       [[g["date"], g["kickoff_et"], g["away"], g["home"], g["status"], g.get("quarter", ""),
         (f'{g["away_points"]}-{g["home_points"]}' if g["away_points"] else ""),
         "not used as a result", g["source_url"]] for g in M.live_games()])}

<h2>Full Week 10 slate</h2>
{table(["Game", "Date", "Kickoff (ET)", "Away", "Home", "Status", "Network", "Venue",
        "Source"],
       [[s["game_slug"], s["date"], s["kickoff_et"], s["away"], s["home"], s["status"],
         s["network"], s["venue"], s["source_url"]] for s in slate_rows])}
<p class="note">Clubs on bye in Week 10: {esc(", ".join(C.BYE_CLUBS_WEEK10))}. They have no
fixture and no injury section, which are two different facts and are published as such.</p>
"""))

    # ---------- standings ----------
    write(os.path.join(DOCS, "standings.html"), page(
        "Point-in-time standings", "standings.html", f"""
<p class="eyebrow">RECONSTRUCTED, THEN CHECKED</p>
<h1>The standings page lies by omission</h1>
<p class="lede">The official standings page renders live. At capture time it already
contained the nine Week 10 games that had finished and excluded the three still going. Read
as a through-Week-9 table it silently mixes two vintages. So the through-Week-9 table below
is reconstructed by subtracting those nine games, and then checked against an independent
official page that printed each club's record before kickoff: <strong>{n_match} of
{len(verif)} matched</strong>.</p>

<h2>Verification against the official pregame page</h2>
{table(["Club", "Record on the pregame page", "Expected from arithmetic", "Match", "Basis",
        "Source"],
       [[v["club"], v["record_on_pregame_page"], v["expected_from_arithmetic"],
         v["match"], v["basis"], v["source_url"]] for v in verif])}

<h2>Integrity checks</h2>
{table(["Check", "Value A", "Value B", "Result", "Note", "Source"],
       [[c["check"], c["value_a"], c["value_b"], c["result"], c["note"],
         C.SOURCE_URL["S3"]] for c in checks])}
<p class="note">Points for equals points against across the league, wins equal losses, and
the implied completed-game count is {luck['games']} - which is the 136-game corpus the brief
refers to, confirmed arithmetically rather than asserted.</p>

<h2>Through Week 9 (reconstructed)</h2>
{table(["Club", "Name", "W", "L", "T", "G", "Win%", "PF", "PA", "Net", "PF/G", "PA/G",
        "Margin/G", "Source"],
       [[r["club"], r["club_name"], r["w"], r["l"], r["t"], r["games"],
         f'{r["win_pct"]:.3f}', r["pf"], r["pa"], r["net_points"],
         f'{r["pf_per_game"]:.2f}', f'{r["pa_per_game"]:.2f}',
         f'{r["margin_per_game"]:.2f}', C.SOURCE_URL["S3"]]
        for r in pit],
       num_cols={"W", "L", "T", "G", "Win%", "PF", "PA", "Net", "PF/G", "PA/G", "Margin/G"})}

<h2>What the page actually rendered (for comparison)</h2>
{table(["Club", "W", "L", "T", "PF", "PA", "Home", "Road", "Div", "Conf", "Streak",
        "Source"],
       [[c, w, l, t, pf, pa, hm, rd, dv, cf, st, C.SOURCE_URL["S3"]]
        for c, w, l, t, _pct, pf, pa, _net, hm, rd, dv, cf, st in C.STANDINGS_RENDER],
       num_cols={"W", "L", "T", "PF", "PA"})}

<h2>Rating, explicitly not opponent-adjusted</h2>
{table(["Club", "Rating (margin/game)", "Win%", "PF/G", "PA/G", "Opponent adjusted",
        "Blocking gate", "Source"],
       [[r["club"], f'{r["rating_ppg"]:.2f}', f'{r["win_pct"]:.3f}',
         f'{r["pf_per_game"]:.2f}', f'{r["pa_per_game"]:.2f}', r["opponent_adjusted"],
         r["blocking_gate"], C.SOURCE_URL["S3"]] for r in M.naive_ratings(pit)],
       num_cols={"Rating (margin/game)", "Win%", "PF/G", "PA/G"})}
<p class="note">This rating is margin per game with no opponent adjustment, because the
game-by-game log does not exist yet. It is published so the size of the gap is visible, and
it is labelled unusable for origination until gate G3 clears.</p>
"""))

    # ---------- transactions ----------
    write(os.path.join(DOCS, "transactions.html"), page(
        "Transactions and the reserve list", "transactions.html", f"""
<p class="eyebrow">ROSTER TURNOVER AS A FIRST-CLASS EVENT</p>
<h1>Trades and Reserve/Injured moves</h1>
<p class="lede">A player missing from the injury report is not necessarily healthy; he may be
on a reserve list. The official transactions hub publishes both streams with dates, so
{len(C.RESERVE_LIST_NOV_2026)} November reserve moves and {len(C.TRADES_NOV_2026)} November
trades are captured and cross-walked against the Week 10 report.
{link(C.SOURCE_URL['S7'], 'official reserve list')}</p>

<h2>Reserve list, cross-walked to the injury report</h2>
{table(["Date", "Club", "Player", "Transaction", "Also on the Week 10 report",
        "Interpretation", "Source"],
       [[r["date"], r["club"], r["player"], r["transaction"], r["on_week10_injury_report"],
         r["interpretation"], r["source_url"]] for r in IN.reserve_coverage()])}
<p class="note">{sum(1 for r in IN.reserve_coverage() if r['on_week10_injury_report'] == 'yes')}
of the {len(IN.reserve_coverage())} reserve players also appear on the Week 10 report. The
rest are absent from the report precisely because they are on a reserve list - which is why
absence can never be published as availability.</p>

<h2>November trades</h2>
{table(["Date", "From", "To", "Player", "Event", "Note", "Source"],
       [[r["date"], r["club_from"], r["club_to"], r["player"], r["event"], r["note"],
         r["source_url"]] for r in IN.roster_events()])}
<p class="note">A trade is a roster event, not a starter announcement: the transactions page
does not say who starts. That distinction is why the two tables are separate.</p>
"""))

    # ---------- correlations ----------
    write(os.path.join(DOCS, "correlations.html"), page(
        "Correlations, with n", "correlations.html", f"""
<p class="eyebrow">MEASURED {len(cors)} &#183; EXCLUDED {len(X.exclusions())}</p>
<h1>Correlations from official numbers only</h1>
<p class="lede">Every estimate below is computed from numbers read off an official page this
session, and every row carries its n, its unit, its interval and one URL per axis. The point
of publishing these is not to claim a signal: with n between {min(c['n'] for c in cors)} and
{max(c['n'] for c in cors)}, none of them supports one. The point is that the method is
checkable and the sample size is visible.</p>

<h2>Measured</h2>
{table(["ID", "X", "Y", "n", "Unit", "Method", "Estimate", "CI low", "CI high", "p",
        "X source", "Y source"],
       [[c["id"], c["x_axis"], c["y_axis"], c["n"], c["unit"], c["method"], c["estimate"],
         c["ci_low"], c["ci_high"], c["p_value"], c["x_source_url"], c["y_source_url"]]
        for c in cors],
       num_cols={"n", "Estimate", "CI low", "CI high", "p"})}
<p class="note">Every interval here straddles zero or is computed on a sample far too small to
decide anything. That is the finding, not a footnote.</p>

<h2>'Questionable', measured instead of assumed</h2>
{table(["Designation", "Sample", "Published resolutions", "Definite", "Active", "Inactive",
        "Play rate", "CI low", "CI high", "Usable as a feature", "Gate", "Source"],
       [[r["designation"], r["sample"], r["n_published_resolutions"], r["n_definite"],
         r["n_active"], r["n_inactive"], r["play_rate"], r["ci_low"], r["ci_high"],
         r["usable_as_feature"], r["blocking_gate"], r["source_url"]]
        for r in X.designation_calibration()],
       num_cols={"Published resolutions", "Definite", "Active", "Inactive", "Play rate",
                 "CI low", "CI high"})}
<p class="note">The one number available comes from a non-random sample: it is the set of
players NFL.com chose to write about, which skews to starters and to genuinely doubtful
cases. The interval is published and the label is marked unusable as a feature until gate G6
clears at 200 pairs.</p>

<h2>Candidates deliberately not estimated</h2>
{table(["ID", "Candidate", "Why not", "What would clear it", "Source"],
       [[e["id"], e["candidate"], e["why_not"], e["what_would_clear_it"], e["source_url"]]
        for e in X.exclusions()])}
"""))

    # ---------- luck ----------
    write(os.path.join(DOCS, "luck.html"), page(
        "Removal of luck", "luck.html", f"""
<p class="eyebrow">{luck['games']} COMPLETED GAMES &#183; {luck['clubs']} CLUBS</p>
<h1>How much of the table is luck</h1>
<p class="lede">Before any strategy can claim skill, the spread it is trying to explain has
to be separated from the spread a coin flip would produce anyway. Using only official
numbers: the observed win-percentage variance across the 32 clubs is compared with the
binomial variance of a fair coin flip over the same number of games.</p>

<div class="kv">
<div><span>Observed win-pct variance</span><strong>{luck['obs_win_pct_variance']:.6f}</strong></div>
<div><span>Coin-flip null variance</span><strong>{luck['null_win_pct_variance']:.6f}</strong></div>
<div><span>Implied skill variance</span><strong>{luck['skill_variance']:.6f}</strong></div>
<div><span>Luck share</span><strong>{luck['luck_share']:.3f}</strong></div>
<div><span>Margin SD (points/game)</span><strong>{luck['margin_sd']:.3f}</strong></div>
<div><span>League points per game</span><strong>{luck['league_ppg']:.3f}</strong></div>
</div>

<h2>Derivation</h2>
<ul>
<li><code>observed</code> = population variance of win percentage across the 32 clubs in the
reconstructed through-Week-9 table.</li>
<li><code>null</code> = mean over clubs of <code>0.25 / games</code>: the variance of a fair
coin flip over that many games, i.e. the spread with no skill difference at all.</li>
<li><code>skill</code> = observed &#8722; null. <code>luck share</code> = null / observed.</li>
</ul>
<p class="note">Roughly {luck['luck_share'] * 100:.0f}% of the win-percentage spread across
the league at this point in the season is what a coin flip would produce anyway. Any model
claiming to explain the standings has to beat that, not merely correlate with it. This is a
share, not a probability, and it is one season slice.</p>

<h2>What is blocked</h2>
<p class="note">The strategy-level version of this panel - how much of a strategy's own
record is luck - needs 100 prospective graded forecasts (gate G8). There are zero, so that
number is blank rather than guessed. {link(C.SOURCE_URL['S3'], 'official standings')}</p>
"""))

    # ---------- strategies ----------
    srows = G.strategy_rows()
    write(os.path.join(DOCS, "strategies.html"), page(
        "Pre-registered strategies", "strategies.html", f"""
<p class="eyebrow">{len(srows)} DEFINITIONS FROZEN BEFORE ANY RESULT</p>
<h1>Strategies, and why none is ranked</h1>
<p class="lede">Every definition below is frozen in this repository before its evaluation
window opens. That is the pre-registration: the file is the registration. There is no
leaderboard because there is no prospective forecast - not one of these strategies has
observed a result yet, and a ranking built on anything else would be a backtest wearing a
record's clothes.</p>

<h2>Registry</h2>
{table(["ID", "Name", "Family", "Frozen definition", "Benchmark", "Window", "Gates",
        "Uncleared", "Status", "Source"],
       [[s["strategy_id"], s["name"], s["family"], s["frozen_definition"], s["benchmark"],
         s["evaluation_window"], s["required_gates"], s["gates_uncleared"], s["status"],
         s["source_url"]]
        for s in srows])}

<h2>What would change our mind, on both sides</h2>
{table(["ID", "Promote if", "Demote if", "Source"],
       [[s["strategy_id"], s["what_would_change_our_mind"].split(". Demote if ")[0],
         "Demote if " + s["what_would_change_our_mind"].split(". Demote if ")[1]
         if ". Demote if " in s["what_would_change_our_mind"] else "", s["source_url"]]
        for s in srows])}

<h2>Leaderboard</h2>
{table(["Division", "Ranked", "Qualified", "Note", "Source"],
       [[r["division"], r["ranked_strategies"], r["qualified_strategies"], r["note"],
         r["source_url"]]
        for r in G.leaderboard_rows()],
       num_cols={"Ranked", "Qualified"})}
<p class="note">Five divisions, zero rows in each. The divisions exist before the rows do so
that a parlay can never be ranked against a single.</p>

<h2>Reward tiers</h2>
{table(["Tier", "Condition", "Reward", "Monetary", "Evidence"],
       [[t["tier"], t["condition"], t["reward"], t["monetary"], t["evidence"]]
        for t in G.REWARD_TIERS],
       internal="governance tiers, no external source; conditions are the gates page")}
<p class="note">Rewards are research priority only. No tier carries money, and no tier is
reachable while a required gate is open.</p>
"""))

    # ---------- gates ----------
    write(os.path.join(DOCS, "validation-gates.html"), page(
        "Validation gates", "validation-gates.html", f"""
<p class="eyebrow">{sum(1 for g in G.GATES if g[5] == 'pass')} OF {len(G.GATES)} PASS</p>
<h1>Gates, with the number that opens each one</h1>
<p class="lede">A gate is a binary that must pass before a strategy moves from paper to live.
Each one names a number, so "not yet" is always measurable.</p>
{table(["ID", "Gate", "Requirement", "Threshold (the number that clears it)", "Observed now",
        "Status", "Source"],
       [[r["gate_id"], r["name"], r["requirement"], r["threshold"], r["observed"],
         r["status"], r["source_url"]] for r in G.gate_rows()])}
<p class="note">The one gate that passes is the drift alarm: the pack's checker pins row
counts and required fields for every table and exits non-zero when one moves. Every other
gate is open, and each names what would close it.</p>
"""))

    # ---------- questions ----------
    write(os.path.join(DOCS, "questions.html"), page(
        "Questions, information, answers", "questions.html", f"""
<p class="eyebrow">{len(A.questions())} OPEN QUESTIONS</p>
<h1>What has to be known before a decision is reasonable</h1>
<p class="lede">Each row states the decision the question blocks, what we already have, what
is missing, and the concrete path to discover the missing part. A question is not answered
with an opinion here; it is answered with a page that can be read.</p>
{table(["ID", "Decision blocked", "Question", "What we have", "What is missing",
        "Discovery path", "Source"],
       [[q["question_id"], q["decision_blocked"], q["question"], q["what_we_have"],
         q["what_is_missing"], q["discovery_path"], q["official_source_url"]]
        for q in A.questions()])}
"""))

    # ---------- suggestions ----------
    write(os.path.join(DOCS, "suggestions.html"), page(
        "Suggestions for review", "suggestions.html", f"""
<p class="eyebrow">{len(A.suggestions())} SUGGESTIONS &#183; NOTHING APPLIED AUTOMATICALLY</p>
<h1>Choose the path before anything is built</h1>
<p class="lede">This is the review page. Each row says what the change would unblock, the
options, and what it costs to do nothing. None of these has been implemented: the point of
the page is that someone chooses first.</p>
{table(["ID", "Suggestion", "Category", "What it changes", "Options",
        "Cost of doing nothing", "Priority"],
       [[s["suggestion_id"], s["title"], s["category"], s["what_it_changes"], s["options"],
         s["cost_of_doing_nothing"], s["priority"]] for s in A.suggestions()],
       internal="proposals for review, not published facts; none has been implemented")}

<h2>How to read the options</h2>
<ul>
<li><strong>A</strong> is the full version: it closes the requirement outright.</li>
<li><strong>B</strong> is the partial version: it buys most of the value at a fraction of the
work, and is often the right first move.</li>
<li><strong>C</strong> is to decline deliberately, which is a decision rather than an
omission - but the blocking gate stays open and that is recorded on the
<a href="decision-readiness.html">decision-readiness table</a>.</li>
</ul>
"""))

    # ---------- repo review ----------
    write(os.path.join(DOCS, "repo-review.html"), page(
        "Repository review", "repo-review.html", f"""
<p class="eyebrow">{len(C.REPO_FINDINGS)} FINDINGS</p>
<h1>Line-by-line review, with the page that settles each one</h1>
<p class="lede">Findings are split by how they were settled: verified against an official
page during this session, verified in the repository's own records, or observed and needing
an owner decision. Nothing here is asserted from memory.</p>
{table(["ID", "Area", "Finding", "How it was checked", "Status", "Effect", "Source"],
       [[i, a, f, h, s, e, u] for i, a, f, h, s, e, u in C.REPO_FINDINGS])}
"""))

    # ---------- sources ----------
    write(os.path.join(DOCS, "sources.html"), page(
        "Sources", "sources.html", f"""
<p class="eyebrow">{len(C.SOURCES)} OFFICIAL PAGES &#183; READ {esc(C.CAPTURE_DATE_UTC)}</p>
<h1>Every page this pack read</h1>
<p class="lede">Clock times are UTC. The chunk column records how the page was served and
which parts were actually read, because a long page served in chunks can be silently
truncated.</p>
{table(["ID", "URL", "Read at (UTC)", "Chunks", "Read", "What it supports"],
       [[s, u, t, c, cr, w] for s, u, t, c, cr, w in C.SOURCES])}

<h2>Routes considered for a price, and what they contained</h2>
{table(["Route", "Kind", "Result", "What the page actually contains", "Conclusion"],
       [[r, k, res, w, con] for r, k, res, w, con in C.PRICE_CAPTURE_ATTEMPTS],
       internal="routes considered; the one row with no link is a route deliberately not "
                "consulted")}
<p class="note">No route produced a price. The cells stay blank rather than being filled with
an estimate, and that is flag 48217-F01. {link(C.SOURCE_URL['S2'], 'official schedule')}</p>
"""))

    # ---------- flagged ----------
    write(os.path.join(DOCS, "flagged.html"), page(
        "Flagged for review", "flagged.html", f"""
<p class="eyebrow">{len(FL.flags())} FLAGS &#183; BLANK NEVER MEANS ZERO</p>
<h1>Every blank and every caveat</h1>
<p class="lede">This page exists so that no empty cell in this pack is silent. Each flag says
which cells are empty or qualified, why, and what would fill them. Items flagged here do not
block anything else: they are published so they can be reviewed.</p>
{table(["ID", "Severity", "Affected tables", "What is blank or caveated", "Why",
        "What would fill it", "Source"],
       [[f[0], f[1], f[2], f[3], f[4], f[5], f[6]] for f in FL.FLAGS])}

<h2>Blank-cell audit</h2>
{table(["Table", "Rows", "Cols", "Cells", "Blanks", "% blank", "Why blank", "Flags"],
       [[a["table"], a["rows"], a["columns"], a["cells"], a["blank_cells"], a["blank_pct"],
         a["why_blank"], a["flag_ids"]] for a in audit],
       num_cols={"Rows", "Cols", "Cells", "Blanks", "% blank"},
       internal="counts of cells in this pack's own tables, not external facts")}
<p class="note">The injury table's blank injury and game-status cells are what the official
page printed, not gaps in our capture. The originated-lines schema is blank because there is
no licensed price source. Both are expected and both are flagged.</p>
"""))

    # ---------- executive summary ----------
    write(os.path.join(DOCS, "executive-summary.html"), page(
        "Executive summary", "executive-summary.html", f"""
<p class="eyebrow">EXECUTIVE SUMMARY &#183; SESSION 48217A55</p>
<h1>What is true, what is blocked, and what each block costs</h1>

<h2>The short version</h2>
<p class="lede">This pack read {len(C.SOURCES)} official NFL pages on
{esc(C.CAPTURE_DATE_UTC)} and published what they say, row by row, with a source link on
every row. It captured the full Week 10 injury report ({len(IN.rows())} rows,
{len(IN.clubs_on_report())} clubs), the Week 10 slate and its {n_final} completed games, the
32-club standings, {len(C.RESERVE_LIST_NOV_2026)} reserve-list moves,
{len(C.TRADES_NOV_2026)} trades and {len(w9)} official Week 9 inactive rows. It originated
no line, ranked no strategy and claimed no edge, because the inputs those need are not
available from any official source.</p>

<h2>Numbers a reviewer can check in one step each</h2>
<div class="kv">
<div><span>Injury rows vs clubs</span><strong>{len(IN.rows())} / {len(IN.clubs_on_report())}</strong></div>
<div><span>Out / Questionable</span><strong>{total_out} / {total_q}</strong></div>
<div><span>Standings checks matched</span><strong>{n_match} of {len(verif)}</strong></div>
<div><span>Points for vs against, league-wide</span><strong>{checks[0]['value_a']} = {checks[0]['value_b']}</strong></div>
<div><span>Completed games through Week 9</span><strong>{luck['games']}</strong></div>
<div><span>Luck share of the standings spread</span><strong>{luck['luck_share']:.3f}</strong></div>
<div><span>Qualified strategies</span><strong>0</strong></div>
<div><span>Gates passing</span><strong>{sum(1 for g in G.GATES if g[5] == 'pass')} of {len(G.GATES)}</strong></div>
</div>

<h2>What is genuinely new here</h2>
<ul>
<li><strong>The standings page is a live table, and that is handled.</strong> The
through-Week-9 table is reconstructed by subtracting the nine completed Week 10 games and
then checked against an independent official page: {n_match} of {len(verif)} matched. The
brief's 136-game corpus is confirmed arithmetically, not assumed.</li>
<li><strong>The depth route question is answered, not deferred.</strong> nfl.com's per-club
depth page is a 404; the roster page publishes no depth order but links a club-hosted depth
chart. The replacement-depth feature is therefore not built, and the report's Out counts are
published as floors instead.</li>
<li><strong>The reserve list closes the "not listed means available" hole.</strong>
{len(C.RESERVE_LIST_NOV_2026)} November reserve moves are cross-walked against the injury
report, and {sum(1 for r in IN.reserve_coverage() if r['on_week10_injury_report'] == 'yes')}
of them also appear on it.</li>
<li><strong>Five named starters are published, and only five</strong> - each with the
official page that names them. No replacement is inferred anywhere.</li>
<li><strong>Luck is quantified before any skill claim:</strong>
{luck['luck_share'] * 100:.0f}% of the win-percentage spread is what a coin flip would
produce.</li>
</ul>

<h2>What is blocked, and by what</h2>
<p class="note">Thirty-three of the {len(reqs)} requirements are blocked. Nearly all of them
trace to three missing inputs: operator prices (no official or licensed source), a depth
order (no official route on nfl.com), and snap counts (no official source found). Each
blocked row on the <a href="decision-readiness.html">decision-readiness table</a> names the
number that would clear it.</p>

<h2>Irregularities worth your attention</h2>
<ul>
<li>The November reserve-list table's earliest row is dated 11/07, yet an official NFL.com
story dated 2026-11-05 reports a Reserve/Injured move with no row in that table. The route
may be truncated (flag 48217-F15).</li>
<li>The injury report groups players under clubs that read as wrong at first glance. One was
checked end to end - Kenneth Walker III is on the Kansas City roster - and it held. The
other {len(IN.rows()) - 1} rows are unchecked (flag 48217-F13).</li>
<li>The by-week schedule page prints no venue, so Week 10 venues are blank; the inactives
page does print venues, and 13 Week 9 venues were transcribed from it (flag 48217-F07).</li>
<li>Eight overlapping NFL packs now exist in this repository. Nothing tells a reader which is
authoritative. The decision-readiness table is this pack's answer.</li>
</ul>

<h2>What to decide next</h2>
<p class="note">The <a href="questions.html">questions register</a> has
{len(A.questions())} rows and the <a href="suggestions.html">suggestions register</a> has
{len(A.suggestions())}. The three decisions that unblock the most are: where prices come
from (Q01/Q02), whether to commit to reading Weeks 1&#8211;9 game by game (SUG-01), and
whether to probe all 32 club-hosted depth pages (SUG-02).</p>
"""))

    print(f"built {len(tables)} CSV tables in data/nfl_48217a55")
    print(f"built {len(PAGES)} pages in docs/nfl-48217a55")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="run the verifier after building")
    args = ap.parse_args()
    rc = main()
    if args.check and rc == 0:
        sys.exit(subprocess.call([sys.executable, os.path.join(REPO, "scripts",
                                                               "check_nfl_48217a55.py")]))
    sys.exit(rc)
