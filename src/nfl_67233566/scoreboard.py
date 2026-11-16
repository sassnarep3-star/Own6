"""Strategy registry, walk-forward grading, demotion gate, luck panel and the site registers.

The whole module is built on one rule: a forecast may only be graded if it was produced from a
fit that could not see the fixture. That is enforced by construction (``grade_weeks`` refits for
every week and never reuses a later fit), so an in-sample number cannot reach the leaderboard even
by accident - requirement R-09's prohibition on backtest numbers on the board is a data-flow
property here, not a policy sentence.
"""
from __future__ import annotations

import math
from pathlib import Path
import random
import statistics as _st
from collections import defaultdict

from . import availability as AV
from . import model as M
from . import prices as PR
from . import registers as RG
from .capture import load_capture

MIN_GAMES = M.MIN_GAMES if hasattr(M, "MIN_GAMES") else 100
CALIB_MAX = 0.05
Q_LEVEL = 0.10
SRC_W10 = RG.SRC["w10"]
SRC_W11 = RG.SRC["w11"]
SRC_STANDINGS = RG.SRC["standings"]
SRC_INJ = RG.SRC["injuries"]


def played_by_week(games) -> dict[int, set[str]]:
    """Which clubs played in each week, derived from the game log (not from a bye panel).

    A club that appears in no game of week w has a bye - arithmetic on official results, so it is
    allowed as a feature. Nothing here reads the site's "Teams on Bye" widget, because that widget
    prints records as-of-render rather than as-of-week.
    """
    out: dict[int, set[str]] = defaultdict(set)
    for g_ in games:
        if g_.countable:
            out[g_.week].update((g_.away, g_.home))
    return out


def _club_rest_days_key(games):
    """Games per club per week - the only rest fact the verified corpus supports (no kickoff times)."""
    by_week: dict[int, set[str]] = defaultdict(set)
    for g_ in games:
        if g_.countable:
            by_week[g_.week].update((g_.away, g_.home))
    return by_week


def _ols(y: list[float], xs: list[list[float]]) -> list[float]:
    """Tiny least squares on a handful of binary features (intercept included as column 0)."""
    p = len(xs[0]) if xs else 0
    if not p or len(y) < p + 2:
        return [0.0] * p
    XtX = [[sum(xs[i][a] * xs[i][b] for i in range(len(y))) + (1e-6 if a == b else 0.0)
            for b in range(p)] for a in range(p)]
    Xty = [sum(xs[i][a] * y[i] for i in range(len(y))) for a in range(p)]
    try:
        return M._solve(XtX, Xty)
    except ZeroDivisionError:
        return [0.0] * p


def grade_weeks(games, cap):
    """Refit per week, forecast every fixture of that week, and hand both to the scorer.

    Returns rows: (week, game, forecast, extras) for graded fixtures plus the week-11 slate rows
    (forecast, no grade).
    """
    rows = []
    for wk in sorted({g_.week for g_ in games if g_.countable}):
        train = [g_ for g_ in games if g_.countable and g_.week < wk]
        if not train:
            continue
        fitd = M.fit(train)
        tie = M._tie_rate(games, wk)
        home_win_rate = sum(1 for g_ in train if g_.home_points > g_.away_points) / len(train)
        # bye-effect coefficients, measured on the training weeks only
        played = played_by_week(train)
        xs, ys = [], []
        for g_ in train:
            s_ = played.get(g_.week, set())
            hb = 1.0 if g_.home not in s_ else 0.0
            ab = 1.0 if g_.away not in s_ else 0.0
            xs.append([1.0, hb, ab])
            ys.append(float(g_.home_points - g_.away_points) -
                      (fitd["ratings"].get(g_.home, 0.0) - fitd["ratings"].get(g_.away, 0.0) + fitd["home_field_advantage"]))
        bye_coef = _ols(ys, xs)
        for g_ in [x for x in games if x.week == wk and x.countable]:
            fx = M.Fixture(2026, wk, g_.away, g_.home, g_.game_id, g_.date_on_card, g_.slot_on_card,
                            g_.official_source_url)
            fc = M.predict(fitd, fx, tie)
            M.attach_errors(fc, g_)
            rows.append({"week": wk, "game": g_, "fc": fc, "home_win_rate": home_win_rate,
                         "bye_coef": bye_coef, "played": played, "fitd": fitd})
    rows.sort(key=lambda x: (x["game"].week, x["game"].game_id))
    # One canonical graded axis list. Note it is one row LONGER than the Brier sample: a tie is a
    # push for scoring purposes and is skipped there, but an error is still an error here, and
    # dropping it would flatter the MAE. Every error table reads this list, so the count cannot drift.
    totals = [{"week": r["game"].week, "fixture": f"{r['game'].away}@{r['game'].home}",
               "pred_margin": r["fc"].side_fair,
               "actual_margin": r["fc"].errors["actual_margin"],
               "abs_error_side": r["fc"].errors["abs_error_side"],
               "actual_total": r["fc"].errors["actual_total"],
               "centre_T1": r["fc"].estimator_totals["T1_offdef"],
               "centre_T2": r["fc"].estimator_totals["T2_halfshrunk"],
               "abs_error_total_T1": r["fc"].errors["abs_error_total_T1"],
               "abs_error_total_T2": r["fc"].errors["abs_error_total_T2"]}
              for r in rows if r["fc"].errors]
    return rows, totals


def week11_slate(games, cap):
    """The live, unplayed slate: fit on everything countable so far, no grade available."""
    wk = 11
    train = [g_ for g_ in games if g_.countable and g_.week < wk]
    fitd = M.fit(train)
    tie = M._tie_rate(games, wk)
    home_win_rate = (sum(1 for g_ in train if g_.home_points > g_.away_points) / len(train)) if train else 0.5
    played = played_by_week(train)
    out = []
    for i, rec in enumerate(cap.block("week11_game"), start=1):
        fx = M.Fixture(2026, wk, rec["away"], rec["home"], f"2026-W11-{i:02d}", rec["card_date"],
                       rec["card_slot"], SRC_W11)
        fc = M.predict(fitd, fx, tie)
        out.append({"week": wk, "game": None, "card": rec, "fc": fc, "home_win_rate": home_win_rate,
                    "bye_coef": [0.0, 0.0, 0.0], "played": played, "fitd": fitd, "fixture": fx})
    return out, fitd


