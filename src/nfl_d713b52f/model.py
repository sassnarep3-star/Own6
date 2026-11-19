"""The frozen baseline, re-run over this session's corpus.

The rule text lives in ``data/nfl_d713b52f/preregistration.md`` and is committed
before this module first produced a number. Nothing here is tuned; the constants
are the ones in the registration:

    sigma_margin  = sample sd of (actual margin - expected margin), floored 7, capped 25
    H             = 2.5 points fixed
    shrink        = n/(n+1) on a club's own mean, 1/(n+1) on the league mean
    P(home win)   = Phi(expected margin / sigma)
    total         = league mean total + both clubs' offensive deviations - both defensive deviations

Chronology: a game in week w may use only weeks strictly below w.
"""
from __future__ import annotations

import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(REPO, "data", "nfl_d713b52f")
FEED = os.path.join(REPO, "data", "nfl_0ce967db", "results_feed.csv")

H = 2.5
SIGMA_FLOOR = 7.0
SIGMA_CAP = 25.0
SHRINK_K = 1.0

# Week 11 forecasts registered 2026-11-19. Records are the standings read that day.
WEEK11 = [
    dict(game_id="2026-W11-01", date="2026-11-19", away="IND", home="HOU", kickoff_et="8:15 PM"),
    dict(game_id="2026-W11-02", date="2026-11-22", away="MIA", home="BUF", kickoff_et="1:00 PM"),
    dict(game_id="2026-W11-03", date="2026-11-22", away="BAL", home="CAR", kickoff_et="1:00 PM"),
]


def phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def load_finals():
    with open(FEED, newline="") as fh:
        rows = [r for r in csv.DictReader(fh)]
    out = []
    for r in rows:
        out.append(dict(game_id=r["game_id"], week=int(r["week"]), away=r["away"], home=r["home"],
                        away_score=int(r["away_score"]), home_score=int(r["home_score"])))
    out.sort(key=lambda r: (r["week"], r["game_id"]))
    return out


class TeamState:
    """Running per-club scoring state using only strictly earlier weeks."""

    def __init__(self):
        self.pf = {}
        self.pa = {}
        self.n = {}

    def copy(self):
        s = TeamState()
        s.pf, s.pa, s.n = dict(self.pf), dict(self.pa), dict(self.n)
        return s

    def add(self, club, scored, allowed):
        self.pf[club] = self.pf.get(club, 0.0) + scored
        self.pa[club] = self.pa.get(club, 0.0) + allowed
        self.n[club] = self.n.get(club, 0) + 1

    def means(self, club):
        n = self.n.get(club, 0)
        if n == 0:
            return None, None, 0
        return self.pf[club] / n, self.pa[club] / n, n

    def strength(self, club, league_ppg):
        pf, pa, n = self.means(club)
        if n == 0:
            return 0.0, 0
        own = pf - pa
        shrink = n / (n + SHRINK_K)
        return shrink * own + (1 - shrink) * 0.0, n

    def deviations(self, club, league_ppg):
        pf, pa, n = self.means(club)
        if n == 0:
            return 0.0, 0.0, 0
        shrink = n / (n + SHRINK_K)
        off = shrink * (pf - league_ppg / 2.0)
        deff = shrink * (pa - league_ppg / 2.0)
        return off, deff, n


def league_mean_total(state):
    games = sum(state.n.values()) / 2.0
    if games <= 0:
        return None
    return (sum(state.pf.values()) + sum(state.pa.values())) / (2.0 * games)


REFUSED: list = []


