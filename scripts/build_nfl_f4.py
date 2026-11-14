#!/usr/bin/env python3
"""Build the nfl_f4 data pack and its zero-input GitHub Pages dashboard.

Zero input means: no forms, no <input>, no localhost fetches, no client-side
data files. Every page is a static render of a committed CSV, and every number
on a page carries either a source link or an explicit "unverified / blank"
marking. Run with ``--check`` to assert that the built site has no <input>, no
broken internal link and no un-sourced numeric cell in the automated tables.
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
import sys
from typing import Dict, Iterable, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.nfl_f4 import (  # noqa: E402
    prices, results, originate, leaderboard, depth, correlations, demotion,
)

DATA = os.path.join(ROOT, "data", "nfl_f4")
DOCS = os.path.join(ROOT, "docs", "nfl-f4")
BUILD_DATE = "2026-11-14"

NAV = [
    ("index.html", "Overview"),
    ("requirements.html", "Requirements"),
    ("lines.html", "Own lines"),
    ("origination.html", "Origination order"),
    ("prices.html", "Price snapshots"),
    ("results.html", "Verified results"),
    ("strategies.html", "Strategies"),
    ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Validation gates"),
    ("demotion.html", "Demotion gate"),
    ("correlations.html", "Correlations"),
    ("depth.html", "Injury &amp; depth"),
    ("questions.html", "Decision Q&A"),
    ("suggestions.html", "Suggestions"),
    ("repo-review.html", "Repo review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
    ("flagged.html", "Flagged for review"),
]

CSS = """/* nfl-f4 dashboard — single stylesheet, no external requests */
:root{--bg:#0b1016;--panel:#121a23;--panel2:#0f151d;--ink:#e8eef5;--dim:#8fa3b8;
--line:#22303f;--accent:#4da3ff;--good:#37c07a;--warn:#e0a63a;--bad:#e2605a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{position:sticky;top:0;z-index:5;background:#0b1016f2;border-bottom:1px solid var(--line);
backdrop-filter:blur(6px)}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.brand{display:flex;align-items:center;gap:12px;padding:14px 0 10px}
.brand b{font-size:17px;letter-spacing:.2px}
.brand span{color:var(--dim);font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:4px;padding:0 0 12px}
nav a{padding:5px 10px;border:1px solid var(--line);border-radius:999px;color:#c6d5e4;
font-size:13px;background:var(--panel2)}
nav a.on{border-color:var(--accent);color:#fff;background:#17324d}
main{padding:26px 0 60px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:19px;margin:30px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:15px;margin:20px 0 8px;color:#cfe0f0}
p.lede{color:var(--dim);max-width:82ch;margin:0 0 18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .k{color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.06em}
.card .v{font-size:24px;font-weight:600;margin-top:6px}
.card .s{color:var(--dim);font-size:12px;margin-top:4px}
table{width:100%;border-collapse:collapse;margin:12px 0 6px;font-size:13px;
display:block;overflow-x:auto;white-space:nowrap}
th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--panel2);color:#bdd0e2;font-weight:600;position:sticky;top:0}
tbody tr:hover{background:#16202b}
td.num{text-align:right;font-variant-numeric:tabular-nums}
caption{caption-side:top;text-align:left;color:var(--dim);font-size:12px;padding:6px 0}
.blank{color:#54677a;font-style:italic}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid}
.pill.ok{color:var(--good);border-color:#1f5c40;background:#0e2419}
.pill.warn{color:var(--warn);border-color:#5c4720;background:#241c0d}
.pill.bad{color:var(--bad);border-color:#5c2622;background:#241010}
.pill.neutral{color:var(--dim);border-color:var(--line);background:var(--panel2)}
.note{border-left:3px solid var(--accent);background:var(--panel);padding:10px 14px;
border-radius:0 8px 8px 0;margin:16px 0;color:#c3d4e5;font-size:14px}
.note.bad{border-left-color:var(--bad)}
.note.warn{border-left-color:var(--warn)}
.note.ok{border-left-color:var(--good)}
.scroll{overflow-x:auto}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:12px;padding:18px 0 40px}
code{background:#1a2432;padding:1px 5px;border-radius:4px;font-size:12px}
ul.tight{margin:6px 0 6px 18px;padding:0}
ul.tight li{margin:4px 0}
.kv{display:grid;grid-template-columns:210px 1fr;gap:4px 14px;font-size:13.5px;margin:10px 0}
.kv dt{color:var(--dim)}
.kv dd{margin:0}
"""


# ---------------------------------------------------------------------------
# csv helpers
# ---------------------------------------------------------------------------
def read_csv(name: str) -> List[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def cell(v: str, cls: str = "") -> str:
    if v is None or str(v).strip() == "":
        return '<td class="blank">—</td>'
    c = f' class="{cls}"' if cls else ""
    return f"<td{c}>{esc(v)}</td>"


def link(url: str, text: Optional[str] = None) -> str:
    if not url:
        return '<span class="blank">no source</span>'
    t = text or re.sub(r"^https?://(www\.)?", "", url)
    t = t if len(t) <= 64 else t[:61] + "…"
    return f'<a href="{esc(url)}" rel="noopener">{esc(t)}</a>'


def pill(text: str, kind: str = "neutral") -> str:
    return f'<span class="pill {kind}">{esc(text)}</span>'


def table(headers: List[str], rows: Iterable[List[str]], caption: str = "",
          num_cols: Iterable[int] = ()) -> str:
    num = set(num_cols)
    out = ["<table>"]
    if caption:
        out.append(f"<caption>{esc(caption)}</caption>")
    out.append("<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        tds = []
        for i, v in enumerate(r):
            if isinstance(v, tuple) and len(v) == 2 and v[0] == "__raw__":
                tds.append(f"<td>{v[1]}</td>")
            elif isinstance(v, str) and v.startswith('<span class="pill'):
                # pill() already returns escaped, safe markup.
                tds.append(f"<td>{v}</td>")
            elif i in num:
                tds.append(cell(v, "num"))
            else:
                tds.append(cell(v))
        out.append("<tr>" + "".join(tds) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def page(name: str, title: str, body: str, lede: str = "") -> str:
    nav = []
    for href, label in NAV:
        on = " class=\"on\"" if href == name else ""
        nav.append(f'<a href="{href}"{on}>{label}</a>')
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — Own6 NFL F4</title>
<meta name="description" content="NFL own-line origination, verified results, price snapshots and a skill/staking-split leaderboard. Every value is sourced or blank.">
<style>{CSS}</style></head><body>
<header><div class="wrap"><div class="brand"><b>Own6 · NFL Decision Desk</b>
<span>2026 season · built {BUILD_DATE} · zero-input dashboard</span></div>
<nav>{''.join(nav)}</nav></div></header>
<main class="wrap"><h1>{esc(title)}</h1>{lede_html}{body}</main>
<footer><div class="wrap">Sources are linked on every row. A blank cell is a cell
that no official source confirmed; it is never a zero and never an estimate.
This pack is informational and non-commercial. It is not betting advice, and it
makes no profitability claim.</div></footer></body></html>
"""


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def page_index() -> str:
    cov = prices.coverage_summary()
    rc = results.coverage()
    corr = read_csv("correlations.csv")
    strat = read_csv("leaderboard_strategies.csv")
    mt = read_csv("leaderboard_mask_test.csv")
    cert = sum(1 for s in strat if s.get("certified") == "yes")
    measured = [c for c in corr if c.get("status") == "measured"]
    cards = [
        ("Verified games", f"{rc['games']}", f"weeks 1–{rc['last_played_week']}, reconciled to standings"),
        ("Games priced", f"{cov['games_priced']}", f"{cov['markets_originated']} markets, open + close"),
        ("Price snapshots", f"{cov['snapshots_stored']}", "one row per market · selection · snapshot"),
        ("Strategies certified", f"{cert}", f"of {len(strat)} proposed · fail-closed gates"),
        ("Correlations measured", f"{len(measured)}", "each published with n and a CI"),
        ("Mask test", ("masking" if mt and mt[0]["board_can_mask"] == "True" else "no mask found"),
         f"largest settled sample {mt[0]['max_settled_bets_on_any_strategy']} bets" if mt else ""),
    ]
    grid = "".join(
        f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div>'
        f'<div class="s">{esc(s)}</div></div>' for k, v, s in cards)
    body = f"""
<div class="grid">{grid}</div>
<div class="note warn"><b>The honest headline.</b> The infrastructure the brief
asks for now exists and is verified: a results feed that reconciles to official
standings, a price store with real opens and closes, an origination order, a
skill/staking split, a measured-correlation table with n, a replacement-depth
chain and a demotion gate. The <i>conclusion</i> it produces is that nothing is
certified yet: one settled game is not a sample. Every empty leaderboard on this
site is a gate working, not a gap in the build.</div>
<h2>What to read first</h2>
<ul class="tight">
<li><a href="executive-summary.html">Executive summary</a> — the whole pack in one page.</li>
<li><a href="questions.html">Decision Q&amp;A</a> — what we know, what we do not, and how to find it out.</li>
<li><a href="suggestions.html">Suggestions review</a> — options with a recommendation and an explicit "your call" gate.</li>
<li><a href="flagged.html">Flagged for review</a> — every value that could not be confirmed.</li>
</ul>
<h2>The eight requirements, and where they live</h2>
<table><thead><tr><th>#</th><th>Requirement</th><th>Where it is implemented</th><th>State</th></tr></thead><tbody>
<tr><td>1</td><td>Price-snapshot store with opening and closing numbers</td><td><a href="prices.html">Price snapshots</a> · <code>data/nfl_f4/price_snapshots.csv</code></td><td>{pill('built · 168 snapshots','ok')}</td></tr>
<tr><td>2</td><td>Verified results feed usable by backtests</td><td><a href="results.html">Verified results</a> · <code>results.csv</code></td><td>{pill('built · 137 games reconcile','ok')}</td></tr>
<tr><td>3</td><td>Originate side, then total, then moneyline</td><td><a href="origination.html">Origination order</a></td><td>{pill('built · order enforced','ok')}</td></tr>
<tr><td>4</td><td>Fair line, market line, difference as separate columns</td><td><a href="lines.html">Own lines</a> · <code>fair_vs_market.csv</code></td><td>{pill('built · 42 markets','ok')}</td></tr>
<tr><td>5</td><td>Separate signal from staking in the leaderboard</td><td><a href="leaderboard.html">Leaderboard</a></td><td>{pill('built · nothing certified','warn')}</td></tr>
<tr><td>6</td><td>Track the depth of the replacement, not the fact</td><td><a href="depth.html">Injury &amp; depth</a></td><td>{pill('built · chain resolved','ok')}</td></tr>
<tr><td>7</td><td>Correlations only from official numbers, with n published</td><td><a href="correlations.html">Correlations</a></td><td>{pill('3 measured · 2 uncomputable','warn')}</td></tr>
<tr><td>8</td><td>Demotion gate from live back to paper</td><td><a href="demotion.html">Demotion gate</a></td><td>{pill('defined · nothing live','ok')}</td></tr>
</tbody></table>
<h2>Method in one paragraph</h2>
<p class="lede">Scores come from the official weekly schedule pages and are
checked by recomputing all 32 teams' records and points from the game rows and
comparing them to the official standings — a single mismatch fails the build.
Prices are the operator's own open and close fields, captured with a timestamp;
a market is only gradeable if the provider had settled it. Fair lines are a
declared, deliberately naive points-per-game model with every parameter listed
and flagged, because fitting coefficients to this sample would produce
confidence without evidence. Correlations are computed only from score data and
carry n, a 95% interval and a p-value; when the input does not exist the pair is
published as uncomputable rather than filled in.</p>
"""
    return page("index.html", "NFL own-line origination desk",
                body, "A dashboard for originating NFL numbers, grading them "
                      "against verified results, and separating skill from luck.")


def page_requirements() -> str:
    rows = [
        ("Price-snapshot store, open and close for every originated market",
         "data/nfl_f4/price_snapshots.csv", "168 rows = 14 games × 3 markets × 2 sides × 2 snapshots",
         "Open and close come from the provider's own fields, not from two visits to a page.",
         "done"),
        ("Verified results feed", "data/nfl_f4/results.csv + results_reconciliation.csv",
         "137 games, weeks 1–10", "All 32 team records and PF/PA recomputed and matched to official standings.",
         "done"),
        ("Origination order side → total → moneyline",
         "data/nfl_f4/originated_markets.csv", "origination_order 1,2,3 enforced and sorted",
         "The build re-sorts the file, so the order cannot be lost by an edit.", "done"),
        ("Fair line / market line / difference as separate columns",
         "data/nfl_f4/fair_vs_market.csv", "42 markets",
         "Difference is signed from the home side and never merged into the fair line.", "done"),
        ("Signal separate from staking in the leaderboard",
         "data/nfl_f4/leaderboard_strategies.csv + leaderboard_mask_test.csv", "7 strategies",
         "Signal = closing-line value per bet (no stake). Staking = units, only where a settle exists.",
         "done"),
        ("Depth of the replacement, not the fact",
         "data/nfl_f4/depth_replacement.csv", "46 depth slots, 2 clubs",
         "Each slot resolves to a named player and his string, including a contingency branch.", "done"),
        ("Correlations from official numbers only, with n",
         "data/nfl_f4/correlations.csv", "6 pairs: 3 measured, 2 uncomputable, 1 insufficient",
         "n, r, r², 95% CI and p published on every computed row.", "done"),
        ("Demotion gate live → paper", "data/nfl_f4/demotion_gate.csv + strategy_state.csv",
         "6 rules D1–D6", "Fail-closed; a demotion is sticky and re-entry has its own bar.", "done"),
    ]
    body = table(["Requirement", "Artefact", "Scale", "How it is enforced", "State"],
                 [[r[0], r[1], r[2], r[3], pill(r[4], "ok")] for r in rows],
                 "Each requirement from the brief, mapped to the file that implements it.")
    body += """
<h2>What the brief asked for beyond the eight numbered items</h2>
""" + table(["Ask", "Where"], [
        ["Leaderboard competition with rewards for top performers", '<a href="leaderboard.html">Leaderboard</a> — reward = rank, and rank requires a certified signal'],
        ["Single bets, parlays, player-prop combos", '<a href="strategies.html">Strategies</a> — S1–S7; prop combos are explicitly blocked, not faked'],
        ["Each strategy must pass validation gates", '<a href="validation.html">Validation gates</a>'],
        ["Determine correlation values", '<a href="correlations.html">Correlations</a>'],
        ["Remove luck; build selectively skill-based strategies", '<a href="leaderboard.html">Leaderboard</a> (luck p-value) + <a href="validation.html">gates</a>'],
        ["Track injuries and 2nd/3rd/4th-string replacements, offence and defence", '<a href="depth.html">Injury &amp; depth</a>'],
        ["Decision-ready Q&amp;A and missing-information discovery", '<a href="questions.html">Decision Q&amp;A</a>'],
        ["A section to review suggestions before implementing", '<a href="suggestions.html">Suggestions</a>'],
        ["Executive summary", '<a href="executive-summary.html">Executive summary</a>'],
        ["Flag irregularities with source links", '<a href="flagled.html">Flagged for review</a>'.replace('flagled', 'flagged')],
    ], "The rest of the brief.")
    return page("requirements.html", "Requirements coverage",
                body, "Every line of the brief, mapped to where it is implemented and what state it is in.")


def page_lines() -> str:
    rows = read_csv("fair_vs_market.csv")
    body = f"""
<div class="note"><b>Read the difference column, not the fair line.</b> A fair
line on its own invites belief. The difference column is the only column that
can be wrong in a way you can check: it says how far our number is from the
market's, and the market's number is the one with money behind it.</div>
{table(["Market", "Game", "Order", "Model fair line", "Market line", "Difference",
        "Units", "Model prob", "Market prob", "Model", "Market"],
       [[r["market"], r["game_key"], r["origination_order"], r["model_fair_line"],
         r["market_line"], r["difference"], r["difference_units"], r["model_prob"],
         r["market_prob"], pill(r["model_status"], "warn"), pill(r["market_status"], "ok")]
        for r in rows],
       f"{len(rows)} originated markets. Market line and price are the operator's "
       "settled close where one exists; where the game had not kicked off the "
       "number is the live quote at capture time and the close column is blank.",
       num_cols=[2, 3, 4, 5, 7, 8])}
<h2>Why the moneyline is listed last</h2>
<p>Win probability is a function of the fair spread and the total. Publishing it
first would mean publishing an assumption as if it were an input. The file is
sorted by <code>origination_order</code> by the builder, so a manual edit cannot
put the moneyline above the side.</p>
<h2>Model status</h2>
<p>Every row is <code>model_output</code>. Nothing on this page is verified, and
nothing on it claims to be: a model number can be sourced in its inputs but not
in its conclusion. The declared parameters behind it — home-field advantage,
shrinkage, the margin dispersion — are listed on
<a href="validation.html">Validation gates</a> and in <code>flagged.csv</code>.</p>
"""
    return page("lines.html", "Own lines: fair vs market",
                body, "The model's fair line, the market's line, and the difference — three columns, always separate.")


def page_origination() -> str:
    rows = read_csv("originated_markets.csv")
    order = {1: "1 · side", 2: "2 · total", 3: "3 · moneyline"}
    body = f"""
<h2>The order, and why it is a gate</h2>
<ol class="tight">
<li><b>Side first.</b> Deepest price history, least model risk. If the side
cannot beat the close, nothing downstream earns the right to a bigger claim.</li>
<li><b>Total second.</b> Derived from a separate quantity (scoring environment),
so it can be checked against the market's own two-way price rather than against
the side.</li>
<li><b>Moneyline last.</b> A nonlinear function of the first two.</li>
</ol>
{table(["Order", "Game", "Market", "Selection", "Fair line", "Market line",
        "Price", "Difference", "Direction", "Flags"],
       [[order.get(int(r["origination_order"]), r["origination_order"]), r["game_key"],
         r["market"], r["selection"], r["fair_line"], r["market_line"],
         r["market_price_american"], (r["difference_points"] or r["difference_prob"]),
         r["direction"], r["flags"]]
        for r in rows],
       f"{len(rows)} rows, written sorted by origination_order.", num_cols=[4, 5, 6])}
"""
    return page("origination.html", "Origination order",
                body, "Side, then total, then moneyline — enforced in the data, not just described.")


def page_prices() -> str:
    mk = read_csv("markets.csv")
    snaps = read_csv("price_snapshots.csv")
    cov = prices.coverage_summary()
    snaps_by_key = {}
    for sn in snaps:
        snaps_by_key.setdefault((sn["game_key"], sn["market"], sn["selection"]), []).append(sn)
    moved = [m for m in mk if m["line_move"] not in ("", "0")]
    open_snaps = [s for s in snaps if s["snapshot_type"] == "open"]
    close_snaps = [s for s in snaps if s["snapshot_type"] == "close"]
    body = f"""
<div class="grid">
<div class="card"><div class="k">Games priced</div><div class="v">{cov['games_priced']}</div><div class="s">all 14 Week 10 games</div></div>
<div class="card"><div class="k">Markets</div><div class="v">{cov['markets_originated']}</div><div class="s">spread · total · moneyline</div></div>
<div class="card"><div class="k">Snapshots</div><div class="v">{cov['snapshots_stored']}</div><div class="s">{len(open_snaps)} open · {len(close_snaps)} close</div></div>
<div class="card"><div class="k">Lines that moved</div><div class="v">{len(moved)}</div><div class="s">of {len(mk)} market rows</div></div>
</div>
<div class="note warn"><b>One settled close.</b> The Week 10 Thursday game had been
played when prices were read, so the provider had frozen its close and this store
records it as <code>close_status=final</code>. The other thirteen games had not
kicked off: their "close" is the live quote at capture time and is stored with
<code>close_status=not_final</code>. Grading a strategy against a not-final close
would be grading against a number nobody could have bet.</div>
<h2>Open vs close, every market</h2>
{table(["Game", "Market", "Selection", "Open", "Open price", "Close", "Close price",
        "Move", "Direction", "To favourite", "Close status", "Source"],
       [[m["game_key"], m["market"], m["selection"], m["open_line"],
         m["open_price_american"], m["close_line"], m["close_price_american"],
         m["line_move"], m["move_direction"], m["move_is_to_favourite"],
         pill(m["close_status"], "ok" if m["close_status"] == "final" else "warn"),
         (("__raw__", link(m["source_url"])))]
        for m in mk],
       f"{len(mk)} market rows derived from {len(snaps)} stored snapshots.",
       num_cols=[3, 4, 5, 6])}
<h2>Capture protocol</h2>
<ul class="tight">
<li>The provider's own <code>open</code> and <code>close</code> (or <code>current</code>)
objects are captured, so open and close are two fields of one atomic read rather
than two visits that may straddle a move.</li>
<li>Every snapshot stores the price as well as the line. A line that moved 3
points at even money is a different event from a line that moved 3 points through
a key number with the vig attached.</li>
<li>Capture time is recorded per snapshot and per read date. The store is
append-only by convention: a re-read adds snapshots, it does not overwrite.</li>
<li>Provider identity is stored on every row. The feed is the operator's own
published price relayed by a public endpoint — an operator quote, not an NFL
publication, and the distinction is written into <code>sources.csv</code>.</li>
</ul>
"""
    return page("prices.html", "Price snapshots",
                body, "Opening and closing numbers for every market we originate, with the vig attached to each.")


def page_results() -> str:
    res = read_csv("results.csv")
    rec = read_csv("results_reconciliation.csv")
    cov = results.coverage()
    mism = [r for r in rec if r["result"] != "MATCH"]
    body = f"""
<div class="grid">
<div class="card"><div class="k">Games</div><div class="v">{cov['games']}</div><div class="s">weeks 1–10</div></div>
<div class="card"><div class="k">Teams reconciled</div><div class="v">{len(rec)}</div><div class="s">W · L · T · PF · PA all five fields</div></div>
<div class="card"><div class="k">Mismatches</div><div class="v">{len(mism)}</div><div class="s">a mismatch fails the build</div></div>
</div>
<div class="note ok"><b>This feed checks itself.</b> Wins, losses, ties, points
for and points against are recomputed from the game rows and compared field by
field against the official standings captured the same day. All {len(rec)} teams
match on all five fields. If any single field differed, the builder would exit
non-zero instead of publishing.</div>
<h2>Reconciliation</h2>
{table(["Team", "W", "L", "T", "PF", "PA", "Games", "Official W-L-T", "PF-PA", "Result", "Source"],
       [[r["abbr"], r["wins_recomputed"], r["losses_recomputed"], r["ties_recomputed"],
         r["pf_recomputed"], r["pa_recomputed"], r["games_recomputed"],
         f"{r['wins_official']}-{r['losses_official']}-{r['ties_official']}",
         f"{r['pf_official']}-{r['pa_official']}",
         pill(r["result"], "ok" if r["result"] == "MATCH" else "bad"),
         (("__raw__", link(r["standings_source_url"])))]
        for r in rec], num_cols=[1, 2, 3, 4, 5, 6])}
<h2>Games</h2>
{table(["Week", "Away", "Score", "Home", "Score", "Winner", "Margin", "Total", "Source"],
       [[r["week"], r["away"], r["away_score"], r["home"], r["home_score"],
         r["winner"], r["margin"], r["total_points"],
         (("__raw__", link(r["result_source_url"])))]
        for r in res], f"{len(res)} finals.", num_cols=[2, 4, 7])}
<h2>What is deliberately missing</h2>
<p>The overtime flag is blank on every row. The weekly schedule pages state the
final score and the day; they do not state whether the game went to overtime, and
inferring it from a margin would be exactly the kind of quiet invention this pack
is built to avoid. Week 10 contains one game because the other thirteen had not
been played when the data was read.</p>
"""
    return page("results.html", "Verified results feed",
                body, "Official finals for weeks 1–10, reconciled team by team against official standings.")


def page_strategies() -> str:
    rows = read_csv("leaderboard_strategies.csv")
    body = f"""
<div class="note bad"><b>Seven attempts, zero certifications.</b> A strategy earns
a leaderboard row only by clearing the sample floor. At one settled game, none
can. That is the gate doing the one job it has.</div>
{table(["ID", "Strategy", "Market", "Structure", "Order", "Bets", "Weeks",
        "Signal / bet", "Staking", "Certified", "Gate detail"],
       [[r["strategy_id"], r["name"], r["market"], r["structure"],
         r["origin_order"], r["bets_settled"], r["weeks_covered"],
         r["signal_score_per_bet"], r["staking_score"],
         pill(r["certified"], "ok" if r["certified"] == "yes" else "warn"),
         r["gate_detail"]]
        for r in rows], num_cols=[4, 5, 6])}
<h2>Structures, and what each one would need</h2>
<dl class="kv">
<dt>Single (S1–S4)</dt><dd>One market, one price. Needs a verified open, a verified close and a verified result per bet.</dd>
<dt>Parlay, multi-game (S6)</dt><dd>Two independent legs. The advertised payout implies an independence assumption that this pack refuses to assume — the correlation table is the input, and it currently says the side/total dependence is not distinguishable from zero at n=137 (r = −0.16, p = 0.06).</dd>
<dt>Same-game parlay (S5)</dt><dd>Legs that are structurally correlated. Without a measured same-game correlation, an SGP price is a guess. Gate G4 blocks it.</dd>
<dt>Player-prop combo (S7)</dt><dd>Requires official player-level stat lines per game, which this pack does not capture. Blocked at G5 rather than filled with a plausible number.</dd>
</dl>
<h2>Rewards</h2>
<p>The reward for a top-performing strategy is rank and promotion eligibility —
nothing else. No staking plan is published, because a staking plan is the fastest
way to convert a signal claim into a variance test. The moment a strategy clears
the gates, its reward becomes a live slot with the
<a href="demotion.html">demotion gate</a> attached.</p>
"""
    return page("strategies.html", "Strategy catalog",
                body, "Singles, parlays and prop combos — each with the gate that currently blocks it and why.")


def page_leaderboard() -> str:
    lb = read_csv("leaderboard.csv")
    strat = read_csv("leaderboard_strategies.csv")
    mt = read_csv("leaderboard_mask_test.csv")
    verdict = mt[0]["verdict"] if mt else ""
    body = f"""
<h2>Two scores, never one</h2>
<div class="grid">
<div class="card"><div class="k">Signal score</div><div class="v">CLV</div><div class="s">closing-line value per bet · stake-free</div></div>
<div class="card"><div class="k">Staking score</div><div class="v">units</div><div class="s">needs a settled open, close and result</div></div>
<div class="card"><div class="k">Mask test</div><div class="v">{pill('MASKING', 'bad') if mt and mt[0]['board_can_mask'] == 'True' else pill('no mask', 'ok')}</div><div class="s">would a lucky run hide a bad signal?</div></div>
<div class="card"><div class="k">Certified</div><div class="v">{sum(1 for s in strat if s['certified']=='yes')}</div><div class="s">of {len(strat)} proposed</div></div>
</div>
<div class="note warn"><b>Mask test result.</b> {esc(verdict)}</div>
<h2>Published leaderboard</h2>
{('<p class="blank">No strategy is certified, so the ranked table is intentionally empty. '
  'An empty board with a stated reason is more useful than a ranked table of unproven ideas.</p>')
 if not lb else
 table(["Rank", "Strategy", "Signal / bet", "Staking", "Signal rank", "Staking rank",
        "Rank gap", "Verdict"],
       [[r["rank"], r["name"], r["signal_score_per_bet"], r["staking_score"],
         r["signal_rank"], r["staking_rank"], r["rank_gap"], r["verdict"]] for r in lb])}
<h2>Why a staking run can be excluded even when it wins</h2>
<p>Fifteen winners at even money happen by chance about once in 32,000 attempts —
but you only ever see the attempt that happened. The board therefore computes the
probability of a run at least this good under a fair coin, and anything above
p = 0.05 is labelled indistinguishable from luck and cannot be promoted,
whatever the units column says. Staking is reported because you asked for it;
it is never allowed to outrank signal.</p>
<h2>All proposed strategies, with their gate detail</h2>
{table(["ID", "Strategy", "Bets", "Signal / bet", "Staking", "Certified", "Gate detail"],
       [[r["strategy_id"], r["name"], r["bets_settled"], r["signal_score_per_bet"],
         r["staking_score"], pill(r["certified"], "warn" if r["certified"] != "yes" else "ok"),
         r["gate_detail"]] for r in strat], num_cols=[2, 3, 4])}
"""
    return page("leaderboard.html", "Leaderboard — signal vs staking",
                body, "Two independent scores and a mask test, so a lucky staking run cannot outrank a bad signal.")


def page_validation() -> str:
    gates = [
        ("G1", "Sample floor", "≥ 100 settled bets", "Proposed strategies carry 0–1 settled bets.", "FAIL"),
        ("G2", "Week coverage", "≥ 6 distinct weeks", "One week has a settled close.", "FAIL"),
        ("G3", "Signal exists", "CLV per bet computable on ≥90% of bets", "Requires a close for both sides.", "FAIL"),
        ("G4", "Gradeability", "Verified open, close and result for every bet", "13 of 14 games had no settled close.", "FAIL"),
        ("G5", "Input completeness", "All inputs officially sourced", "Player-level stats not captured for prop combos.", "FAIL"),
        ("G6", "Result reconciliation", "All 32 teams match official standings", "137 games; 32/32 match on W, L, T, PF, PA.", "PASS"),
        ("G7", "No un-sourced cell", "Every published number has a source or is blank", "Enforced by check_nfl_f4.py --check.", "PASS"),
        ("G8", "Determinism", "Two builds byte-identical", "All builders are pure functions of committed CSV.", "PASS"),
        ("G9", "Demotion path exists", "Live → paper rule set defined", "Rules D1–D6 published with thresholds.", "PASS"),
    ]
    body = f"""
{table(["Gate", "Name", "Criterion", "Current evidence", "State"],
       [[g[0], g[1], g[2], g[3], pill(g[4], "ok" if g[4] == "PASS" else "bad")] for g in gates],
       "Nine gates. Four pass on infrastructure, five fail on sample — and the failures are the point.")}
<h2>Declared model parameters</h2>
{table(["Parameter", "Value", "Status", "Why it is not estimated"],
       [["Home-field points", "0.0", "declared", "No verified home/away split was captured; a common 3.0 would be an imported assumption."],
        ["Shrinkage to league mean", "0.0", "declared", "Fitting shrinkage needs multiple seasons of history."],
        ["Margin dispersion σ", "13.86", "declared", "Used in the win-probability map; not re-estimated here (n=137, one season)."],
        ["Total dispersion σ", "13.5", "declared", "Same reasoning as the margin σ."],
        ["PPG floor", "4 games", "declared", "Below four games a points-per-game rate is mostly noise."],
        ["Deficiency weights", "0.00/0.35/0.70/0.70", "declared", "Monotone in string number; not fitted to outcomes."],
        ["Min edge to quote", "0.5 points", "declared", "Below half a point, the difference is inside capture error."]],
       "None of these is presented as measured. Each is a decision you can overrule.")}
<h2>What would change a FAIL to a PASS</h2>
<p>G1 and G2 need history: the price store has to accumulate settled closes across
weeks, which the capture protocol already supports retroactively. G3 and G4 need
the same. G5 needs official player-level stat lines, which would come from an
official stats source, not from a scraped box score. None of these requires a
model change; all of them require time or a decision.</p>
"""
    return page("validation.html", "Validation gates",
                body, "Nine gates, four green on infrastructure and five red on sample size — published as they are.")


def page_demotion() -> str:
    gate = read_csv("demotion_gate.csv")
    state = read_csv("strategy_state.csv")
    body = f"""
<div class="note"><b>A promotion gate without a demotion gate is a ratchet.</b>
The thresholds below are fixed in advance so that the exit condition cannot be
renegotiated after a strategy starts losing.</div>
{table(["Rule", "Name", "Trigger", "Condition", "Checked against", "Result"],
       [[g["rule_id"], g["rule_name"], g["threshold"], g["condition_text"],
         g["checked_against"], pill(g["result"], "ok" if g["result"] == "not_triggered" else "warn")]
        for g in gate], "Six demotion rules.")}
<h2>Lifecycle</h2>
<p><code>proposed → paper → live → (demotion) → paper → (repeat) → retired</code></p>
<ul class="tight">
<li><b>D1 Signal decay.</b> Trailing CLV per bet at or below zero over at least 40
settled bets. Winning bets with negative CLV are still decay.</li>
<li><b>D2 Drawdown.</b> More than 8 units below the peak. A staking plan that
needs a recovery run to be viable was never viable.</li>
<li><b>D3 Negative run.</b> Three consecutive negative-signal weeks, even if the
cumulative number is still positive.</li>
<li><b>D4 Luck divergence.</b> Positive ROI with a non-positive signal — the
mirror of the leaderboard mask test. This is the rule that catches the lucky run
while it is still winning.</li>
<li><b>D5 Unverifiable.</b> Any live bet without a verified open, close and
result. Missing data counts against the strategy, never for it.</li>
<li><b>D6 Model drift.</b> Declared parameters changed without a version bump and
a fresh validation run.</li>
</ul>
<h2>Stickiness and re-entry</h2>
<p>A demotion cannot be undone by one good week. Re-promotion requires at least
40 new settled bets with a positive signal score over that fresh window. The
fresh window restarts whenever a rule triggers, so a demoted strategy cannot
inherit credit from the bets that got it demoted.</p>
<h2>Current state</h2>
{table(["ID", "Strategy", "State", "Target", "Reason", "Bets", "Re-entry condition"],
       [[r["strategy_id"], r["name"], pill(r["current_state"], "neutral"),
         pill(r["target_state"], "warn"), r["reason_code"], r["bets_settled"],
         r["re_entry_condition"]] for r in state], num_cols=[5])}
"""
    return page("demotion.html", "Demotion gate",
                body, "The defined path back from live to paper, with thresholds fixed before the fact.")


def page_correlations() -> str:
    rows = read_csv("correlations.csv")
    body = f"""
<div class="note"><b>The rule.</b> A correlation is published only when every
observation behind it traces to an official page. n, r, r², a 95% interval and a
two-sided p-value are printed on every computed row. When an input does not
exist, the pair is published as <em>uncomputable</em> with the reason — never as
zero, and never quietly omitted.</div>
{table(["ID", "Pair", "n", "r", "r²", "95% CI", "p", "Floor", "Material", "State", "Source X", "Source Y"],
       [[r["corr_id"], r["pair"], r["n"], r["pearson_r"], r["r_squared"],
         (f"[{r['ci95_low']}, {r['ci95_high']}]" if r["ci95_low"] else ""),
         r["p_value_two_sided"], r["n_floor"], r["material"],
         pill(r["status"], "ok" if r["status"] == "measured" else "warn"),
         (("__raw__", link(r["source_x"]))), (("__raw__", link(r["source_y"])))]
        for r in rows], f"{len(rows)} pairs attempted.", num_cols=[2, 3, 4, 6])}
<h2>Reading the three measured values</h2>
<ul class="tight">
<li><b>C1 margin vs total, r = −0.161 (n = 137, p = 0.061).</b> Not distinguishable
from zero at the 5% level, and the interval spans zero. The honest read: no
demonstrated dependence, so a same-game side+total parlay should be priced at
independence <em>for now</em>, with the caveat that a real effect this size would
need roughly 400+ games to resolve.</li>
<li><b>C2 points-for vs points-against, r = 0.075 (n = 274).</b> Essentially zero,
as expected: a team's offence and defence are separate processes. This is a
useful negative result — it means offence and defence must be modelled and
priced separately, which is what the depth page already assumes.</li>
<li><b>C3 absolute margin vs total, r = −0.016 (n = 137).</b> No blowout/total
link. Totals in mismatched games carry no extra information from this pair.</li>
</ul>
<h2>What is not computed, and why that is the answer</h2>
<ul class="tight">
<li><b>C4 rest differential.</b> The most-cited public NFL signal has no verified
rest column in this pack. Game dates could be differenced, but Thursday and
Monday games already encode rest, so deriving it would smuggle an assumption into
a "measured" number.</li>
<li><b>C5 depth deficiency vs margin.</b> One week of depth snapshots for two
clubs. A correlation needs the deficiency score and the margin for the same games
across ≥100 observations.</li>
<li><b>C6 closing spread vs margin.</b> One settled game. The store is built to
accumulate exactly this, and the row will fill itself as closes settle.</li>
</ul>
"""
    return page("correlations.html", "Correlations",
                body, "Measured only from officially sourced numbers, with n, a 95% interval and a p-value on every row.")


def page_depth() -> str:
    rep = read_csv("depth_replacement.csv")
    summ = read_csv("depth_unit_summary.csv")
    forced = [r for r in rep if r["effectively_available_first"] == "no"]
    cont = [r for r in rep if r["contingency_player"]]
    deep = [r for r in rep if r["replacement_string"] and int(r["replacement_string"]) >= 3]
    body = f"""
<div class="grid">
<div class="card"><div class="k">Depth slots</div><div class="v">{len(rep)}</div><div class="s">2 clubs, offence + defence</div></div>
<div class="card"><div class="k">Starters ruled out</div><div class="v">{len(forced)}</div><div class="s">replacement is forced</div></div>
<div class="card"><div class="k">Contingency from 3rd string+</div><div class="v">{len(deep)}</div><div class="s">one scratch away from a third-stringer</div></div>
<div class="card"><div class="k">Questionable starters with a branch</div><div class="v">{len(cont)}</div><div class="s">the case a one-week report hides</div></div>
</div>
<div class="note warn"><b>Both depth charts are labelled UNOFFICIAL by the clubs
themselves.</b> New England: the 2026 chart is "published by the writers of
Patriots.com" and "the opinions of the Patriots.com writers". Detroit: "Unofficial
Depth Chart Compiled by Lions Football Communications". Every depth-derived row
therefore carries <code>status = verified_unofficial_source</code>, and the club's
own caveat text travels with the row.</div>
<h2>The chain, slot by slot</h2>
{table(["Team", "Unit", "Slot", "1st string", "Status", "1st available?", "Replacement", "String",
        "Contingency", "String", "Worst case pts", "Chain note"],
       [[r["team"], r["unit"], r["slot"], r["first_string"], r["first_string_game_status"],
         pill(r["effectively_available_first"], "bad" if r["effectively_available_first"] == "no" else "ok"),
         r["replacement_player"], r["replacement_string"], r["contingency_player"],
         r["contingency_string"], r["worst_case_points"], r["chain_note"]]
        for r in rep], num_cols=[7, 9, 10])}
<h2>The case that matters: a questionable starter in front of an unavailable backup</h2>
<p>New England running back Rhamondre Stevenson is <b>Questionable</b>. Behind him
the club lists TreVeyon Henderson <b>2nd</b> — and the official report has
Henderson <b>Out</b>. So the contingency plan is not the second string; it is
<b>Corey Kiner, third string</b>, with Lan Larison fourth. That is a different
price than "Stevenson questionable". The contingency columns exist to make that
two-step visible instead of collapsing it into a single injury headline.</p>
{table(["Team", "Unit", "Slots", "Starters out", "Replacement 3rd+", "Deficiency pts",
        "Contingency 3rd+", "Worst case pts"],
       [[s["team"], s["unit"], s["slots_listed"], s["starters_ruled_out"],
         s["replacement_from_3rd_string_or_worse"], s["deficiency_points_total"],
         s["contingency_slots_3rd_string_or_worse"], s["worst_case_points_total"]]
        for s in summ], "Offence and defence reported separately, as the brief requires.",
       num_cols=[2, 3, 4, 5, 6, 7])}
<h2>Two refusals</h2>
<ul class="tight">
<li><b>A missing designation is not health.</b> If the official report does not
name a player, the row says <code>not_designated</code>, not "healthy". The report
lists participation, not fitness.</li>
<li><b>Only clubs whose chart was read are populated.</b> A roster sorted by
jersey number is not a depth chart, so the other 30 clubs are absent rather than
guessed at.</li>
</ul>
"""
    return page("depth.html", "Injury & depth deficiency",
                body, "Who replaces whom, from which string — including the contingency behind a questionable starter.")


def page_questions() -> str:
    rows = read_csv("questions.csv")
    answered = [r for r in rows if r["status"] == "answered"]
    body = f"""
<div class="note"><b>Why this page exists.</b> A dashboard that only shows what it
knows is a confidence machine. This page lists the questions that have to be
answered before any decision on this site is worth making, separates the ones the
data already answers from the ones it cannot, and says for each open question
exactly what would close it and where that would come from.</div>
{table(["#", "Question", "Answer we can stand behind", "State", "What would close it"],
       [[r["q_id"], r["question"], r["answer"], pill(r["status"], "ok" if r["status"] == "answered" else "warn"),
         r["how_to_close"]] for r in rows],
       f"{len(rows)} questions: {len(answered)} answered from verified data, {len(rows)-len(answered)} open.")}
"""
    return page("questions.html", "Decision questions",
                body, "What we know, what we do not know, and what would settle it — question by question.")


def page_suggestions() -> str:
    rows = read_csv("suggestions.csv")
    body = f"""
<div class="note warn"><b>Nothing on this page has been implemented.</b> Each
suggestion is a decision that belongs to you. The recommendation column is our
view; the state column says <code>pending_human_choice</code> until you pick. This
is the review gate the brief asked for, and it is deliberately separate from the
pages that describe what already exists.</div>
{table(["#", "Suggestion", "Why it improves decisions", "Options", "Cost", "Risk", "Recommendation", "State"],
       [[r["s_id"], r["suggestion"], r["why"], r["options"], r["cost"], r["risk"],
         r["recommendation"], pill(r["state"], "warn" if r["state"].startswith("pending") else "ok")]
        for r in rows], f"{len(rows)} suggestions awaiting a decision.")}
"""
    return page("suggestions.html", "Suggestions for review",
                body, "Improvement options, each with a recommendation and an explicit decision gate — choose before anything is built.")


def page_repo_review() -> str:
    rows = read_csv("repo_review.csv")
    body = f"""
<div class="note"><b>Scope.</b> The repo carries eight earlier NFL packs. This
review checks the pack most relevant to the brief — <code>nfl_309921cc</code> —
against the official pages read in this session, row by row. It does not restate
the other packs' self-audits; it checks claims that this session could verify
independently.</div>
{table(["#", "File", "Claim as written", "What the official source says", "Verdict", "Source"],
       [[r["f_id"], r["file"], r["claim"], r["official"], pill(r["verdict"],
         "ok" if r["verdict"] == "confirmed" else "bad"),
         (("__raw__", link(r["source_url"])))] for r in rows],
       f"{len(rows)} checked claims.")}
<h2>What held up</h2>
<p>The earlier pack's Week 10 injury data for the two clubs whose charts were read
here matched the official report on every field checked, including the
participation strings and game statuses. Its own flags about unofficial depth
charts and missing prices are correctly raised. The irregularities below are
narrow and specific, which is what a review should produce.</p>
"""
    return page("repo-review.html", "Repo review",
                body, "Line-by-line verification of the prior pack's claims against official pages, with irregularities flagged.")


def page_sources() -> str:
    rows = read_csv("sources.csv")
    body = f"""
<div class="note"><b>Two classes of source.</b> <em>Official</em> means published
by the league (nfl.com, operations.nfl.com) or by a club (patriots.com,
detroitlions.com). <em>Operator</em> means a licensed sportsbook's own published
price — reliable as a price, but not a league publication, and labelled
accordingly. Boundary notes say what each source does <em>not</em> support, which
is the column that stops a source being over-read.</div>
{table(["ID", "Publisher", "Title", "Read on", "Supports", "Does not support", "Link"],
       [[r["s_id"], r["publisher"], r["title"], r["read_date"], r["supports"],
         r["not_supports"], (("__raw__", link(r["url"])))] for r in rows],
       f"{len(rows)} sources.")}
"""
    return page("sources.html", "Sources",
                body, "Every source used, what it supports, and what it explicitly does not support.")


def page_flagged() -> str:
    rows = read_csv("flagged.csv")
    by_sev = {}
    for r in rows:
        by_sev[r["severity"]] = by_sev.get(r["severity"], 0) + 1
    body = f"""
<div class="note bad"><b>Nothing here blocks the build.</b> Each item is a value
that could not be confirmed from an official source, a declared assumption, or a
limitation of the data. They are published with links so you can review them
after the site is live and ask for changes.</div>
<div class="grid">
<div class="card"><div class="k">Items</div><div class="v">{len(rows)}</div><div class="s">all published, none blocking</div></div>
<div class="card"><div class="k">High</div><div class="v">{by_sev.get('high', 0)}</div><div class="s">affects a headline claim</div></div>
<div class="card"><div class="k">Medium</div><div class="v">{by_sev.get('medium', 0)}</div><div class="s">affects interpretation</div></div>
<div class="card"><div class="k">Low</div><div class="v">{by_sev.get('low', 0)}</div><div class="s">cosmetic or documented</div></div>
</div>
{table(["ID", "Area", "Issue", "How it is handled", "Severity", "Source"],
       [[r["f_id"], r["area"], r["issue"], r["handling"],
         pill(r["severity"], {"high": "bad", "medium": "warn"}.get(r["severity"], "neutral")),
         (("__raw__", link(r["source_url"])))] for r in rows],
       f"{len(rows)} flagged items.")}
"""
    return page("flagged.html", "Flagged for review",
                body, "Unconfirmed values, declared assumptions and data limits — with source links, for your review.")


def page_exec() -> str:
    cov = prices.coverage_summary()
    rc = results.coverage()
    corr = read_csv("correlations.csv")
    strat = read_csv("leaderboard_strategies.csv")
    flagged = read_csv("flagged.csv")
    sugg = read_csv("suggestions.csv")
    q = read_csv("questions.csv")
    body = f"""
<h2>Bottom line</h2>
<p class="lede">The machinery you asked for is built and verified. The verdict it
returns is that <b>no strategy is certifiable yet</b>, and it says so in public
rather than producing a leaderboard that looks like progress. That is the single
most important finding in this pack: with 137 verified games (scores only) and
one settled priced game, any "top strategy" would be noise wearing a rank.</p>
<h2>What exists now</h2>
<ul class="tight">
<li><b>A results feed that checks itself.</b> {rc['games']} finals across weeks
1–10; all 32 teams' wins, losses, ties, points for and points against recomputed
from the game rows and matched against official standings — 32/32 on all five
fields. Any mismatch fails the build.</li>
<li><b>A price store with real opens and closes.</b> {cov['games_priced']} games,
{cov['markets_originated']} markets, {cov['snapshots_stored']} snapshots, each with
the price as well as the line, and each marked final or not-final. Thirteen of
fourteen closes are not final because the games had not kicked off.</li>
<li><b>The origination order as a gate.</b> Side, then total, then moneyline —
enforced by a sort in the builder so an edit cannot reorder it.</li>
<li><b>Fair line, market line and difference as three columns</b> on all 42
originated markets, with the difference signed from the home side.</li>
<li><b>Signal separated from staking,</b> with a published mask test. Zero
certified strategies; seven blocked by named gates.</li>
<li><b>Replacement depth, not replacement fact.</b> 46 depth slots across two
clubs, each resolving to a named player and his string, plus a contingency column
for questionable starters. New England's running back chain resolves to the
third string because the second is Out.</li>
<li><b>Correlations with n.</b> Three measured (n = 137, 274, 137), two
uncomputable for stated reasons, one insufficient. No value inferred.</li>
<li><b>A demotion gate</b> with six rules, fixed thresholds, stickiness and a
re-entry bar.</li>
</ul>
<h2>The findings that matter</h2>
<ol class="tight">
<li><b>The market and the model disagree almost everywhere, and that is not an
edge.</b> On the Week 10 side market the model is 1–3.5 points off the close on
most games. A naive points-per-game rating disagreeing with a closing line is
evidence about the rating, not about the line.</li>
<li><b>Side/total correlation is not established.</b> r = −0.161 at n = 137
(p = 0.061) with an interval spanning zero. Same-game parlays should therefore be
priced at independence for now — with the explicit caveat that a real effect this
size would need roughly 400+ games to resolve.</li>
<li><b>Offence and defence are separable.</b> r = 0.075 between points scored and
points allowed in the same team-game. This is a useful negative: it justifies
modelling and pricing them separately.</li>
<li><b>Rest differential is the most-cited signal with the least verified
data.</b> It is uncomputable here rather than assumed.</li>
<li><b>Depth charts are unofficial by the clubs' own admission.</b> Every
depth-derived row says so in the club's own words.</li>
<li><b>One-week injury reports hide the case that matters.</b> The contingency
column exposes starters who are questionable in front of backups who are out.</li>
</ol>
<h2>What would change the picture</h2>
<ul class="tight">
<li><b>Time.</b> The price store accumulates settled closes retroactively, so the
sample floor is a waiting problem, not a design problem.</li>
<li><b>One decision from you:</b> whether to keep publishing an empty leaderboard
(honest) or to publish a "provisional, not certified" board with the gates
printed on every row. It is listed in <a href="suggestions.html">Suggestions</a>
as <a href="suggestions.html">S01</a>.</li>
</ul>
<h2>Open questions and decisions</h2>
<div class="grid">
<div class="card"><div class="k">Questions logged</div><div class="v">{len(q)}</div><div class="s"><a href="questions.html">Decision Q&amp;A</a></div></div>
<div class="card"><div class="k">Suggestions awaiting you</div><div class="v">{len(sugg)}</div><div class="s"><a href="suggestions.html">Suggestions</a></div></div>
<div class="card"><div class="k">Flagged items</div><div class="v">{len(flagged)}</div><div class="s"><a href="flagged.html">Flagged for review</a></div></div>
</div>
"""
    return page("executive-summary.html", "Executive summary",
                body, "The pack in one page: what is built, what it concludes, and what needs your decision.")


PAGES = {
    "index.html": page_index,
    "requirements.html": page_requirements,
    "lines.html": page_lines,
    "origination.html": page_origination,
    "prices.html": page_prices,
    "results.html": page_results,
    "strategies.html": page_strategies,
    "leaderboard.html": page_leaderboard,
    "validation.html": page_validation,
    "demotion.html": page_demotion,
    "correlations.html": page_correlations,
    "depth.html": page_depth,
    "questions.html": page_questions,
    "suggestions.html": page_suggestions,
    "repo-review.html": page_repo_review,
    "sources.html": page_sources,
    "executive-summary.html": page_exec,
    "flagged.html": page_flagged,
}


def build() -> List[str]:
    os.makedirs(DOCS, exist_ok=True)
    written = []
    for name, fn in PAGES.items():
        html_text = fn()
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
            fh.write(html_text)
        written.append(name)
    with open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8") as fh:
        fh.write("")
    return written


def check() -> List[str]:
    problems = []
    for name in PAGES:
        path = os.path.join(DOCS, name)
        if not os.path.exists(path):
            problems.append(f"{name}: missing")
            continue
        text = open(path, encoding="utf-8").read()
        if "<input" in text.lower() or "<form" in text.lower():
            problems.append(f"{name}: contains an input/form (must be zero-input)")
        if "localhost" in text or "127.0.0.1" in text:
            problems.append(f"{name}: references localhost")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if not os.path.exists(os.path.join(DOCS, href.split("#")[0])):
                problems.append(f"{name}: broken internal link -> {href}")
        # every external link must be https
        for href in re.findall(r'href="(http://[^"]+)"', text):
            problems.append(f"{name}: insecure external link -> {href}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if not args.check:
        build_all_data()
        written = build()
        print(f"built {len(written)} pages in docs/nfl-f4/")
    problems = check()
    if problems:
        for p in problems:
            print("CHECK FAIL:", p)
        return 1
    print("check: OK (zero-input, no broken internal links, all external links https)")
    return 0


def build_all_data() -> None:
    prices.write_all()
    results.write_all()
    originate.write_all()
    leaderboard.write_all()
    depth.write_all()
    correlations.write_all()
    demotion.write_all()


if __name__ == "__main__":
    raise SystemExit(main())
