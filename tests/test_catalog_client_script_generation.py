from __future__ import annotations

import pytest

from jedi_devproject.catalog_client_script_generation import (
    CatalogClientScriptAction,
    CatalogClientScriptIntent,
    catalog_client_script_customer_updates,
    render_catalog_client_script,
)
from jedi_devproject.models import CandidateChange

_ITEM_VARIABLES = {"description", "needs_schedule", "start_date", "end_date"}

_ON_LOAD_SCRIPT = (
    "function onLoad() {\n"
    "    g_form.setValue('description', 'Standard badge request');\n"
    "}"
)


def _script_change(**field_overrides: object) -> CandidateChange:
    fields: dict[str, object] = {
        "name": "Populate description",
        "type": "onLoad",
        "script": _ON_LOAD_SCRIPT,
        "fields_written": ["description"],
    }
    fields.update(field_overrides)
    return CandidateChange(
        table="catalog_script_client",
        operation="insert",
        fields=fields,
        rationale="Populate the description on load.",
    )


def _updates(changes: list[CandidateChange]) -> list[dict[str, object]]:
    return catalog_client_script_customer_updates(
        changes=changes,
        remote_update_set_sys_id="remote-update-set-sys-id",
        catalog_item_name="Request Temporary Badge",
        catalog_item_sys_id="catalog-item-sys-id",
        item_variable_names=_ITEM_VARIABLES,
    )


def test_catalog_client_script_builds_payload_with_item_attachment() -> None:
    updates = _updates([_script_change()])

    assert [update["type"] for update in updates] == ["Catalog Client Script"]
    payload = str(updates[0]["payload"])
    assert '<record_update table="catalog_script_client">' in payload
    assert (
        '<cat_item display_value="Request Temporary Badge">catalog-item-sys-id</cat_item>'
        in payload
    )
    assert "<name>Populate description</name>" in payload
    assert "<type>onLoad</type>" in payload
    assert "<ui_type>10</ui_type>" in payload
    assert "<sys_class_name>catalog_script_client</sys_class_name>" in payload
    assert "<applies_catalog>true</applies_catalog>" in payload
    assert "<applies_req_item>true</applies_req_item>" in payload
    assert "<applies_sc_task>false</applies_sc_task>" in payload
    assert "g_form.setValue(&#x27;description&#x27;" in payload
    assert updates[0]["target_name"] == "Request Temporary Badge.Populate description"


def test_catalog_client_script_payloads_are_deterministic() -> None:
    assert _updates([_script_change()]) == _updates([_script_change()])


def test_catalog_client_script_onchange_carries_watched_variable() -> None:
    script = render_catalog_client_script(
        script_type="onChange",
        variable_name="needs_schedule",
        actions=[CatalogClientScriptAction(kind="clear_value", variable="end_date")],
    )
    updates = _updates(
        [
            _script_change(
                name="Clear end date",
                type="onChange",
                field="needs_schedule",
                script=script,
                fields_written=["end_date"],
            )
        ]
    )

    payload = str(updates[0]["payload"])
    assert "<field>needs_schedule</field>" in payload
    assert "<type>onChange</type>" in payload


def test_catalog_client_script_rejects_other_tables_and_updates() -> None:
    with pytest.raises(ValueError, match="catalog_script_client changes only: sys_script_client"):
        _updates([_script_change().model_copy(update={"table": "sys_script_client"})])
    with pytest.raises(ValueError, match="supports insert only"):
        _updates([_script_change().model_copy(update={"operation": "update"})])


def test_catalog_client_script_rejects_duplicate_script_names() -> None:
    with pytest.raises(ValueError, match="duplicate script: Populate description"):
        _updates([_script_change(), _script_change()])


def test_catalog_client_script_onchange_requires_variable() -> None:
    with pytest.raises(ValueError, match="onChange catalog client script requires a variable"):
        _updates([_script_change(type="onChange", field="")])


def test_catalog_client_script_rejects_unknown_script_type() -> None:
    with pytest.raises(ValueError, match="must be onLoad, onChange, or onSubmit"):
        _updates([_script_change(type="onCellEdit")])


@pytest.mark.parametrize(
    "snippet",
    [
        "document.getElementById('x');",
        "window.location = 'x';",
        "fetch('/api');",
        "new XMLHttpRequest();",
        "new GlideAjax('Helper');",
        "g_form.setValue('description', 'https://example.com');",
        "g_form.setValue('description', 'password');",
    ],
)
def test_catalog_client_script_rejects_forbidden_tokens(snippet: str) -> None:
    script = f"function onLoad() {{\n    {snippet}\n    g_form.getValue('description');\n}}"
    with pytest.raises(ValueError, match="forbidden Client Script token"):
        _updates([_script_change(script=script, fields_written="none")])


