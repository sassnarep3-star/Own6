"""Pure-stdlib unit and data-integrity tests for src/nfl_desk and data/nfl_desk.

Two kinds of test live here. The first pins the arithmetic the published
registers depend on: pricing conventions, the margin distribution, the
correlation estimators, the depth screen, the gate state machine. The second
re-asserts the data invariants on the real registers, including the convention
this pack once got wrong - winning percentage counting a tie as half a game, as
the standings page prints it - so that an error of the same shape fails a test
instead of shipping as a table.

Runnable three ways: ``python3 tools/run_tests.py``, ``python3 -m unittest
tests.test_nfl_desk`` and ``python3 tests/test_nfl_desk.py``.
"""
from __future__ import annotations

import csv
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data" / "nfl_desk"
DERIVED = DATA / "derived"

from nfl_desk import audit, correlation, depth, derive, gates, league, luck, model, pricing  # noqa: E402
from nfl_desk.league import Club, league_facts, load_clubs, round_half  # noqa: E402


def _csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _interval(text: str) -> list[float]:
    return [float(x.strip()) for x in text.strip().strip("[]").split(",")]


def _synthetic_injury_rows() -> list[dict]:
    return [
        {"club": "Test Club", "player": "Alfa One", "position": "QB", "game_status": "Out",
         "practice_status_abbrev": "DNP", "practice_status_verbatim": "DNP - Did Not Practise"},
        {"club": "Test Club", "player": "Bravo Two", "position": "QB", "game_status": "",
         "practice_status_abbrev": "Full", "practice_status_verbatim": "Full - Participated Fully"},
        {"club": "Test Club", "player": "Charlie Three", "position": "CB", "game_status": "",
         "practice_status_abbrev": "DNP", "practice_status_verbatim": "DNP - Did Not Practise"},
        {"club": "Test Club", "player": "Delta Four", "position": "S", "game_status": "",
         "practice_status_abbrev": "Limited", "practice_status_verbatim": "Limited - Participated Limitedly"},
        {"club": "Other Club", "player": "Echo Five", "position": "P", "game_status": "",
         "practice_status_abbrev": "", "practice_status_verbatim": ""},
    ]


# ---------------------------------------------------------------- pricing conventions


def test_american_to_decimal_matches_the_public_convention() -> None:
    assert abs(pricing.american_to_decimal(-110) - 1.9090909090909092) < 1e-12
    assert abs(pricing.american_to_decimal(100) - 2.0) < 1e-12
    assert abs(pricing.american_to_decimal(150) - 2.5) < 1e-12
    assert abs(pricing.american_to_decimal(-200) - 1.5) < 1e-12
    # a -110 favourite pays 10/11 profit per unit staked; a +150 dog pays 3/2
    assert abs((pricing.american_to_decimal(-110) - 1) - 10 / 11) < 1e-12
    assert abs((pricing.american_to_decimal(150) - 1) - 1.5) < 1e-12


def test_breakeven_implied_probability_and_devig_agree() -> None:
    assert abs(pricing.breakeven_win_prob(-110) - 11 / 21) < 1e-12
    assert abs(pricing.implied_prob_american(-110) - 11 / 21) < 1e-12
    assert abs(pricing.implied_prob_american(150) - 1 / 2.5) < 1e-12
    for price in (-105, -110, -115, -130, -200, 120, 150, 200, 500):
        p = pricing.implied_prob_american(price)
        assert 0.0 < p < 1.0, price
        assert abs(p - 1 / pricing.american_to_decimal(price)) < 1e-12, price
        assert abs(pricing.breakeven_win_prob(price) - p) < 1e-12, price
    both = pricing.devig_multiplicative([-110, -110])
    assert abs(sum(both) - 1.0) < 1e-12 and abs(both[0] - 0.5) < 1e-12
    lopsided = pricing.devig_multiplicative([-150, +130])
    assert abs(sum(lopsided) - 1.0) < 1e-12 and lopsided[0] > 0.5 > lopsided[1]
    unbalanced = pricing.devig_multiplicative([-200, -180])
    assert abs(sum(unbalanced) - 1.0) < 1e-12, "an overround must be removed, not ignored"


def test_scoring_rules_measure_probability_not_profit() -> None:
    assert pricing.brier([1.0, 0.0], [1, 0]) == 0.0
    assert abs(pricing.brier([0.0, 1.0], [1, 0]) - 1.0) < 1e-12
    assert abs(pricing.brier([0.5, 0.5], [1, 0]) - 0.25) < 1e-12
    assert pricing.log_loss([1.0], [1]) < 1e-6
    assert 0.69 < pricing.log_loss([0.5], [1]) < 0.70
    clv = pricing.same_line_clv(0.55, [0.50, 0.52])
    assert set(clv) >= {"n", "mean_clv", "t", "passes_gate"}
    assert clv["n"] == 2 and abs(clv["mean_clv"] - 0.04) < 1e-12
    assert pricing.same_line_clv(0.50, [0.50, 0.50])["mean_clv"] == 0.0


# ---------------------------------------------------------------- the line model


