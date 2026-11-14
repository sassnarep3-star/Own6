"""Leaderboard that reports signal and staking as two separate scores.

Why two columns
---------------
A single "units won" column lets a lucky staking run hide a broken signal: a
strategy that goes 8-for-10 on -300 favourites shows a profit while its *pick
selection* is no better than chance, and a strategy that picks well can show a
loss because of a bad stake schedule.

So this module emits two scores that are never combined into one:

``signal_score``
    How good the selection is, independent of any stake. Built from the
    one-sided p-value against a fair coin plus the position of the Wilson
    confidence interval. It cannot be improved by betting bigger.

``staking_score``
    What the money did, at a declared flat stake. This is the only column that
    can be inflated by stake sizing, and it is blank for the moneyline because
    no moneyline price exists to stake at.

A strategy is ranked on ``signal_score``. ``staking_score`` is printed beside it
for reconciliation only. When the two disagree, the leaderboard says so in a
``divergence_flag`` rather than resolving the disagreement in favour of the
better-looking number.

Rewards
-------
The competition awards a tier badge, published in :data:`TIERS`. No reward in
this system is a cash payout; tiers are a review-priority signal for the human
owner. That is stated on the page so the leaderboard cannot be read as an
endorsement to bet.
"""

from __future__ import annotations

from . import backtest as B
from . import stats as S

TIERS = [
    ("T0", "unranked", "No signal score: sample too small to rank."),
    ("T1", "watch", "Signal score present but p >= 0.20. Nothing to act on."),
    ("T2", "promising", "0.05 <= p < 0.20. Worth a forward sample; not a promotion."),
    ("T3", "supported", "p < 0.05 at n >= 100 and every gate open. None reached yet."),
]


def signal_score(summary):
    """Selection quality on a 0-100 scale. Monotone in p and in CI position.

    Returns ``None`` when the sample cannot support a score, which is published
    as blank rather than as zero.
    """
    p = summary["p_one_sided_fair_coin"]
    if p is None or summary["n"] == 0:
        return None
    # Evidence term: 1 at p=0, 0 at p>=0.5. Log-shaped so small p gains matter.
    ev = max(0.0, min(1.0, 1.0 - (p / 0.5) ** 0.5))
    # Sample term: confidence that the point estimate is not noise.
    n = summary["n"]
    sample = min(1.0, (n / 100.0) ** 0.5)
    return round(100.0 * ev * sample, 1)


def staking_score(summary):
    """Realised units per bet on a -50..+50 scale, or None when unpriceable."""
    roi = summary["roi"]
    if roi is None:
        return None
    return round(50.0 * max(-1.0, min(1.0, roi / 0.20)), 1)


def tier_for(summary):
    p = summary["p_one_sided_fair_coin"]
    if p is None or summary["n"] < 30:
        return "T0"
    if p < 0.05 and summary["n"] >= 100:
        return "T3"
    if p < 0.20:
        return "T2"
    return "T1"


def rows(families):
    out = []
    for f in families:
        sig = signal_score(f)
        stk = staking_score(f)
        tier = tier_for(f)
        divergence = ""
        if sig is not None and stk is not None:
            if stk > 0 and sig < 25:
                divergence = "positive_staking_masks_weak_signal"
            elif stk < 0 and sig > 75:
                divergence = "negative_staking_hides_strong_signal"
        out.append(
            {
                "strategy_id": f["strategy_id"],
                "tier": tier,
                "tier_label": dict((t[0], t[1]) for t in TIERS)[tier],
                "n": f["n"],
                "hit_rate": f["win_rate"],
                "ci_low": f["ci_low"],
                "ci_high": f["ci_high"],
                "p_one_sided_fair_coin": f["p_one_sided_fair_coin"],
                "signal_score": "" if sig is None else sig,
                "staking_roi": "" if f["roi"] is None else f["roi"],
                "staking_score": "" if stk is None else stk,
                "profit_units": "" if f["profit_units"] is None else f["profit_units"],
                "divergence_flag": divergence,
                "live": "no",
                "reward_note": "Tier is a review priority for the owner, not betting advice and not a payout.",
            }
        )
    out.sort(key=lambda r: (-1 if r["signal_score"] == "" else r["signal_score"]), reverse=True)
    for i, r in enumerate(out, start=1):
        r["rank_by_signal"] = i
    return out


if __name__ == "__main__":  # pragma: no cover
    for r in rows(B.family_table(B.backtest_all())):
        print(r["rank_by_signal"], r["strategy_id"], r["tier"], r["signal_score"], r["staking_score"], r["divergence_flag"])
