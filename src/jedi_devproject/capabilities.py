from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Capability(StrEnum):
    BUSINESS_RULE_ANALYZE = "business_rule_analyze"
    BUSINESS_RULE_GENERATE = "business_rule_generate"
    CLIENT_SCRIPT_ANALYZE = "client_script_analyze"
    CLIENT_SCRIPT_GENERATE = "client_script_generate"
    SCRIPT_INCLUDE_ANALYZE = "script_include_analyze"
    SCRIPT_INCLUDE_GENERATE = "script_include_generate"
    DICTIONARY_FIELD_CREATE = "dictionary_field_create"
    FIELD_LABEL_CREATE = "field_label_create"
    FORM_LAYOUT_PLACE_FIELD = "form_layout_place_field"
    CHOICE_VALUES_CREATE = "choice_values_create"
    ACL_MODIFY = "acl_modify"
    FLOW_MODIFY = "flow_modify"
    BUSINESS_RULE_CREATE = "business_rule_create"
    SCRIPT_INCLUDE_MODIFY = "script_include_modify"
    DATA_MIGRATION = "data_migration"
    INTEGRATION_MODIFY = "integration_modify"
    UNKNOWN = "unknown"


class SuitabilityOutcome(StrEnum):
    AUTOMATED_BUILD = "automated_build"
    CONTEXT_ANALYSIS = "context_analysis"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    MANUAL_DEVELOPER_BUILD = "manual_developer_build"


class FieldFormIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    field_label: str
    field_type: str
    field_name: str | None = None
    reference_table: str | None = None
    reference_qualifier: str | None = None
    max_length: int | None = None
    mandatory: bool = False
    default_value: str = ""
    placement_anchor: str | None = None
    placement_position: str = "below"

    @field_validator("target_table", "field_label", "field_type")
    @classmethod
    def require_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("placement_position")
    @classmethod
    def validate_position(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {"above", "below", "end"}:
            raise ValueError("placement_position must be above, below, or end")
        return cleaned

    @model_validator(mode="after")
    def normalize_field_name(self) -> FieldFormIntent:
        if self.field_name is not None and self.field_name.strip() != "":
            self.field_name = _normalize_field_name(self.field_name)
            return self
        self.field_name = _derive_custom_field_name(self.field_label)
        return self


class CapabilityProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: Capability
    status: str
    supported_artifacts: list[str]
    required_instance_context: list[str]
    deterministic_validators: list[str]
    unsupported_cases: list[str]
    uat_story_shape: list[str]
    researcher: str
    build_pipeline: str
    current_max_story_points: int
    target_max_story_points: int
    creates_update_set: bool = False


class StoryCapabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_number: str
    outcome: SuitabilityOutcome
    capabilities: set[Capability]
    supported_capabilities: set[Capability]
    intent: FieldFormIntent | None = None
    target_table: str | None = None
    required_instance_context: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    missing_details: list[str] = Field(default_factory=list)
    unsupported_capabilities: set[Capability] = Field(default_factory=set)
    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)

    @property
    def is_automated(self) -> bool:
        return self.outcome is SuitabilityOutcome.AUTOMATED_BUILD

    @property
    def unsupported_capability_names(self) -> list[str]:
        return sorted(capability.value for capability in self.unsupported_capabilities)


def _code_surface_profile(
    *,
    capability: Capability,
    supported_artifact: str,
    required_instance_context: list[str],
    generation_label: str,
) -> CapabilityProfile:
    return CapabilityProfile(
        capability=capability,
        status="context_only",
        supported_artifacts=[supported_artifact],
        required_instance_context=required_instance_context,
        deterministic_validators=[
            "target_table_present",
            f"{supported_artifact}_context_retrieved",
            "script_bodies_redacted",
        ],
        unsupported_cases=[
            f"{generation_label} generation",
            "delete rules",
            "scheduled jobs",
            "embedded credentials",
            "outbound REST calls",
            "cross-table data migration",
        ],
        uat_story_shape=[
            "target table",
            "trigger timing",
            "trigger operations",
            "condition",
            "expected action",
            "test evidence",
        ],
        researcher="code_surface_researcher",
        build_pipeline=f"{generation_label.replace(' ', '_')}_update_set_pipeline",
        current_max_story_points=0,
        target_max_story_points=5,
        creates_update_set=False,
    )


def _dictionary_form_profile(*, capability: Capability) -> CapabilityProfile:
    return CapabilityProfile(
        capability=capability,
        status="enabled",
        supported_artifacts=["sys_dictionary", "sys_documentation", "sys_ui_element"],
        required_instance_context=["table_schema", "form_layout"],
        deterministic_validators=[
            "target_table_present",
            "field_type_supported",
            "form_section_retrieved",
            "anchor_field_resolved",
        ],
        unsupported_cases=[
            "ACL generation",
            "data migration",
            "workflow mutation",
            "integration changes",
        ],
        uat_story_shape=[
            "target table",
            "field label or field name",
            "field type",
            "form placement",
            "acceptance criteria",
        ],
        researcher="dictionary_form_researcher",
        build_pipeline="dictionary_form_update_set_pipeline",
        current_max_story_points=3,
        target_max_story_points=5,
        creates_update_set=True,
    )


