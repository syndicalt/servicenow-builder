from pathlib import Path

import pytest

from jedi_devproject.artifact_handoff import (
    ArtifactExposure,
    ArtifactKind,
    build_artifact_handoff_report,
    build_artifact_handoff_work_note,
    build_reviewed_delivery_artifact_job,
    delivery_attachment_jobs_from_report,
    plan_artifact_handoff,
)


class _HostileSummaryText(str):
    def __str__(self) -> str:
        raise AssertionError("client_secret=artifact-summary-text-secret")


class _HostileSummaryValue:
    def __str__(self) -> str:
        raise AssertionError("client_secret=artifact-summary-object-secret")


class _HostileAttachmentText(str):
    def __str__(self) -> str:
        raise AssertionError("client_secret=attachment-text-secret")


class _HostileAttachmentValue:
    def __str__(self) -> str:
        raise AssertionError("client_secret=attachment-object-secret")


class _HostileAttachFlag:
    def __bool__(self) -> bool:
        raise AssertionError("client_secret=attachment-flag-secret")


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


def test_handoff_report_hashes_artifacts_without_whole_file_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")

    def fail_read_bytes(self: Path) -> bytes:
        raise AssertionError(f"unexpected whole-file read for {self}")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)

    report = build_artifact_handoff_report(
        run_id="handoff-001",
        story_number="STRY0010013",
        artifacts=[
            {
                "artifact_kind": "update_set_xml",
                "artifact_path": str(export_path),
                "approved_for_delivery": True,
                "delivery_contract": "reviewed_export",
            }
        ],
    )

    assert len(report["decisions"][0]["artifact_sha256"]) == 64


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


def test_handoff_report_rejects_hostile_artifact_text_without_coercion() -> None:
    with pytest.raises(ValueError) as exc_info:
        build_artifact_handoff_report(
            run_id="handoff-001",
            story_number="STRY0010013",
            artifacts=[
                {
                    "artifact_kind": _HostileAttachmentText("client_secret=kind-payload"),
                    "artifact_path": _HostileAttachmentValue(),
                    "approved_for_delivery": False,
                }
            ],
        )

    assert str(exc_info.value) == "artifact_handoff_report_invalid"
    assert "kind-payload" not in str(exc_info.value)
    assert "attachment-object-secret" not in str(exc_info.value)


def test_handoff_report_rejects_hostile_approval_flag_without_truthiness() -> None:
    with pytest.raises(ValueError) as exc_info:
        build_artifact_handoff_report(
            run_id="handoff-001",
            story_number="STRY0010013",
            artifacts=[
                {
                    "artifact_kind": "implementation_candidate",
                    "artifact_path": "artifacts/candidate.json",
                    "approved_for_delivery": _HostileAttachFlag(),
                }
            ],
        )

    assert str(exc_info.value) == "artifact_handoff_report_invalid"
    assert "attachment-flag-secret" not in str(exc_info.value)


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


def test_handoff_work_note_sanitizes_untrusted_report_values(tmp_path: Path) -> None:
    report_path = tmp_path / "handoff-001\nclient_secret=path-secret.json"
    report = {
        "run_id": "handoff-001",
        "story_number": "STRY0010013",
        "summary": {
            "total": "2\napi_key=total-secret",
            "attach_to_servicenow": "0\nclient_secret=attach-secret",
            "internal_evidence": "2\nclient_secret=internal-secret",
            "delivery_evidence": "0\nclient_secret=delivery-secret",
        },
        "decisions": [],
    }

    note = build_artifact_handoff_work_note(report=report, report_path=report_path)

    assert "path-secret" not in note
    assert "total-secret" not in note
    assert "attach-secret" not in note
    assert "internal-secret" not in note
    assert "delivery-secret" not in note
    assert "client_secret=***REDACTED***" in note
    assert "api_key=***REDACTED***" in note
    assert "\n" not in note


def test_handoff_work_note_bounds_untrusted_report_values(tmp_path: Path) -> None:
    report_path = tmp_path / f"handoff-001-{'A' * 2200}.json"
    report = {
        "run_id": "handoff-001",
        "story_number": "STRY0010013",
        "summary": {
            "total": f"2 {'B' * 2200}",
            "attach_to_servicenow": f"0 {'C' * 2200}",
            "internal_evidence": f"2 {'D' * 2200}",
            "delivery_evidence": f"0 {'E' * 2200}",
        },
        "decisions": [],
    }

    note = build_artifact_handoff_work_note(report=report, report_path=report_path)

    assert note.count("...[truncated]") == 5
    assert len(note) < 2800


def test_handoff_work_note_does_not_coerce_hostile_summary_values(tmp_path: Path) -> None:
    report = {
        "run_id": "handoff-001",
        "story_number": "STRY0010013",
        "summary": {
            "total": _HostileSummaryText("client_secret=summary-text-payload"),
            "attach_to_servicenow": _HostileSummaryValue(),
            "internal_evidence": 2,
            "delivery_evidence": None,
        },
        "decisions": [],
    }

    note = build_artifact_handoff_work_note(
        report=report,
        report_path=tmp_path / "handoff-001.json",
    )

    assert "summary-text-payload" not in note
    assert "summary-object-secret" not in note
    assert "total=[unsupported handoff summary value]" in note
    assert "attach_to_servicenow=[unsupported handoff summary value]" in note
    assert "internal_evidence=2" in note
    assert "delivery_evidence=None" in note


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
                "artifact_sha256": "b" * 64,
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
            "artifact_sha256": "b" * 64,
            "attachment_label": "Approved Update Set XML",
        }
    ]


