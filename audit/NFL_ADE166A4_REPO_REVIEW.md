# Repository Review — session ade166a4 (2026-11-19)

Scope: line-by-line structural review of `sassnarep3-star/Own6` at branch `arena/ade166a4-own6`
(base `ffbbce6`), with re-execution of the standing gates and re-verification of inherited
findings. Every claim below is either (a) reproduced by a command run this session, or
(b) linked to an official source read this session. Nothing is inferred.

Baseline (from `scripts/audit_repo.py`, re-run after `git fetch --unshallow`):

| metric | value |
|---|---|
| files scanned | 1,359 |
| lines scanned | 136,773 |
| structured records | 20,366 |
| standing findings | 17 |
| audit verdict | OK |

Concurrent-work check: while this session worked, `origin/main` moved `ffbbce6 → d7127da`
(session `0050c939`, PRs #123/#124/#126 — its own `nfl_0050c939` scopes plus a dfc0c1bc
register regeneration). No file in this session's claimed scopes was touched by it. This
branch rebases onto `d7127da` before its next push; the rebase is additive-only from this
pack's side.

## 1. Structure

- 30 `data/nfl_*` pack directories at review time (29 before this pack) plus cross-cutting
  dirs (`data/empirical`, `data/nfl`, `data/assurance`, `data/source_coverage`).
- Per-pack script triad where present: `scripts/build_nfl_<id>.py`,
  `scripts/check_nfl_<id>.py`, `tests/test_nfl_<id>.py`, `.github/workflows/nfl-<id>-ci.yml`.
- Site: root `index.html`, `docs/index.html` hub, one `docs/nfl-<id>/` directory per pack,
  plus shared pages (`docs/leaderboard.html`, `docs/correlations.html`, `docs/flagged.html`,
  `docs/dashboard.html`).
- Root executive summaries: 20 `NFL_*_EXECUTIVE_SUMMARY.md` files; this session adds the 21st
  (`NFL_ADE166A4_EXECUTIVE_SUMMARY.md`).
- Working fixed-point sequence for shared-file changes (unchanged from prior reviews):
  `build_nfl_ade166a4.py` → `build_nfl_dfc0c1bc.py` (twice, for its rule 9) →
  `source_coverage.py` → `audit_repo.py` → `build_assurance.py`; do not run
  `scripts/build_review.py` (it does not exist).

## 2. Gates re-executed this session (all green at review time)

| gate | command | result |
|---|---|---|
| pack unit tests | `python3 -m pytest -q tests/test_nfl_ade166a4.py` | pass (see CI record) |
| site structure | `python3 scripts/check_site.py` | OK |
| repo audit | `python3 scripts/audit_repo.py` | OK (after unshallow) |
| data builder assertions | `python3 src/nfl_ade166a4/build_data.py` | 253+2 injuries / 32 clubs / 13 games / 25+12 transactions, all asserted |

## 3. Irregularities found / re-confirmed (with links)

New this session (published on this pack's Flagged for Review page):

1. **Waddle affiliation anomaly** — the Broncos table on the Week-11 injury hub lists
   Jaylen Waddle at both same-day reads, while the official November trades register (12
   rows, read this session) has no Waddle row and the Dolphins table does not list him.
   Observation published verbatim; explanation unverified. → ADE-F01.
   Sources: [injury hub](https://www.nfl.com/injuries/league/2026/reg11),
   [trades](https://www.nfl.com/transactions/league/trades/2026/11).
2. **Display-name vs URL-slug drift** — 'Jacob Hummel' vs `/players/jake-hummel/`;
   'Dee Alford' vs `/players/deaundre-ford/`. Display text published verbatim. → ADE-F02/F03.
   Source: [injury hub](https://www.nfl.com/injuries/league/2026/reg11).
3. **IR players still on the hub** — Al-Shaair (11/17) and Carlies (11/17) are Reserve/Injured
   per the reserve list yet appear on reg11 with DNP + blank game status at both reads.
   Corroborates the inherited a67ddef8 flag family. → ADE-F04.
   Sources: [reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11),
   [injury hub](https://www.nfl.com/injuries/league/2026/reg11).
4. **Standings H1 template tokens** — H1 renders `$year$ NFL $displayname$ Standings`
   unsubstituted at this read. Cosmetic; table body reconciles exactly. → ADE-F05.
   Source: [standings](https://www.nfl.com/standings/division/2026/reg).

Inherited findings re-tested against today's reads:

- Same-day zero-delta on the injury hub (2.1h window, 253/253 keys unchanged) — the hub is
  stable intraday between reads; designation cadence questions (Q-03, Q-08) stay open.
- Week-12 game statuses still unpublished (no reg12 read claimed this session; inherited
  a67ddef8 finding stands).
- Reserve-list render window (11/10–11/18 only) confirmed again at 11:11Z — pre-11/10 moves
  remain neither confirmable nor deniable. Source:
  [reserve list](https://www.nfl.com/transactions/league/reserve-list/2026/11).

## 4. Verification performed

- Fresh official reads logged in `data/nfl_ade166a4/capture_log.csv` (R101–R105), each with
  UTC clock and sha256 over the transcription artifact only (the artifact cannot prove what
  the page said at read time — stated in every row).
- Standings arithmetic recomputed: 32 clubs, W=149, L=149, T=2, PF=PA=6,923.
- Injury-hub delta computed mechanically by `src/nfl_ade166a4/build_data.py::compute_delta`
  over both same-day transcriptions: 0 added / 0 removed / 0 changed across 253 keys.
- 12 published prior-pack rows re-verified: 12 MATCH (`data/nfl_ade166a4/reverification.csv`).

## 5. Honest limits

- No market prices, no ROI/CLV, no correlation values, no profitability claim anywhere in
  this pack. Price columns stay blank by written policy because no official NFL page prints
  a market price.
- Zero-delta is only as strong as the cache question (Q-06): two fetches through the same
  tool cannot exclude CDN cache by themselves.
- The Week-11 injury corpus ends at kickoff for the Thursday game tonight; a post-game
  re-read (Friday) belongs to the next capture, not this one.