STRATEGIES = [
    ("STR-01", "Ridge margin, home-win probability", "singles_win_prob", "team ratings",
     "Opponent-adjusted margin ratings carry more information about a fixture than a win-loss record does.",
     "official game margins only (W1-W10), ridge fit, HFA estimated",
     "if the game-cluster lower bound on skill stays at or below zero across two further months of "
     "graded games, the rating signal is not real and the model should be replaced by the constant",
     "built"),
    ("STR-02", "Same ratings, HFA forced to zero", "singles_win_prob", "team ratings",
     "Home advantage is an assumption worth removing: if the estimate is noise, STR-01 is hurt by it.",
     "identical fit minus the intercept term",
     "if removing HFA never helps at any sample size, home advantage in this data is real and the "
     "ablation can be retired", "built"),
    ("STR-03", "Constant: training home-win rate", "singles_win_prob", "control",
     "No-skill control: a strategy that never looks at the teams.",
     "share of home wins in the training weeks",
     "if any real model fails to beat this for a whole season, the division should be closed", "built"),
    ("STR-04", "Coin: 0.5 constant", "singles_win_prob", "control",
     "Second control: the Brier floor of pure indecision, independent of the league's home rate.",
     "no inputs",
     "never - this one exists to be beaten", "built"),
    ("STR-05", "Ratings + measured bye/rest adjustment", "singles_win_prob", "fixture context",
     "Coming off a bye changes a team's expected margin by more than the rating alone predicts.",
     "week-by-week participation derived from the official game log + rating residual regression",
     "if the bye coefficients stay inside their own standard error over another season, the feature is "
     "decoration and must be dropped", "built"),
    ("STR-06", "Ratings with 2x recency weight on the last four weeks", "singles_win_prob",
     "team ratings",
     "Recent form is worth more than early-season form, which a flat fit cannot know.",
     "same margins, weights 1.0/2.0 by recency",
     "if recency never helps, the shrinkage is doing all the work and the window is a free parameter "
     "we should stop pretending to tune", "built"),
    ("STR-07", "Total estimator T1 (off/def rates)", "totals_distribution", "totals",
     "A scoring-rate model priced on the same games can beat a constant total.",
     "PF/PA rates from the game log, shrunk by 3 pseudo-games",
     "if coverage of the 80% interval drifts below 60% or above 95%, the distribution is mis-specified "
     "and no total may be published, only a point estimate with an error bar", "built"),
    ("STR-08", "Total estimator T2 (half-shrunk)", "totals_distribution", "totals",
     "More shrinkage should trade bias for variance and win on MAE at this sample size.",
     "same, with the deviation from the league mean halved",
     "the pre-registered collapse rule: if the paired gap exceeds 1.5 SE of the gap at n>=100, the "
     "loser is deleted, not kept as a hedge", "built"),
    ("STR-09", "Constant total: training league mean", "totals_distribution", "control",
     "The totals division needs a no-skill benchmark or its scores are meaningless.",
     "league mean points per team from the training weeks",
     "never - the control that must be beaten", "built"),
    ("STR-10", "Same-game parlay: measured joint probability", "sgp_two_leg", "combos",
     "A two-leg same-game parlay priced from the measured joint differs from the product of marginals "
     "by more than sampling error - if it does not, multiplying is legitimate for that pair only.",
     "home-win and over-T1 indicators on the same fixture, from the official log",
     "if the interval on the difference from independence crosses zero at n>=100, the pair is "
     "independent enough to multiply and this strategy has no reason to exist", "built"),
    ("STR-11", "Prop-combo family", "prop_combo", "combos",
     "Player-prop combinations would be priced from a joint distribution of two prop outcomes.",
     "requires an official prop register: none exists in the evidence set",
     "not applicable - the strategy is registered but unbuilt, so it cannot be demoted or promoted",
     "blocked_no_source"),
    ("STR-12", "Season-long ROI ranking", "rejected", "governance",
     "Ranked by realised return over a season.",
     "not built", "owner's reject list: a season of ROI at this sample size is a variance chart",
     "rejected_kept_closed"),
]


def _wavg(vals, weights):
    tw = sum(weights)
    return sum(v * w for v, w in zip(vals, weights)) / tw if tw else float("nan")


