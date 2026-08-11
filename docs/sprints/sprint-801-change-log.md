# Sprint 801 Change Log - Dockerfile pip environment defaults

## Scope

Hardened runtime image build behavior by making pip's build-time defaults explicit in both API and
worker Dockerfiles.

## Tests First

- Added 4 failing-first Dockerfile pip environment assertions in `tests/test_container_runtime.py::test_runtime_dockerfiles_define_pip_build_environment_defaults`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_801_documents_dockerfile_pip_environment_defaults`.
- Initial failures proved both Dockerfiles did not set `PIP_DISABLE_PIP_VERSION_CHECK=1`, `PIP_NO_CACHE_DIR=1`, or `PIP_ROOT_USER_ACTION=ignore`, and this sprint log was absent.

## Changes

- Added `PIP_DISABLE_PIP_VERSION_CHECK=1` before package installation in `Dockerfile` and `Dockerfile.worker`.
- Added `PIP_NO_CACHE_DIR=1` before package installation in both runtime Dockerfiles.
- Added `PIP_ROOT_USER_ACTION=ignore` before package installation in both runtime Dockerfiles.
- Documented that these defaults avoid pip version-check calls, pip cache layers, and root-user warning noise during the intentional build-time install phase.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "pip_build_environment or pip_environment"`: 2 passed, 905 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3193 passed, 93.36% coverage.
