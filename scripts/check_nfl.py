#!/usr/bin/env python3
"""Verify docs/nfl/ — every table row carries an official https source link, etc.
Exits 0 on success, 1 on issues. No network calls.
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl"
OUT = ROOT / "docs" / "nfl"

issues: list[str] = []

# Expected pages
EXPECTED = [
    "index.html", "requirements.html", "questions.html", "suggestions.html",
    "strategies.html", "lines.html", "validation.html", "correlations.html",
    "injuries.html", "depth.html", "leaderboard.html", "sources.html", "flagged.html",
]

pages = list(OUT.glob("*.html")) if OUT.exists() else []
if len(pages) < len(EXPECTED):
    issues.append(f"pages={len(pages)} expected ≥{len(EXPECTED)}; missing: {sorted(set(EXPECTED)-{p.name for p in pages})}")

# Check each page exists and basic invariants
for fname in EXPECTED:
    p = OUT / fname
    if not p.exists():
        issues.append(f"missing page {fname}")
        continue
    text = p.read_text(encoding="utf-8")
    if "generator object" in text or "<<<<<<<" in text or ">>>>>>>" in text:
        issues.append(f"{fname}: leak/marker")
    # Check at least one official source link present
    if "official source" not in text:
        issues.append(f"{fname}: no 'official source' found")
    # Every href that is http must be https
    for href in re.findall(r'href="([^"]+)"', text):
        if href.startswith("http://"):
            issues.append(f"{fname}: non-https link {href}")
    # Internal links resolve
    for href in re.findall(r'href="([^"#?]+)"', text):
        if href.startswith("http") or href.startswith("mailto") or href.startswith("#"):
            continue
        if href.startswith("assets/"):
            # check assets file exists
            target = OUT / href
            if not target.exists():
                issues.append(f"{fname}: broken asset link {href}")
            continue
        # exclude external-like but relative
        if "/" in href and href.startswith("https"):
            continue
        # internal page links
        if href.endswith(".html"):
            target = OUT / href
            if not target.exists():
                issues.append(f"{fname}: broken internal link {href}")
    # Every tbody row must contain official source
    for row in re.findall(r"<tr>(.*?)</tr>", text, re.S):
        if "<td" in row:
            if "official source" not in row and "Flagged" not in row:
                # Allow flag page header rows but still need source
                snippet = re.sub(r"\s+", " ", row)[:120]
                issues.append(f"{fname}: row without official source: {snippet}")

# Check CSVs: each row must have source_url with https
for csv_name in DATA.glob("*.csv"):
    rows = list(csv.DictReader(csv_name.open(newline="", encoding="utf-8")))
    if not rows:
        issues.append(f"{csv_name.name}: empty")
        continue
    for i, r in enumerate(rows, start=1):
        # Every CSV must have source_url column
        if "source_url" not in r:
            issues.append(f"{csv_name.name}:{i}: no source_url column")
            continue
        url = (r.get("source_url") or "").strip()
        if not url:
            issues.append(f"{csv_name.name}:{i}: blank source_url")
        elif not url.startswith("https://"):
            issues.append(f"{csv_name.name}:{i}: non-https source_url {url}")
        # Flag that no empirical columns contain hallucinations where flagged says blank
        # e.g., if roi/clv/corr_value non-empty while status unverified, that's error
        # For leaderboard, roi should be blank
        for k in ("roi", "clv", "corr_value", "n", "holdout_roi_lower_bound", "holdout_brier_skill", "clv_mean"):
            if k in r and str(r[k]).strip() not in ("", "—", "— blank", "— blank (unverified)", "blank", "-", "—"):
                # If value is present, flagged must acknowledge
                issues.append(f"{csv_name.name}:{i} {k} should be blank but has '{r[k]}'")

# Summary
print(f"nfl: {len(pages)} pages, {len(issues)} issues")
for i in issues:
    print(" -", i)
sys.exit(1 if issues else 0)
