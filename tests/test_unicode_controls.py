from __future__ import annotations

from typing import Any

import pytest

from jedi_devproject.unicode_controls import is_control_character


class StringSubclass(str):
    pass


@pytest.mark.parametrize(
    ("character", "expected_message"),
    [
        (None, "character must be an exact string"),
        (True, "character must be an exact string"),
        (b"\n", "character must be an exact string"),
        (StringSubclass("\n"), "character must be an exact string"),
        ("ab", "character must be a single character"),
        ("", "character must be a single character"),
    ],
)
def test_is_control_character_rejects_malformed_inputs(
    character: Any,
    expected_message: str,
) -> None:
    with pytest.raises(ValueError) as exc:
        is_control_character(character)

    assert str(exc.value) == expected_message


@pytest.mark.parametrize(
    "character",
    [
        "\x00",
        "\n",
        "\t",
        "\x1f",
        "\x7f",
        "\x85",
        "\x9f",
        "\u200b",
        "\u200d",
        "\ud83d",
    ],
)
def test_is_control_character_detects_unicode_controls(character: str) -> None:
    assert is_control_character(character) is True


@pytest.mark.parametrize(
    "character",
    [
        " ",
        "A",
        "0",
        "_",
        "é",
        "😀",
        "\u4e2d",
    ],
)
def test_is_control_character_allows_printable_and_separator_characters(character: str) -> None:
    assert is_control_character(character) is False
