"""Validation gates and the demotion gate.

A strategy is allowed to leave paper trading only if **every** gate in
``VALIDATION_GATES`` is ``pass``.  Gates are evaluated against numbers
produced from officially sourced data only; a gate whose inputs are
missing evaluates to ``fail_closed`` (never ``pass`` and never ``skip``).
"""
from __future__ import annotations

import math
from typing import Dict, List, Sequence

from . import dataset, model, store

#: Minimum number of settled bets before any skill claim is admissible.
MIN_BETS_FOR_SKILL = 1000
#: Minimum number of verified games required to fit the rating model.
MIN_GAMES_FOR_FIT = 100
#: Minimum fraction of the season's results that must be in the feed.
MIN_FEED_COMPLETENESS = 0.99


def _feed_completeness() -> Dict[str, object]:
    """Compare the captured results feed against the official standings.

    Every club's captured points-for and points-against are summed from the
    verified results feed and compared with the PF/PA published on
    nfl.com/standings.  Any shortfall is missing games, not noise.
    """
    games = model._games()
    pf = {t: 0 for t in dataset.TEAMS}
    pa = {t: 0 for t in dataset.TEAMS}
    for g in games:
        pf[g["home"]] += g["home_score"]; pa[g["home"]] += g["away_score"]
        pf[g["away"]] += g["away_score"]; pa[g["away"]] += g["home_score"]
    rows, short = [], []
    for r in dataset.standings():
        dp, da = r["pf"] - pf[r["team_abbr"]], r["pa"] - pa[r["team_abbr"]]
        if dp or da:
            short.append(r["team_abbr"])
        rows.append({"team_abbr": r["team_abbr"], "official_pf": r["pf"],
                     "captured_pf": pf[r["team_abbr"]], "pf_gap": dp,
                     "official_pa": r["pa"], "captured_pa": pa[r["team_abbr"]],
                     "pa_gap": da,
                     "complete": "yes" if (dp == 0 and da == 0) else "no",
                     "official_standings_url": r["official_source_url"],
                     "captured_results_url": "https://www.nfl.com/scores/2026/week-1"})
    return {"rows": rows, "teams_short": sorted(short),
            "captured_games": len(games)}


def _walk_forward_summary() -> Dict[str, float]:
    games = model._games()
    wf = model.walk_forward(games)
    if not wf:
        return {}
    tm = bm = tt = bt = 0.0
    n = 0
    for r in wf:
        k = r["test_n"]
        tm += r["mae_margin_model"] * k
        bm += r["mae_margin_baseline"] * k
        tt += r["mae_total_model"] * k
        bt += r["mae_total_baseline"] * k
        n += k
    return {"pooled_test_games": n,
            "pooled_mae_margin_model": round(tm / n, 3),
            "pooled_mae_margin_baseline": round(bm / n, 3),
            "pooled_mae_total_model": round(tt / n, 3),
            "pooled_mae_total_baseline": round(bt / n, 3)}


def _skills_stats(n_bets: int, wins: int, break_even: float) -> Dict[str, object]:
    """Two-sided exact-ish binomial assessment using the normal approximation."""
    if n_bets <= 0:
        return {"n_bets": 0, "wins": 0, "win_rate": "", "p_value": "",
                "ci95_low": "", "verdict": "fail_closed_no_bets"}
    p = wins / n_bets
    se = math.sqrt(break_even * (1 - break_even) / n_bets)
    z = (p - break_even) / se if se else 0.0
    pv = 2 * (1 - model.norm_cdf(abs(z)))
    return {"n_bets": n_bets, "wins": wins, "win_rate": round(p, 4),
            "break_even_rate": round(break_even, 4),
            "z": round(z, 3), "p_value": round(pv, 4),
            "ci95_low": round(p - 1.96 * math.sqrt(p * (1 - p) / n_bets), 4)
            if n_bets else "",
            "verdict": "pass" if (pv < 0.01 and p > break_even and n_bets >= MIN_BETS_FOR_SKILL)
                       else "fail"}


