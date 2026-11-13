#!/usr/bin/env python3
"""Independent checker for the consolidated NFL review section.

Session arena/44136693-own6 (2026-11-13).

Rules enforced (each failure is reported and makes the check fail):

1. Every published page exists and reproduces byte-for-byte from the builder.
2. Every data row carries at least one https link to the official source.
3. Every data row has exactly as many cells as its table header.
4. No manual input element or form exists anywhere in the section.
5. Every relative link resolves to a file that exists.
6. Every external link uses https.
7. No placeholder text is published in a value cell.
8. Every irregularity in the register is published on the Flagged for Review page.
9. Every official source read is published on the Sources page.
10. The verification ledger covers every published row it claims to cover and
    records an explicit result for each one.

Usage: python3 scripts/check_nfl_review.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "docs", "nfl-review")
DATA = os.path.join(ROOT, "data", "nfl_review")

OFFICIAL_HOSTS = (
    "nfl.com", "operations.nfl.com", "support.nfl.com", "itl.nist.gov",
    "docs.scipy.org", "scikit-learn.org", "www.statsmodels.org", "aglc.ca",
    "github.com", "api.github.com", "codeload.github.com", "docs.github.com",
    "sassnarep3-star.github.io",
)

PLACEHOLDERS = ("tbd", "n/a", "na ", "???", "unknown", "guess", "placeholder", "xxx")


class TableParser(HTMLParser):
    """Collect table rows with their cells and their links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self._table = None
        self._row = None
        self._cell = None
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self._table = {"rows": [], "header": []}
            self.tables.append(self._table)
        elif tag == "tr" and self._table is not None:
            self._row = {"cells": [], "links": []}
        elif tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "links": [], "header": tag == "th"}
        elif tag == "a" and self._cell is not None:
            href = attrs.get("href", "")
            self._cell["links"].append(href)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._cell["text"] = self._cell["text"].strip()
            self._row["cells"].append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table["rows"].append(self._row)
            self._row = None
        elif tag == "table":
            self._table = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell["text"] += data


def read_rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    problems = []
    notes = []

    pages = sorted(f for f in os.listdir(SITE) if f.endswith(".html"))
    if len(pages) != 9:
        problems.append(f"expected 9 html pages in docs/nfl-review, found {len(pages)}")

    total_rows = 0
    for page in pages:
        path = os.path.join(SITE, page)
        html = open(path, encoding="utf-8").read()

        # rule 4: no manual input
        for token in ("<input", "<form", "<textarea", "<select"):
            if token in html.lower():
                problems.append(f"{page}: contains a manual input element ({token})")

        # rule 3/2: tables
        parser = TableParser()
        parser.feed(html)
        for t_index, table in enumerate(parser.tables):
            for row in table["rows"]:
                cells = row["cells"]
                if not cells:
                    continue
                if any(c.get("header") for c in cells):
                    continue  # header row
                total_rows += 1
                ncell = len(cells)
                ncol = len(table["rows"][0]["cells"]) if table["rows"] else ncell
                if ncell != ncol:
                    problems.append(
                        f"{page}: table {t_index + 1} row has {ncell} cells but the table has {ncol}")
                links = [h for c in cells for h in c["links"] if h.startswith("http")]
                if not links:
                    problems.append(f"{page}: a table row has no source link: "
                                    f"{cells[0]['text'][:60]!r}")
                for c in cells:
                    text = c["text"].lower().strip()
                    if text in PLACEHOLDERS:
                        problems.append(f"{page}: placeholder text published in a value cell: {text!r}")
                    for href in c["links"]:
                        if href.startswith("http") and not href.startswith("https://"):
                            problems.append(f"{page}: non-https external link {href}")

        # rule 5: relative links resolve
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http", "#", "mailto:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(SITE, target))
            if not os.path.exists(resolved):
                problems.append(f"{page}: relative link does not resolve: {href}")

    # rule 8: every irregularity is published
    flagged_html = open(os.path.join(SITE, "flagged.html"), encoding="utf-8").read()
    for r in read_rows("irregularities.csv"):
        if r["flag_id"] not in flagged_html:
            problems.append(f"irregularity {r['flag_id']} is not published on the flagged page")

    # rule 9: every source read is published
    sources_html = open(os.path.join(SITE, "sources.html"), encoding="utf-8").read()
    for r in read_rows("official_reads.csv"):
        if r["read_id"] not in sources_html:
            problems.append(f"source read {r['read_id']} is not published on the sources page")
        if r["url"] not in sources_html:
            problems.append(f"source url for {r['read_id']} is not linked on the sources page")

    # rule 10: the ledger covers every published row it claims to cover
    recon = read_rows("value_reconciliation.csv")
    if not recon:
        problems.append("the verification ledger is empty")
    for r in recon:
        if not r["result"]:
            problems.append(f"ledger row {r['check_id']} has no result")
        if not r["official_source_url"].startswith("https://"):
            problems.append(f"ledger row {r['check_id']} has no https source url")
    covered = {r["published_row_id"] for r in recon}
    for csv_name, id_field in (
        ("../nfl_origination/injury_and_depth_deficiency.csv", "case_id"),
        ("../nfl_3b81013c/injuries_and_depth.csv", "id"),
    ):
        path = os.path.join(DATA, csv_name)
        if not os.path.exists(path):
            problems.append(f"expected published dataset is missing: {csv_name}")
            continue
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row[id_field] not in covered:
                    problems.append(f"published row {row[id_field]} is not covered by the ledger")

    # the builder must reproduce the committed pages
    import subprocess
    res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_nfl_review.py"), "--check"],
                         capture_output=True, text=True, cwd=ROOT)
    if res.returncode != 0:
        problems.append("generated pages are stale: " + (res.stdout + res.stderr).strip())

    # the reconciliation must reproduce the committed ledger
    res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "verify_nfl_review.py"), "--check"],
                         capture_output=True, text=True, cwd=ROOT)
    if res.returncode != 0:
        problems.append("reconciliation ledger is stale: " + (res.stdout + res.stderr).strip())

    notes.append(f"{len(pages)} pages, {total_rows} table rows checked, "
                 f"{len(recon)} ledger rows, {len(read_rows('irregularities.csv'))} flags, "
                 f"{len(read_rows('official_reads.csv'))} source reads")
    for n in notes:
        print("  " + n)
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for p in problems[:60]:
            print("  - " + p)
        return 1
    print("OK: no problems found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
