from __future__ import annotations

import math
import re
from collections.abc import Callable
from typing import Any

from jedi_devproject.unicode_controls import is_control_character

MAX_PROVIDER_CANDIDATE_CHANGES = 100
MAX_PROVIDER_CANDIDATE_FIELDS = 100
MAX_PROVIDER_FIELD_NAME_CHARS = 200
MAX_PROVIDER_FIELD_VALUE_TEXT_CHARS = 100_000
MAX_PROVIDER_JSON_SAFE_NUMBER_ABS = 9_007_199_254_740_991
MAX_PROVIDER_RATIONALE_CHARS = 2000
MAX_PROVIDER_TABLE_NAME_CHARS = 200
MIN_PROVIDER_TEXT_ITEM_CHARS = 1
MAX_PROVIDER_TEXT_LIST_ITEMS = 100
MAX_PROVIDER_TEXT_ITEM_CHARS = 2000
PROVIDER_NO_CONTROL_TEXT_PATTERN = (
    r"^[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*"
    r"[^\s\u0000-\u001F\u007F-\u009F\ud800-\udfff]"
    r"[^\u0000-\u001F\u007F-\u009F\ud800-\udfff]*$"
)
PROVIDER_SAFE_IDENTIFIER_PATTERN = r"^[A-Za-z_][A-Za-z0-9_]*$"
PROVIDER_CANDIDATE_KEYS = frozenset({"changes", "test_plan", "rollback_notes"})
PROVIDER_CHANGE_KEYS = frozenset({"table", "operation", "fields", "sys_id", "rationale"})
PROVIDER_FIELD_ENTRY_KEYS = frozenset({"name", "value"})
PROVIDER_CHANGE_OPERATIONS = frozenset({"insert", "update", "delete"})


