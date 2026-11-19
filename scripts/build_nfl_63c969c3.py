#!/usr/bin/env python3
"""Deterministically render the session 63c969c3 register subpages."""
import csv, html, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]; DATA=ROOT/'data/nfl_63c969c3'; DOC=ROOT/'docs/nfl-63c969c3'
PAGES={'requirements':'requirements.csv','captures':'reverification.csv','flags':'flagged.csv','suggestions':'suggestions.csv','questions':'questions.csv','sources':'sources.csv','strategy':'originated_lines.csv','availability':'availability_graph.csv'}
def render(title,rows):
 if not rows:return '<p>Empty by design. No values are published without verified evidence.</p>'
 headers=list(rows[0]); out=['<table><thead><tr>'+''.join('<th>'+html.escape(x.replace('_',' ').title())+'</th>' for x in headers)+'</tr></thead><tbody>']
 for row in rows:
  out.append('<tr>'+''.join('<td>'+ (('<a href="'+html.escape(v,quote=True)+'">official/source link</a>') if v.startswith('https://') else html.escape(v))+'</td>' for v in row.values())+'</tr>')
 return ''.join(out)+'</tbody></table>'
def main():
 DOC.mkdir(parents=True,exist_ok=True)
 for page,file in PAGES.items():
  with open(DATA/file,newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
  body=render(page,rows)
  (DOC/(page+'.html')).write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+page+' · NFL decision readiness</title><style>body{font:16px/1.5 system-ui;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#182437}table{border-collapse:collapse;width:100%;display:block;overflow:auto}td,th{border-bottom:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top}th{background:#edf3f9}a{color:#075da8}</style><a href="index.html">← Dashboard</a><h1>'+page.replace('_',' ').title()+'</h1>'+body,encoding='utf-8')
if __name__=='__main__':main()
