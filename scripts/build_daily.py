#!/usr/bin/env python3
"""Build the 2026-11-05 verified snapshot dashboard into docs/daily/.

Deterministic: reads data/official_2026_11_05/*.csv and analysis.json and
writes static HTML. No network, no timestamps, no randomness.

    python3 scripts/daily_analysis.py
    python3 scripts/build_daily.py
    python3 scripts/check_daily.py
"""
from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "official_2026_11_05"
OUT = ROOT / "docs" / "daily"

CSS = """\
:root{--bg:#0b0f16;--panel:#131a25;--panel2:#0f151e;--line:#243040;--text:#e8eef7;
--muted:#93a4bb;--accent:#4ade80;--warn:#fbbf24;--bad:#f87171;--link:#7dd3fc}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 -apple-system,
BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
nav.top{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:4px 18px;
align-items:center;padding:12px 22px;background:rgba(11,15,22,.94);
border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
nav.top a{color:var(--muted);text-decoration:none;font-size:13.5px;padding:3px 0}
nav.top a:hover{color:var(--text)}
nav.top a.brand{color:var(--text);font-weight:700;letter-spacing:.06em}
nav.top a.active{color:var(--accent)}
main{max-width:1180px;margin:0 auto;padding:30px 22px 70px}
h1{font-size:clamp(26px,4vw,38px);line-height:1.15;margin:.2em 0 .4em}
h2{font-size:21px;margin:2em 0 .5em}
h3{font-size:16px;margin:1.4em 0 .4em;color:var(--text)}
p{color:var(--muted);max-width:88ch}
a{color:var(--link)}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:11.5px;
color:var(--accent);font-weight:700;margin:0 0 6px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
gap:12px;margin:20px 0 6px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.tile span{display:block;font-size:11.5px;text-transform:uppercase;letter-spacing:.08em;
color:var(--muted)}
.tile strong{display:block;font-size:24px;margin-top:4px}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:14px 0 6px}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:640px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel2);color:var(--muted);font-size:11.5px;text-transform:uppercase;
letter-spacing:.07em;white-space:nowrap}
tbody tr:hover{background:#161f2b}
tbody tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.empty{background:repeating-linear-gradient(135deg,#18202c,#18202c 6px,#141b25 6px,#141b25 12px)}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;
font-weight:600;border:1px solid}
.ok{color:var(--accent);border-color:#1f6f45;background:#0f2418}
.warn{color:var(--warn);border-color:#7a5a12;background:#241c07}
.bad{color:var(--bad);border-color:#7a2222;background:#240d0d}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--warn);
border-radius:10px;padding:14px 18px;margin:18px 0}
.note p{margin:.35em 0}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:12.5px;
padding:18px 22px;max-width:1180px;margin:0 auto}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:16px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
padding:16px;text-decoration:none;color:var(--text)}
.card:hover{border-color:#3b5170}
.card h3{margin:0 0 6px;font-size:15px}
.card p{margin:0;font-size:13px;color:var(--muted)}
code{background:#0d131c;border:1px solid var(--line);border-radius:5px;padding:1px 5px;font-size:12.5px}
"""

