#!/usr/bin/env python3
"""Link & source-integrity check for the docs/ site.

Checks per generated HTML page:
  1. every internal href resolves to an existing file (relative to docs/)
  2. every external href is on the verified official-source allowlist
  3. every <tr> in a data table contains at least one source <a href> (row-level sourcing rule)
Exits non-zero on any failure.
"""
import os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs", "own6")

ALLOWED_HOSTS = {
    "www.nba.com", "nba.com", "cdn.nba.com", "pr.nba.com", "stats.nba.com",
    "www.espn.com", "espn.com", "sports.core.api.espn.com", "site.api.espn.com",
    "a.espncdn.com",
    # methodology citations (non-data, editorial references)
    "www.researchgate.net", "quantresearch.org", "dash.harvard.edu",
    "arxiv.org", "www.nessis.org", "faculty.wharton.upenn.edu", "nbaanalytic.com",
    "www.athletepath.com",
}

errors, stats = [], dict(pages=0, links=0, rows=0, row_links=0)

for fn in sorted(os.listdir(DOCS)):
    if not fn.endswith(".html"):
        continue
    path = os.path.join(DOCS, fn)
    text = open(path, encoding="utf-8").read()
    stats["pages"] += 1

    # strip nav/footer noise? no — check everything
    for m in re.finditer(r'href="([^"]+)"', text):
        href = m.group(1)
        stats["links"] += 1
        if href.startswith("http://") or href.startswith("https://"):
            host = urllib.parse.urlparse(href).netloc
            if host not in ALLOWED_HOSTS:
                errors.append(f"{fn}: external host not allowlisted: {host} ({href})")
        elif href.startswith("#") or href.startswith("mailto:"):
            continue
        else:
            target = href.split("#")[0]
            if not target:
                continue
            tpath = os.path.normpath(os.path.join(DOCS, target))
            if not os.path.exists(tpath):
                errors.append(f"{fn}: broken internal link: {href}")

    # row-level sourcing: every <tr> inside <tbody> must contain >=1 <a href
    for tr in re.findall(r"<tr>(.*?)</tr>", text, flags=re.S):
        if "<td>" not in tr:
            continue  # header row
        stats["rows"] += 1
        if re.search(r'<a href="[^"]+"', tr):
            stats["row_links"] += 1
        else:
            errors.append(f"{fn}: table row without source link: {tr[:120]}...")

print(f"pages={stats['pages']} links={stats['links']} data_rows={stats['rows']} rows_with_source={stats['row_links']}")
if errors:
    print(f"FAIL: {len(errors)} issue(s)")
    for e in errors[:40]:
        print(" -", e)
    sys.exit(1)
print("PASS: all internal links resolve, external hosts allowlisted, every data row sourced")
