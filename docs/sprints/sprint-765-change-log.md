# Sprint 765 Change Log - Hosted container port and healthcheck contract

## Scope

Made the API container deployment contract explicit for hosted runtimes. The image now honors the
platform-provided port while keeping the local default, and it exposes a container-level liveness
probe that checks the runtime `/health` endpoint.

## Tests First

- Added 3 failing-first container deployment assertions:
  - `tests/test_container_runtime.py::test_dockerfile_builds_runtime_image_without_copying_local_secrets`
  - `tests/test_container_runtime.py::test_dockerfile_defines_healthcheck_against_public_liveness_probe`
  - `tests/test_container_runtime.py::test_operator_guide_documents_container_runtime`
- Initial failures proved the API Dockerfile was hardcoded to port 8000, lacked a container
  healthcheck, and did not document the hosted runtime port contract.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_765_documents_hosted_container_port_and_healthcheck_contract`

## Changes

- Updated `Dockerfile` so the API starts with:
  `uvicorn jedi_devproject.runtime_api:build_app --factory --host 0.0.0.0 --port ${PORT:-8000}`.
- The hosted API port default is documented as `${PORT:-8000}`.
- Added a Docker `HEALTHCHECK` that calls `GET /health` on `http://127.0.0.1:${PORT:-8000}/health`
  with a 20 second start period, 30 second interval, 5 second timeout, and 3 retries.
- Kept the healthcheck implemented with Python standard-library HTTP so the image does not require
  extra curl or wget packages.
- Documented the hosted API port and healthcheck contract in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "container_runtime or sprint_765"` - 7 passed, 838 deselected.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3113 passed, 93.39% coverage.
