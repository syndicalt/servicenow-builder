from pathlib import Path
from unittest.mock import patch

import pytest

from jedi_devproject.cli import main
from jedi_devproject.models import DataClassification, Story
from jedi_devproject.servicenow import StoryDictionaryField, StoryStateChoice


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


class FakeServiceNowClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.updated_fields: list[dict[str, object]] = []
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
        return [
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
            )
        ]

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

    def update_story_fields(self, story_sys_id: str, fields: dict[str, object]) -> None:
        self.updated_fields.append({"story_sys_id": story_sys_id, "fields": fields})


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
