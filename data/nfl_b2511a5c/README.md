# nfl_b2511a5c: focused official-source re-check (2026-11-18)

Branch: `arena/b2511a5c-own6` (from `main` at `aa82798`). Claim: COORDINATION.md, session `b2511a5c`.
Public site: `docs/nfl-b2511a5c/` (built by `scripts/build_nfl_b2511a5c.py`, verified by `scripts/check_nfl_b2511a5c.py`).

## Executive summary

- **Scope.** The session brief limited this pack to what official reads support: the Week 11 slate, the
  Colts–Texans venue, Willis and Ravens QB roster status, and the Week 10 Lions injury designations.
- **Week 11 slate.** The official schedule (R03) lists 13 games and 6 bye clubs. Together these cover all 32
  clubs. The Thursday game is Colts at Texans, Nov 19, 8:15 PM ET, PRIME. The international game is Vikings at 49ers
  in Mexico City (R05), not San Francisco.
- **Colts–Texans venue.** Reliant Stadium, Houston, TX (R04). Read today.
- **Willis.** The reserve list dates his Reserve/Injured entry 11/10 (R06). The official article (R08) says he was
  placed on IR and misses Weeks 10–13. The article gives no byline date. "Tuesday" is not dated in the article.
- **Ravens QB.** The Ravens' club depth chart (R11, a club page) lists QB as Brissett / Fagnano / Slovis. It omits
  Jackson and Huntley. The official nfl.com roster (R12) lists Jackson and Huntley as RES. The repo's stale-QB flag
  (E5-F07) is therefore contradicted by today's club QB row. **RES is a roster status code, not a confirmed
  IR designation.** The date of the reserve transaction for Jackson and Huntley is **not verified**. The full
  reserve log has not been read.
- **Lions Week 10.** Kerby Joseph, Cade Mays and D.J. Reed are Out on the Week 10 page (R01; first of 8 chunks read).
  The rest of the Week 10 report (chunks 2–8) was not read. Row counts (repo 254 vs live 279) are **not
  re-verified**.
- **Gaps.** The Week 11 injury report is not posted (R02, 404). The Packers depth page is labelled "Unofficial"
  (R10, club site), so it is not an official depth source. The Ravens club page has a "Unofficial" label on neither of its two chunks. Al-Shaair has conflicting official labels (R04 "Did not
  participate" vs R06 reserve 11/17). It is unresolved.

## What is in this folder

| File | Contents |
|---|---|
| `official_reads.csv` | 12 reads (R01–R12): URL, host, class, chunks read, page status, SHA-256 of the raw capture, verbatim excerpt(s) |
| `raw/R01.txt`–`R12.txt` | Verbatim captures of the tool output, with links stripped. Not byte copies of the web pages. |
| `week11_slate.csv` | The 13 games (matchup, day, date, time, network, records, venue status) |
| `week11_byes.csv` | The 6 bye clubs and their records |
| `claim_checks.csv` | 14 claims from the repo and brief, each set against the live reads, with a verdict |
| `club_depth_reads.csv` | Club-site observations (Packers, Ravens). Outside the release-gate allowlist. |
| `flagged.csv` | Flags for manual review, each with evidence IDs and an owner action |
| `pack_suggestions.csv` | Options for the owner. Nothing is implemented. The owner column is blank. Named `pack_` on purpose: the `dfc0c1bc` consolidator scans every `data/nfl_*/suggestions.*` and `questions.*`, so these registers are kept out of that scan. The integration session decides whether to register them. |
| `pack_questions.csv` | Q/I/A register: what we have, what we lack, the next route (also `pack_` prefixed, for the same reason) |
| `sources.csv` | Each source URL, its host, class and read IDs |
| `refetch_log.csv` | Second fetch of each read, the chunks re-fetched, and the result |
| `raw/R13.txt` | October reserve list, all 25 rows (added after the first re-fetch pass) |

## Method and limits

- Each read was made with `fetch_page` on 2026-11-18. The tool does not expose per-request times or HTTP status
  codes, except that R02's body is a 404 page. Read windows are session-level.
- The raw captures were written from the tool output, so the SHA-256 values prove internal consistency only.
  Each excerpt is checked as a substring of its raw capture by `scripts/check_nfl_b2511a5c.py`.
- **Re-fetch (2026-11-18, same session).** Every read was fetched again and compared against its raw capture
  (`refetch_log.csv`). Eleven reads match. R09 was not re-fetched, and no claim depends on it. R13 is a first read, not a re-fetch. Partial chunk
  coverage on re-fetch: R01 (chunk 0 of 8), R03 (chunks 0, 2 of 3), R04 (chunks 0, 1 of 3), R05 (chunk 0 of 2)
  and R11 (chunk 0 of 2). See the log. **One correction:** R04's raw header said
  "chunk 0 of 3", but the venue lines are in chunk 1. The header now reads "chunks 0,1 of 3", the register
  says "2 of 3", and the SHA-256 was recomputed. The original hash was not kept.
- Only the chunks named in `chunks_read` were read. Anything else is not claimed.
- Club-website reads are listed separately. The release gate (`tools/release_gate.py`) allows only nfl.com and
  a few other hosts, so club pages cannot appear in standard official-source table rows.
- A blank field means "not confirmed". It never means zero, empty or available. "Not listed" is not treated as
  "available".

## Protocol deviation

The brief asked for `session-<id>/<task>` branches. The system fixed the branch to `arena/b2511a5c-own6`. This
follows the same deviation that prior sessions logged. The pack files were written before the COORDINATION claim
was committed; the claim is committed first, and this is logged in COORDINATION.md.
