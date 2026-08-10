from __future__ import annotations

import re
from pathlib import Path


def _runtime_environment_variable_names() -> set[str]:
    runtime_config = Path("src/jedi_devproject/runtime_config.py").read_text(
        encoding="utf-8"
    )
    return {
        match.group(1)
        for match in re.finditer(r'values\.get\("([A-Z0-9_]+)"\)', runtime_config)
        if match.group(1).startswith(("JEDI_", "OPENAI_"))
    }


def _env_example_variable_names() -> set[str]:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    return {
        line.split("=", 1)[0]
        for line in env_example.splitlines()
        if line and not line.startswith("#") and "=" in line
    }


def test_dockerfile_builds_runtime_image_without_copying_local_secrets() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert "FROM python:" in dockerfile
    assert "libpq5" in dockerfile
    assert "pip install" in dockerfile
    assert "uvicorn" in dockerfile
    assert "jedi_devproject.runtime_api:build_app" in dockerfile
    assert "--factory" in dockerfile
    assert "JEDI_RUNTIME_ROLE=api" in dockerfile
    assert "${PORT:-8000}" in dockerfile
    assert 'CMD ["sh", "-c", "exec uvicorn' in dockerfile
    assert "useradd --system" in dockerfile
    assert "mkdir -p /app/artifacts" in dockerfile
    assert "chown -R jedi:jedi /app" in dockerfile
    assert "USER jedi" in dockerfile
    assert ".env" in dockerignore
    assert ".env*" in dockerignore
    assert "!.env.example" in dockerignore
    assert "artifacts/" in dockerignore
    assert ".git" in dockerignore


def test_dockerignore_excludes_local_environment_variants_but_keeps_example() -> None:
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert ".env*" in dockerignore
    assert "!.env.example" in dockerignore
    assert ".env.local" not in dockerignore


def test_dockerignore_excludes_local_runtime_evidence_and_coverage_artifacts() -> None:
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    required_exclusions = (
        ".eventloom/",
        ".coverage",
        "coverage.xml",
        ".tox/",
        ".venv/",
        "venv/",
    )
    for exclusion in required_exclusions:
        assert exclusion in dockerignore


def test_dockerignore_excludes_local_control_plane_configuration() -> None:
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    required_exclusions = (
        ".mcp.json",
        "zaxy-mcp.json",
        ".claude/",
        ".codex/",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
    )
    for exclusion in required_exclusions:
        assert exclusion in dockerignore


def test_dockerfile_defines_healthcheck_against_public_liveness_probe() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "HEALTHCHECK" in dockerfile
    assert "http://127.0.0.1:${PORT:-8000}/health" in dockerfile
    assert "--start-period=20s" in dockerfile
    assert "--interval=30s" in dockerfile
    assert "--timeout=5s" in dockerfile
    assert "--retries=3" in dockerfile


def test_worker_dockerfile_runs_runtime_worker_loop() -> None:
    dockerfile = Path("Dockerfile.worker").read_text(encoding="utf-8")

    assert "FROM python:" in dockerfile
    assert "libpq5" in dockerfile
    assert "pip install" in dockerfile
    assert "python" in dockerfile
    assert "-m" in dockerfile
    assert "JEDI_RUNTIME_ROLE=worker" in dockerfile
    assert "jedi_devproject.runtime_worker" in dockerfile
    assert "useradd --system" in dockerfile
    assert "mkdir -p /app/artifacts" in dockerfile
    assert "chown -R jedi:jedi /app" in dockerfile
    assert "USER jedi" in dockerfile
    assert "uvicorn" not in dockerfile


def test_runtime_dockerfiles_pin_python_base_image_digest() -> None:
    expected_from = (
        "FROM python:3.13-slim@"
        "sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6"
    )
    for path in (Path("Dockerfile"), Path("Dockerfile.worker")):
        dockerfile = path.read_text(encoding="utf-8")
        first_line = dockerfile.splitlines()[0]

        assert first_line == expected_from
        assert re.fullmatch(r"FROM python:3\.13-slim@sha256:[0-9a-f]{64}", first_line)


