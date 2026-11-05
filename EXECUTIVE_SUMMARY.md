# Executive Summary — Own6: Originate Your Own NBA Lines

## Integrated current status — 2026-11-05 (session `arena/6eb8d991-own6`)

**Decision:** publish the integrated research, dated evidence and Flagged for Review disclosures. **No strategy is qualified, no leaderboard reward is awarded, and no current executable line, profitable edge or betting recommendation is published.** The assurance engine remains fail-closed with zero authorized observations. The separate daily snapshot contains preliminary retrospective estimates; it does not change that qualification decision or establish NBA data-use permission.

- **Fresh independent score review:** all 15 November 2 finals were opened again on their official NBA game pages on November 5 and matched the dated ledger, including NOP–MEM Final/OT. Direct-read entries V28–V42 and per-game links are in [`data/verification_log.csv`](data/verification_log.csv) and [`audit/FINAL_INTEGRATION_REVIEW_2026-11-05.md`](audit/FINAL_INTEGRATION_REVIEW_2026-11-05.md).
- **Policy review:** Terms §§1/6/9, Stats FAQ, prediction-market release, Korean whole-law header and Article 26(1)/(2)(1)/(2)(2) were freshly read (V43–V54). The Korean effective-date discrepancy and NBA reuse/gambling-use questions remain open; no legal conclusion or license is inferred.
- **Two standings dates, not one “live” truth:** the original 30 rows are a **2026-11-03 historical match**, not current November 5 standings. A concurrent merged PR #49 added a separate dated [November 5 daily snapshot](docs/daily/standings.html). Neither capture should be silently substituted for the other.
- **Preliminary daily analysis is not qualification:** the daily section's walk-forward signal test and descriptive correlations have their own sample/uncertainty disclosures. They are not closing-line evidence, authorized sportsbook prices, prop-combination validation or an all-gate leaderboard result. See [`docs/daily/signals.html`](docs/daily/signals.html) and [`docs/daily/validation.html`](docs/daily/validation.html).
- **Provenance corrections:** removed an erroneous Brazil entry from the official-partner summary; corrected Utah's standings citation; relabelled ESPN gamelogs as third-party/secondary; removed an unsupported commercial-purpose assertion. Unsupported odds, props, ROI, CLV and strategy-qualifying correlations remain blank. Public flags F28–F29 record the dated-source limitation and corrections.
- **Integration provenance:** concurrent PR #49 merged the same five stale PRs while this review was underway. This branch retained both coordination records, rebased onto that work and kept only its unique source-review changes; no daily, coverage or other session work was discarded.

The sections below are dated historical reviews preserved for provenance. Where their wording differs, this integrated status and the current fail-closed assurance report govern the release decision.

---

## Earlier current-status review (session `arena/269a73e2-own6`, 2026-11-03)

**Bottom line.** The project has a working framework for originating lines, pricing parlays with correlation, and gating strategies. It has **no validated strategy, no qualifying leaderboard entry, no verified odds, and no verified correlation estimate.** No edge is claimed. Rewards are non-monetary research priority only. Nothing here is betting advice.

