"""Leaderboard = reward SKILL, not luck. Score uses the LOWER confidence bound, so small-sample heaters cannot win."""
import math
def skill_score(returns, mean_clv, brier_edge, min_n=200):
    n=len(returns)
    if n<min_n: return {"eligible":False,"n":n,"score":None,"reason":f"n={n} < {min_n}"}
    m=sum(returns)/n; sd=math.sqrt(sum((x-m)**2 for x in returns)/(n-1))
    lcb=m-1.96*sd/math.sqrt(n)  # lower confidence bound of ROI
    score=100*lcb + 10*mean_clv + 10*brier_edge  # weights are project policy, disclosed, tunable only pre-season
    return {"eligible":True,"n":n,"roi":m,"roi_lcb":lcb,"score":score}
