import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from jedi_devproject.cli import main
from jedi_devproject.models import DataClassification, Story
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cli_smoke_prints_project_name(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--version"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "jedi-devproject-0" in captured.out
    assert "0.2.0" in captured.out


def test_cli_without_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "usage: jedi-devproject" in captured.out


def test_cli_run_local_processes_sample_stories(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample_path = tmp_path / "stories.json"
    artifact_root = tmp_path / "artifacts"
    sample_path.write_text(
        """
        [
          {
            "sys_id": "abc123",
            "number": "STORY0010001",
            "short_description": "Update portal help text",
            "description": "Change portal help text from Submit to Send.",
            "story_points": 2,
            "priority": 3,
            "state": "Ready",
            "data_classification": "public",
            "acceptance_criteria": "Portal help text shows Send.",
            "affected_tables": ["sp_instance"]
          }
        ]
        """,
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-local",
            "--sample-file",
            str(sample_path),
            "--artifact-root",
            str(artifact_root),
            "--run-id",
            "run-001",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "stories_processed=1" in captured.out
    assert "generated_candidates=1" in captured.out
    assert "enriched_stories=0" in captured.out
    assert "abc123" not in captured.out
    assert (artifact_root / "run-001" / "STORY0010001.json").exists()


def test_cli_run_local_accepts_single_story_object(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample_path = tmp_path / "story.json"
    artifact_root = tmp_path / "artifacts"
    sample_path.write_text(
        """
        {
          "sys_id": "abc123",
          "number": "STORY0010001",
          "short_description": "Update portal help text",
          "description": "Change portal help text from Submit to Send.",
          "story_points": 2,
          "priority": 3,
          "state": "Ready",
          "data_classification": "public",
          "acceptance_criteria": "Portal help text shows Send.",
          "affected_tables": ["sp_instance"]
        }
        """,
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-local",
            "--sample-file",
            str(sample_path),
            "--artifact-root",
            str(artifact_root),
            "--run-id",
            "run-001",
        ]
    )

    assert exit_code == 0
    assert "stories_processed=1" in capsys.readouterr().out
    assert (artifact_root / "run-001" / "STORY0010001.json").exists()


def test_cli_build_implementation_packet_writes_safe_review_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample_path = tmp_path / "story.json"
    artifact_root = tmp_path / "implementation-packets"
    sample_payload = {
        "sys_id": "abc123",
        "number": "STRY0010013",
        "short_description": "Add implementation notes to the story form",
        "description": (
            "Create a string field named u_ai_review_notes on rm_story and place it "
            "on the default story form so release coordinators can see automation "
            "notes before testing."
        ),
        "story_points": 3,
        "priority": 4,
        "state": "Ready",
        "data_classification": "public",
        "acceptance_criteria": (
            "The rm_story table has an active u_ai_review_notes string field labeled "
            "AI Review Notes. The field appears on the default story form below "
            "Acceptance criteria. Existing stories are not modified."
        ),
        "affected_tables": ["sys_dictionary", "sys_ui_form"],
        "additional_context": {
            "target_table": "rm_story",
            "field_name": "u_ai_review_notes",
        },
    }
    sample_path.write_text(json.dumps(sample_payload), encoding="utf-8")

    exit_code = main(
        [
            "build-implementation-packet",
            "--sample-file",
            str(sample_path),
            "--artifact-root",
            str(artifact_root),
            "--run-id",
            "packet-run-001",
        ]
    )

    captured = capsys.readouterr()
    artifact_path = artifact_root / "packet-run-001" / "STRY0010013.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    serialized_artifact = json.dumps(artifact)

    assert exit_code == 0
    assert "implementation_packets=1" in captured.out
    assert "abc123" not in captured.out
    assert artifact_path.exists()
    assert artifact["task"] == "generate_implementation_candidate"
    assert artifact["provider_id"] == "now-assist-native"
    assert artifact["story"]["number"] == "STRY0010013"
    assert "controls" in artifact
    assert artifact["output_contract"]["must_include_test_plan"] is True
    assert "sys_dictionary" in artifact["controls"]["allowed_tables"]
    assert "compliance" in artifact["context"]
    assert "abc123" not in serialized_artifact


def test_cli_build_implementation_packet_fetches_story_from_pdi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "implementation-packets"
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "build-implementation-packet",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--artifact-root",
                str(artifact_root),
                "--run-id",
                "packet-run-002",
            ]
        )

    captured = capsys.readouterr()
    artifact_path = artifact_root / "packet-run-002" / "STORY0010001.json"

    assert exit_code == 0
    assert fake_client.calls[0] == {"sysparm_query": "number=STRY0010013", "limit": 1}
    assert artifact_path.exists()
    assert "implementation_packets=1" in captured.out
    assert "abc123" not in captured.out
    assert "client-secret" not in captured.out


def test_cli_build_implementation_packet_fails_closed_when_pdi_story_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()
    fake_client.stories = []

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "build-implementation-packet",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY9999999",
                "--artifact-root",
                str(tmp_path / "implementation-packets"),
                "--run-id",
                "packet-run-003",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "implementation_packets=0" in captured.out
    assert "reason=no_stories_found" in captured.out
    assert "client-secret" not in captured.out


def test_cli_build_implementation_candidate_writes_validated_candidate_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    sample_path = tmp_path / "story.json"
    provider_response_path = tmp_path / "provider-response.json"
    artifact_root = tmp_path / "implementation-candidates"
    sample_payload = {
        "sys_id": "abc123",
        "number": "STRY0010013",
        "short_description": "Add implementation notes to the story form",
        "description": (
            "Create a string field named u_ai_review_notes on rm_story and place it "
            "on the default story form so release coordinators can see automation "
            "notes before testing."
        ),
        "story_points": 3,
        "priority": 4,
        "state": "Ready",
        "data_classification": "public",
        "acceptance_criteria": (
            "The rm_story table has an active u_ai_review_notes string field labeled "
            "AI Review Notes. The field appears on the default story form below "
            "Acceptance criteria. Existing stories are not modified."
        ),
        "affected_tables": ["sys_dictionary", "sys_ui_form"],
        "additional_context": {
            "target_table": "rm_story",
            "field_name": "u_ai_review_notes",
        },
    }
    provider_response = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": {
                    "name": "rm_story",
                    "element": "u_ai_review_notes",
                    "column_label": "AI Review Notes",
                },
            }
        ],
        "test_plan": ["Confirm AI Review Notes appears on the Story form."],
        "rollback_notes": ["Remove the field and form placement from the update set."],
    }
    sample_path.write_text(json.dumps(sample_payload), encoding="utf-8")
    provider_response_path.write_text(json.dumps(provider_response), encoding="utf-8")

    exit_code = main(
        [
            "build-implementation-candidate",
            "--sample-file",
            str(sample_path),
            "--provider-response-file",
            str(provider_response_path),
            "--artifact-root",
            str(artifact_root),
            "--run-id",
            "candidate-run-001",
        ]
    )

    captured = capsys.readouterr()
    artifact_path = artifact_root / "candidate-run-001" / "STRY0010013.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    serialized_artifact = json.dumps(artifact)

    assert exit_code == 0
    assert "implementation_candidates=1" in captured.out
    assert "abc123" not in captured.out
    assert artifact["story_number"] == "STRY0010013"
    assert artifact["status"] == "Ready for Review"
    assert artifact["changes"][0]["table"] == "sys_dictionary"
    assert artifact["artifact_hash"]
    assert "Rollback:" in artifact["reviewer_notes"][-1]
    assert "abc123" not in serialized_artifact