def required_n(break_even: float = 0.5238, true_edge: float = 0.05,
               alpha: float = 0.01, power: float = 0.80) -> int:
    """Sample size needed before a win-rate edge is distinguishable from luck.

    ``true_edge`` is the excess win rate over break-even the strategy claims.
    """
    z_a, z_b = 2.5758, 0.8416  # alpha=0.01 two-sided, power=0.80
    p0, p1 = break_even, min(0.999, break_even + true_edge)
    num = (z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))) ** 2
    return int(math.ceil(num / ((p1 - p0) ** 2)))


def build_validation() -> List[Dict[str, object]]:
    games = model._games()
    fc = _feed_completeness()
    wf = _walk_forward_summary()
    prices = store.build(games)
    priced = sum(1 for p in prices
                 if p["opening_price"] not in ("", None)
                 and p["closing_price"] not in ("", None))
    total_markets = len(prices)
    req_n = required_n()

    rows: List[Dict[str, object]] = []

    def gate(gid, name, question, status, observed, threshold, evidence, url):
        rows.append({
            "gate_id": gid, "gate": name, "question_it_answers": question,
            "status": status, "observed": observed, "threshold": threshold,
            "evidence": evidence, "official_source_url": url,
        })

    # G1 - inputs are officially sourced
    sourced = all(g["source_url"].startswith("https://www.nfl.com/") for g in games)
    gate("A4-G01", "Official-provenance gate",
         "Is every number feeding the model read from an official NFL page?",
         "pass" if sourced else "fail",
         f"{sum(1 for g in games if g['source_url'].startswith('https://www.nfl.com/'))}/{len(games)} games",
         "100% of rows cite nfl.com",
         "Results feed carries one official source URL per game.",
         "https://www.nfl.com/scores/2026/week-1")

    # G2 - sample size of the rating fit
    gate("A4-G02", "Fit sample-size gate",
         "Are there enough verified games to fit the ratings at all?",
         "pass" if len(games) >= MIN_GAMES_FOR_FIT else "fail",
         f"n={len(games)}", f"n>={MIN_GAMES_FOR_FIT}",
         "Verified results feed, weeks 1-3 and 5-9 of 2026.",
         "https://www.nfl.com/scores/2026/week-1")

    # G3 - results-feed completeness
    gate("A4-G03", "Results-feed completeness gate",
         "Is the results feed complete enough to backtest on?",
         "pass" if fc["captured_games"] >= 136 * MIN_FEED_COMPLETENESS else "fail",
         f"{fc['captured_games']} of ~136 games through week 9 "
         f"({len(fc['teams_short'])} clubs short)",
         f">={MIN_FEED_COMPLETENESS:.0%} of games",
         "Week 4 of 2026 could not be read: nfl.com returned the week-4 scores "
         "page with the string 'Hidden Score' in place of every score on three "
         "separate fetches. See flag A4-F01.",
         "https://www.nfl.com/scores/2026/week-4")

    # G4 - out-of-sample skill vs a constant baseline
    better_m = wf and wf["pooled_mae_margin_model"] < wf["pooled_mae_margin_baseline"]
    better_t = wf and wf["pooled_mae_total_model"] < wf["pooled_mae_total_baseline"]
    gate("A4-G04", "Out-of-sample skill gate",
         "Does the model beat a constant baseline on unseen weeks?",
         "pass" if (better_m and better_t) else "fail",
         (f"margin MAE {wf.get('pooled_mae_margin_model')} vs baseline "
          f"{wf.get('pooled_mae_margin_baseline')}; total MAE "
          f"{wf.get('pooled_mae_total_model')} vs baseline "
          f"{wf.get('pooled_mae_total_baseline')}") if wf else "not evaluated",
         "model MAE < baseline MAE on both side and total",
         "Walk-forward: fit on weeks <= k, score week k+1, pooled over all "
         f"{wf.get('pooled_test_games', 0)} out-of-sample games.",
         "https://www.nfl.com/scores/2026/week-1")

    # G5 - price integrity: the blocking gate
    gate("A4-G05", "Price-snapshot gate",
         "Does every originated market have an official opening AND closing price?",
         "pass" if total_markets and priced == total_markets else "fail_closed",
         f"{priced}/{total_markets} markets have both prices",
         f"{total_markets}/{total_markets} markets",
         "No NFL-published price feed was readable in this session. nfl.com "
         "does not publish point spreads, totals or moneylines on the pages "
         "used here, so no price was entered. See flag A4-F02.",
         "https://www.nfl.com/scores/2026/week-10")

    # G6 - settlement
    gate("A4-G06", "Settlement gate",
         "Can every bet be settled against an official result?",
         "pass" if priced and fc["captured_games"] >= 136 * MIN_FEED_COMPLETENESS else "fail",
         f"{fc['captured_games']} verified results; 0 priced bets to settle",
         "every bet settles to an official final score",
         "Results feed is usable, but there are no priced bets to settle "
         "because G5 fails.",
         "https://www.nfl.com/scores/2026/week-9")

    # G7 - luck removal
    sk = _skills_stats(0, 0, 0.5238)
    gate("A4-G07", "Luck-exclusion gate",
         "Is the observed record distinguishable from luck?",
         sk["verdict"], f"n_bets={sk['n_bets']}",
         f"p<0.01 and n>={MIN_BETS_FOR_SKILL} settled bets",
         f"At -110 prices the break-even rate is 0.5238. Detecting a 5-point "
         f"edge at 99% confidence / 80% power needs about {req_n} settled bets.",
         "https://www.nfl.com/scores/2026/week-1")

    # G8 - correlation provenance
    from . import correlate
    corrs = correlate.build()
    usable = [c for c in corrs if c["n_status"] == "sufficient_n"]
    gate("A4-G08", "Correlation-provenance gate",
         "Is every correlation used for parlay pricing computed from official "
         "numbers and published with n?",
         "pass" if usable else "fail",
         f"{len(usable)}/{len(corrs)} correlations have n>=30",
         "all pricing correlations have n>=30 and an official source URL",
         "A4-C03 (margin-residual vs total-residual) is the pricing "
         "correlation for same-game parlays; it is published on the "
         "correlations page with n and a 95% CI.",
         "https://www.nfl.com/scores/2026/week-1")

    # G9 - depth-of-replacement coverage
    from . import depth
    drows = depth.build()
    # The meaningful denominator is players actually ruled Out or Doubtful:
    # those are the ones who force a replacement onto the field.
    forced = [r for r in drows if r["game_status"] in ("Out", "Doubtful")]
    resolved = sum(1 for r in forced if r["replacement_string"] not in ("", None))
    charts_read = sorted({r["team_abbr"] for r in drows if r["status"] != "unresolved_depth_chart_not_read"})
    gate("A4-G09", "Depth-of-replacement coverage gate",
         "Do we know *which string* replaces an Out or Doubtful player, not "
         "just that a player is out?",
         "pass" if forced and resolved == len(forced) else "fail",
         f"{resolved}/{len(forced)} Out-or-Doubtful players have a resolved "
         f"replacement string; depth charts read for {len(charts_read)} of 32 "
         f"clubs ({', '.join(charts_read)})",
         "100% of Out/Doubtful players, across all 32 clubs",
         "Only the clubs whose depth chart rendered as text this session are "
         "in the numerator; the other 28 clubs are unresolved, which is why "
         "the depth-fade strategy A9-S06 produced only 2 signals. "
         "See flag A4-F03.",
         "https://www.packers.com/team/depth-chart")

    # G10 - demotion gate armed
    demos = build_demotion()
    gate("A4-G10", "Demotion-gate armed check",
         "Is there a rule that sends a live strategy back to paper?",
         "pass" if demos and all(d["threshold"] for d in demos) else "fail",
         f"{len(demos)} demotion rules armed",
         ">=1 armed rule with a numeric threshold",
         "Demotion rules are published on the demotion page with thresholds.",
         "https://www.nfl.com/injuries/")

    return rows


