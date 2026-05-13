import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from jedi_devproject.external_build import (
    ExternalBuildPipelineResult,
    ExternalBuildPipelineStatus,
    reviewed_delivery_jobs_from_build_result,
    writeback_job_from_build_result,
)


def test_successful_external_build_contract_produces_downstream_jobs(
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate.json"
    update_set_path = tmp_path / "STRY0010013.xml"
    evidence_path = tmp_path / "test-evidence.zip"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")
    update_set_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")
    evidence_path.write_text("test evidence", encoding="utf-8")
    result = ExternalBuildPipelineResult(
        story_number="STRY0010013",
        build_reference="build-20260513-010",
        status=ExternalBuildPipelineStatus.SUCCEEDED,
        candidate_artifact_path=candidate_path,
        reviewed_update_set_xml_path=update_set_path,
        test_evidence_path=evidence_path,
        build_actor_id="external-builder",
    )

    writeback_job = writeback_job_from_build_result(result, from_state="Work in Progress")
    delivery_jobs = reviewed_delivery_jobs_from_build_result(result)
    serialized = json.dumps(
        {
            "writeback_job": writeback_job,
            "delivery_jobs": delivery_jobs,
            "result": result.model_dump(mode="json"),
        }
    )

    assert writeback_job == {
        "story_number": "STRY0010013",
        "build_reference": "build-20260513-010",
        "artifact_url": str(candidate_path),
        "build_status": "succeeded",
        "from_state": "Work in Progress",
    }
    assert [job["artifact_kind"] for job in delivery_jobs] == [
        "update_set_xml",
        "test_evidence_bundle",
    ]
    assert all(job["approved_for_delivery"] is True for job in delivery_jobs)
    assert all(job["delivery_contract"] == "reviewed_export" for job in delivery_jobs)
    assert all(job["reviewer_id"] == "external-builder" for job in delivery_jobs)
    assert all(len(str(job["artifact_sha256"])) == 64 for job in delivery_jobs)
    assert "sys_id" not in serialized


def test_successful_external_build_requires_delivery_outputs(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")

    with pytest.raises(ValidationError) as exc:
        ExternalBuildPipelineResult(
            story_number="STRY0010013",
            build_reference="build-20260513-010",
            status=ExternalBuildPipelineStatus.SUCCEEDED,
            candidate_artifact_path=candidate_path,
            build_actor_id="external-builder",
        )

    assert "successful builds require reviewed delivery outputs" in str(exc.value)


def test_failed_external_build_contract_rejects_delivery_jobs(
    tmp_path: Path,
) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")
    result = ExternalBuildPipelineResult(
        story_number="STRY0010013",
        build_reference="build-20260513-010",
        status=ExternalBuildPipelineStatus.FAILED,
        candidate_artifact_path=candidate_path,
        build_actor_id="external-builder",
        failure_reasons=["unit tests failed"],
    )

    writeback_job = writeback_job_from_build_result(result, from_state="Work in Progress")

    assert writeback_job["build_status"] == "failed"
    with pytest.raises(ValueError, match="successful_build_required"):
        reviewed_delivery_jobs_from_build_result(result)


def test_external_build_contract_rejects_unknown_fields(tmp_path: Path) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")

    with pytest.raises(ValidationError):
        ExternalBuildPipelineResult.model_validate(
            {
                "story_number": "STRY0010013",
                "build_reference": "build-20260513-010",
                "status": ExternalBuildPipelineStatus.FAILED,
                "candidate_artifact_path": candidate_path,
                "build_actor_id": "external-builder",
                "failure_reasons": ["unit tests failed"],
                "story_sys_id": "must-not-be-accepted",
            }
        )
