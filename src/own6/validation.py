"""Validation gates & luck removal. A strategy is 'skill' only if it beats breakeven AFTER: walk-forward (no lookahead),
calibration check, closing-line value, bootstrap CI, and multiple-testing correction across ALL strategies tried."""
import math, random
def breakeven(price=-110): return 110/210 if price<0 else 100/(price+100)
def brier(probs,outcomes): return sum((p-o)**2 for p,o in zip(probs,outcomes))/len(probs)
def log_loss(probs,outcomes,eps=1e-12): return -sum(o*math.log(max(p,eps))+(1-o)*math.log(max(1-p,eps)) for p,o in zip(probs,outcomes))/len(probs)
def binomial_p(wins,n,p0):
    """Exact one-sided P(X>=wins) under luck-only p0 (math.comb, no external deps)."""
    return sum(math.comb(n,k)*p0**k*(1-p0)**(n-k) for k in range(wins,n+1))
def bootstrap_roi_ci(returns,iters=5000,seed=6,alpha=0.05):
    rng=random.Random(seed); n=len(returns); means=[]
    for _ in range(iters): means.append(sum(returns[rng.randrange(n)] for _ in range(n))/n)
    means.sort(); return means[int(alpha/2*iters)], means[int((1-alpha/2)*iters)]
def clv_stats(clvs): # closing line value per bet (model prob at close minus price taken, or line diff)
    n=len(clvs); m=sum(clvs)/n; sd=math.sqrt(sum((x-m)**2 for x in clvs)/(n-1)) if n>1 else 0
    return {"n":n,"mean_clv":m,"t_stat": m/(sd/math.sqrt(n)) if sd else 0.0}
def bonferroni(pvals,alpha=0.05): return [p < alpha/max(len(pvals),1) for p in pvals]
GATES=[
 ("G1 Walk-forward only","No parameter fit on data after bet date; expanding/rolling origin."),
 ("G2 Sample size","n >= 200 settled bets per strategy (project threshold; raise for props/parlays)."),
 ("G3 Calibration","Brier <= market-baseline Brier AND log-loss <= market on same games."),
 ("G4 CLV","Mean CLV > 0 with t >= 2 (you beat the closing market, not just outcomes)."),
 ("G5 Luck test","Binomial p vs breakeven < Bonferroni-adjusted alpha across all strategies tried."),
 ("G6 Bootstrap","95% bootstrap ROI CI lower bound > 0."),
 ("G7 Correlation honesty","Parlay joint prob from estimated correlations (n reported), never independence by default."),
 ("G8 Ledger integrity","Every bet logged pre-game with timestamp, price, model prob; no deletions."),
]
def evaluate(n,brier_model,brier_market,clv_t,binom_p,n_strategies_tried,roi_ci_low,walk_forward=True):
    checks={"G1":walk_forward,"G2":n>=200,"G3":brier_model<=brier_market,"G4":clv_t>=2,"G5":binom_p<0.05/max(n_strategies_tried,1),"G6":roi_ci_low>0}
    checks["ALL"]=all(checks.values()); return checks
