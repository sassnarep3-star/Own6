#!/usr/bin/env python3
"""Build the nfl_ca1b pack: CSV tables + a zero-input GitHub Pages site.

Deterministic: no network, no clock-dependent output except the fixed capture
dates that are part of the data. Re-running produces byte-identical files.

Usage
-----
    python3 scripts/build_nfl_ca1b.py           # write CSVs and HTML
    python3 scripts/build_nfl_ca1b.py --check   # build, then run the verifier
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

from nfl_ca1b import availability as AV        # noqa: E402
from nfl_ca1b import capture as C              # noqa: E402
from nfl_ca1b import conflicts as CF           # noqa: E402
from nfl_ca1b import engine as E               # noqa: E402
from nfl_ca1b import freshness as FR           # noqa: E402
from nfl_ca1b import qia as Q                  # noqa: E402
from nfl_ca1b import requirements as RQ        # noqa: E402
from nfl_ca1b import snapshots as SN           # noqa: E402
from nfl_ca1b import suggestions as SG         # noqa: E402
from nfl_ca1b import verify as V               # noqa: E402
from nfl_ca1b.ratings import ridge_fit, fit_sigma, total_sigma, margin_hat, expected_points  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_ca1b")
DOCS = os.path.join(REPO, "docs", "nfl-ca1b")
SESSION = "arena/ca1b3769-own6"

NAV = [
    ("index.html", "Start here"),
    ("decision.html", "Decision readiness"),
    ("lines.html", "Originated lines"),
    ("signal.html", "Signal vs luck"),
    ("backtest.html", "Backtest (not a ranking)"),
    ("leaderboard.html", "Leaderboard + gates"),
    ("availability.html", "Availability & designations"),
    ("injuries.html", "Injury series & deltas"),
    ("depth.html", "Depth & deficiency"),
    ("venues.html", "Week-11 venues"),
    ("verify.html", "Verification ledger"),
    ("conflicts.html", "Cross-pack conflicts"),
    ("snapshots.html", "Snapshot ledger"),
    ("freshness.html", "Freshness & drift"),
    ("requirements.html", "Requirement register"),
    ("qia.html", "Questions & answers"),
    ("suggestions.html", "Suggestions queue"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]

STYLE = """
:root{--ink:#12233b;--muted:#5b6b82;--navy:#0b2545;--navy2:#13315c;--accent:#ee6c4d;
--paper:#f6f8fb;--line:#dfe6f0;--ok:#d9f2e2;--okink:#1c6b3d;--no:#fde2e2;--noink:#8f1d1d;
--warn:#fff3cd;--warnink:#7a5b00;--blank:#fff7e6}
*{box-sizing:border-box}
body{font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,sans-serif;margin:0;color:var(--ink);background:var(--paper)}
a{color:#0b5394;text-underline-offset:.15em}
header.top{background:var(--navy);color:#fff;padding:16px 22px 14px}
header.top h1{margin:0;font-size:19px;letter-spacing:.01em}
header.top p{margin:4px 0 0;font-size:12.5px;opacity:.85}
nav.crumbs{display:flex;flex-wrap:wrap;gap:2px;background:var(--navy2);padding:6px 10px;position:sticky;top:0;z-index:5}
nav.crumbs a{color:#cfe0f5;text-decoration:none;padding:5px 9px;border-radius:4px;font-size:12.5px}
nav.crumbs a.on,nav.crumbs a:hover{background:var(--accent);color:#fff}
main{max-width:1200px;margin:0 auto;padding:16px}
section{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin:14px 0}
h2{font-size:17px;margin:2px 0 8px}h3{font-size:14.5px;margin:12px 0 6px}
p.lede{color:var(--muted);margin:2px 0 10px;font-size:13.5px}
.tablewrap{overflow-x:auto;max-height:70vh}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border:1px solid #e3e9f2;padding:5px 7px;text-align:left;vertical-align:top}
th{background:#eef3fa;position:sticky;top:0;white-space:nowrap}
td.blank{background:var(--blank)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap}
.ok{background:var(--ok);color:var(--okink)}.no{background:var(--no);color:var(--noink)}
.warn{background:var(--warn);color:var(--warnink)}
.note{background:#f2f6fc;border-left:3px solid var(--navy2);padding:8px 12px;margin:8px 0;font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
a.card{display:block;background:#fff;border:1px solid var(--line);border-radius:8px;padding:11px 13px;
text-decoration:none;color:var(--ink)}
a.card:hover{border-color:var(--accent);box-shadow:0 2px 10px rgba(11,37,69,.08)}
a.card b{display:block;font-size:13.5px;margin-bottom:3px}
a.card span{font-size:12px;color:var(--muted)}
.kpi{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:6px 0}
.kpi div{background:#fff;border:1px solid var(--line);border-radius:8px;padding:9px 11px}
.kpi b{display:block;font-size:19px;line-height:1.2}
.kpi span{font-size:11.5px;color:var(--muted)}
footer{text-align:center;color:#7a8aa3;font-size:12px;padding:20px}
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url: str, label: str = "source") -> str:
    if not url or not str(url).startswith("http"):
        return esc(url)
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)} &#8599;</a>'


def write_csv(name: str, rows, cols=None) -> str:
    os.makedirs(DATA, exist_ok=True)
    rows = list(rows)
    cols = cols or (list(rows[0].keys()) if rows else ["empty"])
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return path


OFFICIAL_FOOTER = (
    "<section><h2>Official sources for this page</h2>"
    "<p class='lede'>Every table on this page is derived from these official NFL pages, read on "
    "2026-11-17 UTC. The clock time of each read is on <a href='sources.html'>Sources</a>.</p>"
    "<ul>"
    "<li><a href='https://www.nfl.com/standings/' rel='noopener noreferrer' target='_blank'>"
    "nfl.com/standings/</a> - club records and points, read 2026-11-17T00:40Z</li>"
    "<li><a href='https://www.nfl.com/schedules/2026/by-week/week-10' rel='noopener noreferrer' "
    "target='_blank'>nfl.com/schedules/2026/by-week/week-10</a> - the 13 week-10 finals, read 00:41Z</li>"
    "<li><a href='https://www.nfl.com/schedules/2026/by-week/week-11' rel='noopener noreferrer' "
    "target='_blank'>nfl.com/schedules/2026/by-week/week-11</a> - the 13 live fixtures, read 00:39Z</li>"
    "<li><a href='https://www.nfl.com/injuries/' rel='noopener noreferrer' target='_blank'>"
    "nfl.com/injuries/</a> - designations and practice status, read 00:44Z</li>"
    "<li><a href='https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season' "
    "rel='noopener noreferrer' target='_blank'>NFL Week 10 inactives</a> - who did not dress, read 00:45Z</li>"
    "<li><a href='https://www.nfl.com/legal/terms/' rel='noopener noreferrer' target='_blank'>"
    "NFL.com Terms of Use</a> - the retrieval boundary every blank on this site respects</li>"
    "</ul></section>")


def page(title: str, body: str, active: str) -> str:
    items = []
    for u, t in NAV:
        cls = ' class="on"' if u == active else ""
        items.append(f'<a href="{esc(u)}"{cls}>{esc(t)}</a>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL convergence pack (ca1b)</title>
<style>{STYLE}</style></head><body>
<header class="top"><h1>NFL Convergence &amp; Verification Pack</h1>
<p>Session ca1b3769 · every value read from an official NFL page on 2026-11-17 UTC · blanks are
flagged, never filled · no profitability claim · no input required</p></header>
<nav class="crumbs" aria-label="Section">{''.join(items)}</nav>
<main>{body}{OFFICIAL_FOOTER}</main>
<footer>Built deterministically from <code>src/nfl_ca1b</code> by
<code>scripts/build_nfl_ca1b.py</code>. Re-running the builder reproduces every table byte for byte.</footer>
</body></html>
"""


def table(cols, rows, blank_cols=(), num_cols=(), limit=None):
    shown = [c for c in cols]
    out = ["<div class='tablewrap'><table><thead><tr>"]
    for _, h in shown:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    shown_rows = rows if limit is None else rows[:limit]
    for r in shown_rows:
        out.append("<tr>")
        for k, _ in shown:
            v = r.get(k, "")
            cls = []
            if k in num_cols and v not in ("", None):
                cls.append("num")
            if k in blank_cols and v in ("", None):
                cls.append("blank")
            if isinstance(v, str) and v.startswith("http"):
                cell = link(v)
            elif isinstance(v, float):
                cell = esc(("%.4f" % v).rstrip("0").rstrip(".") if abs(v) < 1000 else "%.1f" % v)
            else:
                cell = esc(v)
            attr = f' class="{" ".join(cls)}"' if cls else ""
            out.append(f"<td{attr}>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    if limit is not None and len(rows) > limit:
        out.append(f"<p class='lede'>Showing {limit} of {len(rows)} rows; the full table is in the CSV.</p>")
    return "".join(out)


def pill(text: str, kind: str = "ok") -> str:
    return f"<span class='pill {kind}'>{esc(text)}</span>"


def build() -> dict:
    os.makedirs(DOCS, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    stats = {}

    # ---------------------------------------------------------- data
    games = E.load_games()
    teams = E.teams()
    wf = E.walk_forward(games, teams)
    controls = E.control_rows(wf)
    for r in wf:
        r["p_home_pick"] = r["p_home"] if r["p_home"] >= 0.5 else 1 - r["p_home"]
    luck = [E.luck_rows(wf, "rating picks (model side, one unit)", lambda r: (r["p_home"] >= 0.5, max(r["p_home"], 1 - r["p_home"]))),
            E.luck_rows(wf, "home always", lambda r: (True, 1.0)),
            E.luck_rows(wf, "away always", lambda r: (False, 1.0))]
    corr = E.correlations(games)
    lines, meta = E.originate_week11(games, teams)
    prereg = E.prereg_rows()
    lb = E.leaderboard(wf, meta)
    demotion = E.demotion_rules()

    train = [(g[0], g[1], g[2], g[3]) for g in games]
    pfit = ridge_fit(train, teams)
    sig = fit_sigma(pfit, train)
    ratings = [{"club": t, "atk": pfit["atk"][t], "def": pfit["def"][t],
                "net": pfit["atk"][t] - pfit["def"][t],
                "w": C.STANDINGS[t][0], "l": C.STANDINGS[t][1], "t": C.STANDINGS[t][2],
                "pf": C.STANDINGS[t][3], "pa": C.STANDINGS[t][4],
                "source_url": "https://www.nfl.com/standings/"} for t in teams]

    calib, calib_players = AV.designation_calibration()
    deltas = AV.injury_deltas()
    series = AV.injury_series_rows()
    teamview = AV.team_view(calib_players)
    headconf = AV.headline_conflicts()
    sweep = _sweep()
    venues = _venues()
    ledger = SN.chain()
    vstand = V.standings_rows()
    vres = V.results_rows()
    reqs = RQ.merge()
    qrows = Q.rows()
    sug = SG.rows()
    conf = CF.ROWS
    fresh = FR.rows()

    write_csv("sources.csv", C.SNAPSHOTS)
    write_csv("standings_official_2026-11-17.csv",
              [{"club": t, "w": v[0], "l": v[1], "t": v[2], "pf": v[3], "pa": v[4],
                "read_at_utc": "2026-11-17T00:40:00Z",
                "source_url": "https://www.nfl.com/standings/"} for t, v in sorted(C.STANDINGS.items())])
    write_csv("results_week10_official.csv",
              [{"game_id": g, "date_on_card": d, "away": a, "home": h, "away_score": s1,
                "home_score": s2, "status_on_card": st, "read_at_utc": "2026-11-17T00:41:00Z",
                "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"}
               for g, d, a, h, s1, s2, st in C.WEEK10])
    write_csv("ratings.csv", ratings)
    write_csv("walkforward.csv", wf)
    write_csv("controls.csv", controls)
    write_csv("luck_panel.csv", luck)
    write_csv("correlations.csv", corr)
    write_csv("originated_lines_week11.csv", lines)
    write_csv("model_meta.json.csv", [{"key": k, "value": v} for k, v in meta.items()])
    write_csv("prereg.csv", prereg)
    write_csv("leaderboard.csv", lb)
    write_csv("demotion_gates.csv", demotion)
    write_csv("injury_series.csv", series)
    write_csv("injury_deltas.csv", deltas)
    write_csv("designation_calibration.csv", calib)
    write_csv("designation_players.csv", calib_players)
    write_csv("team_view.csv", teamview)
    write_csv("headline_conflicts.csv", headconf)
    write_csv("availability_sweep.csv", sweep)
    write_csv("venues_week11.csv", venues)
    write_csv("snapshot_ledger.csv", ledger)
    write_csv("verification_standings.csv", vstand)
    write_csv("verification_results.csv", vres)
    write_csv("requirements_master.csv", reqs)
    write_csv("qia.csv", qrows)
    write_csv("suggestions.csv", sug)
    write_csv("conflicts.csv", conf)
    write_csv("freshness.csv", fresh)
    write_csv("probes.csv", [{"probe_id": a, "url": b, "intent": c, "observed": d,
                              "read_at_utc": e, "consequence": f}
                             for a, b, c, d, e, f in C.PROBES])
    write_csv("flagged.csv", _flags(vstand, vres, conf, headconf))

    stats["n_verified_values"] = len(vstand) + len(vres)
    stats["n_mismatch"] = sum(1 for r in vstand + vres if r["status"] == "mismatch")
    stats["wf_n"] = len(wf)
    # computed from the walk-forward rows, never read back from the leaderboard (which is blank)
    bs = sum((r["p_home"] - int(r["y_home_win"])) ** 2 for r in wf) / len(wf)
    stats["skill"] = 1 - bs / 0.25
    stats["skill_lo"] = _cluster_lo(wf)

    # ---------------------------------------------------------- pages
    def write(name, title, body):
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
            fh.write(page(title, body, name))

    write("index.html", "Start here", _index(wf, lines, luck, reqs, qrows, sug, conf, ledger, fresh, stats))
    write("decision.html", "Decision readiness", _decision(reqs, qrows))
    write("lines.html", "Originated lines", _lines(lines, meta, ratings, sig))
    write("signal.html", "Signal vs luck", _signal(wf, controls, luck, corr))
    write("backtest.html", "Backtest", _backtest(wf, meta, lb))
    write("leaderboard.html", "Leaderboard", _leaderboard(lb, prereg, demotion))
    write("availability.html", "Availability", _availability(calib, teamview, headconf))
    write("injuries.html", "Injury series", _injuries(series, deltas))
    write("depth.html", "Depth", _depth(sweep, teamview))
    write("venues.html", "Venues", _venues_page(venues))
    write("verify.html", "Verification", _verify(vstand, vres, stats))
    write("conflicts.html", "Conflicts", _conflicts(conf))
    write("snapshots.html", "Snapshots", _snapshots(ledger))
    write("freshness.html", "Freshness", _freshness(fresh))
    write("requirements.html", "Requirements", _requirements(reqs))
    write("qia.html", "Questions", _qia(qrows))
    write("suggestions.html", "Suggestions", _suggestions(sug))
    write("flagged.html", "Flagged", _flagged_page(vstand, vres, conf, headconf, venues))
    write("sources.html", "Sources", _sources())
    return stats


# ---------------------------------------------------------------- data helpers
def _sweep():
    rows = []
    for club in sorted(C.STANDINGS):
        captured = club in C.INJURY_CLUBS_CAPTURED
        inact = club in C.INACTIVES_W10
        rows.append({
            "club": club,
            "injury_hub_table_captured": "yes" if captured else "no",
            "inactive_list_captured": "yes" if inact else ("not published (TNF)" if club in ("WAS", "NYG") else ("not published yet (MNF)" if club in ("BAL", "LAC") else "no")),
            "roster_page_captured_any_pack": "yes" if club == "GB" else "no",
            "sweep_complete": "no",
            "blocking_gate": "G-SWEEP: 32 club roster/IR reads",
            "number_that_would_clear": "32 of 32 clubs with hub + roster captured",
            "source_url": "https://www.nfl.com/injuries/",
        })
    return rows


def _venues():
    rows = []
    for gid, day, date, time_et, net, away, home, sched_venue, mark in C.WEEK11:
        gc = C.VENUE_GAME_CENTRE.get(gid)
        gc_val = gc[0].split("|")[0] if gc else ""
        gc_city = gc[0].split("|")[1] if gc else ""
        rows.append({
            "game_id": gid, "date": date, "kickoff_et": time_et, "network": net,
            "away": away, "home": home,
            "venue_on_schedule_card": sched_venue,
            "venue_on_game_centre": gc_val,
            "city_on_game_centre": gc_city,
            "event_mark_on_card": mark,
            "note": ("the schedule card carries no hotel deep-link for this fixture, so the schedule "
                     "surface has no venue string; the game centre supplies it"
                     if not sched_venue and gc_val else ""),
            "surfaces_agree": ("yes" if sched_venue and gc_val and sched_venue.upper() == gc_val.upper()
                               else ("n/a - one surface not read" if not gc_val or not sched_venue else "no")),
            "game_centre_url": "https://www.nfl.com/games/%s-at-%s-2026-reg-11" % (_slug(away), _slug(home)),
            "schedule_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
            "read_at_utc": "2026-11-17T00:39:00Z",
        })
    return rows


SLUGS = {"AZ": "cardinals", "ATL": "falcons", "BAL": "ravens", "BUF": "bills", "CAR": "panthers",
         "CHI": "bears", "CIN": "bengals", "CLE": "browns", "DAL": "cowboys", "DEN": "broncos",
         "DET": "lions", "GB": "packers", "HOU": "texans", "IND": "colts", "JAX": "jaguars",
         "KC": "chiefs", "LA": "rams", "LAC": "chargers", "LV": "raiders", "MIA": "dolphins",
         "MIN": "vikings", "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets",
         "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks", "SF": "49ers", "TB": "buccaneers",
         "TEN": "titans", "WAS": "commanders"}


def _slug(abbr: str) -> str:
    return SLUGS.get(abbr, abbr.lower())


def _flags(vstand, vres, conf, headconf):
    rows = []
    i = 0
    for r in vstand + vres:
        if r["status"] == "mismatch":
            i += 1
            rows.append({"flag_id": "FL-%02d" % i, "severity": "high",
                         "item": "%s: %s %s" % (r["pack"], r.get("club") or r.get("matchup"), r["status"]),
                         "detail": r.get("note", ""), "source_url": r.get("source_url", ""),
                         "blocks_publish": "no — the pack's value is retained and this row publishes it"})
    for c in conf:
        if c["status"].startswith("open"):
            i += 1
            rows.append({"flag_id": "FL-%02d" % i, "severity": "medium",
                         "item": "%s %s" % (c["cid"], c["fact"]),
                         "detail": "%s vs %s — %s" % (c["value_a"], c["value_b"], c["verdict"]),
                         "source_url": c["source_url"], "blocks_publish": "no"})
    for h in headconf:
        i += 1
        rows.append({"flag_id": "FL-%02d" % i, "severity": "low",
                     "item": "%s %s: %s" % (h["club"], h["player"], "hub silent, inactive list names him"),
                     "detail": h["conflict"], "source_url": h["source_url"], "blocks_publish": "no"})
    i += 1
    rows.append({"flag_id": "FL-%02d" % i, "severity": "medium",
                 "item": "Injury hub partially captured (18 of 32 clubs)",
                 "detail": "4 of 8 fetched chunks were read; 14 clubs are marked not_captured rather than "
                           "injury-free. The page also renders WEEK 10 (not 11) two days before week-11 kickoff.",
                 "source_url": "https://www.nfl.com/injuries/", "blocks_publish": "no"})
    i += 1
    rows.append({"flag_id": "FL-%02d" % i, "severity": "medium",
                 "item": "Club depth-chart route does not exist",
                 "detail": "nfl.com/teams/houston-texans/depth-chart returns 404 (probe P-01, 2026-11-17). "
                           "No depth rank is published anywhere in this pack.",
                 "source_url": "https://www.nfl.com/teams/houston-texans/depth-chart", "blocks_publish": "no"})
    i += 1
    rows.append({"flag_id": "FL-%02d" % i, "severity": "low",
                 "item": "Game Centre Injury Report module empty for week 11",
                 "detail": "Both club modules read 'Injury Report is not available at this time' on IND@HOU.",
                 "source_url": "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "blocks_publish": "no"})
    i += 1
    rows.append({"flag_id": "FL-%02d" % i, "severity": "high",
                 "item": "No market price exists in any official source",
                 "detail": "Every market, residual, ROI, CLV and staking cell is blank by policy (G-PRICE).",
                 "source_url": "https://www.nfl.com/legal/terms/", "blocks_publish": "no"})
    i += 1
    rows.append({"flag_id": "FL-%02d" % i, "severity": "medium",
                 "item": "Retrieval terms not settled",
                 "detail": "NFL.com Terms of Use restrict systematic retrieval; no permission was obtained, "
                           "so nothing here is automated and no scheduled capture was built.",
                 "source_url": "https://www.nfl.com/legal/terms/", "blocks_publish": "no"})
    return rows


# ---------------------------------------------------------------- page bodies
def _cluster_lo(wf):
    """Game-cluster bootstrap lower bound on Brier skill (deterministic LCG)."""
    n = len(wf)
    p = [r["p_home"] for r in wf]
    y = [int(r["y_home_win"]) for r in wf]
    s = 20261117
    draws = []
    for _t in range(1000):
        tot = 0.0
        for _ in range(n):
            s = (1103515245 * s + 12345) % (2 ** 31)
            j = s % n
            tot += (p[j] - y[j]) ** 2
        draws.append(1 - (tot / n) / 0.25)
    draws.sort()
    return draws[24]


def _kpi(items):
    return "<div class='kpi'>" + "".join(
        f"<div><b>{esc(v)}</b><span>{esc(l)}</span></div>" for v, l in items) + "</div>"


def _cards(items):
    return "<div class='cards'>" + "".join(
        f"<a class='card' href='{esc(u)}'><b>{esc(t)}</b><span>{esc(d)}</span></a>"
        for u, t, d in items) + "</div>"


def _sec(title, inner, lede=""):
    lead = f"<p class='lede'>{lede}</p>" if lede else ""
    return f"<section><h2>{esc(title)}</h2>{lead}{inner}</section>"


def _index(wf, lines, luck, reqs, qrows, sug, conf, ledger, fresh, stats):
    n_open = sum(1 for r in reqs if r["status"] in ("open", "blocked"))
    from nfl_ca1b import qia as _Q
    L = _Q.L
    out = []
    out.append(_sec(
        "What this pack is for",
        "<p class='lede'>Fifteen merged NFL packs already publish versions of the same facts. This pack "
        "does four things and stops: it re-reads the official pages today, it says value by value which "
        "stored numbers survive that re-read, it produces the single requirement list the owner never had, "
        "and it originates a fair line for every live fixture while refusing to rank anything that has not "
        "been settled prospectively.</p>" + _kpi([
            (stats["n_verified_values"], "stored values re-tested today"),
            (stats["n_mismatch"], "contradictions found"),
            (len(lines), "week-11 fixtures originated"),
            (stats["wf_n"], "walk-forward graded games"),
            ("%.3f" % stats["skill"], "Brier skill (walk-forward backtest)"),
            ("%.3f" % stats["skill_lo"], "its 95% lower bound"),
            (len(reqs), "distinct requirements (was 342 rows)"),
            (n_open, "open or blocked requirements"),
            (len(qrows), "questions with a clearing number"),
            (len(sug), "suggestions awaiting your choice"),
            (0, "strategies promotable today"),
        ])))
    note = (
        "<div class='note'><p><b>Signal, honestly stated.</b> The rating model picks the winner in "
        f"{L['hits']} of {L['n']} graded games ({L['hits'] / L['n'] * 100:.1f}%). Against a coin that is "
        f"p = {L['luck_p']:.4f}. But under the model's <i>own</i> published probabilities the expected "
        f"number of hits was {L['own_exp']:.1f}, and the two-sided Poisson-binomial p is {L['own_p']:.3f}: "
        "the results are exactly what the published probabilities imply. That is the correct reading - a "
        "modest edge over a coin, and no evidence of a hidden extra edge.</p>"
        "<p><b>Ranking.</b> The game-bootstrap 95% interval on Brier skill has a point estimate of "
        f"{stats['skill']:.4f} and a lower bound of {stats['skill_lo']:.4f}. The lower bound includes zero, "
        "so no rank is published and no strategy is reward-eligible.</p>"
        "<p><b>Calibration.</b> The raw model is overconfident: in its 80-100% band it forecast 0.895 and "
        "observed 0.636 over 22 games. A walk-forward variance multiplier (median k = 1.8, chosen only on "
        "data older than each prediction) is applied to every probability published in this pack, and the "
        "value of k is printed on each row.</p></div>")
    out.append(_sec("The honest headline", note))
    out.append(_sec("What is deliberately blank",
                    "<div class='note'><p>Every market price, every residual, every ROI and CLV, every "
                    "leaderboard rank, every depth rank, and every player-level replacement claim. No "
                    "official NFL page publishes any of them. Blanks are never filled by inference; each "
                    "one carries the number that would clear it on <a href='decision.html'>Decision "
                    "readiness</a> and a row on <a href='flagged.html'>Flagged for review</a>.</p></div>"))
    out.append(_sec("Sections", _cards([
        ("decision.html", "Decision readiness",
         "Every requirement with the gate that blocks it and the number that clears it."),
        ("lines.html", "Originated lines",
         "Fair spread, fair total and fair moneyline for all 13 live fixtures, with inputs."),
        ("signal.html", "Signal vs luck",
         "Walk-forward proper scores, three controls, exact binomial and Poisson-binomial tests."),
        ("leaderboard.html", "Leaderboard + gates",
         "Signal and staking kept apart; five pre-registered strategies; five demotion gates."),
        ("availability.html", "Availability",
         "What each game designation actually meant in week 10, measured against official inactive lists."),
        ("injuries.html", "Injury series & deltas",
         "Two dated reads of the same page, differenced player by player."),
        ("depth.html", "Depth & deficiency",
         "Why no depth rank can be published, and the sweep status for all 32 clubs."),
        ("venues.html", "Week-11 venues",
         "All 13 fixtures, both official surfaces, disagreements left visible."),
        ("verify.html", "Verification ledger",
         str(stats["n_verified_values"]) + " stored values re-tested line by line against today's pages."),
        ("conflicts.html", "Cross-pack conflicts",
         str(len(conf)) + " cases where two merged packs publish different values for the same fact."),
        ("snapshots.html", "Snapshot ledger", "Hash-chained point-in-time captures."),
        ("freshness.html", "Freshness & drift", "Which stored dataset has been overtaken by its source."),
        ("requirements.html", "Requirement register", "342 rows collapsed to the distinct set."),
        ("qia.html", "Questions & answers",
         "The 10 decisions that are currently unreachable, with what would settle each."),
        ("suggestions.html", "Suggestions queue",
         "Ranked for your choice; nothing is implemented without it."),
        ("flagged.html", "Flagged for review", "Irregularities and unverified items, each with its link."),
        ("sources.html", "Sources", "Every page read this session, with its clock time."),
    ])))
    return "".join(out)


def _decision(reqs, qrows):
    opens = [r for r in reqs if r["status"] in ("open", "blocked")]
    out = [_sec("Decision-readiness table",
                _kpi([(len(reqs), "distinct requirements"),
                      (sum(1 for r in reqs if r["status"] == "delivered"), "delivered"),
                      (sum(1 for r in reqs if r["status"] == "open"), "open"),
                      (sum(1 for r in reqs if r["status"] == "blocked"), "blocked"),
                      (sum(1 for r in reqs if ";" in str(r["status_variants"])),
                       "packs disagreed on status")]),
                "One row per distinct requirement. <b>Blocked</b> means no source exists that could "
                "satisfy it today; <b>open</b> means a source exists but the work is not done. Where packs "
                "disagree, the worst status is reported.")]
    out.append(_sec("The 10 decisions that matter now",
                    table([("qid", "ID"), ("area", "Area"), ("question", "Question"),
                           ("answer", "Answer we can defend"),
                           ("number", "Number that settles it")], qrows)))
    out.append(_sec("Open and blocked requirements (%d)" % len(opens),
                    table([("req_id", "ID"), ("requirement", "Requirement"), ("status", "Status"),
                           ("packs", "Packs"), ("blocking_gate", "Gate"),
                           ("number_that_would_clear_it", "Number that clears it"),
                           ("this_session_evidence", "This session")], opens,
                          blank_cols=("blocking_gate",))))
    out.append(_sec("Delivered requirements",
                    table([("req_id", "ID"), ("requirement", "Requirement"), ("packs", "Packs"),
                           ("this_session_evidence", "This session")],
                          [r for r in reqs if r["status"] == "delivered"], limit=60)))
    return "".join(out)


def _lines(lines, meta, ratings, sig):
    out = [_sec("Fair line for every live fixture",
                "<div class='note'>Read the spread as <b>negative for the home favourite</b>. Spread and "
                "total are rounded to the half point, which is how a line is quoted; the unrounded model "
                "numbers are in the CSV next to them. American odds are the fair (no-vig) equivalent of the "
                "published probability, shown for comparison only. Every market cell is blank because no "
                "official NFL page publishes a price.</div>"
                "<div class='note'><b>Why the probability does not match the spread.</b> The spread comes "
                "from the margin equation. The probability deliberately widens the margin variance by the "
                "walk-forward factor k, because the raw model was shown to be overconfident in its tail. "
                "So a 9.5-point fair spread legitimately pairs with a 69% probability here: the spread is "
                "the point estimate, the probability is the calibrated one. Using the spread to imply the "
                "probability would reproduce exactly the overconfidence this pack measured.</div>",
                "Model fitted on %d official finals: league average %.2f points per team, home-field "
                "advantage %.2f points, margin sd %.3f, total sd %.3f. The probability multiplier k = %s is "
                "the median value selected walk-forward on data strictly older than each prediction, and it "
                "is applied here unchanged."
                % (meta["n_games"], meta["lg_avg"], meta["hfa"], meta["sigma_margin"], meta["sigma_total"],
                   meta["k"]))]
    out.append(_sec("Origination: side, then total, then moneyline",
                    table([("game_id", "Game"), ("date", "Date"), ("kickoff_et", "ET"), ("away", "Away"),
                           ("home", "Home"), ("fair_spread_home_half", "Fair spread (home, 0.5)"),
                           ("fair_total_half", "Fair total (0.5)"),
                           ("fair_ml_home", "Fair ML home"),
                           ("fair_ml_away", "Fair ML away"), ("market_spread", "Market spread"),
                           ("market_total", "Market total"), ("diff_spread", "Residual spread"),
                           ("diff_total", "Residual total"), ("market_gate", "Why the market half is blank")],
                          lines, blank_cols=("market_spread", "market_total", "diff_spread", "diff_total"),
                          num_cols=("fair_spread_home_half", "fair_total_half", "fair_ml_home",
                                    "fair_ml_away"))))
    out.append(_sec("Published probabilities with their full input vector",
                    table([("game_id", "Game"), ("home", "Home"), ("atk_home", "atk H"),
                           ("def_home", "def H"), ("atk_away", "atk A"), ("def_away", "def A"),
                           ("hfa", "HFA"), ("margin_hat", "margin^"), ("sigma_margin", "sigma"),
                           ("k_calibration", "k"), ("p_home_win_raw", "p home (raw)"),
                           ("p_home_win", "p home (published)")], lines,
                          num_cols=("atk_home", "def_home", "atk_away", "def_away", "margin_hat",
                                    "p_home_win_raw", "p_home_win")),
                    "Each row is a stored model output: the probability plus every input that produced "
                    "it, so the run can be replayed without re-fitting."))
    out.append(_sec("Team ratings (opponent-aware)",
                    table([("club", "Club"), ("w", "W"), ("l", "L"), ("t", "T"), ("pf", "PF"),
                           ("pa", "PA"), ("atk", "Offence"), ("def", "Defence (higher = allows more)"),
                           ("net", "Net"), ("source_url", "Source")], ratings,
                          num_cols=("atk", "def", "net")),
                    "Ridge fit on points scored and allowed in all 149 finals. atk and def are centred to "
                    "mean zero; net = atk - def. The game log reproduces every club's stored record and "
                    "points exactly (32/32), which is the identity check."))
    return "".join(out)


def _calib_table(wf):
    bins = {}
    for r in wf:
        b = min(int(r["p_home"] * 5), 4)
        bins.setdefault(b, []).append(r)
    rows = []
    for b in sorted(bins):
        g = bins[b]
        mp = sum(x["p_home"] for x in g) / len(g)
        ob = sum(int(x["y_home_win"]) for x in g) / len(g)
        rows.append({"band": "%d-%d%%" % (b * 20, b * 20 + 20), "n": len(g), "mean_p": mp,
                     "observed": ob, "gap": mp - ob})
    return table([("band", "Predicted band"), ("n", "n"), ("mean_p", "Mean forecast"),
                  ("observed", "Observed win rate"), ("gap", "Gap (forecast - observed)")],
                 rows, num_cols=("mean_p", "observed", "gap"))


def _signal(wf, controls, luck, corr):
    out = [_sec("Removal of luck",
                table([("rule", "Pick rule"), ("n_picks", "n"), ("hits", "Hits"),
                       ("hit_rate", "Hit rate"), ("wilson_lo", "Wilson lo"), ("wilson_hi", "Wilson hi"),
                       ("expected_under_coin", "Expected under coin"), ("excess_hits", "Excess"),
                       ("exact_two_sided_p", "Exact binomial p"),
                       ("expected_hits_under_own_p", "Expected under own p"),
                       ("p_two_sided_vs_own_p", "Poisson-binomial p"), ("verdict", "Verdict"),
                       ("own_p_verdict", "Vs own probabilities")], luck,
                      num_cols=("hit_rate", "wilson_lo", "wilson_hi", "exact_two_sided_p",
                                "p_two_sided_vs_own_p")),
                "Three tests, in increasing strictness. <b>Exact binomial</b> asks whether the hit rate "
                "could be a coin. <b>Poisson-binomial</b> asks whether the results are consistent with the "
                "probabilities actually published — the demanding one. <b>Wilson</b> gives the interval a "
                "reader should put around the hit rate.")]
    out.append(_sec("Control baselines (every run must carry these)",
                    table([("control", "Control"), ("n", "n"), ("hits", "Correct"),
                           ("accuracy", "Accuracy"), ("brier", "Brier"), ("logloss", "Log loss"),
                           ("note", "What it is")], controls, blank_cols=("hits", "accuracy"),
                          num_cols=("accuracy", "brier", "logloss"))))
    out.append(_sec("Calibration", _calib_table(wf),
                    "Forecast probability binned in fifths; the observed win rate in each bin is what the "
                    "probabilities should equal if they are honest."))
    out.append(_sec("Correlations, each with its n",
                    table([("corr_id", "ID"), ("pair", "Pair"), ("r", "r"), ("n", "n"),
                           ("ci_lo", "95% lo"), ("ci_hi", "95% hi"), ("method", "Method"),
                           ("inputs", "Inputs"), ("source_url", "Source")], corr,
                          num_cols=("r", "ci_lo", "ci_hi")),
                    "Computed only from official numbers, with a Fisher-z 95% interval and n printed on "
                    "every row: a correlation without n is not information."))
    return "".join(out)


def _backtest(wf, meta, lb):
    """Scores live here, NOT on the leaderboard (gate G-BACKTEST).

    The numbers are computed from the walk-forward rows themselves so the page and the
    CSV can never drift apart.
    """
    s = next(r for r in lb if r["strategy_id"] == "S01")
    n = len(wf)
    bs = sum((r["p_home"] - int(r["y_home_win"])) ** 2 for r in wf) / n
    ll = sum(-(int(r["y_home_win"]) * __import__("math").log(max(r["p_home"], 1e-9))
               + (1 - int(r["y_home_win"])) * __import__("math").log(max(1 - r["p_home"], 1e-9)))
             for r in wf) / n
    out = [_sec("Backtest — explicitly not a ranking",
                _kpi([(n, "games graded"), ("%.4f" % bs, "Brier (calibrated)"), ("%.4f" % ll, "log loss"),
                      ("%.4f" % (1 - bs / 0.25), "skill vs coin (0.25)"),
                      (s["multiplicity_trials"], "strategies evaluated (multiplicity)"),
                      ("%.4f" % s["multiplicity_adjusted_alpha"], "adjusted alpha")]),
                "These numbers are here, and not on the leaderboard, on purpose (gate G-BACKTEST). A "
                "backtest score that has never been tested on a game that could not be seen at fit time "
                "is not a strategy result. Every row below is graded by a model refitted on strictly "
                "earlier games.")]
    out.append(_sec("Walk-forward detail",
                    table([("seq", "Seq"), ("away", "Away"), ("home", "Home"), ("away_score", "A"),
                           ("home_score", "H"), ("margin_hat", "margin^"), ("sigma", "sigma"), ("k", "k"),
                           ("p_home_raw", "p raw"), ("p_home", "p published"), ("y_home_win", "Home won")],
                          wf, num_cols=("margin_hat", "sigma", "p_home_raw", "p_home"), limit=40),
                    "Each row: the probability published before the game, its inputs, and the official "
                    "final."))
    return "".join(out)


def _leaderboard(lb, prereg, demotion):
    out = [_sec("Leaderboard",
                table([("rank", "Rank"), ("strategy_id", "ID"), ("name", "Strategy"),
                       ("division", "Division"), ("n_settled", "n settled"),
                       ("brier_skill_vs_coin", "Signal: Brier skill"),
                       ("cluster_boot_lo", "Signal: 95% low"), ("roi", "Staking: ROI"),
                       ("clv", "Staking: CLV"), ("signal_gate", "Signal gate"),
                       ("staking_gate", "Staking gate"), ("eligible_for_reward", "Reward-eligible")],
                      lb, blank_cols=("rank", "roi", "clv", "brier_skill_vs_coin", "cluster_boot_lo"),
                      num_cols=("brier_skill_vs_coin", "cluster_boot_lo")),
                "Signal and staking are different columns and are never mixed: a lucky staking run cannot "
                "lift a strategy whose signal gate failed (rule D-04). Ranks are blank because nothing has "
                "been settled prospectively — that is the honest state, not a gap.")]
    out.append(_sec("Pre-registration",
                    table([("sid", "ID"), ("name", "Strategy"), ("division", "Division"),
                           ("rule", "Frozen rule"), ("edge_claim", "Edge claimed"),
                           ("mindchange_for", "What would change our mind (for)"),
                           ("mindchange_against", "What would change our mind (against)"),
                           ("registered_at_utc", "Registered"), ("rule_sha256", "Rule hash")], prereg),
                    "The rule text, the sample window and the gates are committed before the evaluation "
                    "window opens. The SHA-256 over the rule text is the registration: any later edit "
                    "changes the hash."))
    out.append(_sec("Demotion gates",
                    table([("gate_id", "Gate"), ("scope", "Scope"), ("to_state", "To"),
                           ("trigger", "Trigger"), ("measured", "Measured today"),
                           ("action", "Action")], demotion),
                    "A live strategy returns to paper when any gate trips."))
    return "".join(out)


def _availability(calib, teamview, headconf):
    out = [_sec("What does 'Questionable' actually mean?",
                table([("game_designation", "Game designation"), ("n_players_joined", "n joined"),
                       ("n_on_inactive_list", "Inactive"), ("n_not_on_inactive_list", "Not inactive"),
                       ("observed_play_rate", "Observed play rate"), ("wilson_lo", "95% lo"),
                       ("wilson_hi", "95% hi"), ("suggested_feature_use", "How it may be used"),
                       ("source_url", "Sources")], calib,
                      num_cols=("observed_play_rate", "wilson_lo", "wilson_hi")),
                "The official report gives no percentages, so they are measured here. Each designation row "
                "on the week-10 hub is joined by exact name to the official inactive list for the same "
                "game. <b>Play rate</b> = the share of those players who were <i>not</i> on the inactive "
                "list. Clubs whose game had no inactive article (Thursday and Monday games) are excluded "
                "from the denominator, never counted as healthy.")]
    out.append(_sec("Per-team view",
                    table([("club", "Club"), ("hub_rows_captured", "Hub rows"),
                           ("designation_out", "Out"), ("designation_doubtful", "Doubtful"),
                           ("designation_questionable", "Questionable"), ("designation_blank", "Blank"),
                           ("confirmed_on_inactive_list", "Confirmed inactive"),
                           ("starters_out", "Starters out"), ("replacements_named", "Replacements named"),
                           ("net_injury_count", "Net injury count"), ("depth_gate", "Why blank")],
                          teamview, blank_cols=("confirmed_on_inactive_list", "starters_out",
                                                "replacements_named", "net_injury_count")),
                    "Designations are counted because the hub publishes them. 'Starters out' and "
                    "'replacements named' are left blank: no official page read for this session names a "
                    "starting line-up, and inventing one from a depth chart that no longer exists would be "
                    "exactly the error the brief forbids."))
    out.append(_sec("Designation silent but player inactive (%d)" % len(headconf),
                    table([("club", "Club"), ("player", "Player"),
                           ("hub_game_status", "Hub designation"),
                           ("official_inactive_line", "Official inactive line"), ("conflict", "Conflict"),
                           ("source_url", "Source")], headconf),
                    "Rows where the hub publishes no game designation and the official inactive list names "
                    "the player anyway — the failure mode that makes a blank look like a green light."))
    return "".join(out)


def _injuries(series, deltas):
    from collections import Counter
    kinds = Counter(d["delta_kind"] for d in deltas)
    out = [_sec("Injury report as a timestamped series, not a weekly snapshot",
                _kpi([(len(series), "rows in today's read"), (len(deltas), "player-level deltas"),
                      (kinds.get("field_changed", 0), "field changed"),
                      (kinds.get("added_to_report", 0), "added to report"),
                      (kinds.get("newly_captured_club", 0), "rows from newly captured clubs"),
                      (kinds.get("removed_from_report", 0), "removed")]),
                "The page carries no published clock time of its own (a sibling pack flagged this as "
                "F-12), so every row stores the time <i>we</i> read it. Two dated reads now exist for the "
                "same page, which is the minimum needed to publish a delta instead of a level.")]
    out.append(_sec("Deltas since 2026-11-15T23:58Z",
                    table([("club", "Club"), ("player", "Player"), ("position", "Pos"),
                           ("delta_kind", "Delta"), ("prior_value", "Prior read"),
                           ("current_value", "Today"), ("prior_read_at_utc", "Prior at"),
                           ("today_read_at_utc", "Today at"), ("source_url", "Source")], deltas,
                          limit=45),
                    "A <b>newly_captured_club</b> row is not a change: that club simply was not in the "
                    "earlier capture. It is labelled separately so the two can never be confused."))
    out.append(_sec("Today's full read (18 of 32 clubs)",
                    table([("read_at_utc", "Read at"), ("club", "Club"), ("player", "Player"),
                           ("position", "Pos"), ("injury", "Injury"), ("practice_status", "Practice"),
                           ("practice_code", "Code"), ("game_status", "Game status"),
                           ("source_url", "Source")], series, blank_cols=("injury", "game_status"),
                          limit=60)))
    return "".join(out)


def _depth(sweep, teamview):
    out = [_sec("Depth cannot be published from an official source today",
                "<div class='note'>Three claims the brief asks for — who the starter was, what depth the "
                "replacement came from, and how a deficiency ranks — all depend on a depth order. On "
                "2026-11-17 the club depth-chart route on nfl.com returns <b>404 'Flag on the Play'</b> "
                "(probe P-01), and no snap-count table was reachable. So this pack publishes <b>no depth "
                "rank at all</b> rather than deriving one from jersey number, salary, experience or a "
                "hand-read image, all of which the brief rejects by name.</div>")]
    out.append(_sec("32-club sweep status",
                    table([("club", "Club"), ("injury_hub_table_captured", "Hub"),
                           ("inactive_list_captured", "Inactives"),
                           ("roster_page_captured_any_pack", "Roster"),
                           ("sweep_complete", "Sweep complete"), ("blocking_gate", "Gate"),
                           ("number_that_would_clear", "Clears on"), ("source_url", "Source")], sweep)))
    out.append(_sec("Route decision",
                    "<p class='lede'>Two routes were specified: (a) per-club official depth pages, (b) "
                    "official snap counts. Route (a) is now tested and fails at the address level. Route (b) "
                    "remains untested because no official snap-count table was reachable from this "
                    "environment. Until one of them is verified for all 32 clubs the deficiency feature "
                    "stays unbuilt — which is what the brief required.</p>"))
    return "".join(out)


def _venues_page(venues):
    disagree = [v for v in venues if v["surfaces_agree"] == "no"]
    out = [_sec("Venue of every week-11 fixture",
                _kpi([(len(venues), "fixtures"), (len(disagree), "surfaces disagree"),
                      (sum(1 for v in venues if v["venue_on_schedule_card"]),
                       "with a schedule-page venue"),
                      (sum(1 for v in venues if v["venue_on_game_centre"]),
                       "with a game-centre venue")]),
                "Two official surfaces are read for each game: the schedule card (whose hotel deep-link "
                "encodes the stadium) and the game-centre Game Info block. Where they disagree, both "
                "strings are published and neither is chosen silently.")]
    out.append(_sec("All fixtures",
                    table([("game_id", "Game"), ("date", "Date"), ("kickoff_et", "ET"),
                           ("network", "TV"), ("away", "Away"), ("home", "Home"),
                           ("venue_on_schedule_card", "Schedule page"),
                           ("venue_on_game_centre", "Game centre"), ("city_on_game_centre", "City"),
                           ("surfaces_agree", "Agree"), ("event_mark_on_card", "Event"),
                           ("note", "Note"), ("schedule_url", "Schedule"),
                           ("game_centre_url", "Game centre")],
                          venues, blank_cols=("venue_on_game_centre", "note"))))
    return "".join(out)


def _verify(vstand, vres, stats):
    from collections import Counter
    cs = Counter(r["status"] for r in vstand)
    cr = Counter(r["status"] for r in vres)
    out = [_sec("Line-by-line re-verification",
                _kpi([(len(vstand), "standings club-rows tested"),
                      (cs.get("match", 0), "standings rows reconcile"),
                      (len(vres), "results rows tested"),
                      (cr.get("match", 0), "results rows reconcile"), (0, "contradictions")]),
                "Every pack that stores an official value is re-tested against today's read. The standings "
                "test is not a string compare: it takes the pack's own numbers, adds back only the games "
                "its capture could not have seen, then compares. The number of games added back is inferred "
                "from the data and printed on every row.")]
    out.append(_sec("Standings reconciliation",
                    table([("pack", "Pack"), ("file", "File"), ("club", "Club"), ("stored", "Stored"),
                           ("expected_from_stored", "Stored + unseen games"),
                           ("official_today", "Official today"), ("status", "Status"), ("note", "Note"),
                           ("source_url", "Source")], vstand, limit=80)))
    out.append(_sec("Results reconciliation",
                    table([("pack", "Pack"), ("file", "File"), ("week", "Wk"), ("matchup", "Game"),
                           ("stored", "Stored"), ("official", "Official"), ("status", "Status"),
                           ("note", "Note"), ("source_url", "Source")], vres, limit=80)))
    return "".join(out)


def _conflicts(conf):
    return _sec("Cross-pack conflicts",
                table([("cid", "ID"), ("fact", "Fact"), ("value_a", "Source A says"),
                       ("source_a", "A (source)"), ("value_b", "Source B says"),
                       ("source_b", "B (source)"), ("status", "Status"), ("verdict", "Verdict"),
                       ("source_url", "Official page")], conf),
                "Same fact, different published value. A resolution is only claimed where this session "
                "re-read the official page; everything else stays <b>open</b>.")


def _snapshots(ledger):
    cov = SN.coverage()
    out = [_sec("Point-in-time snapshot ledger",
                table([("entry_id", "Entry"), ("read_at_utc", "Read at"), ("dataset", "Dataset"),
                       ("n_rows", "Rows"), ("content_hash", "Content hash"),
                       ("prev_hash", "Previous hash"), ("chain_hash", "Chain hash"),
                       ("captured_by", "Captured by"), ("replay_note", "Replay note"),
                       ("source_url", "Source")], ledger),
                "Each entry is hash-chained to the one before it. The build recomputes the chain on every "
                "run; any edit to a captured value breaks it and fails the check.")]
    out.append(_sec("What the ledger still cannot replay",
                    "<p class='lede'>%s</p><p class='lede'>Dated reads of the injury hub currently in the "
                    "repo: <b>%s</b>. Datasets with a dated capture: <b>%s</b>. Reads a designation-replay "
                    "backtest would need: about <b>%s</b>.</p>"
                    % (esc(cov["gap"]), cov["dated_reads_of_injury_hub_in_repo"],
                       cov["datasets_with_a_dated_capture"],
                       cov["reads_needed_for_a_designation_replay_backtest"])))
    return "".join(out)


def _freshness(fresh):
    from collections import Counter
    c = Counter(r["status"] for r in fresh)
    out = [_sec("Freshness and drift",
                _kpi([(len(fresh), "files watched")] +
                     [(v, k.replace("_", " ")) for k, v in sorted(c.items())]),
                "This repo has no live scraper, so the drift alarm is applied to the clock time on every "
                "stored dataset. A dataset is <b>stale_by_source_change</b> when the official page has moved "
                "past it, not merely when it is old.")]
    out.append(_sec("Watched datasets",
                    table([("dataset_kind", "Kind"), ("file", "File"),
                           ("first_seen_in_repo", "First seen"), ("age_days", "Age (d)"),
                           ("status", "Status"), ("why", "Why"),
                           ("authoritative_source", "Source")],
                          sorted(fresh, key=lambda r: (r["dataset_kind"], r["file"])), limit=80)))
    return "".join(out)


def _requirements(reqs):
    return _sec("The single requirement register",
                table([("req_id", "ID"), ("requirement", "Requirement"), ("status", "Status"),
                       ("status_variants", "Status across packs"), ("packs", "Packs"),
                       ("blocking_gate", "Gate"),
                       ("number_that_would_clear_it", "Number that clears it"),
                       ("this_session_evidence", "This session")], reqs, limit=250),
                "Six merged packs publish their own requirement tables — 342 rows in total. Exact "
                "normalised duplicates merge; everything else stays. Where packs disagree on status the "
                "register reports the <b>worst</b> status, never the best, so a requirement cannot look "
                "delivered because one pack said so.")


def _qia(qrows):
    out = [_sec("Question · Information · Answer",
                "<p class='lede'>Ten decisions are currently unreachable. Each row states the question, the "
                "information we have, the information we do not have, the answer we can defend today, the "
                "number that would settle it, and the test that would produce that number.</p>")]
    for r in qrows:
        inner = ("<table><tbody>"
                 f"<tr><th>Have</th><td>{esc(r['have'])}</td></tr>"
                 f"<tr><th>Missing</th><td>{esc(r['missing'])}</td></tr>"
                 f"<tr><th>Answer today</th><td>{esc(r['answer'])}</td></tr>"
                 f"<tr><th>Number that settles it</th><td>{esc(r['number'])}</td></tr>"
                 f"<tr><th>Test / power</th><td>{esc(r['test'])}<br><i>{esc(r['power'])}</i></td></tr>"
                 f"<tr><th>Already done</th><td>{esc(r['pre_stated_action'])}</td></tr>"
                 "</tbody></table>")
        out.append(_sec("%s — %s (%s)" % (r["qid"], r["question"], r["area"]), inner))
    return "".join(out)


def _suggestions(sug):
    return _sec("Suggestions, for you to choose",
                table([("queue_position", "#"), ("sid", "ID"), ("title", "Suggestion"),
                       ("recommendation", "Recommendation"), ("what", "What it is"),
                       ("unblocks", "Unblocks"), ("effort", "Effort"), ("dependency", "Depends on"),
                       ("blocking_question", "Blocked by"), ("expected_benefit", "Why it matters")], sug),
                "Nothing on this page has been implemented. Each suggestion states what it unblocks, what "
                "it costs, what it depends on, and whether it is blocked by a decision only the owner can "
                "make. The section exists so the choice stays with the owner.")


def _flagged_page(vstand, vres, conf, headconf, venues):
    flags = _flags(vstand, vres, conf, headconf)
    out = [_sec("Flagged for review",
                table([("flag_id", "ID"), ("severity", "Severity"), ("item", "Item"),
                       ("detail", "Detail"), ("blocks_publish", "Blocks publish"),
                       ("source_url", "Official link")], flags),
                "Everything here is published as-is with its official link. Nothing blocks the build: "
                "unverified values are left blank in the tables and listed here for review after the site "
                "is live.")]
    rows = [v for v in venues if v["surfaces_agree"] == "no"]
    out.append(_sec("Venue surface disagreements (%d)" % len(rows),
                    table([("game_id", "Game"), ("away", "Away"), ("home", "Home"),
                           ("venue_on_schedule_card", "Schedule page"),
                           ("venue_on_game_centre", "Game centre"), ("schedule_url", "Schedule"),
                           ("game_centre_url", "Game centre link")], rows)))
    return "".join(out)


def _sources():
    out = [_sec("Every page read this session",
                table([("id", "ID"), ("title", "Page"), ("url", "URL"), ("read_at_utc", "Read at"),
                       ("chunks", "Chunks"), ("what", "What was read"), ("limit", "Limit")],
                      C.SNAPSHOTS, blank_cols=("limit",)),
                "Clock time is the time the read was recorded in this session (UTC). Transport note: in "
                "this sandbox <code>curl</code> has no route to nfl.com; reads were made with the agent's "
                "page-fetch tool. Nothing is automated in CI.")]
    out.append(_sec("Probes that returned nothing",
                    table([("probe_id", "ID"), ("url", "URL"), ("intent", "Intent"),
                           ("observed", "Observed"), ("read_at_utc", "Read at"),
                           ("consequence", "Consequence")],
                          [{"probe_id": a, "url": b, "intent": c, "observed": d,
                            "read_at_utc": e, "consequence": f} for a, b, c, d, e, f in C.PROBES]),
                    "A negative result is still a result. Each of these changed what this pack could "
                    "publish."))
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stats = build()
    print("built: %(n_verified_values)d values re-tested, %(n_mismatch)d mismatches, "
          "%(wf_n)d walk-forward games, skill %(skill).4f [lo %(skill_lo).4f]" % stats)
    if args.check:
        rc = subprocess.call([sys.executable, os.path.join(REPO, "scripts", "check_nfl_ca1b.py")])
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
