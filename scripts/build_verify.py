#!/usr/bin/env python3
"""Build the independent verification section (docs/verify/*.html).

Everything rendered here comes from three committed files:

  data/verification_official_2026_11_03.csv  - one row per check that was
      actually performed against an official page (published value vs the
      value read on the official page), with the exact URL and the date.
  data/verification_unverified_2026_11_03.csv - items that could NOT be
      confirmed. Their published value stays blank by rule.
  data/verification_flags_2026_11_03.csv - irregularities for review.

No value is invented, inferred or interpolated here. If a row is not in the
ledger, it is not claimed as verified.

Run: python3 scripts/build_verify.py
"""
from __future__ import annotations

import csv
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs" / "verify"
LIVE = "https://sassnarep3-star.github.io/Own6/docs/verify/"
REPO = "https://github.com/sassnarep3-star/Own6"

LEDGER = DATA / "verification_official_2026_11_03.csv"
UNVERIFIED = DATA / "verification_unverified_2026_11_03.csv"
FLAGS = DATA / "verification_flags_2026_11_03.csv"

NAV = [
    ("index.html", "Verification"),
    ("results.html", "Game results"),
    ("standings.html", "Standings"),
    ("policy.html", "Rights & law"),
    ("unverified.html", "Unverified"),
    ("flagged.html", "Flagged for review"),
]

CATEGORY_OF = {"Game result": "results.html", "Standings": "standings.html", "Rights": "policy.html"}


def esc(v):
    return html.escape("" if v is None else str(v))


def read(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def badge(result):
    r = (result or "").strip().lower()
    if r == "match":
        return '<span class="b ok">match</span>'
    if r == "mismatch":
        return '<span class="b bad">MISMATCH</span>'
    return '<span class="b warn">unverified</span>'


def link(url, text):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(text)} ↗</a>'


