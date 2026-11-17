"""Availability, reserve list, stale-depth conflicts, and the injury delta.

Three distinct things are kept apart on purpose, because the brief asks for each:

1. **A level** — "how many players are listed as Out". Published, but never used
   as a signal (the brief: the injury signal must be a surprise, never a level).
2. **A delta** — the change between two timestamped reads of the same source. This
   is the signal. The earlier read is the sibling pack's 2026-11-15T23:58Z hub
   read (read directly from this repo's committed capture, credited as such); the
   later read is this session's 2026-11-17T00:47Z read.
3. **Evidence of who actually started** — this session holds *no* game book, so
   every ``actual_start`` cell is blank and the reason is printed. A replacement
   is never inferred from a blank injury-report cell.
"""

from __future__ import annotations

import csv
import os

from . import capture as C
from . import injury_capture as IC

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRIOR_SERIES = os.path.join(REPO, "data", "nfl_8362b702", "injury_series.csv")

# Positions whose loss removes a starter from a trench or coverage unit. Used
# only to group the published rows for review; it is not a depth model.
UNIT_BY_POSITION = {
    "QB": "offense", "RB": "offense", "WR": "offense", "TE": "offense", "FB": "offense",
    "T": "offense", "G": "offense", "C": "offense", "OL": "offense",
    "DT": "defense", "DE": "defense", "LB": "defense", "CB": "defense", "S": "defense",
    "DB": "defense",
    "K": "special", "P": "special", "LS": "special",
}


