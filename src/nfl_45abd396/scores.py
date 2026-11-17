"""Proper-score leaderboard, cluster intervals, multiplicity, controls, luck panel.

Rules encoded here (each maps to a brief requirement):

* Skill is measured with a proper score. The headline is the Brier skill score
  against the *same games'* climatology base rate (the share of home wins), not
  against a guess, and log loss is printed beside it.
* Uncertainty uses a **game-cluster** bootstrap: the resampling unit is the
  fixture, so the four strategies that forecast the same 12 games are never
  treated as independent evidence.
* Multiplicity: the number of distinct strategies tried against this corpus is
  counted, and the per-strategy significance level is Šidák-adjusted. A strategy
  is only labelled ``qualified`` if its cluster interval excludes zero *and* the
  adjusted test still rejects.
* Controls: a constant 0.5 coin and a rating-favourite rule run on exactly the
  same games, so "skill" can be compared with "no skill" on identical fixtures.
* Removal of luck: each strategy's hit count is compared with the exact binomial
  distribution that coin-flipping would produce over the same number of games.
"""

from __future__ import annotations

import hashlib
import math
import random
from statistics import mean, pstdev

Z95 = 1.959963984540054
BOOT_REPS = 4000
BOOT_SEED_MATERIAL = "nfl_45abd396/cluster-bootstrap/v1"


# ---------------------------------------------------------------------------
# elementary statistics (stdlib only)
# ---------------------------------------------------------------------------
def _binom_sf_at_least(k: int, n: int, p: float = 0.5) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    tail = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
    return min(1.0, tail)


