"""Correlation engine (session 67233566).

Hard rule from the owner's list: *compute correlations only from officially sourced numbers and
publish n with each value.* Two consequences are implemented as code, not as prose:

1. every input series passed to ``measure`` must carry a source URL; ``measure`` raises if either
   axis is unsourced, and it raises if the two series differ in length or contain a gap;
2. a pair that cannot be measured is published in ``EXCLUSIONS`` with the reason, so the absence of
   a number is a result rather than a silence. This is what stops a reader from treating an
   unmeasured dependence as an independent one.

The correlation of a two-leg combination is the *only* thing that licenses pricing that combination
multiplicatively, so ``joint`` returns the measured joint probability next to the product of
marginals: a combo may be ranked when the two differ by less than the sampling error, and must not
be ranked when they do not.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

BOOT_REPS = 4000
SEED = 20261115  # frozen: a different seed is a different pre-registration


def pearson(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or not x:
        raise ValueError("series must be the same non-zero length")
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx <= 0 or syy <= 0:
        raise ValueError("degenerate axis: constant series cannot carry a correlation")
    return sxy / math.sqrt(sxx * syy)


def _boot_ci(x: list[float], y: list[float], reps: int = BOOT_REPS) -> tuple[float, float]:
    rng = random.Random(SEED)
    n = len(x)
    out: list[float] = []
    for _ in range(reps):
        idx = [rng.randrange(n) for _ in range(n)]
        xs = [x[i] for i in idx]
        ys = [y[i] for i in idx]
        try:
            out.append(pearson(xs, ys))
        except ValueError:
            continue
    out.sort()
    if not out:
        return (float("nan"), float("nan"))
    return out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]


def _perm_p(x: list[float], y: list[float], observed: float, reps: int = 2000) -> float:
    """Permutation p-value: shuffle one axis, keep |r| >= |observed| as the tail."""
    rng = random.Random(SEED + 1)
    yy = y[:]
    hits = 0
    for _ in range(reps):
        rng.shuffle(yy)
        try:
            r = pearson(x, yy)
        except ValueError:
            continue
        if abs(r) >= abs(observed) - 1e-15:
            hits += 1
    return (hits + 1) / (reps + 1)


@dataclass
class Correlation:
    pair_id: str
    label: str
    unit: str
    axis_x: str
    axis_y: str
    value: float
    n: int
    ci_low: float
    ci_high: float
    p_value: float
    r_squared: float
    source_x: str
    source_y: str
    method: str
    interpretation: str

    def as_row(self) -> dict[str, str]:
        return {
            "pair_id": self.pair_id,
            "label": self.label,
            "sample_unit": self.unit,
            "axis_x": self.axis_x,
            "axis_y": self.axis_y,
            "pearson_r": f"{self.value:.4f}",
            "n": str(self.n),
            "ci95_low": f"{self.ci_low:.4f}",
            "ci95_high": f"{self.ci_high:.4f}",
            "perm_p": f"{self.p_value:.4f}",
            "r_squared": f"{self.r_squared:.4f}",
            "shared_variance_pct": f"{100 * self.r_squared:.1f}",
            "source_url_x": self.source_x,
            "source_url_y": self.source_y,
            "method": self.method,
            "interpretation": self.interpretation,
        }


def measure(pair_id: str, label: str, unit: str, axis_x: str, axis_y: str,
            x: list[float], y: list[float], source_x: str, source_y: str,
            interpretation: str = "") -> Correlation:
    if not source_x.startswith("https://") or not source_y.startswith("https://"):
        raise ValueError(f"{pair_id}: both axes must carry an https official source url")
    if len(x) != len(y):
        raise ValueError(f"{pair_id}: axis lengths differ ({len(x)} vs {len(y)})")
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in x + y):
        raise ValueError(f"{pair_id}: a gap in either axis is an exclusion, not a zero")
    r = pearson(x, y)
    lo, hi = _boot_ci(x, y)
    p = _perm_p(x, y, r)
    return Correlation(
        pair_id=pair_id, label=label, unit=unit, axis_x=axis_x, axis_y=axis_y,
        value=r, n=len(x), ci_low=lo, ci_high=hi, p_value=p, r_squared=r * r,
        source_x=source_x, source_y=source_y,
        method=f"Pearson r, percentile bootstrap CI ({BOOT_REPS} resamples, seed {SEED}), "
               f"two-sided permutation p (2000 shuffles)",
        interpretation=interpretation,
    )


def joint(a: list[int], b: list[int]) -> dict[str, float]:
    """Measured joint vs the product of marginals - the combo gate's evidence."""
    n = len(a)
    pa = sum(a) / n
    pb = sum(b) / n
    pab = sum(1 for x, y in zip(a, b) if x == 1 and y == 1) / n
    product = pa * pb
    # standard error of the difference of a proportion from its own product, by cluster bootstrap
    rng = random.Random(SEED + 7)
    diffs: list[float] = []
    for _ in range(2000):
        idx = [rng.randrange(n) for _ in range(n)]
        aa = [a[i] for i in idx]
        bb = [b[i] for i in idx]
        pa_ = sum(aa) / n
        pb_ = sum(bb) / n
        pab_ = sum(1 for x, y in zip(aa, bb) if x == 1 and y == 1) / n
        diffs.append(pab_ - pa_ * pb_)
    diffs.sort()
    return {
        "n": float(n),
        "p_a": pa,
        "p_b": pb,
        "p_joint_measured": pab,
        "p_joint_if_independent": product,
        "ratio_measured_to_independent": pab / product if product else float("nan"),
        "diff_ci95_low": diffs[int(0.025 * len(diffs))],
        "diff_ci95_high": diffs[int(0.975 * len(diffs)) - 1],
    }


EXCLUSIONS: list[dict[str, str]] = [
    {
        "pair_id": "EX-01",
        "label": "Any correlation involving a sportsbook price or closing line",
        "reason": "No official NFL page reachable from this repository prints a price, so neither "
                  "axis exists. A correlation with a line cannot be computed and its absence is "
                  "published rather than assumed to be zero.",
        "what_would_clear_it": "A licensed price source whose terms permit storage, plus >= 100 "
                               "graded fixtures with both a snapshot and an official result.",
    },
    {
        "pair_id": "EX-02",
        "label": "Player-prop to player-prop correlation (prop combos)",
        "reason": "No official NFL page publishes prop lines or prop outcomes as a joinable "
                  "dataset; the league's own partners agreement places injury- and "
                  "officiating-linked wagers inside its objectionable category.",
        "what_would_clear_it": "An officially sourced prop register with, for each pair, the joint "
                               "outcome of both legs on the same fixture (>= 200 fixtures).",
    },
    {
        "pair_id": "EX-03",
        "label": "Injury designation to line movement",
        "reason": "Requires a designation time series and a price time series for the same fixture. "
                  "Only one designation capture existed before this session and no price series "
                  "exists at all.",
        "what_would_clear_it": "Two or more dated captures per week of the official report plus the "
                               "price policy cleared; then n = fixtures x events, published per week.",
    },
    {
        "pair_id": "EX-04",
        "label": "Snap-count based depth to points allowed",
        "reason": "No official snap-count source is reachable, so depth has no measured playing-time "
                  "axis to correlate.",
        "what_would_clear_it": "An official snap-count or inactives source covering all 32 clubs.",
    },
]
