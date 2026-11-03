# Independent NBA hub evidence review

Session: `arena/fa10f2e0-own6` · direct source review: 2026-11-03 UTC.

## Executive summary

**Decision: research-only; no betting deployment, qualified rank or reward winner.** The repository contains model utilities, strategy proposals, historical snapshots and fail-closed validation machinery. These do not establish profitable skill. Singles, parlays and prop combinations require authorized pre-decision data, independently checked provenance, chronological holdouts, proper scoring and market benchmarks, uncertainty accounting and multiple-testing controls. Joint models need paired observations and out-of-sample joint calibration; raw-score correlations are not a substitute. No method eliminates luck.

A warning badge beside an unconfirmed number does not satisfy the user's blank-value requirement. No licensed feed is configured, no input or credential is requested, no unauthorized scraper is started, and no results are fabricated by this review. Missing evidence remains missing.

**Coordination:** During final integration, newly opened [PR #36](https://github.com/sassnarep3-star/Own6/pull/36) revealed an earlier concurrent claim on the hub repair. This session withdrew its duplicate hub generator/checker/page implementation and handed that work to the earlier owner. Notification: [coordination comment](https://github.com/sassnarep3-star/Own6/pull/36#issuecomment-6618316111). The retained work is additive: independent reference-integrity gate, adversarial tests, this report and `docs/hub-evidence/index.html`. The owner's versioned publication-policy checker remains canonical. No other session's implementation is overwritten. Full development/test/handoff history remains in `COORDINATION.md`; withdrawn-prototype test counts are not final-release counts.

## Official-source review actually performed

| Source | What was read | Supported finding | Not established |
|---|---|---|---|
| [NBA Terms of Use](https://www.nba.com/termsofuse), chunks 0, 3, 4 | §1 ownership/public reuse; §9 across chunks 3–4 | §1 restricts public republication/reuse absent permission; §9(ii) limits statistics use to legitimate news reporting or private noncommercial purposes, and §9(iv) bars use in connection with gambling including legal gambling | No permission, data license or jurisdiction-specific legal opinion |
| [NBA Stats FAQ](https://www.nba.com/stats/help/faq), chunk 0 | Download/CSV response | NBA says its statistics are not available for download for academic/personal use and are for viewing on NBA.com/Stats | Does not supply/authorize a gambling-related dataset; no numerical data extracted for models |
| [NBA Stats glossary](https://www.nba.com/stats/help/glossary), chunk 0 only | Initial entries and page structure; partial | Official definitions reference exists | Later PACE/OffRtg entries, numeric ratings, player values and betting performance were not read/verified here |
| [Historical reverification ledger](https://github.com/sassnarep3-star/Own6/blob/main/data/reverification_results_2026-11-03.csv) | All 13 records locally | Project records earlier session claims of source reads | Those numerical official-page reads were not repeated or newly certified |
| [Independent reference gate](https://github.com/sassnarep3-star/Own6/blob/main/tools/hub_reference_gate.py) | Entire retained source and fixture regressions | Implementation checks HTTPS, host-label/path boundaries, primary/project versus secondary references, table shape and declared blank cells | Link integrity does not prove a source supports a real-world value or is externally reachable |

Source-text review is separate from offline publication checks. No numerical NBA/statistical scraping was performed. The user's jurisdiction is not inferred from prior Korea-specific research. NBA legal text is reported, not turned into jurisdiction-specific advice.

## Flagged for Review

Published on [`docs/hub-evidence/index.html`](https://github.com/sassnarep3-star/Own6/blob/main/docs/hub-evidence/index.html#flagged).

| ID | Finding | Disposition / remaining condition | Primary reference |
|---|---|---|---|
| HE01 | Unverified market/ratings numbers previously visible with warning badges | Strict blank-value repair delegated to the earlier owner; accepted source evidence remains absent | [PR #36](https://github.com/sassnarep3-star/Own6/pull/36) |
| HE02 | A valid link and matching arithmetic are not source-content verification | Independent gate rejects secondary-only rows and deceptive URLs but makes no factual-verification claim | [Reference gate](https://github.com/sassnarep3-star/Own6/blob/main/tools/hub_reference_gate.py) |
| HE03 | Sample-size cutoff or raw Pearson correlation does not establish usable joint pricing | Need authorized paired training data and out-of-sample joint validation; no coefficient supplied by this review | [Methodology](https://github.com/sassnarep3-star/Own6/blob/main/research/METHODOLOGY.md) |
| HE04 | Rights and source-value evidence remain incomplete | No feed, wagering or reward payout activated; research-only wording is not permission | [NBA Terms §9](https://www.nba.com/termsofuse#nba-statistics) |
| HE05 | Older sections retain different evidence standards and legacy gate claims | Review archives, not certified feeds; full qualification is separate from process score | [Coordination history](https://github.com/sassnarep3-star/Own6/blob/main/COORDINATION.md) |

## Verification scope and commands

The independent gate's primary-reference rule accepts first-party NBA/official methods documentation and this project's own GitHub records. This repo is primary only for repository implementation/findings, not independent evidence of NBA values. Explicit secondary roles never qualify a row. Legacy templates without role attributes are classified as references only, never as verified values. Exact pinned upstream method URLs from the hub owner's implementation are recognized; arbitrary GitHub repositories are not.

- `python3 -m unittest discover -s tests -p test_hub_evidence.py -v`: adversarial fixtures for deceptive hostnames, credentials/ports, arbitrary GitHub records, dot-segment project paths, source-role mismatches, secondary-only rows, missing blob files, table widths and nonempty unverified cells.
- `python3 tools/hub_reference_gate.py`: independent published-hub reference/structure check. The owner's `scripts/check_hub.py` remains responsible for complete dataset/record/field coverage and fail-closed policy enforcement. This helper does not replace or weaken it.
- Existing integration, release, lab, source-coverage and original-site checks are re-run on the combined tree before merge. Internal consistency is not upgraded to factual verification.
- GitHub Pages deployment success and live content readback are recorded separately in `COORDINATION.md`; neither proves historical numerical facts.

Full independent line-by-line external verification of every historical repo claim is **not completed**. Remaining values cannot be invented or inferred to fill that gap. Historical flags and old section sites remain reviewable, and their original “verified”/“fixed” wording is not newly certified by this review. Nonblocking flags allow a clearly labelled research publication, not a claim of qualified betting skill.
