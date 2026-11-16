"""Point-in-time standings reconstruction, verification loop, and the luck panel.

The central problem this module solves
--------------------------------------
``nfl.com/standings`` renders live. At capture time (2026-11-15, mid-Week-10) it already
contained the nine Week 10 games that had gone final and excluded the three still in
progress. Reading it as "the table through Week 9" would silently mix two vintages.

So we reconstruct the through-Week-9 table by *subtracting* the nine completed Week 10
games from the as-of-render table, game by game. That reconstruction is then checked
against an independent official page (S4) that printed each club's record before kickoff.
Ten clubs can be checked; a mismatch on any of them would invalidate the reconstruction.

Everything downstream (dispersion, the luck panel, the naive rating) runs off the
reconstructed table, never off the as-of-render one.
"""

from __future__ import annotations

from . import capture as C
from . import stats as S

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

CLUB_NAME = {
    "BUF": "Buffalo Bills", "NE": "New England Patriots", "NYJ": "New York Jets",
    "MIA": "Miami Dolphins", "PIT": "Pittsburgh Steelers", "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns", "BAL": "Baltimore Ravens", "JAX": "Jacksonville Jaguars",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "TEN": "Tennessee Titans",
    "KC": "Kansas City Chiefs", "DEN": "Denver Broncos", "LV": "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers", "NYG": "New York Giants", "DAL": "Dallas Cowboys",
    "WAS": "Washington Commanders", "PHI": "Philadelphia Eagles", "DET": "Detroit Lions",
    "MIN": "Minnesota Vikings", "CHI": "Chicago Bears", "GB": "Green Bay Packers",
    "CAR": "Carolina Panthers", "TB": "Tampa Bay Buccaneers", "NO": "New Orleans Saints",
    "ATL": "Atlanta Falcons", "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks",
    "LAR": "Los Angeles Rams", "AZ": "Arizona Cardinals",
}


def _norm(club: str) -> str:
    return C.CLUB_ABBR_ALIASES.get(club, club)


def final_games():
    """Week 10 games that had reached FINAL at capture time, as structured rows."""
    out = []
    for slug, date, kickoff, away, home, ap, hp, status, net in C.WEEK10_SLATE:
        if status != "FINAL":
            continue
        away, home = _norm(away), _norm(home)
        out.append(
            {
                "game_slug": slug,
                "date": date,
                "kickoff_et": kickoff,
                "away": away,
                "home": home,
                "away_points": int(ap),
                "home_points": int(hp),
                "winner": away if int(ap) > int(hp) else home,
                "margin": abs(int(ap) - int(hp)),
                "total_points": int(ap) + int(hp),
                "status": status,
                "network": net,
                "source_url": f"https://www.nfl.com/games/{slug}",
            }
        )
    return out


def live_games():
    """Week 10 games in progress or not started at capture time.

    Their scores are published, plainly marked, and are never allowed into the results
    feed or any model fit.
    """
    out = []
    live_scores = {slug: (ap, hp, q) for slug, _a, _h, ap, hp, q in C.WEEK10_LIVE_SCORES}
    for slug, date, kickoff, away, home, ap, hp, status, net in C.WEEK10_SLATE:
        if status == "FINAL":
            continue
        away, home = _norm(away), _norm(home)
        row = {
            "game_slug": slug,
            "date": date,
            "kickoff_et": kickoff,
            "away": away,
            "home": home,
            "away_points": ap,
            "home_points": hp,
            "status": status,
            "network": net,
            "source_url": f"https://www.nfl.com/games/{slug}",
        }
        if slug in live_scores:
            row["away_points"], row["home_points"], row["quarter"] = live_scores[slug][0], live_scores[slug][1], live_scores[slug][2]
        else:
            row["quarter"] = "not started"
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# reconstruction
# ---------------------------------------------------------------------------

