"""Calibration: reliability bins, Brier score, and Brier skill score vs a market baseline.

Definitions follow the standard decomposition used by scikit-learn's calibration
guide (https://scikit-learn.org/stable/modules/calibration.html): a forecaster is
calibrated when the predicted probability matches the observed frequency in each
predicted-probability bin. Brier skill score = 1 - BS_model / BS_baseline.
"""
from __future__ import annotations

import numpy as np


def brier(probs: np.ndarray, outcomes: np.ndarray) -> float:
    probs = np.asarray(probs, dtype=float)
    outcomes = np.asarray(outcomes, dtype=float)
    return float(np.mean((probs - outcomes) ** 2))


def log_loss(probs: np.ndarray, outcomes: np.ndarray, eps: float = 1e-12) -> float:
    p = np.clip(np.asarray(probs, dtype=float), eps, 1 - eps)
    y = np.asarray(outcomes, dtype=float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def reliability(probs: np.ndarray, outcomes: np.ndarray, bins: int = 10) -> list[dict]:
    probs = np.asarray(probs, dtype=float)
    outcomes = np.asarray(outcomes, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (probs >= lo) & (probs < hi if hi < 1.0 else probs <= hi)
        n = int(mask.sum())
        rows.append({
            "bin": f"{lo:.1f}-{hi:.1f}",
            "n": n,
            "mean_predicted": float(probs[mask].mean()) if n else None,
            "observed_rate": float(outcomes[mask].mean()) if n else None,
            "gap": float(outcomes[mask].mean() - probs[mask].mean()) if n else None,
        })
    return rows


def brier_skill_score(model_probs, outcomes, market_probs) -> dict:
    bs_m = brier(model_probs, outcomes)
    bs_k = brier(market_probs, outcomes)
    return {"brier_model": bs_m, "brier_market": bs_k,
            "bss": (1.0 - bs_m / bs_k) if bs_k > 0 else None,
            "n": int(len(model_probs))}


def expected_calibration_error(probs, outcomes, bins: int = 10) -> float | None:
    rows = reliability(probs, outcomes, bins)
    n = sum(r["n"] for r in rows)
    if n == 0:
        return None
    return float(sum(r["n"] * abs(r["gap"]) for r in rows if r["n"]) / n)
