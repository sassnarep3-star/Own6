# CI findings for PR #140

Pack-local checker passes, and the isolated pack tests pass in a local venv (2 passed). Pull-request checks failed because the repository-wide lab workflow runs the full existing suite: 820 passed, 2 failed, 6 subtests passed. The failures observed locally were:

1. `tests/assurance/test_audit.py::test_inventory_hashes_and_line_counts` — the assurance inventory's COORDINATION.md hash/line-count snapshot is stale after the required claim and close-out entries were appended.
2. `tests/test_nfl_dfc0c1bc.py::test_verifier_passes` — the existing dfc0c1bc checker found master-register row-count mismatch (490 vs 504) and nondeterministic generated outputs (19 findings). The check itself rewrote its generated files during test execution; those generated modifications were restored to the branch HEAD after diagnosis.

Neither failure is in the new pack; no attempt has been made to edit dfc0c1bc or the assurance inventory outside this task's claimed scope. Since the user's instruction forbids merging a broken site, PR #140 is intentionally left unmerged pending repair of the shared assurance snapshot and dfc0c1bc fixed-point inconsistency. See GitHub Actions runs linked from PR #140 for CI results.
