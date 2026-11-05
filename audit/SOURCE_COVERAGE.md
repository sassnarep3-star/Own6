# Source coverage acceptance — 2026-11-03

## Executive summary

Scanned **77 published HTML pages** and **15775 data rows**, excluding only this audit's self-generated `docs/coverage/` pages. **15240** rows carry a recognized external official HTTPS reference; **535** are coverage gaps. **No empirical value was independently certified by this structural audit.** Confirmed-value fields remain blank; an official URL, passing arithmetic check or file hash cannot certify a row's factual content.

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
