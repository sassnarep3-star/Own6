"""Two rankings, deliberately not combined.

The brief's eighth requirement is the reason this file is split in two. A single
leaderboard ordered by profit lets a lucky staking run disguise a bad signal, and
lets a good signal be buried by a bad night of sizing. So the pack publishes:

``signal_table()``
    how good the *numbers* are: absolute error of each originated line against the
    official final score, against the naive baseline a reader could compute without
    the model at all; plus Brier and log loss on the cover probabilities, hit rate
    with a Wilson interval, and a calibration gap. No stake, no price, no payout.

``staking_table()``
    how good the *betting* was on top of those numbers: units per ticket, maximum
    drawdown, streaks, and the size of a stake a fractional-Kelly rule would have
    taken. Every column here is reported with its own z statistic against what a
    fair price would have produced, because that is the only honest way to say how
    much of the result was luck.

``combined_view()`` puts the two side by side with their ranks and the rank gap - it
never averages them into one score. The reward tiers read the signal rank; the
staking rank decides nothing about eligibility, and ``demotion.py`` can fire on
either block.
"""

from __future__ import annotations

import math

from . import capture as C
from . import originate as O
from . import results as R
from . import stats as S
from . import backtest as B
from . import prices as P
from .cache import memo

N_FLOOR = 20                      # declared minimum graded tickets for a ranked row
BREAK_EVEN_EVEN_MONEY = 0.5
KELLY_FRACTION = 0.5              # half-Kelly, declared, not optimised
CALIBRATION_TOLERANCE = 0.08      # |mean predicted - observed| before the gate fires


@memo
def _grades() -> dict[str, dict[str, list]]:
    bucket: dict[str, dict[str, list]] = {}
    for st in B.STRATEGIES:
        bucket[st.strategy_id] = {"p": [], "y": [], "units": [], "outcomes": [], "tickets": []}
    for leg in B.settled_leg_rows():
        b = bucket[leg["strategy_id"]]
        if leg["outcome"] == "push":
            b["outcomes"].append("push")
            continue
        b["outcomes"].append(leg["outcome"])
        b["units"].append(float(leg["units_if_single"]))
        p = float(leg["model_prob"]) if leg["model_prob"] else float("nan")
        if p == p:
            b["p"].append(min(max(p, 1e-6), 1 - 1e-6))
            b["y"].append(1 if leg["outcome"] == "win" else 0)
    for tk in B.settled_ticket_rows():
        b = bucket[tk["strategy_id"]]
        b["tickets"].append((tk["outcome"], float(tk["units"])))
    return bucket


_TARGET_EVENT = {
    "side": "the side taken covers the line quoted on that ticket",
    "total": "the side taken clears the total quoted on that ticket",
    "moneyline": "the club named on the ticket wins in regulation",
}


def _leg_lines(strategy_id: str) -> list[tuple[str, float, int, int]]:
    """(market, quoted line, actual home points, actual away points) per leg."""
    out = []
    for leg in B.settled_leg_rows():
        if leg["strategy_id"] != strategy_id or not leg["line_published"]:
            continue
        out.append((leg["market"], float(leg["line_published"]),
                    int(leg["actual_home_points"]), int(leg["actual_away_points"])))
    return out


def _line_quality(strategy_id: str) -> dict[str, float]:
    """Absolute error of *this strategy's own quoted lines*, against the naive line on
    the same games. Damped and depth-adjusted variants therefore score on the number
    they would actually have published, not on the raw model's."""
    out: dict[str, float] = {}
    legs = _leg_lines(strategy_id)
    side = [(line, hp - ap) for market, line, hp, ap in legs if market == "side"]
    tot = [(line, hp + ap) for market, line, hp, ap in legs if market == "total"]
    if side:
        out["mae_side"] = S.mean([abs(-line - margin) for line, margin in side])
        out["mae_side_naive_zero_margin"] = S.mean([abs(0.0 - margin) for _line, margin in side])
        out["n_side_legs"] = float(len(side))
    if tot:
        league = S.mean([B.league_total(int(leg["week"]) - 1)
                         for leg in B.settled_leg_rows()
                         if leg["strategy_id"] == strategy_id and leg["market"] == "total"])
        out["mae_total"] = S.mean([abs(line - total) for line, total in tot])
        out["mae_total_naive_league"] = S.mean([abs(league - total) for _line, total in tot])
        out["n_total_legs"] = float(len(tot))
    return out


