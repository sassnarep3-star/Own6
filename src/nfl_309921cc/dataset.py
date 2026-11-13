"""Derive every published table row for the NFL-309921cc pack.

Rule enforced here: a cell that cannot be traced to an official page read in
this session is emitted as an empty string and is registered in
``flagged.csv``. Model outputs are emitted but never labelled "verified";
they carry ``status=model_output``.
"""

from __future__ import annotations

import csv
import math
import os
from typing import Dict, List, Sequence

from . import verified as V
from . import stats

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "nfl_309921cc")

STANDINGS_URL = "https://www.nfl.com/standings/"
INJURY_URL = "https://www.nfl.com/injuries/"
SLATE_URL = "https://www.nfl.com/schedules"
SCORES_URL = "https://www.nfl.com/scores/"
TERMS_URL = "https://www.nfl.com/legal/terms/"
PARTNERS_URL = "https://www.nfl.com/news/nfl-draftkings-fanduel-fanatics-sports-betting-partners"
RULEBOOK_URL = "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"
CBA_URL = "https://operations.nfl.com/inside-football-ops/players-legends/2020-nfl-nflpa-cba-need-to-know/"
TEAMSTATS_URL = "https://www.nfl.com/stats/team-stats/"

# Preregistered model parameters. These are DECLARED, not measured, and are
# listed in flagged.csv (NFL3-F06). They are all neutral/identity values so the
# published originated line contains no un-sourced fitted coefficient.
HFA_POINTS = 0.0
SHRINKAGE = 1.0  # no regression-to-mean applied; needs licensed history to fit

