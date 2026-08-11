# Sprint 782 Change Log - Docker context runtime evidence exclusion

## Scope

Hardened Docker build context hygiene so local runtime evidence, coverage output, and development
environment directories cannot be copied into API or worker image layers by future Dockerfile edits.

## Tests First

- Added 6 failing-first Docker context artifact assertions in `tests/test_container_runtime.py::test_dockerignore_excludes_local_runtime_evidence_and_coverage_artifacts`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_782_documents_docker_context_runtime_evidence_exclusion`.
- Initial failures proved `.eventloom/`, `.coverage`, `coverage.xml`, `.tox/`, `.venv/`, and `venv/` were not all excluded and this sprint log was absent.

## Changes

- Added `.eventloom/` to `.dockerignore` so local Zaxy/Eventloom runtime history stays out of image build context.
- Added `.coverage` and `coverage.xml` to `.dockerignore` so test coverage artifacts stay local.
- Added `.tox/`, `.venv/`, and `venv/` to `.dockerignore` so development dependency directories are not sent to the Docker daemon.
- Documented the Docker context runtime evidence boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "runtime_evidence_exclusion or runtime_evidence_and_coverage"`: 2 passed, 871 deselected.
- `python3 -m ruff check src tests`: All checks passed.
- `python3 -m mypy src tests`: Success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3155 passed, total coverage 93.36%.
