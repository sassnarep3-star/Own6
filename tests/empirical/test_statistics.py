import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pytest

from nba_lab.statistics import (
    binomial_tail,
    brier,
    calibration_bins,
    cluster_bootstrap,
    log_loss,
    max_drawdown,
    pearson_pair,
    poisson_binomial_tail,
)


def test_scores():
    p = [0.6, 0.7, 0.8]
    y = [1, 1, 0]
    assert brier(p, y) == pytest.approx(sum((a - b) ** 2 for a, b in zip(p, y)) / 3)
    assert log_loss(p, y) > 0
    assert len(calibration_bins(p, y, bins=2)) == 2


def test_cluster_bootstrap_preserves_dependence():
    returns = [0.9, -1.0, 0.9, -1.0]
    groups = ["g1", "g1", "g2", "g2"]
    result = cluster_bootstrap(returns, groups, iterations=500, seed=1)
    assert result["n_clusters"] == 2
    assert result["mean"] == pytest.approx(-0.05)
    assert result["lower"] <= result["mean"] <= result["upper"]


def test_bonferroni_and_poisson():
    from nba_lab.statistics import bonferroni
    assert bonferroni([0.01, 0.04])["adjusted"] == pytest.approx([0.02, 0.08])
    assert 0 <= poisson_binomial_tail(2, [0.5, 0.5]) <= 1
    assert binomial_tail(5, 5, 0.5) > 0


def test_pearson():
    a = [1, 2, 3, 4, 5, 6]
    b = [2, 4, 6, 8, 10, 12]
    r = pearson_pair(a, b)
    assert r["estimate"] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        pearson_pair([1, 1, 1], [1, 2, 3])
    with pytest.raises(ValueError):
        pearson_pair([1, 2], [1, 2])


def test_max_drawdown():
    assert max_drawdown([1.0, -2.0, 3.0]) == pytest.approx(2.0)
    assert max_drawdown([]) is None


def test_scores_reject_unaligned():
    with pytest.raises(ValueError):
        brier([0.5], [1, 0])
    with pytest.raises(ValueError):
        log_loss([], [])
    with pytest.raises(ValueError):
        cluster_bootstrap([1.0], [])
