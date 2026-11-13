"""NFL decision-desk analytics: verified inputs, own-line origination, luck control.

Pure Python 3.11 standard library. No network access, no third-party packages.
Every public function is deterministic: the same registers in give the same
numbers out, which is what makes the published tables independently checkable.
"""
from .league import Club, load_clubs, league_facts  # noqa: F401
from .model import poisson_pmf, game_line, key_number_mass  # noqa: F401
from .luck import pythagorean_fit, luck_table, bootstrap_ci  # noqa: F401
from .correlation import pearson, spearman, correlated_pairs  # noqa: F401
from .depth import UNIT_OF, WEIGHTS, club_group_deficiency  # noqa: F401
from .gates import GATES, evaluate  # noqa: F401
from .leaderboard import STRATEGIES, rank  # noqa: F401
