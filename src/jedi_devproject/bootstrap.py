from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel

from jedi_devproject.servicenow import StoryDictionaryField

BOOTSTRAP_TABLE = "rm_story"


class BootstrapFieldSpec(BaseModel):
    element: str
    column_label: str
    internal_type: str
    max_length: int | None = None


class BootstrapFieldPlan(BaseModel):
    table: str
    missing_fields: list[str]
    fields_to_create: list[BootstrapFieldSpec]
    form_layout_changes: list[str]
    requires_apply_confirmation: bool

    @property
    def ready(self) -> bool:
        return not self.missing_fields


class BootstrapApplyResult(BaseModel):
    applied: bool
    created_fields: list[str]
    form_layout_changes: list[str]
    reasons: list[str]


class LifecycleWebhookApplyResult(BaseModel):
    applied: bool
    upserted_records: list[dict[str, Any]]
    reasons: list[str]


class LifecycleWebhookVerificationResult(BaseModel):
    verified: bool
    matched_records: list[str]
    missing_records: list[str]
    mismatched_fields: dict[str, list[str]]
    reasons: list[str]


class LifecycleBusinessRuleSpec(BaseModel):
    name: str
    table: str
    when: str
    action: str
    active: bool
    condition: str
    script: str


class LifecycleRestMessageSpec(BaseModel):
    name: str
    method_name: str
    endpoint_url: str
    http_method: str
    authentication: str
    content_type: str


class LifecycleWebhookBootstrapSpec(BaseModel):
    rest_message: LifecycleRestMessageSpec
    business_rule: LifecycleBusinessRuleSpec


class BootstrapClient(Protocol):
    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        """Fetch active story dictionary fields."""

    def create_story_dictionary_field(
        self,
        *,
        element: str,
        column_label: str,
        internal_type: str,
        max_length: int | None,
    ) -> dict[str, object]:
        """Create a dictionary field on rm_story."""


