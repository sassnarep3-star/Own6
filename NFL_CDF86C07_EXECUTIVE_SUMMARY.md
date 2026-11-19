# NFL Pack cdf86c07 — Executive Summary

**Session:** `cdf86c07` · **Branch:** `arena/cdf86c07-own6` · **Read date:** 2026-11-19 (UTC)
**Site:** [`docs/nfl-cdf86c07/`](docs/nfl-cdf86c07/index.html) (live after merge at the Pages URL under `/nfl-cdf86c07/`)

## What is captured (official nfl.com, read 2026-11-19)

| Capture | Rows | Source |
|---|---:|---|
| 2026 standings, all 32 clubs | 32 | [nfl.com standings](https://www.nfl.com/standings/division/2026/reg) |
| Week 11 games (time, network, printed records) | 13 | [nfl.com Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) |
| Week 11 teams on bye | 6 | same page |
| Dated schedule announcement (Weeks 16–18) | 3 notices | same page |

## Headline numbers (arithmetic on the captured values)

- League record **149 W · 149 L · 2 T**; points **PF = PA = 6,923** (identity holds).
- All 32 standings rows match an earlier independent transcription in `data/nfl_51698d74/`.
- Week 11: 13 games + 6 byes = all 32 clubs; every printed record agrees with standings.

## What is blocked, and why (82 requirements in the brief)

Status counts: captured 12 · decided 6 · partial 31 · blocked 21 · open 12. Full register on the site
(`requirements.html`) with the blocking gate and the clearing number for each.

Main blockers:
1. **No betting-line source.** No official NFL page publishes a market price, so price snapshots, residuals,
   vig-free consensus and ROI are blank by policy (CDF-06).
2. **Depth order not verified for 32 clubs** (Texans depth is an image; Packers prefix jersey numbers).
   Depth-, starter- and backup-based features cannot be built on this evidence (CD-51).
3. **No inactives, snap counts, Game Books, roof/weather or injury series** captured this session.
4. **Corpus mismatch**: 136-game log vs 150 official finals (CDF-04, Q-11).

## Decisions for the owner

Ten suggestions are on the site's **Suggestions** page (review only, none implemented). Fifteen questions,
each with a discovery path, are on the **Questions** page. Non-blocking flags are on **Flagged for Review**.

## Honesty boundary

Nothing here is a betting recommendation, pick, or payout claim. No strategy is shown to beat a control.