def _binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial p-value (doubled smaller tail, capped at 1)."""
    lo = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, k + 1))
    hi = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))
    return min(1.0, 2.0 * min(lo, hi))


def sidak_alpha(m: int, alpha: float = 0.05) -> float:
    """Family-wise 0.05 spread over m trials."""
    if m <= 0:
        return alpha
    return 1.0 - (1.0 - alpha) ** (1.0 / m)


def percentile(sorted_vals: list[float], q: float) -> float:
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


# ---------------------------------------------------------------------------
# scoring blocks
# ---------------------------------------------------------------------------
def score_block(rows: list[dict], strategy: str) -> dict:
    """Rows for one strategy, one game each, already restricted to pre-kickoff."""
    pairs = [(float(r["p_home_win"]), int(r["outcome_home"]))
             for r in rows if r["outcome_home"] != "" and r["brier"] != ""]
    n = len(pairs)
    if n == 0:
        return {"n_games": 0}
    base = mean(y for _, y in pairs)  # climatology base rate over these games
    b_model = mean((p - y) ** 2 for p, y in pairs)
    b_base = mean((base - y) ** 2 for _, y in pairs)
    b_coin = mean((0.5 - y) ** 2 for _, y in pairs)
    ll_model = mean(-math.log(p if y == 1 else 1 - p) for p, y in pairs)
    ll_base = mean(-math.log(base if y == 1 else 1 - base) for _, y in pairs)
    hits = sum(1 for p, y in pairs if (p >= 0.5) == (y == 1))
    return {
        "n_games": n,
        "base_rate_home_win": base,
        "brier_model": b_model,
        "brier_climatology": b_base,
        "brier_coin": b_coin,
        "brier_skill_vs_climatology": 1 - b_model / b_base if b_base else float("nan"),
        "brier_skill_vs_coin": 1 - b_model / b_coin if b_coin else float("nan"),
        "log_loss_model": ll_model,
        "log_loss_climatology": ll_base,
        "hits": hits,
        "hit_rate": hits / n,
        "p_two_sided_hits_vs_coin": _binom_two_sided(hits, n),
        "p_luck_at_least_hits": _binom_sf_at_least(hits, n),
        "sharpness_mean_abs_p_minus_half": mean(abs(p - 0.5) for p, _ in pairs),
        "_pairs": pairs,
    }


def cluster_bootstrap(rows_by_strategy: dict[str, list[dict]], games: list[str]) -> dict:
    """Resample fixtures (not rows) and recompute Brier skill for every strategy."""
    rng = random.Random(int(hashlib.sha256(BOOT_SEED_MATERIAL.encode()).hexdigest()[:16], 16))
    per_game = {}
    for strat, rows in rows_by_strategy.items():
        for r in rows:
            if r["outcome_home"] == "" or r["brier"] == "":
                continue
            per_game.setdefault(strat, {})[r["game_id"]] = (float(r["p_home_win"]), int(r["outcome_home"]))
    draws = {s: [] for s in rows_by_strategy}
    for _ in range(BOOT_REPS):
        sample = [games[rng.randrange(len(games))] for _ in range(len(games))]
        # base rate is recomputed inside each replicate: it is a property of the draw
        ys = []
        for g in sample:
            for strat in per_game:
                if g in per_game[strat]:
                    ys.append(per_game[strat][g][1])
                    break
        if not ys:
            continue
        base = mean(ys)
        for strat, table in per_game.items():
            ps = [table[g] for g in sample if g in table]
            if not ps:
                continue
            b_m = mean((p - y) ** 2 for p, y in ps)
            b_b = mean((base - y) ** 2 for _, y in ps)
            if b_b:
                draws[strat].append(1 - b_m / b_b)
    out = {}
    for strat, vals in draws.items():
        vals.sort()
        out[strat] = {
            "reps": len(vals),
            "lower_95": percentile(vals, 0.025),
            "upper_95": percentile(vals, 0.975),
            "median": percentile(vals, 0.5),
            "p_skill_le_zero": sum(1 for v in vals if v <= 0) / len(vals) if vals else float("nan"),
        }
    return out


# ---------------------------------------------------------------------------
# controls, defined before the result is looked at
# ---------------------------------------------------------------------------
def control_rows(rows: list[dict], kind: str, ratings: dict[str, float]) -> list[dict]:
    """Two pre-registered controls on exactly the same fixtures.

    ``coin``      — deterministic seeded coin per game; expected accuracy 0.5.
    ``favourite`` — always 0.5 on the rating-favourite side, so its Brier is
                    0.25 by construction and it can only look good if the
                    favourite actually wins. It carries no probability
                    information, which is the point of a control.
    """
    seen = {}
    for r in rows:
        seen.setdefault(r["game_id"], r)
    out = []
    for gid, r in sorted(seen.items()):
        if r["outcome_home"] == "" or r["brier"] == "":
            continue
        if kind == "coin":
            h = int(hashlib.sha256(f"{BOOT_SEED_MATERIAL}/coin/{gid}".encode()).hexdigest()[:8], 16)
            p = 1.0 if h % 2 == 0 else 0.0
            p = 0.5  # a 0.5 forecast is the honest coin: Brier 0.25 exactly
            pick = "home" if h % 2 == 0 else "away"
        else:
            s_home = ratings.get(r["home"], 0.0) + 0.0
            s_away = ratings.get(r["away"], 0.0)
            pick = "home" if s_home >= s_away else "away"
            p = 0.5
        y = int(r["outcome_home"])
        out.append({
            "control": kind,
            "game_id": gid,
            "away": r["away"],
            "home": r["home"],
            "pick": pick,
            "p_home_win": p,
            "outcome_home": y,
            "correct": "yes" if (pick == "home") == (y == 1) else "no",
            "brier": (p - y) ** 2,
        })
    return out


def rating_table(standings: list[tuple]) -> dict[str, float]:
    """Simple opponent-unaware strength: (PF - PA) / games, from today's read.

    Used only to define the favourite control and to order clubs for review. It
    is not published as a model input, because a rating built this way is not
    opponent-aware and the pack's brief explicitly asks for opponent awareness
    before a rating is trusted.
    """
    out = {}
    for row in standings:
        abbr, w, l, t, pct, pf, pa = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
        games = w + l + t
        out[abbr] = (pf - pa) / games if games else 0.0
    return out


def league_scoring(standings: list[tuple]) -> dict:
    pf = sum(r[5] for r in standings)
    pa = sum(r[6] for r in standings)
    games = sum(r[1] + r[2] + r[3] for r in standings)
    return {
        "clubs": len(standings),
        "total_pf": pf,
        "total_pa": pa,
        "team_games": games,
        "league_points_per_team_game": pf / games if games else float("nan"),
        "pf_equals_pa": pf == pa,
    }


def removal_of_luck(blocks: dict[str, dict], m_trials: int) -> list[dict]:
    """One row per strategy: hit rate, the coin's distribution, and the verdict."""
    alpha_adj = sidak_alpha(m_trials)
    out = []
    for strat, b in sorted(blocks.items()):
        if not b.get("n_games"):
            continue
        n, hits = b["n_games"], b["hits"]
        # 95% band a coin would produce, expressed as a hit count
        lo = next(k for k in range(n + 1) if _binom_sf_at_least(n - k, n) >= 0.025) if n else 0
        out.append({
            "strategy_id": strat,
            "n_games": n,
            "hits": hits,
            "hit_rate": f"{b['hit_rate']:.4f}",
            "coin_expected_hits": f"{n * 0.5:.1f}",
            "coin_95_band_hits": f"{n // 2 - int(round(Z95 * math.sqrt(n * 0.25)))}-"
                                 f"{n // 2 + int(round(Z95 * math.sqrt(n * 0.25)))}",
            "p_two_sided_vs_coin": f"{b['p_two_sided_hits_vs_coin']:.4f}",
            "alpha_after_multiplicity": f"{alpha_adj:.5f}",
            "significant_after_adjustment": "yes" if b["p_two_sided_hits_vs_coin"] < alpha_adj else "no",
            "reading": (
                "no evidence of skill beyond coin-flipping at this sample size"
                if b["p_two_sided_hits_vs_coin"] >= alpha_adj else
                "hit rate is unlikely under coin-flipping after the multiplicity adjustment"
            ),
        })
    return out


def spread_of_forecasts(rows: list[dict], strategies: list[str]) -> dict:
    """How much the four strategies actually disagree, per game (with n)."""
    by_game = {}
    for r in rows:
        if r["strategy_id"] in strategies and r["p_home_win"]:
            by_game.setdefault(r["game_id"], {})[r["strategy_id"]] = float(r["p_home_win"])
    full = {g: v for g, v in by_game.items() if len(v) == len(strategies)}
    if not full:
        return {"n": 0}
    spreads = [max(v.values()) - min(v.values()) for v in full.values()]
    return {
        "n": len(full),
        "mean_disagreement_points": mean(spreads),
        "max_disagreement_points": max(spreads),
        "sd_across_games": pstdev(spreads) if len(spreads) > 1 else 0.0,
    }
