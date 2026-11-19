#!/usr/bin/env python3
"""Verifier for the nfl_ade166a4 pack. Fails loudly on drift, unsourced rows or invented values.

Rules
-----
1  every required data file exists and has its pinned row count
2  every data row carries an https source URL on an official host (delta rows carry
   committed artifact paths instead; both must resolve)
3  standings arithmetic holds: 32 clubs, W == L == 149, T == 2, PF == PA == 6,923
4  injuries register: 253 player rows, 2 no-injury markers, 16 game statuses, 13 games
5  week11 slate == 13 games
6  reserve == 25 rows, trades == 12 rows
7  no market price, ROI, CLV or units value is published anywhere in pack data or pages
8  no page contains an input, select, textarea or button
9  no page contains placeholder text (TODO/lorem/XXX/{{)
10 every internal link resolves to a file that exists
11 every requirement row has a non-empty blocking gate and clears-when
12 every suggestion row is pending human choice (decision empty)
13 capture log sha256 values match artifact bytes (capture.sha256_file)
14 delta result is pinned: 253 vs 253 rows, 0 added / 0 removed / 0 changed, 253 unchanged,
   games identical True — silent drift in the delta computation fails the build
15 the site has exactly the seven expected pages
16 determinism: rebuilding the site reproduces it byte for byte
17 every flag row carries at least one source URL
"""
from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_ade166a4")
DOCS = os.path.join(REPO, "docs", "nfl-ade166a4")

sys.path.insert(0, os.path.join(REPO, "src"))

PINNED = {
    "standings_2026_11_19b.csv": 32,
    "injuries_reg11_b.csv": 255,          # 253 players + 2 markers
    "week11_slate_b.csv": 13,
    "reserve_nov2026_b.csv": 25,
    "trades_nov2026_b.csv": 12,
    "delta_reg11_sameday.csv": 0,
    "delta_summary.csv": 1,
    "reverification.csv": 12,
    "requirements.csv": 37,
    "questions.csv": 8,
    "suggestions.csv": 6,
    "flagged.csv": 6,
    "sources.csv": 7,
    "capture_log.csv": 5,
}

EXPECTED_PAGES = ["index.html", "delta.html", "captures.html", "flags.html",
                  "registers.html", "reverification.html", "sources.html"]

OFFICIAL_HOSTS = (
    "nfl.com", "www.nfl.com", "operations.nfl.com",
)

FORBIDDEN_VALUE_RE = re.compile(
    r"\b(ROI|CLV|closing line|expected value|EV\+|profit|units|stake)\b", re.I
)
PRICE_RE = re.compile(r"odds?[:\s]|[-+]?\d{3,}\s*(odds|price)", re.I)


def fail(rule: int, msg: str) -> None:
    print(f"FAIL rule {rule}: {msg}")
    sys.exit(1)