def test_margin_distribution_is_a_proper_distribution() -> None:
    mpmf = model.margin_pmf(21.0, 18.0)
    assert abs(sum(mpmf.values()) - 1.0) < 1e-9
    assert all(p >= 0.0 for p in mpmf.values())
    assert mpmf[0] > 0.04, "a regulation tie must carry mass; that is why it is priced"


def test_game_line_signs_totals_and_rounding() -> None:
    line, kn = model.game_line(27.0, 20.0, 18.0, 26.0)
    assert line.spread_home < 0.0, "the better club at home must be published as the favourite"
    assert line.home_win_prob > 0.5
    # total = (27+26)/2 + (18+20)/2 = 45.5 exactly
    assert abs(line.total - 45.5) < 1e-9
    assert abs(line.total_rounded - round_half(line.total, 0.5)) < 1e-12
    assert abs(line.spread_rounded - round_half(line.spread_home, 0.5)) < 1e-12
    shifted, _ = model.game_line(27.0, 20.0, 18.0, 26.0, home_field_points=2.5)
    assert abs(shifted.total - line.total) < 1e-9, "the total must not move with the home assumption"
    # a bigger home assumption makes the home club the favourite, and the published home spread is negative
    # for a home favourite, so the spread moves by exactly minus the assumption
    assert abs((shifted.spread_home - line.spread_home) + 2.5) < 1e-9
    assert shifted.home_win_prob > line.home_win_prob
    assert 0.0 < kn.get(3, 0.0) < 0.2 and 0.0 < kn.get(7, 0.0) < 0.2
    window = sum(kn.get(k, 0.0) for k in range(1, 9))
    assert 0.5 < window <= 1.0, "a one-score game is the common case, and the register publishes this mass"
    assert abs(sum(kn[k] for k in range(1, 9)) - window) < 1e-12


def test_push_probability_follows_the_quoted_line() -> None:
    """A half-point line cannot push; a whole-number line pushes on one exact margin."""
    half, _ = model.game_line(24.5, 21.0, 21.0, 24.0, tick=0.5)   # fair -3.25 quotes as -3.5
    whole, _ = model.game_line(24.5, 21.0, 21.0, 24.0, tick=1.0)  # and as -3.0 on a whole-number board
    assert half.spread_rounded == -3.5 and half.push_prob_quoted_line == 0.0, "a .5 line cannot push"
    assert whole.spread_rounded == -3.0 and whole.push_prob_quoted_line > 0.04
    assert whole.push_prob_quoted_line > 0.04
    assert whole.tie_prob > 0.04, "regulation-tie mass is reported separately from push mass"
    # for a pick, push mass and tie mass are the same number
    pick, _ = model.game_line(21.0, 21.0, 21.0, 21.0, tick=1.0)
    assert abs(pick.push_prob_quoted_line - pick.tie_prob) < 1e-12


def test_swapping_home_and_away_flips_the_spread_and_preserves_the_total() -> None:
    """game_line() is positional home-first; a reversed call silently flips every sign."""
    forward, _ = model.game_line(27.0, 20.0, 18.0, 26.0)
    reverse, _ = model.game_line(18.0, 26.0, 27.0, 20.0)
    assert forward.spread_home < 0.0 < reverse.spread_home
    assert abs(forward.total - reverse.total) < 1e-9
    assert abs((forward.home_win_prob - 0.5) + (reverse.home_win_prob - 0.5)) < 1e-9


def test_round_half_states_its_tie_convention() -> None:
    """Exactly-half cases go up (toward +infinity), which is a stated choice, not an accident.

    A fair spread of -0.25 therefore quotes as a pick rather than -0.5. The register publishes the
    unrounded fair spread beside the quoted line, so the rounding is visible and reversible.
    """
    assert round_half(0.25, 0.5) == 0.5
    assert round_half(-0.25, 0.5) == 0.0
    assert round_half(1.75, 0.5) == 2.0
    assert round_half(-1.75, 0.5) == -1.5
    assert round_half(2.0, 0.5) == 2.0
    for value in (-9.4, -3.25, 0.0, 2.6, 7.1):
        quoted = round_half(value, 0.5)
        assert abs(quoted * 2 - round(quoted * 2)) < 1e-9, "every published line is on the half-point board"
        assert abs(quoted - value) <= 0.25 + 1e-12


# ---------------------------------------------------------------- league registers


def test_league_registers_balance_and_use_the_printed_pct_convention() -> None:
    for fname in ("standings_2026_thru_w10.csv", "standings_2025_final.csv"):
        rows = _csv(DATA / fname)
        assert len(rows) == 32, fname
        for r in rows:
            gp, w, l, t = (int(r[k]) for k in ("games_played", "wins", "losses", "ties"))
            assert w + l + t == gp, (fname, r["club"])
            assert int(r["home_w"]) + int(r["home_l"]) + int(r["home_t"]) \
                + int(r["road_w"]) + int(r["road_l"]) + int(r["road_t"]) == gp, (fname, r["club"])
            assert int(r["div_w"]) <= w and int(r["div_l"]) <= l and int(r["conf_w"]) >= int(r["div_w"]), fname
            assert abs(float(r["win_pct"]) - round((w + 0.5 * t) / gp, 3)) < 6e-4, (fname, r["club"])
            assert abs(float(r["net_points"]) - (int(r["points_for"]) - int(r["points_against"]))) < 1e-9
            assert r["source_url"].startswith("https://www.nfl.com/")
        assert sum(int(r["wins"]) for r in rows) == sum(int(r["losses"]) for r in rows), fname
        assert sum(int(r["points_for"]) for r in rows) == sum(int(r["points_against"]) for r in rows), fname


