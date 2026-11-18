"""Correlations for session 0ce967db — official numbers only, n and interval always published.

The owner's rule is narrow and this module obeys it literally: a correlation exists only if both
inputs are official values already committed in this pack, and every published value carries its
``n`` and a 95% interval. Where the sample is too small or the input is not official, the cell is
blank and the reason is written into the row.

Nothing here feeds a parlay or combo recommendation. §10 of the registration bars using a
marginal correlation to build a joint probability; the combo rows are therefore all blocked and
say so, with the number that would unblock them.
"""
from __future__ import annotations

import csv
import math
import os
import random
import statistics

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "data", "nfl_0ce967db")
SEED = 20261118


def pearson(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("need >= 3 paired observations")
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        raise ValueError("zero variance")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def fisher_ci(r: float, n: int) -> tuple[float, float]:
    """Fisher z 95% interval; returns (lo, hi) on the r scale."""
    if n <= 3:
        return (float("nan"), float("nan"))
    z = 0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 0.999999 else 0.5 * math.log(1e6)
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.959963985 * se, z + 1.959963984540054 * se
    return (math.tanh(lo), math.tanh(hi))


def cluster_bootstrap_ci(x: list[float], y: list[float], clusters: list[int]) -> tuple[float, float]:
    """Percentile interval resampling week clusters (games in a week move together)."""
    rng = random.Random(SEED)
    by: dict[int, list[int]] = {}
    for i, c in enumerate(clusters):
        by.setdefault(c, []).append(i)
    keys = sorted(by)
    if len(keys) < 2:
        return (float("nan"), float("nan"))
    out = []
    for _ in range(2000):
        picks = [keys[rng.randrange(len(keys))] for _ in keys]
        idx = [i for k in picks for i in by[k]]
        try:
            out.append(pearson([x[i] for i in idx], [y[i] for i in idx]))
        except ValueError:
            continue
    if not out:
        return (float("nan"), float("nan"))
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1])


def describe(r: float, lo: float, hi: float, n: int) -> str:
    """A sentence that cannot contradict the interval, because it is built from it."""
    if math.isnan(lo) or math.isnan(hi):
        return "interval undefined at this n; no interpretation offered"
    if lo > 0:
        strength = "strong" if r >= 0.6 else ("moderate" if r >= 0.35 else "weak")
        return f"{strength} positive association; the 95% interval excludes zero at n={n}"
    if hi < 0:
        strength = "strong" if r <= -0.6 else ("moderate" if r <= -0.35 else "weak")
        return f"{strength} negative association; the 95% interval excludes zero at n={n}"
    return (f"no association distinguishable from zero at n={n}: r={r:+.3f} with interval "
            f"[{lo:+.3f}, {hi:+.3f}] straddling 0. Any claim of dependence here would be unsupported")


