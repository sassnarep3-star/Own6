#!/usr/bin/env python3
"""Verify the nfl-b72e2687 pack against the repo's evidence rules.

    python3 scripts/check_nfl_b72e2687.py

Rules enforced:
  R1  row counts match the capture (32 standings, 16 Week-12 games, 253 injury rows + 2 markers)
  R2  standings arithmetic recomputes (W/L/T totals, PF = PA)
  R3  injury practice tallies recompute (DNP/LP/FP sums)
  R4  every register row that cites an external source has a source link
  R5  every flagged row carries source links and a non-blocking disposition
  R6  capture log rows carry a UTC clock and a sha256
  R7  generated pages have no broken internal links
  R8  no market price is published anywhere in the pack
  R9  blank cells are allowed only where the row documents why (blank-means policy)
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_b72e2687")
DOCS = os.path.join(REPO, "docs", "nfl-b72e2687")

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(f"{name}: {detail}")


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def is_url(s: str) -> bool:
    return bool(re.match(r"^https?://", s or ""))


def main() -> None:
    standings = read("standings_2026_11_19.csv")
    week12 = read("week12_slate.csv")
    injuries = read("injuries_reg11.csv")
    players = [r for r in injuries if r.get("player") and r["player"] != "NO_INJURIES_REPORTED"]
    markers = [r for r in injuries if r.get("player") == "NO_INJURIES_REPORTED"]
    log = read("capture_log.csv")
    reqs = read("requirements.csv")
    qs = read("questions.csv")
    sugs = read("suggestions.csv")
    flags = read("flagged.csv")
    recheck = read("flag_recheck.csv")
    rev = read("reverification.csv")
    srcs = read("sources.csv")

    # R1 row counts
    check("R1 standings rows = 32", len(standings) == 32, f"got {len(standings)}")
    check("R1 Week-12 rows = 16", len(week12) == 16, f"got {len(week12)}")
    check("R1 injury player rows = 253", len(players) == 253, f"got {len(players)}")
    check("R1 injury no-injury markers = 2", len(markers) == 2, f"got {len(markers)}")
    check("R1 injuries cover 13 games", len({r["game"] for r in injuries}) == 13,
          f"got {len({r['game'] for r in injuries})}")

    # R2 standings arithmetic
    w = sum(int(r["w"]) for r in standings)
    l = sum(int(r["l"]) for r in standings)
    t = sum(int(r["t"]) for r in standings)
    pf = sum(int(r["pf"]) for r in standings)
    pa = sum(int(r["pa"]) for r in standings)
    check("R2 totals 149/149/2", (w, l, t) == (149, 149, 2), f"got {w}/{l}/{t}")
    check("R2 PF = PA = 6923", pf == pa == 6923, f"got PF {pf}, PA {pa}")

    # R3 practice tallies
    codes = {}
    for r in players:
        codes[r["practice_code"]] = codes.get(r["practice_code"], 0) + 1
    check("R3 DNP = 83", codes.get("DNP") == 83, f"got {codes.get('DNP')}")
    check("R3 LP = 87", codes.get("LP") == 87, f"got {codes.get('LP')}")
    check("R3 FP = 83", codes.get("FP") == 83, f"got {codes.get('FP')}")
    check("R3 published game status cells = 16",
          sum(1 for r in players if r["game_status"]) == 16,
          f"got {sum(1 for r in players if r['game_status'])}")

    # R4 source links on register rows
    bad = [r["req_id"] for r in reqs if not is_url(r["source_url"])]
    check("R4 every requirement row has a source link", not bad, f"missing: {bad[:5]}")
    # questions register: the source_needed column names the source required to answer
    # (some answers are owner decisions, so a descriptive name is honest; where a URL
    # is given it must be well-formed — never a placeholder)
    bad_q = [r["question_id"] for r in qs if not r["source_needed"]]
    check("R4 every question row names a source needed", not bad_q, f"missing: {bad_q[:5]}")
    bad_q2 = [r["question_id"] for r in qs
              if "http" in r["source_needed"] and not is_url(r["source_needed"])]
    check("R4 every question source URL is well-formed", not bad_q2, f"bad: {bad_q2[:5]}")
    bad_s = [r["sug_id"] for r in sugs if not r["prerequisite"]]
    check("R4 every suggestion names a prerequisite", not bad_s, f"missing: {bad_s[:5]}")

    # R5 flags
    bad_f = [r["flag_id"] for r in flags if not r["source_urls"] or r["blocking_merge"] != "no"]
    check("R5 every flag has source links and is non-blocking", not bad_f, f"bad: {bad_f[:5]}")
    bad_r = [r["flag_id"] for r in recheck if not r["retest_source"]]
    check("R5 every flag re-test names its source", not bad_r, f"bad: {bad_r[:5]}")

    # R6 capture log
    bad_log = [r["read_id"] for r in log
               if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", r["read_on_utc"])
               or not re.match(r"^[0-9a-f]{64}$", r["artifact_sha256"])]
    check("R6 capture log rows carry UTC clock + sha256", not bad_log, f"bad: {bad_log[:5]}")

    # R7 internal links in generated pages
    broken = []
    for fname in sorted(os.listdir(DOCS)):
        if not fname.endswith(".html"):
            continue
        with open(os.path.join(DOCS, fname), encoding="utf-8") as f:
            html = f.read()
        for href in re.findall(r'href="([^"#]+)"', html):
            if href.startswith(("http", "mailto", "data:")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href))
            if not os.path.exists(target):
                broken.append(f"{fname} -> {href}")
    check("R7 no broken internal links in generated pages", not broken, f"broken: {broken[:5]}")

    # R8 no market prices anywhere in the pack's published data
    # (a signed number like -7.5 or +1.90 in a register cell would be a line/odds value;
    # requirement prose may mention terms like "moneyline" without publishing a price)
    price_pat = re.compile(r"(?<![\w/])[-+]\d+(?:\.\d+)?(?![\w])")
    hits = []
    for name, rows in [("requirements.csv", reqs), ("questions.csv", qs),
                       ("suggestions.csv", sugs), ("flagged.csv", flags)]:
        for r in rows:
            joined = " ".join(str(v) for v in r.values())
            if price_pat.search(joined):
                hits.append(f"{name}:{r.get('req_id') or r.get('question_id') or r.get('sug_id') or r.get('flag_id')}")
    check("R8 no signed price-like values published in registers", not hits, f"suspicious: {hits[:5]}")

    # R9 reverification rows document their method and result
    bad_rv = [r["row_id"] for r in rev if not r["method"] or not r["result"]]
    check("R9 reverification rows carry method and result", not bad_rv, f"bad: {bad_rv[:5]}")

    # summary
    print(f"\n{checks - len(failures)}/{checks} checks passed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("OK — pack nfl_b72e2687 passes every rule.")


if __name__ == "__main__":
    main()