def test_values_that_come_from_the_2026_11_13_read() -> None:
    c26 = {x.abbr: x for x in load_clubs("standings_2026_thru_w10.csv")}
    assert (c26["BUF"].w, c26["BUF"].l, c26["BUF"].pf) == (7, 1, 256)
    assert (c26["NYG"].w, c26["NYG"].l, c26["NYG"].t, c26["NYG"].pf, c26["NYG"].pa) == (5, 3, 1, 203, 196)
    assert (c26["WAS"].w, c26["WAS"].l, c26["WAS"].t) == (3, 5, 1)
    facts = league_facts(list(c26.values()))
    assert facts["games"] == 137.0 and facts["points_for"] == 6291.0
    assert abs(facts["league_avg_points_per_team_game"] - 22.9599) < 5e-4
    assert abs(facts["home_win_share"] - 0.4891) < 5e-4
    c25 = {x.abbr: x for x in load_clubs("standings_2025_final.csv")}
    assert (c25["GB"].w, c25["GB"].l, c25["GB"].t, c25["GB"].home_w) == (9, 7, 1, 5)
    assert (c25["GB"].home_t, c25["GB"].road_t) == (0, 1)
    assert league_facts(list(c25.values()))["games"] == 272.0
    printed = [float(r["win_pct"]) for r in _csv(DATA / "standings_2026_thru_w10.csv") if r["ties"] != "0"]
    assert len(printed) == 2 and abs(sum(printed) - (0.611 + 0.389)) < 1e-9, (
        "the two tied clubs must carry the PCT the standings page prints, not wins / (wins + losses)")


def test_unbalanced_register_is_refused_not_published() -> None:
    """A one-point edit must be caught by league_facts, never reach a page.

    The register builder writes to a temp file inside data/nfl_desk so the loader's real path is exercised,
    and the register's own asserts live in league_facts: they raise on an unbalanced league.
    """
    path = DATA / "_test_unbalanced_standings.csv"
    rows = _csv(DATA / "standings_2026_thru_w10.csv")
    hdr = list(rows[0])
    rows[0]["points_for"] = str(int(rows[0]["points_for"]) + 1)
    try:
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=hdr, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        clubs = load_clubs(path.name)
        assert clubs and isinstance(clubs[0], Club)
        try:
            league_facts(clubs)
        except ValueError as exc:
            assert "balance" in str(exc) or "account for every game" in str(exc)
        else:
            raise AssertionError("an unbalanced league register must be refused by league_facts")
    finally:
        if path.exists():
            path.unlink()
    # re-reading the real file must be clean again
    assert league_facts(load_clubs("standings_2026_thru_w10.csv"))["points_for"] == 6291.0
    assert not path.exists(), "the temp register was not cleaned up"


def test_league_facts_rejects_a_league_that_does_not_balance() -> None:
    clubs = load_clubs("standings_2026_thru_w10.csv")
    broken = [Club(**{**c.__dict__, "pf": c.pf + (1 if i == 0 else 0)}) for i, c in enumerate(clubs)]
    try:
        league_facts(broken)
    except ValueError as exc:
        assert "balance" in str(exc)
    else:
        raise AssertionError("league_facts accepted a league whose points do not balance")


# ---------------------------------------------------------------- correlation


def test_correlation_estimators_on_known_data() -> None:
    xs = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert abs(correlation.pearson(xs, xs) - 1.0) < 1e-12
    assert abs(correlation.pearson(xs, [-x for x in xs]) + 1.0) < 1e-12
    assert abs(correlation.spearman(xs, [10.0, 20.0, 30.0, 40.0, 500.0]) - 1.0) < 1e-12
    # a constant series has no defined correlation: the estimator says so instead of inventing 0.0,
    # and the builder refuses to publish a nan, so the two together keep it out of the registers
    assert math.isnan(correlation.pearson(xs, [1.0, 1.0, 1.0, 1.0, 1.0]))
    try:
        correlation.pearson([1.0, 2.0], [1.0, 2.0])
    except ValueError as exc:
        assert "at least 3" in str(exc)
    else:
        raise AssertionError("a two-point series must be refused, not fitted")
    assert correlation.ranks([10.0, 20.0, 20.0, 30.0]) == [1.0, 2.5, 2.5, 4.0], "ties share ranks"


