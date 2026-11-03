#!/usr/bin/env python3
"""Sitewide structural source audit. An official URL is NOT verified row evidence.

No network requests, scraping, betting data, inferred values or source-body claims.
Run normally to regenerate; --check rejects stale artifacts; --strict additionally
rejects missing/secondary/repository-only row references. Legacy findings are
published, not silently waived or mislabeled factual verification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/sassnarep3-star/Own6"
# This is a declared structural reference policy, not a trust/accuracy verdict.
PUBLISHERS = {
    "nba.com": "NBA", "law.go.kr": "Korean legislation portal",
    "nist.gov": "NIST", "scikit-learn.org": "scikit-learn",
    "scipy.org": "SciPy", "statsmodels.org": "statsmodels",
    "docs.github.com": "GitHub documentation", "docs.python.org": "Python documentation",
    "cftc.gov": "CFTC", "kansspelautoriteit.nl": "Dutch Gambling Authority",
    "help.draftkings.com": "DraftKings help", "sportsbook.draftkings.com": "DraftKings sportsbook",
    "support.fanduel.com": "FanDuel support", "gaming.nv.gov": "Nevada Gaming Control Board",
}
STATUSES = ("official_reference_present", "repository_reference_only", "secondary_reference_only", "no_https_reference")
ROWS_FIELDS = ["page", "table", "row", "line", "cells", "row_sha256", "coverage_status", "official_urls", "repository_urls", "other_https_urls", "value_verification", "verified_value", "repository_source"]
PAGE_FIELDS = ["page", "page_sha256", "data_rows", *STATUSES, "repository_source"]


def reference_kind(url: str) -> str:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme.lower() != "https" or not host or parsed.username or parsed.password:
            return "unsupported"
        if host in {"github.com", "api.github.com"}:
            path = parsed.path.rstrip("/")
            prefix = "/sassnarep3-star/Own6" if host == "github.com" else "/repos/sassnarep3-star/Own6"
            return "repository" if path == prefix or path.startswith(prefix + "/") else "other"
        if any(host == domain or host.endswith("." + domain) for domain in PUBLISHERS):
            return "official"
        return "other"
    except ValueError:
        return "unsupported"


class Tables(HTMLParser):
    """Collect td-bearing rows including tables without tbody and optional end tags.

    Nested table rows belong only to their own nearest table. Content and source
    references of child tables are not credited to a parent row.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.table_number = 0
        self.rows = []
        self.ignored = 0

    def finish(self):
        ctx = self.stack[-1]
        row = ctx.get("current")
        if row and row["cells"]:
            row["row_sha256"] = hashlib.sha256(json.dumps(
                [row["cells"], row["parts"], row["links"]], ensure_ascii=False,
                separators=(",", ":")).encode()).hexdigest()
            self.rows.append(row)
        ctx["current"] = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "template"}:
            self.ignored += 1
        if self.ignored:
            return
        if tag == "table":
            self.table_number += 1
            self.stack.append({"number": self.table_number, "rows": 0, "current": None})
        if not self.stack:
            return
        ctx = self.stack[-1]
        if tag == "tr":
            self.finish()
            ctx["rows"] += 1
            ctx["current"] = {"table": ctx["number"], "row": ctx["rows"], "line": self.getpos()[0], "cells": 0, "parts": [], "links": []}
        row = ctx.get("current")
        if row:
            if tag == "td":
                row["cells"] += 1
            if tag == "a" and attrs.get("href"):
                row["links"].append(attrs["href"].strip())

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template"} and self.ignored:
            self.ignored -= 1
            return
        if self.ignored or not self.stack:
            return
        if tag == "tr":
            self.finish()
        if tag == "table":
            self.finish()
            self.stack.pop()

    def handle_data(self, data):
        if self.stack and not self.ignored and self.stack[-1].get("current"):
            self.stack[-1]["current"]["parts"].append(data)

    def close(self):
        super().close()
        while self.stack:
            self.finish()
            self.stack.pop()


