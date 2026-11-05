# Final integration review — 2026-11-05

Session: `arena/6eb8d991-own6`
Integrated local HEAD at review start: `3a517aa`
Publication target: `main` / legacy GitHub Pages `main:/`

**Concurrency update.** While this review was being committed, PR #49 merged the same five stale PRs into `main` at `aea6a5a` and added the separate November 5 daily snapshot. This branch was rebased onto that tree with both coordination records retained. Git omitted the duplicate local merge commits because their changes were already upstream; no concurrent daily, coverage or review work was reverted. PR #48 and PR #50 remain separate active sessions and are not represented as this session's work.

## Decision and evidence boundary

Publish the combined research framework, dated verification ledgers and irregularity register. **Do not publish a current betting line, qualified strategy, correlation estimate, ROI/CLV result or reward winner.** The authorized empirical ledger has zero observations and the leaderboard is empty.

This review distinguishes four things:

1. **Direct source read** — the linked official page was opened and the scoped text/value was read.
2. **Dated historical match** — a value matched when read on its recorded date; a dynamic page may since have changed.
3. **Internal recomputation** — local arithmetic agrees; this is not independent source confirmation.
4. **Unverified** — no adequate official value-level evidence exists; current-site value cells stay blank.

A source link is not a data-use license. NBA Terms §§1/6/9 and Korean-law applicability remain open for qualified review.

## Stale-PR integration preserved

| Pull request | Integrated commit | Disposition | Official project record |
|---|---:|---|---|
| #23 | `91ce915` | Preserved coordination/release evidence | https://github.com/sassnarep3-star/Own6/pull/23 |
| #28 | `324535d` | Preserved landing, summary and flags; reconciled with fail-closed assurance | https://github.com/sassnarep3-star/Own6/pull/28 |
| #31 | `83873ef` | Preserved ten-gate empirical hardening and assurance dashboard | https://github.com/sassnarep3-star/Own6/pull/31 |
| #32 | `967c85f` | Preserved parlay-safety review and tests | https://github.com/sassnarep3-star/Own6/pull/32 |
| #37 | `3a517aa` | Preserved 54-row dated ledger and source-link remediation; generated HTML rebuilt from combined inputs | https://github.com/sassnarep3-star/Own6/pull/37 |

Only `COORDINATION.md` and generated assurance HTML required content conflict resolution. Both board sides were retained; generated HTML was rebuilt rather than choosing one side. No other branch was created or pushed.

## Fresh direct review: all 15 November 2 finals

Each score below was re-opened on its official NBA.com game page on **2026-11-05** and compared with `data/verification_official_2026_11_03.csv`. Result: **15/15 match; zero score corrections**. These are final historical scores, not betting prices or evidence of model skill.

| Check | Recorded and freshly read result | Status | Official source |
|---|---|---|---|
| `0022600158` | OKC 117 – CLE 112 (Final) | match | https://www.nba.com/game/okc-vs-cle-0022600158 |
| `0022600159` | DET 124 – CHA 91 (Final) | match | https://www.nba.com/game/det-vs-cha-0022600159 |
| `0022600160` | ATL 108 – IND 104 (Final) | match | https://www.nba.com/game/atl-vs-ind-0022600160 |
| `0022600161` | BKN 90 – NYK 103 (Final) | match | https://www.nba.com/game/bkn-vs-nyk-0022600161 |
| `0022600162` | WAS 103 – ORL 94 (Final) | match | https://www.nba.com/game/was-vs-orl-0022600162 |
| `0022600163` | CHI 107 – PHI 126 (Final) | match | https://www.nba.com/game/chi-vs-phi-0022600163 |
| `0022600164` | SAC 115 – DAL 100 (Final) | match | https://www.nba.com/game/sac-vs-dal-0022600164 |
| `0022600165` | NOP 135 – MEM 134 (Final/OT) | match | https://www.nba.com/game/nop-vs-mem-0022600165 |
| `0022600166` | MIL 100 – MIN 112 (Final) | match | https://www.nba.com/game/mil-vs-min-0022600166 |
| `0022600167` | BOS 93 – HOU 109 (Final) | match | https://www.nba.com/game/bos-vs-hou-0022600167 |
| `0022600168` | UTA 97 – SAS 119 (Final) | match | https://www.nba.com/game/uta-vs-sas-0022600168 |
| `0022600169` | POR 118 – DEN 110 (Final) | match | https://www.nba.com/game/por-vs-den-0022600169 |
| `0022600170` | PHX 113 – GSW 116 (Final) | match | https://www.nba.com/game/phx-vs-gsw-0022600170 |
| `0022600171` | TOR 125 – LAC 118 (Final) | match | https://www.nba.com/game/tor-vs-lac-0022600171 |
| `0022600172` | MIA 117 – LAL 138 (Final) | match | https://www.nba.com/game/mia-vs-lal-0022600172 |

