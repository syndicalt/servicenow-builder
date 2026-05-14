from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict

from jedi_devproject.servicenow import HttpRequest, HttpTransport


class OpenAIProviderError(RuntimeError):
    """Raised when the OpenAI provider cannot return validated JSON."""


class OpenAIProviderSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: str
    model: str
    base_url: str = "https://api.openai.com/v1"


class OpenAIResponsesProvider:
    def __init__(
        self,
        *,
        settings: OpenAIProviderSettings,
        transport: HttpTransport,
    ) -> None:
        self._settings = settings
        self._transport = transport

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._transport.send(
            HttpRequest(
                method="POST",
                url=f"{self._settings.base_url.rstrip('/')}/responses",
                headers={
                    "Authorization": f"Bearer {self._settings.api_key}",
                    "Content-Type": "application/json",
                },
                body={
                    "model": self._settings.model,
                    "input": [
                        {
                            "role": "system",
                            "content": (
                                "Return only JSON matching the supplied schema. "
                                "If uncertain, return no changes and explain review "
                                "steps in the test plan."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(payload, sort_keys=True),
                        },
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "implementation_candidate",
                            "strict": True,
                            "schema": _implementation_candidate_schema(),
                        }
                    },
                },
            )
        )
        if response.status_code >= 400:
            raise OpenAIProviderError(
                f"OpenAI Responses API failed with status {response.status_code}"
            )
        return _parse_response_json(response.json_body)


def _parse_response_json(response: dict[str, Any]) -> dict[str, Any]:
    output_text = response.get("output_text")
    if isinstance(output_text, str):
        return _normalise_candidate_response(_loads_json_object(output_text))

    output = response.get("output", [])
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for content_item in content:
                if not isinstance(content_item, dict):
                    continue
                if content_item.get("type") == "output_text" and isinstance(
                    content_item.get("text"),
                    str,
                ):
                    return _normalise_candidate_response(
                        _loads_json_object(str(content_item["text"]))
                    )

    raise OpenAIProviderError("OpenAI response did not include output JSON")


def _loads_json_object(raw_json: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise OpenAIProviderError("OpenAI response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise OpenAIProviderError("OpenAI response JSON must be an object")
    return parsed


def _normalise_candidate_response(candidate: dict[str, Any]) -> dict[str, Any]:
    changes = candidate.get("changes")
    if not isinstance(changes, list):
        raise OpenAIProviderError("OpenAI response changes must be a list")

    normalised_changes: list[dict[str, Any]] = []
    for change in changes:
        if not isinstance(change, dict):
            raise OpenAIProviderError("OpenAI response change must be an object")
        fields = change.get("fields")
        if not isinstance(fields, list):
            raise OpenAIProviderError(
                "OpenAI response change fields must be a list of name/value pairs"
            )
        normalised_fields: dict[str, Any] = {}
        for field in fields:
            if not isinstance(field, dict):
                raise OpenAIProviderError(
                    "OpenAI response field entry must be an object"
                )
            name = field.get("name")
            if not isinstance(name, str) or not name:
                raise OpenAIProviderError(
                    "OpenAI response field entry must include a non-empty name"
                )
            normalised_fields[name] = field.get("value")
        normalised_changes.append({**change, "fields": normalised_fields})

    return {**candidate, "changes": normalised_changes}


def _implementation_candidate_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["changes", "test_plan", "rollback_notes"],
        "properties": {
            "changes": {
                "type": "array",
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
                        "sys_id": {"type": ["string", "null"]},
                        "rationale": {"type": ["string", "null"]},
                    },
                },
            },
            "test_plan": {"type": "array", "items": {"type": "string"}},
            "rollback_notes": {"type": "array", "items": {"type": "string"}},
        },
    }
