# Sprint 814 Change Log - Production public-web resource ceiling validation

## Scope

Hardened production public documentation retrieval settings so worker public-web context gathering
cannot be configured with excessive response, excerpt, or result limits.

## Tests First

- Added 1 failing-first public-web resource assertion:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_excessive_public_web_resource_limits`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_814_documents_production_public_web_resource_ceilings`.
- Initial failure proved production worker validation accepted 10 MiB public-web responses, 1,000,000
  excerpt characters, and 1,000 public-web results through direct `RuntimeSettings`.

## Changes

- `JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES` now has a production ceiling of `1048576`.
- `JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS` now has a production ceiling of `16000`.
- `JEDI_PUBLIC_WEB_MAX_RESULTS` now has a production ceiling of `10`.
- Diagnostics name the setting and ceiling without echoing the oversized configured value.
- Updated the operator guide to document the public-web retrieval ceilings.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "excessive_public_web_resource_limits or non_positive_public_web_worker_limits"`: 2 passed, 364 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_814`: 1 passed, 886 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 366 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3227 passed, 93.38% coverage.
