"""Player props: shrunk projection. projection = minutes_proj * per_min_rate, rate shrunk toward season mean.
Minutes and rates must come from official NBA stats / official injury report status — never guessed here."""
import math
def shrink(recent_rate, season_rate, recent_n, k=10.0):
    """Empirical-Bayes-style shrinkage weight w=n/(n+k); k must be chosen by walk-forward validation, not assumed optimal."""
    w=recent_n/(recent_n+k); return w*recent_rate+(1-w)*season_rate
def project(minutes_proj, per_min_rate): return minutes_proj*per_min_rate
def prob_over(projection, sd, line):
    """Normal approx (documented approximation; validate distribution on your residuals before staking)."""
    if sd<=0: return 0.5
    z=(line+0.5-projection)/sd  # continuity correction for counting stats
    return 1-0.5*(1+math.erf(z/math.sqrt(2)))
def residual_sd(residuals):
    n=len(residuals); m=sum(residuals)/n
    return math.sqrt(sum((x-m)**2 for x in residuals)/(n-1)) if n>1 else float("nan")
