#!/usr/bin/env python3
"""Build nfl_a67ddef8 data CSVs from the verified raw transcription artifacts.

Run:  python scripts/build_nfl_a67ddef8_data.py
Idempotent: rewrites the five data CSVs from raw/ every run.

Sources (all transcribed in-session 2026-11-19, see capture_log.csv):
  raw/standings_2026-11-19.md      -> standings_2026_11_19.csv
  raw/injuries_reg11_2026-11-19.md -> injuries_reg11.csv
  raw/week11_schedule_2026-11-19.md + raw/venues_gamecentres_2026-11-19.md
                                    -> week11_slate.csv
  raw/week10_schedule_2026-11-19.md -> week10_finals.csv
  raw/week12_schedule_2026-11-19.md -> week12_slate.csv
"""
from __future__ import annotations

import csv
import os
import re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACK = os.path.join(REPO, "data", "nfl_a67ddef8")
RAW = os.path.join(PACK, "raw")

READ_ON = "2026-11-19T00:00:00Z"  # session read date (UTC); see capture_log rows


def _read(name: str) -> str:
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        return fh.read()


def build_standings() -> int:
    text = _read("standings_2026-11-19.md")
    rows = []
    div = ""
    for line in text.splitlines():
        if line.startswith("### "):
            div = line[4:].strip()
            continue
        m = re.match(
            r"^([A-Za-z0-9 .]+?) \| (\d+) \| (\d+) \| (\d+) \| ([0-9.]+) \| "
            r"(-?\d+) \| (-?\d+) \| (-?\d+) \| (\d+[WL])$",
            line.strip(),
        )
        if not m:
            continue
        club, w, l, t, pct, pf, pa, net, strk = m.groups()
        rows.append({
            "club": club.strip(), "division": div,
            "w": w, "l": l, "t": t, "pct": pct,
            "pf": pf, "pa": pa, "net_pts": net, "streak": strk,
            "source_url": "https://www.nfl.com/standings/division/2026/reg",
            "read_on_utc": READ_ON,
        })
    assert len(rows) == 32, f"expected 32 clubs, got {len(rows)}"
    path = os.path.join(PACK, "standings_2026_11_19.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def build_injuries() -> int:
    text = _read("injuries_reg11_2026-11-19.md")
    rows = []
    game = team = ""
    src = "https://www.nfl.com/injuries/league/2026/reg11"
    for line in text.splitlines():
        if line.startswith("## ") and not line.startswith("### "):
            hdr = line[3:].strip()
            if "THURSDAY" in hdr or "SUNDAY" in hdr or "MONDAY" in hdr:
                game = hdr
            continue
        if line.startswith("### "):
            team = re.sub(r"\s*\(\d+ rows\)\s*$", "", line[4:].strip())
            continue
        if line.strip() in ("No Injuries Reported",):
            rows.append({
                "game": game, "team": team, "player": "",
                "position": "", "injury": "",
                "practice_status": "", "game_status": "",
                "note": "No Injuries Reported",
                "source_url": src, "read_on_utc": READ_ON,
            })
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 5 or not parts[0] or parts[0].startswith("#"):
            continue
        player, position, injury, practice, gstat = parts
        if player == "Player":  # table header repeated
            continue
        rows.append({
            "game": game, "team": team, "player": player,
            "position": position,
            "injury": "" if injury == "(blank)" else injury,
            "practice_status": "" if practice == "(blank)" else practice,
            "game_status": "" if gstat == "(blank)" else gstat,
            "note": "",
            "source_url": src, "read_on_utc": READ_ON,
        })
    player_rows = [r for r in rows if r["player"]]
    assert len(player_rows) == 253, f"expected 253 player rows, got {len(player_rows)}"
    assert sum(1 for r in rows if r["note"]) == 2, "expected 2 No-Injuries markers"
    assert sum(1 for r in player_rows if r["game_status"]) == 16, "expected 16 game statuses"
    path = os.path.join(PACK, "injuries_reg11.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


# --- slates: verified verbatim from the schedule + game-centre reads -------------

W11 = [
    # date, kickoff_et, network, away, away_rec, home, home_rec,
    # stadium (game centre), location (game centre), hotel_param (schedule page), game_url
    ("2026-11-19", "8:15 PM", "PRIME", "IND", "3-7", "HOU", "3-6",
     "RELIANT STADIUM", "HOUSTON, TX", "NRG Stadium", "colts-at-texans"),
    ("2026-11-22", "1:00 PM", "CBS", "MIA", "1-8", "BUF", "8-1",
     "HIGHMARK STADIUM", "ORCHARD PARK, NY", "Highmark Stadium", "dolphins-at-bills"),
    ("2026-11-22", "1:00 PM", "FOX", "BAL", "4-6", "CAR", "4-5",
     "BANK OF AMERICA STADIUM", "CHARLOTTE, NC", "Bank of America Stadium", "ravens-at-panthers"),
    ("2026-11-22", "1:00 PM", "FOX", "NO", "3-6", "CHI", "7-2",
     "SOLDIER FIELD", "CHICAGO, IL", "Soldier Field", "saints-at-bears"),
    ("2026-11-22", "1:00 PM", "FOX", "TEN", "1-8", "DAL", "4-6",
     "AT&T STADIUM", "ARLINGTON, TX", "AT&T Stadium", "titans-at-cowboys"),
    ("2026-11-22", "1:00 PM", "FOX", "TB", "3-6", "DET", "7-2",
     "FORD FIELD", "DETROIT, MI", "Ford Field", "buccaneers-at-lions"),
    ("2026-11-22", "1:00 PM", "CBS", "AZ", "3-7", "KC", "7-2",
     "ARROWHEAD STADIUM", "KANSAS CITY, MO", "GEHA Field at Arrowhead Stadium", "cardinals-at-chiefs"),
    ("2026-11-22", "1:00 PM", "CBS", "PIT", "6-3", "PHI", "2-7",
     "LINCOLN FINANCIAL FIELD", "PHILADELPHIA, PA", "Lincoln Financial Field", "steelers-at-eagles"),
    ("2026-11-22", "4:05 PM", "FOX", "NYJ", "2-8", "LAC", "1-8",
     "SOFI STADIUM", "INGLEWOOD, CA", "SoFi Stadium", "jets-at-chargers"),
    ("2026-11-22", "4:25 PM", "CBS", "JAX", "7-2", "NYG", "5-3-1",
     "METLIFE STADIUM", "EAST RUTHERFORD, NJ", "MetLife Stadium", "jaguars-at-giants"),
    ("2026-11-22", "4:25 PM", "CBS", "LV", "4-6", "DEN", "7-2",
     "EMPOWER FIELD AT MILE HIGH", "DENVER, CO", "Empower Field at Mile High", "raiders-at-broncos"),
    ("2026-11-22", "8:20 PM", "NBC", "MIN", "7-2", "SF", "8-1",
     "ESTADIO BANORTE", "MEXICO CITY", "", "vikings-at-49ers"),  # international: no hotel param
    ("2026-11-23", "8:15 PM", "ESPN", "CIN", "7-2", "WAS", "3-5-1",
     "NORTHWEST STADIUM", "LANDOVER, MD", "FedEx Field", "bengals-at-commanders"),
]


def build_week11() -> int:
    rows = []
    for (date, ko, net, away, arec, home, hrec,
         stadium, loc, hotel, slug) in W11:
        rows.append({
            "game_date": date, "kickoff_et": ko, "network": net,
            "away": away, "away_record": arec, "home": home, "home_record": hrec,
            "venue_stadium_gamecentre": stadium,
            "venue_location_gamecentre": loc,
            "venue_hotel_param_schedulepage": hotel,
            "venue_match": "exact" if hotel.lower() == stadium.lower() else (
                "n/a-international" if not hotel else "mismatch-or-variance"),
            "game_url": f"https://www.nfl.com/games/{slug}-2026-reg-11",
            "schedule_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
            "read_on_utc": READ_ON,
        })
    # mark the four known non-exact cases precisely
    notes = {
        "colts-at-texans": "mismatch: hotel param NRG Stadium (current) vs game centre RELIANT STADIUM (legacy name)",
        "cardinals-at-chiefs": "variance: hotel param GEHA Field at Arrowhead Stadium (sponsor prefix) vs game centre ARROWHEAD STADIUM",
        "vikings-at-49ers": "international fixture; schedule card badge 'Mexico City', no hotel param; game centre gives stadium",
        "bengals-at-commanders": "mismatch: hotel param FedEx Field (legacy) vs game centre NORTHWEST STADIUM (current)",
    }
    for r in rows:
        slug = r["game_url"].split("/games/")[1].replace("-2026-reg-11", "")
        r["venue_note"] = notes.get(slug, "exact match (case-insensitive)")
        if slug in notes:
            r["venue_match"] = "mismatch" if "mismatch" in notes[slug] else (
                "variance" if "variance" in notes[slug] else "n/a-international")
    path = os.path.join(PACK, "week11_slate.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


W10 = [
    ("2026-11-12", "WAS", 24, "NYG", 21, "Thursday Night Football, November 12th", "commanders-at-giants"),
    ("2026-11-15", "NE", 10, "DET", 35, "International Game, November 15th (Munich)", "patriots-at-lions"),
    ("2026-11-15", "KC", 35, "ATL", 13, "Sunday, November 15th", "chiefs-at-falcons"),
    ("2026-11-15", "HOU", 24, "CLE", 27, "Sunday, November 15th", "texans-at-browns"),
    ("2026-11-15", "MIN", 30, "GB", 10, "Sunday, November 15th", "vikings-at-packers"),
    ("2026-11-15", "MIA", 22, "IND", 24, "Sunday, November 15th", "dolphins-at-colts"),
    ("2026-11-15", "CAR", 20, "NO", 17, "Sunday, November 15th", "panthers-at-saints"),
    ("2026-11-15", "BUF", 31, "NYJ", 12, "Sunday, November 15th", "bills-at-jets"),
    ("2026-11-15", "JAX", 40, "TEN", 23, "Sunday, November 15th", "jaguars-at-titans"),
    ("2026-11-15", "LA", 34, "AZ", 6, "Sunday, November 15th", "rams-at-cardinals"),
    ("2026-11-15", "SEA", 21, "LV", 13, "Sunday, November 15th", "seahawks-at-raiders"),
    ("2026-11-15", "SF", 46, "DAL", 40, "Sunday, November 15th", "49ers-at-cowboys"),
    ("2026-11-15", "PIT", 18, "CIN", 38, "Sunday Night Football, November 15th", "steelers-at-bengals"),
    ("2026-11-16", "LAC", 23, "BAL", 20, "Monday Night Football, November 16th", "chargers-at-ravens"),
]


def build_week10() -> int:
    rows = []
    for date, away, as_, home, hs, section, slug in W10:
        rows.append({
            "game_date": date, "away": away, "away_score": as_,
            "home": home, "home_score": hs, "status": "FINAL",
            "schedule_section": section,
            "margin_home": hs - as_,
            "game_url": f"https://www.nfl.com/games/{slug}-2026-reg-10",
            "schedule_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "read_on_utc": READ_ON,
        })
    path = os.path.join(PACK, "week10_finals.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


W12 = [
    ("2026-11-25", "8:00 PM", "NETFLIX", "GB", "6-4", "LA", "6-4", "", "packers-at-rams", ""),
    ("2026-11-26", "1:00 PM", "CBS", "CHI", "7-2", "DET", "7-2", "", "bears-at-lions", ""),
    ("2026-11-26", "4:30 PM", "FOX", "PHI", "2-7", "DAL", "4-6", "", "eagles-at-cowboys", ""),
    ("2026-11-26", "8:20 PM", "NBC", "KC", "7-2", "BUF", "8-1", "", "chiefs-at-bills",
     "section heading on page reads 'Sunday Night Football, November 26th' while game line says Thursday, November 26th"),
    ("2026-11-27", "3:00 PM", "PRIME", "DEN", "7-2", "PIT", "6-3", "ACRISURE STADIUM", "broncos-at-steelers",
     "section heading on page reads 'Thursday Night Football, November 27th' while game line says Friday, November 27th; hotel param on same card says 'Heinz Field Stadium' (stale)"),
    ("2026-11-29", "1:00 PM", "CBS", "NO", "3-6", "CIN", "7-2", "", "saints-at-bengals", ""),
    ("2026-11-29", "1:00 PM", "CBS", "BAL", "4-6", "HOU", "3-6", "", "ravens-at-texans", ""),
    ("2026-11-29", "1:00 PM", "FOX", "NYG", "5-3-1", "IND", "3-7", "", "giants-at-colts", ""),
    ("2026-11-29", "1:00 PM", "CBS", "NYJ", "2-8", "MIA", "1-8", "", "jets-at-dolphins", ""),
    ("2026-11-29", "1:00 PM", "FOX", "ATL", "3-7", "MIN", "7-2", "", "falcons-at-vikings", ""),
    ("2026-11-29", "1:00 PM", "FOX", "TEN", "1-8", "JAX", "7-2", "", "titans-at-jaguars", ""),
    ("2026-11-29", "4:05 PM", "CBS", "NE", "5-5", "LAC", "1-8", "", "patriots-at-chargers", ""),
    ("2026-11-29", "4:25 PM", "FOX", "WAS", "3-5-1", "AZ", "3-7", "", "commanders-at-cardinals", ""),
    ("2026-11-29", "4:25 PM", "FOX", "SEA", "6-4", "SF", "8-1", "", "seahawks-at-49ers", ""),
    ("2026-11-29", "8:20 PM", "NBC", "LV", "4-6", "CLE", "6-4", "", "raiders-at-browns", ""),
    ("2026-11-30", "8:15 PM", "ESPN", "CAR", "4-5", "TB", "3-6", "", "panthers-at-buccaneers", ""),
]


def build_week12() -> int:
    rows = []
    for date, ko, net, away, arec, home, hrec, stadium, slug, note in W12:
        rows.append({
            "game_date": date, "kickoff_et": ko, "network": net,
            "away": away, "away_record": arec, "home": home, "home_record": hrec,
            "venue_stadium_gamecentre": stadium,  # blank: not read from game centre (except DEN@PIT)
            "note": note,
            "game_url": f"https://www.nfl.com/games/{slug}-2026-reg-12",
            "schedule_url": "https://www.nfl.com/schedules/2026/by-week/week-12",
            "read_on_utc": READ_ON,
        })
    path = os.path.join(PACK, "week12_slate.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main() -> None:
    counts = {
        "standings": build_standings(),
        "injuries": build_injuries(),
        "week11_slate": build_week11(),
        "week10_finals": build_week10(),
        "week12_slate": build_week12(),
    }
    for k, v in counts.items():
        print(f"{k}: {v} rows")


if __name__ == "__main__":
    main()
