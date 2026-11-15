#!/usr/bin/env python3
"""Build the consolidated NFL decision-readiness dashboard (session 6ab24751).

Renders ``docs/nfl-6ab24751/`` from ``data/nfl_6ab24751/*.csv`` and emits the
landing-page decision-readiness table fragment. The same data feeds the root
landing page, so the table on the landing page and the table here never drift.

Usage:
    python3 scripts/build_nfl_6ab24751.py            # build dashboard + fragment
    python3 scripts/build_nfl_6ab24751.py --check    # verify committed output is current
"""

from __future__ import annotations

import argparse
import html
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from nfl_6ab24751.readiness import (  # noqa: E402
    ALLOWED_STATUS,
    PackPaths,
    load_pack,
    validate,
)

DATA_DIR = os.path.join(ROOT, "data", "nfl_6ab24751")
DOCS_DIR = os.path.join(ROOT, "docs", "nfl-6ab24751")
ASSETS_DIR = os.path.join(DOCS_DIR, "assets")
ROOT_INDEX = os.path.join(ROOT, "index.html")

LANDING_BEGIN = "<!-- BEGIN DECISION-READINESS TABLE (session 6ab24751) -->"
LANDING_END = "<!-- END DECISION-READINESS TABLE (session 6ab24751) -->"

READINESS_COLS = [
    ("req_id", "ID"),
    ("category", "Category"),
    ("requirement", "Requirement"),
    ("status", "Status"),
    ("blocking_gate", "Blocking gate"),
    ("clearing_number", "Clears when"),
    ("official_source_url", "Official source"),
]

STATUS_LABEL = {
    "implemented": "Implemented",
    "implemented_limited": "Implemented (limited)",
    "blocked": "Blocked",
    "needs_review": "Needs review",
    "not_started": "Not started",
    "rejected_policy": "Rejected (policy)",
}

CSS = """
:root { color-scheme: light; --ink:#13283b; --muted:#526477; --navy:#10263c;
  --teal:#087e79; --mint:#a8f0d3; --gold:#f2b84b; --paper:#f4f7f8; --white:#fff;
  --line:#d8e1e5; --soft:#e9f2f2; --warn:#fff3d8; --warn-ink:#704500; }
* { box-sizing: border-box; }
body { margin:0; color:var(--ink); background:var(--paper); line-height:1.55;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }
a { color:var(--teal); }
.shell { width:min(1160px, calc(100% - 2rem)); margin-inline:auto; }
.topbar { background:var(--navy); color:var(--white); }
.topbar-inner { min-height:60px; display:flex; align-items:center; justify-content:space-between;
  gap:1rem; flex-wrap:wrap; }
.brand { color:var(--white); text-decoration:none; font-weight:850; letter-spacing:.09em; }
.brand span { color:var(--mint); font-size:.75rem; font-weight:650; margin-left:.4rem; }
.topnav { display:flex; flex-wrap:wrap; gap:.3rem 1.1rem; }
.topnav a { color:#e1edf1; text-decoration:none; font-size:.9rem; }
.topnav a:hover { color:var(--mint); }
main { padding:2.2rem 0 4rem; }
h1 { color:var(--navy); font-size:clamp(1.9rem, 3.4vw, 2.8rem); margin:.2rem 0 1rem; letter-spacing:-.03em; }
h2 { color:var(--navy); font-size:1.4rem; margin:2.4rem 0 .9rem; }
.lead { color:var(--muted); max-width:760px; }
.kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1rem; margin:1.4rem 0 2rem; }
.stat { padding:1rem 1.1rem; border:1px solid var(--line); border-radius:10px; background:var(--white); }
.stat .label { color:var(--muted); font-size:.74rem; font-weight:750; letter-spacing:.06em; text-transform:uppercase; }
.stat strong { display:block; color:var(--navy); font-size:1.5rem; }
.stat.warn { background:var(--warn); }
.stat.warn strong { color:var(--warn-ink); }
.tablewrap { overflow-x:auto; border:1px solid var(--line); border-radius:12px; background:var(--white); }
table { border-collapse:collapse; width:100%; font-size:.86rem; }
caption { caption-side:top; text-align:left; padding:.8rem 1rem; color:var(--muted); font-size:.85rem; }
th, td { padding:.6rem .7rem; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
th { background:var(--soft); color:var(--navy); font-weight:750; white-space:nowrap; position:sticky; top:0; }
tbody tr:hover { background:#f7fbfa; }
td.req { min-width:280px; }
td.src a { word-break:break-all; }
.badge { display:inline-block; padding:.12rem .5rem; border-radius:999px; font-size:.72rem; font-weight:800;
  letter-spacing:.03em; white-space:nowrap; }
.b-done { color:var(--teal); background:var(--soft); }
.b-limited { color:#8a5a00; background:#fdf0d5; }
.b-open { color:var(--warn-ink); background:var(--warn); }
.b-rejected { color:#7a2a2a; background:#fbe7e7; }
.note { color:var(--muted); font-size:.82rem; }
.foot { margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--line); color:var(--muted); font-size:.82rem; }
"""


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def badge(status: str) -> str:
    cls = {
        "implemented": "b-done",
        "implemented_limited": "b-limited",
        "blocked": "b-open",
        "needs_review": "b-open",
        "not_started": "b-open",
        "rejected_policy": "b-rejected",
    }.get(status, "b-open")
    return f'<span class="badge {cls}">{esc(STATUS_LABEL.get(status, status))}</span>'


