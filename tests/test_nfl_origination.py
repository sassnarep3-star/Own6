"""Pure-stdlib unit and data-integrity tests for src/nfl_origination and data/nfl_origination."""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from nfl_origination import (  # noqa: E402
    NFL_VALIDATION_GATES,
    DepthSlot,
    NFLGameInput,
    NFLRegimeParams,
    StrategyEvidence,
    american_to_decimal,
    american_to_implied_prob,
    bivariate_normal_joint_prob,
    bonferroni_holm_adjust,
    brier_score,
    correlation_pricing_report,
    devig_multiplicative,
    devig_power,
    evaluate_strategy_gates,
    evaluate_unit_deficiency,
    gaussian_copula_joint_prob,
    log_loss_score,
    originate_nfl_game,
    paired_pearson,
    paired_spearman,
    prob_to_fair_american,
    push_aware_ev,
    rank_nfl_leaderboard,
    same_line_clv,
    validate_nfl_gameday_roster,
    week_block_bootstrap_corr_ci,
    week_block_bootstrap_mean_ci,
)

DATA_DIR = ROOT / "data" / "nfl_origination"


def _assert_raises(exc_type: type[BaseException], fn, *args, **kwargs) -> None:
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__} from {fn.__name__}")


def test_pricing_odds_devig_push_and_clv() -> None:
    assert abs(american_to_decimal(-110) - (21.0 / 11.0)) < 1e-12
    assert abs(american_to_decimal(150) - 2.5) < 1e-12
    assert abs(american_to_implied_prob(-110) - (11.0 / 21.0)) < 1e-12
    assert abs(american_to_implied_prob(110) - (10.0 / 21.0)) < 1e-12
    assert prob_to_fair_american(0.60) == -150
    assert prob_to_fair_american(0.40) == 150

    for bad in (0, 50, -99, True, False, float("nan"), float("inf")):
        _assert_raises(ValueError, american_to_decimal, bad)
        _assert_raises(ValueError, american_to_implied_prob, bad)

    raw_sym = [american_to_implied_prob(-110), american_to_implied_prob(-110)]
    p_mult = devig_multiplicative(raw_sym)
    p_pow = devig_power(raw_sym)
    assert abs(p_mult[0] - 0.5) < 1e-12 and abs(p_mult[1] - 0.5) < 1e-12
    assert abs(p_pow[0] - 0.5) < 1e-9 and abs(p_pow[1] - 0.5) < 1e-9

    raw_asym = [american_to_implied_prob(-160), american_to_implied_prob(135)]
    asym_pow = devig_power(raw_asym)
    assert abs((asym_pow[0] + asym_pow[1]) - 1.0) < 1e-9
    assert asym_pow[0] > 0.55

    # Push returns stake (0 net profit): 10% push, 50% win, 40% loss at +100 -> +0.10 EV
    ev = push_aware_ev(0.50, 0.40, 0.10, 100)
    assert abs(ev - 0.10) < 1e-12
    _assert_raises(ValueError, push_aware_ev, 0.60, 0.40, 0.10, 100)

    # Same-line CLV must reject moved spreads and compute exact de-vigged lift on identical numbers
    assert same_line_clv(0.50, 0.535, entry_line=-2.5, close_line=-3.5) is None
    clv = same_line_clv(0.50, 0.535, entry_line=-3.0, close_line=-3.0)
    assert clv is not None and abs(clv - 0.035) < 1e-12


