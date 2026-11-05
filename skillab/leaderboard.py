"""Selection-bias and multiple-testing controls for a strategy leaderboard.

A leaderboard that shows the best of N tested strategies is a maximum of N
noisy numbers. These functions quantify and correct that:

  * ``bonferroni`` / ``holm``  — family-wise error control (statsmodels
    multipletests documents both; the implementations below are stdlib).
  * ``white_reality_check``    — Romano & Wolf (2005) bootstrap reality check
    against a benchmark, with the stationary bootstrap of Politis & Romano.
  * ``spa_test``               — Hansen (2005) test that is robust to many
    irrelevant strategies in the family.
  * ``deflated_sharpe``        — Bailey & Lopez de Prado (2014) probability a
    reported Sharpe is real given the number of trials and non-normality.
  * ``pbo``                    — probability of backtest overfitting via
    combinatorially symmetric cross-validation (Bailey, Borwein, Lopez de
    Prado, Zhu 2014).

These are published statistical methods. The equations below are stated in the
code and in the site; they are *not* claims that any strategy has skill.
"""
from __future__ import annotations

import math

from .luck import Rng, norm_cdf, norm_ppf, mean, sample_sd


# --------------------------------------------------------------------------
# family-wise error control
# --------------------------------------------------------------------------
def bonferroni(pvals: list[float], alpha: float = 0.05) -> dict:
    m = len(pvals)
    if m == 0:
        return {"m": 0, "adjusted": [], "reject": [], "alpha": alpha}
    adj = [min(1.0, p * m) for p in pvals]
    return {"m": m, "adjusted": adj, "reject": [a <= alpha for a in adj], "alpha": alpha}


