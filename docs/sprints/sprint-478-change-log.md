# Sprint 478 Change Log

## Admin artifact diagnostic JSON non-finite number rejection

Hardened admin artifact diagnostic JSON rendering so redacted artifact payload views cannot emit non-standard JSON if a future projection defect or corrupted diagnostic view contains `NaN`, `Infinity`, or `-Infinity`.
Admin artifact views are operator-facing evidence, so the final serialization step must fail closed
even after earlier scalar normalization.

`_admin_artifact_payload_json()` now serializes admin artifact payload diagnostics with strict JSON
numeric handling before HTML rendering or truncation-preview generation. Non-finite diagnostic
payloads fail with `admin artifact payload diagnostic contains non-finite numeric values`. The
diagnostic is stable and does not echo payload field names, secret-bearing feedback, story
identifiers, or payload values.

## Verification

- Added 1 failing-first admin artifact diagnostic test covering a non-finite payload diagnostic
  value without field-name, secret, or value reflection.
- `python3 -m pytest tests/test_runtime.py::test_admin_artifact_payload_json_rejects_non_finite_payload_without_leak -q`:
  failed before implementation because `_admin_artifact_payload_json()` did not exist and admin
  artifact diagnostics used direct `json.dumps()` calls.
- `python3 -m pytest tests/test_runtime.py::test_admin_artifact_payload_json_rejects_non_finite_payload_without_leak tests/test_runtime.py::test_artifact_payload_view_replaces_non_json_scalar_values tests/test_runtime.py::test_artifact_read_redacts_and_normalizes_untrusted_payload_keys tests/test_runtime.py::test_admin_console_artifact_view_renders_payload_with_basic_auth -q`:
  4 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 552 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2399 total tests passed at 93.87% coverage.
