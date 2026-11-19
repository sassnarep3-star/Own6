#!/usr/bin/env python3
"""Verifier for the d6a947cb pack. Exits 1 on any failure, printing every failure.

Checks:
  1. Every register parses with a consistent field count.
  2. Every requirement row with a source cites an official host (nfl.com or operations.nfl.com).
  3. Every official re-read cites an official URL, its raw excerpt exists, and its sha256 matches capture_log.csv.
  4. Every question and source row has a link (official or repo host) and every source is https.
  5. Statuses come from the allowed vocabulary.
  6. Every suggestion is pending a human choice and not implemented; every flagged item blocks nothing.
  7. The built site: all pages exist, every internal link resolves, counts on the landing match the registers.
  8. No banned promotional wording anywhere in the published pages or the executive summary.
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_d6a947cb"
SITE = ROOT / "docs" / "nfl-d6a947cb"
EXEC = ROOT / "NFL_D6A947CB_EXECUTIVE_SUMMARY.md"
OFFICIAL = {"www.nfl.com", "operations.nfl.com"}
REPO = {"github.com", "api.github.com"}
ALLOWED_STATUS = {"met", "partially_met", "blocked", "rejected_adopted", "not_run", "needs_review", "needs_decision"}
BANNED = [
    r"\bguaranteed (winner|profit|return)s?\b",
    r"\block of the (week|day)\b",
    r"\bbeat the closing line\b",
    r"\bwe (beat|beats) the (market|closing line)\b",
    r"\bprofitable (strategy|system|bets?)\b",
    r"\bsure (bet|thing)\b",
]
PAGES = ["index.html", "requirements.html", "questions.html", "suggestions.html", "flagged.html",
         "verification.html", "sources.html", "repo-review.html", "executive-summary.html"]


def rows(name: str) -> list[dict]:
    p = DATA / name
    with p.open(newline="", encoding="utf-8") as fh:
        raw = list(csv.reader(fh))
    head = raw[0]
    bad = [i for i, r in enumerate(raw[1:], start=2) if len(r) != len(head)]
    if bad:
        raise ValueError(f"{name}: rows with wrong field count at lines {bad}")
    return [dict(zip(head, r)) for r in raw[1:]]


def host(url: str) -> str:
    return urlparse(url).netloc.lower()


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


def main() -> int:
    errs: list[str] = []

    def err(msg: str) -> None:
        errs.append(msg)

    try:
        reqs = rows("requirements.csv")
        reads = rows("official_reads_2026_11_19.csv")
        caps = rows("capture_log.csv") if (DATA / "capture_log.csv").exists() else []
        qs = rows("questions.csv")
        sugg = rows("suggestions.csv")
        rfs = rows("repo_findings.csv")
        srcs = rows("sources.csv")
        rows("ledger_comparison.csv")
    except (OSError, ValueError) as exc:
        print(f"FAIL parse: {exc}")
        return 1

    if len(reqs) != 96:
        err(f"requirements.csv has {len(reqs)} rows; expected 96 (owner ledger rows)")
    for r in reqs:
        if r["source_url"] and host(r["source_url"]) not in OFFICIAL:
            err(f"{r['req_id']}: source host {host(r['source_url'])} is not an official NFL host")
        if r["d6a_status"] not in ALLOWED_STATUS:
            err(f"{r['req_id']}: status {r['d6a_status']!r} not in allowed vocabulary")
        if not r["source_url"]:
            err(f"{r['req_id']}: no source link (must be blank and flagged instead)")

    cap_by_file = {c["file"]: c["sha256"] for c in caps}
    for r in reads:
        if host(r["official_url"]) not in OFFICIAL:
            err(f"{r['check_id']}: official_url host {host(r['official_url'])} is not official")
        raw = ROOT / "data" / "nfl_d6a947cb" / r["raw_file"]
        if not raw.exists():
            err(f"{r['check_id']}: raw file {r['raw_file']} missing")
            continue
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        key = (DATA / r["raw_file"]).relative_to(ROOT).as_posix()
        if cap_by_file.get(key) != digest:
            err(f"{r['check_id']}: sha256 of {r['raw_file']} does not match capture_log.csv")

    for q in qs:
        if host(q["source_url"]) not in OFFICIAL | REPO:
            err(f"{q['q_id']}: source link host {host(q['source_url'])!r} is not official")
    for s in srcs:
        if not s["url"].startswith("https://"):
            err(f"{s['source_id']}: URL is not https")
        if s["publisher"].startswith("NFL") and host(s["url"]) not in OFFICIAL:
            err(f"{s['source_id']}: NFL publisher on a non-NFL host")

    for s in sugg:
        if s["pending_human_choice"] != "yes" or s["implemented"] != "no":
            err(f"{s['s_id']}: suggestion must be pending a human choice and not implemented")
    for f in rfs:
        if f["blocks_merge"] != "no":
            err(f"{f['rf_id']}: flagged items must not block the merge")

    # Site checks.
    if not SITE.exists():
        err("site directory docs/nfl-d6a947cb is missing; run scripts/build_nfl_d6a947cb.py")
    else:
        for page in PAGES:
            if not (SITE / page).exists():
                err(f"missing page {page}")
        for page in PAGES:
            p = SITE / page
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8")
            body = re.sub(r"<style>.*?</style>|<script>.*?</script>", "", text, flags=re.S)
            for cell in re.findall(r"<td>(.*?)</td>", body, flags=re.S):
                plain = re.sub(r"<[^>]+>", "", cell).strip()
                if plain in ("nan", "None", "NaN", "TODO", "null", "undefined") or "{" in plain or "}" in plain:
                    err(f"{page}: suspicious table cell {plain[:40]!r}")
            lp = LinkParser()
            lp.feed(text)
            for href in lp.hrefs:
                if href.startswith("http"):
                    if urlparse(href).scheme != "https":
                        err(f"{page}: non-https external link {href}")
                    continue
                if href.startswith("#") or href.startswith("mailto:"):
                    continue
                target = (SITE / href.split("#")[0]).resolve()
                if not target.exists():
                    err(f"{page}: broken internal link {href}")
        idx = (SITE / "index.html").read_text(encoding="utf-8")
        landing_rows = idx.count('<tr><td><a') + len(re.findall(r'<tr><td>R\d\d</td>', idx))
        if landing_rows < len(reqs):
            err(f"landing shows {landing_rows} requirement rows; registers have {len(reqs)}")
        if f"<strong>{len(reqs)}</strong>" in idx:
            pass
        if not re.search(rf'<div class="n">{len(reqs)}</div>', idx):
            err(f"landing card does not show {len(reqs)} owner rows")
        met = sum(1 for r in reqs if r["d6a_status"] == "met")
        if not re.search(rf'<div class="n">{met}</div>', idx):
            err(f"landing card does not show {met} met rows")

    # Banned wording: pages and the exec summary.
    texts = {}
    if SITE.exists():
        for page in PAGES:
            if (SITE / page).exists():
                texts[page] = (SITE / page).read_text(encoding="utf-8")
    if EXEC.exists():
        texts["NFL_D6A947CB_EXECUTIVE_SUMMARY.md"] = EXEC.read_text(encoding="utf-8")
    for name, text in texts.items():
        for pat in BANNED:
            if re.search(pat, text, flags=re.I):
                err(f"{name}: banned promotional wording matches {pat}")

    total = Counter(r["d6a_status"] for r in reqs)
    print(f"requirements={len(reqs)} unique={sum(1 for r in reqs if not r['duplicate_of'])} "
          f"status={dict(sorted(total.items()))} official_reads={len(reads)} questions={len(qs)} "
          f"suggestions={len(sugg)} findings={len(rfs)} sources={len(srcs)}")
    if errs:
        for e in errs:
            print("FAIL", e)
        print(f"{len(errs)} failure(s)")
        return 1
    print("OK: all d6a947cb checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
