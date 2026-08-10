from __future__ import annotations

from typing import Any, Protocol

from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
from jedi_devproject.models import ProviderPolicy, Story
from jedi_devproject.provider_response_normalization import MAX_PROVIDER_CANDIDATE_CHANGES

MAX_MODEL_RESPONSE_DIAGNOSTIC_CHARS = 256
MODEL_RESPONSE_TRUNCATION_MARKER = "...[truncated]"


class ProviderBlocked(RuntimeError):
    """Raised when provider policy blocks a model task."""


class ModelResponseError(ValueError):
    """Raised when a model response violates safety constraints."""


class ModelProvider(Protocol):
    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Generate a candidate response from a minimized payload."""


def generate_with_provider(
    *,
    story: Story,
    policy: ProviderPolicy,
    provider: ModelProvider,
    task: str,
    allowed_tables: set[str],
    allowed_operations: set[str],
    allowed_sys_ids: set[str],
) -> dict[str, Any]:
    if not policy.allows(task=task, data_class=story.data_classification):
        raise ProviderBlocked(
            f"provider {_safe_model_response_diagnostic(policy.provider_id)} "
            "is not approved for "
            f"task={_safe_model_response_diagnostic(task)} "
            f"data_class={story.data_classification.value}"
        )

    response = provider.generate(_minimized_payload(story))
    _validate_response(
        response,
        allowed_tables=allowed_tables,
        allowed_operations=allowed_operations,
        allowed_sys_ids=allowed_sys_ids,
    )
    return response


def _minimized_payload(story: Story) -> dict[str, Any]:
    return {
        "story_number": story.number,
        "short_description": story.short_description,
        "acceptance_criteria": story.acceptance_criteria,
    }


def _validate_response(
    response: dict[str, Any],
    *,
    allowed_tables: set[str],
    allowed_operations: set[str],
    allowed_sys_ids: set[str],
) -> None:
    changes = response.get("changes", [])
    if not isinstance(changes, list):
        raise ModelResponseError("changes must be a list")
    if len(changes) > MAX_PROVIDER_CANDIDATE_CHANGES:
        raise ModelResponseError(
            f"model response includes too many changes "
            f"(max {MAX_PROVIDER_CANDIDATE_CHANGES})"
        )

    for change in changes:
        if not isinstance(change, dict):
            raise ModelResponseError("change must be an object")

        table = _required_response_text_field(change, "table")
        if table not in allowed_tables:
            raise ModelResponseError(
                f"table not allowed: {_safe_model_response_diagnostic(table)}"
            )

        operation = _required_response_text_field(change, "operation")
        if operation not in allowed_operations:
            raise ModelResponseError(
                "operation not allowed: "
                f"{_safe_model_response_diagnostic(operation)}"
            )

        sys_id = change.get("sys_id")
        if sys_id is not None:
            if type(sys_id) is not str:
                raise ModelResponseError("sys_id must be an exact string")
            if sys_id not in allowed_sys_ids:
                raise ModelResponseError(
                    f"sys_id not allowed: {_safe_model_response_diagnostic(sys_id)}"
                )


def _required_response_text_field(change: dict[str, Any], field_name: str) -> str:
    value = change.get(field_name, "")
    if type(value) is not str:
        raise ModelResponseError(f"{field_name} must be an exact string")
    return value


def _safe_model_response_diagnostic(value: str) -> str:
    redacted = _redact_diagnostic_text(value) or ""
    diagnostic = " ".join(redacted.split())
    if len(diagnostic) <= MAX_MODEL_RESPONSE_DIAGNOSTIC_CHARS:
        return diagnostic
    return (
        f"{diagnostic[:MAX_MODEL_RESPONSE_DIAGNOSTIC_CHARS]}"
        f"{MODEL_RESPONSE_TRUNCATION_MARKER}"
    )
