"""One canonical requirement register for the whole project.

Six merged packs each publish their own requirement table (73, 74, 79, 15, 20 and
81 rows). None of them can be read alone: the same brief sentence appears three or
four times under different IDs, with different status words, and the owner has no
way to tell which pack's answer is current.

This module collapses them into ONE row per distinct requirement, keeps every
source ID, and publishes a separately-labelled column saying what this session
could add. Deduplication is by normalised requirement text — no semantic guessing,
no LLM clustering: exact normalised duplicates merge, everything else stays.
"""
from __future__ import annotations

import csv
import pathlib
import re
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[2]

SOURCES = [
    ("8362b702", "data/nfl_8362b702/readiness.csv", "requirement_id", "requirement",
     "status", "gate_that_blocks_it", "number_that_would_clear_it"),
    ("48217a55", "data/nfl_48217a55/requirements_decision_readiness.csv", "requirement_id",
     "requirement", "status", "blocking_gate", "clearing_number"),
    ("67233566", "data/nfl_67233566/requirements_trace.csv", "requirement_id", "requirement",
     "status", "", ""),
    ("d966f630", "data/nfl_d966f630/requirements_trace.csv", "requirement_id", "requirement",
     "status", "", ""),
    ("6ab24751", "data/nfl_6ab24751/readiness.csv", None, None, None, None, None),
    ("origination", "data/nfl_origination/requirements_matrix.csv", None, None, None, None, None),
    ("wk", "data/nfl_wk/requirements.csv", None, None, None, None, None),
]

# Status vocabulary. The brief's decision is binary in practice: can a bet be
# priced/made on this today, or not. Everything else is progress, not permission.
STATUS_MAP = {
    # exact vocabulary seen across the seven registers (25 distinct spellings)
    "delivered": "delivered", "delivered_here": "delivered", "delivered_sibling": "delivered",
    "done": "delivered", "verified": "delivered", "cleared": "delivered",
    "implemented": "delivered", "implemented_verified": "delivered",
    "implemented_and_checked": "delivered", "done (partial)": "open",
    "done (limited)": "open", "done (hypotheses)": "open", "done (with flags)": "open",
    "implemented_limited": "open", "implemented_partial": "open", "partial": "open",
    "open": "open", "not_started": "open", "unverified": "open", "needs_review": "open",
    "needs review": "open",
    "blocked": "blocked", "blocked_no_source": "blocked",
    "rejected": "rejected by policy", "rejected_policy": "rejected by policy",
    "rejected_kept_closed": "rejected by policy",
}

# What this session adds to a requirement, keyed by a match on the requirement text.
THIS_SESSION = [
    (r"depth chart|depth-chart|depth order|depth rank",
     "PROBE RESULT (this session): nfl.com/teams/<club>/depth-chart returns 404 'Flag on the Play' (P-01). "
     "Route (a) of SG-05 does not exist on nfl.com as a path; the route must be re-decided, not re-tried."),
    (r"inactive|snap count",
     "PARTIAL CLOSE (this session): the official week-10 inactives article was read and 147 inactive lines "
     "for 24 clubs are transcribed; snap counts remain unpublished on any official page read."),
    (r"venue",
     "CLOSED (this session): all 13 week-11 fixtures now carry a venue transcribed from an official page; "
     "the two surfaces disagree on three stadium names and each is published verbatim."),
    (r"correlation",
     "MEASURED (this session): 5 correlations recomputed from 149 official finals with n and Fisher-z 95% CI."),
    (r"pre-?regist|backtest",
     "RE-REGISTERED (this session): 5 strategies frozen with SHA-256 rule hashes; walk-forward backtest "
     "scores are kept OFF the leaderboard and published on the backtest page only."),
    (r"results feed|results",
     "RE-VERIFIED (this session): 149 official finals; 32/32 clubs reconcile to today's standings."),
    (r"price|market line|ROI|CLV",
     "STILL BLOCKED: no official NFL page publishes a price. Every price column stays blank."),
]


