from __future__ import annotations

import re
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jedi_devproject.automation_intent import AutomationIntent, AutomationIntentType
from jedi_devproject.capabilities import Capability, capability_profile


class ServiceNowSurface(StrEnum):
    FORM_LAYOUT = "form_layout"
    UNKNOWN = "unknown"


class SurfaceOperationKind(StrEnum):
    FORM_LAYOUT_SECTION_REMOVE = "form_layout.section.remove"
    FORM_LAYOUT_SECTION_ADD = "form_layout.section.add"
    FORM_LAYOUT_SECTION_RENAME = "form_layout.section.rename"
    FORM_LAYOUT_SECTION_REORDER = "form_layout.section.reorder"
    UNKNOWN = "unknown"


class SurfaceOperationStatus(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class SurfaceOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: SurfaceOperationKind
    status: SurfaceOperationStatus
    targets: list[str] = Field(default_factory=list)
    view: str = "Default view"
    reason_codes: list[str] = Field(default_factory=list)


class SurfaceOperationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: ServiceNowSurface
    target_table: str | None = None
    required_instance_context: list[str] = Field(default_factory=list)
    operations: list[SurfaceOperation] = Field(default_factory=list)

    @property
    def supported_operations(self) -> list[SurfaceOperation]:
        return [
            operation
            for operation in self.operations
            if operation.status is SurfaceOperationStatus.SUPPORTED
        ]

    @property
    def unsupported_operations(self) -> list[SurfaceOperation]:
        return [
            operation
            for operation in self.operations
            if operation.status is SurfaceOperationStatus.UNSUPPORTED
        ]


def plan_surface_operations(
    intent: AutomationIntent | dict[str, Any] | None,
) -> SurfaceOperationPlan:
    if isinstance(intent, dict):
        intent = AutomationIntent.model_validate(intent)
    if intent is None or intent.intent_type is not AutomationIntentType.FORM_SECTION:
        return SurfaceOperationPlan(surface=ServiceNowSurface.UNKNOWN)

    required_context = capability_profile(Capability.FORM_SECTION_REMOVE).required_instance_context
    operation_kind = _form_section_operation_kind(intent)
    status = (
        SurfaceOperationStatus.SUPPORTED
        if operation_kind is SurfaceOperationKind.FORM_LAYOUT_SECTION_REMOVE
        and intent.capability is Capability.FORM_SECTION_REMOVE
        else SurfaceOperationStatus.UNSUPPORTED
    )
    reason_codes = [] if status is SurfaceOperationStatus.SUPPORTED else ["builder_not_implemented"]
    return SurfaceOperationPlan(
        surface=ServiceNowSurface.FORM_LAYOUT,
        target_table=intent.target_table,
        required_instance_context=required_context,
        operations=[
            SurfaceOperation(
                kind=operation_kind,
                status=status,
                targets=[section.strip() for section in intent.form_sections if section.strip()],
                view=(intent.form_view or "Default view").strip() or "Default view",
                reason_codes=reason_codes,
            )
        ],
    )


def _form_section_operation_kind(intent: AutomationIntent) -> SurfaceOperationKind:
    behavior = (intent.expected_behavior or "").lower()
    if _contains_reorder_action(behavior):
        return SurfaceOperationKind.FORM_LAYOUT_SECTION_REORDER
    if _contains_rename_action(behavior):
        return SurfaceOperationKind.FORM_LAYOUT_SECTION_RENAME
    if _contains_add_action(behavior):
        return SurfaceOperationKind.FORM_LAYOUT_SECTION_ADD
    if _contains_remove_action(behavior) or intent.capability is Capability.FORM_SECTION_REMOVE:
        return SurfaceOperationKind.FORM_LAYOUT_SECTION_REMOVE
    return SurfaceOperationKind.UNKNOWN


def _contains_remove_action(value: str) -> bool:
    if re.search(r"\b(?:do not|don't|should not|must not)\s+(?:remove|hide)\b", value):
        return False
    return bool(
        re.search(
            r"\b(?:remove|hide)\b|\bhidden\b|\bnot\s+display\b|"
            r"\bwill\s+not\s+display\b|\bdo\s+not\s+display\b",
            value,
        )
    )


def _contains_add_action(value: str) -> bool:
    return bool(re.search(r"\b(?:add|create|insert)\b", value))


def _contains_rename_action(value: str) -> bool:
    return bool(re.search(r"\b(?:rename|retitle|change\s+the\s+label)\b", value))


def _contains_reorder_action(value: str) -> bool:
    return bool(re.search(r"\b(?:move|reorder|before|after)\b", value))
