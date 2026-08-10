"""Shared admin bearer token policy for startup and request-time validation."""

from __future__ import annotations

from jedi_devproject.url_query_safety import has_whitespace_or_control_character

MAX_ADMIN_BEARER_TOKEN_BYTES = 8 * 1024


def admin_bearer_token_byte_length(value: str) -> int:
    """Return the UTF-8 byte length used for startup diagnostics."""
    return len(value.encode("utf-8"))


def has_non_ascii_admin_bearer_token_character(value: str) -> bool:
    return not value.isascii()


def is_malformed_admin_bearer_token(value: str) -> bool:
    try:
        encoded_value = value.encode("ascii")
    except UnicodeEncodeError:
        return True
    return (
        len(encoded_value) > MAX_ADMIN_BEARER_TOKEN_BYTES
        or value != value.strip()
        or has_whitespace_or_control_character(value)
    )
