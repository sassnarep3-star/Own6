# NFL Fair-Line Origination, Depth-Deficiency & Skill-Gated Strategy Pack — Executive Summary

**Verification Date:** November 12, 2026 (2026 NFL Regular Season — Entering Week 10)  
**Repository / Branch:** `sassnarep3-star/Own6` (`arena/8132a3b1-own6`)  
**Live GitHub Pages Dashboard:** [`https://sassnarep3-star.github.io/Own6/docs/nfl-origination/`](https://sassnarep3-star.github.io/Own6/docs/nfl-origination/)  
**Compliance & Integrity Posture:** Research & analytical verification framework only. Zero manual user input required; zero scraped or fabricated sportsbook odds; every unconfirmed empirical metric is left strictly blank (`""`) and cataloged on [`Flagged for Review`](docs/nfl-origination/flagged.html).

---

> **Live re-verification, 13 Nov 2026 (session `arena/4fc2fd57-own6`).** The official nfl.com standings, Week 10 injury report and 13 Nov news were re-read. The Thursday game is **final: Commanders 24, Giants 21**. League totals are now **136 W – 136 L – 2 T** and **6,291 PF = PA**. The live check of 102 named players found **17 depth/injury statuses contradicted by the official report** (corrected), 3 superseded by the 13 Nov roundup, and 43 named backups with no injury listed (now labelled "not on report"). Lamar Jackson's official timeline is 6–10 weeks. Brissett's move is press-only. Details: [`audit/NFL_LIVE_REVERIFICATION_2026_11_13.md`](audit/NFL_LIVE_REVERIFICATION_2026_11_13.md) · [`data/nfl_origination/live_check_2026_11_13.csv`](data/nfl_origination/live_check_2026_11_13.csv) · [`Flagged NFL-F16..F23`](docs/nfl-origination/flagged.html).

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

- **League-Wide Standings Exact Reconciliation, through Week 9 (`verified_standings_2026_w10.csv`; superseded for NYG and WAS by `standings_live_2026_11_13.csv`):** Across all 32 NFL clubs verified verbatim from [`nfl.com/standings/division/2026/reg`](https://www.nfl.com/standings/division/2026/reg):
  - **Total Wins = Total Losses = `135`**, **Total Ties = `2`** (`NYG 5-2-1`, `WAS 2-5-1` — 136 completed regular-season games through Week 9; live totals after the Nov 12 result are 136 W / 136 L / 2 T and 6,291 PF = PA).
  - **Total Points For = Total Points Against = `6,246` points** (`22.96` points/team-game), and `PF - PA == Net Pts` holds identically for all 32 clubs.
  - Division leaders entering Week 10: **BUF (`7-1`)**, **PIT / CIN (`6-2`)**, **JAX (`6-2`)**, **DEN (`7-2`)** in the AFC; **NYG (`5-2-1` through Week 9; now `5-3-1` after the Nov 12 loss to WAS, per `standings_live_2026_11_13.csv`)**, **CHI (`7-2`)**, **CAR / NO (`3-5`)**, **SF (`7-1`)** in the NFC.
- **Week 10 Schedule (`week10_slate_and_lines.csv`):** 14 games + 4 clubs on bye (`CHI`, `DEN`, `PHI`, `TB`), highlighted by `WAS at NYG` (TNF Nov 12; **FINAL: Commanders 24, Giants 21**, [nfl.com schedule](https://www.nfl.com/schedules/2026/by-week/week-10), read 13 Nov), `NE vs DET` at **FC Bayern Munich Stadium, Germany** (Sunday Nov 15, 9:30 a.m. ET — `neutral_site=true`, `HFA=0`), `MIN at GB`, `SF at DAL`, `PIT at CIN` (SNF), and `LAC at BAL` (MNF Nov 16). All sportsbook spreads/totals and empirical originated lines are **intentionally blank (`""`)** under `NFL-F01` / `NFL-G01`.
- **2025–2026 Rule Regime Shifts (`nfl_official_rules_and_roster.csv`):**
  1. **Rule 6 Dynamic Kickoff:** Touchback dead-ball spot moved to the **35-yard line**; trailing club may declare an onside kick at any time.
  2. **Rule 16 Regular-Season Overtime:** Aligned with postseason so **both teams are guaranteed an opportunity to possess** within a 10-minute regular-season OT period.
  3. **2025 Resolution G-2 (K-Balls):** Pre-gameday kicking-ball preparation permitted, shifting long field-goal range.
  4. **Roster & Depth Mechanics:** 48 gameday active players iff **>= 8 offensive linemen** dress (drops to 47 otherwise); max 2 weekly Practice Squad Standard Elevations (max **3 regular-season elevations per player**); **Emergency 3rd QB** must reside on the **53-man roster** (Practice Squad elevations ineligible per NFLPA veto).

---

## 3. Critical Week 10 Starter-to-Backup Depth Findings (`DEPTH-01`..`DEPTH-24`)

1. **Multi-String Cascading Unit Clusters (Offense & Defense):**
   - **New England Patriots (vs. DET in Munich):** Interior OL and backfield impairments: `Ben Brown` (listed C) **OUT** (knee); `Walter Rouse` **Limited, Questionable** (concussion) per the official report (earlier draft said DNP — corrected); Running Back `Rhamondre Stevenson` **Limited, Questionable** (knee; earlier draft said DNP — corrected) and `TreVeyon Henderson` **OUT** (illness) -> the official report lists no injury for 3rd-string RB Corey Kiner or 4th-string RB Lan Larison, so their status is 'not on report'. Cornerback `Carlton Davis III` **OUT** (knee) -> `Channing Canada` is not on the report; `Charles Woods` is **Full, Questionable** (hamstring; earlier draft said Limited — corrected).
   - **Baltimore Ravens (vs. LAC MNF):** `1st QB Lamar Jackson` on IR (right thumb; surgery) — the coach now says **6–10 weeks** (13 Nov roundup; earlier draft said 'minimum 4 games' — corrected). `2nd QB Tyler Huntley` out for season (turf toe; nfl.com news report headline). Replacement QB **Jacoby Brissett**: **press-only, not officially verified** (flag NFL-F22).
   - **Seattle Seahawks (at LV):** `1st QB Sam Darnold` — nfl.com's news headline says **ruled out**, but the report table lists him as DNP with no game status (conflict flagged NFL-F20). `2nd QB Drew Lock` is **Limited** and expected to start. Emergency 3rd-QB exposure depends on a healthy 53-man QB3, which was not verified.
   - **Green Bay Packers (vs. MIN):** Multi-starter DNP cluster confirmed by the official report across RB/C/LB/EDGE/Nickel (`Josh Jacobs` DNP, finger surgery per nfl.com news headline; `Sean Rhyan`, `Zaire Franklin`, `Lukas Van Ness`, `Javon Bullard` DNP).
   - **Arizona Cardinals (vs. LAR) — claim corrected:** the earlier draft said the interior OL and defensive spine were a DNP cluster. The official report does **not** support that: only `Hjalte Froholdt` (C) is DNP (and the 13 Nov roundup adds concussion, out). `Isaac Seumalo` is **Full**, `Roy Lopez` **Limited**, `Josh Sweat` **Full**, `Mack Wilson` **Full**, `Budda Baker` **Full**, `Andrew Wingard` **DNP**, `Jon Gaines II` **DNP** (ankle, out per 13 Nov). The Arizona starting QB (Carson Beck, per the 11 Nov headline) was missing from the earlier table.
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
