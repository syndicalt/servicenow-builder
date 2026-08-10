from typing import Any

from jedi_devproject.bootstrap import (
    apply_bootstrap_fields,
    apply_lifecycle_webhook_records,
    apply_update_set_importer_records,
    build_lifecycle_business_rule_spec,
    build_lifecycle_webhook_bootstrap_spec,
    build_update_set_importer_bootstrap_spec,
    lifecycle_webhook_servicenow_record_plan,
    plan_bootstrap_fields,
    update_set_importer_servicenow_record_plan,
    verify_update_set_importer_records,
)
from jedi_devproject.bootstrap_lifecycle import (
    LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC,
)
from jedi_devproject.bootstrap_update_set_importer import (
    UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC,
)
from jedi_devproject.servicenow import StoryDictionaryField


class FakeBootstrapClient:
    def __init__(self, fields: list[StoryDictionaryField]) -> None:
        self.fields = fields
        self.created_fields: list[dict[str, object]] = []
        self.upserted_records: list[dict[str, Any]] = []

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        return self.fields

    def create_story_dictionary_field(
        self,
        *,
        element: str,
        column_label: str,
        internal_type: str,
        max_length: int | None,
        read_only: bool,
    ) -> dict[str, object]:
        self.created_fields.append(
            {
                "element": element,
                "column_label": column_label,
                "internal_type": internal_type,
                "max_length": max_length,
                "read_only": read_only,
            }
        )
        return {"element": element}

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> dict[str, object]:
        self.upserted_records.append({"table": table, "lookup": lookup, "fields": fields})
        return {"sys_id": f"{table}-sys-id"}


class SecretBearingBootstrapResponse(dict[str, object]):
    def __bool__(self) -> bool:
        raise AssertionError("client_secret=bootstrap-response-bool-secret")

    def __len__(self) -> int:
        raise AssertionError("client_secret=bootstrap-response-len-secret")


class FakeLifecycleWebhookClient:
    def __init__(self) -> None:
        self.upserts: list[dict[str, object]] = []
        self.records: dict[str, dict[str, object]] = {}

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> dict[str, object]:
        self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
        existing = self.fetch_table_record(table=table, lookup=lookup)
        if existing is not None:
            existing.update(fields)
            return {"sys_id": existing.get("sys_id", f"{table}-sys-id")}
        sys_id = f"{table}-sys-id"
        self.records[f"{table}:{lookup}"] = {**fields, "sys_id": sys_id}
        return {"sys_id": sys_id}

    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, object] | None:
        return self.records.get(f"{table}:{lookup}")


class SecretBearingImporterSysId:
    def __str__(self) -> str:
        return "client_secret=importer-secret"


class SecretBearingImporterSysIdText(str):
    pass


class SecretBearingImporterResponse(dict[str, object]):
    def get(self, key: object, default: object = None) -> object:
        raise AssertionError("client_secret=importer-response-get-secret")


class SecretBearingLifecycleSysId:
    def __str__(self) -> str:
        return "client_secret=lifecycle-secret"


class SecretBearingLifecycleSysIdText(str):
    pass


class ExplodingLifecycleVerificationText(str):
    def lower(self) -> str:
        raise RuntimeError("client_secret=lifecycle-verification-lower-secret")

    def __eq__(self, value: object) -> bool:
        raise RuntimeError("client_secret=lifecycle-verification-eq-secret")


class SecretBearingLifecycleResponse(dict[str, object]):
    def get(self, key: object, default: object = None) -> object:
        raise AssertionError("client_secret=lifecycle-response-get-secret")


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
    assert plan.missing_fields == [
        "u_ai_handoff_type",
        "u_ai_handoff_reference",
        "u_ai_artifact_reference",
    ]
    assert [field.element for field in plan.fields_to_create] == [
        "u_ai_handoff_type",
        "u_ai_handoff_reference",
        "u_ai_artifact_reference",
    ]
    assert all(field.read_only is False for field in plan.fields_to_create)
    assert plan.fields_to_update_writable == []
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
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_type",
                column_label="AI Handoff Type",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_reference",
                column_label="AI Handoff Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_artifact_reference",
                column_label="AI Artifact Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
        ]
    )

    assert plan.missing_fields == []
    assert plan.fields_to_create == []
    assert plan.fields_to_update_writable == []
    assert plan.ready is True


