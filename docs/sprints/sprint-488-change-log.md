# Sprint 488 Change Log

## Flow graph diff non-JSON payload rejection

Hardened Flow Designer graph-diff validation so safety scans do not coerce Python-only payload values into strings. The previous strict JSON helper rejected non-finite floats, but still used `default=str`, which allowed unsupported objects or bytes to enter raw XML and forbidden-token scans as reflected diagnostic text.

`_strict_validation_json()` now serializes without a fallback stringifier. `NaN`, `Infinity`, and `-Infinity` continue to fail with the existing non-finite diagnostics. Unsupported scalar objects, bytes, and other non-JSON values fail with stable non-JSON diagnostics for customer-update records or graph payloads without echoing malformed field names, object type names, object string output, or values.

## Verification

- Added 1 failing-first Flow graph diff validator test proving an object with secret-bearing `__str__` output was accepted before implementation.
- `python3 -m pytest tests/test_generation_validators.py::test_flow_graph_diff_validator_rejects_non_json_payload_values_without_leak -q`: failed before implementation because the validator did not raise.
- `python3 -m pytest tests/test_generation_validators.py::test_flow_graph_diff_validator_rejects_non_json_payload_values_without_leak tests/test_generation_validators.py::test_flow_graph_diff_rejects_non_finite_customer_updates_without_leak tests/test_generation_validators.py::test_flow_graph_diff_validator_rejects_non_finite_graph_payload_without_leak -q`: 3 tests passed.
- `python3 -m pytest tests/test_generation_validators.py -q`: 52 tests passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 562 documentation tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2419 total tests passed at 93.82% coverage.
