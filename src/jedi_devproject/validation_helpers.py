from __future__ import annotations

import re
from typing import Any

from jedi_devproject.models import CandidateChange

TRUTHY_TOKENS = frozenset({"1", "true", "yes"})


def bool_value(
    value: Any,
    *,
    default: bool = False,
    truthy: frozenset[str] = TRUTHY_TOKENS,
) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in truthy


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def string_list(value: Any, *, ignore_none_token: bool = False) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    text = str(value or "").strip()
    if not text or (ignore_none_token and text.lower() == "none"):
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def slug(value: str, *, default: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return cleaned or default


def optional_int(value: Any) -> int | None:
    text = str(value or "").strip()
    return int(text) if text.isdigit() else None


def reference_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("value") or "")
    return str(value or "")


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
