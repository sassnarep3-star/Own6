"""Price-snapshot store and the price-data policy (session 67233566).

Two things live here and they are coupled on purpose:

``POLICY`` is the price-data decision that must exist BEFORE any backtest is published. It says
which price numbers this repository is allowed to publish, from where, and what happens when the
source does not exist. Because no official NFL page prints a betting price, the policy keeps every
``market_*`` column empty and forbids any ROI, CLV or "edge in cents" claim. The builder refuses to
write a results table while the policy row for the current read date is missing, so the ordering
requirement is enforced by code, not by convention.

``snapshot_rows`` is the store. One row per (fixture, market, role) with an opening and a closing
number for every market we originate - for originated markets those numbers are our own published
fair values, timestamped, and hash-chained so a later edit to an earlier row changes every
downstream hash and is visible. The chain is what makes "immutable" checkable here:
``verify_chain`` is run by the verifier and by CI.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .model import MODEL_VERSION, Forecast

PUBLISHER = "session 67233566 (this repository)"

POLICY = {
    "policy_id": "PX-67233566-01",
    "decided_on_utc": "2026-11-15",
    "status": "in force before any backtest was published",
    "rules": [
        {
            "rule_id": "PX-01",
            "rule": "A price may be published only from a source whose terms allow the read and "
                     "whose page prints the number. No page reachable in this repository's evidence "
                     "set prints an NFL betting price, so market_open, market_close and "
                     "difference_to_market stay empty on every row.",
            "consequence": "ROI, CLV and 'cents of edge' are not computable and are not published.",
        },
        {
            "rule_id": "PX-02",
            "rule": "Our own originated fair value IS a price and is stored like one: opening = "
                     "first published value for the fixture, closing = last published value before "
                     "kickoff, both with a UTC clock time and the model version that produced them.",
            "consequence": "Opening/closing movement of our own line is measurable today; movement "
                           "relative to a market is not.",
        },
        {
            "rule_id": "PX-03",
            "rule": "Residual against the market is published on a fixed schedule (Wed/Thu/Fri and "
                     "the Saturday before each Sunday slate) whether or not a market number exists; "
                     "an empty residual row is a published result, not a missing one.",
            "consequence": "The residual schedule table has a row per fixture per scheduled read, and "
                           "each row carries the reason it is empty.",
        },
        {
            "rule_id": "PX-04",
            "rule": "A capture attempt is logged whether it succeeded or failed. A blank column must "
                     "always be traceable to an attempt, never to silence.",
            "consequence": "market_price_capture_log.csv lists the hosts tried and the outcome.",
        },
        {
            "rule_id": "PX-05",
            "rule": "No strategy may be promoted from paper to live on the strength of a number that "
                     "depends on a price. Proper-score skill is necessary but not sufficient.",
            "consequence": "Every strategy is 'paper' in this pack, including the best-ranked one.",
        },
    ],
}

MARKETS = ("side", "total_T1_offdef", "total_T2_halfshrunk", "moneyline_home", "moneyline_away")


@dataclass
class Snapshot:
    snapshot_id: str
    captured_at_utc: str
    fixture_id: str
    market: str
    role: str  # open | close
    value: str
    unit: str
    model_version: str
    inputs_sha256: str
    note: str
    prev_row_sha256: str = ""
    row_sha256: str = ""


def _row_hash(s: Snapshot, prev: str) -> str:
    body = "|".join(
        [s.snapshot_id, s.captured_at_utc, s.fixture_id, s.market, s.role, s.value, s.unit,
         s.model_version, s.inputs_sha256, s.note, prev]
    )
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def inputs_sha(forecast: Forecast) -> str:
    return hashlib.sha256(
        json.dumps(forecast.inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def market_value(forecast: Forecast, market: str) -> tuple[str, str]:
    """Return (value, unit) for one market from one forecast."""
    if market == "side":
        return f"{forecast.fair_spread_line}", "points_home_line"
    if market == "total_T1_offdef":
        return f"{forecast.estimator_totals['T1_offdef']}", "points_game_total"
    if market == "total_T2_halfshrunk":
        return f"{forecast.estimator_totals['T2_halfshrunk']}", "points_game_total"
    if market == "moneyline_home":
        return forecast.fair_moneyline.get("home", ""), "american_odds_vig_free"
    if market == "moneyline_away":
        return forecast.fair_moneyline.get("away", ""), "american_odds_vig_free"
    raise ValueError(f"unknown market {market!r}")


def snapshot_rows(forecasts_open: list[Forecast], forecasts_close: list[Forecast],
                  open_at: str, close_at: str) -> list[Snapshot]:
    """Opening = the first forecast published for the fixture; closing = the last one before kickoff.

    ``forecasts_open`` and ``forecasts_close`` are two vintages of the same fixture list (here: the
    pre-registered fit through week 9 as the opening, and the fit through week 10 finals as the
    closing) which is exactly how a book's open/close pair is produced: same market, different time.
    """
    by_id_open = {f.fixture.game_id: f for f in forecasts_open}
    rows: list[Snapshot] = []
    prev = "GENESIS"
    seq = 0
    for fc in forecasts_close:
        fo = by_id_open.get(fc.fixture.game_id)
        for market in MARKETS:
            for role, src, stamp in (("open", fo, open_at), ("close", fc, close_at)):
                if src is None:
                    continue
                value, unit = market_value(src, market)
                seq += 1
                s = Snapshot(
                    snapshot_id=f"SNAP-67233566-{seq:04d}",
                    captured_at_utc=stamp,
                    fixture_id=src.fixture.game_id,
                    market=market,
                    role=role,
                    value=value,
                    unit=unit,
                    model_version=MODEL_VERSION,
                    inputs_sha256=inputs_sha(src),
                    note="" if value else "no value: probability is 0 or 1 at this rounding",
                    prev_row_sha256=prev,
                )
                s.row_sha256 = _row_hash(s, prev)
                prev = s.row_sha256
                rows.append(s)
    return rows


def movement(rows: list[Snapshot]) -> dict[str, dict[str, str]]:
    """Opening -> closing movement per fixture, from the store itself (never recomputed by hand)."""
    out: dict[str, dict[str, str]] = {}
    for market in MARKETS:
        for fid in sorted({r.fixture_id for r in rows}):
            o = next((r for r in rows if r.fixture_id == fid and r.market == market and r.role == "open"), None)
            c = next((r for r in rows if r.fixture_id == fid and r.market == market and r.role == "close"), None)
            if not o or not c:
                continue
            rec = out.setdefault(fid, {})
            rec[f"{market}_open"] = o.value
            rec[f"{market}_close"] = c.value
            try:
                delta = float(c.value) - float(o.value)
                rec[f"{market}_movement"] = f"{delta:+g}" if o.unit.startswith("points") else "n/a_odds"
            except ValueError:
                rec[f"{market}_movement"] = ""
    return out


def verify_chain(rows: list[Snapshot]) -> list[str]:
    """Recompute the chain; any edited, inserted or removed row shows up as a message."""
    problems: list[str] = []
    prev = "GENESIS"
    for s in rows:
        expect = _row_hash(s, prev)
        if s.row_sha256 != expect:
            problems.append(f"{s.snapshot_id}: row hash does not match its content and predecessor")
        if s.prev_row_sha256 != prev:
            problems.append(f"{s.snapshot_id}: predecessor link broken")
        prev = s.row_sha256 or prev
    return problems