def test_bootstrap_plan_rejects_dictionary_field_collection_subclass_without_leak() -> None:
    class SecretBearingFields(list[StoryDictionaryField]):
        def __iter__(self):  # type: ignore[no-untyped-def]
            raise AssertionError("client_secret=bootstrap-fields-iter-secret")

    fields = SecretBearingFields(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
            )
        ]
    )

    try:
        plan_bootstrap_fields(fields)
    except ValueError as exc:
        diagnostic = str(exc)
    else:
        raise AssertionError("bootstrap dictionary field collection subclass was accepted")

    assert diagnostic == "bootstrap dictionary fields contain non-JSON value"
    assert "SecretBearingFields" not in diagnostic
    assert "bootstrap-fields-iter-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_bootstrap_plan_rejects_dictionary_field_item_subclass_without_leak() -> None:
    class SecretBearingField(StoryDictionaryField):
        def secret_marker(self) -> str:
            return "client_secret=bootstrap-field-model-secret"

    fields: list[StoryDictionaryField] = [
        SecretBearingField(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            active=True,
        )
    ]

    try:
        plan_bootstrap_fields(fields)
    except ValueError as exc:
        diagnostic = str(exc)
    else:
        raise AssertionError("bootstrap dictionary field item subclass was accepted")

    assert diagnostic == "bootstrap dictionary fields contain non-JSON value"
    assert "SecretBearingField" not in diagnostic
    assert "bootstrap-field-model-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_apply_bootstrap_fields_requires_explicit_confirmation() -> None:
    client = FakeBootstrapClient([])

    result = apply_bootstrap_fields(
        client,
        confirm_table=None,
        confirm_fields=False,
    )

    assert result.applied is False
    assert result.created_fields == []
    assert result.updated_writable_fields == []
    assert result.reasons == ["bootstrap_confirmation_required"]
    assert client.created_fields == []
    assert client.upserted_records == []


def test_apply_bootstrap_fields_creates_only_missing_custom_fields() -> None:
    client = FakeBootstrapClient(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
                read_only=False,
            )
        ]
    )

    result = apply_bootstrap_fields(
        client,
        confirm_table="rm_story",
        confirm_fields=True,
    )

    assert result.applied is True
    assert result.created_fields == [
        "u_ai_handoff_type",
        "u_ai_handoff_reference",
        "u_ai_artifact_reference",
    ]
    assert [field["element"] for field in client.created_fields] == [
        "u_ai_handoff_type",
        "u_ai_handoff_reference",
        "u_ai_artifact_reference",
    ]
    assert all(field["read_only"] is False for field in client.created_fields)
    assert result.updated_writable_fields == []
    assert result.platform_readonly_records == [
        "sys_ui_policy:Jedi DevProject read-only automation metadata",
    ]
    assert [record["table"] for record in client.upserted_records] == ["sys_ui_policy"]
    assert client.upserted_records[0]["fields"]["table"] == "rm_story"
    assert client.upserted_records[0]["fields"]["active"] == "true"
    assert client.upserted_records[0]["fields"]["global"] == "true"
    assert client.upserted_records[0]["fields"]["run_scripts"] == "true"
    assert "g_form.setReadOnly('u_ai_status', true);" in str(
        client.upserted_records[0]["fields"]["script_true"]
    )
    assert "g_form.setReadOnly('u_ai_artifact_reference', true);" in str(
        client.upserted_records[0]["fields"]["script_true"]
    )
    assert "state" not in result.created_fields
    assert result.form_layout_changes == []


