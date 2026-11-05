#!/usr/bin/env python3
"""Build the no-input hub. Unconfirmed values are blank, not badged numbers.

Repository record numbers and file links are provenance, not NBA assertions.
Official reference links never imply row-level verification. Stdlib only.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "docs/hub"
BLOB = "https://github.com/sassnarep3-star/Own6/blob/main/"
POLICY = ROOT / "data/hub_publication_policy.json"
NAV = [("index", "Overview"), ("summary", "Executive summary"),
       ("results", "Results"), ("standings", "Standings"), ("lines", "Lines"),
       ("props", "Player props"), ("forward-test", "Forward test"),
       ("strategies", "Strategies & leaderboard"), ("correlations", "Correlations"),
       ("validation", "Validation"), ("sources", "Sources"), ("flagged", "Flagged for Review")]
E = html.escape


def read_csv(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def link(url, text):
    return f'<a href="{E(url, quote=True)}" target="_blank" rel="noopener">{E(text)}</a>'


def repo(path, text="Repository evidence"):
    return link(BLOB + path, text)


def official_reference(url):
    """Only first-party NBA reference URLs, never ESPN-carried quotes."""
    parsed = urlparse(url)
    return (parsed.scheme == "https" and parsed.hostname in {"www.nba.com", "official.nba.com"}
            and not parsed.username and not parsed.password and parsed.port in (None, 443))


def load_policy():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy["mode"] != "withhold_unconfirmed" or policy["accepted_value_evidence"] != []:
        raise ValueError("This release has no accepted value evidence; publication override is forbidden")
    return policy


def blank(field):
    # Empty textContent is intentional: zero, em dash and 'N/A' are not substitutes.
    return f'<td data-field="{E(field, quote=True)}" data-state="unverified" aria-label="Unverified; value withheld"></td>'


def table(headers, rows, dataset=None):
    attrs = f' data-dataset="{E(dataset, quote=True)}"' if dataset else ""
    head = "".join(f'<th scope="col">{E(h)}</th>' for h in headers)
    return f'<div class="tw"><table{attrs} class="sortable"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def text_row(cells):
    return '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'


def dataset_table(spec):
    rows = []
    for index, record in enumerate(read_csv(spec["path"]), 1):
        for field in spec["fields"]:
            if field not in record:
                raise ValueError(f'{spec["path"]}: missing field {field}')
        reference = record.get(spec.get("source_field", ""), "")
        if not official_reference(reference):
            reference = spec["reference"]
        refs = link(reference, "Official reference (not value evidence)") + ' · ' + repo(spec["path"], "Raw repository record")
        cells = f'<td>CSV record {index}</td>' + ''.join(blank(f) for f in spec["fields"])
        cells += '<td><span class="b warn">UNVERIFIED · withheld</span></td><td>' + refs + '</td>'
        rows.append(f'<tr data-record="{index}" data-verification="unverified">{cells}</tr>')
    labels = [f.replace('_', ' ').capitalize() for f in spec["fields"]]
    return f'<h2>{E(spec["title"])}</h2><p class="mut">{len(rows)} repository records. Labels and counts identify local file structure only; blank cells are not zero.</p>' + table(
        ["Local record", *labels, "Publication status", "Source / provenance"], rows, spec["id"])


def page(key, title, body, lead):
    nav = '<a class="brand" href="../index.html">OWN6</a>' + ''.join(
        f'<a {"class=on " if k == key else ""}href="{k}.html">{E(label)}</a>' for k, label in NAV)
    notice = ('<div class="banner"><b>Strict evidence mode.</b> Unconfirmed source observations and derived outputs are blank. '
              'Prior-session verification labels are not accepted as row-level evidence by this release. '
              'An official link is a reference for review, not proof of the value. '
              '<a href="flagged.html">Evidence gaps and archived-site exceptions →</a></div>')
    out = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} — Own6</title><link rel="stylesheet" href="assets/hub.css"></head><body>
<header class="top">{nav}</header><main><h1>{E(title)}</h1><p class="lead">{E(lead)}</p>{notice}{body}</main>
<footer><p>No manual inputs, wagers or cash rewards. No profitable edge is established by this hub. Statistical controls can quantify uncertainty; they cannot eliminate luck.
{repo("audit/HUB_PUBLICATION_2026_11_03.md", "Executive review and limitations")} · <a href="../lab/overview.html">Empirical lab</a> · <a href="../review/index.html">Earlier review</a> · <a href="../verify/index.html">Verification ledger (2026-11-03)</a>.
Historical sections are preserved as unqualified archives, not verified-value publications. This repair covers docs/hub only.</p></footer>
<script src="assets/hub.js"></script></body></html>'''
    (HUB / f"{key}.html").write_text(out, encoding="utf-8")


STRATEGIES = [
    ("Single moneyline", "Fit pregame win distributions from permitted, timestamped inputs; compare with an executable no-vig market benchmark.", "Odds freshness, calibration and selection bias."),
    ("Single spread", "Model the home-margin distribution, retaining push mass where applicable; select only frozen positive-EV thresholds.", "Sign conventions, line movement and end-game variance."),
    ("Single total", "Model possessions and scoring jointly, with minutes and availability scenarios learned on training periods only.", "Roster changes, overtime and pace uncertainty."),
    ("Player prop", "Combine a minutes distribution with conditional production; fit to earlier games and respect provider settlement rules.", "Late availability, minutes tails and inconsistent markets."),
    ("Same-game prop combo", "Estimate joint exceedance on aligned, training-only residuals; validate joint outcomes, not just Pearson r.", "Sparse joint tails, shared pace/minutes and provider restrictions."),
    ("Cross-game parlay", "Require eligible single legs, a calibrated joint probability and the actual executable combo price.", "Shared news shocks and compounded calibration error; no default independence."),
]
GATES = [
    ("Rights & provenance", "Permitted data use, official result evidence and immutable quote snapshots; no scraping workaround."),
    ("Frozen experiment", "Versioned strategy, feature cutoff, market, settlement and trial registry before evaluation."),
    ("Input and quote contract", "Executable prices, event identifiers, time zone, capture time, overround and line-specific push rules."),
    ("Chronological holdout", "Rolling training/validation/test partitions with no future information or retuning on held-out outcomes."),
    ("Market and model calibration", "Reliability, proper scoring and market-relative comparisons with event-clustered uncertainty."),
    ("Economic evaluation", "Net returns and closing-line comparison after vig, fees, slippage and rejected-order handling."),
    ("Dependence", "Training-only aligned residuals; joint exceedance validation and slate/event-clustered intervals."),
    ("Multiple testing", "Log every attempted strategy, freeze the hypothesis family and adjust qualification statistics."),
    ("Robustness and risk", "Preregistered precision/sample requirements, temporal stability, drawdown and exposure caps."),
    ("Reproduction & promotion", "Independent artifact replay and prospective evidence; no qualification from process compliance alone."),
]


def build():
    policy = load_policy()
    HUB.mkdir(parents=True, exist_ok=True)
    datasets = policy["datasets"]
    leads = {
        "results": ("Results evidence ledger", "Local result records, with unsupported scores and identities withheld."),
        "standings": ("Standings and ratings", "Dated archive records are not current verified standings or ratings."),
        "lines": ("NBA line origination", "Market and model values remain blank until official evidence and input rights are resolved."),
        "props": ("Player props", "No confirmed sportsbook quote or settled prop evidence is accepted in this release."),
        "forward-test": ("Forward-test evidence", "Arithmetic reproducibility does not verify the source data or establish prospective skill."),
        "correlations": ("Correlation and joint probability", "No accepted empirical correlation or parlay price is published."),
    }
    for key, (title, lead) in leads.items():
        body = ''.join(dataset_table(d) for d in datasets if d["page"] == key)
        if key == "correlations":
            body += '<h2>Proposed dependence protocol</h2>' + table(["Question", "Proposed control", "Primary project specification"], [
                text_row(["Which correlation?", "Separate raw-score, binary outcome and conditional forecast-residual dependence. None alone identifies a joint tail probability.", repo("research/METHODOLOGY.md")]),
                text_row(["How to estimate?", "Pair outcomes by event and timestamp. Fit margins on training data only; retain zero residuals; report sample, uncertainty and stable out-of-time joint calibration.", repo("nba_lab/statistics.py")]),
                text_row(["How to price a combo?", "Estimate the joint event distribution and compare with an actual provider quote. A zero Pearson correlation does not establish independence; multiplying marginals is not the default.", repo("nba_lab/experiments.py") + " · " + link(policy["methodology_sources"][0]["url"], "SciPy official Pearson documentation")]),
            ])
        page(key, title, body, lead)

    strategy_rows = [text_row([E(name), E(signal), E(risk), '<span class="b warn">Proposed · not qualified</span>', repo("nba_lab/registry.py", "Implemented candidates")])
                     for name, signal, risk in STRATEGIES]
    body = table(["Category", "Signal research proposal", "Risks to validate", "Status", "Project source"], strategy_rows)
    body += '<h2>Leaderboard and reward policy</h2><p>Only independently reproduced, all-gate qualifiers may rank. Proposed ranking: lower confidence bound of net holdout ROI, subject to calibration, market benchmarks, multiplicity and risk controls. Freeze tie-breaks and reward rules before evaluation; do not pay rewards for a lucky win streak or merely completing process gates.</p>'
    body += table(["Eligible strategy", "Rank", "Reward", "Status", "Source"], [
        '<tr><td>No accepted qualifier</td>' + blank("rank") + blank("reward") + '<td>No award authorized; paper research only</td><td>' + repo("data/empirical/report.json", "Lab artifact (local status only)") + '</td></tr>'])
    page("strategies", "Strategies and leaderboard", body, "Authored research proposals, not externally verified betting edges. No cash contest is operated.")
    page("validation", "Validation gates", table(["Proposed gate", "Required control", "Hub release state", "Project specification"], [
        text_row([E(name), E(control), "Not established by this hub", repo("research/METHODOLOGY.md") + (" · " + link(policy["methodology_sources"][1]["url"], "Official time-series validation reference") if name == "Chronological holdout" else "")]) for name, control in GATES
    ]), "All gates must be evidenced together. A fixed sample threshold cannot prove skill or remove luck.")

    summary = [
        ("Executive decision", "Research-only and fail-closed. This hub does not establish a profitable edge or recommend a wager.", "data/hub_publication_policy.json"),
        ("Line origination", "Independent outcome distributions are the research target. Source observations, model projections, odds and edge fields are withheld because accepted row-level evidence is absent.", "scripts/build_hub.py"),
        ("Signals", "Investigate minutes, availability, possessions, scoring efficiency and market discrepancies only with permitted pregame data; compare against simple and market baselines.", "nba_lab/registry.py"),
        ("Singles and combinations", "Separate win, margin, total and prop distributions. Same-game and cross-game combinations require calibrated joint probabilities and executable quotes.", "nba_lab/experiments.py"),
        ("Correlation", "No accepted measured coefficient is published. Raw-score association is not residual dependence, and a sample-size rule alone does not establish usability.", "data/hub_publication_policy.json"),
        ("Skill versus luck", "Chronological holdouts, proper scoring, clustered uncertainty, trial correction and prospective replication quantify evidence; luck cannot be removed completely.", "research/METHODOLOGY.md"),
        ("Rewards", "Rank only qualified strategies under frozen rules. No strategy is qualified by this hub and no reward winner is asserted.", "scripts/build_hub.py"),
        ("Verification boundary", "This session inspected local repository artifacts and GitHub metadata. Direct NBA/source-page reads were not possible within the network allowlist. Historical verification claims are not repeated as current verification.", "audit/HUB_PUBLICATION_2026_11_03.md"),
        ("Remaining work", "Authorized feeds, archived first-party evidence and prospective evaluation are missing. Automated builds need no user input but cannot invent missing permissions or data.", "data/hub_publication_policy.json"),
    ]
    summary_table = table(["Topic", "Finding / proposal", "Primary project evidence"], [text_row([E(a), E(b), repo(c)]) for a, b, c in summary])
    page("summary", "Executive summary", summary_table, "What is built, what is supported, and what remains unverified.")
    cards = ''.join(f'<div class="card"><h3><a href="{key}.html">{E(title)}</a></h3><p>Source-linked records, research methods and explicit evidence limits.</p></div>' for key, title in NAV if key != "index")
    home = '<div class="banner bad"><b>No qualified betting line or reward winner.</b> This is an automated research dashboard, not a live wagering service.</div><div class="grid">' + cards + '</div><h2>At a glance</h2>' + summary_table
    page("index", "Own6 — NBA research dashboard", home, "A clean evidence-first hub for line origination, signal competition and validation. No manual entry required.")

    source_rows = []
    for d in datasets:
        source_rows.append(text_row([E(d["id"]), repo(d["path"], d["path"]), link(d["reference"], "Official reference"), "Not read directly in this session; no row-level value verified", "All displayed observation/output fields blank"]))
    for source in policy["methodology_sources"]:
        source_rows.append(text_row([E(source["id"]), repo("data/hub_publication_policy.json", "Pinned retrieval record"), link(source["url"], "Official project documentation"), E(source["method"] + " on " + source["retrieved_on"]), E(source["scope"])]))
    source_rows += [text_row(["Publication policy", repo("data/hub_publication_policy.json"), repo("scripts/check_hub.py", "Enforcement implementation"), "Locally inspected project artifacts", "Does not verify external NBA facts"])]
    page("sources", "Sources and evidence scope", table(["Dataset", "Repository provenance", "Official reference", "Retrieval / verification", "Publication rule"], source_rows), "References identify where evidence would be checked. They are not attestations that a particular historical value is correct.")

    flag_rows = [text_row(["P-" + d["id"], "Needs review · non-blocking", E(d["path"]), "No accepted source snapshot or value-level evidence; every displayed observation/output field withheld.", link(d["reference"], "Official review reference") + ' · ' + repo(d["path"])]) for d in datasets]
    flag_rows += [
        text_row(["P-gates-brier", "Needs review · repair requested", "Paired Brier edge", "At the inspected base, gates.py subtracts the model forecast rather than the outcome in the market squared-error term. Identical forecasts should have zero paired edge. Active engine owner asked to repair and add a regression; no cross-scope edit.", link("https://github.com/sassnarep3-star/Own6/pull/31#issuecomment-6618275302", "Exact coordination request") + " · " + link(policy["methodology_sources"][2]["url"], "Official Brier definition")]),
        text_row(["P-archives", "Needs review · non-blocking", "Earlier sites and raw data", "Older sections may display unconfirmed numbers, secondary odds, dated legal scope or inconsistent qualification rules. They remain preserved, not endorsed or newly verified by this hub repair.", repo("data/hub_flags.csv", "Historical issue register")]),
        text_row(["P-rights", "Needs review · non-blocking", "Data rights and jurisdiction", "No authorized gambling-use feed is configured. Historical NBA Terms and Korean-law concerns require actual source/legal review; no inference of legal permission is made from research-only labels or the user's location.", link("https://www.nba.com/termsofuse", "Official NBA Terms (reference only)") + ' · ' + repo("README.md")]),
        text_row(["P-model", "Needs review · non-blocking", "Performance and dependence", "Recomputation of stored data cannot establish source accuracy, prediction timestamps, profitable skill or stable joint tails. No empirical value is promoted.", repo("scripts/audit_integration.py")]),
        text_row(["P-access", "Needs review · non-blocking", "Direct verification unavailable", "Network restrictions prevented direct external NBA/statistical-reference reads in this session. No new verified-direct status is assigned. GitHub deployment metadata is checked separately.", repo("audit/HUB_PUBLICATION_2026_11_03.md")]),
    ]
    # Preserve earlier issues as attributed reports, never current verification assertions.
    for f in read_csv("data/hub_flags.csv"):
        flag_rows.append(text_row([E(f['id']), "Historical report · not reverified", E(f['category']), E(f['item']) + ' — historical detail available in the raw issue register.', repo("data/hub_flags.csv", "Attributed historical report")]))
    page("flagged", "Flagged for Review", table(["ID", "Status", "Scope", "Finding", "Source / review reference"], flag_rows), "Unconfirmed values and unresolved evidence limits are visible and do not masquerade as verified facts.")
    print(f"Hub built: {len(NAV)} pages; {len(datasets)} dataset tables; unconfirmed values withheld")


if __name__ == "__main__":
    build()
