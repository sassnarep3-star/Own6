#!/usr/bin/env python3
"""Build the independent verification section of the Own6 GitHub Pages site.

Outputs (all deterministic, no timestamps):
    docs/review/index.html
    docs/review/summary.html
    docs/review/verification.html
    docs/review/repo-review.html
    docs/review/flagged.html
    docs/review/assets/style.css
    docs/review/assets/app.js

Every data table row is validated at build time: it must contain at least one
link to an official URL present in data/verification_log.csv with a
verified-direct* status (or to this project's own official GitHub repository,
which is the primary source for repository facts). A build that violates the
rule fails instead of publishing an unlinked row.

Usage:  python3 tools/build_review.py           # write files
        python3 tools/build_review.py --check   # fail if files are out of date
"""
from __future__ import annotations

import csv
import html
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from check_site import is_official, load_verified  # noqa: E402

OUT = ROOT / "docs" / "review"
ASSETS = OUT / "assets"
VERIFIED = load_verified()

NAV = [
    ("index.html", "Overview"),
    ("summary.html", "Executive summary"),
    ("verification.html", "Verification log"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "⚑ Flagged for review"),
    ("../index.html", "Main dashboard"),
    ("../verified/", "Verified data"),
]


def A(url: str, label: str, title: str | None = None) -> str:
    t = f' title="{html.escape(title, quote=True)}"' if title else ""
    return f'<a href="{url}" target="_blank" rel="noopener"{t}>{label}</a>'


def I(href: str, label: str) -> str:
    return f'<a href="{href}">{label}</a>'


def GH(path: str, label: str | None = None) -> str:
    return A(f"https://github.com/sassnarep3-star/Own6/blob/main/{path}", label or path)


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def validate_rows(rows: list[list[str]], context: str) -> None:
    for i, row in enumerate(rows, 1):
        urls = [html.unescape(u) for u in __import__("re").findall(r'href="(https?://[^"]+)"', " ".join(row))]
        if not any(is_official(u, VERIFIED) for u in urls):
            raise ValueError(f"{context}: row {i} has no directly verified official source link")


def table(caption: str, headers: list[str], rows: list[list[str]], tid: str) -> str:
    validate_rows(rows, f"table '{caption}'")
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return (
        f'<section class="card"><h2>{esc(caption)}</h2>'
        f'<input class="filter" type="search" placeholder="Filter rows…" data-target="{tid}" aria-label="Filter {esc(caption)}">'
        f'<div class="scroll"><table id="{tid}"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
        f'<p class="mut small">Every row links a directly retrieved official source. Click column headings to sort.</p></section>'
    )


def card(title: str, body: str) -> str:
    return f'<section class="card"><h3>{esc(title)}</h3><p>{body}</p></section>'