def test_apply_bootstrap_fields_rejects_create_field_response_subclass_without_leak() -> None:
    class UnsafeCreateResponseClient(FakeBootstrapClient):
        def create_story_dictionary_field(
            self,
            *,
            element: str,
            column_label: str,
            internal_type: str,
            max_length: int | None,
            read_only: bool,
        ) -> dict[str, object]:
            super().create_story_dictionary_field(
                element=element,
                column_label=column_label,
                internal_type=internal_type,
                max_length=max_length,
                read_only=read_only,
            )
            return SecretBearingBootstrapResponse({"element": element})

    client = UnsafeCreateResponseClient([])

    try:
        apply_bootstrap_fields(client, confirm_table="rm_story", confirm_fields=True)
    except ValueError as exc:
        diagnostic = str(exc)
    else:
        raise AssertionError("bootstrap create field response subclass was accepted")

    assert diagnostic == "bootstrap create field result is unsafe"
    assert "SecretBearingBootstrapResponse" not in diagnostic
    assert "bootstrap-response-bool-secret" not in diagnostic
    assert "bootstrap-response-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_apply_bootstrap_fields_rejects_dictionary_upsert_response_subclass_without_leak() -> None:
    class UnsafeDictionaryUpsertResponseClient(FakeBootstrapClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            super().upsert_table_record(table=table, lookup=lookup, fields=fields)
            return SecretBearingBootstrapResponse({"sys_id": f"{table}-sys-id"})

    client = UnsafeDictionaryUpsertResponseClient(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
                read_only=True,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_type",
                column_label="AI Handoff Type",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_reference",
                column_label="AI Handoff Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_artifact_reference",
                column_label="AI Artifact Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
        ]
    )

    try:
        apply_bootstrap_fields(client, confirm_table="rm_story", confirm_fields=True)
    except ValueError as exc:
        diagnostic = str(exc)
    else:
        raise AssertionError("bootstrap dictionary upsert response subclass was accepted")

    assert diagnostic == "bootstrap table upsert result is unsafe"
    assert "SecretBearingBootstrapResponse" not in diagnostic
    assert "bootstrap-response-bool-secret" not in diagnostic
    assert "bootstrap-response-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_apply_bootstrap_fields_adds_platform_readonly_policy() -> None:
    client = FakeBootstrapClient(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_type",
                column_label="AI Handoff Type",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_reference",
                column_label="AI Handoff Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_artifact_reference",
                column_label="AI Artifact Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
        ]
    )

    result = apply_bootstrap_fields(
        client,
        confirm_table="rm_story",
        confirm_fields=True,
    )

    assert result.applied is True
    assert result.created_fields == []
    assert result.updated_writable_fields == []
    assert client.created_fields == []
    assert result.platform_readonly_records == [
        "sys_ui_policy:Jedi DevProject read-only automation metadata",
    ]
    assert [record["table"] for record in client.upserted_records] == ["sys_ui_policy"]


