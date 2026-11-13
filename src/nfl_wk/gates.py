"""Validation gates, leaderboard and reward accounting for the NFL W11 pack.

The gate engine is fail-closed: a strategy is only ELIGIBLE when every gate returns PASS and
the gate result was produced from licensed, timestamped data. Absent such data every gate
returns BLOCKED or FAIL and no leaderboard reward is awarded. Nothing in this module awards a
monetary prize; rewards are research units defined in ``REWARD_POLICY``.
"""

from __future__ import annotations

# Gate definitions. ``requires`` names the artefact that must exist in the repo for the gate
# to be evaluable at all. Missing artefact -> BLOCKED (fail closed), never PASS.
GATES = [
    ("VG-01", "Rights and terms compliance", "Every strategy", "Wagering analytics on NFL data without written permission",
     "A licence or written consent naming gambling-use analytics is on file (nfl.com Terms §1.3 restricts systematic retrieval and non-informational use).",
     "gate_licence_record"),
    ("VG-02", "Pre-kickoff timestamp", "Any signal at all", "Look-ahead: using information published after the market moved or after kickoff",
     "Every observation carries a captured-at timestamp earlier than kickoff and earlier than the price it is compared with.",
     "gate_timestamped_observations"),
    ("VG-03", "Licensed market price archive", "Any edge, ROI or CLV claim", "Inventing a price, a closing line or a profit figure",
     "A timestamped, de-vigged closing-line archive from a licensed provider exists for each market evaluated.",
     "gate_price_archive"),
    ("VG-04", "Chronological walk-forward split", "Any out-of-sample claim", "Parameter fitting that sees its own test weeks",
     "Parameters are frozen before each week; no future information enters the fit; the split is recorded per week.",
     "gate_walkforward_run"),
    ("VG-05", "Calibration (Brier + reliability)", "Probability-based strategies", "A probability model that is confident but wrong",
     "Brier score and a reliability curve are reported out-of-sample and beat the reference (see scikit-learn calibration docs).",
     "gate_calibration_run"),
    ("VG-06", "Uncertainty interval", "Every published number", "A point estimate presented as if it were exact",
     "Every effect carries a confidence interval (NIST/SEMATECH 3.5.2) and the interval is reported beside the point estimate.",
     "gate_interval_run"),
    ("VG-07", "Sample-size floor 200 bets / 60 slates", "Ranking and rewards", "A 6-bet run that looks like skill",
     "At least 200 settled bets across at least 60 distinct slates in the holdout period.",
     "gate_sample_size"),
    ("VG-08", "Multiple-comparison correction", "Any 'significant' finding", "Testing 10 strategies and reporting the best without correction",
     "p-values are corrected (Benjamini-Hochberg or Holm) across every strategy and market actually tested (statsmodels multitest).",
     "gate_multiplicity_run"),
    ("VG-09", "Roster-identity adjustment", "Injury/depth strategies", "Fitting season-long rates to a roster that no longer exists",
     "The model's look-back is explicitly shortened or re-weighted by measured roster identity, and the rule is pre-registered.",
     "gate_roster_identity_run"),
    ("VG-10", "Line-move direction agreement", "Parleys and combos", "Combining legs whose dependence is unmeasured",
     "The sign of each pairwise dependence is pre-registered, measured out-of-sample, and the interval excludes 0.",
     "gate_correlation_run"),
    ("VG-11", "Correlation carried into the price", "SGP/SGP+ combos", "Multiplying leg probabilities as if independent",
     "The joint probability used for pricing is the correlated one; the independence-based price is published beside it for contrast.",
     "gate_correlation_run"),
    ("VG-12", "Pre-registration freeze", "Every strategy", "Moving the goalposts after seeing results",
     "The hypothesis, the signal rule and the thresholds are committed to git before the first observation.",
     "gate_preregistration"),
]

REWARD_POLICY = {
    "unit": "research_units",
    "monetary": False,
    "tiers": [
        ("Tier 0", "0 gates passed", "listed as a hypothesis", "0"),
        ("Tier 1", "VG-01, VG-02, VG-12 pass", "preregistered and legible", "1"),
        ("Tier 2", "Tier 1 + VG-03, VG-04, VG-07 pass", "measured out-of-sample on licensed prices", "3"),
        ("Tier 3", "Tier 2 + VG-05, VG-06, VG-08 pass", "calibrated, uncertain, multiplicity-corrected", "6"),
        ("Tier 4", "All 12 gates pass", "eligible for the leaderboard", "10"),
    ],
    "note": "No money changes hands. A higher tier buys a reviewer's attention, nothing else.",
}