def page(title: str, h1: str, lede: str, body: str, active: str) -> str:
    nav = "".join(
        f'<a href="{href}"{" class=active" if href == active else ""}>{label}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Own6 independent review</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body><header class="top"><span class="brand">OWN6 · INDEPENDENT REVIEW</span><nav>{nav}</nav></header>
<main><h1>{html.escape(h1)}</h1><p class="lede">{lede}</p>
{body}
</main><footer>Independent verification pass · session <code>arena/a6ccf588-own6</code> · 2026-11-02 · final integration re-reads through 2026-11-05 · Research only, not betting advice · Unverified values are blank and flagged.</footer>
<script src="assets/app.js"></script></body></html>
"""


CSS = """:root{--bg:#f5f7fb;--card:#fff;--ink:#172033;--mut:#5c6a85;--acc:#1f6feb;--line:#dce3ef;--ok:#0a7d4b;--bad:#b42318;--warn:#915b00}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.55}
.top{display:flex;gap:18px;align-items:center;flex-wrap:wrap;padding:14px 24px;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.brand{font-weight:800;color:var(--acc);letter-spacing:.04em}.top nav{display:flex;gap:14px;flex-wrap:wrap}.top nav a{color:var(--mut);text-decoration:none;font-weight:600;font-size:14px}.top nav a:hover,.top nav a.active{color:var(--acc)}
main{max-width:1120px;margin:0 auto;padding:28px 20px 70px}h1{font-size:30px;margin:.1em 0 .3em}h2{font-size:19px;margin:0 0 12px}
.lede{color:var(--mut);max-width:860px;margin-bottom:22px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin:14px 0;box-shadow:0 1px 2px rgba(16,24,40,.04)}
.card h3{margin:0 0 8px;font-size:16px}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{background:#f0f4fb;color:#24324b;cursor:pointer;white-space:nowrap}tbody tr:hover{background:#f7faff}a{color:var(--acc)}code{background:#eef2fa;padding:1px 5px;border-radius:4px}
.filter{width:100%;max-width:340px;margin:0 0 12px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff}
.mut{color:var(--mut)}.small{font-size:12px;margin-top:10px}.ok{color:var(--ok);font-weight:700}.flag{color:var(--bad);font-weight:700}.warn{color:var(--warn);font-weight:700}.blank{color:var(--mut);font-style:italic}
footer{text-align:center;color:var(--mut);font-size:13px;padding:24px;border-top:1px solid var(--line)}
@media(max-width:640px){.top{padding:12px}.top nav{gap:10px}main{padding:20px 12px 50px}}
"""

JS = """/* Own6 independent review — progressive enhancement only, no external deps. */
(function () {
  'use strict';
  document.querySelectorAll('a[target="_blank"]').forEach(function (a) {
    if (!a.getAttribute('rel')) a.setAttribute('rel', 'noopener');
  });
  document.querySelectorAll('input.filter').forEach(function (input) {
    var table = document.getElementById(input.getAttribute('data-target'));
    if (!table) return;
    var body = table.tBodies[0];
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      Array.prototype.forEach.call(body.rows, function (row) {
        row.style.display = row.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
      });
    });
  });
  document.querySelectorAll('table thead th').forEach(function (th, index) {
    th.addEventListener('click', function () {
      var table = th.closest('table'), body = table.tBodies[0];
      var rows = Array.prototype.slice.call(body.rows);
      var asc = th.dataset.asc !== '1';
      th.dataset.asc = asc ? '1' : '0';
      rows.sort(function (a, b) {
        var x = (a.cells[index] || {}).textContent || '';
        var y = (b.cells[index] || {}).textContent || '';
        var nx = parseFloat(x.replace(/[^0-9.\\-]/g, '')), ny = parseFloat(y.replace(/[^0-9.\\-]/g, ''));
        if (!isNaN(nx) && !isNaN(ny)) return asc ? nx - ny : ny - nx;
        return asc ? x.localeCompare(y) : y.localeCompare(x);
      });
      rows.forEach(function (r) { body.appendChild(r); });
    });
  });
}());
"""


def build() -> dict[str, str]:
    files: dict[str, str] = {}

    # ---------------- Overview ----------------
    verified_entry_rows = [
        ["NBA Stats Glossary", "PACE, OffRtg, DefRtg, USG% definitions used by the own-line model", A("https://www.nba.com/stats/help/glossary", "Official glossary"), "V02 · verified direct"],
        ["NBA Stats FAQ", "Coverage history, update timing, no CSV download", A("https://www.nba.com/stats/help/faq", "Official FAQ"), "V03 · verified direct"],
        ["NBA Stats overview", "Live official player/team leaders (11/01/2026)", A("https://www.nba.com/stats/overview", "Official stats hub"), "V01 · verified direct"],
        ["NBA Official injury report", "Availability inputs and reporting deadlines", A("https://official.nba.com/nba-injury-report-2026-27-season/", "Official injury report"), "V05 · verified direct"],
        ["NBA NBABet partner list", "Official gaming partners/operators, dated July 9 2026", A("https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "Official list"), "V21 · verified direct"],
        ["NBA prediction-market framework", "Integrity framework, Oct 26 2026; specifics not enumerated", A("https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets", "Official release"), "V22 · verified direct"],
        ["NBA schedule", "Week 3 / Monday Nov 2 2026 slate (15 games)", A("https://www.nba.com/schedule", "Official schedule"), "V23 · verified direct"],
        ["GitHub REST API", "Repository state, Pages config and build status", A("https://api.github.com/repos/sassnarep3-star/Own6", "Official API"), "V18–V20 · verified direct"],
    ]
    blank_rows = [
        ["Current team PACE / OffRtg / DefRtg", '<span class="blank">blank</span>', '<span class="flag">unverified</span>', "No official bulk download; viewer-supplied export required", A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ (source to check)")],
        ["All correlation coefficients ρ", '<span class="blank">blank</span>', '<span class="flag">unverified</span>', "Requires paired residual history from official box scores", A("https://www.nba.com/stats/overview", "NBA Stats (source to check)")],
        ["Fitted home-court advantage / margin SD", '<span class="blank">blank</span>', '<span class="flag">unverified</span>', "Requires an official-data game log with n disclosed", A("https://www.nba.com/stats/overview", "NBA Stats (source to check)")],
        ["Live / closing odds and vig", '<span class="blank">blank</span>', '<span class="flag">unverified</span>', "Book-specific and time-specific; timestamped capture required", A("https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "Official operators list (source to check)")],
        ["Win rate, ROI, CLV, backtest results", '<span class="blank">blank</span>', '<span class="flag">unverified</span>', "No verified, time-stamped bet ledger exists", A("https://scikit-learn.org/stable/modules/calibration.html", "Calibration methodology (official basis)")],
    ]
    overview_body = (
        '<div class="grid">'
        + card("Direct retrieval", "The initial source set was retrieved on 2026-11-02; final integration re-reads carry their own dates through 2026-11-05. Search snippets are not treated as verification. " + A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"))
        + card("No invented values", "No NBA statistic, price, correlation or backtest result is asserted unless it is quoted from an official page. Unconfirmed values stay blank. " + A("https://www.nba.com/stats/overview", "NBA Stats overview"))
        + card("Automated gate", "A script rejects any table row without a directly verified official source link and any broken internal link. " + GH("tools/check_site.py", "tools/check_site.py"))
        + card("Engine tests", "The final integrated tree passes 32/32 dependency-free tests; the separate pinned scientific suite passes 120 tests plus six subtests. These are software checks, not evidence of betting skill. " + GH("tools/run_tests.py", "tools/run_tests.py"))
        + "</div>"
        + table("Verified entry points — official sources used", ["Source", "What it supports", "Official link", "Verification"], verified_entry_rows, "t-entry")
        + table("Values deliberately blank (no official confirmation)", ["Value", "Published value", "Status", "Why", "Source to check"], blank_rows, "t-blank")
        + '<section class="card"><h2>Scope of this section</h2><p>Other sessions produced the ' + I("../index.html", "main dashboard") + ' and the ' + I("../verified/", "source-linked verified data section") + '. This independent section re-verifies the combined result line by line: ' + I("summary.html", "executive summary") + ', ' + I("verification.html", "verification log") + ', ' + I("repo-review.html", "repo review") + ', and ' + I("flagged.html", "flagged items") + '. Publishing sources are documented by ' + A("https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site", "GitHub Docs") + '.</p></section>'
    )
    files["index.html"] = page("Overview", "Independent verification overview",
        "A source-first review of the Own6 NBA-lines research site. Only facts confirmed from official sources are published; everything else is blank and flagged.",
        overview_body, "index.html")

    # ---------------- Executive summary ----------------
    summary_rows = [
        ["Objective", "Originate own NBA lines; treat strategy development as a leaderboard competition that rewards skill, not luck", A("https://github.com/sassnarep3-star/Own6", "Official repository (project charter)"), "Project goal"],
        ["Own lines", "PACE × OffRtg/DefRtg multiplicative matchup → fair spread, total, win probability; home advantage and margin SD fitted from a game log", A("https://www.nba.com/stats/help/glossary", "NBA Stats Glossary (definitions)"), "Design; no numeric values published"],
        ["Player props", "Projected minutes × shrunk per-minute rate; availability from the official injury report", A("https://official.nba.com/nba-injury-report-2026-27-season/", "NBA Official injury report"), "Design; values blank"],
        ["Parlays / prop combos", "Gaussian-copula joint probability with ρ measured from paired residuals; independence only as a labelled special case", A("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "SciPy pearsonr (official)"), "Design; all ρ blank"],
        ["Validation gates", "G1–G8: walk-forward, n≥200, calibration, CLV, binomial + Bonferroni, bootstrap CI, correlation honesty, immutable ledger", A("https://scikit-learn.org/stable/modules/cross_validation.html", "scikit-learn cross-validation (official)"), "Design; no strategy has passed"],
        ["Leaderboard", "Score on the lower confidence bound of ROI plus CLV and calibration edge; small-sample heaters ineligible", A("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html", "SciPy bootstrap (official)"), "Empty by design"],
        ["Data availability", "NBA states stats are not available for download for academic or personal use; advanced stats go back to 1996-97, base stats to 1946-47", A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"), "Verified direct"],
        ["Availability reporting", "Teams must designate a participation status by 5 p.m. local time the day before a game (exceptions for back-to-backs)", A("https://official.nba.com/nba-injury-report-2026-27-season/", "NBA Official injury report"), "Verified direct"],
        ["Market context", "Official NBA gaming partners/operators list dated July 9, 2026; the 2021 co-official partner announcement is historical, not current", A("https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "NBA NBABet official list"), "Verified direct (dated)"],
        ["Integrity context", "Oct 26, 2026 official release cites limitations on permissible markets and alignment with the NBA's latest sports betting restrictions, but does not enumerate them", A("https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets", "NBA official release"), "Partly verified; specifics blank"],
        ["Verification rule", "Every table row links an official source; a value that cannot be confirmed stays blank and appears on Flagged for Review", A("https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site", "GitHub Docs (publishing rules)"), "Project policy"],
        ["Deployment", "GitHub Pages can publish from a branch or a workflow; this repo uses a legacy main:/ source with a root redirect to docs/", A("https://api.github.com/repos/sassnarep3-star/Own6/pages", "GitHub Pages API"), "Verified via API"],
        ["Rights / legal constraint", "NBA.com Terms of Use §1 restricts linking to Basketball Content without written permission; §9 restricts NBA Statistics use in gambling activity. Applicability requires qualified legal review; no statistic values are ingested.", A("https://www.nba.com/termsofuse", "NBA.com Terms of Use (official)"), "Flagged I-24 · needs review"],
        ["Irregularities", "Coordination collisions, broken/incorrect links and unverifiable fields are published on the Flagged for Review page and do not block the site", A("https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md", "COORDINATION.md (official repo)"), "needs review"],
    ]
    fact_rows = [
        ["PACE definition", "“The number of possessions per 48 minutes for a team or player.”", A("https://www.nba.com/stats/help/glossary", "NBA Stats Glossary"), "V02"],
        ["OffRtg definition", "“Measures a team's points scored per 100 possessions.”", A("https://www.nba.com/stats/help/glossary", "NBA Stats Glossary"), "V02"],
        ["NetRtg formula", "“Formula OFFRTG - DEFRTG”", A("https://www.nba.com/stats/help/glossary", "NBA Stats Glossary"), "V02"],
        ["USG% formula", "“(FGA + Possession Ending FTA + TO) / POSS”", A("https://www.nba.com/stats/help/glossary", "NBA Stats Glossary"), "V02"],
        ["No CSV download", "“Our stats are not available for download for either academic or personal use.”", A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"), "V03"],
        ["Advanced-stat coverage", "“Our advanced stats go back to the 1996-97 season”", A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"), "V03"],
        ["Base-stat coverage", "“our base stats go back to the inaugural 1946-47 season”", A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"), "V03"],
        ["Update timing", "“The advanced stats are updated between 10-15 minutes after a game finishes.”", A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"), "V03"],
        ["Injury-report deadline", "“By 5 p.m. local time the day before a game … teams must designate a participation status”", A("https://official.nba.com/nba-injury-report-2026-27-season/", "NBA Official injury report"), "V05"],
        ["Timestamped report", "“Injury Report: 11/02/26 01:45 PM”", A("https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-02_01_45PM.pdf", "Official injury PDF"), "V06"],
        ["2021 partner release", "Dated “November 4, 2021 9:23 AM”", A("https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners", "NBA.com News"), "V07"],
        ["2026 partner list", "Dated “July 9, 2026 11:35 AM”", A("https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "NBA NBABet"), "V21"],
        ["2026 integrity framework", "Dated “October 26, 2026 11:12 AM”; “limitations on permissible markets”", A("https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets", "NBA official release"), "V22"],
        ["Schedule sample", "“Week 3 (Nov 2 - Nov 8)” / “Monday, November 2” / “15 Games”", A("https://www.nba.com/schedule", "NBA.com schedule"), "V23"],
        ["Stats leaders sample", "“Yesterday's Leaders” dated 11/01/2026 with points/rebounds/assists leader tables", A("https://www.nba.com/stats/overview", "NBA Stats overview"), "V01"],
        ["Brier score", "“The Brier score measures the mean squared difference between the predicted probability and the actual outcome.”", A("https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html", "scikit-learn docs"), "V10"],
        ["Binomial luck test", "“The binomial distribution is used when there are exactly two mutually exclusive outcomes of a trial.”", A("https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm", "NIST e-Handbook"), "V14"],
        ["Bonferroni correction", "Method list includes “bonferroni : one-step correction”", A("https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html", "statsmodels docs"), "V13"],
        ["Terms of Use §1 (linking)", "“No Basketball Content from the Services may be … linked to, or otherwise used except as provided in these Terms of Use without the written permission of the Operator.”", A("https://www.nba.com/termsofuse", "NBA.com Terms of Use"), "V25"],
        ["Terms of Use §9 (statistics)", "“the NBA Statistics may not be used in connection with any gambling activity (including legal gambling activity)”", A("https://www.nba.com/termsofuse", "NBA.com Terms of Use"), "V25"],
    ]
    not_verified_rows = [
        ["Current team ratings", '<span class="blank">blank</span>', A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ — no official bulk download")],
        ["Correlation ρ for any pair", '<span class="blank">blank</span>', A("https://www.nba.com/stats/overview", "NBA Stats overview — source to check")],
        ["Closing lines / odds", '<span class="blank">blank</span>', A("https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2", "Official operators list — source to check")],
        ["Strategy ROI / hit rate / CLV", '<span class="blank">blank</span>', A("https://github.com/sassnarep3-star/Own6/blob/main/src/own6/validation.py", "validation.py (policy, not results)")],
        ["Specific prop/parlay restrictions", '<span class="blank">blank</span>', A("https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets", "Official release does not enumerate them")],
    ]
    summary_body = (
        table("Executive summary — important details", ["Topic", "Finding", "Official basis", "Status"], summary_rows, "t-summary")
        + table("Directly verified official facts (exact evidence)", ["Fact", "Evidence quoted from the official page", "Official source", "Log ID"], fact_rows, "t-facts")
        + table("Not verified — left blank by policy", ["Value", "Published value", "Source to check"], not_verified_rows, "t-notverified")
        + '<section class="card"><h2>Interpretation</h2><p>The framework separates <b>skill</b> (repeatable, out-of-sample, market-beating calibration and closing-line value) from <b>luck</b> (small-sample outcomes). No strategy is claimed profitable, and no reward scheme is asserted as empirically validated. See ' + I("../validation.html", "validation gates") + ' and ' + I("../leaderboard.html", "leaderboard") + ' on the main dashboard, plus the methodology basis from ' + A("https://scikit-learn.org/stable/modules/calibration.html", "scikit-learn") + ' and ' + A("https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm", "NIST") + '.</p></section>'
    )
    files["summary.html"] = page("Executive summary", "Executive summary",
        "Important details of the Own6 system, all source-linked. Initial quotes below were retrieved on 2026-11-02; later direct re-reads are dated individually in the verification log.",
        summary_body, "summary.html")

    # ---------------- Verification log ----------------
    with (ROOT / "data" / "verification_log.csv").open(newline="", encoding="utf-8") as fh:
        log_rows_raw = list(csv.DictReader(fh))
    log_rows = [
        [r["id"], esc(r["claim"]), A(r["url"], esc(r["official_source"])), r["retrieved_on"], esc(r["evidence_quote"]),
         f'<span class="{"ok" if r["status"] == "verified-direct" else "warn"}">{esc(r["status"])}</span>']
        for r in log_rows_raw
    ]
    check_rows = [
        ["Dependency-free tests", "python3 tools/run_tests.py", "32/32 pass on the final integrated tree", GH("tools/run_tests.py", "tools/run_tests.py")],
        ["Scientific tests", "python -m pytest -q tests", "120 passed, 6 subtests passed with pinned NumPy/SciPy/pytest", GH("tests", "tests")],
        ["Row-level source gate", "python3 tools/check_site.py", "Every data row on maintained pages links a verified official URL", GH("tools/check_site.py", "tools/check_site.py")],
        ["Internal link check", "python3 tools/check_site.py", "Relative href/src targets resolve inside the Pages root", GH("tools/check_site.py", "tools/check_site.py")],
        ["Site build drift", "python3 tools/build_review.py --check", "Generated review pages match committed files", GH("tools/build_review.py", "tools/build_review.py")],
        ["Source registry", "python3 tools/check_site.py", "Every data/sources.csv URL appears in the verification log", GH("data/sources.csv", "data/sources.csv")],
        ["Pages deployment", "gh api repos/sassnarep3-star/Own6/pages/builds/latest", "Build status and live URL checked after merge", A("https://api.github.com/repos/sassnarep3-star/Own6/pages", "GitHub Pages API")],
        ["Publishing-source rule", "GitHub Docs", "Branch-based and workflow-based publishing both documented", A("https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site", "GitHub Docs")],
    ]
    verification_body = (
        '<div class="grid">'
        + card("Method", "Direct retrieval from the official host (page/PDF) or an official GitHub REST API read. Exact evidence quotes are stored per row. " + A("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"))
        + card("Rule", "Search-engine snippets are not verification. An item marked verified-direct has a logged retrieval date and evidence quote. " + A("https://github.com/sassnarep3-star/Own6", "Official repository"))
        + "</div>"
        + table(f"Source verification log — {len(log_rows)} entries, line by line", ["ID", "Claim checked", "Official source", "Retrieved", "Evidence quoted from official page", "Status"], log_rows, "t-log")
        + table("Automated verification checks", ["Check", "Command", "Result", "Official basis"], check_rows, "t-checks")
        + '<section class="card"><h2>Machine-readable copies</h2><p>Full log: ' + GH("data/verification_log.csv", "data/verification_log.csv") + ' · Source registry: ' + GH("data/sources.csv", "data/sources.csv") + ' · Narrative record: ' + GH("audit/VERIFICATION.md", "audit/VERIFICATION.md") + ' · Final integration: ' + GH("audit/FINAL_INTEGRATION_REVIEW_2026-11-05.md", "2026-11-05 integration review") + ' · Gate report: ' + GH("audit/link_check_report.md", "audit/link_check_report.md") + '. Publishing rules: ' + A("https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site", "GitHub Docs") + '.</p></section>'
    )
    files["verification.html"] = page("Verification log", "Verification log — line by line",
        "Each row records one directly retrieved source, its own retrieval date, the exact scoped evidence observed and its status. V28–V54 are final-integration reads on 2026-11-05; limited rows do not certify a different historical snapshot.",
        verification_body, "verification.html")

    # ---------------- Repo review ----------------
    file_rows = [
        ["README.md", "Project overview; originally 6 bytes (# Own6); expanded by parallel sessions", GH("README.md"), "V20 · verified"],
        ["COORDINATION.md", "Shared task board; several session sections, claims and merge records", GH("COORDINATION.md"), "I-2 overlapping scopes"],
        ["EXECUTIVE_SUMMARY.md", "Objective, system, strategies, correlations, irregularities", GH("EXECUTIVE_SUMMARY.md"), "I-3 corrected claim"],
        ["index.html", "Root meta-refresh redirect to docs/ (Pages source is main:/)", GH("index.html"), "V17 / V19"],
        [".nojekyll / .gitignore", "Jekyll disabled; Python bytecode ignored", GH(".gitignore", ".gitignore on GitHub"), "I-11 resolved"],
        ["data/sources.csv", "Official source registry, S1–S22", GH("data/sources.csv"), "I-4 / I-14 corrected"],
        ["data/*.json", "Schedule, statute, NBA policy, strategies, methodology, flags (other session)", A("https://github.com/sassnarep3-star/Own6/tree/main/data", "data/ tree"), "Other session's scope"],
        ["docs/index.html", "Dashboard with own-line calculator", GH("docs/index.html"), "I-7 calculator repaired"],
        ["docs/sources.html", "Published source table", GH("docs/sources.html"), "I-3 / I-4 / I-20 corrected"],
        ["docs/validation.html", "Validation gates G1–G8", GH("docs/validation.html"), "I-20 rows linked"],
        ["docs/flagged.html", "Flagged for Review page", GH("docs/flagged.html"), "I-6 / new flags"],
        ["docs/leaderboard.html", "Empty leaderboard and scoring rule", GH("docs/leaderboard.html"), "I-20 row linked"],
        ["docs/correlations.html", "Correlation plan, all ρ blank", GH("docs/correlations.html"), "Values blank by policy"],
        ["docs/verified/**", "Separate source-linked section from session 05e359b8", A("https://github.com/sassnarep3-star/Own6/tree/main/docs/verified", "docs/verified/ tree"), "I-18 request logged"],
        ["src/own6/*.py", "Lines, props, parlay, validation, leaderboard utilities", A("https://github.com/sassnarep3-star/Own6/tree/main/src/own6", "src/own6/ tree"), "Definitions match V02 / V09–V16"],
        ["tests/test_engine.py", "Five unit tests", GH("tests/test_engine.py"), "5/5 pass (I-10)"],
        ["scripts/**", "Another session's site generator and checker", A("https://github.com/sassnarep3-star/Own6/tree/main/scripts", "scripts/ tree"), "Not edited"],
        ["tools/**", "This session's runner, gate and review-site generator", A("https://github.com/sassnarep3-star/Own6/tree/main/tools", "tools/ tree"), "New in this pass"],
    ]
    gh_rows = [
        ["Default branch / license", "main / no LICENSE file", A("https://api.github.com/repos/sassnarep3-star/Own6", "Repo API"), "I-19"],
        ["Pages source", "legacy, main:/ (root), https enforced", A("https://api.github.com/repos/sassnarep3-star/Own6/pages", "Pages API"), "I-12"],
        ["File tree", "docs/, docs/verified/, data/, src/, tests/, scripts/", A("https://api.github.com/repos/sassnarep3-star/Own6/git/trees/main?recursive=1", "Tree API"), "V20"],
        ["Initial commit", "c5d6e4c — one file, README.md", A("https://github.com/sassnarep3-star/Own6/commit/c5d6e4c4b3b7ed486d48b0bf4d9d0cbce89ef49d", "Commit page"), "V24"],
        ["Pull requests", "#1–#7 (six merged, #2 closed)", A("https://github.com/sassnarep3-star/Own6/pulls", "PR list"), "V24"],
        ["Branches", "main plus multiple arena/* session branches", A("https://github.com/sassnarep3-star/Own6/branches", "Branches"), "I-2"],
        ["Pages builds", "multiple built builds; live root URL reaches the dashboard", A("https://api.github.com/repos/sassnarep3-star/Own6/pages/builds", "Builds API"), "V19"],
    ]
    repo_body = (
        '<div class="grid">'
        + card("Starting state", "The repository began as a single 6-byte README. All current content was created by parallel sessions on 2026-11-02. " + A("https://github.com/sassnarep3-star/Own6/commit/c5d6e4c4b3b7ed486d48b0bf4d9d0cbce89ef49d", "Initial commit"))
        + card("Manual review", "Every row below links the official GitHub blob or API response so you can check it yourself. " + A("https://api.github.com/repos/sassnarep3-star/Own6/git/trees/main?recursive=1", "Tree API"))
        + "</div>"
        + table("Repository files reviewed line by line", ["Path", "Content checked", "Official link", "Finding / flag"], file_rows, "t-files")
        + table("GitHub-side facts (official API / repo)", ["Item", "Observed", "Official link", "Flag"], gh_rows, "t-gh")
        + table("Manual-review links", ["Artifact", "Why review it", "Official link"], [
            ["Coordination board", "Session claims, status and merge records", GH("COORDINATION.md", "COORDINATION.md")],
            ["Executive summary", "Narrative findings and irregularities", GH("EXECUTIVE_SUMMARY.md", "EXECUTIVE_SUMMARY.md")],
            ["Verification narrative", "Source-by-source verification record", GH("audit/VERIFICATION.md", "audit/VERIFICATION.md")],
            ["Repo-review narrative", "Full file-by-file review", GH("audit/REPO_REVIEW.md", "audit/REPO_REVIEW.md")],
            ["Flagged for Review", "All irregularities with source links", I("flagged.html", "Flagged for Review (this section)") + " · " + A("https://github.com/sassnarep3-star/Own6/blob/main/docs/flagged.html", "main flagged page")],
        ], "t-reviewlinks")
    )
    files["repo-review.html"] = page("Repo review", "Repository review — line by line",
        "Every file and GitHub-side fact checked during this pass, with links to the official repository or REST API for manual review.",
        repo_body, "repo-review.html")

    # ---------------- Flagged for Review ----------------
    F = "https://www.nba.com/stats/help/faq"
    OV = "https://www.nba.com/stats/overview"
    GL = "https://www.nba.com/stats/help/glossary"
    INJ = "https://official.nba.com/nba-injury-report-2026-27-season/"
    PDF = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-02_01_45PM.pdf"
    RULE = "https://official.nba.com/rulebook/"
    P21 = "https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners"
    P26 = "https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2"
    POL = "https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets"
    SCH = "https://www.nba.com/schedule"
    GHD = "https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site"
    API = "https://api.github.com/repos/sassnarep3-star/Own6/pages"
    REPO = "https://github.com/sassnarep3-star/Own6"
    COORD = "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"
    SKL = "https://scikit-learn.org/stable/modules/calibration.html"
    SCI = "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"
    NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm"

    def flag(fid, item, why, verify, url, label, status="needs review"):
        return [fid, esc(item), esc(why), esc(verify), A(url, label), f'<span class="{"ok" if status == "resolved" else "warn"}">{status}</span>']

    flags = [
        flag("F1", "Current team PACE / OffRtg / DefRtg values", "No official bulk download and no viewer-supplied export yet", "Export official stats with a retrieval date; publish n", F, "NBA Stats FAQ (source to check)"),
        flag("F2", "Fitted home-court advantage and margin SD", "Requires a historical game log built from official data", "Run lines.fit_from_games on an official-data log; publish n", OV, "NBA Stats overview (source to check)"),
        flag("F3", "All correlation values (ρ)", "Requires paired residual history from official box scores", "Compute ρ with parlay.pearson on exported residuals; publish ρ and n", SCI, "SciPy pearsonr (official method)"),
        flag("F4", "Strategy win rate / ROI / backtest results", "No verified bet ledger exists", "Walk-forward, timestamped ledger passing G1–G8", SKL, "scikit-learn calibration (official basis)"),
        flag("F5", "Live odds / closing lines", "Book-specific and time-specific; not published by the NBA as a stats table", "Timestamped capture from a licensed operator where legal", P26, "Official NBA operators list"),
        flag("F6", "Timestamped injury-report PDF", "NBA publishes dated PDFs; landing location may change", "Confirm the current report on the official injury-report page", INJ, "NBA Official injury report"),
        flag("F7", "Branch-name deviation", "Brief suggested session-<id> branches; Arena fixes each session to one branch", "Owner confirmation", COORD, "COORDINATION.md (official repo)"),
        flag("I-1", "Branch naming rule conflict", "Arena system rule forbids creating or switching to other branches; the brief's per-task branches cannot be used", "Owner acknowledgement of the platform constraint", COORD, "COORDINATION.md (official repo)"),
        flag("I-2", "Overlapping session claims", "Several parallel sessions claimed root/docs scopes and merged to main within minutes", "Reconcile claims in COORDINATION.md; keep file scopes disjoint", COORD, "COORDINATION.md (official repo)"),
        flag("I-3", "Incorrect “sandbox cannot fetch NBA.com” claim", "Direct retrieval succeeded for NBA Stats, FAQ, glossary, news, schedule and injury pages", "Corrected text and direct retrieval log", GL, "NBA Stats Glossary (directly retrieved)", "resolved"),
        flag("I-4", "Broken FAQ URL", "cdn.nba.com/stats/help/faq returned AccessDenied", "Replaced with www.nba.com/stats/help/faq (directly retrieved)", F, "NBA Stats FAQ", "resolved"),
        flag("I-5", "Injury-report PDF retrieval intermittent", "Chunk 0 failed once; chunk 1 and the official landing page confirm the report", "Use the stable landing page as the primary link", PDF, "Official injury-report PDF"),
        flag("I-6", "Relative link to raw coordination Markdown", "docs/flagged.html linked ../COORDINATION.md (raw file at the Pages root, not a rendered official source)", "Replaced with the official GitHub blob link", COORD, "COORDINATION.md (official repo)", "resolved"),
        flag("I-7", "Calculator used undefined JavaScript Math.erf", "Math.erf does not exist in standard JavaScript (confirmed in Node v22.22.3)", "Replaced with an Abramowitz–Stegun erf approximation; validated by the gate", REPO, "Official repository (fix)", "resolved"),
        flag("I-8", "Rulebook retrieval is content-limited", "official.nba.com/rulebook returned only the page heading", "Retrieve an official rule PDF/section before citing any specific rule", RULE, "NBA Official rulebook"),
        flag("I-9", "2021 partner announcement treated as current", "The NBA.com release is dated November 4, 2021", "Use the 2026 official partner list for current context", P21, "NBA.com News (2021 release)"),
        flag("I-10", "“5 tests passing” needed a rerun", "pytest is not installed in this sandbox (PEP 668 blocks system install)", "Rerun via the dependency-free tools/run_tests.py: 5/5 pass", REPO, "Official repository (tests)", "resolved"),
        flag("I-11", "Tracked Python bytecode in early commits", ".pyc files were committed before a .gitignore existed", ".gitignore added; bytecode absent from main", REPO, "Official repository"),
        flag("I-12", "Pages source could not be switched to /docs", "PUT /repos/.../pages returned HTTP 403 “Resource not accessible by integration”", "Owner can change the publishing source in repository settings", GHD, "GitHub Docs (publishing sources)"),
        flag("I-13", "Historical failed Actions deploy runs", "The earlier pages.yml deploy job failed; the workflow was removed in PR #4", "No deploy job remains; legacy branch publishing is used", GHD, "GitHub Docs (publishing sources)"),
        flag("I-14", "“Verified (indexed)” statuses were not direct verification", "Earlier pages relied on search-engine snippets", "All sources re-retrieved directly; logged in data/verification_log.csv", F, "NBA Stats FAQ (directly retrieved)", "resolved"),
        flag("I-15", "No official source for odds / closing lines", "Odds are not published by the NBA as an official stats table", "Timestamped capture from a licensed operator where legal", P26, "Official NBA operators list"),
        flag("I-16", "NBA prop/parlay restrictions not enumerated", "Official Oct 26 2026 release refers to restrictions without listing them; press reports are not official", "Obtain the official restriction text or leave blank", POL, "NBA official release"),
        flag("I-17", "Concurrent push caused a pull --rebase conflict", "Remote branch history changed while this session was working; the rebase was aborted cleanly", "Merge commit retained; no other session's work discarded", COORD, "COORDINATION.md (official repo)"),
        flag("I-18", "Other-session table rows lack official links", "docs/verified/methodology.html and strategies.html contain methodology rows with no external official link", "Owner of that scope should add official links or mark rows as non-data; request logged in COORDINATION.md", REPO, "Official repository (request logged)"),
        flag("I-19", "No LICENSE file", "GitHub API reports license: null for the repository", "Owner should add an appropriate license", REPO, "Official repository"),
        flag("I-20", "Main-site rows without official source links", "validation.html G5–G8, leaderboard.html's only data row, sources.html S8 and flagged.html F4/F7 lacked official links", "Official links added to every row; enforced by tools/check_site.py", NIST, "NIST e-Handbook (example of added link)", "resolved"),
        flag("I-21", "Coordination board misstates the Pages source", "COORDINATION.md says the site is served from main /docs; the Pages API reports main:/", "Correct the board text or change the publishing source", API, "GitHub Pages API"),
        flag("I-22", "Schedule data is date-specific", "Official schedule shows Week 3 / Monday Nov 2 2026 with 15 games; it changes daily", "Re-retrieve the official schedule on the date of use", SCH, "NBA.com schedule (source to check)"),
        flag("I-23", "Current official gaming partners list is dated", "The official list is dated July 9, 2026", "Re-retrieve before relying on it", P26, "NBA NBABet partners list"),
        flag("I-24", "NBA.com Terms of Use §§1 and 9 — content linking and NBA Statistics use", "§1 restricts linking to Basketball Content without written permission; §9 states NBA Statistics may not be used in connection with any gambling activity (including legal gambling) and only for news reporting or private non-commercial purposes. Legal applicability to this research site is undetermined.", "Obtain written permission / qualified legal review before ingesting NBA Statistics into betting models or republishing NBA content; keep all statistic values blank until resolved", "https://www.nba.com/termsofuse", "NBA.com Terms of Use (official)"),
    ]
    flagged_body = (
        '<div class="grid">'
        + card("Does not block", "Every item below is published for owner review and does not block publication. Flagged/unverified items stay blank in the data. " + A(GHD, "GitHub Docs"))
        + card("How to resolve", "Each row states what would verify it and links the official source to check. " + A(REPO, "Official repository"))
        + "</div>"
        + table("Flagged for Review — complete register", ["ID", "Item", "Why flagged", "What would verify it", "Source to check (official)", "Status"], flags, "t-flags")
        + '<section class="card"><h2>Related pages</h2><p>Main site: ' + I("../flagged.html", "Flagged for Review") + ' · ' + I("../sources.html", "Sources") + '. Other session: ' + I("../verified/flagged.html", "Verified-section flags") + '. Repository board: ' + A(COORD, "COORDINATION.md") + '.</p></section>'
    )
    files["flagged.html"] = page("Flagged for Review", "⚑ Flagged for Review",
        "Clearly labelled list of irregularities and unverified values. Nothing here was filled in by inference; these items do not block the site.",
        flagged_body, "flagged.html")

    return files


def main() -> int:
    files = build()
    check_only = "--check" in sys.argv
    changed: list[str] = []
    ASSETS.mkdir(parents=True, exist_ok=True)
    payload = {**{f"assets/{k}": v for k, v in (("style.css", CSS), ("app.js", JS))}, **files}
    for name, content in payload.items():
        path = OUT / name
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current != content:
            changed.append(str(path.relative_to(ROOT)))
            if not check_only:
                path.write_text(content, encoding="utf-8")
    if check_only:
        if changed:
            print("OUT OF DATE (run python3 tools/build_review.py):")
            for c in changed:
                print(" -", c)
            return 1
        print(f"OK: {len(payload)} generated files match the committed output")
        return 0
    print(f"Wrote/verified {len(payload)} files; changed: {len(changed)}")
    for c in changed:
        print(" -", c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