def test_apply_bootstrap_fields_rejects_platform_policy_response_subclass_without_leak() -> None:
    class UnsafePlatformPolicyResponseClient(FakeBootstrapClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            super().upsert_table_record(table=table, lookup=lookup, fields=fields)
            return SecretBearingBootstrapResponse({"sys_id": f"{table}-sys-id"})

    client = UnsafePlatformPolicyResponseClient(
        [
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_type",
                column_label="AI Handoff Type",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_handoff_reference",
                column_label="AI Handoff Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
            StoryDictionaryField(
                element="u_ai_artifact_reference",
                column_label="AI Artifact Reference",
                internal_type="string",
                active=True,
                read_only=False,
            ),
        ]
    )

    try:
        apply_bootstrap_fields(client, confirm_table="rm_story", confirm_fields=True)
    except ValueError as exc:
        diagnostic = str(exc)
    else:
        raise AssertionError("bootstrap platform policy response subclass was accepted")

    assert diagnostic == "bootstrap table upsert result is unsafe"
    assert "SecretBearingBootstrapResponse" not in diagnostic
    assert "bootstrap-response-bool-secret" not in diagnostic
    assert "bootstrap-response-len-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_lifecycle_business_rule_spec_emits_ready_and_complete_events() -> None:
    spec = build_lifecycle_business_rule_spec(
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
        ready_for_testing_state_value="-7",
        complete_state_value="3",
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
    assert "previous.state == '-7'" in spec.condition
    assert "current.state == '3'" in spec.condition
    assert "(previous.state == '-7' && current.state == '1')" in spec.condition
    assert "(previous.state == '-7' && current.state == '-6')" in spec.condition
    assert "story_state_changed" in spec.script
    assert "servicenow-business-rule" in spec.script
    assert "jedi-devproject-lifecycle-integration" in spec.script
    assert "Jedi DevProject Lifecycle Event API" in spec.script
    assert "post_event" in spec.script
    assert "previousStateLabel" in spec.script
    assert "currentStateLabel" in spec.script
    assert "Ready for Testing" in spec.script
    assert "Complete" in spec.script
    assert "currentStateLabel = 'Ready'" in spec.script
    assert "currentStateLabel = 'Draft'" in spec.script
    assert "https://sidecar.example.gov/lifecycle/events" not in spec.script
    assert "current.number.toString()" in spec.script
    assert "story_sys_id: current.getUniqueValue()" in spec.script


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
    assert spec.rest_message.authentication == "no_authentication"
    assert spec.business_rule.table == "rm_story"
    assert "new sn_ws.RESTMessageV2(" in spec.business_rule.script
    assert "'Jedi DevProject Lifecycle Event API'" in spec.business_rule.script
    assert "'post_event'" in spec.business_rule.script
    assert "story_sys_id: current.getUniqueValue()" in spec.business_rule.script


def test_lifecycle_webhook_bootstrap_spec_can_emit_hmac_signed_requests() -> None:
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
        hmac_secret_property_name="x_jedi.lifecycle.webhook.secret",
    )

    script = spec.business_rule.script
    assert "gs.getProperty('x_jedi.lifecycle.webhook.secret')" in script
    assert "new GlideCertificateEncryption()" in script
    assert "GlideStringUtil.base64Encode(webhookSecret)" in script
    assert "generateMac(encodedSecret, 'HmacSHA256', signatureBase)" in script
    assert "request.setRequestHeader('X-JEDI-Webhook-Timestamp', timestamp)" in script
    assert "request.setRequestHeader('X-JEDI-Webhook-Signature', 'sha256-base64=' + mac)" in script
    assert "webhook-secret" not in script
    assert spec.hmac_secret_property_name == "x_jedi.lifecycle.webhook.secret"


def test_lifecycle_webhook_bootstrap_spec_requires_reviewed_endpoint() -> None:
    import pytest

    with pytest.raises(ValueError, match="endpoint_url must use https"):
        build_lifecycle_webhook_bootstrap_spec(
            endpoint_url="http://sidecar.example.gov/lifecycle/events",
            integration_identity="jedi-devproject-lifecycle-integration",
            draft_state_value="-6",
            ready_state_value="1",
        )


def test_lifecycle_webhook_servicenow_record_plan_has_explicit_tables() -> None:
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    plan = lifecycle_webhook_servicenow_record_plan(spec)

    assert [record["table"] for record in plan] == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert plan[0]["operation"] == "insert_or_update"
    assert plan[0]["lookup"] == {"name": "Jedi DevProject Lifecycle Event API"}
    assert plan[0]["fields"]["rest_endpoint"] == "https://sidecar.example.gov/lifecycle/events"
    assert plan[0]["fields"]["authentication_type"] == "no_authentication"
    assert plan[1]["lookup"] == {
        "rest_message_name": "Jedi DevProject Lifecycle Event API",
        "function_name": "post_event",
    }
    assert plan[1]["fields"]["rest_endpoint"] == "https://sidecar.example.gov/lifecycle/events"
    assert plan[1]["fields"]["http_method"] == "post"
    assert "content_type" not in plan[1]["fields"]
    assert plan[2]["lookup"] == {
        "name": "Jedi DevProject lifecycle event emitter",
        "collection": "rm_story",
    }
    assert plan[2]["fields"]["when"] == "after"
    assert plan[2]["fields"]["action_update"] is True
    assert "story_state_changed" in str(plan[2]["fields"]["script"])
    assert "story_sys_id: current.getUniqueValue()" in str(plan[2]["fields"]["script"])


def test_apply_lifecycle_webhook_records_requires_confirmation() -> None:
    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    result = apply_lifecycle_webhook_records(
        client,
        spec=spec,
        confirm_table=None,
        confirm_records=False,
    )

    assert result.applied is False
    assert result.upserted_records == []
    assert result.reasons == ["lifecycle_webhook_confirmation_required"]
    assert client.upserts == []


def test_apply_lifecycle_webhook_records_upserts_planned_records() -> None:
    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    result = apply_lifecycle_webhook_records(
        client,
        spec=spec,
        confirm_table="rm_story",
        confirm_records=True,
    )

    assert result.applied is True
    assert result.reasons == []
    assert [record["table"] for record in result.upserted_records] == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert client.upserts[1]["lookup"] == {
        "rest_message": "sys_rest_message-sys-id",
        "function_name": "post_event",
    }
    method_fields = client.upserts[1]["fields"]
    assert isinstance(method_fields, dict)
    assert method_fields["rest_message"] == "sys_rest_message-sys-id"
    assert method_fields["rest_endpoint"] == ("https://sidecar.example.gov/lifecycle/events")


def test_apply_lifecycle_webhook_records_rejects_non_json_rest_message_lookup() -> None:
    import pytest

    class CorruptRestMessageLookupClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_rest_message":
                return {"sys_id": SecretBearingLifecycleSysId()}
            msg = "REST method upsert must not run after corrupt REST message lookup"
            raise AssertionError(msg)

    client = CorruptRestMessageLookupClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    with pytest.raises(ValueError) as error:
        apply_lifecycle_webhook_records(
            client,
            spec=spec,
            confirm_table="rm_story",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "lifecycle-secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == ["sys_rest_message"]


def test_apply_lifecycle_webhook_records_rejects_rest_message_response_subclass() -> None:
    import pytest

    class CorruptRestMessageResponseClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_rest_message":
                return SecretBearingLifecycleResponse({"sys_id": "rest-message-sys-id"})
            msg = "REST method upsert must not run after corrupt REST message response"
            raise AssertionError(msg)

    client = CorruptRestMessageResponseClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    with pytest.raises(ValueError) as error:
        apply_lifecycle_webhook_records(
            client,
            spec=spec,
            confirm_table="rm_story",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleResponse" not in diagnostic
    assert "lifecycle-response-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == ["sys_rest_message"]


def test_apply_lifecycle_webhook_records_rejects_string_subclass_rest_message_lookup() -> None:
    import pytest

    class CorruptRestMessageLookupClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_rest_message":
                return {
                    "sys_id": SecretBearingLifecycleSysIdText(
                        "client_secret=lifecycle-subclass-secret"
                    )
                }
            msg = "REST method upsert must not run after corrupt REST message lookup"
            raise AssertionError(msg)

    client = CorruptRestMessageLookupClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    with pytest.raises(ValueError) as error:
        apply_lifecycle_webhook_records(
            client,
            spec=spec,
            confirm_table="rm_story",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleSysIdText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "lifecycle-subclass-secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == ["sys_rest_message"]


def test_apply_lifecycle_webhook_records_rejects_non_json_method_result() -> None:
    import pytest

    class CorruptMethodResultClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_rest_message":
                return {"sys_id": "sys_rest_message-sys-id"}
            if table == "sys_rest_message_fn":
                return {"sys_id": SecretBearingLifecycleSysId()}
            msg = "Business Rule upsert must not run after corrupt REST method result"
            raise AssertionError(msg)

    client = CorruptMethodResultClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    with pytest.raises(ValueError) as error:
        apply_lifecycle_webhook_records(
            client,
            spec=spec,
            confirm_table="rm_story",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "lifecycle-secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_rest_message",
        "sys_rest_message_fn",
    ]


def test_apply_lifecycle_webhook_records_rejects_method_response_subclass_without_leak() -> None:
    import pytest

    class CorruptMethodResponseClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_rest_message":
                return {"sys_id": "rest-message-sys-id"}
            if table == "sys_rest_message_fn":
                return SecretBearingLifecycleResponse({"sys_id": "method-sys-id"})
            msg = "Business Rule upsert must not run after corrupt REST method response"
            raise AssertionError(msg)

    client = CorruptMethodResponseClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    with pytest.raises(ValueError) as error:
        apply_lifecycle_webhook_records(
            client,
            spec=spec,
            confirm_table="rm_story",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleResponse" not in diagnostic
    assert "lifecycle-response-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_rest_message",
        "sys_rest_message_fn",
    ]


def test_verify_lifecycle_webhook_records_confirms_matching_records() -> None:
    from jedi_devproject.bootstrap import verify_lifecycle_webhook_records

    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )
    apply_lifecycle_webhook_records(
        client,
        spec=spec,
        confirm_table="rm_story",
        confirm_records=True,
    )
    script_key = (
        "sys_script:{'name': 'Jedi DevProject lifecycle event emitter', 'collection': 'rm_story'}"
    )
    client.records[script_key]["action_update"] = "true"
    client.records[script_key]["active"] = "true"
    method_key = (
        "sys_rest_message_fn:{'rest_message': 'sys_rest_message-sys-id', "
        "'function_name': 'post_event'}"
    )
    client.records[method_key]["rest_message"] = {
        "link": "https://example.service-now.com/api/now/table/sys_rest_message/sys_rest_message-sys-id",
        "value": "sys_rest_message-sys-id",
    }

    result = verify_lifecycle_webhook_records(client, spec=spec)

    assert result.verified is True
    assert result.matched_records == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert result.missing_records == []
    assert result.mismatched_fields == {}
    assert result.reasons == []


def test_verify_lifecycle_webhook_records_rejects_string_subclass_rest_message_lookup() -> None:
    import pytest

    from jedi_devproject.bootstrap import verify_lifecycle_webhook_records

    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )
    plan = lifecycle_webhook_servicenow_record_plan(spec)
    client.records[f"{plan[0]['table']}:{plan[0]['lookup']}"] = {
        **plan[0]["fields"],
        "sys_id": SecretBearingLifecycleSysIdText("client_secret=lifecycle-subclass-secret"),
    }

    with pytest.raises(ValueError) as error:
        verify_lifecycle_webhook_records(client, spec=spec)

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleSysIdText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "lifecycle-subclass-secret" not in diagnostic


def test_verify_lifecycle_webhook_records_rejects_rest_message_record_subclass() -> None:
    import pytest

    from jedi_devproject.bootstrap import verify_lifecycle_webhook_records

    class CorruptRestMessageRecordClient(FakeLifecycleWebhookClient):
        def fetch_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
        ) -> dict[str, object] | None:
            if table == "sys_rest_message":
                return SecretBearingLifecycleResponse({"sys_id": "rest-message-sys-id"})
            return super().fetch_table_record(table=table, lookup=lookup)

    client = CorruptRestMessageRecordClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )

    with pytest.raises(ValueError) as error:
        verify_lifecycle_webhook_records(client, spec=spec)

    diagnostic = str(error.value)
    assert diagnostic == LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingLifecycleResponse" not in diagnostic
    assert "lifecycle-response-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_verify_lifecycle_webhook_records_reports_missing_and_mismatched_records() -> None:
    from jedi_devproject.bootstrap import verify_lifecycle_webhook_records

    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )
    plan = lifecycle_webhook_servicenow_record_plan(spec)
    client.records[f"{plan[0]['table']}:{plan[0]['lookup']}"] = {
        **plan[0]["fields"],
        "rest_endpoint": "https://wrong.example.gov/lifecycle/events",
        "sys_id": "sys_rest_message-sys-id",
    }

    result = verify_lifecycle_webhook_records(client, spec=spec)

    assert result.verified is False
    assert result.missing_records == ["sys_rest_message_fn", "sys_script"]
    assert result.mismatched_fields == {
        "sys_rest_message": ["rest_endpoint"],
    }
    assert "record_missing" in result.reasons
    assert "field_mismatch" in result.reasons


