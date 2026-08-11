# Sprint 677 Change Log - Anthropic metadata stringification boundary

## Scope

Hardened Anthropic successful-response metadata diagnostics so unexpected `stop_reason` values cannot
execute arbitrary object stringification while provider exceptions are being constructed.

## Tests First

- Added 1 failing-first Anthropic provider assertion:
  `tests/test_anthropic_provider.py::test_anthropic_provider_rejects_unstringifiable_stop_reason_without_leak`
- Initial failure proved a hostile `stop_reason` object could raise `client_secret=stop-reason-secret`
  from `__str__()` before the provider raised its fixed `AnthropicProviderError`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_677_documents_anthropic_metadata_stringification_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added a fixed unsupported-metadata marker for non-exact-string Anthropic response metadata.
- Updated unexpected `stop_reason` diagnostics to avoid calling `str()` on unsupported metadata values.
- Documented that Anthropic successful-response metadata only reflects exact strings.

## Verification

- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_rejects_unstringifiable_stop_reason_without_leak -q`
  failed first because Anthropic metadata diagnostics called hostile `__str__()` and surfaced
  `client_secret=stop-reason-secret`.
- `python3 -m pytest tests/test_anthropic_provider.py -q -k "stop_reason"` passed, 4 tests.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_677_documents_anthropic_metadata_stringification_boundary -q`
  failed first while this changelog was missing.
- `python3 -m pytest tests/test_anthropic_provider.py::test_anthropic_provider_rejects_unstringifiable_stop_reason_without_leak tests/test_anthropic_provider.py::test_anthropic_provider_sanitizes_unexpected_stop_reason_diagnostic tests/test_project_docs.py::test_sprint_677_documents_anthropic_metadata_stringification_boundary -q`
  passed, 3 tests.
- `ruff check src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py tests/test_project_docs.py`
  passed.
- `mypy src/jedi_devproject/anthropic_provider.py tests/test_anthropic_provider.py` passed across 2 source files.
- `python3 -m pytest tests/test_anthropic_provider.py -q` passed, 83 tests.
- `python3 -m pytest tests/test_project_docs.py -q` passed, 751 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2888 tests with 93.05% total coverage.