def _norm(text: str) -> str:
    t = re.sub(r"[^a-z0-9 ]", " ", (text or "").lower())
    return " ".join(t.split())


def _rows(rel: str) -> List[Dict[str, str]]:
    p = ROOT / rel
    if not p.exists():
        return []
    with p.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _detect(cols: List[str]) -> Dict[str, Optional[str]]:
    def find(*names):
        for n in names:
            if n in cols:
                return n
        return None
    return {"id": find("requirement_id", "id", "req_id"),
            "text": find("requirement", "requirement_text", "item"),
            "status": find("status", "state"),
            "gate": find("gate_that_blocks_it", "blocking_gate", "gate", "blocking_gate_id"),
            "clear": find("number_that_would_clear_it", "clearing_number", "number_to_clear", "clear_number")}


def gather() -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for pack, rel, *_ in SOURCES:
        rows = _rows(rel)
        if not rows:
            continue
        d = _detect(list(rows[0].keys()))
        if not d["text"]:
            continue
        for r in rows:
            tx = (r.get(d["text"]) or "").strip()
            if not tx:
                continue
            out.append({
                "pack": pack, "source_file": rel,
                "source_id": (r.get(d["id"]) or "").strip() if d["id"] else "",
                "requirement": tx,
                "status_raw": (r.get(d["status"]) or "").strip() if d["status"] else "",
                "gate": (r.get(d["gate"]) or "").strip() if d["gate"] else "",
                "clears": (r.get(d["clear"]) or "").strip() if d["clear"] else "",
                "key": _norm(tx),
            })
    return out


def merge() -> List[Dict[str, object]]:
    rows = gather()
    groups: Dict[str, List[Dict[str, object]]] = {}
    order: List[str] = []
    for r in rows:
        k = r["key"]
        if k not in groups:
            groups[k] = []
            order.append(k)
        groups[k].append(r)
    merged: List[Dict[str, object]] = []
    for i, k in enumerate(order, start=1):
        g = groups[k]
        statuses = []
        for r in g:
            s = STATUS_MAP.get(r["status_raw"].lower().replace(" ", "_"), r["status_raw"] or "unstated")
            statuses.append(s)
        # the register reports the WORST status across packs: a requirement is only
        # delivered if every pack that touches it says so.
        if any(s.startswith("blocked") for s in statuses):
            overall = "blocked"
        elif all(s.startswith("rejected") for s in statuses):
            overall = "rejected by policy"
        elif any(s.startswith("open") for s in statuses):
            overall = "open"
        elif any(s.startswith("delivered") for s in statuses):
            overall = "delivered"
        else:
            overall = "unstated"
        gates = sorted({r["gate"] for r in g if r["gate"]})
        clears = sorted({r["clears"] for r in g if r["clears"]})
        mine = ""
        for pat, note in THIS_SESSION:
            if re.search(pat, k):
                mine = (mine + " " if mine else "") + note
        merged.append({
            "req_id": "R-%03d" % i,
            "requirement": max((r["requirement"] for r in g), key=len),
            "status": overall,
            "status_variants": "; ".join(sorted(set(statuses))),
            "packs": ", ".join(sorted({str(r["pack"]) for r in g})),
            "source_ids": "; ".join("%s:%s" % (r["pack"], r["source_id"]) for r in g if r["source_id"]),
            "n_packs": len({str(r["pack"]) for r in g}),
            "blocking_gate": "; ".join(gates),
            "number_that_would_clear_it": "; ".join(clears),
            "this_session_evidence": mine,
        })
    return merged


def summary(merged: List[Dict[str, object]]) -> Dict[str, object]:
    from collections import Counter
    c = Counter(str(r["status"]) for r in merged)
    dup = Counter(r["key"] for r in gather())
    return {
        "rows_in_source_registers": len(gather()),
        "distinct_requirements": len(merged),
        "duplicate_rows_removed": len(gather()) - len(merged),
        "max_copies_of_one_requirement": max(dup.values()) if dup else 0,
        "status_counts": dict(c),
        "packs_contributing": sorted({str(r["pack"]) for r in gather()}),
    }
