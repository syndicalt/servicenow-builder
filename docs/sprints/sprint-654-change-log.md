# Sprint 654 Change Log

## Provider candidate exact-object-key normalization boundary

Sprint 654 continued production hardening by tightening shared provider candidate normalization around model-response object keys. The provider normalizer already required exact dictionaries and lists, but exact dictionaries could still contain string-subclass or non-string keys that survived normalization through root and change object copies. Those unsafe keys could then reach later validators, diagnostics, or JSON serialization paths outside the original provider boundary.

Provider candidate response object keys now must be exact strings on the root candidate, each change object, and each field-entry object before lookup, copying, or normalized output. String-subclass keys and non-string keys fail closed with fixed diagnostics such as `<Provider> response candidate keys must be exact strings`, `<Provider> response change keys must be exact strings`, and `<Provider> response field entry keys must be exact strings`. The diagnostics do not echo model-provided keys, values, or exception text.

Verification:

- Added 3 failing-first provider-response-normalization tests proving unsafe root, change, and field-entry string-subclass keys were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_root_key_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_change_key_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_field_key_subclass_without_leak -q`: failed before implementation because unsafe keys were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 131 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 728 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2805 tests passed with 93.01% total coverage.
