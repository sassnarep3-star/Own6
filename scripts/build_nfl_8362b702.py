#!/usr/bin/env python3
"""Build the nfl_8362b702 pack: CSV tables + a zero-input GitHub Pages site.

Everything published is computed from :mod:`src.nfl_8362b702.capture`, whose
only hand-written content is values read from official pages this session. The
builder takes no arguments and touches no network: a re-run must produce
byte-identical files.

Usage
-----
    python3 scripts/build_nfl_8362b702.py            # write CSVs and HTML
    python3 scripts/build_nfl_8362b702.py --check    # build, then run the verifier
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

from nfl_8362b702 import capture as C  # noqa: E402
from nfl_8362b702 import contracts as K  # noqa: E402
from nfl_8362b702 import controls as CO  # noqa: E402
from nfl_8362b702 import injury as IJ  # noqa: E402
from nfl_8362b702 import availability as AV  # noqa: E402
from nfl_8362b702 import leaderboard as LB  # noqa: E402
from nfl_8362b702 import luck as LK  # noqa: E402
from nfl_8362b702 import mindchange as MC  # noqa: E402
from nfl_8362b702 import model as M  # noqa: E402
from nfl_8362b702 import prereg as PR  # noqa: E402
from nfl_8362b702 import readiness as RD  # noqa: E402
from nfl_8362b702 import registers as RG  # noqa: E402
from nfl_8362b702 import reserve as RS  # noqa: E402
from nfl_8362b702 import results as R  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_8362b702")
DOCS = os.path.join(REPO, "docs", "nfl-8362b702")
OFFICIAL_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com", "github.com")


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url: str, label: str = "source") -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)} &#8599;</a>'


def write_csv(name: str, rows, cols=None, source_url: str = ""):
    os.makedirs(DATA, exist_ok=True)
    if not rows:
        rows = []
    rows = list(rows)
    cols = cols or (list(rows[0].keys()) if rows else ["empty"])
    # rule 2: every row carries a source URL; computed tables get theirs stamped here
    if source_url and not any(c in cols for c in URLCOLS):
        cols = cols + ["source_url"]
        for r in rows:
            r.setdefault("source_url", source_url)
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return path


URLCOLS = ("source_url", "game_page_url", "week_page_url", "url")


NAV = [
    ("index.html", "Decision readiness"),
    ("corpus.html", "136-game corpus"),
    ("results.html", "Results feed"),
    ("standings.html", "Standings + delta"),
    ("prereg.html", "Pre-registration"),
    ("model.html", "Model outputs"),
    ("backtest.html", "Backtest (not leaderboard)"),
    ("controls.html", "Control baselines"),
    ("luck.html", "Removal of luck"),
    ("leaderboard.html", "Leaderboard divisions"),
    ("mindchange.html", "What would change our mind"),
    ("injuries.html", "Injury series + deltas"),
    ("availability.html", "Availability graph"),
    ("reserve.html", "Reserve list"),
    ("venues.html", "Week-11 venues"),
    ("drift.html", "Scraper drift"),
    ("readiness.html", "Full requirements ledger"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]


def page(title: str, body: str, active: str) -> str:
    parts = []
    for u, t in NAV:
        cls = ' class="on"' if u == active else ""
        parts.append(f'<a href="{esc(u)}"{cls}>{esc(t)}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL 8362b702</title>
<style>
 body{{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#12233b;background:#f6f8fb}}
 header{{background:#0b2545;color:#fff;padding:18px 22px}}
 header h1{{margin:0;font-size:20px}} header p{{margin:4px 0 0;opacity:.85;font-size:13px}}
 nav{{display:flex;flex-wrap:wrap;gap:2px;background:#13315c;padding:6px 10px}}
 nav a{{color:#cfe0f5;text-decoration:none;padding:5px 9px;border-radius:4px;font-size:12.5px}}
 nav a.on,nav a:hover{{background:#ee6c4d;color:#fff}}
 main{{max-width:1180px;margin:0 auto;padding:18px}}
 section{{background:#fff;border:1px solid #dfe6f0;border-radius:8px;padding:14px 16px;margin:14px 0}}
 h2{{font-size:17px;margin:4px 0 10px}} h3{{font-size:14.5px;margin:12px 0 6px}}
 table{{border-collapse:collapse;width:100%;font-size:12.5px}}
 th,td{{border:1px solid #e3e9f2;padding:5px 7px;text-align:left;vertical-align:top}}
 th{{background:#eef3fa;position:sticky;top:0}}
 td.blank{{background:#fff7e6}}
 a{{color:#0b5394}} .pill{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px}}
 .ok{{background:#d9f2e2;color:#1c6b3d}} .no{{background:#fde2e2;color:#8f1d1d}}
 .warn{{background:#fff3cd;color:#7a5b00}}
 .note{{background:#f2f6fc;border-left:3px solid #13315c;padding:8px 12px;margin:8px 0;font-size:13px}}
 footer{{text-align:center;color:#7a8aa3;font-size:12px;padding:18px}}
</style></head><body>
<header><h1>NFL Own-Lines Requirements Closure Pack (8362b702)</h1>
<p>Capture date 2026-11-15/16 UTC · every row links an official source · blanks are flagged, never filled · no profitability claim</p></header>
<nav>{nav}</nav>
<main>{body}</main>
<footer>Built from src/nfl_8362b702 (deterministic builder; re-run is byte-identical). Values were read from the cited official pages on 2026-11-15/16 UTC.</footer>
</body></html>
"""


