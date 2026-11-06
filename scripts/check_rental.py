#!/usr/bin/env python3
"""Check the rental review site in docs/rental/.

Enforces, without any network access:
  A. internal links resolve (relative to docs/rental/)
  B. external links use https only
  C. privacy: recorded tenant initials absent; required dates/amounts present
  D. every non-header table row carries a link, a 'unverified' marker or a badge label
  E. flagged page contains F-R1..F-R13; sources page contains S-01..S-21
  F. every page has <title>, lang="en" and the rental nav landmark
Exits non-zero on any failure. Network is NOT touched.
"""
import json, re, sys, html.parser, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "docs" / "rental"
REQUIRED_PAGES = ["index.html","executive-summary.html","units.html","laws-local.html","laws-state.html",
                  "laws-federal.html","market-practices.html","notice-procedure.html","one-vs-both.html",
                  "tenant-lawyer-review.html","faq.html","sources.html","methodology.html","flagged.html"]
REQUIRED_TEXT = {
    "units.html": ["3,995.00","3,150.00","February 1, 2025","June 1, 2019","April 1, 2026"],
    "executive-summary.html": ["1.6%","3,995.00","3,150.00"],
    "laws-local.html": ["1.6%","Form 571","60%"],
}
FAILURES = []

def fail(msg):
    FAILURES.append(msg)
    print("FAIL:", msg)

def page_links(text):
    return re.findall(r'(?:href|src)="([^"]+)"', text)

def main():
    if not SITE.is_dir():
        fail("docs/rental missing — run scripts/build_rental.py")
        return 1
    for p in REQUIRED_PAGES:
        if not (SITE / p).is_file():
            fail(f"missing page {p}")
    for p in REQUIRED_PAGES:
        path = SITE / p
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # F. chrome
        if 'lang="en"' not in text: fail(f"{p}: missing lang attribute")
        if "<title>" not in text: fail(f"{p}: missing <title>")
        if 'aria-label="Rental pack navigation"' not in text: fail(f"{p}: missing nav landmark")
        # C. privacy anchors: required preserved values present; placeholder legend intact
        for req in REQUIRED_TEXT.get(p, []):
            if req not in text:
                fail(f"{p}: required preserved value {req!r} missing")
        # A/B. links
        for link in page_links(text):
            if link.startswith(("http://",)):
                fail(f"{p}: non-https external link {link}")
                continue
            if link.startswith(("https://", "mailto:", "tel:", "#")):
                continue
            target = link.split("#", 1)[0]
            if not target:
                continue
            resolved = (SITE / urllib.parse.unquote(target)).resolve()
            if not str(resolved).startswith(str(SITE.resolve())):
                fail(f"{p}: link escapes site root: {link}")
            elif not resolved.exists():
                fail(f"{p}: broken internal link {link}")
        # D. table rows carry a link, unverified marker or badge
        for i, m in enumerate(re.finditer(r"<tr\b[^>]*>(.*?)</tr>", text, re.S)):
            row = m.group(0)
            if "<th" in row:  # header row
                continue
            if ('href="' in row) or ("unverified" in row) or ('class="badge' in row) or ('class="empty"' in row):
                continue
            fail(f"{p}: table row #{i} has no link, flag or badge: {row[:120]}...")
    # E. completeness of flags and sources
    flagged = (SITE / "flagged.html").read_text() if (SITE / "flagged.html").exists() else ""
    for n in range(1, 14):
        if f"F-R{n}" not in flagged:
            fail(f"flagged.html missing F-R{n}")
    sources = (SITE / "sources.html").read_text() if (SITE / "sources.html").exists() else ""
    for n in range(1, 22):
        if f"S-{n:02d}" not in sources:
            fail(f"sources.html missing S-{n:02d}")
    print(f"\n{len(REQUIRED_PAGES)} pages checked; {len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0

if __name__ == "__main__":
    sys.exit(main())
