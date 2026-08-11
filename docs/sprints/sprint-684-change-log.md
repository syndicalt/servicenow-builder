# Sprint 684 Change Log - Provider prompt payload exact-JSON boundary

## Scope

Hardened the shared model-provider prompt payload serializer so OpenAI and Anthropic receive prompt
payload JSON only after the payload has crossed an exact JSON-type boundary. The shared contract now
rejects non-exact containers, object keys, and scalar subclasses before `json.dumps` can execute or
normalize them.

## Tests First

- Added 4 failing-first provider prompt-payload assertions:
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_mapping_subclass_without_leak`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_key_subclass_without_normalization`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_list_subclass_without_leak`
  - `tests/test_provider_contract.py::test_implementation_payload_rejects_string_subclass_without_normalization`
- Initial failures proved direct serialization could execute hostile mapping and list hooks raising
  `client_secret=prompt-mapping-secret` and `client_secret=prompt-list-secret`, and could silently
  normalize key and scalar string subclasses into prompt JSON.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_684_documents_provider_prompt_payload_exact_json_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- `implementation_payload_json` now copies payloads through a strict exact-JSON clone before
  serialization.
- The serializer accepts exact dictionaries with exact string keys, exact lists, exact strings, exact
  integers, exact floats, exact booleans, and null.
- Unsupported payload shapes raise the provider-specific error factory with a fixed diagnostic:
  `Model provider prompt payload contains unsupported JSON value types`.
- Existing non-finite numeric rejection remains separate and still reports:
  `Model provider prompt payload contains non-finite numeric values`.
- Documented the shared provider prompt payload boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_provider_contract.py -q -k "payload_rejects"` failed first because
  direct `json.dumps` executed hostile container hooks and silently normalized subclasses.
- `python3 -m pytest tests/test_provider_contract.py -q` passed, 9 tests.
- `python3 -m pytest tests/test_openai_provider.py tests/test_anthropic_provider.py -q -k "posts_structured_output_request or sends_same_instructions_and_payload_as_openai or rejects_non_finite_prompt_payload_before_transport or request_body_is_deterministic"`
  passed, 6 tests.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_684` failed first while this changelog
  was missing.
- `python3 -m pytest tests/test_project_docs.py -q -k "sprint_683 or sprint_684"` passed, 2 tests.
- `python3 -m pytest tests/test_provider_contract.py tests/test_openai_provider.py tests/test_anthropic_provider.py -q`
  passed, 145 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  2917 tests with 93.13% total coverage.
