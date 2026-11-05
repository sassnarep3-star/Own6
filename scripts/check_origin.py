#!/usr/bin/env python3
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; OUT = ROOT/"docs"/"origin"
issues=[]
pages=list(OUT.glob("*.html"))
if len(pages)<8: issues.append(f"pages={len(pages)}")
for p in pages:
    t=p.read_text(encoding="utf-8")
    if "generator object" in t or "<<<<<<<" in t: issues.append(f"{p.name}: leak/marker")
    for href in re.findall(r'href="([^"]+)"', t):
        if href.startswith("http"):
            if not href.startswith("https://"): issues.append(f"{p.name}: non-https {href}")
        elif not (OUT/href.split("#")[0]).exists() and href: issues.append(f"{p.name}: broken {href}")
    for row in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        if "<td" in row and "official source" not in row: issues.append(f"{p.name}: row without official source: {row[:80]}")
print(f"origin: {len(pages)} pages, {len(issues)} issues")
for i in issues: print(" -",i)
sys.exit(1 if issues else 0)
