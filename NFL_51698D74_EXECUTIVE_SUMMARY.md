# NFL Pack 51698d74 — Executive Summary

**Session:** `51698d74` · **Branch:** `arena/51698d74-own6` · **Read date:** 2026-11-19 (UTC)
**Scope:** fresh official capture (standings, Week-11 injuries, Week-10 finals, Week-11/12 slates,
all 16 Week-12 game-centre venues, November reserve list), independent recomputation of the prior
pack's origination outputs, and the full decision-readiness register.

Site: [`docs/nfl-51698d74/`](docs/nfl-51698d74/index.html) ·
Decision readiness: 80 rows in [`data/nfl_51698d74/requirements.csv`](data/nfl_51698d74/requirements.csv) ·
Flagged (non-blocking): 12 rows in [`data/nfl_51698d74/flagged.csv`](data/nfl_51698d74/flagged.csv)

---

## 1. What was captured (all from official pages, 2026-11-19)

| capture | rows | source |
|---|---:|---|
| Standings, all 32 clubs (W-L-T/PCT/PF/PA/Net/Strk) | 32 | [nfl.com standings](https://www.nfl.com/standings/division/2026/reg) |
| Week 10 finals (incl. Monday LAC 23–20 BAL) | 14 | [week-10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) |
| Week 11 slate + venues (IND@HOU re-read; 12 carried) | 13 | [week-11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) + game centres |
| Week 12 slate + **all 16 game-centre venues** | 16 | [week-12 schedule](https://www.nfl.com/schedules/2026/by-week/week-12) + 16 game centres |
| Week 11 injury report (full register) | 253 + 2 markers | [reg11](https://www.nfl.com/injuries/league/2026/reg11) |
| November reserve list (render window 11/10–11/18) | 25 | [reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11) |

Capture honesty: 8 `capture_log.csv` rows, each `sha256` over the transcription artifact
bytes only — the log states on every row that the hash **cannot prove what the page said**.
`read_on_utc` is the artifact-write clock (upper bound on the fetch). Five artifacts carry data
lines confirmed identical to the prior-session transcription by row-by-row comparison against
this session's fresh read; their headers state this. The Week-12 venue and reserve artifacts are
new transcriptions.

## 2. Headline numbers (recomputed, not restated)

- **149 W / 149 L / 2 T** across **150 games**; **PF = PA = 6,923** (league identity holds;
  corpus totals match the fresh standings exactly, 32/32 clubs at league level).
- Realised home margin **−79/150 = −0.5267 → the published −0.53** (registered +2.5 is wrong
  for 2026; the removal-of-luck finding stands).
- **13/13 Week-11 fair lines MATCH** on independent recomputation with the frozen S01
  forecaster (max |Δmargin| 0.0045 pts; σ = 12.965). Market/difference columns blank by policy.
- **8/8 leaderboard Brier values MATCH** (control Brier 0.254094); **0 qualified strategies**
  (every Brier-skill lower bound negative). Staking never ranks.
- Correlations (official scores only, n=150): home margin vs total **r=−0.14** (CI −0.29..+0.02);
  home margin vs home points **r=+0.63**; total vs home points **r=+0.68**; home vs away points
  **r=+0.05**. Marginal only — never used for joint/parlay probabilities.
- Week-12 venues: **16/16 filled** (prior pack had 1/16): 11 exact, 3 mismatch, 2 variance
  against hotel params. New mismatch found: TEN@JAX EVERBANK (game centre) vs TIAA (hotel).
- Week-11 injuries: **253 player rows**, 13/13 games, CIN/WAS "No Injuries Reported";
  16 game statuses (all Thursday IND@HOU) — Sunday/Monday blanks are cadence, not gaps.

## 3. Flag re-tests (15 inherited findings, live re-read)

| outcome | count | examples |
|---|---:|---|
| **closed / confirmed** | 7 | A67-F01 Week-12 venues now 16/16 (CLOSED) · F-01 Week-11 report live (CLOSED) · F-13 LAC 23–20 FINAL (CLOSED) · VR-08 Lions designations (CLOSED, carried from a67ddef8) · A67-F09 Week-12 panels "not available" (CONFIRMED) · A67-F11 absence≠availability (CONFIRMED) · A67-F12 blanks=cadence (CONFIRMED) |
| **still open** | 5 | A67-F02 RELIANT legacy (re-read) · A67-F03 reserve window · A67-F04 IR blank status · A67-F08 Week-12 headings · A67-F10 LAR/LA drift |
| **not retested** | 3 | A67-F05 Lamar windows · A67-F06 Texans image depth · A67-F07 Packers prefixes (no club-depth fetch this session) |

## 4. New flags this session (12, all `blocking_merge=no`)

1. **516-F01/F02 (venue)** — 3/16 Week-12 mismatches (ACRISURE/Heinz, RELIANT/NRG, EVERBANK/TIAA);
   Houston game centres carry legacy RELIANT in both weeks. Both values published side by side.
2. **516-F03 (transactions)** — reserve list still renders only 11/10–11/18 (25 rows).
3. **516-F04 (designations)** — Al-Shaair & Carlies IR yet blank game status on reg11.
4. **516-F05** — Week-12 SNF/TNF headings contradict game lines (upstream error).
5. **516-F06** — depth-order source still unresolved (Texans image, Packers prefixes, shared/empty slots).
6. **516-F07** — no inactives, snap counts, Game Books or announced-starter evidence captured.
7. **516-F08** — raw rows public; terms not yet read; public/private split undecided.
8. **516-F09** — Questionable uncalibrated; no past-season archive.
9. **516-F10** — roof/surface + NWS overlay not captured.
10. **516-F11** — no weekly diff yet (single snapshot).
11. **516-F12** — kickoff/onside regime priors not estimated.

## 5. Reverification (8 recomputations)

Standings arithmetic · Monday settlement · realised home margin · 13 fair lines · 8 Brier values ·
4 correlations · Week-12 venue completion · reserve window — all MATCH (one MATCH-IMPROVED).
Full table: [`data/nfl_51698d74/reverification.csv`](data/nfl_51698d74/reverification.csv).

## 6. Repo review

[`audit/NFL_51698D74_REPO_REVIEW.md`](audit/NFL_51698D74_REPO_REVIEW.md) — no blocking repo
defect; all findings are upstream data-quality issues. Gates this session: pack checker 21 rules OK,
19 unit tests OK, determinism verified (data + registers + recompute + site rebuilds reproduce bytes).

## 7. Decision-readiness snapshot

- **80 requirements** tracked with blocking gate + clearing number
  ([`requirements.csv`](data/nfl_51698d74/requirements.csv), rendered on the pack landing page).
- **Satisfied this session:** 31 · **satisfied by prior packs (re-verified here):** 9 · **partial:** 15 · **blocked:** 25.
- **10 suggestions**, all `pending_human_choice=yes` — nothing implemented without a human decision.
- **14 questions**, all open (answers need named sources/licenses/terms, not guesses).

## 8. Honesty rules enforced by the checker

`scripts/check_nfl_51698d74.py` (21 rules): pinned row counts · official-host URLs on every
data row · standings/injuries/slate/reserve arithmetic · all 16 Week-12 venues filled ·
venue match counts 11/3/2 · no market prices or return claims · no inputs/selects/buttons ·
no placeholders · internal links resolve · gates+clearing numbers non-empty · suggestions
undecided · capture-log sha256 verification · deterministic rebuild · exactly six pages ·
non-empty retest findings · fair lines 13/13 MATCH with market blank · leaderboard 8/8 MATCH
with 0 qualified · correlations n=150 with Fisher bounds. Determinism also enforced in CI
(`.github/workflows/nfl-51698d74-ci.yml`).

## 9. What a human should decide next (suggestions register)

1. Normalize venue strings in a derived column (keeps both raw values).
2. Add a weekly game-centre-vs-hotel venue diff to the capture checklist.
3. Add reserve-list render-window fields to every capture.
4. Treat blank game-status as an explicit Pending state downstream.
5. Ask the Texans club for a text depth chart.
6. Apply Packers number-stripping with raw string retained.
7. Start the Wed/Thu/Fri injury-report series next week.
8. Publish the per-team availability view (starters out + net count; replacements blank).
9. Estimate the 2026 kickoff/onside regime effect before touching totals priors.
10. Decide the public/private data split after reading NFL + data-partner terms.

## 10. Sources

All 24 sources with last-read dates: [`data/nfl_51698d74/sources.csv`](data/nfl_51698d74/sources.csv)
(published at [`docs/nfl-51698d74/sources.html`](docs/nfl-51698d74/sources.html)).
Primary hosts: `nfl.com`. Hotel affiliate params are labeled cross-check only, never venue sources.
