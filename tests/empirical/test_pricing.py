import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from nba_lab.pricing import (
    american_to_implied,
    devig_two_way,
    empirical_joint,
    expected_value,
    fair_home_spread,
    fair_total,
    prob_to_american,
    probability,
)


def test_prices():
    assert american_to_implied(-110) == pytest.approx(110 / 210)
    assert american_to_implied(110) == pytest.approx(100 / 210)
    assert probability(0.5) == 0.5
    assert prob_to_american(0.5) == -110
    a, b = devig_two_way(0.55, 0.52)
    assert a + b == pytest.approx(1.0)
    assert expected_value(0.5, 2.0) == pytest.approx(0.0)
    assert fair_home_spread(3.0) == -3.0
    assert fair_total(110.0, 100.0) == 210.0


def test_prices_reject_invalid():
    with pytest.raises(ValueError):
        american_to_implied(50)
    with pytest.raises(ValueError):
        probability(1.5)
    with pytest.raises(ValueError):
        expected_value(0.0, 2.0)
    with pytest.raises(ValueError):
        fair_total(-1.0, 2.0)
    with pytest.raises(ValueError):
        fair_total(math.nan, 2.0)


def test_empirical_joint():
    a = [1, 1, 0, 0, 1, 0, 1, 1, 0, 0]
    b = [1, 1, 0, 0, 1, 0, 1, 1, 1, 0]
    j = empirical_joint(a, b)
    assert j["n"] == 10
    assert j["p_joint"] == pytest.approx(0.5)
    assert j["independent_reference"] == pytest.approx(0.3)
    assert j["fair_decimal"] == pytest.approx(1 / 0.5)


def test_empirical_joint_rejects():
    with pytest.raises(ValueError):
        empirical_joint([1, 0], [1, 0, 0])
    with pytest.raises(ValueError):
        empirical_joint([0.5, 0.5], [1, 0])
    with pytest.raises(ValueError):
        empirical_joint([1, 0], [1, 0])  # too few
