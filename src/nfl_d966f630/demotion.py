"""The demotion gate: what has to be true to stay live, and what sends you back.

A strategy is **live** when its originated numbers are the pack's reference lines -
the ones the site labels as the model's current best, and the ones the reward tier
attaches to. Everything else is **paper**: graded, published and ranked, but not
carried forward as reference.

The gate is deliberately two-sided:

* the **signal** block decides whether a strategy may be live at all, and whether it
  stays the reference;
* the **risk** block can send a live strategy back to paper on its own - a drawdown
  past the declared budget is a reason to stop publishing someone's numbers as the
  reference even when their lines are accurate;
* the **integrity** block is a hard override: if the price chain, the standings
  reconciliation or the results-feed identities fail, every strategy goes to paper
  in the same run, because none of the numbers below it can be trusted.

Ranking and eligibility are separate on purpose: a strategy can hold the top signal
rank and still be sent back to paper by the calibration gate. That is the whole
point of the requirement - a good number and a safe number are different questions,
and a board that conflates them lets one excuse the other.

Each gate publishes its observed value, the threshold, the comparison and the row it
was computed from, so a failing strategy's page shows the failing trigger verbatim
rather than a status word.
"""

from __future__ import annotations

from . import capture as C
from . import stats as S
from . import backtest as B
from . import leaderboard as L
from . import originate as O
from . import prices as P
from . import results as R
from .cache import memo

STATES = ("live", "paper")

GATES: list[dict[str, str]] = [
    {"gate_id": "D966-G01", "block": "signal", "metric": "n_legs_graded_excluding_pushes",
     "threshold": f">= {L.N_FLOOR}", "comparison": "at_least",
     "why": "a coefficient computed on a handful of games is a story, not a measurement",
     "action_on_fail": "not_eligible_for_live"},
    {"gate_id": "D966-G02", "block": "signal", "metric": "line_quality_status",
     "threshold": "must not be worse_than_naive_baseline_on_at_least_one_market",
     "comparison": "equals_not",
     "why": "a line that is less accurate than the constant a reader could write down "
            "without the model is not a line, it is noise with branding",
     "action_on_fail": "demote_to_paper"},
    {"gate_id": "D966-G03", "block": "signal", "metric": "hit_rate_ci95_high",
     "threshold": ">= break-even probability implied by the quoted price",
     "comparison": "at_least",
     "why": "the interval must at least touch break-even; a cover rate whose upper bound "
            "sits below it is measurably worse than the price it is quoted at",
     "action_on_fail": "demote_to_paper"},
    {"gate_id": "D966-G04", "block": "signal", "metric": "abs_calibration_gap",
     "threshold": f"<= {L.CALIBRATION_TOLERANCE}", "comparison": "at_most",
     "why": "a model that is right on average but systematically overconfident will be "
            "over-bet by every downstream staking rule, which is a staking failure it "
            "will blame on the staking",
     "action_on_fail": "demote_to_paper"},
    {"gate_id": "D966-G05", "block": "signal", "metric": "edge_retention_ratio_last_two_weeks",
     "threshold": ">= 0.50", "comparison": "at_least",
     "why": "edge decay: if the mean quoted margin has collapsed to half of what it was "
            "two weeks earlier, the inputs have stopped carrying information",
     "action_on_fail": "demote_to_paper"},
    {"gate_id": "D966-G06", "block": "risk", "metric": "max_drawdown_units",
     "threshold": "<= 8.0 units", "comparison": "at_most",
     "why": "declared risk budget for a reference line; breaching it stops us publishing "
            "the numbers as the pack's choice even if they stay accurate",
     "action_on_fail": "demote_to_paper"},
    {"gate_id": "D966-G07", "block": "risk", "metric": "mean_half_kelly_stake_fraction",
     "threshold": "<= 0.25", "comparison": "at_most",
     "why": "a staking rule that would have sized more than a quarter of the bank at our "
            "own prices means the probabilities are too confident, whatever the lines say",
     "action_on_fail": "flag_only_staking_block"},
    {"gate_id": "D966-G08", "block": "integrity", "metric": "price_chain_breaks",
     "threshold": "== 0", "comparison": "equals_zero",
     "why": "the snapshot ledger is what open and close mean; a broken hash chain means "
            "the sequence is not the one that was written",
     "action_on_fail": "demote_all_strategies_to_paper"},
    {"gate_id": "D966-G09", "block": "integrity", "metric": "standings_reconciliation_mismatches",
     "threshold": "== 0", "comparison": "equals_zero",
     "why": "every fair line is built from the standings feed; if the feed and the published "
            "standings disagree, every line inherits the disagreement",
     "action_on_fail": "demote_all_strategies_to_paper"},
    {"gate_id": "D966-G10", "block": "integrity", "metric": "results_feed_identity_failures",
     "threshold": "== 0", "comparison": "equals_zero",
     "why": "sum of wins must equal sum of losses, and so on; these identities are what make "
            "the feed a feed rather than a transcription",
     "action_on_fail": "demote_all_strategies_to_paper"},
]