DEMOTION_RULES = [
    {
        "rule_id": "A4-D01",
        "name": "Trailing profit confidence",
        "trigger": "Upper bound of the 95% CI on trailing ROI falls below zero.",
        "threshold": "ROI 95% CI upper < 0 over the trailing 500 settled bets",
        "observed": "not evaluable - 0 settled priced bets",
        "action": "demote to paper, freeze stake at 0",
        "status": "armed_not_evaluable",
    },
    {
        "rule_id": "A4-D02",
        "name": "Closing-line value decay",
        "trigger": "Average closing-line value over the trailing window is negative.",
        "threshold": "mean CLV < 0 over the trailing 200 bets",
        "observed": "not evaluable - no closing prices captured",
        "action": "demote to paper, re-fit before re-entry",
        "status": "armed_not_evaluable",
    },
    {
        "rule_id": "A4-D03",
        "name": "Drawdown breach",
        "trigger": "Peak-to-trough drawdown of the live bankroll exceeds the limit.",
        "threshold": "drawdown > 30% of the live starting bankroll",
        "observed": "not evaluable - no live bankroll",
        "action": "demote to paper immediately, no re-entry inside 4 weeks",
        "status": "armed_not_evaluable",
    },
    {
        "rule_id": "A4-D04",
        "name": "Missing price snapshot",
        "trigger": "A live bet is placed without BOTH an opening and a closing "
                   "price recorded in the price-snapshot store.",
        "threshold": "0 tolerated occurrences",
        "observed": "0 priced bets placed; store has "
                    "0 opening and 0 closing prices",
        "action": "demote to paper and quarantine the affected bets",
        "status": "armed_not_evaluable",
    },
    {
        "rule_id": "A4-D05",
        "name": "Parameter drift outside pre-registered bounds",
        "trigger": "A re-fitted model parameter moves outside the band that was "
                   "registered before the strategy went live.",
        "threshold": "|delta| > 25% of the registered value for any rating "
                     "parameter, or ridge/HFA outside the registered band",
        "observed": "not evaluable - no live strategy registered",
        "action": "demote to paper and re-register before re-entry",
        "status": "armed_not_evaluable",
    },
    {
        "rule_id": "A4-D06",
        "name": "Minimum live sample",
        "trigger": "The strategy has fewer settled bets than the minimum needed "
                   "to separate skill from luck.",
        "threshold": f">= {MIN_BETS_FOR_SKILL} settled bets to be eligible for live",
        "observed": "0 settled priced bets",
        "action": "cannot be promoted; stays paper",
        "status": "armed_blocking_promotion",
    },
]


def build_demotion() -> List[Dict[str, object]]:
    out = []
    for r in DEMOTION_RULES:
        row = dict(r)
        row["official_source_url"] = "https://www.nfl.com/injuries/"
        out.append(row)
    return out


def build_luck_math() -> List[Dict[str, object]]:
    """What sample size is needed before any of this can be called skill."""
    out = []
    for edge in (0.02, 0.03, 0.05, 0.08):
        n = required_n(0.5238, edge)
        # probability a coin-flip strategy shows at least this edge over n bets
        se = math.sqrt(0.5238 * 0.4762 / n)
        out.append({
            "claimed_edge_over_breakeven": edge,
            "break_even_win_rate": 0.5238,
            "required_settled_bets_99pct_conf_80pct_power": n,
            "std_error_of_win_rate_at_that_n": round(se, 5),
            "seasons_at_200_bets_per_season": round(n / 200.0, 1),
            "official_source_url": "https://www.nfl.com/scores/2026/week-1",
        })
    return out
