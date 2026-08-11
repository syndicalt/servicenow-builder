# Sprint 799 Change Log - Docker context control-plane exclusion

## Scope

Hardened Docker build context hygiene so local operator control-plane files and common private-key
materials cannot be sent to the Docker daemon or captured by future broad-copy Dockerfile changes.

## Tests First

- Added 8 failing-first Docker context control-plane exclusion assertions in `tests/test_container_runtime.py::test_dockerignore_excludes_local_control_plane_configuration`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_799_documents_docker_context_control_plane_exclusion`.
- Initial failures proved `.dockerignore` did not exclude `.mcp.json`, `zaxy-mcp.json`, `.claude/`, `.codex/`, or common private-key and certificate bundle patterns, and this sprint log was absent.

## Changes

- Added `.mcp.json`, `zaxy-mcp.json`, `.claude/`, and `.codex/` to `.dockerignore`.
- Added `*.pem`, `*.key`, `*.p12`, and `*.pfx` to `.dockerignore`.
- Documented that these exclusions protect future Dockerfile changes even though current Dockerfiles copy only explicit package sources.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "control_plane_configuration or control_plane_exclusion"`: 2 passed, 901 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3189 passed, 93.36% coverage.