INITIAL_STATE = "paper"
DECISION_BY = "gate:nfl_d966f630_demotion_v1"


@memo
def edge_retention(strategy_id: str) -> dict[str, object]:
    """Mean absolute quoted margin, first two graded weeks versus last two."""
    weeks = sorted({wk for _g, wk, *_r in C.FINAL_GAMES})
    if len(weeks) < 4:
        return {"ratio": float("nan"), "status": "not_enough_weeks_for_a_decay_test"}
    first, last = weeks[:2], weeks[-2:]
    vals = {w: [] for w in weeks}
    for gid, wk, *_r in C.FINAL_GAMES:
        m = B._game_context(gid, wk)
        vals[wk].append(abs(float(m["side"]["model_margin_undamped"])))
    f = S.mean([v for w in first for v in vals[w]])
    l = S.mean([v for w in last for v in vals[w]])
    if not f:
        return {"ratio": float("nan"), "status": "no_graded_games_in_the_reference_window"}
    return {"ratio": l / f, "mean_abs_margin_first_weeks": f, "mean_abs_margin_last_weeks": l,
            "first_weeks": "+".join(str(w) for w in first), "last_weeks": "+".join(str(w) for w in last),
            "status": "measured_on_the_graded_feed_for_every_originated_game",
            "note": "measured on the model's margins rather than a strategy's edge because the pack has no "
                    "market price to have an edge against (flag D966-F01); that is stated rather than hidden "
                    "behind a favourable-looking ratio"}


def _break_even(strategy_id: str) -> tuple[float, str]:
    legs = [l for l in B.settled_leg_rows() if l["strategy_id"] == strategy_id]
    if not legs:
        return float("nan"), "no_graded_legs"
    probs = []
    for leg in legs:
        if leg["market"] == "moneyline":
            probs.append(1.0 / B.price_decimal(float(leg["line_published"])))
        else:
            probs.append(0.5)
    return S.mean(probs), f"even_money_for_side_and_total_and_no_vig_price_for_moneyline_over_{len(legs)}_legs"


@memo
def gate_rows() -> list[dict[str, str]]:
    sig = {r["strategy_id"]: r for r in L.signal_table()}
    stk = {r["strategy_id"]: r for r in L.staking_table()}
    ledger = P.ledger()
    integrity = {
        "D966-G08": len(P.verify_chain(ledger)),
        "D966-G09": sum(1 for r in R.standings_reconciliation()
                           if r["result"] not in ("match", "no_official_badge_club_on_bye")),
        "D966-G10": sum(1 for r in R.feed_identities() if r["result"] != "pass"),
    }
    rows: list[dict[str, str]] = []
    for st in B.STRATEGIES:
        s, k = sig[st.strategy_id], stk[st.strategy_id]
        decay = edge_retention(st.strategy_id)
        be, be_note = _break_even(st.strategy_id)
        observed = {
            "D966-G01": (s["n_legs_graded_excluding_pushes"], "graded legs excluding pushes"),
            "D966-G02": (s["line_quality_status"], "this strategy's own quoted lines versus the naive line"),
            "D966-G03": (s["hit_rate_ci95_high"], f"upper bound against break-even {S.fmt(be, 4)} ({be_note})"),
            "D966-G04": (S.fmt(abs(float(s["calibration_gap"])) if s["calibration_gap"] else float("nan"), 4),
                          "mean predicted cover probability minus observed cover rate"),
            "D966-G05": (S.fmt(float(decay["ratio"]) if decay["ratio"] == decay["ratio"] else float("nan"), 4),
                         f"{decay['status']} on {s['n_legs_graded_excluding_pushes']} graded legs"),
            "D966-G06": (k["max_drawdown_units"], "peak-to-trough units on this strategy's own tickets"),
            "D966-G07": (k["mean_half_kelly_stake_fraction"], "fractional-Kelly fraction the probabilities implied"),
            "D966-G08": (str(integrity["D966-G08"]), "rows whose prev_row_sha256 did not match"),
            "D966-G09": (str(integrity["D966-G09"]), "club-weeks where the feed and the published standings differ"),
            "D966-G10": (str(integrity["D966-G10"]), "identity checks that failed on the results feed"),
        }
        for g in GATES:
            value, note = observed[g["gate_id"]]
            result, detail = _judge(g["comparison"], g["gate_id"], value, be)
            rows.append({
                "gate_id": g["gate_id"],
                "block": g["block"],
                "strategy_id": st.strategy_id,
                "strategy_name": st.name,
                "metric": g["metric"],
                "observed_value": value if value else "",
                "threshold": g["threshold"],
                "comparison": g["comparison"],
                "result": result,
                "observed_versus_threshold": detail,
                "measurement_note": note,
                "why_this_gate_matters": g["why"],
                "action_on_fail": g["action_on_fail"],
                "official_source_url": s["official_source_url"],
                "read_on_utc": C.CAPTURE_DATE_UTC,
            })
    return rows


