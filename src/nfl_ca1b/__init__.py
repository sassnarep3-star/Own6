"""nfl_ca1b — convergence & verification pack (session ca1b3769).

Every value published by this package is read from an official NFL source during
this session, or is arithmetic on such a value with the derivation shown. Anything
else is left blank and listed in flagged.csv. No market/book prices exist in any
official NFL page, so price-dependent columns are blank by policy.
"""
__all__ = [
    "capture", "verify", "ratings", "availability", "requirements",
    "qia", "suggestions", "freshness",
]
