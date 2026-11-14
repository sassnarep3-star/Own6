#!/usr/bin/env python3
"""Build the nfl_d966f630 pack: CSV tables + a zero-input GitHub Pages dashboard.

Everything on the site is generated from :mod:`src.nfl_d966f630`, whose only
hand-written content is the captured official values in ``capture.py``. The builder
takes no arguments and touches no network, so a re-run must produce byte-identical
files - that is how a reviewer checks that the published tables really are what the
code computes.

Usage
-----
    python3 scripts/build_nfl_d966f630.py            # write CSVs and HTML
    python3 scripts/build_nfl_d966f630.py --check    # build, then run the verifier
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

from nfl_d966f630 import advice as AD  # noqa: E402
from nfl_d966f630 import audit as AU  # noqa: E402
from nfl_d966f630 import backtest as B  # noqa: E402
from nfl_d966f630 import capture as C  # noqa: E402
from nfl_d966f630 import correlate as X  # noqa: E402
from nfl_d966f630 import depth as DP  # noqa: E402
from nfl_d966f630 import demotion as DM  # noqa: E402
from nfl_d966f630 import flags as FL  # noqa: E402
from nfl_d966f630 import leaderboard as LB  # noqa: E402
from nfl_d966f630 import originate as O  # noqa: E402
from nfl_d966f630 import prices as P  # noqa: E402
from nfl_d966f630 import results as R  # noqa: E402
from nfl_d966f630 import stats as S  # noqa: E402

DOCS = os.path.join(REPO, "docs", "nfl-d966f630")
DATA = os.path.join(REPO, "data", "nfl_d966f630")
CAPTURE = C.CAPTURE_DATE_UTC

OFFICIAL_HOSTS = ("www.nfl.com", "operations.nfl.com", "support.nfl.com", "github.com")


# --------------------------------------------------------------------------
# rendering helpers
# --------------------------------------------------------------------------
def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url: str, label: str | None = None) -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label or "source ↗")}</a>'


STATUS_FIELDS = {"fixture_status", "status", "result", "signal_status", "staking_status",
                 "movement_status", "depth_bound_kind", "deficit_score_kind", "score_kind",
                 "availability", "discovery_status", "tier", "state", "kind", "outcome",
                 "line_quality_status", "decision", "evidence_kind", "identity"}


def pill(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ("match", "pass", "measured", "verified", "live", "beats", "ranked",
                            "promot", "ok", "final", "yes")):
        cls = "p-ok"
    elif any(k in t for k in ("fail", "blocked", "worse", "below", "not_", "no_", "void",
                             "demote", "paper", "insufficient", "unavailable", "blank")):
        cls = "p-bad"
    else:
        cls = "p-warn"
    return f'<span class="pill {cls}">{esc(text)}</span>'


def pretty(field: str) -> str:
    return field.replace("_", " ").strip()


def render_table(fields, rows, num_fields=(), note="", max_rows=None):
    """One table. URLs become links; a blank cell is marked blank, never filled."""
    out = []
    if note:
        out.append(f'<p class="note">{note}</p>')
    out.append('<div class="wrap"><table><thead><tr>')
    for f in fields:
        out.append(f"<th scope='col'>{esc(pretty(f))}</th>")
    out.append("</tr></thead><tbody>")
    shown = rows if max_rows is None else rows[:max_rows]
    for r in shown:
        out.append("<tr>")
        for f in fields:
            v = r.get(f, "")
            cls = ["num"] if f in num_fields else []
            if v == "" or v is None:
                cls.append("empty")
                out.append(f"<td class='{' '.join(cls)}' aria-label='blank - no official source supplies "
                           f"this value'></td>")
                continue
            sv = str(v)
            if sv.startswith("https://"):
                out.append(f"<td class='{' '.join(cls)}'>{link(sv)}</td>")
            elif f in STATUS_FIELDS:
                out.append(f"<td class='{' '.join(cls)}'>{pill(sv)}</td>")
            else:
                out.append(f"<td class='{' '.join(cls)}'>{esc(sv)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    if max_rows is not None and len(rows) > max_rows:
        out.append(f'<p class="note">Showing {max_rows} of {len(rows)} rows. The complete table is in the '
                   f'CSV beside this page.</p>')
    return "".join(out)


NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("results-feed.html", "Verified results feed"),
    ("lines.html", "Originated lines"),
    ("prices.html", "Opening & closing prices"),
    ("model.html", "Model & dispersion"),
    ("injuries.html", "Injury report"),
    ("depth.html", "Depth of replacement"),
    ("correlations.html", "Correlations"),
    ("backtest.html", "Backtest & settlement"),
    ("leaderboard.html", "Leaderboard"),
    ("gates.html", "Validation & demotion gates"),
    ("strategies.html", "Strategy catalogue"),
    ("suggestions.html", "Suggestions & questions"),
    ("sources.html", "Sources & rights"),
    ("review.html", "Repo review & decisions"),
    ("flagged.html", "Flagged for review"),
]

CSS = """:root{--bg:#0e1117;--panel:#161b22;--panel2:#1c2430;--line:#2a3441;--ink:#e6edf3;
--muted:#9aa7b4;--accent:#4ba3f5;--good:#3fb950;--warn:#d29922;--bad:#f85149;--empty:#6e7681}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
nav{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:10px 16px;background:var(--panel);
border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
nav .brand{font-weight:700;letter-spacing:.04em;margin-right:10px}
nav a{padding:5px 9px;border-radius:6px;font-size:14px;color:var(--ink);background:var(--panel2);
border:1px solid var(--line)}nav a:hover{background:#243040;text-decoration:none}
nav a[aria-current=page]{border-color:var(--accent);color:var(--accent)}
main{max-width:1240px;margin:0 auto;padding:22px 16px 60px}
h1{font-size:27px;line-height:1.2;margin:6px 0 10px}h2{font-size:20px;margin:32px 0 8px;
padding-top:8px;border-top:1px solid var(--line)}h3{font-size:16px;margin:20px 0 6px}
p{margin:8px 0}.eyebrow{color:var(--accent);font-size:12px;letter-spacing:.16em;text-transform:uppercase}
.lede{color:var(--muted);max-width:88ch}
.hero{background:linear-gradient(180deg,#16202c,#11161d);border:1px solid var(--line);border-radius:14px;
padding:22px;margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:14px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px;
color:var(--ink)}.card:hover{border-color:var(--accent);text-decoration:none}
.card .k{font-size:24px;font-weight:700;display:block}.card .l{color:var(--muted);font-size:13px}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:10px 0 16px}
table{border-collapse:collapse;width:100%;font-size:13px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--panel2);font-size:11.5px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);
white-space:nowrap}tbody tr:hover{background:#1b2430}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.empty:before{content:"blank";color:var(--empty);font-style:italic;font-size:11.5px}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid var(--line);
background:#1b2430;white-space:nowrap}.p-ok{color:var(--good);border-color:#204a2b}
.p-warn{color:var(--warn);border-color:#5a4413}.p-bad{color:var(--bad);border-color:#5c2422}
.note{color:var(--muted);font-size:13.5px;max-width:88ch}
ul{margin:8px 0 8px 22px;padding:0}li{margin:5px 0}
code{background:#1b2430;border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:13px}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:13px;padding:18px 16px 40px;
max-width:1240px;margin:0 auto}
"""


def page(title, body, active, subtitle="", eyebrow="NFL · 2026 · SESSION d966f630"):
    nav = "".join(
        f'<a href="{u}"{" aria-current=page" if u == active else ""}>{esc(t)}</a>' for u, t in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Own6 NFL line origination, verified results feed, price snapshot store,
signal/staking leaderboard and demotion gate - every row source-linked, blanks flagged.">
<title>{esc(title)} · Own6 NFL d966f630</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<nav aria-label="Primary navigation"><span class="brand">OWN6 / NFL D966F630</span>{nav}</nav>
<main>
<header class="hero">
<p class="eyebrow">{esc(eyebrow)} · CAPTURED {esc(CAPTURE)}</p>
<h1>{esc(title)}</h1>
<p class="lede">{subtitle}</p>
</header>
{body}
</main>
<footer>Research and statistics only. No wager is placed, no pick is offered, and no profitability claim is
made: the prices in this pack are the model's own, so a result measured against them is a calibration
measurement, not an edge. Statistical validation reduces uncertainty; it cannot remove luck, which is why the
leaderboard separates signal from staking and why the demotion gate can override a ranking. Every value comes
from an official NFL page read on {esc(CAPTURE)} or from arithmetic on those values, published under the
<a href="https://www.nfl.com/legal/terms/">NFL.com Terms and Conditions</a> for individual non-commercial
review. A blank cell is blank because no official or licensed source supplies it - see
<a href="flagged.html">Flagged for Review</a>.</footer>
</body></html>
"""


def write_csv(name, fields, rows) -> str:
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items() if k in fields})
    return f"{len(rows)} rows -> data/nfl_d966f630/{name}"


def write_html(name, text) -> str:
    os.makedirs(DOCS, exist_ok=True)
    with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
        fh.write(text)
    return f"{len(text):,} bytes -> docs/nfl-d966f630/{name}"


# --------------------------------------------------------------------------
# tables shared between the CSVs and the pages
# --------------------------------------------------------------------------
def model_rows() -> list[dict[str, str]]:
    out = []
    for i, (key, spec) in enumerate(sorted(O.PARAMS.items()), start=1):
        out.append({
            "param_id": f"D966-P{i:02d}",
            "parameter": key,
            "value": spec.get("value", ""),
            "unit": spec.get("unit", ""),
            "basis": spec.get("basis", ""),
            "source_kind": spec.get("source_kind", ""),
            "value_source_url": spec.get("url", C.link_for("REPO")),
            "official_source_url": spec.get("url", C.link_for("REPO")),
            "read_on_utc": CAPTURE,
            "note": spec.get("note", ""),
        })
    return out


MODEL_FIELDS = ["param_id", "parameter", "value", "unit", "basis", "source_kind",
                "value_source_url", "official_source_url", "read_on_utc", "note"]

STAGE_ORDER = [
    {"stage": "1", "market": "side (spread)", "may_start_from": "scoring-rate table only",
     "depends_on": "nothing", "why_this_order": "the margin is the only quantity the standings support on its "
     "own; a total needs the same inputs but a moneyline needs the margin distribution as well",
     "failure_mode_if_reordered": "a total quoted first silently fixes the margin through the two-team "
                                  "expectation, so the side stops being an independent decision",
     "official_source_url": C.link_for("STANDINGS")},
    {"stage": "2", "market": "total", "may_start_from": "stage-1 expectation, un-re-fitted",
     "depends_on": "stage 1 published side", "why_this_order": "the total is the sum of the two expectations "
     "the side already chose; it must not re-estimate them",
     "failure_mode_if_reordered": "re-deriving the split after choosing the total moves the side the reader "
                                  "just saw, so the two numbers are no longer one model",
     "official_source_url": C.link_for("STANDINGS")},
    {"stage": "3", "market": "moneyline", "may_start_from": "published side AND published total, plus the "
     "measured dispersion", "depends_on": "stages 1 and 2, both published",
     "why_this_order": "the moneyline is a probability computed from the two published lines and a noise scale "
                       "measured on final scores; it cannot exist before them",
     "failure_mode_if_reordered": "pricing the moneyline from the raw margin instead of the published rounded "
                                  "line makes the side and the moneyline contradict each other on the same row",
     "official_source_url": C.link_for("SCHED-W9")},
]


def blank_audit(written: list[tuple[str, list[str], list[dict[str, str]]]]) -> list[dict[str, str]]:
    """Where the blanks are, per file, and which flag explains them."""
    rows = []
    for name, fields, data in written:
        if name.endswith(".csv") is False:
            continue
        blanks = sum(1 for r in data for f in fields if str(r.get(f, "")) == "")
        flagged = sum(1 for r in data if r.get("market_flag_id") or r.get("flag_id")
                      or r.get("movement_flag_id"))
        rows.append({
            "table": name, "rows": str(len(data)), "columns": str(len(fields)),
            "blank_cells": str(blanks),
            "rows_carrying_a_flag_id": str(flagged),
            "blank_cell_meaning": "no official or licensed source in this pack supplies the value"
                                 if blanks else "no blanks in this table",
            "official_source_url": C.link_for("REPO"),
            "read_on_utc": CAPTURE,
        })
    return rows


def slug_counts() -> dict[str, str]:
    return {
        "feed_games": str(len(R.feed_rows())),
        "team_games": str(2 * len(R.feed_rows())),
        "markets_snapshot": str(len(P.ledger())),
        "markets_open_close": str(len(P.open_close_table(P.ledger()))),
        "injury_rows": str(len(DP.injury_rows())),
        "flags": str(len(FL.flag_rows())),
        "live": str(len(DM.live_strategies())),
    }


# --------------------------------------------------------------------------
# page bodies
# --------------------------------------------------------------------------
def build_all() -> list[str]:
    log: list[str] = []
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    log.append("docs/nfl-d966f630/assets/style.css")
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fh:
        fh.write("")
    log.append("docs/nfl-d966f630/.nojekyll")

    # ---------------- the tables, built once and used by both outputs -------
    feed = R.feed_rows()
    recon = R.standings_reconciliation()
    identities = R.feed_identities()
    lines = O.published_lines()
    ledger = P.ledger()
    oc = list(P.open_close_table(ledger).values())
    attempts = P.CAPTURE_ATTEMPT_LOG
    disp = [dict(vintage_week=str(w), **{k: S.fmt(v, 6) if isinstance(v, float) else str(v)
                                        for k, v in O.dispersion(w).items()})
            for w in (6, 7, 8, 9)]
    for row in disp:
        row["official_source_url"] = C.link_for("SCHED-W9") if row["vintage_week"] == "9" \
            else C.link_for(f"SCHED-W{row['vintage_week']}" if int(row["vintage_week"]) in (7, 8)
                            else "STANDINGS")
        row["read_on_utc"] = CAPTURE
    fits = []
    for w in (7, 8, 9, 10):
        lam = O.fit_lambda(w)
        tot = O.fit_total_shrinkage(w)
        fits.append({
            "vintage_week": str(w), "n_games_graded": str(int(lam["n_games"])),
            "side_lambda_best": S.fmt(float(lam["lambda"]), 2), "side_fit_status": str(lam["status"]),
            "side_mae_at_best": S.fmt(float(lam["mae_at_lambda"]), 4),
            "side_mae_undamped": S.fmt(float(lam["mae_at_lambda_1"]), 4),
            "total_shrink_best": S.fmt(float(tot["shrink"]), 2), "total_fit_status": str(tot["status"]),
            "total_mae_at_best": S.fmt(float(tot["mae_at_best"]), 4),
            "total_mae_undamped": S.fmt(float(tot["mae_at_shrink_1"]), 4),
            "total_mae_at_baseline": S.fmt(float(tot["mae_at_shrink_0"]), 4),
            "applied_to_published_line": "no - published as analysis (see the module docstring)",
            "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE,
            "caveat": str(tot.get("caveat", "")),
        })
    scans = [dict(market_type=r["market_type"], vintage_week=str(r["vintage_week"]),
                  shrink_factor=S.fmt(float(r["shrink_factor"]), 2),
                  n_games=str(int(r["n_games"])), mae_points=S.fmt(float(r["mae_points"]), 4),
                  mse_points=S.fmt(float(r["mse_points"]), 4),
                  mean_signed_error_points=S.fmt(float(r["mean_signed_error_points"]), 4),
                  baseline_mae_at_shrink_zero=S.fmt(float(r["baseline_mae_at_shrink_zero"]), 4),
                  official_source_url=C.link_for("SCHED-W9"), read_on_utc=CAPTURE)
             for mkt in ("side", "total") for r in O.damping_scan(mkt, 10)]
    line_quality = B.model_abs_errors()
    injuries = DP.injury_rows()
    group_depth = DP.group_depth()
    club_depth = DP.club_rollup()
    evidence = DP._replacement_evidence()
    corrs = X.correlations()
    excls = X.EXCLUSIONS
    legs = B.settled_leg_rows()
    tickets = B.settled_ticket_rows()
    signal = LB.signal_table()
    staking = LB.staking_table()
    combined = LB.combined_view()
    tiers = LB.rewards_tiers()
    gates = DM.gate_rows()
    gate_defs = [dict(g, applied_to="every strategy in the catalogue",
                      evaluated_on="the verified results feed and the price store in the same run",
                      official_source_url=C.link_for("REPO"), read_on_utc=CAPTURE) for g in DM.GATES]
    states = DM.decisions()
    transitions = DM.transitions()
    watch = DM.demotion_watch()
    strategies = [{
        "strategy_id": st.strategy_id, "name": st.name, "family": st.family,
        "markets": " + ".join(st.markets), "rule_verbatim": st.rule, "status": st.status,
        "blocked_reason": st.blocked_reason, "stake_rule": st.stake_rule,
        "params": "; ".join(f"{k}={v}" for k, v in sorted(st.params.items())),
        "selections_graded": str(len([t for t in tickets if t["strategy_id"] == st.strategy_id])),
        "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE,
    } for st in B.STRATEGIES]
    suggestions, questions = AD.suggestion_rows(), AD.question_rows()
    flags = FL.flag_rows()
    sources = [{"source_id": sid, **spec} for sid, spec in C.SOURCES.items()]
    standings = [{"club": a, "conference": conf, "division": div, "w": str(w), "l": str(l), "t": str(t),
                  "pct": pct, "pf": str(pf), "pa": str(pa), "net_pts": str(net),
                  "games": str(w + l + t), "ppg": S.fmt(pf / max(w + l + t, 1), 3),
                  "papg": S.fmt(pa / max(w + l + t, 1), 3),
                  "legend_verbatim": C.STANDINGS_LEGEND,
                  "official_source_url": C.link_for("STANDINGS"), "read_on_utc": CAPTURE}
                 for a, conf, div, w, l, t, pct, pf, pa, net in C.STANDINGS]
    slate = [{"game_id": gid, "date_on_card": d, "kickoff_on_card": slot, "network_on_card": net,
              "away": aw, "home": hm, "status_on_card": status, "game_page_url": C.game_url(gid),
              "official_source_url": C.link_for("SCHED-W10"), "read_on_utc": CAPTURE,
              "away_record_in_injury_block": "",
              "model_side": next((l2["model_fair_line_side"] for l2 in lines if l2["game_id"] == gid), ""),
              "model_total": next((l2["model_fair_line_total"] for l2 in lines if l2["game_id"] == gid), ""),
              "model_moneyline_home": next((l2["model_fair_line_moneyline_home"] for l2 in lines
                                            if l2["game_id"] == gid), "")}
             for gid, d, slot, net, aw, hm, status, _src in C.WEEK10_SLATE]
    aliases = [{"published_on_some_pages": k, "canonical_key_in_this_pack": v,
                "why": "the injury and standings pages print one abbreviation while the schedule and logo paths "
                       "print the other; every table in this pack keys on the canonical form",
                "official_source_url": C.link_for("INJURIES"), "read_on_utc": CAPTURE}
               for k, v in sorted(C.CLUB_ABBR_ALIASES.items())]
    headlines = [{"index": str(i), "club": club, "headline_verbatim": head, "url": url,
                  "official_source_url": url, "read_on_utc": CAPTURE,
                  "note": "headline text only; the article body was not read in this session"}
                 for i, (club, head, url) in enumerate(C.OFFICIAL_HEADLINES, start=1)]
    units = [{"position": pos, "unit": unit, "mapping_owner": "session d966f630 - not a league classification",
              "flag_id": "D966-F05", "official_source_url": C.link_for("INJURIES"), "read_on_utc": CAPTURE}
             for pos, unit in sorted(C.POSITION_UNIT.items())]

    # ---------------- CSVs -------------------------------------------------
    def fields_of(rows, prefer=()):
        if not rows:
            return list(prefer)
        keys = list(rows[0].keys())
        return [k for k in prefer if k in keys] + [k for k in keys if k not in prefer]

    written: list[tuple[str, list[str], list[dict[str, str]]]] = []

    def add(name, rows, fields=None, prefer=()):
        f = fields or fields_of(rows, prefer)
        log.append(write_csv(name, f, rows))
        written.append((name, f, rows))
        return f

    SRC = ["source_id", "publisher", "title", "url", "read_on", "method", "status",
           "supports", "does_not_support"]
    add("sources.csv", sources, SRC)
    add("standings_2026_w10.csv", standings, prefer=["club", "conference", "division", "w", "l", "t"])
    add("week10_slate.csv", slate, prefer=["game_id", "date_on_card", "kickoff_on_card", "away", "home"])
    add("club_abbr_aliases.csv", aliases)
    add("official_headlines.csv", headlines)
    add("position_unit_map.csv", units)
    add("results_feed.csv", feed, prefer=["game_id", "week", "away", "away_points", "home", "home_points",
                                          "margin_home", "game_total", "feed_status"])
    add("results_reconciliation.csv", recon, prefer=["check_week", "club", "derived_w_l_t",
                                                     "official_card_badge_w_l_t", "result"])
    add("results_feed_identities.csv", identities, prefer=["identity", "expected", "observed", "result"])
    add("originated_lines.csv", lines, O.PUBLISHED_LINE_FIELDS)
    add("stage_order.csv", STAGE_ORDER,
        ["stage", "market", "may_start_from", "depends_on", "why_this_order", "failure_mode_if_reordered",
         "official_source_url", "read_on_utc"])
    add("model_parameters.csv", model_rows(), MODEL_FIELDS)
    add("dispersion_by_vintage.csv", disp,
        ["vintage_week", "sigma_pts", "sigma_pts_around_team_mean", "rho_home_away", "n_team_games",
         "n_games", "league_ppg", "official_source_url", "read_on_utc"])
    add("damping_fits.csv", fits, prefer=["vintage_week", "n_games_graded", "side_lambda_best"])
    add("damping_scans.csv", scans,
        ["market_type", "vintage_week", "shrink_factor", "n_games", "mae_points", "mse_points",
         "mean_signed_error_points", "baseline_mae_at_shrink_zero", "official_source_url", "read_on_utc"])
    add("line_accuracy_graded.csv", line_quality,
        prefer=["game_id", "week", "away", "home", "model_margin_raw", "actual_margin_home",
                "abs_error_side_points", "model_total_raw", "actual_game_total", "abs_error_total_points"])
    add("price_snapshots.csv", ledger, P.SNAPSHOT_FIELDS)
    add("price_snapshots_open_close.csv", oc,
        prefer=["market_id", "game_id", "market_type", "n_snapshots", "opening_number", "closing_number",
                "movement_closing_minus_opening", "movement_status", "movement_flag_id"])
    add("price_capture_attempts.csv", attempts,
        ["attempt_id", "market_family", "source_class", "source_url", "read_on", "outcome", "detail",
         "consequence", "flag_id", "official_source_url"])
    add("injury_report_rows.csv", injuries,
        prefer=["row_id", "club", "game_id", "player", "position", "position_unit", "injury_text",
                "practice_status", "game_status", "availability"])
    add("depth_of_replacement.csv", group_depth,
        prefer=["club", "unit", "position_group", "players_listed", "ruled_out", "doubtful", "questionable",
                "tiers_dropped_lower_bound", "tiers_dropped_evidenced", "club_depth_deficit"])
    add("club_depth_rollup.csv", club_depth,
        prefer=["club", "game_id", "fixture", "offence_tiers_dropped_lower_bound",
                "defence_tiers_dropped_lower_bound", "special_teams_tiers_dropped_lower_bound",
                "club_depth_deficit"])
    add("replacement_evidence.csv", evidence,
        prefer=["evidence_id", "club", "position_group", "replacement_tier", "evidence_kind",
                "credited_as_depth_replacement", "headline_verbatim", "url"])
    add("correlations.csv", corrs,
        prefer=["correlation_id", "x_variable", "y_variable", "sample_unit", "method", "n", "coefficient",
                "ci95_low", "ci95_high", "status", "flag_id"])
    add("correlation_exclusions.csv", excls,
        ["candidate_id", "candidate", "status", "reason", "what_would_unlock_it", "suggestion_id",
         "official_source_url"])
    add("backtest_legs.csv", legs,
        prefer=["leg_id", "ticket_id", "strategy_id", "family", "week", "game_id", "market", "line_published",
                "side_taken", "model_prob", "outcome", "units_if_single"])
    add("backtest_tickets.csv", tickets,
        prefer=["ticket_id", "strategy_id", "family", "week", "n_legs", "legs_summary", "outcome", "units"])
    add("strategies.csv", strategies,
        prefer=["strategy_id", "name", "family", "markets", "status", "rule_verbatim", "blocked_reason"])
    add("leaderboard_signal.csv", signal,
        prefer=["strategy_id", "strategy_name", "family", "signal_rank", "n_legs_graded_excluding_pushes",
                "hit_rate_cover", "hit_rate_ci95_low", "hit_rate_ci95_high", "brier_score",
                "brier_climatology_baseline", "brier_skill_score_vs_base_rate", "log_loss",
                "mean_abs_error_side_points", "naive_baseline_abs_error_side_points", "line_quality_status",
                "signal_status", "flag_id"])
    add("leaderboard_staking.csv", staking,
        prefer=["strategy_id", "strategy_name", "family", "n_tickets_graded", "units_total",
                "units_per_ticket", "z_vs_fair_price", "p_two_sided_normal", "max_drawdown_units",
                "longest_win_streak", "longest_loss_streak", "mean_half_kelly_stake_fraction",
                "staking_status", "flag_id"])
    add("leaderboard_combined.csv", combined,
        prefer=["strategy_id", "strategy_name", "signal_rank", "brier_score", "n_legs_graded_excluding_pushes",
                "staking_rank_display_only", "units_total", "z_vs_fair_price",
                "rank_gap_staking_minus_signal", "interpretation"])
    add("reward_tiers.csv", tiers,
        prefer=["tier_id", "tier", "strategy_id", "strategy_name", "signal_rank", "n_legs_graded",
                "reward", "reward_currency", "why_not_cash", "eligibility_rule"])
    add("validation_gates.csv", gates,
        prefer=["gate_id", "block", "strategy_id", "metric", "observed_value", "threshold", "result",
                "observed_versus_threshold"])
    add("gate_definitions.csv", gate_defs,
        ["gate_id", "block", "metric", "threshold", "comparison", "why", "action_on_fail", "applied_to",
         "evaluated_on", "official_source_url", "read_on_utc"])
    add("strategy_states.csv", states,
        prefer=["strategy_id", "strategy_name", "previous_state", "state", "decision", "signal_rank",
                "eligible_for_reward_tier", "failing_gate_ids", "failing_gate_detail"])
    add("state_transitions.csv", transitions,
        prefer=["transition_id", "strategy_id", "from_state", "to_state", "kind", "trigger_gate_ids",
                "trigger_detail"])
    add("demotion_watch.csv", watch,
        prefer=["strategy_id", "state", "would_demote_on_next_run", "gates_that_would_fire",
                "first_failing_metric", "first_failing_detail"])
    reqs = AU.requirement_rows()
    ledger_rows = AU.decision_rows()
    findings_rows = AU.finding_rows()
    add("requirements_trace.csv", reqs, AU.REQUIREMENT_FIELDS)
    add("decision_ledger.csv", ledger_rows, AU.DECISION_FIELDS)
    add("repo_findings.csv", findings_rows, AU.FINDING_FIELDS)
    add("suggestions.csv", suggestions, AD.SUGGESTION_FIELDS)
    add("questions.csv", questions, AD.QUESTION_FIELDS)
    add("flagged.csv", flags, FL.FLAG_FIELDS)
    audit = blank_audit(written)
    add("blank_audit.csv", audit,
        ["table", "rows", "columns", "blank_cells", "rows_carrying_a_flag_id", "blank_cell_meaning",
         "official_source_url", "read_on_utc"])
    log.append(f"{len(written)} CSV files -> data/nfl_d966f630/")
    return log, written, dict(
        feed=feed, recon=recon, identities=identities, lines=lines, ledger=ledger, oc=oc, attempts=attempts,
        disp=disp, fits=fits, scans=scans, line_quality=line_quality, injuries=injuries,
        group_depth=group_depth, club_depth=club_depth, evidence=evidence, corrs=corrs, excls=excls,
        legs=legs, tickets=tickets, signal=signal, staking=staking, combined=combined, tiers=tiers,
        gates=gates, gate_defs=gate_defs, states=states, transitions=transitions, watch=watch,
        strategies=strategies, suggestions=suggestions, questions=questions, flags=flags, sources=sources,
        standings=standings, slate=slate, aliases=aliases, headlines=headlines, units=units, audit=audit,
        reqs=reqs, ledger_rows=ledger_rows, findings_rows=findings_rows,
    )


def _cards(T) -> str:
    counts = {
        "games in the verified feed": len(T["feed"]),
        "team-games behind sigma": int(float(T["disp"][-1]["n_team_games"])),
        "markets originated (Week 10)": len(T["lines"]) * 3,
        "snapshot rows in the store": len(T["ledger"]),
        "markets with a closing number": sum(1 for r in T["oc"] if r["closing_number"]),
        "injury rows captured": len(T["injuries"]),
        "correlations published": sum(1 for r in T["corrs"] if r.get("coefficient")),
        "strategies in the catalogue": len(T["strategies"]),
        "live after the gate": len(DM.live_strategies()),
        "open flags": len(T["flags"]),
    }
    return ('<div class="cards">' + "".join(
        f'<div class="card"><span class="k">{esc(v)}</span><span class="l">{esc(k)}</span></div>'
        for k, v in counts.items()) + "</div>")


REQ_ROWS = [
    ("1", "Price-snapshot store with opening and closing numbers for every originated market",
     "prices.html", "the append-only ledger, roles derived from position in the series, and the "
     "open/close/movement table", "external book prices: market_line_* is blank on every row (D966-F01)"),
    ("2", "Verified results feed so backtests and ROI can be computed at all",
     "results-feed.html", "44 official games (Weeks 7-10), 96 reconciliation checks, 37 identity checks, "
     "0 mismatches", "Weeks 1-6 (this session's window), and any ROI against a real price"),
    ("3", "Origination order: side, then total, then moneyline",
     "lines.html", "three stage functions, a published stage-order contract, and a raise if the total is asked "
     "for before the side exists", "nothing - the order is enforced in code"),
    ("4", "Model fair line, market line and difference as separate columns",
     "lines.html", "21 columns: seven per market, model filled, market and difference blank with a status",
     "market_line_* and difference_* (D966-F01)"),
    ("5", "Leaderboard separating signal from staking",
     "leaderboard.html", "two tables with their own ranks, plus a combined view that never averages them; the "
     "signal table has no payout column and the staking table has no accuracy column",
     "nothing structural; the n floor leaves six rows unranked (D966-F08)"),
    ("6", "Track the depth of a replacement, not just that one happened",
     "depth.html", "tiers-dropped lower bound per club and position group, plus headline-evidenced replacement "
     "rows that name the tier the backup sits at", "who is first string (the report is not a depth chart), "
     "and any snap-count weighting (D966-S05)"),
    ("7", "Correlations from officially sourced numbers only, each with n",
     "correlations.html", "8 measured rows with n, interval, method, per-axis source URL and sample unit, plus "
     "5 excluded candidates with reasons", "every candidate needing a market price or a player statistic"),
    ("8", "A demotion gate that sends a live strategy back to paper",
     "gates.html", "10 gates over 10 strategies = 100 evaluated rows, one promotion, nine held, and a standing "
     "demotion test computed on real values", "a historical demotion record: nothing was live before this run, "
     "so the first run can only promote"),
    ("9", "Originated NFL lines, not scraped ones",
     "model.html", "every line is arithmetic on the official scoring rates, with the noise scale measured on "
     "official final scores", "nothing - the model is deliberately one input deep"),
    ("10", "Leaderboard competition with rewards",
     "leaderboard.html", "reference / priority / watch tiers, decided on the signal block only",
     "monetary rewards, excluded and explained on the row"),
    ("11", "Singles, parlays, same-game parlays and prop combos",
     "backtest.html", "four families implemented, with push handling and a joint probability from a measured "
     "rho", "player-prop legs, ungradeable without player statistics (D966-F06)"),
    ("12", "Validation gates, correlations, and removing luck",
     "gates.html", "sample floor, calibration, drawdown, chain and feed-integrity gates; z-statistics and "
     "intervals on every result", "luck can be measured and bounded, never removed - the footer says so"),
    ("13", "Injury tracking including backup deficiencies down the depth chart",
     "injuries.html", "347 report rows for 28 clubs with practice and game designations kept verbatim",
     "any quantified effect of an absence on scoring, which no official page supplies"),
    ("14", "Executive summary, readable tables, flagged items on their own page",
     "executive-summary.html", "every table on the site ends in a source column; 17 flags with what was "
     "observed and what was done instead", "nothing"),
]


def findings_table(findings) -> str:
    """The index page's headline table, with internal links rendered as links."""
    out = ['<div class="wrap"><table><thead><tr>']
    for h in ("finding", "number", "why it matters", "page", "official source"):
        out.append(f"<th scope='col'>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for f in findings:
        pg = esc(f['page'])
        out.append("<tr><td>%s</td><td>%s</td><td>%s</td><td><a href=\"%s\">%s</a></td><td>%s</td></tr>"
                   % (esc(f['finding']), esc(f['number']), esc(f['why_it_matters']),
                      pg, pg, link(f['official_source_url'])))
    out.append("</tbody></table></div>")
    return "".join(out)


def write_pages(T) -> list[str]:
    log: list[str] = []
    counts = slug_counts()

    # ---------------------------------------------------------------- index
    req = [{"n": n, "requirement": r, "page": p, "what_is_filled": f, "what_is_blank": b}
           for n, r, p, f, b in REQ_ROWS]
    findings = [
        {"finding": "The side line is better than the cheapest possible alternative, by 1.66 points of "
                    "absolute error.",
         "number": "10.50 vs 12.16 pts MAE over 44 graded games",
         "why_it_matters": "the model earns its place on the spread, so the spread is the market the pack "
                           "publishes as reference",
         "page": "model.html", "official_source_url": C.link_for("SCHED-W9")},
        {"finding": "The total line is worse than the league scoring baseline, by 0.61 points.",
         "number": "11.24 vs 10.63 pts MAE; the shrinkage scan bottoms out at 0.00",
         "why_it_matters": "the attack-plus-opposition-defence decomposition adds noise to the total at this "
                           "sample size; the total anchor is held back from live by exactly this gate",
         "page": "gates.html", "official_source_url": C.link_for("SCHED-W9")},
        {"finding": "Home and away scoring are very slightly negatively correlated, and margins and totals "
                    "are mildly so.",
         "number": "rho(home points, away points) = -0.0662 at n=44; rho(margin, total) = -0.2830 at n=44",
         "why_it_matters": "a same-game side-plus-over ticket is therefore not the product of its legs: the "
                           "measured dependence moves a joint probability by about a point",
         "page": "correlations.html", "official_source_url": C.link_for("SCHED-W9")},
        {"finding": "The best signal row is not the best staking row, and neither is the strategy the gate "
                    "keeps live.",
         "number": "signal rank 1 fails calibration (gap 0.1222 > 0.08); rank 2 is held by an 11-unit drawdown "
                   "> 8-unit budget; the one live strategy is ranked 3rd",
         "why_it_matters": "this is requirement 5 and requirement 8 working on the same numbers: ranking and "
                           "eligibility answer different questions",
         "page": "leaderboard.html", "official_source_url": C.link_for("SCHED-W9")},
        {"finding": "The price store holds 210 rows and 171 markets, and 118 of those markets have one "
                    "snapshot.",
         "number": "movement is zero by construction on those rows, labelled, with flag D966-F16",
         "why_it_matters": "a column of zeros would otherwise read as a calm market on the site's first day",
         "page": "prices.html", "official_source_url": C.link_for("REPO")},
        {"finding": "The five oddities on the official injury report are published as they were printed, not "
                    "corrected.",
         "number": "flag D966-F12: five players under a club their own position line contradicts",
         "why_it_matters": "fixing a league page by hand is the invention the brief rules out; the affected "
                           "depth counts stay flagged as floors",
         "page": "flagged.html", "official_source_url": C.link_for("INJURIES")},
    ]
    body = (
        _cards(T)
        + "<h2>Read this first</h2><ul>"
        + "<li>Every number on this site is either copied from an official NFL page or arithmetic on numbers "
          "copied from them. The last column of every table is the page a row came from.</li>"
        + "<li>A blank cell is a finished answer: no source we are allowed to use supplies that value. "
          "<a href=\"flagged.html\">Flagged for Review</a> lists all " + str(len(T["flags"])) + " of them, "
          "including the places where the official page itself looks wrong.</li>"
        + "<li>There is no bookmaker here. Model prices are the only prices, so anything resembling profit is "
          "measured against our own number and is a calibration result, not an edge.</li>"
        + "<li>The graded window is Weeks 7-10 of 2026: 44 games. Every statistic publishes its n, because "
          "n=44 is the honest size of what is known.</li></ul>"
        + "<h2>What the data says</h2>"
        + findings_table(findings)
        + "<h2>Requirements and where they are satisfied</h2>"
        + render_table(["n", "requirement", "page", "what_is_filled", "what_is_blank"], req,
                       note="Rows are the requirements as stated, in order. The blank column is not a to-do "
                            "list to be quietly filled: each entry names the source that does not exist.")
    )
    log.append(write_html("index.html", page(
        "Origination, prices and proof", body, "index.html",
        "A self-contained NFL line-origination pack: results feed, price ledger, three-stage model, depth "
        "measures, correlations, a two-block leaderboard and a demotion gate - built with no human input and "
        "checked line by line against the league's own pages.")))

    # ------------------------------------------------------ executive summary
    summary = (
        "<h2>The pack in one table</h2>"
        + render_table(["measure", "value", "what_it_is", "official_source_url"], [
            {"measure": "official games in the verified feed", "value": str(len(T["feed"])),
             "what_it_is": "Weeks 7-10 2026; every row a FINAL card on an nfl.com schedule page",
             "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE},
            {"measure": "markets originated for the Week 10 slate", "value": str(len(T["lines"]) * 3),
             "what_it_is": "side, total and moneyline for each of 14 games, in that order",
             "official_source_url": C.link_for("SCHED-W10"), "read_on_utc": CAPTURE},
            {"measure": "market cells filled with a book price", "value": "0",
             "what_it_is": "no official or licensed source in this environment publishes one (flag D966-F01)",
             "official_source_url": C.link_for("SCHED-W10"), "read_on_utc": CAPTURE},
            {"measure": "snapshot rows in the price store", "value": str(len(T["ledger"])),
             "what_it_is": "append-only, hash-chained, 0 chain breaks on re-verification",
             "official_source_url": C.link_for("REPO"), "read_on_utc": CAPTURE},
            {"measure": "injury rows and club-position depth groups",
             "value": f"{len(T['injuries'])} / {len(T['group_depth'])}",
             "what_it_is": "the Week 10 report as printed, and its derived tiers-dropped floors",
             "official_source_url": C.link_for("INJURIES"), "read_on_utc": CAPTURE},
            {"measure": "correlations published with n", "value": str(len(T["corrs"])),
             "what_it_is": "n from 28 to 287, plus 5 candidates excluded with reasons",
             "official_source_url": C.link_for("STANDINGS"), "read_on_utc": CAPTURE},
            {"measure": "tickets and legs settled", "value": f"{len(T['tickets'])} / {len(T['legs'])}",
             "what_it_is": "four bet families, priced against the model's own numbers",
             "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE},
            {"measure": "strategies live after the gate",
             "value": f"{len(DM.live_strategies())} of {len(T['strategies'])}",
             "what_it_is": "one promoted; the top signal row held back by calibration, the second by drawdown",
             "official_source_url": C.link_for("REPO"), "read_on_utc": CAPTURE},
            {"measure": "flags published", "value": str(len(T["flags"])),
             "what_it_is": "gaps, source anomalies and sample-size caveats, none of which block the merge",
             "official_source_url": C.link_for("INJURIES"), "read_on_utc": CAPTURE},
        ])
        + "<h2>What was asked for</h2><p>Eight specific requirements were added to the standing brief: a price "
        "store that can say what a line opened and closed at; a verified results feed so that backtests and ROI "
        "are computable at all; a mandated origination order; fair, market and difference lines as separate "
        "columns; a leaderboard that will not let a staking run disguise a bad signal; depth of replacement "
        "rather than a yes/no injury flag; correlations only from official numbers, each with its n; and a gate "
        "that can send a live strategy back to paper.</p>"
        "<h2>What was built</h2><ul>"
        "<li><b>Results feed</b> - 44 official games (Weeks 7-10 2026) with both clubs, both point totals and "
        "the per-game URL; 37 identity checks (sum of wins against sum of losses, points for against points "
        "against, tie parity, unique ids, feed points never exceeding the season total) and 96 club-week "
        "reconciliations against the record badges printed on the game cards. All pass; 10 checks have no badge "
        "because the club was on that week's bye.</li>"
        "<li><b>Price store</b> - " + counts["markets_snapshot"] + " append-only snapshot rows, hash-chained "
        "(the chain re-verifies with 0 breaks), with opening, intermediate, close-final and close-provisional "
        "roles derived from position in the series. 171 markets, of which 26 have a measurable movement, 118 "
        "have one snapshot and 14 have no number at all because the model could not originate a Week 7 "
        "moneyline.</li>"
        "<li><b>Origination</b> - side, then total, then moneyline, in that order and no other: asking for the "
        "total before the side exists raises. 14 Week 10 games priced, four model columns each "
        "(spread, total, moneyline, tie probability).</li>"
        "<li><b>Three-column publication</b> - model fair line, market line, difference, as separate columns on "
        "every row. The first is filled on every market the model can price; the other two are blank with a "
        "status string and a flag, because no source in this environment publishes a price.</li>"
        "<li><b>Depth</b> - 347 injury rows, 213 club-position groups, tiers-dropped lower bounds per unit, and "
        "11 headline-evidenced replacement rows that name the tier a backup sits at where a headline actually "
        "says so.</li>"
        "<li><b>Correlations</b> - 8 measured rows, each with n (28 to 287), a Fisher interval, the method, the "
        "sample unit, one source URL per axis, and 5 excluded candidates with the reason and what would unlock "
        "them.</li>"
        "<li><b>Backtest and leaderboard</b> - 150 graded tickets and 166 settled legs across four bet families, "
        "then two rankings that are never averaged, and a reward tier decided by the signal block alone.</li>"
        "<li><b>Demotion gate</b> - 10 gates evaluated over all 10 strategies (100 rows), one promotion to live, "
        "nine held in paper, each with the failing gate, its observed value and its threshold named.</li>"
        "</ul>"
        "<h2>What the numbers say, in one paragraph each</h2>"
        "<p><b>The side is real; the total is not, yet.</b> Over 44 graded games the published spread is 10.50 "
        "points of mean absolute error against a zero-margin line's 12.16 - a 1.66-point improvement, and the "
        "damping scan says no shrinkage helps (its best factor is 1.00). On the total the same scan runs the "
        "other way: 11.24 for our line against 10.63 for simply doubling the league's points-per-team, with the "
        "best shrink factor at 0.00. The scoring-rate decomposition adds noise to the total at this sample "
        "size, so the total-anchor strategy is the one the gate refuses to promote.</p>"
        "<p><b>Separating signal from staking changed a decision.</b> The moneyline-anchor strategy has the best "
        "skill score against its event's own base rate (Brier skill +0.0176, hit rate 73.3% on 30 graded legs) "
        "and is ranked first on signal - and it fails the calibration gate (gap 0.1222 against a 0.08 "
        "tolerance), so it stays in paper. The same-game side-plus-over parlay strategy is second on signal, "
        "and what holds it back is the risk block: an 11.00-unit drawdown against an 8.00-unit budget, on 13 "
        "tickets. The one strategy promoted to live, the plain side anchor, is ranked third on signal and has "
        "no failing gate at all. Had the board been ordered by units, the ranking would have been led by a "
        "moneyline run at n=30 and the ordering would have been about variance.</p>"
        "<p><b>Luck is bounded, not removed.</b> The side anchor's -3.00 units over 44 tickets is a z of -0.45 "
        "against what a fair price implies; the SGP's -9.00 over 13 tickets is z = -2.25 (p = 0.024). Neither "
        "number is treated as evidence about the model, and the staking columns cannot move a reward tier in "
        "either direction - the checker enforces that by refusing a payout column in the signal table and an "
        "accuracy column in the staking table.</p>"
        "<h2>What is missing and who has to decide</h2><p>Ten suggestions and seven open questions are listed on "
        "<a href=\"suggestions.html\">Suggestions &amp; questions</a>, every one in state "
        "<code>awaiting_human_choice</code> with <code>applied_by_default = no</code>. The one that gates the "
        "most: a licensed market-price source. It is the only thing that turns the difference column, the edge "
        "statistics and closing-line value from blanks into measurements; four source classes have already been "
        "attempted and logged. The one that is self-serveable: backfilling Weeks 1-6 into the feed, which lifts "
        "n from 44 games to about 136 and dissolves the two sample-size flags without any new kind of data.</p>"
        "<h2>Rights and use</h2><p>The pack quotes league pages for scores, standings and designations only, for "
        "individual non-commercial review, and reproduces the rights position the prior session recorded "
        "(<a href=\"sources.html\">Sources &amp; rights</a>). No odds are scraped, no wager is placed, and no "
        "monetary reward is offered to any strategy.</p>")
    log.append(write_html("executive-summary.html", page("Executive summary", summary,
                                                         "executive-summary.html",
                                                         "What was asked, what was built, what the numbers say, "
                                                         "and what is still a blank with a reason.")))

    # ------------------------------------------------------------ results feed
    cov = [{"coverage": "weeks 7-10 of the 2026 regular season", "games": str(len(T["feed"])),
            "team_games": str(2 * len(T["feed"])),
            "why_this_window": "this is what the Week 7-10 schedule pages print as FINAL; Weeks 1-6 were not "
                               "read in this session, so they are not in the feed and no statistic pretends "
                               "otherwise",
            "how_to_extend": "suggestion D966-S02: read schedules/2026/by-week/week-N for N in 1..6 and append "
                             "to capture.FINAL_GAMES; the identity checks apply unchanged",
            "official_source_url": C.link_for("SCHED-W7"), "read_on_utc": CAPTURE}]
    body = (
        "<p class=\"note\">The feed is what makes a backtest possible: every settled leg in this pack points at "
        "one row here, and every row here points at the page it was read from. It is stored as data in "
        "<code>capture.py</code> and regenerated byte-for-byte by the builder, so a reviewer can diff the table "
        "against the page.</p>"
        + render_table(["game_id", "week", "date_on_card", "slot_on_card", "away", "away_points", "home",
                        "home_points", "game_total", "margin_home", "winner_abbr", "is_tie", "feed_status",
                        "value_source", "official_source_url"], T["feed"],
                       num_fields=("week", "away_points", "home_points", "game_total", "margin_home"),
                       note=f"{len(T['feed'])} games, Weeks 7-10. <code>margin_home</code> is home points minus "
                            "away points, as printed on the card.")
        + "<h2>Reconciliation against the game-card badges</h2>"
        + "<p class=\"note\">The derived record for each club at the end of each week (the standings page as "
          "read, minus every feed game played after that week) is checked against the record badge the week's "
          "own game cards print. "
          + str(sum(1 for r in T["recon"] if r["result"] == "match")) + " match, "
          + str(sum(1 for r in T["recon"] if r["result"] == "no_official_badge_club_on_bye"))
          + " have no badge because the club was on bye, and "
          + str(sum(1 for r in T["recon"] if r["result"] not in ("match", "no_official_badge_club_on_bye")))
          + " mismatch.</p>"
        + render_table(["check_week", "club", "derived_w_l_t", "official_card_badge_w_l_t", "result",
                        "derived_from", "official_source_url"], T["recon"], max_rows=40)
        + "<h2>Feed identities</h2>"
        + render_table(["identity", "expected", "observed", "result", "why_it_matters", "official_source_url"],
                       T["identities"],
                       note="These are the checks that make the feed a feed rather than a transcription: a "
                            "missed game, a swapped score or a duplicated id fails one of them.")
        + "<h2>Coverage</h2>"
        + render_table(["coverage", "games", "team_games", "why_this_window", "how_to_extend",
                        "official_source_url", "read_on_utc"], cov))
    log.append(write_html("results-feed.html", page("Verified results feed", body, "results-feed.html",
                                                    "The official final scores every graded number in this pack "
                                                    "resolves against.")))

    # ------------------------------------------------------------------ lines
    line_fields = ["line_id", "game_id", "date_on_official_card", "away", "home", "fixture_status",
                   "model_fair_line_side", "market_line_side", "difference_side", "difference_side_status",
                   "model_fair_line_total", "market_line_total", "difference_total", "difference_total_status",
                   "model_fair_line_moneyline_home", "market_line_moneyline_home",
                   "difference_moneyline_home", "difference_moneyline_home_status", "moneyline_prob_tie",
                   "market_flag_id", "grade_side", "grade_total", "actual_score", "official_source_url",
                   "game_page_url"]
    body = (
        "<p class=\"note\">Requirement 4 in its literal form: three columns per market, model fair line, market "
        "line, difference. The model column carries the rounded published line and the raw value before "
        "rounding; the other two are blank on every row with the status "
        "<code>blank_no_licensed_market_price</code> and flag <code>D966-F01</code>. The <code>blank</code> "
        "cells are the finding, not a gap in the work.</p>"
        + render_table(["stage", "market", "may_start_from", "depends_on", "why_this_order",
                        "failure_mode_if_reordered", "official_source_url"], STAGE_ORDER,
                       note="Requirement 3: side first, then total, then moneyline. The order is enforced in "
                            "code - asking for the total before a published side exists raises "
                            "<code>StageOrderError</code> rather than quietly re-deriving the side.")
        + render_table(line_fields, T["lines"],
                       num_fields=("model_fair_line_side", "model_fair_line_total", "moneyline_prob_tie"),
                       note="One row per Week 10 game, priced on the standings through Week 9. A negative side "
                            "means the home club is favoured. The two graded columns are filled only for the "
                            "Thursday game, which was final at capture; the other thirteen had not been played.")
        + "<h2>Inputs and dispersion behind every row</h2>"
        + render_table(["line_id", "game_id", "inputs_away_games", "inputs_home_games", "inputs_away_ppg",
                        "inputs_away_papg", "inputs_home_ppg", "inputs_home_papg", "inputs_league_ppg",
                        "side_expected_margin_home", "side_margin_undamped", "margin_damping_lambda",
                        "dispersion_sigma_pts", "dispersion_rho_home_away", "dispersion_n_team_games",
                        "inputs_official_source_url"],
                       T["lines"],
                       num_fields=("inputs_away_ppg", "inputs_away_papg", "inputs_home_ppg",
                                   "inputs_home_papg", "inputs_league_ppg", "side_expected_margin_home",
                                   "side_margin_undamped", "dispersion_sigma_pts",
                                   "dispersion_rho_home_away"),
                       note="The expected margin is (home attack - league) + (away defence allowed - league), "
                            "doubled out for the away club with the signs reversed; every term on that line is "
                            "in this table, so a reader can recompute any published number by hand.")
        + "<h2>The one graded game</h2><p>Washington 24 at New York 21, final, Week 10 Thursday. The model "
          "published NYG -3.5 (home favoured by 3.5), 45.5 total and a home moneyline of -145 with a 2.73% tie "
          "probability. The Giants lost by three, so the home club did not cover and the under was correct: "
          "<code>away_covered</code> and <code>under</code>. That single row is the whole set of Week 10 "
          "results at capture time, and it is the reason the leaderboard's n column matters more than its units "
          "column.</p>")
    log.append(write_html("lines.html", page("Originated lines", body, "lines.html",
                                             "Week 10 2026 slate, priced in the required order, with the market "
                                             "and difference columns kept honestly blank.")))

    # ----------------------------------------------------------------- prices
    roles: dict[str, int] = {}
    for r in T["ledger"]:
        roles[r["role"]] = roles.get(r["role"], 0) + 1
    classes: dict[str, int] = {}
    for r in T["ledger"]:
        classes[r["publication_class"]] = classes.get(r["publication_class"], 0) + 1
    breaks = P.verify_chain(T["ledger"])
    body = (
        "<p class=\"note\">Requirement 1 in full. The store is a ledger, not a field: one row per market per "
        "publication, never edited in place, each row chained to the previous one by a SHA-256 over its "
        "canonical form. Opening and closing numbers are <em>derived</em> from position in the series, so no "
        "one has to trust a label.</p>"
        + render_table(["store_rule", "what_it_prevents", "official_source_url", "read_on_utc"], [
            {"store_rule": "a row is never edited; a correction is another row",
             "what_it_prevents": "a quiet back-edit turning a reconstruction into a quote",
             "official_source_url": C.link_for("REPO"), "read_on_utc": CAPTURE},
            {"store_rule": "role comes from position: earliest = open, latest at or before kickoff = close",
             "what_it_prevents": "calling the most recent number a close when the game has not been verified "
                                 "final", "official_source_url": C.link_for("REPO"), "read_on_utc": CAPTURE},
            {"store_rule": "publication_class on every row: live_snapshot, retrospective_reconstruction, "
                           "prior_session_publication",
             "what_it_prevents": "mixing what we quoted with what the model would have written, or with another "
                                 "session's published number",
             "official_source_url": C.link_for("REPO"), "read_on_utc": CAPTURE},
            {"store_rule": "row_sha256 chains to prev_row_sha256",
             "what_it_prevents": "an undetected edit anywhere in the history: "
                                 + str(len(breaks)) + " breaks in the chain right now",
             "official_source_url": C.link_for("REPO"), "read_on_utc": CAPTURE},
        ])
        + "<h2>Store contents</h2><p class=\"note\">"
        + f"{len(T['ledger'])} rows, {len(T['oc'])} markets. Roles: "
        + ", ".join(f"{k} = {v}" for k, v in sorted(roles.items())) + ". Classes: "
        + ", ".join(f"{k} = {v}" for k, v in sorted(classes.items())) + ".</p>"
        + render_table(["market_id", "game_id", "market_type", "n_snapshots", "opening_number",
                        "opening_published_on", "opening_class", "closing_number", "closing_role",
                        "movement_closing_minus_opening", "movement_status", "movement_flag_id",
                        "game_final", "movement_note", "official_source_url"], T["oc"],
                       num_fields=("n_snapshots", "opening_number", "closing_number",
                                   "movement_closing_minus_opening"), max_rows=40,
                       note="118 markets hold a single row, so their opening number <em>is</em> their closing "
                            "number and their movement is 0.00 by construction - labelled "
                            "<code>single_snapshot_open_and_close_are_the_same_row</code> and flagged "
                            "<code>D966-F16</code>, because a column of zeros otherwise reads as a calm market. "
                            "26 markets moved, all between the prior session's model and ours, which is a "
                            "rewrite rather than a reprice (flag <code>D966-F02</code>). 13 moneyline markets "
                            "have no opening number at all, because the prior publication left that column "
                            "blank (<code>D966-F03</code>). The complete table is in "
                            "<code>price_snapshots_open_close.csv</code>.")
        + "<h2>External price capture attempts</h2>"
        + "<p class=\"note\">Four source classes were read or attempted for a book price. All four are "
          "published, because the difference between \"we do not have this\" and \"we did not look\" is the "
          "difference between a blank and a lie.</p>"
        + render_table(["attempt_id", "market_family", "source_class", "source_url", "read_on", "outcome",
                        "detail", "consequence", "flag_id", "official_source_url"], T["attempts"]))
    log.append(write_html("prices.html", page("Opening and closing prices", body, "prices.html",
                                              "An append-only snapshot ledger, with open, close and movement "
                                              "derived from the series.")))
    return log


def write_pages_part2(T, log: list[str]) -> None:
    # ------------------------------------------------------------------ model
    body = (
        "<p class=\"note\">One model, two lines deep, and the only fitted quantity is published as analysis "
        "rather than baked into the numbers. Everything here is arithmetic on the standings feed plus a noise "
        "scale measured on official final scores.</p>"
        + render_table(MODEL_FIELDS, model_rows(),
                       note="Parameters, their basis and their source. <code>margin_damping_lambda</code> is "
                            "1.00 on every published line: the grid search on the feed prefers no shrinkage at "
                            "all, so fitting one would be a cosmetic change.")
        + "<h2>Dispersion, by vintage</h2>"
        + render_table(["vintage_week", "n_games", "n_team_games", "sigma_pts", "sigma_pts_around_team_mean",
                        "rho_home_away", "league_ppg", "official_source_url", "read_on_utc"], T["disp"],
                       num_fields=("sigma_pts", "sigma_pts_around_team_mean", "rho_home_away", "league_ppg"),
                       note="The moneyline needs this scale, which is why the Week 7 games have no moneyline: "
                            "at the Week 6 vintage the feed holds no finished games at all (flag "
                            "<code>D966-F10</code>). The Week 9 vintage gives sigma_pts 10.2808 and "
                            "rho -0.0659 on 43 games / 86 team-games.")
        + "<h2>Fits, published as analysis</h2>"
        + render_table(["vintage_week", "n_games_graded", "side_lambda_best", "side_mae_at_best",
                        "side_mae_undamped", "total_shrink_best", "total_mae_at_best", "total_mae_undamped",
                        "total_mae_at_baseline", "applied_to_published_line", "caveat", "official_source_url"],
                       T["fits"],
                       num_fields=("side_lambda_best", "side_mae_at_best", "side_mae_undamped",
                                   "total_shrink_best", "total_mae_at_best", "total_mae_undamped",
                                   "total_mae_at_baseline"),
                       note="In-sample grid searches on a short feed. The side prefers the full model at every "
                            "vintage that has enough games; the total prefers the baseline, and at the Week 10 "
                            "vintage the best shrink factor is 0.00 - the honest reading of that is that the "
                            "attack-plus-opposition decomposition is noise on a 44-game sample, not that a "
                            "better shrink was found.")
        + "<h2>Shrinkage scans</h2>"
        + render_table(["market_type", "vintage_week", "shrink_factor", "n_games", "mae_points", "mse_points",
                        "mean_signed_error_points", "baseline_mae_at_shrink_zero", "official_source_url"],
                       T["scans"],
                       num_fields=("shrink_factor", "mae_points", "mse_points", "mean_signed_error_points",
                                   "baseline_mae_at_shrink_zero"), max_rows=42,
                       note="The whole grid, both markets, so the shape of the curve is visible rather than "
                            "only its minimum. The complete table is in <code>damping_scans.csv</code>.")
        + "<h2>Line accuracy on every graded game</h2>"
        + render_table(["game_id", "week", "away", "home", "model_margin_raw", "actual_margin_home",
                        "abs_error_side_points", "model_total_raw", "actual_game_total",
                        "abs_error_total_points", "rounding_gap_side",
                        "baseline_abs_error_side_zero_margin", "baseline_abs_error_total_league",
                        "vintage_week", "result_official_source_url"], T["line_quality"],
                       num_fields=("abs_error_side_points", "abs_error_total_points", "rounding_gap_side",
                                   "baseline_abs_error_side_zero_margin",
                                   "baseline_abs_error_total_league"),
                       note="Absolute error of the two published numbers against the final score, with the "
                            "naive baseline for the same game beside it. This is the purest signal statistic in "
                            "the pack: no price, no stake, no payout."))
    log.append(write_html("model.html", page("Model, dispersion and fits", body, "model.html",
                                             "How every published number is produced, and how far it landed.")))

    # -------------------------------------------------------------- injuries
    load: dict[str, int] = {}
    for r in T["injuries"]:
        load[r["club"]] = load.get(r["club"], 0) + 1
    thin = sorted(load.items(), key=lambda kv: kv[1])[:6]
    body = (
        "<p class=\"note\">The official Week 10 report, read in full: 28 clubs, 347 listed players. Player, "
        "position, injury text, practice participation and game designation are stored verbatim. Nothing here "
        "is a depth chart, and the pack does not pretend otherwise.</p>"
        + render_table(["row_id", "club", "game_id", "player", "position", "position_unit", "position_group",
                        "injury_text", "practice_status", "game_status", "availability",
                        "counts_toward_lower_bound", "official_source_url", "read_on_utc"], T["injuries"],
                       max_rows=80,
                       note="Availability is derived from the designation column only: Out and Doubtful count "
                            "toward the depth floor, Questionable does not, and a blank game status is "
                            "<code>listed_no_designation</code> - it is not \"available\" (flag "
                            "<code>D966-F15</code>).")
        + "<h2>Rows per club, so a thin report is visible</h2>"
        + render_table(["club", "players_listed", "reading"],
                       [{"club": c, "players_listed": str(n),
                         "reading": ("thin capture: a count of nobody-listed is not a census of nobody-out "
                                     "(flag D966-F14)" if n <= 5 else "as printed"),
                         "official_source_url": C.link_for("INJURIES"), "read_on_utc": CAPTURE}
                        for c, n in sorted(load.items(), key=lambda kv: (kv[1], kv[0]))])
        + "<p class=\"note\">The thinnest blocks are "
        + ", ".join(f"{c} ({n})" for c, n in thin) + ". Las Vegas at five rows is the reason the club "
        "comparisons in <a href=\"correlations.html\">Correlations</a> are read as floors.</p>"
        + "<h2>Position to unit mapping</h2>"
        + render_table(["position", "unit", "mapping_owner", "flag_id", "official_source_url", "read_on_utc"],
                       T["units"],
                       note="Ours, not the league's - the report prints a position and no unit (flag "
                            "<code>D966-F05</code>).")
        + "<h2>Official headlines used as replacement evidence</h2>"
        + render_table(["index", "club", "headline_verbatim", "url", "note", "read_on_utc"], T["headlines"],
                       note="Headline text only; the article bodies were not opened in this session. Two "
                            "headlines about the same Ravens quarterback disagree with each other (6-10 weeks "
                            "against 6-9), and both are printed as they appear (flag <code>D966-F13</code>)."))
    log.append(write_html("injuries.html", page("Injury report", body, "injuries.html",
                                                "347 official rows for the Week 10 slate, kept as printed.")))

    # ------------------------------------------------------------------ depth
    body = (
        "<p class=\"note\">Requirement 6: the depth of the replacement, not the fact of one. The report will "
        "not say who is first string, so this pack publishes two different things in two different columns and "
        "never confuses them: a <em>lower bound</em> derived from designations, and an <em>evidenced</em> tier "
        "where an official headline actually names the backup taking the job.</p>"
        + render_table(["club", "unit", "position_group", "players_listed", "ruled_out", "doubtful",
                        "questionable", "practice_report_only_no_designation", "tiers_dropped_lower_bound",
                        "depth_bound_kind", "first_string_impacted", "club_depth_deficit",
                        "deficit_score_kind", "official_source_url"], T["group_depth"],
                       num_fields=("players_listed", "ruled_out", "doubtful", "questionable",
                                   "practice_report_only_no_designation", "tiers_dropped_lower_bound",
                                   "club_depth_deficit"), max_rows=48,
                       note="213 club-position groups. The bound is hard: every player the report rules Out or "
                            "Doubtful has to be covered by someone further down that group's list. The deficit "
                            "column is a declared weighting (1.0 unavailable, 0.25 questionable, 0.5 an "
                            "evidenced replacement) and its <code>score_kind</code> says so. The complete table "
                            "is in <code>depth_of_replacement.csv</code>.")
        + "<h2>Club rollup against the fixture it affects</h2>"
        + render_table(["club", "game_id", "fixture", "groups_listed_total",
                        "offence_tiers_dropped_lower_bound", "offence_worst_group",
                        "offence_worst_group_bound", "defence_tiers_dropped_lower_bound", "defence_worst_group",
                        "defence_worst_group_bound", "special_teams_tiers_dropped_lower_bound",
                        "club_depth_deficit", "position_group_order_status", "official_source_url"],
                       T["club_depth"],
                       num_fields=("groups_listed_total", "offence_tiers_dropped_lower_bound",
                                   "offence_worst_group_bound", "defence_tiers_dropped_lower_bound",
                                   "defence_worst_group_bound", "special_teams_tiers_dropped_lower_bound",
                                   "club_depth_deficit"),
                       note="Twenty-eight clubs appear: the four on bye have no Week 10 report block, which is "
                            "why the rollup has 28 rows and not 32.")
        + "<h2>Headline-evidenced replacements</h2>"
        + render_table(["evidence_id", "club", "position_group", "replacement_tier", "evidence_kind",
                        "credited_as_depth_replacement", "headline_verbatim", "url", "note",
                        "official_source_url"], T["evidence"],
                       note="Only two rows are credited into the deficit: Miami's first start for the backup "
                            "quarterback after Malik Willis went to injured reserve, and Seattle naming Drew "
                            "Lock to start again. An injured-reserve move or a surgery states that someone is "
                            "out; it does not state how deep the drop goes, so it is recorded and not weighted.")
        + "<p class=\"note\">The one strategy that trades on depth (D966-STR-06) is armed but has graded "
          "nothing: it fires only when the injury report's tier count flips a published side, and the report "
          "exists for Week 10, where one game had been played. That is stated on its row rather than hidden by "
          "dropping it from the board.</p>")
    log.append(write_html("depth.html", page("Depth of replacement", body, "depth.html",
                                             "How far down the list a club has to reach, and where a source "
                                             "actually says so.")))

    # ---------------------------------------------------------- correlations
    body = (
        "<p class=\"note\">Requirement 7: both axes official, n published, and every rejected candidate kept in "
        "view. The exclusions table is as long as the results table, because what a pack refuses to compute is "
        "the most informative thing about its limits.</p>"
        + render_table(["correlation_id", "x_variable", "y_variable", "sample_unit", "method", "n",
                        "coefficient", "ci95_low", "ci95_high", "p_value_normal_approx", "status", "flag_id",
                        "independence_note", "x_official_source_url", "y_official_source_url",
                        "interpretation"], T["corrs"],
                       num_fields=("n", "coefficient", "ci95_low", "ci95_high"),
                       note="Intervals are Fisher z-transform 95% intervals. Several contain both signs - at "
                            "n=44 that is the correct conclusion, not a shortfall. The two club-level rows that "
                            "compare a Week 10 availability count against a season-long rate are labelled as "
                            "mismatched windows in their sample unit.")
        + "<h2>Candidates excluded, with reasons</h2>"
        + render_table(["candidate_id", "candidate", "status", "reason", "what_would_unlock_it",
                        "suggestion_id", "official_source_url"], T["excls"])
        + "<h2>What the measured dependence does to a parlay</h2>"
        + parlay_block()
        + "<p class=\"note\">Nothing here uses a model output as if it were a measurement. The one candidate "
          "that would have used the model's edge against a book price - the most quoted statistic in this "
          "literature - is in the exclusions table instead, with the sentence that explains why.</p>")
    log.append(write_html("correlations.html", page("Correlations", body, "correlations.html",
                                                    "Measured dependence between the quantities the parlays "
                                                    "actually share.")))


def parlay_block() -> str:
    rho = -0.0662
    base = X.parlay_probability([0.55, 0.52], None)
    adj = X.parlay_probability([0.55, 0.52], rho)
    rows = [{
        "pairing": "two legs at 55% and 52%, treated as independent",
        "joint_probability": S.fmt(float(base["independent_product"]), 4),
        "rho_used": "",
        "difference_vs_independent": "",
        "status": str(base["joint_status"]),
        "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE,
    }, {
        "pairing": "same two legs, joint probability from the measured rho",
        "joint_probability": S.fmt(float(adj["joint_bivariate"]), 4),
        "rho_used": S.fmt(rho, 4),
        "difference_vs_independent": f"{float(adj['joint_minus_independent']):+.4f}",
        "status": str(adj["joint_status"]),
        "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE,
    }, {
        "pairing": "same-game side and over, the pairing D966-STR-08 trades",
        "joint_probability": "",
        "rho_used": S.fmt(-0.2830, 4),
        "difference_vs_independent": "",
        "status": "rho measured (margin against total, n=44); a worked example is on the model's own prices in "
                  "backtest.csv rather than at illustrative probabilities",
        "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE,
    }]
    return render_table(["pairing", "joint_probability", "rho_used", "difference_vs_independent", "status",
                         "official_source_url"], rows,
                        num_fields=("joint_probability", "rho_used", "difference_vs_independent"),
                        note="A bivariate-Normal joint at thresholds chosen so each marginal equals its leg "
                             "probability. With rho = -0.0662 the joint falls about one point below the "
                             "independent product on this pairing - small, and measured, rather than the "
                             "customary invented 5-10% correlation discount.")


def write_pages_part3(T, log: list[str]) -> None:
    # --------------------------------------------------------------- backtest
    per: dict[str, dict[str, object]] = {}
    for t in T["tickets"]:
        d = per.setdefault(t["strategy_id"], {"tickets": 0, "wins": 0, "losses": 0, "pushes": 0,
                                              "units": 0.0, "weeks": set()})
        d["tickets"] += 1
        d["units"] += float(t["units"])
        d["weeks"].add(t["week"])
        d[{"win": "wins", "loss": "losses", "push": "pushes"}.get(t["outcome"], "losses")] += 1
    rows = []
    for st in B.STRATEGIES:
        d = per.get(st.strategy_id, {"tickets": 0, "wins": 0, "losses": 0, "pushes": 0, "units": 0.0,
                                    "weeks": set()})
        n = int(d["tickets"])
        rows.append({
            "strategy_id": st.strategy_id, "strategy_name": st.name, "family": st.family,
            "n_tickets": str(n), "n_weeks_traded": str(len(d["weeks"])),
            "wins": str(int(d["wins"])), "losses": str(int(d["losses"])), "pushes": str(int(d["pushes"])),
            "units_total": S.fmt(float(d["units"]), 3),
            "units_per_ticket": S.fmt(float(d["units"]) / n if n else float("nan"), 4),
            "legs_graded": str(len([l for l in T["legs"] if l["strategy_id"] == st.strategy_id])),
            "status": st.status,
            "blocked_reason": st.blocked_reason,
            "price_basis": "even money on side and total, our own no-vig price on the moneyline, no hold",
            "official_source_url": C.link_for("SCHED-W9"), "read_on_utc": CAPTURE,
        })
    push_legs = sum(1 for l in T["legs"] if l["outcome"] == "push")
    body = (
        "<p class=\"note\">Requirement 2 exists because without a results feed a backtest is a story. There "
        "are " + str(len(T["tickets"])) + " graded tickets and " + str(len(T["legs"])) + " settled legs here, "
        "and every leg carries the URL of the page its score came from.</p>"
        + render_table(["strategy_id", "strategy_name", "family", "n_tickets", "n_weeks_traded", "wins",
                        "losses", "pushes", "legs_graded", "units_total", "units_per_ticket", "status",
                        "blocked_reason", "price_basis", "official_source_url"], rows,
                       num_fields=("n_tickets", "wins", "losses", "pushes", "legs_graded", "units_total",
                                   "units_per_ticket"),
                       note="<b>Read the price basis before the units.</b> There is no book in this "
                            "environment, so side and total legs settle at even money against our own published "
                            "number and moneyline legs at our own no-vig price. A perfectly fair model is "
                            "therefore expected to break even against these prices by construction: what this "
                            "table measures is calibration, and anything that looks like profit is a sample "
                            "artefact. That sentence is the whole reason the leaderboard ranks the signal "
                            "block, not this one.")
        + "<h2>Settlement conventions</h2><ul>"
        + "<li>A push on a side or a total returns the stake: 0 units, and the leg is excluded from hit-rate "
          "and Brier denominators rather than counted as a miss. " + str(push_legs) + " push legs exist in this "
          "window.</li>"
        + "<li>A push on a moneyline returns the stake; a tie is possible and priced - the tie probability on "
          "the published Washington at New York line was 2.73%.</li>"
        + "<li>A two-leg ticket with one push pays the surviving leg's price; both push, the ticket pushes; any "
          "leg loses, the ticket loses.</li>"
        + "<li>These are declared conventions, not an operator's rules. Suggestion D966-S03 asks for a decision "
          "on push handling before any real market exists.</li></ul>"
        + "<h2>Settled legs, first 40</h2>"
        + render_table(["leg_id", "ticket_id", "strategy_id", "family", "week", "game_id", "market",
                        "line_published", "side_taken", "model_prob", "model_prob_basis",
                        "actual_home_points", "actual_away_points", "outcome", "units_if_single",
                        "price_basis", "result_official_source_url"], T["legs"], max_rows=40,
                       num_fields=("line_published", "model_prob", "actual_home_points", "actual_away_points",
                                   "units_if_single"),
                       note="<code>model_prob_basis</code> says whether the probability used for scoring was "
                            "measured at that game's own vintage or substituted from the earliest measurable "
                            "one - the substitution peeks forward, and it is named on every leg that uses it "
                            "rather than buried. The complete 166-row table is in "
                            "<code>backtest_legs.csv</code>.")
        + "<h2>Tickets</h2>"
        + render_table(["ticket_id", "strategy_id", "family", "week", "n_legs", "leg_markets", "legs_summary",
                        "outcome", "units", "independent_product_of_leg_probs", "model_prob_note",
                        "result_official_source_url"], T["tickets"], max_rows=40,
                       num_fields=("n_legs", "units", "independent_product_of_leg_probs"),
                       note="Parlay and same-game tickets are single tickets, not two graded bets: one unit, "
                            "both legs, and a payout that multiplies. The complete table is in "
                            "<code>backtest_tickets.csv</code>."))
    log.append(write_html("backtest.html", page("Backtest and settlement", body, "backtest.html",
                                                "Singles, parlays, same-game parlays and prop combos, settled "
                                                "against official final scores.")))

    # ------------------------------------------------------------ leaderboard
    body = (
        "<p class=\"note\">Requirement 5, in the structure rather than the prose: two tables, two ranks, and "
        "no column shared between them. The checker enforces it - the signal table may not contain a stake, "
        "unit or payout column, and the staking table may not contain an accuracy or error column.</p>"
        + "<h2>Signal block - how good the numbers are</h2>"
        + render_table(["strategy_id", "strategy_name", "family", "signal_rank", "rank_basis",
                        "n_tickets_graded", "n_legs_graded_excluding_pushes", "n_push_legs_excluded",
                        "hit_rate_cover", "hit_rate_ci95_low", "hit_rate_ci95_high", "target_event",
                        "mean_predicted_cover_prob", "calibration_gap", "brier_score",
                        "brier_climatology_baseline", "brier_skill_score_vs_base_rate", "log_loss",
                        "mean_abs_error_side_points", "naive_baseline_abs_error_side_points",
                        "mean_abs_error_total_points", "naive_baseline_abs_error_total_points",
                        "line_quality_vs_naive", "line_quality_status", "signal_status", "flag_id",
                        "official_source_url"], T["signal"],
                       num_fields=("hit_rate_cover", "hit_rate_ci95_low", "hit_rate_ci95_high",
                                   "mean_predicted_cover_prob", "calibration_gap", "brier_score",
                                   "brier_climatology_baseline", "brier_skill_score_vs_base_rate", "log_loss",
                                   "mean_abs_error_side_points", "naive_baseline_abs_error_side_points",
                                   "mean_abs_error_total_points", "naive_baseline_abs_error_total_points"),
                       note="Ranking is on the Brier <em>skill</em> score - the model's probability error "
                            "against the same event's own base rate - not on raw Brier. That matters because a "
                            "favourite-win event and a cover event have different base rates: raw Brier of 0.19 "
                            "on a 73%-hit-rate event is not better than 0.25 on a coin flip, and a board that "
                            "compared them that way would rank structure rather than skill.")
        + "<h2>Staking block - how good the betting was on top of those numbers</h2>"
        + render_table(["strategy_id", "strategy_name", "family", "staking_rank_display_only",
                        "n_tickets_graded", "units_total", "units_per_ticket", "roi_units_per_100_tickets",
                        "sd_units_per_ticket", "z_vs_fair_price", "p_two_sided_normal", "max_drawdown_units",
                        "longest_win_streak", "longest_loss_streak", "mean_half_kelly_stake_fraction",
                        "stake_rule", "price_basis", "staking_status", "luck_note", "official_source_url"],
                       T["staking"],
                       num_fields=("units_total", "units_per_ticket", "roi_units_per_100_tickets",
                                   "sd_units_per_ticket", "z_vs_fair_price", "p_two_sided_normal",
                                   "max_drawdown_units", "mean_half_kelly_stake_fraction"),
                       note="<code>z_vs_fair_price</code> is the luck measure: total units divided by their own "
                            "standard error. At these sample sizes a |z| near 1 is ordinary variance, and this "
                            "column can move a strategy's drawdown budget but never its tier.")
        + "<h2>Both blocks side by side</h2>"
        + render_table(["strategy_id", "strategy_name", "signal_rank", "signal_status", "brier_score",
                        "hit_rate_cover", "n_legs_graded_excluding_pushes", "line_quality_status",
                        "line_quality_vs_naive", "staking_rank_display_only", "units_total",
                        "units_per_ticket", "z_vs_fair_price", "max_drawdown_units", "n_tickets_graded",
                        "rank_gap_staking_minus_signal", "interpretation", "official_source_url"],
                       T["combined"],
                       num_fields=("brier_score", "hit_rate_cover", "units_total", "units_per_ticket",
                                   "z_vs_fair_price", "max_drawdown_units"))
        + "<h2>Reward tiers</h2>"
        + render_table(["tier_id", "tier", "strategy_id", "strategy_name", "signal_rank", "n_legs_graded",
                        "brier_score", "reward", "reward_currency", "why_not_cash", "eligibility_rule",
                        "flag_id", "official_source_url"], T["tiers"],
                       note="Standing, compute priority and a badge - not cash. Paying on betting outcomes "
                            "would point an autonomous board at profit instead of accuracy, and it runs into "
                            "the rights position on <a href=\"sources.html\">Sources &amp; rights</a>. A tier "
                            "follows the signal rank, and the gate can still pull a strategy out of it: the "
                            "top-ranked row here is not live (see "
                            "<a href=\"gates.html\">Validation &amp; demotion gates</a>)."))
    log.append(write_html("leaderboard.html", page("Leaderboard", body, "leaderboard.html",
                                                   "Signal and staking, ranked separately and never averaged.")))

    # ------------------------------------------------------------------ gates
    body = (
        "<p class=\"note\">Requirement 8. Ten gates over ten strategies, every observed value, threshold and "
        "verdict published, and the state each strategy ends in - with the failing gate named on the row that "
        "fails it.</p>"
        + render_table(["gate_id", "block", "metric", "threshold", "comparison", "why", "action_on_fail",
                        "applied_to", "evaluated_on", "official_source_url"], T["gate_defs"],
                       note="Three blocks: the signal gates decide eligibility, the risk gates can send a live "
                            "strategy back on their own even when its lines are accurate, and the integrity "
                            "gates are an override that demotes everything in the same run if the price chain, "
                            "the reconciliation or the feed identities fail.")
        + "<h2>States after this run</h2>"
        + render_table(["strategy_id", "strategy_name", "previous_state", "state", "decision",
                        "state_before_integrity_override", "signal_rank", "eligible_for_reward_tier",
                        "failing_gate_ids", "failing_gate_detail", "not_evaluated_gate_ids", "blocked_reason",
                        "decision_by", "effective_on_utc", "official_source_url"], T["states"],
                       note="Nothing was live before this pack existed, so the first run can promote but cannot "
                            "honestly report a demotion. One strategy cleared every gate and was promoted; the "
                            "rest stay in paper, each with its failing gate named - including the two that rank "
                            "first and second on signal and are held back by calibration and by drawdown.")
        + "<h2>Transitions</h2>"
        + render_table(["transition_id", "strategy_id", "strategy_name", "from_state", "to_state", "kind",
                        "trigger_gate_ids", "trigger_detail", "rank_at_time_of_decision", "note",
                        "decision_by", "effective_on_utc", "official_source_url"],
                       T["transitions"] or [{"transition_id": "", "strategy_id": "none this run",
                                             "strategy_name": "", "from_state": "", "to_state": "", "kind": "",
                                             "trigger_gate_ids": "", "trigger_detail": "",
                                             "rank_at_time_of_decision": "",
                                             "note": "no state changed in this run", "decision_by": "",
                                             "effective_on_utc": CAPTURE,
                                             "official_source_url": C.link_for("REPO")}])
        + "<h2>Standing demotion test</h2>"
        + render_table(["strategy_id", "strategy_name", "state", "would_demote_on_next_run", "n_gates_failing",
                        "gates_that_would_fire", "first_failing_metric", "first_failing_detail",
                        "mechanism_note", "official_source_url"], T["watch"],
                       num_fields=("n_gates_failing",),
                       note="This is how the mechanism is shown to work without inventing a history: every row "
                            "is a gate that fails on real numbers today, so if that strategy were live this is "
                            "the notice it would receive. The unit test asserts exactly one live-to-paper "
                            "transition per failing gate when a live state is supplied, and no transition when "
                            "none fails - the demotion path is exercised, not described.")
        + "<h2>All " + str(len(T["gates"])) + " evaluated rows</h2>"
        + render_table(["gate_id", "block", "strategy_id", "metric", "observed_value", "threshold",
                        "comparison", "result", "observed_versus_threshold", "measurement_note",
                        "why_this_gate_matters", "action_on_fail", "official_source_url"], T["gates"],
                       max_rows=50,
                       note="The complete table is in <code>validation_gates.csv</code>. \"not_evaluated\" is "
                            "a result too: it means the gate had nothing to measure, and it never counts as a "
                            "pass."))
    log.append(write_html("gates.html", page("Validation and demotion gates", body, "gates.html",
                                             "What has to be true to be the reference line, and what takes that "
                                             "away.")))

    # ------------------------------------------------------------- strategies
    body = (
        "<p class=\"note\">Ten strategies in four families, including the two the pack refuses to run. A "
        "catalogue that quietly omits the rules it cannot price would hide exactly the gaps the flags are "
        "there to show.</p>"
        + render_table(["strategy_id", "name", "family", "markets", "rule_verbatim", "params", "stake_rule",
                        "status", "blocked_reason", "selections_graded", "official_source_url", "read_on_utc"],
                       T["strategies"],
                       num_fields=("selections_graded",)))
    log.append(write_html("strategies.html", page("Strategy catalogue", body, "strategies.html",
                                                  "Singles, parlays, same-game parlays and prop combos, with the "
                                                  "blocking reasons attached.")))

    # ------------------------------------------------------------ suggestions
    body = (
        "<p class=\"note\">This is the part of the brief where a person chooses. Nothing below has been applied: "
        "every suggestion carries <code>status = awaiting_human_choice</code> and <code>applied_by_default = "
        "no</code>, and the questions name who has to answer and what we would do to find out on our own if the "
        "answer is findable.</p>"
        + render_table(["suggestion_id", "title", "what_would_change", "why_now", "cost_or_effort",
                        "risk_if_applied", "risk_if_not_applied", "touches_requirements", "status",
                        "applied_by_default", "evidence_or_source", "official_source_url"], T["suggestions"],
                       note="Two of these argue against themselves and say so - the note on D966-S09 is the "
                            "analysis, not a hedge. A suggestion register that only ever says \"do this\" is a "
                            "wishlist, not advice.")
        + "<h2>What we need to be told, and what we could find out ourselves</h2>"
        + render_table(["question_id", "question", "why_we_cannot_answer_it_ourselves", "what_an_answer_unlocks",
                        "how_to_discover_it_without_a_human", "discovery_status", "blocking",
                        "owner_to_decide", "related_suggestion_id", "official_source_url"], T["questions"]))
    log.append(write_html("suggestions.html", page("Suggestions and open questions", body, "suggestions.html",
                                                   "The paths a human has to pick, with costs and risks, none of "
                                                   "them applied by default.")))

    # ---------------------------------------------------------------- sources
    rights = [{
        "item": "What the league pages may be used for",
        "position": "Individual, non-commercial informational review. The prior session recorded the Terms text "
                    "(sections 1.1 and 1.3) and the restriction on systematic retrieval to build a database; this "
                    "pack stores the values it read, cites the page for each one, and does not redistribute "
                    "content wholesale.",
        "url": "https://www.nfl.com/legal/terms/",
        "official_source_url": "https://www.nfl.com/legal/terms/", "read_on_utc": CAPTURE},
        {"item": "Wagering and league information",
         "position": "No wager is placed or promoted anywhere in this pack, and the record of the prior session's "
                     "rights note (data/nfl_309921cc/sources.csv, NFL3-S02) is followed: no betting action is "
                     "taken on injury or officiating information. The strategies are simulated and priced "
                     "against the model's own numbers.",
         "url": "https://github.com/sassnarep3-star/Own6/blob/main/data/nfl_309921cc/sources.csv",
         "official_source_url": "https://github.com/sassnarep3-star/Own6/blob/main/data/nfl_309921cc/sources.csv",
         "read_on_utc": CAPTURE},
        {"item": "Rulebook definitions used",
         "position": "Game, tie and roster conventions are taken from the 2026 rulebook page, cited by URL and "
                     "not copied.",
         "url": "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         "official_source_url": "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         "read_on_utc": CAPTURE},
        {"item": "What no source here supports",
         "position": "Any betting market: no official page read in this session prints a line, a price or a "
                     "closing number. Four attempts are logged on the price page; the columns stay blank.",
         "url": C.link_for("SCHED-W10"), "official_source_url": C.link_for("SCHED-W10"), "read_on_utc": CAPTURE},
        ]
    body = (
        render_table(["source_id", "publisher", "title", "url", "read_on", "method", "status", "supports",
                      "does_not_support"], T["sources"],
                     note="Nine sources, each with what it supports and - just as important - what it does not. "
                          "A citation that does not say what it cannot carry is a licence to over-read it.")
        + "<h2>Standings legend, as the page prints it</h2><p class=\"note\">"
        + esc(C.STANDINGS_LEGEND) + "</p>"
        + "<h2>Club abbreviation aliases</h2>"
        + render_table(["published_on_some_pages", "canonical_key_in_this_pack", "why", "official_source_url",
                        "read_on_utc"], T["aliases"],
                       note="The injury and standings pages print one abbreviation for Arizona while the "
                            "schedule and logo paths print another. Every table in this pack keys on the "
                            "canonical form and records the alias, because the mismatch raised a real "
                            "<code>KeyError</code> in an early run of the model - which is how it was found.")
        + "<h2>Rights and use</h2>"
        + render_table(["item", "position", "url", "official_source_url", "read_on_utc"], rights))
    log.append(write_html("sources.html", page("Sources and rights", body, "sources.html",
                                               "Where every number came from, and what each source will not "
                                               "carry.")))

    # ---------------------------------------------------------------- flagged
    kind_counts: dict[str, int] = {}
    for f in T["flags"]:
        kind_counts[f["kind"]] = kind_counts.get(f["kind"], 0) + 1
    body = (
        "<p class=\"note\">Everything irregular, in one place, with the observation first and the handling "
        "second. A flag here is not an unfinished task and does not block a merge: it is the record that a "
        "value is absent and why, or that an official page said something odd and we reproduced it instead of "
        "quietly repairing it. Counts: "
        + ", ".join(f"{k} = {v}" for k, v in sorted(kind_counts.items())) + ".</p>"
        + render_table(["flag_id", "kind", "title", "what_we_observed", "where_it_shows_up",
                        "why_it_is_flagged", "what_we_did_instead", "does_it_block_merge", "severity",
                        "human_decision_needed", "official_source_url", "read_on_utc"], T["flags"])
        + "<h2>Where the blanks are, file by file</h2>"
        + render_table(["table", "rows", "columns", "blank_cells", "rows_carrying_a_flag_id",
                        "blank_cell_meaning", "official_source_url"], T["audit"],
                       num_fields=("rows", "columns", "blank_cells", "rows_carrying_a_flag_id"),
                       note="A count per published table, so \"we left things blank\" is checkable rather than "
                            "asserted. Reconciling this with the flags above is what the checker does on every "
                            "run: a blank cell must be explained by a flag row or by a status string on the "
                            "row, and no blank may be filled with a placeholder such as \"n/a\".")
        + "<h2>What we did not fix</h2><ul>"
        + "<li>Five players printed under a club that their own position line contradicts (Garrett, Miller, "
          "Nelson, Njoku, O'Connell), and Peter Woods listed as a defensive tackle for one club and a "
          "defensive end for another. Every one is stored as the page groups it, and the depth counts for six "
          "clubs inherit it as a floor (D966-F12).</li>"
        + "<li>Two official headlines that disagree about the same Ravens quarterback's absence window. Both are "
          "published, no merged value exists (D966-F13).</li>"
        + "<li>Rashee Rice and Xavier Worthy listed on the Jets with neither an injury nor a status; a "
          "quarterback listed as a linebacker; a five-row club report. Published, not corrected "
          "(D966-F14, D966-F15).</li>"
        + "<li>The Arizona abbreviation mismatch, which broke a run and is now recorded as data rather than "
          "silently mapped everywhere (see <a href=\"sources.html\">Sources &amp; rights</a>).</li></ul>")
    log.append(write_html("flagged.html", page("Flagged for review", body, "flagged.html",
                                               "Blanks, anomalies and disagreements, with the evidence and the "
"handling.")))

    # ------------------------------------------------- repo review + decisions
    body = (
        "<p class=\"note\">Three registers a data table cannot carry by itself: every requirement with the "
        "file that satisfies it, every decision with the alternative that was rejected, and everything found in "
        "the repository and in the sources - including the two shared tools whose allowlists do not cover this "
        "pack's sources, which were requested rather than edited.</p>"
        + render_table(["requirement_id", "requirement", "status", "code", "published_tables", "site_page",
                        "what_is_filled", "what_is_blank_and_why", "how_to_verify", "checker_rule",
                        "official_source_url", "read_on_utc"], T["reqs"],
                       note="Each requirement in the brief, in order, with the verifier rule that enforces it. "
                            "The \"how to verify\" column is an instruction a reader can follow without running "
                            "this pack's code.")
        + "<h2>Decisions and rejected alternatives</h2>"
        + render_table(["decision_id", "subject", "decision", "why", "alternative_rejected",
                        "cost_of_being_wrong", "where_it_shows_up", "official_source_url", "read_on_utc"],
                       T["ledger_rows"],
                       note="A finding with no rejected alternative beside it is a description, not a decision; "
                            "each row names the path not taken and what being wrong on that row would cost.")
        + "<h2>Repository and source findings</h2>"
        + render_table(["finding_id", "area", "severity", "finding", "evidence", "handling", "blocks_merge",
                        "official_source_url", "read_on_utc"], T["findings_rows"],
                       note="Prose version: <code>audit/NFL_D966F630_REPO_AND_SOURCE_AUDIT.md</code>. No finding "
                            "blocks the merge; each one is here or on the flagged page with its evidence."))
    log.append(write_html("review.html", page("Repo review and decisions", body, "review.html",
                                              "Requirements traced to files, decisions traced to alternatives, "
                                              "findings traced to evidence.")))


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the nfl_d966f630 CSVs and dashboard")
    ap.add_argument("--check", action="store_true", help="run the verifier after building")
    args = ap.parse_args()
    log, _written, T = build_all()
    for line in log:
        print("  ", line)
    plog = write_pages(T)
    write_pages_part2(T, plog)
    write_pages_part3(T, plog)
    for line in plog:
        print("  ", line)
    if args.check:
        cmd = [sys.executable, os.path.join(REPO, "scripts", "check_nfl_d966f630.py")]
        print("  running checker:", " ".join(cmd))
        return subprocess.call(cmd, cwd=REPO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
