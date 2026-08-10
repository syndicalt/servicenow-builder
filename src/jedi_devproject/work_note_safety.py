"""Sanitizers for human-readable ServiceNow work-note values."""

from __future__ import annotations

from collections.abc import Iterable

from jedi_devproject.diagnostic_redaction import _redact_diagnostic_text
from jedi_devproject.literal_secret_values import safe_literal_secret_values

MAX_WORK_NOTE_VALUE_CHARS = 500
WORK_NOTE_TRUNCATION_MARKER = "...[truncated]"
NON_STRING_WORK_NOTE_VALUE_LABEL = "[non-string work note value]"


def safe_work_note_value(
    value: object,
    *,
    secret_values: Iterable[str] = (),
    max_chars: int = MAX_WORK_NOTE_VALUE_CHARS,
) -> str:
    """Redact, normalize, and bound one untrusted value before work-note formatting."""
    if type(value) is not str:
        return NON_STRING_WORK_NOTE_VALUE_LABEL
    redacted = _redact_literal_secrets(value, secret_values)
    redacted = _redact_diagnostic_text(redacted) or ""
    redacted = _redact_literal_secrets(redacted, secret_values)
    normalized = " ".join(redacted.split())
    if len(normalized) <= max_chars:
        return normalized
    return (
        normalized[: max_chars - len(WORK_NOTE_TRUNCATION_MARKER)].rstrip()
        + WORK_NOTE_TRUNCATION_MARKER
    )


def _redact_literal_secrets(value: str, secret_values: Iterable[str]) -> str:
    redacted = value
    for secret in safe_literal_secret_values(secret_values):
        redacted = redacted.replace(secret, "***REDACTED***")
    return redacted
