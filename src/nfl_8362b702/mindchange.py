"""Two-sided 'what would change our mind' fields for every strategy entry.

Each strategy carries one falsifier and one confirmer with numeric thresholds.
The fields are frozen at registration like the rest of the rule text.
"""
from __future__ import annotations

MINDCHANGE = [
    {"strategy_id": "S8362-SHADOW",
     "would_change_our_mind_for": "Brier skill > 0 with a game-cluster 95% lower bound "
                                  "above 0 across a settled window of n >= 32 games, and "
                                  "each club's G-SWEEP complete",
     "would_change_our_mind_against": "Brier skill <= 0 on the first settled window of "
                                      "n >= 32 games, or walk-forward residuals show no "
                                      "advantage over the constant-margin baseline "
                                      "(MAE ratio >= 1.00)",
     "threshold_for": "cluster LB > 0 at n >= 32", "threshold_against": "skill <= 0 at n >= 32",
     "state_at_registration": "unsettled (n_settled = 0)"},
    {"strategy_id": "S8362-RANDOM",
     "would_change_our_mind_for": "nothing — a coin has no skill by construction; it is a "
                                  "control, not a candidate",
     "would_change_our_mind_against": "its realised hit rate falling outside the exact "
                                      "binomial 95% band of p=0.5 would indicate a broken "
                                      "randomiser, not skill",
     "threshold_for": "n/a", "threshold_against": "|z| > 1.96 at n >= 32",
     "state_at_registration": "control armed"},
    {"strategy_id": "S8362-FAVORITE",
     "would_change_our_mind_for": "hit rate above the coin band AND above S8362-SHADOW on "
                                  "the same settled window",
     "would_change_our_mind_against": "hit rate inside the coin 95% band at n >= 32 — the "
                                      "rating adds nothing over a coin",
     "threshold_for": "z > 1.96 vs p=0.5", "threshold_against": "|z| <= 1.96 at n >= 32",
     "state_at_registration": "unsettled"},
    {"strategy_id": "S8362-PARLAY2",
     "would_change_our_mind_for": "a directly validated joint probability table (published, "
                                  "with its own n) plus operator void/push rules on file",
     "would_change_our_mind_against": "any evidence that legs are being priced as "
                                      "independent marginals — that alone demotes the entry",
     "threshold_for": "n_validated_joint >= 1", "threshold_against": "marginal multiplication found",
     "state_at_registration": "blocked at G-JOINT"},
    {"strategy_id": "S8362-SGP",
     "would_change_our_mind_for": "a same-game joint model validated out-of-sample with "
                                  "published calibration error",
     "would_change_our_mind_against": "leg-level calibration error > 0.05 on any settled "
                                      "sample of n >= 32",
     "threshold_for": "joint model published + calibrated", "threshold_against": "ECE > 0.05",
     "state_at_registration": "blocked at G-JOINT"},
    {"strategy_id": "S8362-PROPCOMBO",
     "would_change_our_mind_for": "an official prop-price feed with timestamps AND a "
                                  "validated joint distribution across the combo legs",
     "would_change_our_mind_against": "any prop settlement that disagrees with the official "
                                      "box score (source conflict)",
     "threshold_for": "licensed prop feed + joint table", "threshold_against": "1 settlement conflict",
     "state_at_registration": "blocked at G-PRICE and G-JOINT"},
]


def rows():
    return [dict(r) for r in MINDCHANGE]
