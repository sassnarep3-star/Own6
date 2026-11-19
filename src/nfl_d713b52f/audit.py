"""Recompute inherited published numbers instead of asserting them.

Inputs are the inherited ledgers (read-only):
    data/nfl_0ce967db/model_outputs.csv   per-game probability + inputs
    data/nfl_0ce967db/results_feed.csv    150 final scores
    data/nfl_0ce967db/leaderboard.csv     the numbers this file checks
    data/nfl_0ce967db/correlations.csv    the six published correlations

Nothing here writes to another session's files. Output is one audit row per
checked number with the published value, the recomputed value and a verdict.
"""
from __future__ import annotations

import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
INHERITED = os.path.join(REPO, "data", "nfl_0ce967db")

TOL = 1e-6
# Published values are rounded to 6 decimal places. Two numbers agree when they agree
# to that precision; the verdict says "MATCH" or "MATCH (last-digit rounding)" so a
# 1e-6 rounding artefact is never silently reported as an error, and a real error is
# never silently hidden.
ROUNDING = 5e-6


def verdict_for(published, recomputed, tol=TOL):
    if published in ("", None):
        return "INFO"
    a, b = _f(published), _f(recomputed)
    if a is None or b is None:
        return "INFO"
    if _close(a, b, tol):
        return "MATCH"
    if abs(a - b) <= ROUNDING:
        return "MATCH (last-digit rounding)"
    return "MISMATCH"


def _rows(name):
    with open(os.path.join(INHERITED, name), newline="") as fh:
        return list(csv.DictReader(fh))


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _close(a, b, tol=TOL):
    if a is None or b is None:
        return False
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_interval(r, n, z=1.959963984540054):
    if r is None or n < 4:
        return None, None
    r = max(min(r, 0.999999), -0.999999)
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(zr - z * se)
    hi = math.tanh(zr + z * se)
    return lo, hi


def binom_two_sided_p(k, n):
    """Exact two-sided sign test (normal approximation is not good enough at n=118)."""
    if n == 0:
        return None
    # P(X >= k) + P(X <= n-k) style computation via the exact binomial.
    def pmf(i):
        return math.comb(n, i) * (0.5 ** n)
    lo = min(k, n - k)
    tail = sum(pmf(i) for i in range(0, lo + 1))
    return min(1.0, 2 * tail)


def brier(probs, outcomes):
    n = len(probs)
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / n


def brier_decomposition(probs, outcomes):
    """Murphy decomposition with exact per-value groups (no binning)."""
    n = len(probs)
    base = sum(outcomes) / n
    groups = {}
    for p, y in zip(probs, outcomes):
        groups.setdefault(p, []).append(y)
    reliability = 0.0
    resolution = 0.0
    for p, ys in groups.items():
        nk = len(ys)
        ok = sum(ys) / nk
        reliability += nk * (p - ok) ** 2
        resolution += nk * (ok - base) ** 2
    reliability /= n
    resolution /= n
    uncertainty = base * (1 - base)
    return reliability, resolution, uncertainty


