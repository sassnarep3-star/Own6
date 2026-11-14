"""Settlement of every published line against the verified results feed.

This is the piece that makes a backtest exist at all: each strategy's selections
are resolved against official final scores, and every settled leg carries the URL
of the page that score came from.

Pricing basis - stated once, because it is the most misread part of any internal
backtest
-----------------------------------------------------------------------------
Side and total legs settle at **even money against our own published number**;
moneyline legs settle at **our own no-vig price**. There is no book in this
environment, so there is no vig, no hold and no closing line. What comes out is a
calibration measurement, not an edge measurement: a perfectly fair model has zero
expected profit against its own price by construction. Any number here that looks
like profit is a sample artefact - which is exactly why the leaderboard ranks on
the signal block and the staking block cannot promote a strategy.

Settlement conventions (declared; they must be matched to an operator's rule once a
market exists - see suggestion D966-S03):
* a push on a side or total returns the stake: 0 units, and the leg is excluded
  from hit-rate and Brier denominators rather than counted as a miss;
* a push on a moneyline returns the stake;
* a two-leg parlay with one push pays the surviving leg's price; both push, the
  ticket pushes; any leg loses, the ticket loses.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import capture as C
from . import originate as O
from . import results as R
from . import stats as S
from .cache import memo

PACK = "nfl_d966f630"


@dataclass
class Strategy:
    strategy_id: str
    name: str
    family: str                 # single | parlay | sgp | prop_combo
    markets: tuple[str, ...]
    rule: str
    status: str = "armed"        # armed | blocked
    blocked_reason: str = ""
    params: dict[str, float] = field(default_factory=dict)
    stake_rule: str = "flat 1 unit per ticket"


STRATEGIES: list[Strategy] = [
    Strategy("D966-STR-01", "Side anchor: play the model's side every game", "single", ("side",),
             "one unit on the published home spread for every originated game",
             params={"margin_floor": 0.0}),
    Strategy("D966-STR-02", "Total anchor: side of the league scoring baseline", "single", ("total",),
             "over when the model total exceeds the league-average total at the vintage, under otherwise",
             params={"margin_floor": 0.0}),
    Strategy("D966-STR-03", "Moneyline anchor: play the model's favourite", "single", ("moneyline",),
             "one unit on whichever club the published moneyline favours"),
    Strategy("D966-STR-04", "Damped side at lambda 0.60 with a 3.0-point floor", "single", ("side",),
             "shrink the projection first, then bet only when the damped margin still clears 3.0 points",
             params={"margin_floor": 3.0, "lambda": 0.6}),
    Strategy("D966-STR-05", "Movement follower: open to close inside the store", "single", ("side",),
             "bet the direction our own number moved between its first and last snapshot before kickoff",
             status="blocked",
             blocked_reason="a same-model second snapshot is needed; the store began 2026-11-14, so the first "
                            "week the daily runner closes is the first week this can be graded",
             params={"margin_floor": 0.0}),
    Strategy("D966-STR-06", "Depth override: injury tiers dropped against the scoring-rate line", "single",
             ("side",),
             "penalise a club's expected margin by 0.75 points per tier dropped on the official report and bet "
             "only when the penalty flips the side",
             params={"margin_floor": 0.0, "depth_penalty": 0.75}),
    Strategy("D966-STR-07", "Two-game same-week side parlay", "parlay", ("side",),
             "the two largest absolute model margins of a week, one unit as a two-leg ticket",
             params={"margin_floor": 0.0}),
    Strategy("D966-STR-08", "Same-game side plus over parlay (SGP)", "sgp", ("side", "total"),
             "when the model margin is positive for the home club and the model total exceeds the league "
             "baseline, a two-leg ticket on home side and over",
             params={"margin_floor": 0.0}),
    Strategy("D966-STR-09", "Market-edge side: bet when the fair line beats the book", "single", ("side",),
             "needs a market line to difference against",
             status="blocked",
             blocked_reason="no official or licensed market price exists in this environment (flag D966-F01); "
                            "the rule stays in the catalogue so the gate has something to refuse"),
    Strategy("D966-STR-10", "Player-prop combo, three legs", "prop_combo", ("player_prop",),
             "needs official per-player game statistics to settle",
             status="blocked",
             blocked_reason="per-player statistics were not read in this session (flag D966-F06); no prop leg "
                            "is settled by inference"),
]


@memo
def league_total(vintage_week: int) -> float:
    return 2.0 * R.league_baseline(vintage_week)["points_per_team_game"]


# --------------------------------------------------------------------------
# model probabilities used for scoring (Brier), separate from the quoted line
# --------------------------------------------------------------------------
def _disp(vintage_week: int) -> tuple[float, float, str, str]:
    """Noise scale used only for scoring probabilities (Brier / log loss).

    The dispersion of margins around the model needs finished games at or before
    the vintage; the results feed starts at Week 7, so a Week 7 or Week 8 bet has
    no scale measured at its own vintage. Rather than drop those legs from the
    calibration statistics, the earliest measurable vintage is substituted and the
    substitution is named on every leg that uses it: it peeks forward, and a
    reviewer must be able to see that. No probability is invented.
    """
    for wk in [vintage_week] + [w for w in range(vintage_week + 1, 11)]:
        d = O.dispersion(wk)
        sigma, rho = d["sigma_pts"], d["rho_home_away"]
        if not (math.isnan(sigma) or math.isnan(rho)) and d["n_team_games"] >= 8:
            status = ("measured_at_vintage" if wk == vintage_week
                      else f"substituted_forward_from_vintage_{wk}:uses_results_published_after_this_bet")
            return sigma, rho, str(wk), status
    return float("nan"), float("nan"), "", "unavailable:no_measurable_dispersion_through_week_10"


def _cover_probability(model_margin: float, line: float,
                       vintage_week: int) -> tuple[float, float, str]:
    """P(home covers the published line) and P(push), on the measured noise scale.

    ``line`` is the published home spread (negative = home favoured), so a bet on
    the home club wins when ``actual_home_margin + line > 0``.
    """
    sigma_pts, rho, used_vintage, status = _disp(vintage_week)
    if math.isnan(sigma_pts):
        return float("nan"), float("nan"), status
    sigma_m = sigma_pts * math.sqrt(max(2.0 * (1.0 - rho), 1e-9))
    mu = model_margin + line
    p_cover = S.normal_cdf(mu / sigma_m)
    p_push = max(S.normal_cdf((0.5 - mu) / sigma_m) - S.normal_cdf((-0.5 - mu) / sigma_m), 0.0)
    return p_cover, p_push, f"{status}@vintage_{used_vintage or 'none'}"


def _over_probability(model_total: float, line: float,
                      vintage_week: int) -> tuple[float, float, str]:
    sigma_pts, rho, used_vintage, status = _disp(vintage_week)
    if math.isnan(sigma_pts):
        return float("nan"), float("nan"), status
    sigma_t = sigma_pts * math.sqrt(max(2.0 * (1.0 + rho), 1e-9))
    mu = model_total - line
    return S.normal_cdf(mu / sigma_t), 0.0, f"{status}@vintage_{used_vintage or 'none'}"


# --------------------------------------------------------------------------
# tickets and legs
# --------------------------------------------------------------------------
@memo
def _game_context(gid: str, week: int, lam: float = 1.0) -> dict[str, object]:
    row = next(g for g in C.FINAL_GAMES if g[0] == gid)
    _gid, _wk, _d, _slot, away, home, ap, hp, _src = row
    vintage = week - 1
    inp = O.Inputs(gid, away, home, vintage, R.as_of(vintage))
    out = O.originate(inp)
    if lam != 1.0:
        out["side"] = O.stage1_side(inp, 0.0, lam)
        out["total"] = O.stage2_total(inp, out["side"], 0.0)
        out["moneyline"] = O.stage3_moneyline(out["side"], out["total"], O.dispersion(vintage))
    out["_away"], out["_home"] = away, home
    out["_actual_home"], out["_actual_away"] = hp, ap
    out["_vintage"] = vintage
    return out


def _depth_totals() -> dict[str, float]:
    from . import depth as D
    agg: dict[str, float] = {}
    for row in D.group_depth():
        agg[row["club"]] = agg.get(row["club"], 0.0) + int(row["tiers_dropped_lower_bound"])
    return agg


@memo
def tickets() -> list[dict[str, object]]:
    """Every ticket each strategy takes over the graded window (Weeks 7-10)."""
    out: list[dict[str, object]] = []
    weeks = sorted({wk for _g, wk, *_r in C.FINAL_GAMES})
    by_week: dict[int, list[str]] = {wk: [] for wk in weeks}
    for gid, wk, *_r in C.FINAL_GAMES:
        by_week[wk].append(gid)
    depth = _depth_totals()

    for st in STRATEGIES:
        if st.status == "blocked":
            continue
        for wk in weeks:
            lam = float(st.params.get("lambda", 1.0))
            ctx = {gid: _game_context(gid, wk, lam) for gid in by_week[wk]}
            base_total = league_total(wk - 1)

            if st.strategy_id in ("D966-STR-01", "D966-STR-04"):
                for gid, m in ctx.items():
                    margin_exp = float(m["side"]["expected_margin_home"])
                    if abs(margin_exp) < float(st.params["margin_floor"]):
                        continue
                    out.append(_ticket(st, wk, gid, [{
                        "game_id": gid, "market": "side", "line": float(m["side"]["fair_line"]),
                        "side_taken": "home",
                        "model_prob": _cover_probability(margin_exp, float(m["side"]["fair_line"]),
                                                          int(m["_vintage"]))[0],
                        "prob_status": _cover_probability(margin_exp, float(m["side"]["fair_line"]),
                                                          int(m["_vintage"]))[2],
                    }]))
            elif st.strategy_id == "D966-STR-02":
                for gid, m in ctx.items():
                    line = float(m["total"]["fair_line"])
                    taken = "over" if line > base_total else "under"
                    p_over, _, prob_status = _over_probability(
                        float(m["total"]["fair_line_raw"]), line, int(m["_vintage"]))
                    out.append(_ticket(st, wk, gid, [{
                        "game_id": gid, "market": "total", "line": line, "side_taken": taken,
                        "model_prob": p_over if taken == "over" else 1.0 - p_over,
                        "prob_status": prob_status,
                    }]))
            elif st.strategy_id == "D966-STR-03":
                for gid, m in ctx.items():
                    ml = m["moneyline"]
                    if "fair_prob_home_win" not in ml:
                        continue
                    p_home = float(ml["fair_prob_home_win"])
                    fav_home = p_home >= 0.5
                    out.append(_ticket(st, wk, gid, [{
                        "game_id": gid, "market": "moneyline",
                        "line": float(ml["fair_line"]) if fav_home else float(ml["fair_line_away"]),
                        "side_taken": "home" if fav_home else "away",
                        "model_prob": p_home if fav_home else 1.0 - p_home,
                    }]))
            elif st.strategy_id == "D966-STR-06":
                if wk != 10:
                    continue                    # the injury report exists for Week 10 only
                for gid, m in ctx.items():
                    raw = float(m["side"]["expected_margin_home"])
                    pen = float(st.params.get("depth_penalty", 0.75))
                    adj = raw - pen * depth.get(m["_home"], 0.0) + pen * depth.get(m["_away"], 0.0)
                    if raw == 0 or (raw > 0) == (adj > 0):
                        continue                 # the depth penalty did not flip the side
                    out.append(_ticket(st, wk, gid, [{
                        "game_id": gid, "market": "side", "line": -S.round_half_up(adj, 0.5),
                        "side_taken": "home",
                        "model_prob": _cover_probability(adj, -S.round_half_up(adj, 0.5), int(m["_vintage"]))[0],
                        "prob_status": _cover_probability(adj, -S.round_half_up(adj, 0.5), int(m["_vintage"]))[2],
                        "note": f"raw {raw:+.2f} -> depth-adjusted {adj:+.2f}",
                    }]))
            elif st.strategy_id == "D966-STR-07":
                ranked = sorted(by_week[wk],
                                key=lambda g: -abs(float(ctx[g]["side"]["expected_margin_home"])))[:2]
                if len(ranked) < 2:
                    continue
                legs = []
                for gid in ranked:
                    m = ctx[gid]
                    margin_exp = float(m["side"]["expected_margin_home"])
                    cp = _cover_probability(margin_exp, float(m["side"]["fair_line"]), int(m["_vintage"]))
                    legs.append({
                        "game_id": gid, "market": "side", "line": float(m["side"]["fair_line"]),
                        "side_taken": "home",
                        "model_prob": cp[0], "prob_status": cp[2],
                    })
                out.append(_ticket(st, wk, "+".join(ranked), legs))
            elif st.strategy_id == "D966-STR-08":
                for gid, m in ctx.items():
                    margin_exp = float(m["side"]["expected_margin_home"])
                    line_t = float(m["total"]["fair_line"])
                    if margin_exp <= 0 or line_t <= base_total:
                        continue
                    p_side, _ps, st_side = _cover_probability(
                        margin_exp, float(m["side"]["fair_line"]), int(m["_vintage"]))
                    p_over, _po, st_over = _over_probability(
                        float(m["total"]["fair_line_raw"]), line_t, int(m["_vintage"]))
                    out.append(_ticket(st, wk, gid, [
                        {"game_id": gid, "market": "side", "line": float(m["side"]["fair_line"]),
                         "side_taken": "home", "model_prob": p_side, "prob_status": st_side},
                        {"game_id": gid, "market": "total", "line": line_t, "side_taken": "over",
                         "model_prob": p_over, "prob_status": st_over},
                    ]))
    return out


def _ticket(st, wk, ticket_key, legs) -> dict[str, object]:
    return {"strategy_id": st.strategy_id, "strategy_name": st.name, "week": wk,
            "ticket_key": ticket_key, "family": st.family, "legs": legs}


# --------------------------------------------------------------------------
# leg settlement
# --------------------------------------------------------------------------
def _actual(gid: str) -> tuple[int, int]:
    row = next(g for g in C.FINAL_GAMES if g[0] == gid)
    return row[7], row[6]        # (home points, away points)


def settle_leg(leg: dict[str, object]) -> tuple[str, float]:
    gid = str(leg["game_id"])
    hp, ap = _actual(gid)
    margin = hp - ap
    total = hp + ap
    line = float(leg["line"])
    if leg["market"] == "side":
        adj = margin + line
        if abs(adj) < 1e-9:
            return "push", 0.0
        return ("win", 1.0) if adj > 0 else ("loss", -1.0)
    if leg["market"] == "total":
        diff = total - line
        if abs(diff) < 1e-9:
            return "push", 0.0
        over = leg["side_taken"] == "over"
        return ("win", 1.0) if (diff > 0) == over else ("loss", -1.0)
    if leg["market"] == "moneyline":
        if margin == 0:
            return "push", 0.0
        home = leg["side_taken"] == "home"
        return ("win", 1.0) if (margin > 0) == home else ("loss", -1.0)
    return "unpriced", float("nan")


def price_decimal(odds: float) -> float:
    """Decimal payout (including stake) for an American price, no hold applied."""
    if odds < 0:
        return 1.0 + 100.0 / abs(odds)
    return 1.0 + abs(odds) / 100.0


@memo
def settled_leg_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for tk in tickets():
        for i, leg in enumerate(tk["legs"], start=1):
            outcome, units = settle_leg(leg)
            gid = str(leg["game_id"])
            hp, ap = _actual(gid)
            rows.append({
                "leg_id": "",
                "ticket_id": f"{tk['strategy_id']}:{tk['ticket_key']}",
                "strategy_id": str(tk["strategy_id"]),
                "family": str(tk["family"]),
                "week": str(tk["week"]),
                "game_id": gid,
                "leg_index": str(i),
                "market": str(leg["market"]),
                "line_published": f"{float(leg['line']):+.2f}" if leg["market"] != "moneyline" else f"{int(leg['line'])}",
                "side_taken": str(leg["side_taken"]),
                "model_prob": S.fmt(float(leg.get("model_prob", float("nan"))), 4),
                "model_prob_basis": str(leg.get("prob_status",
                    "published_no_vig_moneyline_probability" if leg["market"] == "moneyline" else "")),
                "actual_home_points": str(hp),
                "actual_away_points": str(ap),
                "outcome": outcome,
                "units_if_single": f"{units:+.2f}",
                "price_basis": ("even_money_internal_price" if leg["market"] != "moneyline"
                                else "no_vig_internal_price"),
                "settlement_note": str(leg.get("note", "")),
                "result_official_source_url": C.game_url(gid),
                "feed_page_url": C.link_for("SCHED-W9" if int(tk["week"]) >= 9 else "SCHED-W7"),
                "read_on_utc": C.CAPTURE_DATE_UTC,
            })
    for i, r in enumerate(rows, start=1):
        r["leg_id"] = f"D966-SET-{i:04d}"
    return rows


@memo
def settled_ticket_rows() -> list[dict[str, str]]:
    """One row per ticket with the combined result and the staking outcome."""
    out: list[dict[str, str]] = []
    for tk in tickets():
        legs = tk["legs"]
        results = []
        decimal = 1.0
        for leg in legs:
            outcome, _u = settle_leg(leg)
            results.append(outcome)
            if outcome == "win":
                decimal *= (2.0 if leg["market"] != "moneyline"
                            else price_decimal(float(leg["line"])))
        if "loss" in results:
            units, status = -1.0, "loss"
        elif all(r == "push" for r in results):
            units, status = 0.0, "push"
        elif all(r in ("win", "push") for r in results):
            units, status = decimal - 1.0, "win"
        else:
            units, status = 0.0, "void_no_winning_leg"
        probs = [float(l.get("model_prob", float("nan"))) for l in legs]
        joint = 1.0
        for p in probs:
            joint *= p if p == p else 1.0
        out.append({
            "ticket_id": f"{tk['strategy_id']}:{tk['ticket_key']}",
            "strategy_id": str(tk["strategy_id"]),
            "family": str(tk["family"]),
            "week": str(tk["week"]),
            "games": str(tk["ticket_key"]),
            "n_legs": str(len(legs)),
            "leg_markets": " + ".join(str(l["market"]) for l in legs),
            "legs_summary": " ; ".join(
                f"{l['game_id']} {l['market']} {l['line']:+.1f} {l['side_taken']}" for l in legs),
            "outcome": status,
            "units": f"{units:+.4f}",
            "independent_product_of_leg_probs": S.fmt(joint, 4),
            "model_prob_note": ("legs share a game, so the product understates or overstates the true "
                                "joint probability by the measured correlation - see correlations.csv"
                                if tk["family"] in ("sgp", "parlay") else "single leg"),
            "result_official_source_url": C.game_url(str(legs[0]["game_id"])),
            "feed_page_url": C.link_for("SCHED-W9" if int(tk["week"]) >= 9 else "SCHED-W7"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


@memo
def model_abs_errors() -> list[dict[str, str]]:
    """Per-game absolute error of the two published numbers against the official
    final score. This is the purest signal statistic in the pack: no price, no
    stake, no payout - just how far the originated line was from the score."""
    rows = []
    for gid, wk, *_r in C.FINAL_GAMES:
        m = _game_context(gid, wk)
        hp, ap = m["_actual_home"], m["_actual_away"]
        margin = hp - ap
        e_side = abs(-float(m["side"]["fair_line_raw"]) - margin)
        e_total = abs(float(m["total"]["fair_line_raw"]) - (hp + ap))
        b_side = abs(float(m["side"]["fair_line"]) - float(m["side"]["fair_line_raw"]))
        rows.append({
            "game_id": gid, "week": str(wk),
            "away": str(m["_away"]), "home": str(m["_home"]),
            "model_margin_raw": S.fmt(float(m["side"]["fair_line_raw"]), 3),
            "actual_margin_home": str(margin),
            "abs_error_side_points": S.fmt(e_side, 3),
            "model_total_raw": S.fmt(float(m["total"]["fair_line_raw"]), 3),
            "actual_game_total": str(hp + ap),
            "abs_error_total_points": S.fmt(e_total, 3),
            "rounding_gap_side": S.fmt(b_side, 3),
            "baseline_abs_error_side_zero_margin": S.fmt(abs(margin), 3),
            "baseline_abs_error_total_league": S.fmt(abs(hp + ap - league_total(wk - 1)), 3),
            "vintage_week": str(wk - 1),
            "result_official_source_url": C.game_url(gid),
            "inputs_official_source_url": C.link_for("STANDINGS"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return rows
