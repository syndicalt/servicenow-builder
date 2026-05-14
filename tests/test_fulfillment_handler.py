from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from jedi_devproject.fulfillment_handler import (
    BuildClaimFulfillmentConfig,
    FulfillmentBlocked,
    build_claim_fulfillment_handler,
)
from jedi_devproject.models import DataClassification, Story
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice


class FakeWritebackClient:
    def __init__(self, *, story_state: str = "Ready") -> None:
        self.story_state = story_state
        self.updated_fields: list[dict[str, object]] = []

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        return [
            Story(
                sys_id="story-sys-id",
                number="STRY0010013",
                short_description="Add AI Review Notes field to Story form",
                description="Add AI Review Notes field to Story form.",
                story_points=3,
                priority=4,
                state=self.story_state,
                data_classification=DataClassification.PUBLIC,
            )
        ]

    def fetch_story_state_choices(self) -> list[StoryStateChoice]:
        return [
            StoryStateChoice(
                label="Ready for Testing",
                value="-7",
                sequence=50,
                inactive=False,
            )
        ]

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        return [
            StoryDictionaryField(
                element="state",
                column_label="State",
                internal_type="choice",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
            ),
        ]

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> None:
        self.updated_fields.append({"story_sys_id": story_sys_id, "fields": fields})


def _job() -> FulfillmentJobRecord:
    return FulfillmentJobRecord(
        job_id="job-evt-001",
        event_id="evt-001",
        story_number="STRY0010013",
        status="running",
        attempt_count=1,
        created_at=datetime(2026, 5, 13, 15, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        locked_by="worker-1",
        locked_at=datetime(2026, 5, 13, 15, 1, tzinfo=UTC),
        last_error=None,
    )


def test_build_claim_handler_applies_claim_for_claimed_job(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(
        client=client,
        config=BuildClaimFulfillmentConfig(
            actor_id="svc-jedi-orchestrator",
            audit_root=tmp_path,
            apply=True,
        ),
    )

    result = handler(_job())

    assert result.message == "Build claim applied for STRY0010013"
    assert client.updated_fields[0]["story_sys_id"] == "story-sys-id"
    fields = client.updated_fields[0]["fields"]
    assert isinstance(fields, dict)
    assert fields["state"] == "Work in Progress"
    assert fields["u_ai_status"] == "Build In Progress"
    assert (tmp_path / "STRY0010013-evt-001-claim.json").exists()


def test_build_claim_handler_supports_dry_run_without_mutating(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(
        client=client,
        config=BuildClaimFulfillmentConfig(
            actor_id="svc-jedi-orchestrator",
            audit_root=tmp_path,
            apply=False,
        ),
    )

    result = handler(_job())

    assert result.message == "Build claim planned for STRY0010013"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []


def test_build_claim_handler_blocks_when_story_state_changed(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Draft")
    handler = build_claim_fulfillment_handler(
        client=client,
        config=BuildClaimFulfillmentConfig(
            actor_id="svc-jedi-orchestrator",
            audit_root=tmp_path,
            apply=True,
        ),
    )

    with pytest.raises(FulfillmentBlocked) as exc:
        handler(_job())

    assert exc.value.reasons == ["fresh_story_state_mismatch"]
    assert client.updated_fields == []


def test_build_claim_handler_requires_actor_for_apply(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(
        client=client,
        config=BuildClaimFulfillmentConfig(
            actor_id=None,
            audit_root=tmp_path,
            apply=True,
        ),
    )

    with pytest.raises(FulfillmentBlocked) as exc:
        handler(_job())

    assert exc.value.reasons == ["actor_identity_required"]


def test_build_claim_handler_uses_job_story_and_event_ids(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    job: FulfillmentJobRecord = _job().model_copy(
        update={"job_id": "job-evt-custom", "event_id": "evt-custom"}
    )
    handler = build_claim_fulfillment_handler(
        client=client,
        config=BuildClaimFulfillmentConfig(
            actor_id="svc-jedi-orchestrator",
            audit_root=tmp_path,
            apply=True,
        ),
    )

    handler(job)

    assert (tmp_path / "STRY0010013-evt-custom-claim.json").exists()