def test_cli_build_implementation_candidate_fetches_story_from_pdi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    provider_response_path = tmp_path / "provider-response.json"
    provider_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sp_instance",
                        "operation": "update",
                        "fields": {"description": "Change portal help text."},
                    }
                ],
                "test_plan": ["Confirm the portal text changed."],
                "rollback_notes": ["Restore the prior portal text."],
            }
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "implementation-candidates"
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "build-implementation-candidate",
                "--env-file",
                str(env_path),
                "--story-number",
                "STORY0010001",
                "--provider-response-file",
                str(provider_response_path),
                "--artifact-root",
                str(artifact_root),
                "--run-id",
                "candidate-run-003",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_client.calls[0] == {"sysparm_query": "number=STORY0010001", "limit": 1}
    assert (artifact_root / "candidate-run-003" / "STORY0010001.json").exists()
    assert "implementation_candidates=1" in captured.out
    assert "abc123" not in captured.out
    assert "client-secret" not in captured.out


def test_cli_build_implementation_candidate_rejects_unsafe_provider_response(
    tmp_path: Path,
) -> None:
    sample_path = tmp_path / "story.json"
    provider_response_path = tmp_path / "provider-response.json"
    artifact_root = tmp_path / "implementation-candidates"
    sample_path.write_text(
        json.dumps(
            {
                "sys_id": "abc123",
                "number": "STRY0010013",
                "short_description": "Add implementation notes to the story form",
                "description": (
                    "Create a string field named u_ai_review_notes on rm_story and "
                    "place it on the default story form."
                ),
                "story_points": 3,
                "priority": 4,
                "state": "Ready",
                "data_classification": "public",
                "acceptance_criteria": "The field appears on the default story form.",
                "affected_tables": ["sys_dictionary", "sys_ui_form"],
            }
        ),
        encoding="utf-8",
    )
    provider_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sys_user",
                        "operation": "update",
                        "fields": {"name": "bad"},
                    }
                ],
                "test_plan": ["Confirm the change."],
                "rollback_notes": ["Undo the change."],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="table not allowed: sys_user"):
        main(
            [
                "build-implementation-candidate",
                "--sample-file",
                str(sample_path),
                "--provider-response-file",
                str(provider_response_path),
                "--artifact-root",
                str(artifact_root),
                "--run-id",
                "candidate-run-002",
            ]
        )

    assert not (artifact_root / "candidate-run-002").exists()