**Biggest open issue: NBA.com rights, not statistics.** NBA.com Terms of Use §9(ii) allows NBA Statistics only for "legitimate news reporting or private, non-commercial purposes", and §9(iv) bars use "in connection with any gambling activity (including legal gambling activity)". Verified text: [NBA.com Terms of Use](https://www.nba.com/termsofuse), read 2026-11-03. The sub-site `docs/own6/` republishes 92 NBA game results with per-game nba.com links (flags F17, F26). This session did not re-fetch those nba.com pages, because doing so would add to the same use. The owner or counsel must decide before anything else is published from that dataset. Flags do not block the merge.

**What this session verified (each with a link in the audit or on the site):**

| Check | Result | Source |
|---|---|---|
| Landing page on `main` | Had unresolved merge-conflict markers. Fixed (F18). | [docs/index.html](docs/index.html) |
| Empirical lab tables | Printed `<generator object>` instead of rows. Fixed (F19). | [scripts/build_lab.py](scripts/build_lab.py) |
| Verified-site rebuild | Dropped the Terms caution. Fixed (F20). | [scripts/build_site.py](scripts/build_site.py) |
| Correlation `home_score_vs_away_score` | r = 0.2004, n = 92, reproduced exactly. 95% CI −0.005 to 0.389; p = 0.055. Not significant (F21). | [data/correlation_findings.csv](data/correlation_findings.csv), [data/games_results_2026-27.csv](data/games_results_2026-27.csv) |
| Correlation `same_date_game_margins` | r = 0.1052, n = 357, reproduces only in one arbitrary pair order. Symmetric version gives 0.0927. Not valid (F22). | same |
| Correlation `teammate_PTS_Mitchell_Allen` | r = −0.4222 on n = 6. 95% CI −0.919 to 0.592. Source rows not in repo (F23). | same |
| Correlation `rest_diff_vs_home_margin` | r = −0.0162, n = 76. Rest input not in repo, so unverifiable (F25). | same |
| Alberta problem-gambling helplines | AGLC Self-Exclusion Program **1-844-468-8034**; Alberta Health Services Addiction Helpline **1-866-332-2322**. Shown in the site footer. | [AGLC common gaming questions](https://aglc.ca/gaming/common-gaming-questions); [AGLC resources](https://aglc.ca/training/reel-facts-vlt-staff-training/resources) |
| Official-source gate | Every external link in the strict pages is in the verified registry. Two AGLC rows were added (V26, V27). | [data/verification_log.csv](data/verification_log.csv) |
| Engine and checks | `pytest tests/` 20/20 pass with pinned dependencies. `verify_data.py` 213/213. `check_lab.py`, `check_site.py`, `linkcheck.py` and `build_review.py --check` pass. | scripts in [`scripts/`](scripts/) and [`tools/`](tools/) |

**Not verified, and left blank on purpose:** odds and closing lines (no official odds feed exists; ESPN and DraftKings data are secondary); player and team statistics (see F26); every correlation estimate that is not reproducible; any win rate, ROI, CLV or backtest result. The sandbox can only reach GitHub, npm and PyPI, so the live `github.io` site is checked after deploy through the GitHub Pages API and the fetch tool.

**Leaderboard.** Empty by design. The empirical lab reports `not_run` with zero observations and zero qualified strategies. The root site has no verified results to rank.

**Next steps for the owner (none block the merge):**
1. Decide on NBA Terms §9 (F17, F26): obtain permission or counsel review, or remove NBA-derived numbers from public pages.
2. Add the rest, same-date and gamelog datasets with official sources and checksums, or keep those values blank (F22, F23, F25).
3. Publish confidence intervals next to every correlation, or remove the value (F21).
4. Prune the duplicate coordination block and record the `arena/325834c9-own6` session (F27).

Full per-item record: [audit/REPO_REVIEW.md](audit/REPO_REVIEW.md) (section "Addendum — session arena/269a73e2-own6"). Register: [docs/verified/flagged.html](docs/verified/flagged.html).

---

**Date:** 2026-11-02 (UTC) · **Status:** combined `main` after integration of parallel sessions' work (PRs #1–#7) and the independent verification pass by `arena/a6ccf588-own6`.
**Evidence rule:** no NBA statistic, price, correlation, ROI or backtest result is asserted unless it is quoted from an official source with a link. Unconfirmable values are blank and published on the Flagged for Review page. Nothing is inferred or filled in. Every official URL used was retrieved **directly** from its official host on 2026-11-02 (not from search snippets); the line-by-line record is in [`data/verification_log.csv`](data/verification_log.csv) and [`audit/VERIFICATION.md`](audit/VERIFICATION.md).

## Objective

Originate your own NBA lines (spread, total, win probability), player-prop projections and correlated parlay/SGP prices. Treat strategy development as a leaderboard competition that rewards **skill, not luck**: every strategy must pass explicit validation gates before it can be ranked, and the ranking must reward the worst plausible skill estimate rather than the best observed outcome.

## The system

| Component | What it does | Official basis |
|---|---|---|
| Own lines (`src/own6/lines.py`) | PACE × OffRtg/DefRtg multiplicative matchup → fair spread, total, home win probability; home advantage and margin SD fitted from a game log, never hard-coded | [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) — PACE = "possessions per 48 minutes", OffRtg = "points scored per 100 possessions", NetRtg = `OFFRTG - DEFRTG` |
| Player props (`src/own6/props.py`) | Projected minutes × shrunk per-minute rate; normal-approximation P(over) with continuity correction | [NBA Stats overview](https://www.nba.com/stats/overview); [NBA Official injury report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| Parlays / prop combos (`src/own6/parlay.py`) | Gaussian-copula joint probability using Pearson ρ estimated from paired residuals with `n` reported; independence only as a labelled special case | [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| Validation gates (`src/own6/validation.py`) | G1 walk-forward · G2 n≥200 · G3 Brier/log-loss vs market · G4 CLV t≥2 · G5 exact binomial + Bonferroni across all strategies tried · G6 bootstrap 95% ROI CI lower bound > 0 · G7 correlation honesty · G8 immutable pre-game ledger | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html), [scikit-learn calibration](https://scikit-learn.org/stable/modules/calibration.html), [Brier score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html), [NIST binomial](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm), [Bonferroni](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html), [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) |
| Leaderboard (`src/own6/leaderboard.py`) | Score = lower confidence bound of ROI + CLV + calibration edge; small-sample heaters ineligible | [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) |

**Tests:** 5/5 pass via [`tools/run_tests.py`](tools/run_tests.py) (stdlib runner; `pytest` is not installed in this sandbox). The demo in `examples/demo_synthetic.py` uses synthetic numbers only and is explicitly labelled "NOT NBA data".

## Strategy families (hypotheses, NOT proven edges — each must pass G1–G8)

| Family | Market | Signal hypothesis | Official inputs |
|---|---|---|---|
| S-A | Single bet — spread/total | Own fair line deviates from market by a threshold derived from fitted margin SD | [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) |
| S-B | Single bet — totals | Pace-blend extremes vs market-implied pace | [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) |
| S-C | Player prop | Recent-form props overreact; shrunk per-minute rate beats the market line | [NBA Stats overview](https://www.nba.com/stats/overview), [injury report](https://official.nba.com/nba-injury-report-2026-27-season/) |
| S-D | Parlay / same-game combo | Positive correlation makes independence multiplication misprice joint probability | [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) |
| S-E | Meta (all markets) | Only take prices that systematically beat the close (CLV-first) | [NBA official operators list](https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2) |
| S-F | Player-prop combos | Teammates' counting stats compete for finite possessions (USG% constraint) | [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) |

None has been validated. No win rate, ROI, CLV or hit rate is published.

## Correlation values

**No correlation coefficient is published.** Determining ρ requires paired residual histories computed from official box scores; none exists in this repository. The measurement plan, with every value cell blank and flagged, is on [Correlations](docs/correlations.html). Correlation methodology is the Pearson coefficient ([SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)); the copula joint probability is a project implementation, not an official NBA statistic.

## Removing luck

1. **Walk-forward only** — no parameter fitted on data after the bet date ([hold-out rationale](https://scikit-learn.org/stable/modules/cross_validation.html)).
2. **Sample size** — n ≥ 200 settled bets per strategy (disclosed project policy).
3. **Calibration** — Brier and log-loss must beat a market baseline on the same games ([scikit-learn](https://scikit-learn.org/stable/modules/calibration.html)).
4. **Closing-line value** — mean CLV > 0 with t ≥ 2, i.e. beating the market, not just outcomes.
5. **Multiple testing** — exact binomial p vs breakeven, Bonferroni-corrected across *all* strategies ever tried ([NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm), [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html)).
6. **Uncertainty** — 95% bootstrap ROI CI lower bound > 0 ([SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html)).
7. **Correlation honesty** — joint probabilities from measured ρ, `n` disclosed; never silent independence.
8. **Ledger integrity** — pre-game timestamped logging, no deletions.
9. **Ranking** — lower confidence bound of ROI, so a short heater cannot win.

## Verified official facts (quoted, not inferred)

- [NBA Stats FAQ](https://www.nba.com/stats/help/faq): "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats"; advanced stats go back to 1996-97, base stats to 1946-47; advanced stats update 10–15 minutes after games.
- [NBA Official injury report](https://official.nba.com/nba-injury-report-2026-27-season/): teams must designate participation status by 5 p.m. local time the day before a game; reports are updated continually.
- [NBA NBABet](https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2): official gaming partners/operators list dated **July 9, 2026**. The [Nov 4, 2021 announcement](https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners) is historical, not a current-status source.
- [NBA official release, Oct 26, 2026](https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets): an integrity framework with "limitations on permissible markets" and restrictions "aligned with the NBA's latest sports betting restrictions" — **the specific restrictions are not enumerated on that page**, so they remain blank/unverified. Press reports are not official sources.
- [NBA.com schedule](https://www.nba.com/schedule): Week 3 (Nov 2–Nov 8), Monday November 2, 15 games — date-specific, re-retrieve on the date of use.
- [NBA Stats overview](https://www.nba.com/stats/overview): "Yesterday's Leaders" dated 11/01/2026 with points/rebounds/assists leader tables.

## Data, legality and deployment notes

- No official bulk CSV download exists; inputs must be exported from official NBA pages with a retrieval date, and used consistently with the site's terms.
- Only bet where legal with licensed operators; this repository is research/analytics, not betting advice, and recommends no bet.
- **Flagged legal/rights concern (I-24, needs review):** the [NBA.com Terms of Use](https://www.nba.com/termsofuse) §1 states "No Basketball Content from the Services may be … linked to, or otherwise used except as provided in these Terms of Use without the written permission of the Operator"; §9 states "the NBA Statistics may not be used in connection with any gambling activity (including legal gambling activity)" and that statistics "may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes". This project ingests **no NBA Statistics values** (all model inputs are blank/unverified) and links official pages only as citations, but applicability to a gambling-related research site is undetermined. Obtain written permission / qualified legal review before using NBA Statistics in betting models or republishing NBA content. This is a flagged concern, not a legal conclusion, and does not block publication (request A28-REQ-01 from session `arena/a28a2ee1-own6`).
- Korean-law exposure is flagged separately in the [verified data section](docs/verified/legal-kr.html); no legal conclusion is asserted here.
- GitHub Pages is configured as a **legacy `main:/` publishing source** with a root `index.html` redirect to `docs/`; an API attempt to switch the source to `/docs` returned HTTP 403 ("Resource not accessible by integration"). Publishing-source options are documented by [GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). The live URL is <https://sassnarep3-star.github.io/Own6/>.
- The repository has **no LICENSE file** ([GitHub API](https://api.github.com/repos/sassnarep3-star/Own6) reports `license: null`).

## Integration re-verification status (2026-11-02 — session `arena/71464040-own6`)

- **Line-by-line re-check:** all 15 Nov 2 schedule rows, all 13 statute rows, and both official policy rows re-matched against live official pages; registry S1–S23 confirmed by direct retrieval (evidence: `data/verification_log.csv`, details in `COORDINATION.md`).
- **Checks run:** `pytest` 5/5 (local venv) and `tools/run_tests.py`; `scripts/check_site.py` = 9 pages, no broken internal links; `examples/demo_synthetic.py` runs (synthetic only); live root → `docs/` redirect, `docs/verified/` and `docs/review/` all confirmed by live fetch after the latest Pages build.
- **Rewards gate (important):** `data/methodology.json` G1 (Korean legal review, 국민체육진흥법 Art. 26) is **open/FAIL** — no leaderboard rewards are configured and nothing should be exposed to Korean users until written counsel review. NBA ToU §§1/9 (I-24/F16) is also open for written review.
- **Flag registries (cross-linked):** [`docs/flagged.html`](docs/flagged.html) (F1–F8 + I-items), [`docs/verified/flagged.html`](docs/verified/flagged.html) (F01–F16), [`docs/review/flagged.html`](docs/review/flagged.html) (complete register). None blocks publication.

## Site map (all tables link official sources)

Dashboard/calculator · Strategies · Validation Gates · Correlations · Leaderboard · Sources · Flagged for Review (all under `docs/`), plus the source-linked [verified data section](docs/verified/index.html) and this session's [independent review section](docs/review/index.html): Overview, Executive summary, Verification log, Repo review, Flagged for Review.

## Verification performed in this pass

- 24 official sources retrieved directly; exact evidence quotes in `data/verification_log.csv` and on the [Verification Log](docs/review/verification.html) page.
- Automated gate [`tools/check_site.py`](tools/check_site.py): every data row on maintained pages has a directly verified official source link; no broken internal links; no undefined `Math.erf()`; every `data/sources.csv` URL is in the verification log. Result: **12 strict pages, 0 errors** ([report](audit/link_check_report.md)).
- Site generator drift check: `python3 tools/build_review.py --check`. Engine tests: 5/5 pass.
- Advisory findings on pages owned by other sessions (rows without official links) are logged as coordination requests in [`COORDINATION.md`](COORDINATION.md) and published on the Flagged for Review page; this session does not edit another session's files.

## Irregularities flagged (do not block publication)

Full row-by-row list with official source links: [`docs/flagged.html`](docs/flagged.html) and [`docs/review/flagged.html`](docs/review/flagged.html). Highlights: coordination collisions between parallel sessions; an incorrect "sandbox cannot fetch NBA.com" claim (corrected); a broken FAQ URL (corrected); a relative Markdown link used as a source (corrected); the calculator's undefined `Math.erf` (fixed); table rows that lacked official links (fixed); a dated 2021 partner announcement; a content-limited rulebook retrieval; no official odds source; NBA prop/parlay restrictions not enumerated; no LICENSE; and 29 advisory rows in the other session's `docs/verified/` pages (request logged, not edited).

**Pull request, merge result and Pages deployment record:** see the completion section of [`COORDINATION.md`](COORDINATION.md).

---

## Session `arena/325834c9-own6` — collected data, backtested model, measured correlations (2026-11-02)

This section was written by the session that collected first-hand NBA data; it extends — and in
two places corrects the picture of — the combined summary above. Nothing above was edited.

- **Collected & verified data (per-row official links):** 2026-27 standings (30 teams), NBA.com
  advanced team ratings, **all 92 game results** Oct 20–Nov 1 (`data/games_results_2026-27.csv`),
  DraftKings market lines for the 2026-11-02 15-game slate with **open + current** values
  (`data/market_lines_2026-11-02.csv`, ESPN feed = secondary, labeled), and a verified player-prop
  subset (`data/player_props_2026-11-02.csv`, identities resolved against ESPN athlete endpoints).
  **`scripts/verify_data.py`: 213/213 PASS** — every team's W-L recomputed from official game
  cards matches the official standings exactly (`verification/verification_report.csv`).
- **Correlation values now exist** (computed from official rows; the "no correlation coefficient
  is published" statement above reflects the earlier state of the repo): same-game team scores
  **r=+0.200** (n=92), cross-game parlay legs **r=+0.105** (n=357), rest differential
  **r=−0.016** (n=76, null), teammate prop pair **r=−0.422** (n=6, flagged small-sample).
  Sources: `data/correlation_findings.csv`, `research/correlation.md`.
- **Walk-forward backtest (model v0.1, n=82 graded):** log-loss **0.6747** vs 0.6932 (coin) and
  0.7059 (expanding home-win baseline); straight-up accuracy **59.8%**; predicted-vs-actual margin
  r=0.210. **Gate G1 (calibration) FAILS** — 95% bootstrap CI [−0.013, +0.073] crosses zero.
  Consistent with the combined summary's stance: **no validated edge, no profitability claim**;
  all seven strategies stay TRACKING or NOT DEPLOYED (`research/strategies.md` leaderboard,
  paper rewards only).
- **Own6 sub-site:** `docs/own6/` (Dashboard, Data, Lines & Props, Strategies, Validation,
  Correlation, Flagged) — 238 data rows, every row sourced; `scripts/linkcheck.py` PASS.
- **Flagged (9 items, needs review, non-blocking):** NBA ToU §9 ingestion concern (I-24/F16
  applies — this session does ingest NBA statistics), unresolved prop athlete IDs (withheld),
  prop quote-side ambiguity, unavailable historical closing lines (CLV gate blocked), prior-season
  log gaps, the G1 failure itself, schedule-vs-feed line drift, ESPN secondary labeling,
  IND–BKN recap-slug mismatch. Full list: `docs/own6/flagged.html`.


---

## Integration update — 2026-11-03 (session `arena/f58e0178-own6`)

Full, linked version: [`docs/hub/summary.html`](docs/hub/summary.html) (live: https://sassnarep3-star.github.io/Own6/docs/hub/summary.html).

**Bottom line.** No Own6 strategy has a statistically supported edge; none is skill-eligible, so no rank or paper reward is awarded. The first dated forward test (15 games, 2026-11-02) found the market at least as accurate as Own6 on margin (MAE 9.70 vs 10.19), total (15.30 vs 16.29) and win probability (log-loss 0.575 vs 0.607), with every interval including zero. No profitability claim is made.

**Verified against official NBA.com pages on 2026-11-03.** 15 new final scores; 13 historical scores re-read (13/13 match); win-loss records recomputed from all 107 result rows equal the official standings for all 30 teams. Not verified: 79 score rows at score level, the team-ratings snapshot, odds/props (secondary ESPN feed, flagged), and NBA/Korean legal questions.

**Errors found and fixed.** (H01) the live landing page contained committed git conflict markers; (H02) market implied probabilities used a wrong formula, understating "edge vs fair" by about 10-17 points; (H03) Brier score was published as 0.6654/0.6946 instead of 0.2408/0.2500. Also flagged: four inconsistent gate registries (H04) and a leaderboard score that rewarded process compliance rather than skill (H05).

**Correlations** (Pearson r, official results): same-game home vs away points +0.22 (n=107); same-game margin vs total +0.01 (n=107); cross-game same-date margins +0.11 (n=357 overlapping pairs, interval not reported); teammate points -0.42 (n=6, unusable).

All open items: [Flagged for Review](docs/hub/flagged.html).

---

## Independent verification update — 2026-11-03 (session `arena/be184e2b-own6`)

Full, row-by-row version: [`docs/verify/index.html`](docs/verify/index.html) · live: https://sassnarep3-star.github.io/Own6/docs/verify/

**What was checked, and against what.** Every published value that could be checked against an official page was re-read in this session and recorded in [`data/verification_official_2026_11_03.csv`](data/verification_official_2026_11_03.csv) with the URL opened and the date read. **54 of 54 checks match; 0 mismatches.**

| Check | Rows | Result | Official page used |
|---|---|---|---|
| 2026-11-02 final scores | 15 | **15/15 match** (incl. NOP 135–134 MEM in OT) | each game's NBA.com game summary |
| 2026-27 standings W-L | 30 | **30/30 match** | https://www.nba.com/standings |
| NBA Terms §1 / §6 / §9, Stats FAQ, prediction-market release | 5 | quoted text matches | nba.com |
| 국민체육진흥법 identity and Art. 26(1), 26(2)①, 26(2)② | 4 | quoted text matches | law.go.kr |

**Aggregate cross-check.** Win-loss records recomputed from all 107 committed result rows equal the official 30-team standings exactly. This is a recomputation over committed data, not a second independent source.

**Rights findings (unchanged position, re-read and quoted this session).**
- [NBA Terms §9](https://www.nba.com/termsofuse#nba-statistics): NBA Statistics "may not be used in connection with any gambling activity (including legal gambling activity)", and §9(vii) restricts comprehensive statistics databases without prior consent.
- [NBA Terms §1](https://www.nba.com/termsofuse#ownership-and-use-restrictions) bars reuse, reproduction or linking of Basketball Content without written permission; §6 allows word links from non-commercial sites to NBA home pages only. This site cites internal game pages as its audit trail, so the conflict is disclosed on the Flagged page rather than hidden.
- [NBA Stats FAQ](https://www.nba.com/stats/help/faq): statistics are "not available for download" — the reason no bulk statistics feed is used.
- [국민체육진흥법 제26조](https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95/%EC%A0%9C26%EC%A1%B0): only the designated foundation may issue tickets or similar instruments for reward; no one may design, provide or distribute a system for similar betting over an information network, provide match information for that purpose, or promote/broker it. Whether this research publication falls inside that scope is a legal question; no opinion exists.

**What stays blank (8 items, published on the Unverified page).** Sportsbook prices and prop lines (ESPN relay of DraftKings, no official or licensed odds page, no capture times), prop settlement, the press-reported prop/parlay restrictions (the official release refers to restrictions without listing them), the team-ratings snapshot, closing-line values and realized ROI, a Korean legal opinion, and 79 of the 92 earlier score rows that were not re-read this session.

**Integrity repairs made this session.**
- The 31 previously advisory table rows in `docs/verified/**` that carried no official source now each carry an explicit official reference — an official methods document for a rule (NBA Terms, Stats FAQ, official release, statute, scikit-learn/NIST/statsmodels/SciPy documentation), or the official release that shows why a press-reported restriction is *not* enumerated. **No published value was changed**, and the strict site gate now reports **0 errors, 0 advisories**.
- New machine checks: `scripts/build_verify.py`, `scripts/check_verify.py` and `.github/workflows/verify-ledger.yml`. The build fails if a ledger row has no official https link, an unknown status, a MISMATCH, an unverified row that carries a value, a table row without a source, or a broken internal link.

**Bottom line, unchanged.** Verifying scores and statutes says nothing about beating a market. On the one graded slate the market was at least as accurate as Own6, every interval included zero, and **no strategy is skill-eligible**. Verifying data removes bookkeeping error; it cannot remove luck from a 15-game sample.

---

## Session `arena/27fdbe09-own6` — 5 November 2026 snapshot and full integration

**Bottom line, unchanged.** No validated strategy, no qualified leaderboard entry, no verified
market price, no player-prop correlation. Rewards remain non-monetary research priority. Nothing
here is betting advice. What is new is that today's facts were re-read from official pages, every
table row links to the page used, and the five outstanding session PRs were merged and re-checked
together.

**What was verified today (2026-11-05, NBA.com):**

| Check | Result | Source |
|---|---|---|
| Standings, 2026-27 | 30 rows read; 121 wins = 121 losses | [nba.com/standings](https://www.nba.com/standings) |
| 4 November final scores | 14/14 read one game card at a time | [nba.com/games 2026-11-04](https://www.nba.com/games?date=2026-11-04) |
| Archive reconciliation, today | 121 games → **30/30** team records match today's standings | [nba.com/standings](https://www.nba.com/standings) |
| Archive reconciliation, 3 Nov | 107 games → **30/30** team records match the 3 Nov snapshot | [nba.com/standings](https://www.nba.com/standings) |
| 4 Nov delta | 28 teams moved by exactly one game; ORL and GSW idle | [nba.com/games](https://www.nba.com/games?date=2026-11-04) |
| Forward slate | 11 games (5–6 Nov) with tip times, IDs, Cup groups | [ORL @ PHX game page](https://www.nba.com/game/orl-vs-phx-0022600187) |
| Rights text | §9(i)–(vii) and the FAQ download statement re-read verbatim | [Terms](https://www.nba.com/termsofuse), [FAQ](https://www.nba.com/stats/help/faq) |

**Signal research, with luck controlled.** A ridge team-rating margin/total model, refitted before
every game, scored 61 unseen games: winner accuracy **67.2%** (95% Wilson 54.7–77.7%) against
**50.8%** for always picking the home team. But the paired McNemar exact test gives **p = 0.0639**
and the bootstrap interval on Brier skill (**+0.130**, 95% **−0.039 to +0.296**) contains zero. The
honest reading is *preliminary signal, unproven*. With ~4 games per team and no market benchmark,
nothing is promoted; the leaderboard stays empty.

**Measured dependence, for parlay design (official finals only).** Margin vs total r = **+0.018**
[−0.161, +0.196] (n=121) — side and total carry little shared information here; home vs away points
r = **+0.199** [+0.022, +0.365] — pace couples the two sides of the same game, so two overs are not
independent; split-half team differential r = **+0.464** [+0.124, +0.706] (n=30) — weak evidence that
team quality persists, on a very small sample. Player-prop correlations stay **blank**: no licensed
player-level archive exists and Terms §9(iv) bars gambling-related use.

**Integration.** Five stale session PRs (#23, #28, #31, #32, #37) were merged into this branch with
both sides of every coordination-board conflict preserved. Their merges close the last 31 advisory
un-sourced rows (`check_site`: 0 errors, **0 advisories**) and add the assurance and verification
ledgers. All nine CI gate suites pass on the combined tree, including 135 pytest tests plus 6
subtests, the fail-closed lab (`not_run`, zero observations), the 12-page hub (335 rows, 0 errors)
and the new 9-page daily snapshot (0 issues). Regenerating the derived artifacts is idempotent.
Their factual claims were structurally re-checked, not independently re-verified by this session, and
are labelled that way.

**Open flags (do not block publication).** Rights under Terms §1/§9(iv); no official price source;
no player-level data; the 3 Nov file named "live" is stale; ~4 games per team; older score rows
validated in aggregate only. Full list on the site's Flagged for Review pages and in
[`audit/SESSION_27fdbe09.md`](audit/SESSION_27fdbe09.md).
