"""Removal-of-luck panel.

Every headline number in this pack that could be produced by luck alone is
published twice: the observed value, and the distribution it would follow if
skill were exactly zero. The panel never deletes luck; it subtracts its
expectation and measures what remains against its standard deviation.
Math: exact binomial sums (no approximation libraries).
"""
from __future__ import annotations

import math

from .results import corpus_rows, standings_rows, team_totals, week10_finals


def binom_pmf(n, k, p):
    return math.comb(n, k) * (p ** k) * ((1.0 - p) ** (n - k))


def binom_ge(n, k, p):
    return sum(binom_pmf(n, i, p) for i in range(k, n + 1))


def binom_le(n, k, p):
    return sum(binom_pmf(n, i, p) for i in range(0, k + 1))


def wilson_ci(k, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    phat = k / n
    d = 1.0 + z * z / n
    c = phat + z * z / (2 * n)
    h = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def luck_band(n, p0=0.5, z=1.959963984540054):
    mu = n * p0
    sd = math.sqrt(n * p0 * (1 - p0))
    return mu, sd, mu - z * sd, mu + z * sd


def record_luck_panel():
    """One row per club: how much of the record would pure coin flips produce?

    p0 = 0.5 per decision (ties count 0.5). Two bands are shown: decisions
    only (ties excluded from n) and games with ties at 0.5.
    """
    games = [g for g in corpus_rows()] + week10_finals()
    stats = team_totals(games)
    out = []
    for row in standings_rows():
        t = row["team_abbr"]
        s = stats[t]
        n = s["w"] + s["l"]           # decided games
        ties = s["t"]
        k = s["w"]
        mu, sd, lo, hi = luck_band(n)
        z = (k - mu) / sd if sd else 0.0
        p_two = min(1.0, 2.0 * min(binom_ge(n, k, 0.5), binom_le(n, k, 0.5)))
        lo_ci, hi_ci = wilson_ci(k, n)
        out.append({
            "team_abbr": t, "games": s["g"], "decided": n, "ties": ties,
            "wins": k, "win_pct_decided": (k / n if n else None),
            "luck_expected_wins": round(mu, 2), "luck_sd": round(sd, 3),
            "luck_band_95_low": round(lo, 2), "luck_band_95_high": round(hi, 2),
            "wins_minus_luck": round(k - mu, 2), "z_vs_coin": round(z, 3),
            "two_sided_binomial_p": round(p_two, 4),
            "wilson_95_low": round(lo_ci, 4), "wilson_95_high": round(hi_ci, 4),
            "outside_95_luck_band": "yes" if (k > hi or k < lo) else "no",
            "method": "exact binomial p=0.5 on decided games; ties reported separately",
        })
    return out


def strategy_luck_panel(rows_hits):
    """rows_hits: list of dicts with strategy_id, n, hits, p0.

    Publishes the luck-adjusted hit rate (hits/n - p0) with its exact
    binomial two-sided p and a Wilson interval. Backtest-window rows are
    labelled as such by the caller and never reach the leaderboard.
    """
    out = []
    for r in rows_hits:
        n, k, p0 = r["n"], r["hits"], r["p0"]
        mu, sd, lo, hi = luck_band(n, p0)
        z = (k - mu) / sd if sd else 0.0
        p_two = min(1.0, 2.0 * min(binom_ge(n, k, p0), binom_le(n, k, p0)))
        lo_ci, hi_ci = wilson_ci(k, n)
        out.append({
            "strategy_id": r["strategy_id"], "window_label": r["window_label"],
            "n": n, "hits": k, "hit_rate": (k / n if n else None),
            "no_skill_rate": p0,
            "luck_expected_hits": round(mu, 3), "luck_sd": round(sd, 4),
            "luck_band_95_low": round(lo, 3), "luck_band_95_high": round(hi, 3),
            "hits_minus_luck": round(k - mu, 3),
            "hit_rate_minus_luck": round(k / n - p0, 4) if n else None,
            "z_vs_no_skill": round(z, 3),
            "two_sided_binomial_p": round(p_two, 5),
            "wilson_95_low": round(lo_ci, 4), "wilson_95_high": round(hi_ci, 4),
            "skill_after_luck_removal": (
                "indistinguishable from luck (p >= 0.05)" if p_two >= 0.05
                else "differs from no-skill at p < 0.05"),
        })
    return out


def luck_summary(panel):
    outside = [r for r in panel if r["outside_95_luck_band"] == "yes"]
    zmax = max(abs(r["z_vs_coin"]) for r in panel)
    return {
        "clubs": len(panel),
        "outside_95_luck_band": len(outside),
        "inside_95_luck_band": len(panel) - len(outside),
        "max_abs_z": round(zmax, 3),
        "clubs_outside": ", ".join(sorted(r["team_abbr"] for r in outside)),
        "reading": ("Each club's decided-game record is compared with the exact "
                    "binomial distribution a coin would produce over the same "
                    f"number of decisions. {len(outside)} of {len(panel)} clubs sit "
                    "outside the 95% luck band; the rest are statistically "
                    "indistinguishable from coin-flip records at this sample size."),
    }
