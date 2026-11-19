"""Parsers for the two league availability pages.

Two official pages carry the availability evidence that the model needs:

* the injury-report hub, ``https://www.nfl.com/injuries/`` and its
  week-specific route ``/injuries/league/<season>/reg<week>``, which prints
  every listed player with the league's *Practice Status* and *Game Status*
  designations;
* the weekly game-day inactive-list article, for example
  ``/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season``, which
  prints each club's game-day inactive list together with the game centre URL
  and the venue of each game.

Both parsers return rows that carry the URL they were read from and the read
time, and both leave anything they cannot read out of the result instead of
filling it in.
"""

from __future__ import annotations

import re

from .htmltext import html_to_lines, split_table_row

#: The league's club nicknames, used to recognise a club heading and to map a
#: heading to the abbreviation the rest of the repository uses. The
#: abbreviation-to-nickname direction is the one the league itself prints in
#: the inactive-list article.
CLUB_NICKNAME = {
    "AZ": "CARDINALS", "ATL": "FALCONS", "BAL": "RAVENS", "BUF": "BILLS",
    "CAR": "PANTHERS", "CHI": "BEARS", "CIN": "BENGALS", "CLE": "BROWNS",
    "DAL": "COWBOYS", "DEN": "BRONCOS", "DET": "LIONS", "GB": "PACKERS",
    "HOU": "TEXANS", "IND": "COLTS", "JAX": "JAGUARS", "KC": "CHIEFS",
    "LV": "RAIDERS", "LAC": "CHARGERS", "LA": "RAMS", "MIA": "DOLPHINS",
    "MIN": "VIKINGS", "NE": "PATRIOTS", "NO": "SAINTS", "NYG": "GIANTS",
    "NYJ": "JETS", "PHI": "EAGLES", "PIT": "STEELERS", "SF": "49ERS",
    "SEA": "SEAHAWKS", "TB": "BUCCANEERS", "TEN": "TITANS", "WAS": "COMMANDERS",
}

#: The league also prints the Arizona Cardinals as "ARI" on some pages.
NICKNAME_TO_ABBR = {nick: abbr for abbr, nick in CLUB_NICKNAME.items()}
NICKNAME_TO_ABBR["CARDINALS"] = "AZ"

GAME_URL_RE = re.compile(
    r"https://www\.nfl\.com/games/([a-z0-9\-]+-\d{4}-reg-\d+)"
)
PLAYER_LINK_RE = re.compile(r"\[([^\]]+)\]\(https://www\.nfl\.com/players/[^)]+\)")
PRACTICE_STATUSES = (
    "Did Not Participate In Practice",
    "Limited Participation in Practice",
    "Full Participation in Practice",
)
GAME_STATUSES = ("Out", "Doubtful", "Questionable")


def parse_inactives_article(html: str, *, url: str, read_at_utc: str) -> dict:
    """Parse the league's weekly game-day inactive-list article.

    Returns ``{"games": [...], "rows": [...], "problems": [...]}``. Each game
    carries its official game centre URL, its venue line and the clubs; each
    row is one inactive player with the club that published it.
    """
    lines = html_to_lines(html)
    games: list[dict] = []
    rows: list[dict] = []
    problems: list[str] = []

    current_game: dict | None = None
    current_club: str | None = None
    in_club_block = False

    for line in lines:
        mg = GAME_URL_RE.search(line)
        if mg:
            slug = mg.group(1)
            current_game = {
                "slug": slug,
                "game_url": f"https://www.nfl.com/games/{slug}",
                "venue_line": "",
                "read_at_utc": read_at_utc,
                "source_url": url,
            }
            games.append(current_game)
            in_club_block = False
            current_club = None
            continue
        if current_game is not None and not in_club_block:
            if line.startswith("WHERE:") or " WHERE:" in line:
                current_game["venue_line"] = line.split("WHERE:", 1)[-1].strip()
                continue
        stripped = line.strip()
        if stripped.startswith("#"):
            stripped = stripped.lstrip("#").strip()
        if stripped.upper() in NICKNAME_TO_ABBR and len(stripped) <= 14:
            current_club = NICKNAME_TO_ABBR[stripped.upper()]
            in_club_block = True
            continue
        if in_club_block and current_club and current_game is not None:
            m = re.match(r"^-?\s*([A-Z]{1,3}|\d[A-Z]{1,2})\s+(.+)$", stripped)
            if m:
                rows.append(
                    {
                        "club": current_club,
                        "position": m.group(1),
                        "player": m.group(2).strip(),
                        "game_slug": current_game["slug"],
                        "game_url": current_game["game_url"],
                        "source_url": url,
                        "read_at_utc": read_at_utc,
                    }
                )
                continue
            if stripped and not stripped.startswith("-"):
                in_club_block = False
                current_club = None
    if not games:
        problems.append("no game centre URL found in the article")
    if not rows:
        problems.append("no inactive rows parsed from the article")
    return {"games": games, "rows": rows, "problems": problems}


