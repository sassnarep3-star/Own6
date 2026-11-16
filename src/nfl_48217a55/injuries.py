"""Week 10 injury-report parsing, rollups and replacement-depth floors.

Design rule that shapes every function here: the official report tells us who is on the
report and what their designation is. It does **not** tell us who will replace them, and
it gives no depth order. So every "replacement" figure published by this pack is a
*floor* on the number of club-position groups affected, never a named starter/backup
pair. A named replacement is published only where an official page names one.
"""

from __future__ import annotations

from . import capture as C

#: Designation strings exactly as the official table prints them.
DESIGNATIONS = ("Out", "Doubtful", "Questionable")

PRACTICE_STATUSES = (
    "Did Not Participate In Practice",
    "Limited Participation in Practice",
    "Full Participation in Practice",
)

#: Positions grouped into the units used for the depth-of-replacement rollup.
UNIT_BY_POSITION = {
    "QB": "Quarterback",
    "RB": "Backfield",
    "FB": "Backfield",
    "WR": "Receivers",
    "TE": "Receivers",
    "T": "Offensive line",
    "G": "Offensive line",
    "C": "Offensive line",
    "OT": "Offensive line",
    "OL": "Offensive line",
    "LS": "Offensive line",
    "DE": "Defensive front",
    "DT": "Defensive front",
    "NT": "Defensive front",
    "DL": "Defensive front",
    "LB": "Linebackers",
    "OLB": "Linebackers",
    "Edge": "Linebackers",
    "CB": "Secondary",
    "S": "Secondary",
    "SAF": "Secondary",
    "DB": "Secondary",
    "K": "Specialists",
    "P": "Specialists",
}

OFFENSE_UNITS = {"Quarterback", "Backfield", "Receivers", "Offensive line"}


def unit_for(position: str) -> str:
    return UNIT_BY_POSITION.get(position.strip(), "Unmapped")


def rows():
    """The injury report as dictionaries, with derived unit and side-of-ball columns."""
    out = []
    for club, player, pos, injury, practice, game in C.INJURY_REPORT:
        unit = unit_for(pos)
        out.append(
            {
                "club": club,
                "player": player,
                "position": pos,
                "unit": unit,
                "side": "offense" if unit in OFFENSE_UNITS else "defense"
                if unit in ("Defensive front", "Linebackers", "Secondary") else "specialists",
                "injury": injury,
                "practice_status": practice,
                "game_status": game,
                "source_url": C.SOURCE_URL["S1"],
                "read_at_utc": C.CAPTURE_CLOCK_UTC,
            }
        )
    return out


def clubs_on_report():
    seen, order = set(), []
    for r in rows():
        if r["club"] not in seen:
            seen.add(r["club"])
            order.append(r["club"])
    return order


def club_rollup():
    """Per-club counts. `listed_no_game_status` counts rows where the official table left
    the game-status cell blank; those are *not* 'available' and are published as blank."""
    out = []
    for club in clubs_on_report():
        rs = [r for r in rows() if r["club"] == club]
        counts = {d: sum(1 for r in rs if r["game_status"] == d) for d in DESIGNATIONS}
        out.append(
            {
                "club": club,
                "rows_on_report": len(rs),
                "out": counts["Out"],
                "doubtful": counts["Doubtful"],
                "questionable": counts["Questionable"],
                "listed_no_game_status": sum(1 for r in rs if r["game_status"] == ""),
                "dnp": sum(1 for r in rs if r["practice_status"].startswith("Did Not")),
                "limited": sum(1 for r in rs if r["practice_status"].startswith("Limited")),
                "full": sum(1 for r in rs if r["practice_status"].startswith("Full")),
                "offense_out": sum(1 for r in rs if r["game_status"] == "Out" and r["side"] == "offense"),
                "defense_out": sum(1 for r in rs if r["game_status"] == "Out" and r["side"] == "defense"),
                "source_url": C.SOURCE_URL["S1"],
                "read_at_utc": C.CAPTURE_CLOCK_UTC,
            }
        )
    return out


def depth_of_replacement():
    """Floors on replacement pressure, by club x unit.

    For every club/unit we publish:
      - on_report:   rows on the report
      - out:         rows designated Out  (a *floor* on starters the club must replace)
      - questionable: rows designated Questionable
      - affected_units: how many distinct units hold at least one Out
    `replacement_named` is empty on every row: the official injury report names no
    replacement, and this pack refuses to infer one. Named replacements come only from
    `announced_starters()`, which cites the official page that publishes the name.
    """
    out = []
    for club in clubs_on_report():
        rs = [r for r in rows() if r["club"] == club]
        for unit in sorted({r["unit"] for r in rs}):
            ur = [r for r in rs if r["unit"] == unit]
            outs = [r for r in ur if r["game_status"] == "Out"]
            out.append(
                {
                    "club": club,
                    "unit": unit,
                    "side": ur[0]["side"],
                    "on_report": len(ur),
                    "out_floor": len(outs),
                    "questionable": sum(1 for r in ur if r["game_status"] == "Questionable"),
                    "doubtful": sum(1 for r in ur if r["game_status"] == "Doubtful"),
                    "replacement_named": "",
                    "replacement_source_url": "",
                    "note": "floor: count of Out rows in this club/unit; the report names no replacement",
                    "source_url": C.SOURCE_URL["S1"],
                }
            )
    return out


