# NFL consolidated review — line-by-line audit and provenance record

**Session:** `arena/44136693-own6` · **Audit date:** 2026-11-13
**Branch:** `arena/44136693-own6` (branched from `main` at `d18f495`)
**Scope claimed:** NFLR-1 … NFLR-6 in `COORDINATION.md`

---

## 1. Method and evidence boundary

Every claim in this audit rests on one of three things, and each is recorded differently:

1. **A direct read of an official page** made in this session on 2026-11-13. These are listed in
   `data/nfl_review/official_reads.csv` (18 rows) with the retrieval method, a verbatim excerpt, what
   the page supports and what it does not support. Rows are marked `verified_direct` only where the
   body of the page was actually read.
2. **A labelled computation from data committed in this repository.** These carry the method and the
   input in the same row so a reader can recompute them.
3. **Nothing else.** A hyperlink is not verification. A checksum is not verification of meaning. An
   internal consistency check is not a source read. A recomputation is only verification of the thing
   recomputed.

Values that could not be confirmed are blank and flagged. The word "blank" in this project always means
*not confirmed from an official source*, never "zero" and never "not applicable".

---

## 2. What was read

| ID | Publisher | Page | What it was used for |
|---|---|---|---|
| NR-S01 | NFL | `https://www.nfl.com/standings/` | 32-club standings: W-L-T, PCT, PF, PA, NET PTS, splits, streak |
| NR-S02 | NFL | `https://www.nfl.com/schedules/2026/reg10/` | Week 10 matchups, dates, kickoffs, networks, the completed Nov 12 final, the four bye clubs |
| NR-S03 | NFL | `https://www.nfl.com/injuries/` | Week 10 participation and status tables (decision-relevant subset) |
| NR-S04 | NFL | Friday Nov 13 league roundup | Final club availability designations for Week 10 |
| NR-S05 | NFL | Wednesday Nov 11 roundup | Browns to start Deshaun Watson; Cardinals to start Carson Beck |
| NR-S06 | NFL | Dolphins place Malik Willis on IR | IR placement; Kyle McCord in line for first start |
| NR-S07 | NFL | Josh Jacobs undergoes finger surgery | Surgery and return timeline |
| NR-S08 | NFL | Sam Darnold ruled out | Seahawks Week 10 availability; Drew Lock expected to start |
| NR-S09 | NFL | Puka Nacua likely to be placed on IR | Turf toe, sprained MCL and PCL |
| NR-S10 | NFL | Tuesday Nov 10 roundup | Bills acquire Amani Hooker; Broncos trade for Daiyan Henley |
| NR-S11 | NFL Operations | CBA summary | 48 active gameday players, at least eight offensive linemen, term through 2030 |
| NR-S12 | NFL Operations | 2026 NFL Rulebook | The live official rulebook page and the four listed changes |
| NR-S13 | NFL | Terms of Use | Individual, non-commercial, informational use; no systematic retrieval without prior written consent |
| NR-S14 | NFL | Betting-partner release | Official partners and integrity policy, including rejection of injury- and officiating-linked wagers |
| NR-S15 | NIST/SEMATECH | Confidence limits | The correct interpretation of a confidence interval, and the limit on any skill claim |
| NR-S16 | GitHub API | `leesharpe/nfldata` | Upstream licence status (`license: null`) and repository metadata |
| NR-S17 | codeload | Upstream archive at `6ea0be6…` | Independent reconstruction of the lines-lab dataset |
| NR-S18 | NFL | Official Week 10 league injury report | All 28 playing clubs, 326 player rows with injury, practice status and game designation |

**Routes that were tried and abandoned.** `https://www.nfl.com/standings/league/2026/reg10` returns
"No Standings Available"; the generic standings page is the working route. Direct `curl` and `urllib`
requests to `www.nfl.com` fail in this environment with an SSL error, so every read above was made with
the page-fetch tool.

---

## 3. Repository audit — what was checked, file by file