def test_runtime_dockerfiles_do_not_upgrade_pip_at_build_time() -> None:
    for path in (Path("Dockerfile"), Path("Dockerfile.worker")):
        dockerfile = path.read_text(encoding="utf-8")

        assert "--upgrade pip" not in dockerfile
        assert "pip install --no-cache-dir ." in dockerfile
        assert dockerfile.count("pip install") == 1


def test_runtime_dockerfiles_define_pip_build_environment_defaults() -> None:
    for path in (Path("Dockerfile"), Path("Dockerfile.worker")):
        dockerfile = path.read_text(encoding="utf-8")

        assert "ENV PIP_DISABLE_PIP_VERSION_CHECK=1" in dockerfile
        assert "ENV PIP_NO_CACHE_DIR=1" in dockerfile
        assert "ENV PIP_ROOT_USER_ACTION=ignore" in dockerfile
        assert dockerfile.index("ENV PIP_DISABLE_PIP_VERSION_CHECK=1") < (
            dockerfile.index("RUN python -m pip install --no-cache-dir .")
        )


def test_runtime_dockerfiles_run_as_non_root_user() -> None:
    api_dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    worker_dockerfile = Path("Dockerfile.worker").read_text(encoding="utf-8")

    for dockerfile in (api_dockerfile, worker_dockerfile):
        assert "groupadd --system jedi" in dockerfile
        assert "useradd --system --gid jedi --home-dir /app" in dockerfile
        assert "USER root" not in dockerfile
        assert dockerfile.index("USER jedi") < dockerfile.index("CMD [")


def test_runtime_dockerfiles_define_owned_audit_root_default() -> None:
    api_dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    worker_dockerfile = Path("Dockerfile.worker").read_text(encoding="utf-8")

    for dockerfile in (api_dockerfile, worker_dockerfile):
        assert "ENV JEDI_AUDIT_ROOT=/app/artifacts/audit" in dockerfile
        assert "mkdir -p /app/artifacts/audit" in dockerfile
        assert dockerfile.index("ENV JEDI_AUDIT_ROOT=/app/artifacts/audit") < (
            dockerfile.index("USER jedi")
        )


def test_compose_defines_api_worker_and_postgres_services() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "api:" in compose
    assert "worker:" in compose
    assert "postgres:" in compose
    assert "postgres:16" in compose
    assert (
        "DATABASE_URL=postgresql://jedi:${JEDI_POSTGRES_PASSWORD:"
        "?JEDI_POSTGRES_PASSWORD_required}@postgres:5432/jedi" in compose
    )
    assert "SERVICENOW_PM_INSTANCE_URL" in compose
    assert "SERVICENOW_DEV_INSTANCE_URL" in compose
    assert "JEDI_AUDIT_ROOT=/app/artifacts/audit" in compose
    assert "uvicorn" in compose
    assert "jedi_devproject.runtime_api:build_app" in compose
    assert "--factory" in compose
    assert "jedi-devproject-worker" in compose
    assert "depends_on:" in compose


def test_compose_binds_api_port_to_loopback_only() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert '      - "127.0.0.1:8000:8000"' in compose
    assert '      - "8000:8000"' not in compose
    assert compose.index("api:") < compose.index('"127.0.0.1:8000:8000"')
    assert compose.index('"127.0.0.1:8000:8000"') < compose.index("worker:")


def test_compose_externalizes_postgres_password() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "POSTGRES_PASSWORD: jedi" not in compose
    assert "postgresql://jedi:jedi@" not in compose
    assert (
        "POSTGRES_PASSWORD: ${JEDI_POSTGRES_PASSWORD:"
        "?JEDI_POSTGRES_PASSWORD_required}" in compose
    )
    assert (
        "DATABASE_URL=postgresql://jedi:${JEDI_POSTGRES_PASSWORD:"
        "?JEDI_POSTGRES_PASSWORD_required}@postgres:5432/jedi" in compose
    )


