from typing import Any

import pytest

from jedi_devproject.models import DataClassification, ProviderPolicy, ProviderStatus, Story
from jedi_devproject.providers import (
    ModelResponseError,
    ProviderBlocked,
    generate_with_provider,
)


class RecordingProvider:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.payloads: list[dict[str, Any]] = []

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.payloads.append(payload)
        return self.response


def _story(data_classification: DataClassification = DataClassification.PUBLIC) -> Story:
    return Story(
        sys_id="abc123",
        number="STORY0010001",
        short_description="Update portal help text",
        description="Change portal help text from Submit to Send.",
        story_points=2,
        priority=3,
        state="Ready",
        data_classification=data_classification,
        acceptance_criteria="The portal shows Send instead of Submit.",
        affected_tables=["sp_instance"],
    )


def _policy(
    *,
    allowed_tasks: set[str] | None = None,
    allowed_data_classes: set[DataClassification] | None = None,
) -> ProviderPolicy:
    return ProviderPolicy(
        provider_id="approved-mock",
        deployment_boundary="local-dev",
        authorization_level="test-only",
        allowed_data_classes=allowed_data_classes or {DataClassification.PUBLIC},
        allowed_tasks=allowed_tasks or {"generate_candidate"},
        max_context_policy="minimal-story-fields",
        retention_policy="no-retention",
        status=ProviderStatus.APPROVED,
    )


def _valid_response() -> dict[str, Any]:
    return {
        "changes": [
            {
                "table": "sp_instance",
                "operation": "update",
                "fields": {"description": "Change portal help text from Submit to Send."},
                "sys_id": "abc123",
            }
        ],
        "reviewer_notes": ["Review before export."],
    }


def test_disallowed_provider_task_fails_before_prompt_construction() -> None:
    provider = RecordingProvider(_valid_response())

    with pytest.raises(ProviderBlocked):
        generate_with_provider(
            story=_story(),
            policy=_policy(allowed_tasks={"classify_story"}),
            provider=provider,
            task="generate_candidate",
            allowed_tables={"sp_instance"},
            allowed_operations={"update"},
            allowed_sys_ids={"abc123"},
        )

    assert provider.payloads == []


def test_disallowed_data_class_fails_closed() -> None:
    provider = RecordingProvider(_valid_response())

    with pytest.raises(ProviderBlocked):
        generate_with_provider(
            story=_story(DataClassification.CUI),
            policy=_policy(allowed_data_classes={DataClassification.PUBLIC}),
            provider=provider,
            task="generate_candidate",
            allowed_tables={"sp_instance"},
            allowed_operations={"update"},
            allowed_sys_ids={"abc123"},
        )

    assert provider.payloads == []


def test_approved_provider_receives_minimized_story_fields() -> None:
    provider = RecordingProvider(_valid_response())

    generate_with_provider(
        story=_story(),
        policy=_policy(),
        provider=provider,
        task="generate_candidate",
        allowed_tables={"sp_instance"},
        allowed_operations={"update"},
        allowed_sys_ids={"abc123"},
    )

    assert provider.payloads == [
        {
            "story_number": "STORY0010001",
            "short_description": "Update portal help text",
            "acceptance_criteria": "The portal shows Send instead of Submit.",
        }
    ]


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (
            {"changes": [{"table": "sys_user", "operation": "update", "fields": {}}]},
            "table not allowed: sys_user",
        ),
        (
            {"changes": [{"table": "sp_instance", "operation": "delete", "fields": {}}]},
            "operation not allowed: delete",
        ),
        (
            {
                "changes": [
                    {
                        "table": "sp_instance",
                        "operation": "update",
                        "fields": {},
                        "sys_id": "unknown",
                    }
                ]
            },
            "sys_id not allowed: unknown",
        ),
    ],
)
def test_model_response_validation_rejects_unsafe_changes(
    response: dict[str, Any],
    message: str,
) -> None:
    provider = RecordingProvider(response)

    with pytest.raises(ModelResponseError) as exc:
        generate_with_provider(
            story=_story(),
            policy=_policy(),
            provider=provider,
            task="generate_candidate",
            allowed_tables={"sp_instance"},
            allowed_operations={"update"},
            allowed_sys_ids={"abc123"},
        )

    assert message in str(exc.value)
