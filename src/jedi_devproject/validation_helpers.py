from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from jedi_devproject.models import CandidateChange

TRUTHY_TOKENS = frozenset({"1", "true", "yes"})
GENERATION_FIELD_NON_JSON_DIAGNOSTIC = (
    "generation field scalar value contains non-JSON value"
)


def stable_record_sys_id(*parts: str) -> str:
    """Deterministic 32-character sys_id derived from stable name parts.

    Matches the catalog-family convention (sha256 of pipe-joined parts,
    truncated to 32 hex characters) so records generated in the same update
    set can reference each other deterministically.
    """
    if any(type(part) is not str for part in parts):
        raise ValueError(GENERATION_FIELD_NON_JSON_DIAGNOSTIC)
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def bool_value(
    value: Any,
    *,
    default: bool = False,
    truthy: frozenset[str] = TRUTHY_TOKENS,
) -> bool:
    if value is None:
        return default
    return _scalar_text(value).strip().lower() in truthy


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def string_list(value: Any, *, ignore_none_token: bool = False) -> list[str]:
    if type(value) is list:
        return [text for item in value if (text := _scalar_text(item).strip())]
    text = "" if not value else _scalar_text(value).strip()
    if not text or (ignore_none_token and text.lower() == "none"):
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def slug(value: str, *, default: str) -> str:
    if type(value) is not str or type(default) is not str:
        raise ValueError(GENERATION_FIELD_NON_JSON_DIAGNOSTIC)
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned or default


def optional_int(value: Any) -> int | None:
    text = _scalar_text(value).strip()
    return int(text) if text.isdigit() else None


def reference_value(value: Any) -> str:
    if type(value) is dict:
        return _scalar_text(value.get("value"))
    return _scalar_text(value)


def single_insert_change(
    changes: list[CandidateChange],
    *,
    table: str,
    label: str,
) -> CandidateChange:
    if len(changes) != 1:
        raise ValueError(f"{label} handoff requires exactly one {table} change")
    change = changes[0]
    if change.table != table:
        raise ValueError(f"{label} handoff requires a {table} change")
    if change.operation != "insert":
        raise ValueError(f"{label} handoff supports insert only")
    return change


def _scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) is bool or type(value) is int:
        return str(value)
    if type(value) is float:
        if math.isfinite(value):
            return str(value)
        raise ValueError(GENERATION_FIELD_NON_JSON_DIAGNOSTIC)
    raise ValueError(GENERATION_FIELD_NON_JSON_DIAGNOSTIC)
