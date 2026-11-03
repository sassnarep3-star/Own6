# Source assurance and repository review

**Review date:** 2026-11-03. **Session:** `arena/74d27b5d-own6`. **Upstream review baseline:** `86eca0f`.

## Decision

Publish the research framework and review ledger, but do **not** publish a current betting line, a measured correlation, a profitable strategy, or a reward winner. No authorized gambling-use data feed is configured. The NBA's official terms restrict gambling use of NBA Statistics; the Stats FAQ does not offer a download. A source link is not a license.

## What was checked

`python scripts/audit_repo.py` scans every line of the non-generated repository text inventory, records a SHA-256 digest and line count per file, parses Python/JSON/CSV, and reviews every legacy data record. The generated `data/assurance/summary.json` is authoritative for counts. The audit does not recursively treat its own outputs as independent evidence.

- `inventory.csv`: file-level coverage and checksums. A checksum proves file identity, not factual correctness.
- `row_audit.csv`: every legacy data record, its supplied source, and a separate value-verification status. All 541 legacy data records remain **unverified** in this review; official URL presence is not value-level confirmation.
- `sources.csv`: 20 directly read official-source records and two explicitly partial reads. Each record states what the source supports and what it does not support.
- `findings.csv`: reproducible findings with immutable upstream code links, external method/policy references, severity and disposition.

This is a complete structural scan and record-level provenance review, **not** a claim that every historical NBA score or sportsbook quote was independently re-fetched. No new NBA statistics were collected or republished. Existing archives are preserved and clearly separated from the empty authorized ledger.

## Important findings

1. The legacy line model formerly converted American odds incorrectly (`scripts/model.py:197–203`). Concurrent PR #29 repaired the formula and regenerated its outputs; the official operator formula and a pure arithmetic regression demonstrate the original defect. Historical ESPN quotes remain unverified even after the arithmetic repair.
2. The empirical engine previously accepted self-asserted audit booleans, discarded zero-valued residuals, and did not bind combo qualification to a real joint sample. The D2 hardening addresses these failure modes without adding data.
3. A win-count Poisson-binomial test is not a family-wise correction for clustered ROI. The revised design uses a common slate-cluster resampling family for the actual qualification statistics. The independent-trial win-count test remains only a diagnostic.
4. The 200-event sample floor is a policy minimum, not a power calculation. A training-only precision/power analysis is required; no sample size guarantees discovery of an edge.
5. Internal agreement among local standings, ratings and results is not official-source verification. The earlier “213 checks” result must not be presented as independent fact certification.
6. Concurrent sessions already repaired the root conflict markers and lab table rendering. Those repairs are credited and preserved, not duplicated.

## Official references

- [NBA Terms of Use](https://www.nba.com/termsofuse), §§1 and 9: reuse and gambling-use restrictions.
- [NBA Stats FAQ](https://www.nba.com/stats/help/faq): no download offering; Four Factors are feature vocabulary, not current measurements.
- [NBA injury-report policy](https://official.nba.com/nba-injury-report-2026-27-season/): reports change throughout the day, so availability must be timestamped.
- [DraftKings odds calculator](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB): official operator reference for American-odds conversion.
- [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html): proper scores are not a calibration-only test.
- [NIST confidence limits](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm): confidence is a property of the interval method, not a probability of future profit.

The full source register and all review rows are published in the assurance dashboard. Partial Korean-law and rulebook reads remain flagged; no legal applicability is inferred.

## Reproduce

```sh
python -m pip install -r requirements-empirical.txt
python scripts/audit_repo.py
python -m pytest -q tests/assurance
```

The audit is offline and deterministic. It never fills a missing value, converts an unverified row into a verified one, or treats synthetic tests as empirical results.
