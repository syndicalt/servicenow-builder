# Sprint 395 Change Log

## Collision-safe artifact truncation marker

Hardened admin artifact payload projection so the internal `__jedi_payload_truncated__` diagnostic marker cannot overwrite a user-supplied payload key with the same name. Wide artifact payload projection previously appended the internal marker after user key rendering, so a persisted artifact containing `__jedi_payload_truncated__` could lose that user-visible diagnostic value in the admin projection.

The internal truncation marker now uses the same collision-aware payload key renderer as user payload keys. If a user key already occupies `__jedi_payload_truncated__`, the internal metadata renders as `__jedi_payload_truncated__ [duplicate 2]` and the user value remains visible.

## Tests

- Failing-first coverage: 1 test failed before implementation, proving wide artifact payload projection overwrote a user-supplied `__jedi_payload_truncated__` key.
- Focused verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys or truncation_marker"` passed with 6 tests.
- Broader artifact verification: `python3 -m pytest tests/test_runtime.py -q -k "payload_keys or truncation_marker or artifact_view or artifact_read or admin_console_artifact"` passed with 23 tests.
- Static verification: `python3 -m ruff check src tests && python3 -m mypy src tests` passed with all checks passed and no issues found in 190 source files.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 190 source files, 469 documentation tests passed, and 2148 total tests passed at 93.92% coverage.
