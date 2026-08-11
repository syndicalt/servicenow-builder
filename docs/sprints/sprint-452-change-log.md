# Sprint 452 Change Log

## Shared sensitive-key unstringifiable input hardening

Hardened the shared sensitive-key classifier so malformed key objects cannot crash diagnostic redaction paths. Prior behavior normalized every key with `str(key)`, which meant an untrusted object with a hostile or broken `__str__` method could raise before caller-specific key sanitization or diagnostic bounds ran.

Sensitive-key normalization now fails closed to an empty canonical key when string conversion raises. Real string keys still normalize with the existing trim, lowercase, and hyphen-to-underscore behavior, so known sensitive variants such as `X-Client-Secret` continue to match the shared vocabulary.

## Verification

- Added 2 failing-first sensitive-key tests covering unstringifiable objects and existing string variant normalization.
- `python3 -m pytest tests/test_sensitive_keys.py -q`: failed before implementation because `normalize_sensitive_key()` called the key object's `__str__`.
- `python3 -m pytest tests/test_sensitive_keys.py -q`: 2 tests passed.
- `python3 -m pytest tests/test_alert_delivery.py tests/test_url_query_safety.py tests/test_runtime_redaction.py -q`: 84 adjacent redaction and alert tests passed.
- `python3 -m ruff check src tests`: all checks passed.
- `python3 -m mypy src tests`: no issues found in 195 source files.
- `python3 -m pytest tests/test_project_docs.py -q`: 526 documentation tests passed.
- `python3 -m pytest --cov=jedi_devproject --cov-report=term --cov-fail-under=90 -q`: 2343 total tests passed at 93.84% coverage.
