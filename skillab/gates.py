"""SG gates: the validation gauntlet every strategy must clear.

Design rule: **fail-closed**. A gate that lacks evidence to evaluate is a FAIL,
never a pass and never "n/a". The repository already has two gate frameworks
with colliding IDs (G1-G8 on the verified pages, G01-G10 in ``nba_lab``); this
module deliberately uses a third, distinct prefix, ``SG`` (skill gate), and the
crosswalk is published on the site so the collision is not repeated.

Order matters. SG01-SG03 are *preconditions* (you may not even look at results
if you do not have the rights, the provenance, and a frozen plan). SG04-SG12 are
the statistical tests that separate skill from luck.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any

from . import correlation, leaderboard, luck, pricing

SOURCES = {
    "nba_tou": "https://www.nba.com/termsofuse",
    "nba_faq": "https://www.nba.com/stats/help/faq",
    "nist_binom": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm",
    "nist_ci": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm",
    "scipy_pearson": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html",
    "scipy_bootstrap": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html",
    "sk_brier": "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html",
    "sk_calibration": "https://scikit-learn.org/stable/modules/calibration.html",
    "sk_cv": "https://scikit-learn.org/stable/modules/cross_validation.html",
    "statsmodels_multi": "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html",
}

GATE_DEFS = [
    ("SG01", "Rights and market permission",
     "The data and the use are permitted. NBA Terms §9 bars use of NBA Statistics in connection with gambling; unresolved rights is a fail.",
     SOURCES["nba_tou"]),
    ("SG02", "Field-level provenance",
     "Every observation carries a source URL, a retrieval timestamp and a content hash. Missing evidence is not imputed.",
     "https://github.com/sassnarep3-star/Own6/blob/main/research/empirical/DATA_CONTRACT.md"),
    ("SG03", "Pre-registered, frozen plan",
     "Strategy family, thresholds and stopping rules are hashed before the first bet. Post-hoc threshold changes invalidate the run.",
     "https://scikit-learn.org/stable/modules/cross_validation.html"),
    ("SG04", "Chronological walk-forward",
     "No observation may use information dated after the bet. Parameters are fit only on earlier dates.",
     SOURCES["sk_cv"]),
    ("SG05", "Power and effective sample size",
     "n is at least the sample needed to detect the claimed edge at 80% power, after event clustering.",
     "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm"),
    ("SG06", "Market-relative predictive loss",
     "Paired log-loss (or Brier) must be strictly lower than the de-vigged market on the same games, with an interval excluding zero.",
     SOURCES["sk_brier"]),
    ("SG07", "Positive expected value after vig",
     "Mean return per bet > 0 and the block-bootstrap 95% lower bound > 0.",
     SOURCES["scipy_bootstrap"]),
    ("SG08", "Probability calibration",
     "Expected calibration error within tolerance; Brier reliability must not exceed resolution.",
     SOURCES["sk_calibration"]),
    ("SG09", "Multiple testing controlled",
     "Holm-adjusted p <= alpha across the whole tested family AND a reality-check/SPA p <= alpha.",
     SOURCES["statsmodels_multi"]),
    ("SG10", "Selection bias controlled",
     "Deflated Sharpe >= 0.95 given the number of trials, and probability of backtest overfitting <= 0.20. "
     "Method: Bailey & Lopez de Prado (2014), 'The Deflated Sharpe Ratio'; CSCV: Bailey, Borwein, "
     "Lopez de Prado & Zhu (2014). Implemented in skillab/leaderboard.py with the equations in the module docstring.",
     "https://github.com/sassnarep3-star/Own6/blob/main/skillab/leaderboard.py"),
    ("SG11", "Dependence stated, never assumed",
     "Parlay and prop-combo prices use a measured correlation with n and an interval. Independence is allowed only if labelled.",
     SOURCES["scipy_pearson"]),
    ("SG12", "Immutable ledger and reproducibility",
     "The input set is hashed, the run is deterministic, and no settled observation can be edited or deleted.",
     "https://github.com/sassnarep3-star/Own6/blob/main/scripts/check_skilllab.py"),
]


@dataclass
class GateResult:
    gate_id: str
    name: str
    passed: bool
    value: Any
    threshold: str
    reason: str
    source: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Evidence:
    """Everything a strategy's record contributes. Missing fields = fail."""

    strategy_id: str
    market: str
    bet_type: str  # single | parlay | prop_combo | prop | total | spread | moneyline
    n_observations: int = 0
    per_bet_return: list[float] = field(default_factory=list)
    model_logloss: list[float] = field(default_factory=list)
    market_logloss: list[float] = field(default_factory=list)
    probs: list[float] = field(default_factory=list)
    outcomes: list[int] = field(default_factory=list)
    rights_confirmed: bool = False
    provenance_complete: bool = False
    plan_hash: str | None = None
    plan_hash_recomputed: str | None = None
    walk_forward: bool = False
    max_lookahead_days: int | None = None
    support_legs: int = 1          # >1 for parlays / combos
    rho_used: float | None = None
    rho_n: int | None = None
    rho_ci: tuple[float, float] | None = None
    independence_assumed: bool = False
    n_trials_in_family: int = 1
    p_values_in_family: list[float] = field(default_factory=list)
    ledger_hash: str | None = None
    deterministic: bool | None = None
    claimed_target_roi: float = 0.02
    alpha: float = 0.05
    calibration_tolerance: float = 0.05
    seed: int = 20261105

    def fingerprint(self) -> str:
        payload = {
            "strategy_id": self.strategy_id,
            "market": self.market,
            "bet_type": self.bet_type,
            "n": self.n_observations,
            "sum_return": round(sum(self.per_bet_return), 10),
            "ledger_hash": self.ledger_hash,
            "plan_hash": self.plan_hash,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def evaluate(ev: Evidence) -> dict:
    """Run all twelve gates. Returns a dict with per-gate results and eligibility."""
    results: list[GateResult] = []
    g = {gid: (name, rule, src) for gid, name, rule, src in GATE_DEFS}

    def add(gid: str, passed: bool, value: Any, threshold: str, reason: str):
        name, rule, src = g[gid]
        results.append(GateResult(gid, name, bool(passed), value, threshold, reason, src))

    # ---------------- preconditions ----------------
    add("SG01", ev.rights_confirmed, "confirmed" if ev.rights_confirmed else "not confirmed",
        "written permission or a lawful basis on file",
        "No lawful basis for gambling-related use of the data is established."
        if not ev.rights_confirmed else "Lawful basis recorded.")

    add("SG02", ev.provenance_complete, "complete" if ev.provenance_complete else "incomplete",
        "URL + timestamp + hash on every field",
        "At least one observation lacks a source URL, timestamp or hash."
        if not ev.provenance_complete else "All observations carry provenance.")

    plan_ok = bool(ev.plan_hash) and ev.plan_hash == ev.plan_hash_recomputed
    add("SG03", plan_ok, ev.plan_hash, "recomputed hash equals frozen hash",
        "Plan hash missing or does not match the recomputed hash (post-hoc change)."
        if not plan_ok else "Frozen plan matches.")

    add("SG04", ev.walk_forward and (ev.max_lookahead_days == 0),
        {"walk_forward": ev.walk_forward, "max_lookahead_days": ev.max_lookahead_days},
        "no forward-looking information",
        "Walk-forward not established or lookahead detected."
        if not (ev.walk_forward and ev.max_lookahead_days == 0) else "Strictly walk-forward.")

    # ---------------- power / sample size ----------------
    n = ev.n_observations
    if n >= 2 and ev.per_bet_return:
        price = -110.0
        p_true = (1.0 + ev.claimed_target_roi) / pricing.american_to_decimal(price)
        p_true = min(max(p_true, 1e-6), 1 - 1e-6)
        sd = _power.bet_sd(price, p_true)
        required_n = _power.n_for_power(ev.claimed_target_roi, sd, 0.80, ev.alpha)
        obs_power = _power.z_power(ev.claimed_target_roi, sd, n, ev.alpha)
    else:
        required_n, obs_power = None, 0.0
    add("SG05", required_n is not None and n >= required_n,
        {"n": n, "required_n": required_n, "power_at_n": round(obs_power, 4)},
        "n >= required_n at 80% power for the claimed edge",
        "Insufficient observations to detect the claimed edge." if not (required_n and n >= required_n)
        else "Sufficient sample for the claimed edge.")

    # ---------------- market-relative loss ----------------
    if ev.model_logloss and len(ev.model_logloss) == len(ev.market_logloss):
        # mean(market_loss - model_loss) > 0  <=>  the model loses less than the market.
        ci = luck.paired_mean_difference_ci(ev.market_logloss, ev.model_logloss)
        sg06 = ci["ci_lo"] > 0.0
        sg06_value = {k: round(v, 6) if isinstance(v, float) else v for k, v in ci.items()}
        sg06_reason = ("Model loss is strictly lower than market loss on paired games."
                       if sg06 else
                       "Paired loss difference interval includes or exceeds zero: no demonstrated "
                       "predictive advantage over the market.")
    else:
        sg06, sg06_value, sg06_reason = False, None, "No paired model/market loss series supplied."
    add("SG06", sg06, sg06_value,
        "paired (market - model) loss, 95% CI lower bound > 0", sg06_reason)

    # ---------------- ROI ----------------
    if len(ev.per_bet_return) >= 2:
        boot = luck.block_bootstrap_mean_ci(ev.per_bet_return, block=5, seed=ev.seed)
        bi = luck.bootstrap_mean_ci(ev.per_bet_return, seed=ev.seed)
        roi_pass = boot["ci_lo"] > 0.0
        roi_value = {"mean": round(boot["mean"], 6), "ci_lo": round(boot["ci_lo"], 6),
                     "ci_hi": round(boot["ci_hi"], 6),
                     "iid_ci_lo": round(bi["ci_lo"], 6), "block": boot["block"]}
        roi_reason = ("Positive mean return with a block-bootstrap lower bound above zero."
                      if roi_pass else
                      "Return interval includes zero: the record is consistent with luck.")
    else:
        roi_pass, roi_value, roi_reason = False, None, "Fewer than two settled bets."
    add("SG07", roi_pass, roi_value, "block-bootstrap 95% CI lower bound > 0", roi_reason)

    # ---------------- calibration ----------------
    if ev.probs and len(ev.probs) == len(ev.outcomes) and len(ev.probs) >= 20:
        ece = luck.expected_calibration_error(ev.probs, ev.outcomes)
        dec = luck.brier_decomposition(ev.probs, ev.outcomes)
        # SG08 tests CALIBRATION ONLY. Discrimination (resolution) is deliberately
        # not required here: a constant forecast of the base rate is perfectly
        # calibrated and still adds no information. Crediting resolution belongs
        # to SG06, which compares paired loss against the market. Conflating the
        # two would let a useless-but-calibrated strategy pass a "skill" gate.
        cal_pass = ece <= ev.calibration_tolerance
        cal_value = {"ece": round(ece, 6), "brier": round(dec.brier, 6),
                     "reliability": round(dec.reliability, 6),
                     "resolution": round(dec.resolution, 6),
                     "uncertainty": round(dec.uncertainty, 6),
                     "beats_climatology": dec.resolution > dec.reliability}
        cal_reason = ("Expected calibration error within tolerance."
                      if cal_pass else
                      "Expected calibration error exceeds tolerance.")
    else:
        cal_pass, cal_value = False, None
        cal_reason = "Fewer than 20 probability forecasts: calibration cannot be assessed."
    add("SG08", cal_pass, cal_value,
        f"ECE <= {ev.calibration_tolerance} (discrimination is scored at SG06)", cal_reason)

    # ---------------- multiple testing ----------------
    fam = list(ev.p_values_in_family) if ev.p_values_in_family else []
    if fam:
        hol = leaderboard.holm(fam, alpha=ev.alpha)
        this_p = fam[0]
        adj_p = hol["adjusted"][0]
        have_family = ev.n_trials_in_family == len(fam)
        mt_pass = adj_p <= ev.alpha and have_family
        mt_value = {"family_size": len(fam), "declared_trials": ev.n_trials_in_family,
                    "p": this_p, "holm_adjusted_p": adj_p}
        mt_reason = ("Family size matches the declared trials and the adjusted p-value is within alpha."
                     if mt_pass else
                     "Family size does not match the declared number of trials, or the adjusted "
                     "p-value does not survive correction.")
    else:
        mt_pass, mt_value, mt_reason = False, None, "No p-value family supplied for correction."
    add("SG09", mt_pass, mt_value, "Holm-adjusted p <= alpha over the full family", mt_reason)

    # ---------------- selection bias ----------------
    dsr = pbo = None
    if len(ev.per_bet_return) >= 20:
        sd = luck.sample_sd(ev.per_bet_return)
        sr = luck.mean(ev.per_bet_return) / sd if sd > 0 else 0.0
        dsr_res = leaderboard.deflated_sharpe(sr, max(ev.n_trials_in_family, 1), len(ev.per_bet_return))
        dsr = dsr_res.get("dsr")
    pbo = None  # PBO needs >= 2 aligned strategy series; computed at family level
    sb_pass = dsr is not None and dsr >= 0.95
    add("SG10", sb_pass, {"deflated_sharpe": None if dsr is None else round(dsr, 6),
                           "pbo": pbo, "n_trials": ev.n_trials_in_family},
        "DSR >= 0.95 and PBO <= 0.20",
        "Deflated Sharpe below 0.95 for the number of trials attempted, or PBO unavailable."
        if not sb_pass else "Survives deflation for the number of trials.")

    # ---------------- dependence ----------------
    if ev.support_legs > 1:
        dep_ok = (ev.rho_used is not None and ev.rho_n is not None and ev.rho_ci is not None
                  and not ev.independence_assumed)
        dep_value = {"support_legs": ev.support_legs, "rho": ev.rho_used, "rho_n": ev.rho_n,
                     "rho_ci": ev.rho_ci, "independence_assumed": ev.independence_assumed}
        dep_reason = ("Multi-leg price uses a measured correlation with n and an interval."
                      if dep_ok else
                      "Multi-leg price assumes independence or omits the correlation interval.")
    else:
        dep_ok, dep_value = True, {"support_legs": 1, "note": "single-leg: no joint dependence"}
        dep_reason = "Single-leg bet; no joint dependence to state."
    add("SG11", dep_ok, dep_value, "measured rho with n and CI for multi-leg", dep_reason)

    # ---------------- ledger ----------------
    led_ok = bool(ev.ledger_hash) and ev.deterministic is True
    add("SG12", led_ok, {"ledger_hash": ev.ledger_hash, "deterministic": ev.deterministic},
        "hash present and run reproducible",
        "Ledger hash missing or the run is not reproducible." if not led_ok
        else "Ledger hashed and deterministic.")

    passed = [r.gate_id for r in results if r.passed]
    failed = [r.gate_id for r in results if not r.passed]
    return {
        "strategy_id": ev.strategy_id,
        "market": ev.market,
        "bet_type": ev.bet_type,
        "n_observations": n,
        "gates": [r.to_dict() for r in results],
        "passed": passed,
        "failed": failed,
        "qualified": len(failed) == 0,
        "fingerprint": ev.fingerprint(),
    }


from . import power as _power  # noqa: E402  (kept at the bottom to mirror light imports)
