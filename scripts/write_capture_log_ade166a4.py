"""Write capture_log.csv for the ade166a4 pack (hashes computed from artifact bytes)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.nfl_ade166a4.capture import append_capture_log  # noqa: E402

ROWS = [
    {
        "read_id": "R101",
        "source_url": "https://www.nfl.com/injuries/league/2026/reg11",
        "page_title_as_read": "Official NFL Injury Report for Players - Week 11 of the 2026 Season",
        "what_was_read": "all 13 games, 253 player rows + 2 No-Injuries markers, 16 game statuses "
                         "(Thursday IND@HOU only), 25-headline news rail (7 chunks)",
        "read_on_utc": "2026-11-19T11:07:00Z",
        "access_method": "page-fetch tool (agent session), in-session read",
        "artifact_path": "data/nfl_ade166a4/raw/injuries_reg11_2026-11-19_b.md",
    },
    {
        "read_id": "R102",
        "source_url": "https://www.nfl.com/standings/division/2026/reg",
        "page_title_as_read": "2026 NFL Division Standings",
        "what_was_read": "all 32 clubs: W-L-T, PCT, PF, PA, NET PTS, STRK (2 chunks)",
        "read_on_utc": "2026-11-19T11:08:00Z",
        "access_method": "page-fetch tool (agent session), in-session read",
        "artifact_path": "data/nfl_ade166a4/raw/standings_2026-11-19_b.md",
    },
    {
        "read_id": "R103",
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "page_title_as_read": "NFL Week 11 Schedule 2026: Games, Times, Matchups & Tickets",
        "what_was_read": "13-game slate with times/networks/records, 6-team bye list, "
                         "Mexico City international marker, TBD footnote (3 chunks)",
        "read_on_utc": "2026-11-19T11:10:00Z",
        "access_method": "page-fetch tool (agent session), in-session read",
        "artifact_path": "data/nfl_ade166a4/raw/week11_schedule_2026-11-19_b.md",
    },
    {
        "read_id": "R104",
        "source_url": "https://www.nfl.com/transactions/league/reserve-list/2026/11",
        "page_title_as_read": "2026 NFL reserve-list by month | NFL.com",
        "what_was_read": "November reserve table, 25 rows, dates 11/10-11/18, no pagination (2 chunks)",
        "read_on_utc": "2026-11-19T11:11:00Z",
        "access_method": "page-fetch tool (agent session), in-session read",
        "artifact_path": "data/nfl_ade166a4/raw/transactions_2026-11-19_b.md",
    },
    {
        "read_id": "R105",
        "source_url": "https://www.nfl.com/transactions/league/trades/2026/11",
        "page_title_as_read": "2026 NFL trades by month | NFL.com",
        "what_was_read": "November trades table, 12 rows, dates 11/06-11/10, no Waddle row (1 chunk)",
        "read_on_utc": "2026-11-19T11:11:30Z",
        "access_method": "page-fetch tool (agent session), in-session read",
        "artifact_path": "data/nfl_ade166a4/raw/transactions_2026-11-19_b.md",
    },
]

if __name__ == "__main__":
    print("capture_log ->", append_capture_log(ROWS))