def test_compose_requires_split_servicenow_runtime_values() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    required_variables = (
        "SERVICENOW_PM_INSTANCE_URL",
        "SERVICENOW_PM_CLIENT_ID",
        "SERVICENOW_PM_CLIENT_SECRET",
        "SERVICENOW_DEV_INSTANCE_URL",
        "SERVICENOW_DEV_CLIENT_ID",
        "SERVICENOW_DEV_CLIENT_SECRET",
    )
    for variable in required_variables:
        assert f"- {variable}=${{{variable}:?{variable}_required}}" in compose

    assert "- SERVICENOW_INSTANCE_URL=${SERVICENOW_INSTANCE_URL}" not in compose
    assert "- SERVICENOW_CLIENT_ID=${SERVICENOW_CLIENT_ID}" not in compose
    assert "- SERVICENOW_CLIENT_SECRET=${SERVICENOW_CLIENT_SECRET}" not in compose


def test_env_example_documents_compose_postgres_password_without_default() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "JEDI_POSTGRES_PASSWORD=" in env_example
    assert "JEDI_POSTGRES_PASSWORD=jedi" not in env_example
    assert "# Required for docker compose local PostgreSQL." in env_example


def test_env_example_uses_neutral_servicenow_instance_placeholders() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    operator_guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "dev205693.service-now.com" not in env_example
    assert "dev205693.service-now.com" not in operator_guide
    assert "SERVICENOW_INSTANCE_URL=https://<instance>.service-now.com" in env_example
    assert "SERVICENOW_INSTANCE_URL=https://<instance>.service-now.com" in operator_guide


def test_env_example_documents_runtime_role_and_hsts_controls() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "JEDI_RUNTIME_ROLE=combined" in env_example
    assert "# Public production API roles must set this to true after HTTPS is final." in (
        env_example
    )
    assert "JEDI_STRICT_TRANSPORT_SECURITY_ENABLED=false" in env_example
    assert "JEDI_STRICT_TRANSPORT_SECURITY_MAX_AGE_SECONDS=31536000" in env_example


def test_env_example_documents_all_runtime_environment_controls() -> None:
    parsed_runtime_variables = _runtime_environment_variable_names()
    documented_variables = _env_example_variable_names()

    assert parsed_runtime_variables - documented_variables == set()


def test_compose_defines_runtime_restart_policies() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "postgres:" in compose
    assert "image: postgres:16@" in compose
    assert "restart: unless-stopped" in compose
    assert "api:" in compose
    assert "worker:" in compose
    assert compose.count("restart: on-failure") == 2


def test_compose_pins_postgres_image_digest() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    expected_image = (
        "image: postgres:16@"
        "sha256:95206741a5b214807675e14165369d05b93a9cf692223b616d07cca227e74b0b"
    )

    assert expected_image in compose
    assert "image: postgres:16\n" not in compose
    assert re.search(r"image: postgres:16@sha256:[0-9a-f]{64}", compose)


def test_compose_uses_role_specific_runtime_dockerfiles() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert (
        "api:\n"
        "    build:\n"
        "      context: .\n"
        "      dockerfile: Dockerfile\n" in compose
    )
    assert (
        "worker:\n"
        "    build:\n"
        "      context: .\n"
        "      dockerfile: Dockerfile.worker\n" in compose
    )


def test_compose_declares_runtime_roles_per_service() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "api:" in compose
    assert "worker:" in compose
    assert "- JEDI_RUNTIME_ROLE=api" in compose
    assert "- JEDI_RUNTIME_ROLE=worker" in compose
    assert compose.index("- JEDI_RUNTIME_ROLE=api") < compose.index(
        "- JEDI_WORKER_ID=jedi-devproject-api"
    )
    assert compose.index("- JEDI_RUNTIME_ROLE=worker") < compose.index(
        "- JEDI_WORKER_ID=jedi-devproject-worker"
    )


def test_compose_defines_api_readiness_healthcheck() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("healthcheck:") == 2
    assert "urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=3)" in compose
    assert "      interval: 30s" in compose
    assert "      timeout: 5s" in compose
    assert "      retries: 3" in compose
    assert "      start_period: 20s" in compose
    assert compose.index("api:") < compose.index("http://127.0.0.1:8000/ready")
    assert compose.index("http://127.0.0.1:8000/ready") < compose.index("worker:")


