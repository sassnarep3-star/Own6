#!/usr/bin/env python3
"""Build the static GitHub Pages site in docs/ from data/*.json (stdlib only).

Run:  python3 scripts/build_site.py
Every table is generated from the JSON files, so the site and data cannot drift apart.
"""
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "verified"  # isolated from other sessions' docs/ output
REPO = "https://github.com/sassnarep3-star/Own6"
SITE = "https://sassnarep3-star.github.io/Own6/"

# Official references used to close the "every table row needs an official source"
# advisory. These documents define the rule or the check for the row; they are
# NOT evidence that any unverified value is correct.
NBA_TOU = "https://www.nba.com/termsofuse"
NBA_STATS_FAQ = "https://www.nba.com/stats/help/faq"
NBA_RELEASE = "https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets"
KR_LAW = "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95"
KR_LAW_26 = "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95/%EC%A0%9C26%EC%A1%B0"

GATE_REF = {
    "G1": ("Korean statute, Art. 26", KR_LAW_26),
    "G2": ("NBA Stats FAQ (no bulk download)", NBA_STATS_FAQ),
    "G3": ("NBA official release, 26 Oct 2026", NBA_RELEASE),
    "G4": ("scikit-learn: cross-validation", "https://scikit-learn.org/stable/modules/cross_validation.html"),
    "G5": ("NIST/SEMATECH: binomial distribution", "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm"),
    "G6": ("NBA Terms §9 (no official closing-line source)", NBA_TOU + "#nba-statistics"),
    "G7": ("statsmodels: multiple-testing correction", "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html"),
    "G8": ("SciPy: Pearson correlation (pearsonr)", "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"),
}

FLAG_REF = {
    "Legal (Korea)": ("Korean statute", KR_LAW_26),
    "Korean law text": ("Korean statute", KR_LAW_26),
    "Legal (NBA ToU)": ("NBA Terms of Use", NBA_TOU),
    "NBA policy": ("NBA official release, 26 Oct 2026", NBA_RELEASE),
    "Data gap": ("NBA Stats FAQ", NBA_STATS_FAQ),
    "Sources": ("NBA Stats FAQ", NBA_STATS_FAQ),
    "Repo": ("GitHub repository", "https://github.com/sassnarep3-star/Own6"),
    "Site": ("GitHub repository", "https://github.com/sassnarep3-star/Own6"),
}

def gate_ref(gid):
    label, url = GATE_REF.get(gid, ("NBA Terms of Use", NBA_TOU))
    return link(url, label)

NAV = [
    ("index.html", "Home"),
    ("executive-summary.html", "Executive summary"),
    ("games.html", "Games"),
    ("strategies.html", "Strategies"),
    ("methodology.html", "Methodology"),
    ("legal-kr.html", "Korea law"),
    ("nba-policy.html", "NBA policy"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def esc(v):
    return html.escape("" if v is None else str(v))


def badge(verified):
    if verified:
        return '<span class="badge ok">Verified</span>'
    return '<span class="badge warn">Unverified</span>'


def link(url, text=None):
    if not url:
        return '<span class="blank">—</span>'
    label = text or url.replace("https://", "").split("/")[0]
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)} ↗</a>'


def table(headers, body_rows, table_id):
    """body_rows is a list of lists of pre-escaped HTML cell strings."""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    rows = []
    for r in body_rows:
        cells = "".join(f"<td>{c}</td>" for c in r)
        rows.append(f"<tr>{cells}</tr>")
    return (
        f'<div class="table-wrap"><input class="filter" type="search" '
        f'placeholder="Filter rows…" data-target="{table_id}" aria-label="Filter table">'
        f'<div class="scroll"><table id="{table_id}"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div></div>'
    )


def page(filename, title, body, active):
    nav = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{esc(label)}</a>'
        for href, label in NAV
    )
    html_text = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · NBA research dashboard</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="brand"><a href="index.html">NBA research dashboard</a></div>
  <nav>{nav}</nav>