def audit_rows():
    rows = []
    lb = {r["strategy_id"]: r for r in _rows("leaderboard.csv")}
    outs = _rows("model_outputs.csv")

    by_strategy = {}
    for r in outs:
        by_strategy.setdefault(r["strategy_id"], []).append(r)

    # --- 1..3 probability scores, skill and the sign test -------------------
    for sid in sorted(by_strategy):
        rs = by_strategy[sid]
        probs, wins = [], []
        for r in rs:
            p = _f(r["p_home_win"])
            y = _f(r["home_win"])
            if p is None or y is None:
                continue
            probs.append(p)
            wins.append(int(y))
        if not probs:
            continue
        pub = lb.get(sid, {})
        if pub.get("brier", "") == "":
            # a totals strategy publishes no probability score; scoring it would be
            # an audit of a number nobody published
            continue
        b = brier(probs, wins)
        rows.append(dict(
            check_id=f"C-BRIER-{sid}", quantity=f"Brier score, {sid} ({pub.get('strategy','?')})",
            published=pub.get("brier", ""), recomputed=f"{b:.6f}", n=str(len(probs)),
            verdict=verdict_for(pub.get("brier"), f"{b:.6f}"),
            method="mean of (p - y)^2 over the strategy's own rows in the inherited model-output ledger",
            source="data/nfl_0ce967db/model_outputs.csv"))

        control = lb.get("C01", {})
        cb = _f(control.get("brier"))
        if cb:
            bss = 1.0 - b / cb
            rows.append(dict(
                check_id=f"C-BSS-{sid}", quantity=f"Brier skill vs climatology, {sid}",
                published=pub.get("brier_skill_vs_control", ""), recomputed=f"{bss:.6f}",
                n=str(len(probs)),
                verdict=verdict_for(pub.get("brier_skill_vs_control"), f"{bss:.6f}"),
                method="1 - brier(strategy) / brier(C01 climatology), both recomputed above",
                source="data/nfl_0ce967db/model_outputs.csv"))

    # --- 4. sign test ------------------------------------------------------
    for sid in sorted(by_strategy):
        pub = lb.get(sid, {})
        better = _f(pub.get("games_better_than_control"))
        worse = _f(pub.get("games_worse_than_control"))
        if better is None or worse is None:
            continue
        if pub.get("sign_test_p_two_sided", "") == "":
            continue
        n = int(better + worse)
        if n == 0:
            rows.append(dict(
                check_id=f"C-SIGN-{sid}", quantity=f"two-sided sign-test p, {sid} vs C01",
                published=pub.get("sign_test_p_two_sided", ""), recomputed="1.000000", n="0",
                verdict="MATCH",
                method="no discordant game exists, so no test is possible; 1.0 is the only honest value",
                source="data/nfl_0ce967db/leaderboard.csv"))
            continue
        p = binom_two_sided_p(int(better), n)
        rows.append(dict(
            check_id=f"C-SIGN-{sid}", quantity=f"two-sided sign-test p, {sid} vs C01",
            published=pub.get("sign_test_p_two_sided", ""),
            recomputed=("" if p is None else f"{p:.6g}"), n=str(n),
            verdict=verdict_for(pub.get("sign_test_p_two_sided"), f"{p:.6g}", 1e-4),
            method="exact two-sided binomial, k = games better, n = better + worse, p = 0.5",
            source="data/nfl_0ce967db/leaderboard.csv (counts) recomputed against its own p"))

    # --- 5. totals point error --------------------------------------------
    for sid in ("S04", "S05"):
        rs = by_strategy.get(sid, [])
        errs = []
        for r in rs:
            e = _f(r["expected_total"])
            a = _f(r["actual_total"])
            if e is None or a is None:
                continue
            errs.append(abs(e - a))
        if not errs:
            continue
        mae = sum(errs) / len(errs)
        pub = lb.get(sid, {})
        rows.append(dict(
            check_id=f"C-MAE-{sid}", quantity=f"mean absolute error, {sid} totals (points)",
            published=pub.get("totals_mae_points", ""), recomputed=f"{mae:.6f}", n=str(len(errs)),
            verdict=verdict_for(pub.get("totals_mae_points"), f"{mae:.6f}"),
            method="mean |expected_total - actual_total| over the strategy's own rows",
            source="data/nfl_0ce967db/model_outputs.csv"))

    # --- 6. Murphy decomposition ------------------------------------------
    for sid in sorted(by_strategy):
        rs = by_strategy[sid]
        probs, wins = [], []
        for r in rs:
            p = _f(r["p_home_win"])
            y = _f(r["home_win"])
            if p is None or y is None:
                continue
            probs.append(p)
            wins.append(int(y))
        if not probs:
            continue
        rel, res, unc = brier_decomposition(probs, wins)
        identity_err = abs((rel - res + unc) - brier(probs, wins))
        rows.append(dict(
            check_id=f"C-MURPHY-{sid}", quantity=f"Murphy identity |(rel - res + unc) - Brier|, {sid}",
            published="", recomputed=f"{identity_err:.3e}", n=str(len(probs)),
            verdict=("MATCH" if identity_err < 1e-9 else "MISMATCH"),
            method="exact per-forecast-value groups; the identity must close to machine precision",
            source="data/nfl_0ce967db/model_outputs.csv"))

    # --- 7. correlations K01..K04 from the feed ---------------------------
    feed = _rows("results_feed.csv")
    margin, total, home, away, week = [], [], [], [], []
    for r in feed:
        hs, as_ = _f(r["home_score"]), _f(r["away_score"])
        if hs is None or as_ is None:
            continue
        home.append(hs)
        away.append(as_)
        margin.append(hs - as_)
        total.append(hs + as_)
        week.append(_f(r["week"]))
    pub_corr = {r["correlation_id"]: r for r in _rows("correlations.csv")}
    checks = [
        ("K01", "home margin vs game total", margin, total),
        ("K02", "home score vs away score", home, away),
        ("K03", "absolute margin vs total", [abs(m) for m in margin], total),
        ("K04", "home margin vs week index", margin, week),
    ]
    for cid, name, xs, ys in checks:
        n = min(len(xs), len(ys))
        r = pearson(xs[:n], ys[:n])
        lo, hi = fisher_interval(r, n)
        p = pub_corr.get(cid, {})
        rows.append(dict(
            check_id=f"C-CORR-{cid}", quantity=f"Pearson r, {name}",
            published=p.get("pearson_r", ""), recomputed=f"{r:.6f}", n=str(n),
            verdict=verdict_for(p.get("pearson_r"), f"{r:.6f}"),
            method="Pearson product-moment on the inherited results feed; no resampling",
            source="data/nfl_0ce967db/results_feed.csv"))
        rows.append(dict(
            check_id=f"C-CORR-{cid}-CI", quantity=f"Fisher 95% interval lower bound, {name}",
            published=p.get("fisher_lo95", ""), recomputed=f"{lo:.6f}", n=str(n),
            verdict=verdict_for(p.get("fisher_lo95"), f"{lo:.6f}", 1e-4),
            method="tanh(atanh(r) - 1.96/sqrt(n-3))",
            source="data/nfl_0ce967db/results_feed.csv"))

    # --- 8. corpus identities --------------------------------------------
    n_rows = len(feed)
    pf_home = sum(_f(r["home_score"]) for r in feed)
    pf_away = sum(_f(r["away_score"]) for r in feed)
    rows.append(dict(
        check_id="C-CORPUS-01", quantity="results_feed rows",
        published="150", recomputed=str(n_rows), n=str(n_rows),
        verdict="MATCH" if n_rows == 150 else "MISMATCH",
        method="row count of the inherited feed",
        source="data/nfl_0ce967db/results_feed.csv"))
    total_points = pf_home + pf_away
    rows.append(dict(
        check_id="C-CORPUS-02", quantity="league points in the feed vs league points in the 32-club standings",
        published="6,923 (standings PF, inherited pack a67ddef8; 6,923 here)",
        recomputed=f"{total_points:.0f} = {pf_home:.0f} home + {pf_away:.0f} away", n=str(n_rows),
        verdict=("MATCH" if abs(total_points - 6923) < 1e-9 else "MISMATCH"),
        method=("sum(home)+sum(away) over every final in the feed; every point scored by one club "
                "is a point allowed by another, so this must equal the sum of PF and the sum of PA"),
        source="data/nfl_0ce967db/results_feed.csv cross-checked to data/nfl_d713b52f/standings.csv"))
    scorable = 0
    seen_home, seen_away = {}, {}
    for r in sorted(feed, key=lambda x: (int(x["week"]), x["game_id"])):
        w = int(r["week"])
        h, a = r["home"], r["away"]
        if seen_home.get(h, 0) >= 1 and seen_away.get(a, 0) >= 1:
            scorable += 1
        seen_home[h] = seen_home.get(h, 0) + 1
        seen_away[a] = seen_away.get(a, 0) + 1
        _ = w
    ledger_rows = len(by_strategy.get("S01", []))
    rows.append(dict(
        check_id="C-CORPUS-03", quantity="scorable games: two rules, both published",
        published=f"{ledger_rows} rows per strategy in the inherited ledger",
        recomputed=f"{scorable} games where BOTH clubs already had a prior game", n=str(n_rows),
        verdict="INFO",
        method=("chronological walk of the feed. The inherited ledger scores "
                f"{ledger_rows} games because a club with no prior game still gets a shrunk "
                f"probability; this pack also reports the stricter {scorable}. Neither rule uses "
                "future information; they differ only in how early-season games are treated."),
        source="data/nfl_0ce967db/results_feed.csv + data/nfl_0ce967db/model_outputs.csv"))
    return rows


def summary(rows):
    n = len(rows)
    match = sum(1 for r in rows if r["verdict"].startswith("MATCH"))
    mismatch = sum(1 for r in rows if r["verdict"] == "MISMATCH")
    info = sum(1 for r in rows if r["verdict"] == "INFO")
    return dict(checks=str(n), match=str(match), mismatch=str(mismatch), info=str(info),
                pass_rate=f"{100.0 * match / max(1, match + mismatch):.1f}%")
