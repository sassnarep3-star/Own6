#!/usr/bin/env python3
"""Structural and evidence-state checks for the assurance dashboard."""
from __future__ import annotations

import csv
import html.parser
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assurance"
DATA = ROOT / "data" / "assurance"
EXPECTED = {"index.html", "strategies.html", "lines.html", "correlations.html", "leaderboard.html",
            "validation.html", "sources.html", "flagged.html", "repo-audit.html"}
OFFICIAL_SUFFIXES = ("nba.com", "github.com", "scikit-learn.org", "scipy.org", "nist.gov",
                     "statsmodels.org", "python.org", "law.go.kr", "draftkings.com")
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def official(url: str) -> bool:
    p = urlparse(url)
    host = (p.hostname or "").lower()
    return p.scheme == "https" and any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES)


class Parser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.h1 = 0
        self.in_tbody = False
        self.in_row = False
        self.row_has_source = False
        self.rows: list[bool] = []
        self.inputs = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_row and official(a["href"]):
                self.row_has_source = True
        if tag == "h1":
            self.h1 += 1
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_has_source = False
        if tag == "input":
            self.inputs += 1

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            self.rows.append(self.row_has_source)
            self.in_row = False
        if tag == "tbody":
            self.in_tbody = False


def load_csv(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    pages = sorted(OUT.glob("*.html"))
    if {p.name for p in pages} != EXPECTED:
        fail(f"expected pages {sorted(EXPECTED)}, found {[p.name for p in pages]}")
    all_ids = {}
    parsed = {}
    for path in pages:
        text = path.read_text(encoding="utf-8")
        p = Parser()
        p.feed(text)
        parsed[path.name] = p
        all_ids[path.name] = p.ids
        if p.h1 != 1:
            fail(f"{path.name}: expected one h1, found {p.h1}")
        if p.inputs:
            fail(f"{path.name}: manual input field is not allowed in the no-input dashboard")
        if "<generator object" in text:
            fail(f"{path.name}: generator repr leaked")
        if re.search(r"^(<<<<<<<|=======|>>>>>>>)", text, re.M):
            fail(f"{path.name}: conflict marker")
        if not p.rows:
            fail(f"{path.name}: no table rows")
        for i, has_source in enumerate(p.rows, 1):
            if not has_source:
                fail(f"{path.name}: table row {i} lacks an official HTTPS source link")
    for name, p in parsed.items():
        for href in p.links:
            u = urlparse(href)
            if u.scheme:
                if u.scheme != "https":
                    fail(f"{name}: non-HTTPS external link {href}")
                continue
            if href.startswith("//"):
                fail(f"{name}: protocol-relative link {href}")
                continue
            target = unquote(u.path)
            resolved = (OUT / name).parent / target if target else (OUT / name)
            if target and not resolved.resolve().exists():
                fail(f"{name}: broken internal link {href}")
            if u.fragment:
                frag_ids = all_ids.get(resolved.resolve().name, set())
                if target and resolved.resolve().name in all_ids and u.fragment not in frag_ids:
                    fail(f"{name}: broken fragment {href}")
    report = json.loads((ROOT / "data/empirical/report.json").read_text(encoding="utf-8"))
    if report["status"] != "not_run" or report["n_observations"] != 0 or report["n_qualified"] != 0 or report["leaderboard"]:
        fail("assurance dashboard requires the bundled fail-closed empty report")
    if any(s["qualified"] for s in report["strategies"]):
        fail("a strategy is qualified without authorized evidence")
    if any(c["status"] != "unverified" for c in report["correlations"]):
        fail("a correlation is published without authorized residuals")
    sources = load_csv("sources.csv")
    if len(sources) != 22 or sum(s["status"] == "verified_direct" for s in sources) != 20:
        fail("source register changed; review direct/partial counts")
    findings = load_csv("findings.csv")
    flagged = (OUT / "flagged.html").read_text(encoding="utf-8")
    for f in findings:
        if f["id"] not in flagged:
            fail(f"finding {f['id']} missing from Flagged for Review")
    row_audit = load_csv("row_audit.csv")
    legacy = sum(r["category"] == "legacy_data" for r in row_audit)
    if str(legacy) not in (OUT / "index.html").read_text(encoding="utf-8"):
        fail("legacy unverified count missing from overview")
    if not (OUT / "assets/style.css").exists():
        fail("stylesheet missing")
    if errors:
        print("ASSURANCE CHECK FAILED")
        for e in errors:
            print(" -", e)
        return 1
    rows = sum(len(p.rows) for p in parsed.values())
    print(f"OK: {len(pages)} assurance pages; {rows} table rows all carry official HTTPS sources; fail-closed report preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
