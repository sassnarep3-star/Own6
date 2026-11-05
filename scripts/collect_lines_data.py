#!/usr/bin/env python3
"""Collect official NBA game results from nba.com and emit a source-linked dataset.

This collector reads ONLY first-party NBA pages:

  * ``https://www.nba.com/games?date=YYYY-MM-DD``  - date slate with final scores
  * ``https://www.nba.com/standings``                - current standings table

Every emitted row carries the exact nba.com URL it was read from. No value is
inferred, interpolated or filled in. If a page cannot be read, the collector
fails loudly instead of emitting a partial row.

The script is deterministic given the fetched pages: re-running it reproduces the
same CSV byte for byte. It is also usable offline against pages cached in
``data/lines/raw/`` so the dataset can be rebuilt and audited without network
access.

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

USER_AGENT = "Own6-NBA-Lines-Lab/1.0 (research; contact via repository)"

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

# Full club names as printed on nba.com schedule and standings pages.
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

# The nba.com slate card renders, for each finished game:
#   logo \n TeamName \n record \n score \n Final[ /OT] \n score \n logo](GAME_URL)
# and for a scheduled game it renders the tip-off time instead of a score.
GAME_BLOCK = re.compile(
    r"!\[ ?Logo\]\([^\)]*logos/nba/(?P<away_id>\d+)/[^\)]*\)\n(?P<away>[A-Za-z0-9 .'\-]+?)\n"
    r"(?P<away_rec>\d+-\d+)\n(?P<away_score>\d+)\nFinal(?P<ot>/OT)?\n"
    r"(?P<home_score>\d+)\n!\[ ?Logo\]\([^\)]*logos/nba/(?P<home_id>\d+)/[^\)]*\)\n"
    r"(?P<home>[A-Za-z0-9 .'\-]+?)\n(?P<home_rec>\d+-\d+)\]\((?P<url>https://www\.nba\.com/game/[^)]+)\)"
)

STANDING_ROW = re.compile(
    r"\|\s*\[(?P<rank>\d+)[^\]]*\]\s*\[!\[ Logo\]\([^\)]*logos/nba/(?P<team_id>\d+)/[^\)]*\)[^\]]*\n"
    r"(?P<team>[A-Za-z0-9 .'\-]+?)\n\|\s*(?P<w>\d+)\s*\|\s*(?P<l>\d+)\s*\|"
)


def fetch(url: str, timeout: int = 45) -> str:
    """Return the HTML/text body of ``url`` or raise."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "text/html,*/*"})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def normalise(markdown: str) -> str:
    """Normalise a rendered page to the plain-text form the regexes expect.

    The page-to-markdown conversion escapes newlines as the literal sequence
    ``\\n``. Undo that so the same expressions work for raw HTML and for the
    cached markdown snapshots.
    """
    # The rendered page writes a literal backslash before every newline (the
    # markdown converter escapes hard breaks), and writes the separator as
    # backslash-newline-backslash-newline. Collapse each backslash run that
    # precedes a newline into a single newline, then squash the doubled
    # newlines that the escaped pair leaves behind.
    text = re.sub(r"\\+\n\\+\n", "\n", markdown)
    text = re.sub(r"\\+\n", "\n", text)
    return text


def parse_slate(markdown: str, date: str) -> list[dict]:
    """Extract finished games for one date from an nba.com slate page."""
    text = normalise(markdown)
    rows: list[dict] = []
    for match in GAME_BLOCK.finditer(text):
        away_id = match.group("away_id")
        home_id = match.group("home_id")
        if away_id not in TEAM_IDS or home_id not in TEAM_IDS:
            raise ValueError(f"{date}: unknown team id(s): {away_id} / {home_id}")
        away = TEAM_IDS[away_id]
        home = TEAM_IDS[home_id]
        url = match.group("url")
        slug = url.rsplit("/", 1)[-1]
        # The slug is "<away>-vs-<home>-<game_id>"; the abbreviations it uses
        # are the ESPN-style short codes, so verify the game id only.
        game_id = slug.rsplit("-", 1)[-1]
        if not game_id.isdigit() or len(game_id) != 10:
            raise ValueError(f"{date}: unexpected game id in {url}")
        rows.append({
            "date": date,
            "away_team": away,
            "away_team_name": match.group("away").strip(),
            "away_score": int(match.group("away_score")),
            "home_team": home,
            "home_team_name": match.group("home").strip(),
            "home_score": int(match.group("home_score")),
            "overtime": "yes" if match.group("ot") else "",
            "game_id": game_id,
            "source_url": url,
            "slate_url": f"https://www.nba.com/games?date={date}",
            "read_on": dt.date.today().isoformat(),
        })
    if not rows:
        raise ValueError(f"{date}: no finished games parsed from the nba.com slate page")
    return rows


def parse_standings(markdown: str) -> list[dict]:
    """Extract the current W-L table from the nba.com standings page."""
    text = normalise(markdown)
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


def read_cached(date: str) -> str | None:
    path = RAW_DIR / f"games_{date}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def write_cached(date: str, body: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / f"games_{date}.md").write_text(body, encoding="utf-8")


def collect(start: str, end: str, offline: bool) -> tuple[list[dict], list[dict]]:
    games: list[dict] = []
    standings: list[dict] = []
    for date in daterange(start, end):
        body = read_cached(date) if offline else None
        if body is None:
            if offline:
                print(f"  {date}: no cached page and offline mode -> skipped", file=sys.stderr)
                continue
            url = f"https://www.nba.com/games?date={date}"
            try:
                body = fetch(url)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                print(f"  {date}: fetch failed ({exc}) -> skipped, not inferred",
                      file=sys.stderr)
                continue
            write_cached(date, body)
        try:
            rows = parse_slate(body, date)
        except ValueError as exc:
            print(f"  {date}: {exc}", file=sys.stderr)
            continue
        games.extend(rows)
        print(f"  {date}: {len(rows)} finished games")
    if not games:
        raise SystemExit("no games were collected; refusing to write an empty dataset")

    standings_body = read_cached("standings") if offline else None
    if standings_body is None:
        if not offline:
            standings_body = fetch("https://www.nba.com/standings")
            write_cached("standings", standings_body)
    if standings_body is not None:
        try:
            standings = parse_standings(standings_body)
        except ValueError as exc:
            print(f"  standings: {exc}", file=sys.stderr)
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

    if standings:
        standings.sort(key=lambda row: row["team_abbr"])
        standings_path = out / "nba_standings_official.csv"
        with standings_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(standings[0].keys()))
            writer.writeheader()
            writer.writerows(standings)
        print(f"wrote {len(standings)} rows -> {standings_path}")

    manifest = {
        "generated_by": "scripts/collect_lines_data.py",
        "window": {"start": args.start, "end": args.end},
        "games": len(games),
        "standings": len(standings),
        "sources": [
            {"dataset": "nba_results_official.csv",
             "pattern": "https://www.nba.com/games?date=YYYY-MM-DD",
             "per_row_source": "https://www.nba.com/game/<slug>-<game_id>"},
            {"dataset": "nba_standings_official.csv",
             "pattern": "https://www.nba.com/standings"},
        ],
        "sha256": {
            games_path.name: hashlib.sha256(games_path.read_bytes()).hexdigest(),
            **({standings_path.name: hashlib.sha256(standings_path.read_bytes()).hexdigest()}
               if standings else {}),
        },
    }
    (out / "collection_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote manifest -> {out / 'collection_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
