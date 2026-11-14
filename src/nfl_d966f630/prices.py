"""Price-snapshot store: an append-only ledger of every number this project has
published for a market it originates, with the opening and closing numbers
derived from the ledger rather than asserted.

Store rules (these are the contract the checker enforces)
---------------------------------------------------------
1. One row per (market, publication). A row is never edited; correcting a
   mistake means appending another row, so the audit trail is the series itself.
2. ``role`` is a property of position in the series, not of intent:
   ``open`` is the earliest row for the market, ``close_final`` is the last row
   recorded at or before kickoff once the game is verified final, and
   ``close_provisional`` is the latest row for a game that has not kicked off.
3. Every row carries ``publication_class``. Only ``live_snapshot`` rows are real
   time-stamped quotes; ``retrospective_reconstruction`` rows are what the model
   would have published from data available before kickoff, and
   ``prior_session_publication`` rows are an earlier pack's published number read
   from the repository record at a named commit. Mixing the three silently would
   turn a reconstruction into a quote, so the class is on the row.
4. ``external_market_price`` rows are the *absence* of a book price recorded as
   data. The opening and closing cells are blank and carry the flag id, which is
   the difference between "we do not have this" and "we did not look".
5. ``row_sha256`` chains to the previous row, so a back-edit of an old snapshot
   changes every later hash. The chain is recomputed by the checker.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from . import capture as C
from . import results as R
from .cache import memo

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIOR_CSV = REPO_ROOT / "data" / "nfl_309921cc" / "originated_lines.csv"
LIVE_VINTAGE_WEEK = 9            # Week 10 slate priced on data through Week 9

SNAPSHOT_FIELDS = [
    "snapshot_id", "game_id", "market_id", "market_type", "published_value", "raw_value",
    "unit", "role", "publication_class", "published_on_utc", "publisher", "model_version",
    "model_inputs_as_of_week", "input_source_url", "provenance_url", "market_flag_id",
    "prev_row_sha256", "row_sha256", "official_source_url",
]

MARKET_TYPES = ("side", "total", "moneyline")

MODEL_VERSION = "nfl_d966f630_v1"
PRIOR_MODEL_VERSION = "nfl_309921cc_v1"
# The prior pack's published lines, as committed by PR #82. Resolution of this
# blob was re-confirmed through the GitHub contents API on 2026-11-14 (the local
# clone is shallow, so the object itself is not in this checkout).
PRIOR_PUBLICATION_COMMIT = "46391f1fe1362a0dc376e81f14694c1c1362a91b"
PRIOR_PUBLICATION_PATH = "data/nfl_309921cc/originated_lines.csv"
PRIOR_PUBLICATION_DATE = "2026-11-13"
PRIOR_PUBLICATION_URL = (
    f"https://github.com/sassnarep3-star/Own6/blob/{PRIOR_PUBLICATION_COMMIT}/{PRIOR_PUBLICATION_PATH}"
)


def market_id(game_id: str, market_type: str) -> str:
    return f"{game_id}-{market_type}"


def canonical(row: dict[str, str]) -> str:
    return "|".join(str(row.get(f, "")) for f in SNAPSHOT_FIELDS[:-2])


def row_hash(row: dict[str, str]) -> str:
    return hashlib.sha256(canonical(row).encode("utf-8")).hexdigest()


def build_snapshots(live: list[dict[str, object]], retro: list[dict[str, object]],
                    prior: dict[tuple[str, str], dict[str, str]],
                    published_on: str) -> list[dict[str, str]]:
    """Assemble the ledger for one run.

    ``live``  - this session's origination output for games that have not kicked off
    ``retro`` - the same output for games that are already final (reconstruction)
    ``prior`` - {(game_id, market_type): {"value": ..., "raw": ...}} from the
                repository's earlier publication, used as the opening number
    """
    entries = [(e, "retrospective_reconstruction") for e in retro]
    entries += [(e, "live_snapshot") for e in live]
    rows: list[dict[str, str]] = []
    final_games = {str(e["game_id"]) for e in retro}

    def emit(gid: str, mtype: str, value: str, raw: str, unit: str, cls: str,
             when: str, publisher: str, version: str, vintage: str,
             input_url: str, prov_url: str, flag: str, official_url: str) -> None:
        rows.append({
            "snapshot_id": "", "game_id": gid, "market_id": market_id(gid, mtype),
            "market_type": mtype, "published_value": value, "raw_value": raw, "unit": unit,
            "role": "", "publication_class": cls, "published_on_utc": when,
            "publisher": publisher, "model_version": version,
            "model_inputs_as_of_week": vintage, "input_source_url": input_url,
            "provenance_url": prov_url, "market_flag_id": flag,
            "prev_row_sha256": "", "row_sha256": "",
            "official_source_url": official_url,
        })

    for entry, cls in entries:
        gid = str(entry["game_id"])
        is_retro = cls == "retrospective_reconstruction"
        when = C.CAPTURE_DATE_UTC
        vintage = str(entry["vintage_week"])
        official = str(entry["result_source_url"]) if is_retro else C.link_for("SCHED-W10")
        for mtype in MARKET_TYPES:
            m = entry[mtype]
            value = str(m.get("fair_line", ""))
            raw = _raw_of(mtype, m)
            unit = "american_odds_no_vig" if mtype == "moneyline" else "points"
            prior_row = prior.get((prior_key(gid), mtype)) if not is_retro else None
            # Emit the prior row even when its value is blank: "the earlier
            # publication had nothing here, and this is the reason it printed" is a
            # row of the store, not a gap in it.
            if prior_row:
                emit(gid, mtype, prior_row["value"], prior_row.get("raw", ""), unit,
                     "prior_session_publication", PRIOR_PUBLICATION_DATE,
                     "session 309921cc (this repository)", PRIOR_MODEL_VERSION, vintage,
                     C.link_for("STANDINGS"), PRIOR_PUBLICATION_URL,
                     "" if prior_row.get("value") else (
                         "D966-F03" if mtype == "moneyline" else "D966-F10"), official)
            own_flag = "" if value else "D966-F10"
            emit(gid, mtype, value, raw, unit, cls, when, "session d966f630 (this repository)",
                 MODEL_VERSION, vintage, C.link_for("STANDINGS"),
                 PRIOR_PUBLICATION_URL if is_retro else C.link_for("SCHED-W10"),
                 own_flag, official)

    rows.sort(key=lambda r: (r["game_id"], r["market_type"], r["published_on_utc"]))
    _assign_roles(rows, final_games)
    for i, r in enumerate(rows, start=1):
        r["snapshot_id"] = f"D966-SNAP-{i:04d}"
    _chain(rows)
    return rows


@memo
def prior_rows(path: Path | None = None) -> tuple[dict[tuple[str, str], dict[str, str]], str]:
    """The earlier pack's published numbers, read from the committed CSV.

    Returns the lookup plus a status string. A missing file is not an error: it
    means there is no opening number for these markets, which the ledger records as
    a single-snapshot row rather than a movement.
    """
    path = path or PRIOR_CSV
    if not path.exists():
        return {}, "prior_publication_not_found_in_checkout"
    out: dict[tuple[str, str], dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            gid = row.get("game_id", "").strip()
            if not gid:
                continue
            for mtype, col, raw_col in (("side", "originated_home_spread", "originated_home_spread"),
                                        ("total", "originated_total", "originated_total"),
                                        ("moneyline", "originated_moneyline_home_prob",
                                         "originated_moneyline_home_prob")):
                value = (row.get(col) or "").strip()
                out[(gid, mtype)] = {"value": value, "raw": (row.get(raw_col) or "").strip(),
                                     "status": (row.get("status") or "").strip(),
                                     "note": (row.get(f"{col}_note") or "").strip()}
    return out, "read_from_committed_publication"


def retro_entries(vintage_offset: int = 1) -> list[dict[str, object]]:
    """Reconstructed pre-kickoff numbers for every graded game in the feed."""
    from . import originate as O
    out = []
    for gid, wk, _d, _s, away, home, _ap, _hp, _src in C.FINAL_GAMES:
        vintage = wk - vintage_offset
        inp = O.Inputs(gid, away, home, vintage, R.as_of(vintage))
        entry: dict[str, object] = {"game_id": gid, "vintage_week": vintage,
                                    "result_source_url": C.game_url(gid)}
        entry.update(O.originate(inp))
        out.append(entry)
    return out


def live_entries(vintage_week: int = LIVE_VINTAGE_WEEK) -> list[dict[str, object]]:
    """This run's numbers for Week 10 games that have not been graded yet."""
    from . import originate as O
    graded = {g[0] for g in C.FINAL_GAMES}
    out = []
    for gid, _date, _slot, _net, away, home, _src, _status in C.WEEK10_SLATE:
        if gid in graded:
            continue
        inp = O.Inputs(gid, away, home, vintage_week, R.as_of(vintage_week))
        entry: dict[str, object] = {"game_id": gid, "vintage_week": vintage_week,
                                    "result_source_url": C.link_for("SCHED-W10")}
        entry.update(O.originate(inp))
        out.append(entry)
    return out