def inspect_page(path: Path, root: Path) -> tuple[dict, list[dict]]:
    relative = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    parser = Tables()
    parser.feed(raw.decode("utf-8"))
    parser.close()
    records = []
    for row in sorted(parser.rows, key=lambda r: (r["table"], r["row"])):
        urls = {kind: sorted({u for u in row["links"] if reference_kind(u) == kind}) for kind in ("official", "repository", "other")}
        status = STATUSES[0] if urls["official"] else STATUSES[1] if urls["repository"] else STATUSES[2] if urls["other"] else STATUSES[3]
        records.append({
            "page": relative, "table": row["table"], "row": row["row"], "line": row["line"], "cells": row["cells"],
            "row_sha256": row["row_sha256"], "coverage_status": status,
            "official_urls": " | ".join(urls["official"]), "repository_urls": " | ".join(urls["repository"]),
            "other_https_urls": " | ".join(urls["other"]), "value_verification": "not_independently_verified_in_this_audit",
            "verified_value": "", "repository_source": f"{REPO}/blob/main/{quote(relative)}#L{row['line']}",
        })
    counts = Counter(r["coverage_status"] for r in records)
    page = {"page": relative, "page_sha256": hashlib.sha256(raw).hexdigest(), "data_rows": len(records),
            **{s: counts[s] for s in STATUSES}, "repository_source": f"{REPO}/blob/main/{quote(relative)}"}
    return page, records


def csv_text(records, fields):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return buf.getvalue()


def anchor(url, text):
    return f'<a href="{escape(url, quote=True)}">{escape(str(text))}</a>'


