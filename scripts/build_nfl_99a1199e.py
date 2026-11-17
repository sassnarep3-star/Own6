#!/usr/bin/env python3
"""Build the nfl_99a1199e pack: CSV tables + a zero-input dashboard site.

Everything published is computed from :mod:`src.nfl_99a1199e.sweep`, whose only
hand-written content is values read verbatim from the 32 official NFL roster
pages this session (stored in :mod:`src.nfl_99a1199e.roster_data`). The builder
takes no arguments and touches no network: a re-run must produce byte-identical
files.

Usage
-----
    python3 scripts/build_nfl_99a1199e.py            # write CSVs and HTML
    python3 scripts/build_nfl_99a1199e.py --check    # build, then run the verifier
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from nfl_99a1199e import sweep as S  # noqa: E402

DATA = os.path.join(REPO, "data", "nfl_99a1199e")
DOCS = os.path.join(REPO, "docs", "nfl-99a1199e")

URLCOLS = ("source_url", "roster_url", "url")

NAV = [
    ("index.html", "Sweep dashboard"),
    ("register.html", "Reserve register"),
    ("flagged.html", "Flagged irregularities"),
    ("sources.html", "Sources"),
    ("capture-log.html", "Capture log"),
    ("executive-summary.html", "Executive summary"),
]


def esc(x) -> str:
    return html.escape("" if x is None else str(x), quote=False)


def link(url: str, label: str = "source") -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">{esc(label)} &#8599;</a>'


def write_csv(name: str, rows, cols=None, source_url: str = ""):
    os.makedirs(DATA, exist_ok=True)
    rows = list(rows)
    cols = cols or (list(rows[0].keys()) if rows else ["empty"])
    # every row carries a source URL; tables without one get it stamped here
    if source_url and not any(c in cols for c in URLCOLS):
        cols = cols + ["source_url"]
        for r in rows:
            r.setdefault("source_url", source_url)
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return path


def page(title: str, body: str, active: str) -> str:
    parts = []
    for u, t in NAV:
        cls = ' class="on"' if u == active else ""
        parts.append(f'<a href="{esc(u)}"{cls}>{esc(t)}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL 99a1199e</title>
<style>
 body{{font:15px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#12233b;background:#f6f8fb}}
 header{{background:#0b2545;color:#fff;padding:18px 22px}}
 header h1{{margin:0;font-size:20px}} header p{{margin:4px 0 0;opacity:.85;font-size:13px}}
 nav{{display:flex;flex-wrap:wrap;gap:2px;background:#13315c;padding:6px 10px}}
 nav a{{color:#cfe0f5;text-decoration:none;padding:5px 9px;border-radius:4px;font-size:12.5px}}
 nav a.on,nav a:hover{{background:#ee6c4d;color:#fff}}
 main{{max-width:1180px;margin:0 auto;padding:18px}}
 section{{background:#fff;border:1px solid #dfe6f0;border-radius:8px;padding:14px 16px;margin:14px 0}}
 h2{{font-size:17px;margin:4px 0 10px}} h3{{font-size:14.5px;margin:12px 0 6px}}
 table{{border-collapse:collapse;width:100%;font-size:12.5px}}
 th,td{{border:1px solid #e3e9f2;padding:5px 7px;text-align:left;vertical-align:top}}
 th{{background:#eef3fa;position:sticky;top:0}}
 td.blank{{background:#fff7e6}}
 a{{color:#0b5394}} .pill{{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px}}
 .ok{{background:#d9f2e2;color:#1c6b3d}} .no{{background:#fde2e2;color:#8f1d1d}}
 .warn{{background:#fff3cd;color:#7a5b00}}
 .note{{background:#f2f6fc;border-left:3px solid #13315c;padding:8px 12px;margin:8px 0;font-size:13px}}
 footer{{text-align:center;color:#7a8aa3;font-size:12px;padding:18px}}
</style></head><body>
<header><h1>NFL 32-Club Roster Sweep (99a1199e)</h1>
<p>Capture date 2026-11-17 UTC · every row links an official roster page · status codes stored verbatim · no interpretation, no price values</p></header>
<nav>{nav}</nav>
<main>{body}</main>
<footer>Built from src/nfl_99a1199e (deterministic builder; re-run is byte-identical). Values were read from the cited official roster pages on 2026-11-17 UTC.</footer>
</body></html>
"""


