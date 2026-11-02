"""Game lines from official NBA advanced stats (definitions: NBA Stats Glossary, nba.com/stats/help/glossary).
PACE = possessions/48min; OffRtg = pts/100 poss; DefRtg = pts allowed/100 poss. Formulas below use only those definitions.
Home-court advantage and margin SD are NOT hard-coded from memory: fit them from your own game log (fit_from_games)."""
import math
from dataclasses import dataclass

@dataclass
class Team: name:str; pace:float; off_rtg:float; def_rtg:float  # per NBA glossary definitions

def expected_points(home:Team, away:Team, league_off_rtg:float, home_adv_pts:float=0.0):
    """Multiplicative matchup: exp_pace=(Ph+Pa)/2; exp_pts = pace * (OffRtg_team/100)*(DefRtg_opp/100)/(League/100)."""
    pace=(home.pace+away.pace)/2
    h=pace*(home.off_rtg/100)*(away.def_rtg/100)/(league_off_rtg/100)
    a=pace*(away.off_rtg/100)*(home.def_rtg/100)/(league_off_rtg/100)
    return h+home_adv_pts/2, a-home_adv_pts/2, pace

def fair_lines(home,away,league_off_rtg,home_adv_pts,margin_sd):
    h,a,pace=expected_points(home,away,league_off_rtg,home_adv_pts)
    margin=h-a; total=h+a
    # Normal margin model; Phi via erf. margin_sd must be fitted (fit_from_games), never assumed.
    win_prob=0.5*(1+math.erf((margin/margin_sd)/math.sqrt(2))) if margin_sd>0 else 0.5
    return {"exp_home":h,"exp_away":a,"pace":pace,"fair_spread_home":-margin,"fair_total":total,"home_win_prob":win_prob}

def fit_from_games(rows):
    """rows: dicts home_margin, model_margin (pre-game). Returns (home_adv residual mean, margin SD, n). Pure stdlib OLS-free moment fit."""
    res=[r["home_margin"]-r["model_margin"] for r in rows]
    n=len(res); mean=sum(res)/n
    sd=math.sqrt(sum((x-mean)**2 for x in res)/(n-1)) if n>1 else float("nan")
    return {"home_adv_residual":mean,"margin_sd":sd,"n":n}

def american_to_prob(odds): return 100/(odds+100) if odds>0 else -odds/(-odds+100)
def prob_to_american(p):
    return round(-100*p/(1-p)) if p>=0.5 else round(100*(1-p)/p)
def edge(model_p, odds): return model_p - american_to_prob(odds)  # vs implied (vig-included; de-vig with both sides for real use)
def devig(p_home_raw,p_away_raw):
    s=p_home_raw+p_away_raw; return p_home_raw/s, p_away_raw/s
