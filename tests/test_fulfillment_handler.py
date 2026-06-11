from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from jedi_devproject import fulfillment_handler as fulfillment_handler_module
from jedi_devproject.fulfillment_handler import (
    INTAKE_FEEDBACK_ARTIFACT_KIND,
    BuildClaimFulfillmentConfig,
    FulfillmentBlocked,
    build_claim_fulfillment_handler,
)
from jedi_devproject.models import DataClassification, Story
from jedi_devproject.operational_store import FulfillmentJobRecord
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice

# The default story text is a gate-failing request: the deterministic capability
# analysis classifies it as needs_clarification (missing field label/name and type).
GATE_FAILING_STORY_TEXT = "Add AI Review Notes field to Story form"
GATE_PASSING_STORY_TEXT = "Add a string field labeled AI Review Notes to the rm_story form"


class FakeWritebackClient:
    def __init__(
        self,
        *,
        story_state: str = "Ready",
        story_points: float = 3,
        story_text: str = GATE_FAILING_STORY_TEXT,
    ) -> None:
        self.story_state = story_state
        self.story_points = story_points
        self.story_text = story_text
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
                short_description=self.story_text,
                description=f"{self.story_text}.",
                story_points=self.story_points,
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


class FlakyIntakeFetchClient(FakeWritebackClient):
    """Fails the second story fetch (the intake assessment fetch) only.

    The first fetch belongs to the build claim, so the claim succeeds while the
    intake assessment errors.
    """

    def __init__(self, *, story_state: str = "Ready") -> None:
        super().__init__(story_state=story_state)
        self.fetch_calls = 0

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        self.fetch_calls += 1
        if self.fetch_calls == 2:
            raise RuntimeError("intake story fetch failed")
        return super().fetch_stories(sysparm_query, limit=limit)


class MissingStoryClient(FakeWritebackClient):
    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        return []


def _config(tmp_path: Path, **overrides: object) -> BuildClaimFulfillmentConfig:
    defaults: dict[str, object] = {
        "actor_id": "svc-jedi-orchestrator",
        "audit_root": tmp_path,
        "apply": True,
    }
    defaults.update(overrides)
    return BuildClaimFulfillmentConfig.model_validate(defaults)


def _work_note_only_updates(client: FakeWritebackClient) -> list[dict[str, object]]:
    return [
        update
        for update in client.updated_fields
        if isinstance(update["fields"], dict) and set(update["fields"]) == {"work_notes"}
    ]


