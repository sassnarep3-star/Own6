# Pre-Decision Readiness Q&A, Missing-Information Discovery & Site Improvement Suggestions

**Scope:** Decision-making governance for `sassnarep3-star/Own6` (`data/nfl_origination/decision_qa_and_missing_info.csv` & `data/nfl_origination/site_suggestions.csv`).  
**Core Rule:** No capital-allocation, automated line-publication, or shared-root structural edit should occur until blocking unknowns are resolved through lawful primary sources and a human reviewer selects their preferred implementation option.

---

## Part I — Pre-Decision Inventory: What We Have vs. What We Do Not Have

### A. Verified Information Already in Hand (`100% Primary-Source Confirmed`)
1. **Exact 2026 League Standings & Scoring Totals Entering Week 10 (`NFL-S09`):** All 32 teams' W-L-T, PF, PA, Net Pts, Home/Road/Division/Conference records, and streaks (`135W = 135L`, `2 Ties`, `6,246 PF = 6,246 PA`).
2. **Exact Week 10 Matchups, Venues & Bye Clubs (`NFL-S10`, `NFL-S11`, `NFL-S14`):** All 14 games (Nov 12–16, 2026), 4 bye clubs (`CHI, DEN, PHI, TB`), broadcast windows, and FC Bayern Munich Arena neutral-site designation (`NE vs DET`).
3. **2025–2026 NFL Playing & Roster Rules (`NFL-S03`..`NFL-S08`):** 35-yard Dynamic Kickoff touchback, 10-minute both-possess regular-season OT, pre-game K-Ball prep, 53-man / 47-vs-48 active 8-OL rule, 2 weekly Standard Elevations (3-game player cap), 53-man Emergency 3rd QB rule, and 4-game IR minimum / 8+2 return limits.
4. **Data Rights & Sportsbook Integrity Boundaries (`NFL-S01`, `NFL-S02`):** NFL.com Terms (`§§1.3, 12`) prohibit scraping/gambling use; Genius Sports is the NFL's exclusive official data distributor for DraftKings, FanDuel, and Fanatics; officiating and injury wagers are banned.
5. **Week 10 Starter-to-Backup Depth Chains (`NFL-S12`, `NFL-S16`..`NFL-S23`):** 24 verified offensive and defensive 1st-to-4th string replacement cases, plus proof that club web depth charts carry `"Unofficial"` disclaimers and lag trades/injuries.
6. **Pure-Stdlib Mathematical & Statistical Engine (`src/nfl_origination/`):** Verified implementations of multiplicative/power de-vigging, push-exact EV, same-line CLV, discrete integer-margin PMF, 48-OL/QB3 roster validation, bivariate Simpson quadrature & Cholesky Gaussian copulas, week-block bootstrap CIs, Holm-Bonferroni FWER, and composite `SkillScore` ranking.

### B. Missing Information Intentionally Left Blank (`""`) & How to Discover It Lawfully
1. **Commercial Data & Odds Feed License (`Q-01` -> `Gate NFL-G01`):**
   - *Missing:* Written license to ingest play-by-play, Next Gen Stats participation, and executable sportsbook quotes.
   - *Discovery Path:* Request commercial or academic data licensing from **Genius Sports** (official NFL distributor) and regulated odds-feed aggregators; store the executed license metadata in `data/nfl_origination/license_manifest.json`.
2. **Timestamped Multi-Book Opening, Pre-Inactive (`T-95m`), Post-Inactive (`T-85m`) & Closing Odds (`Q-02` -> `NFL-G06/G07`):**
   - *Missing:* Historical and Week 10 spread, total, moneyline, player-prop, and simultaneous SGP prices.
   - *Discovery Path:* Record read-only snapshots from licensed regulated feeds at 4 fixed weekly timestamps (Sunday open, Wednesday injury report, Saturday 4 p.m. ET PS wire, and `T-95m / T-85m / T-1m` kickoff).
3. **Post-2025 Regime Empirical Calibration (`Q-03` -> `NFL-G03/G05`):**
   - *Missing:* Fitted post-2025 drive-start EPA curve, K-Ball 55+ yd FG conversion lift, and empirical integer-margin multipliers on `3, 7, 6, 10, 14` and OT ties.
   - *Discovery Path:* Fit strictly on the `408` post-rule NFL regular-season games (`2025` Weeks 1–18 = `272` games + `2026` Weeks 1–9 = `136` games) from a licensed play-by-play feed; never pool unweighted pre-2025 25-yard touchback seasons.
