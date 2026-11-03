#!/usr/bin/env python3
"""Offline hub publication gate: structure and provenance, not fact verification.

Every body row needs a scoped official reference or this project's primary
record. ESPN/press and historical citations may be linked but never qualify a
row. Declared unverified value cells must be genuinely empty. Hostname suffix
spoofs, credentials, non-HTTPS links and project-path escapes are rejected.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "/sassnarep3-star/Own6/"
OFFICIAL_DOMAINS = (
    "nba.com", "law.go.kr", "docs.github.com", "scikit-learn.org",
    "docs.scipy.org", "scipy.org", "statsmodels.org", "nist.gov", "docs.python.org",
)
SECONDARY_DOMAINS = (
    "espn.com", "mk.co.kr", "sportsbusinessjournal.com", "tsn.ca", "betting.net",
    "yahoo.com", "sassnarep3-star.github.io", "aglc.ca",
)
SOURCE_KINDS = {"official-reference", "project-record", "secondary-record"}
# Pinned primary-method references used by the existing strict hub owner.
METHOD_REFERENCES = {
    "https://github.com/scikit-learn/scikit-learn/blob/d5a61d1149cb94a936d4b32212330f4ba8f24ce0/sklearn/metrics/_classification.py#L3719-L3724",
    "https://github.com/scipy/scipy/blob/05d068ed2503fad79d5484ae09d55b50a682ec3b/scipy/stats/_stats_py.py#L4656-L4662",
    "https://github.com/scikit-learn/scikit-learn/blob/d5a61d1149cb94a936d4b32212330f4ba8f24ce0/doc/modules/cross_validation.rst#L878-L905",
}



def host_in(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def safe_https(url):
    try:
        u = urlparse(url)
        return (u.scheme == "https" and bool(u.hostname) and not u.username and not u.password
                and u.port in (None, 443) and not any(c.isspace() for c in url)
                and "\\" not in url)
    except ValueError:
        return False


def project_record(url):
    if not safe_https(url):
        return False
    u = urlparse(url)
    # GitHub is primary only for this repository, not arbitrary user content.
    path = unquote(u.path)
    return (u.hostname == "github.com" and (path == PROJECT.rstrip("/") or path.startswith(PROJECT))
            and not any(p in (".", "..") for p in path.split("/")))


def official_reference(url):
    return safe_https(url) and (host_in(urlparse(url).hostname, OFFICIAL_DOMAINS) or url in METHOD_REFERENCES)


def qualifies(url, kind):
    # Honor explicit roles when present. Legacy templates have no role attribute:
    # infer reference category only, never factual verification.
    if kind is None:
        return official_reference(url) or project_record(url)
    return ((kind == "project-record" and project_record(url))
            or (kind == "official-reference" and official_reference(url)))


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.h1 = 0
        self.rows = []
        self.row = None
        self.cell = None
        self.headers = 0
        self.body = False
        self.current_width = 0
        self.table_id = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "table":
            self.headers = 0
            self.table_id = attrs.get("id")
        if tag == "th":
            self.headers += 1
        if tag == "tbody":
            self.body = True
        if tag == "tr" and self.body:
            self.row = {"cells": [], "links": [], "headers": self.headers, "table": self.table_id}
        if tag == "td" and self.row is not None:
            self.cell = {"text": "", "unverified": (attrs.get("data-evidence") == "unverified" or attrs.get("data-state") == "unverified"), "markup": False}
        elif self.cell is not None:
            # Empty unverified fields may not hide values in child markup.
            self.cell["markup"] = True
        if tag == "a" and attrs.get("href"):
            item = (attrs["href"], attrs.get("data-source-kind"))
            self.links.append(item)
            if self.row is not None:
                self.row["links"].append(item)
        for name in ("src", "href"):
            if attrs.get(name) and not (tag == "a" and name == "href"):
                self.links.append((attrs[name], None))

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data

    def handle_endtag(self, tag):
        if tag == "td" and self.cell is not None and self.row is not None:
            self.row["cells"].append(self.cell)
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.body = False


def check_page(path, root=ROOT):
    path, root = Path(path), Path(root).resolve()
    errors = []
    label = str(path.relative_to(root))
    text = path.read_text(encoding="utf-8")
    p = Page()
    p.feed(text)
    if p.h1 != 1:
        errors.append(f"{label}: expected one h1, got {p.h1}")
    if re.search(r"^(?:<{7}|>{7}|={7}$)", text, re.M) or "<generator object" in text:
        errors.append(f"{label}: conflict marker or malformed generated content")
    for url, kind in p.links:
        u = urlparse(url)
        if u.scheme or u.netloc:
            if not safe_https(url):
                errors.append(f"{label}: external link is not safe HTTPS: {url}")
                continue
            host = u.hostname
            api_record = (host == "api.github.com" and (u.path == "/repos/sassnarep3-star/Own6"
                          or u.path.startswith("/repos/sassnarep3-star/Own6/")))
            if not (official_reference(url) or project_record(url) or api_record or host_in(host, SECONDARY_DOMAINS)):
                errors.append(f"{label}: unrecognized source host or project path: {url}")
            if kind and kind not in SOURCE_KINDS:
                errors.append(f"{label}: unknown source kind: {kind}")
            if kind in {"official-reference", "project-record"} and not qualifies(url, kind):
                errors.append(f"{label}: source role does not match host/path: {url}")
            if host == "github.com" and project_record(url):
                pathpart = unquote(u.path)
                prefix = PROJECT + "blob/main/"
                if pathpart.startswith(prefix):
                    target = (root / pathpart[len(prefix):]).resolve()
                    if not target.is_relative_to(root) or not target.is_file():
                        errors.append(f"{label}: missing project source file: {url}")
        else:
            if not u.path:
                continue
            target = (path.parent / unquote(u.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            if u.path.startswith("/") or not target.is_relative_to(root) or not target.is_file():
                errors.append(f"{label}: broken or escaping internal link: {url}")
    for i, row in enumerate(p.rows, 1):
        cells = row["cells"]
        if len(cells) != row["headers"]:
            errors.append(f"{label}: row {i} has {len(cells)} cells for {row['headers']} headers")
        if not any(qualifies(url, kind) for url, kind in row["links"]):
            errors.append(f"{label}: row {i} lacks a scoped official/project source")
        for cell in cells:
            if cell["unverified"] and (cell["text"].strip() or cell["markup"]):
                errors.append(f"{label}: row {i} has a nonblank unverified value cell")
    return errors, len(p.rows)


def check_hub(root=ROOT):
    root = Path(root).resolve()
    errors, count = [], 0
    pages = sorted((root / "docs/hub").glob("*.html"))
    expected = {"index", "summary", "results", "standings", "lines", "props", "forward-test", "strategies", "correlations", "validation", "sources", "flagged"}
    if {p.stem for p in pages} != expected:
        errors.append("Hub must contain the 12 expected category pages")
    landing = root / "docs/index.html"
    if not landing.exists() or "hub/index.html" not in landing.read_text(encoding="utf-8"):
        errors.append("Landing page must link to the hub")
    for page in pages:
        issues, rows = check_page(page, root)
        errors.extend(issues)
        count += rows
    return errors, len(pages), count


if __name__ == "__main__":
    errors, pages, rows = check_hub()
    print(f"pages={pages} table_rows={rows} errors={len(errors)} (structural checks, not factual verification)")
    for error in errors:
        print("ERROR", error)
    sys.exit(bool(errors))