Machine-readable direct-read entries: `data/verification_log.csv` **V28–V42**, rendered on `docs/review/verification.html`.

## Fresh direct review: policy and method scope

| Ledger row | Fresh result on 2026-11-05 | Official source |
|---|---|---|
| P-01 / Terms §1 | Quoted Basketball Content reuse/linking restriction still matches. Permission is not established. | https://www.nba.com/termsofuse#ownership-and-use-restrictions |
| P-02 / Terms §6 | §6(2) describes qualifying word links; §6(5) restricts links to Services/team home pages and disallows internal-page links. Deep source citations remain flagged. | https://www.nba.com/termsofuse#links |
| P-03 / Terms §9 | §9(iv) gambling-use restriction and §9(vii) comprehensive-database restriction still match. No authorization is inferred. | https://www.nba.com/termsofuse#nba-statistics |
| P-04 / Stats FAQ | “Our stats are not available for download for either academic or personal use” still matches. | https://www.nba.com/stats/help/faq |
| P-05 / prediction markets | October 26 release names Kalshi/Polymarket and refers to aligned market restrictions; it does not enumerate specific prop/parlay bans. | https://www.nba.com/news/nba-establishes-integrity-framework-and-commercial-partnerships-for-prediction-markets |
| P-06 / Korean whole-law header | Whole law displays `[시행 2026. 9. 3.] [법률 제21742호, 2026. 6. 2., 일부개정]`; Article 26 view displays a different effective date. Discrepancy remains flagged, not resolved. | https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95 |
| P-07 / Article 26(1) | Korean prohibition text matches the scoped ledger claim; English remains a compiler summary. | https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95/%EC%A0%9C26%EC%A1%B0 |
| P-08 / Article 26(2)(1) | System design/production/distribution/public-provision prohibition text matches; applicability requires counsel. | https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95/%EC%A0%9C26%EC%A1%B0 |
| P-09 / Article 26(2)(2) | Sports-information prohibition for the stated purpose matches; no legal conclusion is drawn from location or project language. | https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%EB%AF%BC%EC%B2%B4%EC%9C%A1%EC%A7%84%ED%9D%A5%EB%B2%95/%EC%A0%9C26%EC%A1%B0 |
| Odds formula | Positive/negative American and decimal implied-probability formulas match the tested conversion scope; examples are not current NBA prices. | https://sportsbook.draftkings.com/help/how-to-bet/odds-calculator?intendedSiteExp=US-SB |
| Parlay arithmetic | Decimal prices multiply; this does not prove leg independence or value. | https://sportsbook.draftkings.com/help/how-to-bet/parlay-calculator |
| Spread settlement | Favorite/underdog signs and whole-number push/void explanation match the method reference. | https://sportsbook.draftkings.com/help/how-to-bet-spread |
| Injury reporting | Participation-status deadline and continual-update policy remain as represented; landing now lists November 5 reports. | https://official.nba.com/nba-injury-report-2026-27-season/ |
| Gaming partners | Page dated July 9, 2026 lists DraftKings/FanDuel domestically; no South Korea or Brazil entry appears in the returned table. | https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2 |

