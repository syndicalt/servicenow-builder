# Sprint 520 Change Log

## Lifecycle webhook apply-result sys_id non-JSON value rejection

Sprint 520 continued production hardening by tightening the payload returned by the bootstrap path that installs the ServiceNow REST Message, REST Method, and Business Rule used for lifecycle event emission. Sprint 519 made the `sys_rest_message.sys_id` lookup safe before using it as the `sys_rest_message_fn` parent reference. Sprint 520 extends the same strictness to every `sys_id` stored in the `LifecycleWebhookApplyResult.upserted_records` evidence payload.

`apply_lifecycle_webhook_records()` now validates the `sys_id` returned from each `sys_rest_message`, `sys_rest_message_fn`, and `sys_script` upsert before adding it to the apply result. Unsupported objects, bytes, containers, floats, and non-scalar values fail with the fixed `Lifecycle webhook lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned sys_ids, endpoint values, or ServiceNow response internals.

This keeps lifecycle webhook bootstrap evidence JSON-safe at the source: corrupted or hostile ServiceNow upsert responses cannot be returned as apply-result payloads for later CLI rendering, audit serialization, or operator inspection.

Verification:

- Added 1 failing-first lifecycle webhook apply-result test covering a secret-bearing REST Method upsert result with a hostile `__str__`.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_method_result -q`: failed before implementation because the corrupt REST Method result was accepted and execution continued to the Business Rule upsert.
- `python3 -m pytest tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_rest_message_lookup tests/test_bootstrap.py::test_apply_lifecycle_webhook_records_rejects_non_json_method_result -q`: 2 tests passed.
- `python3 -m pytest tests/test_bootstrap.py -q`: 23 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 594 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2487 total tests passed at 93.43% coverage.
