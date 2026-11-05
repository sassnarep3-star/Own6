# Executive Summary — Own6 NBA Lines Research

## Final integration update — 2026-11-05

Session `arena/6eb8d991-own6` rebased onto concurrent `main` after PR #49, preserving the separate `docs/daily/` November 5 snapshot and all earlier sections. The decision below is unchanged: **zero strategies are qualified and no reward winner, current executable price, profitable edge or betting recommendation is published.**

Fresh direct reads in V28–V54 reconfirmed all 15 November 2 final scores and the scoped NBA/Korean policy claims. The original 30-team W-L ledger remains a November 3 historical match, not current standings; PR #49's November 5 daily capture is separately dated. The daily walk-forward and descriptive correlations are preliminary retrospective evidence with disclosed uncertainty, not an authorized data feed or an all-gate qualification. The assurance engine still has zero authorized observations and an empty leaderboard.

Four provenance defects were corrected without filling gaps: the NBA partner list no longer includes Brazil, Utah's dated W-L row cites standings, ESPN gamelogs are labelled third-party/secondary, and an unsupported commercial-status assertion was removed. Full record: [`audit/FINAL_INTEGRATION_REVIEW_2026-11-05.md`](../audit/FINAL_INTEGRATION_REVIEW_2026-11-05.md) and the [direct verification log](../data/verification_log.csv).

---

**Original assurance summary date:** 2026-11-03 · **Session:** `arena/74d27b5d-own6` · **Protocol:** v1.1.0

## Decision

Publish the research framework, source audit and fail-closed dashboard. **Do not publish a current betting line, measured correlation, profitable strategy or reward winner.** No authorized gambling-use data feed is configured, and no strategy has passed the validation gates. Luck cannot be eliminated; the protocol reduces false discoveries through rights, provenance, chronology, dependence-aware uncertainty, multiplicity control and frozen preregistration.

## Objective

Originate NBA moneylines, spreads, totals, player props, same-game prop combos and parlays; compare them with timestamped executable market prices; and rank only strategies that demonstrate market-relative skill on an untouched holdout. The leaderboard is a research-priority competition, not a payout system.

## What is delivered

1. **Assurance dashboard** — nine no-input pages: overview, strategies, lines/props, correlations, leaderboard, validation gates, sources, Flagged for Review and full repo audit. Every table row carries an official HTTPS source/reference link. Unavailable empirical values are blank and flagged.
2. **Current-tree audit** — `scripts/audit_repo.py` structurally scans every line of the non-generated text inventory, records file checksums, and reviews every legacy data record. The current review leaves legacy numeric values unverified unless separately matched to an authorized official snapshot. A URL or checksum is not fact certification.
3. **Official source register** — 20 directly read official sources and two explicitly partial reads, each with supports/does-not-support scope. Sources include NBA Terms/FAQ/glossary/injury policy, DraftKings odds/spread/parlay help, scikit-learn, NIST, SciPy, statsmodels and GitHub Pages documentation.
4. **Hardened empirical engine** — fair American pricing without invented vig; strategy/market and edge/EV contracts; artifact-bound audit evidence; de-vigged same-line CLV sidecar; strict training-only residuals retaining zeros; slate-clustered correlation intervals; joint-sample combo gates; Bonferroni across actual qualification statistics; and an all-gate leaderboard.
5. **Signal research** — six frozen candidate specifications covering singles, player props, prop combos and a two-game parlay. They are hypotheses, not verified edges. Adding a candidate after inspecting holdout results requires a new preregistered family and holdout.
6. **Validation protocol v2** — ten gates: rights, provenance, chronology, sample/precision, market-relative proper scores, post-vig ROI, comparable CLV, multiplicity, joint dependence and frozen auditable ledger.

## Key findings

- **Rights blocker.** [NBA Terms §9](https://www.nba.com/termsofuse#nba-statistics) restricts gambling use of NBA Statistics; §1 restricts public reuse. The [Stats FAQ](https://www.nba.com/stats/help/faq) does not offer a download. No license is inferred.
- **Legacy pricing defect repaired upstream.** The earlier legacy model used incorrect American-odds denominators. Concurrent PR #29 repaired the formula and regenerated its outputs. Historical ESPN quotes remain secondary-source and unverified even after the arithmetic repair.
- **Empirical gate defects repaired in this session.** Self-asserted booleans, zero-dropping residual parsing, raw-price CLV, weak combo dependence and win-count-only multiplicity were replaced with artifact-bound, dependence-aware checks.
- **Internal consistency is not source verification.** Earlier “213 checks” demonstrate agreement among local tables, not independent confirmation of scores, ratings or odds.
- **No empirical qualification.** The authorized ledger is empty. Correlation, edge, ROI and CLV fields remain blank; the leaderboard is empty.

## Validation gates

| Gate | Requirement | Official reference |
|---|---|---|
| G01 | Rights and market permission | [NBA Terms](https://www.nba.com/termsofuse#nba-statistics) |
| G02 | Field-level provenance | [NBA Terms](https://www.nba.com/termsofuse#nba-statistics) |
| G03 | Chronological walk-forward | [scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html) |
| G04 | Sample floors + power/precision audit | [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) |
| G05 | Market-relative Brier and log-loss improvement | [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html) |
| G06 | Post-vig ROI lower bound | [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda352.htm) |
| G07 | Comparable de-vigged CLV | [DraftKings odds formulas](https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB) |
| G08 | Family-wise qualification multiplicity | [NIST Bonferroni](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm) |
| G09 | Joint dependence for combos | [SciPy Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| G10 | Frozen auditable ledger | [Repository contract](https://github.com/sassnarep3-star/Own6/blob/main/research/empirical/DATA_CONTRACT.md) |

## What remains unverified

- Current/historical executable odds, player-prop prices, strategy-qualifying joint dependence, ROI, CLV and strategy performance from an authorized ledger. The separate daily section contains descriptive estimates, not qualified performance.
- Resolution of the Korean whole-law/Article 26 effective-date discrepancy and legal applicability. Article 26(1), 26(2)(1) and 26(2)(2) were directly read; other article bodies are not freshly certified by final integration.
- Specific NBA prop restrictions reported only by press sources.
- Any legal applicability or data-use permission.

These are published on **Flagged for Review** with source links. They block empirical qualification, not publication of the research framework.

## Reproduce

```sh
python -m pip install -r requirements-empirical.txt
python scripts/audit_repo.py
python scripts/run_lab.py
python scripts/build_assurance.py
python scripts/check_assurance.py
python -m pytest -q tests
```

The bundled empty ledger reports `not_run`, zero observations, zero qualified strategies and an empty leaderboard. Synthetic test fixtures never enter the report.

## No betting advice

This repository does not place bets, accept stakes, distribute rewards or provide picks. A strategy that eventually passes can still lose. The current evidence supports a research framework, not a profitable edge.