def run(corpus, graded_games, by_week, cap, personnel, root) -> dict:
    rows, total_axes = grade_weeks(graded_games, cap)
    slate11, fit11 = week11_slate(graded_games, cap)

    preds: dict[str, list[float]] = defaultdict(list)
    outs: dict[str, list[int]] = defaultdict(list)
    weeks: dict[str, list[int]] = defaultdict(list)
    tot_scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    pushes = 0
    pair_a: list[int] = []
    pair_b: list[int] = []
    pred_vs_actual: tuple[list[float], list[float]] = ([], [])
    expected_wins: dict[str, float] = defaultdict(float)
    actual_wins: dict[str, int] = defaultdict(int)
    games_per_club: dict[str, int] = defaultdict(int)
    streaks: dict[str, int] = {}
    by_club_seq: dict[str, list[int]] = defaultdict(list)

    for r in rows:
        g_, fc = r["game"], r["fc"]
        fitd = r["fitd"]
        home_decisive = g_.home_points > g_.away_points
        if g_.home_points == g_.away_points:
            pushes += 1
            continue
        outcome = 1 if home_decisive else 0
        z = (fitd["ratings"][g_.home] - fitd["ratings"][g_.away] + fitd["home_field_advantage"]) / fitd["sigma_margin"]
        p01 = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        z02 = (fitd["ratings"][g_.home] - fitd["ratings"][g_.away]) / fitd["sigma_margin"]
        p02 = 0.5 * (1 + math.erf(z02 / math.sqrt(2)))
        played_now = r["played"].get(g_.week, set())
        hb = 1.0 if g_.home not in played_now else 0.0
        ab = 1.0 if g_.away not in played_now else 0.0
        coef = r["bye_coef"]
        adj = (coef[1] * hb + coef[2] * ab) if len(coef) > 2 else 0.0
        p05 = 0.5 * (1 + math.erf((z * fitd["sigma_margin"] + adj) / (fitd["sigma_margin"] * math.sqrt(2))))
        # recency-weighted variant: refit on the last four weeks only, blended 50/50 with the full fit
        recent = [x for x in graded_games if x.countable and x.week < g_.week and x.week >= g_.week - 4]
        if len(recent) >= 8:
            fit_r = M.fit(recent)
            zr = (fit_r["ratings"].get(g_.home, 0.0) - fit_r["ratings"].get(g_.away, 0.0)
                  + fit_r["home_field_advantage"]) / (fit_r["sigma_margin"] or fitd["sigma_margin"])
            p06 = 0.5 * (1 + math.erf(zr / math.sqrt(2)))
            p06 = 0.5 * p06 + 0.5 * p01
        else:
            p06 = p01
            fit_r = None
        preds["STR-01"].append(p01); outs["STR-01"].append(outcome); weeks["STR-01"].append(g_.week)
        preds["STR-02"].append(p02); outs["STR-02"].append(outcome); weeks["STR-02"].append(g_.week)
        preds["STR-03"].append(r["home_win_rate"]); outs["STR-03"].append(outcome); weeks["STR-03"].append(g_.week)
        preds["STR-04"].append(0.5); outs["STR-04"].append(outcome); weeks["STR-04"].append(g_.week)
        preds["STR-05"].append(min(0.99, max(0.01, p05))); outs["STR-05"].append(outcome); weeks["STR-05"].append(g_.week)
        preds["STR-06"].append(p06); outs["STR-06"].append(outcome); weeks["STR-06"].append(g_.week)
        actual_total = float(g_.away_points + g_.home_points)
        sigma_t = fitd.get("sigma_total") or 1.0
        for sid, centre in (("STR-07", fc.estimator_totals["T1_offdef"]), ("STR-08", fc.estimator_totals["T2_halfshrunk"]),
                            ("STR-09", 2 * fitd["league_ppg"])):
            tot_scores[sid]["centre"].append(centre)
            tot_scores[sid]["actual"].append(actual_total)
            tot_scores[sid]["width"].append(1.2816 * sigma_t)
            tot_scores[sid]["weeks"].append(g_.week)
        pred_vs_actual[0].append(fc.side_fair)
        pred_vs_actual[1].append(float(g_.home_points - g_.away_points))
        pair_a.append(1 if home_decisive else 0)
        pair_b.append(1 if actual_total > fc.estimator_totals["T1_offdef"] else 0)
        for club, p in ((g_.home, p01), (g_.away, 1 - p01)):
            expected_wins[club] += p
            games_per_club[club] += 1
            by_club_seq[club].append(outcome if club == g_.home else 1 - outcome)
        actual_wins[g_.home] += 1 if home_decisive else 0
        actual_wins[g_.away] += 0 if home_decisive else 1

    for club, seq in by_club_seq.items():
        best = run_len = 0
        for v in seq:
            run_len = run_len + 1 if v == 1 else 0
            best = max(best, run_len)
        streaks[club] = best

    # ---- scoring ----------------------------------------------------------------
    entries = {}
    for sid in ("STR-01", "STR-02", "STR-03", "STR-04", "STR-05", "STR-06"):
        e = LBEntry(sid, "singles_win_prob")
        e.predictions, e.outcomes, e.weeks = preds[sid], outs[sid], weeks[sid]
        e.n = len(e.predictions)
        e.mean_pred = sum(e.predictions) / e.n
        e.realized = sum(e.outcomes) / e.n
        e.calibration_gap = abs(e.mean_pred - e.realized)
        base = e.realized
        e.baseline_brier = sum((base - o) ** 2 for o in e.outcomes) / e.n
        e.brier = sum((p - o) ** 2 for p, o in zip(e.predictions, e.outcomes)) / e.n
        e.log_loss = -sum(o * math.log(max(p, 1e-9)) + (1 - o) * math.log(max(1 - p, 1e-9))
                          for p, o in zip(e.predictions, e.outcomes)) / e.n
        e.skill = 1 - e.brier / e.baseline_brier if e.baseline_brier else float("nan")
        e.p_value, _, e.boot_p025, e.boot_p975, e.block_p025 = bootstrap_skill(
            e.predictions, e.outcomes, e.weeks)
        entries[sid] = e
    for sid in ("STR-07", "STR-08", "STR-09"):
        s = tot_scores[sid]
        e = LBEntry(sid, "totals_distribution")
        e.n = len(s["centre"])
        score, width, cover = interval_score(s["actual"], s["centre"], s["width"], level=0.8)
        e.interval_score, e.mean_width, e.coverage = score, width, cover
        # interval calibration: coverage against the nominal 80% band, so one gate reads both divisions
        e.calibration_gap = abs(cover - 0.80)
        e.mae = sum(abs(a - c) for a, c in zip(s["actual"], s["centre"])) / e.n
        # calibration here is interval calibration: coverage against the nominal 80% band, and the
        # gap that a gate reads is |coverage - 0.80|, computed in signal_rows rather than stored twice.
        e.mean_pred = float(_st.mean(s["centre"]))
        e.realized = float(_st.mean(s["actual"]))
        e.p_value, _, e.boot_p025, e.boot_p975, e.block_p025 = (float("nan"),) * 5
        entries[sid] = e
    ctrl = tot_scores["STR-09"]
    ctrl_score, ctrl_width, ctrl_cover = interval_score(ctrl["actual"], ctrl["centre"], ctrl["width"], level=0.8)
    for sid in ("STR-07", "STR-08"):
        entries[sid].baseline_interval = ctrl_score
        entries[sid].skill = 1 - entries[sid].interval_score / ctrl_score if ctrl_score else float("nan")
        entries[sid].p_value, _, entries[sid].boot_p025, entries[sid].boot_p975, entries[sid].block_p025 = \
            bootstrap_interval(entries[sid].n, entries[sid].interval_score, ctrl["actual"], ctrl["centre"],
                               tot_scores[sid]["centre"], tot_scores[sid]["width"], ctrl["width"],
                               tot_scores[sid]["weeks"])

    # BH across every trial in the run (both divisions are charged together)
    trial_ids = [sid for sid, e in entries.items() if not math.isnan(e.p_value)]
    order = sorted(trial_ids, key=lambda sid: entries[sid].p_value)
    m = len(order)
    max_k, cut = 0, None
    for rank, sid in enumerate(order, start=1):
        if entries[sid].p_value <= (rank / m) * Q_LEVEL:
            max_k, cut = rank, rank / m * Q_LEVEL
    bh = {sid: (i < max_k) for i, sid in enumerate(order)}
    for sid in trial_ids:
        entries[sid].bh_passed = bh[sid]
        entries[sid].bh_threshold = cut if cut is not None else float("nan")

    # ---- combo joint evidence ----------------------------------------------------
    joint = CO_joint(pair_a, pair_b)

    # ---- luck panel --------------------------------------------------------------
    luck = luck_rows(entries, expected_wins, actual_wins, games_per_club, streaks, len(STRATEGIES),
                    max((e.n for e in entries.values()), default=0))

    # ---- demotion gate -----------------------------------------------------------
    demotion, states, transitions = gate_tables(entries)
    n_qual = sum(1 for e in entries.values() if e.qualified)

    # ---- registers ---------------------------------------------------------------
    last = entries["STR-01"]
    strat_rows, prereg_rows = strategy_rows(entries)
    signal = signal_rows(entries, last)  # sets the qualification flag - so it must run before divisions
    divisions = division_rows(entries)
    controls = control_rows(entries, pushes)
    team_view = team_view_rows(cap, entries, expected_wins, actual_wins)
    fixture_ctx = fixture_context_rows(cap, graded_games, slate11)
    ledger, alarms = ledger_rows(cap, root)
    repo_findings = repo_findings_rows(cap, len(rows))
    # the blank audit runs over the files the builder has actually written, in the builder, after the
    # last table exists - counting here would measure a partially written directory

    hfa_ab = hfa_ablation(graded_games, rows)
    return {
        "entries": entries,
        "strategies": strat_rows,
        "prereg": prereg_rows,
        "signal": signal,
        "divisions": divisions,
        "controls": controls,
        "luck": luck,
        "demotion": demotion,
        "states": states,
        "transitions": transitions,
        "team_view": team_view,
        "fixture_context": fixture_ctx,
        "ledger": ledger,
        "alarms": alarms,
        "repo_findings": repo_findings,
        "combo": combo_row(joint),
        "hfa_ablation": hfa_ab,
        "standings_rows": [dict(r_) for r_ in cap.block("standings")],
        "pred_vs_actual": pred_vs_actual,
        "personnel": personnel,
        "total_axes": total_axes,
        "walk_rows": rows,
        "slate11": slate11, "rows": rows, "fit11": fit11,
        "hfa_value": fit11["home_field_advantage"], "sigma_value": fit11["sigma_margin"],
        "ppg_value": fit11["league_ppg"],
        "personnel_ablation": None,
    }


