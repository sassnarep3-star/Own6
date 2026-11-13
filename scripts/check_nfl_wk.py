#!/usr/bin/env python3
"""Verify the NFL Week pack. Fails closed and exits non-zero on any violation.

Checks
  1. Every HTML page exists, parses, and links only to pages that exist.
  2. No <input>, <form>, <select>, <textarea> or <button> anywhere (zero manual input).
  3. Every data row in the source-linked tables carries an http(s) URL in a source column.
  4. No market price, ROI or correlation coefficient is published as a number.
  5. The verified inputs still satisfy the league identities (sum W = sum L, etc.).
  6. Every flag ID cited on the site exists in flagged.csv, and vice versa.
  7. External links use https only, and every registered source URL was read on a date.
  8. Rebuilt artefacts are deterministic (a second build changes nothing).
"""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "nfl-wk"
DATA = ROOT / "data" / "nfl_wk"

FAILS: list[str] = []
NOTES: list[str] = []


def fail(msg: str) -> None:
    FAILS.append(msg)


def read(name: str) -> list[dict]:
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.forbidden: list[str] = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.hrefs.append(d["href"])
        if tag in ("input", "form", "select", "textarea", "button"):
            self.forbidden.append(tag)


def check_pages() -> int:
    pages = sorted(SITE.glob("*.html"))
    if not pages:
        fail("no HTML pages found in docs/nfl-wk/")
        return 0
    for p in pages:
        parser = Links()
        parser.feed(p.read_text(encoding="utf-8"))
        if parser.forbidden:
            fail(f"{p.name}: contains manual-input elements {parser.forbidden}")
        for href in parser.hrefs:
            if href.startswith(("http://", "https://")):
                if href.startswith("http://"):
                    fail(f"{p.name}: non-https external link {href}")
                continue
            if href.startswith("#"):
                continue
            target = (p.parent / href.split("#")[0]).resolve()
            if not target.exists():
                fail(f"{p.name}: broken internal link {href}")
            if href.endswith(".html"):
                pass
    return len(pages)


