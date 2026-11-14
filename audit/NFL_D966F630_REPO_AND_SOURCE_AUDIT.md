# Repository and source audit — session `d966f630`, line by line

Audited 2026-11-14 on branch `arena/d966f630-own6`, against `main` at
`36c6f84a88c6c0ec01f9f4434b6590a4b0c973bd`. Machine-readable companions:
`data/nfl_d966f630/sources.csv` (what each page supports and refuses to support),
`data/nfl_d966f630/flagged.csv` (15 flags), `data/nfl_d966f630/results_feed_identities.csv`
(37 identity checks), and the 51-check verifier `scripts/check_nfl_d966f630.py`.

## Method

1. Read the branch note and the whole of `COORDINATION.md`; claimed this session's scope
   (P1–P12) with a file list before writing anything, and pushed the claim first.
2. Enumerated the repository's NFL-related files and read the prior pack's data in full,
   so this pack reuses its published numbers instead of duplicating or contradicting them.
3. Fetched each official URL this pack cites and recorded what the page returned *on the
   read date*, including the two things it returned that a reader would not expect: the
   standings page already counted the Week 10 Thursday game, and the injury report's club
   grouping contradicts its own position line for five players.
4. Recomputed every published derived number twice: once inside the pack's modules and
   once in the verifier, which re-derives the 14 published lines from `capture.py` rather
   than trusting `originated_lines.csv`.
5. Rebuilt the whole site and diffed it against what was written, then ran the shared
   repo gates (`tools/release_gate.py`, `tools/check_site.py`, `tools/run_tests.py`,
   `scripts/source_coverage.py --check`).

## What the sources actually support