def holm(pvals: list[float], alpha: float = 0.05) -> dict:
    """Holm step-down: uniformly more powerful than Bonferroni, same FWER control."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [1.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * pvals[idx])
        running = max(running, val)
        adjusted[idx] = min(1.0, running)
    return {"m": m, "adjusted": adjusted, "reject": [a <= alpha for a in adjusted], "alpha": alpha}


def bh_fdr(pvals: list[float], alpha: float = 0.05) -> dict:
    """Benjamini-Hochberg step-up FDR control (statsmodels 'fdr_bh')."""
    m = len(pvals)
    if m == 0:
        return {"m": 0, "adjusted": [], "reject": [], "alpha": alpha}
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [1.0] * m
    running = 1.0
    for rank in range(m - 1, -1, -1):
        idx = order[rank]
        val = min(1.0, pvals[idx] * m / (rank + 1))
        running = min(running, val)
        adjusted[idx] = min(1.0, running)
    return {"m": m, "adjusted": adjusted, "reject": [a <= alpha for a in adjusted], "alpha": alpha}


def effective_trials_from_rejected(m: int, rejected: int) -> float:
    """Rough share of a family that survived correction — reporting only."""
    if m == 0:
        return 0.0
    return rejected / m


def max_of_n_median(n_strategies: int, per_bet_sd: float, n_bets: int) -> float:
    """Median ROI of the BEST of N zero-edge strategies (closed form).

    Each strategy's mean return is approximately Normal(0, sd/sqrt(n)). For N
    independent strategies the CDF of the maximum is F(x)^N, so the median of
    the maximum solves F(x)^N = 0.5, i.e. x = (sd/sqrt(n)) * Phi^-1(0.5^(1/N)).
    This is the exact quantity a leaderboard is showing when it ranks the top
    of a family that has no skill in it.
    """
    if n_strategies < 1 or n_bets < 1:
        return float("nan")
    q = 0.5 ** (1.0 / n_strategies)
    return (per_bet_sd / math.sqrt(n_bets)) * norm_ppf(q)


def max_of_n_quantile(n_strategies: int, per_bet_sd: float, n_bets: int, p: float) -> float:
    """Quantile ``p`` of the best-of-N zero-edge ROI."""
    if n_strategies < 1 or n_bets < 1:
        return float("nan")
    q = p ** (1.0 / n_strategies)
    return (per_bet_sd / math.sqrt(n_bets)) * norm_ppf(q)


# --------------------------------------------------------------------------
# bootstrap reality check / SPA
# --------------------------------------------------------------------------
def _stationary_bootstrap_indices(n: int, rng: Rng, expected_block: float = 5.0) -> list[int]:
    """Politis-Romano stationary bootstrap: geometric block lengths."""
    p = 1.0 / max(expected_block, 1.0)
    idx: list[int] = []
    while len(idx) < n:
        if not idx or rng.random() < p:
            start = rng.randrange(n)
            idx.append(start)
        else:
            idx.append((idx[-1] + 1) % n)
    return idx[:n]


def performance_matrix(per_bet: list[list[float]], block: float = 5.0,
                       n_resamples: int = 1000, seed: int = 20261105) -> list[list[list[float]]]:
    """Resampled performance for every strategy using the SAME index draws.

    Using one index set per bootstrap replicate preserves cross-strategy
    correlation, which is what makes a max-statistic test valid.
    """
    if not per_bet:
        return []
    n = len(per_bet[0])
    for row in per_bet:
        if len(row) != n:
            raise ValueError("all strategies must be aligned to the same number of bets")
    rng = Rng(seed)
    out: list[list[list[float]]] = []
    for _ in range(n_resamples):
        idx = _stationary_bootstrap_indices(n, rng, block)
        out.append([[row[i] for i in idx] for row in per_bet])
    return out


def white_reality_check(per_bet: list[list[float]], names: list[str] | None = None,
                        block: float = 5.0, n_resamples: int = 1000,
                        seed: int = 20261105) -> dict:
    """Reality check for the null 'no strategy beats zero mean return'.

    Statistic V = max_k sqrt(n) * mean_k. Bootstrap the centred statistic
    V* = max_k sqrt(n) * (mean*_k - mean_k) and take p = P(V* >= V).
    """
    k = len(per_bet)
    if k == 0:
        return {"k": 0, "p_value": None}
    n = len(per_bet[0])
    obs_means = [mean(row) for row in per_bet]
    v_obs = max(math.sqrt(n) * m for m in obs_means)
    if n_resamples <= 0:
        return {"k": k, "n": n, "v_obs": v_obs, "p_value": None, "names": names}
    rng = Rng(seed)
    exceed = 0
    for _ in range(n_resamples):
        idx = _stationary_bootstrap_indices(n, rng, block)
        v_star = max(
            math.sqrt(n) * (mean([row[i] for i in idx]) - obs_means[j])
            for j, row in enumerate(per_bet)
        )
        if v_star >= v_obs:
            exceed += 1
    p = (exceed + 1) / (n_resamples + 1)
    return {
        "k": k,
        "n": n,
        "v_obs": v_obs,
        "p_value": p,
        "best_mean": max(obs_means),
        "best_index": obs_means.index(max(obs_means)),
        "names": names,
        "n_resamples": n_resamples,
        "block": block,
    }


def spa_test(per_bet: list[list[float]], block: float = 5.0, n_resamples: int = 1000,
             seed: int = 20261105, threshold_frac: float = 0.5) -> dict:
    """Hansen (2005) SPA: recentre only strategies above a threshold.

    Standardisation uses a bootstrap estimate of each strategy's standard
    error, so a single high-variance strategy cannot dominate the maximum.
    Returns a p-value for 'no strategy in the family has positive expected
    return' and is intentionally conservative when many strategies are noise.
    """
    k = len(per_bet)
    if k == 0:
        return {"k": 0, "p_value": None}
    n = len(per_bet[0])
    obs_means = [mean(row) for row in per_bet]
    # bootstrap standard errors
    se = []
    rng = Rng(seed + 1)
    for row in per_bet:
        draws = []
        for _ in range(200):
            s = 0.0
            for _ in range(n):
                s += row[rng.randrange(n)]
            draws.append(s / n)
        se.append(sample_sd(draws) or 1e-12)
    z = [m / s for m, s in zip(obs_means, se)]
    v_obs = max(z)
    # threshold rule (Hansen): strategies with z below -threshold are removed
    cut = -abs(threshold_frac) * math.sqrt(2.0 * math.log(math.log(max(n, 3))))
    active = [i for i in range(k) if z[i] >= cut]
    rng = Rng(seed)
    exceed = 0
    for _ in range(n_resamples):
        idx = _stationary_bootstrap_indices(n, rng, block)
        best = -1e18
        for i in active:
            row = per_bet[i]
            m_star = mean([row[j] for j in idx])
            g = m_star - obs_means[i]
            z_star = g / se[i]
            if z_star > best:
                best = z_star
        if best >= v_obs:
            exceed += 1
    return {
        "k": k,
        "n": n,
        "active": len(active),
        "v_obs": v_obs,
        "p_value": (exceed + 1) / (n_resamples + 1),
        "n_resamples": n_resamples,
        "block": block,
    }


# --------------------------------------------------------------------------
# deflated Sharpe ratio
# --------------------------------------------------------------------------
def deflated_sharpe(observed_sharpe: float, n_trials: int, n_obs: int,
                    skew: float = 0.0, kurtosis: float = 3.0) -> dict:
    """P(true Sharpe > 0) after correcting for the number of trials.

    SR0 = sqrt(Var(SR_trials)) * ((1-gamma)*Phi^-1(1-1/N) + gamma*Phi^-1(1-1/(N*e)))
    DSR = Phi( ((SR - SR0) * sqrt(n-1)) / sqrt(1 - skew*SR + (kurtosis-1)/4 * SR^2) )
    with gamma the Euler-Mascheroni constant and Var(SR_trials) approximated
    as 1/n_obs when the trial dispersion is not supplied (the conservative
    'all trials are independent noise' assumption).
    """
    if n_trials < 1 or n_obs < 2:
        return {"dsr": None, "reason": "insufficient arguments"}
    gamma = 0.5772156649015329
    var_sr = 1.0 / n_obs
    e = math.e
    if n_trials <= 1:
        # A single trial needs no selection adjustment: no maximum is being taken.
        sr0 = 0.0
    else:
        sr0 = math.sqrt(var_sr) * (
            (1.0 - gamma) * norm_ppf(1.0 - 1.0 / n_trials)
            + gamma * norm_ppf(1.0 - 1.0 / (n_trials * e))
        )
    denom = math.sqrt(max(1e-12, 1.0 - skew * observed_sharpe + (kurtosis - 1.0) / 4.0 * observed_sharpe ** 2))
    z = (observed_sharpe - sr0) * math.sqrt(n_obs - 1.0) / denom
    return {
        "dsr": norm_cdf(z),
        "sr0": sr0,
        "z": z,
        "n_trials": n_trials,
        "n_obs": n_obs,
        "observed_sharpe": observed_sharpe,
    }


# --------------------------------------------------------------------------
# probability of backtest overfitting (CSCV)
# --------------------------------------------------------------------------
def probability_of_overfitting(per_bet: list[list[float]], n_splits: int = 8,
                               max_combinations: int = 70) -> dict:
    """CSCV estimate of the probability that the in-sample winner underperforms.

    Split the timeline into S contiguous blocks. For every combination of S/2
    blocks as in-sample, rank strategies by in-sample Sharpe, take the winner,
    and record whether its out-of-sample rank is below the median. PBO is the
    frequency of that failure. Requires >= 2 strategies and enough
    observations to estimate a Sharpe in each half.
    """
    k = len(per_bet)
    if k < 2:
        return {"pbo": None, "reason": "needs >= 2 strategies"}
    n = len(per_bet[0])
    if n < n_splits * 4:
        return {"pbo": None, "reason": f"needs >= {n_splits * 4} observations, has {n}"}
    bounds = [round(i * n / n_splits) for i in range(n_splits + 1)]
    blocks = [(bounds[i], bounds[i + 1]) for i in range(n_splits)]

    def sharpe(rows: list[list[float]], idxs: list[int]) -> list[float]:
        out = []
        for row in rows:
            vals = [row[i] for i in idxs]
            sd = sample_sd(vals)
            out.append(mean(vals) / sd if sd > 0 else 0.0)
        return out

    import itertools

    combos = list(itertools.combinations(range(n_splits), n_splits // 2))
    if len(combos) > max_combinations:
        combos = combos[:max_combinations]
    failures = 0
    used = 0
    for combo in combos:
        is_idx, oos_idx = [], []
        for b, (s, e) in enumerate(blocks):
            (is_idx if b in combo else oos_idx).extend(range(s, e))
        if not is_idx or not oos_idx:
            continue
        sr_is = sharpe(per_bet, is_idx)
        sr_oos = sharpe(per_bet, oos_idx)
        best = max(range(k), key=lambda i: sr_is[i])
        rank = sum(1 for v in sr_oos if v < sr_oos[best])
        pct = rank / (k - 1) if k > 1 else 0.5
        if pct <= 0.5:
            failures += 1
        used += 1
    return {
        "pbo": (failures / used) if used else None,
        "splits": n_splits,
        "combinations_used": used,
        "strategies": k,
        "observations": n,
    }