def test_intake_feedback_delivered_for_gate_failing_story(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    result = handler(_job())

    assert result.message == "Build claim applied for STRY0010013"
    intake_updates = _work_note_only_updates(client)
    assert len(intake_updates) == 1
    assert len(client.updated_fields) == 2
    assert client.updated_fields[1] == intake_updates[0]
    assert intake_updates[0]["story_sys_id"] == "story-sys-id"
    fields = intake_updates[0]["fields"]
    assert isinstance(fields, dict)
    note = fields["work_notes"]
    assert isinstance(note, str)
    assert "cannot be automated as written" in note
    assert "missing_detail:field_type" in note
    assert "blocks the Dictionary Field and Form Placement automated build path" in note
    assert "Suggested rewrite:" in note

    assert len(result.artifacts) == 1
    artifact = result.artifacts[0]
    assert artifact.artifact_kind == INTAKE_FEEDBACK_ARTIFACT_KIND
    artifact_path = Path(artifact.path)
    assert artifact_path.exists()
    assert artifact_path.name.startswith("STRY0010013-intake-feedback-")
    assert artifact.sha256 == hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["feedback"]["reason_codes"] == [
        "missing_detail:field_label_or_field_name",
        "missing_detail:field_type",
    ]
    assert payload["feedback"]["suggested_story"]
    assert payload["delivered_fields"] == ["work_notes"]


def test_intake_feedback_is_idempotent_for_re_received_events(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    first = handler(_job())
    redelivered = handler(_job())
    new_event = handler(
        _job().model_copy(update={"job_id": "job-evt-002", "event_id": "evt-002"})
    )

    assert redelivered.message == "Build claim already recorded for STRY0010013"
    assert len(_work_note_only_updates(client)) == 1
    assert len(first.artifacts) == 1
    assert len(redelivered.artifacts) == 1
    assert len(new_event.artifacts) == 1
    assert redelivered.artifacts[0].path == first.artifacts[0].path
    assert redelivered.artifacts[0].sha256 == first.artifacts[0].sha256
    assert new_event.artifacts[0].path == first.artifacts[0].path


def test_intake_feedback_uses_story_sys_id_lookup_when_available(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    result = handler(_job().model_copy(update={"story_sys_id": "story-sys-id"}))

    assert len(result.artifacts) == 1
    assert result.artifacts[0].artifact_kind == INTAKE_FEEDBACK_ARTIFACT_KIND
    assert len(_work_note_only_updates(client)) == 1


def test_gate_passing_story_produces_no_intake_feedback(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready", story_text=GATE_PASSING_STORY_TEXT)
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    result = handler(_job())

    assert result.message == "Build claim applied for STRY0010013"
    assert result.artifacts == []
    assert _work_note_only_updates(client) == []
    assert len(client.updated_fields) == 1
    assert [path.name for path in tmp_path.iterdir()] == ["STRY0010013-evt-001-claim.json"]


def test_intake_assessment_error_does_not_block_fulfillment(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = FlakyIntakeFetchClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    with caplog.at_level("ERROR", logger="jedi_devproject.fulfillment_handler"):
        result = handler(_job())

    assert result.message == "Build claim applied for STRY0010013"
    assert result.artifacts == []
    assert "intake feedback assessment failed for story STRY0010013" in caplog.text
    assert _work_note_only_updates(client) == []
    assert len(client.updated_fields) == 1


def test_intake_feedback_dry_run_returns_payload_artifact_without_mutating(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(
        client=client,
        config=_config(tmp_path, apply=False),
    )

    result = handler(_job())

    assert result.message == "Build claim planned for STRY0010013"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []
    assert len(result.artifacts) == 1
    artifact = result.artifacts[0]
    assert artifact.artifact_kind == INTAKE_FEEDBACK_ARTIFACT_KIND
    assert artifact.payload_json is not None
    assert artifact.payload_json["reason_codes"] == [
        "missing_detail:field_label_or_field_name",
        "missing_detail:field_type",
    ]
    assert artifact.payload_json["suggested_story"]


def test_intake_feedback_can_be_disabled(tmp_path: Path) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(
        client=client,
        config=_config(tmp_path, intake_feedback_enabled=False),
    )

    result = handler(_job())

    assert result.artifacts == []
    assert _work_note_only_updates(client) == []


def test_intake_feedback_skips_when_story_is_missing(tmp_path: Path) -> None:
    client = MissingStoryClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    with pytest.raises(FulfillmentBlocked) as exc:
        handler(_job())

    assert exc.value.reasons == ["story_not_found"]
    assert client.updated_fields == []


class VanishingStoryClient(FakeWritebackClient):
    """Returns the story for the build claim fetch, then nothing afterwards."""

    def __init__(self, *, story_state: str = "Ready") -> None:
        super().__init__(story_state=story_state)
        self.fetch_calls = 0

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        self.fetch_calls += 1
        if self.fetch_calls > 1:
            return []
        return super().fetch_stories(sysparm_query, limit=limit)


def test_intake_feedback_skips_when_story_vanishes_after_claim(tmp_path: Path) -> None:
    client = VanishingStoryClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))

    result = handler(_job())

    assert result.message == "Build claim applied for STRY0010013"
    assert result.artifacts == []
    assert _work_note_only_updates(client) == []


def test_intake_feedback_blocks_non_allowlisted_fields_fail_open(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeWritebackClient(story_state="Ready")
    handler = build_claim_fulfillment_handler(client=client, config=_config(tmp_path))
    monkeypatch.setattr(
        fulfillment_handler_module,
        "StoryWritebackPolicy",
        lambda: SimpleNamespace(allowed_fields=set()),
    )

    with caplog.at_level("ERROR", logger="jedi_devproject.fulfillment_handler"):
        result = handler(_job())

    assert result.message == "Build claim applied for STRY0010013"
    assert result.artifacts == []
    assert _work_note_only_updates(client) == []
    assert "intake feedback assessment failed for story STRY0010013" in caplog.text
