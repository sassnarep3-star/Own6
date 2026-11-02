"""Transparent candidate model primitives, fitted only on supplied training rows.

These are specifications, not fitted NBA models. No NBA observations are bundled.
The empirical residual distributions avoid an unsupported normal-count assumption.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np

from .pricing import probability


def assert_chronological(train_end: datetime, evaluation_start: datetime) -> None:
    if train_end.tzinfo is None or evaluation_start.tzinfo is None:
        raise ValueError("split timestamps must be timezone-aware")
    if train_end >= evaluation_start:
        raise ValueError("training outcomes must end before the evaluation window starts")


class RidgeLineModel:
    """Intercept + standardized ridge regression with training-only residual CDF."""

    def __init__(self, ridge: float = 10.0):
        if not np.isfinite(ridge) or ridge <= 0:
            raise ValueError("ridge penalty must be positive and finite")
        self.ridge = float(ridge)
        self.fitted = False

    def fit(self, features, target) -> "RidgeLineModel":
        x = np.asarray(features, dtype=float)
        y = np.asarray(target, dtype=float)
        if x.ndim != 2 or y.ndim != 1 or len(x) != len(y) or len(x) <= x.shape[1] + 1:
            raise ValueError("need a 2-D feature matrix and more training rows than parameters")
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("training values must be finite")
        self.mean_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0)
        self.scale_[self.scale_ == 0] = 1.0
        z = (x - self.mean_) / self.scale_
        self.intercept_ = float(y.mean())
        design = np.vstack([z, np.sqrt(self.ridge) * np.eye(x.shape[1])])
        response = np.concatenate([y - self.intercept_, np.zeros(x.shape[1])])
        self.coef_ = np.linalg.lstsq(design, response, rcond=None)[0]
        self.residuals_ = y - self._predict_array(x)
        dof = len(y) - x.shape[1] - 1
        self.residual_scale_ = float(np.sqrt(np.sum(self.residuals_ ** 2) / dof))
        self.fitted = True
        return self

    def _predict_array(self, x: np.ndarray) -> np.ndarray:
        return self.intercept_ + ((x - self.mean_) / self.scale_) @ self.coef_

    def predict(self, features) -> float:
        if not self.fitted:
            raise ValueError("model is not fitted")
        x = np.asarray(features, dtype=float)
        if x.ndim != 1 or len(x) != len(self.mean_) or not np.isfinite(x).all():
            raise ValueError("invalid prediction features")
        return float(self._predict_array(x[None, :])[0])

    def win_probability(self, expected_margin: float) -> float:
        if not self.fitted or not np.isfinite(expected_margin):
            raise ValueError("fitted model and finite margin required")
        # Future margin = expected_margin + residual. Add-one smoothing avoids
        # claiming certainty from a finite empirical residual sample.
        hits = int(np.sum(self.residuals_ > -expected_margin))
        return (hits + 0.5) / (len(self.residuals_) + 1)


def shrunk_prop_projection(minutes, points, league_rate: float, shrinkage_n: float = 10.0) -> dict:
    m = np.asarray(minutes, dtype=float)
    p = np.asarray(points, dtype=float)
    if m.ndim != 1 or p.ndim != 1 or len(m) != len(p) or len(m) < 2:
        raise ValueError("prop fit requires aligned samples of at least two prior games")
    if not np.isfinite(m).all() or not np.isfinite(p).all() or np.any(m <= 0) or np.any(p < 0):
        raise ValueError("minutes must be positive and points nonnegative")
    if not np.isfinite(league_rate) or league_rate < 0 or not np.isfinite(shrinkage_n) or shrinkage_n <= 0:
        raise ValueError("league rate must be nonnegative and shrinkage count positive")
    recent_rate = float(p.sum() / m.sum())
    weight = len(m) / (len(m) + shrinkage_n)
    rate = weight * recent_rate + (1 - weight) * league_rate
    projected_minutes = float(m.mean())
    return {"projected_minutes": projected_minutes, "recent_rate": recent_rate, "shrunk_rate": rate, "projection": projected_minutes * rate, "n_prior_games": len(m), "shrinkage_weight": weight}


def empirical_over_probability(training_residuals, projection: float, line: float) -> float:
    r = np.asarray(training_residuals, dtype=float)
    if r.ndim != 1 or len(r) < 2 or not np.isfinite(r).all() or not np.isfinite(projection) or not np.isfinite(line):
        raise ValueError("need finite aligned residuals, projection and line")
    hits = int(np.sum(r > line - projection))
    return (hits + 0.5) / (len(r) + 1)
