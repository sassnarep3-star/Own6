"""Derived registers for session a119bb6d.

Everything here is a pure function of the committed official reads in
``data/nfl_a119bb6d/parsed/``. No value is invented, no gap is filled: where
the league did not print a number the cell stays empty and the row carries the
reason it is empty.

Three registers are built:

``availability_graph``
    Who was expected to start and who actually did, per club, per position
    slot, for two consecutive weeks. The *expected* starter is the same club's
    official starter at that slot in the previous game, read from the previous
    week's official Game Book. The league publishes no depth chart and no snap
    counts, so the depth of a replacement is reported as a **lower bound**:
    one more than the number of the previous week's starters at that position
    who did not start again, which counts only the players the league itself
    shows were unavailable.

``designation_calibration``
    What the league's injury-report designations actually mean, measured
    against the official Game Book of the same week. For every designated
    player the Game Book says whether the player started, came off the bench,
    was inactive or did not play. Each designation gets its count, its play
    rate and a Wilson 95% interval.

``snapshot_ledger``
    The point-in-time ledger of every official read: what was read, from
    which URL, at what clock time and with what SHA-256.
"""

from __future__ import annotations

import csv
import math
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(REPO, "data", "nfl_a119bb6d")
PARSED = os.path.join(DATA, "parsed")

#: The club abbreviations the game books use in their club names.
CLUB_NAMES = {
    "Arizona Cardinals": "AZ", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX", "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LA", "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN", "New England Patriots": "NE",
    "New Orleans Saints": "NO", "New York Giants": "NYG", "New York Jets": "NYJ",
    "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA",
    "Tampa Bay Buccaneers": "TB", "Tennessee Titans": "TEN",
    "Washington Commanders": "WAS",
}


def load(name: str, folder: str = PARSED) -> list[dict]:
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def week_of_game(game_slug: str) -> int:
    m = re.search(r"-reg-(\d+)$", game_slug)
    return int(m.group(1)) if m else 0


def club_of(team_name: str) -> str:
    return CLUB_NAMES.get(team_name.strip(), "")


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = (
        z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    )
    return (max(0.0, centre - margin), min(1.0, centre + margin))


# ---------------------------------------------------------------------------
# 1. The availability graph
# ---------------------------------------------------------------------------

