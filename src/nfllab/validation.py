"""Validation gates and the leaderboard.

A strategy qualifies only if EVERY gate passes. Gates are frozen here, before any
result is inspected; the site publishes the same thresholds it scores against.
Anything that cannot be evaluated (missing evidence) is reported as `blocked`,
never as `passed`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

ALPHA_FAMILY = 0.05          # family-wise alpha across all tested candidates
MIN_BETS = 200               # distinct settled bets required for a candidate
MIN_EVENTS = 200             # distinct games required (no double-counting a game)
MIN_CLUSTERS = 60            # distinct slate dates required
MIN_ROI_LOWER = 0.0          # clustered bootstrap lower bound must exceed this
MIN_BSS = 0.0                # Brier skill score vs market must exceed this
MIN_CLV_LOWER = 0.0          # comparable de-vigged CLV lower bound
MIN_SHARPE_DSR = 0.95        # DSR is a probability; require 95% confidence the Sharpe beats the selection benchmark


GATE_IDS = [f"G{i:02d}" for i in range(1, 11)]

GATE_DEFINITIONS = {
    "G01": {"name": "Data rights & market-permission audit", "threshold": "a verified license for every input series"},
    "G02": {"name": "Field-level provenance", "threshold": ">= 99% of rows carry an official https source and a snapshot hash"},
    "G03": {"name": "Chronological walk-forward", "threshold": "fit window strictly before the test window"},
    "G04": {"name": "Sample floor", "threshold": f">= {MIN_BETS} bets, >= {MIN_EVENTS} games, >= {MIN_CLUSTERS} slate dates"},
    "G05": {"name": "Calibration vs market", "threshold": f"Brier skill score > {MIN_BSS} with a clustered CI above 0"},
    "G06": {"name": "Post-vig ROI", "threshold": f"clustered bootstrap lower bound > {MIN_ROI_LOWER}"},
    "G07": {"name": "Closing-line value", "threshold": f"de-vigged same-line CLV lower bound > {MIN_CLV_LOWER}"},
    "G08": {"name": "Multiplicity control", "threshold": f"Bonferroni-adjusted p < {ALPHA_FAMILY}"},
    "G09": {"name": "Dependence & joint sample", "threshold": ">= 30 paired observations and a clustered CI for every combo leg"},
    "G10": {"name": "Deflated Sharpe ratio", "threshold": f"deflated Sharpe probability > {MIN_SHARPE_DSR:.0%} given the number of trials"},
}

# assertions: the registry above must stay complete and in order
assert sorted(GATE_DEFINITIONS) == GATE_IDS


@dataclass
class GateResult:
    gate_id: str
    name: str
    passed: bool | None            # None = blocked (missing evidence)
    observed: str
    threshold: str
    note: str = ""
    source: str = ""

    def as_row(self) -> dict:
        return {"gate_id": self.gate_id, "gate": self.name,
                "status": "pass" if self.passed else ("blocked" if self.passed is None else "fail"),
                "observed": self.observed, "threshold": self.threshold, "note": self.note,
                "source": self.source}


def gate_rights(license_status: str, source_url: str) -> GateResult:
    ok = license_status == "verified"
    return GateResult("G01", "Data rights & market-permission audit", ok,
                      f"license_status={license_status}",
                      "a verified license for every input series",
                      "Community sources without a license cannot certify redistribution or betting use.",
                      source_url)


def gate_provenance(rows_with_urls: int, rows_total: int, source_url: str) -> GateResult:
    if rows_total == 0:
        return GateResult("G02", "Field-level provenance", None, "no rows", "every row carries a source + hash", source=source_url)
    frac = rows_with_urls / rows_total
    return GateResult("G02", "Field-level provenance", frac >= 0.99,
                      f"{rows_with_urls}/{rows_total} rows carry an https source",
                      ">= 99% of rows carry an official https source and a snapshot hash",
                      "Official reads in data/nfl/raw/ carry their URL; the community file does not.",
                      source_url)


def gate_chronology(train_seasons: list[int], test_season: int, source_url: str) -> GateResult:
    ok = bool(train_seasons) and max(train_seasons) < test_season
    return GateResult("G03", "Chronological walk-forward", ok,
                      f"fit seasons {min(train_seasons) if train_seasons else '-'}-{max(train_seasons) if train_seasons else '-'} "
                      f"-> test {test_season}", "fit window strictly before the test window",
                      "No test-season value enters the fit.", source_url)


def gate_sample(n_bets: int, n_events: int, n_clusters: int, source_url: str) -> GateResult:
    ok = n_bets >= MIN_BETS and n_events >= MIN_EVENTS and n_clusters >= MIN_CLUSTERS
    return GateResult("G04", "Sample floor", ok,
                      f"bets={n_bets}, events={n_events}, slates={n_clusters}",
                      f">= {MIN_BETS} bets, >= {MIN_EVENTS} events, >= {MIN_CLUSTERS} slate dates",
                      "Policy minimums, not a power calculation.", source_url)


def gate_calibration(bss: float | None, bss_ci: tuple[float, float] | None, source_url: str) -> GateResult:
    if bss is None:
        return GateResult("G05", "Calibration vs market", None, "not computed", f"BSS > {MIN_BSS} with CI lower bound > 0", source=source_url)
    ok = bss > MIN_BSS and bss_ci is not None and bss_ci[0] > MIN_BSS
    return GateResult("G05", "Calibration vs market", ok,
                      f"BSS={bss:+.4f}, CI {bss_ci[0]:+.4f}..{bss_ci[1]:+.4f}" if bss_ci else f"BSS={bss:+.4f}",
                      f"Brier skill score > {MIN_BSS} and clustered CI lower bound > {MIN_BSS}",
                      "Brier skill score against the de-vigged market probability.", source_url)


def gate_roi(roi: float | None, roi_ci: tuple[float, float] | None, source_url: str) -> GateResult:
    if roi is None or roi_ci is None:
        return GateResult("G06", "Post-vig ROI", None, "not computed", f"ROI CI lower bound > {MIN_ROI_LOWER}", source=source_url)
    ok = roi_ci[0] > MIN_ROI_LOWER
    return GateResult("G06", "Post-vig ROI", ok, f"ROI={roi:+.2%}, CI {roi_ci[0]:+.2%}..{roi_ci[1]:+.2%}",
                      f"slate-clustered ROI lower bound > {MIN_ROI_LOWER}",
                      "Breakeven at -110 is +0% only if the price has no vig; this gate uses the actual offered price.",
                      source_url)


def gate_clv(clv: float | None, clv_ci: tuple[float, float] | None, source_url: str) -> GateResult:
    if clv is None or clv_ci is None:
        return GateResult("G07", "Closing-line value", None, "no closing probability sidecar", f"CLV CI lower bound > {MIN_CLV_LOWER}", source=source_url)
    ok = clv_ci[0] > MIN_CLV_LOWER
    return GateResult("G07", "Closing-line value", ok, f"CLV={clv:+.4f}, CI {clv_ci[0]:+.4f}..{clv_ci[1]:+.4f}",
                      "comparable same-line de-vigged CLV lower bound > 0", source=source_url)


def gate_multiplicity(p_values: list[float], source_url: str) -> GateResult:
    if not p_values:
        return GateResult("G08", "Multiplicity control", None, "no tested candidates", f"Bonferroni across {ALPHA_FAMILY}/{len(p_values)}", source=source_url)
    p_adj = min(p * len(p_values) for p in p_values)
    return GateResult("G08", "Multiplicity control", p_adj < ALPHA_FAMILY,
                      f"min adjusted p={p_adj:.4f} across {len(p_values)} candidates",
                      f"Bonferroni-adjusted p < {ALPHA_FAMILY}",
                      "The family is every candidate tested, including failures.", source_url)


def gate_correlation(r: float | None, n: int, r_ci: tuple[float, float] | None, source_url: str) -> GateResult:
    if r is None:
        return GateResult("G09", "Dependence & joint sample", None, "no paired residual sample",
                          "correlation CI and joint sample present for every combo leg", source=source_url)
    ok = n >= 30 and r_ci is not None
    return GateResult("G09", "Dependence & joint sample", ok,
                      f"r={r:+.3f}, n={n}" + (f", CI {r_ci[0]:+.3f}..{r_ci[1]:+.3f}" if r_ci else ", CI unavailable"),
                      "n >= 30 paired observations and a clustered CI",
                      "Independent multiplication is never the default.", source_url)


def gate_deflated_sharpe(roi_series: np.ndarray, n_trials: int, source_url: str) -> GateResult:
    """Deflated Sharpe ratio (Bailey & Lopez de Prado) on per-bet returns."""
    x = np.asarray(roi_series, dtype=float)
    if len(x) < 30 or x.std() == 0:
        return GateResult("G10", "Deflated Sharpe ratio", None, f"n={len(x)}", f"DSR > {MIN_SHARPE_DSR:.0%}", source=source_url)
    sr = x.mean() / x.std()
    from scipy.stats import norm
    n = len(x)
    if n_trials < 2:
        # Degenerate case: with a single trial there is no selection to deflate.
        # The honest benchmark is "no skill" (SR of 0), not the -inf expected
        # maximum of one draw, which would award an automatic pass.
        exp_max = 0.0
        label = "1 trial (no selection penalty)"
    else:
        e = 0.5772156649
        exp_max = (1 - e) * norm.ppf(1 - 1.0 / n_trials) + e * norm.ppf(1 - 1.0 / (n_trials * np.e))
        label = f"{n_trials} trials"
    se = np.sqrt((1 + 0.5 * sr ** 2) / n)
    dsr = norm.cdf((sr - exp_max) / se)
    return GateResult("G10", "Deflated Sharpe ratio", dsr > MIN_SHARPE_DSR,
                      f"SR={sr:+.4f}/bet, expected max under {label}={exp_max:+.4f}, DSR={dsr:.4f}",
                      f"DSR > {MIN_SHARPE_DSR:.0%}", "Penalises the best strategy for the number of trials run.", source_url)


def evaluate_candidate(candidate: dict, results: dict | None) -> dict:
    """Assemble the gate board for one candidate. `results` None => fail-closed."""
    gates = [gate_rights(candidate.get("license_status", "unverified"), candidate["source_url"]),
             gate_provenance(candidate.get("rows_with_urls", 0), candidate.get("rows_total", 0), candidate["source_url"])]
    if results:
        gates += [gate_chronology(results["train_seasons"], results["test_season"], candidate["source_url"]),
                  gate_sample(results["n_bets"], results["n_events"], results["n_clusters"], candidate["source_url"]),
                  gate_calibration(results.get("bss"), results.get("bss_ci"), candidate["source_url"]),
                  gate_roi(results.get("roi"), results.get("roi_ci"), candidate["source_url"]),
                  gate_clv(results.get("clv"), results.get("clv_ci"), candidate["source_url"]),
                  gate_multiplicity(results.get("p_values", []), candidate["source_url"]),
                  gate_correlation(results.get("r"), results.get("r_n", 0), results.get("r_ci"), candidate["source_url"]),
                  gate_deflated_sharpe(results.get("returns", np.array([])), results.get("n_trials", 1), candidate["source_url"])]
    else:
        for gid, name in (("G03", "Chronological walk-forward"), ("G04", "Sample floor"),
                          ("G05", "Calibration vs market"), ("G06", "Post-vig ROI"),
                          ("G07", "Closing-line value"), ("G08", "Multiplicity control"),
                          ("G09", "Dependence & joint sample"), ("G10", "Deflated Sharpe ratio")):
            gates.append(GateResult(gid, name, None, "not run", "no authorized observation ledger", source=candidate["source_url"]))
    # Status roll-up, fail-closed:
    #   qualifies : every gate passed on evidence
    #   blocked   : nothing failed, but at least one gate could not be evaluated
    #   rejected  : at least one gate failed (missing evidence elsewhere cannot rescue it)
    if all(g.passed is True for g in gates):
        status = "qualifies"
    elif any(g.passed is False for g in gates):
        status = "rejected"
    else:
        status = "blocked"
    return {"candidate_id": candidate["candidate_id"], "name": candidate["name"], "market": candidate["market"],
            "status": status, "gates_passed": sum(g.passed is True for g in gates), "gates_total": len(gates),
            "gates": [g.as_row() for g in gates]}


def leaderboard(boards: list[dict], scores: dict | None = None) -> list[dict]:
    """Rank only qualifiers, by the lower bound of clustered holdout ROI."""
    rows = []
    for b in boards:
        roi_lb = (scores or {}).get(b["candidate_id"], {}).get("roi_lower")
        rows.append({"rank": None, "candidate_id": b["candidate_id"], "name": b["name"], "market": b["market"],
                     "status": b["status"], "gates_passed": b["gates_passed"], "gates_total": b["gates_total"],
                     "roi_lower": roi_lb if b["status"] == "qualifies" else None,
                     "reward": None})
    qual = sorted([r for r in rows if r["status"] == "qualifies"],
                  key=lambda r: (r["roi_lower"] if r["roi_lower"] is not None else -9e9), reverse=True)
    tiers = {1: "Tier A research priority + review slot", 2: "Tier B research priority", 3: "Tier C listing"}
    for i, r in enumerate(qual, start=1):
        r["rank"] = i
        r["reward"] = tiers.get(i, "Listed, no reward")
    return rows
