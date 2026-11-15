"""Validation and aggregation for the consolidated decision-readiness table.

The readiness table maps every requirement in the brief to:
  * a current status,
  * the gate that blocks it (or ``none``),
  * the number / condition that would clear it,
  * the evidence artifact that implements or flags it,
  * an official source link.

Nothing here produces a measured model value. ``clearing_number`` holds a
threshold or a condition (e.g. "32/32 club depth charts", "a licensed price
archive"), never a computed ROI / CLV / edge figure.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from typing import Dict, List

ALLOWED_STATUS = {
    "implemented",
    "implemented_limited",
    "blocked",
    "needs_review",
    "not_started",
    "rejected_policy",
}

# Statuses for which a blocking gate is expected (a gate that blocks progress),
# versus statuses that are either done or explicitly rejected by policy.
STATUS_GROUPS = {
    "done": {"implemented"},
    "limited": {"implemented_limited"},
    "open": {"blocked", "needs_review", "not_started"},
    "rejected": {"rejected_policy"},
}

# A gate reference is either "none" (not blocked), a "none (policy rejection)"
# / "none structural" note, or a gate id that must exist in gates.csv.
NONE_GATE_MARKERS = ("none",)


@dataclass
class PackPaths:
    data_dir: str
    readiness: str = "readiness.csv"
    gates: str = "gates.csv"
    sources: str = "sources.csv"
    flagged: str = "flagged.csv"

    @classmethod
    def for_repo(cls, repo_root: str) -> "PackPaths":
        return cls(data_dir=os.path.join(repo_root, "data", "nfl_6ab24751"))

    def path(self, name: str) -> str:
        return os.path.join(self.data_dir, name)


@dataclass
class ReadinessPack:
    rows: List[Dict[str, str]] = field(default_factory=list)
    gates: List[Dict[str, str]] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)
    flags: List[Dict[str, str]] = field(default_factory=list)
    paths: PackPaths = field(default_factory=lambda: PackPaths(data_dir="."))

    # ---- lookups -------------------------------------------------------
    @property
    def gate_ids(self) -> set:
        return {g["gate_id"] for g in self.gates}

    @property
    def source_urls(self) -> set:
        return {s["url"] for s in self.sources}

    def status_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {s: 0 for s in ALLOWED_STATUS}
        for r in self.rows:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        return counts

    def group_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {g: 0 for g in STATUS_GROUPS}
        for r in self.rows:
            for group, members in STATUS_GROUPS.items():
                if r["status"] in members:
                    counts[group] += 1
        return counts


def _read_csv(path: str) -> List[Dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def load_pack(paths: PackPaths) -> ReadinessPack:
    pack = ReadinessPack(paths=paths)
    pack.rows = _read_csv(paths.path(paths.readiness))
    pack.gates = _read_csv(paths.path(paths.gates))
    pack.sources = _read_csv(paths.path(paths.sources))
    pack.flags = _read_csv(paths.path(paths.flagged))
    return pack


def validate(pack: ReadinessPack) -> List[str]:
    """Return a list of validation errors (empty means the pack is consistent)."""
    errors: List[str] = []
    gate_ids = pack.gate_ids

    req_ids = [r["req_id"] for r in pack.rows]
    if len(req_ids) != len(set(req_ids)):
        errors.append("readiness.csv: duplicate req_id values")

    required_readiness = {"req_id", "category", "requirement", "status",
                          "blocking_gate", "clearing_number",
                          "evidence_artifact", "official_source_url"}
    for r in pack.rows:
        rid = r.get("req_id", "?")
        for col in required_readiness:
            if col not in r or r[col] == "":
                # clearing_number may legitimately be blank for done/rejected rows
                if col == "clearing_number" and r.get("status") in (
                    "implemented", "rejected_policy"
                ):
                    continue
                # evidence_artifact may be blank when nothing is built yet or the
                # requirement is rejected by policy (there is no artifact to point at)
                if col == "evidence_artifact" and r.get("status") in (
                    "not_started", "rejected_policy"
                ):
                    continue
                errors.append(f"readiness.csv {rid}: missing {col}")
        status = r.get("status", "")
        if status not in ALLOWED_STATUS:
            errors.append(f"readiness.csv {rid}: unknown status {status!r}")
        src = r.get("official_source_url", "")
        if not src.startswith("https://"):
            errors.append(f"readiness.csv {rid}: source is not https: {src!r}")

        gate = r.get("blocking_gate", "")
        if gate and not any(gate.startswith(m) for m in NONE_GATE_MARKERS):
            # allow a gate reference that contains a gate id from gates.csv
            if not any(g in gate for g in gate_ids):
                errors.append(
                    f"readiness.csv {rid}: blocking_gate {gate!r} does not "
                    "reference a gate in gates.csv"
                )

        # A clearing number is required for any open or limited requirement.
        if status in ("not_started", "needs_review", "implemented_limited", "blocked"):
            if not r.get("clearing_number", "").strip():
                errors.append(f"readiness.csv {rid}: open/limited row has no clearing_number")

    # gates.csv integrity
    gate_ids_seen = [g["gate_id"] for g in pack.gates]
    if len(gate_ids_seen) != len(set(gate_ids_seen)):
        errors.append("gates.csv: duplicate gate_id values")
    for g in pack.gates:
        if not g.get("official_or_method_source", "").startswith("https://"):
            errors.append(f"gates.csv {g.get('gate_id','?')}: source is not https")
        if not g.get("threshold_or_clearing_number", "").strip():
            errors.append(f"gates.csv {g.get('gate_id','?')}: missing threshold/clearing number")

    # sources.csv integrity
    src_urls = [s["url"] for s in pack.sources]
    if len(src_urls) != len(set(src_urls)):
        errors.append("sources.csv: duplicate url values")
    for s in pack.sources:
        if not s.get("url", "").startswith("https://"):
            errors.append(f"sources.csv {s.get('source_id','?')}: url is not https")

    # flagged.csv integrity
    flag_ids = [f["flag_id"] for f in pack.flags]
    if len(flag_ids) != len(set(flag_ids)):
        errors.append("flagged.csv: duplicate flag_id values")
    for f in pack.flags:
        if not f.get("official_source_url", "").startswith("https://"):
            errors.append(f"flagged.csv {f.get('flag_id','?')}: source is not https")

    return errors
