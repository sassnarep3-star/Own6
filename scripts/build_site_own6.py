#!/usr/bin/env python3
"""Static site generator for the Own6 research dashboard (docs/).

Reads verified CSVs and emits HTML pages where every table row carries at least
one source link (official URL from the data, or the repo data file for computed
rows whose inputs are official-source rows).
"""
import csv, html, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs", "own6")
os.makedirs(DOCS, exist_ok=True)

def rows(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))

def esc(x):
    return html.escape(str(x if x is not None else ""))

def link(url, label=None):
    if not url:
        return ""
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label or url)}</a>'

def table(headers, body_rows, cls="data"):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for r in body_rows:
        cells = "".join(f"<td>{c}</td>" for c in r)
        trs.append(f"<tr>{cells}</tr>")
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'

def badge(text):
    t = str(text).lower()
    cls = "ok" if t in ("pass", "validated", "done") else ("warn" if t in ("tracking", "needs review") else "bad")
    return f'<span class="badge {cls}">{esc(text)}</span>'

STYLES = """
:root{--bg:#0b1020;--card:#121a33;--line:#243056;--txt:#e8edfb;--mut:#93a0c4;--acc:#5b8cff;--ok:#28c76f;--bad:#ff5d5d;--warn:#f7b731}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--txt)}
header{background:linear-gradient(90deg,#10193a,#16224d);border-bottom:1px solid var(--line);padding:18px 26px}
header h1{margin:0;font-size:22px}header p{margin:4px 0 0;color:var(--mut);font-size:13px}
nav{padding:10px 26px;background:#0e1530;border-bottom:1px solid var(--line);display:flex;gap:14px;flex-wrap:wrap}
nav a{color:var(--acc);text-decoration:none;font-size:14px}nav a:hover{text-decoration:underline}
main{padding:22px 26px;max-width:1280px;margin:0 auto}
h2{font-size:19px;margin:26px 0 8px}h3{font-size:16px;margin:18px 0 6px;color:#c6d0f5}
p,li{color:#cfd8f7;font-size:14px}.mut{color:var(--mut);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card .k{font-size:26px;font-weight:700}.card .l{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.tw{overflow:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:10px 0}
table.data{border-collapse:collapse;width:100%;font-size:13px}
table.data th{background:#18224a;color:#aebbf0;text-align:left;padding:9px 10px;position:sticky;top:0}
table.data td{padding:8px 10px;border-top:1px solid var(--line);vertical-align:top}
table.data tr:nth-child(even) td{background:#141d3c}
a{color:var(--acc)}
.badge{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;font-weight:600}
.badge.ok{background:#0f3c25;color:#5ff0a0}.badge.bad{background:#4a1420;color:#ff8f8f}.badge.warn{background:#453411;color:#ffd479}
.note{background:#101a38;border-left:3px solid var(--acc);padding:10px 14px;border-radius:6px;margin:10px 0}
footer{color:var(--mut);font-size:12px;padding:20px 26px;border-top:1px solid var(--line);margin-top:30px}
"""

def page(title, body, active):
    navs = [("index.html","Dashboard"),("data.html","Data"),("lines.html","Lines & Props"),
            ("strategies.html","Strategies"),("validation.html","Validation"),
            ("correlation.html","Correlation"),("flagged.html","Flagged for Review")]
    nav_html = "".join(
        f'<a href="{h}"{" style=font-weight:700" if h==active else ""}>{t}</a>' for h, t in navs)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · Own6</title>
<style>{STYLES}</style></head><body>
<header><h1>Own6 — NBA line-origination research</h1>
<p>Official-source verified data · walk-forward model · gated strategy leaderboard · paper research only (no real wagers)</p></header>
<nav>{nav_html}</nav><main>{body}</main>
<footer>Data cut 2026-11-02 · NBA.com + ESPN official feeds (DraftKings lines, NBA co-official sports betting partner —
<a href="https://pr.nba.com/draftkings-and-fanduel-become-co-official-sports-betting-partners-of-the-nba/" target="_blank" rel="noopener">NBA press release</a>)
· every table row carries a source link · unconfirmable values are blank and flagged · 21+/gambling-problem resources: 1-800-GAMBLER · NBA Terms of Use §9 use concern is a published
flagged item on this sub-site's Flagged page (needs qualified review, non-blocking)</footer></body></html>"""

