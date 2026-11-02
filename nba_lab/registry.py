"""Frozen candidate family and project policy, not empirical findings.

Changing a candidate, threshold, or scoring rule requires a new version and a new
untouched holdout. The six-member family is the multiplicity denominator even if
some candidates are abandoned. Official links define vocabulary, not an edge.
"""
from __future__ import annotations

import hashlib
import json

GLOSSARY = "https://www.nba.com/stats/help/glossary"
TERMS = "https://www.nba.com/termsofuse#nba-statistics"
CALIBRATION = "https://scikit-learn.org/stable/modules/calibration.html"
NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm"
BONFERRONI = "https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm"

CONFIG = {
    "version": "1.0.0",
    "family_size": 6,
    "min_bets": 200,
    "min_events": 200,
    "min_nonpush": 200,
    "alpha": 0.05,
    "bootstrap_iterations": 10000,
    "bootstrap_seed": 20261102,
    "minimum_model_edge": 0.02,
    "minimum_expected_value": 0.02,
    "split_order": ["train", "validation", "holdout"],
    "stake_units": 1.0,
    "reward_policy": "Non-monetary research priority only; no payouts, stakes, or betting recommendations.",
    "ranking_metric": "Lower bound of event-clustered holdout ROI; only all-gate qualifiers are ranked.",
}

# These require independent evidence, not a checkbox supplied by a strategy.
EXTERNAL_EVIDENCE = {
    "rights_verified": False,
    "provenance_verified": False,
    "walk_forward_verified": False,
    "ledger_audited": False,
    "preregistered": False,
    "dependence_verified": False,
}

STRATEGIES = [
    {
        "id": "L1", "name": "Efficiency moneyline", "category": "Single bet", "market": "moneyline",
        "signal": "Out-of-sample margin distribution from prior-game offensive/defensive efficiency, pace and venue features.",
        "selection_rule": "Compare the model win probability with the same-side de-vigged market probability; require the frozen probability and post-vig EV thresholds.",
        "features": "Prior-game possessions, points for/against, venue, rest and availability snapshots; all timestamps must precede the decision.",
        "risk": "Market efficiency, lineup news, rating drift and non-normal margins. A fair line is not evidence of a market edge.",
        "dependence": "Single selection; cluster all bets sharing an event for uncertainty.",
        "source_url": GLOSSARY,
    },
    {
        "id": "L2", "name": "Margin-residual spread", "category": "Single bet", "market": "spread",
        "signal": "Own expected home margin versus the offered handicap, priced with the training residual distribution.",
        "selection_rule": "Freeze fair home spread = -expected margin; trade only if the residual-based cover probability clears the frozen edge/EV thresholds.",
        "features": "Prior-game margins, efficiency, pace, venue and rest; offered handicap and both-side prices.",
        "risk": "Push rules, key-player absences, garbage time and closing-line movement. Never fit residuals on the evaluated game.",
        "dependence": "Single selection; event-clustered uncertainty.",
        "source_url": GLOSSARY,
    },
    {
        "id": "L3", "name": "Pace-efficiency total", "category": "Single bet", "market": "total",
        "signal": "Projected possessions multiplied by matchup efficiencies, with separate over/under residual distributions.",
        "selection_rule": "Compare the projected total distribution with the offered total and de-vigged two-side price; apply the frozen edge/EV thresholds.",
        "features": "Prior-game pace, offensive/defensive efficiency, rest, venue and availability; no current-game outcome features.",
        "risk": "Pace is not an independent causal signal; overtime, fouling and rotation changes can dominate.",
        "dependence": "Single selection; event-clustered uncertainty.",
        "source_url": GLOSSARY,
    },
    {
        "id": "P1", "name": "Shrunk player-points rate", "category": "Player prop", "market": "player_prop",
        "signal": "Projected minutes times a recent scoring rate shrunk toward a training-only league rate.",
        "selection_rule": "Use an empirical residual distribution for the offered half-point line; require the frozen edge/EV thresholds and an authorized market.",
        "features": "Prior-game minutes/points, training-only league rate, timestamped availability and the official provider's settlement rule.",
        "risk": "Minutes volatility, usage changes, blowouts and restricted prop types. The exact current restriction list is not primary-sourced here.",
        "dependence": "Single selection; multiple props on one player/game share an event cluster.",
        "source_url": GLOSSARY,
    },
    {
        "id": "C1", "name": "Two-player same-game overs", "category": "Prop combo", "market": "prop_combo",
        "signal": "Direct training-only joint hit frequency for two player-point overs in the same game, after marginal projection residuals.",
        "selection_rule": "Require at least the frozen paired-event sample, stable fold estimates, provider permission and positive joint-probability EV. Never multiply marginals by default.",
        "features": "Paired prior-game residual outcomes, shared pace/total exposure, availability and an executable same-game combo price.",
        "risk": "Sparse joint tails, roster changes, positive or negative dependence, and sportsbook correlation adjustments.",
        "dependence": "Empirical two-leg joint probability; undefined or unstable correlation blocks the strategy.",
        "source_url": GLOSSARY,
    },
    {
        "id": "X1", "name": "Two-game moneyline parlay", "category": "Parlay", "market": "parlay",
        "signal": "Two single-game win probabilities plus explicit cross-game dependence evidence and a real executable parlay price.",
        "selection_rule": "Use a validated joint model; independence is a special case requiring evidence, not a default. Require the frozen joint EV threshold.",
        "features": "Timestamped single-game probabilities, shared roster/news exposure, provider parlay rules and the actual combo quote.",
        "risk": "Common news shocks, shared players, provider restrictions and compounding calibration error. No synthetic parlay returns are published.",
        "dependence": "Cross-game joint evidence required; missing evidence blocks qualification.",
        "source_url": GLOSSARY,
    },
]