def point_in_time_standings():
    """Through-Week-9 table, reconstructed by subtracting the nine completed Week 10 games.

    Returns (rows, checks). `checks` records the arithmetic performed on each club.
    """
    rendered = {c: dict(zip(("w", "l", "t", "pct", "pf", "pa"), (w, l, t, pct, pf, pa)))
                for c, w, l, t, pct, pf, pa, *_ in C.STANDINGS_RENDER}

    sub = {}
    for g in final_games():
        for club, own, opp in (
            (g["away"], g["away_points"], g["home_points"]),
            (g["home"], g["home_points"], g["away_points"]),
        ):
            sub.setdefault(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
            sub[club]["pf"] += own
            sub[club]["pa"] += opp
            if own > opp:
                sub[club]["w"] += 1
            elif own < opp:
                sub[club]["l"] += 1
            else:
                sub[club]["t"] += 1

    rows, checks = [], []
    for club, rec in rendered.items():
        s = sub.get(club, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0})
        w, l, t = rec["w"] - s["w"], rec["l"] - s["l"], rec["t"] - s["t"]
        pf, pa = rec["pf"] - s["pf"], rec["pa"] - s["pa"]
        gp = w + l + t
        rows.append(
            {
                "club": club,
                "club_name": CLUB_NAME.get(club, club),
                "through_week": 9,
                "w": w,
                "l": l,
                "t": t,
                "games": gp,
                "win_pct": (w + 0.5 * t) / gp if gp else 0.0,
                "pf": pf,
                "pa": pa,
                "net_points": pf - pa,
                "pf_per_game": pf / gp if gp else 0.0,
                "pa_per_game": pa / gp if gp else 0.0,
                "margin_per_game": (pf - pa) / gp if gp else 0.0,
                "week10_games_removed": s["w"] + s["l"] + s["t"],
            }
        )
        checks.append(
            {
                "club": club,
                "rendered_record": f"{rec['w']}-{rec['l']}-{rec['t']}",
                "rendered_pf": rec["pf"],
                "rendered_pa": rec["pa"],
                "week10_games_subtracted": s["w"] + s["l"] + s["t"],
                "subtracted_pf": s["pf"],
                "subtracted_pa": s["pa"],
                "reconstructed_record": f"{w}-{l}-{t}",
                "reconstructed_pf": pf,
                "reconstructed_pa": pa,
            }
        )
    rows.sort(key=lambda r: (-r["win_pct"], -r["net_points"]))
    return rows, checks


def verification_against_pregame_page(pit_rows):
    """Check the reconstruction against S4, the official page that printed each club's
    record before Week 10 kickoff. Returns one row per checkable club."""
    pit = {r["club"]: r for r in pit_rows}
    rendered = {c: (w, l, t) for c, w, l, t, *_ in C.STANDINGS_RENDER}

    def as_wlt(w, l, t):
        """Render a record the way the official pregame page does: it drops a zero tie
        column (prints '3-5', not '3-5-0')."""
        return f"{w}-{l}" if t == 0 else f"{w}-{l}-{t}"

    out, seen = [], set()
    for club, record, _player, _pos, _des, _res, _note in C.WEEK10_PREGAME:
        if club in seen:
            continue
        seen.add(club)
        if any(g["away"] == club or g["home"] == club for g in final_games()):
            r = pit[club]
            expected = as_wlt(r["w"], r["l"], r["t"])
            basis = "reconstructed through-Week-9 table"
        else:
            expected = as_wlt(*rendered[club])
            basis = "as-of-render standings (this club's Week 10 game had not gone final)"
        out.append(
            {
                "club": club,
                "record_on_pregame_page": record,
                "expected_from_arithmetic": expected,
                "match": "yes" if record == expected else "no",
                "basis": basis,
                "source_url": C.SOURCE_URL["S4"],
            }
        )
    return out