def parse_injury_report(html: str, *, url: str, read_at_utc: str) -> dict:
    """Parse the league's injury report.

    The report is one table per club per game, and the columns are the ones
    the league prints: ``Player``, ``Position``, ``Injuries``, ``Practice
    Status`` and ``Game Status``. The injury column is empty for most players
    and the game-status column is empty for a player the league expects to
    play, so the columns are read by position rather than by searching for a
    status string: a shifted column would otherwise be read as the wrong
    designation, which is exactly the kind of quiet error this pack must not
    publish.

    The club heading above each table is the club's nickname, and the game
    centre URL of the game is printed next to the two clubs' logos.
    """
    lines = html_to_lines(html)
    rows: list[dict] = []
    problems: list[str] = []

    week_line = ""
    club = ""
    current_game_url = ""
    columns: list[str] = []
    expected = ("player", "position", "injuries", "practice status", "game status")

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.upper().startswith("INJURIES - WEEK"):
            week_line = line
            continue
        mg = GAME_URL_RE.search(line)
        if mg:
            current_game_url = f"https://www.nfl.com/games/{mg.group(1)}"
        if line.startswith("|"):
            cells = split_table_row(line)
            if not cells:
                continue
            header = [c.strip().lower() for c in cells]
            if header[:2] == ["player", "position"]:
                columns = header
                continue
            if header and all(set(c) <= {"-"} and c for c in header):
                # The markdown separator row the league prints under a header.
                continue
            if not columns:
                problems.append(f"injury row before any header: {line[:80]}")
                continue
            if not PLAYER_LINK_RE.search(cells[0]):
                # A row without a player link is not a player row.
                continue
            if len(cells) != len(expected):
                problems.append(
                    f"injury row with {len(cells)} columns, expected "
                    f"{len(expected)}: {line[:80]}"
                )
                continue
            m = PLAYER_LINK_RE.search(cells[0])
            player = m.group(1).strip() if m else cells[0].strip()
            practice = cells[3].strip()
            game_status = cells[4].strip()
            if practice and practice not in PRACTICE_STATUSES:
                problems.append(f"unknown practice status: {practice!r}")
            if game_status and game_status not in GAME_STATUSES:
                problems.append(f"unknown game status: {game_status!r}")
            rows.append(
                {
                    "club": club,
                    "player": player,
                    "position": cells[1].strip(),
                    "injury": cells[2].strip(),
                    "practice_status": practice,
                    "game_status": game_status,
                    "game_url": current_game_url,
                    "source_url": url,
                    "read_at_utc": read_at_utc,
                }
            )
            continue
        # A heading that names the club. The league prints the nickname alone.
        stripped = line.strip()
        if stripped.upper() in NICKNAME_TO_ABBR and len(stripped) <= 14:
            club = NICKNAME_TO_ABBR[stripped.upper()]
            columns = []
            continue
        if "Player" in stripped and "Position" in stripped:
            # The header of a table that was not printed as a pipe row.
            columns = [
                c.strip().lower()
                for c in re.split(r"\s{2,}|\|", stripped)
                if c.strip()
            ]
            if columns[:2] != ["player", "position"]:
                columns = []
    if not rows:
        problems.append("no injury rows parsed")
    return {
        "rows": rows,
        "week_line": week_line,
        "problems": problems,
    }