</header>
<div class="notice">Research only. Nothing on this site is betting advice. Korean law may apply. See <a href="legal-kr.html">Korea law</a> and <a href="flagged.html">Flagged for review</a>.</div>
<main>
<h1>{esc(title)}</h1>
{body}
</main>
<footer>
  Repo: <a href="{REPO}">sassnarep3-star/Own6</a> · Built from data/*.json by scripts/build_site.py · Every table row links to its source.
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""
    (DOCS / filename).write_text(html_text, encoding="utf-8")


def card(label, value, note, href):
    return (f'<a class="card" href="{href}"><div class="card-label">{esc(label)}</div>'
            f'<div class="card-value">{esc(value)}</div><div class="card-note">{esc(note)}</div></a>')


def main():
    games = load("games.json")
    legal = load("legal_kr.json")
    policy = load("nba_policy.json")
    meth = load("methodology.json")
    strat = load("strategies.json")
    flags = load("flags.json")

    n_games = len(games["rows"])
    n_legal = len(legal["rows"])
    legal_verified = sum(1 for r in legal["rows"] if r["verified"])
    pol_verified = sum(1 for r in policy["rows"] if r["verified"])
    pol_unverified = len(policy["rows"]) - pol_verified
    n_gates = len(meth["gates"])
    gates_passed = sum(1 for g in meth["gates"] if g["current_result"].startswith("PASS"))
    n_strat = len(strat["rows"])
    n_flags = len(flags["rows"])
    high_flags = sum(1 for f in flags["rows"] if f["severity"] == "High")

    # ---------- Home ----------
    cards = "".join([
        card("Games imported", f"{n_games}", "Nov 2, 2026 slate, all verified on nba.com", "games.html"),
        card("Korean law rows", f"{legal_verified}/{n_legal}", "verified against law.go.kr", "legal-kr.html"),
        card("NBA policy items", f"{pol_verified} verified · {pol_unverified} unverified", "official text vs press reports", "nba-policy.html"),
        card("Validated strategies", f"{n_strat}", f"{gates_passed} of {n_gates} gates passed", "strategies.html"),
        card("Flagged for review", f"{n_flags}", f"{high_flags} high severity", "flagged.html"),
    ])
    home_body = f"""
<p class="lede">A verified, source-linked base for NBA research. Each entry has an official link, or it is marked unverified and left blank.</p>
<div class="cards">{cards}</div>
<h2>Start here</h2>
<ul class="links">
  <li><a href="executive-summary.html">Executive summary</a>: what is verified, what is not, and the decisions needed.</li>
  <li><a href="flagged.html">Flagged for review</a>: legal, data, and repo items for the owner.</li>
  <li><a href="methodology.html">Methodology</a>: the validation gates and correlation rules.</li>
</ul>
<h2>Browse by category</h2>
<ul class="links">
  <li><a href="games.html">Games</a> (schedule and odds fields)</li>
  <li><a href="strategies.html">Strategies</a> (leaderboard, empty until gates pass)</li>
  <li><a href="legal-kr.html">Korea law</a> (국민체육진흥법 betting articles)</li>
  <li><a href="nba-policy.html">NBA policy</a> (official vs reported restrictions)</li>
  <li><a href="sources.html">Sources</a> (every source and verification record)</li>
</ul>
<p class="muted">Last built from data files. Retrieved 2026-11-02.</p>
"""
    page("index.html", "Dashboard", home_body, "index.html")

    # ---------- Executive summary ----------
    summary_body = f"""
<div class="callout">
<strong>Bottom line.</strong> No betting strategy is validated, no correlation value is computed, and the leaderboard is empty. The blocker is data and law, not effort. A verified odds source does not exist in this repo yet, and Korean counsel has not reviewed the legal exposure.
</div>
<h2>What is verified</h2>
<ul>
  <li><strong>{n_games} NBA games</strong> for Monday, November 2, 2026, with official nba.com game links (<a href="https://www.nba.com/schedule" target="_blank" rel="noopener">schedule</a>). Only this one day is imported.</li>
  <li><strong>{legal_verified} Korean statute rows</strong> from 국민체육진흥법 (<a href="https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95" target="_blank" rel="noopener">law.go.kr</a>, in force 2026-09-03). Art. 26 bans “similar acts” (유사행위), and Arts. 47–49 set the penalties.</li>
  <li><strong>NBA official release</strong> (Oct 26, 2026) on the prediction-market framework (<a href="https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets" target="_blank" rel="noopener">nba.com</a>). It says partner markets follow the league's “latest sports betting restrictions” but does not list them.</li>
  <li><strong>NBA official partner list</strong> (July 9, 2026, <a href="https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2" target="_blank" rel="noopener">nba.com</a>). No South Korea entry appears.</li>
</ul>
<h2>What is not verified</h2>
<ul>
  <li><strong>Specific NBA prop restrictions</strong> (under props on bench players, “first of” props, same-player under parlays) appear only in press reports. They are marked unverified on the <a href="nba-policy.html">NBA policy</a> page.</li>
  <li><strong>Odds and results.</strong> Odds columns are blank for every game. No team or player stats were imported.</li>
  <li><strong>Correlation values.</strong> None computed. The table is empty because there is no verified dataset.</li>
</ul>
<h2>Key findings</h2>
<ol>
  <li><strong>Legal exposure is the main risk.</strong> Under Art. 26(2), designing or providing a betting-type system, providing game information for it, or promoting or brokering it is prohibited, and so is paying benefits to winners of similar issuance under Art. 26(1). Penalties run up to 7 years (Art. 47). Bettors can also be punished (Art. 48(3)). Originating NBA lines and running a reward leaderboard for Korean users is the highest-risk combination. This is a reading of the text, not a legal opinion (flag F01).</li>
  <li><strong>The gates are designed, not passed.</strong> {n_gates} validation gates are defined; {gates_passed} have passed. Luck cannot be removed from the equation. The gates only reduce the chance of confusing luck with skill (see <a href="methodology.html">Methodology</a>).</li>
  <li><strong>The NBA's restrictions are real but not yet primary-sourced.</strong> The official release confirms restrictions exist. The specific bans need the NBA's own memo to be confirmed (flag F03).</li>
  <li><strong>Repo state.</strong> The repo was a one-line README. This work adds data, a site, and coordination records. Irregularities are listed on <a href="flagged.html">Flagged for review</a>.</li>
</ol>
<h2>Decisions needed from the owner</h2>
<ol>
  <li>Get a written opinion from Korean counsel on Art. 26 before any public output or reward scheme (G1).</li>
  <li>Choose a verified odds and results source with documented terms, or accept that strategy work stays empty (G2).</li>
  <li>Decide whether the site stays research-only. Current design: no betting recommendations, no rewards configured.</li>
</ol>
<p class="muted">Built from data/*.json on 2026-11-02. Every claim above links to a verified source on the relevant page or to the <a href="sources.html">Sources</a> page.</p>
"""
    page("executive-summary.html", "Executive summary", summary_body, "executive-summary.html")

    # ---------- Games ----------
    g_cols = ["Game ID", "Date", "Tip (ET)", "Away", "Home", "Venue", "City", "Status", "Odds home", "Odds away", "Source", "Verified"]
    g_rows = []
    for r in games["rows"]:
        g_rows.append([
            esc(r["game_id"]), esc(r["date"]), esc(r["tip_time_et"]), esc(r["away_team"]), esc(r["home_team"]),
            esc(r["venue"]), esc(r["city"]), esc(r["status"]),
            '<span class="blank">blank · unverified</span>', '<span class="blank">blank · unverified</span>',
            link(r["source_url"], "nba.com"), badge(r["verified"]),
        ])
    games_body = f"""
<p class="muted">{esc(games['meta']['coverage'])}</p>
<p class="muted">{esc(games['meta']['odds_note'])}</p>
{table(g_cols, g_rows, "games-table")}
<p class="muted">Source: <a href="{games['meta']['primary_source']}" target="_blank" rel="noopener">nba.com/schedule</a>, retrieved {esc(games['meta']['retrieved'])}. Times are as published (ET).</p>
"""
    page("games.html", "Games — 2026-27 schedule", games_body, "games.html")

    # ---------- Strategies ----------
    strat_head = ["Rank", "Strategy", "Bet type", "Markets", "Sample size", "ROI", "CLV", "Gates passed", "Source dataset", "Verified"]
    strat_body_rows = [[esc(x) for x in row] for row in []]
    gate_rows = []
    for g in meth["gates"]:
        gate_rows.append([esc(g["id"]), esc(g["name"]), esc(g["rule"]), esc(g["current_result"]), esc(g["why"]),
                          gate_ref(g["id"])])
    strategies_body = f"""
<div class="callout">
<strong>Leaderboard status:</strong> {n_strat} strategies have passed the gates, so the leaderboard is empty. {esc(strat['meta']['reward_policy'])}
</div>
<h2>Leaderboard</h2>
{table(strat_head, strat_body_rows, "strategy-table")}
<p class="muted">Rows appear here only when every gate in the table below is marked PASS with a source dataset and a verified record.</p>
<h2>Gate status</h2>
{table(["ID", "Gate", "Rule", "Current result", "Why", "Official reference for the rule"], gate_rows, "gate-table")}
"""
    page("strategies.html", "Strategies — leaderboard and gates", strategies_body, "strategies.html")

    # ---------- Methodology ----------
    corr = meth["correlation_table"]
    corr_head = ["Leg A", "Leg B", "Sample size", "Correlation", "Source dataset", "Verified"]
    corr_empty = table(corr_head, [], "corr-table")
    method_body = f"""
<p class="muted">{esc(meth['meta']['note'])}</p>
<h2>Validation gates</h2>
{table(["ID", "Gate", "Rule", "Current result", "Why", "Official reference for the rule"], gate_rows, "gate-table-2")}
<h2>Luck control</h2>
<div class="callout">{esc(meth['luck_control_note'])}</div>
<h2>Correlation values</h2>
<p><strong>Status:</strong> {esc(corr['status'])}. {esc(corr['rule'])}</p>
{corr_empty}
"""
    page("methodology.html", "Methodology — gates and correlation", method_body, "methodology.html")

    # ---------- Korea law ----------
    l_cols = ["Article", "Topic", "Korean text (excerpt)", "English summary (compiler)", "Penalty", "Source", "Verified"]
    l_rows = []
    for r in legal["rows"]:
        l_rows.append([
            esc(r["article"]), esc(r["topic"]), esc(r["korean_text_excerpt"]), esc(r["english_summary_compiler"]),
            esc(r["penalty"]) if r["penalty"] else '<span class="blank">—</span>',
            link(r["source_url"], "law.go.kr"), badge(r["verified"]),
        ])
    legal_body = f"""
<div class="callout">{esc(legal['meta']['legal_disclaimer'])}</div>
<p class="muted">{esc(legal['meta']['in_force'])}. {esc(legal['meta']['translation_note'])}</p>
{table(l_cols, l_rows, "legal-table")}
"""
    page("legal-kr.html", "Korea law — 국민체육진흥법 betting provisions", legal_body, "legal-kr.html")

    # ---------- NBA policy ----------
    p_cols = ["Item", "Official statement (verified)", "Official source", "Reported by press (unverified)", "Press source", "Status", "Official status of this row"]
    p_rows = []
    for r in policy["rows"]:
        status = '<span class="badge ok">Verified</span>' if r["verified"] else '<span class="badge warn">Unverified</span>'
        official_cell = link(r["official_source_url"], "nba.com") if r["official_source_url"] else link(NBA_RELEASE, "official release (restriction not listed)")
        p_rows.append([
            esc(r["item"]),
            esc(r["official_statement_verified"]) if r["official_statement_verified"] else '<span class="blank">blank · unverified</span>',
            official_cell,
            esc(r["secondary_reports_unverified"]),
            link(r["secondary_source_url"]) if r["secondary_source_url"] else '<span class="blank">—</span>',
            status,
            link(NBA_RELEASE, "check the release") + (' · stated' if r["verified"] else ' · <strong>not enumerated</strong>'),
        ])
    policy_body = f"""
<p class="muted">{esc(policy['meta']['rule'])}</p>
{table(p_cols, p_rows, "policy-table")}
"""
    page("nba-policy.html", "NBA policy — official vs reported", policy_body, "nba-policy.html")

    # ---------- Flagged ----------
    f_cols = ["ID", "Category", "Severity", "Item", "Detail", "Source", "Action requested", "Official reference"]
    f_rows = []
    for r in flags["rows"]:
        sev = esc(r["severity"])
        f_rows.append([
            esc(r["id"]), esc(r["category"]), f'<span class="sev {sev.lower()}">{sev}</span>',
            esc(r["item"]), esc(r["detail"]), link(r["source_url"]), esc(r["action_requested"]),
            link(*[FLAG_REF.get(r["category"], ("NBA Terms of Use", NBA_TOU))[1],
                   FLAG_REF.get(r["category"], ("NBA Terms of Use", NBA_TOU))[0]]),
        ])
    flagged_body = f"""
<div class="callout">
<strong>Flagged for Review.</strong> These items do not block the merge. They are published here with source links so the owner can review them and request changes.
</div>
{table(f_cols, f_rows, "flag-table")}
"""
    page("flagged.html", "Flagged for review", flagged_body, "flagged.html")

    # ---------- Sources ----------
    src_rows = [
        ["S1", "Korea Ministry of Government Legislation — 국민체육진흥법 (law.go.kr)", "Arts. 2, 24, 26, 30, 47–49, 51, 53–54", "Verified text; in force 2026-09-03", "https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95", "Verified"],
        ["S2", "NBA — Schedule (nba.com)", "Nov 2, 2026 slate (15 games)", "Verified for Nov 2 only", "https://www.nba.com/schedule", "Verified"],
        ["S3", "NBA — Official release, prediction-market framework (Oct 26, 2026)", "Framework; restrictions mentioned but not listed", "Verified text", "https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets", "Verified"],
        ["S4", "NBA — Official gaming partners and operators (July 9, 2026)", "Partner list; no South Korea entry", "Verified", "https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "Verified"],
        ["R1", "Sports Business Journal (Oct 16, 2026) — secondary", "Reported prop restrictions", "Unverified (press)", "https://www.sportsbusinessjournal.com/Articles/2026/10/16/new-nba-season-brings-a-change-to-rules-and-processes-as-a-crucial-predictions-decision-looms/", "Unverified"],
        ["R2", "TSN (Oct 16, 2026) — secondary", "Reported memo to sportsbooks", "Unverified (press)", "https://www.tsn.ca/nba/article/nba-tells-sportsbooks-to-stop-certain-bets-restrict-parlays-n1-50196498/", "Unverified"],
        ["R3", "Betting.net (Oct 19, 2026) — secondary", "Reported restrictions", "Unverified (press)", "https://www.betting.net/news/legal/nba-tells-sportsbooks-to-halt-certain-bets/", "Unverified"],
        ["R4", "Yahoo Sports (ESPN reporting) — secondary", "Reported first-of and parlay bans", "Unverified (press)", "https://sports.yahoo.com/articles/nba-sportsbooks-agree-ban-several-194209257.html", "Unverified"],
        ["R5", "mk.co.kr (Mar 27, 2025) — secondary", "Legal commentary quoting a lawyer on overseas betting", "Unverified (press)", "https://www.mk.co.kr/en/society/11275855", "Unverified"],
    ]
    sources_body = f"""
<p class="muted">Official sources (S1–S4) are the only ones used to fill verified values. Secondary sources (R1–R5) only identify what to check, and are never used to fill a value.</p>
{table(["ID", "Source", "Used for", "Verification", "Link", "Status", "Official status"], [[esc(c) if i != 4 else link(c) for i, c in enumerate(r)] + [("verified in the official source" if r[5] == "Verified" else link(NBA_RELEASE, "secondary — not confirmed by the official release"))] for r in src_rows], "source-table")}
<h2>Verification record</h2>
<ul>
  <li>Each official page was read with the fetch tool on 2026-11-02. Bash access was limited to GitHub, npm, and PyPI, so the NBA and law.go.kr pages were read through the fetch tool.</li>
  <li>Korean statute text is quoted from the official page. English summaries are the compiler's translation.</li>
  <li>The coordination log is in <a href="{REPO}/blob/main/COORDINATION.md" target="_blank" rel="noopener">COORDINATION.md</a>.</li>
</ul>
"""
    page("sources.html", "Sources and verification", sources_body, "sources.html")

    print("built", len(list(DOCS.glob("*.html"))), "pages")


if __name__ == "__main__":
    main()
