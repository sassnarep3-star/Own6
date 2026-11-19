#!/usr/bin/env python3
"""Build docs/nfl-d713b52f/** from the committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_d713b52f.py
    python3 scripts/build_nfl_d713b52f.py --check     # build then run the verifier

Design rules held by every page:
  * one table or one list per section, no decorative filler
  * every published value carries its official source link
  * a cell that no official page supports is blank and the page says why
  * no form control anywhere (no input, select, textarea, button)
"""
from __future__ import annotations

import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_d713b52f")
DOCS = os.path.join(REPO, "docs", "nfl-d713b52f")

PAGES = [
    ("index.html", "Readiness", "Decision readiness: one row per brief bullet"),
    ("evidence.html", "Evidence", "What was read, and what it says"),
    ("model.html", "Model", "Frozen baseline, proper scores, Week 11 forecasts"),
    ("availability.html", "Availability", "Declared out, not active, and what they played"),
    ("questions.html", "Questions", "What must be answered before a decision"),
    ("suggestions.html", "Suggestions", "Proposals, decisions left to the owner"),
    ("flagged.html", "Flagged", "Irregularities, with the official link"),
]

CSS = """
:root{--ink:#14212b;--muted:#5c6f7e;--navy:#0d2231;--teal:#0a7a72;--line:#d7e0e6;--paper:#f4f7f8;
--white:#fff;--warn:#fff5dc;--warnink:#7a4900;--ok:#0a684c;--bad:#98292a;--soft:#ecf3f4}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.55;
font:15px/1.55 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--teal);text-underline-offset:.16em}
header{background:var(--navy);color:#fff}
.wrap{width:min(1240px,calc(100% - 2rem));margin:0 auto}
.top{display:flex;flex-wrap:wrap;gap:.5rem 1.2rem;align-items:baseline;padding:.9rem 0 .3rem}
.top b{letter-spacing:.05em;font-size:.98rem}
.top span{color:#9fc7c2;font-size:.76rem;letter-spacing:.09em;text-transform:uppercase}
nav{display:flex;flex-wrap:wrap;gap:.2rem 1rem;padding:.2rem 0 .7rem}
nav a{color:#cfe3e0;text-decoration:none;font-size:.85rem;padding:.12rem 0;border-bottom:2px solid transparent}
nav a:hover{border-bottom-color:#7fd3c6}
nav a.on{color:#fff;border-bottom-color:#7fd3c6;font-weight:600}
main{padding:1.3rem 0 3rem}
h1{font-size:1.45rem;margin:.2rem 0 .35rem}
h2{font-size:1.08rem;margin:1.8rem 0 .5rem;padding-bottom:.28rem;border-bottom:1px solid var(--line)}
h3{font-size:.96rem;margin:1.1rem 0 .3rem}
p{max-width:80ch}
.lead{color:var(--muted);max-width:84ch}
.cards{display:grid;gap:.65rem;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));margin:.9rem 0 .3rem}
.card{background:var(--white);border:1px solid var(--line);border-radius:9px;padding:.7rem .85rem}
.card .k{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.card .v{font-size:1.5rem;font-weight:700;line-height:1.15;margin-top:.12rem}
.card .s{font-size:.76rem;color:var(--muted)}
.tw{overflow-x:auto;background:var(--white);border:1px solid var(--line);border-radius:9px;margin:.55rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.83rem}
th,td{padding:.4rem .55rem;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--soft);font-size:.71rem;letter-spacing:.04em;text-transform:uppercase;color:#37505e;
position:sticky;top:0;white-space:nowrap}
tbody tr:hover{background:#fbfdfd}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:.04rem .4rem;border-radius:999px;font-size:.7rem;font-weight:600;white-space:nowrap}
.pill.ok{background:#dcf2ea;color:var(--ok)}
.pill.warn{background:var(--warn);color:var(--warnink)}
.pill.bad{background:#fae4e4;color:var(--bad)}
.pill.info{background:#e6eef4;color:#2f556e}
.pill.paper{background:#eef0f2;color:#4a5b66}
.note{background:var(--white);border-left:3px solid var(--teal);padding:.55rem .8rem;margin:.6rem 0 1rem;
border-radius:0 7px 7px 0;font-size:.87rem;color:#31434f}
.note.warn{border-left-color:#c98a00;background:var(--warn)}
.note.bad{border-left-color:var(--bad);background:#fdf0f0}
.small{font-size:.78rem;color:var(--muted)}
footer{border-top:1px solid var(--line);padding:1.1rem 0 2rem;color:var(--muted);font-size:.78rem}
code{background:#eef2f4;padding:.05rem .28rem;border-radius:4px;font-size:.86em}
.blank{color:#9aaab4}
"""


def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def read(name):
    path = os.path.join(DATA, name)
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def link(url, text=None):
    if not url:
        return '<span class="blank">no source</span>'
    label = text or host_label(url)
    return f'<a href="{esc(url)}" rel="noreferrer" target="_blank">{esc(label)}</a>'


