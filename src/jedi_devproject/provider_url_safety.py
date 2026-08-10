"""Provider endpoint URL validation for model adapters."""

from __future__ import annotations

from urllib.parse import urlsplit

from jedi_devproject.url_host_safety import is_non_public_hostname, normalize_hostname
from jedi_devproject.url_query_safety import (
    has_encoded_whitespace_or_control_character,
    has_whitespace_or_control_character,
)

MAX_PROVIDER_BASE_URL_CHARS = 2048


def validate_provider_base_url(value: str) -> str:
    """Validate a model-provider base URL before request construction."""
    if type(value) is not str:
        raise ValueError("base_url must be an exact string")
    if value == "":
        raise ValueError("base_url must not be empty")
    if len(value) > MAX_PROVIDER_BASE_URL_CHARS:
        raise ValueError(f"base_url must be <= {MAX_PROVIDER_BASE_URL_CHARS} characters")
    if has_whitespace_or_control_character(value):
        raise ValueError("base_url must not contain whitespace or control characters")
    if has_encoded_whitespace_or_control_character(value):
        raise ValueError(
            "base_url must not contain encoded whitespace or control characters"
        )

    parsed = urlsplit(value)
    if parsed.scheme != "https":
        raise ValueError("base_url must be an absolute HTTPS URL")
    host = normalize_hostname(parsed.hostname or "")
    if not host:
        raise ValueError("base_url must include a hostname")
    if is_non_public_hostname(host):
        raise ValueError("base_url must not target local, private, or link-local addresses")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("base_url must not include embedded credentials")
    if parsed.query:
        raise ValueError("base_url must not include query parameters")
    if parsed.fragment:
        raise ValueError("base_url must not include a fragment")
    return value