def build_availability_graph(
    games: list[dict],
    lineups: list[dict],
    participation: list[dict],
) -> tuple[list[dict], list[str]]:
    """Return the availability graph rows and the problems found.

    The graph is built per club, per unit and per **position group**, not per
    numbered slot. The league's Game Book prints the position (``WR``, ``TE``,
    ``DL`` ...) but it does not print a depth rank, so pairing "last week's
    first wide receiver" with "this week's first wide receiver" would invent a
    rank the league never published. Comparing the *sets* of starters at each
    position group answers the owner's question exactly -- who was expected to
    start and who actually did -- without inventing anything.

    The depth of the replacement is a lower bound: one more than the number of
    the club's previous starters at that position who the Game Book shows were
    inactive or did not play. A player who merely lost the job is not counted.
    """
    problems: list[str] = []

    # Starters per game, club and position group.
    starters: dict[tuple, list[str]] = {}
    for row in lineups:
        key = (row["game_slug"], row["side"], row["unit"], row["position"])
        starters.setdefault(key, []).append(row["player"])

    # Game-day status per game and club.
    status: dict[tuple, dict[str, str]] = {}
    for row in participation:
        key = (row["game_slug"], row["side"])
        status.setdefault(key, {})[row["player"]] = row["role"]

    # The games each club played, in week order, so that "expected" means
    # "the club's official starter in its previous game".
    club_games: dict[str, list[tuple[int, str, str]]] = {}
    for game in games:
        week = week_of_game(game["game_slug"])
        for side, name in (("away", game["away_team"]), ("home", game["home_team"])):
            club = club_of(name)
            if club:
                club_games.setdefault(club, []).append((week, game["game_slug"], side))
    for club in club_games:
        club_games[club].sort()

    rows: list[dict] = []
    for game in games:
        week = week_of_game(game["game_slug"])
        game_slug = game["game_slug"]
        for side in ("away", "home"):
            club = club_of(game[f"{side}_team"])
            if not club:
                problems.append(
                    f"{game_slug}: club name not recognised ({game[f'{side}_team']})"
                )
                continue
            history = club_games.get(club, [])
            previous = None
            for gweek, gslug, gside in history:
                if gweek < week and (previous is None or gweek >= previous[0]):
                    previous = (gweek, gslug, gside)
            for unit in ("offense", "defense"):
                positions = sorted(
                    {
                        pos
                        for (gslug, gside, uunit, pos) in starters
                        if gslug == game_slug and gside == side and uunit == unit
                    }
                )
                for position in positions:
                    actual = sorted(starters.get((game_slug, side, unit, position), []))
                    if not actual:
                        continue
                    expected: list[str] = []
                    if previous:
                        expected = sorted(
                            starters.get((previous[1], previous[2], unit, position), [])
                        )
                    starters_out = [p for p in expected if p not in actual]
                    starters_in = [p for p in actual if p not in expected]
                    game_status = status.get((game_slug, side), {})
                    unavailable = [
                        p
                        for p in starters_out
                        if game_status.get(p) in ("not_active", "did_not_play")
                    ]
                    pushed_back = [p for p in starters_out if p not in unavailable]
                    if not expected:
                        change = "no_prior_game_book"
                    elif not starters_in:
                        change = "held_over"
                    else:
                        change = "replaced"
                    rows.append(
                        {
                            "week": week,
                            "game_slug": game_slug,
                            "game_url": game["game_url"],
                            "club": club,
                            "opponent": club_of(
                                game["home_team"] if side == "away" else game["away_team"]
                            ),
                            "side": side,
                            "unit": unit,
                            "position": position,
                            "expected_starters": "; ".join(expected),
                            "actual_starters": "; ".join(actual),
                            "starters_out": "; ".join(starters_out),
                            "starters_in": "; ".join(starters_in),
                            "unavailable_ahead": len(unavailable),
                            "pushed_back": "; ".join(pushed_back),
                            "replacement_string_lower_bound": (
                                len(unavailable) + 1 if unavailable else ""
                            ),
                            "change_type": change,
                            "previous_game_slug": previous[1] if previous else "",
                            "expected_source": (
                                game.get("gamebook_url", "") if previous else ""
                            ),
                            "actual_source": game["gamebook_url"],
                            "source_url": game["game_url"],
                            "read_at_utc": game.get("read_at_utc", ""),
                            "note": (
                                "the league publishes no depth rank and no snap counts, so "
                                "the comparison is between the sets of starters at the "
                                "position and the depth of the replacement is a lower "
                                "bound counted only from the official Game Book"
                            ),
                        }
                    )
    return rows, problems


# ---------------------------------------------------------------------------
# 2. The designation calibration
# ---------------------------------------------------------------------------

def build_matchup_matrix(
    games: list[dict],
    lineups: list[dict],
    participation: list[dict],
) -> tuple[list[dict], list[str]]:
    """Return the offence-versus-defence personnel matrix and its problems.

    For every game, every position group on the attack is set against the
    starting defenders at the corresponding group, and the personnel
    deficiency of each side is read from the Game Book: a starter who was
    <em>Not Active</em> or <em>Did Not Play</em> leaves the position group
    without its first-choice player, and the replacement who started there
    takes the place.

    The string column is a lower bound for the reason given in
    :func:`build_availability_graph`: the league publishes no depth order and
    no snap counts.
    """
    problems: list[str] = []

    starters: dict[tuple, list[str]] = {}
    for row in lineups:
        key = (row["game_slug"], row["side"], row["unit"], row["position"])
        starters.setdefault(key, []).append(row["player"])

    status: dict[tuple, dict[str, str]] = {}
    for row in participation:
        key = (row["game_slug"], row["side"])
        status.setdefault(key, {})[row["player"]] = row["role"]

    rows: list[dict] = []
    for game in games:
        slug = game["game_slug"]
        week = week_of_game(slug)
        for attack, defence in (("away", "home"), ("home", "away")):
            attack_club = club_of(game[f"{attack}_team"])
            defence_club = club_of(game[f"{defence}_team"])
            if not attack_club or not defence_club:
                problems.append(
                    f"{slug}: club name not recognised in the match-up matrix"
                )
                continue
            positions = sorted(
                {
                    pos
                    for (gslug, gside, unit, pos) in starters
                    if gslug == slug and gside == attack and unit == "offense"
                }
            )
            for position in positions:
                offense = sorted(starters.get((slug, attack, "offense", position), []))
                defense = sorted(starters.get((slug, defence, "defense", position), []))
                if not offense or not defense:
                    continue
                game_status = status.get((slug, attack), {})
                unavailable = [
                    p for p in offense
                    if game_status.get(p) in ("not_active", "did_not_play")
                ]
                replacement = [p for p in offense if p not in unavailable]
                rows.append(
                    {
                        "week": week,
                        "game_slug": slug,
                        "game_url": game["game_url"],
                        "offense_club": attack_club,
                        "defense_club": defence_club,
                        "position": position,
                        "offense_starters": "; ".join(offense),
                        "defense_starters": "; ".join(defense),
                        "offense_unavailable": "; ".join(unavailable),
                        "offense_replacement_started": "; ".join(replacement),
                        "offense_deficiency_count": len(unavailable),
                        "offense_replacement_string_lower_bound": (
                            len(unavailable) + 1 if unavailable else ""
                        ),
                        "source_url": game["game_url"],
                        "gamebook_url": game.get("gamebook_url", ""),
                        "read_at_utc": game.get("read_at_utc", ""),
                        "note": (
                            "the deficiency count is the number of the attack's official "
                            "starters at this position whom the official Game Book shows "
                            "were inactive or did not play; the string is a lower bound "
                            "because the league publishes no depth order and no snap counts"
                        ),
                    }
                )
    return rows, problems


