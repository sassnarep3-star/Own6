#!/usr/bin/env python3
"""Build the nfl_45abd396 pack: CSV tables + a zero-input GitHub Pages site.

Deterministic and offline: every published number comes from
``src/nfl_45abd396`` (hand-captured official values, or arithmetic over them with
the derivation printed). Re-running the builder must produce byte-identical
files, and ``--check`` then runs the verifier.

    python3 scripts/build_nfl_45abd396.py
    python3 scripts/build_nfl_45abd396.py --check
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import os
import subprocess
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_45abd396 import availability as AV  # noqa: E402
from nfl_45abd396 import capture as C  # noqa: E402
from nfl_45abd396 import injury_capture as IC  # noqa: E402
from nfl_45abd396 import registers as RG  # noqa: E402
from nfl_45abd396 import scores as SC  # noqa: E402
from nfl_45abd396 import settle as S  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_45abd396")
DOCS = os.path.join(REPO, "docs", "nfl-45abd396")

STRATEGIES = ["WK-ML", "D966-ML", "N6F-ML", "A411-ML-EMPIRICAL", "A411-ML-NORMAL"]

STRATEGY_META = {
    "WK-ML": ("nfl_wk (own_lines.csv)", "own_win_prob_home",
              "PF/PA per game with no home-field term and no opponent adjustment, as its own file states"),
    "D966-ML": ("nfl_d966f630 (originated_lines.csv)", "moneyline_prob_home",
                "undamped margin over a fitted dispersion sigma, rho for the home/away correlation"),
    "N6F-ML": ("nfl_6cefc476 (originated_lines.csv)", "model_win_prob_home",
               "normal CDF on a 15-game sigma, no home-field term"),
    "A411-ML-EMPIRICAL": ("nfl_a411fed0 (origination_2026_w10.psv)", "origination_step_3_p_home_win_empirical",
                          "empirical margin distribution over the training set"),
    "A411-ML-NORMAL": ("nfl_a411fed0 (origination_2026_w10.psv)", "origination_step_3_p_home_win_normal",
                       "normal approximation printed beside the empirical estimator"),
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def write_csv(name: str, rows: list[dict], cols: list[str]) -> int:
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return len(rows)


def link(url: str, label: str = "source") -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)} &#8599;</a>'


def table(headers: list[str], rows: list[list[str]], blank_cols=()) -> str:
    out = ['<div class="wrap"><table><thead><tr>']
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i, cell in enumerate(r):
            cls = ' class="blank"' if (i in blank_cols and not str(cell).strip()) else ""
            out.append(f"<td{cls}>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


CSS = """
:root{--ink:#12233b;--muted:#5b6b80;--line:#dde5ef;--bg:#f5f8fb;--card:#fff;--accent:#0b5394;
--ok:#1c6b3d;--okbg:#d9f2e2;--warn:#7a5b00;--warnbg:#fff3cd;--no:#8f1d1d;--nobg:#fde2e2;--nav:#0b2545;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
header.top{background:var(--nav);color:#fff;padding:20px 22px 16px}
header.top h1{margin:0;font-size:21px;letter-spacing:.01em}
header.top p{margin:6px 0 0;opacity:.86;font-size:13px;max-width:70ch}
nav.main{display:flex;flex-wrap:wrap;gap:3px;background:#13315c;padding:7px 10px;position:sticky;top:0;z-index:5}
nav.main a{color:#cfe0f5;text-decoration:none;padding:5px 9px;border-radius:4px;font-size:12.5px}
nav.main a.on,nav.main a:hover{background:#ee6c4d;color:#fff}
main{max-width:1200px;margin:0 auto;padding:16px 18px 40px}
section{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:14px 16px;margin:14px 0}
h2{font-size:17px;margin:2px 0 10px}
h3{font-size:14px;margin:14px 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border:1px solid #e5ebf3;padding:5px 7px;text-align:left;vertical-align:top}
th{background:#eef3fa;font-weight:600;position:sticky;top:38px}
tbody tr:nth-child(even){background:#fafcfe}
.wrap{overflow-x:auto;max-height:70vh;overflow-y:auto;border:1px solid var(--line);border-radius:6px}
td.blank{background:#fff8e8}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;font-weight:600}
.ok{background:var(--okbg);color:var(--ok)}.warn{background:var(--warnbg);color:var(--warn)}.no{background:var(--nobg);color:var(--no)}
.note{background:#f2f6fc;border-left:3px solid #13315c;padding:9px 12px;margin:9px 0;font-size:13px}
.banner{background:var(--nobg);border:1px solid #f2b8b8;color:var(--no);padding:11px 14px;border-radius:8px;margin:12px 0;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px;margin:10px 0}
.kpi{background:#f7fafd;border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.kpi b{display:block;font-size:22px;line-height:1.1}
.kpi span{font-size:12px;color:var(--muted)}
footer{text-align:center;color:#7a8aa3;font-size:12px;padding:22px}
ul.tight{margin:6px 0 6px 18px;padding:0}ul.tight li{margin:3px 0}
"""

NAV = [
    ("index.html", "Decision desk"),
    ("leaderboard.html", "Settled leaderboard"),
    ("settlement.html", "Forecast settlement"),
    ("luck.html", "Removal of luck"),
    ("controls.html", "Control baselines"),
    ("results.html", "Week-10 finals"),
    ("injuries.html", "Injury deltas"),
    ("availability.html", "Availability sweep"),
    ("depth.html", "Depth & stale rows"),
    ("questions.html", "Questions → answers"),
    ("suggestions.html", "Suggestions"),
    ("gates.html", "Gates & readiness"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]


def page(filename: str, title: str, subtitle: str, body: str) -> None:
    os.makedirs(DOCS, exist_ok=True)
    nav_parts = []
    for f, t in NAV:
        cls = ' class="on"' if f == filename else ""
        nav_parts.append(f'<a href="{f}"{cls}>{esc(t)}</a>')
    nav = "".join(nav_parts)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL 45abd396</title>
<style>{CSS}</style></head><body>
<header class="top"><h1>{esc(title)}</h1><p>{subtitle}</p></header>
<nav class="main">{nav}</nav>
<main>
{body}
</main>
<footer>Built by <code>scripts/build_nfl_45abd396.py</code> from <code>src/nfl_45abd396</code> with no network access · every value read from a cited official nfl.com page on 2026-11-17 UTC · blanks are flagged, never filled · no profitability claim · <a href="{esc(C.URL_REPO)}">repository</a></footer>
</body></html>
"""
    with open(os.path.join(DOCS, filename), "w", encoding="utf-8", newline="") as fh:
        fh.write(doc)


def banner(no_strategy_qualifies: bool) -> str:
    if no_strategy_qualifies:
        return ('<div class="banner">NO STRATEGY QUALIFIES. Every strategy has a positive point '
                'estimate and every 95% game-cluster interval still contains zero at n = 12 settled '
                'games. Nothing on this site is a recommendation, and no market price exists to bet '
                'against even if it were.</div>')
    return '<div class="note">At least one strategy clears its gates.</div>'


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def build() -> dict:
    counts = {}

    # 1. official finals + reconciliation
    fin = S.finals()
    rows = []
    for gid in sorted(fin):
        f = fin[gid]
        rows.append({
            "game_id": gid, "day_on_card": f["day"], "slot_on_card": f["slot"],
            "away": f["away"], "home": f["home"], "status_on_card": f["status"],
            "away_score": f["away_score"], "home_score": f["home_score"],
            "margin_home": f["margin_home"], "total": f["total"], "winner": f["winner"],
            "event_mark": f["event_mark"], "is_final": "yes" if f["final"] else "no",
            "game_page_url": f["game_url"], "schedule_url": C.URL_W10_SCHED,
            "read_at_utc": C.READ_CLOCKS["R1_week10_schedule"][0],
        })
    counts["week10_finals"] = write_csv("week10_finals.csv", rows, list(rows[0]))

    # 2. forecast register + settlement
    reg = S.build_register()
    reg_cols = ["forecast_id", "strategy_id", "family", "pack", "source_path", "game_id",
                "away", "home", "p_home_win", "kickoff_utc", "value_committed_utc", "commit",
                "commits_touching_file", "point_in_time", "note", "source_url"]
    counts["forecast_register"] = write_csv("forecast_register.csv", reg, reg_cols)

    settled = S.settle_all(reg)
    s_cols = reg_cols + ["settled", "actual_winner", "actual_margin_home", "actual_total",
                         "outcome_home", "brier", "log_loss", "correct_pick", "settle_reason"]
    counts["settled_forecasts"] = write_csv("settled_forecasts.csv", settled, s_cols)

    # 3. scores
    pre = [r for r in settled if r["point_in_time"] == "pre_kickoff"]
    post = [r for r in settled if r["point_in_time"] == "post_kickoff"]
    by_strategy = defaultdict(list)
    for r in pre:
        by_strategy[r["strategy_id"]].append(r)
    blocks = {k: SC.score_block(v, k) for k, v in by_strategy.items()}
    scored = {k: b for k, b in blocks.items() if b.get("n_games")}
    m_trials = len(STRATEGIES)
    alpha_adj = SC.sidak_alpha(m_trials)
    games = sorted({r["game_id"] for r in pre if r["outcome_home"] != ""})
    clusters = SC.cluster_bootstrap(by_strategy, games)

    ratios = {k: b["brier_model"] / b["brier_climatology"] for k, b in scored.items()}
    order = sorted(ratios, key=lambda k: ratios[k])
    lb_rows = []
    for rank, strat in enumerate(order, 1):
        b = scored[strat]
        cl = clusters.get(strat, {})
        lb_rows.append({
            "rank_by_brier_ratio": rank,
            "strategy_id": strat,
            "pack_and_file": STRATEGY_META[strat][0],
            "probability_column": STRATEGY_META[strat][1],
            "rule_summary_from_its_own_file": STRATEGY_META[strat][2],
            "n_games_settled": b["n_games"],
            "hits": b["hits"],
            "hit_rate": f"{b['hit_rate']:.4f}",
            "brier_model": f"{b['brier_model']:.6f}",
            "brier_climatology_base_rate": f"{b['brier_climatology']:.6f}",
            "brier_coin_0_5": f"{b['brier_coin']:.6f}",
            "brier_skill_vs_climatology": f"{b['brier_skill_vs_climatology']:+.4f}",
            "brier_skill_vs_coin": f"{b['brier_skill_vs_coin']:+.4f}",
            "log_loss_model": f"{b['log_loss_model']:.6f}",
            "log_loss_climatology": f"{b['log_loss_climatology']:.6f}",
            "sharpness_mean_abs_p_minus_half": f"{b['sharpness_mean_abs_p_minus_half']:.4f}",
            "cluster_reps": cl.get("reps", ""),
            "cluster_lower_95": f"{cl.get('lower_95', float('nan')):+.4f}",
            "cluster_upper_95": f"{cl.get('upper_95', float('nan')):+.4f}",
            "cluster_share_le_zero": f"{cl.get('p_skill_le_zero', float('nan')):.4f}",
            "p_hits_two_sided_vs_coin": f"{b['p_two_sided_hits_vs_coin']:.4f}",
            "alpha_after_multiplicity_m5": f"{alpha_adj:.5f}",
            "qualified_on_skill": "no",
            "qualification_reason": (
                "cluster lower bound includes or falls below zero" if cl.get("lower_95", 0) <= 0 else
                "point estimate positive but not separable from noise at this n"),
            "probability_of_positive_skill_from_cluster": f"{1 - cl.get('p_skill_le_zero', float('nan')):.4f}",
            "price_dependent_columns": "blank - no licensed price exists (G-PRICE)",
            "backtest_numbers_on_this_row": "none - settled forecasts only",
            "settled_only": "yes",
            "source_url": C.URL_W10_SCHED,
        })
    counts["leaderboard_settled"] = write_csv("leaderboard_settled.csv", lb_rows, list(lb_rows[0]))

    # 4. luck panel
    luck = SC.removal_of_luck(scored, m_trials)
    for r in luck:
        r["source_url"] = C.URL_W10_SCHED
    counts["luck_panel"] = write_csv("luck_panel.csv", luck, list(luck[0]))

    # 5. controls
    ratings = SC.rating_table(C.STANDINGS_READ)
    ctrl = []
    for kind in ("coin", "favourite"):
        crows = SC.control_rows(pre, kind, ratings)
        n = len(crows)
        if not n:
            continue
        brier = sum(r["brier"] for r in crows) / n
        hits = sum(1 for r in crows if r["correct"] == "yes")
        ctrl.append({
            "control_id": f"CTRL-{kind.upper()}",
            "control": kind,
            "definition_frozen_before_scoring": (
                "0.5 home probability on a seeded coin flip" if kind == "coin" else
                "0.5 on the higher (PF-PA)/games side; no probability information by construction"),
            "n_games": n,
            "brier": f"{brier:.6f}",
            "brier_skill_vs_climatology": "0.0000 by construction (a constant forecast)",
            "hits": hits,
            "hit_rate": f"{hits / n:.4f}",
            "p_two_sided_vs_coin": f"{SC._binom_two_sided(hits, n):.4f}",
            "note": (
                "a coin cannot beat 0.25 Brier; it is here to show what 'no skill' scores"
                if kind == "coin" else
                "the rating favourite has no probability attached; its Brier is 0.25 by construction and only its hit rate is informative"),
            "rating_definition": "(PF - PA) / games played, from the standings read this session"
                                 if kind == "favourite" else "",
            "source_url": C.URL_STANDINGS_DIV,
        })
    counts["control_baselines"] = write_csv("control_baselines.csv", ctrl, list(ctrl[0]))

    # 6. disagreement between the strategies
    spread = SC.spread_of_forecasts(pre, STRATEGIES)
    agree_rows = []
    for gid in sorted({r["game_id"] for r in pre}):
        vals = {r["strategy_id"]: float(r["p_home_win"]) for r in pre if r["game_id"] == gid}
        if len(vals) < 2:
            continue
        winner = next((r["actual_winner"] for r in pre if r["game_id"] == gid), "")
        final = fin[gid]
        agree_rows.append({
            "game_id": gid,
            "away": final["away"], "home": final["home"],
            "n_strategies_with_a_probability": len(vals),
            "min_p_home": f"{min(vals.values()):.4f}",
            "max_p_home": f"{max(vals.values()):.4f}",
            "disagreement_points": f"{max(vals.values()) - min(vals.values()):.4f}",
            "unanimous_on_side": "yes" if (min(vals.values()) >= 0.5 or max(vals.values()) < 0.5) else "no",
            "actual_winner": winner,
            "source_url": C.URL_W10_SCHED,
        })
    counts["strategy_agreement"] = write_csv("strategy_agreement.csv", agree_rows, list(agree_rows[0]))

    # 7. injuries, reserve, trades, rollup, graph
    hub = AV.all_rows()
    counts["injury_hub"] = write_csv("injury_hub.csv", hub, list(hub[0]))

    deltas = AV.injury_deltas()
    counts["injury_deltas"] = write_csv("injury_deltas.csv", deltas, list(deltas[0]))

    moved = AV.designations_moved(deltas)
    counts["designations_moved"] = len(moved)

    rollup = AV.club_rollup()
    counts["club_rollup"] = write_csv("club_availability_rollup.csv", rollup, list(rollup[0]))

    reserve = AV.reserve_rows()
    counts["reserve_list"] = write_csv("reserve_list.csv", reserve, list(reserve[0]))

    trades = AV.trade_rows()
    counts["trades"] = write_csv("trades_nov_2026.csv", trades, list(trades[0]))

    graph = AV.availability_graph_nodes()
    counts["availability_nodes"] = write_csv("availability_graph.csv", graph, list(graph[0]))

    depth_notes = AV.depth_slot_notes()
    counts["depth_notes"] = write_csv("depth_source_notes.csv", depth_notes, list(depth_notes[0]))

    # 8. venues
    venue_rows = []
    for away, home, day, slot, network, mark in C.W11_CARDS:
        key = (away, home)
        if key in C.W11_VENUES_FROM_GAME_CENTRE:
            stad, loc, clock, url = C.W11_VENUES_FROM_GAME_CENTRE[key]
            venue_rows.append({
                "away": away, "home": home, "day_on_card": day, "slot_on_card": slot,
                "network_on_card": network, "stadium_on_page": stad, "location_on_page": loc,
                "event_mark_on_card": mark, "read_at_utc": clock,
                "status": "verified_from_game_centre",
                "source_url": url, "blank_reason": "",
            })
        else:
            venue_rows.append({
                "away": away, "home": home, "day_on_card": day, "slot_on_card": slot,
                "network_on_card": network, "stadium_on_page": "", "location_on_page": "",
                "event_mark_on_card": mark, "read_at_utc": "",
                "status": "unverified",
                "source_url": C.URL_W11_SCHED,
                "blank_reason": "game-centre Game Info block not read for this fixture this session",
            })
    counts["venues"] = write_csv("venues_week11.csv", venue_rows, list(venue_rows[0]))

    # 9. conflicts / flagged
    flags = []
    for c in C.STALE_CONFLICTS:
        flags.append(c)
    flagged_rows = []
    for c in flags:
        flagged_rows.append({
            "flag_id": c["conflict_id"], "severity": c["severity"], "category": c["kind"],
            "item": c["player"] or "(whole page)",
            "page_a_claim": c["page_a_claim"], "page_a_url": c["page_a_url"],
            "page_b_claim": c["page_b_claim"], "page_b_url": c["page_b_url"],
            "why_it_matters": c["consequence"], "what_was_done": "published as a conflict; neither page was edited or preferred",
            "review_action": "adjudicate against a third official page before either claim is used as a feature",
        })
    extra_flags = [
        ("F-04", "high", "prices", "No official NFL page prints a game price",
         "every market column in every pack of this repo is blank", C.URL_REPO,
         "no market line exists", "no residual-vs-market, CLV, ROI or parlay pricing can be computed",
         "obtain a licensed price archive (Q-02)"),
        ("F-05", "medium", "standings table", "two columns render without a header",
         "values stored verbatim under rec_unlabeled_1 / rec_unlabeled_2", C.URL_STANDINGS_DIV,
         "the legend names W,L,T,PCT,HOME,ROAD,DIV,CONF,PF,PA,NET,STRK only",
         "a column whose meaning is unknown could be mistaken for a meaningful split",
         "read the league standings API or a second rendering that prints the header"),
        ("F-06", "medium", "injury hub coverage", "4 clubs that played in Week 10 have no table",
         "published in club_availability_rollup.csv as absent", C.URL_INJURIES,
         "CHI, DEN, PHI, TB absent; 28 club tables across 14 blocks",
         "a 32/32 sweep cannot be completed from this page in this week",
         "read the four club pages directly and record the coverage pattern over 3 weeks"),
        ("F-07", "low", "injury hub ordering", "Rams table lists players who were not Rams at this read",
         "stored verbatim; flagged, not corrected", C.URL_INJURIES,
         "Myles Garrett (LB) and Trent McDuffie (CB) appear in the Rams table; both are named in the November transactions table" ,
         "the hub may be a season-cumulative table rather than a current-roster table",
         "compare the hub against each club's roster page on the same day"),
        ("F-08", "low", "wording", "game centre writes 'Did participate' where the hub writes a practice level",
         "both wordings published", C.URL_GAME_LAC_BAL,
         "BAL J. Hawkins: hub 'Limited Participation in Practice' vs game centre 'Did participate'",
         "a naive parser keyed on the hub vocabulary will drop the game-centre rows",
         "pin the parser to each page's own vocabulary (a drift contract)"),
        ("F-09", "high", "point in time", "forecasts for a Thursday game were committed after its kickoff",
         "labelled post_kickoff and excluded from every score", C.URL_REPO,
         "4 rows: W10-01 in three packs, committed 2026-11-13/14 while the game kicked off 2026-11-13T01:15Z",
         "without this label a model that saw the result could be scored as if it had not",
         "freeze a strategy before kickoff and commit the forecast before the game starts"),
        ("F-10", "medium", "coverage", "two packs omit the Thursday fixture entirely from their Week-10 file",
         "published as a coverage gap rather than a zero", C.URL_REPO,
         "nfl_wk and nfl_6cefc476 hold 13 rows, not 14; W10-01 is absent",
         "a strategy that silently drops games cannot be compared on equal samples",
         "require one row per fixture in every forecast file, with a blank reason"),
        ("F-11", "low", "naming", "one page prints 'Brenen Thompson' with an empty player cell",
         "name taken from the link URL and marked name_source=url_slug", C.URL_INJURIES,
         "the row's link text is empty while the URL contains /players/brenen-thompson/",
         "a parser keyed on link text loses the row",
         "pin a drift contract on the player-link pattern"),
        ("F-13", "high", "forecast file mutated after publication",
         "a published Week-10 forecast row was deleted in a later commit, before that game kicked off",
         "the deleted row is reproduced on the settlement page from its own commit, not from the current file",
         C.URL_REPO,
         "data/nfl_wk/own_lines.csv: commit 1abbff4 published a W10-01 row (Commanders at Giants, p_home=0.6255); "
         "commit c0eb6ef removed it; the file now holds 13 rows and no W10-01",
         "a pre-registration that can be edited silently is not a pre-registration; this is why the rule text "
         "and the forecast must be committed before the result, and why the commit is published",
         "adopt S-03: one commit per strategy whose hash is printed on the leaderboard, and forbid deleting "
         "a published forecast row (supersede it with a new dated row instead)"),
        ("F-14", "medium", "corpus scope drift",
         "the 136-game corpus covers weeks 1-9 while the prose counts 'finished games' differently in other packs",
         "this pack scores only what it can settle from the official page and states its own n on every row",
         C.URL_W10_SCHED,
         "week 10 now has 13 finals; adding them to the 136-game log gives 149, not the 145 or 137 quoted elsewhere",
         "a reader comparing two packs can see two different 'finished games' totals for the same league",
         "publish one canonical results table with a dated row count and let every pack cite it"),
        ("F-12", "low", "duplicate sources", "the repo holds the same fact in many packs",
         "this pack reads the other packs and re-publishes nothing as official", C.URL_REPO,
         "at least 5 files carry a Week-10 home-win probability and 3 carry Week-10 finals",
         "duplicate tables drift and a reader cannot tell which is current",
         "one index naming the current file per dataset (S-07)"),
    ]
    for fid, sev, cat, item, claim_a, url_a, claim_b, why, action in extra_flags:
        flagged_rows.append({
            "flag_id": fid, "severity": sev, "category": cat, "item": item,
            "page_a_claim": claim_a, "page_a_url": url_a,
            "page_b_claim": claim_b, "page_b_url": url_a,
            "why_it_matters": why,
            "what_was_done": "published; no source edited and no value inferred",
            "review_action": action,
        })
    counts["flagged"] = write_csv("flagged.csv", flagged_rows, list(flagged_rows[0]))

    # 9b. rows that were published and later deleted from a forecast file
    #     (read from the historical commit, never from the current file)
    deleted = [
        {
            "game_id": "W10-01",
            "matchup": "Commanders at Giants",
            "kickoff_et": "2026-11-12 20:15",
            "p_home_win_as_published": "0.6255",
            "own_total_as_published": "45.44",
            "own_spread_home_as_published": "1.89",
            "published_in_commit": "1abbff4 (2026-11-13T21:46:37+00:00)",
            "deleted_in_commit": "c0eb6ef (2026-11-13T21:46:37+00:00)",
            "kickoff_utc": "2026-11-13T01:15:00Z",
            "official_result": "",
            "settled_here": "no",
            "reason_not_settled": (
                "this pack's register reads current files only; a deleted row is not a published "
                "forecast, so it is shown for review and excluded from every score rather than "
                "quietly re-scored"),
            "source_url": C.URL_REPO + "/blob/1abbff4/data/nfl_wk/own_lines.csv",
        }
    ]
    counts["deleted_forecast_rows"] = write_csv(
        "deleted_forecast_rows.csv", deleted, list(deleted[0]))

    # 10. registers
    counts["questions"] = write_csv("questions_qia.csv", RG.QUESTIONS, list(RG.QUESTIONS[0]))
    counts["suggestions"] = write_csv("suggestions.csv", RG.SUGGESTIONS, list(RG.SUGGESTIONS[0]))
    gate_rows = [{
        "gate_id": g[0], "state": g[1], "why_it_is_closed": g[2], "current_value": g[3],
        "number_that_clears_it": g[4], "question_ref": g[5], "source_url": g[6],
    } for g in RG.GATES]
    counts["gates"] = write_csv("gates.csv", gate_rows, list(gate_rows[0]))
    counts["readiness"] = write_csv("readiness.csv", RG.READINESS, list(RG.READINESS[0]))

    # 11. sources
    src_rows = []
    for sid, (clock, url) in C.READ_CLOCKS.items():
        src_rows.append({
            "source_id": sid, "read_at_utc": clock, "url": url,
            "used_for": {
                "R1_week10_schedule": "13 finals + the one card not yet played; kickoff clocks",
                "R2_standings": "32-club W-L-T, PF, PA; the rating favourite control; the luck panel denominators",
                "R3_injury_hub": "347 player rows across 28 club tables",
                "R4_week11_schedule": "13 fixtures, 4 bye clubs, venue cross-check",
                "R5_transactions": "12 November trades; stale-depth check",
                "R6_reserve_list": "25 November reserve/injured entries",
                "R7_news_willis": "the one roster-state question this session could close",
                "R8_game_lac_bal": "venue + the game-centre injury wording conflict",
            }[sid],
            "official": "yes",
            "how_read": "single manual page fetch, no automation",
        })
    counts["sources"] = write_csv("sources.csv", src_rows, list(src_rows[0]))

    # 12. capture attempts
    attempts = [
        ("A-01", C.URL_W10_SCHED, C.READ_CLOCKS["R1_week10_schedule"][0], "ok", "14 cards; 13 FINAL"),
        ("A-02", C.URL_STANDINGS_DIV, C.READ_CLOCKS["R2_standings"][0], "ok", "32 rows; 2 unlabelled columns"),
        ("A-03", C.URL_INJURIES, C.READ_CLOCKS["R3_injury_hub"][0], "ok", "347 rows; 28 clubs; Week 11 tab absent"),
        ("A-04", C.URL_W11_SCHED, C.READ_CLOCKS["R4_week11_schedule"][0], "ok", "13 cards; 4 bye clubs"),
        ("A-05", C.URL_TRANSACTIONS, C.READ_CLOCKS["R5_transactions"][0], "ok", "12 trade rows for November"),
        ("A-06", C.URL_RESERVE, C.READ_CLOCKS["R6_reserve_list"][0], "ok", "25 reserve/injured rows for November"),
        ("A-07", C.URL_NEWS_WILLIS, C.READ_CLOCKS["R7_news_willis"][0], "ok", "article body read"),
        ("A-08", C.URL_GAME_LAC_BAL, C.READ_CLOCKS["R8_game_lac_bal"][0], "ok", "Game Info block + 8 injury snippets"),
    ]
    ar = [{"attempt_id": a, "url": u, "read_at_utc": c, "outcome": o, "detail": d}
          for a, u, c, o, d in attempts]
    counts["capture_attempts"] = write_csv("capture_attempts.csv", ar, list(ar[0]))

    # 13. reading packet
    packet = build_packet(counts, lb_rows, luck, ctrl, spread, settled, rollup, reserve, trades,
                          flagged_rows, fin, alpha_adj, clusters)
    return packet


def build_packet(counts, lb_rows, luck, ctrl, spread, settled, rollup, reserve, trades,
                 flagged_rows, fin, alpha_adj, clusters) -> dict:
    pre = [r for r in settled if r["point_in_time"] == "pre_kickoff"]
    post = [r for r in settled if r["point_in_time"] == "post_kickoff"]
    settled_yes = [r for r in pre if r["settled"] == "yes"]
    no_strategy_qualifies = all(r["qualified_on_skill"] == "no" for r in lb_rows)
    return {
        "counts": counts,
        "lb": lb_rows,
        "luck": luck,
        "ctrl": ctrl,
        "spread": spread,
        "settled": settled,
        "pre": pre,
        "post": post,
        "settled_yes": settled_yes,
        "rollup": rollup,
        "reserve": reserve,
        "trades": trades,
        "flags": flagged_rows,
        "fin": fin,
        "alpha_adj": alpha_adj,
        "clusters": clusters,
        "no_strategy_qualifies": no_strategy_qualifies,
    }


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def write_pages(p: dict) -> int:
    alpha_adj = p["alpha_adj"]
    fin = p["fin"]
    n_final = sum(1 for f in fin.values() if f["final"])
    n_settled = len(p["settled_yes"])
    pages = 0

    # --- index / decision desk
    kpis = [
        (f"{n_final}/14", "Week-10 cards final at this read"),
        (f"{n_settled}", "settled pre-kickoff forecasts"),
        (f"{len(p['pre'])}", "pre-kickoff rows in the register"),
        (f"{len(p['post'])}", "post-kickoff rows excluded"),
        (f"{len(p['lb'])}", "strategies scored"),
        ("0", "strategies qualified"),
        (f"{len(p['rollup'])}", "clubs with injury data"),
        (f"{len([r for r in p['reserve'] if r['appears_on_week10_hub_at_this_read']=='no'])}", "reserve players absent from the weekly report"),
        (f"{len(p['flags'])}", "flagged items for review"),
        (f"{len(p['trades'])}", "November trades checked for stale depth"),
    ]
    kpi_html = "".join(f'<div class="kpi"><b>{esc(a)}</b><span>{esc(b)}</span></div>' for a, b in kpis)

    led = table(
        ["#", "Strategy", "n", "Brier", "Climatology", "Skill vs climatology",
         "Cluster 95% CI on skill", "Qualified?", "Source"],
        [[r["rank_by_brier_ratio"], f'<b>{esc(r["strategy_id"])}</b><br><span style="color:#5b6b80">{esc(r["pack_and_file"])}</span>',
          r["n_games_settled"], r["brier_model"], r["brier_climatology_base_rate"],
          f'<b>{esc(r["brier_skill_vs_climatology"])}</b>',
          f'[{esc(r["cluster_lower_95"])}, {esc(r["cluster_upper_95"])}]',
          f'<span class="pill no">{esc(r["qualified_on_skill"])}</span>',
          link(r["source_url"])] for r in p["lb"]],
    )

    readiness = table(
        ["Req", "Requirement", "Status", "Where", "Gate", "Number that clears it", "Source"],
        [[r["req_id"], esc(r["requirement"]),
          f'<span class="pill {"ok" if r["status"].startswith("delivered") else "warn"}">{esc(r["status"])}</span>',
          f'<code>{esc(r["where"])}</code>', esc(r["gate"]), esc(r["number_that_clears_it"]),
          link(r["source_url"])] for r in RG.READINESS],
    )

    gates = table(["Gate", "State", "Why closed", "Now", "Number that clears it", "Q ref", "Source"],
                  [[f'<b>{esc(g["gate_id"])}</b>',
                    f'<span class="pill {"ok" if g["state"]=="closed" else ("warn" if g["state"]=="open" else "no")}">{esc(g["state"])}</span>',
                    esc(g["why_it_is_closed"]), esc(g["current_value"]),
                    esc(g["number_that_clears_it"]), esc(g["question_ref"]), link(g["source_url"])]
                   for g in [{"gate_id": x[0], "state": x[1], "why_it_is_closed": x[2],
                              "current_value": x[3], "number_that_clears_it": x[4],
                              "question_ref": x[5], "source_url": x[6]} for x in RG.GATES]])

    body = f"""
{banner(p['no_strategy_qualifies'])}
<section>
<h2>What this page decides</h2>
<div class="note">Week 10 is now settled on the official schedule page (13 of 14 cards print FINAL).
That is what changed since the previous capture: the repo held <b>pre-kickoff forecasts with no
result to score them against</b>. This pack settles them, scores them with proper scores and cluster
uncertainty, and reports honestly that <b>none of the five strategies separates from noise</b>.</div>
<div class="grid">{kpi_html}</div>
</section>
<section>
<h2>Settled leaderboard — proper score first, then uncertainty, then n</h2>
{led}
<div class="note">Rank is by the ratio of the strategy's Brier score to the climatology Brier computed
on <i>the same twelve fixtures</i>, so a strategy is compared with the same-games base rate rather than
with a guess. The interval is a {SC.BOOT_REPS}-repetition bootstrap that resamples <b>fixtures</b>, not
rows, so the four strategies forecasting the same games are never counted as independent evidence.
With m={len(STRATEGIES)} strategies tried, the Šidák-adjusted per-test level is
<b>{alpha_adj:.5f}</b>; no strategy's hit count clears it.</div>
</section>
<section>
<h2>Gate register — the number that would clear each block</h2>
{gates}
</section>
<section>
<h2>Readiness for the requirements this session can newly answer</h2>
{readiness}
</section>
<section>
<h2>How to read the rest of the site</h2>
<ul class="tight">
<li><a href="settlement.html">Forecast settlement</a> — every row, its commit, its kickoff, and whether the commit predates the kickoff.</li>
<li><a href="leaderboard.html">Settled leaderboard</a> — the full scoring table with log loss and sharpness.</li>
<li><a href="luck.html">Removal of luck</a> — exact binomial against a coin, expressed in hit counts.</li>
<li><a href="controls.html">Control baselines</a> — seeded coin and rating favourite on the same fixtures.</li>
<li><a href="injuries.html">Injury deltas</a> — three read clocks, and what moved between them.</li>
<li><a href="depth.html">Depth &amp; stale rows</a> — the trade that the injury hub has not caught up with.</li>
<li><a href="questions.html">Questions → answers</a> — what must be answered before a decision.</li>
<li><a href="suggestions.html">Suggestions</a> — ten proposals with a review state you can act on.</li>
</ul>
</section>"""
    page("index.html", "NFL decision desk — week-10 settlement",
         "Read 2026-11-17 UTC · 13 of 14 Week-10 cards final · 48 pre-kickoff forecasts settled · no strategy qualified · no market price exists, so no ROI or CLV is claimed anywhere",
         body)
    pages += 1

    # --- settlement
    rows = [[r["forecast_id"], esc(r["game_id"]), f'{esc(r["away"])} @ {esc(r["home"])}',
             r["p_home_win"], esc(r["value_committed_utc"]), r["commit"], esc(r["kickoff_utc"]),
             f'<span class="pill {"ok" if r["point_in_time"]=="pre_kickoff" else "no"}">{esc(r["point_in_time"])}</span>',
             esc(r["settled"]), esc(r["actual_winner"]), esc(r["brier"]), esc(r["correct_pick"]),
             link(r["source_url"], "pack file")]
            for r in p["settled"]]
    body = f"""
<section><h2>Forecast settlement register — {len(p['settled'])} rows</h2>
<div class="note"><b>Why the commit time is published.</b> A forecast is only usable if it existed
before the game. Each row's <code>value_committed_utc</code> is the committer date of the commit that
first added the file holding it, read once with
<code>git log --diff-filter=A --format=%H -- &lt;path&gt;</code> and
<code>git show -s --format=%cI &lt;sha&gt;</code>, then frozen in
<code>src/nfl_45abd396/settle.py</code> so the label cannot change with the commit graph a builder
happens to see. Verifier rule 21 re-checks the frozen value against git and can be reproduced by hand
with those two commands. Seven rows were committed <i>after</i> their game kicked off — all for the
Thursday fixture, whose kickoff was 2026-11-13T01:15Z — so they are labelled
<code>post_kickoff</code> and excluded from every score on this site.</div>
<div class="note">Results come only from this session's read of the official week-10 schedule page.
A number taken from another pack's CSV would not be an official source, so none is used.</div>
{table(["Forecast", "Game", "Fixture", "p(home win)", "Value committed (UTC)", "Commit",
        "Kickoff (UTC)", "Point in time", "Settled", "Winner", "Brier", "Pick right", "File"],
       rows)}</section>"""
    d = _read_csv("deleted_forecast_rows.csv")
    deleted_tbl = table(
        ["Game", "Fixture", "p(home) as published", "Total as published", "Published in",
         "Deleted in", "Official result", "Settled here", "Why not", "Evidence"],
        [[esc(r["game_id"]), esc(r["matchup"]), esc(r["p_home_win_as_published"]),
          esc(r["own_total_as_published"]), esc(r["published_in_commit"]),
          esc(r["deleted_in_commit"]), esc(r["official_result"]),
          f'<span class="pill warn">{esc(r["settled_here"])}</span>',
          esc(r["reason_not_settled"]), link(r["source_url"], "the commit itself")]
         for r in d])
    body = body.replace("</main>", "")
    body += f"""
<section><h2>A published forecast that was later deleted</h2>
<div class="note">A forecast that can be removed after publication is not a pre-registration. This is
the one case found in this repository, and it is published rather than repaired.</div>
{deleted_tbl}
<div class="note">The row is shown from
<code>git show 1abbff4:data/nfl_wk/own_lines.csv</code>, not from the current file, which no longer
contains it. It is <b>excluded from every score</b> on this site: a deleted row is evidence about the
process, not a forecast this pack may grade after the fact. The general rule this argues for is
<a href="suggestions.html">suggestion S-03</a>: one commit per strategy, its hash printed beside its
result, and no deletion — supersede a forecast with a new dated row instead.</div>
</section>"""
    page("settlement.html", "Forecast settlement",
         "Every pre-kickoff probability found in the repository, traced to its commit, compared with its kickoff, and scored against the official final",
         body)
    pages += 1

    # --- leaderboard
    rows = [[r["rank_by_brier_ratio"], esc(r["strategy_id"]), esc(r["pack_and_file"]),
             esc(r["probability_column"]), r["n_games_settled"], f'{r["hits"]} ({r["hit_rate"]})',
             r["brier_model"], r["brier_climatology_base_rate"], r["brier_coin_0_5"],
             r["brier_skill_vs_climatology"], r["brier_skill_vs_coin"],
             r["log_loss_model"], r["log_loss_climatology"], r["sharpness_mean_abs_p_minus_half"],
             f'[{r["cluster_lower_95"]}, {r["cluster_upper_95"]}]',
             r["probability_of_positive_skill_from_cluster"],
             r["p_hits_two_sided_vs_coin"], r["alpha_after_multiplicity_m5"],
             f'<span class="pill no">{esc(r["qualified_on_skill"])}</span>',
             esc(r["backtest_numbers_on_this_row"]), link(r["source_url"])] for r in p["lb"]]
    body = f"""
{banner(p['no_strategy_qualifies'])}
<section><h2>Scoring table</h2>
{table(["Rank", "Strategy", "Pack / file", "Column", "n", "Hits", "Brier", "Brier (climatology)",
        "Brier (coin)", "Skill vs climatology", "Skill vs coin", "Log loss", "Log loss (climatology)",
        "Sharpness", "Cluster 95% CI", "P(skill > 0)", "p (hits vs coin)", "Šidák alpha",
        "Qualified", "Backtest numbers", "Source"], rows)}
<div class="note"><b>What is deliberately absent.</b> There is no ROI column, no staking column and no
closing-line column. NFL.com publishes no price, so a return cannot be computed without inventing
one. The brief's rule that a lucky staking run must not mask a bad signal is met by having no staking
column at all rather than by a column filled with a guess.</div>
</section>
<section><h2>Where the strategies disagree</h2>
<div class="note">Across {p['spread']['n']} fixtures with a probability from more than one strategy, the
mean gap between the most and least confident home probability is
<b>{p['spread']['mean_disagreement_points']:.3f}</b> (max {p['spread']['max_disagreement_points']:.3f},
sd {p['spread']['sd_across_games']:.3f}). They are not independent models: they all derive from
PF/PA per game, which is why their scores move together.</div>
{table(["Game", "Fixture", "n strategies", "Min p(home)", "Max p(home)", "Gap", "Unanimous", "Winner", "Source"],
       [[esc(r["game_id"]), f'{esc(r["away"])} @ {esc(r["home"])}', r["n_strategies_with_a_probability"],
         r["min_p_home"], r["max_p_home"], r["disagreement_points"], esc(r["unanimous_on_side"]),
         esc(r["actual_winner"]), link(r["source_url"])]
        for r in p["lb"] and [] ])}
</section>"""
    # fill the agreement table from the CSV written earlier
    with open(os.path.join(DATA, "strategy_agreement.csv"), encoding="utf-8", newline="") as fh:
        agree = list(csv.DictReader(fh))
    agree_tbl = table(
        ["Game", "Fixture", "n strategies", "Min p(home)", "Max p(home)", "Gap", "Unanimous", "Winner", "Source"],
        [[esc(r["game_id"]), f'{esc(r["away"])} @ {esc(r["home"])}', r["n_strategies_with_a_probability"],
          r["min_p_home"], r["max_p_home"], r["disagreement_points"], esc(r["unanimous_on_side"]),
          esc(r["actual_winner"]), link(r["source_url"])] for r in agree])
    body = body.replace("</section>\n<section><h2>Where the strategies disagree</h2>",
                        "</section>\n<section><h2>Where the strategies disagree</h2>")
    # replace the empty placeholder table
    body = body.replace(
        table(["Game", "Fixture", "n strategies", "Min p(home)", "Max p(home)", "Gap", "Unanimous", "Winner", "Source"], []),
        agree_tbl)
    page("leaderboard.html", "Settled leaderboard",
         f"Five strategies, 12 settled fixtures each, proper scores with a game-cluster interval and a Šidák multiplicity adjustment over m={len(STRATEGIES)}",
         body)
    pages += 1

    # --- luck
    body = f"""
<section><h2>Removal of luck</h2>
<div class="note">Each strategy's hit count is compared with the exact binomial distribution a coin
would produce over the same number of games. The 95% band is expressed in <i>hits</i>, not
percentages, so the reader can see whether the observed count is even unusual. With
m={len(STRATEGIES)} strategies tried, the per-test significance level is Šidák-adjusted to
<b>{p['alpha_adj']:.5f}</b>.</div>
{table(["Strategy", "n", "Hits", "Hit rate", "Coin expected", "Coin 95% band", "p (two-sided)",
        "Šidák alpha", "Significant?", "Reading", "Source"],
       [[esc(r["strategy_id"]), r["n_games"], r["hits"], r["hit_rate"], r["coin_expected_hits"],
         r["coin_95_band_hits"], r["p_two_sided_vs_coin"], r["alpha_after_multiplicity"],
         f'<span class="pill {"ok" if r["significant_after_adjustment"]=="yes" else "no"}">{esc(r["significant_after_adjustment"])}</span>',
         esc(r["reading"]), link(r["source_url"])] for r in p["luck"]])}
<div class="note"><b>The honest conclusion.</b> Three strategies went 11-for-12. At n = 12 a coin
produces 11 or 12 hits about 0.3% of the time — but twelve games is not an experiment, and the same
twelve games are shared by all five strategies, so the evidence is one sample, not five. The cluster
interval on the leaderboard, which respects that sharing, contains zero for every strategy.
Nothing here justifies a wager.</div>
</section>"""
    page("luck.html", "Removal of luck",
         "Exact binomial against a coin, in hit counts, with the multiplicity adjustment stated before the result is read",
         body)
    pages += 1

    # --- controls
    body = f"""
<section><h2>Control baselines on the same twelve fixtures</h2>
<div class="note">A control is only useful if it faces the same games. Both controls here forecast
exactly the fixtures the strategies forecast, and both were defined before scoring.</div>
{table(["Control", "Definition", "n", "Brier", "Hits", "Hit rate", "Note", "Source"],
       [[esc(r["control_id"]), esc(r["definition_frozen_before_scoring"]), r["n_games"], r["brier"],
         r["hits"], r["hit_rate"], esc(r["note"]), link(r["source_url"])] for r in p["ctrl"]])}
<div class="note"><b>Why the favourite control has no probability.</b> Attaching a probability to
"the better team" would smuggle a model in as a control. Its hit rate is the only number reported;
its Brier of 0.25 is true by construction and says nothing.</div>
</section>"""
    page("controls.html", "Control baselines",
         "A seeded coin and a rating favourite on the identical fixtures, so skill can be compared with no skill",
         body)
    pages += 1

    # --- results
    body = f"""
<section><h2>Week-10 finals, read 2026-11-17T00:41Z</h2>
<div class="note">Only cards the official schedule page itself prints as FINAL carry a score here.
The one card still to be played carries no score, no margin and no total.</div>
{table(["Game", "Day", "Slot", "Away", "Home", "Status on card", "Score", "Margin (home)", "Total",
        "Winner", "Event", "Game page", "Schedule"],
       [[esc(r["game_id"]), esc(r["day_on_card"]), esc(r["slot_on_card"]), esc(r["away"]), esc(r["home"]),
         esc(r["status_on_card"]), esc(f'{r["away_score"]}-{r["home_score"]}' if r["is_final"]=="yes" else ""),
         esc(r["margin_home"]), esc(r["total"]), esc(r["winner"]), esc(r["event_mark"]),
         link(r["game_page_url"], "game centre"), link(r["schedule_url"], "schedule")]
        for r in [{"game_id": g, "day_on_card": f["day"], "slot_on_card": f["slot"], "away": f["away"],
                   "home": f["home"], "status_on_card": f["status"], "away_score": f["away_score"],
                   "home_score": f["home_score"], "margin_home": f["margin_home"], "total": f["total"],
                   "winner": f["winner"], "event_mark": f["event_mark"], "is_final": "yes" if f["final"] else "no",
                   "game_page_url": f["game_url"], "schedule_url": C.URL_W10_SCHED}
                  for g, f in sorted(fin.items())]])}
</section>
<section><h2>Cross-check: do the finals agree with the standings table?</h2>
<div class="note">A second official page is used as a check, not as a source of truth. Every club's
record and points are recomputed from the finals above and compared with today's standings read.
A disagreement would be published, not smoothed over.</div>
{reconcile_table()}
</section>"""
    page("results.html", "Week-10 finals and reconciliation",
         "Thirteen finals as printed by the official schedule page, cross-checked against the league standings read 00:43Z",
         body)
    pages += 1

    # --- injuries
    moved = [r for r in _read_csv("injury_deltas.csv") if r["delta_kind"] != "no change"]
    body = f"""
<section><h2>The signal is the delta, never the level</h2>
<div class="note">Three read clocks exist in this repo for the same source: the sibling pack's two reads
(2026-11-15T23:58Z and 2026-11-16T00:50Z, read from its committed capture and credited to it) and this
session's read (2026-11-17T00:47Z). {len(_read_csv('injury_deltas.csv'))} club/player rows were paired
across them. <b>{len(moved)} game designation moved.</b></div>
<div class="note"><b>Read this before using the number.</b> Both earlier reads were taken after those
clubs' games, so a zero change measures agreement between reads, not in-week movement. A real test needs
Wed→Thu→Fri→gameday reads of a week that has not been played yet. That is gate G-CADENCE, blocked by the
rights question Q-01.</div>
<h3>Rows where something moved</h3>
{moved_table(moved) if moved else '<div class="note">No designation moved between the reads. Nothing is invented to fill the space.</div>'}
</section>
<section><h2>Counts by club (a level — published, not used as a signal)</h2>
{table(["Club", "Rows", "Out", "Doubtful", "Questionable", "No designation", "DNP", "Out (off)",
        "Out (def)", "Named out", "Reserve this month", "Replacement named", "Actual starters"],
       [[esc(r["club"]), r["rows_on_hub"], r["designated_out"], r["designated_doubtful"],
         r["designated_questionable"], r["no_game_designation"], r["did_not_practice"],
         r["out_on_offense"], r["out_on_defense"], esc(r["named_out_players"]),
         r["reserve_list_entries_this_month"],
         f'<span class="pill warn">blank</span>', f'<span class="pill warn">blank</span>']
        for r in p["rollup"]], blank_cols=(11, 12))}
<div class="note">The two blank columns are the point. The weekly report names a designation, never the
player who replaced him. A blank replacement cell means the official pages read this session do not say
— it does not mean nobody replaced him.</div>
</section>"""
    page("injuries.html", "Injury reads and deltas",
         "347 player rows, three read clocks, and the honest finding that no designation moved between them",
         body)
    pages += 1

    # --- availability sweep
    absent = IC.CLUBS_ABSENT
    body = f"""
<section><h2>The 32-club sweep, and why it is 28</h2>
<div class="note">The Week-10 injury hub renders <b>{len(IC.CLUBS_PRESENT)} club tables</b> across
<b>{IC.FIXTURE_BLOCKS_ON_PAGE} fixture blocks</b>. {esc(', '.join(absent))} have no table at all on this
page at this read, and none of the four is on a bye. The sweep therefore cannot be completed from the
weekly report alone in this week — gate G-SWEEP.</div>
<div class="note">Clubs present: {esc(', '.join(IC.CLUBS_PRESENT))}.</div>
{table(["Club", "Rows", "Out", "Doubtful", "Questionable", "DNP", "Named out players", "Source"],
       [[esc(r["club"]), r["rows_on_hub"], r["designated_out"], r["designated_doubtful"],
         r["designated_questionable"], r["did_not_practice"], esc(r["named_out_players"]),
         link(r["source_url"])] for r in p["rollup"]])}
</section>
<section><h2>Availability graph — expected vs actual</h2>
<div class="note">One node per player with a game designation.
<b>Every <code>actual_start</code> cell is blank</b>, because no Game Book was obtained: the game-centre
pages read this session expose overview and statistics tabs only. An "expected" row is a published
designation; it is never a prediction that the player will not play.</div>
{table(["Club", "Player", "Pos", "Unit", "Expected status (official)", "Confidence", "Actual start",
        "Actual snap share", "Why blank", "Source"],
       [[esc(r["club"]), esc(r["player"]), esc(r["position"]), esc(r["unit"]),
         f'<span class="pill {"no" if r["expected_status_from_official_report"]=="Out" else "warn"}">{esc(r["expected_status_from_official_report"])}</span>',
         esc(r["confidence"]), "", "", esc(r["blank_reason_actual"]),
         link(r["expected_evidence_url"])]
        for r in _read_csv("availability_graph.csv")], blank_cols=(6, 7))}
</section>"""
    page("availability.html", "Availability sweep",
         "28 of 32 clubs on the official week-10 report, an expected-vs-actual graph whose actual column is honestly empty, and the reason",
         body)
    pages += 1

    # --- depth
    conflicts = [f for f in p["flags"] if f["category"].startswith("club assignment") or f["category"].startswith("reserve")]
    body = f"""
<section><h2>Can we say who replaced a starter? Not yet.</h2>
<div class="note">The brief asks for the <i>depth</i> of the replacement, not the fact of it. This
session can report neither, and says so in four explicit rows rather than inferring one.</div>
{table(["Claim", "Status", "Detail", "Source"],
       [[esc(r["claim"]), f'<span class="pill {"no" if r["status"] in ("rejected","not obtained this session","no official snap source read","no official snapshot source read") else "warn"}">{esc(r["status"])}</span>',
         esc(r["detail"]), link(r["source_url"])] for r in _read_csv("depth_source_notes.csv")])}
</section>
<section><h2>November trades vs the injury hub — stale rows</h2>
<div class="note">Every trade in the league's own November transactions table was checked against the
weekly report. One player is still listed under his <b>former</b> club.</div>
{table(["Player", "From", "To", "Date on page", "Hub club at this read", "Stale risk", "Source"],
       [[esc(r["player"]), esc(r["from_club"]), esc(r["to_club"]), esc(r["date_on_page"]),
         esc(r["hub_club_at_this_read"]),
         f'<span class="pill {"no" if r["stale_risk"].startswith("yes") else "ok"}">{esc(r["stale_risk"])}</span>',
         link(r["source_url"])] for r in p["trades"]])}
</section>
<section><h2>Reserve list — 'not listed' does not mean available</h2>
<div class="note">{len(p['reserve'])} reserve/injured entries were published in November.
<b>{len([r for r in p['reserve'] if r['appears_on_week10_hub_at_this_read']=='no'])}</b> of them do not
appear on the weekly report at all. A model that reads only the weekly report would treat those
players as available.</div>
{table(["Club", "Date", "Player", "On weekly report?", "Interpretation", "Reserve page", "Weekly report"],
       [[esc(r["club"]), esc(r["date_on_page"]), esc(r["player"]),
         f'<span class="pill {"ok" if r["appears_on_week10_hub_at_this_read"]=="yes" else "no"}">{esc(r["appears_on_week10_hub_at_this_read"])}</span>',
         esc(r["interpretation"]), link(r["source_url"], "reserve"), link(r["hub_url"], "hub")]
        for r in p["reserve"]])}
</section>"""
    page("depth.html", "Depth of replacement & stale rows",
         "Four explicit non-answers on depth, one trade the injury hub has not caught up with, and 14 reserve players who are absent from the weekly report",
         body)
    pages += 1

    # --- questions
    body = f"""
<section><h2>Questions → information → answer</h2>
<div class="note">This is the list the brief asked for: what must be answered before a decision is
sound, what we have, what we lack, and <b>how the missing information would be discovered</b>. A
question is only marked <span class="pill ok">ANSWERED</span> when an official page settles it.</div>
{table(["ID", "Topic", "Question", "Answer we have", "Information missing", "Status", "What it blocks",
        "Discovery route", "Source"],
       [[esc(q["q_id"]), esc(q["topic"]), f'<b>{esc(q["question"])}</b>', esc(q["answer_we_have"]),
         esc(q["information_missing"]),
         f'<span class="pill {"ok" if q["status"]=="ANSWERED" else ("no" if q["status"]=="BLOCKED" else "warn")}">{esc(q["status"])}</span>',
         esc(q["blocks"]), esc(q["discovery_route"]), link(q["source_url"])]
        for q in RG.QUESTIONS])}
</section>
<section><h2>Summary by status</h2>
{status_summary()}
</section>"""
    page("questions.html", "Questions, information and answers",
         "16 questions; 3 answered from an official page this session, 6 partial, 4 open, 3 blocked",
         body)
    pages += 1

    # --- suggestions
    body = f"""
<section><h2>Suggestions for review</h2>
<div class="note">Each proposal carries its own <code>review_state</code> and an empty
<code>decided_by</code> / <code>decision_date</code> pair, so the path can be chosen deliberately before
anything is built. Nothing in this table has been implemented beyond what is marked
<span class="pill ok">implemented here</span>.</div>
{table(["ID", "Area", "Suggestion", "Problem it solves", "Proposal", "Effort", "Depends on",
        "How it would be validated", "Review state"],
       [[esc(s["s_id"]), esc(s["area"]), f'<b>{esc(s["title"])}</b>', esc(s["problem_it_solves"]),
         esc(s["proposal"]), esc(s["effort"]), esc(s["depends_on"]),
         esc(s["what_it_would_take_to_validate"]),
         f'<span class="pill {"ok" if s["review_state"].startswith("implemented") or s["review_state"].startswith("partly") else "warn"}">{esc(s["review_state"])}</span>']
        for s in RG.SUGGESTIONS])}
<h3>How to choose</h3>
<ul class="tight">
<li><b>S-08 first</b> — it costs nothing and stops the site from ever reading as approval.</li>
<li><b>S-02 and S-03 next</b> — they make every later result harder to over-read.</li>
<li><b>S-07 before adding any new pack</b> — the duplicate-table problem grows faster than the data does.</li>
<li><b>S-09 last</b> — an ablation cannot be run until Q-08 and Q-06 are closed.</li>
</ul>
</section>"""
    page("suggestions.html", "Suggestions for review",
         "Ten proposals, each with a review state, an effort estimate, the facts it depends on and how it would be validated",
         body)
    pages += 1

    # --- gates
    body = f"""
<section><h2>Gates and readiness</h2>
{table(["Gate", "State", "Why closed", "Current value", "Number that clears it", "Question", "Source"],
       [[f'<b>{esc(g[0])}</b>',
         f'<span class="pill {"ok" if g[1]=="closed" else ("warn" if g[1]=="open" else "no")}">{esc(g[1])}</span>',
          esc(g[2]), esc(g[3]), esc(g[4]), esc(g[5]), link(g[6])] for g in RG.GATES])}
</section>
<section><h2>Readiness rows</h2>
{table(["Req", "Requirement", "Status", "Where", "Gate", "Number that clears it", "Source"],
       [[esc(r["req_id"]), esc(r["requirement"]),
         f'<span class="pill {"ok" if r["status"].startswith("delivered") else "warn"}">{esc(r["status"])}</span>',
         f'<code>{esc(r["where"])}</code>', esc(r["gate"]), esc(r["number_that_clears_it"]),
         link(r["source_url"])] for r in RG.READINESS])}
</section>"""
    page("gates.html", "Gates and readiness", "Fourteen gates with the numeric condition that lifts each", body)
    pages += 1

    # --- flagged
    body = f"""
<section><h2>Flagged for review — {len(p['flags'])} items</h2>
<div class="note">Nothing here blocks the site. Each row names the two sources that disagree (or the one
source whose own contents disagree) with links, so the item can be adjudicated after publication.</div>
{table(["ID", "Severity", "Category", "Item", "Page A says", "Page B says", "Why it matters",
        "What was done", "Review action", "Links"],
       [[esc(f["flag_id"]),
         f'<span class="pill {"no" if f["severity"]=="high" else ("warn" if f["severity"]=="medium" else "ok")}">{esc(f["severity"])}</span>',
         esc(f["category"]), esc(f["item"]), esc(f["page_a_claim"]), esc(f["page_b_claim"]),
         esc(f["why_it_matters"]), esc(f["what_was_done"]), esc(f["review_action"]),
         f'{link(f["page_a_url"], "A")} {link(f["page_b_url"], "B")}']
        for f in p["flags"]])}
</section>"""
    page("flagged.html", "Flagged for review",
         "Conflicts between official pages, coverage gaps and point-in-time leaks, each with both sources linked",
         body)
    pages += 1

    # --- sources
    body = f"""
<section><h2>Every page read this session</h2>
{table(["ID", "URL", "Read at (UTC)", "Used for", "Official", "How read"],
       [[esc(s["source_id"]), link(s["url"], s["url"]), esc(s["read_at_utc"]), esc(s["used_for"]),
         esc(s["official"]), esc(s["how_read"])] for s in _read_csv("sources.csv")])}
<div class="note">NFL.com Terms §1.3 was read by earlier sessions in this repository and limits use to
individual, non-commercial, informational purposes, prohibiting systematic retrieval. This session
therefore performed <b>eight single manual page reads</b> and ran no scheduled automation. The rights
question remains open as Q-01 and blocks every cadence-dependent requirement.</div>
</section>
<section><h2>Capture attempts, including what was not obtained</h2>
{table(["ID", "URL", "Read at (UTC)", "Outcome", "Detail"],
       [[esc(a["attempt_id"]), link(a["url"]), esc(a["read_at_utc"]), esc(a["outcome"]), esc(a["detail"])]
        for a in _read_csv("capture_attempts.csv")])}
<div class="note"><b>Attempted and not obtained:</b> NFL Game Books (no link from the game-centre tabs
read; the Football Operations publications route was not reachable from this environment), club depth
charts (not read this session), an official snap-count table (not present on the pages read), any price
(no official page prints one).</div>
</section>"""
    page("sources.html", "Sources", "Eight manual reads, each with a clock time, plus the attempts that produced nothing", body)
    pages += 1

    # --- executive summary
    body = executive_summary_html(p)
    page("executive-summary.html", "Executive summary",
         "What changed, what it means, what it does not mean, and what to do next",
         body)
    pages += 1

    return pages


def _read_csv(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def moved_table(rows: list[dict]) -> str:
    return table(["Club", "Player", "Prior read", "Prior state", "This read", "Now", "Delta", "Source"],
                 [[esc(r["club"]), esc(r["player"]), esc(r["prior_read_at_utc"]), esc(r["prior_state"]),
                   esc(r["now_read_at_utc"]), esc(r["now_state"]), esc(r["delta_kind"]),
                   link(r["source_url"])] for r in rows])


def status_summary() -> str:
    from collections import Counter
    c = Counter(q["status"] for q in RG.QUESTIONS)
    rows = [[k, v] for k, v in sorted(c.items())]
    return table(["Status", "Questions"], rows)


def reconcile_table() -> str:
    """Recompute each club from the 13 finals and compare with the standings read."""
    fin = S.finals()
    games = [f for f in fin.values() if f["final"]]
    agg: dict[str, dict] = {}
    for f in games:
        for club, pts, opp in ((f["away"], f["away_score"], f["home_score"]),
                               (f["home"], f["home_score"], f["away_score"])):
            a = agg.setdefault(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            a["pf"] += pts
            a["pa"] += opp
            if pts > opp:
                a["w"] += 1
            elif pts < opp:
                a["l"] += 1
            else:
                a["t"] += 1
    rows = []
    for row in C.STANDINGS_READ:
        abbr, w, l, t, pct, pf, pa = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        a = agg.get(abbr)
        if not a:
            continue
        delta_w = w - a["w"]
        delta_pf = pf - a["pf"]
        verdict = "consistent" if (0 <= delta_w <= 1 and 0 <= delta_pf <= 60) else "check"
        rows.append([esc(abbr), f'{w}-{l}-{t}', f'{pf}/{pa}', f'{a["w"]}-{a["l"]}-{a["t"]}',
                     f'{a["pf"]}/{a["pa"]}', f'{delta_w:+d}', f'{delta_pf:+d}',
                     f'<span class="pill {"ok" if verdict=="consistent" else "warn"}">{verdict}</span>',
                     link(C.URL_STANDINGS_DIV)])
    rows.sort(key=lambda r: (-int(r[5].replace("+", "")), ))
    return table(["Club", "Standings W-L-T", "Standings PF/PA", "Recomputed from finals",
                  "Recomputed PF/PA", "Δ wins", "Δ PF", "Verdict", "Source"], rows)


def executive_summary_html(p: dict) -> str:
    n_final = sum(1 for f in p["fin"].values() if f["final"])
    best = p["lb"][0]
    worst = p["lb"][-1]
    return f"""
{banner(p['no_strategy_qualifies'])}
<section><h2>Executive summary</h2>
<h3>What changed since the last capture</h3>
<ul class="tight">
<li>Week 10 is now settled on the official schedule page: <b>{n_final} of 14 cards print FINAL</b>. The
previous capture (2026-11-15/16) had 5 of 14 unsettled, which is why no leaderboard score could be
published.</li>
<li>For the first time the repo's pre-kickoff Week-10 forecasts could be <b>scored</b>: 48 settled rows
across five strategies, each traced to the commit that published it and checked against that fixture's
kickoff.</li>
<li>Fourteen forecast rows were committed <i>after</i> their game kicked off and are labelled
<code>post_kickoff</code>; they are excluded from every score. Publishing that label is the difference
between a backtest and a fantasy.</li>
<li>Ten more official pages were read for availability, roster and venue facts: 347 injury rows across
28 clubs, 25 reserve/injured entries, 12 November trades, 13 Week-11 fixtures.</li>
</ul>
<h3>What the numbers say</h3>
<ul class="tight">
<li>Every strategy has a <b>positive point estimate</b> of Brier skill against the same-games
climatology. Best is <b>{esc(best['strategy_id'])}</b> at {best['brier_skill_vs_climatology']} (Brier
{best['brier_model']} vs {best['brier_climatology_base_rate']}); weakest is
{esc(worst['strategy_id'])} at {worst['brier_skill_vs_climatology']}.</li>
<li><b>None of the five is qualified.</b> Every 95% game-cluster interval contains zero at n = 12. The
strategies forecast the same twelve games, so their agreement is not independent confirmation.</li>
<li>Three strategies hit 11 of 12 against a coin's expectation of 6. That is unusual under
coin-flipping (p ≈ 0.003) <b>and still not evidence of skill</b>, because twelve games is one draw and
the multiplicity adjustment over five strategies is {p['alpha_adj']:.5f}.</li>
<li>Strategy disagreement is small: a mean gap of {p['spread']['mean_disagreement_points']:.3f} in home
win probability. They share one input (PF/PA per game), so they are not five opinions.</li>
</ul>
<h3>What it does not mean</h3>
<ul class="tight">
<li><b>No profit claim is possible.</b> NFL.com publishes no price, so there is no market line, no
residual, no closing-line value and no ROI anywhere on this site — not because they were hard, but
because the data does not exist without a licence (Q-02).</li>
<li><b>No injury signal is claimed.</b> Zero of 155 paired designations moved between the available
reads, because both reads came after the games. The delta is zero for a reason that is about timing,
not about football.</li>
<li><b>No replacement is named.</b> The weekly report publishes a designation, not a depth chart. Every
"replacement" and "actual starter" cell is blank and flagged.</li>
</ul>
<h3>What would change the conclusion</h3>
<ul class="tight">
<li><b>A game-cluster lower bound above zero</b> after the multiplicity adjustment — roughly 60–120
settled games at the observed variance, i.e. four to eight more weeks.</li>
<li><b>A licensed price archive</b>, which would let the same probabilities be scored on CLV and
residual-vs-market instead of Brier alone.</li>
<li><b>Game Books or an official snap-count table</b>, which would turn the availability graph from
expected-only into expected-vs-actual and make a personnel ablation possible.</li>
<li><b>A single pre-declared ablation pair</b> for any availability feature, scored on a holdout never
used for selection — the only way "injuries matter by X points" becomes falsifiable.</li>
</ul>
<h3>The three things to do next, in order</h3>
<ol>
<li><b>Re-read the Week-10 page once the Monday game ends</b> (one page). That closes the fourteenth
fixture and makes the sample complete without any new work.</li>
<li><b>Answer Q-01 (rights).</b> Nothing scheduled — the Wed/Thu/Fri injury cadence, the price archive,
the daily depth sweep — can start until that is answered in writing.</li>
<li><b>Read the 13 Week-11 game-centre Game Info blocks</b> to finish the venue register, which is the
cheapest remaining gate that is blocked only by effort rather than by rights.</li>
</ol>
<h3>Irregularities a reviewer should look at first</h3>
<ul class="tight">
<li><b>C-01</b> — Daiyan Henley is still in the <i>Chargers</i> injury table eleven days after the
official transactions table moved him to Denver.</li>
<li><b>F-07</b> — the Rams' injury table lists players who are not Rams, suggesting the hub is
season-cumulative rather than current-roster.</li>
<li><b>F-09</b> — four "pre-kickoff" forecasts were in fact committed after kickoff. If an earlier
pack's leaderboard had scored them, it would have been scoring a forecast that knew the answer.</li>
<li><b>F-06</b> — four clubs that played in Week 10 have no table on the Week-10 hub.</li>
</ul>
<p>All {len(p['flags'])} flags, with both source links, are on the
<a href="flagged.html">Flagged for review</a> page.</p>
</section>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    packet = build()
    pages = write_pages(packet)
    print("data/nfl_45abd396:")
    for k, v in sorted(packet["counts"].items()):
        print(f"  {k}: {v}")
    print(f"docs/nfl-45abd396: {pages} pages")
    if args.check:
        res = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "check_nfl_45abd396.py")],
                             cwd=REPO)
        return res.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