# Gate artefact registry. Keys are the artefacts named in GATES; values are the state as of
# the 2026-11-13 build. 'absent' is the honest value for everything not yet in the repo.
ARTEFACTS = {
    "gate_licence_record": "absent",
    "gate_timestamped_observations": "absent",
    "gate_price_archive": "absent",
    "gate_walkforward_run": "absent",
    "gate_calibration_run": "absent",
    "gate_interval_run": "partial (this pack reports intervals on descriptive aggregates only)",
    # Repo-local registers that exist and are auditable, but are not licensed data.
    "gate_preregistration": "present",
    "gate_sample_size": "absent",
    "gate_multiplicity_run": "absent",
    "gate_roster_identity_run": "absent",
    "gate_correlation_run": "absent",
}


def gate_result(requires: str) -> tuple[str, str]:
    """Return (status, reason). Fail closed: unknown or absent artefact is BLOCKED."""
    state = ARTEFACTS.get(requires)
    if state is None:
        return "BLOCKED", f"artefact '{requires}' is not registered"
    if state == "present":
        return "PASS", "artefact present in the repo"
    if state.startswith("partial"):
        return "BLOCKED", f"artefact partial: {state}"
    return "BLOCKED", f"artefact absent: {state}"


def evaluate_all() -> list[dict]:
    out = []
    for gid, name, blocks, failure, rule, requires in GATES:
        status, reason = gate_result(requires)
        out.append({
            "gate_id": gid,
            "gate": name,
            "what_it_blocks": blocks,
            "failure_mode_prevented": failure,
            "rule": rule,
            "status": status,
            "reason": reason,
            "artefact": requires,
        })
    return out


def strategy_eligibility(passed_gates: list[str]) -> tuple[str, str, int]:
    """Return (eligibility, tier, research_units) for a strategy's passed-gate list."""
    s = set(passed_gates)
    if len(s) == len(GATES):
        return "ELIGIBLE", "Tier 4", 10
    if {"VG-01", "VG-02", "VG-12"} <= s:
        tier, units = "Tier 1", 1
    else:
        return "QUARANTINED", "Tier 0", 0
    if {"VG-03", "VG-04", "VG-07"} <= s:
        tier, units = "Tier 2", 3
    if {"VG-05", "VG-06", "VG-08"} <= s:
        tier, units = "Tier 3", 6
    return "QUARANTINED", tier, units


