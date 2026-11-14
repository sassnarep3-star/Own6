"""Price-snapshot store: opening and closing numbers for every market we originate.

Why opens and closes at all
---------------------------
A single "market line" cannot answer the only question that matters after the
fact: did the number we beat still exist when the money went down? A strategy
that "beat the close" is making a different — and much harder — claim than one
that beat a stale open. So every market originated by this pack is stored twice,
with the provider's own open and close fields, a capture timestamp, and the
prices (vig) alongside the line. Market moves are computed, never copied.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "nfl_f4", "raw")
OUT = os.path.join(ROOT, "data", "nfl_f4")

PROVIDER = "DraftKings (published via ESPN odds endpoint)"
PROVIDER_STATUS = {
    "official_nfl_partner": True,
    "note": ("DraftKings is one of the three NFL official sports-betting partners "
             "named on nfl.com (source S02). The price feed itself is the operator's "
             "own published number relayed by ESPN's public odds endpoint; it is an "
             "operator quote, not an NFL publication."),
}

PRICE_FIELDS = [
    "snapshot_id", "game_key", "week", "provider_event_id", "away", "home",
    "market", "selection", "snapshot_type", "line", "price_american",
    "price_decimal", "implied_prob_raw", "captured_at_utc", "read_date",
    "provider", "source_url", "status",
]

MARKET_FIELDS = [
    "market_id", "game_key", "week", "away", "home", "market", "selection",
    "origination_order", "open_line", "close_line", "line_move",
    "open_price_american", "close_price_american", "price_move_american",
    "move_direction", "move_is_to_favourite", "close_status",
    "source_url", "status",
]


def american_to_decimal(price: int) -> float:
    """American odds -> decimal odds. Caller must not pass 0."""
    if price > 0:
        return 1.0 + price / 100.0
    return 1.0 + 100.0 / abs(price)


def implied_prob(price: int) -> float:
    """Raw (vigged) implied probability of an American price."""
    dec = american_to_decimal(price)
    return 1.0 / dec


def devig_two_way(price_a: int, price_b: int) -> Tuple[float, float]:
    """Multiplicative two-way de-vig. Returns (p_a, p_b); p_a + p_b == 1."""
    ia, ib = implied_prob(price_a), implied_prob(price_b)
    s = ia + ib
    return ia / s, ib / s


def _signed(diff: float) -> str:
    if diff == 0:
        return "0"
    return f"{diff:+g}"


def _num(x: str) -> Optional[float]:
    if x is None or str(x).strip() == "":
        return None
    return float(x)


def load_prices() -> List[dict]:
    path = os.path.join(RAW, "prices.csv")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def snapshot_rows() -> List[dict]:
    """Flatten the raw capture into one row per (market, selection, snapshot)."""
    out: List[dict] = []
    for r in load_prices():
        for snap in ("open", "close"):
            line = r.get(f"{snap}_line", "")
            price = r.get(f"{snap}_price", "")
            if price == "" and line == "":
                continue
            pl = _num(price)
            out.append({
                "snapshot_id": f"{r['provider_event_id']}-{r['market']}-{r['selection']}-{snap}",
                "game_key": f"{r['away']}@{r['home']}",
                "week": 10,
                "provider_event_id": r["provider_event_id"],
                "away": r["away"],
                "home": r["home"],
                "market": r["market"],
                "selection": r["selection"],
                "snapshot_type": snap,
                "line": line,
                "price_american": price,
                "price_decimal": f"{american_to_decimal(int(pl)):.4f}" if pl is not None else "",
                "implied_prob_raw": f"{implied_prob(int(pl)):.4f}" if pl is not None else "",
                "captured_at_utc": f"{r['read_date']}T00:00:00Z",
                "read_date": r["read_date"],
                "provider": PROVIDER,
                "source_url": r["source_url"],
                "status": "verified",
            })
    return out


ORIGINATION_ORDER = {"moneyline": 1, "spread": 2, "total": 3}


def market_rows() -> List[dict]:
    """One row per originated market/selection with open vs close compared."""
    out: List[dict] = []
    for r in load_prices():
        key = f"{r['away']}@{r['home']}"
        market, sel = r["market"], r["selection"]
        o_line, c_line = _num(r["open_line"]), _num(r["close_line"])
        o_price = _num(r["open_price"])
        c_price = _num(r["close_price"])
        move = ""
        direction = ""
        to_fav = ""
        if o_line is not None and c_line is not None:
            d = c_line - o_line
            move = _signed(d)
            if market == "total":
                direction = "up" if d > 0 else ("down" if d < 0 else "flat")
                to_fav = "n/a_total"
            else:
                # Home spread stored as home's own number, so a larger
                # (less negative) home number = home got less favoured.
                direction = "toward_home" if d > 0 else ("toward_away" if d < 0 else "flat")
                to_fav = "yes" if (d < 0 and sel == r["home"]) or (d > 0 and sel == r["away"]) else ("no" if d else "flat")
        price_move = ""
        if o_price is not None and c_price is not None:
            price_move = _signed(c_price - o_price)
        out.append({
            "market_id": f"{r['provider_event_id']}-{market}-{sel}",
            "game_key": key,
            "week": 10,
            "away": r["away"],
            "home": r["home"],
            "market": market,
            "selection": sel,
            "origination_order": ORIGINATION_ORDER[market],
            "open_line": r["open_line"],
            "close_line": r["close_line"],
            "line_move": move,
            "open_price_american": r["open_price"],
            "close_price_american": r["close_price"],
            "price_move_american": price_move,
            "move_direction": direction,
            "move_is_to_favourite": to_fav,
            "close_status": r["close_status"],
            "source_url": r["source_url"],
            "status": "derived",
        })
    return out


def coverage_summary() -> Dict[str, object]:
    prices = load_prices()
    games = {p["provider_event_id"] for p in prices}
    settled = {p["provider_event_id"] for p in prices if p["close_status"] == "final"}
    markets = sum(3 for _ in games)  # spread, total, moneyline per game
    return {
        "games_priced": len(games),
        "games_with_settled_close": len(settled),
        "markets_originated": markets,
        "snapshots_stored": len(snapshot_rows()),
        "provider": PROVIDER,
        "provider_is_official_nfl_partner": True,
    }


def write_csv(path: str, fields: Iterable[str], rows: Iterable[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_all() -> None:
    write_csv(os.path.join(OUT, "price_snapshots.csv"), PRICE_FIELDS, snapshot_rows())
    write_csv(os.path.join(OUT, "markets.csv"), MARKET_FIELDS, market_rows())
