# Sprint 771 Change Log - Non-root container runtime

## Scope

Hardened the API and worker container images so hosted runtime processes no longer run as root.

## Tests First

- Added 3 failing-first non-root container assertions:
  - `tests/test_container_runtime.py::test_dockerfile_builds_runtime_image_without_copying_local_secrets`
  - `tests/test_container_runtime.py::test_worker_dockerfile_runs_runtime_worker_loop`
  - `tests/test_container_runtime.py::test_runtime_dockerfiles_run_as_non_root_user`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_771_documents_non_root_container_runtime`
- Initial failures proved `Dockerfile`, `Dockerfile.worker`, and the operator guide did not define
  a non-root runtime user, and this sprint log was absent.

## Changes

- Added a system `jedi` group and user in the API image.
- Added a system `jedi` group and user in the worker image.
- Created `/app/artifacts` in both images and assigned `/app` ownership to `jedi:jedi` so mounted
  runtime artifact paths can initialize with application-owned permissions.
- Added `USER jedi` before the API and worker commands.
- Documented the non-root container runtime posture in the operator guide.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "dockerfile_builds_runtime_image or worker_dockerfile or non_root_container or sprint_771"` -> 3 passed, 850 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3134 passed, 93.36% coverage.
