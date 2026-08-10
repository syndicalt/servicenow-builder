"""Shared validation for model-provider settings."""

from __future__ import annotations

from jedi_devproject.url_query_safety import has_whitespace_or_control_character

MAX_PROVIDER_API_KEY_CHARS = 4096
MAX_PROVIDER_MODEL_CHARS = 256


def validate_provider_api_key(value: str) -> str:
    """Validate a model-provider API key before transport construction."""
    return _validate_single_token_provider_value(
        value,
        field_name="api_key",
        max_chars=MAX_PROVIDER_API_KEY_CHARS,
    )


def validate_provider_model(value: str) -> str:
    """Validate a model-provider model identifier before request construction."""
    return _validate_single_token_provider_value(
        value,
        field_name="model",
        max_chars=MAX_PROVIDER_MODEL_CHARS,
    )


def _validate_single_token_provider_value(
    value: str,
    *,
    field_name: str,
    max_chars: int,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an exact string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > max_chars:
        raise ValueError(f"{field_name} must be <= {max_chars} characters")
    if has_whitespace_or_control_character(value):
        raise ValueError(f"{field_name} must not contain whitespace or control characters")
    return value
