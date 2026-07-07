"""Shared model-provider contract for implementation-candidate generation.

Single source of truth for the system prompt and JSON schema that both the
OpenAI (:mod:`jedi_devproject.openai_provider`) and Anthropic
(:mod:`jedi_devproject.anthropic_provider`) adapters must send. The two
providers are interchangeable for model_fulfillment, so the prompt bytes and
the schema they transmit must stay byte-identical; adapters import from this
module rather than duplicating either.
"""

from __future__ import annotations

from typing import Any

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
    "inside the executable script."
    "For standard Catalog Item builds, return one "
    "sc_cat_item insert change, one item_option_new "
    "insert change per variable, and optional "
    "sc_cat_item_category and m2m_connected_content "
    "insert changes using discovered catalog, category, "
    "taxonomy, and Employee Center topic display names. "
    "Do not invent sys_ids; the deterministic handoff "
    "builder resolves existing records from instance context."
)


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
                        "table": {"type": "string"},
                        "operation": {
                            "type": "string",
                            "enum": ["insert", "update", "delete"],
                        },
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["name", "value"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "value": {
                                        "type": [
                                            "string",
                                            "number",
                                            "boolean",
                                            "null",
                                        ]
                                    },
                                },
                            },
                        },
                        "sys_id": {"type": "null"},
                        "rationale": {"type": ["string", "null"]},
                    },
                },
            },
            "test_plan": {"type": "array", "items": {"type": "string"}},
            "rollback_notes": {"type": "array", "items": {"type": "string"}},
        },
    }
