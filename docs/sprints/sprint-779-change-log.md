# Sprint 779 Change Log - Neutral ServiceNow example targets

## Scope

Removed developer-instance-specific ServiceNow target defaults from committed example configuration
and operator documentation.

## Tests First

- Added 4 failing-first ServiceNow example target assertions in
  `tests/test_container_runtime.py::test_env_example_uses_neutral_servicenow_instance_placeholders`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_779_documents_neutral_servicenow_example_targets`.
- Initial failures proved `.env.example` and the operator guide still referenced
  `dev205693.service-now.com`, and this sprint log was absent.

## Changes

- Replaced the legacy single-instance fallback in `.env.example` with
  `https://<instance>.service-now.com`.
- Replaced the operator guide local configuration snippet with the same neutral placeholder.
- Documented that PDI-specific and customer-specific ServiceNow URLs belong in local `.env`, not in
  committed templates or docs.

## Verification

- Focused regression: `python3 -m pytest tests/test_container_runtime.py tests/test_project_docs.py -q -k "neutral_servicenow_instance_placeholders or sprint_779"` -> 2 passed, 865 deselected.
- Static lint: `python3 -m ruff check src tests` -> passed.
- Static typing: `python3 -m mypy src tests` -> passed.
- Full coverage gate: `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` -> 3149 passed, 93.36% coverage.
