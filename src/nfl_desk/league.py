"""Verified club register loading and league-level arithmetic (no inference)."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data" / "nfl_desk"


@dataclass(frozen=True)
class Club:
    abbr: str
    club: str
    conference: str
    division: str
    gp: int
    w: int
    l: int
    t: int
    pf: int
    pa: int
    home_w: int
    home_l: int
    home_t: int
    road_w: int
    road_l: int
    road_t: int
    source_url: str

    @property
    def net(self) -> int:
        return self.pf - self.pa

    @property
    def ppg(self) -> float:
        return self.pf / self.gp

    @property
    def papg(self) -> float:
        return self.pa / self.gp

    @property
    def net_ppg(self) -> float:
        return (self.pf - self.pa) / self.gp

    @property
    def wins_adj(self) -> float:
        """A tie counts as half a win - the arithmetic used for winning percentage."""
        return self.w + 0.5 * self.t


def load_clubs(filename: str = "standings_2026_thru_w10.csv") -> list[Club]:
    path = DATA / filename
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    clubs: list[Club] = []
    for r in rows:
        clubs.append(
            Club(
                abbr=r["abbr"], club=r["club"], conference=r["conference"], division=r["division"],
                gp=int(r["games_played"]), w=int(r["wins"]), l=int(r["losses"]), t=int(r["ties"]),
                pf=int(r["points_for"]), pa=int(r["points_against"]),
                home_w=int(r["home_w"]), home_l=int(r["home_l"]), home_t=int(r["home_t"]),
                road_w=int(r["road_w"]), road_l=int(r["road_l"]), road_t=int(r["road_t"]),
                source_url=r["source_url"],
            )
        )
    return clubs


def league_facts(clubs: list[Club]) -> dict[str, float]:
    """League aggregates that follow by arithmetic from the register - nothing is estimated."""
    if not clubs:
        raise ValueError("empty register")
    gp = sum(c.gp for c in clubs)
    games = gp / 2.0
    pf = sum(c.pf for c in clubs)
    pa = sum(c.pa for c in clubs)
    if pf != pa:
        raise ValueError(f"league points must balance: PF={pf} PA={pa}")
    home_w = sum(c.home_w for c in clubs)
    home_l = sum(c.home_l for c in clubs)
    home_t = sum(c.home_t for c in clubs)
    if home_w + home_l + home_t != games:
        raise ValueError("home records do not account for every game")
    net_abs_mean = sum(abs(c.net_ppg) for c in clubs) / len(clubs)
    var_net = sum((c.net_ppg - 0.0) ** 2 for c in clubs) / (len(clubs) - 1)
    return {
        "clubs": float(len(clubs)),
        "team_games": float(gp),
        "games": games,
        "points_for": float(pf),
        "points_against": float(pa),
        "league_avg_points_per_team_game": pf / gp,
        "home_wins": float(home_w),
        "home_losses": float(home_l),
        "home_ties": float(home_t),
        "home_win_share": home_w / games,
        "home_tie_share": home_t / games,
        "mean_abs_net_ppg": net_abs_mean,
        "sd_team_net_ppg": math.sqrt(var_net),
    }


def round_half(x: float, tick: float = 0.5) -> float:
    """Round to the nearest published line increment (banks quote .5 or .0)."""
    return math.floor(x / tick + 0.5) * tick
