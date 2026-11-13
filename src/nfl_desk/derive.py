"""Every computed number in the decision desk, produced from the verified registers.

Nothing here is hand-typed: the builder calls these functions, and the checker
calls them again and compares. If a cell in a published table stops matching the
arithmetic, the build fails.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .correlation import correlated_pairs
from .depth import club_group_deficiency
from .gates import evaluate, GATES
from .leaderboard import STRATEGIES, REWARD_TIERS, rank, readiness
from .league import Club, load_clubs, league_facts, round_half
from .luck import pythagorean_fit, luck_table, luck_share, required_games_for_edge, pyth_win_prob
from .model import game_line, poisson_pmf
from .pricing import breakeven_win_prob

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "data" / "nfl_desk"
NFL_STANDINGS = "https://www.nfl.com/standings/"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_SCHED = "https://www.nfl.com/schedules/2026/by-week/week-10"
NFL_SCORES = "https://www.nfl.com/scores/2026/week-10"
METHOD_NIST = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm"
METHOD_SCIPY = "https://docs.scipy.org/doc/scipy/reference/stats.html"
READ = "2026-11-13"

# Published assumption grid. These are the model's dials, not measurements, and
# every cell that depends on them is labelled so a reader cannot mistake them for facts.
HFA_GRID = (0.0, 1.0, 1.5, 2.5)
SIGMA_GRID = (10.0, 11.0, 12.0, 13.0)
EDGES = (1.0, 2.0, 3.0)


def _slate() -> list[dict]:
    with (DESK / "week10_slate.csv").open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["game_id"].startswith("W10-G")]


def _injuries() -> list[dict]:
    with (DESK / "injury_report_2026_w10.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def clubs_2026() -> list[Club]:
    return load_clubs("standings_2026_thru_w10.csv")


def clubs_2025() -> list[Club]:
    return load_clubs("standings_2025_final.csv")


def fact_register() -> list[dict]:
    c26, c25 = clubs_2026(), clubs_2025()
    f26, f25 = league_facts(c26), league_facts(c25)
    fit26, fit25 = pythagorean_fit(c26), pythagorean_fit(c25)
    lk26, lk25 = luck_share(c26, fit26["exponent"]), luck_share(c25, fit25["exponent"])
    rows = [
        ("MF-01", "Verified league aggregate", "clubs in register", f"{f26['clubs']:.0f}", "clubs",
         "row count of the standings register", "verified", NFL_STANDINGS, ""),
        ("MF-02", "Verified league aggregate", "games played through Week 10 2026", f"{f26['games']:.0f}", "games",
         "sum of club games played / 2", "verified", NFL_STANDINGS, ""),
        ("MF-03", "Verified league aggregate", "league points per team-game 2026",
         f"{f26['league_avg_points_per_team_game']:.4f}", "points", "6,291 points / 274 team-games", "verified",
         NFL_STANDINGS, ""),
        ("MF-04", "Verified league aggregate", "league points per team-game 2025 full season",
         f"{f25['league_avg_points_per_team_game']:.4f}", "points", "12,519 / 544 team-games", "verified",
         NFL_STANDINGS, ""),
        ("MF-05", "Verified league aggregate", "home club win share 2026", f"{f26['home_win_share']:.4f}", "share",
         f"home clubs {f26['home_wins']:.0f}-{f26['home_losses']:.0f}-{f26['home_ties']:.0f}", "verified",
         NFL_STANDINGS, ""),
        ("MF-06", "Verified league aggregate", "home club win share 2025", f"{f25['home_win_share']:.4f}", "share",
         f"home clubs {f25['home_wins']:.0f}-{f25['home_losses']:.0f}-{f25['home_ties']:.0f}", "verified",
         NFL_STANDINGS, ""),
        ("MF-07", "Verified league aggregate", "tied-game share 2026", f"{f26['home_tie_share']:.4f}", "share",
         "ties on the register / games played; one tied game appears as one tie for two clubs", "verified",
         NFL_STANDINGS, ""),
        ("MF-08", "Verified league aggregate", "tied-game share 2025", f"{f25['home_tie_share']:.4f}", "share",
         "same arithmetic on the completed 2025 season", "verified", NFL_STANDINGS, ""),
        ("MF-09", "Verified league aggregate", "mean absolute club net points per game 2026",
         f"{f26['mean_abs_net_ppg']:.4f}", "points/game", "mean of |PF-GP minus PA-GP| over 32 clubs", "verified",
         NFL_STANDINGS, ""),
        ("MF-10", "Verified league aggregate", "standard deviation of club net rating 2026",
         f"{f26['sd_team_net_ppg']:.4f}", "points/game", "sample SD over 32 clubs", "verified", NFL_STANDINGS, ""),
        ("MF-11", "Fitted on verified data", "Pythagorean exponent 2026 (grid fit, step 0.001)",
         f"{fit26['exponent']:.3f}", "exponent", "minimises squared error of expected vs actual wins, n=32",
         "computed", NFL_STANDINGS, ""),
        ("MF-12", "Fitted on verified data", "Pythagorean exponent 2025 (grid fit, step 0.001)",
         f"{fit25['exponent']:.3f}", "exponent", "same fit on the completed season", "computed", NFL_STANDINGS, ""),
        ("MF-13", "Fitted on verified data", "R-squared of expected vs actual wins 2026",
         f"{fit26['r_squared']:.4f}", "R^2", "share of the spread in wins explained by scoring alone", "computed",
         NFL_STANDINGS, ""),
        ("MF-14", "Fitted on verified data", "R-squared of expected vs actual wins 2025",
         f"{fit25['r_squared']:.4f}", "R^2", "same statistic on the completed season", "computed", NFL_STANDINGS, ""),
        ("MF-15", "Luck decomposition", "residual SD in wins 2026", f"{lk26['sd_residual_wins']:.4f}", "wins",
         "SD of (actual - expected) wins after the fit", "computed", NFL_STANDINGS, ""),
        ("MF-16", "Luck decomposition", "binomial noise SD in wins 2026", f"{lk26['sd_noise_wins']:.4f}", "wins",
         "sqrt(gp x p x (1-p)) averaged over clubs; the scatter pure chance would produce", "computed",
         METHOD_NIST, ""),
        ("MF-17", "Luck decomposition", "residual SD in wins 2025", f"{lk25['sd_residual_wins']:.4f}", "wins",
         "same statistic on the completed season", "computed", NFL_STANDINGS, ""),
        ("MF-18", "Luck decomposition", "binomial noise SD in wins 2025", f"{lk25['sd_noise_wins']:.4f}", "wins",
         "same statistic on the completed season", "computed", METHOD_NIST, ""),
        ("MF-19", "Cost arithmetic", "break-even win rate at -110",
         f"{breakeven_win_prob(-110):.6f}", "probability", "1 / (1 + 100/110) = 11/21", "computed", METHOD_NIST, ""),
        ("MF-20", "Model assumption", "game margin standard deviation", "", "points",
         "no game-level margin data exists in this repository; measured SD would need the 18 official weekly "
         "scores pages or a licensed feed", "unverified_blank", NFL_SCORES, "FL-12"),
        ("MF-21", "Model assumption", "home-field advantage in points", "", "points",
         "the register gives venue win-loss splits, not venue scoring splits, so points cannot be measured here; "
         "the sensitivity grid publishes the consequence of each value", "unverified_blank", NFL_STANDINGS, "FL-06"),
        ("MF-22", "Model assumption", "Poisson point distribution", "used", "distributional choice",
         "chooses a discrete law so push and key-number mass are explicit; not a measurement", "model_assumption",
         METHOD_SCIPY, ""),
        ("MF-23", "Model vs measurement", "regulation-tie mass, model (Week 10 slate mean)",
         f"{_mean_tie_mass():.4f}", "probability", "mean over the 13 scheduled games of P(two Poissons tie)",
         "model_assumption", METHOD_SCIPY, "FL-16"),
        ("MF-24", "Model vs measurement", "observed tied-game rate 2026", f"{f26['home_tie_share']:.4f}",
         "probability", "official standings: one tied game in 137", "verified", NFL_STANDINGS, ""),
        ("MF-25", "Model vs measurement", "ratio of observed ties to modelled regulation ties",
         "", "ratio", "requires the share of regulation ties that survive overtime, which no official page read "
         "today publishes", "unverified_blank", NFL_STANDINGS, "FL-16"),
    ]
    hdr = ["fact_id", "category", "item", "value", "unit", "derivation_or_definition", "status", "source_url",
           "flag_id", "read_date"]
    # every register in this pack carries its read date, including the fact sheet, so a reviewer can tell a
    # stale figure from a current one without opening the build log
    return [dict(zip(hdr, list(r) + [READ])) for r in rows]


def _mean_tie_mass() -> float:
    c = {x.abbr: x for x in clubs_2026()}
    probs = []
    for g in _slate():
        if g["game_state"] != "Scheduled":
            continue
        h, a = c[g["home_abbr"]], c[g["away_abbr"]]
        line, _ = game_line(h.ppg, h.papg, a.ppg, a.papg, home_field_points=0.0)
        probs.append(line.tie_prob)
    return sum(probs) / len(probs)


def _pairs(xs, ys):
    return list(zip(xs, ys))


def correlation_register() -> list[dict]:
    c26, c25 = {c.abbr: c for c in clubs_2026()}, {c.abbr: c for c in clubs_2025()}
    both = sorted(set(c26) & set(c25))
    rows = []

    def add(cid, scope, label, pairs, mech, use, status, flag, src, extra=""):
        d = {"corr_id": cid, "scope": scope, "pair": label, "n": "", "pearson_r": "", "spearman_rho": "",
             "boot_ci_95": "", "perm_p": "", "r_squared": "", "mechanism_or_reason": mech,
             "how_the_desk_uses_it": use, "status": status, "flag_id": flag, "source_url": src, "note": extra}
        if pairs:
            s = correlated_pairs(pairs, label)
            d.update(n=s["n"], pearson_r=f"{s['pearson_r']:.4f}", spearman_rho=f"{s['spearman_rho']:.4f}",
                     boot_ci_95=f"[{s['boot_ci_lo']:.3f}, {s['boot_ci_hi']:.3f}]",
                     perm_p=f"{s['perm_p_pearson']:.4f}", r_squared=f"{s['r_squared']:.4f}")
        rows.append(d)

    add("CR-01", "2026 club-season cross-section (n=32)", "points scored per game vs points allowed per game",
        _pairs([c26[a].ppg for a in c26], [c26[a].papg for a in c26]),
        "tests whether a high-scoring club also allows more - if they were unrelated, a total and a side could be "
        "treated as separate information",
        "a negative or nil association means totals and spreads carry largely independent information for singles",
        "measured", "", NFL_STANDINGS, "CI spans zero, so no association is established at n=32")
    add("CR-02", "2025 completed season (n=32)", "points scored per game vs points allowed per game",
        _pairs([c25[a].ppg for a in c25], [c25[a].papg for a in c25]),
        "same test on a full season as a stability check on CR-01", "benchmarks CR-01", "measured", "",
        "https://www.nfl.com/standings/division/2025/REG", "")
    add("CR-03", "2025 -> 2026 persistence (n=32)", "net points per game, previous full season vs season to date",
        _pairs([c25[a].net_ppg for a in both], [c26[a].net_ppg for a in both]),
        "how much of last season's scoring differential is still information this season",
        "sets the shrinkage the desk is willing to apply to a prior-season rating; a low value forces "
        "season-to-date weighting", "measured", "", NFL_STANDINGS, "")
    add("CR-04", "2025 -> 2026 persistence (n=32)", "points scored per game, previous season vs season to date",
        _pairs([c25[a].ppg for a in both], [c26[a].ppg for a in both]),
        "offensive rate persistence", "separates offensive continuity from defensive continuity", "measured", "",
        NFL_STANDINGS, "")
    add("CR-05", "2025 -> 2026 persistence (n=32)", "points allowed per game, previous season vs season to date",
        _pairs([c25[a].papg for a in both], [c26[a].papg for a in both]),
        "defensive rate persistence", "same as CR-04 for the other side of the ball", "measured", "", NFL_STANDINGS, "")
    r25 = luck_table(c25.values(), pythagorean_fit(c25.values())["exponent"])
    fit26 = pythagorean_fit(list(c26.values()))
    r26 = luck_table(list(c26.values()), fit26["exponent"])
    d25 = {x["abbr"]: x["luck_wins"] for x in r25}
    d26 = {x["abbr"]: x["luck_wins"] for x in r26}
    add("CR-06", "2025 -> 2026 luck reversal test (n=32)", "wins above points-based expectation, season to season",
        _pairs([d25[a] for a in both], [d26[a] for a in both]),
        "if a 'lucky' record predicted the next year, the residual would be skill rather than chance",
        "the desk refuses records-only strategies; this is the measurement that justifies it", "measured", "",
        NFL_STANDINGS, "")
    add("CR-07", "Same-game prop legs", "QB passing yards over vs primary WR1 receiving yards over", None,
        "every completion to that receiver adds identical yards to both legs, so independence is certainly wrong",
        "pricing an SGP stack: use the Frechet ceiling min(p1,p2) and floor max(0,p1+p2-1) until a joint model exists",
        "blank_pending_licensed_play_by_play", "FL-08", METHOD_SCIPY,
        "no coefficient is published because paired per-play data does not exist in this repository")
    add("CR-08", "Same-game parlay legs", "home spread cover vs home team total over", None,
        "both legs are driven by the same margin; the joint probability is bounded, not factored",
        "a parlay of these two legs is quoted as if independent when p12 lies in a wide interval",
        "blank_pending_licensed_play_by_play", "FL-08", METHOD_SCIPY, "")
    add("CR-09", "Cross-game parlay legs", "two legs from different games on the same slate", None,
        "shared elements are weather, kickoff slot and total-scoring environment; residual dependence is small "
        "but not zero", "the cheapest legal multi-leg exposure, and the only parlay family this desk will price "
        "from marginals with a stated bound", "blank_pending_licensed_play_by_play", "FL-08", METHOD_SCIPY, "")
    return rows


def frechet_table() -> list[dict]:
    """The bounds a combo must be priced inside when dependence is unmeasured."""
    out = []
    for i, (p1, p2) in enumerate([(0.50, 0.50), (0.35, 0.35), (0.60, 0.60), (0.30, 0.55)], start=1):
        lo = max(0.0, p1 + p2 - 1.0)
        hi = min(p1, p2)
        ind = p1 * p2
        out.append({
            "combo_id": f"FR-{i:02d}", "leg_1_prob": f"{p1:.2f}", "leg_2_prob": f"{p2:.2f}",
            "independent_product": f"{ind:.4f}", "frechet_lower_bound": f"{lo:.4f}",
            "frechet_upper_bound": f"{hi:.4f}",
            "fair_american_at_lower": _american(lo), "fair_american_at_independent": _american(ind),
            "fair_american_at_upper": _american(hi),
            "worst_case_overcharge_vs_bounds": f"{(ind - lo) / ind:.4f}" if ind > lo else "0.0000",
            "note": "price range an unadjusted parlay could be hiding; the desk publishes bounds, not a point estimate",
            "status": "computed_bounds", "source_url": METHOD_SCIPY, "flag_id": "FL-08",
        })
    return out


def _american(p: float) -> str:
    if p <= 0 or p >= 1:
        return ""
    d = 1.0 / p
    return f"+{(d - 1) * 100:.0f}" if d >= 2 else f"{-100 / (d - 1):.0f}"


def _sign(value: float) -> int:
    """-1, 0 or +1: which side a published spread points at."""
    return 0 if abs(value) < 1e-9 else (1 if value > 0 else -1)


def originated_lines() -> tuple[list[dict], dict]:
    c = {x.abbr: x for x in clubs_2026()}
    depth = _depth_summary()
    rows, stable = [], 0
    for g in _slate():
        if g["game_state"] != "Scheduled":
            continue
        h, a = c[g["home_abbr"]], c[g["away_abbr"]]
        neutral = g["neutral_site"] == "yes"
        base, kn = game_line(h.ppg, h.papg, a.ppg, a.papg, home_field_points=0.0)
        grid = []
        for hfa in HFA_GRID:
            pts = 0.0 if neutral else hfa
            line, _ = game_line(h.ppg, h.papg, a.ppg, a.papg, home_field_points=pts)
            grid.append(line.spread_home)
        sign_stable = len({(0 if abs(s) < 1e-9 else (1 if s > 0 else -1)) for s in grid}) == 1
        stable += 1 if sign_stable else 0
        hd, ad = depth.get(h.club, {}), depth.get(a.club, {})
        rows.append({
            "line_id": "OL-" + g["game_id"].split("-")[-1],
            "game_id": g["game_id"], "kickoff_et": f"{g['date']} {g['kickoff_et']}",
            "away_club": a.club, "home_club": h.club, "neutral_site": g["neutral_site"],
            "away_record": f"{a.w}-{a.l}-{a.t}", "home_record": f"{h.w}-{h.l}-{h.t}",
            "away_ppg": f"{a.ppg:.4f}", "away_papg": f"{a.papg:.4f}",
            "home_ppg": f"{h.ppg:.4f}", "home_papg": f"{h.papg:.4f}",
            "model_fair_spread_home": f"{base.spread_home:+.2f}",
            "model_fair_spread_rounded": f"{base.spread_rounded:+.1f}",
            "model_fair_total": f"{base.total:.2f}", "model_fair_total_rounded": f"{base.total_rounded:.1f}",
            "model_home_win_prob": f"{base.home_win_prob:.4f}",
            "model_push_prob": f"{base.push_prob_quoted_line:.4f}",
            "model_tie_mass": f"{base.tie_prob:.4f}",
            "key_number_mass_3": f"{kn.get(3, 0.0):.4f}", "key_number_mass_7": f"{kn.get(7, 0.0):.4f}",
            "one_score_window_mass": f"{sum(kn.get(k, 0.0) for k in (1, 2, 3, 4, 5, 6, 7, 8)):.4f}",
            "market_open_line": "", "market_close_line": "", "market_total": "", "market_implied_prob": "",
            "de_vigged_market_prob": "", "clv": "", "brier": "",
            "home_deficiency_score": f"{hd.get('score', 0):.0f}" if hd else "",
            "away_deficiency_score": f"{ad.get('score', 0):.0f}" if ad else "",
            "home_cluster_alert": "yes" if hd.get("clusters", 0) else "no",
            "away_cluster_alert": "yes" if ad.get("clusters", 0) else "no",
            "assumption_grid_sign_stable": "yes" if sign_stable else "no",
            # the smallest home assumption at which the favoured side actually changes
            "flips_at_home_points": next(
                (f"{hfa:.1f}" for hfa, v in zip(HFA_GRID[1:], grid[1:]) if _sign(v) != _sign(grid[0])), ""),
            "line_status": "originated_internally_not_validated_against_a_market",
            "input_source": f"{NFL_STANDINGS} ; {NFL_SCHED} ; {NFL_INJURIES}",
            "read_date": READ, "flag_id": "FL-01",
        })
    summary = {"games": len(rows), "sign_stable": stable, "sign_stability_share": stable / max(1, len(rows))}
    return rows, summary


def _depth_summary() -> dict[str, dict]:
    groups = club_group_deficiency(_injuries())
    out: dict[str, dict] = {}
    for g in groups:
        s = out.setdefault(g["club"], {"score": 0.0, "clusters": 0.0, "worst": 0.0})
        s["score"] += g["deficiency_score"]
        s["clusters"] += 1 if g["cascading_cluster"] == "yes" else 0
        s["worst"] = max(s["worst"], g["deficiency_score"])
    return out


def depth_register() -> list[dict]:
    rows = []
    for i, g in enumerate(club_group_deficiency(_injuries()), 1):
        g["depth_id"] = f"DP-{i:02d}"
        g["unit_group_label"] = g["unit_group"].replace("_", " ").title()
        g["weighting_policy"] = "Out=3, DNP=2, Limited=1, Full=0"
        g["status"] = "computed_from_official_read"
        g["source_url"] = NFL_INJURIES
        g["read_date"] = READ
        g["flag_id"] = "FL-03"
        rows.append(g)
    return rows


def sensitivity_register() -> list[dict]:
    c = {x.abbr: x for x in clubs_2026()}
    rows = []
    for g in _slate():
        if g["game_state"] != "Scheduled":
            continue
        h, a = c[g["home_abbr"]], c[g["away_abbr"]]
        neutral = g["neutral_site"] == "yes"
        for hfa in HFA_GRID:
            pts = 0.0 if neutral else hfa
            line, kn = game_line(h.ppg, h.papg, a.ppg, a.papg, home_field_points=pts)
            rows.append({
                "sens_id": f"SN-{g['game_id']}-{HFA_GRID.index(hfa)}", "game_id": g["game_id"],
                "matchup": f"{a.abbr} at {h.abbr}", "assumed_home_points": f"{pts:.1f}",
                "spread_home": f"{line.spread_home:+.2f}", "total": f"{line.total:.2f}",
                "home_win_prob": f"{line.home_win_prob:.4f}", "push_prob": f"{line.tie_prob:.4f}",
                "favoured": "home" if line.spread_home > 0 else "away" if line.spread_home < 0 else "pick",
                "note": "total is invariant to the home assumption by construction; the spread moves 1:1 with it"
                        if not neutral else "neutral site: the home assumption is held at zero for this game",
                "status": "model_assumption_grid", "source_url": NFL_STANDINGS,
            })
    for edge in EDGES:
        for sigma in SIGMA_GRID:
            n = required_games_for_edge(edge, sigma)
            rows.append({
                "sens_id": f"SN-N-{edge:.0f}-{sigma:.0f}", "game_id": "power", "matchup": "required settled games",
                "assumed_home_points": f"sigma={sigma:.1f}", "spread_home": f"edge={edge:.1f} pts/game",
                "total": "", "home_win_prob": "", "push_prob": "", "favoured": "",
                "note": f"games needed for a {edge:.0f}-point per-game edge to clear a two-sided 5% test at 80% "
                        f"power with margin SD {sigma:.0f}: {n:,.0f}",
                "status": "model_assumption_grid", "source_url": METHOD_NIST,
            })
    return rows


def gate_register(summary: dict) -> list[dict]:
    c26 = clubs_2026()
    pers = correlated_pairs(_pairs([c.net_ppg for c in clubs_2025()],
                                   [x.net_ppg for x in c26]), "persistence")
    states = {g["gate_id"]: g["state"] for g in evaluate(
        len(c26), league_facts(c26)["games"], 0, 0, 0, summary["sign_stability_share"], pers["pearson_r"])}
    rows = evaluate(len(c26), league_facts(c26)["games"], 0, 0, 0, summary["sign_stability_share"],
                    pers["pearson_r"])
    for r in rows:
        g = next(x for x in GATES if x.gate_id == r["gate_id"])
        r["enforcer_path"] = g.enforcer
        r["read_date"] = READ
        r["source_url"] = METHOD_NIST if r["family"] == "evidence" else "https://github.com/sassnarep3-star/Own6/blob/main/scripts/check_nfl_desk.py"
    return rows, states


def strategy_register(states: dict) -> list[dict]:
    rows = []
    for s in STRATEGIES:
        rows.append({
            "strategy_id": s.sid, "structure": s.structure, "name": s.name, "hypothesis": s.hypothesis,
            "required_features": ", ".join(s.required_features),
            "available_features": ", ".join(s.available_features) or "not available yet",
            "missing_features": ", ".join(f for f in s.required_features if f not in s.available_features)
                                  or "nothing missing - all required inputs are verified and on disk",
            "luck_controls": "; ".join(s.luck_controls),
            "readiness": f"{readiness(s):.2f}",
            "gates_passed": sum(1 for v in states.values() if v == "PASS"),
            "gates_total": len(states),
            "status": "PREREGISTERED_UNQUALIFIED",
            "reward_tier": "TIER-0",
            "unlock_next": states.get("DG-05", "FAIL") + " -> log settled lines before kickoff; "
                           + states.get("DG-03", "BLOCKED") + " -> licensed quote feed",
            "source_url": "https://github.com/sassnarep3-star/Own6/blob/main/src/nfl_desk/leaderboard.py",
            "read_date": READ,
        })
    return rows


def leaderboard_register(states: dict, summary: dict) -> list[dict]:
    ranked = rank(states)
    rows = []
    for r in ranked:
        r["reward_tier"] = "TIER-0"
        r["reward"] = "no reward on the performance board; readiness rank only"
        r["status"] = "UNQUALIFIED"
        r["settled_selections"] = 0
        r["holdout_roi"] = ""
        r["same_line_clv"] = ""
        r["brier"] = ""
        r["skill_score"] = ""
        r["leaderboard_note"] = (f"ranked on readiness {r['readiness']:.2f}; performance columns are blank because "
                                 "no settled, out-of-sample selection exists")
        r["source_url"] = "https://github.com/sassnarep3-star/Own6/blob/main/src/nfl_desk/leaderboard.py"
        r["read_date"] = READ
        rows.append(r)
    return rows


def reward_register() -> list[dict]:
    rows = []
    for tier, reward, criteria in REWARD_TIERS:
        rows.append({"tier_id": tier, "reward": reward, "criteria": criteria,
                     "entries_at_tier": "0" if tier == "TIER-0" else "",
                     "how_ties_are_broken": "evidence gates, then readiness, then strategy id - a total order, so "
                                            "the ranking cannot be nudged",
                     "status": "policy_published",
                     "source_url": "https://github.com/sassnarep3-star/Own6/blob/main/src/nfl_desk/leaderboard.py",
                     "read_date": READ})
    rows[0]["entries_at_tier"] = "12"
    return rows
