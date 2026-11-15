"""Consolidated NFL requirements decision-readiness pack (session 6ab24751).

This package loads the requirements decision-readiness dataset and its gate /
source / flag registers, validates them, and exposes the aggregates used by the
site builder and the line-by-line checker. It is pure standard library and
deterministic: it reads the committed CSVs and produces no measured model values.
"""

from .readiness import (
    PackPaths,
    ReadinessPack,
    ALLOWED_STATUS,
    STATUS_GROUPS,
    load_pack,
)

__all__ = [
    "PackPaths",
    "ReadinessPack",
    "ALLOWED_STATUS",
    "STATUS_GROUPS",
    "load_pack",
]
