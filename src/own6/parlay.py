"""Parlay correlation: Gaussian-copula Monte Carlo. Independence is a special case (rho=0) — never default to it silently.
Correlations must be ESTIMATED from paired historical residuals (pearson below), with n reported."""
import math, random
def pearson(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den=math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys))
    return num/den if den else 0.0
def _norm_cdf(z): return 0.5*(1+math.erf(z/math.sqrt(2)))
def joint_prob(marginals, corr, sims=20000, seed=6):
    """marginals: list of leg probs; corr: matrix. Cholesky of corr; seeded => reproducible."""
    k=len(marginals); rng=random.Random(seed)
    # Cholesky
    L=[[0.0]*k for _ in range(k)]
    for i in range(k):
        for j in range(i+1):
            s=sum(L[i][t]*L[j][t] for t in range(j)); L[i][j]=math.sqrt(max(corr[i][i]-s,0)) if i==j else (corr[i][j]-s)/L[j][j]
    thresholds=[_norm_inv(p) for p in marginals]; hits=0
    for _ in range(sims):
        z=[rng.gauss(0,1) for _ in range(k)]
        x=[sum(L[i][t]*z[t] for t in range(i+1)) for i in range(k)]
        if all(x[i]<=thresholds[i] for i in range(k)): hits+=1
    return hits/sims
def _norm_inv(p): # Acklam approximation
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285984469534e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    plow=0.02425
    if p<plow: q=math.sqrt(-2*math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>1-plow: q=math.sqrt(-2*math.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; r=q*q; return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
def independent_prob(marginals):
    p=1.0
    for m in marginals: p*=m
    return p