def table(cols, rows, blank_cols=()):
    """cols: list of (key, header). Renders a plain table; URL keys become links."""
    cols = list(cols)
    shown = {k for k, _ in cols}
    for r in rows:
        for c in URLCOLS:
            if c not in shown and r.get(c):
                cols.append((c, "Official source"))
                shown.add(c)
    out = ["<div style='overflow-x:auto'><table><thead><tr>"]
    for _, h in cols:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for k, _ in cols:
            v = r.get(k, "")
            is_url = isinstance(v, str) and v.startswith("http")
            cls = " class='blank'" if (k in blank_cols and not v) else ""
            cell = link(v) if is_url else esc(v)
            out.append(f"<td{cls}>{cell}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def pill(ok: bool, yes="OK", no="FLAGGED") -> str:
    return f"<span class='pill {'ok' if ok else 'no'}'>{esc(yes if ok else no)}</span>"


def build():
    os.makedirs(DOCS, exist_ok=True)

    sweep = S.sweep_rows()
    register = S.register_rows()
    flags = S.flagged_rows()
    log = S.capture_log_rows()
    sources = S.sources_rows()
    stats = S.summary_stats()

    # ---------------- data tables ----------------
    write_csv("roster_sweep.csv", sweep)
    write_csv("reserve_register.csv", register)
    write_csv("capture_log.csv", log)
    write_csv("flagged.csv", flags)
    write_csv("sources.csv", sources)
    write_csv("status_code_tally.csv", S.code_tally())

    # ---------------- pages ----------------
    def save(name, title, body):
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as fh:
            fh.write(page(title, body, name))

    # index: the sweep dashboard
    tally_by_code = {t["status_code"]: t["rows"] for t in stats["code_tally"]}
    code_cells = " · ".join(
        f"<b>{esc(c)}</b> {n}" for c, n in sorted(tally_by_code.items()))
    body = f"""
<section><h2>Sweep dashboard — 32 official roster pages, one row per club</h2>
<div class="note">Every value below was read verbatim from the club's official NFL roster
page on 2026-11-17 UTC. The STATUS column is the authoritative designation printed by the
publisher and is stored as printed. Rows whose status is not ACT form the reserve register
(captured per player); ACT rows are summarised by count only.</div>
<p>Clubs swept: <b>{stats['clubs']}</b> · roster rows read: <b>{stats['total_rows']}</b>
· active rows: <b>{stats['active_rows']}</b> · reserve rows: <b>{stats['reserve_rows']}</b>
· status codes observed: <b>{stats['status_codes']}</b> · flagged irregularities:
<b>{stats['flagged']}</b>.</p>
<p>Status-code distribution: {code_cells}.</p>
{table([("club", "Club"), ("roster_url", "Roster page"), ("read_at_utc", "Read at (UTC)"),
        ("total_rows", "Rows"), ("active_count", "ACT"), ("reserve_count", "Reserve"),
        ("status_codes_seen", "Codes (verbatim)")], sweep)}</section>"""
    save("index.html", "Sweep dashboard", body)

    body = f"""
<section><h2>Reserve register — every non-ACT roster row, per player</h2>
<div class="note">{stats['reserve_rows']} rows across {stats['clubs']} clubs, in page order.
"Not active" is what the page printed; nothing is inferred from a code's likely meaning, and
no row is dropped or merged. Status codes are verbatim (ACT is excluded from this register by
construction; it is counted per club on the dashboard).</div>
{table([("club", "Club"), ("player", "Player"), ("position", "Pos"),
        ("status_code", "Status code"), ("read_at_utc", "Read at (UTC)"),
        ("source_url", "Source")], register)}</section>"""
    save("register.html", "Reserve register", body)

    body = f"""
<section><h2>Flagged for review — irregularities captured, not interpreted</h2>
<div class="note">Flagged items do not block anything. Each row is published with its source
link so a human can review it. The sweep's rule is verbatim capture: irregularities are
recorded as printed and never silently fixed.</div>
{table([("flag_id", "ID"), ("club", "Club"), ("category", "Category"), ("issue", "Issue"),
        ("what_was_done", "What was done"), ("remediation", "Remediation"),
        ("source_url", "Source")], flags)}</section>"""
    save("flagged.html", "Flagged irregularities", body)

    body = f"""
<section><h2>Sources — every roster page read, its clock, and what was taken from it</h2>
<div class="note">{len(sources)} official roster pages, one per club. The read clock is the
UTC moment the page was read; it is stamped on every published row from that page.</div>
{table([("source_id", "ID"), ("title", "Title"), ("url", "Official page"),
        ("read_on_utc", "Read on (UTC)"), ("what_was_read", "What was read")], sources)}</section>"""
    save("sources.html", "Sources", body)

    body = f"""
<section><h2>Capture log — every roster-page read, including repeats</h2>
<div class="note">Repeat reads are data too: the CAR page was re-read to reconcile its row
total, and the outcome is published rather than hidden. All reads were successful; a failed
read would ship as a blank with its reason, never as a guess.</div>
{table([("read_at_utc", "Read at (UTC)"), ("url", "URL"), ("intent", "Intent"),
        ("outcome", "Outcome"), ("note", "Note")], log)}</section>"""
    save("capture-log.html", "Capture log", body)

    body = f"""
<section><h2>Executive summary</h2>
<div class="note">The G-SWEEP / R-13 sweep: all 32 official NFL club roster pages read on
2026-11-17 UTC and transcribed verbatim into this pack. It closes the roster-sweep gap that
earlier packs left open — a factual, source-linked roster/IR sweep across every club, with
status codes stored exactly as the publisher printed them.</div>
<h3>The numbers a reviewer can re-check in one line each</h3>
<ul>
<li>Clubs swept: {stats['clubs']} of 32 — every club's official roster page was read.</li>
<li>Roster rows read: {stats['total_rows']} ({stats['active_rows']} ACT + {stats['reserve_rows']} reserve).</li>
<li>Status codes observed: {stats['status_codes']} — ACT, CUT, DEV, EXE, PUP, RES, RLS, RSN, RSR, TRC, TRD, TRT.</li>
<li>Flagged irregularities: {stats['flagged']} (see <a href="flagged.html">Flagged for review</a>).</li>
</ul>
<h3>What is deliberately not in this pack</h3>
<ul>
<li>No interpretation of status codes: each code is stored verbatim; none is expanded to an
invented meaning.</li>
<li>No merging of the same name printed on two club pages: every occurrence is kept on its own
club page and flagged for review.</li>
<li>No price, line, odds, ROI, CLV or profitability values anywhere (no official price data exists).</li>
</ul>
<h3>Irregularities</h3>
<p>See <a href="flagged.html">Flagged for Review</a>: the GB name/slug mismatch, the IND
unusual status listing, the NE embedded-quote name, the two unlinked reserve rows (NO, TB), the
CAR row-total reconciliation, and the cross-club repeated names.</p>
</section>"""
    save("executive-summary.html", "Executive summary", body)

    return len(sweep), len(register), len(flags), len(log)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    n_sweep, n_reg, n_flags, n_log = build()
    print(f"built: sweep {n_sweep} clubs, register {n_reg} rows, flags {n_flags}, capture log {n_log}")
    if args.check:
        sys.exit(subprocess.call([sys.executable,
                                  os.path.join(REPO, "scripts", "check_nfl_99a1199e.py")]))
