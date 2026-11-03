#!/usr/bin/env python3
"""Offline hub gate: structural coverage and blank-unconfirmed publication.

This is not fact verification. No network access, scraping, or user input.
"""
from __future__ import annotations

import csv
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = {"index", "summary", "results", "standings", "lines", "props", "forward-test",
         "strategies", "correlations", "validation", "sources", "flagged"}
NBA_HOSTS = {"www.nba.com", "official.nba.com"}
REPO_PREFIX = "/sassnarep3-star/Own6/"
# Only these exact upstream documents were read directly. Not a generic GitHub allowlist.
METHOD_REFERENCES = {
    'https://github.com/scikit-learn/scikit-learn/blob/d5a61d1149cb94a936d4b32212330f4ba8f24ce0/sklearn/metrics/_classification.py#L3719-L3724',
    "https://github.com/scipy/scipy/blob/05d068ed2503fad79d5484ae09d55b50a682ec3b/scipy/stats/_stats_py.py#L4656-L4662",
    "https://github.com/scikit-learn/scikit-learn/blob/d5a61d1149cb94a936d4b32212330f4ba8f24ce0/doc/modules/cross_validation.rst#L878-L905",
}


def official(url):
    try:
        u = urlparse(url)
        if u.scheme != "https" or u.username or u.password or u.port not in (None, 443):
            return False
        return url in METHOD_REFERENCES or u.hostname in NBA_HOSTS or (u.hostname == "github.com" and u.path.startswith(REPO_PREFIX))
    except ValueError:
        return False


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.rows = []
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])
        if tag == "table":
            self.table = {"id": a.get("data-dataset"), "rows": []}
            self.tables.append(self.table)
        if tag == "tr":
            self.row = {"attrs": a, "cells": [], "links": []}
        if tag == "td" and self.row is not None:
            self.cell = {"attrs": a, "text": "", "children": []}
            self.row["cells"].append(self.cell)
        elif self.cell is not None:
            self.cell["children"].append(tag)
        if tag == "a" and self.row is not None and a.get("href"):
            self.row["links"].append(a["href"])

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag == "td":
            self.cell = None
        if tag == "tr" and self.row is not None:
            if self.row["cells"]:
                self.rows.append(self.row)
                if self.table is not None:
                    self.table["rows"].append(self.row)
            self.row = None
        if tag == "table":
            self.table = None


def check_page(path, root=ROOT):
    errors = []
    text = path.read_text(encoding="utf-8")
    parser = Parser()
    parser.feed(text)
    rel = path.relative_to(root)
    if parser.h1 != 1:
        errors.append(f"{rel}: expected one h1")
    if re.search(r"^(?:<{7}(?:\s|$)|={7}$|>{7}(?:\s|$))", text, re.M):
        errors.append(f"{rel}: merge conflict markers")
    if re.search(r"<generator object|Math\.erf\(", text):
        errors.append(f"{rel}: generated content failure")
    for target in parser.links:
        u = urlparse(target)
        if u.scheme or u.netloc:
            if not official(target):
                errors.append(f"{rel}: non-primary reference {target}")
            continue
        resolved = (path.parent / unquote(u.path)).resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
            errors.append(f"{rel}: broken/escaping link {target}")
    for index, row in enumerate(parser.rows, 1):
        if not any(official(u) for u in row["links"]):
            errors.append(f"{rel}: row {index} missing official reference")
        for cell in row["cells"]:
            attrs = cell["attrs"]
            if "data-field" in attrs:
                if attrs.get("data-state") != "unverified" or cell["text"] != "" or cell["children"]:
                    errors.append(f"{rel}: nonblank/unmarked unconfirmed field {attrs['data-field']}")
                if set(attrs) != {"data-field", "data-state", "aria-label"}:
                    errors.append(f"{rel}: unsupported attributes in withheld field")
    return errors, parser


def check(root=ROOT):
    errors = []
    policy = json.loads((root / "data/hub_publication_policy.json").read_text())
    if policy.get("mode") != "withhold_unconfirmed" or policy.get("accepted_value_evidence") != []:
        errors.append("Hub must fail closed: no accepted value-level evidence in this release")
    hub = root / "docs/hub"
    files = sorted(hub.glob("*.html"))
    if {p.stem for p in files} != PAGES:
        errors.append("Missing or unexpected hub pages")
    parsed = {}
    for path in files:
        found, parser = check_page(path, root)
        errors += found
        parsed[path.stem] = parser
    observed = {}
    for key, parser in parsed.items():
        for table in parser.tables:
            if table["id"]:
                if table["id"] in observed:
                    errors.append(f"Duplicate dataset table {table['id']}")
                observed[table["id"]] = (key, table)
    expected = {d["id"] for d in policy["datasets"]}
    if set(observed) != expected:
        errors.append("Dataset coverage mismatch")
    for spec in policy["datasets"]:
        if spec["id"] not in observed:
            continue
        key, table = observed[spec["id"]]
        if key != spec["page"]:
            errors.append(f"{spec['id']}: wrong category")
        with (root / spec["path"]).open(newline="", encoding="utf-8") as stream:
            records = list(csv.DictReader(stream))
        if len(table["rows"]) != len(records):
            errors.append(f"{spec['id']}: record coverage mismatch")
        for number, row in enumerate(table["rows"], 1):
            cells = row["cells"]
            if row["attrs"] != {"data-record": str(number), "data-verification": "unverified"}:
                errors.append(f"{spec['id']}: missing record identity/status")
            fields = [c["attrs"].get("data-field") for c in cells[1:-2]]
            if fields != spec["fields"] or len(cells) != len(spec["fields"]) + 3:
                errors.append(f"{spec['id']}: field coverage mismatch")
            if cells and cells[0]["text"] != f"CSV record {number}":
                errors.append(f"{spec['id']}: raw observation leaked into record label")
            if len(cells) >= 2 and cells[-2]["text"] != "UNVERIFIED · withheld":
                errors.append(f"{spec['id']}: missing visible UNVERIFIED flag")
            if not any(u.startswith("https://github.com/sassnarep3-star/Own6/blob/main/" + spec["path"])
                       for u in row["links"]):
                errors.append(f"{spec['id']}: missing raw provenance")
    return errors, sum(len(p.rows) for p in parsed.values())


def main():
    errors, rows = check()
    for error in errors:
        print("ERROR", error)
    print(f"Hub: {len(PAGES)} pages; {rows} source-linked rows; {len(errors)} errors. Link/blank checks are not fact verification.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