def table(rows, cols, *, caption="", row_class=None):
    head = "".join(f"<th>{esc(title)}</th>" for _, title in cols)
    body = []
    for r in rows:
        cells = []
        for key, _ in cols:
            val = r.get(key, "")
            if key == "status":
                cells.append(f"<td>{badge(val)}</td>")
            elif key == "official_source_url" or key == "official_or_method_source":
                url = val
                cells.append(
                    f'<td class="src"><a href="{esc(url)}" target="_blank" rel="noopener">source</a></td>'
                    if url else '<td class="src">&nbsp;</td>'
                )
            elif key == "requirement":
                cells.append(f'<td class="req">{esc(val)}</td>')
            else:
                cells.append(f"<td>{esc(val)}</td>")
        rc = f' class="{row_class(r)}"' if row_class else ""
        body.append(f"<tr{rc}>{''.join(cells)}</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f"<table>{cap}<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def page(title: str, nav_active: str, body: str) -> str:
    nav = [
        ("index.html", "Overview", "index"),
        ("gates.html", "Gates", "gates"),
        ("sources.html", "Sources", "sources"),
        ("flagged.html", "Flagged", "flagged"),
        ("executive-summary.html", "Executive summary", "exec"),
    ]
    parts = []
    for u, t, k in nav:
        cls = ' class="on"' if k == nav_active else ""
        parts.append(f'<a href="{u}"{cls}>{esc(t)}</a>')
    nav_html = "".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Own6 NFL decision-readiness: one row per requirement with the gate that blocks it and the number that would clear it.">
<title>{esc(title)} | Own6 NFL Decision Readiness</title>
<style>{CSS}</style>
</head>
<body>
<header class="topbar"><div class="shell topbar-inner">
<a class="brand" href="index.html">OWN6 <span>NFL Decision Readiness</span></a>
<nav class="topnav">{nav_html}</nav>
</div></header>
<main><div class="shell">
{body}
<div class="foot">Generated deterministically from <code>data/nfl_6ab24751/*.csv</code>.
Every row links an official source. Unconfirmed values are blank and flagged; nothing is inferred.</div>
</div></main>
</body>
</html>
"""


def build_dashboard(pack) -> dict:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    counts = pack.status_counts()
    groups = pack.group_counts()

    # ---- overview / index ----
    kpi = "".join(
        f'<div class="stat"><span class="label">{esc(label)}</span><strong>{n}</strong></div>'
        for label, n in [
            ("Requirements", len(pack.rows)),
            ("Implemented", counts.get("implemented", 0)),
            ("Implemented (limited)", counts.get("implemented_limited", 0)),
            ("Open / blocked", groups.get("open", 0)),
            ("Rejected (policy)", groups.get("rejected", 0)),
        ]
    )
    readiness_tbl = table(
        pack.rows, READINESS_COLS,
        caption="One row per requirement. 'Blocking gate' names the gate that blocks it; "
                "'Clears when' states the number or condition that would clear it.",
    )
    overview = page(
        "Decision readiness",
        "index",
        f"""
<h1>Decision readiness: one row per requirement</h1>
<p class="lead">The brief's explicit deliverable: a decision-readiness table with, for every
requirement, the gate that blocks it and the number that would clear it. Statuses are grounded in
the validation-gate and flag registers of the merged NFL packs; nothing is inferred.</p>
<div class="kpis">{kpi}</div>
<h2>Requirements, gates and clearing numbers</h2>
<div class="tablewrap">{readiness_tbl}</div>
<p class="note">A status of <strong>Implemented</strong> means the artifact exists and is checked.
<strong>Implemented (limited)</strong> means the structure exists but its key numeric output is blank
because a required input (a licensed price archive, full depth coverage, graded selections) is absent.
<strong>Open</strong> rows name the gate that blocks them and the condition that would clear them.
<strong>Rejected</strong> rows are shortcuts the brief explicitly rejects.</p>
""",
    )

    # ---- gates ----
    gates_tbl = table(
        pack.gates,
        [("gate_id", "Gate"), ("gate_name", "Name"), ("what_it_blocks", "Blocks"),
         ("threshold_or_clearing_number", "Clears when"), ("source_pack", "Pack"),
         ("official_or_method_source", "Source")],
        caption="Gate reference. Every blocking gate referenced in the readiness table resolves here.",
    )
    gates_page = page(
        "Gates", "gates",
        f"""<h1>Validation gates</h1>
<p class="lead">The gates that block requirements. Each entry names what it blocks and the threshold or
clearing condition. Gate ids are drawn from the merged packs (VG, NFL-G, D966-G families).</p>
<div class="tablewrap">{gates_tbl}</div>""",
    )

    # ---- sources ----
    sources_tbl = table(
        pack.sources,
        [("source_id", "ID"), ("url", "URL"), ("publisher", "Publisher"),
         ("used_for", "Used for"), ("read_on_utc", "Read on"), ("status", "Status")],
        caption="Official source register. Each URL was read in a prior session and is carried here.",
    )
    sources_page = page(
        "Sources", "sources",
        f"""<h1>Official source register</h1>
<p class="lead">The official and methodological sources behind this readiness roll-up. Each URL is
carried from the merged packs' recorded reads; this session did not re-fetch every page.</p>
<div class="tablewrap">{sources_tbl}</div>""",
    )

    # ---- flagged ----
    flagged_tbl = table(
        pack.flags,
        [("flag_id", "Flag"), ("area", "Area"), ("item", "Item"), ("severity", "Severity"),
         ("what_is_blank_or_unverified", "What is blank / unverified"),
         ("official_source_url", "Source"), ("review_status", "Status")],
        caption="Flagged for review. None of these blocks the readiness table or the merge.",
    )
    flagged_page = page(
        "Flagged for review", "flagged",
        f"""<h1>Flagged for review</h1>
<p class="lead">Irregularities and unverified gaps for this consolidation. They are published, not
concealed, and do not block publication.</p>
<div class="tablewrap">{flagged_tbl}</div>""",
    )

    # ---- executive summary ----
    blockers = [r for r in pack.rows if r["status"] in ("not_started", "blocked", "needs_review")]
    limited = [r for r in pack.rows if r["status"] == "implemented_limited"]
    exec_body = f"""
<h1>Executive summary</h1>
<p class="lead">This pack consolidates the brief's full requirement list into a single
decision-readiness table: for each requirement, the current status, the gate that blocks it, and the
number or condition that would clear it. It is the landing-page table the brief asks for, plus the
gate, source and flag registers behind it.</p>
<div class="kpis">
<div class="stat"><span class="label">Requirements</span><strong>{len(pack.rows)}</strong></div>
<div class="stat"><span class="label">Implemented</span><strong>{counts.get('implemented',0)}</strong></div>
<div class="stat"><span class="label">Implemented (limited)</span><strong>{counts.get('implemented_limited',0)}</strong></div>
<div class="stat warn"><span class="label">Open / blocked</span><strong>{groups.get('open',0)}</strong></div>
<div class="stat"><span class="label">Rejected (policy)</span><strong>{groups.get('rejected',0)}</strong></div>
</div>
<h2>What is done</h2>
<p>{counts.get('implemented',0)} requirements are implemented and checked: the line-origination order,
the signal/staking split, the demotion gate, pre-registration, proper-score ranking, the joint-evidence
gate for combos, and the coordination/PR workflow. {counts.get('implemented_limited',0)} are implemented
but limited: the structure exists and is checked, but the key numeric output is blank because a required
input is absent.</p>
<h2>The binding blockers</h2>
<p>The dominant blocker is <strong>VG-03: no licensed market price archive</strong>. No official NFL page
publishes a price, so every market line, difference, residual, open/close snapshot, ROI and CLV cell stays
blank. The second is <strong>NFL-G10: partial depth coverage</strong> — only a minority of the 32 clubs have
a verified depth chart, so deficiency scores are floors, not charts. A third is <strong>VG-07: the sample
floor</strong> — zero strategies are certified because no graded selections exist yet.</p>
<h2>Open requirements ({len(blockers)})</h2>
<ul>
{''.join(f'<li><strong>{esc(r["req_id"])}</strong> — {esc(r["requirement"])}. Blocks: {esc(r["blocking_gate"])}. Clears when: {esc(r["clearing_number"])}.</li>' for r in blockers[:20])}
</ul>
<p class="note">The remaining open requirements are listed in full in the decision-readiness table.</p>
<h2>Deliberate non-findings</h2>
<ul>
<li>No market price, ROI, CLV or reward payout is published anywhere in this pack.</li>
<li>No depth is inferred from jersey number, experience or salary (rejected by policy).</li>
<li>No strategy is ranked by raw win rate or season-long ROI (rejected by policy).</li>
<li>The readiness table is a consolidated roll-up, not a fresh re-verification of every underlying value.</li>
</ul>
"""
    exec_page = page("Executive summary", "exec", exec_body)

    written = {
        "index.html": overview,
        "gates.html": gates_page,
        "sources.html": sources_page,
        "flagged.html": flagged_page,
        "executive-summary.html": exec_page,
    }
    for name, content in written.items():
        with open(os.path.join(DOCS_DIR, name), "w", encoding="utf-8") as fh:
            fh.write(content)

    # ---- landing fragment (single source of truth for the landing table) ----
    fragment = table(
        pack.rows, READINESS_COLS,
        caption="Decision readiness — one row per requirement, with the gate that blocks it and the number that would clear it.",
    )
    with open(os.path.join(DOCS_DIR, "landing-table.fragment.html"), "w", encoding="utf-8") as fh:
        fh.write(fragment)

    return written


def inject_landing(pack) -> bool:
    """Insert or refresh the decision-readiness table on the root landing page."""
    fragment_path = os.path.join(DOCS_DIR, "landing-table.fragment.html")
    with open(fragment_path, encoding="utf-8") as fh:
        fragment = fh.read()
    section = (
        f'{LANDING_BEGIN}\n'
        '<section id="readiness" class="section" aria-labelledby="readiness-title">\n'
        '  <div class="section-head">\n'
        '    <p class="eyebrow">Readiness</p>\n'
        '    <h2 id="readiness-title">Decision readiness: one row per requirement</h2>\n'
        '    <p>For every requirement: the gate that blocks it and the number that would clear it. '
        'Statuses are grounded in the merged NFL packs\u2019 gate and flag registers. Full detail and '
        'sources: <a href="docs/nfl-6ab24751/index.html">NFL Decision Readiness</a>.</p>\n'
        '  </div>\n'
        f'  <div class="tablewrap">\n{fragment}\n  </div>\n'
        '</section>\n'
        f'{LANDING_END}\n'
    )
    if not os.path.exists(ROOT_INDEX):
        return False
    with open(ROOT_INDEX, encoding="utf-8") as fh:
        content = fh.read()
    if LANDING_BEGIN in content and LANDING_END in content:
        start = content.index(LANDING_BEGIN)
        end = content.index(LANDING_END) + len(LANDING_END)
        new = content[:start] + section + content[end:]
    elif LANDING_BEGIN in content:
        # begin marker without end: replace from begin to end of file tail section
        start = content.index(LANDING_BEGIN)
        new = content[:start] + section
    else:
        # append before the closing </main> if present, else append at end
        marker = "</main>"
        if marker in content:
            idx = content.index(marker)
            new = content[:idx] + section + "\n" + content[idx:]
        else:
            new = content.rstrip() + "\n" + section
    with open(ROOT_INDEX, "w", encoding="utf-8") as fh:
        fh.write(new)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify committed output is current")
    args = ap.parse_args()

    paths = PackPaths.for_repo(ROOT)
    pack = load_pack(paths)
    errors = validate(pack)
    if errors:
        print("VALIDATION ERRORS:")
        for e in errors:
            print(" -", e)
        return 1

    if args.check:
        # Rebuild into a temp check by regenerating and comparing byte-for-byte.
        before = {}
        for name in ("index.html", "gates.html", "sources.html", "flagged.html",
                     "executive-summary.html", "landing-table.fragment.html"):
            p = os.path.join(DOCS_DIR, name)
            before[name] = open(p, encoding="utf-8").read() if os.path.exists(p) else None
        build_dashboard(pack)
        drifted = []
        for name, old in before.items():
            new = open(os.path.join(DOCS_DIR, name), encoding="utf-8").read()
            if old != new:
                drifted.append(name)
        if drifted:
            print("DRIFT: committed output differs from regeneration for:", ", ".join(drifted))
            return 1
        print("OK: readiness pack validates; dashboard regenerates byte-identically.")
        return 0

    build_dashboard(pack)
    injected = inject_landing(pack)
    counts = pack.status_counts()
    print(f"Built docs/nfl-6ab24751 ({len(pack.rows)} requirements; "
          f"implemented={counts.get('implemented',0)}, limited={counts.get('implemented_limited',0)}, "
          f"open={sum(v for k,v in counts.items() if k in ('blocked','needs_review','not_started'))}, "
          f"rejected={counts.get('rejected_policy',0)})")
    print(f"Landing table injected into index.html: {injected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
