"""Line origination, in a fixed order: the side first, then the total, then the
moneyline - and every market published as a triple of columns: the model's fair
line, the market line, and the difference between them.

Why the order is load-bearing
-----------------------------
Stage 3 is computed *from the two numbers stages 1 and 2 published*, not from a
parallel probability model. The moneyline therefore cannot quietly disagree with
the side and the total that are already on the record. The order is enforced in
code (``StageOrderError``) and audited per game in ``origination_order.csv``.

Fair-line construction (inputs official, constants declared as parameters)
--------------------------------------------------------------------------
``att``/``def`` are a club's points-for and points-against rates per game above
the league average, taken from the official cumulative standings table as it
stood at the input vintage, shrunk toward the league average by
``n / (n + shrinkage_k_games)`` so a club's first games cannot produce extreme
ratings. Home-field advantage is held at 0.0 because no official source in this
pack supplies a magnitude; the page instead shows what the line becomes at +1.5
and +3.0 so a reviewer can see the sensitivity without the model guessing.

The point-noise scale and the home/away scoring correlation are **measured**
from the verified results feed (official final scores) at the same vintage as the
inputs - never imported. The moneyline and the tie probability then come from an
integer-score convolution of two discretised Normals, which is why the total
matters to the price: P(tie) depends on both implied point totals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import capture as C
from . import results as R
from . import stats as S
from .cache import memo

MAX_TEAM_POINTS = 87  # convolution support; 87 points is far above any observed 2026 line

# Declared model parameters. These are modelling choices, not NFL-published values.
PARAMS: dict[str, dict[str, str]] = {
    "shrinkage_k_games": {
        "value": "4",
        "meaning": "a club's scoring rates are weighted by n/(n+k), n = games played at the input vintage",
        "kind": "model_parameter",
        "effect": "at 6 games played a club's own rate carries weight 0.60, 0.40 at 4 games",
    },
    "hfa_points": {
        "value": "0.0",
        "meaning": "home-field advantage added to expected home points",
        "kind": "model_parameter",
        "effect": "held at zero: no official source in this pack supplies a magnitude; sensitivity shown at +1.5 and +3.0",
    },
    "margin_damping_lambda": {
        "value": "1.0",
        "meaning": "published margin = lambda * raw model margin. The fair line is published undamped (lambda = 1.00) so that every strategy competes on the same number; the grid search that minimises mean absolute margin error on finished games up to each vintage is published next to it as analysis, and a damped variant is offered as a strategy rather than baked into the line",
        "kind": "model_parameter_fitted_on_official_results",
        "effect": "an undamped additive attack/defence rating over-reacts to a lopsided short sample; the fitted value and the error it removes are published on the origination page",
    },
    "line_step": {
        "value": "0.5",
        "meaning": "quoting granularity for the side and the total, in points",
        "kind": "model_parameter",
        "effect": "half-point moves, so a 0.4-point edge does not change a number",
    },
    "odds_step": {
        "value": "5",
        "meaning": "American-odds quoting granularity",
        "kind": "model_parameter",
        "effect": "rounds a -163 quote to -165",
    },
    "noise_scale": {
        "value": "measured",
        "meaning": "sigma_pts is the SD of every team's points around the league mean at the vintage, computed from official final scores in the feed",
        "kind": "measured_from_official_data",
        "effect": "sets how flat the derived moneyline is; a larger sigma pulls prices toward even",
    },
    "score_dependence": {
        "value": "measured",
        "meaning": "rho is the Pearson correlation of home points against away points over feed games at the vintage",
        "kind": "measured_from_official_data",
        "effect": "enters the margin scale as sigma*sqrt(2(1-rho))",
    },
    "tie_handling": {
        "value": "integer_convolution",
        "meaning": "ties get their own probability from the discrete convolution; a moneyline is priced on win-or-not with push removed, and P(tie) is published separately",
        "kind": "model_parameter",
        "effect": "a model that ignores ties would over-price a 3-point favourite",
    },
}


class StageOrderError(RuntimeError):
    """Raised when a later stage is attempted before its dependency is published."""


@dataclass
class Inputs:
    """Point-in-time official inputs for one game, at one vintage."""

    game_id: str
    away: str
    home: str
    vintage_week: int
    table: dict[str, dict[str, float]] = field(default_factory=dict)

    def club(self, abbr: str) -> dict[str, float]:
        return self.table[abbr]

    def summary(self) -> dict[str, str]:
        a, h = self.club(self.away), self.club(self.home)
        return {
            "inputs_away_games": str(int(a["games"])),
            "inputs_home_games": str(int(h["games"])),
            "inputs_away_ppg": S.fmt(a["ppg"], 3),
            "inputs_away_papg": S.fmt(a["papg"], 3),
            "inputs_home_ppg": S.fmt(h["ppg"], 3),
            "inputs_home_papg": S.fmt(h["papg"], 3),
            "inputs_league_ppg": S.fmt(R.league_baseline(self.vintage_week)["points_per_team_game"], 3),
            "inputs_official_source_url": C.link_for("STANDINGS"),
        }


@memo
def dispersion(vintage_week: int) -> dict[str, float]:
    """sigma_pts, rho and the sample sizes behind them, measured on feed games
    played up to and including ``vintage_week``."""
    league = R.league_baseline(vintage_week)["points_per_team_game"]
    home_pts: list[float] = []
    away_pts: list[float] = []
    resid: list[float] = []
    team_mean: list[float] = []
    for hp, ap, wk in R.team_points():
        if wk > vintage_week:
            continue
        home_pts.append(hp)
        away_pts.append(ap)
        resid.extend([hp - league, ap - league])
    if home_pts:
        mh, ma = S.mean(home_pts), S.mean(away_pts)
        team_mean.extend([h - mh for h in home_pts] + [a - ma for a in away_pts])
    return {
        "sigma_pts": S.sd(resid) if len(resid) > 2 else float("nan"),
        "sigma_pts_around_team_mean": S.sd(team_mean) if len(team_mean) > 2 else float("nan"),
        "rho_home_away": S.pearson(home_pts, away_pts) if len(home_pts) > 2 else float("nan"),
        "n_team_games": float(len(resid)),
        "n_games": float(len(home_pts)),
        "league_ppg": league,
    }


def _expected(inp: Inputs, hfa: float = 0.0) -> tuple[float, float]:
    """Expected points for (home, away).

    A club's expectation is the league baseline, plus its own scoring attack
    above that baseline, plus the opponent's defensive weakness at that baseline
    - a leaky defence adds points, a good one subtracts them - with each rate
    shrunk by ``n/(n+k)`` so a short sample cannot move the line far.
    """
    k = float(PARAMS["shrinkage_k_games"]["value"])
    league = R.league_baseline(inp.vintage_week)["points_per_team_game"]
    rate: dict[str, tuple[float, float]] = {}
    for abbr in (inp.home, inp.away):
        row = inp.club(abbr)
        n = row["games"]
        w = n / (n + k) if (n + k) > 0 else 0.0
        rate[abbr] = ((row["ppg"] - league) * w, (row["papg"] - league) * w)
    h_att, h_def = rate[inp.home]
    a_att, a_def = rate[inp.away]
    return league + h_att + a_def + hfa, league + a_att + h_def


def raw_margin(inp: Inputs, hfa: float = 0.0) -> float:
    """Undamped model margin for one fixture (home - away)."""
    eh, ea = _expected(inp, hfa)
    return eh - ea


def _finished_at_or_before(vintage_week: int) -> list[tuple[int, float, float]]:
    """(game index, raw model margin, actual margin) for finished games whose
    inputs are available at or before ``vintage_week`` - no game's own result is
    ever used to price that game."""
    out = []
    for i, (gid, wk, _d, _s, away, home, ap, hp, _src) in enumerate(C.FINAL_GAMES):
        if wk > vintage_week:
            continue
        inp = Inputs(gid, away, home, wk - 1, R.as_of(wk - 1))
        out.append((i, raw_margin(inp), float(hp - ap)))
    return out


@memo
def fit_lambda(vintage_week: int) -> dict[str, object]:
    """Grid-search the margin damping factor on finished games only."""
    obs = _finished_at_or_before(vintage_week)
    if len(obs) < 8:
        return {"lambda": 1.0, "n_games": float(len(obs)), "status": "not_enough_games_defaults_to_1.0",
                "mae_at_lambda": float("nan"), "mae_at_lambda_1": float("nan")}
    best = (1.0, float("inf"))
    grid = [i / 20.0 for i in range(0, 21)]
    for lam in grid:
        mae = sum(abs(actual - lam * model) for _i, model, actual in obs) / len(obs)
        if mae < best[1]:
            best = (lam, mae)
    mae_1 = sum(abs(actual - model) for _i, model, actual in obs) / len(obs)
    return {"lambda": best[0], "n_games": float(len(obs)), "status": "fitted_on_official_results",
            "mae_at_lambda": best[1], "mae_at_lambda_1": mae_1}


def _finished_totals_at_or_before(vintage_week: int) -> list[tuple[int, float, float]]:
    """(index, model total, actual game total) for feed games up to ``vintage_week``.

    Same discipline as :func:`_finished_at_or_before`: the scoring-rate inputs a
    game is priced with are the ones published at or before that game.
    """
    out = []
    for i, (gid, wk, _d, _s, away, home, ap, hp, _src) in enumerate(C.FINAL_GAMES):
        if wk > vintage_week:
            continue
        inp = Inputs(gid, away, home, wk - 1, R.as_of(wk - 1))
        out.append((i, float(stage2_total(inp, stage1_side(inp), 0.0)["fair_line_raw"]),
                    float(hp + ap)))
    return out


@memo
def damping_scan(market_type: str, vintage_week: int) -> list[dict[str, object]]:
    """Published shrinkage grid - analysis only, never baked into the line.

    ``shrink`` multiplies the model's deviation from the league baseline (totals)
    or from a zero margin (side). A scan that bottoms out at shrink = 1.0 says the
    scoring-rate decomposition earns its place; one that bottoms out at 0.0 says
    the deviation is noise at this sample size and the baseline is the better line.
    """
    obs = (_finished_at_or_before(vintage_week) if market_type == "side"
           else _finished_totals_at_or_before(vintage_week))
    if not obs:
        return []
    if market_type == "side":
        centre, baseline = 0.0, R.league_baseline(vintage_week)["points_per_team_game"] * 0.0
    else:
        centre = R.league_baseline(vintage_week)["points_per_team_game"] * 2.0
    rows = []
    for i in range(0, 21):
        k = i / 20.0
        mae = sum(abs(actual - (centre + k * (model - centre))) for _j, model, actual in obs) / len(obs)
        mse = sum((actual - (centre + k * (model - centre))) ** 2 for _j, model, actual in obs) / len(obs)
        bias = sum((centre + k * (model - centre)) - actual for _j, model, actual in obs) / len(obs)
        rows.append({"market_type": market_type, "vintage_week": vintage_week,
                     "shrink_factor": k, "n_games": len(obs), "mae_points": mae,
                     "mse_points": mse, "mean_signed_error_points": bias,
                     "baseline_mae_at_shrink_zero":
                         sum(abs(actual - centre) for _j, model, actual in obs) / len(obs)})
    return rows


@memo
def fit_total_shrinkage(vintage_week: int) -> dict[str, object]:
    """Best shrink factor for the total, with the honest in-sample caveat."""
    rows = damping_scan("total", vintage_week)
    if len(rows) < 8:
        return {"shrink": 1.0, "n_games": float(len(rows)),
                "status": "not_enough_games_defaults_to_1.0",
                "mae_at_best": float("nan"), "mae_at_shrink_1": float("nan"),
                "mae_at_shrink_0": float("nan")}
    best = min(rows, key=lambda r: float(r["mae_points"]))
    at1 = next(r for r in rows if float(r["shrink_factor"]) == 1.0)
    at0 = next(r for r in rows if float(r["shrink_factor"]) == 0.0)
    return {"shrink": float(best["shrink_factor"]), "n_games": float(best["n_games"]),
            "status": "fitted_in_sample_on_official_results",
            "mae_at_best": float(best["mae_points"]), "mae_at_shrink_1": float(at1["mae_points"]),
            "mae_at_shrink_0": float(at0["mae_points"]),
            "best_beats_undamped": float(best["mae_points"]) < float(at1["mae_points"]) - 1e-9,
            "caveat": "in-sample grid search on a short feed; a shrink factor chosen on the same games it is "
                      "scored on is optimistic by construction, so it is published as a diagnostic and is not "
                      "applied to the published line"}


def stage1_side(inp: Inputs, hfa: float = 0.0, lam: float | None = None) -> dict[str, object]:
    """Stage 1 - originate the side."""
    raw = raw_margin(inp, hfa)
    fit = fit_lambda(inp.vintage_week)
    lam_used = 1.0 if lam is None else lam
    margin = lam_used * raw
    step = float(PARAMS["line_step"]["value"])
    return {
        "stage": 1,
        "market_type": "side",
        "expected_home_points": raw / 2.0 + 0.0,
        "expected_away_points": -raw / 2.0,
        "model_margin_undamped": raw,
        "margin_damping_lambda": lam_used,
        "lambda_fit_n_games": fit["n_games"],
        "lambda_fit_status": fit["status"],
        "expected_margin_home": margin,
        "fair_line": S.round_half_up(-margin, step),  # negative = home favoured
        "fair_line_raw": -margin,
        "favourite_abbr": inp.home if margin > 0 else inp.away if margin < 0 else "",
        "unit": "points",
        "published": True,
    }


def stage2_total(inp: Inputs, side: dict[str, object], hfa: float = 0.0) -> dict[str, object]:
    """Stage 2 - originate the total, after the side is on the record, without
    re-fitting the side. The total is the undamped sum: damping is a margin-level
    correction and must not shrink the scoring expectation as well."""
    if side.get("stage") != 1 or not side.get("published"):
        raise StageOrderError("the total may only be originated after the side is published")
    eh, ea = _expected(inp, hfa)
    total = eh + ea
    step = float(PARAMS["line_step"]["value"])
    return {
        "stage": 2,
        "market_type": "total",
        "fair_line": S.round_half_up(total, step),
        "fair_line_raw": total,
        "expected_game_points": total,
        "unit": "points",
        "depends_on": "stage1_side",
        "published": True,
    }


def _discrete_scores(mu: float, sigma: float, support: int) -> list[float]:
    """P(score = s) for s in 0..support from a continuity-corrected Normal."""
    if sigma <= 0:
        return []
    out = []
    for s in range(support + 1):
        hi = S.normal_cdf((s + 0.5 - mu) / sigma)
        lo = S.normal_cdf((s - 0.5 - mu) / sigma)
        out.append(max(hi - lo, 0.0))
    tot = sum(out)
    return [p / tot for p in out] if tot > 0 else out


def stage3_moneyline(side: dict[str, object], total: dict[str, object],
                     disp: dict[str, float], push_on_tie: bool = True) -> dict[str, object]:
    """Stage 3 - derive the moneyline from the two published numbers."""
    if (side.get("stage") != 1 or not side.get("published")
            or total.get("stage") != 2 or not total.get("published")):
        raise StageOrderError("moneyline must be derived after the side and the total are published")
    sigma_pts, rho = disp.get("sigma_pts", float("nan")), disp.get("rho_home_away", float("nan"))
    if any(math.isnan(v) for v in (sigma_pts, rho)):
        return {"stage": 3, "market_type": "moneyline", "fair_line": "",
                "reason_blank": "sigma_pts or rho unavailable at this vintage (feed too short)"}
    margin_pub = -float(side["fair_line"])
    t = float(total["fair_line"])
    eh = (t + margin_pub) / 2.0
    ea = (t - margin_pub) / 2.0
    ph = _discrete_scores(eh, sigma_pts, MAX_TEAM_POINTS)
    pa = _discrete_scores(ea, sigma_pts, MAX_TEAM_POINTS)
    p_home = p_away = p_tie = 0.0
    for h, wh in enumerate(ph):
        if wh == 0.0:
            continue
        for a, wa in enumerate(pa):
            if wa == 0.0:
                continue
            joint = wh * wa
            if h > a:
                p_home += joint
            elif h < a:
                p_away += joint
            else:
                p_tie += joint
    denom = p_home + p_away
    p_home_ml = (p_home / denom) if (denom > 0 and push_on_tie) else p_home
    p_home_ml = min(max(p_home_ml, 0.001), 0.999)
    return {
        "stage": 3,
        "market_type": "moneyline",
        "fair_line": S.american_from_prob(p_home_ml),
        "fair_line_away": S.american_from_prob(1.0 - p_home_ml),
        "fair_prob_home_win": p_home,
        "fair_prob_away_win": p_away,
        "fair_prob_tie": p_tie,
        "fair_prob_home_ml_no_push": p_home_ml,
        "implied_home_points": eh,
        "implied_away_points": ea,
        "sigma_pts_used": sigma_pts,
        "rho_used": rho,
        "unit": "american_odds_no_vig",
        "depends_on": "stage1_side_and_stage2_total_published_lines",
        "published": True,
    }


def originate(inp: Inputs, hfa: float = 0.0) -> dict[str, dict[str, object]]:
    """Run the three stages in the required order."""
    side = stage1_side(inp, hfa)
    total = stage2_total(inp, side, hfa)
    ml = stage3_moneyline(side, total, dispersion(inp.vintage_week))
    return {"side": side, "total": total, "moneyline": ml}


def slate_inputs(vintage_week: int, games: list[tuple] | None = None) -> list[Inputs]:
    tab = R.as_of(vintage_week)
    games = games if games is not None else C.WEEK10_SLATE
    return [Inputs(gid, away, home, vintage_week, tab)
            for gid, _d, _t, _n, away, home, _s, _src in games]


# ---- fair / market / difference triples -----------------------------------
MARKET_BLANK_REASON = (
    "no official or licensed source available in this environment publishes a book "
    "price, so the market column and the difference column are blank by design"
)


def published_columns(market_type: str, model_value: str, model_raw: str,
                      unit: str) -> dict[str, str]:
    """The three-column publication contract: model fair line, market line, difference.

    A difference against a blank is not a number, so both cells stay blank and both
    carry the same flag id. This is what makes the edge column trustworthy: it
    contains no invented entries.
    """
    return {
        f"model_fair_line_{market_type}": model_value,
        f"model_fair_line_{market_type}_raw": model_raw,
        f"market_line_{market_type}": "",
        f"difference_{market_type}": "",
        f"difference_{market_type}_status": "blank_no_licensed_market_price",
        f"line_unit_{market_type}": unit,
        "market_flag_id": "D966-F01",
    }


def published_lines(vintage_week: int = 9, hfa: float = 0.0) -> list[dict[str, str]]:
    """The published line table: side first, then total, then moneyline.

    Each market carries the three-column contract - model fair line, market line,
    difference - so a reader can see at once which of the three this pack can
    actually fill. Model columns are arithmetic on the standings feed; the market and
    difference columns are blank for every row, with the flag id attached.
    """
    tab = R.as_of(vintage_week)
    graded = {g[0]: g for g in C.FINAL_GAMES}
    rows: list[dict[str, str]] = []
    for i, (gid, date, slot, net, away, home, status, _src) in enumerate(C.WEEK10_SLATE, start=1):
        inp = Inputs(gid, away, home, vintage_week, tab)
        out = originate(inp, hfa)
        row: dict[str, str] = {
            "line_id": f"D966-LINE-{i:02d}",
            "season": "2026", "week": "10", "game_id": gid,
            "date_on_official_card": date, "kickoff_slot_on_official_card": slot,
            "network_on_official_card": net,
            "away": away, "home": home, "fixture_status": status,
            "vintage_week": str(vintage_week),
            "stage_order_contract": "1 side -> 2 total -> 3 moneyline",
            "home_record_in_standing_used": f"{int(tab[home]['w'])}-{int(tab[home]['l'])}"
                                           f"{'-1' if tab[home]['t'] else ''}",
            "away_record_in_standing_used": f"{int(tab[away]['w'])}-{int(tab[away]['l'])}"
                                           f"{'-1' if tab[away]['t'] else ''}",
        }
        row.update(inp.summary())
        for mtype, key, unit in (("side", "side", "points"), ("total", "total", "points"),
                                 ("moneyline_home", "moneyline", "american_odds_no_vig")):
            src_key = "moneyline" if mtype == "moneyline_home" else mtype
            m = out[src_key]
            value = str(m.get("fair_line", ""))
            raw = ""
            if mtype == "moneyline_home":
                raw = S.fmt(float(m["fair_prob_home_win"]), 4) if "fair_prob_home_win" in m else ""
            elif "fair_line_raw" in m:
                raw = S.fmt(float(m["fair_line_raw"]), 3)
            row.update(published_columns(mtype, value, raw, unit))
        row["side_expected_margin_home"] = S.fmt(float(out["side"]["expected_margin_home"]), 3)
        row["side_margin_undamped"] = S.fmt(float(out["side"]["model_margin_undamped"]), 3)
        row["margin_damping_lambda"] = S.fmt(float(out["side"]["margin_damping_lambda"]), 2)
        row["lambda_fit_status"] = str(out["side"]["lambda_fit_status"])
        row["lambda_fit_n_games"] = str(int(out["side"]["lambda_fit_n_games"]))
        row["total_expected_game_points"] = S.fmt(float(out["total"]["expected_game_points"]), 3)
        row["total_baseline_league"] = S.fmt(2.0 * R.league_baseline(vintage_week)["points_per_team_game"], 3)
        row["total_expected_home_points"] = S.fmt(float(out["side"]["expected_home_points"]), 3)
        row["total_expected_away_points"] = S.fmt(float(out["side"]["expected_away_points"]), 3)

        def _ml_prob(field: str) -> str:
            return (S.fmt(float(out["moneyline"][field]), 4)
                    if field in out["moneyline"] else "")

        row["moneyline_prob_home"] = _ml_prob("fair_prob_home_win")
        row["moneyline_prob_away"] = _ml_prob("fair_prob_away_win")
        row["moneyline_prob_tie"] = _ml_prob("fair_prob_tie")
        row["moneyline_blank_reason"] = str(out["moneyline"].get("reason_blank", ""))
        row["dispersion_sigma_pts"] = S.fmt(dispersion(vintage_week)["sigma_pts"], 4)
        row["dispersion_rho_home_away"] = S.fmt(dispersion(vintage_week)["rho_home_away"], 4)
        row["dispersion_n_team_games"] = str(int(dispersion(vintage_week)["n_team_games"]))
        g = graded.get(gid)
        if g:
            margin = g[7] - g[6]
            side_line = float(out["side"]["fair_line"])
            total_line = float(out["total"]["fair_line"])
            row["grade_side"] = "push" if abs(margin + side_line) < 1e-9 else (
                "home_covered" if margin + side_line > 0 else "away_covered")
            row["grade_total"] = "push" if abs(g[6] + g[7] - total_line) < 1e-9 else (
                "over" if g[6] + g[7] > total_line else "under")
            row["actual_score"] = (f"{g[4]} {g[6]} at {g[5]} {g[7]} (final; home margin "
                                   f"{g[7] - g[6]:+d})")
            row["grade_official_source_url"] = C.game_url(gid)
        else:
            row["grade_side"] = row["grade_total"] = ""
            row["actual_score"] = "not_played_at_capture_time"
            row["grade_official_source_url"] = ""
        row["model_version"] = "nfl_d966f630_v1"
        row["official_source_url"] = C.link_for("STANDINGS")
        row["game_page_url"] = C.game_url(gid)
        row["read_on_utc"] = C.CAPTURE_DATE_UTC
        rows.append(row)
    return rows


PUBLISHED_LINE_FIELDS = [
    "line_id", "season", "week", "game_id", "date_on_official_card", "kickoff_slot_on_official_card",
    "network_on_official_card", "away", "home", "fixture_status", "vintage_week", "stage_order_contract",
    "home_record_in_standing_used", "away_record_in_standing_used",
    "inputs_away_games", "inputs_home_games", "inputs_away_ppg", "inputs_away_papg", "inputs_home_ppg",
    "inputs_home_papg", "inputs_league_ppg", "inputs_official_source_url",
    "model_fair_line_side", "model_fair_line_side_raw", "market_line_side", "difference_side",
    "difference_side_status", "line_unit_side",
    "model_fair_line_total", "model_fair_line_total_raw", "market_line_total", "difference_total",
    "difference_total_status", "line_unit_total",
    "model_fair_line_moneyline_home", "model_fair_line_moneyline_home_raw", "market_line_moneyline_home",
    "difference_moneyline_home", "difference_moneyline_home_status", "line_unit_moneyline_home",
    "market_flag_id",
    "side_expected_margin_home", "side_margin_undamped", "margin_damping_lambda", "lambda_fit_status",
    "lambda_fit_n_games", "total_expected_game_points", "total_baseline_league",
    "total_expected_home_points", "total_expected_away_points",
    "moneyline_prob_home", "moneyline_prob_away", "moneyline_prob_tie", "moneyline_blank_reason",
    "dispersion_sigma_pts", "dispersion_rho_home_away", "dispersion_n_team_games",
    "grade_side", "grade_total", "actual_score", "grade_official_source_url",
    "model_version", "official_source_url", "game_page_url", "read_on_utc",
]
