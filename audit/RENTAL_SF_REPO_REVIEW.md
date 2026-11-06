# Repo Review — SF Rental Increase Analysis Scope (RS1)

Session: `arena/983e0354-own6` · Date: 2026-11-06 · Base commit: `b5a53da` (main) + claim commit `2c2b126`

## What this repo is
`Own6` is primarily an NBA lines research lab plus prior re-verification and integration sessions.
Its tracked content (289 files) is what was reviewed for this scope: `docs/**` (98 HTML dashboards),
`scripts/**` (29 Python check/build tools), `data/**` (CSV/JSON ledgers), `.github/workflows/**` (10 CI files),
root docs (`README.md`, `EXECUTIVE_SUMMARY.md`, `research/**`, `audit/**`).

## Changes made by this session
- Additive only: `audit/RENTAL_SF_REPO_REVIEW.md`, `data/rental_sf/**`, `docs/rental-sf/**`,
  `EXECUTIVE_SUMMARY_RENTAL_SF.md`, `scripts/check_rental_sf.py`, plus append-only sections/records in
  `COORDINATION.md`, and (at integration) one additive nav link in `docs/index.html`.
- No pre-existing file, check, dataset or page was edited or deleted, except the single additive nav link
  in `docs/index.html` (integration step, logged in COORDINATION.md).

## Privacy scan (user requirement: tenant personal information stays internal)
Grepped the working tree for the user-supplied figures and identifiers before writing anything
(`git grep` over tracked files):
- No tenant names, initials, or personal identifiers appear anywhere in tracked content.
- The strings `3995` / `3150` matched only inside `COORDINATION.md` (this session's claim text) and
  incidental byte-count fields in `data/assurance/inventory.csv` / `data/source_coverage/rows.csv`
  (line counts/byte sizes, not dollar amounts).
- `94122` appears only in this session's claim text.
- Conclusion: no personal information about the tenants is present in the repo. The public site and
  all committed files anonymize tenants (Unit 1 / Unit 2; Tenant placeholders) and keep dates and
  amounts unchanged, as the user directed.

## Existing check tooling — run this session (results)
| Check | Command | Result |
|---|---|---|
| Site check | `python3 scripts/check_site.py` | OK — 9 pages; data rules pass; 0 broken internal links; all external links https |
| Assurance check | `python3 scripts/check_assurance.py` | OK — 9 pages; 2011 table rows official-HTTPS-sourced |
| Verify ledger check | `python3 scripts/check_verify.py` | PASS — 6 pages; 73 rows; 54/54 checks match; 8 unverified (as published) |
| Link check | `python3 scripts/linkcheck.py` | PASS — 7 pages; 322 links; 240/240 data rows sourced |

The NBA/Korean-law corpus itself was **not** re-verified line by line by this session — it was
independently re-verified by prior sessions (see `audit/SESSION_63A5B5EF_RECHECK.md`,
`audit/INDEPENDENT_REVIEW_B1BDFB4B.md`, and the verification-ledger sections of COORDINATION.md).
Re-reading it here would duplicate work already done and reviewed on `main`.

## GitHub Pages configuration (verified via API, 2026-11-06)
- `GET /repos/sassnarep3-star/Own6/pages` → `build_type: legacy`, source `branch: main`, `path: /`,
  status `built`, url `https://sassnarep3-star.github.io/Own6/`.
- Root `index.html` redirects to `docs/assurance/`. The rental section publishes at
  `https://sassnarep3-star.github.io/Own6/docs/rental-sf/`.
- Note (doc drift, informational): top-of-file docs in older README sections describe Pages as serving
  from `main /docs`; the live API shows `/` (root) with a redirect at root. Functionally equivalent for
  the `docs/**` tree; logged for review, not changed.

## Irregularities / observations (for the user's review)
1. Pages source path (`/`) vs older README wording (`/docs`) — doc drift, informational; site works.
2. `README.md` still describes the project purely as the NBA research lab; it does not mention the new
   rental section. Out of this session's scope to rewrite README; logged here and in COORDINATION.md.
   (A pointer is included in `EXECUTIVE_SUMMARY_RENTAL_SF.md` instead.)
3. Open PRs #52, #54, #56 (carried from prior sessions) are not part of this scope and were not touched.
4. `scripts/audit_sources.py` base-object issue and the "Utah schedule-citation request" remain open for
   their owners per prior COORDINATION.md records; not this session's scope.
5. No tenant data, lease documents, or rent histories exist in-repo; every unit-specific figure on the
   site traces to the user's brief (dates/amounts kept) and is labeled as such, not as an official record.
6. Building coverage classification (multi-unit vs condo/single-family) is **not confirmable** from
   official sources by this session; both coverage paths are documented on the site, and the assumption
   (multi-unit, pre-1979 → covered) is flagged prominently rather than asserted.

## Scope boundary
This review is of the repository as a publishing surface for the rental analysis. It is not an audit
of the NBA research claims themselves (already performed and linked above), and it is not legal advice.