def test_verify_lifecycle_webhook_records_rejects_string_subclass_boolean_metadata() -> None:
    from jedi_devproject.bootstrap import verify_lifecycle_webhook_records

    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )
    apply_lifecycle_webhook_records(
        client,
        spec=spec,
        confirm_table="rm_story",
        confirm_records=True,
    )
    script_key = (
        "sys_script:{'name': 'Jedi DevProject lifecycle event emitter', 'collection': 'rm_story'}"
    )
    client.records[script_key]["action_update"] = ExplodingLifecycleVerificationText("true")
    client.records[script_key]["active"] = "true"

    result = verify_lifecycle_webhook_records(client, spec=spec)

    assert result.verified is False
    assert result.mismatched_fields == {"sys_script": ["action_update"]}
    assert "field_mismatch" in result.reasons


def test_verify_lifecycle_webhook_records_rejects_string_subclass_reference_metadata() -> None:
    from jedi_devproject.bootstrap import verify_lifecycle_webhook_records

    client = FakeLifecycleWebhookClient()
    spec = build_lifecycle_webhook_bootstrap_spec(
        endpoint_url="https://sidecar.example.gov/lifecycle/events",
        integration_identity="jedi-devproject-lifecycle-integration",
        draft_state_value="-6",
        ready_state_value="1",
    )
    apply_lifecycle_webhook_records(
        client,
        spec=spec,
        confirm_table="rm_story",
        confirm_records=True,
    )
    script_key = (
        "sys_script:{'name': 'Jedi DevProject lifecycle event emitter', 'collection': 'rm_story'}"
    )
    client.records[script_key]["action_update"] = "true"
    client.records[script_key]["active"] = "true"
    method_key = (
        "sys_rest_message_fn:{'rest_message': 'sys_rest_message-sys-id', "
        "'function_name': 'post_event'}"
    )
    client.records[method_key]["rest_message"] = {
        "value": ExplodingLifecycleVerificationText("sys_rest_message-sys-id"),
    }

    result = verify_lifecycle_webhook_records(client, spec=spec)

    assert result.verified is False
    assert result.mismatched_fields == {"sys_rest_message_fn": ["rest_message"]}
    assert "field_mismatch" in result.reasons


