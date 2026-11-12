#!/usr/bin/env python3
"""Build the NFL lines lab pages (docs/nfl/lab/) from the committed JSON artefacts.

No network, no manual input. Every table row rendered here carries at least one
outbound https source link; blank means unverified and stays blank.
"""
from __future__ import annotations

import json
import pathlib
import sys
from html import escape

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl"
OUT = ROOT / "docs" / "nfl" / "lab"

FLAG_SRC = "https://www.nfl.com/legal/terms"
STANDINGS = "https://www.nfl.com/standings/"
INJURIES = "https://www.nfl.com/injuries/"
SCHED9 = "https://www.nfl.com/schedules/2026/by-week/week-9"
SCHED10 = "https://www.nfl.com/schedules/2026/by-week/week-10"
RULES = "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"
REPO = "https://github.com/sassnarep3-star/Own6"
NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm"
SKLEARN = "https://scikit-learn.org/stable/modules/calibration.html"
SCIPY = "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"

NAV = [
    ("index.html", "Dashboard"),
    ("lines.html", "Own lines"),
    ("strategies.html", "Strategies"),
    ("validation.html", "Validation gates"),
    ("correlations.html", "Correlation"),
    ("leaderboard.html", "Leaderboard"),
    ("injuries.html", "Injuries"),
    ("depth.html", "Depth"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("findings.html", "Findings"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged"),
    ("audit.html", "Repo review"),
]

CSS = """:root{--bg:#0b1220;--panel:#121c2e;--panel2:#16233a;--ink:#e9eef7;--mut:#9fb0c9;--line:#26364f;--acc:#38bdf8;--warn:#fbbf24;--bad:#f87171;--ok:#34d399}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:#7dd3fc;text-decoration:none}a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:5;background:rgba(11,18,32,.96);border-bottom:1px solid var(--line);padding:10px 20px}
.brand{font-weight:800;letter-spacing:.12em;color:var(--acc);font-size:13px}
.brand span{color:var(--mut);font-weight:500;letter-spacing:.06em}
nav.main{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:6px}
nav.main a{font-size:12.5px;color:var(--mut);padding:2px 0}
nav.main a.on{color:#fff;border-bottom:2px solid var(--acc)}
main{max-width:1240px;margin:0 auto;padding:26px 20px 70px}
h1{font-size:27px;margin:6px 0 6px;letter-spacing:-.02em}
h2{font-size:19px;margin:30px 0 8px}h3{font-size:15.5px;margin:18px 0 6px}
p.lead{color:#c7d3e4;max-width:900px}
.eyebrow{font-size:11px;letter-spacing:.18em;color:var(--acc);font-weight:800;margin:0 0 4px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin:16px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.card b{display:block;font-size:26px;line-height:1.1}
.card span{color:var(--mut);font-size:12px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:#182741;color:#fff;text-align:left;font-size:11px;letter-spacing:.05em;text-transform:uppercase;padding:8px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:7px 8px;border-bottom:1px solid #1e2c44;vertical-align:top}
tbody tr:nth-child(even){background:#101a2b}
tbody tr:hover{background:#17253a}
td.num{text-align:right;font-variant-numeric:tabular-nums}
td.blank{color:#64748b}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:700;border:1px solid}
.ok{color:var(--ok);border-color:#1f6f52}.bad{color:var(--bad);border-color:#7f2b2b}
.warn{color:var(--warn);border-color:#7a5a10}.mut{color:var(--mut);border-color:#33415c}
.note{background:#0f1a2b;border-left:3px solid var(--acc);padding:10px 14px;border-radius:0 8px 8px 0;color:#c9d6e6;margin:12px 0}
.flagbox{border-left:3px solid var(--bad)}
footer{border-top:1px solid var(--line);margin-top:40px;padding:18px 0;color:var(--mut);font-size:12px}
.small{font-size:12px;color:var(--mut)}
ul.tight{margin:6px 0 6px 18px;padding:0}ul.tight li{margin:3px 0}
code{background:#0c1626;border:1px solid #1f2c44;border-radius:4px;padding:0 4px;font-size:12px}
.bar{height:6px;background:#0c1626;border-radius:3px;overflow:hidden;margin-top:4px}
.bar i{display:block;height:100%;background:var(--acc)}
"""


def L(*path) -> str:
    return "/".join(path)


def load(name):
    return json.loads((DATA / name).read_text())


def page(name: str, title: str, body: str) -> str:
    parts = []
    for href, label in NAV:
        cls = ' class="on"' if href == name else ""
        parts.append(f'<a href="{href}"{cls}>{escape(label)}</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} - Own6 NFL Lab</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<header class="top"><div class="brand">OWN6 <span>/ NFL LINES LAB</span></div>
<nav class="main" aria-label="NFL lab sections">{nav}</nav></header>
<main>
<p class="eyebrow">NFL RESEARCH LAB - EVIDENCE STATE 2026-11-12</p>
<h1>{escape(title)}</h1>
{body}
<footer>Research only. No wagers, stakes, picks or profitability claims. Blank = unverified; never inferred.
Sources are official NFL / club pages unless a row says otherwise. Methods cite NIST, SciPy and scikit-learn for
definitions only. <a href="flagged.html">Flagged for Review</a> lists every unresolved item.</footer>
</main></body></html>
"""


def table(headers, rows, cls=""):
    head = "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
    def cell(c):
        s = str(c)
        return s if s.startswith("<td") else f"<td>{s}</td>"
    body = "".join("<tr>" + "".join(cell(c) for c in r) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table class="{cls}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def a(url, text=None):
    return f'<a href="{escape(url, quote=True)}">{escape(text or url)}</a>'


def tag(kind, text):
    return f'<span class="tag {kind}">{escape(text)}</span>'


def num(x, digits=2, pct=False, sign=False):
    if x is None or x == "":
        return '<td class="blank" aria-label="blank"></td>'
    if pct:
        return f'<td class="num">{"+" if sign and x > 0 else ""}{x*100:.{digits}f}%</td>'
    return f'<td class="num">{"+" if sign and x > 0 else ""}{x:.{digits}f}</td>'


def ci(pair, digits=1, pct=False):
    if not pair:
        return '<td class="blank"></td>'
    lo, hi = pair
    if pct:
        return f'<td class="num">{lo*100:+.{digits}f}% to {hi*100:+.{digits}f}%</td>'
    return f'<td class="num">{lo:+.{digits}f} to {hi:+.{digits}f}</td>'


# ---------------------------------------------------------------- pages
def p_index(s, b, w, c, q, sg):
    cards = "".join([
        f'<div class="card"><b>{s["reconciliation"]["checks"]}</b><span>official-value checks, {s["reconciliation"]["discrepancies"]} discrepancies</span></div>',
        f'<div class="card"><b>{s["qualified_strategies"]}</b><span>qualified strategies (of {s["candidates"]} frozen candidates)</span></div>',
        f'<div class="card"><b>{s["own_lines_published"]}</b><span>Week 10 own lines published, market cells blank</span></div>',
        f'<div class="card"><b>{s["injury_rows_published"]}</b><span>injury rows transcribed from NFL.com</span></div>',
        f'<div class="card"><b>{len([x for x in q["questions"] if x["status"]=="open"])}</b><span>open questions blocking a decision</span></div>',
        f'<div class="card"><b>{len(sg["suggestions"])}</b><span>reviewable suggestions (none auto-applied)</span></div>',
    ])
    body = f"""
<p class="lead">A working lab for originating your own NFL lines: singles, parlays and player-prop combos, each
scored against frozen validation gates. The lab publishes its own lines for the Week 10 slate, the full gate board
with the losing results, the dependence tests that decide whether a combo may be priced, and the injury/depth
deficiency board. <strong>Nothing here is a pick or a claim of profit.</strong></p>
<div class="cards">{cards}</div>

<h2>What is live, and what it proves</h2>
{table(["Area","What you can see","Evidence status","Source"], [
 ["Own lines", f'{s["own_lines_published"]} Week 10 games: model spread, total, moneyline, win probability, and the uncertainty band',
  tag("warn","model only, no market input"), a(SCHED10,"NFL Week 10 schedule") + " / " + a("lines.html","own lines")],
 ["Validation", "10 gates, the frozen thresholds, and the board for every candidate", tag("bad","0 qualify"), a(f"{REPO}/blob/main/src/nfllab/validation.py","validation.py") + " / " + a("validation.html","gate board")],
 ["Correlation", "Measured dependence for spread/over, cross-game pairs, margin/total", tag("ok","measured"), a(f"{REPO}/blob/main/data/nfl/model/correlations.json","correlations.json") + " / " + a("correlations.html","dependence")],
 ["Injuries", f'{s["injury_rows_published"]} Week 10 rows with report status, practice status and injury', tag("ok","official read"), a(INJURIES,"NFL injury report") + " / " + a("injuries.html","injury table") + " / " + a(NIST,"method")],
 ["Depth", f'{s["availability_rows"]} starter-level deficiencies for WAS / NYG / DET from official depth charts', tag("warn","3 of 32 clubs"), a("https://www.detroitlions.com/team/depth-chart","DET depth chart") + " / " + a("depth.html","depth board")],
 ["Questions", f'{len(q["questions"])} questions with the exact evidence that would close each one', tag("mut","register"), a("questions.html","Questions") + " / " + a(NIST,"method")],
 ["Suggestions", f'{len(sg["suggestions"])} ranked suggestions with impact/confidence/effort/risk', tag("mut","review before apply"), a("suggestions.html","Suggestions") + " / " + a(f"{REPO}/blob/main/data/nfl/suggestions.json","register") + " / " + a(f"{REPO}/blob/main/COORDINATION.md","board")],
],)}

<h2>How to use this section</h2>
<div class="grid2">
<div class="panel"><h3>1. Start with the decision, not the table</h3>
<p class="small">Every page that changes a decision (lines, strategies, leaderboard) opens with the gate that would
have to pass for the number to matter. The <a href="questions.html">Questions</a> page lists what is unknown and
what would resolve it; the <a href="suggestions.html">Suggestions</a> page ranks what to build next.</p></div>
<div class="panel"><h3>2. Trust the blanks</h3>
<p class="small">Where a market price is not licensed and verified, the cell is empty. No row is filled to look
complete. The <a href="flagged.html">Flagged for Review</a> page lists each blank with the source that would
settle it.</p></div>
<div class="panel"><h3>3. The model is allowed to lose</h3>
<p class="small">The 2025 holdout is published with its losses: spread bets -1.2% (interval -12.3% to +10.4%),
totals -3.7%, moneyline dogs -7.5%. That is the point. A method that cannot show its failures cannot show skill.</p></div>
<div class="panel"><h3>4. Combos are priced from measured dependence</h3>
<p class="small">The <a href="correlations.html">Correlation</a> page reports phi and a clustered interval for
same-game cover+over, and the observed-vs-independent multiplier. Independence is never assumed silently.</p></div>
</div>

<h2>Executive summary</h2>
<div class="panel">
<ul class="tight">
<li><strong>The signal fails.</strong> A transparent, opponent-adjusted efficiency rating does not beat the closing spread on a season it never saw. Only the downside is statistically distinguishable from zero.</li>
<li><strong>The data is honest but thin.</strong> {s["reconciliation"]["checks"]} official-value checks pass against verbatim NFL.com reads; the historical backtest leans on a community file with no licence (F-N02).</li>
<li><strong>Most of the combo space is data-blocked, not model-blocked.</strong> {s["testable_candidates"]} of {s["candidates"]} candidates can be tested at all; props, opening lines and historical injuries are missing.</li>
<li><strong>The path forward is a capture problem.</strong> Licensed prices, player props, daily depth charts and dated injury archives are the four blockers. Until they exist, no strategy can qualify.</li>
</ul></div>
"""
    return page("index.html", "NFL lines lab - dashboard", body)


def p_lines(w):
    rows = []
    for g in w["games"]:
        rows.append([
            f'{escape(g["gameday"])}<br><span class="small">{escape(g["kickoff_et"])} ET</span>',
            f'{a(g["game_url"], g["away"])}<br><span class="small">{escape(g["away_club"])}</span>',
            f'{a(g["game_url"], g["home"])}<br><span class="small">{escape(g["home_club"])}</span>',
            f'<td class="num">{g["own_spread_home"]:+.1f}</td>',
            f'<td class="num">{g["own_total"]:.1f}</td>',
            f'<td class="num">{g["own_ml_home"]:+.0f}</td>',
            f'<td class="num">{g["own_ml_away"]:+.0f}</td>',
            f'<td class="num">{g["p_home_win"]*100:.1f}%</td>',
            ci(g["spread_interval"], 1),
            '<td class="blank" aria-label="blank"></td>',
            '<td class="blank" aria-label="blank"></td>',
            a(g["game_url"], "NFL"),
        ])
    body = f"""
<p class="lead">The model's own line for every Week 10 game, published before the first kickoff (Thursday 20:15 ET).
Own line = expected margin and total from the opponent-adjusted ratings, with home-field and season decay. The
uncertainty column is the 95% band from the model's parameter error, not a betting range. <strong>Market columns
are intentionally empty</strong> - no licensed price feed exists (F-N01).</p>
<div class="note">Read the band before the number: the Thursday game's own spread is a single figure with a
plus-or-minus six point parameter error. A 2.5-point disagreement with a market price is inside that band.</div>
{table(["Game","Away","Home","Own spread (home)","Own total","Own ML home","Own ML away","P(home win)","Spread 95% band","Market spread","Market total","Source"], rows)}
<h2>How the own line is built</h2>
<div class="grid2">
<div class="panel"><h3>Ratings</h3>
<ul class="tight">
<li>Points for / against, opponent-adjusted by alternating least squares, fitted on every season before the test season only.</li>
<li>Season decay 0.55 per year, so last year counts about half of this year.</li>
<li>Shrinkage 6 games toward league average, so a two-game team is not treated as a full season.</li>
<li>Home field is estimated from the data (about 2.0 points in the window), not hard-coded.</li>
</ul></div>
<div class="panel"><h3>Dispersion</h3>
<ul class="tight">
<li>Margin SD is measured out-of-sample on the holdout season (13.9 points), not from the fit.</li>
<li>Total SD is set 6% wider than margin SD as a stated assumption.</li>
<li>Pushes on whole-number lines are reported separately; they are never split 50/50.</li>
</ul></div>
</div>
<h2>What would make these lines useful</h2>
<p class="small">A verified closing price. With it, every row gets a fair-price comparison, a de-vigged edge, and a
closing-line-value check - which is the only way the line becomes a decision rather than a description. See
<a href="suggestions.html">SG-03</a> and <a href="questions.html">Q03</a>.</p>
"""
    return page("lines.html", "Own lines - Week 10 slate", body)


def p_strategies(b):
    fam = [
        ("S1", "Model spread vs close", "single", "testable", "Home or away side when |model - market| >= 1.5 points after shrink"),
        ("S2", "Model total vs close", "single", "testable", "Over or under when |model total - market| >= 1.5 points"),
        ("S3", "Model moneyline, underdog only", "single", "testable", "Dog when model probability exceeds the implied price by >= 3 points"),
        ("S4", "Line-move fade", "single", "blocked", "Needs an opening-line archive, not just the close"),
        ("S5", "Player prop residual", "single", "blocked", "Needs prop history and prop prices"),
        ("S6", "Same-game parlay (QB yards + WR yards)", "prop combo", "blocked", "Needs player-level outcomes to pair"),
        ("S7", "Cross-game 2-leg parlay", "parlay", "blocked", "Needs both legs' verified prices on the same slate"),
        ("S8", "Injury-shock re-pricing", "single", "blocked", "Needs dated injury archive + pre-news lines"),
    ]
    rows = []
    status = {x["candidate_id"]: x for x in b["gates"]}
    for cid, name, kind, st, rule in fam:
        board = status.get(cid, {})
        rows.append([
            f"<strong>{cid}</strong>", escape(name), escape(kind),
            tag("ok" if st == "testable" else "warn", st),
            escape(rule),
            f'{board.get("gates_passed","-")}/{board.get("gates_total","-")}',
            tag({"qualifies":"ok","blocked":"warn","rejected":"bad"}.get(board.get("status",""), "mut"), board.get("status","-")),
            a(f"{REPO}/blob/main/src/nfllab/harness.py", "harness"),
            a(f"{REPO}/blob/main/src/nfllab/validation.py", "gates"),
        ])
    res = b["results"]
    perf = []
    for sid in ("S1", "S2", "S3"):
        r = res[sid]
        perf.append([f"<strong>{sid}</strong>", f'<td class="num">{r["n_bets"]}</td>', f'<td class="num">{r["n_clusters"]}</td>',
                     num(r["win_rate"], 1, pct=True), num(r["roi"], 2, pct=True, sign=True), ci(r["roi_ci"], 1, pct=True),
                     a(f'{REPO}/blob/main/data/nfl/model/backtest.json', "backtest.json")])
    body = f"""
<p class="lead">Eight candidates are frozen before the run: three single-bet families, one prop family, two
combination families and two that need archives the project does not have. Freezing matters: a candidate invented
after seeing the results cannot be tested. Each candidate must pass all ten gates in
<a href="validation.html">Validation</a> to reach the leaderboard.</p>
<h2>Frozen candidate family</h2>
{table(["ID","Candidate","Type","Data state","Selection rule","Gates passed","Verdict","Rule source","Gate source"], rows)}
<h2>2025 holdout results (the part most sites would hide)</h2>
{table(["ID","Bets","Slate dates","Win rate","ROI per bet","95% clustered interval","Source"], perf)}
<div class="note flagbox">Every interval includes zero, and the moneyline family's point estimate is negative.
Under the frozen rules that is a <strong>rejection</strong>, not a "promising early result". The model is kept
published because a rejected strategy that is honestly measured is more useful than an unmeasured one.</div>
<h2>Why the combos and parlays cannot be tested yet</h2>
<div class="grid2">
<div class="panel"><h3>Prop combos (S5, S6)</h3><p class="small">A prop combo needs paired player-level outcomes: the
same player, the same game, the outcome on both legs. No prop history or prop price was obtained, so the paired
residual file that would feed the copula is empty. See <a href="questions.html">Q08</a>.</p></div>
<div class="panel"><h3>Parlays (S7)</h3><p class="small">A two-leg cross-game parlay needs both legs priced at the
same moment, then a joint probability from measured dependence plus the offered payout. Without verified prices
the only honest output is the dependence study on <a href="correlations.html">Correlation</a>, not a parlay price.</p></div>
</div>
<h2>Sizing, without recommending a bet</h2>
<p class="small">The library can compute a quarter-Kelly stake from a model probability and an offered price, but
publishes no stake because no verified price exists. Sizing an unverified edge is how a research project becomes a
gambling problem. See <a href="flagged.html">F-N01</a>.</p>
"""
    return page("strategies.html", "Strategies - singles, parlays, prop combos", body)


def p_validation(b):
    from importlib import import_module
    sys.path.insert(0, str(ROOT / "src"))
    validation = import_module("nfllab.validation")
    defs = [
        ("G01","Data rights & market-permission audit", validation.gate_rights, "verified licence for every input series", a(FLAG_SRC,"NFL Terms")),
        ("G02","Field-level provenance", None, ">= 99% of rows carry an official https source and a snapshot hash", a(INJURIES,"NFL injury report")),
        ("G03","Chronological walk-forward", None, "fit window strictly before the test window", a(SKLEARN,"scikit-learn calibration")),
        ("G04","Sample floor", None, f">= {validation.MIN_BETS} bets, >= {validation.MIN_EVENTS} games, >= {validation.MIN_CLUSTERS} slate dates", a(NIST,"NIST interval guide")),
        ("G05","Calibration vs market", None, "Brier skill score > 0 with clustered CI above 0", a(SKLEARN,"Brier / calibration")),
        ("G06","Post-vig ROI", None, "clustered bootstrap lower bound > 0", a(NIST,"NIST intervals")),
        ("G07","Closing-line value", None, "de-vigged same-line CLV lower bound > 0", a(f"{REPO}/blob/main/research/VALIDATION_v2.md","Validation v2")),
        ("G08","Multiplicity control", None, "Bonferroni-adjusted p < 0.05 across every tested candidate", a(NIST,"NIST intervals")),
        ("G09","Dependence & joint sample", None, ">= 30 paired observations and a clustered CI for every combo leg", a(SCIPY,"SciPy Pearson")),
        ("G10","Deflated Sharpe ratio", None, "deflated Sharpe > 0 given the number of trials", a(f"{REPO}/blob/main/src/nfllab/validation.py","validation.py")),
    ]
    rows = [[f"<td><strong>{g}</strong></td>", escape(n), escape(t), s] for g, n, _, t, s in defs]
    board = []
    for cand in b["gates"]:
        for g in cand["gates"]:
            src = g.get("source") or f"{REPO}/blob/main/data/nfl/model/backtest.json"
            board.append([cand["candidate_id"], g["gate_id"],
                          tag({"pass":"ok","fail":"bad","blocked":"warn"}[g["status"]], g["status"]),
                          escape(g["observed"]), escape(g["threshold"]), a(src, "source")])
    counts = {}
    for cand in b["gates"]:
        for g in cand["gates"]:
            counts[g["status"]] = counts.get(g["status"], 0) + 1
    body = f"""
<p class="lead">Ten gates, frozen in code before any result was inspected. A strategy qualifies only if every gate
returns <em>pass</em>. A gate that cannot be evaluated returns <em>blocked</em>, never <em>pass</em>. That is why the
leaderboard is empty: {counts.get("blocked",0)} gate evaluations are blocked on missing evidence and
{counts.get("fail",0)} are outright failures, against {counts.get("pass",0)} passes.</p>
<div class="cards">
<div class="card"><b>{counts.get("pass",0)}</b><span>passes</span></div>
<div class="card"><b>{counts.get("fail",0)}</b><span>failures</span></div>
<div class="card"><b>{counts.get("blocked",0)}</b><span>blocked on missing data</span></div>
<div class="card"><b>{len(b["gates"])}</b><span>candidates scored</span></div>
</div>
<h2>Gate definitions</h2>
{table(["Gate","Requirement","Threshold / definition","Method source"], rows)}
<h2>Full gate board - every candidate, every gate</h2>
<p class="small">This is the working table. It is deliberately long: the point is that a reader can see exactly
which gate stops which candidate.</p>
{table(["Candidate","Gate","Status","Observed","Threshold","Source"], board)}
<h2>Reading a "blocked" gate</h2>
<div class="note">Blocked is not a technicality. G07 (closing-line value) is blocked for every candidate because no
opening/closing price sidecar exists; G05 is blocked because no market probability series exists. A future session
that adds a licensed price feed moves these from blocked to pass or fail automatically - the code does not change,
only the evidence does.</div>
"""
    return page("validation.html", "Validation gates - all ten, no exceptions", body)


def p_corr(c):
    c1 = c["C1_same_game_cover_over"]; c2 = c["C2_cross_game_pairs"]; c3 = c["C3_abs_margin_total"]
    rows = []
    if c1.get("available"):
        rows.append(["C1", "Home covers the spread AND the game goes over (same game)",
                     f'<td class="num">{c1["n"]:,}</td>', f'<td class="num">{c1["phi"]:+.3f}</td>',
                     ci(c1["phi_ci"], 3), f'<td class="num">{c1["joint_observed"]*100:.2f}%</td>',
                     f'<td class="num">{c1["joint_if_independent"]*100:.2f}%</td>',
                     f'<td class="num">{c1["ratio_observed_to_independent"]:.3f}x</td>',
                     tag("ok" if "not rejected" in c1["verdict"] else "bad", "independent" if "not rejected" in c1["verdict"] else "dependent"),
                     a(f"{REPO}/blob/main/data/nfl/model/correlations.json","correlations.json")])
    if c2.get("available"):
        rows.append(["C2", "Two legs from different games on the same slate",
                     f'<td class="num">{c2["n"]:,}</td>', f'<td class="num">{c2["phi"]:+.3f}</td>', ci(c2["phi_ci"], 3),
                     '<td class="blank"></td>', '<td class="blank"></td>', '<td class="blank"></td>',
                     tag("warn","noise baseline"), a(f"{REPO}/blob/main/data/nfl/model/correlations.json","correlations.json")])
    if c3.get("available"):
        rows.append(["C3", "Absolute margin vs total points (all games)", f'<td class="num">{c3["n"]:,}</td>',
                     f'<td class="num">{c3["r"]:+.3f}</td>', ci(c3["clustered_ci"], 3),
                     '<td class="blank"></td>', '<td class="blank"></td>', '<td class="blank"></td>',
                     tag("ok","measured"), a(SCIPY,"SciPy pearsonr")])
    combo = c.get("combo_pricing_example", [])
    combo_rows = [[escape(x["method"]),
                   f'<td class="num">{x["joint"]*100:.2f}%</td>' if x["joint"] is not None else '<td class="blank"></td>',
                   f'<td class="num">{x["fair_american"]:+.0f}</td>' if x["fair_american"] is not None else '<td class="blank"></td>',
                   (f'<td class="num">{x["ev_at_offered"]["2.61"]*100:+.1f}% at 2.61</td>' if x.get("ev_at_offered") else '<td class="blank"></td>'),
                   a(SCIPY, "SciPy"),
                   ] for x in combo]
    body = f"""
<p class="lead">Whether a combo can be priced by multiplying its legs is an empirical question, not a house rule.
This page answers it with {c1.get("n", 0):,} historical games, a clustered interval over {c1.get("clusters", 0)}
slate dates, and a Fisher exact test on the paired 2x2 table.</p>
<h2>Dependence studies</h2>
{table(["Study","Pair","Games","Measure","95% clustered interval","Observed joint","If independent","Ratio","Verdict","Source"], rows)}
<div class="note">C1 is the honest answer for the one pair the data can test: phi = {c1.get("phi", 0):+.3f} with an
interval that includes zero, so independence is <em>not rejected</em> - but the observed joint is
{c1.get("ratio_observed_to_independent", 1):.3f}x the independent product, and that ratio is published beside any
combo price rather than hidden.</div>
<h2>Pricing a two-leg combo three ways</h2>
<p class="small">Example: two legs with marginal probabilities 52% and 55%, priced at 2.61 and 2.70 decimal
(the same as +161 and +170). The table shows what the payout must clear under each assumption.</p>
{table(["Method","Joint probability","Fair American price","EV at an offered price","Method source"], combo_rows)}
<div class="note flagbox">The Frechet bounds show the honest range: for these two marginals the joint can be anywhere
from 7% to 52% without any dependence at all. A combo price that looks generous under independence can be a
guaranteed loser under the lower bound. No copula value is shown because no measured rho exists for this pair.</div>
<h2>Rules the lab applies to every combo</h2>
<ul class="tight">
<li><strong>Never multiply without a test.</strong> Independence is a labelled special case, not a default.</li>
<li><strong>Paired residuals, not marginal rates.</strong> The unit of observation is the game, and both legs must be present.</li>
<li><strong>Cluster by slate date.</strong> Multiple bets on one night are not independent draws from the season.</li>
<li><strong>Publish the ratio.</strong> Observed joint divided by independent joint appears next to every price.</li>
<li><strong>Require the sample.</strong> Gate G09 blocks any combo without 30 paired observations and a clustered interval.</li>
</ul>
<h2>What is still unknown</h2>
<p class="small">Player-prop dependence - the kind that actually moves same-game parlays - is untested because no
prop outcomes were obtained (<a href="questions.html">Q08</a>). The only published prop conclusion is that it
cannot be computed yet.</p>
"""
    return page("correlations.html", "Correlation - what may be multiplied", body)


def p_leaderboard(b):
    lb = b["leaderboard"]
    rows = []
    for r in lb:
        rows.append([r["rank"] or "-", f'<td><strong>{r["candidate_id"]}</strong></td>', escape(r["name"]), escape(r["market"]),
                     tag({"qualifies":"ok","blocked":"warn","rejected":"bad"}.get(r["status"],"mut"), r["status"]),
                     f'{r["gates_passed"]}/{r["gates_total"]}',
                     num(r["roi_lower"], 2, pct=True) if r["roi_lower"] is not None else '<td class="blank"></td>',
                     escape(r["reward"] or "none - not qualified"),
                     a(f'{REPO}/blob/main/data/nfl/model/backtest.json', "backtest.json")])
    body = f"""
<p class="lead">A leaderboard only means something if entry is hard. Here entry requires all ten gates; ranking uses
the <strong>lower bound</strong> of the clustered holdout ROI, so a lucky upper tail cannot win. Today the board is
empty, and that is the correct output.</p>
<div class="cards">
<div class="card"><b>0</b><span>qualified entries</span></div>
<div class="card"><b>{len(lb)}</b><span>candidates scored</span></div>
<div class="card"><b>3</b><span>reward tiers defined in code</span></div>
<div class="card"><b>0</b><span>monetary rewards, ever</span></div>
</div>
<h2>Board</h2>
{table(["Rank","ID","Candidate","Market","Status","Gates","ROI lower bound","Reward","Source"], rows)}
<h2>Reward policy (frozen, non-monetary)</h2>
{table(["Tier","Condition","Reward","Revocation","Source"], [
 ["A", "Rank 1 among qualifiers, lower bound > 0", "Research priority slot + independent review", "Automatic if a later holdout season's lower bound turns negative", a(f"{REPO}/blob/main/src/nfllab/validation.py","validation.py")],
 ["B", "Rank 2", "Research priority for the next data budget", "Same", a(f"{REPO}/blob/main/src/nfllab/validation.py","validation.py")],
 ["C", "Rank 3+", "Listed with a dated result", "Same", a(f"{REPO}/blob/main/data/nfl/model/backtest.json","backtest.json")],
 ["-", "Rejected or blocked", "Published with the gate that stopped it", "n/a", a(NIST,"NIST")],
],)}
<div class="note">Why no money: a monetary reward creates pressure to loosen the gates exactly when the evidence is
weakest. Research priority is a real reward inside a research programme and cannot be gamed by variance.</div>
<h2>The rules that keep it honest</h2>
<ul class="tight">
<li><strong>Frozen family.</strong> All candidates are declared before the run; adding one after seeing results is a new, separately-adjusted test.</li>
<li><strong>Lower bound ranking.</strong> Rank by the 5th percentile of the clustered bootstrap, never the point estimate.</li>
<li><strong>Multiplicity.</strong> Bonferroni across every candidate tested, including the failures.</li>
<li><strong>Deflated Sharpe.</strong> The best of eight trials must clear the expected maximum under eight trials.</li>
<li><strong>No promotion on one season.</strong> A single holdout can reject a strategy; it cannot prove one.</li>
</ul>
<p class="small">See <a href="validation.html">Validation</a> for the gate definitions and
<a href="questions.html">Q14</a> for why the ranking rule is what it is.</p>
"""
    return page("leaderboard.html", "Leaderboard - empty by design", body)


def p_injuries(inj_rows):
    counts = {}
    teams = {}
    for r in inj_rows:
        key = r["game_status"] or "(not set)"
        counts[key] = counts.get(key, 0) + 1
        teams.setdefault(r["team"], []).append(r)
    rows = []
    for r in inj_rows:
        gs = r["game_status"]
        cls = "bad" if gs == "Out" else "warn" if gs in ("Doubtful", "Questionable") else "mut"
        rows.append([escape(r["team"]), escape(r["game"]), escape(r["player"]), escape(r["position"]),
                     escape(r["report_injury"]) or '<span class="blank">not listed</span>',
                     escape(r["practice_status"]),
                     tag(cls, gs) if gs else '<span class="blank">not set</span>',
                     a(r["source_url"], "NFL")])
    cards = "".join(f'<div class="card"><b>{v}</b><span>{escape(k)}</span></div>' for k, v in sorted(counts.items(), key=lambda x: -x[1]))
    body = f"""
<p class="lead">Every row below was read from <a href="{INJURIES}">the official NFL injury report</a> for Week 10 of
the 2026 season on 2026-11-12 and transcribed verbatim: team, player, position, listed injury, practice status and
game status. Nothing is inferred. A blank game status means the report had not set one at the time of reading.</p>
<div class="cards">{cards}</div>
<div class="note">Only six rows carry an explicit game status today. This is a normal early-week state, and it is
exactly why an injury model must have a "status not yet set" state instead of guessing from practice
participation (<a href="findings.html">L-06</a>).</div>
<h2>Players listed, by club ({len(teams)} clubs)</h2>
{table(["Team","Game","Player","Pos","Injury","Practice","Game status","Source"], rows)}
<h2>Clubs with nothing listed</h2>
<p class="small">Two groups are absent from the report by construction, not by omission: the four Week 10 byes
(<a href="{SCHED10}">CHI, DEN, PHI, TB</a>) and the two Monday-night clubs the official page shows as
<em>"No Injuries Reported"</em> (LAC, BAL). That accounts for {len(teams)} of the 32 clubs; every other club
appears in the table above.</p>
<h2>From report to decision</h2>
<div class="grid2">
<div class="panel"><h3>What this table can support</h3><ul class="tight">
<li>A confirmed availability list for the Week 10 slate.</li>
<li>A starter/replacement chain for the three clubs with a captured depth chart (<a href="depth.html">Depth</a>).</li>
<li>An honest "unknown" for every player without a game status.</li></ul></div>
<div class="panel"><h3>What it cannot support</h3><ul class="tight">
<li>Points of line value (no historical injury archive; <a href="questions.html">Q10</a>).</li>
<li>Whether practice status predicts game status (no multi-week archive; Q11).</li>
<li>Any prop adjustment (no prop data; F-N07).</li></ul></div>
</div>
"""
    return page("injuries.html", f"Week 10 injury report - {len(inj_rows)} rows", body)


def p_depth(av):
    rows = []
    for r in av["rows"]:
        rows.append([escape(r["team"]), escape(r["unit"]), escape(r["position_slot"]), escape(r["starter"]),
                     escape(r["starter_status"]) or '<span class="blank">not set</span>', escape(r["practice_status"]),
                     escape(r["replacement"]) or '<span class="blank">none published</span>',
                     f'<td class="num">{r["replacement_string"] or ""}</td>',
                     f'<td class="num">{r["deficiency_index"]:.3f}</td>',
                     a(r["source_injury"], "NFL"), a(r["source_depth"], "club")])
    idx = av["team_index"]
    parts = []
    for team in sorted(av["team_index"], key=lambda k: -av["team_index"][k]):
        rows_t = [r for r in av["rows"] if r["team"] == team]
        moved = [r for r in rows_t if r["deficiency_index"] > 0]
        moved.sort(key=lambda r: -r["deficiency_index"])
        if moved:
            top = moved[0]
            detail = "; ".join(
                f'{escape(r["starter"])} ({escape(r["position_slot"])}, '
                f'{escape(r["practice_status"] or r["starter_status"] or "no status").lower()}) '
                f'to {escape(r["replacement"] or "no published backup")}'
                f'{" at string " + str(r["replacement_string"]) if r["replacement_string"] else ""}'
                f', index {r["deficiency_index"]:.4f}'
                for r in moved)
            parts.append(
                f'<p class="small"><strong>{escape(team)} - {av["team_index"][team]:.4f}</strong>: '
                f'{len(moved)} of {len(rows_t)} listed starters carry a non-zero index. {detail}.</p>'
            )
        else:
            parts.append(
                f'<p class="small"><strong>{escape(team)} - {av["team_index"][team]:.4f}</strong>: '
                f'none of the {len(rows_t)} listed starters with a matching injury row carries a non-zero index '
                f'(all are full participants or have a 1-string replacement).</p>'
            )
    narrative = "\n".join(parts)
    body = f"""
<p class="lead">Which backup is playing, and how far down the depth chart is he? This page answers that for the
three clubs whose official depth chart and official injury report were both read this session
(WAS, NYG, DET). It does not guess at the other 29 clubs.</p>
<div class="cards">
<div class="card"><b>{len(av["rows"])}</b><span>starter-level deficiencies</span></div>
<div class="card"><b>{idx["WAS"]:.3f}</b><span>WAS deficiency index</span></div>
<div class="card"><b>{idx["NYG"]:.3f}</b><span>NYG deficiency index</span></div>
<div class="card"><b>{idx["DET"]:.3f}</b><span>DET deficiency index</span></div>
</div>
<h2>Starter / replacement board</h2>
{table(["Team","Unit","Slot","Listed starter","Game status","Practice","Replacement","String","Deficiency","Injury source","Depth source"], rows)}
<h2>How the index works (and what it is not)</h2>
<div class="grid2">
<div class="panel"><h3>The formula</h3>
<p class="small"><code>deficiency = position weight x string penalty x status risk</code></p>
<ul class="tight">
<li><strong>Position weight</strong>: QB 1.00, LT 0.45, RT 0.35, C 0.30, WR 0.35, CB/DE 0.40, S 0.32, LB 0.30, RB 0.30, K 0.20, KR/PR 0.05. A modelling choice, published in full and editable in one dict.</li>
<li><strong>String penalty</strong>: 2nd string 0.35, 3rd 0.62, 4th 0.80 - the cost of replacing a starter with that depth.</li>
<li><strong>Status risk</strong>: Out 1.0, Doubtful 0.75, Questionable 0.45, plus half the practice risk (DNP 0.65, limited 0.30).</li>
</ul></div>
<div class="panel"><h3>What it is not</h3>
<ul class="tight">
<li>Not a measured points value. There is no historical injury archive to regress against (<a href="questions.html">Q10</a>).</li>
<li>Not a snap-share model: no snap counts were obtained.</li>
<li>Not league-wide: 29 clubs are missing (F-N06).</li>
<li>Not stable: a Wednesday practice status is not a Sunday status.</li>
</ul></div>
</div>
<h2>Where each club's index comes from</h2>
{narrative}
<h2>What the index is actually made of</h2>
<p class="small">Only rows with a non-zero index move a club's number. Everything else on the board is a
full-participation starter or a 1-string replacement, and a 1-string replacement carries no penalty in the
published formula - which is a stated limitation, not a finding: losing a starter to a same-position backup may
still matter, and the index cannot see it.</p>
<h2>What would make this league-wide</h2>
<p class="small">A daily capture of the 32 club depth-chart pages (<a href="suggestions.html">SG-04</a>) plus a dated
capture of the injury report (<a href="suggestions.html">SG-05</a>). Those two jobs convert this page from a
demonstration into a table a reviewer could bet a decision on.</p>
"""
    return page("depth.html", "Depth deficiency - starters vs 2nd/3rd/4th string", body)


def p_questions(q):
    rows = []
    for x in q["questions"]:
        cls = {"answered": "ok", "partial": "warn", "open": "bad"}[x["status"]]
        rows.append([f'<td><strong>{x["id"]}</strong></td>', escape(x["topic"]), escape(x["question"]),
                     tag(cls, x["status"]), tag("bad" if x["blocking"] == "yes" else "mut", "blocking" if x["blocking"] == "yes" else "non-blocking"),
                     escape(x["have"]), escape(x["missing"]), escape(x["would_close"]),
                     a(x["source"], "source")])
    body = f"""
<p class="lead">Before any decision can be made reasonably, these questions have to be answered - and if they cannot
be answered, the decision cannot be made. Each row states what is already known, exactly what is missing, what
evidence would close it, and who owns it. Seven of the eighteen are blocking today.</p>
<div class="cards">
<div class="card"><b>{sum(1 for x in q["questions"] if x["status"]=="answered")}</b><span>answered</span></div>
<div class="card"><b>{sum(1 for x in q["questions"] if x["status"]=="partial")}</b><span>partly answered</span></div>
<div class="card"><b>{sum(1 for x in q["questions"] if x["status"]=="open")}</b><span>open</span></div>
<div class="card"><b>{sum(1 for x in q["questions"] if x["blocking"]=="yes")}</b><span>blocking a decision</span></div>
</div>
{table(["ID","Topic","Question","Status","Blocking","What we have","What is missing","What would close it","Source"], rows)}
<h2>The five questions that block everything else</h2>
<div class="panel">
<ul class="tight">
<li><strong>Q01 / Q02 - rights and licence.</strong> Without written permission and a licensed dataset, no derived value can be published as a performance record.</li>
<li><strong>Q03 - verified prices.</strong> Without a book and a timestamp, there is no edge to measure, only an assumption.</li>
<li><strong>Q08 - prop outcomes.</strong> Prop singles, prop combos and same-game parlays cannot be tested at all.</li>
<li><strong>Q10 - injury value.</strong> Without an archive there is no way to size a starter-out adjustment.</li>
<li><strong>Q05 - the model's own skill.</strong> Answered, and the answer is negative: the current signal does not beat the close.</li>
</ul></div>
<h2>How to use this register</h2>
<p class="small">A question is closed by evidence, not by opinion. When a source is found, the row changes status,
the source link is added, and the change is dated. Suggestions on the
<a href="suggestions.html">Suggestions</a> page are ordered by which questions they would close.</p>
"""
    return page("questions.html", "Questions, information and answers", body)


def p_suggestions(sg):
    rows = []
    for x in sg["suggestions"]:
        rows.append([f'<td><strong>{x["id"]}</strong></td>', escape(x["title"]), escape(x["category"]),
                     escape(x["problem"]), escape(x["proposal"]), escape(x["expected_benefit"]),
                     f'<td class="num">{x["impact"]}</td>', f'<td class="num">{x["confidence"]}</td>',
                     f'<td class="num">{x["effort"]}</td>', f'<td class="num">{x["risk"]}</td>',
                     f'<td class="num">{x["priority"]:.2f}</td>',
                     tag("bad" if x["blocks_decision"]=="yes" else "mut", "blocking" if x["blocks_decision"]=="yes" else "optional"),
                     escape(x["owner"]),
                     a(x["source"], "evidence")])
    body = f"""
<p class="lead">Fifteen concrete improvements, each with the problem it solves, the evidence that it would work and
the file it would touch. <strong>Nothing on this page is implemented automatically.</strong> The page exists so a
reviewer can choose the best path before any change lands.</p>
<h2>How suggestions are scored</h2>
{table(["Field","Scale","Meaning","Definition source"], [
 ["Impact", "1-5", "5 = changes whether a decision can be made at all", a(f"{REPO}/blob/main/data/nfl/suggestions.json","suggestions.json")],
 ["Confidence", "1-5", "5 = the evidence is already in this repository", a(f"{REPO}/blob/main/data/nfl/suggestions.json","suggestions.json")],
 ["Effort", "1-5", "5 = a multi-week data contract", a(f"{REPO}/blob/main/data/nfl/suggestions.json","suggestions.json")],
 ["Risk", "1-5", "5 = irreversible or a public commitment", a(f"{REPO}/blob/main/data/nfl/suggestions.json","suggestions.json")],
 ["Priority", "formula", "impact x confidence / (effort x risk) - higher first", a(NIST,"NIST on intervals")],
 ["Gate", "rule", "never let a low-risk item jump a blocking one", a(f"{REPO}/blob/main/COORDINATION.md","COORDINATION.md")],
])}
<h2>The suggestion register</h2>
{table(["ID","Suggestion","Category","Problem","Proposal","Expected benefit","Impact","Conf.","Effort","Risk","Priority","Blocks?","Owner","Evidence"], rows)}
<h2>Review workflow (choose a path, then implement)</h2>
<div class="panel">
<ol class="tight">
<li><strong>Read the top of the register.</strong> SG-01 and SG-06 cost an hour and improve how every other number is read.</li>
<li><strong>Handle the blockers in order.</strong> SG-03 (licensed prices) unblocks CLV, de-vigged fair prices and every ROI statement; it is low priority on the formula only because it is expensive.</li>
<li><strong>Pilot anything with confidence <= 2.</strong> None of the current fifteen is that speculative, but the rule stays.</li>
<li><strong>Record the decision.</strong> Accepted, deferred or rejected - with a date and a reason - in COORDINATION.md.</li>
<li><strong>Implement on a claimed scope.</strong> One session, one branch, one file set; no shared file without a request.</li>
</ol></div>
<h2>What was deliberately not suggested</h2>
<div class="note flagbox">A live odds widget, a "best bets today" card and a public leaderboard with money prizes
were all rejected before scoring. Each requires a licensed price feed this project does not have and each creates
pressure to publish before verification. They are recorded here so the decision is not silently reversed later.</div>
"""
    return page("suggestions.html", "Suggestions - review before implementing", body)


def p_findings(les):
    rows = [[f'<td><strong>{x["id"]}</strong></td>', escape(x["area"]), escape(x["finding"]), escape(x["evidence"]),
             escape(x["implication"]), a(x["source"], "source")] for x in les["lessons"]]
    body = f"""
<p class="lead">Twelve findings from building this lab - including the ones that make the project less impressive
and more useful. Each is tied to the artefact that produced it.</p>
{table(["ID","Area","Finding","Evidence","Implication","Source"], rows)}
<h2>The three findings that matter most</h2>
<div class="grid2">
<div class="panel"><h3>The signal does not beat the close</h3>
<p class="small">A transparent efficiency model lost 1.2% per spread bet on 172 holdout bets, with an interval from
-12.3% to +10.4%. That is not a near miss to be tuned away; it is what an information-free signal looks like after
vig. Finding <strong>L-01</strong>.</p></div>
<div class="panel"><h3>Directional accuracy is not edge</h3>
<p class="small">The model gets the margin sign right 59.9% of the time and still loses money. The market gets it
right 85.3% of the time because it already knows what the model knows. Finding <strong>L-10</strong>.</p></div>
<div class="panel"><h3>Most of the combo space is data-blocked</h3>
<p class="small">Five of eight candidates cannot be evaluated because the archives do not exist: opening lines,
prop outcomes, prop prices and dated injuries. Finding <strong>L-11</strong>.</p></div>
<div class="panel"><h3>Dependence is measurable, and small</h3>
<p class="small">Spread-cover vs over: phi +0.022 over 2,792 games, ratio 1.023. Cross-game pairs show +0.099 at
n=234 with an interval through zero - a useful picture of how noisy parlay samples are. Findings
<strong>L-04</strong> and <strong>L-05</strong>.</p></div>
</div>
"""
    return page("findings.html", "Findings - what the work showed", body)


def p_sources(s, man):
    off = [[f'<strong>{x["id"]}</strong>', a(x["url"], x["title"]), escape(x["publisher"]), escape(x["supports"]),
            escape(x["read_at"])] for x in s["sources"]]
    sec = [[f'<strong>{x["id"]}</strong>', a(x["url"], x["title"]), escape(x["publisher"]),
            escape(x.get("license", "")), escape(x["supports"]), escape(x["read_at"])] for x in s["secondary_sources"]]
    manr = [[f'<strong>{x["source_id"]}</strong>', a(x["url"], x["url"].split("//")[-1][:52]), escape(x["transcribed_to"]),
             f'<td class="num">{x["rows"]}</td>', escape(x["verification"])] for x in man["official_reads"]]
    body = f"""
<p class="lead">Every value on this site comes from a page listed here. Official NFL and club pages are read
directly and transcribed verbatim into <code>data/nfl/raw/</code>; community data is used only for the historical
backtest and is reconciled against the official reads before publication.</p>
<h2>Official sources read this session</h2>
{table(["ID","Source","Publisher","What it supports","Read"], off)}
<h2>Transcription register</h2>
<p class="small">What was taken from each official page, and how it was checked.</p>
{table(["ID","Page","Transcribed to","Rows","Verification"], manr)}
<h2>Secondary and method sources</h2>
{table(["ID","Source","Publisher","Licence","Used for","Read"], sec)}
<h2>Quoted terms that bound this project</h2>
<div class="panel">
<p class="small">NFL.com Terms and Conditions (updated 2024-05-16), section 1.3 - quoted verbatim:</p>
<blockquote class="small" style="border-left:3px solid #38bdf8;margin:8px 0;padding:6px 14px;color:#c9d6e6">
"You may use the Services solely for your own individual non-commercial and informational purposes only. Any other
use, including for any commercial purposes, is strictly prohibited without our express prior written consent.
Systematic retrieval of data or other content from the Services, whether to create or compile, directly or
indirectly, a collection, compilation, database, or directory, is prohibited absent our express prior written
consent." - {a(FLAG_SRC, "nfl.com/legal/terms")}</blockquote>
<p class="small">This is why the lab stores only verbatim transcriptions of the pages it needs for verification,
with URLs, and why no live odds feed or scraping job exists. See <a href="flagged.html">F-N03</a>.</p>
</div>
<h2>Method references</h2>
<p class="small">NIST/SEMATECH e-Handbook on confidence intervals ({a(NIST, "NIST")}), scikit-learn calibration
({a(SKLEARN, "scikit-learn")}), SciPy Pearson correlation ({a(SCIPY, "SciPy")}). These define the methods; they do
not validate any edge, line or correlation value on this site.</p>
"""
    return page("sources.html", "Sources - every value, traced", body)


def p_flagged(fl):
    rows = [[f'<strong>{x["id"]}</strong>', tag({"high":"bad","medium":"warn","low":"mut","info":"mut"}[x["severity"]], x["severity"]),
             escape(x["topic"]), escape(x["item"]), escape(x["detail"]), a(x["source"], "source"), escape(x["status"])] for x in fl["flags"]]
    body = f"""
<p class="lead">Everything unresolved, in one place, with the source that would settle it. A flag never fills a
value. Items here do not block publication of the research framework - they block any claim that depends on them.</p>
<div class="note flagbox">If you review only one page, review this one. It is the list of reasons a number on this
site might be wrong.</div>
{table(["ID","Severity","Topic","Item","Why it is unresolved","Source","Status"], rows)}
<h2>What happens to a flagged item</h2>
<ul class="tight">
<li><strong>It stays blank</strong> in every table that would otherwise need it.</li>
<li><strong>It is linked</strong> from the page it affects, so a reader cannot read a value without knowing its status.</li>
<li><strong>It closes</strong> only when an official or licensed source removes the doubt, and the row records that source and the date.</li>
</ul>
"""
    return page("flagged.html", "Flagged for review - unresolved items", body)


def p_audit(recon, man, meta):
    disc = recon["discrepancies"]
    disc_rows = [[escape(d["check"]), escape(d["key"]), tag("bad" if d["status"] != "pass" else "ok", d["status"]),
                  escape(d["official_value"]), escape(d["community_value"]), a(d["official_url"], "official")] for d in disc]
    body = f"""
<p class="lead">A line-by-line review of the repository and of every value this lab publishes. It records what was
checked, what was found, and what was fixed or flagged. Defects found elsewhere in the repository are listed
too, because a reader deserves to know the state of the whole tree.</p>
<h2>Data reconciliation: {recon["checks_run"]} official-value checks</h2>
<div class="cards">
<div class="card"><b>{recon["checks_run"]}</b><span>checks run</span></div>
<div class="card"><b>{recon["checks_failed"]}</b><span>discrepancies after reconciliation</span></div>
<div class="card"><b>{recon["stats"]["final_games_2026_in_community_file"]}</b><span>final 2026 games reconciled</span></div>
<div class="card"><b>{recon["stats"]["injury_rows_transcribed"]}</b><span>injury rows transcribed</span></div>
</div>
<p class="small">Method: every standings row is re-derived from all final games in the community log (wins, losses,
ties, points for, points against); every Week 9 score is compared to the official page; every Week 10 opponent and
kickoff time is compared. A missing row is reported, never filled. Club-code alias ARI (community file) = AZ
(NFL.com) is the only normalisation applied and it is documented.</p>
{table(["Check","Key","Status","Official value","Community value","Source"], disc_rows) if disc_rows else '<div class="note">No discrepancies remained after the documented alias. The three raw discrepancies found before the alias (Arizona season totals, AZ@SEA Week 9, LA@AZ Week 10) are recorded in <a href="flagged.html">F-N05</a>.</div>'}
<h2>Repository review - line by line</h2>
{table(["ID","Severity","Finding","Evidence","Status","Source"], [
 ["D-01","medium","The full test suite fails on a clean checkout of main (1 test in tests/assurance/test_audit.py) before any NFL file is added.","Reproduced in a fresh worktree at b41bc81: the stored SHA-256 for .gitignore does not match after checkout.","needs review - not caused by this work, not fixed here", a(f"{REPO}/blob/main/tests/assurance/test_audit.py","test_audit.py")],
 ["D-02","medium","The community game log lacked three 2026 rows the official pages show.","AZ season totals, AZ@SEA (W9), LA@AZ (W10) - reported by the reconciliation, not filled.","flagged F-N05", a(SCHED9,"week 9")],
 ["D-03","medium","Historical bets are priced at an assumed -110 with no book and no vig.","backtest.json configuration.bet_price_assumption.","flagged F-N04 - blocks any performance claim", a(f"{REPO}/blob/main/data/nfl/model/backtest.json","backtest.json")],
 ["D-04","low","Two NFL sections exist after PR #66 merged during this build.","Disjoint files; readers may see two entry points.","flagged F-N10 - request R-2 logged", a(f"{REPO}/blob/main/COORDINATION.md","COORDINATION.md")],
 ["D-05","info","The lab depends on a Python environment with numpy and scipy.","requirements-empirical.txt already pins both.","ok", a(f"{REPO}/blob/main/requirements-empirical.txt","requirements")],
])}
<h2>What this review verified</h2>
<ul class="tight">
<li>{man["official_reads"][0]["source_id"]}: all {recon["stats"]["standings_rows_confirmed_by_game_log"]} standings rows re-derived from {recon["stats"]["final_games_2026_in_community_file"]} final games - {a(STANDINGS,"NFL standings")}.</li>
<li>{recon["stats"]["week9_games_official"]} Week 9 finals compared one by one - {a(SCHED9,"Week 9 schedule")}.</li>
<li>{recon["stats"]["week10_games_official"]} Week 10 games compared for opponents, dates and kickoff times - {a(SCHED10,"Week 10 schedule")}.</li>
<li>{recon["stats"]["injury_rows_transcribed"]} injury rows transcribed across {recon["stats"]["injury_teams_transcribed"]} clubs - {a(INJURIES,"injury report")}.</li>
<li>Three club depth charts transcribed slot by slot, published blanks preserved - <a href="https://www.commanders.com/team/depth-chart">WAS</a>, <a href="https://www.giants.com/team/depth-chart">NYG</a>, <a href="https://www.detroitlions.com/team/depth-chart">DET</a>.</li>
<li>The 2026 rule-change table and the Terms section 1.3 quoted verbatim - {a(RULES,"rulebook")}, {a(FLAG_SRC,"terms")}.</li>
</ul>
<h2>Reproduce</h2>
<div class="panel"><p class="small">
<code>python3 scripts/nfl_reconcile.py</code> -> re-runs the {recon["checks_run"]} checks<br>
<code>python3 scripts/nfl_analysis.py</code> -> rebuilds every model artefact<br>
<code>python3 scripts/build_nfl_lab.py</code> -> rebuilds these pages<br>
<code>python3 scripts/check_nfl_lab.py</code> -> fails on a missing source, a filled blank, a broken link or a drifted count<br>
<code>python3 -m pytest -q tests/test_nfl_lab.py</code> -> 12 adversarial unit tests
</p>
<p class="small">Input hash: <code>{meta["sha256"][:32]}...</code> - {meta["rows"]} rows, {meta["bytes"]:,} bytes,
source {a(meta["commit_url"], "nfldata@" + meta["commit"][:8])}.</p></div>
"""
    return page("audit.html", "Repository review - line by line", body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS)
    summary = load("model/summary.json")
    backtest = load("model/backtest.json")
    week10 = load("model/week10.json")
    corr = load("model/correlations.json")
    avail = load("model/availability.json")
    questions = load("questions.json")
    suggestions = load("suggestions.json")
    lessons = load("lessons.json")
    flagged = load("flagged.json")
    sources = load("sources.json")
    manifest = load("source_manifest.json")
    recon = load("model/reconciliation.json")
    meta = load("model/games_2015_2026.meta.json")
    import csv
    with (DATA / "raw" / "injuries_week10_read.csv").open(newline="", encoding="utf-8") as f:
        injuries = list(csv.DictReader(f))

    pages = {
        "index.html": p_index(summary, backtest, week10, corr, questions, suggestions),
        "lines.html": p_lines(week10),
        "strategies.html": p_strategies(backtest),
        "validation.html": p_validation(backtest),
        "correlations.html": p_corr(corr),
        "leaderboard.html": p_leaderboard(backtest),
        "injuries.html": p_injuries(injuries),
        "depth.html": p_depth(avail),
        "questions.html": p_questions(questions),
        "suggestions.html": p_suggestions(suggestions),
        "findings.html": p_findings(lessons),
        "sources.html": p_sources(sources, manifest),
        "flagged.html": p_flagged(flagged),
        "audit.html": p_audit(recon, manifest, meta),
    }
    for name, html in pages.items():
        (OUT / name).write_text(html, encoding="utf-8")
    print(f"build_nfl_lab: {len(pages)} pages -> docs/nfl/lab/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