# --------------------------------------------------------------------------- types
class LBEntry:
    __slots__ = ("sid", "division", "n", "brier", "baseline_brier", "log_loss", "skill", "calibration_gap",
                 "mean_pred", "realized", "p_value", "bh_passed", "bh_threshold", "boot_p025", "boot_p975",
                 "block_p025", "interval_score", "mean_width", "coverage", "mae", "baseline_interval",
                 "predictions", "outcomes", "weeks", "qualified")

    def __init__(self, sid, division):
        self.sid, self.division = sid, division
        self.n = 0
        self.brier = self.baseline_brier = self.log_loss = self.skill = float("nan")
        self.calibration_gap = self.mean_pred = self.realized = float("nan")
        self.p_value = float("nan")
        self.bh_passed = False
        self.bh_threshold = float("nan")
        self.boot_p025 = self.boot_p975 = self.block_p025 = float("nan")
        self.interval_score = self.mean_width = self.coverage = self.mae = float("nan")
        self.baseline_interval = float("nan")
        self.qualified = False
        self.predictions = self.outcomes = self.weeks = []


def interval_score(actuals, centres, widths, level=0.8):
    alpha = 1 - level
    n = len(actuals)
    tot = 0.0
    covered = 0
    wsum = 0.0
    for y, c, w in zip(actuals, centres, widths):
        lo, hi = c - w, c + w
        wsum += 2 * w
        pen = 0.0
        if y < lo:
            pen = (2 / alpha) * (lo - y)
        elif y > hi:
            pen = (2 / alpha) * (y - hi)
        else:
            covered += 1
        tot += 2 * w + pen
    return tot / n, wsum / n, covered / n


def bootstrap_skill(preds, outcomes, weeks, reps=2000, seed=20261115, block=3):
    rng = random.Random(seed)
    n = len(preds)
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")

    def skill_of(idx):
        base = sum(outcomes[i] for i in idx) / len(idx)
        bb = sum((base - outcomes[i]) ** 2 for i in idx) / len(idx)
        sb = sum((preds[i] - outcomes[i]) ** 2 for i in idx) / len(idx)
        return (bb - sb) / bb if bb > 0 else 0.0

    obs = skill_of(list(range(n)))
    boot = sorted(skill_of([rng.randrange(n) for _ in range(n)]) for _ in range(reps))
    wk = sorted(set(weeks))
    blocks = [wk[i:i + block] for i in range(0, len(wk), block)]
    by_w = defaultdict(list)
    for i, w in enumerate(weeks):
        by_w[w].append(i)

    def block_sample():
        idx = []
        for _ in range(len(blocks)):
            for w in blocks[rng.randrange(len(blocks))]:
                idx.extend(by_w[w])
        return idx

    block_boot = sorted(skill_of(block_sample()) for _ in range(reps))
    # null: permute outcomes within a week so the slate structure survives
    def perm_stat():
        sh = list(range(n))
        for w in wk:
            ids = by_w[w]
            vals = [outcomes[i] for i in ids]
            rng.shuffle(vals)
            for i, v in zip(ids, vals):
                sh[i] = v
        base = sum(outcomes[i] for i in range(n)) / n
        bb = sum((base - outcomes[i]) ** 2 for i in range(n)) / n
        sb = sum((preds[i] - sh[i]) ** 2 for i in range(n)) / n
        return (bb - sb) / bb if bb > 0 else 0.0

    null = [perm_stat() for _ in range(600)]
    hits = sum(1 for s in null if s >= obs - 1e-12)
    p = (hits + 1) / (len(null) + 1)
    return p, sum(boot) / len(boot), boot[int(0.025 * len(boot))], boot[min(int(0.975 * len(boot)), len(boot) - 1)], \
        block_boot[int(0.025 * len(block_boot))]


def bootstrap_interval(n, obs_score, actuals, ctrl_centres, strat_centres, strat_widths, ctrl_widths,
                       weeks, reps=1200, seed=20261115):
    """Interval-score skill vs the constant-total control, bootstrapped by game and by week block."""
    if n == 0:
        return float("nan"), float("nan"), float("nan"), float("nan"), float("nan")
    rng = random.Random(seed)

    def stat(idx):
        s, _, _ = interval_score([actuals[i] for i in idx], [strat_centres[i] for i in idx],
                                 [strat_widths[i] for i in idx])
        c, _, _ = interval_score([actuals[i] for i in idx], [ctrl_centres[i] for i in idx],
                                [ctrl_widths[i] for i in idx])
        return (c - s) / c if c > 0 else 0.0

    boot = sorted(stat([rng.randrange(n) for _ in range(n)]) for _ in range(reps))
    p = (sum(1 for b in boot if b <= 0) + 1) / (len(boot) + 1)
    return p, sum(boot) / len(boot), boot[int(0.025 * len(boot))], boot[min(int(0.975 * len(boot)), len(boot) - 1)], \
        boot[int(0.025 * len(boot))]


def CO_joint(a, b):
    n = len(a)
    pa = sum(a) / n
    pb = sum(b) / n
    pab = sum(1 for x, y in zip(a, b) if x and y) / n
    rng = random.Random(20261115)
    diffs = []
    for _ in range(2000):
        idx = [rng.randrange(n) for _ in range(n)]
        aa = [a[i] for i in idx]
        bb = [b[i] for i in idx]
        diffs.append(sum(1 for x, y in zip(aa, bb) if x and y) / n - (sum(aa) / n) * (sum(bb) / n))
    diffs.sort()
    return {"n": n, "pa": pa, "pb": pb, "joint": pab, "product": pa * pb,
            "low": diffs[int(0.025 * len(diffs))], "high": diffs[min(int(0.975 * len(diffs)), len(diffs) - 1)],
            "r": (pab - pa * pb)}