def test_catalog_client_script_requires_g_form_usage() -> None:
    with pytest.raises(ValueError, match="must use g_form APIs"):
        _updates(
            [_script_change(script="function onLoad() { return; }", fields_written="none")]
        )


def test_catalog_client_script_rejects_undeclared_field_writes() -> None:
    with pytest.raises(ValueError, match="writes undeclared field: description"):
        _updates([_script_change(fields_written="none")])


def test_catalog_client_script_rejects_variables_outside_the_item() -> None:
    with pytest.raises(
        ValueError,
        match="references a variable .* not one of .* own variables: badge_color",
    ):
        _updates(
            [
                _script_change(
                    script=(
                        "function onLoad() {\n"
                        "    g_form.setValue('badge_color', 'blue');\n"
                        "}"
                    ),
                    fields_written=["badge_color"],
                )
            ]
        )
    with pytest.raises(
        ValueError,
        match="references a variable .* not one of .* own variables: requested_for",
    ):
        _updates([_script_change(fields_read=["requested_for"])])


def test_render_catalog_client_script_renders_canonical_bodies() -> None:
    on_load = render_catalog_client_script(
        script_type="onload",
        actions=[
            CatalogClientScriptAction(
                kind="set_value",
                variable="description",
                value="Standard badge request",
            )
        ],
    )
    assert on_load == _ON_LOAD_SCRIPT

    on_change = render_catalog_client_script(
        script_type="onChange",
        variable_name="needs_schedule",
        actions=[CatalogClientScriptAction(kind="clear_value", variable="end_date")],
    )
    assert on_change == (
        "function onChange(control, oldValue, newValue, isLoading, isTemplate) {\n"
        "    if (isLoading) {\n"
        "        return;\n"
        "    }\n"
        "    g_form.clearValue('end_date');\n"
        "}"
    )

    on_submit = render_catalog_client_script(
        script_type="onSubmit",
        actions=[
            CatalogClientScriptAction(kind="set_value", variable="description", value="Ready")
        ],
    )
    assert on_submit == (
        "function onSubmit() {\n"
        "    g_form.setValue('description', 'Ready');\n"
        "    return true;\n"
        "}"
    )


def test_render_catalog_client_script_escapes_quotes_and_fails_closed() -> None:
    script = render_catalog_client_script(
        script_type="onLoad",
        actions=[
            CatalogClientScriptAction(
                kind="set_value",
                variable="description",
                value="Visitor's badge",
            )
        ],
    )
    assert "g_form.setValue('description', 'Visitor\\'s badge');" in script

    with pytest.raises(ValueError, match="requires at least one action"):
        render_catalog_client_script(script_type="onLoad", actions=[])
    with pytest.raises(ValueError, match="onChange catalog client script requires a variable"):
        render_catalog_client_script(
            script_type="onChange",
            actions=[CatalogClientScriptAction(kind="clear_value", variable="end_date")],
        )
    with pytest.raises(ValueError, match="single-line text"):
        render_catalog_client_script(
            script_type="onLoad",
            actions=[
                CatalogClientScriptAction(
                    kind="set_value",
                    variable="description",
                    value="line one\nline two",
                )
            ],
        )
    with pytest.raises(ValueError, match="forbidden Client Script token"):
        render_catalog_client_script(
            script_type="onLoad",
            actions=[
                CatalogClientScriptAction(
                    kind="set_value",
                    variable="description",
                    value="see https://example.com",
                )
            ],
        )


def test_catalog_client_script_action_model_fails_closed() -> None:
    with pytest.raises(ValueError, match="requires a variable"):
        CatalogClientScriptAction(kind="set_value", variable="  ", value="x")
    with pytest.raises(ValueError, match="set_value action requires a value"):
        CatalogClientScriptAction(kind="set_value", variable="description", value=" ")
    with pytest.raises(ValueError, match="clear_value action must not carry a value"):
        CatalogClientScriptAction(kind="clear_value", variable="description", value="x")


def test_catalog_client_script_intent_requires_named_script_and_body() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        CatalogClientScriptIntent(
            catalog_item_name="Request Temporary Badge",
            script_name="  ",
            script_type="onLoad",
            script=_ON_LOAD_SCRIPT,
            fields_read=[],
            fields_written=["description"],
        )
