from __future__ import annotations

import pytest

from jedi_devproject.models import CandidateChange
from jedi_devproject.validation_helpers import (
    TRUTHY_TOKENS,
    bool_text,
    bool_value,
    optional_int,
    reference_value,
    single_insert_change,
    slug,
    string_list,
)


def test_bool_value_accepts_truthy_tokens() -> None:
    assert bool_value("1") is True
    assert bool_value("true") is True
    assert bool_value(" Yes ") is True
    assert bool_value(True) is True


def test_bool_value_rejects_falsy_tokens() -> None:
    assert bool_value("0") is False
    assert bool_value("false") is False
    assert bool_value("no") is False
    assert bool_value(False) is False
    assert bool_value("") is False
    assert bool_value("maybe") is False


def test_bool_value_uses_default_only_for_none() -> None:
    assert bool_value(None) is False
    assert bool_value(None, default=True) is True
    assert bool_value("", default=True) is False
    assert bool_value("false", default=True) is False


def test_bool_value_supports_custom_truthy_tokens() -> None:
    truthy = TRUTHY_TOKENS | {"required", "mandatory"}
    assert bool_value("required", truthy=truthy) is True
    assert bool_value(" Mandatory ", truthy=truthy) is True
    assert bool_value("required") is False
    assert bool_value("optional", truthy=truthy) is False


def test_bool_text_renders_lowercase_tokens() -> None:
    assert bool_text(True) == "true"
    assert bool_text(False) == "false"


def test_string_list_keeps_non_blank_list_items() -> None:
    assert string_list(["a", " ", "", "b", 3]) == ["a", "b", "3"]
    assert string_list([]) == []


def test_string_list_splits_comma_separated_text() -> None:
    assert string_list("one, two , ,three") == ["one", "two", "three"]
    assert string_list("  solo  ") == ["solo"]


def test_string_list_returns_empty_for_blank_values() -> None:
    assert string_list(None) == []
    assert string_list("") == []
    assert string_list("   ") == []
    assert string_list(0) == []


def test_string_list_none_token_is_kept_by_default() -> None:
    assert string_list("none") == ["none"]
    assert string_list(" None ") == ["None"]


def test_string_list_none_token_can_be_ignored() -> None:
    assert string_list("none", ignore_none_token=True) == []
    assert string_list(" NONE ", ignore_none_token=True) == []
    assert string_list("none,one", ignore_none_token=True) == ["none", "one"]
    assert string_list(["none"], ignore_none_token=True) == ["none"]


def test_slug_normalizes_text_to_identifier_characters() -> None:
    assert slug("JEDI Incident Priority Note", default="fallback") == "jedi_incident_priority_note"
    assert slug("  A-b.C  ", default="fallback") == "a_b_c"
    assert slug("__keep_underscores__", default="fallback") == "keep_underscores"


def test_slug_falls_back_to_default_when_nothing_remains() -> None:
    assert slug("", default="generated_rule") == "generated_rule"
    assert slug("!!!", default="generated_rule") == "generated_rule"
    assert slug("...", default="") == ""


def test_optional_int_parses_digit_strings_only() -> None:
    assert optional_int("42") == 42
    assert optional_int(" 7 ") == 7
    assert optional_int(7) == 7
    assert optional_int("") is None
    assert optional_int(None) is None
    assert optional_int("abc") is None
    assert optional_int("-5") is None
    assert optional_int("4.2") is None


def test_reference_value_reads_value_key_from_reference_dicts() -> None:
    assert reference_value({"value": "sys-id", "display_value": "Display"}) == "sys-id"
    assert reference_value({"display_value": "Display"}) == ""
    assert reference_value({}) == ""


def test_reference_value_coerces_scalars_to_text() -> None:
    assert reference_value("plain") == "plain"
    assert reference_value(None) == ""
    assert reference_value("") == ""
    assert reference_value(123) == "123"


def _change(**overrides: object) -> CandidateChange:
    values: dict[str, object] = {
        "table": "sys_script",
        "operation": "insert",
        "fields": {"name": "JEDI Rule"},
    }
    values.update(overrides)
    return CandidateChange.model_validate(values)


def test_single_insert_change_returns_the_only_change() -> None:
    change = _change()

    selected = single_insert_change([change], table="sys_script", label="Business Rule")

    assert selected is change


def test_single_insert_change_rejects_empty_and_multiple_changes() -> None:
    message = "Business Rule handoff requires exactly one sys_script change"
    with pytest.raises(ValueError, match=message):
        single_insert_change([], table="sys_script", label="Business Rule")
    with pytest.raises(ValueError, match=message):
        single_insert_change(
            [_change(), _change()],
            table="sys_script",
            label="Business Rule",
        )


def test_single_insert_change_rejects_unexpected_table() -> None:
    with pytest.raises(ValueError, match="Client Script handoff requires a sys_script_client"):
        single_insert_change(
            [_change(table="sys_script")],
            table="sys_script_client",
            label="Client Script",
        )


def test_single_insert_change_rejects_non_insert_operations() -> None:
    with pytest.raises(ValueError, match="Script Include handoff supports insert only"):
        single_insert_change(
            [_change(table="sys_script_include", operation="update")],
            table="sys_script_include",
            label="Script Include",
        )
