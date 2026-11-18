#!/usr/bin/env python3
"""Build the nfl-0ce967db Pages site from committed data. No network, no clock, no inputs.

    python3 scripts/build_nfl_0ce967db.py            # write docs/nfl-0ce967db/**
    python3 scripts/build_nfl_0ce967db.py --check    # build then run the verifier

Every page is a table or a list. Every published row links to the official page it came from.
Cells that no official source supports stay empty and the page says why.
"""
from __future__ import annotations

import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_0ce967db")
DOCS = os.path.join(REPO, "docs", "nfl-0ce967db")


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def a(url: str, label: str = "source") -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)}&nbsp;&#8599;</a>'


def num(v, nd=3):
    if v in ("", None):
        return ""
    try:
        return f"{float(v):.{nd}f}"
    except (TypeError, ValueError):
        return esc(v)


def blank(v) -> str:
    """A blank cell must never look like a zero."""
    return esc(v) if str(v).strip() else '<span class="nb" title="no official source supports a value">—</span>'


CSS = """
:root{--ink:#16232e;--muted:#5d7183;--navy:#0f2433;--teal:#0a7d74;--line:#dbe3e8;--paper:#f5f8f9;
--white:#fff;--warn:#fff4dc;--warnink:#7a4b00;--ok:#0a6b4f;--bad:#9c2b2b;--soft:#eef4f5}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);line-height:1.55;
font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:15px}
a{color:var(--teal);text-underline-offset:.16em}
header{background:var(--navy);color:#fff}
.wrap{width:min(1220px,calc(100% - 2rem));margin:0 auto}
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
p{max-width:78ch}
.lead{color:var(--muted);max-width:82ch}
.cards{display:grid;gap:.7rem;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));margin:1rem 0 .4rem}
.card{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:.8rem .9rem}
.card .k{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.card .v{font-size:1.65rem;font-weight:700;line-height:1.15;margin-top:.15rem}
.card .s{font-size:.78rem;color:var(--muted)}
.tw{overflow-x:auto;background:var(--white);border:1px solid var(--line);border-radius:10px;margin:.6rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.84rem}
th,td{padding:.42rem .6rem;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--soft);font-size:.74rem;letter-spacing:.05em;text-transform:uppercase;color:#39505f;
position:sticky;top:0;white-space:nowrap}
tbody tr:hover{background:#fbfdfd}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.nb{color:#93a6b3;cursor:help}
.pill{display:inline-block;padding:.05rem .42rem;border-radius:999px;font-size:.72rem;font-weight:600;
white-space:nowrap;border:1px solid}
.p-met{background:#e7f6ef;color:var(--ok);border-color:#b9e3d0}
.p-blocked{background:#fdeaea;color:var(--bad);border-color:#f2c6c6}
.p-partially_met{background:var(--warn);color:var(--warnink);border-color:#f0d9a8}
.p-not_run,.p-out_of_scope{background:#eceff1;color:#4a5c69;border-color:#d3dae0}
.p-rejected_adopted{background:#eef0fb;color:#3d3f8a;border-color:#cfd4ef}
.note{background:var(--warn);border:1px solid #f0d9a8;border-left:4px solid #d99b1a;color:#4a3300;
padding:.7rem .9rem;border-radius:8px;margin:.9rem 0;max-width:92ch;font-size:.88rem}
.good{background:#eef8f3;border:1px solid #bfe3d2;border-left:4px solid var(--ok);color:#134a37;
padding:.7rem .9rem;border-radius:8px;margin:.9rem 0;max-width:92ch;font-size:.88rem}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.8rem;word-break:break-all}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.8rem;padding:1rem 0 2rem}
.tag{font-size:.72rem;color:var(--muted)}
ul.tight{margin:.3rem 0 .8rem;padding-left:1.1rem}
ul.tight li{margin:.18rem 0;max-width:86ch}
"""

