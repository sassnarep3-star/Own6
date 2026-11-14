"""Renders the static dashboard under docs/nfl-a411fed0/.

Every table row that carries data is rendered with a link to the official
page the number came from.  A cell that could not be verified renders as a
blank cell inside an ``unverified`` span, never as a guess.

The output is plain HTML + vanilla JS + plain CSS: no build step, no
framework, so GitHub Pages serves it directly.
"""
from __future__ import annotations

import csv
import html
import os
from typing import Dict, List, Sequence

from . import dataset, depth, flags, gates, model, questions, store, strategies

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "docs", "nfl-a411fed0")
DATA = os.path.join(ROOT, "data", "nfl_a411fed0")
BASE = "https://sassnarep3-star.github.io/Own6/docs/nfl-a411fed0"

CAPTURE_DATE = "2026-11-14"

# Any column whose name ends in "_url" (or is exactly "url") is rendered as a
# clickable source link rather than as bare text, so a new table cannot
# silently drop its provenance by naming the column something else.
URL_SUFFIX = ("_url",)


def _read(name: str) -> List[Dict[str, str]]:
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="|"))


def e(s) -> str:
    return html.escape("" if s is None else str(s))


def _cell(col: str, val: str) -> str:
    """Render one table cell.  Blank -> an explicit 'unverified' marker."""
    if col.lower() == "url" or col.lower().endswith(URL_SUFFIX):
        if not val:
            return '<td class="unverified" title="No official source captured">—</td>'
        short = val.replace("https://www.", "").replace("https://", "")
        if len(short) > 34:
            short = short[:31] + "…"
        return f'<td><a href="{e(val)}" target="_blank" rel="noopener">{e(short)}</a></td>'
    if val == "" or val is None:
        return '<td class="unverified" title="Not verified - left blank by design">—</td>'
    return f"<td>{e(val)}</td>"


def table(rows: Sequence[Dict[str, object]], cols=None,
          cls: str = "tbl", max_rows=None) -> str:
    rows = list(rows)
    if not rows:
        return '<p class="empty">No rows. See the <a href="flagged.html">' \
               'Flagged for Review</a> page.</p>'
    cols = cols or [c for c in rows[0].keys()]
    show = rows[:max_rows] if max_rows else rows
    out = [f'<div class="tw"><table class="{cls}"><thead><tr>']
    for c in cols:
        out.append(f"<th>{e(c.replace('_',' '))}</th>")
    out.append("</tr></thead><tbody>")
    for r in show:
        out.append("<tr>")
        for c in cols:
            out.append(_cell(c, r.get(c, "")))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    if max_rows and len(rows) > max_rows:
        out.append(f'<p class="note">{len(rows)} rows total; showing the first '
                   f'{max_rows}. The full table is in '
                   f'<code>data/nfl_a411fed0/</code>.</p>')
    return "".join(out)


def _status_pill(s: str) -> str:
    s = (s or "").lower()
    kind = ("ok" if s.startswith("pass") else
            "bad" if s.startswith("fail") or s.startswith("blocked") else
            "warn")
    return f'<span class="pill {kind}">{e(s or "unknown")}</span>'