def _generation_profile(
    *,
    capability: Capability,
    status: str,
    supported_artifact: str,
    required_instance_context: list[str],
    researcher: str,
    build_pipeline: str,
    unsupported_cases: list[str],
    current_max_story_points: int = 0,
) -> CapabilityProfile:
    return CapabilityProfile(
        capability=capability,
        status=status,
        supported_artifacts=[supported_artifact],
        required_instance_context=required_instance_context,
        deterministic_validators=[
            "target_table_present",
            "required_context_retrieved",
            "structured_output_schema_valid",
            "script_safety_validated",
            "xml_customer_update_validated",
        ],
        unsupported_cases=unsupported_cases,
        uat_story_shape=[
            "target table",
            "trigger timing",
            "trigger operations",
            "explicit condition",
            "expected behavior",
            "fields read",
            "fields written",
            "test evidence",
        ],
        researcher=researcher,
        build_pipeline=build_pipeline,
        current_max_story_points=current_max_story_points,
        target_max_story_points=5,
        creates_update_set=True,
    )


CAPABILITY_REGISTRY: dict[Capability, CapabilityProfile] = {
    Capability.DICTIONARY_FIELD_CREATE: _dictionary_form_profile(
        capability=Capability.DICTIONARY_FIELD_CREATE
    ),
    Capability.FORM_LAYOUT_PLACE_FIELD: _dictionary_form_profile(
        capability=Capability.FORM_LAYOUT_PLACE_FIELD
    ),
    Capability.BUSINESS_RULE_ANALYZE: _code_surface_profile(
        capability=Capability.BUSINESS_RULE_ANALYZE,
        supported_artifact="sys_script",
        required_instance_context=["table_schema", "business_rules"],
        generation_label="business rule",
    ),
    Capability.CLIENT_SCRIPT_ANALYZE: _code_surface_profile(
        capability=Capability.CLIENT_SCRIPT_ANALYZE,
        supported_artifact="sys_script_client",
        required_instance_context=["table_schema", "client_scripts"],
        generation_label="client script",
    ),
    Capability.SCRIPT_INCLUDE_ANALYZE: _code_surface_profile(
        capability=Capability.SCRIPT_INCLUDE_ANALYZE,
        supported_artifact="sys_script_include",
        required_instance_context=["script_includes"],
        generation_label="script include",
    ),
    Capability.BUSINESS_RULE_GENERATE: _generation_profile(
        capability=Capability.BUSINESS_RULE_GENERATE,
        status="enabled",
        supported_artifact="sys_script",
        required_instance_context=["table_schema", "business_rules"],
        researcher="code_surface_researcher",
        build_pipeline="business_rule_update_set_pipeline",
        unsupported_cases=[
            "delete rules",
            "async/display rules",
            "scheduled jobs",
            "outbound REST calls",
            "credentials",
            "cross-table writes",
            "broad GlideRecord mutation",
        ],
        current_max_story_points=3,
    ),
    Capability.CLIENT_SCRIPT_GENERATE: _generation_profile(
        capability=Capability.CLIENT_SCRIPT_GENERATE,
        status="designed",
        supported_artifact="sys_script_client",
        required_instance_context=["table_schema", "client_scripts"],
        researcher="code_surface_researcher",
        build_pipeline="client_script_update_set_pipeline",
        unsupported_cases=[
            "DOM manipulation outside g_form APIs",
            "GlideAjax dependency creation",
            "external calls",
            "credentials",
        ],
    ),
    Capability.SCRIPT_INCLUDE_GENERATE: _generation_profile(
        capability=Capability.SCRIPT_INCLUDE_GENERATE,
        status="planned",
        supported_artifact="sys_script_include",
        required_instance_context=["script_includes", "code_surface_analysis"],
        researcher="code_surface_researcher",
        build_pipeline="script_include_update_set_pipeline",
        unsupported_cases=[
            "global privilege escalation",
            "cross-scope access changes",
            "external calls",
            "credentials",
        ],
    ),
}


def capability_profile(capability: Capability) -> CapabilityProfile:
    return CAPABILITY_REGISTRY[capability]


def generation_capability_profiles() -> list[CapabilityProfile]:
    return [
        CAPABILITY_REGISTRY[Capability.DICTIONARY_FIELD_CREATE],
        CAPABILITY_REGISTRY[Capability.FORM_LAYOUT_PLACE_FIELD],
        CAPABILITY_REGISTRY[Capability.BUSINESS_RULE_GENERATE],
        CAPABILITY_REGISTRY[Capability.CLIENT_SCRIPT_GENERATE],
        CAPABILITY_REGISTRY[Capability.SCRIPT_INCLUDE_GENERATE],
    ]


def _normalize_field_name(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned.startswith("u_"):
        cleaned = f"u_{cleaned}"
    return cleaned


def _derive_custom_field_name(label: str) -> str:
    return _normalize_field_name(label)
