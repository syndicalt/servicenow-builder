from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from jedi_devproject.provider_settings_safety import (
    validate_provider_api_key,
    validate_provider_model,
)
from jedi_devproject.provider_url_safety import validate_provider_base_url


class ProviderBaseUrlSubclass(str):
    pass


class ProviderTokenSubclass(str):
    pass


def test_validate_provider_api_key_rejects_oversized_value() -> None:
    with pytest.raises(ValueError, match="api_key"):
        validate_provider_api_key("k" * 4097)


def test_validate_provider_model_rejects_oversized_value() -> None:
    with pytest.raises(ValueError, match="model"):
        validate_provider_model("m" * 257)


def test_validate_provider_settings_allow_boundary_values() -> None:
    assert validate_provider_api_key("k" * 4096) == "k" * 4096
    assert validate_provider_model("m" * 256) == "m" * 256


@pytest.mark.parametrize(
    ("field_name", "validator", "value"),
    [
        ("api_key", validate_provider_api_key, None),
        ("api_key", validate_provider_api_key, True),
        ("api_key", validate_provider_api_key, 123),
        ("api_key", validate_provider_api_key, ProviderTokenSubclass("provider-key")),
        ("model", validate_provider_model, None),
        ("model", validate_provider_model, True),
        ("model", validate_provider_model, 123),
        ("model", validate_provider_model, ProviderTokenSubclass("provider-model")),
    ],
)
def test_validate_provider_tokens_reject_non_exact_strings(
    field_name: str,
    validator: Callable[[Any], str],
    value: Any,
) -> None:
    with pytest.raises(ValueError) as exc:
        validator(value)

    assert str(exc.value) == f"{field_name} must be an exact string"


@pytest.mark.parametrize(
    "base_url",
    [
        None,
        True,
        123,
        ProviderBaseUrlSubclass("https://api.provider.example.gov/v1"),
    ],
)
def test_validate_provider_base_url_rejects_non_exact_strings(base_url: object) -> None:
    with pytest.raises(ValueError) as exc:
        validate_provider_base_url(base_url)  # type: ignore[arg-type]

    assert str(exc.value) == "base_url must be an exact string"


@pytest.mark.parametrize(
    "base_url",
    [
        "https://localhost/v1",
        "https://alerts.localhost/v1",
        "https://127.0.0.1/v1",
        "https://[::1]/v1",
        "https://169.254.169.254/latest/meta-data",
        "https://0.0.0.0/v1",
        "https://2130706433/v1",
        "https://0x7f000001/v1",
        "https://2852039166/latest/meta-data",
    ],
)
def test_validate_provider_base_url_rejects_non_public_hosts(base_url: str) -> None:
    with pytest.raises(ValueError, match="base_url") as exc:
        validate_provider_base_url(base_url)

    message = str(exc.value)
    assert "local, private, or link-local addresses" in message
    assert "169.254.169.254" not in message
    assert "2130706433" not in message