# ---------- data ----------
standings = rows("standings_2026-27.csv")
ratings = rows("team_ratings_2026-27.csv")
games = rows("games_results_2026-27.csv")
market = rows("market_lines_2026-11-02.csv")
our = rows("our_lines_2026-11-02.csv")
props = rows("player_props_2026-11-02.csv")
flags = rows("flagged_items.csv")
corrs = rows("correlation_findings.csv")
our_by_ev = {r["event_id"]: r for r in our}

# ---------- index ----------
def kpi(k, l, sub=""):
    s = f'<div class="mut">{esc(sub)}</div>' if sub else ""
    return f'<div class="card"><div class="l">{esc(l)}</div><div class="k">{k}</div>{s}</div>'

slate_rows = []
for m in market:
    o = our_by_ev.get(m["event_id"], {})
    matchup = f'{m["away_team"]} @ {m["home_team"]}'
    mk = f'{esc(m["favorite"])} {esc(m["market_spread"])} · O/U {esc(m["market_total"])}'
    mdl = f'{esc(o.get("model_favorite",""))} {esc(o.get("our_spread",""))} · O/U {esc(o.get("our_total",""))}'
    edge = o.get("model_edge_vs_market_fair","")
    edge_s = f'{float(edge)*100:+.1f}%' if edge not in ("", None) else ""
    src = link(m["source_url"], "DK/ESPN")
    slate_rows.append([esc(matchup), mk, mdl, edge_s, badge(o.get("model_vs_market_fav","")), src])

lb_rows = [
    ["S-6","Cross-game 2-leg parlay","2/6","4",badge("TRACKING"),link("../../research/strategies.md","spec")],
    ["S-1","Rating-margin singles","2/6","3",badge("TRACKING"),link("../../research/strategies.md","spec")],
    ["S-3","Rest-adjusted singles","2/6","3",badge("NOT DEPLOYED"),link("../../research/strategies.md","spec")],
    ["S-4","Player-prop single","1/6","2",badge("TRACKING"),link("../../research/strategies.md","spec")],
    ["S-5","Same-game teammate combo","1/6","2",badge("NOT DEPLOYED"),link("../../research/strategies.md","spec")],
    ["S-7","Open→close line-move","1/6","2",badge("TRACKING"),link("../../research/strategies.md","spec")],
    ["S-2","Model totals","1/6","1",badge("NOT DEPLOYED"),link("../../research/strategies.md","spec")],
]
gates_rows = [
    ["G1 Calibration (log-loss CI>0)",badge("FAIL"),'[−0.013, +0.073]',link("../../verification/backtest_metrics.csv","metrics")],
    ["G2 Discrimination ≥55% / n≥100",badge("PARTIAL"),"59.8% @ n=82",link("../../verification/backtest_metrics.csv","metrics")],
    ["G3 Leg correlations measured",badge("PASS"),"r ∈ {0.200, 0.105, −0.422, −0.016}",link("../../research/correlation.md","correlation.md")],
    ["G4 Multiple-testing log",badge("PASS"),"N=1 trials logged",link("../../research/validation.md","validation.md")],
    ["G5 Closing-line value ≥0",badge("BLOCKED"),"no historical odds in sources (flagged)",link("flagged.html","flagged")],
    ["G6 Sample ≥100 graded",badge("PARTIAL"),"82 graded",link("../../verification/backtest_metrics.csv","metrics")],
]
body = f"""
<h2>Dashboard — 2026-11-02</h2>
<div class="cards">
{kpi(len(games),"Official game results","Oct 20 – Nov 1, per-row nba.com links")}
{kpi("213/213","Verification checks","records recompute exactly from results")}
{kpi(len(market),"Tonight's market lines","DraftKings via ESPN, open+current")}
{kpi("0","Validated strategies","no edge claimed — gates honest")}
{kpi(len(flags),"Flagged items","non-blocking, see Flagged page")}
</div>
<div class="note"><b>Status:</b> model v0.1 backtests better than coin-flip and home baselines on
point estimates, but <b>G1 calibration gate is not met</b> (bootstrap CI crosses zero). All strategies
are TRACKING or NOT DEPLOYED. S-2/S-3/S-5 failed outright and are not deployed.</div>

<h2>Leaderboard snapshot (paper rewards: 20/10/5 units)</h2>
{table(["ID","Strategy","Gates passed","Score","Status","Spec"], lb_rows)}

<h2>Tonight's slate — market vs Own6 model</h2>
{table(["Matchup","DraftKings (ESPN feed)","Own6 model v0.1","Edge vs fair","Favs","Source"], slate_rows)}
<p class="mut">Edge = model P(model favourite) − de-vigged market P(favourite); positive = model
thinks the side is underpriced. S-1 requires ≥3% plus gate G1 before any paper allocation — G1 currently fails,
so these are leans only.</p>

<h2>Validation gates</h2>
{table(["Gate","Status","Result","Evidence"], gates_rows)}

<h2>Start here</h2>
<ul>
<li><a href="data.html">Data</a> — standings, ratings, all 92 results (every row sourced)</li>
<li><a href="lines.html">Lines &amp; Props</a> — 15-game market/model table + verified player props</li>
<li><a href="strategies.html">Strategies</a> — pre-registered catalog, leaderboard, rewards</li>
<li><a href="validation.html">Validation</a> — gates, backtest, luck-removal protocol, citations</li>
<li><a href="correlation.html">Correlation</a> — measured dependence for parlays/combos</li>
<li><a href="flagged.html">Flagged for Review</a> — irregularities, blanks, blocked checks</li>
<li>Repo docs: <a href="../../EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a> · <a href="../../COORDINATION.md">COORDINATION.md</a></li>
</ul>"""
open(os.path.join(DOCS, "index.html"), "w").write(page("Dashboard", body, "index.html"))

