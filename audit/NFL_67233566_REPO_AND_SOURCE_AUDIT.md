# Repository and source audit — session `67233566`, line by line

Audited 2026-11-15 on branch `arena/67233566-own6`, base `32a1b692ea6674b3755716e9926596e4772a3364` of
`main`. Machine-readable companions, all rebuilt from the frozen capture:
[`data/nfl_67233566/sources.csv`](data/nfl_67233566/sources.csv) (9 rows: what each page supports and
what it refuses to support), [`data/nfl_67233566/flagged.csv`](data/nfl_67233566/flagged.csv)
(15 flags), [`data/nfl_67233566/reconciliation_checks.csv`](data/nfl_67233566/reconciliation_checks.csv)
(220 identity checks), [`data/nfl_67233566/repo_findings.csv`](data/nfl_67233566/repo_findings.csv)
(RV-01…RV-07), and the 15-check verifier [`scripts/check_nfl_67233566.py`](scripts/check_nfl_67233566.py).

## 1. Method, in the order it happened

1. Read the branch note and the whole of `COORDINATION.md` (2,400+ lines, 47 session blocks). Claimed
   this session's scope with an explicit file list **before** writing anything, and pushed the claim
   first, so no other session's claimed file is touched.
2. Enumerated the repository's NFL-related files. Every prior pack was read as data, not as truth:
   `data/nfl_f4/results.csv` is pinned by commit and used as the Week 1–9 corpus **after** it reconciled
   against reads taken here; `data/nfl_market/injuries_week10.csv` is used only as the prior side of a
   delta, never as a league-wide count.
3. Fetched each official URL and recorded what the page returned *on the read date*, chunk by chunk,
   into one immutable text file (`data/nfl_67233566/raw/2026-11-15T2326Z_official_reads.txt`, sha256
   recorded in `capture_log.csv` and in every ledger row). Nothing in this pack is typed from memory.
4. Derived every published number from that file with one builder (`scripts/build_nfl_67233566.py`).
   The builder reads no clock and no network, and refuses to publish if a single reconciliation identity
   fails — so "0 mismatches" is a property of the build, not a claim about it.
5. Re-derived the same numbers a second time inside the verifier, from the committed CSVs rather than
   from the run, including recomputing the price hash chain and the blank-cell audit from the files.

## 2. Source-by-source finding list

