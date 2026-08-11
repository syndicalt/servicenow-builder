# Sprint 712 Change Log - ServiceNow transport JSON body exact-JSON boundary

## Scope

Hardened ServiceNow transport JSON request-body serialization so application/json dictionary bodies
must contain only exact JSON containers and scalars before `json.dumps()` is called.

## Tests First

- Added 2 failing-first ServiceNow transport JSON body assertions:
  - `tests/test_servicenow.py::test_urllib_transport_rejects_json_body_string_subclass_key_before_serialization`
  - `tests/test_servicenow.py::test_urllib_transport_rejects_json_body_non_json_value_before_serialization`
- Initial failures proved `UrllibTransport.send()` accepted a string subclass as a JSON object key
  and proceeded to opener construction, while an unsupported nested Python object reached
  `json.dumps()` and raised a raw `TypeError`. The hostile fixtures carried
  `client_secret=servicenow-json-key-secret` and `client_secret=servicenow-json-value-secret`.
- Added 1 failing-first documentation assertion:
  `tests/test_project_docs.py::test_sprint_712_documents_servicenow_transport_json_body_exact_json_boundary`
- Initial documentation failure proved this sprint log did not exist yet.

## Changes

- Added `_servicenow_json_body()` to recursively validate JSON request bodies before serialization.
- JSON request bodies now require exact dictionaries, exact lists, exact string keys, exact strings,
  exact booleans, exact integers, finite exact floats, and null values.
- Non-finite floats preserve the existing
  `ServiceNow JSON request body contains non-finite numeric values` diagnostic.
- Unsupported Python values, string subclasses, numeric subclasses, bytes, tuples, and arbitrary
  objects fail with `ServiceNow JSON request body contains non-JSON values`.
- Documented the ServiceNow transport JSON body exact-JSON boundary in the operator guide.

## Verification

- `python3 -m pytest tests/test_servicenow.py -q -k "json_body_string_subclass_key or json_body_non_json_value"`
  failed first with 2 failures.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_712` failed first with 1 failure.
- `python3 -m pytest tests/test_servicenow.py -q -k "json_body_string_subclass_key or json_body_non_json_value or non_finite_json_request_body or form_body_string_subclass or encodes_query_and_form_body or body_bytes_subclass or headers_dict_subclass or body_dict_subclass or query_params_dict_subclass or handles_request_without_params_or_body"`
  passed, 19 tests and 238 deselected.
- `python3 -m pytest tests/test_project_docs.py -q -k sprint_712` passed, 1 test and 785
  deselected.
- `python3 -m pytest tests/test_servicenow.py -q` passed, 257 tests.
- `ruff check src tests` passed.
- `mypy src tests` passed across 197 source files.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q` passed,
  3,008 tests with 93.29% total coverage.