def test_correlation_register_shape_and_blank_discipline() -> None:
    rows = derive.correlation_register()
    assert len(rows) == 9
    measured = [r for r in rows if r["status"] == "measured"]
    assert len(measured) == 6
    for r in measured:
        assert int(r["n"]) == 32, r["corr_id"]
        lo, hi = _interval(r["boot_ci_95"])
        assert lo <= float(r["pearson_r"]) <= hi, (r["corr_id"], r["boot_ci_95"])
        assert 0.0 <= float(r["perm_p"]) <= 1.0
        assert abs(float(r["r_squared"]) - float(r["pearson_r"]) ** 2) < 5e-4
        assert abs(float(r["spearman_rho"])) <= 1.0
    for r in rows:
        if r["status"].startswith("blank"):
            for k in ("pearson_r", "spearman_rho", "boot_ci_95", "perm_p", "r_squared"):
                assert r[k].strip() == "", (r["corr_id"], k)
            assert r["flag_id"], "a blank correlation must point at the flag that explains it"
        assert r["source_url"].startswith("https://")
    # the two headline results are quoted in the summary, so pin them
    by_id = {r["corr_id"]: r for r in rows}
    assert by_id["CR-06"]["pearson_r"] == "-0.0077", "luck persistence is the measured null the desk relies on"
    assert by_id["CR-03"]["pearson_r"] == "0.4973"
    assert float(by_id["CR-01"]["boot_ci_95"].strip("[]").split(",")[0]) < 0.0 < \
        float(by_id["CR-01"]["boot_ci_95"].strip("[]").split(",")[1]), "CR-01's interval must span zero"


def test_frechet_bounds_are_ordered_and_contain_the_independence_price() -> None:
    for p1, p2 in ((0.5, 0.5), (0.2, 0.9), (0.75, 0.75), (0.05, 0.05), (1.0, 0.4)):
        lo, hi = max(0.0, p1 + p2 - 1.0), min(p1, p2)
        assert lo <= hi <= 1.0 and lo <= p1 * p2 <= hi, (p1, p2)
    rows = derive.frechet_table()
    assert len(rows) == 4
    for r in rows:
        lo, hi = float(r["frechet_lower_bound"]), float(r["frechet_upper_bound"])
        assert lo <= float(r["independent_product"]) <= hi, r["combo_id"]
        assert r["flag_id"] == "FL-08"


# ---------------------------------------------------------------- luck


def test_pythagorean_expectation_is_monotone_and_bounded() -> None:
    assert luck.pyth_win_prob(30.0, 20.0, 3.37) > 0.5
    assert luck.pyth_win_prob(20.0, 30.0, 3.37) < 0.5
    assert abs(luck.pyth_win_prob(25.0, 25.0, 3.37) - 0.5) < 1e-9
    for pf, pa in ((40.0, 10.0), (10.0, 40.0), (21.0, 21.0), (35.0, 34.0)):
        assert 0.0 <= luck.pyth_win_prob(pf, pa, 3.37) <= 1.0
    assert luck.pyth_win_prob(28.0, 22.0, 3.9) > luck.pyth_win_prob(28.0, 22.0, 2.5)


def test_luck_is_measured_against_the_noise_floor() -> None:
    clubs = load_clubs("standings_2026_thru_w10.csv")
    fit = luck.pythagorean_fit(clubs)
    assert 1.5 <= fit["exponent"] <= 4.5 and 0.0 <= fit["r_squared"] <= 1.0
    assert fit["n"] == 32
    table = luck.luck_table(clubs, fit["exponent"])
    assert len(table) == 32
    for row in table:
        assert 0.0 <= row["expected_wins"] <= row["gp"]
        assert abs(row["luck_wins"] - (row["wins_adj"] - row["expected_wins"])) < 1e-6
    share = luck.luck_share(clubs, fit["exponent"])
    assert share["sd_residual_wins"] > 0.0
    assert share["sd_noise_wins"] > share["sd_residual_wins"], (
        "the published result is that residual scatter is *smaller* than chance; if this flips, the "
        "no-residual-skill conclusion has to be rewritten, not the test")
    assert share["excess_over_noise"] < 0.0


def test_required_sample_arithmetic_scales_the_right_way() -> None:
    thin = luck.required_games_for_edge(1.0, 12.0)
    fat = luck.required_games_for_edge(3.0, 12.0)
    noisier = luck.required_games_for_edge(1.0, 14.0)
    assert fat < thin, (fat, thin)
    assert noisier > thin, (noisier, thin)
    assert thin > 1.0
    power = [r for r in derive.sensitivity_register() if r["game_id"] == "power"]
    assert len(power) == 12, "4 edges x 3 sigma is the frozen grid"
    assert any(r["note"].endswith("125") for r in power), "the 1-point / sigma=10 cell is quoted in the summary"


# ---------------------------------------------------------------- depth screen


