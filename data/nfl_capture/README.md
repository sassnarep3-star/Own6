# Official injury-report capture (session 79fd4958)

**What runs.** `.github/workflows/nfl-official-capture.yml` runs
`scripts/capture_nfl_official.py` at 16:00 UTC on Sunday, Wednesday, Thursday,
Friday and Saturday, and on manual dispatch. It fetches
<https://www.nfl.com/injuries/> (the page resolves to the current week) and
records one row per run.

**What is stored where.**

| Item | Location | Visibility |
|---|---|---|
| Raw response bytes | workflow artifact `nfl-official-raw-<run_id>` | private to repo collaborators, 90-day retention |
| sha256, UTC clock, byte count, status | `data/nfl_capture/index.csv` (committed) | public, derived metadata only |
| Player-level text | nowhere in git | kept out until the terms of use are read |

Raw bytes are never committed (`.gitignore`: `data/nfl_capture/raw/`). If
replay beyond 90 days is needed, that is a decision for the repo owner after
the terms are read; it is logged in the flags, not decided here.

**Drift checks (fail loudly).** A run fails when any of these hold: HTTP status
is not 200; the page title lacks "Injury Report"; no "Week N of the YYYY Season"
label; fewer than 8 tables carry the exact header
`Player | Position | Injuries | Practice Status | Game Status`; any table
carries a near-miss header; fewer than 100 player rows; any data row does not
have 5 cells; the body is empty or the fetch errors. Each failed run still
appends its row (with the reason) and then exits 1.

**Index columns.** `capture_utc` (fetch clock, UTC), `requested_url`,
`final_url`, `http_status`, `bytes`, `sha256` (of the raw bytes),
`raw_file` (name of the artifact file), `page_title`, `week_label`,
`injury_tables`, `player_rows`, `blank_game_status_rows` (counted, never filled),
`changed_vs_previous` (`first` / `yes` / `no` / `unknown`), `status`, `failure_reason`.

**Limits, stated plainly.**
- Capture cadence is 5 days a week, not hourly. Monday and Tuesday are not captured.
- The page is captured as it is served at fetch time. A later re-publication
  that changes the page is detected only as `changed_vs_previous=yes`; the
  reason is not inferred.
- No conflict flags, no game-book data, and no snap counts are captured here.
- Until the first scheduled run is confirmed in GitHub Actions, the capture is
  unverified. See the coordination log for the run record.

**Sources.** Official page: <https://www.nfl.com/injuries/>. Observed on
2026-11-19 (UTC, fetch tool read, not this job): the unversioned URL served
the Week 11 report, title "Official Latest NFL Injury Report for Players - Week
11 of the 2026 Season | NFL.com". This is one observation on one day, not a
guarantee that the URL always points at the current week. The index's
`week_label` column records what each capture actually showed.
Week 11 versioned page, same day: <https://www.nfl.com/injuries/league/2026/reg11>.
