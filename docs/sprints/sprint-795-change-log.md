# Sprint 795 Change Log - Runtime base image digest pinning

## Scope

Hardened runtime container supply-chain posture by pinning the API and worker Python base images to
the current immutable multi-architecture image digest instead of relying on the mutable
`python:3.13-slim` tag alone.

## Tests First

- Added 4 failing-first runtime base image digest assertions in `tests/test_container_runtime.py::test_runtime_dockerfiles_pin_python_base_image_digest`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_795_documents_runtime_base_image_digest_pinning`.
- Initial failures proved both `Dockerfile` and `Dockerfile.worker` still used unpinned `python:3.13-slim` and this sprint log was absent.

## Changes

- Replaced both runtime base image declarations with `python:3.13-slim@sha256:9662417aace5ae7b8e2609cce472b72a8958e134ba372808abe9cc1a0c0125e6`.
- Documented that base image digest refreshes are intentional maintenance work after upstream image review and rebuild validation.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "base_image_digest or runtime_base_image"`: 2 passed, 893 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3181 passed, 93.36% coverage.