def test_update_set_importer_bootstrap_spec_defines_scripted_rest_api() -> None:
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    assert spec.definition.name == "Jedi DevProject Update Set Import API"
    assert spec.definition.service_id == "jedi_update_set_import"
    assert spec.definition.active is True
    assert spec.operation.name == "import_update_set_xml"
    assert spec.operation.http_method == "POST"
    assert spec.operation.requires_authentication is True
    assert spec.operation.requires_acl_authorization is True
    assert "GlideUpdateManager2" in spec.operation.operation_script
    assert "loadXML(xmlPayload)" in spec.operation.operation_script
    assert "update_set_xml" in spec.operation.operation_script
    assert "replace(/^<\\?xml[^>]*>/, '')" in spec.operation.operation_script
    assert "jedi-devproject-update-set-importer" in spec.operation.operation_script


def test_update_set_importer_servicenow_record_plan_has_explicit_tables() -> None:
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    plan = update_set_importer_servicenow_record_plan(spec)

    assert [record["table"] for record in plan] == [
        "sys_ws_definition",
        "sys_ws_operation",
    ]
    assert plan[0]["lookup"] == {"service_id": "jedi_update_set_import"}
    assert "base_uri" not in plan[0]["fields"]
    assert plan[0]["fields"]["consumes"] == "application/json"
    assert plan[1]["lookup"] == {
        "web_service_definition_name": "Jedi DevProject Update Set Import API",
        "name": "import_update_set_xml",
    }
    assert plan[1]["fields"]["http_method"] == "POST"
    assert plan[1]["fields"]["requires_authentication"] is True
    assert plan[1]["fields"]["requires_acl_authorization"] is True
    assert "web_service_definition" not in plan[1]["fields"]


