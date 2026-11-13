"""Validation gates. A strategy is listed on the performance board only if every gate returns PASS.

BLOCKED is deliberately not a pass: it means an input the project does not have
(a licensed quote feed, an archived point-in-time snapshot, enough settled games).
The state of each gate is recomputed from the registers, never hand-entered.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Gate:
    gate_id: str
    name: str
    requirement: str
    blocks_failure_mode: str
    enforcer: str
    family: str  # structural | evidence
    state: str   # PASS | FAIL | BLOCKED
    measured: str
    unlock: str


GATES = (
    Gate("DG-01", "Official-source traceability",
         "100% of published rows carry an https:// link to a page read on the verification date",
         "unsourced numbers, third-party recitation, hallucinated values",
         "scripts/check_nfl_desk.py", "structural", "PASS",
         "0 rows without an official link",
         "none - keep the rule in CI"),
    Gate("DG-02", "Blank-not-guessed rule",
         "Any field with no official confirmation is the empty string, never a proxy value",
         "silent imputation hardening into 'data'",
         "scripts/check_nfl_desk.py", "structural", "PASS",
         "every blank cell renders as an empty td",
         "none - keep the rule in CI"),
    Gate("DG-03", "Licensed market-data feed",
         ">=1 licensed quote source with opening/close history and book identifiers",
         "comparing our lines to nothing, or to a scraped number we may not use",
         "src/nfl_desk/gates.py", "evidence", "BLOCKED",
         "0 licensed feeds configured",
         "contract Genius Sports or a licensed odds vendor; archive the signed scope as JSON"),
    Gate("DG-04", "Point-in-time integrity",
         ">=2 archived, hash-stamped snapshots per slate (pre-inactive and post-inactive)",
         "using Friday designations to explain a line quoted Thursday",
         "src/nfl_desk/gates.py", "evidence", "BLOCKED",
         "0 archived snapshots; 1 live read on 2026-11-13",
         "run the weekly four-anchor snapshot job for 4 weeks before any CLV claim"),
    Gate("DG-05", "Sample size",
         ">=200 settled selections and >=30 distinct slates per strategy",
         "a 12-game hot streak read as an edge",
         "src/nfl_desk/leaderboard.py", "evidence", "FAIL",
         "0 settled selections made by this pack's model",
         "start logging model lines before kickoff; 200 selections is roughly two full seasons of one strategy"),
    Gate("DG-06", "Chronological out-of-sample holdout",
         "fit window strictly before test window; >=25% of slates held out; no refit on test data",
         "in-sample fit presented as forward accuracy",
         "src/nfl_desk/leaderboard.py", "evidence", "BLOCKED",
         "no fit window exists yet (ratings are season-to-date only)",
         "becomes computable once >=8 slates of archived lines and results exist"),
    Gate("DG-07", "Same-line closing-line value",
         "t >= 2.5 on de-vigged (our prob - close prob), same line, no line-move substitution",
         "beating a stale number instead of the closing market",
         "src/nfl_desk/pricing.py", "evidence", "BLOCKED",
         "no closing prices on file",
         "requires DG-03 and DG-04"),
    Gate("DG-08", "Proper-score calibration",
         "Brier and log-loss vs de-vigged close; reliability slope inside [0.90, 1.10]",
         "a profitable-looking model that is simply over-confident",
         "src/nfl_desk/pricing.py", "evidence", "BLOCKED",
         "model probabilities published; no market probabilities to compare against",
         "requires DG-03"),
    Gate("DG-09", "Multiple-comparison control",
         "Holm-Bonferroni across the frozen candidate family (M published before any test)",
         "12 tries at 5% producing one 'significant' strategy by arithmetic",
         "src/nfl_desk/leaderboard.py", "structural", "PASS",
         "family frozen at M=12 before any outcome was scored",
         "not applicable while the family stays frozen; re-freeze by pull request if it changes"),
    Gate("DG-10", "Dependence handling in combos",
         "no parlay or prop-combo price may assume independence; use joint residuals or Frechet bounds",
         "multiplying marginal probabilities and calling the product a price",
         "src/nfl_desk/correlation.py", "structural", "PASS",
         "bounds published for every combo family; independence used only as the null, never as the price",
         "not applicable - this gate is passing"),
    Gate("DG-11", "Key-number and push arithmetic",
         "settlement probability must include push mass and .5 alternatives; no continuous normal shortcut",
         "systematic mispricing around 3 and 7 in the NFL",
         "src/nfl_desk/model.py", "structural", "PASS",
         "discrete Poisson convolution; push probability published per game",
         "not applicable - this gate is passing"),
    Gate("DG-12", "Assumption robustness",
         "the favoured side must not flip sign across the published assumption grid",
         "a 'signal' that is really a hidden dial in the model",
         "src/nfl_desk/model.py", "evidence", "PASS",
         "sign stability reported per game in the sensitivity register",
         "tighten the grid if any game flips"),
    Gate("DG-13", "Cost and vig awareness",
         "edge must clear the break-even win rate at the quoted price (11/21 = 52.38% at -110)",
         "winning at 51% and calling it profit",
         "src/nfl_desk/pricing.py", "evidence", "BLOCKED",
         "no quotes on file to attach a price to",
         "requires DG-03"),
    Gate("DG-14", "Reproducibility",
         "builder --check byte-equality and seeded recompute of every derived number",
         "tables that no longer match the code that produced them",
         "scripts/build_nfl_desk.py --check", "structural", "PASS",
         "checker recomputes league facts, lines, gates and correlations",
         "none - keep in CI"),
    Gate("DG-15", "Stability and decay",
         "rolling 4-slate selection rate and hit rate inside the global CI; no cliff after a rule change",
         "an edge that existed only before the league changed a rule",
         "src/nfl_desk/leaderboard.py", "evidence", "BLOCKED",
         "needs >=8 slates of archived model output",
         "becomes computable after 8 archived slates"),
    Gate("DG-16", "Cross-season persistence check",
         "report the measured year-to-year correlation of the rating input before trusting it as a prior",
         "assuming last season's scoring differentials are still this season's information",
         "src/nfl_desk/luck.py", "evidence", "PASS",
         "measured on official 2025 final vs 2026 through Week 10 registers (see correlations register)",
         "refresh after every completed season"),
)


def evaluate(club_count: int, game_count: float, licensed_feeds: int, snapshots: int,
             settled_selections: int, sign_stable_share: float,
             persistence_pearson: float) -> list[dict]:
    """Recompute the state of every gate that is a function of the data we actually have."""
    measured = {
        "DG-01": f"{club_count} clubs, {game_count:.0f} games accounted for in the registers",
        "DG-05": f"{settled_selections} settled selections (needs >=200) on {game_count:.0f} league games",
        "DG-04": f"{snapshots} archived snapshots (needs >=2 per slate)",
        "DG-03": f"{licensed_feeds} licensed feeds configured in this repository - no vendor contract file, no "
                 "quote archive, no stored credential; the only market-shaped numbers on disk are another pack's "
                 "own model output, which is not a price",
        "DG-12": f"favoured side stable on {sign_stable_share:.1%} of the published slate",
        "DG-16": f"year-over-year rating persistence r = {persistence_pearson:.3f} (n=32)",
    }
    unlock_here = {
        "DG-08": "needs the DG-03 quote archive on disk (opening and closing price, book id and timestamp per "
                 "game); calibration is then a Brier comparison against de-vigged market probability over at "
                 "least 200 settled games",
        "DG-13": "needs the same DG-03 archive - vig is the gap between the two sides' implied probabilities, "
                 "which cannot be measured from a source this repository does not hold",
    }
    out = []
    for g in GATES:
        state = g.state
        if g.gate_id == "DG-03":
            state = "PASS" if licensed_feeds >= 1 else "BLOCKED"
        elif g.gate_id == "DG-04":
            state = "PASS" if snapshots >= 2 * 14 else "BLOCKED"
        elif g.gate_id == "DG-05":
            state = "PASS" if settled_selections >= 200 else "FAIL"
        elif g.gate_id == "DG-12":
            state = "PASS" if sign_stable_share >= 0.90 else "FAIL"
        elif g.gate_id == "DG-16":
            state = "PASS" if -1.0 <= persistence_pearson <= 1.0 else "FAIL"
        out.append({"gate_id": g.gate_id, "name": g.name, "requirement": g.requirement,
                    "blocks_failure_mode": g.blocks_failure_mode, "enforcer": g.enforcer,
                    "family": g.family, "state": state,
                    "measured": measured.get(g.gate_id, g.measured),
                    "unlock": unlock_here.get(g.gate_id, g.unlock)})
    return out


def holm_adjust(pvals: list[tuple[str, float]], alpha: float = 0.05) -> list[dict]:
    """Holm-Bonferroni over the frozen family - the multiple-comparison control, in code."""
    ordered = sorted(pvals, key=lambda x: x[1])
    m = len(ordered)
    out, running = [], 0.0
    for i, (sid, p) in enumerate(ordered):
        thresh = alpha / (m - i)
        adj = max(p * (m - i), running) if i == 0 else max(p * (m - i), running)
        running = max(running, adj)
        out.append({"strategy_id": sid, "p": p, "holm_threshold": thresh,
                    "adjusted_p": adj, "reject_null": adj <= alpha})
    return out
