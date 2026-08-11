# Sprint 847 Change Log - Unicode control character guard

## Intent

Harden the low-level control-character helper so direct callers cannot pass nulls,
booleans, bytes, string subclasses, empty strings, or multi-character strings into
`ord()` and receive raw parser/runtime diagnostics. Extend the guard from ASCII-only
C0 controls to every Unicode control, surrogate, and format category so C1 controls,
zero-width spaces, and surrogate sequences are rejected consistently across URL,
config, provider-response, and packet validation.

## Changes

- Added `src/jedi_devproject/unicode_controls.py` with a shared `is_control_character()`
  predicate backed by `unicodedata.category(c).startswith("C")`.
- `is_control_character()` rejects malformed direct calls with
  `character must be an exact string` or `character must be a single character`.
- Replaced `url_query_safety.is_ascii_control()` with the shared predicate; URL helpers
  now reject all Unicode control, surrogate, and format characters, not just ASCII
  C0 controls and DEL.
- Updated `config._has_control_character()`, `packet_validation._has_control_character()`,
  and `provider_response_normalization` control checks to use the shared predicate,
  eliminating duplicated ASCII-only validators.
- Added 1 failing-first Unicode control character assertion:
  `tests/test_unicode_controls.py::test_is_control_character_rejects_malformed_inputs`.
- Added adversarial assertions for double-encoded C1 controls and zero-width spaces in
  `tests/test_url_query_safety.py`.

## Verification

- `pytest tests/test_unicode_controls.py tests/test_url_query_safety.py::test_is_control_character_rejects_non_exact_single_characters tests/test_project_docs.py::test_sprint_847_documents_unicode_control_character_guard -q`
- `pytest tests/test_url_query_safety.py tests/test_alert_webhook_url.py tests/test_provider_settings_safety.py tests/test_provider_contract.py tests/test_config.py tests/test_packet_validation.py tests/test_provider_response_normalization.py tests/test_runtime.py tests/test_rag.py tests/test_servicenow.py tests/test_numeric_settings.py tests/test_runtime_worker_retention.py -q`
- `pytest tests/test_project_docs.py -q`
- `pytest --cov=src/jedi_devproject --cov-report=term-missing -q`