@memo
def ledger(published_on: str | None = None) -> list[dict[str, str]]:
    """The store this run writes - shared by the builder, the site and the gate."""
    prior, _status = prior_rows()
    return build_snapshots(live_entries(), retro_entries(), prior,
                           published_on or C.CAPTURE_DATE_UTC)


def prior_key(gid: str) -> str:
    """The prior pack numbered the same games ``W10-01`` .. ``W10-14``."""
    return gid.replace("2026-", "")


def _raw_of(mtype: str, m: dict[str, object]) -> str:
    if mtype == "moneyline":
        p = m.get("fair_prob_home_win", "")
        return f"{float(p):.4f}" if p != "" else ""
    raw = m.get("fair_line_raw", "")
    return f"{float(raw):.3f}" if raw != "" else ""


def _assign_roles(rows: list[dict[str, str]], final_games: set[str]) -> None:
    """Role is position in the series: earliest = open, latest = close.

    A close is ``close_final`` only once the game is verified final in the results
    feed; before kickoff the latest row is ``close_provisional`` and the daily
    runner is expected to append over it.
    """
    by_market: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_market.setdefault(r["market_id"], []).append(r)
    for series in by_market.values():
        series.sort(key=lambda r: (r["published_on_utc"], r["publication_class"]))
        is_final = series[-1]["game_id"] in final_games
        for r in series:
            r["role"] = "open"
        if len(series) == 1:
            if is_final:
                # the one row we hold is the earliest and the latest pre-kickoff number
                series[0]["role"] = "open_and_close_final"
        else:
            last = series[-1]
            last["role"] = "close_final" if is_final else "close_provisional"
            for r in series[1:-1]:
                r["role"] = "intermediate"


