# Independent close-out — session arena/8dd3131f-own6

**Date:** 2026-11-05 (UTC)  
**Scope:** Executive-summary currency, the current fail-closed report, and reproducible publication/test checks. This is not a fresh fact certification of all legacy NBA rows.

## Results

- The current empirical artifacts list six candidates and report zero authorized observations, zero qualified strategies, and `not_run`; estimated ROI, CLV, current correlation, and model-versus-market values are empty/null. Reproduced by running `python scripts/run_lab.py` after installing `requirements-empirical.txt` into a local virtual environment. The command printed: `FAIL-CLOSED: 0 authorized observations; status=not_run, leaderboard empty. Strategies: 6; gates: 10.` The report files had no diff after generation. Evidence: [`data/empirical/report.json`](../data/empirical/report.json), [`data/empirical/report.csv`](../data/empirical/report.csv), [`data/empirical/evidence.json`](../data/empirical/evidence.json), [`scripts/run_lab.py`](../scripts/run_lab.py).
- `python3 tools/run_tests.py` passed **32/32** tests.
- `python3 scripts/check_assurance.py` passed: nine assurance pages, 14,458 source-linked table rows, fail-closed report preserved.
- `python3 scripts/check_site.py` passed: nine pages, no broken internal links, all external links HTTPS.
- `python3 scripts/linkcheck.py` passed: seven pages / 322 links / 240 data rows, every data row has a source, all internal links resolve, external hosts allowlisted.
- All of the above are software/data-shape and site-publication checks. A source URL or successful checker does not prove that historical NBA data is accurate, licensed, or suitable for gambling research.

## Official source reads (retrieved directly 2026-11-05)

- [NBA.com Terms of Use](https://www.nba.com/termsofuse), chunks 0, 3 and 4: §1 says Basketball Content may not be used publicly or commercially absent the stated permission; §9(ii) limits NBA Statistics to legitimate news reporting or private, non-commercial purposes; §9(iv) says NBA Statistics may not be used in connection with any gambling activity, including legal gambling. This records the text, not a legal conclusion about this project's applicability. The existing issue is already listed as I-24/F17 on [`docs/flagged.html`](../docs/flagged.html) and the assurance [Flagged for Review](../docs/assurance/flagged.html) page.
- [NBA Stats FAQ](https://www.nba.com/stats/help/faq): the page says its statistics are not available for download for academic or personal use. It does not establish whether a separately licensed feed exists.
- [NBA Stats glossary](https://www.nba.com/stats/help/glossary): metric definitions were reachable. These definitions do not verify any model's predictive value.

## Reproducibility limitation / irregularity

Initially, `python3 scripts/audit_repo.py` could not run because baseline commit `86eca0f` was absent from the shallow checkout (boundary `aea6a5ae3093a855331eded7b8c9bf9d90090491`). After final integration PR #50 merged, this session fetched full history, confirmed the baseline object was available, then ran `scripts/audit_repo.py` successfully: 240 files / 31,519 lines scanned and 14,114 data records reviewed. It also ran `scripts/build_assurance.py`; the changed generated outputs are included with this integration update. The old assurance summary had been dated 2026-11-03; the regenerated tree summary is dated 2026-11-05. Structural audit results are not independent factual verification of NBA data.

The initial direct `python3 scripts/run_lab.py` attempt failed because NumPy was not installed in the base interpreter. Installing the pinned requirements in ignored `.venv/` resolved that environment issue; the script then completed and the committed report remained unchanged. `.venv/` is excluded/ignored and is not a deliverable.

## Pull request / integration status

PR [#52](https://github.com/sassnarep3-star/Own6/pull/52) is open against `main`. Its initial GitHub checks `lab` and `assurance` failed after the summary/coordination changes because the shared inventory contained pre-edit hashes; the local pytest reproduction had 134 passed, one failed and six subtests. The final integration PR [#50](https://github.com/sassnarep3-star/Own6/pull/50) subsequently merged at `2ab44bb9519194dc3382eb8a5a93a2036739364c`, with all checks passing. After that integration, this session fetched full history and regenerated the assurance audit/inventory/pages on its combined tree. Full local pytest now passes (135 tests + 6 subtests); `check_assurance.py` reports 14,458 sourced rows, and the other recorded release checks pass. GitHub checks must rerun on the newest PR #52 commit before merge.

PR [#51](https://github.com/sassnarep3-star/Own6/pull/51) remains a parallel, unmerged strategy-pack PR and its `lab`/`assurance` checks currently fail on the shared inventory gate; its append-only executive-summary section should be preserved and its generated inventory rebuilt by that PR's owner/final integrator. The updated PR #52 has not yet merged and Pages deployment of its summary change is pending. Do not merge until all required checks pass.

No additional NBA data, odds, legal interpretations, correlation estimates, or strategy-performance claims were added. Current rights/authorization and legacy archive issues remain flagged rather than resolved.
