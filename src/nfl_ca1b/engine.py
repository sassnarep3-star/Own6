"""Origination engine: ratings -> probabilities -> grading -> leaderboard gates.

Design commitments (all of them are brief requirements):
  * every output row stores a probability AND the complete input vector;
  * the leaderboard separates SIGNAL (proper-score skill) from STAKING (ROI/CLV),
    and staking stays blank while no price exists;
  * control baselines (coin, home-always, rating-favourite) run in the same pass;
  * luck is removed with an exact binomial two-sided test, never eyeballed;
  * a strategy must clear a prospective sample AND a confidence interval that
    excludes zero before it can be promoted; otherwise it is paper-only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import pathlib
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from . import capture
from .ratings import (ridge_fit, fit_sigma, total_sigma, margin_hat, win_prob,
                      expected_points, phi_inv)

ROOT = pathlib.Path(__file__).resolve().parents[2]
CORPUS = ROOT / "data/nfl_8362b702/corpus_136.csv"
WEEK10 = ROOT / "data/nfl_8362b702/results_week10.csv"


# ------------------------------------------------------------------ game log
def load_games() -> List[Tuple[str, str, int, int, str]]:
    """(away, home, away_score, home_score, source_tag) — official FINAL cards only."""
    out = []
    with CORPUS.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("away_score") and r.get("home_score"):
                out.append((r["away"], r["home"], int(r["away_score"]),
                            int(r["home_score"]), "pack8362b702 corpus week %s" % r["week"]))
    with WEEK10.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if r.get("away_score") and r.get("home_score"):
                out.append((r["away"], r["home"], int(r["away_score"]),
                            int(r["home_score"]), "pack8362b702 week10 final"))
    for gid, away, home, a_s, h_s in capture.NEW_FINALS:
        out.append((away, home, a_s, h_s, "this session week10 %s read 2026-11-17T00:41Z" % gid))
    return out


def teams() -> List[str]:
    return sorted(capture.STANDINGS)


# ------------------------------------------------------------------ scoring
def brier(p: float, y: int) -> float:
    return (p - float(y)) ** 2


def logloss(p: float, y: int) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def wilson(k: int, n: int, z: float = 1.959964) -> Tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact binomial two-sided p-value (sum of pmf <= pmf(observed))."""
    def pmf(i):
        return math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    obs = pmf(k)
    tot = 0.0
    for i in range(n + 1):
        v = pmf(i)
        if v <= obs * (1 + 1e-12):
            tot += v
    return min(1.0, tot)


def poisson_binomial(ps: Sequence[float], hits: int) -> Tuple[float, float, float]:
    """(expected hits, sd, two-sided p) under the model's OWN probabilities.

    This is the demanding luck test: it asks whether the realisations are
    consistent with the probabilities we published, not merely with a coin.
    """
    n = len(ps)
    dist = [1.0]
    for p in ps:
        nxt = [0.0] * (len(dist) + 1)
        for i, v in enumerate(dist):
            nxt[i] += v * (1 - p)
            nxt[i + 1] += v * p
        dist = nxt
    exp = sum(ps)
    var = sum(p * (1 - p) for p in ps)
    obs = dist[hits] if 0 <= hits < len(dist) else 0.0
    tot = 0.0
    for v in dist:
        if v <= obs * (1 + 1e-12):
            tot += v
    return exp, math.sqrt(var), min(1.0, tot)


# ------------------------------------------------------------- walk-forward
K_GRID = [round(1.0 + 0.05 * i, 2) for i in range(17)]
WARMUP = 48


