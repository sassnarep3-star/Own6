# Repo Audit — Own6 Empirical NBA Lab

**Audited upstream commit:** `77a28cccea34e0764f6d45ff3316d3aa8f6b90b7`
**Audit script:** `scripts/audit_sources.py`
**Outputs:** `data/empirical/source_audit.csv`, `data/empirical/repo_inventory.csv`, `data/empirical/repo_findings.csv`

## Scope

The audit reviews the upstream tracked files that existed when this session began, plus the official sources listed in `data/empirical/sources.json`. It does not modify upstream files. It does not scrape or republish NBA statistics.

## Method

- Each upstream data row was reviewed against an official source or explicitly marked unverified.
- The upstream file inventory was computed with line counts and SHA-256 checksums.
- Official pages were read directly with the page-fetch tool. Short citations identify the reviewed passage.
- Search-index-only evidence is not counted as direct verification.
- The Korean statute header was readable, but the dynamic article body was not returned. The injury PDF fetch failed. These limitations are flagged, not filled in.

## Results

| Output | Count |
|---|---|
| Upstream data rows reviewed | 63 |
| Upstream files inventoried | 43 |
| Reproducible findings | 20 |
| Official source records | 15 |

## Key findings

- **R01** — The original executive summary omits NBA Terms §9 gambling restriction and §1 reuse restriction.
- **R02** — The original validation gates were declared but not enforced; log loss, correlation honesty, and ledger integrity were missing.
- **R03** — The original leaderboard eligibility used only sample size and could mark a negative strategy eligible.
- **R04** — The original bootstrap resampled individual bets, breaking event dependence.
- **R13** — The original source registry labeled search-index evidence as verified.
- **R14** — The Korean statute article body was not independently reproduced.
- **R16** — The upstream site checker only scanned `docs/verified`, not the combined site.
- **R17** — The upstream test suite did not cover the failure modes above.

## Source links

All findings and audit rows include official source URLs or explicitly flag missing evidence. The full table is in `data/empirical/repo_findings.csv` and `data/empirical/source_audit.csv`.

## No betting advice

This is analytics research only. It does not place bets, accept stakes, distribute rewards, or provide picks.
