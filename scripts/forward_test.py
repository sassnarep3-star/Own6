#!/usr/bin/env python3
"""Forward (out-of-sample) test of the Own6 lines published for the 2026-11-02 slate.

Inputs (all committed before the games were played; see audit/INTEGRATION_AUDIT.md for timestamps):
  data/our_lines_2026-11-02.csv   Own6 model v0.1 lines (home spread convention: negative = home favoured)
  data/market_lines_2026-11-02.csv  DraftKings lines via ESPN feed (SECONDARY source, flagged)
  data/results_2026-11-02.csv     Final scores read from nba.com on 2026-11-03 (official)

Everything here is descriptive. n=15 cannot validate or invalidate a strategy; no gate is passed or failed.
Stdlib only, deterministic (bootstrap seed 42).
"""
import csv, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda n: os.path.join(ROOT, "data", n)
ABBR = {"WSH": "WAS", "NY": "NYK", "NO": "NOP", "SA": "SAS", "GS": "GSW"}  # ESPN -> NBA.com
norm = lambda t: ABBR.get(t, t)

def rd(n):
    with open(D(n), newline="") as f:
        return list(csv.DictReader(f))

def imp(ml):  # American odds -> implied probability
    return 100.0 / (ml + 100.0) if ml > 0 else -ml / (-ml + 100.0)

def ll(p, y):
    p = min(max(p, 1e-9), 1 - 1e-9)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))

def binom_two_sided(k, n, p=0.5):
    pm = [math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(x for x in pm if x <= pm[k] + 1e-12))

def main():
    ours = {(norm(r["away"]), norm(r["home"])): r for r in rd("our_lines_2026-11-02.csv")}
    mkt = {(norm(r["away_team"]), norm(r["home_team"])): r for r in rd("market_lines_2026-11-02.csv")}
    res = rd("results_2026-11-02.csv")
    out = []
    for g in res:
        k = (g["away_team"], g["home_team"])
        o, m = ours[k], mkt[k]
        hs, as_ = int(g["home_score"]), int(g["away_score"])
        margin, total = hs - as_, hs + as_
        # market home line: favourite's spread is negative
        mh = float(m["market_spread"]) if norm(m["favorite"]) == k[1] else -float(m["market_spread"])
        oh = float(o["our_spread"])
        fav_ml, dog_ml = int(m["fav_ml_current"]), int(m["dog_ml_current"])
        pf, pd = imp(fav_ml), imp(dog_ml)
        fav_fair = pf / (pf + pd)
        p_home_mkt = fav_fair if norm(m["favorite"]) == k[1] else 1 - fav_fair
        mp = float(o["model_p_model_fav"])
        p_home_mod = mp if norm(o["model_favorite"]) == k[1] else 1 - mp
        y = 1 if margin > 0 else 0
        lean = "home" if -oh > -mh else ("away" if -oh < -mh else "none")
        cover = margin + mh  # >0 home covers market line
        ats = "push" if cover == 0 else ("home" if cover > 0 else "away")
        lean_res = "n/a" if lean == "none" else ("push" if ats == "push" else ("win" if ats == lean else "loss"))
        mt, ot = float(m["market_total"]), float(o["our_total"])
        tl = "over" if ot > mt else ("under" if ot < mt else "none")
        tres = "push" if total == mt else ("over" if total > mt else "under")
        tlean_res = "n/a" if tl == "none" else ("push" if tres == "push" else ("win" if tres == tl else "loss"))
        out.append(dict(
            game_id=g["game_id"], away=k[0], home=k[1], home_margin=margin, total=total,
            market_home_line=mh, own6_home_line=oh,
            market_pred_margin=-mh, own6_pred_margin=-oh,
            err_market=round(margin + mh, 1), err_own6=round(margin + oh, 1),
            p_home_market_devig=round(p_home_mkt, 4), p_home_own6=round(p_home_mod, 4), home_won=y,
            logloss_market=round(ll(p_home_mkt, y), 5), logloss_own6=round(ll(p_home_mod, y), 5),
            brier_market=round((p_home_mkt - y) ** 2, 5), brier_own6=round((p_home_mod - y) ** 2, 5),
            spread_lean=lean, ats_winner=ats, spread_lean_result=lean_res,
            market_total=mt, own6_total=ot, total_err_market=round(total - mt, 1), total_err_own6=round(total - ot, 1),
            total_lean=tl, total_result=tres, total_lean_result=tlean_res,
            result_source=g["source_url"], line_source=m["source_url"]))
    fields = list(out[0].keys())
    with open(D("forward_test_2026-11-02.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(out)

    n = len(out)
    mean = lambda xs: sum(xs) / len(xs)
    S = {}
    S["n_games"] = n
    S["margin_MAE_market"] = mean([abs(r["err_market"]) for r in out])
    S["margin_MAE_own6"] = mean([abs(r["err_own6"]) for r in out])
    S["margin_bias_market"] = mean([r["err_market"] for r in out])
    S["margin_bias_own6"] = mean([r["err_own6"] for r in out])
    S["total_MAE_market"] = mean([abs(r["total_err_market"]) for r in out])
    S["total_MAE_own6"] = mean([abs(r["total_err_own6"]) for r in out])
    S["logloss_market"] = mean([r["logloss_market"] for r in out])
    S["logloss_own6"] = mean([r["logloss_own6"] for r in out])
    S["logloss_coin"] = math.log(2)
    S["brier_market"] = mean([r["brier_market"] for r in out])
    S["brier_own6"] = mean([r["brier_own6"] for r in out])
    S["su_correct_market"] = sum(1 for r in out if (r["p_home_market_devig"] > .5) == (r["home_won"] == 1))
    S["su_correct_own6"] = sum(1 for r in out if (r["p_home_own6"] > .5) == (r["home_won"] == 1))
    # paired bootstrap, per-game logloss(market) - logloss(own6): >0 means own6 better
    d = [r["logloss_market"] - r["logloss_own6"] for r in out]
    rng = random.Random(42)
    bs = sorted(mean([d[rng.randrange(n)] for _ in range(n)]) for _ in range(10000))
    S["logloss_diff_market_minus_own6"] = mean(d)
    S["logloss_diff_ci95_lo"], S["logloss_diff_ci95_hi"] = bs[249], bs[9749]
    dm = [abs(r["err_market"]) - abs(r["err_own6"]) for r in out]
    bs = sorted(mean([dm[rng.randrange(n)] for _ in range(n)]) for _ in range(10000))
    S["abs_margin_err_diff_market_minus_own6"] = mean(dm)
    S["abs_margin_err_diff_ci95_lo"], S["abs_margin_err_diff_ci95_hi"] = bs[249], bs[9749]
    for lab, key in (("spread", "spread_lean_result"), ("total", "total_lean_result")):
        w = sum(1 for r in out if r[key] == "win"); l = sum(1 for r in out if r[key] == "loss")
        S[f"{lab}_lean_W"], S[f"{lab}_lean_L"] = w, l
        S[f"{lab}_lean_pushes"] = sum(1 for r in out if r[key] == "push")
        S[f"{lab}_lean_none"] = sum(1 for r in out if r[key] == "n/a")
        S[f"{lab}_lean_binom_p_two_sided_vs_50pct"] = binom_two_sided(w, w + l) if w + l else ""
    rows = [("metric", "value")] + [(k, (round(v, 5) if isinstance(v, float) else v)) for k, v in S.items()]
    with open(D("forward_test_summary_2026-11-02.csv"), "w", newline="") as f:
        csv.writer(f).writerows(rows)
    for k, v in rows[1:]: print(f"{k:45s} {v}")

if __name__ == "__main__":
    main()