# ---------- data ----------
st_e = [[esc(r["rank"]), f'{esc(r["team"])} ({esc(r["team_abbr"])})', esc(r["w"]), esc(r["l"]),
         esc(r["win_pct"]), esc(r["gb"]), esc(r["streak"]), link(r["source_url"], "nba.com")]
        for r in standings if r["conference"] == "East"]
st_w = [[esc(r["rank"]), f'{esc(r["team"])} ({esc(r["team_abbr"])})', esc(r["w"]), esc(r["l"]),
         esc(r["win_pct"]), esc(r["gb"]), esc(r["streak"]), link(r["source_url"], "nba.com")]
        for r in standings if r["conference"] == "West"]
rt = [[f'{esc(r["team"])} ({esc(r["team_abbr"])})', esc(r["gp"]), esc(r["off_rtg"]), esc(r["def_rtg"]),
       esc(r["net_rtg"]), esc(r["pace"]), esc(r["ts_pct"]), link(r["source_url"], "nba.com advanced")]
      for r in sorted(ratings, key=lambda x: float(x["net_rtg"]), reverse=True)]
gm = [[esc(r["date"]), f'{esc(r["away_team"])} {esc(r["away_score"])} @ {esc(r["home_team"])} {esc(r["home_score"])}',
       esc(r["ot"] or "—"), link(r["source_url"], "nba.com game")]
      for r in games]
