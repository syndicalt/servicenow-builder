from pathlib import Path

import pytest

from jedi_devproject.models import DataClassification, Story
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice
from jedi_devproject.writeback import ActorType, ExternalBuildStatus
from jedi_devproject.writeback_orchestration import (
    WritebackExecutionRequest,
    build_writeback_batch_report,
    evaluate_writeback_capability,
    execute_writeback,
    load_writeback_requests,
    run_writeback_batch,
)


class FakeWritebackClient:
    def __init__(
        self,
        *,
        story_state: str = "Ready",
        build_reference: str | None = None,
    ) -> None:
        self.updated_fields: list[dict[str, object]] = []
        self.story_state = story_state
        self.build_reference = build_reference
        self.dictionary_fields = [
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
            StoryDictionaryField(
                element="u_ai_build_reference",
                column_label="AI Build Reference",
                internal_type="string",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_candidate_artifact",
                column_label="AI Candidate Artifact",
                internal_type="string",
                active=True,
            ),
        ]

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
                additional_context={
                    "u_ai_build_reference": self.build_reference,
                },
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
        return self.dictionary_fields

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> None:
        self.updated_fields.append({"story_sys_id": story_sys_id, "fields": fields})


def test_execute_writeback_dry_run_does_not_mutate_or_write_audit(tmp_path: Path) -> None:
    client = FakeWritebackClient()

    result = execute_writeback(
        client,
        WritebackExecutionRequest(
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            artifact_url="artifacts/STRY0010013.json",
            build_status=ExternalBuildStatus.SUCCEEDED,
            from_state="Ready",
            apply=False,
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="run-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.allowed is True
    assert result.applied is False
    assert result.audit_path is None
    assert result.plan.fields["state"] == "-7"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []


def test_execute_writeback_applies_and_writes_audit_for_service_actor(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient()

    result = execute_writeback(
        client,
        WritebackExecutionRequest(
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            artifact_url="artifacts/STRY0010013.json",
            build_status=ExternalBuildStatus.SUCCEEDED,
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="run-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.applied is True
    fields = client.updated_fields[0]["fields"]
    assert isinstance(fields, dict)
    assert fields["state"] == "-7"
    assert result.audit_path == tmp_path / "STRY0010013-build-20260513-001.json"


def test_execute_writeback_retry_is_idempotent_when_audit_exists(tmp_path: Path) -> None:
    first_client = FakeWritebackClient()
    request = WritebackExecutionRequest(
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        artifact_url="artifacts/STRY0010013.json",
        build_status=ExternalBuildStatus.SUCCEEDED,
        from_state="Ready",
        apply=True,
        confirm_story_number="STRY0010013",
        actor_type=ActorType.SERVICE,
        actor_id="svc-jedi-orchestrator",
        execution_id="run-20260513-001",
        audit_root=tmp_path,
    )
    first = execute_writeback(first_client, request)
    retry_client = FakeWritebackClient()

    retry = execute_writeback(retry_client, request)

    assert first.applied is True
    assert retry.applied is False
    assert retry.idempotent is True
    assert retry.audit_path == first.audit_path
    assert retry.reasons == ["writeback_already_recorded"]
    assert retry_client.updated_fields == []


def test_execute_writeback_retry_is_idempotent_when_remote_story_matches(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient(
        story_state="-7",
        build_reference="build-20260513-001",
    )

    result = execute_writeback(
        client,
        WritebackExecutionRequest(
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            artifact_url="artifacts/STRY0010013.json",
            build_status=ExternalBuildStatus.SUCCEEDED,
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="run-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.applied is False
    assert result.idempotent is True
    assert result.reasons == ["remote_writeback_already_applied"]
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []


def test_evaluate_writeback_capability_passes_with_state_and_fields() -> None:
    result = evaluate_writeback_capability(FakeWritebackClient())

    assert result.allowed is True
    assert result.ready_for_testing_state == "-7"
    assert result.missing_fields == []
    assert result.reasons == []


def test_evaluate_writeback_capability_fails_closed_when_field_is_missing() -> None:
    client = FakeWritebackClient()
    client.dictionary_fields = [
        StoryDictionaryField(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            active=True,
        )
    ]

    result = evaluate_writeback_capability(client)

    assert result.allowed is False
    assert "state" not in result.missing_fields
    assert "u_ai_build_reference" in result.missing_fields
    assert "missing_required_writeback_fields" in result.reasons


def test_evaluate_writeback_capability_treats_state_choice_as_state_field() -> None:
    client = FakeWritebackClient()
    client.dictionary_fields = [
        StoryDictionaryField(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            active=True,
        ),
        StoryDictionaryField(
            element="u_ai_build_reference",
            column_label="AI Build Reference",
            internal_type="string",
            active=True,
        ),
        StoryDictionaryField(
            element="u_ai_candidate_artifact",
            column_label="AI Candidate Artifact",
            internal_type="string",
            active=True,
        ),
    ]

    result = evaluate_writeback_capability(client)

    assert result.allowed is True
    assert result.missing_fields == []


def test_run_writeback_batch_applies_requests_after_single_preflight(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient()
    requests = [
        WritebackExecutionRequest(
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            build_status=ExternalBuildStatus.SUCCEEDED,
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="run-20260513-001",
            audit_root=tmp_path,
        )
    ]

    result = run_writeback_batch(client, requests)

    assert result.summary == {
        "total": 1,
        "allowed": 1,
        "applied": 1,
        "idempotent": 0,
        "blocked": 0,
    }
    assert result.capability.allowed is True
    assert len(result.results) == 1
    assert len(client.updated_fields) == 1


def test_run_writeback_batch_fails_closed_when_capability_preflight_fails(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient()
    client.dictionary_fields = [
        StoryDictionaryField(
            element="state",
            column_label="State",
            internal_type="choice",
            active=True,
        )
    ]

    result = run_writeback_batch(
        client,
        [
            WritebackExecutionRequest(
                story_number="STRY0010013",
                build_reference="build-20260513-001",
                build_status=ExternalBuildStatus.SUCCEEDED,
                from_state="Ready",
                apply=True,
                confirm_story_number="STRY0010013",
                actor_type=ActorType.SERVICE,
                actor_id="svc-jedi-orchestrator",
                execution_id="run-20260513-001",
                audit_root=tmp_path,
            )
        ],
    )

    assert result.capability.allowed is False
    assert result.summary["blocked"] == 1
    assert result.results[0].reasons == ["writeback_capability_failed"]
    assert client.updated_fields == []


def test_load_writeback_requests_maps_json_jobs_to_execution_requests(
    tmp_path: Path,
) -> None:
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        """
        [
          {
            "story_number": "STRY0010013",
            "build_reference": "build-20260513-001",
            "artifact_url": "artifacts/STRY0010013.json",
            "from_state": "Ready"
          }
        ]
        """,
        encoding="utf-8",
    )

    requests = load_writeback_requests(
        jobs_path,
        apply=True,
        actor_type=ActorType.SERVICE,
        actor_id="svc-jedi-orchestrator",
        execution_id="run-20260513-001",
        audit_root=tmp_path / "audit",
    )

    assert requests == [
        WritebackExecutionRequest(
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            artifact_url="artifacts/STRY0010013.json",
            build_status=ExternalBuildStatus.SUCCEEDED,
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="run-20260513-001",
            audit_root=tmp_path / "audit",
        )
    ]


def test_load_writeback_requests_rejects_empty_job_file(tmp_path: Path) -> None:
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        load_writeback_requests(
            jobs_path,
            apply=True,
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="run-20260513-001",
            audit_root=tmp_path / "audit",
        )

    assert "at least one writeback job" in str(exc.value)


def test_build_writeback_batch_report_excludes_story_sys_ids(tmp_path: Path) -> None:
    client = FakeWritebackClient()
    batch = run_writeback_batch(
        client,
        [
            WritebackExecutionRequest(
                story_number="STRY0010013",
                build_reference="build-20260513-001",
                build_status=ExternalBuildStatus.SUCCEEDED,
                from_state="Ready",
                apply=True,
                confirm_story_number="STRY0010013",
                actor_type=ActorType.SERVICE,
                actor_id="svc-jedi-orchestrator",
                execution_id="run-20260513-001",
                audit_root=tmp_path,
            )
        ],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    assert report["execution_id"] == "run-20260513-001"
    assert report["summary"]["applied"] == 1
    assert report["results"][0]["story_number"] == "STRY0010013"
    assert "story_sys_id" not in repr(report)
