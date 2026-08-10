"""Shared model-provider contract for implementation-candidate generation.

Single source of truth for the system prompt and JSON schema that both the
OpenAI (:mod:`jedi_devproject.openai_provider`) and Anthropic
(:mod:`jedi_devproject.anthropic_provider`) adapters must send. The two
providers are interchangeable for model_fulfillment, so the prompt bytes and
the schema they transmit must stay byte-identical; adapters import from this
module rather than duplicating either.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from jedi_devproject.provider_response_normalization import (
    MAX_PROVIDER_CANDIDATE_CHANGES,
    MAX_PROVIDER_CANDIDATE_FIELDS,
    MAX_PROVIDER_FIELD_NAME_CHARS,
    MAX_PROVIDER_FIELD_VALUE_TEXT_CHARS,
    MAX_PROVIDER_JSON_SAFE_NUMBER_ABS,
    MAX_PROVIDER_RATIONALE_CHARS,
    MAX_PROVIDER_TABLE_NAME_CHARS,
    MAX_PROVIDER_TEXT_ITEM_CHARS,
    MAX_PROVIDER_TEXT_LIST_ITEMS,
    MIN_PROVIDER_TEXT_ITEM_CHARS,
    PROVIDER_NO_CONTROL_TEXT_PATTERN,
    PROVIDER_SAFE_IDENTIFIER_PATTERN,
)

IMPLEMENTATION_SYSTEM_PROMPT = (
    "Return only JSON matching the supplied schema. "
    "The deterministic gates decide whether the request "
    "is safe to automate before this model call. For an "
    "automated build packet, return at least one concrete "
    "ServiceNow change. "
    "For ServiceNow Business Rule sys_script changes, "
    "scripts must write fields only through current.<field> "
    "or current.setValue('<field>', value), must not use "
    "globals or other implicit objects for record writes, "
    "and must include fields_written naming every field "
    "the script writes in the JSON field metadata only. "
    "Do not put fields_written, tables_read, tables_written, "
    "test notes, rollback notes, or any metadata variable "
    "inside the executable script. "
    "For standard Catalog Item builds, return one "
    "sc_cat_item insert change, one item_option_new "
    "insert change per variable, and optional "
    "sc_cat_item_category and m2m_connected_content "
    "insert changes using discovered catalog, category, "
    "taxonomy, and Employee Center topic display names. "
    "Do not invent sys_ids; the deterministic handoff "
    "builder resolves existing records from instance context."
)

MODEL_PROVIDER_PROMPT_PAYLOAD_NON_FINITE_ERROR = (
    "Model provider prompt payload contains non-finite numeric values"
)
MODEL_PROVIDER_PROMPT_PAYLOAD_UNSUPPORTED_ERROR = (
    "Model provider prompt payload contains unsupported JSON value types"
)


def implementation_payload_json(
    payload: dict[str, Any],
    *,
    error_factory: Callable[[str], Exception],
) -> str:
    """Serialize implementation payloads for provider prompts as strict JSON."""
    try:
        safe_payload = _copy_exact_json_value(payload)
        return json.dumps(safe_payload, sort_keys=True, allow_nan=False)
    except TypeError:
        raise error_factory(MODEL_PROVIDER_PROMPT_PAYLOAD_UNSUPPORTED_ERROR) from None
    except ValueError:
        raise error_factory(MODEL_PROVIDER_PROMPT_PAYLOAD_NON_FINITE_ERROR) from None


def _copy_exact_json_value(value: Any) -> Any:
    if value is None or type(value) in {str, int, float, bool}:
        return value
    if type(value) is list:
        return [_copy_exact_json_value(item) for item in value]
    if type(value) is dict:
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("JSON object keys must be exact strings")
            copied[key] = _copy_exact_json_value(item)
        return copied
    raise TypeError("JSON value must be an exact JSON type")


def loads_strict_json_object(
    raw_json: str,
    *,
    error_factory: Callable[[str], Exception],
    invalid_json_message: str,
    non_object_message: str,
) -> dict[str, Any]:
    """Load provider JSON text without Python's non-standard numeric constants."""
    try:
        parsed = json.loads(raw_json, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError):
        raise error_factory(invalid_json_message) from None
    if not isinstance(parsed, dict):
        raise error_factory(non_object_message)
    return parsed


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def implementation_candidate_schema() -> dict[str, Any]:
    """Return a fresh copy of the implementation-candidate JSON schema.

    Returned as a new dict on every call so callers cannot mutate shared
    state; the Anthropic adapter strips constraints its structured-output
    validator rejects before sending.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["changes", "test_plan", "rollback_notes"],
        "properties": {
            "changes": {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_PROVIDER_CANDIDATE_CHANGES,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "table",
                        "operation",
                        "fields",
                        "sys_id",
                        "rationale",
                    ],
                    "properties": {
                        "table": {
                            "type": "string",
                            "maxLength": MAX_PROVIDER_TABLE_NAME_CHARS,
                            "pattern": PROVIDER_SAFE_IDENTIFIER_PATTERN,
                        },
                        "operation": {
                            "type": "string",
                            "enum": ["insert", "update", "delete"],
                        },
                        "fields": {
                            "type": "array",
                            "maxItems": MAX_PROVIDER_CANDIDATE_FIELDS,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["name", "value"],
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "maxLength": MAX_PROVIDER_FIELD_NAME_CHARS,
                                        "pattern": PROVIDER_SAFE_IDENTIFIER_PATTERN,
                                    },
                                    "value": {
                                        "type": [
                                            "string",
                                            "number",
                                            "boolean",
                                            "null",
                                        ],
                                        "maxLength": MAX_PROVIDER_FIELD_VALUE_TEXT_CHARS,
                                        "minimum": -MAX_PROVIDER_JSON_SAFE_NUMBER_ABS,
                                        "maximum": MAX_PROVIDER_JSON_SAFE_NUMBER_ABS,
                                    },
                                },
                            },
                        },
                        "sys_id": {"type": "null"},
                        "rationale": {
                            "type": ["string", "null"],
                            "maxLength": MAX_PROVIDER_RATIONALE_CHARS,
                            "pattern": PROVIDER_NO_CONTROL_TEXT_PATTERN,
                        },
                    },
                },
            },
            "test_plan": {
                "type": "array",
                "maxItems": MAX_PROVIDER_TEXT_LIST_ITEMS,
                "items": {
                    "type": "string",
                    "minLength": MIN_PROVIDER_TEXT_ITEM_CHARS,
                    "maxLength": MAX_PROVIDER_TEXT_ITEM_CHARS,
                    "pattern": PROVIDER_NO_CONTROL_TEXT_PATTERN,
                },
            },
            "rollback_notes": {
                "type": "array",
                "maxItems": MAX_PROVIDER_TEXT_LIST_ITEMS,
                "items": {
                    "type": "string",
                    "minLength": MIN_PROVIDER_TEXT_ITEM_CHARS,
                    "maxLength": MAX_PROVIDER_TEXT_ITEM_CHARS,
                    "pattern": PROVIDER_NO_CONTROL_TEXT_PATTERN,
                },
            },
        },
    }