def normalise_provider_candidate_response(
    candidate: dict[str, Any],
    *,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> dict[str, Any]:
    if type(candidate) is not dict:
        raise error_factory(f"{provider_name} response candidate must be an exact object")
    _validate_object_keys(
        candidate,
        label="candidate",
        provider_name=provider_name,
        error_factory=error_factory,
    )
    _validate_supported_keys(
        candidate,
        allowed_keys=PROVIDER_CANDIDATE_KEYS,
        label="candidate",
        provider_name=provider_name,
        error_factory=error_factory,
    )
    changes = candidate.get("changes")
    if type(changes) is not list:
        raise error_factory(f"{provider_name} response changes must be an exact list")
    if len(changes) > MAX_PROVIDER_CANDIDATE_CHANGES:
        raise error_factory(
            f"{provider_name} response includes too many changes "
            f"(max {MAX_PROVIDER_CANDIDATE_CHANGES})"
        )
    normalised_changes: list[dict[str, Any]] = []
    for change in changes:
        if type(change) is not dict:
            raise error_factory(f"{provider_name} response change must be an exact object")
        _validate_object_keys(
            change,
            label="change",
            provider_name=provider_name,
            error_factory=error_factory,
        )
        _validate_supported_keys(
            change,
            allowed_keys=PROVIDER_CHANGE_KEYS,
            label="change",
            provider_name=provider_name,
            error_factory=error_factory,
        )
        fields = change.get("fields")
        if type(fields) is not list:
            raise error_factory(
                f"{provider_name} response change fields must be an exact list"
            )
        if len(fields) > MAX_PROVIDER_CANDIDATE_FIELDS:
            raise error_factory(
                f"{provider_name} response change includes too many fields "
                f"(max {MAX_PROVIDER_CANDIDATE_FIELDS})"
            )
        normalised_fields: dict[str, Any] = {}
        for field in fields:
            if type(field) is not dict:
                raise error_factory(
                    f"{provider_name} response field entry must be an exact object"
                )
            _validate_object_keys(
                field,
                label="field entry",
                provider_name=provider_name,
                error_factory=error_factory,
            )
            _validate_supported_keys(
                field,
                allowed_keys=PROVIDER_FIELD_ENTRY_KEYS,
                label="field entry",
                provider_name=provider_name,
                error_factory=error_factory,
            )
            name = field.get("name")
            if type(name) is not str or name == "":
                raise error_factory(
                    f"{provider_name} response field entry must include a non-empty exact name"
                )
            _validate_field_name(
                name,
                provider_name=provider_name,
                error_factory=error_factory,
            )
            if name in normalised_fields:
                raise error_factory(
                    f"{provider_name} response field entry names must be unique"
                )
            if "value" not in field:
                raise error_factory(
                    f"{provider_name} response field entry must include value"
                )
            value = field["value"]
            _validate_field_value(
                value,
                provider_name=provider_name,
                error_factory=error_factory,
            )
            normalised_fields[name] = value
        _validate_change_metadata(
            change,
            provider_name=provider_name,
            error_factory=error_factory,
        )
        normalised_changes.append({**change, "fields": normalised_fields})

    _validate_text_list(
        candidate.get("test_plan"),
        label="test_plan",
        provider_name=provider_name,
        error_factory=error_factory,
    )
    _validate_text_list(
        candidate.get("rollback_notes"),
        label="rollback_notes",
        provider_name=provider_name,
        error_factory=error_factory,
    )
    if len(changes) == 0:
        raise error_factory(f"{provider_name} response must include at least one change")

    return {**candidate, "changes": normalised_changes}


def _validate_object_keys(
    value: dict[Any, Any],
    *,
    label: str,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if any(type(key) is not str for key in value):
        raise error_factory(f"{provider_name} response {label} keys must be exact strings")


def _validate_supported_keys(
    value: dict[str, Any],
    *,
    allowed_keys: frozenset[str],
    label: str,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if not value.keys() <= allowed_keys:
        raise error_factory(
            f"{provider_name} response {label} includes unsupported properties"
        )


def _validate_change_metadata(
    change: dict[str, Any],
    *,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    table = change.get("table")
    if type(table) is not str:
        raise error_factory(f"{provider_name} response change table must be an exact string")
    _validate_table_name(
        table,
        provider_name=provider_name,
        error_factory=error_factory,
    )

    operation = change.get("operation")
    if type(operation) is not str:
        raise error_factory(
            f"{provider_name} response change operation must be an exact string"
        )
    if operation not in PROVIDER_CHANGE_OPERATIONS:
        raise error_factory(f"{provider_name} response change operation is unsupported")

    if change.get("sys_id") is not None:
        raise error_factory(f"{provider_name} response change sys_id must be null")

    rationale = change.get("rationale")
    if rationale is not None and type(rationale) is not str:
        raise error_factory(
            f"{provider_name} response change rationale must be an exact string or null"
        )
    if type(rationale) is str and len(rationale) > MAX_PROVIDER_RATIONALE_CHARS:
        raise error_factory(
            f"{provider_name} response change rationale exceeds "
            f"{MAX_PROVIDER_RATIONALE_CHARS} characters"
        )
    if type(rationale) is str and _contains_control_character(rationale):
        raise error_factory(
            f"{provider_name} response change rationale must not contain control characters"
        )
    if type(rationale) is str and not _matches_text_pattern(rationale):
        raise error_factory(
            f"{provider_name} response change rationale must not match text policy"
        )


# ServiceNow scripts legitimately contain tab, LF, and CR, so field-value control-character
# validation allows those three ASCII whitespace controls while rejecting every other
# Unicode control, surrogate, and format category.
_ALLOWED_FIELD_VALUE_CONTROLS = frozenset("\t\n\r")


def _validate_field_value(
    value: Any,
    *,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if type(value) is str:
        if len(value) > MAX_PROVIDER_FIELD_VALUE_TEXT_CHARS:
            raise error_factory(
                f"{provider_name} response field value exceeds "
                f"{MAX_PROVIDER_FIELD_VALUE_TEXT_CHARS} characters"
            )
        if any(
            is_control_character(character)
            and character not in _ALLOWED_FIELD_VALUE_CONTROLS
            for character in value
        ):
            raise error_factory(
                f"{provider_name} response field value must not contain control characters"
            )
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        _validate_json_safe_number(
            value,
            provider_name=provider_name,
            error_factory=error_factory,
        )
        return
    if type(value) is float and math.isfinite(value):
        _validate_json_safe_number(
            value,
            provider_name=provider_name,
            error_factory=error_factory,
        )
        return
    raise error_factory(f"{provider_name} response field value must be a JSON scalar")


def _validate_text_list(
    value: Any,
    *,
    label: str,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if type(value) is not list:
        raise error_factory(f"{provider_name} response {label} must be an exact list")
    if len(value) > MAX_PROVIDER_TEXT_LIST_ITEMS:
        raise error_factory(
            f"{provider_name} response {label} includes too many items "
            f"(max {MAX_PROVIDER_TEXT_LIST_ITEMS})"
        )
    if any(type(item) is not str for item in value):
        raise error_factory(f"{provider_name} response {label} items must be exact strings")
    if any(item.strip() == "" for item in value):
        raise error_factory(
            f"{provider_name} response {label} items must be non-empty exact strings"
        )
    if any(_contains_control_character(item) for item in value):
        raise error_factory(
            f"{provider_name} response {label} items must not contain control characters"
        )
    if any(not _matches_text_pattern(item) for item in value):
        raise error_factory(
            f"{provider_name} response {label} items must not match text policy"
        )
    if any(len(item) > MAX_PROVIDER_TEXT_ITEM_CHARS for item in value):
        raise error_factory(
            f"{provider_name} response {label} item exceeds "
            f"{MAX_PROVIDER_TEXT_ITEM_CHARS} characters"
        )


def _validate_field_name(
    name: str,
    *,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if len(name) > MAX_PROVIDER_FIELD_NAME_CHARS:
        raise error_factory(
            f"{provider_name} response field entry name exceeds "
            f"{MAX_PROVIDER_FIELD_NAME_CHARS} characters"
        )
    if any(_is_whitespace_or_control(character) for character in name):
        raise error_factory(
            f"{provider_name} response field entry name must not contain "
            "whitespace or control characters"
        )
    if not _is_safe_identifier(name):
        raise error_factory(
            f"{provider_name} response field entry name must be a safe identifier"
        )


def _validate_json_safe_number(
    value: int | float,
    *,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if abs(value) > MAX_PROVIDER_JSON_SAFE_NUMBER_ABS:
        raise error_factory(
            f"{provider_name} response field numeric value is outside safe JSON range"
        )


def _validate_table_name(
    table: str,
    *,
    provider_name: str,
    error_factory: Callable[[str], Exception],
) -> None:
    if table.strip() == "":
        raise error_factory(
            f"{provider_name} response change table must be a non-empty identifier"
        )
    if len(table) > MAX_PROVIDER_TABLE_NAME_CHARS:
        raise error_factory(
            f"{provider_name} response change table exceeds "
            f"{MAX_PROVIDER_TABLE_NAME_CHARS} characters"
        )
    if any(_is_whitespace_or_control(character) for character in table):
        raise error_factory(
            f"{provider_name} response change table must not contain "
            "whitespace or control characters"
        )
    if not _is_safe_identifier(table):
        raise error_factory(
            f"{provider_name} response change table must be a safe identifier"
        )


def _is_whitespace_or_control(character: str) -> bool:
    return character.isspace() or is_control_character(character)


def _contains_control_character(value: str) -> bool:
    return any(is_control_character(character) for character in value)


def _matches_text_pattern(value: str) -> bool:
    return re.fullmatch(PROVIDER_NO_CONTROL_TEXT_PATTERN, value) is not None


def _is_safe_identifier(value: str) -> bool:
    return re.fullmatch(PROVIDER_SAFE_IDENTIFIER_PATTERN, value) is not None
