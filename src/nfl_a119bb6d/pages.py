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

from .htmltext import html_to_lines

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

    The report is a table per club per game. Each row is one player with the
    league's *Practice Status* and *Game Status* designations. The header the
    league prints above the tables gives the game date and kickoff.
    """
    lines = html_to_lines(html)
    rows: list[dict] = []
    problems: list[str] = []

    header_line = ""
    week_line = ""
    game_date = ""
    club = ""
    current_game_url = ""
    in_table = False
    header_cells: list[str] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Injuries - ") or line.startswith("Injuries -"):
            week_line = line
            continue
        if line.upper() in NICKNAME_TO_ABBR and len(line) <= 14:
            club = NICKNAME_TO_ABBR[line.upper()]
            in_table = False
            continue
        mplayers = PLAYER_LINK_RE.findall(line)
        if mplayers and club:
            # A table row: the player's name is a link to the player's page.
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c]
            if len(cells) < 4:
                problems.append(f"short injury row: {line[:80]}")
                continue
            player = mplayers[0]
            rest = [c for c in cells if PLAYER_LINK_RE.sub("", c).strip() != player]
            position = rest[0] if rest else ""
            injury = rest[1] if len(rest) > 1 else ""
            practice = ""
            game_status = ""
            for cell in rest[2:]:
                cell = PLAYER_LINK_RE.sub("", cell).strip()
                if cell in PRACTICE_STATUSES and not practice:
                    practice = cell
                elif cell in GAME_STATUSES and not game_status:
                    game_status = cell
            rows.append(
                {
                    "club": club,
                    "player": player,
                    "position": position,
                    "injury": injury,
                    "practice_status": practice,
                    "game_status": game_status,
                    "game_url": current_game_url,
                    "source_url": url,
                    "read_at_utc": read_at_utc,
                }
            )
            continue
        if "Player" in line and "Position" in line and "Practice" in line:
            header_cells = [c.strip() for c in line.split("|") if c.strip()]
            in_table = True
            continue
        if line.startswith("|") and header_cells:
            continue
        if not header_cells and not PLAYER_LINK_RE.search(line):
            if re.match(r"^[A-Z]+DAY, [A-Z]+ \d{1,2}(ST|TH)?$", line):
                header_line = line
            mg = GAME_URL_RE.search(line)
            if mg:
                current_game_url = f"https://www.nfl.com/games/{mg.group(1)}"
            continue
        mg = GAME_URL_RE.search(line)
        if mg:
            current_game_url = f"https://www.nfl.com/games/{mg.group(1)}"
    if not rows:
        problems.append("no injury rows parsed")
    return {
        "rows": rows,
        "week_line": week_line,
        "problems": problems,
    }