body = f"""
<h2>Data — all rows official-sourced</h2>
<p>Verification: <code>python3 scripts/verify_data.py</code> → <a href="../../verification/verification_report.csv">verification_report.csv</a>
(213/213 pass: every team's W-L recomputed from the results file matches the official standings page exactly).</p>
<h3>Standings — East (NBA.com)</h3>
{table(["#","Team","W","L","Win%","GB","Streak","Source"], st_e)}
<h3>Standings — West (NBA.com)</h3>
{table(["#","Team","W","L","Win%","GB","Streak","Source"], st_w)}
<h3>Team advanced ratings (NBA.com stats)</h3>
{table(["Team","GP","OffRtg","DefRtg","NetRtg","Pace","TS%","Source"], rt)}
<p class="mut">Sorted by NetRtg. Small samples (4–7 games) — shrinkage dominates the model's use of these values.</p>
<h3>Game results, 2026-10-20 → 2026-11-01 (n=92)</h3>
{table(["Date","Score","OT","Source"], gm)}"""
open(os.path.join(DOCS, "data.html"), "w").write(page("Data", body, "data.html"))

# ---------- lines & props ----------
ln = []
for m in market:
    o = our_by_ev.get(m["event_id"], {})
    ln.append([
        esc(m["date"]), f'{esc(m["away_team"])} @ {esc(m["home_team"])}',
        f'{esc(m["favorite"])} {esc(m["market_spread"])}',
        f'{esc(o.get("our_spread",""))} ({esc(o.get("model_favorite",""))})',
        esc(m["market_total"]), esc(o.get("our_total","")),
        f'{esc(m["fav_ml_current"])} / {esc(m["dog_ml_current"])}',
        f'{esc(m["spread_open"])} → {esc(m["market_spread"])}',
        esc(o.get("model_edge_vs_market_fair","")),
        link(m["source_url"], "odds feed")])
pr = []
for p in props:
    pr.append([f'{esc(p["athlete"])} ({esc(p["team"])})', esc(p["market"]),
               esc(p["line_open"]), esc(p["line_current"]),
               esc(p["american_quotes_current_rowA_rowB"]), esc(p["last_updated"]),
               link(p["source_url"], "prop feed")])
body = f"""
<h2>Lines — 2026-11-02 slate</h2>
<p>Market = DraftKings lines as republished by the <b>ESPN odds feed (secondary source — ESPN is
not an NBA-official source)</b>; DraftKings itself is an NBA co-official sports betting partner
(<a href="https://pr.nba.com/draftkings-and-fanduel-become-co-official-sports-betting-partners-of-the-nba/" target="_blank" rel="noopener">NBA announcement</a>).
Official-vs-secondary labeling applies throughout this sub-site.
Own6 columns come from <code>scripts/model.py</code> over official results/ratings; each row's
market cell links the official per-event odds JSON (open + current, single consistent snapshot).</p>
{table(["Date","Matchup","DK spread","Own6 spread (fav)","DK total","Own6 total","DK ML fav/dog","Spread move","Model edge","Source"], ln)}
<div class="note">Favourite agreement 13/15. Model disagreements: <b>WSH@ORL</b> (model WSH +2.3) and
<b>POR@DEN</b> (model POR +2.3) — leans only; S-1 blocked by gate G1. Model totals diverge most on
CHI@PHI (−11.6) and BOS@HOU (+11.8); totals strategy S-2 failed its MAE gate.</div>

<h3>Player props — verified subset (event 401909907, OKC @ CLE)</h3>
{table(["Athlete","Market","Line (open)","Line (current)","Quotes rowA/rowB","Last updated","Source"], pr)}
<div class="note">Identities resolved against official ESPN athlete/roster endpoints. Six feed athlete IDs
could not be resolved and are <a href="flagged.html">withheld and flagged</a> (no inference rule).
Quote sides are unlabeled in the feed → dual quotes published, sides not assigned. SGA projection left
blank (season PPG not collected).</div>"""
open(os.path.join(DOCS, "lines.html"), "w").write(page("Lines & Props", body, "lines.html"))

