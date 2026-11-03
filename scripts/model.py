#!/usr/bin/env python3
"""Own6 line origination model v0.1 + walk-forward backtest.

Model (pre-registered, no parameters fitted to tonight's market):
  Strength  s_t  = shrunk mean of (team margin adjusted for venue) from PRIOR games only.
                   shrink k=8 toward 0 (league average), initialized before any data.
  HCA       = expanding empirical mean home margin, prior games only, init 2.5 pts.
  sigma     = expanding stdev of game margins, prior games only, init 12.0 pts.
  Pred home margin = HCA + s_home - s_away.
  Win prob  = Phi(pred_margin / sigma).
  Our spread = -pred_margin (home-favorite convention, like market "details").
  Our total  = (PF_home + PA_away)/2 + (PF_away + PA_home)/2,
               PF/PA = shrunk prior scoring means (k=4 toward league avg, init 114.0).

Walk-forward backtest on every 2026-27 game (chronological, prior games only):
  log-loss / Brier vs baselines (coin 0.5; expanding empirical home-win rate),
  sign accuracy, Pearson r(pred margin, actual margin), bootstrap CI (seed=42).

Outputs:
  data/backtest_walkforward.csv
  data/our_lines_2026-11-02.csv  (model lines vs DraftKings for today's slate)
  verification/backtest_metrics.csv
"""
import csv, math, os, random, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUTV = os.path.join(ROOT, "verification")
os.makedirs(OUTV, exist_ok=True)

K_STR = 8.0      # prior strength weight (games)
K_PTS = 4.0      # prior scoring weight (games)
HCA0 = 2.5       # initial home-court estimate (points)
SIG0 = 12.0      # initial margin sigma (points)
PF0 = 114.0      # initial scoring level (points/team/game)
WARMUP = 10      # min league games before a pick is graded

def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def load(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))

games = load("games_results_2026-27.csv")
market = load("market_lines_2026-11-02.csv")
ratings = load("team_ratings_2026-27.csv")
games.sort(key=lambda g: (g["date"], g["game_id"]))

# --- walk-forward state ---
sum_m = {}          # team -> sum of venue-adjusted margin observations
n_m = {}            # team -> count
sum_pf = {}; sum_pa = {}; n_pf = {}; n_pa = {}
home_margins = []
home_wins = 0
rows_bt = []

def strength(t):
    n = n_m.get(t, 0)
    return (sum_m.get(t, 0.0)) / (n + K_STR)   # prior mean 0

def pts_scored(t):
    n = n_pf.get(t, 0)
    return (sum_pf.get(t, PF0 * n if n else 0.0) + K_PTS * PF0) / (n + K_PTS) if True else PF0

def pts_allowed(t):
    n = n_pa.get(t, 0)
    return (sum_pa.get(t, 0.0) + K_PTS * PF0) / (n + N_K(t)) if False else (sum_pa.get(t, 0.0) + K_PTS * PF0) / (n + K_PTS)

def N_K(n):  # unused placeholder kept for clarity
    return K_PTS

HCA = HCA0
SIG = SIG0
home_p_base = 0.5

for i, g in enumerate(games):
    a, h = g["away_team"], g["home_team"]
    as_, hs = int(g["away_score"]), int(g["home_score"])
    hm = hs - as_                      # home margin
    record = i >= WARMUP
    if record:
        s_h, s_a = strength(h), strength(a)
        pred_m = HCA + s_h - s_a
        p = norm_cdf(pred_m / SIG)
        p = min(max(p, 1e-6), 1 - 1e-6)
        exp_home = (pts_scored(h) + pts_allowed(a)) / 2.0
        exp_away = (pts_scored(a) + pts_allowed(h)) / 2.0
        our_total = exp_home + exp_away
        our_spread = -pred_m           # home-favorite convention
        y = 1 if hm > 0 else 0
        ll_model = -(y * math.log(p) + (1 - y) * math.log(1 - p))
        ll_coin = -math.log(0.5)
        pb = min(max(home_p_base, 1e-6), 1 - 1e-6)
        ll_home = -(y * math.log(pb) + (1 - y) * math.log(1 - pb))
        br_model = (p - y) ** 2
        br_coin = (0.5 - y) ** 2
        rows_bt.append(dict(
            game_id=g["game_id"], date=g["date"], away=a, home=h,
            actual_home_margin=hm, predicted_home_margin=round(pred_m, 2),
            model_p_home=round(p, 4), our_total=round(our_total, 1),
            logloss_model=round(ll_model, 5), logloss_coin=round(ll_coin, 5),
            logloss_homebase=round(ll_home, 5),
            brier_model=round(br_model, 5), brier_coin=round(br_coin, 5),
            sign_hit=1 if (pred_m > 0) == (hm > 0) else 0,
            source_url=g["source_url"]))
    # update state AFTER grading (no leakage)
    for t, obs in ((h, hm - HCA), (a, -hm + HCA)):
        sum_m[t] = sum_m.get(t, 0.0) + obs
        n_m[t] = n_m.get(t, 0) + 1
    for t, pf, pa in ((h, hs, as_), (a, as_, hs)):
        sum_pf[t] = sum_pf.get(t, 0.0) + pf
        sum_pa[t] = sum_pa.get(t, 0.0) + pa
        n_pf[t] = n_pf.get(t, 0) + 1
        n_pa[t] = n_pa.get(t, 0) + 1
    home_margins.append(hm)
    home_wins += 1 if hm > 0 else 0
    HCA = sum(home_margins) / len(home_margins) if len(home_margins) >= 5 else HCA0
    if len(home_margins) >= 5:
        SIG = statistics.pstdev(home_margins) if len(home_margins) > 1 else SIG0
        SIG = max(SIG, 8.0)
    home_p_base = home_wins / len(home_margins)

