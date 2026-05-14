from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Capability(StrEnum):
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
    NEEDS_CLARIFICATION = "needs_clarification"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    MANUAL_DEVELOPER_BUILD = "manual_developer_build"


class FieldFormIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_table: str
    field_label: str
    field_type: str
    field_name: str | None = None
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


class StoryCapabilityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    story_number: str
    outcome: SuitabilityOutcome
    capabilities: set[Capability]
    supported_capabilities: set[Capability]
    intent: FieldFormIntent | None = None
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


def _normalize_field_name(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned.startswith("u_"):
        cleaned = f"u_{cleaned}"
    return cleaned


def _derive_custom_field_name(label: str) -> str:
    return _normalize_field_name(label)