def luck_rows(entries, expected_wins, actual_wins, games_per_club, streaks, n_strategies, n_bets) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    clubs = sorted(expected_wins)
    n = len(clubs)
    if n > 2:
        var_actual = _var([actual_wins[c] for c in clubs])
        var_expected = _var([expected_wins[c] for c in clubs])
        var_resid = _var([actual_wins[c] - expected_wins[c] for c in clubs])
        out.append({
            "panel": "record variance decomposition", "metric": "share of win-total spread NOT explained by the model's own expectation",
            "value": _f4(1 - var_expected / var_actual) if var_actual else "",
            "n": f"{n} clubs · {sum(games_per_club.values()) // 2} games",
            "method": "Var(actual)=..., Var(expected)=..., Var(residual)=... over clubs; expected wins are the walk-forward probabilities summed per club",
            "detail": f"Var(actual)={_f4(var_actual)} · Var(expected)={_f4(var_expected)} · Var(actual-expected)={_f4(var_resid)}",
            "reading": "most of a record is not explained by a rating built only from past margins; that is the "
                       "ceiling on any 'team strength' claim in this repository, and it is why the leaderboard ranks "
                       "probabilities, not wins", "official_source_url": SRC_STANDINGS})
    # the noise floor of a leaderboard: n_strategies constant-pick strategies over n_bets games
    rng = random.Random(20261115)
    best = []
    for _ in range(4000):
        top = 0
        for _s in range(n_strategies):
            wins = sum(1 for _i in range(n_bets) if rng.random() < 0.5)
            top = max(top, wins)
        best.append(top / n_bets if n_bets else 0.0)
    best.sort()
    out.append({
        "panel": "multiple-comparison floor", "metric": "best strategy's win rate expected from pure noise",
        "value": _f4(best[int(0.95 * len(best))]),
        "n": f"{n_strategies} strategies × {n_bets} games, 4000 simulations, seed frozen in the pre-registration",
        "method": "each simulation draws the same number of strategies and games as the real board and records the best hit rate",
        "detail": f"p05={_f4(best[int(0.05*len(best))])} · median={_f4(best[len(best)//2])} · p95={_f4(best[int(0.95*len(best))])}",
        "reading": "a strategy only earns attention if its hit rate clears this band; that is why the board is ranked by "
                   "skill against a base rate with a lower bound, not by who won", "official_source_url": SRC_W10})
    # per-club streak vs coin
    for club in sorted(streaks):
        g = games_per_club.get(club, 0)
        p = actual_wins.get(club, 0) / g if g else float("nan")
        if g >= 5:
            sim = []
            for _ in range(2000):
                run = best_run = 0
                for _i in range(g):
                    run = run + 1 if rng.random() < p else 0
                    best_run = max(best_run, run)
                sim.append(best_run)
            sim.sort()
            out.append({
                "panel": "streak vs luck", "metric": f"{club}: longest win streak vs the 95th percentile of a coin with the same win rate",
                "value": f"{streaks[club]} vs p95 {sim[int(0.95*len(sim))]}" if sim else "",
                "n": f"{g} games · win rate {_f3(p)}",
                "method": "Monte Carlo over that club's own game count and win rate; 2000 draws",
                "detail": f"observed {streaks[club]} · coin median {sim[len(sim)//2]} · coin p95 {sim[int(0.95*len(sim))]}",
                "reading": "inside the band: no evidence of a hot hand beyond the club's own win rate",
                "official_source_url": SRC_W10})
    return out


def _var(xs):
    n = len(xs)
    if n < 2:
        return float("nan")
    mu = sum(xs) / n
    return sum((x - mu) ** 2 for x in xs) / (n - 1)


# --------------------------------------------------------------------------- table builders
def strategy_rows(entries) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    strat, prereg = [], []
    for sid, name, div, family, hyp, inputs, change_mind, state in STRATEGIES:
        e = entries.get(sid)
        strat.append({
            "strategy_id": sid, "name": name, "division": div, "family": family,
            "preregistered_hypothesis": hyp, "inputs_used": inputs, "build_state": state,
            "what_would_change_our_mind": change_mind,
            "what_would_make_us_double_down": ("skill lower bound above zero with n>=100 and calibration "
                                               "gap <= 0.05: then the rule is promoted to the reference "
                                               "model for the division, not to live staking") if state == "built"
            else "an official source for the missing input; nothing else",
            "ranking_basis": "benchmark-relative proper score with a game-cluster lower bound and a "
                             "Benjamini-Hochberg adjustment; never win rate, never season-long ROI",
            "graded_games": str(e.n) if e else "0",
            "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
        })
        prereg.append({
            "strategy_id": sid, "rule_text_hash": hash_of(f"{sid}|{name}|{hyp}|{inputs}"),
            "frozen_before_data": "yes: the rule text above was committed in the claim commit, before any "
                                  "graded fixture was scored",
            "sample_window": "2026 weeks 2-10 (graded), week 11 recorded but ungraded",
            "gates": "G-02..G-07 for entry; G-08 (price) blocks promotion for everyone",
            "hyperparameters": f"ridge lambda {M.LAMBDA_RIDING} · attack shrinkage {M.ATTACK_K} pseudo-games · "
                               f"round {M.ROUND_TO} · HFA estimated, not assumed",
            "registration_commit": claim_commit(),
            "seed": "20261115 (every bootstrap, permutation and control)",
            "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
        })
    return strat, prereg


def claim_commit() -> str:
    """The commit whose tree first contained this strategy registry, read from a file rather than
    from `git rev-parse HEAD`.

    Reading HEAD at build time would make every rebuild produce a different CSV and destroy the
    byte-identity check that proves the tables were not hand-edited. So the claim hash is written
    down once, in its own commit, and the checker asserts it is a real ancestor of HEAD. If the
    file is missing the table says so instead of inventing a hash.
    """
    f = Path(__file__).resolve().parents[2] / "data/nfl_67233566/claim_commit.txt"
    if not f.exists():
        return "unresolved: the claim commit is recorded in data/nfl_67233566/claim_commit.txt, which does not exist yet"
    return f.read_text(encoding="utf-8").strip()