with open(os.path.join(DATA, "backtest_walkforward.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_bt[0].keys()))
    w.writeheader(); w.writerows(rows_bt)

# --- metrics ---
n = len(rows_bt)
ll_m = sum(r["logloss_model"] for r in rows_bt) / n
ll_c = sum(r["logloss_coin"] for r in rows_bt) / n
ll_h = sum(r["logloss_homebase"] for r in rows_bt) / n
br_m = sum(r["brier_model"] for r in rows_bt) / n
br_c = sum(r["brier_coin"] for r in rows_bt) / n
acc = sum(r["sign_hit"] for r in rows_bt) / n
pm = [r["predicted_home_margin"] for r in rows_bt]
am = [r["actual_home_margin"] for r in rows_bt]
r_pma = statistics.correlation(pm, am)

# paired per-game log-loss diff (home baseline - model): positive = model better
diffs = [r["logloss_homebase"] - r["logloss_model"] for r in rows_bt]
mean_d = statistics.mean(diffs)
random.seed(42)
boot = []
for _ in range(10000):
    s = sum(diffs[random.randrange(n)] for _ in range(n)) / n
    boot.append(s)
boot.sort()
lo, hi = boot[250], boot[9750]  # 95% percentile CI
wins_d = sum(1 for d in diffs if d > 0)

metrics = [
    ("games_graded", n, "", "backtest_walkforward.csv"),
    ("logloss_model", round(ll_m, 5), "lower better", "data/backtest_walkforward.csv"),
    ("logloss_coin", round(ll_c, 5), "baseline p=0.5", "data/backtest_walkforward.csv"),
    ("logloss_homebase", round(ll_h, 5), "baseline expanding home-win rate", "data/backtest_walkforward.csv"),
    ("brier_model", round(br_m, 5), "lower better", "data/backtest_walkforward.csv"),
    ("brier_coin", round(br_c, 5), "baseline p=0.5", "data/backtest_walkforward.csv"),
    ("sign_accuracy_model_fav", round(acc, 4), "model favorite straight-up", "data/backtest_walkforward.csv"),
    ("corr_pred_vs_actual_margin", round(r_pma, 4), "Pearson r", "data/backtest_walkforward.csv"),
    ("mean_logloss_diff_homebase_minus_model", round(mean_d, 5), ">0 = model beats home baseline", "data/backtest_walkforward.csv"),
    ("bootstrap95_ci_logloss_diff", f"[{round(lo,5)}, {round(hi,5)}]", "10000 resamples, seed 42", "data/backtest_walkforward.csv"),
    ("games_model_beats_homebase", wins_d, f"of {n}", "data/backtest_walkforward.csv"),
    ("gate_logloss_beats_homebase", "PASS" if lo > 0 else "FAIL", "95% CI strictly > 0 required", "verification/verification_report.csv"),
    ("gate_sign_accuracy_vs_coin", "PASS" if acc > 0.55 else "NOT MET", "pre-registered threshold 0.55", "verification/verification_report.csv"),
    ("final_HCA_est", round(HCA, 2), "expanding empirical, points", "data/backtest_walkforward.csv"),
    ("totals_MAE_our_model", round(statistics.mean(
        abs(r["our_total"] - (int(next(g for g in games if g["game_id"] == r["game_id"])["home_score"])
            + int(next(g for g in games if g["game_id"] == r["game_id"])["away_score"])))
        for r in rows_bt), 3), "points, vs actual totals", "data/backtest_walkforward.csv"),
    ("totals_bias_our_model", round(statistics.mean(
        r["our_total"] - (int(next(g for g in games if g["game_id"] == r["game_id"])["home_score"])
            + int(next(g for g in games if g["game_id"] == r["game_id"])["away_score"]))
        for r in rows_bt), 3), "points, model minus actual (>0 = over-predicts)", "data/backtest_walkforward.csv"),
    ("final_sigma_est", round(SIG, 2), "expanding empirical, points", "data/backtest_walkforward.csv"),
    ("home_win_rate_2026_27", round(home_wins / len(home_margins), 4), f"{home_wins}-{len(home_margins)-home_wins}", "data/games_results_2026-27.csv"),
]
with open(os.path.join(OUTV, "backtest_metrics.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value", "note", "source"])
    w.writerows(metrics)

# --- tonight's lines (ratings from ALL games so far; state above ended after last game) ---
by_abbr = {r["team_abbr"]: r for r in ratings}
# recompute strength state after final game already equals full-season state
mkt_rows = []
for m in market:
    a, h = m["away_team"], m["home_team"]
    ra, rh = by_abbr.get(a), by_abbr.get(h)
    s_h, s_a = strength(h), strength(a)
    pred_m = HCA + s_h - s_a
    p = norm_cdf(pred_m / SIG)
    exp_home = (pts_scored(h) + pts_allowed(a)) / 2.0
    exp_away = (pts_scored(a) + pts_allowed(h)) / 2.0
    our_total = exp_home + exp_away
    our_spread = -pred_m
    # market implied (de-vig, proportional): from american ML
    def imp(ml):
        # American odds -> implied probability. (Fixed by session f58e0178: the earlier
        # version returned 100/ml and -ml/100, i.e. decimal-style odds ratios, not probabilities.)
        return 100.0 / (ml + 100.0) if ml > 0 else -ml / (-ml + 100.0)
    fav_ml = int(m["fav_ml_current"]); dog_ml = int(m["dog_ml_current"])
    pf, pd = imp(fav_ml), imp(dog_ml)
    tot = pf + pd
    fav_fair = pf / tot
    fav_implied = fav_fair
    our_p_fav = p if pred_m > 0 else 1 - p   # prob that model's favored side wins
    # model favourite = home if pred_m>0 else away; market favourite from m['favorite']
    model_fav = h if pred_m > 0 else a
    market_fav = m["favorite"]
    # de-vigged market probability OF OUR favourite: same side if favs agree, else complement
    our_fav_fair = fav_fair if model_fav == market_fav else (1.0 - fav_fair)
    edge = our_p_fav - our_fav_fair
    mkt_rows.append(dict(
        event_id=m["event_id"], date=m["date"], away=a, home=h,
        market_favorite=market_fav, market_spread=m["market_spread"],
        market_total=m["market_total"], fav_ml_current=fav_ml, dog_ml_current=dog_ml,
        market_fav_fair_prob=round(fav_fair, 4),
        model_favorite=model_fav, our_spread=round(our_spread, 1),
        our_total=round(our_total, 1), model_p_model_fav=round(our_p_fav, 4),
        our_fav_fair_prob=round(our_fav_fair, 4),
        model_edge_vs_market_fair=round(edge, 4),
        model_vs_market_fav=("same" if model_fav == market_fav else "different"),
        total_diff_model_minus_market=round(our_total - float(m["market_total"]), 1),
        source_market=m["source_url"],
        source_model="Own6 model v0.1 (scripts/model.py)"))

with open(os.path.join(DATA, "our_lines_2026-11-02.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(mkt_rows[0].keys()))
    w.writeheader(); w.writerows(mkt_rows)

print(f"backtest games={n} logloss model={ll_m:.4f} coin={ll_c:.4f} homebase={ll_h:.4f}")
print(f"sign_acc={acc:.3f} corr={r_pma:.3f} mean_diff={mean_d:.4f} CI=[{lo:.4f},{hi:.4f}]")
print(f"HCA={HCA:.2f} sigma={SIG:.2f} home_wr={home_wins/len(home_margins):.3f}")
print(f"our lines rows={len(mkt_rows)}")
