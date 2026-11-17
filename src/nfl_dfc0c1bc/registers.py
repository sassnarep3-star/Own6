"""Discovery and loading of every suggestion / question / register file in ``data/``.

The registers were written by different sessions with different column vocabularies, so this module
carries one alias map per canonical field and nothing else: no value is invented here, missing
fields come back as the empty string, and the caller must show which file and row each value came
from.
"""
from __future__ import annotations

import csv
import hashlib
import os
from typing import Dict, Iterable, List, Tuple

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(REPO, "data")

#: canonical field -> the names packs actually used, tried in order
ALIASES: Dict[str, Tuple[str, ...]] = {
    "id": ("suggestion_id", "question_id", "sug_id", "s_id", "q_id", "qid", "qa_id", "id"),
    "area": ("area", "category", "topic", "decision_domain", "kind"),
    "title": ("title",),
    "statement": (
        "suggestion", "question", "critical_question", "what_would_change", "decision_blocked",
    ),
    "problem": (
        "problem_it_solves", "why_it_improves_decisions", "decision_problem_solved",
        "what_it_changes", "why_now", "what_an_answer_unlocks", "why_it_matters",
        "current_repo_state", "reasoning",
    ),
    "options": (
        "options", "options_for_review", "option_paths_for_review", "option_a", "option_b",
        "option_c", "paths",
    ),
    "recommended": ("recommended_path", "recommended", "recommendation", "answer",
                    "current_answer_and_gate_impact", "known_answer", "answer_we_have"),
    "evidence_needed": ("evidence_needed", "what_we_have", "information_we_have_verified",
                        "have_it", "how_to_discover_it_without_a_human", "discovery_path",
                        "discovery_protocol", "discovery_suggestion_path", "discovery_suggestion",
                        "how_to_answer", "how_to_close", "what_is_missing", "what_we_lack",
                        "information_we_do_not_have", "why_we_cannot_answer_it_ourselves"),
    "effort": ("effort", "effort_and_reversibility", "cost_or_effort", "cost",
               "cost_of_doing_nothing", "cost_or_risk"),
    "risk": ("risk_if_ignored", "risk_if_not_done", "risk_if_adopted", "risk_if_applied",
             "risk_if_not_applied", "risk", "what_it_unblocks", "blocks_which_decision",
             "blocking_decision", "blocking_severity", "why"),
    "priority": ("priority", "impact", "decision_impact"),
    "status": ("status", "review_status", "answer_status", "verification_status", "state",
               "discovery_status", "implemented", "applied_by_default"),
    "owner": ("decision_owner", "suggestion_owner", "owner_to_decide", "owner_decides",
              "decision_owner_needs", "review_status"),
    "source_url": ("official_source_url", "source_url", "evidence_url", "methodology_reference_url",
                   "method_reference_url", "verification_url", "url"),
    "read_on": ("read_on_utc", "as_of", "read_on", "raised_on", "captured_at_utc",
                "verification_date"),
    "requirements": ("touches_requirements", "blocks_which_brief_items", "affects", "flag_id",
                     "related_suggestion_id", "affected_tables"),
    "source_label": ("official_source_label", "source_label"),
}


def read_table(path: str) -> List[Dict[str, str]]:
    """Read a CSV or PSV file into a list of dicts (BOM-tolerant, \r\n tolerant)."""
    delim = "|" if path.endswith(".psv") else ","
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows: List[Dict[str, str]] = []
        for raw in csv.DictReader(fh, delimiter=delim):
            rows.append({(k or "").strip(): (v or "").strip() for k, v in raw.items()})
        return rows


def field(row: Dict[str, str], canonical: str) -> str:
    for name in ALIASES.get(canonical, (canonical,)):
        val = row.get(name, "")
        if val:
            return val
    return ""


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def is_suggestions_file(name: str) -> bool:
    stem = os.path.basename(name)
    return stem.startswith("suggestions.") or stem.startswith("site_suggestions.")


def is_questions_file(name: str) -> bool:
    stem = os.path.basename(name)
    return (stem.startswith("questions.") or stem.startswith("open_questions.")
            or stem.startswith("decision_questions.") or stem.startswith("decision_qa"))


def iter_registers(subdirs: Iterable[str] = ()) -> List[Dict[str, str]]:
    """Every suggestions/questions register under ``data/``, sorted by path.

    Returns inventory rows: kind, pack, path, rows, columns, sha256.
    """
    out: List[Dict[str, str]] = []
    packs = sorted(d for d in os.listdir(DATA) if os.path.isdir(os.path.join(DATA, d)))
    if subdirs:
        wanted = set(subdirs)
        packs = [p for p in packs if p in wanted]
    for pack in packs:
        pdir = os.path.join(DATA, pack)
        for fname in sorted(os.listdir(pdir)):
            if not fname.endswith((".csv", ".psv")):
                continue
            if not (is_suggestions_file(fname) or is_questions_file(fname)):
                continue
            path = os.path.join(pdir, fname)
            rows = read_table(path)
            cols = list(rows[0].keys()) if rows else []
            kind = "suggestions" if is_suggestions_file(fname) else "questions"
            out.append({
                "kind": kind,
                "pack": pack,
                "path": os.path.relpath(path, REPO).replace(os.sep, "/"),
                "rows": str(len(rows)),
                "columns": ";".join(cols),
                "sha256": sha256(path),
            })
    return out


def load_rows(inventory: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Flatten every register into canonical rows, keeping the provenance of each value."""
    out: List[Dict[str, str]] = []
    for entry in inventory:
        path = os.path.join(REPO, entry["path"])
        for n, raw in enumerate(read_table(path), 1):
            rid = field(raw, "id") or f"row{n:03d}"
            rec = {
                "kind": entry["kind"],
                "pack": entry["pack"],
                "file": entry["path"],
                "local_id": rid,
                "id": f"{entry['pack'].replace('nfl_', '')}-{entry['kind'][:4]}-{rid}",
            }
            for canon in ALIASES:
                rec[canon] = field(raw, canon)
            rec["_raw_keys"] = ";".join(sorted(k for k, v in raw.items() if v))
            out.append(rec)
    return out


def any_register_field(row: Dict[str, str], names: Iterable[str]) -> str:
    for name in names:
        val = row.get(name, "")
        if val:
            return val
    return ""
