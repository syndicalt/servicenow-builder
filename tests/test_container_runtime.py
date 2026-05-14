from __future__ import annotations

from pathlib import Path


def test_dockerfile_builds_runtime_image_without_copying_local_secrets() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert "FROM python:" in dockerfile
    assert "libpq5" in dockerfile
    assert "pip install" in dockerfile
    assert "uvicorn" in dockerfile
    assert "jedi_devproject.runtime_api:build_app" in dockerfile
    assert "--factory" in dockerfile
    assert ".env" in dockerignore
    assert "artifacts/" in dockerignore
    assert ".git" in dockerignore


def test_worker_dockerfile_runs_runtime_worker_loop() -> None:
    dockerfile = Path("Dockerfile.worker").read_text(encoding="utf-8")

    assert "FROM python:" in dockerfile
    assert "libpq5" in dockerfile
    assert "pip install" in dockerfile
    assert "python" in dockerfile
    assert "-m" in dockerfile
    assert "jedi_devproject.runtime_worker" in dockerfile
    assert "uvicorn" not in dockerfile


def test_compose_defines_api_worker_and_postgres_services() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "api:" in compose
    assert "worker:" in compose
    assert "postgres:" in compose
    assert "postgres:16" in compose
    assert "DATABASE_URL=postgresql://jedi:jedi@postgres:5432/jedi" in compose
    assert "SERVICENOW_INSTANCE_URL" in compose
    assert "SERVICENOW_CLIENT_ID" in compose
    assert "SERVICENOW_CLIENT_SECRET" in compose
    assert "JEDI_AUDIT_ROOT=/app/artifacts/audit" in compose
    assert "uvicorn" in compose
    assert "jedi_devproject.runtime_api:build_app" in compose
    assert "--factory" in compose
    assert "jedi-devproject-worker" in compose
    assert "depends_on:" in compose


def test_operator_guide_documents_container_runtime() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Container Runtime" in guide
    assert "docker compose up" in guide
    assert "api" in guide
    assert "worker" in guide
    assert "postgres" in guide
    assert "JEDI_BUILD_CLAIM_APPLY" in guide


def test_sprint_seventy_four_change_log_documents_container_runtime() -> None:
    change_log = Path("docs/sprints/sprint-74-change-log.md").read_text(
        encoding="utf-8"
    )

    assert "Dockerfile" in change_log
    assert "docker-compose.yml" in change_log
    assert "runtime_api" in change_log
    assert "runtime_worker" in change_log
    assert "PostgreSQL" in change_log