def build_designation_calibration(
    injuries: list[dict],
    games: list[dict],
    lineups: list[dict],
    participation: list[dict],
) -> tuple[list[dict], list[str]]:
    """Return the calibration rows and the problems found."""
    problems: list[str] = []
    starter_names: dict[tuple, set[str]] = {}
    for row in lineups:
        key = (row["game_slug"], row["side"])
        starter_names.setdefault(key, set()).add(row["player"])

    participation_by_game: dict[tuple, dict[str, str]] = {}
    for row in participation:
        key = (row["game_slug"], row["side"])
        participation_by_game.setdefault(key, {})[row["player"]] = row["role"]

    # Which game each club played in each week, so a designation for a week can
    # be joined to that club's game in the same week.
    club_game: dict[tuple[int, str], tuple[str, str]] = {}
    for game in games:
        week = week_of_game(game["game_slug"])
        for side in ("away", "home"):
            club = club_of(game[f"{side}_team"])
            if club:
                club_game[(week, club)] = (game["game_slug"], side)

    counts: dict[str, dict[str, int]] = {}
    for row in injuries:
        week = row.get("week", "")
        if not week:
            continue
        try:
            week_int = int(week)
        except ValueError:
            continue
        designation = (row.get("game_status") or "").strip() or "(none printed)"
        club = row["club"]
        target = club_game.get((week_int, club))
        if target is None:
            problems.append(
                f"{club} week {week_int}: no official game book to join the designation to"
            )
            continue
        game_slug, side = target
        player = row["player"]
        starters = starter_names.get((game_slug, side), set())
        roles = participation_by_game.get((game_slug, side), {})
        if player in starters:
            outcome = "started"
        elif roles.get(player) == "substitute":
            outcome = "played_off_bench"
        elif roles.get(player) == "did_not_play":
            outcome = "did_not_play"
        elif roles.get(player) == "not_active":
            outcome = "inactive"
        else:
            outcome = "not_in_game_book"
        bucket = counts.setdefault(
            designation, {"n": 0, "started": 0, "played_off_bench": 0,
                          "did_not_play": 0, "inactive": 0, "not_in_game_book": 0}
        )
        bucket["n"] += 1
        bucket[outcome] = bucket.get(outcome, 0) + 1

    rows: list[dict] = []
    for designation in sorted(counts):
        bucket = counts[designation]
        n = bucket["n"]
        played = bucket["started"] + bucket["played_off_bench"]
        rate = played / n if n else 0.0
        low, high = wilson_interval(played, n)
        rows.append(
            {
                "designation": designation,
                "n": n,
                "n_started": bucket["started"],
                "n_played_off_bench": bucket["played_off_bench"],
                "n_did_not_play": bucket["did_not_play"],
                "n_inactive": bucket["inactive"],
                "n_not_in_game_book": bucket["not_in_game_book"],
                "play_rate": f"{rate:.4f}",
                "play_rate_ci95_low": f"{low:.4f}",
                "play_rate_ci95_high": f"{high:.4f}",
                "interpretation": (
                    "the share of designated players the official Game Book shows "
                    "actually played, with a Wilson 95% interval; n is the number "
                    "of designated players with an official game book in the same "
                    "week"
                ),
                "source_url": "https://www.nfl.com/injuries/",
                "read_at_utc": "",
            }
        )
    return rows, problems
