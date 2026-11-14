"""Line origination: side -> total -> moneyline.

The order is fixed by the operating requirement:

1. **Side**  - a least-squares power rating fitted on *verified* final
   margins from the official NFL scores pages.  Output: fair spread.
2. **Total** - a separate least-squares rating fitted on *verified* final
   totals from the same pages.  Output: fair total.
3. **Moneyline** - derived last, from the side and the total together:
   the win probability comes from the predicted margin plus the empirical
   residual distribution of the margin model (the total model supplies the
   correlated team-total legs used by same-game parlays).

Nothing here uses market odds, because no official (NFL-published) price
feed was readable in this session - see ``store.py``.
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

from . import dataset

RIDGE = 2.0  # regularisation on the team-rating block (points^2)


# ---------------------------------------------------------------- linear algebra
def _solve(a: List[List[float]], b: List[float]) -> List[float]:
    """Gauss-Jordan solve of a square system.  Raises on a singular matrix."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular normal equations")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(n):
            if r == col:
                continue
            f = m[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def _fit(rows: Sequence[Tuple[str, str, float]], teams: Sequence[str],
         ridge: float, home_adv: bool, intercept: bool) -> Dict[str, object]:
    """Least squares with sum-to-zero on the team block.

    ``rows`` is (team_a, team_b, y).  Design columns are
    ``coef(a) - coef(b)`` for a margin model and ``coef(a) + coef(b)``
    for a total model; ``sign`` is chosen by the caller through
    ``home_adv``/``intercept`` flags below.
    """
    idx = {t: i for i, t in enumerate(teams)}
    k = len(teams) - 1  # last team is the negative sum of the rest
    extra = (1 if home_adv else 0) + (1 if intercept else 0)
    p = k + extra
    a = [[0.0] * p for _ in range(p)]
    b = [0.0] * p
    sign = -1.0 if home_adv or not intercept else 1.0
    # margin model: +1 home, -1 away, +1 hfa  (no intercept)
    # total model:  +1 home, +1 away, +1 intercept (no hfa)
    for ta, tb, y in rows:
        cols: List[Tuple[int, float]] = []
        for t, s in ((ta, 1.0), (tb, sign)):
            j = idx[t]
            if j < k:
                cols.append((j, s))
            else:
                for jj in range(k):
                    cols.append((jj, -s))
        if home_adv:
            cols.append((k, 1.0))
        if intercept:
            cols.append((k + (1 if home_adv else 0), 1.0))
        for i, ci in cols:
            b[i] += ci * y
            for j, cj in cols:
                a[i][j] += ci * cj
    for i in range(k):
        a[i][i] += ridge
    x = _solve(a, b)
    rate = {teams[i]: x[i] for i in range(k)}
    rate[teams[k]] = -sum(x[:k])
    return {"rate": rate, "hfa": x[k] if home_adv else None,
            "intercept": x[k + (1 if home_adv else 0)] if intercept else None}


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ------------------------------------------------------------------- game views
def _games() -> List[Dict[str, object]]:
    out = []
    for r in dataset.results():
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        out.append({
            "week": int(r["week"]), "home": r["home_abbr"], "away": r["away_abbr"],
            "home_score": hs, "away_score": as_,
            "margin": hs - as_, "total": hs + as_,
            "game_slug": r["game_slug"], "source_url": r["official_source_url"],
        })
    return out


def fit_side(games: Sequence[Dict[str, object]]) -> Dict[str, object]:
    rows = [(g["home"], g["away"], float(g["margin"])) for g in games]
    teams = sorted(dataset.TEAM_NAMES)
    f = _fit(rows, teams, RIDGE, home_adv=True, intercept=False)
    resid = []
    for g in games:
        pred = f["rate"][g["home"]] - f["rate"][g["away"]] + f["hfa"]
        resid.append(g["margin"] - pred)
    return {"rate": f["rate"], "hfa": f["hfa"], "residuals": resid, "n": len(games)}


def fit_total(games: Sequence[Dict[str, object]]) -> Dict[str, object]:
    rows = [(g["home"], g["away"], float(g["total"])) for g in games]
    teams = sorted(dataset.TEAM_NAMES)
    f = _fit(rows, teams, RIDGE, home_adv=False, intercept=True)
    resid = []
    for g in games:
        pred = f["rate"][g["home"]] + f["rate"][g["away"]] + f["intercept"]
        resid.append(g["total"] - pred)
    return {"rate": f["rate"], "intercept": f["intercept"],
            "residuals": resid, "n": len(games)}


def american(prob: float) -> str:
    if prob <= 0.0 or prob >= 1.0:
        return ""
    if prob >= 0.5:
        return str(int(round(-100.0 * prob / (1.0 - prob))))
    return "+" + str(int(round(100.0 * (1.0 - prob) / prob)))


def win_prob_empirical(pred_margin: float, residuals: Sequence[float]) -> float:
    """Non-parametric win probability using the model's own residuals.

    Ties are split, which is why the empirical residual distribution is
    preferred here over a closed-form normal.
    """
    if not residuals:
        return ""
    wins = sum(1 for r in residuals if pred_margin + r > 0)
    ties = sum(1 for r in residuals if pred_margin + r == 0)
    return (wins + 0.5 * ties) / len(residuals)


# ------------------------------------------------------------------ origination
def originate(games=None, side=None, total=None) -> List[Dict[str, object]]:
    """Originate the side, then the total, then the moneyline."""
    games = games if games is not None else _games()
    side = side or fit_side(games)
    total = total or fit_total(games)
    out = []
    for g in dataset.slate():
        home, away = g["home_abbr"], g["away_abbr"]
        slug = g["game_slug"]
        # 1. side
        m_hat = side["rate"][home] - side["rate"][away] + side["hfa"]
        fair_spread = -m_hat                # spread quoted on the home team
        # 2. total
        t_hat = total["rate"][home] + total["rate"][away] + total["intercept"]
        # 3. moneyline, derived from the side using the model's residuals
        p_home = win_prob_empirical(m_hat, side["residuals"])
        p_home_norm = norm_cdf(m_hat / _sd(side["residuals"])) if _sd(side["residuals"]) else ""
        row = {
            "season": 2026, "week": 10, "game_slug": slug,
            "away_abbr": away, "home_abbr": home,
            "kickoff_date": g["kickoff_local_date"],
            "kickoff_et": g["kickoff_et"],
        }
        # Steps 1-3, each published as three separate columns: the model's
        # fair line, the market line, and the difference between them.
        for label, key, fair in (
            ("step_1_side_spread_home", "side", round(fair_spread, 2)),
            ("step_2_game_total", "total", round(t_hat, 2)),
            ("step_3_moneyline_home", "moneyline", american(p_home)),
        ):
            row[f"origination_{label}_fair_line"] = fair
            row[f"origination_{label}_market_line"] = ""
            row[f"origination_{label}_market_line_status"] = (
                "unverified_no_official_price")
            row[f"origination_{label}_difference"] = ""
            row[f"origination_{label}_difference_status"] = (
                "not_computable_market_line_blank")
        row.update({
            "origination_step_1_fair_margin_home": round(m_hat, 2),
            "origination_step_3_p_home_win_empirical": round(p_home, 4),
            "origination_step_3_p_home_win_normal": round(p_home_norm, 4) if p_home_norm != "" else "",
            "origination_step_3_fair_moneyline_away": american(1 - p_home),
            "derived_fair_team_total_home": round((t_hat + m_hat) / 2.0, 2),
            "derived_fair_team_total_away": round((t_hat - m_hat) / 2.0, 2),
            "model_residual_sd_margin": round(_sd(side["residuals"]), 3),
            "model_residual_sd_total": round(_sd(total["residuals"]), 3),
            "training_games_n": side["n"],
            "inputs_source_url": g["official_source_url"],
            "ratings_source_url": "https://www.nfl.com/scores/2026/week-1",
            "market_line_source_url": "",
        })
        out.append(row)
    return out


def _sd(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mu = sum(xs) / n
    return math.sqrt(sum((x - mu) ** 2 for x in xs) / (n - 1))


# ------------------------------------------------------------ walk-forward test
def walk_forward(games: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Train on weeks <= k, score week k+1.  Reports error vs a naive baseline.

    The baseline predicts every game at the training home-field advantage
    (constant).  A model that cannot beat a constant is not a signal.
    """
    weeks = sorted({g["week"] for g in games})
    out = []
    for k in weeks[:-1]:
        nxt = weeks[weeks.index(k) + 1]
        train = [g for g in games if g["week"] <= k]
        test = [g for g in games if g["week"] == nxt]
        if len(train) < 20 or not test:
            continue
        s = fit_side(train)
        t = fit_total(train)
        base = sum(g["margin"] for g in train) / len(train)
        btotal = sum(g["total"] for g in train) / len(train)
        m_err, b_err, t_err, bt_err = [], [], [], []
        hits = 0
        for g in test:
            pm = s["rate"][g["home"]] - s["rate"][g["away"]] + s["hfa"]
            pt = t["rate"][g["home"]] + t["rate"][g["away"]] + t["intercept"]
            m_err.append(abs(g["margin"] - pm))
            b_err.append(abs(g["margin"] - base))
            t_err.append(abs(g["total"] - pt))
            bt_err.append(abs(g["total"] - btotal))
            if (pm > 0) == (g["margin"] > 0):
                hits += 1
        out.append({
            "train_through_week": k, "test_week": nxt,
            "official_source_url": "https://www.nfl.com/scores/2026/week-1",
            "train_n": len(train), "test_n": len(test),
            "mae_margin_model": round(sum(m_err) / len(m_err), 3),
            "mae_margin_baseline": round(sum(b_err) / len(b_err), 3),
            "mae_total_model": round(sum(t_err) / len(t_err), 3),
            "mae_total_baseline": round(sum(bt_err) / len(bt_err), 3),
            "ats_side_direction_hit": f"{hits}/{len(test)}",
        })
    return out