# ---------- strategies ----------
st_rows = [
 ["S-6","Cross-game 2-leg parlay","Parlays","G3, G4","4",badge("TRACKING"),
  "cross-game r=+0.105 (n=357) measured", "legs inherit S-1's failed G1 → no allocation yet", link("../../research/strategies.md","spec")],
 ["S-1","Rating-margin singles","Singles","G3, G4","3",badge("TRACKING"),
  "G1 FAIL (CI crosses zero); G2/G6 partial @ n=82", "paper lean only; ≥3% edge rule pre-registered", link("../../research/strategies.md","spec")],
 ["S-3","Rest-adjusted singles","Singles","G3, G4","3",badge("NOT DEPLOYED"),
  "G2 failed: own-sample rest r=−0.016 (null)", "literature effect too small for this sample", link("../../research/validation.md","citations")],
 ["S-4","Player-prop single","Player props","G4","2",badge("TRACKING"),
  "Mitchell 22.5 vs official 22.7 Oct avg", "vig eats the 0.2 lean; SGA blank+flagged", link("lines.html","props")],
 ["S-5","Same-game teammate combo","Combos","G4","2",badge("NOT DEPLOYED"),
  "G3 partial (r=−0.422, n=6); G6 unmet", "needs n≥60 (G6)", link("../../research/correlation.md","r")],
 ["S-7","Open→close line-move","Singles","G4","2",badge("TRACKING"),
  "open+current captured for 15 games", "settlement tonight → G5 seed", link("lines.html","moves")],
 ["S-2","Model totals","Singles","G4","1",badge("NOT DEPLOYED"),
  "G2 failed: MAE 16.45 vs 16.80 baseline (tie)", "no deployable edge", link("../../research/strategies.md","spec")],
]
rewards = [["1st","+20 paper units + top leaderboard slot"],["2nd","+10 paper units"],["3rd","+5 paper units"]]
body = f"""
<h2>Strategies — pre-registered catalog &amp; leaderboard</h2>
<p>Full specs, bet rules and gate math: <a href="../../research/strategies.md">research/strategies.md</a>.
Every strategy and its thresholds were written down before results were examined (protocol:
<a href="validation.html">validation</a>). Rewards are paper units — research bankroll, no real wagers.</p>
{table(["ID","Strategy","Category","Gates passed","Score","Status","Key evidence","Deploy rule","Spec"], st_rows)}
<h3>Reward table (monthly)</h3>
{table(["Rank","Reward"], [[badge(r[0]), esc(r[1]), link("../../research/strategies.md","rules")] for r in rewards])}
<h3>Ranking score</h3>
<p>score = 2×gates fully passed − gates failed (untested = neither; partial passes don't count).
Current order: <b>S-6 (4)</b> · S-1, S-3 (3) · S-4, S-5, S-7 (2) · S-2 (1), ties broken by
status tier. Bankroll starts 100 units; ≤1 unit/night while TRACKING; ≤5 units/night only when
VALIDATED (none).</p>
<div class="note"><b>No strategy is validated.</b> The leaderboard ranks <i>evidence</i>, not profit:
the top score today is 4/6 — driven by measured correlation structure and protocol compliance,
not by a demonstrated edge (G1 failed, G5 blocked).</div>"""
open(os.path.join(DOCS, "strategies.html"), "w").write(page("Strategies", body, "strategies.html"))

