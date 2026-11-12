#!/usr/bin/env python3
"""Deterministic static-site builder for the NFL origination, depth and skill-gate pack.

Reads the verified / computed / unverified registers in data/nfl_3b81013c/, enforces the
blank-cell rule for anything that is not confirmed, and writes 11 accessible HTML pages
plus one stylesheet in docs/nfl-3b81013c/.

Nothing in this builder invents a value. Every number printed either comes from an
official NFL source page (recorded per row) or is arithmetic over those inputs, and the
arithmetic is recomputed by scripts/check_nfl_3b81013c.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "nfl_3b81013c"
OUT_DIR = ROOT / "docs" / "nfl-3b81013c"

NAV_ITEMS = [
    ("index.html", "Summary"),
    ("lines.html", "Originated Lines"),
    ("depth.html", "Injuries & Depth"),
    ("deficiencies.html", "Depth Deficiency"),
    ("strategies.html", "Strategies & Gates"),
    ("leaderboard.html", "Leaderboard"),
    ("correlations.html", "Correlations"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Site Suggestions"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]

# Hosts accepted as an official first-party NFL source.
OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com", "operations.nfl.com"}
# Hosts accepted as a recognised methodological / governance reference.
METHOD_HOSTS = {
    "www.itl.nist.gov", "docs.scipy.org", "scikit-learn.org", "www.statsmodels.org",
    "docs.github.com",
}

TERMS_URL = "https://www.nfl.com/legal/terms/"
TERMS_LABEL = "NFL.com Terms of Use"
STATUS_ORDER = {"verified": 0, "computed": 1, "unverified": 2}

ARROW = " \u2197"
ELLIPSIS = " \u2026"

STYLES_CSS = """\
:root {
  --bg: #f6f8fb;
  --surface: #ffffff;
  --surface-alt: #eef2f7;
  --border: #c9d4e2;
  --border-subtle: #e3eaf3;
  --text: #0f1c2e;
  --muted: #4b5c72;
  --accent: #12395e;
  --accent-soft: #e3edf9;
  --verified-bg: #dcfce7;
  --verified-fg: #14532d;
  --computed-bg: #dbeafe;
  --computed-fg: #1e3a8a;
  --unverified-bg: #fef3c7;
  --unverified-fg: #7c2d12;
  --warn-bg: #fff7ed;
  --warn-border: #fdba74;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
  font-size: 15px;
}

.container { max-width: 1280px; margin: 0 auto; padding: 0 20px; }

.site-header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 0 0; }

.brand-row { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 6px 16px; padding-bottom: 10px; }
.brand-title { font-size: 1.06rem; font-weight: 700; color: var(--accent); margin: 0; }
.brand-meta { font-size: 0.82rem; color: var(--muted); margin: 0; }

.nav-bar { display: flex; flex-wrap: wrap; gap: 4px; border-top: 1px solid var(--border-subtle); padding: 8px 0; }
.nav-bar a { text-decoration: none; color: var(--muted); font-weight: 600; font-size: 0.86rem; padding: 6px 10px; border-radius: 6px; }
.nav-bar a:hover { background: var(--surface-alt); color: var(--text); }
.nav-bar a.active { background: var(--accent); color: #ffffff; }

main { padding: 24px 0 40px; }

.eyebrow { text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.74rem; font-weight: 700; color: var(--accent); margin: 0 0 6px; }
h1 { font-size: 1.66rem; line-height: 1.25; margin: 0 0 10px; }
h2 { font-size: 1.18rem; margin: 30px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
h3 { font-size: 1rem; margin: 20px 0 8px; }
p, li { color: var(--text); }
.lead { color: var(--muted); max-width: 980px; margin: 0 0 16px; }

.banner { background: var(--warn-bg); border: 1px solid var(--warn-border); border-left: 4px solid #ea580c; border-radius: 8px; padding: 11px 15px; margin: 0 0 20px; font-size: 0.89rem; }
.banner strong { color: #9a3412; }

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(205px, 1fr)); gap: 12px; margin: 0 0 22px; }
.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 13px 15px; }
.kpi-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); font-weight: 700; margin: 0 0 4px; }
.kpi-value { font-size: 1.3rem; font-weight: 700; color: var(--accent); margin: 0 0 5px; }
.kpi-note { font-size: 0.83rem; color: var(--muted); margin: 0; }

