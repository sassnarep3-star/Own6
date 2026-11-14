"""Price-snapshot store.

Requirement: "record opening and closing numbers for every market we
originate".  The store is a real table with a real schema: one row per
originated market per week, with an opening column and a closing column
plus the provenance of each.

Reality check: the NFL does not publish point spreads, totals or
moneylines on any page readable in this session.  Every price cell is
therefore left **blank** and stamped ``unverified_no_official_price``.
The store is built and the rows are enumerated so that the moment a
licensable/official price feed exists the columns fill without a schema
change - but until then G5 (price-snapshot gate) fails closed and nothing
can be promoted out of paper.
"""
from __future__ import annotations

from typing import Dict, List

from . import dataset

UNVERIFIED_PRICE = "unverified_no_official_price"

#: Market families this desk originates for each game.
MARKET_FAMILIES = [
    ("side", "Point spread on the home team"),
    ("total", "Game total (both teams combined)"),
    ("moneyline_home", "Moneyline, home team"),
    ("moneyline_away", "Moneyline, away team"),
    ("team_total_home", "Home team total (derived)"),
    ("team_total_away", "Away team total (derived)"),
]

SCORE_URL = "https://www.nfl.com/scores/2026/week-10"


def build(games=None) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for g in dataset.slate():
        for fam, desc in MARKET_FAMILIES:
            rows.append({
                "season": 2026,
                "week": 10,
                "market_id": f"2026-10-{g['game_slug']}-{fam}",
                "game_slug": g["game_slug"],
                "market_family": fam,
                "market_description": desc,
                "opening_capture_window": "T-6d (first publish of the official "
                                          "weekly schedule) "
                                          if g["game_status"] == "Scheduled" else "pre-kickoff",
                "opening_price": "",
                "opening_price_source_url": "",
                "opening_status": UNVERIFIED_PRICE,
                "closing_capture_window": "kickoff",
                "closing_price": "",
                "closing_price_source_url": "",
                "closing_status": UNVERIFIED_PRICE,
                "price_capture_method": "none - no official price feed readable",
                "official_game_url": f"https://www.nfl.com/games/{g['game_slug']}",
                "official_slate_url": SCORE_URL,
            })
    return rows


def coverage(rows) -> Dict[str, object]:
    n = len(rows)
    op = sum(1 for r in rows if r["opening_price"] not in ("", None))
    cl = sum(1 for r in rows if r["closing_price"] not in ("", None))
    return {"markets_originated": n, "with_opening_price": op,
            "with_closing_price": cl,
            "opening_coverage": f"{op}/{n}", "closing_coverage": f"{cl}/{n}",
            "status": "fail_closed" if (op < n or cl < n) else "pass",
            "official_slate_url": SCORE_URL}
