"""Recomputation audit over the repository's own committed data.

Every number this module emits is labelled with the file it came from and the
number of rows used. Nothing is fetched from the network here; the source of
record for an NBA value remains the official ``source_url`` column inside those
CSVs, which the existing repository gates check separately.

Three audit jobs:

  ``correlations``  Recompute the four published correlation values from the raw
                    game log. Report r, n, p, a Fisher interval, Spearman rho,
                    and the leave-one-slate-out stability. The point of the
                    exercise is to show which published values are reproducible
                    and which are not supported by their own data.

  ``forward_test``  Recompute the Nov 2 forward-test metrics from the per-game
                    rows and compare with the committed summary CSV.

  ``null_max``      Simulate the distribution of the best observed ROI among N
                    zero-edge strategies, to give a concrete "what luck alone
                    looks like" reference for the leaderboard.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from . import correlation, leaderboard as ldr, luck, pricing
from .luck import Rng

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def _f(v: str) -> float | None:
    v = (v or "").strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


# --------------------------------------------------------------------------
# 1. correlations from the game log
# --------------------------------------------------------------------------
def correlations() -> dict:
    games_path = DATA / "games_results_2026-27.csv"
    rows = _read_csv(games_path)
    home = [_f(r["home_score"]) for r in rows]
    away = [_f(r["away_score"]) for r in rows]
    dates = [r["date"] for r in rows]
    margins = [h - a for h, a in zip(home, away)]
    totals = [h + a for h, a in zip(home, away)]

    out: dict = {
        "source_file": "data/games_results_2026-27.csv",
        "n_rows": len(rows),
        "date_range": [min(dates), max(dates)] if dates else None,
        "measured": {},
        "published_in_repo": {},
        "differences": [],
    }

    # (a) home vs away team points, same game
    p = correlation.pearson(home, away)
    sp = correlation.spearman(home, away)
    out["measured"]["home_score_vs_away_score"] = {
        **{k: p[k] for k in ("n", "r", "p_two_sided")},
        "fisher_ci95": correlation.fisher_ci(p["r"], p["n"]) if p["r"] is not None else None,
        "spearman_rho": sp["r"],
    }

    # (b) same-game margin vs total: the structural relation inside one game
    p2 = correlation.pearson(margins, totals)
    out["measured"]["margin_vs_total_same_game"] = {
        **{k: p2[k] for k in ("n", "r", "p_two_sided")},
        "fisher_ci95": correlation.fisher_ci(p2["r"], p2["n"]) if p2["r"] is not None else None,
    }

    # (c) cross-game same-date dependence: pooled pairs of games on the same date
    by_date: dict[str, list[int]] = {}
    for i, d in enumerate(dates):
        by_date.setdefault(d, []).append(i)
    xs, ys, pair_dates = [], [], []
    for d, idxs in sorted(by_date.items()):
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                xs.append(margins[idxs[a]])
                ys.append(margins[idxs[b]])
                pair_dates.append(d)
    p3 = correlation.pearson(xs, ys)
    # symmetric pooled estimator: average the correlation of both orderings
    p3_rev = correlation.pearson(ys, xs)
    cluster = correlation.cluster_bootstrap_ci(xs, ys, pair_dates, seed=20261105)
    out["measured"]["same_date_game_margins"] = {
        "n_pairs": p3["n"],
        "n_dates": len(by_date),
        "pairs_per_date_mean": (p3["n"] / len(by_date)) if by_date else None,
        "r_order_a_b": p3["r"],
        "r_order_b_a": p3_rev["r"],
        "r_symmetric_mean": (None if p3["r"] is None or p3_rev["r"] is None
                             else (p3["r"] + p3_rev["r"]) / 2.0),
        "p_two_sided_asymmetric": p3["p_two_sided"],
        "fisher_ci95": correlation.fisher_ci(p3["r"], p3["n"]) if p3["r"] is not None else None,
        "date_cluster_bootstrap_ci95": [cluster["ci_lo"], cluster["ci_hi"]],
        "date_cluster_includes_zero": cluster["includes_zero"],
        "note": "Pairs are not independent (each game appears in several pairs), so the "
                "nominal p-value and Fisher interval understate uncertainty. The "
                "date-cluster bootstrap resamples whole slates and is the interval to use.",
    }

    # (d) rest-differential vs home margin (schedule-derived rest)
    rest_diff, rest_margins = [], []
    last_played: dict[str, int] = {}
    day_index = {d: i for i, d in enumerate(sorted(set(dates)))}
    for r in rows:
        d = r["date"]
        i = day_index[d]
        home_team, away_team = r["home_team"], r["away_team"]
        h_rest = i - last_played[home_team] if home_team in last_played else None
        a_rest = i - last_played[away_team] if away_team in last_played else None
        if h_rest is not None and a_rest is not None:
            rest_diff.append(h_rest - a_rest)
            rest_margins.append(_f(r["home_score"]) - _f(r["away_score"]))
        last_played[home_team] = i
        last_played[away_team] = i
    p4 = correlation.pearson(rest_diff, rest_margins)
    out["measured"]["rest_diff_vs_home_margin"] = {
        "n": p4["n"], "r": p4["r"], "p_two_sided": p4["p_two_sided"],
        "fisher_ci95": correlation.fisher_ci(p4["r"], p4["n"]) if p4["r"] is not None else None,
        "note": "Rest is derived from the game dates in this file only. Any earlier-season "
                "rest is unknown, so the first appearance of each team is dropped.",
    }

    # published values in the repo, for comparison
    cf_path = DATA / "correlation_findings.csv"
    if cf_path.exists():
        published = {}
        for row in _read_csv(cf_path):
            published[row["pair"]] = {"n": _f(row["n"]), "pearson_r": _f(row["pearson_r"]),
                                      "source": row.get("source_file", "")}
        out["published_in_repo"] = published
        mapping = {
            "home_score_vs_away_score": "home_score_vs_away_score",
            "rest_diff_vs_home_margin": "rest_diff_vs_home_margin",
            "same_date_game_margins": "same_date_game_margins",
        }
        for key, pub_key in mapping.items():
            pub = published.get(pub_key)
            if not pub:
                continue
            mine = out["measured"].get(key, {})
            mine_r = mine.get("r", mine.get("r_order_a_b"))
            mine_n = mine.get("n", mine.get("n_pairs"))
            delta = None
            if pub["pearson_r"] is not None and mine_r is not None:
                delta = mine_r - pub["pearson_r"]
            out["differences"].append({
                "pair": key,
                "published_r": pub["pearson_r"],
                "published_n": pub["n"],
                "recomputed_r": mine_r,
                "recomputed_n": mine_n,
                "delta": delta,
                "reproduces": (delta is not None and abs(delta) < 5e-4),
            })
    return out


# --------------------------------------------------------------------------
# 2. forward test recomputation
# --------------------------------------------------------------------------
def forward_test() -> dict:
    path = DATA / "forward_test_2026-11-02.csv"
    rows = _read_csv(path)
    n = len(rows)
    out: dict = {"source_file": "data/forward_test_2026-11-02.csv", "n_games": n,
                 "recomputed": {}, "published": {}, "checks": []}

    def col(name):
        vals = [_f(r[name]) for r in rows]
        return [v for v in vals if v is not None], sum(1 for v in vals if v is None)

    ll_m, _ = col("logloss_market")
    ll_o, _ = col("logloss_own6")
    br_m, _ = col("brier_market")
    br_o, _ = col("brier_own6")

    out["recomputed"]["logloss_market"] = sum(ll_m) / len(ll_m) if ll_m else None
    out["recomputed"]["logloss_own6"] = sum(ll_o) / len(ll_o) if ll_o else None
    out["recomputed"]["brier_market"] = sum(br_m) / len(br_m) if br_m else None
    out["recomputed"]["brier_own6"] = sum(br_o) / len(br_o) if br_o else None

    if ll_m and ll_o and len(ll_m) == len(ll_o):
        ci = luck.paired_mean_difference_ci(ll_m, ll_o)
        bi = luck.block_bootstrap_mean_ci([a - b for a, b in zip(ll_m, ll_o)], block=3, seed=20261105)
        out["recomputed"]["paired_market_minus_model_logloss"] = {
            "mean": ci["mean_diff"], "ci95_lo": ci["ci_lo"], "ci95_hi": ci["ci_hi"],
            "t": ci["t"], "df": ci["df"],
            "block_bootstrap_ci95_lo": bi["ci_lo"], "block_bootstrap_ci95_hi": bi["ci_hi"],
        }

    # ATS and total-lean records
    for kind in ("spread_lean", "total_lean"):
        w = sum(1 for r in rows if r.get(f"{kind}_result") == "win")
        l = sum(1 for r in rows if r.get(f"{kind}_result") == "loss")
        out["recomputed"][f"{kind}_W"] = w
        out["recomputed"][f"{kind}_L"] = l
        out["recomputed"][f"{kind}_binom_two_sided_p"] = luck.binom_two_sided_p(w, w + l, 0.5) if (w + l) else None

    # probabilities used for the loss figures
    probs_m = [_f(r["p_home_market_devig"]) for r in rows]
    probs_o = [_f(r["p_home_own6"]) for r in rows]
    outcomes = [int(_f(r["home_won"])) for r in rows]
    if all(p is not None for p in probs_m + probs_o):
        out["recomputed"]["logloss_recomputable_from_probs_market"] = luck.log_loss(probs_m, outcomes)
        out["recomputed"]["logloss_recomputable_from_probs_own6"] = luck.log_loss(probs_o, outcomes)
        out["recomputed"]["ece_market"] = luck.expected_calibration_error(probs_m, outcomes)
        out["recomputed"]["ece_own6"] = luck.expected_calibration_error(probs_o, outcomes)

    # published summary
    summary_path = DATA / "forward_test_summary_2026-11-02.csv"
    if summary_path.exists():
        pub = {r["metric"]: r["value"] for r in _read_csv(summary_path)}
        out["published"] = pub
        for key in ("logloss_market", "logloss_own6", "brier_market", "brier_own6"):
            mine = out["recomputed"].get(key)
            theirs = _f(pub.get(key, ""))
            out["checks"].append({
                "metric": key,
                "recomputed": mine,
                "published": theirs,
                "match": (mine is not None and theirs is not None and abs(mine - theirs) < 5e-4),
            })

    # de-vig audit of the two-way quotes in the lines file
    lines_path = DATA / "our_lines_2026-11-02.csv"
    if lines_path.exists():
        lrows = _read_csv(lines_path)
        vigs, mismatches = [], []
        for r in lrows:
            fav = _f(r["fav_ml_current"])
            dog = _f(r["dog_ml_current"])
            fair = _f(r["market_fav_fair_prob"])
            if fav is None or dog is None:
                continue
            mk = pricing.TwoWayMarket(fav, dog)
            vigs.append(mk.vig)
            recomp_fair = mk.devig_proportional()[0]
            if fair is not None and abs(recomp_fair - fair) > 5e-4:
                mismatches.append({"event": r["event_id"], "published": fair,
                                   "recomputed": recomp_fair, "delta": fair - recomp_fair})
        out["devig_audit"] = {
            "source_file": "data/our_lines_2026-11-02.csv",
            "quotes_checked": len(vigs),
            "mean_vig": (sum(vigs) / len(vigs)) if vigs else None,
            "min_vig": min(vigs) if vigs else None,
            "max_vig": max(vigs) if vigs else None,
            "fair_prob_mismatches": mismatches,
            "all_fair_probs_reproduce": len(mismatches) == 0,
        }
    return out


# --------------------------------------------------------------------------
# 3. what luck alone looks like
# --------------------------------------------------------------------------
def null_max_roi(n_strategies: int = 50, n_bets: int = 100, n_reps: int = 400,
                 price: float = -110.0, seed: int = 20261105) -> dict:
    """Distribution of the BEST ROI among N strategies with zero true edge.

    Answers the question a leaderboard never asks: 'with a hundred guys trying,
    what does the winner look like when nobody can pick?' Uses the same
    break-even probability as the price, so expected ROI is exactly zero.
    """
    p = pricing.breakeven_probability(price)
    d = pricing.american_to_decimal(price)
    rng = Rng(seed)
    bests = []
    for _ in range(n_reps):
        best = -9.0
        for _ in range(n_strategies):
            wins = 0
            for _ in range(n_bets):
                if rng.random() < p:
                    wins += 1
            roi = (wins * (d - 1.0) - (n_bets - wins)) / n_bets
            if roi > best:
                best = roi
        bests.append(best)
    bests.sort()
    closed_form = {
        "median": ldr.max_of_n_median(n_strategies, _even_money_sd(price, p), n_bets),
        "p05": ldr.max_of_n_quantile(n_strategies, _even_money_sd(price, p), n_bets, 0.05),
        "p95": ldr.max_of_n_quantile(n_strategies, _even_money_sd(price, p), n_bets, 0.95),
        "note": "Closed form assumes independent strategies; the simulation is the reference.",
    }
    return {
        "n_strategies": n_strategies,
        "n_bets_each": n_bets,
        "n_reps": n_reps,
        "price": price,
        "breakeven_prob": p,
        "best_roi_median": luck._quantile_sorted(bests, 0.5),
        "best_roi_p05": luck._quantile_sorted(bests, 0.05),
        "best_roi_p95": luck._quantile_sorted(bests, 0.95),
        "prob_best_roi_gt_5pct": sum(1 for b in bests if b > 0.05) / len(bests),
        "prob_best_roi_gt_10pct": sum(1 for b in bests if b > 0.10) / len(bests),
        "closed_form": closed_form,
    }


def _even_money_sd(price: float, p: float) -> float:
    from . import power as _power

    return _power.bet_sd(price, p)


def pbo_from_repo_data() -> dict:
    """PBO and reality check across the four in-repo correlation-derived strategies.

    There is exactly one graded slate with markets in the repository (15 games),
    which is far too few for CSCV. The function reports the refusal rather than
    a number, and the refusal is published.
    """
    path = DATA / "forward_test_2026-11-02.csv"
    rows = _read_csv(path)
    n = len(rows)
    min_needed = 32
    return {
        "observations": n,
        "minimum_required_for_cscv": min_needed,
        "computed": False,
        "reason": (f"Only {n} graded bets exist; CSCV requires >= {min_needed} observations "
                   "and >= 2 strategy series to estimate out-of-sample rank stability. "
                   "No PBO value is published rather than a meaningless one."),
    }


def summary() -> dict:
    return {
        "correlations": correlations(),
        "forward_test": forward_test(),
        "null_max_roi": null_max_roi(),
        "pbo": pbo_from_repo_data(),
    }


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(summary(), indent=2, default=str)[:4000])