def _chain(rows: list[dict[str, str]]) -> None:
    prev = ""
    for r in rows:
        r["prev_row_sha256"] = prev
        r["row_sha256"] = row_hash(r)
        prev = r["row_sha256"]


def verify_chain(rows: list[dict[str, str]]) -> list[str]:
    """Return a message per row whose hash or link does not match its content."""
    bad: list[str] = []
    prev = ""
    for r in rows:
        if r["prev_row_sha256"] != prev:
            bad.append(f"{r['snapshot_id']}: chain break (prev_row_sha256)")
        if r["row_sha256"] != row_hash(r):
            bad.append(f"{r['snapshot_id']}: content hash mismatch")
        prev = r["row_sha256"]
    return bad


def open_close_table(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Opening number, closing number and movement per market, derived from the ledger.

    Read only from the published CSV rows, so the same function works for the
    builder and for the independent checker.
    """
    by_market: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_market.setdefault(r["market_id"], []).append(r)
    final_games = {r["game_id"] for r in rows
                   if r["publication_class"] == "retrospective_reconstruction"}
    out: dict[str, dict[str, str]] = {}
    for market, series in sorted(by_market.items()):
        series.sort(key=lambda r: (r["published_on_utc"], r["publication_class"]))
        opening, closing = series[0], series[-1]
        n = len(series)
        game_id = opening["game_id"]
        is_final = game_id in final_games
        closed = n > 1 or is_final
        move = ""
        move_status = "blank_single_snapshot" if not closed else "not_closed_game_not_final"
        if not opening["published_value"]:
            move_status = ("blank_opening_number_not_published_by_the_prior_session"
                           if n > 1 else "blank_no_number_on_file")
        elif closed:
            try:
                o = float(opening["published_value"])
                c = float(closing["published_value"]) if closed else float("nan")
                if n > 1:
                    move = f"{c - o:+.2f}"
                    move_status = "measured_within_store"
                else:
                    move = "0.00"
                    move_status = "single_snapshot_open_and_close_are_the_same_row"
            except (TypeError, ValueError):
                move_status = "blank_unparsable_value"
        out[market] = {
            "market_id": market,
            "game_id": opening["game_id"],
            "market_type": opening["market_type"],
            "n_snapshots": str(n),
            "opening_number": opening["published_value"],
            "opening_published_on": opening["published_on_utc"],
            "opening_class": opening["publication_class"],
            "opening_source_url": opening["provenance_url"],
            "closing_number": closing["published_value"] if closed else "",
            "closing_published_on": closing["published_on_utc"] if closed else "",
            "closing_role": closing["role"] if closed else "not_yet_closed",
            "closing_source_url": closing["provenance_url"] if closed else "",
            "movement_closing_minus_opening": move,
            "movement_status": move_status,
            "movement_note": (
                "the prior publication left this market blank (its own note explains why), so there is "
                "no opening number to move from; see flag D966-F03"
                if not opening["published_value"] and n > 1 else
                "open and close come from two different model versions, so movement mixes "
                "a model change with the passage of time; see flag D966-F02"
                if n > 1 and opening["model_version"] != closing["model_version"] else
                "single snapshot: the opening number is the closing number, movement is zero "
                "by construction and is not evidence of a stable market" if n == 1 and closed else
                "same model version, movement is pure re-origination" if n > 1 else
                "no closing number yet: the game has not kicked off"
            ),
            "official_source_url": opening["official_source_url"],
            "game_final": "yes" if is_final else "no",
            "movement_flag_id": ("D966-F03" if not opening["published_value"] and n > 1 else
                                 "D966-F16" if n == 1 and closed and move_status.startswith("single_snapshot")
                                 else ("D966-F02" if n > 1 and opening["model_version"] != closing["model_version"]
                                       else "")),
        }
    return out


CAPTURE_ATTEMPT_LOG = [
    {
        "attempt_id": "D966-ATT-01",
        "market_family": "NFL game side, total, moneyline",
        "source_class": "league official site",
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "read_on": C.CAPTURE_DATE_UTC,
        "outcome": "no_price_published",
        "detail": "The Week 10 schedule page was read in full for this pack. It prints matchups, dates, networks, "
                   "FINAL scores and team records; it prints no betting line, no price and no closing number.",
        "consequence": "market_line_* and difference_* columns stay blank for every market",
        "flag_id": "D966-F01",
        "official_source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
    },
    {
        "attempt_id": "D966-ATT-02",
        "market_family": "NFL game side, total, moneyline",
        "source_class": "league official injury report",
        "source_url": "https://www.nfl.com/injuries/",
        "read_on": C.CAPTURE_DATE_UTC,
        "outcome": "no_price_published",
        "detail": "Read in full for the Week 10 slate (28 clubs, 347 listed rows). Carries designations and practice "
                   "participation only - no market numbers of any kind.",
        "consequence": "injury data feeds depth_of_replacement; it cannot feed the market line",
        "flag_id": "D966-F01",
        "official_source_url": "https://www.nfl.com/injuries/",
    },
    {
        "attempt_id": "D966-ATT-03",
        "market_family": "any book price",
        "source_class": "commercial sportsbook data feed",
        "source_url": "",
        "read_on": C.CAPTURE_DATE_UTC,
        "outcome": "not_available_in_environment",
        "detail": "No licensed odds feed is reachable from this session's network allowlist (github.com, "
                   "registry.npmjs.org, pypi.org and their file hosts only). Operator sportsbook pages are "
                   "third-party commercial pages, not league-official sources, and the repository's own "
                   "rights boundary notes that systematic retrieval of league content is restricted.",
        "consequence": "opening and closing book numbers cannot be recorded; the suggestion register asks the "
                   "owner to license a feed before any CLV or edge gate is switched on",
        "flag_id": "D966-F01",
        "official_source_url": "https://github.com/sassnarep3-star/Own6/blob/main/data/nfl_309921cc/sources.csv",
    },
    {
        "attempt_id": "D966-ATT-04",
        "market_family": "player-prop totals for prop combos",
        "source_class": "league official per-game statistics",
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
        "read_on": C.CAPTURE_DATE_UTC,
        "outcome": "not_collected_for_this_pack",
        "detail": "Prop settlement needs per-player game statistics. Final team scores were collected; player "
                   "statistics pages were not read in this session, so no prop leg is settled here.",
        "consequence": "prop-combination strategies are specified and gate-blocked with zero selections",
        "flag_id": "D966-F06",
        "official_source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
    },
]
