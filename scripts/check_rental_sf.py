#!/usr/bin/env python3
"""Checker for the SF Rent Increase Review site section (docs/rental-sf/).

Verifies, for every page in the section:
  1. Every internal (relative) href/src resolves to an existing file.
  2. Every external href/src uses https:// (no http://, no protocol-relative).
  3. Every table row that contains a dollar figure also contains a
     trace element: an <a href="http…"> source link, a .tag badge
     (COMPUTED / FLAGGED / ANALYSIS / UNVERIFIED …), or the word flag.
  4. Every page carries the anonymization banner and links to both
     flagged.html and sources.html (privacy + review trail).
  5. data/rental_sf/*.json parse.

Exits non-zero on any failure; prints a summary otherwise.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "docs" / "rental-sf"
DATA = ROOT / "data" / "rental_sf"

errors, notes = [], []

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.attrs = []
        self._cur_tr_text, self._cur_tr_has_link, self._cur_tr_has_tag = None, False, False
        self.rows = []
        self.in_banner = False
        self.banner_text = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "link", "script", "img"):
            for key in ("href", "src"):
                if key in a:
                    self.attrs.append((tag, key, a[key]))
                    if tag == "a":
                        self.links.append(a[key])
        if tag == "span" and "tag" in (a.get("class") or ""):
            self._cur_tr_has_tag = True
        if tag == "div" and "banner" in (a.get("class") or ""):
            self.in_banner = True
        if tag == "tr":
            self._cur_tr_text, self._cur_tr_has_link, self._cur_tr_has_tag = "", False, False
        if tag == "a" and self._cur_tr_text is not None:
            self._cur_tr_has_link = True

    def handle_endtag(self, tag):
        if tag == "div" and self.in_banner:
            self.in_banner = False
        if tag == "tr" and self._cur_tr_text is not None:
            self.rows.append((self._cur_tr_text, self._cur_tr_has_link, self._cur_tr_has_tag))
            self._cur_tr_text = None

    def handle_data(self, data):
        if self.in_banner:
            self.banner_text += data
        if self._cur_tr_text is not None:
            self._cur_tr_text += " " + data

def main():
    pages = sorted(SITE.glob("*.html"))
    if not pages:
        print("FAIL: no pages under", SITE); return 1
    total_rows = total_dollar_rows = 0
    for page in pages:
        parser = Page()
        parser.feed(page.read_text(encoding="utf-8"))
        for tag, key, val in parser.attrs:
            if not val or val.startswith(("#", "mailto:", "tel:", "data:")):
                continue
            parsed = urlparse(val)
            if parsed.scheme in ("http", "https"):
                if parsed.scheme != "https":
                    errors.append(f"{page.name}: non-https external link: {val}")
                continue
            if parsed.scheme:  # javascript: etc.
                errors.append(f"{page.name}: disallowed scheme in {tag} {key}: {val}")
                continue
            target = (page.parent / val.split("#")[0]).resolve()
            if not target.exists():
                errors.append(f"{page.name}: broken internal link: {val}")
        # anonymization banner + review links
        if "Anonymized" not in parser.banner_text:
            errors.append(f"{page.name}: missing anonymization banner")
        joined = " ".join(parser.links)
        for needed in ("flagged.html", "sources.html"):
            if needed not in joined:
                errors.append(f"{page.name}: missing link to {needed}")
        # dollar-figure rows must be sourced or labeled
        for text, has_link, has_tag in parser.rows:
            total_rows += 1
            if "$" not in text:
                continue
            total_dollar_rows += 1
            has_flag_word = bool(re.search(r"flag|analysis|computed|unverified|assumption|user brief", text, re.I))
            if not (has_link or has_tag or has_flag_word):
                errors.append(f"{page.name}: dollar figure row lacks trace element: {text.strip()[:110]}")
    for j in sorted(DATA.glob("*.json")):
        try:
            json.loads(j.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{j}: invalid JSON: {e}")
    print(f"pages={len(pages)} table_rows={total_rows} dollar_rows={total_dollar_rows}")
    if errors:
        print("FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: rental-sf section — links resolve, sources https, dollar rows traced, privacy banner present, JSON valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())