def test_nfl_discrete_margin_pmf_and_fail_closed_origination() -> None:
    uncal_game = NFLGameInput(
        game_id="W10-G02",
        away_team="NE",
        home_team="DET",
        neutral_site=True,
    )
    uncal_out = originate_nfl_game(uncal_game, regime=None)
    assert uncal_out["status"] == "unverified_missing_inputs"
    assert uncal_out["fair_spread_home"] is None
    assert uncal_out["fair_total"] is None

    regime = NFLRegimeParams(
        league_mean_pts_per_drive=2.05,
        mean_drives_per_team=11.0,
        hfa_points=2.0,
        margin_sd=13.5,
        total_sd=10.2,
        reg_ot_tie_prob_when_close=0.008,
        dynamic_kickoff_35yd_active=True,
        both_teams_possess_ot_active=True,
        key_number_pmf_weights={3: 1.90, 7: 1.55, 6: 1.25, 10: 1.30, 14: 1.25},
    )

    # Munich neutral-site game forces HFA=0 even when regime.hfa_points == 2.0
    munich_eq = NFLGameInput(
        game_id="W10-G02-SYNTH",
        away_team="NE",
        home_team="DET",
        neutral_site=True,
        away_off_pts_per_drive=2.05,
        away_def_pts_per_drive=2.05,
        home_off_pts_per_drive=2.05,
        home_def_pts_per_drive=2.05,
    )
    res_eq = originate_nfl_game(munich_eq, regime=regime)
    assert res_eq["status"] == "computed_from_supplied_inputs"
    assert abs(float(res_eq["fair_spread_home"])) < 1e-9
    assert float(res_eq["tie_prob"]) > 0.002
    assert abs(
        float(res_eq["home_win_prob"]) + float(res_eq["away_win_prob"]) + float(res_eq["tie_prob"]) - 1.0
    ) < 1e-9

    # Key number 3 push mass and half-point equity check (-2.5 vs -3.0 vs -3.5)
    fav_game = NFLGameInput(
        game_id="SYNTH-FAV",
        away_team="VIS",
        home_team="HOM",
        neutral_site=False,
        away_off_pts_per_drive=1.95,
        away_def_pts_per_drive=2.10,
        home_off_pts_per_drive=2.15,
        home_def_pts_per_drive=1.95,
    )
    r25 = originate_nfl_game(fav_game, regime=regime, target_spread_home=-2.5)["spread_cover_probs"]
    r30 = originate_nfl_game(fav_game, regime=regime, target_spread_home=-3.0)["spread_cover_probs"]
    r35 = originate_nfl_game(fav_game, regime=regime, target_spread_home=-3.5)["spread_cover_probs"]
    assert r25["p_push"] == 0.0
    assert r30["p_push"] > 0.04
    ev25 = push_aware_ev(r25["p_cover"], r25["p_loss"], r25["p_push"], -110)
    ev35 = push_aware_ev(r35["p_cover"], r35["p_loss"], r35["p_push"], -110)
    assert (ev25 - ev35) > 0.07


def test_roster_48_ol_elevations_qb3_and_depth_cascades() -> None:
    ok = validate_nfl_gameday_roster(
        roster_53_count=53,
        ps_standard_elevations=2,
        gameday_active_count=48,
        active_offensive_linemen=8,
        active_bona_fide_qbs=2,
        has_emergency_third_qb=True,
        emergency_qb_is_ps_elevation=False,
        player_season_ps_elevations=(1, 3),
        regular_season_ir_returns_used=5,
    )
    assert ok.valid is True
    assert ok.max_gameday_active_allowed == 48
    assert ok.total_contract_pool == 55

    bad_ol = validate_nfl_gameday_roster(
        roster_53_count=53,
        ps_standard_elevations=1,
        gameday_active_count=48,
        active_offensive_linemen=7,
        active_bona_fide_qbs=2,
        has_emergency_third_qb=False,
    )
    assert bad_ol.valid is False
    assert bad_ol.max_gameday_active_allowed == 47

    bad_qb3_and_ps = validate_nfl_gameday_roster(
        roster_53_count=53,
        ps_standard_elevations=2,
        gameday_active_count=47,
        active_offensive_linemen=7,
        active_bona_fide_qbs=2,
        has_emergency_third_qb=True,
        emergency_qb_is_ps_elevation=True,
        player_season_ps_elevations=(4,),
        regular_season_ir_returns_used=9,
    )
    assert bad_qb3_and_ps.valid is False
    assert len(bad_qb3_and_ps.violations) == 3

    # Patriots Week 10 RB cascade: RB1 Stevenson DNP + RB2 Henderson Out -> RB3 Corey Kiner
    ne_rb = evaluate_unit_deficiency(
        team="NE",
        side="OFFENSE",
        unit_group="RUNNING_BACK",
        slots=[
            DepthSlot("Rhamondre Stevenson", "RB", "RUNNING_BACK", "OFFENSE", 1, "DNP", "QUESTIONABLE"),
            DepthSlot("TreVeyon Henderson", "RB", "RUNNING_BACK", "OFFENSE", 2, "DNP", "OUT"),
            DepthSlot("Corey Kiner", "RB", "RUNNING_BACK", "OFFENSE", 3, "FULL", "ACTIVE_EXPECTED"),
            DepthSlot("Lan Larison", "RB", "RUNNING_BACK", "OFFENSE", 4, "FULL", "ACTIVE_EXPECTED"),
        ],
    )
    assert ne_rb.projected_active_Top_string == 3
    assert ne_rb.projected_replacement_player == "Corey Kiner"
    assert ne_rb.cascading_cluster_alert is True
    assert ne_rb.deficiency_tier == "SEVERE_3RD_STRING_ELEVATION"
    assert ne_rb.estimated_epa_per_play_delta is None


