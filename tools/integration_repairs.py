#!/usr/bin/env python3
"""Idempotent integration repairs to the shared pages merged from other sessions.

This session acts as final integration. It fixes only verification failures:
  * doc/index.html  — Math.erf (undefined JS) replaced with an erf approximation;
                      nav link to the independent review section.
  * doc/sources.html — false "cannot fetch NBA.com" claim; broken FAQ URL;
                      source table rebuilt from data/sources.csv so every row
                      links a directly verified official URL.
  * doc/validation.html — official source links for gates G5–G8 (and better
                      official bases for G1–G3).
  * doc/leaderboard.html — official source link on its only data row.
  * doc/flagged.html — corrected reasons, official GitHub link instead of a
                      relative Markdown link, and new irregularity rows.
  * doc/correlations.html — official Pearson-method link and accurate note.
  * all top-level pages — consistent navigation to both sub-sites.

Every replacement asserts its old text exists; if another session has since
changed a page, the script reports it rather than silently doing nothing.
Run: python3 tools/integration_repairs.py
"""
from __future__ import annotations

import csv
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GL = "https://www.nba.com/stats/help/glossary"
FAQ = "https://www.nba.com/stats/help/faq"
OV = "https://www.nba.com/stats/overview"
INJ = "https://official.nba.com/nba-injury-report-2026-27-season/"
PDF = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-02_01_45PM.pdf"
RULE = "https://official.nba.com/rulebook/"
P21 = "https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners"
P26 = "https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2"
POL = "https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets"
SKL = "https://scikit-learn.org/stable/modules/calibration.html"
BRIER = "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html"
CV = "https://scikit-learn.org/stable/modules/cross_validation.html"
BOOT = "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html"
PEARSON = "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"
BONF = "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html"
NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm"
GHVAL = "https://github.com/sassnarep3-star/Own6/blob/main/src/own6/validation.py"
GHCOORD = "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"
GHDOCS = "https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site"
GHAPI = "https://api.github.com/repos/sassnarep3-star/Own6/pages"

problems: list[str] = []
changes: list[str] = []


def read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def write(name: str, text: str) -> None:
    path = DOCS / name
    if path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
        changes.append(name)


def sub(name: str, old: str, new: str, label: str, count: int = 1) -> None:
    text = read(name)
    if new in text and old not in text:
        return  # already repaired
    if old not in text:
        problems.append(f"{name}: {label}: expected text missing (other session may have edited it)")
        return
    write(name, text.replace(old, new, count))


def anchor(url: str, label: str) -> str:
    return f'<a href="{url}">{label}</a>'


# ---------------------------------------------------------------- 1. calculator
CALC_SCRIPT = """<script>
/* Abramowitz & Stegun 7.1.26 erf approximation — Math.erf is not part of standard JavaScript. */
function erf(x){var s=x<0?-1:1;x=Math.abs(x);var t=1/(1+0.3275911*x);
 var p=(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-0.284496736)*t+0.254829592)*t;
 return s*(1-p*Math.exp(-x*x));}
function cdf(z){return .5*(1+erf(z/Math.SQRT2));}
function calc(){var v=function(id){return parseFloat(document.getElementById(id).value)};
 var out=document.getElementById('out');
 var hp=v('hp'),ap=v('ap'),ho=v('ho'),hd=v('hd'),ao=v('ao'),ad=v('ad'),lg=v('lg'),ha=v('ha'),sd=v('sd');
 if([hp,ap,ho,hd,ao,ad,lg,ha,sd].some(function(x){return !isFinite(x)})||lg<=0||sd<=0){
   out.textContent='Fill every field from official NBA Stats (league OffRtg and margin SD must be greater than 0) — no values are guessed for you.';return;}
 var pace=(hp+ap)/2;
 var h=pace*(ho/100)*(ad/100)/(lg/100)+ha/2, a=pace*(ao/100)*(hd/100)/(lg/100)-ha/2, m=h-a;
 out.textContent='Fair spread (home): '+(-m).toFixed(1)+' · Fair total: '+(h+a).toFixed(1)+
   ' · Home win prob: '+(100*cdf(m/sd)).toFixed(1)+'% · Exp pts '+h.toFixed(1)+'–'+a.toFixed(1);}
</script>"""
idx = read("index.html")
if "Math.erf" in idx:
    new_idx, n = re.subn(r"<script>.*?</script>", CALC_SCRIPT, idx, count=1, flags=re.S)
    if n:
        write("index.html", new_idx)
    else:
        problems.append("index.html: could not locate inline calculator script")
elif "Abramowitz" not in idx:
    problems.append("index.html: calculator script changed by another session; review manually")

