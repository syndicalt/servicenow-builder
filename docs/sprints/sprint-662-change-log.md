# Sprint 662 Change Log

## Provider numeric field-value safe JSON boundary

Sprint 662 continued production hardening by bounding provider numeric field values to an interoperable JSON-safe range. Earlier sprints rejected non-finite floats and non-JSON scalar values, but exact integers and finite floats outside the safe cross-runtime range could still enter normalized candidate fields. That created avoidable precision and serialization risk across Python, JSON, JavaScript-like review tooling, and ServiceNow transport handling.

Provider numeric field values now must be within `-9007199254740991..9007199254740991`. Exact integers and finite floats outside that range fail closed with `<Provider> response field numeric value is outside safe JSON range`. The diagnostic does not echo the submitted numeric value.

Verification:

- Added 4 failing-first provider-response-normalization assertions proving unsafe numeric field values were accepted before implementation while boundary-safe integer and float values remain accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_numeric_value_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_safe_numeric_value -q`: failed before implementation because unsafe numeric field values were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_unsafe_numeric_value_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_accepts_safe_numeric_value -q`: 4 tests passed.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_662_documents_provider_numeric_field_value_bounds -q`: failed before documentation because the Sprint 662 change log did not exist.
- `python3 -m pytest tests/test_project_docs.py::test_sprint_662_documents_provider_numeric_field_value_bounds -q`: 1 test passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 159 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py tests/test_project_docs.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 736 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2841 tests passed with 93.03% total coverage.