NAV = [
    ("index.html", "Overview"),
    ("readiness.html", "Decision readiness"),
    ("board.html", "Strategy board"),
    ("origination.html", "Originated lines"),
    ("availability.html", "Injuries & depth"),
    ("evidence.html", "Schedule & results"),
    ("questions.html", "Q / I / A"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources & method"),
]


def page(title: str, active: str, body: str) -> str:
    nav_parts = []
    for h, t in NAV:
        cls = ' class="on"' if h == active else ""
        nav_parts.append(f'<a href="{h}"{cls}>{esc(t)}</a>')
    nav = "".join(nav_parts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own6 NFL decision desk</title>
<style>{CSS}</style></head>
<body>
<header><div class="wrap">
  <div class="top"><b>OWN6</b><span>NFL decision desk · session 0ce967db</span>
  <span style="margin-left:auto;color:#8fb7b2">reads of 2026-11-18 UTC</span></div>
  <nav>{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  Every number on this site is either read from the official nfl.com page linked beside it, or is
  arithmetic on such numbers with the derivation shown. Market prices are not published by any source in
  this evidence set, so every price, ROI and CLV cell is empty. No profitability claim is made anywhere.
  <a href="sources.html">Sources &amp; method</a>.
</footer>
</body></html>"""


def table(headers: list[tuple[str, str]], rows: list[list[str]], extra: str = "") -> str:
    head = "".join(f'<th class="{cls}">{esc(label)}</th>' for label, cls in headers)
    body = "".join("<tr>" + "".join(f'<td class="{c}">{v}</td>' for (_, c), v in zip(headers, r)) + "</tr>"
                   for r in rows)
    return f'<div class="tw"><table {extra}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


# ---------------------------------------------------------------------------------------------
def page_index() -> str:
    reqs = read("requirements.csv")
    board = read("leaderboard.csv")
    corr = read("correlations.csv")
    slat = read("week11_slate.csv")
    inj = read("availability_week10_read.csv")
    flags = read("flagged.csv")
    metrics = read("metrics.csv")
    m = {r["metric"]: r for r in metrics}
    states = {}
    for r in reqs:
        states[r["state"]] = states.get(r["state"], 0) + 1
    qual = sum(1 for r in board if r.get("proper_score_qualified") == "yes")
    clin = m.get("corpus_games", {}).get("value", "150")
    body = [f"""
<h1>Own6 NFL decision desk</h1>
<p class="lead">A working decision surface, not a tout sheet. It publishes what the official sources
actually say as of <strong>2026-11-18 UTC</strong>, what the model measures on 150 settled games, and —
in the same table — every requirement it cannot yet satisfy and the exact number that would clear it.
No page accepts input; nothing here is a recommendation.</p>

<div class="cards">
  <div class="card"><div class="k">Settled games scored</div><div class="v">{esc(clin)}</div>
    <div class="s">weeks 1–10, 32/32 clubs reconciled</div></div>
  <div class="card"><div class="k">Strategies qualified</div><div class="v">{qual}</div>
    <div class="s">of {len([r for r in board if r['kind'] != 'control'])} candidates; 0 rewards paid</div></div>
  <div class="card"><div class="k">Requirements blocked</div><div class="v">{states.get('blocked', 0)}</div>
    <div class="s">of {len(reqs)} rows in the ledger</div></div>
  <div class="card"><div class="k">Correlations published</div><div class="v">{len(corr)}</div>
    <div class="s">{sum(1 for c in corr if c['excludes_zero']=='yes')} with an interval excluding zero</div></div>
  <div class="card"><div class="k">Week-11 games captured</div><div class="v">{len(slat)}</div>
    <div class="s">kickoff, network and bye verified</div></div>
  <div class="card"><div class="k">Availability rows</div><div class="v">{len(inj)}</div>
    <div class="s">designations, 14 clubs read in full</div></div>
  <div class="card"><div class="k">Flagged for review</div><div class="v">{len(flags)}</div>
    <div class="s">including 2 bugs found and fixed today</div></div>
  <div class="card"><div class="k">Market price</div><div class="v">none</div>
    <div class="s">no official source prints one</div></div>
</div>

<div class="note"><strong>Read this before any number below.</strong> Every scored model shows a
<em>positive</em> point estimate of Brier skill against a climatology control, and every one of them has a
<em>negative</em> lower bound once whole weeks are resampled. So the apparent skill is not distinguishable
from luck at this sample size. The removal-of-luck panel goes further and shows the models are also
<em>miscalibrated</em>: they expect a 55% home-win rate in a season where home clubs won 46% of the games
scored, because the registration adds a fixed +2.5 points of home field and 2026 has produced −0.53. That
defect is measured, published and registered for a prospective fix — not quietly tuned away.</div>

<h2>The five numbers that decide the project</h2>
"""]
    key = []
    if "bss_lower_bound_best" in m:
        key.append(["Best week-cluster lower bound of Brier skill", num(m["bss_lower_bound_best"]["value"], 4),
                    "negative ⇒ no candidate survives clustering", "board.html"])
    if "totals_mae_best" in m:
        key.append(["Best totals MAE (points)", num(m["totals_mae_best"]["value"], 2),
                    "two estimators published, neither collapsed", "board.html"])
    key += [
        ["Clubs reconciled against official standings", "32 / 32",
         "record, PF and PA all match after one code repair", "evidence.html"],
        ["Requirements blocked on a missing source", str(states.get("blocked", 0)),
         "each names the gate and the clearing number", "readiness.html"],
        ["Questions still needing the owner", "2",
         "consent for scheduled reads; a private data layer", "questions.html"],
    ]
    body.append(table([("What", ""), ("Value", "n"), ("Why it matters", ""), ("Where", "")], key))

    body.append("""
<h2>What changed today (2026-11-18)</h2>
<ul class="tight">
<li><strong>The corpus is settled at 150 games.</strong> The Monday game left blank by the previous
session is officially final: <a href="https://www.nfl.com/schedules/2026/by-week/week-10" rel="noopener">Chargers 23, Ravens 20</a>.</li>
<li><strong>One real data defect found and repaired read-only.</strong> The inherited corpus writes the
Rams as both <span class="mono">LA</span> and <span class="mono">LAR</span>; per-club reconciliation
against the official standings failed for exactly one club until that was repaired.</li>
<li><strong>Two of my own bugs found and fixed before publication</strong> — totals were first scored as
probabilities, and a league-mean unit error inflated every total by about 23 points. Both are on the
Flagged for Review page with the numbers that exposed them.</li>
<li><strong>The week-11 injury report does not exist yet.</strong> The hub still serves WEEK 10 and a
week-11 URL redirects to week 10, so 18 clubs' blocks are blank rather than "healthy".</li>
<li><strong>Three previously flagged blanks are closed</strong>: the Lions' Joseph, Mays and Reed are
published as <span class="mono">Out</span> today.</li>
</ul>

<h2>Start with these</h2>
""")
    links = [
        ("readiness.html", "Decision readiness",
         f"{len(reqs)} rows, one per requirement, each with its blocking gate and the number that clears it"),
        ("board.html", "Strategy board",
         "proper scores, week-cluster intervals, multiplicity adjustment, controls, luck panel, demotion gate"),
        ("origination.html", "Originated lines",
         "13 week-11 games priced side → total → moneyline, with the market columns deliberately empty"),
        ("availability.html", "Injuries &amp; depth",
         f"{len(inj)} dated designation rows and an honest account of what is missing"),
        ("questions.html", "Q / I / A",
         "what we know, what we lack, and the route to each missing answer"),
        ("flagged.html", "Flagged for review",
         f"{len(flags)} items, none of which block publication but all of which the owner should see"),
    ]
    body.append(table([("Page", ""), ("What is on it", "")],
                      [[f'<a href="{h}">{t}</a>', d] for h, t, d in links]))
    return page("Overview", "index.html", "".join(body))


def page_readiness() -> str:
    reqs = read("requirements.csv")
    counts: dict[str, int] = {}
    for r in reqs:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    order = ["met", "partially_met", "blocked", "not_run", "rejected_adopted", "out_of_scope"]
    body = [f"""
<h1>Decision readiness</h1>
<p class="lead">One row per requirement in the owner's brief, in the owner's order. Each row states what
exists <em>with its numbers</em>, the gate that still blocks it, and the exact number or artefact that
would clear it. A requirement is only <span class="pill p-met">met</span> when the artefact is populated,
not merely when a schema exists.</p>
"""]
    body.append(table([("State", "n"), ("Rows", "n")],
                      [[f'<span class="pill p-{s}">{esc(s)}</span>', str(counts.get(s, 0))]
                       for s in order if s in counts]))
    rows = []
    for r in reqs:
        rows.append([
            esc(r["req_id"]),
            esc(r["owner_requirement"]),
            f'<span class="pill p-{esc(r["state"])}">{esc(r["state"])}</span>',
            esc(r["what_we_have_with_numbers"]),
            esc(r["blocking_gate"]),
            esc(r["number_that_would_clear_it"]),
            a(r["source_url"]),
        ])
    body.append(table([("ID", ""), ("Requirement (owner's words)", ""), ("State", ""),
                       ("What exists now, with numbers", ""), ("Blocking gate", ""),
                       ("Number that would clear it", ""), ("Official source", "")], rows))
    body.append('<div class="note">Blank is not zero. Where a value has no official source, the row says '
                'so instead of estimating. The verifier fails the build if any requirement row lacks an '
                'nfl.com source link.</div>')
    return page("Decision readiness", "readiness.html", "".join(body))


def page_board() -> str:
    board = read("leaderboard.csv")
    luck = read("luck_panel.csv")
    abl = read("ablations.csv")
    ablrun = read("ablations_run.csv")
    dem = read("demotion_gate.csv")
    f11 = read("week11_forecasts.csv")
    body = ["""
<h1>Strategy board</h1>
<p class="lead">Proper scores on official outcomes, ranked by skill rather than by wins. Every value
carries its sample size, a week-cluster interval and a multiplicity adjustment for the size of the
frozen family. The prospective leaderboard is <strong>empty by rule</strong>: backtest numbers are
barred from it, so the state of every strategy is <span class="mono">paper</span>.</p>

<div class="note"><strong>How to read the skill column.</strong> Brier skill is
<em>1 − (model Brier ÷ control Brier)</em>. The point estimate uses every scored game; the interval
resamples whole <em>weeks</em>, because games in the same week share conditions. When the lower bound is
below zero the honest reading is "no demonstrated skill", however good the point estimate looks.</div>
"""]
    rows = []
    for r in board:
        rows.append([
            esc(r["strategy_id"]), esc(r["strategy"]),
            f'<span class="tag">{esc(r["division"])}</span>',
            esc(r["n_scored"]),
            num(r.get("brier"), 4),
            num(r.get("brier_skill_vs_control"), 4),
            blank(num(r.get("bss_lower_95_week_cluster"), 4)),
            blank(num(r.get("bss_upper_95_week_cluster"), 4)),
            blank(num(r.get("sign_test_p_two_sided"), 4)),
            esc(r.get("bonferroni_pass", "")),
            '<span class="pill p-%s">%s</span>' % (
                "met" if r.get("proper_score_qualified") == "yes" else "blocked",
                esc(r.get("proper_score_qualified", ""))),
            blank(num(r.get("totals_mae_points"), 2)),
            blank(num(r.get("totals_rmse_points"), 2)),
            blank(r.get("roi")),
            blank(r.get("clv")),
        ])
    body.append(table([("ID", ""), ("Strategy", ""), ("Division", ""), ("n", "n"),
                       ("Brier", "n"), ("Brier skill", "n"), ("Lower 95%", "n"), ("Upper 95%", "n"),
                       ("Sign-test p", "n"), ("Bonferroni pass", ""), ("Qualified", ""),
                       ("Totals MAE", "n"), ("Totals RMSE", "n"), ("ROI", "n"), ("CLV", "n")], rows))
    body.append("""
<p class="tag">Family size frozen at 7 in the registration, so the Bonferroni threshold is
0.05 ÷ 7 = 0.007143. The sign test is a per-game comparison with the climatology control; it is a second,
independent read on direction and it is <em>not</em> a substitute for the clustered interval. Totals MAE
and RMSE are in points and apply only to the two totals candidates; a total is not a win probability, so
their Brier cells stay empty rather than borrowing the margin model's probabilities.</p>

<h2>Control baselines</h2>
<p>Every run carries controls, so a reader can see what "no skill" scores.</p>
""")
    ctrl = [r for r in board if r["kind"] == "control"]
    body.append(table([("Control", ""), ("Brier", "n"), ("Brier skill vs climatology", "n"),
                       ("What it proves", "")],
                      [[esc(r["strategy"]), num(r.get("brier"), 4),
                        num(r.get("brier_skill_vs_control"), 4),
                        esc("climatology is the reference; always-home is the floor")] for r in ctrl]))

    body.append("""
<h2>Removal-of-luck panel</h2>
<p>The exact Murphy decomposition of each score, computed per distinct forecast value so the identity
holds (a binned version loses within-bin spread — an earlier version of this panel did exactly that and a
test caught it): <strong>reliability</strong> is the part of the score caused by miscalibration,
<strong>resolution</strong> is the part earned by separating good games from bad,
<strong>uncertainty</strong> is the irreducible base-rate variance. <span class="mono">Luck share</span>
is reliability ÷ Brier.</p>
<div class="note"><strong>What the luck share says here.</strong> For the three probability models it is
near 1.0, and that number means something more specific than "the model is lucky": their Brier score is
almost entirely calibration error. Those models forecast a mean home probability near 0.55 while home
clubs actually won 45.8% of the scored games. A large share of the accuracy they <em>do</em> have comes
from the resolution term — they rank games better than a base rate — but the level of the forecast is
wrong, which is a defect that a well-calibrated forecaster of the same shape would not have.</div>
<h3>Where the miscalibration comes from, measured</h3>
<p>The registered model adds a fixed <strong>+2.5 points</strong> of home-field advantage. In this
corpus the realised mean home margin is <strong>−0.53 points</strong> over 150 games and home clubs won
47.3% of them. The table below replaces that constant and re-scores the identical model, so the effect is
isolated rather than argued.</p>
""")
    body.append(table([("Strategy", ""), ("n", "n"), ("Mean probability", "n"), ("Observed home-win rate", "n"),
                       ("Brier", "n"), ("Reliability", "n"), ("Resolution", "n"), ("Uncertainty", "n"),
                       ("Luck share", "n")],
                      [[esc(r["strategy"]), esc(r["n"]), num(r.get("mean_probability"), 3),
                        num(r.get("base_rate"), 3), num(r.get("brier"), 4),
                        num(r.get("reliability"), 4), num(r.get("resolution"), 4),
                        num(r.get("uncertainty"), 4), num(r.get("luck_share"), 3)] for r in luck]))

    hf = read("homefield_diagnostic.csv")
    if hf:
        body.append(table([("Home-field variant", ""), ("Mean forecast P(home)", "n"),
                           ("Observed home-win rate", "n"), ("Margin MAE (pts)", "n"),
                           ("MAE lower 95%", "n"), ("MAE upper 95%", "n"), ("Margin bias (pts)", "n"),
                           ("Bias lower 95%", "n"), ("Bias upper 95%", "n"), ("n", "n")],
                          [[esc(r["variant"]), num(r["mean_forecast_home_prob"], 4),
                            num(r["observed_home_win_rate"], 4), num(r["margin_mae_pts"], 3),
                            num(r["mae_lower_95"], 3), num(r["mae_upper_95"], 3),
                            num(r["margin_bias_pts"], 3), num(r["bias_lower_95"], 3),
                            num(r["bias_upper_95"], 3), esc(r["n"])] for r in hf]))
        body.append('<p class="tag">These four variants are <strong>post-hoc diagnostics</strong>, not '
                    'candidates. They were computed after the backtest was seen, they appear in no '
                    'leaderboard column, and they do not count toward any promotion sample. Their only '
                    'job is to show that the constant, not the information, is what is wrong. The fix '
                    'is registered separately as amendment A1 (candidate S06) and will only be judged '
                    'on games not yet played.</p>')

    body.append("""
<h2>Only one total is published twice until one wins</h2>
<p>The owner's rule is explicit: keep both estimators visible with the gap, and collapse only after a
walk-forward comparison. Neither is collapsed here.</p>
""")
    tot = [r for r in board if r["kind"] == "total"]
    body.append(table([("Estimator", ""), ("MAE", "n"), ("MAE lower 95%", "n"), ("MAE upper 95%", "n"),
                       ("RMSE", "n"), ("Mean error (bias)", "n"), ("n", "n")],
                      [[esc(r["strategy"]), num(r.get("totals_mae_points"), 2),
                        num(r.get("totals_mae_lower_95"), 2), num(r.get("totals_mae_upper_95"), 2),
                        num(r.get("totals_rmse_points"), 2), num(r.get("totals_mean_error_points"), 2),
                        esc(r.get("totals_n"))] for r in tot]))
    for r in tot:
        if r["strategy_id"] == "S05" and r.get("gap_vs_S04_abs_error_points"):
            body.append(f'<p class="tag">S05 − S04 paired difference in absolute error: '
                        f'{num(r["gap_vs_S04_abs_error_points"], 3)} points '
                        f'[{num(r.get("gap_vs_S04_lower_95"), 3)}, {num(r.get("gap_vs_S04_upper_95"), 3)}] '
                        f'— the interval includes zero, so the gap is not shown to be real.</p>')

    body.append("""
<h2>Ablations, not penalties</h2>
<p>The registered test of a feature is a paired comparison of the same model with and without it.
No fixed point penalty for a missing starter is applied anywhere in this project.</p>
""")
    body.append(table([("ID", ""), ("Ablation", ""), ("Statistic", ""), ("State", ""), ("Detail / gate", ""), ("Source", "")],
                      [[esc(r["ablation_id"]), esc(r["ablation"]), esc(r["statistic"]),
                        f'<span class="pill p-{"met" if r["state"]=="run" else "not_run"}">{esc(r["state"])}</span>',
                        esc(r["detail"] or r["blocking_gate"]), a(r["source_url"])] for r in abl]))
    body.append(table([("ID", ""), ("Comparison", ""), ("Feature removed", ""), ("Metric without", "n"),
                       ("Metric with", "n"), ("Paired difference", "n"), ("Lower 95%", "n"),
                       ("Upper 95%", "n"), ("Excludes zero", "")],
                      [[esc(r["ablation_id"]), esc(r["comparison"]), esc(r["feature_removed"]),
                        num(r["metric_without"], 4), num(r["metric_with"], 4),
                        num(r["paired_difference"], 4), num(r["lower_95"], 4), num(r["upper_95"], 4),
                        esc(r["interval_excludes_zero"])] for r in ablrun]))

    body.append("""
<h2>Demotion gate</h2>
<p>A strategy that reaches a live state is sent back to paper automatically when its trailing evidence
turns negative — the number that triggers it is published here in advance.</p>
""")
    body.append(table([("Strategy", ""), ("State", ""), ("Promotion rule", ""), ("Demotion rule", ""),
                       ("Prospective scored", "n"), ("Needs", "n"), ("Blocking gate", "")],
                      [[esc(r["strategy_id"]),
                        f'<span class="pill p-partially_met">{esc(r["state"])}</span>',
                        esc(r["promotion_rule"]), esc(r["demotion_rule"]),
                        esc(r["prospective_scored"]), esc(r["promotion_needs"]),
                        esc(r["blocking_gate"])] for r in dem]))

    body.append("""
<h2>Prospective batch: week 11</h2>
<p>Registered before kickoff, so the prospective claim is auditable. These are the first rows that may
ever enter the leaderboard, and only after the games are played and the rows are scored.</p>
""")
    body.append(table([("Game", ""), ("Home win prob (S01)", "n"), ("Home win prob (S03)", "n"),
                       ("Fair margin", "n"), ("Fair total S04", "n"), ("Fair total S05", "n"),
                       ("σ (pts)", "n"), ("State", "")],
                      [[f'{esc(r["away"])} at {esc(r["home"])}', num(r["p_home_win_S01"], 3),
                        num(r["p_home_win_S03"], 3), num(r["expected_margin_home_S01"], 2),
                        num(r["expected_total_S04"], 2), num(r["expected_total_S05"], 2),
                        num(r["sigma_margin"], 2),
                        f'<span class="pill p-not_run">{esc(r["state"])}</span>'] for r in f11]))
    return page("Strategy board", "board.html", "".join(body))


def page_origination() -> str:
    orig = read("originated_lines.csv")
    pol = read("price_policy.csv")
    body = ["""
<h1>Originated lines</h1>
<p class="lead">Our own number for every week-11 market, published in a fixed order — side, then total,
then moneyline — with the model's uncertainty beside it. The market columns exist, are separate, and are
<strong>empty</strong>: no source in this evidence set prints a price, and inventing one is not allowed.</p>
"""]
    rows = []
    for r in orig:
        rows.append([
            esc(r["game_id"]), f'{esc(r["away"])} at {esc(r["home"])}', esc(r["kickoff_et"]),
            num(r["fair_margin_home"], 2), num(r["fair_total"], 2), num(r["fair_home_win_prob"], 3),
            num(r["sigma_margin_pts"], 2),
            blank(r["market_margin_home"]), blank(r["market_total"]), blank(r["market_home_price"]),
            blank(r["difference_margin"]), blank(r["difference_total"]),
            a(r["source_url"]),
        ])
    body.append(table([("ID", ""), ("Fixture", ""), ("Kickoff ET", ""), ("Fair home margin", "n"),
                       ("Fair total", "n"), ("Fair P(home)", "n"), ("σ margin", "n"),
                       ("Market margin", "n"), ("Market total", "n"), ("Market price", "n"),
                       ("Difference (margin)", "n"), ("Difference (total)", "n"), ("Source", "")], rows))
    body.append("""
<div class="note"><strong>A fair number is not an edge and not a pick.</strong> With no market number
beside it, a fair line cannot be said to be better or worse than anything. The moment a licensed price
exists, the difference columns fill and the residual schedule starts; until then they stay empty with the
reason attached to each row.</div>

<h2>Price-data policy (decided before any backtest was published)</h2>
""")
    body.append(table([("Policy", ""), ("Question", ""), ("Decision", ""), ("Reason", ""), ("Consequence", ""), ("Source", "")],
                      [[esc(r["policy_id"]), esc(r["question"]),
                        f'<span class="pill p-{"blocked" if r["decision"].startswith("no") else "met"}">{esc(r["decision"])}</span>',
                        esc(r["reason"]), esc(r["consequence_for_publishing"]), a(r["evidence_url"])]
                       for r in pol]))
    body.append("""
<h2>What the order means</h2>
<ul class="tight">
<li><strong>Side first</strong> — home margin in points from the shrunk scoring-differential model plus
2.5 points of home field.</li>
<li><strong>Total second</strong> — league mean total plus both clubs' shrunk offensive deviations minus
both defensive deviations; published in two estimators until a walk-forward comparison separates them.</li>
<li><strong>Moneyline third</strong> — the side probability through a normal CDF with σ fitted on prior
games and bounded between 7 and 25 points by the registration.</li>
</ul>
<p class="tag">All three are arithmetic on official season-to-date scoring. The inputs and their sample
sizes are in <span class="mono">data/nfl_0ce967db/week11_forecasts.csv</span> and in the model-output
ledger, one row per game per candidate.</p>
""")
    return page("Originated lines", "origination.html", "".join(body))


def page_availability() -> str:
    inj = read("availability_week10_read.csv")
    st = read("standings_2026_11_18.csv")
    clubs: dict[str, dict] = {}
    for r in inj:
        c = clubs.setdefault(r["club"], {"n": 0, "Out": 0, "Doubtful": 0, "Questionable": 0, "": 0,
                                         "cov": r["block_coverage"]})
        c["n"] += 1
        c[r["game_status_as_published"]] = c.get(r["game_status_as_published"], 0) + 1
    body = [f"""
<h1>Injuries &amp; depth</h1>
<p class="lead">{len(inj)} player rows read from the official injury hub at
<strong>2026-11-18T03:44Z</strong>, across {len(clubs)} clubs. The hub still publishes
<em>week 10</em>; a request for the week-11 path was served the week-10 page. The remaining clubs are
blank and labelled unread — a blank here is <strong>not</strong> "healthy".</p>
"""]
    body.append(table([("Club", ""), ("Rows read", "n"), ("Out", "n"), ("Doubtful", "n"),
                       ("Questionable", "n"), ("Blank game status", "n"), ("Block coverage", "")],
                      [[esc(k), str(v["n"]), str(v.get("Out", 0)), str(v.get("Doubtful", 0)),
                        str(v.get("Questionable", 0)), str(v.get("", 0)), esc(v["cov"])]
                       for k, v in sorted(clubs.items())]))
    unread = sorted(set(r["club"] for r in st) - set(clubs))
    body.append(f'<div class="note"><strong>{len(unread)} clubs are not in this table because their block '
                f'was not read</strong>: {esc(", ".join(unread))}. They are not injury-free; the page is '
                f'delivered in 8 chunks and 3 were read. Row-level data is below.</div>')
    body.append("<h2>Every row read</h2>")
    body.append(table([("Club", ""), ("Player", ""), ("Pos", ""), ("Injury (as published)", ""),
                       ("Practice", ""), ("Game status", ""), ("Source", "")],
                      [[esc(r["club"]), esc(r["player"]), esc(r["position"]),
                        blank(r["injury_as_published"]), esc(r["practice_code"]),
                        blank(r["game_status_as_published"]), a(r["source_url"], "hub")]
                       for r in inj]))
    body.append("""
<h2>What the rows already prove</h2>
<ul class="tight">
<li><strong>Practice status does not predict game status.</strong> The Jaguars' B.J. Green II is a full
participant and still <span class="mono">Out</span>; the Jets' Garrett Wilson is a full participant and
<span class="mono">Questionable</span>; the Chiefs' Omarr Norman-Lott is limited and <span class="mono">Out</span>.
Any feature that maps practice to availability would be wrong on these rows.</li>
<li><strong>The hub carries non-injury absences.</strong> Two Jaguars rows read
<span class="mono">"Not injury related - resting player"</span> with game status Out. A parser that
counts them as injuries inflates the injury burden.</li>
<li><strong>Only {}+{} of these rows carry a game designation.</strong> The vast majority carry a practice
status and a blank game status, which is why designation counts alone cannot support a replacement model.</li>
</ul>
<h2>What this page cannot tell you — and the exact reason</h2>
""")
    body.append(table([("Question the owner asked", ""), ("Status", ""), ("Why", ""), ("What would clear it", "")], [
        ["Who replaced each unavailable starter?",
         '<span class="pill p-blocked">blocked</span>',
         "the injury hub names designations, never replacements; no depth chart was read this session",
         "one official depth chart per club, dated the same week"],
        ["Who actually started?",
         '<span class="pill p-blocked">blocked</span>',
         "no game book or official starter list was read; designations are not starters",
         "one official game book per game"],
        ["How many snaps did the replacement play?",
         '<span class="pill p-blocked">blocked</span>',
         "no official snap-count table was read",
         "one snap-count table per game"],
        ["Is the depth of the replacement 2nd, 3rd or 4th string?",
         '<span class="pill p-blocked">blocked</span>',
         "depth rank cannot be derived from designations, and deriving it from jersey number, experience or "
         "salary is explicitly rejected by the owner",
         "a depth source verified club by club, or snap counts as the starter proxy"],
        ["Does the injury signal improve the model?",
         '<span class="pill p-not_run">not run</span>',
         "an ablation needs a played game whose pre-kickoff designation and inactive list are both known; "
         "this pack has neither",
         "inactive lists captured on game day, then the paired ablation"],
    ]))
    return page("Injuries & depth", "availability.html", "".join(body))


def page_evidence() -> str:
    slat = read("week11_slate.csv")
    rec = read("corpus_reconciliation.csv")
    st = read("standings_2026_11_18.csv")
    feed = read("results_feed.csv")
    body = [f"""
<h1>Schedule &amp; results</h1>
<p class="lead">The evidence layer: what the official pages say right now, and how the 150-game corpus was
reconciled against the official standings club by club.</p>

<h2>Week 11 fixtures (read 2026-11-18)</h2>
<p>{len(slat)} games. Kickoff time, network and bye clubs are read verbatim. A stadium name is published
only where the official page prints one; the city is published only where the game centre prints it.</p>
"""]
    body.append(table([("ID", ""), ("Fixture", ""), ("Date", ""), ("Kickoff ET", ""), ("Network", ""),
                       ("Event mark", ""), ("Stadium", ""), ("City", ""), ("How the venue was sourced", ""),
                       ("Source", "")],
                      [[esc(r["game_id"]), f'{esc(r["away"])} at {esc(r["home"])}', esc(r["date_et"]),
                        esc(r["kickoff_et"]), esc(r["network"]), blank(r["event_mark_on_card"]),
                        blank(r["venue_stadium"]), blank(r["venue_city"]), esc(r["venue_basis"]),
                        a(r["game_page_url"])] for r in slat]))
    body.append("""
<div class="note"><strong>Venue provenance is weaker than the requirement asks, and the page says so.</strong>
Twelve of the thirteen stadium strings come from the ticket-partner link inside the card
(<span class="mono">destinationAddress.location=…</span>), not from a stadium field. Only Minnesota at
San Francisco was read from a game centre, which prints <span class="mono">Location MEXICO CITY</span> and
<span class="mono">Stadium ESTADIO BANORTE</span>. That is why the city column is blank for the other
twelve.</div>

<h2>Corpus reconciliation: 150 games against the official standings</h2>
<p>Every club's wins, losses, ties, points for and points against were recomputed from the corpus and
compared to the official standings read the same day.</p>
""")
    ok = sum(1 for r in rec if r["record_match"] == "yes" and r["pf_match"] == "yes" and r["pa_match"] == "yes")
    body.append(f'<div class="good"><strong>{ok} of {len(rec)} clubs match on all three checks.</strong> '
                f'Corpus totals 6,923 points for and 6,923 against, as a closed league must. This is the '
                f'strongest internal check available without a per-game official feed.</div>')
    body.append(table([("Club", ""), ("Corpus W-L-T", ""), ("Official W-L-T", ""), ("Corpus PF", "n"),
                       ("Official PF", "n"), ("Corpus PA", "n"), ("Official PA", "n"), ("All match", "")],
                      [[esc(r["club"]), f'{r["corpus_w"]}-{r["corpus_l"]}-{r["corpus_t"]}',
                        f'{r["official_w"]}-{r["official_l"]}-{r["official_t"]}',
                        esc(r["corpus_pf"]), esc(r["official_pf"]), esc(r["corpus_pa"]),
                        esc(r["official_pa"]),
                        "yes" if (r["record_match"] == "yes" and r["pf_match"] == "yes" and r["pa_match"] == "yes")
                        else '<span class="pill p-blocked">no</span>'] for r in rec]))
    body.append("<h2>Standings as read today</h2>")
    body.append(table([("Club", ""), ("Division", ""), ("W", "n"), ("L", "n"), ("T", "n"), ("PF", "n"),
                       ("PA", "n"), ("PPG", "n"), ("PAPG", "n"), ("Week 11", ""), ("Source", "")],
                      [[esc(r["club"]), esc(r["division"]), esc(r["w"]), esc(r["l"]), esc(r["t"]),
                        esc(r["pf"]), esc(r["pa"]), num(r["ppg_computed"], 2), num(r["papg_computed"], 2),
                        esc(r["week11_status"]), a(r["source_url"], "standings")] for r in st]))
    return page("Schedule & results", "evidence.html", "".join(body))


def page_questions() -> str:
    qs = read("questions.csv")
    counts: dict[str, int] = {}
    for q in qs:
        counts[q["answer_status"]] = counts.get(q["answer_status"], 0) + 1
    body = [f"""
<h1>Questions, information and answers</h1>
<p class="lead">The list the owner asked for: what must be settled before a decision is reasonable, what we
already have, what we do not, and — for every gap — the route to closing it. {len(qs)} questions.</p>
"""]
    body.append(table([("Status", ""), ("Count", "n"),
                       ("Meaning", "")],
                      [[f'<span class="pill p-{"met" if k.startswith("answered") else ("blocked" if k.startswith("blocked") else "partially_met")}">{esc(k)}</span>',
                        str(v),
                        esc({"answered_yes": "settled by an official read today",
                             "answered_no": "settled negatively by an official read today",
                             "answered_partially": "partly settled; a sample or a second read is missing",
                             "blocked": "no source exists in this evidence set",
                             "blocked_waiting": "the source exists but has not published yet",
                             "open": "two options remain; not decided",
                             "needs_owner": "only the owner can decide"}.get(k, ""))]
                       for k, v in sorted(counts.items())]))
    rows = []
    for q in qs:
        cls = ("met" if q["answer_status"].startswith("answered") else
               "blocked" if q["answer_status"].startswith("blocked") else "partially_met")
        rows.append([esc(q["question_id"]), esc(q["question"]),
                     f'<span class="pill p-{cls}">{esc(q["answer_status"])}</span>',
                     esc(q["what_we_have"]), esc(q["what_we_lack"]),
                     esc(q["discovery_route"]), esc(q["number_that_would_clear_it"]),
                     esc(q["linked_req"]), a(q["source_url"], "nfl.com")])
    body.append(table([("ID", ""), ("Question", ""), ("Answer status", ""), ("What we have", ""),
                       ("What we lack", ""), ("Discovery route", ""), ("Number that clears it", ""),
                       ("Requirement", ""), ("Source", "")], rows))
    return page("Q / I / A", "questions.html", "".join(body))


def page_suggestions() -> str:
    sug = read("suggestions.csv")
    body = [f"""
<h1>Suggestions</h1>
<p class="lead">Improvements proposed for the owner to review <em>before</em> any of them is implemented.
{len(sug)} entries. Nothing on this page is built, and the decision column is deliberately empty.</p>
<div class="note">This section exists because the owner asked for one: a place to choose the best path
before changes happen. Each row states the decision it would improve, the evidence it needs, and its cost,
so the cheap high-value ones can be separated from the expensive ones.</div>
"""]
    rows = []
    for s in sug:
        rows.append([esc(s["suggestion_id"]), esc(s["suggestion"]), esc(s["what_it_improves"]),
                     esc(s["what_it_needs"]), esc(s["what_it_needs"] and s["cost"]),
                     esc(s["linked_questions"]),
                     '<span class="nb" title="owner decision left blank on purpose">—</span>'])
    body.append(table([("ID", ""), ("Suggestion", ""), ("Decision it improves", ""), ("What it needs", ""),
                       ("Cost", ""), ("Linked", ""), ("Owner decision", "")], rows))
    body.append("""
<h2>If only three are done</h2>
<ul class="tight">
<li><strong>SUG-06 — capture inactive lists on game day.</strong> It is the single largest evidence gap:
it converts the injury report from a list of designations into a measurable play rate, and it is the
prerequisite for the ablation the owner asked for by name.</li>
<li><strong>SUG-07 — read one official game book and publish actual starters.</strong> One read settles
whether starter data is obtainable at all before committing to 272 of them.</li>
<li><strong>SUG-15 — raise the qualification sample from 100 to a full season.</strong> At the measured
effect size, 100 games is very unlikely to separate skill from luck; the interval published on the board
is the evidence for that.</li>
</ul>
""")
    return page("Suggestions", "suggestions.html", "".join(body))


def page_flagged() -> str:
    fl = read("flagged.csv")
    rf = read("repo_findings.csv")
    body = [f"""
<h1>Flagged for review</h1>
<p class="lead">{len(fl)} items. None of them blocks publication — the site publishes them instead, with
their sources, so the owner can review after the fact. {len(rf)} repo-level findings follow.</p>
"""]
    rows = []
    for r in fl:
        sev = {"high": "blocked", "medium": "partially_met", "low": "not_run"}.get(r["severity"], "not_run")
        rows.append([esc(r["flag_id"]), esc(r["kind"]),
                     f'<span class="pill p-{sev}">{esc(r["severity"])}</span>',
                     esc(r["finding"]), esc(r["status"]), a(r["source_url"])])
    body.append(table([("ID", ""), ("Kind", ""), ("Severity", ""), ("Finding", ""), ("Status", ""),
                       ("Source", "")], rows))
    body.append("<h2>Repository findings</h2>")
    body.append(table([("ID", ""), ("Kind", ""), ("Finding", ""), ("Severity", ""), ("Where", "")],
                      [[esc(r["finding_id"]), esc(r["kind"]), esc(r["finding"]), esc(r["severity"]),
                        esc(r["path_or_source"])] for r in rf]))
    return page("Flagged for review", "flagged.html", "".join(body))


def page_sources() -> str:
    log = read("capture_log.csv")
    body = [f"""
<h1>Sources &amp; method</h1>
<p class="lead">Every number on this site traces to one of {len(log)} dated reads of an official page.
This page publishes the read log, the exact rule that decides what may be published, and the two genuine
limitations of the evidence.</p>

<h2>Read log</h2>
"""]
    body.append(table([("Read", ""), ("Official page", ""), ("What was read", ""), ("Clock (UTC)", ""),
                       ("Status", ""), ("Artifact sha256 (first 16)", "")],
                      [[esc(r["read_id"]), a(r["source_url"], "nfl.com"), esc(r["what_was_read"]),
                        esc(r["read_on_utc"]),
                        f'<span class="pill p-{"met" if r["status"].startswith("read_ok") else "partially_met"}">{esc(r["status"])}</span>',
                        f'<span class="mono">{esc(r["artifact_sha256"][:16])}</span>'] for r in log]))
    body.append("""
<h2>The publication rule</h2>
<p>A value is published only if it is (a) text read from the official page named in its source link and
logged above with a clock, or (b) arithmetic on such values with the derivation shown in the row.
Everything else is an empty cell with a flag. Market prices are not published by any official page, so
every price, ROI, CLV and units cell on this site is empty by written policy, not by omission.</p>

<h2>Two limitations, stated plainly</h2>
<div class="note"><strong>1. No raw page bytes were retained.</strong> This sandbox has no network route to
nfl.com from a shell — only GitHub, npm and PyPI are reachable — so official pages were read through a
page-fetch tool that returns text. The sha256 values in the log cover the transcription artifacts written
from that text. They prove the artifacts were not edited afterwards; they cannot independently prove the
page said it. A reader who wants that guarantee must open the linked page themselves.</div>
<div class="note"><strong>2. Reading is manual, not scheduled.</strong> The NFL terms restrict systematic
retrieval of the Services without express written consent. This project therefore performs single manual
reads and does not run a crawler. Any weekly capture, archive or price feed is blocked until consent
exists — see the Q/I/A page, question Q20.</div>

<h2>Reproducing every number</h2>
<ul class="tight">
<li><span class="mono">python3 src/nfl_0ce967db/run.py</span> — rebuilds the results feed, the model
ledger, the scores, the luck panel, the demotion state and the week-11 batch from committed inputs.
No network. Deterministic.</li>
<li><span class="mono">python3 src/nfl_0ce967db/correlate.py</span> — rebuilds the six correlations with
their intervals.</li>
<li><span class="mono">python3 scripts/build_nfl_0ce967db.py</span> — rebuilds these pages.</li>
<li><span class="mono">python3 scripts/check_nfl_0ce967db.py</span> — the verifier: source links, blank
policy, no input controls, registered family size, reconciliation, determinism.</li>
</ul>
<p class="tag">The pre-registration that fixes the model family, thresholds and evaluation protocol was
committed before any model code existed; its hash is cited in every model row.</p>
""")
    return page("Sources & method", "sources.html", "".join(body))


def main() -> int:
    os.makedirs(DOCS, exist_ok=True)
    pages = {
        "index.html": page_index(),
        "readiness.html": page_readiness(),
        "board.html": page_board(),
        "origination.html": page_origination(),
        "availability.html": page_availability(),
        "evidence.html": page_evidence(),
        "questions.html": page_questions(),
        "suggestions.html": page_suggestions(),
        "flagged.html": page_flagged(),
        "sources.html": page_sources(),
    }
    for name, body in pages.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(body)
    print(f"wrote {len(pages)} pages to docs/nfl-0ce967db/")
    if "--check" in sys.argv:
        return subprocess.call([sys.executable, os.path.join(REPO, "scripts", "check_nfl_0ce967db.py")])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