def test_depth_screen_orders_groups_by_impairment() -> None:
    out = {g["club"] + "|" + g["unit_group"]: g for g in depth.club_group_deficiency(_synthetic_injury_rows())}
    qb = out["Test Club|OFFENCE_QB"]
    sec = out["Test Club|DEFENCE_SECONDARY"]
    st = out["Other Club|SPECIAL_TEAMS"]
    assert qb["deficiency_score"] == 3 and qb["impaired_count"] == 1
    assert qb["cascading_cluster"] == "no", "one impaired player is not a cluster"
    assert sec["deficiency_score"] == 3, "DNP (2) + Limited (1)"
    assert sec["impaired_count"] == 1 and sec["cascading_cluster"] == "no"
    assert st["deficiency_score"] == 0 and st["replacement_tier"] == "no impairment listed"
    assert qb["starter_dependent_unit"] == "yes" and st["starter_dependent_unit"] == "no"
    assert qb["affected_players"].startswith("Alfa One (QB, Out)"), "the strongest claim is listed first"
    assert depth.weight_of({"game_status": "Out", "practice_status_abbrev": "DNP"}) == 3
    assert depth.weight_of({"game_status": "", "practice_status_abbrev": "DNP"}) == 2
    assert depth.weight_of({"game_status": "", "practice_status_abbrev": "Limited"}) == 1
    assert depth.weight_of({"game_status": "", "practice_status_abbrev": "Full"}) == 0
    assert depth.tier_label(0) == "no impairment listed"
    try:
        depth.club_group_deficiency([{"club": "X", "player": "Y", "position": "XX", "game_status": "",
                                      "practice_status_abbrev": ""}])
    except ValueError as exc:
        assert "unmapped position" in str(exc)
    else:
        raise AssertionError("an unmapped position must fail loudly, not join a catch-all group")


def test_cluster_alert_fires_when_two_in_a_group_are_impaired() -> None:
    rows = _synthetic_injury_rows()
    rows.append({"club": "Test Club", "player": "Foxtrot Six", "position": "CB", "game_status": "",
                 "practice_status_abbrev": "DNP", "practice_status_verbatim": "DNP - Did Not Practise"})
    sec = {g["unit_group"]: g for g in depth.club_group_deficiency(rows)}["DEFENCE_SECONDARY"]
    assert sec["impaired_count"] == 2 and sec["cascading_cluster"] == "yes"
    assert sec["deficiency_score"] == 5


def test_depth_register_reconciles_with_the_published_injury_rows() -> None:
    register = _csv(DATA / "injury_report_2026_w10.csv")
    by_name = {r["player"]: r for r in register}
    raw = [l.split("|") for l in (DATA / "raw" / "injury_report_week10_read.psv")
           .read_text(encoding="utf-8").splitlines()[1:]]
    page_by_club: dict[str, set[str]] = {}
    for club, player, *_rest in raw:
        page_by_club.setdefault(club, set()).add(player.strip())
    rows = derive.depth_register()
    assert len(rows) == 77
    assert sum(int(r["impaired_count"]) for r in rows) > 0
    for row in rows:
        assert row["depth_id"].startswith("DP-")
        assert row["unit_group_label"] == row["unit_group"].replace("_", " ").title()
        assert row["weighting_policy"] == "Out=3, DNP=2, Limited=1, Full=0"
        assert row["flag_id"] == "FL-03" and row["read_date"] == "2026-11-13"
        impaired, score = int(row["impaired_count"]), int(row["deficiency_score"])
        assert score >= impaired and (row["cascading_cluster"] == "yes") == (impaired >= 2)
        assert (int(row["deficiency_score"]) == 0) == (row["replacement_tier"] == "no impairment listed")
        assert int(row["players_listed"]) >= int(row["impaired_count"]) >= int(row["out_count"]) >= 0
        # a group record lists every player the page put in that group, including Full and Limited rows the
        # published register deliberately filters out, so names are checked against the raw read
        assert row["players_listed"] <= len(page_by_club[row["club"]])
        for entry in row["affected_players"].split("; "):
            name = entry.split(" (")[0]
            assert name in page_by_club[row["club"]], f"{row['club']}: {name} is not on that club's page"
            if name in by_name:
                assert by_name[name]["club"] == row["club"], f"{name} filed under the wrong club"


# ---------------------------------------------------------------- gates


def test_gate_states_recompute_from_their_inputs() -> None:
    args = dict(club_count=32, game_count=137.0, licensed_feeds=0, snapshots=0, settled_selections=0,
                sign_stable_share=0.8462, persistence_pearson=0.4973)
    base = {g["gate_id"]: g for g in gates.evaluate(**args)}
    assert base["DG-03"]["state"] == "BLOCKED" and base["DG-04"]["state"] == "BLOCKED"
    assert base["DG-05"]["state"] == "FAIL" and base["DG-12"]["state"] == "FAIL"
    assert {g["gate_id"]: g["state"] for g in gates.evaluate(**{**args, "licensed_feeds": 1})}["DG-03"] == "PASS"
    assert {g["gate_id"]: g["state"] for g in gates.evaluate(**{**args, "snapshots": 28})}["DG-04"] == "PASS"
    assert {g["gate_id"]: g["state"] for g in gates.evaluate(**{**args, "settled_selections": 200})}["DG-05"] == "PASS"
    assert {g["gate_id"]: g["state"] for g in gates.evaluate(**{**args, "sign_stable_share": 0.95})}["DG-12"] == "PASS"
    for gate_id, row in base.items():
        assert row["state"] in ("PASS", "FAIL", "BLOCKED"), gate_id
        if row["state"] != "PASS":
            assert len(row["measured"]) > 20, f"{gate_id} must say what was measured"
            assert len(row["unlock"]) > 20, f"{gate_id} must name the artefact that unlocks it"
        assert row["family"] in ("structural", "evidence")