def announced_starters():
    """Officially announced starter changes, transcribed from the cited official page only.

    This is the one place a named replacement may appear. Every row carries the URL of the
    page that publishes the name and the date the story carries. Nothing here is derived
    from a depth chart, a jersey number, experience or salary.

    A headline can announce more than one starter, so each is emitted as its own row and
    the headline text is repeated verbatim on every row it produces.
    """
    out = []
    for date, headline, url in C.OFFICIAL_NEWS_SURFACED:
        low = headline.lower()
        found = []
        if "drew lock" in low and ("will start" in low or "expected to start" in low):
            found.append(("SEA", "Drew Lock", "QB"))
        if "deshaun watson" in low and "to start" in low:
            found.append(("CLE", "Deshaun Watson", "QB"))
        if "carson beck" in low and "to start" in low:
            found.append(("AZ", "Carson Beck", "QB"))
        if "mccord" in low and "first start" in low:
            found.append(("MIA", "Kyle McCord", "QB"))
        for club, player, pos in found:
            out.append(
                {
                    "club": club,
                    "player": player,
                    "position": pos,
                    "evidence_kind": "announced_starter",
                    "announced_for": "Week 10" if date >= "2026-11-09" else "",
                    "date_in_official_story": date,
                    "headline": headline,
                    "source_url": url,
                    "read_at_utc": C.CAPTURE_CLOCK_UTC,
                }
            )
    return out


def roster_events():
    """Dated official roster events that can invalidate an availability row.

    Kept separate from `announced_starters()` because a trade is not a starter
    announcement: the club moved, and whether the player starts is not stated on the
    transactions page.
    """
    out = []
    for date, from_club, to_club, player, txn in C.TRADES_NOV_2026:
        out.append(
            {
                "date": f"2026-{date.replace('/', '-')}",
                "club_from": C.CLUB_ABBR_ALIASES.get(from_club, from_club),
                "club_to": C.CLUB_ABBR_ALIASES.get(to_club, to_club),
                "player": player,
                "event": txn,
                "starter_announced": "",
                "note": "a trade is not a starter announcement; no start is claimed here",
                "source_url": C.SOURCE_URL["S6"],
                "read_at_utc": C.CAPTURE_CLOCK_UTC,
            }
        )
    return out


def reserve_coverage():
    """Cross-walk: players who are on a reserve list, so 'absent from the injury report'
    can never be read as 'available'.

    `on_week10_injury_report` is computed from this session's capture, not assumed.
    """
    report_players = {(r["player"], r["club"]) for r in rows()}
    out = []
    for date, club, player, txn in C.RESERVE_LIST_NOV_2026:
        club_norm = C.CLUB_ABBR_ALIASES.get(club, club)
        on_report = "yes" if (player, club_norm) in report_players else "no"
        out.append(
            {
                "date": f"2026-{date.replace('/', '-')}",
                "club": club_norm,
                "player": player,
                "transaction": txn,
                "on_week10_injury_report": on_report,
                "interpretation": "absent from report because on a reserve list"
                if on_report == "no" else "also carried on the Week 10 report",
                "source_url": C.SOURCE_URL["S7"],
                "read_at_utc": C.CAPTURE_CLOCK_UTC,
            }
        )
    return out


def week9_inactive_rows():
    """One row per (game, club, inactive player), from the official Week 9 inactives page."""
    out = []
    for slug, away, home, kickoff, venue, a_in, h_in in C.WEEK9_INACTIVES:
        for club, lst in ((away, a_in), (home, h_in)):
            for entry in lst:
                entry_clean = entry.replace(" (emergency third QB)", "")
                is_em3 = "(emergency third QB)" in entry
                parts = entry_clean.split(" ", 1)
                pos = parts[0] if len(parts) > 1 else ""
                name = parts[1] if len(parts) > 1 else entry_clean
                out.append(
                    {
                        "game_slug": slug,
                        "club": club,
                        "player": name.strip(),
                        "position": pos.strip(),
                        "emergency_third_qb": "yes" if is_em3 else "no",
                        "venue": venue,
                        "kickoff_et": kickoff,
                        "source_url": C.SOURCE_URL["S5"],
                        "read_at_utc": C.CAPTURE_CLOCK_UTC,
                    }
                )
    return out


def venues():
    """Venue per fixture, transcribed from the official page that prints it."""
    return [
        {
            "week": 9,
            "season": C.SEASON,
            "game_slug": slug,
            "away": away,
            "home": home,
            "kickoff_et": kickoff,
            "venue": venue,
            "source_url": C.SOURCE_URL["S5"],
            "read_at_utc": C.CAPTURE_CLOCK_UTC,
        }
        for slug, away, home, kickoff, venue, _a, _h in C.WEEK9_INACTIVES
    ]
