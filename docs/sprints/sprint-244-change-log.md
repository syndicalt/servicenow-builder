# Sprint 244 Change Log - Public Web Allowlist Domain Hygiene

## Summary

- Public web allowlist domain hygiene keeps documentation retrieval policy boundaries explicit.
- Added a production startup regression test for padded `JEDI_PUBLIC_WEB_ALLOWED_DOMAINS` values.
- Updated runtime validation so production deployments reject empty, padded, whitespace/control-character, encoded-whitespace/control-character, or local public-web allowlist domains before the worker can fetch public documentation.
- Documented that allowed domains must be non-local hostnames without padding, whitespace, or control characters.

## Verification

- `python3 -m pytest tests/test_runtime.py::test_validate_runtime_settings_rejects_malformed_public_web_allowed_domains -q`
  - `1 passed`
- `python3 -m ruff check src tests`
  - `All checks passed!`
- `python3 -m mypy src tests`
  - `Success: no issues found in 174 source files`
- `python3 -m pytest tests/test_project_docs.py -q`
  - `318 passed`
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`
  - `1596 passed, 93.93% coverage`
