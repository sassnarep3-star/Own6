"""Synthetic mathematical regressions only; no NBA observations or claimed edge.

Plain test functions also run via tools/run_tests.py without pytest installed.
"""
import math
import pathlib
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from own6 import parlay


def rejects(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError(f"{fn.__name__} accepted invalid/unsupported input")


def test_pearson_known_pairs_and_generators():
    assert math.isclose(parlay.pearson([1, 2, 3], [2, 4, 6]), 1)
    assert math.isclose(parlay.pearson([1, 2, 3], [6, 4, 2]), -1)
    assert abs(parlay.pearson([1, -1, 1, -1], [1, 1, -1, -1])) < 1e-15
    assert math.isclose(parlay.pearson(iter([1, 2, 3]), iter([2, 4, 6])), 1)


def test_pearson_rejects_bad_alignment_and_missing_values():
    for x, y in [([], []), ([1], [1]), ([1, 2], [1, 2, 3]),
                 ([1, 1], [1, 2]), ([0, 0], [1, 2]),
                 ([1, math.nan], [1, 2]), ([1, math.inf], [1, 2]),
                 ([True, 2], [1, 2]), (["1", 2], [1, 2]),
                 ([1, 1 + 1e-15], [1, 2]), (None, [1, 2])]:
        rejects(parlay.pearson, x, y)


def test_pearson_avoids_squaring_overflow():
    assert math.isclose(parlay.pearson([1e300, 2e300, 3e300], [3e300, 2e300, 1e300]), -1)
    assert math.isclose(parlay.pearson([1e-300, 2e-300, 3e-300], [1, 2, 3]), 1)


def test_invalid_matrix_shapes_and_entries_fail_closed():
    for matrix in [None, [], [[1]], [[1, 0]], [[1, 0], [0]],
                   [[1, 0.4], [0.2, 1]], [[2, 0], [0, 1]],
                   [[1, 1.1], [1.1, 1]], [[1, math.nan], [math.nan, 1]],
                   [[1, math.inf], [math.inf, 1]], [[True, 0], [0, 1]]]:
        rejects(parlay.joint_prob, [0.5, 0.5], matrix, sims=1)


def test_indefinite_singular_and_near_singular_matrices_are_not_clipped():
    # All pairwise entries are in range, but the 3D matrix is indefinite.
    rejects(parlay.joint_prob, [.5] * 3, [[1, .9, .9], [.9, 1, -.9], [.9, -.9, 1]], sims=1)
    for rho in [1, -1, 1 - 1e-14]:
        rejects(parlay.joint_prob, [.5, .5], [[1, rho], [rho, 1]], sims=1)
    # Even deterministic outcomes must not bypass matrix validation.
    rejects(parlay.joint_prob, [0, 1], [[1, 2], [2, 1]], sims=1)


def test_probability_validation_applies_to_both_pricers():
    for probabilities in [[], [math.nan], [math.inf], [-.01], [1.01], ["0.5"], [True], None]:
        rejects(parlay.independent_prob, probabilities)
        rejects(parlay.joint_prob, probabilities, [[1]], sims=1)
    assert parlay.independent_prob([.5, .6]) == .3
    assert parlay.independent_prob([0, 1]) == 0
    assert parlay.independent_prob([1, 1]) == 1


def test_simulation_controls_require_positive_integer_count_and_integer_seed():
    for sims in [0, -1, 1.5, True, None]:
        rejects(parlay.joint_prob, [.5], [[1]], sims=sims)
    for seed in [None, True, 1.5, "6"]:
        rejects(parlay.joint_prob, [.5], [[1]], seed=seed)


def test_deterministic_marginals_are_supported_and_wilson_is_not_false_certainty():
    zero = parlay.joint_prob_report([0, 1], [[1, 0], [0, 1]], sims=100)
    one = parlay.joint_prob_report([1, 1], [[1, 0], [0, 1]], sims=100)
    assert zero["probability"] == 0 and zero["mc_ci_high"] > 0
    assert one["probability"] == 1 and one["mc_ci_low"] < 1
    assert 0 <= zero["mc_ci_low"] <= zero["mc_ci_high"] <= 1
    assert "Monte Carlo" in zero["interval_scope"]
    assert "latent" in zero["correlation_scope"]


def test_seeded_joint_probability_matches_analytic_normal_orthant():
    # For centered bivariate normals, P(Z1<=0,Z2<=0)=1/4+asin(rho)/(2*pi).
    # Synthetic numerical test, not an observed NBA coefficient.
    for rho in [-.6, 0, .6]:
        report = parlay.joint_prob_report([.5, .5], [[1, rho], [rho, 1]], sims=20000, seed=23)
        expected = .25 + math.asin(rho) / (2 * math.pi)
        assert abs(report["probability"] - expected) < .012
        assert report["mc_ci_low"] <= report["probability"] <= report["mc_ci_high"]
        assert report["sims"] == 20000 and report["hits"] / 20000 == report["probability"]
    assert parlay.joint_prob([.6, .7], [[1, .2], [.2, 1]], sims=50) == parlay.joint_prob([.6, .7], [[1, .2], [.2, 1]], sims=50)


def test_inverse_normal_rejects_endpoints_and_roundtrips():
    for p in [0, 1, -.1, 1.1, math.nan, True]:
        rejects(parlay._norm_inv, p)
    for p in [.00001, .1, .5, .9, .99999]:
        assert math.isclose(parlay._norm_cdf(parlay._norm_inv(p)), p, abs_tol=1e-14)


def test_parlay_review_has_official_reference_on_every_row_and_working_links():
    class Review(HTMLParser):
        def __init__(self):
            super().__init__()
            self.rows, self.links, self.current = [], [], None
            self.data = False
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "tr":
                self.current, self.data = [], False
            if tag == "td":
                self.data = True
            if tag == "a" and attrs.get("href"):
                self.links.append(attrs["href"])
                if self.current is not None:
                    self.current.append(attrs["href"])
        def handle_endtag(self, tag):
            if tag == "tr":
                if self.data:
                    self.rows.append(self.current)
                self.current = None
    page = ROOT / "docs/parlay-safety/index.html"
    parser = Review()
    parser.feed(page.read_text())
    official = {"github.com", "www.nba.com", "docs.scipy.org", "numpy.org", "www.statsmodels.org", "www.itl.nist.gov"}
    assert len(parser.rows) >= 10
    for row in parser.rows:
        assert any(urlparse(u).scheme == "https" and urlparse(u).hostname in official for u in row)
    for link in parser.links:
        parsed = urlparse(link)
        if not parsed.scheme and parsed.path:
            assert (page.parent / parsed.path).resolve().is_file(), link