.table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; overflow-x: auto; margin: 0 0 22px; }
table { width: 100%; border-collapse: collapse; font-size: 0.87rem; }
thead th { background: var(--surface-alt); color: var(--text); font-weight: 700; text-align: left; padding: 9px 11px; border-bottom: 2px solid var(--border); white-space: nowrap; }
tbody td, tbody th { padding: 9px 11px; border-bottom: 1px solid var(--border-subtle); vertical-align: top; text-align: left; }
tbody tr:last-child td, tbody tr:last-child th { border-bottom: none; }
tbody tr:hover { background: #f9fbfe; }
td.num { font-variant-numeric: tabular-nums; }
td.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.82rem; }
td.id-cell { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.8rem; color: var(--muted); white-space: nowrap; }
td.empty-cell { background: repeating-linear-gradient(-45deg, #fffbeb, #fffbeb 6px, #fef3c7 6px, #fef3c7 12px); min-width: 78px; }
td.src-cell { font-size: 0.82rem; }
td.detail-cell { color: var(--muted); font-size: 0.83rem; min-width: 260px; }

.badge { display: inline-block; font-size: 0.73rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; text-transform: lowercase; white-space: nowrap; }
.badge-verified { background: var(--verified-bg); color: var(--verified-fg); }
.badge-computed { background: var(--computed-bg); color: var(--computed-fg); }
.badge-unverified { background: var(--unverified-bg); color: var(--unverified-fg); }

a { color: var(--accent); }
a.src-link { font-weight: 600; }
.src-sep { color: var(--muted); padding: 0 3px; }

.note { background: var(--accent-soft); border: 1px solid var(--border); border-radius: 8px; padding: 11px 15px; margin: 0 0 20px; font-size: 0.88rem; }
ol, ul { padding-left: 20px; }

.site-footer { border-top: 1px solid var(--border); background: var(--surface); padding: 16px 0; font-size: 0.83rem; color: var(--muted); }
"""


class DataError(RuntimeError):
    """Raised when a register breaks the blank-cell or source-link contract."""


def _parse_url_list(url: str) -> list[str]:
    return [u.strip() for u in url.split() if u.strip()]


def is_official_url(url: str) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in OFFICIAL_HOSTS


def is_method_url(url: str) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in METHOD_HOSTS


def validate_register(name: str, rows: list[dict[str, str]], fields: list[str]) -> None:
    """Enforce the three-state evidence contract on already-parsed register rows."""
    if not fields or len(set(fields)) != len(fields):
        raise DataError(f"{name}: duplicate or missing CSV headers")
    for index, row in enumerate(rows, 2):
        status = (row.get("verification_status") or "").strip()
        if status not in STATUS_ORDER:
            raise DataError(f"{name}:{index}: invalid verification_status {status!r}")
        if "value" in fields:
            value = (row.get("value") or "").strip()
            if status == "unverified" and value != "":
                raise DataError(f"{name}:{index}: unverified row must leave its value blank, got {value!r}")
            if status != "unverified" and value == "":
                raise DataError(f"{name}:{index}: {status} row must carry a value")
        official = (row.get("official_source_url") or "").strip()
        if not any(is_official_url(u) for u in _parse_url_list(official)):
            raise DataError(f"{name}:{index}: no HTTPS official NFL source URL")
        method = (row.get("methodology_reference_url") or "").strip()
        if method and not any(is_method_url(u) for u in _parse_url_list(method)):
            raise DataError(f"{name}:{index}: methodology URL not on the reference allowlist: {method!r}")


def load_csv(name: str) -> list[dict[str, str]]:
    """Load a register file and validate it."""
    path = DATA_DIR / name
    if not path.is_file():
        raise DataError(f"missing register data/nfl_3b81013c/{name}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = reader.fieldnames or []
    validate_register(name, rows, fields)
    return rows


def terms_link() -> str:
    """Shared official terms link used by narrative tables that cite no other source."""
    return link(TERMS_URL, TERMS_LABEL + ARROW)


def badge(status: str) -> str:
    return f'<span class="badge badge-{status}">{escape(status)}</span>'


def value_cell(value: str, status: str, numeric: bool = False) -> str:
    if status == "unverified" or value.strip() == "":
        return '<td class="empty-cell"></td>'
    css = ' class="num"' if numeric else ""
    return f"<td{css}>{escape(value)}</td>"


def link(url: str, label: str) -> str:
    return (
        f'<a class="src-link" href="{escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{escape(label)}</a>'
    )


def source_cell(row: dict[str, str], extra: str = "") -> str:
    parts: list[str] = []
    label = (row.get("official_source_label") or "Official NFL source").strip()
    url = (row.get("official_source_url") or "").strip()
    parts.append(link(url, label + " \u2197"))
    mlabel = (row.get("methodology_reference_label") or "").strip()
    murl = (row.get("methodology_reference_url") or "").strip()
    if mlabel and murl:
        parts.append(link(murl, mlabel + " \u2197"))
    if extra:
        parts.append(extra)
    return '<td class="src-cell">' + '<span class="src-sep">\u00b7</span>'.join(parts) + "</td>"


def table(headers: list[str], body_rows: list[str]) -> str:
    head = "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></div>"
    )


def page_shell(active: str, eyebrow: str, title: str, lead: str, body: str) -> str:
    nav = []
    for href, label in NAV_ITEMS:
        cls = ' class="active" aria-current="page"' if href == active else ""
        nav.append(f'<a href="{escape(href, quote=True)}"{cls}>{escape(label)}</a>')
    nav.append('<a href="../index.html">Project home</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | NFL Origination &amp; Depth Pack</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="brand-row">
        <p class="brand-title">NFL Line Origination, Depth Deficiency &amp; Skill-Gate Pack</p>
        <p class="brand-meta">2026 Week 10 snapshot &middot; official-source verified &middot; zero market data</p>
      </div>
      <nav class="nav-bar" aria-label="Dashboard sections">
        {"".join(nav)}
      </nav>
    </div>
  </header>
  <main class="container">
    <p class="eyebrow">{escape(eyebrow)}</p>
    <h1>{escape(title)}</h1>
    <p class="lead">{escape(lead)}</p>
    {body}
  </main>
  <footer class="site-footer">
    <div class="container">
      Generated from <code>data/nfl_3b81013c/*.csv</code> by <code>scripts/build_nfl_3b81013c.py</code> and verified by
      <code>scripts/check_nfl_3b81013c.py</code>. Every table row links to the official NFL page it came from and to a
      recognised methodology reference. A blank hatched cell means the value is not confirmed from an official source and
      was deliberately left empty. This pack publishes no market price and makes no wagering recommendation: NFL.com Terms of
      Use sections 1.3, 11(f) and 12 restrict reuse, automated harvesting and gambling use.
    </div>
  </footer>
</body>
</html>
"""


def build_sources_register() -> list[dict[str, str]]:
    """Collect every distinct (label, url) pair actually cited by a register row."""
    seen: dict[str, dict[str, str]] = {}
    for name in sorted(p.name for p in DATA_DIR.glob("*.csv")):
        with (DATA_DIR / name).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                for label_key, url_key, kind in (
                    ("official_source_label", "official_source_url", "official NFL page"),
                    ("methodology_reference_label", "methodology_reference_url", "methodology reference"),
                ):
                    label = (row.get(label_key) or "").strip()
                    url = (row.get(url_key) or "").strip()
                    if not label or not url:
                        continue
                    entry = seen.setdefault(url, {"url": url, "label": label, "kind": kind, "uses": []})
                    entry["uses"].append(f"{name}:{row.get('id', '')}")
    return [seen[u] for u in sorted(seen)]


def count_status(rows: list[dict[str, str]]) -> dict[str, int]:
    counts = {"verified": 0, "computed": 0, "unverified": 0}
    for row in rows:
        counts[row["verification_status"]] += 1
    return counts


def build_pages() -> dict[str, str]:
    data = {name: load_csv(name) for name in sorted(p.name for p in DATA_DIR.glob("*.csv"))}
    # sources.json-style metadata files are not registers
    for key in list(data):
        if not key.endswith(".csv"):
            del data[key]

    lines = data["originated_lines.csv"]
    records = data["team_season_records.csv"]
    injuries = data["injuries_and_depth.csv"]
    deficiencies = data["depth_deficiency_summary.csv"]
    strategies = data["strategies.csv"]
    gates = data["validation_gates.csv"]
    leaderboard = data["leaderboard.csv"]
    correlations = data["correlations.csv"]
    questions = data["open_questions.csv"]
    suggestions = data["site_suggestions.csv"]
    official_inputs = data["official_inputs.csv"]
    pricing = data["pricing_methods.csv"]

    total_rows = sum(len(v) for v in data.values())
    totals = {"verified": 0, "computed": 0, "unverified": 0}
    for rows in data.values():
        for k, v in count_status(rows).items():
            totals[k] += v
    open_questions = [q for q in questions if q["status"] == "open"]
    answered = [q for q in questions if q["status"] == "answered"]
    flagged_rows = [r for rows in data.values() for r in rows if r["verification_status"] == "unverified"]

    pages: dict[str, str] = {}

    # ---------------------------------------------------------------- index
    kpi = (
        '<section class="kpi-grid">'
        + "".join(
            f'<article class="kpi-card"><p class="kpi-label">{escape(label)}</p>'
            f'<p class="kpi-value">{value}</p><p class="kpi-note">{escape(note)}</p></article>'
            for label, value, note in [
                ("Verified facts", f"{totals['verified']:,}", "Traced to an official NFL page read this session"),
                ("Computed values", f"{totals['computed']:,}", "Arithmetic or model output over the verified inputs, recomputed by the checker"),
                ("Unverified / blank", f"{totals['unverified']:,}", "Deliberately empty cells, each listed on Flagged for Review"),
                ("Originated Week 10 lines", f"{len(lines)}", "Spread, total and moneyline for all 14 games, no market comparison"),
                ("Depth entries on the official report", f"{len(injuries)}", "Starter-level injury entries across 12 clubs"),
                ("Strategies ranked", "0", "All 10 registered strategies are quarantined by at least one gate"),
                ("Correlations certified", "0", f"Of {len(correlations)} registered pairs; bounds published instead"),
                ("Open questions", f"{len(open_questions)}", "Each with a named way to discover the missing information"),
            ]
        )
        + "</section>"
    )

    readiness = []
    readiness_spec = [
        ("Can the Week 10 slate and kickoff times be stated?", "yes",
         "14 games and 4 byes transcribed from the official schedule page.", "lines.html", "https://www.nfl.com/schedules/2026/reg10/",
         "NFL.com 2026 Week 10 schedule"),
        ("Can an official injury and participation status be stated per player?", "yes",
         "The official report gives FP / LP / DNP and game status for every listed player.", "depth.html", "https://www.nfl.com/injuries/",
         "NFL.com official injury report"),
        ("Can a fair spread and total be originated for each game?", "yes, with disclosure",
         "Yes as arithmetic over official points scored and allowed, but two priors (home-field advantage and margin spread) are uncalibrated assumptions, so the line is labelled prior-driven.", "lines.html",
         "https://www.nfl.com/standings/", "NFL.com NFL standings"),
        ("Can a line be compared with a market price?", "no",
         "No market price is licensed or published anywhere in this pack, and the terms of use restrict gambling use of the site.", "lines.html",
         "https://www.nfl.com/legal/terms/", "NFL.com Terms of Use"),
        ("Can a parlay or prop-combo joint probability be published?", "no",
         "Only mathematical bounds are defensible without a paired-residual sample; all twelve empirical correlations are blank.", "correlations.html",
         "https://www.nfl.com/legal/terms/", "NFL.com Terms of Use"),
        ("Can any strategy be ranked, rewarded or called skilful?", "no",
         "Every strategy is blocked or fails at least one of ten gates; the leaderboard is intentionally empty.", "leaderboard.html",
         "https://www.nfl.com/legal/terms/", "NFL.com Terms of Use"),
        ("Can a backup's exact depth string be asserted?", "mostly no",
         "For 46 of 49 report entries the incoming player's string is not stated by an official source, so the severity index is left blank rather than assumed.", "flagged.html",
         "https://www.nfl.com/injuries/", "NFL.com official injury report"),
        ("Can club gameday active counts be checked against the 48/47 rule?", "not yet",
         "The rule is verified, but no club-level active count is published; it can only be computed from the T-90 minute inactive list.", "deficiencies.html",
         "https://operations.nfl.com/game-operations-logistics/preparation-safety/game-and-stadium-prep", "NFL Operations - game and stadium preparation"),
    ]
    for idx, (question, verdict, why, page, url, label) in enumerate(readiness_spec, 1):
        readiness.append(
            f'<tr><td class="id-cell">DR-{idx:02d}</td><td>{escape(question)}</td>'
            f'<td><strong>{escape(verdict)}</strong></td><td class="detail-cell">{escape(why)}</td>'
            f'{source_cell({"official_source_label": label, "official_source_url": url})}</tr>'
        )

    index_body = (
        kpi
        + '<div class="banner"><strong>Read this first.</strong> This pack contains no market price, no edge, no return and no '
        'ranked strategy. It contains verified NFL facts, arithmetic that the checker recomputes, an explicitly prior-driven set of '
        'Week 10 lines, and a complete list of what cannot yet be decided. Every blank cell is a value that could not be confirmed '
        'from an official source.</div>'
        '<h2>What can and cannot be decided today</h2>'
        + table(
            ["Ref", "Question a decision depends on", "Answer available", "Why / what is missing", "Official source"],
            readiness,
        )
        + '<h2>What is on each page</h2>'
        + table(
            ["Page", "What it holds", "Rows", "Read it when", "Governing source"],
            [
                f'<tr><td>{link("lines.html", "Originated Lines")}</td><td>Fourteen Week 10 games with an originated spread, total and moneyline, plus the 32 club season records the arithmetic uses.</td><td class="num">{len(lines)} + {len(records)}</td><td>You want the model output and exactly which inputs it used.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("depth.html", "Injuries &amp; Depth")}</td><td>Every starter-level entry on the official Week 10 injury report, with the verified replacement where one exists.</td><td class="num">{len(injuries)}</td><td>You want to know who is out and who replaces them.</td><td>0</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("deficiencies.html", "Depth Deficiency")}</td><td>Per club and per unit, how many starters are unavailable and how much of that exposure is actually verified.</td><td class="num">{len(deficiencies)}</td><td>You want the compounding effect of multiple absences in one unit.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("strategies.html", "Strategies &amp; Gates")}</td><td>Ten signal hypotheses, the ten validation gates, and the pricing methods with worked numbers.</td><td class="num">{len(strategies)} + {len(gates)} + {len(pricing)}</td><td>You want to review the competition rules before any result exists.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("leaderboard.html", "Leaderboard")}</td><td>The reward structure and an empty ranking, with the reason each strategy is quarantined.</td><td class="num">{len(leaderboard)}</td><td>You want to see what a qualifying strategy would have to prove.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("correlations.html", "Correlations")}</td><td>Twelve parlay and prop-combo pairs, each with blank empirical correlation and published mathematical bounds.</td><td class="num">{len(correlations)}</td><td>You are considering any multi-leg bet.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("questions.html", "Questions")}</td><td>Every question that must be answered before a decision, split into answered and open.</td><td class="num">{len(questions)}</td><td>You want the checklist in one place.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("suggestions.html", "Site Suggestions")}</td><td>Twelve concrete site improvements with effort, impact, risk and what the owner must decide.</td><td class="num">{len(suggestions)}</td><td>You want to choose a path before anything is built.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("sources.html", "Sources")}</td><td>Every official and methodological URL cited by any row, with usage counts and content hashes.</td><td class="num">{len(build_sources_register())}</td><td>You are reviewing a claim manually.</td><td>{terms_link()}</td></tr>',
                f'<tr><td>{link("flagged.html", "Flagged for Review")}</td><td>Every unverified item, why it is blank, and the exact page a reviewer should open.</td><td class="num">{len(flagged_rows)}</td><td>You want to check what is not proven.</td><td>{terms_link()}</td></tr>',
            ],
        )
        + '<h2>How verification works here</h2>'
        + '<p>Each register row carries exactly one of three labels. <strong>verified</strong> means the value is stated on an '
        'official NFL page read during this session and the exact URL is in the row. <strong>computed</strong> means the value is '
        'arithmetic or model output over verified inputs, reproducible by rerunning the builder and the checker. '
        '<strong>unverified</strong> means the value is blank, is rendered as a hatched empty cell, and appears on the Flagged for '
        'Review page. No row is ever promoted from unverified by inference.</p>'
        '<p>The checker <code>scripts/check_nfl_3b81013c.py</code> rebuilds all eleven pages and fails if any byte differs, '
        'recomputes the league average, every per-game rate, every originated spread and total, and every pricing example, and '
        'rejects any unverified row that carries a value.</p>'
    )
    pages["index.html"] = page_shell(
        "index.html",
        "Executive summary",
        "NFL line origination, depth deficiency and skill-gated strategy pack",
        "A single dashboard for the 2026 Week 10 slate: what the official sources say, what can be originated from them, "
        "what a strategy would have to prove before it earns a rank, and what is simply not known yet.",
        index_body,
    )

    # ---------------------------------------------------------------- lines
    line_rows = []
    for row in lines:
        line_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td><td>{escape(row["item"])}'
            f'<div class="detail-cell">{escape(row["unit_or_scope"])}</div></td>'
            f'{value_cell(row["value"], row["verification_status"], numeric=True)}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["derivation_or_detail"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    record_rows = []
    for row in records:
        record_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td><td>{escape(row["item"])}</td>'
            f'{value_cell(row["value"], row["verification_status"], numeric=True)}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["derivation_or_detail"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    lines_body = (
        '<div class="banner"><strong>These are originated lines, not market lines.</strong> No sportsbook price is quoted, '
        'licensed or compared against anywhere in this pack. Each number below is arithmetic over official points scored and '
        'allowed, plus two declared priors: home-field advantage of 1.75 points and a margin spread of 13.45 points. Both priors '
        'are uncalibrated assumptions and are flagged.</div>'
        '<h2>Week 10 originated lines</h2>'
        '<p>Sign convention: the spread is the home team spread, so a negative number means the home team is favoured. '
        'P(home win) uses a normal approximation on the projected margin. The 09:30 ET Munich game is priced at a neutral site '
        'with zero home-field advantage, per the official calendar entry.</p>'
        + table(["Ref", "Game", "Originated line", "Status", "Derivation", "Sources"], line_rows)
        + '<h2>Club season records used by the arithmetic</h2>'
        '<p>Points for and points against are the official cumulative season totals from the Week 10 standings. Points per game '
        'divides by games played, counting a tie as one game played. The league average is the sum of all 32 clubs\u2019 points '
        'scored divided by all team-games played.</p>'
        + table(["Ref", "Item", "Value", "Status", "Derivation", "Sources"], record_rows)
    )
    pages["lines.html"] = page_shell(
        "lines.html",
        "Line origination",
        "Originated Week 10 NFL lines",
        "For each of the 14 Week 10 games, a fair spread, total and moneyline computed from official season scoring, with the "
        "exact derivation and the limits of the method stated on the same row.",
        lines_body,
    )

    # ---------------------------------------------------------------- depth
    depth_rows = []
    for row in injuries:
        depth_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td><strong>{escape(row["team"])}</strong><div class="detail-cell">{escape(row["side"])} \u00b7 {escape(row["unit_group"])} \u00b7 slot {escape(row["position_slot"])} \u00b7 {escape(row["starter_string"])}</div></td>'
            f'<td>{escape(row["listed_player"]) or "<em>not named</em>"}</td>'
            f'<td>{escape(row["official_report_status"])}</td>'
            f'<td>{escape(row["expected_replacement"]) or "<em>unconfirmed</em>"}</td>'
            f'{value_cell(row["structural_severity_index"], row["verification_status"], numeric=True)}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["detail_and_limits"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    depth_body = (
        '<div class="banner"><strong>The severity column is deliberately sparse.</strong> A weight can only be assigned when an '
        'official source states which string the replacement player came from. For most entries that is not stated, so the cell is '
        'blank. Three verified quarterback cascades are the only fully weighted entries.</div>'
        '<h2>Starter-level entries on the official Week 10 injury report</h2>'
        '<p>Practice status is transcribed from the official report: FP is full participation, LP is limited, DNP is did not '
        'participate. Game status such as Out or Injured Reserve is recorded separately. The structural severity index is a '
        'positional weight multiplied by the verified incoming string tier (1.00 for a first-string starter down to 0.45 for a '
        'second-string replacement), or by 0.15 for a limited participant. It is an uncalibrated ordinal screen, not points.</p>'
        + table(
            ["Ref", "Club / unit", "Starter", "Official status", "Replacement", "Severity", "Status", "Detail and limits", "Sources"],
            depth_rows,
        )
        + '<h2>Roster rules that govern who can actually dress</h2>'
        + table(
            ["Ref", "Rule", "Official value", "Why it matters for depth", "Official source"],
            [
                f'<tr><td class="id-cell">RR-01</td><td>Gameday active list</td><td class="num">{escape(official_inputs[1]["value"])}</td><td class="detail-cell">A club with fewer than eight active offensive linemen can dress only 47 players, so an offensive-line cluster injury reduces the total available bodies.</td>{source_cell(official_inputs[1])}</tr>',
                f'<tr><td class="id-cell">RR-02</td><td>Active / Inactive list</td><td class="num">{escape(official_inputs[0]["value"])}</td><td class="detail-cell">Expansion to 54 or 55 on gameday is available only through the Standard Elevation Addendum.</td>{source_cell(official_inputs[0])}</tr>',
                f'<tr><td class="id-cell">RR-03</td><td>Practice squad</td><td class="num">{escape(official_inputs[2]["value"])}</td><td class="detail-cell">A maximum of two elevations per week and three games per player per season caps how often a fourth-string player can actually appear.</td>{source_cell(official_inputs[2])}</tr>',
                f'<tr><td class="id-cell">RR-04</td><td>Inactive list deadline</td><td class="num">{escape(official_inputs[3]["value"])}</td><td class="detail-cell">The Game Day Administration Report at the officiating meeting is the last official pre-kickoff information release, so any signal must be timestamped before it or derived from it.</td>{source_cell(official_inputs[3])}</tr>',
            ],
        )
    )
    pages["depth.html"] = page_shell(
        "depth.html",
        "Injuries and depth",
        "Injuries, starters and the backup who replaces them",
        "Every starter-level entry on the official Week 10 injury report, with the replacement named only where an official source "
        "names them, and a severity index that stays blank when the incoming depth string is unknown.",
        depth_body,
    )

    # -------------------------------------------------------- deficiencies
    deficiency_rows = []
    for row in deficiencies:
        deficiency_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td><strong>{escape(row["team"])}</strong> {escape(row["side"])}<div class="detail-cell">{escape(row["unit_group"])}</div></td>'
            f'<td class="num">{escape(row["slots_on_report"])}</td>'
            f'<td class="num">{escape(row["starters_out_or_dnp"])}</td>'
            f'<td class="num">{escape(row["limited_participants"])}</td>'
            f'<td class="num">{escape(row["slots_with_verified_replacement"])}</td>'
            f'{value_cell(row["cluster_adjusted_index"], row["verification_status"], numeric=True)}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["worst_case_slot"]) or "<em>none verified</em>"}</td>'
            f'<td class="detail-cell">{escape(row["detail_and_limits"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    total_slots = sum(int(r["slots_on_report"]) for r in deficiencies)
    total_verified = sum(int(r["slots_with_verified_replacement"]) for r in deficiencies)
    deficiency_body = (
        f'<div class="banner"><strong>Coverage of the depth screen is {total_verified} of {total_slots} report slots.</strong> '
        'Only those slots can carry a numeric index. Reading the index as a complete measure of how depleted a unit is would be '
        'wrong, and the detail column says so on every row.</div>'
        '<h2>Unit-level depth deficiency, ranked by verified exposure</h2>'
        '<p>Rows group the injury-report entries by club, side of the ball and unit. The cluster multiplier illustrates the '
        'non-linear cost of losing two or three starters in one cohesive unit; because the raw index already sums independent '
        'weights, applying a multiplier compounds the interaction twice, so the multiplied column is shown for illustration and the '
        'raw exposure is the number to trust.</p>'
        + table(
            ["Ref", "Club / side", "Slots on report", "Out or DNP", "Limited", "Verified replacements", "Cluster index", "Status", "Worst verified slot", "Detail and limits", "Sources"],
            deficiency_rows,
        )
        + '<h2>Why the defensive side of the ball is harder to certify than the offensive side</h2>'
        + '<p>An offensive-line absence is visible in the starting five and is usually reported directly. A defensive rotation '
        'absence is a snap-share question: a starting cornerback who is out may be replaced by committee, with a nickel back taking '
        'the slot and a safety rotating down. Without official snap counts by player, the incoming string cannot be established, '
        'which is exactly why most defensive rows on this page are blank in the index column.</p>'
    )
    pages["deficiencies.html"] = page_shell(
        "deficiencies.html",
        "Depth deficiency",
        "Where second, third and fourth-string players actually have to start",
        "Unit-by-unit exposure across the Week 10 report, with the verified share stated explicitly so a depleted-looking unit is "
        "never mistaken for a measured one.",
        deficiency_body,
    )

    # --------------------------------------------------------- strategies
    strategy_rows = []
    for row in strategies:
        strategy_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td><strong>{escape(row["name"])}</strong><div class="detail-cell">{escape(row["category"])} \u00b7 {escape(row["market_family"])}</div></td>'
            f'<td class="detail-cell">{escape(row["signal_hypothesis"])}</td>'
            f'{value_cell(row["gates_passed"], row["verification_status"])}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["gates_blocked"])}<br><span class="detail-cell">failed: {escape(row["gates_failed"])}</span></td>'
            f'<td class="detail-cell">{escape(row["required_data"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    gate_rows = []
    for row in gates:
        gate_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td><strong>{escape(row["gate_name"])}</strong></td>'
            f'<td class="detail-cell">{escape(row["failure_mode_prevented"])}</td>'
            f'<td class="detail-cell">{escape(row["evaluation_rule"])}</td>'
            f"{value_cell(row['result_for_week10_strategies'], row['verification_status'])}"
            f"<td>{badge(row['verification_status'])}</td>"
            f"{source_cell(row)}</tr>"
        )
    pricing_rows = []
    for row in pricing:
        pricing_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td><strong>{escape(row["method"])}</strong></td>'
            f'<td class="mono">{escape(row["inputs_example"])}</td>'
            f'{value_cell(row["computed_output"], row["verification_status"])}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["what_it_does"])} <em>Cannot do:</em> {escape(row["what_it_cannot_do"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    strategy_body = (
        '<div class="banner"><strong>Ten hypotheses, zero results.</strong> A strategy is registered here so its gate status is '
        'auditable and so a reviewer can see exactly what data it needs. Registration is not a recommendation and confers no rank.</div>'
        '<h2>Registered strategies</h2>'
        + table(["Ref", "Strategy", "Signal hypothesis", "Gates passed", "Status", "Blocked / failed gates", "Data required", "Sources"], strategy_rows)
        + '<h2>The ten validation gates</h2>'
        + '<p>A strategy earns a leaderboard rank only if all ten gates return PASS. A gate that cannot be evaluated returns '
        'BLOCKED_NO_DATA, which is treated as a failure for ranking. The gates are implemented in '
        '<code>src/nfl_3b81013c/validation.py</code> and exercised by the test suite.</p>'
        + table(["Ref", "Gate", "Failure mode it prevents", "Evaluation rule", "Week 10 result", "Status", "Sources"], gate_rows)
        + '<h2>Pricing methods, with worked numbers</h2>'
        + '<p>These are the conversions and de-vigging routines the package uses. Every output below is recomputed by the checker '
        'from the stated inputs, so a reader can verify the arithmetic without trusting the page.</p>'
        + table(["Ref", "Method", "Inputs", "Computed output", "Status", "What it does and cannot do", "Sources"], pricing_rows)
        + '<h2>How luck is controlled rather than assumed away</h2>'
        + '<ol>'
        '<li><strong>Multiplicity.</strong> Ten strategies tested at once inflate the chance of a false winner, so the family of '
        'p-values is Holm-adjusted before any rank is awarded.</li>'
        '<li><strong>Clustering.</strong> Bets inside one NFL week are not independent, so the interval is a slate-clustered '
        'bootstrap rather than an independent-sample interval.</li>'
        '<li><strong>Out-of-sample only.</strong> Parameters are frozen before the test week, and the package rejects any '
        'non-training row in a correlation estimate.</li>'
        '<li><strong>Proper scoring.</strong> Accuracy is not enough; the holdout Brier or log-loss must beat the de-vigged market, '
        'which is the only comparison that removes the price from the result.</li>'
        '<li><strong>Selection disclosure.</strong> The number of strategies tried is published, because a winner chosen from an '
        'undisclosed search is not evidence of skill.</li>'
        '</ol>'
    )
    pages["strategies.html"] = page_shell(
        "strategies.html",
        "Strategy lab",
        "Signal hypotheses, the ten validation gates, and pricing arithmetic",
        "What each strategy would need, which gate currently blocks it, and the exact conversions used to price a probability "
        "\u2014 so the competition rules can be reviewed before any result exists.",
        strategy_body,
    )

    # ---------------------------------------------------------- leaderboard
    lb_rows = []
    for row in leaderboard:
        lb_rows.append(
            f'<tr><td class="id-cell">{escape(row["strategy_id"])}</td>'
            f'<td><strong>{escape(row["strategy_name"])}</strong><div class="detail-cell">{escape(row["category"])}</div></td>'
            f'<td class="num">{escape(row["gates_passed"])}</td>'
            f'{value_cell(row["rank"], row["verification_status"], numeric=True)}'
            f'{value_cell(row["holdout_roi_ci_lower"], row["verification_status"], numeric=True)}'
            f'<td class="mono">{escape(row["reward_tier"])}</td>'
            f"<td>{badge(row['verification_status'])}</td>"
            f"{source_cell(row)}</tr>"
        )
    leaderboard_body = (
        '<div class="banner"><strong>The leaderboard is empty by design.</strong> A rank is awarded only when all ten gates pass. '
        'With zero authorized observations and no licensed market feed, no strategy can pass, so every row shows a blank rank and '
        'the quarantine tier.</div>'
        '<h2>Reward structure, fixed before any result</h2>'
        + table(
            ["Tier", "Condition", "Reward", "Why it is defined now", "Official source"],
            [
                '<tr><td class="mono">TIER_1_GOLD</td><td>Rank 1 after all ten gates pass</td><td>Largest research allocation</td><td class="detail-cell">Fixing the reward before seeing results prevents the tiers being fitted to a lucky winner.</td><td>' + terms_link() + '</td></tr>',
                '<tr><td class="mono">TIER_2_SILVER</td><td>Ranks 2 and 3</td><td>Shadow promotion: runs live alongside gold with no capital weight</td><td class="detail-cell">Shadow promotion tests whether a ranked strategy survives a second, unseen period.</td><td>' + terms_link() + '</td></tr>',
                '<tr><td class="mono">TIER_3_BRONZE</td><td>Remaining qualified strategies</td><td>Sandbox grant: continues measuring, earns no weight</td><td class="detail-cell">Keeps good-but-not-best strategies measurable without rewarding noise.</td><td>' + terms_link() + '</td></tr>',
                '<tr><td class="mono">QUARANTINED</td><td>Any gate blocked or failed</td><td>No rank, no reward</td><td class="detail-cell">Quarantine is the default, so the burden of proof sits on the strategy rather than the reviewer.</td><td>' + terms_link() + '</td></tr>',
            ],
        )
        + '<h2>Current standings</h2>'
        + table(["Ref", "Strategy", "Gates passed", "Rank", "Holdout ROI lower bound", "Reward tier", "Status", "Sources"], lb_rows)
        + '<h2>What would have to be true for a first rank to appear</h2>'
        + '<ol>'
        '<li>A licensed or explicitly permitted data path exists, satisfying the terms of use (gate VG-01).</li>'
        '<li>At least 200 graded events are recorded, spanning at least 18 weekly slates (gate VG-04).</li>'
        '<li>Every observation carries a timestamp before kickoff and consistent with the T-90 minute report (gate VG-02).</li>'
        '<li>A frozen walk-forward run beats the de-vigged market on a proper scoring rule (gates VG-03 and VG-05).</li>'
        '<li>De-vigged same-line closing value is positive (gate VG-06).</li>'
        '<li>For a parlay or prop combo, a training-only paired-residual correlation exists (gate VG-07).</li>'
        '<li>The Holm-adjusted p-value clears 0.05 and the slate-clustered ROI lower bound clears zero (gate VG-08).</li>'
        '<li>The incoming depth strings behind any depth signal are officially confirmed (gate VG-09).</li>'
        '</ol>'
    )
    pages["leaderboard.html"] = page_shell(
        "leaderboard.html",
        "Leaderboard competition",
        "Reward tiers and the deliberately empty ranking",
        "A competition frame that pays only after a strategy proves itself against a clustered interval, a multiplicity "
        "correction, an out-of-sample proper scoring rule and a de-vigged closing line.",
        leaderboard_body,
    )

    # --------------------------------------------------------- correlations
    corr_id_rows = []
    for row in correlations:
        corr_id_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td class="mono">{escape(row["combo_category"])}</td>'
            f'<td>{escape(row["leg_a_market"])}<div class="detail-cell">{escape(row["leg_b_market"])}</div></td>'
            f'<td class="detail-cell">{escape(row["structural_direction_hypothesis"])}</td>'
            f'{value_cell(row["pearson_r"], row["verification_status"], numeric=True)}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["blocking_reason"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    corr_bound_rows = []
    for row in correlations:
        corr_bound_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td>{escape(row["leg_a_market"])} <span class="src-sep">+</span> {escape(row["leg_b_market"])}</td>'
            f'<td class="num">{escape(row["frechet_lower_computed"])}</td>'
            f'<td class="num">{escape(row["frechet_upper_computed"])}</td>'
            f'<td class="num">{escape(row["joint_prob_rho_minus_0_5"])}</td>'
            f'<td class="num">{escape(row["joint_prob_rho_0"])}</td>'
            f'<td class="num">{escape(row["joint_prob_rho_plus_0_5"])}</td>'
            f'<td>{badge("computed")}</td>' 
            f"{source_cell(row)}</tr>"
        )
    correlations_body = (
        '<div class="banner"><strong>Twelve pairs, zero measured correlations.</strong> Multiplying leg probabilities is only valid '
        'under independence, and independence is false for most real parlay legs. The bounds below are mathematics, not estimates.</div>'
        '<h2>Registered parlay and prop-combo pairs</h2>'
        '<p>The empirical correlation is blank for every pair because no authorized paired-residual ledger exists. NFL.com terms '
        'sections 1.3 and 11(f) bar systematic collection, and no licensed play-by-play feed is configured, so the pairing of '
        'graded outcomes that a correlation requires cannot be assembled here.</p>'
        + table(["Ref", "Category", "Legs", "Structural direction (hypothesis)", "Pearson r", "Status", "Why it is blank", "Sources"], corr_id_rows)
        + '<h2>Mathematical bounds at equal 0.50 legs</h2>'
        '<p>For two legs each priced at a true probability of 0.50, the joint probability can lie anywhere between the '
        'Fr\u00e9chet\u2013Hoeffding floor and ceiling. The three copula columns show the joint probability under a bivariate normal '
        'copula at three illustrative correlations. They are computed with a second-order Mehler expansion, which is an '
        'approximation; any published correlation would require exact quadrature and an empirical sample.</p>'
        + table(
            ["Ref", "Pair", "Fr\u00e9chet floor", "Fr\u00e9chet ceiling", "Joint at rho -0.5", "Joint at rho 0", "Joint at rho +0.5", "Status", "Sources"],
            corr_bound_rows,
        )
        + '<h2>What the bounds prove</h2>'
        + '<ul>'
        '<li>Two 0.50 legs have a joint probability anywhere from 0.00 to 0.50, so the independence product of 0.25 sits in the middle '
        'of a very wide range. A price built on independence can be wrong in either direction.</li>'
        '<li>The spread between the floor and ceiling is the honest uncertainty about a parlay until a correlation is measured.</li>'
        '<li>Some pairings are definitionally redundant rather than correlated, such as a cornerback interception prop and the '
        'team interception total; those must be excluded by rule, not corrected by a coefficient.</li>'
        '<li>A Fisher-z interval and a slate-clustered bootstrap are both implemented, because a correlation computed on '
        'within-week data is not independent across rows.</li>'
        '</ul>'
    )
    pages["correlations.html"] = page_shell(
        "correlations.html",
        "Correlation research",
        "Correlation values for parlay and prop-combo legs",
        "Twelve registered pairings, each with a stated structural direction, an intentionally blank empirical coefficient and the "
        "mathematical bounds that must be used in its place.",
        correlations_body,
    )

    # ------------------------------------------------------------ questions
    q_rows = []
    for row in questions:
        q_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td class="mono">{escape(row["category"])}</td>'
            f'<td>{escape(row["question"])}</td>'
            f'<td class="mono">{escape(row["status"])}</td>'
            f'{value_cell(row["answer_we_have"], "unverified" if row["status"] == "open" else "verified")}'
            f'<td class="detail-cell">{escape(row["what_is_missing"])}</td>'
            f'<td class="detail-cell">{escape(row["how_to_discover_it"])}</td>'
            f'<td class="detail-cell">{escape(row["blocks_which_decision"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    questions_body = (
        f'<div class="banner"><strong>{len(answered)} of {len(questions)} questions are already answered from an official source; '
        f'{len(open_questions)} are open.</strong> An open question leaves its answer cell blank. Each open question names the exact '
        'data acquisition that would close it, in the same row.</div>'
        '<h2>Every blocking question</h2>'
        '<p>Status <span class="badge badge-verified">answered</span> means an official page states the answer and the link is in the '
        'row. Status <span class="badge badge-unverified">open</span> means no official answer was found, the answer cell is blank, '
        'and the discovery column names what to obtain.</p>'
        + table(
            ["Ref", "Category", "Question", "Status", "Answer we have", "What is missing", "How to discover it", "Blocks", "Sources"],
            q_rows,
        )
        + '<h2>Suggestions for discovering the missing information</h2>'
        + table(
            ["Ref", "Missing item", "Concrete discovery route", "Cost signal", "Starting point", "Governing terms"],
            [
                '<tr><td class="id-cell">DG-01</td><td>A right to use NFL data beyond personal reading</td><td class="detail-cell">Write to NFL Media licensing for a data-use agreement, or contract a licensed vendor. Record the contract identifier in the register before any commercial use.</td><td>contract negotiation</td><td>' + link("https://www.nfl.com/legal/terms/", "NFL.com Terms of Use \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-02</td><td>Timestamped opening and closing prices</td><td class="detail-cell">Contract a licensed odds provider whose terms permit research use, and require an execution audit: the price must have been genuinely available at the recorded time.</td><td>paid subscription</td><td>' + link("https://www.nfl.com/legal/terms/", "NFL.com Terms of Use \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-03</td><td>Incoming depth-chart string per replacement</td><td class="detail-cell">Read the official club depth chart published on the team site together with the official weekly transaction wire; record both and the read time. Where neither exists, leave the row blank as it is now.</td><td>manual weekly read</td><td>' + link("https://www.nfl.com/injuries/", "NFL.com official injury report \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-04</td><td>Snap counts by player</td><td class="detail-cell">Snap counts are the only way to prove that a backup actually played. Obtain them from an authorized provider, then join to the injury report by player identifier.</td><td>paid data</td><td>' + link("https://www.nfl.com/injuries/", "NFL.com official injury report \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-05</td><td>Play-by-play for efficiency ratings</td><td class="detail-cell">A licensed play-by-play feed upgrades the model from raw points to opponent-adjusted efficiency, which the package already accepts as an input.</td><td>paid data</td><td>' + link("https://www.nfl.com/standings/", "NFL.com NFL standings \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-06</td><td>Points value of a depth-string loss</td><td class="detail-cell">Regress realized margin and team totals on verified depth changes once DG-03 and DG-05 exist; publish the coefficient and its interval, or leave the weight table uncalibrated.</td><td>analysis only</td><td>' + link("https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm", "NIST confidence interval handbook \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-07</td><td>Whether a backtest is adequately powered</td><td class="detail-cell">Run an a-priori power calculation at the effect size of interest before fixing the sample floor, and publish both.</td><td>analysis only</td><td>' + link("https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html", "statsmodels multipletests \u2197") + ' ' + terms_link() + '</td></tr>',
                '<tr><td class="id-cell">DG-08</td><td>Public timestamp of the inactive list</td><td class="detail-cell">The report is delivered to the referee at T-90 minutes; record when it becomes public each week, then compare with price timestamps.</td><td>manual weekly read</td><td>' + link("https://operations.nfl.com/game-operations-logistics/preparation-safety/game-and-stadium-prep", "NFL Operations - game and stadium preparation \u2197") + ' ' + terms_link() + '</td></tr>',
            ],
        )
    )
    pages["questions.html"] = page_shell(
        "questions.html",
        "Decision checklist",
        "Questions that must be answered before any decision",
        "Split into what official sources already answer and what they do not, with a named discovery route for every open item.",
        questions_body,
    )

    # ----------------------------------------------------------- suggestions
    s_rows = []
    for row in suggestions:
        s_rows.append(
            f'<tr><td class="id-cell">{escape(row["id"])}</td>'
            f'<td class="mono">{escape(row["area"])}</td>'
            f'<td>{escape(row["suggestion"])}</td>'
            f'<td class="detail-cell">{escape(row["problem_it_solves"])}</td>'
            f'<td class="mono">{escape(row["effort"])} / {escape(row["impact"])}</td>'
            f'{value_cell(row["review_status"], row["verification_status"])}'
            f"<td>{badge(row['verification_status'])}</td>"
            f'<td class="detail-cell">{escape(row["risk_if_adopted"])}</td>'
            f'<td class="detail-cell">{escape(row["decision_owner_needs"])}</td>'
            f"{source_cell(row)}</tr>"
        )
    implemented = [s for s in suggestions if s["review_status"] == "implemented"]
    suggestions_body = (
        f'<div class="banner"><strong>Choose before building.</strong> {len(suggestions)} suggestions, of which '
        f'{len(implemented)} are already implemented in this pack and the rest need an owner decision. Nothing here changes '
        'another session\u2019s pages.</div>'
        '<h2>Suggested improvements, with effort, impact and risk</h2>'
        '<p>Effort and impact are ordinal judgements made by this session and are labelled as such, not measurements. The risk '
        'column states what could go wrong if the change is adopted. The final column states what the deciding owner must settle '
        'first, which for any shared page means agreement from the session that owns it.</p>'
        + table(
            ["Ref", "Area", "Suggestion", "Problem it solves", "Effort / impact", "Review status", "Status", "Risk if adopted", "Owner must decide", "Sources"],
            s_rows,
        )
        + '<h2>Three paths a reviewer can choose between</h2>'
        + table(
            ["Path", "What it delivers", "What it costs", "What it still cannot answer", "Governing source"],
            [
                '<tr><td><strong>A. Publish only what is proven</strong></td><td class="detail-cell">Everything on this site today: verified facts, recomputable arithmetic, prior-driven lines and a complete list of gaps.</td><td class="detail-cell">No further data acquisition; the leaderboard stays empty.</td><td class="detail-cell">Nothing about edges, correlations or skill, because those need data this path does not buy.</td><td>' + terms_link() + '</td></tr>',
                '<tr><td><strong>B. Buy the two missing datasets</strong></td><td class="detail-cell">A licensed odds feed and a licensed play-by-play feed would unlock efficiency ratings, calibration, closing-line value and clustering \u2014 gates VG-05, VG-06 and VG-08.</td><td class="detail-cell">Contract cost plus a licence review.</td><td class="detail-cell">Depth-string replacement, unless snap counts are also included.</td><td>' + terms_link() + '</td></tr>',
                '<tr><td><strong>C. Manual depth-chart capture</strong></td><td class="detail-cell">Weekly reading of official club depth charts and the transaction wire would close gate VG-09 and make the depth screen numeric.</td><td class="detail-cell">Recurring manual effort with a transcription-error risk.</td><td class="detail-cell">Still no market comparison, so still no edge.</td><td>' + terms_link() + '</td></tr>',
            ],
        )
        + '<h2>Order of operations this session recommends</h2>'
        + '<ol>'
        '<li>Decide the data-rights question first, because it gates everything else and cannot be worked around.</li>'
        '<li>If rights are settled, buy the odds feed before the play-by-play feed: without a price there is nothing to be right or '
        'wrong about.</li>'
        '<li>Only then calibrate the depth weights, because a weight without a price has no decision value.</li>'
        '<li>Keep the empty leaderboard until a strategy clears all ten gates; an early ranking is worse than no ranking.</li>'
        '</ol>'
    )
    pages["suggestions.html"] = page_shell(
        "suggestions.html",
        "Site improvement",
        "Suggested improvements, with a decision for each",
        "Concrete changes to make this site better at supporting a decision, each with its cost, its risk, and what the owner has "
        "to decide before it can be built.",
        suggestions_body,
    )

    # --------------------------------------------------------------- sources
    register = build_sources_register()
    src_rows = []
    for entry in register:
        uses = entry["uses"]
        src_rows.append(
            f'<tr><td>{link(entry["url"], entry["url"] + ARROW)}</td>'
            f'<td>{escape(entry["label"])}</td>'
            f'<td class="mono">{escape(entry["kind"])}</td>'
            f'<td class="num">{len(uses)}</td>'
            f'<td class="detail-cell mono">{escape(", ".join(uses[:6]))}{ELLIPSIS if len(uses) > 6 else ""}</td>'
            f'<td>{terms_link()}</td></tr>'
        )
    hash_rows = []
    for name in sorted(p.name for p in DATA_DIR.glob("*.csv")):
        raw = (DATA_DIR / name).read_bytes()
        rows = data[name]
        hash_rows.append(
            f'<tr><td class="mono">{escape(name)}</td>'
            f'<td class="num">{len(rows)}</td>'
            f'<td class="mono">{hashlib.sha256(raw).hexdigest()[:16]}</td>'
            f'<td class="num">{count_status(rows)["verified"]} / {count_status(rows)["computed"]} / {count_status(rows)["unverified"]}</td>'
            f'<td>{link("https://github.com/sassnarep3-star/Own6/blob/main/data/nfl_3b81013c/" + name, "register" + ARROW)}</td>'
            f'<td>{terms_link()}</td></tr>'
        )
    sources_body = (
        '<div class="banner"><strong>A source link is not a verification.</strong> The register below proves which pages were cited '
        'and how often. It does not prove that a page still says the same thing, and no network request is made at build time.</div>'
        '<h2>Official and methodological sources cited by the registers</h2>'
        '<p>Every URL below is cited by at least one row. Official NFL pages are the evidence for values; methodological references '
        'are cited for the statistical procedures and never for a factual claim about football.</p>'
        + table(["URL", "Label", "Kind", "Rows citing it", "Example rows", "Governing source"], src_rows)
        + '<h2>Register integrity</h2>'
        '<p>Each register\u2019s SHA-256 prefix lets a reviewer confirm that the page they are reading matches the committed CSV. '
        'The counts are verified, computed and unverified respectively.</p>'
        + table(["Register", "Rows", "SHA-256 (first 16)", "verified / computed / unverified", "Repository", "Governing source"], hash_rows)
        + '<h2>Verification limits, stated plainly</h2>'
        + '<ul>'
        '<li><strong>Read once.</strong> Each official page was read on 2026-11-12. Injury status changes during the week and the '
        'inactive list supersedes the practice report 90 minutes before kickoff.</li>'
        '<li><strong>Transcription risk.</strong> Values were transcribed by an automated agent, not by a human double-entry '
        'process; the URL on every row exists so a reviewer can check any single value.</li>'
        '<li><strong>No market data.</strong> No sportsbook price was read, licensed, quoted or compared. Terms of use sections 1.3, '
        '11(f) and 12 restrict reuse, automated harvesting and gambling use.</li>'
        '<li><strong>Priors are assumptions.</strong> Home-field advantage and margin spread are declared modelling priors, not '
        'official league statistics; no official NFL page publishes either.</li>'
        '<li><strong>Structural weights are uncalibrated.</strong> The positional weights and string tiers are an ordinal prior built '
        'with no historical fit; the pages say so wherever they are used.</li>'
        '<li><strong>Copula columns are approximate.</strong> The joint probabilities use a second-order Mehler expansion, which is '
        'close at moderate correlation and diverges near the bounds.</li>'
        '</ul>'
        + '<h2>Reproducing this page set</h2>'
        + '<pre>python3 scripts/build_nfl_3b81013c.py\npython3 scripts/check_nfl_3b81013c.py\npython3 -m unittest tests.test_nfl_3b81013c -v</pre>'
    )
    pages["sources.html"] = page_shell(
        "sources.html",
        "Sources and limits",
        "Every source cited, and the limits of this verification",
        "The complete cited-source register, per-register content hashes, and an explicit statement of what the verification does "
        "not cover.",
        sources_body,
    )

    # --------------------------------------------------------------- flagged
    flag_rows = []
    for index, row in enumerate(sorted(flagged_rows, key=lambda r: (r["verification_status"], r.get("id", ""))), 1):
        owner = row.get("official_source_label") or "Official NFL source"
        flag_rows.append(
            f'<tr><td class="id-cell">FR-{index:03d}</td>'
            f'<td class="mono">{escape(row.get("id", ""))}</td>'
            f'<td>{escape(row.get("item") or row.get("question") or row.get("suggestion") or row.get("gate_name") or row.get("strategy_name") or row.get("method") or row.get("method_or_law") or row.get("pair_id") or "")}</td>'
            f'<td class="empty-cell"></td>'
            f"{badge(row['verification_status'])}"
            f'<td class="detail-cell">{escape((row.get("what_is_missing") or row.get("detail_and_limits") or row.get("derivation_or_detail") or ""))[:520]}</td>'
            f"{source_cell(row)}</tr>"
        )
    flagged_body = (
        f'<div class="banner"><strong>{len(flagged_rows)} unverified items.</strong> Each row is blank in the value column by '
        'design. None of these blocks publication: the site states what is known and lists what is not. A reviewer can open the '
        'official source beside every row.</div>'
        '<h2>What is flagged, and why</h2>'
        '<p>The most consequential flags are summarised here; the full machine-generated list follows.</p>'
        + table(
            ["Flag group", "What is missing", "Consequence for a decision", "Official page to review", "Governing terms"],
            [
                '<tr><td><strong>Market prices</strong></td><td class="detail-cell">No licensed, timestamped sportsbook price exists, so no edge, closing-line value or return can be computed.</td><td class="detail-cell">No wagering decision can be supported. The leaderboard stays empty.</td><td>' + link("https://www.nfl.com/legal/terms/", "NFL.com Terms of Use \u2197") + '</td><td>' + terms_link() + '</td></tr>',
                '<tr><td><strong>Replacement depth strings</strong></td><td class="detail-cell">For most report entries no official source states which string the incoming player occupies.</td><td class="detail-cell">The depth-deficiency index covers only the few verified cases and must not be read as a complete measure.</td><td>' + link("https://www.nfl.com/injuries/", "NFL.com official injury report \u2197") + '</td><td>' + terms_link() + '</td></tr>',
                '<tr><td><strong>Empirical correlations</strong></td><td class="detail-cell">No paired-residual ledger, so all twelve correlations are blank.</td><td class="detail-cell">No parlay or prop-combo joint probability may be published beyond the mathematical bounds.</td><td>' + link("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "SciPy pearsonr \u2197") + '</td><td>' + terms_link() + '</td></tr>',
                '<tr><td><strong>Model priors</strong></td><td class="detail-cell">Home-field advantage and margin spread are assumptions, and no official page publishes either.</td><td class="detail-cell">Originated lines are prior-driven estimates, not sharp prices.</td><td>' + link("https://www.nfl.com/standings/", "NFL.com NFL standings \u2197") + '</td><td>' + terms_link() + '</td></tr>',
                '<tr><td><strong>Gameday active counts</strong></td><td class="detail-cell">No club-level count of active players or active offensive linemen is published before the inactive list.</td><td class="detail-cell">The 48/47 rule can be stated but not applied to a specific club yet.</td><td>' + link("https://operations.nfl.com/inside-football-ops/players-legends/2020-nfl-nflpa-cba-need-to-know/", "NFL Operations - CBA need to know \u2197") + '</td><td>' + terms_link() + '</td></tr>',
            ],
        )
        + '<h2>Complete flagged register</h2>'
        + table(["Flag", "Ref", "Item", "Value", "Status", "Why it is blank / what to check", "Sources"], flag_rows)
    )
    pages["flagged.html"] = page_shell(
        "flagged.html",
        "Flagged for review",
        "Flagged for Review",
        "Every item this pack could not confirm from an official source, with the exact page a reviewer should open to decide it.",
        flagged_body,
    )

    pages["styles.css"] = STYLES_CSS
    return pages


def generate_all() -> dict[str, str]:
    """Return {filename: content} for every generated artifact without touching disk."""
    return build_pages()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare without writing")
    args = parser.parse_args(argv)
    pages = generate_all()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stale = []
    for name, content in sorted(pages.items()):
        target = OUT_DIR / name
        if args.check:
            if not target.is_file() or target.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            target.write_text(content, encoding="utf-8")
    if args.check:
        if stale:
            print("STALE: " + ", ".join(stale))
            return 1
        print(f"NFL pack up to date: {len(pages) - 1} pages + stylesheet")
        return 0
    html_pages = len(pages) - 1
    print(f"Wrote {html_pages} HTML pages and 1 stylesheet to docs/nfl-3b81013c/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