# --------------------------------------------------------------------------------------
# Strategy families
# --------------------------------------------------------------------------------------
STRATEGIES = [
    {
        "id": "NFL-W11-01",
        "family": "Single bet",
        "market": "Spread",
        "name": "Own-line vs market-line disagreement (single)",
        "hypothesis": "When our originated spread (built from official standings points-for/against with opponent adjustment) differs from a licensed market spread by more than a pre-registered threshold, the market price is stale.",
        "signal_rule": "Emit a signal only if |own_spread - market_spread| >= 1.5 points AND the disagreement survives the multiplicity correction.",
        "needs": "Licensed timestamped spread archive; official play-by-play for opponent adjustment.",
        "data_state": "0 licensed prices; own line computable from official standings only (no opponent adjustment possible from totals alone).",
    },
    {
        "id": "NFL-W11-02",
        "family": "Single bet",
        "market": "Total (over/under)",
        "name": "Pace-and-efficiency total (single)",
        "hypothesis": "Combining each club's official points-for and points-against rates with an opponent adjustment produces a total that is more accurate than the licensed market total.",
        "signal_rule": "Signal only when the own total differs from the licensed total by >= 2.0 points AND the over/under probability clears the calibrated edge threshold.",
        "needs": "Licensed totals archive; scoring-play detail to split offensive and defensive points.",
        "data_state": "0 licensed prices; own total computable as a descriptive aggregate only.",
    },
    {
        "id": "NFL-W11-03",
        "family": "Single bet",
        "market": "Moneyline",
        "name": "Calibrated win probability from own margin (single)",
        "hypothesis": "A normal margin model calibrated to official results produces win probabilities that beat the de-vigged market probability on the same selection.",
        "signal_rule": "Signal only if the calibrated edge >= threshold and the reliability curve is within tolerance out-of-sample.",
        "needs": "Licensed moneyline archive; at least 3 seasons of official results for calibration.",
        "data_state": "0 licensed prices; no calibration run.",
    },
    {
        "id": "NFL-W11-04",
        "family": "Single bet",
        "market": "Team total",
        "name": "Verified first-string loss on the offensive line (single)",
        "hypothesis": "When a club-chart first-string offensive lineman is ruled Out and the club's own chart lists a second-string replacement, the originated team total is too high.",
        "signal_rule": "Signal only when the club chart shows the replacement AND the injury report shows Out AND the market price was captured after the report and before kickoff.",
        "needs": "Club depth chart with publication timestamp; injury-report snapshot with hash; licensed team-total archive.",
        "data_state": "Depth charts read for 7 clubs on 2026-11-13 (no publication timestamp on the page); licensed prices absent.",
    },
    {
        "id": "NFL-W11-05",
        "family": "Single bet",
        "market": "Opposing team total",
        "name": "Secondary-cluster deficiency fade (single)",
        "hypothesis": "Two or more first-string defensive backs ruled Out in the same week raise the opposing passing game beyond the defensive line's compensating pressure.",
        "signal_rule": "Signal only when the count of Out first-string DBs >= 2 AND the opposing quarterback is confirmed active on the inactive list.",
        "needs": "Inactive lists captured at T-90; licensed passing-prop archive.",
        "data_state": "No inactive lists captured; no licensed props.",
    },
    {
        "id": "NFL-W11-06",
        "family": "Single bet",
        "market": "Moneyline",
        "name": "Quarterback cascade (single)",
        "hypothesis": "A club starting its third-string or lower quarterback produces a non-linear drop in offensive efficiency that the market under-prices.",
        "signal_rule": "Signal only when the club chart lists the starter at string 3 or lower AND the inactive list confirms strings 1 and 2 are unavailable.",
        "needs": "Inactive list; club chart; licensed moneyline archive.",
        "data_state": "Two clubs show a non-first-string QB on the chart as of 2026-11-13 (BAL, PHI); inactive lists absent, so no signal.",
    },
    {
        "id": "NFL-W11-07",
        "family": "Parlay",
        "market": "Two-leg same-game",
        "name": "Correlated same-game two-leg (parlay)",
        "hypothesis": "Two legs whose measured dependence is positive can be combined at a price that is better than the product of the legs' implied probabilities.",
        "signal_rule": "Signal only when the measured correlation interval excludes 0 AND the correlated joint probability gives a positive expected value at the licensed parlay price.",
        "needs": "Paired outcome history; licensed parlay price; correlation run.",
        "data_state": "Correlation values are blank: no paired outcome history is licensed.",
    },
    {
        "id": "NFL-W11-08",
        "family": "Parlay",
        "market": "Cross-game",
        "name": "Cross-game slate parlay (parlay)",
        "hypothesis": "Cross-game legs are close to independent but not exactly so; slate-level shocks create weak coupling that matters at scale.",
        "signal_rule": "Signal only when the measured cross-game correlation interval is published AND the parlay price beats the independence price by more than the measured coupling.",
        "needs": "Slate-clustered residual history; licensed parlay price.",
        "data_state": "Blank. No history, no price.",
    },
    {
        "id": "NFL-W11-09",
        "family": "Player prop",
        "market": "Player passing yards",
        "name": "Quarterback prop with confirmed depth cascade (prop)",
        "hypothesis": "When a first-string quarterback is ruled Out and a third-string quarterback starts, the passing-yards distribution shifts down by more than the posted line allows.",
        "signal_rule": "Signal only when the inactive list confirms both quarterbacks ahead of the starter are unavailable AND the prop line was posted after confirmation.",
        "needs": "Inactive list at T-90; licensed player-prop archive.",
        "data_state": "No licensed props; no inactive lists.",
    },
    {
        "id": "NFL-W11-10",
        "family": "Player prop combination",
        "market": "QB passing yards + WR receiving yards (same game)",
        "name": "Same-game prop combo (prop combo)",
        "hypothesis": "A quarterback's passing yards and his first-string receiver's receiving yards are positively dependent, so the joint over is more likely than the product of the marginals.",
        "signal_rule": "Signal only when the measured correlation interval excludes 0 AND the combo is priced off the correlated joint distribution.",
        "needs": "Paired player-game logs; licensed prop prices; correlation run.",
        "data_state": "Blank. No paired history and no licensed prices.",
    },
    {
        "id": "NFL-W11-11",
        "family": "Player prop combination",
        "market": "RB rushing yards + team total (same game)",
        "name": "Game-script combo (prop combo)",
        "hypothesis": "A team total and its lead running back's rushing yards move together when the game script is positive, and apart when it is negative.",
        "signal_rule": "Signal only when the measured conditional correlation (by script) is published and the combo price beats the conditional joint.",
        "needs": "Conditional history; licensed team-total and prop prices.",
        "data_state": "Blank.",
    },
]