# ---------- validation ----------
gate_tbl = [
 ["G1 Calibration","log-loss improvement vs expanding home-win baseline, 95% bootstrap CI > 0",badge("FAIL"),
  "mean +0.0312, CI [−0.0130, +0.0733]", link("../../verification/backtest_metrics.csv","metrics")],
 ["G2 Discrimination","sign accuracy ≥55% over ≥100 graded games",badge("PARTIAL"),
  "59.8% at n=82 (threshold needs n≥100)", link("../../verification/backtest_metrics.csv","metrics")],
 ["G3 Correlation structure","measure every leg's pairwise r; joint pricing required",badge("PASS"),
  "4 correlations measured + published", link("correlation.html","correlation")],
 ["G4 Multiple-testing","log all trials; thresholds deflate with N (DSR framing)",badge("PASS"),
  "N=1 (model v0.1) logged here", link("https://www.researchgate.net/publication/286121118_The_Deflated_Sharpe_RatioCorrecting_for_Selection_Bias_BacktestOverfitting_and_Non-Normality","Bailey–LdP 2014")],
 ["G5 Closing-line value","mean CLV ≥ 0 over ≥100 bets",badge("BLOCKED"),
  "historical closing odds unavailable from official sources — flagged; tracking opens 2026-11-02", link("flagged.html","flag")],
 ["G6 Sample size","≥100 graded events to reach VALIDATED",badge("PARTIAL"),
  "82 graded backtest games", link("../../data/backtest_walkforward.csv","game rows")],
]
met = [
 ["Log-loss — model","0.6747",badge("best"),link("../../data/backtest_walkforward.csv","rows")],
 ["Log-loss — coin baseline","0.6932","baseline p=0.5",link("../../data/backtest_walkforward.csv","rows")],
 ["Log-loss — expanding home-win baseline","0.7059","baseline",link("../../data/backtest_walkforward.csv","rows")],
 ["Brier — model / coin","0.6654 / 0.6946","lower better",link("../../verification/backtest_metrics.csv","metrics")],
 ["Straight-up accuracy (model fav)","59.8%","gate ≥55%",link("../../verification/backtest_metrics.csv","metrics")],
 ["r(predicted, actual margin)","0.210","walk-forward",link("../../verification/backtest_metrics.csv","metrics")],
 ["Totals MAE / baseline","16.45 / 16.80","tie → S-2 not deployed",link("../../verification/backtest_metrics.csv","metrics")],
 ["Estimated HCA / margin σ","1.64 pts / 16.48 pts","expanding, official results",link("../../verification/backtest_metrics.csv","metrics")],
 ["Home win rate 2026-27","52.2% (48–44)","small sample vs ~59% norm",link("../../data/games_results_2026-27.csv","results")],
]
body = f"""
<h2>Validation gates &amp; backtest</h2>
<div class="note"><b>Headline:</b> model v0.1 beats both baselines on point estimates, but the
calibration gate (G1) fails because the 95% CI crosses zero. Honest status: no validated edge,
strategies TRACKING/NOT DEPLOYED only.</div>
{table(["Gate","Pre-registered requirement","Status","Result","Evidence"], gate_tbl)}
<h3>Backtest metrics (walk-forward, 82 graded games, warmup 10)</h3>
{table(["Metric","Value","Note","Source"], met)}
<h3>Luck-removal protocol</h3>
<ul>
<li>Walk-forward grading (prior games only) — no look-ahead; code: <code>scripts/model.py</code></li>
<li>Shrinkage k=8 (strength) / k=4 (scoring) toward league average — early-season noise damped</li>
<li>Pre-registration: gates &amp; strategy rules written before results (this page + strategies.md)</li>
<li>Baseline comparisons (coin / expanding home-win / expanding mean) — raw accuracy never trusted</li>
<li>10,000-resample paired bootstrap (seed 42) on log-loss difference; CI crossing zero = fail</li>
<li>Multiple-testing log for DSR-style deflation (currently N=1)</li>
</ul>
<h3>Methodology citations</h3>
<ul>
<li>Bailey &amp; López de Prado (2014), <i>Deflated Sharpe Ratio</i>, JPM 40(5):94–107 —
<a href="https://www.researchgate.net/publication/286121118_The_Deflated_Sharpe_RatioCorrecting_for_Selection_Bias_BacktestOverfitting_and_Non-Normality" target="_blank" rel="noopener">record</a> ·
<a href="https://quantresearch.org/Publications.htm" target="_blank" rel="noopener">author list</a></li>
<li>Closing-line accuracy — Harvard DASH thesis (MLB 1977–2018):
<a href="https://dash.harvard.edu/bitstreams/24950429-b1b7-4372-a029-1b68de1872e3/download" target="_blank" rel="noopener">PDF</a></li>
<li>NFL betting-line performance —
<a href="https://www.researchgate.net/publication/233427163_The_Performance_of_Betting_Lines_for_Predicting_the_Outcome_of_NFL_Games" target="_blank" rel="noopener">Szalkowski &amp; Nelson</a></li>
<li>ML sports-betting systematic review (2024) —
<a href="https://arxiv.org/html/2410.21484v1" target="_blank" rel="noopener">arXiv:2410.21484</a></li>
<li>Pythagorean expectation / margin→wins —
<a href="https://nbaanalytic.com/articles/pythagorean-expectation-nba-standings.html" target="_blank" rel="noopener">NBAAnalytic</a></li>
<li>Rest effects — Entine (Wharton):
<a href="https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Nba.pdf" target="_blank" rel="noopener">PDF</a> ·
Small (NESSIS 2007): <a href="https://www.nessis.org/nessis07/Dylan_Small.pdf" target="_blank" rel="noopener">PDF</a> ·
<a href="https://nbaanalytic.com/articles/rest-back-to-backs-load-management.html" target="_blank" rel="noopener">NBAAnalytic B2B split</a></li>
<li>DraftKings = NBA co-official sports betting partner —
<a href="https://pr.nba.com/draftkings-and-fanduel-become-co-official-sports-betting-partners-of-the-nba/" target="_blank" rel="noopener">NBA press release (2021)</a></li>
</ul>"""
open(os.path.join(DOCS, "validation.html"), "w").write(page("Validation", body, "validation.html"))

