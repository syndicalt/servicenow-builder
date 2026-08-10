from __future__ import annotations

import pytest

from jedi_devproject.xml_builder import (
    SYS_SCOPE_GLOBAL,
    XML_DECLARATION,
    bool_element,
    cdata,
    container_element,
    record_update,
    reference_qualifier_elements,
    text_element,
)


def test_xml_declaration_matches_servicenow_unload_header() -> None:
    assert XML_DECLARATION == '<?xml version="1.0" encoding="UTF-8"?>'


def test_sys_scope_global_matches_servicenow_global_scope_element() -> None:
    assert SYS_SCOPE_GLOBAL == '<sys_scope display_value="Global">global</sys_scope>'


def test_text_element_escapes_text_content() -> None:
    assert text_element("name", "JEDI <Rule> & 'quotes'") == (
        "<name>JEDI &lt;Rule&gt; &amp; &#x27;quotes&#x27;</name>"
    )
    assert text_element("name", 'a "b"') == "<name>a &quot;b&quot;</name>"


def test_text_element_keeps_empty_values_as_empty_elements() -> None:
    assert text_element("description", "") == "<description></description>"


def test_text_element_renders_attributes_in_call_order() -> None:
    assert text_element(
        "view",
        "section-sys-id",
        display_value="Default view",
        name="NULL",
    ) == '<view display_value="Default view" name="NULL">section-sys-id</view>'


def test_text_element_escapes_attribute_values() -> None:
    assert text_element("ui_policy", "policy-id", display_value='A & "B" <C>') == (
        '<ui_policy display_value="A &amp; &quot;B&quot; &lt;C&gt;">policy-id</ui_policy>'
    )


def test_bool_element_renders_lowercase_boolean_text() -> None:
    assert bool_element("active", True) == "<active>true</active>"
    assert bool_element("mandatory", False) == "<mandatory>false</mandatory>"


def test_container_element_joins_parts_without_escaping_them() -> None:
    assert container_element(
        "sys_script",
        "<active>true</active>",
        text_element("name", "a & b"),
        action="INSERT_OR_UPDATE",
    ) == (
        '<sys_script action="INSERT_OR_UPDATE">'
        "<active>true</active><name>a &amp; b</name>"
        "</sys_script>"
    )


def test_container_element_supports_no_attributes_and_empty_body() -> None:
    assert container_element("record_update") == "<record_update></record_update>"


def test_container_element_escapes_attribute_values_in_order() -> None:
    assert container_element(
        "sys_ui_section",
        caption="A & B",
        section_id="section-sys-id",
        sys_domain="global",
        version="3",
    ) == (
        '<sys_ui_section caption="A &amp; B" section_id="section-sys-id" '
        'sys_domain="global" version="3"></sys_ui_section>'
    )


def test_record_update_wraps_body_with_declaration() -> None:
    assert record_update("<sys_script>x</sys_script>") == (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<record_update><sys_script>x</sys_script></record_update>"
    )


def test_record_update_joins_multiple_parts() -> None:
    assert record_update("<a>1</a>", "<b>2</b>") == (
        '<?xml version="1.0" encoding="UTF-8"?><record_update><a>1</a><b>2</b></record_update>'
    )


def test_record_update_renders_optional_table_attribute() -> None:
    assert record_update("<sc_cat_item>x</sc_cat_item>", table="sc_cat_item") == (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record_update table="sc_cat_item"><sc_cat_item>x</sc_cat_item></record_update>'
    )


def test_cdata_wraps_value_without_escaping() -> None:
    assert cdata("a < b & c") == "<![CDATA[a < b & c]]>"
    assert cdata("") == "<![CDATA[]]>"


def test_cdata_splits_terminator_sequences() -> None:
    assert cdata("before ]]> after") == "<![CDATA[before ]]]]><![CDATA[> after]]>"
    assert cdata("]]>]]>") == "<![CDATA[]]]]><![CDATA[>]]]]><![CDATA[>]]>"


def test_reference_qualifier_elements_render_simple_qualifier() -> None:
    assert reference_qualifier_elements(
        reference_table="sys_user",
        reference_qualifier='active=true^name<"z"',
    ) == (
        "<reference>sys_user</reference>"
        "<reference_qual>active=true^name&lt;&quot;z&quot;</reference_qual>"
        "<reference_qual_condition>active=true^name&lt;&quot;z&quot;</reference_qual_condition>"
        "<use_reference_qualifier>simple</use_reference_qualifier>"
    )


def test_reference_qualifier_elements_render_empty_qualifier() -> None:
    assert reference_qualifier_elements(reference_table="sys_user", reference_qualifier="") == (
        "<reference>sys_user</reference>"
        "<reference_qual></reference_qual>"
        "<reference_qual_condition></reference_qual_condition>"
        "<use_reference_qualifier></use_reference_qualifier>"
    )


def test_text_element_rejects_invalid_xml_control_character() -> None:
    with pytest.raises(ValueError, match="Invalid XML character"):
        text_element("name", "prefix\x00suffix")


def test_text_element_rejects_xml_surrogate_character() -> None:
    with pytest.raises(ValueError, match="Invalid XML character"):
        text_element("name", "\ud83d")


def test_text_element_rejects_c1_control_character() -> None:
    with pytest.raises(ValueError, match="Invalid XML character"):
        text_element("name", "\x85")


def test_text_element_accepts_valid_whitespace_and_high_unicode() -> None:
    # Tab, LF, and characters outside the BMP are valid XML text content.
    assert text_element("name", "line1\nline2\t\U0001F600") == (
        "<name>line1\nline2\t\U0001F600</name>"
    )


def test_text_element_rejects_invalid_attribute_value() -> None:
    with pytest.raises(ValueError, match="Invalid XML character"):
        text_element("tag", "value", display_value="\x1b")


def test_record_update_rejects_invalid_table_attribute() -> None:
    with pytest.raises(ValueError, match="Invalid XML character"):
        record_update("<x></x>", table="bad\x00table")


def test_cdata_rejects_invalid_xml_character() -> None:
    with pytest.raises(ValueError, match="Invalid XML character"):
        cdata("prefix\x00suffix")
