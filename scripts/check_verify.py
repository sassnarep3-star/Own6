#!/usr/bin/env python3
"""Check the verification section.

Fails (exit 1) if:
  * a ledger row lacks an https official source, has an unknown status, or is a MISMATCH;
  * the ledger does not cover every row of the data it claims to verify;
  * an unverified row carries a published value;
  * a built page is missing, unlinked, or has a table data row without an official link;
  * an internal link or asset does not resolve, or a page leaks a Python repr;
  * the summary counts on the index page disagree with the ledger.

Stdlib only. Run: python3 scripts/check_verify.py
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFY = os.path.join(ROOT, "docs", "verify")
LEDGER = os.path.join(ROOT, "data", "verification_official_2026_11_03.csv")
UNVERIFIED = os.path.join(ROOT, "data", "verification_unverified_2026_11_03.csv")
RESULTS = os.path.join(ROOT, "data", "results_2026-11-02.csv")
STANDINGS = os.path.join(ROOT, "data", "standings_live_2026-11-03.csv")

REQUIRED_PAGES = [f"{n}.html" for n in ("index", "results", "standings", "policy", "unverified", "flagged")] + ["assets/verify.css"]
OFFICIAL_HOSTS = ("nba.com", "law.go.kr", "github.com", "espn.com")

errors: list[str] = []


def rd(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.row: list[str] | None = None
        self.rows: list[list[str]] = []
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link") and a.get("href"):
            self.links.append(a["href"])
        if tag == "script" and a.get("src"):
            self.links.append(a["src"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row = []
        if tag == "a" and self.row is not None and a.get("href"):
            self.row.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def check_ledger() -> tuple[list[dict], list[dict]]:
    ledger = rd(LEDGER)
    unv = rd(UNVERIFIED)
    if not ledger:
        errors.append("ledger is empty")
    ids = set()
    for r in ledger:
        cid = r.get("check_id", "")
        if not cid:
            errors.append("ledger row without check_id")
        if cid in ids:
            errors.append(f"duplicate check_id {cid}")
        ids.add(cid)
        if not r["source_url"].startswith("https://") or not any(
            urlparse(r["source_url"]).netloc.endswith(h) for h in OFFICIAL_HOSTS
        ):
            errors.append(f"{cid}: source is not an allowlisted official https URL")
        if r["result"].strip().lower() == "mismatch":
            errors.append(f"{cid}: recorded MISMATCH is an open failure")
        elif r["result"].strip().lower() != "match":
            errors.append(f"{cid}: invalid status {r['result']!r}")
        if not r["checked_on"].startswith("2026-"):
            errors.append(f"{cid}: missing/invalid checked_on date")
        if not r["published_value"].strip() or not r["official_value"].strip():
            errors.append(f"{cid}: empty published or official value")

    # coverage: every published row must appear in the ledger
    result_ids = {r["check_id"] for r in ledger}
    for row in rd(RESULTS):
        if f"R-{row['game_id']}" not in result_ids:
            errors.append(f"results row {row['game_id']} is not covered by the ledger")
    for row in rd(STANDINGS):
        if f"S-{row['team_abbr']}" not in result_ids:
            errors.append(f"standings row {row['team_abbr']} is not covered by the ledger")

    for r in unv:
        if r["published_value"].strip():
            errors.append("an unverified row carries a published value")
        if not r["official_reference"].startswith("https://"):
            errors.append("an unverified row lacks an official reference link")
        if not r["reason"].strip():
            errors.append("an unverified row lacks a reason")
    return ledger, unv


def check_pages(ledger: list[dict], unv: list[dict]) -> None:
    files = sorted(glob.glob(os.path.join(VERIFY, "*.html")))
    names = {os.path.basename(f)[:-5] for f in files}
    for req in REQUIRED_PAGES:
        if not os.path.exists(os.path.join(VERIFY, req)):
            errors.append(f"missing required file docs/verify/{req}")

    total_rows = 0
    for f in files:
        txt = open(f, encoding="utf-8").read()
        rel = os.path.relpath(f, ROOT)
        if len(txt) < 1500:
            errors.append(f"{rel}: suspiciously small")
        if re.search(r"^(<<<<<<<|=======|>>>>>>>)", txt, re.M):
            errors.append(f"{rel}: conflict marker")
        if re.search(r"<generator object", txt):
            errors.append(f"{rel}: python repr leak")
        p = Rows()
        p.feed(txt)
        for href in p.links:
            u = urlparse(href)
            if u.scheme in ("http", "https"):
                if not any(u.netloc.endswith(h) for h in OFFICIAL_HOSTS):
                    errors.append(f"{rel}: non-official external host {href}")
                if u.scheme != "https":
                    errors.append(f"{rel}: non-https link {href}")
            elif u.scheme == "":
                target = os.path.normpath(os.path.join(VERIFY, unquote(u.path)))
                if u.path and not os.path.exists(target):
                    errors.append(f"{rel}: broken internal link {href}")
        for i, row in enumerate(p.rows, 1):
            total_rows += 1
            if not any(h.startswith("https://") for h in row):
                errors.append(f"{rel}: table row {i} has no official source link")
        # every page must be reachable from the index
        index = open(os.path.join(VERIFY, "index.html"), encoding="utf-8").read()
        base = os.path.basename(f)
        if base != "index.html" and base not in index:
            errors.append(f"{rel}: page is not linked from the verification index")

    matches = sum(1 for r in ledger if r["result"].lower() == "match")
    index = open(os.path.join(VERIFY, "index.html"), encoding="utf-8").read()
    for expected in (str(len(ledger)), f"{matches}/{len(ledger)}", str(len(unv))):
        if expected not in index:
            errors.append(f"index summary does not show expected count {expected}")
    print(f"pages={len(files)} table_rows={total_rows} checks={len(ledger)} "
          f"matches={matches} unverified={len(unv)}")


def main() -> int:
    ledger, unv = check_ledger()
    check_pages(ledger, unv)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for e in errors[:60]:
            print(" -", e)
        return 1
    print("PASS: ledger complete and consistent; every row source-linked; links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