def _judge(comparison: str, gate_id: str, value: str, break_even: float) -> tuple[str, str]:
    if gate_id in ("D966-G08", "D966-G09", "D966-G10"):
        n = float(value or "nan")
        return ("pass", f"{value} breaks") if n == 0 else ("fail", f"{value} breaks")
    if gate_id == "D966-G02":
        if value.startswith("not_applicable"):
            return "not_evaluated", "no priced line in this strategy to compare"
        if value.startswith("beats_naive"):
            return "pass", "the quoted lines beat the naive baseline"
        if value.startswith("worse_than_naive"):
            return "fail", "at least one quoted market is less accurate than the naive baseline"
        return "not_evaluated", "no graded legs"
    if value == "":
        return "not_evaluated", "no graded legs at this vintage"
    x = float(value)
    if comparison == "at_least":
        ref = break_even if gate_id == "D966-G03" else float(GATES_REF[gate_id])
        if x != x:
            return "not_evaluated", "not computable at this sample size"
        return ("pass" if x >= ref else "fail"), f"{x:.4f} versus {ref:.4f}"
    if comparison == "at_most":
        ref = float(GATES_REF[gate_id])
        if x != x:
            return "not_evaluated", "not computable at this sample size"
        return ("pass" if x <= ref else "fail"), f"{x:.4f} versus {ref:.4f}"
    return "not_evaluated", "no rule"


# numeric thresholds, kept next to the gate definitions the table publishes
GATES_REF = {"D966-G01": float(L.N_FLOOR), "D966-G04": float(L.CALIBRATION_TOLERANCE),
             "D966-G05": 0.50, "D966-G06": 8.0, "D966-G07": 0.25}