def test_apply_update_set_importer_records_requires_confirmation() -> None:
    client = FakeLifecycleWebhookClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    result = apply_update_set_importer_records(
        client,
        spec=spec,
        confirm_service_id=None,
        confirm_records=False,
    )

    assert result.applied is False
    assert result.upserted_records == []
    assert result.reasons == ["update_set_importer_confirmation_required"]
    assert client.upserts == []


def test_apply_update_set_importer_records_upserts_definition_then_operation() -> None:
    client = FakeLifecycleWebhookClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    result = apply_update_set_importer_records(
        client,
        spec=spec,
        confirm_service_id="jedi_update_set_import",
        confirm_records=True,
    )

    assert result.applied is True
    assert result.reasons == []
    assert [record["table"] for record in result.upserted_records] == [
        "sys_ws_definition",
        "sys_ws_operation",
    ]
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_ws_definition",
        "sys_ws_operation",
    ]
    assert client.upserts[1]["lookup"] == {
        "web_service_definition": "sys_ws_definition-sys-id",
        "name": "import_update_set_xml",
    }
    operation_fields = client.upserts[1]["fields"]
    assert isinstance(operation_fields, dict)
    assert operation_fields["web_service_definition"] == "sys_ws_definition-sys-id"


def test_apply_update_set_importer_records_rejects_non_json_definition_lookup() -> None:
    import pytest

    class CorruptDefinitionLookupClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_ws_definition":
                return {"sys_id": SecretBearingImporterSysId()}
            msg = "operation upsert must not run after corrupt definition lookup"
            raise AssertionError(msg)

    client = CorruptDefinitionLookupClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    with pytest.raises(ValueError) as error:
        apply_update_set_importer_records(
            client,
            spec=spec,
            confirm_service_id="jedi_update_set_import",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "importer-secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == ["sys_ws_definition"]


def test_apply_update_set_importer_records_rejects_definition_response_subclass() -> None:
    import pytest

    class CorruptDefinitionResponseClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_ws_definition":
                return SecretBearingImporterResponse({"sys_id": "definition-sys-id"})
            msg = "operation upsert must not run after corrupt definition response"
            raise AssertionError(msg)

    client = CorruptDefinitionResponseClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    with pytest.raises(ValueError) as error:
        apply_update_set_importer_records(
            client,
            spec=spec,
            confirm_service_id="jedi_update_set_import",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterResponse" not in diagnostic
    assert "importer-response-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == ["sys_ws_definition"]


def test_apply_update_set_importer_records_rejects_non_json_operation_result() -> None:
    import pytest

    class CorruptOperationResultClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_ws_definition":
                return {"sys_id": "sys_ws_definition-sys-id"}
            return {"sys_id": SecretBearingImporterSysId()}

    client = CorruptOperationResultClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    with pytest.raises(ValueError) as error:
        apply_update_set_importer_records(
            client,
            spec=spec,
            confirm_service_id="jedi_update_set_import",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterSysId" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "importer-secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_ws_definition",
        "sys_ws_operation",
    ]


def test_apply_update_set_importer_records_rejects_operation_response_subclass() -> None:
    import pytest

    class CorruptOperationResponseClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_ws_definition":
                return {"sys_id": "sys_ws_definition-sys-id"}
            return SecretBearingImporterResponse({"sys_id": "operation-sys-id"})

    client = CorruptOperationResponseClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    with pytest.raises(ValueError) as error:
        apply_update_set_importer_records(
            client,
            spec=spec,
            confirm_service_id="jedi_update_set_import",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterResponse" not in diagnostic
    assert "importer-response-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == [
        "sys_ws_definition",
        "sys_ws_operation",
    ]


def test_apply_update_set_importer_records_rejects_string_subclass_definition_lookup() -> None:
    import pytest

    class CorruptDefinitionLookupClient(FakeLifecycleWebhookClient):
        def upsert_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
            fields: dict[str, object],
        ) -> dict[str, object]:
            self.upserts.append({"table": table, "lookup": lookup, "fields": fields})
            if table == "sys_ws_definition":
                return {
                    "sys_id": SecretBearingImporterSysIdText(
                        "client_secret=importer-subclass-secret"
                    )
                }
            msg = "operation upsert must not run after corrupt definition lookup"
            raise AssertionError(msg)

    client = CorruptDefinitionLookupClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    with pytest.raises(ValueError) as error:
        apply_update_set_importer_records(
            client,
            spec=spec,
            confirm_service_id="jedi_update_set_import",
            confirm_records=True,
        )

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterSysIdText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "importer-subclass-secret" not in diagnostic
    assert [upsert["table"] for upsert in client.upserts] == ["sys_ws_definition"]


def test_verify_update_set_importer_records_rejects_string_subclass_definition_lookup() -> None:
    import pytest

    client = FakeLifecycleWebhookClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )
    definition_key = "sys_ws_definition:{'service_id': 'jedi_update_set_import'}"
    client.records[definition_key] = {
        "sys_id": SecretBearingImporterSysIdText("client_secret=verify-importer-subclass"),
        "name": spec.definition.name,
        "service_id": spec.definition.service_id,
        "active": spec.definition.active,
        "consumes": spec.definition.consumes,
        "produces": spec.definition.produces,
        "short_description": spec.definition.short_description,
    }

    with pytest.raises(ValueError) as error:
        verify_update_set_importer_records(client, spec=spec)

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterSysIdText" not in diagnostic
    assert "client_secret" not in diagnostic
    assert "verify-importer-subclass" not in diagnostic


