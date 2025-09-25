"""Data contract validation helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ContractValidationError(RuntimeError):
    """Raised when a data contract fails validation."""


@dataclass(slots=True)
class FieldSpec:
    name: str
    type: str
    required: bool


@dataclass(slots=True)
class DataContract:
    producer: str
    consumer: str
    schema_version: int
    fields: list[FieldSpec]
    freshness_sla_minutes: int
    max_null_percentage: float
    rules: list[str]

    @classmethod
    def from_path(cls, path: Path) -> "DataContract":
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        fields = [
            FieldSpec(name=str(item["name"]), type=str(item.get("type", "string")), required=bool(item.get("required", True)))
            for item in payload.get("fields", [])
        ]
        quality = payload.get("quality", {})
        validation = payload.get("validation", [])
        return cls(
            producer=str(payload.get("producer", "")),
            consumer=str(payload.get("consumer", "")),
            schema_version=int(payload.get("schema_version", 1)),
            fields=fields,
            freshness_sla_minutes=int(quality.get("freshness_sla_minutes", 0)),
            max_null_percentage=float(quality.get("max_null_percentage", 0.0)),
            rules=[str(rule.get("rule", "")) for rule in validation],
        )


REQUIRED_FIELDS = {"producer", "consumer", "schema_version", "fields"}


def validate_contract(path: Path) -> None:
    contract = DataContract.from_path(path)
    missing = [name for name in ("producer", "consumer") if not getattr(contract, name)]
    if missing:
        raise ContractValidationError(f"Missing required attributes: {', '.join(missing)}")
    if not contract.fields:
        raise ContractValidationError("Contract must specify at least one field")
    if contract.freshness_sla_minutes <= 0:
        raise ContractValidationError("freshness_sla_minutes must be > 0")
    if not 0 <= contract.max_null_percentage <= 100:
        raise ContractValidationError("max_null_percentage must be between 0 and 100")
    for field in contract.fields:
        if field.required and field.name not in {"experiment_id", "metric"} and not field.name:
            raise ContractValidationError("Required fields must have names")
    if not contract.rules:
        raise ContractValidationError("At least one validation rule required")
