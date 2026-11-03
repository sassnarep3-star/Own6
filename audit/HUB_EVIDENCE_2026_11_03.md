# NBA hub evidence-boundary audit and executive decision

Session: `arena/fa10f2e0-own6` · review date: 2026-11-03 UTC.

## Executive summary

**Decision: research-only; no betting deployment, qualified leaderboard rank or reward winner.** The repository contains model utilities, strategy proposals, historical snapshots and fail-closed validation machinery. That does not establish profitable skill. Singles, parlays and prop combinations require authorized pre-decision data, independently checked provenance, chronological holdouts, proper scoring and market benchmarks, uncertainty accounting and multiple-testing controls. Joint models need paired observations and out-of-sample joint calibration; raw-score correlations are not a substitute. No method can eliminate luck.

The unified hub now withholds unverified numerical scores, standings, ratings, quotes, projections, performance summaries and correlations, rather than displaying them with warnings. It preserves all underlying rows as archive identifiers and links to the unchanged raw files. No licensed feed is configured, no input or credential is requested, no unauthorized scraper is started, and no results are fabricated. The lack of verified inputs is an evidence boundary, not an invitation to infer values.

This is a **narrow incremental hub repair**, not a claim that all historical repository facts have been independently checked. Several other sessions have active PRs. Their scopes and all historical records are preserved. Legacy sites may still publish unverified numbers and contradictory gate claims; HE07 flags this explicitly.

## Official-source review (direct tool reads)

| Source | What was actually read | Supported finding | Not established |
|---|---|---|---|
| [NBA Terms of Use](https://www.nba.com/termsofuse), chunks 0, 3, 4 | §1 ownership/public reuse; §9 across chunks 3–4 | §1 restricts public republication/reuse absent permission; §9(ii) limits statistics use to legitimate news reporting or private noncommercial purposes, and §9(iv) bars use in connection with gambling including legal gambling | No legal opinion, permission, jurisdictional determination or blanket license is provided |
| [NBA Stats FAQ](https://www.nba.com/stats/help/faq), chunk 0 | Download/CSV question and response | NBA says its statistics are not available for download for academic or personal use; the page is for viewing on NBA.com/Stats | Does not supply or authorize a gambling-related dataset; no numerical data extracted for models |
| [NBA Stats glossary](https://www.nba.com/stats/help/glossary), chunk 0 only | Initial glossary entries and page structure | An official definitions reference exists | Later PACE/OffRtg entries, numeric team ratings, player values, betting edge and empirical performance were not verified in this session |
| [Repository hub generator](https://github.com/sassnarep3-star/Own6/blob/main/scripts/build_hub.py) | Entire pre-repair generator and replacement, local line-by-line code review | Previous publication displayed unverified secondary quotes and stale ratings; repaired value cells are empty | A code/source link is primary evidence of the project implementation, not independent verification of NBA facts |
| [Previous reverification ledger](https://github.com/sassnarep3-star/Own6/blob/main/data/reverification_results_2026-11-03.csv) | All 13 records locally | Records prior session claims of reads for a subset of scores | Those official numerical source reads were not repeated or newly certified |

Source text review is distinct from the offline checks below. Source links support only the stated scope. NBA legal text is reported, not interpreted as jurisdiction-specific advice. The user's country is not inferred from historical Korea-specific work. No new numerical NBA/statistical scrape was performed.

## Reproducible findings and dispositions

| ID | Finding | Disposition | Primary reference |
|---|---|---|---|
| HE01 | Warning badges left unconfirmed values visible | Withhold them as actual empty cells, retain archive keys and raw links; no dependent model values promoted | [Generator](https://github.com/sassnarep3-star/Own6/blob/main/scripts/build_hub.py) |
| HE02 | Checker accepted secondary-only source rows and unsafe hostname suffixes | Validate HTTPS, host-label boundaries, project-specific GitHub paths and explicit source roles; add adversarial regressions | [Checker](https://github.com/sassnarep3-star/Own6/blob/main/scripts/check_hub.py) |
| HE03 | A sample-size threshold labelled raw correlations usable; a copula rule was treated as universal | Coefficients/intervals withheld; paired residual/joint validation required; no claim that zero correlation proves independence | [Methodology](https://github.com/sassnarep3-star/Own6/blob/main/research/METHODOLOGY.md) |
| HE04 | Rights remain absent | Fail closed; no scraping, live feed or automated betting | [NBA Terms](https://www.nba.com/termsofuse#nba-statistics) |
| HE05 | Hub's subset of legacy gates could be confused with full lab qualification | No legacy pass/score/rank/reward claims adopted; qualification delegated to the versioned all-gate lab | [Gate implementation](https://github.com/sassnarep3-star/Own6/blob/main/nba_lab/gates.py) |
| HE06 | Historical read claims and arithmetic could be mistaken for independent verification | Historical evidence explicitly labelled and numeric fields blank; no new source-certification claim | [Historical ledger](https://github.com/sassnarep3-star/Own6/blob/main/data/reverification_results_2026-11-03.csv) |
| HE07 | Other historical sections retain different evidence standards | Linked as review archives, not certified feeds; needs review, does not block publication | [Coordination board](https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md) |

All historical flags are preserved without silently rewriting their wording. A historical “fixed” or “verified” status in a flag is not a new certification by this session. Each flag row links the actual primary project record plus its historical citation, rather than laundering a press source into official verification.

## Scope and verification procedure

1. Reviewed repository tree, all coordination records, current Pages configuration, open PR file scopes, hub builder/checker, all hub inputs and published hub pages. The whole repository's numerical claims were **not** independently confirmed against official sites.
2. Claim committed/pushed before implementation on the environment-fixed branch. Initial pull of the not-yet-created remote branch returned “remote ref not found”; pulled/rebased `origin/main` before the initial branch push instead. No other branch created, checked out or pushed.
3. Rebuild with `python3 scripts/build_hub.py`. All stored result entries, standings/ratings entries, market/prop entries, forward-test rows and metrics, legacy strategy IDs, correlation rows, source registry entries and historical flags remain indexable. Counts are repository counts, not externally verified NBA totals.
4. Run `python3 scripts/check_hub.py`: exact category pages, working internal links, one heading per page, table widths, empty declared-unverified cells, source-role/host validation and local existence of project blob targets. These checks cannot prove page contents support a value or that external sites are reachable.
5. Run regression and existing release suites. No test is reported as passing until actually executed; final results and deployment are appended to the coordination log.
6. PR/merge and Pages confirmation use GitHub's authenticated API/CLI. API deployment success alone is not a live content read; report those separately.

## Evidence still required before qualification

Authorized timestamped pre-event prices/results and clear rights; complete field-level independent source evidence; frozen features and all trials; realistic execution/vig/push handling; untouched future holdout; calibrated probability forecasts and comparable market baseline; event/slate-aware uncertainty and multiplicity correction; validated joint-tail behavior for combinations; all implemented gates passing. No strategy winner, rank, return or correlation is filled in to compensate for missing evidence.

Flagged items are non-blocking publication disclosures, not completed evidence validation. No claim that all project requirements can be met by inventing a dataset or removing randomness is made.
