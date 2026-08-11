# Sprint 295 Change Log - Public Web Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed public documentation retrieval settings when `JEDI_PUBLIC_WEB_ACCESS=worker`.
- Worker-enabled public web allowlists must be present, unpadded, free of whitespace/control characters, and limited to non-local hostnames before runtime settings are returned.
- Worker-enabled public documentation URLs must be present, HTTPS, allowlist-matched, and free of credentials, fragments, whitespace/control characters, encoded whitespace/control characters, and sensitive query parameters before any worker can construct a public documentation retriever.
- Public documentation URL diagnostics at settings load use fixed setting names and do not echo URL credentials or sensitive query values.
- Existing direct `RuntimeSettings` production validation remains intact for non-env wiring.
- Added failing regressions proving malformed worker public-web env values were previously accepted during settings loading.
- Documented the public-web settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k "public_web_worker and load_runtime_settings"` - 3 tests failed before implementation because malformed public-web worker settings were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k "public_web_worker and load_runtime_settings"` - 5 passed after implementation.
- `python3 -m pytest tests/test_runtime.py -q -k "public_web"` - 28 passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_five_documents_public_web_load_guard -q` - 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 369 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1785 passed, total coverage 93.89%.
