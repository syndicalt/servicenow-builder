# Sprint 655 Change Log

## Provider field-value JSON-scalar normalization boundary

Sprint 655 continued production hardening by tightening shared provider candidate normalization around model-response field values. The provider schema requires each field entry to contain `name` and `value`, and the `value` must be a JSON scalar. The normalizer previously treated a missing `value` key as `None` and allowed arbitrary in-process Python objects, string subclasses, and non-finite floats into the normalized `fields` dictionary.

Provider field entries now must include an explicit `value` key before normalized field insertion. Field values must be exact JSON scalar values: `str`, `bool`, `int`, finite `float`, or `null`. Missing values fail closed with `<Provider> response field entry must include value`. Objects, containers, string subclasses, integer subclasses, non-finite floats, and other unsupported values fail closed with `<Provider> response field value must be a JSON scalar`. Diagnostics do not echo model-provided field values or exception text.

Verification:

- Added 4 failing-first provider-response-normalization tests proving missing values, object values, string-subclass values, and non-finite floats were accepted before implementation.
- `python3 -m pytest tests/test_provider_response_normalization.py::test_provider_candidate_normalization_requires_field_value_key tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_object_field_value_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_field_value_subclass_without_leak tests/test_provider_response_normalization.py::test_provider_candidate_normalization_rejects_non_finite_field_value_without_leak -q`: failed before implementation because unsafe values were accepted.
- `python3 -m pytest tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py -q`: 135 tests passed.
- `ruff check src/jedi_devproject/provider_response_normalization.py tests/test_provider_response_normalization.py tests/test_anthropic_provider.py tests/test_openai_provider.py`: all checks passed.
- `ruff check src tests`: all checks passed.
- `mypy src tests`: success with no issues in 197 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 729 tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2810 tests passed with 93.00% total coverage.