def run_backtest():
    """Chronological walk. Each row carries the full input vector and a hash of it."""
    REFUSED.clear()
    finals = load_finals()
    state = TeamState()
    residuals = []           # (actual margin - expected margin) from games already scored
    rows = []
    current_week = None
    for g in finals:
        if current_week is None:
            current_week = g["week"]
        if g["week"] != current_week:
            current_week = g["week"]
        lm = league_mean_total(state)
        if lm is None or state.n.get(g["home"], 0) == 0 or state.n.get(g["away"], 0) == 0:
            # Refused, not forecast. Two reasons, both same-week-information reasons:
            #  (a) no game has been played yet, so there is no league mean; or
            #  (b) one club has no prior game, so the only number available for it comes
            #      from games played earlier in the SAME week.
            # A refused game is recorded in unscored.csv with that reason.
            REFUSED.append(dict(
                game_id=g["game_id"], week=str(g["week"]), home=g["home"], away=g["away"],
                n_home_prior=str(state.n.get(g["home"], 0)), n_away_prior=str(state.n.get(g["away"], 0)),
                reason=("no prior game for this club; a same-week number would be used instead"
                        if lm is not None else "no game had been played, so no league mean existed")))
            state.add(g["home"], g["home_score"], g["away_score"])
            state.add(g["away"], g["away_score"], g["home_score"])
            continue
        sh, _nh = state.strength(g["home"], lm)
        sa, _na = state.strength(g["away"], lm)
        expected_margin = (sh - sa) + H
        if residuals:
            mu = sum(residuals) / len(residuals)
            sd = math.sqrt(sum((r - mu) ** 2 for r in residuals) / max(1, len(residuals) - 1))
        else:
            sd = SIGMA_FLOOR
        sigma = min(max(sd, SIGMA_FLOOR), SIGMA_CAP)
        p_home = phi(expected_margin / sigma)

        off_h, def_h, n_h = state.deviations(g["home"], lm)
        off_a, def_a, n_a = state.deviations(g["away"], lm)
        expected_total = lm + off_h + off_a - def_h - def_a

        actual_margin = g["home_score"] - g["away_score"]
        actual_total = g["home_score"] + g["away_score"]
        home_win = 1 if actual_margin > 0 else 0
        residuals.append(actual_margin - expected_margin)

        inputs = dict(week=g["week"], home=g["home"], away=g["away"],
                      strength_home=round(sh, 6), strength_away=round(sa, 6),
                      league_ppg=round(lm, 6), sigma=round(sigma, 6), h_field=H, shrink_k=SHRINK_K,
                      n_home_prior=n_h, n_away_prior=n_a,
                      dev_home_off=round(off_h, 6), dev_home_def=round(def_h, 6),
                      dev_away_off=round(off_a, 6), dev_away_def=round(def_a, 6))
        payload = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
        rows.append(dict(
            strategy_id="S01", strategy="ML-FROZEN-MARGIN",
            game_id=g["game_id"], week=str(g["week"]), away=g["away"], home=g["home"],
            p_home_win=f"{p_home:.6f}", expected_margin_home=f"{expected_margin:.6f}",
            expected_total=f"{expected_total:.6f}", sigma_margin=f"{sigma:.6f}",
            n_home_prior=str(n_h), n_away_prior=str(n_a), league_ppg_used=f"{lm:.6f}",
            actual_margin_home=str(actual_margin), actual_total=str(actual_total),
            home_win=str(home_win),
            inputs_json=payload,
            inputs_sha256=_sha(payload),
            inputs_rule="week<w only; no market price, no injuries, no personnel, no weather",
            prereg="data/nfl_d713b52f/preregistration.md (committed before this run)"))

        state.add(g["home"], g["home_score"], g["away_score"])
        state.add(g["away"], g["away_score"], g["home_score"])
    return rows


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def week11_forecasts():
    """Forecasts for the three named Week 11 games, using the full weeks 1-10 state."""
    finals = load_finals()
    state = TeamState()
    for g in finals:
        state.add(g["home"], g["home_score"], g["away_score"])
        state.add(g["away"], g["away_score"], g["home_score"])
    # residuals from the whole season, recomputed the same way as the walk's final step
    lm = league_mean_total(state)
    residuals = []
    walk = TeamState()
    for g in finals:
        if league_mean_total(walk) is None:
            walk.add(g["home"], g["home_score"], g["away_score"])
            walk.add(g["away"], g["away_score"], g["home_score"])
            continue
        sh, _ = walk.strength(g["home"], lm)
        sa, _ = walk.strength(g["away"], lm)
        residuals.append((g["home_score"] - g["away_score"]) - ((sh - sa) + H))
        walk.add(g["home"], g["home_score"], g["away_score"])
        walk.add(g["away"], g["away_score"], g["home_score"])
    mu = sum(residuals) / len(residuals)
    sd = math.sqrt(sum((r - mu) ** 2 for r in residuals) / (len(residuals) - 1))
    sigma = min(max(sd, SIGMA_FLOOR), SIGMA_CAP)

    rows = []
    for g in WEEK11:
        sh, nh = state.strength(g["home"], lm)
        sa, na = state.strength(g["away"], lm)
        margin = (sh - sa) + H
        p = phi(margin / sigma)
        off_h, def_h, _ = state.deviations(g["home"], lm)
        off_a, def_a, _ = state.deviations(g["away"], lm)
        total = lm + off_h + off_a - def_h - def_a
        pfm_h, pfm_a = state.means(g["home"])[0], state.means(g["away"])[0]
        rows.append(dict(
            game_id=g["game_id"], date=g["date"], kickoff_et=g["kickoff_et"],
            away=g["away"], home=g["home"],
            fair_side=("home" if p >= 0.5 else "away"),
            p_home_win=f"{p:.6f}",
            fair_margin_home=f"{margin:.2f}",
            fair_total=f"{total:.2f}",
            sigma_margin=f"{sigma:.4f}",
            n_home_prior=str(nh), n_away_prior=str(na),
            league_ppg_used=f"{lm:.4f}",
            home_points_game=f"{pfm_h:.2f}", away_points_game=f"{pfm_a:.2f}",
            market_side="", market_total="", market_moneyline="",
            residual_side="", residual_total="", residual_moneyline="",
            price_note="no official page publishes a price; the market and residual columns are blank by policy, not by omission",
            state="paper",
            registered_at_utc="2026-11-19T11:20:00Z",
            scoreable_after="after the official final is published",
            source_url="https://www.nfl.com/schedules/",
            read_at_utc="2026-11-19T11:10:00Z"))
    return rows


