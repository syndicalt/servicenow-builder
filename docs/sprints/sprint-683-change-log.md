# Sprint 683 Change Log - Anthropic response header exact-container boundary

## Scope

Hardened Anthropic response-header handling so retry and diagnostic paths only inspect exact
header dictionaries with exact string keys and exact string values. Header mapping subclasses,
string-key subclasses, and string-value subclasses are treated as unsupported header data instead of
being executed or surfaced.

## Tests First

- Added 3 failing-first Anthropic response-header assertions:
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_header_mapping_subclass_diagnostic`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_header_key_subclass_diagnostic`
  - `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_header_value_subclass_diagnostic`
- Initial failures proved hostile response headers could execute custom mapping iteration and key
  lowercasing hooks raising `client_secret=header-mapping-secret` and
  `client_secret=header-key-secret`, and could surface a non-exact `request-id` value.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_683_documents_anthropic_response_header_exact_container_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Anthropic response-header normalization now returns no headers unless the response header
  container is an exact `dict`.
- Header entries are skipped unless both key and value are exact `str` instances.
- Existing case-insensitive `request-id` and `retry-after` lookup behavior is preserved for ordinary
  exact dictionaries.
- Documented exact Anthropic response-header handling in the operator guide.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py -q -k "header_mapping_subclass or header_key_subclass or header_value_subclass"`
  failed first because header normalization executed hostile `.items()` and `.lower()` hooks and
  surfaced non-exact request-id values.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "header_mapping_subclass or header_key_subclass or header_value_subclass or sanitizes_request_id_diagnostic or surfaces_error_after_exhausting_retries or retry_after"`
  passed, 15 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_683`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_683` passed, 1 test.
- `python3 -m pytest tests/test_anthropic_provider.py -q` passed, 92 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 757 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2912 tests with 93.12% total coverage.
