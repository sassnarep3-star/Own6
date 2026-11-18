#!/usr/bin/env python3
"""Verifier for the nfl-0d4da02c pack.

Fails loudly on any of:
  1. a missing data file
  2. a data row with no source link
  3. a source link that is not an official host
  4. an interactive control on any page
  5. a broken internal link
  6. a rebuild that is not byte-identical
  7. an inconsistent register (count sums, gate references, option coverage)
  8. a profitability claim anywhere
  9. a missing decision column (the review-before-implement contract)

Usage:  python3 scripts/check_nfl_0d4da02c.py
Exit 0 on success, 1 with a printed report on failure.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_0d4da02c")
DOCS = os.path.join(REPO, "docs", "nfl-0d4da02c")

OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com", "operations.nfl.com", "api.weather.gov",
                  "github.com"}
PROFIT_PAT = re.compile(
    r"(guaranteed (profit|return|win)|risk[- ]free (profit|bet)|sure[- ]?thing|"
    r"(win|winning) rate of \d|expected roi of|profitable strateg)", re.I)
CONTROL_PAT = re.compile(r"<(input|select|textarea|button)\b", re.I)
LINK_PAT = re.compile(r'href="([^"]+)"')

# (file, source column) — these are published DATA tables; every row must carry a link.
MUST_HAVE_SOURCE = [
    ("injury_report_2026_11_18.csv", "source_url"),
    ("week10_absent_clubs.csv", "source_url"),
    ("week11_byes.csv", "source_url"),
    ("schedule_announcement.csv", "source_url"),
    ("starter_announcements.csv", "source_url"),
    ("designation_counts.csv", "source_url"),
    ("designation_xtab.csv", "source_url"),
    ("club_injury_counts.csv", "source_url"),
    ("position_group_counts.csv", "source_url"),
    ("designation_calibration_status.csv", "source_url"),
    ("week11_schedule.csv", "game_url"),
]
EXPECTED_FILES = [
    "requirements.csv", "requirement_terms.csv", "gates.csv", "suggestions.csv",
    "suggestion_options.csv", "qia.csv", "information_gaps.csv", "sources.csv",
    "official_reads.csv", "injury_report_2026_11_18.csv", "week10_absent_clubs.csv",
    "week11_schedule.csv", "week11_byes.csv", "schedule_announcement.csv",
    "starter_announcements.csv", "designation_counts.csv", "designation_xtab.csv",
    "club_injury_counts.csv", "position_group_counts.csv",
    "designation_calibration_status.csv", "repo_findings.csv", "repo_inventory.csv",
    "repo_evidence.csv", "repo_stats.csv", "flagged.csv",
]
STATUS_VOCAB = {"cleared", "cleared_repo", "structural", "blocked", "rejected", "open",
                "partially cleared", "needs review", "in progress"}


def rows(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    fail: list[str] = []
    checks = 0

    def ok(label: str) -> None:
        nonlocal checks
        checks += 1
        print(f"  ok   {label}")

    def bad(label: str, detail: str) -> None:
        nonlocal checks
        checks += 1
        fail.append(f"{label}: {detail}")
        print(f"  FAIL {label}: {detail}")

    # 1 files exist ---------------------------------------------------------
    print("[1] data files")
    missing = [f for f in EXPECTED_FILES if not os.path.exists(os.path.join(DATA, f))]
    bad("files present", f"missing {missing}") if missing else ok(
        f"all {len(EXPECTED_FILES)} expected data files present")

    # 2 every data row has a source ----------------------------------------
    print("[2] every data row carries a source link")
    for name, col in MUST_HAVE_SOURCE:
        rs = rows(name)
        blanks = [i for i, r in enumerate(rs, 2) if not (r.get(col) or "").strip()]
        bad(f"{name} source", f"{len(blanks)} row(s) with a blank {col}, first at line "
                              f"{blanks[0]}") if blanks else ok(
            f"{name}: {len(rs)} rows, every row sourced")

    # 3 official hosts only -------------------------------------------------
    print("[3] source links point at official hosts")
    bad_hosts = []
    for name, col in MUST_HAVE_SOURCE:
        for r in rows(name):
            url = (r.get(col) or "").strip()
            if not url:
                continue
            host = (urlparse(url).hostname or "").lower()
            if host not in OFFICIAL_HOSTS:
                bad_hosts.append(f"{name}:{host}")
    bad("official hosts", f"{len(bad_hosts)} non-official host(s): "
                          f"{sorted(set(bad_hosts))[:6]}") if bad_hosts else ok(
        "every source link is on an official host")

    # 4 no interactive controls --------------------------------------------
    print("[4] no interactive controls on any page")
    pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
    ctrl = []
    for p in pages:
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        hits = CONTROL_PAT.findall(text)
        if hits:
            ctrl.append(f"{p}:{','.join(sorted(set(hits)))}")
    bad("no input controls", f"{ctrl}") if ctrl else ok(
        f"{len(pages)} pages, no input/select/textarea/button")

    # 5 internal links resolve ---------------------------------------------
    print("[5] internal links resolve")
    broken = []
    for p in pages:
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        for href in LINK_PAT.findall(text):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href.split("?")[0].split("#")[0]))
            if not os.path.exists(target):
                broken.append(f"{p}->{href}")
    bad("internal links", f"{broken}") if broken else ok("all internal links resolve")

    # 6 determinism ---------------------------------------------------------
    print("[6] deterministic rebuild")
    before = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
              for p in pages}
    subprocess.run([sys.executable, "scripts/build_nfl_0d4da02c.py"], cwd=REPO,
                   capture_output=True, check=True)
    after = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
             for p in pages}
    changed = [p for p in pages if before[p] != after[p]]
    bad("determinism", f"rebuild changed {changed}") if changed else ok(
        f"{len(pages)} pages rebuild byte-identically")

    # 7 register consistency ------------------------------------------------
    print("[7] register consistency")
    reqs = rows("requirements.csv")
    gates = {g["gate_id"] for g in rows("gates.csv")}
    bad_status = sorted({r["status"] for r in reqs} - STATUS_VOCAB)
    bad("status vocabulary", f"unknown statuses {bad_status}") if bad_status else ok(
        f"{len(reqs)} requirement rows, statuses all in the vocabulary")
    dangling = sorted({r["blocking_gate"] for r in reqs if r["blocking_gate"]} - gates)
    bad("gate references", f"requirements reference undefined gates {dangling}") if dangling \
        else ok(f"all {len(gates)} gates referenced correctly")
    noclear = [g["gate_id"] for g in rows("gates.csv") if not g["clearing_number"].strip()]
    bad("gate clearing numbers", f"gates without a clearing number: {noclear}") if noclear \
        else ok("every gate has a clearing number")

    sug = rows("suggestions.csv")
    opts = rows("suggestion_options.csv")
    counts: dict[str, int] = {}
    for o in opts:
        counts[o["suggestion_id"]] = counts.get(o["suggestion_id"], 0) + 1
    thin = [s["suggestion_id"] for s in sug if counts.get(s["suggestion_id"], 0) < 2]
    bad("option coverage", f"suggestions with fewer than 2 options: {thin}") if thin else ok(
        f"{len(sug)} suggestions, {len(opts)} options, every suggestion has >= 2 paths")
    orphan = sorted(set(counts) - {s["suggestion_id"] for s in sug})
    bad("option orphans", f"options with no suggestion: {orphan}") if orphan else ok(
        "no orphan options")

    # 8 no profitability claim ---------------------------------------------
    print("[8] no profitability claim")
    hits = []
    for p in pages:
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        for m in PROFIT_PAT.findall(text):
            hits.append(f"{p}:{m}")
    bad("no profit claim", f"{hits[:6]}") if hits else ok("no profitability language")

    # 9 decision columns are blank -----------------------------------------
    print("[9] decision columns left blank for the owner")
    filled = [s["suggestion_id"] for s in sug if (s.get("owner_decision") or "").strip()]
    filled += [o["option_id"] for o in opts if (o.get("owner_choice") or "").strip()]
    bad("blank decisions", f"decision columns already filled: {filled}") if filled else ok(
        "every decision column is blank, as the review-before-implement contract requires")

    # 10 arithmetic ---------------------------------------------------------
    print("[10] arithmetic on official counts")
    inj = rows("injury_report_2026_11_18.csv")
    clubs = {r["club"] for r in inj}
    if len(clubs) != 28:
        bad("injury clubs", f"expected 28 clubs, found {len(clubs)}")
    else:
        ok(f"{len(inj)} injury rows across 28 clubs")
    dc = {r["value"]: int(r["n"]) for r in rows("designation_counts.csv")
          if r["dimension"] == "game_status"}
    if sum(dc.values()) != len(inj):
        bad("designation sum", f"{sum(dc.values())} != {len(inj)}")
    else:
        ok(f"game-status counts sum to {len(inj)}")
    g11 = rows("week11_schedule.csv")
    b11 = rows("week11_byes.csv")
    if len(g11) * 2 + len(b11) != 32:
        bad("week 11 coverage", f"{len(g11)} games + {len(b11)} byes != 32 clubs")
    else:
        ok(f"{len(g11)} games + {len(b11)} byes = 32 clubs")

    print()
    if fail:
        print(f"FAILED {len(fail)} of {checks} checks:")
        for f in fail:
            print(f"  - {f}")
        return 1
    print(f"PASSED all {checks} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