def integrity_checks(pit_rows):
    """Arithmetic identities the reconstructed table must satisfy."""
    total_pf = sum(r["pf"] for r in pit_rows)
    total_pa = sum(r["pa"] for r in pit_rows)
    total_games = sum(r["games"] for r in pit_rows) // 2
    wins = sum(r["w"] for r in pit_rows)
    losses = sum(r["l"] for r in pit_rows)
    ties = sum(r["t"] for r in pit_rows)
    return [
        {
            "check": "league points for equals league points against",
            "value_a": total_pf,
            "value_b": total_pa,
            "result": "pass" if total_pf == total_pa else "fail",
            "note": "every point scored by one club is conceded by another",
        },
        {
            "check": "wins equal losses",
            "value_a": wins,
            "value_b": losses,
            "result": "pass" if wins == losses else "fail",
            "note": f"{ties} tie game(s) counted on both clubs",
        },
        {
            "check": "team-games is even",
            "value_a": sum(r["games"] for r in pit_rows),
            "value_b": 2 * total_games,
            "result": "pass" if sum(r["games"] for r in pit_rows) == 2 * total_games else "fail",
            "note": "each game is counted twice, once per club",
        },
        {
            "check": "clubs in reconstructed table",
            "value_a": len(pit_rows),
            "value_b": 32,
            "result": "pass" if len(pit_rows) == 32 else "fail",
            "note": "the sweep must cover all 32 clubs before any team-level model is trusted",
        },
        {
            "check": "completed games through Week 9",
            "value_a": total_games,
            "value_b": 136,
            "result": "info",
            "note": "the brief refers to a 136-game log; this is the count the official "
                    "standings imply, derived as half the summed team-games",
        },
    ]


# ---------------------------------------------------------------------------
# luck panel
# ---------------------------------------------------------------------------

def luck_panel(pit_rows):
    """How much of the standings spread is luck?

    Method (uses only official numbers plus the standard binomial variance):
      obs_var  = population variance of win percentage across the 32 clubs
      null_var = mean over clubs of p(1-p)/n with p = 0.5, i.e. the spread we would see
                 if every game were a fair coin flip and no club were better than another
      luck_share = null_var / obs_var
      skill_var  = obs_var - null_var

    `luck_share` is a share, not a probability, and it is computed on a single season
    slice. It is published with its n and its caveat, never as a forecast.
    """
    wp = [r["win_pct"] for r in pit_rows]
    obs_var = S.pvariance(wp)
    null_vars = [0.25 / r["games"] for r in pit_rows if r["games"]]
    mean_null = S.mean(null_vars)
    skill_var = max(0.0, obs_var - mean_null)
    margin = [r["margin_per_game"] for r in pit_rows]
    return {
        "clubs": len(pit_rows),
        "team_games": sum(r["games"] for r in pit_rows),
        "games": sum(r["games"] for r in pit_rows) // 2,
        "obs_win_pct_variance": obs_var,
        "obs_win_pct_sd": S.pstdev(wp),
        "null_win_pct_variance": mean_null,
        "skill_variance": skill_var,
        "luck_share": (mean_null / obs_var) if obs_var else 0.0,
        "margin_sd": S.pstdev(margin),
        "league_ppg": S.mean([r["pf_per_game"] for r in pit_rows]),
        "league_papg": S.mean([r["pa_per_game"] for r in pit_rows]),
    }


def naive_ratings(pit_rows):
    """Net-points-per-game rating.

    Explicitly NOT opponent-aware. Opponent-aware ratings require the game-by-game log
    (gate G3); this table is published so the gap between the two is visible, and it is
    labelled on the page as unusable for origination until that gate clears.
    """
    out = []
    for r in pit_rows:
        out.append(
            {
                "club": r["club"],
                "club_name": r["club_name"],
                "rating_ppg": r["margin_per_game"],
                "win_pct": r["win_pct"],
                "pf_per_game": r["pf_per_game"],
                "pa_per_game": r["pa_per_game"],
                "opponent_adjusted": "no",
                "blocking_gate": "G3",
                "note": "margin per game with no opponent adjustment; unusable for origination",
            }
        )
    return sorted(out, key=lambda r: -r["rating_ppg"])