def table(cols, rows, blank_cols=()):
    """cols: list of (key, header). Renders a plain table; URL keys become links.
    Rule 2 also holds on the rendered page: any URL-ish field not shown already
    is appended as an 'Official source' column so every visible row links out."""
    cols = list(cols)
    shown = {k for k, _ in cols}
    for r in rows:
        for c in URLCOLS:
            if c not in shown and r.get(c):
                cols.append((c, "Official source"))
                shown.add(c)
    out = ["<div style='overflow-x:auto'><table><thead><tr>"]
    for _, h in cols:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for k, _ in cols:
            v = r.get(k, "")
            is_url = isinstance(v, str) and v.startswith("http")
            cls = " class='blank'" if (k in blank_cols and not v) else ""
            if is_url:
                cell = link(v)
            else:
                cell = esc(v)
            out.append(f"<td{cls}>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def pill(ok: bool, yes="OK", no="FLAGGED") -> str:
    return f"<span class='pill {'ok' if ok else 'no'}'>{esc(yes if ok else no)}</span>"


def build():
    os.makedirs(DOCS, exist_ok=True)

    # ---------------- data tables ----------------
    corpus = R.corpus_rows()
    w10 = R.week10_finals()
    nonfinal = R.non_final_cards()
    std = R.standings_rows()
    ident = R.standings_identities()
    splits = R.split_identity_checks()
    recon = R.reconcile_corpus_plus_w10()
    corr = R.corpus_identities(corpus)

    write_csv("corpus_136.csv", corpus)
    write_csv("results_week10.csv", w10)
    write_csv("week10_nonfinal.csv", nonfinal)
    write_csv("standings_asof.csv", std, source_url=C.STANDINGS_URL)
    write_csv("standings_split_checks.csv", splits, source_url=C.STANDINGS_URL)
    write_csv("reconciliation.csv", recon, source_url=C.STANDINGS_URL)

    # model outputs + backtest
    wf = M.walk_forward(corpus)
    w11f, fitinfo = M.week11_forecasts()
    out_rows = []
    for f in w11f:
        i = f["inputs"]
        out_rows.append({
            "game_id": f["game_id"], "away": f["away"], "home": f["home"],
            "kickoff_on_card": f.get("kickoff_on_card", ""),
            "p_home_win": round(f["p_home_win"], 6), "p_away_win": round(f["p_away_win"], 6),
            "margin_hat": round(i["margin_hat"], 4),
            "s_home": round(i["s_home"], 4), "s_away": round(i["s_away"], 4),
            "hfa_applied": round(i["hfa_applied"], 4), "sigma": round(i["sigma"], 4),
            "home_g": i["home_g"], "away_g": i["away_g"],
            "home_pf": i["home_pf"], "home_pa": i["home_pa"],
            "away_pf": i["away_pf"], "away_pa": i["away_pa"],
            "neutral_site": "yes" if i["neutral_site"] else "no",
            "market_line": "", "line_difference": "",
            "model_id": M.MODEL_ID,
            "registered_at_utc": PR.REGISTRATION_TIME_UTC,
            "inputs_complete": "yes",
            "game_page_url": f.get("game_page_url", ""),
            "standings_source_url": C.STANDINGS_URL,
            "blank_reason_market": "no official price exists (G-PRICE, FLAG-06)",
        })
    write_csv("model_outputs.csv", out_rows)
    bt_rows = []
    for f in wf:
        i = f["inputs"]
        p = f["p_home_win"]; y = f["outcome_home"]
        brier = (p - y) ** 2
        bt_rows.append({
            "game_id": f["game_id"], "away": f["away"], "home": f["home"],
            "p_home_win": round(p, 6), "outcome_home": y,
            "brier": round(brier, 6),
            "margin_hat": round(i["margin_hat"], 4), "sigma": round(i["sigma"], 4),
            "s_home": round(i["s_home"], 4), "s_away": round(i["s_away"], 4),
            "hfa_applied": round(i["hfa_applied"], 4),
            "window_label": "BACKTEST walk-forward (never on the leaderboard)",
            "week_page_url": f"https://www.nfl.com/schedules/2026/by-week/week-{int(f['game_id'][6:8])}",
        })
    write_csv("backtest_walkforward.csv", bt_rows)

    # controls
    ctrl = []
    w11_urls = {g[0]: g[10] for g in C.WEEK11_GAMES}
    for f in w11f:
        g = {"game_id": f["game_id"], "away": f["away"], "home": f["home"]}
        ctrl.extend(CO.control_rows([g]))
    for r in ctrl:
        r["window_label"] = "week 11 prospective (unsettled)"
        r["source_url"] = w11_urls.get(r["game_id"], "https://www.nfl.com/schedules/2026/by-week/week-11")
    write_csv("control_baselines.csv", ctrl)

    # luck panels
    panel = LK.record_luck_panel()
    write_csv("luck_panel_records.csv", panel, source_url=C.STANDINGS_URL)
    lsum = LK.luck_summary(panel)
    write_csv("luck_summary.csv", [{"metric": k, "value": v} for k, v in lsum.items()], source_url=C.STANDINGS_URL)

    # leaderboard
    write_csv("leaderboard_divisions.csv", LB.division_rows(), source_url="https://github.com/sassnarep3-star/Own6")
    write_csv("leaderboard_strategies.csv", LB.strategy_rows(), source_url="https://github.com/sassnarep3-star/Own6")
    write_csv("leaderboard_gates.csv", LB.gate_rows(), source_url="https://github.com/sassnarep3-star/Own6")
    write_csv("mindchange.csv", MC.rows(), source_url="https://github.com/sassnarep3-star/Own6")

    # injuries / availability / reserve
    write_csv("injury_series.csv", IJ.series_rows())
    write_csv("injury_deltas.csv", IJ.delta_rows())
    write_csv("injury_cross_read.csv", IJ.cross_read_notes())
    nodes = AV.designation_nodes() + AV.roster_nodes()
    write_csv("availability_nodes.csv", nodes)
    write_csv("availability_edges.csv", AV.edges())
    sweep = AV.sweep_rows()
    write_csv("availability_sweep.csv", sweep)
    write_csv("reserve_register.csv", RS.register_rows())
    write_csv("reserve_absence.csv", RS.absence_rows())
    write_csv("reserve_mismatch.csv", RS.mismatch_rows())

    # venues
    vrows = []
    for gid, slug, date, kickoff, network, away, home, ar, hr, mark, url in C.WEEK11_GAMES:
        v = C.VENUE_READS.get(gid)
        vrows.append({
            "game_id": gid, "away": away, "home": home,
            "date_on_card": date, "kickoff_on_card": kickoff,
            "stadium_on_page": v[0] if v else "",
            "location_on_page": v[1] if v else "",
            "event_mark_on_card": mark,
            "read_at_utc": v[2] if v else "",
            "game_page_url": url,
            "blank_reason": "" if v else "game-centre Game Info not yet read for this fixture (gated at the venue row)",
        })
    write_csv("venues_week11.csv", vrows)

    # drift + registers
    write_csv("scraper_contracts.csv", K.drift_rows())
    write_csv("capture_attempts.csv", RG.attempt_rows())
    write_csv("sources.csv", RG.sources_rows())
    write_csv("flagged.csv", RG.flagged_rows())
    write_csv("questions.csv", RG.questions_rows())
    write_csv("suggestions.csv", RG.suggestions_rows(), source_url="https://github.com/sassnarep3-star/Own6")
    write_csv("price_policy.csv", RG.price_policy_rows(), source_url="https://github.com/sassnarep3-star/Own6")
    write_csv("readiness.csv", RD.rows())
    write_csv("prereg.csv", [{"strategy_id": s["strategy_id"], "division": s["division"],
                              "rule_text": s["rule_text"], "window": s["window"],
                              "frozen_before_kickoff": s["frozen_before_kickoff"],
                              "price_dependent": s["price_dependent"],
                              "registration_id": PR.REGISTRATION_ID,
                              "registered_at_utc": PR.REGISTRATION_TIME_UTC,
                              "source_url": "https://github.com/sassnarep3-star/Own6"}
                             for s in PR.STRATEGY_SPECS])

    # ---------------- pages ----------------
    def save(name, title, body):
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
            fh.write(page(title, body, name))

    # index: decision-readiness on the landing page
    ready_cols = [("requirement_id", "ID"), ("requirement", "Requirement"), ("status", "Status"),
                  ("gate_that_blocks_it", "Gate that blocks it"),
                  ("number_that_would_clear_it", "Number that would clear it"),
                  ("source_url", "Source")]
    counts = {}
    for r in RD.rows():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    body = f"""
<section><h2>Decision readiness — one row per requirement</h2>
<div class="note">{esc(lsum['reading'])}</div>
<p>Requirements: <b>{len(RD.rows())}</b> · delivered here <span class="pill ok">{counts.get('delivered_here', 0)}</span>
· delivered by a sibling pack <span class="pill ok">{counts.get('delivered_sibling', 0)}</span>
· open <span class="pill warn">{counts.get('open', 0)}</span>
· blocked <span class="pill no">{counts.get('blocked', 0)}</span>.
The full ledger with implementation locations is on <a href="readiness.html">the requirements page</a>.</p>
{table(ready_cols, RD.rows())}</section>
<section><h2>What this pack adds</h2><ul>
<li><b>Removal-of-luck panel</b> — every record and hit rate is published beside the exact binomial distribution luck alone would produce.</li>
<li><b>Control baselines</b> — a pre-registered seeded coin and a rating-favourite run on every window.</li>
<li><b>Availability graph</b> — expected-vs-actual nodes with evidence levels; nothing is inferred.</li>
<li><b>Injury deltas</b> — timestamped reads; the delta is the signal, never the level.</li>
<li><b>Model-output ledger</b> — probability plus full input vector per game.</li>
<li><b>Drift alarms</b> — per-source contracts; the build fails loudly on drift.</li>
<li><b>Proper-score divisions</b> — singles eligible; combos behind the joint-evidence gate.</li>
</ul></section>"""
    save("index.html", "Decision readiness", body)

    body = ("<section><h2>The 136-game log (weeks 1-9, 2026) — pre-registered backtest corpus</h2>"
            f"<div class='note'>Corpus identities: {corr['games']} games · {corr['decisions']} decisions · "
            f"{corr['tie_games']} tie game · points {corr['points_total']} (PF = PA {pill(corr['pf_equals_pa'])}). "
            f"Standings identities at read: W {ident['sum_w']} = L {ident['sum_l']} "
            f"(= {pill(ident['w_equals_l'])}), T {ident['sum_t']}, PF {ident['sum_pf']} = PA {ident['sum_pa']} "
            f"{pill(ident['pf_equals_pa'])}. Only cards whose own text printed FINAL are results.</div>"
            + table([("game_id", "Game"), ("week", "Wk"), ("date_on_card", "Date on card"),
                     ("away", "Away"), ("away_score", ""), ("home_score", ""), ("home", "Home"),
                     ("margin_home", "Home margin"), ("total", "Total"),
                     ("event_mark_on_card", "Event mark"), ("game_page_url", "Official game page")],
                    corpus) + "</section>")
    save("corpus.html", "136-game corpus", body)

    body = f"""
<section><h2>Week-10 results feed (cards printing FINAL)</h2>
<div class="note">Read {esc(C.WEEK10_SCHED_READ)} from the official week-10 schedule page. Live and
scheduled cards are never results; their on-card strings are kept beside the feed for the record.</div>
{table([("game_id", "Game"), ("date_on_card", "Date"), ("away", "Away"), ("away_score", ""),
        ("home_score", ""), ("home", "Home"), ("event_mark_on_card", "Event mark"),
        ("game_page_url", "Official game page")], w10)}
<h3>Not results (live or scheduled at read time)</h3>
{table([("game_id", "Game"), ("status_on_card", "Status on card"), ("away", "Away"), ("home", "Home"),
        ("score_string_on_card", "Card string (not a result)"), ("game_page_url", "Official game page")], nonfinal)}
<h3>Reconciliation: corpus (W1-9) + week-10 finals vs standings read</h3>
{table([("team_abbr", "Club"), ("verdict", "Verdict"), ("reason", "Reason"),
        ("corpus_plus_w10", "Corpus + W10"), ("standings", "Standings read")], recon)}
<h3>Split identity check (HOME + ROAD must equal W-L-T)</h3>
{table([("team_abbr", "Club"), ("w", "W"), ("l", "L"), ("t", "T"), ("home_rec", "HOME"),
        ("road_rec", "ROAD"), ("home_plus_road_w", "ΣW"), ("home_plus_road_l", "ΣL"),
        ("home_plus_road_t", "ΣT"), ("identity_holds", "Holds"), ("note", "Note")], splits)}
</section>"""
    save("results.html", "Results feed", body)

    body = f"""
<section><h2>Standings as of {esc(C.STANDINGS_READ_1)}</h2>
<div class="note">Two dated reads of the same page are stored; the delta panel below is the
"what changed" view. Clubs with an unfinished week-10 game at read time carry a reason, not a guess.</div>
{table([("team_abbr", "Club"), ("team_name", "Team"), ("w", "W"), ("l", "L"), ("t", "T"),
        ("pct", "PCT"), ("pf", "PF"), ("pa", "PA"), ("net", "NET"), ("strk", "STRK"),
        ("home_rec", "HOME"), ("road_rec", "ROAD"), ("rec_unlabeled_1", "Unlabeled col (verbatim)"),
        ("rec_unlabeled_2", "Unlabeled col (verbatim)")], std)}
<h3>What changed between dated reads</h3>
{"<p>No second read has been taken yet in this build; the delta table fills when read B lands in capture.py.</p>"
 if not os.path.exists(os.path.join(DATA, "standings_delta.csv")) else ""}
</section>"""
    save("standings.html", "Standings + delta", body)

    body = f"""
<section><h2>Pre-registration ({esc(PR.REGISTRATION_ID)})</h2>
<div class="note">Registered {esc(PR.REGISTRATION_TIME_UTC)}, before the first week-11 kickoff
({esc(PR.FIRST_WEEK11_KICKOFF_ET)}). The registration is the commit that first contains
src/nfl_8362b702/prereg.py. Rule text, windows and gates are frozen there.</div>
<h3>Strategy rules (frozen)</h3>
{table([("strategy_id", "Strategy"), ("division", "Division"), ("rule_text", "Rule text (frozen)"),
        ("window", "Window"), ("frozen_before_kickoff", "Frozen before kickoff"),
        ("price_dependent", "Price dependent")],
       [{"strategy_id": s["strategy_id"], "division": s["division"], "rule_text": s["rule_text"],
         "window": s["window"], "frozen_before_kickoff": s["frozen_before_kickoff"],
         "price_dependent": s["price_dependent"]} for s in PR.STRATEGY_SPECS])}
<h3>Gates</h3>{table(
 [("gate_id", "Gate"), ("rule", "Rule"), ("threshold", "Threshold"), ("closes_if", "Closes when")],
 LB.gate_rows())}
<h3>Price-data policy (decided before any backtest is published)</h3>
{table([("policy_id", "ID"), ("rule", "Rule"), ("state", "State")], RG.price_policy_rows())}
</section>"""
    save("prereg.html", "Pre-registration", body)

    body = f"""
<section><h2>Model outputs — probability plus its full input vector</h2>
<div class="note">Model {esc(M.MODEL_ID)}: {esc(M.SPEC_TEXT)} Fit parameters at registration:
HFA = {fitinfo['hfa']:.4f} pts (n={fitinfo['hfa_n']} non-neutral corpus games),
sigma = {fitinfo['sigma']:.4f}. Market line and difference columns exist and are blank
({esc('G-PRICE, FLAG-06')}).</div>
{table([("game_id", "Game"), ("kickoff_on_card", "Kickoff"), ("away", "Away"), ("home", "Home"),
        ("p_home_win", "P(home win)"), ("p_away_win", "P(away win)"), ("margin_hat", "Fair margin (home)"),
        ("s_home", "S home"), ("s_away", "S away"), ("hfa_applied", "HFA used"), ("sigma", "Sigma"),
        ("home_g", "Home G"), ("away_g", "Away G"), ("neutral_site", "Neutral"),
        ("market_line", "Market line"), ("line_difference", "Difference"),
        ("game_page_url", "Official game page")], out_rows, blank_cols=("market_line", "line_difference"))}
</section>"""
    save("model.html", "Model outputs", body)

    base = sum((f["p_home_win"] - f["outcome_home"]) ** 2 for f in wf) / len(wf)
    body = f"""
<section><h2>Backtest — walk-forward over the corpus (NEVER on the leaderboard)</h2>
<div class="note">Rolling re-fit: week k forecast from ratings fit on weeks &lt; k
(week 1 has no prior data and is skipped). {len(wf)} forecast rows, mean Brier
{base:.4f}. G-BACKTEST: none of these numbers may appear on the leaderboard page.</div>
{table([("game_id", "Game"), ("p_home_win", "P(home win)"), ("outcome_home", "Outcome (home)"),
        ("brier", "Brier"), ("margin_hat", "Margin hat"), ("sigma", "Sigma"),
        ("window_label", "Window label"), ("week_page_url", "Official week page")], bt_rows)}
</section>"""
    save("backtest.html", "Backtest", body)

    body = f"""
<section><h2>Control baselines (week-11 window, pre-registered)</h2>
<div class="note">S8362-RANDOM is a deterministic seeded coin (seed {esc(CO.RANDOM_SEED_HEX)});
S8362-FAVORITE picks the rating favourite from the corpus. A market-favourite control is
impossible without licensed prices and is not approximated. Both controls run on exactly the
same games as the strategies they police.</div>
{table([("control_id", "Control"), ("game_id", "Game"), ("pick", "Pick"),
        ("input_vector", "Input vector (frozen)"), ("model_id", "Model"),
        ("source_url", "Source")], ctrl)}
</section>"""
    save("controls.html", "Control baselines", body)

    body = f"""
<section><h2>Removal-of-luck panel</h2>
<div class="note">{esc(lsum['reading'])}</div>
{table([("team_abbr", "Club"), ("games", "G"), ("decided", "Decided"), ("ties", "Ties"),
        ("wins", "W"), ("luck_expected_wins", "Luck E[W]"), ("luck_sd", "Luck sd"),
        ("luck_band_95_low", "95% low"), ("luck_band_95_high", "95% high"),
        ("wins_minus_luck", "W − luck"), ("z_vs_coin", "z vs coin"),
        ("two_sided_binomial_p", "Exact p"), ("wilson_95_low", "Wilson low"),
        ("wilson_95_high", "Wilson high"), ("outside_95_luck_band", "Outside 95% band")], panel)}
</section>"""
    save("luck.html", "Removal of luck", body)

    body = f"""
<section><h2>Leaderboard — proper-score divisions</h2>
<div class="note">Ranking statistic (once settled): Brier skill vs each event's own base rate,
with a game-cluster lower bound and a multiplicity note for the number of trials. At
registration no forecast in the evaluation window is settled, so every score cell is blank
with the gate that will fill it. Backtest numbers are forbidden here (G-BACKTEST).</div>
<h3>Divisions</h3>
{table([("division", "Division"), ("eligible_for_ranking", "Eligible"), ("joint_evidence_gate", "Gate"),
        ("n_registered_strategies", "Strategies"), ("n_settled", "Settled"),
        ("brier_skill", "Brier skill"), ("blocked_reason", "Blocked because"),
        ("blank_reason", "Blank because")], LB.division_rows(),
       blank_cols=("brier_skill",))}
<h3>Strategies</h3>
{table([("strategy_id", "Strategy"), ("division", "Division"), ("registered", "Registered"),
        ("registered_before_kickoff", "Before kickoff"), ("leaderboard_eligible", "Eligible"),
        ("n_forecasts_registered", "Forecasts"), ("n_settled", "Settled"),
        ("brier", "Brier"), ("brier_skill_vs_base", "Brier skill"),
        ("cluster_lower_bound", "Cluster LB"), ("rank", "Rank"),
        ("blank_or_blocked_reason", "Reason")], LB.strategy_rows(),
       blank_cols=("brier", "brier_skill_vs_base", "cluster_lower_bound", "rank"))}
<h3>Gates</h3>
{table([("gate_id", "Gate"), ("rule", "Rule"), ("threshold", "Threshold"), ("closes_if", "Closes when")],
       LB.gate_rows())}
</section>"""
    save("leaderboard.html", "Leaderboard divisions", body)

    body = ("<section><h2>What would change our mind (two-sided, frozen at registration)</h2>"
            + table([("strategy_id", "Strategy"), ("would_change_our_mind_for", "Would change our mind FOR"),
                     ("threshold_for", "Threshold (for)"),
                     ("would_change_our_mind_against", "Would change our mind AGAINST"),
                     ("threshold_against", "Threshold (against)"),
                     ("state_at_registration", "State at registration")], MC.rows())
            + "</section>")
    save("mindchange.html", "What would change our mind", body)

    dr = IJ.delta_rows()
    body = f"""
<section><h2>Injury hub — timestamped series, deltas, never levels</h2>
<div class="note">Read A: {esc(IJ.INJURY_READ_A)} ({esc(IJ.INJURY_READ_A_WINDOW)}).
Rows carry their read clock; the published signal is the delta between reads.
{esc("Read B lands in a later build of this same page when capture.INJURY_ROWS_B exists.")}</div>
<h3>Series (read A{'+ B' if dr else ''})</h3>
{table([("hub_game_id", "Slot"), ("club", "Club"), ("player", "Player"), ("position", "Pos"),
        ("injury_text", "Injury text"), ("practice_status", "Practice"), ("game_status", "Game status"),
        ("read_at_utc", "Read at (UTC)"), ("source_url", "Source")], IJ.series_rows(),
       blank_cols=("game_status",))}
<h3>Cross-read deltas on the record</h3>
{table([("item", "Item"), ("earlier_state", "Earlier state"), ("state_at_read_a_2026-11-15T23:58Z", "State at read A"),
        ("delta_kind", "Delta"), ("note", "Note"), ("source_url", "Source")], IJ.cross_read_notes())}
</section>"""
    save("injuries.html", "Injury series + deltas", body)

    body = f"""
<section><h2>Availability graph — expected vs actual, evidence per node</h2>
<div class="note">Depth order is never derived from jersey number, experience or salary.
actual_start cells are blank everywhere: the brief's Game Books were not reachable (G-GAMEBOOK,
FLAG-07). A blank is published as unknown, never as 'no deficiency'.</div>
<h3>Sweep status (32 clubs)</h3>
{table([("club", "Club"), ("hub_table_read", "Hub table"), ("roster_page_read", "Roster page"),
        ("sweep_complete", "Sweep complete"), ("blocking_gate", "Blocking gate"),
        ("number_that_would_clear", "Number that clears"), ("source_url", "Source")], sweep)}
<h3>Nodes ({len(nodes)})</h3>
{table([("node_id", "Node"), ("player", "Player"), ("club", "Club"), ("position", "Pos"),
        ("game_slot", "Slot"), ("game_status_at_read_a", "Game status"), ("expected_to_start", "Expected"),
        ("actual_start", "Actual"), ("replacement_named", "Replacement"), ("evidence_level", "Evidence"),
        ("source_url", "Source")], nodes, blank_cols=("expected_to_start", "actual_start", "replacement_named"))}
<h3>Edges ({len(AV.edges())})</h3>
{table([("edge_id", "Edge"), ("from_node", "From node"), ("to_slot", "To slot"), ("edge_type", "Type"),
        ("replacement_named", "Replacement"), ("actual_start_evidence", "Actual-start evidence"),
        ("note", "Note"), ("source_url", "Source")], AV.edges(),
       blank_cols=("replacement_named", "actual_start_evidence"))}
</section>"""
    save("availability.html", "Availability graph", body)

    body = f"""
<section><h2>Reserve list — "not listed" never means "available"</h2>
<div class="note">{esc(C.GB_ROSTER_STATUS_NOTE)}</div>
<h3>Non-active roster rows (GB, read {esc(C.GB_ROSTER_READ)})</h3>
{table([("player_display_name", "Display name"), ("player_url_slug", "URL slug"),
        ("jersey_on_page", "Jersey"), ("position_on_page", "Pos"),
        ("status_code_on_page", "Status code"), ("reserve_section", "Reserve section"),
        ("read_at_utc", "Read at"), ("source_url", "Source")], RS.register_rows())}
<h3>Absences (first-class rows)</h3>
{table([("player", "Player"), ("club", "Club"), ("state_on_page", "State on page"),
        ("other_qbs_on_page", "Other QBs on page"), ("interpretation", "Interpretation"),
        ("source_url", "Source")], RS.absence_rows())}
<h3>Name/slug conflicts</h3>
{table([("display_name_on_page", "Display name"), ("url_slug_on_page", "URL slug"),
        ("row_on_page", "Row"), ("issue", "Issue"), ("source_url", "Source")], RS.mismatch_rows())}
</section>"""
    save("reserve.html", "Reserve list", body)

    body = ("<section><h2>Week-11 venues — transcribed from the official game centre</h2>"
            "<div class='note'>Venue strings come from each fixture's own game-centre Game Info "
            "block. Ticketing and hotel links are never used as venue evidence. Fixtures without "
            "a game-centre read keep a blank venue and a gate.</div>"
            + table([("game_id", "Game"), ("date_on_card", "Date"), ("kickoff_on_card", "Kickoff"),
                     ("away", "Away"), ("home", "Home"), ("stadium_on_page", "Stadium on page"),
                     ("location_on_page", "Location on page"), ("event_mark_on_card", "Event mark"),
                     ("read_at_utc", "Read at"), ("game_page_url", "Official game centre"),
                     ("blank_reason", "Blank reason")], vrows,
                    blank_cols=("stadium_on_page",)) + "</section>")
    save("venues.html", "Week-11 venues", body)

    body = f"""
<section><h2>Scraper contracts and drift alarms</h2>
<div class="note">Every source is pinned to an expected row count and required fields. The
verifier fails the build on any drift — a missing field never ships as a blank.</div>
{table([("source_id", "Source"), ("url", "URL"), ("read_at_utc", "Read at"),
        ("row_unit", "Row unit"), ("expected_rows", "Expected"), ("observed_rows", "Observed"),
        ("required_fields", "Required fields"), ("verdict", "Verdict"), ("drift_detail", "Drift")],
       K.drift_rows())}
<h3>Capture attempts (negative results are data)</h3>
{table([("read_at_utc", "Read at"), ("url", "URL"), ("intent", "Intent"), ("outcome", "Outcome"),
        ("note", "Note")], RG.attempt_rows())}
</section>"""
    save("drift.html", "Scraper drift", body)

    body = ("<section><h2>Full requirements ledger</h2>"
            + table(ready_cols, RD.rows()) + "</section>")
    save("readiness.html", "Requirements ledger", body)

    body = ("<section><h2>Questions — what we have, what we lack, how to find it</h2>"
            + table([("question_id", "ID"), ("topic", "Topic"), ("question", "Question"),
                     ("what_we_have", "What we have"), ("what_we_lack", "What we lack"),
                     ("status", "Status"), ("discovery_route", "Discovery route"),
                     ("source_url", "Source")], RG.questions_rows()) + "</section>")
    save("questions.html", "Questions", body)

    body = ("<section><h2>Suggestions — review and choose a path before anything is built</h2>"
            "<div class='note'>Nothing on this page has been implemented. Each row is waiting for "
            "a human choice.</div>"
            + table([("suggestion_id", "ID"), ("area", "Area"), ("suggestion", "Suggestion"),
                     ("reasoning", "Reasoning"), ("priority", "Priority"), ("effort", "Effort"),
                     ("cost_or_risk", "Cost / risk"), ("state", "State"),
                     ("implementation", "Implementation")], RG.suggestions_rows()) + "</section>")
    save("suggestions.html", "Suggestions", body)

    body = ("<section><h2>Flagged for review</h2>"
            "<div class='note'>Flagged items do not block anything. They are published with their "
            "source links so a human can review them after the site is live.</div>"
            + table([("flag_id", "ID"), ("severity", "Severity"), ("category", "Category"),
                     ("issue", "Issue"), ("what_was_done", "What was done"),
                     ("remediation", "Remediation"), ("source_url", "Source")], RG.flagged_rows())
            + "</section>")
    save("flagged.html", "Flagged for review", body)

    body = ("<section><h2>Sources — every read, its clock, and what was taken from it</h2>"
            + table([("source_id", "ID"), ("title", "Title"), ("url", "Official page"),
                     ("read_on_utc", "Read on (UTC)"), ("what_was_read", "What was read")],
                    RG.sources_rows()) + "</section>")
    save("sources.html", "Sources", body)

    body = f"""
<section><h2>Executive summary</h2>
<div class="note">This pack closes the eight brief requirements that no merged sibling pack had
built: the removal-of-luck panel, control baselines, the availability graph as a first-class
dataset, injury deltas (surprise, not level), the model-output probability+inputs ledger,
scraper drift alarms, proper-score leaderboard divisions with the joint-evidence gate, and the
two-sided what-would-change-our-mind field. It also turns the 136-game log into the
pre-registered backtest corpus and resolves two brief data items at the source (the three Lions
game-status designations now publish as Out; the reserve list is captured so 'not listed' never
means available).</div>
<h3>The numbers a reviewer can re-check in one line each</h3>
<ul>
<li>Corpus: 136 games, 135 decisions + 1 tie, points 6246 = 6246 (weeks 1-9 FINAL cards).</li>
<li>Standings read: sum W = {ident['sum_w']} = sum L, sum PF = {ident['sum_pf']} = sum PA.</li>
<li>Reconciliation: corpus + week-10 finals reproduce the standings read for every club with no
unfinished week-10 card ({sum(1 for r in recon if r['verdict'] == 'match')} matches,
{sum(1 for r in recon if r['verdict'] == 'MISMATCH')} mismatches).</li>
<li>HFA = {fitinfo['hfa']:.3f} pts (mean home margin, {fitinfo['hfa_n']} non-neutral corpus games);
sigma = {fitinfo['sigma']:.3f}.</li>
<li>Luck panel: {lsum['outside_95_luck_band']} of {lsum['clubs']} club records sit outside the
95% binomial luck band (max |z| {lsum['max_abs_z']}).</li>
<li>Drift alarms: {sum(1 for r in K.drift_rows() if r['verdict'] == 'OK')} of {len(K.drift_rows())}
source contracts OK at build time.</li>
</ul>
<h3>What is deliberately blank</h3>
<ul>
<li>Every market/price/CLV/ROI cell (G-PRICE: no official price exists — FLAG-06).</li>
<li>Every actual-start and replacement-named cell (G-GAMEBOOK — FLAG-07).</li>
<li>Every leaderboard proper score (G-SETTLE: the window has not kicked off).</li>
</ul>
<h3>Irregularities</h3>
<p>See <a href="flagged.html">Flagged for Review</a>: the MIN home/road split inconsistency
(FLAG-01), the Malik Willis unknown roster state (FLAG-03), the name/slug conflict (FLAG-04),
the week-1 date oddity (FLAG-05), and the NFL Terms §1.3 rights boundary (FLAG-02).</p>
</section>"""
    save("executive-summary.html", "Executive summary", body)

    return len(corpus), len(w10), len(w11f), len(wf)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    c, w, f, b = build()
    print(f"built: corpus {c}, week-10 finals {w}, forecasts {f}, backtest rows {b}")
    if args.check:
        sys.exit(subprocess.call([sys.executable,
                                  os.path.join(REPO, "scripts", "check_nfl_8362b702.py")]))
