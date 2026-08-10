"""Shared admin Basic-auth credential policy."""

from __future__ import annotations

from jedi_devproject.url_query_safety import has_whitespace_or_control_character

MAX_BASIC_AUTH_ENCODED_BYTES = 8 * 1024
MAX_BASIC_AUTH_CREDENTIAL_BYTES = 8 * 1024


def is_malformed_basic_auth_encoded_section(value: str) -> bool:
    if value != value.strip() or has_whitespace_or_control_character(value):
        return True
    try:
        encoded_value = value.encode("ascii")
    except UnicodeEncodeError:
        return True
    return len(encoded_value) > MAX_BASIC_AUTH_ENCODED_BYTES


def basic_auth_credential_byte_length(value: str) -> int:
    """Return the UTF-8 byte length used for settings diagnostics."""
    return len(value.encode("utf-8"))


def is_malformed_admin_console_credential_part(value: str) -> bool:
    try:
        encoded_value = value.encode("ascii")
    except UnicodeEncodeError:
        return True
    return (
        len(encoded_value) > MAX_BASIC_AUTH_CREDENTIAL_BYTES
        or value != value.strip()
        or has_whitespace_or_control_character(value)
    )