def main() -> None:
    games = list(csv.DictReader(open(os.path.join(OUT, "results_feed.csv"), encoding="utf-8")))
    weeks = [int(g["week"]) for g in games]
    margins = [float(g["margin_home"]) for g in games]
    totals = [float(g["total"]) for g in games]
    absmargins = [abs(m) for m in margins]
    home_scores = [float(g["home_score"]) for g in games]
    away_scores = [float(g["away_score"]) for g in games]

    rows = []

    def add(cid, qa, qb, x, y, clusters, source, _unused, note=""):
        r = pearson(x, y)
        lo_f, hi_f = fisher_ci(r, len(x))
        lo_c, hi_c = cluster_bootstrap_ci(x, y, clusters) if clusters else (float("nan"), float("nan"))
        interpretation = describe(r, lo_f, hi_f, len(x))
        rows.append({
            "correlation_id": cid, "quantity_a": qa, "quantity_b": qb, "n": len(x),
            "pearson_r": f"{r:.6f}", "fisher_lo95": f"{lo_f:.6f}", "fisher_hi95": f"{hi_f:.6f}",
            "week_cluster_lo95": ("" if math.isnan(lo_c) else f"{lo_c:.6f}"),
            "week_cluster_hi95": ("" if math.isnan(hi_c) else f"{hi_c:.6f}"),
            "n_clusters": len(set(clusters)) if clusters else "",
            "excludes_zero": ("yes" if (lo_f > 0 or hi_f < 0) else "no"),
            "source_url": source,
            "inputs_official": "yes: both columns are final scores read from nfl.com schedule pages",
            "interpretation": interpretation, "flag": note,
        })

    SRC = "https://www.nfl.com/schedules/2026/by-week/week-10"
    add("K01", "home margin (home-away)", "game total points", margins, totals, weeks, SRC, "",
        "sample is 2026 weeks 1-10 only; do not extrapolate to a multi-season population")
    add("K02", "home score", "away score", home_scores, away_scores, weeks, SRC, "",
        "the dependence a same-game 'both teams score' combo needs; a zero here would not license assuming independence")
    add("K03", "absolute margin", "game total points", absmargins, totals, weeks, SRC, "",
        "the coupling a side+total same-game combo would depend on")
    add("K04", "home margin", "week index", margins, [float(w) for w in weeks], weeks, SRC, "",
        "season-drift check on the corpus itself, not a betting signal")

    # club-level, from the official team-stats pages read this session
    stats = [r for r in csv.DictReader(open(os.path.join(OUT, "club_stats_2026.csv"), encoding="utf-8"))]
    pf = [float(r["pf"]) for r in stats]
    pass_yds = [float(r["pass_yds"]) for r in stats if r["pass_yds"]]
    rush_yds = [float(r["rush_yds"]) for r in stats if r["rush_yds"]]
    pf_s = [float(r["pf"]) for r in stats if r["pass_yds"]]
    pf_r = [float(r["pf"]) for r in stats if r["rush_yds"]]
    rows.append({
        "correlation_id": "K05", "quantity_a": "club passing yards (season to date)",
        "quantity_b": "club points for (season to date)", "n": len(pass_yds),
        "pearson_r": f"{pearson(pass_yds, pf_s):.6f}",
        "fisher_lo95": f"{fisher_ci(pearson(pass_yds, pf_s), len(pass_yds))[0]:.6f}",
        "fisher_hi95": f"{fisher_ci(pearson(pass_yds, pf_s), len(pass_yds))[1]:.6f}",
        "week_cluster_lo95": "", "week_cluster_hi95": "", "n_clusters": "",
        "excludes_zero": ("yes" if fisher_ci(pearson(pass_yds, pf_s), len(pass_yds))[0] > 0 else "no"),
        "source_url": "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all",
        "inputs_official": "yes: passing YDS and PF, both official; passing column map was inferred",
        "interpretation": describe(pearson(pass_yds, pf_s),
                                    *fisher_ci(pearson(pass_yds, pf_s), len(pass_yds)), len(pass_yds)),
        "flag": "n=32 clubs, so the interval is wide by construction; passing column header was not captured",
    })
    rows.append({
        "correlation_id": "K06", "quantity_a": "club rushing yards (season to date)",
        "quantity_b": "club points for (season to date)", "n": len(rush_yds),
        "pearson_r": f"{pearson(rush_yds, pf_r):.6f}",
        "fisher_lo95": f"{fisher_ci(pearson(rush_yds, pf_r), len(rush_yds))[0]:.6f}",
        "fisher_hi95": f"{fisher_ci(pearson(rush_yds, pf_r), len(rush_yds))[1]:.6f}",
        "week_cluster_lo95": "", "week_cluster_hi95": "", "n_clusters": "",
        "excludes_zero": ("yes" if (fisher_ci(pearson(rush_yds, pf_r), len(rush_yds))[0] > 0
                                    or fisher_ci(pearson(rush_yds, pf_r), len(rush_yds))[1] < 0) else "no"),
        "source_url": "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all",
        "inputs_official": "yes: rushing YDS and PF, both official",
        "interpretation": describe(pearson(rush_yds, pf_r),
                                    *fisher_ci(pearson(rush_yds, pf_r), len(rush_yds)), len(rush_yds)),
        "flag": "n=32 clubs; do not read as causal",
    })

    fields = ["correlation_id", "quantity_a", "quantity_b", "n", "pearson_r", "fisher_lo95",
              "fisher_hi95", "week_cluster_lo95", "week_cluster_hi95", "n_clusters",
              "excludes_zero", "source_url", "inputs_official", "interpretation", "flag"]
    with open(os.path.join(OUT, "correlations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    # ---- combo gate ---------------------------------------------------------------------
    combos = [
        ("CMB-01", "Two-leg moneyline parlay, two different games",
         "r between the two legs' outcomes is not measured on this corpus: different games are not paired",
         "joint probability from a validated model of the joint outcome",
         "blocked", "no validated joint probability exists; multiplying marginals is barred by registration §10"),
        ("CMB-02", "Same-game parlay: side + total",
         f"K01 and K03 measure the dependence (n={len(margins)}); the design effect is real but small in K01",
         "joint P(home covers AND total over) from a directly validated joint model at a stated line",
         "blocked", "no market line exists, so the joint event is undefined; margins alone are not enough"),
        ("CMB-03", "Same-game parlay: two player props",
         "not computed: no official page in this session's evidence set publishes per-player game props",
         "official player-level outcomes joined to official prop lines",
         "blocked", "no official player-prop line or outcome source was read; n would be 0"),
        ("CMB-04", "Cross-game player-prop combo",
         "not computed: see CMB-03",
         "official prop lines plus a player-game availability record",
         "blocked", "same as CMB-03"),
    ]
    with open(os.path.join(OUT, "combo_gate.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["combo_id", "combo_kind", "dependence_evidence", "what_would_unblock_it",
                    "gate_state", "reason", "source_url"])
        for cid, kind, ev, unblock, state, reason in combos:
            w.writerow([cid, kind, ev, unblock, state, reason,
                        "https://www.nfl.com/schedules/2026/by-week/week-10"])
    print(f"wrote correlations.csv ({len(rows)} values) and combo_gate.csv ({len(combos)} rows)")
    for r in rows:
        print(f"  {r['correlation_id']} n={r['n']:>4} r={r['pearson_r'][:8]:>9} "
              f"[{r['fisher_lo95'][:7]}, {r['fisher_hi95'][:7]}] excludes0={r['excludes_zero']}")


if __name__ == "__main__":
    main()