def test_cli_run_implementation_candidates_processes_job_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    story_path = tmp_path / "story.json"
    provider_response_path = tmp_path / "provider-response.json"
    jobs_path = tmp_path / "implementation-jobs.json"
    artifact_root = tmp_path / "implementation-candidates"
    batch_report_root = tmp_path / "implementation-candidate-batches"
    story_path.write_text(
        json.dumps(
            {
                "sys_id": "abc123",
                "number": "STRY0010013",
                "short_description": "Add implementation notes to the story form",
                "description": (
                    "Create a string field named u_ai_review_notes on rm_story and "
                    "place it on the default story form."
                ),
                "story_points": 3,
                "priority": 4,
                "state": "Ready",
                "data_classification": "public",
                "acceptance_criteria": "The field appears on the default story form.",
                "affected_tables": ["sys_dictionary", "sys_ui_form"],
            }
        ),
        encoding="utf-8",
    )
    provider_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sys_dictionary",
                        "operation": "insert",
                        "fields": {
                            "name": "rm_story",
                            "element": "u_ai_review_notes",
                        },
                    }
                ],
                "test_plan": ["Confirm the field appears on the Story form."],
                "rollback_notes": ["Remove the field and form placement."],
            }
        ),
        encoding="utf-8",
    )
    jobs_path.write_text(
        json.dumps(
            [
                {
                    "sample_file": str(story_path),
                    "provider_response_file": str(provider_response_path),
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-implementation-candidates",
            "--jobs-file",
            str(jobs_path),
            "--artifact-root",
            str(artifact_root),
            "--batch-report-root",
            str(batch_report_root),
            "--run-id",
            "candidate-batch-001",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "total=1" in captured.out
    assert "built=1" in captured.out
    assert "blocked=0" in captured.out
    assert "abc123" not in captured.out
    assert (artifact_root / "candidate-batch-001" / "STRY0010013.json").exists()


def test_cli_run_implementation_candidates_writes_batch_report(
    tmp_path: Path,
) -> None:
    story_path = tmp_path / "story.json"
    provider_response_path = tmp_path / "provider-response.json"
    jobs_path = tmp_path / "implementation-jobs.json"
    artifact_root = tmp_path / "implementation-candidates"
    batch_report_root = tmp_path / "implementation-candidate-batches"
    story_path.write_text(
        json.dumps(
            {
                "sys_id": "abc123",
                "number": "STRY0010013",
                "short_description": "Add implementation notes to the story form",
                "description": (
                    "Create a string field named u_ai_review_notes on rm_story and "
                    "place it on the default story form."
                ),
                "story_points": 3,
                "priority": 4,
                "state": "Ready",
                "data_classification": "public",
                "acceptance_criteria": "The field appears on the default story form.",
                "affected_tables": ["sys_dictionary", "sys_ui_form"],
            }
        ),
        encoding="utf-8",
    )
    provider_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sys_dictionary",
                        "operation": "insert",
                        "fields": {
                            "name": "rm_story",
                            "element": "u_ai_review_notes",
                        },
                    }
                ],
                "test_plan": ["Confirm the field appears on the Story form."],
                "rollback_notes": ["Remove the field and form placement."],
            }
        ),
        encoding="utf-8",
    )
    jobs_path.write_text(
        json.dumps(
            [
                {
                    "sample_file": str(story_path),
                    "provider_response_file": str(provider_response_path),
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-implementation-candidates",
            "--jobs-file",
            str(jobs_path),
            "--artifact-root",
            str(artifact_root),
            "--batch-report-root",
            str(batch_report_root),
            "--run-id",
            "candidate-batch-001",
        ]
    )

    report_path = batch_report_root / "candidate-batch-001.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    serialized_report = json.dumps(report)

    assert exit_code == 0
    assert report["run_id"] == "candidate-batch-001"
    assert report["summary"] == {"total": 1, "built": 1, "blocked": 0}
    assert report["outcomes"] == [
        {
            "story_number": "STRY0010013",
            "status": "built",
            "candidate_artifact": str(
                artifact_root / "candidate-batch-001" / "STRY0010013.json"
            ),
        }
    ]
    assert "abc123" not in serialized_report


def test_cli_run_implementation_candidates_rejects_empty_job_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    jobs_path = tmp_path / "implementation-jobs.json"
    jobs_path.write_text("[]", encoding="utf-8")

    exit_code = main(
        [
            "run-implementation-candidates",
            "--jobs-file",
            str(jobs_path),
            "--artifact-root",
            str(tmp_path / "implementation-candidates"),
            "--batch-report-root",
            str(tmp_path / "implementation-candidate-batches"),
            "--run-id",
            "candidate-batch-empty",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "total=0" in captured.out
    assert "reason=no_jobs" in captured.out


def test_cli_run_implementation_candidates_isolates_failed_jobs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    good_story_path = tmp_path / "good-story.json"
    bad_story_path = tmp_path / "bad-story.json"
    good_response_path = tmp_path / "good-response.json"
    bad_response_path = tmp_path / "bad-response.json"
    jobs_path = tmp_path / "implementation-jobs.json"
    artifact_root = tmp_path / "implementation-candidates"
    batch_report_root = tmp_path / "implementation-candidate-batches"
    base_story = {
        "sys_id": "abc123",
        "short_description": "Add implementation notes to the story form",
        "description": (
            "Create a string field named u_ai_review_notes on rm_story and place it "
            "on the default story form."
        ),
        "story_points": 3,
        "priority": 4,
        "state": "Ready",
        "data_classification": "public",
        "acceptance_criteria": "The field appears on the default story form.",
        "affected_tables": ["sys_dictionary", "sys_ui_form"],
    }
    good_story_path.write_text(
        json.dumps({"number": "STRY0010013", **base_story}),
        encoding="utf-8",
    )
    bad_story_path.write_text(
        json.dumps({"number": "STRY0010014", **base_story}),
        encoding="utf-8",
    )
    good_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sys_dictionary",
                        "operation": "insert",
                        "fields": {
                            "name": "rm_story",
                            "element": "u_ai_review_notes",
                        },
                    }
                ],
                "test_plan": ["Confirm the field appears on the Story form."],
                "rollback_notes": ["Remove the field and form placement."],
            }
        ),
        encoding="utf-8",
    )
    bad_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sys_user",
                        "operation": "update",
                        "fields": {"name": "bad"},
                    }
                ],
                "test_plan": ["Confirm the change."],
                "rollback_notes": ["Undo the change."],
            }
        ),
        encoding="utf-8",
    )
    jobs_path.write_text(
        json.dumps(
            [
                {
                    "sample_file": str(good_story_path),
                    "provider_response_file": str(good_response_path),
                },
                {
                    "sample_file": str(bad_story_path),
                    "provider_response_file": str(bad_response_path),
                },
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "run-implementation-candidates",
            "--jobs-file",
            str(jobs_path),
            "--artifact-root",
            str(artifact_root),
            "--batch-report-root",
            str(batch_report_root),
            "--run-id",
            "candidate-batch-002",
        ]
    )

    captured = capsys.readouterr()
    report = json.loads(
        (batch_report_root / "candidate-batch-002.json").read_text(encoding="utf-8")
    )
    serialized_report = json.dumps(report)

    assert exit_code == 1
    assert "total=2" in captured.out
    assert "built=1" in captured.out
    assert "blocked=1" in captured.out
    assert (artifact_root / "candidate-batch-002" / "STRY0010013.json").exists()
    assert not (artifact_root / "candidate-batch-002" / "STRY0010014.json").exists()
    assert report["summary"] == {"total": 2, "built": 1, "blocked": 1}
    assert report["outcomes"][1]["story_number"] == "STRY0010014"
    assert report["outcomes"][1]["status"] == "blocked"
    assert "table not allowed" in report["outcomes"][1]["reason"]
    assert "abc123" not in serialized_report


def test_cli_run_lifecycle_smoke_builds_artifacts_and_plans_writeback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    provider_response_path = tmp_path / "provider-response.json"
    provider_response_path.write_text(
        json.dumps(
            {
                "changes": [
                    {
                        "table": "sp_instance",
                        "operation": "update",
                        "fields": {"description": "Change portal help text."},
                    }
                ],
                "test_plan": ["Confirm the portal text changed."],
                "rollback_notes": ["Restore the prior portal text."],
            }
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "artifacts"
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "run-lifecycle-smoke",
                "--env-file",
                str(env_path),
                "--story-number",
                "STORY0010001",
                "--provider-response-file",
                str(provider_response_path),
                "--artifact-root",
                str(artifact_root),
                "--run-id",
                "lifecycle-smoke-001",
                "--build-reference",
                "build-lifecycle-smoke-001",
                "--from-state",
                "Ready",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "packet_built=1" in captured.out
    assert "candidate_built=1" in captured.out
    assert "writeback_allowed=True" in captured.out
    assert "writeback_applied=False" in captured.out
    assert "abc123" not in captured.out
    assert "client-secret" not in captured.out
    assert fake_client.updated_fields == []
    assert (
        artifact_root
        / "implementation-packets"
        / "lifecycle-smoke-001"
        / "STORY0010001.json"
    ).exists()
    assert (
        artifact_root
        / "implementation-candidates"
        / "lifecycle-smoke-001"
        / "STORY0010001.json"
    ).exists()
    assert (
        artifact_root
        / "implementation-candidate-batches"
        / "lifecycle-smoke-001.json"
    ).exists()
    manifest_path = (
        artifact_root
        / "lifecycle-manifests"
        / "lifecycle-smoke-001.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["story_number"] == "STORY0010001"
    assert manifest["build_reference"] == "build-lifecycle-smoke-001"
    assert "implementation_packet" in manifest["artifacts"]
    assert "implementation_candidate" in manifest["artifacts"]
    assert "implementation_candidate_batch" in manifest["artifacts"]
    assert manifest["writeback"]["allowed"] is True
    assert manifest["writeback"]["applied"] is False
    assert "abc123" not in json.dumps(manifest)


def test_cli_run_lifecycle_smoke_fails_closed_when_story_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    provider_response_path = tmp_path / "provider-response.json"
    provider_response_path.write_text(
        json.dumps(
            {
                "changes": [],
                "test_plan": ["Confirm no implementation was generated."],
                "rollback_notes": ["No rollback required."],
            }
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "artifacts"
    fake_client = FakeServiceNowClient()
    fake_client.stories = []

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "run-lifecycle-smoke",
                "--env-file",
                str(env_path),
                "--story-number",
                "STORY9999999",
                "--provider-response-file",
                str(provider_response_path),
                "--artifact-root",
                str(artifact_root),
                "--run-id",
                "lifecycle-smoke-missing",
                "--build-reference",
                "build-lifecycle-smoke-missing",
                "--from-state",
                "Ready",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "packet_built=0" in captured.out
    assert "candidate_built=0" in captured.out
    assert "reason=no_stories_found" in captured.out
    assert "client-secret" not in captured.out
    assert not artifact_root.exists()


class FakeServiceNowClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.updated_fields: list[dict[str, object]] = []
        self.created_dictionary_fields: list[dict[str, object]] = []
        self.upserted_table_records: list[dict[str, object]] = []
        self.attached_files: list[dict[str, object]] = []
        self.ai_status = "Ready for Testing"
        self.build_reference = "build-20260513-001"
        self.candidate_artifact = "artifacts/STORY0010001.json"
        self.stories = [
            Story(
                sys_id="abc123",
                number="STORY0010001",
                short_description="Update portal help text",
                description="Change portal help text from Submit to Send.",
                story_points=2,
                priority=3,
                state="Ready",
                data_classification=DataClassification.PUBLIC,
                acceptance_criteria="Portal help text shows Send.",
                affected_tables=["sp_instance"],
                additional_context={
                    "u_ai_status": self.ai_status,
                    "u_ai_build_reference": self.build_reference,
                    "u_ai_candidate_artifact": self.candidate_artifact,
                },
            )
        ]
        self.dictionary_fields = [
            StoryDictionaryField(
                element="state",
                column_label="State",
                internal_type="choice",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_status",
                column_label="AI Status",
                internal_type="string",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_build_reference",
                column_label="AI Build Reference",
                internal_type="string",
                active=True,
            ),
            StoryDictionaryField(
                element="u_ai_candidate_artifact",
                column_label="AI Candidate Artifact",
                internal_type="string",
                active=True,
            ),
        ]

    def fetch_ready_stories(
        self,
        project_sys_id: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        self.calls.append({"project_sys_id": project_sys_id, "limit": limit})
        return self.stories

    def fetch_stories(
        self,
        sysparm_query: str | None = None,
        *,
        limit: int = 100,
    ) -> list[Story]:
        self.calls.append({"sysparm_query": sysparm_query, "limit": limit})
        return self.fetch_ready_stories(limit=limit)

    def fetch_story_state_choices(self) -> list[StoryStateChoice]:
        self.calls.append({"fetch_story_state_choices": True})
        return [
            StoryStateChoice(
                label="Ready for Testing",
                value="-7",
                sequence=50,
                inactive=False,
            )
        ]

    def fetch_story_dictionary_fields(self) -> list[StoryDictionaryField]:
        self.calls.append({"fetch_story_dictionary_fields": True})
        return self.dictionary_fields

    def create_story_dictionary_field(
        self,
        *,
        element: str,
        column_label: str,
        internal_type: str,
        max_length: int | None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "element": element,
            "column_label": column_label,
            "internal_type": internal_type,
            "max_length": max_length,
        }
        self.created_dictionary_fields.append(payload)
        return payload

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> None:
        self.updated_fields.append({"story_sys_id": story_sys_id, "fields": fields})
        story = self.stories[0]
        self.stories[0] = story.model_copy(
            update={
                "state": str(fields.get("state", story.state)),
                "additional_context": {
                    **story.additional_context,
                    **{
                        key: str(fields[key])
                        for key in [
                            "u_ai_status",
                            "u_ai_build_reference",
                            "u_ai_candidate_artifact",
                        ]
                        if key in fields
                    },
                },
            }
        )

    def upsert_table_record(
        self,
        *,
        table: str,
        lookup: dict[str, str],
        fields: dict[str, object],
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "table": table,
            "lookup": lookup,
            "fields": fields,
        }
        self.upserted_table_records.append(payload)
        return {"sys_id": f"{table}-sys-id"}

    def attach_story_file(
        self,
        story_sys_id: str,
        *,
        file_path: Path,
        file_name: str,
        content_type: str,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "story_sys_id": story_sys_id,
            "file_path": str(file_path),
            "file_name": file_name,
            "content_type": content_type,
        }
        self.attached_files.append(payload)
        return {"sys_id": f"attachment-{len(self.attached_files)}"}


def test_cli_run_pdi_fetches_stories_and_prints_safe_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "artifacts"
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "run-pdi",
                "--env-file",
                str(env_path),
                "--artifact-root",
                str(artifact_root),
                "--run-id",
                "run-001",
                "--limit",
                "7",
                "--project-sys-id",
                "project-123",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert fake_client.calls == [{"project_sys_id": "project-123", "limit": 7}]
    assert "stories_processed=1" in captured.out
    assert "generated_candidates=1" in captured.out
    assert "abc123" not in captured.out
    assert "client-secret" not in captured.out
    assert (artifact_root / "run-001" / "STORY0010001.json").exists()


def test_cli_run_pdi_uses_optional_sysparm_query(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "run-pdi",
                "--env-file",
                str(env_path),
                "--artifact-root",
                str(tmp_path / "artifacts"),
                "--run-id",
                "run-002",
                "--limit",
                "1",
                "--sysparm-query",
                "active=true",
            ]
        )

    assert exit_code == 0
    assert fake_client.calls[0] == {"sysparm_query": "active=true", "limit": 1}
    assert "stories_processed=1" in capsys.readouterr().out


def test_cli_plan_writeback_dry_run_uses_instance_state_mapping_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-001",
                "--artifact-url",
                "artifacts/STRY0010013.json",
                "--from-state",
                "Ready",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert fake_client.calls[0] == {"sysparm_query": "number=STRY0010013", "limit": 1}
    assert fake_client.calls[-2:] == [
        {"fetch_story_state_choices": True},
        {"fetch_story_dictionary_fields": True},
    ]
    assert fake_client.updated_fields == []
    assert "story_number=STORY0010001" in captured.out
    assert "allowed=True" in captured.out
    assert "state=-7" in captured.out
    assert "client-secret" not in captured.out
    assert "abc123" not in captured.out


def test_cli_plan_writeback_fails_closed_when_required_fields_are_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()
    fake_client.dictionary_fields = [
        StoryDictionaryField(
            element="state",
            column_label="State",
            internal_type="choice",
            active=True,
        )
    ]

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-001",
                "--from-state",
                "Ready",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert fake_client.updated_fields == []
    assert "allowed=False" in captured.out
    assert "missing" in captured.out
    assert "u_ai_status" in captured.out


def test_cli_plan_writeback_apply_requires_matching_story_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-001",
                "--from-state",
                "Ready",
                "--apply",
                "--confirm-story-number",
                "WRONG001",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert fake_client.updated_fields == []
    assert "applied=False" in captured.out
    assert "confirmation_mismatch" in captured.out


def test_cli_plan_writeback_apply_requires_operator_and_audit_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-001",
                "--from-state",
                "Ready",
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert fake_client.updated_fields == []
    assert "applied=False" in captured.out
    assert "actor_identity_required" in captured.out


def test_cli_plan_writeback_apply_updates_story_after_validation_and_confirmation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-001",
                "--artifact-url",
                "artifacts/STRY0010013.json",
                "--from-state",
                "Ready",
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-type",
                "service",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--execution-id",
                "run-20260513-001",
                "--audit-root",
                str(tmp_path / "writeback-audit"),
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert fake_client.updated_fields == [
        {
            "story_sys_id": "abc123",
            "fields": {
                "state": "-7",
                "u_ai_status": "Ready for Testing",
                "u_ai_build_reference": "build-20260513-001",
                "u_ai_candidate_artifact": "artifacts/STRY0010013.json",
                "work_notes": (
                    "External build completed. "
                    "Build reference: build-20260513-001."
                ),
            },
        }
    ]
    assert "applied=True" in captured.out
    assert "abc123" not in captured.out
    audit_path = (
        tmp_path
        / "writeback-audit"
        / "STORY0010001-build-20260513-001.json"
    )
    assert audit_path.exists()


def test_cli_plan_writeback_apply_writes_lifecycle_manifest_when_requested(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    packet_path = tmp_path / "packet.json"
    candidate_path = tmp_path / "candidate.json"
    packet_path.write_text(json.dumps({"story": {"number": "STORY0010001"}}), encoding="utf-8")
    candidate_path.write_text(
        json.dumps({"story_number": "STORY0010001", "artifact_hash": "abc"}),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-003",
                "--artifact-url",
                "artifacts/STRY0010013.json",
                "--from-state",
                "Ready",
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-type",
                "service",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--execution-id",
                "run-20260513-003",
                "--audit-root",
                str(tmp_path / "writeback-audit"),
                "--manifest-root",
                str(tmp_path / "lifecycle-manifests"),
                "--packet-path",
                str(packet_path),
                "--candidate-path",
                str(candidate_path),
            ]
        )

    captured = capsys.readouterr()
    manifest_path = tmp_path / "lifecycle-manifests" / "run-20260513-003.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "lifecycle_manifest_written=True" in captured.out
    assert manifest["story_number"] == "STORY0010001"
    assert manifest["build_reference"] == "build-20260513-003"
    assert manifest["artifacts"]["implementation_packet"]["sha256"]
    assert manifest["artifacts"]["implementation_candidate"]["sha256"]
    assert manifest["artifacts"]["writeback_audit"]["sha256"]
    assert manifest["writeback"]["applied"] is True
    assert manifest["verification"]["verified"] is True
    assert "sys_id" not in json.dumps(manifest)


def test_cli_plan_writeback_apply_accepts_manual_human_actor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STRY0010013",
                "--build-reference",
                "build-20260513-002",
                "--from-state",
                "Ready",
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-type",
                "human",
                "--actor-id",
                "operator@example.gov",
                "--audit-root",
                str(tmp_path / "writeback-audit"),
            ]
        )

    assert exit_code == 0
    assert "applied=True" in capsys.readouterr().out


def test_cli_check_writeback_capability_reports_ready_instance(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "check-writeback-capability",
                "--env-file",
                str(env_path),
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "allowed=True" in captured.out
    assert "ready_for_testing_state=-7" in captured.out
    assert "client-secret" not in captured.out


def test_cli_verify_writeback_reports_verified_remote_story(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()
    fake_client.stories[0] = fake_client.stories[0].model_copy(update={"state": "-7"})

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "verify-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STORY0010001",
                "--build-reference",
                "build-20260513-001",
                "--artifact-url",
                "artifacts/STORY0010001.json",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "verified=True" in captured.out
    assert "state=-7" in captured.out
    assert "u_ai_status=Ready for Testing" in captured.out
    assert "abc123" not in captured.out
    assert "client-secret" not in captured.out


def test_cli_record_lifecycle_manifest_writes_phase_manifest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    packet_path = tmp_path / "packet.json"
    candidate_path = tmp_path / "candidate.json"
    audit_path = tmp_path / "audit.json"
    for path, payload in [
        (packet_path, {"story": {"number": "STRY0010013"}}),
        (candidate_path, {"story_number": "STRY0010013", "artifact_hash": "abc"}),
        (audit_path, {"story_number": "STRY0010013", "applied": True}),
    ]:
        path.write_text(json.dumps(payload), encoding="utf-8")
    manifest_root = tmp_path / "lifecycle-manifests"

    exit_code = main(
        [
            "record-lifecycle-manifest",
            "--run-id",
            "lifecycle-001",
            "--story-number",
            "STRY0010013",
            "--build-reference",
            "build-20260513-001",
            "--packet-path",
            str(packet_path),
            "--candidate-path",
            str(candidate_path),
            "--writeback-audit-path",
            str(audit_path),
            "--verification-verified",
            "--verification-state",
            "-7",
            "--manifest-root",
            str(manifest_root),
        ]
    )

    captured = capsys.readouterr()
    manifest_path = manifest_root / "lifecycle-001.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "lifecycle_manifest_written=True" in captured.out
    assert "STRY0010013" in captured.out
    assert manifest["artifacts"]["implementation_packet"]["sha256"]
    assert manifest["verification"]["verified"] is True
    assert "sys_id" not in json.dumps(manifest)


def test_cli_process_external_build_result_writes_writeback_and_delivery_jobs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate_path = tmp_path / "candidate.json"
    update_set_path = tmp_path / "STRY0010013.xml"
    evidence_path = tmp_path / "test-evidence.zip"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")
    update_set_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")
    evidence_path.write_text("test evidence", encoding="utf-8")
    result_path = tmp_path / "build-result.json"
    result_path.write_text(
        json.dumps(
            {
                "story_number": "STRY0010013",
                "build_reference": "build-20260513-010",
                "status": "succeeded",
                "candidate_artifact_path": str(candidate_path),
                "reviewed_update_set_xml_path": str(update_set_path),
                "test_evidence_path": str(evidence_path),
                "build_actor_id": "external-builder",
            }
        ),
        encoding="utf-8",
    )
    writeback_root = tmp_path / "writeback-jobs"
    delivery_root = tmp_path / "delivery-jobs"

    exit_code = main(
        [
            "process-external-build-result",
            "--result-file",
            str(result_path),
            "--from-state",
            "Work in Progress",
            "--run-id",
            "external-build-001",
            "--writeback-job-root",
            str(writeback_root),
            "--delivery-job-root",
            str(delivery_root),
        ]
    )

    captured = capsys.readouterr()
    writeback_jobs = json.loads((writeback_root / "external-build-001.json").read_text())
    delivery_jobs = json.loads((delivery_root / "external-build-001.json").read_text())

    assert exit_code == 0
    assert "writeback_jobs=1" in captured.out
    assert "reviewed_delivery_jobs=2" in captured.out
    assert writeback_jobs == [
        {
            "story_number": "STRY0010013",
            "build_reference": "build-20260513-010",
            "artifact_url": str(candidate_path),
            "build_status": "succeeded",
            "from_state": "Work in Progress",
        }
    ]
    assert [job["artifact_kind"] for job in delivery_jobs] == [
        "update_set_xml",
        "test_evidence_bundle",
    ]
    assert all(job["delivery_contract"] == "reviewed_export" for job in delivery_jobs)
    assert "sys_id" not in json.dumps({"writeback": writeback_jobs, "delivery": delivery_jobs})


def test_cli_process_failed_external_build_result_writes_only_writeback_job(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate_path = tmp_path / "candidate.json"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")
    result_path = tmp_path / "build-result.json"
    result_path.write_text(
        json.dumps(
            {
                "story_number": "STRY0010013",
                "build_reference": "build-20260513-010",
                "status": "failed",
                "candidate_artifact_path": str(candidate_path),
                "build_actor_id": "external-builder",
                "failure_reasons": ["unit tests failed"],
            }
        ),
        encoding="utf-8",
    )
    writeback_root = tmp_path / "writeback-jobs"
    delivery_root = tmp_path / "delivery-jobs"

    exit_code = main(
        [
            "process-external-build-result",
            "--result-file",
            str(result_path),
            "--from-state",
            "Work in Progress",
            "--run-id",
            "external-build-001",
            "--writeback-job-root",
            str(writeback_root),
            "--delivery-job-root",
            str(delivery_root),
        ]
    )

    captured = capsys.readouterr()
    writeback_jobs = json.loads((writeback_root / "external-build-001.json").read_text())

    assert exit_code == 0
    assert "writeback_jobs=1" in captured.out
    assert "reviewed_delivery_jobs=0" in captured.out
    assert writeback_jobs[0]["build_status"] == "failed"
    assert not (delivery_root / "external-build-001.json").exists()


def test_cli_process_lifecycle_event_writes_story_ready_plan(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    event_path = tmp_path / "story-ready-event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_id": "evt-20260513-001",
                "event_type": "story_state_changed",
                "source": "servicenow-business-rule",
                "table": "rm_story",
                "story_number": "STRY0010013",
                "previous_state": "Draft",
                "current_state": "Ready",
                "occurred_at": "2026-05-13T15:45:00Z",
                "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
                "emitted_by": "jedi-devproject-lifecycle-integration",
            }
        ),
        encoding="utf-8",
    )
    plan_root = tmp_path / "lifecycle-event-plans"

    exit_code = main(
        [
            "process-lifecycle-event",
            "--event-file",
            str(event_path),
            "--run-id",
            "lifecycle-event-001",
            "--plan-root",
            str(plan_root),
        ]
    )

    captured = capsys.readouterr()
    plan_path = plan_root / "lifecycle-event-001.json"
    payload = json.loads(plan_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "lifecycle_event_plans=1" in captured.out
    assert "should_evaluate=True" in captured.out
    assert "claim_state=Work in Progress" in captured.out
    assert payload["event"]["story_number"] == "STRY0010013"
    assert payload["event"]["event_id"] == "evt-20260513-001"
    assert payload["plan"]["lifecycle_action"] == "evaluate_story"
    assert payload["plan"]["claim_state"] == "Work in Progress"
    assert payload["plan"]["idempotency_key"] == "evt-20260513-001"
    assert "story_sys_id" not in json.dumps(payload)


def test_cli_process_lifecycle_event_fails_closed_for_invalid_event(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    event_path = tmp_path / "invalid-event.json"
    event_path.write_text(
        json.dumps(
            {
                "event_id": "evt-20260513-001",
                "event_type": "story_state_changed",
                "source": "servicenow-business-rule",
                "table": "rm_story",
                "story_number": "STRY0010013",
                "previous_state": "Draft",
                "current_state": "Ready",
                "occurred_at": "2026-05-13T15:45:00Z",
                "correlation_id": "STRY0010013-Draft-Ready-20260513T154500Z",
                "emitted_by": "jedi-devproject-lifecycle-integration",
                "story_sys_id": "must-not-cross-this-boundary",
            }
        ),
        encoding="utf-8",
    )
    plan_root = tmp_path / "lifecycle-event-plans"

    exit_code = main(
        [
            "process-lifecycle-event",
            "--event-file",
            str(event_path),
            "--run-id",
            "lifecycle-event-001",
            "--plan-root",
            str(plan_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "lifecycle_event_plans=0" in captured.out
    assert "reason=invalid_lifecycle_event" in captured.out
    assert not (plan_root / "lifecycle-event-001.json").exists()


def test_cli_plan_artifact_handoff_writes_decision_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate_path = tmp_path / "STRY0010013.json"
    export_path = tmp_path / "STRY0010013.xml"
    candidate_path.write_text('{"story_number":"STRY0010013"}', encoding="utf-8")
    export_path.write_text("<unload/>", encoding="utf-8")
    jobs_path = tmp_path / "handoff-jobs.json"
    jobs_path.write_text(
        json.dumps(
            [
                {
                    "artifact_kind": "implementation_candidate",
                    "artifact_path": str(candidate_path),
                    "approved_for_delivery": False,
                },
                {
                    "artifact_kind": "update_set_xml",
                    "artifact_path": str(export_path),
                    "approved_for_delivery": True,
                    "delivery_contract": "reviewed_export",
                },
            ]
        ),
        encoding="utf-8",
    )
    report_root = tmp_path / "handoff-reports"

    exit_code = main(
        [
            "plan-artifact-handoff",
            "--run-id",
            "handoff-001",
            "--story-number",
            "STRY0010013",
            "--jobs-file",
            str(jobs_path),
            "--report-root",
            str(report_root),
        ]
    )

    captured = capsys.readouterr()
    report_path = report_root / "handoff-001.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "handoff_plans=2" in captured.out
    assert "attach_to_servicenow=1" in captured.out
    assert report["summary"]["delivery_evidence"] == 1
    assert len(report["decisions"][0]["artifact_sha256"]) == 64
    assert report["decisions"][1]["service_now_attachment_label"] == (
        "Approved Update Set XML"
    )
    assert "sys_id" not in json.dumps(report)


def test_cli_review_delivery_artifact_writes_handoff_job(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload><sys_update_xml /></unload>", encoding="utf-8")
    job_root = tmp_path / "reviewed-delivery-jobs"

    exit_code = main(
        [
            "review-delivery-artifact",
            "--run-id",
            "reviewed-export-001",
            "--story-number",
            "STRY0010013",
            "--artifact-kind",
            "update_set_xml",
            "--artifact-path",
            str(export_path),
            "--reviewer-id",
            "release-coordinator",
            "--job-root",
            str(job_root),
        ]
    )

    captured = capsys.readouterr()
    job_path = job_root / "reviewed-export-001.json"
    jobs = json.loads(job_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "reviewed_delivery_artifacts=1" in captured.out
    assert jobs == [
        {
            "story_number": "STRY0010013",
            "artifact_kind": "update_set_xml",
            "artifact_path": str(export_path),
            "approved_for_delivery": True,
            "delivery_contract": "reviewed_export",
            "reviewer_id": "release-coordinator",
            "artifact_sha256": jobs[0]["artifact_sha256"],
        }
    ]
    assert len(jobs[0]["artifact_sha256"]) == 64


def test_cli_review_delivery_artifact_fails_closed_for_placeholder_xml(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text(
        '<placeholder_update_set story_number="STRY0010013" />',
        encoding="utf-8",
    )
    job_root = tmp_path / "reviewed-delivery-jobs"

    exit_code = main(
        [
            "review-delivery-artifact",
            "--run-id",
            "reviewed-export-001",
            "--story-number",
            "STRY0010013",
            "--artifact-kind",
            "update_set_xml",
            "--artifact-path",
            str(export_path),
            "--reviewer-id",
            "release-coordinator",
            "--job-root",
            str(job_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reviewed_delivery_artifacts=0" in captured.out
    assert "reason=reviewed_export_artifact_required" in captured.out
    assert not (job_root / "reviewed-export-001.json").exists()


def test_cli_review_delivery_artifact_fails_closed_for_empty_update_set_xml(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    job_root = tmp_path / "reviewed-delivery-jobs"

    exit_code = main(
        [
            "review-delivery-artifact",
            "--run-id",
            "reviewed-export-001",
            "--story-number",
            "STRY0010013",
            "--artifact-kind",
            "update_set_xml",
            "--artifact-path",
            str(export_path),
            "--reviewer-id",
            "release-coordinator",
            "--job-root",
            str(job_root),
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reviewed_delivery_artifacts=0" in captured.out
    assert "reason=reviewed_export_artifact_required" in captured.out
    assert not (job_root / "reviewed-export-001.json").exists()


def test_cli_write_artifact_handoff_summary_updates_work_notes_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 2,
                    "attach_to_servicenow": 0,
                    "internal_evidence": 2,
                    "delivery_evidence": 0,
                },
                "decisions": [],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "write-artifact-handoff-summary",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-id",
                "svc-jedi-orchestrator",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "handoff_summary_written=True" in captured.out
    assert fake_client.updated_fields == [
        {
            "story_sys_id": "abc123",
            "fields": {
                "work_notes": (
                    "Artifact handoff planned. Report: "
                    f"{report_path}. total=2 attach_to_servicenow=0 "
                    "internal_evidence=2 delivery_evidence=0."
                )
            },
        }
    ]
    updated_fields = fake_client.updated_fields[0]["fields"]
    assert isinstance(updated_fields, dict)
    assert "state" not in updated_fields
    assert "abc123" not in captured.out


def test_cli_write_artifact_handoff_summary_dry_run_does_not_mutate(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 0,
                    "internal_evidence": 1,
                    "delivery_evidence": 0,
                },
                "decisions": [],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "write-artifact-handoff-summary",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
            ]
        )

    assert exit_code == 0
    assert "handoff_summary_written=False" in capsys.readouterr().out
    assert fake_client.updated_fields == []


def test_cli_attach_delivery_artifacts_dry_run_does_not_attach(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "delivery_contract": "reviewed_export",
                        "artifact_sha256": _sha256(export_path),
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "delivery_attachments_planned=1" in captured.out
    assert "delivery_attachments_applied=0" in captured.out
    assert fake_client.attached_files == []


def test_cli_attach_delivery_artifacts_requires_confirmation_to_apply(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "delivery_contract": "reviewed_export",
                        "artifact_sha256": _sha256(export_path),
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--audit-root",
                str(tmp_path / "attachment-audit"),
                "--run-id",
                "attach-001",
            ]
        )

    captured = capsys.readouterr()
    audit_path = tmp_path / "attachment-audit" / "attach-001.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "delivery_attachments_applied=1" in captured.out
    assert fake_client.attached_files == [
        {
            "story_sys_id": "abc123",
            "file_path": str(export_path),
            "file_name": "Approved Update Set XML - STRY0010013.xml",
            "content_type": "application/xml",
        }
    ]
    assert audit["story_number"] == "STORY0010001"
    assert audit["actor_id"] == "svc-jedi-orchestrator"
    assert audit["attachments"][0]["attachment_sys_id"] == "attachment-1"
    assert fake_client.updated_fields == []
    assert "abc123" not in captured.out


def test_cli_attach_delivery_artifacts_dry_run_blocks_hash_mismatch(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    reviewed_hash = _sha256(export_path)
    export_path.write_text("<unload><mutated /></unload>", encoding="utf-8")
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "delivery_contract": "reviewed_export",
                        "artifact_sha256": reviewed_hash,
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reason=artifact_hash_mismatch" in captured.out
    assert fake_client.attached_files == []


def test_cli_attach_delivery_artifacts_dry_run_blocks_missing_artifact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "missing-STRY0010013.xml"
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "delivery_contract": "reviewed_export",
                        "artifact_sha256": "0" * 64,
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reason=artifact_missing" in captured.out
    assert fake_client.attached_files == []


def test_cli_attach_delivery_artifacts_blocks_hash_mismatch_before_attachment(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    reviewed_hash = _sha256(export_path)
    export_path.write_text("<unload><mutated /></unload>", encoding="utf-8")
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "delivery_contract": "reviewed_export",
                        "artifact_sha256": reviewed_hash,
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--audit-root",
                str(tmp_path / "attachment-audit"),
                "--run-id",
                "attach-001",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reason=artifact_hash_mismatch" in captured.out
    assert fake_client.attached_files == []


def test_cli_attach_delivery_artifacts_blocks_existing_audit_before_attachment(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "delivery_contract": "reviewed_export",
                        "artifact_sha256": _sha256(export_path),
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    audit_root = tmp_path / "attachment-audit"
    audit_root.mkdir()
    (audit_root / "attach-001.json").write_text("{}", encoding="utf-8")
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--audit-root",
                str(audit_root),
                "--run-id",
                "attach-001",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reason=attachment_audit_already_exists" in captured.out
    assert fake_client.attached_files == []


def test_cli_attach_delivery_artifacts_blocks_legacy_report_without_delivery_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    export_path = tmp_path / "STRY0010013.xml"
    export_path.write_text("<unload/>", encoding="utf-8")
    report_path = tmp_path / "handoff-001.json"
    report_path.write_text(
        json.dumps(
            {
                "run_id": "handoff-001",
                "story_number": "STORY0010001",
                "summary": {
                    "total": 1,
                    "attach_to_servicenow": 1,
                    "internal_evidence": 0,
                    "delivery_evidence": 1,
                },
                "decisions": [
                    {
                        "artifact_kind": "update_set_xml",
                        "artifact_path": str(export_path),
                        "attach_to_servicenow": True,
                        "service_now_attachment_label": "Approved Update Set XML",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "attach-delivery-artifacts",
                "--env-file",
                str(env_path),
                "--report-file",
                str(report_path),
                "--apply",
                "--confirm-story-number",
                "STORY0010001",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--audit-root",
                str(tmp_path / "attachment-audit"),
                "--run-id",
                "attach-001",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "reason=delivery_contract_required" in captured.out
    assert fake_client.attached_files == []


def test_cli_run_delivery_artifact_smoke_creates_placeholder_and_plans_attachment(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_root = tmp_path / "delivery-smoke"

    exit_code = main(
        [
            "run-delivery-artifact-smoke",
            "--run-id",
            "delivery-smoke-001",
            "--story-number",
            "STRY0010013",
            "--artifact-root",
            str(artifact_root),
        ]
    )

    captured = capsys.readouterr()
    export_path = artifact_root / "exports" / "delivery-smoke-001" / "STRY0010013.xml"
    report_path = (
        artifact_root
        / "artifact-handoff-reports"
        / "delivery-smoke-001.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "delivery_artifact_created=True" in captured.out
    assert "delivery_attachments_planned=0" in captured.out
    assert "delivery_attachments_applied=0" in captured.out
    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8").startswith("<placeholder_update_set")
    assert report["summary"]["attach_to_servicenow"] == 0
    assert report["decisions"][0]["artifact_kind"] == "update_set_xml"
    assert report["decisions"][0]["delivery_contract"] == "smoke_placeholder"
    assert len(report["decisions"][0]["artifact_sha256"]) == 64
    assert "sys_id" not in json.dumps(report)


def test_cli_run_reviewed_delivery_smoke_creates_reviewed_handoff_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact_root = tmp_path / "reviewed-delivery-smoke"

    exit_code = main(
        [
            "run-reviewed-delivery-smoke",
            "--run-id",
            "reviewed-delivery-smoke-001",
            "--story-number",
            "STRY0010013",
            "--reviewer-id",
            "release-coordinator",
            "--artifact-root",
            str(artifact_root),
        ]
    )

    captured = capsys.readouterr()
    export_path = artifact_root / "exports" / "reviewed-delivery-smoke-001" / "STRY0010013.xml"
    job_path = (
        artifact_root
        / "reviewed-delivery-jobs"
        / "reviewed-delivery-smoke-001.json"
    )
    report_path = (
        artifact_root
        / "artifact-handoff-reports"
        / "reviewed-delivery-smoke-001.json"
    )
    manifest_path = (
        artifact_root
        / "reviewed-delivery-lifecycle-manifests"
        / "reviewed-delivery-smoke-001.json"
    )
    jobs = json.loads(job_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "reviewed_delivery_artifacts=1" in captured.out
    assert "handoff_plans=1" in captured.out
    assert "delivery_attachments_planned=1" in captured.out
    assert "delivery_attachments_applied=0" in captured.out
    assert "lifecycle_manifest_written=True" in captured.out
    assert export_path.exists()
    assert "<placeholder_update_set" not in export_path.read_text(encoding="utf-8")
    assert jobs[0]["delivery_contract"] == "reviewed_export"
    assert jobs[0]["reviewer_id"] == "release-coordinator"
    assert report["summary"]["attach_to_servicenow"] == 1
    assert report["decisions"][0]["delivery_contract"] == "reviewed_export"
    assert manifest["story_number"] == "STRY0010013"
    assert manifest["artifacts"]["delivery_artifact"]["path"] == str(export_path)
    assert manifest["artifacts"]["reviewed_delivery_job"]["path"] == str(job_path)
    assert manifest["artifacts"]["artifact_handoff_report"]["path"] == str(report_path)
    assert manifest["delivery_attachment_plan"] == {
        "dry_run": True,
        "planned": 1,
        "applied": 0,
    }
    assert "sys_id" not in json.dumps(report)
    assert "sys_id" not in json.dumps(manifest)


def test_cli_verify_writeback_fails_when_remote_story_does_not_match(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "verify-writeback",
                "--env-file",
                str(env_path),
                "--story-number",
                "STORY0010001",
                "--build-reference",
                "build-20260513-001",
                "--artifact-url",
                "artifacts/STORY0010001.json",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "verified=False" in captured.out
    assert "reason=state_mismatch" in captured.out


def test_cli_plan_bootstrap_fields_reports_missing_custom_fields_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()
    fake_client.dictionary_fields = [
        StoryDictionaryField(
            element="u_ai_status",
            column_label="AI Status",
            internal_type="string",
            active=True,
        )
    ]

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "plan-bootstrap-fields",
                "--env-file",
                str(env_path),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert fake_client.updated_fields == []
    assert "ready=False" in captured.out
    assert "table=rm_story" in captured.out
    assert "missing_fields=u_ai_build_reference,u_ai_candidate_artifact" in captured.out
    assert "form_layout_changes=0" in captured.out
    assert "state" not in captured.out
    assert "client-secret" not in captured.out


def test_cli_apply_bootstrap_fields_requires_confirmation_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "apply-bootstrap-fields",
                "--env-file",
                str(env_path),
                "--audit-root",
                str(tmp_path / "bootstrap-audit"),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "applied=False" in captured.out
    assert "reason=bootstrap_confirmation_required" in captured.out
    assert fake_client.created_dictionary_fields == []


def test_cli_apply_bootstrap_fields_creates_missing_fields_and_writes_audit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()
    fake_client.dictionary_fields = []
    audit_root = tmp_path / "bootstrap-audit"

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "apply-bootstrap-fields",
                "--env-file",
                str(env_path),
                "--confirm-table",
                "rm_story",
                "--confirm-fields",
                "--audit-root",
                str(audit_root),
                "--run-id",
                "bootstrap-run-001",
            ]
        )

    captured = capsys.readouterr()
    audit_path = audit_root / "bootstrap-run-001.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "applied=True" in captured.out
    assert "created_fields=3" in captured.out
    assert "form_layout_changes=0" in captured.out
    assert [field["element"] for field in fake_client.created_dictionary_fields] == [
        "u_ai_status",
        "u_ai_build_reference",
        "u_ai_candidate_artifact",
    ]
    assert audit["created_fields"] == [
        "u_ai_status",
        "u_ai_build_reference",
        "u_ai_candidate_artifact",
    ]
    assert audit["form_layout_changes"] == []
    assert "state" not in json.dumps(audit)
    assert "client-secret" not in captured.out


def test_cli_plan_lifecycle_business_rule_writes_reviewable_spec(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec_root = tmp_path / "lifecycle-bootstrap"

    exit_code = main(
        [
            "plan-lifecycle-business-rule",
            "--endpoint-url",
            "https://sidecar.example.gov/lifecycle/events",
            "--integration-identity",
            "jedi-devproject-lifecycle-integration",
            "--draft-state-value",
            "-6",
            "--ready-state-value",
            "1",
            "--run-id",
            "lifecycle-business-rule-001",
            "--spec-root",
            str(spec_root),
        ]
    )

    captured = capsys.readouterr()
    spec_path = spec_root / "lifecycle-business-rule-001.json"
    payload = json.loads(spec_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "lifecycle_business_rule_specs=1" in captured.out
    assert payload["rest_message"]["endpoint_url"] == (
        "https://sidecar.example.gov/lifecycle/events"
    )
    assert payload["rest_message"]["method_name"] == "post_event"
    assert payload["business_rule"]["table"] == "rm_story"
    assert payload["business_rule"]["when"] == "after"
    assert payload["business_rule"]["action"] == "update"
    assert [record["table"] for record in payload["servicenow_records"]] == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert "previous.state == '-6'" in payload["business_rule"]["condition"]
    assert "current.state == '1'" in payload["business_rule"]["condition"]
    assert "https://sidecar.example.gov/lifecycle/events" not in payload["business_rule"]["script"]
    assert "Jedi DevProject Lifecycle Event API" in payload["business_rule"]["script"]
    assert "story_state_changed" in payload["business_rule"]["script"]
    assert "story_sys_id" not in json.dumps(payload)


def test_cli_apply_lifecycle_webhook_requires_confirmation_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    spec_path = tmp_path / "lifecycle-bootstrap.json"
    spec_path.write_text(
        json.dumps(
            {
                "rest_message": {
                    "name": "Jedi DevProject Lifecycle Event API",
                    "method_name": "post_event",
                    "endpoint_url": "https://sidecar.example.gov/lifecycle/events",
                    "http_method": "POST",
                    "authentication": "configured_in_servicenow",
                    "content_type": "application/json",
                },
                "business_rule": {
                    "name": "Jedi DevProject lifecycle event emitter",
                    "table": "rm_story",
                    "when": "after",
                    "action": "update",
                    "active": True,
                    "condition": "current.state.changes()",
                    "script": "(function executeRule(current, previous) {})(current, previous);",
                },
            }
        ),
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "apply-lifecycle-webhook",
                "--env-file",
                str(env_path),
                "--spec-file",
                str(spec_path),
                "--audit-root",
                str(tmp_path / "bootstrap-audit"),
                "--run-id",
                "lifecycle-webhook-apply-001",
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "lifecycle_webhook_applied=False" in captured.out
    assert "reason=lifecycle_webhook_confirmation_required" in captured.out
    assert fake_client.upserted_table_records == []
    assert not (tmp_path / "bootstrap-audit" / "lifecycle-webhook-apply-001.json").exists()


def test_cli_apply_lifecycle_webhook_upserts_records_and_writes_audit(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    spec_root = tmp_path / "lifecycle-bootstrap"
    main(
        [
            "plan-lifecycle-business-rule",
            "--endpoint-url",
            "https://sidecar.example.gov/lifecycle/events",
            "--integration-identity",
            "jedi-devproject-lifecycle-integration",
            "--draft-state-value",
            "-6",
            "--ready-state-value",
            "1",
            "--run-id",
            "lifecycle-business-rule-001",
            "--spec-root",
            str(spec_root),
        ]
    )
    spec_path = spec_root / "lifecycle-business-rule-001.json"
    fake_client = FakeServiceNowClient()
    audit_root = tmp_path / "bootstrap-audit"

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "apply-lifecycle-webhook",
                "--env-file",
                str(env_path),
                "--spec-file",
                str(spec_path),
                "--confirm-table",
                "rm_story",
                "--confirm-records",
                "--audit-root",
                str(audit_root),
                "--run-id",
                "lifecycle-webhook-apply-001",
            ]
        )

    captured = capsys.readouterr()
    audit_path = audit_root / "lifecycle-webhook-apply-001.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "lifecycle_webhook_applied=True" in captured.out
    assert "upserted_records=3" in captured.out
    assert [record["table"] for record in fake_client.upserted_table_records] == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert [record["table"] for record in audit["upserted_records"]] == [
        "sys_rest_message",
        "sys_rest_message_fn",
        "sys_script",
    ]
    assert "story_sys_id" not in json.dumps(audit)
    assert "client-secret" not in captured.out


def test_cli_run_writeback_batch_processes_job_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "SERVICENOW_INSTANCE_URL=https://dev205693.service-now.com",
                "SERVICENOW_CLIENT_ID=client-id",
                "SERVICENOW_CLIENT_SECRET=client-secret",
            ]
        ),
        encoding="utf-8",
    )
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(
        """
        [
          {
            "story_number": "STORY0010001",
            "build_reference": "build-20260513-001",
            "artifact_url": "artifacts/STORY0010001.json",
            "from_state": "Ready"
          }
        ]
        """,
        encoding="utf-8",
    )
    fake_client = FakeServiceNowClient()

    with patch("jedi_devproject.cli.servicenow_client_from_env", return_value=fake_client):
        exit_code = main(
            [
                "run-writeback-batch",
                "--env-file",
                str(env_path),
                "--jobs-file",
                str(jobs_path),
                "--apply",
                "--actor-id",
                "svc-jedi-orchestrator",
                "--execution-id",
                "run-20260513-001",
                "--audit-root",
                str(tmp_path / "writeback-audit"),
                "--batch-report-root",
                str(tmp_path / "writeback-batches"),
            ]
        )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "total=1" in captured.out
    assert "applied=1" in captured.out
    assert fake_client.updated_fields
    assert (tmp_path / "writeback-batches" / "run-20260513-001.json").exists()