class LifecycleWebhookClient(Protocol):
    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a ServiceNow table record."""


class LifecycleWebhookReadClient(Protocol):
    def fetch_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
    ) -> dict[str, Any] | None:
        """Fetch one ServiceNow table record by lookup fields."""


REQUIRED_BOOTSTRAP_FIELDS = [
    BootstrapFieldSpec(
        element="u_ai_status",
        column_label="AI Status",
        internal_type="string",
        max_length=80,
    ),
    BootstrapFieldSpec(
        element="u_ai_build_reference",
        column_label="AI Build Reference",
        internal_type="string",
        max_length=255,
    ),
    BootstrapFieldSpec(
        element="u_ai_candidate_artifact",
        column_label="AI Candidate Artifact",
        internal_type="string",
        max_length=1024,
    ),
]


def plan_bootstrap_fields(
    dictionary_fields: list[StoryDictionaryField],
) -> BootstrapFieldPlan:
    existing_fields = {field.element for field in dictionary_fields if field.active}
    fields_to_create = [
        field
        for field in REQUIRED_BOOTSTRAP_FIELDS
        if field.element not in existing_fields
    ]
    return BootstrapFieldPlan(
        table=BOOTSTRAP_TABLE,
        missing_fields=[field.element for field in fields_to_create],
        fields_to_create=fields_to_create,
        form_layout_changes=[],
        requires_apply_confirmation=True,
    )


def apply_bootstrap_fields(
    client: BootstrapClient,
    *,
    confirm_table: str | None,
    confirm_fields: bool,
) -> BootstrapApplyResult:
    if confirm_table != BOOTSTRAP_TABLE or not confirm_fields:
        return BootstrapApplyResult(
            applied=False,
            created_fields=[],
            form_layout_changes=[],
            reasons=["bootstrap_confirmation_required"],
        )

    plan = plan_bootstrap_fields(client.fetch_story_dictionary_fields())
    created_fields: list[str] = []
    for field in plan.fields_to_create:
        client.create_story_dictionary_field(
            element=field.element,
            column_label=field.column_label,
            internal_type=field.internal_type,
            max_length=field.max_length,
        )
        created_fields.append(field.element)

    return BootstrapApplyResult(
        applied=bool(created_fields),
        created_fields=created_fields,
        form_layout_changes=[],
        reasons=[],
    )


def build_lifecycle_business_rule_spec(
    *,
    integration_identity: str,
    draft_state_value: str,
    ready_state_value: str,
    rest_message_name: str = "Jedi DevProject Lifecycle Event API",
    rest_method_name: str = "post_event",
) -> LifecycleBusinessRuleSpec:
    _require_non_empty("integration_identity", integration_identity)
    _require_non_empty("draft_state_value", draft_state_value)
    _require_non_empty("ready_state_value", ready_state_value)
    _require_non_empty("rest_message_name", rest_message_name)
    _require_non_empty("rest_method_name", rest_method_name)

    condition = (
        "current.state.changes() && "
        f"previous.state == {_js_string(draft_state_value)} && "
        f"current.state == {_js_string(ready_state_value)}"
    )
    script = f"""(function executeRule(current, previous) {{
    var request = new sn_ws.RESTMessageV2(
        {_js_string(rest_message_name)},
        {_js_string(rest_method_name)}
    );
    request.setRequestHeader('Content-Type', 'application/json');

    var eventId = [
        current.number.toString(),
        previous.state.toString(),
        current.state.toString(),
        new GlideDateTime().getNumericValue().toString()
    ].join('-');

    var payload = {{
        event_id: eventId,
        event_type: 'story_state_changed',
        source: 'servicenow-business-rule',
        table: 'rm_story',
        story_number: current.number.toString(),
        previous_state: 'Draft',
        current_state: 'Ready',
        occurred_at: new GlideDateTime().getValue(),
        correlation_id: eventId,
        emitted_by: {_js_string(integration_identity)}
    }};

    request.setRequestBody(JSON.stringify(payload));
    request.executeAsync();
}})(current, previous);"""

    return LifecycleBusinessRuleSpec(
        name="Jedi DevProject lifecycle event emitter",
        table=BOOTSTRAP_TABLE,
        when="after",
        action="update",
        active=True,
        condition=condition,
        script=script,
    )


def build_lifecycle_webhook_bootstrap_spec(
    *,
    endpoint_url: str,
    integration_identity: str,
    draft_state_value: str,
    ready_state_value: str,
) -> LifecycleWebhookBootstrapSpec:
    rest_message = build_lifecycle_rest_message_spec(endpoint_url=endpoint_url)
    business_rule = build_lifecycle_business_rule_spec(
        integration_identity=integration_identity,
        draft_state_value=draft_state_value,
        ready_state_value=ready_state_value,
        rest_message_name=rest_message.name,
        rest_method_name=rest_message.method_name,
    )
    return LifecycleWebhookBootstrapSpec(
        rest_message=rest_message,
        business_rule=business_rule,
    )


def build_lifecycle_rest_message_spec(
    *,
    endpoint_url: str,
) -> LifecycleRestMessageSpec:
    if not endpoint_url.startswith("https://"):
        raise ValueError("endpoint_url must use https")
    return LifecycleRestMessageSpec(
        name="Jedi DevProject Lifecycle Event API",
        method_name="post_event",
        endpoint_url=endpoint_url,
        http_method="POST",
        authentication="no_authentication",
        content_type="application/json",
    )


def lifecycle_webhook_servicenow_record_plan(
    spec: LifecycleWebhookBootstrapSpec,
) -> list[dict[str, Any]]:
    return [
        {
            "table": "sys_rest_message",
            "operation": "insert_or_update",
            "lookup": {"name": spec.rest_message.name},
            "fields": {
                "name": spec.rest_message.name,
                "rest_endpoint": spec.rest_message.endpoint_url,
                "authentication_type": spec.rest_message.authentication,
            },
        },
        {
            "table": "sys_rest_message_fn",
            "operation": "insert_or_update",
            "lookup": {
                "rest_message_name": spec.rest_message.name,
                "function_name": spec.rest_message.method_name,
            },
            "fields": {
                "function_name": spec.rest_message.method_name,
                "rest_endpoint": spec.rest_message.endpoint_url,
                "http_method": spec.rest_message.http_method.lower(),
            },
        },
        {
            "table": "sys_script",
            "operation": "insert_or_update",
            "lookup": {
                "name": spec.business_rule.name,
                "collection": spec.business_rule.table,
            },
            "fields": {
                "name": spec.business_rule.name,
                "collection": spec.business_rule.table,
                "when": spec.business_rule.when,
                "action_update": spec.business_rule.action == "update",
                "active": spec.business_rule.active,
                "condition": spec.business_rule.condition,
                "script": spec.business_rule.script,
            },
        },
    ]


def apply_lifecycle_webhook_records(
    client: LifecycleWebhookClient,
    *,
    spec: LifecycleWebhookBootstrapSpec,
    confirm_table: str | None,
    confirm_records: bool,
) -> LifecycleWebhookApplyResult:
    if confirm_table != BOOTSTRAP_TABLE or not confirm_records:
        return LifecycleWebhookApplyResult(
            applied=False,
            upserted_records=[],
            reasons=["lifecycle_webhook_confirmation_required"],
        )

    upserted_records: list[dict[str, Any]] = []
    for record in _servicenow_apply_records(spec, rest_message_sys_id=None):
        result = client.upsert_table_record(
            table=str(record["table"]),
            lookup=record["lookup"],
            fields=record["fields"],
        )
        if record["table"] == "sys_rest_message":
            rest_message_sys_id = str(result.get("sys_id") or "")
            upserted_records.append(
                {
                    "table": record["table"],
                    "lookup": record["lookup"],
                    "sys_id": result.get("sys_id"),
                }
            )
            if rest_message_sys_id:
                for method_record in _servicenow_apply_records(
                    spec,
                    rest_message_sys_id=rest_message_sys_id,
                ):
                    if method_record["table"] != "sys_rest_message_fn":
                        continue
                    method_result = client.upsert_table_record(
                        table=str(method_record["table"]),
                        lookup=method_record["lookup"],
                        fields=method_record["fields"],
                    )
                    upserted_records.append(
                        {
                            "table": method_record["table"],
                            "lookup": method_record["lookup"],
                            "sys_id": method_result.get("sys_id"),
                        }
                    )
            continue
        if record["table"] == "sys_rest_message_fn":
            continue
        upserted_records.append(
            {
                "table": record["table"],
                "lookup": record["lookup"],
                "sys_id": result.get("sys_id"),
            }
        )

    return LifecycleWebhookApplyResult(
        applied=bool(upserted_records),
        upserted_records=upserted_records,
        reasons=[],
    )


def verify_lifecycle_webhook_records(
    client: LifecycleWebhookReadClient,
    *,
    spec: LifecycleWebhookBootstrapSpec,
) -> LifecycleWebhookVerificationResult:
    matched_records: list[str] = []
    missing_records: list[str] = []
    mismatched_fields: dict[str, list[str]] = {}

    for planned_record in _servicenow_verification_records(spec, rest_message_sys_id=None):
        table = str(planned_record["table"])
        actual_record = client.fetch_table_record(
            table=table,
            lookup=planned_record["lookup"],
        )
        if actual_record is None:
            missing_records.append(table)
            continue

        expected_fields = planned_record["fields"]
        mismatches = _mismatched_fields(actual_record, expected_fields)
        if mismatches:
            mismatched_fields[table] = mismatches
        else:
            matched_records.append(table)

        if table != "sys_rest_message":
            continue
        rest_message_sys_id = str(actual_record.get("sys_id") or "")
        if not rest_message_sys_id:
            missing_records.append("sys_rest_message_fn")
            continue
        for method_record in _servicenow_verification_records(
            spec,
            rest_message_sys_id=rest_message_sys_id,
        ):
            actual_method = client.fetch_table_record(
                table=str(method_record["table"]),
                lookup=method_record["lookup"],
            )
            if actual_method is None:
                missing_records.append(str(method_record["table"]))
                continue
            method_mismatches = _mismatched_fields(actual_method, method_record["fields"])
            if method_mismatches:
                mismatched_fields[str(method_record["table"])] = method_mismatches
            else:
                matched_records.append(str(method_record["table"]))

    reasons: list[str] = []
    if missing_records:
        reasons.append("record_missing")
    if mismatched_fields:
        reasons.append("field_mismatch")
    return LifecycleWebhookVerificationResult(
        verified=not reasons,
        matched_records=matched_records,
        missing_records=missing_records,
        mismatched_fields=mismatched_fields,
        reasons=reasons,
    )


def _servicenow_apply_records(
    spec: LifecycleWebhookBootstrapSpec,
    *,
    rest_message_sys_id: str | None,
) -> list[dict[str, Any]]:
    plan = lifecycle_webhook_servicenow_record_plan(spec)
    records: list[dict[str, Any]] = []
    for record in plan:
        if record["table"] != "sys_rest_message_fn":
            records.append(record)
            continue
        if rest_message_sys_id is None:
            continue
        records.append(
            {
                **record,
                "lookup": {
                    "rest_message": rest_message_sys_id,
                    "function_name": spec.rest_message.method_name,
                },
                "fields": {
                    **record["fields"],
                    "rest_message": rest_message_sys_id,
                },
            }
        )
    return records


def _servicenow_verification_records(
    spec: LifecycleWebhookBootstrapSpec,
    *,
    rest_message_sys_id: str | None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for record in lifecycle_webhook_servicenow_record_plan(spec):
        if rest_message_sys_id is None and record["table"] == "sys_rest_message_fn":
            continue
        if rest_message_sys_id is not None and record["table"] != "sys_rest_message_fn":
            continue
        if record["table"] == "sys_rest_message_fn":
            records.append(
                {
                    **record,
                    "lookup": {
                        "rest_message": rest_message_sys_id,
                        "function_name": spec.rest_message.method_name,
                    },
                    "fields": {
                        **record["fields"],
                        "rest_message": rest_message_sys_id,
                    },
                }
            )
        else:
            records.append(record)
    return records


def _mismatched_fields(
    actual_record: dict[str, Any],
    expected_fields: dict[str, Any],
) -> list[str]:
    return [
        field_name
        for field_name, expected_value in expected_fields.items()
        if _normalise_servicenow_value(actual_record.get(field_name))
        != _normalise_servicenow_value(expected_value)
    ]


def _normalise_servicenow_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value["value"]
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower()
    return value


def _require_non_empty(field_name: str, value: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be empty")


def _js_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
