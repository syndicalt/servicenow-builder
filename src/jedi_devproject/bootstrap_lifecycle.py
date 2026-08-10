"""Lifecycle webhook bootstrap: business-rule emitter and REST message plan/apply/verify."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from jedi_devproject.bootstrap_fields import BOOTSTRAP_TABLE

LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC = (
    "Lifecycle webhook lookup contains non-JSON value"
)
_UNSAFE_LIFECYCLE_VERIFICATION_VALUE = object()


class LifecycleWebhookApplyResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    applied: bool
    upserted_records: list[dict[str, Any]]
    reasons: list[str]


class LifecycleWebhookVerificationResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    verified: bool
    matched_records: list[str]
    missing_records: list[str]
    mismatched_fields: dict[str, list[str]]
    reasons: list[str]


class LifecycleBusinessRuleSpec(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    name: str
    table: str
    when: str
    action: str
    active: bool
    condition: str
    script: str


class LifecycleRestMessageSpec(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    name: str
    method_name: str
    endpoint_url: str
    http_method: str
    authentication: str
    content_type: str


class LifecycleWebhookBootstrapSpec(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    rest_message: LifecycleRestMessageSpec
    business_rule: LifecycleBusinessRuleSpec
    hmac_secret_property_name: str | None = None


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


def build_lifecycle_business_rule_spec(
    *,
    integration_identity: str,
    draft_state_value: str,
    ready_state_value: str,
    ready_for_testing_state_value: str | None = None,
    complete_state_value: str | None = None,
    rest_message_name: str = "Jedi DevProject Lifecycle Event API",
    rest_method_name: str = "post_event",
    hmac_secret_property_name: str | None = None,
) -> LifecycleBusinessRuleSpec:
    _require_non_empty("integration_identity", integration_identity)
    _require_non_empty("draft_state_value", draft_state_value)
    _require_non_empty("ready_state_value", ready_state_value)
    _require_non_empty("rest_message_name", rest_message_name)
    _require_non_empty("rest_method_name", rest_method_name)
    if hmac_secret_property_name is not None:
        _require_non_empty("hmac_secret_property_name", hmac_secret_property_name)
    if ready_for_testing_state_value is not None:
        _require_non_empty("ready_for_testing_state_value", ready_for_testing_state_value)
    if complete_state_value is not None:
        _require_non_empty("complete_state_value", complete_state_value)

    transition_conditions = [
        (
            f"(previous.state == {_js_string(draft_state_value)} && "
            f"current.state == {_js_string(ready_state_value)})"
        )
    ]
    complete_transition_enabled = (
        ready_for_testing_state_value is not None and complete_state_value is not None
    )
    if complete_transition_enabled:
        if ready_for_testing_state_value is None or complete_state_value is None:
            raise ValueError(
                "ready_for_testing_state_value and complete_state_value are required together"
            )
        transition_conditions.append(
            f"(previous.state == {_js_string(ready_for_testing_state_value)} && "
            f"current.state == {_js_string(ready_state_value)})"
        )
        transition_conditions.append(
            f"(previous.state == {_js_string(ready_for_testing_state_value)} && "
            f"current.state == {_js_string(draft_state_value)})"
        )
        transition_conditions.append(
            f"(previous.state == {_js_string(ready_for_testing_state_value)} && "
            f"current.state == {_js_string(complete_state_value)})"
        )

    condition = "current.state.changes() && (" + " || ".join(transition_conditions) + ")"
    complete_label_branch = ""
    if complete_transition_enabled:
        complete_label_branch = f"""
    }} else if (
        previous.state == {_js_string(ready_for_testing_state_value or "")} &&
        current.state == {_js_string(ready_state_value)}
    ) {{
        previousStateLabel = 'Ready for Testing';
        currentStateLabel = 'Ready';
    }} else if (
        previous.state == {_js_string(ready_for_testing_state_value or "")} &&
        current.state == {_js_string(draft_state_value)}
    ) {{
        previousStateLabel = 'Ready for Testing';
        currentStateLabel = 'Draft';
    }} else if (
        previous.state == {_js_string(ready_for_testing_state_value or "")} &&
        current.state == {_js_string(complete_state_value or "")}
    ) {{
        previousStateLabel = 'Ready for Testing';
        currentStateLabel = 'Complete';"""
    hmac_script = ""
    if hmac_secret_property_name is not None:
        hmac_script = f"""
    var body = JSON.stringify(payload);
    var timestamp = Math.floor(new GlideDateTime().getNumericValue() / 1000).toString();
    var webhookSecret = gs.getProperty({_js_string(hmac_secret_property_name)});
    if (!webhookSecret) {{
        gs.error('Jedi DevProject lifecycle webhook secret property is not configured');
        return;
    }}
    var encodedSecret = GlideStringUtil.base64Encode(webhookSecret);
    var signatureBase = timestamp + '.' + body;
    var signer = new GlideCertificateEncryption();
    var mac = signer.generateMac(encodedSecret, 'HmacSHA256', signatureBase);
    request.setRequestHeader('X-JEDI-Webhook-Timestamp', timestamp);
    request.setRequestHeader('X-JEDI-Webhook-Signature', 'sha256-base64=' + mac);

    request.setRequestBody(body);"""
    else:
        hmac_script = """
    request.setRequestBody(JSON.stringify(payload));"""

    script = f"""(function executeRule(current, previous) {{
    var previousStateLabel = 'Draft';
    var currentStateLabel = 'Ready';

    if (
        previous.state == {_js_string(draft_state_value)} &&
        current.state == {_js_string(ready_state_value)}
    ) {{
        previousStateLabel = 'Draft';
        currentStateLabel = 'Ready';{complete_label_branch}
    }} else {{
        return;
    }}

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
        story_sys_id: current.getUniqueValue(),
        previous_state: previousStateLabel,
        current_state: currentStateLabel,
        occurred_at: new GlideDateTime().getValue(),
        correlation_id: eventId,
        emitted_by: {_js_string(integration_identity)}
    }};
{hmac_script}
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
    ready_for_testing_state_value: str | None = None,
    complete_state_value: str | None = None,
    hmac_secret_property_name: str | None = None,
) -> LifecycleWebhookBootstrapSpec:
    rest_message = build_lifecycle_rest_message_spec(endpoint_url=endpoint_url)
    business_rule = build_lifecycle_business_rule_spec(
        integration_identity=integration_identity,
        draft_state_value=draft_state_value,
        ready_state_value=ready_state_value,
        ready_for_testing_state_value=ready_for_testing_state_value,
        complete_state_value=complete_state_value,
        rest_message_name=rest_message.name,
        rest_method_name=rest_message.method_name,
        hmac_secret_property_name=hmac_secret_property_name,
    )
    return LifecycleWebhookBootstrapSpec(
        rest_message=rest_message,
        business_rule=business_rule,
        hmac_secret_property_name=hmac_secret_property_name,
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
        result = _lifecycle_webhook_upsert_result(
            client.upsert_table_record(
                table=str(record["table"]),
                lookup=record["lookup"],
                fields=record["fields"],
            )
        )
        if record["table"] == "sys_rest_message":
            rest_message_sys_id = _lifecycle_webhook_lookup_text(result.get("sys_id"))
            upserted_records.append(
                {
                    "table": record["table"],
                    "lookup": record["lookup"],
                    "sys_id": rest_message_sys_id,
                }
            )
            if rest_message_sys_id:
                for method_record in _servicenow_apply_records(
                    spec,
                    rest_message_sys_id=rest_message_sys_id,
                ):
                    if method_record["table"] != "sys_rest_message_fn":
                        continue
                    method_result = _lifecycle_webhook_upsert_result(
                        client.upsert_table_record(
                            table=str(method_record["table"]),
                            lookup=method_record["lookup"],
                            fields=method_record["fields"],
                        )
                    )
                    method_sys_id = _lifecycle_webhook_lookup_text(
                        method_result.get("sys_id")
                    )
                    upserted_records.append(
                        {
                            "table": method_record["table"],
                            "lookup": method_record["lookup"],
                            "sys_id": method_sys_id,
                        }
                    )
            continue
        if record["table"] == "sys_rest_message_fn":
            continue
        result_sys_id = _lifecycle_webhook_lookup_text(result.get("sys_id"))
        upserted_records.append(
            {
                "table": record["table"],
                "lookup": record["lookup"],
                "sys_id": result_sys_id,
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
        actual_record = _lifecycle_webhook_fetch_result(actual_record)
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
        rest_message_sys_id = _lifecycle_webhook_lookup_text(actual_record.get("sys_id"))
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
            actual_method = _lifecycle_webhook_fetch_result(actual_method)
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


def _lifecycle_webhook_lookup_text(value: Any) -> str:
    if value is None:
        return ""
    if type(value) is str:
        return value
    if type(value) in {bool, int}:
        return str(value)
    raise ValueError(LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC)


def _lifecycle_webhook_upsert_result(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise ValueError(LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC)
    return result


def _lifecycle_webhook_fetch_result(result: object) -> dict[str, Any] | None:
    if result is None:
        return None
    if type(result) is not dict:
        raise ValueError(LIFECYCLE_WEBHOOK_LOOKUP_NON_JSON_DIAGNOSTIC)
    return result


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
    if type(value) is dict:
        if "value" not in value:
            return _UNSAFE_LIFECYCLE_VERIFICATION_VALUE
        return _normalise_servicenow_value(value["value"])
    if value is None:
        return None
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        if value.lower() in {"true", "false"}:
            return value.lower()
        return value
    if type(value) is int:
        return value
    return _UNSAFE_LIFECYCLE_VERIFICATION_VALUE


def _require_non_empty(field_name: str, value: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be empty")


def _js_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