| Source | What it gave | What it refuses to give |
|---|---|---|
| [Week 7 schedule](https://www.nfl.com/schedules/2026/by-week/week-7) | 14 FINAL games: both clubs, both totals, dates, per-game URLs | kickoff clock times; Weeks 1–6; any market |
| [Week 8 schedule](https://www.nfl.com/schedules/2026/by-week/week-8) | 14 FINAL games plus the four bye clubs and each card's post-game record badge | point-in-time records for bye clubs (the bye panel prints records as of render) |
| [Week 9 schedule](https://www.nfl.com/schedules/2026/by-week/week-9) | 15 FINAL games, two byes, the Madrid marker | kickoff times (cards print only "Nov 5/8/9"); any market |
| [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) | 14 matchups, one FINAL, 13 scheduled with date/network, Munich marker | any score for the 13 unplayed games; any price |
| [2026 division standings](https://www.nfl.com/standings/division/2026/reg) | 32 clubs × W/L/T/PCT/PF/PA/NET plus the printed LEGEND | the meaning of two further numeric columns; an as-of timestamp; week splits |
| [Official injury report](https://www.nfl.com/injuries/) | per club: slot, kickoff time, networks, both pre-game records, 347 players with position, injury, practice and game status | depth charts, snap counts, who replaces whom, any quantified effect of an absence |
| [2026 rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) | tie and roster conventions, cited by URL | anything about betting |
| [NFL.com Terms](https://www.nfl.com/legal/terms/) | the non-commercial and no-database rights boundary | permission to redistribute or to run a betting product on the data |
| [Prior pack's published lines](https://github.com/sassnarep3-star/Own6/blob/46391f1fe1362a0dc376e81f14694c1c1362a91b/data/nfl_309921cc/originated_lines.csv) | 14 rows of model lines used as the store's opening numbers | market and closing numbers, which that pack also left blank |

`nfl.com/scores/2026/by-week/week-9` returns 404 — the schedule path is the one that
prints finals. Five signed `routify-file-proxy…` URLs returned `SignatureDoesNotMatch`;
every value in this pack was re-read from the canonical `www.nfl.com` URL instead
(`flagged.csv` D966-F17).

## Findings against the repository

| ID | Area | Severity | Finding | Handled by |
|---|---|---|---|---|
| D966-A01 | Site data | **high** | No official or licensed source in this environment publishes a book price, so "fair vs market vs difference" can only be half-filled. The prior pack hit the same wall (its `NFL3-F08`). | All three columns exist; market and difference blank with `D966-F01` on every row; four capture attempts logged; suggestion `D966-S01` asks for a licence. |
| D966-A02 | Shared tooling | medium | `tools/release_gate.py`'s `OFFICIAL_HOSTS` does not include `www.nfl.com`, so an nfl.com link is only enforced by that gate for `docs/index.html` rows. | Request **R6** in `COORDINATION.md`; this pack's own verifier enforces the allowlist on all 16 pages, so the gap is closed without editing shared tooling. |
| D966-A03 | Shared tooling | medium | `scripts/source_coverage.py`'s `PUBLISHERS` list has no nfl.com entry, so published NFL tables classify as `other_link_only`. | Request **R5**; every row in this pack still carries a concrete source URL, and the coverage artifacts were regenerated so the shared audit stays in sync with the added pages. |
| D966-A04 | Consistency | medium | The injury and standings pages print `AZ` for Arizona while schedule/logo paths print `ARI`. The mismatch raised a `KeyError` in an early run of the model. | Single canonical key `ARI` throughout, with the alias recorded as data in `club_abbr_aliases.csv`. |
| D966-A05 | Source quality | medium | Five players are grouped under a club that contradicts their own position line, and one player is two different positions in two clubs on the same page. | Stored exactly as printed; nothing re-attributed; depth counts labelled floors (`D966-F12`). |
| D966-A06 | Source quality | low | Two official headlines disagree on the same quarterback's absence window (6–10 vs 6–9 weeks). | Both published side by side, no merged value (`D966-F13`). |
| D966-A07 | Method | **high** | Badges printed on a game card are *post-game*, and the bye panel on the same page prints records as of render, not as of that week — deriving "through week N" from those panels double-counts. | Every vintage table is derived by subtracting feed games from the standings read, then reconciled against the card badges: 86 matched, 10 clubs on bye with no badge, 0 mismatches. |
| D966-A08 | Method | high | A shrinkage factor fitted on the same games it is scored on is optimistic by construction, and at n = 43–44 the fits are unstable (the side fit returns λ = 0.0 at one vintage and 1.0 at another). | Published lines stay undamped (λ = 1.00); every fit is published as analysis with its n, its MAE at both ends of the grid and an in-sample caveat. |
| D966-A09 | Presentational | medium | A store whose markets mostly hold one snapshot would print a column of zeros that reads as a calm market. | `movement_status` distinguishes single-snapshot (zero by construction, flag `D966-F16`) from measured movement, and cross-version movement is flagged `D966-F02`. |
| D966-A10 | Repo hygiene | low | Adding pages to `docs/**` makes the shared source-coverage artifacts stale, because that audit inventories every published table. | `python3 scripts/source_coverage.py` re-run in this branch; `--check` now reports 0 stale artifacts, and the shared workflow rebuilds before checking. |
| D966-A11 | Safety | low | The task brief's earlier wording suggested `session-<id>/<task>` branches; Arena fixes this session to its own branch, and the sibling sessions recorded the same deviation. | All work on `arena/d966f630-own6`; deviation logged in this session's claim. |
| D966-A12 | Rights | medium | A leaderboard with cash rewards on betting outcomes would collide with the non-commercial/no-database terms and would point an autonomous agent at profit rather than accuracy. | Rewards are standing, compute priority and a badge; `reward_tiers.csv` states `reward_currency = none_no_monetary_payout` and why on every row. |

## Verification record for this audit

```
python3 tools/release_gate.py     →  Release gate: 0 issue(s) across published HTML and tracked text
python3 tools/check_site.py       →  STRICT PAGES: 13 | ERRORS: 0 | ADVISORY: 0
python3 tools/run_tests.py        →  RESULT: 53/53 tests passed
python3 -m unittest discover -s tests -p test_nfl_d966f630.py  →  Ran 61 tests … OK
python3 scripts/check_nfl_d966f630.py → 51 checks run, 0 failures — ALL CHECKS PASS
python3 scripts/build_nfl_d966f630.py → 41 CSVs + 16 pages, byte-identical on a second run
python3 scripts/source_coverage.py --check → 0 stale artifacts
```

## What this audit cannot claim

It cannot certify a value as "independently verified" in the sense the hub's ledger uses
(`data/verification_log.csv` is owned by another session and was not edited): the sources
here are official and re-read, but the certification column in the shared coverage audit
stays 0 for every published table, including this one, until the integration pass records
it. It also cannot produce any edge, CLV or ROI figure at all, because the number that
would anchor them — a market price — does not exist in this environment. A blank with a
cited reason is the correct output, and it is what was published.
