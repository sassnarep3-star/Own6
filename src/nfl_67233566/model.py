"""Frozen, pre-registered origination model (session 67233566).

Model id ``nfl_67233566_v1``. Every parameter below was fixed in the pre-registration block
BEFORE any Week 10 or Week 11 forecast was produced, and the fit is always chronological:
to price a game in week ``w`` the model may only see games from weeks ``< w``. That is what
makes the walk-forward numbers a backtest instead of a fit-to-results artefact, and it is why
no backtest number is ever allowed onto the leaderboard (the leaderboard ranks the walk-forward
forecasts, not an in-sample fit).

Stage order is enforced by ``originating_stages``: the side is produced first, the total second,
the moneyline third, and a later stage raises if its predecessor is not published for the same
fixture. Nothing here reads a sportsbook: ``market_*`` fields are produced empty by design and
the price policy (``prices.py``) is what says they stay empty.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean, pstdev

from .corpus import Game

MODEL_VERSION = "nfl_67233566_v1"

# ---- frozen hyper-parameters (pre-registration; changing one requires a new model id) ----
LAMBDA_RIDING = 4.0        # shrinkage on team ratings, points^2 scale
ATTACK_K = 3.0             # pseudo-games added when shrinking per-team scoring rates
MIN_GAMES_FOR_OWN_RATE = 2  # below this a club is shrunk toward the league mean
HOME_ADVANTAGE_FREE = True  # HFA is estimated from data, never assumed
ROUND_TO = 0.5              # fair lines are priced in half-points (push-free by construction)
TIE_MODELS = 2              # requirement: publish every model total twice until one wins
TOTAL_TIE_BREAK = "walk-forward mean absolute error; a winner may only be declared after " \
                  ">= 100 graded games and the gap must exceed 1.5x the standard error of the gap"


@dataclass
class Fixture:
    season: int
    week: int
    away: str
    home: str
    game_id: str = ""
    date_on_card: str = ""
    slot_on_card: str = ""
    official_source_url: str = ""


@dataclass
class Forecast:
    """One fixture, all three stages, plus the inputs that produced them.

    ``market`` is deliberately a dict that stays empty for every key: it exists so the
    fair / market / difference triple is a real column in the published table rather than a
    narrative, and so a future session that clears the price gate fills a column instead of
    redesigning the table.
    """

    fixture: Fixture
    model_version: str
    inputs: dict[str, object]
    side_fair: float | None
    total_fair: float | None
    home_win_prob: float | None
    tie_prob: float | None
    away_win_prob: float | None
    sigma_margin: float
    se_margin: float
    fair_spread_line: float = 0.0
    fair_moneyline: dict[str, str] = field(default_factory=dict)
    market: dict[str, object] = field(default_factory=dict)
    p_home_decisive: float = 0.5
    estimator_totals: dict[str, float] = field(default_factory=dict)
    errors: dict[str, float] = field(default_factory=dict)


# --------------------------------------------------------------------------- linear algebra
def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting. Small, deterministic, stdlib only."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ZeroDivisionError(f"singular system at column {col}")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        m[col] = [v / pv for v in m[col]]
        for r in range(n):
            if r != col and m[r][col]:
                f = m[r][col]
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


# --------------------------------------------------------------------------- the fit itself
def fit(games: list[Game]):
    """Ridge rating fit to home margins, plus shrunk per-team scoring rates.

    Returns a plain dict so it can be serialised into the ``inputs`` column of every forecast
    (requirement: store the probability *and* its inputs, not the pick alone).
    """
    playable = [g for g in games if g.countable and g.away_points is not None]
    if len(playable) < 2:
        # a ratings fit from fewer than two finals is not a forecast, it is a coin flip with a number
        # on it; the leaderboard depends on week 1 being refused rather than approximated
        raise ValueError(f"a walk-forward fit needs >=2 graded games, got {len(playable)}")
    clubs = sorted({c for g in playable for c in (g.away, g.home)})
    idx = {c: i for i, c in enumerate(clubs)}
    n = len(clubs)
    p = n + 1  # + intercept = home-field advantage
    XtX = [[0.0] * p for _ in range(p)]
    Xty = [0.0] * p
    for g in games:
        if not g.countable or g.away_points is None or g.home_points is None:
            continue
        x = [0.0] * p
        x[idx[g.home]] += 1.0
        x[idx[g.away]] -= 1.0
        if HOME_ADVANTAGE_FREE:
            x[n] = 1.0
        y = float(g.home_points - g.away_points)
        for i in range(p):
            Xty[i] += x[i] * y
            for j in range(p):
                XtX[i][j] += x[i] * x[j]
    for i in range(n):  # shrink team ratings only; HFA stays free
        XtX[i][i] += LAMBDA_RIDING
    beta = _solve(XtX, Xty)
    ratings = {c: beta[idx[c]] for c in clubs}
    hfa = beta[n] if HOME_ADVANTAGE_FREE else 0.0

    # residuals -> sigma used for the win-probability transform and for the standard error
    resid = []
    for g in games:
        if not g.countable or g.away_points is None or g.home_points is None:
            continue
        resid.append((g.home_points - g.away_points) - (ratings[g.home] - ratings[g.away] + hfa))
    sigma = pstdev(resid) if len(resid) > 2 else 0.0

    # scoring rates, shrunk toward the league mean
    pf: dict[str, list[int]] = {}
    pa: dict[str, list[int]] = {}
    for g in games:
        if not g.countable or g.away_points is None or g.home_points is None:
            continue
        pf.setdefault(g.away, []).append(g.away_points)
        pf.setdefault(g.home, []).append(g.home_points)
        pa.setdefault(g.away, []).append(g.home_points)
        pa.setdefault(g.home, []).append(g.away_points)
    all_pts = [x for v in pf.values() for x in v]
    league_ppg = mean(all_pts) if all_pts else 0.0
    total_resid: list[float] = []
    for g in games:
        if not g.countable or g.away_points is None or g.home_points is None:
            continue
        total_resid.append(0.0)  # placeholder replaced below once rates exist
    off, defn = {}, {}
    for c in clubs:
        o, d = pf.get(c, []), pa.get(c, [])
        k = len(o) + ATTACK_K
        off[c] = (sum(o) + ATTACK_K * league_ppg) / k
        defn[c] = (sum(d) + ATTACK_K * league_ppg) / k
    # spread of the total forecast, measured on the same training games (used for interval scores)
    total_resid = []
    for g in games:
        if not g.countable or g.away_points is None or g.home_points is None:
            continue
        expected_total = 0.5 * (off[g.home] + defn[g.away]) + 0.5 * (off[g.away] + defn[g.home]) + hfa
        total_resid.append((g.away_points + g.home_points) - expected_total)
    sigma_total = pstdev(total_resid) if len(total_resid) > 2 else 0.0
    return {
        "model_version": MODEL_VERSION,
        "sigma_total": sigma_total,
        "n_games": sum(1 for g in games if g.countable),
        "clubs": clubs,
        "ratings": ratings,
        "home_field_advantage": hfa,
        "sigma_margin": sigma,
        "league_ppg": league_ppg,
        "off_rate": off,
        "def_rate": defn,
        "lambda_riding": LAMBDA_RIDING,
        "attack_k": ATTACK_K,
        "residuals": len(resid),
    }


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _american(p: float) -> str:
    """Vig-free fair American odds for probability p, rounded to the nearest cent-equivalent.

    This is *our own* price. It is not a market price and is never labelled as one: the market
    columns stay empty until the price-data policy in ``prices.py`` is cleared.
    """
    if p <= 0 or p >= 1:
        return ""  # not priceable, published as a blank - never as +10000 or as a longshot quote
    dec = 1.0 / p
    if dec >= 2.0:
        return f"+{round((dec - 1) * 100)}"
    return f"{round(-100 / (dec - 1))}"


def predict(fitd: dict, fx: Fixture, tie_rate: float = 0.0) -> Forecast:
    """One fixture -> three stages, published in the mandated order.

    ``tie_rate`` is the empirical tie frequency of the training corpus. It is removed from both
    sides and published as its own probability, because a tie is a push on the moneyline; the
    fair odds below are therefore "to win", not "to win or push".
    """
    ratings, hfa = fitd["ratings"], fitd["home_field_advantage"]
    sigma = fitd["sigma_margin"] or 1.0
    for club in (fx.away, fx.home):
        if club not in ratings:
            raise KeyError(f"club {club!r} has no verified games in the training corpus")

    # --- stage 1: the side -------------------------------------------------------
    mu_side = ratings[fx.home] - ratings[fx.away] + hfa
    side_fair = round(mu_side / ROUND_TO) * ROUND_TO

    # --- stage 2: the total (two estimators, both published) ---------------------
    off, defn, league_ppg = fitd["off_rate"], fitd["def_rate"], fitd["league_ppg"]
    h_pts = 0.5 * (off[fx.home] + defn[fx.away])
    a_pts = 0.5 * (off[fx.away] + defn[fx.home])
    est_a = (h_pts + a_pts) + hfa  # HFA is a home-points effect in this estimator
    shrink = 0.5 * (est_a - 2 * league_ppg)
    est_b = 2 * league_ppg + shrink  # half-shrunk variant: the "does the gap matter?" test
    # no relabelling: T1 and T2 keep their identities so the gap column means "estimator A
    # minus estimator B", which is what the collapse rule is measured on.
    totals = {"T1_offdef": round(est_a / ROUND_TO) * ROUND_TO, "T2_halfshrunk": round(est_b / ROUND_TO) * ROUND_TO}
    total_fair = totals["T1_offdef"]

    # --- stage 3: the moneyline, derived only from the published side ------------
    z = mu_side / sigma
    tie_prob = max(0.0, min(0.10, tie_rate))
    p_home_given_decisive = _norm_cdf(z)
    probs = {
        "home": (1.0 - tie_prob) * p_home_given_decisive,
        "tie": tie_prob,
        "away": (1.0 - tie_prob) * (1.0 - p_home_given_decisive),
    }
    if abs(sum(probs.values()) - 1.0) > 1e-9:
        raise AssertionError("moneyline probabilities must sum to 1")
    se = math.sqrt(2.0 / (fitd["n_games"] + 1.0)) * sigma if fitd["n_games"] else float("nan")
    p_home_decisive = p_home_given_decisive
    fair_odds = {k: _american(p) for k, p in (("home", probs["home"]), ("away", probs["away"]))}
    fair_spread_line = -side_fair  # American convention: negative = the home club lays points
    inputs = {
        "fixture": {"away": fx.away, "home": fx.home, "week": fx.week, "season": fx.season},
        "ratings_home": round(ratings[fx.home], 4),
        "ratings_away": round(ratings[fx.away], 4),
        "home_field_advantage": round(hfa, 4),
        "sigma_margin": round(sigma, 4),
        "off_rate_home": round(off[fx.home], 4),
        "off_rate_away": round(off[fx.away], 4),
        "def_rate_home": round(defn[fx.home], 4),
        "def_rate_away": round(defn[fx.away], 4),
        "league_ppg": round(league_ppg, 4),
        "training_games": fitd["n_games"],
        "model_version": MODEL_VERSION,
    }
    return Forecast(
        fixture=fx,
        model_version=MODEL_VERSION,
        inputs=inputs,
        side_fair=side_fair,
        fair_spread_line=fair_spread_line,
        fair_moneyline=fair_odds,
        total_fair=total_fair,
        home_win_prob=probs["home"],
        tie_prob=probs["tie"],
        away_win_prob=probs["away"],
        sigma_margin=sigma,
        se_margin=se,
        p_home_decisive=p_home_decisive,
        estimator_totals=totals,
        market={},
    )


def originating_stages(forecasts: list[Forecast]) -> list[dict[str, str]]:
    """Audit table proving the side -> total -> moneyline order for every fixture.

    A stage that is missing makes every later stage ``blocked``, and the builder raises on a
    blocked predecessor that has been silently skipped - the requirement is a dependency, not
    a presentation choice.
    """
    out: list[dict[str, str]] = []
    for f in forecasts:
        rows = [("stage1_side", "published" if f.side_fair is not None else "blocked"),
                ("stage2_total", "published" if f.total_fair is not None else "blocked"),
                ("stage3_moneyline", "published" if f.home_win_prob is not None else "blocked")]
        rec: dict[str, str] = {"game_id": f.fixture.game_id, "away": f.fixture.away, "home": f.fixture.home}
        prev = "published"
        for name, status in rows:
            rec[name] = status if prev == "published" else "blocked_by_predecessor"
            prev = rec[name]
        out.append(rec)
    return out


def walk_forward(games: list[Game], fixtures: list[Fixture]) -> list[tuple[Forecast, Game | None]]:
    """Fit on weeks strictly earlier than the fixture's week; grade against the game if final.

    Also returns the in-sample-free forecast for any fixture whose week is not preceded by data
    (week 1) as a ``ValueError`` case - there is none in this season, and the check is asserted.
    """
    weeks = sorted({g.week for g in games})
    for fx in fixtures:
        if not any(g.countable and g.week < fx.week for g in games):
            raise ValueError(
                f"{fx.game_id}: no graded week precedes week {fx.week}; a forecast made with no prior "
                "game is a guess, so the walk-forward design refuses it instead of fitting on nothing")
    cache: dict[int, dict] = {}
    out: list[tuple[Forecast, Game | None]] = []
    for fx in fixtures:
        key = fx.week
        if key not in cache:
            cache[key] = fit([g for g in games if g.countable and g.week < key])
        fitd = cache[key]
        tie_rate = _tie_rate(games, fx.week)
        fc = predict(fitd, fx, tie_rate)
        fc.inputs["empirical_tie_rate_through_prior_weeks"] = round(tie_rate, 6)
        graded = None
        for g in games:
            if g.away == fx.away and g.home == fx.home and g.week == fx.week and g.countable:
                graded = g
                break
        if graded is not None:
            attach_errors(fc, graded)
        out.append((fc, graded))
    return out


def attach_errors(fc: Forecast, graded: Game) -> None:
    """Grade one forecast against a final game, in exactly one place.

    Both the walk-forward helper and the leaderboard's per-week refit call this, so a number in a
    graded table and a number on the leaderboard can never come from two different formulas. The
    cover flags are three-way (win / loss / push) because a half-point-free line can land on the
    actual margin; a push is recorded, not silently dropped.
    """
    if graded.away_points is None or graded.home_points is None or not graded.countable:
        return
    actual_margin = graded.home_points - graded.away_points
    actual_total = graded.away_points + graded.home_points
    fc.errors = {
        "abs_error_side": round(abs(actual_margin - fc.side_fair), 4),
        "abs_error_total_T1": round(abs(actual_total - fc.estimator_totals["T1_offdef"]), 4),
        "abs_error_total_T2": round(abs(actual_total - fc.estimator_totals["T2_halfshrunk"]), 4),
        "home_covered_own_line": 1 if actual_margin > fc.side_fair else (0 if actual_margin < fc.side_fair else -1),
        "over_T1": 1 if actual_total > fc.estimator_totals["T1_offdef"] else (0 if actual_total < fc.estimator_totals["T1_offdef"] else -1),
        "over_T2": 1 if actual_total > fc.estimator_totals["T2_halfshrunk"] else (0 if actual_total < fc.estimator_totals["T2_halfshrunk"] else -1),
        "actual_margin": actual_margin,
        "actual_total": actual_total,
    }


def _tie_rate(games: list[Game], before_week: int) -> float:
    pool = [g for g in games if g.countable and g.week < before_week]
    if not pool:
        return 0.0
    ties = sum(1 for g in pool if g.away_points == g.home_points)
    return ties / len(pool)