def test_holm_bonferroni_is_monotone_and_capped() -> None:
    ps = [("a", 0.001), ("b", 0.02), ("c", 0.03), ("d", 0.4), ("e", 0.9)]
    out = gates.holm_adjust(ps)
    adj = [r["adjusted_p"] for r in out]
    assert adj == sorted(adj), "adjusted p-values stay ordered"
    assert all(x <= 1.0 for x in adj)
    assert [r["reject_null"] for r in out] == [True, True, False, False, False] or \
        all(out[i]["reject_null"] >= out[i + 1]["reject_null"] for i in range(4))
    assert abs(out[0]["holm_threshold"] - 0.05 / 5) < 1e-12, "the smallest p gets alpha/m"
    assert out[-1]["holm_threshold"] == 0.05, "the largest p is compared against alpha"
    assert out[0]["p"] < out[1]["p"]


# ---------------------------------------------------------------- verification ledger


def test_disposition_vocabulary_is_closed_and_self_consistent() -> None:
    rows = audit.ledger_rows()
    # the audited registers belong to other sessions, so the row count moves under us: pin the invariants that
    # must hold whatever they contain, and a floor that catches a register silently dropping out
    assert len(rows) >= 500, f"the ledger fell to {len(rows)} rows: an audited register is probably no longer read"
    assert len({r[0] for r in rows}) == len(rows), "ledger row ids must be globally unique"
    seen: set[str] = set()
    for row in rows:
        disp, status = row[6], row[10]
        assert disp in audit.DISPOSITION_STATUS, f"unknown disposition {disp}"
        assert status == audit.DISPOSITION_STATUS[disp], f"{row[0]}: {disp} cannot be {status}"
        assert row[7].strip(), f"{row[0]}: every row needs an explanation"
        assert row[1] and row[2] and row[3], f"{row[0]}: register, subject and field are all required"
        seen.add(disp)
    assert {"CONFIRMED", "PROVENANCE_MISMATCH", "DRIFT_STATUS_CHANGED"} <= seen
    assert 0 < sum(1 for r in rows if r[10] == "needs_review"), "a re-verification that finds nothing has stopped comparing"


def test_ledger_reconciles_the_settled_thursday_result_exactly() -> None:
    rows = [dict(zip(audit.LEDGER_HDR, r)) for r in audit.ledger_rows()]
    records = [r for r in rows if r["field"] in ("away_record", "home_record") and r["subject"] == "W10-G01"]
    assert len(records) == 2
    # the settled Thursday result was 24-21, so Washington +1 win / New York +1 loss. Whether that shows up as a
    # reconciliation or as a match depends on whether the peer register has since been updated, so both branches
    # are allowed here - but only those two, and each with its arithmetic stated.
    for r in records:
        prior, now = audit._parse_rec(r["prior_value"]), audit._parse_rec(r["official_value_2026_11_13"])
        expect = (1, 0, 0) if r["field"] == "away_record" else (0, 1, 0)
        diff = tuple(x - y for x, y in zip(now, prior))
        if diff == (0, 0, 0):
            assert r["disposition"] == "CONFIRMED", r
        else:
            assert diff == expect, f"{r['row_id']}: {prior} -> {now} is neither a match nor the settled delta"
            assert r["disposition"] == "SUPERSEDED_RECONCILED", r
    moved = {(club, field): (prior, now) for club, field, prior, now in (
        ("New York Giants", "l", "2", "3"), ("Washington Commanders", "w", "2", "3"),
        ("New York Giants", "w", "5", "5"), ("Washington Commanders", "l", "5", "5"))}
    for r in rows:
        key = (r["subject"], r["field"])
        if key not in moved:
            continue
        prior, now = moved[key]
        if prior == now:
            assert r["disposition"] == "CONFIRMED", r
        else:
            assert r["disposition"] == "SUPERSEDED_RECONCILED", (
                f"{key}: a record cell that moved because of the settled game cannot be reported as confirmed")
    pct = [r for r in rows if r["field"] == "win_pct" and r["subject"] in ("New York Giants", "Washington Commanders")]
    assert pct and all(r["disposition"] == "SUPERSEDED_RECONCILED" for r in pct)


def test_repo_checks_are_computed_not_transcribed() -> None:
    rows = audit.repo_checks()
    assert len(rows) == 9
    by_id = {r["finding_id"]: r for r in rows}
    assert "BASE=" in by_id["RA-09"]["evidence_computed_here"], (
        "the unreachable-base finding is computed from the scripts and the clone, so it must name a ref")
    for r in rows:
        assert r["read_date"] == "2026-11-13"
        assert r["official_source_url"].startswith("https://github.com/")
        assert r["evidence_computed_here"].strip() and r["finding"].strip()
        assert r["severity"] in ("low", "info", "medium", "high")
    crlf = sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.csv") if b"\r\n" in p.read_bytes())
    evidence = {r["finding_id"]: r["evidence_computed_here"] for r in rows}
    assert evidence["RA-01"].startswith(f"{len(crlf)} CSV files contain CRLF"), (
        "the CRLF count in the audit text must equal what the tree shows today")


# ---------------------------------------------------------------- derived registers


