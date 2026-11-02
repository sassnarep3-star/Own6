"""Strict, fail-closed ledger and rights contracts. No network collection."""
from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

HASH = re.compile(r"^[0-9a-f]{64}$")
MARKETS = {"moneyline", "spread", "total", "player_prop", "prop_combo", "parlay"}
COMBOS = {"prop_combo", "parlay"}
SPLITS = {"train", "validation", "holdout"}
FIELDS = [
    "observation_id", "event_id", "strategy_id", "split", "event_start_utc",
    "forecast_time_utc", "features_asof_utc", "market", "selection", "line",
    "probability", "market_probability", "decimal_odds", "closing_decimal_odds",
    "closing_line", "outcome", "odds_source_url", "close_source_url",
    "result_source_url", "feature_source_url", "odds_sha256", "close_sha256",
    "result_sha256", "feature_sha256", "license_id", "settlement_url",
    "model_version", "dependence_evidence",
]


class ContractError(ValueError):
    """Missing or malformed evidence; never impute a replacement value."""


def _text(row: dict, key: str) -> str:
    value = row.get(key, "")
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{key} is required")
    return value.strip()


def _number(row: dict, key: str) -> float:
    try:
        value = float(_text(row, key))
    except ValueError as exc:
        raise ContractError(f"{key} must be numeric") from exc
    if not math.isfinite(value):
        raise ContractError(f"{key} must be finite")
    return value


def _prob(row: dict, key: str) -> float:
    value = _number(row, key)
    if not 0 < value < 1:
        raise ContractError(f"{key} must be in (0,1)")
    return value


def _time(row: dict, key: str) -> datetime:
    raw = _text(row, key)
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError(f"{key} must be ISO-8601") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise ContractError(f"{key} must include a timezone")
    return value.astimezone(timezone.utc)


def _url(row: dict, key: str, approved_hosts: set[str]) -> str:
    value = _text(row, key)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in approved_hosts or parsed.username or parsed.password:
        raise ContractError(f"{key} is not an approved HTTPS provider source")
    return value