def test_verify_update_set_importer_records_rejects_definition_record_subclass() -> None:
    import pytest

    class CorruptDefinitionRecordClient(FakeLifecycleWebhookClient):
        def fetch_table_record(
            self,
            *,
            table: str,
            lookup: dict[str, str],
        ) -> dict[str, object] | None:
            if table == "sys_ws_definition":
                return SecretBearingImporterResponse({"sys_id": "definition-sys-id"})
            return super().fetch_table_record(table=table, lookup=lookup)

    client = CorruptDefinitionRecordClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )

    with pytest.raises(ValueError) as error:
        verify_update_set_importer_records(client, spec=spec)

    diagnostic = str(error.value)
    assert diagnostic == UPDATE_SET_IMPORTER_LOOKUP_NON_JSON_DIAGNOSTIC
    assert "SecretBearingImporterResponse" not in diagnostic
    assert "importer-response-get-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_verify_update_set_importer_records_confirms_matching_records() -> None:
    client = FakeLifecycleWebhookClient()
    spec = build_update_set_importer_bootstrap_spec(
        integration_identity="jedi-devproject-update-set-importer"
    )
    apply_update_set_importer_records(
        client,
        spec=spec,
        confirm_service_id="jedi_update_set_import",
        confirm_records=True,
    )
    operation_key = (
        "sys_ws_operation:{'web_service_definition': 'sys_ws_definition-sys-id', "
        "'name': 'import_update_set_xml'}"
    )
    client.records[operation_key]["requires_authentication"] = "true"
    client.records[operation_key]["requires_acl_authorization"] = "true"
    client.records[operation_key]["active"] = "true"
    client.records[operation_key]["web_service_definition"] = {"value": "sys_ws_definition-sys-id"}

    result = verify_update_set_importer_records(client, spec=spec)

    assert result.verified is True
    assert result.matched_records == ["sys_ws_definition", "sys_ws_operation"]
    assert result.missing_records == []
    assert result.mismatched_fields == {}
    assert result.reasons == []
