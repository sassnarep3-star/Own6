#!/usr/bin/env python3
"""Build nfl_2dd0cbcb data CSVs from the verified raw transcription artifacts.

Run:  python3 scripts/build_nfl_2dd0cbcb_data.py
Idempotent: rewrites the capture CSVs and the capture log from raw/ on every run.
Registers (requirements/rechecks/flagged/sources/questions/suggestions) are
authored by the session and are NOT rewritten by this script.

Sources (all transcribed in-session 2026-11-19, see capture_log.csv):
  raw/week12_venues_2026-11-19.md          -> week12_venues.csv
  raw/week12_injuries_probe_2026-11-19.md  -> thursday_status_reg11.csv
  raw/reserve_list_2026-11-19.md           -> reserve_rows.csv
  raw/club_depth_retests_2026-11-19.md     -> depth_retest.csv
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACK = os.path.join(REPO, "data", "nfl_2dd0cbcb")
RAW = os.path.join(PACK, "raw")

sys.path.insert(0, os.path.join(REPO, "src"))
from nfl_2dd0cbcb import capture  # noqa: E402

READ_ON = "2026-11-19T11:08:00Z"  # session read clock (UTC); artifact-write bound
SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-12"


def _read(name: str) -> str:
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        return fh.read()


def norm_venue(s: str) -> str:
    """Upper-case, drop non-alphanumerics (handles LEVI'S® vs Levis)."""
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def build_week12_venues() -> int:
    rows = []
    for line in _read("week12_venues_2026-11-19.md").splitlines():
        if not line.startswith("VENUE|"):
            continue
        parts = line.split("|")
        _, match, date, kickoff, network, loc, stadium, hotel, url = parts
        fold = lambda s: re.sub(r"\s+", " ", s.strip().casefold())  # noqa: E731
        raw_differs = "no" if fold(stadium) == fold(hotel) else "yes"
        norm_differs = "yes" if norm_venue(stadium) != norm_venue(hotel) else "no"
        rows.append({
            "game_date": date, "kickoff_et": kickoff, "network": network,
            "away": match.split("@")[0], "home": match.split("@")[1],
            "location_gamecentre": loc, "venue_stadium_gamecentre": stadium,
            "venue_hotel_param_schedulepage": hotel,
            "venue_raw_differs": raw_differs,
            "venue_mismatch_after_normalization": norm_differs,
            "game_url": url, "schedule_url": SCHED_URL,
            "read_on_utc": READ_ON,
        })
    rows.sort(key=lambda r: (r["game_date"], r["kickoff_et"], r["away"]))
    out = os.path.join(PACK, "week12_venues.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def build_thursday_status() -> int:
    rows = []
    for line in _read("week12_injuries_probe_2026-11-19.md").splitlines():
        if not line.startswith("THUR|"):
            continue
        _, club, player, pos, inj, prac, game = line.split("|")
        rows.append({
            "game": "IND@HOU 2026-11-19 (Week 11 Thursday, 8:15 PM ET, Prime Video)",
            "club": club, "player": player, "position": pos,
            "injury": inj, "practice_status": prac, "game_status": game,
            "source_url": "https://www.nfl.com/injuries/league/2026/reg11",
            "read_on_utc": READ_ON,
        })
    out = os.path.join(PACK, "thursday_status_reg11.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def build_reserve_rows() -> int:
    rows = []
    for line in _read("reserve_list_2026-11-19.md").splitlines():
        if not line.startswith("RES|"):
            continue
        _, date, name, club, txn = line.split("|")
        rows.append({
            "date": date, "name": name, "club": club, "transaction": txn,
            "window_first_date_rendered": "11/10",
            "window_last_date_rendered": "11/18",
            "row_count_on_page": str(len(rows) + 1),  # provisional; fixed below
            "source_url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
            "read_on_utc": READ_ON,
        })
    n = str(len(rows))
    for r in rows:
        r["row_count_on_page"] = n
    out = os.path.join(PACK, "reserve_rows.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def build_depth_retest() -> int:
    _read("club_depth_retests_2026-11-19.md")  # existence check; counts are documented per section
    az_rows = 29  # Offense 11 + Defense 12 + Special Teams 6, as enumerated in Section A
    gb_rows = 29  # Offense 12 (incl. one blank-position row) + Defense 11 + ST 6, per Section B
    rows = [
        {
            "club": "AZ", "page": "https://www.azcardinals.com/team/depth-chart",
            "render": "text-table", "text_rows_count": str(az_rows),
            "date_stamp_as_read": "(none — no publication date rendered on the page)",
            "jersey_prefixes": "no",
            "qb_group_as_read": "Carson Beck | Josh Johnson | Joey Aguilar",
            "brissett_present": "no", "finding": (
                "QB1 is Carson Beck; Brissett absent; Murray and Minshew also absent "
                "while the game centre still lists G. Minshew as season passing leader "
                "— blank+flag, no inference"
            ),
        },
        {
            "club": "GB", "page": "https://www.packers.com/team/depth-chart",
            "render": "text-table", "text_rows_count": str(gb_rows),
            "date_stamp_as_read": "Unofficial, Nov. 10, 2026",
            "jersey_prefixes": "yes",
            "qb_group_as_read": "10 Jordan Love | 6 Tyrod Taylor",
            "brissett_present": "n/a", "finding": (
                "jersey prefixes still present (strip+keep-raw exercised); footer "
                "unchanged since the 09:01Z read (nine days stale, self-labelled "
                "Unofficial); Kitan Oladapo printed in both S rows"
            ),
        },
        {
            "club": "HOU", "page": "https://www.houstontexans.com/team/depth-chart",
            "render": "image-only", "text_rows_count": "0",
            "date_stamp_as_read": "(none rendered)",
            "jersey_prefixes": "n/a",
            "qb_group_as_read": "",
            "brissett_present": "n/a", "finding": (
                "image-only render persists (third consecutive session); club banner "
                "names 'Reliant Stadium' for tonight's game while schedule hotel param "
                "says NRG Stadium"
            ),
        },
    ]
    for r in rows:
        r["source_url"] = r.pop("page")
        r["read_on_utc"] = READ_ON
    out = os.path.join(PACK, "depth_retest.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return len(rows)


LOG_ROWS = [
    ("R001", "https://www.nfl.com/injuries/league/2026/reg12 (renders Week 11; selector ends at WEEK 11)",
     "Official NFL Injury Report for Players - Week 11 of the 2026 Season (as rendered)",
     "reg12 probe: week selector WEEK 1..11, no WEEK 12; Thursday IND@HOU full tables — 26 rows, 16 game statuses; blank-status notes",
     "data/nfl_2dd0cbcb/raw/week12_injuries_probe_2026-11-19.md"),
    ("R002", "https://www.nfl.com/schedules/2026/by-week/week-12",
     "NFL Week 12 Schedule 2026: Games, Times, Matchups & Tickets",
     "16-game slate verbatim headings and lines; heading/weekday contradictions still present; TBD-games flex block; week nav",
     "data/nfl_2dd0cbcb/raw/week12_schedule_page_2026-11-19.md"),
    ("R003", "https://www.nfl.com/transactions/league/reserve-list/2026/11",
     "2026 NFL reserve-list by month | NFL.com",
     "render-window probe: 25 rows, window 11/10-11/18, no intra-month pagination; position column blank on all rows",
     "data/nfl_2dd0cbcb/raw/reserve_list_2026-11-19.md"),
    ("R004", "https://www.nfl.com/games/<16 fixtures>-2026-reg-12 (game centres; URLs in week12_venues.csv)",
     "Week 12 Game Centres (16 fetched)",
     "Location + Stadium fields for all 16 Week-12 fixtures, with schedule-page hotel param as cross-check only",
     "data/nfl_2dd0cbcb/raw/week12_venues_2026-11-19.md"),
    ("R005", "https://www.azcardinals.com/team/depth-chart",
     "Arizona Cardinals Official Depth Chart",
     "full text tables; QB group Beck/Johnson/Aguilar; no Brissett/Murray/Minshew rows; OLB shared cell Collins+Browning; no publication date",
     "data/nfl_2dd0cbcb/raw/club_depth_retests_2026-11-19.md"),
    ("R006", "https://www.packers.com/team/depth-chart",
     "Green Bay Packers Depth Chart",
     "full text tables with jersey prefixes; footer 'Unofficial, Nov. 10, 2026' unchanged; Oladapo in both S rows",
     "data/nfl_2dd0cbcb/raw/club_depth_retests_2026-11-19.md"),
    ("R007", "https://www.houstontexans.com/team/depth-chart",
     "Depth Chart | Houston Texans - HoustonTexans.com",
     "image-only render confirmed again; club banner text names Reliant Stadium for tonight's game",
     "data/nfl_2dd0cbcb/raw/club_depth_retests_2026-11-19.md"),
]


def build_capture_log() -> int:
    rows = []
    for rid, url, title, what, art in LOG_ROWS:
        path = os.path.join(REPO, art)
        rows.append({
            "read_id": rid, "source_url": url, "page_title_as_read": title,
            "what_was_read": what, "read_on_utc": READ_ON,
            "artifact_path": art,
            "artifact_sha256": capture.sha256_file(path),
            "status": "verified-2026-11-19",
            "note": ("in-session page read on 2026-11-19 (UTC); read_on_utc is the "
                     "artifact-write clock, an upper bound on the fetch time; sha256 "
                     "covers the transcription artifact only and cannot prove what the "
                     "page said" + ("; multiple read_ids share this artifact"
                                    if "depth_retests" in art else "")),
        })
    capture.write_capture_log(rows)
    return len(rows)


def main() -> int:
    counts = {
        "week12_venues": build_week12_venues(),
        "thursday_status": build_thursday_status(),
        "reserve_rows": build_reserve_rows(),
        "depth_retest": build_depth_retest(),
        "capture_log": build_capture_log(),
    }
    for k, v in counts.items():
        print(f"{k}: {v} rows")
    problems = capture.verify_capture_log()
    if problems:
        for p in problems:
            print("CAPTURE-LOG PROBLEM:", p)
        return 1
    print("capture log hashes verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
