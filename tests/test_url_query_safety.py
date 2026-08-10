from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from jedi_devproject.unicode_controls import is_control_character
from jedi_devproject.url_query_safety import (
    has_encoded_whitespace_or_control_character,
    has_whitespace_or_control_character,
    query_pair_candidates,
    query_pairs,
    sensitive_query_keys,
)


class QueryStringSubclass(str):
    pass


@pytest.mark.parametrize(
    ("helper", "value", "expected_message"),
    [
        (
            has_whitespace_or_control_character,
            None,
            "value must be an exact string",
        ),
        (
            has_encoded_whitespace_or_control_character,
            True,
            "value must be an exact string",
        ),
        (
            sensitive_query_keys,
            123,
            "query must be an exact string",
        ),
        (
            query_pairs,
            QueryStringSubclass("api_key=secret"),
            "query must be an exact string",
        ),
        (
            query_pair_candidates,
            b"api_key=secret",
            "query must be an exact string",
        ),
    ],
)
def test_url_query_helpers_reject_non_exact_strings(
    helper: Callable[[Any], object],
    value: Any,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError) as exc:
        helper(value)

    assert str(exc.value) == expected_message


@pytest.mark.parametrize(
    ("character", "expected_message"),
    [
        (None, "character must be an exact string"),
        (True, "character must be an exact string"),
        (b"\n", "character must be an exact string"),
        (QueryStringSubclass("\n"), "character must be an exact string"),
        ("ab", "character must be a single character"),
        ("", "character must be a single character"),
    ],
)
def test_is_control_character_rejects_non_exact_single_characters(
    character: Any,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError) as exc:
        is_control_character(character)

    assert str(exc.value) == expected_message


@pytest.mark.parametrize(
    "value",
    [
        "https://example.gov/path%250aX-Injected",
        "https://example.gov/path%2509tab",
    ],
)
def test_has_encoded_whitespace_or_control_character_rejects_double_encoded_values(
    value: str,
) -> None:
    assert has_encoded_whitespace_or_control_character(value) is True


def test_has_encoded_whitespace_or_control_character_allows_benign_encoded_values() -> None:
    assert has_encoded_whitespace_or_control_character("https://example.gov/a%252Fb") is False


@pytest.mark.parametrize(
    "value",
    [
        "https://example.gov/path%25C2%2585nel",  # double-encoded U+0085
        "https://example.gov/path%25E2%2580%258B",  # double-encoded U+200B zero-width space
    ],
)
def test_has_encoded_whitespace_or_control_character_rejects_unicode_controls(
    value: str,
) -> None:
    assert has_encoded_whitespace_or_control_character(value) is True
