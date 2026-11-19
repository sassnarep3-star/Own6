#!/usr/bin/env python3
"""Integrity checks for the 63c969c3 evidence pack."""
import csv,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[1];D=R/'data/nfl_63c969c3'; errors=[]
def read(f):
 with open(D/f,newline='',encoding='utf8') as h:return list(csv.DictReader(h))
for f in ['standings_2026_11_19c.csv','injuries_reg11_c.csv','week11_slate_c.csv']:
 rows=read(f)
 for i,r in enumerate(rows,2):
  if not any(v.startswith('https://www.nfl.com/') for v in r.values()):errors.append(f'{f}:{i}: missing official source URL')
assertions=[('standings rows',len(read('standings_2026_11_19c.csv')),32),('Week 11 games',len(read('week11_slate_c.csv')),13),('Week 11 injury rows',len(read('injuries_reg11_c.csv')),255)]
for name,got,want in assertions:
 if got!=want: errors.append(f'{name}: got {got}, expected {want}')
for f in ['originated_lines.csv','price_snapshots.csv','correlations.csv','leaderboard.csv','per_team.csv','availability_graph.csv']:
 if len(read(f)):errors.append(f'{f}: should remain empty until verified inputs exist')
for f in ['requirements.html','captures.html','flags.html','suggestions.html','questions.html','sources.html','strategy.html','availability.html']:
 if not (R/'docs/nfl-63c969c3'/f).exists():errors.append(f'missing page {f}')
if errors: print('\n'.join(errors));sys.exit(1)
print('PASS: source links, 32 standings, 13 Week 11 games, 255 injury rows, empty unverified modeling registers, pages present')
