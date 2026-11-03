#!/usr/bin/env python3
"""Build the unified Own6 hub (docs/hub/*.html) from the committed data files.

Stdlib only. Every table body row carries at least one source link. Values that were not
confirmed are shown blank or with an UNVERIFIED badge; nothing is inferred here.
"""
import csv, html, json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
HUB = os.path.join(DOCS, "hub")
BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"
LIVE = "https://sassnarep3-star.github.io/Own6/"
E = html.escape

def rd(*a):
    with open(os.path.join(ROOT, *a), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def lnk(url, text=None):
    if not url.startswith(("http://", "https://")):
        url = BLOB + url  # repo-relative path -> GitHub blob link
        text = text or url
    return f'<a href="{E(url, quote=True)}" target="_blank" rel="noopener">{E(text or url)}</a>'

def blob(path, text=None):
    return lnk(BLOB + path, text or path)

def badge(text, kind):
    return f'<span class="b {kind}">{E(text)}</span>'

def md_inline(s):
    s = E(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: f'<a href="{BLOB}research/{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>' if not m.group(2).startswith("#") else m.group(1), s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s

NAV = [
    ("Overview", [("Home", "index"), ("Executive summary", "summary")]),
    ("Data", [("Results", "results"), ("Standings", "standings"), ("Lines", "lines"), ("Props", "props")]),
    ("Analysis", [("Forward test", "forward-test"), ("Strategies", "strategies"), ("Correlations", "correlations"), ("Validation", "validation")]),
    ("Reference", [("Sources", "sources"), ("Flagged for Review", "flagged")]),
]

def href(key):
    return key + ".html"

def page(key, title, body, lead=""):
    assets = "assets/"
    nav = ['<a class="brand" href="../index.html">OWN6</a>']
    for grp, items in NAV:
        nav.append(f'<span class="grp">{grp}</span>')
        for label, k in items:
            on = ' class="on"' if k == key else ""
            nav.append(f'<a{on} href="{href(k)}">{E(label)}</a>')
    legacy = "../"
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — Own6 NBA Lines Lab</title><link rel="stylesheet" href="{assets}hub.css"></head><body>
<header class="top">{''.join(nav)}</header>
<main><h1>{E(title)}</h1>{f'<p class="lead">{lead}</p>' if lead else ''}{body}</main>
<footer><p>Research and paper tracking only. No wagers, no betting advice, no profitability claim. Every table row links to its source; blank or UNVERIFIED means it could not be confirmed from an official page. Earlier section sites remain available: <a href="{legacy}dashboard.html">calculator</a> · <a href="{legacy}verified/">verified data</a> · <a href="{legacy}own6/">research sub-site</a> · <a href="{legacy}lab/overview.html">empirical lab</a> · <a href="{legacy}review/">independent review</a>.</p></footer>
<script src="{assets}hub.js"></script></body></html>"""
    path = os.path.join(HUB, key + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)

_tid = [0]
def table(headers, rows, filt=True, numeric=()):
    _tid[0] += 1
    tid = f"t{_tid[0]}"
    th = "".join(f"<th>{E(h)}</th>" for h in headers)
    trs = []
    for r in rows:
        tds = []
        for i, c in enumerate(r):
            cls = ' class="n"' if i in numeric else ""
            tds.append(f"<td{cls}>{c}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    f = f'<div class="tools"><input data-filter="{tid}" placeholder="Filter rows…" aria-label="Filter rows"> <span class="mut">{len(rows)} rows · click a header to sort</span></div>' if filt else ""
    return f'{f}<div class="tw"><table id="{tid}" class="sortable"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>'

def f1(x, nd=1):
    return "" if x in ("", None) else f"{float(x):.{nd}f}"

ABBR = {"WSH": "WAS", "NY": "NYK", "NO": "NOP", "SA": "SAS", "GS": "GSW"}
nz = lambda t: ABBR.get(t, t)

# ---------- load data ----------
hist = rd("data", "games_results_2026-27.csv")
new = rd("data", "results_2026-11-02.csv")
reread = {r["game_id"]: r for r in rd("data", "reverification_results_2026-11-03.csv")}
stand = rd("data", "standings_2026-27.csv")
live = rd("data", "standings_live_2026-11-03.csv")
ratings = rd("data", "team_ratings_2026-27.csv")
mkt = rd("data", "market_lines_2026-11-02.csv")
ours = rd("data", "our_lines_2026-11-02.csv")
props = rd("data", "player_props_2026-11-02.csv")
fwd = rd("data", "forward_test_2026-11-02.csv")
fsum = {r["metric"]: r["value"] for r in rd("data", "forward_test_summary_2026-11-02.csv")}
corr_csv = rd("data", "correlation_findings.csv")
sources = rd("data", "sources.csv")
games = {g["game_id"]: g for g in json.load(open(os.path.join(ROOT, "data", "games.json"), encoding="utf-8"))["rows"]}
flags_a = json.load(open(os.path.join(ROOT, "data", "flags.json"), encoding="utf-8"))["rows"]
flags_b = rd("data", "flagged_items.csv")
flags_c = rd("data", "empirical", "repo_findings.csv")
flags_h = rd("data", "hub_flags.csv")
abbr_name = {r["team_abbr"]: r["team"] for r in stand}

all_results = []
for r in hist:
    all_results.append(dict(date=r["date"], away=r["away_team"], a=int(r["away_score"]), home=r["home_team"], h=int(r["home_score"]),
                            ot=r["ot"], gid=r["game_id"], src=r["source_url"], new=False))
for r in new:
    all_results.append(dict(date=r["date"], away=r["away_team"], a=int(r["away_score"]), home=r["home_team"], h=int(r["home_score"]),
                            ot=r["overtime"], gid=r["game_id"], src=r["source_url"], new=True))
all_results.sort(key=lambda x: (x["date"], x["gid"]), reverse=True)

# ---------- stats helpers ----------
def pearson(x, y):
    n = len(x); mx = sum(x) / n; my = sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x); syy = sum((b - my) ** 2 for b in y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sxx * syy)

def fisher_ci(r, n):
    if n <= 3 or abs(r) >= 1:
        return ("", "")
    z = math.atanh(r); se = 1 / math.sqrt(n - 3)
    return (math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se))

# ================= RESULTS =================
rows = []
for r in all_results:
    verified = r["gid"] in reread or r["new"]
    st = badge("re-read on nba.com 2026-11-03", "ok") if verified else badge("prior session; score not re-read", "warn")
    score = f'{E(r["away"])} {r["a"]} – {r["h"]} {E(r["home"])}'
    rows.append([r["date"], E(r["away"]), str(r["a"]), E(r["home"]), str(r["h"]), "OT" if r["ot"] else "", r["gid"], st, lnk(r["src"], "nba.com game page")])
body = (f'<div class="banner ok">107 final scores: 92 from 2026-10-20 to 2026-11-01 (earlier sessions) and 15 from the 2026-11-02 slate (read from NBA.com on 2026-11-03). '
        f'Scores of <b>28</b> rows were re-read against NBA.com date pages this session and all matched; win-loss records recomputed from all 107 rows equal the official standings for all 30 teams (see Standings). '
        f'Home team is listed second on NBA.com and is the right-hand team here.</div>'
        + table(["Date", "Away", "Away pts", "Home", "Home pts", "OT", "Game ID", "Verification", "Source"], rows, numeric=(2, 4)))
page("results", "Game results", body, "Final scores for the 2026-27 regular season so far, one row per game, each linked to the official NBA.com game page.")

# ================= STANDINGS =================
tot = {}
for r in all_results:
    w, l = (r["home"], r["away"]) if r["h"] > r["a"] else (r["away"], r["home"])
    tot.setdefault(w, [0, 0])[0] += 1; tot.setdefault(l, [0, 0])[1] += 1
rows = []
for r in sorted(live, key=lambda x: (-int(x["w"]) / (int(x["w"]) + int(x["l"])), x["team_abbr"])):
    a = r["team_abbr"]; rc = tot.get(a, [0, 0]); ok = rc == [int(r["w"]), int(r["l"])]
    src = lnk(r["source_url"], "nba.com " + ("standings" if "standings" in r["source_url"] else "scoreboard"))
    rows.append([E(abbr_name.get(a, a)), a, r["w"], r["l"], f"{rc[0]}-{rc[1]}", badge("match", "ok") if ok else badge("MISMATCH", "bad"), src, E(r["note"])])
rt = []
for r in ratings:
    rt.append([E(r["team"]), r["team_abbr"], r["gp"], f1(r["off_rtg"]), f1(r["def_rtg"]), f1(r["net_rtg"]), f1(r["pace"], 2), badge("snapshot 2026-11-02 · not re-verified", "warn"), lnk(r["source_url"], "nba.com/stats advanced")])
body = ('<h2>Official standings (read 2026-11-03) vs. record recomputed from the results table</h2>'
        + table(["Team", "Abbr", "W", "L", "Recomputed W-L (107 games)", "Check", "Source", "Note"], rows, numeric=(2, 3))
        + '<h2>Team ratings — snapshot taken 2026-11-02</h2><div class="banner">NBA.com advanced stats are a live page that now includes the Nov 2 games, so these values cannot be reproduced today. They are not used in the forward test. Definitions: '
        + lnk("https://www.nba.com/stats/help/glossary", "NBA Stats Glossary") + '.</div>'
        + table(["Team", "Abbr", "GP", "OffRtg", "DefRtg", "NetRtg", "Pace", "Status", "Source"], rt, numeric=(2, 3, 4, 5, 6)))
page("standings", "Standings and ratings", body, "Official win-loss records cross-checked against every result row, plus the dated team-ratings snapshot.")

# ================= LINES =================
rows = []
res_by = {(r["away_team"], r["home_team"]): r for r in new}
gid_by = {(g["away_team"], g["home_team"]): gid for gid, g in games.items()}
fw = {(r["away"], r["home"]): r for r in fwd}
for m, o in zip(mkt, ours):
    k = (nz(m["away_team"]), nz(m["home_team"]))
    f = fw[k]
    tip = [g["tip_time_et"] for g in games.values() if g["away_team"].endswith(abbr_name.get(k[0], "?").split()[-1]) and g["home_team"].endswith(abbr_name.get(k[1], "?").split()[-1])]
    rows.append([f"{k[0]} @ {k[1]}", (tip[0] + " ET") if tip else "",
                 f1(f["market_home_line"]), f1(f["market_total"]), f'{m["fav_ml_current"]} / {m["dog_ml_current"]} ({E(m["favorite"])} fav)',
                 f"{float(f['p_home_market_devig']) * 100:.1f}%",
                 f1(f["own6_home_line"]), f1(f["own6_total"]), f"{float(f['p_home_own6']) * 100:.1f}%",
                 f'{res_by[k]["away_score"]}–{res_by[k]["home_score"]}',
                 badge("UNVERIFIED · secondary (ESPN feed)", "warn"),
                 lnk(m["source_url"], "ESPN odds feed") + " · " + lnk(res_by[k]["source_url"], "nba.com result") + " · " + blob("data/our_lines_2026-11-02.csv", "Own6 file")])
body = ('<div class="banner">Market numbers are DraftKings prices as relayed by ESPN\'s API — a <b>secondary</b> source, shown with an UNVERIFIED badge and flagged (H07). The capture time of each "current" line was not recorded, so it is not assumed to be the closing line. '
        'Own6 lines come from <code>scripts/model.py</code> (model v0.1, prior-games-only, pre-registered). Line convention here: home team, negative = home favoured. '
        'De-vig fixed 2026-11-03 (flag H02): proportional removal of vig from the current moneylines.</div>'
        + table(["Game", "Tip", "Mkt home line", "Mkt total", "Mkt ML fav / dog", "Mkt P(home)", "Own6 home line", "Own6 total", "Own6 P(home)", "Final (away–home)", "Status", "Sources"], rows, numeric=(2, 3, 5, 6, 7, 8)))
page("lines", "Lines — market vs. Own6 (2026-11-02 slate)", body, "The 15-game Nov 2 slate: independent Own6 spread, total and win probability next to the market, with the official final score.")

# ================= PROPS =================
rows = []
for p in props:
    rows.append([E(p["athlete"]), E(p["team"]), E(p["market"]), p["line_open"], p["line_current"], E(p["american_quotes_current_rowA_rowB"]), E(p["last_updated"]),
                 badge("UNVERIFIED · secondary (ESPN feed) · no settlement", "warn"), lnk(p["source_url"], "ESPN prop feed")])
body = ('<div class="banner">Seven player-points lines for the OKC–CLE game (ESPN feed of DraftKings). Over/under labels are not provided by the feed, so the two prices are shown as published (row A / row B) and no side is assigned. '
        'Settlement is <b>not</b> filled in: the player points were not read from an official box score in this session. Six more feed rows have unresolved athlete IDs and are withheld (see Flagged). '
        'Player-prop combos: see Correlations (teammate points) and Strategies (S-4, S-5).</div>'
        + table(["Player", "Team", "Market", "Open", "Current", "Prices (A / B)", "Feed last updated (UTC)", "Status", "Source"], rows, numeric=(3, 4)))
page("props", "Player props", body, "Player prop lines captured on 2026-11-02, with no side or result inferred.")

# ================= FORWARD TEST =================
rows = []
for r in fwd:
    rows.append([f'{r["away"]} @ {r["home"]}', r["home_margin"], f1(r["market_home_line"]), f1(r["own6_home_line"]), r["err_market"], r["err_own6"],
                 r["spread_lean"], badge(r["spread_lean_result"], {"win": "ok", "loss": "bad"}.get(r["spread_lean_result"], "info")),
                 r["total"], f1(r["market_total"]), f1(r["own6_total"]), r["total_lean"], badge(r["total_lean_result"], {"win": "ok", "loss": "bad"}.get(r["total_lean_result"], "info")),
                 lnk(r["result_source"], "nba.com result") + " · " + lnk(r["line_source"], "ESPN feed")])
def fv(k, nd=3):
    return f"{float(fsum[k]):.{nd}f}"
met = [
    ["Games", fsum["n_games"], "15 final scores from NBA.com", lnk("https://www.nba.com/games?date=2026-11-02", "nba.com scoreboard")],
    ["Margin MAE — market / Own6 (pts)", f'{fv("margin_MAE_market", 2)} / {fv("margin_MAE_own6", 2)}', "lower is better", blob("data/forward_test_summary_2026-11-02.csv", "summary csv")],
    ["Mean abs-error difference (market − Own6), 95% bootstrap CI", f'{fv("abs_margin_err_diff_market_minus_own6", 2)} [{fv("abs_margin_err_diff_ci95_lo", 2)}, {fv("abs_margin_err_diff_ci95_hi", 2)}]', "negative = market better; interval includes 0", blob("scripts/forward_test.py", "script")],
    ["Total MAE — market / Own6 (pts)", f'{fv("total_MAE_market", 2)} / {fv("total_MAE_own6", 2)}', "lower is better", blob("data/forward_test_2026-11-02.csv", "game rows")],
    ["Log-loss (home win) — market / Own6 / coin", f'{fv("logloss_market")} / {fv("logloss_own6")} / {fv("logloss_coin")}', "lower is better", blob("data/forward_test_2026-11-02.csv", "game rows")],
    ["Log-loss difference (market − Own6), 95% bootstrap CI", f'{fv("logloss_diff_market_minus_own6")} [{fv("logloss_diff_ci95_lo")}, {fv("logloss_diff_ci95_hi")}]', "negative = market better; interval includes 0", blob("scripts/forward_test.py", "script")],
    ["Brier — market / Own6", f'{fv("brier_market")} / {fv("brier_own6")}', "lower is better", blob("data/forward_test_2026-11-02.csv", "game rows")],
    ["Straight-up winners correct — market / Own6", f'{fsum["su_correct_market"]} / {fsum["su_correct_own6"]} of 15', "", blob("data/forward_test_2026-11-02.csv", "game rows")],
    ["Spread lean record (W-L-push)", f'{fsum["spread_lean_W"]}-{fsum["spread_lean_L"]}-{fsum["spread_lean_pushes"]}', f'exact binomial two-sided p = {fv("spread_lean_binom_p_two_sided_vs_50pct", 2)} vs 50%; −110 break-even is 52.4%', blob("scripts/forward_test.py", "script")],
    ["Total lean record (W-L-push)", f'{fsum["total_lean_W"]}-{fsum["total_lean_L"]}-{fsum["total_lean_pushes"]}', f'exact binomial two-sided p = {fv("total_lean_binom_p_two_sided_vs_50pct", 2)} vs 50%', blob("scripts/forward_test.py", "script")],
]
body = ('<div class="banner bad"><b>Reading this honestly:</b> with 15 games every interval includes zero. On this slate the market was at least as accurate as Own6 on margin, total and win probability (point estimates), and the spread/total leans are within coin-flip noise. '
        'This neither validates nor rejects any strategy; no gate is passed. It is a first dated, out-of-sample data point. The lean definition (side where Own6 differs from the market line) is a neutral post-hoc choice (flag H06).</div>'
        + '<h2>Summary</h2>' + table(["Measure", "Value", "Note", "Source"], met, filt=False)
        + '<h2>Per-game rows</h2><p class="mut">Margin errors are actual home margin minus the predicted home margin (positive = home did better than predicted). Leans: W = the side Own6 preferred relative to the market line covered.</p>'
        + table(["Game", "Home margin", "Mkt home line", "Own6 home line", "Err mkt", "Err Own6", "Spread lean", "Lean result", "Total pts", "Mkt total", "Own6 total", "Total lean", "Lean result", "Sources"], rows, numeric=(1, 2, 3, 4, 5, 8, 9, 10)))
page("forward-test", "Forward test — Nov 2 slate", body, "Lines published before tip-off, graded against official final scores. Descriptive only.")

# ================= STRATEGIES =================
sm = open(os.path.join(ROOT, "research", "strategies.md"), encoding="utf-8").read()
strat = []
for line in sm.splitlines():
    if line.startswith("| S-"):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        strat.append(c)
cat_note = {"S-1": "Single", "S-2": "Single", "S-3": "Single", "S-4": "Prop", "S-5": "Prop combo", "S-6": "Parlay", "S-7": "Single"}
rows = []
for c in strat:
    sid, name, cat, passed, failed, status, score = c[:7]
    data_src = {"S-1": ["data/backtest_walkforward.csv", "data/our_lines_2026-11-02.csv"], "S-2": ["data/backtest_walkforward.csv"],
                "S-3": ["data/games_results_2026-27.csv"], "S-4": ["data/player_props_2026-11-02.csv"], "S-5": ["data/correlation_findings.csv"],
                "S-6": ["data/correlation_findings.csv"], "S-7": ["data/market_lines_2026-11-02.csv"]}[sid]
    rows.append([sid, md_inline(name), md_inline(cat), md_inline(passed), md_inline(failed), md_inline(status), score,
                 badge("not eligible — skill gates G1/G2 not passed", "bad"), "—",
                 " · ".join([blob("research/strategies.md", "spec & results")] + [blob(d, d.split("/")[-1]) for d in data_src])])
body = ('<div class="banner bad"><b>No strategy qualifies for a rank or reward.</b> Rank and rewards here go only to strategies that pass the skill gates (calibration CI &gt; 0 <i>and</i> discrimination at n ≥ 100). None do. '
        'The "legacy score" column is the earlier sessions\' 2 × gates-passed − gates-failed; it counts process gates that any strategy passes, so it is shown for transparency only (flag H05).</div>'
        '<h2>Strategy registry (single bets, parlays, player props, prop combos)</h2>'
        + table(["ID", "Strategy", "Category", "Gates passed", "Failed / unmet", "Status", "Legacy score", "Hub eligibility", "Hub rank", "Source"], rows, numeric=(6,))
        + '<h2>Reward policy</h2><div class="card"><p><b>Paper units only; no money.</b> The earlier schedule (1st +20, 2nd +10, 3rd +5 paper units) is retained as a design, but this hub pays nothing until a strategy is eligible: ≥100 graded events, calibration CI strictly above zero versus the baseline, and a market-relative (CLV) result once closing lines exist. '
        'Reward design carries legal exposure (flags F01/F02): public reward contests tied to sports results were flagged for counsel. Source: ' + blob("research/strategies.md", "research/strategies.md") + ' · ' + blob("data/strategies.json", "data/strategies.json") + '.</p></div>')
page("strategies", "Strategies and leaderboard", body, "Seven pre-registered signal strategies and where each stands. Ranking is skill-gated.")

# ================= CORRELATIONS =================
H = [g for g in all_results]
hs = [g["h"] for g in H]; as_ = [g["a"] for g in H]
mg = [g["h"] - g["a"] for g in H]; tt = [g["h"] + g["a"] for g in H]
comp = [
    ("home_score vs away_score (same game, 107 games)", "same-game team-total legs", pearson(hs, as_), len(H)),
    ("home margin vs game total (same game, 107 games)", "same-game spread + total parlay legs", pearson(mg, tt), len(H)),
]
rows = []
for c in corr_csv:
    r = float(c["pearson_r"]); n = int(c["n"]); lo, hi = fisher_ci(r, n)
    pooled = c["pair"] == "same_date_game_margins"
    src = c["source_file"]
    if src.startswith("data/"):
        s = blob(src, src) + " · " + lnk("https://www.nba.com/games", "nba.com results")
    else:
        s = lnk("https://www.espn.com/nba/player/gamelog/_/id/3908809", "ESPN gamelog (Mitchell)") + " · " + lnk("https://www.espn.com/nba/player/gamelog/_/id/4066328", "ESPN gamelog (Allen)")
    sev = badge("n too small", "warn") if n < 30 else badge("usable", "ok")
    rows.append([E(c["pair"]), E(c["interpretation"]), str(n), f"{r:+.3f}", ("n/a — pairs overlap, naive CI would be too narrow" if pooled else ("" if lo == "" else f"[{lo:+.2f}, {hi:+.2f}]")), sev, "earlier session", s])
for name, why, r, n in comp:
    lo, hi = fisher_ci(r, n)
    rows.append([name, why, str(n), f"{r:+.3f}", f"[{lo:+.2f}, {hi:+.2f}]", badge("usable", "ok"), "computed this session (Pearson, Fisher-z 95% CI)",
                 blob("data/games_results_2026-27.csv", "results csv") + " · " + blob("data/results_2026-11-02.csv", "Nov 2 csv") + " · " + lnk("https://www.nba.com/games", "nba.com results")])
body = ('<div class="banner">Correlation is what makes parlays and prop combos non-independent: pricing a combination as the product of marginal probabilities is wrong when r ≠ 0. '
        'Values are Pearson r from official results (and ESPN game logs for the one player pair). Intervals are Fisher-z 95% intervals, computed here from r and n. '
        'Only rows with n ≥ 30 are treated as usable; the teammate pair (n = 6) is not. Leg-level model-error correlations cannot be estimated yet (no settled history of bets).</div>'
        + table(["Pair", "Relevant to", "n", "Pearson r", "95% CI", "Sample", "Origin", "Source"], rows, numeric=(2, 3))
        + '<h2>How correlations are used</h2><div class="tw"><table><thead><tr><th>Bet type</th><th>Rule</th><th>Source</th></tr></thead><tbody>'
        f'<tr><td>Parlay</td><td>Joint probability from a Gaussian copula with the measured r; independence is a labelled special case, not a default.</td><td>{blob("src/own6/parlay.py", "src/own6/parlay.py")} · {blob("research/correlation.md", "research/correlation.md")}</td></tr>'
        f'<tr><td>Same-game prop combo</td><td>Require r measured on ≥ 60 same-game pairs before any combo is priced (current: n = 6, so none).</td><td>{blob("research/strategies.md", "S-5 spec")}</td></tr>'
        '</tbody></table></div>')
page("correlations", "Correlations", body, "Measured dependence between legs, with sample sizes and uncertainty.")

# ================= VALIDATION =================
vm = open(os.path.join(ROOT, "research", "validation.md"), encoding="utf-8").read()
gates = []
sec = vm.split("## Gates (pre-registered)")[1].split("##")[0]
for line in sec.splitlines():
    if line.startswith("| G"):
        gates.append([x.strip() for x in line.strip().strip("|").split("|")])
rows = [[md_inline(g[0]), md_inline(g[1]), md_inline(g[2]), blob("research/validation.md", "research/validation.md")] for g in gates]
bt = [
    ["Log-loss (model / coin / home-win baseline)", "0.6747 / 0.6932 / 0.7059", "n=82, walk-forward"],
    ["Brier (model / coin)", "0.2408 / 0.2500", "corrected 2026-11-03 (flag H03)"],
    ["Straight-up accuracy (model favourite)", "59.8% (49 of 82)", "gate needs n ≥ 100"],
    ["Paired log-loss improvement vs baseline, 95% bootstrap CI", "+0.0312 [−0.0130, +0.0733]", "crosses 0 → G1 FAIL"],
]
bt_rows = [[a, b, c, blob("verification/backtest_metrics.csv", "backtest_metrics.csv") + " · " + blob("data/backtest_walkforward.csv", "game rows") + " · " + blob("scripts/audit_integration.py", "recomputed by audit")] for a, b, c in bt]
luck = []
sec2 = vm.split("## Luck-removal protocol (applied to every strategy)")[1].split("## Gates")[0]
for line in sec2.splitlines():
    if line.startswith("- **"):
        m = re.match(r"- \*\*(.+?)\*\*\s*[—-]?\s*(.*)", line)
        luck.append([md_inline(m.group(1)), md_inline(m.group(2)), blob("research/validation.md", "research/validation.md")])
reg = [
    ["docs/own6 · research/validation.md", "G1–G6: calibration, discrimination, correlation, multiple testing, CLV, sample size", lnk(LIVE + "docs/own6/validation.html", "own6 validation")],
    ["docs/verified · data/methodology.json", "G1–G8: legal review, provenance, integrity screen, out-of-sample, sample size, CLV, multiple-testing significance, correlation", lnk(LIVE + "docs/verified/methodology.html", "verified methodology")],
    ["docs/lab · nba_lab/gates.py", "10 fail-closed gates on an authorized-data ledger", lnk(LIVE + "docs/lab/methodology.html", "lab methodology")],
    ["src/own6/validation.py", "G1–G6: walk-forward, n ≥ 200, Brier/log-loss vs market, CLV t ≥ 2, binomial+Bonferroni, bootstrap ROI CI", blob("src/own6/validation.py", "validation.py")],
]
body = ('<div class="banner">A strategy is <b>skill-eligible</b> only if G1 (calibration CI strictly &gt; 0 against a baseline) <i>and</i> G2 (discrimination at n ≥ 100) pass. Everything else is tracking. Process gates (G3, G4) do not make a strategy eligible. Current eligible strategies: <b>0</b>.</div>'
        '<h2>Gates in force on this hub</h2>' + table(["Gate", "Requirement", "Status on 2026-11-02", "Source"], rows, filt=False)
        + '<h2>Luck-removal protocol</h2>' + table(["Rule", "Detail", "Source"], luck, filt=False)
        + '<h2>Backtest evidence (recomputed by the audit script)</h2>' + table(["Metric", "Value", "Note", "Source"], bt_rows, filt=False)
        + '<h2>Other gate registries in the repo (flag H04)</h2><p class="mut">The same gate label means different things on different earlier pages. They are all kept; this hub does not renumber them.</p>' + table(["Where", "Gates", "Source"], [[a, b, c] for a, b, c in reg], filt=False))
page("validation", "Validation gates", body, "What a strategy must pass before it can rank, and how luck is removed.")

# ================= SOURCES =================
rows = []
for s in sources:
    rows.append([s["id"], E(s["claim_or_input"]), E(s["official_source"]), badge(s["status"], "ok" if s["status"].startswith("verified-direct") and "limited" not in s["status"] else "warn"), E(s["verified_via"]), lnk(s["url"])])
extra = [
    ("N1", "Final scores, 2026-11-02 slate and re-verified dates", "NBA.com games & scores", "read 2026-11-03", "https://www.nba.com/games?date=2026-11-02"),
    ("N2", "Official standings W-L (30 teams)", "NBA.com standings", "read 2026-11-03", "https://www.nba.com/standings"),
    ("N3", "IND–BKN 2026-10-25 game card", "NBA.com game page", "read 2026-11-03", "https://www.nba.com/game/ind-vs-bkn-0022600113"),
    ("N4", "Terms of use (sections 1 and 9)", "NBA.com Terms of Use", "read by earlier sessions; not re-read here", "https://www.nba.com/termsofuse"),
    ("N5", "Official partner list (DraftKings listed)", "NBA gaming partners and operators", "read by earlier session; not re-read here", "https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2"),
    ("N6", "Repository state and PR timestamps (PR #15, #18, #19)", "GitHub", "queried 2026-11-03 via GitHub API", "https://github.com/sassnarep3-star/Own6/pulls?q=is%3Apr"),
]
for i, c, o, v, u in extra:
    rows.append([i, E(c), E(o), badge("verified-direct" if "2026-11-03" in v else "earlier session", "ok" if "2026-11-03" in v else "warn"), E(v), lnk(u)])
body = table(["ID", "Used for", "Source", "Status", "How verified", "Link"], rows)
page("sources", "Source registry", body, "Official pages behind every table. Rows N1–N6 were added in this session.")

# ================= FLAGGED =================
rows = []
for f in flags_h:
    rows.append([f["id"], badge(f["severity"], {"High": "bad", "Medium": "warn"}.get(f["severity"], "info")), E(f["category"]), E(f["item"]), E(f["detail"]), E(f["status"]), lnk(f["source_url"]), E(f["action_requested"]), "this session"])
for f in flags_a:
    rows.append([f["id"], badge(f["severity"], {"High": "bad", "Medium": "warn"}.get(f["severity"], "info")), E(f["category"]), E(f["item"]), E(f["detail"]), "needs review", lnk(f["source_url"]), E(f.get("action_requested", "")), "docs/verified"])
for i, f in enumerate(flags_b, 1):
    rows.append([f"B{i:02d}", badge("—", "info"), E(f["category"]), E(f["item"]), E(f["detail"]), E(f["status"]), lnk(f["source_url"]), "", "docs/own6"])
for f in flags_c:
    rows.append([f["id"], badge(f["severity"], {"High": "bad", "Medium": "warn"}.get(f["severity"], "info")), "Repo audit", E(f["finding"] + " (" + f["file"] + " " + f["lines"] + ")"), E(f["detail"]), E(f["status"]), lnk(f["source_url"]), E(f["action"]), "docs/lab"])
body = (f'<div class="banner">{len(rows)} items from every session in one table: {len(flags_h)} from this session (H01–H15), {len(flags_a)} from the verified dashboard (F01–F16), {len(flags_b)} from the research sub-site (B01–B09) and {len(flags_c)} repo-audit findings (R01–R20). '
        'Overlaps between earlier lists are not de-duplicated. "fixed" items are corrected on this branch; "needs review" and "unverified" items do not block publication.</div>'
        + table(["ID", "Severity", "Category", "Item", "Detail", "Status", "Source", "Action requested", "Origin"], rows))
page("flagged", "Flagged for Review", body, "Irregularities, unverified values and open decisions, each with a source link, for manual review.")

# ================= SUMMARY =================
body = f"""
<div class="banner bad"><b>Bottom line:</b> no Own6 strategy has shown a statistically supported edge. The first dated forward test (15 games) found the market at least as accurate as Own6 on margin, total and win probability, with all intervals including zero. No profitability claim is made, no rewards are paid, and no wager is placed.</div>
<h2>What the project does</h2>
<div class="tw"><table><thead><tr><th>Goal</th><th>Where it stands</th><th>Evidence</th></tr></thead><tbody>
<tr><td>Originate own lines</td><td>Own6 model v0.1 (shrunk venue-adjusted margins, prior games only) gives spread, total and win probability. Walk-forward on 82 games: log-loss 0.6747 vs 0.7059 baseline, but the improvement CI [−0.013, +0.073] includes 0.</td><td>{blob("scripts/model.py", "model.py")} · {blob("verification/backtest_metrics.csv", "backtest_metrics.csv")}</td></tr>
<tr><td>Single bets, parlays, prop combos</td><td>7 pre-registered strategies; none validated. Parlay legs inherit the singles' failed calibration; prop-combo correlation measured on only 6 games.</td><td>{blob("research/strategies.md", "strategies.md")} · {blob("data/correlation_findings.csv", "correlation csv")}</td></tr>
<tr><td>Correlation values</td><td>Same-game home/away points r = {pearson(hs, as_):+.2f} and margin/total r = {pearson(mg, tt):+.2f} (n = 107); cross-game same-date margins r = +0.11 (n = 357); teammate points r = −0.42 (n = 6, unusable).</td><td><a href="correlations.html">Correlations page</a> · {blob("data/correlation_findings.csv", "correlation csv")} · {blob("data/games_results_2026-27.csv", "results csv")}</td></tr>
<tr><td>Remove luck / skill only</td><td>Walk-forward only, shrinkage, baselines, bootstrap CIs, trial logging, skill-eligibility gate. 0 strategies eligible.</td><td><a href="validation.html">Validation page</a> · {blob("research/validation.md", "validation.md")}</td></tr>
<tr><td>Leaderboard and rewards</td><td>Skill-gated. No rank and no paper reward awarded.</td><td><a href="strategies.html">Strategies page</a> · {blob("research/strategies.md", "strategies.md")}</td></tr>
</tbody></table></div>
<h2>Findings of the line-by-line review (2026-11-03)</h2>
<div class="tw"><table><thead><tr><th>Finding</th><th>Impact</th><th>Status</th><th>Source</th></tr></thead><tbody>
<tr><td>Live landing page showed raw git conflict markers (H01)</td><td>Broken first impression, navigation lost</td>{'<td>fixed</td>'}<td>{lnk(LIVE + "docs/", "live page (pre-fix)")}</td></tr>
<tr><td>Market implied probability formula wrong (H02)</td><td>"Edge vs fair" off by about 10–17 points on every row</td><td>fixed</td><td>{blob("scripts/model.py", "model.py")}</td></tr>
<tr><td>Brier score published as 0.6654/0.6946; real 0.2408/0.2500 (H03)</td><td>Misstated metric</td><td>fixed</td><td>{blob("data/backtest_walkforward.csv", "backtest rows")}</td></tr>
<tr><td>Leaderboard scored process compliance (H05) and gate numbering conflicts (H04)</td><td>Ranking not skill-based</td><td>hub rule applied; owner to confirm</td><td>{blob("research/strategies.md", "strategies.md")}</td></tr>
<tr><td>Odds are from ESPN's DraftKings feed, not an official odds source (H07)</td><td>Cannot be verified as official</td><td>shown UNVERIFIED</td><td>{lnk("https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "NBA partner list")}</td></tr>
<tr><td>NBA.com Terms §§1 and 9 limit gambling-related use of NBA statistics (H08)</td><td>Rights and legal exposure; Korean-law flags F01/F02</td><td>needs review</td><td>{lnk("https://www.nba.com/termsofuse", "NBA Terms of Use")}</td></tr>
</tbody></table></div>
<h2>Verified this session</h2>
<div class="tw"><table><thead><tr><th>Check</th><th>Result</th><th>Source</th></tr></thead><tbody>
<tr><td>Nov 2 final scores (15 games)</td><td>Read from NBA.com; added with per-row links</td><td>{lnk("https://www.nba.com/games?date=2026-11-02", "nba.com scoreboard")}</td></tr>
<tr><td>13 historical scores re-read (Oct 20, 22, 25 IND–BKN, 29, Nov 1)</td><td>13 of 13 match</td><td>{blob("data/reverification_results_2026-11-03.csv", "reverification csv")}</td></tr>
<tr><td>W-L of all 30 teams recomputed from 107 rows vs official standings</td><td>30 of 30 match</td><td>{lnk("https://www.nba.com/standings", "nba.com standings")}</td></tr>
<tr><td>Backtest metrics recomputed from game rows</td><td>match published CSV; Brier typo found</td><td>{blob("scripts/audit_integration.py", "audit_integration.py")}</td></tr>
</tbody></table></div>
<h2>Not verified</h2>
<p class="mut">79 of 107 score rows were not re-read at score level; team-ratings snapshot not reproducible now; odds and props are secondary-source; props are unsettled; correlation of model errors across legs cannot be estimated until settled history exists; NBA rights and Korean-law questions need counsel. All are on the <a href="flagged.html">Flagged for Review</a> page.</p>
<h2>Next steps that would move the needle</h2>
<p class="mut">(1) Resolve rights/legal review (H08, F01). (2) Obtain an authorised odds and closing-line source with capture times (H07). (3) Grade each new slate with <code>scripts/forward_test.py</code> and accumulate ≥ 100 games. (4) Rewrite the S-1 rule unambiguously before further grading (H06).</p>
"""
page("summary", "Executive summary", body, "What was built, what was found, what is and is not verified.")

# ================= HOME =================
nres = len(all_results)
cards = [
    ("Executive summary", "Findings, fixes and what is unverified.", "summary.html"),
    ("Results", f"{nres} official final scores with links.", "results.html"),
    ("Standings", "Official W-L vs recomputed; ratings snapshot.", "standings.html"),
    ("Lines", "Market vs Own6 for the Nov 2 slate.", "lines.html"),
    ("Props", "Seven player-points lines, unsettled.", "props.html"),
    ("Forward test", "15 games graded out-of-sample.", "forward-test.html"),
    ("Strategies", "7 strategies; skill-gated leaderboard.", "strategies.html"),
    ("Correlations", "Parlay and prop-combo dependence.", "correlations.html"),
    ("Validation", "Gates and luck-removal protocol.", "validation.html"),
    ("Sources", "Official pages behind every table.", "sources.html"),
    ("Flagged for Review", f"{len(flags_h)+len(flags_a)+len(flags_b)+len(flags_c)} open items with source links.", "flagged.html"),
]
body = f"""
<div class="grid">
<div class="card"><div class="kpi">0<small>strategies passing skill gates</small></div></div>
<div class="card"><div class="kpi">{nres}<small>official results tabulated</small></div></div>
<div class="card"><div class="kpi">30 / 30<small>teams' W-L match official standings</small></div></div>
<div class="card"><div class="kpi">15<small>games in first forward test (market ≥ Own6)</small></div></div>
</div>
<div class="banner">Own6 originates its own NBA lines and tests them against official results. <b>No edge is claimed.</b> Odds data is secondary-source and flagged. Research and paper tracking only.</div>
<h2>Browse by category</h2>
<div class="grid">{''.join(f'<div class="card"><h3><a href="{h}">{E(t)}</a></h3><p>{E(d)}</p></div>' for t, d, h in cards)}</div>
<h2>Earlier section sites (kept)</h2>
<p class="mut"><a href="../index.html">Site home</a> · <a href="../dashboard.html">Own-line calculator (manual input)</a> · <a href="../verified/">Verified data (schedule, Korean law, NBA policy)</a> · <a href="../own6/">Research sub-site</a> · <a href="../lab/overview.html">Fail-closed empirical lab</a> · <a href="../review/">Independent review</a> · <a href="../strategies.html">Original strategy pages</a></p>
"""
page("index", "Own6 — NBA Lines Lab", body, "Originate your own NBA lines, test them against official results, and rank strategies on skill rather than luck.")
print("hub built: index + 11 pages")