def decisions(previous_states: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Current state per strategy, with every failing gate named.

    ``previous_states`` is the state carried in from the run before. It defaults to
    :data:`INITIAL_STATE` for every strategy, because this pack had no live strategy
    before its first publication - so the first run can promote but cannot honestly
    report a demotion. Passing an explicit state is how a later run (or the test that
    exercises the mechanism) evaluates the live -> paper edge.
    """
    previous = previous_states or {}
    rows = gate_rows()
    by_strategy: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_strategy.setdefault(r["strategy_id"], []).append(r)
    sig = {r["strategy_id"]: r for r in L.signal_table()}
    out = []
    integrity_fail = [r for r in rows if r["block"] == "integrity" and r["result"] == "fail"]
    for st in B.STRATEGIES:
        mine = by_strategy[st.strategy_id]
        signal_fail = [r for r in mine if r["block"] == "signal" and r["result"] == "fail"]
        risk_fail = [r for r in mine if r["block"] == "risk" and r["result"] == "fail"]
        to_state = "paper"
        if not signal_fail and not risk_fail and not integrity_fail and st.status != "blocked":
            to_state = "live"
        fail_ids = [r["gate_id"] for r in signal_fail + risk_fail + integrity_fail]
        out.append({
            "strategy_id": st.strategy_id,
            "strategy_name": st.name,
            "previous_state": previous.get(st.strategy_id, INITIAL_STATE),
            "state": to_state,
            "state_before_integrity_override": "live" if not (signal_fail or risk_fail) else "paper",
            "eligible_for_reward_tier": "yes" if to_state == "live" else "no",
            "failing_gate_ids": "; ".join(fail_ids),
            "failing_gate_detail": " | ".join(
                f"{r['gate_id']} {r['metric']}={r['observed_value']} vs {r['threshold']}"
                for r in signal_fail + risk_fail + integrity_fail),
            "not_evaluated_gate_ids": "; ".join(
                r["gate_id"] for r in mine if r["result"] == "not_evaluated"),
            "signal_rank": sig[st.strategy_id].get("signal_rank", ""),
            "signal_status": sig[st.strategy_id]["signal_status"],
            "rule_verbatim": st.rule,
            "blocked_reason": st.blocked_reason,
            "decision_by": DECISION_BY,
            "effective_on_utc": C.CAPTURE_DATE_UTC,
            "decision": ("promote_to_live" if to_state == "live" and previous.get(st.strategy_id, INITIAL_STATE) != "live"
                         else "stay_live" if to_state == "live"
                         else "demote_to_paper" if previous.get(st.strategy_id, INITIAL_STATE) == "live"
                         else "not_promoted"),
            "official_source_url": sig[st.strategy_id]["official_source_url"],
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


def transitions(previous_states: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Only the rows where a state actually changed - the demotions and promotions."""
    out = []
    for i, d in enumerate(decisions(previous_states), start=1):
        if d["state"] == d["previous_state"]:
            continue
        kind = "promotion_to_live" if d["state"] == "live" else "demotion_to_paper"
        out.append({
            "transition_id": f"D966-ST-{i:02d}",
            "strategy_id": d["strategy_id"],
            "strategy_name": d["strategy_name"],
            "from_state": d["previous_state"],
            "to_state": d["state"],
            "kind": kind,
            "trigger_gate_ids": d["failing_gate_ids"],
            "trigger_detail": d["failing_gate_detail"],
            "rank_at_time_of_decision": d["signal_rank"],
            "note": ("a strategy can hold a top signal rank and still be sent back to paper - the gate answers "
                     "a different question from the ranking"
                     if kind == "demotion_to_paper" else
                     "promotion means this strategy's numbers are the pack's reference line for the next week"),
            "decision_by": d["decision_by"],
            "effective_on_utc": d["effective_on_utc"],
            "official_source_url": d["official_source_url"],
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out


def live_strategies(previous_states: dict[str, str] | None = None) -> list[str]:
    return [d["strategy_id"] for d in decisions(previous_states) if d["state"] == "live"]


def demotion_watch() -> list[dict[str, str]]:
    """What would send each strategy back to paper, computed on real numbers today.

    The first run of the pack has no live strategy to demote, so the mechanism is
    published as a standing test rather than a claim that a demotion happened. Every
    row here is a gate that currently fails for that strategy: if it were live, that
    row is the reason it goes back to paper, verbatim.
    """
    rows = gate_rows()
    out = []
    for st in B.STRATEGIES:
        mine = [r for r in rows if r["strategy_id"] == st.strategy_id and r["result"] == "fail"]
        out.append({
            "strategy_id": st.strategy_id,
            "strategy_name": st.name,
            "state": [d for d in decisions() if d["strategy_id"] == st.strategy_id][0]["state"],
            "gates_that_would_fire": "; ".join(r["gate_id"] for r in mine),
            "n_gates_failing": str(len(mine)),
            "first_failing_detail": mine[0]["observed_versus_threshold"] if mine else "",
            "first_failing_metric": mine[0]["metric"] if mine else "",
            "would_demote_on_next_run": "yes" if mine else "no",
            "mechanism_note": ("the pack's first publication has no previously live strategy, so this row is "
                               "the standing test, not a reported demotion"
                               if not mine else "this row is what a demotion notice would carry"),
            "official_source_url": C.link_for("SCHED-W9"),
            "read_on_utc": C.CAPTURE_DATE_UTC,
        })
    return out
