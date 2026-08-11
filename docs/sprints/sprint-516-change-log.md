# Sprint 516 Change Log

## Legacy Update Set apply lookup non-JSON value rejection

Sprint 516 continued production hardening by tightening the legacy local Update Set apply path. The preferred implementation route is retrieved Update Set handoff, but the compatibility `JEDI_UPDATE_SET_APPLY=true` path still resolves an integration user and mutates the user's current Update Set preference before applying dictionary/form changes.

`apply_candidate_to_update_set()` now rejects unsupported objects, bytes, containers in scalar positions, floats, and non-scalar values from the integration user lookup with the fixed `Update Set apply lookup contains non-JSON value` diagnostic. The diagnostic does not echo object type names, object string output, credential-like keys, returned user sys_ids, or ServiceNow response internals.

This keeps the legacy apply path fail-closed for corrupted or hostile ServiceNow lookup responses: unsupported lookup metadata fails before setting the current Update Set preference, applying dictionary/form changes, fetching captured customer updates, or reporting an apply result.

Verification:

- Added 1 failing-first legacy Update Set apply lookup test covering a secret-bearing object with a hostile `__str__`.
- `python3 -m pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_non_json_integration_user_sys_id_without_leak -q`: failed before implementation because the strict diagnostic did not exist.
- `python3 -m pytest tests/test_update_set_apply.py::test_apply_candidate_rejects_non_json_integration_user_sys_id_without_leak -q`: 1 test passed.
- `python3 -m pytest tests/test_update_set_apply.py -q`: 12 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 590 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2479 total tests passed at 93.46% coverage.
