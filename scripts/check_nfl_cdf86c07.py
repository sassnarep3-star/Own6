#!/usr/bin/env python3
"""Verifier for pack cdf86c07. Exit 0 only if every rule passes."""
from __future__ import annotations

import csv
import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "nfl_cdf86c07"
DOCS = ROOT / "docs" / "nfl-cdf86c07"
OFFICIAL_HOSTS = ("https://www.nfl.com/",)
ALLOWED_STATUS = {"captured", "partial", "blocked", "open", "decided"}
PAGES = ["index", "standings", "week11", "requirements", "questions", "suggestions", "flags", "sources"]
ABBR_CLUB = {
    "BUF": "Buffalo Bills", "NE": "New England Patriots", "NYJ": "New York Jets", "MIA": "Miami Dolphins",
    "CIN": "Cincinnati Bengals", "PIT": "Pittsburgh Steelers", "CLE": "Cleveland Browns", "BAL": "Baltimore Ravens",
    "JAX": "Jacksonville Jaguars", "HOU": "Houston Texans", "IND": "Indianapolis Colts", "TEN": "Tennessee Titans",
    "KC": "Kansas City Chiefs", "DEN": "Denver Broncos", "LV": "Las Vegas Raiders", "LAC": "Los Angeles Chargers",
    "NYG": "New York Giants", "DAL": "Dallas Cowboys", "WAS": "Washington Commanders", "PHI": "Philadelphia Eagles",
    "DET": "Detroit Lions", "MIN": "Minnesota Vikings", "CHI": "Chicago Bears", "GB": "Green Bay Packers",
    "CAR": "Carolina Panthers", "TB": "Tampa Bay Buccaneers", "NO": "New Orleans Saints", "ATL": "Atlanta Falcons",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks", "LA": "Los Angeles Rams", "AZ": "Arizona Cardinals",
}
FORBIDDEN = re.compile(r"<input|<select|<button|<form|-110\b|moneyline odds|sportsbook", re.I)


