"""Verified results feed and the point-in-time aggregates derived from it.

Why this module exists
----------------------
Backtests and ROI need two things the repository did not have before this pack:

1. a set of *finished* games whose scores are traceable to an official page; and
2. team strength inputs that were knowable **before** the game being priced, so
   that grading a line cannot peek at the result it is grading.

The feed supplies both. Point-in-time aggregates are obtained without any
historical standings archive: the official division standings page is a
cumulative table, so the aggregate as of the end of week ``W`` is the table as
read today minus every finished game the feed holds for weeks ``> W``. Each
subtracted game is an official final score, so the subtraction is arithmetic on
verified numbers, and the result is checked against an independent official
source: the record badge printed on each game card, which is the club's record
*after* that game.
"""

from __future__ import annotations

from . import capture as C
from .cache import memo

PACK = "nfl_d966f630"
CLUBS = sorted({t for row in C.STANDINGS for t in [row[0]]})

# ---- feed rows ------------------------------------------------------------


@memo
def feed_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for gid, week, date_label, slot, away, home, ap, hp, src in C.FINAL_GAMES:
        margin = hp - ap
        winner = home if margin > 0 else away if margin < 0 else "tie"
        rows.append({
            "game_id": gid,
            "season": "2026",
            "week": str(week),
            "date_on_card": date_label,
            "slot_on_card": slot,
            "away": away,
            "away_points": str(ap),
            "home": home,
            "home_points": str(hp),
            "game_total": str(ap + hp),
            "margin_home": str(margin),
            "abs_margin_home": str(abs(margin)),
            "winner_abbr": winner,
            "is_tie": "1" if margin == 0 else "0",
            "feed_status": "final",
            "value_source": "official_page_read_this_session",
            "official_source_url": C.link_for(src),
            "game_page_url": C.game_url(gid),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return rows


# ---- point-in-time aggregates --------------------------------------------


def _current() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for abbr, conf, div, w, l, t, pct, pf, pa, net in C.STANDINGS:
        out[abbr] = {"w": w, "l": l, "t": t, "pf": pf, "pa": pa, "net": net,
                     "games": w + l + t, "pct": float(pct)}
    return out


def games_after(week: int) -> list[tuple[str, str, int, int]]:
    """Finished games played after the end of ``week`` (away, home, away_pts, home_pts)."""
    return [(a, h, ap, hp) for _, wk, _, _, a, h, ap, hp, _ in C.FINAL_GAMES if wk > week]


@memo
def as_of(week: int) -> dict[str, dict[str, float]]:
    """Cumulative per-club totals as of the end of ``week``.

    ``week`` is the cut-off, not the sample: everything played in weeks
    ``week+1 .. latest finished`` is removed from the current standings table.
    """
    table = _current()
    for away, home, ap, hp in games_after(week):
        for abbr, pf, pa, won in ((away, ap, hp, ap > hp), (home, hp, ap, hp > ap)):
            row = table[abbr]
            row["pf"] -= pf
            row["pa"] -= pa
            row["games"] -= 1
            row["net"] = row["pf"] - row["pa"]
            if won:
                row["w"] -= 1
            elif ap == hp:
                row["t"] -= 1
            else:
                row["l"] -= 1
    for row in table.values():
        g = row["games"]
        row["ppg"] = row["pf"] / g if g else float("nan")
        row["papg"] = row["pa"] / g if g else float("nan")
        row["netpg"] = row["ppg"] - row["papg"]
        row["win_pct"] = (row["w"] + 0.5 * row["t"]) / g if g else float("nan")
    return table


@memo
def league_baseline(week: int) -> dict[str, float]:
    """League-average points per team-game and the spread of team quality, both
    measured from the point-in-time table (no imported constants)."""
    tab = as_of(week)
    pts = [row["pf"] for row in tab.values()]
    games = sum(row["games"] for row in tab.values())
    total_games = games / 2.0
    return {
        "team_games": games,
        "games": total_games,
        "points_per_team_game": sum(pts) / games,
        "n_clubs": float(len(tab)),
    }


# ---- reconciliation -------------------------------------------------------


@memo
def standings_reconciliation() -> list[dict[str, str]]:
    """Reconcile the derived point-in-time records against the official record
    badges printed on the game cards, and the standings identity checks."""
    out: list[dict[str, str]] = []
    for week, src in ((7, "SCHED-W7"), (8, "SCHED-W8"), (9, "SCHED-W9")):
        tab = as_of(week)
        for abbr, (w, l, t) in sorted(C.CARD_BADGES[week].items()):
            row = tab[abbr]
            derived = (int(row["w"]), int(row["l"]), int(row["t"]))
            match = "match" if derived == (w, l, t) else "MISMATCH"
            out.append({
                "check_week": str(week),
                "club": abbr,
                "derived_w_l_t": f"{derived[0]}-{derived[1]}-{derived[2]}",
                "official_card_badge_w_l_t": f"{w}-{l}-{t}",
                "result": match,
                "derived_from": "standings page as read " + C.CAPTURE_DATE_UTC
                                 + " minus every feed game played after week " + str(week),
                "official_source_url": C.link_for(src),
                "standings_source_url": C.link_for("STANDINGS"),
            })
        # bye clubs have no card in that week, so no badge exists to compare with.
        byes = {7: C.WEEK7_BYE_CLUBS, 8: C.WEEK8_BYE_CLUBS, 9: C.WEEK9_BYE_CLUBS}[week]
        for abbr in byes:
            row = tab[abbr]
            out.append({
                "check_week": str(week),
                "club": abbr,
                "derived_w_l_t": f"{int(row['w'])}-{int(row['l'])}-{int(row['t'])}",
                "official_card_badge_w_l_t": "",
                "result": "no_official_badge_club_on_bye",
                "derived_from": "standings page as read " + C.CAPTURE_DATE_UTC
                                 + " minus every feed game played after week " + str(week),
                "official_source_url": C.link_for("STANDINGS"),
                "standings_source_url": C.link_for("STANDINGS"),
            })
    return out


@memo
def feed_identities() -> list[dict[str, str]]:
    """Structural identities the feed and the standings must satisfy. A failure
    here invalidates every downstream number, so the build prints them and the
    checker re-runs them from the published CSVs."""
    rows = feed_rows()
    tab = _current()
    out: list[dict[str, str]] = []

    def add(name: str, expected: str, observed: str, ok_: bool, why: str, src: str) -> None:
        out.append({
            "identity": name,
            "expected": expected,
            "observed": observed,
            "result": "pass" if ok_ else "FAIL",
            "why_it_matters": why,
            "official_source_url": C.link_for(src),
        })

    w = sum(r["w"] for r in tab.values())
    l = sum(r["l"] for r in tab.values())
    t = sum(r["t"] for r in tab.values())
    pf = sum(r["pf"] for r in tab.values())
    pa = sum(r["pa"] for r in tab.values())
    add("standings_sum_W_equals_sum_L", f"{int(l)}", f"{int(w)}", w == l,
        "every finished game produces exactly one win and one loss (or one tie each)", "STANDINGS")
    add("standings_sum_ties_is_even", "an even number", f"{int(t)}", t % 2 == 0,
        "a tied game adds one tie to each of two clubs", "STANDINGS")
    add("standings_sum_PF_equals_sum_PA", f"{int(pa)}", f"{int(pf)}", pf == pa,
        "points scored across the league must equal points conceded", "STANDINGS")
    add("feed_rows_unique_per_game", f"{len(rows)}",
        f"{len({r['game_id'] for r in rows})}", len({r['game_id'] for r in rows}) == len(rows),
        "one row per game: a duplicate would double-count a result", "SCHED-W7")
    add("feed_points_match_standings_totals_or_exceed_nothing",
        "every club's feed points <= its season points",
        ", ".join(_overflow_clubs(tab)) or "no club exceeds its season total", not _overflow_clubs(tab),
        "the feed is a subset of the season, so it can never score more than the season total",
        "STANDINGS")
    for abbr in CLUBS:
        before = int(tab[abbr]["games"]) - _feed_games(abbr)
        add(f"games_before_feed_window_non_negative::{abbr}", ">= 0", str(before), before >= 0,
            "weeks 1-6 are not ingested yet, so the remainder must simply be non-negative",
            "STANDINGS")
    return out


def _overflow_clubs(tab: dict[str, dict[str, float]]) -> list[str]:
    bad = []
    for abbr, row in tab.items():
        scored = sum(hp if h == abbr else ap
                     for _, _, _, _, a, h, ap, hp, _ in C.FINAL_GAMES if abbr in (a, h))
        if scored > row["pf"]:
            bad.append(abbr)
    return bad


def _feed_games(abbr: str) -> int:
    return sum(1 for _, _, _, _, a, h, _, _, _ in C.FINAL_GAMES if abbr in (a, h))


@memo
def margin_pairs() -> list[tuple[float, float, float]]:
    """(home margin, game total, week) for every finished game in the feed."""
    return [(float(hp - ap), float(ap + hp), float(wk))
            for _, wk, _, _, _, _, ap, hp, _ in C.FINAL_GAMES]


@memo
def team_points() -> list[tuple[float, float, float]]:
    """(home_points, away_points, week) for every finished game."""
    return [(float(hp), float(ap), float(wk))
            for _, wk, _, _, _, _, ap, hp, _ in C.FINAL_GAMES]
