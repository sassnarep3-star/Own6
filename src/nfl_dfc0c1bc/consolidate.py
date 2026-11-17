"""Fold 16 suggestion registers and 10 question registers onto one schema, then rank the decisions.

The scoring is deliberately simple and printed on the page with its inputs, so a reviewer can
reproduce or attack it:

    source_rows  = register rows classified into the theme
    packs        = distinct packs raising at least one of those rows
    evidence     = this session's dated observations + answers touching the theme
    effort_score = 1 low, 2 medium/unspecified, 3 high  (mode over the rows' effort text)
    value        = 2*packs + source_rows + 2*evidence
    ratio        = value / effort_score
    sequence     = ratio desc, then packs desc, then theme id asc

No term reads a result, so the ranking cannot be a backtest in disguise.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Tuple

from . import themes as TH

CANON_TEXT = ("area", "title", "statement", "problem", "options", "recommended",
              "evidence_needed", "effort", "risk", "priority", "status", "owner",
              "requirements", "source_url", "read_on")


def _short(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _effort_score(values: List[str]) -> int:
    buckets = []
    for v in values:
        t = (v or "").lower()
        if re.search(r"\blow\b|cheap|mechanical|one[- ]line", t):
            buckets.append(1)
        elif re.search(r"\bhigh\b|heavy|weeks|procurement|licen", t):
            buckets.append(3)
        elif re.search(r"\bmed|medium\b", t):
            buckets.append(2)
    if not buckets:
        return 2
    return Counter(buckets).most_common(1)[0][0]


def assign_themes(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    for r in rows:
        hay = " ".join(r.get(k, "") for k in
                      ("statement", "title", "area", "problem", "options", "recommended", "requirements"))
        r["theme_id"] = TH.classify(r["pack"], r["kind"], r["local_id"], hay)
    return rows


def group_by_theme(rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    out: Dict[str, List[Dict[str, str]]] = {t: [] for t in TH.THEME_IDS}
    out["T00"] = []
    for r in rows:
        out.setdefault(r["theme_id"], []).append(r)
    return out


def _raised_by(rows: List[Dict[str, str]]) -> str:
    seen: List[str] = []
    for r in sorted(rows, key=lambda x: (x["pack"], x["local_id"])):
        seen.append(f"{r['pack'].replace('nfl_', '')}:{r['local_id'] or '?'}")
    return "; ".join(seen)


def _options(rows: List[Dict[str, str]]) -> str:
    """Verbatim option/recommendation text from the source rows, capped and de-duplicated."""
    vals: List[str] = []
    for r in rows:
        for key in ("options", "recommended"):
            v = _short(r.get(key, ""), 180)
            if v and v not in vals:
                vals.append(v)
    return " || ".join(vals[:6])


def _efforts(rows: List[Dict[str, str]], key: str) -> List[str]:
    return [r.get(key, "") for r in rows if r.get(key, "")]


def suggestions_master(sug_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    out = []
    for i, r in enumerate(sorted(sug_rows, key=lambda x: (x["theme_id"], x["pack"], x["local_id"])), 1):
        out.append({
            "master_id": f"SM-{i:03d}",
            "theme_id": r["theme_id"],
            "theme_name": TH.theme_names().get(r["theme_id"], "unsorted"),
            "source_pack": r["pack"],
            "source_file": r["file"],
            "source_row_id": r["local_id"],
            "area": _short(r.get("area", ""), 60),
            "suggestion": _short(r.get("statement") or r.get("title") or r.get("recommended"), 300),
            "problem_it_solves": _short(r.get("problem"), 300),
            "options_raised": _short(r.get("options"), 240),
            "recommended_by_source": _short(r.get("recommended"), 220),
            "effort": _short(r.get("effort"), 120),
            "risk_if_deferred": _short(r.get("risk"), 200),
            "priority_in_source": _short(r.get("priority"), 60),
            "status_in_source": _short(r.get("status"), 60),
            "requirements_touched": _short(r.get("requirements"), 120),
            "source_url": r.get("source_url", ""),
            "read_on": _short(r.get("read_on"), 40),
            "owner_decision": "",
            "owner_notes": "",
            "decision_logged_on": "",
        })
    return out


def questions_master(q_rows: List[Dict[str, str]], answers: List[Dict[str, str]],
                     obs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    closed = {a["theme"] for a in answers if a["status"].startswith(("CLOSED", "ANSWERED", "OPENED"))}
    partial = {a["theme"] for a in answers if a["status"].startswith("PARTIAL")}
    out = []
    for i, r in enumerate(sorted(q_rows, key=lambda x: (x["theme_id"], x["pack"], x["local_id"])), 1):
        tid = r["theme_id"]
        touched = [a for a in answers if a["theme"] == tid]
        status_src = _short(r.get("status"), 40)
        if tid in closed and touched:
            status_now = "EVIDENCE_ADDED_THIS_SESSION"
        elif tid in partial and touched:
            status_now = "PARTIALLY_CLOSED"
        else:
            status_now = "OPEN"
        out.append({
            "master_id": f"QM-{i:03d}",
            "theme_id": tid,
            "theme_name": TH.theme_names().get(tid, "unsorted"),
            "source_pack": r["pack"],
            "source_file": r["file"],
            "source_row_id": r["local_id"],
            "question": _short(r.get("statement") or r.get("title"), 300),
            "what_we_have": _short(r.get("evidence_needed") or r.get("recommended"), 260),
            "what_we_lack": _short(r.get("risk"), 200),
            "how_to_discover": _short(r.get("recommended") or r.get("evidence_needed"), 200),
            "status_in_source": status_src,
            "status_after_this_session": status_now,
            "this_session_answer": _short(touched[0]["answer"], 300) if touched else "",
            "answer_ids": ";".join(a["answer_id"] for a in touched),
            "observation_ids": ";".join(o["obs_id"] for o in obs if o["theme"] == tid),
            "source_url": r.get("source_url", ""),
            "owner_answer": "",
            "answer_logged_on": "",
        })
    return out


def decision_paths(sug_by_theme: Dict[str, List[Dict[str, str]]],
                   q_by_theme: Dict[str, List[Dict[str, str]]],
                   answers: List[Dict[str, str]],
                   obs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    rows_out: List[Dict[str, str]] = []
    for t in TH.THEMES:
        tid = t["theme_id"]
        srows, qrows = sug_by_theme.get(tid, []), q_by_theme.get(tid, [])
        allrows = srows + qrows
        packs = sorted({r["pack"] for r in allrows})
        evidence = [a for a in answers if a["theme"] == tid] + [o for o in obs if o["theme"] == tid]
        effort = _effort_score(_efforts(allrows, "effort"))
        value = 2 * len(packs) + len(allrows) + 2 * len(evidence)
        rows_out.append({
            "theme_id": tid,
            "decision": t["decision_question"],
            "theme_name": t["name"],
            "options": t["options"],
            "evidence_needed_to_choose": t["evidence_to_choose"],
            "why_now": t["why_now"],
            "brief_items_unblocked": t["brief_items"],
            "suggestion_rows": str(len(srows)),
            "question_rows": str(len(qrows)),
            "packs_raising_it": str(len(packs)),
            "packs": ";".join(p.replace("nfl_", "") for p in packs),
            "evidence_rows_this_session": str(len(evidence)),
            "effort_score": str(effort),
            "value": str(value),
            "ratio": f"{value / effort:.2f}",
            "status": "awaiting_owner_choice",
            "owner_choice": "",
            "owner_notes": "",
            "implement_only_after_choice": "yes",
        })
    rows_out.sort(key=lambda r: (-float(r["ratio"]), -int(r["packs_raising_it"]), r["theme_id"]))
    for i, r in enumerate(rows_out, 1):
        r["sequence"] = str(i)
    return rows_out


def information_board(sug_by_theme: Dict[str, List[Dict[str, str]]],
                      q_by_theme: Dict[str, List[Dict[str, str]]],
                      answers: List[Dict[str, str]],
                      obs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """One row per theme: what we know, what we do not, and how to find out."""
    out = []
    for t in TH.THEMES:
        tid = t["theme_id"]
        arows = [a for a in answers if a["theme"] == tid]
        orows = [o for o in obs if o["theme"] == tid]
        qrows = q_by_theme.get(tid, [])
        have = " || ".join(_short(a["answer"], 200) for a in arows) if arows else \
               " || ".join(_short(o["observation"], 200) for o in orows)
        lack_bits = [_short(a.get("still_open", ""), 160) for a in arows]
        lack = " || ".join(x for x in lack_bits if x)
        status = "ANSWERED OR EVIDENCED THIS SESSION" if arows else (
            "PARTIAL — evidence added, decision still open" if orows else "OPEN — nothing read yet")
        out.append({
            "theme_id": tid,
            "theme_name": t["name"],
            "question_to_answer": t["decision_question"],
            "information_we_have_from_the_repo": _short(
                " || ".join(_short(r.get("recommended") or r.get("evidence_needed"), 120)
                             for r in qrows[:4]), 420),
            "information_added_by_official_reads": have,
            "information_still_missing": lack or _short(t["evidence_to_choose"], 300),
            "how_to_get_it": t["evidence_to_choose"],
            "why_the_decision_waits": t["why_now"],
            "question_rows": str(len(qrows)),
            "suggestion_rows": str(len(sug_by_theme.get(tid, []))),
            "observation_ids": ";".join(o["obs_id"] for o in orows),
            "answer_ids": ";".join(a["answer_id"] for a in arows),
            "board_status": status,
        })
    return out