Direct-read entries: `data/verification_log.csv` **V43–V54**.

## Dynamic standings limitation

The 30 W-L rows in `data/verification_official_2026_11_03.csv` remain a **2026-11-03 historical match**, not current standings. A fresh read of https://www.nba.com/standings on 2026-11-05 shows the live table has advanced; for example PHI is **8–1**, not the dated **7–1**. Therefore:

- the fresh page does **not** independently reconfirm all 30 historical rows;
- no dated value is silently replaced with a current value;
- current-site navigation and summaries label the snapshot date;
- a future current-state analysis needs a new timestamped capture.

Concurrent PR #49 independently added `data/official_2026_11_05/standings.csv` and `docs/daily/standings.html` as a separate November 5 capture. That later snapshot is useful dated evidence, but it neither rewrites the November 3 ledger nor authorizes gambling-related reuse. Its descriptive model/correlation results remain outside the assurance leaderboard's all-gate qualification.

This limitation is V49 and public flag F28. It does not alter the 15 final scores above.

## Corrections and irregularities

| Item | Disposition | Source / record |
|---|---|---|
| NBA partner list incorrectly included Brazil | Corrected from the freshly read official table; no replacement country inferred | https://www.nba.com/nbabet/official-nba-gaming-partners-and-operators-2 |
| Utah W-L source was a schedule URL | Corrected to official standings; dated value remains 1–6 and is not represented as current | https://www.nba.com/standings |
| ESPN gamelogs called “official” | Relabelled third-party/secondary; estimate remains unverified | https://www.espn.com/nba/player/gamelog/_/id/3908809 |
| Unsupported “commercial-purpose” assertion | Removed; commercial status and legal applicability are not assumed | https://www.nba.com/termsofuse#nba-statistics |
| Outdated “no verified results” flag | Clarified: 15 scores are verified historical finals; sportsbook odds/prop prices remain unverified | https://www.nba.com/game/okc-vs-cle-0022600158 |
| 79 earlier score rows, legacy ratings, odds, props, ROI/CLV and unsupported correlations | Not freshly certified; remain blank/unverified in the current assurance view | https://github.com/sassnarep3-star/Own6/blob/main/data/assurance/row_audit.csv |
| NBA Terms §§1/6/9 and Korean-law date/applicability | Open needs-review disclosures; no license or legal conclusion inferred | https://www.nba.com/termsofuse |
| No root LICENSE | Still open; public visibility is not a reuse license | https://api.github.com/repos/sassnarep3-star/Own6 |

Public flags F28–F29 were added without deleting earlier flags. Existing findings are not marked resolved merely because a local check passes.

## Combined-tree checks completed before final navigation pass

| Check | Result | Project source |
|---|---|---|
| Dependency-free tests | 32/32 passed | https://github.com/sassnarep3-star/Own6/blob/main/tools/run_tests.py |
| Scientific suite | 120 passed, 6 subtests passed | https://github.com/sassnarep3-star/Own6/tree/main/tests |
| Arithmetic/recomputation | 213/213 passed; internal consistency only | https://github.com/sassnarep3-star/Own6/blob/main/scripts/verify_data.py |
| Dated official-value ledger | 54/54 recorded matches; 15 scores freshly reconfirmed above | https://github.com/sassnarep3-star/Own6/blob/main/data/verification_official_2026_11_03.csv |
| Empirical engine | fail closed: zero authorized observations, zero qualifiers, six frozen candidates, ten gates | https://github.com/sassnarep3-star/Own6/blob/main/data/empirical/report.json |
| Structural and link gates | Green locally before this review; final regenerated tree must be rerun | https://github.com/sassnarep3-star/Own6/tree/main/scripts |

Local green checks do not certify remote CI, live deployment, all inherited facts, data-use permission or betting skill. Final CI, merge SHA and Pages readback must be recorded separately after deployment.