def walk_forward(games: Sequence[Tuple[str, str, int, int, str]],
                 teams_: Sequence[str]) -> List[Dict[str, object]]:
    """Fit on every prior game, predict the next; k chosen only on older data.

    The k multiplier (a variance guard for the normal-approximation sigma) is
    selected on the last 40 games of the *training* window, which are always
    strictly older than the game being predicted. No future information enters.
    """
    rows: List[Dict[str, object]] = []
    for i in range(WARMUP, len(games)):
        train = [(g[0], g[1], g[2], g[3]) for g in games[:i]]
        p = ridge_fit(train, teams_)
        sig = fit_sigma(p, train)
        cut = max(24, len(train) - 40)
        inner_fit = [(g[0], g[1], g[2], g[3]) for g in games[:cut]]
        p_in = ridge_fit(inner_fit, teams_)
        s_in = fit_sigma(p_in, inner_fit)
        inner = [(g[0], g[1], g[2], g[3]) for g in games[cut:i]]
        best_k, best_s = 1.0, None
        for k in K_GRID:
            s = 0.0
            for a, h, a_s, h_s in inner:
                pr = win_prob(margin_hat(p_in, a, h), s_in * k)
                s += brier(pr, 1 if h_s > a_s else 0)
            if best_s is None or s < best_s:
                best_s, best_k = s, k
        a, h, a_s, h_s = games[i][:4]
        m = margin_hat(p, a, h)
        y = 1 if h_s > a_s else 0
        rows.append({
            "seq": i + 1, "away": a, "home": h, "away_score": a_s, "home_score": h_s,
            "margin_home": h_s - a_s, "margin_hat": m, "sigma": sig, "k": best_k,
            "p_home_raw": win_prob(m, sig), "p_home": win_prob(m, sig * best_k),
            "p_home_control_coin": 0.5,
            "y_home_win": y,
            "source_tag": games[i][4],
        })
    return rows


