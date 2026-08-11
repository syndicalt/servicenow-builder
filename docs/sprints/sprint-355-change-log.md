# Sprint 355 Change Log

## Provider successful-output parse bounds

Hardened successful model-provider response parsing for both OpenAI Responses and Anthropic
Messages adapters. API error diagnostics were already redacted and bounded, but successful `200`
responses could still provide arbitrarily large model output text to `json.loads`. That made a
malformed or unexpectedly large provider response an avoidable CPU and memory pressure path inside
fulfillment workers.

Both adapters now define explicit successful-output limits of 1,000,000 characters and reject
oversized output before JSON parsing. The rejection diagnostics are fixed, name the relevant limit,
and do not echo the model output. Valid structured candidate responses continue through the existing
normalization and downstream packet validators.

## Tests

- Failing-first coverage: 2 tests failed before implementation because neither provider exposed or
  enforced a successful-output parse limit.
- Focused verification: `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q -k "oversized_output_before_json_parse"` passed with 2 tests after implementation.
- Provider regression verification: `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q` passed with 98 tests.
- Full verification gate: `python3 -m ruff check src tests && python3 -m mypy src tests && python3 -m pytest tests/test_project_docs.py -q && python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed with all checks passed, no issues found in 187 source files, 429 documentation tests passed, and 2035 total tests passed at 94.05% coverage.
