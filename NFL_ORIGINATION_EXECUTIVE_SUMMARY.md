# NFL Fair-Line Origination, Depth-Deficiency & Skill-Gated Strategy Pack — Executive Summary

**Verification Date:** November 12, 2026 (2026 NFL Regular Season — Entering Week 10)  
**Repository / Branch:** `sassnarep3-star/Own6` (`arena/8132a3b1-own6`)  
**Live GitHub Pages Dashboard:** [`https://sassnarep3-star.github.io/Own6/docs/nfl-origination/`](https://sassnarep3-star.github.io/Own6/docs/nfl-origination/)  
**Compliance & Integrity Posture:** Research & analytical verification framework only. Zero manual user input required; zero scraped or fabricated sportsbook odds; every unconfirmed empirical metric is left strictly blank (`""`) and cataloged on [`Flagged for Review`](docs/nfl-origination/flagged.html).

---

## 1. Purpose & Scope Overview

This project delivers a complete, self-contained, zero-user-input NFL fair-line origination, signal research, starter-to-backup depth-deficiency, and pre-decision governance suite inside `sassnarep3-star/Own6`:

1. **Itemized Requirements & Official-Source Verification (`REQ-01`..`REQ-16`, `NFL-S01`..`NFL-S28`):** Every claim, rule parameter, 32-club 2026 standing, 14-game Week 10 matchup, and 24-unit starter/backup depth chain was retrieved directly from primary official sources (`nfl.com`, `operations.nfl.com`, `support.nfl.com`, official NFL club depth charts, `scipy.org`, `scikit-learn.org`, `statsmodels.org`, `itl.nist.gov`, `aglc.ca`, and `github.com`).
2. **Pre-Decision Q&A & Missing-Information Discovery (`Q-01`..`Q-16`):** Separates what we **already know with 100% primary-source certainty** from what we **do not yet have** (licensed play-by-play EPA feeds, timestamped multi-book closing odds, post-2025 empirical key-number weights, paired player-prop residual vectors, and hourly stadium wind/roof logs), paired with concrete, lawful discovery protocols.
3. **Review-First Site & Decision-Making Suggestions (`SUG-01`..`SUG-14`):** Presents 14 concrete architectural and workflow improvements—each with multi-path options (`Path A / B / C`), pros/cons, prerequisites, effort, and reversibility—in a `pending_human_choice` review state so a human reviewer can choose the best path before modifying shared repository files.
4. **NFL Fair-Line Origination, Signal Strategies & Skill Leaderboard (`src/nfl_origination/`):** Pure Python 3.11 stdlib engine implementing discrete integer-margin NFL pricing (key numbers `3, 7, 6, 10, 14`, push-exact expected value, and 2025+ regular-season 10-minute both-possess overtime ties), 10 preregistered NFL strategies across **Single Bets**, **Multi-Game Parlays**, and **Same-Game Parlay / Player-Prop Combos**, bivariate Simpson quadrature & Cholesky Gaussian copulas, 12 fail-closed validation gates (`NFL-G01`..`NFL-G12`), and a luck-controlled composite `SkillScore` leaderboard (`0` strategies qualified at launch).
5. **Offensive & Defensive Starter-vs-Backup (1st–4th String) Depth Tracking (`DEPTH-01`..`DEPTH-24`):** Reconciles official Week 10 `nfl.com/injuries/` participation with 1st-, 2nd-, 3rd-, and 4th-string club depth orders, enforcing the NFL 48-vs-47 active 8-OL rule, 3-game Practice Squad elevation cap, and 53-man Emergency 3rd QB rule.
6. **Line-by-Line Repository Review (`RA-01`..`RA-16`) & Flagged-for-Review Ledger (`NFL-F01`..`NFL-F15`):** Audits legacy repo code (`src/own6/`, `nba_lab/`, `scripts/`, `tools/`, `docs/`, CI workflows, and sibling packs) with exact file/line references and non-blocking review flags.

---

## 2. Verified 2026 NFL State Entering Week 10 (Nov 12–16, 2026)

- **League-Wide Standings Exact Reconciliation (`verified_standings_2026_w10.csv`):** Across all 32 NFL clubs verified verbatim from [`nfl.com/standings/division/2026/reg`](https://www.nfl.com/standings/division/2026/reg):
  - **Total Wins = Total Losses = `135`**, **Total Ties = `2`** (`NYG 5-2-1`, `WAS 2-5-1` — 136 completed regular-season games through Week 9).
  - **Total Points For = Total Points Against = `6,246` points** (`22.96` points/team-game), and `PF - PA == Net Pts` holds identically for all 32 clubs.
  - Division leaders entering Week 10: **BUF (`7-1`)**, **PIT / CIN (`6-2`)**, **JAX (`6-2`)**, **DEN (`7-2`)** in the AFC; **NYG (`5-2-1`)**, **CHI (`7-2`)**, **CAR / NO (`3-5`)**, **SF (`7-1`)** in the NFC.
- **Week 10 Schedule (`week10_slate_and_lines.csv`):** 14 games + 4 clubs on bye (`CHI`, `DEN`, `PHI`, `TB`), highlighted by `WAS at NYG` (TNF Nov 12), `NE vs DET` at **FC Bayern Munich Arena, Germany** (Sunday Nov 15, 9:30 a.m. ET — `neutral_site=true`, `HFA=0`), `MIN at GB`, `SF at DAL`, `PIT at CIN` (SNF), and `LAC at BAL` (MNF Nov 16). All sportsbook spreads/totals and empirical originated lines are **intentionally blank (`""`)** under `NFL-F01` / `NFL-G01`.
- **2025–2026 Rule Regime Shifts (`nfl_official_rules_and_roster.csv`):**
  1. **Rule 6 Dynamic Kickoff:** Touchback dead-ball spot moved to the **35-yard line**; trailing club may declare an onside kick at any time.
  2. **Rule 16 Regular-Season Overtime:** Aligned with postseason so **both teams are guaranteed an opportunity to possess** within a 10-minute regular-season OT period.
  3. **2025 Resolution G-2 (K-Balls):** Pre-gameday kicking-ball preparation permitted, shifting long field-goal range.
  4. **Roster & Depth Mechanics:** 48 gameday active players iff **>= 8 offensive linemen** dress (drops to 47 otherwise); max 2 weekly Practice Squad Standard Elevations (max **3 regular-season elevations per player**); **Emergency 3rd QB** must reside on the **53-man roster** (Practice Squad elevations ineligible per NFLPA veto).

---

## 3. Critical Week 10 Starter-to-Backup Depth Findings (`DEPTH-01`..`DEPTH-24`)

1. **Multi-String Cascading Unit Clusters (Offense & Defense):**
   - **New England Patriots (vs. DET in Munich):** Simultaneous cascading impairments at Left Guard/Center (`1st LG Ben Brown OUT` + `2nd LG/RG Walter Rouse DNP`), Running Back (`1st RB Rhamondre Stevenson DNP` + `2nd RB TreVeyon Henderson OUT` -> elevates **3rd-string RB Corey Kiner** and **4th-string RB Lan Larison**), and Cornerback (`1st CB Carlton Davis III OUT` -> **2nd-string CB Channing Canada**, with `2nd CB Charles Woods Limited`).
   - **Baltimore Ravens (vs. LAC MNF):** `1st QB Lamar Jackson` placed on IR (right thumb; minimum 4-game absence) and `2nd QB Tyler Huntley` out for season (turf toe), forcing **3rd-tier replacement QB Jacoby Brissett**.
   - **Seattle Seahawks (at LV):** `1st QB Sam Darnold` ruled OUT and `2nd QB Drew Lock` listed LIMITED, creating acute mid-game Emergency 3rd QB exposure unless a healthy 3rd QB sits on the 53-man roster.
   - **Green Bay Packers (vs. MIN) & Arizona Cardinals (vs. LAR):** Severe multi-starter DNP clusters across Packers RB/C/LB/EDGE/Nickel (`Josh Jacobs`, `Sean Rhyan`, `Zaire Franklin`, `Lukas Van Ness`, `Javon Bullard`) and Cardinals interior OL + defensive spine (`Isaac Seumalo`, `Hjalte Froholdt`, `Roy Lopez`, `Josh Sweat`, `Mack Wilson Sr.`, `Budda Baker`).
2. **Proof That Static Club Web Depth Charts Cannot Be Used Unreconciled (`NFL-F07`):**
   - `patriots.com`, `detroitlions.com`, `vikings.com`, and `packers.com` explicitly label their web depth charts **"Unofficial"**.
   - `vikings.com` (as of Nov 12) still lists `1st Kyler Murray (DNP) / 2nd Carson Wentz (Limited) / 3rd Max Brosmer` without integrating trade-deadline acquisition **QB Kirk Cousins** (confirmed by `nfl.com` Nov 11 preview).
   - `commanders.com` omits `C Lucas Patrick` from its web Center row even though `nfl.com/injuries/` officially rules `Lucas Patrick (C) — OUT (Concussion)`.

---

## 4. Luck Removal, Correlations & Why Zero Strategies Qualify Today

- **Why Raw NFL Win-Loss ROI Is Dominated by Luck in Short Samples:** Over `N = 250` standard `-110` bets, binomial outcome standard error is `~6.03%` ROI—meaning a zero-skill coin flipper can easily post `+8%` ROI over half an NFL season.
- **How `src/nfl_origination/` Removes Luck From Qualification:** Every candidate strategy (`NFL-STR-01`..`NFL-STR-10`) must clear all 12 gates (`NFL-G01`..`NFL-G12`), including **same-line de-vigged CLV (`t >= 2.50`)**, **strictly proper scoring dominance (`Brier` and `LogLoss` beating closing market)**, **NFL week-clustered block bootstrap (`95% CI low > 0`)**, and **Holm-Bonferroni multiple-testing adjustment (`M = 10`)**.
- **Correlations (`correlations.py`):** All parlay and player-prop combo strategies are blocked under `NFL-G11` until paired training-only residual correlations (`e = y - E[y]`) and simultaneous sportsbook SGP quotes (to audit implicit SGP "correlation taxes") are licensed.
- **Current Leaderboard Result:** **`0 / 10` real strategies qualified** (`NONE_UNQUALIFIED`). The scoring and gate math are verified via deterministic pure-stdlib unit tests (`tests/test_nfl_origination.py`).

---

## 5. Deliverable Map

| Artifact | Path | Purpose |
| :--- | :--- | :--- |
| Pure-Stdlib NFL Engine | `src/nfl_origination/*.py` | Pricing, discrete margin origination, 1st–4th string depth, copulas, 12 gates, leaderboard |
| Verified CSV Datasets (13 files) | `data/nfl_origination/*.csv` | 222 source-linked rows; exact 32-team accounting; blank unverified cells |
| Live Static Dashboard (11 pages) | `docs/nfl-origination/*.html` | Zero-`<input>` responsive dashboard with per-row official links & review pages |
| Line-by-Line Repo & Source Audit | `audit/NFL_ORIGINATION_REPO_AND_SOURCE_AUDIT.md` | Full code/workflow/link audit (`RA-01`..`RA-16`) & 28-source register |
| Research Specifications (3 docs) | `research/nfl_origination/*.md` | Pre-decision Q&A, suggestions, origination/copula math, depth methodology |
| Automated Verifier & Tests | `scripts/check_nfl_origination.py`, `tests/test_nfl_origination.py` | Enforces 0 `<input>`, 100% row source coverage, blank cells, and accounting math |

*Responsible Gaming & Informational Notice (Alberta, Canada): Analytical software verification artifact only; not wagering advice. Support resources: Alberta Gaming, Liquor and Cannabis (AGLC) GameSense / Self-Exclusion `1-844-468-8034` ([aglc.ca](https://aglc.ca/gaming/common-gaming-questions)).*