def test_delivery_attachment_jobs_reject_hostile_text_without_coercion() -> None:
    report = {
        "run_id": "handoff-001",
        "story_number": _HostileAttachmentText("client_secret=story-payload"),
        "summary": {},
        "decisions": [
            {
                "artifact_kind": _HostileAttachmentValue(),
                "artifact_path": "artifacts/export.xml",
                "attach_to_servicenow": True,
                "delivery_contract": "reviewed_export",
                "artifact_sha256": "b" * 64,
                "service_now_attachment_label": "Approved Update Set XML",
            },
        ],
    }

    with pytest.raises(ValueError) as exc_info:
        delivery_attachment_jobs_from_report(report)

    assert str(exc_info.value) == "artifact_handoff_report_invalid"
    assert "story-payload" not in str(exc_info.value)
    assert "attachment-object-secret" not in str(exc_info.value)


def test_delivery_attachment_jobs_reject_hostile_attach_flag_without_truthiness() -> None:
    report = {
        "run_id": "handoff-001",
        "story_number": "STRY0010013",
        "summary": {},
        "decisions": [
            {
                "artifact_kind": "update_set_xml",
                "artifact_path": "artifacts/export.xml",
                "attach_to_servicenow": _HostileAttachFlag(),
                "delivery_contract": "reviewed_export",
                "artifact_sha256": "b" * 64,
                "service_now_attachment_label": "Approved Update Set XML",
            },
        ],
    }

    with pytest.raises(ValueError) as exc_info:
        delivery_attachment_jobs_from_report(report)

    assert str(exc_info.value) == "artifact_handoff_report_invalid"
    assert "attachment-flag-secret" not in str(exc_info.value)


def test_reviewed_delivery_artifact_job_records_contract_and_hash(
    tmp_path: Path,
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")

    job = build_reviewed_delivery_artifact_job(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path=export_path,
        reviewer_id="release-coordinator",
    )

    assert job["story_number"] == "STRY0010013"
    assert job["artifact_kind"] == "update_set_xml"
    assert job["artifact_path"] == str(export_path)
    assert job["approved_for_delivery"] is True
    assert job["delivery_contract"] == "reviewed_export"
    assert job["reviewer_id"] == "release-coordinator"
    assert len(str(job["artifact_sha256"])) == 64


def test_reviewed_delivery_artifact_job_validates_xml_without_whole_file_text_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")

    def fail_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        raise AssertionError(f"unexpected whole-file text read for {self}")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    job = build_reviewed_delivery_artifact_job(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path=export_path,
        reviewer_id="release-coordinator",
    )

    assert len(str(job["artifact_sha256"])) == 64


def test_reviewed_delivery_artifact_job_validates_xml_without_path_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")

    def fail_open(self: Path, *_args: object, **_kwargs: object) -> object:
        raise AssertionError(f"unexpected direct Path.open for {self}")

    monkeypatch.setattr(Path, "open", fail_open)

    job = build_reviewed_delivery_artifact_job(
        story_number="STRY0010013",
        artifact_kind=ArtifactKind.UPDATE_SET_XML,
        artifact_path=export_path,
        reviewer_id="release-manager",
    )

    assert len(str(job["artifact_sha256"])) == 64


def test_reviewed_delivery_artifact_job_rejects_internal_artifact_kind(
    tmp_path: Path,
) -> None:
    packet_path = tmp_path / "STRY0010013.json"
    packet_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")

    with pytest.raises(ValueError, match="delivery_artifact_kind_required"):
        build_reviewed_delivery_artifact_job(
            story_number="STRY0010013",
            artifact_kind=ArtifactKind.IMPLEMENTATION_PACKET,
            artifact_path=packet_path,
            reviewer_id="release-coordinator",
        )


def test_reviewed_delivery_artifact_job_rejects_smoke_placeholder_xml(
    tmp_path: Path,
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text(
        '<placeholder_update_set story_number="STRY0010013" />',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="reviewed_export_artifact_required"):
        build_reviewed_delivery_artifact_job(
            story_number="STRY0010013",
            artifact_kind=ArtifactKind.UPDATE_SET_XML,
            artifact_path=export_path,
            reviewer_id="release-coordinator",
        )


def test_reviewed_delivery_artifact_job_rejects_empty_update_set_xml(
    tmp_path: Path,
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")

    with pytest.raises(ValueError, match="reviewed_export_artifact_required"):
        build_reviewed_delivery_artifact_job(
            story_number="STRY0010013",
            artifact_kind=ArtifactKind.UPDATE_SET_XML,
            artifact_path=export_path,
            reviewer_id="release-coordinator",
        )
