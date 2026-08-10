"""Shared lifecycle webhook credential policy."""

from __future__ import annotations

from jedi_devproject.url_query_safety import has_whitespace_or_control_character

MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES = 8 * 1024


def lifecycle_webhook_credential_byte_length(value: str) -> int:
    """Return the UTF-8 byte length used for startup diagnostics."""
    return len(value.encode("utf-8"))


def is_malformed_lifecycle_webhook_credential(value: str) -> bool:
    try:
        encoded_value = value.encode("ascii")
    except UnicodeEncodeError:
        return True
    return (
        len(encoded_value) > MAX_LIFECYCLE_WEBHOOK_CREDENTIAL_BYTES
        or value != value.strip()
        or has_whitespace_or_control_character(value)
    )
