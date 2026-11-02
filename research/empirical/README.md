# Evidence-first NBA research extension

This is an isolated extension by Arena session `arena-5dfdc6d5`. It preserves the existing `src/own6`, `data`, and `docs` work. Its purpose is to make the difference between a **research hypothesis**, a **verified source fact**, a **computed estimate**, and a **qualified strategy** explicit.

## Important boundary

No authorized NBA gambling-use data license, historical sportsbook archive, or prospective prediction ledger was available. NBA.com's Terms of Use §9 restricts gambling-related use of NBA Statistics; §1 restricts public reuse. The NBA Stats FAQ says statistics are not available for download. This extension therefore does **not** scrape, republish, or invent NBA statistics, odds, correlations, or returns. Official-source links are citations, not a claim that reuse permission has been granted.

The automated pipeline runs without user input and produces an honest `not_run` report when its licensed observation ledger is empty. Synthetic fixtures exist only in tests; they are never included in the empirical leaderboard.

## Evidence files

- `data/empirical/sources.json`: directly read official sources and the limits of each source.
- `data/empirical/source_audit.csv`: row-level review of the upstream data, with official review links.
- `data/empirical/repo_inventory.csv`: checksum and line-count inventory of the upstream tracked files.
- `data/empirical/repo_findings.csv`: reproducible code/documentation findings, with immutable source links.
- `data/empirical/observations.csv`: empty, schema-only ledger; no real observations were available.
- `data/empirical/licenses.json`: empty rights registry; a self-asserted license is not accepted as proof.

Regenerate the audit with `python scripts/audit_sources.py`. The audit is a snapshot of the upstream tree at `77a28cccea34e0764f6d45ff3316d3aa8f6b90b7`; it does not silently overwrite another session's work.