def test_originated_lines_are_internally_consistent() -> None:
    lines, summary = derive.originated_lines()
    assert len(lines) == 13
    assert summary["games"] == 13 and summary["sign_stable"] == 11
    assert abs(summary["sign_stability_share"] - 11 / 13) < 1e-9
    for r in lines:
        for k in ("market_open_line", "market_close_line", "market_total", "market_implied_prob",
                  "de_vigged_market_prob", "clv", "brier"):
            assert r[k].strip() == "", f"{r['line_id']}: {k} must stay blank without a licensed feed"
        spread, total = float(r["model_fair_spread_home"]), float(r["model_fair_total"])
        p, push, tie = float(r["model_home_win_prob"]), float(r["model_push_prob"]), float(r["model_tie_mass"])
        assert -14.0 < spread < 14.0 and 28.0 < total < 70.0
        assert 0.0 <= p <= 1.0 and 0.0 <= push <= 0.2 and 0.0 < tie < 0.2
        assert (spread < 0 and p > 0.5) or (spread > 0 and p < 0.5), r["line_id"]
        assert r["line_status"] == "originated_internally_not_validated_against_a_market"
        assert r["flag_id"] == "FL-01" and r["read_date"] == "2026-11-13"
        assert r["input_source"].startswith("https://www.nfl.com/")
        rounded = float(r["model_fair_spread_rounded"])
        assert abs(rounded - round_half(spread, 0.5)) < 1e-9
        if abs(rounded * 2 - round(rounded * 2)) > 1e-9:
            assert push == 0.0, f"{r['line_id']}: a half-point line cannot carry push mass"
        assert 0.0 < float(r["one_score_window_mass"]) <= 1.0
    flips = [r for r in lines if r["assumption_grid_sign_stable"] == "no"]
    assert len(flips) == 2 and {r["line_id"] for r in flips} == {"OL-G05", "OL-G07"}
    for r in flips:
        assert r["flips_at_home_points"] == "1.0", "the grid threshold must be computed, not asserted"
        assert abs(float(r["model_fair_spread_home"])) < 1.0, "only near-picks can flip on a one-point dial"


def test_model_facts_blank_rules_and_arithmetic() -> None:
    facts = {r["fact_id"]: r for r in derive.fact_register()}
    assert len(facts) == 25 and set(facts) == {f"MF-{i:02d}" for i in range(1, 26)}
    for fid in ("MF-20", "MF-21", "MF-25"):
        assert facts[fid]["value"].strip() == "", f"{fid} has a value but no verified input for it"
        assert facts[fid]["status"] == "unverified_blank"
        assert len(facts[fid]["derivation_or_definition"]) > 40
        assert facts[fid]["flag_id"], f"{fid} must point at a flag"
    for r in facts.values():
        assert r["source_url"].startswith("https://") and r["read_date"] == "2026-11-13"
        assert r["category"] and r["item"] and r["status"] in (
            "verified", "computed", "unverified_blank", "model_assumption")
    assert facts["MF-19"]["value"] == "0.523810"
    assert abs(float(facts["MF-19"]["value"]) - 11 / 21) < 1e-6
    assert facts["MF-02"]["value"] == "137" and facts["MF-01"]["value"] == "32"
    assert facts["MF-22"]["status"] == "model_assumption"
    assert float(facts["MF-23"]["value"]) > float(facts["MF-24"]["value"]), (
        "the model's regulation-tie mass exceeds the observed tie rate; that gap is FL-16 and must stay visible")


def test_gate_and_strategy_and_leaderboard_registers() -> None:
    lines, summary = derive.originated_lines()
    gates_rows, states = derive.gate_register(summary)
    assert len(gates_rows) == 16
    assert sum(1 for r in gates_rows if r["state"] == "PASS") == 7
    assert sum(1 for r in gates_rows if r["state"] == "FAIL") == 2
    assert sum(1 for r in gates_rows if r["state"] == "BLOCKED") == 7
    for r in gates_rows:
        assert states[r["gate_id"]] == r["state"]
        assert r["enforcer_path"].startswith(("src/", "scripts/", "data/", "tools/"))
    strat = derive.strategy_register(states)
    board = derive.leaderboard_register(states, summary)
    assert len(strat) == len(board) == 12
    kinds = " ".join(r["structure"] for r in strat).lower()
    assert "single" in kinds and "parlay" in kinds and "prop" in kinds, "the brief covers all three structures"
    for r in strat:
        assert r["status"] == "PREREGISTERED_UNQUALIFIED"
        assert r["hypothesis"].strip() and r["luck_controls"].strip()
        assert r["reward_tier"] == "TIER-0"
    ranks = [int(r["rank"]) for r in board]
    assert ranks == sorted(ranks) and len(set(ranks)) == 12
    ready = [float(r["readiness"]) for r in board]
    assert ready == sorted(ready, reverse=True)
    for r in board:
        assert r["status"] == "UNQUALIFIED" and r["reward_tier"] == "TIER-0"
        assert int(r["settled_selections"]) == 0, "the measured count is zero, not blank"
        for k in ("holdout_roi", "same_line_clv", "brier", "skill_score"):
            assert r[k].strip() == "", f"{r['strategy_id']}: {k} must be blank until the gates pass"
        assert r["missing_features"].strip()
    tiers = derive.reward_register()
    assert len(tiers) == 4 and tiers[0]["tier_id"] == "TIER-0"
    assert tiers[0]["entries_at_tier"] == "12"