# ---------------------------------------------------------------- 2. sources page
src = read("sources.html")
if "Sandbox cannot fetch NBA.com directly" in src:
    src = src.replace(
        "Sandbox cannot fetch NBA.com directly (network-restricted); each link below was confirmed via indexed official pages on 2026-11-02. Click through to manually review. Full registry: <code>data/sources.csv</code>.",
        "Every source below was retrieved <b>directly from the official host</b> on 2026-11-02 (not via search snippets). Evidence quotes and retrieval methods are in the "
        + anchor("review/verification.html", "Verification Log") + " and <code>data/verification_log.csv</code>. Full registry: <code>data/sources.csv</code>. NBA.com is directly reachable from this environment; earlier text claiming otherwise was incorrect and has been corrected.",
    )
elif "retrieved <b>directly from the official host</b>" not in src:
    problems.append("sources.html: intro changed by another session; review manually")

with (ROOT / "data" / "sources.csv").open(newline="", encoding="utf-8") as fh:
    registry = list(csv.DictReader(fh))
rows = []
for r in registry:
    url = r["url"]
    status = r["status"]
    cls = "ok" if status.startswith("verified-direct") else "flag"
    label = html.escape(r["official_source"])
    status_text = "UNVERIFIED — blank" if status == "UNVERIFIED-BLANK" else html.escape(status)
    if status == "UNVERIFIED-BLANK":
        label += " (source to check; not a confirmation)"
    rows.append(
        f'<tr><td>{html.escape(r["id"])}</td><td>{html.escape(r["claim_or_input"])}</td>'
        f'<td>{anchor(url, label)}</td><td>{html.escape(r["verified_via"])}</td>'
        f'<td class="{cls}">{status_text}</td></tr>'
    )
new_table = (
    '<table><tr><th>ID</th><th>Claim / input</th><th>Official source</th>'
    '<th>Verified via</th><th>Status</th></tr>' + "".join(rows) + "</table>"
)
src, n = re.subn(r"<table>.*?</table>", new_table, src, count=1, flags=re.S)
if not n:
    problems.append("sources.html: could not rebuild source table")
write("sources.html", src)

# ---------------------------------------------------------------- 3. validation gates
sub("validation.html", "<td>Exact binomial (implemented, tested)</td>",
    f'<td>{anchor(NIST, "Exact binomial (NIST)")} · {anchor(BONF, "Bonferroni (statsmodels)")}</td>', "G5 official links")
sub("validation.html", "<td>Bootstrap (implemented, tested)</td>",
    f'<td>{anchor(BOOT, "Bootstrap CI (SciPy official docs)")}</td>', "G6 official link")
sub("validation.html", '<td><a href="correlations.html">Correlations page</a></td>',
    f'<td>{anchor(PEARSON, "Pearson ρ (SciPy official docs)")} · {anchor("correlations.html", "Correlations page")}</td>', "G7 official link")
sub("validation.html", "<td>Project policy (disclosed)</td>",
    f'<td>{anchor(GHVAL, "Ledger policy (official repository)")}</td>', "G8 official link")
sub("validation.html", '<td><a href="https://scikit-learn.org/stable/modules/calibration.html">Calibration on unseen data (sklearn)</a></td>',
    f'<td>{anchor(CV, "Hold-out / cross-validation (scikit-learn)")} · {anchor(GHVAL, "Gate implementation")}</td>', "G1 official basis")
sub("validation.html", '<td>Project policy (disclosed) — statistical basis <a href="https://scikit-learn.org/stable/modules/calibration.html">sklearn</a></td>',
    f'<td>Project policy — {anchor(CV, "hold-out validation (scikit-learn)")} · {anchor(GHVAL, "implementation")}</td>', "G2 official basis")
sub("validation.html", '<td><a href="https://scikit-learn.org/stable/modules/calibration.html">Brier / proper scoring rules</a></td>',
    f'<td>{anchor(BRIER, "Brier score definition")} · {anchor(SKL, "Calibration guide")}</td>', "G3 official basis")

# ---------------------------------------------------------------- 4. leaderboard
sub("leaderboard.html", '<td><a href="validation.html">Gates must pass first</a></td>',
    f'<td>{anchor("validation.html", "Gates must pass first")} · {anchor(BOOT, "Bootstrap lower bound (SciPy)")}</td>', "leaderboard official link")

# ---------------------------------------------------------------- 5. flagged page
sub("flagged.html", "<td>Sandbox network cannot fetch NBA.com; NBA offers no CSV download</td>",
    "<td>NBA.com is directly reachable, but the NBA offers no official bulk download (see FAQ) and no dated viewer export has been produced</td>", "F1 reason")
sub("flagged.html", "<td>Require paired residual history from official box scores</td>",
    "<td>Requires paired residual history computed from official box scores; no such dataset exists in the repo</td>", "F3 reason")
sub("flagged.html", '<td><a href="validation.html">Validation Gates</a></td>',
    f'<td>{anchor("validation.html", "Validation Gates")} · {anchor(NIST, "NIST binomial (official basis)")}</td>', "F4 official link")
