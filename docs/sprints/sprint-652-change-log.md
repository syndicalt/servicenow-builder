# Sprint 652 Change Log

## Provider candidate exact-container normalization boundary

Sprint 652 continued production hardening by tightening shared provider candidate normalization around model-response container shapes. The shared OpenAI and Anthropic normalizer previously accepted `list` and `dict` subclasses for `changes`, change objects, change `fields`, and field entries before length checks, mapping lookups, iteration, and field normalization. A malformed in-process provider response could execute custom container hooks before normalization failed.

Provider candidate response containers now must be exact JSON-native lists or dictionaries at every normalization boundary. `changes` and change `fields` must be exact lists; change objects and field entries must be exact dictionaries. Container subclasses and non-container values fail closed with fixed exact-container diagnostics before length checks, lookups, iteration, copying, or field normalization can run. Diagnostics do not echo model-provided values.

Verification:

- Added 4 failing-first provider-response-normalization tests proving hostile `list` and `dict` subclasses executed `__len__` or `get()` hooks before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_changes_list_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_change_dict_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_fields_list_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_field_dict_subclass_without_leak -q`: failed before implementation because hostile container hooks ran.
- `python3 -m pytest tests/test_provider_response_normalization.py -q`: 10 tests passed.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 127 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 726 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2799 tests passed with 93.00% total coverage.
