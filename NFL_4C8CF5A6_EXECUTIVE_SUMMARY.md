# NFL 4c8cf5a6 — Executive Summary

Session `arena/4c8cf5a6-own6`, branch `arena/4c8cf5a6-own6`, base `ffbbce6620ef4a2006c70d1d780a105011231274` (origin/main, merged PR #122).
Live site: https://sassnarep3-star.github.io/Own6/docs/nfl-4c8cf5a6/

## Where the programme actually stands

The owner's brief contains 73 requirements across prices & results, origination, leaderboard,
depth & availability, injuries, correlation & luck, and site & data.

- 2 cleared
- 5 cleared as inherited repo claims
- 23 structural (schema/code exist, no data behind them)
- 40 blocked by a named gate
- 3 rejected by policy
- 2 open

## The binding blockers

1. No official market-price source exists. Until one does, residuals, closing-line value, vig
   decomposition, and any price-based backtest cannot be published. The owner's ordering rule
   (R-20) says to decide the price-data policy first.
2. No verified depth-order source for all 32 clubs. Fourteen requirements sit behind this,
   including the entire backup-deficiency feature. Resolved before the feature is built.
3. No official inactive list captured. The injury register is verifiable weekly, but "did the
   player actually play" is unanswerable without inactives, so Questionable cannot be calibrated
   and no designation may become a model feature.
4. Zero strategies pre-registered. No rule text, sample window, and gates are committed before
   any evaluation window, so no strategy can qualify and the leaderboard stays empty.

## What this session verified from official pages

This session cannot reach nfl.com (sandbox outbound limit: github.com / api.github.com only), so
it performed no new NFL official-source reads. Verified cells are empty; prior session reads are
inherited as labelled repo claims. Everything not confirmed is left blank and flagged — never
inferred, never filled in.

## The decision board

- 15 suggestions with 30 option paths; decision columns blank by design (owner chooses the path
  before anything is implemented)
- 40 questions with what we have and what we lack
- 20 information gaps with the route that closes each
- 10 declared strategies, 0 registered, 0 qualified
- 20 flags published on the Flagged for Review page; none block the merge

## What is deliberately missing

No prices, no odds, no closing-line value, no vig decomposition, no leaderboard rows, no
profitability claim, and no statement that any strategy is skillful. Those cells are blank because
the evidence does not exist yet — filling them would be the exact failure mode this project is
built to avoid.

## Verification

- Builder: `scripts/build_nfl_4c8cf5a6.py` — 20 deterministic HTML pages, zero `"` characters,
  compiles cleanly
- Verifier: `scripts/check_nfl_4c8cf5a6.py` — PASSED all 26 checks
- Tests: `tests/test_nfl_4c8cf5a6.py` — OK (6/6)
- CI: `.github/workflows/nfl-4c8cf5a6-ci.yml` (build, verify, test)

## Integration record

- PR: https://github.com/sassnarep3-star/Own6/pull/134
- Merge result: PR #134 merged into `main` with merge commit `5765da8e7887b25cd2816be94430be7c230f9441`
- Pages deploy: GitHub Pages build reached status `built`; live site at
  https://sassnarep3-star.github.io/Own6/docs/nfl-4c8cf5a6/

Research only. No wagers, stakes, picks, payouts or profitability claims. Luck cannot be
eliminated; the protocol reduces false discoveries through rights, provenance, chronology,
dependence-aware uncertainty, multiplicity control and frozen preregistration.