def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join(f'<th scope="col">{escape(h)}</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{cell}</td>' for cell in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def layout(title, body):
    nav = [('index.html', 'Summary'), ('pages.html', 'Page coverage'), ('rows.html', 'Every row'), ('flagged.html', 'Flagged for Review'), ('sources.html', 'Sources & limits'), ('../index.html', 'Project home')]
    return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(title) + ' · Own6</title><link rel="stylesheet" href="style.css"></head><body><header><strong>OWN6 / SOURCE COVERAGE</strong><nav aria-label="Main">' + ''.join(anchor(u, t) for u, t in nav) + '</nav></header><main><p class="eyebrow">INDEPENDENT RELEASE ACCEPTANCE · 2026-11-03</p><h1>' + escape(title) + '</h1>' + body + '</main><footer>Offline structural audit, not factual certification. No scraped statistics, betting recommendations or manufactured performance. Every audit row links to its repository evidence; an NBA reference does not certify a value.</footer></body></html>\n'


def artifacts(root: Path):
    # Coverage pages are excluded to prevent recursive self-inventory; their
    # structure and links are exercised separately by tests/release_gate.py.
    paths = sorted(p for p in (root / 'docs').rglob('*.html') if 'coverage' not in p.relative_to(root / 'docs').parts[:1])
    if (root / 'index.html').exists():
        paths.insert(0, root / 'index.html')
    pages, rows = [], []
    for p in paths:
        page, records = inspect_page(p, root)
        pages.append(page)
        rows.extend(records)
    counts = Counter(r['coverage_status'] for r in rows)
    total = {'scope': 'root index.html and docs/**/*.html excluding docs/coverage/** (self-generated audit)',
             'pages': len(pages), 'data_rows': len(rows), 'coverage': {s: counts[s] for s in STATUSES},
             'independently_value_verified_by_this_audit': 0,
             'note': 'Zero certified by this structural audit is not a claim that all prior facts are false. Official link presence never verifies a row value.',
             'input_manifest_sha256': hashlib.sha256(json.dumps(pages, sort_keys=True).encode()).hexdigest()}
    gaps = [r for r in rows if r['coverage_status'] != STATUSES[0]]
    out = {
        'data/source_coverage/rows.csv': csv_text(rows, ROWS_FIELDS),
        'data/source_coverage/pages.csv': csv_text(pages, PAGE_FIELDS),
        'data/source_coverage/summary.json': json.dumps(total, indent=2, sort_keys=True) + '\n',
    }
    caveat = '<div class="notice"><strong>Reference coverage ≠ factual verification.</strong> This report checks actual HTTPS anchor links inside each table row. It does not download source bodies or certify game scores, odds, correlations, ROI, model skill, rights or legal eligibility. Confirmed empirical values remain blank in this audit.</div>'
    cards = '<section class="cards">' + ''.join(f'<article><strong>{v:,}</strong><span>{escape(k)}</span></article>' for k, v in [('pages scanned', len(pages)), ('data rows', len(rows)), ('external official-reference rows', counts[STATUSES[0]]), ('coverage gaps', len(gaps))]) + '</section>'
    summary = [
        ['Publication readiness', 'Structural source coverage only; gaps published, not hidden.', anchor(REPO, 'Repository')],
        ['Evidence decision', 'No betting strategy or empirical value is certified by this audit.', anchor('https://www.nba.com/stats/help/glossary', 'NBA definitions only')],
        ['Data rights', 'NBA Terms §9 restrict gambling-connected use of NBA Statistics; no permission is inferred from public availability.', anchor('https://www.nba.com/termsofuse#nba-statistics', 'NBA Terms §9')],
        ['Definitions vs predictions', 'The glossary defines basketball metrics; it does not validate a predictive edge or a correlation estimated here.', anchor('https://www.nba.com/stats/help/glossary', 'NBA glossary')],
        ['No manual data entry', 'Run python3 scripts/source_coverage.py; CI builds exact-tested-tree coverage and checks repeatability automatically.', anchor(REPO + '/blob/main/scripts/source_coverage.py', 'Audit implementation')],
        ['Scope boundary', 'All published HTML tables except this self-generated audit. Header-only rows excluded. No API/JavaScript-loaded tables are certified.', anchor(REPO + '/blob/main/data/source_coverage/pages.csv', 'Exact page inventory')],
    ]
    out['docs/coverage/index.html'] = layout('Source coverage executive summary', caveat + cards + '<h2>Executive decision</h2>' + table(['Category', 'Finding / limitation', 'Official reference / repository evidence'], summary) + '<h2>Review the evidence</h2><p>Browse '+anchor('pages.html', 'page coverage')+', '+anchor('rows.html', 'every inventoried row')+' and '+anchor('flagged.html', 'Flagged for Review')+'. The data exports contain hashes, row coordinates and source URLs—not copied unverified empirical values.</p><p>'+anchor('../../data/source_coverage/rows.csv', 'Download every row (CSV)')+' · '+anchor('../../data/source_coverage/summary.json', 'Machine-readable summary')+'</p>')
    page_rows = [[anchor('../../' + p['page'], p['page']), str(p['data_rows']), *[str(p[s]) for s in STATUSES], anchor(p['repository_source'], 'Source file')] for p in pages]
    out['docs/coverage/pages.html'] = layout('Coverage by page', caveat + table(['Page', 'Data rows', 'Official reference', 'Repo only', 'Secondary only', 'No HTTPS reference', 'Repository evidence'], page_rows))
    def row_cells(r):
        official = '<br>'.join(anchor(u, urlsplit(u).hostname) for u in r['official_urls'].split(' | ') if u)
        return [escape(r['page']), f"{r['table']} / {r['row']}", escape(r['coverage_status']), official, '', '<span class="badge">UNVERIFIED IN THIS AUDIT</span>', anchor(r['repository_source'], 'Inspect row')]
    headers = ['Page', 'Table / row', 'Reference coverage', 'External official reference', 'Confirmed value', 'Value status', 'Repository evidence']
    out['docs/coverage/rows.html'] = layout('Every inventoried table row', caveat + '<p>Coordinates are one-based and include header rows in the row counter. A blank confirmed-value field is intentional. Use the browser’s Find command to locate a page or status.</p>' + table(headers, [row_cells(r) for r in rows]))
    out['docs/coverage/flagged.html'] = layout('Flagged for Review', caveat + f'<p><strong>{len(gaps):,} rows lack a recognized external official HTTPS reference.</strong> Repository-only rows may describe this repository correctly, but they do not verify NBA/market facts. Secondary-only includes publisher domains outside the declared reference policy; it does not by itself prove a claim false. Gaps do not block publication of the clearly labeled research site.</p><p>Request logged for the respective page owners in COORDINATION.md. No other session’s pages were silently edited.</p>' + table(headers, [row_cells(r) for r in gaps]))
    source_rows = [
        ['NBA Terms §§1,9', 'Directly read 2026-11-03 (chunks 0,3,4). Ownership/use and NBA Statistics restrictions; not a legal opinion.', anchor('https://www.nba.com/termsofuse', 'NBA official terms')],
        ['NBA Stats FAQ', 'Directly read 2026-11-03, chunk 0. Download question says stats are for viewing on NBA.com/Stats. The FAQ includes historical examples; not a current ratings feed.', anchor('https://www.nba.com/stats/help/faq', 'NBA official FAQ')],
        ['NBA Stats glossary', 'Directly read 2026-11-03, chunk 0 only. Metric-definition page; no game outcomes or edge values checked.', anchor('https://www.nba.com/stats/help/glossary', 'NBA official glossary')],
        ['GitHub Pages documentation', 'Directly read 2026-11-03, full single chunk. Static hosting and project-site URL conventions.', anchor('https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages', 'GitHub official docs')],
        ['Reference classification policy', 'Exact hostname or dot-boundary subdomain match; HTTPS required; embedded credentials rejected. Arbitrary github.com repositories are not first-party evidence for Own6.', anchor(REPO + '/blob/main/scripts/source_coverage.py', 'Implementation & publisher policy')],
        ['Snapshot reproducibility', 'Per-page SHA-256 plus per-row canonical-content hashes. This is structural repeatability, not independent source-body verification. GitHub main links resolve current main; hashes identify the audited snapshot.', anchor(REPO + '/blob/main/data/source_coverage/pages.csv', 'Page hashes')],
        ['Full row values', 'Not copied into this audit. The confirmed-value column is blank for every row; no value inferred from a hyperlink, checksum or passing test.', anchor(REPO + '/blob/main/data/source_coverage/rows.csv', 'Row audit ledger')],
    ]
    out['docs/coverage/sources.html'] = layout('Sources and verification limits', caveat + table(['Source / policy', 'Verification performed / boundary', 'Official reference / repository evidence'], source_rows) + '<h2>How to reproduce</h2><pre>python3 scripts/source_coverage.py\npython3 scripts/source_coverage.py --check\npython3 scripts/source_coverage.py --check --strict\npython3 -m unittest discover -s tests -p test_source_coverage.py -v</pre><p>The optional strict command fails while coverage gaps exist. CI builds a current-tree artifact and checks repeatability and parser regressions; it does not enforce committed-snapshot freshness. A green CI check is not a green factual-verification gate. External HTTP reachability and fragment existence are not checked by this offline tool.</p>')
    out['docs/coverage/style.css'] = '/* No external fonts, trackers, or dependencies. */\n:root{font-family:system-ui,sans-serif;color:#193149;background:#f3f6fa;line-height:1.55}*{box-sizing:border-box}body{margin:0}header{background:#122a43;color:white;padding:1.3rem 4vw}nav{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;margin-top:1rem}nav a{color:#deebff}main{max-width:1400px;margin:auto;padding:2rem 4vw}h1{font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.15}h2{margin-top:2rem}a{color:#075ea6;text-underline-offset:3px}a:focus-visible{outline:3px solid #d09200;outline-offset:4px}.eyebrow{font-size:.75rem;letter-spacing:.1em;font-weight:700;color:#52667a}.notice{border-left:4px solid #bd730b;background:#fff5df;padding:1rem;margin:1.3rem 0}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:1rem}article{background:white;padding:1.2rem;border:1px solid #d8e2ee;border-radius:10px}article strong{display:block;font-size:2rem}article span{font-size:.85rem}.table-wrap{overflow:auto;background:white;border:1px solid #d8e2ee;border-radius:8px;margin:1rem 0}table{border-collapse:collapse;width:100%;font-size:.85rem}th,td{padding:.7rem;text-align:left;vertical-align:top;border-bottom:1px solid #e1e8f0;overflow-wrap:anywhere;min-width:90px}th{background:#e9f0f8}tr:hover td{background:#f7faff}.badge{color:#865400;font-size:.7rem;font-weight:bold}footer{max-width:1400px;margin:auto;padding:2rem 4vw;color:#52667a;font-size:.8rem}pre{overflow:auto;background:#142d46;color:#e1ecf5;padding:1rem;border-radius:8px}\n'
    out['audit/SOURCE_COVERAGE.md'] = f'''# Source coverage acceptance — 2026-11-03

## Executive summary

Scanned **{len(pages)} published HTML pages** and **{len(rows)} data rows**, excluding only this audit's self-generated `docs/coverage/` pages. **{counts[STATUSES[0]]}** rows carry a recognized external official HTTPS reference; **{len(gaps)}** are coverage gaps. **No empirical value was independently certified by this structural audit.** Confirmed-value fields remain blank; an official URL, passing arithmetic check or file hash cannot certify a row's factual content.

Site: https://sassnarep3-star.github.io/Own6/docs/coverage/

## Exact scope and verification

- Page hashes: `data/source_coverage/pages.csv`.
- Every td-bearing row, coordinates, row hash and URL classifications: `data/source_coverage/rows.csv`.
- Machine summary: `data/source_coverage/summary.json`.
- HTML parser covers all `docs/**/*.html`, not only selected maintained sections, plus root `index.html`. It handles missing tbody, header rows, optional tr end tags, and nested-table isolation. It is not a full browser or JavaScript evaluator.
- Every generated audit row carries a first-party repository evidence link. That link supports the structural finding, NOT the underlying score, price or correlation. External official-reference links are retained where present. No source link or verified numerical value is invented for uncovered rows.
- Link checks do not test external URL reachability, source-body support, data permission or valid HTML semantics in general.
- Build: `python3 scripts/source_coverage.py`; freshness check: `python3 scripts/source_coverage.py --check`; optional strict coverage gate: add `--strict` (expected to fail with outstanding legacy coverage gaps).
- Repeatability CI cannot make the legacy coverage gaps disappear; it uploads regenerated artifacts without silently editing or deploying snapshots from other sessions. These are explicitly published on **Flagged for Review**.

## Official sources read this session

1. https://www.nba.com/termsofuse — chunks 0,3,4: §§1 and 9 ownership/reuse and NBA Statistics restrictions; no permission inferred. This is not a jurisdiction-specific legal opinion.
2. https://www.nba.com/stats/help/faq — chunk 0: download question, for viewing on NBA.com/Stats. Historical illustrative values in that FAQ are not live ratings.
3. https://www.nba.com/stats/help/glossary — chunk 0 only: metric definitions. No game outcome, market quote or predictive advantage independently checked.
4. https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages — full single chunk: static repository hosting and project URL convention.

## Coordination and irregularities

Only additive claimed files were changed. Existing research results, correlations, odds and verified labels are not upgraded to independently verified evidence. Active PR #31 owns assurance/model hardening; PR #28 owns legacy review repairs. Requests to their owners are logged in COORDINATION.md; no overlapping edits or duplicate model/site rewrite.

A full-source, line-by-line empirical verification of existing NBA and secondary-market records is **not completed by this audit**, and no such claim is made. Skill, correlations and returns require authorized timestamped evidence, frozen strategies, out-of-sample assessment and uncertainty controls. No approach eliminates outcome randomness or guarantees profit.
'''
    return out, total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='reject stale/missing generated artifacts without writing')
    parser.add_argument('--strict', action='store_true', help='also reject rows without external official references')
    args = parser.parse_args()
    outputs, summary = artifacts(ROOT)
    stale = []
    for relative, content in outputs.items():
        p = ROOT / relative
        if args.check:
            if not p.exists() or p.read_text(encoding='utf-8') != content:
                stale.append(relative)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8')
    gaps = summary['data_rows'] - summary['coverage'][STATUSES[0]]
    print(json.dumps(summary, indent=2))
    if stale:
        print('STALE artifacts: ' + ', '.join(stale))
    if args.strict and gaps:
        print(f'STRICT COVERAGE FAIL: {gaps} legacy rows lack external official-reference coverage; see docs/coverage/flagged.html')
    return int(bool(stale) or (args.strict and gaps > 0))


if __name__ == '__main__':
    raise SystemExit(main())
