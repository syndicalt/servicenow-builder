"""Shared builders for the hand-crafted customer-update XML emitted by generation modules.

Output is byte-identical to the previous inline f-string payloads: text and attribute
values are escaped with html.escape, attributes render in call order, and pre-rendered
parts are joined without separators.
"""

from __future__ import annotations

from html import escape

XML_DECLARATION = '<?xml version="1.0" encoding="UTF-8"?>'
SYS_SCOPE_GLOBAL = '<sys_scope display_value="Global">global</sys_scope>'


def text_element(name: str, value: str, /, **attributes: str) -> str:
    return f"<{name}{_render_attributes(attributes)}>{escape(value)}</{name}>"


def bool_element(name: str, value: bool) -> str:
    return f"<{name}>{'true' if value else 'false'}</{name}>"


def container_element(name: str, /, *parts: str, **attributes: str) -> str:
    return f"<{name}{_render_attributes(attributes)}>{''.join(parts)}</{name}>"


def record_update(*parts: str, table: str | None = None) -> str:
    body = "".join(parts)
    if table is None:
        return f"{XML_DECLARATION}<record_update>{body}</record_update>"
    return f'{XML_DECLARATION}<record_update table="{escape(table)}">{body}</record_update>'


def cdata(value: str) -> str:
    return f"<![CDATA[{value.replace(']]>', ']]]]><![CDATA[>')}]]>"


def reference_qualifier_elements(*, reference_table: str, reference_qualifier: str) -> str:
    return (
        text_element("reference", reference_table)
        + text_element("reference_qual", reference_qualifier)
        + text_element("reference_qual_condition", reference_qualifier)
        + text_element("use_reference_qualifier", "simple" if reference_qualifier else "")
    )


def _render_attributes(attributes: dict[str, str]) -> str:
    return "".join(f' {key}="{escape(value)}"' for key, value in attributes.items())
