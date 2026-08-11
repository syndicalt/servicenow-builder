# Sprint 812 Change Log - Public production lifecycle replay window ceiling

## Scope

Hardened public production lifecycle webhook validation so HMAC replay protection cannot be weakened
by configuring an excessive timestamp skew window.

## Tests First

- Added 2 failing-first public production replay-window assertions:
  `tests/test_runtime.py::test_validate_runtime_settings_rejects_excessive_lifecycle_webhook_replay_window`.
- Added 1 failing-first sprint documentation assertion:
  `tests/test_project_docs.py::test_sprint_812_documents_public_production_replay_window_ceiling`.
- Initial failures proved `JEDI_RUNTIME_ROLE=api` and explicitly accepted
  `JEDI_RUNTIME_ROLE=combined` production runtimes accepted
  `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS=86400`.

## Changes

- `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS` now has a public production ceiling.
- Added a public production replay-window ceiling:
  `JEDI_LIFECYCLE_WEBHOOK_MAX_SKEW_SECONDS<=900`.
- The existing default remains `300` seconds.
- Public API and combined production roles retain HMAC-SHA256 as the required lifecycle webhook auth
  posture.
- Updated the operator guide to document the replay-window ceiling and the default posture.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "excessive_lifecycle_webhook_replay_window or non_positive_runtime_limits or api_role_does_not_require_model_provider"`: 4 passed, 360 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_812`: 1 passed, 884 deselected.
- `python3 -m pytest tests/test_runtime.py -q`: 364 passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: success, no issues found in 199 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 3223 passed, 93.38% coverage.
