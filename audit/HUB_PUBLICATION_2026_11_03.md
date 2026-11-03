# Own6 executive review — strict hub publication

Session: `arena/2dbac92a-own6` · 2026-11-03 UTC. Scope: `docs/hub/`, its generator, checker, policy and CI. This is an incremental integration repair, **not** an assertion that every inherited file or external fact has been independently verified.

## Executive summary

- **Decision: research only; no qualified pick, empirical correlation, profitable edge or reward winner asserted.** Statistical controls can reduce uncertainty; they cannot remove luck.
- The existing hub displayed third-party odds and derived performance with UNVERIFIED badges. That failed the user's explicit rule that unconfirmed values must be blank. This release withholds observation/output fields instead of treating a warning badge as permission to publish them.
- The automated hub preserves all **253 local records in 10 dataset tables**, while leaving **1,367 observation/output fields blank**, including unsupported identities, scores, quotes, projections, performance and correlations. These counts describe local file structure, not verified NBA facts. Every table row has an official/reference or primary project-evidence link; a URL's existence is **not** proof of a value.
- Research categories cover single moneylines, spreads, totals, individual props, same-game prop combinations and cross-game parlays. Each is a proposal, not a proven edge. Candidate/rule implementation remains in the [canonical registry](https://github.com/sassnarep3-star/Own6/blob/main/nba_lab/registry.py).
- Proposed selection requires permitted pregame inputs, independently estimated outcome distributions, executable prices and a frozen positive-EV rule. Combinations additionally require joint-probability calibration; raw-score Pearson correlation is not a substitute.
- Proposed qualification requires chronological holdouts, proper scoring and market benchmarks, clustered uncertainty, multiplicity control, risk reporting, preregistration and independent reproduction. Rewards are withheld until all eligibility requirements are established. No cash contest is operated by this change.
- **Full empirical completion is blocked by missing authorized data and value-level evidence.** No manual entry is requested or needed to build the site, but automation cannot supply permissions, certify historical snapshots or manufacture prospective results.

## Repository review and exact verification boundary

Read the existing coordination board before implementation and immediately committed/pushed the claim. Examined the current generators, checkers, workflows, data headers, source log, raw hub issues and relevant model-gate formula; checked open PR scopes before claiming. All changes are on the fixed Arena branch; no other session branch or overlapping implementation was created.

The prior repository contains several parallel sites and historical verification statements. This session did **not** reread every NBA score, regulation, historical snapshot or every line of inherited code. The phrase “verified this session” has been removed from this hub where it previously represented another session. Local recomputation, URL-domain checks and unit-test success are described as such, never as official-value verification.

### Directly checked official primary sources

| Source | What was actually checked | What it does not verify |
|---|---|---|
| [SciPy official source, pinned commit](https://github.com/scipy/scipy/blob/05d068ed2503fad79d5484ae09d55b50a682ec3b/scipy/stats/_stats_py.py#L4656-L4662) | Contents API payload decoded/read directly. Pearson documentation explicitly states that no correlation does not imply independence unless jointly normal. | Any NBA coefficient, joint betting probability, sample adequacy or causation. |
| [scikit-learn official cross-validation documentation, pinned commit](https://github.com/scikit-learn/scikit-learn/blob/d5a61d1149cb94a936d4b32212330f4ba8f24ce0/doc/modules/cross_validation.rst#L878-L905) | Contents API payload decoded/read directly. Time-series evaluation calls for future observations; time-aware and group-aware split guidance read. | Authenticity of supplied timestamps, sports-specific validity or demonstrated skill. |
| [scikit-learn Brier definition, pinned commit](https://github.com/scikit-learn/scikit-learn/blob/d5a61d1149cb94a936d4b32212330f4ba8f24ce0/sklearn/metrics/_classification.py#L3719-L3724) | Contents API payload decoded/read directly: mean squared difference between probability and actual outcome. Supports the paired-edge defect report. | Any source value or NBA performance estimate. |
| [Own6 official repository](https://github.com/sassnarep3-star/Own6) | Local checkout, authenticated GitHub PR/commit metadata and file provenance. | External source truth or a license for any data. |
| [GitHub Pages configuration API](https://api.github.com/repos/sassnarep3-star/Own6/pages) | Initial authenticated read: legacy build, public HTTPS site, `main:/`, status `built`. | The later release's deployment until its merge SHA is confirmed. |

Pinned excerpts and retrieval scope are in [publication policy](https://github.com/sassnarep3-star/Own6/blob/main/data/hub_publication_policy.json). All direct reads above are 2026-11-03. The network allowlist permits GitHub and package registries, **not NBA.com**. NBA links on the site are official references **not directly fetched in this session**. No new NBA `verified-direct` status is assigned. Older sessions' attributed evidence is retained in their raw ledgers, not silently upgraded.

## Dataset review

All following values are structural counts from committed CSV parsing. Source links identify the repository's own records, not official confirmation of their basketball contents.

| Dataset | Local records | Withheld fields per record | Evidence / source |
|---|---:|---:|---|
| Historical results | 92 | 6 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/games_results_2026-27.csv) |
| Dated slate results | 15 | 6 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/results_2026-11-02.csv) |
| Standings | 30 | 4 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/standings_live_2026-11-03.csv) |
| Ratings | 30 | 6 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/team_ratings_2026-27.csv) |
| Market quotes | 15 | 7 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/market_lines_2026-11-02.csv) |
| Model outputs | 15 | 6 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/our_lines_2026-11-02.csv) |
| Props | 7 | 7 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/player_props_2026-11-02.csv) |
| Forward game rows | 15 | 7 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/forward_test_2026-11-02.csv) |
| Forward summary rows | 30 | 2 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/forward_test_summary_2026-11-02.csv) |
| Correlation rows | 4 | 4 | [CSV](https://github.com/sassnarep3-star/Own6/blob/main/data/correlation_findings.csv) |

All ten tables contain one visible UNVERIFIED flag per record. Raw CSVs remain unchanged for provenance and independent review. Local record numbers do not identify a verified player or game. No official value-evidence acceptance or manual publication override is configured; altering that requires code/policy review rather than a user-input form.

## Irregularities and coordination requests

| ID | Finding | Disposition | Primary source |
|---|---|---|---|
| P-publish | UNVERIFIED odds, outputs and estimates were still visible in hub numeric cells. | Fixed in this hub: blank all unsupported observation/output fields. | [Generator](https://github.com/sassnarep3-star/Own6/blob/main/scripts/build_hub.py) |
| P-correlation | Earlier hub labelled raw-score correlations “usable” at a sample-size threshold and computed naive intervals for some rows. | Those usability labels and numeric estimates are not published; joint/residual validation is required. | [Earlier issue ledger](https://github.com/sassnarep3-star/Own6/blob/main/data/hub_flags.csv) |
| P-gates-brier | At inspected base, `nba_lab/gates.py` computes paired Brier edge with `(market_probability-model_probability)^2` instead of `(market_probability-outcome)^2`. Identical forecasts would yield a negative rather than zero paired edge. | Needs review. Requested repair by the active gate owner in PR #31; no cross-scope edit. No qualified result asserted here. | [Exact coordination request](https://github.com/sassnarep3-star/Own6/pull/31#issuecomment-6618275302) |
| P-archives | Older public sections still have weaker verification standards, legacy numbers, secondary odds and 31 advisory official-link gaps. | Needs review; explicitly flagged as archives, not newly verified. No claim that the entire site meets the row-evidence requirement. | [Existing source-check implementation](https://github.com/sassnarep3-star/Own6/blob/main/tools/check_site.py) |
| P-rights | No authorized gambling-use feed established; historical rights and Korean-law concerns require review. | Needs review. No legal conclusion or jurisdiction inference from the user's location. | [Existing project disclosure](https://github.com/sassnarep3-star/Own6/blob/main/README.md) |
| P-access | NBA official pages cannot be fetched under this session's network allowlist. | No verified NBA values published by this repair. | [Publication policy](https://github.com/sassnarep3-star/Own6/blob/main/data/hub_publication_policy.json) |

All current-scope unresolved findings are on the hub [Flagged for Review](https://sassnarep3-star.github.io/Own6/docs/hub/flagged.html) page and do not block the structural repair's release. Other sessions retain their implementation scopes; comments and this board coordinate requests.

## Verification performed before integration

- Hub generator: 12 deterministic pages; 335 source-linked table rows, including authored methodology and attributed review rows. All 253 dataset records accounted for; 1,367 empty unverified cells. Link presence is not factual verification.
- 12 new failure-path tests cover zero/number insertion, missing field/status, hidden elements/attributes, policy override, secondary links, deceptive domains, broken links and page removal.
- Full suite on pre-integration tree: **46 tests passed**, plus 6 subtests.
- Existing integration audit, release gate, generated review check, lab checker, report fail-closed checker, original link/source checker, data recomputation checker and verified-site checker pass. Existing strict site checker: 0 errors and **31 advisory gaps** outside this session's scope.
- Dependency install initially hit system Python's externally-managed guard; resolved using ignored `.venv/` and the existing pinned requirements. No system override or tracked dependency artifact.
- Source audit/recomputation scripts validate structure/arithmetic only; their “verified” labels are not adopted as new source checks.

## Release record

PR, merge SHA, final checks and Pages deployment will be recorded in this session's `COORDINATION.md` section after integration. No live-success claim is made before GitHub deployment metadata confirms the merged revision.
