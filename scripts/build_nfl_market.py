#!/usr/bin/env python3
"""Build the NFL market data pack (CSVs) and the zero-input GitHub Pages site.

Usage
-----
    python3 scripts/build_nfl_market.py            # write data + site
    python3 scripts/build_nfl_market.py --check    # also run the verifier
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

from nfl_market import backtest as B  # noqa: E402
from nfl_market import capture as C  # noqa: E402
from nfl_market import correlations as K  # noqa: E402
from nfl_market import demotion as DM  # noqa: E402
from nfl_market import depth as DEP  # noqa: E402
from nfl_market import gates as G  # noqa: E402
from nfl_market import leaderboard as L  # noqa: E402
from nfl_market import model as M  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_market")
DOCS = os.path.join(REPO, "docs", "nfl-market")
CAPTURE_DATE = C.CAPTURE_DATE

CSS = """
:root{--bg:#0d1117;--panel:#151b23;--panel2:#1b232d;--line:#293341;--ink:#e6edf3;
--muted:#93a1b0;--accent:#4da3ff;--good:#3fb950;--warn:#d29922;--bad:#f85149;--blank:#6e7681}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15.5px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
nav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:10px 16px;
background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:9}
nav .brand{font-weight:700;letter-spacing:.03em;margin-right:8px;color:var(--ink)}
nav a{padding:5px 9px;border-radius:6px;font-size:13.5px;color:var(--ink);
background:var(--panel2);border:1px solid var(--line)}
nav a.on{background:#22385a;border-color:var(--accent)}
main{max-width:1240px;margin:0 auto;padding:22px 16px 70px}
h1{font-size:27px;line-height:1.2;margin:8px 0 10px}
h2{font-size:20px;margin:32px 0 8px;padding-top:8px;border-top:1px solid var(--line)}
h3{font-size:16px;margin:20px 0 6px}
p{margin:8px 0}
.eyebrow{color:var(--accent);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;margin:0 0 4px}
.lede{color:var(--muted);max-width:82ch}
.hero{background:linear-gradient(180deg,#16202b,#11161d);border:1px solid var(--line);
border-radius:14px;padding:22px;margin-bottom:16px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px;margin:14px 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
.tile b{display:block;font-size:21px}.tile span{color:var(--muted);font-size:12px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:10px 0 18px}
table{border-collapse:collapse;width:100%;font-size:13px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--panel2);font-size:11.5px;letter-spacing:.03em;text-transform:uppercase;
color:var(--muted);white-space:nowrap;position:sticky;top:50px}
tbody tr:hover{background:#1a222c}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.blank{color:var(--blank);font-style:italic;font-size:12px}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;
border:1px solid var(--line);background:#1b2430;white-space:nowrap}
.ok{color:var(--good)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:8px;padding:11px 13px;margin:12px 0}
.note.bad{border-left-color:var(--bad)}.note.warn{border-left-color:var(--warn)}
ul,ol{margin:8px 0 8px 20px}li{margin:4px 0}
code{background:#1b2430;border:1px solid var(--line);border-radius:4px;padding:1px 5px;font-size:12.5px}
footer{color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);
margin-top:30px;padding-top:14px}
"""

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("lines.html", "Originated lines"),
    ("snapshots.html", "Price snapshots"),
    ("results.html", "Verified results"),
    ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Validation gates"),
    ("correlations.html", "Correlations"),
    ("depth.html", "Depth & injuries"),
    ("demotion.html", "Demotion gate"),
    ("decision-ledger.html", "Decision questions"),
    ("suggestions.html", "Suggestions"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
    ("repo-review.html", "Repo review"),
]


# --------------------------------------------------------------------- helpers
def write_csv(name, rows, columns=None):
    path = os.path.join(DATA, name)
    if not rows:
        raise SystemExit("refusing to write empty csv: %s" % name)
    cols = columns or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return path


def esc(v):
    return html.escape("" if v is None else str(v))


def cell(v, num=False, maxlen=170):
    if v is None or v == "":
        return '<td class="blank">blank</td>'
    s = str(v)
    if len(s) > maxlen:
        s = s[: maxlen - 1] + "\u2026"
    cls = ' class="num"' if num else ""
    return "<td%s>%s</td>" % (cls, esc(s))


def link_cell(url):
    if not url:
        return '<td class="blank">blank</td>'
    return '<td><a href="%s" rel="noopener">source</a></td>' % esc(url)


def status_pill(v):
    v = "" if v is None else str(v)
    cls = "ok" if v in ("open", "published", "final_verified", "done", "yes") else (
        "bad" if v in ("closed", "refused_no_official_source", "no") else "warn")
    return '<span class="pill %s">%s</span>' % (cls, esc(v or "blank"))


def table(headers, rows, num_cols=(), status_cols=(), link_cols=(), maxlen=170):
    out = ['<div class="wrap"><table><thead><tr>']
    for h in headers:
        out.append("<th>%s</th>" % esc(h))
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for h in headers:
            v = r.get(h)
            if h in status_cols:
                out.append("<td>%s</td>" % status_pill(v))
            elif h in link_cols:
                out.append(link_cell(v))
            else:
                out.append(cell(v, num=h in num_cols, maxlen=maxlen))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def page(slug, title, body, subtitle=""):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (h, ' class="on"' if h == slug else "", esc(t)) for h, t in NAV
    )
    doc = (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>%s \u00b7 NFL own-line desk</title><style>%s</style></head><body>"
        "<nav><span class=\"brand\">NFL Own-Line Desk</span>%s</nav>"
        "<main><p class=\"eyebrow\">NFL market pack \u00b7 captured %s</p>"
        "<h1>%s</h1>%s%s"
        "<footer>Every value on this site is either transcribed from an official NFL-family page "
        "on %s or computed from those transcriptions by <code>src/nfl_market</code>. Blank cells are "
        "values that could not be confirmed from an official source; they are listed on the "
        "<a href=\"flagged.html\">Flagged for review</a> page. No profitability claim is made "
        "anywhere on this site.</footer></main></body></html>\n"
    ) % (esc(title), CSS, nav, CAPTURE_DATE, esc(title), subtitle, body, CAPTURE_DATE)
    with open(os.path.join(DOCS, slug), "w", encoding="utf-8") as fh:
        fh.write(doc)
    return slug


# ------------------------------------------------------------------ data build
def build_data():
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(DOCS, exist_ok=True)

    datasets = {}

    # 1. Standings
    st = []
    for abbr, w, l, t, pf, pa in C.STANDINGS:
        st.append(
            {
                "team_abbr": abbr,
                "wins": w,
                "losses": l,
                "ties": t,
                "games_played": w + l + t,
                "win_pct": round((w + 0.5 * t) / (w + l + t), 4),
                "points_for": pf,
                "points_against": pa,
                "point_diff": pf - pa,
                "points_for_per_game": round(pf / (w + l + t), 2),
                "points_against_per_game": round(pa / (w + l + t), 2),
                "computed_fields": "win_pct,point_diff,points_for_per_game,points_against_per_game",
                "official_source_url": C.CAPTURES["standings"]["url"],
                "retrieved_utc": CAPTURE_DATE,
            }
        )
    datasets["standings.csv"] = write_csv("standings.csv", st)

    # 2. Results feed
    res = B.results_rows()
    for r in res:
        r["official_source_url"] = r.pop("official_source_url")
    datasets["results.csv"] = write_csv("results.csv", res)

    # 3. Slate
    slate = []
    for week, day, date, kick, net, away, home in C.SLATE_W10:
        slate.append(
            {
                "game_key": "W10-%s-%s" % (away, home),
                "week": week,
                "season": 2026,
                "day": day,
                "date": date,
                "kickoff_et": kick,
                "network": net,
                "away": away,
                "home": home,
                "official_source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
                "retrieved_utc": CAPTURE_DATE,
            }
        )
    datasets["slate_week10.csv"] = write_csv("slate_week10.csv", slate)

    # 4. Injuries
    inj = []
    for team, player, pos, injury, practice, game in C.INJURIES_W10:
        inj.append(
            {
                "team_abbr": team,
                "player": player,
                "position": pos,
                "injury": injury,
                "practice_status": practice,
                "game_status": game,
                "status_kind": "out" if game == "Out" else ("questionable" if game == "Questionable" else "practice_only"),
                "official_source_url": C.CAPTURES["injuries"]["url"],
                "retrieved_utc": CAPTURE_DATE,
            }
        )
    datasets["injuries_week10.csv"] = write_csv("injuries_week10.csv", inj)

    # 5. Originated markets -- side, total, moneyline in that order
    rows, agg, unplayed = M.originate_slate(C.GAMES, C.SLATE_W10, before_week=10)
    orig = []
    for r in rows:
        for order, market in enumerate(M.MARKET_ORDER, start=1):
            mm = r["model"][market]
            orig.append(
                {
                    "game_key": "W10-%s-%s" % (r["away"], r["home"]),
                    "week": r["week"],
                    "date": r["date"],
                    "away": r["away"],
                    "home": r["home"],
                    "origination_order": order,
                    "market": market,
                    "model_fair_line": mm.get("model_fair_line", ""),
                    "model_extra": mm.get("model_home_win_prob", ""),
                    "market_line": "" if mm.get("market_line") is None else mm["market_line"],
                    "difference": "" if mm.get("difference") is None else mm["difference"],
                    "status": mm.get("status", ""),
                    "inputs_used": "weeks 1-9 verified results; min 4 games per club",
                    "official_source_url": "https://www.nfl.com/schedules",
                    "retrieved_utc": CAPTURE_DATE,
                }
            )
    datasets["originated_markets.csv"] = write_csv("originated_markets.csv", orig)

    # 6. Price snapshots
    snaps = B.price_snapshot_rows(B.backtest_all())
    datasets["price_snapshots.csv"] = write_csv("price_snapshots.csv", snaps)

    # 7. Backtest ledger
    bt = B.backtest_all()
    led = []
    for r in bt:
        led.append(
            {
                "week": r["week"],
                "game_date": r["game_date"],
                "away": r["away"],
                "home": r["home"],
                "away_score": r["away_score"],
                "home_score": r["home_score"],
                "actual_total": r["actual_total"],
                "actual_margin_home": r["actual_margin_home"],
                "side_fair_line": "" if r["side_line"] is None else r["side_line"],
                "side_grade": "" if r["side_grade"] is None else r["side_grade"],
                "total_fair_line": "" if r["total_line"] is None else r["total_line"],
                "total_grade": "" if r["total_grade"] is None else r["total_grade"],
                "ml_model_home_prob": "" if r["ml_prob_home"] is None else r["ml_prob_home"],
                "ml_pick": "" if r["ml_pick"] is None else r["ml_pick"],
                "ml_grade": "" if r["ml_grade"] is None else r["ml_grade"],
                "ml_brier": "" if r["ml_brier"] is None else round(r["ml_brier"], 4),
                "official_source_url": "https://www.nfl.com/schedules/2026/by-week/week-%d" % r["week"],
                "retrieved_utc": CAPTURE_DATE,
            }
        )
    datasets["backtest_ledger.csv"] = write_csv("backtest_ledger.csv", led)

    # 8. Leaderboard
    fams = B.family_table(bt)
    lb = L.rows(fams)
    datasets["leaderboard.csv"] = write_csv("leaderboard.csv", lb)

    # 9. Validation gates + ladder
    corr = K.all_rows()
    gates = G.gate_rows(fams, corr)
    datasets["validation_gates.csv"] = write_csv("validation_gates.csv", gates)
    lad = G.ladder(fams, gates)
    datasets["promotion_ladder.csv"] = write_csv("promotion_ladder.csv", lad)

    # 10. Correlations
    datasets["correlations.csv"] = write_csv("correlations.csv", corr)

    # 11. Luck index
    luck = []
    for key, grades in B.strategy_results(bt).items():
        li = B.luck_index(grades)
        li["strategy_id"] = key
        luck.append(
            {
                "strategy_id": key,
                "n": li["n"],
                "hit_rate": li["win_rate"],
                "ci_low": li["ci_low"],
                "ci_high": li["ci_high"],
                "p_one_sided_fair_coin": li["p_one_sided_fair_coin"],
                "luck_share": li["luck_share"],
                "verdict": li["verdict"],
                "method": "one-sided exact binomial against p0=0.5; Wilson 95% interval",
                "official_source_url": "https://www.nfl.com/schedules",
            }
        )
    datasets["luck_index.csv"] = write_csv("luck_index.csv", luck)

    # 12. Depth register
    drow = DEP.register_rows("NE") + DEP.register_rows("DET")
    for r in drow:
        # A depth row has two official supports: the ordering (club depth chart) and
        # the availability (NFL injury report). The primary URL is the depth chart.
        r["official_source_url"] = r["depth_chart_url"]
    datasets["replacement_depth.csv"] = write_csv("replacement_depth.csv", drow)

    dnotes = DEP.register_notes("NE") + DEP.register_notes("DET")
    for n in dnotes:
        n["official_source_url"] = C.CAPTURES["injuries"]["url"]
        n["depth_chart_url"] = C.DEPTH_URL_BY_TEAM[n["team"]]
    datasets["depth_conflicts.csv"] = write_csv("depth_conflicts.csv", dnotes)

    # 13. Demotion gate
    datasets["demotion_gate.csv"] = write_csv("demotion_gate.csv", DM.gate_table(bt))

    # 14. Price snapshot coverage summary
    cov = [{
        "market": m,
        "originated_rows": len(B.price_snapshot_rows(bt)) // 3,
        "snapshot_rows": 2 * (len(B.price_snapshot_rows(bt)) // 3),
        "prices_captured": 0,
        "coverage_note": "Store is built and row-complete; every price cell is blank because no "
                         "official NFL price source exists.",
        "official_source_url": "https://www.nfl.com/odds/",
    } for m in ("side", "total", "moneyline")]
    datasets["price_snapshot_coverage.csv"] = write_csv("price_snapshot_coverage.csv", cov)

    return {
        "standings": st, "results": res, "slate": slate, "injuries": inj, "orig": orig,
        "snaps": snaps, "bt": bt, "ladder": lad, "lb": lb, "gates": gates, "corr": corr,
        "luck": luck, "depth": drow, "dc": dnotes, "dem": DM.gate_table(bt), "cov": cov,
        "fams": fams, "files": datasets,
    }


# ------------------------------------------------------------------ site build
def build_site(D):
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    bt = D["bt"]
    fams = D["fams"]
    gates = D["gates"]
    n_played = len([r for r in D["results"] if r["result_status"] == "final_verified"])
    n_blank = sum(1 for r in D["orig"] if r["market_line"] == "") + sum(
        1 for r in D["snaps"] if r["opening_price"] == "")
    open_gates = len([g for g in gates if g["status"] == "open"])

    # ---- index
    tiles = [
        (n_played, "verified final scores"),
        (len(D["orig"]), "originated markets"),
        (len(D["snaps"]), "price-snapshot rows"),
        (len(fams), "strategy families"),
        ("%d/%d" % (open_gates, len(gates)), "validation gates open"),
        (len([r for r in D["depth"] if r["is_backup_start"] == "yes"]), "backup starts detected"),
        (len(D["corr"]), "correlation rows"),
        (n_blank, "blank cells (flagged)"),
    ]
    tiles_html = "".join('<div class="tile"><b>%s</b><span>%s</span></div>' % (esc(v), esc(k)) for v, k in tiles)

    findings = [
        ("The NFL publishes no odds or line page.", "https://www.nfl.com/odds/ returns the NFL 404 page. "
         "There is therefore no official opening price, closing price, or market line to compare against."),
        ("Results are verifiable, so ROI is computable in principle.", "%d final scores were transcribed from "
         "nfl.com schedule pages, one URL per week." % n_played),
        ("The side model is worse than a coin flip.", "Walking forward over weeks 5-9 it went %d-%d "
         "(hit rate %s). That is a finding, not a bug: it is published, not hidden." % (
             fams[0]["wins"], fams[0]["losses"], fams[0]["win_rate"])),
        ("The moneyline is the only family with a signal-shaped p-value, and it has no price.",
         "p = %s at n = %d. With no moneyline price, no ROI can be attached, so the family reports a "
         "blank staking score." % (fams[2]["p_one_sided_fair_coin"], fams[2]["n"])),
        ("Same-game parlay legs are negatively correlated in this sample.",
         "r = %s (n = %d) between the side and total grades, which means two-leg same-game parlays are "
         "*worse* than the independence assumption predicts, not better." % (
             D["corr"][2]["correlation_value"], D["corr"][2]["n"])),
        ("No strategy is live and none may be.", "%d of %d gates are closed, including the forward-sample gate, "
         "which cannot be opened by any amount of analysis." % (len(gates) - open_gates, len(gates))),
    ]
    fn_html = "".join("<li><strong>%s</strong> %s</li>" % (esc(a), esc(b)) for a, b in findings)
    glance = table(
        ["Section", "What it answers", "Rows"],
        [
            {"Section": "Originated lines", "What it answers": "What does the model say, and where is the market?",
             "Rows": len(D["orig"])},
            {"Section": "Price snapshots", "What it answers": "What were the opening and closing numbers?",
             "Rows": len(D["snaps"])},
            {"Section": "Verified results", "What it answers": "What actually happened, per official source?",
             "Rows": len(D["results"])},
            {"Section": "Leaderboard", "What it answers": "Which strategy has signal, and which just has money?",
             "Rows": len(D["lb"])},
            {"Section": "Validation gates", "What it answers": "What still blocks a promotion?", "Rows": len(D["gates"])},
            {"Section": "Correlations", "What it answers": "Which legs really move together, at what n?",
             "Rows": len(D["corr"])},
            {"Section": "Depth & injuries", "What it answers": "How deep is the replacement?", "Rows": len(D["depth"])},
            {"Section": "Demotion gate", "What it answers": "When does a live strategy go back to paper?",
             "Rows": len(D["dem"])},
            {"Section": "Decision questions", "What it answers": "What must be answered before deciding?", "Rows": 12},
            {"Section": "Suggestions", "What it answers": "What are the options, and what is recommended?", "Rows": 8},
        ],
        num_cols=("Rows",),
    )

    body = (
        '<div class="hero"><p class="lede">This desk originates its own NFL numbers, records a full '
        'price-snapshot store for every market it originates, grades itself against a verified results '
        'feed, and reports signal and staking as two separate scores so a lucky staking run cannot '
        'disguise a broken signal. It is built to fail closed.</p></div>'
        '<div class="tiles">%s</div>'
        "<h2>The six findings that matter</h2><ol>%s</ol>"
        '<div class="note bad"><strong>Read this before any table.</strong> The market-line and '
        'difference columns are blank for every row. That is not an unfinished section: no official NFL '
        'line exists, and filling those columns from a sportsbook would break the rule that every value '
        'traces to an official source. The consequence is that <em>no edge has been measured</em>, and '
        'the leaderboard ranks signal quality only.</div>'
        "<h2>What is in each section</h2>"
        "<ul>"
        "<li><a href=\"executive-summary.html\">Executive summary</a> &mdash; the one-page read.</li>"
        "<li><a href=\"lines.html\">Originated lines</a> &mdash; side first, then total, then moneyline, "
        "with fair line / market line / difference as three separate columns.</li>"
        "<li><a href=\"snapshots.html\">Price snapshots</a> &mdash; the opening and closing store, its "
        "schema, and its coverage gap.</li>"
        "<li><a href=\"results.html\">Verified results</a> &mdash; %d final scores with one official URL each.</li>"
        "<li><a href=\"leaderboard.html\">Leaderboard</a> &mdash; signal score and staking score kept apart.</li>"
        "<li><a href=\"validation.html\">Validation gates</a> and <a href=\"demotion.html\">demotion gate</a> "
        "&mdash; how a strategy would be promoted, and how it is sent back.</li>"
        "<li><a href=\"correlations.html\">Correlations</a> &mdash; only from officially sourced numbers, "
        "with n on every row.</li>"
        "<li><a href=\"depth.html\">Depth &amp; injuries</a> &mdash; depth of the replacement, not just "
        "the fact of one.</li>"
        "<li><a href=\"decision-ledger.html\">Decision questions</a> &mdash; what must be answered before "
        "any change is made.</li>"
        "<li><a href=\"suggestions.html\">Suggestions</a> &mdash; options to review and choose between.</li>"
        "<li><a href=\"sources.html\">Sources</a>, <a href=\"flagged.html\">flagged</a>, and "
        "<a href=\"repo-review.html\">repo review</a>.</li>"
        "</ul>"
        "<h2>Contents at a glance</h2>%s" % (tiles_html, fn_html, n_played, glance)
    )
    page("index.html", "NFL Own-Line Desk", body)

    # ---- executive summary page
    es = "<p class=\"lede\">A short, decision-oriented read of the whole pack.</p>"
    es += "<h2>What was asked for and what exists</h2>"
    es += table(
        ["Requirement", "Status", "Where it lives", "Honest limit"],
        [
            {"Requirement": "Price-snapshot store with opening and closing numbers",
             "Status": "built, prices blank",
             "Where it lives": "snapshots.html, price_snapshots.csv",
             "Honest limit": "No official NFL price source exists."},
            {"Requirement": "Verified results feed so backtests and ROI can be computed",
             "Status": "done", "Where it lives": "results.csv, %d games" % n_played,
             "Honest limit": "Scores only; no per-player box scores beyond the injury report."},
            {"Requirement": "Originate side, then total, then moneyline",
             "Status": "done", "Where it lives": "lines.html",
             "Honest limit": "Moneyline inherits every error of the side."},
            {"Requirement": "Fair line, market line and difference as separate columns",
             "Status": "done", "Where it lives": "originated_markets.csv",
             "Honest limit": "Market line and difference are blank by rule."},
            {"Requirement": "Separate signal from staking on the leaderboard",
             "Status": "done", "Where it lives": "leaderboard.html",
             "Honest limit": "Signal score is a declared summary, not a probability."},
            {"Requirement": "Track depth of the replacement",
             "Status": "done for 2 clubs", "Where it lives": "depth.html",
             "Honest limit": "Only NE and DET depth charts were captured."},
            {"Requirement": "Correlations only from official numbers, with n",
             "Status": "done", "Where it lives": "correlations.html",
             "Honest limit": "Three requested correlations are refused, not estimated."},
            {"Requirement": "Demotion gate for live strategies",
             "Status": "done", "Where it lives": "demotion.html",
             "Honest limit": "Not yet exercised by a live strategy, because none is live."},
        ],
        status_cols=(), link_cols=(),
    )
    es += ("<h2>The headline number</h2><p>The originated side went <strong>%d-%d</strong> over %d graded "
           "bets in weeks 5-9 (hit rate %s, one-sided p vs a fair coin %s). The model is not merely "
           "unproven; at this sample it is actively wrong on the side. The demotion gate correctly "
           "returns it to paper.</p>" % (
               fams[0]["wins"], fams[0]["losses"], fams[0]["n"], fams[0]["win_rate"],
               fams[0]["p_one_sided_fair_coin"]))
    es += ("<h2>What would change the answer</h2><ul>"
           "<li>An official, citable market line. Without one the difference column cannot exist.</li>"
           "<li>A forward sample of 200+ bets, which is a matter of weeks, not analysis.</li>"
           "<li>Depth charts for the remaining 30 clubs, so the depth signal is not a two-club anecdote.</li>"
           "</ul>")
    page("executive-summary.html", "Executive summary", es)

    # ---- lines
    body = ("<p class=\"lede\">Side first, then total, then moneyline &mdash; in that order, because that "
            "is the order in which the model's evidence degrades. Fair line, market line and difference "
            "are three separate columns; the market and difference columns are blank for every row.</p>")
    body += table(
        ["game_key", "market", "origination_order", "model_fair_line", "model_extra", "market_line",
         "difference", "status", "official_source_url"],
        D["orig"], num_cols=("model_fair_line", "model_extra", "market_line", "difference"),
        status_cols=("status",), link_cols=("official_source_url",), maxlen=60,
    )
    body += ("<div class=\"note warn\"><strong>Why the difference column is empty.</strong> "
             "<code>difference = model_fair_line - market_line</code>, and <code>market_line</code> is "
             "blank because NFL.com publishes no line. A blank difference is the correct output of an "
             "honest pipeline, not a missing step.</div>")
    page("lines.html", "Originated lines", body)

    # ---- snapshots
    body = ("<p class=\"lede\">The store exists and is row-complete. It records an opening and a closing "
            "number for every market originated, with capture timestamps and a status. Every price cell "
            "is blank.</p>")
    body += table(["market", "snapshot_rows", "prices_captured", "coverage_note", "official_source_url"],
                  D["cov"], num_cols=("snapshot_rows", "prices_captured"),
                  link_cols=("official_source_url",), maxlen=200)
    body += "<h2>Store schema</h2>" + table(
        ["Field", "Meaning"],
        [
            {"Field": "game_id", "Meaning": "Week and matchup, matching results.csv."},
            {"Field": "market", "Meaning": "side | total | moneyline."},
            {"Field": "opening_price", "Meaning": "Blank. No official NFL opening number exists."},
            {"Field": "closing_price", "Meaning": "Blank. No official NFL closing number exists."},
            {"Field": "opening_captured_utc / closing_captured_utc", "Meaning": "Blank with the price, since there is no price to timestamp."},
            {"Field": "snapshot_status", "Meaning": "unverified_no_official_price_source."},
            {"Field": "official_source_url", "Meaning": "https://www.nfl.com/odds/ \u2014 which is the NFL 404 page."},
        ],
    )
    body += "<h2>Every snapshot row</h2>" + table(
        ["game_id", "market", "model_fair_line", "opening_price", "closing_price", "snapshot_status"],
        D["snaps"][:60], num_cols=("model_fair_line", "opening_price", "closing_price"),
        status_cols=("snapshot_status",), maxlen=40,
    )
    body += ("<p class=\"lede\">First 60 of %d rows &mdash; full data in "
             "<code>data/nfl_market/price_snapshots.csv</code>.</p>" % len(D["snaps"]))
    page("snapshots.html", "Price snapshots", body)

    # ---- results
    body = ("<p class=\"lede\">%d final scores, each transcribed from the nfl.com week page that "
            "listed it. This feed is what makes a backtest possible at all.</p>" % n_played)
    body += table(["week", "game_date", "away_team", "home_team", "away_score", "home_score",
                   "total_points", "home_margin", "winner", "result_status", "official_source_url"],
                  D["results"], num_cols=("away_score", "home_score", "total_points", "home_margin"),
                  status_cols=("result_status",), link_cols=("official_source_url",), maxlen=40)
    page("results.html", "Verified results feed", body)

    # ---- leaderboard
    body = ("<p class=\"lede\">Ranked on signal score only. The staking score is printed beside it and is "
            "never added to it. When the two disagree, the row says so.</p>")
    body += table(["rank_by_signal", "strategy_id", "tier", "n", "hit_rate", "ci_low", "ci_high",
                   "p_one_sided_fair_coin", "signal_score", "staking_roi", "staking_score",
                   "divergence_flag", "live"],
                  D["lb"], num_cols=("n", "hit_rate", "ci_low", "ci_high", "p_one_sided_fair_coin",
                                     "signal_score", "staking_roi", "staking_score"),
                  maxlen=50)
    body += ("<h2>The two scores, defined</h2>"
             "<p><strong>signal_score</strong> = evidence term (1 &minus; &radic;(p/0.5)) &times; sample term "
             "&radic;(n/100), scaled to 100. It cannot be raised by betting more.</p>"
             "<p><strong>staking_score</strong> = 50 &times; ROI/0.20 clamped to &plusmn;50 at a declared flat "
             "stake and &minus;110. It is blank for the moneyline because no moneyline price exists.</p>"
             "<div class=\"note\">A divergence flag of <code>positive_staking_masks_weak_signal</code> is "
             "exactly the failure mode this table was built to expose.</div>")
    body += "<h2>Reward tiers</h2>" + table(
        ["Tier", "Label", "Meaning"], [{"Tier": t, "Label": l, "Meaning": m} for t, l, m in L.TIERS])
    page("leaderboard.html", "Leaderboard: signal vs staking", body)

    # ---- validation
    body = ("<p class=\"lede\">Ten gates, fail-closed. A strategy reaches live only if all ten open. "
            "%d of %d are open.</p>" % (open_gates, len(gates)))
    body += table(["gate_id", "gate_name", "status", "blocks_promotion", "evidence", "why_it_blocks"],
                  D["gates"], status_cols=("status", "blocks_promotion"), maxlen=240)
    body += "<h2>Promotion ladder</h2>" + table(
        ["strategy_id", "n", "hit_rate", "gates_closed", "rung", "promotion_granted", "why"],
        D["ladder"], num_cols=("n", "hit_rate", "promotion_granted"), maxlen=200)
    body += "<h2>Luck index</h2>" + table(
        ["strategy_id", "n", "hit_rate", "ci_low", "ci_high", "p_one_sided_fair_coin", "luck_share", "verdict"],
        D["luck"], num_cols=("n", "hit_rate", "ci_low", "ci_high", "p_one_sided_fair_coin", "luck_share"),
        maxlen=60)
    page("validation.html", "Validation gates", body)

    # ---- correlations
    body = ("<p class=\"lede\">Only from officially sourced numbers. n is on every row, including the "
            "refused ones.</p>")
    body += table(["correlation_id", "leg_a", "leg_b", "n", "method", "correlation_value", "p_two_sided",
                   "status", "interpretation_note", "official_source_url"],
                  D["corr"], num_cols=("n", "correlation_value", "p_two_sided"),
                  status_cols=("status",), link_cols=("official_source_url",), maxlen=230)
    body += ("<div class=\"note warn\"><strong>COR-06 to COR-08 are refusals.</strong> They are the "
             "correlations this project would most like to have, and they cannot be computed from "
             "official sources. Refusing is the correct output.</div>")
    page("correlations.html", "Correlations", body)

    # ---- depth
    body = ("<p class=\"lede\">Depth of the replacement, not the fact of one. For each listed slot: who "
            "starts, which string is the first body actually available, and how deep the club goes if a "
            "questionable starter is scratched.</p>")
    body += table(["team", "unit", "position_slot", "starter", "starter_designation", "listed_strings",
                   "first_available_player", "replacement_designation", "depth_of_replacement",
                   "depth_if_starter_scratched", "unavailable_above_replacement", "is_backup_start",
                   "replacement_is_4th_string_or_worse", "deficiency_points", "score_kind"],
                  D["depth"], num_cols=("depth_of_replacement", "depth_if_starter_scratched",
                                        "unavailable_above_replacement", "deficiency_points"),
                  maxlen=40)
    body += ("<h2>Where the two official pages disagree</h2>"
             "<p>Every case below is a player who is on a club depth chart but ruled <code>Out</code> on "
             "the official injury report. These are the rows a line should move on.</p>")
    body += table(["team", "unit", "position_slot", "string", "player", "designation", "injury",
                   "practice_status", "note", "official_source_url"],
                  D["dc"], num_cols=("string",), maxlen=80, link_cols=("official_source_url",))
    body += "<h2>Not covered</h2><p>30 of 32 clubs have no captured depth chart. Their rows are absent, " \
            "not guessed. Closing that gap is suggestion S-04.</p>"
    page("depth.html", "Replacement depth and injuries", body)

    # ---- demotion
    body = ("<p class=\"lede\">A promotion ladder without a way down is a trap. These triggers are "
            "mechanical and published, so the same data always produces the same demotion.</p>")
    body += table(["strategy_id", "trailing_window_n", "trailing_hit_rate", "trailing_p_vs_fair_coin",
                   "max_drawdown_units", "triggers_fired", "lifecycle_status"],
                  D["dem"], num_cols=("trailing_window_n", "trailing_hit_rate",
                                      "trailing_p_vs_fair_coin", "max_drawdown_units"), maxlen=80)
    body += "<h2>Thresholds</h2>" + table(
        ["threshold", "value"],
        [{"threshold": "D1", "value": "20-game trailing window, hit rate floor 0.45"},
         {"threshold": "D2", "value": "10.0 units max drawdown"},
         {"threshold": "D3", "value": "trailing p vs fair coin must stay <= 0.20"},
         {"threshold": "D4", "value": "sample integrity: a re-graded source invalidates the record"},
         {"threshold": "D5", "value": "same-game leg |r| > 0.35 forbids independent parlay pricing"}])
    page("demotion.html", "Demotion gate", body)

    # ---- decision ledger / suggestions / sources / flagged / repo review are written by
    #      separate modules to keep this builder readable.
    return D


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    D = build_data()
    build_site(D)

    from nfl_market import editorial  # local import: keeps build order explicit

    editorial.write_pages(page, table, write_csv, DATA)
    print("built %d CSVs and %d pages" % (len(D["files"]) + 5, len(NAV)))

    if args.check:
        rc = subprocess.call([sys.executable, os.path.join(REPO, "scripts", "check_nfl_market.py")])
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
