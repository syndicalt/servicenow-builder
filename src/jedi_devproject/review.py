from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel

from jedi_devproject.models import CandidateStatus, UpdateSetCandidate


class ReviewError(ValueError):
    """Raised when a review decision is invalid."""


class ExportBlocked(RuntimeError):
    """Raised when export preflight blocks a candidate."""


class ReviewSettings(BaseModel):
    xml_export_enabled: bool = False


class ReviewEvent(BaseModel):
    story_number: str
    reviewer_id: str
    reason: str
    status_before: CandidateStatus
    status_after: CandidateStatus
    decided_at: datetime


class ReviewResult(BaseModel):
    candidate: UpdateSetCandidate
    event: ReviewEvent


def approve_for_export(
    candidate: UpdateSetCandidate,
    *,
    reviewer_id: str,
    reason: str,
) -> ReviewResult:
    return _review_transition(
        candidate,
        reviewer_id=reviewer_id,
        reason=reason,
        next_status=CandidateStatus.APPROVED_FOR_EXPORT,
    )


def reject_candidate(
    candidate: UpdateSetCandidate,
    *,
    reviewer_id: str,
    reason: str,
) -> ReviewEvent:
    return _review_transition(
        candidate,
        reviewer_id=reviewer_id,
        reason=reason,
        next_status=CandidateStatus.REJECTED,
    ).event


def export_preflight(candidate: UpdateSetCandidate, settings: ReviewSettings) -> None:
    if candidate.status is not CandidateStatus.APPROVED_FOR_EXPORT:
        raise ExportBlocked("candidate is not approved for export")

    if not settings.xml_export_enabled:
        raise ExportBlocked("xml export is disabled")


def _review_transition(
    candidate: UpdateSetCandidate,
    *,
    reviewer_id: str,
    reason: str,
    next_status: CandidateStatus,
) -> ReviewResult:
    if reviewer_id.strip() == "":
        raise ReviewError("reviewer_id is required")

    if not candidate.can_transition_to(next_status):
        raise ReviewError(
            f"invalid status transition: {candidate.status.value} -> {next_status.value}"
        )

    updated = candidate.model_copy(update={"status": next_status})
    event = ReviewEvent(
        story_number=candidate.story_number,
        reviewer_id=reviewer_id,
        reason=reason,
        status_before=candidate.status,
        status_after=next_status,
        decided_at=datetime.now(UTC),
    )
    return ReviewResult(candidate=updated, event=event)
