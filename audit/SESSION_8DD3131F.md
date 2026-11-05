# Independent close-out — session arena/8dd3131f-own6

**Date:** 2026-11-05 (UTC)  
**Scope:** Executive-summary currency, the current fail-closed report, and reproducible publication/test checks. This is not a fresh fact certification of all legacy NBA rows.

## Results

- The current empirical artifacts list six candidates and report zero authorized observations, zero qualified strategies, and `not_run`; estimated ROI, CLV, current correlation, and model-versus-market values are empty/null. Reproduced by running `python scripts/run_lab.py` after installing `requirements-empirical.txt` into a local virtual environment. The command printed: `FAIL-CLOSED: 0 authorized observations; status=not_run, leaderboard empty. Strategies: 6; gates: 10.` The report files had no diff after generation. Evidence: [`data/empirical/report.json`](../data/empirical/report.json), [`data/empirical/report.csv`](../data/empirical/report.csv), [`data/empirical/evidence.json`](../data/empirical/evidence.json), [`scripts/run_lab.py`](../scripts/run_lab.py).
- `python3 tools/run_tests.py` passed **32/32** tests.
- `python3 scripts/check_assurance.py` passed: nine assurance pages, 14,457 source-linked table rows, fail-closed report preserved.
- `python3 scripts/check_site.py` passed: nine pages, no broken internal links, all external links HTTPS.
- `python3 scripts/linkcheck.py` passed: seven pages / 322 links / 240 data rows, every data row has a source, all internal links resolve, external hosts allowlisted.
- All of the above are software/data-shape and site-publication checks. A source URL or successful checker does not prove that historical NBA data is accurate, licensed, or suitable for gambling research.

## Official source reads (retrieved directly 2026-11-05)

- [NBA.com Terms of Use](https://www.nba.com/termsofuse), chunks 0, 3 and 4: §1 says Basketball Content may not be used publicly or commercially absent the stated permission; §9(ii) limits NBA Statistics to legitimate news reporting or private, non-commercial purposes; §9(iv) says NBA Statistics may not be used in connection with any gambling activity, including legal gambling. This records the text, not a legal conclusion about this project's applicability. The existing issue is already listed as I-24/F17 on [`docs/flagged.html`](../docs/flagged.html) and the assurance [Flagged for Review](../docs/assurance/flagged.html) page.
- [NBA Stats FAQ](https://www.nba.com/stats/help/faq): the page says its statistics are not available for download for academic or personal use. It does not establish whether a separately licensed feed exists.
- [NBA Stats glossary](https://www.nba.com/stats/help/glossary): metric definitions were reachable. These definitions do not verify any model's predictive value.

## Reproducibility limitation / irregularity

`python3 scripts/audit_repo.py` could not run in this checkout: it references baseline commit `86eca0f`, but the repository is a shallow clone whose only recorded shallow boundary is `aea6a5ae3093a855331eded7b8c9bf9d90090491`; `git show 86eca0f:scripts/model.py` fails because that object is unavailable locally. No assurance inventory or historical audit output was regenerated in this session. Prior `data/assurance/summary.json` is dated 2026-11-03 and is treated as a prior-session record, not as a new 2026-11-05 audit.

The initial direct `python3 scripts/run_lab.py` attempt failed because NumPy was not installed in the base interpreter. Installing the pinned requirements in ignored `.venv/` resolved that environment issue; the script then completed and the committed report remained unchanged. `.venv/` is excluded/ignored and is not a deliverable.

## Pull request / integration status

PR [#52](https://github.com/sassnarep3-star/Own6/pull/52) was opened against `main` and is intentionally **not merged**. Required GitHub checks `lab` and `assurance` failed after the summary/coordination changes: the `lab` pytest step failed `tests/assurance/test_audit.py::test_inventory_hashes_and_line_counts` because `data/assurance/inventory.csv` still contains the old `COORDINATION.md` digest; Assurance CI's generated-artifacts-committed check also detects rebuild diffs. The same stale hash failure reproduced locally under `pytest` (134 passed, one failed, six subtests); `tools/run_tests.py` remains 32/32 because it runs the non-pytest subset. Other workflow checks passed. This is not presented as a code logic failure or as a green CI run.

The final integration owner on PR [#50](https://github.com/sassnarep3-star/Own6/pull/50) was asked to rebuild the shared assurance inventory/pages on the combined tree, preserving PR [#51](https://github.com/sassnarep3-star/Own6/pull/51)'s append-only executive-summary section. Per the coordination rule, this session did not alter the shared `data/assurance/**` or `docs/assurance/**` outputs owned by that integration. Merge and Pages deployment remain pending; do not merge until shared artifacts are regenerated and all required checks pass.

No additional NBA data, odds, legal interpretations, correlation estimates, or strategy-performance claims were added. Current rights/authorization and legacy archive issues remain flagged rather than resolved.