def test_correlations_zero_preservation_copula_and_block_bootstrap() -> None:
    # Exact zero residuals must be preserved (fixing legacy truthiness bug A-F04)
    xs = [-2.0, 0.0, 0.0, 2.0, 4.0, -4.0]
    ys = [-1.0, 0.0, 0.0, 1.0, 2.0, -2.0]
    assert abs(paired_pearson(xs, ys) - 1.0) < 1e-12
    assert abs(paired_spearman(xs, ys) - 1.0) < 1e-12

    _assert_raises(ValueError, paired_pearson, [1.0, 1.0, 1.0], [1.0, 2.0, 3.0])
    _assert_raises(ValueError, paired_pearson, [True, 0.0, 1.0], [1.0, 2.0, 3.0])

    weeks = ["W1", "W1", "W2", "W2", "W3", "W3", "W4", "W4"]
    a = [1.2, 0.8, -1.0, -0.5, 2.1, 1.4, -1.8, -0.9]
    b = [1.0, 0.6, -0.9, -0.4, 1.9, 1.1, -1.5, -0.7]
    ci = week_block_bootstrap_corr_ci(weeks, a, b, n_resamples=400, seed=7)
    assert ci["n_week_clusters"] == 4
    assert float(ci["ci_low"]) > 0.5

    # Sheppard's identity at p1=p2=0.5: P(Z1<=0, Z2<=0) = 1/4 + arcsin(rho)/(2*pi)
    p0 = bivariate_normal_joint_prob(0.5, 0.5, 0.0)
    p_pos = bivariate_normal_joint_prob(0.5, 0.5, 0.5)
    p_neg = bivariate_normal_joint_prob(0.5, 0.5, -0.5)
    assert abs(p0 - 0.25) < 1e-6
    assert abs(p_pos - (1.0 / 3.0)) < 1e-4
    assert abs(p_neg - (1.0 / 6.0)) < 1e-4

    tri = gaussian_copula_joint_prob(
        [0.5, 0.5, 0.5],
        [[1.0, 0.4, 0.3], [0.4, 1.0, 0.35], [0.3, 0.35, 1.0]],
        sims=15000,
        seed=11,
    )
    assert float(tri["joint_prob"]) > 0.16 and float(tri["correlation_multiplier"]) > 1.25

    _assert_raises(
        ValueError,
        gaussian_copula_joint_prob,
        [0.5, 0.5, 0.5],
        [[1.0, 0.9, 0.9], [0.9, 1.0, -0.9], [0.9, -0.9, 1.0]],
    )

    blocked = correlation_pricing_report([0.52, 0.51], empirical_corr_matrix=None)
    assert blocked["status"] == "blocked_unverified_correlation"
    assert blocked["joint_prob"] is None


