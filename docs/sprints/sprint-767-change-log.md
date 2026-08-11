# Sprint 767 Change Log - Hosted process separation contract

## Scope

Made hosted API and worker process separation explicit and testable. The Railway API service now has
a checked manifest for Dockerfile, healthcheck, and restart policy, and the worker has a separate
service template that builds from the worker Dockerfile without exposing a public HTTP process.

## Tests First

- Added 3 failing-first hosted deployment assertions:
  - `tests/test_hosted_deployment.py::test_railway_api_manifest_uses_api_dockerfile_healthcheck_and_restart_policy`
  - `tests/test_hosted_deployment.py::test_railway_worker_manifest_template_uses_worker_dockerfile_without_public_healthcheck`
  - `tests/test_hosted_deployment.py::test_operator_guide_documents_hosted_api_worker_service_split`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_767_documents_hosted_process_separation_contract`
- Initial failures proved `railway.json`, `deploy/railway/worker-service.json`, operator docs, and
  this sprint log were absent.

## Changes

- Added `railway.json` for the public API service:
  - Dockerfile build from `Dockerfile`.
  - `/health` Railway healthcheck path.
  - 60 second healthcheck timeout.
  - on-failure restart policy with 10 maximum retries.
- Added `deploy/railway/worker-service.json` as the separate worker service template:
  - Dockerfile build from `Dockerfile.worker`.
  - start command `python -m jedi_devproject.runtime_worker`.
  - on-failure restart policy with 10 maximum retries.
  - no public `healthcheckPath`.
- Documented the hosted Railway API/worker split in the operator guide.

## Verification

- `python3 -m pytest tests/test_hosted_deployment.py tests/test_project_docs.py -q -k "hosted_deployment or sprint_767"` - 4 passed, 840 deselected.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3119 passed, 93.39% coverage.
