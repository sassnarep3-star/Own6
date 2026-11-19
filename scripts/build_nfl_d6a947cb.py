#!/usr/bin/env python3
"""Build the d6a947cb static site (docs/nfl-d6a947cb/) from data/nfl_d6a947cb/.

Every number on every page is computed from the CSV registers at build time.
Deterministic: running twice produces identical files.
"""
from __future__ import annotations

import csv
import html
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_d6a947cb"
OUT = ROOT / "docs" / "nfl-d6a947cb"
EXEC_MD = ROOT / "NFL_D6A947CB_EXECUTIVE_SUMMARY.md"
OFFICIAL_HOSTS = ("www.nfl.com", "operations.nfl.com")
REPO_HOSTS = ("github.com", "api.github.com")

NAV = [
    ("index.html", "Overview"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions &amp; answers"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for Review"),
    ("verification.html", "Official re-reads"),
    ("sources.html", "Sources"),
    ("repo-review.html", "Repo review"),
    ("executive-summary.html", "Executive summary"),
]


def read(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def host(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url or "")
    return m.group(1) if m else ""


def official(url: str) -> bool:
    return host(url) in OFFICIAL_HOSTS


def src_cell(url: str, read_tag: str) -> str:
    if not url:
        return '<span class="flag">no source link: unverified</span>'
    tag = read_tag or "not re-read this session"
    cls = "ok" if read_tag else "muted"
    return f'<a href="{esc(url)}" rel="noopener">{esc(host(url))}</a><br><span class="{cls}">{esc(tag)}</span>'


def link_or_text(value: str, read_tag: str = "") -> str:
    """A URL becomes a source cell; anything else (e.g. a file list) is shown as plain text."""
    if value.startswith("http"):
        return src_cell(value, read_tag)
    return esc(value) if value else '<span class="flag">no source link: unverified</span>'


def read_map(official_reads: list[dict], sources: list[dict]) -> dict[str, str]:
    """URL -> read stamp, for URLs read in this session (official reads only)."""
    m: dict[str, str] = {}
    for r in official_reads:
        m.setdefault(r["official_url"], f'read {r["read_utc"]} ({r["scope_read"]})')
    for s in sources:
        if s["publisher"].startswith("NFL") and s["result"]:
            m.setdefault(s["url"], f'read {s["read_utc"]} ({s["scope_read"]})')
    return m


def table(headers: list[str], rows: list[list[str]], cls: str = "data") -> str:
    th = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="wrap"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def page(title: str, active: str, body: str) -> str:
    nav = "".join(
        f'<a href="{href}"{" class=on" if href == active else ""}>{label}</a>' for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | Own6 NFL Decision Desk</title>
<style>
:root{{--ink:#17202a;--muted:#5b6670;--line:#dfe4ea;--bg:#f7f9fb;--ok:#1e7a46;--warn:#9a5b00;--bad:#a12626;--acc:#1d4f91}}
*{{box-sizing:border-box}} body{{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
header{{background:#fff;border-bottom:1px solid var(--line);padding:14px 22px}}
header h1{{font-size:18px;margin:0 0 8px}} header .sub{{color:var(--muted);font-size:13px}}
nav{{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}} nav a{{padding:5px 10px;border:1px solid var(--line);border-radius:6px;color:var(--acc);text-decoration:none;font-size:13px;background:#fff}}
nav a.on{{background:var(--acc);color:#fff;border-color:var(--acc)}}
main{{max-width:1200px;margin:0 auto;padding:18px 22px 40px}}
h2{{font-size:17px;margin:26px 0 8px}} h3{{font-size:15px;margin:18px 0 6px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:10px 0}}
.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:12px}}
.card .n{{font-size:24px;font-weight:700}} .card .l{{color:var(--muted);font-size:12px}}
.wrap{{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:8px}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:#eef2f6;position:sticky;top:0}} td a{{color:var(--acc)}}
.ok{{color:var(--ok)}} .muted{{color:var(--muted)}} .flag{{color:var(--bad);font-weight:600}} .warn{{color:var(--warn);font-weight:600}}
.note{{background:#fff;border-left:4px solid var(--acc);padding:10px 14px;border-radius:6px;margin:10px 0;color:#2d3742}}
.filter{{padding:7px 10px;border:1px solid var(--line);border-radius:6px;width:360px;max-width:100%;margin:8px 0}}
footer{{color:var(--muted);font-size:12px;margin-top:30px}}
.pill{{display:inline-block;border:1px solid var(--line);border-radius:10px;padding:1px 8px;font-size:12px;background:#fff}}
</style>
</head>
<body>
<header>
<h1>Own6 NFL Decision Desk</h1>
<div class="sub">Research framework, not a betting feed or picks service. No profitability claim. Every value is read from an official NFL page with a UTC clock, carried from a named earlier pack, or left blank and flagged.</div>
<nav>{nav}</nav>
</header>
<main>
{body}
<footer>Generated by scripts/build_nfl_d6a947cb.py from data/nfl_d6a947cb/ (session d6a947cb, branch arena/d6a947cb-own6). Rebuild with: python3 scripts/build_nfl_d6a947cb.py</footer>
</main>
<script>
function filt(id, box){{var q=box.value.toLowerCase();document.querySelectorAll('#'+id+' tbody tr').forEach(function(r){{r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none';}});}}
</script>
</body>
</html>
"""


def md_to_html(md: str) -> str:
    out, para, in_table, rows = [], [], False, []

    def inline(s: str) -> str:
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"\[(.+?)\]\((https?://[^)]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
        return s

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def flush_table():
        nonlocal in_table, rows
        if rows:
            head, body = rows[0], rows[2:]
            out.append(table(head, [[inline(c) for c in r] for r in body], cls="data md"))
        rows = []
        in_table = False

    for line in md.splitlines():
        if line.startswith("|"):
            flush_para()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
            in_table = True
            continue
        if in_table:
            flush_table()
        if not line.strip():
            flush_para()
        elif line.startswith("### "):
            flush_para(); out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_para(); out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_para(); out.append(f"<h2>{inline(line[2:])}</h2>")
        elif line.startswith("- "):
            flush_para(); out.append("<ul><li>" + inline(line[2:]) + "</li></ul>")
        else:
            para.append(line.strip())
    flush_para()
    if in_table:
        flush_table()
    # merge consecutive single-item lists
    html_s = "".join(out).replace("</li></ul><ul><li>", "</li><li>")
    return html_s


def main() -> None:
    reqs = read("requirements.csv")
    reads = read("official_reads_2026_11_19.csv")
    qs = read("questions.csv")
    sugg = read("suggestions.csv")
    rfs = read("repo_findings.csv")
    srcs = read("sources.csv")
    ledgers = read("ledger_comparison.csv")
    rm = read_map(reads, srcs)

    OUT.mkdir(parents=True, exist_ok=True)
    cnt = Counter(r["d6a_status"] for r in reqs)
    unique = [r for r in reqs if not r["duplicate_of"]]
    rd_match = Counter(r["result"] for r in reads)
    q_status = Counter(r["answer_status"].split(" ")[0] for r in qs)
    flagged_rf = [r for r in rfs if r["blocks_merge"] == "no"]
    needs = [r for r in reqs if r["d6a_status"] in ("needs_review", "needs_decision")]
    n_read_src = sum(1 for r in reqs if r["source_read_today_utc"])

    def badge(s: str) -> str:
        cls = {"met": "ok", "partially_met": "warn", "blocked": "flag", "needs_review": "warn", "needs_decision": "warn"}.get(s, "muted")
        return f'<span class="{cls}">{esc(s)}</span>'

    # ---------- Overview (landing) ----------
    cards = [
        (len(reqs), "owner bullets (rows)"),
        (len(unique), "unique requirements"),
        (cnt.get("met", 0), "met (carried + re-checked)"),
        (cnt.get("partially_met", 0), "partially met"),
        (cnt.get("blocked", 0), "blocked by a named gate"),
        (len(needs), "needs review or decision"),
        (len(reads), "official re-reads today"),
        (len(qs), "questions tracked"),
        (len(sugg), "suggestions pending your choice"),
        (len(flagged_rf), "flagged for review"),
    ]
    card_html = "".join(f'<div class="card"><div class="n">{n}</div><div class="l">{esc(l)}</div></div>' for n, l in cards)
    landing_rows = []
    for r in reqs:
        dup = f' <span class="pill">duplicate of {esc(r["duplicate_of"])}</span>' if r["duplicate_of"] else ""
        landing_rows.append([
            esc(r["req_id"]), esc(r["owner_requirement"]) + dup, esc(r["category"]), badge(r["d6a_status"]),
            esc(r["blocking_gate"]), esc(r["number_that_would_clear_it"]),
            src_cell(r["source_url"], rm.get(r["source_url"], "")),
        ])
    landing = f"""
<div class="note"><strong>How to read this page.</strong> Each row is one owner requirement. Status is what this session could support; the gate column names what blocks it; the number column says what would clear it. A link without a read stamp was not re-read this session and is shown as such. Nothing here is a betting recommendation.</div>
<div class="cards">{card_html}</div>
<h2>Decision readiness: one row per requirement</h2>
<input class="filter" placeholder="Filter rows (id, text, status, gate)..." oninput="filt('landing',this)">
{table(["ID", "Requirement", "Category", "Status", "Blocking gate", "Number that would clear it", "Source (official link)"], landing_rows).replace('<table class="data"', '<table id="landing" class="data"')}
<h2>Where to go next</h2>
<div class="cards">
<div class="card"><a href="requirements.html">Requirements</a><div class="l">Full register with carried state, re-check basis and flags.</div></div>
<div class="card"><a href="questions.html">Questions and answers</a><div class="l">What must be known, what we have, what is missing, how to find out.</div></div>
<div class="card"><a href="suggestions.html">Suggestions</a><div class="l">Site and method options for you to choose. Nothing is implemented.</div></div>
<div class="card"><a href="flagged.html">Flagged for Review</a><div class="l">Irregularities and unverified items, with source links. None blocks the merge.</div></div>
<div class="card"><a href="verification.html">Official re-reads</a><div class="l">Each re-read today: expected, observed, result, raw file hash.</div></div>
<div class="card"><a href="repo-review.html">Repo review</a><div class="l">Counts and irregularities at base e9185b3, with the command that reproduces each.</div></div>
<div class="card"><a href="executive-summary.html">Executive summary</a><div class="l">The short version: what is known, what is not, what decides it.</div></div>
</div>
"""
    (OUT / "index.html").write_text(page("Overview", "index.html", landing), encoding="utf-8")

    # ---------- Requirements ----------
    req_rows = []
    for r in reqs:
        req_rows.append([
            esc(r["req_id"]), esc(r["category"]), esc(r["owner_requirement"]) + (f' <span class="pill">dup of {esc(r["duplicate_of"])}</span>' if r["duplicate_of"] else ""),
            esc(r["carried_state"]), badge(r["d6a_status"]), esc(r["d6a_basis"]), esc(r["blocking_gate"]),
            esc(r["number_that_would_clear_it"]), src_cell(r["source_url"], rm.get(r["source_url"], "")), esc(r["flag_ids"]),
        ])
    req_body = f"""
<h2>Requirement register ({len(reqs)} rows; {len(unique)} unique bullets)</h2>
<div class="note">Carried state is copied from data/nfl_0ce967db/requirements.csv. Status is this session's state after re-checks; it changes only where a row lists a re-read result. Categories were assigned by hand for this pack.</div>
<input class="filter" placeholder="Filter rows..." oninput="filt('reqs',this)">
{table(["ID", "Category", "Owner bullet", "Carried state", "Status now", "Basis", "Blocking gate", "Number that would clear it", "Source", "Flags"], req_rows).replace('<table class="data"', '<table id="reqs" class="data"')}
<h2>Ledger comparison (ten requirement ledgers in the repo)</h2>
<div class="note">The same owner bullets are tracked in ten ledgers with different status words. The counts below are computed from each file. They cannot be added together without a mapping (suggestion S-02).</div>
{table(["Ledger file", "Rows", "Status column", "Status counts"], [[esc(l["ledger"]), esc(l["rows"]), esc(l["status_column"]), esc(l["status_counts"])] for l in ledgers])}
"""
    (OUT / "requirements.html").write_text(page("Requirements", "requirements.html", req_body), encoding="utf-8")

    # ---------- Questions ----------
    q_rows = [[esc(q["q_id"]), esc(q["question"]), esc(q["information_we_have"]), esc(q["information_missing"]), esc(q["answer_status"]),
               esc(q["answer_now"]), esc(q["blocks_requirements"]), esc(q["discovery_path_no_guessing"]), esc(q["owner_decision_needed"]),
               src_cell(q["source_url"], rm.get(q["source_url"], ""))] for q in qs]
    q_body = f"""
<h2>Questions, information and answers before any decision</h2>
<div class="note">Answer status is one of answered, partly answered, or unanswered. An answer is given only where an official read supports it. Where the source link is an entry point we did not read, the row says so.</div>
{table(["ID", "Question", "Information we have", "Information missing", "Answer status", "Answer now", "Blocks", "How to discover it (no guessing)", "Owner decision?", "Source"], q_rows)}
"""
    (OUT / "questions.html").write_text(page("Questions and answers", "questions.html", q_body), encoding="utf-8")

    # ---------- Suggestions ----------
    s_rows = [[esc(s["s_id"]), esc(s["area"]), esc(s["suggestion"]), esc(s["why_evidence"]), esc(s["option_a"]), esc(s["option_b"]),
               esc(s["effort"]), esc(s["reversible"]), '<span class="warn">pending your choice</span>' if s["pending_human_choice"] == "yes" else "", esc(s["implemented"])] for s in sugg]
    s_body = f"""
<h2>Suggestions for you to choose from</h2>
<div class="note"><strong>Nothing on this page has been implemented.</strong> Each row offers two options. Record your choice in data/nfl_d6a947cb/suggestions.csv (owner_choice column) or tell the agent which option to build. Only the owner chooses.</div>
{table(["ID", "Area", "Suggestion", "Why (evidence)", "Option A", "Option B", "Effort", "Reversible", "Decision", "Implemented"], s_rows)}
"""
    (OUT / "suggestions.html").write_text(page("Suggestions", "suggestions.html", s_body), encoding="utf-8")

    # ---------- Flagged ----------
    f_rows = [[esc(r["rf_id"]), esc(r["area"]), esc(r["finding"]), esc(r["severity"]),
               link_or_text(r["official_or_repo_link"], rm.get(r["official_or_repo_link"], "")), esc(r["reproduce_with"]), esc(r["blocks_merge"])] for r in flagged_rf]
    n_rows = [[esc(r["req_id"]), esc(r["owner_requirement"]), badge(r["d6a_status"]), esc(r["d6a_basis"]), src_cell(r["source_url"], rm.get(r["source_url"], ""))] for r in needs]
    f_body = f"""
<h2>Flagged for Review</h2>
<div class="note"><strong>None of these items blocks the merge.</strong> They are published so you can review them after the site is live and ask for changes. Each row names its source link and how to reproduce it.</div>
<h3>Irregularities in the repo ({len(flagged_rf)})</h3>
{table(["ID", "Area", "Finding", "Severity", "Source link", "How to reproduce", "Blocks merge"], f_rows)}
<h3>Requirements that need a review or a decision ({len(needs)})</h3>
{table(["ID", "Owner bullet", "Status now", "Basis", "Source"], n_rows)}
"""
    (OUT / "flagged.html").write_text(page("Flagged for Review", "flagged.html", f_body), encoding="utf-8")

    # ---------- Verification ----------
    v_rows = [[esc(r["check_id"]), esc(r["requirement_ids"]), src_cell(r["official_url"], f'read {r["read_utc"]} ({r["scope_read"]})'),
               esc(r["claim_tested"]), esc(r["expected_value"]), esc(r["observed_value"]), esc(r["result"]), esc(r["flag_id"]), esc(r["raw_file"])] for r in reads]
    caps = read_capture_log()
    c_rows = [[esc(c["file"]), esc(c["sha256"]), esc(c["bytes"])] for c in caps]
    v_body = f"""
<h2>Official re-reads on 2026-11-19 (UTC)</h2>
<div class="note">Result counts: {esc(', '.join(f'{k} {v}' for k, v in sorted(rd_match.items())))}. Each row names the official page, the part of the page read, what was expected and what was observed. Raw excerpts are copies of tool output; their hashes below cover those excerpt files, not the live pages.</div>
{table(["Check", "Requirement IDs", "Official source", "Claim tested", "Expected", "Observed", "Result", "Flag", "Raw excerpt"], v_rows)}
<h2>Capture log (sha256 of each raw excerpt)</h2>
{table(["File", "sha256", "Bytes"], c_rows)}
"""
    (OUT / "verification.html").write_text(page("Official re-reads", "verification.html", v_body), encoding="utf-8")

    # ---------- Sources ----------
    s2 = [[esc(s["source_id"]), esc(s["publisher"]), src_cell(s["url"], f'read {s["read_utc"]} ({s["scope_read"]})' if s["result"] else ""), esc(s["result"]), esc(s["used_for"])] for s in srcs]
    src_body = f"""
<h2>Sources read or relied on</h2>
<div class="note">Official NFL sources are on nfl.com and operations.nfl.com. The two GitHub rows are the repo's own commits and Pages settings; they are labelled as not NFL sources. Carried sources from earlier packs are listed in each pack's register and are not re-read here.</div>
{table(["ID", "Publisher", "URL", "Result", "Used for"], s2)}
"""
    (OUT / "sources.html").write_text(page("Sources", "sources.html", src_body), encoding="utf-8")

    # ---------- Repo review ----------
    rr_rows = [[esc(r["rf_id"]), esc(r["area"]), esc(r["finding"]), esc(r["evidence"]), esc(r["severity"]), esc(r["reproduce_with"])] for r in rfs]
    rr_body = f"""
<h2>Repo review (base commit e9185b3, the main branch at claim time)</h2>
<div class="note">Counts were read from git at the base commit, not from the working tree, so later packs do not change them. Each finding names the command that reproduces it. The full review is in audit/NFL_D6A947CB_REPO_REVIEW.md.</div>
{table(["ID", "Area", "Finding", "Evidence", "Severity", "Reproduce with"], rr_rows)}
"""
    (OUT / "repo-review.html").write_text(page("Repo review", "repo-review.html", rr_body), encoding="utf-8")

    # ---------- Executive summary ----------
    es = md_to_html(EXEC_MD.read_text(encoding="utf-8")) if EXEC_MD.exists() else "<p>Missing executive summary.</p>"
    (OUT / "executive-summary.html").write_text(page("Executive summary", "executive-summary.html", f'<div class="note">Plain-text version of NFL_D6A947CB_EXECUTIVE_SUMMARY.md at the repo root.</div>{es}'), encoding="utf-8")
    print(f"built {len(NAV)} pages into {OUT.relative_to(ROOT)}")


def read_capture_log() -> list[dict]:
    p = DATA / "capture_log.csv"
    return list(csv.DictReader(p.open(newline="", encoding="utf-8"))) if p.exists() else []


if __name__ == "__main__":
    sys.exit(main())
