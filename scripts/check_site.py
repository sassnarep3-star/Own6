#!/usr/bin/env python3
"""Check the data and the built site. Exits non-zero on any failure.

Data rules:
  * Every verified row has a source_url on an official host (nba.com or law.go.kr).
  * Every unverified policy row leaves its official value and official link blank.
  * Every flag has an https source link.
Site rules:
  * Every internal href/src resolves to a file in docs/ (no broken links).
  * Every external link uses https.
  * Every page has exactly one <h1>.
"""
import html.parser
import json
import pathlib
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs" / "verified"  # this session's output only
OFFICIAL_HOSTS = {"www.nba.com", "www.law.go.kr"}

errors = []


def fail(msg):
    errors.append(msg)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def check_data():
    for name in ["games.json", "legal_kr.json"]:
        for i, r in enumerate(load(name)["rows"]):
            url = r.get("source_url", "")
            host = urlparse(url).hostname or ""
            if not r.get("verified"):
                fail(f"{name} row {i}: not verified; should not be published as verified")
            if host not in OFFICIAL_HOSTS:
                fail(f"{name} row {i}: source '{url}' is not an official host")
    for i, r in enumerate(load("nba_policy.json")["rows"]):
        if r["verified"]:
            host = urlparse(r["official_source_url"]).hostname or ""
            if host not in OFFICIAL_HOSTS:
                fail(f"nba_policy row {i}: verified but official host is '{host}'")
        else:
            if r["official_statement_verified"] or r["official_source_url"]:
                fail(f"nba_policy row {i}: unverified row has an official value; must be blank")
            if not r["secondary_source_url"]:
                fail(f"nba_policy row {i}: unverified row needs a source link to check")
    for i, r in enumerate(load("flags.json")["rows"]):
        if not str(r["source_url"]).startswith("https://"):
            fail(f"flags row {r.get('id', i)}: source is not https")
    for i, r in enumerate(load("strategies.json")["rows"]):
        if not r.get("verified"):
            fail(f"strategies row {i}: a strategy row must be verified to appear")


class LinkCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.h1 = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        for key in ("href", "src"):
            if key in a and a[key]:
                self.links.append(a[key])


def check_site():
    pages = sorted(DOCS.glob("*.html"))
    if not pages:
        fail("no HTML pages in docs/verified/")
    for page in pages:
        p = LinkCollector()
        p.feed(page.read_text(encoding="utf-8"))
        if p.h1 != 1:
            fail(f"{page.name}: expected exactly one <h1>, found {p.h1}")
        for link in p.links:
            if link.startswith("#") or link.startswith("mailto:"):
                continue
            parsed = urlparse(link)
            if parsed.scheme in ("http", "https"):
                if parsed.scheme != "https":
                    fail(f"{page.name}: external link not https: {link}")
                continue
            if parsed.scheme or link.startswith("//"):
                fail(f"{page.name}: unsupported link scheme: {link}")
                continue
            target = (page.parent / parsed.path).resolve()
            if not target.exists():
                fail(f"{page.name}: broken internal link -> {link}")
    return len(pages)


if __name__ == "__main__":
    check_data()
    n = check_site()
    if errors:
        print("FAILED")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"OK: data rules pass; {n} pages, no broken internal links, all external links https.")
