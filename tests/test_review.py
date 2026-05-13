import pytest

from jedi_devproject.models import CandidateStatus, UpdateSetCandidate
from jedi_devproject.review import (
    ExportBlocked,
    ReviewError,
    ReviewSettings,
    approve_for_export,
    export_preflight,
    reject_candidate,
)


def _candidate(status: CandidateStatus = CandidateStatus.READY_FOR_REVIEW) -> UpdateSetCandidate:
    return UpdateSetCandidate(
        story_number="STORY0010001",
        name="UPD_STORY0010001_Content_Update",
        eligibility_decision="eligible",
        eligibility_reasons=[],
        confidence=0.9,
        risk_score=0.1,
        status=status,
    )


def test_approve_for_export_requires_named_reviewer() -> None:
    with pytest.raises(ReviewError) as exc:
        approve_for_export(_candidate(), reviewer_id=" ", reason="Looks safe.")

    assert "reviewer_id is required" in str(exc.value)


def test_rejected_candidate_cannot_be_approved_without_new_revision() -> None:
    with pytest.raises(ReviewError) as exc:
        approve_for_export(
            _candidate(CandidateStatus.REJECTED),
            reviewer_id="dev@example.gov",
            reason="Reconsidered.",
        )

    assert "invalid status transition" in str(exc.value)


def test_reject_candidate_records_reviewer_reason_and_status() -> None:
    event = reject_candidate(
        _candidate(),
        reviewer_id="dev@example.gov",
        reason="Unsupported table mapping.",
    )

    assert event.reviewer_id == "dev@example.gov"
    assert event.reason == "Unsupported table mapping."
    assert event.status_after is CandidateStatus.REJECTED


def test_draft_candidate_cannot_be_exported() -> None:
    with pytest.raises(ExportBlocked) as exc:
        export_preflight(_candidate(CandidateStatus.DRAFT), ReviewSettings())

    assert "candidate is not approved for export" in str(exc.value)


def test_xml_export_feature_flag_defaults_off() -> None:
    approved = approve_for_export(
        _candidate(),
        reviewer_id="dev@example.gov",
        reason="Ready for sandbox export.",
    )

    with pytest.raises(ExportBlocked) as exc:
        export_preflight(approved.candidate, ReviewSettings())

    assert "xml export is disabled" in str(exc.value)
