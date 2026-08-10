from pathlib import Path
from typing import Any

import pytest

from jedi_devproject.models import DataClassification, Story
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice
from jedi_devproject.writeback import ActorType, ExternalBuildStatus, StoryWritebackPlan
from jedi_devproject.writeback_orchestration import (
    BuildClaimExecutionRequest,
    WritebackBatchResult,
    WritebackCapabilityResult,
    WritebackExecutionRequest,
    WritebackExecutionResult,
    build_writeback_batch_report,
    evaluate_writeback_capability,
    execute_build_claim,
    execute_writeback,
    load_writeback_requests,
    run_writeback_batch,
    verify_writeback,
)


class FakeWritebackClient:
    def __init__(
        self,
        *,
        story_state: str = "Ready",
        ai_status: str | None = None,
        build_reference: str | None = None,
        candidate_artifact: str | None = None,
    ) -> None:
        self.updated_fields: list[dict[str, object]] = []
        self.story_state = story_state
        self.ai_status = ai_status
        self.build_reference = build_reference
        self.candidate_artifact = candidate_artifact
        self.fetch_story_queries: list[str | None] = []
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
        self.fetch_story_queries.append(sysparm_query)
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
                    key: value
                    for key, value in {
                        "u_ai_status": self.ai_status,
                        "u_ai_build_reference": self.build_reference,
                        "u_ai_candidate_artifact": self.candidate_artifact,
                    }.items()
                    if value is not None
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


