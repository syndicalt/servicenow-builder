# Sprint 653 Change Log

## Provider candidate root exact-object normalization boundary

Sprint 653 continued production hardening by tightening the shared provider candidate normalizer around the root candidate object. The normalizer already required exact nested response containers, but it still read `candidate.get("changes")` before validating the root candidate object. A malformed in-process provider response could pass a dictionary subclass that executed a custom `get()` hook before normalization failed.

Provider candidate roots now must be exact JSON-native dictionaries before the normalizer reads `changes` or performs any nested response-container validation. Dictionary subclasses and non-dictionary values fail closed with `<Provider> response candidate must be an exact object`. The diagnostic does not echo model-provided values or exception text, and nested exact-container checks remain in place for `changes`, change objects, `fields`, and field entries.

Verification:

- Added 1 failing-first provider-response-normalization test proving a hostile root candidate dictionary subclass executed `get()` before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_dict_subclass_without_leak -q`: failed before implementation because the hostile root `get()` hook ran.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 128 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 727 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2801 tests passed with 93.00% total coverage.
