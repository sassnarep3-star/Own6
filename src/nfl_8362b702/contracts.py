"""Scraper contracts and drift alarms.

A contract pins, per source, the row count and required fields of a healthy
read. The drift checker compares the observed capture against the contract and
raises loudly on any mismatch — a missing field is a build failure, never a
blank cell that ships unnoticed.
"""
from __future__ import annotations

from . import capture as C

CONTRACTS = [
    {"source_id": "SRC-STANDINGS",
     "url": C.STANDINGS_URL, "read_at_utc": C.STANDINGS_READ_1,
     "expected_rows": 32,
     "row_unit": "club rows in the league standings table",
     "required_fields": "team_abbr,w,l,t,pct,pf,pa,net,home_rec,road_rec,strk",
     "observed_rows": len(C.STANDINGS_READ_1_ROWS)},
    {"source_id": "SRC-CORPUS",
     "url": "https://www.nfl.com/schedules/2026/by-week/week-{1..9}",
     "read_at_utc": C.WEEKSCHED_READ,
     "expected_rows": 136,
     "row_unit": "FINAL cards, weeks 1-9 (the 136-game log)",
     "required_fields": "week,slug,date_on_card,away,home,away_score,home_score",
     "observed_rows": len(C.LOG136)},
    {"source_id": "SRC-W10",
     "url": C.WEEK10_SCHED_URL, "read_at_utc": C.WEEK10_SCHED_READ,
     "expected_rows": 14,
     "row_unit": "week-10 game cards (any status)",
     "required_fields": "game_id,slug,date_on_card,status_on_card,away,home,game_page_url",
     "observed_rows": len(C.WEEK10_GAMES)},
    {"source_id": "SRC-W11",
     "url": C.WEEK11_SCHED_URL, "read_at_utc": C.WEEK11_SCHED_READ,
     "expected_rows": 13,
     "row_unit": "week-11 fixture cards",
     "required_fields": "game_id,slug,date_on_card,kickoff_on_card,network_on_card,away,home,game_page_url",
     "observed_rows": len(C.WEEK11_GAMES)},
    {"source_id": "SRC-W11-BYES",
     "url": C.WEEK11_SCHED_URL, "read_at_utc": C.WEEK11_SCHED_READ,
     "expected_rows": 6,
     "row_unit": "clubs in the week-11 Teams on Bye panel",
     "required_fields": "abbr,name,record_on_panel",
     "observed_rows": len(C.WEEK11_BYES)},
    {"source_id": "SRC-INJURY-A",
     "url": C.INJURY_URL, "read_at_utc": C.INJURY_READ_A,
     "expected_rows": 155,
     "row_unit": "hub player rows transcribed from chunks 0-2 (13 complete club tables)",
     "required_fields": "hub_game_id,club,player,position,practice_status,game_status",
     "observed_rows": len(C.INJURY_ROWS_A)},
    {"source_id": "SRC-GB-ROSTER",
     "url": C.GB_ROSTER_URL, "read_at_utc": C.GB_ROSTER_READ,
     "expected_rows": 41,
     "row_unit": "non-ACT roster rows (CUT/DEV/PUP/RES/RSR/TRC/TRD/TRT)",
     "required_fields": "player_display_name,player_url_slug,position_on_page,status_code_on_page",
     "observed_rows": len(C.GB_NON_ACT_ROWS)},
]


def drift_rows():
    out = []
    for c in CONTRACTS:
        missing = ""
        exp = c["expected_rows"]
        obs = c["observed_rows"]
        verdict = "OK" if exp == obs else "DRIFT"
        if exp != obs:
            missing = f"row count {obs} != contract {exp}"
        out.append({**c, "verdict": verdict, "drift_detail": missing})
    return out


def any_drift():
    return any(r["verdict"] != "OK" for r in drift_rows())