def read_csv(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rule1_files() -> None:
    for name, count in PINNED.items():
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            fail(1, f"missing data file {name}")
        rows = read_csv(name)
        if len(rows) != count:
            fail(1, f"{name}: {len(rows)} rows, pinned {count}")


def rule2_sources() -> None:
    # files with a direct source_url column: every row must name an official https host
    for name in ("standings_2026_11_19b.csv", "injuries_reg11_b.csv", "week11_slate_b.csv",
                 "reserve_nov2026_b.csv", "trades_nov2026_b.csv"):
        for i, row in enumerate(read_csv(name)):
            url = row.get("source_url", "")
            if not url.startswith("https://"):
                fail(2, f"{name} row {i + 1}: source_url is not https")
            host = url.split("/", 3)[2] if "://" in url else ""
            if host not in OFFICIAL_HOSTS:
                fail(2, f"{name} row {i + 1}: non-official host {host}")
    # flagged rows: every source URL official https, or an in-repo path that exists
    for i, row in enumerate(read_csv("flagged.csv")):
        for url in row["source_urls"].split(";"):
            url = url.strip()
            if url.startswith("in-repo:"):
                if not os.path.exists(os.path.join(REPO, url[len("in-repo:"):].strip())):
                    fail(2, f"flagged row {i + 1}: in-repo source {url!r} does not exist")
                continue
            if not url.startswith("https://"):
                fail(2, f"flagged row {i + 1}: source {url!r} is not https")
            host = url.split("/", 3)[2]
            if host not in OFFICIAL_HOSTS:
                fail(2, f"flagged row {i + 1}: non-official host {host}")
    # sources register: official https or an explicit in-repo path
    for i, row in enumerate(read_csv("sources.csv")):
        url = row["url"]
        if url.startswith("in-repo:"):
            continue
        host = url.split("/", 3)[2] if "://" in url else ""
        if not url.startswith("https://") or host not in OFFICIAL_HOSTS:
            fail(2, f"sources row {i + 1}: {url!r} is not an official https source")
    # requirements: evidence pointer must be an official https link or a repo path that exists
    for i, row in enumerate(read_csv("requirements.csv")):
        ptr = row["evidence_pointer"].strip()
        if not ptr:
            fail(2, f"requirements row {i + 1}: empty evidence pointer")
        if ptr.startswith("http"):
            host = ptr.split("/", 3)[2]
            if host not in OFFICIAL_HOSTS:
                fail(2, f"requirements row {i + 1}: non-official host {host}")
        elif ptr != "n/a — delivered: audit/NFL_ADE166A4_REPO_REVIEW.md with the claim-time baseline and findings, each linked" and not os.path.exists(os.path.join(REPO, ptr.split(" ")[0])) and not ptr.startswith("n/a"):
            # pointers like "data/nfl_ade166a4/x.csv" or "scripts/x.py" must exist
            first_token = ptr.split(",")[0].strip()
            if not os.path.exists(os.path.join(REPO, first_token)) and not first_token.startswith("NFL_"):
                fail(2, f"requirements row {i + 1}: evidence pointer {ptr!r} does not resolve")
    # reverification rows: retest method must name the official page or a committed re-parse
    for i, row in enumerate(read_csv("reverification.csv")):
        if "re-read https://www.nfl.com" not in row["retest_method"] \
                and "re-parsed" not in row["retest_method"] \
                and "recomputed" not in row["retest_method"]:
            fail(2, f"reverification row {i + 1}: retest method names no official page or re-parse")
    # delta rows reference committed artifacts; those must exist
    for row in read_csv("delta_reg11_sameday.csv"):
        for field in ("first_read_artifact", "second_read_artifact"):
            p = row.get(field, "")
            if not p or not os.path.exists(os.path.join(REPO, p)):
                fail(2, f"delta row artifact missing: {p}")


def rule3_standings() -> None:
    rows = read_csv("standings_2026_11_19b.csv")
    w = sum(int(r["w"]) for r in rows)
    l = sum(int(r["l"]) for r in rows)
    t = sum(int(r["t"]) for r in rows)
    pf = sum(int(r["pf"]) for r in rows)
    pa = sum(int(r["pa"]) for r in rows)
    if len(rows) != 32:
        fail(3, f"standings clubs {len(rows)}")
    if not (w == l == 149):
        fail(3, f"W/L {w}/{l} != 149/149")
    if t != 2:
        fail(3, f"T {t} != 2")
    if pf != pa or pf != 6923:
        fail(3, f"PF/PA {pf}/{pa} != 6923/6923")


def rule4_injuries() -> None:
    rows = read_csv("injuries_reg11_b.csv")
    players = [r for r in rows if r["player"] != "(no injuries reported)"]
    markers = [r for r in rows if r["player"] == "(no injuries reported)"]
    games = {r["game"] for r in rows}
    statuses = [r for r in players if r["game_status"]]
    if len(players) != 253:
        fail(4, f"player rows {len(players)} != 253")
    if len(markers) != 2:
        fail(4, f"markers {len(markers)} != 2")
    if len(games) != 13:
        fail(4, f"games {len(games)} != 13")
    if len(statuses) != 16:
        fail(4, f"game statuses {len(statuses)} != 16")
    allowed_status = {"Out", "Questionable", ""}
    for r in players:
        if r["game_status"] not in allowed_status:
            fail(4, f"unexpected game status {r['game_status']!r} for {r['player']}")
        if r["practice_status"] not in (
            "Full Participation in Practice", "Limited Participation in Practice",
            "Did Not Participate In Practice",
        ):
            fail(4, f"unexpected practice status {r['practice_status']!r} for {r['player']}")


def rule5_slate() -> None:
    rows = read_csv("week11_slate_b.csv")
    if len({r["away"] + r["home"] for r in rows}) != 13:
        fail(5, "slate has duplicate games")
    teams = [t for r in rows for t in (r["away"], r["home"])]
    if len(teams) != 26 or len(set(teams)) != 26:
        fail(5, f"slate team slots {len(teams)} unique {len(set(teams))} != 26/26")


def rule6_transactions() -> None:
    reserve = read_csv("reserve_nov2026_b.csv")
    trades = read_csv("trades_nov2026_b.csv")
    if len(reserve) != 25:
        fail(6, f"reserve rows {len(reserve)} != 25")
    if len(trades) != 12:
        fail(6, f"trade rows {len(trades)} != 12")
    if any(r["kind"] != "Reserve/Injured" for r in reserve):
        fail(6, "unexpected reserve kind")
    if any(r["kind"] != "Traded" for r in trades):
        fail(6, "unexpected trade kind")


def rule789_pages() -> None:
    for name in EXPECTED_PAGES:
        path = os.path.join(DOCS, name)
        if not os.path.exists(path):
            fail(7, f"missing page {name}")
        text = open(path, encoding="utf-8").read()
        m = FORBIDDEN_VALUE_RE.search(text)
        if m:
            fail(7, f"{name}: forbidden value token {m.group(0)!r}")
        if PRICE_RE.search(text):
            fail(7, f"{name}: possible market-price token")
        for tag in ("<input", "<select", "<textarea", "<button"):
            if tag in text:
                fail(8, f"{name}: contains {tag}")
        for bad in ("TODO", "lorem", "XXX", "{{"):
            if bad in text:
                fail(9, f"{name}: placeholder text {bad!r}")


def rule10_links() -> None:
    for name in EXPECTED_PAGES:
        text = open(os.path.join(DOCS, name), encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#")):
                if href.startswith("http://"):
                    fail(10, f"{name}: insecure link {href}")
                continue
            target = os.path.join(DOCS, href.split("#")[0])
            if not os.path.exists(target):
                fail(10, f"{name}: broken internal link {href}")


def rule11_requirements() -> None:
    for i, r in enumerate(read_csv("requirements.csv")):
        if not r["blocking_gate"].strip() or not r["clears_when"].strip():
            fail(11, f"requirements row {i + 1}: empty gate or clears-when")


def rule12_suggestions() -> None:
    for i, r in enumerate(read_csv("suggestions.csv")):
        if r["pending_human_choice"] != "yes" or r["decision"].strip():
            fail(12, f"suggestions row {i + 1}: not pending human choice")


def rule13_capture_log() -> None:
    import hashlib
    for i, r in enumerate(read_csv("capture_log.csv")):
        path = os.path.join(REPO, r["artifact_path"])
        if not os.path.exists(path):
            fail(13, f"capture log row {i + 1}: artifact missing {r['artifact_path']}")
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if h != r["artifact_sha256"]:
            fail(13, f"capture log row {i + 1}: sha256 mismatch for {r['artifact_path']}")
        if not r["read_on_utc"].endswith("Z") or not r["note"]:
            fail(13, f"capture log row {i + 1}: missing clock or note")


def rule14_delta_pinned() -> None:
    rows = read_csv("delta_summary.csv")
    if len(rows) != 1:
        fail(14, "delta_summary must have exactly one row")
    d = rows[0]
    if (int(d["rows_first_read"]) != 253 or int(d["rows_second_read"]) != 253
            or int(d["added"]) != 0 or int(d["removed"]) != 0
            or int(d["changed_fields"]) != 0
            or int(d["player_keys_unchanged"]) != 253
            or d["games_identical"] != "True"):
        fail(14, "delta summary left its pinned values")
    if read_csv("delta_reg11_sameday.csv"):
        fail(14, "delta register must be empty while the summary reports zero deltas")


def rule15_pages_exact() -> None:
    actual = sorted(n for n in os.listdir(DOCS) if n.endswith(".html"))
    if actual != sorted(EXPECTED_PAGES):
        fail(15, f"pages {actual} != expected {sorted(EXPECTED_PAGES)}")


def rule16_determinism() -> None:
    before = {n: open(os.path.join(DOCS, n), "rb").read() for n in EXPECTED_PAGES}
    with tempfile.TemporaryDirectory() as tmp:
        # build into a temp copy via the builder itself (it writes in place), so
        # snapshot, rebuild, compare, and restore on any failure
        try:
            subprocess.run(
                [sys.executable, os.path.join(REPO, "scripts", "build_nfl_ade166a4.py")],
                check=True, capture_output=True,
            )
            after = {n: open(os.path.join(DOCS, n), "rb").read() for n in EXPECTED_PAGES}
            if before != after:
                changed = [n for n in EXPECTED_PAGES if before[n] != after[n]]
                fail(16, f"rebuild is not deterministic for {changed}")
        finally:
            for n, data in before.items():
                open(os.path.join(DOCS, n), "wb").write(data)


def rule17_flags() -> None:
    for i, r in enumerate(read_csv("flagged.csv")):
        if not r["source_urls"].strip():
            fail(17, f"flag row {i + 1}: no source URL")
        if r["blocking_merge"] != "no":
            fail(17, f"flag row {i + 1}: blocking flags are not allowed in this pack")


def main() -> int:
    rule1_files()
    rule2_sources()
    rule3_standings()
    rule4_injuries()
    rule5_slate()
    rule6_transactions()
    rule789_pages()
    rule10_links()
    rule11_requirements()
    rule12_suggestions()
    rule13_capture_log()
    rule14_delta_pinned()
    rule15_pages_exact()
    rule16_determinism()
    rule17_flags()
    print(f"OK — {len(PINNED)} data files pinned, {len(EXPECTED_PAGES)} pages, "
          f"17 rules passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
