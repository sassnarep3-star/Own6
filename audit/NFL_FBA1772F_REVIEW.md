# NFL decision-guide review — session `fba1772f`

**Review date:** 2026-11-19 (UTC)
**Scope:** existing core NFL dashboard and registers (`docs/nfl/`, `data/nfl/`), the source/decision artifacts referenced by those pages, and the immediate official-evidence records in `data/nfl_ade166a4/` and `data/nfl_d713b52f/`. This is not a claim that every line in the 1,000+ file repository or every external source was freshly verified.
**External source limitation:** network retrieval of NFL pages is not available in this tool environment. I read local committed files and their source metadata, but did not fetch any official page in this session. Accordingly, this report does not mark external content freshly verified.

## Deliverables and checks

- `docs/nfl-fba1772f/` — standalone decision guide with overview, seven prioritized proposals, eight Q/I/A rows, five flagged repository issues, and source limitations.
- `NFL_FBA1772F_EXECUTIVE_SUMMARY.md` — concise project decision summary.
- `scripts/check_nfl_fba1772f.py` — offline local-link and table-row-source-link checker.
- Each table row in the new page has an HTTPS context/source link and states limits; external links are not represented as checked in this session.

## Files read in the scoped audit

1. `data/nfl/decision_questions.csv` — 10 rows; fields include what is known/missing, answer state, discovery suggestion, URL.
2. `data/nfl/suggestions.csv` — 3 rows (S01–S03); all displayed as needs review.
3. `data/nfl/requirements.csv` — 18 rows.
4. `data/nfl/flagged.csv` — 13 rows, including rights/data, price, injury-policy, and depth gaps.
5. `data/nfl/sources.csv` — 26 rows; checked-date and support/not-support descriptions read.
6. `data/nfl/validation_gates.csv`, `origin_strategies.csv`, `leaderboard.csv`, `correlations.csv`, `injury_tracking.csv`, `depth_model.csv` — table headers and data rows read for the core research/validation boundary; no fresh model values were computed.
7. `docs/nfl/index.html`, `suggestions.html`, `questions.html`, `sources.html`, `requirements.html`, `validation.html`, `leaderboard.html`, `correlations.html`, `injuries.html`, `depth.html`, `flagged.html`, `lines.html`, `strategies.html` — navigation, counts, rendered table rows, and source links checked where relevant.
8. `research/NFL_SUGGESTIONS.md` — suggestion IDs/count and choice sequence cross-checked against the rendered page.
9. `data/nfl_ade166a4/capture_log.csv`, `delta_summary.csv`, `questions.csv`, `flagged.csv`; `data/nfl_d713b52f/sources.csv` — inspected as evidence of prior captures and Game Book provenance, not independently reverified.
10. `COORDINATION.md` — read before task claim; scoped claim recorded and pushed first.

## Findings (local repository comparisons)

- **FBA-F01, high — suggestion count mismatch.** The main NFL page advertises 12 suggestions, the core suggestions CSV contains three rows, and the current `docs/nfl/suggestions.html` table renders S01–S03. `research/NFL_SUGGESTIONS.md` describes twelve proposals. This is a repository-derived count, not an NFL fact. The core board and page need integration-owner reconciliation.
- **FBA-F02, medium — recommended IDs not rendered.** The existing suggestions page’s “Recommended path” refers to S06 and S08, but those IDs are absent from its displayed three-row table. The research note identifies both. A reviewer cannot review an unrendered recommendation in the advertised table.
- **FBA-F03, high — injury-policy source conflict in local registers.** Core Q02 links to the 2017 injury-report-policy PDF. Core F-NFL-03 says this URL returned 404 when checked on 2026-11-13 and instructs that timing rules are unverified. This review did not fetch either the PDF or the current policy endpoint; current status remains unverified here.
- **FBA-F04, medium — citations overstate support.** Some suggestions and Q10 cite broad official pages as source links for subjective site-design or prioritization proposals. The official source does not establish that a UI is beneficial, a particular proposal should be selected, or an impact score is correct. Distinguish official fact provenance from project recommendation rationale.
- **FBA-F05, unverified — full integration state.** This session did not rerun the global build, repo-wide cross-pack fixed-point generators, external link checker, GitHub Pages build/deploy, or a full current source-by-source audit. Prior coordination entries report checks, but are not a substitute for a new final integration run.

These findings are deliberately not fixed in `docs/nfl/` or shared registers because those are outside this session’s exclusive scope and are integration-owned shared outputs. They are published as requests on the new Flagged for Review page.

## Decision blockers and no-inference policy

- No licensed, documented market-data feed was established by this review. No market line, residual, ROI, CLV, correlation, model probability, pick, or reward qualification is added.
- Injury report rows do not alone establish roster eligibility, actual starting status, depth rank, inactives, or playing time. Keep each evidence state distinct.
- Prior source records and captures were read locally but not fetched again. New pages explicitly say so; no value is marked externally verified.
- Suggestions remain pending. This session selected no implementation path on the user’s behalf.

## Verification performed

Run `python scripts/check_nfl_fba1772f.py` to check the isolated site’s expected page set, title/main landmarks, local links, and an HTTPS source/context link on every table row. This is an offline HTML/link check; it does not confirm external URLs or source contents. Global checks remain for the final integration session.
