# Executive Summary — Own6: Originate Your Own NBA Lines

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
- GitHub Pages is configured as a **legacy `main:/` publishing source** with a root `index.html` redirect to `docs/`; an API attempt to switch the source to `/docs` returned HTTP 403 ("Resource not accessible by integration"). Publishing-source options are documented by [GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). The live URL is <https://sassnarep3-star.github.io/Own6/>.
- The repository has **no LICENSE file** ([GitHub API](https://api.github.com/repos/sassnarep3-star/Own6) reports `license: null`).

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
