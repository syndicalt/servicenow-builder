from __future__ import annotations

from typing import Any, Protocol

from jedi_devproject.models import ProviderPolicy, Story


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
            f"provider {policy.provider_id} is not approved for "
            f"task={task} data_class={story.data_classification.value}"
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

    for change in changes:
        if not isinstance(change, dict):
            raise ModelResponseError("change must be an object")

        table = str(change.get("table", ""))
        if table not in allowed_tables:
            raise ModelResponseError(f"table not allowed: {table}")

        operation = str(change.get("operation", ""))
        if operation not in allowed_operations:
            raise ModelResponseError(f"operation not allowed: {operation}")

        sys_id = change.get("sys_id")
        if sys_id is not None and str(sys_id) not in allowed_sys_ids:
            raise ModelResponseError(f"sys_id not allowed: {sys_id}")
