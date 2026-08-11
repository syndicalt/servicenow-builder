# Sprint 465 Change Log

## Stable artifact hash non-finite number rejection

Hardened shared artifact provenance hashing so `stable_artifact_hash()` cannot mint SHA-256 values
over non-strict JSON representations containing `NaN`, `Infinity`, or `-Infinity`. The helper is
used for stable artifact identity and audit comparisons, so hashing Python's default `json.dumps()`
output for non-finite values would create a legitimate-looking digest over JSON that other strict
systems cannot parse.

`stable_artifact_hash()` now serializes the canonical payload with strict JSON numeric handling and
raises the fixed `artifact hash payload contains non-finite numeric values` diagnostic before
SHA-256 computation. The diagnostic does not echo payload field names, credential-like keys, or
values. Existing deterministic key ordering remains unchanged.

## Verification

- Added 1 failing-first stable artifact hash test covering non-finite payload rejection without
  field-name, credential-key, or value reflection.
- `python3 -m pytest tests/test_models.py::test_stable_artifact_hash_rejects_non_finite_values_without_payload_leak -q`:
  failed before implementation because `NaN` received a SHA-256 hash.
- `python3 -m pytest tests/test_models.py::test_stable_artifact_hash_is_order_independent_for_mapping_keys tests/test_models.py::test_stable_artifact_hash_rejects_non_finite_values_without_payload_leak tests/test_candidates.py -q`:
  8 tests passed.
- `python3 -m ruff check src tests`: passed.
- `python3 -m mypy src tests`: passed.
- `python3 -m pytest tests/test_project_docs.py -q`: 539 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`:
  2371 total tests passed at 93.83% coverage.
