# Sprint 766 Change Log - Docker context secret exclusion contract

## Scope

Hardened the Docker build context so local environment files cannot be sent to container builds as
the repository grows. The contract protects `.env.local` and future `.env.<name>` variants while
keeping the non-secret `.env.example` documentation file available.

## Tests First

- Added 2 failing-first Docker context assertions:
  - `tests/test_container_runtime.py::test_dockerignore_excludes_local_environment_variants_but_keeps_example`
  - `tests/test_project_docs.py::test_sprint_766_documents_docker_context_secret_exclusion_contract`
- Initial failures proved `.dockerignore` only ignored exact `.env` and did not exclude `.env.local`
  or future environment variants. The sprint documentation file was also absent.

## Changes

- Replaced the exact `.env` Docker ignore rule with `.env*`.
- Added `!.env.example` so the non-secret example contract can remain in build context if needed.
- Documented the Docker build context secret boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "dockerignore or sprint_766"` - 2 passed, 845 deselected.
- `python3 -m ruff check src tests` - passed.
- `python3 -m mypy src tests` - passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 3115 passed, 93.39% coverage.
