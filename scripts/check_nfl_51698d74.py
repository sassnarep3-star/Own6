#!/usr/bin/env python3
"""Verifier for the nfl_51698d74 pack. Fails loudly on drift, unsourced rows or invented values.

Rules
-----
1  every required data file exists and has its pinned row count
2  every data row carries an https source URL on an official host
3  standings arithmetic holds: 32 clubs, W == L, PF == PA, T == 2
4  injuries register: 253 player rows, 2 no-injury markers, 16 game statuses, 13 games
5  slates: week11 == 13, week10 == 14, week12 == 16 with all 16 venues filled
6  no market price, ROI, CLV or units value is published anywhere
7  no page contains an input, select, textarea or button
8  no page contains placeholder text (TODO/TBD/lorem/XXX/{{)
9  every internal link resolves to a file that exists
10 every requirement row has a non-empty blocking gate and clearing number
11 every suggestion row is pending human choice (decision empty)
12 capture log sha256 values match artifact bytes (capture.verify_capture_log)
13 determinism: rebuilding the site reproduces it byte for byte
14 the site has exactly the six expected pages
15 flag recheck has no empty retest finding
16 originated-lines check: 13 rows, all MATCH, market columns blank
17 leaderboard check: 8 rows, all MATCH, 0 qualified
18 correlations check: 4 rows, n == 150 each, Fisher bounds present
19 reserve list: 25 rows within the 11/10-11/18 window
20 week12 venue match counts: 11 exact, 3 mismatch, 2 variance
21 every repository blob/tree href on a pack page resolves to a real tracked path (no joined or
   space-encoded hrefs)
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_51698d74")
DOCS = os.path.join(REPO, "docs", "nfl-51698d74")

sys.path.insert(0, os.path.join(REPO, "src"))

PINNED = {
    "standings_2026_11_19.csv": 32,
    "injuries_reg11.csv": 255,          # 253 players + 2 markers
    "week11_slate.csv": 13,
    "week10_finals.csv": 14,
    "week12_slate.csv": 16,
    "reserve_list.csv": 25,
    "flag_recheck.csv": 15,
    "reverification.csv": 8,
    "requirements.csv": 80,
    "questions.csv": 14,
    "suggestions.csv": 10,
    "flagged.csv": 12,
    "sources.csv": 24,
    "capture_log.csv": 8,
    "originated_lines_check.csv": 13,
    "leaderboard_check.csv": 8,
    "correlations_check.csv": 4,
    "repo_findings.csv": 8,
}

EXPECTED_PAGES = ["index.html", "captures.html", "flags.html", "reverification.html",
                  "registers.html", "sources.html"]

OFFICIAL_HOSTS = (
    "nfl.com", "www.nfl.com", "operations.nfl.com",
    "baltimoreravens.com", "www.baltimoreravens.com",
    "houstontexans.com", "www.houstontexans.com",
    "packers.com", "www.packers.com",
    "azcardinals.com", "www.azcardinals.com",
    "github.com", "www.marriott.com",
)

BANNED_WORDS = re.compile(
    r"\b(ROI|CLV|units won|guaranteed profit|expected return|buy now|lorem ipsum)\b",
    re.I,
)
PLACEHOLDER = re.compile(r"TODO|TBD|\{\{|lorem ipsum|\bXXX\b", re.I)

problems: list[str] = []


def fail(rule: int, msg: str) -> None:
    problems.append(f"rule {rule}: {msg}")


def read(name: str) -> list[dict]:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        fail(1, f"missing data file {name}")
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_pinned() -> None:
    for name, n in PINNED.items():
        rows = read(name)
        if rows and len(rows) != n:
            fail(1, f"{name}: expected {n} rows, found {len(rows)}")


def check_sources() -> None:
    for name in ("standings_2026_11_19.csv", "injuries_reg11.csv", "week11_slate.csv",
                 "week10_finals.csv", "week12_slate.csv", "reserve_list.csv",
                 "flag_recheck.csv", "flagged.csv", "sources.csv",
                 "originated_lines_check.csv", "correlations_check.csv"):
        for r in read(name):
            joined = " ".join(v for v in r.values() if isinstance(v, str))
            if "http" not in joined:
                fail(2, f"{name}: row without any URL: {r.get('flag_id') or r}")
                continue
            for u in re.findall(r"https?://[^\s;]+", joined):
                host = re.sub(r"^https?://", "", u).split("/")[0]
                if host not in OFFICIAL_HOSTS:
                    fail(2, f"{name}: non-official host {host} in {u}")


def check_standings() -> None:
    rows = read("standings_2026_11_19.csv")
    if len(rows) != 32:
        fail(3, f"standings rows {len(rows)} != 32")
        return
    w = sum(int(r["w"]) for r in rows)
    l = sum(int(r["l"]) for r in rows)
    t = sum(int(r["t"]) for r in rows)
    pf = sum(int(r["pf"]) for r in rows)
    pa = sum(int(r["pa"]) for r in rows)
    if w != l:
        fail(3, f"W {w} != L {l}")
    if t != 2:
        fail(3, f"T {t} != 2")
    if pf != pa:
        fail(3, f"PF {pf} != PA {pa}")
    if w != 149:
        fail(3, f"W {w} != 149 (150 games through Week 10)")
    if pf != 6923:
        fail(3, f"PF {pf} != 6923")


def check_injuries() -> None:
    rows = read("injuries_reg11.csv")
    players = [r for r in rows if r["player"]]
    markers = [r for r in rows if r["note"]]
    statuses = [r for r in players if r["game_status"]]
    games = {r["game"] for r in rows}
    if len(players) != 253:
        fail(4, f"player rows {len(players)} != 253")
    if len(markers) != 2:
        fail(4, f"markers {len(markers)} != 2")
    if len(statuses) != 16:
        fail(4, f"game statuses {len(statuses)} != 16")
    if len(games) != 13:
        fail(4, f"games {len(games)} != 13")
    thu = {r["game"] for r in statuses}
    if len(thu) != 1 or "THURSDAY" not in next(iter(thu), ""):
        fail(4, "game statuses not confined to the Thursday game")


def check_slates() -> None:
    if len(read("week11_slate.csv")) != 13:
        fail(5, "week11_slate != 13")
    if len(read("week10_finals.csv")) != 14:
        fail(5, "week10_finals != 14")
    w12 = read("week12_slate.csv")
    if len(w12) != 16:
        fail(5, "week12_slate != 16")
    for r in read("week11_slate.csv"):
        if not r["venue_stadium_gamecentre"]:
            fail(5, f"week11 missing game-centre venue for {r['away']}@{r['home']}")
    for r in w12:
        if not r["venue_stadium_gamecentre"]:
            fail(5, f"week12 missing game-centre venue for {r['away']}@{r['home']}")


def check_no_prices() -> None:
    for root, _dirs, files in os.walk(DOCS):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            text = open(os.path.join(root, fn), encoding="utf-8").read()
            for m in BANNED_WORDS.finditer(text):
                fail(6, f"{fn}: banned claim language {m.group(0)!r}")


def check_no_inputs() -> None:
    for fn in os.listdir(DOCS) if os.path.isdir(DOCS) else []:
        if not fn.endswith(".html"):
            continue
        text = open(os.path.join(DOCS, fn), encoding="utf-8").read()
        for tag in ("<input", "<select", "<textarea", "<button"):
            if tag in text:
                fail(7, f"{fn}: contains {tag}")


def check_placeholders() -> None:
    for fn in os.listdir(DOCS) if os.path.isdir(DOCS) else []:
        if not fn.endswith(".html"):
            continue
        text = open(os.path.join(DOCS, fn), encoding="utf-8").read()
        m = PLACEHOLDER.search(text)
        if m:
            fail(8, f"{fn}: placeholder {m.group(0)!r}")


def check_links() -> None:
    for fn in EXPECTED_PAGES:
        path = os.path.join(DOCS, fn)
        if not os.path.exists(path):
            fail(9, f"missing page {fn}")
            continue
        text = open(path, encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(DOCS, href))
            if not os.path.exists(target):
                fail(9, f"{fn}: broken internal link {href}")


def check_requirements() -> None:
    for r in read("requirements.csv"):
        if not r["blocking_gate"].strip():
            fail(10, f"{r['req_id']}: empty blocking_gate")
        if not r["clears_when"].strip():
            fail(10, f"{r['req_id']}: empty clears_when")


def check_suggestions() -> None:
    for r in read("suggestions.csv"):
        if r["pending_human_choice"] != "yes" or r["decision"].strip():
            fail(11, f"{r['s_id']}: decision made without a human ({r['decision']!r})")


def check_capture_log() -> None:
    from nfl_51698d74 import capture
    for p in capture.verify_capture_log():
        fail(12, p)


def check_determinism() -> None:
    before = {}
    for fn in EXPECTED_PAGES:
        p = os.path.join(DOCS, fn)
        if os.path.exists(p):
            before[fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    subprocess.run([sys.executable, os.path.join(REPO, "scripts", "build_nfl_51698d74.py")],
                   check=True, capture_output=True)
    for fn, h in before.items():
        p = os.path.join(DOCS, fn)
        now = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if now != h:
            fail(13, f"{fn}: rebuild not deterministic")


def check_pages() -> None:
    have = sorted(f for f in os.listdir(DOCS) if f.endswith(".html")) if os.path.isdir(DOCS) else []
    if have != sorted(EXPECTED_PAGES):
        fail(14, f"pages {have} != {sorted(EXPECTED_PAGES)}")


def check_recheck() -> None:
    for r in read("flag_recheck.csv"):
        if not r["retest_finding"].strip():
            fail(15, f"{r['flag_id']}: empty retest_finding")


def check_lines() -> None:
    rows = read("originated_lines_check.csv")
    if len(rows) != 13:
        fail(16, f"originated_lines_check rows {len(rows)} != 13")
    for r in rows:
        if r["verdict"] != "MATCH":
            fail(16, f"{r['game_id']}: verdict {r['verdict']!r} != MATCH")
        for col in ("market_margin_home", "market_total", "market_home_price",
                    "difference_margin", "difference_total"):
            if r[col].strip():
                fail(16, f"{r['game_id']}: market column {col} not blank: {r[col]!r}")


def check_board() -> None:
    rows = read("leaderboard_check.csv")
    if len(rows) != 8:
        fail(17, f"leaderboard_check rows {len(rows)} != 8")
    for r in rows:
        if not r["verdict"].startswith("MATCH"):
            fail(17, f"{r['strategy_id']}: verdict {r['verdict']!r} not MATCH")
        if r["proper_score_qualified"] != "no":
            fail(17, f"{r['strategy_id']}: qualified={r['proper_score_qualified']!r} != no")


def check_corrs() -> None:
    rows = read("correlations_check.csv")
    if len(rows) != 4:
        fail(18, f"correlations_check rows {len(rows)} != 4")
    for r in rows:
        if r["n"] != "150":
            fail(18, f"{r['pair']}: n={r['n']!r} != 150")
        if not r["fisher_95_lo"].strip() or not r["fisher_95_hi"].strip():
            fail(18, f"{r['pair']}: missing Fisher bounds")


def check_reserve() -> None:
    rows = read("reserve_list.csv")
    if len(rows) != 25:
        fail(19, f"reserve rows {len(rows)} != 25")
    dates = sorted(r["date"] for r in rows)
    if dates[0] != "2026-11-10" or dates[-1] != "2026-11-18":
        fail(19, f"reserve window {dates[0]}..{dates[-1]} != 2026-11-10..2026-11-18")


def check_venue_counts() -> None:
    rows = read("week12_slate.csv")
    from collections import Counter
    c = Counter(r["venue_match"] for r in rows)
    if c.get("exact", 0) != 11 or c.get("mismatch", 0) != 3 or c.get("variance", 0) != 2:
        fail(20, f"week12 venue counts {dict(c)} != 11 exact / 3 mismatch / 2 variance")


def check_repo_links() -> None:
    """Rule 21: every repository blob/tree href on a pack page must resolve to a real path."""
    for fn in EXPECTED_PAGES:
        path = os.path.join(DOCS, fn)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        for href in re.findall(r'href="(https://github\.com/sassnarep3-star/Own6/(?:blob|tree)/main/[^"]+)"', text):
            if "%20" in href or ";" in href or " " in href:
                fail(21, f"{fn}: malformed repository href {href}")
                continue
            rel = href.split("/main/", 1)[1].strip("/")
            if not os.path.exists(os.path.join(REPO, rel)):
                fail(21, f"{fn}: repository href points at a missing path: {rel}")


def main() -> int:
    check_pinned()
    check_sources()
    check_standings()
    check_injuries()
    check_slates()
    check_no_prices()
    check_no_inputs()
    check_placeholders()
    check_links()
    check_requirements()
    check_suggestions()
    check_capture_log()
    check_determinism()
    check_pages()
    check_recheck()
    check_lines()
    check_board()
    check_corrs()
    check_reserve()
    check_venue_counts()
    check_repo_links()
    if problems:
        print(f"FAIL — {len(problems)} problem(s):")
        for p in problems:
            print(" -", p)
        return 1
    print(f"OK — 21 rules, {sum(PINNED.values())} data rows, "
          f"{len(EXPECTED_PAGES)} pages, capture log verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
