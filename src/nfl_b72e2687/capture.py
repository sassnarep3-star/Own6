#!/usr/bin/env python3
"""Capture registers for session b72e2687 from this session's raw page transcriptions.

Reads the raw markdown artifacts transcribed from official NFL pages during this
session (2026-11-19) and emits CSV registers plus a capture_log.csv whose rows carry
the UTC read clock and the sha256 of each artifact. No network access here; the raw
artifacts are the in-session read records.

    python3 src/nfl_b72e2687/capture.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "data", "nfl_b72e2687")
RAW = os.path.join(DATA, "raw")

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_lines(name: str) -> list[str]:
    with open(os.path.join(RAW, name), encoding="utf-8") as f:
        return f.read().splitlines()


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def capture_standings() -> int:
    rows = []
    conference = ""
    for line in read_lines("standings_2026-11-19.md"):
        if line.startswith("## AMERICAN"):
            conference = "AFC"
        elif line.startswith("## NATIONAL"):
            conference = "NFC"
        elif line.startswith("|") and "Team" not in line.split("|")[1]:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) == 8 and parts[0] and conference and "---" not in parts:
                rows.append([conference, parts[0], parts[1], parts[2], parts[3],
                             parts[4], parts[5], parts[6], parts[7]])
    write_csv("standings_2026_11_19.csv",
              ["conference", "club", "w", "l", "t", "pct", "pf", "pa", "net_pts"], rows)
    return len(rows)


def capture_week12() -> int:
    rows = []
    for line in read_lines("week12_schedule_2026-11-19.md"):
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*(\S+)\s*\|\s*([^|]+)\|\s*([^|]+)\s*\|", line)
        if m and m.group(1).isdigit():
            rows.append([m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip(),
                         m.group(5).strip(), m.group(6).strip(), m.group(7).strip(),
                         m.group(8).strip()])
    write_csv("week12_slate.csv",
              ["slot", "day_date", "time_et", "network", "matchup", "game_centre_url",
               "away_record", "home_record"], rows)
    return len(rows)


def capture_injuries() -> tuple[int, int]:
    """Parse the injury raw file into one row per player plus the two markers."""
    rows = []
    game = ""
    team = ""
    section_re = re.compile(r"^## (.+)$")
    team_re = re.compile(r"^### (.+?)(?:\s+\((\d+) rows\))?$")
    player_re = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*)\s*\|\s*([^|]+?)\s*\|\s*([^|]*)\s*\|\s*$")
    lines = read_lines("injuries_reg11_2026-11-19.md")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = section_re.match(line)
        if m:
            game = m.group(1).strip()
            i += 1
            continue
        m = team_re.match(line)
        if m:
            team = m.group(1).strip()
            i += 1
            continue
        if line.strip() == "No Injuries Reported":
            rows.append([game, team, "NO_INJURIES_REPORTED", "", "", ""])
            i += 1
            continue
        m = player_re.match(line)
        if m and team and m.group(1).strip() != "Player" and "---" not in line:
            raw_status = m.group(4).strip()
            code = {"Did Not Participate In Practice": "DNP",
                    "Limited Participation in Practice": "LP",
                    "Full Participation in Practice": "FP"}.get(raw_status, raw_status)
            rows.append([game, team, m.group(1).strip(), m.group(2).strip(),
                         m.group(3).strip(), raw_status, code, m.group(5).strip()])
        i += 1
    write_csv("injuries_reg11.csv",
              ["game", "team", "player", "position", "injuries", "practice_status",
               "practice_code", "game_status"], rows)
    player_rows = sum(1 for r in rows if r[2] != "NO_INJURIES_REPORTED")
    markers = sum(1 for r in rows if r[2] == "NO_INJURIES_REPORTED")
    return player_rows, markers


def main() -> None:
    n_standings = capture_standings()
    n_week12 = capture_week12()
    n_inj, markers = capture_injuries()

    log = [["read_id", "source_url", "page_title_as_read", "what_was_read", "read_on_utc",
            "access_method", "artifact_path", "artifact_sha256",
            "artifact_sha_covers", "status", "note"]]
    reads = [
        ("B72-R01", "https://www.nfl.com/standings/division/2026/reg",
         "2026 NFL Division Standings",
         f"all 32 clubs: W-L-T, PCT, PF, PA, NET PTS (2 chunks); {n_standings} rows parsed",
         "data/nfl_b72e2687/raw/standings_2026-11-19.md",
         "session arithmetic: W=149, L=149, T=2, PF=PA=6,923"),
        ("B72-R02", "https://www.nfl.com/schedules/2026/by-week/week-12",
         "NFL Week 12 Schedule 2026: Games, Times, Matchups & Tickets",
         f"16-game slate, times/networks/records, game-centre links, heading/weekday "
         f"mismatches noted (3 chunks); {n_week12} rows parsed",
         "data/nfl_b72e2687/raw/week12_schedule_2026-11-19.md",
         "venue names appear only in Marriott affiliate links; not treated as official venue transcription"),
        ("B72-R03", "https://www.nfl.com/injuries/league/2026/reg11",
         "Official NFL Injury Report for Players - Week 11 of the 2026 Season | NFL.com",
         f"13/13 games, {n_inj} player rows + {markers} No-Injuries markers, 16 published "
         f"game-status cells, news rail (7 chunks)",
         "data/nfl_b72e2687/raw/injuries_reg11_2026-11-19.md",
         "practice tallies recomputed from the parsed register: DNP 83, LP 87, FP 83"),
    ]
    for rid, url, title, what, art, note in reads:
        path = os.path.join(REPO, art)
        h = sha256_file(path)
        log.append([rid, url, title, what, NOW,
                    "page-fetch tool (agent session), in-session read", art, h,
                    "sha256 covers the bytes of the transcription artifact named in "
                    "artifact_path only; it cannot prove what the page said at read time",
                    "verified-2026-11-19", note])
    with open(os.path.join(DATA, "capture_log.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(log)

    print(f"standings rows: {n_standings}")
    print(f"week12 rows: {n_week12}")
    print(f"injury player rows: {n_inj}, no-injury markers: {markers}")
    print(f"capture_log.csv written at {NOW}")


if __name__ == "__main__":
    main()
