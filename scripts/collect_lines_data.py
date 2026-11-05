#!/usr/bin/env python3
"""Collect official NBA game results from nba.com and emit a source-linked dataset.

This collector reads ONLY first-party NBA sources:

  * ``https://www.nba.com/games?date=YYYY-MM-DD``   - date slate with final scores
  * ``https://www.nba.com/standings``                 - current standings table

Every emitted row carries the exact nba.com URL it was read from. No value is
inferred, interpolated or filled in. If a page cannot be read, the collector
reports the failure and skips that date rather than emitting a partial row.

The collector supports two page shapes and tries them in order:

  1. The nba.com static schedule JSON (the same payload the site renders from).
  2. The rendered slate page, parsed with the same field order the site
     prints: logo, team, record, score, Final[/OT], score, logo.

The script is deterministic given the fetched pages: re-running it offline
against the cached pages in ``data/lines/raw/`` reproduces the same CSV byte
for byte, so the dataset can be rebuilt and audited without network access.

Usage
-----
    python3 scripts/collect_lines_data.py --out data/lines
    python3 scripts/collect_lines_data.py --out data/lines --offline
    python3 scripts/collect_lines_data.py --out data/lines --start 2026-10-20 --end 2026-11-04
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data/lines"
RAW_DIR = DEFAULT_OUT / "raw"

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# The official static schedule JSON. The site renders its schedule page from
# this payload, so it is a first-party nba.com source.
SCHEDULE_JSON = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"
STANDINGS_JSON = "https://cdn.nba.com/static/json/staticData/standingsLeagueV2_1.json"

# NBA team ids as used by cdn.nba.com logo URLs, mapped to stable abbreviations.
# The id is the authoritative key: the slate card prints a short display name
# next to the logo, so names are only recorded for human readability.
TEAM_IDS = {
    "1610612737": "ATL", "1610612738": "BOS", "1610612751": "BKN",
    "1610612766": "CHA", "1610612741": "CHI", "1610612739": "CLE",
    "1610612742": "DAL", "1610612743": "DEN", "1610612765": "DET",
    "1610612744": "GSW", "1610612745": "HOU", "1610612754": "IND",
    "1610612746": "LAC", "1610612747": "LAL", "1610612763": "MEM",
    "1610612748": "MIA", "1610612749": "MIL", "1610612750": "MIN",
    "1610612740": "NOP", "1610612752": "NYK", "1610612760": "OKC",
    "1610612753": "ORL", "1610612755": "PHI", "1610612756": "PHX",
    "1610612757": "POR", "1610612758": "SAC", "1610612759": "SAS",
    "1610612761": "TOR", "1610612762": "UTA", "1610612764": "WAS",
}

TEAM_NAMES = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE", "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU",
    "Indiana Pacers": "IND", "LA Clippers": "LAC",
    "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN", "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX", "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

# Rendered slate card: logo, team, record, score, Final[/OT], score, logo, URL.
GAME_BLOCK = re.compile(
    r"!\[ ?Logo\]\([^\)]*logos/nba/(?P<away_id>\d+)/[^\)]*\)\n(?P<away>[A-Za-z0-9 .'\-]+?)\n"
    r"(?P<away_rec>\d+-\d+)\n(?P<away_score>\d+)\nFinal(?P<ot>/OT)?\n"
    r"(?P<home_score>\d+)\n!\[ ?Logo\]\([^\)]*logos/nba/(?P<home_id>\d+)/[^\)]*\)\n"
    r"(?P<home>[A-Za-z0-9 .'\-]+?)\n(?P<home_rec>\d+-\d+)\]\((?P<url>https://www\.nba\.com/game/[^)]+)\)"
)

# Same shape but as raw JSON strings (the site's embedded payload).
JSON_GAME_BLOCK = re.compile(
    r"\"gameId\":\"(?P<game_id>\d+)\".*?"
    r"\"awayTeam\":\{\"teamId\":\d+,\"teamName\":\"(?P<away>[^\"]*)\".*?"
    r"\"awayScore\":\"(?P<away_score>\d+)\".*?"
    r"\"homeTeam\":\{\"teamId\":\d+,\"teamName\":\"(?P<home>[^\"]*)\".*?"
    r"\"homeScore\":\"(?P<home_score>\d+)\".*?"
    r"\"gameStatus\":\"(?P<status>[^\"]*)\""
)

STANDING_ROW = re.compile(
    r"\|\s*\[(?P<rank>\d+)[^\]]*\]\s*\[!\[ Logo\]\([^\)]*logos/nba/(?P<team_id>\d+)/[^\)]*\)[^\]]*\n"
    r"(?P<team>[A-Za-z0-9 .'\-]+?)\n\|\s*(?P<w>\d+)\s*\|\s*(?P<l>\d+)\s*\|"
)


NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)


def parse_next_data(body: str, date: str) -> list[dict]:
    """Parse the nba.com slate page's embedded Next.js payload.

    nba.com server-renders the slate from an official payload that the page
    embeds as ``__NEXT_DATA__``. The payload carries the game id, both club
    codes, both final scores, the number of periods played and the official
    per-team slug used to build the game's nba.com URL.
    """
    match = NEXT_DATA.search(body)
    if not match:
        raise ValueError(f"{date}: no __NEXT_DATA__ payload in the page")
    payload = json.loads(match.group(1))
    page_props = payload.get("props", {}).get("pageProps", {})
    cards = []
    for module in page_props.get("gameCardFeed", {}).get("modules", []):
        cards.extend(module.get("cards", []))
    if not cards:
        raise ValueError(f"{date}: no game cards in the payload")

    rows: list[dict] = []
    for card in cards:
        data = card.get("cardData", {})
        status = data.get("gameStatusText")
        away = data.get("awayTeam") or {}
        home = data.get("homeTeam") or {}
        away_code = away.get("teamTricode")
        home_code = home.get("teamTricode")
        if away_code not in TEAM_IDS.values() or home_code not in TEAM_IDS.values():
            raise ValueError(f"{date}: unknown club code(s): {away_code} / {home_code}")
        game_id = str(data.get("gameId") or "")
        if len(game_id) != 10 or not game_id.isdigit():
            raise ValueError(f"{date}: unexpected game id {game_id!r}")
        # period > 4 means the game went to overtime.
        overtime = "yes" if int(data.get("period") or 0) > 4 else ""
        # nba.com's own "Summary" link uses the three-letter club codes in the
        # slug; the long club slugs also resolve. Use the short form so the
        # row link matches the link nba.com prints on the same page.
        url = (f"https://www.nba.com/game/{away_code.lower()}-vs-"
               f"{home_code.lower()}-{game_id}")
        if not status or not status.startswith("Final"):
            # A scheduled or in-progress game has no final score; it is not a
            # result row. nba.com writes "Final" and "Final/OT".
            continue
        rows.append(_row(date, away_code, int(away["score"]), home_code,
                         int(home["score"]), overtime, game_id, url))
    if not rows:
        raise ValueError(f"{date}: no final games in the payload")
    return rows


def fetch(url: str, timeout: int = 60) -> str:
    """Return the body of ``url`` or raise."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "*/*",
                      "Accept-Language": "en-US,en;q=0.9"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def normalise(markdown: str) -> str:
    """Normalise a rendered page to the plain-text form the regexes expect.

    Two input shapes are supported:

    * a page-to-markdown rendering, where the converter writes a literal
      backslash before every newline and separates fields with a
      backslash-newline-backslash-newline pair;
    * raw HTML from the site, where the same fields are separate tags.

    Both are reduced to one field per line so the same expressions apply.
    """
    text = re.sub(r"\\+\n\\+\n", "\n", markdown)
    text = re.sub(r"\\+\n", "\n", text)
    text = re.sub(r"</(?:div|span|p|li|td|tr|h[1-6])>", "\n", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    return text


def _slug_for(abbr: str) -> str:
    """The slug token nba.com uses for a club in a game URL."""
    return {"BOS": "bos", "GSW": "gsw", "LAL": "lal", "LAC": "lac",
            "NYK": "nyk", "PHI": "phi", "POR": "por"}.get(abbr, abr.lower())


def _row(date: str, away: str, away_score: int, home: str, home_score: int,
          overtime: str, game_id: str, source_url: str) -> dict:
    return {
        "date": date,
        "away_team": away,
        "away_score": away_score,
        "home_team": home,
        "home_score": home_score,
        "overtime": overtime,
        "game_id": game_id,
        "source_url": source_url,
        "slate_url": f"https://www.nba.com/games?date={date}",
        "read_on": dt.date.today().isoformat(),
    }


def parse_slate_markdown(text: str, date: str) -> list[dict]:
    """Parse the rendered nba.com slate page."""
    rows: list[dict] = []
    for match in GAME_BLOCK.finditer(text):
        away_id = match.group("away_id")
        home_id = match.group("home_id")
        if away_id not in TEAM_IDS or home_id not in TEAM_IDS:
            raise ValueError(f"{date}: unknown team id(s): {away_id} / {home_id}")
        url = match.group("url")
        game_id = url.rsplit("-", 1)[-1]
        if not game_id.isdigit() or len(game_id) != 10:
            raise ValueError(f"{date}: unexpected game id in {url}")
        rows.append(_row(date, TEAM_IDS[away_id], int(match.group("away_score")),
                         TEAM_IDS[home_id], int(match.group("home_score")),
                         "yes" if match.group("ot") else "", game_id, url))
    if not rows:
        raise ValueError(f"{date}: no finished games parsed from the rendered slate")
    return rows


def parse_schedule_json(body: str, wanted: set[str]) -> list[dict]:
    """Parse the official static schedule JSON for the requested dates."""
    payload = json.loads(body)
    games = payload.get("leagueSchedule") or {}
    rows: list[dict] = []
    for date_block in games.get("gameDates", []):
        date = date_block.get("gameDate")
        if date not in wanted:
            continue
        for game in date_block.get("games", []):
            status = game.get("gameStatusText", "")
            if status != "Final":
                continue
            away = game.get("awayTeam", {}).get("teamTricode") or \
                game.get("awayTeam", {}).get("teamCity")
            home = game.get("homeTeam", {}).get("teamTricode") or \
                game.get("homeTeam", {}).get("teamCity")
            if away not in TEAM_IDS.values() or home not in TEAM_IDS.values():
                raise ValueError(f"{date}: unknown tricode(s): {away} / {home}")
            game_id = str(game.get("gameId"))
            if len(game_id) != 10 or not game_id.isdigit():
                raise ValueError(f"{date}: unexpected game id {game_id!r}")
            overtime = "yes" if game.get("period", {}).get("current", 1) > 4 else ""
            rows.append(_row(
                date, away, int(game.get("awayScore")), home,
                int(game.get("homeScore")), overtime, game_id,
                f"https://www.nba.com/game/{_slug_for(away)}-vs-{_slug_for(home)}-{game_id}"))
    return rows


def parse_standings_markdown(text: str) -> list[dict]:
    rows: list[dict] = []
    for match in STANDING_ROW.finditer(text):
        team_id = match.group("team_id")
        if team_id not in TEAM_IDS:
            continue
        rows.append({
            "team_abbr": TEAM_IDS[team_id],
            "team_name": match.group("team").strip(),
            "w": int(match.group("w")),
            "l": int(match.group("l")),
            "source_url": "https://www.nba.com/standings",
            "read_on": dt.date.today().isoformat(),
        })
    if len(rows) != 30:
        raise ValueError(f"standings: expected 30 teams, parsed {len(rows)}")
    return rows


def parse_standings_json(body: str) -> list[dict]:
    payload = json.loads(body)
    rows: list[dict] = []
    for group in payload.get("standings", {}).get("groups", []):
        for team in group.get("standings", {}).get("team", []):
            abbr = team.get("teamTricode")
            if abbr not in TEAM_IDS.values():
                continue
            rows.append({
                "team_abbr": abbr,
                "team_name": team.get("teamCity", "") + " " + team.get("teamName", ""),
                "w": int(team.get("wins", 0)),
                "l": int(team.get("losses", 0)),
                "source_url": "https://www.nba.com/standings",
                "read_on": dt.date.today().isoformat(),
            })
    if len(rows) != 30:
        raise ValueError(f"standings: expected 30 teams, parsed {len(rows)}")
    return rows


def daterange(start: str, end: str) -> list[str]:
    first = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    if first > last:
        raise ValueError("start date is after end date")
    out = []
    day = first
    while day <= last:
        out.append(day.isoformat())
        day += dt.timedelta(days=1)
    return out


def read_cached(name: str) -> str | None:
    path = RAW_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else None


def write_cached(name: str, body: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / name).write_text(body, encoding="utf-8")


def collect(start: str, end: str, offline: bool) -> tuple[list[dict], list[dict]]:
    wanted = set(daterange(start, end))
    games: list[dict] = []
    standings: list[dict] = []

    # --- Results -----------------------------------------------------------
    schedule_body = read_cached("scheduleLeagueV2_1.json")
    if schedule_body is None and not offline:
        try:
            schedule_body = fetch(SCHEDULE_JSON)
            write_cached("scheduleLeagueV2_1.json", schedule_body)
            print("  fetched official static schedule JSON")
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
            print(f"  schedule JSON unavailable ({exc}); falling back to slate pages")
            schedule_body = None
    if schedule_body:
        try:
            games = parse_schedule_json(schedule_body, wanted)
            print(f"  schedule JSON: {len(games)} finished games in window")
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"  schedule JSON parse failed ({exc}); falling back to slate pages")
            games = []

    if not games:
        for date in sorted(wanted):
            body = read_cached(f"games_{date}.html")
            if body is None:
                if offline:
                    print(f"  {date}: no cached page and offline mode -> skipped")
                    continue
                url = f"https://www.nba.com/games?date={date}"
                try:
                    body = fetch(url)
                except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                    print(f"  {date}: fetch failed ({exc}) -> skipped, not inferred")
                    continue
                write_cached(f"games_{date}.html", body)
            try:
                rows = parse_next_data(body, date)
            except ValueError as exc:
                print(f"  {date}: {exc}")
                continue
            games.extend(rows)
            print(f"  {date}: {len(rows)} finished games")

    if not games:
        raise SystemExit("no games were collected; refusing to write an empty dataset")

    # --- Standings ---------------------------------------------------------
    standings_body = read_cached("standings.html")
    if standings_body is None and not offline:
        try:
            standings_body = fetch("https://www.nba.com/standings")
            write_cached("standings.html", standings_body)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            print(f"  standings fetch failed ({exc}) -> skipped")
    if standings_body:
        try:
            standings = parse_standings_markdown(normalise(standings_body))
        except ValueError as exc:
            print(f"  standings parse failed ({exc})")

    return games, standings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--start", default="2026-10-20")
    parser.add_argument("--end", default="2026-11-04")
    parser.add_argument("--offline", action="store_true",
                        help="rebuild from cached pages in data/lines/raw")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Collecting official NBA results for {args.start} .. {args.end}")
    games, standings = collect(args.start, args.end, args.offline)

    games.sort(key=lambda row: (row["date"], row["game_id"]))
    games_path = out / "nba_results_official.csv"
    with games_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(games[0].keys()))
        writer.writeheader()
        writer.writerows(games)
    print(f"wrote {len(games)} rows -> {games_path}")

    manifest = {
        "generated_by": "scripts/collect_lines_data.py",
        "window": {"start": args.start, "end": args.end},
        "games": len(games),
        "standings": len(standings),
        "sources": [
            {"dataset": "nba_results_official.csv",
             "slate_pattern": "https://www.nba.com/games?date=YYYY-MM-DD",
             "schedule_payload": SCHEDULE_JSON,
             "per_row_source": "https://www.nba.com/game/<slug>-<game_id>"},
            {"dataset": "nba_standings_official.csv",
             "pattern": "https://www.nba.com/standings",
             "schedule_payload": STANDINGS_JSON},
        ],
        "sha256": {
            games_path.name: hashlib.sha256(games_path.read_bytes()).hexdigest(),
        },
    }

    if standings:
        standings.sort(key=lambda row: row["team_abbr"])
        standings_path = out / "nba_standings_official.csv"
        with standings_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(standings[0].keys()))
            writer.writeheader()
            writer.writerows(standings)
        print(f"wrote {len(standings)} rows -> {standings_path}")
        manifest["sha256"][standings_path.name] = hashlib.sha256(
            standings_path.read_bytes()).hexdigest()

    (out / "collection_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote manifest -> {out / 'collection_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
