# Sprint 152 Change Log

## Bootstrap metadata platform read-only policy

- Kept the `rm_story` automation metadata fields dictionary-writable so the worker can continue writing `u_ai_status`, `u_ai_handoff_type`, `u_ai_handoff_reference`, and `u_ai_artifact_reference` through the ServiceNow Table API.
- Added bootstrap application of the `Jedi DevProject read-only automation metadata` UI Policy on `rm_story`.
- Added a UI Policy script that calls `g_form.setReadOnly(...)` for each automation metadata field in the ServiceNow form experience while preserving the Table API write path.
- Kept bootstrap form placement unchanged; the project team still decides whether these operational fields are visible on the Story form.
- Updated the operator guide to document dictionary writeability versus platform read-only behavior.
- Applied the corrected bootstrap to the new ServiceNow instance and verified the UI Policy is active, global, runs scripts, and marks all four automation metadata fields read-only.
- Removed orphan `sys_ui_policy_action` rows created during the rejected action-based attempt; the final bootstrap uses the single UI Policy script and does not depend on child action records.
- UAT passed for read-only bootstrap fields.

## Complete lifecycle AI status closeout

- Fixed a lifecycle loose end where stories moved to `Complete` in ServiceNow could keep `u_ai_status=Ready for Testing`.
- Added API-side closeout writeback for `Ready for Testing -> Complete` lifecycle events: the app now sets `u_ai_status=Complete` and writes a closeout work note without enqueueing a worker job.
- Kept the worker out of the human wait loop; the Complete event remains API-driven and uses `story_sys_id` for the ServiceNow update.

## Verification

- `pytest tests/test_bootstrap.py::test_apply_bootstrap_fields_creates_only_missing_custom_fields tests/test_bootstrap.py::test_apply_bootstrap_fields_adds_platform_readonly_policy -q`
- `pytest tests/test_cli.py::test_cli_apply_bootstrap_fields_creates_missing_fields_and_writes_audit -q`
- `pytest tests/test_bootstrap.py tests/test_cli.py::test_cli_apply_bootstrap_fields_creates_missing_fields_and_writes_audit tests/test_project_docs.py -q`
- `pytest tests/test_runtime.py::test_runtime_complete_event_updates_ai_status_without_enqueueing_worker tests/test_lifecycle_api.py::test_lifecycle_webhook_records_complete_event_and_closes_related_job -q`
- `ruff check .`
- `mypy src tests`