| Source read | What it gave | What it did **not** give | Consequence in this pack |
|---|---|---|---|
| `nfl.com/schedules/2026/by-week/week-10` | 14 cards: pairings, scores, `Final`/`in progress`/`unplayed`, W-L-T badges | a finished week — 3 games were live and 2 unplayed at read time | Week 10 publishes as 9 graded finals + 3 live-at-read + 2 unplayed (`week10_at_capture.csv`); no live score can enter the corpus (`c06`, and a unit test) |
| `nfl.com/schedules/2026/by-week/week-11` | 13 fixtures with dates, times, networks, the Mexico City marker, and the bye list | results, injuries, any price, venues, or Week 16–18 flex slots (officially TBD until after Weeks 14/15) | the originate-able slate is 13 fixtures, all `graded=False`; the schedule-announcement requirement stays open with a dated reason |
| `nfl.com/standings/division/2026/reg` | 32 club rows: W/L/T, PCT, PF, PA, differential, streak, clincher markers | point-in-time history; also prints `AZ` where other pages print `ARI` | 220 reconciliation identities; the alias is published in `venues.csv` as a join hazard rather than silently normalised |
| `nfl.com/injuries/` (Week 10) | 50 player rows across 4 complete club sections + 1 truncated, practice status, sparse game status | a Week 11 report (the page's own selector stops at `WEEK 10`), a league-wide register, or any starter/depth order | availability is published as *edges and floors* per position group (`availability_graph.csv`, `replacement_depth.csv`); the 32-club sweep marks 27 clubs `not_in_chunk_read` with **no** counts filled (`c15`) |
| `nfl.com/games/colts-at-texans-2026-reg-11?tab=overview` | venue, network, both records, the At-a-glance ranking block, team leaders, both clubs' injury blocks, prior-game cards | any price (the "Ways to watch"/ticket blocks carry none), and any injury content — both printed "Injury Report is not available at this time" | one fixture gets a transcribed venue; the other 12 say so in `venues.csv`; the ranking block is the template for `fixture_context.csv` |
| Repo-pinned `data/nfl_f4/results.csv` | Weeks 1–9, 136 countable games | kickoff dates, times, venues — the capture stored no date column | used as corpus with `provenance=prior_capture_reconciled`; the missing date column is published as a finding, not repaired by guessing |
| Repo-pinned `data/nfl_market/injuries_week10.csv` | the same injury page one day earlier, 50 rows | adjudication between the four row counts in circulation (50 / 347 / 254 / 279) | a delta table with 0 changes over exactly the rows both reads share, and a drift alarm (`DRIFT-SCHEMA`) saying a zero delta over one chunk is not league-wide stability |
| `nfl.com` terms of service | nothing read this session | any permission inference in either direction | cited as `link_only` (S67-L01) and the reason SG-04 exists; the raw-capture rights question stays a human decision (Q-12) |
| `operations.nfl.com` | nothing — the report-cadence policy page was not located | the official Wed/Thu/Fri cadence, and the 4pm ET game-status deadline | the cadence is **not** asserted as verified; it appears only as the capture *design* in SG-02, and the failed search is logged (S67-N01, MC-05) |

## 3. Repository findings (all recorded, none edited outside this pack's scope)

| ID | Finding | Disposition |
|---|---|---|
| RV-01 | Several sessions' claims reserve the same additive edits to shared surfaces (`COORDINATION.md`, root `index.html`, `data/assurance/inventory.csv`); the file-level scopes are disjoint but the shared rows are not | this pack appends `COORDINATION.md`, adds one link line to the root index, and re-runs `scripts/source_coverage.py` so the inventory hash converges; the collision is logged for the integration session rather than resolved by editing another pack |
| RV-02 | `scripts/source_coverage.py` `PUBLISHERS` has no `nfl.com` / `operations.nfl.com` entry, so an official NFL read cannot count as coverage | request **R5** logged in `COORDINATION.md`; **not edited** (another session owns the tool) |
| RV-03 | `tools/release_gate.py` `OFFICIAL_HOSTS` lists `www.nba.com` but not `www.nfl.com` | request **R6** logged in `COORDINATION.md`; not edited. The gate's host allowlist only binds `docs/index.html` rows, and this pack's rows there are repo links, so the pack does not fail on it today |
| RV-04 | Corpus boundaries differ pack to pack (145 here, 44 there, 347 injury rows versus 50), which makes cross-pack comparison silently wrong | `corpus_summary.csv` publishes this pack's boundary keys; SG-06 proposes a `corpus_id` column on every leaderboard header |
| RV-05 | Prior packs' injury captures disagree with each other on row counts for one page | `drift_alarms.csv` `DRIFT-SCHEMA` fires with the four counts and demands a per-club pin plus a stored raw hash |
| RV-06 | Running the whole test suite regenerates other packs' published pages (`docs/daily/**` and several `docs/nfl-*/**`) as a side effect, because their tests call their builders | measured here: the outputs came back byte-identical, so nothing was dirtied — but a pack whose builder is not deterministic would show up as a phantom diff in someone else's commit, so this pack's own artefacts are pinned by `c01` plus the CI byte-identity step, and the hazard is recorded for the integration session |
| RV-07 | The strategy leaderboard concept is implemented at least three times (here, `nfl_d966f630`, `nfl_origination`) with different gate names and no shared register | SG-12 proposes one canonical desk; this pack deliberately does **not** rename anyone else's files, and instead publishes its own gate ids (G-01…G-13, DG-01…DG-07) with the rule text inline |

## 4. Irregularities in the sources themselves

The 15 flags are the full list, published at
[`docs/nfl-67233566/flagged.html`](docs/nfl-67233566/flagged.html) with a link per row. Three are marked
high: the Week 11 report's non-existence (selector ends at Week 10; both game-centre injury blocks print
"not available at this time"), the injury page's own club/position contradictions carried in from an
earlier read, and the four-count problem for one page. **None blocks the merge**, by the owner's rule —
they are published, not suppressed, and every one of them has a named action.

Two of the flags are about this pack's limits rather than the league's data: the depth register has zero
verified clubs (route a is text-unextractable for 4-of-32 sampled clubs and route b has no snap source),
and the personnel ablation could only be tested on 2 fixtures — which is exactly why the pack publishes an
ablation with `n=2` instead of a "points per missing starter" penalty it cannot justify.

## 5. What was refused, and on whose authority

* No price was filled from a third-party site, although one is reachable in principle: policy PX-01
  requires a source whose terms permit the read *and* whose page prints the number. The five capture
  attempts in `market_price_capture_log.csv` are the evidence that the blank is a result.
* No starter was derived from jersey order, experience or salary — the owner's reject list, recorded in
  `depth_source_register.csv` as `rejected_by_owner_keep_closed` so a later session does not re-propose it.
* No prop line, no prop outcome, no prop combo priced: no official register exists, so STR-11 is
  `blocked_no_source` and the division is published with zero entrants and the reason.
* Marginal prop probabilities were not multiplied into a parlay price. The same-game two-leg pair is
  measured jointly (n = 128, difference from independence −0.0161, CI [−0.0582, 0.0267]) and the gate
  says the pair may be *ranked*, not priced.
* No season-long ROI ranking, no win-rate leaderboard: the signal board ranks proper scores with a
  game-cluster lower bound and a Benjamini-Hochberg adjustment, and `win_rate` appears nowhere as a
  ranking key.
* No suggestion was implemented on the strength of being a good idea: all 12 rows of `suggestions.csv`
  are `awaiting_human_choice`, and the checker fails any page containing an input control.

## 6. Verification commands

```bash
python3 scripts/build_nfl_67233566.py                    # 58 tables, 20 pages, refuses on any mismatch
python3 scripts/check_nfl_67233566.py                    # 15 checks (c13 needs the claim commit)
python3 -m unittest discover -s tests -p test_nfl_67233566.py   # 36 tests
git diff --exit-code -- data/nfl_67233566 docs/nfl-67233566      # empty == nothing hand-edited
python3 tools/release_gate.py                            # repo-wide: markers, links, escaping
python3 tools/check_site.py                              # maintained pages: link + row-source rules
python3 scripts/source_coverage.py --check                # provenance coverage for every data file
```
