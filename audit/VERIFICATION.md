# Line-by-line verification record — session `arena/a6ccf588-own6`

**Date:** 2026-11-02 (UTC) · **Role:** independent final integration / verification pass on the combined `main` content.
**Method:** every official URL in this project was retrieved **directly from the official host** during this session (page/PDF retrieval for web pages; `gh api` for GitHub REST endpoints). Search-engine snippets are **not** treated as verification. Exact evidence text and retrieval method are recorded in [`data/verification_log.csv`](../data/verification_log.csv) (V01–V24) and mirrored on the site's [Verification Log](../docs/review/verification.html) page.
**Rule:** a value that cannot be confirmed from an official source is left blank and published on the [Flagged for Review](../docs/flagged.html) page. Nothing is inferred, interpolated or filled in.

## 1. Source-by-source verification (line by line)

| ID | Claim checked | Official source (link) | Directly observed evidence | Verdict |
|---|---|---|---|---|
| V01 | NBA Stats hub is live and contains per-game leaders | [NBA.com/Stats overview](https://www.nba.com/stats/overview) | Title `Official NBA Stats`; "Yesterday's Leaders" dated 11/01/2026; points/rebounds/assists leader tables | Verified direct |
| V02 | Model inputs are official NBA definitions | [NBA Stats Glossary](https://www.nba.com/stats/help/glossary) | "PACE … The number of possessions per 48 minutes for a team or player."; "OffRtg … Measures a team's points scored per 100 possessions."; "NetRtg … Formula OFFRTG - DEFRTG"; "USG% … (FGA + Possession Ending FTA + TO) / POSS" | Verified direct |
| V03 | No official bulk CSV; coverage and update timing | [NBA.com/Stats FAQ](https://www.nba.com/stats/help/faq) | "Our stats are not available for download for either academic or personal use. They are for viewing and enjoying on NBA.com/Stats"; advanced stats back to 1996-97, base stats to 1946-47; advanced stats updated 10–15 min after games | Verified direct |
| V04 | Rulebook / game context | [NBA Official rulebook](https://official.nba.com/rulebook/) | Page returns only the heading "NBA Rulebook"; no rule text available to the retrieval tool | Verified (limited); rule details unverified → flag I-8 |
| V05 | Availability inputs and reporting deadlines | [NBA Official injury report 2026-27](https://official.nba.com/nba-injury-report-2026-27-season/) | "NBA teams must report information concerning player injuries … By 5 p.m. local time the day before a game … teams must designate a participation status"; reports updated continually | Verified direct |
| V06 | Timestamped injury report | [11/02/26 01:45 PM PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-02_01_45PM.pdf) | "Injury Report: 11/02/26 01:45 PM" with matchup/player/status rows; URL also listed on V05 | Verified direct (PDF chunk); initial chunk-0 retrieval failed → flag I-5 |
| V07 | Betting-partner context (historical) | [NBA.com News, Nov 4 2021](https://www.nba.com/news/draftkings-fanduel-become-nbas-co-official-sports-betting-partners) | "November 4, 2021"; "making DraftKings … and FanDuel Group co-official sports betting partners of the NBA" | Verified direct, but **dated** → current status taken from V21; flag I-9 |
| V08 | Extra official stat definitions | [NBA.com Stat Glossary article, Oct 20 2025](https://www.nba.com/news/inside-the-game-stat-glossary) | "Learn more about the following statistical terms and how they are determined on the basketball court." | Verified direct |
| V09 | Calibration / proper scoring rules | [scikit-learn calibration guide](https://scikit-learn.org/stable/modules/calibration.html) | "Strictly proper scoring rules for probabilistic predictions like sklearn.metrics.brier_score_loss and sklearn.metrics.log_loss assess calibration…" | Verified direct |
| V10 | Brier score | [scikit-learn brier_score_loss](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html) | "The Brier score measures the mean squared difference between the predicted probability and the actual outcome." | Verified direct |
| V11 | Bootstrap CI | [SciPy bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) | Signature includes `confidence_level=0.95`, `method='BCa'` | Verified direct |
| V12 | Pearson ρ | [SciPy pearsonr](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) | "Pearson correlation coefficient and p-value for testing non-correlation." | Verified direct |
| V13 | Bonferroni correction | [statsmodels multipletests](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html) | Method list: "bonferroni : one-step correction" | Verified direct |
| V14 | Exact binomial luck test | [NIST/SEMATECH e-Handbook](https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm) | "The binomial distribution is used when there are exactly two mutually exclusive outcomes of a trial"; PMF/CDF formulas | Verified direct |
| V15 | `math.erf` / `math.comb` used by the Python engine | [Python math docs](https://docs.python.org/3/library/math.html) | "This module provides access to common mathematical functions and constants…" | Verified direct |
| V16 | Walk-forward / no lookahead | [scikit-learn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) | "Learning the parameters of a prediction function and testing it on the same data is a methodological mistake … hold out part of the available data as a test set" | Verified direct |
| V17 | Pages publishing-source options | [GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) | "You can configure your GitHub Pages site to publish when changes are pushed to a specific branch, or you can write a GitHub Actions workflow…" | Verified direct |
| V18 | Repo metadata | [GitHub REST API repo](https://api.github.com/repos/sassnarep3-star/Own6) | `default_branch: main`, `has_pages: true`, `license: null`, created 2026-10-31 | Verified direct |
| V19 | Pages config / build status | [GitHub REST API pages](https://api.github.com/repos/sassnarep3-star/Own6/pages) | `build_type: legacy`, `source: main:/`, `status: built`, `html_url: https://sassnarep3-star.github.io/Own6/` | Verified direct |
| V20 | Repo file tree for the review | [GitHub REST API tree](https://api.github.com/repos/sassnarep3-star/Own6/git/trees/main?recursive=1) | `README.md`, `COORDINATION.md`, `EXECUTIVE_SUMMARY.md`, `data/`, `docs/`, `src/own6/`, `tests/`, `index.html`, `.gitignore`, `.nojekyll`, `scripts/`, `docs/verified/` | Verified direct |
| V21 | Current official gaming partners | [NBA.com NBABet, July 9 2026](https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2) | "Below is a list of official NBA gaming partners and operators"; "Domestic Official Gaming Partners" (DraftKings, FanDuel); international partners by country | Verified direct |
| V22 | Integrity framework / market restrictions | [NBA.com News, Oct 26 2026](https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets) | "limitations on permissible markets"; "market restrictions aligned with the NBA's latest sports betting restrictions" — **the specific restrictions are not listed on this page** | Verified direct; specifics unverified → flag I-16 |
| V23 | Schedule data sample | [NBA.com schedule](https://www.nba.com/schedule) | "Week 3 (Nov 2 - Nov 8)", "Monday, November 2", "15 Games"; OKC at CLE 7:00 PM ET, Rocket Arena | Verified direct (partial retrieval) |
| V24 | Repository content / coordination board | [GitHub repo](https://github.com/sassnarep3-star/Own6) | Landing page, commit history, file listing, README heading | Verified direct |
| V25 | NBA.com Terms of Use §§1 and 9 | [NBA.com Terms of Use](https://www.nba.com/termsofuse) | §1: "No Basketball Content from the Services may be … linked to, or otherwise used except as provided in these Terms of Use without the written permission of the Operator."; §9: "the NBA Statistics may not be used in connection with any gambling activity (including legal gambling activity)" and "may only be used, displayed, or published for legitimate news reporting or private, non-commercial purposes" | Verified direct → flag I-24 |

## 2. Code and site verification performed

| Check | Command / method | Result |
|---|---|---|
| Engine unit tests (5) | `python3 tools/run_tests.py` (stdlib runner; `pytest` is not installed in this sandbox) | 5/5 pass (`test_lines_sum`, `test_devig_sums1`, `test_corr_parlay`, `test_luck`, `test_shrink`) |
| Source registry vs. verification log | `python3 tools/check_site.py` | Every `data/sources.csv` URL must exist in `data/verification_log.csv` with a `verified-direct*` status |
| Every table row has an official source link | `python3 tools/check_site.py` | Enforced on all top-level `docs/*.html` and `docs/review/*.html`; header rows (`<tr>` with no `<td>`) excluded |
| No broken internal links | `python3 tools/check_site.py` | All relative `href`/`src` targets resolve inside the Pages root (`docs/`); `../` escapes are rejected |
| No undefined JavaScript math | `python3 tools/check_site.py` | Fails if `Math.erf` appears anywhere in `docs/**` (it is not part of standard JavaScript — confirmed in Node v22.22.3) |
| Site build drift | `python3 tools/build_review.py --check` | Generated `docs/review/*.html` must match committed files byte for byte |
| GitHub Pages deploy | `gh api repos/.../pages/builds/latest` + live URL retrieval | Build status and live content confirmed after merge (recorded in `COORDINATION.md`) |

## 3. Values deliberately left blank (no official confirmation)

- Team PACE / OffRtg / DefRtg for the current season — no official bulk download exists ([V03](https://www.nba.com/stats/help/faq)); a viewer-supplied export would be needed.
- Fitted home-court advantage and margin standard deviation — require an official-data game log, not yet built.
- **All correlation coefficients ρ** — require paired residual histories; no value is published anywhere in this project.
- Live/closing odds, vig, prices, bet results, ROI, CLV, Brier comparisons, win rates and backtest returns — no verified bet ledger exists.
- Specific 2026 prop-bet / parlay market restrictions — official release refers to restrictions but does not enumerate them ([V22](https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets)); press reports are not official sources.
- Rulebook details beyond the page heading ([V04](https://official.nba.com/rulebook/)).

## 4. Irregularities found (published on the Flagged for Review page)

I-1 branch-naming deviation · I-2 overlapping session claims · I-3 incorrect "sandbox cannot fetch NBA.com" claim · I-4 `cdn.nba.com/stats/help/faq` AccessDenied · I-5 injury PDF retrieval intermittent · I-6 `../COORDINATION.md` broken from Pages root · I-7 `Math.erf` undefined · I-8 rulebook content-limited · I-9 2021 partner announcement is dated · I-10 "5 tests passing" needed a dependency-free rerun · I-11 tracked `.pyc` build artifacts in git history · I-12 Pages API 403 prevented switching source to `/docs` · I-13 earlier Actions deploy workflow runs failed · I-14 "verified-indexed" statuses replaced by direct retrieval · I-15 no official odds source · I-16 NBA market restrictions not enumerated · I-17 concurrent pushes caused a `pull --rebase` conflict · I-18 other sessions' `docs/verified/*` methodology/strategy table rows lack official links (request logged in `COORDINATION.md`, not edited by this session) · I-19 no LICENSE · I-20 rows without official links (repaired) · I-21 coordination board misstates the Pages source · I-22 date-specific schedule data · I-23 dated partners list · **I-24 NBA.com Terms of Use §§1/9 legal/rights concern (request A28-REQ-01, published on both Flagged for Review pages; needs qualified legal review; no legal conclusion asserted)**.

See [`docs/review/flagged.html`](../docs/review/flagged.html) and [`docs/flagged.html`](../docs/flagged.html) for the full row-by-row list with source links.