def test_sensitivity_grid_covers_every_line_and_assumption() -> None:
    rows = derive.sensitivity_register()
    assert len({r["sens_id"] for r in rows}) == len(rows), "sensitivity ids must be unique"
    power = [r for r in rows if r["game_id"] == "power"]
    grid = [r for r in rows if r["game_id"] != "power"]
    assert len(grid) == 13 * 4 and len(power) == 12
    per_game: dict[str, list[str]] = {}
    for r in grid:
        per_game.setdefault(r["game_id"], []).append(r["assumed_home_points"])
    assert len(per_game) == 13
    neutral = [g["game_id"] for g in _csv(DATA / "week10_slate.csv")
               if g["game_state"] == "Scheduled" and g["neutral_site"] == "yes"]
    for game_id, values in per_game.items():
        if game_id in neutral:
            assert values == ["0.0"] * 4, "a neutral site holds the home assumption at zero by design"
        else:
            assert values == ["0.0", "1.0", "1.5", "2.5"], (game_id, values)
    by_game: dict[str, dict[str, dict]] = {}
    for r in grid:
        by_game.setdefault(r["game_id"], {})[r["assumed_home_points"]] = r
    for game_id, cells in by_game.items():
        if "1.0" not in cells:
            continue
        totals = {float(c["total"]) for c in cells.values()}
        assert max(totals) - min(totals) < 1e-9, f"{game_id}: the total moved with the home assumption"
        # the published spread is quoted on the home club, so adding home points moves it by exactly -hfa
        for assumed, cell in cells.items():
            if assumed == "0.0":
                continue
            step = float(cell["spread_home"]) - float(cells["0.0"]["spread_home"])
            assert abs(step + float(assumed)) < 1e-9, f"{game_id}: {assumed} pt moved the spread by {step}"


# ---------------------------------------------------------------- published artefacts


def test_no_carriage_returns_in_this_packs_files() -> None:
    paths = list(DATA.rglob("*.csv")) + list(DATA.rglob("*.psv")) \
        + list((ROOT / "docs" / "nfl-decision-desk").rglob("*.html")) + list(
            (ROOT / "docs" / "nfl-decision-desk").rglob("*.css"))
    assert paths, "nothing to check"
    for path in paths:
        assert b"\r" not in path.read_bytes(), path


def test_dashboard_builder_is_reproducible_and_the_verifier_passes() -> None:
    build = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_nfl_desk.py"), "--check"],
                           capture_output=True, text=True, cwd=ROOT)
    assert build.returncode == 0, build.stderr[:900]
    if str(ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(ROOT / "scripts"))
    import check_nfl_desk  # noqa: WPS433

    checker = check_nfl_desk.Checker()
    check_nfl_desk.check_line_endings(checker)
    check_nfl_desk.check_inputs(checker)
    check_nfl_desk.check_derived(checker)
    check_nfl_desk.check_pages(checker)
    assert checker.fails == [], "verifier problems:\n  " + "\n  ".join(checker.fails[:12])


def test_executive_summary_numbers_match_the_registers() -> None:
    """The prose carries numbers; this test is what stops them drifting from the data."""
    text = (ROOT / "NFL_DECISION_DESK_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    facts = {r["fact_id"]: r["value"] for r in derive.fact_register()}
    for token in (facts["MF-03"], facts["MF-04"], facts["MF-05"], facts["MF-06"], facts["MF-19"],
                  facts["MF-13"], facts["MF-14"], facts["MF-11"], facts["MF-12"]):
        assert token and token in text, f"{token} is in the register but not in the summary"
    corr = {r["corr_id"]: r for r in derive.correlation_register()}
    assert corr["CR-06"]["pearson_r"] in text and corr["CR-03"]["pearson_r"] in text
    assert "137 games" in text and "2026-11-13" in text
    led = [dict(zip(audit.LEDGER_HDR, r)) for r in audit.ledger_rows()]
    verified = sum(1 for r in led if r["verification_status"] == "verified")
    # the summary quotes the ledger's size and split; recompute them rather than trusting the prose
    for token in (f"{len(led)} rows", f"{verified} verified", f"{len(led) - verified} needing review"):
        assert token in text, f"summary is stale: it should say {token!r}"


def load_tests(loader, tests, pattern):  # noqa: ARG001 - lets unittest discover collect these functions
    suite = unittest.TestSuite()
    for name in sorted(globals()):
        fn = globals()[name]
        if name.startswith("test_") and callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn, description=name))
    return suite


if __name__ == "__main__":
    failures = 0
    for name in sorted(globals()):
        fn = globals()[name]
        if not (name.startswith("test_") and callable(fn)):
            continue
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {name}")
    print(f"RESULT: {len([1 for n in globals() if n.startswith('test_')]) - failures} passed, {failures} failed")
    raise SystemExit(1 if failures else 0)
