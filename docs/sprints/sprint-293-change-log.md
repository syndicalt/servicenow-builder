# Sprint 293 Change Log - Build Claim State Settings Load Guard

## Summary

- Runtime settings loading now rejects malformed `JEDI_BUILD_CLAIM_FROM_STATE` and `JEDI_BUILD_CLAIM_STATE` env values.
- Build claim state values must be non-empty, unpadded, and free of control characters before they enter worker settings.
- Default build claim state values remain `Ready` and `Work in Progress` when the env values are absent.
- Existing production validation for direct `RuntimeSettings` build claim state values remains intact when `JEDI_BUILD_CLAIM_APPLY=true`.
- Added failing regressions proving padded and control-character build claim state env values were previously accepted during settings loading.
- Documented the build claim state settings-load boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_runtime.py -q -k malformed_build_claim_state_values` - 3 tests failed before implementation because malformed build claim state env values were accepted during settings loading.
- `python3 -m pytest tests/test_runtime.py -q -k malformed_build_claim_state_values` - 3 passed.
- `python3 -m pytest tests/test_runtime.py -q -k malformed_build_claim_state_values && python3 -m pytest tests/test_project_docs.py::test_sprint_two_hundred_ninety_three_documents_build_claim_state_load_guard -q` - 3 passed, then 1 passed.
- `python3 -m ruff check src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - all checks passed.
- `python3 -m mypy src/jedi_devproject/runtime_config.py tests/test_runtime.py tests/test_project_docs.py` - success: no issues found in 3 source files.
- `python3 -m ruff check src tests` - all checks passed.
- `python3 -m mypy src tests` - success: no issues found in 179 source files.
- `python3 -m pytest tests/test_project_docs.py -q` - 367 passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` - 1777 passed; total coverage 93.92%.
