from __future__ import annotations

from jedi_devproject.sensitive_keys import is_sensitive_key, normalize_sensitive_key


class UnstringifiableSensitiveKey:
    def __str__(self) -> str:
        raise ValueError("client_secret=key-secret")


class StringifiableSensitiveKey:
    def __str__(self) -> str:
        return "client_secret"


class SensitiveKeySubclass(str):
    pass


def test_sensitive_key_classifier_rejects_unstringifiable_keys() -> None:
    key = UnstringifiableSensitiveKey()

    assert normalize_sensitive_key(key) == ""
    assert is_sensitive_key(key) is False


def test_sensitive_key_classifier_rejects_non_exact_strings() -> None:
    stringified_key = StringifiableSensitiveKey()
    subclass_key = SensitiveKeySubclass("client_secret")

    assert normalize_sensitive_key(stringified_key) == ""
    assert is_sensitive_key(stringified_key) is False
    assert normalize_sensitive_key(subclass_key) == ""
    assert is_sensitive_key(subclass_key) is False


def test_sensitive_key_classifier_still_matches_string_variants() -> None:
    assert normalize_sensitive_key(" X-Client-Secret ") == "x_client_secret"
    assert is_sensitive_key(" X-Client-Secret ") is True
