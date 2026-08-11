from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_OPERATOR_GUIDE_FILES = (
    "docs/operator-guide.md",
    "docs/installation.md",
    "docs/local-development.md",
    "docs/runtime-operations.md",
    "docs/security-hardening.md",
)


def _read_operator_guide() -> str:
    return "\n".join(
        Path(path).read_text(encoding="utf-8") for path in _OPERATOR_GUIDE_FILES
    )


def _read_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_railway_api_manifest_uses_api_dockerfile_healthcheck_and_restart_policy() -> None:
    manifest = _read_json("deploy/railway/api-service.json")

    assert manifest["$schema"] == "https://railway.app/railway.schema.json"
    assert manifest["build"]["builder"] == "DOCKERFILE"
    assert manifest["build"]["dockerfilePath"] == "Dockerfile"
    assert manifest["deploy"]["healthcheckPath"] == "/ready"
    assert manifest["deploy"]["healthcheckTimeout"] == 60
    assert manifest["deploy"]["restartPolicyType"] == "ON_FAILURE"
    assert manifest["deploy"]["restartPolicyMaxRetries"] == 10
    assert "runtime_worker" not in json.dumps(manifest)


def test_railway_worker_manifest_uses_worker_dockerfile_without_healthcheck() -> None:
    manifest = _read_json("deploy/railway/worker-service.json")

    assert manifest["$schema"] == "https://railway.app/railway.schema.json"
    assert manifest["build"]["builder"] == "DOCKERFILE"
    assert manifest["build"]["dockerfilePath"] == "Dockerfile.worker"
    assert manifest["deploy"]["startCommand"] == "python -m jedi_devproject.runtime_worker"
    assert "healthcheckPath" not in manifest["deploy"]
    assert manifest["deploy"]["restartPolicyType"] == "ON_FAILURE"
    assert manifest["deploy"]["restartPolicyMaxRetries"] == 10
    assert "uvicorn" not in json.dumps(manifest)


def test_operator_guide_documents_hosted_api_worker_service_split() -> None:
    guide = _read_operator_guide()

    assert "Hosted Railway Process Split" in guide
    assert "`deploy/railway/api-service.json` is the API service manifest" in guide
    assert "`deploy/railway/worker-service.json` is the worker service manifest" in guide
    assert "exposes `/ready` as the Railway healthcheck path" in guide
    assert "The API service owns" in guide
    assert "`/health`, `/ready`, lifecycle webhooks" in guide
    assert "The worker service must not expose a public HTTP process" in guide


def test_sprint_773_documents_hosted_api_readiness_deploy_gate() -> None:
    change_log = Path("docs/sprints/sprint-773-change-log.md").read_text(encoding="utf-8")
    operator_guide = _read_operator_guide()

    assert "Hosted API readiness deploy gate" in change_log
    assert "2 failing-first Railway readiness assertions" in change_log
    assert "`/ready`" in change_log
    assert "`/health`" in change_log
    assert "Railway deploy healthcheck uses `/ready`" in operator_guide
    assert "container liveness probe still uses `/health`" in operator_guide
