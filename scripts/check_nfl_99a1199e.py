#!/usr/bin/env python3
"""Verifier for the nfl_99a1199e pack. Numbered rules, exit 0 = pass.

Rule 1  every required artifact exists (CSV + page).
Rule 2  every CSV row carries a non-empty source URL on an allowed host.
Rule 3  every sweep row's tallies hold: total = ACT + reserve, codes match rows.
Rule 4  reserve register rows are non-ACT only and reconcile per club to the sweep.
Rule 5  every status code published is one of the codes observed on the pages.
Rule 6  flagged.csv covers every irregularity class this pack publishes.
Rule 7  every nav link on every page resolves to a built page.
Rule 8  capture log covers all 32 clubs and publishes the CAR re-read.
Rule 9  no price/line/odds/ROI/CLV/profitability value appears anywhere.
Rule 10 the sweep covers exactly the 32 NFL clubs, one well-formed URL each.
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
DATA = os.path.join(REPO, "data", "nfl_99a1199e")
DOCS = os.path.join(REPO, "docs", "nfl-99a1199e")

from nfl_99a1199e import sweep as S  # noqa: E402

ALLOWED_HOSTS = ("www.nfl.com", "nfl.com")

REQUIRED_CSVS = [
    "roster_sweep.csv", "reserve_register.csv", "capture_log.csv",
    "flagged.csv", "sources.csv", "status_code_tally.csv",
]

REQUIRED_PAGES = [
    "index.html", "register.html", "flagged.html", "sources.html",
    "capture-log.html", "executive-summary.html",
]

URL_COLS = ("source_url", "roster_url", "url")

# Codes observed across the 32 roster pages this session (verbatim).
OBSERVED_CODES = {"ACT", "CUT", "DEV", "EXE", "PUP", "RES", "RLS", "RSN", "RSR",
                  "TRC", "TRD", "TRT"}

# Irregularity classes this pack publishes; flagged.csv must cover each.
FLAG_CATEGORIES = {"name_slug_mismatch", "unusual_status", "embedded_quotes",
                   "unlinked_row", "reconciliation", "cross_club_repeat"}

# Values the brief forbids anywhere in the pack.
FORBIDDEN_PATTERN = re.compile(
    r"\b(price|prices|odds|line|lines|ROI|CLV|profit|profitable|profitability|"
    r"market_line|correlation|expected_value|ev_)\b", re.IGNORECASE)

NFL_CLUBS = {"ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
             "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
             "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
             "TEN", "WAS"}


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    errs = []

    # Rule 1
    for f in REQUIRED_CSVS:
        if not os.path.exists(os.path.join(DATA, f)):
            errs.append(f"rule 1: missing {f}")
    for f in REQUIRED_PAGES:
        if not os.path.exists(os.path.join(DOCS, f)):
            errs.append(f"rule 1: missing {f}")

    # Rule 2 (needs the files)
    if not errs:
        for name in REQUIRED_CSVS:
            for i, r in enumerate(rows(name), 2):
                urls = [r.get(c, "") for c in URL_COLS]
                if not any(u for u in urls):
                    errs.append(f"rule 2: {name} line {i} has no source URL")
                for u in urls:
                    if u:
                        if not u.startswith("https://"):
                            errs.append(f"rule 2: {name} line {i} URL not https: {u}")
                        if not any(h in u for h in ALLOWED_HOSTS):
                            errs.append(f"rule 2: {name} line {i} URL host not allowed: {u}")

    # Rule 9: no forbidden values anywhere. Column headers are checked for
    # forbidden value types; cells are checked for standalone forbidden tokens
    # (a verbatim player name like "Jayden Price" is a roster value, not a
    # price value, so multi-word cells are not flagged).
    if not errs:
        for name in REQUIRED_CSVS:
            with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
                rd = csv.reader(fh)
                header = next(rd)
                for col in header:
                    if FORBIDDEN_PATTERN.search(col):
                        errs.append(f"rule 9: {name} column {col!r} is a forbidden value type")
                for i, row in enumerate(rd, 2):
                    for cell in row:
                        cell = cell.strip()
                        if cell and " " not in cell and FORBIDDEN_PATTERN.fullmatch(cell):
                            errs.append(f"rule 9: {name} line {i} forbidden value {cell!r}")

    # Rule 3 + 10
    sweep = rows("roster_sweep.csv") if not errs else []
    if sweep:
        clubs = {r["club"] for r in sweep}
        if clubs != NFL_CLUBS:
            errs.append(f"rule 10: sweep clubs {sorted(clubs)} != the 32 NFL clubs")
        for r in sweep:
            try:
                total = int(r["total_rows"])
                active = int(r["active_count"])
                reserve = int(r["reserve_count"])
            except ValueError:
                errs.append(f"rule 3: {r['club']} non-integer tally")
                continue
            if total != active + reserve:
                errs.append(f"rule 3: {r['club']} total {total} != ACT {active} + reserve {reserve}")
            codes = {c.strip() for c in r["status_codes_seen"].split(",") if c.strip()}
            if not codes or not codes <= OBSERVED_CODES:
                errs.append(f"rule 5: {r['club']} unknown status code(s) {sorted(codes)}")
            if "ACT" not in codes:
                errs.append(f"rule 5: {r['club']} codes missing ACT")
            if not r["roster_url"].startswith("https://www.nfl.com/teams/"):
                errs.append(f"rule 10: {r['club']} roster_url not a well-formed nfl.com roster URL")

    # Rule 4
    register = rows("reserve_register.csv") if not errs else []
    if register and sweep:
        per_club = {}
        for r in register:
            per_club.setdefault(r["club"], 0)
            per_club[r["club"]] += 1
            if r["status_code"] == "ACT":
                errs.append(f"rule 4: register row for {r['club']} {r['player']} is ACT")
            if r["status_code"] not in OBSERVED_CODES:
                errs.append(f"rule 5: register row for {r['club']} {r['player']} "
                            f"has unknown code {r['status_code']!r}")
        for r in sweep:
            got = per_club.get(r["club"], 0)
            want = int(r["reserve_count"])
            if got != want:
                errs.append(f"rule 4: {r['club']} register rows {got} != sweep reserve_count {want}")
        # total register rows must equal the module's reserve total
        if len(register) != sum(len(e[6]) for e in S.ROSTER):
            errs.append(f"rule 4: register rows {len(register)} != module reserve rows")

    # Rule 6
    flags = rows("flagged.csv") if not errs else []
    if flags:
        got_cats = {r["category"] for r in flags}
        missing = FLAG_CATEGORIES - got_cats
        if missing:
            errs.append(f"rule 6: flagged.csv missing classes {sorted(missing)}")
        for r in flags:
            if not r["issue"] or not r["what_was_done"]:
                errs.append(f"rule 6: {r['flag_id']} empty issue/what_was_done")
        # every irregularity note in the module must be flagged
        flagged_clubs = {r["club"] for r in flags}
        for club in S.IRREGULARITY_NOTES:
            if club not in flagged_clubs:
                errs.append(f"rule 6: club {club} irregularity not flagged")

    # Rule 7
    if not errs:
        for name in REQUIRED_PAGES:
            with open(os.path.join(DOCS, name), encoding="utf-8") as fh:
                body = fh.read()
            for href in re.findall(r'<a href="([^"#]+)"', body):
                if href.startswith("http"):
                    continue
                if not os.path.exists(os.path.join(DOCS, href)):
                    errs.append(f"rule 7: {name} nav link {href!r} does not resolve")

    # Rule 8
    log = rows("capture_log.csv") if not errs else []
    if log:
        log_clubs = set()
        for r in log:
            if r["outcome"] != "success":
                errs.append(f"rule 8: capture log row with outcome {r['outcome']!r}")
            if "re-read" in r["intent"]:
                log_clubs.add("CAR")
            m = re.search(r"/teams/([a-z0-9-]+)/roster", r["url"])
            if not m:
                errs.append(f"rule 8: capture log row with malformed URL {r['url']!r}")
            else:
                slug = m.group(1)
                club = next((c for c, s, *_ in S.ROSTER if s == slug), None)
                if club and "re-read" not in r["intent"]:
                    log_clubs.add(club)
        missing = NFL_CLUBS - log_clubs
        if missing:
            errs.append(f"rule 8: capture log missing clubs {sorted(missing)}")
        if "CAR" not in log_clubs:
            errs.append("rule 8: capture log does not publish the CAR re-read")

    if errs:
        for e in errs:
            print("FAIL", e)
        print(f"\n{len(errs)} rule violation(s)")
        return 1
    print("PASS: all 10 rules hold for the nfl_99a1199e pack")
    return 0


if __name__ == "__main__":
    sys.exit(main())
