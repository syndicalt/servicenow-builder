# Sprint 1051 Change Log - ServiceNow runtime client direct settings boundary

## Summary

Sprint 1051 continued production hardening by tightening ServiceNow runtime client construction. Startup validation already exact-string guards ServiceNow instance URLs and OAuth credentials, but the runtime client wiring still resolved PM/story and development fallbacks directly with `or` and compared direct `RuntimeSettings` values with `==`. Embedded callers using mutated settings objects could therefore execute string-subclass truthiness, length, or equality hooks while deciding which ServiceNow instance reads stories and which instance receives generated changes.

ServiceNow runtime client construction now normalizes all base, PM, and development ServiceNow URL and OAuth credential settings before fallback selection, equality comparison, OAuth credential construction, or `ServiceNowClient` construction.

## Changes

- Added `_servicenow_runtime_connection_settings()` to exact-string validate and hygiene-check base, PM, and development ServiceNow connection settings.
- `_servicenow_story_client_from_settings()` now uses normalized PM/story settings before creating the story client.
- `_servicenow_development_client_from_settings()` now uses normalized development settings before creating the development client.
- `_servicenow_pm_and_dev_settings_match()` now compares normalized strings instead of raw `RuntimeSettings` attributes.
- Updated the operator guide to document the runtime ServiceNow client construction boundary.

## Tests

- Added 2 failing-first ServiceNow runtime construction assertions:
  - `test_servicenow_story_client_rejects_pm_url_subclass_before_fallback_truthiness`
  - `test_servicenow_pm_dev_match_rejects_secret_subclass_before_equality`
- Initial focused run failed before implementation because ServiceNow client wiring executed string-subclass `__len__` and `__eq__` hooks.
- Focused regression after implementation:
  - `pytest tests/test_runtime.py -q -k "servicenow_story_client_rejects_pm_url_subclass or servicenow_pm_dev_match_rejects_secret_subclass"` - 2 passed.