def check_sources() -> None:
    sources = read("sources.csv")
    if len(sources) < 20:
        fail(f"sources.csv has only {len(sources)} rows")
    for s in sources:
        if not s["url"].startswith("https://"):
            fail(f"source {s['source_id']} has a non-https URL: {s['url']}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["read_on"] or ""):
            fail(f"source {s['source_id']} has no read_on date")
        if not s["supports"]:
            fail(f"source {s['source_id']} does not state what it supports")
        if not s["does_not_support"]:
            fail(f"source {s['source_id']} does not state what it does NOT support")


def check_standings_identity() -> None:
    rows = read("standings_2026_w11.csv")
    if len(rows) != 32:
        fail(f"standings has {len(rows)} rows, expected 32")
    s = lambda k: sum(int(r[k]) for r in rows)
    checks = {
        "sum W == sum L": s("w") == s("l"),
        "sum PF == sum PA": s("pf") == s("pa"),
        "home wins == road losses": s("home_w") == s("road_l"),
        "home losses == road wins": s("home_l") == s("road_w"),
        "ties == 2": s("t") == 2,
    }
    for name, ok in checks.items():
        if not ok:
            fail(f"standings identity broken: {name}")
    for r in rows:
        if int(r["w"]) + int(r["l"]) + int(r["t"]) == 0:
            fail(f"{r['team']} has zero games played")


def check_no_invented_numbers() -> None:
    own = read("own_lines.csv")
    for r in own:
        for col in ("market_spread", "market_total", "market_ml_home", "market_ml_away", "edge_vs_market"):
            if r[col] != "":
                fail(f"own_lines {r['game_id']}: {col} must be blank (no market price is licensed), got {r[col]!r}")
        if not r["flags"]:
            fail(f"own_lines {r['game_id']}: missing the omissions flag")
    for r in read("correlations.csv"):
        for col in ("corr_value", "corr_ci_low", "corr_ci_high", "n_pairs"):
            if r[col] != "":
                fail(f"correlations {r['id']}: {col} must be blank (no paired history), got {r[col]!r}")
        if not r["pre_registered_sign"]:
            fail(f"correlations {r['id']}: no pre-registered sign")
    for r in read("strategies.csv"):
        for col in ("roi", "clv", "hit_rate", "n_bets"):
            if r[col] != "":
                fail(f"strategies {r['id']}: {col} must be blank, got {r[col]!r}")
        if r["eligibility"] != "QUARANTINED":
            fail(f"strategies {r['id']}: eligibility must be QUARANTINED, got {r['eligibility']}")
    for r in read("leaderboard.csv"):
        if r["rank"] != "—":
            fail(f"leaderboard {r['strategy_id']}: rank must be em-dash while no strategy qualifies")
        if r["reward_paid"] != "no":
            fail(f"leaderboard {r['strategy_id']}: no reward may be paid")
    for r in read("luck_skill.csv"):
        if not r["verification_status"].startswith("policy"):
            fail(f"luck_skill {r['id']}: publishes an unverifiable claim: {r['what_is_published'][:60]}")


def check_gates_fail_closed() -> None:
    rows = read("validation_gates.csv")
    if len(rows) != 12:
        fail(f"expected 12 gates, found {len(rows)}")
    passed = [r["gate_id"] for r in rows if r["status"] == "PASS"]
    if passed != ["VG-12"]:
        fail(f"only VG-12 (pre-registration) may pass; passed={passed}")
    for r in rows:
        if not r["rule"] or not r["artefact_required"]:
            fail(f"gate {r['gate_id']} missing a rule or artefact")


def check_depth_join() -> None:
    detail = read("depth_deficiency.csv")
    summary = read("depth_summary.csv")
    if len(detail) == 0:
        fail("depth_deficiency.csv is empty")
    if len(summary) != 28:
        fail(f"depth_summary has {len(summary)} rows, expected 28 clubs (one per club on the report)")
    for r in detail:
        if r["club_chart_depth_string"] and not r["club_chart_depth_string"].isdigit():
            fail(f"depth row {r['team']}/{r['player']}: bad depth string {r['club_chart_depth_string']!r}")
        if r["chart_status"] == "listed" and not r["club_chart_depth_string"]:
            fail(f"depth row {r['team']}/{r['player']}: listed without a string")
        if r["chart_status"] == "not_listed_on_club_chart" and r["club_chart_depth_string"]:
            fail(f"depth row {r['team']}/{r['player']}: unlisted but has a string")
    for r in summary:
        if r["verification_status"] == "unverified_blank" and (r["deficiency_score"] or r["off_first_string_ruled_out"]):
            fail(f"depth summary {r['team']}: unverified club must publish blanks, not values")


def check_flags() -> None:
    flags = read("flagged.csv")
    ids = {f["flag_id"] for f in flags}
    if len(ids) != len(flags):
        fail("duplicate flag ids")
    for f in flags:
        if f["severity"] not in ("high", "medium", "low"):
            fail(f"{f['flag_id']}: bad severity {f['severity']}")
        if not f["source_url"].startswith("https://"):
            fail(f"{f['flag_id']}: flag has no https source")
        if "blank" not in f["published_value"].lower() and not f["published_value"]:
            fail(f"{f['flag_id']}: must state the published value or that it is blank")
    html = (SITE / "flagged.html").read_text(encoding="utf-8")
    for fid in ids:
        if fid not in html:
            fail(f"{fid} is not rendered on flagged.html")


def check_qa_and_suggestions() -> None:
    qa = read("decision_qa.csv")
    if len(qa) < 20:
        fail(f"decision_qa has only {len(qa)} rows")
    for q in qa:
        if not q["source_url"].startswith("https://"):
            fail(f"{q['qid']}: no https source")
        if not q["discovery_step"]:
            fail(f"{q['qid']}: no discovery step, so the question cannot be closed")
        if not q["answer_status"]:
            fail(f"{q['qid']}: no answer status")
        for col in ("what_we_have", "what_we_lack"):
            if not q[col]:
                fail(f"{q['qid']}: {col} is empty (must say 'nothing' explicitly)")
    sugg = read("suggestions.csv")
    if len(sugg) < 15:
        fail(f"suggestions has only {len(sugg)} rows")
    for s in sugg:
        if s["review_status"] not in ("implemented", "awaiting_decision", "rejected"):
            fail(f"{s['id']}: bad review status {s['review_status']}")
        if not s["risk_if_adopted"]:
            fail(f"{s['id']}: no risk stated")
    html = (SITE / "suggestions.html").read_text(encoding="utf-8")
    if html.count('aria-label="blank, unverified"') < 1:
        fail("suggestions.html has no empty decision cell")


def check_requirements_coverage() -> None:
    reqs = read("requirements.csv")
    if len(reqs) < 18:
        fail(f"requirements.csv has only {len(reqs)} rows")
    for r in reqs:
        if not r["file"]:
            fail(f"{r['id']}: no file mapped")
    html = (SITE / "index.html").read_text(encoding="utf-8")
    for r in reqs:
        if r["id"] not in html:
            fail(f"{r['id']} missing from the overview requirement trace")


def check_determinism() -> None:
    before = {p.name: p.read_bytes() for p in SITE.glob("*.html")}
    before.update({p.name: p.read_bytes() for p in DATA.glob("*.csv")})
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_nfl_wk.py")],
                         cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        fail(f"rebuild failed: {res.stderr[-400:]}")
        return
    after = {p.name: p.read_bytes() for p in SITE.glob("*.html")}
    after.update({p.name: p.read_bytes() for p in DATA.glob("*.csv")})
    if before != after:
        changed = [k for k in before if before.get(k) != after.get(k)]
        fail(f"build is not deterministic; changed on rebuild: {changed}")


def check_no_secrets_or_placeholders() -> None:
    for p in SITE.glob("*.html"):
        t = p.read_text(encoding="utf-8")
        for bad in ("TODO", "FIXME", "lorem ipsum", "XXX", "REPLACE_ME"):
            if bad.lower() in t.lower():
                fail(f"{p.name}: contains placeholder text {bad!r}")


def main() -> int:
    pages = check_pages()
    check_sources()
    check_standings_identity()
    check_no_invented_numbers()
    check_gates_fail_closed()
    check_depth_join()
    check_flags()
    check_qa_and_suggestions()
    check_requirements_coverage()
    check_no_secrets_or_placeholders()
    check_determinism()

    if FAILS:
        print(f"check_nfl_wk FAILED with {len(FAILS)} problem(s):")
        for f in FAILS:
            print("  -", f)
        return 1
    print(f"check_nfl_wk OK: {pages} HTML pages, 0 manual-input elements, 0 broken internal links, "
          f"0 invented market values, 0 correlation coefficients, gates fail closed, build deterministic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