def load_prior_series() -> list[dict]:
    if not os.path.exists(PRIOR_SERIES):
        return []
    with open(PRIOR_SERIES, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def club_rows(club: str) -> list[dict]:
    out = []
    for player, pos, inj, practice, game in IC.CLUB_TABLES.get(club, []):
        out.append({
            "club": club,
            "player": player,
            "position": pos,
            "unit": UNIT_BY_POSITION.get(pos, ""),
            "injury_text": inj,
            "practice_status": practice,
            "game_status": game,
            "read_at_utc": IC.READ_AT_UTC,
            "source_url": IC.SOURCE_URL,
            "name_source": "url_slug" if (club, player) in IC.NAME_SOURCE_NOTES else "page_link_text",
        })
    return out


def all_rows() -> list[dict]:
    rows = []
    for club in IC.CLUBS_PRESENT:
        rows.extend(club_rows(club))
    return rows


def reserve_rows() -> list[dict]:
    out = []
    for club, date_on_page, player in C.RESERVE_NOV_2026:
        # cross-check against this session's hub read
        on_hub = any(p == player for (p, *_r) in IC.CLUB_TABLES.get(club, []))
        out.append({
            "club": club,
            "date_on_page": date_on_page,
            "player": player,
            "transaction_on_page": "Reserve/Injured",
            "appears_on_week10_hub_at_this_read": "yes" if on_hub else "no",
            "interpretation": (
                "on the reserve list and also on the weekly report"
                if on_hub else
                "on the reserve list and NOT on the weekly report - 'not listed' does not mean available"
            ),
            "source_url": C.URL_RESERVE,
            "hub_url": C.URL_INJURIES,
        })
    return out


def trade_rows() -> list[dict]:
    out = []
    for frm, to, date_on_page, player in C.TRADES_NOV_2026:
        hubs = []
        for club in (frm, to):
            if any(p == player for (p, *_r) in IC.CLUB_TABLES.get(club, [])):
                hubs.append(club)
        out.append({
            "from_club": frm,
            "to_club": to,
            "date_on_page": date_on_page,
            "player": player,
            "transaction_on_page": "Traded",
            "hub_club_at_this_read": ",".join(hubs) if hubs else "absent from the week-10 hub",
            "stale_risk": (
                "yes - the hub still names the sending club" if hubs and hubs[0] == frm
                else ("no" if not hubs else "hub names the receiving club")
            ),
            "source_url": C.URL_TRANSACTIONS,
        })
    return out


def club_rollup() -> list[dict]:
    """Per club: designated-out count, doubtful, questionable, by unit."""
    out = []
    for club in IC.CLUBS_PRESENT:
        rows = club_rows(club)
        out_tab = [r for r in rows if r["game_status"] == "Out"]
        dbt = [r for r in rows if r["game_status"] == "Doubtful"]
        q = [r for r in rows if r["game_status"] == "Questionable"]
        dnp = [r for r in rows if r["practice_status"] == "Did Not Participate In Practice"]
        reserve = [r for r in C.RESERVE_NOV_2026 if r[0] == club]
        out.append({
            "club": club,
            "rows_on_hub": len(rows),
            "designated_out": len(out_tab),
            "designated_doubtful": len(dbt),
            "designated_questionable": len(q),
            "no_game_designation": len([r for r in rows if not r["game_status"]]),
            "did_not_practice": len(dnp),
            "out_on_offense": len([r for r in out_tab if r["unit"] == "offense"]),
            "out_on_defense": len([r for r in out_tab if r["unit"] == "defense"]),
            "named_out_players": "; ".join(r["player"] + " (" + r["position"] + ")" for r in out_tab),
            "reserve_list_entries_this_month": len(reserve),
            "reserve_players": "; ".join(r[2] for r in reserve),
            "replacement_named_on_official_page": "",  # never filled from a blank cell
            "actual_starters_evidence": "",
            "blank_reason_replacement": (
                "no official page read this session names the player who replaced any of these; "
                "the weekly report has no depth column and no game book was obtained"
            ),
            "source_url": IC.SOURCE_URL,
            "reserve_url": C.URL_RESERVE,
        })
    return out


def injury_deltas() -> list[dict]:
    """Join the prior two reads with this session's read, per (club, player)."""
    prior = load_prior_series()
    prior_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for r in prior:
        key = (r["club"], r["player"])
        prior_by_key.setdefault(key, {})[r["read_at_utc"]] = (
            f"practice={r['practice_status']};game={r['game_status']}"
        )
    now = {}
    for r in all_rows():
        now[(r["club"], r["player"])] = f"practice={r['practice_status']};game={r['game_status']}"

    out = []
    covered_clubs = {c for (c, _p) in prior_by_key}
    for key, states in sorted(prior_by_key.items()):
        reads = sorted(states)
        latest_prior = states[reads[-1]]
        cur = now.get(key, "")
        if not cur:
            change = "disappeared from the hub between reads"
        elif cur == latest_prior:
            change = "no change"
        else:
            before_g = latest_prior.split("game=")[-1].strip()
            after_g = cur.split("game=")[-1].strip()
            before_p = latest_prior.split("practice=")[-1].split(";")[0]
            after_p = cur.split("practice=")[-1].split(";")[0]
            if before_g != after_g and before_p == after_p:
                change = f"game designation {before_g or 'blank'} -> {after_g or 'blank'}"
            elif before_p != after_p and before_g == after_g:
                change = f"practice {before_p or 'blank'} -> {after_p or 'blank'}"
            else:
                change = "both columns changed"
        out.append({
            "club": key[0],
            "player": key[1],
            "prior_read_at_utc": reads[-1],
            "prior_state": latest_prior,
            "now_read_at_utc": IC.READ_AT_UTC,
            "now_state": cur or "(absent)",
            "delta_kind": change,
            "is_surprise": "yes" if change not in ("no change",) else "no",
            "source_url": IC.SOURCE_URL,
        })
    # players on the hub now, in a club that a prior read did cover, that no
    # prior read carried. Clubs never read before are NOT a delta: they are new
    # coverage, and calling them a change would invent a change that did not happen.
    for key, cur in sorted(now.items()):
        if key not in prior_by_key and key[0] in covered_clubs:
            out.append({
                "club": key[0], "player": key[1],
                "prior_read_at_utc": "2026-11-16T00:50:00Z",
                "prior_state": "(absent from the pack's two reads)",
                "now_read_at_utc": IC.READ_AT_UTC,
                "now_state": cur,
                "delta_kind": "appeared on the hub after the prior reads",
                "is_surprise": "yes",
                "source_url": IC.SOURCE_URL,
            })
    return out


def designations_moved(deltas: list[dict]) -> list[dict]:
    """Only the rows where the *game* designation moved: the surprise set."""
    keep = []
    for d in deltas:
        k = d["delta_kind"]
        if k.startswith("game designation") or "appeared" in k or "disappeared" in k:
            keep.append(d)
    return keep


def availability_graph_nodes() -> list[dict]:
    """Expected-vs-actual nodes. ``actual`` is blank everywhere: no game book."""
    nodes = []
    for r in all_rows():
        if not r["game_status"]:
            continue
        nodes.append({
            "node_id": f"{r['club']}:{r['player']}:{r['position']}",
            "club": r["club"],
            "player": r["player"],
            "position": r["position"],
            "unit": r["unit"],
            "expected_status_from_official_report": r["game_status"],
            "expected_evidence_url": IC.SOURCE_URL,
            "actual_start": "",
            "actual_snap_share": "",
            "actual_evidence_url": "",
            "confidence": "expected-only" if r["game_status"] == "Out" else "expected-listed",
            "blank_reason_actual": (
                "Game Books and snap counts were not obtained; the NFL.com game centre read this "
                "session shows overview/statistics tabs only. Actual participation is not inferred."
            ),
        })
    return nodes


def depth_slot_notes() -> list[dict]:
    """What this session can and cannot say about depth of the replacement."""
    return [
        {
            "claim": "a club's published depth chart is the only official source naming a backup",
            "status": "not obtained this session",
            "detail": "no club depth-chart page was read this session; earlier packs found 32/32 unverified or unreachable",
            "source_url": C.URL_RESERVE,
        },
        {
            "claim": "snap counts could stand in for depth",
            "status": "no official snapshot source read",
            "detail": "the game-centre pages read this session expose overview and statistics tabs, no snap-count table",
            "source_url": C.URL_GAME_LAC_BAL,
        },
        {
            "claim": "a player who is Out is replaced by 'the next man up' at the same position",
            "status": "rejected",
            "detail": "that is an inference, not a published fact; the league publishes the designation, not the replacement",
            "source_url": IC.SOURCE_URL,
        },
        {
            "claim": "reserve/IR entries explain blank weekly-report cells",
            "status": "supported for one case this session",
            "detail": "Malik Willis is on the reserve list 11/10 and absent from the week-10 hub (conflict C-02)",
            "source_url": C.URL_RESERVE,
        },
    ]
