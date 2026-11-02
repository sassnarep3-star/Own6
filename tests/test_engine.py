import sys; sys.path.insert(0,"src")
from own6 import lines, props, parlay, validation
def test_lines_sum():
    h=lines.Team("H",100,115,105); a=lines.Team("A",100,110,110)
    r=lines.fair_lines(h,a,112,0,13)
    assert abs((r["exp_home"]+r["exp_away"])-r["fair_total"])<1e-9 and 0<r["home_win_prob"]<1
def test_devig_sums1():
    x,y=lines.devig(0.55,0.52); assert abs(x+y-1)<1e-9
def test_corr_parlay():
    ind=parlay.independent_prob([0.6,0.6]); pos=parlay.joint_prob([0.6,0.6],[[1,0.5],[0.5,1]],sims=8000)
    assert pos>ind  # positive correlation raises joint prob of both hitting
def test_luck():
    assert validation.binomial_p(60,100,0.5)<0.05
    assert validation.evaluate(10,0.2,0.25,3,0.001,1,0.1)["ALL"] is False  # fails sample gate
def test_shrink():
    assert 0<props.shrink(1.2,1.0,5)<1.2
