# Sprint 768 Change Log - Runtime role startup boundary

## Scope

Added explicit runtime role configuration so hosted API and worker services can fail closed when
production settings cross process boundaries. The API role rejects worker-only model and build
settings, while the worker role rejects API-only webhook and admin settings.

## Tests First

- Added 7 failing-first runtime role assertions:
  - `tests/test_runtime.py::test_load_runtime_settings_reads_runtime_role`
  - `tests/test_runtime.py::test_validate_runtime_settings_api_role_does_not_require_model_provider`
  - `tests/test_runtime.py::test_validate_runtime_settings_rejects_worker_secrets_on_api_role`
  - `tests/test_runtime.py::test_validate_runtime_settings_worker_role_does_not_require_api_secrets`
  - `tests/test_runtime.py::test_validate_runtime_settings_rejects_api_secrets_on_worker_role`
  - `tests/test_container_runtime.py::test_dockerfile_builds_runtime_image_without_copying_local_secrets`
  - `tests/test_container_runtime.py::test_worker_dockerfile_runs_runtime_worker_loop`
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_768_documents_runtime_role_startup_boundary`
- Initial failures proved the runtime settings model did not expose `runtime_role`, the Docker
  images did not set role defaults, and this sprint documentation was absent.

## Changes

- Added `JEDI_RUNTIME_ROLE` parsing with allowed values `combined`, `api`, and `worker`.
- Added `RuntimeSettings.runtime_role`, defaulting to `combined` for local compatibility.
- Added production validation for `JEDI_RUNTIME_ROLE=api`:
  - rejects `JEDI_MODEL_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL`,
    `JEDI_PUBLIC_WEB_ACCESS=worker`, and `JEDI_UPDATE_SET_APPLY=true`.
  - does not require model provider settings on the public API service.
- Added production validation for `JEDI_RUNTIME_ROLE=worker`:
  - rejects `JEDI_LIFECYCLE_WEBHOOK_AUTH_MODE`, `JEDI_LIFECYCLE_WEBHOOK_SECRET`,
    `JEDI_ADMIN_API_TOKEN`, `JEDI_ADMIN_AUTH_MODE`, and local admin console credentials.
  - does not require lifecycle webhook or admin authentication settings on the private worker.
- Set `JEDI_RUNTIME_ROLE=api` in `Dockerfile`.
- Set `JEDI_RUNTIME_ROLE=worker` in `Dockerfile.worker`.
- Documented the runtime role boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py tests/test_container_runtime.py tests/test_project_docs.py -q -k "api_role or worker_role or runtime_role or dockerfile_builds_runtime_image or worker_dockerfile or sprint_768"` - 8 passed, 1188 deselected.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3125 passed, 93.35% coverage.
