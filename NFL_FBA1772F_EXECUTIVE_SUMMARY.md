# NFL Executive Summary — decision guide review (`fba1772f`)

**Date:** 2026-11-19 · **Standalone review site:** `docs/nfl-fba1772f/index.html` · **Detailed audit:** `audit/NFL_FBA1772F_REVIEW.md`

## Executive decision

The repository has a broad NFL research framework and multiple evidence packs, but this session did not independently establish authorization for gambling-use data, a licensed timestamped market archive, a leaguewide verified availability/depth feed, or a qualifying prospective strategy. The correct decision today is to **keep the system in research/shadow mode**: publish methods and evidence gaps, not picks, fabricated lines, profitability claims, or rewards implying skill.

## Recommended order

1. **Rights and source policy:** document per-source permission, purpose, retention, redistribution, and expiry before expanding capture or public output. NFL terms are a starting point for review, not a project license.
2. **Immutable point-in-time ledger:** preserve source, observation time, event key, raw hash, parser/schema version, conflicts, and model version. Retain raw data privately until terms are resolved.
3. **Singles-only shadow baseline:** preregister one simple model and controls; store each forecast as a probability with all inputs known at the cutoff. Keep chronological train/validation/final holdout boundaries.
4. **Verify result and market joins:** score only official results that reconcile to the event identity. Compare against a timestamped, licensed executable quote on the same market/line with vig and settlement policy stated.
5. **Add availability cautiously:** distinguish practice designation, announced starter, inactive, actual starter, and playtime. Injury is a timestamped change/surprise, not a static level. Do not infer depth from jersey number, experience, or salary.
6. **Gate leaderboard and combinations:** rank signal via prospective benchmark-relative proper scores and uncertainty; show staking separately. Lock parlays and prop combinations until joint probability and operator-specific settlement rules are directly validated. Declare demotion gates before evaluation.

## Important repository irregularities flagged

- **Suggestions mismatch:** dashboard advertises 12 reviewable proposals, yet the core CSV and rendered table contain only three; the research note describes twelve.
- **Unrendered recommendations:** the existing “recommended path” cites S06 and S08, which are not displayed in the suggestions table.
- **Injury-policy conflict:** Q02 cites a 2017 policy PDF while the existing flag register reports that URL returned 404 on 2026-11-13. The current policy endpoint was not externally re-read in this session.
- **Citation quality:** some official source links provide general context but do not support the recommendation, UI impact score, or prioritization judgment.
- **Full release not re-verified:** no repo-wide build, final link audit, Pages deployment check, or fresh source-by-source validation was performed for this isolated review.

Each irregularity is non-blocking for this standalone page and listed with an owner-facing remediation on `docs/nfl-fba1772f/flagged.html`.

## Questions that still block a defensible decision

1. What sources and uses are authorized, including retention and derivative publication?
2. Which licensed market source supplies executable open/close quotes and exact settlement semantics?
3. What is the stable event key and official result precedence for the backtest corpus?
4. Can each injury snapshot be replayed as known at the prediction cutoff, independently of cache?
5. Can one verified path identify official expected starters, actual starters, inactives, and playtime for every team?
6. Which frozen inputs and method produce side, total, then moneyline probabilities?
7. What prospectively registered thresholds qualify, demote, or reward a strategy?
8. Which proposed site/research task is selected, and which are explicitly deferred?

The companion Q/I/A page specifies known repository evidence, missing information, discovery steps, and official-source limitations for each. Unknown answers remain open rather than being inferred.

## Suggested human review

Review proposals in dependency order: rights/source matrix → immutable ledger → availability evidence chain → singles-only shadow protocol → proper-score leaderboard → joint-evidence gate for combos → per-strategy decision card. **No suggestion is selected or implemented automatically in this session.**

## Verification boundaries

This session inspected the core NFL page/register set and supporting local evidence artifacts listed in the audit. It did not fetch official web pages; links are for manual review, and external facts are not marked freshly verified. New-page local integrity can be checked with `python scripts/check_nfl_fba1772f.py`. That script does not validate external links or substitute for the final integration/site-deploy checks.