CORRELATION_PAIRS = [
    {"id": "C-01", "leg_a": "Player A points-over residual", "leg_b": "Player B points-over residual", "scope": "Same game, two players", "method": "Pearson phi on paired binary residual hits; event-bootstrap interval; training folds only."},
    {"id": "C-02", "leg_a": "Player points residual", "leg_b": "Same player assists residual", "scope": "Same player, same game", "method": "Pearson correlation of paired continuous residual outcomes; event-bootstrap interval."},
    {"id": "C-03", "leg_a": "Team-total residual", "leg_b": "Game-total residual", "scope": "Same game", "method": "Paired residual correlation; mechanical overlap disclosed; not a causal estimate."},
    {"id": "C-04", "leg_a": "Home margin residual", "leg_b": "Starter minutes residual", "scope": "Same game", "method": "Paired residual correlation; blowout/rotation confounding disclosed."},
    {"id": "C-05", "leg_a": "Game A favorite win indicator", "leg_b": "Game B favorite win indicator", "scope": "Different games, same slate", "method": "Slate-clustered residual dependence; zero is not assumed."},
    {"id": "C-06", "leg_a": "Player points residual", "leg_b": "Same player rebounds residual", "scope": "Same player, same game", "method": "Paired residual correlation with minutes/pace exposure disclosed."},
]
for pair in CORRELATION_PAIRS:
    pair.update({"estimate": None, "n": None, "ci_low": None, "ci_high": None, "status": "unverified", "source_url": TERMS})

GATE_DEFINITIONS = [
    {"id": "G01", "name": "Rights and market permission", "rule": "Documented rights for the intended use and an authorized market; no self-asserted permission.", "source_url": TERMS},
    {"id": "G02", "name": "Field-level provenance", "rule": "Official provider URLs, source hashes, settlement rules and independently reviewed provenance for every observation.", "source_url": TERMS},
    {"id": "G03", "name": "Chronological walk-forward", "rule": "Features and fits precede decisions; decisions precede events; qualification uses only the untouched chronological holdout.", "source_url": NIST},
    {"id": "G04", "name": "Effective sample size", "rule": "At least 200 holdout bets, 200 distinct event clusters and 200 non-push scoring observations per candidate.", "source_url": NIST},
    {"id": "G05", "name": "Market-relative predictive quality", "rule": "Positive Brier and log-loss improvement versus the same-selection de-vigged market; event-clustered lower bounds above zero. Reliability bins are reported separately.", "source_url": CALIBRATION},
    {"id": "G06", "name": "Post-vig profitability", "rule": "Positive unit-stake holdout ROI with an event-clustered 95% bootstrap lower bound above zero.", "source_url": NIST},
    {"id": "G07", "name": "Closing-line value", "rule": "Positive mean log(offered price / closing price) for identical selections/lines, with an event-clustered lower bound above zero.", "source_url": NIST},
    {"id": "G08", "name": "Luck and multiple testing", "rule": "Heterogeneous-price Poisson-binomial diagnostic, Bonferroni-adjusted across all six frozen candidates; never sufficient without the cluster-robust gates.", "source_url": BONFERRONI},
    {"id": "G09", "name": "Joint dependence", "rule": "Singles use event clustering; combos additionally require training-only joint evidence, adequate paired samples and provider permission. Missing is not independence.", "source_url": TERMS},
    {"id": "G10", "name": "Frozen, auditable ledger", "rule": "Preregistered candidate family and thresholds, immutable model versions, independent timestamp/ledger audit and reproducible artifacts.", "source_url": "https://github.com/sassnarep3-star/Own6/blob/main/research/empirical/DATA_CONTRACT.md"},
]


def config_sha256() -> str:
    payload = json.dumps(CONFIG, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def strategy_ids() -> list[str]:
    return [row["id"] for row in STRATEGIES]