def rows(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.hrefs.append(d["href"])
        if "id" in d:
            self.ids.add(d["id"])


def check() -> list[str]:
    errs: list[str] = []

    # 1. standings: 32 unique clubs, official host, arithmetic
    st = rows("standings_2026_11_19.csv")
    if len(st) != 32:
        errs.append(f"standings rows {len(st)} != 32")
    if len({r["club"] for r in st}) != 32:
        errs.append("standings clubs not unique")
    for r in st:
        if not r["source_url"].startswith(OFFICIAL_HOSTS):
            errs.append(f"standings non-official source: {r['club']}")
        w, l, t = int(r["w"]), int(r["l"]), int(r["t"])
        g = w + l + t
        pct = f"{(w + 0.5 * t) / g:.3f}"
        if pct != r["pct"]:
            errs.append(f"pct mismatch {r['club']}: {r['pct']} vs {pct}")
        if int(r["pf"]) - int(r["pa"]) != int(r["net_pts"]):
            errs.append(f"net mismatch {r['club']}")
    W = sum(int(r["w"]) for r in st)
    L = sum(int(r["l"]) for r in st)
    T = sum(int(r["t"]) for r in st)
    PF = sum(int(r["pf"]) for r in st)
    PA = sum(int(r["pa"]) for r in st)
    if (W, L, T) != (149, 149, 2):
        errs.append(f"league W/L/T {(W, L, T)} != (149,149,2)")
    if PF != PA or PF != 6923:
        errs.append(f"league PF/PA {(PF, PA)} != 6923 each")
    standings = {r["club"]: r for r in st}

    # 2. Week-11 slate: 13 games, records agree with standings, 26 teams
    sl = rows("week11_slate.csv")
    if len(sl) != 13:
        errs.append(f"slate rows {len(sl)} != 13")
    teams_playing = []
    for r in sl:
        for side, rec in (("away", "away_record"), ("home", "home_record")):
            club = ABBR_CLUB.get(r[side])
            teams_playing.append(r[side])
            if club is None or standings[club]["w"] + "-" + standings[club]["l"] + ("-" + standings[club]["t"] if standings[club]["t"] != "0" else "") != r[rec]:
                errs.append(f"slate record mismatch {r[side]} {r[rec]}")
        if not r["game_url"].startswith(OFFICIAL_HOSTS):
            errs.append(f"slate non-official url {r['game_url']}")
    byes = rows("byes_week11.csv")
    if len(byes) != 6:
        errs.append(f"byes rows {len(byes)} != 6")
    for b in byes:
        club = ABBR_CLUB.get(b["team_abbr"])
        if club is None:
            errs.append(f"bye unknown team {b['team_abbr']}")
            continue
        s = standings[club]
        rec = s["w"] + "-" + s["l"] + ("-" + s["t"] if s["t"] != "0" else "")
        if rec != b["record_as_printed"]:
            errs.append(f"bye record mismatch {b['team_abbr']}")
        teams_playing.append(b["team_abbr"])
    if len(set(teams_playing)) != 32 or len(teams_playing) != 32:
        errs.append(f"Week-11 teams not a partition of 32 clubs ({len(teams_playing)} entries, {len(set(teams_playing))} unique)")

    # 3. requirements register
    req = rows("requirements.csv")
    if len(req) != 82:
        errs.append(f"requirements rows {len(req)} != 82")
    if len({r["req_id"] for r in req}) != len(req):
        errs.append("requirement ids not unique")
    for r in req:
        if r["status"] not in ALLOWED_STATUS:
            errs.append(f"bad status {r['req_id']}")
        if not r["blocking_gate"] or not r["clearing_number"]:
            errs.append(f"empty gate/clearing {r['req_id']}")

    # 4. questions, suggestions, flags, sources
    if len(rows("questions.csv")) != 15:
        errs.append("questions != 15")
    sug = rows("suggestions.csv")
    if len(sug) != 10 or any(s["pending_human_choice"] != "yes" or s["implemented"] != "no" for s in sug):
        errs.append("suggestions must be 10 rows, all pending and not implemented")
    for f in rows("flagged.csv"):
        if f["blocking_merge"] != "no":
            errs.append(f"flag {f['flag_id']} blocks merge")
        if not f["source_url"].startswith(OFFICIAL_HOSTS):
            errs.append(f"flag non-official source {f['flag_id']}")

    # 5. capture log hashes match artifacts
    for c in rows("capture_log.csv"):
        digest = hashlib.sha256((DATA / c["artifact"]).read_bytes()).hexdigest()
        if digest != c["sha256"]:
            errs.append(f"sha256 mismatch {c['capture_id']}")

    # 6. site: pages exist, no forms/prices, internal links resolve
    for name in PAGES:
        p = DOCS / f"{name}.html"
        if not p.exists():
            errs.append(f"missing page {name}")
            continue
        text = p.read_text(encoding="utf-8")
        if FORBIDDEN.search(text):
            errs.append(f"forbidden token in {name}")
        parser = Links()
        parser.feed(text)
        for h in parser.hrefs:
            if h.startswith("http"):
                if not h.startswith(OFFICIAL_HOSTS) and not h.startswith("https://sassnarep3-star"):
                    errs.append(f"non-official external link in {name}: {h}")
                continue
            target = h.split("#")[0]
            if target and not (DOCS / target).exists():
                errs.append(f"broken internal link {name} -> {h}")
    standings_src = "https://www.nfl.com/standings/division/2026/reg"
    if (DOCS / "standings.html").read_text(encoding="utf-8").count(standings_src) < 32:
        errs.append("standings page missing per-row source links")
    return errs


def main() -> int:
    errs = check()
    if errs:
        print("FAIL")
        for e in errs:
            print(" -", e)
        return 1
    print("OK: cdf86c07 verifier passed (standings 32, slate 13, byes 6, requirements 82, 8 pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
