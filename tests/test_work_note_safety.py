from collections.abc import Iterator
from typing import Any

from jedi_devproject.literal_secret_values import safe_literal_secret_values
from jedi_devproject.work_note_safety import (
    NON_STRING_WORK_NOTE_VALUE_LABEL,
    safe_work_note_value,
)


class _HostileText(str):
    def __str__(self) -> str:
        raise AssertionError("client_secret=hostile-string-secret")


class _HostileObject:
    def __str__(self) -> str:
        raise AssertionError("client_secret=hostile-object-secret")


class _HostileSecretValues:
    def __iter__(self) -> Iterator[str]:
        raise AssertionError("client_secret=hostile-secret-iterator")


class _SecretValueSubclass(str):
    pass


class _PartiallyHostileSecretValues:
    def __iter__(self) -> Iterator[str]:
        yield "longer-secret"
        yield "secret"
        raise AssertionError("client_secret=partial-secret-iterator")


def test_safe_literal_secret_values_keeps_prior_values_when_iterator_fails() -> None:
    rendered = safe_literal_secret_values(_PartiallyHostileSecretValues())

    assert rendered == ("longer-secret", "secret")
    assert "partial-secret-iterator" not in rendered


def test_safe_work_note_value_rejects_string_subclasses_without_coercion() -> None:
    rendered = safe_work_note_value(_HostileText("client_secret=payload-secret"))

    assert rendered == NON_STRING_WORK_NOTE_VALUE_LABEL
    assert "payload-secret" not in rendered


def test_safe_work_note_value_ignores_hostile_secret_iterator_for_exact_strings() -> None:
    rendered = safe_work_note_value(
        "ready client_secret=payload-secret",
        secret_values=_HostileSecretValues(),
    )

    assert rendered == "ready client_secret=***REDACTED***"
    assert "hostile-secret-iterator" not in rendered
    assert "payload-secret" not in rendered


def test_safe_work_note_value_ignores_non_exact_literal_secret_values() -> None:
    secret_values: list[Any] = [
        "literal-secret",
        _SecretValueSubclass("subclass-secret"),
        123,
    ]
    rendered = safe_work_note_value(
        "ready literal-secret subclass-secret client_secret=payload-secret",
        secret_values=secret_values,
    )

    assert rendered == (
        "ready ***REDACTED*** subclass-secret client_secret=***REDACTED***"
    )
    assert "payload-secret" not in rendered


def test_safe_work_note_value_rejects_non_strings_without_coercion() -> None:
    rendered = safe_work_note_value(_HostileObject())

    assert rendered == NON_STRING_WORK_NOTE_VALUE_LABEL
    assert "hostile-object-secret" not in rendered


def test_safe_work_note_value_skips_secret_iterator_for_rejected_values() -> None:
    rendered = safe_work_note_value(
        _HostileText("client_secret=payload-secret"),
        secret_values=_HostileSecretValues(),
    )

    assert rendered == NON_STRING_WORK_NOTE_VALUE_LABEL