# ---------- correlation ----------
cr = []
for c in corrs:
    src = c["source_file"]
    if src.startswith("http"):
        sl = link(src, "source")
    else:
        sl = link("../../" + src if not src.startswith(".") else src, src.split("/")[-1])
    cr.append([esc(c["pair"]), esc(c["interpretation"]), esc(c["n"]), esc(c["pearson_r"]), sl])
body = f"""
<h2>Correlation findings</h2>
<p>Computed from official game rows and ESPN player logs — reproduction data:
<a href="../../data/correlation_findings.csv">correlation_findings.csv</a>. Full narrative:
<a href="../../research/correlation.md">research/correlation.md</a>.</p>
{table(["Pair","Interpretation","n","Pearson r","Source"], cr)}
<h3>What it means for parlays &amp; combos</h3>
<ul>
<li><b>Same-game legs</b> (team totals): r=+0.200 — pace couples them; joint P(both over) exceeds
the independence product. Pricing must use a joint model.</li>
<li><b>Cross-game legs</b>: r=+0.105 (n=357) — weak but non-zero; strict independence slightly
overstates joint win probability for favorite legs.</li>
<li><b>Teammate props</b>: r=−0.422 at n=6 — usage-sharing direction, insufficient sample;
strategy S-5 stays NOT DEPLOYED until n≥60.</li>
<li><b>Rest signal</b>: r=−0.016 (n=76) — null in this sample; S-3 not deployed despite
literature support for a small effect.</li>
</ul>"""
open(os.path.join(DOCS, "correlation.html"), "w").write(page("Correlation", body, "correlation.html"))

# ---------- flagged ----------
fl = [[esc(f["item"]), esc(f["category"]), esc(f["detail"]), badge(f["status"]),
       link(f["source_url"] if f["source_url"].startswith("http") else "../../" + f["source_url"], "source")]
      for f in flags]
body = f"""
<h2>Flagged for Review</h2>
<p>Irregularities, blanks and blocked checks. Per project rules these are published, never
silently reconciled, and <b>do not block</b> merge/deploy. Status: <b>needs review</b>.</p>
{table(["Item","Category","Detail","Status","Source"], fl)}
<h3>Rules applied</h3>
<ul>
<li>Unconfirmable values stay <b>blank</b> and are flagged (e.g., unresolved prop athlete IDs are
withheld from the props table entirely; SGA projection blank).</li>
<li>Official-source conflicts (IND–BKN recap slug vs card) are recorded with both readings; the
authoritative game card value is used for standings-consistency checks, discrepancy flagged.</li>
<li>Failed gates are findings, not secrets: G1 FAIL is itself a flagged row in
<a href="validation.html">Validation</a>.</li>
</ul>"""
open(os.path.join(DOCS, "flagged.html"), "w").write(page("Flagged for Review", body, "flagged.html"))

print("built:", sorted(os.listdir(DOCS)))