| Area | Files | Result |
|---|---|---|
| `docs/nfl/` | 13 pages | Regenerated pages are byte-identical to the builder output. Source links resolve. The published `data/nfl/sources.csv` contained a 404 rules URL, a redirecting terms URL, two 2024-season links and a policy PDF that does not return readable text; all are now repaired or flagged by session `5a49ead3` |
| `docs/nfl-3b81013c/` | 11 pages | 49 injury/depth rows and 14 originated lines reconciled against the official read |
| `docs/nfl-origination/` | 11 pages | 32-club standings reconcile exactly against the official league identity; the Week 10 bye row still packs four clubs into single fields, which is flagged and was corrected by session `c1125799` |
| `docs/nfl/lab/` | 14 pages (PR #68) | Merged into this branch. The dataset reproduces byte-for-byte; the licence does not exist |
| `docs/nfl-review/` | 9 pages | New. Built from the registers in `data/nfl_review/` |
| `data/nfl_review/` | 12 registers | New. Every row carries a source URL or an explicit reason for being blank |

### 3.1 The 496-row ledger

`data/nfl_review/value_reconciliation.csv` holds one row per published claim:

`check_id, published_file, published_row_id, field, published_value, official_value_read_2026_11_13,
result, note, official_source_url`

Results: **455 match · 34 differ · 0 not_checked · 6 not_found_in_2026_11_13_capture ·
1 unverified_no_player_named**.

Coverage. The ledger compares every cell of five published registers against the official reads:
the through-Week-9 standings snapshot (`data/nfl_origination/verified_standings_2026_w10.csv`, 192
rows), the live standings snapshot added by the concurrently merged live-verification session
(`data/nfl_origination/standings_live_2026_11_13.csv`, 160 rows), the published Week 10 slate
(`data/nfl_origination/week10_slate_and_lines.csv`, 71 rows), the Week 10 pack's injury and depth
register (`data/nfl_3b81013c/injuries_and_depth.csv`, 49 rows) and the origination pack's depth chains
(`data/nfl_origination/injury_and_depth_deficiency.csv`, 24 rows). Nothing was sampled: every cell of
every register is in the ledger.

What each result means:

- `match` — the published value equals the official value read on 2026-11-13.
- `differs` — they disagree. This is **not** an assertion that the published value was wrong: the
  official injury report and the standings page are republished continuously, and a dated snapshot
  legitimately ages. Each such row says so and is flagged for review. No published value was changed by
  this session.
- `not_checked` — the published cell is an expectation ("Active Expected") or a derived figure with no
  official counterpart, so there is nothing to compare.
- `not_found_in_2026_11_13_capture` — the named player does not appear in the official Week 10 league
  injury report, which lists every player of every club with a reportable status, nor in the Friday
  roundup. Absence from a decision-relevant capture is **not** proof that a claim was false.
- `unverified_no_player_named` — the published row names no player, so no player-level claim exists to
  confirm.

### 3.2 The specific discrepancies

- **Standings (34 of 36 differences are in this class).** The published `verified_standings_2026_w10.csv`
  is a dated pre-game snapshot; the official page has since advanced as games were played. Every
  difference is an ageing snapshot, not a transcription error. The published file is left untouched.
- **Player status.** The official Week 10 league injury report shows Jaxon Smith-Njigba, Christian
  McCaffrey and Dre Greenlaw with practice participation and no game designation, and Joey Porter Jr.
  not participating in practice. A secondary pack carries different statuses for the same players. These
  rows are **not** republished as current; they are reconciled and flagged.
- **Record formatting.** `3-5-0` and `3-5` are equivalent and are compared as such; club abbreviations
  are normalised; practice-table rows are matched to designation rows by player and club.

---

## 4. PR #68 provenance — seven checks

`data/nfl_review/pr68_verification.csv`.

| Check | Subject | Result |
|---|---|---|
| PR68-01 | Committed dataset SHA-256 equals the value recorded in the metadata | **pass** — `9fe5bd67…3090` recomputed locally |
| PR68-02 | Committed dataset row count equals the recorded count | **pass** — 3,167 data rows |
| PR68-03 | Committed dataset byte size equals the recorded size | **pass** — 523,913 bytes |
| PR68-04 | Committed dataset column list equals the recorded list | **pass** — 24 columns in the recorded order |
| PR68-05 | The upstream commit is the one that was retrieved | **pass** — `6ea0be6dd9bfc95c818c05568753bc70f1986ea2`, confirmed via the GitHub API |
| PR68-06 | The upstream repository declares a licence | **fail** — GitHub API `license: null`, no licence file in the archive root |
| PR68-07 | Independent reconstruction from the upstream archive | **pass** — the digest was reproduced exactly |

### 4.1 The reconstruction, stated precisely

The upstream `data/games.csv` at commit `6ea0be6…` was filtered to `game_type == REG` and
`season >= 2015`, the 24 recorded columns were written in the recorded order, and the file was written
as minimal CSV with CRLF line endings. The SHA-256 of that output is
`9fe5bd67210691255cf90af21e39cc242b606f253dbc65198b7915565ce83090` — identical to the PR's recorded
value.

**What that proves:** the PR's committed dataset is a byte-exact transformation of the upstream archive
at the recorded commit. **What it does not prove:** that any historical row is accurate, that any price
column is a real market price, that any model has predictive value, or that the repository may lawfully
redistribute the data. The upstream declares no licence, which means the data is published by default
without redistribution permission.

The dataset is therefore labelled community-compiled and non-official everywhere it appears, and no
figure derived from it is described as a verified market result.

### 4.2 The backtest

The lines lab reports 2025 holdout ROI of approximately −1.22 %, −3.69 % and −7.50 % for its three
testable candidates, with confidence intervals that include zero, and `no_profitability_claim: true`.
That is reported as a computation on non-official data. It is not a league result and not a market
result, and nothing in this session describes it as either.

---

## 5. Depth deficiencies — why every index is blank

The official injury report gives availability. A depth deficiency — what a unit loses when a second or
third string player starts — needs two things: the club's depth order, and the replacement's expected
snap share.

- The depth order exists as an official club page for **8 of 32 clubs** in this repository (Patriots,
  Lions, Commanders, Giants, Vikings, Packers, Browns, Cardinals). Those pages list names by position
  group; they do not publish a string number.
- Snap share and expected-points-added drop-off exist **nowhere** as an official source. The league's
  next-gen-stats programme is the only plausible route and is not public.

Therefore all 32 `deficiency_index` cells in `data/nfl_review/depth_status.csv` are blank, each with
the reason stated on the page. Filling them would require inventing numbers, which the brief forbids.

---

## 6. Irregularities

Twenty rows in `data/nfl_review/irregularities.csv`, each published on the Flagged for Review page with
its source, severity, status and the requested action. Flagged items do not block publication. The
highest-severity entries:

| ID | Severity | Subject | Finding |
|---|---|---|---|
| NFLR-F04 | high | Sources | The NFL Lab source register cites `https://www.nfl.com/official-nfl-rules/`, which returns an official NFL 404 page. Re-pointed at the live 2026 rulebook by session `5a49ead3`; retained here as the independent record of this session's own read |
| NFLR-F09 | high | Data rights | The dataset used by the lines lab comes from a community repository that declares no licence. Redistribution rights are unresolved. This is the check that fails (PR68-06) |
| NFLR-F10 | high | Market data | The historical moneyline, spread and total columns are community-sourced prices, not official league prices. Any ROI computed from them is a community-data estimate and must never be described as a verified market figure |
| NFLR-F13 | high | Compliance | The three official NFL betting partners agreed to prohibit wagers the league finds objectionable, including injury- and officiating-linked wagers. Disclosed on the injuries page; any injury-driven product inherits this exposure |
| NFLR-F16 | high | Market data | No closing line has ever been confirmed for any bet, so the strongest available luck control is unavailable |
| NFLR-F03 | medium | Injuries | Eighteen published practice-status claims differ from the official Week 10 report read on 2026-11-13. A secondary pack conflicts with the official report for several named players; the legacy rows are not republished as current |
| NFLR-F08 | medium | Rules | The CBA page read on 2026-11-13 states the 48-player gameday active roster and the eight-offensive-lineman rule. It does not establish the size of the 53-man Active/Inactive List |
| NFLR-F12 | medium | Injuries | A published Week 10 depth row lists Amani Hooker as a Dallas defensive back, while NFL.com reports him acquired by Buffalo |
| NFLR-F18 | medium | Depth | Twenty-four of the 32 clubs have no official club depth-chart page captured, so the 2nd, 3rd and 4th string order is unknown for them |
| NFLR-F19 | medium | Depth | The published depth chains cite eight club depth-chart pages that were not re-read in this session, so their content is not confirmed here |
| NFLR-F14 | medium | Consistency | Three gate sets use the same identifiers for different gates (`G1-G8`, `G01-G10`, `G1-G8`) |
| NFLR-F01 | medium | Site structure | Four NFL sections are published side by side with overlapping requirements, questions and suggestions |
| NFLR-F06 | medium | Sources | The NFL Lab source register labels the 2017 injury-report policy PDF `verified_direct` although the text did not return |
| NFLR-F11 | low | Sources | The official standings page shows two record columns that its own legend does not define |
| NFLR-F15 | low | Repository | The repository has no LICENSE file |
| NFLR-F17 | low | Consistency | The three packs write the same concept three ways: DNP, LP and LIMITED for practice participation |
| NFLR-F20 | low | Status | Four executive summaries and four sets of flag lists exist, one per pack, with no statement of which governs |
| NFLR-F02 | low | Data freshness | Eight published standings values for the New York Giants and Washington Commanders no longer match the official page, because the published file is a pre-game snapshot and the league has since played |
| NFLR-F07 | low | Navigation | The README publishes the live URL `https://sassnarep3-star.github.io/Own6/nfl/`, which is not the live path |

Every flag is published on the Flagged for Review page with its evidence, why it matters, the requested
action and its status. Flags do not block publication.

---

## 7. Cross-session requests (logged, not edited by other owners)

| Request | Target owner | Requested change |
|---|---|---|
| NFLR-REQ-01 | owner of `docs/nfl/**` and the README live-URL line | The README published `https://sassnarep3-star.github.io/Own6/nfl/` while the live path is `https://sassnarep3-star.github.io/Own6/docs/nfl/`. Correct the URL |
| NFLR-REQ-02 | owner of `data/nfl/sources.csv` | `S-NFL-07` cited `https://www.nfl.com/official-nfl-rules/`, which returned an official NFL 404 page. Re-point at `https://operations.nfl.com/rules-officiating/2026-nfl-rulebook` and re-verify |
| NFLR-REQ-03 | owner of `data/nfl/sources.csv` | `S-NFL-09` should cite `https://www.nfl.com/legal/terms/`; `https://www.nfl.com/terms/` resolves to the subscription terms, a different scope |
| NFLR-REQ-04 | owner of `data/nfl/sources.csv` | `S-NFL-06` was labelled `verified_direct` but the linked 2017 injury-report policy PDF did not return readable text. Downgrade to link-only until the text is read |

Requests NFLR-REQ-02 to NFLR-REQ-04 were independently confirmed as live defects by session `5a49ead3`
before this session began, and that session repaired `data/nfl/sources.csv` directly. They are retained
here as the audit trail for this session's own review, which read the same pages independently.

---

## 8. Gates and reproducibility

| Gate | Command | Result |
|---|---|---|
| Rebuild the review pages | `python3 scripts/build_nfl_review.py` | 10 files written, byte-reproducible |
| Page gate | `python3 scripts/check_nfl_review.py` | 9 pages, 1129 table rows, 496 ledger rows, 20 flags, 18 source reads — no problems |
| Reconciliation gate | `python3 scripts/verify_nfl_review.py --check` | 496 compared values and 7 PR #68 checks reproduce exactly |
| Regression suite | `python3 -m unittest discover -s tests -p test_nfl_review.py` | 33 tests, all passing |
| Repository gate | `python3 tools/release_gate.py` | run as part of the final integration |

The gate fails the build if a published table row has no source link, a cell contains a placeholder, a
table row has the wrong number of cells, a relative link does not resolve, an external link is not
`https`, an input element appears, an irregularity or source read is missing from its page, or a
published row is missing from the ledger.

---

## 9. Limits of this audit

- This audit covers the NFL packs in this repository as of 2026-11-13. It does not validate any
  strategy's economic merit, because no strategy has passed a gate.
- The ledger compares against a single dated read. A later read may legitimately differ.
- Absence from the capture is not evidence of falsehood. Six rows remain unresolved for that reason and
  are published as unresolved rather than as corrections.
- Whether the upstream community dataset may be redistributed is a legal question this audit does not
  answer. It records that no licence was found and leaves the decision to the owner and counsel.
- Applicability of NFL.com's terms, the betting-partner policy and the CBA to any intended use is
  flagged for qualified counsel, not asserted here.