def _hash(row: dict, key: str) -> str:
    value = _text(row, key)
    if not HASH.fullmatch(value):
        raise ContractError(f"{key} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class Observation:
    observation_id: str
    event_id: str
    strategy_id: str
    split: str
    event_start: datetime
    forecast_time: datetime
    features_asof: datetime
    market: str
    selection: str
    line: float | None
    probability: float
    market_probability: float
    decimal_odds: float
    closing_decimal_odds: float
    closing_line: float | None
    outcome: float
    license_id: str
    model_version: str
    dependence_evidence: str
    source_urls: dict[str, str]
    source_hashes: dict[str, str]

    @property
    def is_combo(self) -> bool:
        return self.market in COMBOS

    @property
    def net_return(self) -> float:
        if self.outcome == 0.5:
            return 0.0
        return self.outcome * (self.decimal_odds - 1) - (1 - self.outcome)

    @property
    def clv(self) -> float:
        return math.log(self.decimal_odds / self.closing_decimal_odds)

    @classmethod
    def from_row(cls, row: dict, strategy_ids: set[str], approved_hosts: set[str], license_ids: set[str]) -> "Observation":
        sid = _text(row, "strategy_id")
        if sid not in strategy_ids:
            raise ContractError("unknown strategy; the frozen family cannot be expanded silently")
        split = _text(row, "split")
        if split not in SPLITS:
            raise ContractError("unknown split")
        market = _text(row, "market")
        if market not in MARKETS:
            raise ContractError("unknown market")
        start, forecast, features = (_time(row, k) for k in ("event_start_utc", "forecast_time_utc", "features_asof_utc"))
        if not features <= forecast < start:
            raise ContractError("require features_asof <= forecast < event_start")
        line_required = market in {"spread", "total", "player_prop"}
        line = _number(row, "line") if line_required else None
        close_line = _number(row, "closing_line") if line_required else None
        if line_required and line != close_line:
            raise ContractError("CLV requires the identical closing line")
        if not line_required and (row.get("line") or row.get("closing_line")):
            raise ContractError("line must be blank for this market; encode combo legs in selection")
        p, market_p = _prob(row, "probability"), _prob(row, "market_probability")
        odds, close = _number(row, "decimal_odds"), _number(row, "closing_decimal_odds")
        if odds <= 1 or close <= 1:
            raise ContractError("offered and closing decimal odds must exceed 1")
        outcome = _number(row, "outcome")
        if outcome not in (0.0, 0.5, 1.0):
            raise ContractError("outcome must be 0, 0.5 (push), or 1")
        license_id = _text(row, "license_id")
        if license_id not in license_ids:
            raise ContractError("no independently reviewed rights record for license_id")
        dependence = _text(row, "dependence_evidence")
        if market in COMBOS and dependence != "verified":
            raise ContractError("combo dependence evidence is missing")
        if market not in COMBOS and dependence != "not_required":
            raise ContractError("single-bet dependence_evidence must be not_required")
        url_keys = ["odds_source_url", "close_source_url", "result_source_url", "feature_source_url", "settlement_url"]
        hash_keys = ["odds_sha256", "close_sha256", "result_sha256", "feature_sha256"]
        return cls(
            observation_id=_text(row, "observation_id"), event_id=_text(row, "event_id"),
            strategy_id=sid, split=split, event_start=start, forecast_time=forecast,
            features_asof=features, market=market, selection=_text(row, "selection"),
            line=line, probability=p, market_probability=market_p,
            decimal_odds=odds, closing_decimal_odds=close, closing_line=close_line,
            outcome=outcome, license_id=license_id, model_version=_text(row, "model_version"),
            dependence_evidence=dependence,
            source_urls={k: _url(row, k, approved_hosts) for k in url_keys},
            source_hashes={k: _hash(row, k) for k in hash_keys},
        )


def load_rights(path: Path) -> tuple[set[str], set[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    hosts = data.get("approved_hosts", [])
    if not isinstance(hosts, list) or any(not isinstance(h, str) or not h or "/" in h or h != h.lower() for h in hosts):
        raise ContractError("approved_hosts must be lowercase hostnames without paths")
    approved = set(hosts)
    ids = set()
    for row in data.get("rows", []):
        if row.get("status") != "rights_reviewed":
            continue
        required = ["id", "provider", "contract_url", "contract_sha256", "reviewed_by", "reviewed_on"]
        if any(not isinstance(row.get(k), str) or not row[k].strip() for k in required):
            raise ContractError("incomplete rights record")
        if not HASH.fullmatch(row["contract_sha256"]):
            raise ContractError("invalid contract checksum")
        parsed = urlparse(row["contract_url"])
        if parsed.scheme != "https" or parsed.hostname not in approved:
            raise ContractError("rights contract is not on an approved HTTPS host")
        scope = row.get("use_scope", [])
        if not isinstance(scope, list) or not {"model_research", "public_summary"}.issubset(scope):
            raise ContractError("rights do not cover the intended research and publication")
        if row["id"] in ids:
            raise ContractError("duplicate rights record")
        ids.add(row["id"])
    return approved, ids


def load_ledger(path: Path, rights_path: Path, strategy_ids: set[str]) -> list[Observation]:
    approved, license_ids = load_rights(rights_path)
    observations = []
    seen = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ContractError("ledger header does not match contract v1")
        for line_number, row in enumerate(reader, 2):
            try:
                obs = Observation.from_row(row, strategy_ids, approved, license_ids)
            except ContractError as exc:
                raise ContractError(f"row {line_number}: {exc}") from exc
            if obs.observation_id in seen:
                raise ContractError(f"row {line_number}: duplicate observation_id")
            seen.add(obs.observation_id)
            observations.append(obs)
    return observations