4. **Positional Starter-to-Backup (`1st -> 2nd -> 3rd -> 4th String`) EPA Drop-Off Priors & Snap Shares (`Q-04`..`Q-08` -> `NFL-G10`):**
   - *Missing:* Shrunk positional replacement EPA/play curves, cumulative season Practice Squad elevation counters (`0..3`), and Week 10 post-game snap shares.
   - *Discovery Path:* Reconcile daily NFL League Transaction Wire + T-90m Inactive Lists + post-game official NFL Gamebook offensive/defensive snap counts; fit hierarchical ridge/empirical-Bayes replacement priors by position group.
5. **Paired Pregame-Centered Residual Correlations & Implicit SGP Hold (`Q-09`, `Q-10` -> `NFL-G11`):**
   - *Missing:* Out-of-sample residual correlations `corr(y_1 - E[y_1], y_2 - E[y_2])` and simultaneous sportsbook SGP price quotes.
   - *Discovery Path:* Compute paired model residuals across `>= 300` licensed historical games with week-block bootstrap CIs and log quoted SGP payouts alongside two-way single-leg prop quotes to measure each book's implicit correlation tax.
6. **Outdoor Stadium Kickoff Weather & Retractable-Roof Declarations (`Q-11` -> `SUG-11`):**
   - *Missing:* Hourly kickoff wind speed/gusts, precipitation, temperature, and roof open/closed status for Week 10 venues.
   - *Discovery Path:* Query **U.S. National Weather Service (`api.weather.gov`)** (public-domain U.S. government data, zero licensing cost) for domestic stadiums + **Deutscher Wetterdienst (`dwd.de`)** for Munich, paired with club T-90m roof declarations.

---

## Part II — Review-First Suggestions to Improve the Site & Decision-Making (`SUG-01`..`SUG-14`)

All 14 proposals in `data/nfl_origination/site_suggestions.csv` and [`docs/nfl-origination/suggestions.html`](../../docs/nfl-origination/suggestions.html) remain in `pending_human_choice` status so reviewers can evaluate trade-offs before implementation:

1. **`SUG-01` (Neutral Multi-Domain Root Portal):** Replace `index.html`'s NBA-only redirect with a 3-card selector (`NBA Assurance | NFL Origination | SF 94122 Compliance`) once parallel sessions finish merging.
2. **`SUG-02` (Parallel Battle-Pack Consolidation):** Add non-destructive provenance banners to older parallel packs so reviewers always identify the canonical module per domain.
3. **`SUG-03` (Top-of-Page Go/No-Go Gate Readiness Banner):** Bind page headers directly to `evaluate_strategy_gates()` output so blocked research models are never mistaken for live-ready signals (previewed across `docs/nfl-origination/`).
4. **`SUG-04` (Two-Stage Wednesday vs. `T-85m` Post-Inactive Origination Views):** Separate early-week practice projections from binding post-inactive lines.
5. **`SUG-05` (Unit-Depth Cascade & 47-Active OL Penalty Badges):** Group injuries by positional depth chain (`1st -> 2nd -> 3rd -> 4th`) rather than alphabetical player lists (previewed on `injuries-depth.html`).
6. **`SUG-06` (Key-Number Push & Half-Point Equity Columns):** Display `P(Cover) / P(Loss) / P(Push)` plus `Key 3` and `Key 7` probability mass on all spread tables.
7. **`SUG-07` (Implicit Sportsbook SGP Correlation-Tax Audit Column):** Require side-by-side display of `Independent Fair Odds`, `Copula Correlated Fair Odds`, and `Book Quoted Odds & Tax` before evaluating any SGP.
8. **`SUG-08` (CLV & Proper-Score Primary Leaderboard Sorting):** Sort leaderboards by composite `SkillScore` (`LCB95_ROI + CLV + BrierEdge`) rather than lucky short-sample win percentage.
9. **`SUG-09` (Self-Referential Checksum & Stdlib CI Guard):** Keep `tests/test_*.py` pure stdlib and automate `audit_repo.py` + `build_assurance.py` pre-commit syncing.
10. **`SUG-10` (Legacy Prototype Quarantine & Dead-Link Advisory):** Preserve frozen legacy paths needed by `audit_sources.py` while adding explicit provenance warnings.
11. **`SUG-11` (Public-Domain NOAA/NWS & DWD Stadium Weather Feed):** Add free, official meteorological wind/precipitation telemetry for outdoor NFL totals and passing props.
12. **`SUG-12` (Bottom-Up Roster-Assembled Team Ratings):** Price teams from active Week `N` starters + playbook-tenure shrinkage so mid-season QB trades (`MIN Kirk Cousins`) and IR placements (`BAL Lamar Jackson`) update immediately.
13. **`SUG-13` (Append-Only Git Preregistration Trial Counter):** Increment family size `M` automatically on every committed strategy/hyperparameter variant to prevent offline survivor bias.
14. **`SUG-14` (Automated Tuesday Post-Week Reconciliation Script):** Reconcile pre-kickoff depth flags and originated probabilities against official Tuesday NFL Gamebook snap counts and final scores.
