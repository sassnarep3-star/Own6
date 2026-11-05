"""Odds conversion, de-vigging and expected value.

All functions are pure arithmetic. They contain no basketball assumptions.

Definitions used (textbook arithmetic, no source claimed as authority for the
*project's* choice of method):

  American +150  -> decimal 2.50      (1 + 150/100)
  American -200  -> decimal 1.50      (1 + 100/200)
  decimal d      -> implied probability 1/d   (this is the bookmaker's quote,
                                               not a true probability)
  Two-way proportional de-vig: divide each implied probability by their sum.
      This is the *multiplicative* method. It is one of several de-vig methods
      (additive, Shin, power, worst-case). Its choice is a stated project
      convention, not a sourced NBA fact, and it is flagged as such.
"""
from __future__ import annotations

from dataclasses import dataclass


def american_to_decimal(american: float) -> float:
    """Convert American odds to decimal (total return per 1 unit staked)."""
    a = float(american)
    if a == 0:
        raise ValueError("American odds of 0 are not valid")
    if a > 0:
        return 1.0 + a / 100.0
    return 1.0 + 100.0 / abs(a)


def american_to_implied(american: float) -> float:
    """Bookmaker implied probability (includes vig)."""
    return 1.0 / american_to_decimal(american)


def decimal_to_implied(dec: float) -> float:
    if dec <= 1.0:
        raise ValueError("decimal odds must exceed 1.0")
    return 1.0 / dec


def implied_to_american(p: float) -> float:
    """Convert a probability into the American odds that exactly price it."""
    if not 0.0 < p < 1.0:
        raise ValueError("probability must be strictly between 0 and 1")
    if p == 0.5:
        return 100.0
    if p > 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


@dataclass(frozen=True)
class TwoWayMarket:
    """A two-outcome market quoted on both sides."""

    side_a_american: float
    side_b_american: float

    @property
    def implied_a(self) -> float:
        return american_to_implied(self.side_a_american)

    @property
    def implied_b(self) -> float:
        return american_to_implied(self.side_b_american)

    @property
    def vig(self) -> float:
        """Overround: implied_a + implied_b - 1. 0 for a fair book."""
        return self.implied_a + self.implied_b - 1.0

    def devig_proportional(self) -> tuple[float, float]:
        """Multiplicative de-vig. Returns (p_a, p_b); they sum to exactly 1."""
        s = self.implied_a + self.implied_b
        if s <= 0:
            raise ValueError("non-positive implied probability sum")
        return self.implied_a / s, self.implied_b / s

    def devig_additive(self) -> tuple[float, float]:
        """Additive de-vig: subtract half the overround from each side."""
        v = self.vig
        return self.implied_a - v / 2.0, self.implied_b - v / 2.0


def fair_prob(american: float, other_american: float) -> float:
    """De-vigged probability of the side quoted at ``american``."""
    return TwoWayMarket(american, other_american).devig_proportional()[0]


def expected_value_per_unit(p_win: float, american: float) -> float:
    """EV of a 1-unit stake at ``american`` if the true win probability is p_win."""
    dec = american_to_decimal(american)
    return p_win * (dec - 1.0) - (1.0 - p_win)


def breakeven_probability(american: float) -> float:
    """Win probability at which EV is exactly zero."""
    return american_to_implied(american)


def kelly_fraction(p_win: float, american: float) -> float:
    """Full-Kelly stake fraction. Negative means 'no bet'."""
    dec = american_to_decimal(american)
    b = dec - 1.0
    if b <= 0:
        return 0.0
    f = (p_win * b - (1.0 - p_win)) / b
    return max(0.0, f)


def settle(p_win: float, american: float, won: bool) -> float:
    """Realised profit on a 1-unit stake."""
    if won:
        return american_to_decimal(american) - 1.0
    return -1.0


def two_way_settle_all_payouts(american: float) -> tuple[float, float]:
    return american_to_decimal(american) - 1.0, -1.0