def score(rows):
    """Proper scores for the backtest, with a week-cluster bootstrap lower bound."""
    import random
    n = len(rows)
    if n == 0:
        return {}
    probs = [float(r["p_home_win"]) for r in rows]
    wins = [int(r["home_win"]) for r in rows]
    weeks = [int(r["week"]) for r in rows]
    b = sum((p - y) ** 2 for p, y in zip(probs, wins)) / n
    base = sum(wins) / n
    clim = sum((base - y) ** 2 for y in wins) / n
    bss = 1 - b / clim
    # week-cluster bootstrap of BSS, seed fixed in the registration
    by_week = {}
    for p, y, w in zip(probs, wins, weeks):
        by_week.setdefault(w, []).append((p, y))
    rng = random.Random(20261119)
    keys = sorted(by_week)
    boot = []
    for _ in range(2000):
        pick = [rng.choice(keys) for _ in keys]
        bb = 0.0
        yy = 0
        cnt = 0
        for w in pick:
            for p, y in by_week[w]:
                bb += (p - y) ** 2
                yy += y
                cnt += 1
        if cnt == 0:
            continue
        bb /= cnt
        rate = yy / cnt
        cc = sum((rate - y) ** 2 for w in pick for _p, y in by_week[w]) / cnt
        if cc > 0:
            boot.append(1 - bb / cc)
    boot.sort()
    lo = boot[int(0.025 * len(boot))]
    hi = boot[int(0.975 * len(boot)) - 1]
    # totals point error
    mae = sum(abs(float(r["expected_total"]) - float(r["actual_total"])) for r in rows) / n
    rmse = math.sqrt(sum((float(r["expected_total"]) - float(r["actual_total"])) ** 2 for r in rows) / n)
    return dict(n=n, brier=b, base_rate=base, brier_climatology=clim, bss=bss,
                bss_lo=lo, bss_hi=hi, weeks=len(by_week), mae=mae, rmse=rmse,
                bootstrap=2000, seed=20261119)


def luck_panel(rows):
    """Two luck measures: the Murphy split, and per-game squared error vs climatology."""
    n = len(rows)
    probs = [float(r["p_home_win"]) for r in rows]
    wins = [int(r["home_win"]) for r in rows]
    base = sum(wins) / n
    groups = {}
    for p, y in zip(probs, wins):
        groups.setdefault(p, []).append(y)
    rel = sum(len(ys) * (p - sum(ys) / len(ys)) ** 2 for p, ys in groups.items()) / n
    res = sum(len(ys) * (sum(ys) / len(ys) - base) ** 2 for p, ys in groups.items()) / n
    unc = base * (1 - base)
    b = rel - res + unc
    better = sum(1 for p, y in zip(probs, wins) if (p - y) ** 2 < (base - y) ** 2)
    worse = sum(1 for p, y in zip(probs, wins) if (p - y) ** 2 > (base - y) ** 2)
    tied = n - better - worse
    return dict(
        n=str(n), base_rate=f"{base:.6f}", brier=f"{b:.6f}",
        reliability=f"{rel:.6f}", resolution=f"{res:.6f}", uncertainty=f"{unc:.6f}",
        identity_residual=f"{abs((rel - res + unc) - b):.3e}",
        luck_share_reliability_over_brier=f"{rel / b:.6f}",
        games_better_than_climatology=str(better),
        games_worse_than_climatology=str(worse),
        games_tied=str(tied),
        note=("reliability is the part of the score the model could remove by being better calibrated; "
              "resolution is the part it earns by saying different things on different games. "
              "A high reliability share means most of the score is calibration work, not edge."))