def host_label(url):
    if "static.www.nfl.com" in url and url.endswith(".pdf"):
        return "Game Book (PDF)"
    if "/games/" in url:
        return "game centre"
    if "/injuries" in url:
        return "injury report"
    if "/standings" in url:
        return "standings"
    if "/schedules" in url:
        return "schedule"
    if "/stats/" in url:
        return "stats"
    return url.split("/")[2]


def pill(text, kind="info"):
    return f'<span class="pill {kind}">{esc(text)}</span>'


def status_pill(status):
    kind = {"done": "ok", "partial": "warn", "blocked": "bad"}.get(status, "info")
    return pill(status, kind)


def table(headers, rows, numeric=(), cls=""):
    out = [f'<div class="tw"><table class="{cls}">', "<thead><tr>"]
    for i, h in enumerate(headers):
        c = ' class="n"' if h in numeric else ""
        out.append(f"<th{c}>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        names = headers
        for h, v in zip(names, r):
            c = ' class="n"' if h in numeric else ""
            out.append(f"<td{c}>{v}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def shell(page, title, subtitle, body):
    nav = []
    for href, label, _ in PAGES:
        cls = ' class="on"' if href == page else ""
        nav.append(f'<a href="{href}"{cls}>{esc(label)}</a>')
    nav.append('<a href="../index.html">All packs</a>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL decision desk (d713b52f)</title>
<style>{CSS}</style></head>
<body>
<header><div class="wrap">
<div class="top"><b>NFL DECISION DESK</b><span>session d713b52f · read 2026-11-19 UTC · official sources only</span></div>
<nav>{''.join(nav)}</nav>
</div></header>
<main><div class="wrap">
<h1>{esc(title)}</h1>
<p class="lead">{subtitle}</p>
{body}
</div></main>
<footer><div class="wrap">
Every value on this page was read from the official NFL page linked beside it on 2026-11-19 UTC, or is
arithmetic on such values with the derivation shown. No market price exists on any official page, so price, ROI and
CLV columns are blank by policy. No profitability claim is made anywhere. Blank is not zero and blank is not healthy.
</div></footer>
</body></html>
"""


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def page_index():
    reqs = read("requirements.csv")
    flags = read("flagged.csv")
    bt = read("backtest_summary.csv")[0]
    lk = read("luck_panel.csv")[0]
    rs = read("recompute_summary.csv")[0]
    qs = read("questions.csv")
    sug = read("suggestions.csv")
    pr = read("source_probe.csv")

    done = sum(1 for r in reqs if r["status"] == "done")
    partial = sum(1 for r in reqs if r["status"] == "partial")
    blocked = sum(1 for r in reqs if r["status"] == "blocked")

    cards = f"""<div class="cards">
<div class="card"><div class="k">Brief bullets traced</div><div class="v">{len(reqs)}</div>
<div class="s">{done} done · {partial} partial · {blocked} blocked</div></div>
<div class="card"><div class="k">Official pages read</div><div class="v">11</div>
<div class="s">4 game books · 2 injury reports · schedule · standings · 3 probes</div></div>
<div class="card"><div class="k">Prospective singles scored</div><div class="v">0</div>
<div class="s">nothing can be promoted on a backtest</div></div>
<div class="card"><div class="k">Corpus reconciliation</div><div class="v">150</div>
<div class="s">{esc(bt['reconciliation'])}</div></div>
<div class="card"><div class="k">Frozen model BSS</div><div class="v">{float(bt['bss']):+.3f}</div>
<div class="s">week-cluster 95% lower bound {float(bt['bss_lo_week_cluster']):+.3f}</div></div>
<div class="card"><div class="k">Inherited numbers re-computed</div><div class="v">{rs['checks']}</div>
<div class="s">{rs['match']} match · {rs['mismatch']} mismatch · {rs['info']} info</div></div>
<div class="card"><div class="k">Open irregularities</div><div class="v">{len(flags)}</div>
<div class="s">all linked to the official page · none blocks the merge</div></div>
<div class="card"><div class="k">Open questions</div><div class="v">{len(qs)}</div>
<div class="s">each with the route to answer it</div></div>
<div class="card"><div class="k">Suggestions awaiting a decision</div><div class="v">{len(sug)}</div>
<div class="s">decision field left empty for the owner</div></div>
</div>"""

    head = f"""<div class="note"><b>The one-line answer to "can we bet this yet".</b> No. The frozen model's
best backtest skill is {float(bt['bss']):+.3f} with a 95% week-cluster interval of
{float(bt['bss_lo_week_cluster']):+.3f} to {float(bt['bss_hi_week_cluster']):+.3f} — it includes zero, so the model
cannot be told apart from guessing the base rate. Of the 150-game corpus it could honestly score {esc(bt['n'])}; the
other {esc(bt['refused'])} would have needed a same-week number and are published as refused, not dropped. On top of that no official page publishes a price, so no
residual, ROI or CLV can be computed at all. The pack therefore publishes what it can prove and blanks the rest.</div>
<div class="note warn"><b>The one-line answer to "can we measure replacement depth yet".</b> Partly, and better than
before. The route that every earlier pack recorded as blocked — the official Game Book PDF, reachable or not — is
reachable from this session. Four books were read end to end: <b>176 named starters</b>, <b>50 Not Active entries</b>,
and the NFL's own playtime table. That table is captioned <code>(Unofficial)</code> by the NFL, so every snap value
here is labelled Unofficial and none is called certified.</div>"""

    rows = []
    for r in reqs:
        rows.append([
            esc(r["rid"]),
            esc(r["group"]),
            esc(r["requirement"]),
            esc(r["what_exists"]),
            f'<code>{esc(r["gate"])}</code>',
            esc(r["clears_it"]),
            status_pill(r["status"]),
        ])
    req_table = table(["ID", "Group", "Requirement (owner's words)", "What exists in the repo today",
                       "Blocking gate", "The number that would clear it", "State"], rows)

    probe_rows = [[esc(p["probe_id"]), esc(p["question"]), esc(p["answer"]),
                   esc(p["caveat"]), link(_probe_url(p))] for p in pr]
    probe_table = table(["ID", "Question", "Dated answer", "Caveat that travels with the answer", "Source"],
                        probe_rows)

    body = f"""{cards}
{head}
<h2>Decision readiness — one row per bullet of the owner's brief</h2>
<p class="lead">86 rows. Each row states what exists, which gate blocks a decision, and the number that would clear
it. Status is <b>done</b> (the deliverable exists and is enforced), <b>partial</b> (a measured start with less coverage
than the brief asks for) or <b>blocked</b> (a required input is missing and nothing can substitute for it).</p>
{req_table}
<h2>What the source probe found on 2026-11-19</h2>
<p class="lead">The brief depends on sources whose existence was previously assumed. These are the dated answers,
each with the page that produced it.</p>
{probe_table}
"""
    return shell("index.html", "Decision readiness", "One row per brief bullet, with the gate that blocks it and the number that would clear it. Everything else on this site is the evidence behind these rows.", body)


def _probe_url(p):
    raw = p["raw"]
    if "cap10" in raw:
        return "https://www.nfl.com/stats/player-stats/"
    if "cap09" in raw:
        return "https://www.nfl.com/injuries/league/2026/reg10"
    if "cap05" in raw:
        return "https://static.www.nfl.com/image/upload/v1794916121/gamecenter/ab78ad5a-4feb-11f1-abca-2c54536568a9.pdf"
    return "https://www.nfl.com/injuries/"


def page_evidence():
    caps = read("capture_log.csv")
    fx = read("fixtures.csv")
    st = read("standings.csv")
    rs = read("recompute_summary.csv")[0]
    rc = read("recompute.csv")
    im = read("implementation_comparison.csv")[0]
    diff = read("diff.csv")
    srcs = read("sources.csv")
    ffeat = read("fixture_features.csv")

    cap_rows = []
    for c in caps:
        cap_rows.append([
            f'<code>{esc(c["capture_id"])}</code>',
            esc(c["kind"]),
            link(c["source_url"]),
            esc(c["read_at_utc"]),
            f'<code title="{esc(c["sha256"])}">{esc(c["sha256"][:16])}…</code>',
            esc(c["bytes"]),
            esc(c["used_for"]),
        ])
    cap_table = table(["Capture", "Kind", "Official page", "Read at UTC", "sha256 (transcript)",
                       "Bytes", "Used for"], cap_rows)

    fx_rows = [[esc(f["game_id"]), esc(f["date"]), esc(f["kickoff_et"]), esc(f["away"]), esc(f["home"]),
                f'{esc(f["away_score"])}–{esc(f["home_score"])}', esc(f["venue_game_book"]),
                esc(f["venue_game_centre"]), pill(f["venue_match"], "ok" if f["venue_match"] == "exact" else "warn"),
                esc(f["roof_surface"]), esc(f["weather"]), esc(f["temp_f"]), esc(f["wind"]),
                esc(f["referee"]), link(f["source_url"])] for f in fx]
    fx_table = table(["Game", "Date", "Kickoff ET", "Away", "Home", "Score", "Venue (book)",
                      "Venue (game centre)", "Match", "Roof & surface", "Weather", "Temp °F",
                      "Wind", "Referee", "Source"], fx_rows)

    st_rows = [[esc(s["club"]), esc(s["division"]), esc(s["w"]), esc(s["l"]), esc(s["t"]), esc(s["pct"]),
                esc(s["pf"]), esc(s["pa"]), esc(s["net_pts"]), link(s["source_url"])]
               for s in sorted(st, key=lambda r: (r["division"], -int(r["w"])))]
    st_table = table(["Club", "Division", "W", "L", "T", "PCT", "PF", "PA", "Net", "Source"],
                     st_rows, numeric=("W", "L", "T", "PCT", "PF", "PA", "Net"))

    rc_rows = [[f'<code>{esc(r["check_id"])}</code>', esc(r["quantity"]), esc(r["published"]),
                esc(r["recomputed"]), esc(r["n"]),
                pill(r["verdict"], "ok" if r["verdict"].startswith("MATCH") else ("bad" if r["verdict"] == "MISMATCH" else "info"))]
               for r in rc]
    rc_table = table(["Check", "Quantity", "As published by the inherited pack", "Recomputed here",
                      "n", "Verdict"], rc_rows, numeric=("n",))

    df_rows = [[esc(d["entity"]), esc(d["key"]), esc(d["before"]), esc(d["after"]),
                pill(d["changed"], "warn" if d["changed"] not in ("no", "0") else "ok"), esc(d["note"])]
               for d in diff if d["entity"] == "standings"]
    df_table = table(["Entity", "Club", "Before (2026-11-19 inherited read)", "Now (this read)",
                      "Changed", "Detail"], df_rows)

    ff_rows = [[esc(f["feature"]), pill(f["available"], "ok" if f["available"] == "yes" else "bad"),
                esc(f["n_games_read"]), esc(f["detail"]), esc(f["blocker"]), link(f["source_url"])]
               for f in ffeat]
    ff_table = table(["Fixture-context feature", "Available", "Coverage", "What was read",
                      "What blocks it", "Source"], ff_rows)

    src_rows = [[f'<code>{esc(s["source_id"])}</code>', link(s["url"]), esc(s["host"]),
                 esc(s["kind"]), esc(s["used_for"]), esc(s["read_at_utc"])] for s in srcs]
    src_table = table(["ID", "URL", "Host", "Kind", "Used for", "Read at UTC"], src_rows)

    body = f"""
<div class="note warn"><b>What the hash proves, and what it does not.</b> The sha256 in the capture log is taken over
the committed <i>transcription</i> of each page, not over the remote response bytes. It proves the transcription has
not changed since it was written; it does not prove the NFL served those bytes. The URL and the UTC clock are on every
row so a reader can re-read the page and compare. Stating this plainly is cheaper than pretending a hash is a witness.</div>
<h2>Capture log — 11 official reads, 2026-11-19 UTC</h2>
{cap_table}
<h2>The four games read end to end</h2>
<p class="lead">Only games whose <b>official Game Book</b> was read are published here. The book is the NFL's own
settlement record: it names the line-up that started, the players who did not dress, and the playtime table.</p>
{fx_table}
<h2>Independent re-computation of inherited numbers</h2>
<p class="lead">{int(rs['checks'])} checks: {rs['match']} reproduce the inherited published value, {rs['mismatch']}
disagree, {int(rs['info'])} are informational. Every check recomputes from the inherited ledgers with this pack's own
code; none of them trusts the inherited code. A <b>MATCH (last-digit rounding)</b> means the two agree at the six
decimals the inherited pack published.</p>
{rc_table}
<div class="note"><b>Finding, published as a finding.</b> The same frozen rule, implemented twice, gives Brier
{float(im['brier_inherited_pack']):.4f} and {float(im['brier_this_pack']):.4f} on the same {im['games']} games.
The gap ({float(im['difference']):.4f}) is {float(im['difference']) / max(1e-9, abs(float(im['measured_skill_full_run_bss']))):.1f}× the
measured skill ({float(im['measured_skill_full_run_bss']):.4f}). On this sample the score cannot be separated from the
implementation, let alone from noise. That is the honest reading and it is the reason nothing is promoted.</div>
<h2>The two dated reads, compared</h2>
<p class="lead">This pack's standings read is compared club by club against the inherited read of the same day.
No row moved, which independently confirms the Week 11 games had not been played at either read.</p>
{df_table}
<h2>Fixture-context features: what exists and what does not</h2>
{ff_table}
<h2>Standings — all 32 clubs, as rendered</h2>
{st_table}
<h2>Source register</h2>
{src_table}
"""
    return shell("evidence.html", "Evidence", "Eleven official reads with hashes and clocks, the four games read end to end, and an independent re-computation of 38 inherited numbers.", body)


def page_model():
    bt = read("backtest_summary.csv")[0]
    lk = read("luck_panel.csv")[0]
    st = read("strategies.csv")
    w11 = read("week11_forecasts.csv")
    im = read("implementation_comparison.csv")[0]

    strat_rows = [[esc(s["strategy_id"]), esc(s["name"]), esc(s["division"]), esc(s["definition"]),
                   esc(s["backtest_n"]), esc(s["backtest_bss"]), esc(s["backtest_bss_lo"]),
                   esc(s["prospective_n"]), pill(s["state"], "paper" if s["state"] == "paper" else "info"),
                   esc(s["what_would_change_our_mind_up"]), esc(s["what_would_change_our_mind_down"])]
                  for s in st]
    strat_table = table(["ID", "Strategy", "Division", "Frozen definition", "Backtest n", "Backtest BSS",
                         "BSS lower bound", "Prospective n", "State", "What would change our mind — up",
                         "What would change our mind — down"], strat_rows, numeric=("Backtest n", "Prospective n"))

    refuse = read("unscored.csv")
    refuse_rows = [[esc(r["game_id"]), esc(r["week"]), esc(r["away"]), esc(r["home"]),
                    esc(r["n_home_prior"]), esc(r["n_away_prior"]), esc(r["reason"])] for r in refuse]
    refuse_table = table(["Game", "Week", "Away", "Home", "Home prior games", "Away prior games", "Why refused"],
                         refuse_rows, numeric=("Week", "Home prior games", "Away prior games"))

    w_rows = [[esc(w["game_id"]), esc(w["date"]), esc(w["away"]), esc(w["home"]), esc(w["kickoff_et"]),
               f'{esc(w["fair_side"])} {esc(w["fair_margin_home"])}', esc(w["fair_total"]),
               esc(w["p_home_win"]),
               f'<span class="blank">{esc(w["market_side"] or "blank")}</span>',
               f'<span class="blank">{esc(w["market_total"] or "blank")}</span>',
               f'<span class="blank">{esc(w["residual_side"] or "blank")}</span>',
               pill(w["state"], "paper"), link(w["source_url"])] for w in w11]
    w_table = table(["Game", "Date", "Away", "Home", "Kickoff ET", "Our side (fair margin)", "Our total",
                     "P(home win)", "Market side", "Market total", "Residual", "State", "Source"], w_rows)

    luck_rows = [[esc(k), esc(v)] for k, v in lk.items() if k not in ("note",)]
    luck_table = table(["Quantity", "Value"], luck_rows)

    body = f"""
<div class="cards">
<div class="card"><div class="k">Games scored</div><div class="v">{esc(bt['n'])}</div><div class="s">of 150; {esc(bt['refused'])} refused, {esc(bt['weeks'])} weeks</div></div>
<div class="card"><div class="k">Brier</div><div class="v">{float(bt['brier']):.4f}</div><div class="s">climatology {float(bt['brier_climatology']):.4f}</div></div>
<div class="card"><div class="k">Brier skill</div><div class="v">{float(bt['bss']):+.4f}</div><div class="s">vs the base-rate control</div></div>
<div class="card"><div class="k">95% week-cluster</div><div class="v">{float(bt['bss_lo_week_cluster']):+.3f}</div><div class="s">to {float(bt['bss_hi_week_cluster']):+.3f} — includes zero</div></div>
<div class="card"><div class="k">Totals MAE</div><div class="v">{float(bt['totals_mae_points']):.2f}</div><div class="s">points, RMSE {float(bt['totals_rmse_points']):.2f}</div></div>
<div class="card"><div class="k">Promoted</div><div class="v">0</div><div class="s">backtest can never promote</div></div>
</div>
<div class="note bad"><b>Reading the score honestly.</b> {esc(bt['reading'])}. The bootstrap resamples whole weeks
({esc(bt['bootstrap_resamples'])} resamples, seed {esc(bt['bootstrap_seed'])}), because games inside a week share a
league environment and are not independent draws. A lower bound that includes zero is not a small edge; it is the
absence of evidence for one.</div>
<h2>The 16 games the model refuses to score, and why</h2>
<p class="lead">A margin model cannot forecast a club's first game without borrowing a number from a game played
inside the same week. That is same-week information, so those games are refused rather than scored. Publishing the
refusal is the difference between a 150-game claim and an honest one: <b>{esc(bt['reconciliation'])}</b>.</p>
{refuse_table}
<h2>Strategies and controls</h2>
<p class="lead">Every entry carries both directions of "what would change our mind", as the brief requires. The two
controls exist so that a model has something to lose to.</p>
{strat_table}
<h2>The removal-of-luck panel</h2>
<p class="lead">The score is split the only way that means anything: the part the model could remove by being
better calibrated (reliability), the part it earns by saying different things on different games (resolution), and
the part nobody can remove because football is football (uncertainty). The split is computed on five fixed
probability bands, not on the exact forecast values — an exact-value split puts one game in each band, makes
reliability equal the Brier score and would look tidy while measuring nothing.</p>
{luck_table}
<div class="note warn">The panel says the model is <b>not over-fit to luck</b>: reliability is only
<b>{100 * float(lk['reliability']) / float(lk['brier']):.1f}%</b> of the score, so almost none of it can be
recovered by recalibration alone. What it does say is worse for the model — the bands are badly ordered in the
middle. Where the model says a game is close to a coin flip (0.40&ndash;0.50), home clubs actually won
<b>32.0%</b> of the time; where it says 0.50&ndash;0.60, they won <b>44.0%</b>. The model is confident in the wrong
direction in the games it should be least sure about.</div>
<p class="small">{esc(lk['note'])}</p>
<h2>Week 11 forecasts — published before kickoff, market columns blank by policy</h2>
<p class="lead">Three fixtures, because three fixtures were read from the official schedule. The other ten Week 11
games are not forecast here; inventing them would be the exact failure the brief forbids. Each row carries our fair
number, and the market and residual columns are blank:</p>
<div class="note">no official NFL page publishes a price. A residual needs a price. The column exists, is empty, and
says so — that is the price-data policy, applied rather than described.</div>
{w_table}
<h2>Implementation comparison</h2>
<div class="note warn">{esc(im['finding'])}<br><br>
Inherited pack: Brier {float(im['brier_inherited_pack']):.6f}. This pack: {float(im['brier_this_pack']):.6f}.
Difference {float(im['difference']):.6f}, on {esc(im['games'])} identical games. Sources:
<code>{esc(im['inherited_source'])}</code> and <code>{esc(im['this_source'])}</code>.</div>
<h2>What is deliberately absent</h2>
<p>Parlay and prop-combo scores (no validated joint probability exists), ROI and CLV (no price), promotion (no
prospective sample), and any injury or personnel term in the model (the ablation is registered but coverage is
4 games). Each absence has a gate on the readiness page.</p>
"""
    return shell("model.html", "Model and proper scores", "The frozen baseline re-run from its pre-registered text, scored on official finals, with the interval that decides whether the score means anything.", body)


def page_availability():
    starts = read("starters.csv")
    na = read("not_active.csv")
    pt = read("playtime.csv")
    cv = read("club_view.csv")
    jo = read("designation_join.csv")
    gs = read("game_status.csv")
    rep = read("replacement.csv")
    gap = read("snap_gap.csv")
    ss = read("snap_sum.csv")

    cv_rows = [[esc(c["club"]), esc(c["opponent"]), esc(c["declared_out"]), esc(c["declared_questionable"]),
                esc(c["blank_game_status"]), esc(c["not_active_entries_this_pack"]),
                esc(c["out_and_not_active"]), esc(c["out_not_on_inactive"]),
                link(c["report_url"]), link(c["book_url"])] for c in cv]
    cv_table = table(["Club", "Opponent", "Declared Out", "Questionable", "Blank status",
                      "Not Active entries (book)", "Out & inactive", "Out but not on inactive",
                      "Report", "Book"], cv_rows, numeric=("Declared Out", "Questionable", "Blank status",
                                                          "Not Active entries (book)", "Out & inactive",
                                                          "Out but not on inactive"))

    gap_rows = [[esc(g["club"]), esc(g["player"]), esc(g["position"]), esc(g["report_says"]),
                 esc(g["book_says"]),
                 pill(g["consistent"], "ok" if g["consistent"] == "yes" else "bad"),
                 esc(g["action"]), link(g["report_url"]), link(g["book_url"])] for g in gap]
    gap_table = table(["Club", "Player", "Pos", "Week 10 report", "Book Not Active", "Agree",
                       "Action taken", "Report", "Book"], gap_rows)

    na_rows = [[esc(n["game_id"]), esc(n["club"]), esc(n["position_listed"]), esc(n["jersey_as_printed"]),
                esc(n["player_as_printed"]), link(n["source_url"])] for n in na]
    na_table = table(["Game", "Club", "Position as printed", "Jersey as printed", "Player as printed", "Source"],
                     na_rows)

    ss_rows = [[esc(s["club"]), esc(s["unit_snaps"]), esc(s["players_transcribed"]),
                esc(s["player_snaps_transcribed"]), esc(s["capacity_player_snaps"]), esc(s["pct_of_capacity"]),
                pill(s["within_capacity"], "ok" if s["within_capacity"] == "yes" else "bad")] for s in ss]
    ss_table = table(["Club", "Unit snaps", "Players transcribed", "Player-snaps transcribed",
                      "Capacity (snaps × 11)", "% of capacity", "Within capacity"], ss_rows,
                     numeric=("Unit snaps", "Players transcribed", "Player-snaps transcribed", "Capacity (snaps × 11)"))

    pt_rows = [[esc(p["club"]), esc(p["player_as_printed"]), esc(p["position"]), esc(p["snaps"]),
                esc(p["pct_of_unit_snaps"]), pill(p["publisher_label"], "warn"), link(p["source_url"])]
               for p in sorted(pt, key=lambda r: (r["club"], -int(r["snaps"])))]
    pt_table = table(["Club", "Player as printed", "Pos", "Offense snaps", "% of unit snaps",
                      "Publisher's label", "Source"], pt_rows, numeric=("Offense snaps",))

    rep_rows = [[esc(r["game_id"]), esc(r["club"]), esc(r["player"]), esc(r["position"]), esc(r["designation"]),
                 esc(r["was_listed_starter"]), esc(r["on_not_active"]), esc(r["offensive_snaps"]),
                 link(r["book_url"])] for r in rep]
    rep_table = table(["Game", "Club", "Player", "Pos", "Report said", "Named starter in this game",
                       "On Not Active", "Offense snaps", "Book"], rep_rows)

    # starter grid: one row per club, positions in order
    by_club = {}
    for s in starts:
        by_club.setdefault((s["game_id"], s["club"]), {"offense": [], "defense": []})
        by_club[(s["game_id"], s["club"])][s["unit"]].append(f'{s["position_listed"]} {s["player_as_printed"]}')
    st_rows = []
    for (gid, club), v in sorted(by_club.items()):
        st_rows.append([esc(gid), esc(club),
                        "<br>".join(esc(x) for x in v["offense"]),
                        "<br>".join(esc(x) for x in v["defense"])])
    st_table = table(["Game", "Club", "Offense as the book lists it", "Defense as the book lists it"], st_rows)

    body = f"""
<div class="note"><b>Order of reliability, stated before any table.</b>
1. <b>Not Active</b> and <b>Lineups</b> are formal blocks of the NFL's official Game Book.
2. <b>Playtime Percentage</b> is also in the official book but the NFL captions the table
<code>(Unofficial)</code>. Every such value here is labelled Unofficial.
3. Nothing here is inferred from a jersey number, a depth chart, or a club's website.</div>
<div class="note bad"><b>The finding that matters.</b> Across the four games, 16 players were marked <b>Out</b> by the
Week 10 report. Twelve appear on their club's Not Active list. Four do not — DET S Kerby Joseph, NE RB TreVeyon
Henderson, CLE FB Michael Burton and LAC G Branson Taylor. The pack publishes both official values and does not pick a
winner. A model that maps "Out" to "did not dress" would be wrong on one in four of these rows.</div>
<h2>Per-club view: starters out, replacements named, net count</h2>
{cv_table}
<h2>Every Out designation, joined to the official inactive list</h2>
<p class="lead">Match rule, fixed before the join ran: printed surname equal <i>and</i> printed first initial equal,
ignoring generational suffixes. No fuzzy matching, no manual pairing.</p>
{gap_table}
<h2>Not Active — as the books print it</h2>
<p class="lead">These are settlement records: the book is published after the game. They are the best official evidence
of who did not dress, not a pre-kickoff feed. A pre-kickoff inactive page was searched for and not found
(<code>Q05</code>).</p>
{na_table}
<h2>Playing time, with the publisher's own label attached</h2>
<p class="lead">Only offence is transcribed. Defence is not, and is therefore absent rather than zero.</p>
{pt_table}
<h3>Capacity check</h3>
<p class="lead">A club's offensive player-snaps can never exceed unit snaps × 11. The transcribed subset is checked
against that ceiling, which catches the double-printed rows the books contain (CLE lists T. Pride twice, DET lists
C. Izien twice).</p>
{ss_table}
<h2>Declared out, and what the club actually played</h2>
{rep_table}
<h2>The 176 starters the books name</h2>
<p class="lead">Listed in the order the book prints them. Several positions repeat — three receivers, three
cornerbacks — which is exactly why the pack refuses to convert this into a depth rank: the book names a line-up,
not a ranking.</p>
{st_table}
"""
    return shell("availability.html", "Availability and replacement depth", "Who the official report said would not play, who the official book said did not dress, and how much the club actually played each man.", body)


def page_questions():
    qs = read("questions.csv")
    gates = read("gates.csv")
    rows = [[f'<code>{esc(q["qid"])}</code>', esc(q["group"]), esc(q["question"]), esc(q["have"]),
             esc(q["need"]), esc(q["discovery"]), esc(q["changes"]), pill(q["status"], "warn")]
            for q in qs]
    q_table = table(["ID", "Theme", "Question that must be answered", "What we already have",
                     "What is missing", "How to discover it", "What changes when it is answered", "Status"],
                    rows)
    g_rows = [[f'<code>{esc(g["gate"])}</code>', esc(g["states"]), esc(g["clears"]),
               pill(g["state"], "ok" if g["state"] == "closed" else "bad")] for g in gates]
    g_table = table(["Gate", "What it is", "What clears it", "State"], g_rows)

    body = f"""
<div class="note"><b>How to read this page.</b> A question is not answered by an opinion. Each row names what we
already hold, what is genuinely missing, the concrete route to get it, and what becomes possible once it is answered.
The last column stays <b>open</b> until a source has been read or the owner has recorded a decision.</div>
<h2>{len(qs)} open questions</h2>
{q_table}
<h2>Gate register — the same information as a checklist</h2>
<p class="lead">{sum(1 for g in gates if g['state'] == 'closed')} of {len(gates)} gates are closed. A closed gate is
one whose clearing condition has been met and can be re-checked by anyone from the repository alone.</p>
{g_table}
"""
    return shell("questions.html", "Questions, information and answers", "What must be answered before a decision can reasonably be made, what is missing, and the route to discovering it.", body)


def page_suggestions():
    sug = read("suggestions.csv")
    rows = [[f'<code>{esc(s["sid"])}</code>', esc(s["title"]), esc(s["why"]), esc(s["evidence"]),
             pill(s["gain"], "ok" if s["gain"] == "high" else "info"),
             pill(s["cost"], "warn" if s["cost"] == "medium" else "info"),
             pill(s["risk"], "bad" if s["risk"] == "high" else ("warn" if s["risk"] == "medium" else "ok")),
             esc(s["route"]),
             '<span class="blank">owner decision pending</span>'] for s in sug]
    t = table(["ID", "Proposal", "Why it improves decisions", "Evidence in this repo", "Gain", "Cost", "Risk",
               "How it would be built", "Decision"], rows)

    body = f"""
<div class="note"><b>Nothing here is implemented.</b> These are proposals, ordered by expected value on decision
quality rather than by effort. Each carries the evidence for it, the cost, the risk, and an empty decision field so
the owner can accept, reject or defer one at a time without reading the rest.</div>
<h2>{len(sug)} suggestions awaiting a decision</h2>
{t}
<h2>The three that matter most, in one paragraph each</h2>
<h3>S06 — get a written price-policy decision before any more pricing work</h3>
<p>Nine requirement rows are blocked on one missing input and no amount of engineering can clear them. Either the
owner supplies a licensed price archive or the project formally drops ROI, CLV and every residual column. Both are
defensible; continuing to build plumbing around an input that will never arrive is not.</p>
<h3>S03 — adopt a three-level definition of "verified"</h3>
<p>The site currently uses one word for a certified count, a number the league itself labels Unofficial, and a
number the pack derived. That is the single easiest way for a careful site to mislead a reader. A legend on every
table fixes it in an afternoon.</p>
<h3>S05 — read the 2024 and 2025 finals next</h3>
<p>One season cannot produce a holdout, and a holdout is what turns a backtest into a decision. The pages are
published, the read is cheap, and it unblocks calibration, designation scoring and the ablation at the same time.</p>
"""
    return shell("suggestions.html", "Suggestions", "Twelve proposals to improve decision quality, each with its evidence, cost, risk and build route. Decisions are left to the owner.", body)


def page_flagged():
    flags = read("flagged.csv")
    rows = [[f'<code>{esc(f["fid"])}</code>',
             pill(f["severity"], "bad" if f["severity"] == "high" else ("warn" if f["severity"] == "medium" else "info")),
             esc(f["finding"]), esc(f["detail"]), esc(f["impact"]), esc(f["action"]),
             link(f["source_url"]), pill("does not block", "ok")] for f in flags]
    t = table(["ID", "Severity", "Finding", "Exactly what the pages show", "Why it matters", "What this pack did",
               "Official source", "Merge"], rows)

    body = f"""
<div class="note warn"><b>These are not blockers and they are not hidden.</b> Each row is something the official
pages show that a careful reader should not paper over. None of them stops the merge; all of them are published here
with the link that produced them so they can be checked, disputed or accepted.</div>
<h2>{len(flags)} irregularities</h2>
{t}
<h2>What was rejected rather than flagged</h2>
<p>Two shortcuts were available and both were refused: ranking depth from a depth chart that no source read here
publishes, and reading a blank game-status cell as "healthy". The first would have produced the interactive
match-up matrix the brief asks for and every number in it would have been invented. The second would have turned
38 blank cells into 38 implied clearances. Both are recorded on the readiness page as blocked gates.</p>
"""
    return shell("flagged.html", "Flagged for review", "Twelve irregularities found against the official pages on 2026-11-19, each with the link that produced it. None blocks the merge.", body)


def build():
    os.makedirs(DOCS, exist_ok=True)
    pages = {
        "index.html": page_index,
        "evidence.html": page_evidence,
        "model.html": page_model,
        "availability.html": page_availability,
        "questions.html": page_questions,
        "suggestions.html": page_suggestions,
        "flagged.html": page_flagged,
    }
    for name, fn in pages.items():
        text = fn()
        with open(os.path.join(DOCS, name), "w") as fh:
            fh.write(text)
        print(f"wrote docs/nfl-d713b52f/{name} ({len(text):,} bytes)")


def main():
    build()
    if "--check" in sys.argv:
        rc = subprocess.call([sys.executable, os.path.join(REPO, "scripts", "check_nfl_d713b52f.py")])
        sys.exit(rc)


if __name__ == "__main__":
    main()
