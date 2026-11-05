#!/usr/bin/env python3
"""Build the luck-vs-skill and publication-acceptance section of the site.

Inputs (all committed):
  data/luck/required_bets.csv, detectable_roi.csv, parlay_requirements.csv,
  correlation_requirements.csv, multiple_testing.csv, luck_verdicts.csv,
  meta.json, bh_example.json, numerics_crosscheck.json, flags.csv
  data/acceptance/claims.csv, pages.csv, pr_ledger.csv, summary.json

Outputs:
  docs/luck/index.html        executive summary
  docs/luck/requirements.html sample-size requirements
  docs/luck/parlays.html      parlay / prop-combination requirements
  docs/luck/testing.html      multiple testing and observed-record verdicts
  docs/luck/method.html       formulas, cross-check evidence, sources
  docs/luck/acceptance.html   publication acceptance audit
  docs/luck/flagged.html      Flagged for Review
  docs/luck/assets/luck.css

Every table row carries a source link: an official method document for a
formula, or the repository/API evidence for a publication claim.  Nothing here
asserts an NBA fact.

Usage: python3 scripts/build_luck.py [--check]
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LUCK = ROOT / "data" / "luck"
ACCEPT = ROOT / "data" / "acceptance"
OUT = ROOT / "docs" / "luck"

REPO_BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"
METHOD_URL = "method.html"
ENGINE_URL = f"{REPO_BLOB}src/own6/power.py"
DATA_URL = f"{REPO_BLOB}data/luck/"

NAV = [
    ("index.html", "Overview"),
    ("requirements.html", "Sample size"),
    ("parlays.html", "Parlays & props"),
    ("testing.html", "Multiple testing"),
    ("method.html", "Method & checks"),
    ("acceptance.html", "Acceptance"),
    ("flagged.html", "Flagged for review"),
]

CAVEAT = (
    "Every figure on this page is arithmetic from the formulas in "
    "<code>src/own6/power.py</code>: a statement of how much evidence would be "
    "needed. No NBA result, sportsbook price, correlation estimate or return is "
    "observed, scraped or inferred here. Values that cannot be confirmed stay blank and are"
    " marked unverified; a blank is not zero."
)

CSS = """:root{--bg:#090f1e;--card:#131e31;--line:#30405b;--ink:#f3f6fd;--mut:#b2bfd2;--acc:#fba94b}
body{background:radial-gradient(ellipse at 78% 0%,#1b2c46 0%,#090f1e 45%);min-height:100vh}
main{max-width:1160px}
nav{align-items:center;gap:16px;background:#0d1729e6;padding:14px max(20px,calc((100vw - 1160px)/2))}
nav .brand{color:#fba94b;font-weight:800;letter-spacing:.06em;margin-right:auto;text-decoration:none}
nav a[aria-current="page"]{color:#fba94b}
.caveat{border-left:3px solid #fba94b;background:#131e31;border-radius:0 10px 10px 0;padding:14px 18px;color:#c4cfe0;margin:18px 0 26px}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:22px 0}
.stat{background:#131e31;border:1px solid #30405b;border-radius:12px;padding:16px}
.stat span{display:block;color:#b2bfd2;font-size:12px;min-height:32px}
.stat strong{font-size:26px;color:#fff;display:block;margin-top:6px}
.stat small{color:#8fa0ba;font-size:11px}
.table-wrap{overflow-x:auto;border:1px solid #30405b;border-radius:12px;background:#131e31;margin:16px 0 30px}
table{min-width:640px;font-size:13.5px}
th{background:#1a2a40;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:#eef3fb}
td{color:#d6e0ec}
td.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;white-space:nowrap}
.b-ok{background:#0f3d2e;color:#6ee7b7;border:1px solid #17715a}
.b-warn{background:#3b2a12;color:#fbbf24;border:1px solid #7c5a12}
.b-bad{background:#3d1720;color:#fca5a5;border:1px solid #7f1d1d}
.b-info{background:#12293d;color:#7dd3fc;border:1px solid #1e4b6b}
h1{font-size:32px;letter-spacing:-.02em}h2{margin-top:38px;font-size:23px}
.lead{color:#c8d3e2;font-size:16px;line-height:1.7;max-width:840px}
code{background:#0e1426;padding:1px 5px;border-radius:5px;font-size:12.5px}
.section-links{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 6px}
.section-links a{background:#131e31;border:1px solid #30405b;border-radius:9px;padding:10px 14px;text-decoration:none;font-weight:600;font-size:13.5px}
.section-links a:hover{border-color:#fba94b}
footer{border-top:1px solid #30405b;color:#9fb0c6;padding:20px max(20px,calc((100vw - 1160px)/2));font-size:13px;line-height:1.7}
.formula{background:#0e1426;border:1px solid #253450;border-radius:10px;padding:12px 16px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;color:#dbe4f2;overflow-x:auto}
"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_csv(name: Path) -> list[dict[str, str]]:
    with name.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(name: Path) -> dict:
    return json.loads(name.read_text(encoding="utf-8"))


def verdict_badge(verdict: str) -> str:
    mapping = {
        "verified": ("b-ok", "verified"),
        "mismatch": ("b-bad", "mismatch"),
        "needs review": ("b-warn", "needs review"),
        "verification blocked": ("b-warn", "blocked"),
        "not assessable": ("b-info", "not assessable"),
    }
    css, label = mapping.get(verdict.strip().lower(), ("b-info", verdict))
    return f'<span class="badge {css}">{esc(label)}</span>'


def severity_badge(severity: str) -> str:
    css = {"High": "b-bad", "Medium": "b-warn", "Low": "b-info", "Info": "b-info"}.get(severity, "b-info")
    return f'<span class="badge {css}">{esc(severity)}</span>'


def page(slug: str, title: str, intro: str, body: str) -> str:
    nav_parts = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == slug else ""
        nav_parts.append(f'<a href="{href}"{current}>{esc(label)}</a>')
    nav = "".join(nav_parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(intro[:180])}">
<title>{esc(title)} · Own6</title>
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="assets/luck.css">
</head>
<body>
<nav aria-label="Section navigation"><a class="brand" href="../index.html">OWN6 / LUCK &amp; SKILL</a>{nav}</nav>
<main>
<h1>{esc(title)}</h1>
<p class="lead">{intro}</p>
<div class="caveat">{CAVEAT}</div>
{body}
</main>
<footer>Research only — no wagers, no picks, no profitability claim. Statistical requirements reduce luck; they cannot create an edge. <a href="flagged.html">Flagged for review</a> · <a href="../index.html">Back to the dashboard</a> · <a href="https://www.nba.com/termsofuse">NBA Terms of Use</a> (not read this session)</footer>
</body>
</html>
"""


def table(caption: str, headers: list[str], rows: list[list[str]], numeric: set[int] | None = None) -> str:
    numeric = numeric or set()
    head = "".join(f'<th scope="col">{esc(header)}</th>' for header in headers)
    body = []
    for row in rows:
        cells = []
        for index, cell in enumerate(row):
            klass = ' class="num"' if index in numeric else ""
            cells.append(f"<td{klass}>{cell}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="table-wrap"><table>'
        f"<caption class=\"mut\" style=\"text-align:left;padding:10px 12px\">{esc(caption)}</caption>"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def source_cell(label: str, url: str) -> str:
    return f'<a href="{esc(url)}">{esc(label)}</a>'


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def build_index() -> str:
    required = read_csv(LUCK / "required_bets.csv")
    detectable = read_csv(LUCK / "detectable_roi.csv")
    verdicts = read_csv(LUCK / "luck_verdicts.csv")
    summary = read_json(ACCEPT / "summary.json")
    crosscheck = read_json(LUCK / "numerics_crosscheck.json")

    standard = [row for row in required if row["american_odds"] == "-110"]
    three = next(row for row in standard if row["true_roi_per_bet"] == "0.0300")
    five = next(row for row in standard if row["true_roi_per_bet"] == "0.0500")
    n500 = next(row for row in detectable if row["bets"] == "500")

    stats = f"""
<div class="stat-grid">
  <div class="stat"><span>Bets needed to prove a 3% edge at -110 (80% power)</span><strong>{esc(three['required_bets_alpha_0.05_power_0.80'])}</strong><small>Bonferroni over 200 candidates: {esc(three['required_bets_bonferroni_200_candidates'])}</small></div>
  <div class="stat"><span>Bets needed to prove a 5% edge at -110</span><strong>{esc(five['required_bets_alpha_0.05_power_0.80'])}</strong><small>Same test, larger edge, fewer bets</small></div>
  <div class="stat"><span>Smallest ROI detectable from 500 bets at -110</span><strong>{esc(n500['minimum_detectable_roi_percent'])}%</strong><small>Anything below this is luck at alpha 0.05</small></div>
  <div class="stat"><span>Numerical cross-checks against SciPy / statsmodels</span><strong>{sum(1 for c in crosscheck['checks'] if c['pass'])}/{len(crosscheck['checks'])}</strong><small>Largest difference {max(float(c['max_abs_difference']) for c in crosscheck['checks'] if 'max_abs_difference' in c):.2e}</small></div>
</div>
"""

    luck_rows = []
    for row in verdicts:
        luck_rows.append(
            [
                f"{esc(row['wins'])}/{esc(row['bets'])}",
                row["observed_win_rate"],
                row["exact_binomial_p_value_one_sided"],
                row["wilson_95_low"],
                verdict_badge("verified" if row["verdict"] == "exceeds_luck" else "needs review")
                + f" {esc(row['verdict'])}",
                source_cell("engine", ENGINE_URL),
            ]
        )

    body = f"""
{stats}
<h2>Why a record alone proves nothing</h2>
<p class="lead">A leaderboard rewards the strategy that looks best. Luck guarantees that one candidate looks best even when no candidate has an edge: with 200 tested candidates at alpha 0.05, about ten pass by chance alone. This section computes, in closed form, the sample sizes and corrections that separate a real edge from that noise, and then applies the rule to illustrative records.</p>
{table(
    "Luck-exclusion decisions for illustrative records at -110 (arithmetic, not a real strategy record)",
    ["Record", "Win rate", "Exact p-value", "Wilson 95% low", "Decision", "Source"],
    luck_rows,
    numeric={1, 2, 3},
)}
<p class="lead">A 55%/100-bet record looks excellent and is indistinguishable from luck: the p-value is 0.336 and the Wilson lower bound sits below the 52.38% break-even rate. Even 540 wins in 1,000 bets fails. Only when the sample grows to roughly 560 of 1,000 does the interval clear break-even.</p>

<h2>What each page contains</h2>
<div class="section-links">
  <a href="requirements.html">Sample-size requirements →</a>
  <a href="parlays.html">Parlays and prop combinations →</a>
  <a href="testing.html">Multiple testing and verdicts →</a>
  <a href="method.html">Formulas and numerical checks →</a>
  <a href="acceptance.html">Publication acceptance audit →</a>
  <a href="flagged.html">Flagged for review ({len(read_csv(LUCK / 'flags.csv'))} items) →</a>
</div>

<h2>Acceptance snapshot</h2>
<p class="lead">The publication audit checks the claims that can be checked from a primary source reachable in this environment. It verified {summary['claims_verified']} of {summary['claims']} claims against the GitHub API and the committed tree, flagged {summary['claims_needs_review']} for review, recorded {summary['claims_mismatch']} mismatch, and marked {summary['claims_blocked']} as blocked because the cited official hosts were unreachable.</p>
"""

    intro = (
        "How much evidence is needed before a betting record stops being explainable by luck — "
        "computed in closed form, with the multiple-testing penalty made explicit."
    )
    return page("index.html", "Luck is the default explanation", intro, body)


def build_requirements() -> str:
    required = read_csv(LUCK / "required_bets.csv")
    detectable = read_csv(LUCK / "detectable_roi.csv")

    bet_rows = []
    for row in required:
        bet_rows.append(
            [
                esc(row["scenario"]),
                esc(row["american_odds"]),
                esc(row["decimal_odds"]),
                f"{float(row['true_roi_per_bet']) * 100:.1f}%",
                esc(row["required_bets_alpha_0.05_power_0.80"]),
                esc(row["required_bets_bonferroni_200_candidates"]),
                source_cell("engine", ENGINE_URL),
            ]
        )
    detect_rows = []
    for row in detectable:
        detect_rows.append(
            [
                esc(row["bets"]),
                esc(row["american_odds"]),
                row["minimum_detectable_roi_percent"] + "%",
                row["per_bet_variance_at_break_even"],
                source_cell("engine", ENGINE_URL),
            ]
        )

    body = f"""
<h2>Bets required to detect a real edge</h2>
<p class="lead">The requirement is a one-sided test at alpha 0.05 with 80% power. The last column applies a Bonferroni correction for searching 200 candidate strategies, which is the realistic cost of running a leaderboard.</p>
{table(
    "Required independent bets per candidate strategy (computed; source: src/own6/power.py)",
    ["Price scenario", "American", "Decimal", "True ROI/bet", "Bets required", "Bets required (200 candidates)", "Source"],
    bet_rows,
    numeric={1, 2, 3, 4, 5},
)}
<p class="lead">Read the table as a gate, not a target. A strategy with a genuine 3% edge at -110 needs roughly 6,200 graded bets to be distinguishable from luck at these settings, and roughly 18,800 once 200 candidates compete. A 200-bet trial cannot support any claim about a 3% edge.</p>

<h2>The resolution limit of a small record</h2>
<p class="lead">Inverting the same formula gives the smallest ROI that a given number of bets can distinguish from noise. This is the honest resolution of the leaderboard: below these thresholds the ranking is a ranking of luck.</p>
{table(
    "Minimum detectable ROI by sample size at -110 (computed; source: src/own6/power.py)",
    ["Bets", "Price", "Minimum detectable ROI", "Per-bet variance", "Source"],
    detect_rows,
    numeric={0, 2, 3},
)}
<p class="lead">At 100 bets nothing under a 23.7% ROI is separable; at 1,000 bets the floor is still 7.5%. A leaderboard that rewards a 5% edge from a few hundred bets is rewarding noise.</p>
<h2>How this connects to the validation gates</h2>
<p class="lead">The wider project requires out-of-sample testing, calibration and uncertainty bounds before any strategy qualifies. This page supplies the sample-size input to those gates: it states the minimum n at which a gate can be evaluated at all. The published leaderboard still contains zero qualified strategies, because no authorised observation ledger exists.</p>
"""
    return page(
        "requirements.html",
        "Sample-size requirements",
        "Closed-form minimum sample sizes for detecting a positive per-bet ROI, and the smallest ROI a record of a given size can resolve.",
        body,
    )


def build_parlays() -> str:
    parlay = read_csv(LUCK / "parlay_requirements.csv")
    correlation = read_csv(LUCK / "correlation_requirements.csv")

    parlay_rows = []
    for row in parlay:
        parlay_rows.append(
            [
                esc(row["legs"]),
                esc(row["parlay_decimal_odds"]),
                row["true_joint_probability_independent"],
                f"{float(row['true_roi_per_parlay']) * 100:.2f}%",
                row["per_parlay_variance"],
                esc(row["required_parlays"]),
                source_cell("engine", ENGINE_URL),
            ]
        )
    corr_rows = []
    for row in correlation:
        corr_rows.append(
            [
                esc(row["true_correlation"]),
                esc(row["required_paired_observations"]),
                esc(row["method"]),
                source_cell("engine", ENGINE_URL),
            ]
        )

    body = f"""
<h2>Parlays: the edge compounds, and so does the variance</h2>
<p class="lead">Each extra leg multiplies both the payout and the joint probability. With an equal assumed 2% true edge per leg at -110, the ROI per ticket rises with the number of legs, but the variance rises faster, so the number of graded tickets needed stays in the same large range — and the independence assumption is exactly what a same-game parlay violates.</p>
{table(
    "Required graded parlays at an assumed 2% true edge per leg, independent-leg baseline (computed; source: src/own6/power.py)",
    ["Legs", "Parlay decimal odds", "True joint probability", "ROI per ticket", "Per-ticket variance", "Tickets required", "Source"],
    parlay_rows,
    numeric={0, 1, 2, 3, 4, 5},
)}
<p class="lead"><strong>Dependence warning.</strong> Same-game legs are correlated. The independent joint probability is a baseline for comparison only; a correlated ticket has a different joint probability and therefore a different variance and requirement. The project does not publish a correlation value, because none has been measured on a verified dataset.</p>

<h2>How much data a correlation estimate needs</h2>
<p class="lead">Prop combinations and parlays are only priced correctly if dependence is measured, and measuring dependence itself needs a large paired sample. These are the paired-observation requirements for a two-sided Fisher-z test at alpha 0.05 with 80% power.</p>
{table(
    "Paired observations required to detect a correlation (computed; source: src/own6/power.py)",
    ["True correlation", "Paired observations required", "Method", "Source"],
    corr_rows,
    numeric={0, 1},
)}
<p class="lead">A correlation of 0.10 needs about 783 paired observations; 0.20 needs about 194. Any teammate or same-game dependence asserted from a handful of games — several earlier pages in this repository use n = 6 — is not measurable at these settings, which is why the published correlation fields remain blank and flagged.</p>
<h2>Consequence for prop-combination strategies</h2>
<p class="lead">Multiply-the-marginals pricing is only valid under independence. Because the dependence measurement needs hundreds of paired observations and no verified dataset is configured, the prop-combination strategies on this site stay unqualified rather than being priced on an assumption.</p>
"""
    return page(
        "parlays.html",
        "Parlays and prop combinations",
        "What an n-leg ticket costs in evidence, and how many paired observations are needed before a correlation can be measured at all.",
        body,
    )


def build_testing() -> str:
    multiple = read_csv(LUCK / "multiple_testing.csv")
    verdicts = read_csv(LUCK / "luck_verdicts.csv")
    example = read_json(LUCK / "bh_example.json")

    mt_rows = []
    for row in multiple:
        mt_rows.append(
            [
                esc(row["candidate_strategies"]),
                esc(row["per_test_alpha_bonferroni"]),
                esc(row["expected_false_positives_if_all_noise"]),
                esc(row["required_bets_3pct_edge"]),
                source_cell("engine", ENGINE_URL),
            ]
        )
    verdict_rows = []
    for row in verdicts:
        verdict_rows.append(
            [
                f"{esc(row['wins'])}/{esc(row['bets'])}",
                esc(row["observed_win_rate"]),
                esc(row["roi"]),
                esc(row["exact_binomial_p_value_one_sided"]),
                esc(row["wilson_95_low"]),
                esc(row["wilson_95_high"]),
                verdict_badge("verified" if row["verdict"] == "exceeds_luck" else "needs review")
                + f" {esc(row['verdict'])}",
                source_cell("engine", ENGINE_URL),
            ]
        )

    bh_rows = []
    for p_value, q_value in zip(example["p_values"], example["q_values"]):
        bh_rows.append(
            [
                f"{p_value:.3f}",
                f"{q_value:.4f}",
                verdict_badge("verified" if q_value <= 0.05 else "needs review")
                + (" reject" if q_value <= 0.05 else " keep"),
                source_cell("engine", ENGINE_URL),
            ]
        )

    body = f"""
<h2>The leaderboard is a multiple-testing problem</h2>
<p class="lead">Selecting the best of many candidates inflates the winner's apparent skill. Two corrections are reported: Bonferroni controls the chance of <em>any</em> false discovery and is the conservative gate; Benjamini-Hochberg controls the expected <em>proportion</em> of false discoveries and is reported as a comparison.</p>
{table(
    "Cost of searching m candidate strategies (computed; source: src/own6/power.py)",
    ["Candidates", "Per-test alpha (Bonferroni)", "Expected false positives if all are noise", "Bets required for a 3% edge", "Source"],
    mt_rows,
    numeric={0, 1, 2, 3},
)}
<p class="lead">With 200 candidates, about ten pure-noise strategies pass an uncorrected alpha of 0.05. The correction also raises the sample each winner must show, from roughly 6,200 to roughly 18,800 bets for a 3% edge at -110.</p>

<h2>Worked Benjamini-Hochberg example</h2>
<p class="lead">The ten p-values below are an arbitrary illustration of the correction, not measured strategies. With m = 10, the largest rank satisfying p(j) ≤ (j/m)·alpha is rank 2, so exactly two hypotheses are rejected at 5%.</p>
{table(
    "Benjamini-Hochberg step-up on an illustrative p-value vector",
    ["p-value", "q-value", "Decision at 5%", "Source"],
    bh_rows,
    numeric={0, 1},
)}

<h2>The rule applied to observed records</h2>
<p class="lead">The decision rule requires both a p-value below alpha <em>and</em> a Wilson lower bound above the price's break-even probability. Requiring both prevents a significant but imprecise record from being called skill. Illustrative records only — no real strategy record exists on this site.</p>
{table(
    "Luck-exclusion decisions at -110 (computed; illustrative records)",
    ["Record", "Win rate", "ROI", "Exact p-value", "Wilson 95% low", "Wilson 95% high", "Decision", "Source"],
    verdict_rows,
    numeric={1, 2, 3, 4, 5},
)}
<h2>What would earn a leaderboard place</h2>
<p class="lead">A candidate qualifies only if, after the multiple-testing correction and on out-of-sample data, its lower confidence bound still clears break-even and its calibration passes. On the published evidence, zero candidates qualify; the reward table stays empty by design rather than by omission.</p>
"""
    return page(
        "testing.html",
        "Multiple testing and verdicts",
        "Corrections for searching many strategies, and the two-condition rule that decides whether a record exceeds luck.",
        body,
    )


def build_method() -> str:
    meta = read_json(LUCK / "meta.json")
    crosscheck = read_json(LUCK / "numerics_crosscheck.json")

    check_rows = []
    for check in crosscheck["checks"]:
        detail = []
        if "grid_points" in check:
            detail.append(f"grid points: {check['grid_points']}")
        if "max_abs_difference" in check:
            detail.append(f"max |difference|: {float(check['max_abs_difference']):.2e}")
        if "max_abs_difference_bets" in check:
            detail.append(f"max |difference|: {check['max_abs_difference_bets']} bets")
        if "max_abs_difference_pairs" in check:
            detail.append(f"max |difference|: {check['max_abs_difference_pairs']} pairs")
        check_rows.append(
            [
                esc(check["check"]),
                esc("; ".join(detail)),
                esc(check["tolerance"]),
                verdict_badge("verified" if check["pass"] else "mismatch"),
                source_cell("evidence", f"{REPO_BLOB}data/luck/numerics_crosscheck.json"),
            ]
        )

    source_rows = []
    for source in meta["method_sources"]:
        source_rows.append(
            [
                esc(source["name"]),
                source_cell("open", source["url"]),
                esc("read this session" if source["read_this_session"] else "NOT read this session"),
                esc(source["note"]),
            ]
        )

    FORMULA_BLOCK = """<div class="formula">per-bet mean  mu = p * d - 1 ;   variance = p(d-1)^2 + (1-p) - mu^2   (d = decimal odds, p = win probability)
required n     n = ceil( ((z_{1-alpha} + z_{power}) * sigma / mu)^2 )      one-sided test
detectable ROI mu_min = (z_{1-alpha} + z_{power}) * sigma / sqrt(n)
Bonferroni     alpha' = alpha / m  ;   expected false positives = m * alpha
Benjamini-Hochberg  q_(i) = min over j >= i of (m/j) * p_(j)
Fisher z       n = ceil( ((z_{1-alpha/2} + z_{power}) / atanh(r))^2 + 3 )
Wilson interval  standard score interval for a binomial proportion
p-value        exact binomial upper tail, evaluated in log space (no normal approximation)"""
    body = f"""
<h2>Formulas</h2>
<p class="lead">All figures are closed form; no simulation and no fitted parameter is involved.</p>
{FORMULA_BLOCK}
</div>

<h2>Numerical verification performed in this session</h2>
<p class="lead">The engine was compared against independent implementations installed from PyPI: SciPy {esc(crosscheck['libraries']['scipy'])} and statsmodels, running on Python {esc(crosscheck['libraries']['python'])}. Each quantity was computed twice and the difference recorded. This is evidence that the arithmetic is implemented correctly — it is not evidence about basketball.</p>
{table(
    "Cross-check results (committed evidence: data/luck/numerics_crosscheck.json)",
    ["Check", "Result", "Tolerance", "Verdict", "Source"],
    check_rows,
)}
<p class="lead">Reproduce with <code>python3 scripts/verify_luck_numerics.py</code> after installing the development dependencies, and re-verify the committed tables with <code>python3 scripts/luck_analysis.py --check</code>.</p>

<h2>Method references and their status</h2>
<p class="lead">These are the standard documents for the formulas used. Each row states plainly whether it was read during this session. None was: this sandbox could reach GitHub and PyPI only, so the references are citations, and the numerical cross-check above is the actual in-session verification.</p>
{table(
    "Method references (links open the official documentation)",
    ["Reference", "Link", "Read status", "Note"],
    source_rows,
)}

<h2>Assumptions and limits</h2>
<p class="lead">The requirements assume independent, fixed-price, equal-stake bets and a known true edge. Real markets move, stakes vary, and same-game legs are dependent, so the parlay rows are an independence baseline. The normal approximation is used for sample-size planning, while the p-value for an observed record is exact binomial. Nothing on this site observes a price or a result: the values are requirements, and the published leaderboard remains empty.</p>
<p class="lead">Machine-readable data: <a href="{esc(DATA_URL)}">data/luck/</a> · engine: <a href="{esc(ENGINE_URL)}">src/own6/power.py</a> · tests: <a href="{esc(REPO_BLOB)}tests/test_power.py">tests/test_power.py</a> · audit note: <a href="{esc(REPO_BLOB)}audit/LUCK_SKILL_2026_11_05.md">audit/LUCK_SKILL_2026_11_05.md</a></p>
"""
    return page(
        "method.html",
        "Method and numerical checks",
        "The exact formulas, the cross-check against SciPy and statsmodels, and the read status of every cited method reference.",
        body,
    )


def build_acceptance() -> str:
    claims = read_csv(ACCEPT / "claims.csv")
    pages = read_csv(ACCEPT / "pages.csv")
    ledger = read_csv(ACCEPT / "pr_ledger.csv")
    summary = read_json(ACCEPT / "summary.json")

    claim_rows = []
    for row in claims:
        claim_rows.append(
            [
                esc(row["id"]),
                esc(row["category"]),
                esc(row["claim"]),
                esc(row["observed"]),
                verdict_badge(row["verdict"]),
                source_cell("source", row["source_url"]),
            ]
        )
    page_rows = []
    for row in pages:
        page_rows.append(
            [
                f'<a href="../{esc(row["page"].replace("docs/", "", 1))}">{esc(row["page"])}</a>',
                esc(row["title"]),
                esc(row["generator"]),
                esc(row["table_rows"]),
                esc(row["inbound_links"]),
                verdict_badge("mismatch" if row["orphan"] == "yes" and row["intentional_orphan"] == "no" else "verified")
                + (f' orphan{" (intentional)" if row["intentional_orphan"] == "yes" else ""}' if row["orphan"] == "yes" else ""),
                source_cell("evidence", row["evidence_url"]),
            ]
        )
    pr_rows = []
    for row in ledger:
        pr_rows.append(
            [
                esc(row["pr"]),
                esc(row["title"][:90]),
                esc(row["state"]),
                esc(row["merged"]),
                esc((row["merged_at"] or "")[:10]),
                esc(row["head"]),
                source_cell("PR", row["evidence_url"]),
            ]
        )

    body = f"""
<h2>What was checked, and against what</h2>
<p class="lead">The audit separates three kinds of statement. Claims a primary source can settle here — the GitHub API and the committed tree — are verified or marked as a mismatch. Claims needing an official NBA or statute page are marked blocked, because those hosts did not answer from this sandbox. Claims about events outside a shallow clone are marked not assessable rather than guessed.</p>
<div class="stat-grid">
  <div class="stat"><span>Claims audited</span><strong>{summary['claims']}</strong><small>{summary['claims_verified']} verified · {summary['claims_needs_review']} needs review · {summary['claims_mismatch']} mismatch · {summary['claims_blocked']} blocked · {summary['claims_not_assessable']} not assessable</small></div>
  <div class="stat"><span>Published pages inventoried</span><strong>{summary['pages']}</strong><small>{summary['table_rows']} table rows · {summary['orphans']} unreachable</small></div>
  <div class="stat"><span>Pull requests referenced by the board</span><strong>{summary['prs_referenced']}</strong><small>{summary['prs_merged']} merged · {summary['prs_unmerged']} open or unmerged</small></div>
  <div class="stat"><span>API snapshot</span><strong>{esc(str(summary['snapshot_fetched_at_utc'])[:10])}</strong><small>{esc(str(summary['snapshot_fetched_at_utc']))}</small></div>
</div>

<h2>Claim-by-claim record</h2>
{table(
    "Publication acceptance claims (each row links its primary source)",
    ["ID", "Category", "Claim", "Observed", "Verdict", "Source"],
    claim_rows,
)}

<h2>Page inventory and provenance</h2>
<p class="lead">Every published HTML page, its generator, its row count and its reachability. A page with no inbound link cannot be found by a visitor, so it is treated as a defect unless its exclusion is deliberate and recorded.</p>
{table(
    "Every page under docs/ (evidence link opens the committed file)",
    ["Page", "Title", "Generator", "Rows", "Inbound", "Reachability", "Evidence"],
    page_rows,
    numeric={3, 4},
)}

<h2>Pull requests referenced by the coordination board</h2>
<p class="lead">Verification of the board's own record against the GitHub API. Unmerged references are disclosed, not merged by this session.</p>
{table(
    "Referenced pull requests and their API state",
    ["PR", "Title", "State", "Merged", "Merged on", "Head branch", "Source"],
    pr_rows,
    numeric={0},
)}
"""
    return page(
        "acceptance.html",
        "Publication acceptance audit",
        "Every checkable publication and repository claim, resolved against the GitHub API and the committed tree — with the checks that were impossible recorded as such.",
        body,
    )


def build_flagged() -> str:
    flags = read_csv(LUCK / "flags.csv")
    rows = []
    for row in flags:
        rows.append(
            [
                esc(row["id"]),
                severity_badge(row["severity"]),
                esc(row["category"]),
                f'<strong>{esc(row["item"])}</strong><br><span class="mut">{esc(row["detail"])}</span>',
                esc(row["status"]),
                source_cell("source", row["source_url"]),
                esc(row["action_requested"]),
            ]
        )
    body = f"""
<p class="lead">These items are published rather than hidden. None blocks the merge; each names what is unknown and what would settle it. Items marked <em>needs review</em> are open questions for the owner, not resolved facts.</p>
{table(
    "Flagged for review — luck/skill analysis and publication acceptance",
    ["ID", "Severity", "Category", "Item", "Status", "Source", "Action requested"],
    rows,
)}
<h2>Standing boundaries</h2>
<p class="lead">No NBA statistics, market prices or proprietary data are reproduced on this site. The published strategy leaderboard remains empty: zero strategies qualify. Values that could not be confirmed are blank, and a blank means unverified — not zero.</p>
"""
    return page(
        "flagged.html",
        "Flagged for review",
        "Open questions, blocked verifications and fixed defects from the luck/skill analysis and the publication audit.",
        body,
    )


PAGES = {
    "index.html": build_index,
    "requirements.html": build_requirements,
    "parlays.html": build_parlays,
    "testing.html": build_testing,
    "method.html": build_method,
    "acceptance.html": build_acceptance,
    "flagged.html": build_flagged,
}


def outputs() -> dict[Path, str]:
    files = {OUT / "assets" / "luck.css": CSS}
    for name, builder in PAGES.items():
        files[OUT / name] = builder()
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    files = outputs()
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, content in files.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        for name in stale:
            print(f"FAIL stale {name}")
        if stale:
            return 1
        print(f"OK: {len(files)} luck pages up to date")
        return 0
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"wrote {len(files)} files under docs/luck/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
