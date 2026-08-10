from __future__ import annotations

from typing import Any

import pytest

import jedi_devproject.provider_response_normalization as provider_response_normalization
from jedi_devproject.provider_response_normalization import (
    normalise_provider_candidate_response,
)


class ProviderNormalizationError(RuntimeError):
    pass


def _normalise(candidate: dict[str, Any]) -> dict[str, Any]:
    return normalise_provider_candidate_response(
        candidate,
        provider_name="TestProvider",
        error_factory=ProviderNormalizationError,
    )


def test_provider_candidate_normalization_rejects_duplicate_field_names() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "fields": [
                    {"name": "element", "value": "u_vendor_reference"},
                    {"name": "element", "value": "client_secret=result-secret"},
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert "field entry names must be unique" in diagnostic
    assert "client_secret" not in diagnostic
    assert "result-secret" not in diagnostic


@pytest.mark.parametrize(
    "field_name",
    [
        " element",
        "elem ent",
        "element\nclient_secret=result-secret",
        "element\u200bclient_secret=result-secret",
    ],
)
def test_provider_candidate_normalization_rejects_unsafe_field_names(
    field_name: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "fields": [{"name": field_name, "value": "u_vendor_reference"}],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert "field entry name must not contain whitespace or control characters" in diagnostic
    assert "client_secret" not in diagnostic
    assert "result-secret" not in diagnostic


@pytest.mark.parametrize(
    "field_name",
    [
        "u-vendor-reference",
        "u.vendor_reference",
        "1u_vendor_reference",
        "u_vendor_reference$client_secret=field-secret",
    ],
)
def test_provider_candidate_normalization_rejects_unsafe_field_identifier_without_leak(
    field_name: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [{"name": field_name, "value": "Vendor Reference"}],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field entry name must be a safe identifier"
    assert "u_vendor_reference" not in diagnostic
    assert "field-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize(
    "field_name",
    [
        "element",
        "u_vendor_reference",
        "x_jedi_app_field",
    ],
)
def test_provider_candidate_normalization_accepts_safe_field_identifier(
    field_name: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [{"name": field_name, "value": "Vendor Reference"}],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    normalised = _normalise(candidate)

    assert normalised["changes"][0]["fields"][field_name] == "Vendor Reference"


def test_provider_candidate_normalization_uses_exported_identifier_pattern_for_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        provider_response_normalization,
        "PROVIDER_SAFE_IDENTIFIER_PATTERN",
        r"^sys_dictionary$",
    )
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "cmdb_ci",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change table must be a safe identifier"
    assert "cmdb_ci" not in diagnostic


def test_provider_candidate_normalization_uses_exported_identifier_pattern_for_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        provider_response_normalization,
        "PROVIDER_SAFE_IDENTIFIER_PATTERN",
        r"^(sys_dictionary|element)$",
    )
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [{"name": "short_description", "value": "Description"}],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field entry name must be a safe identifier"
    assert "short_description" not in diagnostic


def test_provider_candidate_normalization_rejects_oversized_field_name() -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "fields": [
                    {
                        "name": "x" * 201,
                        "value": "client_secret=result-secret",
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert "field entry name exceeds 200 characters" in diagnostic
    assert "client_secret" not in diagnostic
    assert "result-secret" not in diagnostic


def test_provider_candidate_normalization_rejects_field_name_subclass_without_leak() -> None:
    class HostileFieldName(str):
        def __len__(self) -> int:
            raise AssertionError("client_secret=field-name-secret")

    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "fields": [
                    {
                        "name": HostileFieldName("element"),
                        "value": "u_vendor_reference",
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field entry must include a non-empty exact name"
    assert "HostileFieldName" not in diagnostic
    assert "field-name-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_changes_list_subclass_without_leak() -> None:
    class HostileChanges(list[dict[str, Any]]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=changes-secret")

    candidate = {"changes": HostileChanges()}

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response changes must be an exact list"
    assert "HostileChanges" not in diagnostic
    assert "changes-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_empty_changes() -> None:
    candidate: dict[str, Any] = {
        "changes": [],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    assert str(exc.value) == "TestProvider response must include at least one change"


def test_provider_candidate_normalization_rejects_change_dict_subclass_without_leak() -> None:
    class HostileChange(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            raise AssertionError("client_secret=change-secret")

    candidate = {"changes": [HostileChange()]}

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change must be an exact object"
    assert "HostileChange" not in diagnostic
    assert "change-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_fields_list_subclass_without_leak() -> None:
    class HostileFields(list[dict[str, Any]]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=fields-secret")

    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "fields": HostileFields(),
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change fields must be an exact list"
    assert "HostileFields" not in diagnostic
    assert "fields-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_field_dict_subclass_without_leak() -> None:
    class HostileField(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            raise AssertionError("client_secret=field-secret")

    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "fields": [HostileField()],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field entry must be an exact object"
    assert "HostileField" not in diagnostic
    assert "field-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_root_dict_subclass_without_leak() -> None:
    class HostileCandidate(dict[str, Any]):
        def get(self, key: str, default: Any = None) -> Any:
            raise AssertionError("client_secret=root-candidate-secret")

    candidate = HostileCandidate()

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response candidate must be an exact object"
    assert "HostileCandidate" not in diagnostic
    assert "root-candidate-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_root_key_subclass_without_leak() -> None:
    class HostileRootKey(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=root-key-secret")

    candidate = {
        "changes": [],
        HostileRootKey("test_plan"): ["Confirm the field exists."],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response candidate keys must be exact strings"
    assert "HostileRootKey" not in diagnostic
    assert "root-key-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_change_key_subclass_without_leak() -> None:
    class HostileChangeKey(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=change-key-secret")

    candidate = {
        "changes": [
            {
                "fields": [],
                HostileChangeKey("table"): "sys_dictionary",
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change keys must be exact strings"
    assert "HostileChangeKey" not in diagnostic
    assert "change-key-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_field_key_subclass_without_leak() -> None:
    class HostileFieldKey(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=field-key-secret")

    candidate = {
        "changes": [
            {
                "fields": [
                    {
                        "name": "element",
                        HostileFieldKey("value"): "u_vendor_reference",
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field entry keys must be exact strings"
    assert "HostileFieldKey" not in diagnostic
    assert "field-key-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_requires_field_value_key() -> None:
    candidate = {
        "changes": [
            {
                "fields": [
                    {
                        "name": "element",
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    assert str(exc.value) == "TestProvider response field entry must include value"


def test_provider_candidate_normalization_rejects_object_field_value_without_leak() -> None:
    class SecretBearingValue:
        def __str__(self) -> str:
            raise AssertionError("client_secret=field-value-secret")

    candidate = {
        "changes": [
            {
                "fields": [
                    {
                        "name": "element",
                        "value": SecretBearingValue(),
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field value must be a JSON scalar"
    assert "SecretBearingValue" not in diagnostic
    assert "field-value-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_field_value_subclass_without_leak() -> None:
    class HostileFieldValue(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=field-value-secret")

    candidate = {
        "changes": [
            {
                "fields": [
                    {
                        "name": "element",
                        "value": HostileFieldValue("u_vendor_reference"),
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field value must be a JSON scalar"
    assert "HostileFieldValue" not in diagnostic
    assert "field-value-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_non_finite_field_value_without_leak() -> None:
    candidate = {
        "changes": [
            {
                "fields": [
                    {
                        "name": "element",
                        "value": float("nan"),
                    }
                ],
            }
        ]
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field value must be a JSON scalar"
    assert "nan" not in diagnostic.lower()


def test_provider_candidate_normalization_rejects_oversized_string_value_without_leak() -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_script",
                "operation": "insert",
                "fields": [
                    {
                        "name": "script",
                        "value": f"{'x' * 100_001}client_secret=field-value-secret",
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field value exceeds 100000 characters"
    assert "field-value-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_accepts_large_bounded_string_field_value() -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_script",
                "operation": "insert",
                "fields": [
                    {
                        "name": "script",
                        "value": "x" * 100_000,
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    normalised = _normalise(candidate)

    assert normalised["changes"][0]["fields"]["script"] == "x" * 100_000


@pytest.mark.parametrize(
    "control_value",
    [
        "script\x85client_secret=field-secret",
        "script\u200bclient_secret=field-secret",
        "script\ud83dclient_secret=field-secret",
    ],
)
def test_provider_candidate_normalization_rejects_field_value_control_characters_without_leak(
    control_value: str,
) -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_script",
                "operation": "insert",
                "fields": [
                    {
                        "name": "script",
                        "value": control_value,
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field value must not contain control characters"
    assert "field-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_allows_ascii_whitespace_in_script_field_values() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_script",
                "operation": "insert",
                "fields": [
                    {
                        "name": "script",
                        "value": (
                            "if (current.priority == '1') {\n"
                            "\tcurrent.work_notes = 'escalated';\r\n}"
                        ),
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    expected_script = str(candidate["changes"][0]["fields"][0]["value"])

    normalised = _normalise(candidate)

    assert normalised["changes"][0]["fields"]["script"] == expected_script


@pytest.mark.parametrize("value", [9_007_199_254_740_992, 9_007_199_254_740_992.0])
def test_provider_candidate_normalization_rejects_unsafe_numeric_value_without_leak(
    value: int | float,
) -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [
                    {
                        "name": "max_length",
                        "value": value,
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field numeric value is outside safe JSON range"
    assert "9007199254740992" not in diagnostic


@pytest.mark.parametrize("value", [9_007_199_254_740_991, -9_007_199_254_740_991.0])
def test_provider_candidate_normalization_accepts_safe_numeric_value(
    value: int | float,
) -> None:
    candidate = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [
                    {
                        "name": "max_length",
                        "value": value,
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    normalised = _normalise(candidate)

    assert normalised["changes"][0]["fields"]["max_length"] == value


def test_provider_candidate_normalization_rejects_test_plan_list_subclass_without_leak() -> None:
    class HostileTextList(list[str]):
        def __len__(self) -> int:
            raise AssertionError("client_secret=test-plan-secret")

    candidate = {
        "changes": [],
        "test_plan": HostileTextList(),
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response test_plan must be an exact list"
    assert "HostileTextList" not in diagnostic
    assert "test-plan-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_rollback_note_subclass_without_leak() -> None:
    class HostileNote(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=rollback-note-secret")

    candidate = {
        "changes": [],
        "test_plan": [],
        "rollback_notes": [HostileNote("Back out generated changes.")],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response rollback_notes items must be exact strings"
    assert "HostileNote" not in diagnostic
    assert "rollback-note-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("test_plan", ""),
        ("rollback_notes", "   "),
    ],
)
def test_provider_candidate_normalization_rejects_empty_root_text_item(
    label: str,
    value: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }
    candidate[label] = [value]

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    assert (
        str(exc.value)
        == f"TestProvider response {label} items must be non-empty exact strings"
    )


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("test_plan", "Confirm generated change.\nclient_secret=test-plan-secret"),
        ("rollback_notes", "Back out generated change.\x7fclient_secret=rollback-secret"),
    ],
)
def test_provider_candidate_normalization_rejects_root_text_item_control_characters_without_leak(
    label: str,
    value: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }
    candidate[label] = [value]

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert (
        diagnostic
        == f"TestProvider response {label} items must not contain control characters"
    )
    assert "test-plan-secret" not in diagnostic
    assert "rollback-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("test_plan", "Confirm generated change.\u200bclient_secret=unicode-secret"),
        ("rollback_notes", "Back out generated change.\ud83dclient_secret=unicode-secret"),
    ],
)
def test_provider_candidate_normalization_rejects_unicode_control_root_text_items(
    label: str,
    value: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }
    candidate[label] = [value]

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert (
        diagnostic
        == f"TestProvider response {label} items must not contain control characters"
    )
    assert "unicode-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize(
    ("label", "value"),
    [
        ("test_plan", "Confirm the generated change in the target instance."),
        ("rollback_notes", "Remove the generated change through the retrieved Update Set."),
    ],
)
def test_provider_candidate_normalization_accepts_sentence_root_text_item(
    label: str,
    value: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }
    candidate[label] = [value]

    normalised = _normalise(candidate)

    assert normalised[label] == [value]


def test_provider_candidate_normalization_uses_exported_text_pattern_for_root_text_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        provider_response_normalization,
        "PROVIDER_NO_CONTROL_TEXT_PATTERN",
        r"^Approved review item$",
    )
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": ["Confirm generated change."],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response test_plan items must not match text policy"
    assert "Confirm generated change" not in diagnostic


def test_provider_candidate_normalization_requires_root_text_lists() -> None:
    candidate = {
        "changes": [],
        "test_plan": ["Confirm generated changes."],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    assert str(exc.value) == "TestProvider response rollback_notes must be an exact list"


def test_provider_candidate_normalization_rejects_too_many_test_plan_items_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [],
        "test_plan": ["client_secret=test-plan-secret"] * 101,
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response test_plan includes too many items (max 100)"
    assert "test-plan-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_oversized_rollback_note_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [],
        "test_plan": [],
        "rollback_notes": [f"{'x' * 2001} client_secret=rollback-note-secret"],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response rollback_notes item exceeds 2000 characters"
    assert "rollback-note-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_unknown_root_property() -> None:
    candidate: dict[str, Any] = {
        "changes": [],
        "test_plan": [],
        "rollback_notes": [],
        "client_secret": "root-secret",
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response candidate includes unsupported properties"
    assert "client_secret" not in diagnostic
    assert "root-secret" not in diagnostic


def test_provider_candidate_normalization_rejects_unknown_change_property() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
                "client_secret": "change-secret",
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change includes unsupported properties"
    assert "client_secret" not in diagnostic
    assert "change-secret" not in diagnostic


def test_provider_candidate_normalization_rejects_unknown_field_property() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [
                    {
                        "name": "element",
                        "value": "u_vendor_reference",
                        "client_secret": "field-secret",
                    }
                ],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response field entry includes unsupported properties"
    assert "client_secret" not in diagnostic
    assert "field-secret" not in diagnostic


def test_provider_candidate_normalization_requires_change_table() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    assert str(exc.value) == "TestProvider response change table must be an exact string"


def test_provider_candidate_normalization_rejects_change_table_subclass_without_leak() -> None:
    class HostileTable(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=table-secret")

    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": HostileTable("sys_dictionary"),
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change table must be an exact string"
    assert "HostileTable" not in diagnostic
    assert "table-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("table_name", ["", "   "])
def test_provider_candidate_normalization_rejects_blank_change_table_without_leak(
    table_name: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": table_name,
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change table must be a non-empty identifier"
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_unsafe_change_table_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys dictionary\nclient_secret=table-secret",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert (
        diagnostic
        == "TestProvider response change table must not contain whitespace or control characters"
    )
    assert "table-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_normalization_rejects_unicode_control_table_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary\u200bclient_secret=table-secret",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert (
        diagnostic
        == "TestProvider response change table must not contain whitespace or control characters"
    )
    assert "table-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_oversized_change_table_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": f"{'x' * 201}client_secret=table-secret",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change table exceeds 200 characters"
    assert "table-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize(
    "table_name",
    [
        "sys-dictionary",
        "sys.dictionary",
        "1sys_dictionary",
        "sys_dictionary$client_secret=table-secret",
    ],
)
def test_provider_candidate_normalization_rejects_unsafe_table_identifier_without_leak(
    table_name: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": table_name,
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change table must be a safe identifier"
    assert "table-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize("table_name", ["sys_dictionary", "cmdb_ci", "x_jedi_app_table"])
def test_provider_candidate_normalization_accepts_safe_table_identifier(
    table_name: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": table_name,
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    normalised = _normalise(candidate)

    assert normalised["changes"][0]["table"] == table_name


def test_provider_candidate_normalization_rejects_invalid_change_operation_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "client_secret=operation-secret",
                "fields": [],
                "sys_id": None,
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change operation is unsupported"
    assert "operation-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_non_null_sys_id_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": "client_secret=sys-id-secret",
                "rationale": None,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change sys_id must be null"
    assert "sys-id-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_rejects_rationale_subclass_without_leak() -> None:
    class HostileRationale(str):
        def __str__(self) -> str:
            raise AssertionError("client_secret=rationale-secret")

    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": HostileRationale("Create requested field."),
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change rationale must be an exact string or null"
    assert "HostileRationale" not in diagnostic
    assert "rationale-secret" not in diagnostic
    assert "client_secret" not in diagnostic


@pytest.mark.parametrize(
    "rationale",
    [
        "Create requested field.\nclient_secret=rationale-secret",
        "Create requested field.\x7fclient_secret=rationale-secret",
    ],
)
def test_provider_candidate_normalization_rejects_rationale_control_characters_without_leak(
    rationale: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": rationale,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert (
        diagnostic
        == "TestProvider response change rationale must not contain control characters"
    )
    assert "rationale-secret" not in diagnostic
    assert "client_secret" not in diagnostic


def test_provider_candidate_normalization_accepts_sentence_rationale() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": "Create the requested field after validating instance context.",
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    normalised = _normalise(candidate)

    assert (
        normalised["changes"][0]["rationale"]
        == "Create the requested field after validating instance context."
    )


@pytest.mark.parametrize("rationale", ["", "   "])
def test_provider_candidate_normalization_rejects_blank_rationale_without_leak(
    rationale: str,
) -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": rationale,
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change rationale must not match text policy"
    if rationale:
        assert rationale not in diagnostic


def test_provider_candidate_normalization_uses_exported_text_pattern_for_rationale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        provider_response_normalization,
        "PROVIDER_NO_CONTROL_TEXT_PATTERN",
        r"^Approved rationale$",
    )
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": "Create requested field.",
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change rationale must not match text policy"
    assert "Create requested field" not in diagnostic


def test_provider_candidate_normalization_rejects_oversized_rationale_without_leak() -> None:
    candidate: dict[str, Any] = {
        "changes": [
            {
                "table": "sys_dictionary",
                "operation": "insert",
                "fields": [],
                "sys_id": None,
                "rationale": f"{'x' * 2001}client_secret=rationale-secret",
            }
        ],
        "test_plan": [],
        "rollback_notes": [],
    }

    with pytest.raises(ProviderNormalizationError) as exc:
        _normalise(candidate)

    diagnostic = str(exc.value)
    assert diagnostic == "TestProvider response change rationale exceeds 2000 characters"
    assert "rationale-secret" not in diagnostic
    assert "client_secret" not in diagnostic
