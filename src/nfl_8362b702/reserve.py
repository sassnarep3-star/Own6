"""Reserve-list register: 'not listed' never means 'available'.

The register stores every non-active roster row read from the official club
roster page, with the page's own status code verbatim (no legend is published
by the page, so none is invented here). The Malik Willis case is the reason
this table exists.
"""
from __future__ import annotations

from .capture import (GB_NON_ACT_ROWS, GB_ROSTER_READ, GB_ROSTER_URL,
                      GB_ROSTER_STATUS_NOTE, GB_WILLIS_FINDING,
                      GB_NAME_SLUG_MISMATCH)

RESERVE_CODES = ("PUP", "RES", "RSR")  # the page's non-active, non-cut codes


def register_rows():
    out = []
    for name, slug, jersey, pos, code in GB_NON_ACT_ROWS:
        out.append({"club": "GB", "player_display_name": name,
                    "player_url_slug": slug, "jersey_on_page": jersey,
                    "position_on_page": pos, "status_code_on_page": code,
                    "reserve_section": "yes" if code in RESERVE_CODES else "no",
                    "read_at_utc": GB_ROSTER_READ,
                    "source_url": GB_ROSTER_URL,
                    "legend_on_page": "none — codes published verbatim"})
    return out


def absence_rows():
    """Absences are first-class rows. Willis is not on the page at all."""
    f = GB_WILLIS_FINDING
    return [{
        "player": f["player"], "club": "GB",
        "state_on_page": f["state_on_page"],
        "other_qbs_on_page": f["qbs_listed"],
        "interpretation": "unknown — neither available nor unavailable is supported by "
                          "this read; the brief's 'not listed never means available' rule applies",
        "read_at_utc": GB_ROSTER_READ,
        "source_url": GB_ROSTER_URL,
    }]


def mismatch_rows():
    m = GB_NAME_SLUG_MISMATCH
    return [{
        "club": "GB", "display_name_on_page": m["display_name"],
        "url_slug_on_page": m["url_slug"], "row_on_page": m["row"],
        "issue": "display name and player-URL slug on the same row name different people; "
                 "kept verbatim, not reconciled",
        "read_at_utc": GB_ROSTER_READ,
        "source_url": GB_ROSTER_URL,
    }]


def sweep_summary(sweep):
    done = sum(1 for r in sweep if r["sweep_complete"] == "yes")
    return {"clubs_swept": done, "clubs_total": 32,
            "gate": "G-SWEEP (32/32 hub + roster reads) blocks every team-level model",
            "note": GB_ROSTER_STATUS_NOTE}