# ------------------------------------------------------------------ controls
def control_rows(wf: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Three benchmarks every run must carry: coin, always-home, climatology."""
    n = len(wf)
    home_rate = sum(int(r["y_home_win"]) for r in wf) / n
    fav = sum(1 for r in wf if (r["margin_hat"] > 0) == bool(r["y_home_win"])) / n
    rows = [
        {"control": "C0 coin-flip (p=0.500)", "n": n, "hits": sum(int(r["y_home_win"]) for r in wf) // 2 if False else "",
         "brier": sum(brier(0.5, int(r["y_home_win"])) for r in wf) / n,
         "logloss": sum(logloss(0.5, int(r["y_home_win"])) for r in wf) / n,
         "accuracy": "", "note": "no picks; p=0.5 on every game"},
        {"control": "C1 always-home", "n": n, "hits": sum(int(r["y_home_win"]) for r in wf),
         "brier": sum(brier(home_rate, int(r["y_home_win"])) for r in wf) / n,
         "logloss": sum(logloss(home_rate, int(r["y_home_win"])) for r in wf) / n,
         "accuracy": sum(int(r["y_home_win"]) for r in wf) / n,
         "note": "constant p = observed home-win rate; the accuracy of picking home every time"},
        {"control": "C2 rating-favourite (sign of margin_hat)", "n": n,
         "hits": sum(1 for r in wf if (r["margin_hat"] > 0) == bool(r["y_home_win"])),
         "brier": sum(brier(0.5, int(r["y_home_win"])) for r in wf) / n,
         "logloss": sum(logloss(0.5, int(r["y_home_win"])) for r in wf) / n,
         "accuracy": fav, "note": "pick the side the ratings favour; probability still 0.5, so Brier equals coin by construction"},
    ]
    return rows


# ---------------------------------------------------------------- luck panel
def luck_rows(wf: Sequence[Dict[str, object]], name: str,
              pick_fn) -> Dict[str, object]:
    """Exact binomial removal-of-luck record for one pick rule."""
    hits = 0
    n = 0
    for r in wf:
        pick, conf = pick_fn(r)
        if pick is None:
            continue
        n += 1
        if pick == bool(r["y_home_win"]):
            hits += 1
    p_val = binom_two_sided(hits, n) if n else float("nan")
    lo, hi = wilson(hits, n)
    ps = [float(r["p_home_pick"]) for r in wf if r.get("p_home_pick") is not None]
    if ps and len(ps) == n:
        exp_own, sd_own, p_own = poisson_binomial(ps, hits)
    else:
        exp_own, sd_own, p_own = "", "", ""
    return {
        "rule": name, "n_picks": n, "hits": hits,
        "expected_hits_under_own_p": exp_own, "sd_under_own_p": sd_own,
        "p_two_sided_vs_own_p": p_own,
        "own_p_verdict": ("" if exp_own == "" else
                          ("over-performs own probabilities" if hits > exp_own else
                           ("under-performs own probabilities" if hits < exp_own else "on expectation"))),
        "hit_rate": (hits / n) if n else "",
        "expected_under_coin": n / 2 if n else "",
        "excess_hits": hits - n / 2 if n else "",
        "wilson_lo": lo, "wilson_hi": hi,
        "exact_two_sided_p": p_val,
        "verdict": ("luck-compatible" if (n and p_val >= 0.05) else
                    ("signal beyond luck at 5%" if n else "no picks")),
    }


# -------------------------------------------------------------- correlations
def _pearson(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float]:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return (float("nan"), n)
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    return r, n


def _fisher_ci(r: float, n: int, z: float = 1.959964) -> Tuple[float, float]:
    if n <= 3 or abs(r) >= 1:
        return (float("nan"), float("nan"))
    zi = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    return (math.tanh(zi - z * se), math.tanh(zi + z * se))


def correlations(games: Sequence[Tuple[str, str, int, int, str]]) -> List[Dict[str, object]]:
    out = []
    # 1. same-game points: home vs away
    r, n = _pearson([g[3] for g in games], [g[2] for g in games])
    lo, hi = _fisher_ci(r, n)
    out.append({"corr_id": "CORR-01", "pair": "home points vs away points (same game)",
                "r": r, "n": n, "ci_lo": lo, "ci_hi": hi, "method": "Pearson, Fisher z 95% CI",
                "inputs": "official FINAL scores, weeks 1-10 (149 games)",
                "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
    # 2. margin vs total
    r, n = _pearson([g[3] - g[2] for g in games], [g[3] + g[2] for g in games])
    lo, hi = _fisher_ci(r, n)
    out.append({"corr_id": "CORR-02", "pair": "home margin vs game total",
                "r": r, "n": n, "ci_lo": lo, "ci_hi": hi, "method": "Pearson, Fisher z 95% CI",
                "inputs": "official FINAL scores, weeks 1-10",
                "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
    # 3. expected total (model) vs actual total
    t = teams()
    p = ridge_fit([(g[0], g[1], g[2], g[3]) for g in games], t)
    exp_t = [sum(expected_points(p, g[0], g[1])) for g in games]
    r, n = _pearson(exp_t, [g[2] + g[3] for g in games])
    lo, hi = _fisher_ci(r, n)
    out.append({"corr_id": "CORR-03", "pair": "model expected total vs actual total (in-sample)",
                "r": r, "n": n, "ci_lo": lo, "ci_hi": hi, "method": "Pearson, Fisher z 95% CI",
                "inputs": "official FINAL scores; model fitted on all 149 games (in-sample, optimistic)",
                "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
    # 4. model margin vs actual margin (in-sample)
    exp_m = [margin_hat(p, g[0], g[1]) for g in games]
    r, n = _pearson(exp_m, [g[3] - g[2] for g in games])
    lo, hi = _fisher_ci(r, n)
    out.append({"corr_id": "CORR-04", "pair": "model margin vs actual margin (in-sample)",
                "r": r, "n": n, "ci_lo": lo, "ci_hi": hi, "method": "Pearson, Fisher z 95% CI",
                "inputs": "official FINAL scores; in-sample",
                "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10"})
    # 5. week index vs total (scoring trend)
    weeks = []
    for r_ in csv.DictReader(CORPUS.open(newline="")):
        if r_.get("away_score"):
            weeks.append(int(r_["week"]))
    weeks += [10] * 9
    r, n = _pearson(weeks, [g[3] + g[2] for g in games])
    lo, hi = _fisher_ci(r, n)
    out.append({"corr_id": "CORR-05", "pair": "week number vs game total (scoring drift)",
                "r": r, "n": n, "ci_lo": lo, "ci_hi": hi, "method": "Pearson, Fisher z 95% CI",
                "inputs": "official FINAL scores with the week index from the official schedule",
                "source_url": "https://www.nfl.com/schedules/2026/by-week/week-1"})
    return out


# --------------------------------------------------------------- origination
def originate_week11(games: Sequence[Tuple[str, str, int, int, str]],
                     teams_: Sequence[str]) -> Tuple[List[Dict[str, object]], Dict[str, float]]:
    """Week-11 fair line per fixture + probability with the full input vector."""
    train = [(g[0], g[1], g[2], g[3]) for g in games]
    p = ridge_fit(train, teams_)
    sig = fit_sigma(p, train)
    tsig = total_sigma(p, train)
    wf = walk_forward(games, teams_)
    k_final = sorted(r["k"] for r in wf)[len(wf) // 2]  # prospective prior: median chosen k
    rows = []
    for (gid, day, date, time_et, net, away, home, venue, mark) in capture.WEEK11:
        m = margin_hat(p, away, home)
        ea, eh = expected_points(p, away, home)
        p_raw = win_prob(m, sig)
        p_cal = win_prob(m, sig * k_final)
        rows.append({
            "game_id": gid, "date": date, "day": day, "kickoff_et": time_et, "network": net,
            "away": away, "home": home, "neutral_site_event": mark,
            "atk_away": p["atk"][away], "def_away": p["def"][away],
            "atk_home": p["atk"][home], "def_home": p["def"][home],
            "hfa": p["hfa"], "lg_avg": p["lg_avg"], "sigma_margin": sig,
            "sigma_total": tsig, "k_calibration": k_final,
            "margin_hat": m, "fair_spread_home": -m, "fair_spread_away": m,
            "fair_spread_home_half": round((-m) * 2) / 2.0, "fair_spread_away_half": round(m * 2) / 2.0,
            "exp_total": ea + eh, "fair_total_half": round((ea + eh) * 2) / 2.0,
            "exp_away_pts": ea, "exp_home_pts": eh,
            "p_home_win_raw": p_raw, "p_home_win": p_cal, "p_away_win": 1 - p_cal,
            "fair_ml_home": _fair_ml(p_cal), "fair_ml_away": _fair_ml(1 - p_cal),
            "market_spread": "", "market_total": "", "market_ml_home": "", "market_ml_away": "",
            "diff_spread": "", "diff_total": "", "diff_ml_home": "", "diff_ml_away": "",
            "market_gate": "G-PRICE: no official NFL page publishes a price; blank by policy",
        })
    meta = {"lg_avg": p["lg_avg"], "hfa": p["hfa"], "sigma_margin": sig,
            "sigma_total": tsig, "k": k_final, "n_games": len(train)}
    return rows, meta


def _fair_ml(p: float) -> float:
    """Fair (no-vig) American odds implied by probability p. Display only."""
    if p <= 0 or p >= 1:
        return float("nan")
    if p >= 0.5:
        return round(-100.0 * p / (1 - p), 1)
    return round(100.0 * (1 - p) / p, 1)


def prereg_rows() -> List[Dict[str, object]]:
    """Strategy registrations. The rule text is hashed so any later edit is visible."""
    base = [
        dict(sid="S01", name="RATING-MARGIN singles (spread + ML, shadow)",
             division="singles",
             rule="Fit ridge offence/defence ratings on all official FINAL games to date; "
                  "p_home = Phi(margin_hat / (sigma * k)); k chosen on the last 40 training games. "
                  "One unit per game on the side with p >= 0.5. No totals, no props, no parlays.",
             edge_claim="opponent-aware margin model beats a coin on proper scores",
             mindchange_for="Brier skill vs coin > 0 with a game-cluster bootstrap 95% lower bound > 0 "
                            "on a prospective sample of >= 100 games",
             mindchange_against="lower bound <= 0 after 100 prospective games, or calibration slope "
                                "outside [0.8, 1.25] on the same sample"),
        dict(sid="S02", name="TOTAL-MARGIN singles (fair total, shadow)",
             division="singles",
             rule="Publish the model's fair total (exp_away + exp_home) for every fixture and compare it "
                  "with the official card only. No bet is placed while no price exists.",
             edge_claim="expected points carry information about the realised total",
             mindchange_for="CORR-03 out-of-sample correlation > 0 with 95% CI excluding 0",
             mindchange_against="CORR-03 out-of-sample CI includes 0 after 100 prospective games"),
        dict(sid="S03", name="GAME PARLAY: favourite ML + over (joint-copula)",
             division="game_parlays",
             rule="Only rankable when a directly validated JOINT probability exists; multiplying marginals "
                  "is forbidden by G-JOINT.",
             edge_claim="", mindchange_for="n_validated_joint >= 1 and void/push rules on file",
             mindchange_against="any leg of the joint uses a marginal product as its probability"),
        dict(sid="S04", name="SAME-GAME PARLAY: QB pass yards over + WR rec yards over",
             division="same_game_parlays",
             rule="Requires player-level official stats for every leg; blocked until G-PLAYERSTATS clears.",
             edge_claim="", mindchange_for=">= 100 player-games of official stat lines captured",
             mindchange_against="legs remain dependent through the same passing volume"),
        dict(sid="S05", name="PROP COMBO: two rushers over on the same team",
             division="prop_combos",
             rule="Same-team carries are negatively correlated; a combo may only be ranked with a "
                  "measured joint distribution, which needs snap/target shares (G-SNAP).",
             edge_claim="", mindchange_for="official snap counts for >= 8 games of the same backfield",
             mindchange_against="no snap-count source verified for the 32 clubs"),
    ]
    rows = []
    for r in base:
        text = "|".join([r["sid"], r["name"], r["division"], r["rule"], r["edge_claim"],
                         r["mindchange_for"], r["mindchange_against"]])
        rows.append({**r,
                     "registered_at_utc": "2026-11-17T00:00:00Z",
                     "registration_basis": "this file's first commit on branch arena/ca1b3769-own6",
                     "rule_sha256": hashlib.sha256(text.encode()).hexdigest()})
    return rows


def leaderboard(wf: Sequence[Dict[str, object]], totals_meta: Dict[str, float]):
    """Six divisions; signal and staking are separate columns and never mixed."""
    n = len(wf)
    # signal metrics
    p = [r["p_home"] for r in wf]
    y = [int(r["y_home_win"]) for r in wf]
    bs = sum(brier(a, b) for a, b in zip(p, y)) / n
    ll = sum(logloss(a, b) for a, b in zip(p, y)) / n
    skill = 1 - bs / 0.25
    # game-cluster bootstrap lower bound (deterministic LCG resampling)
    def lcg(seed, k):
        s = seed
        out = []
        for _ in range(k):
            s = (1103515245 * s + 12345) % (2 ** 31)
            out.append(s % n)
        return out
    samples = []
    for t in range(1000):
        idx = lcg(20261117 + t, n)
        b = sum(brier(p[j], y[j]) for j in idx) / n
        samples.append(1 - b / 0.25)
    samples.sort()
    lo, hi = samples[24], samples[974]
    m = 5  # multiplicity: strategies evaluated in this run
    adj = 1 - (1 - 0.05) ** (1.0 / m)
    rows = [{
        "rank": "", "strategy_id": "S01", "name": "RATING-MARGIN singles (shadow)",
        "division": "singles", "estimator": "walk_forward_ridge_hfa260_kmult",
        # G-BACKTEST: a backtest score is never a leaderboard number. The columns exist
        # so the shape is fixed, and they stay blank until a PROSPECTIVE settlement exists.
        "n_settled": 0, "brier": "", "logloss": "",
        "brier_skill_vs_coin": "", "cluster_boot_lo": "", "cluster_boot_hi": "",
        "backtest_reference": ("see backtest.html: %d walk-forward games, Brier skill %.4f "
                               "[cluster 95%% low %.4f] - NOT a rank" % (n, skill, lo)),
        "multiplicity_trials": m, "multiplicity_adjusted_alpha": adj,
        "signal_gate": ("FAIL: lower bound <= 0" if lo <= 0 else "PASS"),
        "roi": "", "clv": "", "staking_gate": "G-PRICE: no price exists, so ROI and CLV are blank",
        "eligible_for_reward": "no",
        "reward_note": "promotion requires prospective n>=100 with lower bound > 0",
    }]
    rows.append({
        "rank": "", "strategy_id": "S02", "name": "TOTAL-MARGIN (fair total only)",
        "division": "singles", "estimator": "same_ratings_total_equation",
        "n_settled": 0, "brier": "", "logloss": "",
        "brier_skill_vs_coin": "", "cluster_boot_lo": "", "cluster_boot_hi": "",
        "multiplicity_trials": m, "multiplicity_adjusted_alpha": adj,
        "signal_gate": "NOT RUN: totals have no official price and no binary outcome without a line",
        "roi": "", "clv": "", "staking_gate": "G-PRICE",
        "eligible_for_reward": "no",
        "reward_note": "publication only; cannot be scored as a bet without a price",
    })
    for sid, name, div in (("S03", "GAME PARLAY: favourite ML + over", "game_parlays"),
                           ("S04", "SGP: pass yards + rec yards", "same_game_parlays"),
                           ("S05", "PROP COMBO: two rushers over", "prop_combos")):
        rows.append({
            "rank": "", "strategy_id": sid, "name": name, "division": div,
            "estimator": "joint_copula_required", "n_settled": 0,
            "brier": "", "logloss": "", "brier_skill_vs_coin": "",
            "cluster_boot_lo": "", "cluster_boot_hi": "",
            "multiplicity_trials": m, "multiplicity_adjusted_alpha": adj,
            "signal_gate": "INELIGIBLE: joint-evidence gate open (G-JOINT)",
            "roi": "", "clv": "", "staking_gate": "G-JOINT + G-PRICE",
            "eligible_for_reward": "no",
            "reward_note": "multiplying marginals is forbidden; no rank is emitted",
        })
    return rows


def demotion_rules() -> List[Dict[str, object]]:
    return [
        dict(gate_id="D-01", scope="S01", to_state="paper", trigger="cluster-bootstrap 95% lower bound of Brier skill <= 0 after 100 prospective games", measured="not reached (n=0 prospective; backtest only)", action="demote and re-register the rule text before re-testing"),
        dict(gate_id="D-02", scope="S01", to_state="paper", trigger="calibration slope outside [0.80, 1.25] on the prospective sample", measured="in-sample slope is the k multiplier history; not yet measurable prospectively", action="refit sigma guard only; never refit on prospective data"),
        dict(gate_id="D-03", scope="S01", to_state="paper", trigger="decay: 8 consecutive settled picks at chance or worse", measured="not reached", action="freeze registrations, publish the losing run"),
        dict(gate_id="D-04", scope="any staking", to_state="paper", trigger="live ROI < 0 over 50 settled priced bets", measured="unmeasurable: no price exists (G-PRICE)", action="a staking run cannot carry a strategy that failed D-01"),
        dict(gate_id="D-05", scope="all", to_state="paper", trigger="a source re-read contradicts a stored value and the stored value was used in a published number", measured="0 such cases as of 2026-11-17 re-read (see conflicts.csv)", action="republish with the corrected value; the old row keeps its hash"),
    ]