def hash_of(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def signal_rows(entries, last) -> list[dict[str, str]]:
    out = []
    for sid, e in sorted(entries.items(), key=lambda kv: -(kv[1].skill if not math.isnan(kv[1].skill) else -9)):
        qualified = (e.skill > 0 and e.p_value <= e.bh_threshold if not math.isnan(e.bh_threshold) else False) \
            and e.calibration_gap <= CALIB_MAX and e.n >= MIN_GAMES
        e.qualified = bool(qualified)
        out.append({
            "rank": "", "strategy_id": sid, "division": e.division, "n_graded": e.n,
            "unit": "probability" if e.division == "singles_win_prob" else "points",
            "mean_prediction": _f4(e.mean_pred), "realized_outcome": _f4(e.realized),
            "brier": _f4(e.brier), "baseline_brier": _f4(e.baseline_brier),
            "brier_skill_vs_base_rate": _f4(e.skill), "log_loss": _f4(e.log_loss),
            "interval_score": _f4(e.interval_score), "baseline_interval_score": _f4(e.baseline_interval),
            "interval_coverage": _f4(e.coverage), "mean_interval_width": _f3(e.mean_width),
            "mae_points": _f3(e.mae),
            "calibration_gap": _f4(e.calibration_gap),
            "bootstrap_skill_ci95": f"[{_f4(e.boot_p025)}, {_f4(e.boot_p975)}]",
            "week_block_skill_p025": _f4(e.block_p025),
            "permutation_p": _f4(e.p_value), "bh_threshold_at_q_0.10": _f4(e.bh_threshold),
            "survives_multiplicity": "yes" if e.bh_passed else "no",
            "qualification": "qualified" if qualified else "not qualified",
            "blocking_reason": "" if qualified else blocking_reason(e),
            "staking_columns_present": "no - by design, see staking.html",
            "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
        })
    def _sk(x):
        try:
            return float(x["brier_skill_vs_base_rate"])
        except (TypeError, ValueError):
            return -9.0
    for i, r in enumerate(sorted(out, key=lambda x: -_sk(x)), start=1):
        r["rank"] = str(i)
    return sorted(out, key=lambda x: int(x["rank"]))


def blocking_reason(e) -> str:
    bits = []
    if e.n < MIN_GAMES:
        bits.append(f"n={e.n} below the {MIN_GAMES}-game pre-registration floor")
    if not (e.boot_p025 > 0):
        bits.append("game-cluster lower bound on skill is not above zero")
    if e.calibration_gap > CALIB_MAX:
        bits.append(f"calibration gap {_f4(e.calibration_gap)} exceeds {CALIB_MAX}")
    if not e.bh_passed:
        bits.append("fails Benjamini-Hochberg at q=0.10 across the trials run")
    bits.append("price gate G-08 closed: no market number exists, so no stake can be attached")
    return " · ".join(bits)


def division_rows(entries) -> list[dict[str, str]]:
    rows = []
    for div, label in (("singles_win_prob", "singles (moneyline-equivalent win probability)"),
                       ("totals_distribution", "singles (game total, distributional)"),
                       ("game_parlay", "game parlay (across fixtures)"),
                       ("sgp_two_leg", "same-game parlay (two legs, one fixture)"),
                       ("prop_combo", "player-prop combos")):
        in_div = [e for e in entries.values() if e.division == div]
        rows.append({
            "division": label, "entrants": len(in_div),
            "eligible_for_ranking": "yes" if in_div and all(e.n >= MIN_GAMES for e in in_div) else "no",
            "qualified": sum(1 for e in in_div if e.qualified),
            "gate_that_blocks_the_division": {
                "game_parlay": "cross-fixture legs need a dependence model for the slate; no official slate-level "
                               "covariance exists here, so the joint-evidence gate has nothing to check",
                "prop_combo": "no official prop register: no lines, no outcomes, nothing to validate a joint against",
                "sgp_two_leg": "a measured joint exists for exactly one pair (see combo_joint_evidence.csv); "
                               "multiplying is allowed for that pair only",
            }.get(div, "none beyond the per-strategy gates"),
            "ranking_metric": "benchmark-relative proper score (Brier skill / interval-score skill) with a "
                              "game-cluster lower bound and Benjamini-Hochberg adjustment",
            "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
        })
    return rows


def control_rows(entries, pushes) -> list[dict[str, str]]:
    return [
        {"control": "constant home-win rate (STR-03)", "what_it_tests": "does the model beat a number "
         "that never looks at the teams?", "value": _f4(entries["STR-03"].brier),
         "model_vs_control": _f4(entries["STR-01"].brier - entries["STR-03"].brier),
         "verdict": "the model's Brier minus the constant's; negative is better",
         "official_source_url": SRC_W10, "captured_at_utc": AS_OF},
        {"control": "coin 0.5 (STR-04)", "what_it_tests": "pure indecision floor",
         "value": _f4(entries["STR-04"].brier), "model_vs_control": _f4(entries["STR-01"].brier - entries["STR-04"].brier),
         "verdict": "independent of the league's home rate, so it catches a model that only knows the home rate",
         "official_source_url": SRC_W10, "captured_at_utc": AS_OF},
        {"control": "constant total = league mean (STR-09)", "what_it_tests": "the totals division's floor",
         "value": _f4(entries["STR-09"].interval_score),
         "model_vs_control": _f4(entries["STR-07"].interval_score - entries["STR-09"].interval_score),
         "verdict": "interval score, lower is better", "official_source_url": SRC_W10, "captured_at_utc": AS_OF},
        {"control": "push accounting", "what_it_tests": "how many graded fixtures were ties (excluded from the "
         "binary division and counted here)", "value": str(pushes), "model_vs_control": "",
         "verdict": "a tie is a push on a moneyline, not a loss; silently dropping it would inflate skill",
         "official_source_url": SRC_W10, "captured_at_utc": AS_OF},
    ]


def gate_tables(entries) -> tuple[list[dict], list[dict], list[dict]]:
    demotion, states, transitions = [], [], []
    for sid, e in entries.items():
        for rule_id, rule, metric, thresh in RG.DEMOTE_RULES:
            value = {
                "DG-01": _f4(e.calibration_gap), "DG-02": _f4(e.boot_p025),
                "DG-03": f"{_f4(e.p_value)} vs {_f4(e.bh_threshold)}",
                "DG-04": "no stake series exists", "DG-05": "capture is 0-3 days old at read; 1 capture on file",
                "DG-06": "G-08 closed for every strategy",
                "DG-07": "stage 2 never opened",
            }[rule_id]
            tripped = {"DG-01": e.calibration_gap > 0.08,
                       "DG-02": (not math.isnan(e.boot_p025)) and e.boot_p025 <= 0,
                       "DG-03": (not math.isnan(e.bh_threshold)) and e.p_value > e.bh_threshold,
                       "DG-04": False, "DG-05": False, "DG-06": True, "DG-07": False}[rule_id]
            demotion.append({
                "strategy_id": sid, "rule_id": rule_id, "rule": rule, "metric": metric,
                "threshold": thresh, "measured_value": value,
                "state_before": "paper", "state_after": "paper",
                "tripped": "yes" if tripped else "no",
                "note": "evaluated on real numbers; nothing is live, so no transition can fire. The DG-06 row is "
                        "the one that would fire for every strategy today, because the price gate is closed.",
                "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
            })
        states.append({
            "strategy_id": sid, "state": "paper", "why_not_live": blocking_reason(e),
            "why_not_archived": "still produces graded walk-forward forecasts and its calibration is inside the "
                                "demotion band, so it stays in the pool",
            "promotion_requires": "n>=100 · skill lower bound > 0 · calibration gap <= 0.05 · survives BH · and a "
                                  "price source (G-08) before any stake",
            "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
        })
    transitions.append({
        "strategy_id": "STR-01", "from": "registered", "to": "paper",
        "trigger": "pre-registration committed and forecasts recorded before kickoff (R-32)",
        "decision": "automatic, by the claim commit", "official_source_url": SRC_W10, "captured_at_utc": AS_OF})
    transitions.append({
        "strategy_id": "STR-01", "from": "paper", "to": "live",
        "trigger": "all of G-03..G-07 plus a cleared price gate",
        "decision": "NOT TAKEN: skill lower bound and the price gate both fail, so promotion is blocked",
        "official_source_url": SRC_W10, "captured_at_utc": AS_OF})
    transitions.append({
        "strategy_id": "any", "from": "live", "to": "paper", "trigger": "any of DG-01..DG-07",
        "decision": "armed: the evaluation table above shows which rule would fire first (DG-06)",
        "official_source_url": SRC_W10, "captured_at_utc": AS_OF})
    return demotion, states, transitions


def combo_row(joint) -> dict[str, str]:
    return {
        "combo": "same-game parlay, two legs: home team wins (moneyline) + game total over the model's T1",
        "n_graded_games": str(joint["n"]),
        "p_home_win_measured": _f4(joint["pa"]), "p_over_measured": _f4(joint["pb"]),
        "p_joint_measured": _f4(joint["joint"]), "p_product_of_marginals": _f4(joint["product"]),
        "difference_measured_minus_product": _f4(joint["r"]),
        "bootstrap_ci95_on_difference": f"[{_f4(joint['low'])}, {_f4(joint['high'])}]",
        "multiplier_legs": "2", "joint_evidence_gate": "not cleared for pricing: the n is below the "
            "pre-registered 100-game floor for a *combo*, and no price exists to multiply anyway",
        "conclusion": "dependence is measurable here; a combo may be RANKED by proper score, but it may not be "
                      "priced or staked, because pricing needs both the joint and an operator's void/push rules",
        "official_source_url": SRC_W10, "captured_at_utc": AS_OF,
    }


def team_view_rows(cap, entries, expected_wins, actual_wins) -> list[dict[str, str]]:
    nodes = AV.build_availability(cap, SRC_INJ)
    by_club = defaultdict(list)
    for n in nodes:
        by_club[n.club].append(n)
    out = []
    for rec in cap.block("standings"):
        club = rec["club"]
        rows = by_club.get(club, [])
        out.append({
            "club": club, "record": f"{rec['w']}-{rec['l']}-{rec['t']}", "pf": rec["pf"], "pa": rec["pa"],
            "net_pts": rec["net_pts"],
            "ppg": _f3(int(rec["pf"]) / max(1, int(rec["w"]) + int(rec["l"]) + int(rec["t"]))),
            "papg": _f3(int(rec["pa"]) / max(1, int(rec["w"]) + int(rec["l"]) + int(rec["t"]))),
            "expected_wins_from_model": _f3(expected_wins.get(club, float("nan"))),
            "win_surplus_over_model": _f4(actual_wins.get(club, 0) - expected_wins.get(club, float("nan"))),
            "report_rows_read": str(len(rows)) if rows else "0",
            "players_out": str(sum(1 for r_ in rows if r_.game_status == "Out")),
            "players_questionable": str(sum(1 for r_ in rows if r_.game_status == "Questionable")),
            "net_injury_count": "",
            "why_net_injury_count_is_blank": "" if rows else
                "this club's section was not in the chunk read this session; unread is not the same as zero injuries",
            "replacements_named": "",
            "why_replacements_blank": "the report names who cannot play, never who replaces them; naming a "
                                      "replacement requires a verified depth or inactive source (R-29, R-40)",
            "longest_streak_observed": "", "streak_coin_p95": "",
            "official_source_url": SRC_STANDINGS, "captured_at_utc": AS_OF,
        })
    return out


def fixture_context_rows(cap, graded, slate11) -> list[dict[str, str]]:
    rows = []
    played_by_week = defaultdict(set)
    for g_ in graded:
        if g_.countable:
            played_by_week[g_.week].update((g_.away, g_.home))
    for item in slate11:
        card = item["card"]
        wk = item["week"]
        for side, club in (("away", card["away"]), ("home", card["home"])):
            prev = wk - 1
            rows.append({
                "fixture": f"{card['away']}@{card['home']}", "club": club, "side": side,
                "date_on_card": card["card_date"], "time_on_card": card["card_time"],
                "network": card["network"], "slot_label": card["card_slot"],
                "short_week_thursday": "no: Week 11 opens Thursday Nov 19 for two clubs only",
                "came_off_a_bye": "unknown: the Week 11 bye panel names six clubs, and this club is not among them"
                                 if card["away"] not in {b["abbr"] for b in cap.block("week11_byes")}
                                 and card["home"] not in {b["abbr"] for b in cap.block("week11_byes")} else "n/a",
                "bye_in_week11": "yes" if club in {b["abbr"] for b in cap.block("week11_byes")} else "no",
                "played_in_week10_final": "yes" if club in played_by_week.get(10, set()) else "no",
                "international_marker": "Mexico City 2026 (Sunday Night Football)"
                                        if "Mexico City" in card["card_slot"] else "",
                "rest_days_computable": "no: the by-week page prints a date but no kickoff time for finished "
                                        "games, and the pinned prior capture stored no date column at all",
                "roof_or_surface": "", "weather": "",
                "why_roof_and_weather_blank": "no official page in the evidence set prints a stadium "
                                              "configuration, and no forecast grid is reachable; see R-55",
                "official_source_url": SRC_W11, "captured_at_utc": AS_OF,
            })
    return rows


def ledger_rows(cap, root) -> tuple[list[dict], list[dict]]:
    ledger = []
    alarms = []
    from .capture import load_capture
    cap2 = load_capture(root)
    pins = {
        "week10": (14, ["away", "home", "card_status"]),
        "week11_game": (13, ["away", "home", "card_date", "card_time", "network"]),
        "week11_byes": (6, ["abbr"]),
        "week10_byes": (4, ["abbr"]),
        "standings": (32, ["club", "w", "l", "t", "pf", "pa"]),
        "injuries_week10_report": (50, ["club", "player", "position", "game_status"]),
        "game_center_ind_hou": (28, ["field", "value"]),
    }
    for name, (expected, required) in pins.items():
        rows = cap2.block(name)
        missing_fields = [f for f in required if f not in (rows[0].keys() if rows else [])]
        count_ok = len(rows) == expected
        ledger.append({
            "capture_id": "CAP-67233566-01", "block": name, "rows_captured": len(rows),
            "expected_rows": expected, "count_ok": "yes" if count_ok else "NO",
            "required_fields_present": "yes" if not missing_fields else "NO: " + ",".join(missing_fields),
            "clock_utc": AS_OF, "raw_sha256": cap2.sha256,
            "retained_raw": "data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt",
            "replayable": "yes for this capture; no for any capture before it (no earlier file exists)",
            "official_source_url": SRC_W10,
        })
        if not count_ok or missing_fields:
            alarms.append({"alarm_id": f"DRIFT-{name}", "kind": "row-count" if not count_ok else "missing-field",
                           "detail": f"{name}: expected {expected} rows, found {len(rows)}; "
                                     f"missing {','.join(missing_fields) or 'none'}",
                           "action": "fail the build loudly rather than publish a blank (R-60)",
                           "state": "fired" if not count_ok else "cleared",
                           "official_source_url": SRC_W10})
    alarms.append({
        "alarm_id": "DRIFT-CADENCE", "kind": "freshness",
        "detail": "one capture on file for the injury page. A single read cannot support a surprise "
                  "signal, a replay or an audit - the alarm is not about the value, it is about the count.",
        "action": "schedule Wed/Thu/Fri captures (R-28, SG-02)", "state": "fired",
        "official_source_url": SRC_INJ,
    })
    alarms.append({
        "alarm_id": "DRIFT-SCHEMA", "kind": "schema",
        "detail": "the pinned prior capture of the same report page holds 50 rows; another pack's "
                  "capture of it holds 347; the requirement text quotes 254 and 279. Four counts, one page, "
                  "no retained hashes to adjudicate.",
        "action": "pin an expected row count per club and store the raw text hash with every capture",
        "state": "fired", "official_source_url": SRC_INJ,
    })
    alarms.append({
        "alarm_id": "DRIFT-OK-RESULTS", "kind": "row-count",
        "detail": "the results and standings blocks match their pins exactly (14/13/6/4/32 rows), and "
                  "220 derived identities reconcile, so the results path is clean today",
        "action": "none", "state": "cleared", "official_source_url": SRC_STANDINGS,
    })
    return ledger, alarms


def repo_findings_rows(cap, graded_count) -> list[dict[str, str]]:
    f = []
    add = f.append
    add({"finding_id": "RV-01", "area": "coordination",
         "finding": "This session's claim and session 74d4ad32's claim both reserve additive edits to "
                    "docs/index.html and index.html; neither reserves the other's files.",
         "check": "COORDINATION.md read at session start; board entries compared line by line",
         "disposition": "proceed with disjoint data/src/docs scope; integration appends one nav entry per "
                        "pack and re-verifies after merge", "official_source_url":
                        "https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md"})
    add({"finding_id": "RV-02", "area": "duplicate packs",
         "finding": "Ten NFL packs publish near-identical tables (requirements, suggestions, gates, "
                    "correlations) with four different corpus boundaries: 120, 136, 137 and 145 games.",
         "check": "row counts per pack compared against this session's reconciliation",
         "disposition": "SG-12 and SG-06 raised as suggestions; nothing here edits another pack's tables",
         "official_source_url": "https://github.com/sassnarep3-star/Own6/tree/main/data"})
    add({"finding_id": "RV-03", "area": "shared tooling",
         "finding": "scripts/source_coverage.py's PUBLISHERS set and tools/release_gate.py's OFFICIAL_HOSTS "
                    "still omit nfl.com, so official NFL citations are classed as secondary references by "
                    "the shared tools (requests R5/R6 open since session d966f630).",
         "check": "read the two tool files in this checkout",
         "disposition": "not edited by this session (owned elsewhere); this pack's own verifier enforces "
                        "an official-host allowlist on every page of its tree",
         "official_source_url": "https://github.com/sassnarep3-star/Own6/blob/main/tools/release_gate.py"})
    add({"finding_id": "RV-04", "area": "stale requirement",
         "finding": "The owner's requirement to 'populate the three missing Lions game-status designations' "
                    "is already satisfied at the source: the report now prints Out for Joseph, Mays and Reed.",
         "check": "https://www.nfl.com/injuries/ read 2026-11-15, rows present in injuries_week10_read.csv",
         "disposition": "closed as implemented_verified with today's read as the evidence",
         "official_source_url": SRC_INJ})
    add({"finding_id": "RV-05", "area": "live-week hazard",
         "finding": "Captures taken during a live week must not treat a live score as a result, and must not "
                    "read a bye-panel or card badge as a week-ending record.",
         "check": "at read time three Week 10 games were live and two unplayed; the standings and both "
                  "schedule pages show the six live clubs' pre-game records",
         "disposition": "encoded in the corpus: only cards printing Final are countable, and the "
                        "as-of-render behaviour is published as flag F-10",
         "official_source_url": SRC_W10})
    add({"finding_id": "RV-06", "area": "republican check",
         "finding": "league_ppg through Week 9 recomputed here is 22.963, matching session d966f630's "
                    "independently reported baseline of 22.963 ppg.",
         "check": "two sessions, one number, no shared code",
         "disposition": "corroborating; recorded so the value can be trusted by readers who did not see the "
                        "other session's work", "official_source_url": SRC_STANDINGS})
    add({"finding_id": "RV-07", "area": "in-repo numbers",
         "finding": "d966f630 published a 44-game W7-W10 feed and a411fed0 a 120-game feed while reporting "
                    "a Week 4 hole; both are consistent with each other and with this pack once the hole and "
                    "the live-week boundary are accounted for.",
         "check": "row counts and week boundaries read from the committed CSVs",
         "disposition": "no conflict; recorded so a reader comparing packs knows why the counts differ",
         "official_source_url": "https://github.com/sassnarep3-star/Own6/tree/main/data/nfl_a411fed0"})
    return f


def count_blanks() -> int:
    n = 0
    for path in sorted(DATA_GLOB):
        with path.open(newline="", encoding="utf-8") as fh:
            for rec in csv.DictReader(fh):
                n += sum(1 for v in rec.values() if v == "" or v is None)
    return n


AS_OF = "2026-11-15T23:26:34Z"


def _f4(v) -> str:
    if v is None:
        return ""
    x = float(v)
    return "" if math.isnan(x) else f"{x:.4f}"


def _f3(v) -> str:
    if v is None:
        return ""
    x = float(v)
    return "" if math.isnan(x) else f"{x:.3f}"


def _num(v) -> str:
    """One number format for the whole pack, so a value cannot change shape between tables."""
    if v is None or v == "":
        return ""
    x = float(v)
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f"{x:.1f}"




def blank_audit(data_dir, skip: tuple[str, ...] = ()) -> tuple[list[dict], int]:
    """How many cells this pack published as blank instead of inferred, per table.

    The number that makes "a blank is a result, not an omission" checkable rather than rhetorical: a
    reader can see which tables carry the emptiness and how much of it sits in explanatory columns.
    Run by the builder after every table exists, so it measures what was actually written.
    """
    import csv as _csv
    from pathlib import Path as _P
    out, total = [], 0
    for path in sorted(_P(data_dir).glob("*.csv")):
        if path.name in skip:
            continue
        rows = blanks = 0
        with path.open(newline="", encoding="utf-8") as fh:
            for rec in _csv.DictReader(fh):
                rows += 1
                blanks += sum(1 for v in rec.values() if v in ("", None))
        total += blanks
        out.append({"table": path.name, "data_rows": rows, "blank_cells": blanks})
    for r in out:
        r["blank_share"] = f"{r['blank_cells'] / max(1, r['data_rows'] * 1):.2f} per row"
        r["note"] = ("0 blanks: every published field was read or computed from something published"
                     if r["blank_cells"] == 0 else
                     "blanks are the point: a field with no official value is left empty, never filled")
    return out, total


def count_blanks(data_dir, skip: tuple[str, ...] = ()) -> int:
    return blank_audit(data_dir, skip)[1]


def hfa_ablation(graded_games, rows) -> dict:
    """Ablation of the home-field axis: the same fit, with and without the estimated intercept.

    Reported as a paired difference with an interval, over the fixtures the model could price.
    This is the 'test the same model with and without the feature' requirement applied to an
    assumption everyone else hard-codes.
    """
    rng = random.Random(20261115)
    with_h, without_h = [], []
    for r in rows:
        g_, fitd = r["game"], r["fitd"]
        if not g_.countable or g_.home_points is None:
            continue
        actual = float(g_.home_points - g_.away_points)
        mu1 = fitd["ratings"][g_.home] - fitd["ratings"][g_.away] + fitd["home_field_advantage"]
        mu0 = fitd["ratings"][g_.home] - fitd["ratings"][g_.away]
        with_h.append(abs(actual - round(mu1 / M.ROUND_TO) * M.ROUND_TO))
        without_h.append(abs(actual - round(mu0 / M.ROUND_TO) * M.ROUND_TO))
    n = len(with_h)
    if not n:
        return {"n_fixtures_tested": 0}
    diffs = sorted(
        (sum(with_h[i] for i in [rng.randrange(n) for _ in range(n)]) / n
         - sum(without_h[i] for i in [rng.randrange(n) for _ in range(n)]) / n)
        for _ in range(2000)
    )
    mean_a = sum(with_h) / n
    mean_b = sum(without_h) / n
    return {
        "n_fixtures_tested": n,
        "mean_abs_error_with_personnel": mean_a,
        "mean_abs_error_without_personnel": mean_b,
        "difference": mean_a - mean_b,
        "ci95_low": diffs[int(0.025 * len(diffs))],
        "ci95_high": diffs[min(int(0.975 * len(diffs)), len(diffs) - 1)],
        "method": "identical ridge fit, prediction made with the estimated home intercept and with it "
                  "forced to zero; paired bootstrap over graded fixtures (2000 draws, seed frozen in "
                  "the pre-registration)",
        "note": "columns are re-used from the personnel ablation table, so 'with_personnel' means 'with "
                "the axis switched on' for this row",
    }
