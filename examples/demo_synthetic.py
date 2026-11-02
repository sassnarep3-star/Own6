"""DEMO ONLY — synthetic numbers invented for pipeline testing. NOT NBA data, NOT a betting signal."""
import sys; sys.path.insert(0,"src")
from own6 import lines
h=lines.Team("SYNTH_HOME",101.0,114.0,108.0); a=lines.Team("SYNTH_AWAY",99.0,110.0,112.0)
print(lines.fair_lines(h,a,league_off_rtg=112.0,home_adv_pts=0.0,margin_sd=13.0))