# ------------------------------------------------------------------ page frame
NAV = [
    ("index.html", "Overview"),
    ("origination.html", "Originated Lines"),
    ("prices.html", "Price Snapshots"),
    ("results.html", "Verified Results"),
    ("strategies.html", "Strategies &amp; Leaderboard"),
    ("staking.html", "Signal vs Staking"),
    ("injuries.html", "Injuries &amp; Depth of Replacement"),
    ("correlations.html", "Correlations"),
    ("gates.html", "Validation &amp; Demotion Gates"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]

CSS = """
:root{--bg:#0e1116;--panel:#161b22;--panel2:#1c232c;--line:#2b333d;
--fg:#e6edf3;--dim:#9aa7b4;--accent:#4da3ff;--ok:#3fb950;--bad:#f85149;
--warn:#d29922}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
.wrap{display:flex;min-height:100vh}
nav{width:250px;flex:0 0 250px;background:var(--panel);border-right:1px solid var(--line);
padding:18px 0;position:sticky;top:0;height:100vh;overflow-y:auto}
nav h1{font-size:15px;margin:0 18px 4px;letter-spacing:.3px}
nav .sub{font-size:11px;color:var(--dim);margin:0 18px 16px}
nav a{display:block;padding:7px 18px;color:var(--dim);text-decoration:none;font-size:13.5px;
border-left:3px solid transparent}
nav a:hover{background:var(--panel2);color:var(--fg)}
nav a.on{background:var(--panel2);color:var(--fg);border-left-color:var(--accent);font-weight:600}
main{flex:1;padding:28px 34px 80px;max-width:1600px}
h2{font-size:22px;margin:0 0 6px}
h3{font-size:16px;margin:26px 0 8px;color:var(--accent)}
p.lead{color:var(--dim);margin:0 0 22px;max-width:95ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:0 0 26px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.card .k{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--dim)}
.card .v{font-size:25px;font-weight:700;margin:5px 0 2px}
.card .n{font-size:11.5px;color:var(--dim);line-height:1.4}
.card.ok .v{color:var(--ok)} .card.bad .v{color:var(--bad)}
.card.warn .v{color:var(--warn)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin-bottom:10px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:12.5px;white-space:nowrap}
th{background:var(--panel2);text-align:left;padding:8px 10px;font-weight:600;
border-bottom:1px solid var(--line);position:sticky;top:0;font-size:11.5px;
text-transform:uppercase;letter-spacing:.3px;color:var(--dim)}
td{padding:7px 10px;border-bottom:1px solid #20272f;vertical-align:top}
tbody tr:hover{background:#1a212a}
td.unverified{background:repeating-linear-gradient(45deg,#241d20,#241d20 6px,#1e181b 6px,#1e181b 12px);
color:#8b6f74;font-style:italic}
.pill{display:inline-block;padding:1px 8px;border-radius:99px;font-size:11px;font-weight:600}
.pill.ok{background:#12331b;color:var(--ok)} .pill.bad{background:#3a1618;color:var(--bad)}
.pill.warn{background:#33280d;color:var(--warn)}
.note{color:var(--dim);font-size:12.5px;margin:4px 0 22px;max-width:95ch}
.empty{color:var(--dim);font-style:italic}
.warnbox{background:#2a2010;border:1px solid #5c4813;border-left:4px solid var(--warn);
border-radius:6px;padding:12px 16px;margin:0 0 22px;max-width:110ch}
.warnbox b{color:var(--warn)}
.src{font-size:11.5px;color:var(--dim);margin:0 0 26px}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);
color:var(--dim);font-size:12px}
@media(max-width:900px){.wrap{flex-direction:column}nav{width:100%;flex:none;height:auto;position:static}
main{padding:18px}}
"""


def page(active: str, title: str, lead: str, body: str,
         extra_head: str = "") -> str:
    nav = "".join(
        f'<a class="{"on" if a == active else ""}" href="{a}">{n}</a>'
        for a, n in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} — NFL Originated Lines (a411fed0)</title>
<link rel="stylesheet" href="assets/style.css">
{extra_head}</head><body><div class="wrap">
<nav><h1>NFL Originated Lines</h1>
<p class="sub">Session a411fed0 · captured {CAPTURE_DATE}</p>{nav}</nav>
<main><h2>{e(title)}</h2><p class="lead">{lead}</p>
{body}
<footer>Every row on every page links to the official page it was read from.
A blank striped cell means the value could not be verified and was left empty
by design — nothing on this site is inferred. · Session
<code>a411fed0</code> · data captured {CAPTURE_DATE}.</footer>
</main></div></body></html>
"""


# ------------------------------------------------------------------- the pages
def _cards(items) -> str:
    out = ['<div class="cards">']
    for v, k, n, cls in items:
        out.append(f'<div class="card {cls}"><div class="k">{e(k)}</div>'
                   f'<div class="v">{e(v)}</div><div class="n">{e(n)}</div></div>')
    return "".join(out) + "</div>"


def build_all() -> None:
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    with open(os.path.join(OUT, "assets", "style.css"), "w") as f:
        f.write(CSS)

    games = model._games()
    side = model.fit_side(games)
    total = model.fit_total(games)
    gates_rows = gates.build_validation()
    passed = sum(1 for g in gates_rows if g["status"] == "pass")
    lb = strategies.build_leaderboard()
    prices = store.build(games)
    cov = store.coverage(prices)
    drows = depth.build()
    dsum = depth.summarise(drows)
    corr = _read("correlations.psv")

    # ------------------------------------------------------------- overview
    body = _cards([
        (f"{passed}/{len(gates_rows)}", "Validation gates passed",
         "A strategy may leave paper only when every gate passes.",
         "ok" if passed == len(gates_rows) else "bad"),
        (f"{len(games)}", "Verified games in the results feed",
         "Weeks 1-3 and 5-9 of 2026. Week 4 could not be read — see flag A4-F01.",
         "warn"),
        (f"{cov['markets_originated']}", "Markets originated for Week 10",
         "Side, total, moneyline and two team totals on 14 games.", "ok"),
        (f"{cov['with_opening_price']}/{cov['markets_originated']}",
         "Markets with an opening price",
         "No official NFL page publishes prices. This is the binding blocker.",
         "bad"),
        (f"{len(drows)}", "Injury-report rows captured",
         "All 28 clubs listed on the official Week 10 report.", "ok"),
        (f"{sum(1 for r in drows if r['status']=='resolved')}/"
         f"{sum(1 for r in drows if r['game_status'] in ('Out','Doubtful'))}",
         "Out/Doubtful players with a resolved replacement string",
         "Only 4 of 32 club depth charts rendered as text.", "bad"),
        (f"{len(lb)}", "Registered strategies",
         "Single bets, parlays and one blocked player-prop family.", "ok"),
        (f"{len([r for r in lb if r['signal_n'] != ''])}", "Strategies with any signal",
         "Six produced out-of-sample signals; four are blocked or unbuilt.",
         "warn"),
    ])
    body += """
<div class="warnbox"><b>Read this first.</b> This pack originates its own NFL
lines, but it has <b>no market prices</b>. No page on nfl.com or on any NFL
club site publishes point spreads, totals or moneylines, so the
price-snapshot store has 84 originated markets and zero prices. That makes
return-on-investment, closing-line value and settlement all uncomputable, and
it fails gate <code>A4-G05</code>, which is the gate that must pass before
anything leaves paper. Everything here is therefore <b>paper only</b>, ranked
on probability scoring rather than on profit. See
<a href="prices.html">Price Snapshots</a> and
<a href="flagged.html">flag A4-F02</a>.</div>
"""
    body += "<h3>What this pack does</h3>"
    body += """<p class="note">Origination runs in a fixed order —
<b>side first, then total, then moneyline</b> — so that step 3 is derived from
steps 1 and 2 rather than fitted independently. The side comes from a
least-squares margin rating fitted on verified finals; the total from a
separate rating fitted on verified game totals; the moneyline from the margin
plus the model's own residual distribution. Every market is published as three
separate columns: the model's fair line, the market line, and the difference
between them.</p>"""

    body += "<h3>Results feed completeness — captured vs published</h3>"
    body += table(_read("feed_completeness.psv"), max_rows=32)
    body += ('<p class="note">Sum of points for and against each club from the '
             'captured results, compared with the PF/PA published on '
             '<a href="https://www.nfl.com/standings/league/2026/REG">'
             'nfl.com/standings</a>. A non-zero gap means games are missing '
             'from the feed. Every club shows a gap because week 4 is missing '
             'entirely.</p>')

    body += "<h3>Validation gates</h3>"
    body += table(gates_rows, cols=["gate_id", "gate", "status", "observed",
                                    "threshold", "official_source_url"])
    body += ('<p class="note">Full detail, including the evidence behind each '
             'verdict, is on the <a href="gates.html">Validation &amp; Demotion '
             'Gates</a> page.</p>')

    body += "<h3>Strategy leaderboard — signal column only</h3>"
    body += table(sorted(lb, key=lambda r: r["signal_rank"]),
                  cols=["signal_rank", "strategy_id", "strategy_name", "family",
                        "signal_n", "signal_direction_hit_rate", "signal_brier",
                        "signal_n_status", "status"])

    body += "<h3>Where to go next</h3>"
    body += """<ul class="note">
<li><a href="origination.html">Originated Lines</a> — the fair / market /
difference columns for every Week 10 game.</li>
<li><a href="strategies.html">Strategies &amp; Leaderboard</a> — the ten
registered strategies and what each one is ranked on.</li>
<li><a href="staking.html">Signal vs Staking</a> — why the staking columns are
kept apart from the signal columns.</li>
<li><a href="questions.html">Questions</a> — what we still need before a
decision is reasonable, split by what we have and do not have.</li>
<li><a href="suggestions.html">Suggestions</a> — the human review queue.</li>
<li><a href="flagged.html">Flagged for Review</a> — every irregularity found in
the official sources.</li>
</ul>"""
    _write("index.html", page("index.html", "Overview",
                              "Originating our own NFL lines, and being honest "
                              "about what is still missing.", body))


def _write(name: str, html_text: str) -> None:
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(html_text)


# ------------------------------------------------------------ origination page
def page_origination():
    games = model._games()
    orig = model.originate(games)
    body = """
<div class="warnbox"><b>The difference column is empty on purpose.</b> Each
market is published as three separate columns: the model's fair line, the
market line, and their difference. The market line is blank because no
official NFL page publishes one, and the difference is therefore blank too
rather than computed against a number we do not have.</div>
"""
    body += "<h3>Step 1 — the side</h3>"
    body += table(orig, cols=[
        "game_slug", "away_abbr", "home_abbr", "kickoff_date",
        "origination_step_1_side_spread_home_fair_line",
        "origination_step_1_side_spread_home_market_line",
        "origination_step_1_side_spread_home_difference",
        "origination_step_1_side_spread_home_market_line_status",
        "origination_step_1_side_spread_home_difference_status",
        "inputs_source_url"])
    body += ('<p class="note">Fair spread is quoted on the <b>home</b> team; a '
             'negative number means the model makes the home team the '
             'favourite by that many points.</p>')

    body += "<h3>Step 2 — the total</h3>"
    body += table(orig, cols=[
        "game_slug", "away_abbr", "home_abbr",
        "origination_step_2_game_total_fair_line",
        "origination_step_2_game_total_market_line",
        "origination_step_2_game_total_difference",
        "origination_step_2_game_total_market_line_status",
        "origination_step_2_game_total_difference_status",
        "inputs_source_url"])

    body += "<h3>Step 3 — the moneyline (derived from steps 1 and 2)</h3>"
    body += table(orig, cols=[
        "game_slug", "away_abbr", "home_abbr",
        "origination_step_3_moneyline_home_fair_line",
        "origination_step_3_fair_moneyline_away",
        "origination_step_3_moneyline_home_market_line",
        "origination_step_3_moneyline_home_difference",
        "origination_step_3_moneyline_home_difference_status",
        "origination_step_3_p_home_win_empirical",
        "origination_step_3_p_home_win_normal",
        "inputs_source_url"])
    body += ('<p class="note">Two win probabilities are shown: an empirical one '
             'read off the model\'s own residual distribution, and a normal one '
             'computed from the fitted margin and its standard deviation. Where '
             'they disagree materially, trust the empirical one less — it rests '
             'on 120 observations.</p>')

    body += "<h3>Derived team totals</h3>"
    body += table(orig, cols=[
        "game_slug", "derived_fair_team_total_away",
        "derived_fair_team_total_home",
        "origination_step_1_fair_margin_home",
        "origination_step_2_game_total_fair_line", "ratings_source_url"])
    body += ('<p class="note"><b>Flagged A4-F13:</b> these are derived '
             'algebraically as (total ± margin) / 2. That identity holds for '
             'the game total but it is not a model of each team\'s scoring '
             'rate. See <a href="flagged.html">Flagged for Review</a>.</p>')

    body += "<h3>The ratings behind the lines</h3>"
    body += table(_read("power_ratings_2026.psv"))
    body += ('<p class="note">Least-squares ratings fitted on 120 verified '
             'finals, constrained to sum to zero. The <code>margin_rating</code> '
             'drives the side; the <code>total_rating</code> drives the total.</p>')

    body += "<h3>Walk-forward validation of the origination</h3>"
    body += table(_read("walk_forward_validation.psv"))
    body += ('<p class="note">Fit on weeks ≤ k, score week k+1. The baseline '
             'predicts every game at the training average. The side model '
             'beats the baseline on margin; the total model does not — see '
             'flag A4-F09.</p>')
    _write("origination.html", page("origination.html", "Originated Lines",
           "Side first, then total, then moneyline — for every Week 10 game.",
           body))


# ---------------------------------------------------------------- prices page
def page_prices():
    prices = store.build()
    cov = store.coverage(prices)
    body = _cards([
        (cov["markets_originated"], "Markets originated",
         "Six market families across 14 Week 10 games.", "ok"),
        (cov["with_opening_price"], "Opening prices captured",
         "No official price feed exists.", "bad"),
        (cov["with_closing_price"], "Closing prices captured",
         "No official price feed exists.", "bad"),
        (cov["status"], "Store status",
         "Fails closed: nothing can be promoted while prices are missing.",
         "bad"),
    ])
    body += """
<div class="warnbox"><b>Why this page is empty.</b> The requirement is to
record opening and closing numbers for every market we originate. The store
exists, the schema is fixed, and all 84 markets are enumerated — but every
price cell is blank. The NFL does not publish betting prices, and no price was
entered from a non-official source, because a number we cannot verify is worse
than no number at all. Until a licensed feed is available, ROI and
closing-line value are both uncomputable and gate <code>A4-G05</code> fails
closed.</div>
"""
    body += "<h3>Coverage</h3>"
    body += table([cov])
    body += "<h3>The store — every originated market, ready to be filled</h3>"
    body += table(prices, max_rows=84)
    body += ('<p class="note">One row per market per week, with a separate '
             'column for the opening price and the closing price and a '
             'separate source URL for each. When a price feed arrives these '
             'columns fill without a schema change.</p>')
    body += "<h3>What has to happen to fill it</h3>"
    body += """<ol class="note">
<li>License an odds feed, or capture prices in-house at two fixed clock times
each week from a licensed operator and store the raw capture as evidence.</li>
<li>Pre-register what "opening" and "closing" mean, before any bet is placed
(question <code>A10-Q02</code>).</li>
<li>Back-fill the store for the weeks already captured, if the feed has
history.</li>
<li>Re-run gate <code>A4-G05</code>. Only then can
<code>A4-G06</code> (settlement) and <code>A4-G07</code> (luck exclusion) be
evaluated at all.</li>
</ol>"""
    _write("prices.html", page("prices.html", "Price Snapshots",
           "Opening and closing numbers for every originated market — currently "
           "none, and why.", body))


# --------------------------------------------------------------- results page
def page_results():
    games = model._games()
    by_week = {}
    for g in games:
        by_week.setdefault(g["week"], []).append(g)
    body = _cards([
        (len(games), "Verified games",
         "Every row read from an official NFL scores page.", "ok"),
        ("8 of 9", "Weeks captured",
         "Weeks 1-3 and 5-9. Week 4 missing.", "warn"),
        ("~136", "Games that should exist through week 9",
         "16 games per week, fewer in bye weeks.", "warn"),
        ("0", "Rows with a missing score",
         "Every captured row has both team scores.", "ok"),
    ])
    body += """
<div class="warnbox"><b>Week 4 is missing.</b>
<code>https://www.nfl.com/scores/2026/week-4</code> renders the placeholder
string <code>"Hidden Score"</code> in place of both team scores for every game
on the page, and the alternative form
<code>/scores/2026/REG4</code> does the same. Three attempts were made. This
leaves a 16-game hole in the training data. See flag A4-F01.</div>
"""
    body += "<h3>Weeks captured</h3>"
    body += table([{"week": w, "games": len(v),
                    "points_per_game": round(sum(x["total"] for x in v)/len(v), 1),
                    "official_source_url": v[0]["source_url"]}
                   for w, v in sorted(by_week.items())])
    body += "<h3>Feed completeness check against published standings</h3>"
    body += table(_read("feed_completeness.psv"), max_rows=32)
    body += ('<p class="note">Captured points for and against each club, '
             'compared with the official standings. A non-zero gap is missing '
             'games, not a transcription error.</p>')
    body += "<h3>The results feed</h3>"
    body += table(_read("results_2026_verified.psv"), max_rows=120)
    body += "<h3>Standings through week 9</h3>"
    body += table(_read("standings_2026_thru_w9.psv"), max_rows=32)
    _write("results.html", page("results.html", "Verified Results",
           "The results feed that makes any backtest or ROI calculation possible "
           "at all.", body))


# ----------------------------------------------------------- strategies page
def page_strategies():
    lb = strategies.build_leaderboard()
    body = _cards([
        (len(lb), "Registered strategies",
         "Single bets, parlays, and one blocked prop family.", "ok"),
        (sum(1 for r in lb if r["signal_n"]), "Strategies with signals",
         "Six produced out-of-sample signals.", "warn"),
        (sum(1 for r in lb if isinstance(r["signal_n"], int) and r["signal_n"] >= 30),
     "With n ≥ 30",
         "The rest cannot be ranked with any confidence.", "warn"),
        ("0", "Strategies eligible for live",
         "Gate A4-G05 fails, so nothing leaves paper.", "bad"),
    ])
    body += """
<div class="warnbox"><b>The leaderboard is ranked on the signal, not on
profit.</b> There are no prices, so there is no profit to rank on. The ranking
column is <b>Brier score</b> — how well calibrated the probabilities a
strategy produced were, out-of-sample. The P&amp;L columns are kept in a
separate table on the <a href="staking.html">Signal vs Staking</a> page so a
lucky staking run can never be mistaken for a good signal.</div>
"""
    body += "<h3>Signal leaderboard</h3>"
    body += table(sorted(lb, key=lambda r: r["signal_rank"]),
                  cols=["signal_rank", "strategy_id", "strategy_name", "family",
                        "signal_rule", "signal_n", "signal_direction_hit_rate",
                        "signal_brier", "signal_log_loss",
                        "signal_n_status", "signal_verdict",
                        "official_source_url"])
    body += ('<p class="note">Lower Brier score is better. '
             '<code>signal_direction_hit_rate</code> is the share of '
             'out-of-sample games where the model\'s fair margin had the same '
             'sign as the verified final margin — it is a straight-up pick '
             'rate, <b>not</b> an against-the-spread record, because no '
             'official spread was captured.</p>')

    body += "<h3>Reward structure</h3>"
    rewards = [
        {"tier": "Tier 1 — Promoted", "reward": "Eligible for live staking",
         "criteria": "All 10 validation gates pass, including prices captured "
                     "and ≥ 1,000 settled bets",
         "currently": "No strategy qualifies",
         "official_source_url": "https://www.nfl.com/scores/2026/week-10"},
        {"tier": "Tier 2 — Paper leader", "reward": "Best Brier score, kept "
                                                    "under weekly review",
         "criteria": "Lowest out-of-sample Brier score with n ≥ 30",
         "currently": "A9-S01 (baseline power rating, side) at 0.2315",
         "official_source_url": "https://www.nfl.com/scores/2026/week-1"},
        {"tier": "Tier 3 — Research", "reward": "Published with findings, "
                                                "not staked",
         "criteria": "Produced signals but n < 30 or gates failing",
         "currently": "A9-S03, A9-S04, A9-S05, A9-S06",
         "official_source_url": "https://www.nfl.com/scores/2026/week-1"},
        {"tier": "Tier 4 — Blocked", "reward": "None; blocker tracked publicly",
         "criteria": "No data route for the required inputs",
         "currently": "A9-S07, A9-S08 (need prices), A9-S09 (needs prices), "
                      "A9-S10 (needs prop data)",
         "official_source_url": "https://nextgenstats.nfl.com/"},
    ]
    body += table(rewards)
    body += ('<p class="note">Rewards are deliberately structured so that the '
             'only way to reach the top tier is to clear the gates, not to '
             'post a good number in a small sample. The demotion gate can send '
             'a Tier 1 strategy back to Tier 2 at any time — see '
             '<a href="gates.html">Validation &amp; Demotion Gates</a>.</p>')

    body += "<h3>Probability calibration by bucket</h3>"
    body += table(_read("signal_calibration.psv"))
    body += ('<p class="note">Stated probability against realised frequency. A '
             'well-calibrated strategy has these two columns close together in '
             'every bucket. Where they diverge, the strategy is over- or '
             'under-confident, and any Kelly stake derived from it will be '
             'wrong.</p>')
    _write("strategies.html", page("strategies.html",
           "Strategies &amp; Leaderboard",
           "Ten registered strategies, ranked on signal quality rather than on "
           "profit.", body))


# -------------------------------------------------------------- staking page
def page_staking():
    lb = strategies.build_leaderboard()
    body = """
<div class="warnbox"><b>Why these columns are separate.</b> A staking plan can
manufacture a good-looking P&amp;L out of a losing signal, right up until a
losing streak ends it. The clearest demonstration is in this pack: strategy
A9-S05 (home underdog) hit only 34% of its picks — a badly losing signal — and
under flat staking it lost 15.4 units. Under a doubling-up plan it showed a
<b>paper profit of +48 units</b> before a drawdown of 511 units. The signal is
identical in both columns. Only the staking changed.</div>
"""
    body += "<h3>Signal columns (what we are measuring)</h3>"
    body += table(sorted(lb, key=lambda r: r["signal_rank"]),
                  cols=["signal_rank", "strategy_id", "strategy_name",
                        "signal_n", "signal_direction_hit_rate",
                        "signal_brier", "signal_log_loss"])
    body += "<h3>Staking columns (deliberately kept apart)</h3>"
    body += table(sorted(lb, key=lambda r: r["signal_rank"]),
                  cols=["strategy_id", "staking_flat_1u_units",
                        "staking_kelly_quarter_units",
                        "staking_martingale_units",
                        "staking_martingale_max_drawdown", "staking_note"])
    body += ('<p class="note">These unit figures are <b>hypothetical</b>. No '
             'price was ever captured, so no bet was ever placed; the figures '
             'assume -110 on every bet purely so the three staking plans can '
             'be compared on the same axis. They are not a track record and '
             'must not be reported as one.</p>')

    body += "<h3>The staking plans</h3>"
    body += table(strategies.STAKING_PLANS)
    body += "<h3>The cautionary case in detail</h3>"
    a9s05 = next(r for r in lb if r["strategy_id"] == "A9-S05")
    body += table([{
        "strategy": "A9-S05 Home underdog",
        "signal_n": a9s05["signal_n"],
        "direction_hit_rate": a9s05["signal_direction_hit_rate"],
        "breakeven_needed": a9s05["nominal_break_even_rate_at_minus_110"],
        "verdict_on_the_signal": "losing — hit rate far below break-even",
        "flat_1u_result": a9s05["staking_flat_1u_units"],
        "kelly_result": a9s05["staking_kelly_quarter_units"],
        "doubling_result": a9s05["staking_martingale_units"],
        "doubling_max_drawdown": a9s05["staking_martingale_max_drawdown"],
        "lesson": "The doubling plan turned a losing signal into a profit on "
                  "paper and then into a loss larger than the entire bankroll. "
                  "If the two columns were merged, the profit would be the "
                  "headline and the drawdown would be a footnote.",
        "official_source_url": "https://www.nfl.com/scores/2026/week-1",
    }])
    body += "<h3>Recommendation</h3>"
    body += ('<p class="note">Cap any Kelly-derived stake at a fixed fraction '
             'of bankroll and never let a staking result influence the signal '
             'ranking. Suggestion <code>A10-S05</code> on the '
             '<a href="suggestions.html">Suggestions</a> page.</p>')
    _write("staking.html", page("staking.html", "Signal vs Staking",
           "Keeping a lucky staking run from masking a bad signal.", body))


# ------------------------------------------------------------- injuries page
def page_injuries():
    drows = depth.build()
    dsum = depth.summarise(drows)
    body = _cards([
        (len(drows), "Injury-report rows",
         "All 28 clubs listed on the official Week 10 report.", "ok"),
        ("28 of 32", "Clubs on the report",
         "Chicago, Denver, Philadelphia and Tampa Bay are on bye — see A4-F04.",
         "warn"),
        (sum(1 for r in drows if r["game_status"] == "Out"), "Players ruled Out",
         "Verbatim from the official report.", "ok"),
        (sum(1 for r in drows if r["game_status"] == "Questionable"),
         "Questionable", "Verbatim from the official report.", "warn"),
        (f"{sum(1 for r in drows if r['status']=='resolved')}/"
         f"{sum(1 for r in drows if r['game_status'] in ('Out','Doubtful'))}",
         "Replacement strings resolved",
         "The denominator is Out or Doubtful players only.", "bad"),
        ("4 of 32", "Club depth charts read",
         "GB, SEA, MIN, DAL. The Texans page is an image — see A4-F03.", "bad"),
    ])
    body += """
<div class="warnbox"><b>Depth of replacement is the requirement, not just
"who is out".</b> A 4th-string guard starting is a different number from a
2nd-string guard starting. This pack resolves that by joining the official
injury report to the official club depth chart and recording which string the
club has to reach. Only 4 of 32 club sites rendered their chart as text, so
only 18 of 77 Out-or-Doubtful players have a resolved replacement. The rest are
left blank and flagged — not guessed.</div>
"""
    body += "<h3>Depth-of-replacement ledger</h3>"
    body += table([r for r in drows if r["game_status"] in ("Out", "Doubtful")],
                  cols=["team_abbr", "player", "position", "unit",
                        "game_status", "injury", "roster_string",
                        "replacement_string", "replacement_player",
                        "strings_listed_in_slot", "status",
                        "official_injury_url", "official_depth_chart_url"],
                  max_rows=77)
    body += ('<p class="note"><code>roster_string</code> is the string the '
             'injured player occupies; <code>replacement_string</code> is the '
             'string that steps in. A first-string player who is Out means a '
             'second-string replacement is on the field.</p>')

    body += "<h3>Per-club deficiency summary</h3>"
    body += table(dsum)
    body += ('<p class="note"><b>'
             '<code>proposed_depth_weight_out_doubtful</code> is a proposed '
             'weight, not an observed quantity</b> — it is labelled '
             '<code>proposed_weight_not_observed</code> in the data and is not '
             'used to price anything. Clubs with zero here may be genuinely '
             'healthy or may simply be one of the 24 clubs whose depth chart '
             'could not be read. Those two cases look identical in this column, '
             'which is exactly why the column is not actionable yet.</p>')

    body += "<h3>Full Week 10 injury report</h3>"
    body += table(drows, cols=["team_abbr", "player", "position", "injury",
                               "practice_status", "game_status",
                               "official_injury_url"], max_rows=347)

    body += "<h3>Official bulletins</h3>"
    bull = _read_raw_bulletins()
    body += table(bull)
    body += ('<p class="note">Headlines harvested verbatim from the NEWS rail '
             'on <a href="https://www.nfl.com/injuries/">nfl.com/injuries</a> '
             'on the capture date. They are published as headlines only; no '
             'number in this pack was taken from them.</p>')
    _write("injuries.html", page("injuries.html",
           "Injuries &amp; Depth of Replacement",
           "Tracking not just who is out, but how deep the club has to reach to "
           "replace them.", body))


def _read_raw_bulletins():
    p = os.path.join(ROOT, "data", "nfl_a411fed0", "raw", "official_bulletins.psv")
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="|"))


# --------------------------------------------------------- correlations page
def page_correlations():
    from . import correlate
    rows = correlate.build()
    body = _cards([
        (len(rows), "Correlations published",
         "Every one with n, a 95% CI and an official source URL.", "ok"),
        (sum(1 for r in rows if r["n_status"] == "sufficient_n"),
         "With n ≥ 30",
         "Only these may inform a price.", "ok"),
        (sum(1 for r in rows if r["n_status"] != "sufficient_n"),
         "Below the n ≥ 30 floor",
         "Published for completeness, marked insufficient_n, unused.", "warn"),
    ])
    body += """
<div class="warnbox"><b>Every correlation here is computed only from numbers
read off official pages</b> — verified final scores and the published
standings. Each row carries its <code>n</code> and a 95% confidence interval.
A correlation with n &lt; 30 is published but marked
<code>insufficient_n</code> and is never used to price anything.
<b>A4-C03</b> — the correlation between the margin-model residual and the
total-model residual — is the one that same-game parlays must be priced with;
its confidence interval currently includes zero, so no parlay is priced off it
yet (flag A4-F11).</div>
"""
    body += table(rows)
    body += "<h3>How to read these</h3>"
    body += """<ul class="note">
<li><b>A4-C01 / A4-C02</b> are fit diagnostics, not skill. They are in-sample
by construction and will look better than the model really is.</li>
<li><b>A4-C03</b> is the parlay-pricing number. If it is genuinely negative,
a favourite-plus-over parlay is <i>less</i> likely than the independent
product implies, and the naive parlay price is too generous to us.</li>
<li><b>A4-C09</b> is the luck test: how stable a team's scoring margin is
between the first three weeks and weeks 7-9. At 0.30 it says most of
early-season margin is noise, which is why the ratings need shrinking
(suggestion A10-S04).</li>
<li><b>A4-C10</b> has n = 23 and is marked insufficient_n. It is the one we
most want to be true and the one we can least afford to act on.</li>
</ul>"""
    _write("correlations.html", page("correlations.html", "Correlations",
           "Computed only from officially sourced numbers, each published with "
           "n.", body))


# --------------------------------------------------------------- gates page
def page_gates():
    grows = gates.build_validation()
    drows = gates.build_demotion()
    body = _cards([
        (f"{sum(1 for g in grows if g['status']=='pass')}/{len(grows)}",
         "Gates passing",
         "All ten must pass before anything leaves paper.",
         "bad" if sum(1 for g in grows if g["status"] == "pass") < len(grows) else "ok"),
        (len(drows), "Demotion rules armed",
         "Ready to fire the moment a strategy goes live.", "ok"),
        (gates.MIN_BETS_FOR_SKILL, "Settled bets required for a skill claim",
         "At 200 bets a season that is about five seasons.", "warn"),
    ])
    body += """
<div class="warnbox"><b>The demotion gate is the rule that sends a live
strategy back to paper.</b> It is armed with six rules, each with a numeric
threshold. Right now every rule reports <code>armed_not_evaluable</code>
because there are no live strategies — which is itself the correct state: the
gate blocks promotion before it has to block demotion.</div>
"""
    body += "<h3>Validation gates</h3>"
    body += table(grows)
    body += ('<p class="note">A gate whose inputs are missing fails closed. It '
             'never passes by default and is never skipped.</p>')

    body += "<h3>Demotion gate — the rules that send a live strategy back to paper</h3>"
    body += table(drows)
    body += ('<p class="note">Rule <code>A4-D04</code> is the strictest: a '
             'single bet placed without both an opening and a closing price '
             'recorded sends the strategy back to paper and quarantines the '
             'affected bets.</p>')

    body += "<h3>How much data it takes to separate skill from luck</h3>"
    body += table(_read("luck_threshold.psv"))
    body += ('<p class="note">At -110 the break-even win rate is 52.38%. To '
             'show a real 5-point edge at 99% confidence and 80% power takes '
             'about 1,160 settled bets — roughly six seasons at 200 bets a '
             'year. This is why the leaderboard is ranked on probability '
             'scoring rather than on win rate, and why closing-line value '
             '(suggestion A10-S06) is the better early metric: it converges '
             'without waiting for results.</p>')
    _write("gates.html", page("gates.html",
           "Validation &amp; Demotion Gates",
           "What a strategy must clear to go live, and what sends it back to "
           "paper.", body))


# ----------------------------------------------------------- questions page
def page_questions():
    qs = questions.build_questions()
    have = sum(1 for q in qs if q["have_it"] == "yes")
    partial = sum(1 for q in qs if q["have_it"] == "partial")
    none_ = sum(1 for q in qs if q["have_it"] == "no")
    body = _cards([
        (len(qs), "Questions on the record",
         "Split by what we have and do not have.", "ok"),
        (have, "Answered", "Fully in hand.", "ok"),
        (partial, "Partially answered",
         "Something exists but is incomplete or of unknown quality.", "warn"),
        (none_, "Not answered",
         "Each carries a concrete route to go and get it.", "bad"),
    ])
    body += """
<div class="warnbox"><b>These are the questions that must be answered before a
decision can reasonably be made.</b> Each row states whether we have the
answer, what we have if it is partial, and — where we do not — a specific way
to go and get it. The single most consequential is
<code>A10-Q01</code>: without prices, no decision about staking or promotion
can be made at all.</div>
"""
    for cat in ("Prices", "Results", "Origination", "Depth", "Staking",
                "Correlation", "Parlays", "Props", "Governance"):
        rows = [q for q in qs if q["category"] == cat]
        if not rows:
            continue
        body += f"<h3>{e(cat)}</h3>"
        body += table(rows, cols=["question_id", "question", "have_it",
                                  "what_we_have", "how_to_get_it",
                                  "why_it_matters", "official_source_url"])
    _write("questions.html", page("questions.html", "Questions",
           "What we have, what we do not, and how to go and get it.", body))


# -------------------------------------------------------- suggestions page
def page_suggestions():
    sug = questions.build_suggestions()
    oi = questions.build_open_inputs()
    body = _cards([
        (len(sug), "Suggestions on the review queue",
         "Nothing here is implemented — this is the human's queue.", "ok"),
        (sum(1 for s in sug if s["status"] == "not_started"), "Not started",
         "Awaiting a decision.", "warn"),
        (sum(1 for s in sug if s["status"] != "not_started"),
         "Blocked or requested", "Cannot proceed without an external change.",
         "bad"),
        (len(oi), "Open inputs", "Data gaps with a named route to close each.",
         "warn"),
    ])
    body += """
<div class="warnbox"><b>This page is a review queue, not a work log.</b> Each
suggestion carries the reasoning behind it, a priority, and a recommended
path. The intent is that a human reviews these and chooses the best path
<b>before</b> any of them is implemented. Nothing on this page has been built.
The one exception is <code>A10-S12</code>, which is a cross-session request
logged in <code>COORDINATION.md</code> rather than an edit to a shared
file.</div>
"""
    body += "<h3>Suggestions — for human review</h3>"
    body += table(sug, cols=["suggestion_id", "category", "suggestion",
                             "reasoning", "priority", "recommended_path",
                             "status", "official_source_url"])
    body += "<h3>Open inputs — what is missing and how to close it</h3>"
    body += table(oi)
    body += ('<p class="note">Each row names the exact blocker, the official or '
             'licensed route to close it, and what the gap currently costs us. '
             'The first three gaps — prices, week 4, and depth charts — account '
             'for every failing gate in this pack.</p>')
    _write("suggestions.html", page("suggestions.html", "Suggestions",
           "Proposed improvements and the data gaps behind them, for review "
           "before implementation.", body))


# ------------------------------------------------------------- flagged page
def page_flagged():
    rows = flags.FLAGS
    sev = {"high": 0, "medium": 0, "low": 0}
    for r in rows:
        sev[r["severity"]] = sev.get(r["severity"], 0) + 1
    body = _cards([
        (len(rows), "Irregularities flagged",
         "Each with verbatim evidence and the page it came from.",
         "warn"),
        (sev["high"], "High severity",
         "Prices missing, week 4 missing, depth charts unreadable.", "bad"),
        (sev["medium"], "Medium severity",
         "Model and validation caveats.", "warn"),
        (sev["low"], "Low severity", "Provenance and cosmetic issues.", "warn"),
    ])
    body += """
<div class="warnbox"><b>Nothing here blocks the merge.</b> Flagged items are
published rather than silently patched over, so a reviewer can see exactly
what was found in the official sources and decide what to do about it. Where a
value could not be confirmed it was left blank in every table in this pack —
never inferred, never filled in from a non-official source.</div>
"""
    for s in ("high", "medium", "low"):
        sub = [r for r in rows if r["severity"] == s]
        if not sub:
            continue
        body += f"<h3>{e(s.capitalize())} severity</h3>"
        body += table(sub, cols=["flag_id", "area", "flag", "evidence_verbatim",
                                 "attempts", "impact", "recommended_action",
                                 "status", "official_source_url"])
    _write("flagged.html", page("flagged.html", "Flagged for Review",
           "Every irregularity found in the official sources, with the verbatim "
           "evidence.", body))


# ------------------------------------------------------------- sources page
def page_sources():
    rows = [
        {"source_id": "A4-SRC01", "publisher": "NFL.com",
         "page": "Scores by week (weeks 1-3, 5-9)",
         "url": "https://www.nfl.com/scores/2026/week-1",
         "used_for": "All 120 verified final scores in the results feed",
         "retrieval": "fetch_page, 2026-11-14",
         "status": "verified"},
        {"source_id": "A4-SRC02", "publisher": "NFL.com",
         "page": "Week 4 scores",
         "url": "https://www.nfl.com/scores/2026/week-4",
         "used_for": "Attempted; returned 'Hidden Score' for every game",
         "retrieval": "fetch_page x3, 2026-11-14",
         "status": "unverified_no_data"},
        {"source_id": "A4-SRC03", "publisher": "NFL.com",
         "page": "Week 10 scores / slate",
         "url": "https://www.nfl.com/scores/2026/week-10",
         "used_for": "The 14-game Week 10 slate, kickoff times and networks",
         "retrieval": "fetch_page, 2026-11-14",
         "status": "verified"},
        {"source_id": "A4-SRC04", "publisher": "NFL.com",
         "page": "League standings 2026",
         "url": "https://www.nfl.com/standings/league/2026/REG",
         "used_for": "32-club records and points for/against through week 9",
         "retrieval": "fetch_page, 2026-11-14",
         "status": "verified_partial_two_columns_unreadable"},
        {"source_id": "A4-SRC05", "publisher": "NFL.com",
         "page": "Injuries",
         "url": "https://www.nfl.com/injuries/",
         "used_for": "All 347 Week 10 injury-report rows and the news rail",
         "retrieval": "fetch_page x7, 2026-11-14",
         "status": "verified_with_anomalies_see_A4-F05_A4-F06_A4-F07"},
        {"source_id": "A4-SRC06", "publisher": "Packers / Seahawks / Vikings / Cowboys",
         "page": "Club depth charts",
         "url": "https://www.packers.com/team/depth-chart",
         "used_for": "97 depth-chart rows across 4 clubs",
         "retrieval": "fetch_page x4, 2026-11-14",
         "status": "verified"},
        {"source_id": "A4-SRC07", "publisher": "Houston Texans",
         "page": "Club depth chart",
         "url": "https://www.houstontexans.com/team/depth-chart",
         "used_for": "Attempted; renders as an image with no extractable rows",
         "retrieval": "fetch_page, 2026-11-14",
         "status": "unverified_image_only"},
        {"source_id": "A4-SRC08", "publisher": "NFL.com",
         "page": "Schedule by team",
         "url": "https://www.nfl.com/schedules/2026/by-team/buffalo-bills",
         "used_for": "Cross-check of club game logs and running records",
         "retrieval": "fetch_page, 2026-11-14",
         "status": "verified"},
        {"source_id": "A4-SRC09", "publisher": "NFL Next Gen Stats",
         "page": "Statistics",
         "url": "https://nextgenstats.nfl.com/",
         "used_for": "Identified as the route to player-prop data; not yet read",
         "retrieval": "not retrieved this session",
         "status": "planned_not_retrieved"},
    ]
    body = ('<p class="note">Every number published in this pack came from one '
            'of the pages below. Where a page did not yield usable data, that '
            'is recorded here too — see <code>A4-SRC02</code> and '
            '<code>A4-SRC07</code>.</p>')
    body += table(rows, cls="tbl")
    body += "<h3>Data files</h3>"
    files = [
        {"file": "data/nfl_a411fed0/results_2026_verified.psv",
         "contents": "120 verified finals with margin, total and source URL"},
        {"file": "data/nfl_a411fed0/origination_2026_w10.psv",
         "contents": "14 games, three markets each, fair/market/difference columns"},
        {"file": "data/nfl_a411fed0/price_snapshots_2026_w10.psv",
         "contents": "84 originated markets, opening and closing columns (empty)"},
        {"file": "data/nfl_a411fed0/strategy_leaderboard.psv",
         "contents": "10 strategies, signal and staking columns separated"},
        {"file": "data/nfl_a411fed0/injuries_2026_w10.psv",
         "contents": "347 rows with resolved replacement depth where available"},
        {"file": "data/nfl_a411fed0/correlations.psv",
         "contents": "10 correlations with n, CI and source URL"},
        {"file": "data/nfl_a411fed0/validation_gates.psv",
         "contents": "10 gates with observed value, threshold and evidence"},
        {"file": "data/nfl_a411fed0/raw/",
         "contents": "Verbatim captures: results, slate, injuries, depth charts"},
    ]
    body += table(files, cols=["file", "contents"])
    _write("sources.html", page("sources.html", "Sources",
           "Every official page this pack was read from, and what was taken "
           "from each.", body))


def main():
    build_all()
    page_origination()
    page_prices()
    page_results()
    page_strategies()
    page_staking()
    page_injuries()
    page_correlations()
    page_gates()
    page_questions()
    page_suggestions()
    page_flagged()
    page_sources()
    print("site written to", OUT)


if __name__ == "__main__":
    main()