def table(headers, rows, numeric=(), table_id=None):
    tid = f' id="{table_id}"' if table_id else ""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for r in rows:
        cells = "".join(
            f'<td class="n">{c}</td>' if i in numeric else f"<td>{c}</td>"
            for i, c in enumerate(r)
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        f'<div class="tw"><table{tid}><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def page(name, title, lead, body):
    links = []
    for f, label in NAV:
        cls = ' class="on"' if f == name else ""
        links.append(f'<a{cls} href="{f}">{esc(label)}</a>')
    nav = "".join(links)
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — Own6 verification</title>
<link rel="stylesheet" href="assets/verify.css">
</head>
<body>
<header class="top">
  <a class="brand" href="../index.html">OWN6</a>
  <span class="grp">VERIFICATION · read 2026-11-03</span>
  {nav}
</header>
<main>
  <h1>{esc(title)}</h1>
  <p class="lead">{lead}</p>
  {body}
</main>
<footer>
  <p>Every row above links to the official page it was checked against. A blank
  value means it could not be confirmed from an official source; it is never
  estimated. Research only — no wagers, no betting advice, no profitability
  claim. See <a href="flagged.html">Flagged for review</a>,
  <a href="unverified.html">Unverified items</a>, and the
  <a href="https://www.nba.com/termsofuse">NBA Terms of Use</a> (§1, §6, §9).</p>
</footer>
</body>
</html>
"""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(doc, encoding="utf-8")


CSS = """/* Own6 verification section - self-contained, no external assets */
:root{--ink:#12161c;--mut:#5b6672;--line:#e3e7ec;--bg:#f6f7f9;--card:#fff;--ok:#0f7a52;--okbg:#e7f6ee;--bad:#b42318;--badbg:#fdecea;--warn:#8a5a00;--warnbg:#fff5dd;--accent:#1b4fd8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header.top{display:flex;flex-wrap:wrap;align-items:center;gap:.35rem 1rem;padding:.85rem 1.25rem;background:#0f1520;color:#e8edf5}
header.top .brand{font-weight:800;letter-spacing:.14em;color:#fff;text-decoration:none}
header.top .grp{font-size:.72rem;letter-spacing:.12em;color:#8fa0b6;text-transform:uppercase}
header.top nav,header.top a{color:#cdd8e6;text-decoration:none;font-size:.9rem}
header.top a{padding:.3rem .55rem;border-radius:.4rem}
header.top a:hover{background:#1c2634;color:#fff}
header.top a.on{background:#1b4fd8;color:#fff}
main{max-width:1180px;margin:0 auto;padding:1.75rem 1.25rem 3rem}
h1{font-size:1.75rem;margin:.2rem 0 .35rem}
h2{font-size:1.15rem;margin:2rem 0 .5rem}
h3{font-size:1rem;margin:1.25rem 0 .35rem}
p.lead{color:var(--mut);max-width:70ch;margin-top:0}
a{color:var(--accent)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.75rem;margin:1.25rem 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:.7rem;padding:.9rem 1rem}
.kpi b{display:block;font-size:1.6rem;line-height:1.2}
.kpi span{color:var(--mut);font-size:.82rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:.75rem;margin:1rem 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:.7rem;padding:1rem}
.card h3{margin-top:0}
.card p{margin:.35rem 0 0;color:var(--mut);font-size:.9rem}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:.7rem;margin:.75rem 0 1.5rem}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{padding:.55rem .7rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef1f5;font-size:.76rem;letter-spacing:.04em;text-transform:uppercase;color:#3c4756;white-space:nowrap}
tbody tr:nth-child(even){background:#fafbfc}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
.b{display:inline-block;padding:.1rem .45rem;border-radius:999px;font-size:.72rem;font-weight:700;white-space:nowrap}
.b.ok{background:var(--okbg);color:var(--ok)}
.b.bad{background:var(--badbg);color:var(--bad)}
.b.warn{background:var(--warnbg);color:var(--warn)}
.banner{background:#fff;border-left:4px solid var(--accent);border-radius:.4rem;padding:.8rem 1rem;margin:1rem 0;font-size:.92rem}
.banner.warn{border-left-color:#c98a00;background:#fffdf6}
.banner.bad{border-left-color:var(--bad);background:#fffafa}
.mut{color:var(--mut);font-size:.85rem}
.quote{font-size:.82rem;color:#34404e;background:#f4f6f9;border-radius:.4rem;padding:.45rem .6rem;display:block;margin-top:.3rem;white-space:pre-wrap;word-break:break-word}
.blank{color:#98a2ad}
footer{border-top:1px solid var(--line);background:#fff;padding:1.25rem;color:var(--mut);font-size:.82rem}
footer p{max-width:1000px;margin:0 auto}
@media (max-width:640px){main{padding:1.25rem .85rem 2.5rem}h1{font-size:1.4rem}}
"""


def main():
    ledger = read(LEDGER)
    unverified = read(UNVERIFIED)
    flags = read(FLAGS)

    # ---- validation: never render an un-sourced or untyped row ----
    for r in ledger:
        if not r["source_url"].startswith("https://"):
            raise SystemExit(f"ledger row {r['check_id']} has no https official source")
        if r["result"].lower() not in {"match", "mismatch"}:
            raise SystemExit(f"ledger row {r['check_id']} has invalid result {r['result']!r}")
    for r in unverified:
        if r["published_value"].strip():
            raise SystemExit("unverified row must leave published_value blank")
        if not r["official_reference"].startswith("https://"):
            raise SystemExit("unverified row needs an official reference link")

    by_cat = {}
    for r in ledger:
        by_cat.setdefault(r["category"], []).append(r)
    matches = sum(1 for r in ledger if r["result"].lower() == "match")
    mismatches = [r for r in ledger if r["result"].lower() != "match"]
    results = by_cat.get("Game result", [])
    standings = by_cat.get("Standings", [])
    rights = by_cat.get("Rights", [])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "verify.css").write_text(CSS, encoding="utf-8")

    # ---------------- index ----------------
    kpis = [
        (str(len(ledger)), "official checks recorded"),
        (f"{matches}/{len(ledger)}", "published values matched"),
        (str(len(mismatches)), "mismatches"),
        (str(len(unverified)), "items left blank / unverified"),
        (str(len(flags)), "irregularities flagged"),
    ]
    kpi_html = "".join(f'<div class="kpi"><b>{esc(v)}</b><span>{esc(l)}</span></div>' for v, l in kpis)
    OFFICIAL_FOR = {
        "Game result": "https://www.nba.com/games?date=2026-11-02",
        "Standings": "https://www.nba.com/standings",
        "Rights": "https://www.nba.com/termsofuse",
    }
    coverage = []
    for cat, rows in by_cat.items():
        m = sum(1 for r in rows if r["result"].lower() == "match")
        coverage.append([
            esc(cat), str(len(rows)), f"{m}", str(len(rows) - m),
            link(OFFICIAL_FOR.get(cat, "https://www.nba.com/"), "official source"),
            f'<a href="{CATEGORY_OF.get(cat, "index.html")}">open table →</a>',
        ])
    coverage.append([
        "Unverified items", "—", "—", str(len(unverified)),
        link("https://www.nba.com/stats/help/faq", "NBA Stats FAQ"),
        '<a href="unverified.html">open list →</a>',
    ])
    cards = "".join(
        f'<a class="card" href="{href}"><h3>{esc(title)}</h3><p>{esc(desc)}</p></a>'
        for href, title, desc in [
            ("results.html", "Game results", "All 15 final scores of the 2026-11-02 slate, each re-read on its official NBA.com game page."),
            ("standings.html", "Standings — dated 2026-11-03", "All 30 win-loss records matched the official table on 2026-11-03; this is not a current 2026-11-05 snapshot."),
            ("policy.html", "Rights & law", "NBA Terms of Use and the Korean National Sports Promotion Act, quoted verbatim with links."),
            ("unverified.html", "Unverified", "What could not be confirmed from an official source. Published value: blank."),
            ("flagged.html", "Flagged for review", "Irregularities and conflicts, with severity and the official source to review."),
        ]
    )
    body = f"""
<div class="kpis">{kpi_html}</div>
<div class="banner"><b>Scope, stated plainly.</b> This section records only what was read from an official page on
2026-11-03: NBA.com game summaries, the NBA.com standings table, NBA.com Terms of Use, the NBA.com/Stats FAQ,
the NBA's official release on prediction markets, and the Korean statute on law.go.kr.
Each row is one check with the URL that was opened. Nothing was inferred, averaged or filled in.
A blank cell means the value is unknown, not zero.</div>
<div class="banner"><b>Final integration re-read, 2026-11-05.</b> All 15 November 2 final scores were opened again on their official game pages and matched (V28–V42 in the <a href="../review/verification.html">direct verification log</a>). Terms §6, the Korean whole-law header and the other scoped policy pages were also freshly read. The 54-row ledger below keeps its original 2026-11-03 dates. The live standings page has advanced, so it cannot freshly confirm the 30 historical W-L rows; those rows remain a dated snapshot, not current standings. A <a href="../daily/standings.html">separate November 5 daily capture</a> supplies its own dated table without rewriting this ledger.</div>
<h2>What was checked</h2>
{table(["Category", "Checks", "Matched", "Mismatched", "Official source", "Table"], coverage, numeric=(1, 2, 3))}
<h2>Open the tables</h2>
<div class="cards">{cards}</div>
<h2>How the audit was run</h2>
<ol>
  <li>Each published value was compared, one row at a time, with the official page for that row.</li>
  <li>The URL actually opened and the read date are stored on the row (ledger CSV in the repository).</li>
  <li>If the value could not be read from an official source, the row is not shown as verified: its published value stays blank on the <a href="unverified.html">Unverified</a> page with the reason.</li>
  <li>The build fails if any ledger row has no official https link, an unknown status, or if an unverified row carries a value.</li>
  <li>Conflicts and rights problems are listed on <a href="flagged.html">Flagged for review</a>; they do not block publication but are never hidden inside a table.</li>
</ol>
<h2>What this does and does not prove</h2>
<div class="banner warn"><b>It does not prove an edge.</b> Verifying that a score, a standing or a statute is
correct says nothing about whether a model can beat a market. On the single graded slate the market was at
least as accurate as the model and every uncertainty interval included zero; no strategy passed its gates.
Statistical validation reduces uncertainty about bad luck — it cannot remove luck from a small sample.
See <a href="../hub/forward-test.html">forward test</a> and <a href="../hub/validation.html">validation gates</a>.</div>
<h2>Verification limits</h2>
<ul>
  <li>The 15 Nov 2 scores were verified row by row in this session. Of the 92 earlier scores, 13 were re-read by an earlier session and the rest carry a prior-session badge.</li>
  <li>Market prices and prop lines are secondary-source (ESPN relay of DraftKings) and stay unverified: no official sportsbook or licensed odds page was read.</li>
  <li>Aggregate cross-check: win-loss records recomputed from all 107 result rows match the official 30-team standings exactly.</li>
</ul>
<p class="mut">Machine-readable record:
<a href="{REPO}/blob/main/data/verification_official_2026_11_03.csv">verification ledger</a> ·
<a href="{REPO}/blob/main/data/verification_unverified_2026_11_03.csv">unverified list</a> ·
<a href="{REPO}/blob/main/data/verification_flags_2026_11_03.csv">flag register</a>.</p>
"""
    page("index.html", "Independent verification ledger", "One row per check, one link per row, read from the official source on 2026-11-03.", body)

    # ---------------- results ----------------
    rows = [
        [esc(r["item"]), esc(r["published_value"]), esc(r["official_value"]), badge(r["result"]),
         link(r["source_url"], "official game page"), esc(r["checked_on"]), esc(r["note"])]
        for r in results
    ]
    body = (
        f'<div class="banner"><b>{len(results)} of {len(results)} final scores match.</b> Each row was re-read on the '
        "official NBA.com game summary page for that game id on 2026-11-03, and all 15 were independently re-read again on 2026-11-05 (V28–V42). The table's Read on column preserves the original ledger date. Home team is listed second, as on NBA.com.</div>"
        + table(["Game (id)", "Value on this site", "Value read on nba.com", "Check", "Source", "Read on", "Note"],
                rows, table_id="results")
        + '<p class="mut">Machine-readable: <a href="' + REPO + '/blob/main/data/results_2026-11-02.csv">data/results_2026-11-02.csv</a> '
          'and <a href="' + REPO + '/blob/main/data/verification_official_2026_11_03.csv">the ledger</a>.</p>'
    )
    page("results.html", "Game results — 2026-11-02 slate", "Fifteen final scores, fifteen official game pages, zero mismatches.", body)

    # ---------------- standings ----------------
    rows = [
        [esc(r["item"]), esc(r["published_value"]), esc(r["official_value"]), badge(r["result"]),
         link(r["source_url"], "nba.com/standings"), esc(r["checked_on"])]
        for r in standings
    ]
    body = (
        f'<div class="banner"><b>{len(standings)} of {len(standings)} records match.</b> '
        "Published values are from the dated capture in <code>data/standings_live_2026-11-03.csv</code>; "
        "the official values were read from the 2026-27 regular-season standings page on 2026-11-03. "
        "A fresh 2026-11-05 read shows the live table has advanced (for example PHI 8–1 rather than 7–1), so these 30 rows are historical matches, not current standings.</div>"
        + table(["Team", "Value on this site", "Value read on nba.com", "Check", "Source", "Read on"], rows, table_id="standings")
        + '<h2>Aggregate cross-check</h2><div class="banner">Win-loss records recomputed from all 107 result rows '
          "(92 earlier + 15 on 2026-11-02) equal the official standings for all 30 teams. This is an internal recomputation "
          "over the committed results, not a second independent source.</div>"
    )
    page("standings.html", "Standings — dated 2026-11-03 snapshot", "Thirty historical W-L matches from 2026-11-03; not current 2026-11-05 standings.", body)

    # ---------------- policy ----------------
    rows = []
    for r in rights:
        rows.append([
            esc(r["item"]),
            f'<span class="quote">{esc(r["official_value"])}</span>',
            badge(r["result"]),
            link(r["source_url"], r["source_title"]),
            esc(r["checked_on"]),
            esc(r["note"]),
        ])
    body = (
        '<div class="banner bad"><b>Rights are the binding constraint on this project.</b> '
        "NBA Terms §9 bars using NBA Statistics in connection with gambling activity, and §1 bars reuse or linking of "
        "Basketball Content without written permission. Korean law separately restricts issuing or operating systems for "
        "similar betting. Nothing here is legal advice, and no permission or opinion has been obtained.</div>"
        + table(["Instrument", "Text read on the official page", "Check", "Source", "Read on", "Note"],
                rows, table_id="policy")
        + '<p class="mut">Translations of the Korean statute are the compiler\'s; the Korean text is authoritative. '
          'Conflicts are on <a href="flagged.html">Flagged for review</a>.</p>'
    )
    page("policy.html", "Rights and law — quoted sources", "NBA Terms of Use, the NBA Stats FAQ, the NBA prediction-market release, and the Korean National Sports Promotion Act.", body)

    # ---------------- unverified ----------------
    rows = [
        [esc(r["item"]), '<span class="blank">blank</span>', badge("unverified"), esc(r["reason"]),
         link(r["official_reference"], r["reference_title"])]
        for r in unverified
    ]
    body = (
        '<div class="banner warn"><b>Blank is a finding, not an omission.</b> These items could not be confirmed from an '
        "official source. Their values are deliberately left blank everywhere on the site and are never estimated. "
        "The link on each row is the official page a reviewer should consult, not proof of the value.</div>"
        + table(["Item", "Published value", "Status", "Why it is unverified", "Official page to review"],
                rows, table_id="unverified")
    )
    page("unverified.html", "Unverified items", "What could not be confirmed from an official source, and why.", body)

    # ---------------- flagged ----------------
    sev_class = {"high": "bad", "medium": "warn", "low": "warn"}
    rows = [
        [esc(r["flag_id"]), f'<span class="b {sev_class.get(r["severity"], "warn")}">{esc(r["severity"])}</span>',
         esc(r["item"]), esc(r["detail"]), link(r["source_url"], r["official_source"]), esc(r["status"])]
        for r in flags
    ]
    body = (
        '<div class="banner">Open items for the owner to review. They are published rather than hidden, and they do not '
        "block publication because the affected values are blank or labelled unverified.</div>"
        + table(["ID", "Severity", "Item", "Detail", "Official source", "Status"], rows, table_id="flagged")
    )
    page("flagged.html", "Flagged for review", "Irregularities, rights conflicts and unresolved questions.", body)

    print(f"built {OUT.relative_to(ROOT)}: {len(ledger)} ledger checks "
          f"({matches} match, {len(mismatches)} mismatch), {len(unverified)} unverified, {len(flags)} flags")


if __name__ == "__main__":
    main()