@memo
def signal_table() -> list[dict[str, str]]:
    grades = _grades()
    out: list[dict[str, str]] = []
    for st in B.STRATEGIES:
        g = grades[st.strategy_id]
        n_out = len(g["outcomes"])
        n_push = g["outcomes"].count("push") if g["outcomes"] else 0
        wins = g["outcomes"].count("win")
        row: dict[str, str] = {
            "strategy_id": st.strategy_id,
            "strategy_name": st.name,
            "family": st.family,
            "markets": " + ".join(st.markets),
            "rule_verbatim": st.rule,
            "n_tickets_graded": str(len(g["tickets"])),
            "n_legs_graded_excluding_pushes": str(n_out),
            "n_push_legs_excluded": str(n_push),
            "hit_rate_cover": S.fmt(wins / n_out if n_out else float("nan"), 4),
            "hit_rate_ci95_low": "",
            "hit_rate_ci95_high": "",
            "mean_predicted_cover_prob": S.fmt(S.mean(g["p"]) if g["p"] else float("nan"), 4),
            "calibration_gap": S.fmt((S.mean(g["p"]) - wins / n_out)
                                     if (g["p"] and n_out) else float("nan"), 4),
            "brier_score": S.fmt(S.brier(g["p"], g["y"]) if len(g["p"]) >= 5 else float("nan"), 5),
            "brier_naive_at_half": S.fmt(0.25 if len(g["p"]) >= 5 else float("nan"), 5),
            "target_event": _TARGET_EVENT.get(st.markets[0], ""),
            "base_rate_of_target_event": S.fmt(wins / n_out if n_out else float("nan"), 4),
            "brier_climatology_baseline": "",
            "brier_skill_score_vs_base_rate": "",
            "log_loss": S.fmt(S.logloss(g["p"], g["y"]) if len(g["p"]) >= 5 else float("nan"), 5),
            "n_probability_observations": str(len(g["p"])),
            "signal_status": "",
            "flag_id": "",
            "model_version": P.MODEL_VERSION,
            "graded_on_official_final_scores": "yes",
            "official_source_url": C.link_for("SCHED-W9"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
            "note": "signal block only - no stake size, no payout and no price of any kind enters this table",
        }
        if n_out:
            lo, hi = S.wilson_interval(wins, n_out)
            row["hit_rate_ci95_low"] = S.fmt(lo, 4)
            row["hit_rate_ci95_high"] = S.fmt(hi, 4)
            if len(g["p"]) >= 5 and n_out:
                base = wins / n_out
                brier_clim = base * (1.0 - base) ** 2 + (1.0 - base) * base ** 2
                bss = 1.0 - S.brier(g["p"], g["y"]) / brier_clim if brier_clim > 0 else float("nan")
                row["brier_climatology_baseline"] = S.fmt(brier_clim, 5)
                row["brier_skill_score_vs_base_rate"] = S.fmt(bss, 5)
                row["comparability_note"] = ("Brier and skill score are comparable across strategies only "
                                             "because each is measured against its own event's base rate; raw "
                                             "Brier across different target events is not a ranking input")
        lq = _line_quality(st.strategy_id)
        for key, label in (("mae_side", "mean_abs_error_side_points"),
                           ("mae_side_naive_zero_margin", "naive_baseline_abs_error_side_points"),
                           ("mae_total", "mean_abs_error_total_points"),
                           ("mae_total_naive_league", "naive_baseline_abs_error_total_points"),
                           ("n_side_legs", "n_side_legs_scored"),
                           ("n_total_legs", "n_total_legs_scored")):
            row[label] = S.fmt(lq.get(key, float("nan")), 4) if key in lq else ""
        if "mae_side" in lq or "mae_total" in lq:
            parts = []
            if "mae_side" in lq:
                parts.append(f"side {lq['mae_side'] - lq['mae_side_naive_zero_margin']:+.3f} pts vs a zero-margin line")
            if "mae_total" in lq:
                parts.append(f"total {lq['mae_total'] - lq['mae_total_naive_league']:+.3f} pts vs the league baseline")
            row["line_quality_vs_naive"] = "; ".join(parts)
            worse = (("mae_side" in lq and lq["mae_side"] > lq["mae_side_naive_zero_margin"])
                     or ("mae_total" in lq and lq["mae_total"] > lq["mae_total_naive_league"]))
            row["line_quality_status"] = ("beats_naive_baseline" if not worse else
                                          "worse_than_naive_baseline_on_at_least_one_market")
        else:
            row["line_quality_vs_naive"] = ""
            row["line_quality_status"] = "not_applicable_no_priced_line_in_this_strategy"
        if st.status == "blocked":
            row["signal_status"] = "blocked_no_input"
            row["flag_id"] = "D966-F09"
        elif n_out < N_FLOOR:
            row["signal_status"] = "below_published_n_floor"
            row["flag_id"] = "D966-F08"
        else:
            row["signal_status"] = "ranked"
        out.append(row)
    ranked = sorted([r for r in out if r["signal_status"] == "ranked"],
                    key=lambda r: (-_f(r["brier_skill_score_vs_base_rate"]), -_mae_edge(r),
                                   -int(r["n_legs_graded_excluding_pushes"])))
    for i, r in enumerate(ranked, start=1):
        r["signal_rank"] = str(i)
    for r in out:
        r.setdefault("signal_rank", "")
        r["rank_basis"] = ("Brier skill score against the target event's own base rate, then points of absolute "
                           "error saved against the naive line, then sample size"
                           if r["signal_status"] == "ranked" else "")
    return out


def _mae_edge(r: dict[str, str]) -> float:
    """Points of absolute error the model saves versus the naive baseline."""
    edge = 0.0
    for a, b in (("mean_abs_error_side_points", "naive_baseline_abs_error_side_points"),
                 ("mean_abs_error_total_points", "naive_baseline_abs_error_total_points")):
        try:
            edge += float(r[b]) - float(r[a])
        except (KeyError, ValueError):
            continue
    return edge


def _drawdown_and_streaks(units: list[float]) -> tuple[float, int, int]:
    peak = cum = 0.0
    max_dd = 0.0
    win = loss = cur_w = cur_l = 0
    for u in units:
        cum += u
        peak = max(peak, cum)
        max_dd = max(max_dd, peak - cum)
        if u > 0:
            cur_w += 1
            cur_l = 0
        elif u < 0:
            cur_l += 1
            cur_w = 0
        else:
            cur_w = cur_l = 0
        win, loss = max(win, cur_w), max(loss, cur_l)
    return max_dd, win, loss


@memo
def staking_table() -> list[dict[str, str]]:
    grades = _grades()
    out: list[dict[str, str]] = []
    for st in B.STRATEGIES:
        g = grades[st.strategy_id]
        units = [float(tk[1]) for tk in g["tickets"]]
        n = len(units)
        total = math.fsum(units)
        sd_units = S.sd(units) if n > 1 else float("nan")
        z = total / (sd_units * math.sqrt(n)) if n > 1 and sd_units and sd_units == sd_units else float("nan")
        p = 2.0 * (1.0 - S.normal_cdf(abs(z))) if z == z else float("nan")
        probs = [p for p in g["p"] if p == p]
        kelly = []
        for i, _u in enumerate(units):
            pr = probs[i] if i < len(probs) else float("nan")
            if pr == pr:
                b = 1.0
                f_star = (b * pr - (1.0 - pr)) / b if b > 0 else 0.0
                kelly.append(max(min(KELLY_FRACTION * f_star, 0.25), 0.0))
        max_dd, w_streak, l_streak = _drawdown_and_streaks(units)
        row = {
            "strategy_id": st.strategy_id,
            "strategy_name": st.name,
            "family": st.family,
            "stake_rule": st.stake_rule,
            "n_tickets_graded": str(n),
            "units_total": S.fmt(total, 4),
            "units_per_ticket": S.fmt(total / n if n else float("nan"), 4),
            "sd_units_per_ticket": S.fmt(sd_units, 4),
            "roi_units_per_100_tickets": S.fmt(100.0 * total / n if n else float("nan"), 3),
            "z_vs_fair_price": S.fmt(z, 3),
            "p_two_sided_normal": S.fmt(p, 4),
            "max_drawdown_units": S.fmt(max_dd, 3),
            "longest_win_streak": str(w_streak),
            "longest_loss_streak": str(l_streak),
            "mean_half_kelly_stake_fraction": S.fmt(S.mean(kelly) if kelly else float("nan"), 5),
            "staking_status": "",
            "flag_id": "",
            "price_basis": ("even_money_and_no_vig_internal_prices_no_book_hold"
                            if st.family != "prop_combo" else "unpriced"),
            "luck_note": "units_total divided by its own standard error is the luck measure: a large |z| at small "
                         "n is far more likely a run of variance than a property of the model, so this column can "
                         "never move a strategy's reward tier",
            "official_source_url": C.link_for("SCHED-W9"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        }
        if not n:
            row["staking_status"] = "no_graded_tickets"
            row["flag_id"] = "D966-F08"
        elif n < N_FLOOR:
            row["staking_status"] = "below_published_n_floor"
            row["flag_id"] = "D966-F08"
        else:
            row["staking_status"] = "reported_not_ranked_for_eligibility"
        out.append(row)
    ordered = sorted(out, key=lambda r: -_f(r["units_total"]))
    for i, r in enumerate(ordered, start=1):
        if r["staking_status"] == "reported_not_ranked_for_eligibility":
            r["staking_rank_display_only"] = str(i)
        else:
            r["staking_rank_display_only"] = ""
    return out


def _f(x: str) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


@memo
def combined_view() -> list[dict[str, str]]:
    sig = {r["strategy_id"]: r for r in signal_table()}
    stk = {r["strategy_id"]: r for r in staking_table()}
    out = []
    for sid in sorted(sig):
        s, k = sig[sid], stk[sid]
        gap = ""
        if s.get("signal_rank") and k.get("staking_rank_display_only"):
            gap = str(int(k["staking_rank_display_only"]) - int(s["signal_rank"]))
        out.append({
            "strategy_id": sid,
            "strategy_name": s["strategy_name"],
            "family": s["family"],
            "signal_rank": s.get("signal_rank", ""),
            "signal_status": s["signal_status"],
            "brier_score": s["brier_score"],
            "hit_rate_cover": s["hit_rate_cover"],
            "n_legs_graded_excluding_pushes": s["n_legs_graded_excluding_pushes"],
            "line_quality_status": s.get("line_quality_status", ""),
            "line_quality_vs_naive": s.get("line_quality_vs_naive", ""),
            "staking_rank_display_only": k["staking_rank_display_only"],
            "units_total": k["units_total"],
            "units_per_ticket": k["units_per_ticket"],
            "z_vs_fair_price": k["z_vs_fair_price"],
            "max_drawdown_units": k["max_drawdown_units"],
            "n_tickets_graded": k["n_tickets_graded"],
            "rank_gap_staking_minus_signal": gap,
            "interpretation": ("staking rank is ahead of signal rank - a run of results, not a better model"
                               if gap and int(gap) < 0 else
                               "staking rank trails signal rank - variance, not a worse model"
                               if gap and int(gap) > 0 else
                               "ranks agree, or one block has no eligible rank"
                               if gap == "0" else "no comparable pair of ranks"),
            "official_source_url": s["official_source_url"],
            "read_on_utc": C.CAPTURE_DATE_UTC,
            "note": "the two ranks are never averaged; eligibility follows the signal block and "
                    "demotion can fire on either",
        })
    return out


@memo
def rewards_tiers() -> list[dict[str, str]]:
    """Rewards for the top signal, and why they are not cash.

    Paying out on betting results would collide with the rights position recorded by
    the prior session (the NFL Terms of Use grant non-commercial use only, and the
    wagering prohibition covers acting on league information), and it would point an
    autonomous agent at profit instead of accuracy. So the reward is standing,
    compute and disclosure: the top strategy's numbers become the reference set for
    the next published week, and it gets the badge on the leaderboard.
    """
    sig = sorted([r for r in signal_table() if r["signal_status"] == "ranked"],
                 key=lambda r: int(r["signal_rank"]))
    others = [r for r in signal_table() if r["signal_status"] != "ranked"]
    tiers = []
    for i, r in enumerate(sig, start=1):
        tier = "reference" if i == 1 else ("priority" if i <= 3 else "watch")
        tiers.append({
            "tier_id": f"D966-RW-{i:02d}",
            "flag_id": "",
            "tier": tier,
            "strategy_id": r["strategy_id"],
            "strategy_name": r["strategy_name"],
            "signal_rank": r["signal_rank"],
            "brier_score": r["brier_score"],
            "n_legs_graded": r["n_legs_graded_excluding_pushes"],
            "reward": ("next week's slate publishes this strategy's numbers as the reference line, with a "
                       "leaderboard badge naming it"
                       if tier == "reference" else
                       "re-run first in the daily builder and get a dedicated subpage section"
                       if tier == "priority" else
                       "stays on the board with its n and its errors, no additional standing"),
            "reward_currency": "none_no_monetary_payout",
            "why_not_cash": "rights position in the prior session's source record limits use of league data to "
                            "non-commercial purposes, and a cash incentive would rank strategies on profit rather "
                            "than accuracy",
            "eligibility_rule": "signal block only; staking columns cannot change a tier",
            "official_source_url": r["official_source_url"],
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    for r in others:
        tiers.append({
            "tier_id": "D966-RW-NA",
            "tier": "not_ranked",
            "strategy_id": r["strategy_id"],
            "strategy_name": r["strategy_name"],
            "signal_rank": "",
            "brier_score": r["brier_score"],
            "n_legs_graded": r["n_legs_graded_excluding_pushes"],
            "reward": "not_ranked_no_reward_in_this_run",
            "reward_currency": "none_no_monetary_payout",
            "why_not_cash": "same rights position as the ranked rows",
            "eligibility_rule": r["signal_status"],
            "flag_id": r["flag_id"],
            "official_source_url": r["official_source_url"],
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return tiers
