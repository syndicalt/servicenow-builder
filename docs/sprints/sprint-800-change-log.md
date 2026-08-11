# Sprint 800 Change Log - Dockerfile pip upgrade removal

## Scope

Hardened runtime image build reproducibility by removing the build-time `pip` self-upgrade from the
API and worker Dockerfiles after the Python base image digest has already been pinned.

## Tests First

- Added 3 failing-first Dockerfile pip upgrade assertions in `tests/test_container_runtime.py::test_runtime_dockerfiles_do_not_upgrade_pip_at_build_time`.
- Added 1 failing-first sprint documentation assertion: `tests/test_project_docs.py::test_sprint_800_documents_dockerfile_pip_upgrade_removal`.
- Initial failures proved both Dockerfiles still ran the mutable `--upgrade pip` build step and this sprint log was absent.

## Changes

- Replaced the two-step pip upgrade and package install with `python -m pip install --no-cache-dir .` in `Dockerfile`; the surviving install shape is `pip install --no-cache-dir .`.
- Replaced the same two-step command with `python -m pip install --no-cache-dir .` in `Dockerfile.worker`; the surviving install shape is `pip install --no-cache-dir .`.
- Documented that the images use the pip version supplied by the pinned Python base image to avoid an extra mutable build-time package-manager fetch.

## Verification

- `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "upgrade_pip or pip_upgrade"`: 2 passed, 903 deselected.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3191 passed, 93.36% coverage.
