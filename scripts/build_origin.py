#!/usr/bin/env python3
"""Build docs/origin/ from data/origin_strategies.csv. Every row source-linked; blank=unverified."""
import csv, html, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "origin"
CSS = "body{font-family:system-ui;margin:2rem;max-width:1100px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:.4rem;font-size:.9rem}nav a{margin-right:1rem}.blank{color:#888}"
NAV = '<nav><a href="index.html">Overview</a><a href="strategies.html">Strategies</a><a href="lines.html">Own Lines</a><a href="correlations.html">Correlations</a><a href="leaderboard.html">Leaderboard</a><a href="validation.html">Validation</a><a href="flagged.html">Flagged</a><a href="sources.html">Sources</a></nav>'
def esc(x): return html.escape(str(x or ""))
def cell(x): return f'<td class="blank">— unverified</td>' if not str(x or "").strip() else f'<td>{esc(x)}</td>'
def page(title, body):
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title><style>{CSS}</style></head><body>{NAV}<h1>{esc(title)}</h1>{body}<p>Research only. No betting advice. Blank = unverified.</p></body></html>'
def src(u): return f'<td><a href="{esc(u)}">official source</a></td>'
def rows():
    with open(ROOT/"data/origin_strategies.csv", newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def table(headers, body_rows): return "<table><thead><tr>"+"".join(f"<th>{esc(h)}</th>" for h in headers)+"</tr></thead><tbody>"+body_rows+"</tbody></table>"
def build():
    OUT.mkdir(parents=True, exist_ok=True); R = rows()
    strat = "".join(f"<tr><td>{esc(r['id'])}</td><td>{esc(r['family'])}</td><td>{esc(r['market'])}</td><td>{esc(r['hypothesis'])}</td><td>{esc(r['signal_rule'])}</td>{cell(r['roi'])}<td>{esc(r['status'])}</td>{src(r['source_url'])}</tr>" for r in R)
    (OUT/"strategies.html").write_text(page("Strategies — singles, parlays, prop combos", table(["ID","Family","Market","Hypothesis (not proven)","Signal rule","ROI","Status","Source"], strat)), encoding="utf-8")
    lines = "".join(f"<tr><td>{esc(r['id'])}</td><td>{esc(r['market'])}</td><td>{esc(r['own_line_method'])}</td>{cell('')}{cell('')}{src(r['source_url'])}</tr>" for r in R)
    (OUT/"lines.html").write_text(page("Originate your own lines", "<p>Method only. Own-line and market-line values are blank until an authorized timestamped feed exists.</p>"+table(["ID","Market","Own-line method","Own line","Market line","Source"], lines)), encoding="utf-8")
    corr = "".join(f"<tr><td>{esc(r['id'])}</td><td>{esc(r['correlation_pair'])}</td>{cell(r['corr_value'])}{cell(r['n'])}<td>Training-only paired residuals, slate-clustered CI, joint sample required</td>{src(r['source_url'])}</tr>" for r in R)
    (OUT/"correlations.html").write_text(page("Correlations — blank until measured", table(["ID","Pair","ρ","n","Method","Source"], corr)), encoding="utf-8")
    gates = [
        ("Rights & provenance","Authorized feed only; NBA Statistics gambling use restricted","https://www.nba.com/termsofuse"),
        ("Chronology","Walk-forward train/validation/holdout; no look-ahead","https://scikit-learn.org/stable/modules/cross_validation.html"),
        ("Sample size","Frozen minimums (n>=200, >=60 slates in repo config)","","https://github.com/sassnarep3-star/Own6/blob/main/data/empirical/report.json"),
        ("Calibration","Brier / log-loss vs de-vigged market","https://scikit-learn.org/stable/modules/calibration.html"),
        ("CLV","De-vigged same-line close; moved lines blank","https://scikit-learn.org/stable/modules/calibration.html"),
        ("Multiplicity","Bonferroni over whole frozen family","https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html"),
        ("Clustered ROI","Slate-clustered bootstrap lower bound > 0","https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html"),
        ("Correlation","Training-only residuals; joint sample for combos","https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"),
    ]
    # fix 3-tuple/4-tuple mix
    grows=""
    for g in gates:
        name,rule,url = g[0],g[1],g[-1]
        grows+=f"<tr><td>{esc(name)}</td><td>{esc(rule)}</td><td>open — not run</td>{src(url)}</tr>"
    (OUT/"validation.html").write_text(page("Validation gates — luck control", table(["Gate","Rule","Result","Source"], grows)), encoding="utf-8")
    (OUT/"leaderboard.html").write_text(page("Leaderboard — empty by design", "<p>No strategy has passed all gates. Ranking metric (when qualifiers exist): lower bound of slate-clustered holdout ROI. Rewards: non-monetary research priority only.</p>"+table(["Rank","Strategy","ROI lower bound","Source"], "<tr><td>—</td><td>— no qualifiers</td>"+cell("")+src("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html")+"</tr>")), encoding="utf-8")
    flags=[("F-O1","No authorized odds/closing feed; all market values blank","https://www.nba.com/stats/help/faq"),("F-O2","NBA Statistics gambling-use rights unresolved (Terms §9)","https://www.nba.com/termsofuse"),("F-O3","All correlations blank; independence not assumed","https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"),("F-O4","No qualified strategy; leaderboard empty; luck not eliminated","https://scikit-learn.org/stable/modules/cross_validation.html")]
    frows="".join(f"<tr><td>{a}</td><td>{b}</td>{cell('')}{src(u)}</tr>" for a,b,u in flags)
    (OUT/"flagged.html").write_text(page("Flagged for Review", table(["ID","Item","Confirmed value","Source"], frows)), encoding="utf-8")
    srows="".join(f"<tr><td>{esc(r['source_url'])}</td><td>Strategy {esc(r['id'])} method basis — does not verify any value</td>{src(r['source_url'])}</tr>" for r in R)
    (OUT/"sources.html").write_text(page("Sources", table(["Official URL","Use","Link"], srows)), encoding="utf-8")
    (OUT/"index.html").write_text(page("Own6 — Originate Your Own NBA Lines", "<p>Executive summary: originate spread/total/win-probability and prop lines from efficiency definitions, test singles, parlays and prop combos as a leaderboard, pass every validation gate, measure correlations from training residuals only, and rank by worst-plausible skill — not best luck. Currently: 0 qualified strategies, 0 authorized observations, all empirical values blank.</p>"+table(["Area","Status","Detail","Source"], f"<tr><td>Strategies O1–O10</td><td>unverified</td><td>See Strategies page</td>{src('https://www.nba.com/stats/help/glossary')}</tr>")), encoding="utf-8")
    print(f"built {len(list(OUT.glob('*.html')))} pages")
if __name__=="__main__":
    if "--check" in sys.argv: build()
    else: build()
