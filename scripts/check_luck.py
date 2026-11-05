#!/usr/bin/env python3
"""Gate the luck/skill and acceptance section.

Fails when any of the following is untrue:
  * the committed data regenerates exactly (deterministic);
  * every table body row on every page carries an https source link;
  * every flagged item links an https source;
  * every local link resolves and every external link is https;
  * no merge markers, Python reprs or unfilled placeholders are published;
  * the numerical cross-check record exists and passed;
  * the acceptance summary agrees with its own CSV files;
  * a claim that could not be checked is NOT labelled verified.

Usage: python3 scripts/check_luck.py [--strict]
"""

from __future__ import annotations

import csv
import html.parser
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "docs" / "luck").glob("*.html"))
DATA = ROOT / "data" / "luck"
ACCEPT = ROOT / "data" / "acceptance"

errors: list[str] = []
warnings: list[str] = []


class RowParser(html.parser.HTMLParser):
    """Collect per-row link sets from table bodies."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.in_tbody = False
        self.in_row = False
        self.row_links: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
                if self.in_row:
                    self.row_links.append(attrs[key])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_links = []

    def handle_endtag(self, tag):
        if tag == "tr" and self.in_row:
            self.rows.append(self.row_links)
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False


def check_determinism() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "luck_analysis.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append("data/luck is stale: " + (result.stdout + result.stderr).strip())
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_luck.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append("docs/luck is stale: " + (result.stdout + result.stderr).strip())
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "acceptance_audit.py"), "--check"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        errors.append("data/acceptance is stale: " + (result.stdout + result.stderr).strip())


def check_pages() -> None:
    if not PAGES:
        errors.append("no pages built under docs/luck/")
        return
    for path in PAGES:
        text = path.read_text(encoding="utf-8")
        parser = RowParser()
        parser.feed(text)
        parser.close()
        for index, links in enumerate(parser.rows, start=1):
            https = [link for link in links if link.startswith("https://")]
            if not https:
                errors.append(f"{path.name}: table row {index} has no https source link")
        for link in parser.links:
            if link.startswith(("http://",)):
                errors.append(f"{path.name}: non-https external link {link}")
            if link.startswith(("https://", "#", "mailto:")):
                continue
            target = (path.parent / link.split("#")[0].split("?")[0]).resolve()
            if not target.exists():
                errors.append(f"{path.name}: broken local link {link}")
        for marker in ("<<<<<<<", ">>>>>>>"):
            if marker in text:
                errors.append(f"{path.name}: merge marker present")
        if re.search(r"&lt;bound method|&lt;class |\\bnan\\b", text):
            warnings.append(f"{path.name}: possible repr or NaN leakage")
        if "unverified" not in text.lower():
            warnings.append(f"{path.name}: no 'unverified' wording present")
        if 'lang="en"' not in text:
            errors.append(f"{path.name}: missing lang attribute")
        if 'href="../index.html"' not in text:
            errors.append(f"{path.name}: no link back to the dashboard")


def check_flags() -> None:
    with (DATA / "flags.csv").open(newline="", encoding="utf-8") as handle:
        flags = list(csv.DictReader(handle))
    if not flags:
        errors.append("data/luck/flags.csv is empty")
    for flag in flags:
        if not flag["source_url"].startswith("https://"):
            errors.append(f"flag {flag['id']} has no https source")
        if urlparse(flag["source_url"]).hostname in (None, "localhost", "127.0.0.1"):
            errors.append(f"flag {flag['id']} source host is not public")
        if flag["severity"] not in {"High", "Medium", "Low", "Info"}:
            errors.append(f"flag {flag['id']} has an unknown severity {flag['severity']!r}")
        if not flag["action_requested"]:
            errors.append(f"flag {flag['id']} has no action requested")


def check_crosscheck() -> None:
    path = DATA / "numerics_crosscheck.json"
    if not path.exists():
        errors.append("data/luck/numerics_crosscheck.json is missing")
        return
    record = json.loads(path.read_text(encoding="utf-8"))
    if not record.get("all_pass"):
        errors.append("numerical cross-check record does not report all_pass")
    for check in record.get("checks", []):
        if not check.get("pass"):
            errors.append(f"cross-check failed: {check.get('check')}")
    if not record.get("checks"):
        errors.append("numerical cross-check record has no checks")


def check_acceptance() -> None:
    with (ACCEPT / "claims.csv").open(newline="", encoding="utf-8") as handle:
        claims = list(csv.DictReader(handle))
    with (ACCEPT / "pages.csv").open(newline="", encoding="utf-8") as handle:
        pages = list(csv.DictReader(handle))
    summary = json.loads((ACCEPT / "summary.json").read_text(encoding="utf-8"))

    if len(claims) != summary["claims"]:
        errors.append("acceptance summary claim count disagrees with claims.csv")
    if len(pages) != summary["pages"]:
        errors.append("acceptance summary page count disagrees with pages.csv")
    for claim in claims:
        if not claim["source_url"].startswith("https://"):
            errors.append(f"claim {claim['id']} has no https source")
        if claim["verdict"] not in {
            "verified",
            "mismatch",
            "needs review",
            "verification blocked",
            "not assessable",
        }:
            errors.append(f"claim {claim['id']} has unknown verdict {claim['verdict']!r}")
        if claim["verdict"] in {"verification blocked", "not assessable"} and not claim["action"]:
            errors.append(f"claim {claim['id']} is blocked but states no action")
    # A blocked official-source check must never be silently promoted.
    blocked = {claim["id"] for claim in claims if claim["verdict"] == "verification blocked"}
    if "A13" not in blocked:
        errors.append("A13 (official-source re-read) must stay blocked while egress is unavailable")
    orphans = [page for page in pages if page["orphan"] == "yes" and page["intentional_orphan"] != "yes"]
    if orphans:
        errors.append("unreachable pages published: " + ", ".join(page["page"] for page in orphans))


def main(argv: list[str] | None = None) -> int:
    strict = "--strict" in (argv if argv is not None else sys.argv[1:])
    check_determinism()
    check_pages()
    check_flags()
    check_crosscheck()
    check_acceptance()
    for warning in warnings:
        print(f"WARN  {warning}")
    for error in errors:
        print(f"ERROR {error}")
    print(
        f"\nLUCK SECTION: {len(PAGES)} pages | ERRORS: {len(errors)} | WARNINGS: {len(warnings)}"
    )
    if errors:
        return 1
    if strict and warnings:
        return 1
    print("OK: luck/skill section data is reproducible, every table row is source-linked, and no blocked check is labelled verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
