import pytest

from jedi_devproject.numeric_settings import (
    parse_optional_ascii_decimal_float,
    parse_optional_base10_int,
)


def test_parse_optional_base10_int_accepts_ascii_digits() -> None:
    assert parse_optional_base10_int("120", name="JEDI_LIMIT") == 120


@pytest.mark.parametrize("value", ["+120", "1_000", "１２", "١٢"])
def test_parse_optional_base10_int_rejects_non_ascii_decimal_tokens(value: str) -> None:
    with pytest.raises(ValueError, match="JEDI_LIMIT") as exc:
        parse_optional_base10_int(value, name="JEDI_LIMIT")

    message = str(exc.value)
    assert "ASCII base-10 digits only" in message
    assert value not in message


def test_parse_optional_base10_int_rejects_padding_without_echo() -> None:
    with pytest.raises(ValueError, match="JEDI_LIMIT") as exc:
        parse_optional_base10_int("12\tfallback", name="JEDI_LIMIT")

    message = str(exc.value)
    assert "without padding or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2", 2.0),
        ("2.5", 2.5),
        ("0.25", 0.25),
    ],
)
def test_parse_optional_ascii_decimal_float_accepts_fixed_ascii_decimals(
    value: str,
    expected: float,
) -> None:
    assert parse_optional_ascii_decimal_float(value, name="JEDI_TIMEOUT") == expected


@pytest.mark.parametrize("value", ["+2.5", "-2.5", "1_000.5", "1e3", "１２.5"])
def test_parse_optional_ascii_decimal_float_rejects_non_fixed_decimal_tokens(
    value: str,
) -> None:
    with pytest.raises(ValueError, match="JEDI_TIMEOUT") as exc:
        parse_optional_ascii_decimal_float(value, name="JEDI_TIMEOUT")

    message = str(exc.value)
    assert "ASCII decimal number" in message
    assert value not in message


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_parse_optional_ascii_decimal_float_rejects_non_finite_tokens(value: str) -> None:
    with pytest.raises(ValueError, match="JEDI_TIMEOUT") as exc:
        parse_optional_ascii_decimal_float(value, name="JEDI_TIMEOUT")

    assert "finite number" in str(exc.value)


def test_parse_optional_ascii_decimal_float_rejects_padding_without_echo() -> None:
    with pytest.raises(ValueError, match="JEDI_TIMEOUT") as exc:
        parse_optional_ascii_decimal_float("2.5\tfallback", name="JEDI_TIMEOUT")

    message = str(exc.value)
    assert "without padding or control characters" in message
    assert "fallback" not in message
    assert "\t" not in message
