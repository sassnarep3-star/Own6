"""Structured, artifact-bound audit evidence. Missing evidence never passes.

This module validates the *structure and binding* of supplied audit records. It
cannot independently certify the truth of an external artifact offline. A pass
means a reviewer supplied a hashed artifact bound to this config and ledger; the
artifact itself remains subject to review. The bundled file has no records.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

HASH = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_KEYS = (
    "rights_verified", "provenance_verified", "walk_forward_verified",
    "ledger_audited", "preregistered", "dependence_verified", "power_verified",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_evidence(path: Path, *, config_sha256: str, ledger_sha256: str) -> dict:
    result = {key: False for key in EVIDENCE_KEYS}
    result.update({"records": [], "config_sha256": config_sha256, "ledger_sha256": ledger_sha256})
    if not path.exists():
        return result
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 2:
        raise ValueError("evidence file must use schema_version 2")
    records = data.get("records", [])
    if not isinstance(records, list):
        raise ValueError("evidence records must be a list")
    seen = set()
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"evidence record {i} must be an object")
        key = record.get("key")
        if key not in EVIDENCE_KEYS or key in seen:
            raise ValueError(f"evidence record {i}: unknown or duplicate key")
        seen.add(key)
        if record.get("status") != "verified":
            continue
        for field in ("reviewer", "reviewed_on", "artifact_url", "artifact_sha256", "config_sha256", "ledger_sha256"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f"evidence record {key}: missing {field}")
        if not HASH.fullmatch(record["artifact_sha256"]):
            raise ValueError(f"evidence record {key}: invalid artifact checksum")
        if record["config_sha256"] != config_sha256 or record["ledger_sha256"] != ledger_sha256:
            raise ValueError(f"evidence record {key}: audit is not bound to this config and ledger")
        parsed = urlparse(record["artifact_url"])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"evidence record {key}: artifact_url must be HTTPS")
        try:
            date.fromisoformat(record["reviewed_on"])
        except ValueError as exc:
            raise ValueError(f"evidence record {key}: reviewed_on must be ISO date") from exc
        scope = record.get("scope")
        if not isinstance(scope, list) or not scope or not all(isinstance(x, str) and x for x in scope):
            raise ValueError(f"evidence record {key}: explicit scope required")
        result[key] = True
        result["records"].append(record)
    return result
