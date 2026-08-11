# Sprint 773 Change Log - Hosted API readiness deploy gate

## Scope

Hardened the hosted API deployment manifest so Railway rollout healthchecks verify API readiness
against the PostgreSQL-backed operational store instead of checking only process liveness.

## Tests First

- Added 2 failing-first Railway readiness assertions:
  - `tests/test_hosted_deployment.py::test_railway_api_manifest_uses_api_dockerfile_healthcheck_and_restart_policy`
  - `tests/test_hosted_deployment.py::test_sprint_773_documents_hosted_api_readiness_deploy_gate`
- Initial failures proved `railway.json` still used `/health` for hosted deploy checks and this
  sprint log was absent.

## Changes

- Changed `railway.json` deploy healthcheck path from `/health` to `/ready`.
- Documented that Railway deploy healthcheck uses `/ready` while the container liveness probe still
  uses `/health`.

## Verification

- Focused regression: `python3 -m pytest tests/test_hosted_deployment.py -q` -> 4 passed.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3137 passed, 93.36% coverage.
