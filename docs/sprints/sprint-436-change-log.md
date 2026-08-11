# Sprint 436 Change Log

## Lifecycle webhook invalid UTF-8 JSON rejection

Hardened lifecycle webhook JSON parsing so invalid UTF-8 request bodies fail closed with the same stable `422 invalid lifecycle webhook JSON` response as malformed JSON syntax. Prior behavior caught `json.JSONDecodeError` but allowed `UnicodeDecodeError` from `json.loads(body)` to escape when the authenticated request body contained invalid UTF-8 bytes.

The webhook still authenticates over the exact raw request body before parsing. After authentication, both JSON syntax failures and UTF-8 decode failures are classified as invalid lifecycle JSON without echoing submitted body fragments, credential-like keys, or malformed byte content.

## Verification

- Added 1 failing-first lifecycle webhook test covering an HMAC-signed invalid UTF-8 JSON body containing a `client_secret` key.
- `python3 -m pytest tests/test_lifecycle_api.py -q -k "invalid_json_before_recording or invalid_utf8_json"`: failed before implementation because `UnicodeDecodeError` escaped from `json.loads(body)`.
- `python3 -m pytest tests/test_lifecycle_api.py -q -k "invalid_json_before_recording or invalid_utf8_json"`: 2 tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 193 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 510 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2295 total tests passed at 93.96% coverage.