def test_validation_gates_luck_controls_and_leaderboard() -> None:
    assert len(NFL_VALIDATION_GATES) == 12
    assert brier_score([0.7, 0.3], [1, 0]) < brier_score([0.5, 0.5], [1, 0])
    assert log_loss_score([0.7, 0.3], [1, 0]) < log_loss_score([0.5, 0.5], [1, 0])

    bonf, holm = bonferroni_holm_adjust([0.004, 0.02, 0.20])
    assert abs(bonf[0] - 0.012) < 1e-12
    assert abs(holm[0] - 0.012) < 1e-12
    assert holm[1] <= bonf[1]

    unqualified_ev = StrategyEvidence(
        strategy_id="NFL-STR-01",
        is_combo_or_parlay=False,
        has_data_license=False,
        n_observations=0,
    )
    rep_unq = evaluate_strategy_gates(unqualified_ev)
    assert rep_unq["qualified"] is False
    assert rep_unq["gates_passed"] < 12

    # Synthetic 12/12 control verifying qualification & leaderboard sorting math
    qualified_ev = StrategyEvidence(
        strategy_id="SYNTH-CONTROL-01",
        is_combo_or_parlay=True,
        has_data_license=True,
        has_pre_kickoff_timestamps=True,
        is_walk_forward_regime_consistent=True,
        n_observations=420,
        n_nfl_weeks=22,
        has_push_exact_settlement=True,
        model_brier=0.231,
        market_brier=0.242,
        model_log_loss=0.654,
        market_log_loss=0.676,
        clv_mean=0.024,
        clv_week_cluster_t=3.15,
        roi_mean=0.048,
        roi_week_cluster_ci_low=0.016,
        raw_p_value=0.0018,
        family_size_m=10,
        has_depth_reconciliation=True,
        has_verified_copula_correlations=True,
        has_sha256_ledger_audit=True,
    )
    rep_qual = evaluate_strategy_gates(qualified_ev)
    assert rep_qual["qualified"] is True
    assert rep_qual["gates_passed"] == 12

    board = rank_nfl_leaderboard(
        [
            ("SINGLE", unqualified_ev),
            ("SGP_COMBO", qualified_ev),
        ]
    )
    assert board[0].strategy_id == "SYNTH-CONTROL-01"
    assert board[0].rank == 1
    assert board[0].reward_tier == "TIER_1_GOLD_COMPUTE_AND_PAPER_ALLOCATION"
    assert board[1].strategy_id == "NFL-STR-01"
    assert board[1].rank is None
    assert board[1].reward_tier == "NONE_UNQUALIFIED"

    weeks = [f"W{(i % 8) + 1}" for i in range(64)]
    vals = [0.08 + 0.01 * (i % 3) for i in range(64)]
    wb = week_block_bootstrap_mean_ci(weeks, vals, n_resamples=500, seed=42)
    assert float(wb["ci_low"]) > 0.05


def test_nfl_origination_csv_datasets_and_blank_integrity() -> None:
    expected_csvs = {
        "sources.csv",
        "requirements_matrix.csv",
        "verified_standings_2026_w10.csv",
        "week10_slate_and_lines.csv",
        "nfl_official_rules_and_roster.csv",
        "decision_qa_and_missing_info.csv",
        "site_suggestions.csv",
        "strategies_leaderboard.csv",
        "validation_gates.csv",
        "correlations_and_combos.csv",
        "injury_and_depth_deficiency.csv",
        "repo_audit_findings.csv",
        "flagged_for_review.csv",
    }
    found = {p.name for p in DATA_DIR.glob("*.csv")}
    assert expected_csvs.issubset(found)

    for name in sorted(expected_csvs):
        with (DATA_DIR / name).open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames is not None
            assert len(reader.fieldnames) == len(set(reader.fieldnames))
            rows = list(reader)
            assert len(rows) >= 10, name
            for r in rows:
                assert None not in r and all(v is not None for v in r.values()), f"{name}: malformed row"
                assert r["official_source_url"].startswith("https://"), f"{name}: non-https source"

    # 32-team 2026 NFL Week 10 standings exact league accounting identity
    with (DATA_DIR / "verified_standings_2026_w10.csv").open(newline="", encoding="utf-8") as fh:
        st = list(csv.DictReader(fh))
    assert len(st) == 32
    assert sum(int(r["w"]) for r in st) == sum(int(r["l"]) for r in st) == 135
    assert sum(int(r["t"]) for r in st) == 2
    assert sum(int(r["pf"]) for r in st) == sum(int(r["pa"]) for r in st) == 6246
    for r in st:
        assert int(r["pf"]) - int(r["pa"]) == int(r["net_pts"])

    # Unverified lines, empirical correlations, and EPA drop-offs MUST remain blank ("")
    with (DATA_DIR / "week10_slate_and_lines.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for col in (
                "market_spread_home",
                "market_total",
                "originated_fair_spread_home",
                "originated_fair_total",
                "originated_home_win_prob",
            ):
                assert r[col] == "", f"Hallucinated Week 10 line in {r['slot_id']}.{col}"

    with (DATA_DIR / "correlations_and_combos.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for col in ("empirical_pearson_r", "empirical_spearman_rho", "week_cluster_ci_95", "empirical_n_pairs"):
                assert r[col] == "", f"Unverified correlation filled in {r['corr_id']}.{col}"

    with (DATA_DIR / "injury_and_depth_deficiency.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            assert r["empirical_epa_dropoff"] == ""
            assert r["verified_week10_snap_share"] == ""

    with (DATA_DIR / "strategies_leaderboard.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            assert r["reward_tier"] == "NONE_UNQUALIFIED"
            for col in ("holdout_roi", "same_line_clv", "brier_score", "skill_score", "leaderboard_rank"):
                assert r[col] == ""