NAV = [
    ("index.html", "Overview"),
    ("standings.html", "Standings"),
    ("results.html", "Results"),
    ("slate.html", "Forward slate"),
    ("signals.html", "Signal test"),
    ("correlations.html", "Correlation"),
    ("validation.html", "Validation gates"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]

NBA = "https://www.nba.com"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def link(url: str, text: str | None = None) -> str:
    label = escape(text or url)
    return f'<a href="{escape(url)}" rel="noopener">{label} ↗</a>'


def pill(status: str) -> str:
    klass = {"verified": "ok", "pass": "ok", "unverified": "bad", "fail": "bad",
             "needs review": "warn", "not met": "bad", "open": "warn"}[status]
    return f'<span class="pill {klass}">{escape(status)}</span>'


def page(slug: str, title: str, body: str) -> str:
    nav = []
    for href, label in NAV:
        active = ' class="active"' if href == slug else ""
        nav.append(f'<a href="{href}"{active}>{escape(label)}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Own6 verified snapshot</title>
<meta name="description" content="Own6 NBA line research: official-source verified 5 November 2026 snapshot. Research only, no picks, no betting advice.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<nav class="top" aria-label="Section navigation">
<a class="brand" href="index.html">OWN6 / DAILY VERIFY</a>
{''.join(nav)}
</nav>
<main>
{body}
</main>
<footer>
<p>Snapshot read from NBA.com on 2026-11-05. Research and record-keeping only: no picks,
no prices, no wagers, no profitability claim. NBA statistics and content are the property
of the NBA Entities — see the <a href="https://www.nba.com/termsofuse">NBA Terms of Use</a>
and the <a href="flagged.html">Flagged for Review</a> page. Data: Facts only; every table
row links to the official page that was read.</p>
</footer>
</body>
</html>
"""


def table(headers: list[str], body_rows: list[str]) -> str:
    head = "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
    return (f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body_rows)}</tbody></table></div>')


def main() -> int:
    data = json.loads((DATA / "analysis.json").read_text(encoding="utf-8"))
    standings = rows(DATA / "standings.csv")
    results = rows(DATA / "results_2026_11_04.csv")
    slate = rows(DATA / "slate_2026_11_05_06.csv")
    prior = {r["team_abbr"]: (int(r["w"]), int(r["l"])) for r in rows(ROOT / "data" / "standings_live_2026-11-03.csv")}
    cons = data["consistency"]
    walk = data["model"]["walk_forward"]
    corr = data["correlations"]
    walls = [r for r in data["slate"]]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")

    # ---------------------------------------------------------------- index
    findings = [
        ("All 121 committed final scores reconcile to today's official standings",
         f"{cons['standings_2026_11_05_matches']}/{cons['standings_2026_11_05_total']} team records match",
         "verified",
         "https://www.nba.com/standings",
         "standings.html"),
        ("The same archive, cut at 2 Nov, reconciles to the 3 Nov standings snapshot",
         f"{cons['standings_2026_11_03_matches']}/{cons['standings_2026_11_03_total']} team records match",
         "verified",
         "https://www.nba.com/standings",
         "results.html"),
        ("14 new 4 Nov final scores read from official NBA.com game cards",
         f"{cons['nov4_rows']} games · {cons['teams_in_nov4_delta']} teams moved by exactly one game",
         "verified",
         "https://www.nba.com/games?date=2026-11-04",
         "results.html"),
        ("The 3 Nov page labelled 'live' is already stale against today's official page",
         "e.g. Philadelphia 7-1 → 8-1, Detroit 6-1 → 6-2",
         "needs review",
         "https://www.nba.com/standings",
         "flagged.html"),
        ("Team-rating signal, walk-forward, 61 out-of-sample games",
         f"winner accuracy {walk['winner_accuracy']:.1%} vs {walk['home_always_accuracy']:.1%} always-home; "
         f"McNemar exact p={walk['mcnemar_exact_p_two_sided']}",
         "needs review",
         "https://www.nba.com/games",
         "signals.html"),
        ("Brier skill of that signal vs home-team base rate",
         f"{walk['brier_skill_score']:+.3f} (bootstrap CI {walk['brier_skill_score_ci95_low']:+.3f} to "
         f"{walk['brier_skill_score_ci95_high']:+.3f}) — interval includes zero",
         "unverified",
         "https://www.nba.com/games",
         "signals.html"),
        ("Game margin vs game total correlation, 121 official finals",
         f"r={corr['margin_vs_total']['r']:+.3f} "
         f"[{corr['margin_vs_total']['ci95_low']:+.3f}, {corr['margin_vs_total']['ci95_high']:+.3f}]",
         "verified",
         "https://www.nba.com/games",
         "correlations.html"),
        ("Player-prop and parlay-leg correlations",
         "blank — no licensed player-level archive, and NBA Terms §9(iv) bars gambling use",
         "unverified",
         "https://www.nba.com/termsofuse",
         "correlations.html"),
        ("Market prices for the forward slate",
         "blank — no official sportsbook price source is configured",
         "unverified",
         "https://www.nba.com/termsofuse",
         "slate.html"),
        ("Leaderboard entries clearing every gate",
         "0 — rights gate fails, sample is 4 games per team, no market benchmark",
         "fail",
         "https://www.nba.com/termsofuse",
         "validation.html"),
    ]
    frows = []
    for finding, value, status, source, anchor in findings:
        frows.append(
            f"<tr><td>{escape(finding)}</td><td>{escape(value)}</td>"
            f"<td>{pill(status)}</td><td>{link(source)}</td>"
            f'<td><a href="{anchor}">detail →</a></td></tr>'
        )
    cards = [
        ("standings.html", "Standings · 30 rows", "Conference, rank, W-L, pct, games behind, each row linked to nba.com/standings."),
        ("results.html", "Results · 14 games", "4 Nov final scores with official game-card links and a per-team delta check."),
        ("slate.html", "Forward slate · 11 games", "5–6 Nov tip times and model line estimates; market columns blank and flagged."),
        ("signals.html", "Signal test", "Walk-forward margin/total model, proper scoring, bootstrap and McNemar luck tests."),
        ("correlations.html", "Correlation", "Measured game-level dependence, plus blank prop cells where no official data exists."),
        ("validation.html", "Validation gates", "Eight gates per candidate with pass/fail reasons and the leaderboard result."),
        ("sources.html", "Sources", "Every official page read today, with what it does and does not support."),
        ("flagged.html", "Flagged for Review", "Rights, missing prices, missing props, sample size and naming irregularities."),
    ]
    card_html = "".join(
        f'<a class="card" href="{href}"><h3>{escape(title)}</h3><p>{escape(text)}</p></a>'
        for href, title, text in cards
    )
    index_body = f"""
<p class="eyebrow">Verified snapshot · 5 November 2026</p>
<h1>NBA lines research, checked against official pages</h1>
<p>This section is rebuilt from pages I read on NBA.com on 2026-11-05: the standings table,
the 4 November scoreboard with one game card per match, and the schedule listing that carries
the 5–6 November slate. Every table row links to the page it came from. Where an official
source does not exist, the cell is left blank and flagged — it is never filled by inference.</p>
<div class="tiles">
  <div class="tile"><span>Final scores reconciled</span><strong>{cons['games_total']}</strong></div>
  <div class="tile"><span>Standings rows matched</span><strong>{cons['standings_2026_11_05_matches']}/30</strong></div>
  <div class="tile"><span>Forward games priced by model</span><strong>{len(slate)}</strong></div>
  <div class="tile"><span>Validated strategies</span><strong>0</strong></div>
</div>
<h2>What the verification found table by table</h2>
<p>Status vocabulary: <strong>verified</strong> means the value was read from the linked
official page; <strong>needs review</strong> means the value is real but not yet proven to be
skill; <strong>unverified</strong> means the cell is blank and no official source exists.</p>
{table(["Finding", "Published value", "Status", "Official source", "Page"], frows)}
<h2>Browse the snapshot</h2>
<div class="cards">{card_html}</div>
<div class="note">
<p><strong>What this is not.</strong> There are no picks here, no sportsbook prices, no ROI and no
"lock" of any kind. The model numbers are labelled estimates computed from 121 official final
scores; they are compared against no market, so they cannot show an edge.
The rights gate (NBA Terms of Use §1 and §9) is unresolved for any gambling-related reuse.</p>
<p><strong>Luck control.</strong> A strategy is only promoted if its out-of-sample score beats a
documented baseline with an interval that excludes luck, and if it survives a market benchmark.
Today's candidate fails the interval test, the sample-size gate and the market gate, so it sits on
the board as <em>unqualified</em> with the reason shown.</p>
</div>
"""
    (OUT / "index.html").write_text(page("index.html", "Verified snapshot", index_body), encoding="utf-8")

    # ------------------------------------------------------------ standings
    srows = []
    for row in standings:
        abbr = row["team_abbr"]
        before = prior.get(abbr)
        if before is None:
            delta = "—"
        else:
            dw = int(row["w"]) - before[0]
            dl = int(row["l"]) - before[1]
            delta = f"{dw:+d}W / {dl:+d}L"
        srows.append(
            f"<tr><td>{escape(row['conference'])}</td><td class='num'>{escape(row['rank'])}</td>"
            f"<td>{escape(row['team'])}</td><td class='num'>{escape(row['w'])}–{escape(row['l'])}</td>"
            f"<td class='num'>{escape(row['win_pct'])}</td><td class='num'>{escape(row['gb'])}</td>"
            f"<td class='num'>{escape(delta)}</td>"
            f"<td>{link(row['source_url'])} <small>read {escape(row['read_on'])}</small></td></tr>"
        )
    standings_body = f"""
<p class="eyebrow">Category · Standings</p>
<h1>2026-27 standings, read 5 November 2026</h1>
<p>Thirty rows, copied one by one from the official standings table. The last column shows how
each record moved since the 3 November snapshot; every team that played on 4 November moved by
exactly one game and the two idle teams did not move. Sum of wins ({sum(int(r['w']) for r in standings)})
equals sum of losses ({sum(int(r['l']) for r in standings)}), which is the arithmetic check that no
row was mistyped.</p>
{table(["Conf.", "Seed", "Team", "W–L", "Win%", "GB", "Since 3 Nov", "Official source"], srows)}
<div class="note"><p><strong>Earlier irregularity closed.</strong> A previous session left the Utah row
citing a schedule page because the standings text was cut off. Today's read returns the Utah row
directly from the standings table (1–7), so that row is now sourced to the standings page itself.
The earlier note is kept in the repository history, not silently deleted.</p></div>
"""
    (OUT / "standings.html").write_text(page("standings.html", "Standings", standings_body), encoding="utf-8")

    # -------------------------------------------------------------- results
    rrows = []
    for row in results:
        away, home = row["away_team"], row["home_team"]
        rrows.append(
            f"<tr><td>{escape(row['date'])}</td><td>{escape(away)} @ {escape(home)}</td>"
            f"<td class='num'>{escape(row['away_score'])}–{escape(row['home_score'])}</td>"
            f"<td>{escape(row['status'])}</td><td><code>{escape(row['game_id'])}</code></td>"
            f"<td>{link(row['source_url'], 'NBA.com game card')}</td></tr>"
        )
    results_body = f"""
<p class="eyebrow">Category · Results</p>
<h1>4 November 2026 final scores</h1>
<p>Fourteen games, each read from its own official game card. Every team that appears moved its
record by exactly one game between the 3 and 5 November standings snapshots
({cons['teams_in_nov4_delta']} of 30 teams; idle: {escape(', '.join(cons['teams_idle_nov4']))}).
That delta check is what makes this archive usable as model input: a mis-typed score would show up
as a team whose record did not move.</p>
{table(["Date", "Matchup", "Final", "Status", "Game ID", "Official source"], rrows)}
<p>Two games went to overtime (Utah–New Orleans, Miami–LA Clippers); the card labels them
<code>Final/OT</code>. Overtime scores are kept as-is because the model below scores margin and
total, not regulation-only results.</p>
<div class="note"><p><strong>Archive boundary.</strong> This page publishes only the 14 scores read
today. The older 107-game archive (20 Oct – 2 Nov) is used by the model as training data and is
validated by the standings reconciliation shown on the
<a href="signals.html">signal page</a>; its individual score cells were read by earlier sessions,
not re-read today — that is disclosed on <a href="flagged.html">Flagged for Review</a>.</p></div>
"""
    (OUT / "results.html").write_text(page("results.html", "Results", results_body), encoding="utf-8")

    # ---------------------------------------------------------------- slate
    trows = []
    for row in walls:
        trows.append(
            f"<tr><td>{escape(row['date'])}</td><td>{escape(row['tip_et'])}</td>"
            f"<td>{escape(row['away_team'])} @ {escape(row['home_team'])}</td>"
            f"<td>{escape(row['competition'])}</td>"
            f"<td class='num'>{row['model_home_margin']:+.1f}<br><small>{row['model_margin_low80']:+.1f} to {row['model_margin_high80']:+.1f}</small></td>"
            f"<td class='num'>{row['model_total']:.1f}<br><small>{row['model_total_low80']:.1f} to {row['model_total_high80']:.1f}</small></td>"
            f"<td class='num'>{row['model_home_win_prob']:.3f}</td>"
            f'<td class="empty" aria-label="blank, unverified"></td>'
            f'<td class="empty" aria-label="blank, unverified"></td>'
            f"<td>{link(row['source_url'], 'NBA.com game page')}</td></tr>"
        )
    slate_body = f"""
<p class="eyebrow">Category · Forward slate</p>
<h1>5–6 November 2026: originated lines with blank markets</h1>
<p>Eleven games: two regular-season games tonight and nine NBA Cup group games on 6 November.
Tip times and game IDs are read from the official NBA.com game/schedule pages. The model columns
are our own origination — a ridge team-rating model fitted only on games that finished before the
game being priced, with an 80% interval from its own out-of-sample residual spread.</p>
{table(["Date", "Tip (ET)", "Matchup", "Competition", "Model home margin (80%)",
        "Model total (80%)", "Model home win p", "Market spread", "Market total", "Official source"], trows)}
<div class="note">
<p><strong>Why the market columns are blank.</strong> The project requires an official, timestamped
price source to compare against. No sportsbook or exchange feed is configured, and NBA.com does not
publish betting prices, so both columns stay empty rather than being filled from a secondary
aggregator. Blank means "not confirmed", never zero. Flagged as F04 on
<a href="flagged.html">Flagged for Review</a>.</p>
<p><strong>How to read the intervals.</strong> The 80% band is
±{1.2816 * data['model']['final_sigma_margin']:.1f} points on the margin and
±{1.2816 * data['model']['final_sigma_total']:.1f} on the total, taken from the model's final
residual spread ({data['model']['final_sigma_margin']:.2f} and
{data['model']['final_sigma_total']:.2f}). With roughly four games per team these bands are wide
and the point estimates should be treated as provisional, not as a line you could bet into.</p>
</div>
"""
    (OUT / "slate.html").write_text(page("slate.html", "Forward slate", slate_body), encoding="utf-8")

    # -------------------------------------------------------------- signals
    s2 = walk
    metric_rows = [
        ("Out-of-sample games scored", f"{s2['n_predictions']}", "—",
         "Expanding-window refit before every game; first scored game <code>%s</code>." % s2["first_predicted_game"], "games"),
        ("Mean absolute error, margin", f"{s2['mae_margin']:.2f} pts", "—",
         "How far the originated spread lands from the actual margin.", "games"),
        ("RMSE, margin", f"{s2['rmse_margin']:.2f} pts", "—",
         "Penalises the blow-ups; sets the 80% band width.", "games"),
        ("Mean absolute error, total", f"{s2['mae_total']:.2f} pts", "—",
         "Total-points origination error against the official final totals.", "games"),
        ("Winner accuracy", f"{s2['winner_accuracy']:.1%}",
         f"{s2['winner_accuracy_ci95_low']:.1%}–{s2['winner_accuracy_ci95_high']:.1%}",
         "Wilson 95% interval on 61 predictions.", "games"),
        ("Always-pick-home benchmark", f"{s2['home_always_accuracy']:.1%}", "—",
         "The naive benchmark any signal must beat.", "games"),
        ("Accuracy edge over that benchmark", f"{s2['accuracy_vs_home_always']:+.1%}", "—",
         "Point estimate only; see the paired test below.", "games"),
        ("Paired McNemar test", f"p = {s2['mcnemar_exact_p_two_sided']:.4f}", "—",
         f"Discordant games: model right / benchmark wrong {s2['mcnemar_model_only_correct']}, "
         f"benchmark right / model wrong {s2['mcnemar_home_only_correct']}. "
         "Exact two-sided; above 0.05, so not significant.", "standings"),
        ("Brier score, model", f"{s2['brier_model']:.4f}", "—",
         "Proper scoring rule on the home-win probability.", "games"),
        ("Brier score, home-rate baseline", f"{s2['brier_home_rate_baseline']:.4f}", "—",
         "Same games, constant training home-win rate.", "games"),
        ("Brier skill score", f"{s2['brier_skill_score']:+.4f}",
         f"{s2['brier_skill_score_ci95_low']:+.4f} to {s2['brier_skill_score_ci95_high']:+.4f}",
         "1 − model/baseline. The bootstrap interval contains zero: the point estimate is not "
         "distinguishable from luck at 95%.", "games"),
    ]
    mrows = []
    for name, value, interval, note, anchor in metric_rows:
        mrows.append(
            f"<tr><td>{escape(name)}</td><td class='num'><strong>{escape(value)}</strong></td>"
            f"<td class='num'>{escape(interval)}</td><td>{note}</td>"
            f"<td>{link(NBA + '/standings' if anchor == 'standings' else NBA + '/games', 'NBA.com')}</td></tr>"
        )
    ratings = data["model"]["ratings"]
    rated = sorted(ratings.items(), key=lambda kv: -kv[1])
    rrows2 = []
    for team, value in rated:
        rrows2.append(
            f"<tr><td>{escape(team)}</td><td class='num'>{value:+.2f}</td>"
            f"<td class='num'>{data['model']['total_effects'][team]:+.2f}</td>"
            f"<td>{link(NBA + '/standings')}</td></tr>"
        )
    signals_body = f"""
<p class="eyebrow">Category · Signal test</p>
<h1>Is there skill, or is it luck?</h1>
<p>The candidate signal is deliberately simple: a ridge team-rating model fitted on point margin
and total, with one league-wide home advantage, refitted before every game so no future result can
leak backwards. It is scored on 61 games it had never seen, with a proper scoring rule, a bootstrap
interval and a paired test against the naive benchmark.</p>
{table(["Metric (walk-forward)", "Value", "95% interval", "What it means", "Input source"], mrows)}
<h2>Verdict</h2>
<div class="note">
<p><strong>Point estimate:</strong> the model beats picking the home team on accuracy
({s2['winner_accuracy']:.1%} vs {s2['home_always_accuracy']:.1%}) and on Brier score
({s2['brier_skill_score']:+.3f} skill). <strong>But</strong> the paired McNemar test
(p = {s2['mcnemar_exact_p_two_sided']:.4f}) and the bootstrap interval on Brier skill
({s2['brier_skill_score_ci95_low']:+.3f} to {s2['brier_skill_score_ci95_high']:+.3f}) both fail
to exclude luck. With 61 games this is the expected outcome: the honest statement is
<em>preliminary signal, unproven</em>.</p>
<p><strong>What would change the verdict:</strong> a fixed pre-registered rule, several hundred
out-of-sample games, a market comparison after vig, and a multiple-testing correction across every
candidate tried. None of those exist today, which is exactly what the
<a href="validation.html">validation gates</a> record.</p>
</div>
<h2>Fitted team ratings (margin scale, final fit on 121 games)</h2>
<p>Positive is better. This is a description of who has outscored whom so far, shrunk toward the
league mean because each team has only played about four games. It is not a projection of the
rest of the season.</p>
{table(["Team", "Margin rating (pts)", "Total effect (pts)", "Input source"], rrows2)}
"""
    (OUT / "signals.html").write_text(page("signals.html", "Signal test", signals_body), encoding="utf-8")

    # ---------------------------------------------------------- correlations
    def crow(name: str, item: dict | None, meaning: str, source: str, status: str) -> str:
        if item is None:
            value = '<td class="empty" aria-label="blank, unverified"></td>'
            interval = '<td class="empty" aria-label="blank, unverified"></td>'
            n = '<td class="num">—</td>'
        else:
            value = f"<td class='num'>{item['r']:+.3f}</td>"
            interval = f"<td class='num'>{item['ci95_low']:+.3f} to {item['ci95_high']:+.3f}</td>"
            n = f"<td class='num'>{item['n']}</td>"
        return (f"<tr><td>{escape(name)}</td>{value}{interval}{n}<td>{meaning}</td>"
                f"<td>{pill(status)}</td><td>{link(source, 'NBA.com')}</td></tr>")

    corr_rows = [
        crow("Game margin vs game total (121 finals)", corr["margin_vs_total"],
             "Near zero and the interval spans zero: on this sample, scoring margin carries almost no "
             "information about the total. A parlay pricing that treats a side and a total as "
             "independent is not contradicted here — but 121 games is too few to certify independence.",
             NBA + "/games", "verified"),
        crow("Home points vs away points, same game", corr["home_points_vs_away_points"],
             "Positive and the interval excludes zero: both teams score in a shared pace environment. "
             "Any parlay combining two scoring overs is therefore <em>not</em> a product of two "
             "independent probabilities; the naive product understates the joint probability.",
             NBA + "/games", "verified"),
        crow("Team differential: first half vs second half of its games", corr["team_differential_first_half_vs_second_half"],
             "The luck-versus-skill probe: if results were pure noise this correlation would sit at "
             "zero. It is positive with an interval above zero, which is weak evidence that some team "
             "quality persists — but each half is only about two games per team, so the estimate is "
             "extremely unstable.",
             NBA + "/standings", "needs review"),
        crow("Player-prop correlations and prop-parlay legs", None,
             "No licensed player-level observation archive exists for this project, and NBA Terms "
             "§9(iv) bars use of NBA statistics in connection with gambling. The cells stay blank.",
             NBA + "/termsofuse", "unverified"),
        crow("Same-player stat correlation across two legs", None,
             "Requires per-player game logs with licensing; not available, so blank.",
             NBA + "/termsofuse", "unverified"),
    ]
    corr_body = f"""
<p class="eyebrow">Category · Correlation</p>
<h1>Measured dependence, and the cells we refuse to fill</h1>
<p>Correlation is what decides whether a parlay is priced correctly. Multiplying marginal
probabilities is only valid under independence; where the data show dependence, the joint
probability has to be modelled. The first three rows are measured from the 121 official final
scores in this repository. The prop rows are blank because no official, licensed player-level
source is available to this project.</p>
{table(["Quantity", "Pearson r", "95% interval", "n", "Interpretation", "Status", "Source"], corr_rows)}
<div class="note">
<p><strong>What a parlay builder should do with this.</strong> Two legs on the same game share a
pace factor (row 2), so a joint model is required; two legs on different games can be treated as
independent only after checking that no shared team or player appears in both, and even then the
independence assumption is a modelling choice, not a measured fact.</p>
<p><strong>Multiple testing.</strong> Three correlations are reported here; at a 5% level, roughly
one false positive is expected per twenty tests. Nothing on this page is corrected for multiplicity
because nothing here is being promoted as a signal — they are descriptions used to design the
joint model.</p>
</div>
"""
    (OUT / "correlations.html").write_text(page("correlations.html", "Correlation", corr_body), encoding="utf-8")

    # ------------------------------------------------------------ validation
    gates = [
        ("G1 Rights and licence", "fail",
         "NBA Terms §1 bars republication of Basketball Content without permission and §9(iv) bars use "
         "of NBA Statistics in connection with gambling; the NBA Stats FAQ states statistics are not "
         "available for download. No licence or written permission is held.",
         "https://www.nba.com/termsofuse"),
        ("G2 Sample adequacy", "fail",
         "121 games, about 4 per team, 61 out-of-sample. Far below the pre-registered minimum for a "
         "team-rating signal.",
         "https://www.nba.com/standings"),
        ("G3 Time-ordered out-of-sample test", "pass",
         "Expanding-window refit before each scored game; no future information used. Implemented in "
         "<code>scripts/daily_analysis.py</code>.",
         "https://www.nba.com/games"),
        ("G4 Proper scoring and calibration", "not met",
         f"Brier skill {walk['brier_skill_score']:+.3f} with bootstrap interval "
         f"[{walk['brier_skill_score_ci95_low']:+.3f}, {walk['brier_skill_score_ci95_high']:+.3f}]; "
         "interval includes zero.",
         "https://www.nba.com/games"),
        ("G5 Luck control", "not met",
         f"McNemar exact p = {walk['mcnemar_exact_p_two_sided']:.4f} against the always-home benchmark; "
         "not significant at 5%.",
         "https://www.nba.com/standings"),
        ("G6 Market benchmark after vig", "fail",
         "No official price source is configured, so no closing-line value, hold or ROI can be "
         "computed. Market cells are blank, not zero.",
         "https://www.nba.com/termsofuse"),
        ("G7 Joint-probability handling for parlays and props", "fail",
         "Game-level dependence is measured, but prop-level dependence is unavailable; parlay legs "
         "therefore cannot be priced defensibly.",
         "https://www.nba.com/termsofuse"),
        ("G8 Auditability and reproducibility", "pass",
         "Every published value is regenerated by committed, dependency-free scripts from committed "
         "CSVs; the site checker re-verifies row counts, source links and blank-cell rules.",
         "https://www.nba.com/standings"),
    ]
    grows = []
    for name, status, reason, source in gates:
        grows.append(f"<tr><td>{escape(name)}</td><td>{pill(status)}</td><td>{escape(reason)}</td>"
                     f"<td>{link(source)}</td></tr>")
    validation_body = f"""
<p class="eyebrow">Category · Validation gates</p>
<h1>Eight gates, and a leaderboard that stays empty</h1>
<p>Every candidate strategy has to clear the same gates before it can earn a leaderboard slot or a
reward. A gate is only marked pass when the repository can show the evidence; the rights and market
gates fail today for structural reasons, which is what keeps the leaderboard at zero qualified
entries.</p>
{table(["Gate", "Status", "Reason", "Source"], grows)}
<h2>Leaderboard</h2>
{table(["Rank", "Candidate", "Eligible", "Reward", "Reason", "Source"],
       ['<tr><td class="num">—</td><td>team-rating margin/total model (S1)</td>'
        '<td>No</td><td>—</td>'
        f'<td>Fails G1, G2, G4, G5, G6, G7. Point estimate is encouraging; evidence is not.</td>'
        f'<td>{link(NBA + "/games", "NBA.com")}</td></tr>',
        '<tr><td class="num">—</td><td>home-team baseline</td><td>No</td><td>—</td>'
        '<td>Control, not a candidate: it exists to be beaten, and it is not eligible for reward.</td>'
        f'<td>{link(NBA + "/standings", "NBA.com")}</td></tr>',
        '<tr><td class="num">—</td><td>prop / parlay combination candidates</td><td>No</td><td>—</td>'
        '<td>No licensed player-level data; G7 cannot be satisfied, so nothing can be scored.</td>'
        f'<td>{link(NBA + "/termsofuse", "NBA.com")}</td></tr>'])}
<div class="note"><p><strong>Reward design.</strong> Rewards are research priority and publication
space, not money. Eligibility requires all eight gates; a candidate that fails any gate stays off
the leaderboard no matter how good its point estimate looks. This is the mechanism that keeps
sample-size luck from being rewarded.</p></div>
"""
    (OUT / "validation.html").write_text(page("validation.html", "Validation gates", validation_body), encoding="utf-8")

    # --------------------------------------------------------------- sources
    src = [
        ("NBA.com standings", "https://www.nba.com/standings",
         "30 team records, seeds, win%, games behind, for 2026-27.", "Read 2026-11-05, both conference tables."),
        ("NBA.com games — 4 November scoreboard", "https://www.nba.com/games?date=2026-11-04",
         "14 final scores, overtime flags, game IDs.", "Read 2026-11-05, three page chunks."),
        ("NBA.com game page — ORL @ PHX", "https://www.nba.com/game/orl-vs-phx-0022600187",
         "5–6 November tip times, game IDs, NBA Cup group labels, current records.", "Read 2026-11-05."),
        ("NBA.com game page — MIA @ GSW", "https://www.nba.com/game/mia-vs-gsw-0022600188",
         "Second game of tonight's slate.", "Linked from the same schedule listing."),
        ("NBA Terms of Use", "https://www.nba.com/termsofuse",
         "§1 ownership/use restrictions; §9 (i)–(vii) NBA Statistics conditions, including §9(iv) "
         "no use in connection with any gambling activity.",
         "Read 2026-11-05, chunks 0, 3 and 4."),
        ("NBA Stats FAQ", "https://www.nba.com/stats/help/faq",
         "Statistics are not available for download for either academic or personal use.",
         "Read 2026-11-05, chunk 0."),
    ]
    srows3 = []
    for name, url, supports, method in src:
        srows3.append(f"<tr><td>{escape(name)}</td><td>{link(url)}</td><td>{escape(supports)}</td>"
                      f"<td>{escape(method)}</td><td>{pill('verified')}</td></tr>")
    sources_body = f"""
<p class="eyebrow">Category · Sources</p>
<h1>Official pages read for this snapshot</h1>
<p>Only NBA.com and NBA Official pages were used for facts. Each row records what the page was used
for, so a reviewer can open the same page and check the same cells.</p>
{table(["Source", "Link", "Supports", "Retrieval", "Status"], srows3)}
<h2>What these sources do <em>not</em> support</h2>
<p>NBA.com publishes no betting prices, no model performance statistics and no profitability
evidence. Nothing on this site is confirmed by an official source other than the factual cells
listed above; every derived number is labelled as a project computation with its method and
interval.</p>
"""
    (OUT / "sources.html").write_text(page("sources.html", "Sources", sources_body), encoding="utf-8")

    # --------------------------------------------------------------- flagged
    flags = [
        ("F01", "High", "Rights: gambling-related reuse of NBA data is not permitted by the terms",
         "NBA Terms §9(iv): 'the NBA Statistics may not be used in connection with any gambling "
         "activity (including legal gambling activity)'; §9(ii) limits use to legitimate news "
         "reporting or private non-commercial purposes; §1 bars republication without written "
         "permission. This project is a private research record, publishes no prices and no picks, "
         "and attributes NBA.com. A qualified reviewer should confirm before any public or "
         "commercial reuse.", "https://www.nba.com/termsofuse"),
        ("F02", "High", "No official price source, so every market cell is blank",
         "No sportsbook or exchange feed is configured; NBA.com does not publish prices. Primary "
         "market spread, total and price columns are therefore empty on the forward slate, and no "
         "closing-line value, hold percentage or ROI can be computed.", "https://www.nba.com/termsofuse"),
        ("F03", "High", "Player-prop and parlay-leg correlations cannot be measured",
         "No licensed player-level archive; §9(iv) bars gambling use of NBA statistics. Cells are "
         "blank rather than estimated, which is why no prop or combination strategy is scored.",
         "https://www.nba.com/stats/help/faq"),
        ("F04", "Medium", "The page labelled 'live' was already stale when re-read",
         "The 3 November snapshot is a dated record, not a live feed: today's official page shows "
         "Philadelphia 8-1 rather than 7-1, Detroit 6-2 rather than 6-1, and twelve other changes. "
         "The new snapshot is published as dated, and the existing files were not overwritten.",
         "https://www.nba.com/standings"),
        ("F05", "Medium", "Model inputs are only about four games per team",
         "The 121-game archive is internally consistent but small; the 80% bands on the forward slate "
         "are wide and the walk-forward interval includes zero. No strategy is promoted on this "
         "sample.", "https://www.nba.com/games"),
        ("F06", "Medium", "Older score rows were not re-read one by one in this session",
         "The 107-game archive used for training was validated by reconciling all 30 team records to "
         "two official standings snapshots, which catches mis-typed scores but is not the same as "
         "re-reading 107 game cards. Per-row links exist in the source CSVs.",
         "https://www.nba.com/standings"),
        ("F07", "Low", "NBA Cup games use a different game-ID series",
         "The 6 November Cup games carry IDs 0022600025–0022600033 while regular-season games use "
         "00226001xx. Both forms are taken verbatim from official NBA.com pages; the difference is "
         "expected, not a typo, and is recorded so it is not 'fixed' by a later session.",
         "https://www.nba.com/game/orl-vs-phx-0022600187"),
        ("F08", "Low", "Inherited pages describe different evidence standards",
         "Earlier project sections (original framework, prototype, lab, verified archive) were built "
         "by other sessions with their own conventions. This snapshot does not rewrite them; a later "
         "integration session should reconcile the wording, and readers should treat each section's "
         "own disclosures as authoritative for that section.",
         "https://www.nba.com/termsofuse"),
        ("F09", "Low", "Statements by NBA about restricted bet types are press-reported only",
         "The official NBA release on its prediction-market integrity framework of 26 October 2026 "
         "refers to 'the NBA's latest sports betting restrictions' but does not enumerate them. No "
         "specific restricted market is reproduced here.",
         "https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets"),
    ]
    frow_html = []
    for fid, severity, title, detail, source in flags:
        frow_html.append(
            f"<tr><td><code>{escape(fid)}</code></td><td>{pill('unverified') if severity == 'High' else pill('needs review')}</td>"
            f"<td><strong>{escape(severity)}</strong></td><td>{escape(title)}</td>"
            f"<td>{escape(detail)}</td><td>{link(source)}</td></tr>"
        )
    flagged_body = f"""
<p class="eyebrow">Category · Flagged for Review</p>
<h1>Flagged for Review</h1>
<p>Everything that could not be confirmed from an official source, and every irregularity found
while reading. Flagged items do not block publication of the rest of the snapshot; they mark the
cells a reviewer should look at first.</p>
{table(["ID", "Blocking", "Severity", "Item", "Detail", "Source"], frow_html)}
<div class="note"><p><strong>Rule applied.</strong> If a value could not be read from an official
page, it is blank here and on the page where it would have appeared. No cell was filled by
inference, interpolation or a secondary report.</p></div>
"""
    (OUT / "flagged.html").write_text(page("flagged.html", "Flagged for Review", flagged_body), encoding="utf-8")

    pages = sorted(p.as_posix() for p in OUT.rglob("*.html"))
    print(f"Built {len(pages)} pages: " + ", ".join(pages))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
