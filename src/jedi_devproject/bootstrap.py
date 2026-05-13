from __future__ import annotations

from typing import Protocol

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
        authentication="configured_in_servicenow",
        content_type="application/json",
    )


def _require_non_empty(field_name: str, value: str) -> None:
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be empty")


def _js_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
