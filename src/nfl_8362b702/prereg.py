"""Pre-registration record and validation gates for the S8362 strategies.

Rule text, sample windows and gates are frozen here. The registration is the
commit that first contains this file; the builder prints its hash so the
ledger can cite it. Nothing here reads a result.
"""
from __future__ import annotations

REGISTRATION_TIME_UTC = "2026-11-16T00:20:00Z"
FIRST_WEEK11_KICKOFF_ET = "2026-11-19 8:15 PM ET (Colts at Texans card)"
CORPUS_WINDOW = "2026 regular season, weeks 1-9 finals (the 136-game log)"
EVALUATION_WINDOW = "week 10 (settling) and week 11 (prospective, unsettled at registration)"

STRATEGY_SPECS = [
    {"strategy_id": "S8362-SHADOW",
     "division": "singles",
     "rule_text": "Pick the side with higher p_home_win from S8362-SHADOW-v1; "
                  "publish the probability and its full input vector; no staking.",
     "window": CORPUS_WINDOW + " for fit; " + EVALUATION_WINDOW + " for evaluation",
     "frozen_before_kickoff": "yes",
     "price_dependent": "no"},
    {"strategy_id": "S8362-RANDOM",
     "division": "singles",
     "rule_text": "Deterministic seeded coin flip per game (seed = first 8 hex of "
                  "sha256('nfl_8362b702/controls/v1')); expected accuracy 0.5 exactly.",
     "window": EVALUATION_WINDOW,
     "frozen_before_kickoff": "yes",
     "price_dependent": "no"},
    {"strategy_id": "S8362-FAVORITE",
     "division": "singles",
     "rule_text": "Pick the rating favorite (higher corpus S_t; tie-break higher "
                  "PF/g). A market-favorite control is impossible without licensed "
                  "prices and is not approximated.",
     "window": CORPUS_WINDOW + " for fit; " + EVALUATION_WINDOW + " for evaluation",
     "frozen_before_kickoff": "yes",
     "price_dependent": "no"},
    {"strategy_id": "S8362-PARLAY2",
     "division": "game_parlays",
     "rule_text": "Two-leg game parlays may be RANKED only when a directly "
                  "validated joint probability and the operator's void/push rules "
                  "are both available. Multiplying marginal probabilities is invalid "
                  "under dependence.",
     "window": "not opened",
     "frozen_before_kickoff": "yes",
     "price_dependent": "no"},
    {"strategy_id": "S8362-SGP",
     "division": "same_game_parlays",
     "rule_text": "Same-game parlays sit behind the joint-evidence gate; legs of one "
                  "game are maximally dependent.",
     "window": "not opened",
     "frozen_before_kickoff": "yes",
     "price_dependent": "no"},
    {"strategy_id": "S8362-PROPCOMBO",
     "division": "prop_combos",
     "rule_text": "Prop combos require official prop prices AND a validated joint "
                  "probability; neither exists.",
     "window": "not opened",
     "frozen_before_kickoff": "yes",
     "price_dependent": "yes (blocked)"},
]

GATES = [
    {"gate_id": "G-REG", "rule": "Rule text frozen in git before the first kickoff of the "
                                 "evaluation window", "threshold": "registration commit "
                                 "predates " + FIRST_WEEK11_KICKOFF_ET, "closes_if": "never"},
    {"gate_id": "G-PROB", "rule": "Every model output stores a probability and its full "
                                  "input vector", "threshold": "100% of output rows", "closes_if": "never"},
    {"gate_id": "G-BACKTEST", "rule": "No backtest number may appear on the leaderboard",
     "threshold": "leaderboard rows carry no fitted-sample statistic", "closes_if": "never"},
    {"gate_id": "G-JOINT", "rule": "Combo divisions rank only with a validated joint "
                                   "probability AND operator void/push rules", "threshold":
         "n_validated_joint >= 1 and void rules on file", "closes_if": "both conditions true"},
    {"gate_id": "G-PRICE", "rule": "Any price-dependent evaluation (CLV, ROI, settlement) "
                                   "waits for a licensed price feed", "threshold":
         "timestamped opening AND closing price rows > 0", "closes_if": "licensed feed exists"},
    {"gate_id": "G-SETTLE", "rule": "Leaderboard proper scores appear only after official "
                                    "finals settle the forecast window", "threshold":
         "n_settled >= 1 (week-11 games final on official pages)", "closes_if": "finals published"},
]

REGISTRATION_ID = "REG-8362-2026-11-16"