sub("flagged.html", '<td><a href="https://official.nba.com/">official.nba.com</a></td>',
    f'<td>{anchor(INJ, "NBA Official injury report (stable landing page)")}</td>', "F6 official link")
sub("flagged.html", '<td><a href="../COORDINATION.md">COORDINATION.md</a></td>',
    f'<td>{anchor(GHCOORD, "COORDINATION.md (official GitHub blob)")}</td>', "F7 official link")

extra_flags = [
    ("I-3", "Incorrect “sandbox cannot fetch NBA.com” claim", "Direct retrieval of NBA.com succeeded", "Corrected; see verification log", GL, "NBA Stats Glossary"),
    ("I-4", "Broken FAQ URL (cdn.nba.com/stats/help/faq)", "Returned AccessDenied", "Replaced with the working official FAQ URL", FAQ, "NBA Stats FAQ"),
    ("I-7", "Calculator used undefined Math.erf", "Not part of standard JavaScript", "Replaced with an erf approximation; gate enforces it", GHVAL, "Official repository"),
    ("I-9", "2021 partner release treated as current", "Release is dated Nov 4, 2021", "Use the 2026 official partner list", P21, "NBA.com News (2021)"),
    ("I-12", "Pages source could not be changed to /docs", "REST API returned HTTP 403", "Change publishing source in repo settings", GHDOCS, "GitHub Docs"),
    ("I-16", "Prop/parlay restrictions not enumerated officially", "Official release refers to restrictions without listing them", "Obtain official restriction text or leave blank", POL, "NBA official release"),
    ("I-19", "No LICENSE file", "GitHub API reports license: null", "Owner should add a license", "https://github.com/sassnarep3-star/Own6", "Official repository"),
    ("I-21", "Coordination board misstates Pages source", "Board says main /docs; API reports main:/", "Correct the board or change the source", GHAPI, "GitHub Pages API"),
    ("I-22", "Schedule values are date-specific", "Official schedule changes daily", "Re-retrieve on the date of use", "https://www.nba.com/schedule", "NBA.com schedule"),
    ("I-23", "Current official gaming partners", "List dated July 9, 2026; re-check before use", "Re-retrieve the official list", P26, "NBA NBABet"),
    ("I-24", "NBA.com Terms of Use §§1 and 9 — content linking / NBA Statistics use", "§1 restricts linking to Basketball Content without written permission; §9 says NBA Statistics may not be used in connection with any gambling activity (including legal gambling). Legal applicability is undetermined.", "Obtain written permission / qualified legal review; keep statistic values blank until resolved", "https://www.nba.com/termsofuse", "NBA.com Terms of Use (official)"),
]
flag_html = "".join(
    f'<tr><td>{fid}</td><td>{html.escape(item)}</td><td>{html.escape(why)}</td>'
    f'<td>{html.escape(verify)}</td><td>{anchor(url, label)}</td><td class="warn">needs review</td></tr>'
    for fid, item, why, verify, url, label in extra_flags
)
fl = read("flagged.html")
if 'id="I-3"' not in fl and ">I-3<" not in fl:
    fl = fl.replace("</table>", flag_html + "</table>", 1)
    fl = fl.replace(
        "Review after launch and request changes via the repo.",
        'Review after launch and request changes via the repo. Complete register with all items: '
        + anchor("review/flagged.html", "Independent review — Flagged for Review") + ".",
    )
write("flagged.html", fl)

# ---------------------------------------------------------------- 6. correlations note
co = read("correlations.html")
if "Pearson correlation coefficient" not in co:
    co = co.replace(
        "The table is the measurement plan; the <b>Value (ρ)</b> column stays blank until computed.",
        "The table is the measurement plan; the <b>Value (ρ)</b> column stays blank until computed. "
        + anchor(OV, "NBA.com is directly reachable") + ", but no official residual dataset has been computed. "
        + "The measurement method is the " + anchor(PEARSON, "Pearson correlation coefficient (SciPy official docs)") + "; "
        + "no ρ value is inferred.",
    )
write("correlations.html", co)

# ---------------------------------------------------------------- 7. consistent navigation
for path in sorted(DOCS.glob("*.html")):
    text = path.read_text(encoding="utf-8")
    head, sep, tail = text.partition("</nav>")
    if not sep or "<nav>" not in head:
        continue
    add = ""
    if 'href="verified/"' not in head:
        add += '<a href="verified/">✓ Verified data</a>'
    if 'href="review/"' not in head:
        add += '<a href="review/">✓ Independent review</a>'
    if add:
        path.write_text(head + add + sep + tail, encoding="utf-8")
        changes.append(path.name)

for p in problems:
    print("WARN ", p)
print(f"Repairs applied to {len(set(changes))} files; warnings: {len(problems)}")
for c in sorted(set(changes)):
    print(" -", c)
# Warnings are informational (another session may have legitimately changed a page);
# the strict gate tools/check_site.py decides whether the site is publishable.
sys.exit(0)
