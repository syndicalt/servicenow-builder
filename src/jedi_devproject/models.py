from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class DataClassification(StrEnum):
    PUBLIC = "public"
    CUI = "cui"
    PII = "pii"


class ProviderStatus(StrEnum):
    DISABLED = "disabled"
    EVALUATION = "evaluation"
    APPROVED = "approved"
    REVOKED = "revoked"


class CandidateStatus(StrEnum):
    DRAFT = "Draft"
    READY_FOR_REVIEW = "Ready for Review"
    APPROVED_FOR_EXPORT = "Approved for Export"
    REJECTED = "Rejected"
    MANUAL_BUILD = "Manual Build"


class Story(BaseModel):
    sys_id: str
    number: str
    short_description: str
    description: str
    story_points: float = Field(ge=0)
    priority: int = Field(ge=1, le=5)
    state: str
    data_classification: DataClassification
    acceptance_criteria: str | None = None
    business_value: float | None = None
    risk: float | None = None
    effort_estimate: float | None = None
    dependencies: list[str] = Field(default_factory=list)
    affected_tables: list[str] = Field(default_factory=list)
    affected_applications: list[str] = Field(default_factory=list)
    additional_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sys_id", "number", "short_description", "description", "state")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


class ProjectContext(BaseModel):
    name: str
    objectives: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    success_metrics: list[str] = Field(default_factory=list)
    authorized_environments: list[str] = Field(default_factory=list)
    approved_model_providers: list[str] = Field(default_factory=list)
    data_handling_constraints: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def require_non_empty_name(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


class ProviderPolicy(BaseModel):
    provider_id: str
    deployment_boundary: str
    authorization_level: str
    allowed_data_classes: set[DataClassification]
    allowed_tasks: set[str]
    max_context_policy: str
    retention_policy: str
    status: ProviderStatus

    def allows(self, *, task: str, data_class: DataClassification) -> bool:
        return (
            self.status is ProviderStatus.APPROVED
            and task in self.allowed_tasks
            and data_class in self.allowed_data_classes
        )


class RetrievalCitation(BaseModel):
    source: str
    content_hash: str
    confidence: float = Field(ge=0, le=1)
    version: str | None = None


class CandidateChange(BaseModel):
    table: str
    operation: Literal["insert", "update", "delete"]
    fields: dict[str, Any] = Field(default_factory=dict)
    sys_id: str | None = None
    rationale: str | None = None


class CandidateScript(BaseModel):
    type: str
    name: str
    content: str
    when: str
    rationale: str | None = None


class UpdateSetCandidate(BaseModel):
    story_number: str
    name: str
    eligibility_decision: Literal["eligible", "manual_review", "rejected"]
    eligibility_reasons: list[str]
    confidence: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    status: CandidateStatus
    changes: list[CandidateChange] = Field(default_factory=list)
    scripts: list[CandidateScript] = Field(default_factory=list)
    retrieval_citations: list[RetrievalCitation] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    reviewer_notes: list[str] = Field(default_factory=list)
    artifact_hash: str | None = None

    @field_validator("story_number", "name")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value

    def can_transition_to(self, next_status: CandidateStatus) -> bool:
        allowed_transitions = {
            CandidateStatus.DRAFT: {
                CandidateStatus.READY_FOR_REVIEW,
                CandidateStatus.REJECTED,
                CandidateStatus.MANUAL_BUILD,
            },
            CandidateStatus.READY_FOR_REVIEW: {
                CandidateStatus.APPROVED_FOR_EXPORT,
                CandidateStatus.REJECTED,
                CandidateStatus.MANUAL_BUILD,
            },
            CandidateStatus.APPROVED_FOR_EXPORT: set(),
            CandidateStatus.REJECTED: {CandidateStatus.MANUAL_BUILD},
            CandidateStatus.MANUAL_BUILD: set(),
        }
        return next_status in allowed_transitions[self.status]


class RunManifest(BaseModel):
    run_id: str
    artifact_hashes: list[str] = Field(default_factory=list)

    @field_validator("run_id")
    @classmethod
    def require_non_empty_run_id(cls, value: str) -> str:
        if value.strip() == "":
            raise ValueError("must not be empty")
        return value


def stable_artifact_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
