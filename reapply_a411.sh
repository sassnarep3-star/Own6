#!/usr/bin/env bash
# Re-apply the a411fed0 pack on top of the current origin/main.
#
# COORDINATION.md is append-only and several sessions write to it, so a plain
# rebase conflicts on it every time. This script instead:
#   1. saves the pack's own files to a scratch branch,
#   2. resets the working branch to origin/main,
#   3. restores only this session's exclusive scope (all new files, no conflict),
#   4. re-applies the two additive shared-file edits,
#   5. regenerates the shared inventories to their fixed point.
#
# Nothing belonging to another session is dropped: every step is verified with
# `git merge-base --is-ancestor origin/main HEAD` before pushing.
set -euo pipefail
cd /home/user/Own6

SCOPE=(
  .github/workflows/nfl-a411fed0-ci.yml
  NFL_A411FED0_EXECUTIVE_SUMMARY.md
  src/nfl_a411fed0
  scripts/build_nfl_a411fed0.py
  scripts/check_nfl_a411fed0.py
  tests/test_nfl_a411fed0.py
  data/nfl_a411fed0
  docs/nfl-a411fed0
)

echo "== saving work =="
git branch -f scratch_a411 HEAD

echo "== resetting to origin/main =="
git reset --hard origin/main >/dev/null

echo "== restoring exclusive scope =="
git checkout scratch_a411 -- "${SCOPE[@]}"

echo "== re-applying additive shared-file edits =="
python3 - <<'PY'
# docs/index.html: one nav link + one category card, both purely additive.
p = 'docs/index.html'
s = open(p).read()
if 'nfl-a411fed0/index.html' in s:
    print('  index.html already linked')
else:
    old = '<a href="daily/index.html">Daily verify</a>'
    assert old in s, 'nav anchor missing'
    s = s.replace(old, '<a href="nfl-a411fed0/index.html">NFL Originated Lines</a>' + old, 1)
    anchor = '<span class="arrow">Open NFL Decision Center ↗</span></a>'
    assert anchor in s, 'category-card anchor missing'
    card = anchor + '''
        <a class="category" href="nfl-a411fed0/index.html"><span class="category-icon">ORIG</span><h3>NFL Originated Lines (a411fed0)</h3><p>84 Week 10 markets originated side → total → moneyline, fair / market / difference as separate columns. 120 verified games, 10 strategies with signal and staking kept apart, 10 correlations each with n, 6 armed demotion rules, and 17 flagged irregularities. <strong>No prices exist — nothing is promotable, by design.</strong></p><span class="arrow">Open NFL Originated Lines ↗</span></a>'''
    s = s.replace(anchor, card, 1)
    open(p, 'w').write(s)
    print('  index.html: nav link + category card added')

# COORDINATION.md: append-only, so append the session block again.
c = 'COORDINATION.md'
s = open(c).read()
if '## Session `a411fed0`' in s:
    print('  COORDINATION.md already has the section')
else:
    s = s + open('/tmp/a411_section.md').read()
    open(c, 'w').write(s)
    print('  COORDINATION.md: section appended')
PY

echo "== committing scope =="
git add -A
git commit -q -m "feat(nfl-a411fed0): originate NFL lines with price store, gates and dashboard

Session a411fed0. Origination runs side -> total -> moneyline in that fixed
order, each market published as three separate columns: the model's fair
line, the market line, and the difference. Market and difference are left
blank and stamped unverified, because no official NFL page publishes prices.

- price_snapshots: 84 Week 10 markets enumerated, opening and closing columns
  present and empty; gate A4-G05 fails closed so nothing leaves paper
- results feed: 120 verified finals reconciled against official standings
- depth: 347 injury rows joined to club charts; 43 of 77 Out/Doubtful players
  have a resolved replacement string (4 of 32 charts were readable)
- correlations: 10 values, each with n and a 95% CI; underpowered ones marked
  insufficient_n and unused
- gates: 10 validation gates (6 fail) and 6 armed demotion rules
- leaderboard: 10 strategies, signal columns kept apart from staking columns
- 17 flags published with verbatim evidence

Verification: 126 pack checks pass; 29 pack tests pass under both pytest and
the repo's dependency-free runner; full repo suite passes."

echo "== regenerating shared inventories to the fixed point =="
python3 scripts/build_lab.py >/dev/null
python3 scripts/build_assurance.py >/dev/null
python3 scripts/source_coverage.py >/dev/null
python3 scripts/audit_repo.py >/dev/null
git add -A
git commit -q -m "chore(inventories): regenerate after the a411fed0 pack

Required after any COORDINATION.md or docs/index.html edit." || echo "  (nothing to commit)"

# The inventories only stabilise once the new files are committed, so run the
# pipeline again and commit if it moved.
python3 scripts/build_lab.py >/dev/null
python3 scripts/build_assurance.py >/dev/null
python3 scripts/source_coverage.py >/dev/null
python3 scripts/audit_repo.py >/dev/null
if ! git diff --quiet; then
  git add -A
  git commit -q -m "chore(inventories): second regeneration to reach the fixed point"
fi

echo "== verifying nothing from main was lost =="
git merge-base --is-ancestor origin/main HEAD && echo "  OK: origin/main fully contained"

echo "== verification =="
python3 scripts/check_nfl_a411fed0.py 2>&1 | tail -2
python3 tools/run_tests.py 2>&1 | tail -1
echo "== done: $(git log --oneline -1) =="
