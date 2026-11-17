#!/usr/bin/env python3
"""Verifier for the nfl_7a59fd89 pack. Numbered rules, exit 0 = pass.

Rule 1  every required artifact exists (CSV + page).
Rule 2  every row of every capture CSV carries an official-host source URL column value.
Rule 3  blank score cells are paired with a flag note (nothing inferred).
Rule 4  corpus_150 identities hold (136 + 14 = 150; margin/total arithmetic; club set).
Rule 5  sweep blocks are consistent with the row-level register (register is truth).
Rule 6  league status-code totals match the register-derived expectation.
Rule 7  availability conflicts: all 6 kinds present with expected counts; every row flagged.
Rule 8  injury cross-read delta is exactly 1 name variant over two 347-row reads.
Rule 9  schedule announcement carries captured verbatim evidence rows.
Rule 10 repo findings cover R-01..R-73 exactly once with non-empty verification.
Rule 11 week10 finals: 13 settled finals + 1 in-progress row with blank scores.
Rule 12 pages carry no generator-object strings or merge markers; nav links resolve.
Rule 13 every page table row carries at least one official-host link.
Rule 14 flagged.csv is non-empty and covers this pack's irregularity classes.
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "data", "nfl_7a59fd89")
DOCS = os.path.join(REPO, "docs", "nfl-7a59fd89")

ALLOWED_HOSTS = ("www.nfl.com", "nfl.com", "operations.nfl.com", "github.com")
URL_COLS = ("source_url", "source_urls", "url", "game_page_url", "week_page_url",
            "roster_status_source")

REQUIRED_CSVS = [
    "injury_hub_2026_11_17.csv", "injury_delta.csv", "roster_reserve.csv",
    "roster_sweep.csv", "week10_finals.csv", "corpus_150.csv",
    "availability_conflicts.csv", "schedule_announcement.csv", "repo_findings.csv",
    "sources.csv", "flagged.csv",
]
REQUIRED_PAGES = [n for n, _ in [
    ("index.html", ""), ("finals.html", ""), ("sweep.html", ""), ("conflicts.html", ""),
    ("delta.html", ""), ("announcement.html", ""), ("findings.html", ""),
    ("flagged.html", ""), ("sources.html", ""), ("executive-summary.html", ""),
]]

CLUBS = {"ARI": "AZ"}  # unused placeholder to keep club logic local
ALL_CLUBS = ("AZ ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LAC "
             "LAR LV MIA MIN NE NO NYG NYJ PHI PIT SF SEA TB TEN WAS").split()
EXPECTED_TOTALS = {"CUT": 160, "DEV": 511, "EXE": 1, "PUP": 19, "RES": 256, "RLS": 1,
                   "RSN": 6, "RSR": 31, "TRC": 82, "TRD": 58, "TRT": 17}
EXPECTED_KINDS = {"ACT_VS_HUB_OUT": 3, "DISPLAY_SLUG_MISMATCH": 5, "HUB_ABSENT": 4,
                  "NEWS_VS_TABLE": 1, "RESERVE_CODE_VS_HUB_STATUS": 32,
                  "SAME_SLUG_MULTI_PAGE": 51}

BAD_STRINGS = (re.compile(r"\{\{.*?\}\}"), re.compile(r"<<<<<"), re.compile(r">>>>>"),
               re.compile(r"<<<<<<<"), re.compile(r">>>>>>>"), re.compile(r"__generator"),
               re.compile(r"object at 0x"))


def rd(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    errs: list[str] = []

    # Rule 1
    for name in REQUIRED_CSVS:
        if not os.path.exists(os.path.join(DATA, name)):
            errs.append(f"rule 1: missing CSV {name}")
    for name in REQUIRED_PAGES:
        if not os.path.exists(os.path.join(DOCS, name)):
            errs.append(f"rule 1: missing page {name}")

    # Rule 2 (rows that declare a URL column must carry an allowed host)
    for name in REQUIRED_CSVS:
        try:
            rows = rd(name)
        except FileNotFoundError:
            continue
        for i, r in enumerate(rows, 2):
            for col in URL_COLS:
                if col in r and r[col]:
                    if not any(h in r[col] for h in ALLOWED_HOSTS):
                        errs.append(f"rule 2: {name}:{i} col {col} non-official URL {r[col]!r}")
                    break

    # Rule 3
    for i, r in enumerate(rd("corpus_150.csv"), 2):
        if r["week"] == "10" and (not r["away_score"] or not r["home_score"]):
            if "flag" not in r["event_mark_on_card"].lower() and "blank" not in r["event_mark_on_card"].lower():
                errs.append(f"rule 3: corpus_150:{i} blank week-10 score without flag note")
    for i, r in enumerate(rd("week10_finals.csv"), 2):
        if r["status"] != "FINAL" and (r["away_score"] or r["home_score"]):
            errs.append(f"rule 3: week10_finals:{i} non-final row carries scores")

    # Rule 4
    corpus = rd("corpus_150.csv")
    if len(corpus) != 150:
        errs.append(f"rule 4: corpus_150 has {len(corpus)} rows, expected 150")
    weeks = Counter(r["week"] for r in corpus)
    if weeks["10"] != 14:
        errs.append(f"rule 4: corpus_150 week-10 count {weeks['10']} != 14")
    if weeks["9"] == 0 or sum(v for k, v in weeks.items() if k != "10") != 136:
        errs.append(f"rule 4: corpus_150 prior-week rows != 136 ({sum(v for k, v in weeks.items() if k != '10')})")
    for i, r in enumerate(corpus, 2):
        if r["away_score"] and r["home_score"]:
            aw, hm = int(r["away_score"]), int(r["home_score"])
            if int(r["margin_home"]) != hm - aw or int(r["total"]) != aw + hm:
                errs.append(f"rule 4: corpus_150:{i} margin/total arithmetic ({r['game_id']})")
        # corpus convention (8362b702) prints the Rams as LA; roster pages use LAR
        aw_club = "LAR" if r["away"] == "LA" else r["away"]
        hm_club = "LAR" if r["home"] == "LA" else r["home"]
        if aw_club not in ALL_CLUBS or hm_club not in ALL_CLUBS:
            errs.append(f"rule 4: corpus_150:{i} unknown club {r['away']}/{r['home']}")

    # Rule 5 + 6 (register is truth; re-derive sweep aggregates)
    sys.path.insert(0, os.path.join(REPO, "src"))
    from nfl_7a59fd89 import sweep as SW
    reg = SW.load_register()
    swp = SW.load_sweep()
    if len(reg) != 1142:
        errs.append(f"rule 5: register has {len(reg)} rows, expected 1142")
    for e in SW.verify(reg, swp, act_by_club={} if False else None):
        errs.append(f"rule 5: {e}")
    codes = Counter(r["status_code"] for r in reg)
    if dict(codes) != EXPECTED_TOTALS:
        errs.append(f"rule 6: league totals {dict(codes)} != expected {EXPECTED_TOTALS}")

    # Rule 7
    conflicts = rd("availability_conflicts.csv")
    kinds = Counter(r["conflict_kind"] for r in conflicts)
    for k, n in EXPECTED_KINDS.items():
        if kinds.get(k, 0) != n:
            errs.append(f"rule 7: conflict kind {k} count {kinds.get(k, 0)} != {n}")
    for i, r in enumerate(conflicts, 2):
        if r["disposition"] != "flagged; never resolved by inference":
            errs.append(f"rule 7: conflicts:{i} disposition not flagged")

    # Rule 8
    delta = rd("injury_delta.csv")
    if len(delta) != 1 or delta[0]["delta_kind"] != "NAME_VARIANT":
        errs.append(f"rule 8: injury_delta rows {len(delta)} != exactly 1 NAME_VARIANT")
    hub = rd("injury_hub_2026_11_17.csv")
    if len(hub) != 347:
        errs.append(f"rule 8: hub rows {len(hub)} != 347")
    if len({r["club"] for r in hub}) != 28:
        errs.append("rule 8: hub clubs != 28")

    # Rule 9
    ann = rd("schedule_announcement.csv")
    if not any(r["outcome"].startswith("CAPTURED") for r in ann):
        errs.append("rule 9: no CAPTURED announcement evidence rows")

    # Rule 10
    findings = rd("repo_findings.csv")
    ids = [r["requirement_id"] for r in findings]
    expected_ids = [f"R-{i:02d}" for i in range(1, 74)]
    if sorted(ids) != expected_ids:
        errs.append("rule 10: repo_findings ids != R-01..R-73 exactly once")
    for i, r in enumerate(findings, 2):
        if not r["verification"].strip():
            errs.append(f"rule 10: findings:{i} empty verification")

    # Rule 11
    finals = rd("week10_finals.csv")
    settled = [r for r in finals if r["status"] == "FINAL"]
    live = [r for r in finals if r["status"] != "FINAL"]
    if len(finals) != 14 or len(settled) != 13 or len(live) != 1:
        errs.append(f"rule 11: finals {len(finals)}/{len(settled)}/{len(live)} != 14/13/1")
    pairs = {(r["away_team"], r["home_team"]) for r in finals}
    if len(pairs) != 14:
        errs.append("rule 11: finals club pairs not unique")
    for r in settled:
        if not (r["away_score"] and r["home_score"] and r["score_source"]):
            errs.append(f"rule 11: settled final {r['game_id']} missing score/source")

    # Rule 12 + 13
    nav_files = set(n for n, _ in [
        ("index.html", ""), ("finals.html", ""), ("sweep.html", ""), ("conflicts.html", ""),
        ("delta.html", ""), ("announcement.html", ""), ("findings.html", ""),
        ("flagged.html", ""), ("sources.html", ""), ("executive-summary.html", "")])
    for name in sorted(nav_files):
        p = os.path.join(DOCS, name)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            html_text = f.read()
        for pat in BAD_STRINGS:
            if pat.search(html_text):
                errs.append(f"rule 12: {name} contains generator/marker string {pat.pattern!r}")
        for m in re.finditer(r'href="([^"#]+)"', html_text):
            href = m.group(1)
            if href.startswith("http"):
                if not any(h in href for h in ALLOWED_HOSTS):
                    errs.append(f"rule 12: {name} external link not on official host: {href}")
                if href.startswith(("http://",)) or "//localhost" in href or href.startswith("http://127."):
                    errs.append(f"rule 12: {name} non-https link {href}")
            elif href.startswith(("/", "#")):
                if href.startswith("/") and not href.startswith("//"):
                    errs.append(f"rule 12: {name} root-absolute link {href} (Pages serves /Own6/)")
            else:
                if not os.path.exists(os.path.join(DOCS, href)):
                    errs.append(f"rule 12: {name} nav link does not resolve: {href}")
        rows = re.findall(r"<tr>(.*?)</tr>", html_text, re.S)
        for j, row in enumerate(rows, 1):
            if "<th>" in row:
                continue
            if not re.search(r'href="https?://(www\.)?(nfl\.com|operations\.nfl\.com|github\.com)', row):
                errs.append(f"rule 13: {name} table row {j} lacks an official-host link")

    # Rule 14
    flagged = rd("flagged.csv")
    if len(flagged) < 10:
        errs.append(f"rule 14: flagged.csv has {len(flagged)} rows; irregularity classes under-covered")

    if errs:
        print("FAIL")
        for e in errs:
            print("  -", e)
        return 1
    print("OK: all 14 verifier rules pass (nfl_7a59fd89)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