def test_execute_build_claim_dry_run_does_not_mutate_or_write_audit(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient(story_state="Ready")

    result = execute_build_claim(
        client,
        BuildClaimExecutionRequest(
            story_number="STRY0010013",
            lifecycle_event_id="evt-20260513-001",
            candidate_artifact_url="artifacts/implementation-candidates/STRY0010013.json",
            from_state="Ready",
            apply=False,
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="claim-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.allowed is True
    assert result.applied is False
    assert result.audit_path is None
    assert result.plan.fields["state"] == "Work in Progress"
    assert result.plan.fields["u_ai_status"] == "Build In Progress"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []


def test_execute_build_claim_applies_and_writes_claim_audit(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient(story_state="Ready")

    result = execute_build_claim(
        client,
        BuildClaimExecutionRequest(
            story_number="STRY0010013",
            lifecycle_event_id="evt-20260513-001",
            candidate_artifact_url="artifacts/implementation-candidates/STRY0010013.json",
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="claim-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.allowed is True
    assert result.applied is True
    assert result.audit_path == tmp_path / "STRY0010013-evt-20260513-001-claim.json"
    fields = client.updated_fields[0]["fields"]
    assert isinstance(fields, dict)
    assert fields["state"] == "Work in Progress"
    assert fields["u_ai_status"] == "Build In Progress"
    assert "Automated build started" in str(fields["work_notes"])


def test_execute_build_claim_prefers_story_sys_id_for_fresh_story_lookup(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient(story_state="Ready")

    result = execute_build_claim(
        client,
        BuildClaimExecutionRequest(
            story_number="STRY0010013",
            story_sys_id="correct-story-sys-id",
            lifecycle_event_id="evt-20260513-001",
            candidate_artifact_url=None,
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="claim-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.allowed is True
    assert client.fetch_story_queries[0] == "sys_id=correct-story-sys-id"


def test_execute_build_claim_fails_closed_when_fresh_story_is_not_ready(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient(story_state="Draft")

    result = execute_build_claim(
        client,
        BuildClaimExecutionRequest(
            story_number="STRY0010013",
            lifecycle_event_id="evt-20260513-001",
            candidate_artifact_url=None,
            from_state="Ready",
            apply=True,
            confirm_story_number="STRY0010013",
            actor_type=ActorType.SERVICE,
            actor_id="svc-jedi-orchestrator",
            execution_id="claim-20260513-001",
            audit_root=tmp_path,
        ),
    )

    assert result.allowed is False
    assert result.applied is False
    assert result.reasons == ["fresh_story_state_mismatch"]
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []


def test_execute_writeback_accepts_state_from_state_mapping_when_dictionary_omits_state(
    tmp_path: Path,
) -> None:
    client = FakeWritebackClient()
    client.dictionary_fields = [
        field for field in client.dictionary_fields if field.element != "state"
    ]

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
    assert result.plan.fields["state"] == "-7"
    assert result.reasons == []


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


def test_evaluate_writeback_capability_rejects_state_choice_collection_subclass_without_leak(
) -> None:
    class SecretBearingStateChoices(list[StoryStateChoice]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=writeback-state-choices-iter-secret")

    class MalformedStateChoiceClient(FakeWritebackClient):
        def fetch_story_state_choices(self) -> list[StoryStateChoice]:
            return SecretBearingStateChoices(
                [
                    StoryStateChoice(
                        label="Ready for Testing",
                        value="-7",
                        sequence=50,
                        inactive=False,
                    )
                ]
            )

    with pytest.raises(ValueError) as exc_info:
        evaluate_writeback_capability(MalformedStateChoiceClient())

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback state choices contain non-JSON value"
    assert "SecretBearingStateChoices" not in diagnostic
    assert "writeback-state-choices-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_evaluate_writeback_capability_rejects_state_choice_item_subclass_without_leak() -> None:
    class SecretBearingStateChoice(StoryStateChoice):
        def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("client_secret=writeback-state-choice-model-dump-secret")

    class MalformedStateChoiceClient(FakeWritebackClient):
        def fetch_story_state_choices(self) -> list[StoryStateChoice]:
            return [
                SecretBearingStateChoice(
                    label="Ready for Testing",
                    value="-7",
                    sequence=50,
                    inactive=False,
                )
            ]

    with pytest.raises(ValueError) as exc_info:
        evaluate_writeback_capability(MalformedStateChoiceClient())

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback state choices contain non-JSON value"
    assert "SecretBearingStateChoice" not in diagnostic
    assert "writeback-state-choice-model-dump-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_execute_writeback_rejects_state_choice_collection_subclass_before_mutation(
    tmp_path: Path,
) -> None:
    class SecretBearingStateChoices(list[StoryStateChoice]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=writeback-execute-state-choices-iter")

    class MalformedStateChoiceClient(FakeWritebackClient):
        def fetch_story_state_choices(self) -> list[StoryStateChoice]:
            return SecretBearingStateChoices(
                [
                    StoryStateChoice(
                        label="Ready for Testing",
                        value="-7",
                        sequence=50,
                        inactive=False,
                    )
                ]
            )

    client = MalformedStateChoiceClient()

    with pytest.raises(ValueError) as exc_info:
        execute_writeback(
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

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback state choices contain non-JSON value"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []
    assert "SecretBearingStateChoices" not in diagnostic
    assert "writeback-execute-state-choices-iter" not in diagnostic
    assert "client_secret" not in diagnostic


def test_evaluate_writeback_capability_rejects_dictionary_field_collection_subclass_without_leak(
) -> None:
    class SecretBearingDictionaryFields(list[StoryDictionaryField]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=writeback-dictionary-fields-iter-secret")

    class MalformedDictionaryFieldClient(FakeWritebackClient):
        def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
            return SecretBearingDictionaryFields(self.dictionary_fields)

    with pytest.raises(ValueError) as exc_info:
        evaluate_writeback_capability(MalformedDictionaryFieldClient())

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback dictionary fields contain non-JSON value"
    assert "SecretBearingDictionaryFields" not in diagnostic
    assert "writeback-dictionary-fields-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_evaluate_writeback_capability_rejects_dictionary_field_item_subclass_without_leak(
) -> None:
    class SecretBearingDictionaryField(StoryDictionaryField):
        def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise RuntimeError("client_secret=writeback-dictionary-field-model-dump-secret")

    class MalformedDictionaryFieldClient(FakeWritebackClient):
        def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
            return [
                SecretBearingDictionaryField(
                    element="u_ai_status",
                    column_label="AI Status",
                    internal_type="string",
                    active=True,
                )
            ]

    with pytest.raises(ValueError) as exc_info:
        evaluate_writeback_capability(MalformedDictionaryFieldClient())

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback dictionary fields contain non-JSON value"
    assert "SecretBearingDictionaryField" not in diagnostic
    assert "writeback-dictionary-field-model-dump-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_execute_writeback_rejects_dictionary_field_collection_subclass_before_mutation(
    tmp_path: Path,
) -> None:
    class SecretBearingDictionaryFields(list[StoryDictionaryField]):
        def __iter__(self) -> Any:
            raise RuntimeError("client_secret=writeback-execute-dictionary-fields-iter")

    class MalformedDictionaryFieldClient(FakeWritebackClient):
        def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
            return SecretBearingDictionaryFields(self.dictionary_fields)

    client = MalformedDictionaryFieldClient()

    with pytest.raises(ValueError) as exc_info:
        execute_writeback(
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

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback dictionary fields contain non-JSON value"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []
    assert "SecretBearingDictionaryFields" not in diagnostic
    assert "writeback-execute-dictionary-fields-iter" not in diagnostic
    assert "client_secret" not in diagnostic


def test_verify_writeback_rejects_story_collection_subclass_without_leak() -> None:
    class SecretBearingStories(list[Story]):
        def __len__(self) -> int:
            raise RuntimeError("client_secret=writeback-stories-len-secret")

    class MalformedStoryClient(FakeWritebackClient):
        def fetch_stories(
            self,
            sysparm_query: str | None = None,
            *,
            limit: int = 100,
        ) -> list[Story]:
            return SecretBearingStories(super().fetch_stories(sysparm_query, limit=limit))

    with pytest.raises(ValueError) as exc_info:
        verify_writeback(
            MalformedStoryClient(),
            story_number="STRY0010013",
            build_reference="build-20260513-001",
            artifact_url="artifacts/STRY0010013.json",
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback stories contain non-JSON value"
    assert "SecretBearingStories" not in diagnostic
    assert "writeback-stories-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_execute_writeback_rejects_story_item_subclass_before_mutation(
    tmp_path: Path,
) -> None:
    class SecretBearingStory(Story):
        def model_copy(self, *args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("client_secret=writeback-story-model-copy-secret")

    class MalformedStoryClient(FakeWritebackClient):
        def fetch_stories(
            self,
            sysparm_query: str | None = None,
            *,
            limit: int = 100,
        ) -> list[Story]:
            story = super().fetch_stories(sysparm_query, limit=limit)[0]
            return [SecretBearingStory.model_validate(story.model_dump())]

    client = MalformedStoryClient()

    with pytest.raises(ValueError) as exc_info:
        execute_writeback(
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

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback stories contain non-JSON value"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []
    assert "SecretBearingStory" not in diagnostic
    assert "writeback-story-model-copy-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_execute_build_claim_rejects_story_collection_subclass_before_mutation(
    tmp_path: Path,
) -> None:
    class SecretBearingStories(list[Story]):
        def __bool__(self) -> bool:
            raise RuntimeError("client_secret=writeback-claim-stories-bool-secret")

    class MalformedStoryClient(FakeWritebackClient):
        def fetch_stories(
            self,
            sysparm_query: str | None = None,
            *,
            limit: int = 100,
        ) -> list[Story]:
            return SecretBearingStories(super().fetch_stories(sysparm_query, limit=limit))

    client = MalformedStoryClient()

    with pytest.raises(ValueError) as exc_info:
        execute_build_claim(
            client,
            BuildClaimExecutionRequest(
                story_number="STRY0010013",
                lifecycle_event_id="evt-20260513-001",
                candidate_artifact_url="artifacts/implementation-candidates/STRY0010013.json",
                from_state="Ready",
                apply=True,
                confirm_story_number="STRY0010013",
                actor_type=ActorType.SERVICE,
                actor_id="svc-jedi-orchestrator",
                execution_id="claim-20260513-001",
                audit_root=tmp_path,
            ),
        )

    diagnostic = str(exc_info.value)
    assert diagnostic == "writeback stories contain non-JSON value"
    assert client.updated_fields == []
    assert list(tmp_path.iterdir()) == []
    assert "SecretBearingStories" not in diagnostic
    assert "writeback-claim-stories-bool-secret" not in diagnostic
    assert "client_secret" not in diagnostic


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


def test_build_writeback_batch_report_redacts_diagnostic_values(tmp_path: Path) -> None:
    batch = WritebackBatchResult(
        capability=WritebackCapabilityResult(
            allowed=False,
            reasons=["capability failed\napi_key=capability-secret"],
        ),
        summary={"total": 1, "allowed": 0, "applied": 0, "idempotent": 0, "blocked": 1},
        results=[
            WritebackExecutionResult(
                plan=StoryWritebackPlan(
                    story_sys_id="story-sys-id",
                    story_number="STRY0010013",
                    work_notes="",
                    allowed=False,
                    reasons=["plan blocked\nclient_secret=plan-secret"],
                ),
                allowed=False,
                applied=False,
                audit_path=tmp_path / "audit\napi_key=path-secret.json",
                reasons=["result blocked\nclient_secret=result-secret"],
            )
        ],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001\nclient_secret=execution-secret",
        actor_id="svc-jedi-orchestrator\napi_key=actor-secret",
    )

    rendered_report = repr(report)
    assert "capability-secret" not in rendered_report
    assert "plan-secret" not in rendered_report
    assert "path-secret" not in rendered_report
    assert "result-secret" not in rendered_report
    assert "execution-secret" not in rendered_report
    assert "actor-secret" not in rendered_report
    assert "client_secret=***REDACTED***" in rendered_report
    assert "api_key=***REDACTED***" in rendered_report
    assert "\n" not in rendered_report
    assert "story_sys_id" not in rendered_report


def test_build_writeback_batch_report_handles_cyclic_and_deep_diagnostics(
    tmp_path: Path,
) -> None:
    cyclic_summary: dict[str, object] = {"total": 1}
    cyclic_summary["self"] = cyclic_summary
    deep_reason: object = "leaf"
    for _ in range(80):
        deep_reason = [deep_reason]
    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[deep_reason],
        ),
        summary=cyclic_summary,
        results=[
            WritebackExecutionResult(
                plan=StoryWritebackPlan(
                    story_sys_id="story-sys-id",
                    story_number="STRY0010013",
                    work_notes="",
                    allowed=False,
                    reasons=[],
                ),
                allowed=False,
                applied=False,
                audit_path=tmp_path / "audit.json",
                reasons=[],
            )
        ],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    rendered_report = repr(report)
    assert "[circular reference]" in rendered_report
    assert "[max depth exceeded]" in rendered_report
    assert "RecursionError" not in rendered_report


def test_build_writeback_batch_report_normalizes_unsupported_scalar_diagnostics() -> (
    None
):
    object_value = object()
    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[
                b"binary-secret",
                object_value,
                float("nan"),
                float("inf"),
                -float("inf"),
                1.25,
                True,
                None,
            ],
        ),
        summary={
            "total": 1,
            "unsafe": object_value,
            "bad_score": float("nan"),
            "safe_score": 1.25,
            "flag": True,
            "empty": None,
        },
        results=[],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    rendered_report = repr(report)
    assert "binary-secret" not in rendered_report
    assert "object at 0x" not in rendered_report
    assert "nan" not in rendered_report.lower()
    assert "inf" not in rendered_report.lower()
    assert "[non-json value]" in rendered_report
    assert report["summary"]["safe_score"] == 1.25
    assert report["summary"]["flag"] is True
    assert report["summary"]["empty"] is None
    assert 1.25 in report["capability"]["reasons"]
    assert True in report["capability"]["reasons"]
    assert None in report["capability"]["reasons"]
    assert "story_sys_id" not in rendered_report


def test_build_writeback_batch_report_rejects_string_subclass_diagnostics() -> None:
    class HostileDiagnosticText(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=batch-report-string-secret")

    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[HostileDiagnosticText("client_secret=reason-payload")],
        ),
        summary={"unsafe": HostileDiagnosticText("client_secret=summary-payload")},
        results=[],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    rendered_report = repr(report)
    assert "reason-payload" not in rendered_report
    assert "summary-payload" not in rendered_report
    assert report["capability"]["reasons"] == ["[non-json value]"]
    assert report["summary"]["unsafe"] == "[non-json value]"


def test_build_writeback_batch_report_rejects_scalar_subclass_diagnostics() -> None:
    class HostileDiagnosticOrder(int):
        def __str__(self) -> str:
            raise AssertionError("client_secret=batch-report-scalar-secret")

    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[HostileDiagnosticOrder(3)],
        ),
        summary={"unsafe": HostileDiagnosticOrder(4)},
        results=[],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    assert report["capability"]["reasons"] == ["[non-json value]"]
    assert report["summary"]["unsafe"] == "[non-json value]"


def test_build_writeback_batch_report_rejects_container_subclass_diagnostics() -> (
    None
):
    class HostileReportDict(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("client_secret=writeback-dict-subclass-secret")

    class HostileReportList(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=writeback-list-subclass-secret")

    class HostileReportTuple(tuple[Any, ...]):
        def __iter__(self) -> Any:
            raise AssertionError("client_secret=writeback-tuple-subclass-secret")

    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[],
        ),
        summary={
            "dict": HostileReportDict({"message": "hidden dict"}),
            "list": HostileReportList(["hidden list"]),
            "tuple": HostileReportTuple(("hidden tuple",)),
        },
        results=[],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    rendered_report = repr(report)
    assert report["capability"]["reasons"] == []
    assert report["summary"] == {
        "dict": "[non-json value]",
        "list": "[non-json value]",
        "tuple": "[non-json value]",
    }
    assert "hidden dict" not in rendered_report
    assert "hidden list" not in rendered_report
    assert "hidden tuple" not in rendered_report
    assert "subclass-secret" not in rendered_report


def test_build_writeback_batch_report_normalizes_non_string_diagnostic_keys() -> None:
    class ExplodingDiagnosticKey:
        def __str__(self) -> str:
            raise AssertionError("client_secret=writeback-key-str-secret")

        def __repr__(self) -> str:
            return "ExplodingDiagnosticKey(client_secret=writeback-key-repr-secret)"

    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[],
        ),
        summary={
            "total": 1,
            ExplodingDiagnosticKey(): "visible diagnostic",
        },
        results=[],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    rendered_report = repr(report)
    assert "[non-json key]" in rendered_report
    assert "visible diagnostic" in rendered_report
    assert "ExplodingDiagnosticKey" not in rendered_report
    assert "client_secret" not in rendered_report
    assert "writeback-key" not in rendered_report


def test_build_writeback_batch_report_preserves_colliding_diagnostic_keys() -> None:
    class ExplodingDiagnosticKey:
        def __str__(self) -> str:
            raise AssertionError("client_secret=writeback-collision-str-secret")

        def __repr__(self) -> str:
            return "ExplodingDiagnosticKey(client_secret=writeback-collision-repr-secret)"

    batch = WritebackBatchResult.model_construct(
        capability=WritebackCapabilityResult.model_construct(
            allowed=False,
            reasons=[],
        ),
        summary={
            ExplodingDiagnosticKey(): "first non-json diagnostic",
            ExplodingDiagnosticKey(): "second non-json diagnostic",
            "api_key=first-collision": "first redacted-key diagnostic",
            "api_key=second-collision": "second redacted-key diagnostic",
        },
        results=[],
    )

    report = build_writeback_batch_report(
        batch,
        execution_id="run-20260513-001",
        actor_id="svc-jedi-orchestrator",
    )

    rendered_report = repr(report)
    assert report["summary"]["[non-json key]"] == "first non-json diagnostic"
    assert (
        report["summary"]["[non-json key] [duplicate 2]"]
        == "second non-json diagnostic"
    )
    assert (
        report["summary"]["api_key=***REDACTED***"]
        == "first redacted-key diagnostic"
    )
    assert (
        report["summary"]["api_key=***REDACTED*** [duplicate 2]"]
        == "second redacted-key diagnostic"
    )
    assert "ExplodingDiagnosticKey" not in rendered_report
    assert "client_secret" not in rendered_report
    assert "writeback-collision" not in rendered_report


def test_verify_writeback_confirms_remote_story_matches_expected_fields() -> None:
    client = FakeWritebackClient(
        story_state="-7",
        ai_status="Ready for Testing",
        build_reference="build-20260513-001",
        candidate_artifact="artifacts/STRY0010013.json",
    )

    result = verify_writeback(
        client,
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        artifact_url="artifacts/STRY0010013.json",
    )

    assert result.verified is True
    assert result.story_number == "STRY0010013"
    assert result.expected_state == "-7"
    assert result.actual_fields["state"] == "-7"
    assert result.actual_fields["u_ai_status"] == "Ready for Testing"
    assert result.reasons == []


def test_verify_writeback_compares_against_sanitized_structured_fields() -> None:
    client = FakeWritebackClient(
        story_state="-7",
        ai_status="Ready for Testing",
        build_reference="build-20260513-001 client_secret=***REDACTED***",
        candidate_artifact=(
            "https://artifacts.example.gov/STRY0010013.json?api_key=***REDACTED***"
        ),
    )

    result = verify_writeback(
        client,
        story_number="STRY0010013",
        build_reference="build-20260513-001\nclient_secret=reference-secret",
        artifact_url="https://artifacts.example.gov/STRY0010013.json?api_key=artifact-secret",
    )

    assert result.verified is True
    assert result.reasons == []


def test_verify_writeback_reports_field_mismatches_without_mutation() -> None:
    client = FakeWritebackClient(
        story_state="Ready",
        ai_status="Build Complete",
        build_reference="older-build",
        candidate_artifact="artifacts/old.json",
    )

    result = verify_writeback(
        client,
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        artifact_url="artifacts/STRY0010013.json",
    )

    assert result.verified is False
    assert "state_mismatch" in result.reasons
    assert "u_ai_status_mismatch" in result.reasons
    assert "u_ai_build_reference_mismatch" in result.reasons
    assert "u_ai_candidate_artifact_mismatch" in result.reasons
    assert client.updated_fields == []


def test_verify_writeback_redacts_actual_field_diagnostics_without_changing_mismatch() -> None:
    client = FakeWritebackClient(
        story_state="Ready\nclient_secret=state-secret",
        ai_status="Build Complete\napi_key=status-secret",
        build_reference="older-build\nclient_secret=reference-secret",
        candidate_artifact=(
            "https://artifacts.example.gov/old.json?api_key=artifact-secret"
        ),
    )

    result = verify_writeback(
        client,
        story_number="STRY0010013",
        build_reference="build-20260513-001",
        artifact_url="artifacts/STRY0010013.json",
    )

    assert result.verified is False
    assert "state_mismatch" in result.reasons
    assert "u_ai_status_mismatch" in result.reasons
    assert "u_ai_build_reference_mismatch" in result.reasons
    assert "u_ai_candidate_artifact_mismatch" in result.reasons
    rendered_actual_fields = repr(result.actual_fields)
    assert "state-secret" not in rendered_actual_fields
    assert "status-secret" not in rendered_actual_fields
    assert "reference-secret" not in rendered_actual_fields
    assert "artifact-secret" not in rendered_actual_fields
    assert "client_secret=***REDACTED***" in rendered_actual_fields
    assert "api_key=***REDACTED***" in rendered_actual_fields
    assert "\n" not in rendered_actual_fields
    assert client.updated_fields == []