def test_compose_reduces_api_and_worker_container_privileges() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    api_section = compose[compose.index("  api:") : compose.index("  worker:")]
    worker_section = compose[compose.index("  worker:") : compose.index("\nvolumes:")]

    for section in (api_section, worker_section):
        assert "security_opt:" in section
        assert "- no-new-privileges:true" in section
        assert "cap_drop:" in section
        assert "- ALL" in section

    assert "cap_drop:" not in compose[compose.index("  postgres:") : compose.index("  api:")]


def test_compose_reduces_postgres_container_privileges() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    postgres_section = compose[compose.index("  postgres:") : compose.index("  api:")]

    assert "security_opt:" in postgres_section
    assert "- no-new-privileges:true" in postgres_section
    assert "pids_limit: 512" in postgres_section
    assert "read_only: true" not in postgres_section
    assert "cap_drop:" not in postgres_section


def test_compose_uses_read_only_app_container_roots() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("read_only: true") == 2
    assert compose.count("tmpfs:") == 2
    assert compose.count("- /tmp") == 2
    assert compose.count("- runtime-artifacts:/app/artifacts") == 2
    assert compose.index("api:") < compose.index("read_only: true")
    assert compose.index("read_only: true") < compose.index("runtime-artifacts:/app/artifacts")
    assert compose.rindex("read_only: true") > compose.index("worker:")
    assert "postgres:\n    image: postgres:16@" in compose
    assert "    restart: unless-stopped" in compose


def test_compose_worker_waits_for_api_readiness() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    worker_section = compose[compose.index("  worker:") :]

    assert "depends_on:" in worker_section
    assert "postgres:\n        condition: service_healthy" in worker_section
    assert "api:\n        condition: service_healthy" in worker_section
    assert worker_section.index("postgres:") < worker_section.index("api:")
    assert compose.index("http://127.0.0.1:8000/ready") < compose.index("  worker:")


def test_compose_bounds_service_log_files() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("logging:") == 3
    assert compose.count("driver: json-file") == 3
    assert compose.count("max-size: \"10m\"") == 3
    assert compose.count("max-file: \"5\"") == 3
    assert compose.index("postgres:") < compose.index("logging:")
    assert compose.index("api:") < compose.index("driver: json-file", compose.index("api:"))
    assert compose.index("worker:") < compose.rindex("driver: json-file")


def test_compose_app_services_use_init_shim() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("init: true") == 2
    assert compose.index("api:") < compose.index("init: true")
    assert compose.index("init: true") < compose.index("worker:")
    assert compose.rindex("init: true") > compose.index("worker:")
    assert compose.index("postgres:") < compose.index("api:")


def test_compose_limits_app_container_process_counts() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert compose.count("pids_limit: 256") == 2
    assert compose.index("api:") < compose.index("pids_limit: 256")
    assert compose.index("pids_limit: 256") < compose.index("worker:")
    assert compose.rindex("pids_limit: 256") > compose.index("worker:")
    assert compose.index("postgres:") < compose.index("api:")


def test_compose_defines_app_graceful_shutdown_window() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    api_section = compose[compose.index("  api:") : compose.index("  worker:")]
    worker_section = compose[compose.index("  worker:") : compose.index("\nvolumes:")]

    for section in (api_section, worker_section):
        assert "stop_signal: SIGTERM" in section
        assert "stop_grace_period: 30s" in section


def test_compose_defines_postgres_graceful_shutdown_window() -> None:
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    postgres_section = compose[compose.index("  postgres:") : compose.index("  api:")]

    assert "stop_signal: SIGTERM" in postgres_section
    assert "stop_grace_period: 60s" in postgres_section
    assert "stop_grace_period: 30s" not in postgres_section


def test_operator_guide_documents_container_runtime() -> None:
    guide = Path("docs/operator-guide.md").read_text(encoding="utf-8")

    assert "Container Runtime" in guide
    assert "docker compose up" in guide
    assert "The hosted API image binds to `${PORT:-8000}`" in guide
    assert "container healthcheck calls `GET /health`" in guide
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
