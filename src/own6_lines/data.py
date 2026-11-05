"""Loading and integrity checks for the official NBA results dataset.

Every row in ``data/lines/nba_results_official.csv`` was read from nba.com
during the collection run and carries the nba.com URL of the game page it came
from. This module refuses to load a row that breaks that contract, so a
downstream number can never rest on an untraceable value.
"""
from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS_CSV = ROOT / "data/lines/nba_results_official.csv"
STANDINGS_CSV = ROOT / "data/lines/nba_standings_official.csv"

OFFICIAL_HOSTS = {"www.nba.com", "nba.com", "cdn.nba.com", "official.nba.com"}


@dataclass(frozen=True)
class Game:
    """One finished regular-season game from an official nba.com source."""

    date: str
    away_team: str
    away_score: int
    home_team: str
    home_score: int
    overtime: str
    game_id: str
    source_url: str
    slate_url: str
    read_on: str

    @property
    def day(self) -> dt.date:
        return dt.date.fromisoformat(self.date)

    @property
    def home_margin(self) -> int:
        """Points scored by the home club minus points scored by the away club."""
        return self.home_score - self.away_score

    @property
    def total_points(self) -> int:
        return self.home_score + self.away_score

    @property
    def home_win(self) -> int:
        return 1 if self.home_score > self.away_score else 0

    @property
    def away_win(self) -> int:
        return 1 if self.away_score > self.home_score else 0

    @property
    def went_to_overtime(self) -> bool:
        return bool(self.overtime)


@dataclass
class TeamRecord:
    """Running win/loss and scoring record for one club."""

    team: str
    games: int = 0
    wins: int = 0
    losses: int = 0
    points_for: int = 0
    points_against: int = 0
    home_games: int = 0
    away_games: int = 0
    home_wins: int = 0
    away_wins: int = 0
    margins: list[float] = field(default_factory=list)

    @property
    def win_pct(self) -> float:
        return self.wins / self.games if self.games else 0.0

    @property
    def points_per_game(self) -> float:
        return self.points_for / self.games if self.games else 0.0

    @property
    def points_allowed_per_game(self) -> float:
        return self.points_against / self.games if self.games else 0.0

    @property
    def net_rating(self) -> float:
        """Points scored per game minus points allowed per game."""
        if not self.games:
            return 0.0
        return (self.points_for - self.points_against) / self.games

    @property
    def pace(self) -> float:
        """Total points per game for this club (points scored by either side)."""
        if not self.games:
            return 0.0
        return (self.points_for + self.points_against) / self.games


def _is_official_url(url: str) -> bool:
    if not url.startswith("https://"):
        return False
    host = url.split("/", 3)[2].split(":", 1)[0].lower()
    return host in OFFICIAL_HOSTS


def load_games(path: Path = RESULTS_CSV, strict: bool = True) -> list[Game]:
    """Load official game results.

    ``strict`` (the default) raises on any row whose source link is missing
    or does not point at nba.com, because such a row cannot be audited.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run scripts/collect_lines_data.py first.")
    games: list[Game] = []
    problems: list[str] = []
    with path.open(newline="", encoding="utf-8") as stream:
        for number, row in enumerate(csv.DictReader(stream), start=2):
            if not row.get("source_url"):
                problems.append(f"line {number}: no source_url")
                if strict:
                    continue
            elif not _is_official_url(row["source_url"]):
                problems.append(f"line {number}: source_url is not an nba.com page")
                if strict:
                    continue
            try:
                games.append(Game(
                    date=row["date"],
                    away_team=row["away_team"],
                    away_score=int(row["away_score"]),
                    home_team=row["home_team"],
                    home_score=int(row["home_score"]),
                    overtime=row.get("overtime", ""),
                    game_id=row["game_id"],
                    source_url=row["source_url"],
                    slate_url=row.get("slate_url", ""),
                    read_on=row.get("read_on", ""),
                ))
            except (KeyError, ValueError) as exc:
                problems.append(f"line {number}: {exc}")
                if strict:
                    continue
    games.sort(key=lambda game: (game.date, game.game_id))
    if strict and problems:
        raise ValueError("official dataset failed integrity checks:\n  " +
                         "\n  ".join(problems[:20]))
    return games


def load_standings(path: Path = STANDINGS_CSV) -> list[dict]:
    """Load the official standings snapshot, if one was collected."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def records_through(games: list[Game], cutoff: str) -> dict[str, TeamRecord]:
    """Per-club records using only games played on or before ``cutoff``.

    ``cutoff`` is an ISO date. Games after it are excluded entirely, which is
    how the walk-forward engine guarantees a model never sees a future game.
    """
    out: dict[str, TeamRecord] = {}
    for game in games:
        if game.date > cutoff:
            continue
        for side in ("away", "home"):
            team = getattr(game, f"{side}_team")
            record = out.setdefault(team, TeamRecord(team=team))
            record.games += 1
            record.points_for += getattr(game, f"{side}_score")
            record.points_against += (game.home_score if side == "away"
                                      else game.away_score)
            if side == "home":
                record.home_games += 1
                record.margins.append(game.home_margin)
                if game.home_win:
                    record.wins += 1
                    record.home_wins += 1
                else:
                    record.losses += 1
            else:
                record.away_games += 1
                record.margins.append(-game.home_margin)
                if game.away_win:
                    record.wins += 1
                    record.away_wins += 1
                else:
                    record.losses += 1
    return out


def schedule_for_games(games: list[Game]) -> dict[str, list[Game]]:
    """Group games by date, in date order."""
    by_date: dict[str, list[Game]] = {}
    for game in games:
        by_date.setdefault(game.date, []).append(game)
    return dict(sorted(by_date.items()))
