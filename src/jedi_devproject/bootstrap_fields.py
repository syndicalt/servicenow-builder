"""ServiceNow story-table bootstrap field planning, creation, and read-only UI policy."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict

from jedi_devproject.servicenow import StoryDictionaryField

BOOTSTRAP_TABLE = "rm_story"


class BootstrapFieldSpec(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    element: str
    column_label: str
    internal_type: str
    max_length: int | None = None
    read_only: bool = False


class BootstrapFieldPlan(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    table: str
    missing_fields: list[str]
    fields_to_create: list[BootstrapFieldSpec]
    fields_to_update_writable: list[str] = []
    form_layout_changes: list[str]
    requires_apply_confirmation: bool

    @property
    def ready(self) -> bool:
        return not self.missing_fields and not self.fields_to_update_writable


class BootstrapApplyResult(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    applied: bool
    created_fields: list[str]
    updated_writable_fields: list[str] = []
    platform_readonly_records: list[str] = []
    form_layout_changes: list[str]
    reasons: list[str]


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
        read_only: bool,
    ) -> dict[str, object]:
        """Create a dictionary field on rm_story."""

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """Create or update a ServiceNow table record."""


REQUIRED_BOOTSTRAP_FIELDS = [
    BootstrapFieldSpec(
        element="u_ai_status",
        column_label="AI Status",
        internal_type="string",
        max_length=80,
    ),
    BootstrapFieldSpec(
        element="u_ai_handoff_type",
        column_label="AI Handoff Type",
        internal_type="string",
        max_length=255,
    ),
    BootstrapFieldSpec(
        element="u_ai_handoff_reference",
        column_label="AI Handoff Reference",
        internal_type="string",
        max_length=1024,
    ),
    BootstrapFieldSpec(
        element="u_ai_artifact_reference",
        column_label="AI Artifact Reference",
        internal_type="string",
        max_length=1024,
    ),
]

BOOTSTRAP_READONLY_UI_POLICY_NAME = "Jedi DevProject read-only automation metadata"
BOOTSTRAP_DICTIONARY_FIELDS_UNSAFE_DIAGNOSTIC = (
    "bootstrap dictionary fields contain non-JSON value"
)
BOOTSTRAP_CREATE_FIELD_RESULT_UNSAFE_DIAGNOSTIC = (
    "bootstrap create field result is unsafe"
)
BOOTSTRAP_TABLE_UPSERT_RESULT_UNSAFE_DIAGNOSTIC = (
    "bootstrap table upsert result is unsafe"
)


def plan_bootstrap_fields(
    dictionary_fields: list[StoryDictionaryField],
) -> BootstrapFieldPlan:
    safe_dictionary_fields = _bootstrap_dictionary_fields(dictionary_fields)
    existing_fields = {field.element: field for field in safe_dictionary_fields if field.active}
    fields_to_create = [
        field for field in REQUIRED_BOOTSTRAP_FIELDS if field.element not in existing_fields
    ]
    fields_to_update_writable = [
        field.element
        for field in REQUIRED_BOOTSTRAP_FIELDS
        if field.element in existing_fields
        and not field.read_only
        and existing_fields[field.element].read_only
    ]
    return BootstrapFieldPlan(
        table=BOOTSTRAP_TABLE,
        missing_fields=[field.element for field in fields_to_create],
        fields_to_create=fields_to_create,
        fields_to_update_writable=fields_to_update_writable,
        form_layout_changes=[],
        requires_apply_confirmation=True,
    )


def _bootstrap_dictionary_fields(fields: object) -> list[StoryDictionaryField]:
    if type(fields) is not list:
        raise ValueError(BOOTSTRAP_DICTIONARY_FIELDS_UNSAFE_DIAGNOSTIC)
    for field in fields:
        if type(field) is not StoryDictionaryField:
            raise ValueError(BOOTSTRAP_DICTIONARY_FIELDS_UNSAFE_DIAGNOSTIC)
    return fields


def _bootstrap_create_field_result(result: object) -> dict[str, object]:
    if type(result) is not dict:
        raise ValueError(BOOTSTRAP_CREATE_FIELD_RESULT_UNSAFE_DIAGNOSTIC)
    return result


def _bootstrap_table_upsert_result(result: object) -> dict[str, Any]:
    if type(result) is not dict:
        raise ValueError(BOOTSTRAP_TABLE_UPSERT_RESULT_UNSAFE_DIAGNOSTIC)
    return result


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
            updated_writable_fields=[],
            form_layout_changes=[],
            reasons=["bootstrap_confirmation_required"],
        )

    plan = plan_bootstrap_fields(client.fetch_story_dictionary_fields())
    created_fields: list[str] = []
    for field in plan.fields_to_create:
        _bootstrap_create_field_result(
            client.create_story_dictionary_field(
                element=field.element,
                column_label=field.column_label,
                internal_type=field.internal_type,
                max_length=field.max_length,
                read_only=field.read_only,
            )
        )
        created_fields.append(field.element)

    updated_writable_fields: list[str] = []
    for element in plan.fields_to_update_writable:
        _bootstrap_table_upsert_result(
            client.upsert_table_record(
                table="sys_dictionary",
                lookup={"name": BOOTSTRAP_TABLE, "element": element},
                fields={"read_only": "false"},
            )
        )
        updated_writable_fields.append(element)

    platform_readonly_records = apply_platform_readonly_policy(client)

    return BootstrapApplyResult(
        applied=bool(created_fields or updated_writable_fields or platform_readonly_records),
        created_fields=created_fields,
        updated_writable_fields=updated_writable_fields,
        platform_readonly_records=platform_readonly_records,
        form_layout_changes=[],
        reasons=[],
    )


def apply_platform_readonly_policy(client: BootstrapClient) -> list[str]:
    script_true = _bootstrap_readonly_ui_policy_script()
    _bootstrap_table_upsert_result(
        client.upsert_table_record(
            table="sys_ui_policy",
            lookup={
                "table": BOOTSTRAP_TABLE,
                "short_description": BOOTSTRAP_READONLY_UI_POLICY_NAME,
            },
            fields={
                "table": BOOTSTRAP_TABLE,
                "short_description": BOOTSTRAP_READONLY_UI_POLICY_NAME,
                "active": "true",
                "global": "true",
                "on_load": "true",
                "reverse_if_false": "false",
                "conditions": "",
                "run_scripts": "true",
                "script_true": script_true,
                "script_false": "function onCondition() {\n}",
            },
        )
    )
    return [f"sys_ui_policy:{BOOTSTRAP_READONLY_UI_POLICY_NAME}"]


def _bootstrap_readonly_ui_policy_script() -> str:
    read_only_lines = "\n".join(
        f"    g_form.setReadOnly('{field.element}', true);" for field in REQUIRED_BOOTSTRAP_FIELDS
    )
    return f"function onCondition() {{\n{read_only_lines}\n}}"
