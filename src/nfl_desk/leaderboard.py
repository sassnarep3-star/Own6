"""The competition: preregistered strategies, readiness scoring, rewards.

Rewards are research priority, not money, and the performance board is empty by
design until every evidence gate returns PASS. Readiness measures how much of a
strategy's required input set this repository can already source from official
pages - it is a work-planning number, not evidence of skill.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Strategy:
    sid: str
    structure: str
    name: str
    hypothesis: str
    required_features: tuple[str, ...]
    luck_controls: tuple[str, ...]
    available_features: tuple[str, ...] = field(default=())


STRATEGIES = (
    Strategy("DS-01", "Single bet - spread",
             "Same-unit injury cluster vs opponent front",
             "Two or more Out/DNP designations in the same OL or pass-rush group shift the fair spread",
             ("OL_cluster_flag", "pass_rush_cluster_flag", "club_scoring_rating"),
             ("pre-inactive timestamped report", "bootstrap over slates", "push-inclusive settlement"),
             ("club_scoring_rating", "OL_cluster_flag", "pass_rush_cluster_flag")),
    Strategy("DS-02", "Single bet - moneyline",
             "Quarterback replacement tier",
             "A QB1 absence priced only by the backup's own quality leaves residual value on the opponent side",
             ("qb_depth_tier", "bulletin_confirmation", "club_scoring_rating"),
             ("announcement-lag control", "same-line CLV", "excluding the starter's own game from any fit"),
             ("qb_depth_tier", "club_scoring_rating")),
    Strategy("DS-03", "Single bet - total",
             "Availability-weighted scoring environment",
             "Sum of both clubs' scoring rates moved by listed absences on both sides of the ball beats a raw average",
             ("scoring_rates", "absence_weights", "neutral_site_flag"),
             ("assumption grid", "walk-forward holdout", "vig break-even test"),
             ("scoring_rates", "absence_weights", "neutral_site_flag")),
    Strategy("DS-04", "Single bet - total",
             "Neutral-site international game adjustment",
             "International games carry no travel asymmetry for the designated home club, so home points should be zeroed",
             ("neutral_site_flag", "scoring_rates"),
             ("explicit single-slate case study, no generalisation from n=1", "assumption grid"),
             ("neutral_site_flag", "scoring_rates")),
    Strategy("DS-05", "Player prop combo (SGP)",
             "Correlated passing-volume stack",
             "A stack that prices marginal props as independent underestimates the joint tail; price it with dependence",
             ("prop_market_lines", "residual_dependence"),
             ("Frechet bounds instead of point dependence", "no independence assumption", "same-game joint settlement"),
             ()),
    Strategy("DS-06", "Player prop combo (SGP)",
             "Game-script hedge stack",
             "Pairing an overs leg with a trailing-team leg makes the joint distribution depend on margin, not just totals",
             ("prop_market_lines", "margin_model"),
             ("margin-scenario reweighting", "joint settlement"),
             ("margin_model",)),
    Strategy("DS-07", "Parlay - same game",
             "Spread plus team total on the same side",
             "Two legs of the same game are strongly positively dependent; a parlay priced on independence is expensive",
             ("team_total_lines", "spread_lines"),
             ("joint distribution of margin and team points", "push handling on both legs"),
             ()),
    Strategy("DS-08", "Parlay - same game",
             "Over/under pair across two games with weather and venue independence",
             "Cross-game legs are near independent, so a same-slate two-leg parlay is the cheapest legal exposure",
             ("slate_selections", "independence_bound"),
             ("correlation bound check before any parlay is priced", "bootstrap across slates"),
             ("slate_selections",)),
    Strategy("DS-09", "Single bet - spread",
             "Season-to-date rating with measured persistence shrinkage",
             "Ratings should be shrunk by the measured year-over-year persistence of scoring differentials, not by taste",
             ("club_scoring_rating", "persistence_estimate"),
             ("out-of-sample season split", "no in-sample shrinkage fit"),
             ("club_scoring_rating", "persistence_estimate")),
    Strategy("DS-10", "Single bet - spread",
             "Luck-reversal fade",
             "A club's wins above its points-based expectation mean-reverts, so fading the residual adds no information about next season",
             ("pyth_residual_2025", "pyth_residual_2026"),
             ("cross-season test published with its own CI", "no cherry-picked season"),
             ("pyth_residual_2025", "pyth_residual_2026")),
    Strategy("DS-11", "Player prop combo (SGP)",
             "Backfield committee split on an injured lead rusher",
             "When the 1st-string RB is Out, workhorse-style volume projections overpay the starter and underpay the committee",
             ("rb_depth_tier", "prop_market_lines"),
             ("snap-share floor from an official source", "excluding unverified snap counts"),
             ("rb_depth_tier",)),
    Strategy("DS-12", "Single bet - spread",
             "Depth-chart depletion count on the offensive line",
             "Clubs with fewer than eight active linemen are systematically worse than their record says",
             ("active_roster_count", "club_scoring_rating"),
             ("48/53-man roster rules as the only count source", "excluding practice-squad ambiguity"),
             ("club_scoring_rating",)),
)

REWARD_TIERS = (
    ("TIER-0", "no reward", "0 gates passed on evidence"),
    ("TIER-1", "review priority", "all structural gates pass and >=1 evidence gate passes"),
    ("TIER-2", "shadow-ledger promotion", "all evidence gates pass on a chronological holdout, CLV t >= 2.5"),
    ("TIER-3", "capital allocation proposal", "TIER-2 plus stability across 8 slates and a written post-mortem"),
)


def readiness(strategy: Strategy) -> float:
    if not strategy.required_features:
        return 0.0
    return len(set(strategy.available_features) & set(strategy.required_features)) / len(strategy.required_features)


def rank(gate_states: dict[str, str], settled: dict[str, int] | None = None) -> list[dict]:
    """Rank by evidence first, readiness second, id third - a total, reproducible order."""
    settled = settled or {}
    rows = []
    for s in STRATEGIES:
        evidence_pass = sum(1 for g in gate_states.values() if g == "PASS")
        rows.append({
            "strategy_id": s.sid, "structure": s.structure, "name": s.name,
            "hypothesis": s.hypothesis,
            "required_features": ", ".join(s.required_features),
            "luck_controls": "; ".join(s.luck_controls),
            "readiness": readiness(s),
            "missing_features": ", ".join(f for f in s.required_features if f not in s.available_features)
                          or "nothing missing - all required inputs are verified and on disk",
            "gates_passed_evidence": evidence_pass,
            "settled_selections": settled.get(s.sid, 0),
        })
    rows.sort(key=lambda r: (-r["gates_passed_evidence"], -r["readiness"], r["strategy_id"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["reward_tier"] = "TIER-0"
        r["reward"] = "no reward - unqualified"
        r["status"] = "UNQUALIFIED"
    return rows