# Proposed (NOT observed) depth-deficiency weights - flag NFL3-F07.
DEFICIENCY_WEIGHTS = {
    "starter_healthy": 0.00,
    "starter_questionable": 0.35,
    "second_string_healthy": 0.65,
    "second_string_questionable": 0.85,
    "third_string_or_worse": 1.00,
    "no_listed_replacement": 1.00,
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _f(x, nd=3):
    return f"{x:.{nd}f}"


def _blank():
    return ""


def record_pct(rec: str) -> float:
    """Win percentage from a 'W-L-T' record string using the NFL convention
    (a tie counts as half a win). Returns 0.0 for a 0-game record."""
    parts = rec.split("-")
    if len(parts) != 3:
        return 0.0
    try:
        w, l, t = (int(p) for p in parts)
    except ValueError:
        return 0.0
    g = w + l + t
    if g == 0:
        return 0.0
    return (w + 0.5 * t) / g


def team_index() -> Dict[str, dict]:
    idx = {}
    for (conf, div, team, abbr, w, l, t, pct, home, road, divrec, confrec,
         pf, pa, net, streak) in V.STANDINGS:
        g = w + l + t
        idx[abbr] = {
            "conference": conf, "division": div, "team": team, "abbr": abbr,
            "w": w, "l": l, "t": t, "pct": pct, "home": home, "road": road,
            "div": divrec, "conf": confrec, "pf": pf, "pa": pa,
            "net": net, "streak": streak, "games": g,
            "ppg": pf / g if g else 0.0,
            "papg": pa / g if g else 0.0,
            "net_ppg": net / g if g else 0.0,
            "win_pct": (w + 0.5 * t) / g if g else 0.0,
            "home_win_pct": record_pct(home),
            "road_win_pct": record_pct(road),
            "div_win_pct": record_pct(divrec),
            "conf_win_pct": record_pct(confrec),
        }
    return idx


# --------------------------------------------------------------------------
# 1. standings
# --------------------------------------------------------------------------
def standings_rows() -> List[dict]:
    out = []
    for t in team_index().values():
        out.append({
            "conference": t["conference"], "division": t["division"],
            "team": t["team"], "abbr": t["abbr"],
            "w": t["w"], "l": t["l"], "t": t["t"], "pct": t["pct"],
            "pf": t["pf"], "pa": t["pa"], "net_pts": t["net"],
            "home": t["home"], "road": t["road"], "div": t["div"],
            "conf": t["conf"], "streak": t["streak"],
            "games_played": t["games"],
            "pf_per_game": _f(t["ppg"], 3),
            "pa_per_game": _f(t["papg"], 3),
            "net_pts_per_game": _f(t["net_ppg"], 3),
            "status": "verified",
            "official_source_url": STANDINGS_URL,
        })
    return out


STANDINGS_FIELDS = ["conference", "division", "team", "abbr", "w", "l", "t", "pct",
                    "pf", "pa", "net_pts", "home", "road", "div", "conf", "streak",
                    "games_played", "pf_per_game", "pa_per_game", "net_pts_per_game",
                    "status", "official_source_url"]


# --------------------------------------------------------------------------
# 2. slate + byes
# --------------------------------------------------------------------------
def slate_rows() -> List[dict]:
    out = []
    for (gid, day, date, time_et, net, away, arec, home, hrec, status,
         ascore, hscore, url) in V.SLATE:
        row = {
            "game_id": gid, "week": 10, "season": 2026, "day": day, "date": date,
            "kickoff_et": time_et, "network": net,
            "away": away, "away_record_pregame": arec,
            "home": home, "home_record_pregame": hrec,
            "game_status": status,
            "away_score": ascore, "home_score": hscore,
            "official_source_url": url,
        }
        out.append(row)
    return out


SLATE_FIELDS = ["game_id", "week", "season", "day", "date", "kickoff_et", "network",
                "away", "away_record_pregame", "home", "home_record_pregame",
                "game_status", "away_score", "home_score", "official_source_url"]


def bye_rows() -> List[dict]:
    return [{
        "week": 10, "season": 2026, "team_abbr": abbr, "record_pregame": rec,
        "official_source_url": url,
    } for abbr, rec, url in V.BYES]


BYE_FIELDS = ["week", "season", "team_abbr", "record_pregame", "official_source_url"]


# --------------------------------------------------------------------------
# 3. injuries + per-club load
# --------------------------------------------------------------------------
def injury_rows() -> List[dict]:
    out = []
    for i, (team, player, pos, injury, practice, game_status) in enumerate(V.INJURIES, 1):
        out.append({
            "row_id": f"INJ-{i:03d}",
            "week": 10, "season": 2026, "team_abbr": team, "player": player,
            "position": pos, "injury": injury,
            "practice_status": practice, "game_status": game_status,
            "official_source_url": INJURY_URL,
        })
    return out


INJURY_FIELDS = ["row_id", "week", "season", "team_abbr", "player", "position",
                 "injury", "practice_status", "game_status", "official_source_url"]


def injury_load_rows() -> List[dict]:
    by_team: Dict[str, List[tuple]] = {}
    for team, player, pos, injury, practice, game_status in V.INJURIES:
        by_team.setdefault(team, []).append((player, pos, injury, practice, game_status))

    # Official NFL practice-status vocabulary, as it appears on the page.
    dnp = "Did Not Participate In Practice"
    lim = "Limited Participation in Practice"
    full = "Full Participation in Practice"

    out = []
    order = []
    for (gid, _d, _dt, _t, _n, away, _ar, home, _hr, *_rest) in V.SLATE:
        order.extend([away, home])
    for team in order:
        rows = by_team.get(team, [])
        n = len(rows)
        c_dnp = sum(1 for r in rows if r[3] == dnp)
        c_lim = sum(1 for r in rows if r[3] == lim)
        c_full = sum(1 for r in rows if r[3] == full)
        c_out = sum(1 for r in rows if r[4] == "Out")
        c_q = sum(1 for r in rows if r[4] == "Questionable")
        c_doubt = sum(1 for r in rows if r[4] == "Doubtful")
        c_none = sum(1 for r in rows if r[4] == "")
        out.append({
            "team_abbr": team, "week": 10, "season": 2026,
            "players_listed": n,
            "did_not_participate": c_dnp,
            "limited": c_lim,
            "full": c_full,
            "designated_out": c_out,
            "designated_questionable": c_q,
            "designated_doubtful": c_doubt,
            "no_game_status_published": c_none,
            "dnp_share": _f(c_dnp / n, 3) if n else _blank(),
            "status": "verified_count",
            "official_source_url": INJURY_URL,
        })
    return out


INJURY_LOAD_FIELDS = ["team_abbr", "week", "season", "players_listed",
                      "did_not_participate", "limited", "full",
                      "designated_out", "designated_questionable",
                      "designated_doubtful", "no_game_status_published",
                      "dnp_share", "status", "official_source_url"]


# --------------------------------------------------------------------------
# 4. depth charts + deficiency
# --------------------------------------------------------------------------
def depth_chart_rows() -> List[dict]:
    out = []
    for team, unit, slot, strings in V.DEPTH_CHARTS:
        out.append({
            "team_abbr": team, "unit": unit, "position_slot": slot,
            "first_string": strings[0], "second_string": strings[1],
            "third_string": strings[2], "fourth_string": strings[3],
            "strings_listed": sum(1 for s in strings if s),
            "source_status": "verified_direct_unofficial_source",
            "source_caveat": V.DEPTH_CHART_CAVEAT[team],
            "official_source_url": V.DEPTH_CHART_SOURCE[team],
        })
    return out


DEPTH_CHART_FIELDS = ["team_abbr", "unit", "position_slot", "first_string",
                      "second_string", "third_string", "fourth_string",
                      "strings_listed", "source_status", "source_caveat",
                      "official_source_url"]


def _designation(team: str, player: str) -> str:
    """Game status on the official report for this player.

    Returns ``not_on_injury_report`` when the player does not appear on the
    report at all, and ``no_designation_published`` when the report lists the
    player but leaves the Game Status cell blank.
    """
    for t, p, _pos, _inj, _pr, gs in V.INJURIES:
        if t == team and p == player:
            return gs if gs else "no_designation_published"
    return "not_on_injury_report"


def depth_deficiency_rows() -> List[dict]:
    """Map every club depth slot onto the official injury designations.

    A slot's *active string* is the shallowest listed string not ruled Out.
    ``deficiency_score`` uses the proposed weights in ``DEFICIENCY_WEIGHTS``
    (flag NFL3-F07): it is a design hypothesis, not an observed quantity.
    """
    out = []
    w = DEFICIENCY_WEIGHTS
    for team, unit, slot, strings in V.DEPTH_CHARTS:
        designations = [_designation(team, s) if s else "empty_slot"
                        for s in strings]
        active_idx = None
        for i, s in enumerate(strings):
            if s and designations[i] != "Out":
                active_idx = i
                break
        if active_idx is None:
            active_string = "no_listed_player"
            score = w["no_listed_replacement"]
            replacement = ""
            replacement_string = ""
        else:
            active_string = str(active_idx + 1)
            replacement = ""
            replacement_string = ""
            for j in range(active_idx + 1, len(strings)):
                # "available" means listed on the chart and NOT ruled Out.
                if strings[j] and designations[j] != "Out":
                    replacement = strings[j]
                    replacement_string = str(j + 1)
                    break
            gs = designations[active_idx]
            if active_idx == 0:
                score = (w["starter_questionable"] if gs == "Questionable"
                         else w["starter_healthy"])
            elif active_idx == 1:
                score = (w["second_string_questionable"] if gs == "Questionable"
                         else w["second_string_healthy"])
            else:
                score = w["third_string_or_worse"]

        out_players = [s for i, s in enumerate(strings) if s and designations[i] == "Out"]
        q_players = [s for i, s in enumerate(strings)
                     if s and designations[i] == "Questionable"]
        out.append({
            "team_abbr": team, "unit": unit, "position_slot": slot,
            "first_string": strings[0],
            "active_string": active_string,
            "active_player": strings[active_idx] if active_idx is not None else "",
            "active_game_status": (designations[active_idx]
                                   if active_idx is not None else "none_listed"),
            "next_available_backup": replacement,
            "next_backup_string": replacement_string if replacement else "",
            "ruled_out_in_slot": "; ".join(out_players),
            "questionable_in_slot": "; ".join(q_players),
            "deficiency_score": _f(score, 2),
            "score_kind": "proposed_weight_not_observed",
            "official_source_url": V.DEPTH_CHART_SOURCE[team],
            "injury_report_url": INJURY_URL,
        })
    return out


DEPTH_DEFICIENCY_FIELDS = ["team_abbr", "unit", "position_slot", "first_string",
                           "active_string", "active_player", "active_game_status",
                           "next_available_backup", "next_backup_string",
                           "ruled_out_in_slot", "questionable_in_slot",
                           "deficiency_score", "score_kind",
                           "official_source_url", "injury_report_url"]


def _name_variant(player: str, names: Sequence[str]) -> str:
    """Chart entries whose name shares a token prefix with ``player``.

    This is a pure string comparison and is reported as a candidate only. It is
    NOT an identity claim: the pack does not assert that "Kevin Byard" and
    "Kevin Byard III" are the same person, because no official page here says so.
    """
    p = player.lower().strip()
    hits = []
    for n in names:
        q = n.lower().strip()
        if not q or q == p:
            continue
        if q.startswith(p) or p.startswith(q):
            hits.append(n)
    return "; ".join(sorted(hits))


def unlisted_designated_rows() -> List[dict]:
    """Designated players who do not appear anywhere on their club's chart."""
    charts: Dict[str, set] = {}
    for team, _u, _s, strings in V.DEPTH_CHARTS:
        charts.setdefault(team, set()).update(s for s in strings if s)
    out = []
    for team, player, pos, injury, practice, gs in V.INJURIES:
        if team in charts and gs in ("Out", "Questionable", "Doubtful"):
            if player not in charts[team]:
                variant = _name_variant(player, sorted(charts[team]))
                out.append({
                    "team_abbr": team, "player": player, "position": pos,
                    "game_status": gs, "practice_status": practice,
                    "injury": injury,
                    "finding": "Designated on the official NFL injury report but absent from the club's published (unofficial) depth chart under this exact spelling.",
                    "same_prefix_name_on_chart": variant,
                    "name_match_is_verified_identity": "no - string prefix only, not an identity claim",
                    "official_source_url": INJURY_URL,
                    "depth_chart_url": V.DEPTH_CHART_SOURCE[team],
                })
    return out


UNLISTED_FIELDS = ["team_abbr", "player", "position", "game_status",
                   "practice_status", "injury", "finding",
                   "same_prefix_name_on_chart", "name_match_is_verified_identity",
                   "official_source_url", "depth_chart_url"]


# --------------------------------------------------------------------------
# 5. measured correlations + luck index
# --------------------------------------------------------------------------
def _pairs(abbrs: Sequence[str], key_x: str, key_y: str, idx: Dict[str, dict]):
    xs = [idx[a][key_x] for a in abbrs]
    ys = [idx[a][key_y] for a in abbrs]
    return xs, ys


def correlation_rows() -> List[dict]:
    idx = team_index()
    abbrs = [r[3] for r in V.STANDINGS]
    specs = [
        ("NFL3-COR-01", "Points for per game", "Win percentage",
         "ppg", "win_pct", "pearson"),
        ("NFL3-COR-02", "Points against per game", "Win percentage",
         "papg", "win_pct", "pearson"),
        ("NFL3-COR-03", "Net points per game", "Win percentage",
         "net_ppg", "win_pct", "pearson"),
        ("NFL3-COR-04", "Points for per game", "Points against per game",
         "ppg", "papg", "pearson"),
        ("NFL3-COR-05", "Net points per game", "Win percentage",
         "net_ppg", "win_pct", "spearman"),
        ("NFL3-COR-06", "Home win percentage", "Overall win percentage",
         "home_win_pct", "win_pct", "pearson"),
        ("NFL3-COR-07", "Division win percentage", "Overall win percentage",
         "div_win_pct", "win_pct", "pearson"),
        ("NFL3-COR-08", "Points for per game", "Net points per game",
         "ppg", "net_ppg", "pearson"),
    ]
    out = []
    for cid, xlabel, ylabel, kx, ky, method in specs:
        xs, ys = _pairs(abbrs, kx, ky, idx)
        r = stats.pearson(xs, ys) if method == "pearson" else stats.spearman(xs, ys)
        n = len(xs)
        if r is None:
            out.append({
                "correlation_id": cid, "x_variable": xlabel, "y_variable": ylabel,
                "method": method, "n": n, "coefficient": _blank(),
                "p_value": _blank(), "ci95_low": _blank(), "ci95_high": _blank(),
                "bootstrap_ci95_low": _blank(), "bootstrap_ci95_high": _blank(),
                "status": "unverified", "official_source_url": STANDINGS_URL,
            })
            continue
        df = n - 2
        t = r * math.sqrt(df / (1 - r * r)) if abs(r) < 1 else float("inf")
        p = stats.t_sf_two_sided(t, df)
        ci = stats.fisher_z_ci(r, n)
        bci = stats.percentile_bootstrap_ci(xs, ys, stats.pearson if method == "pearson"
                                            else stats.spearman, draws=5000)
        out.append({
            "correlation_id": cid, "x_variable": xlabel, "y_variable": ylabel,
            "method": method, "n": n, "coefficient": _f(r, 4),
            "p_value": f"{p:.6g}",
            "ci95_low": _f(ci[0], 4) if ci else _blank(),
            "ci95_high": _f(ci[1], 4) if ci else _blank(),
            "bootstrap_ci95_low": _f(bci[0], 4) if bci else _blank(),
            "bootstrap_ci95_high": _f(bci[1], 4) if bci else _blank(),
            "status": "measured_from_verified_official_data",
            "official_source_url": STANDINGS_URL,
        })
    return out


CORRELATION_FIELDS = ["correlation_id", "x_variable", "y_variable", "method", "n",
                      "coefficient", "p_value", "ci95_low", "ci95_high",
                      "bootstrap_ci95_low", "bootstrap_ci95_high", "status",
                      "official_source_url"]


def luck_rows() -> tuple:
    """OLS win% ~ net points per game. The residual is the luck proxy."""
    idx = team_index()
    abbrs = [r[3] for r in V.STANDINGS]
    xs = [idx[a]["net_ppg"] for a in abbrs]
    ys = [idx[a]["win_pct"] for a in abbrs]
    fit = stats.ols_simple(xs, ys)
    rows = []
    for a, resid in zip(abbrs, fit["residuals"]):
        rows.append({
            "team_abbr": a, "team": idx[a]["team"],
            "games_played": idx[a]["games"],
            "win_pct": _f(idx[a]["win_pct"], 3),
            "net_pts_per_game": _f(idx[a]["net_ppg"], 3),
            "expected_win_pct_from_net_pts": _f(fit["intercept"] + fit["slope"] * idx[a]["net_ppg"], 3),
            "luck_residual_win_pct": _f(resid, 3),
            "luck_residual_wins": _f(resid * idx[a]["games"], 2),
            "status": "measured_from_verified_official_data",
            "official_source_url": STANDINGS_URL,
        })
    rows.sort(key=lambda r: float(r["luck_residual_win_pct"]), reverse=True)
    summary = {
        "n": fit["n"],
        "intercept": _f(fit["intercept"], 4),
        "slope": _f(fit["slope"], 6),
        "r2": _f(fit["r2"], 4),
        "residual_sd_win_pct": _f(fit["residual_sd"], 4),
        "se_slope": _f(fit["se_slope"], 6),
        "t_slope": _f(fit["t_slope"], 4),
        "p_slope": f"{fit['p_slope']:.6g}",
        "df": fit["df"],
    }
    return rows, summary


LUCK_FIELDS = ["team_abbr", "team", "games_played", "win_pct", "net_pts_per_game",
               "expected_win_pct_from_net_pts", "luck_residual_win_pct",
               "luck_residual_wins", "status", "official_source_url"]


# --------------------------------------------------------------------------
# 6. originated lines
# --------------------------------------------------------------------------
def originated_line_rows() -> tuple:
    idx = team_index()
    rows = []
    for (gid, _d, _dt, _t, _n, away, _ar, home, _hr, status, *_rest) in V.SLATE:
        h, a = idx[home], idx[away]
        home_exp = SHRINKAGE * (h["ppg"] + a["papg"]) / 2.0 + HFA_POINTS / 2.0
        away_exp = SHRINKAGE * (a["ppg"] + h["papg"]) / 2.0 - HFA_POINTS / 2.0
        margin = home_exp - away_exp
        played = status == "final"
        rows.append({
            "game_id": gid, "away": away, "home": home,
            "home_ppg_input": _f(h["ppg"], 3),
            "home_papg_input": _f(h["papg"], 3),
            "away_ppg_input": _f(a["ppg"], 3),
            "away_papg_input": _f(a["papg"], 3),
            "inputs_status": "verified",
            "inputs_source_url": STANDINGS_URL,
            "hfa_points_parameter": _f(HFA_POINTS, 2),
            "shrinkage_parameter": _f(SHRINKAGE, 2),
            "expected_home_points": _blank() if played else _f(home_exp, 2),
            "expected_away_points": _blank() if played else _f(away_exp, 2),
            "originated_home_spread": _blank() if played else _f(-margin, 2),
            "originated_total": _blank() if played else _f(home_exp + away_exp, 2),
            "model_applicability": ("already_final - not modelled; the verified result is on the Slate page"
                                    if played else "scheduled"),
            "originated_moneyline_home_prob": _blank(),
            "originated_moneyline_home_prob_note": "Blank: requires a margin-distribution (spread of victory-margin) parameter that no official NFL page in this pack supplies. See flag NFL3-F08.",
            "market_spread": _blank(),
            "market_total": _blank(),
            "closing_line_value": _blank(),
            "status": "model_output",
            "official_source_url": SLATE_URL,
        })
    # self-consistency check against the league's own totals
    total_team_games = sum(idx[a]["games"] for a in idx)
    league_pts_per_team_game = sum(idx[a]["pf"] for a in idx) / total_team_games
    live = [r for r in rows if r["model_applicability"] == "scheduled"]
    model_mean_total = sum(float(r["originated_total"]) for r in live) / len(live)
    model_mean_abs_spread = sum(abs(float(r["originated_home_spread"])) for r in live) / len(live)
    check = {
        "league_points_per_team_game": _f(league_pts_per_team_game, 4),
        "league_points_per_game_both_teams": _f(2 * league_pts_per_team_game, 4),
        "model_mean_total": _f(model_mean_total, 4),
        "model_minus_league_total": _f(model_mean_total - 2 * league_pts_per_team_game, 4),
        "model_mean_abs_home_spread": _f(model_mean_abs_spread, 4),
        "games_modelled": len(live),
        "games_excluded_already_final": len(rows) - len(live),
    }
    return rows, check


ORIGINATED_FIELDS = ["game_id", "away", "home", "home_ppg_input", "home_papg_input",
                     "away_ppg_input", "away_papg_input", "inputs_status",
                     "inputs_source_url", "hfa_points_parameter", "shrinkage_parameter",
                     "expected_home_points", "expected_away_points",
                     "model_applicability",
                     "originated_home_spread", "originated_total",
                     "originated_moneyline_home_prob",
                     "originated_moneyline_home_prob_note", "market_spread",
                     "market_total", "closing_line_value", "status",
                     "official_source_url"]


# --------------------------------------------------------------------------
# 7. strategy catalog (preregistered, zero selections graded)
# --------------------------------------------------------------------------
# family, market, hypothesis, signal_rule, own_line_method, inputs_verified,
# correlation_pair, required_gates, selections_graded, status
STRATEGIES = [
    ("NFL3-ST-01", "Single bet", "Spread",
     "A team whose net-points-per-game advantage over its opponent exceeds the model's own fair spread by more than a frozen edge threshold is a candidate.",
     "Signal only if the originated spread deviates from the graded reference line by at least the frozen minimum edge AND every gate in required_gates is open.",
     "Originated spread from verified PF/PA per game (NFL3-S05) and the verified slate (NFL3-S07).",
     "Verified: 32 standings rows and all 14 Week 10 games. Not verified: the edge threshold, which is a declared parameter and has not been fitted.",
     "n/a - single leg", "G01,G02,G03,G04,G05,G06,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-02", "Single bet", "Total (over/under)",
     "A matchup of a high points-for team against a high points-against team produces a total above the model's own fair total.",
     "Signal only if the gap between the model total and the reference total clears the frozen threshold and the calibration gates pass.",
     "Originated total from verified PF/PA per game (NFL3-S05).",
     "Verified: 32 standings rows, and the model total is checked against the league's own points-per-game. Not verified: the threshold and any reference total.",
     "n/a - single leg", "G01,G02,G03,G04,G05,G06,G07,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-03", "Single bet", "Moneyline",
     "The model's win probability for the home side, once a victory-margin distribution is licensed and fitted, will be compared to the reference price.",
     "Blocked until a margin-distribution parameter exists (flag NFL3-F08); no probability is published and no selection may be graded.",
     "Originated margin from verified PF/PA per game; the margin distribution is NOT available from any official source in this pack.",
     "Verified: the point margin inputs. Missing: the margin-distribution parameter, so this strategy cannot produce a price at all.",
     "n/a - single leg", "G01,G02,G03,G04,G05,G06,G07,G10,G11,G12", 0,
     "blocked_missing_parameter"),
    ("NFL3-ST-04", "Player prop", "Player performance markets",
     "Only markets that are not within the league's objectionable categories are eligible; injury-tied and officiating-tied markets are permanently excluded.",
     "Eligibility gate G11 is applied before any modelling: a prop family tied to injuries or officiating is rejected by construction.",
     "Eligibility rule taken from the NFL's own release (NFL3-S02); no prop line data is captured anywhere in this pack.",
     "Verified: the eligibility rule text. Missing: every prop line, every player-level dataset, and every settlement rule.",
     "Within-same-player markets share one performer and must never be treated as independent",
     "G01,G02,G03,G04,G05,G06,G09,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-05", "Player prop", "Depth-driven usage props",
     "When a 1st-string player at a skill position is ruled Out, the next listed string's usage share rises; this is a usage hypothesis, not a price hypothesis.",
     "Requires a licensed snap-share and target-share history; both are absent, so no value is produced.",
     "Depth ordering from the club charts (NFL3-S09, NFL3-S10) and designations from the official report (NFL3-S08).",
     "Verified: the depth ordering and the designations. Missing: any usage-share history, so the hypothesis is untestable here.",
     "Backup usage is negatively dependent on the starter's own prop",
     "G01,G02,G03,G04,G05,G06,G09,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-06", "Prop combo (SGP)", "Same-game quarterback + receiver stack",
     "A quarterback's passing market and his receiver's receiving market are positively dependent; pricing them as independent misprices the joint event.",
     "The joint price is produced only from a measured dependence; no independence assumption is permitted anywhere in this catalog.",
     "Dependence method defined on the Correlations page; the measured rho stays blank until a paired licensed history exists (flag NFL3-F09).",
     "Verified: the method and the eight league-level correlations measured from official data. Missing: any measured dependence for this pair.",
     "QB passing yards vs WR receiving yards",
     "G01,G02,G03,G04,G05,G06,G07,G09,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-07", "Prop combo (SGP)", "Same-game running back + team total",
     "A running back's rushing market and his own team's total are positively dependent through game script.",
     "Joint price from a measured dependence only; independence is never assumed.",
     "Dependence method defined on the Correlations page; the measured rho stays blank until a paired licensed history exists (flag NFL3-F09).",
     "Verified: the method. Missing: any measured dependence for this pair.",
     "RB rushing yards vs own team total",
     "G01,G02,G03,G04,G05,G06,G07,G09,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-08", "Parlay", "Cross-game spread parlay",
     "Legs drawn from different games are treated as independent only after an empirical test; independence is a claim to be tested, not an input.",
     "Cross-game dependence must be estimated from graded history before any multi-leg price is published.",
     "Slate from NFL3-S07; no graded history exists yet.",
     "Verified: the 14-game slate. Missing: graded leg outcomes, so no dependence can be estimated.",
     "Game A margin vs Game B margin",
     "G01,G02,G03,G04,G05,G06,G07,G09,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-09", "Parlay", "Same-game spread + total parlay",
     "The home cover event and the over event share the same scoring process and are dependent, in a direction that depends on which team leads.",
     "The joint price requires the measured same-game dependence; blank until measured.",
     "Model margin and total from verified PF/PA per game (NFL3-S05).",
     "Verified: the model margin and total inputs. Missing: the measured same-game dependence.",
     "Home cover vs game over",
     "G01,G02,G03,G04,G05,G06,G07,G09,G10,G11,G12", 0,
     "preregistered_not_qualified"),
    ("NFL3-ST-10", "Meta", "Closing-line value (CLV) diagnostic",
     "A strategy that cannot beat the closing price is not a skill strategy, no matter what its win rate looks like in a small sample.",
     "CLV is computed only against licensed closing prices; none are held, so the column stays blank.",
     "No licensed price archive is configured (flag NFL3-F10).",
     "Verified: the definition and the reason it matters. Missing: every closing price.",
     "n/a - diagnostic", "G01,G02,G03,G04,G08,G10,G12", 0,
     "blocked_missing_data"),
]


def strategy_rows() -> List[dict]:
    out = []
    for (sid, family, market, hyp, rule, method, inputs, pair, gates,
         graded, status) in STRATEGIES:
        out.append({
            "strategy_id": sid, "family": family, "market": market,
            "hypothesis": hyp, "signal_rule": rule,
            "own_line_method": method, "inputs_verified": inputs,
            "correlation_pair": pair, "required_gates": gates,
            "selections_graded": graded,
            "qualified": "no",
            "status": status,
            "official_source_url": PARTNERS_URL if family == "Player prop" else SLATE_URL,
        })
    return out


STRATEGY_FIELDS = ["strategy_id", "family", "market", "hypothesis", "signal_rule",
                   "own_line_method", "inputs_verified", "correlation_pair",
                   "required_gates", "selections_graded", "qualified", "status",
                   "official_source_url"]


# --------------------------------------------------------------------------
# 8. validation gates
# --------------------------------------------------------------------------
# gate_id, name, rule, why_it_removes_luck, blocking_missing_input, status
GATES = [
    ("G01", "Rights and provenance",
     "Every input row must trace to an official NFL or club page read in this session, and the pack must be non-commercial and informational only.",
     "Does not remove luck; it prevents a result that cannot be lawfully reproduced from ever reaching the board.",
     "", "open"),
    ("G02", "No invented market prices",
     "A strategy may not be graded against any price this repository did not obtain under licence. Reference prices stay blank.",
     "Prevents a fabricated benchmark from manufacturing apparent skill.",
     "Licensed historical price archive.", "blocked"),
    ("G03", "Minimum sample",
     "At least 200 graded selections per strategy family before any performance statistic is published.",
     "Small samples are dominated by variance; the floor stops a short lucky run from qualifying.",
     "Graded selection history.", "blocked"),
    ("G04", "Chronological out-of-sample",
     "Parameters are fitted on seasons strictly before the test season; no random k-fold and no same-season fitting.",
     "Removes in-sample optimism, the most common way luck is mistaken for skill.",
     "Multi-season results and price history.", "blocked"),
    ("G05", "Pre-registration",
     "Hypothesis, signal rule, stop rule and parameter values are recorded before any selection is graded.",
     "Removes post-hoc rule-shopping, which turns noise into apparent signal.",
     "", "open"),
    ("G06", "Multiple-testing control",
     "Holm-Bonferroni correction across the whole strategy family at family-wise alpha = 0.05.",
     "Ten strategies tested at 5% produce a false positive far more often than 5% of the time.",
     "Test statistics from G03/G04.", "blocked"),
    ("G07", "Calibration and proper scoring",
     "Forecasts are scored with Brier score and log loss against a stated baseline, and reliability is reported.",
     "A strategy can win bets and still be badly calibrated; proper scores expose that.",
     "Graded probability-outcome pairs.", "blocked"),
    ("G08", "Closing-line value",
     "Report the difference between the price taken and the closing price.",
     "Beating the close is the standard test that separates information from variance.",
     "Licensed closing prices.", "blocked"),
    ("G09", "Dependence handled, never assumed",
     "Every parlay and same-game combo price is built from a measured dependence. Independence is never an input.",
     "Assuming independence in a correlated combo misprices the joint event in one direction only.",
     "Paired licensed residual history for each leg pair.", "blocked"),
    ("G10", "Luck-separated skill statistic",
     "The lower bound of a slate-clustered 95% confidence interval on the skill statistic must exceed zero.",
     "A point estimate above zero is not evidence; the interval must exclude zero after clustering by slate.",
     "Graded selections with slate identifiers.", "blocked"),
    ("G11", "Market-integrity eligibility",
     "A market family tied to officiating or injuries, or knowable in advance or manipulable by one person, is permanently ineligible.",
     "Keeps the catalog inside the league's own integrity policy rather than testing the boundary.",
     "", "open"),
    ("G12", "Reproducibility",
     "One deterministic command rebuilds every table; seeds are fixed; all inputs are versioned in git.",
     "A result that cannot be recomputed cannot be audited, so it cannot count as evidence.",
     "", "open"),
]


def gate_rows() -> List[dict]:
    out = []
    for gid, name, rule, why, blocking, status in GATES:
        out.append({
            "gate_id": gid, "gate": name, "rule": rule,
            "how_it_removes_luck": why,
            "blocking_missing_input": blocking,
            "status": status,
            "official_or_method_reference": (
                PARTNERS_URL if gid == "G11" else
                TERMS_URL if gid == "G01" else
                "https://www.itl.nist.gov/div898/handbook/prc/section4/prc474.htm" if gid == "G06" else
                "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35f.htm"
            ),
        })
    return out


GATE_FIELDS = ["gate_id", "gate", "rule", "how_it_removes_luck",
               "blocking_missing_input", "status", "official_or_method_reference"]


# --------------------------------------------------------------------------
# 9. leaderboard (rewards are non-monetary research standing only)
# --------------------------------------------------------------------------
REWARD_TIERS = [
    ("Tier 3 - Preregistered", "All G01/G05/G11/G12 gates open and the rule frozen before any grading.",
     "Listed on the catalog page with its full rule; no performance claim.", 0),
    ("Tier 2 - Measurable", "G03 and G04 additionally open: at least 200 chronologically out-of-sample selections.",
     "Published Brier score, log loss and hit rate with intervals.", 0),
    ("Tier 1 - Skill-evidenced", "G06, G07 and G10 additionally open: Holm-corrected, calibrated, and the slate-clustered interval lower bound above zero.",
     "Top of the leaderboard and the only tier allowed to publish a skill statistic.", 0),
    ("Tier 0 - Price-evidenced", "G08 additionally open: positive closing-line value against licensed closes.",
     "Highest research standing; still non-monetary.", 0),
]


def leaderboard_rows() -> List[dict]:
    rows = []
    for i, (tier, requirement, reward, count) in enumerate(REWARD_TIERS, 1):
        rows.append({
            "tier_id": f"NFL3-T{i}", "tier": tier,
            "requirement": requirement, "reward": reward,
            "entries_at_this_tier": count,
            "monetary_value": "non-monetary: research standing and publication priority only",
            "official_or_method_reference": TERMS_URL,
        })
    _ = rows
    entries = []
    for s in strategy_rows():
        entries.append({
            "strategy_id": s["strategy_id"], "family": s["family"],
            "market": s["market"], "selections_graded": s["selections_graded"],
            "gates_open": "G01,G05,G11,G12",
            "gates_blocked": s["required_gates"].replace("G01,", "").replace(",G05", "").replace(",G11", "").replace(",G12", "").strip(","),
            "tier": "unqualified",
            "reward_awarded": "not_awarded",
            "status": s["status"],
            "official_source_url": s["official_source_url"],
        })
    return rows, entries


LEADERBOARD_TIER_FIELDS = ["tier_id", "tier", "requirement", "reward",
                           "entries_at_this_tier", "monetary_value",
                           "official_or_method_reference"]
LEADERBOARD_ENTRY_FIELDS = ["strategy_id", "family", "market", "selections_graded",
                            "gates_open", "gates_blocked", "tier",
                            "reward_awarded", "status", "official_source_url"]


# --------------------------------------------------------------------------
# 10. decision-readiness ledger
# --------------------------------------------------------------------------
# question_id, area, question, information_we_have, information_we_lack,
# decision_blocked, discovery_suggestion, priority, status, source
DECISIONS = [
    ("NFL3-Q01", "Data rights",
     "May this repository publish NFL-derived numbers at all?",
     "The NFL.com Terms (read 2026-11-13) state the Services may be used 'solely for your own individual non-commercial and informational purposes only' and that 'Systematic retrieval of data ... to create or compile ... a database ... is prohibited absent our express prior written consent.'",
     "A written licence, or written counsel opinion, covering republication of standings, schedule and injury-report data in a public web page.",
     "Whether any numeric NFL table on this site may be published in its current form.",
     "Take the one-page question to counsel: does quoting official standings/injury rows with attribution and no commercial use fall inside §1.3? Record the answer in COORDINATION.md before the next pack is merged.",
     "High", "unresolved", TERMS_URL),
    ("NFL3-Q02", "Market benchmark",
     "What price is a strategy actually compared against?",
     "The NFL's own release names DraftKings, FanDuel and Fanatics as 2026 official sportsbook partners and Genius Sports as the exclusive official betting-data distributor.",
     "A licensed archive of timestamped opening and closing prices, so that G02, G08 and G10 can be evaluated.",
     "Every performance gate: G02, G08, G10 and therefore the whole leaderboard.",
     "Decide between (a) buying a commercial odds archive, (b) restricting the project to no-price research, or (c) manual timestamped capture under a documented fair-use rationale. Nothing else can be graded until one is chosen.",
     "High", "unresolved", PARTNERS_URL),
    ("NFL3-Q03", "Line origination inputs",
     "Which inputs may the originated line use without importing an un-sourced coefficient?",
     "Verified points-for/against per game for all 32 clubs, plus the 14-game Week 10 slate; the model self-consistency check shows the model mean total differs from the league's own points-per-game by a computed amount (see the Lines page).",
     "A fitted home-field-advantage value, a shrinkage factor, and a victory-margin distribution - none of which any official page in this pack supplies.",
     "Publication of any moneyline probability, and therefore strategy NFL3-ST-03.",
     "Fit HFA, shrinkage and margin SD on a licensed multi-season results file, then re-run the builder. Until then the two parameters stay at their declared neutral values and the moneyline column stays blank.",
     "High", "unresolved", STANDINGS_URL),
    ("NFL3-Q04", "Injury data timing",
     "How stale is the official injury report, and when is it final?",
     "The Week 10 report read on 2026-11-13 publishes Player / Position / Injuries / Practice Status / Game Status. Designations were populated for 3 of 14 games; the other 11 clubs had Game Status blank.",
     "The publication cadence and the final-designation deadline, and a hash-stamped archive so a decision can be audited after the fact.",
     "Any claim that a depth deficiency was known before kickoff.",
     "Capture the injury page three times per week (Wednesday, Friday, Saturday) with a SHA-256 of the parsed table and an ET timestamp; only the latest pre-kickoff capture may be used to justify a deficiency flag.",
     "High", "unresolved", INJURY_URL),
    ("NFL3-Q05", "Standings freshness",
     "Which games does the official standings table actually include?",
     "A completed Thursday 12 November game (Commanders 24, Giants 21) is published on nfl.com/scores, but the standings table still shows both clubs with their pre-game 9-game records (WAS 3-5-1, NYG 5-3-1).",
     "An official statement of the standings refresh cadence.",
     "Any model that mixes standings-derived rates with already-played Week 10 results.",
     "Either lag all inputs to the standings snapshot date, or wait for the standings to refresh; never mix a standings-derived rate with a result the standings do not yet contain.",
     "High", "unresolved", SCORES_URL),
    ("NFL3-Q06", "Depth-chart authority",
     "Is a club depth chart an official statement of who will start?",
     "Both captured charts say so themselves: Patriots.com says the chart 'is unofficial and is published by the writers of Patriots.com'; the Lions chart is an 'Unofficial Depth Chart Compiled by Lions Football Communications'.",
     "An official NFL source that defines a starter, or a club-signed gameday designation.",
     "Whether a '2nd string will replace the starter' statement can be presented as fact.",
     "Publish every depth-derived row with the club's own caveat attached to the row, and treat the deficiency score as a proposed ranking, not a measured quantity.",
     "High", "unresolved", V.DEPTH_CHART_SOURCE["NE"]),
    ("NFL3-Q07", "Restricted markets",
     "Which prop families are off-limits before we even model them?",
     "The NFL release states partners will work together 'to prohibit wagers the league finds objectionable, including bets tied to officiating and injuries, along with those that can be knowable in advance or easily manipulated by a single person.'",
     "The operator-level list of which specific markets each partner actually restricts.",
     "Strategy eligibility: gate G11 rejects a family before any modelling happens.",
     "Keep G11 as a hard pre-filter and add the operator restriction lists when they are published; never model an injury-outcome market as a candidate.",
     "High", "unresolved", PARTNERS_URL),
    ("NFL3-Q08", "Combo dependence",
     "What is the measured dependence between two legs of a parlay or same-game combo?",
     "A method: paired residuals, Pearson/phi on a joint sample, slate-clustered interval, and a copula-free empirical joint. Eight correlations measured from official standings data are published on the Correlations page as a worked demonstration.",
     "Any measured dependence for an actual betting pair: no licensed paired residual history exists in the repo.",
     "Gates G07 and G09, and therefore every parlay and SGP strategy.",
     "Accumulate graded paired outcomes in the ledger first; compute rho only on a training window; never assume independence to make a price look better.",
     "High", "unresolved", STANDINGS_URL),
    ("NFL3-Q09", "Luck separation",
     "How do we know a result is skill rather than a short run of variance?",
     "A working demonstration: an OLS fit of win percentage on net points per game over the 32 official standings rows, with R-squared, slope interval and per-team residuals published.",
     "Graded selections with slate identifiers so the same statistic can be computed for a strategy rather than for a team.",
     "Gate G10 and every leaderboard tier above Tier 3.",
     "Reuse the same estimator on strategy residuals, clustered by slate, and require the interval lower bound to clear zero before any reward.",
     "High", "unresolved", STANDINGS_URL),
    ("NFL3-Q10", "Sample size",
     "How many graded selections before a number is publishable?",
     "A declared floor (200 per family) and the reason for it: with ten strategies each tested, an uncorrected threshold produces false positives far more often than the nominal rate.",
     "Any graded selection at all: the ledger is empty.",
     "Gates G03, G04, G06, G07 and G10.",
     "Start the ledger with paper-graded (unbet) selections; the floor is about statistical power, not about money, so it can be met without placing a wager.",
     "Medium", "unresolved", "https://www.itl.nist.gov/div898/handbook/prc/section4/prc474.htm"),
    ("NFL3-Q11", "Roster rules",
     "What constrains how many players can actually be active?",
     "The NFL Operations CBA summary states the gameday active list rises to 48 (from 46) and that teams must have at least eight offensive linemen; the 14-team playoff format is also stated there.",
     "2026 practice-squad elevation counts and injured-reserve return counts, which are not on that page.",
     "The roster-availability sanity check inside the depth model.",
     "Add the current-season roster rules page when captured; until then, treat the 48-player figure as the only sourced constraint.",
     "Medium", "unresolved", CBA_URL),
    ("NFL3-Q12", "Rule changes",
     "Do 2026 rule changes affect any market we model?",
     "The 2026 rulebook page lists the 2026 changes including 6-1-6, which permits the kicking team to declare an onside kick at any time during the game.",
     "The full text of each changed rule, and any official scoring or timing interpretation.",
     "Any total or special-teams market that a rule change could move.",
     "Read the specific changed rules before modelling totals, and record which market families each change touches.",
     "Medium", "unresolved", RULEBOOK_URL),
    ("NFL3-Q13", "Site architecture",
     "Which NFL pack is the canonical one?",
     "Four independent NFL dashboards are now published from this repository: docs/nfl/, docs/nfl-3b81013c/, docs/nfl-origination/ and this one.",
     "An owner decision naming one canonical pack per question.",
     "Which table a reviewer should trust when two packs answer the same question differently.",
     "Pick a canonical pack per question and mark the others 'Archived provenance' with a banner. Do not delete: each carries its own source register.",
     "High", "unresolved", "https://github.com/sassnarep3-star/Own6/tree/main/docs"),
    ("NFL3-Q14", "Broken references",
     "Which published source links no longer resolve?",
     "nfl.com/official-nfl-rules/ returns the official NFL 404 page when fetched on 2026-11-13. It is cited by 71 rows across 20+ files in this repository, including live published pages.",
     "An owner decision to repoint or withdraw each citation.",
     "Whether any row citing that URL can be treated as verified.",
     "Repoint every citation to operations.nfl.com/rules-officiating/2026-nfl-rulebook, or to the specific rule section, and re-run the source checkers.",
     "High", "unresolved", RULEBOOK_URL),
    ("NFL3-Q15", "Live URL correctness",
     "Does the URL printed in the README actually load?",
     "GitHub Pages is served from main:/, so docs/nfl/ is live at /docs/nfl/. The README's https://sassnarep3-star.github.io/Own6/nfl/ returns GitHub's 404 page.",
     "An owner edit to the README and to the older handoff notes.",
     "A reader following the README link lands on a 404.",
     "Change every /nfl/ link to /docs/nfl/ and re-check after the next Pages build.",
     "Medium", "unresolved", "https://github.com/sassnarep3-star/Own6/edit/main/README.md"),
    ("NFL3-Q16", "Rewards",
     "What does 'top performing strategy' actually earn?",
     "A four-tier ladder whose rewards are research standing and publication priority only; no monetary prize is offered and none may be offered while the terms restrict commercial use.",
     "An owner decision on whether any non-monetary reward beyond publication priority is wanted.",
     "How the leaderboard is described to contributors.",
     "Keep rewards non-monetary and state that explicitly on the leaderboard page, as it is now.",
     "Low", "resolved", TERMS_URL),
]


def decision_rows() -> List[dict]:
    out = []
    for (qid, area, q, have, lack, blocked, discover, prio, status, url) in DECISIONS:
        out.append({
            "question_id": qid, "decision_area": area, "question": q,
            "information_we_have": have, "information_we_lack": lack,
            "decision_it_blocks": blocked,
            "suggested_way_to_discover": discover,
            "priority": prio, "status": status,
            "official_source_url": url,
        })
    return out


DECISION_FIELDS = ["question_id", "decision_area", "question", "information_we_have",
                   "information_we_lack", "decision_it_blocks",
                   "suggested_way_to_discover", "priority", "status",
                   "official_source_url"]


# --------------------------------------------------------------------------
# 11. site-improvement suggestions (review only - nothing auto-applied)
# --------------------------------------------------------------------------
# sug_id, area, title, current_state, problem, option_paths, recommended,
# prerequisites, effort, review_status, source
SUGGESTIONS = [
    ("NFL3-SUG-01", "Site architecture",
     "Replace the NBA-only root redirect with a neutral multi-domain portal",
     "Root index.html is a meta-refresh that sends every visitor to docs/assurance/, an NBA-only dashboard.",
     "A decision-maker opening the live root never sees the NFL or SF-94122 work and may mistake the NBA '0 observations' cards for the state of the whole project.",
     "Path A: neutral root selector (NBA | NFL | SF 94122). Path B: keep the redirect and add a global domain switcher. Path C: split into one repository per domain.",
     "Path A - neutral selector page",
     "Sign-off after the concurrent Arena sessions stop merging, so the root file has no conflict.",
     "Low (1 file) - fully reversible", "pending_human_choice",
     "https://github.com/sassnarep3-star/Own6/blob/main/index.html"),
    ("NFL3-SUG-02", "Duplicate packs",
     "Name one canonical NFL pack and archive the others",
     "docs/nfl/, docs/nfl-3b81013c/, docs/nfl-origination/ and now docs/nfl-309921cc/ each answer overlapping questions with different evidence standards.",
     "A reviewer can act on an older or less complete checklist without realising a newer one exists.",
     "Path A: keep all, add an 'Archived provenance' banner and a canonical pointer. Path B: merge the best tables into one hub. Path C: delete the superseded packs.",
     "Path A now, Path B later; never Path C while each pack holds its own source register.",
     "Compare flagged-item coverage and strictness across the four packs first.",
     "Low - non-destructive and reversible", "pending_human_choice",
     "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"),
    ("NFL3-SUG-03", "Broken sources",
     "Repoint every citation of the dead nfl.com/official-nfl-rules/ URL",
     "71 rows across 20+ files, including live published pages, cite that URL; it returned the official NFL 404 page on 2026-11-13.",
     "A row whose supporting link is a 404 cannot be treated as verified, yet it is currently presented as sourced.",
     "Path A: repoint all to operations.nfl.com/rules-officiating/2026-nfl-rulebook. Path B: repoint to the specific rule section each row relies on. Path C: leave and mark unverified.",
     "Path B where the specific section is known, otherwise Path A.",
     "Owner edit of data/nfl/sources.csv and a rebuild of docs/nfl/.",
     "Medium - touches another session's files, so log the request first",
     "pending_human_choice", RULEBOOK_URL),
    ("NFL3-SUG-04", "Documentation accuracy",
     "Correct the live URLs printed in the README",
     "The README publishes https://sassnarep3-star.github.io/Own6/nfl/, which returns GitHub's 404; Pages is served from main:/ so the live path is /docs/nfl/.",
     "The first link a reader follows from the repository is dead.",
     "Path A: edit the README. Path B: add a redirect page at docs/nfl-legacy/. Path C: change the Pages source.",
     "Path A", "Owner edit; no other file needs to change.",
     "Low - reversible", "pending_human_choice",
     "https://github.com/sassnarep3-star/Own6/edit/main/README.md"),
    ("NFL3-SUG-05", "Data freshness",
     "Stamp every official capture with a UTC timestamp and a content hash",
     "Captures are dated by session day only; nothing records what the page looked like at capture time.",
     "Two packs captured hours apart can disagree, and there is no way to tell which reflects the newer page.",
     "Path A: write a SHA-256 of the parsed table to a metadata file per capture. Path B: store the raw parsed text. Path C: rely on the session date.",
     "Path A, with Path B for the injury report because designations change intraday.",
     "Decide a capture cadence (the injury report changes three times a week).",
     "Medium - reversible, but must be applied to new captures only",
     "pending_human_choice", INJURY_URL),
    ("NFL3-SUG-06", "Standings lag",
     "Either lag all inputs to the standings snapshot or wait for the refresh",
     "The standings table read on 2026-11-13 does not yet include the completed Thursday 12 November game.",
     "Mixing a standings-derived rate with a result the standings do not contain silently double-counts or omits a game.",
     "Path A: refuse to model any game already played. Path B: adjust the standings by hand. Path C: ignore the discrepancy.",
     "Path A - reject already-played games at build time.",
     "A build-time check comparing the standings snapshot date with the slate dates.",
     "Low - reversible", "pending_human_choice", SCORES_URL),
    ("NFL3-SUG-07", "Depth-chart status",
     "Show the club's own 'unofficial' caveat on every depth-derived row",
     "Both captured charts state they are unofficial and reflect writers' opinions, not the organisation's.",
     "A reader can read '2nd string will replace the starter' as an official fact when the source explicitly disclaims it.",
     "Path A: carry the caveat text into the row. Path B: a page-level banner only. Path C: drop depth charts entirely.",
     "Path A - caveat on the row, banner on the page.",
     "Nothing; already implemented in this pack.",
     "Low - reversible", "pending_human_choice", V.DEPTH_CHART_SOURCE["NE"]),
    ("NFL3-SUG-08", "Correlation honesty",
     "Label proposed thresholds and measured values differently, everywhere",
     "Elsewhere in the repo, expected signs, minimum-sample floors and depth thresholds are published in value columns without saying they are design choices.",
     "A proposed threshold in a value column reads like an observed measurement.",
     "Path A: a required 'value_kind' column on every table. Path B: a page-level legend. Path C: leave as is.",
     "Path A - every row states measured, model output, proposed, or unverified.",
     "Nothing; already implemented in this pack.",
     "Low - reversible", "pending_human_choice", STANDINGS_URL),
    ("NFL3-SUG-09", "Coordination file",
     "Split COORDINATION.md into a task board and an append-only archive",
     "COORDINATION.md is roughly 194 KB of append-only session history, with the live task board buried above it.",
     "A session claiming a task must read a very large file to find out what is already claimed, which raises the chance of duplicate work.",
     "Path A: keep COORDINATION.md as the board and move history to COORDINATION_HISTORY.md. Path B: one file per session in a directory. Path C: leave as is.",
     "Path A - board stays at the top of COORDINATION.md; older sections move to an archive file.",
     "Every active session must agree to the split before it happens.",
     "Low - reversible, but it is a shared file", "pending_human_choice",
     "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"),
    ("NFL3-SUG-10", "Merge safety",
     "Stop concurrent branches editing the same derived inventories",
     "Open PR #68 and PR #72 both modify data/assurance/*, data/source_coverage/* and audit/SOURCE_COVERAGE.md, which are regenerated build outputs.",
     "Every integration session must resolve the same conflicts in generated files, and a stale hash can fail CI for unrelated reasons.",
     "Path A: mark generated inventories as build artifacts and exclude them from PR diffs. Path B: regenerate only in the final integration run. Path C: leave as is.",
     "Path B - regenerate derived inventories only in the final integration, never in a feature branch.",
     "Agreement from the owners of the two open PRs.",
     "Medium - reversible", "pending_human_choice",
     "https://github.com/sassnarep3-star/Own6/pull/68"),
    ("NFL3-SUG-11", "Evidence ledger",
     "Publish a single 'what we cannot show' table per domain",
     "Each pack has its own flagged page; a reader must open four pages to learn what is missing.",
     "The most important content - what is unknown - is the hardest to find.",
     "Path A: one consolidated evidence-gap page per domain. Path B: keep per-pack flagged pages. Path C: a machine-readable gaps file.",
     "Path C plus Path A - a gaps CSV rendered as one page.",
     "A canonical pack decision (see NFL3-SUG-02).",
     "Low - reversible", "pending_human_choice", TERMS_URL),
    ("NFL3-SUG-12", "Rights gate",
     "Put the rights question first, before any further numeric capture",
     "The NFL.com terms prohibit systematic retrieval to compile a database without written consent; this repository is, by construction, a compiled database of official NFL tables.",
     "Continuing to add official tables increases exposure while the question is unanswered.",
     "Path A: pause numeric capture pending counsel. Path B: keep capturing but reduce to what a human reader could verify in one page view. Path C: continue unchanged.",
     "Path A for the decision, Path B as an interim operating rule.",
     "A written answer to NFL3-Q01.",
     "High impact if adopted - reversible only by deleting captured data",
     "pending_human_choice", TERMS_URL),
    ("NFL3-SUG-13", "Verification automation",
     "Make the source-link checker also probe for HTTP errors, not just shape",
     "Existing checkers validate that a row has an https link and that internal links resolve; they do not fetch the link.",
     "A 404 in a source column passes every current check, which is how 71 dead citations survived to publication.",
     "Path A: a nightly workflow that HEADs every distinct source URL. Path B: check links at build time. Path C: manual review.",
     "Path A - nightly HEAD check with a per-URL pass/fail table.",
     "Agreement on which workflow owns it, to avoid duplicate CI.",
     "Medium - reversible", "pending_human_choice",
     "https://github.com/sassnarep3-star/Own6/tree/main/.github/workflows"),
    ("NFL3-SUG-14", "Leaderboard rewards",
     "Keep rewards non-monetary and say so on the page",
     "The four-tier ladder awards publication priority and research standing only.",
     "Any hint of a prize would conflict with the non-commercial-use restriction in the terms.",
     "Path A: keep non-monetary and label it. Path B: offer a monetary prize. Path C: remove the ladder.",
     "Path A", "Nothing; already stated on the leaderboard page.",
     "None - already in place", "pending_human_choice", TERMS_URL),
]


def suggestion_rows() -> List[dict]:
    out = []
    for (sid, area, title, current, problem, paths, rec, pre, effort, status,
         url) in SUGGESTIONS:
        out.append({
            "suggestion_id": sid, "area": area, "title": title,
            "current_repo_state": current, "decision_problem_solved": problem,
            "option_paths_for_review": paths, "recommended_path": rec,
            "prerequisites_before_implementing": pre,
            "effort_and_reversibility": effort,
            "review_status": status,
            "official_source_url": url,
        })
    return out


SUGGESTION_FIELDS = ["suggestion_id", "area", "title", "current_repo_state",
                     "decision_problem_solved", "option_paths_for_review",
                     "recommended_path", "prerequisites_before_implementing",
                     "effort_and_reversibility", "review_status",
                     "official_source_url"]


# --------------------------------------------------------------------------
# 12. repository review findings (line-by-line, verified this session)
# --------------------------------------------------------------------------
# finding_id, area, finding, evidence, impact, files_affected, severity, source
REPO_FINDINGS = [
    ("NFL3-RF-01", "Site navigation",
     "The repository root is a hard redirect to an NBA-only dashboard",
     "Root index.html contains a meta refresh to docs/assurance/ and a canonical link to the same path; it renders no content of its own.",
     "Every other domain in the repository - NFL, SF 94122, rentals - is invisible to anyone who opens the live root URL.",
     "index.html", "Medium",
     "https://github.com/sassnarep3-star/Own6/blob/main/index.html"),
    ("NFL3-RF-02", "Duplication",
     "Four independent NFL dashboards are published from one repository",
     "docs/nfl/ (session efebf74f), docs/nfl-3b81013c/ (session 3b81013c), docs/nfl-origination/ (session 8132a3b1) and docs/nfl-309921cc/ (this session) are all live under the same Pages site.",
     "Overlapping answers to the same questions, with different evidence standards and no canonical pointer.",
     "docs/nfl/, docs/nfl-3b81013c/, docs/nfl-origination/, docs/nfl-309921cc/",
     "High", "https://github.com/sassnarep3-star/Own6/tree/main/docs"),
    ("NFL3-RF-03", "Broken source link",
     "A dead nfl.com rules URL is cited 71 times, including on live pages",
     "Fetching https://www.nfl.com/official-nfl-rules/ on 2026-11-13 returned the official NFL 404 page ('404 - Flag on the Play.'). A repository-wide grep counts 71 occurrences across 20+ files, including docs/nfl/index.html, docs/nfl/strategies.html and docs/nfl/sources.html.",
     "Rows that cite it cannot be treated as verified, yet they are published as sourced.",
     "data/nfl/sources.csv, data/nfl/requirements.csv, data/nfl/origin_strategies.csv, data/nfl/decision_questions.csv, data/nfl/injury_tracking.csv, data/nfl/depth_model.csv, data/nfl/correlations.csv, docs/nfl/*.html, data/assurance/row_audit.csv, data/source_coverage/rows.csv, audit/NFL_AUDIT.md, COORDINATION.md",
     "High", "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"),
    ("NFL3-RF-04", "Incorrect live URL",
     "The README publishes a 404 Pages URL",
     "README.md line 97 prints https://sassnarep3-star.github.io/Own6/nfl/. Fetching it on 2026-11-13 returned GitHub's 'Unicorn' 404 page. GitHub Pages for this repository is served from main:/, so the same content is live at /docs/nfl/.",
     "The first link a reader follows from the repository is dead.",
     "README.md", "Medium",
     "https://sassnarep3-star.github.io/Own6/docs/nfl/"),
    ("NFL3-RF-05", "Source-scope mismatch",
     "A subscription terms page is cited as the general NFL terms",
     "https://www.nfl.com/terms/ redirects to https://www.nfl.com/legal/subscriptions_terms, which scopes itself to subscription, authentication and mobile products. The general page is https://www.nfl.com/legal/terms/ (updated May 16, 2024).",
     "A rights argument built on the subscription terms may not cover the pages actually being quoted.",
     "data/nfl/sources.csv, data/nfl/requirements.csv, data/nfl/decision_questions.csv, data/nfl/validation_gates.csv, data/nfl/flagged.csv, docs/nfl/flagged.html",
     "Medium", "https://www.nfl.com/legal/terms/"),
    ("NFL3-RF-06", "Unreadable source",
     "A linked injury-policy PDF returned no readable content",
     "https://operations.nfl.com/media/2683/2017-nfl-injury-report-policy.pdf is cited as verified on docs/nfl/index.html; a prior session recorded that it returned empty parsed content.",
     "A source that cannot be read cannot verify the claims attached to it.",
     "docs/nfl/index.html, data/nfl/sources.csv, data/nfl/injury_tracking.csv",
     "Medium", "https://www.nfl.com/injuries/"),
    ("NFL3-RF-07", "Evidence labelling",
     "Proposed thresholds are published in value columns elsewhere in the repository",
     "Expected signs in data/nfl/correlations.csv, floors such as 200 observations / 60 slates, and depth thresholds such as >0.5 / >0.6 are design choices, but they appear as values rather than as labelled proposals.",
     "A design hypothesis reads like a measurement.",
     "data/nfl/correlations.csv, data/nfl/validation_gates.csv, data/nfl/depth_model.csv",
     "Medium", "https://github.com/sassnarep3-star/Own6/tree/main/data/nfl"),
    ("NFL3-RF-08", "Data freshness",
     "The official standings table lags a completed game",
     "nfl.com/scores shows Thursday 12 November Commanders 24, Giants 21 as Final, while nfl.com/standings still lists WAS 3-5-1 and NYG 5-3-1, both pre-game 9-game records.",
     "A model that mixes standings rates with completed Week 10 results is internally inconsistent.",
     "docs/nfl/, docs/nfl-origination/, any pack using standings-derived rates",
     "High", "https://www.nfl.com/scores/"),
    ("NFL3-RF-09", "Column provenance",
     "The standings table renders two columns its own legend does not define",
     "The NFL.com standings LEGEND defines W, L, T, PCT, HOME, ROAD, DIV, CONF, PF, PA, NET PTS and STRK. The rendered row carries two further unlabelled record/percentage columns.",
     "Capturing them would require guessing their meaning, which this pack refuses to do; they are omitted and flagged.",
     "data/nfl_309921cc/standings_2026_w10.csv", "Low",
     "https://www.nfl.com/standings/"),
    ("NFL3-RF-10", "Unreadable table headers",
     "The official team-stats tables rendered without readable column headers",
     "Fetching https://www.nfl.com/stats/team-stats/ returned 32 data rows per table but no header row in the parsed output, so no statistic can be attributed to a column with confidence.",
     "Useful official statistics exist but cannot be reproduced here without guessing which number is which.",
     "data/nfl_309921cc/sources.csv (row NFL3-S11)", "Medium",
     "https://www.nfl.com/stats/team-stats/"),
    ("NFL3-RF-11", "Concurrency",
     "Two open pull requests edit the same generated inventories",
     "PR #68 (arena/34dacba5-own6) and PR #72 (arena/3b81013c-own6) both modify data/assurance/inventory.csv, data/assurance/summary.json, data/source_coverage/pages.csv, data/source_coverage/rows.csv, data/source_coverage/summary.json and audit/SOURCE_COVERAGE.md.",
     "Every integration session re-resolves the same conflicts in build outputs, and a stale hash can fail CI for unrelated reasons.",
     "data/assurance/*, data/source_coverage/*, audit/SOURCE_COVERAGE.md",
     "Medium", "https://github.com/sassnarep3-star/Own6/pull/68"),
    ("NFL3-RF-12", "Coordination file size",
     "The shared task board is buried in roughly 194 KB of append-only history",
     "COORDINATION.md is 194,096 bytes; the live task board sits above many past session sections.",
     "A session must read a very large file to see what is already claimed, raising the chance of duplicated work.",
     "COORDINATION.md", "Low",
     "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"),
    ("NFL3-RF-13", "Verification coverage",
     "Source checkers validate link shape, not link liveness",
     "scripts/check_nfl.py, scripts/check_nfl_origination.py and scripts/check_site.py assert that a row carries an https link and that internal links resolve; none of them fetch the external URL.",
     "A dead external link passes every current gate, which is how 71 citations of a 404 URL reached publication.",
     "scripts/check_nfl.py, scripts/check_nfl_origination.py, scripts/check_site.py",
     "High", "https://github.com/sassnarep3-star/Own6/tree/main/scripts"),
    ("NFL3-RF-14", "Data rights",
     "The repository is, by construction, a compiled database of official NFL tables",
     "NFL.com Terms §1.3 (read 2026-11-13) prohibits systematic retrieval of content 'to create or compile, directly or indirectly, a collection, compilation, database, or directory' without express prior written consent, while permitting individual non-commercial informational use.",
     "The rights question applies to the whole repository, not to any single pack, and is currently unanswered.",
     "All data/nfl*/ directories and all published NFL pages",
     "High", "https://www.nfl.com/legal/terms/"),
]


def repo_finding_rows() -> List[dict]:
    return [{
        "finding_id": fid, "area": area, "finding": finding, "evidence": evidence,
        "impact": impact, "files_affected": files, "severity": sev,
        "review_status": "needs review",
        "official_or_repo_source_url": url,
    } for (fid, area, finding, evidence, impact, files, sev, url) in REPO_FINDINGS]


REPO_FINDING_FIELDS = ["finding_id", "area", "finding", "evidence", "impact",
                       "files_affected", "severity", "review_status",
                       "official_or_repo_source_url"]


# --------------------------------------------------------------------------
# 13. source register
# --------------------------------------------------------------------------
def source_rows() -> List[dict]:
    return [{
        "source_id": sid, "publisher": pub, "title": title,
        "official_source_url": url, "verified_date": date,
        "retrieval_method": method, "verification_status": status,
        "verbatim_evidence_excerpt": excerpt,
        "supports_claim": supports,
        "does_not_support_boundary": boundary,
    } for (sid, pub, title, url, date, method, status, excerpt, supports,
           boundary) in V.SOURCES]


SOURCE_FIELDS = ["source_id", "publisher", "title", "official_source_url",
                 "verified_date", "retrieval_method", "verification_status",
                 "verbatim_evidence_excerpt", "supports_claim",
                 "does_not_support_boundary"]


# --------------------------------------------------------------------------
# 14. flagged for review
# --------------------------------------------------------------------------
# flag_id, area, item, what_is_blank_or_unresolved, why, source, severity
FLAGS = [
    ("NFL3-F01", "Rights", "Commercial use and database compilation",
     "No licence or counsel opinion is on file.",
     "NFL.com Terms §1.3 permits individual non-commercial informational use and prohibits systematic retrieval to compile a database without express prior written consent.",
     TERMS_URL, "High"),
    ("NFL3-F02", "Standings", "Two standings columns omitted",
     "The two unlabelled record/percentage columns rendered by the NFL standings table are not captured.",
     "The page LEGEND does not define them; capturing them would require guessing.",
     STANDINGS_URL, "Low"),
    ("NFL3-F03", "Team statistics", "No team-statistic value is reproduced",
     "Every offensive/defensive team statistic is blank.",
     "The official team-stats tables rendered without readable column headers, so no number can be attributed to a statistic with confidence.",
     TEAMSTATS_URL, "Medium"),
    ("NFL3-F04", "Depth charts", "Club depth charts are unofficial",
     "Every depth-derived row carries the club's own disclaimer.",
     "Patriots.com says the chart 'is unofficial and is published by the writers of Patriots.com'; the Lions chart is 'Unofficial ... Compiled by Lions Football Communications'.",
     V.DEPTH_CHART_SOURCE["NE"], "High"),
    ("NFL3-F05", "Standings", "Standings lag a completed game",
     "The Thursday 12 November result is not reflected in the standings used as model input.",
     "nfl.com/scores shows the game Final while nfl.com/standings still shows both clubs with pre-game records.",
     SCORES_URL, "High"),
    ("NFL3-F06", "Line origination", "Two model parameters are declared, not fitted",
     "Home-field advantage is 0.00 points and shrinkage is 1.00.",
     "Neither value has an official source; both are neutral placeholders that must be fitted on licensed history before the lines can be validated.",
     STANDINGS_URL, "High"),
    ("NFL3-F07", "Depth model", "Deficiency weights are proposed, not observed",
     "All deficiency scores are labelled 'proposed_weight_not_observed'.",
     "No official source defines how much a 2nd or 3rd string replacement weakens a unit; the weights are a design hypothesis.",
     V.DEPTH_CHART_SOURCE["NE"], "High"),
    ("NFL3-F08", "Moneyline", "No moneyline probability is published",
     "The originated moneyline column is blank for every game.",
     "Converting a point margin to a win probability needs a margin-distribution parameter; no official page in this pack supplies one.",
     STANDINGS_URL, "High"),
    ("NFL3-F09", "Combos", "No measured dependence for any betting pair",
     "Every parlay and same-game-combo correlation cell is blank.",
     "Measuring a dependence needs graded paired outcomes under licence; the ledger is empty.",
     STANDINGS_URL, "High"),
    ("NFL3-F10", "Market prices", "No market or closing price is held",
     "Market spread, market total and closing-line value are blank for all 14 games.",
     "No licensed price archive is configured, so gate G02 stays closed.",
     PARTNERS_URL, "High"),
    ("NFL3-F11", "Injury report", "Most Game Status cells were blank at capture",
     "11 of 14 games had no Out/Questionable/Doubtful designations published.",
     "The report is populated progressively through the week; the capture is a Friday snapshot and later designations will differ.",
     INJURY_URL, "Medium"),
    ("NFL3-F12", "Injury report", "Injury column is blank for most rows",
     "The 'Injuries' cell is empty for the majority of listed players.",
     "The official page leaves it blank; no injury description is inferred.",
     INJURY_URL, "Low"),
    ("NFL3-F13", "Cross-check", "Designated players missing from their club chart",
     "Designated players who do not appear anywhere on their club's depth chart are listed separately.",
     "A designation without a chart position cannot be mapped to a replacement string.",
     INJURY_URL, "Medium"),
    ("NFL3-F14", "Repo", "Concurrency on generated inventories",
     "Two open pull requests edit the same build outputs.",
     "PR #68 and PR #72 both modify data/assurance/*, data/source_coverage/* and audit/SOURCE_COVERAGE.md.",
     "https://github.com/sassnarep3-star/Own6/pull/68", "Medium"),
    ("NFL3-F15", "Repo", "Dead rules URL cited across the repository",
     "71 citations of nfl.com/official-nfl-rules/, which returned a 404 on 2026-11-13.",
     "A link that does not resolve cannot support a verified row; the fix belongs to the owning session.",
     RULEBOOK_URL, "High"),
    ("NFL3-F16", "Repo", "README publishes a 404 Pages URL",
     "https://sassnarep3-star.github.io/Own6/nfl/ returned GitHub's 404 page.",
     "Pages is served from main:/, so the live path is /docs/nfl/; the fix belongs to the owning session.",
     "https://github.com/sassnarep3-star/Own6/edit/main/README.md", "Medium"),
]


def flag_rows() -> List[dict]:
    return [{
        "flag_id": fid, "area": area, "item": item, "what_is_blank": blank,
        "why": why, "official_source_url": url, "severity": sev,
        "review_status": "needs review",
    } for (fid, area, item, blank, why, url, sev) in FLAGS]


FLAG_FIELDS = ["flag_id", "area", "item", "what_is_blank", "why",
               "official_source_url", "severity", "review_status"]


# --------------------------------------------------------------------------
# 15. CSV writing
# --------------------------------------------------------------------------
def write_csv(name: str, fields: Sequence[str], rows: Sequence[dict]) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(fields), extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    return path
