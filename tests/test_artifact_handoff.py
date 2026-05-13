from pathlib import Path

import pytest

from jedi_devproject.artifact_handoff import (
    ArtifactExposure,
    ArtifactKind,
    build_artifact_handoff_report,
    build_artifact_handoff_work_note,
    delivery_attachment_jobs_from_report,
    plan_artifact_handoff,
)


def test_internal_evidence_artifacts_are_not_servicenow_attachments() -> None:
    plan = plan_artifact_handoff(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.IMPLEMENTATION_PACKET,
        artifact_path="artifacts/lifecycle-smoke/implementation-packets/run/STRY0010013.json",
        approved_for_delivery=False,
    )

    assert plan.exposure is ArtifactExposure.INTERNAL_EVIDENCE
    assert plan.attach_to_servicenow is False
    assert plan.write_story_link is True
    assert plan.required_before_ready_for_testing is False
    assert "internal audit evidence" in plan.rationale


def test_approved_update_set_export_requires_reviewed_export_contract() -> None:
    plan = plan_artifact_handoff(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path="artifacts/exports/STRY0010013.xml",
        approved_for_delivery=True,
    )

    assert plan.exposure is ArtifactExposure.INTERNAL_EVIDENCE
    assert plan.attach_to_servicenow is False
    assert plan.service_now_attachment_label is None
    assert "reviewed export contract" in plan.rationale


def test_reviewed_update_set_export_is_delivery_attachment() -> None:
    plan = plan_artifact_handoff(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path="artifacts/exports/STRY0010013.xml",
        approved_for_delivery=True,
        delivery_contract="reviewed_export",
    )

    assert plan.exposure is ArtifactExposure.DELIVERY_EVIDENCE
    assert plan.attach_to_servicenow is True
    assert plan.write_story_link is True
    assert plan.required_before_ready_for_testing is True
    assert plan.service_now_attachment_label == "Approved Update Set XML"


def test_unapproved_update_set_export_stays_internal() -> None:
    plan = plan_artifact_handoff(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path="artifacts/exports/STRY0010013.xml",
        approved_for_delivery=False,
    )

    assert plan.exposure is ArtifactExposure.INTERNAL_EVIDENCE
    assert plan.attach_to_servicenow is False
    assert plan.required_before_ready_for_testing is False
    assert "human approval" in plan.rationale


def test_test_evidence_bundle_is_attached_after_approval() -> None:
    plan = plan_artifact_handoff(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.TEST_EVIDENCE_BUNDLE,
        artifact_path="artifacts/test-evidence/STRY0010013.zip",
        approved_for_delivery=True,
        delivery_contract="reviewed_export",
    )

    assert plan.exposure is ArtifactExposure.DELIVERY_EVIDENCE
    assert plan.attach_to_servicenow is True
    assert plan.service_now_attachment_label == "Test Evidence Bundle"


def test_handoff_report_summarizes_multiple_artifact_decisions(tmp_path: Path) -> None:
    candidate_path = tmp_path / "STRY0010013.json"
    evidence_path = tmp_path / "STRY0010013.zip"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")
    evidence_path.write_text("test evidence", encoding="utf-8")

    report = build_artifact_handoff_report(
        run_id="handoff-001",
        story_number="STRY0010013",
        artifacts=[
            {
                "artifact_kind": "implementation_candidate",
                "artifact_path": str(candidate_path),
                "approved_for_delivery": False,
            },
            {
                "artifact_kind": "test_evidence_bundle",
                "artifact_path": str(evidence_path),
                "approved_for_delivery": True,
                "delivery_contract": "reviewed_export",
            },
        ],
    )

    assert report["run_id"] == "handoff-001"
    assert report["story_number"] == "STRY0010013"
    assert report["summary"] == {
        "total": 2,
        "attach_to_servicenow": 1,
        "internal_evidence": 1,
        "delivery_evidence": 1,
    }
    assert report["decisions"][0]["attach_to_servicenow"] is False
    assert len(report["decisions"][0]["artifact_sha256"]) == 64
    assert report["decisions"][1]["service_now_attachment_label"] == (
        "Test Evidence Bundle"
    )


def test_handoff_report_rejects_missing_artifact_path(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        build_artifact_handoff_report(
            run_id="handoff-001",
            story_number="STRY0010013",
            artifacts=[
                {
                    "artifact_kind": "implementation_candidate",
                    "artifact_path": str(tmp_path / "missing.json"),
                    "approved_for_delivery": False,
                }
            ],
        )


def test_handoff_work_note_summarizes_report_without_hash_dump(tmp_path: Path) -> None:
    report = {
        "run_id": "handoff-001",
        "story_number": "STRY0010013",
        "summary": {
            "total": 2,
            "attach_to_servicenow": 0,
            "internal_evidence": 2,
            "delivery_evidence": 0,
        },
        "decisions": [
            {
                "artifact_kind": "implementation_candidate",
                "artifact_sha256": "a" * 64,
            }
        ],
    }

    note = build_artifact_handoff_work_note(
        report=report,
        report_path=tmp_path / "handoff-001.json",
    )

    assert "Artifact handoff planned." in note
    assert "Report: " in note
    assert "attach_to_servicenow=0" in note
    assert "internal_evidence=2" in note
    assert "aaaa" not in note


def test_delivery_attachment_jobs_include_only_attachable_decisions() -> None:
    report = {
        "run_id": "handoff-001",
        "story_number": "STRY0010013",
        "summary": {
            "total": 2,
            "attach_to_servicenow": 1,
            "internal_evidence": 1,
            "delivery_evidence": 1,
        },
        "decisions": [
            {
                "artifact_kind": "implementation_candidate",
                "artifact_path": "artifacts/candidate.json",
                "attach_to_servicenow": False,
                "service_now_attachment_label": None,
            },
            {
                "artifact_kind": "update_set_xml",
                "artifact_path": "artifacts/export.xml",
                "attach_to_servicenow": True,
                "delivery_contract": "reviewed_export",
                "service_now_attachment_label": "Approved Update Set XML",
            },
        ],
    }

    jobs = delivery_attachment_jobs_from_report(report)

    assert jobs == [
        {
            "story_number": "STRY0010013",
            "artifact_kind": "update_set_xml",
            "artifact_path": "artifacts/export.xml",
            "delivery_contract": "reviewed_export",
            "attachment_label": "Approved Update Set XML",
        }
    ]
