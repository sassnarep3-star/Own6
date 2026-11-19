#!/usr/bin/env python3
"""Verifier for the nfl-4c8cf5a6 pack.

Fails loudly on any of:
  1. a missing expected data file
  2. a published data row with no source link (source-linked files)
  3. a source link that is not an official host
  4. an interactive control on any page
  5. a broken internal link
  6. a rebuild that is not byte-identical
  7. an inconsistent register (status vocab, gate references, option coverage)
  8. a profitability claim anywhere
  9. a non-blank owner decision column (review-before-implement contract)
  10. a strategy marked registered without a pre-window commit hash

Usage:  python3 scripts/check_nfl_4c8cf5a6.py
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
DATA = os.path.join(REPO, "data", "nfl_4c8cf5a6")
DOCS = os.path.join(REPO, "docs", "nfl-4c8cf5a6")

OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com", "operations.nfl.com", "api.weather.gov",
                  "docs.github.com", "github.com"}
PROFIT_PAT = re.compile(
    r"(guaranteed (profit|return|win)|risk[- ]free (profit|bet)|sure[- ]?thing|\n"
    r"(win|winning) rate of \d|expected roi of|profitable strateg)", re.I)
CONTROL_PAT = re.compile(r"<\s*(input|select|textarea|button)\b", re.I)
LINK_PAT = re.compile(r'href="([^"]+)"')

MUST_HAVE_SOURCE = [
    ("injury_tracking.csv", "source_url"),
    ("depth_model.csv", "depth_source_url"),
    ("depth_chart_register.csv", "source_url"),
    ("availability_graph.csv", "source_url"),
    ("snapshot_ledger.csv", "source_url"),
    ("price_snapshot_store.csv", "open_source_url"),
    ("originated_lines.csv", "market_capture_url"),
    ("results_feed.csv", "result_source_url"),
    ("correlations.csv", "source_url"),
    ("roster_sweep.csv", "source_url"),
    ("drift_alarms.csv", "source_url"),
    ("ablations.csv", "source_url"),
]
EXPECTED_FILES = [
    "requirements.csv", "gates.csv", "qia.csv", "information_gaps.csv",
    "suggestions.csv", "suggestion_options.csv", "flagged.csv", "sources.csv",
    "official_reads.csv", "strategies.csv", "validation_gates.csv", "correlations.csv",
    "leaderboard.csv", "price_snapshot_store.csv", "results_feed.csv",
    "originated_lines.csv", "depth_model.csv", "availability_graph.csv",
    "depth_chart_register.csv", "snapshot_ledger.csv", "injury_tracking.csv",
    "roster_sweep.csv", "drift_alarms.csv", "ablations.csv",
    "repo_findings.csv", "repo_stats.csv",
]
STATUS_VOCAB = {"cleared", "cleared_repo", "structural", "blocked", "rejected", "open",
                "partially cleared", "needs review", "in progress"}
STRAT_STATUS = {"declared", "registered", "qualified", "demoted", "rejected"}


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

    # 1 files exist
    print("[1] data files")
    missing = [f for f in EXPECTED_FILES if not os.path.exists(os.path.join(DATA, f))]
    bad("files present", f"missing {missing}") if missing else ok(
        f"all {len(EXPECTED_FILES)} expected data files present")

    # 2 every source-linked data row carries a source
    print("[2] every source-linked row carries a source link")
    for name, col in MUST_HAVE_SOURCE:
        rs = rows(name)
        blanks = [i for i, r in enumerate(rs, 2) if not (r.get(col) or "").strip()]
        bad(f"{name} source", f"{len(blanks)} row(s) with a blank {col}, first at line "
                              f"{blanks[0]}") if blanks else ok(
            f"{name}: {len(rs)} rows, every row sourced")

    # 3 official hosts only
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

    # 4 no interactive controls
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

    # 5 internal links resolve
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

    # 6 determinism
    print("[6] deterministic rebuild")
    before = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
              for p in pages}
    subprocess.run([sys.executable, "scripts/build_nfl_4c8cf5a6.py"], cwd=REPO,
                   capture_output=True, check=True)
    after = {p: hashlib.sha256(open(os.path.join(DOCS, p), "rb").read()).hexdigest()
             for p in pages}
    changed = [p for p in pages if before[p] != after[p]]
    bad("determinism", f"rebuild changed {changed}") if changed else ok(
        f"{len(pages)} pages rebuild byte-identically")

    # 7 register consistency
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
    strat = rows("strategies.csv")
    reg_no_commit = [s["strategy_id"] for s in strat
                     if s["status"] == "registered" and not s["registration_commit"].strip()]
    bad("registered without commit", f"strategies registered without a commit: "
                                     f"{reg_no_commit}") if reg_no_commit else ok(
        f"{len(strat)} strategies; none registered without a pre-window commit hash")

    # 8 no profitability claim
    print("[8] no profitability claim")
    hits = []
    for p in pages:
        text = open(os.path.join(DOCS, p), encoding="utf-8").read()
        for m in PROFIT_PAT.findall(text):
            hits.append(f"{p}:{m}")
    bad("no profit claim", f"{hits[:6]}") if hits else ok("no profitability language")

    # 9 decision columns blank
    print("[9] decision columns left blank for the owner")
    filled = [s["suggestion_id"] for s in sug if (s.get("owner_decision") or "").strip()]
    filled += [o["option_id"] for o in opts if (o.get("owner_choice") or "").strip()]
    bad("blank decisions", f"decision columns already filled: {filled}") if filled else ok(
        "every decision column is blank, as the review-before-implement contract requires")

    # 10 strategy count vs leaderboard
    print("[10] strategy/leaderboard consistency")
    lb = rows("leaderboard.csv")
    bad("leaderboard rows", f"{len(lb)} leaderboard rows (expected 0 by design)") if lb \
        else ok("leaderboard empty by design, 0 qualified strategies")

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
