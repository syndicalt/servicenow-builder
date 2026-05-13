from __future__ import annotations

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
