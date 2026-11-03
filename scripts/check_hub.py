#!/usr/bin/env python3
"""Check the unified hub: internal links resolve, every table body row has an https source link,
no conflict markers, no empty pages. Stdlib only."""
import glob, os, re, sys
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
files = sorted(glob.glob(os.path.join(DOCS, "hub", "*.html")))
if "hub/index.html" not in open(os.path.join(DOCS, "index.html"), encoding="utf-8").read():
    print("ERROR docs/index.html does not link to the hub"); sys.exit(1)
ALLOW = ("nba.com", "github.com", "espn.com", "law.go.kr", "sassnarep3-star.github.io", "docs.github.com",
         "scikit-learn.org", "docs.scipy.org", "statsmodels.org", "itl.nist.gov", "docs.python.org")  # official docs
PRESS = ("mk.co.kr", "sportsbusinessjournal.com", "tsn.ca", "betting.net")  # press: only allowed on the flagged page, as the thing being flagged
errs, rows_total = [], 0

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.links = []; s.in_tbody = False; s.in_tr = False; s.row = None; s.rows = []
    def handle_starttag(s, t, a):
        a = dict(a)
        if t in ("a", "link") and a.get("href"): s.links.append(a["href"])
        if t == "script" and a.get("src"): s.links.append(a["src"])
        if t == "tbody": s.in_tbody = True
        if t == "tr" and s.in_tbody: s.row = []
        if t == "a" and s.row is not None and a.get("href"): s.row.append(a["href"])
    def handle_endtag(s, t):
        if t == "tbody": s.in_tbody = False
        if t == "tr" and s.row is not None: s.rows.append(s.row); s.row = None

for f in files:
    txt = open(f, encoding="utf-8").read()
    rel = os.path.relpath(f, ROOT)
    if re.search(r"^(<<<<<<<|>>>>>>>)", txt, re.M): errs.append(f"{rel}: conflict marker")
    if len(txt) < 1500: errs.append(f"{rel}: suspiciously small")
    p = P(); p.feed(txt)
    for l in p.links:
        u = urlparse(l)
        if u.scheme in ("http", "https"):
            if not (u.netloc.endswith(ALLOW) or (u.netloc.endswith(PRESS) and f.endswith("flagged.html"))): errs.append(f"{rel}: external host not allowlisted: {l}")
            if u.scheme != "https": errs.append(f"{rel}: not https {l}")
        elif u.scheme == "": 
            path = unquote(u.path)
            if not path: continue
            tgt = os.path.normpath(os.path.join(os.path.dirname(f), path))
            if os.path.isdir(tgt): tgt = os.path.join(tgt, "index.html")
            if not os.path.exists(tgt): errs.append(f"{rel}: broken internal link {l}")
    for i, r in enumerate(p.rows, 1):
        rows_total += 1
        if not any(h.startswith("https://") for h in r): errs.append(f"{rel}: table row {i} has no source link")
    # repo-file blob links must point at files that exist in this checkout
    for m in re.finditer(r'href="https://github.com/sassnarep3-star/Own6/blob/main/([^"#?]+)"', txt):
        if not os.path.exists(os.path.join(ROOT, unquote(m.group(1)))): errs.append(f"{rel}: blob link to missing file {m.group(1)}")
print(f"pages={len(files)} table_rows={rows_total} errors={len(errs)}")
for e in errs[:40]: print("ERROR", e)
sys.exit(1 if errs else 0)
