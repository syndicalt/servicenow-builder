# Sprint 249 Change Log - Public Web Worker Limit Hygiene

## Summary

- Public web worker limit hygiene prevents worker-side public documentation retrieval from running with zero-sized or zero-time retrieval limits.
- Added a runtime settings regression test for `JEDI_PUBLIC_WEB_ACCESS=worker` with non-positive `JEDI_PUBLIC_WEB_TIMEOUT_SECONDS`, `JEDI_PUBLIC_WEB_MAX_RESPONSE_BYTES`, `JEDI_PUBLIC_WEB_MAX_EXCERPT_CHARS`, and `JEDI_PUBLIC_WEB_MAX_RESULTS`.
- Updated `load_runtime_settings()` so worker public-web retrieval limits must be greater than zero at settings-load time.
- Documented that enabled worker public documentation retrieval cannot silently build an empty public-documentation context from invalid limits.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_load_runtime_settings_rejects_non_positive_public_web_worker_limits tests/test_runtime.py::test_load_runtime_settings_reads_public_web_worker_controls -q`
  - `2 passed`
- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_non_positive_runtime_limits -q`
  - `1 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `323 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1606 passed`
  - `Total coverage: 93.95%`
