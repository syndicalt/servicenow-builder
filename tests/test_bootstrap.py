from jedi_devproject.bootstrap import (
    apply_bootstrap_fields,
    build_lifecycle_business_rule_spec,
    build_lifecycle_webhook_bootstrap_spec,
    plan_bootstrap_fields,
)
from jedi_devproject.servicenow import StoryDictionaryField


class FakeBootstrapClient:
    def __init__(self, fields: list[StoryDictionaryField]) -> None:
        self.fields = fields
        self.created_fields: list[dict[str, object]] = []

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        return self.fields

    def create_story_dictionary_field(
        self,
        *,
        element: str,
        column_label: str,
        internal_type: str,
        max_length: int | None,
    ) -> dict[str, object]:
        self.created_fields.append(
            {
                "element": element,
                "column_label": column_label,
                "internal_type": internal_type,
                "max_length": max_length,
            }
        )
        return {"element": element}


def test_bootstrap_plan_only_includes_missing_custom_writeback_fields() -> None:
    plan = plan_bootstrap_fields(
        [
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
    )

    assert plan.table == "rm_story"
    assert plan.missing_fields == ["u_ai_build_reference", "u_ai_candidate_artifact"]
    assert [field.element for field in plan.fields_to_create] == [
        "u_ai_build_reference",
        "u_ai_candidate_artifact",
    ]
    assert "state" not in [field.element for field in plan.fields_to_create]
    assert plan.requires_apply_confirmation is True
    assert plan.form_layout_changes == []


def test_bootstrap_plan_is_noop_when_custom_fields_exist() -> None:
    plan = plan_bootstrap_fields(
        [
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
    )

    assert plan.missing_fields == []
    assert plan.fields_to_create == []
    assert plan.ready is True


def test_apply_bootstrap_fields_requires_explicit_confirmation() -> None:
    client = FakeBootstrapClient([])

    result = apply_bootstrap_fields(
        client,
        confirm_table=None,
        confirm_fields=False,
    )

    assert result.applied is False
    assert result.created_fields == []
    assert result.reasons == ["bootstrap_confirmation_required"]
    assert client.created_fields == []


def test_apply_bootstrap_fields_creates_only_missing_custom_fields() -> None:
    client = FakeBootstrapClient(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
            )
        ]
    )

    result = apply_bootstrap_fields(
        client,
        confirm_table="rm_story",
        confirm_fields=True,
    )

    assert result.applied is True
    assert result.created_fields == ["u_ai_build_reference", "u_ai_candidate_artifact"]
    assert [field["element"] for field in client.created_fields] == [
        "u_ai_build_reference",
        "u_ai_candidate_artifact",
    ]
    assert "state" not in result.created_fields
    assert result.form_layout_changes == []


def test_lifecycle_business_rule_spec_emits_draft_to_ready_event_only() -> None:
    spec = build_lifecycle_business_rule_spec(
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
        rest_message_name="Jedi DevProject Lifecycle Event API",
        rest_method_name="post_event",
    )

    assert spec.table == "rm_story"
    assert spec.name == "Jedi DevProject lifecycle event emitter"
    assert spec.when == "after"
    assert spec.action == "update"
    assert spec.active is True
    assert "current.state.changes()" in spec.condition
    assert "previous.state == '-6'" in spec.condition
    assert "current.state == '1'" in spec.condition
    assert "story_state_changed" in spec.script
    assert "servicenow-business-rule" in spec.script
    assert "jedi-devproject-lifecycle-integration" in spec.script
    assert "Jedi DevProject Lifecycle Event API" in spec.script
    assert "post_event" in spec.script
    assert "https://sidecar.example.gov/lifecycle/events" not in spec.script
    assert "current.number.toString()" in spec.script
    assert "current.sys_id" not in spec.script
    assert "story_sys_id" not in spec.model_dump_json()


def test_lifecycle_webhook_bootstrap_spec_includes_rest_message_and_business_rule() -> None:
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    assert spec.rest_message.name == "Jedi DevProject Lifecycle Event API"
    assert spec.rest_message.endpoint_url == "https://sidecar.example.gov/lifecycle/events"
    assert spec.rest_message.http_method == "POST"
    assert spec.rest_message.authentication == "configured_in_servicenow"
    assert spec.business_rule.table == "rm_story"
    assert "new sn_ws.RESTMessageV2(" in spec.business_rule.script
    assert "'Jedi DevProject Lifecycle Event API'" in spec.business_rule.script
    assert "'post_event'" in spec.business_rule.script
    assert "story_sys_id" not in spec.model_dump_json()


def test_lifecycle_webhook_bootstrap_spec_requires_reviewed_endpoint() -> None:
    import pytest

    with pytest.raises(ValueError, match="endpoint_url must use https"):
        build_lifecycle_webhook_bootstrap_spec(
            endpoint_url="http://sidecar.example.gov/lifecycle/events",
            integration_identity="jedi-devproject-lifecycle-integration",
            draft_state_value="-6",
            ready_state_value="1",
        )
